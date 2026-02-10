from flask import jsonify
from auth.utils import get_current_user_id
from partition.manager import partition_manager
from roles.acl_store import acl_store, ROLE_OWNER


def list_user_trees(g):
    """
    List all trees the current user can access (owner/editor/viewer).
    """
    try:
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({"error": "User not authenticated"}), 401

        all_members = g.V().hasLabel("_Member").has("_partitionKey").elementMap().toList()
        member_counts = {}
        for member_data in all_members:
            partition_key = member_data.get("_partitionKey")
            if not partition_key:
                continue
            _, tree_id = partition_manager.parse_partition_key(partition_key)
            if not tree_id:
                continue
            member_counts[tree_id] = member_counts.get(tree_id, 0) + 1

        roles = acl_store.list_roles_for_user(user_id)
        trees = []

        for entry in roles:
            tree_id = entry.get("treeId")
            role = entry.get("role")
            partition_key = None

            if tree_id:
                if role == ROLE_OWNER:
                    partition_key = partition_manager.generate_partition_key(user_id, tree_id)
                else:
                    # Editor/viewer: look up the owner so we can build the partition key
                    owner_id = acl_store.get_owner(tree_id)
                    if owner_id:
                        partition_key = partition_manager.generate_partition_key(owner_id, tree_id)

            trees.append({
                "tree_id": tree_id,
                "role": role,
                "partition_key": partition_key,
                "member_count": member_counts.get(tree_id, 0)
            })

        return jsonify({
            "trees": trees,
            "count": len(trees)
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def list_owned_trees(g):
    """
    List trees owned by the current user (legacy /myTrees behavior).
    """
    try:
        # Get current user
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({"error": "User not authenticated"}), 401
        
        # Get all members with partition keys
        all_members = g.V().hasLabel("_Member").has("_partitionKey").elementMap().toList()
        
        # Group by partition key
        trees_dict = {}
        
        for member_data in all_members:
            partition_key = member_data.get("_partitionKey")
            
            if partition_key:
                # Check if this tree belongs to the current user
                tree_user_id, tree_id = partition_manager.parse_partition_key(partition_key)
                
                if tree_user_id == user_id:
                    if partition_key not in trees_dict:
                        # First member encountered for this tree
                        trees_dict[partition_key] = {
                            "tree_id": tree_id,
                            "partition_key": partition_key,
                            "member_count": 1,
                        }
                    else:
                        # Additional member in this tree
                        trees_dict[partition_key]["member_count"] += 1
        
        trees = list(trees_dict.values())
        
        return jsonify({
            "trees": trees,
            "count": len(trees),
            "note": "Fetch tree metadata (name, description) from Amplify DynamoDB using tree_id"
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
