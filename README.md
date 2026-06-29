# Travel Planner A2A

An AI-powered travel planning app built with the **Agent-to-Agent (A2A) protocol**.
A planner agent orchestrates four specialized sub-agents — **Flight**, **Hotel**,
**Itinerary**, and **Budget** — running in parallel to generate a complete trip plan
in real time.

Results stream to the frontend over **WebSockets** as each agent completes, so users
see their plan build progressively rather than waiting for everything at once.

## Stack

- **Backend**: Python · FastAPI · Google Gemini · A2A SDK · Redis (rate limiting)
- **Frontend**: Next.js · TypeScript

---

## Getting Started

### 1. Start Redis
```bash
brew services start redis
```

### 2. Start the FastAPI backend
```bash
cd backend
source .venv/bin/activate
uvicorn main:app --reload --port 8000
```

### 3. Start the Next.js frontend _(separate terminal)_
```bash
cd frontend
nvm use 20.19.6 && npm run dev
```

The app will be available at [http://localhost:3000](http://localhost:3000).
