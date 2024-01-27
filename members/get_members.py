from flask import jsonify

def get_member_query(g, member_id):
    try:
        member = g.V(member_id)

        member.next()

        return jsonify(member)
    except Exception as e:
        return jsonify({'error': str(e)})
    
def get_all_members_query(g):
    try:
        members = g.V().toList()

        members_data = [{'id': member.id, 'name': member.name, 'surname': member.surname} for member in members]

        return jsonify(members_data)
    except Exception as e:
        return jsonify({'error': str(e)})
    
def get_related_members_query(g, member_id, relations_degree):
    try:

        member = g.V(member_id)
        for _ in range(relations_degree):
            member = member.repeat(g.both()).times(1).simplePath()

        related_members = member.dedup().toList()

        # Format the result
        related_members_data = [{'id': vertex.id, 'label': vertex.label} for vertex in related_members]

        return jsonify(related_members_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Alternative: 
#   Get all members connected as relation type 0 - 3 seperately
#   {0: [{id, name}, ...], 1: [{id, name}], 2: [{id, name}], 3: [{id, name}]}