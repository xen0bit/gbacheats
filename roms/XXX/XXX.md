# XXX / xXx (GBA) — Reverse Engineering Report

> Queue 269. Analysis target is the scene-patched USA image of **xXx** (stylised `xXx`,
> AGB-AX3E-USA), renamed `XXX` in this collection. All screenshots/evidence live in
> `/tmp/opencode/xxx/`, **not** in the ROM folder. No ROM or game assets are redistributed.

## 1. Target identity

| Field | Value |
|---|---|
| File | `/mnt/gbacheats/roms/XXX/XXX.gba` |
| Size | 8,388,608 bytes (8 MiB / 64 Mbit) |
| `file` | Game Boy Advance ROM image: "XXX" (AX3E52, Rev.00) |
| Header title | `XXX` (collection rename; see cracktro below) |
| Game code / maker | `AX3E` / `52` — matches **AGB-AX3E-USA** (xXx) |
| Version / fixed / complement / checksum | `0x00` / `0x96` / `0x00` / `0x00D1` |
| MD5 | `5b1bd32db98ffbc90f644ebe03400c5d` |
| SHA-1 | `80d5ad34315133be6cdea8fc40f0d2563c38b3e0` |
| SHA-256 | `a915ea555b9a4adfb73d737c07cbc610f65a4dd3a93aad4098e9e55eb501dbce` |
| Publisher / developer / release | Activision / Digital Eclipse (with Tuna Technologies), NA 2002-08-06 |

### 1.1 Scene-patched image (§16.1)

The reset vector is **not** the stock `0xEA00002E` (`b 0x080000C0`). ROM word 0 is
`0xEA1FC02E`, which branches to **`0x087F00C0`**. The original crt0 is still intact at
`0x080000C0`. The trampoline at `0x087F00C0` sets up IRQ/SVC/user stacks
(`0x03007FA0`, `0x03007FE0`, `0x03007F00`), clears registers, then selects an entry through
a small jump table keyed on bits of `0x04000200`.

Emulation shows this is a **Team Venom cracktro** (Observed, screenshot
`/tmp/opencode/xxx/t2c.png`):

```
VENOM BRINGING YOU:
XXX (C) ACTIVISION
USA - 64MBIT
SUPPLIED BY: TEAM VENOM
RELEASED ON: 02 AUG 2002
```

followed by "LOOK OUT FOR MORE RELEASES COMING SOON / VENOM / NO PITY FOR THE MAJORITY! /
TEXT RESTARTS...". It is an appended intro, **not** an in-game cheat device; it is excluded
from the findings below. The legal screens name Revolution Studios, Digital Eclipse and
Activision, confirming the SKU. Pressing Start skips the cracktro and hands control to the
stock game.

## 2. Executive summary

**No developer-intended password / text-code system exists in this build**, and no ROM-resident
button-code table could be located in any of the encodings searched. The only published
cheats for this SKU are two short button sequences and a beat-the-game unlockable:

1. Pause → `B,B,A,A,Start` → "invincibility for the level" (GameFAQs and SuperCheats).
   GameFAQs' own effect/code table contradicts its prose and lists `B,A,B,A,Start`.
2. `A,B,L,R,A` → "Get Everything!" / "you will hear a noise" (SuperCheats), entry screen
   unspecified.
3. Beat Yorgi in level 12 → Extras menu gains infinite health / ammunition.

Every reachable screen was walked with screenshots (§3). All four text-code representations
that a password system would use (u16/u8 keypad masks, button indices, ASCII letters,
active-low variants, multiple strides and prefix lengths) were searched exhaustively with
**zero** full-sequence matches; the literal-pool, cmp-chain and validator-candidate scans
likewise found no game-specific table. Attempts to reproduce the two button cheats on the
pause screen, the main menu and the Extras screen produced **no difference against a
near-miss control sequence** and no change to the locked Extras entries.

