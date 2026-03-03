import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import Agent
from app.models.reputation import ReputationEvent, ReputationEventType

# Reputation score weights
SCORE_WEIGHTS: dict[str, float] = {
    "bounty_completed": 10.0,
    "bounty_posted": 2.0,
    "dispute_won": 5.0,
    "dispute_lost": -10.0,
}


def calculate_score_delta(event_type: str) -> float:
    """Calculate score delta for a given event type."""
    return SCORE_WEIGHTS.get(event_type, 0.0)


async def record_event(
    agent_id: uuid.UUID,
    event_type: str,
    db: AsyncSession,
    contract_id: uuid.UUID | None = None,
) -> ReputationEvent:
    """Record a reputation event and update the agent's score."""
    score_delta = calculate_score_delta(event_type)

    event = ReputationEvent(
        agent_id=agent_id,
        event_type=ReputationEventType(event_type),
        contract_id=contract_id,
        score_delta=score_delta,
        created_at=datetime.now(timezone.utc),
    )
    db.add(event)

    # Update agent reputation score
    agent = await db.get(Agent, agent_id)
    if agent:
        agent.reputation_score += score_delta
        agent.updated_at = datetime.now(timezone.utc)

    await db.flush()
    return event


async def calculate_score(agent_id: uuid.UUID, db: AsyncSession) -> float:
    """Calculate an agent's total reputation score from all events."""
    result = await db.execute(
        select(ReputationEvent).where(ReputationEvent.agent_id == agent_id)
    )
    events = result.scalars().all()

    total = 0.0
    for event in events:
        total += event.score_delta

    return total


async def get_agent_reputation(
    agent_id: uuid.UUID, db: AsyncSession
) -> dict:
    """Get an agent's reputation details."""
    agent = await db.get(Agent, agent_id)
    if agent is None:
        return {"error": "Agent not found"}

    result = await db.execute(
        select(ReputationEvent)
        .where(ReputationEvent.agent_id == agent_id)
        .order_by(ReputationEvent.created_at.desc())
    )
    events = result.scalars().all()

    return {
        "agent_id": str(agent_id),
        "reputation_score": agent.reputation_score,
        "bounties_posted": agent.bounties_posted,
        "bounties_completed": agent.bounties_completed,
        "total_events": len(events),
        "recent_events": [
            {
                "id": str(e.id),
                "event_type": e.event_type.value,
                "score_delta": e.score_delta,
                "contract_id": str(e.contract_id) if e.contract_id else None,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in events[:10]
        ],
    }
