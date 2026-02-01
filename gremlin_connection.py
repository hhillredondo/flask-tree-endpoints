import logging
import os
import ssl
from boto3 import Session
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from gremlin_python.driver.aiohttp.transport import AiohttpTransport
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.process.anonymous_traversal import traversal


logger = logging.getLogger(__name__)


class SigV4AiohttpTransport(AiohttpTransport):
    """Aiohttp transport that signs each websocket connect with fresh SigV4 headers."""

    def __init__(self, signing_url: str, region: str, host_header: str):
        self._signing_url = signing_url
        self._region = region
        self._host_header = host_header
        ssl_context = ssl.create_default_context()
        super().__init__(call_from_event_loop=True, ssl=ssl_context)

    def connect(self, url, headers=None):
        session = Session()
        credentials = session.get_credentials()
        if credentials is None:
            raise RuntimeError("AWS credentials not available for SigV4 auth")
        creds = credentials.get_frozen_credentials()
        request = AWSRequest(method="GET", url=self._signing_url, data=None)
        if "Host" not in request.headers:
            request.headers["Host"] = self._host_header
        SigV4Auth(creds, "neptune-db", self._region).add_auth(request)
        signed_headers = dict(request.headers)
        logger.info(
            "Gremlin websocket connect (url=%s, has_auth=%s, has_token=%s, host=%s)",
            url,
            "Authorization" in signed_headers,
            "X-Amz-Security-Token" in signed_headers,
            signed_headers.get("Host"),
        )
        return super().connect(url, signed_headers)


def create_gremlin_connection():
    endpoint = os.getenv("GREMLIN_ENDPOINT", "localhost")
    port = int(os.getenv("GREMLIN_PORT", "8182"))
    use_ssl = os.getenv("GREMLIN_SSL", "false").lower() == "true"
    use_iam = os.getenv("GREMLIN_IAM_AUTH", "false").lower() == "true"
    default_region = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION") or "us-east-1"

    # Neptune uses wss:// (WebSocket Secure), local uses ws://
    protocol = "wss" if use_ssl else "ws"
    connection_string = f"{protocol}://{endpoint}:{port}/gremlin"

    if use_iam:
        session = Session()
        region = session.region_name if session.region_name else default_region
        logger.info(
            "Using IAM auth for Gremlin (endpoint=%s, region=%s, url=%s)",
            endpoint,
            region,
            connection_string,
        )
        transport = lambda: SigV4AiohttpTransport(
            signing_url=connection_string,
            region=region,
            host_header=endpoint,
        )
        remote = DriverRemoteConnection(
            connection_string,
            "g",
            transport_factory=transport,
        )
    else:
        remote = DriverRemoteConnection(connection_string)

    g = traversal().withRemote(remote)
    return g