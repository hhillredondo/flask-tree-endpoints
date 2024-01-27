from flask import jsonify

def get_relation_query(g, relation_id):
    try:
        relation = g.E(relation_id)

        relation.next()

        return jsonify(relation)
    except Exception as e:
        return jsonify({'error': str(e)})