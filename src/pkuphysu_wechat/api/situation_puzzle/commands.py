from msilib.schema import Error
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


@wechat_mgr.command(keywords=["海龟汤"],groups=["situation_puzzle"])
def get(payload:str,message:Textmessage):
    li=payload.split()
    openid= message.source
    try:
        if len(li)==1 :
            if li[0]=="汤面":
                cover=Puzzle.get_cover()
                return cover
                
            elif li[0]=="关键词":
                keyword=Puzzle.get_keyword()
                for item in keyword:
                    if Puzzle.get_locked(i)==True:
                        keyword.remove(i)
                return " ".join(keyword)

            elif li[0]=="问题":
                return Puzzle.get_questions()
            
            elif Puzzle.get_locked(li[0])==False:
                return "\n".join(Puzzle.get_keyquestions())
            elif Puzzle.get_locked(li[0])==True:
                id=PuzzleDependence.get_Kid(li[0])
                if PuzzleUnlock.check(openid,id)==True:
                    return "\n".join(Puzzle.get_keyquestions())
            else:
                return f"您的输入是{payload}，输入有误"
                

        elif len(li)==2 :
            if Puzzle.get_locked(li[0])==False :
                all= PuzzleDependence.query.all()
                for item in all:
                    if item.question=="%s %s"%(li[0],li[1]):
                        PuzzleUnlock.add(openid,item.id)
                return Puzzle.get_clue(li[0],li[1])
            elif Puzzle.get_locked(li[0])==True:
                id=PuzzleDependence.get_Kid(li[0])
                if PuzzleUnlock.check(openid,id)==True:
                    all= PuzzleDependence.query.all()
                for item in all:
                    if item.question=="%s %s"%(li[0],li[1]):
                        PuzzleUnlock.add(openid,item.id)
                return Puzzle.get_clue(li[0],li[1])

        return f"您的输入是{payload}，输入有误"
    except:
        res= f"您的输入是{payload}，输入有误"



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
