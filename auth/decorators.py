from .middleware import require_auth


def auth_required(f):
    """Decorator to require authentication for Flask routes"""
    return require_auth(f)


# `admin_required`, `rate_limit`, `auth_optional` and `email_verified_required`
# used to live here. All were removed rather than kept as placeholders:
#
#   - `admin_required` read `g.current_user['cognito:groups']`, a claim that
#     extract_user_info never copied, so it could never succeed. It failed closed,
#     but it read like a working control.
#   - `rate_limit` returned the wrapped function unchanged, so decorating a route
#     with it advertised throttling that did not exist.
#
#   - `auth_optional` and `email_verified_required` were pass-through aliases with
#     no call sites. `require_email_verified` (their middleware counterpart) was a
#     working control that was simply never applied to a route; recover it from
#     git history if you decide to enforce verification.
#
# Re-add any of them only with a working implementation and a test that proves it.
