from flask import jsonify


def delete_member_query(g, data):
    try:
        member_id = data.get("member_id")
        print("deleting member with id: ", member_id)

        if data is None:
            return jsonify({"error": "No JSON data provided"}), 400

        if not isinstance(member_id, int):
            return jsonify(f"Vertex id {member_id} is not a number")

        if not g.V(member_id).hasNext():
            return jsonify({"error": f"Member with ID {member_id} does not exist"}), 404

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
