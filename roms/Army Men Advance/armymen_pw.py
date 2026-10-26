#!/usr/bin/env python3
"""Army Men Advance (GBA) level-password encoder/decoder.

Format (reverse-engineered from the retail ROM, see "Army Men Advance.md"):
  8 symbols from the on-screen ring alphabet
      BCDFGHJKLMNPQRSTVWXYZ!
  v[i]  = alphabet_index(code[i]) XOR KEY[i]
  check = (45 - (v[2]&15) - (v[5]&15) - (v[7]&15)) & 15   ==  v[0]&15
  level = 16 - (v[5]&15)          (1..12 in retail content)
  char  = 15 - (v[7]&15)          (0 = Sarge, 1 = Vicki)
  v[1], v[2], v[3], v[4], v[6] are free filler (v[2] participates in the
  checksum; v[0] is the check nibble and is recomputed).

KEY was dumped from ROM 0x083BCF5C (8 bytes):
      07 02 03 09 0A 0B 08 0E
"""
import sys

KEY = [7, 2, 3, 9, 10, 11, 8, 14]
ALPHABET = "BCDFGHJKLMNPQRSTVWXYZ!"   # 22 symbols; '#' (index 22) is not selectable
LEVELS = ["TAN ARMY JAIL", "TRAINING CAMP", "AREA 41", "HANGAR 13",
          "BEDROOM", "HALLWAY", "BATHROOM", "IN THE BATH", "PATIO",
          "GARAGE", "GREEN CAMP", "AREA 41-RETURN"]
CHARS = ["Sarge", "Vicki"]


def decode(code):
    """Return the eight nibble values v[0..7] for an 8-symbol code."""
    if len(code) != 8:
        raise ValueError("password must be 8 symbols")
    return [(ALPHABET.index(c) ^ KEY[i]) for i, c in enumerate(code)]


def is_valid(code):
    try:
        v = decode(code)
    except ValueError:
        return False
    return (v[0] & 15) == ((45 - (v[2] & 15) - (v[5] & 15) - (v[7] & 15)) & 15)


def fields(code):
    """Decode level and character; raises ValueError for an invalid code."""
    if not is_valid(code):
        raise ValueError("bad checksum")
    v = decode(code)
    return 16 - (v[5] & 15), 15 - (v[7] & 15)


def encode(level, char, v1=0, v2=14, v3=0, v4=0, v6=0):
    """Mint a code.

    level 1..15 (1..12 correspond to real levels), char 0..15 (0/1 real).
    v1,v2,v3,v4,v6 are arbitrary nibbles (filler); defaults reproduce the
    all-zero filler family.  Returns None if level+char cannot fit the check
    nibble (the validator then has no accepted value).
    """
    v5 = (16 - level) & 15
    v7 = (15 - char) & 15
    check = 45 - v2 - v5 - v7
    if not 0 <= check <= 15:
        return None
    v0 = check
    nibbles = [v0, v1, v2, v3, v4, v5, v6, v7]
    idx = [nibbles[i] ^ KEY[i] for i in range(8)]
    if any(not 0 <= x < len(ALPHABET) for x in idx):
        return None
    return "".join(ALPHABET[x] for x in idx)


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 1
    cmd = argv[1]
    if cmd == "decode":
        for c in argv[2:]:
            try:
                lv, ch = fields(c)
                v = decode(c)
                print(f"{c}: valid  level={lv} ({LEVELS[lv-1] if 1 <= lv <= 12 else 'out of range'})  "
                      f"char={ch} ({CHARS[ch] if 0 <= ch < 2 else 'out of range'})  v={v}")
            except ValueError as e:
                print(f"{c}: INVALID ({e})")
    elif cmd == "make":
        level, char = int(argv[2]), int(argv[3])
        defaults = [0, 14, 0, 0, 0]          # filler order: v1 v2 v3 v4 v6
        given = [int(x, 0) for x in argv[4:9]]
        filler = given + defaults[len(given):]
        v1, v2, v3, v4, v6 = filler
        code = encode(level, char, v1, v2, v3, v4, v6)
        print(code if code else "no representable code for those fields")
    else:
        print(__doc__)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
