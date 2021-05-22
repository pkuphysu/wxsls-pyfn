import os

import requests

from pkuphysu_wechat import create_app
from sls_wsgi import handle_request

SCF_HOST = os.environ.get("SCF_RUNTIME_API")
SCF_PORT = os.environ.get("SCF_RUNTIME_API_PORT")
FUNC_NAME = os.environ.get("_HANDLER")

READY_URL = f"http://{SCF_HOST}:{SCF_PORT}/runtime/init/ready"
EVENT_URL = f"http://{SCF_HOST}:{SCF_PORT}/runtime/invocation/next"
RESPONSE_URL = f"http://{SCF_HOST}:{SCF_PORT}/runtime/invocation/response"
ERROR_URL = f"http://{SCF_HOST}:{SCF_PORT}/runtime/invocation/error"

app = create_app()

requests.post(
    READY_URL,
    headers={"Content-Type": "application/x-www-form-urlencoded"},
    data="",
)

while True:
    event = requests.get(EVENT_URL).json()
    print(f"Received {event}")
    try:
        resp = handle_request(app, event)
        requests.post(RESPONSE_URL, json=resp)
    except Exception as e:
        requests.post(ERROR_URL, json=dict(msg=str(e)))
