from flask import jsonify
from composed.spouses.create_spouse import create_spouse
from utils import get_born, get_parents_number, normalize_vertex
import validation.dataTypes as vdt
import validation.coreTreeLogic as ctl
from validation.performValidations import perform_validations


def create_parent(g, data):

    try:
        if data is None:
            return jsonify({"error": "No JSON data provided"}), 400

        child_id = data.get("child_id")
        name = data.get("name")
        surname = data.get("surname")
        gender = data.get("gender")
        description = data.get("description")
        born = data.get("born")
        died = data.get("died")
        pic = data.get("pic")
        photos = data.get("photos")

        required_fields = [
            "child_id",
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

        existing_parents = get_parents_number(child_id, g)

        validations = [
            (vdt.validate_vertex_exists, (child_id, "Target", g)),
            (ctl.validate_parents_number, (existing_parents,)),
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

        child_born = get_born(child_id, g)

        validations.append(
            (ctl.validate_parent_is_alive_and_fertile, (gender, born, died, child_born))
        )

        result = perform_validations(validations)
        if result:
            return result

        parent = (
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
            parent = parent.property("died", died)

        parent = parent.as_("parent").V(child_id).addE("parent").from_("parent")

        parent = parent.select("parent").next()

        return normalize_vertex(parent), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500
