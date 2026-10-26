import subprocess, time, sys, os

DISP = ":127"
env = dict(os.environ, DISPLAY=DISP)

def sh(*a):
    return subprocess.run(a, env=env, capture_output=True, text=True)

def focus():
    out = sh("xdotool", "search", "--name", "mGBA").stdout.split()
    if out:
        sh("xdotool", "windowfocus", out[-1])
        sh("xdotool", "windowactivate", out[-1])
    return out

def key(name, hold=0.20, gap=0.25):
    focus()
    sh("xdotool", "keydown", name)
    time.sleep(hold)
    sh("xdotool", "keyup", name)
    time.sleep(gap)

def keys(seq, hold=0.20, gap=0.25):
    for k in seq:
        key(k, hold, gap)

def shot(path):
    sh("import", "-window", "root", path)
    g = path.replace("s_", "g_")
    if g == path:
        g = path
    subprocess.run(["convert", path, "-crop", "720x480+152+144", "+repage", g], env=env)

if __name__ == "__main__":
    for a in sys.argv[1:]:
        key(a)
