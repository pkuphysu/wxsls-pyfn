from functools import wraps

from command4bot import Command
from werobot.messages.messages import TextMessage

from pkuphysu_wechat.config import settings


def check_master(message: TextMessage) -> bool:
    return message.source in settings.wechat.MASTER_IDS


def is_master_command(command: Command):
    return getattr(command.command_func, "master", False)


def master(func):
    @wraps(func)
    def deco(**kwargs):
        message = kwargs.get("message")
        if message is None:
            raise ValueError("Missing required `message` to check master")
        if check_master(message):
            return func(**kwargs)
        return "权限不足以运行该命令..."

    deco.master = True
    return deco


def get_similar_help_for_user(wechat_command_reg, keyword: str, message: TextMessage):
    return "\n".join(
        command.brief_help
        for command in wechat_command_reg.get_similar_commands(keyword)
        if check_master(message) or not is_master_command(command)
    )
