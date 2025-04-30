from flask import jsonify


def delete_tree(g, data):

    # Delete vertices with a given partition key

    try:
        g.V().drop().iterate()

    except Exception as e:
        return jsonify({"error": str(e)}), 500
