import { useState, useEffect, useRef, useCallback } from "react";

const WS_BASE = "ws://localhost:8000/ws/live";

/**
 * useLiveMatch — connects to the live simulation WebSocket.
 *
 * @param {string|null} homeTeam
 * @param {string|null} awayTeam
 * @param {number|null} homeXg   — alternative to team names
 * @param {number|null} awayXg
 * @param {number}      speed    — seconds per simulated minute (default 0.35)
 * @param {number}      stride   — simulated minutes per tick (default 1)
 *
 * Returns:
 *   state       — latest tick payload (null before first tick)
 *   history     — array of all tick payloads
 *   status      — "idle" | "connecting" | "running" | "finished" | "error"
 *   start()     — open the WebSocket
 *   stop()      — close the WebSocket
 *   reset()     — clear history and state
 */
export function useLiveMatch({
  homeTeam = null,
  awayTeam = null,
  homeXg   = null,
  awayXg   = null,
  speed    = 0.35,
  stride   = 1,
} = {}) {
  const [state,   setState]   = useState(null);
  const [history, setHistory] = useState([]);
  const [status,  setStatus]  = useState("idle");
  const wsRef = useRef(null);

  const buildUrl = useCallback(() => {
    const params = new URLSearchParams({ speed, stride });
    if (homeTeam && awayTeam) {
      params.set("home_team", homeTeam);
      params.set("away_team", awayTeam);
    } else if (homeXg != null && awayXg != null) {
      params.set("home_xg", homeXg);
      params.set("away_xg", awayXg);
    }
    return `${WS_BASE}?${params}`;
  }, [homeTeam, awayTeam, homeXg, awayXg, speed, stride]);

  const stop = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  const reset = useCallback(() => {
    stop();
    setState(null);
    setHistory([]);
    setStatus("idle");
  }, [stop]);

  const start = useCallback(() => {
    reset();
    setStatus("connecting");

    const ws = new WebSocket(buildUrl());
    wsRef.current = ws;

    ws.onopen  = () => setStatus("running");
    ws.onerror = () => setStatus("error");
    ws.onclose = () => setStatus((s) => s === "running" ? "finished" : s);

    ws.onmessage = (e) => {
      try {
        const payload = JSON.parse(e.data);
        setState(payload);
        setHistory((h) => [...h, payload]);
        if (payload.type === "final") {
          setStatus("finished");
          ws.close();
        }
      } catch (_) {}
    };
  }, [buildUrl, reset]);

  useEffect(() => () => stop(), [stop]);

  return { state, history, status, start, stop, reset };
}
