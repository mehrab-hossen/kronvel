import { useEffect, useRef, useState } from "react"

interface PollingResult<T> {
  data: T | null
  error: Error | null
  loading: boolean
}

/**
 * Generic polling hook. Intentionally simple (no caching layer, no dedup) —
 * appropriate for an MVP dashboard with two low-frequency endpoints, not a
 * general-purpose data-fetching library.
 */
export function usePolling<T>(fetchFn: () => Promise<T>, intervalMs: number): PollingResult<T> {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<Error | null>(null)
  const [loading, setLoading] = useState(true)
  const fetchFnRef = useRef(fetchFn)
  fetchFnRef.current = fetchFn

  useEffect(() => {
    let cancelled = false

    async function tick() {
      try {
        const result = await fetchFnRef.current()
        if (!cancelled) {
          setData(result)
          setError(null)
        }
      } catch (err) {
        if (!cancelled) setError(err as Error)
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    tick()
    const timer = window.setInterval(tick, intervalMs)
    return () => {
      cancelled = true
      window.clearInterval(timer)
    }
  }, [intervalMs])

  return { data, error, loading }
}
