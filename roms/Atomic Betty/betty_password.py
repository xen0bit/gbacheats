#!/usr/bin/env python3
"""Atomic Betty (GBA, BETE) four-portrait password codec.

ROM analysed:
  roms/Atomic Betty/Atomic Betty.gba
  md5    a3dd3b98ad5049503af18f80c84731fc
  sha1   59e7400802ab634065b9674de3f437ddf8309d6e
  sha256 e85966aef5fded854a4c1d833f6ef6750a466975402b9f3bd87eead4bc96aa35

Format (derived from the ARM validator at 0x0805C8F8):
  four portrait slots, each value 0..7
  packed = d0*512 + d1*64 + d2*8 + d3      (base-8, left to right)
  the packed value is looked up in a 21-entry u32 table at ROM 0x087349B4
  (RAM copy 0x03004568).  Entries are 0x000..0xFFF, so exactly 21 of the
  4096 possible codes are accepted; everything else shows "Incorrect Password".

The first table entry is 0x00000000, i.e. Betty/Betty/Betty/Betty, which is also
the screen's default selection and starts the game from the training stage.

This script only reads the user's own ROM; it distributes no game data.
"""
import os
import struct
import sys

ROM = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Atomic Betty.gba")
TABLE_OFF = 0x7349B4          # file offset; ROM address 0x087349B4
TABLE_COUNT = 21

# Internal portrait ids, in the order the on-screen selector stores them.
NAMES = ["Betty", "Red Robot", "Chameleon", "Maximus",
         "Minimus", "Gray Robot", "Sparky", "X-5"]

# Published list (GameFAQs "knucklessonic8" + "Foppe"), used only to verify
# the table->level ordering.  Labels are the published ones.
PUBLISHED = {
    2:  "Red Robot, X-5, Betty, Minimus",
    3:  "Chameleon, Gray Robot, Gray Robot, Maximus",
    4:  "Minimus, Red Robot, X-5, Gray Robot",
    5:  "Betty, Gray Robot, Chameleon, Sparky",
    6:  "Red Robot, Betty, X-5, Sparky",
    7:  "Maximus, Chameleon, Maximus, X-5",
    8:  "X-5, Maximus, Maximus, X-5",
    9:  "Gray Robot, Minimus, Betty, Chameleon",
    10: "X-5, X-5, Red Robot, Minimus",
    11: "X-5, Maximus, Maximus, Gray Robot",
    12: "Minimus, Sparky, Betty, Maximus",
    13: "Betty, Chameleon, Betty, Chameleon",
    14: "Gray Robot, Minimus, Betty, Maximus",
    15: "Gray Robot, Betty, X-5, Chameleon",
    16: "Gray Robot, Chameleon, Chameleon, Maximus",
    17: "Chameleon, Chameleon, X-5, Maximus",
    18: "Minimus, Minimus, Chameleon, Chameleon",
    19: "Betty, X-5, Chameleon, Red Robot",   # published "Last Boss"
}


def encode(digits):
    return (digits[0] << 9) | (digits[1] << 6) | (digits[2] << 3) | digits[3]


def decode(value):
    return [(value >> 9) & 7, (value >> 6) & 7, (value >> 3) & 7, value & 7]


def load_table(path=ROM):
    rom = open(path, "rb").read()
    return list(struct.unpack_from("<%dI" % TABLE_COUNT, rom, TABLE_OFF))


def name_code(digits):
    return ", ".join(NAMES[d] for d in digits)


def main():
    table = load_table()
    print("index  packed  code")
    for i, v in enumerate(table):
        label = ""
        if i == 0:
            label = "  (default selection / training stage)"
        elif i in (1, 2):
            label = "  (pre-Level-2 checkpoint; not published)"
        elif 3 <= i <= 19:
            label = "  = published Level %d" % (i - 1)
        elif i == 20:
            label = "  = published Last Boss"
        print("%5d  0x%03X  %s%s" % (i, v, name_code(decode(v)), label))

    # Verify the published list is a subset of the table.
    pub_vals = set()
    for level, text in PUBLISHED.items():
        names = text.split(", ")
        digits = [NAMES.index(n) if n != "Atomic Betty" else 0 for n in names]
        pub_vals.add(encode(digits))
        assert encode(digits) in table, (level, text)
    print("\nall %d published codes are table entries" % len(pub_vals))

    # Enumerate the whole space.
    valid = set(table) & set(range(4096))
    print("space = 8^4 = %d, accepted = %d, rejected = %d"
          % (4096, len(valid), 4096 - len(valid)))

    if len(sys.argv) == 2:
        text = sys.argv[1]
        names = [n.strip() for n in text.split(",")]
        digits = [NAMES.index(n) if n != "Atomic Betty" else 0 for n in names]
        v = encode(digits)
        print("code %s -> 0x%03X  %s"
              % (name_code(digits), v,
                 "ACCEPTED (table index %d)" % table.index(v)
                 if v in table else "REJECTED"))


if __name__ == "__main__":
    main()
