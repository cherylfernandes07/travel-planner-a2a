# models.py
# Pydantic models — mirror the TypeScript types in ws-events.ts
# exactly. If you change a field here, update the TS types too.

from __future__ import annotations
from enum import Enum
from typing import Literal, Optional, Union
from datetime import date
import re
from pydantic import BaseModel, field_validator, model_validator


# Enums

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


# Inbound request (from frontend POST /plan)

SAFE_TEXT_RE = re.compile(r'^[a-zA-Z0-9\s\-\',\.]+$')

class TripRequest(BaseModel):
    destination:   str
    origin:        str
    departureDate: str
    returnDate:    str
    budget:        float
    travelers:     int = 1
    interests:     list[str] = []

    @field_validator('destination', 'origin')
    @classmethod
    def validate_location(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError('Cannot be empty')
        if len(v) > 100:
            raise ValueError('Cannot exceed 100 characters')
        if not SAFE_TEXT_RE.match(v):
            raise ValueError('Contains invalid characters')
        return v

    @field_validator('departureDate', 'returnDate')
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        try:
            date.fromisoformat(v)
        except ValueError:
            raise ValueError('Must be a valid date in YYYY-MM-DD format')
        return v

    @field_validator('budget')
    @classmethod
    def validate_budget(cls, v: float) -> float:
        if v <= 0:
            raise ValueError('Budget must be greater than $0')
        if v > 100_000:
            raise ValueError('Budget cannot exceed $100,000')
        return v

    @field_validator('travelers')
    @classmethod
    def validate_travelers(cls, v: int) -> int:
        if v < 1:
            raise ValueError('Must have at least 1 traveler')
        if v > 20:
            raise ValueError('Cannot exceed 20 travelers')
        return v

    @field_validator('interests')
    @classmethod
    def validate_interests(cls, v: list[str]) -> list[str]:
        if len(v) > 10:
            raise ValueError('Cannot have more than 10 interests')
        for interest in v:
            if len(interest) > 50:
                raise ValueError(f'Interest "{interest[:20]}..." exceeds 50 characters')
        return v

    @model_validator(mode='after')
    def validate_dates(self) -> 'TripRequest':
        dep = date.fromisoformat(self.departureDate)
        ret = date.fromisoformat(self.returnDate)
        today = date.today()

        if dep < today:
            raise ValueError('Departure date must be in the future')
        if ret <= dep:
            raise ValueError('Return date must be after departure date')
        if (ret - dep).days > 30:
            raise ValueError('Trip cannot exceed 30 days')
        if (ret - dep).days < 1:
            raise ValueError('Trip must be at least 1 day')

        return self


# Artifact shapes

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


# Assembled trip plan

class TripPlan(BaseModel):
    destination: str
    dates:       str
    flight:      Optional[FlightArtifact]    = None
    hotel:       Optional[HotelArtifact]     = None
    itinerary:   Optional[ItineraryArtifact] = None
    budget:      Optional[BudgetArtifact]    = None


# WebSocket event shapes

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