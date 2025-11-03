from flask import jsonify
from gremlin_python.process.graph_traversal import __
from gremlin_python.process.traversal import T

from utils import get_divorce_date, get_marriage_date, normalize_vertex
from partition.middleware import get_current_partition


def get_member_query(g, data):
    try:
        if data is None:
            return jsonify({"error": "No JSON data provided"}), 400

        member_id = data.get("id")

        if not isinstance(member_id, int):
            return jsonify(f"Vertex id {member_id} is not a number")

        # Get partition key from context
        partition_key = get_current_partition()

        # Check if member exists in the current partition
        if partition_key:
            member_traversal = g.V(member_id).has("_partitionKey", partition_key)
        else:
            # Fallback for backward compatibility
            member_traversal = g.V(member_id)

        if not member_traversal.hasNext():
            return (
                jsonify(
                    {"error": f"Member with ID {member_id} does not exist in this tree"}
                ),
                404,
            )

        member = member_traversal.next()

        return normalize_vertex(member), 201
    except Exception as e:
        return jsonify({"error": str(e)})


def get_all_members_query(g):
    try:
        # Get partition key from context
        partition_key = get_current_partition()

        # Get members in current partition
        if partition_key:
            all_members = (
                g.V().hasLabel("_Member").has("_partitionKey", partition_key).toList()
            )

        normalized_members = [normalize_vertex(member) for member in all_members]

        return normalized_members
    except Exception as e:
        return jsonify({"error": str(e)})


def get_direct_relations_query(g, data):
    try:
        if data is None:
            return jsonify({"error": "No JSON data provided"}), 400

        member_id = data.get("id")

        if not isinstance(member_id, int):
            return jsonify({"error": f"Vertex id {member_id} is not a number"}), 400

        # Get partition key from context
        partition_key = get_current_partition()

        # Check if member exists in the current partition
        if partition_key:
            member_exists = g.V(member_id).has("_partitionKey", partition_key).hasNext()

        if not member_exists:
            return (
                jsonify(
                    {"error": f"Member with ID {member_id} does not exist in this tree"}
                ),
                404,
            )

        related_members_list = (
            g.V(member_id)
            .project("member", "parents", "children", "spouses")
            .by(__.identity())
            .by(__.inE("parent").outV().dedup().fold())
            .by(__.outE("parent").inV().dedup().fold())
            .by(__.bothE("spouse").otherV().dedup().fold())
            .toList()
        )

        if len(related_members_list) == 0:
            return jsonify({"error": "No relations found"}), 404

        related_members = related_members_list[0]

        related_members_data = {
            "member": normalize_vertex(related_members.get("member")),
            "parents": [
                normalize_vertex(parent) for parent in related_members.get("parents")
            ],
            "children": [
                normalize_vertex(child) for child in related_members.get("children")
            ],
            "spouses": [
                normalize_vertex(spouse) for spouse in related_members.get("spouses")
            ],
        }

        for spouse in related_members_data["spouses"]:
            spouse_id = spouse["id"]
            marriage_date = get_marriage_date(member_id, spouse_id, g)
            divorce_date = get_divorce_date(member_id, spouse_id, g)
            spouse["married"] = marriage_date
            spouse["divorced"] = divorce_date

        return related_members_data, 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
