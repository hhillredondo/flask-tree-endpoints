from functools import wraps
from flask import jsonify, g
from .middleware import require_auth, optional_auth, require_email_verified


def auth_required(f):
    """Decorator to require authentication for Flask routes"""
    return require_auth(f)


def auth_optional(f):
    """Decorator for optional authentication - sets user context if token is valid"""
    return optional_auth(f)


def email_verified_required(f):
    """Decorator to require email verification"""
    return require_email_verified(f)


def admin_required(f):
    """Decorator to require admin privileges (placeholder for future use)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # First require authentication
        from .middleware import authenticate_request
        is_authenticated, result = authenticate_request()
        
        if not is_authenticated:
            return jsonify({
                'error': 'Authentication required',
                'message': result
            }), 401
        
        # Check if user is admin (placeholder logic)
        # You can implement admin logic based on user groups or custom attributes
        user_groups = g.current_user.get('cognito:groups', [])
        if 'admin' not in user_groups:
            return jsonify({
                'error': 'Admin access required',
                'message': 'You do not have permission to access this resource'
            }), 403
        
        # Call the original function
        return f(*args, **kwargs)
    
    return decorated_function


def rate_limit(max_requests=100, window_seconds=3600):
    """Decorator for rate limiting (placeholder for future use)"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Placeholder for rate limiting logic
            # You can implement Redis-based rate limiting here
            return f(*args, **kwargs)
        return decorated_function
    return decorator
