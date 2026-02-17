from flask import jsonify, g
from auth.utils import get_current_user_id
from partition.middleware import get_current_tree_id
from roles.acl_store import acl_store, ROLE_OWNER
from roles.service import get_user_role, invalidate_role_cache


def quit_tree():
    """Remove current user's role from the tree (editor/viewer only)."""
    try:
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

        # Get current role
        role = get_user_role(tree_id, user_id)
        if not role:
            return jsonify({
                "error": "User not found",
                "message": "No role entry for this user in this tree"
            }), 404

        # Prevent owners from quitting (they must delete the tree instead)
        if role == ROLE_OWNER:
            return jsonify({
                "error": "Invalid operation",
                "message": "Owners cannot quit trees. Use DELETE /trees to delete the tree instead."
            }), 403

        # Remove the role
        success = acl_store.delete_role(tree_id, user_id)
        if not success:
            return jsonify({
                "error": "Failed to remove role",
                "message": "Could not remove role from tree"
            }), 500

        # Invalidate role cache
        invalidate_role_cache(tree_id, user_id)

        return jsonify({
            "message": "Successfully quit tree",
            "tree_id": tree_id,
            "user_id": user_id,
            "previous_role": role
        }), 200
    except Exception as e:
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500

