import os
from gremlin_python.process.anonymous_traversal import traversal
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection


def create_gremlin_connection():
    endpoint = os.getenv('GREMLIN_ENDPOINT', 'localhost')
    port = int(os.getenv('GREMLIN_PORT', '8182'))
    ssl = os.getenv('GREMLIN_SSL', 'false').lower() == 'true'
    
    # Neptune uses wss:// (WebSocket Secure), local uses ws://
    protocol = 'wss' if ssl else 'ws'
    connection_string = f'{protocol}://{endpoint}:{port}/gremlin'
    
    g = traversal().withRemote(
        DriverRemoteConnection(connection_string))
    
    return g