from gremlin_python.process.anonymous_traversal import traversal
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection


def create_gremlin_connection():
    g = traversal().withRemote(
          DriverRemoteConnection('ws://localhost:8182/gremlin'))

    return g