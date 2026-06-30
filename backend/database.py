# database.py
# NeonDB (serverless Postgres) setup and trip plan persistence.
# Uses SQLAlchemy async engine + asyncpg driver.

import os
import json
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy import Column, String, Text, DateTime, Integer
from sqlalchemy import text
import ssl



# ── Engine setup ──────────────────────────────────────────────
# NeonDB connection string uses postgresql:// — swap to
# postgresql+asyncpg:// for async support

DATABASE_URL = os.environ["DATABASE_URL"].replace(
    "postgresql://", "postgresql+asyncpg://"
)

# Strip sslmode param — asyncpg handles SSL differently
raw_url = os.environ["DATABASE_URL"].replace(
    "postgresql://", "postgresql+asyncpg://"
).split("?")[0]  # remove query params

# Create SSL context for NeonDB
ssl_context = ssl.create_default_context()

engine = create_async_engine(
    raw_url,
    echo=False,
    pool_size=5,
    max_overflow=10,
    connect_args={"ssl": ssl_context},
)

AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ── ORM Base ──────────────────────────────────────────────────

class Base(DeclarativeBase):
    pass


# ── Tables ────────────────────────────────────────────────────

class TripPlanRecord(Base):
    __tablename__ = "trip_plans"

    id           = Column(String, primary_key=True)   # uuid
    user_id      = Column(String, nullable=False)      # Clerk user ID
    destination  = Column(String, nullable=False)
    dates        = Column(String, nullable=False)
    plan_json    = Column(Text, nullable=False)         # full TripPlan as JSON
    status       = Column(String, default="complete")  # complete | partial
    created_at   = Column(DateTime, default=datetime.utcnow)


# ── Create tables on startup ──────────────────────────────────

async def init_db():
    """Create tables if they don't exist."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# ── CRUD ──────────────────────────────────────────────────────

async def save_trip_plan(
    plan_id: str,
    user_id: str,
    destination: str,
    dates: str,
    plan_data: dict,
    status: str = "complete",
) -> None:
    """Save a completed or partial trip plan to NeonDB."""
    async with AsyncSessionLocal() as session:
        record = TripPlanRecord(
            id=plan_id,
            user_id=user_id,
            destination=destination,
            dates=dates,
            plan_json=json.dumps(plan_data),
            status=status,
        )
        session.add(record)
        await session.commit()


async def get_user_trips(user_id: str) -> list[dict]:
    """Fetch all trip plans for a user, newest first."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            text("""
                SELECT id, destination, dates, plan_json, status, created_at
                FROM trip_plans
                WHERE user_id = :user_id
                ORDER BY created_at DESC
            """),
            {"user_id": user_id},
        )
        rows = result.fetchall()
        return [
            {
                "id":          row.id,
                "destination": row.destination,
                "dates":       row.dates,
                "plan":        json.loads(row.plan_json),
                "status":      row.status,
                "createdAt":   row.created_at.isoformat(),
            }
            for row in rows
        ]


async def get_trip_by_id(plan_id: str, user_id: str) -> dict | None:
    """Fetch a single trip plan — scoped to the user for security."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            text("""
                SELECT id, destination, dates, plan_json, status, created_at
                FROM trip_plans
                WHERE id = :plan_id AND user_id = :user_id
            """),
            {"plan_id": plan_id, "user_id": user_id},
        )
        row = result.fetchone()
        if not row:
            return None
        return {
            "id":          row.id,
            "destination": row.destination,
            "dates":       row.dates,
            "plan":        json.loads(row.plan_json),
            "status":      row.status,
            "createdAt":   row.created_at.isoformat(),
        }