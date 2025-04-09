from flask import jsonify, request
from utils import normalize_vertex
import validation.dataTypes as vdt
import validation.businessLogic as vbl


def update_member_query(g):
    try:
        data = request.get_json()

        if data is None:
            return jsonify({"error": "No JSON data provided"}), 400

        member_id = data.get("id")
        if not member_id:
            return jsonify({"error": "Missing 'id' field"}), 400

        if not g.V(member_id).hasNext():
            return jsonify({"error": f"Member with ID {member_id} does not exist"}), 404

        name = data.get("name")
        surname = data.get("surname")
        gender = data.get("gender")
        description = data.get("description")
        born = data.get("born")
        died = data.get("died")
        pic = data.get("pic")
        photos = data.get("photos")

        validations = []
        if name:
            validations.append((vdt.validate_member_name, ("name", name)))
        if surname:
            validations.append((vdt.validate_member_name, ("surname", surname)))
        if gender:
            validations.append((vdt.validate_gender, (gender,)))
        if description:
            validations.append((vdt.validate_member_description, (description,)))
        if born:
            validations.append((vdt.validate_date_format, (born,)))
        if died:
            validations.append((vdt.validate_date_format, (died,)))
            if born:
                validations.append((vbl.validate_date_order, (born, died)))
        if pic:
            validations.append((vdt.validate_url, ("pic", pic)))
        if photos:
            validations.append((vdt.validate_url, ("photos", photos)))

        for validator, args in validations:
            valid, error_msg = validator(*args)
            if not valid:
                return jsonify({"error": error_msg}), 400

        traversal = g.V(member_id)
        if name:
            traversal.property("name", name)
        if surname:
            traversal.property("surname", surname)
        if gender:
            traversal.property("gender", gender)
        if description:
            traversal.property("description", description)
        if born:
            traversal.property("born", born)
        if died:
            traversal.property("died", died)
        if pic:
            traversal.property("pic", pic)
        if photos:
            traversal.property("photos", photos)

        updated_member = traversal.next()

        return jsonify(normalize_vertex(updated_member)), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
