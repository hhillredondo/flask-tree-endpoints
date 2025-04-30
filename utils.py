def normalize_vertex(vertex):
    try:
        normalized_data = {
            "id": str(vertex.id),
            "label": vertex.label,
        }

        properties = {}
        for prop in vertex.properties:
            key = prop.key
            value = prop.value
            properties[key] = value

        normalized_data.update(properties)
        return normalized_data
    except Exception as e:
        print(f"Error normalizing data: {e}")
        raise


def normalize_edge(edge):
    return {
        "id": str(edge.id),
        "label": edge.label,
        "source_id": str(edge.outV.id),
        "target_id": str(edge.inV.id),
    }


def check_gender(vertex_id: int, g):
    gender_iter = g.V(vertex_id).values("gender")
    if gender_iter.hasNext():
        gender = gender_iter.next()
        return True, "", gender
    else:
        return False, "Vertex does not have a 'gender' property", None


def check_born(vertex_id: int, g):
    born_iter = g.V(vertex_id).values("born")
    if born_iter.hasNext():
        born = born_iter.next()
        return True, "", born
    else:
        return False, "Vertex does not have a 'born' property", None


def check_died(vertex_id: int, g):
    died_iter = g.V(vertex_id).values("died")
    if died_iter.hasNext():
        died = died_iter.next()
        return True, "", died
    else:
        return False, "Vertex does not have a 'died' property", None
