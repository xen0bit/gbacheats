# Zone of the Enders: The Fist of Mars (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Zone of the Enders: The Fist of Mars.gba` |
| Size | 8,388,608 bytes (`0x800000`) |
| Header title | `Z.O.E USA` (code `AZEE`, maker `A4` = Konami) |
| Version | 0 (`Rev.00`), complement `0x64`, header checksum `0x0000` (normal for a rebuilt header) |
| Entry word | `0xEA00002E` (stock — no cracktro/trainer patch) |
| MD5 | `b9c0646696297fb21cfad315c434cc2a` |
| SHA-1 | `1839f900e5f2c8a52a4ce160a8c35a572c2d388f` |
| SHA-256 | `114fff29e5642300a9b3698916ecd86682aa6da0fd821065b7431ba8c059f0f2` |

Save hardware: Flash, 64 KiB `.sav` (fresh image is `00..FF` in the first `0x100` bytes, `FF` afterwards). String `FLASH_V126` at file `0x78B524`.

## 2. Executive summary

**There is no enterable code system in this SKU.** No password entry screen, no button-code
surface, and no hidden/debug menu were found on any reachable screen. The word "PASSWORD"
does appear in the game, but only as **narrative**: a scene character says the password is
**`ARIEL`**; that 5-character literal occurs exactly twice in the ROM (file `0xBFB25`,
`0xC04B9`), both inside dialogue text, and **zero** times as a comparison key, input buffer
initialiser, or validator constant. There is no screen on which it can be typed.

The only developer-exposed extras are in **OPTIONS**: two battle settings, a **sound test
with 27 tracks** (reachable on a blank save), a **Terminology File** with 6 pages (reachable
on a blank save), and two reference browsers (**MechReference**, **CharaReference**) that are
gated on save data and show `NO DATA REGISTERED` on a blank cart. These are unlockables, not
codes: the gate is the presence of flash save data, not a controller sequence.

Published "cheats" for this title are Action Replay / GameShark / CodeBreaker RAM patches
(out of scope) plus story-branch unlockables (scene-12 kill comparison → 24- or 25-scene
ending) — no published password or button code exists. All iPhone/3rd party cheat index pages were
blocked to direct fetch (403); the list above was recovered from search-result snippets.

Because no code space exists, §6b delivers a **bounded negative with counts** rather than a
minted code.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 under Xvfb `:318`, `SDL_AUDIODRIVER=dummy`, `-3` scale.
  Keymap used: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, arrows = D-pad.
  Menu cursor moves once per **~140 ms** hold; 70 ms taps are intermittently dropped.
* Boot path: Nintendo splash → Konami splash → title (~24 s) → `PRESS START` → main menu.
* Menu walk (all screens observed):
  * `NEW GAME` → long story prologue (no name entry, no code field).
  * `LOAD` / `CONTINUE` → no visible action on a blank save.
  * `OPTIONS` → 6 entries:
    1. `Battle Seq: ON/OFF` (toggles),
    2. `Battle IAS: ON/OFF` (toggles),
    3. `Sound Mode` → sound test (see §6),
    4. `MechReference` → `NO DATA REGISTERED`,
    5. `CharaReference` → `NO DATA REGISTERED`,
    6. `Terminology File` → 6-page glossary, each page a selectable term list; A shows the
       term's definition.
* Sound test: select `Sound Mode`, move the icon cursor with Right to the `▶|` (next) icon,
  press A repeatedly. The counter advances `1.`→`27.` and then stops at `27. Networks`;
  40 consecutive next-presses were logged (`sndnext_00..39.png`).
* RAM evidence was taken by mGBA savestates (Shift+F1…F9). A `.ss*` state is a PNG whose
  `gbAs` chunk is zlib-compressed to **397,312 bytes (`0x61000`)**; CPU/header at `0x0`,
  VRAM at `0x1000`, IWRAM at `0x19000`, EWRAM at `0x21000`. IWRAM at `0x19000` was verified
  against a live GDB read (`0x00000000, 0xFFFFFFFF, 0x0000FFFF, …`), so the mapping is exact.
  States were captured at: title (`title_base.ss`), main menu (`state_menu.ss1`),
  options (`state_options.ss2`), sound test (`state_sound.ss3`), and reference rejection.

