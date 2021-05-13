import time
from logging import getLogger

from flask import Blueprint, jsonify, request

from pkuphysu_wechat.auth import token_required
from pkuphysu_wechat.config import settings

from .data.database import Datax10nProbs
from .database import Datax10n

logger = getLogger(__name__)
bp = Blueprint("x10n", __name__)


@bp.route("/api/x10n", methods=["GET", "POST"])
def index():
    openid = token_required()
    if request.method == "GET":
        info = Datax10n.get_info(openid)
        if not info["played"]:
            prob_ids = Datax10nProbs.get_ran_probids(settings.x10n.PROBLEMS_NUMBER)
            starttime = str(time.time())
            probs = [Datax10nProbs.get_prob(x) for x in prob_ids]
            for number in range(len(probs)):
                probs[number]["number"] = prob_ids[number]
            info["questions"] = probs
            if not Datax10n.startgame(openid, starttime, prob_ids):
                return {"msg": "failed"}
        return jsonify(info)
    elif request.method == "POST":
        result = request.get_json(force=True).get("result")
        info = Datax10n.get_info(openid)
        if not info["played"]:
            return {"msg": "you haven't sign in yet"}
        elif info["played"] and info["result"]:
            return {"msg": "submit too many times"}
        end_time = time.time()
        start_time = Datax10n.get_starttime(openid)
        if end_time - start_time > settings.x10n.TIMEOUT:
            return None
        time_used = f"{end_time-start_time:.2f}"
        Datax10n.put_name(openid, result["name"], result["stuID"])
        prob_ids = Datax10n.get_probs(openid)
        questions = result["questions"]
        if len(questions) != settings.x10n.PROBLEMS_NUMBER:
            return {"msg": "you have submit a list with wrong probids"}
        for question in questions:
            if question["number"] not in prob_ids:
                return {"msg": "you have submit a list with wrong probids"}
            question["answer"] = str(question["answer"]) == Datax10nProbs.get_ans(
                question["number"]
            )
        user_result = {
            "time": time_used,
            "name": result["name"],
            "questions": questions,
        }
        Datax10n.put_info(openid, user_result)
        returns = {
            "msg": "success",
            "result": user_result,
        }
        return jsonify(returns)
    return {"msg": "da lao rao ming"}
