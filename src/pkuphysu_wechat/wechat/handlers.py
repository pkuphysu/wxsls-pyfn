import traceback
from logging import getLogger
from textwrap import dedent

from werobot.messages.messages import TextMessage
from werobot.replies import SuccessReply, TransferCustomerServiceReply

from .core import wechat_mgr, wechat_robot
from .models import CommandStatus

logger = getLogger(__name__)


def text_handler(message: TextMessage):
    try:
        wechat_mgr.batch_update_status(
            wechat_mgr.command_reg.calc_status_diff(CommandStatus.get_all_status())
        )
        response = wechat_mgr.exec(message.content, message=message)
        return dedent(response) if isinstance(response, str) else response
    except:  # noqa
        logger.error(traceback.format_exc())
        return "抱歉回复机器人出现了一些问题[OMG]，暂时无法处理"


wechat_robot.text(text_handler)


@wechat_robot.subscribe
def respond_subscribe(message):
    return "欢迎关注物院学生会公众号[Hey]"


@wechat_robot.image
@wechat_robot.location
@wechat_robot.link
@wechat_robot.voice
@wechat_robot.unknown
def respond_image(message):
    return TransferCustomerServiceReply(message)


@wechat_robot.handler
def respond_others(message):
    return SuccessReply()
