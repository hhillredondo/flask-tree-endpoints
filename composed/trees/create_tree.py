from flask import jsonify, request
from utils import normalize_vertex
import validation.dataTypes as vdt
import validation.coreTreeLogic as vbl
from members.create_member import create_member_query


def create_tree(g, data):

    # Create tree id to use as partition key
    # Assign permissions to tree creator

    try:
        base_user = {
            "name": "John",
            "surname": "Doe",
            "gender": "male",
            "description": "",
            "born": "1900-01-01T00:00:00Z",
            "death": "2000-01-01T00:00:00Z",
            "pic": "",
            "photos": "",
        }

        create_member_query(g, base_user)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
