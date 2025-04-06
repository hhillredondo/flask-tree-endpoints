from flask import jsonify, request
from utils import normalize_edge
import validation.dataTypes as vdt
from gremlin_python.process.graph_traversal import __


def create_relation_query(g):
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ["relation_type", "source_id", "target_id"]
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required field(s)"}), 400

        relation_type = data["relation_type"]
        source_id = data["source_id"]
        target_id = data["target_id"]

        validations = [
            (vdt.validate_relation_type, (relation_type,)),
            (vdt.validate_vertex_ids_differ, (source_id, target_id)),
            (vdt.validate_vertex_exists, (source_id, "Source", g)),
            (vdt.validate_vertex_exists, (target_id, "Target", g)),
        ]

        for validator, args in validations:
            valid, error_msg = validator(*args)
            if not valid:
                return jsonify({"error": error_msg}), 400

        # Create the relationship
        new_relation = g.V(source_id).addE(relation_type).to(__.V(target_id)).next()

        return jsonify(normalize_edge(new_relation)), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500
