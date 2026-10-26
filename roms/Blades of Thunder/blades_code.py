#!/usr/bin/env python3
"""Blades of Thunder (GBA, BBHE) level-code table and field model.

Recovered from ROM 10185cf2a77c8be78ba7657d648c25b0d7c19ec7514b177a62637fb5e451a80c.
Validator: ARM routine at 0x080174F0 (file 0x174F0).  It converts the four
ASCII digits at 0x03005E50 to a decimal value and compares it against exactly
30 constants.  On a match it writes:
    0x03005E48 = difficulty (0 easy, 1 medium, 2 hard)
    0x03005E4C = level      (1..10; 10 is shown in game as "Level F")
and returns 1.  Every other value returns -1.
"""
TABLE = {
    # code: (difficulty, level)
    "4265": (0, 1), "6932": (1, 1), "1979": (2, 1),
    "7332": (0, 2), "3682": (1, 2), "2034": (2, 2),
    "6578": (0, 3), "5892": (1, 3), "7809": (2, 3),
    "7213": (0, 4), "4468": (1, 4), "6776": (2, 4),
    "8234": (0, 5), "1127": (1, 5), "9054": (2, 5),
    "9322": (0, 6), "9902": (1, 6), "4311": (2, 6),
    "1279": (0, 7), "2332": (1, 7), "8282": (2, 7),
    "5682": (0, 8), "8658": (1, 8), "2468": (2, 8),
    "3211": (0, 9), "7745": (1, 9), "1410": (2, 9),
    "9598": (0, 10), "1884": (1, 10), "9864": (2, 10),
}
DIFF = ["easy", "medium", "hard"]

def decode(code):
    code = "%04d" % int(code)
    return TABLE.get(code)

def encode(difficulty, level):
    for c, (d, l) in TABLE.items():
        if d == difficulty and l == level:
            return c
    raise KeyError((difficulty, level))

if __name__ == "__main__":
    print("code  difficulty  level")
    for c in sorted(TABLE):
        d, l = TABLE[c]
        print("%s  %-8s    %s" % (c, DIFF[d], l))
    print("\nspace: 10000 (0000-9999); accepted: %d" % len(TABLE))
    print("e.g. 9864 ->", decode("9864"))   # hard, 10
    print("e.g. hard/10 ->", encode(2, 10)) # 9864
