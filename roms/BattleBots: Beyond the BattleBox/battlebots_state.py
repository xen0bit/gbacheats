#!/usr/bin/env python3
"""Read the game-state bytes out of an mGBA PNG savestate (*.ss1...*.ss9).

Usage: python3 battlebots_state.py "BattleBots: Beyond the BattleBox.ss1"

mGBA 0.10.x stores the serialized GBA state zlib-compressed in a PNG chunk
named 'gbAs'.  The 0x61000-byte structure documented in
/usr/include/mgba/internal/gba/serialize.h places IWRAM at 0x19000.
"""
import struct
import sys
import zlib


def iwram(path):
    d = open(path, "rb").read()
    i = d.find(b"gbAs") - 4
    ln = struct.unpack(">I", d[i:i + 4])[0]
    s = zlib.decompress(d[i + 8:i + 8 + ln])
    assert len(s) == 0x61000
    return s[0x19000:0x19000 + 0x8000]


def main(path):
    w = iwram(path)
    for name, addr in [("state 0x030005AC", 0x5AC),
                       ("substate 0x030001A4", 0x1A4),
                       ("init 0x030001A5", 0x1A5)]:
        print("%-20s = 0x%02X" % (name, w[addr]))
    print("held   0x03000194 = 0x%04X" % struct.unpack_from("<H", w, 0x194)[0])
    print("pressed 0x03000196 = 0x%04X" % struct.unpack_from("<H", w, 0x196)[0])
    print("released 0x03000198 = 0x%04X" % struct.unpack_from("<H", w, 0x198)[0])


if __name__ == "__main__":
    main(sys.argv[1])
