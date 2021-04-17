import json
from os.path import dirname, join

__all__ = ["EMOJI_DATA", "parse_emoji"]

with open(join(dirname(__file__), "emoji.json"), encoding="utf-8") as f:
    EMOJI_DATA = json.load(f)


def parse_emoji(string):
    # return re.sub(p, lambda m: EMOJI_DATA.get(m.group(1), m.group()), s)
    for k, v in EMOJI_DATA.items():
        string = string.replace(k, v)
    return string