This is therefore reported as a **bounded negative** (§0.2 item 5): the space that was
checked is stated with counts in §6b. It is *not* a claim that no cheat has ever existed in
any xXx build — only that this image exposes no code system reachable by the searched
surfaces.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 (`/usr/local/bin/mgba`), `Xvfb :317` + openbox,
  `SDL_AUDIODRIVER=dummy`, `mgba -3`. Default SDL keymap: A=`x`, B=`z`, L=`a`, R=`s`,
  Start=`Return`, Select=`BackSpace`, D-pad=arrows. Hold 120 ms, gap 160 ms.
* Boot, press **Start** once to skip the Venom cracktro, then press Start through the legal
  text, Revolution Studios and Digital Eclipse splash screens to reach the main menu.
* Menu path: START NEW GAME → FILE TRANSFER → select a file → briefing TASKS → level 1 →
  **Start** to pause. LOAD GAME also reaches the level from a saved file.
* Codes tested: `B,B,A,A,Start`, `B,A,B,A,Start`, near-miss `B,B,A,B,Start`,
  `A,B,L,R,A` on the pause screen, on the main menu, on the Extras screen and during
  gameplay.
* Debugger: GDB port 2345 was already held by another agent's mGBA, so mGBA's stub-free
  `-d` CLI debugger was driven over a pty (see §9); savestates were parsed as PNG + zlib
  `gbAs` chunks for RAM evidence (§16.13).

## 4. Address map

