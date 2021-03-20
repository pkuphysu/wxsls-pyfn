import traceback
from logging import getLogger
from textwrap import dedent

from werobot.messages.messages import TextMessage
from werobot.replies import SuccessReply, TransferCustomerServiceReply

from .core import wechat_client, wechat_mgr, wechat_robot
from .database import CommandStatus

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
        return "抱歉出现了一些问题[OMG]，暂时无法处理[Doge]"


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
    wechat_client.send_text_message(message.source, "暂时没有开发识别功能[Shrunken]，请等待回复哟~")
    return TransferCustomerServiceReply(message)


@wechat_robot.handler
def respond_others(message):
    return SuccessReply()
