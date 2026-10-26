#!/usr/bin/env python3
"""Enumerate the trivia answer key without printing question/answer text.

Each record begins '@' + category letter + correct-button letter.
Usage: python3 trivia_key.py [path-to-rom]
"""
import os, re, sys
from collections import Counter

here = os.path.dirname(os.path.abspath(__file__))
rom_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "..", "Atari Anniversary Advance.gba")
rom = open(rom_path, "rb").read()

seg = rom[0xB468C:0xB6800].decode("latin1")
recs = re.findall(r"@([A-Z])([A-Z])", seg)
print("records:", len(recs))
print("categories:", dict(Counter(c for c, _ in recs)))
print("answer keys:", dict(Counter(k for _, k in recs)))
print()
print("index  offset-in-bank  category  correct-button")
pos = 0
for idx, m in enumerate(re.finditer(r"@([A-Z])([A-Z])", seg), 1):
    print(f"{idx:3d}    {m.start():#06x}         {m.group(1)}         {m.group(2)}")
