from flask import jsonify, request

def create_member_query(g):
    try:
        data = request.get_json()
        name = data.get('name')
        description = data.get('description')
        born = data.get('born')

        new_member = g.addV('_Member').property('name', name).property('description', description).property('born', born).next()

        return jsonify(new_member)
    except Exception as e:
        return jsonify({'error': str(e)})