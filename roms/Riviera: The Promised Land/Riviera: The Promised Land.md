# Riviera: The Promised Land (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Riviera: The Promised Land.gba` |
| Size | 33,554,432 bytes (0x02000000, 32 MiB) |
| Header title | `RIVIERA` (at 0xA0) |
| Game code | `BREE` (at 0xAC) |
| Maker code | `EB` (at 0xB0) |
| Version | 0x00; fixed byte 0x96 OK; complement 0x9A; header checksum 0x0000 |
| Entry branch | `0xEA00002E` → `0x080000C0` (stock crt0) |
| Embedded GBA headers | exactly **1** (the header at file 0x0; 156-byte Nintendo logo occurs once) — not a multi-game pack |
| Patch / trainer | none found (no cracktro/trainer strings; stock entry word and logo) |
| Build stamp in ROM | `May 12 2005 / 14:51:52` at file `0x8B2E4` — matches TCRF's US build ID `8B2E4`; this is the **US revision** |
| MD5 | `16b5f1c6f8567cbe42f7562fccbb6426` |
| SHA-1 | `30ee6610aaa77bce2ffd8911058078147d61b925` |
| SHA-256 | `9c11c7c147eed526318ad471af4c8c3edd2d2d7c0ea68ce01877489ecc8a6626` |

File offset → ROM address for the low 16 MiB is `0x08000000 + offset`. Strings in the upper half are referenced through the `0x09xxxxxx` mirror; e.g. `0x0900E5E4` is file offset `0x0100E5E4`.

## 2. Executive summary

This game has **no password/button-code system**, but it does contain a developer-intended **hidden "Start Stage" debug menu** on the title screen, plus an "Extra Contents" unlockables menu.

The title screen has four selector slots but only three are selectable. The fourth is gated by a **single signed byte in EWRAM, `0x0200AEC8`**, which is the title-menu selection index itself:

* `-1 (0xFF)` = attract/idle, `0` = Game Start, `1` = Continue, `2` = Extra Contents, **`3` = hidden "SELECT START STAGE"**.

The game's own Down handler wraps `2 → 0` (`0x0803B554–0x0803B562`, `r4 = 0`), so controller input alone can **never** produce 3 — this is a **gated** hidden debug menu (guide §16.3 case 4), not a button code. Setting that byte to 3 and pressing A opens a black debug screen titled `SELECT START STAGE` with a single-selector list of **81 entries (indices 0–80)**.

TCRF publishes the memory-code equivalent (`3200AEC8 0003`); the literal address `0x0200AEC8` is present twice in the ROM (`0x0803AF6C`, `0x0803B094`) and the gate was verified dynamically. That CodeBreaker code is **not** a finding of this report (memory-edit codes are out of scope) — it is used only as a published anchor to locate the developer menu, which was then reached, walked and enumerated on the real screen.

The 81 stage-select entries include **undocumented content absent from TCRF/GameFAQs/VGChartz**: `13 TOWN CAP5`, `14 TOWN CAP6`, `15 TOWN CAP7`, `16 GO TITLE`, and 64 generated stage entries `17..80` rendered as `"NN c-s TITLE"`. A novel entry (**index 80, `80 8-1 TITLE`**) was activated on the real screen, produced a distinct gameplay scene, and the selection value was observed in game state at `0x0200B320`.

"Extra Contents" (title option 2) is an unlockables screen with eight `?????` entries; on a fresh save all are locked and the on-screen character says "Not available yet...". Its UI strings are **font/tile-indexed** (no ASCII hits), so the negative is based on rendered screens, not on `strings`.

## 3. How to reproduce

**Environment:** `Xvfb :317 -screen 0 1024x768x24`, `openbox`, `SDL_AUDIODRIVER=dummy`, mGBA SDL build, 3× scale. Input via XTEST on the focused mGBA window; A = `x`, B = `z`, Start = `Return`, L = `a`, R = `s`, D-pad = arrow keys (verified: holding `x` makes `KEYINPUT 0x04000130` read `0x03FE`).

**Deterministic route to the hidden menu:**

