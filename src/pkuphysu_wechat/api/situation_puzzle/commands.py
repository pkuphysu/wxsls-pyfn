import re
from logging import getLogger

from werobot.messages.messages import TextMessage

from pkuphysu_wechat.wechat.core import wechat_mgr
from pkuphysu_wechat.wechat.utils import master

from .data import DEPENDENCE_DATA, PUZZLE_DATA
from .data.database import Puzzle, PuzzleDependence
from .models import PuzzleUnlock

logger = getLogger(__name__)
wechat_mgr.command_reg.mark_default_closed("situation_puzzle")


@wechat_mgr.command(keywords=["alterpuzzle"], groups=["situation_puzzle"])
@master
def alter_puzzle(payload: str, message: TextMessage):
    """
    alterpuzzle | 从本目录下的data/puzzle.json和
    data/dependence.json更换海龟汤内容 alterpuzzle [0-9]
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


# “海龟汤”/
# Puzzle.get_cover()

# 询问关键词
# 返回全部关键词 （可以单独写一个）判断锁与否？？？

# situationpuzzle [keyword] 询问某关键词
# - 查看是否默认上锁 ->查看此人是否解锁

# situationpuzzle [keyword] [A-Z] 询问某关键词
# - 查看是否默认上锁 ->查看此人是否解锁
# - 返回clue
# - PuzzleDependence->拿id和openid PuzzleUnlock.add(?)

# “回答问题”/
# Puzzle.get_questions()

# 注：所有返回None------>处理


@wechat_mgr.command(keywords=["answerpuzzle", "海龟汤回答"], groups=["situation_puzzle"])
def answer_puzzle(payload: str, message: TextMessage):
    answer = Puzzle.get_answers()
    explanation = Puzzle.get_explanation()
    if not re.match(r"^(\d[A-Z])+$", payload):
        return f"您输入了:{payload}，格式错误，请认真阅读说明"
    # 加上一些常见错误，比如大小写的比对
    if payload == answer:
        openid = message.source
        PuzzleUnlock.clear_personal_information(openid)
        return explanation
    return "回答有误呀！请重新尝试~"
