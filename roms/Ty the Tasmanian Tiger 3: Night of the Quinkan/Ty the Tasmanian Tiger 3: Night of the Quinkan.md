# Ty the Tasmanian Tiger 3: Night of the Quinkan (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Ty the Tasmanian Tiger 3: Night of the Quinkan.gba` |
| Size | 8,388,608 bytes (0x800000, 8 MiB) |
| `file` ID | Game Boy Advance ROM image: "TY3" (BTVE52, Rev.00) |
| Header title (0xA0) | `TY3` |
| Game code (0xAC) | `BTVE` |
| Maker (0xB0) | `52` |
| Version (0xBC) | `0x00` (Rev.00) |
| Fixed byte (0xB2) | `0x96` (present — normal header) |
| Complement (0xBD) | `0xD9`; header checksum (0xBE–BF) = `0x0000` |
| Entry word (0x00) | `0xEA00002E` — stock `b` branch, **not** a cracktro/trainer patch |
| MD5 | `5cbca58a164385a5b256fff5c27b7f38` |
| SHA-1 | `07fafa1c96cc039a1788d6526d52f7d3ec0ba3c3` |
| SHA-256 | `eb27dbfd7fb468dee537075ebd8c76496082f20958f4ebce99e67d1689bf83d2` |

The GBA SKU was developed by **Halfbrick Studios**, not Krome (who made the console
versions). This matters because every published "cheat code" for Ty 3 is for the
GameCube/PS2/Xbox builds and uses a Krome engine that is not present here.

## 2. Executive summary

**No in-game password system, button-code system, or reachable hidden/debug menu was
found in this GBA image.** This is a *bounded negative* (§0.2 / §16.3 "no system"),
backed by a complete walk of every reachable screen, a full sweep of the game's
localisation key table and ASCII text banks, a targeted search for button-mask
sequences and code tables, complete disassembly of the input subsystem, and
in-emulator rejection of the published console codes adapted to GBA buttons.

What does exist, but is **not** a cheat:

* `MENU_LEVEL_SELECT` (localisation key ID 0x25D) and the displayed text
  `LEVEL SELECT` (0x087B603A) are present in the data banks, but no reachable
  screen exposes such a menu item. It is either progress-gated behind a 100%
  completion flag that was not attained, or an unused/cut entry. Classified as
  **gated/unverified**, not as a confirmed unlockable (§16.3 category 4).
* `invincible_flag` (0x080D6F1C) is an **actor script property name** in the
  object-property table (alongside `holding_boomerang_flag`, `hurt_flag`, etc.),
  not a cheat flag or code validator.
* `'GOD=<=A@1$#%7??:1'` (0x081B76F0) is one of hundreds of random printable
  ASCII runs in a high-entropy (compressed asset) region, with **zero** 32-bit
  pointer references. It is not a code (§16.8).
* `"E3 Demo"` / `"Build: 041220-002p"` (0x087AF7C6/DE) are build-info strings.
* `"Level Editing:"` (0x087CB73E/0x087CBC6E) is a **credits role category**, not
  a debug menu.
* `"  Enter level"` (0x087B3167) is a **Crabmersible vehicle control hint**
  (grouped with `Direction`, `Accelerate`, `Fire`), not a level-select prompt.

The published console codes were tested in gameplay in three GBA-adaptations;
none changed the ARRANGE (rang chassis) screen or any observable state.

## 3. How to reproduce

