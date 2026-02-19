from flask import jsonify, current_app
from auth.utils import get_current_user_id
from auth.user_tier import is_limit_exempt
from partition.manager import partition_manager
from partition.middleware import set_partition_context
from members.create_member import create_member_query
from roles.acl_store import ROLE_OWNER, acl_store


def create_tree(g, data):
    """
    Create first member in a new tree
    
    Tree metadata is stored in Amplify DynamoDB.
    This function only creates the first member in Neptune with a partition key.
    
    Args:
        g: Gremlin traversal source
        data: Member data for the tree creator (name, surname, gender, etc.)
              Must include 'tree_id' from Amplify
        
    Returns:
        Created member with partition key information
    """
    try:
        # Get current user
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({"error": "User not authenticated"}), 401
        
        # Check tree limit (only in production, and only for free users)
        if current_app.config.get('ENFORCE_LIMITS') and not is_limit_exempt(user_id):
            roles = acl_store.list_roles_for_user(user_id)
            tree_count = len(roles)
            max_trees = current_app.config.get('MAX_TREES_PER_USER', 3)
            
            if tree_count >= max_trees:
                return jsonify({
                    "error": "Tree limit reached",
                    "message": f"You have reached the limit of {max_trees} trees. You currently have access to {tree_count} trees (as owner, editor, or viewer)."
                }), 403
        
        # Get tree_id from Amplify (required)
        tree_id = data.get("tree_id")
        if not tree_id:
            return jsonify({
                "error": "tree_id is required",
                "message": "tree_id must be provided from Amplify DynamoDB tree record"
            }), 400
        
        # Guard: prevent reusing an existing tree_id in the ACL table
        existing_roles = acl_store.list_roles(tree_id)
        if existing_roles:
            return jsonify({
                "error": "Tree already initialized",
                "message": "tree_id already has ACL entries",
                "tree_id": tree_id,
                "role_count": len(existing_roles)
            }), 409

        # Generate partition key using Amplify tree ID
        partition_key = partition_manager.generate_partition_key(user_id, tree_id)

        # Guard: prevent reusing an existing partition key in Neptune
        if g.V().has("_partitionKey", partition_key).hasNext():
            return jsonify({
                "error": "Tree already initialized",
                "message": "Partition key already exists in Neptune for this tree",
                "partition_key": partition_key
            }), 409
        
        # Set partition context so create_member_query can use it
        set_partition_context(partition_key, user_id, tree_id)

        # Seed ACL: creator is owner
        if not acl_store.put_role(tree_id, user_id, ROLE_OWNER):
            return jsonify({"error": "Failed to assign owner role"}), 500
        
        # Create the first member using the existing create_member_query
        # This will run all the important validations
        member_result = create_member_query(g, data)
        
        # Check if member creation was successful
        if isinstance(member_result, tuple):
            member_data, status_code = member_result
            if status_code != 201:
                return member_result
        else:
            member_data = member_result
        
        # Return partition key and member information
        response = {
            "message": "First member created successfully in tree",
            "tree_id": tree_id,
            "partition_key": partition_key,
            "member": member_data.get_json() if hasattr(member_data, 'get_json') else member_data
        }
        
        return jsonify(response), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500
