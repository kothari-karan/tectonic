"""Tectonic OpenClaw Bridge - MCP-style tool functions for agent integration."""

from .config import BridgeConfig, get_config
from .tools import (
    tectonic_browse_engagements,
    tectonic_check_inbox,
    tectonic_fund_escrow,
    tectonic_list_proposals,
    tectonic_my_engagements,
    tectonic_my_reputation,
    tectonic_negotiate,
    tectonic_post_engagement,
    tectonic_review_delivery,
    tectonic_start_negotiation,
    tectonic_submit_delivery,
    tectonic_submit_proposal,
    tectonic_verify_delivery,
)

__all__ = [
    "BridgeConfig",
    "get_config",
    "tectonic_post_engagement",
    "tectonic_list_proposals",
    "tectonic_start_negotiation",
    "tectonic_negotiate",
    "tectonic_fund_escrow",
    "tectonic_review_delivery",
    "tectonic_verify_delivery",
    "tectonic_my_engagements",
    "tectonic_my_reputation",
    "tectonic_browse_engagements",
    "tectonic_check_inbox",
    "tectonic_submit_proposal",
    "tectonic_submit_delivery",
]
