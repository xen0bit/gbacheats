import struct
P="/mnt/gbacheats/roms/All-Star Baseball 2004/All-Star Baseball 2004.gba"
rom=open(P,"rb").read()
NAME_T=0x797df8; HAND_T=0x797f84
names=[]
for i in range(84):
    p=struct.unpack_from("<I",rom,NAME_T+4*i)[0]
    if p==0: names.append(None); continue
    off=p-0x08000000
    e=rom.find(b"\0",off)
    names.append(rom[off:e].decode())
print("names",len(names),names[0],names[-1])
hand=[]
for i in range(84):
    v=struct.unpack_from("<I",rom,HAND_T+4*i)[0]
    hand.append(v)
print("handlers:")
for i,(n,h) in enumerate(zip(names,hand)):
    print(i, n, hex(h) if h else "NULL")
