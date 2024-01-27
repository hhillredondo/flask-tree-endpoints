from flask import jsonify

def delete_relation_query(g, relation_id):
    try:
        relation = g.V(relation_id)

        relation.drop().iterate()

        return jsonify(relation)
    except Exception as e:
        return jsonify({'error': str(e)})