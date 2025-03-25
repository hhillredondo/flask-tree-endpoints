from flask import jsonify, request
from utils import normalize_data
import validation.dataTypes as vdt
import validation.businessLogic as vbl


def create_member_query(g):
    try:
        data = request.get_json()

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
        root = data.get("root")

        required_fields = [
            "name",
            "surname",
            "gender",
            "description",
            "born",
            "died",
            "pic",
            "photos",
            "root",
        ]
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required fields"}), 400

        validations = [
            (vdt.validate_name_fields, ("name", name)),
            (vdt.validate_name_fields, ("surname", surname)),
            (vdt.validate_gender, (gender)),
            (vdt.validate_description, (description)),
            (vdt.validate_date_format, (born)),
            (vdt.validate_date_format, (died)),
            (vbl.validate_date_order, (born, died)),
            (vdt.validate_url, ("pic", pic)),
            (vdt.validate_url, ("photos", photos)),
            (vdt.validate_boolean, ("root", root)),
        ]

        for validator, args in validations:
            valid, error_msg = validator(*args)
        if not valid:
            return jsonify({"error": error_msg}), 400

        new_member = (
            g.addV("_Member")
            .property("name", name)
            .property("surname", surname)
            .property("gender", gender)
            .property("description", description)
            .property("born", born)
            .property("died", died)
            .property("pic", pic)
            .property("photos", photos)
            .property("root", root)
            .next()
        )

        return normalize_data(new_member), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500
