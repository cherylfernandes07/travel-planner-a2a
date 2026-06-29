# ─────────────────────────────────────────────────────────────
# models.py
# Pydantic models — mirror the TypeScript types in ws-events.ts
# exactly. If you change a field here, update the TS types too.
# ─────────────────────────────────────────────────────────────

from __future__ import annotations
from enum import Enum
from typing import Literal, Optional, Union
from pydantic import BaseModel


# ── Enums ─────────────────────────────────────────────────────

class AgentName(str, Enum):
    flight    = "flight"
    hotel     = "hotel"
    itinerary = "itinerary"
    budget    = "budget"

class TaskStatus(str, Enum):
    submitted = "submitted"
    working   = "working"
    completed = "completed"
    failed    = "failed"


# ── Inbound request (from frontend POST /plan) ────────────────

class TripRequest(BaseModel):
    destination:   str
    origin:        str
    departureDate: str           # ISO 8601 e.g. "2025-10-15"
    returnDate:    str
    budget:        float         # USD
    travelers:     int = 1
    interests:     list[str] = []


# ── Artifact shapes ───────────────────────────────────────────

class FlightOption(BaseModel):
    id:           str
    airline:      str
    priceUsd:     float
    durationMins: int
    stops:        int
    bookingUrl:   str

class FlightArtifact(BaseModel):
    options:        list[FlightOption]
    recommendedId:  str

class HotelOption(BaseModel):
    id:           str
    name:         str
    nightlyRate:  float
    totalCost:    float
    stars:        int
    neighborhood: str
    amenities:    list[str]

class HotelArtifact(BaseModel):
    options:       list[HotelOption]
    recommendedId: str

class Activity(BaseModel):
    time:        str
    name:        str
    estCostUsd:  float

class Day(BaseModel):
    day:        int
    theme:      str
    activities: list[Activity]

class ItineraryArtifact(BaseModel):
    days: list[Day]

class BudgetBreakdown(BaseModel):
    flights:    float
    hotels:     float
    activities: float
    dailyMisc:  float
    total:      float

class BudgetArtifact(BaseModel):
    breakdown:      BudgetBreakdown
    fitsBudget:     bool
    surplusDeficit: float


# ── Assembled trip plan ───────────────────────────────────────

class TripPlan(BaseModel):
    destination: str
    dates:       str
    flight:      Optional[FlightArtifact]    = None
    hotel:       Optional[HotelArtifact]     = None
    itinerary:   Optional[ItineraryArtifact] = None
    budget:      Optional[BudgetArtifact]    = None


# ── WebSocket event shapes ────────────────────────────────────
# These are what the backend pushes down the WS connection.
# Match ws-events.ts on the frontend exactly.

class TaskCreatedEvent(BaseModel):
    event:  Literal["task_created"] = "task_created"
    agent:  AgentName
    status: Literal["submitted"]    = "submitted"
    taskId: str

class TaskUpdatedEvent(BaseModel):
    event:  Literal["task_updated"] = "task_updated"
    agent:  AgentName
    status: TaskStatus
    taskId: str

class ArtifactEvent(BaseModel):
    event:  Literal["artifact"] = "artifact"
    agent:  AgentName
    taskId: str
    data:   Union[FlightArtifact, HotelArtifact, ItineraryArtifact, BudgetArtifact]

class PlanCompleteEvent(BaseModel):
    event: Literal["plan_complete"] = "plan_complete"
    data:  TripPlan

class AgentError(BaseModel):
    agent:   AgentName
    message: str

class PlanPartialEvent(BaseModel):
    """Emitted when some agents failed but others succeeded."""
    event:         Literal["plan_partial"] = "plan_partial"
    data:          TripPlan
    failed_agents: list[AgentError]

class ErrorEvent(BaseModel):
    event:   Literal["error"] = "error"
    agent:   Optional[AgentName] = None
    message: str

WSEvent = Union[
    TaskCreatedEvent,
    TaskUpdatedEvent,
    ArtifactEvent,
    PlanCompleteEvent,
    PlanPartialEvent,
    ErrorEvent,
]