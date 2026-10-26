#!/usr/bin/env python3
"""Ballistic: Ecks vs. Sever (GBA, header BALLISTIC EC / AEEE) - password model.

The ROM's PASSWORD screen compares the typed string against exactly two
fixed tables (see the report, sections 4-6):

  * cheat table  : 0x080F648D, 9 entries x 12 bytes, 10-byte compare
                   -> sets bit N of the u32 at 0x02005270
  * level table  : 0x080F632D, 20 entries x 16 bytes, 10-byte compare
                   -> level id at 0x02000084; character/mode at 0x02000052

Input is A-Z only (26 symbols), stored lower-case, maximum 9 characters
(the append path refuses length > 8 at 0x080271E0).  This script is the
reimplementation of the accept/reject decision and the table->effect map.

Usage:
  python3 ballistic_pw.py                 # dump the full accepted set
  python3 ballistic_pw.py CODE [CODE...]  # classify input(s)
"""
import sys

CHEATS = [  # index == bit in the flag word at 0x02005270
    ("deathwish", "invincibility"),
    ("bigpocket", "unlimited ammo"),
    ("tooledup",  "all weapons"),
    ("coldfeet",  "enemies frozen"),
    ("oohstopit", "one-hit kills"),
    ("mybigun",   "rapid fire (Neosterd)"),
    ("acmebangs", "bigger explosions"),
    ("hornblow",  "alternate sound effects"),
    ("doyoucme",  "invisibility / enemies ignore you"),
]

LEVELS = [  # (spelling, level id written to 0x02000084)
    ("smokey",     1), ("butterfly",  2), ("covey",     3),
    ("tiger",      4), ("hornet",     5), ("litterbug", 6),
    ("mustang",    7), ("spectre",    8), ("nimrod",    9),
    ("spooky",    10),
    ("raven",     21), ("firefly",   22), ("bulldog",  23),
    ("dragon",    24), ("loudmouth", 25), ("stinger",  26),
    ("nail",      27), ("zorro",     28), ("xray",     29),
    ("reddog",    30),
]

MAXLEN = 9
ALPHABET = "abcdefghijklmnopqrstuvwxyz"


def mission_of(level_id):
    """Observed: Ecks ids 1..10 start mission id+1, Sever ids 21..30 start
    mission id-19 (both campaigns have 11 missions; mission 1 has no code)."""
    if 1 <= level_id <= 10:
        return "ECKS", level_id + 1
    if 21 <= level_id <= 30:
        return "SEVER", level_id - 19
    return None, None


def lookup(code):
    """Return ('cheat', bit, desc) | ('level', id, char, mission) | None."""
    c = code.strip().lower()
    if not c or len(c) > MAXLEN or any(ch not in ALPHABET for ch in c):
        return None
    for i, (s, desc) in enumerate(CHEATS):
        if c == s:
            return ("cheat", i, desc)
    for s, lid in LEVELS:
        if c == s:
            char, mission = mission_of(lid)
            return ("level", lid, char, mission)
    return None


def main(argv):
    if len(argv) > 1:
        for code in argv[1:]:
            r = lookup(code)
            if r is None:
                print(f"{code!r}: REJECTED (INCORRECT PASSWORD)")
            elif r[0] == "cheat":
                print(f"{code!r}: cheat bit {r[1]} (0x{1 << r[1]:X}) - {r[2]}")
            else:
                print(f"{code!r}: level id {r[1]} - {r[2]} mission {r[3]}")
        return 0

    print("cheat codes (value written to 0x02005270 is 1<<bit):")
    for i, (s, desc) in enumerate(CHEATS):
        print(f"  bit {i}  0x{1 << i:03X}  {s:<10} {desc}")
    print("\nlevel codes (level id stored at 0x02000084):")
    for s, lid in LEVELS:
        char, mission = mission_of(lid)
        print(f"  id {lid:<3} {s:<10} {char:<5} mission {mission}")
    total = sum(26 ** k for k in range(1, MAXLEN + 1))
    print(f"\naccepted strings: {len(CHEATS) + len(LEVELS)}")
    print(f"input space (A-Z, 1..{MAXLEN} chars): {total:,}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
