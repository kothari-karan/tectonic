from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://tectonic:tectonic@localhost:5432/tectonic"
    API_SECRET_KEY: str = "dev-secret-key-change-in-production"
    SEPOLIA_RPC_URL: str | None = None
    ESCROW_CONTRACT_ADDRESS: str | None = None

    model_config = {"env_prefix": "TECTONIC_", "case_sensitive": False}


settings = Settings()
