import struct, json
P = "/mnt/gbacheats/roms/All-Star Baseball 2004/All-Star Baseball 2004.gba"
rom = open(P,"rb").read()
T=0x1fc6bc
verb, size, z, count = struct.unpack_from("<IIII", rom, T+4)
base = T + 0x14 + count*4
print("TDBB ver",verb,"size",size,"count",count,"strbase",hex(base),rom[base:base+12])
strs={}
for k in range(count):
    sid, o = struct.unpack_from("<HH", rom, T+0x14+4*k)
    p = base+o
    e = rom.find(b"\x00", p)
    strs[sid]=rom[p:e].decode("latin1")
print("ids", min(strs), max(strs), "n", len(strs))
for sid in sorted(strs):
    s=strs[sid]
    if any(w in s for w in ["Tweak","Parameter","Debug","Test","nlock","Extra","assword","heat","ecret","Code","All Your","tadium","Team"]):
        print(sid, repr(s))
json.dump(strs, open("/tmp/opencode/asb2004/tdb.json","w"), indent=0)
