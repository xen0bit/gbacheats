# Kong: King of Atlantis (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Kong: King of Atlantis.gba`, 4,194,304 bytes (4 MiB) |
| `file(1)` | `Game Boy Advance ROM image: "KONG:KOA" (BK7E5G, Rev.00)` |
| Header title / code / maker | `KONG:KOA` / `BK7E` / `5G` (serial AGB-BK7E-USA, rev 0) |
| Entry word | `0xEA00002E` → `0x080000C0` (stock crt0) |
| MD5 | `d3100683634506761d3412b728617307` |
| SHA-1 | `e490a1a0954d349f54c60e18c66c32977c6c6e30` |
| SHA-256 | `afd0b2c5e5c719143ced1d32e6ed8583d1b53fea9aa242e562b78d942fad8f61` |

Phase 0: exactly **one** Nintendo-logo hit (file `0x04`, header `0x0`); no appended
second image, trainer, cracktro, or patch stub. Header checksum is `0x0000` and
the complement byte is `0x88` (recomputed from bytes `0xA0`–`0xBC` it should be
`0xA1`), so the header was normalized/rebuilt at some point; the logo, fixed
`0x96` and stock entry branch are intact. CRC32 `5E8B2644` matches the USA SKU
listed at GameHacking.org.

## 2. Executive summary

The developer-intended cheat surface is a **7-letter password system** on the
in-game PASSWORD screen; there is no need for, and no scope here for,
GameShark/CodeBreaker memory codes. The on-screen keyboard shows 17 letters
(A–Q) but only eight letter codes (`1`–`8`: **B D F G J L M P**) can pass the
validator. All 14 codes published at GameFAQs-derived lists, GameGenie,
SuperCheats, VictoryCheats, CheatsCorner and mariogba.nl are present in the ROM
and accepted by the reversed validator.

The accepted space is **1,792 codes** out of `8^7 = 2,097,152` representable
strings — not the 882 published by the well-known Ghidra/PCode blog, which
brute-forced only seven of the eight symbols and therefore missed every code
containing **P**. The decoder maps accepted codes onto 15 level codes and 9
starting-lives values (120 distinct effects).

A novel code, **`PBBDJLP`**, absent from every published list (it uses `P`,
which no published enumeration covers), was entered on the real screen and
produced level code `1` (= published "1-2") with **9 lives**, where the
published code for the same level, `FJLJBDG`, gives 6 lives. Bounds were proven
by in-game rejection of an out-of-range letter (`ABBBBBB`, A = 0x0A > 8) and a
bad-checksum all-B code (`BBBBBBB`); both showed "WRONG PASSWORD" and left the
level/lives RAM at zero.

A 5-entry developer MAIN MENU table containing a **Level Select** item exists
at `0x0836FD70` with handler pointers, but the shipping title menu is a
4-item ring (New Game / Password / Options / Credits); the 5th entry was not
reachable from any walked screen or tested button combination.

## 3. How to reproduce

* mGBA (SDL) under `Xvfb :317`, `SDL_AUDIODRIVER=dummy`, `-3` scale.
  Keymap: A = `x`, B = `z`, L = `a`, R = `s`, Start = `Return`,
  Select = `BackSpace`, D-pad = arrow keys.
  **Do not send input until the ~15 s intro has finished.**
* Title → Down once → `PASSWORD` → A. Grid (clamped, *not* wrapping):
  `A B C D E F` / `G H I J K L` / `M N O P Q ←`. Select seven letters with A;
  the game parses automatically on the seventh.
