from functools import wraps
from typing import Optional
from flask import request, g, jsonify, current_app
from .manager import partition_manager
from auth.utils import get_current_user_id


class PartitionContext:
    """Request-scoped partition context"""
    
    def __init__(self, partition_key: str, user_id: str, tree_id: str):
        self.partition_key = partition_key
        self.user_id = user_id
        self.tree_id = tree_id
    
    def __str__(self):
        return f"PartitionContext(partition_key='{self.partition_key}', user_id='{self.user_id}', tree_id='{self.tree_id}')"


def set_partition_context(partition_key: str, user_id: str, tree_id: str):
    """Set partition context in Flask g"""
    g.partition_context = PartitionContext(partition_key, user_id, tree_id)
    current_app.logger.info(f"Set partition context: {g.partition_context}")


def get_current_partition() -> Optional[str]:
    """Get current partition key from Flask g context"""
    if hasattr(g, 'partition_context'):
        return g.partition_context.partition_key
    return None


def extract_partition_from_request() -> str:
    partition_key = request.headers.get('X-Partition-Key')
    if not partition_key:
        raise ValueError('X-Partition-Key header is required')
    return partition_key


def validate_partition_access(partition_key: str, user_id: str) -> bool:
    """Validate that a user has access to a specific partition"""
    if not partition_key:
        return False
    
    if not partition_manager.validate_partition_key(partition_key):
        return False
    
    if not partition_manager.user_owns_partition(user_id, partition_key):
        return False
    
    return True


def require_partition(f):
    """Decorator to require partition context for Flask routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get current user
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({
                'error': 'Authentication required',
                'message': 'User not authenticated'
            }), 401
        
        # Extract partition key from request
        partition_key = extract_partition_from_request()
        
        if not partition_key:
            return jsonify({
                'error': 'Partition required',
                'message': 'partition_key is required (X-Partition-Key header)'
            }), 400
        
        # Validate partition access
        if not validate_partition_access(partition_key, user_id):
            return jsonify({
                'error': 'Access denied',
                'message': 'You do not have access to this partition'
            }), 403
        
        # Parse partition key to get tree_id
        _, tree_id = partition_manager.parse_partition_key(partition_key)
        
        if not tree_id:
            return jsonify({
                'error': 'Invalid partition key',
                'message': 'Partition key format is invalid'
            }), 400
        
        # Set partition context
        set_partition_context(partition_key, user_id, tree_id)
        
        # Call the original function
        return f(*args, **kwargs)
    
    return decorated_function
