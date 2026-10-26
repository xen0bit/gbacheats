import struct
P="/mnt/gbacheats/roms/All-Star Baseball 2004/All-Star Baseball 2004.gba"
rom=open(P,"rb").read(); BASE=0x08000000
valid={1,2,4,8,0x10,0x20,0x40,0x80,0x100,0x200}
runs=[]
i=0
while i < len(rom)-2*5:
    vals=[];j=i
    while j<len(rom)-1 and len(vals)<64:
        v=struct.unpack_from("<H",rom,j)[0]
        if v not in valid: break
        vals.append(v);j+=2
    if len(vals)>=5:
        runs.append((i,vals)); i=j
    else: i+=2
print("runs>=5",len(runs))
found=0
for off,vals in runs:
    a=BASE+off
    hits=[]
    for cand in (a,a|1):
        n=struct.pack("<I",cand); k=0
        while True:
            k=rom.find(n,k)
            if k<0: break
            hits.append(k); k+=1
    if hits:
        found+=1
        print(hex(off), [hex(v) for v in vals][:12], "ptr at", [hex(h) for h in hits][:6])
print("referenced runs",found)
