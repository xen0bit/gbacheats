import unicorn
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE
from unicorn.arm_const import *

ROM="/mnt/gbacheats/roms/Blades of Thunder/Blades of Thunder.gba"
data=open(ROM,"rb").read()
FUNC=0x080174f0
SENT=0x03007000

uc=Uc(UC_ARCH_ARM, UC_MODE_ARM)
uc.mem_map(0x08000000, 0x800000)
uc.mem_write(0x08000000, data)
uc.mem_map(0x02000000, 0x40000)
uc.mem_map(0x03000000, 0x8000)
uc.reg_write(UC_ARM_REG_SP, 0x03007f00)

steps=[0]
def hook(uc,addr,size,user):
    steps[0]+=1
    if addr==SENT:
        uc.emu_stop()
uc.hook_add(UC_HOOK_CODE, hook)

def run(code4):
    steps[0]=0
    uc.mem_write(0x03005e48, b"\x00\x00\x00\x00")
    uc.mem_write(0x03005e50, code4.encode())
    uc.mem_write(0x030058e4, b"\x00\x00\x00\x00")
    uc.reg_write(UC_ARM_REG_SP, 0x03007f00)
    uc.reg_write(UC_ARM_REG_LR, SENT)
    uc.reg_write(UC_ARM_REG_R0, 0)
    try:
        uc.emu_start(FUNC, SENT, count=500)
    except unicorn.UcError as e:
        return ("ERR",str(e),steps[0])
    r0=uc.reg_read(UC_ARM_REG_R0)
    if r0>=0x80000000: r0-=0x100000000
    return r0, bytes(uc.mem_read(0x03005e48,8)), bytes(uc.mem_read(0x030058e4,4)), steps[0]

if __name__=="__main__":
    res={}
    for i in range(10000):
        c="%04d"%i
        r=run(c)
        if r[0]==1:
            res[c]=r
    print("accepted",len(res))
    for k in sorted(res):
        v=res[k]
        print(k, v[0], v[1].hex(' '), v[2].hex(' '), "steps",v[3])
