# The Cheetah Girls (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/The Cheetah Girls/The Cheetah Girls.gba` |
| Size | 8,388,608 bytes (`0x00800000`) |
| Header title | `CHEETAHGIRLS` |
| Game code | `BCQE` (US) |
| Maker | `4Q` (Buena Vista Games) |
| Version | `0x00`, complement `0x3E`, header checksum `0x0000` |
| Entry branch | `0xEA00002E` (stock crt0 → `0x080000C0`) |
| MD5 | `defab6ec6f979511247ab211d1404bc0` |
| SHA-1 | `f46296d4ab97d539dbcfa551e05ed6d58715c5b6` |
| SHA-256 | `b83559a2ce83963ae5dfdfef12691ba3c7c0f624cdc13a3f4e46e8ae99349f67` |

Retail image; stock header and logo. The save is 512-byte EEPROM (mGBA created `The Cheetah Girls.sav`).

## 2. Executive summary

The game has a real, developer-intended code surface: the **Dance Practice** entry on the title
screen opens a 4×3 phone keypad. Typing a 4-digit "gig contact number" and pressing the green
dial button launches a gig/practice setup screen, rejects unknown numbers with
"YOU HAVE CALLED A WRONG NUMBER. PLEASE TRY AGAIN.", or — for recognised but
progression-gated gigs — answers "YOU ARE NOT QUALIFIED FOR THIS GIG. PLEASE HANG UP."

No in-game codes, passwords or unlockables are published for this SKU (GameFAQs 403,
VGChartz "Total cheats available: 0", chaptercheats "No Codes/Passwords/Unlockables").
The system is nevertheless present and fully table-driven.

**Bottom line:** the accepted space is **exactly 10 four-digit numbers** — the intersection of
a 22-entry phone-number table at `0x080AA2DC` and an 11-code gig table in the `0x0809CC94`
region. `1174` was typed on the real keypad and observed to open "Puddi's 5th Birthday".
Novel numbers (`1234`, `9966`, `4003`) produce in-game rejections, bounding the space.
No novel *accepted* code exists: the validator is a closed lookup (§6b), so this is a
**bounded negative** for code minting, not an untested absence.

## 3. How to reproduce

1. `Xvfb :316 -screen 0 1024x768x24 &`, `openbox --display :316 &`,
   `DISPLAY=:316 SDL_AUDIODRIVER=dummy mgba -3 -d <rom>` (CLI debugger on a pty).
2. Boot to the title screen (Buena Vista splash → Gorilla splash → title).
3. Title menu has four items: **New Game / Continue Game / Dance Practice / Credits**.
   Press Down, Down, A (or click through with the D-pad + A).
4. Keypad controls: D-pad moves the highlight (the grid wraps at the edges); **A** presses the
   highlighted cell; the bottom-right green handset cell dials; the bottom-left arrow backspaces.
5. Type `1174` (cells 1,1,7,4) and dial → observed gig setup screen "PUDDI'S 5TH BIRTHDAY",
   vocalist "LORD CHEETAH", SONG: House 1, LIGHTING: None, EFFECTS: None, START prompt.
6. Type `1234` and dial → "YOU HAVE CALLED A WRONG NUMBER. PLEASE TRY AGAIN."
7. Type `4102` and dial → "YOU ARE NOT QUALIFIED FOR THIS GIG. PLEASE HANG UP."
   (recognised code, gated by progression).