Emulator: mGBA 0.10.5 under Xvfb `:315`, `SDL_AUDIODRIVER=dummy`, `-3` scale.
Default SDL keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`,
D-pad=arrow keys. Hold keys 80–150 ms.

Screen path (all screens walked):

1. Boot: Activision logo → legal text → "Press Start".
2. **Title**: only `NEW GAME` and `OPTIONS`. Pressing Start toggles between the
   collapsed "Press Start" prompt and the two-item menu.
3. **OPTIONS**: `Music`, `Sound`, `Display: GBA SP`, `Credits`. Credits scrolls a
   text roll (Krome / Halfbrick / Activision Value); `B` returns.
4. **NEW GAME**: three save slots, each initially `0% NEW`, with `ERASE`.
   Selecting a slot plays the game intro cutscene (mash A) into gameplay.
5. **Gameplay**: first snow/ice area, Ty + green rang opponent.
6. **Pause menu (Start)** — three pages selected with L/R:
   * L page: `ARRANGE` (rang chassis / appearance, 3 slots).
   * centre page: `CONTINUE`, `EXIT GAME`.
   * R page: `CALL SHEET` / missions — initially `No Missions Available`.

Debug-combo probes at the title screen (each held 250 ms, screen captured):
`L+R`, `L+R+Start`, `L+R+Select`, `A+B+Start+Select`, `Select`,
`Start+Select`, `L+R+A+B`. **None** opened a hidden menu or changed the menu
item count; the only state change was A/Start legitimately entering NEW GAME.

Published-code probes in gameplay (each entered at normal speed, then ARRANGE
screen re-checked against a captured baseline):

* `Start,Start,A,Start,Start,A,B,A,B,A` — no change
* `Start,Start,B,Start,Start,B,A,B,A,B` — no change
* `Start,Start,A,Start,Start,A,A,B,A,B` — no change

These are GBA adaptations of the console `Start,Start,Y,Start,Start,Y,X,B,X,B`
(all chassis) / `…X,A,X,A` (100,000 opals) codes.

## 4. Address map

| Address | Meaning | Evidence |
|---|---|---|
| `0x08000000` | ROM base | header |
| `0x080BD774` | input helper: hold-duration-on-release | Disassembly |
| `0x080BD858` | input helper: hold-duration-while-held (17 BL callers) | Disassembly |
| `0x080BD930` | reset input counters | BL caller `0x08000268` (crt0) |
| `0x080BD958` | wrapper → `0x080BD9E4` (input poll) | BL scan |
| `0x080BD970` | "just pressed" test (144 BL callers) | BL scan |
| `0x080BD998` / `0x080BD9B8` | held-combination tests | BL scan |
| `0x080BD9E4`–`0x080BDA2C` | **input poll**: reads `0x04000130`, inverts to active-high, updates state and 10 hold counters | Disassembly |
| `0x080BDA14` | literal pool word `0x04000130` (KEYINPUT) | Disassembly |
| `0x02004410` / `0x02004412` | previous / current active-high button state (u16) | Disassembly + savestate RAM |
| `0x02004420` | 10 × u32 per-button hold-duration counters | Disassembly + savestate RAM |
| `0x080D6F00`–`0x080D7010` | actor script property-name table (`invincible_flag`, `code`, `hurt_flag`, …) | `strings` + `xxd` |
| `0x087B5800`–`0x087C4000` | English displayed-text bank (length-prefixed ASCII; 2,978 strings across all banks) | `strings` + `xxd` |
| `0x087B603A` | text `LEVEL SELECT` | `xxd` |
| `0x087C8000`–`0x087C…` | localisation key table: 36-byte entries `{u16 id, char[34] name}` | `xxd` |
| `0x087C9A1E` | key `MENU_LEVEL_SELECT`, id `0x025D` | `xxd` |
| `0x081B76F0` | false-positive ASCII run in compressed data | pointer scan (0 refs) |

Savestate note: mGBA `.ss1` is a PNG whose `gbAs` chunk zlib-decompresses to a
397,312-byte raw state (§16.13). Header/CPU at raw `+0x0000`, IWRAM at `+0x19000`,
EWRAM at `+0x21000`. The input state was read at raw `+0x25410` (= `0x02004410`)
and the hold counters at raw `+0x25420` in the captured state. This was the RAM
evidence path used because the mGBA GDB stub returned protocol errors
(`Ignoring packet error` / `vMustReplyEmpty: timeout`) on this build.

## 5. Algorithm

There is no password/checksum algorithm to reconstruct. The only reverse-engineered
algorithm is the **input subsystem**, which was fully disassembled to rule out a
hidden validator:

```
# 0x080BD9E4 (called once per frame from 0x080BD958)
prev = state[0]                 # 0x02004410
state[0] = state[2]             # shift current -> previous
state[2] = ~KEYINPUT & 0x3FFF   # active-high button mask, 0x04000130
for i in 0..9:                  # 10 buttons
    bit = 1 << i
    if prev & bit:  counter[i] += 1    # 0x02004420 + i*4
    else:           counter[i]  = 0
