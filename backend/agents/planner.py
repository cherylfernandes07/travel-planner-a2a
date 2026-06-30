# agents/planner.py
# Orchestrates the full A2A flow with error handling and logging.

import asyncio
import uuid
import time
from typing import Callable, Awaitable, Optional

from logger import get_logger, TraceLogger
from models import (
    TripRequest, WSEvent,
    TaskCreatedEvent, TaskUpdatedEvent, ArtifactEvent,
    PlanCompleteEvent, PlanPartialEvent, ErrorEvent, AgentError,
    AgentName, TripPlan,
    ItineraryArtifact,
)
from agents.flight    import run_flight_agent
from agents.hotel     import run_hotel_agent
from agents.itinerary import run_itinerary_agent
from agents.budget    import run_budget_agent
from constants import AGENT_TIMEOUT_SECONDS

Push = Callable[[WSEvent], Awaitable[None]]
log = get_logger("planner")


async def run_planner(request: TripRequest, push: Push, trace_id: str = "") -> None:
    tlog = TraceLogger(log, trace_id, agent="planner")
    tlog.info(f"Starting plan for {request.destination}")

    failed_agents: list[AgentError] = []  # ← defined here, shared by run_agent

    async def run_agent(name: AgentName, coro: Awaitable) -> Optional[object]:
        task_id = f"task-{name}-{uuid.uuid4().hex[:6]}"
        alog = TraceLogger(log, trace_id, agent=name.value)

        await push(TaskCreatedEvent(agent=name, taskId=task_id))
        await push(TaskUpdatedEvent(agent=name, status="working", taskId=task_id))

        start = time.time()
        try:
            artifact = await asyncio.wait_for(coro, timeout=AGENT_TIMEOUT_SECONDS)
            duration = int((time.time() - start) * 1000)
            alog.info("Agent completed", extra={"duration_ms": duration})
            await push(ArtifactEvent(agent=name, taskId=task_id, data=artifact))
            await push(TaskUpdatedEvent(agent=name, status="completed", taskId=task_id))
            return artifact

        except asyncio.TimeoutError:
            msg = f"Agent timed out after {AGENT_TIMEOUT_SECONDS}s"
            alog.error(msg)
            await push(TaskUpdatedEvent(agent=name, status="failed", taskId=task_id))
            await push(ErrorEvent(agent=name, message=msg))
            failed_agents.append(AgentError(agent=name, message=msg))
            return None

        except Exception as e:
            msg = str(e)
            alog.error(f"Agent failed: {msg}")
            await push(TaskUpdatedEvent(agent=name, status="failed", taskId=task_id))
            await push(ErrorEvent(agent=name, message=msg))
            failed_agents.append(AgentError(agent=name, message=msg))
            return None

    # Step 1: dispatch Flight, Hotel, Itinerary in parallel
    flight_result, hotel_result, itinerary_result = await asyncio.gather(
        run_agent(AgentName.flight,    run_flight_agent(request)),
        run_agent(AgentName.hotel,     run_hotel_agent(request)),
        run_agent(AgentName.itinerary, run_itinerary_agent(request)),
    )

    # Step 2: Budget runs last — only if Flight + Hotel succeeded
    budget_result = None
    if flight_result and hotel_result:
        budget_result = await run_agent(
            AgentName.budget,
            run_budget_agent(
                request,
                flight_result,
                hotel_result,
                itinerary_result or _empty_itinerary(),
            ),
        )
    else:
        failed_agents.append(AgentError(
            agent=AgentName.budget,
            message="Skipped — requires Flight and Hotel results",
        ))

    # Step 3: check if we have enough to build any plan
    if not any([flight_result, hotel_result, itinerary_result]):
        tlog.error("All agents failed")
        await push(ErrorEvent(
            message="All agents failed — unable to generate a trip plan. Please try again."
        ))
        return

    # Step 4: assemble plan with whatever succeeded
    plan = TripPlan(
        destination=request.destination,
        dates=f"{request.departureDate} – {request.returnDate}",
        flight=flight_result,
        hotel=hotel_result,
        itinerary=itinerary_result,
        budget=budget_result,
    )

    if failed_agents:
        tlog.warning(f"Plan partial — {len(failed_agents)} agent(s) failed")
        await push(PlanPartialEvent(data=plan, failed_agents=failed_agents))
    else:
        tlog.info("Plan complete")
        await push(PlanCompleteEvent(data=plan))


def _empty_itinerary() -> ItineraryArtifact:
    return ItineraryArtifact(days=[])