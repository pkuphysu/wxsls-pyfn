import json
from os.path import dirname, join

__all__ = ["PUZZLE_DATA"]

with open(join(dirname(__file__), "puzzle.json"), encoding="utf-8") as f:
    PUZZLE_DATA = json.load(f)