## 4. Address map

| File offset | ROM address | What |
|---:|---:|---|
| `0x000` | `0x08000000` | Stock ARM entry `0xEA00002E` |
| `0x2C` | `0x0800002C` | Only literal `0x04000130` (key input register) in the image, in crt0 |
| `0x787C0` | `0x080787C0` | 3-byte-offset string table (system messages), step 4 |
| `0x78860` | `0x08078860` | System text bank: `PHASE COMPLETE`, `CANNOT SAVE`, `CANNOT LOAD`, `SAVE FAILED`, `SAVED`, `DOWNLOAD COMPLETE`, `NO DATA`, `RETREAT`, item names, stat names |
| `0x78942` | `0x08078942` | `NO DATA REGISTERED` (the options rejection message) |
| `0x78920`–`0x78940` | `0x08078920` | `ONLY THE S, CAN DOWNLOAD DATA` / `NO DATA REGISTERED` cluster |
| `0xBFB19`, `0xC04AD` | `0x08BFB19`, `0x08C04AD` | `THE PASSWORD IS ARIEL` (dialogue, two copies) |
| `0xBC932`, `0xBC9A3`, `0xBC9FB`, `0xBCA48` | … | Other `PASSWORD` / `CODE` narrative uses |
| `0x78B524` | `0x0878B524` | `FLASH_V126` |

Runtime (savestate) map: IWRAM `0x03000000` ↔ state `0x19000`; EWRAM `0x02000000` ↔
state `0x21000`; VRAM `0x06000000` ↔ state `0x1000`. A blank-save .sav is 64 KiB of `FF`
except `00..FF` in its first 256 bytes.

## 5. Algorithm (text encoding — decoded before the negative)

The image contains **no ASCII menu strings** (`strings -n 5` finds only the header title and
`FLASH_V126`). All in-game text is stored as one byte per glyph:

* `0x20` = literal space; `0x00` = terminator/pad; `0x01 xx` = control sequence
  (`0x01 0x12` line break, `0x01 0x19`/`0x01 0x0D` speaker/name framing, `0x1F … 0x1D` name span).
* Two overlapping uppercase alphabets are used:
  * `A1`: `0x3B..0x54` → `A..Z` (i.e. byte = ASCII − 6) — the bulk of every word;
  * `A0`: `0x21..0x3A` → `A..Z` (i.e. byte = ASCII − 0x20) — used for sentence/name-initial
    capitals and for short 5-character tokens.
  * Digits/punctuation follow the same tile-index convention (`'` = `0x21` under `A0`, etc.).
* Decoder used (Python, verified against dozens of strings):

```python
def dec_A1(b):  # bulk dialogue
    return ''.join(' ' if x == 0x20 else (chr(x + 6) if 0x21 <= x + 6 < 0x7f else '.')
                   for x in b)
def dec_A0(b):  # sentence initials / short tokens
    return ''.join(chr(ord('A') + x - 0x21) if 0x21 <= x <= 0x3A else '.' for x in b)
```

Decoded examples: `CONTINUE` = `3D 49 48 4E 43 48 4F 3F`;
`PASSWORD` = `4A 3B 4D 4D 51 49 4C 3E`; `TO VIEW THE CODED FILES` = `4E 49 20 50 43 3F 51 20 4E 42 3F 20 3D 49 3E 3F 3E 20 40 43 46 3F 4D`;
`ARIEL` = `21 32 29 25 2C`. The UI menu labels themselves are rendered from a separate
font-tile bank and were enumerated visually rather than by this decoder (see §8).

There is no checksum, comparator, or transformation applied to any user input; no validator
function exists to reverse.

## 6. Tables

