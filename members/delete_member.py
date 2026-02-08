from flask import jsonify
from composed.trees.delete_tree import delete_tree
from partition.middleware import get_current_partition
from storage.s3_media import (
    delete_prefix,
    get_media_bucket,
    get_media_prefix,
    build_member_base_prefix,
)


def delete_member_query(g, data):
    try:
        if data is None:
            return jsonify({"error": "No JSON data provided"}), 400

        member_id = data.get("member_id")
        print("deleting member with id: ", member_id)

        if member_id is None or (isinstance(member_id, str) and not member_id.strip()):
            return jsonify({"error": "Member id is required"}), 400

        partition_key = get_current_partition()
        if not partition_key:
            return jsonify({"error": "Partition key is required"}), 400

        member_exists = g.V(member_id).has("_partitionKey", partition_key).hasNext()
        if not member_exists:
            return jsonify({"error": f"Member with ID {member_id} does not exist in this tree"}), 404

        member_count = (
            g.V()
            .hasLabel("_Member")
            .has("_partitionKey", partition_key)
            .count()
            .next()
        )

        if member_count == 1:
            return delete_tree(g)

        edge_count = g.V(member_id).bothE().has("_partitionKey", partition_key).count().next()

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

        bucket = get_media_bucket()
        if bucket:
            prefix_root = get_media_prefix()
            delete_prefix(
                bucket,
                f"{build_member_base_prefix(prefix_root, partition_key, member_id)}/",
            )

        return jsonify({"message": f"Member {member_id} deleted successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
