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
        if member_id is None or (isinstance(member_id, str) and not member_id.strip()):
            return jsonify({"error": "Member id is required"}), 400

        partition_key = get_current_partition()
        if not partition_key:
            return jsonify({"error": "Partition key is required"}), 400

        member_traversal = (
            g.V(member_id).has("_partitionKey", partition_key).elementMap()
        )

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
        partition_key = get_current_partition()
        if not partition_key:
            return jsonify({"error": "Partition key is required"}), 400

        all_members = (
            g.V()
            .hasLabel("_Member")
            .has("_partitionKey", partition_key)
            .elementMap()
            .toList()
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
        if member_id is None or (isinstance(member_id, str) and not member_id.strip()):
            return jsonify({"error": "Member id is required"}), 400

        partition_key = get_current_partition()
        if not partition_key:
            return jsonify({"error": "Partition key is required"}), 400

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
            .project("member", "parents", "children", "spouses", "siblings")
            .by(__.elementMap())
            .by(__.inE("parent").outV().elementMap().dedup().fold())
            .by(__.outE("parent").inV().elementMap().dedup().fold())
            .by(__.bothE("spouse").otherV().elementMap().dedup().fold())
            .by(
                __.inE("parent")
                .outV()
                .outE("parent")
                .inV()
                .where(__.not_(__.hasId(member_id)))
                .dedup()
                .elementMap()
                .fold()
            )
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
            "siblings": [
                normalize_vertex(sibling)
                for sibling in related_members.get("siblings")
            ],
        }

        for spouse in related_members_data["spouses"]:
            spouse_id = spouse["id"]
            marriage_date = get_marriage_date(member_id, spouse_id, g)
            divorce_date = get_divorce_date(member_id, spouse_id, g)
            spouse["married"] = marriage_date
            spouse["divorced"] = divorce_date

        focused_parent_ids = {p["id"] for p in related_members_data["parents"]}
        for sibling in related_members_data["siblings"]:
            sibling_parent_ids = {
                str(pid)
                for pid in g.V(sibling["id"]).inE("parent").outV().id_().toList()
            }
            shared = sibling_parent_ids & focused_parent_ids
            sibling["siblingType"] = (
                "full" if shared == focused_parent_ids else "half"
            )

        return related_members_data, 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
