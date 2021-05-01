import logging
from typing import List

import command4bot
import werobot
from command4bot.command import calc_status_diff
from werobot.client import Client

from pkuphysu_wechat.config import settings

from .models import AccessToken, CommandStatus


class CommandRegistry(command4bot.CommandRegistry):
    _all: List[command4bot.Command]

    def __init__(self):
        super().__init__()
        self._default_status = {}
        self._all_but_master = []
        self._all = []

    def register(self, command: command4bot.Command) -> None:
        self._all.append(command)
        if not getattr(command.command_func, "master", False):
            self._all_but_master.append(command)
        return super().register(command)

    def get_status(self, name: str) -> bool:
        return self._status.get(name, self._default_status.get(name, True))

    def set_status(self, name: str, status: bool) -> None:
        self._status[name] = status
        CommandStatus.set_status(name, status)

    def set_default_closed(self, name: str) -> None:
        self._default_status[name] = False

    def get_all(self, master=False) -> List[command4bot.Command]:
        return self._all if master else self._all_but_master

    def calc_status_diff(self, new_status):
        before = {**self._default_status, **self._status}
        return calc_status_diff(before, new_status)


class WechatClient(Client):
    def get_access_token(self):
        return AccessToken.get(self.grant_token)

    def oauth(self, code: str):
        """
        获取 OAuth Access Token。
        :return: 返回的 JSON 数据包
        """
        return self.get(
            url="https://api.weixin.qq.com/sns/oauth2/access_token",
            params={
                "grant_type": "authorization_code",
                "appid": self.appid,
                "secret": self.appsecret,
                "code": code,
            },
        )

    def oauth_userinfo(self, access_token: str, openid: str):
        """
        获取用户信息。
        :return: 返回的 JSON 数据包
        """
        return self.get(
            url="https://api.weixin.qq.com/sns/userinfo",
            params={
                "access_token": access_token,
                "openid": openid,
                "lang": "zh_CN",
            },
        )


wechat_robot = werobot.WeRoBot(
    token=settings.wechat.TOKEN, logger=logging.getLogger(__name__)
)
wechat_robot.config["APP_ID"] = settings.wechat.APP_ID
wechat_robot.config["APP_SECRET"] = settings.wechat.APP_SECRET
wechat_robot.config["SESSION_STORAGE"] = False
wechat_command_reg = CommandRegistry()
wechat_mgr = command4bot.CommandsManager(
    command_reg=wechat_command_reg,
    command_context_ignore=["message"],
    enable_default_fallback=False,
    text_command_closed="不好意思，该命令不在活动时间段，暂不开放",
    command_case_sensitive=False,
)
wechat_client = WechatClient(wechat_robot.config)
