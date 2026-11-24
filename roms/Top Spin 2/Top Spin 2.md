# Top Spin 2 (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

Queue 217. Analysis date 2026-11-20. Work dir `/tmp/topspin2`.
All addresses below are ROM addresses (`0x08000000 + file offset`) unless marked RAM.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Top Spin 2/Top Spin 2.gba` |
| Size | 16,777,216 bytes (`0x1000000`), 16 MiB |
| `file` | Game Boy Advance ROM image: "TOP SPIN 2" (B27E9G, Rev.00) |
| Header title | `TOP SPIN 2` (at `0xA0`) |
| Game code | `B27E` (at `0xAC`) |
| Maker | `9G` (at `0xB0`) |
| Version | `0x00`; complement `0x42`; header checksum `0x0000` |
| Entry word | `0xEA000030` (ordinary crt0 branch to `0x080000C0`) — no cracktro/trainer patch |
| MD5 | `94c6ec2dad53ef7d7ec44b7e438833b8` |
| SHA-1 | `16b9fd8ccddb9853b35138621ab3b7dbc2695089` |
| SHA-256 | `daf1cf05aa37abf782f37a386597a4719e8b79c7d8e5a4a0bfbda4a614ce8a0b` |

Save: 512-byte EEPROM, two mirrored 256-byte banks (`00 00 02 77 a3 3c cb 30 …`).

## 2. Executive summary

**No developer-intended cheat system exists in this ROM.** There is no password
screen, no code-entry field, no button-code table, and no reachable debug menu.
The only free-form text entry is the 10-character **career player name**, and its
sole consumer is the career label: its handler copies bytes into the career
struct and never compares them to a constant (§4, §7). The unlockable content —
tournaments, training drills, customization sets — is gated by a career
level/progress value in the EEPROM save, not by any input code (§6b).

The one multi-button combination in the global input routine,
`L+R+Select`, is the **documented Sleep Mode** command (UI string at
`0x08035E4FA`), not a cheat. It was located statically at `0x0805E89C` and
confirmed live by observing the gate flags in RAM before/during/after the press.

This is therefore a **bounded negative** (§0.2 point 5), with the search spaces
and counts given in §6b. Confidence: high for "no code surface reachable from
the retail UI"; high for "name is a label, not a validator"; moderate for the
claim that the two orphan debug strings are dead code (zero xrefs, but no full
decompilation of all 16 MiB was performed).

## 3. How to reproduce

* Emulator: mGBA 0.10.5, `SDL_AUDIODRIVER=dummy`, `Xvfb :318`, openbox, `mgba -3`.
* Keymap (verified on the language screen): A=`x`, B=`z`, L=`a`, R=`s`,
  Start=`Return`, Select=`BackSpace`, D-pad=arrow keys. Hold keys 150–300 ms;
  short taps are missed.
* Boot path: splash → "SELECT YOUR LANGUAGE" → A → title "PRESS START" →
  Start → main menu.
* Sleep-mode proof: at the main menu hold `a`+`s`+`BackSpace` together for
  ~0.4 s, release. The sleep message appears. Repeat to wake.
* Savestates: `Shift+F1` writes `Top Spin 2.ss1` in the ROM folder. RAM was read
  by decompressing the PNG `gbAs` chunk (zlib) and reading IWRAM at raw offset
  `0x19000 + (addr-0x03000000)` (§16.13). The sleep-mode RAM readings used this
  method.
* Note: `xdotool key` single-shot events are occasionally dropped by this game;
  `keydown`/`sleep 0.2`/`keyup` is reliable. This is a harness issue (§16.2),
  not game behavior.

## 4. Address map

| Address | Meaning | Evidence |
|---|---|---|
| `0x0805E83C` | Global joypad poll. Reads `0x04000130`, computes held/pressed/released. | Derived (disassembly) |
| `0x0300382C` | active-high held keys (16-bit, `~KEYINPUT & 0xFFFF`) | Derived |
| `0x03002E8C` / `0x03002E7C` | new presses / new releases | Derived |
| `0x0805E89C`–`0x0805E8A2` | only multi-button compare: `held & 0x3FF == 0x304` (L+R+Select) | Derived + observed |
| `0x03002C30` | mode flags: bit16 = normal mode, bit17 = sleep mode, bit4 = countdown active | Derived + observed |
| `0x03002E70` | frame counter byte, wraps `0x55 → … → 0xFF → 0x55` (`0x0805FCC0`) | Derived + observed |
| `0x03001598` | screen-state byte; must be 0 for the sleep check | Derived |
| `0x0805E6B8` | sleep-mode entry: clears bit16, draws the sleep message | Derived + observed |
| `0x0804EFC0`–`0x0804F118` | on-screen keyboard handler (career name) | Derived |
| `0x03001520` | name buffer, 10 bytes, ASCII | Observed (savestate diff) |
| `0x0300152B` | name length byte | Observed |
| `0x08035C794`–`0x08035FE2C` | English text bank, plain ASCII with `0x0004` control prefix | Derived |
| `0x08035E4FA` | "To exit Sleep Mode, press SELECT + L Button + R Button at the same time." | Observed (screenshot) |
| `0x08057768` | orphan string "GMOD7: CACHE NOT IMPLEMENTED" | Derived, 0 xrefs |
| `0x0806B9A0`/`0x0806B9C0` | orphan debug block: "PRESS ANY KEY TO CONTINUE", Magic Pockets banner, build date `Oct 12 2005` | Derived, 0 xrefs |

Text is stored as **plain ASCII**, not font/tile indices: the bank was decoded
directly (735 printable strings, `regex [ -~]{3,}` over `0x35C794..0x35FE2C`).
The `+0x20` lowercase variant and UTF-16 searches were therefore unnecessary;
a case-insensitive keyword scan of the whole 16 MiB was run anyway (§6b).

## 5. Algorithm

No password/checksum algorithm exists. The only nontrivial input logic is the
sleep-mode gate:

```
; 0x0805E83C, every frame
held   = ~KEYINPUT & 0xFFFF ; store 0x0300382C
press  = held & ~prev       ; store 0x03002E8C
rel    = (held ^ prev) & prev ; store 0x03002E7C
prev   = held
if (flags & 0x10000) && byte[0x03002E70]==0x55 && byte[0x03001598]==0:
    if (held & 0x3FF) == (0xC1 << 2) == 0x304:    ; L + R + Select
        flags |= 0x20000                          ; sleep request latched
    elif (flags & 0x20000) && (held & 0x3FF)==0:
        sleep_mode_enter()                        ; 0x0805E6B8
        flags &= 0xFFFDFFFF                       ; clear bit17
