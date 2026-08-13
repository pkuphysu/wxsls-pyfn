from logging import getLogger

from pkuphysu_wechat.config import settings

from .ai import SituationPuzzleAI, SituationPuzzleAIError
from .data import PUZZLE_DATA
from .models import (
    SituationPuzzleState,
    SituationPuzzleTurn,
    SituationPuzzleTurnPending,
)
from .prompts import build_system_prompt

logger = getLogger(__name__)

AI_UNAVAILABLE_REPLY = "AI 汤主本次未能回应，问题已保存，请重试。"
STALE_TURN_REPLY = "本轮对话已被重置，请重新提问。"
TURN_PENDING_REPLY = "上一轮仍在处理中，请稍后再试。"
VERDICT_REPLIES = {
    "yes": "是",
    "no": "否",
    "irrelevant": "无关",
    "unknown": "无法确定",
}


def get_active_puzzle():
    puzzle_id = SituationPuzzleState.get_active_puzzle_id()
    puzzle = PUZZLE_DATA.get(puzzle_id)
    if puzzle is None:
        raise ValueError("Active situation puzzle does not exist")
    return puzzle_id, puzzle


def chat(open_id, user_content):
    puzzle_id, puzzle = get_active_puzzle()
    try:
        turn = SituationPuzzleTurn.begin(open_id, puzzle_id, user_content)
    except SituationPuzzleTurnPending:
        return TURN_PENDING_REPLY

    history = SituationPuzzleTurn.messages_for(
        turn,
        settings.situation_puzzle_ai.MAX_HISTORY_TURNS,
    )
    messages = [
        {
            "role": "system",
            "content": build_system_prompt(puzzle["cover"], puzzle["explanation"]),
        }
    ] + history

    try:
        verdict = SituationPuzzleAI.complete(messages)
    except SituationPuzzleAIError:
        logger.exception("Situation-puzzle AI is unavailable")
        SituationPuzzleTurn.fail(turn.id)
        return AI_UNAVAILABLE_REPLY

    if verdict == "solved":
        assistant_content = "恭喜通关！\n" + puzzle["explanation"]
    else:
        assistant_content = VERDICT_REPLIES[verdict]
    if not SituationPuzzleTurn.complete(turn.id, assistant_content):
        return STALE_TURN_REPLY
    return assistant_content
