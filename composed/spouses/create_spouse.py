from flask import jsonify
from utils import (
    check_date_is_in_period,
    get_born,
    get_children,
    get_gender,
    get_marriages,
    get_parents_number,
    normalize_vertex,
)
import validation.dataTypes as vdt
import validation.coreTreeLogic as ctl
from validation.performValidations import perform_validations
from gremlin_python.process.traversal import T


def create_spouse(g, data):

    try:
        if data is None:
            return jsonify({"error": "No JSON data provided"}), 400

        spouse_id = data.get("spouse_id")
        name = data.get("name")
        surname = data.get("surname")
        gender = data.get("gender")
        description = data.get("description")
        born = data.get("born")
        died = data.get("died")
        pic = data.get("pic")
        photos = data.get("photos")
        married = data.get("married")
        divorced = data.get("divorced")

        required_fields = [
            "spouse_id",
            "name",
            "surname",
            "gender",
            "description",
            "born",
            "pic",
            "photos",
            "married",
            "divorced",
        ]
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required fields"}), 400

        validations = [
            (vdt.validate_vertex_exists, (spouse_id, "Target", g)),
            (ctl.verify_marriage_divorce_date_order, (married, divorced)),
            (vdt.validate_member_name, ("name", name)),
            (vdt.validate_member_name, ("surname", surname)),
            (vdt.validate_gender, (gender,)),
            (vdt.validate_member_description, (description,)),
            (vdt.validate_date_format, (born,)),
            (vdt.validate_url, ("pic", pic)),
            (vdt.validate_url, ("photos", photos)),
            (ctl.verify_legal_marriage_age, (born, married)),
        ]

        if died:
            validations.append((vdt.validate_date_format, (died,)))
            validations.append((ctl.validate_life_date_order, (born, died)))

        spouse_gender = get_gender(spouse_id, g)
        validations.append(
            (ctl.validate_heterosexual_marriage, (gender, spouse_gender))
        )

        spouse_born = get_born(spouse_id, g)
        validations.append((ctl.verify_legal_marriage_age, (spouse_born, married)))

        spouse_marriages = get_marriages(spouse_id, g)

        single_status_params = (
            (married, spouse_marriages, [])
            if gender == "female"
            else (married, [], spouse_marriages)
        )

        validations.append(
            (
                ctl.validate_groom_and_bride_single_status,
                single_status_params,
            )
        )

        spouse_children = get_children(spouse_id, g)
        common_children = []

        if len(spouse_children) != 0:
            for child in spouse_children:
                child_id = child.get(T.id)
                if get_parents_number(child_id, g) >= 2:
                    continue

                child_born = child.get("born")
                if not check_date_is_in_period(child_born, married, divorced):
                    continue

                valid, _ = ctl.validate_parent_is_alive_and_fertile(
                    gender, born, died, child_born
                )

                if not valid:
                    continue

                common_children.append(child_id)

        result = perform_validations(validations)
        if result:
            return result

        spouse = (
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
            spouse = spouse.property("died", died)

        spouse = (
            spouse.as_("spouse")
            .V(spouse_id)
            .addE("spouse")
            .property("married", married)
            .property("divorced", divorced)
            .from_("spouse")
        )

        for child_id in common_children:
            spouse = spouse.V(child_id).addE("parent").from_("spouse")

        spouse = spouse.select("spouse").next()

        return normalize_vertex(spouse), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500
