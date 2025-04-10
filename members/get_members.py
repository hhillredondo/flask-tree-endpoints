from flask import jsonify, request
from gremlin_python.process.graph_traversal import __
from gremlin_python.process.traversal import T

from utils import normalize_vertex


def get_member_query(g):
    try:
        data = request.get_json()

        if data is None:
            return jsonify({"error": "No JSON data provided"}), 400

        member_id = data.get("id")

        if not isinstance(member_id, int):
            return jsonify(f"Vertex id {member_id} is not a number")

        if not g.V(member_id).hasNext():
            return jsonify({"error": f"Member with ID {member_id} does not exist"}), 404

        member = g.V(member_id).next()

        return normalize_vertex(member), 201
    except Exception as e:
        return jsonify({"error": str(e)})


def get_all_members_query(g):
    try:
        all_members = g.V().toList()

        normalized_members = [normalize_vertex(member) for member in all_members]

        return normalized_members
    except Exception as e:
        return jsonify({"error": str(e)})


def get_direct_relations_query(g, member_id):
    try:
        related_members = (
            g.V(member_id)
            .bothE()
            .group()
            .by(T.label)
            .by(__.bothV().valueMap().fold())
            .toList()
        )

        related_members_data = [normalize_vertex(member) for member in related_members]

        return related_members_data
    except Exception as e:
        return jsonify({"error": str(e)}), 500
