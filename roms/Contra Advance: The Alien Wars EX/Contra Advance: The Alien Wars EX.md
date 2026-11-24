# Contra Advance: The Alien Wars EX (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Item | Value |
|---|---|
| File | `roms/Contra Advance: The Alien Wars EX/Contra Advance: The Alien Wars EX.gba` |
| Size | 4,194,304 bytes (32 Mbit) |
| Header title | `CONTRAADVANC` (0xA0, 12 bytes) |
| Game code | `AAWE` |
| Maker code | `A4` |
| Software version | `00` |
| Fixed byte 0xB2 | `0x96` |
| Complement check | `0x4A` (matches computed `0x4A`) |
| Header checksum (0xBE) | stored `0x0000`; computed `0xFA4A` (header was rebuilt) |
| MD5 | `deb9740c2871d0729a9b00386d22dba6` |
| SHA-1 | `bb6e3a3b66aad9fb9b3eb700fbb9aa2bb6ce065a` |
| SHA-256 | `02286ab52784cfd8069c1b57290919509e658e13ce82d6f735cf2dac4b16160e` |

### Release state / patch

This is a scene release, not the clean retail image:

* Header entry word is `0xEA0FEFFE`, an ARM branch to `0x083FC000`, not the
  stock `0xEA00002E` branch to `0x080000C0`.
* `0x083FC000` is a MODE7 intro: it copies a 1 KiB payload to `0x02010000`,
  clears VRAM/IO and jumps into the copied payload. The scroll text at file
  `0x3FFD58` reads `MODE7 PRESENTS ON NOVEMBER 7TH, 2002 :: CONTRA ADVANCE:
  THE ALIEN WARS EX (C) KONAMI...`.
* There is no trainer menu. Searches for `TRAINER`, `INFINITE`, `CRACK`, etc.
  returned only the MODE7 scroll text.
* Analysis was done on a copy with word 0 restored to `0xEA00002E` (the stock
  crt0 at `0x080000C0` is intact); only those four bytes differ. All addresses
  below are ROM addresses in that stock copy. Header checksum `0x0000` is the
  expected artefact of the rebuilt header (`0xBC` complement is still valid).

## 2. Executive summary

* The game has a full in-game **18-character password system**, reachable from
  `1 PLAYER → CONTINUE GAME`. It stores a continue/restore state (score,
  starting lives, area index, difficulty and three auxiliary fields).
* The entry grid offers the alphabet `1-9 A-Z` (35 symbols, no `0`). The data
  payload is base-26 over `A-Z` (A=0). On submit every cell is mapped through
  `1↔A, 2↔I, 3↔U, 4↔E, 5↔O`; two of the 18 cells are `mod 26` checksums
  (`'A' + value`).
* The published GBA password list was verified: **all 13 published codes pass
  both checksums** under the recovered model, and three were entered in-game
  and accepted.
* **A novel code was generated, entered and RAM-verified**:
  `2Q1H1NVZ2N1Z1FYKG1` starts a game with **77 lives** (no published list has
  77), score `123456`, area `19`. The lives field was then observed
  decrementing `77 → 76 → 75 → … → 67` as the player died.
* **Bounds proven by rejection:** changing one data cell without recomputing
  the checksums (`21111NTYLH1ZFCS5H1`) leaves the player on the
  `PASSWORD ERROR` screen and starts no game. Out-of-range fields are clamped:
  a checksum-valid code asking for `120` lives stores `99`, and one asking for
  area `31` stores `29`.
* **Hidden developer password found and verified:** the ROM literal at
  `0x08185140` is `KONAMICONTRASPCOMD`. Entered at the password screen it
  bypasses the checksum path and sets the stage-select unlock flag
  `0x03001A64 = 1`. The next `1 PLAYER → NEW GAME` shows a hidden
  `LEVEL 1 … LEVEL 6` menu (`0x0800984A`) instead of starting the game.
