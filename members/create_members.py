from flask import jsonify, request
from utils import normalize_data


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

        # Input validation
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

        # Data type validation with Marshmallow (eg. max char lengths, alphabetical chars only for names, proper date formats, etc.)
        # Business logic constraints validation (eg. date of death must be after date of birth)

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
