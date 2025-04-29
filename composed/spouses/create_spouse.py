from flask import jsonify, request
from utils import normalize_vertex
import validation.dataTypes as vdt
import validation.coreTreeLogic as vbl
from members.create_member import create_member_query


def create_spouse(g, data):

    try:
        # validate_heterosexual_marriage
        # validate_life_date_order
        # verify_marriage_divorce_date_order
        # validate_groom_and_bride_single_status
        # if other parent has children
        #   for child in children
        #       if child has 2 parents
        #           continue
        #       if child birth is outside marriage
        #           continue
        #       if spouse is male
        #           validate_father_is_alive_and_fertile
        #       elif spouse is female
        #           validate_mother_is_alive_and_fertile
        #       Add parent relation
        # Create spouse connected to other spouse & any children

        create_member_query(g, data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500