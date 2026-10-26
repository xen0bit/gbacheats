#!/usr/bin/env python3
"""Enter an A Sound of Thunder password with real controller input and verify
it through the emulator's memory.

This is the tool that produced the evidence in "A Sound of Thunder.md".

Requirements
------------
* mGBA signed with the ROM and started with `-g` (GDB stub). The SDL frontend
  hard-codes TCP 2345; if that port is busy, shim bind() to another port and
  pass `--port`.
* Xvfb + a window manager on DISPLAY (default :104), and xdotool/ImageMagick.
* The emulator must be past the title screen on the Password screen. A
  savestate (`-t file.ss1`) makes this repeatable.

Usage
-----
    python3 asot_type_code.py BHRTYP                # type, verify, screenshot
    python3 asot_type_code.py BHRTYP --level2       # then start level 2
    ASOT_SHOTS=/tmp/shots python3 asot_type_code.py DCRDTS

What it verifies
----------------
* after each letter, the byte actually stored at 0x03007630 (not what the
  screen seems to show);
* the cursor variables 0x03003D08 (row) / 0x03003D04 (column), so navigation
  never relies on guessing;
* the level-unlock array 0x03001B34 and the ending variables 0x03006B14/B18.
"""
import argparse
import os
import socket
import struct
import subprocess
import sys
import time

DISPLAY = os.environ.get("ASOT_DISPLAY", ":104")
SHOTS = os.environ.get("ASOT_SHOTS", os.path.dirname(os.path.abspath(__file__)))
ENV = {**os.environ, "DISPLAY": DISPLAY}
KEYS = {"a": "x", "b": "z", "up": "Up", "down": "Down",
        "left": "Left", "right": "Right"}

BUF = 0x03007630          # six space-padded input bytes
CUR_COL = 0x03003D04      # cursor column, 0..6
CUR_ROW = 0x03003D08      # cursor row, 0..2
FLAG_IDX = 0x03001B30     # last applied record index
FLAG_ARR = 0x03001B34     # 11-word level unlock array
END_MODE = 0x03006B14     # mode/level word
END_FLAG = 0x03006B18     # ending request byte

GRID = ["BCDFGHJ", "KLMNPQR", "STVWXYZ"]


# --------------------------------------------------------------------------
# minimal GDB-RSP client (mGBA stub: max 256-byte reads, 'c' has no reply)
# --------------------------------------------------------------------------
class RSP:
    def __init__(self, port, timeout=6.0):
        self.s = socket.create_connection(("127.0.0.1", port), timeout=timeout)

    def _packet(self, timeout=6.0):
        self.s.settimeout(timeout)
        while True:
            b = self.s.recv(1)
            if not b:
                raise EOFError
            if b == b"$":
                break
        data = b""
        while True:
            b = self.s.recv(1)
            if b == b"#":
                break
            data += b
        csum = self.s.recv(2)
        self.s.sendall(b"+")
        if csum.decode() != "%02x" % (sum(data) & 0xFF):
            raise RuntimeError("checksum mismatch: %s" % csum)
        return data.decode("latin1")

    def cmd(self, payload, timeout=6.0):
        pkt = "$" + payload + "#%02x" % (sum(payload.encode()) & 0xFF)
        self.s.sendall(pkt.encode())
        return self._packet(timeout)

    def read(self, addr, n):
        out = b""
        while n:
            chunk = min(n, 0x100)
            r = self.cmd("m%x,%x" % (addr, chunk))
            if r.startswith("E"):
                raise RuntimeError("read failed: %s" % r)
            b = bytes.fromhex(r)
            out += b
            addr += len(b)
            n -= len(b)
        return out

    def halt(self, timeout=2.0):
        self.s.sendall(b"\x03")
        try:
            while True:
                p = self._packet(timeout)
                if p[:1] in ("S", "T", "W", "X"):
                    return p
        except socket.timeout:
            return "already"

    def resume(self):
        p = "c"
        self.s.sendall(("$" + p + "#%02x" % (sum(p.encode()) & 0xFF)).encode())
        time.sleep(0.05)

    def close(self):
        try:
            self.s.sendall(b"$D#44")
        except Exception:
            pass
        self.s.close()


# --------------------------------------------------------------------------
# input helpers
# --------------------------------------------------------------------------
def window():
    out = subprocess.run(["xdotool", "search", "--name", "mGBA"], env=ENV,
                         capture_output=True, text=True).stdout.split()
    if not out:
        raise SystemExit("no mGBA window on DISPLAY=%s" % DISPLAY)
    return out[0]


