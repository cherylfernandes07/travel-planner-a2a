# backend/constants.py

GEMINI_MODEL = "gemini-3.5-flash"  # update to whatever model worked
GROQ_MODEL = "llama-3.1-8b-instant" 

MAX_TOKENS_DEFAULT = 1000
MAX_TOKENS_ITINERARY = 4000  # itinerary needs much more room
AGENT_TIMEOUT_SECONDS = 10