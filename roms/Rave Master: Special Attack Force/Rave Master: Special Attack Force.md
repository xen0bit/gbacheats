# Rave Master: Special Attack Force! (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Rave Master: Special Attack Force.gba` |
| Size | 8,388,608 bytes (0x800000) |
| `file` ID | Game Boy Advance ROM image: "RAVE MASTER" (BRMEA4, Rev.00) |
| Header title | `RAVE MASTER` (0xA0) |
| Game code | `BRME` (0xAC) |
| Maker code | `A4` (0xB0) |
| Fixed byte | 0x96 (0xB2) — OK |
| Version | 0x00 (0xBC) |
| Entry word | `0xEA00002E` → branch to `0x080000C0` (stock crt0) |
| Header checksum / complement | `0x0000` / `0x9C` |
| MD5 | `2c1e1db8121b8eb26a55eabbb960bd67` |
| SHA-1 | `5cf4fa61626e4d0a887efab249dbd682fc770211` |
| SHA-256 | `8faca7d22a1de6c160bca7400ab398c5c2dfb0675c7da6cf791a683d7b6a1705` |

**Phase 0 result:** exactly **1** Nintendo-logo hit (at file 0x0). No multi-game
header, no appended trainer, no patched entry word. The image is the retail
revision; all addresses below are for this exact hash.

## 2. Executive summary

This ROM has **no developer-intended password, cheat-code, button-code, or
hidden debug menu that could be found or made to work** on the analysed
revision. The negative is bounded, not assumed:

* The only "cheat" content published for this SKU is (a) GameShark/CodeBreaker
  memory-edit codes — explicitly out of scope — and (b) **save-bit unlockables**
  (expert difficulty, five extra characters, original finishers) that are
  earned by story/ranking results, not entered as a code (§16.18 of the guide).
* One user-submitted button sequence exists on SuperCheats
  ("Up Up Left B A A A A Up L+R", labelled "Invinceabillaty"). It is **not
  present in the ROM in any of eight plausible key-mask encodings**, and
  entering it on the title screen, the main menu, and during gameplay produced
  **no persistent RAM change** and no new menu entry. It is reported as
  *unverified / ineffective on BRMEA4*, not as a working code.
* Every reachable screen was walked with savestate/RAM evidence: title, main
  menu (6 items), Story gameplay, Ranking, Free Battle, Link Battle, Training,
  Option (6 items) and their sub-screens. No unlabelled or gated menu entry was
  observed.
* Game text is **tile-indexed** (u16 tilemap entries; e.g. EWRAM `0x02000808`
  holds `0x019D`-style entries), not ASCII. Exhaustive raw/UTF/Shift/LZ77 text
  searches returned **zero** cheat/debug/password strings, so the negative
  rests on screen enumeration plus these counts, not on `strings` alone.

## 3. How to reproduce

Environment: `Xvfb :315 -screen 0 1024x768x24`, `openbox`, `SDL_AUDIODRIVER=dummy`,
`mgba -3` (mGBA SDL). Keymap used: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
Select=`BackSpace`, D-pad=arrow keys. Holds of 90 ms with 220 ms gaps avoid
double-stepping menus.

1. Boot; Konami splash → title (`PRESS START`). Press Start.
2. Main menu: Story Mode / Ranking Battle / Free Battle / Link Battle /
   Training / Option. Navigate with Up/Down, confirm with A (`x`).
3. Option shows: Difficulty `NORMAL`, Time Setting `3 min`, Indicator `ON`,
   `Clear Time`, `Reset Data`, `Change Battle Cry`, `OK`.
   * `Clear Time` → `LOAD DATA` (`New Game` / `Continue`).
   * `Reset Data` → "Clear all data, OK to proceed? Yes / No".
   * `Change Battle Cry` → character list (Haru …).
   * Difficulty / Time Setting / Indicator change value in place.
4. Button-code test: on title, main menu, or during Story gameplay press
   `Up Up Left B A A A A Up L+R`. No effect was observed in any context.
5. RAM evidence: mGBA `.ss1` savestates were parsed by extracting the `gbAs`
   PNG chunk, `zlib.decompress`, and diffing the raw state. Layout verified by
   holding Up: raw `0x1FAA0` toggles `0x00→0x40`, which maps to IWRAM
   `0x03006AA0 = 0x19000 + 0x6AA0`. EWRAM starts at raw `0x21000`.

Screenshots used as evidence (kept in `/tmp/ravemaster/`):
`title.png`, `menu1.png`, `s_story2.png`, `option4.png`, `cleartime.png`,
`v_ranking.png`, `v_free.png`, `v_link.png`, `v_training.png`,
`o_reset.png`, `o_battlecry.png`.

## 4. Address map

