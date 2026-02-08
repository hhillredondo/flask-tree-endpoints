from flask import jsonify
from partition.middleware import get_current_partition, get_current_tree_id
from partition.query_helper import PartitionedQueryHelper
from roles.acl_store import acl_store
from storage.s3_media import delete_prefix, get_media_bucket, get_media_prefix


def delete_tree(g, data):
    """Delete all vertices/edges for the current partition."""
    try:
        tree_id = get_current_tree_id()
        if not tree_id:
            return jsonify({
                "error": "Partition required",
                "message": "tree_id missing from partition context"
            }), 400

        if not acl_store.delete_roles_for_tree(tree_id):
            return jsonify({
                "error": "Failed to delete roles for tree"
            }), 500

        bucket = get_media_bucket()
        if not bucket:
            return jsonify({"error": "S3_MEDIA_BUCKET is not configured"}), 500
        partition_key = get_current_partition()
        if not partition_key:
            return jsonify({"error": "Partition key is required"}), 400

        prefix = f"{get_media_prefix()}/{partition_key}/"
        delete_prefix(bucket, prefix)

        PartitionedQueryHelper.delete_partition(g)
        return jsonify({"message": "Tree deleted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
