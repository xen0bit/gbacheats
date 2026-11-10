#!/usr/bin/env python3
"""CT Special Forces 2: Back in the Trenches (GBA, A9CE) - password decoder.

Reads the 250 x 4-byte code table at ROM 0x087D8618 (file 0x7D8618) and
reimplements the in-game validator:

    index = linear search of the 4 digit bytes in the table (0..249)
    if index < 0: reject
    level = index // 10
    lives = index % 10
    if level > 21: reject          (0x080009AC, cmp #21)
    accept -> [0x0300000C] = level (u32), [0x0300314C] = lives (u16)

Usage: python3 ctsf2_password.py [ROM]
       python3 ctsf2_password.py --list
"""
import struct, sys

TABLE_ROM = 0x087D8618
COUNT = 250

def load_table(path):
    rom = open(path, "rb").read()
    off = TABLE_ROM - 0x08000000
    t = []
    for i in range(COUNT):
        t.append(tuple(rom[off + 4*i: off + 4*i + 4]))
    return t

def validate(table, code):
    digits = tuple(int(c) for c in code)
    for i, rec in enumerate(table):
        if rec == digits:
            level, lives = divmod(i, 10)
            return (level <= 21, i, level, lives)
    return (False, None, None, None)

def main():
    path = "game.gba"
    args = [a for a in sys.argv[1:]]
    if "--list" in args:
        args.remove("--list")
        rompath = args[0] if args and args[0].lower().endswith(".gba") else path
        table = load_table(rompath)
        for i, rec in enumerate(table):
            level, lives = divmod(i, 10)
            print(f"{i:3d} {''.join(map(str,rec))} level={level:2d} lives={lives} {'ok' if level<=21 else 'DEAD'}")
        return
    if args and args[0].lower().endswith(".gba"):
        path = args.pop(0)
    table = load_table(path)
    for code in args or ["1431"]:
        ok, i, level, lives = validate(table, code)
        print(f"{code}: accepted={ok} index={i} level={level} lives={lives}")

if __name__ == "__main__":
    main()
