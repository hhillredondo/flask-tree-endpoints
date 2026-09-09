from .middleware import optional_auth, require_auth, require_email_verified


def auth_required(f):
    """Decorator to require authentication for Flask routes"""
    return require_auth(f)


def auth_optional(f):
    """Decorator for optional authentication - sets user context if token is valid"""
    return optional_auth(f)


def email_verified_required(f):
    """Decorator to require email verification"""
    return require_email_verified(f)


# `admin_required` and `rate_limit` used to live here. Both were removed rather
# than kept as placeholders:
#
#   - `admin_required` read `g.current_user['cognito:groups']`, a claim that
#     extract_user_info never copied, so it could never succeed. It failed closed,
#     but it read like a working control.
#   - `rate_limit` returned the wrapped function unchanged, so decorating a route
#     with it advertised throttling that did not exist.
#
# Re-add either only with a working implementation and a test that proves it.
