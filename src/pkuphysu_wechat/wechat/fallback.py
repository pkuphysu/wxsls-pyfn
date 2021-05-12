import json

from command4bot.manager import split_keyword
from werobot.replies import TransferCustomerServiceReply

from .core import wechat_command_reg, wechat_mgr
from .models import AutoReply
from .utils import get_similar_help_for_user


@wechat_mgr.fallback
def help_with_similar(content: str, message) -> str:
    reply_record = AutoReply.query.get(content)
    if reply_record is not None:
        return json.loads(reply_record.response)
    keyword, _ = split_keyword(content)
    # get command not found help message
    helps = get_similar_help_for_user(wechat_command_reg, keyword, message)
    # No similar commands found
    if not helps:
        for command in wechat_command_reg.get_all():
            for keyword in command.keywords:
                if content.startswith(keyword):
                    return f'看起来想使用命令"{keyword}"但忘了在"{keyword}"后打空格？'
        return TransferCustomerServiceReply(message)
    # print similar commands
    return f'看起来命令"{keyword}"打错了? 可能的命令有:\n' + helps