```

Helpers at `0x080BD774` / `0x080BD858` return `counter[i]` for a given button
on release / while held. Call sites use ordinary gameplay thresholds (e.g.
`cmp r0,#12; bls` at `0x08036B86`, i.e. ignore holds ≤ 12 frames) for charging
and debouncing. **No call site compares a hold count to a cheat constant, and no
function in this cluster writes a cheat/flag word.** The button-bit → counter-index
table at `0x080DB824` (`08 08 10 10 20 20 40 40 08 10 08 20 …`) is a
control-scheme lookup table referenced from 6+ ordinary gameplay functions, not
a cheat sequence.

## 6. Tables

| Item | Value / count |
|---|---|
| Localisation keys in scanned region (`0x087C8000`–`0x087CD000`) | **718** |
| Keys containing `CHEAT`, `PASSWORD`, `DEBUG`, `UNLOCK`, `BONUS`, `SECRET` | **0** |
| Keys containing `LEVEL SELECT` | **1** (`MENU_LEVEL_SELECT`, id 0x25D) |
| Displayed-text strings scanned (`0x087AF000`–`0x087C8000`, all languages) | **2,978** |
| Password/cheat-entry text prompts (`PASSWORD`, `ENTER CODE`, `ENTER PASSWORD`) | **0** |
| Reachable menu items: title / options / pause pages | **2 / 4 / 2+1+1** |
| Save slots | **3** (0x280-byte stride; `.sav` 8,192 bytes) |
| Hold-duration counters | **10** (buttons A,B,Select,Start,R,L,U,D,R-trigger,L-trigger) |

Console cheat sequences (published; **console SKUs only, not this ROM**):

| Effect | GameCube | PS2 | Xbox |
|---|---|---|---|
| All rang chassis | `Start,Start,Y,Start,Start,Y,X,B,X,B` | `…,○,□,○,□` | `…,B,X,B,X` |
| 100,000 opals | `Start,Start,Y,Start,Start,Y,X,A,X,A` | `…,○,×,○,×` | `…,B,A,B,A` |

## 6b. Enumeration

**Space definition.** There is no code space to enumerate: the ROM contains no
password alphabet, no code-entry UI, no validator, and no developer-intended
button sequence. The enumeration therefore consists of the bounded searches
below, each with an explicit count.

| Search space | Method | Count | Result |
|---|---|---|---|
| Reachable screens | Manual walk in mGBA (§3) | 8 distinct screens (title, options, credits, new-game slots, intro, gameplay, pause×3 pages) | No password/cheat/level-select entry on any screen |
| Title-screen debug combos | 7 simultaneous-button probes with screen capture | 7 | 0 hidden menus |
| Published console codes, GBA-adapted | 3 sequences entered in gameplay; ARRANGE screen compared | 3 | 0 state changes (rejected) |
| Localisation keys | Full `strings` dump of key table | 718 | 0 cheat/password/debug/unlock keys |
| Displayed text (all languages) | Full `strings` dump of text banks | 2,978 | 0 password/code prompts |
| Button-code prefix `[Start,Start,X,Start,Start,X]` | literal byte search, u16 active-high, u16 active-low (raw), u8; X over all 10 buttons | 30 encodings × whole 8 MiB | **0 hits** |
| Generic `[8,8,?,8,8,?]` u16 scan | every 2-byte offset | whole ROM | **0 hits** |
| Button-mask arrays (raw) | u16 runs of ≥4 values from {1,2,4,8,0x10,0x20,0x40,0x80,0x100,0x200} | 1,105 runs | all in compressed asset regions |
| Button-mask arrays (pointer-referenced) | filter the above by 32-bit ROM pointers from code region | 9,207 candidate pointers → **5 arrays** | all 5 are control-scheme/literal-pool tables, **0 cheat tables** |
| Console cheat effect constant | 100,000 / `0x186A0` search in code region | 0 occurrences | console opal reward not ported |
| Input subsystem | Full Thumb disassembly `0x080BD774`–`0x080BDA2C` + BL scan of 6 helpers | 6 helpers, 0/17/1/22/144/24 callers | no validator, no flag write |
| Suspicious ASCII `'GOD=…'` | 32-bit pointer search for its address | 0 references | not a code |

