"""
Minimal web3.py wrapper for blockchain interactions.
For POC, mostly pass-through / validation only.
"""

from app.config import settings


async def verify_transaction(tx_hash: str) -> dict:
    """
    Verify that a transaction exists on Sepolia.

    For POC, this performs basic validation and returns a result.
    In production, this would use web3.py to query the actual chain.
    """
    if not tx_hash or not tx_hash.startswith("0x"):
        return {
            "valid": False,
            "error": "Invalid transaction hash format. Must start with 0x.",
        }

    if len(tx_hash) != 66:
        return {
            "valid": False,
            "error": "Invalid transaction hash length. Must be 66 characters.",
        }

    if not settings.SEPOLIA_RPC_URL:
        # POC mode: accept the transaction without on-chain verification
        return {
            "valid": True,
            "tx_hash": tx_hash,
            "verified_on_chain": False,
            "message": "Transaction accepted (POC mode - no RPC configured)",
        }

    # If RPC is configured, attempt verification via web3
    try:
        from web3 import Web3
        from web3.providers import HTTPProvider

        w3 = Web3(HTTPProvider(settings.SEPOLIA_RPC_URL))

        if not w3.is_connected():
            return {
                "valid": True,
                "tx_hash": tx_hash,
                "verified_on_chain": False,
                "message": "RPC connection failed, accepting transaction in POC mode",
            }

        tx = w3.eth.get_transaction(tx_hash)
        if tx is None:
            return {
                "valid": False,
                "error": "Transaction not found on chain",
            }

        return {
            "valid": True,
            "tx_hash": tx_hash,
            "verified_on_chain": True,
            "block_number": tx.get("blockNumber"),
            "from_address": tx.get("from"),
            "to_address": tx.get("to"),
            "value": str(tx.get("value", 0)),
        }
    except Exception as e:
        # Graceful fallback for POC
        return {
            "valid": True,
            "tx_hash": tx_hash,
            "verified_on_chain": False,
            "message": f"Chain verification failed ({str(e)}), accepting in POC mode",
        }


def validate_address(address: str) -> bool:
    """Validate an Ethereum address format."""
    if not address or not address.startswith("0x"):
        return False
    if len(address) != 42:
        return False
    try:
        int(address, 16)
        return True
    except ValueError:
        return False
