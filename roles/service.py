import os
import time
from typing import Optional, Tuple

from flask import current_app

from .acl_store import acl_store

_CACHE_TTL_SECONDS = int(os.getenv("ROLE_CACHE_TTL_SECONDS", "30"))
_role_cache = {}


def _cache_key(tree_id: str, user_id: str) -> Tuple[str, str]:
    return tree_id, user_id


def get_user_role(tree_id: str, user_id: str) -> Optional[str]:
    """Fetch role from cache or DynamoDB."""
    if not tree_id or not user_id:
        return None

    key = _cache_key(tree_id, user_id)
    now = time.time()
    cached = _role_cache.get(key)

    if cached and cached["expires_at"] > now:
        return cached["role"]

    role = acl_store.get_role(tree_id, user_id)
    _role_cache[key] = {"role": role, "expires_at": now + _CACHE_TTL_SECONDS}
    return role


def invalidate_role_cache(tree_id: str, user_id: str) -> None:
    key = _cache_key(tree_id, user_id)
    if key in _role_cache:
        del _role_cache[key]


def clear_role_cache() -> None:
    _role_cache.clear()
    current_app.logger.debug("Cleared role cache")



