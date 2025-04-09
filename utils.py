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
