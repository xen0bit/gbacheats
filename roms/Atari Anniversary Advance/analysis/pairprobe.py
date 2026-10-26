import subprocess,time,itertools,sys,os
D=":147"
keys=["x","z","a","s","Return","BackSpace","Up","Down","Left","Right"]
def load(slot):
    subprocess.run(["xdotool","key",f"F{slot}"],env={"DISPLAY":D});time.sleep(1.2)
def press2(k1,k2):
    env={"DISPLAY":D}
    subprocess.run(["xdotool","keydown",k1],env=env);time.sleep(0.08)
    subprocess.run(["xdotool","keydown",k2],env=env);time.sleep(0.22)
    subprocess.run(["xdotool","keyup",k2],env=env);subprocess.run(["xdotool","keyup",k1],env=env)
    time.sleep(0.9)
def ocr():
    subprocess.run(["scrot","-o","pp.png"],env={"DISPLAY":D})
    subprocess.run(["convert","pp.png","-crop","720x480+154+184","+repage","ppc.png"])
    subprocess.run(["convert","ppc.png","-crop","720x60+0+0","+repage","pph.png"])
    return " ".join(subprocess.run(["tesseract","pph.png","stdout","--psm","6"],capture_output=True,text=True).stdout.split())
slot=sys.argv[1]
for k1,k2 in itertools.combinations(keys,2):
    load(slot)
    press2(k1,k2)
    t=ocr()
    print(f"{k1}+{k2}: {t[:90]}",flush=True)
