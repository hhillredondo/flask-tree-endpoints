from flask import Flask, jsonify, request
from gremlin_connection import create_gremlin_connection
from members.create_members import create_member_query
from members.update_members import update_member_query
from members.get_members import get_member_query, get_all_members_query
from members.delete_members import delete_member_query
from relations.create_relations import create_relation_query


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


@app.route("/members", methods=["GET"])
def get_members():
    return get_all_members_query(g)


@app.route("/relation", methods=["POST"])
def create_relation():
    return create_relation_query(g)


if __name__ == "__main__":
    app.run(debug=True)
