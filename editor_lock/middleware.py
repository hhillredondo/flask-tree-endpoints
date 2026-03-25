from functools import wraps
from typing import Optional

from flask import current_app, jsonify, request

from auth.utils import get_current_user_id
from partition.middleware import get_current_tree_id

from .service import get_editor_lock

_WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def _extract_lock_owner(lock: Optional[dict]) -> Optional[str]:
    if not lock:
        return None
    return lock.get("lockOwner")


def require_editor_lock(f):
    """Require the current user to hold the editor lock for write operations."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method not in _WRITE_METHODS:
            return f(*args, **kwargs)

        user_id = get_current_user_id()
        tree_id = get_current_tree_id()

        if not user_id:
            return jsonify({
                "error": "Authentication required",
                "message": "User not authenticated"
            }), 401

        if not tree_id:
            return jsonify({
                "error": "Partition required",
                "message": "tree_id missing from partition context"
            }), 400

        lock = get_editor_lock(tree_id)
        lock_owner = _extract_lock_owner(lock)

        if not lock_owner:
            return jsonify({
                "error": "Editor lock required",
                "message": "Acquire the editor lock before modifying the tree"
            }), 409

        if lock_owner != user_id:
            current_app.logger.info(
                "Editor lock denied",
                extra={
                    "user_id": user_id,
                    "tree_id": tree_id,
                    "lock_owner": lock_owner,
                    "method": request.method,
                    "path": request.path,
                },
            )
            return jsonify({
                "error": "Editor locked",
                "message": "Another user currently holds the editor lock",
                "lock_owner": lock_owner,
            }), 409

        return f(*args, **kwargs)

    return decorated_function