1. Boot the ROM; press Start repeatedly to skip the Nintendo/Sting/Ragnarok intros until the title screen (3 options + a dimmed fourth line behind the copyright text).
2. Attach mGBA's command-line debugger (`mgba -3 -d`) and, while paused, write the gate byte:
   * `w/1 0x0200AEC8 3`
   * verify `r/1 0x0200AEC8` → `0x03`
3. `c` (continue), press **A** (`x`) once.
4. The black `SELECT START STAGE` screen appears with `0 NORMAL`.
5. Navigate the selector with **Left/Right** (Up/Down do nothing here). The selected index is readable at `0x02006068` (`r/2`), the sub-state at `0x02006051`.
6. Press **A** to launch the selected stage/chapter; observe the write of the index to `0x0200B320` (set `watch/w 0x0200B320` before pressing A).

Screenshots are kept in `/tmp/riviera/` (`stage3c.png` = menu entry, `ss1c.png` = `1 CHAPTER1`, `act80c.png` = novel index 80 gameplay, `extra2c.png` = Extra Contents, `oor81c.png` = out-of-range label, `oor81actc.png` = corrupted launch).

## 4. Address map

| Address | File offset | Meaning | Evidence |
|---|---|---|---|
| `0x0200AEC8` | EWRAM | title-menu selection byte (`-1,0,1,2,3`); the hidden-menu gate | observed read/write + watchpoint |
| `0x0803B4C8–0x0803B4D2` | `0x3B4C8` | initialises gate from save flag (`0x803ADC0` result: 0 or 1 only) | derived (disassembly) |
| `0x0803B528–0x0803B534` | `0x3B528` | Up: `S--`, wrap to 2 | derived |
| `0x0803B554–0x0803B562` | `0x3B554` | Down: `S++`, if `S>2` then `S=r4(=0)` → **3 unreachable** | derived |
| `0x0803B6A0` | `0x3B6A0` | title-option dispatch table (5 pointers, base `0x0803B6A0`) | derived |
| `0x0803B6E8` | `0x3B6E8` | `SceneCreate(41, 0x0803BDD1)` — start stage-select scene | derived |
| `0x0803BDD0` (`0x0803BDD1` Thumb) | `0x3BDD0` | stage-select scene handler; sub-states 0–3 at `+9` | derived + live breakpoint (r0 = struct) |
| `0x02006048` | EWRAM | observed stage-select scene struct; `+9` = sub-state, `+0x20` = index | observed |
| `0x02006068` | EWRAM | stage-select selector index (u16, 0–80) | observed (Left/Right) |
| `0x0803BE84` | `0x3BE84` | stage-select input handler; Left/Right bounds 0x50 = 80 | derived |
| `0x0803BED6` | `0x3BED6` | `str r0,[r1,#0]` writes selected index into game state `0x0200B320` | observed via watchpoint |
| `0x0200B320` | EWRAM | game-state slot receiving the chosen stage index | observed (watchpoint new/old values) |
| `0x0800E5E4` (mirror `0x0900E5E4`) | `0x100E5E4` | 17-entry pointer table to labels `0 NORMAL` … `16 GO TITLE` | derived |
| `0x0800AE04` | `0xAE04` | `16 GO TITLE` | strings + render |
| `0x0800AE34` | `0xAE34` | `13 TOWN CAP5` (undocumented entry) | strings + render |
| `0x0800AF04` | `0xAF04` | `0 NORMAL` | strings + render |
| `0x0800AF14` | `0xAF14` | `SELECT START STAGE` (screen title) | pointer at `0x0803BE7C` |
| `0x0800AF28` | `0xAF28` | format `"%2d %d-%d"` for generated stage labels | strings + render |
| `0x08093AEC` | `0x93AEC` | ASCII debug leftover `DEBUG LOAD INFO` (no code xref found) | strings |

## 5. Algorithm