**Novel code:** not applicable — no code system exists to mint from. No code is
claimed.

**Bounds proven by rejection:** the three GBA-adapted console codes were entered
on the real gameplay screen and produced no change in the ARRANGE chassis list;
the seven title-screen button combos produced no extra menu items. These are
observed in-game rejections, not inference.

**Unverified gate:** `MENU_LEVEL_SELECT` / `LEVEL SELECT` text exists with no
reachable UI entry. Attaining 100% completion (or otherwise flipping the save
gate) was out of scope for this pass, so this entry is reported as gated/unused
rather than confirmed reachable. Its key id (0x25D) has **0** literal references
in the code region, which suggests the string is unused by the retail front end.

## 7. Validation evidence

* **Observed** — emulator screenshots: every screen in §3; ARRANGE baseline vs.
  each of the three code attempts (identical chassis list); seven combo probes.
* **Observed** — savestate RAM extraction: input state at `0x02004410`, zeroed
  hold counters at `0x02004420`, consistent with the disassembled input poll.
* **Derived** — full Thumb disassembly of the input subsystem; the bit→index
  mapping; the localisation key/text structure; the 0-reference result for the
  suspicious ASCII run and for `MENU_LEVEL_SELECT`'s id.
* **Inferred** — `LEVEL SELECT` is progress-gated or cut (not proven reachable);
  the console codes are absent because the GBA build uses a different engine.
* **Tooling limitation** — the mGBA GDB stub was unusable on this build; RAM
  evidence was obtained via savestate decoding instead. No debugger call into a
  validator was possible because no validator was found.

## 8. Unknowns

1. Whether `MENU_LEVEL_SELECT` becomes reachable after a 100% save; the gate
   flag and its writer were not isolated. No controller input path to it was
   found on any walked screen.
2. The exact mapping of the 0x280-byte save-slot fields (the displayed `0%`
   is likely derived from collectible bitfields rather than a single byte).
3. Whether any *link/transfer* feature (the GBA build is single-player per
   Wikipedia) could set hidden flags — no such UI exists in this ROM.

## 9. Tooling

Scripts written for this engagement (all in `/tmp/ty3`, not shipped):

* `scan_buttons.py` — literal button-prefix search in u8/u16 active-high/raw.
* `scan_input.py` — `0x04000130` literal and LDR-reference scan.
* `scan_refs.py` — RAM-address xref scan.
* `scan_maskarrays.py` — raw u8/u16 button-mask run scan.
* `scan_ref_arrays.py` — pointer-referenced mask-array filter.
* `scan_bl.py` — Thumb BL caller scan for input helpers.
* `scan_effects.py` — search for console cheat effect constants.
* `parse_state.py` — mGBA `.ss1` `gbAs` chunk decoder → RAM snapshot.
* `combos.sh`, `test_codes.sh`, `goto_game.sh` — xdotool input harnesses.

Toolchain: mGBA 0.10.5, Xvfb, openbox, xdotool, scrot, ImageMagick,
`arm-none-eabi-objdump`, Capstone, gdb-multiarch (stub unreliable), Python 3.

## 10. Legal note

No ROM image or copyrighted asset is reproduced here. Only hashes, addresses,
counts, algorithms, and screenshots of on-screen state were recorded.

*Report completed 2026-11-20. Analyst reached all reachable screens independently;
no findings were taken from sibling Ty-game analyses.*
