from flask import jsonify, request
from utils import check_born, check_died, check_gender, normalize_vertex
import validation.dataTypes as vdt
import validation.coreTreeLogic as ctl
from members.create_member import create_member_query
from validation.performValidations import perform_validations


def create_child(g, data):

    try:
        if data is None:
            return jsonify({"error": "No JSON data provided"}), 400

        parent_id = data.get("parent_id")
        name = data.get("name")
        surname = data.get("surname")
        gender = data.get("gender")
        description = data.get("description")
        born = data.get("born")
        died = data.get("died")
        pic = data.get("pic")
        photos = data.get("photos")

        required_fields = [
            "name",
            "surname",
            "gender",
            "description",
            "born",
            "pic",
            "photos",
        ]
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required fields"}), 400

        validations = [
            (vdt.validate_vertex_exists, (parent_id, "Source", g)),
            (vdt.validate_member_name, ("name", name)),
            (vdt.validate_member_name, ("surname", surname)),
            (vdt.validate_gender, (gender,)),
            (vdt.validate_member_description, (description,)),
            (vdt.validate_date_format, (born,)),
            (vdt.validate_url, ("pic", pic)),
            (vdt.validate_url, ("photos", photos)),
        ]

        if died:
            validations.append((vdt.validate_date_format, (died,)))
            validations.append((ctl.validate_life_date_order, (born, died)))

        parent_gender = check_gender(parent_id, g)
        parent_born = check_born(parent_id, g)
        parent_died = check_died(parent_id, g)

        validations.append(
            (
                ctl.validate_parent_is_alive_and_fertile,
                (parent_gender, parent_born, parent_died, born),
            )
        )

        result = perform_validations(validations)
        if result:
            return result

        # if parent is in a marriage on child's birth date - 9 months
        #   validate_mother_is_alive_and_fertile / validate_father_is_alive_and_fertile
        # if has father && father has other children
        #   validate_father_side_siblings_birth_dates
        # if has mother && mother has other children
        #   validate_mother_side_siblings_birth_dates
        # Create child member connected to parent (& other parent if it exists)

        create_member_query(g, data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