```

The name-entry handler is equally simple: for each A press, the selected glyph
is stored at `name[len++]`, `len` capped at 10; DEL decrements; END exits. No
comparison, hash, or checksum is executed on the buffer.

## 6. Tables

**Keyboard alphabet (39 symbols, observed):** `0 1 2 3 4 5 6 7 8 9`
`A B C D E F G H I J` `K L M N O P Q R S T` `U V W X Y Z , . !`,
plus DEL and END. Name buffer observed as `"0B"` at `0x03001520` with length 2.

**Button-mask facts (GBA active-high):** A=`0x001`, B=`0x002`, Select=`0x004`,
Start=`0x008`, Right=`0x010`, Left=`0x020`, Up=`0x040`, Down=`0x080`,
R=`0x100`, L=`0x200`. Sleep mask = `0x304`.

**Unlockable content enumerated from the decoded text bank (all progression-gated):**

* 22 named tour venues + `TOURNAMENT OF CHAMPIONS`, `CHARITY TOURNAMENT`,
  `CHICAGO PLAYGROUND` (25 tournament entries) — shown as padlocks on the
  career world map (`career_created.png`).
* 6 training drills: `SHOT SEQUENCE`, `TIC-TAC-TOE TENNIS`, `TRAINING LOOP`,
  `INFLATABLE CARNAGE`, `BALL MACHINE MADNESS`, `SERVE SNIPER`
  (`career_training.png`).
* 16 playable pros (8 men + 8 women, all selectable in Exhibition from a fresh
  save); customization sets and shop brands are bought with in-game money.
* Messages confirming progression unlocks: `NEW CUSTOMIZATION SET UNLOCKED`,
  `NEW TRAINING LEVEL UNLOCKED`, `UNLOCKED TOURNAMENTS` (text bank offsets
  `0x35E63B`, `0x35E65B`, `0x35E678`).

## 6b. Enumeration

**Result: the code/password space is empty; this is a proven bounded negative.**

1. **Input-surface enumeration.** Exactly one text-entry UI exists (career
   name, 10 chars over a 39-symbol alphabet → 39^10 ≈ 8.14×10^15 representable
   strings). It has **no validator**: 8 literal pointers to its buffer
   (`0x4F00C`, `0x4F0A8`, `0x4F110`, `0x4F160`, `0x4F1EC`, `0x4F358`,
   `0x4F3BC`, `0x4F43C`) all lie inside the keyboard handler; a search of the
   whole ROM for constants containing any plausible cheat word returned 0 hits.
   No password screen exists on any of the 24 screens walked (§7).
2. **Button-code enumeration.** A Thumb scan of code offsets `0x0..0x610000`
   found **33** `movs #imm; lsls; cmp` mask-construction snippets; **3** lie
   within ±0x80 of a key-global literal; only **1** is a real multi-button
   compare (`0x0805E89C`, mask `0x304`). Its single effect (sleep mode) is
   documented in the shipped UI. No sequence matcher/ring buffer/table exists.
3. **Novel input test.** Entered the novel name `"0B"` (not a published code)
   through the on-screen keyboard; it was accepted as a career label and
   produced no unlock, no flag write, and no message (screenshots
   `name2.png`, `name_after.png`, `career_created.png`). Because the buffer has
   no consumer beyond the label, this is the maximal in-game input test.
