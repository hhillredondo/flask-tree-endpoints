from flask import jsonify


def create_tree(g, data):

    # Return some statistics, eg.
    # Number of members
    # Number of relations
    # Number of generations
    # Oldest member
    # Youngest member
    # Most common names
    # Number of males vs females
    # Members with most marriages
    # Number of dead members who never married
    # Number of dead members who married

    try:
        g.V().count().next()

    except Exception as e:
        return jsonify({"error": str(e)}), 500
