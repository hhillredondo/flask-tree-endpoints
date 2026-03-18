from flask import jsonify
from utils import normalize_vertex
import validation.dataTypes as vdt
import validation.coreTreeLogic as vbl
from validation.performValidations import perform_validations
from partition.middleware import get_current_partition


def update_member_query(g, data):
    try:
        if data is None:
            return jsonify({"error": "No JSON data provided"}), 400

        member_id = data.get("id")
        if not member_id:
            return jsonify({"error": "Missing 'id' field"}), 400

        if "born" in data or "died" in data:
            return jsonify({
                "error": "Immutable fields",
                "message": "born and died cannot be modified"
            }), 400

        partition_key = get_current_partition()
        if not partition_key:
            return jsonify({"error": "Partition key is required"}), 400

        member_exists = g.V(member_id).has("_partitionKey", partition_key).hasNext()
        if not member_exists:
            return jsonify({"error": f"Member with ID {member_id} does not exist in this tree"}), 404

        name = data.get("name")
        surname = data.get("surname")
        description = data.get("description")
        pic = data.get("pic")
        photos = data.get("photos")
        profession = data.get("profession")
        birth_location = data.get("birth_location")
        death_location = data.get("death_location")
        height = data.get("height")

        validations = []
        if name:
            validations.append((vdt.validate_member_name, ("name", name)))
        if surname:
            validations.append((vdt.validate_member_name, ("surname", surname)))
        if description:
            validations.append((vdt.validate_member_description, (description,)))
        if pic:
            validations.append((vdt.validate_url, ("pic", pic)))
        if photos:
            validations.append((vdt.validate_url, ("photos", photos)))

        result = perform_validations(validations)
        if result:
            return result

        traversal = g.V(member_id)
        if name:
            traversal.property("name", name)
        if surname:
            traversal.property("surname", surname)
        if description:
            traversal.property("description", description)
        if pic:
            traversal.property("pic", pic)
        if photos:
            traversal.property("photos", photos)
        if "profession" in data:
            traversal.property("profession", profession or "")
        if "birth_location" in data:
            traversal.property("birth_location", birth_location or "")
        if "death_location" in data:
            traversal.property("death_location", death_location or "")
        if "height" in data:
            traversal.property("height", height if height is not None else "")

        updated_member = traversal.next()

        return jsonify(normalize_vertex(updated_member)), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