* **The published GBA title-screen stage-select button code does not exist in
  this ROM.** The button-mask tables for the SNES/GB sequences and the Konami
  code are absent, and the only instruction that can set the stage-select gate
  to 1 is the developer-password path at `0x0800A5DA`. The listed sequence was
  also pressed in-game: the flag stayed 0 and the game started normally.
* No sound-test/debug menu exists: `SOUND` occurs only in the credits string
  `SOUND DESIGNERS`; no sound-test screen code exists.

## 3. How to reproduce

Emulator: mGBA (SDL) under Xvfb, `SDL_AUDIODRIVER=dummy`, scale `-3`.
Default mGBA SDL keymap used throughout:

| GBA | Key |
|---|---|
| A | `x` |
| B | `z` |
| Start | `Return` |
| Select | `BackSpace` |
| D-pad | arrow keys |

Exact path to the password screen (verified by stack/RAM reads at each step):

```
boot → title "PRESS START"
press Start            -> title menu (1 PLAYER / 2 PLAYERS / OPTION)
press A                -> 1 PLAYER: NEW GAME / CONTINUE GAME menu
press Down, press A    -> password screen (18-cell grid, buffer 0x0300224C = 'A'×18)
```

Editor controls (verified by reading `0x0300224C` after each key):

* `Left` / `Right` move the 18-cell cursor (wraps 0↔17).
* `Down` advances the cell through `1 2 … 9 A B … Z 1`; `Up` reverses
  (`A→9`, `1→Z`; `0` is not in the cycle).
* `Start` or `A` submits; `B` returns to the title.
* On a failed checksum the game displays `PASSWORD ERROR`, keeps the string and
  waits for `Start`/`A` to re-open the editor. The string is not cleared.

Key timing that worked: 150 ms hold / 250–400 ms gap for menus; 70 ms hold /
70 ms gap for the 18-cell entry (each key is sampled once per frame).

To retest without replaying: save a state on the password screen (mGBA
`Shift+F1`), enter a code, and load it with `F1`.

Test codes and expected RAM (all entered on the real screen):

| Code | Result |
|---|---|
| `11111NTYLH1ZFCS5H1` | accepted; lives 6, score 0, area 19, difficulty Novice, aux 1/6/0 |
| `111113TYLH1WBHZXZ1` | accepted; lives 6, score 0, area 19, aux 2/6/0 |
| `Y4HC1BL5P21234ZWF1` | accepted; lives 99, score 40012, area 4, aux 1/5/0 |
| `2Q1H1NVZ2N1Z1FYKG1` | **novel** accepted; lives 77, score 123456, area 19 |
| `FYFLBCSH5RBP2B4WG1` | accepted; requested 120 lives → 99, requested area 31 → 29 |
| `21111NTYLH1ZFCS5H1` | **rejected** (bad checksum) → `PASSWORD ERROR`, no game |
| `KONAMICONTRASPCOMD` | **developer password** accepted; `0x03001A64 = 1`, returns to title |
| `K5N1M2C5NTR1SPC5MD` | rejected (this is *not* the entry form; see §6) |

Developer-password path after unlock:

```
boot → Start → A (1 PLAYER) → A (NEW GAME)
   -> hidden LEVEL 1..6 menu (stack 0x0800985F loop)
   -> Start on any entry starts the game with area 29 (Novice) / 19 (Normal)
```

## 4. Address map

All ROM addresses include the `0x08000000` base; file offset = address −
`0x08000000`.

### Code