| Address | Kind | Evidence | Meaning |
|---|---|---|---|
| `0x08000000` | ROM | Derived | Reset word `0xEA1FC02E` → cracktro |
| `0x080000C0` | ROM | Derived | Original, intact libgba-style crt0 |
| `0x087F00C0` | ROM | Derived (objdump) | Venom trampoline: stacks, jump table at `0x087F0114`, reads `0x04000200` |
| `0x0862A48C` | ROM | Derived (objdump) | Engine key-update routine: reads `0x04000130`, writes key RAM vars |
| `0x0861D0C8` | ROM | Derived + watchpoint | Central input dispatcher; reads `0x03001894/98/9C/A0`, calls `0x0861D110` |
| `0x0861D110` → `0x0863C23C` | ROM | Derived | Event post with IDs 4, 6, 5, 2, 3 |
| `0x03001894` | IWRAM | Observed (watchpoint) | Key mask |
| `0x03001898` | IWRAM | Observed | Previous held keys (active-high) |
| `0x0300189C` | IWRAM | Observed | Held keys (active-high; e.g. `0xFE00` with L held) |
| `0x030018A0` | IWRAM | Observed (watchpoint #1) | Pressed keys; **single reader** at `0x0861D0D9` |
| `0x03000D40+` | IWRAM | Observed (rejected) | 8-byte-stride array of `0x00000200`/`0`; write-watchpoint never fired on button presses → not the code buffer |
| Savestate raw `0x19000` / `0x21000` | file layout | Observed | IWRAM `0x03000000` / EWRAM `0x02000000`; 397,312-byte raw state |

## 5. Algorithm / validator model

No validator was recovered. The closest reconstructible component is the engine's input path:

```
KEYINPUT @ 0x04000130 (active-low)
  -> ~KEYINPUT                      @ 0x0300189C   (held, active-high)
  -> held & ~mask                   @ 0x030018A0   (pressed)
  -> 0x0861D110(event, value) -> 0x0863C23C(global handler, event, value)
```

A read-watchpoint on `0x030018A0` produced exactly one reader site
(`0x0861D0DE`/`0x0861D0E6`, LR `0x0861D123`) across 15 continues, i.e. keypad state is
funnelled through one dispatcher rather than read ad hoc by a cheat checker. No function in
the image was found that holds a 5-press history and compares it against stored masks.

## 6. Tables

Published material (treated as data, never instructions):

| Source | Claim | ROM verification |
|---|---|---|
| GameFAQs "Codes" prose | Pause → `B,B,A,A,Start` = level invincibility | Sequence absent as mask table (§6b); visual A/B test inconclusive |
| GameFAQs effect/code table | `B,A,B,A,Start` | Same; internal contradiction with the prose recorded |
| SuperCheats "Level Invincibility" | `B,B,A,A,Start` | As above |
| SuperCheats "Get Everything!" | `A,B,L,R,A`, "hear a noise" | Tested on pause, main menu, Extras and in-level; no unlock/confirmation seen |
| GameFAQs/Neoseeker "Extra bonuses" | Beat level 12 → Extras infinite health/ammo | Extras screen **observed** with 4 `Locked` entries (§3), consistent with a save-bit unlock; not brute-forced (§16.18) |

No password string, alphabet string, code table, name-entry screen, debug menu or hidden
"cheat" menu was found. GBA UI text in this game is stored as font/tile indices, so plain
`strings` finds no menus (§11); the negative below rests on the structural searches, not on
the absence of ASCII strings.

## 6b. Enumeration

This is a **bounded negative** engagement; no code was minted because no alphabet, table or
validator exists to mint from. Stating the searched space is the deliverable.

### 6b.1 Screen enumeration (all reachable screens walked)

13 distinct screens were captured and inspected: Venom cracktro (3 states), legal text,
Revolution Studios splash, Digital Eclipse splash, main menu (4 items: START NEW GAME,
LOAD GAME, OPTIONS, EXTRAS), FILE TRANSFER (3 save slots), TASKS briefing, gameplay level 1,
pause menu (5 items), View Statistics, Options (MUSIC/SOUND FX/CREDITS), Extras (7 rows:
View Best Times, Play Race 1, 4× Locked) and the "Are you sure?" confirm. No code-entry
surface, on-screen keyboard, cheat menu, debug menu or hidden text field appears on any of
them. Evidence: `/tmp/opencode/xxx/*.png`.

### 6b.2 Button-sequence space and table search counts

* Button alphabet = 10 active-high masks
  `A=0x1, B=0x2, Select=0x4, Start=0x8, Right=0x10, Left=0x20, Up=0x40, Down=0x80, R=0x100, L=0x200`.
  A 5-press code space is 10^5 = **100,000** ordered sequences.
* Literal table search — u16 and u8, active-high and active-low, prefix lengths 2–5,
  contiguous and strides 2/4/8: `BBAAS` and `BABAS` produced **0** full 5-press matches;
  the u16 `B,A,B` prefix had exactly 1 hit (`0x08109946`) and `A,B,L` 1 hit
  (`0x087035C4`), neither part of a 5-entry table.
* Alternate encodings — 4 button-index schemes × 4 integer widths × 2 sequences, plus
  uppercase/lowercase/reversed ASCII forms: all "hits" were dumped and identified as signed
  8-bit PCM audio data (e.g. `0x086A83C0`, `0x086B6138`, `0x086F2A20`), not tables.
* Thumb `cmp #imm` chains over the whole 8 MiB: **40,625** `cmp`-immediate instructions
  scanned, **0** chains matching `[2,2,1,1,8]` or `[2,1,2,1,8]`.
* `ldrh [rX,#4]` validator-candidate scan: **3,411** sites, **20** with a nearby button-mask
  `cmp`, **all** inside the shared engine library `0x0861xxxx–0x0863xxxx`; none is a
  game-specific cheat table and none checks a 5-press history.
* Literals for `0x04000130`: **9** occurrences (8 in asset banks `0x084357DA–0x084377E2`,
  1 in the engine at `0x0862A4BC`); **0** direct Thumb/ARM PC-relative literal loads found.
* RAM scans of three savestates (paused baseline, correct-code, near-miss) for runs of
  5+ 16-bit button masks: only incidental hits (e.g. stack `0x03007DCC` = `1,1,1,1,8`),
  none matching either published code.
* Dynamic rejection bounds: `A,B,L,R,A` on Extras was consumed as ordinary menu navigation
  (screen changed to Best Times, `Locked` rows unchanged); `A,B,L,R,A` during gameplay left
  all 4 Extras rows `Locked`; `B,B,A,A,Start` and near-miss `B,B,A,B,Start` produced
  indistinguishable HUD/screens. A write-watchpoint on the candidate IWRAM array
  `0x03000D40` never fired during pause-screen button presses, and a 32 KiB IWRAM before/after
  diff over `L,R,L,R,A` yielded 21 change regions, none a button-history buffer.

### 6b.3 Unlockables (not a code)

Extras exposes 4 locked rows. Per §16.18 this is a save-bit unlock, not a controller code:
the published setter is story progress (defeat Yorgi in level 12). The only reachable write
path observed is the save/completion flow; it was not brute-forced and is not reported as a
code.

### 6b.4 Conclusion of enumeration

For this exact hash there is **no text/password code system** (no alphabet, no input surface,
no validator) and **no recoverable button-code table**. Space searched: 100,000 ordered
5-press combinations in representation, 4 encodings × 4 widths × 2 sequences in alternate
form, 40,625 Thumb comparisons and 3,411 candidate load sites. A novel working code could
not be generated; reporting one without ROM or emulator proof would be fabricated.

## 7. Validation evidence

* **Observed** — emulator screenshots of all 13 screens; Cracktro text read from
  `/tmp/opencode/xxx/t2c.png`; live keypad `0x04000130 = 0x1FF` with L held and
  `0x0300189C = 0xFE00`; single reader of `0x030018A0` from a read-watchpoint; write-watchpoint
  on `0x03000D40` never firing; savestate raw dumps and diffs; Extras remaining 4× Locked
  after every code attempt.
* **Derived** — reset-vector arithmetic; objdump of the trampoline, key-update routine and
  input dispatcher; literal/pointer/cmp scan results; savestate chunk layout.
* **Inferred** — that the published invincibility code ever worked on this SKU; the
  GameFAQs `B,B,A,A,Start` vs `B,A,B,A,Start` discrepancy suggests a transcription error in
  at least one published list. Not confirmed in ROM.
* Fetched web pages were treated strictly as data. No prompt-injection payload was
  encountered in this session; ROM strings were not executed.

## 8. Unknowns

* Where (if anywhere) the `B,B,A,A,Start` invincibility effect is implemented. The visual
  A/B test cannot distinguish a hidden flag from no effect; neither code produced a HUD change.
* The exact entry screen for `A,B,L,R,A`; four surfaces were tested without success.
* Whether a different regional build or the original uncracked image contains a code table
  absent from this scene release.
* Identity of the 8-byte-stride `0x00000200` array at `0x03000D40+` (write-watchpoint proved
  it is not the button history).
* The four locked Extras rows were not unlocked; their exact labels remain unread.

## 9. Tooling

* `strings`, `xxd`, `file`, `md5sum`/`sha1sum`/`sha256sum` — Phase 0.
* `arm-none-eabi-objdump -M force-thumb/-M force-arm`, Capstone Python — disassembly and scans.
* mGBA 0.10.5: normal `-3` runs, `-t` state reload, `-g` (blocked by another agent),
  `-d` CLI debugger over pty (`dbg2.py`, `dc2.sh`) with `watch/r`, `watch/c`, `r/2`, `r/4`,
  `x/4`, `BREAK` (Ctrl+C).
* Savestate parsing: PNG `gbAs` chunk → zlib → 397,312-byte raw state; scripts
  `readstate.py`, `diffstates.py`, `threeway.py`, `scan_ramhist.py`.
* Search scripts in `/tmp/opencode/xxx/`: `scan_codes.py`, `scan_tables.py`, `scan_enc.py`,
  `scan_cmp.py`, `scan_keypad.py`, `scan_inputrefs.py`, `scan_iwramrefs.py`,
  `scan_validator2.py`.
* X11: Xvfb `:317`, openbox, xdotool (`key.py`), scrot; all evidence images in the work dir.

## 10. Legal note

No ROM image, extracted graphics, audio or game text is redistributed. This report contains
only hashes, addresses, counts and the analyst's own tooling.
