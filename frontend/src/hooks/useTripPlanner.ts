// ─────────────────────────────────────────────────────────────
// useTripPlanner.ts
// Drop-in hook for both mock and real WebSocket modes.
//
// Mock mode (default):  set NEXT_PUBLIC_USE_MOCK_WS=true
// Real mode:            set NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
//
// The hook interface is identical in both modes — your
// components never need to know which is running.
// ─────────────────────────────────────────────────────────────

import { useState, useRef, useCallback } from "react";
import { WSEvent, TripPlan, AgentName, TaskStatus } from "../lib/ws-events";
import { MOCK_WS_SEQUENCE } from "../lib/mock-ws-events";
import { useAuth } from '@clerk/nextjs'

// ── Public types ──────────────────────────────────────────────

export interface TripRequest {
  destination: string;
  origin: string;
  departureDate: string;
  returnDate: string;
  budget: number;
  travelers: number;
  interests: string[];
}

export interface AgentState {
  name: AgentName;
  status: TaskStatus | "idle";
  taskId?: string;
  hasArtifact: boolean;
}

export interface EventLogEntry {
  timestamp: string;
  event: WSEvent;
}

export type PlannerStatus =
  | "idle"
  | "connecting"
  | "planning"
  | "complete"
  | "error";

export interface UseTripPlannerReturn {
  status: PlannerStatus;
  agents: AgentState[];
  eventLog: EventLogEntry[];
  plan: TripPlan | null;
  error: string | null;
  startPlanning: (request: TripRequest) => void;
  reset: () => void;
}

// ── Initial agent states ──────────────────────────────────────

const INITIAL_AGENTS: AgentState[] = [
  { name: "flight", status: "idle", hasArtifact: false },
  { name: "hotel", status: "idle", hasArtifact: false },
  { name: "itinerary", status: "idle", hasArtifact: false },
  { name: "budget", status: "idle", hasArtifact: false },
];

// ── Hook ──────────────────────────────────────────────────────

export function useTripPlanner(): UseTripPlannerReturn {
  const [status, setStatus] = useState<PlannerStatus>("idle");
  const [agents, setAgents] = useState<AgentState[]>(INITIAL_AGENTS);
  const [eventLog, setEventLog] = useState<EventLogEntry[]>([]);
  const [plan, setPlan] = useState<TripPlan | null>(null);
  const [error, setError] = useState<string | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const isCompleteRef = useRef(false);
  const timersRef = useRef<ReturnType<typeof setTimeout>[]>([]);
  const { getToken } = useAuth()

  // ── Shared event processor (same for mock + real) ─────────
  const processEvent = useCallback((wsEvent: WSEvent) => {
    const entry: EventLogEntry = {
      timestamp: new Date().toLocaleTimeString("en-US", { hour12: false }),
      event: wsEvent,
    };

    setEventLog(prev => [...prev, entry]);
    switch (wsEvent.event) {
      case "task_created":
      case "task_updated":
        setAgents(prev => prev.map(a =>
          a.name === wsEvent.agent
            ? { ...a, status: wsEvent.status, taskId: wsEvent.taskId }
            : a
        ));
        break;

      case "artifact":
        setAgents(prev => prev.map(a =>
          a.name === wsEvent.agent
            ? { ...a, hasArtifact: true }
            : a
        ));
        break;

      case "plan_complete":
      case "plan_partial":
        setPlan(wsEvent.data);
        setStatus("complete");
        isCompleteRef.current = true; 
        break;

      case "error":
        if (wsEvent.agent) {
          setAgents(prev => prev.map(a =>
            a.name === wsEvent.agent ? { ...a, status: "failed" } : a
          ));
        }
        setError(wsEvent.message);
        setStatus("error");
        break;
    }
  }, []);

  // ── Mock mode ─────────────────────────────────────────────
  const startMock = useCallback(() => {
    setStatus("planning");
    timersRef.current = MOCK_WS_SEQUENCE.map(([delay, event]) =>
      setTimeout(() => processEvent(event), delay)
    );
  }, [processEvent]);

  // ── Real WebSocket mode ───────────────────────────────────
const startReal = useCallback(async (request: TripRequest) => {
  const wsUrl = process.env.NEXT_PUBLIC_WS_URL;
  if (!wsUrl) {
    setError("NEXT_PUBLIC_WS_URL is not set");
    setStatus("error");
    return;
  }

  setStatus("connecting");

  // Get Clerk token
  const token = await getToken();
  if (!token) {
    setError("Not authenticated");
    setStatus("error");
    return;
  }

  // POST to /plan with Authorization header
  fetch(wsUrl.replace("ws://", "http://").replace("/ws", "/plan"), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`,  // ← sends Clerk JWT
    },
    body: JSON.stringify(request),
  })
    .then(r => r.json())
    .then(({ sessionId }) => {
      if (!sessionId) {
        setError("Failed to create session");
        setStatus("error");
        return;
      }
      const ws = new WebSocket(`${wsUrl}/${sessionId}`);
      wsRef.current = ws;

      ws.onopen = () => setStatus("planning");

      ws.onmessage = (e) => {
        try {
          const event = JSON.parse(e.data) as WSEvent;
          processEvent(event);
        } catch {
          console.error("Failed to parse WS event", e.data);
        }
      };

      ws.onerror = () => {
        setError("WebSocket connection failed");
        setStatus("error");
      };

      ws.onclose = () => {
        // if (status !== "complete") setStatus("error");
        if (!isCompleteRef.current) {
          setError("Connection closed unexpectedly");
          setStatus("error");
        }        
      };
    })
    .catch(err => {
      setError(err.message);
      setStatus("error");
    });
}, [processEvent, status, getToken]);  // ← getToken added here

  // ── Public startPlanning — checks env var ─────────────────
  const startPlanning = useCallback((request: TripRequest) => {
    reset();
    const useMock = process.env.NEXT_PUBLIC_USE_MOCK_WS === "true"
      || !process.env.NEXT_PUBLIC_WS_URL;

    if (useMock) {
      startMock();
    } else {
      startReal(request);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [startMock, startReal]);

  // ── Reset everything ──────────────────────────────────────
const reset = useCallback(() => {
  timersRef.current.forEach(clearTimeout);
  timersRef.current = [];
  wsRef.current?.close();
  wsRef.current = null;
  isCompleteRef.current = false;  // ← add this
  setStatus("idle");
  setAgents(INITIAL_AGENTS);
  setEventLog([]);
  setPlan(null);
  setError(null);
}, []);

  return { status, agents, eventLog, plan, error, startPlanning, reset };
}