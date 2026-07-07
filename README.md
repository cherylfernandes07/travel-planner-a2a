# Travel Planner A2A

An AI-powered travel planning system built on **Google's Agent-to-Agent (A2A) protocol**.
A Planner agent orchestrates four specialized sub-agents — Flight, Hotel, Itinerary, and Budget —
each exposing a `/.well-known/agent-card.json` discovery endpoint per the A2A spec.

Results stream to the frontend over WebSockets as each agent completes, so users see
their plan build progressively in real time.

🚀 **[Live Demo](https://travel-planner-a2a-front-end.vercel.app)** · 🎥 **[Demo Video](https://youtu.be/KCTgk7MbkLE)**

---

## What makes this different from a standard multi-agent app

Most multi-agent systems wire agents together as internal function calls. This project
implements the A2A protocol properly:

- Each sub-agent exposes a `/.well-known/agent-card.json` endpoint describing its name,
  skills, input schema, and output schema
- The Planner discovers agents via these cards at startup — not hardcoded imports
- Tasks follow the A2A lifecycle: `submitted → working → completed → artifact returned`
- Typed Pydantic contracts enforce schema at every agent boundary — schema drift fails
  loudly at validation, not silently downstream

---

## Architecture

```
Browser (Next.js)
      │
      ├── POST /plan ──────────────────► FastAPI (Planner Agent)
      │                                        │
      │                              ┌─────────┼─────────┐
      │                              ▼         ▼         ▼
      │                          Flight     Hotel    Itinerary
      │                          Agent      Agent      Agent
      │                              │         │         │
      │                              └────┬────┘         │
      │                                   ▼              │
      │                              Budget Agent        │
      │                          (runs last, depends     │
      │                           on flight + hotel)     │
      │                                   │              │
      └── WS /ws/{session} ◄──────────────┴──────────────┘
          (live event stream)      Assembled TripPlan JSON
```

Each agent exposes:
- `GET /agents/{name}/.well-known/agent-card.json` — A2A agent discovery
- Internal async function called by the Planner via `asyncio.gather` for parallel dispatch

---

## Agent Cards

The Planner agent card is available at:

```
GET /.well-known/agent-card.json
```

Sub-agent cards:

```
GET /agents/flight/.well-known/agent-card.json
GET /agents/hotel/.well-known/agent-card.json
GET /agents/itinerary/.well-known/agent-card.json
GET /agents/budget/.well-known/agent-card.json
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14 · TypeScript · Tailwind CSS |
| Backend | Python · FastAPI · WebSockets |
| Agents | Groq (llama-3.1-8b-instant) |
| Protocol | Google A2A SDK v1.1.0 |
| Auth | Clerk (Google OAuth) |
| Database | NeonDB (serverless Postgres) |
| Cache / Rate limiting | Redis |
| Deployment | Railway (backend) · Vercel (frontend) |

---

## Features

- **Real-time agent activity feed** — watch each agent fire, complete, and return artifacts
- **A2A agent card discovery** — each agent self-describes via `/.well-known/agent-card.json`
- **Typed data contracts** — Pydantic models enforce schema at every agent boundary
- **Partial plan support** — if one agent fails, the plan assembles from what succeeded
- **Per-IP rate limiting** — Redis-backed, 5 requests/day on free tier
- **Trip persistence** — completed plans saved to NeonDB, retrievable by user
- **Auth** — Clerk JWT verified on every request, Google OAuth supported
- **Input validation** — XSS, SQL injection, date logic, budget bounds all validated
- **Structured logging** — every request traced with a `trace_id` across all agents
- **Error handling** — 10s agent timeouts, automatic retry on rate limits, graceful fallbacks

---

## Development phases

This project was built in 5 phases:

| Phase | What was built |
|---|---|
| 1 | Next.js frontend with mocked WebSocket events · FastAPI backend scaffolded · Groq agents |
| 2 | A2A task lifecycle · WebSocket event streaming · Agent card endpoints · Frontend ↔ backend integration |
| 3 | Rate limiting (Redis) · Error handling · Input validation · Clerk auth · NeonDB persistence · Structured logging |
| 4 | Railway deployment · Vercel deployment · Redis on Railway · Production CORS · CI/CD |
| 5 | README · Demo recording · Cost monitoring · Launch prep |

---

## Running locally

### Prerequisites
- Python 3.12+
- Node.js 20+
- Redis (`brew install redis`)
- Groq API key ([console.groq.com](https://console.groq.com))
- Clerk account ([clerk.com](https://clerk.com))
- NeonDB project ([neon.tech](https://neon.tech))

### 1. Clone and set up environment files

```bash
git clone https://github.com/your-username/travel-planner-a2a.git
cd travel-planner-a2a
```

Copy the example env files and fill in your values:

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
```

### 2. Start Redis

```bash
brew services start redis
```

### 3. Start the backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 4. Start the frontend

```bash
cd frontend
nvm use 20.19.6
npm install
npm run dev
```

The app will be available at [http://localhost:3000](http://localhost:3000).

---

## Testing

```bash
cd backend
./.venv/bin/python -m pytest tests/test_input_validation.py -v
```

Security tests cover XSS injection, SQL injection, date logic, budget bounds,
and traveler count validation.

---

## Planned

- [ ] Real flight and hotel data via Amadeus API
- [ ] Split sub-agents into separate Railway services (true A2A HTTP task dispatch)
- [ ] Redis pub/sub for multi-instance WebSocket support
- [ ] Per-agent auth and quota management
- [ ] Voice input via speech-to-text
- [ ] RAGAS evaluation for agent output quality

---

## Author

Built by [Cheryl Fernandes](https://github.com/your-username) · [Nirvaan Labs](https://nirvaan.dev)