| Address | Meaning |
|---|---|
| `0x080089A8` | key update: reads `KEYINPUT 0x04000130`, stores active-high `0x03001A5A` (held) and `0x03001A58` (newly pressed) |
| `0x08009A6C` | OPTION MODE menu (DIFFICULTY LEVEL / EXIT) |
| `0x08009C62` | stores difficulty value `r6` to `0x03001A80` and `0x03001A82` |
| `0x08009C90` | NEW GAME / CONTINUE GAME menu (returns 0, 1 or −1) |
| `0x08009E44` | password screen entry, called from `0x080097E6` |
| `0x08009E7C` | editor block: 3×6 grid, cursor, per-cell character cycle |
| `0x08009FFC`–`0x0800A006` | `Up`/`Down` character cycle (1-9 then A-Z) |
| `0x0800A07C`–`0x0800A18C` | submit: applies the `1↔A 2↔I 3↔U 4↔E 5↔O` map (jump table `0x0800A398`) |
| `0x0800A198` | checksum computation over the 18 mapped cells (`B[5]=B[11]='A'`) |
| `0x0800A214` | payload decode: v1 → record+8, v2 → `0x03001A7C`, v3 → field writes |
| `0x0800A498` | second map pass + literal-password compare path |
| `0x0800A5B4` | 18-byte compare against `0x08185140` |
| `0x0800A5DA` | `0x03001A64 = 1` (developer unlock) |
| `0x0800A5FC` | `PASSWORD ERROR` screen loop; string drawn at `0x0800A648` from `0x080692E0` |
| `0x0800A6F8` | base-26 hash helper called at `0x0800A218`, `0x0800A244`, `0x0800A258` |
| `0x08009840` | stage-select gate: reads `0x03001A64`; non-zero → menu, zero → start game |
| `0x0800984A` | hidden `LEVEL 1..6` menu loop |
| `0x0800998C` | menu selection: clears keys, sound `0x123`, falls to `0x0800999A` |
| `0x0800999A` | writes area `19` (normal) or `29` (novice) into `record+0x18` |

### Data

| Address | Meaning |
|---|---|
| `0x08185140` | `KONAMICONTRASPCOMD` (18 bytes, no NUL; developer password) |
| `0x08185154` | menu label pointer table: 0 `1 PLAYER`, 1 `2 PLAYERS`, 2 `OPTION`, 5 `OPTION MODE`, 6 `DIFFICULTY LEVEL`, 7 `EXIT`, 8 `NORMAL`, 9 `NOVICE`, 10 `NEW GAME`, 11 `CONTINUE GAME`, 12 `PASSWORD`, 13 `CONTINUE`, 15–20 `LEVEL 1`–`LEVEL 6` |
| `0x08069238` | `PASSWORD` |
| `0x080692E0` | `PASSWORD ERROR` |
| `0x0300224C` | 18-byte password input buffer (cells 0–17) |
| `0x03002C5C` | player record table, stride `0x64C`, active index at `0x03001A78` (0/1) |
| record `+0x04` | starting lives (observed decrementing on death; 99 in the published “99 lives” codes) |
| record `+0x08` | score = min(v1, 10,000,000) |
| record `+0x18` | area/level index 0–31, clamped to 29 (Normal) or 19 (Novice) |
| record `+0x4C` | auxiliary field 0–7, values > 5 forced to 0 |
| `0x03001A64` | stage-select unlock flag (only writer of 1: `0x0800A5DA`) |
| `0x03001A6C` | `((v3>>1)&7)+1`, 1–8, clamped to 5 (Normal) / 3 (Novice) |
| `0x03001A7C` | `v2 − 111111` (u32, clamped to 10,000,000); canonical codes equal the score |
| `0x03001A80` | difficulty mirror (written together with `0x03001A82`) |
| `0x03001A82` | difficulty: `0` = Normal, `1` = Novice |
| `0x03001A84` | `(v3>>19)&0xF`, clamped to 5 (Normal) / 10 (Novice) |
| `0x03001A78` | active record index used by the key-history writer (`0x08008A1C`) |

## 5. Algorithm

### 5.1 Character map

```
map(1)=A map(A)=1   map(2)=I map(I)=2   map(3)=U map(U)=3
map(4)=E map(E)=4   map(5)=O map(O)=5   every other character unchanged
```

The map is an involution. The editor applies it once on submit; the failure
path applies it a second time, which is why the literal comparison at
`0x0800A5B4` sees the original typed string.

### 5.2 Checksums (exact)

Let `B[0..17]` be the mapped 18 bytes. Set `B[5]=B[11]=0x41 ('A')` before
computing.

