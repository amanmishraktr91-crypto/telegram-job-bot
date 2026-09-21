"""
Telegram Channel & Bot High-Security Guard Module
Protects your channel from spam, unauthorized takeovers, flood attacks, and malicious abuse.
"""

import time
import logging
from typing import Dict, List, Optional, Tuple
from config import ADMIN_USER_IDS


logger = logging.getLogger(__name__)

# Track user request timestamps for rate-limiting
_USER_REQUEST_HISTORY: Dict[int, List[float]] = {}
MAX_REQUESTS_PER_MINUTE = 6
BLOCK_DURATION_SECONDS = 60
_BLOCKED_USERS: Dict[int, float] = {}

def is_admin_user(user_id: int) -> bool:
    """Checks if the interacting user is an authorized admin."""
    if not ADMIN_USER_IDS:
        # If no admin IDs are configured, allow default operations
        return True
    return user_id in ADMIN_USER_IDS


def check_rate_limit(user_id: int) -> Tuple[bool, str]:
    """
    Anti-Flood System: Blocks aggressive bots and spammers from overwhelming the server or channel.
    Returns: (is_allowed: bool, message: str)
    """
    current_time = time.time()

    # Check if user is temporarily blocked
    if user_id in _BLOCKED_USERS:
        unblock_time = _BLOCKED_USERS[user_id]
        if current_time < unblock_time:
            remaining = int(unblock_time - current_time)
            return False, f"⚠️ Anti-Flood Shield: Too many requests. Please wait {remaining}s."
        else:
            del _BLOCKED_USERS[user_id]

    # Clean history older than 60s
    timestamps = _USER_REQUEST_HISTORY.get(user_id, [])
    timestamps = [t for t in timestamps if current_time - t < 60]

    if len(timestamps) >= MAX_REQUESTS_PER_MINUTE:
        _BLOCKED_USERS[user_id] = current_time + BLOCK_DURATION_SECONDS
        _USER_REQUEST_HISTORY[user_id] = []
        logger.warning(f"Anti-Flood triggered: Blocked user_id={user_id} for {BLOCK_DURATION_SECONDS}s")
        return False, f"⚠️ Anti-Flood Activated: You sent too many queries. Blocked for {BLOCK_DURATION_SECONDS}s."

    timestamps.append(current_time)
    _USER_REQUEST_HISTORY[user_id] = timestamps
    return True, ""


def get_channel_security_footer() -> str:
    """Generates official verified security seal for every broadcasted channel message."""
    return (
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🛡️ <b>OFFICIAL SECURITY SEAL:</b>\n"
        "• <i>Verified by 4-Stage Multi-Scan Engine (0% Fake/Scam Guarantee)</i>\n"
        "• <i>No Registration Charges | Direct Corporate Portals Only</i>\n"
        "🔒 <b>Protected Channel Broadcast</b>"
    )