4. **Rejection/bounds proof.** The name field bounds were derived from code:
   length check `cmp r2,#9` before append (`0x0804EFDE`) and `cmp r2,#10`
   in the copy loop (`0x0804F0D8`) cap it at 10 characters. The sleep gate was
   rejected with A+Up+Down (mask `0x0C1`, observed `held=0xFCC1`): flags stayed
   `0x00010002`, no sleep (`shot_combo2.png`). It was accepted only with the
   exact mask `0x304` (observed `held=0xFF04`, flags `0x00030002` then
   `0x00020002`, `shot_debug.png`). This isolates the mask, not a checksum.
5. **Published-code reconciliation.** No published *in-game* code was found:
   Cheat Happens "no cheats", VGChartz "Total cheats available: 0", GameFAQs
   returned HTTP 403, Codejunkies lists only DS Action Replay RAM patches
   (`94…/62…/B2…` with Select activators) — cheat-device codes, explicitly
   out of scope. No literal from those lists occurs in this GBA image.
6. **Debug-menu negative.** 2 orphan debug text blocks were found
   (`GMOD7: CACHE NOT IMPLEMENTED`, and the Magic Pockets "PRESS ANY KEY TO
   CONTINUE" / "NOT FOR RELEASE" block with build stamp `Oct 12 2005`). Both
   have **0** 32-bit literal pointers anywhere in the 16 MiB and no reachable
   menu entry in the 24-screen walk — classified as dead data (§16.3/§16.21),
   not a hidden menu.

## 7. Validation evidence

**Observed (emulator + RAM):** language select, title, main menu, Options
(5 entries), Display Controls, Play Now → Exhibition/Tournament, Exhibition
Settings (6 fields), venue select 1/10, player select (8 men + 8 women),
opponent select, Career slots (4), Player Creator (INFO/PLAYER LOOK/STYLE),
name entry, career world map with padlocks, training map, pause menu
(RESUME/OPTIONS/QUIT) and quit confirmation. Screenshots listed in §9.

**Observed (RAM):** name buffer `0x03001520 = "0B"`, length `0x0300152B = 2`
(savestate diff). Sleep gate transitions `0x00010002 → 0x00030002 →
0x00020002` at `0x03002C30`, with `held 0xFF04` during the combo and `0xFC00`
after release. Rejected A+Up+Down left flags at `0x00010002`.

**Derived (disassembly):** input routine and gate; keyboard handler; sleep entry
function; text bank decoding; mask scan; pointer/xref counts.

**Inferred (lower confidence):** that the two orphan debug blocks are dead code
from another platform build; that tournament/training/customization unlocks are
driven by the career level byte in the EEPROM (consistent with padlocks,
unlock messages and save format, but no full playthrough was completed).

## 8. Unknowns

* The exact EEPROM bit/byte layout of each unlock flag, and the career routine
  that sets it, were not fully mapped (a complete career playthrough was not
  performed). No input path to those flags was found, which is the part needed
  for this engagement.
* Multiplayer Mode screens requiring a second GBA/link cable were not entered.
* The text-bank ID table was not reconstructed; strings were located by direct
  ASCII scan and their consumers by literal-pointer analysis instead.

## 9. Tooling and artifacts

* Tools: `mgba` 0.10.5, Xvfb `:318` + openbox, `xdotool`, `scrot`,
  `arm-none-eabi-objdump`, Python 3 + `capstone`, zlib savestate parser.
* Scripts in `/tmp/topspin2/`: `drive.py` (input), `state.py`
  (savestate RAM read), `diffstate.py` (IWRAM/EWRAM diff), `scancmp.py` and
  `scanmask.py` (key-mask scans), `counts.py` (keyword/pointer counts),
  `ptydbg.py` (mGBA CLI debugger driver, used for early probing).
* Evidence screenshots in `/tmp/topspin2/`: `shot0.png`, `shot1.png`
  (splash/language), `shot_lang.png` (title), `shot_menu.png` (main menu),
  `shot_options.png`, `shot_controls.png`, `shot_playnow1.png`, `shot_exh.png`,
  `shot_exh1p.png` (settings), `shot_selectp.png` (venue),
  `shot_player1.png`/`shot_women.png` (rosters), `shot_career1.png`,
  `shot_newcareer.png`, `shot_tab3.png`, `name2.png`/`name_after.png`
  (keyboard), `career_created.png`, `career_training.png`, `career_pause.png`,
  `quitconfirm.png`, `shot_combo2.png` (rejected mask), `shot_debug.png`
  (accepted L+R+Select/Sleep Mode).
* No ROM or copyrighted assets are redistributed by this report.

## 10. Cleanup

All processes started for this engagement were stopped by PID number only
(`Xvfb :318`, openbox on `:318`, and every mGBA launched by this job). No
`pkill`/`pkill -f` was used. All `.sav`, `.ss1`, `.ss2` files created in the ROM
folder were removed. Other agents' displays/processes were left untouched.
