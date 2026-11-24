# The Flintstones: Big Trouble in Bedrock (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `The Flintstones: Big Trouble in Bedrock.gba` |
| Size | 4,194,304 bytes (`0x400000`) |
| Header title (`0xA0`) | `FSTONES BTIB` |
| Game code (`0xAC`) | `AFSE` (region `E` = USA) |
| Maker (`0xB0`) | `5Z` |
| Version (`0xBC`) | `0x00` |
| Entry branch (`0x00`) | `0xEA00002E` — **stock** (no scene-release cracktro, §16.1) |
| Fixed byte `0xB2` | `0x96` |
| Complement `0xBD` | `0x40`; header checksum `0xBE` = `0x0000` (rebuilt-header artifact, §16.1) |
| MD5 | `a73253d79628d92c2fee1e9d2bbd6ff5` |
| SHA-1 | `7621ae8d6110d8c7d41cde336d67e0e44cdbf48b` |
| SHA-256 | `14a826b7e9e44f479b6bfccccbad2ddec638d01665710ed51b9003231b545e65` |

Engine: custom H2O Entertainment / Conspiracy Entertainment engine with MusyX audio; source-module strings `./src/*.c` survive in the image.

## 2. Executive summary

**No in-game cheat system exists in this ROM.** There is no password entry, no button-code sequence, no hidden/debug menu and no cheat table. This is a **bounded negative**, proved by counts (§6b), not an absence of searching.

The strongest evidence is structural:

1. The game has exactly **8 application scenes**, recovered statically from the scene dispatcher at `0x08004A4`. All 8 are identified by their surviving `./src/*.c` error strings: cutscene view, splash, map screen, option menu (×2), credits, legal screen and language select. None is a password, cheat or debug screen.
2. There is exactly **one** `KEYINPUT` (`0x04000130`) reader in the whole 4 MiB image — the poller at `0x080123A0`. It converts to active-high and increments **eight per-button hold counters**; it holds no press-history buffer and performs no sequence comparison. Only three literal pointers to its input-state struct exist, all inside that one function.
3. Every text bank that survives as ASCII was extracted and read: 43,433 strings total, of which 457 are `{C:nn}{B/N}`-tagged script records (391 unique) — **all of them are credits roll staff names and roles**. Zero matches for `password`, `cheat`, `code`, `secret`, `debug`, `level select`, `unlock` in any bank. A second, tile-index font renders the menus; its strings are not ASCII, but the complete menu item set is fixed in code and was enumerated by walking every screen (titles 2, Options 6, Pause 2, quit-confirm 2) — none is a cheat entry.
4. Web recon (§3.4) found **no published password/cheat list** for this title (search integrations returned no results; 3rd party cheat indexes returned HTTP 403). No literal from a published list was available to seed a table search, so the negative rests on the static and dynamic counts above.

No GameShark/CodeBreaker/Action Replay codes were used or reported (out of scope).

## 3. How to reproduce

* Emulator: mGBA 0.10.5, `SDL_AUDIODRIVER=dummy`, Xvfb `:318`, `mgba -d -3 <rom>`.
* Keymap (mGBA SDL): A = `x`, B = `z`, Start = `Return`, Select = `BackSpace`, D-pad = arrows. Hold keys 100–150 ms.
* Debugger: `mgba -d` command-line debugger over a pty; `BREAK` sends Ctrl-C, then `r/4 <addr>`, `continue`.
* Screen path:
  * Title: `START` / `OPTIONS` (screens `game0`, `title_down`).
  * `OPTIONS` → `Difficulty` (Left/Right: Easy / Medium / Hard), `Control Setup` (Right: Type A / Type B), `SFX` (0..≥35, Left/Right), `Music` (0..≥20), `Credits` (scrolling roll), `Main Menu` (`options`, `opt_diff_left`, `opt_diff_right`, `control_r`, `credits1`, `credits2`).
  * `START` → intro cutscene (advance with A) → gameplay with HUD `lives ×` / `gems ×` (`cutscene_after`, `play_start`).
  * Gameplay + Start → `Pause`: `Continue` / `Quit` → `Are you sure?`: `No` / `Yes` (`pause`, `after_mainmenu`, `nav_title`).
  * Playing right through level 1 reaches a level-clear map screen labelled `Crazy Quarry` (`play_jump`, `play_map2`).
* Savestates: `Shift+F1` writes `<rom>.ss1` in the ROM folder; these were parsed and then deleted (§9).

## 4. Address map

