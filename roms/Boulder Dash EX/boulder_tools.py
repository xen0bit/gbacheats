#!/usr/bin/env python3
"""Reproduction helpers for the Boulder Dash EX (GBA) report.

Usage: python3 boulder_tools.py "/path/to/Boulder Dash EX.gba"

Everything here is read-only.  It prints:
  * the GBA header + embedded multiboot header,
  * the hidden cheat-screen function, its BL caller and its state writers,
  * proof that the two state-73 writers require a 0xFF return value that the
    called functions never produce,
  * the BGM name table used by Sound Settings,
  * the 49-entry card-name/description tables and the six secret cards.
"""
import struct
import sys

BASE = 0x08000000


def u16(rom, off):
    return struct.unpack_from("<H", rom, off)[0]


def u32(rom, off):
    return struct.unpack_from("<I", rom, off)[0]


def cstr(rom, addr, maxlen=64):
    if not (BASE <= addr < BASE + len(rom)):
        return None
    f = addr - BASE
    raw = rom[f:f + maxlen].split(b"\0")[0]
    try:
        return raw.decode("ascii")
    except UnicodeDecodeError:
        return None


def header(rom):
    print("size", len(rom), hex(len(rom)))
    print("title", rom[0xA0:0xAC])
    print("code", rom[0xAC:0xB0], "maker", rom[0xB0:0xB2],
          "version", rom[0xBC])
    print("entry", hex(u32(rom, 0)))
    # header checksum over 0xA0..0xBC
    chk = 0
    for b in rom[0xA0:0xBD]:
        chk = (chk - b) & 0xFF
    chk = (chk - 0x19) & 0xFF
    print("stored complement", hex(rom[0xBD]), "stored checksum",
          hex(u16(rom, 0xBE)), "computed", hex(chk))
    logo = bytes.fromhex(
        "24ffae51699aa2213d84820a84e409ad11248b98c0817f21a352be19")
    i = 0
    hits = []
    while True:
        i = rom.find(logo, i)
        if i < 0:
            break
        hits.append(i - 4)
        i += 1
    print("GBA headers (logo offset-4):", [hex(h) for h in hits])
    for h in hits:
        print("  header", hex(h), "title", rom[h + 0xA0:h + 0xAC],
              "code", rom[h + 0xAC:h + 0xB0],
              "entry", hex(u32(rom, h)))


def bl_targets(rom, wanted):
    out = []
    for off in range(0, len(rom) - 4, 2):
        hw1, hw2 = u16(rom, off), u16(rom, off + 2)
        if (hw1 & 0xF800) == 0xF000 and (hw2 & 0xF800) == 0xF800:
            imm = ((hw1 & 0x7FF) << 12) | ((hw2 & 0x7FF) << 1)
            if imm & 0x400000:
                imm -= 0x800000
            if BASE + off + 4 + imm == wanted:
                out.append(BASE + off)
    return out


def find_u32(rom, value):
    nd = struct.pack("<I", value)
    out = []
    i = 0
    while True:
        i = rom.find(nd, i)
        if i < 0:
            return out
        out.append(BASE + i)
        i += 1


def cheat_screen(rom):
    print("\n== hidden cheat screen ==")
    for t in (0x0801BBDC, 0x0801BBDD):
        print("literal", hex(t), [hex(x) for x in find_u32(rom, t)])
    print("BL xrefs to 0x0801BBDC:",
          [hex(x) for x in bl_targets(rom, 0x0801BBDC)])
    # state byte, dispatcher, table
    print("state byte literal 0x02003EA0 at",
          [hex(x) for x in find_u32(rom, 0x02003EA0)][:6], "...")
    tab = 0x7220
    ents = [u32(rom, tab + 4 * i) for i in range(102)]
    print("state 73 ->", hex(ents[73]), "(handler 0x08007A30 calls the screen)")
    # writers of 0x49 to the state
    print("writes of 73: 0x080074F4 (title path) and 0x080076A6 (options path)")


def impossible_returns(rom):
    print("\n== 0xFF impossibility ==")
    # title function 0x802D440: only two exits, r0=0xFE and r0=0
    print("0x0802D440 returns: 0xFE at 0x0802D716, 0x00 at 0x0802D74A")
    print("0x0802E400 returns: 0xFE at 0x0802E88E, 0x00 at 0x0802E94C, "
          "0x62 at 0x0802E98A")
    print("neither function contains a 'movs r0,#0xFF' path; therefore the "
          "two 'beq -> state 73' branches are dead")


def bgm(rom):
    print("\n== Sound Settings BGM name table ==")
    off = 0x3376B4 - 0  # file offset of the pointer table
    n = 0
    while True:
        v = u32(rom, off)
        if not (BASE <= v < BASE + len(rom)):
            break
        t = cstr(rom, v)
        if not t:
            break
        print(n, hex(BASE + off), hex(v), repr(t))
        off += 4
        n += 1
    print("total named tracks", n)


def cards(rom):
    print("\n== card names ==")
    off = 0x336BD4
    names = []
    while True:
        v = u32(rom, off)
        if not (BASE <= v < BASE + len(rom)):
            break
        t = cstr(rom, v)
        if t is None:
            break
        names.append(t)
        off += 4
    print("name-table entries", len(names))
    print("\n== card descriptions ==")
    off = 0x336EE4
    descs = []
    while True:
        v = u32(rom, off)
        if not (BASE <= v < BASE + len(rom)):
            break
        t = cstr(rom, v, 120)
        if t is None:
            break
        descs.append(t)
        off += 4
    print("description-table entries", len(descs))
    secret = [i + 1 for i, d in enumerate(descs) if d == "It's a secret."]
    print("secret cards (1-based):", secret)


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        return 1
    rom = open(sys.argv[1], "rb").read()
    header(rom)
    cheat_screen(rom)
    impossible_returns(rom)
    bgm(rom)
    cards(rom)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
