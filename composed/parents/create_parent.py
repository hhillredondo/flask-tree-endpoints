from flask import jsonify
from composed.spouses.create_spouse import create_spouse
from utils import get_born, get_parents_number, normalize_vertex
import validation.dataTypes as vdt
import validation.coreTreeLogic as ctl
from validation.performValidations import perform_validations
from partition.query_helper import PartitionedQueryHelper
from partition.middleware import get_current_partition


def create_parent(g, data):

    try:
        if data is None:
            return jsonify({"error": "No JSON data provided"}), 400

        child_id = data.get("child_id")
        name = data.get("name")
        surname = data.get("surname")
        gender = data.get("gender")
        description = data.get("description")
        born = data.get("born")
        died = data.get("died")
        pic = data.get("pic")
        photos = data.get("photos")
        profession = data.get("profession")
        birth_location = data.get("birth_location")
        death_location = data.get("death_location")
        height = data.get("height")

        required_fields = [
            "child_id",
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

        # PARTITION VALIDATION: Ensure child_id is in the current partition
        is_valid, error_response = PartitionedQueryHelper.validate_vertex_in_partition(g, child_id)
        if not is_valid:
            return error_response

        existing_parents = get_parents_number(child_id, g)

        validations = [
            (vdt.validate_vertex_exists, (child_id, "Target", g)),
            (ctl.validate_parents_number, (existing_parents,)),
            (vdt.validate_member_name, ("name", name)),
            (vdt.validate_member_name, ("surname", surname)),
            (vdt.validate_gender, (gender,)),
            (vdt.validate_member_description, (description,)),
            (vdt.validate_date_format, (born,)),
            (vdt.validate_url, ("pic", pic)),
            (vdt.validate_url, ("photos", photos)),
            (ctl.validate_death_date_required_for_old_birth, (born, died)),
        ]

        if died:
            validations.append((vdt.validate_date_format, (died,)))
            validations.append((ctl.validate_life_date_order, (born, died)))
            validations.append((ctl.validate_max_lifespan, (born, died)))

        child_born = get_born(child_id, g)

        validations.append(
            (ctl.validate_parent_is_alive_and_fertile, (gender, born, died, child_born))
        )

        result = perform_validations(validations)
        if result:
            return result

        # Get partition key from context
        partition_key = get_current_partition()
        if not partition_key:
            return jsonify({"error": "No partition context"}), 400

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
        if profession:
            properties["profession"] = profession
        if birth_location:
            properties["birth_location"] = birth_location
        if death_location:
            properties["death_location"] = death_location
        if height is not None:
            properties["height"] = height

        # Create parent vertex with partition key
        parent = PartitionedQueryHelper.create_partitioned_vertex(
            g=g,
            label="_Member",
            properties=properties,
            partition_key=partition_key
        )

        # Create parent-child relationship with partition key
        PartitionedQueryHelper.create_partitioned_edge(
            g=g,
            from_vertex_id=parent.id,
            to_vertex_id=child_id,
            label="parent",
            properties=None,
            partition_key=partition_key
        )

        return normalize_vertex(parent), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500
