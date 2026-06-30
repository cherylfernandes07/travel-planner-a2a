# ─────────────────────────────────────────────────────────────
# agents/hotel.py
# ─────────────────────────────────────────────────────────────

import os
import json
from models import TripRequest, HotelArtifact, HotelOption

from constants import GROQ_MODEL, GEMINI_MODEL, MAX_TOKENS_DEFAULT

# pyrefly: ignore [missing-import]
from groq import AsyncGroq


# from google import genai
# from google.genai import types
# client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])


client = AsyncGroq(api_key=os.environ["GROQ_API_KEY"])

AGENT_CARD = {
    "name": "Hotel Agent",
    "version": "1.0.0",
    "description": "Finds hotel options given destination, dates, and budget.",
    "url": "http://localhost:8000/agents/hotel",
    "skills": ["hotel-search", "availability-check"],
    "inputSchema": {
        "destination":   {"type": "string",  "description": "City name"},
        "departureDate": {"type": "string",  "description": "Check-in date ISO 8601"},
        "returnDate":    {"type": "string",  "description": "Check-out date ISO 8601"},
        "budget":        {"type": "number",  "description": "Total trip budget in USD"},
        "travelers":     {"type": "integer", "description": "Number of guests"},
    },
    "outputSchema": {
        "options":       {"type": "array",  "description": "List of HotelOption objects"},
        "recommendedId": {"type": "string", "description": "ID of the best value option"},
    },
}


SYSTEM_PROMPT = """You are a hotel search specialist agent in a travel planning system.

Given a trip request, return realistic hotel options as JSON.
Return ONLY a JSON object — no markdown, no explanation, no backticks.

Schema:
{
  "options": [
    {
      "id": "h1",
      "name": "Shinjuku Granbell Hotel",
      "nightlyRate": 135,
      "totalCost": 675,
      "stars": 4,
      "neighborhood": "Shinjuku",
      "amenities": ["WiFi", "Gym", "Bar"]
    }
  ],
  "recommendedId": "h1"
}

Rules:
- Return 3 options: budget, recommended, luxury
- totalCost = nightlyRate * number of nights
- Use real neighborhoods for the destination city
- recommendedId should be the best value option
"""


async def run_hotel_agent(request: TripRequest) -> HotelArtifact:
    from datetime import date
    dep = date.fromisoformat(request.departureDate)
    ret = date.fromisoformat(request.returnDate)
    nights = (ret - dep).days

    user_message = (
        f"Find hotels in {request.destination}. "
        f"Check-in: {request.departureDate}, Check-out: {request.returnDate} ({nights} nights). "
        f"Guests: {request.travelers}. Budget: ${request.budget} total trip."
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
    # print(f"[hotel raw response]:\n{raw}\n")
    data = json.loads(raw)

    return HotelArtifact(
        options=[HotelOption(**o) for o in data["options"]],
        recommendedId=data["recommendedId"],
    )