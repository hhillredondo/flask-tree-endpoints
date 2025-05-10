from flask import jsonify
from utils import (
    get_born,
    get_common_children_birth_dates,
    get_marriage_date,
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
        current_married_value = get_marriage_date(husband_id, wife_id, g)

        husband_marriages = [
            d
            for d in get_marriages(husband_id, g)
            if d.get("married") != current_married_value
        ]
        wife_marriages = [
            d
            for d in get_marriages(wife_id, g)
            if d.get("married") != current_married_value
        ]

        common_children_birth_dates = get_common_children_birth_dates(
            husband_id, wife_id, g
        )

        husband_born = get_born(husband_id, g)
        wife_born = get_born(wife_id, g)

        validations = [
            (ctl.verify_marriage_divorce_date_order, (married, divorced)),
            (ctl.verify_legal_marriage_age, (husband_born, married)),
            (ctl.verify_legal_marriage_age, (wife_born, married)),
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

        g.E(marriage_id).property("married", married).property(
            "divorced", divorced
        ).iterate()

        return "Marriage details updated successfully", 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500
