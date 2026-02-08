from flask import Flask, jsonify, request, g
from flask_cors import CORS
from composed.children.create_child import create_child
from composed.parents.create_parent import create_parent
from composed.spouses.update_spouse_relation import update_spouse_relation
from composed.spouses.create_spouse import create_spouse
from composed.trees.create_tree import create_tree
from composed.trees.delete_tree import delete_tree
from composed.trees.list_trees import list_user_trees, list_owned_trees
from gremlin_connection import create_gremlin_connection
from members.update_member import update_member_query
from members.upload_member_media import (
    upload_member_pic,
    upload_member_photos,
    get_member_pic_url,
    get_member_photo_urls,
)
from members.get_member import (
    get_direct_relations_query,
    get_member_query,
    get_all_members_query,
)
from members.delete_member import delete_member_query
from auth.decorators import auth_required
from auth.utils import get_current_user_id, get_current_user_info
from partition.middleware import require_partition, get_current_partition
from roles.acl_store import ROLE_OWNER, ROLE_EDITOR
from roles.handlers import list_roles, add_role, remove_role
from roles.middleware import require_role
from editor_lock.handlers import (
    get_lock_status,
    acquire_lock,
    release_lock,
    force_release_lock,
)
from editor_lock.middleware import require_editor_lock
from config.settings import get_config
from metrics import snapshot
import logging
import os

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
        g.V().limit(1).toList()
        return jsonify({
            "status": "healthy",
            "message": "Flask API is running",
            "gremlin_connection": "connected"
        }), 200
    except Exception as e:
        logger.exception("Health check failed")
        debug_info = {
            "gremlin_endpoint": os.getenv("GREMLIN_ENDPOINT"),
            "gremlin_port": os.getenv("GREMLIN_PORT"),
            "gremlin_ssl": os.getenv("GREMLIN_SSL"),
            "gremlin_iam_auth": os.getenv("GREMLIN_IAM_AUTH"),
            "aws_region": os.getenv("AWS_REGION"),
            "aws_default_region": os.getenv("AWS_DEFAULT_REGION"),
        }
        return jsonify({
            "status": "unhealthy",
            "message": "Flask API is running but Gremlin connection failed",
            "error": str(e),
            "error_type": type(e).__name__,
            "debug": debug_info
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
    """Get all trees for the current user (owner/editor/viewer)."""
    try:
        user_id = get_current_user_id()
        logger.info(f"Get user trees for user {user_id}")
        return list_user_trees(g)
    except Exception as e:
        logger.error(f"Error getting user trees: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/myTrees", methods=["GET"])
@auth_required
def get_owned_trees():
    """Get trees owned by the current user (legacy behavior)."""
    try:
        user_id = get_current_user_id()
        logger.info(f"Get owned trees for user {user_id}")
        return list_owned_trees(g)
    except Exception as e:
        logger.error(f"Error getting owned trees: {e}")
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


# Owner-only destructive op: delete entire tree by partition
@app.route("/trees", methods=["DELETE"])
@auth_required
@require_partition
@require_role(required_roles=[ROLE_OWNER])
def delete_existing_tree():
    """Delete a tree (owner-only, requires partition_key header)."""
    try:
        data = request.get_json() or {}
        user_id = get_current_user_id()
        partition_key = get_current_partition()
        logger.info(f"Delete tree by user {user_id} (partition: {partition_key})")
        return delete_tree(g, data)
    except Exception as e:
        logger.error(f"Error deleting tree: {e}")
        return jsonify({"error": str(e)}), 500


# Metrics endpoint (auth-required)
@app.route("/metrics", methods=["GET"])
@auth_required
def get_metrics():
    """Return in-memory auth/role metrics."""
    return jsonify({"metrics": snapshot()}), 200


# Partitioned Endpoints (require partition_key in header)
@app.route("/member", methods=["GET", "PUT", "DELETE"])
@auth_required
@require_partition
@require_role()
@require_editor_lock
def member():
    """Member CRUD operations - requires partition_key in header"""
    data = request.get_json()
    user_id = get_current_user_id()
    partition_key = get_current_partition()
    logger.info(f"Member operation by user {user_id} (partition: {partition_key}): {request.method}")
    
    if request.method == "DELETE":
        return delete_member_query(g, data)
    elif request.method == "GET":
        return get_member_query(g, data)
    elif request.method == "PUT":
        return update_member_query(g, data)


@app.route("/member/pic", methods=["POST"])
@auth_required
@require_partition
@require_role()
@require_editor_lock
def upload_member_pic_route():
    """Upload and store a member profile pic (24x24px)."""
    return upload_member_pic(g, request)


@app.route("/member/photos", methods=["POST"])
@auth_required
@require_partition
@require_role()
@require_editor_lock
def upload_member_photos_route():
    """Upload and store member photos (original size)."""
    return upload_member_photos(g, request)


@app.route("/member/pic-url", methods=["GET"])
@auth_required
@require_partition
@require_role()
def get_member_pic_url_route():
    """Get a presigned URL for a member profile pic."""
    return get_member_pic_url(g, request)


@app.route("/member/photos-urls", methods=["GET"])
@auth_required
@require_partition
@require_role()
def get_member_photo_urls_route():
    """Get presigned URLs for a member's photos."""
    return get_member_photo_urls(g, request)


@app.route("/members", methods=["GET"])
@auth_required
@require_partition
@require_role()
def get_members():
    """Get all members - requires partition_key in header"""
    user_id = get_current_user_id()
    partition_key = get_current_partition()
    logger.info(f"Get all members by user {user_id} (partition: {partition_key})")
    return get_all_members_query(g)


@app.route("/memberDirectRelations", methods=["GET"])
@auth_required
@require_partition
@require_role()
def get_direct_relations():
    """Get direct relations for a member - requires partition_key in header"""
    data = request.get_json()
    user_id = get_current_user_id()
    partition_key = get_current_partition()
    logger.info(f"Get direct relations by user {user_id} (partition: {partition_key})")
    return get_direct_relations_query(g, data)


@app.route("/child", methods=["POST"])
@auth_required
@require_partition
@require_role()
@require_editor_lock
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
@require_role()
@require_editor_lock
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
@require_role()
@require_editor_lock
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


@app.route("/roles", methods=["GET"])
@auth_required
@require_partition
@require_role(required_roles=[ROLE_OWNER])
def get_roles():
    """List roles for a tree (owner-only)."""
    return list_roles()


@app.route("/roles", methods=["POST"])
@auth_required
@require_partition
@require_role(required_roles=[ROLE_OWNER])
def create_role():
    """Owner adds editor/viewer role to a user."""
    return add_role()


@app.route("/roles", methods=["DELETE"])
@auth_required
@require_partition
@require_role(required_roles=[ROLE_OWNER])
def delete_role():
    """Owner removes editor/viewer role from a user."""
    return remove_role()


@app.route("/editor-lock", methods=["GET"])
@auth_required
@require_partition
@require_role(required_roles=[ROLE_OWNER, ROLE_EDITOR])
def get_editor_lock_status():
    """Get current editor lock status for a tree."""
    return get_lock_status()


@app.route("/editor-lock", methods=["POST"])
@auth_required
@require_partition
@require_role(required_roles=[ROLE_OWNER, ROLE_EDITOR])
def acquire_editor_lock():
    """Acquire editor lock for a tree."""
    return acquire_lock()


@app.route("/editor-lock", methods=["DELETE"])
@auth_required
@require_partition
@require_role(required_roles=[ROLE_OWNER, ROLE_EDITOR])
def release_editor_lock():
    """Release editor lock for a tree."""
    return release_lock()


@app.route("/editor-lock/force", methods=["POST"])
@auth_required
@require_partition
@require_role(required_roles=[ROLE_OWNER])
def force_release_editor_lock():
    """Owner-only force release editor lock for a tree."""
    return force_release_lock()


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
    # This only runs when using Flask's dev server (python app.py)
    # Gunicorn imports app directly, so this won't run in production
    logger.info("Starting Flask application (development mode)...")
    logger.info(f"Environment: {app.config.get('FLASK_ENV', 'development')}")
    logger.info(f"Debug mode: {app.config.get('DEBUG', False)}")
    logger.info(f"CORS origins: {app.config.get('CORS_ORIGINS', [])}")
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=app.config.get('DEBUG', False)
    )
else:
    # This runs when imported by Gunicorn
    logger.info("Flask app loaded by Gunicorn (production mode)")
