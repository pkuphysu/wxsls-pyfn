"""
This module is intended to encode user by a number.
Ideally, the number should be the first blessing id sent by the user.
"""

from functools import reduce

# TIP: fold PARTS in your editor
PARTS = [
    [
        "Alice",
        "Bob",
        "Carol",
        "Dave",
        "Eve",
        "Francis",
        "Grace",
        "Hans",
        "Isabella",
        "Jason",
        "Kate",
        "Louis",
        "Margaret",
        "Nathan",
        "Olivia",
        "Paul",
        "Queen",
        "Richard",
        "Susan",
        "Thomas",
        "Uma",
        "Vivian",
        "Winnie",
        "Xander",
        "Yasmine",
        "Zach",
    ],
    [
        "angry",
        "brilliant",
        "crazy",
        "diligent",
        "excited",
        "fat",
        "greedy",
        "hungry",
        "interesting",
        "jolly",
        "kind",
        "little",
        "magic",
        "naïve",
        "old",
        "powerful",
        "quiet",
        "rich",
        "super",
        "thu",
        "undefined",
        "valuable",
        "wifeless",
        "young",
        "zombie",
    ],
    [
        "ambitious",
        "blue",
        "curious",
        "drunk",
        "earnest",
        "friendly",
        "gentle",
        "hearty",
        "idle",
        "jovial",
        "keen",
        "lovely",
        "mild",
        "naughty",
        "obliging",
        "passionate",
        "quick",
        "responsible",
        "sturdy",
        "talented",
        "unaffected",
        "versatile",
        "warm",
        "yearning",
        "zealous",
    ],
]


N = reduce(lambda x, y: x * y, [len(p) for p in PARTS])
# Good prime! 3001 mod 26, 25*26, 24*25*26 gives different result!
# NOTE: hard coded! different to different lenths of PARTS!
P = 3001


def encode_name(number: int) -> str:
    name_parts = []
    index = (number * P) % N
    for part in PARTS:
        index, index_in_part = divmod(index, len(part))
        name_parts.append(part[index_in_part])
    name_parts.insert(2, "and")  # NOTE: hard coded 2!
    return " ".join(reversed(name_parts))


def decode_name(name: str) -> int:
    name_parts = list(reversed(name.split(" ")))
    del name_parts[2]  # NOTE: hard coded 2!
    index = 0
    weight = 1
    for part_index, part in enumerate(PARTS):
        index += weight * part.index(name_parts[part_index])
        weight *= len(part)
    number = index
    while number % P:
        number += N
    return number // P


def is_valid_name(name: str) -> bool:
    name_parts = list(reversed(name.split(" ")))
    del name_parts[2]  # NOTE: hard coded 2!
    if len(name_parts) != len(PARTS):
        return False
    for part_index, part in enumerate(PARTS):
        if name_parts[part_index] not in part:
            return False
    return True
