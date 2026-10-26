import re
P="/mnt/gbacheats/roms/All-Star Baseball 2004/All-Star Baseball 2004.gba"
rom=open(P,"rb").read()
words=["password","passcode","cheat","debug","secret","unlock","tweak","parameter","code","menu","invalid","select","test","extra team","legends","classic"]
print("== ASCII (case-insensitive) counts, substring over whole ROM")
for w in words:
    print(f"{w:14s}", len(re.findall(w.encode(),rom,re.I)))
print("== UTF-16LE counts")
for w in words:
    pat=b''.join(bytes([c,0]) for c in w.encode())
    print(f"{w:14s}", rom.count(pat))
print("== ASCII uppercase->lowercase shifted text: search for 'PASSWORD' as 0x61-based")
for w in ["password","cheat","debug","unlock"]:
    pat=bytes(c+0x20 if 0x41<=c<=0x5A else c for c in w.upper().encode())
    print(w, rom.count(pat))
# strings runs >=4
runs=re.findall(rb"[\x20-\x7e]{4,}",rom)
print("ASCII runs >=4:",len(runs))
kw={w:0 for w in words}
for r in runs:
    s=r.decode('latin1').lower()
    for w in words:
        if w in s: kw[w]+=1
print("runs containing keyword:",kw)