| Item | Address | Evidence |
|---|---|---|
| Nintendo logo / header | file `0x0` / `0x4` | Observed (1 hit) |
| ARM entry crt0 | `0x08000000` (`0xEA00002E`) | Observed |
| Key-input update (held/pressed/prev from `0x04000130` & `0x3FF`) | `0x08000EA8` | Derived (Thumb disasm, literal pool at `0x08000F20`) |
| Literals `0x04000130`, `0x03FF`, `0x03006AA0` | `0x08000F20/24/28` | Observed |
| `get_held` | `0x08000FB8` | Derived |
| `get_pressed` | `0x08000FD4` | Derived |
| `get_released` (`prev & ~held`) | `0x08000FE0` | Derived |
| `get_field6` / `get_field8` | `0x08000FF0` / `0x08000FFC` | Derived |
| Raw key state (held/pressed/prev) | IWRAM `0x03006AA0` | Derived + savestate diff |
| Game input mirror (`base 0x030046B0 + 0x13C0`) | IWRAM `0x03005A70` | Derived; raw `0x1EA70` confirmed by held-Up diff |
| Global state base | IWRAM `0x030046B0` | Derived (421 literal references) |
| Tilemap/text glyph indices rendered for menus | EWRAM `0x02000808` | Observed (u16 `0x019D`-style entries) |
| Suspected "in-game cheats" flag from a public GameShark claim | EWRAM `0x02007C28` | Patched during analysis only; no effect; not a finding |
| Save image (SRAM) | 32 KiB `.sav`, data `0x0–0x25CC`, `0xFF` after | Observed |

## 5. Algorithm

No password/validator/button-code algorithm exists on this revision, so there
is no decoder to reimplement. For completeness, the input path that *would* be
the attack surface is:

```
held   = ~KEYINPUT(0x04000130) & 0x3FF
pressed = held & ~prev ; released = prev & ~held
state  = [0x03006AA0] = {held@+0, pressed@+2, prev@+4, f6@+6, f8@+8}
mirror = [0x030046B0 + 0x13C0] = held  (0x03005A70), +2 = pressed
```

A cheat validator would have to read that mirror and compare a sequence. No
such comparison chain was found (see §6b).

## 6. Tables

**Reachable menu inventory (all screens walked):**

| Screen | Entries / content |
|---|---|
| Title | `PRESS START` |
| Main menu | Story Mode, Ranking Battle, Free Battle, Link Battle, Training, Option |
| Story | gameplay; HUD shows Ruby / Musica / Reina / Celia |
| Ranking | `LOAD DATA` (New Game / Continue) |
| Free Battle | character select |
| Link Battle | "Please connect a Game Link Cable, After connecting please wait." |
| Training | `PLAYER'S SELECT` |
| Option | Difficulty (NORMAL), Time Setting (3 min), Indicator (ON), Clear Time, Reset Data, Change Battle Cry, OK |
| Clear Time | `LOAD DATA` |
| Reset Data | "Clear all data, OK to proceed? Yes / No" |
| Change Battle Cry | character list (Haru …) |

**Published unlockables (data; from GameFAQs/SuperCheats, not ROM-verified):**

| Unlockable | Condition |
|---|---|
| Expert Level | finish Ranking Battle (rank 1) |
| Gale | beat Story Mode with 5 characters, ≥Normal, without powering off |
| King | beat Story Mode with 9 characters |
| Lucia | rank 1 in Ranking Battle |
| Ogre | beat Story Mode with Gale and King |
| Doryu | beat Story Mode with Ogre |
| Original finishers | clear Story with Haru / Elie / Musica / Griff & Plue |

These are save-data bits, not a code system; per guide §16.18 the correct test
would be the setter's callers, which are story/ranking results. Exact SRAM bit
offsets were not isolated (§8).

**Published codes checked:**

| Source | Claim | Verification |
|---|---|---|
| SuperCheats user submission | "Up Up Left B A A A A Up L+R" (invincibility, then Clear Time) | Literal absent in 8 encodings; entered in 3 contexts; no RAM effect → unverified |
| Neoseeker / SuperCheats / GameHacking | GameShark codes, incl. `73007C28 0003` "Unlock In Game Cheats" | Out of scope (memory edit). Address patched in a savestate for analysis; no menu change → claim unsupported on this revision |
| GameFAQs | 7 unlockables (above) | Consistent with walkthrough; save-bit based, no entry code |

## 6b. Enumeration

This is a **bounded negative**, with the search space stated explicitly.

1. **ROM identity space** — 1 GBA header / 1 Nintendo logo in 8,388,608 bytes;
   0 patches/trainers. Revision is unambiguous.
