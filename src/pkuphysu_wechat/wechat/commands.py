import json
from logging import getLogger

from command4bot.manager import split_keyword
from werobot.messages.messages import TextMessage

from .core import wechat_client, wechat_command_reg, wechat_mgr
from .models import AutoReply
from .utils import check_master, get_similar_help_for_user, is_master_command, master

logger = getLogger(__name__)
wechat_mgr.command_reg.mark_default_closed("debug")


@wechat_mgr.command
@master
def close(payload, message: TextMessage):
    "close <command> | 关闭命令（组）"
    logger.info("Closing %s", payload)
    wechat_mgr.close(payload)
    return "成功关闭 " + payload


@wechat_mgr.command
@master
def open(payload, message: TextMessage):
    "open <command> | 打开命令（组）"
    logger.info("Opening %s", payload)
    wechat_mgr.open(payload)
    return "成功打开 " + payload


@wechat_mgr.command(keywords=("cst", "status"))
@master
def status(message):
    "status/cst | 显示命令开关状态"
    return "\n".join(
        (
            "Default",
            *(f"{k}: {v}" for k, v in wechat_command_reg._default_status.items()),
            "-" * 15,
            "Manual",
            *(f"{k}: {v}" for k, v in wechat_command_reg._status.items()),
        )
    )


@wechat_mgr.command(keywords=("help", "ls", "?"))
def help(payload, message: TextMessage):
    """
    help [命令名称] | 获取命令帮助
    指令均不包含短横、引号、方尖括号等字符，它们仅是辅助用途。
    竖线前为命令格式，其后为简单解释，详细解释请使用 help <命令名称> 查看。
    命令名称为 help 返回的短横后以空格为分割的第一个单词（词语）。如有斜杠，表示该命令支持多个关键词，选其一即可。
    方、尖括号表示一个参数，<尖括号> 表示必填参数，[方括号] 表示可选参数。

    """
    if payload:
        command = wechat_mgr.command_reg.get(payload)
        if command and wechat_command_reg.resolve_command_status(command):
            if check_master(message) or not is_master_command(command):
                return command.help
        helps = get_similar_help_for_user(wechat_command_reg, payload, message)
        if helps:
            return f'看起来命令"{payload}"不存在或已关闭? 可能的命令有:\n' + helps
        return f'看起来命令"{payload}"不存在或已关闭？连长得像的命令都没有'
    return "【命令帮助】\n建议使用 help help 查看格式解释\n\n" + "\n".join(
        command.brief_help
        for command in wechat_command_reg.get_all(check_master(message))
        if wechat_command_reg.resolve_command_status(command)
    )


@wechat_mgr.command(groups=["debug"])
def openid(message: TextMessage) -> str:
    "openid | 返回您的 openid，debug 用"
    return message.source


@wechat_mgr.command
@master
def reply_add(payload: str, message: TextMessage):
    """
    reply_add <无空格的词> <JSON> | 设置或更新自动回复

    设置文字回复时，需要用双引号引起，即 JSON 语法
    设置文章回复时，应为 [["title", "description", "image", "url"]]
    如果为未引起的文字，将在最近 20 篇素材中查找匹配的素材自动生成
    """
    keyword, response = split_keyword(payload)
    if not (response.startswith('"') or response.startswith("[")):
        possible_articles = [
            item["content"]["news_item"][0]
            for item in wechat_client.get_media_list("news", 0, 20)["item"]
            if (
                len(item["content"]["news_item"]) == 1
                and response in item["content"]["news_item"][0]["title"]
            )
        ]
        if len(possible_articles) != 1:
            return (
                f'有{len(possible_articles)}篇文章包含"{response}": '
                f'{";".join(a["title"] for a in possible_articles)}'
            )
        article = possible_articles[0]
        response_obj = [
            [
                article["title"],
                article["digest"],
                (
                    "https://mmbiz.qpic.cn/sz_mmbiz_jpg/19av21fYDOU49vxPXLMk2lXPENJqk"
                    "894nT9RUA8dic9q3JPncUyfsctjrsvIaZlLKJL5zlE04KzH7bIp6FmSeDw/640"
                ),
                article["url"],
            ]
        ]
        response = json.dumps(response_obj, ensure_ascii=False)
    else:
        try:
            response_obj = json.loads(response)
        except json.JSONDecodeError as e:
            return str(e)
        if isinstance(response_obj, list):
            if len(response_obj[0]) != 4:
                return "文章回复格式不对"
    AutoReply.update(keyword, response)
    logger.info(response_obj)
    return response_obj


@wechat_mgr.command
@master
def reply_remove(payload: str, message: TextMessage):
    "reply_remove <无空格的词> | 删除自动回复"
    return f"Remove {AutoReply.remove(payload)} rule."


@wechat_mgr.command
@master
def reply_list(message: TextMessage):
    "reply_list | 列出所有自动回复"
    return (
        "\n".join(f"{r.keyword}::{r.response}" for r in AutoReply.query.all())
        or "Nothing."
    )
