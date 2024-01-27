from flask import jsonify
from gremlin_python.process.graph_traversal import __
from gremlin_python.process.traversal import T

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

        related_members_data = [{'id': vertex.id, 'label': vertex.label} for vertex in related_members]

        return jsonify(related_members_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def get_direct_relations_query(g, member_id):
    try:
        related_members = g.V(member_id).bothE().group().by(T.label).by(__.bothV().valueMap().fold()).toList()

        related_members_data = [{'id': member.id, 'label': member.label} for member in related_members]

        return jsonify(related_members_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500