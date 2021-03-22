import sys
from base64 import b64decode
from io import BytesIO
from logging import getLogger
from urllib.parse import urlencode

from . import create_app


def transform_header(header: str):
    return "HTTP_" + header.upper().replace("-", "_")


class ResponseHandler:
    def __init__(self) -> None:
        self.response = {
            "isBase64Encoded": False,
            "statusCode": 200,
            "headers": {},
            "body": "",
        }

    def start_response(self, status: str, response_headers, exc_info=None):
        self.response["statusCode"] = int(status.split(" ")[0])
        self.response["headers"] = {k: v for k, v in response_headers}

    def write(self, data: bytes):
        self.response["body"] += data.decode()


# Declare `app` here to optimize cloud function performance
app = create_app()
logger = getLogger(__name__)


def main(event, context):
    logger.info("Event: %s", event)
    logger.info("Context: %s", context)
    request_body = event.get("body", "").encode()
    if event["isBase64Encoded"]:
        request_body = b64decode(request_body)
    environ = {
        "REQUEST_METHOD": event["httpMethod"],
        "SCRIPT_NAME": "",
        "PATH_INFO": event["path"],
        "QUERY_STRING": urlencode(event.get("queryStringParameters", "")),
        "wsgi.version": (1, 0),
        "wsgi.url_scheme": event["headers"]["x-forwarded-proto"],
        "wsgi.input": BytesIO(request_body),
        "wsgi.input_terminated": True,
        "wsgi.errors": sys.stderr,
        **{transform_header(k): v for k, v in event["headers"].items()},
    }
    if "HTTP_CONTENT_TYPE" in environ:
        environ["CONTENT_TYPE"] = environ["HTTP_CONTENT_TYPE"]
    print(environ)
    response_handler = ResponseHandler()
    for data in app(environ, response_handler.start_response):
        response_handler.write(data)
    return response_handler.response
