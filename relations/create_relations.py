from flask import jsonify, request


def create_relation_query(g):
    try:
        data = request.get_json()
        relation_type = data.get("relation_type")
        source_id = data.get("source_id")
        target_id = data.get("target_id")

        new_relation = g.V(source_id).addE(relation_type).to(target_id).next()

        return jsonify(new_relation)
    except Exception as e:
        return jsonify({"error": str(e)})
