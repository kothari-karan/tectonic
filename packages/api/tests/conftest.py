import uuid
from datetime import datetime, timezone, timedelta
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.auth.api_key import generate_api_key, hash_api_key
from app.models.agent import Agent, AgentType
from app.models.bounty import Bounty, BountyStatus
from app.models.proposal import Proposal, ProposalStatus
from app.models.negotiation import Negotiation, NegotiationStatus
from app.models.contract import Contract, ContractStatus
from app.models.reputation import ReputationEvent, ReputationEventType

# Use SQLite for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionFactory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create tables and provide a test database session."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionFactory() as session:
        try:
            yield session
        finally:
            await session.rollback()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create a test HTTP client with overridden DB dependency."""
    from app.main import app

    async def override_get_db():
        try:
            yield db_session
        except Exception:
            await db_session.rollback()
            raise

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


async def create_test_agent(
    db: AsyncSession,
    name: str = "test-agent",
    agent_type: AgentType = AgentType.both,
    wallet_address: str | None = "0x1234567890abcdef1234567890abcdef12345678",
    capabilities: list | None = None,
) -> tuple[Agent, str]:
    """Create a test agent and return (agent, plaintext_api_key)."""
    api_key = generate_api_key()
    api_key_hashed = hash_api_key(api_key)

    agent = Agent(
        id=uuid.uuid4(),
        name=name,
        agent_type=agent_type,
        wallet_address=wallet_address,
        api_key_hash=api_key_hashed,
        capabilities=capabilities or ["testing"],
        reputation_score=0.0,
        bounties_posted=0,
        bounties_completed=0,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(agent)
    await db.flush()
    await db.refresh(agent)
    return agent, api_key


async def create_test_bounty(
    db: AsyncSession,
    poster: Agent,
    title: str = "Test Bounty",
    description: str = "A test bounty description",
    category: str = "testing",
    reward_amount: float = 1.0,
    status: BountyStatus = BountyStatus.open,
    deadline: datetime | None = None,
) -> Bounty:
    """Create a test bounty."""
    if deadline is None:
        deadline = datetime.now(timezone.utc) + timedelta(days=7)

    bounty = Bounty(
        id=uuid.uuid4(),
        title=title,
        description=description,
        acceptance_criteria=["Criterion 1", "Criterion 2"],
        category=category,
        reward_amount=reward_amount,
        reward_token="ETH",
        poster_id=poster.id,
        status=status,
        deadline=deadline,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(bounty)
    await db.flush()
    await db.refresh(bounty)
    return bounty


async def create_test_proposal(
    db: AsyncSession,
    bounty: Bounty,
    solver: Agent,
    proposed_price: float = 0.8,
    status: ProposalStatus = ProposalStatus.pending,
) -> Proposal:
    """Create a test proposal."""
    proposal = Proposal(
        id=uuid.uuid4(),
        bounty_id=bounty.id,
        solver_id=solver.id,
        status=status,
        proposed_price=proposed_price,
        proposed_deadline=datetime.now(timezone.utc) + timedelta(days=5),
        approach_summary="Test approach summary",
        created_at=datetime.now(timezone.utc),
    )
    db.add(proposal)
    await db.flush()
    await db.refresh(proposal)
    return proposal


async def create_test_negotiation(
    db: AsyncSession,
    bounty: Bounty,
    proposal: Proposal,
    poster: Agent,
    solver: Agent,
    status: NegotiationStatus = NegotiationStatus.active,
    turn_count: int = 0,
    current_terms: dict | None = None,
) -> Negotiation:
    """Create a test negotiation."""
    negotiation = Negotiation(
        id=uuid.uuid4(),
        bounty_id=bounty.id,
        proposal_id=proposal.id,
        poster_id=poster.id,
        solver_id=solver.id,
        status=status,
        current_terms=current_terms,
        turn_count=turn_count,
        max_turns=10,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(negotiation)
    await db.flush()
    await db.refresh(negotiation)
    return negotiation
