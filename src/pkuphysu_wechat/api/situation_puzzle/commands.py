import re
from logging import getLogger

from werobot.messages.messages import TextMessage

from pkuphysu_wechat.wechat.core import wechat_mgr
from pkuphysu_wechat.wechat.utils import master

from .data import DEPENDENCE_DATA, PUZZLE_DATA
from .data.database import RULE, Puzzle, PuzzleDependence
from .models import PuzzleUnlock,PuzzleReview

logger = getLogger(__name__)
wechat_mgr.command_reg.mark_default_closed("situation_puzzle")


@wechat_mgr.command(keywords=["alterpuzzle"], groups=["situation_puzzle"])
@master
def alter_puzzle(payload: str, message: TextMessage):
    """
    alterpuzzle | 更换谜题
    从本目录下的data/puzzle.json和data/dependence.json更换海龟汤内容 alterpuzzle [0-9]
    """
    if not re.match(r"^\d$", payload):
        return f"输入{payload}，格式错误，请认真阅读说明"
    try:
        puzzle = PUZZLE_DATA[payload]
        Puzzle.clear()
        Puzzle.put_in(puzzle)
        dependence = DEPENDENCE_DATA[payload]
        PuzzleDependence.clear()
        PuzzleDependence.put_in(dependence)
    except:  # noqa
        return "更改失败，请重试"
    PuzzleUnlock.clear()
    return "更改成功"


@wechat_mgr.command(keywords=["海龟汤","situation_puzzle"], groups=["situation_puzzle"])
def get(payload: str, message: TextMessage):
    """
    situation_puzzle |询问汤面、问题、规则、查看某关键词的问题
    具体规则输入"海龟汤 规则"查看，别忘了空格哦
    """
    payloads = payload.split()
    openid = message.source
    try:
        if len(payloads) == 1:
            if payloads[0] == "汤面":
                cover = Puzzle.get_cover()
                keyword = Puzzle.get_keyword()
                for item in keyword:
                    if Puzzle.get_locked(item) is True:
                        keyword.remove(item)
                return cover + "\n" + "关键词：" + " ".join(keyword)

            elif payloads[0] == "问题":
                return Puzzle.get_questions() + "\n" + "回答格式（例）：\n海龟汤回答 1A2A"

            elif payloads[0] == "规则":
                return RULE

            elif Puzzle.get_locked(payloads[0]) is False:
                return "\n".join(Puzzle.get_keyquestions(payloads[0]))
            elif Puzzle.get_locked(payloads[0]) is True:
                dependence_id = PuzzleDependence.get_Kid(payloads[0])
                if PuzzleUnlock.check(openid, dependence_id) is True:
                    return "\n".join(Puzzle.get_keyquestions(payloads[0]))
            else:
                return f"您的输入是「{payload}」，输入有误"

        elif len(payloads) == 2:
            if Puzzle.get_locked(payloads[0]) is False:
                dependence_id = PuzzleDependence.get_Qid(
                    "%s %s" % (payloads[0], payloads[1])
                )
                if dependence_id is not None:
                    PuzzleUnlock.add(openid, dependence_id)
                return Puzzle.get_clue(payloads[0], payloads[1])

            elif Puzzle.get_locked(payloads[0]) is True:
                dependence_id = PuzzleDependence.get_Kid(payloads[0])
                if PuzzleUnlock.check(openid, dependence_id) is True:

                    dependence_id = PuzzleDependence.get_Qid(
                        "%s %s" % (payloads[0], payloads[1])
                    )
                    if dependence_id is not None:
                        PuzzleUnlock.add(openid, dependence_id)

                    return Puzzle.get_clue(payloads[0], payloads[1])

        return f"您的输入是「{payload}」，输入有误"
    except:  # noqa
        return f"您的输入是「{payload}」，输入有误"


@wechat_mgr.command(keywords=["answerpuzzle", "海龟汤回答"], groups=["situation_puzzle"])
def answer_puzzle(payload: str, message: TextMessage):
    """
    answerpuzzle <问题答案> |回答海龟汤的问题
    答案格式应为数字加大写字母，中间没有空格，也应该按顺序输入答案，例如：海龟汤回答 1A2B
    """
    answer = Puzzle.get_answers()
    explanation = Puzzle.get_explanation()
    if not re.match(r"^(\d[A-Z])+$", payload):
        return f"您输入了「{payload}」，格式错误，请认真阅读说明"
    # 加上一些常见错误，比如大小写的比对
    if payload == answer:
        openid = message.source
        PuzzleUnlock.clear_personal_information(openid)
        return explanation+"\n"
    return "回答有误呀！请重新尝试~"

@wechat_mgr.command(keywords=["reviewpuzzle", "海龟汤评论"], groups=["situation_puzzle"])
def review_puzzle(payload: str, message: TextMessage):
    """
    reviewpuzzle<海龟汤评论>|请您对海龟汤的内容或者形式给出建议
    例如：
    海龟汤评论 这个海龟汤真下饭，就是题目多了点
    """
    if len(payload) > 100:
        return "字数太多了[Respect]建议精简一些到100字以内哦"
    open_id = message.source
    PuzzleReview.add(open_id, payload)
    return f"已收到您的建议！感谢您的支持"