```
c1 = 0
c2 = 0xFF
for i in 0,2,4,...,16:
    c1 = (c1 + 0xBF + B[i]) & 0xFF
    c2 ^= (B[i]   - 0x41) & 0xFF
    c1 = (c1 + 0x41 - B[i+1]) & 0xFF
    c2 |= (B[i+1] - 0x41) & 0xFF
# c1 == sum(B[even]) - sum(B[odd]) mod 256
require B[5]  == 'A' + (c1 % 26)
require B[11] == 'A' + (c2 % 26)
```

There are no reserved bits; both checksum characters are always `A-Z`.

### 5.3 Payload

Base-26, least-significant character first (A = 0):

```
v1 = sum_{k=0..4} (B[k]    - 0x41) * 26^k      # cells 0..4
v2 = sum_{k=0..4} (B[6+k]  - 0x41) * 26^k      # cells 6..10
v3 = sum_{k=0..4} (B[12+k] - 0x41) * 26^k      # cells 12..16
```

`B[17]` is a free salt character: it is covered by both checksums but is not
part of any decoded field. Cell 5 is the checksum for group 1, cell 11 for
group 2.

### 5.4 Decode into the player record

```
idx  = u16[0x03001A78] & 1
rec  = 0x03002C5C + idx * 0x64C
rec[+0x08]      = min(v1, 10_000_000)                 # score
u32[0x03001A7C] = min(v2 - 111_111, 10_000_000)       # score mirror
u16[0x03001A82] = v3 & 1                              # 0 Normal / 1 Novice
u16[0x03001A6C] = ((v3 >> 1) & 7) + 1                 # 1..8
rec[+0x04]      = min((v3 >> 4) & 0x7F, 99)           # lives
rec[+0x4C]      = (v3 >> 11) & 7; if > 5 then 0
rec[+0x18]      = (v3 >> 14) & 0x1F
u16[0x03001A84] = (v3 >> 19) & 0xF
if u16[0x03001A82] != 0:        # Novice
    u16[0x03001A6C] = min(u16[0x03001A6C], 3)
    rec[+0x18] = min(rec[+0x18], 19)
    u16[0x03001A84] = min(u16[0x03001A84], 10)
else:                          # Normal
    u16[0x03001A6C] = min(u16[0x03001A6C], 5)
    rec[+0x18] = min(rec[+0x18], 29)
    u16[0x03001A84] = min(u16[0x03001A84], 5)
return 1
```

The lives field `record+0x04` is **not** clamped by the difficulty branch; it
is clamped to 99 at `0x0800A288`–`0x0800A298`, which is why the published
“99 lives” codes keep 99 under the Normal flag.

Note: the decoder does **not** compare v1 with v2−111111. All 13 published
codes satisfy `v1 == v2-111111`; a code that violates it is still
checksum-valid and would store different score values in the two slots.

### 5.5 Encoder (inverse)

Given `V`, `V2 = V + 111111`, `F` (23-bit field word), and salt `s` in 0..25:

```
B[0..4]   = base26(V)   least-significant first
B[6..10]  = base26(V2)  least-significant first
B[12..16] = base26(F)   least-significant first
B[17]     = 'A' + s
compute c1,c2 with B[5]=B[11]='A'
B[5]='A'+c1%26 ; B[11]='A'+c2%26
typed_code = map(B)
```

### 5.6 Developer password path

```
submit → map typed chars (B)
       → checksum fails (the literal is not checksum-valid)
       → restore B[5],B[11]
       → map B again (undoes the first map: buffer == typed string)
       → compare 18 bytes with 0x08185140 "KONAMICONTRASPCOMD"
       → if equal: sound 0x1CB; u16[0x03001A64]=1; return 0 (back to title)
```

The literal must therefore be typed **verbatim**: `KONAMICONTRASPCOMD`.
Typing the already-mapped form `K5N1M2C5NTR1SPC5MD` fails, because the double
map leaves it unchanged and it does not equal the ROM literal (observed:
rejected).

## 6. Tables

### 6.1 Field layout of `v3`

