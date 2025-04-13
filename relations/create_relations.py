from flask import jsonify, request
from utils import normalize_edge
import validation.dataTypes as vdt
import validation.coreTreeLogic as ctl
from gremlin_python.process.graph_traversal import __


def create_relation_query(g):
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ["relation_type", "source_id", "target_id"]

        if relation_type == "spouse":
            required_fields.extend(["married", "divorced"])

        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required field(s)"}), 400

        relation_type = data["relation_type"]
        source_id = data["source_id"]
        target_id = data["target_id"]
        married = data["married"]
        divorced = data["divorced"] # Must be passed as null if divorce did not happen

        validations = [
            (vdt.validate_relation_type, (relation_type,)),
            (vdt.validate_vertex_ids_differ, (source_id, target_id)),
            (vdt.validate_vertex_exists, (source_id, "Source", g)),
            (vdt.validate_vertex_exists, (target_id, "Target", g)),
        ]

        if relation_type == "spouse":
            validations.extend(
                (ctl.verify_marriage_divorce_date_order, (married, divorced))
            )

        for validator, args in validations:
            valid, error_msg = validator(*args)
            if not valid:
                return jsonify({"error": error_msg}), 400

        # Create the relationship
        new_relation = g.V(source_id).addE(relation_type)

        if relation_type == "spouse":
            new_relation.property("married", married).property("divorced", divorced)

        new_relation = new_relation.to(__.V(target_id)).next()

        return jsonify(normalize_edge(new_relation)), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500
