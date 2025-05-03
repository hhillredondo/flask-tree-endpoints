from flask import jsonify
from utils import get_marriages
import validation.dataTypes as vdt
import validation.coreTreeLogic as ctl
from validation.performValidations import perform_validations


def update_spouse_relation(g, data):

    try:
        marriage_id = data.get("marriage_id")
        husband_id = data.get("husband_id")
        wife_id = data.get("wife_id")
        married = data.get("married")
        divorced = data.get("divorced")

        # Only one of married & divorced should be required!
        # If both are missing, do nothing

        required_fields = [
            "marriage_id",
            "husband_id",
            "wife_id",
            "married",
            "divorced",
        ]
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required fields"}), 400

        husband_marriages = get_marriages(husband_id, g)
        wife_marriages = get_marriages(wife_id, g)

        # Get common children
        # verify_common_children_born_in_marriage

        validations = [
            (ctl.verify_marriage_divorce_date_order, (married, divorced)),
            (
                ctl.validate_groom_and_bride_single_status,
                (married, husband_marriages, wife_marriages),
            ),
        ]

        result = perform_validations(validations)
        if result:
            return result
        
        # Update vertex by marriage_id

    except Exception as e:
        return jsonify({"error": str(e)}), 500