| Address | Meaning | Evidence |
|---|---|---|
| `0x08000000` | Stock ARM entry branch `0xEA00002E` | Derived |
| `0x0800023C` | Main loop; calls input poller at `0x08000260` | Derived |
| `0x08004A4` | Scene dispatcher: `r2 = [0x03008040]`, index `<= 7`, 8-entry jump table at `0x08004C8` | Derived |
| `0x080123A0` | Sole input poller: `~KEYINPUT`, writes held/pressed + 8 counters | Derived |
| `0x08012444` | Literal `0x04000130` (KEYINPUT) | Derived |
| `0x08012448` | Literal `0x03005F30` (input-state struct) | Derived |
| `0x08013D54` | ASCII text renderer: `tile = (char − 32) * 8`, 8×8 1-bpp font, `0x0A` = newline, NUL-terminated | Derived |
| `0x08002ABC` | Credits scene (error string `0x0802ED70`) | Derived |
| `0x08019C0`, `0x0800A738` | Option-menu scene handlers | Derived |
| `0x08007028` | Language-select scene | Derived |
| `0x08007230` | Legal-screen scene | Derived |
| `0x08003128` | Cutscene-view scene | Derived |
| `0x0800B7F8` | Splash scene | Derived |
| `0x080095D0` | Map-screen scene | Derived |
| `0x0806DD80`..`0x0806DE78` | Legal-screen ASCII strings (12 pointers at `0x080071CC`) | Derived |
| `0x0802E378`..`0x0802EDC8` | Credits script strings (`{C:nn}{B/N}` tokens) | Derived |
| `0x03005F30` | IWRAM input struct (see §6) | Observed (debugger) |
| `0x03008040` | Global state block used by the scene dispatcher | Observed (debugger) |

File offset ↔ ROM address: `rom = 0x08000000 + file_offset` (flat 4 MiB image, no multi-game headers; Nintendo logo searched, single header only).

## 5. Algorithm

There is no password/checksum algorithm to reimplement. The two relevant algorithms are:

**Input poller (`0x080123A0`)** — Thumb, once per frame:

```
held   = ~(*(u16*)0x04000130) & 0xFFFF
pressed = held & ~old_held
struct->held = held;  struct->pressed = pressed
for each button bit b in {0x40 Up, 0x80 Down, 0x20 Left, 0x10 Right,
                          0x04 Select, 0x08 Start, 0x02 B, 0x01 A}:
    if held & b: struct->counter[b] += 1
```

No ring buffer, no `last-N` matching, no XOR toggle — compare with §16.6.

**Text renderer (`0x08013D54`)**:

```
for each signed byte c of NUL-terminated string:
    if c == 0: stop
    if c == 10: y += 10; x = start; continue
    tile_byte_offset = (c - 32) * 8
    draw 8x8 1-bpp glyph from ROM font at font_base + tile_byte_offset
```

This proves the legal/credits banks are plain ASCII and that the renderer is not a validator.

## 6. Tables

**Input-state struct at `0x03005F30`** (all `u16`):

| Offset | Field | Button mask |
|---:|---|---|
| `+0x00` | held (active-high) | — |
| `+0x02` | pressed (edge) | — |
| `+0x04` | Up counter | `0x40` |
| `+0x06` | Down counter | `0x80` |
| `+0x08` | Left counter | `0x20` |
| `+0x0A` | Right counter | `0x10` |
| `+0x0C` | Start counter | `0x08` |
| `+0x0E` | Select counter | `0x04` |
| `+0x10` | A counter | `0x01` |
| `+0x12` | B counter | `0x02` |

**Scene jump table at `0x08004C8`** (8 entries, index from dispatcher):

| Index | Handler | Module (from error string) |
|---:|---|---|
| 0 | `0x08003128` | `cutsceneview.c` |
| 1 | `0x0800B7F8` | `splash.c` |
| 2 | `0x080095D0` | `mapscreen.c` |
| 3 | `0x0800A738` | `optionmenu.c` |
| 4 | `0x08002ABC` | `credits.c` |
| 5 | `0x08019C0` | `optionmenu.c` |
| 6 | `0x08007230` | `legalscreen.c` |
| 7 | `0x08007028` | `langselect.c` |

A further module, `clamscreen.c`, shares the option-menu state machine; no separate cheat scene exists.

**Options values (observed):** Difficulty ∈ {Easy, Medium, Hard}; Control Setup ∈ {Type A, Type B}; SFX and Music are numeric volume settings (SFX observed to 35, Music to 20; neither is a code field); Credits and Main Menu are scene transitions.

**ASCII→tile:** `tile = (char − 32) × 8` (8 bytes/glyph, bit 7 = leftmost pixel in each row, per the bit loop at `0x08013E10`–`0x08013E40`).

## 6b. Enumeration

This is a **bounded negative**. No code space exists, so no novel code could be minted; the four required §0.2 negative deliverables are supplied as counts:

1. **Space definition — empty.** No input alphabet, no code length, no field widths, no checksum width/position, no lookup table of accepted strings. Representable values: **0**. The only user-settable fields are the 4 Options settings above, all of which are ordinary configuration (difficulty 3, controls 2, two volumes), not unlock codes.
2. **Validator model — none.** No function reads a user string and compares it to a constant. Every `ldr`/`str` of the input state is inside the single poller; there is no `strcmp`/`memcmp` against an entry buffer (§16.2b: the only text field is absent).
3. **Novel code — not applicable.** There is no system to mint a code for. Instead: of the **8** statically enumerated app scenes, **0** are cheat/password/debug screens; of the **12** menu items across Title (2), Options (6), Pause (2) and Quit-confirm (2), **0** are cheat entries.
4. **Bounds proven by rejection/counts:**

