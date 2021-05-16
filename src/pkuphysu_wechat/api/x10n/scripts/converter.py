import csv
import json

result = []


with open("./初赛题目（终）.csv", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f, f.readline()[:-1].split(","))
    for i, record in enumerate(reader):
        result.append(
            dict(
                img="",
                text=record["题目"],
                answer=str("ABCD".index(record["答案"])),
                choices=json.dumps([record[c] for c in "ABCD"]),
                probid=str(i),
            )
        )

with open("x10n.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
