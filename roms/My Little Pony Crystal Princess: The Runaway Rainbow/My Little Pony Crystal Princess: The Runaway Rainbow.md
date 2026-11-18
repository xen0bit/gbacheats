# My Little Pony Crystal Princess: The Runaway Rainbow (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `My Little Pony Crystal Princess: The Runaway Rainbow.gba` |
| Size | 4,194,304 bytes (0x400000) |
| Header title | `MYLITTLEPONY` |
| Game code / maker | `BL6E` / `78` (`file(1)` reports "BL6E78, Rev.00") |
| Version | 0x00 |
| Entry word | `0xEA00002E` → stock branch to `0x080000C0` (no cracktro) |
| Fixed byte 0x96 | present; complement byte 0x1F; header checksum 0x0000 |
| Embedded GBA headers | exactly one Nintendo logo hit, at file offset 0x4 (no multiboot/2-in-1/trainer) |
| MD5 | `ddd0670792619198933dcef3571428b3` |
| SHA-1 | `41c2a6940ed285c5f5c1604e01b2162fd2a8af60` |
| SHA-256 | `e88bbb0e6e492c61e79bd513702319c3662c9ef41decf7dd31a159c9df824191` |

No scene patch, trainer, or appended image. The only ASCII strings are a C++ runtime
(`Z:\Source\ByteCodeInterpreter\ByteCodeInterpreter.cpp` at `0x080090E0`, exception
strings at `0x0808C43B+`); **all UI text is u16/tile-indexed**, so `strings` finds none
of it. The game runs a custom bytecode VM (Webfoot Technologies).

## 2. Executive summary

The title menu offers **New Game** and **Password**. The Password screen is a 9-slot
numeric (0–9) entry with ACCEPT (A) / CANCEL (B), and it implements a real,
developer-intended unlock code system.

The validator is ARM/Thumb code at **`0x0800CBD6`**, called from the ACCEPT path at
`0x0800CD82`. It is *not* a checksum: it is a **per-position symbol gate**. Each of the
nine slots has its own 16-symbol alphabet stored as a u16 table in ROM at
`0x08120B96 + 34*i`. For slot `i < 8` the code accepts digit `d` iff the **ASCII code of
`d` (`0x30+d`)** occurs anywhere in that slot's alphabet; for slot `8` it must occur in
the 5-entry table at `0x08120CA6`. This yields an exact accepted space of
**1,536 nine-digit codes** (Cartesian product of the per-position digit sets).

Submitting an accepted code shows **"Accepted"**, clears the digit buffer, and enters
the game's main menu (Rarity's Adventure / Mini Games / Princess Gallery). The **last
digit selects the chapter**: 6 → Chapter 3 "Rarity Visits Ponyville", 9 → Chapter 2
"Rarity Meets the Breezies" (verified by screenshots). A rejected code shows
**"Denied"** and stays on the entry screen.

All published-code searches were attempted and produced **no published code list** for
this SKU (see §8); therefore every valid code reported here is novel.

## 3. How to reproduce

* Emulator: mGBA (`mgba -3`), display `:318`, `SDL_AUDIODRIVER=dummy`, Xvfb 1024×768, openbox.
* Keymap (mGBA SDL defaults): A=`x`, B=`z`, Start=`Return`, D-pad=arrow keys.
* Intro is long: THQ → Webfoot → title logo → title menu (~15–20 s total); do not
  press keys during the fade or they are swallowed.
* Path: **Password** (Down, A) → 9 slots, all 0 → adjust digits with Up/Down, move with
  Left/Right → **A** (ACCEPT) → "Accepted" → (≈10 s transition) main menu →
  "Rarity's Adventure" (A) → chapter book → gameplay/dialogue.
* B on the Password screen cancels. In a minigame, Start gives
  "Game Paused / Continue / Retry / Quit".
* Codes tested in-game (patch + on-screen verification):
  `178628669` (novel, ACCEPT, Chapter 2), `428628479` (ACCEPT, Chapter 2),
  `174698466` (ACCEPT, Chapter 3), `124623366` (ACCEPT, Chapter 3),
  `000000000`, `999999999`, `124623360`, `024623366`, `124623365`, `101000106`
  (all DENY). Full per-position sweep in §6b.

Screenshot-and-RAM workflow used for reliability: savestate at the blank Password screen
(raw `gbAs` chunk = 397,312 bytes), patch the nine u32 digits at EWRAM `0x0203FF38`
(state offset `0x60F38`), reload with F1, move the cursor across all slots and back to
force a glyph redraw, then press A. This is necessary because direct RAM patching does
not refresh the digit sprites until a cursor event occurs.

