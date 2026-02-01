from flask import jsonify
from partition.middleware import get_current_partition


def delete_member_query(g, data):
    try:
        if data is None:
            return jsonify({"error": "No JSON data provided"}), 400

        member_id = data.get("member_id")
        print("deleting member with id: ", member_id)

        if member_id is None or (isinstance(member_id, str) and not member_id.strip()):
            return jsonify({"error": "Member id is required"}), 400

        # Get partition key from context
        partition_key = get_current_partition()
        
        # Check if member exists in the current partition
        if partition_key:
            member_exists = g.V(member_id).has("_partitionKey", partition_key).hasNext()
        else:
            # Fallback for backward compatibility
            member_exists = g.V(member_id).hasNext()
        
        if not member_exists:
            return jsonify({"error": f"Member with ID {member_id} does not exist in this tree"}), 404

        # Count edges (only in current partition if partition_key exists)
        if partition_key:
            edge_count = g.V(member_id).bothE().has("_partitionKey", partition_key).count().next()
        else:
            edge_count = g.V(member_id).bothE().count().next()

        if edge_count >= 2:
            return (
                jsonify(
                    {
                        "error": f"Cannot delete member {member_id}: it has {edge_count} connected edges"
                    }
                ),
                400,
            )

        g.V(member_id).drop().iterate()

        return jsonify({"message": f"Member {member_id} deleted successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
