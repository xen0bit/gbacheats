#!/usr/bin/env python3
"""Enumerate the Barbie in the 12 Dancing Princesses (GBA) 4-icon password table.

Usage: python3 password_enum.py "Barbie in the 12 Dancing Princesses.gba"

The ROM stores a 416-record table of 4-byte passwords at file offset 0x1275F0
(ROM address 0x081275F0).  Records are 13 levels x 32 variants.  A record is
enterable only if all four bytes are in 0..7 (the entry screen exposes 8 icons).
"""
import sys

ROM = sys.argv[1] if len(sys.argv) > 1 else "Barbie in the 12 Dancing Princesses.gba"
TABLE = 0x1275F0
COUNT = 416
ICONS = ["Blonde Girl", "Slippers", "Old Lady", "Bird",
         "Prince", "Cat", "Brunette Girl", "Monkey"]
LEVELS = ["2-A", "2-B", "3-A", "3-B", "4-A", "4-B", "5-A", "5-B",
          "6-A", "6-B", "7-A", "7-B", "8"]
PUBLISHED = {
    "2-A": (5, 5, 1, 4), "2-B": (5, 2, 3, 7), "3-A": (2, 1, 1, 1),
    "3-B": (0, 0, 7, 0), "4-A": (2, 6, 5, 6), "4-B": (7, 4, 0, 3),
    "5-A": (2, 3, 1, 7), "5-B": (6, 3, 0, 2), "6-A": (4, 7, 0, 2),
    "6-B": (6, 5, 2, 1), "7-A": (0, 6, 4, 2), "7-B": (7, 5, 0, 2),
    "8": (0, 0, 4, 6),
}
# mariogba.nl's character-name list is mislabeled but is still a public list.
# Exclude every code it can produce under either girl-name assignment.
OTHER_PUBLIC = {
    (3, 0, 6, 0), (3, 6, 0, 6), (2, 3, 1, 7), (3, 1, 5, 0),
    (3, 1, 5, 6), (1, 2, 4, 4), (3, 3, 0, 6), (3, 3, 6, 0),
    (1, 0, 7, 5), (1, 6, 7, 5), (5, 0, 4, 0), (5, 6, 4, 6),
}

rom = open(ROM, "rb").read()
records = [tuple(rom[TABLE + 4 * i: TABLE + 4 * i + 4]) for i in range(COUNT)]
valid = [(i, r) for i, r in enumerate(records) if max(r) <= 7]

print("space: 8^4 = 4096")
print("table records:", COUNT, " enterable:", len(valid),
      " distinct:", len(set(r for _, r in valid)))
for row, level in enumerate(LEVELS):
    codes = [(i, r) for i, r in valid if i // 32 == row]
    novel = [x for x in codes if x[1] not in PUBLISHED.values()
                   and x[1] not in OTHER_PUBLIC]
    print("\nlevel %-3s (row %2d): %2d codes" % (level, row, len(codes)))
    print("  published:", PUBLISHED[level], "index",
          next(i for i, r in codes if r == PUBLISHED[level]))
    if novel:
        i, r = novel[0]
        print("  novel    :", r, "index", i,
              "=", ", ".join(ICONS[x] for x in r),
              "| flags col=%d" % (i % 32))

# Flag model recovered from 0x080154F0.
def flags(index):
    row, col = divmod(index, 32)
    return {
        "level": row + 1,
        "b4": col & 1,
        "w990_bit29": (col >> 1) & 1,
        "6c1c_1_bit2": (col >> 2) & 1,
        "6c1c_2_bit2": (col >> 3) & 1,
        "6c1c_3_bit2": (col >> 4) & 1,
        "6ba8": 3 + bin(col & 0x1C).count("1"),
    }

for code in [(4, 4, 5, 4), (1, 4, 6, 4), (5, 5, 6, 4),
             (3, 1, 4, 3), (5, 6, 2, 4)]:
    i = next(i for i, r in valid if r == code)
    print("\n", code, "index", i, flags(i))