```
; title selector (EWRAM byte S = [0x0200AEC8], signed)
init:   S = (save_flag_byte & 0x0F) != 0 ? 1 : 0        ; 0x0803B4C8
idle:   after ~0x09D7 frames S = 0xFF                   ; 0x0803B584
up:     S = S - 1; if S < 0 then S = 2                  ; 0x0803B528
down:   S = S + 1; if S > 2 then S = 0                  ; 0x0803B554  <-- gate
A/ok:   dispatch[S] (table 0x0803B6A0):
          S=0 -> normal game
          S=1 -> Continue scene
          S=2 -> Extra Contents
          S=3 -> SceneCreate(41, 0x0803BDD1)  ; hidden Start Stage

; stage-select scene (struct at 0x02006048)
idx = [struct+0x20]                                     ; 0x02006068, u16
left:   idx--; if idx & 0x8000 then idx = 0x50 (80)     ; 0x0803BE96..BEA6
right:  idx++; if idx > 0x50 then idx = 0               ; 0x0803BEBC..BEC6
label:  idx in 0..16 -> string_ptr[idx] from table 0x0800E5E4
        idx in 17..80 -> printf("%2d %d-%d TITLE", idx, chapter, stage)
accept: [0x0200B320] = idx                              ; 0x0803BED6 (verified)
```

The title gate is **not** a checksum code: it is a raw state byte. The space of the hidden menu is exactly the 81 reachable selector values; there is no separate validator to invert.

## 6. Tables

**Title selector byte `0x0200AEC8`:**

| Value | Meaning | Reachable by controller? |
|---|---|---|
| `0xFF` (-1) | attract / idle timeout | yes (idle) |
| `0` | Game Start | yes |
| `1` | Continue | yes (if save flag set) |
| `2` | Extra Contents | yes |
| `3` | **hidden Start Stage** | **no** — Down wraps `2→0` |

**Stage-select labels (indices verified by rendering and by the pointer table):**

| Index | Label | Published? |
|---|---|---|
| 0 | `0 NORMAL` | yes (TCRF) |
| 1–8 | `1 CHAPTER1` … `8 CHAPTER8` | yes (TCRF) |
| 9–12 | `9 TOWN CAP1` … `12 TOWN CAP4` | partially (TCRF mentions chapters only) |
| 13–15 | `13 TOWN CAP5`, `14 TOWN CAP6`, `15 TOWN CAP7` | **no** |
| 16 | `16 GO TITLE` | **no** |
| 17–80 | `17 1-1 TITLE` … `80 8-1 TITLE` (64 entries) | **no** |

