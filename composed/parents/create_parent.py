from flask import jsonify, request
from utils import normalize_vertex
import validation.dataTypes as vdt
import validation.coreTreeLogic as vbl
from members.create_member import create_member_query


def create_parent(g, data):

    try:
        # if child has a parent already, return
        # validate_life_date_order
        # if parent is male
        #   validate_father_is_alive_and_fertile
        # if parent is female
        #   validate_mother_is_alive_and_fertile
        #   
        # Create parent member connected to child

        create_member_query(g, data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500