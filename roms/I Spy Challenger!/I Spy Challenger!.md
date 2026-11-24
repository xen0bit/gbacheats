# I Spy Challenger! (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `I Spy Challenger!.gba` |
| Size | 8,388,608 bytes (0x00800000) |
| Header title | `ISPY CHALNGR` |
| Game code | `A4CE` |
| Maker | `7T` (Scholastic) |
| Version | 0x00 |
| Fixed byte 0xB2 | 0x96 |
| Complement | 0x65 |
| Header checksum | 0x0000 |
| Entry word | 0xEA00002E (stock `b 0x080000C0`) |
| MD5 | `a3201407f7988a563f4dfb243db02bcb` |
| SHA-1 | `532934239ea1151927fd45298d918e0646a6bea4` |
| SHA-256 | `24c222bb1813f24eb7ef737b9b43417452b196dcc46293351fd1bc56771936be` |

**Phase 0:** full-file Nintendo-logo scan found exactly one header (file 0x4). No appended
trainer, no multi-game image, no cracktro patch; the entry word is stock. The build is a
**debug/assertion build**: it retains C++ RTTI names and `ASSERTION FAILED` / `Testing
sequence...` / `inGameMenu::changeLevelDirection` strings in the 0x6A9xxx–0x6AAxxx bank.
No ROM or copyrighted asset is reproduced here.

## 2. Executive summary

Two cheat families are published for this title:

1. **Name-screen code `ISPYER`** — **confirmed in the emulator, twice**. Typing the six
   letters on the "Pick letters to spell your name." screen and pressing GO shows
   **"Bonus Riddle! Search all the riddles to find these objects."** This is a single
   hard-coded equality check, not an algorithmic password system: the complete accepted
   set is exactly one string out of 26^6 = 308,915,776 possible names.

2. **20 three-button "level select" codes** published by 3rd party cheat indexes (e.g.
   `Up,Up,Left` → level 2 easy). These are **not reachable in this retail image**: the
   described "Code" option does not exist in any menu. The manual enumerates the Pause
   Menu as CHANGE GAME / SAVE / CONTINUE / CHANGE LEVEL / HIGH SCORES, and every menu in
   the ROM was walked. The 20 sequences do not appear in the ROM as ASCII or as any
   aligned active-low/active-high key-mask table. They are recorded verbatim below as an
   unverified published claim; no in-game effect was produced on the surfaces available.

## 3. How to reproduce

