from flask import Flask, jsonify, request, g
from flask_cors import CORS
from composed.children.create_child import create_child
from composed.parents.create_parent import create_parent
from composed.spouses.update_spouse_relation import update_spouse_relation
from composed.spouses.create_spouse import create_spouse
from composed.trees.create_tree import create_tree
from composed.trees.list_trees import list_user_trees
from gremlin_connection import create_gremlin_connection
from members.create_member import create_member_query
from members.update_member import update_member_query
from members.get_member import (
    get_direct_relations_query,
    get_member_query,
    get_all_members_query,
)
from members.delete_member import delete_member_query
from relations.create_relation import create_relation_query
from auth.decorators import auth_required
from auth.utils import get_current_user_id, get_current_user_info
from partition.middleware import require_partition, get_current_partition
from config.settings import get_config
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Load configuration
app.config.from_object(get_config())

# Configure CORS
CORS(app, origins=app.config['CORS_ORIGINS'], supports_credentials=True)

# Initialize Gremlin connection
g = create_gremlin_connection()


@app.route("/", methods=["GET"])
def health_check():
    """Health check endpoint - no authentication required"""
    try:
        # Test Gremlin connection
        vertex_count = g.V().count().next()
        return jsonify({
            "status": "healthy",
            "message": "Flask API is running",
            "gremlin_connection": "connected",
            "vertex_count": vertex_count
        }), 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            "status": "unhealthy",
            "message": "Flask API is running but Gremlin connection failed",
            "error": str(e)
        }), 500


@app.route("/auth/debug", methods=["GET"])
def debug_auth():
    """Debug authentication - shows what token we received"""
    try:
        auth_header = request.headers.get('Authorization')
        
        debug_info = {
            "auth_header_present": auth_header is not None,
            "auth_header_length": len(auth_header) if auth_header else 0,
            "auth_header_preview": auth_header[:50] + "..." if auth_header and len(auth_header) > 50 else auth_header,
            "starts_with_bearer": auth_header.startswith('Bearer ') if auth_header else False,
            "all_headers": dict(request.headers)
        }
        
        return jsonify(debug_info), 200
    except Exception as e:
        logger.error(f"Error in debug endpoint: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/auth/me", methods=["GET"])
@auth_required
def get_current_user():
    """Get current authenticated user information"""
    try:
        user_info = get_current_user_info()
        return jsonify({
            "user": user_info,
            "message": "Authentication successful"
        }), 200
    except Exception as e:
        logger.error(f"Error getting current user: {e}")
        return jsonify({"error": str(e)}), 500


# Tree Management Endpoints (no partition required)
@app.route("/trees", methods=["GET"])
@auth_required
def get_user_trees():
    """Get all trees for the current user"""
    try:
        user_id = get_current_user_id()
        logger.info(f"Get user trees for user {user_id}")
        return list_user_trees(g)
    except Exception as e:
        logger.error(f"Error getting user trees: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/trees", methods=["POST"])
@auth_required
def create_new_tree():
    """Create first member in a new tree (returns partition_key)"""
    try:
        data = request.get_json()
        user_id = get_current_user_id()
        logger.info(f"Create tree by user {user_id}")
        return create_tree(g, data)
    except Exception as e:
        logger.error(f"Error creating tree: {e}")
        return jsonify({"error": str(e)}), 500


# Partitioned Endpoints (require partition_key in header)
@app.route("/member", methods=["POST", "GET", "PUT", "DELETE"])
@auth_required
@require_partition
def member():
    """Member CRUD operations - requires partition_key in header"""
    data = request.get_json()
    user_id = get_current_user_id()
    partition_key = get_current_partition()
    logger.info(f"Member operation by user {user_id} (partition: {partition_key}): {request.method}")
    
    if request.method == "POST":
        return create_member_query(g, data)
    elif request.method == "DELETE":
        return delete_member_query(g, data)
    elif request.method == "GET":
        return get_member_query(g, data)
    elif request.method == "PUT":
        return update_member_query(g, data)


@app.route("/members", methods=["GET"])
@auth_required
@require_partition
def get_members():
    """Get all members - requires partition_key in header"""
    user_id = get_current_user_id()
    partition_key = get_current_partition()
    logger.info(f"Get all members by user {user_id} (partition: {partition_key})")
    return get_all_members_query(g)


@app.route("/memberDirectRelations", methods=["GET"])
@auth_required
@require_partition
def get_direct_relations():
    """Get direct relations for a member - requires partition_key in header"""
    data = request.get_json()
    user_id = get_current_user_id()
    partition_key = get_current_partition()
    logger.info(f"Get direct relations by user {user_id} (partition: {partition_key})")
    return get_direct_relations_query(g, data)


@app.route("/relation", methods=["POST"])
@auth_required
@require_partition
def create_relation():
    """Create a relation - requires partition_key in header"""
    data = request.get_json()
    user_id = get_current_user_id()
    partition_key = get_current_partition()
    logger.info(f"Create relation by user {user_id} (partition: {partition_key})")
    return create_relation_query(g, data)


@app.route("/child", methods=["POST"])
@auth_required
@require_partition
def child():
    """Create child relationship - requires partition_key in header"""
    data = request.get_json()
    user_id = get_current_user_id()
    partition_key = get_current_partition()
    logger.info(f"Create child by user {user_id} (partition: {partition_key})")
    return create_child(g, data)


@app.route("/parent", methods=["POST"])
@auth_required
@require_partition
def parent():
    """Create parent relationship - requires partition_key in header"""
    data = request.get_json()
    user_id = get_current_user_id()
    partition_key = get_current_partition()
    logger.info(f"Create parent by user {user_id} (partition: {partition_key})")
    return create_parent(g, data)


@app.route("/spouse", methods=["POST", "PUT"])
@auth_required
@require_partition
def spouse():
    """Spouse relationship operations - requires partition_key in header"""
    data = request.get_json()
    user_id = get_current_user_id()
    partition_key = get_current_partition()
    logger.info(f"Spouse operation by user {user_id} (partition: {partition_key}): {request.method}")
    if request.method == "POST":
        return create_spouse(g, data)
    elif request.method == "PUT":
        return update_spouse_relation(g, data)


@app.errorhandler(401)
def unauthorized(error):
    """Handle 401 Unauthorized errors"""
    return jsonify({
        "error": "Authentication required",
        "message": "Please provide a valid JWT token"
    }), 401


@app.errorhandler(403)
def forbidden(error):
    """Handle 403 Forbidden errors"""
    return jsonify({
        "error": "Access denied",
        "message": "You do not have permission to access this resource"
    }), 403


@app.errorhandler(404)
def not_found(error):
    """Handle 404 Not Found errors"""
    return jsonify({
        "error": "Not found",
        "message": "The requested resource was not found"
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 Internal Server errors"""
    logger.error(f"Internal server error: {error}")
    return jsonify({
        "error": "Internal server error",
        "message": "An unexpected error occurred"
    }), 500


if __name__ == "__main__":
    logger.info("Starting Flask application...")
    logger.info(f"Environment: {app.config.get('FLASK_ENV', 'development')}")
    logger.info(f"Debug mode: {app.config.get('DEBUG', False)}")
    logger.info(f"CORS origins: {app.config.get('CORS_ORIGINS', [])}")
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=app.config.get('DEBUG', False)
    )