## 4. Address map

| Item | Address | Evidence |
|---|---|---|
| Digit input array (9 × u32) | EWRAM `0x0203FF38` | Observed: changing slot 1 with Up×5 changed `[0x203FF38]=5`; slot 2 → `[0x203FF3C]`; patch+redraw reproduced the displayed digits exactly |
| Password screen state struct | EWRAM `0x0203FF30` | `digits[]` at struct+8; per-digit draw state at struct+0x30; handler registers observed with `r5=r6=0x0203FF30` |
| Password validator | ROM `0x0800CBD6` | Thumb disassembly: 9-slot loop, per-position u16 table lookups, returns 0/1 |
| Validator literal pool | ROM `0x0800CE94`–`0x0800CEC0` | `0x08120B28` (global `g`), `0x0300213C`, etc. |
| ACCEPT handler (calls validator) | ROM `0x0800CD76`–`0x0800CD88` | `bl 0x800CBD6; cmp r0,#0; bne <deny path>` |
| Digit Up/Down/Left/Right handler | ROM `0x0800CC6E` | reads key bits, clamps selected slot 0–8, increments/decrements `[struct+8+4*slot]` |
| Digit draw routine | ROM `0x0800CF32` | loops `r4=0..8`, loads `[struct+4*i+8]`, calls `0x0800CAD6` |
| Global `g` (font/VM object) | ROM `0x08120B28` | literal at `0x0800CE98` |
| Glyph/ASCII table `T1` (16 × u16) | ROM `0x08120B4C` | `0x30..0x39,0x41..0x46` = `0123456789ABCDEF` |
| Position alphabets `A[0..8]` (17 × u16 each) | ROM `0x08120B96` | 16 symbols + `0x0000` terminator; dumped in §6 |
| savestate RAM offsets | state `0x19000`=IWRAM `0x03000000`; `0x21000`=EWRAM `0x02000000` | §16.13 method; state length 0x61000 |

## 5. Algorithm

Reimplementation of `validate(code)` (bit-exact with `0x0800CBD6`):

```
g = 0x08120B28
T1[j] = u16[g+0x24 + 2*j] for j in 0..15        # "0123456789ABCDEF"
A[i][j] = u16[g+0x6E + 34*i + 2*j] for i in 0..8, j in 0..15

valid = true
for i in 0..7:
    d = digit[i]                              # 0..9, from input array
    found = false
    for j in 0..15:
        if A[i][j] == T1[d]:                  # ASCII(d) must be in A[i]
            found = true
    if not found: return REJECT
# slot 8 uses a 5-entry table
found = false
for j in 0..4:
    if A[8][j] == T1[digit[8]]: found = true
if not found: return REJECT
return ACCEPT
```

Notes: the check is *position-dependent symbol membership*, not addition/XOR. The
alphabets contain 'x' (`0x78`) filler entries that are deliberately **not** in `T1`,
so digits indexing those entries are rejected. There is no cross-slot constraint, so
the accepted set is the plain Cartesian product of the per-slot sets (§6b).

On ACCEPT the handler draws "Accepted", resets the nine digit words to 0, fills the
digit sprite state with `0xFF`, and switches the VM to the main-menu screen state
(`0x63`). The chapter shown by "Rarity's Adventure" is selected from the last digit
(9 → Chapter 2, 6 → Chapter 3, observed).

## 6. Tables

`A[i]` (16 u16 symbols at `0x08120B96 + 34*i`; `A[8]` has 5 active entries at
`0x08120CA6`):

| i | alphabet (16 symbols) | accepted digits (observed = derived) |
|---|---|---|
| 0 | `Q1Fx4JLxNP5STVWx` | 1, 4, 5 |
| 1 | `BDGxHJKxNPQ72CXx` | 2, 7 |
| 2 | `WBCxJ4HxL8PRSTZx` | 4, 8 |
| 3 | `B6XxGHYxKRSTM8Wx` | 6, 8 |
| 4 | `2CZxHJLxRS9VWXYx` | 2, 9 |
| 5 | `BC8xHKJxLMP3SXWx` | 3, 8 |
| 6 | `SB3xH7JxM6PQRT4x` | 3, 4, 6, 7 |
| 7 | `B7FxGKLxPQ6TVXYx` | 6, 7 |
| 8 | `B96HL` | 6, 9 |

`T1 = 0123456789ABCDEF` at `0x08120B4C`.

Chapter selection (observed, last digit): `6 → Chapter 3`, `9 → Chapter 2`.

## 6b. Enumeration

