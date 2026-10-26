#!/usr/bin/env python3
"""Reproducible static evidence for the BattleBots: Beyond the BattleBox report.

Usage: python3 battlebots_scan.py "BattleBots: Beyond the BattleBox.gba"

Prints: header/hashes; text-bank keyword counts; robot/arena/option/pit
pointer tables; the SRAM slot layout expectation; the key-input globals and
the state/handler tables. Exits non-zero if the password-system probes that
are present in the "Design & Destroy" re-release are found here (they are not).
"""
import hashlib
import re
import struct
import sys

OFF_TEXT_BANK = 0x3A000          # main English text bank (observed)
OFF_TEXT_BANK_END = 0x46000


def main(path):
    rom = open(path, "rb").read()

    print("== identity ==")
    print("size", len(rom), hex(len(rom)))
    for algo in ("md5", "sha1", "sha256"):
        print(algo, getattr(hashlib, algo)(rom).hexdigest())
    print("title", rom[0xA0:0xAC].rstrip(b"\0 ").decode())
    print("game code", rom[0xAC:0xB0].decode(), "maker", rom[0xB0:0xB2].decode())
    print("version", rom[0xBC], "complement", hex(rom[0xBD]))
    logo = bytes.fromhex(
        "24ffae51699aa2213d84820a84e409ad11248b98c0817f21a352be19"
        "9309ce2010464a4af82731ec58c7e83382e3cebf85f4df94ce4b09c1"
        "94568ac01372a7fc9f844d73a3ca9a615897a327fc039876231dc761"
        "0304ae56bf38840040a70efdff52fe036f9530f197fbc08560d68025a9"
        "63be03014e38e2f9a234ffbb3e0344780090cb88113a9465c07c6387f0"
        "3cafd625e48b380aac7221d4f807")
    hits = [m.start() - 4 for m in re.finditer(re.escape(logo), rom)]
    print("GBA logo headers", [hex(h) for h in hits])

    print("\n== text scan ==")
    runs = []
    i = 0
    while i < len(rom):
        if 32 <= rom[i] < 127:
            j = i
            while j < len(rom) and 32 <= rom[j] < 127:
                j += 1
            if j - i >= 3:
                runs.append((i, rom[i:j].decode("latin-1")))
            i = j
        else:
            i += 1
    ui = [(o, s) for o, s in runs if OFF_TEXT_BANK <= o < OFF_TEXT_BANK_END]
    print("printable runs >=3 in ROM:", len(runs))
    print("printable runs >=3 in UI bank:", len(ui))
    print("printable runs >=8 in UI bank:", sum(1 for _, s in ui if len(s) >= 8))
    for kw in ("password", "passwd", "cheat", "debug", "secret", "unlock",
               "hidden", "code", "sound test", "stage select", "level select",
               "continue", "bonus", "extra", "config", "setup", "test"):
        hits2 = [(o, s) for o, s in runs if kw in s.lower()]
        print("KW %-13s %d %s" % (kw, len(hits2),
                                  [(hex(o), s[:50]) for o, s in hits2[:4]]))

    print("\n== re-release (Design & Destroy) password probes ==")
    probes = [b"PASSWORD", b"ENTER BOT PASSWORD", b"ENTER TEAM PASSWORD",
              b"INVALID TEAM PASSWORD", b"BCDFGHJKLMNPQRSTVWXYZ-0123456789<>"]
    present = 0
    for p in probes:
        n = len(re.findall(re.escape(p), rom))
        present += n
        print("probe", p.decode(), "hits", n)

    print("\n== pointer tables (short ROM strings) ==")

    def s_at(v):
        if not (0x08000000 <= v < 0x0A000000):
            return None
        o = v - 0x08000000
        if o >= len(rom):
            return None
        e = o
        while e < len(rom) and e - o < 20 and 32 <= rom[e] < 127:
            e += 1
        s = rom[o:e]
        if len(s) < 3 or len(s) > 18:
            return None
        if not all(65 <= c <= 90 or 48 <= c <= 57 or
                   c in b" .,!?-*/=+:&$<>" for c in s):
            return None
        return s.decode()

    def table(off, maxn=40):
        out = []
        for k in range(maxn):
            s = s_at(struct.unpack_from("<I", rom, off + 4 * k)[0])
            if not s:
                break
            out.append(s)
        return out

    for name, off in [("robot short names (16)", 0x28619C),
                      ("robot long names (16)", 0x2861DC),
                      ("default team names", 0x26550),
                      ("default names A-D", 0x26564),
                      ("arena names (5)", 0x28A1EC),
                      ("options strings", 0x289FE8),
                      ("pit categories", 0x28B56C),
                      ("weight classes", 0x28BE38)]:
        print(name, hex(off), table(off))

    print("\n== input + screen dispatch ==")
    print("key poll (Thumb)", hex(0x08003208))
    print("key globals: held 0x03000194 pressed 0x03000196 released 0x03000198")
    print("main loop (Thumb)", hex(0x0800430C))
    print("state byte 0x030005AC, substate byte 0x030001A4")
    print("state table 0x08288420:",
          [hex(struct.unpack_from("<I", rom, 0x288420 + 4 * i)[0]) for i in range(6)])
    print("update table 0x08288390:",
          [hex(struct.unpack_from("<I", rom, 0x288390 + 4 * i)[0]) for i in range(18)])
    print("draw table 0x082883D8:",
          [hex(struct.unpack_from("<I", rom, 0x2883D8 + 4 * i)[0]) for i in range(18)])

    print("\n== name-entry alphabet (keyboard table) ==")
    off, end = 0x4244C, 0x4244C
    while rom[end] != 0:
        end += 1
    alpha = rom[off:end].decode("latin-1")
    print("alphabet", len(alpha), repr(alpha), "-> names of up to 8 chars;",
          "%d**8 = %.3e" % (len(alpha), len(alpha) ** 8))

    print("\n== SRAM ==")
    print("observed save image size 512 bytes; 3 slots at 0x000/0x090/0x120 "
          "(0x90 each): 8-byte name at +0, slot check word at +8, 0x5203 at +0x0E")
    print("configuration block at 0x1F0: B0 17 00 00 04 04 02 02 00 06 B0 0B B0 0B B0 0B")
    print("result: password-system probes present =", present,
          "(expected 0 for ABEE; BBDE has PASSWORD strings)")
    return 0 if present == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
