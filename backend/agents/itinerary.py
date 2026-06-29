# ─────────────────────────────────────────────────────────────
# agents/itinerary.py
# ─────────────────────────────────────────────────────────────

import os
import json
from models import TripRequest, ItineraryArtifact, Day, Activity
from constants import GROQ_MODEL, GEMINI_MODEL, MAX_TOKENS_ITINERARY

# pyrefly: ignore [missing-import]
from groq import AsyncGroq


# from google import genai
# from google.genai import types
# client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])


client = AsyncGroq(api_key=os.environ["GROQ_API_KEY"])

AGENT_CARD = {
    "name": "Itinerary Agent",
    "version": "1.0.0",
    "description": "Generates a day-by-day activity itinerary based on destination and interests.",
    "url": "http://localhost:8000/agents/itinerary",
    "skills": ["itinerary-generation", "activity-recommendation"],
    "inputSchema": {
        "destination":   {"type": "string",  "description": "City name"},
        "departureDate": {"type": "string",  "description": "Arrival date ISO 8601"},
        "returnDate":    {"type": "string",  "description": "Departure date ISO 8601"},
        "travelers":     {"type": "integer", "description": "Number of travelers"},
        "interests":     {"type": "array",   "description": "List of interests e.g. food, culture"},
    },
    "outputSchema": {
        "days": {"type": "array", "description": "List of Day objects with themed activities"},
    },
}

SYSTEM_PROMPT = """You are an itinerary planning specialist agent in a travel planning system.

Given a trip request, return a detailed day-by-day itinerary as JSON.
Return ONLY a JSON object — no markdown, no explanation, no backticks.

Schema:
{
  "days": [
    {
      "day": 1,
      "theme": "Arrive + Shinjuku",
      "activities": [
        {
          "time": "18:00",
          "name": "Check in and evening walk",
          "estCostUsd": 20
        }
      ]
    }
  ]
}

Rules:
- One object per day of the trip
- 3-4 activities per day
- theme should be a short evocative title for the day
- time in 24h format HH:MM
- estCostUsd is per person in USD (0 for free activities)
- Tailor activities to the traveler's interests
"""


async def run_itinerary_agent(request: TripRequest) -> ItineraryArtifact:
    from datetime import date
    dep = date.fromisoformat(request.departureDate)
    ret = date.fromisoformat(request.returnDate)
    days = (ret - dep).days

    interests = ", ".join(request.interests) if request.interests else "general sightseeing"

    user_message = (
        f"Create a {days}-day itinerary for {request.destination}. "
        f"Arrival: {request.departureDate}, Departure: {request.returnDate}. "
        f"Travelers: {request.travelers}. Interests: {interests}."
    )

    # response = await client.aio.models.generate_content(
    #     model=GEMINI_MODEL,
    #     config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
    #     contents=user_message,
    # )
    # raw = response.text.strip()

    response = await client.chat.completions.create(
        model=GROQ_MODEL,
        max_tokens=MAX_TOKENS_ITINERARY,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_message},
        ],
    )
    raw = response.choices[0].message.content.strip() 
    raw = raw.replace("```json", "").replace("```", "").strip() 
    data = json.loads(raw)

    return ItineraryArtifact(
        days=[
            Day(
                day=d["day"],
                theme=d["theme"],
                activities=[Activity(**a) for a in d["activities"]],
            )
            for d in data["days"]
        ]
    )