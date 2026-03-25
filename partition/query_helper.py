from flask import jsonify
from gremlin_python.process.graph_traversal import __

from .middleware import get_current_partition


class PartitionedQueryHelper:
    """Helper class for creating partitioned Gremlin queries"""
    
    @staticmethod
    def validate_vertex_in_partition(g, vertex_id, partition_key: str = None):
        """
        Validate that a vertex belongs to the current partition
        
        Args:
            g: Gremlin traversal source
            vertex_id: The vertex ID to validate
            partition_key: The partition key (uses current context if None)
            
        Returns:
            Tuple of (is_valid: bool, error_response)
        """
        if partition_key is None:
            partition_key = get_current_partition()
        
        if not partition_key:
            return False, (jsonify({"error": "No partition context"}), 400)
        
        # Check if vertex exists
        vertex_exists = g.V(vertex_id).hasNext()
        if not vertex_exists:
            return False, (jsonify({"error": f"Vertex {vertex_id} does not belong to this tree partition"}), 404)
        
        # Check if vertex belongs to the partition
        vertex_in_partition = g.V(vertex_id).has("_partitionKey", partition_key).hasNext()
        if not vertex_in_partition:
            return False, (jsonify({"error": f"Vertex {vertex_id} does not belong to this tree partition"}), 404)
        
        return True, None
    
    @staticmethod
    def validate_vertices_in_partition(g, vertex_ids: list, partition_key: str = None):
        """
        Validate that multiple vertices belong to the current partition
        
        Args:
            g: Gremlin traversal source
            vertex_ids: List of vertex IDs to validate
            partition_key: The partition key (uses current context if None)
            
        Returns:
            Tuple of (is_valid: bool, error_response)
        """
        for vertex_id in vertex_ids:
            if vertex_id is None:
                continue
            is_valid, error_response = PartitionedQueryHelper.validate_vertex_in_partition(
                g, vertex_id, partition_key
            )
            if not is_valid:
                return False, error_response
        
        return True, None
    
    @staticmethod
    def add_partition_filter(traversal, partition_key: str = None):
        """
        Add partition filter to any Gremlin traversal
        
        Args:
            traversal: The Gremlin traversal to filter
            partition_key: The partition key to filter by (uses current context if None)
            
        Returns:
            Filtered traversal
        """
        if partition_key is None:
            partition_key = get_current_partition()
        
        if not partition_key:
            raise ValueError("No partition key available for filtering")
        
        return traversal.has("_partitionKey", partition_key)
    
    @staticmethod
    def create_partitioned_vertex(g, label: str, properties: dict, partition_key: str = None):
        """
        Create vertex with partition key
        
        Args:
            g: Gremlin traversal source
            label: Vertex label
            properties: Vertex properties
            partition_key: Partition key (uses current context if None)
            
        Returns:
            Created vertex
        """
        if partition_key is None:
            partition_key = get_current_partition()
        
        if not partition_key:
            raise ValueError("No partition key available for vertex creation")
        
        # Start with vertex creation
        vertex = g.addV(label)
        
        # Add all properties
        for key, value in properties.items():
            if value is not None:  # Skip null values
                vertex = vertex.property(key, value)
        
        # Add partition key
        vertex = vertex.property("_partitionKey", partition_key)
        
        return vertex.next()
    
    @staticmethod
    def create_partitioned_edge(g, from_vertex_id, to_vertex_id, label: str, properties: dict = None, partition_key: str = None):
        """
        Create edge with partition key
        
        Args:
            g: Gremlin traversal source
            from_vertex_id: Source vertex ID
            to_vertex_id: Target vertex ID
            label: Edge label
            properties: Edge properties
            partition_key: Partition key (uses current context if None)
            
        Returns:
            Created edge
        """
        if partition_key is None:
            partition_key = get_current_partition()
        
        if not partition_key:
            raise ValueError("No partition key available for edge creation")
        
        # Start with edge creation
        edge = g.V(from_vertex_id).addE(label).to(__.V(to_vertex_id))
        
        # Add properties if provided
        if properties:
            for key, value in properties.items():
                if value is not None:  # Skip null values
                    edge = edge.property(key, value)
        
        # Add partition key
        edge = edge.property("_partitionKey", partition_key)
        
        return edge.next()
    
    @staticmethod
    def get_vertices_by_partition(g, label: str = None, partition_key: str = None):
        """
        Get all vertices in a partition
        
        Args:
            g: Gremlin traversal source
            label: Optional vertex label filter
            partition_key: Partition key (uses current context if None)
            
        Returns:
            Traversal for vertices in partition
        """
        if partition_key is None:
            partition_key = get_current_partition()
        
        if not partition_key:
            raise ValueError("No partition key available")
        
        traversal = g.V().has("_partitionKey", partition_key)
        
        if label:
            traversal = traversal.hasLabel(label)
        
        return traversal
    
    @staticmethod
    def get_edges_by_partition(g, label: str = None, partition_key: str = None):
        """
        Get all edges in a partition
        
        Args:
            g: Gremlin traversal source
            label: Optional edge label filter
            partition_key: Partition key (uses current context if None)
            
        Returns:
            Traversal for edges in partition
        """
        if partition_key is None:
            partition_key = get_current_partition()
        
        if not partition_key:
            raise ValueError("No partition key available")
        
        traversal = g.E().has("_partitionKey", partition_key)
        
        if label:
            traversal = traversal.hasLabel(label)
        
        return traversal
    
    @staticmethod
    def count_vertices_by_partition(g, label: str = None, partition_key: str = None):
        """
        Count vertices in a partition
        
        Args:
            g: Gremlin traversal source
            label: Optional vertex label filter
            partition_key: Partition key (uses current context if None)
            
        Returns:
            Count of vertices
        """
        return PartitionedQueryHelper.get_vertices_by_partition(g, label, partition_key).count().next()
    
    @staticmethod
    def count_edges_by_partition(g, label: str = None, partition_key: str = None):
        """
        Count edges in a partition
        
        Args:
            g: Gremlin traversal source
            label: Optional edge label filter
            partition_key: Partition key (uses current context if None)
            
        Returns:
            Count of edges
        """
        return PartitionedQueryHelper.get_edges_by_partition(g, label, partition_key).count().next()
    
    @staticmethod
    def delete_partition(g, partition_key: str = None):
        """
        Delete all vertices and edges in a partition
        
        Args:
            g: Gremlin traversal source
            partition_key: Partition key (uses current context if None)
            
        Returns:
            Number of deleted elements
        """
        if partition_key is None:
            partition_key = get_current_partition()
        
        if not partition_key:
            raise ValueError("No partition key available")
        
        # Delete all edges in partition
        g.E().has("_partitionKey", partition_key).drop().iterate()
        
        # Delete all vertices in partition
        vertex_count = g.V().has("_partitionKey", partition_key).drop().iterate()
        
        return vertex_count
