#!/usr/bin/env python3
"""Power Rangers Time Force (GBA) password codec.

4 symbols x 5 bits = 20 bits, little-endian in the entered string.
Payload (15 bits): v0 marker (=1), chapter A (3), mode (2), continues B (4),
progress flags C (5).  Check bits: v6/v12/v4/v19 are field parities, v16 is
the XOR of those four plus v0.

Validated against the ROM (2 Games in 1 - Power Rangers, MD5
beaa0de66f48e52efcc97b50b7777dec):
  validator 0x08401BB8, submit packer 0x0840D77C, generator 0x08402260,
  check-bit repair 0x08401D14.

Usage:
  python3 time_force_password.py W3DB          # decode + validate
  python3 time_force_password.py --pack 6 2 0 0  # chapter mode continues flags
  python3 time_force_password.py --selftest
"""
import sys

ALPHA = "BCDFGHJKLMNPQRSTVWXYZ0123456789-"
POS = {c: i for i, c in enumerate(ALPHA)}


def pack(chapter, mode, continues, flags):
    """chapter 0..6, mode 0..2, continues 0..15, flags 0..30 -> 4 chars."""
    assert 0 <= chapter <= 6 and 0 <= mode <= 2
    assert 0 <= continues <= 15 and 0 <= flags <= 30
    v = 1  # v0 marker
    a = [(chapter >> i) & 1 for i in range(3)]
    v |= a[0] << 1 | a[1] << 8 | a[2] << 11
    v |= ((continues >> 0) & 1) << 2 | ((continues >> 1) & 1) << 7
    v |= ((continues >> 2) & 1) << 13 | ((continues >> 3) & 1) << 15
    v |= ((mode >> 0) & 1) << 3 | ((mode >> 1) & 1) << 9
    v |= ((flags >> 0) & 1) << 5 | ((flags >> 1) & 1) << 10
    v |= ((flags >> 2) & 1) << 14 | ((flags >> 3) & 1) << 17
    v |= ((flags >> 4) & 1) << 18
    b_par = continues.bit_count() & 1
    m_par = ((mode >> 0) ^ (mode >> 1)) & 1
    v |= (a[0] ^ a[1] ^ a[2]) << 6
    v |= b_par << 12
    v |= m_par << 4
    v |= (flags.bit_count() & 1) << 19
    v |= ((a[0] ^ a[1] ^ a[2]) ^ 1 ^ b_par ^ m_par
          ^ (flags.bit_count() & 1)) << 16
    return "".join(ALPHA[(v >> (5 * i)) & 31] for i in range(4))


def unpack(code):
    if len(code) != 4:
        return None
    try:
        v = sum(POS[c] << (5 * i) for i, c in enumerate(code))
    except KeyError:
        return None
    b = [(v >> i) & 1 for i in range(20)]
    return {
        "value": v,
        "chapter": b[1] | b[8] << 1 | b[11] << 2,
        "mode": b[3] | b[9] << 1,
        "continues": b[2] | b[7] << 1 | b[13] << 2 | b[15] << 3,
        "flags": b[5] | b[10] << 1 | b[14] << 2 | b[17] << 3 | b[18] << 4,
        "check": (b[6], b[12], b[4], b[19], b[16]),
    }


def valid(code):
    d = unpack(code)
    if d is None:
        return False
    b = [(d["value"] >> i) & 1 for i in range(20)]
    return (b[0] == 1
            and (b[1] ^ b[8] ^ b[11]) == b[6]
            and (b[2] ^ b[7] ^ b[13] ^ b[15]) == b[12]
            and (b[3] ^ b[9]) == b[4]
            and (b[5] ^ b[10] ^ b[14] ^ b[17] ^ b[18]) == b[19]
            and (b[6] ^ b[0] ^ b[12] ^ b[4] ^ b[19]) == b[16]
            and d["chapter"] <= 6
            and d["mode"] <= 2
            and d["flags"] <= 30)


def selftest():
    vectors = {  # published codes -> (chapter, mode, continues, flags)
        "HBLD": (0, 0, 5, 0), "KD4Q": (1, 0, 5, 30),
        "CNGF": (2, 0, 8, 0), "FLLF": (3, 0, 12, 0),
        "HDSF": (4, 0, 13, 0), "KGNF": (5, 0, 15, 0),
        "8QSD": (6, 1, 7, 0),
    }
    for code, args in vectors.items():
        assert valid(code), code
        assert pack(*args) == code, (code, pack(*args))
    assert pack(0, 1, 3, 0) == "8GBB"   # generated in-game after HBLD
    assert pack(6, 2, 0, 0) == "W3DB"   # novel code
    for bad in ("HBLB", "BBBB", "FNDB", "CCW7", "MVBD"):
        assert not valid(bad), bad
    n = sum(1 for a in range(7) for m in range(3)
            for b in range(16) for c in range(31) if valid(pack(a, m, b, c)))
    assert n == 10416, n
    print("selftest ok: 7 published vectors, W3DB novel, 5 rejections, "
          "10,416 valid codes")


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--selftest":
        selftest()
    elif len(sys.argv) == 6 and sys.argv[1] == "--pack":
        print(pack(*map(int, sys.argv[2:])))
    elif len(sys.argv) == 2:
        d = unpack(sys.argv[1])
        print(d, "VALID" if valid(sys.argv[1]) else "INVALID")
    else:
        print(__doc__)
        raise SystemExit(1)
