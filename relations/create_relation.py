from flask import jsonify
from utils import normalize_edge
import validation.dataTypes as vdt
import validation.coreTreeLogic as ctl
from gremlin_python.process.graph_traversal import __
from validation.performValidations import perform_validations
from partition.query_helper import PartitionedQueryHelper
from partition.middleware import get_current_partition


def create_relation_query(g, data):
    try:
        # Validate required fields
        required_fields = ["relation_type", "source_id", "target_id"]

        relation_type = data.get("relation_type")
        source_id = data.get("source_id")
        target_id = data.get("target_id")
        married = data.get("married")
        divorced = data.get("divorced")  # Must be passed as null if divorce did not happen

        if relation_type == "spouse":
            required_fields.extend(["married", "divorced"])

        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required field(s)"}), 400

        # PARTITION VALIDATION: Ensure both source_id and target_id are in the current partition
        is_valid, error_response = PartitionedQueryHelper.validate_vertices_in_partition(
            g, [source_id, target_id]
        )
        if not is_valid:
            return error_response

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

        result = perform_validations(validations)
        if result:
            return result

        # Get partition key from context
        partition_key = get_current_partition()
        if not partition_key:
            return jsonify({"error": "No partition context"}), 400

        # Build edge properties
        edge_properties = None
        if relation_type == "spouse":
            edge_properties = {
                "married": married,
                "divorced": divorced
            }

        # Create the relationship with partition key
        new_relation = PartitionedQueryHelper.create_partitioned_edge(
            g=g,
            from_vertex_id=source_id,
            to_vertex_id=target_id,
            label=relation_type,
            properties=edge_properties,
            partition_key=partition_key
        )

        return jsonify(normalize_edge(new_relation)), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500
