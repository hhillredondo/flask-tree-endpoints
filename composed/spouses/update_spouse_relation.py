from flask import jsonify
from utils import (
    get_common_children_birth_dates,
    get_marriage_id,
    get_marriages,
    normalize_edge,
)
import validation.dataTypes as vdt
import validation.coreTreeLogic as ctl
from validation.performValidations import perform_validations


def update_spouse_relation(g, data):

    try:
        husband_id = data.get("husband_id")
        wife_id = data.get("wife_id")
        married = data.get("married")
        divorced = data.get("divorced")

        required_fields = [
            "husband_id",
            "wife_id",
            "married",
            "divorced",
        ]

        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required fields"}), 400

        husband_exists, error_msg = vdt.validate_vertex_exists(husband_id, "Source", g)
        if not husband_exists:
            return jsonify({"error": error_msg}), 400

        wife_exists, error_msg = vdt.validate_vertex_exists(wife_id, "Target", g)
        if not wife_exists:
            return jsonify({"error": error_msg}), 400

        marriage_id = get_marriage_id(husband_id, wife_id, g)

        husband_marriages = get_marriages(husband_id, g)
        wife_marriages = get_marriages(wife_id, g)

        common_children_birth_dates = get_common_children_birth_dates(
            husband_id, wife_id, g
        )

        validations = [
            (ctl.verify_marriage_divorce_date_order, (married, divorced)),
            (
                ctl.validate_groom_and_bride_single_status,
                (married, husband_marriages, wife_marriages),
            ),
            (
                ctl.verify_common_children_born_in_marriage,
                (common_children_birth_dates, married, divorced),
            ),
        ]

        result = perform_validations(validations)
        if result:
            return result
        
        updated_spouse_relation = (
            g.E(marriage_id)
            .property("married", married)
            .property("divorced", divorced)
            .next()
        )

        return jsonify(normalize_edge(updated_spouse_relation)), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500
