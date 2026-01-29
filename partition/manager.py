import uuid
import re
from typing import Optional, Tuple

class PartitionManager:
    """Manages partition keys for multi-tenant tree isolation"""
    
    @staticmethod
    def generate_partition_key(user_id: str, tree_id: str) -> str:
        """
        Generate a partition key for a user's tree
        
        Args:
            user_id: The user's unique identifier
            tree_id: The tree's unique identifier
            
        Returns:
            Partition key in format: "{user_id}_{tree_id}"
        """
        # Clean the user_id and tree_id to ensure they're safe for use
        clean_user_id = PartitionManager._sanitize_id(user_id)
        clean_tree_id = PartitionManager._sanitize_id(tree_id)
        
        return f"{clean_user_id}_{clean_tree_id}"
    
    @staticmethod
    def parse_partition_key(partition_key: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Parse a partition key to extract user_id and tree_id
        
        Args:
            partition_key: The partition key to parse
            
        Returns:
            Tuple of (user_id, tree_id) or (None, None) if invalid
        """
        if not partition_key or '_' not in partition_key:
            return None, None
        
        # Split on the last underscore to handle user_ids that might contain underscores
        parts = partition_key.rsplit('_', 1)
        if len(parts) != 2:
            return None, None
        
        user_id, tree_id = parts
        return user_id, tree_id
    
    @staticmethod
    def validate_partition_key(partition_key: str) -> bool:
        """
        Validate that a partition key has the correct format
        
        Args:
            partition_key: The partition key to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not partition_key:
            return False
        
        # Check format: should contain at least one underscore
        if '_' not in partition_key:
            return False
        
        # Check length (reasonable limits)
        if len(partition_key) < 3 or len(partition_key) > 100:
            return False
        
        # Check for valid characters (alphanumeric, underscore, hyphen)
        if not re.match(r'^[a-zA-Z0-9_-]+$', partition_key):
            return False
        
        return True
    
    @staticmethod
    def generate_tree_id() -> str:
        """
        Generate a unique tree ID
        
        Returns:
            A unique tree identifier
        """
        return str(uuid.uuid4())
    
    @staticmethod
    def user_owns_partition(user_id: str, partition_key: str) -> bool:
        """
        Check if a user owns a specific partition
        
        Args:
            user_id: The user's ID
            partition_key: The partition key to check
            
        Returns:
            True if user owns the partition, False otherwise
        """
        parsed_user_id, _ = PartitionManager.parse_partition_key(partition_key)
        return parsed_user_id == user_id
    
    @staticmethod
    def _sanitize_id(id_string: str) -> str:
        """
        Sanitize an ID string for safe use in partition keys
        
        Args:
            id_string: The ID to sanitize
            
        Returns:
            Sanitized ID string
        """
        if not id_string:
            return ""
        
        # Remove any potentially dangerous characters
        sanitized = re.sub(r'[^a-zA-Z0-9_-]', '', str(id_string))
        
        # Ensure it's not empty
        if not sanitized:
            sanitized = "default"
        
        return sanitized


# Global instance
partition_manager = PartitionManager()
