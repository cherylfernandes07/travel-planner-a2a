# ─────────────────────────────────────────────────────────────
# agents/flight.py
# Calls Claude API with a flight-specialist system prompt.
# Returns a FlightArtifact matching the data contract.
# ─────────────────────────────────────────────────────────────

import os
import json
from models import TripRequest, FlightArtifact, FlightOption
from constants import GROQ_MODEL, GEMINI_MODEL, MAX_TOKENS_DEFAULT

# pyrefly: ignore [missing-import]
from groq import AsyncGroq


# from google import genai
# from google.genai import types
# client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])


client = AsyncGroq(api_key=os.environ["GROQ_API_KEY"])

AGENT_CARD = {
    "name": "Flight Agent",
    "version": "1.0.0",
    "description": "Searches for flight options given origin, destination, dates, and budget.",
    "url": "http://localhost:8000/agents/flight",
    "skills": ["flight-search", "price-lookup"],
    "inputSchema": {
        "origin":        {"type": "string",  "description": "IATA airport code e.g. SFO"},
        "destination":   {"type": "string",  "description": "City or IATA code e.g. Tokyo"},
        "departureDate": {"type": "string",  "description": "ISO 8601 date e.g. 2025-10-15"},
        "returnDate":    {"type": "string",  "description": "ISO 8601 date"},
        "budget":        {"type": "number",  "description": "Total trip budget in USD"},
        "travelers":     {"type": "integer", "description": "Number of travelers"},
    },
    "outputSchema": {
        "options":       {"type": "array",  "description": "List of FlightOption objects"},
        "recommendedId": {"type": "string", "description": "ID of the best value option"},
    },
}


SYSTEM_PROMPT = """You are a flight search specialist agent in a travel planning system.

Given a trip request, return realistic flight options as JSON.
Return ONLY a JSON object — no markdown, no explanation, no backticks.

Schema:
{
  "options": [
    {
      "id": "f1",
      "airline": "ANA NH006",
      "priceUsd": 840,
      "durationMins": 690,
      "stops": 0,
      "bookingUrl": "https://example.com/book"
    }
  ],
  "recommendedId": "f1"
}

Rules:
- Return 3 options: one budget, one recommended, one premium
- recommendedId should be the best value option
- Use realistic airline names, prices, and durations for the route
- nonstop flights have stops: 0
"""


async def run_flight_agent(request: TripRequest) -> FlightArtifact:
    user_message = (
        f"Find flights from {request.origin} to {request.destination}. "
        f"Departure: {request.departureDate}, Return: {request.returnDate}. "
        f"Travelers: {request.travelers}. Budget: ${request.budget} total trip."
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
    # print(f"[flight raw response]:\n{raw}\n")
    data = json.loads(raw)

    return FlightArtifact(
        options=[FlightOption(**o) for o in data["options"]],
        recommendedId=data["recommendedId"],
    )