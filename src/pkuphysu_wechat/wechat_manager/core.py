import json
import random
import re
from datetime import datetime
from http.cookiejar import Cookie
from logging import getLogger
from typing import Optional, Tuple
from urllib.parse import quote

import requests

from .models import WechatSession

logger = getLogger(__name__)

MP_BASE = "https://mp.weixin.qq.com"
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0"
)
REQUEST_TIMEOUT = (3, 8)

FINGERPRINT_PATTERN = re.compile(r"[0-9a-fA-F]{32}")


def new_sessionid() -> str:
    "照页面：Date.now() + Math.floor(Math.random()*100)"
    return f"{int(datetime.now().timestamp() * 1000)}{random.randint(0, 99)}"


def new_session(user_agent: str = DEFAULT_USER_AGENT) -> requests.Session:
    session = requests.Session()
    session.headers["User-Agent"] = user_agent
    return session


def serialize_cookies(session: requests.Session) -> str:
    cookies = []
    for cookie in session.cookies:
        cookies.append(
            {
                "name": cookie.name,
                "value": cookie.value,
                "domain": cookie.domain,
                "path": cookie.path,
                "expires": cookie.expires,
                "secure": cookie.secure,
                "rest": {"HttpOnly": cookie.has_nonstandard_attr("HttpOnly")},
            }
        )
    return json.dumps(cookies)


def load_cookies(session: requests.Session, raw: str):
    for item in json.loads(raw):
        session.cookies.set_cookie(
            Cookie(
                version=0,
                name=item["name"],
                value=item["value"],
                port=None,
                port_specified=False,
                domain=item["domain"],
                domain_specified=bool(item["domain"]),
                domain_initial_dot=item["domain"].startswith("."),
                path=item["path"],
                path_specified=bool(item["path"]),
                secure=item["secure"],
                expires=item["expires"],
                discard=False,
                comment=None,
                comment_url=None,
                rest=item["rest"],
            )
        )


