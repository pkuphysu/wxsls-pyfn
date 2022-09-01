import json
from os.path import dirname, join

__all__ = ["PUZZLE_DATA", "DEPENDENCE_DATA", "database", "RULE"]

with open(join(dirname(__file__), "puzzle.json"), encoding="utf-8") as f:
    PUZZLE_DATA = json.load(f)

with open(join(dirname(__file__), "dependence.json"), encoding="utf-8") as f:
    DEPENDENCE_DATA = json.load(f)

RULE = """玩家输入关键词：
1. 海龟汤 汤面（或situation_puzzle 汤面）
返回谜面和关键词
2. 海龟汤 皮特 （或situation_puzzle 皮特）
返回所有可问的问题
3. 海龟汤 皮特 A （或situation_puzzle 皮特 A）
返回此问题答案以及一些提示
4. 海龟汤 问题（或situation_puzzle 问题）
返回要回答的问题
5. 海龟汤回答 1A2A（或 answerpuzzle 1A2A）
返回回答正误与谜底
6. 海龟汤 规则（或situation_puzzle 规则）
返回输入规则
7. 海龟汤评论 内容
为我们的海龟汤进行点评"""
