from logging import getLogger

from werobot.messages.messages import TextMessage

from pkuphysu_wechat.wechat.core import wechat_mgr
from pkuphysu_wechat.wechat.utils import master

from .data import PUZZLE_DATA
from .models import SituationPuzzleConversation, SituationPuzzleState
from .service import chat, get_active_puzzle

logger = getLogger(__name__)
wechat_mgr.command_reg.mark_default_closed("situation_puzzle")

RULE = """海龟汤已经由 AI 汤主主持：
1. 输入“海龟汤 汤面”查看当前谜面。
2. 每轮输入“海龟汤 <你的问题>”自由提问，汤主会根据汤底回答。
3. 猜到完整真相后，直接把推理作为问题发送；AI 汤主会判断是否通关。
4. 输入“海龟汤 重置”开启新一局，旧记录仍保存在数据库中。
5. 输入“海龟汤 规则”再次查看本说明。
"""


@wechat_mgr.command(keywords=["alterpuzzle"], groups=["situation_puzzle"])
@master
def alter_puzzle(payload: str, message: TextMessage):
    """
    alterpuzzle | 更换谜题
    从本目录下的 data/puzzle.json 更换海龟汤内容 alterpuzzle <题号>
    """
    puzzle_id = payload.strip()
    if puzzle_id not in PUZZLE_DATA:
        return f"输入{payload}，格式错误，请认真阅读说明"
    SituationPuzzleState.set_active_puzzle_id(puzzle_id)
    return "更改成功"


@wechat_mgr.command(keywords=["海龟汤", "situation_puzzle"], groups=["situation_puzzle"])
def get(payload: str, message: TextMessage):
    """
    situation_puzzle <问题> | 与 AI 汤主进行海龟汤对话
    输入“海龟汤 汤面”查看谜面，输入“海龟汤 规则”查看完整规则。
    """
    payload = payload.strip()
    openid = message.source
    if not payload or payload == "规则":
        return RULE
    if payload == "汤面":
        _, puzzle = get_active_puzzle()
        return puzzle["cover"] + "\n\n请用“海龟汤 <你的问题>”继续推理。"
    if payload == "重置":
        puzzle_id, _ = get_active_puzzle()
        SituationPuzzleConversation.reset(openid, puzzle_id)
        return "当前对话已重置，旧记录仍保存在数据库中。"
    return chat(openid, payload)


@wechat_mgr.command(keywords=["answerpuzzle", "海龟汤回答"], groups=["situation_puzzle"])
def answer_puzzle(payload: str, message: TextMessage):
    """
    answerpuzzle <完整推理> | 将完整推理交给 AI 汤主判断
    """
    payload = payload.strip()
    if not payload:
        return "请在命令后写出您的完整推理。"
    return chat(message.source, payload)