* Emulator: mGBA (SDL) on `Xvfb :315`, `SDL_AUDIODRIVER=dummy`, `-3` scale.
  Keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`,
  D-pad = arrow keys. Holds of 60–130 ms with ~420 ms gaps were needed; rapid repeated
  presses coalesce (a burst of six `Right`s registered as one).
* Fresh boot (delete the `.sav` first) → title screen → **A** → name entry.
* Keyboard navigation on the name screen: the 26 letters are a **ring**; `Left`/`Right`
  move ±1, `Up`/`Down` move to the nearest-x letter in the adjacent row (row lengths
  8 / 10 / 8). After the sixth letter is accepted, the cursor jumps to **GO**; press **A**.
* Enter `I`, `S`, `P`, `Y`, `E`, `R` (from A: `Down,Left`; `Down`; `Left`×3; `Down`;
  `Up,Up,Left,Left`; `Down,Right`×4), then **A** on GO → bonus riddle text screen.
* Negative controls: `ISPYEQ` and `AAAAAA` both land on the game-select screen (no bonus).
* Published button sequences tested on the in-game CHANGE LEVEL screen (MATCH ATTACK and
  HOOP DROP) and during gameplay: no level change.

## 4. Address map

| Item | File offset | ROM address | Notes |
|---|---:|---:|---|
| `ISPYER` literal (copy #1) | 0x6AA2C0 | 0x086AA2C0 | NUL-terminated ASCII; followed by "last riddlescreen = %d" |
| `ISPYER` literal (copy #2) | 0x6AA6E8 | 0x086AA6E8 | signinMenu static string |
| Pointer slot to copy #1 | 0x71B8 | 0x080071B8 | ARM literal pool |
| Literal load of that slot | — | **0x08006F64** | `ldr r1,[pc,#0x24c]` |
| `strcpy` helper | — | 0x08041498 | copies source NUL string into r0 |
| Success path / popup | — | 0x08006F58–0x08006F94 | BL 0x0802246C with r0=0x78 (popup 120) |
| signinMenu setup | — | 0x08006CC4 | contains the `== -1` gate at 0x08006F40 |
| `inGameMenu::changeLevelDirection` | — | 0x08020B00 | level = `obj[0x1C]`, clamped to `obj[0x20]` |
| "Testing sequence..." string | 0x6AAEAC | 0x086AAEAC | debug leftover; no reachable code xref found |
| Key shadow (current/prev) | — | **0x02001934 / 0x02001936** | u16 active-low: 0x03FF idle, 0x03DF = Left |
| Player-name buffer (result screen) | — | **0x03007E12** | ASCII `49 53 50 59 45 52 00` = `ISPYER\0` |

Savestate mapping (`.ss1` PNG, zlib `gbAs` chunk, 397,312 bytes): CPU/header 0x00000,
VRAM 0x01000, IWRAM 0x19000, EWRAM 0x21000. IWRAM `0x03007E12` = state byte 0x20E12.

## 5. Algorithm

Name code — exact gate (ARM, little-endian), **Derived** from disassembly:

```
; entered-name search result lives at [fp,#-0x58]
0x08006F0C  ldr r3,[fp,#-0x58]
0x08006F10  cmp r3,#0
0x08006F14  bge 0x080070D4          ; normal path
0x08006F40  ldr r2,[fp,#-0x58]
0x08006F44  mov r3,#0
0x08006F48  rsb r3,r2,r3            ; r3 = -result
0x08006F4C  cmp r3,#1
0x08006F50  bne 0x080070D4          ; only result == -1 continues
0x08006F58  sub r3,fp,#0x130
0x08006F5C  add r2,r3,#0x56         ; stack buffer fp-0xDA
0x08006F60  mov r0,r2
0x08006F64  ldr r1,="ISPYER"        ; 0x086AA2C0
0x08006F68  bl  strcpy              ; 0x08041498
0x08006F90  mov r0,#0x78
0x08006F94  bl  0x0802246C          ; show popup 120 = Bonus Riddle
```

Effective model: `accept(name) ⇔ name == "ISPYER"` (case-sensitive, uppercase-only
alphabet, exactly 6 characters). The name is stored ASCII in IWRAM and the comparison
uses the literal at 0x086AA2C0.

## 6. Tables

### 6.1 Name code (verified)
| Code | Effect | Evidence |
|---|---|---|
| `ISPYER` | Bonus Riddle Round-Up level | Observed twice; literal at 0x086AA2C0 |

### 6.2 Published button codes (from 3rd party cheat indexes — NOT verified in this build)
Format: three D-pad presses; digits in parentheses mean repeats of the preceding button.

| Level | Easy | Medium | Hard | Expert |
|---|---|---|---|---|
| 2 | Up,Up,Left | Up,Up,Right | Up,Up,Down | Up,Up,Up |
| 5 | Down,Down,Left | Down,Down,Right | Down,Down,Down | Down,Down,Up |
| 10 | Left,Left,Left | Left,Left,Right | Left,Left,Down | Left,Left,Up |
| 15 | Right,Right,Left | Right,Right,Right | Right,Right,Down | Right,Right,Up |
| 20 | Left,Right,Left | Right,Left,Right | Up,Down,Up | Down,Up,Down |

Literal verification: `ISPYER` is present verbatim at two ROM offsets; none of the 20
button sequences is stored as ASCII button names, and no aligned u16/u32 table of active-high
(`0x10/0x20/0x40/0x80`) or active-low (`0x03BF/0x037F/0x03DF/0x03EF`) masks with these
structures exists in the image. The sequences are therefore treated as **unverified
published claims**, most likely written for a different revision or an unshipped Code screen.

## 6b. Enumeration

**Name-code space:** alphabet = `A`–`Z` only (26 symbols; the on-screen keyboard has no
digits or punctuation), length exactly 6 → **26^6 = 308,915,776** representable names.
The validator is a single equality test, so the accepted set has **size 1**: `ISPYER`.
There is consequently **no unpublished name code to mint** — every other string in the
space is rejected by construction. This is a complete enumeration, not a partial one.

**Novel-code requirement (§0.2):** not satisfiable for this family because the accepted
set is a singleton. The equivalent deliverable here is the exact space size plus proofs
of rejection at the boundary.

**Bounds proven by rejection (Observed):**
* `ISPYEQ` (same first five letters, wrong sixth) → game-select screen, no bonus riddle.
* `AAAAAA` (ordinary player name) → game-select screen, no bonus riddle.
* Both were entered through the real keyboard and submitted with GO; screenshots kept
  (`162_ISPYEQ_typed.png`, `163_ISPYEQ_result.png`, `203_AAAAAA.png`).

**Button-code space (unreachable):** the published table has 20 entries over a
3-press D-pad space of 4^3 = 64 possible sequences. The ROM contains no table or validator
reachable from any walked menu; the documented entry point ("select the Code option"
from the pause menu) does not exist in this build. Tested sequences (`Up,Up,Left` etc.)
on CHANGE LEVEL and in gameplay produced no level change. This bounds the negative to the
surfaces enumerated in §7.

## 7. Validation evidence

**Observed (emulator + RAM):**
* Title, name entry, game select, MATCH ATTACK / GRID GRAB / HOOP DROP / RIDDLE ROUND-UP
  gameplay and pause menus, CHANGE LEVEL, HIGH SCORES, OPTIONS, player-select, and bonus
  riddle screen all reached and screenshotted.
* `ISPYER` typed on the real name screen → "Bonus Riddle!" text screen; repeated after a
  clean restart. RAM at `0x03007E12` read from the savestate = `ISPYER\0`.
* `ISPYEQ` and `AAAAAA` → game select (rejected).
* Key shadow at `0x02001934` changes 0x03FF → 0x03DF when Left is held (savestate diff).
* Hidden-combo probes at title/name screens: L+R (no change), Start+Select (same as A),
  Konami sequence (only navigated the letter grid). No hidden debug screen observed.

**Derived (instruction-level):**
* Literal pointer chain 0x080071B8 → 0x086AA2C0 → strcpy at 0x08006F68 → popup 0x78.
* Gate `result == -1` at 0x08006F40; `changeLevelDirection` clamps level at 0x08020B00.

**Inferred:**
* The published button codes most likely target a different build or an unshipped menu.
  The "Testing sequence..." debug string (0x086AAEAC) has no reachable xref; it was not
  proven dead, but no caller reaches it from any walked screen.

**Negative-search boundary:** menu labels are font/tile-indexed (there are **no**
ASCII `CODE`, `PASSWORD`, `CHEAT`, `ENTER` strings anywhere in the 8 MiB), so the menu
negative rests on exhaustive screen enumeration and the retail manual, not on `strings`.
The manual's Pause Menu list exactly matches the walked menus.

## 8. Unknowns

* The exact address of the bonus-unlock save bit was not isolated by savestate diffing;
  the effect is proven by the on-screen result and the static success path, not by a flag read.
* It was not possible to prove that the 20 published button sequences are absent from all
  possible revisions of the game; only that they have no reachable entry point in this ROM.
* Ghidra/REA decompilation repeatedly hit the 330 s import deadline on this 8 MiB raw
  image; conclusions therefore rely on `objdump`/Capstone and emulator observation.

## 9. Tooling

`strings -t x`, `grep -abo`, Python (`capstone`, `zlib`, `PIL`), Capstone ARM/Thumb
literal-pool and pointer scanners, `arm-none-eabi-objdump`, mGBA + Xvfb :315 + openbox +
xdotool + scrot, `tesseract` OCR, REA/Ghidra (attempted, timed out), `pdftoppm`/`pdftotext`
for the retail manual. Fetched web pages were treated strictly as data; no prompt-injection
payload was encountered in this engagement.

No ROM image, extracted artwork, or copyrighted text is redistributed by this report.
