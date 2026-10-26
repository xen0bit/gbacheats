import struct, hashlib, sys

P = "/mnt/gbacheats/roms/All-Star Baseball 2004/All-Star Baseball 2004.gba"
rom = open(P, "rb").read()

print("size", len(rom), hex(len(rom)))
print("md5", hashlib.md5(rom).hexdigest())
print("sha1", hashlib.sha1(rom).hexdigest())
print("sha256", hashlib.sha256(rom).hexdigest())
title = rom[0xA0:0xAC].decode("ascii", "replace").rstrip("\0 ")
game_code = rom[0xAC:0xB0].decode("ascii", "replace")
maker = rom[0xB0:0xB2].decode("ascii", "replace")
version = rom[0xBC]
print("title", repr(title), "code", game_code, "maker", maker, "ver", version)
print("entry", hex(struct.unpack_from("<I", rom, 0)[0]))
print("fixed 0x96", hex(rom[0xB2]), "unit", rom[0xB3], "dev", rom[0xB4])
# complement check
chk = 0
for b in rom[0xA0:0xBD]:
    chk = (chk - b - 1) & 0xFF
print("complement stored", hex(rom[0xBD]), "computed", hex(chk), "ok", chk == rom[0xBD])
print("header checksum stored", hex(struct.unpack_from("<H", rom, 0xBE)[0]))

# Embedded GBA header scan: Nintendo logo is at header offset 4, 156 bytes
logo = bytes.fromhex("24ffae51699aa2213d84820a84e409ad11248b98c0817f21a352be199309ce20"
                     "10464a4af82731ec58c7e83382e3cebf85f4df94ce4b09c194568ac0")
print("logo len", len(logo))
hits = []
i = 0
while True:
    i = rom.find(logo, i)
    if i < 0:
        break
    hits.append(i)
    i += 1
print("logo hits(file offsets):", [hex(h) for h in hits])
for h in hits:
    base = h - 4
    t = rom[base + 0xA0: base + 0xAC].decode("ascii", "replace")
    gc = rom[base + 0xAC: base + 0xB0].decode("ascii", "replace")
    print("  header at", hex(base), "title", repr(t), "code", gc, "entry", hex(struct.unpack_from("<I", rom, base)[0]))

# LZ77 header census (0x10, size24)
lz = 0
runs = []
i = 0
while i < len(rom) - 4:
    if rom[i] == 0x10:
        sz = rom[i+1] | (rom[i+2] << 8) | (rom[i+3] << 16)
        if 0x20 < sz < 0x40000 and sz % 1 == 0:
            lz += 1
            i += 4
            continue
    i += 1
print("lz77-ish headers", lz)

# high-entropy check: count 0xFF runs etc
print("nonFF bytes", len(rom) - rom.count(0xFF))
