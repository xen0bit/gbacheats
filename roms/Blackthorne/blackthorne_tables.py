#!/usr/bin/env python3
"""Regenerate the Blackthorne (GBA, AQXE) cheat/password tables from the ROM.

Usage: python3 blackthorne_tables.py Blackthorne.gba

Verified against SHA-256
2699ea8f2848dc41a5a22dd2ed236c3b8502fad04f9aff0b7e39cc898ef27db8
"""
import sys

BASE = 0x08000000


def main(path):
    rom = open(path, "rb").read()

    def u16(o):
        return rom[o] | (rom[o + 1] << 8)

    print("=== hidden button code table 0x08046FE4 (8 x u16) ===")
    masks = [u16(0x46FE4 + 2 * i) for i in range(8)]
    names = {0x1: "A", 0x2: "B", 0x4: "Select", 0x8: "Start", 0x10: "Right",
             0x20: "Left", 0x40: "Up", 0x80: "Down", 0x100: "R", 0x200: "L"}
    print(" ".join("%04X(%s)" % (m, names.get(m, "?")) for m in masks))

    print("\n=== 17-entry name/code table (runtime index = level-1) ===")
    print("idx level name        code")
    for i in range(17):
        name = rom[0x44534 + 12 * (16 - i):0x44534 + 12 * (16 - i) + 12].split(b"\0")[0].decode()
        code = rom[0x44600 + 8 * (16 - i):0x44600 + 8 * (16 - i) + 4].decode()
        print("%3d %5d %-11s %s" % (i, i + 1, name, code))

    print("\n=== master password table 0x08022C36 (23 x 10 bytes) ===")
    print("#  code id     x      y")
    for i in range(23):
        o = 0x22C36 + 10 * i
        code = rom[o:o + 4].decode()
        print("%2d %-4s %#06x %#06x %#06x" % (i, code, u16(o + 4), u16(o + 6), u16(o + 8)))

    print("\n=== checker / selector addresses ===")
    print("checker            0x08001D28  (called from 0x08001244, state 4 = LOAD GAME slots)")
    print("level selector     0x08001392  (LEFT/RIGHT, clamp 0..0x10)")
    print("save decode        0x080014B4  (17-entry compare)")
    print("level start        0x080015A4  (confirm / write save / start)")
    print("flags              0x030022DC level-select unlocked, 0x030022DD god mode (dead)")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "Blackthorne.gba")
