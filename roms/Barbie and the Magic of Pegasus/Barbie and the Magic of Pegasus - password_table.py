#!/usr/bin/env python3
"""Decoder / table dump for Barbie and the Magic of Pegasus (GBA, BE5E).

Reads the 34-entry password table straight from the ROM and reproduces every
result in "Barbie and the Magic of Pegasus.md".  Usage:

    python3 "Barbie and the Magic of Pegasus - password_table.py" "Barbie and the Magic of Pegasus.gba"
    python3 "Barbie and the Magic of Pegasus - password_table.py" ROM 0 1 4 1

The four arguments after the ROM are *display* indices:
    0 Palace  1 Ollie/Ogre  2 Wenlock  3 Wand  4 Brietta/Pegasus  5 Annika
"""
import sys

TABLE = 0x141878          # 34 * 4 bytes
LEVEL_CHARS = 0x141900    # 17 bytes: "012/9:;8<=>?,-.+3"
SYMBOLS = ["Palace", "Ollie", "Wenlock", "Wand", "Brietta", "Annika"]
# key: n = index-1 (Easy) or index-18 (Normal); value: observed screen id
LEVELS = {
    "0": 49, "1": 50, "2": 40, "/": 18, "9": 58, ":": 59, ";": 39, "8": 19,
    "<": 61, "=": 62, ">": 38, "?": 20, ",": 45, "-": 46, ".": 37, "+": 13,
}
NAMES = {49: "Cloud 2", 50: "Cloud 3", 40: "CINEMA CLOUD BOSS", 18: "Flying 2",
         58: "Village 2", 59: "Village 3", 39: "CINEMA VILLAGE BOSS", 19: "Flying 3",
         61: "Forest 2", 62: "Forest 3", 38: "CINEMA FOREST BOSS", 20: "Flying 4",
         45: "Glacier 2", 46: "Glacier 3", 37: "CINEMA GLACIER BOSS", 13: "Final boss"}


def load(path):
    rom = open(path, "rb").read()
    assert rom[0xA0:0xAC].rstrip(b"\0 ") == b"BARBIEPEGASU", "wrong ROM"
    return rom


def raw_of(display):
    """Display index -> value stored in the password entity (+0x28)."""
    return [(-x) % 6 for x in display]


def entries(rom):
    return [tuple(rom[TABLE + 4 * i:TABLE + 4 * i + 4]) for i in range(34)]


def decode(rom, display):
    raw = raw_of(display)
    for i, e in enumerate(entries(rom)):
        if list(e) == raw:
            if i in (0, 17):
                return i, None, None, "padding (matched, no level)"
            if i <= 16:
                n, diff = i - 1, "Easy"
            else:
                n, diff = i - 18, "Normal"
            ch = chr(rom[LEVEL_CHARS + n])
            lvl = LEVELS.get(ch)
            return i, lvl, diff, "level char %r -> screen %d (%s)" % (ch, lvl, NAMES.get(lvl, "?"))
    return None, None, None, "not in table (rejected)"


def main():
    rom = load(sys.argv[1])
    if len(sys.argv) > 2:
        d = [int(x) for x in sys.argv[2:6]]
        print(d, decode(rom, d))
        return
    for i, e in enumerate(entries(rom)):
        disp = [(-x) % 6 for x in e]
        s = " ".join(SYMBOLS[x] for x in disp)
        tag = "padding" if i in (0, 17) else ("Easy" if i < 17 else "Normal")
        print("%2d  raw=%s  %-40s %s" % (i, ",".join(map(str, e)), s, tag))
    # exhaustive count over the 6^4 UI space
    acc = []
    for v in range(1296):
        d = [v % 6, (v // 6) % 6, (v // 36) % 6, (v // 216) % 6]
        i, lvl, diff, _ = decode(rom, d)
        if lvl is not None:
            acc.append((tuple(d), lvl, diff))
    print("accepted level codes:", len(acc))
    for a in sorted(acc, key=lambda t: (t[1], t[2])):
        print(" ", a)


if __name__ == "__main__":
    main()
