from flask import jsonify, request

def update_member_query(g, member_id):
    try:
        data = request.get_json()

        member = g.V(member_id)

        for key, value in data.items():
            member = member.property(key, value)

        updated_member = member.next()

        return jsonify(updated_member)
    except Exception as e:
        return jsonify({'error': str(e)})
    
def set_tree_root_query(g, member_id):
    try:
        g.V().has("root", True).properties("root").drop().iterate()

        new_root = g.V(member_id).property("root", True).next()

        return jsonify(new_root)
    except Exception as e:
        return jsonify({'error': str(e)})