| Bits | Destination | Range / clamp | Name (confidence) |
|---|---|---|---|
| 0 | `0x03001A82` | 0/1 | difficulty: 0 Normal, 1 Novice (observed in option menu) |
| 1–3 | `0x03001A6C` | 1–8, clamp 5 (Normal) / 3 (Novice) | unknown counter (possibly continues) |
| 4–10 | record+4 | 0–127, clamp 99 | lives (Observed: decrements on death) |
| 11–13 | record+0x4C | 0–7, >5→0 | unknown |
| 14–18 | record+0x18 | 0–31, clamp 29 (Normal) / 19 (Novice) | area/level index |
| 19–22 | `0x03001A84` | 0–15, clamp 5 (Normal) / 10 (Novice) | unknown |

### 6.2 Published GBA passwords (3rd party cheat indexes) decoded with the model

Payloads are `v1`, `v2-111111` (always equal), `v3`; then the decoded fields.
“Diff” is `0x03001A82` (0 Normal / 1 Novice).

| Published label | Code | v1 | v3 | diff | 1A6C | rec4 | rec4C | rec18 | 1A84 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Stage 2 Novice | `11111NTYLH1ZFCS5H1` | 0 | 3457121 | 1 | 1 | 6 | 0 | 19 | 6 |
| Stage 2 Normal | `111111TYLH1S35MYH1` | 0 | 3629152 | 0 | 1 | 6 | 4 | 29 | 6 |
| Stage 2 99 lives | `Y4HC1BL5P21234ZWF1` | 40012 | 2688576 | 0 | 1 | 99 | 0 | 4 | 5 |
| Stage 3 Novice | `111113TYLH1WBHZXZ1` | 0 | 11845731 | 1 | 2 | 6 | 0 | 19 | 6 |
| Stage 3 Normal | `11111HTYLH1XQTTH1B` | 0 | 136386 | 0 | 3 | 76 | 2 | 8 | 0 |
| Stage 3 99 lives | `WXJD1ZJHSJ1QKKNCY1` | 59432 | 11011634 | 0 | 3 | 99 | 0 | 0 | 5 |
| Stage 4 Novice | `11111BTYLH1TXLGHSB` | 0 | 8352965 | 1 | 3 | 76 | 6 | 29 | 15 |
| Stage 4 Normal | `11111JTYLH1ZMY1RSB` | 0 | 8524996 | 0 | 3 | 76 | 2 | 8 | 0 |
| Stage 4 99 lives | `ZWJF1JMGSL1BGP3LQB` | 94561 | 7518868 | 0 | 3 | 41 | 7 | 10 | 14 |
| Stage 5 Normal | `11111VTYLH132D21LC` | 0 | 5032230 | 0 | 4 | 18 | 1 | 19 | 9 |
| Stage 5 99 lives | `G3421NTDN51NC3BV2C` | 143838 | 4026102 | 0 | 4 | 99 | 5 | 21 | 7 |
| Stage 6 Normal | `11111MTYLH1VCFDJDD` | 0 | 1531272 | 0 | 5 | 88 | 3 | 29 | 2 |
| Stage 6 99 lives | `W3MJ1SJ4VP1NYY24BD` | 166838 | 533336 | 0 | 5 | 53 | 4 | 0 | 1 |

Observations:

* All 13 pass both checksums and all satisfy `v1 == v2 - 111111`.
* The published “99 lives” label is exact: every one of those six codes
  decodes `record+4 = 99` (the clamp ceiling).
* The published **stage labels do not map linearly to `record+0x18`**. In
  particular the Stage 3 Normal and Stage 4 Normal strings decode to the
  *identical* field tuple `(diff=0, 1A6C=3, lives=76, rec4C=2, area=8, 1A84=0)`:
  a genuine alias pair (§16.4b). Report the decoded payload, not the label.

### 6.3 Generated codes (not in any published list)

| Code | Purpose | v1 | v3 | diff | 1A6C | lives | rec4C | area | 1A84 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `2Q1H1NVZ2N1Z1FYKG1` | novel playable code | 123456 | 2933970 | 0 | 2 | **77** | 0 | 19 | 5 |
| `FYFLBCSH5RBP2B4WG1` | clamp test | 654321 | 3131266 | 0 | 2 | 120→**99** | 0 | 31→**29** | 5 |