**Extra Contents:** 8 entries, all displayed `?????` on a fresh save; B returns to title. Hidden dev strings also present in ROM: `AGBRIVIERA-SYS1/DAT1/DATA` (xref'd at `0x08074E44` etc.), `DEBUG LOAD INFO`, `SRAM FLAG : %04x`, `GAME CLEAR`, `CHAP8 CLEAR` — no reachable screen displaying these was found (see §8).

## 6b. Enumeration

**Space size:** the hidden menu's selector is a single u16 index with envelope 0–80 (the input handler clamps at `0x50`), so **81 values** are expressible by controller. The label table has 17 real string pointers; indices 17–80 are synthesised from `"%2d %d-%d"` + `"TITLE"`. There is no checksum and no second field.

**Full-set proof (§16.9 style):** Right/Left steps were taken through the entire range and every rendered label was captured/OCR'd — indices 0,1,…,80 all render a label. Circular bounds were proven in RAM:

* write `0x50` (80) to `0x02006068`, press Right → read back `0x0000` (wrap to 0).
* write `0x0000`, press Left → read back `0x0050` (wrap to 80).

Therefore no controller sequence can express index ≥ 81.

**Novel code / unpublished entry:** index **80** (`80 8-1 TITLE`) is absent from TCRF, GameFAQs and VGChartz. Reached by one Left press from index 0 (RAM index read `0x0050`), then A on the real `SELECT START STAGE` screen. Observed effect: a distinct gameplay scene (`act80c.png`, blue-lit stage) and selector index reset to 0. A second novel-class entry, index **1** (`1 CHAPTER1`), was used for the clean write proof below.

**RAM proof of effect (watchpoint at `0x0200B320`):**

* index 1 + A → `Hit watchpoint: new value = 0x00000001, old = 0x00000000`, `r0=1`, `r1=0x0200B320`, PC `0x0803BEDA`, from `str` at `0x0803BED6` followed by the chapter-1 opening scene (`ch1c.png`).
* index 81 (injected, not controller-reachable) + A → `new value = 0x00000051`, i.e. **81 is written unchecked** into the game-state slot; the label at 81 degrades to `80 8-1` with the `TITLE` field missing (`oor81c.png`) and launching it produces corrupted graphics with the debug title bleeding through (`oor81actc.png`). This proves the semantic bound is enforced only by the input wrapper, not by the accept routine.

**Published-code verification:** TCRF's `3200AEC8 0003` decodes to a byte write of `3` at `0x0200AEC8`; that exact literal exists in the ROM at `0x0803AF6C` and `0x0803B094`, and writing 3 + A reproduces the menu. No password literals, key-mask tables or button codes were found (see §8), and the GameFAQs "Patch Codes" (FAQ 37820) are GameShark memory patches, not in-game codes; VGChartz's six "cheats" are walkthrough tips.

## 7. Validation evidence

* **Observed:** `0x0200AEC8 = 0` at title; `w/1 … 3` then A opens `SELECT START STAGE` (`stage3c.png`); selector index reads `0x0000`, `0x0001`, `0x0050`, `0x0000` across Left/Right tests; all 81 labels rendered; watchpoint at `0x0200B320` captured writes of `1` and `0x51`; index 80 and index 81 launches produced distinct scenes; Extra Contents shows eight locked `?????` entries with "Not available yet..." (`extra2c.png`); KEYINPUT verified the A keymap.
* **Derived:** gate initialisation and down-wrap from disassembly (`0x0803B4C8`, `0x0803B554`); stage-select handler and its 4 sub-states (`0x0803BDD0`); label pointer table at `0x0800E5E4`; scene-creation call `0x0803B6E8`; bounds arithmetic at `0x0803BE84–BEC6`; accept write at `0x0803BED6`.
* **Inferred:** the third `TITLE` column is an unpopulated stage-name field in this debug build (rendered identically for every generated index); `13–15`/`16` are leftover debug destinations rather than player content. The `DEBUG LOAD INFO` text bank is a development leftover with no located caller.

`§16.19` oracle technique was used in the debugger sense: the live gate/index bytes and watchpoints, not visual inference alone, were treated as ground truth for every claim.

## 8. Unknowns

* No in-game controller or password route to gate value 3 was found: the only writer of `0/1` is `0x0803B4D2` (from a save flag) and the Down handler wraps `2→0`; the value can only be injected by external memory access. Under guide §16.3 this is a **gated** feature, not dead code (the menu demonstrably works once gated open).
* `DEBUG LOAD INFO`, `LOAD DATA READ`, `SRAM FLAG : %04x`, `GAME CLEAR`, `CHAP8 CLEAR` (all at `0x08093AEC`+) have no direct 32-bit pointer xref; whether an obscure key combination displays them was not proven. They are reported as development leftovers, not as reachable screens.
* How the eight Extra Contents entries unlock (likely game-clear/chapter-clear save flags) was not exercised — no cleared save was available, and the strings for that menu are tile-indexed rather than ASCII. The negative "all locked on a fresh save" is bounded to that state.
* The meaning of `0x0200B320` after the scene consumes the index was not traced beyond the observed write.

## 9. Tooling

* `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings -t x`, Python 3 structural scans (literal/pointer/BL tables).
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for the disassembly excerpts; Capstone 5.0.7 available for literal-load scans.
* REA skill loaded per guide §1; raw GBA analysis done with objdump + emulator (REA/Ghidra not required for these small ranges).
* mGBA SDL with `-d` command-line debugger driven through a PTY (`script` + FIFO) because the `-g` GDB stub was unreliable in this build; commands used: `status`, `r/1`, `r/2`, `r/4`, `x/4`, `w/1`, `w/2`, `b/t`, `watch/w`, `delete`, `c`, `reset`.
* `xdotool` XTEST input, `scrot` + ImageMagick `convert`, `tesseract` for bulk label OCR (the GBA font is stylised, so final label reads were confirmed visually and against ROM strings).

**Legal note:** no ROM bytes, graphics, audio or game text are redistributed here; only hashes, addresses, algorithms, and observations.
