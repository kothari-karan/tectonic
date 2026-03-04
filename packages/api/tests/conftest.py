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
from app.models.bounty import Engagement, EngagementStatus, EngagementType
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
        engagements_posted=0,
        engagements_completed=0,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(agent)
    await db.flush()
    await db.refresh(agent)
    return agent, api_key


async def create_test_engagement(
    db: AsyncSession,
    requester: Agent,
    title: str = "Test Engagement",
    description: str = "A test engagement description",
    category: str = "testing",
    reward_amount: float = 1.0,
    status: EngagementStatus = EngagementStatus.open,
    deadline: datetime | None = None,
    engagement_type: EngagementType = EngagementType.open,
    target_provider_ids: list[str] | None = None,
) -> Engagement:
    """Create a test engagement."""
    if deadline is None:
        deadline = datetime.now(timezone.utc) + timedelta(days=7)

    engagement = Engagement(
        id=uuid.uuid4(),
        title=title,
        description=description,
        acceptance_criteria=["Criterion 1", "Criterion 2"],
        category=category,
        reward_amount=reward_amount,
        reward_token="ETH",
        requester_id=requester.id,
        status=status,
        engagement_type=engagement_type,
        target_provider_ids=target_provider_ids,
        deadline=deadline,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(engagement)
    await db.flush()
    await db.refresh(engagement)
    return engagement


async def create_test_proposal(
    db: AsyncSession,
    engagement: Engagement,
    provider: Agent,
    proposed_price: float = 0.8,
    status: ProposalStatus = ProposalStatus.pending,
) -> Proposal:
    """Create a test proposal."""
    proposal = Proposal(
        id=uuid.uuid4(),
        engagement_id=engagement.id,
        provider_id=provider.id,
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
    engagement: Engagement,
    proposal: Proposal,
    requester: Agent,
    provider: Agent,
    status: NegotiationStatus = NegotiationStatus.active,
    turn_count: int = 0,
    current_terms: dict | None = None,
) -> Negotiation:
    """Create a test negotiation."""
    negotiation = Negotiation(
        id=uuid.uuid4(),
        engagement_id=engagement.id,
        proposal_id=proposal.id,
        requester_id=requester.id,
        provider_id=provider.id,
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
