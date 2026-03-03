"""Configuration for the Tectonic OpenClaw bridge."""

from pydantic_settings import BaseSettings


class BridgeConfig(BaseSettings):
    """Bridge configuration loaded from environment variables.

    Environment variables are prefixed with ``TECTONIC_``.

    Examples::

        export TECTONIC_API_URL=http://localhost:8000
        export TECTONIC_API_KEY=tec_abc123
        export TECTONIC_AGENT_ID=550e8400-e29b-41d4-a716-446655440000
    """

    api_url: str = "http://localhost:8000"
    api_key: str = ""
    agent_id: str = ""

    model_config = {"env_prefix": "TECTONIC_"}


def get_config() -> BridgeConfig:
    """Return a BridgeConfig instance populated from the environment."""
    return BridgeConfig()
