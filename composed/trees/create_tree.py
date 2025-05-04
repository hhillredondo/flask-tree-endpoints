from flask import jsonify
from members.create_member import create_member_query


def create_tree(g, data):

    # Create tree id to use as partition key
    # Assign permissions to tree creator

    try:
        return create_member_query(g, data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