## 6b. Enumeration

### Space size

* Input surface: 18 cells × 35 symbols (`1-9`, `A-Z`) = **35^18 =
  6,211,904,899,255,558,013,916,015,625** raw strings.
* Both checksum cells are `A-Z` (26 values). For every choice of the remaining
  16 cells the two checksums are uniquely determined, so the accepted input
  space is **35^16 = 5,070,942,774,902,496,337,890,625** strings.
* Canonical (letter-only, base-26) payloads: 15 base-26 digits = **26^15 =
  1,677,259,342,285,725,925,376** payload triples. Restricting to the canonical
  `v1 = v2-111111` relation leaves **11,770,264** distinct (v1,v2) pairs
  (`v2 = v1+111111` must remain < 26^5).
* Semantically distinct canonical codes: `V` (11,770,264) × 23-bit `F`
  (8,388,608) × salt (26) = **2,567,139,399,565,312** strings, before the
  field clamps alias many `F` values.
* Cells 5/11 are the only checksum positions; `B[17]` is a free salt; no
  reserved bits.

### Novel code and in-game proof

`2Q1H1NVZ2N1Z1FYKG1` — generated by the encoder with V=123456, F=2933970,
salt=0:

* Accepted on the real password screen; the game started (stack moved to the
  gameplay loop `0x08008C8D` / `0x0800FB2D`).
* RAM read after acceptance (`0x03002C5C` record):
  `+0x08 = 123456`, `+0x04 = 77` (lives), `+0x18 = 19` (area), `+0x4C = 0`,
  `0x03001A7C = 123456`, `0x03001A82 = 0`, `0x03001A6C = 2`,
  `0x03001A84 = 5`.
* The lives counter was then observed live: after moving into enemies the value
  went `77 → 76 → 75 → 74 → 73 → 72 → 70 → 69 → 68 → 67` at 3 s intervals
  (each step is a death). No published list contains 77 lives.

Second generated code `FYFLBCSH5RBP2B4WG1` proves the decoder’s range layer:
requested lives 120 stored 99; requested area 31 stored 29.

### Bounds proven by rejection

* `21111NTYLH1ZFCS5H1` (cell 0 changed, checksums left untouched): the screen
  returns to the `PASSWORD ERROR` loop (`0x0800A5FC`, stack `0x0800A611`), the
  game does not start, and `0x03001A64` stays 0. Both checksum layers are
  independently required.
* The editor cannot express `0`: `Down` goes `9→A` and `Up` goes `A→9`, so
  `0` is not in the cycle. `A` itself is expressible but maps to `1`.
* Out-of-range fields (above) prove the semantic clamps rather than silent
  acceptance.

### Button-code space (negative result, bounded)

Searches of the whole 4 MiB for the published sequences in every plausible
encoding returned zero hits for the 6-press stage-select and the 10-press
Konami code:

| Sequence | u16 held | u8 held | u16 active-low | u8 active-low | 4-bit dirs |
|---|---:|---:|---:|---:|---:|
| Down, Down-Left, Left, Up-Left, Up (5) | 0 | 0 | 0 | 0 | 0 |
| Konami Up Up Down Down Left Right Left Right B A | 0 | 0 | 0 | 0 | 0 |
| Sound test Right, Right-Down, Right, A | 0 | 0 | 0 | 0 | n/a |

The 6-press published GBA stage-select sequence was also pressed on the real
title screen: `0x03001A64` remained 0, and `1 PLAYER → NEW GAME` went straight
to gameplay (`record+0x18 = 29`), not to the LEVEL menu. A closed-set proof
backs this up: the only instruction in the ROM that stores 1 to `0x03001A64` is
`0x0800A5DA` (the developer-password path). No button matcher can reach it.

## 7. Validation evidence

**Observed (emulator RAM / savestate reads):**

