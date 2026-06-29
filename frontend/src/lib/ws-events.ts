// ─────────────────────────────────────────────────────────────
// ws-events.ts
// Single source of truth for every WebSocket event shape.
// Both the mock and the real WS hook emit these exact types.
// ─────────────────────────────────────────────────────────────

export type AgentName = "flight" | "hotel" | "itinerary" | "budget";
export type TaskStatus = "submitted" | "working" | "completed" | "failed";

// ── Individual event types ────────────────────────────────────

export interface TaskCreatedEvent {
    event: "task_created";
    agent: AgentName;
    status: "submitted";
    taskId: string;
}

export interface TaskUpdatedEvent {
    event: "task_updated";
    agent: AgentName;
    status: TaskStatus;
    taskId: string;
}

export interface ArtifactEvent {
    event: "artifact";
    agent: AgentName;
    taskId: string;
    data: FlightArtifact | HotelArtifact | ItineraryArtifact | BudgetArtifact;
}

export interface PlanCompleteEvent {
    event: "plan_complete";
    data: TripPlan;
}

export interface ErrorEvent {
    event: "error";
    agent?: AgentName;
    message: string;
}

// Add PlanPartialEvent to the union
export type WSEvent =
    | TaskCreatedEvent
    | TaskUpdatedEvent
    | ArtifactEvent
    | PlanCompleteEvent
    | PlanPartialEvent  // ← add this
    | ErrorEvent;

// ── Artifact shapes (match the data contracts) ───────────────

export interface FlightOption {
    id: string;
    airline: string;
    priceUsd: number;
    durationMins: number;
    stops: number;
    bookingUrl: string;
}

export interface FlightArtifact {
    options: FlightOption[];
    recommendedId: string;
}

export interface HotelOption {
    id: string;
    name: string;
    nightlyRate: number;
    totalCost: number;
    stars: number;
    neighborhood: string;
    amenities: string[];
}

export interface HotelArtifact {
    options: HotelOption[];
    recommendedId: string;
}

export interface Activity {
    time: string;
    name: string;
    estCostUsd: number;
}

export interface Day {
    day: number;
    theme: string;
    activities: Activity[];
}

export interface ItineraryArtifact {
    days: Day[];
}

export interface BudgetArtifact {
    breakdown: {
        flights: number;
        hotels: number;
        activities: number;
        dailyMisc: number;
        total: number;
    };
    fitsBudget: boolean;
    surplusDeficit: number;
}

// ── Assembled plan (plan_complete payload) ────────────────────

export interface TripPlan {
    destination: string;
    dates: string;
    flight: FlightArtifact | null;
    hotel: HotelArtifact | null;
    itinerary: ItineraryArtifact | null;
    budget: BudgetArtifact | null;
}

// Add these two new types
export interface AgentError {
    agent: AgentName;
    message: string;
}

export interface PlanPartialEvent {
    event: "plan_partial";
    data: TripPlan;
    failed_agents: AgentError[];
}

