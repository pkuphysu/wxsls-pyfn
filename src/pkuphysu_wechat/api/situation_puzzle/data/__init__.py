import json
from os.path import dirname, join

__all__ = ["PUZZLE_DATA", "DEPENDENCE_DATA", "database"]

with open(join(dirname(__file__), "puzzle.json"), encoding="utf-8") as f:
    PUZZLE_DATA = json.load(f)

with open(join(dirname(__file__), "dependence.json"), encoding="utf-8") as f:
    DEPENDENCE_DATA = json.load(f)
