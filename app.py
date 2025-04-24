from flask import Flask, jsonify, request
from gremlin_connection import create_gremlin_connection
from members.create_member import create_member_query
from members.update_member import update_member_query
from members.get_member import (
    get_direct_relations_query,
    get_member_query,
    get_all_members_query,
)
from members.delete_member import delete_member_query
from relations.create_relation import create_relation_query


app = Flask(__name__)

g = create_gremlin_connection()


@app.route("/", methods=["GET"])
def get_vertices_count():
    try:
        result_set = g.V().count().next()
        return jsonify(result_set)
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route("/member", methods=["POST", "DELETE", "GET", "PUT"])
def member():
    data = request.get_json()
    if request.method == "POST":
        return create_member_query(g, data)
    elif request.method == "DELETE":
        return delete_member_query(g, data)
    elif request.method == "GET":
        return get_member_query(g, data)
    elif request.method == "PUT":
        return update_member_query(g, data)


@app.route("/memberDirectRelations", methods=["GET"])
def get_direct_relations():
    data = request.get_json()
    return get_direct_relations_query(g, data)


@app.route("/members", methods=["GET"])
def get_members():
    return get_all_members_query(g)


@app.route("/relation", methods=["POST"])
def create_relation():
    data = request.get_json()
    return create_relation_query(g, data)


@app.route("/child", methods=["POST", "PUT"])
def child():
    data = request.get_json()
    if request.method == "POST":
        return create_child_query(g, data)
    elif request.method == "PUT":
        return update_child_query(g, data)


@app.route("/parent", methods=["POST", "PUT"])
def parent():
    data = request.get_json()
    if request.method == "POST":
        return create_parent_query(g, data)
    elif request.method == "PUT":
        return update_parent_query(g, data)


@app.route("/spouse", methods=["POST", "PUT"])
def spouse():
    data = request.get_json()
    if request.method == "POST":
        return create_spouse_query(g, data)
    elif request.method == "PUT":
        return update_spouse_query(g, data)


@app.route("/tree", methods=["POST", "GET", "DELETE"])
def tree():
    data = request.get_json()
    if request.method == "POST":
        return create_tree_query(g, data)
    elif request.method == "GET":
        return get_tree_query(g, data)
    elif request.method == "DELETE":
        return update_tree_query(g, data)


if __name__ == "__main__":
    app.run(debug=True)
