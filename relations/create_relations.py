from flask import jsonify, request

def create_relation_query(g, source_id, target_id):
    try:
        data = request.get_json()
        relation_type = data.get('relation_type')

        new_relation = g.V(source_id).addE(relation_type).to(target_id).next()

        return jsonify(new_relation)
    except Exception as e:
        return jsonify({'error': str(e)})