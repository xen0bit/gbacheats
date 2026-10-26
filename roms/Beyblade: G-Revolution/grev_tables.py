#!/usr/bin/env python3
"""Beyblade: G-Revolution (GBA) -- table/address dumper.

Reproduces the static findings in the report:
  * identity fields
  * the debug-menu gate expression and the only write to it
  * the 82-entry debug level-select table
  * the debug screen struct chain

Usage: python3 grev_tables.py "/path/to/Beyblade: G-Revolution.gba"
"""
import hashlib
import struct
import sys

BASE = 0x08000000


def u16(rom, off):
    return struct.unpack_from("<H", rom, off)[0]


def u32(rom, off):
    return struct.unpack_from("<I", rom, off)[0]


def cstr(rom, addr, n=40):
    off = addr - BASE
    return rom[off:off + n].split(b"\0")[0].decode("latin1", "replace")


def main(path):
    rom = open(path, "rb").read()
    print("size      ", len(rom), hex(len(rom)))
    print("title     ", repr(rom[0xA0:0xAC]))
    print("game code ", repr(rom[0xAC:0xB0]))
    print("maker     ", repr(rom[0xB0:0xB2]))
    print("version   ", rom[0xBC])
    print("md5       ", hashlib.md5(rom).hexdigest())
    print("sha1      ", hashlib.sha1(rom).hexdigest())
    print("sha256    ", hashlib.sha256(rom).hexdigest())
    s = sum(rom[0xA0:0xBD])
    print("complement check stored/computed", hex(rom[0xBD]), hex((-s - 0x19) & 0xFF))
    print("header checksum stored/computed  ", hex(u16(rom, 0xBE)),
          hex((-(s + 0x19)) & 0xFFFF))

    print("\n--- debug gate ---")
    print("pause-menu list builder     0x%08x" % (BASE + 0x53010))
    print("  ldr r0,=0x03000198 ...   0x%08x" % (BASE + 0x5301A))
    print("  ldr r1,=0x00001850 ...   0x%08x" % (BASE + 0x5301E))
    print("  ldrb / cmp #0 / beq      0x%08x .. 0x%08x" % (BASE + 0x53022, BASE + 0x5302A))
    print("gate expression             *(u8*)(*(u32*)0x03000198 + 0x1850) != 0")
    print("only writer (zeroes it):    0x%08x (state init)" % (BASE + 0x46196))
    print("  bytes                       ", rom[0x46196:0x4619c].hex())

    print("\n--- debug screens (screen-id table at 0x%08x) ---" % (BASE + 0xBA1A8))
    for idx, name in [(31, "Select level"), (34, "Blader stats editor"),
                      (35, "Test/QA root"), (36, "View characters"),
                      (37, "Level viewer"), (38, "Inventory editor"),
                      (39, "Blade editor")]:
        p = u32(rom, 0xBA1A8 + idx * 4) - BASE
        vals = [u32(rom, p + i) for i in range(0, 0x30, 4)]
        print("%2d %-20s struct 0x%08x enter 0x%08x update 0x%08x input 0x%08x"
              % (idx, name, BASE + p, vals[0], vals[1], vals[2]))

    print("\n--- debug level-select table 0x%08x ---" % (BASE + 0xBB110))
    off = 0xBB110
    n = 0
    while True:
        lid, x, y, namep = struct.unpack_from("<IIII", rom, off)
        if lid == 0xFFFFFFFF:
            break
        print("%2d id=0x%02x (%3d) x=%4d y=%4d %s"
              % (n, lid, lid, x, y, cstr(rom, namep)))
        off += 16
        n += 1
    print("count", n, "terminator at 0x%08x" % (BASE + off))

    print("\n--- strings ---")
    for off, *rest in [(0x3A86F4, "Test/QA"), (0x3A7384, "Select level"),
                       (0x3A7394, "Blader stats editor"),
                       (0x3A73A8, "View characters"),
                       (0x3A73B8, "Level viewer"),
                       (0x3A73C8, "Inventory editor"),
                       (0x3A73DC, "Blade editor"),
                       (0x3A74C8, "Use shoulder buttons to change blade")]:
        print("0x%08x %s" % (BASE + off, cstr(rom, BASE + off)))

    print("\n--- beyblade picker table (dragoon S record) ---")
    print("record base 0x%08x, stride 0x28" % (BASE + 0x7A1F4))
    for k in range(6):
        o = 0x7A1F4 + k * 0x28
        print("  +0x%02x %s" % (k * 0x28, cstr(rom, u32(rom, o))))


if __name__ == "__main__":
    main(sys.argv[1])
