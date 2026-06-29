# ─────────────────────────────────────────────────────────────
# agents/budget.py
# Runs last — consumes flight + hotel artifacts to compute
# the full trip budget breakdown.
# ─────────────────────────────────────────────────────────────

import os
import json
from models import (
    TripRequest, BudgetArtifact, BudgetBreakdown,
    FlightArtifact, HotelArtifact, ItineraryArtifact,
)
from constants import GROQ_MODEL, GEMINI_MODEL, MAX_TOKENS_DEFAULT

# pyrefly: ignore [missing-import]
from groq import AsyncGroq


# from google import genai
# from google.genai import types
# client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])


client = AsyncGroq(api_key=os.environ["GROQ_API_KEY"])

AGENT_CARD = {
    "name": "Budget Agent",
    "version": "1.0.0",
    "description": "Calculates a full trip budget breakdown from flight, hotel, and activity costs.",
    "url": "http://localhost:8000/agents/budget",
    "skills": ["budget-calculation", "cost-summary"],
    "inputSchema": {
        "budget":        {"type": "number",  "description": "User's total trip budget in USD"},
        "flightCost":    {"type": "number",  "description": "Recommended flight cost from Flight Agent"},
        "hotelCost":     {"type": "number",  "description": "Recommended hotel total from Hotel Agent"},
        "activityCosts": {"type": "array",   "description": "List of activity costs from Itinerary Agent"},
        "tripDays":      {"type": "integer", "description": "Number of trip days"},
    },
    "outputSchema": {
        "breakdown":      {"type": "object",  "description": "Cost breakdown by category"},
        "fitsBudget":     {"type": "boolean", "description": "Whether total fits within user budget"},
        "surplusDeficit": {"type": "number",  "description": "Positive = under budget, negative = over"},
    },
}



SYSTEM_PROMPT = """You are a travel budget specialist agent in a travel planning system.

Given actual flight costs, hotel costs, activity costs, and trip length,
return a complete budget breakdown as JSON.
Return ONLY a JSON object — no markdown, no explanation, no backticks.

Schema:
{
  "breakdown": {
    "flights": 840,
    "hotels": 675,
    "activities": 410,
    "dailyMisc": 350,
    "total": 2275
  },
  "fitsBudget": true,
  "surplusDeficit": 725
}

Rules:
- Use the exact flight and hotel costs provided — do not estimate them
- activities = sum of all activity estCostUsd across all days * number of travelers
- dailyMisc = estimated food, local transport, tips per day * number of days
- total = flights + hotels + activities + dailyMisc
- fitsBudget = total <= userBudget
- surplusDeficit = userBudget - total (positive = under budget, negative = over)
"""


async def run_budget_agent(
    request: TripRequest,
    flight: FlightArtifact,
    hotel: HotelArtifact,
    itinerary: ItineraryArtifact,
) -> BudgetArtifact:
    # Pull recommended options
    rec_flight = next(o for o in flight.options if o.id == flight.recommendedId)
    rec_hotel  = next(o for o in hotel.options  if o.id == hotel.recommendedId)

    # Sum activity costs from itinerary
    activity_total = sum(
        a.estCostUsd
        for day in itinerary.days
        for a in day.activities
    ) * request.travelers

    from datetime import date
    dep   = date.fromisoformat(request.departureDate)
    ret   = date.fromisoformat(request.returnDate)
    days  = (ret - dep).days

    user_message = (
        f"Trip to {request.destination} for {request.travelers} traveler(s), {days} days.\n"
        f"User budget: ${request.budget}\n"
        f"Flight cost (recommended): ${rec_flight.priceUsd}\n"
        f"Hotel cost (recommended, {days} nights): ${rec_hotel.totalCost}\n"
        f"Activities total (from itinerary): ${activity_total:.2f}\n"
        f"Calculate the full budget breakdown."
    )

    # response = await client.aio.models.generate_content(
    #     model=GEMINI_MODEL,
    #     config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
    #     contents=user_message,
    # )
    # raw = response.text.strip()

    response = await client.chat.completions.create(
        model=GROQ_MODEL,
        max_tokens=MAX_TOKENS_DEFAULT,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_message},
        ],
    )
    raw = response.choices[0].message.content.strip()       
    raw = raw.replace("```json", "").replace("```", "").strip() 
    data = json.loads(raw)

    return BudgetArtifact(
        breakdown=BudgetBreakdown(**data["breakdown"]),
        fitsBudget=data["fitsBudget"],
        surplusDeficit=data["surplusDeficit"],
    )