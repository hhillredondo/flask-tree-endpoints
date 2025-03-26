import json


def normalize_data(vertex):
    try:
        # Extract basic vertex information
        normalized_data = {
            "id": str(vertex.id),  # Convert ID to string
            "label": vertex.label,
        }

        # Extract properties from the list of VertexProperty objects
        properties = {}
        for prop in vertex.properties:
            key = prop.key  # Property name (e.g., "name", "born")
            value = prop.value  # Property value (e.g., "John", "1990-01-01")
            properties[key] = value

        normalized_data.update(properties)
        return normalized_data
    except Exception as e:
        print(f"Error normalizing data: {e}")
        raise