class MpClient:
    "One protocol client bound to a Session + fingerprint (+ token when logged in)"

    def __init__(
        self,
        session: requests.Session,
        fingerprint: str,
        token: str = "",
        user_agent: str = DEFAULT_USER_AGENT,
    ):
        self.session = session
        self.fingerprint = fingerprint
        self.token = token or ""
        self.session.headers["User-Agent"] = user_agent

    @property
    def headers(self):
        return {"Origin": MP_BASE, "Referer": MP_BASE + "/"}

    def _common_params(self):
        return {
            "token": self.token,
            "lang": "zh_CN",
            "f": "json",
            "ajax": "1",
            "fingerprint": self.fingerprint,
        }

    def _post_json(self, path: str, data: dict) -> dict:
        resp = self.session.post(
            MP_BASE + path,
            data={**data, **self._common_params()},
            headers=self.headers,
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json()

    def prelogin(self) -> dict:
        return self._post_json("/cgi-bin/bizlogin", {"action": "prelogin"})

    def startlogin(self, sessionid: str) -> dict:
        return self._post_json(
            "/cgi-bin/bizlogin?action=startlogin",
            {
                "userlang": "zh_CN",
                "redirect_url": quote(MP_BASE + "/", safe=""),
                "login_type": "3",
                "sessionid": sessionid,
            },
        )

    def get_qrcode(self) -> bytes:
        resp = self.session.get(
            f"{MP_BASE}/cgi-bin/scanloginqrcode?action=getqrcode"
            f"&random={int(datetime.now().timestamp() * 1000)}&login_appid=",
            headers=self.headers,
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.content

    def ask(self) -> dict:
        resp = self.session.get(
            MP_BASE + "/cgi-bin/scanloginqrcode?action=ask",
            params=self._common_params(),
            headers=self.headers,
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json()

    def login(self) -> dict:
        return self._post_json(
            "/cgi-bin/bizlogin?action=login",
            {
                "userlang": "zh_CN",
                "redirect_url": "",
                "cookie_forbidden": "0",
                "cookie_cleaned": "1",
                "plugin_used": "0",
                "login_type": "3",
            },
        )

    def get_fans_info(self, openid: str) -> Optional[str]:
        "Return user_head_img URL, or None on any failure"
        try:
            resp = self._post_json(
                "/cgi-bin/user_tag?action=get_fans_info",
                {"user_openid": openid, "identity_open_id": ""},
            )
        except requests.RequestException:
            logger.info("MpFansInfoRequestFailed openid=%s", openid)
            return None
        except ValueError:
            logger.info("MpFansInfoNotJson openid=%s", openid)
            return None
        ret = resp.get("base_resp", {}).get("ret")
        if ret != 0:
            logger.info(
                "MpFansInfoRejected openid=%s ret=%s err_msg=%s",
                openid,
                ret,
                resp.get("base_resp", {}).get("err_msg"),
            )
            return None
        user_info_list = resp.get("user_list", {}).get("user_info_list") or []
        if not user_info_list:
            logger.info("MpFansInfoEmpty openid=%s", openid)
            return None
        head_img = user_info_list[0].get("user_head_img")
        if not head_img:
            logger.info(
                "MpFansInfoNoHeadImg openid=%s keys=%s",
                openid,
                sorted(user_info_list[0]),
            )
        return head_img

    def check_home(self) -> bool:
        "Session validity probe: valid sessions stay on the tokenized home page"
        resp = self.session.get(
            MP_BASE + "/cgi-bin/home",
            params={"t": "home/index", "lang": "zh_CN", "token": self.token},
            headers=self.headers,
            timeout=REQUEST_TIMEOUT,
            allow_redirects=True,
        )
        resp.raise_for_status()
        return "token=" in resp.url


def client_from_credentials(credentials) -> MpClient:
    cookies, fingerprint, token, user_agent = credentials
    session = new_session(user_agent)
    load_cookies(session, cookies)
    return MpClient(session, fingerprint, token, user_agent)


def client_from_session_row(session_row: WechatSession) -> MpClient:
    return client_from_credentials(
        (
            session_row.cookies,
            session_row.fingerprint,
            session_row.token,
            session_row.user_agent,
        )
    )


def get_mp_credentials():
    """Snapshot of the stored session as a plain tuple.

    Callers working in worker threads must pass this snapshot to fetch_avatar
    instead of letting it query the DB: db.session needs a Flask app context,
    which worker threads do not have.
    """
    session_row = WechatSession.get_active()
    if session_row is None:
        return None
    return (
        session_row.cookies,
        session_row.fingerprint,
        session_row.token,
        session_row.user_agent,
    )


def fetch_avatar(openid: str, mp_credentials=None) -> Optional[Tuple[str, bytes]]:
    """Exchange openid for an avatar: (url, image bytes), or None.

    Returns None immediately when no valid backend session exists; callers
    (e.g. the invest command hook) rely on this to no-op gracefully.
    Worker threads must pass mp_credentials from get_mp_credentials() —
    the default DB lookup needs a Flask app context.
    """
    if mp_credentials is None:
        mp_credentials = get_mp_credentials()
        if mp_credentials is None:
            logger.info("MpAvatarNoSession openid=%s", openid)
            return None
    client = client_from_credentials(mp_credentials)
    url = client.get_fans_info(openid)
    if not url:
        return None
    url = re.sub(r"/\d+$", "/0", url)  # /64 -> /0: 640x640 snapshot
    try:
        img = client.session.get(url, timeout=REQUEST_TIMEOUT)
    except requests.RequestException:
        logger.info("MpAvatarDownloadFailed openid=%s", openid)
        return None
    if not img.ok or not img.content:
        logger.info(
            "MpAvatarDownloadBadResp openid=%s http=%s len=%s",
            openid,
            img.status_code,
            len(img.content),
        )
        return None
    content_type = img.headers.get("Content-Type", "")
    if not content_type.startswith("image/"):
        logger.info("MpAvatarNotImage openid=%s content_type=%s", openid, content_type)
        return None
    return url, img.content


def check_session() -> bool:
    "Probe the stored session. Network errors raise; definitive answers return bool"
    session_row = WechatSession.get_active()
    if session_row is None:
        return False
    client = client_from_session_row(session_row)
    try:
        valid = client.check_home()
    except requests.RequestException:
        logger.info("MpSessionCheckRequestFailed")
        raise
    WechatSession.mark_check(valid)
    return valid
