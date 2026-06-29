
# 1. Start Redis
brew services start redis

# 2. Start FastAPI backend
cd backend
source .venv/bin/activate
uvicorn main:app --reload --port 8000

# 3. Start Next.js frontend (separate terminal)
cd frontend
nvm use 20.19.6 && npm run dev