* Password screen buffer `0x0300224C` matched every typed string exactly
  (13+ entries), and the editor’s 35-symbol cycle was measured by reading the
  buffer after single `Up`/`Down` presses.
* Published code `11111NTYLH1ZFCS5H1`: lives 6, score 0, area 19, diff 1,
  aux 1/6/0.
* Published code `111113TYLH1WBHZXZ1`: lives 6, score 0, area 19, diff 1,
  aux 2/6/0.
* Published code `Y4HC1BL5P21234ZWF1`: lives 99, score 40012, area 4, diff 0,
  aux 1/5/0.
* Novel code `2Q1H1NVZ2N1Z1FYKG1`: lives 77, score 123456, area 19, aux 2/5/0;
  lives then decremented to 67 over nine deaths.
* Clamp code `FYFLBCSH5RBP2B4WG1`: lives 99 (from 120), area 29 (from 31),
  score 654321.
* Bad-checksum code `21111NTYLH1ZFCS5H1`: `PASSWORD ERROR` loop, no game.
* Developer password `KONAMICONTRASPCOMD`: `0x03001A64=1`, returns to title;
  next `1 PLAYER → NEW GAME` enters the `LEVEL 1..6` menu loop
  (`0x0800985F`).
* OPTION MODE difficulty: moving the selector and confirming writes the same
  value to `0x03001A80` and `0x03001A82` (observed 0→1).
* Published title-screen button sequence: no effect on `0x03001A64`; game
  starts normally.

**Derived (instruction-level):**

* Checksum equations and field bit assignments (§5) from `0x0800A198`–
  `0x0800A2FC`; every decoded value agrees with RAM for six codes.
* The only writer of `0x03001A64 = 1` is `0x0800A5DA`; the only reader is the
  gate at `0x08009842`.
* The LEVEL menu selection path (`0x0800998C`–`0x0800999A`) does not read the
  cursor register `r8`, so the chosen label does not influence the area byte.
  Consistent with the one selection observed (area 29).
* `record+4` is the lives counter: it is the field the published “99 lives”
  codes set to 99, and the novel code’s value was observed decrementing once
  per death.

**Inferred:**

* `0x03001A6C`, `record+0x4C` and `0x03001A84` are auxiliary progress fields
  (continues / weapon / rank); their exact labels were not proven by a
  gameplay observation.
* The exact mapping from `record+0x18` to a printed stage name is not linear
  and was not proven; the decoded payloads are the reliable data.

## 8. Unknowns

* The game’s own password **generator** (the screen that would display a
  password after a game-over) was not reached; only the decoder/entry side was
  reversed. The decoder is sufficient to mint canonical codes because the
  encoder is its exact inverse and six generated/accepted codes prove it.
* Semantic names of `0x03001A6C`, `record+0x4C` and `0x03001A84`.
* The area-index → stage-name mapping (published stage labels and the area byte
  disagree; Stage 3 Normal and Stage 4 Normal are exact aliases).
* Whether the MODE7 intro returns to the stock entry or expects a key; the
  analysis used the restored stock entry and did not exercise the intro.

## 9. Tooling

* `arm-none-eabi-objdump` (binutils-arm-none-eabi), Capstone not required.
* mGBA SDL under `Xvfb :262` + openbox, `SDL_AUDIODRIVER=dummy`.
* Python helpers in `/tmp/contraadvance/`:
  * `gba.py` — key injection, savestate save/load, gbAs chunk decompression
    (PNG chunk `gbAs`, zlib; IWRAM at state offset `0x19000`, EWRAM at
    `0x21000`).
  * `typer.py` — drives the 18-cell editor from the current buffer to a target
    string and verifies `0x0300224C`.
  * `decode.py` (inline in the session) — encoder/decoder and enumeration.
* Savestates were used as the primary RAM read path; no screenshots were taken
  and no image files were read (media ban respected). All proofs above are
  text/RAM/address based.

## Legal note

No ROM, extracted graphics, music or game text is redistributed here. Only
addresses, algorithms, hashes and self-generated codes are published.
