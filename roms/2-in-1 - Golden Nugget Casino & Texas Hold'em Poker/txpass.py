#!/usr/bin/env python3
"""Texas Hold'em Poker (GBA, image B) 18-character career password codec.

Format (derived from the decoder at 0x084174B8 and validator at 0x08417768):
  direct[0:5]   chips, 5 base-36 digits, little-endian
  direct[5]     tournament index (0..4)
  direct[6:17]  name field, 11 characters: alphabet[len(name)] + name + 'A' padding
  direct[17]    checksum = sum(ASCII of direct[0:17]) mod 36
  entered[i]    = alphabet[(index(direct[i]) - 3 - i) mod 36]
Alphabet: ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 (A=0 ... Z=25, 0=26 ... 9=35)
The screen draws A,E,I,O,U as up/right/down/blank/left glyphs; the stored
characters are plain ASCII letters.
"""
AL = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
TOURNAMENTS = ["RIVERBOAT", "LAKE TAHOE", "RENO", "ATLANTIC CITY", "LAS VEGAS"]

def _val(c):
    return AL.index(c)

def direct_decode(code18):
    """Entered code -> 18 direct alphabet digits (undo positional shift)."""
    code18 = code18.replace("<", "U").replace("^", "A").replace("v", "I").replace(">", "E").replace("#", "O")
    if len(code18) != 18:
        raise ValueError("need 18 chars")
    return "".join(AL[(_val(c) + 3 + i) % 36] for i, c in enumerate(code18))

def direct_encode(direct18):
    """18 direct alphabet digits -> entered code."""
    if len(direct18) != 18:
        raise ValueError("need 18 digits")
    return "".join(AL[(_val(c) - 3 - i) % 36] for i, c in enumerate(direct18))

def decode(code18):
    d = direct_decode(code18)
    chips = sum(_val(d[i]) * 36**i for i in range(5))
    tour = _val(d[5])
    nlen = _val(d[6])
    name = d[7:7+nlen]
    check = _val(d[17])
    ok = (sum(d[:17].encode()) % 36) == check
    return {"code": code18, "direct": d, "chips": chips, "tournament": tour,
            "tournament_name": TOURNAMENTS[tour] if 0 <= tour < len(TOURNAMENTS) else None,
            "name": name, "checksum_ok": ok}

def encode(chips, tournament, name):
    if not (0 <= chips < 36**5):
        raise ValueError("chips out of range (0..60466175)")
    if not (0 <= tournament < 5):
        raise ValueError("tournament out of range (0..4)")
    if len(name) > 10:
        raise ValueError("name too long (max 10)")
    digits = []
    v = chips
    for _ in range(5):
        digits.append(AL[v % 36]); v //= 36
    digits.append(AL[tournament])
    field = AL[len(name)] + name + "A" * (10 - len(name))
    digits.append(field)
    d = "".join(digits)
    check = sum(d.encode()) % 36
    d += AL[check]
    return direct_encode(d)

if __name__ == "__main__":
    import sys
    published = [
        ("VB64338F^YL0CLTSR0", "Lake Tahoe tournament"),
        ("D4B4348F^YL0CLTSR^", "Reno tournament"),
        ("7<^5358F^YL0CLTSR2", "Atlantic City tournament"),
        ("763^368F^YL0CLTSR6", "Las Vegas tournament"),
        ("HP64335F668WV<TSRJ", "Phil, Lake Tahoe"),
        ("XDC4345F668WV<TSRN", "Phil, Reno"),
        ("7<^5355F668WV<TSRL", "Phil, Atlantic City"),
        ("763^365F668WV<TSRP", "Phil, Las Vegas"),
    ]
    for code, label in published:
        info = decode(code)
        print(f"{label:28s} {code}  chips={info['chips']:6d} tour={info['tournament']} "
              f"name={info['name']!r} check={info['checksum_ok']}")
    # round-trip from the decoded state
    print("\nre-encode check (glyphs < and ^ normalised to U and A):")
    norm = lambda c: c.replace("<", "U").replace("^", "A")
    for code, label in published:
        i = decode(code)
        re = encode(i["chips"], i["tournament"], i["name"])
        ok = norm(re) == norm(code)
        print(f"  {label:28s} {re}  {'OK' if ok else 'MISMATCH'}")
