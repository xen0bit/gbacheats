#!/usr/bin/env python3
"""Static verification of the A Sound of Thunder password table.

Reads the code table and the {char *code; void (*apply)();} record table
directly from the ROM, and reimplements the validator at 0x08019680.
"""
import hashlib, struct, sys

ROM = "/mnt/gbacheats/roms/A Sound of Thunder/A Sound of Thunder.gba"
CODE_TABLE = 0x64970          # file offset == ROM addr - 0x08000000
REC_TABLE = 0x649C8
VALIDATOR = 0x08019680

rom = open(ROM, "rb").read()
print("rom:", ROM)
print("sha256:", hashlib.sha256(rom).hexdigest())


def u32(off):
    return struct.unpack_from("<I", rom, off)[0]


def cstr(addr):
    off = addr - 0x08000000
    return rom[off:rom.index(b"\0", off)].decode("ascii")


print("\ncode table @ file 0x%x (ROM 0x%x):" % (CODE_TABLE, 0x08000000 + CODE_TABLE))
for i in range(11):
    raw = rom[CODE_TABLE + i * 8:CODE_TABLE + i * 8 + 8]
    print("  [%2d] %-8s %s" % (i, raw[:6].decode(), raw.hex()))

print("\nrecord table @ file 0x%x:" % REC_TABLE)
recs = []
i = 0
while True:
    cp = u32(REC_TABLE + i * 8)
    if cp == 0:
        break
    fp = u32(REC_TABLE + i * 8 + 4)
    recs.append((cp, fp))
    print("  [%2d] code=0x%08x (%s)  apply=0x%08x" % (i, cp, cstr(cp), fp))
    i += 1
print("  terminator at file 0x%x" % (REC_TABLE + i * 8))

print("\nvalidator reimplementation (0x08019680): compare buf[0..5] to each entry")
def validate(buf):
    """buf: bytes, at least 6 bytes; no NUL termination required."""
    for idx, (cp, fp) in enumerate(recs):
        off = cp - 0x08000000
        if bytes(buf[:6]) == rom[off:off + 6]:
            return idx, fp
    return None

for code in ["BHRTYP", "LSKGHG", "LZDBVZ", "LBKVRG", "VWLFLG", "LZVKBD",
             "KBDBVL", "LVBRLG", "KJBLVB", "LKDSVB", "DCRDTS",
             "BHRTY", "BHRTYPP", "ZZZZZZ", "bhRtyp"]:
    r = validate(code.encode())
    print("  %-8s -> %s" % (code, "record %d, apply 0x%08x" % r if r else "rejected"))