| Search | Space checked | Result |
|---|---|---|
| Full-image `strings -t x -n 4` | 4,194,304 bytes | 43,433 strings; **0** cheat/password/debug/secret/unlock/level-select keyword hits |
| Script-token text bank | 457 records (391 unique) | **100% credits staff names/roles**; 0 cheat content |
| Menu-string transforms | raw, ±0x20, ±0x40, XOR 0x20/0x40/0x80/0xFF, bit-reverse, lower/upper, UTF-16LE/BE, NUL-interleaved, 16 tile bases — for `Options`, `Difficulty`, `Continue`, `Password`, `Cheat`, `Debug` | **0** hits; menu text uses a separate pre-rendered 8-bpp tile font |
| `KEYINPUT` (`0x04000130`) literals | whole ROM | **1** raw word + **1** Thumb PC-relative LDR (the single poller) |
| Input-state struct `0x03005F30` xrefs | whole ROM | **3** raw + **3** Thumb LDRs — all inside `0x08012390`–`0x08012452` |
| u16 button-mask-like runs | 1,249 runs of ≥4 plausible mask values | **0** form a button sequence; all are palette/lookup/graphics data |
| Konami prefix `UUDDLRLRBA` | active-high/active-low × u16/bytes, whole ROM | **0** hits (one coincidental `UUDD` byte hit at file `0x3D17DA`, inside compressed graphics) |
| App scenes | 8 dispatcher entries, all handlers disassembled | **0** debug/cheat/password scenes |
| Published codes (web recon) | multiple search engines + 3 direct sites | **0** lists found; 3rd party cheat indexes HTTP 403, DDG bot challenge |

Because no accepted set exists, §16.9's "run the validator over the whole space" degenerates to "the validator does not exist"; the negative is closed by the scene count, the input-xref count and the text-bank enumeration rather than by an untested assumption.

## 7. Validation evidence

* **Observed** (emulator screenshots, all saved under `/tmp/flintstones/`): title; Options and all six entries; three Difficulty values; Type A/B; scrolling Credits; legal/splash boot screens; intro cutscene; gameplay HUD and level-clear map `Crazy Quarry`; Pause; `Are you sure?` confirmation.
* **Observed** (mGBA `-d` RAM reads): input state at `0x03005F30` read as `0x0000FC00` with the game running; global state pointers at `0x03008040`= `0x03006DC8` (title/options phase); savestate `gbAs` chunk decompressed to a 397,312-byte state with IWRAM at offset `0x19000` (§16.13).
* **Derived** (static, verified against bytes): single `KEYINPUT` poller and its counter layout; 8-entry scene dispatcher and all 8 scene identities; ASCII text renderer formula; absence of any string/table comparison against user input.
* **Inferred**: The tile-font strings for the menu were not glyph-by-glyph decoded; the inference that no hidden menu entry exists rests on the fixed menu-item count in the OptionMenu state machine plus the complete screen walk, not on reading those tiles. This is labelled inference, not observation.

## 8. Unknowns

* Gameplay-only screens beyond the level-clear map (`Crazy Quarry`) were not exhaustively walked — a full game-over sequence was not completed. No code surface was observed in any gameplay screen, but this is not a proof about unreached game states.
* Collectible-based unlockables (the `gems ×` HUD counter) were not proven absent: testing that would require a full playthrough. The `.sav` created by mGBA was 0 bytes; no unlock-bit setter was isolated (§16.18).
* The language-select scene (dispatcher index 7) was not entered on this USA build; it is identified statically but its runtime gate was not exercised.
* Web sources were blocked (403 / bot challenge) and the websearch integration returned no results, so the "no published list" finding is bounded by those sources, not universal.

## 9. Tooling

* `file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings -t x` for Phase 0/1.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for all disassembly.
* Python + Capstone 5.0.7: `scans.py` (KEYINPUT literals, mask runs), `inputxref.py`, `blscan.py`, `ldrscan.py`, `ptrscan.py`, `find_text.py`/`find_text2.py` (encoding search).
* `mgba -d -3` driven over a pty (`mgba_dbg.py`, `dbg_server.py`, `dbg.sh`) for RAM reads; `parse_ss.py` to extract the zlib `gbAs` chunk from `.ss1` savestates.
* Reproduction artifacts (screenshots, scripts, parsed state) were left in `/tmp/flintstones/`. No ROM or copyrighted assets are redistributed by this report.

## 10. Cleanup

Own PIDs only were terminated by number: mGBA `555270`, debugger server `555269`/`555258`, openbox `550971`, Xvfb `:318` `550968` (an earlier mGBA `553830` had already exited). `pgrep` verified no Flintstones mGBA, no `:318` Xvfb and no debugger server remained; other agents' Xvfb/mGBA processes were left untouched. The generated `The Flintstones: Big Trouble in Bedrock.sav` and `.ss1` were deleted from the ROM folder, which now contains only the `.gba` and this report.
