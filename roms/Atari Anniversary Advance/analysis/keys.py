#!/usr/bin/env python3
import subprocess, time, sys
D=":147"
def key(name, hold=0.18, gap=0.20):
    env={"DISPLAY":D}
    subprocess.run(["xdotool","keydown",name],env=env,check=True)
    time.sleep(hold)
    subprocess.run(["xdotool","keyup",name],env=env,check=True)
    time.sleep(gap)
if __name__=="__main__":
    for a in sys.argv[1:]:
        key(a)
