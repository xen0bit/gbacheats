#!/usr/bin/env python3
"""Alienators: Evolution Continues (GBA, AEVE) password codec.

Reversed from ROM file, matching the validator at 0x0829098C and the
encoder at 0x08290738 (ROM base 0x08000000).

8 symbols, 16-symbol alphabet, 4 bits each, 32-bit packed word XOR
0x571EA60B, 6-bit additive checksum scattered through the bytes.

Use:  python3 alienators_pw.py CODE [CODE ...]
      python3 alienators_pw.py --encode L E V E L M O D E
"""
import sys

ALPHABET = "BCDFGHJKLM PRSTXZ".replace(" ", "")   # 16 symbols, index 0..15
KEY = 0x571EA60B


def decode(code):
    idx = [ALPHABET.index(c) for c in code]
    packed = 0
    for i, v in enumerate(idx):
        packed |= v << (4 * i)
    q = [(packed ^ KEY) >> (8 * i) & 0xFF for i in range(4)]
    payload = [q[0] & ~0x18, q[1] & ~0x18, q[2] & ~0x08, q[3] & ~0x02]
    computed = sum(payload) & 0x3F
    stored = (((q[0] >> 3) & 1) | (((q[0] >> 4) & 1) << 1)
              | (((q[1] >> 3) & 1) << 2) | (((q[1] >> 4) & 1) << 3)
              | (((q[2] >> 3) & 1) << 4) | (((q[3] >> 1) & 1) << 5))
    return {
        "packed": packed, "q": q, "payload": payload,
        "checksum_computed": computed, "checksum_stored": stored,
        "valid": computed == stored,
        "mission_index": (q[3] >> 2) & 0xF,
        "level": ((q[3] >> 2) & 0xF) + 1,
        "mode": q[3] >> 6,
    }


def encode(payload, mission_index=None, mode=None):
    q = list(payload)
    if mission_index is not None:
        q[3] = (q[3] & ~0x3C) | ((mission_index & 0xF) << 2)
    if mode is not None:
        q[3] = (q[3] & 0x3F) | ((mode & 3) << 6)
    c = sum(q) & 0x3F
    q[0] = (q[0] & ~0x18) | ((c & 1) << 3) | (((c >> 1) & 1) << 4)
    q[1] = (q[1] & ~0x18) | (((c >> 2) & 1) << 3) | (((c >> 3) & 1) << 4)
    q[2] = (q[2] & ~0x08) | (((c >> 4) & 1) << 3)
    q[3] = (q[3] & ~0x02) | (((c >> 5) & 1) << 1)
    packed = (q[0] | q[1] << 8 | q[2] << 16 | q[3] << 24) ^ KEY
    return "".join(ALPHABET[(packed >> (4 * i)) & 0xF] for i in range(8))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--encode":
        args = sys.argv[2:]
        level_index = int(args[0])
        mode = int(args[1])
        payload = [int(x, 0) for x in args[2:6]] if len(args) >= 6 else [0, 0, 0, 0]
        print(encode(payload, level_index, mode))
    else:
        for code in sys.argv[1:]:
            d = decode(code)
            print(f"{code}  level={d['level']:2d} idx={d['mission_index']:2d} "
                  f"mode={d['mode']} payload="
                  f"{[hex(x) for x in d['payload']]} "
                  f"chk={d['checksum_computed']:02x}/{d['checksum_stored']:02x} "
                  f"{'OK' if d['valid'] else 'BAD'}")