* **Input space:** 9 slots × 10 digits = **1,000,000,000** representable strings.
* **Accepted space:** `3×2×2×2×2×2×4×2×2 = 1,536` codes (exact; derived from the ROM
  tables and confirmed exhaustively per position, below).
* **Novel code generated and accepted in-game:** **`178628669`**.
  On-screen result: "Accepted" (screenshot `novel3_accepted.png`), followed by the
  main menu; derived chapter 2. This code appears in no published list — none exists
  for this SKU (§8). Other accepted novel codes: `428628479`, `174698466`,
  `124623366`, plus 1,531 others in the enumerated space.
* **Bounds proven by rejection:** an exhaustive per-position sweep was run against the
  ROM (hold all other digits at a valid value, vary one digit 0–9, submit, read
  "Accepted"/"Denied"). Result string, digit 0…9 (`A`=accepted, `.`=denied):

  ```
  pos0: .A..AA....    pos1: ..A....A..    pos2: ....A...A.
  pos3: ......A.A.    pos4: ..A......A    pos5: ...A....A.
  pos6: ...AA.AA..    pos7: ......AA..    pos8: ......A..A
  ```

  This matches the derived sets exactly, so every one of the 1,000,000,000 − 1,536
  other strings is rejected. Additional explicit rejections: `000000000`,
  `999999999`, `101000106`, `124623360`, `024623366`, `124623365`.

## 7. Validation evidence

* **Observed:** title menu, Password entry (9 slots), "Denied", "Accepted",
  main menu (3 entries), chapter books 1/2/3, gameplay/dialogue, gameplay scene,
  "Game Paused / Continue / Retry / Quit", Mini Games list (Matching Kites,
  Breezie Hide 'n Seek, Rescue Buddies, Caterpillar Catch, …), Matching Kites
  playfield, Princess Gallery, Credits. Every transition was paired with a
  savestate (`st_*.bin`) and RAM dumps; the digit buffer and its 9→0 clear on ACCEPT
  were observed in RAM (`0x0203FF38`…`0x0203FF58`).
* **Derived:** validator loop and per-position table addresses from Thumb disassembly
  (`0x0800CBD6`, `0x0800CC00`–`0x0800CC6C`); table contents dumped from ROM; model
  agrees with all 90 per-position tests and all additional codes.
* **Inferred:** the exact role of the 5-entry `A[8]` table beyond chapter selection
  (other `A[8]` symbols `B/H/L` are unreachable because only digits 0–9 can be typed).

## 8. Unknowns / negative results (bounded)

* **Published codes:** `websearch` returned no results for 8 queries (titles +
  "password"/"cheat"/"codes"/"walkthrough"); direct fetches of GameFAQs (403),
  Google (JS-only), DuckDuckGo (bot challenge), Bing via `r.jina.ai` (irrelevant
  results) produced no usable list. No code was found in `web.archive.org` snapshots
  tested (404). No prompt-injection payload was encountered in fetched content.
* **No button-code system:** a bounded scan for u16 runs of active-high key masks
  (A=1,B=2,Select=4,Start=8,Right=0x10,Left=0x20,Up=0x40,Down=0x80,R=0x100,L=0x200)
  found 835 runs ≥4 but all are data coincidences (long runs of 0x1/0x2/0x100 in
  graphics/audio), not an action branch table; no hidden debug screen was reachable
  from any walked menu, and no ASCII `DEBUG`/`CHEAT` string exists in the image.
* **Save data:** no non-empty `.sav` is produced; the password is the unlock path, not
  a save password.
* The mapping from `A[8]` symbols other than `6`/`9` to chapters could not be exercised
  because the on-screen keypad only offers digits 0–9.

## 9. Tooling

* `arm-none-eabi-objdump -M force-thumb` — validator/handler disassembly.
* Ghidra 12.1.4 via REA MCP (`open_binary`, `procedure_address`, `analyze_function`)
  used for initial function discovery and evidence records.
* Python 3 + capstone 5.0.7, Pillow; `binutils`, `xxd`, `strings`, `file`, `scrot`,
  `convert`, `tesseract`.
* Custom scripts in `/tmp/opencode/mlp/`: `ui.py` (keypress/screenshot),
  `stateutil.py` (savestate PNG `gbAs` decode, RAM read, diff),
  `patch.py` (write 9 u32 digits into savestate), `verify.py` (model + accept/deny
  classifier), `gdbc.py` (persistent GDB controller, ultimately unused because the
  port was contended), `fasttest.py` (batch tester).
* Savestate method per §16.13: PNG `gbAs` chunk zlib-decompressed to a 397,312-byte
  raw state; IWRAM at `0x19000`, EWRAM at `0x21000`.
