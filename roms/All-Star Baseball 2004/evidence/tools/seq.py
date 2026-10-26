import subprocess,os,time,sys
D=":133"; e={**os.environ,"DISPLAY":D}
W=subprocess.check_output(["xdotool","search","--name","mGBA"],env=e).decode().split()[0]
subprocess.run(["xdotool","windowfocus",W],env=e)
def key(k,hold=0.16,gap=0.18):
    subprocess.run(["xdotool","keydown",k],env=e); time.sleep(hold)
    subprocess.run(["xdotool","keyup",k],env=e); time.sleep(gap)
def shot(n):
    subprocess.run(["import","-window",W,n],env=e)
seq=sys.argv[1].split(",")
for s in seq:
    if s.startswith("shot="): shot(s[5:])
    elif s.startswith("sleep="): time.sleep(float(s[6:]))
    elif s.startswith("rep="):
        n,_,k=s[4:].partition(":"); [key(k) for _ in range(int(n))]
    else: key(s)
