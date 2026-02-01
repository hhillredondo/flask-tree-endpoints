from functools import wraps
from typing import Iterable, Optional, Set

from flask import jsonify, request, g, current_app

from auth.utils import get_current_user_id
from partition.middleware import get_current_tree_id
from .acl_store import ROLE_EDITOR, ROLE_OWNER, ROLE_VIEWER
from .service import get_user_role
from metrics import increment

_READ_METHODS = {"GET", "HEAD", "OPTIONS"}
_WRITE_METHODS = {"POST", "PUT", "PATCH"}
_DELETE_METHODS = {"DELETE"}


def _default_allowed_roles(method: str) -> Set[str]:
    if method in _DELETE_METHODS:
        return {ROLE_OWNER, ROLE_EDITOR}
    if method in _WRITE_METHODS:
        return {ROLE_OWNER, ROLE_EDITOR}
    return {ROLE_OWNER, ROLE_EDITOR, ROLE_VIEWER}


def require_role(required_roles: Optional[Iterable[str]] = None):
    """Decorator to enforce tree role access for the current request."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
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

            allowed_roles = set(required_roles) if required_roles else _default_allowed_roles(request.method)
            role = get_user_role(tree_id, user_id)

            if not role:
                current_app.logger.warning(
                    f"No ACL entry for user {user_id} on tree {tree_id}"
                )
                increment("auth_failure", {"reason": "missing_role"})
                return jsonify({
                    "error": "Access denied",
                    "message": "You do not have access to this tree"
                }), 403

            if role not in allowed_roles:
                increment("auth_failure", {"reason": "role_denied", "role": role})
                return jsonify({
                    "error": "Access denied",
                    "message": "Insufficient role for this operation",
                    "role": role
                }), 403

            current_app.logger.info(
                "Role allowed",
                extra={
                    "user_id": user_id,
                    "tree_id": tree_id,
                    "role": role,
                    "allowed_roles": sorted(allowed_roles),
                    "method": request.method,
                    "path": request.path,
                },
            )
            g.current_role = role
            return f(*args, **kwargs)

        return decorated_function

    return decorator



