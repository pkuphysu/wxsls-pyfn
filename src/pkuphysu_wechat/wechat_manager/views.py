import re
from base64 import b64encode
from datetime import datetime, timedelta
from logging import getLogger

import requests
from flask import Blueprint, request

from pkuphysu_wechat import db
from pkuphysu_wechat.auth.utils import master_before_request
from pkuphysu_wechat.utils import respond_error, respond_success

from .core import (
    FINGERPRINT_PATTERN,
    MP_BASE,
    REQUEST_TIMEOUT,
    MpClient,
    check_session,
    load_cookies,
    new_session,
    new_sessionid,
    serialize_cookies,
)
from .models import LOGIN_TTL, WechatLoginSession, WechatSession

logger = getLogger(__name__)

bp = Blueprint("wechat_manager", __name__, url_prefix="/wechat-manager")
bp.before_request(master_before_request)


def qrcode_data_uri(image: bytes) -> str:
    return "data:image/jpeg;base64," + b64encode(image).decode("ascii")


def client_for_login_row(login_row: WechatLoginSession) -> MpClient:
    session = new_session(login_row.user_agent)
    if login_row.cookies:
        load_cookies(session, login_row.cookies)
    return MpClient(session, login_row.fingerprint, user_agent=login_row.user_agent)


def drop_login_row(login_row: WechatLoginSession):
    db.session.delete(login_row)
    db.session.commit()


@bp.route("/login/start", methods=["POST"])
def login_start():
    fingerprint = (request.json or {}).get("fingerprint")
    if not isinstance(fingerprint, str) or not FINGERPRINT_PATTERN.fullmatch(
        fingerprint
    ):
        return respond_error(400, "MpLoginFingerprintInvalid")
    stale = WechatLoginSession.query.filter(
        WechatLoginSession.created_at < datetime.now() - timedelta(seconds=LOGIN_TTL)
    )
    for row in stale:
        db.session.delete(row)
    db.session.commit()
    user_agent = (request.user_agent.string or "")[:256]
    login_row = WechatLoginSession.create(
        fingerprint=fingerprint, sessionid=new_sessionid(), user_agent=user_agent
    )
    session = new_session(user_agent)
    client = MpClient(session, fingerprint, user_agent=user_agent)
    try:
        session.get(MP_BASE + "/", timeout=REQUEST_TIMEOUT)  # bootstrap the cookie jar
        client.prelogin()
        start_resp = client.startlogin(login_row.sessionid)
    except requests.RequestException:
        logger.info("MpLoginStartUpstreamError")
        drop_login_row(login_row)
        return respond_error(502, "MpLoginUpstreamError")
    ret = start_resp.get("base_resp", {}).get("ret")
    if ret != 0:
        logger.info("MpLoginStartRejected ret=%s", ret)
        drop_login_row(login_row)
        return respond_error(502, "MpLoginStartRejected", f"ret={ret}")
    try:
        qrcode = client.get_qrcode()
    except requests.RequestException:
        logger.info("MpLoginQrcodeUpstreamError")
        drop_login_row(login_row)
        return respond_error(502, "MpLoginUpstreamError")
    login_row.cookies = serialize_cookies(session)
    login_row.state = "pending"
    login_row.save()
    return respond_success(
        login_id=login_row.id,
        qrcode=qrcode_data_uri(qrcode),
        expires_in=LOGIN_TTL,
    )


@bp.route("/login/<login_id>")
def login_poll(login_id: str):
    login_row = db.session.get(WechatLoginSession, login_id)
    if login_row is None:
        return respond_error(404, "MpLoginNoState")
    if login_row.expired():
        drop_login_row(login_row)
        return respond_success(state="expired")
    client = client_for_login_row(login_row)
    try:
        ask_resp = client.ask()
    except (requests.RequestException, ValueError):
        logger.info("MpLoginAskUpstreamError")
        return respond_error(502, "MpLoginUpstreamError")
    ret = ask_resp.get("base_resp", {}).get("ret")
    if ret != 0:
        logger.info("MpLoginAskRejected ret=%s", ret)
        return respond_error(502, "MpLoginAskRejected", f"ret={ret}")
    status = ask_resp.get("status")
    if status == 1:
        return confirm_login(login_row, client)
    if status in (2, 3):
        return refresh_qrcode(login_row, client)
    if status in (4, 6):
        login_row.state = "scanned"
        login_row.save()
        return respond_success(state="scanned", acct_size=ask_resp.get("acct_size"))
    if status == 5:
        return respond_success(state="need_email")
    return respond_success(state="pending")


def confirm_login(login_row: WechatLoginSession, client: MpClient):
    try:
        login_resp = client.login()
    except (requests.RequestException, ValueError):
        logger.info("MpLoginConfirmUpstreamError")
        return respond_error(502, "MpLoginUpstreamError")
    ret = login_resp.get("base_resp", {}).get("ret")
    token_match = re.search(r"token=(\d+)", login_resp.get("redirect_url") or "")
    if ret != 0 or not token_match:
        logger.info("MpLoginConfirmFailed ret=%s", ret)
        return respond_error(502, "MpLoginConfirmFailed", f"ret={ret}")
    WechatSession.store(
        cookies=serialize_cookies(client.session),
        fingerprint=login_row.fingerprint,
        token=token_match.group(1),
        user_agent=login_row.user_agent,
        mp_account="物院学生会",
    )
    drop_login_row(login_row)
    return respond_success(state="done")


def refresh_qrcode(login_row: WechatLoginSession, client: MpClient):
    "status 2/3: qrcode expired, redo steps 2+3 within the same login session"
    try:
        login_row.sessionid = new_sessionid()
        start_resp = client.startlogin(login_row.sessionid)
    except (requests.RequestException, ValueError):
        logger.info("MpLoginRefreshUpstreamError")
        return respond_error(502, "MpLoginUpstreamError")
    ret = start_resp.get("base_resp", {}).get("ret")
    if ret != 0:
        logger.info("MpLoginRefreshRejected ret=%s", ret)
        return respond_error(502, "MpLoginStartRejected", f"ret={ret}")
    try:
        qrcode = client.get_qrcode()
    except requests.RequestException:
        logger.info("MpLoginQrcodeUpstreamError")
        return respond_error(502, "MpLoginUpstreamError")
    login_row.cookies = serialize_cookies(client.session)
    login_row.state = "pending"
    login_row.save()
    return respond_success(state="pending", qrcode=qrcode_data_uri(qrcode))


@bp.route("/session")
def session_status():
    session_row = db.session.get(WechatSession, 1)
    if session_row is None:
        return respond_success(logged_in=False)
    return respond_success(
        logged_in=session_row.valid and bool(session_row.token),
        mp_account=session_row.mp_account,
        created_at=session_row.created_at,
        last_check_at=session_row.last_check_at,
    )


@bp.route("/session/check", methods=["POST"])
def session_check():
    try:
        valid = check_session()
    except requests.RequestException:
        logger.info("MpSessionCheckUpstreamError")
        return respond_error(502, "MpSessionCheckFailed")
    return respond_success(valid=valid)
