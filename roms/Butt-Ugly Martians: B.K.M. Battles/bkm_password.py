#!/usr/bin/env python3
"""Butt-Ugly Martians: B.K.M. Battles (GBA) level-password codec.

Reimplements the 15-symbol password format derived from:
  validator      0x080253F4
  string->state  0x08025730
  checksum       0x08025838
  xor            0x080255A8 / 0x080255FC
  state->string  0x08025650
  generator      0x080251AC

Alphabet at 0x083CFF68, XOR key "SNIPPY02" at 0x083A7C8C,
tables C/A/B at 0x083A7C31 / 0x083A7C51 / 0x083A7C6D.

Usage:
  python3 bkm_password.py decode MBFY6Y3WHBPZBCT
  python3 bkm_password.py encode --level 7 --char 0
  python3 bkm_password.py list
"""
import argparse
import struct

ALPHABET = "*BCDFGHJKLMNPQRSTVWXYZ0123456789"
KEY = b"SNIPPY02"
assert len(ALPHABET) == 32

# C @0x083A7C31 (32 bytes incl. overlap), A @0x083A7C51, B @0x083A7C6D
C = [0, 1, 2, 255, 3, 255, 255, 255, 4, 5, 6, 7, 8, 9, 10, 11,
     12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27]
A = [0, 1, 2, 0, 0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3,
     0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3]
B = [0, 0, 0, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4,
     5, 5, 5, 5, 6, 6, 6, 6, 7, 7, 7, 7]

LEVEL_NAMES = {0: "tutorial/intro", 1: "unknown (solo)", 2: "Mechtropolis",
               3: "Aquatica", 4: "Arborea", 5: "Silicon City",
               6: "Magma", 7: "Koo Foo Ship"}


def char_index(ch):
    """0x08025704: index in ALPHABET; any missing char aliases to 31 ('9')."""
    return ALPHABET.index(ch) if ch in ALPHABET else 31


def checksum(st):
    s = sum((b - 256 if b >= 128 else b) for b in st[0:8])
    s += st[8] & 0xE0
    return s & 0x7F


def decode_string(text):
    """Return (plain_state12, f1). Raises ValueError on a bad checksum."""
    idx = [char_index(c) for c in (text + "\0" * 15)[:15]]
    w0 = 0
    for i in range(6):
        w0 = (w0 << 5) | idx[i]
    w0 = ((w0 << 2) | (idx[6] >> 3)) & 0xFFFFFFFF
    q = idx[6]
    for i in range(7, 12):
        q = (q << 5) | idx[i]
    q &= 0xFFFFFFFF
    w1 = ((q << 4) | (idx[12] >> 1)) & 0xFFFFFFFF
    t = (idx[12] << 10) | (idx[13] << 5) | idx[14]
    w2 = (t << 21) & 0xFFFFFFFF
    st = bytearray(struct.pack("<III", w0, w1, w2))
    chk = checksum(st)
    for i, k in enumerate(KEY):
        st[i] ^= k
    if (st[11] >> 1) != chk:
        raise ValueError("bad checksum: stored %d, computed %d" %
                         (st[11] >> 1, chk))
    return bytes(st), (st[2] >> 2) & 0x1F


def pack_state(plain):
    """plain: 12 decoded bytes (bytes 8/9 must be 0, byte 10 < 8)."""
    st = bytearray(plain)
    for i, k in enumerate(KEY):
        st[i] ^= k
    chk = checksum(st)
    st[11] = (st[11] & 1) | (chk << 1)
    w0, w1, w2 = struct.unpack("<III", bytes(st))
    idx = [0] * 15
    p = w0 >> 2
    for i in range(6):
        idx[i] = (p >> (25 - 5 * i)) & 31
    q = w1 >> 4
    idx[6] = (((w0 & 3) << 3) | ((q >> 25) & 7)) & 31
    for i in range(7, 12):
        idx[i] = (q >> (5 * (11 - i))) & 31
    idx[12] = ((w1 & 0xF) << 1) | ((w2 >> 31) & 1)
    idx[13] = (w2 >> 26) & 31
    idx[14] = (w2 >> 21) & 31
    return "".join(ALPHABET[i] for i in idx), bytes(st)


def fields(plain, f1):
    s = plain
    w0, w1, w2 = struct.unpack("<III", bytes(s))
    return {
        "F1": f1,
        "world": B[f1] if f1 < 28 else None,
        "axis": A[f1] if f1 < 28 else None,
        "v1": (w1 >> 15) & 7,
        "v2": (s[6] >> 2) & 7,
        "v3": (s[6] >> 5) & 7,
        "v4": (struct.unpack("<H", s[4:6])[0] >> 6) & 7,
        "v5": (s[5] >> 1) & 7,
        "v6": (s[5] >> 4) & 7,
        "v7": (s[3] >> 5) & 7,
        "v8": s[4] & 7,
        "v9": (s[4] >> 3) & 7,
        "v10": s[0] & 7,
        "v11": (struct.unpack("<H", s[2:4])[0] >> 7) & 7,
        "v12": (s[3] >> 2) & 7,
        "v13": (s[7] >> 5) & 7,
        "f2": s[7] & 0x1F,
        "d1": (struct.unpack("<H", s[10:12])[0] >> 7) & 3,
        "d2": (s[10] >> 5) & 3,
    }


def code_for(level, axis_value, zero_state=True):
    f1 = C[level * 4 + axis_value]
    if f1 == 255:
        raise ValueError("invalid (level, axis) combination")
    st = bytearray(12) if zero_state else bytearray(12)
    st[2] = (f1 & 0x1F) << 2
    return pack_state(st)[0]


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("decode")
    d.add_argument("code")
    e = sub.add_parser("encode")
    e.add_argument("--level", type=int, required=True)
    e.add_argument("--char", type=int, required=True, dest="axis")
    sub.add_parser("list")
    args = ap.parse_args()

    if args.cmd == "decode":
        st, f1 = decode_string(args.code)
        print("state:", st.hex())
        for k, v in fields(st, f1).items():
            print(f"  {k} = {v}")
    elif args.cmd == "encode":
        print(code_for(args.level, args.axis))
    elif args.cmd == "list":
        for f1 in range(28):
            lv, ax = B[f1], A[f1]
            print(f"world {lv} axis {ax} F1 {f1:2d}  {code_for(lv, ax)}  "
                  f"{LEVEL_NAMES.get(lv, '?')}")


if __name__ == "__main__":
    main()
