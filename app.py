from flask import Flask, jsonify, request
from gremlin_connection import create_gremlin_connection
from members.create_members import create_member_query
from members.update_members import update_member_query
from members.get_members import get_member_query, get_all_members_query
from members.delete_members import delete_member_query
from relations.create_relations import create_relation_query
from relations.get_relations import get_relation_query
from relations.delete_relations import delete_relation_query


app = Flask(__name__)

g = create_gremlin_connection()

@app.route('/', methods=['GET'])
def get_vertices_count():
    try:
        result_set = g.V().count().next()
        return jsonify(result_set)
    except Exception as e:
        return jsonify({'error': str(e)})

# MEMBERS

@app.route('/member', methods=['POST'])
def create_member():
    return create_member_query(g)

@app.route('/member/<member_id>', methods=['GET', 'PUT', 'DELETE'])
def member(member_id):
    if request.method == 'GET':
        return get_member_query(g, member_id)
    elif request.method == 'PUT':
        return update_member_query(g, member_id)
    elif request.method == 'DELETE':
        return delete_member_query(g, member_id)
    
@app.route('/members', methods=['GET'])
def create_member():
    return get_all_members_query(g)

# RELATIONS
    
@app.route('/relation', methods=['POST'])
def create_relation():
    return create_relation_query(g)

@app.route('/relation/<relation_id>', methods=['GET', 'DELETE'])
def relation(relation_id):
    if request.method == 'GET':
        return get_relation_query(g, relation_id)
    elif request.method == 'DELETE':
        return delete_relation_query(g, relation_id)
    


if __name__ == '__main__':
    app.run(debug=True)