import struct, zlib, sys
src=sys.argv[1]; dst=sys.argv[2]; n=int(sys.argv[3]); extra=[int(x) for x in sys.argv[4:]]
d=open(src,"rb").read(); out=bytearray(d[:8]); i=8
while i<len(d):
    oln=struct.unpack(">I",d[i:i+4])[0]; typ=d[i+4:i+8]; data=d[i+8:i+8+oln]
    if typ==b'gbAs':
        raw=bytearray(zlib.decompress(data))
        base=0x19000 + (0x030004C4-0x03000000)
        for k in range(n): raw[base+k]=1
        for e in extra: raw[base+e]=1
        data=zlib.compress(bytes(raw),9)
    out += struct.pack(">I",len(data))+typ+data+struct.pack(">I",zlib.crc32(typ+data)&0xffffffff)
    i += 12+oln
open(dst,"wb").write(bytes(out)); print("ok")
