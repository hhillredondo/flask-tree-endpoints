from flask import jsonify, request
from utils import normalize_vertex
import validation.dataTypes as vdt
import validation.coreTreeLogic as vbl
from members.create_member import create_member_query


def create_child(g, data):

    try:
        # validate_life_date_order
        # if parent is male
        #   validate_father_is_alive_and_fertile
        # if parent is female
        #   validate_mother_is_alive_and_fertile
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
