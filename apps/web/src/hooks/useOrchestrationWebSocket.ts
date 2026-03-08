"use client";

import { useEffect, useRef, useCallback, useState } from "react";

const getWsUrl = (sessionId: string) => {
  const base = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const wsBase = base.replace(/^http/, "ws");
  return `${wsBase}/ws/${sessionId}`;
};

export interface OrchestrationState {
  phase: string;
  step_count?: number;
  providers?: any[];
  offers?: any[];
  plans?: any[];
  decomposition?: any;
  workload?: any;
}

export type StateUpdateHandler = (state: OrchestrationState) => void;

export function useOrchestrationWebSocket(
  sessionId: string | null,
  onStateUpdate?: StateUpdateHandler
) {
  const [connectionStatus, setConnectionStatus] = useState<"disconnected" | "connecting" | "connected">("disconnected");
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const onStateUpdateRef = useRef(onStateUpdate);
  onStateUpdateRef.current = onStateUpdate;

  const requestState = useCallback((ws: WebSocket) => {
    if (ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: "state", data: {} }));
    }
  }, []);

  const connect = useCallback(() => {
    if (!sessionId) return;

    setConnectionStatus("connecting");
    const url = getWsUrl(sessionId);
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnectionStatus("connected");
      requestState(ws);
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === "state" && msg.data) {
          onStateUpdateRef.current?.(msg.data);
        } else if (msg.type === "observation" && msg.data) {
          onStateUpdateRef.current?.({
            phase: msg.data.phase,
            step_count: msg.data.step_count,
            ...msg.data.observation,
          });
        } else if (msg.type === "error") {
          console.warn("[WebSocket]", msg.data?.message || "Unknown error");
        }
      } catch (e) {
        console.warn("[WebSocket] Parse error", e);
      }
    };

    ws.onclose = () => {
      setConnectionStatus("disconnected");
      wsRef.current = null;
      reconnectTimeoutRef.current = setTimeout(() => {
        if (sessionId) connect();
      }, 2000);
    };

    ws.onerror = () => {
      setConnectionStatus("disconnected");
    };
  }, [sessionId, requestState]);

  useEffect(() => {
    if (!sessionId) {
      setConnectionStatus("disconnected");
      return;
    }
    connect();
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      wsRef.current?.close();
      wsRef.current = null;
      setConnectionStatus("disconnected");
    };
  }, [sessionId, connect]);

  const refreshState = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      requestState(wsRef.current);
    }
  }, [requestState]);

  return { connectionStatus, refreshState };
}
