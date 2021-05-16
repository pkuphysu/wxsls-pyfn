import json
from csv import DictWriter

with open("./x10nUser-1621085063582.json", encoding="utf-8") as f:
    data = json.load(f)

with open("./x10n-result.csv", "w", encoding="utf-8-sig", newline="") as f:
    writer = DictWriter(
        f, ["name", "stu_id", "score", "time", "prob_ids", "openid", "starttime"]
    )
    writer.writeheader()
    for datum in data:
        if datum["result"] is None:
            continue
        result = json.loads(datum.pop("result"))
        datum["score"] = [question["answer"] for question in result["questions"]].count(
            True
        )
        datum["time"] = result["time"]
        writer.writerow(datum)
