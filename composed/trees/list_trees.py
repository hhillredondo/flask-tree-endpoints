from flask import jsonify
from auth.utils import get_current_user_id
from partition.manager import partition_manager


def list_user_trees(g):
    """
    List all trees for the current authenticated user
    
    Scans all members and groups by partition key to find unique trees.
    Tree metadata (name, description) should be fetched from Amplify DynamoDB.
    
    Args:
        g: Gremlin traversal source
        
    Returns:
        List of user's trees with partition keys and basic stats
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
                        # First member of this tree
                        trees_dict[partition_key] = {
                            "tree_id": tree_id,
                            "partition_key": partition_key,
                            "member_count": 1,
                            "first_member": {
                                "id": str(member_data.get("id")),
                                "name": member_data.get("name", ""),
                                "surname": member_data.get("surname", "")
                            }
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
