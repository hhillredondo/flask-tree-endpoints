from flask import jsonify

def delete_member_query(g, member_id):
    try:
        member = g.V(member_id)

        member.drop().iterate()

        return jsonify(member)
    except Exception as e:
        return jsonify({'error': str(e)})