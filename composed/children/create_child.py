from flask import jsonify
from utils import (
    get_born,
    get_died,
    get_gender,
    get_potential_spouse_at_child_birth,
    get_parents_other_children_birth_dates,
    normalize_vertex,
)
import validation.dataTypes as vdt
import validation.coreTreeLogic as ctl
from validation.performValidations import perform_validations
from gremlin_python.process.traversal import T
from partition.query_helper import PartitionedQueryHelper
from partition.middleware import get_current_partition


def create_child(g, data):

    try:
        if data is None:
            return jsonify({"error": "No JSON data provided"}), 400

        parent_id = data.get("parent_id")
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
            "parent_id",
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

        # PARTITION VALIDATION: Ensure parent_id is in the current partition
        is_valid, error_response = PartitionedQueryHelper.validate_vertex_in_partition(g, parent_id)
        if not is_valid:
            return error_response

        parent_exists, error_msg = vdt.validate_vertex_exists(parent_id, "Source", g)
        if not parent_exists:
            return jsonify({"error": error_msg}), 400

        validations = [
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

        parent_gender = get_gender(parent_id, g)
        parent_born = get_born(parent_id, g)
        parent_died = get_died(parent_id, g)

        validations.append(
            (
                ctl.validate_parent_is_alive_and_fertile,
                (parent_gender, parent_born, parent_died, born),
            )
        )

        parent_children_birth_dates = get_parents_other_children_birth_dates(
            parent_id, g
        )
        validations.append(
            (
                ctl.validate_siblings_birth_dates,
                (born, parent_children_birth_dates),
            )
        )

        potential_spouse = get_potential_spouse_at_child_birth(parent_id, born, g)

        if potential_spouse != None:
            spouse_id = potential_spouse.get(T.id)
            spouse_gender = potential_spouse.get("gender")
            spouse_born = potential_spouse.get("born")
            spouse_died = potential_spouse.get("died")
            validations.append(
                (
                    ctl.validate_parent_is_alive_and_fertile,
                    (spouse_gender, spouse_born, spouse_died, born),
                )
            )

            spouse_children_birth_dates = get_parents_other_children_birth_dates(
                spouse_id, g
            )
            validations.append(
                (
                    ctl.validate_siblings_birth_dates,
                    (born, spouse_children_birth_dates),
                )
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
            properties["height"] = str(height)

        # Create child vertex with partition key
        child = PartitionedQueryHelper.create_partitioned_vertex(
            g=g,
            label="_Member",
            properties=properties,
            partition_key=partition_key
        )

        # Create parent-child relationship with partition key
        PartitionedQueryHelper.create_partitioned_edge(
            g=g,
            from_vertex_id=parent_id,
            to_vertex_id=child.id,
            label="parent",
            properties=None,
            partition_key=partition_key
        )

        # If there's a potential spouse, create edge from spouse to child
        if potential_spouse != None:
            spouse_id = potential_spouse.get(T.id)
            PartitionedQueryHelper.create_partitioned_edge(
                g=g,
                from_vertex_id=spouse_id,
                to_vertex_id=child.id,
                label="parent",
                properties=None,
                partition_key=partition_key
            )

        return normalize_vertex(child), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500
