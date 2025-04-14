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
    if request.method == "POST":
        return create_member_query(g)
    elif request.method == "DELETE":
        return delete_member_query(g)
    elif request.method == "GET":
        return get_member_query(g)
    elif request.method == "PUT":
        return update_member_query(g)


@app.route("/memberDirectRelations", methods=["GET"])
def get_direct_relations():
    return get_direct_relations_query(g)


@app.route("/members", methods=["GET"])
def get_members():
    return get_all_members_query(g)


@app.route("/relation", methods=["POST"])
def create_relation():
    return create_relation_query(g)


@app.route("/child", methods=["POST", "PUT"])
def child():
    if request.method == "POST":
        return create_child_query(g)
    elif request.method == "PUT":
        return update_child_query(g)


@app.route("/parent", methods=["POST", "PUT"])
def parent():
    if request.method == "POST":
        return create_parent_query(g)
    elif request.method == "PUT":
        return update_parent_query(g)


@app.route("/spouse", methods=["POST", "PUT"])
def spouse():
    if request.method == "POST":
        return create_spouse_query(g)
    elif request.method == "PUT":
        return update_spouse_query(g)


@app.route("/tree", methods=["POST", "GET", "DELETE"])
def tree():
    if request.method == "POST":
        return create_tree_query(g)
    elif request.method == "GET":
        return get_tree_query(g)
    elif request.method == "DELETE":
        return update_tree_query(g)


if __name__ == "__main__":
    app.run(debug=True)
