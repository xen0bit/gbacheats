#!/usr/bin/env python3
"""Print the six option blocks and their !N value counts.

Usage: python3 parse_options.py [path-to-rom]
Default path is ../Atari Anniversary Advance.gba relative to this file.
"""
import os, re, sys

here = os.path.dirname(os.path.abspath(__file__))
rom_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "..", "Atari Anniversary Advance.gba")
rom = open(rom_path, "rb").read()
seg = rom[0xB3F38:0xB468C].decode("latin1")

# Blocks are separated by '@'; blocks start with a !N field.
blocks = [b for b in seg.split("@") if b.strip()]
print("blocks:", len(blocks))
for bi, block in enumerate(blocks, 1):
    fields = re.split(r"!(\d)", block)
    counts = []
    for i in range(1, len(fields), 2):
        counts.append(int(fields[i]))
    # Drop the trailing !1 padding fields from the summary.
    real = [c for c in counts if c > 1]
    prod = 1
    for c in real:
        prod *= c
    print(f"block {bi}: value-counts {counts} -> {prod} combinations")