* Savestates: `Shift+F1`…`Shift+F9` save, `F1`…`F9` load. To read RAM without a
  GDB stub (this mGBA build's stub returns malformed packets), parse the `.ssN`
  PNG, `zlib.decompress` the `gbAs` chunk, and use IWRAM base `0x19000`:

  | Game address | State offset | Meaning |
  |---|---:|---|
  | `0x030027E0` | `0x1B7E0` | 7 password input codes |
  | `0x030027DC` | `0x1B7DC` | decoded level code (0–14) |
  | `0x030020A2` | `0x1B0A2` | decoded starting lives |
  | `0x03004650/51` | `0x1D650` | keyboard cursor X/Y |

* Codes exercised: `FJLJBDG` (published), `PBBDJLP` (novel),
  `BBBBBBB` + `ABBBBBB` (rejected).

## 4. Address map

| Address | Type | Role |
|---|---|---|
| `0x082CA72E` | Thumb fn | password screen handler (`FUN_082ca72e`); writes input codes, auto-submits at length 7 |
| `0x082CAAFA` | BL | call to validator |
| `0x082CC970` | Thumb fn | **validator** `check_password_1` (7 byte args, returns 0/1) |
| `0x82CCC2A`–`0x82CCC8E` | code | bucket assignment loop + validity checks |
| `0x082CCCBC` | Thumb fn | **decoder** `password_check`; writes level/lives to IWRAM |
| `0x082CB2C1` | Thumb fn | Level Select menu handler (in unreachable 5-item table) |
| `0x0836FD70`–`0x0836FE58` | data | 5 × 0x28-byte MAIN MENU records (`text[32]`, id `0x0E`–`0x12`, handler u32) |
| `0x030027E0` | IWRAM | password buffer (7 bytes) |
| `0x030027DC` | IWRAM | decoded level code |
| `0x030020A2` | IWRAM | decoded starting lives |
| `0x03004650/51` | IWRAM | password keyboard cursor X/Y |
| `0x365418` / `0x365428` | ROM | "Enter PassWord" / "Wrong PassWord" (literal xrefs at `0x82CA828`/`0x82CA840`) |
| `0x36FD90`–`0x36FE58` | ROM | main-menu labels including Level Select |

## 5. Algorithm

**`check_password_1(c[0..6])`** (derived from Thumb disassembly):

```
if any(c[i] > 8): return 0                 # symbols 0x09..0x12 rejected
P = table_by_first_char[c[0]]              # permutation of 0..5 (below)
bucket[P[i-1]] = c[i]  for i = 1..6        # chars 2..7
ok = (bucket[0] + bucket[3] == 9)          # pairs (1,8)..(8,1)
  && (bucket[4] == bucket[1] + 4)          # pairs (1,5)..(4,8)
  && (bucket[2] + bucket[5] == 8)          # pairs (1,7)..(7,1)
return ok
```

**`password_check(c[0..6])`** (decoder): same bucket idea but with its own
permutation table (P's permutation differs from the validator's), then

```
level_code = f(bucket[1], bucket[2])   # 0..14; 0 = Stage 1-lvl 1, 14 = Stage 4 BOSS
lives      = bucket[0] + 1             # 2..9
store level_code at 0x030027DC ; store lives at 0x030020A2
```

Level code to published label: `n+1` maps to `1-2`…`4-3`; code `0` (Stage
1-lvl 1) is the unadvertised default level.

## 6. Tables

**Letter → code** (on-screen A–Q grid, X/Y in brackets):

| A | B | C | D | E | F | G | H | I | J | K | L | M | N | O | P | Q |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0x0A | 0x01 | 0x0B | 0x02 | 0x0C | 0x03 | 0x04 | 0x0D | 0x0E | 0x05 | 0x0F | 0x06 | 0x07 | 0x10 | 0x11 | 0x08 | 0x12 |
| (0,0) | (1,0) | (2,0) | (3,0) | (4,0) | (5,0) | (0,1) | (1,1) | (2,1) | (3,1) | (4,1) | (5,1) | (0,2) | (1,2) | (2,2) | (3,2) | (4,2) |

**Validator permutation (bucket for chars 2..7):**

| first | B | D | F | G | J | L | M | P |
|---|---|---|---|---|---|---|---|---|
| perm | 0,1,2,3,4,5 | 5,0,1,2,3,4 | 4,5,0,1,2,3 | 3,4,5,0,1,2 | 2,3,4,5,0,1 | 1,2,3,4,5,0 | 3,1,2,4,5,0 | 3,1,2,4,5,0 |

**Decoder permutation:** identical except **P = 4,1,2,3,5,0** — this mismatch
is why P-prefixed passwords decode to different level/lives than the otherwise
equivalent M-prefixed ones.

**Published codes verified** (all 14 accepted; "lvl/lives" from decoder and
confirmed in RAM for the first entry):

```
1-2 FJLJBDG(1/6)   1-3 GGJJJBF(2/6)   1-4 BFBGLJG(3/4)
2-1 LDBMLMD(4/3)   2-2 GMLLDDD(5/3)   2-3 LDFMLJD(6/3)
2-4 DGDDGML(7/3)   3-1 GMMMDFB(8/3)   3-2 MPFDMLB(9/2)
3-3 FMJBFFP(10/2)  3-4 LFGPMGB(11/2)  4-1 GPPMBGB(12/2)
4-2 DLBGDPP(13/2)  4-3 LGFPPJB(14/2)
```

The `JASON88`, `CHIROS20`, … list on one "Kong Cheats" page belongs to a
different game/SKU (digit symbols are not in this game's alphabet) and was
recorded as **unverified / wrong SKU**, per §16.11.

## 6b. Enumeration

* **Representable space:** 17-letter keyboard, but validator restricts every
  character to codes 1–8 → `8^7 = 2,097,152` candidate strings.
* **Exact accepted set:** brute force over all `8^7` with the reimplemented
  validator gives **1,792** accepted codes. Closed form: 8 choices of first
  character × 8 choices for `(bucket0,bucket3)=(1,8)…(8,1)` × 4 choices for
  `bucket4=bucket1+4` × 7 choices for `bucket2+bucket5=8` = **1792**.
* **Prior art gap:** the wrongbaud/voidstarsec blog emulated `7^7 = 823,543`
  inputs with symbols `{B,D,F,G,J,L,M}` and reported 882 codes. That is exactly
  the subset of the 1,792 with no `P`: **910 accepted codes contain P** and are
  absent from that enumeration and from every published cheat list.
* **Distinct effects:** 120 `(level_code, lives)` pairs; all level codes
  `0…14` occur; lives range `2…9`. 224 accepted codes begin with P.
* **Novel code (observed in emulator):** `PBBDJLP` — codes
  `08 01 01 02 05 06 08`, not on GameFAQs/GameGenie/VGChartz/TCRF/SuperCheats
  or in the 882-code blog list. Entered on the real PASSWORD screen:
  RAM `0x030027DC = 1` (level 1-2) and `0x030020A2 = 9` (nine lives), versus
  published `FJLJBDG` → level 1, lives 6. Screenshot: `pw_novel.png`.
* **Bounds proven by rejection (observed):**
  * `ABBBBBB` — buffer `0a 01 01 01 01 01 01`, letter A has code `0x0A > 8`.
    Level/lives stayed `0/0`; OCR of `pw_reject_range3.png` reads
    "WRONG PASSWORD".
  * `BBBBBBB` — all symbols in alphabet but checksum equations fail.
    Level/lives stayed `0/0`; OCR of `pw_reject_check.png` reads
    "WRONG PASSWORD".
  * Code value `0x09` has no keyboard letter at all (unrepresentable), so the
    reserved hole between the two alphabets is closed by construction.

## 7. Validation evidence

* **Derived** — validator/decoder algorithm, tables, permutations, 1,792-code
  count and closed form, from Thumb disassembly at `0x082CC970` and
  `0x082CCCBC` plus reimplementation. Reimplementation accepts all 14 published
  codes and reproduces all 14 published level labels exactly.
* **Observed** — mGBA screenshots and savestate RAM: title (4-item ring; 5 Downs
  returns to item 2), password grid, options (Music/SFX Volume, Default All),
  credits ("Executive Creative Director Joseph Sutton"), pause (Brightness,
  Music Vol, SFX Vol, Quit), level intro/gameplay. Published `FJLJBDG` →
  level 1, lives 6; novel `PBBDJLP` → level 1, lives 9; two rejected inputs →
  level 0, lives 0 and "WRONG PASSWORD" (OCR).
* **Inferred** — the IWRAM byte at `0x030020A2` is labelled "starting lives"
  from the decoder store and its correlation with every published code; the
  full "lives" gameplay consumption was not played out to zero. The 5-item
  menu's Level Select entry is present as data/handler but its activation gate
  was not identified.

## 8. Unknowns

* The 5th MAIN MENU entry (Level Select, id `0x12`, handler `0x082CB2C1`) is
  not shown on the shipping 4-item title ring. No 32-bit pointer to the table
  base `0x0836FD70` exists in the ROM, no BL/BLX caller reaches the handler
  directly, and L+R+Start, L+R+A, L+R+B, Select+Start and Konami-style
  sequences produced no new screen. It is most likely a gated/development
  menu; the gate itself remains unknown.
* Whether `level_code = 0` (Stage 1-lvl 1) is intentionally omitted from the
  published list or simply never printed at a level end was not determined.

## 9. Tooling

`arm-none-eabi-objdump -M force-thumb`, Capstone/Keystone, `strings`, Python 3
(`phase0.py`, `recon.py`, `locate.py`, `model.py`, `decode.py`, `state.py`,
`emu.py`, `diffstate.py`, `combos.py` in `/tmp/opencode/kongatlantis`), mGBA SDL
with savestate RAM reads, Xvfb `:317`, xdotool, ImageMagick, tesseract OCR.
No ROM or copyrighted assets are redistributed; only addresses, hashes, and
the author's own scripts/results are published.
