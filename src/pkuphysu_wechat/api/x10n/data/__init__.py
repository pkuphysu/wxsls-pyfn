# import csv
import json
import os

from flask import request

from .. import bp
from .database import Datax10nProbs

# from pkuphysu_wechat.auth import token_required


# from logging import getLogger


@bp.route("/api/x10n/data", methods=["GET", "POST"])
def json_initialize() -> int:
    # openid = token_required()
    # check admin
    if request.method == "POST":
        basedir = os.path.abspath(os.path.dirname(__file__))
        path = os.path.join(basedir, "probs.json")
        with open(path, encoding="utf-8") as f:
            probs = json.load(f)
            for prob_id in range(len(probs)):
                prob = probs[prob_id]
                prob["probid"] = str(prob_id)
                Datax10nProbs.put_prob(prob)
        return len(probs)


# def csv_initialize() -> int:
#     basedir = os.path.abspath(os.path.dirname(__file__))
#     path = os.path.join(basedir, 'probs.csv')
#     with open(path, encoding='utf-8') as f:
#         reader = list(csv.DictReader(f))
#         n = 0
#         for prob in reader:
#             prob['probid'] = str(n)
#             Datax10nProbs.put_prob(prob)
#             n += 1
#     return n
