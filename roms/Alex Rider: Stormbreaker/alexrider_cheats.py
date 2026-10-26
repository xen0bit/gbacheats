#!/usr/bin/env python3
"""Alex Rider: Stormbreaker (GBA, BAWE) cheat-table extractor / savestate reader.

Usage:
  python3 alexrider_cheats.py                 # identity + full cheat table
  python3 alexrider_cheats.py state.ss1       # also dump cheat RAM from an mGBA savestate

The ROM is expected next to this script (or set AR_ROM).
"""
import hashlib, os, struct, sys, zlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROM = os.environ.get("AR_ROM", os.path.join(HERE, "Alex Rider: Stormbreaker.gba"))
BASE = 0x08000000

CODE_IDS = 0x37A9A2       # u16[10] text IDs of the expected code strings
NAME_IDS = 0x37A98E       # u16[10] text IDs of the cheat names
KEYPAD   = 0x37A9B6       # 40 key bytes (38 typeable + backspace 0x22 + enter 0x0A)
BANK     = 0x3B9C60       # text bank (English); language tables selected via +8+lang*8

def load():
    return open(ROM, "rb").read()

def text_table(rom, lang=0):
    descr = struct.unpack_from("<I", rom, BANK + 8 + lang * 8)[0]
    return BANK + ((descr >> 2) << 2)

def text(rom, tid, lang=0):
    t = text_table(rom, lang)
    off = struct.unpack_from("<I", rom, t + tid * 4)[0]
    p = t + off
    if p >= len(rom):
        return None
    e = rom.find(b"\0", p)
    return rom[p:e].decode("ascii", "replace") if 0 <= e - p < 200 else None

def main():
    rom = load()
    print("size  %d (0x%x)" % (len(rom), len(rom)))
    print("md5   " + hashlib.md5(rom).hexdigest())
    print("sha1  " + hashlib.sha1(rom).hexdigest())
    print("sha256 " + hashlib.sha256(rom).hexdigest())
    print("title %r code %r maker %r version %d" % (
        rom[0xA0:0xAC].decode("ascii", "replace").rstrip("\0 "),
        rom[0xAC:0xB0].decode("ascii", "replace"),
        rom[0xB0:0xB2].decode("ascii", "replace"), rom[0xBC]))
    print()
    names = struct.unpack_from("<10H", rom, NAME_IDS)
    codes = struct.unpack_from("<10H", rom, CODE_IDS)
    print("slot  name-id name                   code-id  code            file-off")
    for i in range(10):
        c = text(rom, codes[i])
        n = text(rom, names[i])
        t = text_table(rom)
        off = struct.unpack_from("<I", rom, t + codes[i] * 4)[0]
        print("%4d  0x%02x    %-22s 0x%02x     %-15s 0x%x" % (i, names[i], n, codes[i], c, t + off))
    print("\nkeypad alphabet (typeable): %r" % rom[KEYPAD:KEYPAD + 38])
    print("key 38 -> 0x%02x (backspace), key 39 -> 0x%02x (enter)" % (rom[KEYPAD + 38], rom[KEYPAD + 39]))
    print("\nbit i of 0x0200018C enables slot i (built at 0x0801FB40)")
    print("RAM: 0x02006be8 + 4*slot = {unlocked, enabled, 0, 0}")
    if len(sys.argv) > 1:
        d = open(sys.argv[1], "rb").read()
        i = d.find(b"gbAs"); ln = struct.unpack_from(">I", d, i - 4)[0]
        st = zlib.decompress(d[i + 4:i + 4 + ln])
        tbl = st[0x21000 + 0x6BE8:0x21000 + 0x6BE8 + 40]
        flags = struct.unpack_from("<H", st, 0x21000 + 0x18C)[0]
        print("\nsavestate %s" % sys.argv[1])
        print(" table: " + " ".join("%d:%02x%02x" % (i, tbl[i*4], tbl[i*4+1]) for i in range(10)))
        print(" flags: 0x%04x" % flags)

if __name__ == "__main__":
    main()
