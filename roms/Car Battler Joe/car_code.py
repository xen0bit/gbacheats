#!/usr/bin/env python3
"""Car Battler Joe (GBA) custom-machine code encoder/decoder.

Reconstructed from the ROM (SHA-256 e9d2ea68...) at:
  encoder 0x08020F98, decoder 0x080210E0,
  alphabet 0x083BDFF8, char map 0x083B5894,
  preset table 0x083BDD78, body table 0x083B04D8.

Payload: five 7-bit fields packed into seven 5-bit symbols,
plus one 5-bit checksum symbol.

    field 0      body index, 0..67
    fields 1-4   part/stat words, 0..76
                 (encoder stores n-1 for n>0; decoder restores n+1;
                  therefore 0 and 1 encode identically)

Usage:
    python3 car_code.py encode 0 0 0 0 0        # -> 11111118
    python3 car_code.py encode 67 76 0 0 0
    python3 car_code.py decode 11111118
"""
import sys

ALPHABET = "1234KLMN5678PQRS9BCDTVWXFGHJYZ!?"
PRESETS = {  # the 20 fixed secret-machine passwords
    "BOM!BOM!": "WNN Special", "TK000056": "Takah's LSR",
    "MARRON!!": "MRIN's Dream", "KINNIKU!": "MSSL Dolly",
    "MR!HURRY": "Matsu K MK4", "90!60!92": "Millennium 90",
    "8998981!": "Issue X", "HAMA!333": "Big Bang",
    "CUREWAND": "Cavalier", "GO!HOME!": "Piston GH",
    "M!M!M!M!": "Mega M", "CDMACAPA": "Copa Zone 23",
    "GANKOMAX": "MAX-K", "NAGOYADB": "Long Valley Z",
    "!KOKICHI": "Casey's WHLS", "TODOROKI": "Jim Joe Zero",
    "RED!GUNS": "Solid Wind", "SHISYO!!": "Blue Gate EV",
    "GUARANT!": "Queen Dohmo", "EMPIRE!!": "EMP Force X",
}


def checksum(symbols):
    """5-bit check over the first six symbols (init 11, add/xor alternation)."""
    ck = 11
    for i, v in enumerate(symbols[:6]):
        ck = (ck ^ v) if (i & 1) else ((ck + v) & 0xFF)
    return ck & 0x1F


def encode(body, f1=0, f2=0, f3=0, f4=0):
    if not 0 <= body <= 67:
        raise ValueError("body index must be 0..67")
    fields = [body] + [0 if v == 0 else v - 1 for v in (f1, f2, f3, f4)]
    if any(v < 0 or v > 0x7F for v in fields):
        raise ValueError("field out of 7-bit range")
    bits = 0
    for i, v in enumerate(fields):
        bits |= (v & 0x7F) << (7 * i)
    symbols = [(bits >> (5 * k)) & 0x1F for k in range(7)]
    symbols.append(checksum(symbols))
    return "".join(ALPHABET[s] for s in symbols)


def decode(code):
    if code in PRESETS:
        return {"preset": PRESETS[code]}
    if len(code) != 8 or any(c not in ALPHABET for c in code):
        return None
    symbols = [ALPHABET.index(c) for c in code]
    if checksum(symbols) != symbols[7]:
        return None
    bits = 0
    for k in range(7):
        bits |= symbols[k] << (5 * k)
    fields = [(bits >> (7 * i)) & 0x7F for i in range(5)]
    if fields[0] >= 68 or any(f > 75 for f in fields[1:]):
        return None
    return {
        "body": fields[0],
        "parts": [0 if f == 0 else f + 1 for f in fields[1:]],
    }


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    cmd, args = sys.argv[1], sys.argv[2:]
    if cmd == "encode":
        nums = [int(a, 0) for a in args]
        code = encode(*nums)
        print(code, "->", decode(code))
    elif cmd == "decode":
        print(decode(args[0]))
    else:
        raise SystemExit("unknown command; use encode/decode")
