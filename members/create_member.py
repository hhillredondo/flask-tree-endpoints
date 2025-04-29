from flask import jsonify
from utils import normalize_vertex
import validation.dataTypes as vdt
import validation.coreTreeLogic as vbl
from validation.performValidations import perform_validations


def create_member_query(g, data):
    try:
        if data is None:
            return jsonify({"error": "No JSON data provided"}), 400

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
            validations.append((vbl.validate_date_order, (born, died)))

        result = perform_validations(validations)
        if result:
            return result

        new_member = (
            g.addV("_Member")
            .property("name", name)
            .property("surname", surname)
            .property("gender", gender)
            .property("description", description)
            .property("born", born)
            .property("pic", pic)
            .property("photos", photos)
        )

        if died:
            new_member = new_member.property("died", died)

        new_member = new_member.next()

        return normalize_vertex(new_member), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500
