import os
import time
from typing import Dict, Optional, Tuple

from .store import editor_lock_store

_LOCK_TTL_SECONDS = int(os.getenv("LOCK_TTL_SECONDS", "300"))


def _expires_at(now: Optional[int] = None) -> int:
    current = now if now is not None else int(time.time())
    return current + _LOCK_TTL_SECONDS


def _is_expired(lock: Optional[Dict[str, str]], now: Optional[int] = None) -> bool:
    if not lock:
        return True
    expires_at = lock.get("expiresAt")
    if expires_at is None:
        return True
    current = now if now is not None else int(time.time())
    return int(expires_at) <= current


def get_editor_lock(tree_id: str) -> Optional[Dict[str, str]]:
    if not tree_id:
        return None
    lock = editor_lock_store.get_lock(tree_id)
    if _is_expired(lock):
        return None
    return lock


def acquire_editor_lock(tree_id: str, user_id: str) -> Tuple[bool, Optional[Dict[str, str]]]:
    if not tree_id or not user_id:
        return False, None

    now = int(time.time())
    lock = editor_lock_store.try_acquire(tree_id, user_id, _expires_at(now), now)
    if lock:
        return True, lock

    existing = editor_lock_store.get_lock(tree_id)
    if existing and existing.get("lockOwner") == user_id and not _is_expired(existing, now):
        return True, existing

    if _is_expired(existing, now):
        return False, None

    return False, existing


def release_editor_lock(tree_id: str, user_id: str) -> bool:
    if not tree_id or not user_id:
        return False
    return editor_lock_store.release_lock(tree_id, user_id)


def force_release_editor_lock(tree_id: str) -> bool:
    if not tree_id:
        return False
    return editor_lock_store.force_release(tree_id)

