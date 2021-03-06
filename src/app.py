import os
import sys

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
    # Tencent does not catch stdout here
    print(f"Received {event}", file=sys.stderr)
    if event.get("Type") == "Timer" and event.get("TriggerName") == "health-check":
        requests.post(RESPONSE_URL, json={"message": "ok"})
        continue
    try:
        resp = handle_request(app, event)
        requests.post(RESPONSE_URL, json=resp)
    except Exception:
        import traceback

        traceback.print_exc()
        requests.post(ERROR_URL, json={"msg": "Error, see log"})
