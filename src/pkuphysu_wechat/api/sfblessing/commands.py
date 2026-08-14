import datetime
import random
import re
from logging import getLogger
from typing import Counter

from werobot.messages.messages import TextMessage

from pkuphysu_wechat.wechat.core import wechat_client, wechat_mgr, wechat_robot
from pkuphysu_wechat.wechat.utils import master

from . import simple_cipher
from .models import BlessBan, SFBackBlessing, SFBlessing, format_message

logger = getLogger(__name__)
wechat_mgr.command_reg.mark_default_closed("sfblessing", "getcover")


BANNED_HINT = """对不起，您的账号已被禁止发送祝福
（一般情况下是多次发送无关或负面信息）。
如有疑问，可尝试后台发送信息或找相关人员反馈。"""

COVER_URL = r"""奖品来啦！可以<a href = "https://support.weixin.qq.com/cgi-bin/"""
COVER_URL += r"""mmsupport-bin/showredpacket?receiveuri=pSJlkzH2LWT&check_type=2"""
COVER_URL += r"""#wechat_redirect">点我领取红包封面</a>啦(一定要用手机点开哟~)~"""


@wechat_mgr.command(keywords=("bless", "祝福", "祝"), groups=["sfblessing", "getcover"])
def bless(payload: str, message: TextMessage) -> str:
    """
    祝 <content> | 发送祝福
    如：
        bless 万事如意！
        祝福 学业有成！
        祝 绩点高高！
    （千万不要学例子一样用老套的祝福语 [Doge]
    """
    if len(payload) > 250:
        return "字数太多了[Respect]建议精简一些"
    open_id = message.source
    if BlessBan.is_name_baned(open_id):
        return BANNED_HINT
    blessing_id = SFBlessing.get_first_bless_id_by(open_id)
    bless_record = SFBlessing.add_bless(open_id, payload)
    msg = f"已收到您的祝福！编号为 {bless_record.blessing_id}"
    if blessing_id is None:
        msg += "\n" + COVER_URL
    return msg


@wechat_mgr.command(keywords=["reply", "re", "Re", "回复"], groups=["sfblessing"])
def reply(payload: str, message: TextMessage) -> str:
    """
    Re <name>: <content> | 对收到的祝福进行回复。
    如：
        Re ambitious and angry Alice: 感谢！[Rose]
        reply ambitious and angry Alice: 感谢！[Rose]
        回复 ambitious and angry Alice: 感谢！[Rose]
    """
    if len(payload) > 250:
        return "字数太多了[Respect]建议精简一些"
    if BlessBan.is_name_baned(message.source):
        return BANNED_HINT
    pattern = r"(?P<name>.+?): (?P<content>.+)"
    mat = re.match(pattern, payload)
    if mat is None:
        return (
            "格式有误，请检查格式。输入 help reply 以获取帮助。"
            "简单提示: Re ambitious and angry Alice: 感谢！[Rose]"
        )
    name = mat.group("name")
    content = mat.group("content")
    if not simple_cipher.is_valid_name(name):
        return f'"{name}" 不像是正确的名字。注意大小写和空格敏感。'
    blessing_id = simple_cipher.decode_name(name)
    open_id = SFBlessing.get_creator(blessing_id)
    if open_id is None:
        return "目标用户现在不存在！"
    SFBackBlessing.add_backbless(message.source, open_id, content)
    return f"对 {name} 的回复已收到！"


@wechat_mgr.command(keywords=["撤回祝福"], groups=["sfblessing"])
def undo_blessing(message):
    "撤回祝福 | 撤回自己最近一次发出的祝福，谨慎使用。"
    content = SFBlessing.undo_bless(message.source)
    if content is None:
        return "没有祝福可供撤回"
    return f"已撤回祝福：{content}"


@wechat_mgr.command(groups=["sfblessing"])
def whoami(message):
    """whoami | 获取您在活动中的“代号”。至少发送过一条祝福参与活动后才会分配。"""
    blessing_id = SFBlessing.get_first_bless_id_by(message.source)
    if blessing_id is None:
        return "您尚未发送祝福，或祝福被删除，没有分配昵称"
    return simple_cipher.encode_name(blessing_id)


@wechat_mgr.command(keywords=["blessban"], groups=["sfblessing"])
@master
def bless_ban(payload: str, message: TextMessage):
    """blessban | ban掉某openid，blessban openid1 openid2"""
    ban_ids = payload.split()
    ret = []
    for ban_id in ban_ids:
        try:
            BlessBan.add_name(ban_id)
            SFBlessing.remove_bless(person=ban_id)
        except:  # noqa
            logger.error("bless_ban %s failed", ban_id)
            ret.append(ban_id)
    return "以下openid禁止失败：\n" + "\n".join(ret) if ret else "ban successfully"


@wechat_mgr.command(keywords=["blessunban"], groups=["sfblessing"])
@master
def bless_unban(payload: str, message: TextMessage):
    """blessunban | unban某openid，unblessban openid1 openid2"""
    unban_ids = payload.split()
    ret = []
    for unban_id in unban_ids:
        try:
            BlessBan.remove_name(unban_id)
        except:  # noqa
            logger.error("bless_unban %s failed", unban_id)
            ret.append(unban_id)
    return "以下openid解封失败：\n" + "\n".join(ret) if ret else "unban successfully"


@wechat_mgr.command(keywords=["blessdelete"], groups=["sfblessing"])
@master
def bless_delete(payload: str, message: TextMessage):
    """blessdelete | 删去某条祝福，blessdelete num1 num2"""
    delete_ids = payload.split()
    ret = []
    for delete_id in delete_ids:
        try:
            SFBlessing.remove_bless(blessing_id=delete_id)
        except:  # noqa
            logger.error(f"bless_delete {delete_id} failed")
            ret.append(str(delete_id))
    return "以下祝福删除失败：\n" + "  ".join(ret) if ret else "删除成功"


@wechat_mgr.command(groups=["sfblessing"])
@master
def send(payload: str, message: TextMessage):
    """send | 发送祝福@从click转过来的 send 1 1代表昨日"""
    try:
        delta = int(payload)
    except:  # noqa
        return f"输入{payload}，形式错误"
    blessings = SFBlessing.get_by_date(
        datetime.date.today() - datetime.timedelta(days=delta)
    )
    counter = Counter(blessing.create_by for blessing in blessings)
    ret = True
    for open_id, count in counter.items():
        blessings_except_mine = [
            blessing for blessing in blessings if blessing.create_by != open_id
        ]
        num = random.randint(
            min(3 * count, len(blessings_except_mine)),
            min(5 * count, len(blessings_except_mine)),
        )
        msgs = random.sample(blessings_except_mine, num)
        send_msg = "快来看看收到的祝福吧！\n" + "\n".join(
            format_message(msg.create_by, msg.content) for msg in msgs
        )
        try:
            wechat_client.send_text_message(
                open_id,
                send_msg,
            )
        except:  # noqa
            logger.error("Blessing to %s not sent", open_id)
            ret = False
    return "发送成功！" if ret else "发送失败"


@wechat_robot.key_click("blessing_reply")
def get_blessing_reply(message):
    backblessings = SFBackBlessing.get_backbless_to(message.source)
    if not backblessings:
        return "暂无回复[Sigh]"
    return "以下为活动期间您收到的所有回复：\n" + "\n".join(
        format_message(msg.create_by, msg.content) for msg in backblessings
    )
