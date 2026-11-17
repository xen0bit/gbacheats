#!/usr/bin/env python3
"""Type a 6-char code on the Drome Racers GBA 'Enter Code' on-screen keyboard.
Grid:
 row0: A B C D E F G H I J K L M   (cols 0..12)
 row1: N O P Q R S T U V W X Y Z   (cols 0..12)
 row2: 0 1 2 3 4 5 6 7 8 9 ! "    (cols 0..11)
"""
import subprocess, time, sys

ROW0 = "ABCDEFGHIJKLM"
ROW1 = "NOPQRSTUVWXYZ"
ROW2 = '0123456789!"'
ROWS = [ROW0, ROW1, ROW2]

def pos(ch):
    for r, row in enumerate(ROWS):
        if ch in row:
            return r, row.index(ch)
    raise ValueError(ch)

def key(name, hold=0.07, gap=0.13):
    subprocess.run(["xdotool", "keydown", name], check=True)
    time.sleep(hold)
    subprocess.run(["xdotool", "keyup", name], check=True)
    time.sleep(gap)

def type_code(code, do_submit=True, reload_state=True):
    code = code.upper()
    assert len(code) == 6, code
    if reload_state:
        key("F1", 0.10, 0.7)   # load savestate slot 1 = empty code screen
    cur = (0, 0)  # keyboard cursor starts on 'A'
    for ch in code:
        tr, tc = pos(ch)
        # move vertically first (row0<->row1 same columns; row1->row2 clamp col)
        while cur[0] < tr:
            if cur[0] == 1 and tc > 11:  # row2 has only 12 cols
                # move down then left to target col
                key("Down"); cur = (2, cur[1])
                while cur[1] > tc:
                    key("Left"); cur = (2, cur[1]-1)
                break
            key("Down"); cur = (cur[0]+1, cur[1])
        while cur[0] > tr:
            key("Up"); cur = (cur[0]-1, cur[1])
        while cur[1] < tc:
            key("Right"); cur = (cur[0], cur[1]+1)
        while cur[1] > tc:
            key("Left"); cur = (cur[0], cur[1]-1)
        assert cur == (tr, tc), (cur, (tr, tc), ch)
        key("x")  # GBA A button = add char
    if do_submit:
        key("x")  # focus auto-moved to OK; press A to submit
    return cur

if __name__ == "__main__":
    code = sys.argv[1]
    submit = "--no-submit" not in sys.argv
    reloadst = "--no-reload" not in sys.argv
    print("typing", code, "submit", submit, "reload", reloadst)
    type_code(code, submit, reloadst)
    print("done")
