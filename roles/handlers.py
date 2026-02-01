from flask import jsonify, request, current_app

from auth.cognito import get_user_sub_by_email
from partition.middleware import get_current_tree_id
from .acl_store import ROLE_EDITOR, ROLE_VIEWER, ROLE_OWNER, acl_store
from .service import invalidate_role_cache


def list_roles():
    """List ACL entries for a tree (owner-only)."""
    try:
        tree_id = get_current_tree_id()
        if not tree_id:
            return jsonify({
                "error": "Partition required",
                "message": "tree_id missing from partition context"
            }), 400

        roles = acl_store.list_roles(tree_id)
        return jsonify({
            "tree_id": tree_id,
            "roles": roles,
            "count": len(roles)
        }), 200
    except Exception as exc:
        current_app.logger.exception(f"Error listing roles: {exc}")
        return jsonify({"error": "Failed to list roles"}), 500


def add_role():
    """Owner adds an editor/viewer role by email."""
    try:
        data = request.get_json() or {}
        email = data.get("email")
        role = data.get("role")
        tree_id = get_current_tree_id()

        if not tree_id:
            return jsonify({
                "error": "Partition required",
                "message": "tree_id missing from partition context"
            }), 400

        if role not in {ROLE_EDITOR, ROLE_VIEWER}:
            return jsonify({
                "error": "Invalid role",
                "message": "role must be editor or viewer"
            }), 400

        if not email:
            return jsonify({
                "error": "Missing email",
                "message": "email is required"
            }), 400

        target_user_id = get_user_sub_by_email(email)
        if not target_user_id:
            return jsonify({
                "error": "User not found",
                "message": "No Cognito user found for this email"
            }), 404

        existing_role = acl_store.get_role(tree_id, target_user_id)
        if existing_role == ROLE_OWNER:
            return jsonify({
                "error": "Invalid operation",
                "message": "Owner role cannot be changed"
            }), 400

        success = acl_store.put_role(tree_id, target_user_id, role)
        if not success:
            return jsonify({
                "error": "Role assignment failed",
                "message": "Could not assign role"
            }), 500

        invalidate_role_cache(tree_id, target_user_id)

        return jsonify({
            "message": "Role assigned",
            "tree_id": tree_id,
            "user_id": target_user_id,
            "role": role
        }), 200
    except Exception as exc:
        current_app.logger.exception(f"Error adding role: {exc}")
        return jsonify({"error": "Failed to assign role"}), 500


def remove_role():
    """Owner removes a role by email or user_id."""
    try:
        data = request.get_json() or {}
        email = data.get("email")
        target_user_id = data.get("user_id")
        tree_id = get_current_tree_id()

        if not tree_id:
            return jsonify({
                "error": "Partition required",
                "message": "tree_id missing from partition context"
            }), 400

        if not target_user_id and email:
            target_user_id = get_user_sub_by_email(email)

        if not target_user_id:
            return jsonify({
                "error": "Missing user",
                "message": "email or user_id is required"
            }), 400

        existing_role = acl_store.get_role(tree_id, target_user_id)
        if not existing_role:
            return jsonify({
                "error": "User not found",
                "message": "No role entry for that user"
            }), 404

        if existing_role == ROLE_OWNER:
            return jsonify({
                "error": "Invalid operation",
                "message": "Owner role cannot be removed"
            }), 400

        success = acl_store.delete_role(tree_id, target_user_id)
        if not success:
            return jsonify({
                "error": "Role removal failed",
                "message": "Could not remove role"
            }), 500

        invalidate_role_cache(tree_id, target_user_id)

        return jsonify({
            "message": "Role removed",
            "tree_id": tree_id,
            "user_id": target_user_id,
            "previous_role": existing_role
        }), 200
    except Exception as exc:
        current_app.logger.exception(f"Error removing role: {exc}")
        return jsonify({"error": "Failed to remove role"}), 500

