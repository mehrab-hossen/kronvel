import { FormEvent, useEffect, useRef, useState } from "react"
import ReactMarkdown from "react-markdown"

import { useCopilotChat } from "../../hooks/useCopilotChat"

export function CopilotChat() {
  const { turns, trace, streaming, sendMessage } = useCopilotChat()
  const [input, setInput] = useState("")
  const chatEndRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({
      behavior: "smooth",
    })
  }, [turns, streaming])

  function handleSubmit(e: FormEvent) {
    e.preventDefault()

    if (!input.trim() || streaming) return

    sendMessage(input.trim())
    setInput("")
  }

  return (
    <div className="panel">
      <h2>Copilot</h2>

      <div className="chat-log">
        {turns.length === 0 && (
          <div className="empty-state">
            Ask about cluster health — e.g. "why is gpu-node-6 unhealthy?"
          </div>
        )}

        {turns.map((turn, i) => (
          <div key={i} className={`chat-turn chat-turn--${turn.role}`}>
            <strong>{turn.role === "user" ? "You" : "Copilot"}:</strong>{" "}
            <ReactMarkdown>{turn.text}</ReactMarkdown>
          </div>
        ))}

        {streaming && (
          <div className="chat-trace">
            {trace
              .filter((t) => t.type === "tool_call")
              .map((t, i) => (
                <div key={i} className="chat-trace__item">
                  → calling {String(t.payload.tool)}…
                </div>
              ))}
          </div>
        )}

        <div ref={chatEndRef} />
      </div>

      <form onSubmit={handleSubmit} className="chat-input">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about cluster health…"
          disabled={streaming}
        />

        <button type="submit" disabled={streaming}>
          {streaming ? "Thinking…" : "Send"}
        </button>
      </form>
    </div>
  )
}
