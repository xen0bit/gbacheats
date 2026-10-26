import struct, zlib, sys
p=sys.argv[1]
d=open(p,"rb").read()
print(d[:8])
i=8; chunks=[]
while i<len(d):
    ln=struct.unpack(">I",d[i:i+4])[0]; typ=d[i+4:i+8].decode('latin1'); data=d[i+8:i+8+ln]
    chunks.append((typ,ln,data)); i+=8+ln+4
for t,l,_ in chunks: print(t,l)
for t,l,data in chunks:
    if t=='gbAs':
        raw=zlib.decompress(data)
        print("state len",len(raw))
        open(p+".raw","wb").write(raw)
