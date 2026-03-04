from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import (
    agents,
    agreements,
    bounties as engagements,
    contracts,
    listings,
    negotiations,
    proposals,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan handler: create tables on startup for dev."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="Tectonic Agent Commerce Protocol",
    description="API backend for agent-to-agent commerce on the Tectonic protocol",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS - allow all origins for POC
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(agents.router)
app.include_router(engagements.router)
app.include_router(proposals.router)
app.include_router(negotiations.router)
app.include_router(contracts.router)
app.include_router(listings.router)
app.include_router(agreements.router)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "tectonic-api"}
