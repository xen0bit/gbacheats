import struct
P = "/mnt/gbacheats/roms/All-Star Baseball 2004/All-Star Baseball 2004.gba"
rom = open(P, "rb").read()
logo = rom[0x04:0x04+156]
hits=[]; i=0
while True:
    i = rom.find(logo, i)
    if i<0: break
    hits.append(i); i+=1
print("156-byte logo hits:", [hex(h) for h in hits], "count", len(hits))
# complement variants
for name, f in [
  ("sub(b+1)", lambda: __import__('functools').reduce(lambda a,b: (a-b-1)&0xFF, rom[0xA0:0xBD], 0)),
  ("sub(b) - 0x19", lambda: (__import__('functools').reduce(lambda a,b:(a-b)&0xFF, rom[0xA0:0xBD],0) - 0x19) & 0xFF),
]:
    print(name, hex(f()))
print("stored", hex(rom[0xBD]))
