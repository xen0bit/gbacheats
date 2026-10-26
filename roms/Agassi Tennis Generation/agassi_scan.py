#!/usr/bin/env python3
"""Reproducible scans for the Agassi Tennis Generation (GBA) report.

Usage: python3 agassi_scan.py "Agassi Tennis Generation.gba"

Prints:
  1. header + hashes
  2. the five 49-entry UI string tables (one per language)
  3. full-ROM keyword scan (password/cheat/debug/secret/unlock/...)
  4. count of Thumb LDR-literal sites for each key-state / save variable
  5. the two KEYINPUT literal sites used for polling
"""
import hashlib
import struct
import sys

TABLES = {  # language -> file offset of the 49-entry u32 string-pointer table
    "EN": 0x58034,
    "DE": 0x58330,
    "ES": 0x5859C,
    "IT": 0x58828,
    "FR": 0x58A90,
}

KEYWORDS = [
    "password", "passwort", "contrase", "mot de passe", "parola d",
    "cheat", "debug", "secret", "unlock", "bonus", "hidden",
    "enter code", "code entry", "extra", "unlockable", "trophy",
]

BASE = 0x08000000


def cstr(rom, addr):
    off = addr - BASE
    end = rom.find(b"#", off)
    return rom[off:end].decode("latin1")


def scan_ldr_value(rom, value):
    """Thumb `ldr rX,[pc,#imm]` sites whose literal word equals `value`."""
    out = []
    for off in range(0, len(rom) - 2, 2):
        h = rom[off] | (rom[off + 1] << 8)
        if (h & 0xF800) != 0x4800:
            continue
        lit = ((BASE + off + 4) & ~3) + (h & 0xFF) * 4
        lo = lit - BASE
        if 0 <= lo <= len(rom) - 4 and struct.unpack_from("<I", rom, lo)[0] == value:
            out.append(BASE + off)
    return out


def main(path):
    rom = open(path, "rb").read()
    print("== 1. identity ==")
    print("size", len(rom), hex(len(rom)))
    for name in ("md5", "sha1", "sha256"):
        print(name, hashlib.new(name, rom).hexdigest())
    print("title", repr(rom[0xA0:0xAC].decode("ascii", "replace").rstrip("\0 ")))
    print("code", rom[0xAC:0xB0].decode("ascii", "replace"),
          "maker", rom[0xB0:0xB2].decode("ascii", "replace"),
          "version", rom[0xBC])
    chk = 0
    for b in rom[0xA0:0xBD]:
        chk = (chk - b) & 0xFF
    print("complement stored", hex(rom[0xBD]), "computed", hex((chk - 0x19) & 0xFF))
    print("header checksum stored", hex(struct.unpack_from("<H", rom, 0xBE)[0]))

    print("\n== 2. UI string tables (49 entries each) ==")
    for lang, base in TABLES.items():
        print(f"-- {lang} @ {hex(BASE + base)}")
        for i in range(49):
            ptr = struct.unpack_from("<I", rom, base + 4 * i)[0]
            print(f"  {i:2d} {ptr:08x} {cstr(rom, ptr)!r}")

    print("\n== 3. keyword scan (whole ROM, case-insensitive) ==")
    low = rom.lower()
    for kw in KEYWORDS:
        print(f"  {kw:16s} {low.count(kw.encode('latin1'))}")

    print("\n== 4. LDR-literal sites per variable ==")
    for var in (0x030008E0, 0x03000980, 0x03000684, 0x030008C0, 0x0E000000):
        sites = scan_ldr_value(rom, var)
        print(f"  {var:08x}: {len(sites)} sites {[hex(s) for s in sites][:6]}")

    print("\n== 5. KEYINPUT / KEYCNT literal sites ==")
    for var in (0x04000130, 0x04000132):
        print(f"  {var:08x}: {[hex(s) for s in scan_ldr_value(rom, var)]}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "Agassi Tennis Generation.gba")
