from flask import jsonify
from utils import normalize_vertex
import validation.dataTypes as vdt
import validation.coreTreeLogic as vbl
from validation.performValidations import perform_validations
from partition.query_helper import PartitionedQueryHelper
from partition.middleware import get_current_partition


def create_member_query(g, data):
    try:
        if data is None:
            return jsonify({"error": "No JSON data provided"}), 400

        name = data.get("name")
        surname = data.get("surname")
        gender = data.get("gender")
        description = data.get("description")
        born = data.get("born")
        died = data.get("died")
        pic = data.get("pic")
        photos = data.get("photos")

        required_fields = [
            "name",
            "surname",
            "gender",
            "description",
            "born",
            "pic",
            "photos",
        ]
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required fields"}), 400

        validations = [
            (vdt.validate_member_name, ("name", name)),
            (vdt.validate_member_name, ("surname", surname)),
            (vdt.validate_gender, (gender,)),
            (vdt.validate_member_description, (description,)),
            (vdt.validate_date_format, (born,)),
            (vdt.validate_url, ("pic", pic)),
            (vdt.validate_url, ("photos", photos)),
            (vbl.validate_death_date_required_for_old_birth, (born, died)),
        ]

        if died:
            validations.append((vdt.validate_date_format, (died,)))
            validations.append((vbl.validate_life_date_order, (born, died)))
            validations.append((vbl.validate_max_lifespan, (born, died)))

        result = perform_validations(validations)
        if result:
            return result

        # Build properties dict
        properties = {
            "name": name,
            "surname": surname,
            "gender": gender,
            "description": description,
            "born": born,
            "pic": pic,
            "photos": photos,
        }
        
        if died:
            properties["died"] = died

        partition_key = get_current_partition()
        if not partition_key:
            return jsonify({"error": "Partition key is required"}), 400

        new_member = PartitionedQueryHelper.create_partitioned_vertex(
            g=g,
            label="_Member",
            properties=properties,
            partition_key=partition_key,
        )

        return normalize_vertex(new_member), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500