2. **Plaintext text space** — `strings -t x -n 4` produced **42,675** strings;
   case-insensitive hits for `password|cheat|code|debug|secret|unlock|level
   select|menu|invalid|continue|boss|extra` = **0**. UTF-16LE, UTF-16BE,
   UTF-32LE and `+0x20` shifted searches for the same words = **0**. All
   `0x10`-prefixed LZ77 candidates: **50,198**, of which **1** decompressed
   validly; keyword hits in decompressed data = **0**. Text is tile-indexed
   (u16 tilemap entries), so `strings` alone cannot decide the question; all
   reachable screens were therefore enumerated visually as well.
3. **Password/code-table space** — literal searches for all published strings
   and for the known GameShark target `0x02007C28` = **0** hits. No NUL-padded
   equal-length code table exists.
4. **Button-code space** — the one published sequence was searched as u16 LE,
   u16 BE, u32, u8, reversed, L+R split into two presses, active-high and
   active-low masks, L/R swapped, and 5 index conventions: **0** full-sequence
   hits (the only 3-press prefix hit, file `0x46C7FA`, is inside compressed
   graphics data and is not followed by the rest of the sequence).
5. **Input-validator call-graph space** — **173** BL sites call the six
   key-state getters at `0x08000FB8/FC4/FD4/FE0/FF0/FFC`; **1,394** Thumb
   `cmp rX,#imm8` instructions use a GBA key mask. Clusters were examined;
   none is a 10-step sequence comparison chain. No hidden branch was found.
6. **Dynamic tests** — the published sequence was entered at title, main menu,
   and during Story gameplay. In the title test, EWRAM bytes changed =
   **67** total, **0** in `0x02000000–0x02000FFF`, **0** in
   `0x02007000–0x02007FFF`; flag `0x02007C28` stayed `0x00000000`. No new
   menu item or HUD change was observed in any context.
7. **Menu space** — main menu has 6 labelled entries; Option has 6; every
   entry was opened. No unlabelled/gated entry was reachable or observed.

Because no code system exists, §0.2's "mint a novel code and prove bounds by
rejection" is **not applicable**: there is no alphabet, no validator, and no
accepted set to enumerate. The accepted set is empty; bounds are proven by the
counts above.

## 7. Validation evidence

* **Observed** — ROM hashes/header/logo count; savestate diffs (held-Up toggles
  raw `0x1FAA0` `0→0x40`); all screen contents; no-effect button-code tests;
  SRAM size/layout; GDB reads of `0x04000130 = 0x03BF` while Up was held.
* **Derived** — key reader and getter functions (Thumb disassembly with
  verified literal pools); input mirror `0x03005A70` from
  `0x030046B0 + 0x13C0`; menu/tile-index nature of text.
* **Inferred** — the GameShark `0x02007C28` claim is probably for a different
  build or simply inaccurate; the SuperCheats button sequence is probably a
  false/other-edition submission. Both are labelled unverified, not confirmed.
* No prompt-injection content was encountered in fetched pages or ROM data;
  all fetched text was treated as data.

## 8. Unknowns

* Exact SRAM bit offsets for the five character unlocks, Expert difficulty,
  and original finishers were not isolated. Determining them would require
  completing story/ranking runs and diffing `.sav` files.
* The font glyph→ASCII mapping was not fully reconstructed: the tilemap entries
  are present (EWRAM `0x02000808`, u16 `0x019D`-style), but sampled VRAM tiles
  did not resolve into a clean alphabet with the time available. All reachable
  labels were nonetheless read directly from rendered screens.
* A validator keyed on a *hashed* press history rather than a literal table
  cannot be excluded by static searches alone; however, no such behaviour was
  observed dynamically, and no code writes a cheat flag from input.
* The Link Battle screen was reached but a cable/second console was not
  available, so its post-connect screens were not walked.

## 9. Tooling

* `file`, `xxd`, `strings -t x`, `grep -abo`, `md5sum`/`sha1sum`/`sha256sum`.
* `arm-none-eabi-objdump -D -b binary -marm -M force-thumb` with
  `--adjust-vma=0x08000000` (and `dd` extraction for ranges objdump skipped).
* Python scripts in `/tmp/ravemaster/`: `header_scan.py`,
  `keysearch.py`, `keysearch2.py` (mask encodings), `blscan.py` (BL targets),
  `scan_cmp.py` (key-mask comparisons), `textdecode.py`, `lzscan.py`,
  `parse_state.py`, `patch_state.py`, `state_preview.py`, `saves.py`, `k.py`,
  `seq.py`, `visit.py`, `visitopt.py`.
* mGBA `-3` under `Xvfb :315` + `openbox`; `xdotool` XTEST input; `scrot` +
  ImageMagick crop; `tesseract` OCR. GDB stub (`-g`) was used only for
  `0x04000130` confirmation; savestate diffing was the primary RAM method.

**Legal note:** no ROM or copyrighted asset is redistributed here; only
addresses, hashes, counts and the author's own tooling are published.
