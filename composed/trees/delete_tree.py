from flask import jsonify
from partition.query_helper import PartitionedQueryHelper


def delete_tree(g, data):
    """Delete all vertices/edges for the current partition."""
    try:
        PartitionedQueryHelper.delete_partition(g)
        return jsonify({"message": "Tree deleted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
