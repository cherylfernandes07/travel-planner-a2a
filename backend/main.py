from dotenv import load_dotenv
load_dotenv()

import uuid
import json
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# A2A SDK
from a2a.types import AgentCard, AgentSkill
from a2a.server.routes.agent_card_routes import create_agent_card_routes
from a2a.server.routes.fastapi_routes import add_a2a_routes_to_fastapi
from rate_limiter import check_rate_limit, get_client_ip, get_rate_limit_status

from models import TripRequest, WSEvent
from agents.planner import run_planner
from agents.flight    import AGENT_CARD as flight_card
from agents.hotel     import AGENT_CARD as hotel_card
from agents.itinerary import AGENT_CARD as itinerary_card
from agents.budget    import AGENT_CARD as budget_card

from auth import verify_clerk_token

from database import init_db, save_trip_plan, get_user_trips, get_trip_by_id, save_waitlist_email
from logger import setup_logging, get_logger
import uuid as uuid_module
from pydantic import BaseModel, EmailStr

log = get_logger("main")

# ── App setup ─────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()  # ← add this
    await init_db()    
    yield

app = FastAPI(title="AI Travel Planner", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://travel-planner-a2a-front-end.vercel.app",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── A2A Planner Agent Card ────────────────────────────────────
planner_agent_card = AgentCard(
    name="Travel Planner",
    description="Orchestrates flight, hotel, itinerary and budget agents.",
    version="1.0.0",
    skills=[
        AgentSkill(
            id="plan_trip",
            name="Plan Complete Trip",
            description="Generates a full trip plan with flights, hotels, itinerary and budget.",
            tags=["travel", "planning", "a2a"],
        )
    ],
)

# ── Mount A2A routes — exposes /.well-known/agent-card.json ──
agent_card_routes = create_agent_card_routes(agent_card=planner_agent_card)
add_a2a_routes_to_fastapi(app, agent_card_routes=agent_card_routes)

# ── In-memory session store ───────────────────────────────────
sessions: dict[str, TripRequest] = {}

# ── Sub-agent card endpoints ──────────────────────────────────
@app.get("/rate-limit-status")
async def rate_limit_status(http_request: Request) -> dict:
    ip = get_client_ip(http_request)
    return await get_rate_limit_status(ip)
    
@app.get("/agents/flight/.well-known/agent-card.json")
async def flight_agent_card():
    return flight_card

@app.get("/agents/hotel/.well-known/agent-card.json")
async def hotel_agent_card():
    return hotel_card

@app.get("/agents/itinerary/.well-known/agent-card.json")
async def itinerary_agent_card():
    return itinerary_card

@app.get("/agents/budget/.well-known/agent-card.json")
async def budget_agent_card():
    return budget_card

# ── POST /plan ────────────────────────────────────────────────
session_metadata: dict[str, str] = {}  # session_id → user_id

@app.post("/plan")
async def create_plan(
    request: TripRequest,
    http_request: Request,
    token_payload: dict = Depends(verify_clerk_token),
) -> dict:
    user_id = token_payload.get("sub")
    ip = get_client_ip(http_request)
    usage = await check_rate_limit(ip)
    session_id = str(uuid_module.uuid4())
    trace_id = str(uuid_module.uuid4())[:8]  # short trace ID
    sessions[session_id] = request
    session_metadata[session_id] = {"user_id": user_id, "trace_id": trace_id}

    log.info("Plan request received", extra={
        "trace_id": trace_id,
        "user_id": user_id,
        "destination": request.destination,
        "ip": ip,
    })

    return {"sessionId": session_id, "rateLimit": usage}

# ── WS /ws/{session_id} ───────────────────────────────────────
@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    request = sessions.pop(session_id, None)
    if not request:
        await websocket.send_text(json.dumps({
            "event": "error",
            "message": f"Session {session_id} not found or already used"
        }))
        await websocket.close()
        return

    # get metadata
    meta = session_metadata.pop(session_id, {})
    user_id = meta.get("user_id")
    trace_id = meta.get("trace_id", "")

    async def push(event: WSEvent):
        await websocket.send_text(event.model_dump_json())
        if event.event in ("plan_complete", "plan_partial"):
            if user_id:
                import uuid
                await save_trip_plan(
                    plan_id=str(uuid.uuid4()),
                    user_id=user_id,
                    destination=event.data.destination,
                    dates=event.data.dates,
                    plan_data=event.data.model_dump(),
                    status="complete" if event.event == "plan_complete" else "partial",
                )

    try:
        await run_planner(request, push, trace_id=trace_id)  # ← pass trace_id
    except WebSocketDisconnect:
        log.info("Client disconnected", extra={"trace_id": trace_id})
    except Exception as e:
        log.error(f"WebSocket error: {e}", extra={"trace_id": trace_id})
        await websocket.send_text(json.dumps({
            "event": "error", "message": str(e)
        }))
    finally:
        sessions.pop(session_id, None)
        session_metadata.pop(session_id, None)

        
# ── Health check ──────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/trips")
async def get_trips(
    token_payload: dict = Depends(verify_clerk_token),
) -> list:
    user_id = token_payload.get("sub")
    return await get_user_trips(user_id)

@app.get("/trips/{plan_id}")
async def get_trip(
    plan_id: str,
    token_payload: dict = Depends(verify_clerk_token),
) -> dict:
    user_id = token_payload.get("sub")
    trip = await get_trip_by_id(plan_id, user_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip



class WaitlistRequest(BaseModel):
    email: EmailStr

@app.post("/waitlist")
async def join_waitlist(request: WaitlistRequest) -> dict:
    await save_waitlist_email(request.email)
    return {"message": "You're on the list!"}