from functools import wraps
from flask import request, g, jsonify, current_app
from .utils import auth_utils


def extract_token_from_request() -> str:
    """Extract JWT token from request headers"""
    auth_header = request.headers.get('Authorization')
    
    if not auth_header:
        return None
    
    # Handle "Bearer <token>" format
    if auth_header.startswith('Bearer '):
        return auth_header[7:]  # Remove "Bearer " prefix
    
    # Handle just the token
    return auth_header


def authenticate_request():
    """Authenticate the current request and set user context"""
    try:
        # Extract token from request
        token = extract_token_from_request()
        
        if not token:
            current_app.logger.warning("No authorization token provided")
            return False, "No authorization token provided"
        
        # Validate token
        payload = auth_utils.validate_token(token)
        
        if not payload:
            current_app.logger.warning("Invalid or expired token")
            return False, "Invalid or expired token"
        
        # Extract user information
        user_info = auth_utils.extract_user_info(payload)
        
        # Set user context in Flask g
        g.current_user = user_info
        
        current_app.logger.info(f"Authenticated user: {user_info.get('email')}")
        return True, user_info
        
    except Exception as e:
        current_app.logger.error(f"Authentication error: {e}")
        return False, "Authentication failed"


def require_auth(f):
    """Decorator to require authentication for Flask routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Authenticate the request
        is_authenticated, result = authenticate_request()
        
        if not is_authenticated:
            return jsonify({
                'error': 'Authentication required',
                'message': result
            }), 401
        
        # Call the original function
        return f(*args, **kwargs)
    
    return decorated_function


def optional_auth(f):
    """Decorator for optional authentication - sets user context if token is valid"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Try to authenticate, but don't fail if no token
        token = extract_token_from_request()
        
        if token:
            is_authenticated, result = authenticate_request()
            if not is_authenticated:
                # Clear any invalid user context
                if hasattr(g, 'current_user'):
                    delattr(g, 'current_user')
        
        # Call the original function
        return f(*args, **kwargs)
    
    return decorated_function


def require_email_verified(f):
    """Decorator to require email verification"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # First require authentication
        is_authenticated, result = authenticate_request()
        
        if not is_authenticated:
            return jsonify({
                'error': 'Authentication required',
                'message': result
            }), 401
        
        # Check if email is verified
        if not g.current_user.get('email_verified', False):
            return jsonify({
                'error': 'Email verification required',
                'message': 'Please verify your email address before accessing this resource'
            }), 403
        
        # Call the original function
        return f(*args, **kwargs)
    
    return decorated_function