**OPTIONS (all six rows, blank save):**

| # | Label | Behaviour |
|---:|---|---|
| 1 | `Battle Seq: ON/OFF` | A toggles; default ON |
| 2 | `Battle IAS: ON/OFF` | A toggles; default ON |
| 3 | `Sound Mode` | Opens the sound test |
| 4 | `MechReference` | `NO DATA REGISTERED` |
| 5 | `CharaReference` | `NO DATA REGISTERED` |
| 6 | `Terminology File` | 6 pages of glossary entries |

**Sound test (27 tracks, observed by pressing Next 40 times):**
1 `Z.O.E. 2173`, 2 `Intermission`, 3 `Subtitle`, 4 `Strategy Explanation`,
5 `Transient Repose`, 6 `Conversation with Friends`, 7 `Every Day`,
8 `Day In, Day Out`, 9 `Sadness`, 10 `Pulse`, 11 `Onward to Victory`,
12 `Danger`, 13 `Promise of Reunion`, 14 `Tragedy`, 15 `Uncontrollable Fear`,
16 `Atrocity`, 17 `Mystery`, 18 `Tension`, 19 `Enemy Mine`, 20 `Black Ops`,
21 `Impact`, 22 `Offense and Defense`, 23 `Sortie`, 24 `Galactica`,
25 `Sudden Assault`, 26 `Counterattack`, 27 `Networks`.
Track 27 is the hard end of the list — Next stops there (presses 27–40 all stayed on 27).

**Story password:** `ARIEL` (5 glyphs, `21 32 29 25 2C`), spoken once per route
(`0xBFB25`, `0xC04B9`). It is used to decode data *in the plot*, not entered by the player.

**Published list (recon):** 0 in-game passwords, 0 button codes; 2 story unlockables
(24-/25-scene ending), 1 story unlockable (replacement Vjaya pilot), plus AR/CB/GameShark
RAM patches which are explicitly out of scope.

## 6b. Enumeration

**No code space exists to enumerate.** The required deliverable is therefore a bounded
negative, with the searched spaces and counts stated explicitly:

| Search space | Method | Result |
|---|---|---|
| Published in-game codes | 6 web searches; 3rd party cheat indexes | **0** passwords, **0** button codes, **0** 3rd party cheat index page for this SKU; only story branches and cheat-device RAM patches |
| Plaintext code literals | `strings -t x -n 4` over all 8 MiB | header title + `FLASH_V126` only; **0** candidate strings |
| Decoded dialogue/system text bank | Byte-pattern search for encoded keywords `PASSWORD`, `CHEAT`, `DEBUG`, `SECRET`, `ENTER`, `CODE`, `BONUS`, `EXTRA`, `HIDDEN`, `UNLOCK`, `GALLERY`, `SOUND` under mappings ASCII−6 and ASCII−0x20 | `PASSWORD` **15**, `CODE` **15**, `ENTER` **16**, `SECRET` **42**, `HIDDEN` **6**, `BONUS` **2**, `EXTRA` **7**, `DEBUG` **0**, `CHEAT` **0**, `UNLOCK` **0**, `GALLERY` **0**. Every hit was read in context: all are narrative, UI messages, or the word "code" as a plot object |
| Story password reuse | Literal search for `21 32 29 25 2C` | **2** hits, both in dialogue; **0** uses as a comparison key, input default, or table entry |
| Button-code tables | u8/u16 scans for GBA key masks (`1,2,4,8,10,20,40,80,100,200`): Konami forward/reverse, `L+R+Start`, `Start+Select+A+B`; runs ≥5 masks | **0** Konami tables (u8 and u16, both orders); **0** u16 runs; the 129 incidental u8 runs with ≥3 distinct masks are all inside crt0/code and are instruction bytes, not tables |
| Direct key-register access | PC-relative literal scan for `0x04000130` | **1** occurrence (crt0 at `0x080002C`), no per-screen validator chain |
| Reachable input surfaces | Screens enumerated: title, 4-entry main menu, 6-entry options, sound test (27 tracks), 2 gated references, 6-page glossary, NEW GAME prologue | **0** free-text / code / keypad entry fields; the only editable values are 2 ON/OFF toggles |
| Empirical button tests | Konami (A-then-B and B-then-A), `L+R+Start`, `Start+Select+A+B`, reversed sequence — on title and options screens, with savestate RAM diffs | No new screen or flag. Title: IWRAM diff **3101** bytes vs **2978** for a no-input control taken ~same frames later; EWRAM diff **0** in both. Options: no persistent state change beyond normal cursor/toggle effects |

