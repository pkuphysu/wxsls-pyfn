import re
import string
from functools import wraps
from logging import getLogger

from werobot.messages.messages import TextMessage

from pkuphysu_wechat.wechat.core import wechat_mgr

from .models import PRIZE_COUNT, PRIZE_NAMES, CJParticipant

logger = getLogger(__name__)
wechat_mgr.command_reg.mark_default_closed("eveparty")


def name_required(f):
    @wraps(f)
    def deco(**kwargs):
        if not CJParticipant.get_user_name(kwargs["message"].source):
            return "请先绑定姓名"
        return f(**kwargs)

    return deco


@wechat_mgr.command(groups=["eveparty"])
def name(payload: str, message: TextMessage) -> str:
    """
    name <姓名> <学号> | 设置姓名和学号
    需与校园卡上一致，否则无法领奖
    注意：只有现场的同学才能抽奖！
        如："name 小明"
    """
    if CJParticipant.get_user_name(message.source):
        return "您已设置过姓名！"
    match = re.findall(r"^(\w+) (\d{10})", payload)
    if not match:
        return "格式不太对？请使用 help name 查看帮助"
    name, stu_id = match[0]
    CJParticipant.add_user(message.source, name, stu_id)
    return "注册成功！可以用 invest 投点啦~\n" + "ps: 可以通过输入 help invest 查看命令帮助"


def create_invest():
    prize_count = PRIZE_COUNT
    prize_names = PRIZE_NAMES
    prize_letters = list(string.ascii_uppercase[:prize_count])

    help_str = f'''\
invest <{"> <".join(prize_letters[:prize_count])}> | 来进行投点

其中{"、".join(prize_letters[:prize_count])}为非负整数，
分别为{"、".join(prize_names[:prize_count])}
投入的点数，且总和在0-99之间。
    如："invest{" 10"*prize_count}"'''

    @name_required
    def invest(payload: str, message: TextMessage) -> str:
        invalid = "invest指令格式错误\n    正确格式为\n   " + help_str

        value_invalid = "点数总和应在0-99之间！"
        success = "投点成功，在投点时间结束前再次输入invest指令可更改投点。"

        investments = payload.split()
        if len(investments) != prize_count:
            return invalid

        if not all(n.isdecimal() for n in investments):
            return invalid

        investment = list(map(int, investments))

        if not all(n >= 0 for n in investment):
            return invalid

        if (sum(investment) < 0) or (sum(investment) > 99):
            return value_invalid

        CJParticipant.user_invest(message.source, investment)
        return success

    invest.__doc__ = help_str
    wechat_mgr.command(groups=["eveparty"])(invest)


create_invest()
