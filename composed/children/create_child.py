from flask import jsonify
from utils import (
    get_born,
    get_died,
    get_gender,
    get_potential_spouse_at_child_birth,
    get_parents_other_children_birth_dates,
    normalize_vertex,
)
import validation.dataTypes as vdt
import validation.coreTreeLogic as ctl
from validation.performValidations import perform_validations
from gremlin_python.process.traversal import T


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
            "parent_id",
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

        parent_exists, error_msg = vdt.validate_vertex_exists(parent_id, "Source", g)
        if not parent_exists:
            return jsonify({"error": error_msg}), 400

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
            validations.append((ctl.validate_life_date_order, (born, died)))

        parent_gender = get_gender(parent_id, g)
        parent_born = get_born(parent_id, g)
        parent_died = get_died(parent_id, g)

        validations.append(
            (
                ctl.validate_parent_is_alive_and_fertile,
                (parent_gender, parent_born, parent_died, born),
            )
        )

        parent_children_birth_dates = get_parents_other_children_birth_dates(
            parent_id, g
        )
        validations.append(
            (
                ctl.validate_siblings_birth_dates,
                (born, parent_children_birth_dates),
            )
        )

        potential_spouse = get_potential_spouse_at_child_birth(parent_id, born, g)

        if potential_spouse != None:
            spouse_id = potential_spouse.get(T.id)
            spouse_gender = potential_spouse.get("gender")
            spouse_born = potential_spouse.get("born")
            spouse_died = potential_spouse.get("died")
            validations.append(
                (
                    ctl.validate_parent_is_alive_and_fertile,
                    (spouse_gender, spouse_born, spouse_died, born),
                )
            )

            spouse_children_birth_dates = get_parents_other_children_birth_dates(
                spouse_id, g
            )
            validations.append(
                (
                    ctl.validate_siblings_birth_dates,
                    (born, spouse_children_birth_dates),
                )
            )

        result = perform_validations(validations)
        if result:
            return result

        child = (
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
            child = child.property("died", died)

        child = child.as_("child").V(parent_id).addE("parent").to("child")

        if potential_spouse != None:
            spouse_id = potential_spouse.get(T.id)
            child.V(spouse_id).addE("parent").to("child")

        child = child.next()

        return normalize_vertex(child), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500