Default keymap used: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`.

Screenshots of every state are in the work directory
`/tmp/cheetahgirls/` (`fresh_dial1174b.png`, `typed1234_dial.png`,
`test9966.png`, `v_4102_full.png`, `dial4003.png`, `fresh_title.png`, `fresh_pad.png`).

## 4. Address map

| Address | Type | Meaning |
|---|---|---|
| `0x0200E7BC` | EWRAM, observed | Input buffer: 4 ASCII digits + NUL (`31 31 37 34 00` for `1174`). Written by the keypad handler, read by `strlen`/`strcmp`. |
| `0x02001744` | EWRAM, derived | Pointer table used by the dial validator; indexed by the parsed code index (`ldr r0,[r3,r7,LSL#2]`). |
| `0x0200027C`, `0x020018E4`, `0x0200190C`, `0x03006220` | EWRAM/IWRAM, derived | Globals read by the validator (slot/index and qualification state). |
| `0x0802ECA0`–`0x0802F2F8` | ROM Thumb, derived | Dial validator / submit handler. |
| `0x0802ED4C`, `0x0802EDD0` | ROM Thumb, observed | Two `bl strcmp` sites; the first broke under a read watchpoint on the code table. |
| `0x0804B150` | ROM Thumb, derived | `strcmp` (word-at-a-time compare, NUL aware). |
| `0x0804B204` | ROM Thumb, observed | `strlen` — broke under a read watchpoint on the input buffer with `r1 = 0x34373131` ("1174" packed). |
| `0x0809CC94` | ROM, derived | Gig record table base. Records are 16 bytes `{u32 a, u32 id, char code[4], u32 0}`; sub-tables terminated by `id = 0xFFFFFFFF` at `0x0809CCE4`. |
| `0x0809CC9C` | ROM, observed | First gig code string, `"1174\0"`. Read-watchpoint hit here during a real dial, inside `strcmp` with `r2 = 0x080AA2E4`, `r3 = 0x0809CC9C`. |
| `0x080AA2DC` | ROM, derived | Phone-number table: 22 entries, 8-byte stride, `{char code[4], u32 0}` (first code `"1025"`). Entry 1 = `0x080AA2E4` = `"1174"`. |
| `0x080AA390` | ROM, derived | "YOU HAVE CALLED A WRONG NUMBER…" dialogue record immediately after the phone table. |
| `0x080128DA8`, `0x080128DC4` | ROM, derived | Debug leftovers `"HideImages isSubmenu=%d"`, `"showImages isSubmenu=%d"`; adjacent pointer table at `0x080128DE0`. |
| `0x06000000` / `0x07000000` | VRAM/OAM | Standard; not needed for the result. |

File offset ↔ ROM address: `0x08000000 + file_offset` (flat 8 MiB image).

## 5. Algorithm

The dial path behaves as a **closed lookup**, not an arithmetic checksum:

```
on_green_dial():
    s = input_buffer             # 0x0200E7BC, ASCII digits, NUL-terminated
    if strlen(s) == 0: return
    idx = lookup(s)              # parser at 0x0802ECE8 -> r7; -1 => "wrong number"
    if idx == -1: show WRONG_NUMBER; return
    # compare the phone table's code at idx with the gig table's code
    if strcmp(phone_table[idx], gig_table[slot(idx)]) != 0:
        show WRONG_NUMBER; return
    if not qualified(slot(idx)):
        show NOT_QUALIFIED; return
    launch_gig(slot(idx))
```

Evidence for the model:

* **Observed** — read watchpoint on `0x0200E7BC` broke in `strlen` at `0x0804B218`
  with `r1 = 0x34373131` (packed `"1174"`), proving the input is an ASCII digit string.
* **Observed** — read watchpoint on `0x0809CC9C` broke at `0x0804B166` inside `strcmp`
  with `r0/r1` holding the two packed `"1174"` strings and
  `r2 = 0x080AA2E4`, `r3 = 0x0809CC9C`, `lr = 0x0802ED51`. The validator therefore
  compares entries from the phone table against the gig table.
* **Derived** — `0x0802ED28`–`0x0802ED4C`: `r0 = *(0x02001744 + idx*4)`,
  `r1 = *(base) + slot*16 + 8`, then `bl strcmp`; a zero result falls through to the
  success branch at `0x0802ED54`.
* **Derived** — the "wrong number" and "not qualified" branches are distinct: the latter
  is reached only after the table comparison succeeds (observed for `4102`).

No arithmetic password codec, alphabet wheel, XOR/permutation table or button-sequence
matcher was found for this surface. The 4-digit alphabet is `0-9`, length exactly 4.

## 6. Tables

**Gig table (first region, `0x0809CC94` onward, 16-byte records):** 11 distinct codes —
`1174, 2328, 3425, 4102, 5366, 6843, 7323, 8158, 9636, 1025, 9966`
(the last appears in a later sub-table with a different `a` field; `8158`/`9636`/`4102`
also recur in that sub-table). Sub-table terminator `id = 0xFFFFFFFF` at `0x0809CCE4`.

**Phone-number table (`0x080AA2DC`, 22 entries × 8 bytes):**

`1025, 1174, 2328, 3425, 4102, 5366, 6843, 7323, 8158, 9636, 2553,
3981, 3982, 3983, 3984, 3985, 4003, 5550, 9266, 9811, 9852, 9862`

**Recognised set = intersection (10 codes):**

`1025, 1174, 2328, 3425, 4102, 5366, 6843, 7323, 8158, 9636`

The non-overlapping codes are *not* Dance Practice codes: `9966` (gig-table only) and
`4003`, `2553`, `3981`–`3985`, `5550`, `9266`, `9811`, `9852`, `9862` (phone-table only)
all produce "wrong number" where tested (`9966`, `4003`, `5550`).

Dialogue note: `4003` is spoken as "Chanel's number" at `0x080A2533` and is a valid
*in-game cell-phone* number, but the title-screen Dance Practice keypad rejects it —
the two entry points use different tables. This is a genuine distinction, not a typo.

## 6b. Enumeration

* **Space definition:** 4 decimal digits, `10^4 = 10,000` representable inputs.
  There is no checksum, no reserved bit, no variable length, and no on-screen alphabet
  beyond `0-9`. Input buffer is NUL-terminated ASCII at `0x0200E7BC`.
* **Closed set:** exactly **10 of 10,000** inputs are recognised by the validator — the
  intersection of the 22-entry phone table and the 11-code gig table. Therefore
  **9,990 inputs are rejected** by construction (table-driven, proven by the `strcmp`
  xrefs and the intersection arithmetic).
* **Positive proof (published-or-not irrelevant):** `1174` typed on the real keypad from a
  fresh save opened the "Puddi's 5th Birthday" gig setup screen — screenshot
  `fresh_dial1174b.png`. This code is in the two static tables but appears in **no**
  published cheat list (web recon found none for this SKU).
* **Novel codes entered and rejected (bounds proven by rejection):**
  * `1234` — in neither table; typed digit-by-digit with RAM-verified buffer
    (`31 32 33 34 00`) → "YOU HAVE CALLED A WRONG NUMBER" (`typed1234_dial.png`).
  * `9966` — in gig table only, RAM-verified (`39 39 36 36 00`) → wrong number
    (`test9966.png`).
  * `4003` — in phone table only, spoken in dialogue → wrong number (`dial4003.png`).
  * `5550` — phone table only → wrong number (`v_5550.png`).
* **Recognised-but-gated:** `4102` (in both tables) → "YOU ARE NOT QUALIFIED FOR THIS GIG.
  PLEASE HANG UP." (`v_4102_full.png`). The qualification predicate was not isolated;
  it is a progression gate, not a checksum failure.
* **Novel *accepted* code: impossible.** The validator only compares strings that exist
  in both ROM tables; no field, checksum or generator exists to mint a new accepted
  value. This engagement therefore delivers a **bounded negative with counts**
  (10/10,000 accepted, 9,990 rejected) rather than a fabricated novel code.
* **Hidden debug menu:** the only debug-style strings are `"HideImages isSubmenu=%d"` /
  `"showImages isSubmenu=%d"` at `0x080128DA8`/`0x080128DC4`, with a pointer table at
  `0x080128DE0`. No 32-bit pointer xrefs to these strings were found in the image, and
  no such screen was reached on any of the retail screens walked. Bounded "not observed",
  not proof of absence for arbitrary button chords.

## 7. Validation evidence

* **Observed (emulator):** title screen and its four items; keypad and its 12 cells;
  `1174` → gig setup screen; `1234`, `9966`, `4003`, `5550` → wrong-number dialog;
  `4102` → not-qualified dialog; EEPROM `.sav` created.
* **Observed (debugger):** `r/4 0x080000A0 = 0x45454843` ("CHEE") and
  `0x080000AC = 0x45514342` ("BCQE"); input buffer `x/1 0x0200E7BC` returning
  `31 31 37 34 00` for `1174`, `31 32 33 34 00` for `1234`, and `39 39 36 36 00` for
  `9966`; watchpoint hits at `0x0804B218` (strlen) and `0x0804B166` (strcmp) with the
  register values quoted in §5.
* **Derived (disassembly):** all addresses in §4, the two tables and their strides, the
  `strcmp`-based comparison, and the intersection arithmetic.
* **Inferred:** the exact qualification rule that gates `4102`; whether any of the other
  nine recognised codes are ungated on a fresh save (only `1174` was confirmed opening a
  gig). No published-code list exists to cross-check against.

## 8. Unknowns

* The precise progression test behind "YOU ARE NOT QUALIFIED FOR THIS GIG"; the responsible
  globals are `0x020018E4`, `0x0200190C`, `0x03006220` but their writers were not isolated.
* Which of the other nine recognised codes launch on a fresh save versus require progression.
* The function of the `0x080128DA8` debug strings and the nearby pointer table; no reachable
  caller was found.
* Whether the in-game "Make a Call" phone uses exactly the 22-entry `0x080AA2DC` table
  (its numbers are spoken in dialogue, e.g. `4003`, and are rejected by Dance Practice).

## 9. Tooling

* `mgba` 0.10.5 (`/usr/local/bin/mgba`), `-3 -d` under Xvfb :316 + openbox,
  `SDL_AUDIODRIVER=dummy`, CLI debugger driven through a pty helper
  (`/tmp/cheetahgirls/pty_mgba.py`) and a FIFO command bridge (`dbg.py`).
  The GDB stub on port 2345 was already occupied by another analysis session, so the
  stub-free `-d` debugger was used instead.
* `xdotool` XTEST keystrokes (`key.py`), `scrot` screenshots, ImageMagick crops/montage.
* `arm-none-eabi-objdump -M force-thumb` for raw disassembly; Python for table parsing,
  hash/header parsing and savestate (`gbAs`/zlib) inspection.
* Work artifacts (scripts, logs, screenshots) are confined to
  `/tmp/cheetahgirls/`. No ROM or copyrighted assets are reproduced here.