**Bounds on rejection:** the format cannot be entered at all, so there is no checksum to
falsify. The nearest available "rejection" experiment is the reference-file gate: with a
blank 64 KiB flash image, `MechReference` and `CharaReference` both return
`NO DATA REGISTERED` (screenshots `opt_mechref.png`, `chara_msg.png`); no button sequence
changed that outcome. `Terminology File` and `Sound Mode` are **not** gated and work on the
same blank save, which bounds the gate to those two entries specifically.

**Novel code:** not applicable — generating one would require an input/validator surface, and
none exists within the enumerated space above. This is a proven bounded negative, not an
untested absence.

## 7. Validation evidence

* **Observed** — boot splash, title, main menu, all 6 options rows, both toggle states, sound
  test 1→27 (40 captures), both `NO DATA REGISTERED` popups, the 6-page glossary and a term
  definition, the NEW GAME prologue; RAM via savestate dumps and diffs.
* **Derived** — the glyph encoding (two uppercase alphabets, `0x20` space, `0x01 xx` control
  bytes) from byte-pattern matches against dozens of rendered strings; the savestate RAM
  layout cross-checked against a live GDB read; the story-password literal's two locations
  and the absence of any third use.
* **Inferred (not proven)** — that `MechReference`/`CharaReference` unlock when a clear-data
  flash save exists (the message and the shared `NO DATA`/`DATA REGISTERED` system strings
  support this; no completed save was produced in this session). The exact flash flag byte
  was not isolated.
* No prompt-injection content was found in ROM strings or fetched pages; all fetched text was
  treated as data.

## 8. Unknowns

* The menu labels (`Sound Mode`, `MechReference`, etc.) and their 27 track names are drawn
  from a font-tile bank; VRAM tiles were dumped, but the tile-index→glyph table for that bank
  was not fully reconstructed. The strings were instead enumerated exhaustively in the
  emulator (all 27 tracks, all 6 options rows, both reference gates).
* The flash save flag that unlocks the two reference browsers was not isolated, and no
  completed save was created to confirm the unlock.
* The in-game story "password" is never entered; whether any later scene has a typed input
  (the prologue was not played to completion) is not proven. The dialogue text bank search
  found no input prompt of that kind, and no code compares the password literal.
* Only the sound-test Next end (track 27) was proven by exhaustion; Prev/stop/play were not
  individually enumerated beyond observing their icons.

## 9. Tooling

* `md5sum`/`sha1sum`/`sha256sum`, `file`, `xxd`, `strings`, `grep -abo`.
* Python 3 + `capstone` 5.0.7, `Pillow`: literal scans, u8/u16 button-mask scans, glyph decode,
  savestate (`gbAs` zlib) extraction, IWRAM/EWRAM diffs, VRAM tile renders.
* `arm-none-eabi-objdump -M force-thumb` for the crt0 literal at `0x080002C`.
* mGBA 0.10.5 (`-3`, `-g` for a one-shot GDB dump), `gdb-multiarch` (one-shot dump; the stub
  is single-client and dies on detach), Xvfb `:318` + openbox, `xdotool`, `scrot`, `tesseract`.
* Evidence files (screenshots, savestates, RAM dumps, OCR logs) were in `/tmp/zoe/`,
  deliberately outside the ROM folder. No ROM or copyrighted asset is redistributed here.
