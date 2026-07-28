import { useCallback, useRef, useState } from "react"

export interface ChatTurn {
  role: "user" | "assistant"
  text: string
}

export interface AgentTraceItem {
  type: "tool_call" | "tool_result" | "answer" | "error" | "session"
  payload: Record<string, unknown>
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000"

export function useCopilotChat() {
  const [turns, setTurns] = useState<ChatTurn[]>([])
  const [trace, setTrace] = useState<AgentTraceItem[]>([])
  const [streaming, setStreaming] = useState(false)
  const sessionIdRef = useRef<string | null>(null)

  const sendMessage = useCallback(async (message: string) => {
    setTurns((prev) => [...prev, { role: "user", text: message }])
    setTrace([])
    setStreaming(true)

    const response = await fetch(`${API_BASE_URL}/copilot/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionIdRef.current, message }),
    })

    if (!response.body) {
      setStreaming(false)
      return
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ""

    // eslint-disable-next-line no-constant-condition
    while (true) {
      const { value, done } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })

      const chunks = buffer.split("\n\n")
      buffer = chunks.pop() ?? ""

      for (const raw of chunks) {
        const lines = raw.split("\n")
        const eventLine = lines.find((l) => l.startsWith("event:"))
        const dataLine = lines.find((l) => l.startsWith("data:"))
        if (!eventLine || !dataLine) continue

        const type = eventLine.replace("event:", "").trim() as AgentTraceItem["type"]
        const payload = JSON.parse(dataLine.replace("data:", "").trim())

        if (type === "session") {
          sessionIdRef.current = payload.session_id as string
          continue
        }
        if (type === "answer") {
          setTurns((prev) => [...prev, { role: "assistant", text: payload.text as string }])
        }
        setTrace((prev) => [...prev, { type, payload }])
      }
    }

    setStreaming(false)
  }, [])

  return { turns, trace, streaming, sendMessage }
}