def taps(names, hold=0.06, gap=0.30):
    subprocess.run(["xdotool", "windowfocus", window()], env=ENV)
    for n in names:
        k = KEYS[n]
        subprocess.run(["xdotool", "keydown", k], env=ENV, check=True)
        time.sleep(hold)
        subprocess.run(["xdotool", "keyup", k], env=ENV, check=True)
        time.sleep(gap)


def shot(name):
    os.makedirs(SHOTS, exist_ok=True)
    path = os.path.join(SHOTS, name)
    subprocess.run(["import", "-window", window(), path], env=ENV, check=True)
    return path


def state(c):
    c.halt()
    cur = c.read(CUR_COL, 8)
    return dict(
        col=cur[0], row=cur[4], buf=c.read(BUF, 6),
        idx=struct.unpack("<I", c.read(FLAG_IDX, 4))[0],
        arr=struct.unpack("<11I", c.read(FLAG_ARR, 44)),
        end_mode=struct.unpack("<I", c.read(END_MODE, 4))[0],
        end_flag=c.read(END_FLAG, 1)[0],
    )


def cell(ch):
    for r, line in enumerate(GRID):
        if ch in line:
            return r, line.index(ch)
    raise KeyError("%r is not on the password grid" % ch)


def goto(c, row, col):
    for _ in range(12):
        s = state(c)
        if s["row"] == row and s["col"] == col:
            return
        if s["row"] < row:
            seq = ["down"] * (row - s["row"])
        elif s["row"] > row:
            seq = ["up"] * (s["row"] - row)
        elif s["col"] < col:
            seq = ["right"] * (col - s["col"])
        else:
            seq = ["left"] * (s["col"] - col)
        c.resume()
        taps(seq)
        time.sleep(0.25)
    raise RuntimeError("could not reach cell row=%d col=%d" % (row, col))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("code")
    ap.add_argument("--port", type=int, default=2471)
    ap.add_argument("--level2", action="store_true",
                    help="after acceptance, start level 2 from Level Select")
    args = ap.parse_args()

    if len(args.code) != 6:
        raise SystemExit("a password is exactly 6 letters")

    c = RSP(args.port)
    s = state(c)
    print("pre: cursor=(%d,%d) buf=%r idx=%d arr=%s end=%02x/%d" %
          (s["row"], s["col"], s["buf"], s["idx"], list(s["arr"]),
           s["end_flag"], s["end_mode"]))

    typed = ""
    for ch in args.code:
        row, col = cell(ch)
        goto(c, row, col)
        c.resume()
        taps(["a"])
        time.sleep(0.35)
        s = state(c)
        got = chr(s["buf"][len(typed)]) if len(s["buf"]) > len(typed) else "?"
        print("  %s -> cell(%d,%d) buf=%r slot=%r idx=%d" %
              (ch, row, col, s["buf"], got, s["idx"]))
        if got != ch:
            raise SystemExit("stored %r, expected %r; aborting" % (got, ch))
        typed += ch

    print("after 6: buf=%r idx=%d arr=%s end=%02x/%d" %
          (s["buf"], s["idx"], list(s["arr"]), s["end_flag"], s["end_mode"]))
    for i in range(4):
        c.resume()
        time.sleep(1.0)
        s = state(c)
        print("t=%ds cursor=(%d,%d) buf=%r idx=%d arr=%s end=%02x/%d" %
              (i + 1, s["row"], s["col"], s["buf"], s["idx"],
               list(s["arr"]), s["end_flag"], s["end_mode"]))
        print("  shot:", shot("%s_t%d.png" % (args.code, i + 1)))

    if args.level2:
        c.resume(); taps(["a"]); time.sleep(2.0); c.halt()
        print("  shot:", shot("single_player.png"))
        c.resume(); taps(["down", "a"]); time.sleep(2.0); c.halt()
        print("  shot:", shot("level_select.png"))
        c.resume(); taps(["right"]); time.sleep(0.8); c.halt()
        print("  shot:", shot("level2_selected.png"))
        c.resume(); taps(["a"]); time.sleep(2.5); c.halt()
        print("  shot:", shot("level2_start.png"))
        c.resume(); time.sleep(3.0); c.halt()
        print("  shot:", shot("level2_gameplay.png"))
        s = state(c)
        print("level2: arr=%s end=%02x/%d" %
              (list(s["arr"]), s["end_flag"], s["end_mode"]))

    c.close()


if __name__ == "__main__":
    main()
