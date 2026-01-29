import os
import ssl
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from botocore.session import Session
from gremlin_python.driver.aiohttp.transport import AiohttpTransport
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.process.anonymous_traversal import traversal


def _get_sigv4_headers(url: str, region: str) -> dict:
    session = Session()
    credentials = session.get_credentials()
    if credentials is None:
        raise RuntimeError("AWS credentials not available for SigV4 auth")
    frozen = credentials.get_frozen_credentials()
    request = AWSRequest(method="GET", url=url)
    SigV4Auth(frozen, "neptune-db", region).add_auth(request)
    return dict(request.headers)


def _build_transport() -> AiohttpTransport:
    # Neptune IAM auth requires SigV4-signed headers over TLS.
    ssl_context = ssl.create_default_context()
    return AiohttpTransport(
        call_from_event_loop=True,
        ssl=ssl_context,
    )


def create_gremlin_connection():
    endpoint = os.getenv("GREMLIN_ENDPOINT", "localhost")
    port = int(os.getenv("GREMLIN_PORT", "8182"))
    use_ssl = os.getenv("GREMLIN_SSL", "false").lower() == "true"
    use_iam = os.getenv("GREMLIN_IAM_AUTH", "false").lower() == "true"
    region = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION")

    # Neptune uses wss:// (WebSocket Secure), local uses ws://
    protocol = "wss" if use_ssl else "ws"
    connection_string = f"{protocol}://{endpoint}:{port}/gremlin"

    if use_iam:
        if not region:
            raise RuntimeError("AWS_REGION must be set when GREMLIN_IAM_AUTH=true")
        headers = _get_sigv4_headers(connection_string, region)
        transport = _build_transport
        remote = DriverRemoteConnection(
            connection_string,
            "g",
            transport_factory=transport,
            headers=headers,
        )
    else:
        remote = DriverRemoteConnection(connection_string)

    g = traversal().withRemote(remote)
    return g