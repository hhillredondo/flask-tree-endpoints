from flask import current_app, jsonify

from auth.cognito import delete_user_by_sub
from auth.utils import get_current_user_id
from partition.manager import partition_manager
from partition.query_helper import PartitionedQueryHelper
from roles.acl_store import ROLE_OWNER, acl_store
from roles.service import invalidate_role_cache
from storage.s3_media import delete_prefix, get_media_bucket, get_media_prefix


def delete_account(g):
    """Delete the current user's account and all owned tree data."""
    try:
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({"error": "User not authenticated"}), 401

        roles = acl_store.list_roles_for_user(user_id)
        owned_tree_ids = [
            entry.get("treeId")
            for entry in roles
            if entry.get("role") == ROLE_OWNER and entry.get("treeId")
        ]

        bucket = get_media_bucket()
        prefix_root = get_media_prefix() if bucket else None

        # Delete trees owned by the user (roles, media, graph data)
        for tree_id in owned_tree_ids:
            if not acl_store.delete_roles_for_tree(tree_id):
                return jsonify({"error": "Failed to delete roles for owned tree"}), 500

            partition_key = partition_manager.generate_partition_key(user_id, tree_id)
            if bucket:
                delete_prefix(bucket, f"{prefix_root}/{partition_key}/")

            PartitionedQueryHelper.delete_partition(g, partition_key=partition_key)

        # Remove any remaining roles for this user in other trees
        for entry in roles:
            tree_id = entry.get("treeId")
            if tree_id:
                invalidate_role_cache(tree_id, user_id)

        if not acl_store.delete_roles_for_user(user_id):
            return jsonify({"error": "Failed to delete roles for user"}), 500

        # Delete the Cognito user last
        if not delete_user_by_sub(user_id):
            return jsonify({"error": "Failed to delete user from Cognito"}), 500

        return jsonify({"message": "Account deleted"}), 200
    except Exception as exc:
        current_app.logger.exception(f"Error deleting account: {exc}")
        return jsonify({"error": "Failed to delete account"}), 500

