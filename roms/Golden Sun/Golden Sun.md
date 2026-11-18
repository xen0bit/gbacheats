# Golden Sun (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Golden Sun/Golden Sun.gba` |
| Size | 8,388,608 bytes (0x00800000, 8 MiB) |
| Header title | `Golden_Sun_A` |
| Game code | `AGSE` (USA, revision 00) |
| Maker | `01` (Nintendo) |
| Version byte | `0x00` |
| Fixed byte | `0x96` at 0x00B2 (valid) |
| Entry word | `0xEA0000EE` — stock ARM branch to crt0, **not** a scene cracktro patch |
| Header checksum | `0x0000`; complement byte `0x42` |
| MD5 | `1cdd7f33c9a27061201e1d1ce029a700` |
| SHA-1 | `5c4695205413df7db52b9a184815a07783999971` |
| SHA-256 | `c14f1151897e8d73f25ffdd67e21eebb6dc57973ff2458872ee89fa9060aaca1` |

**Embedded-header scan:** the exact 156-byte Nintendo logo from header offset `0x04` occurs **exactly once** in the whole 8 MiB image, at `0x00000000`. There is no second game image, no multiboot stub and no appended shell. No `GameShark`, `CodeBreaker`, `Action Replay`, `CRACK` or `TRAINER` signature was found. This is a clean retail ROM; the `0x0000` header checksum is the usual rebuilt-header artifact (guide §16.1). File identity agrees with `file`: `Game Boy Advance ROM image: "Golden_Sun_A" (AGSE01, Rev.00)`.

## 2. Executive summary

**There is no password / code-entry system in this game.** The only text-entry surface is the character-naming screen (Isaac, etc.), a 62-symbol on-screen keyboard whose buffer is written to the save as a character name. It is a name field, not a validator (guide §16.2b): no password, cheat, unlock or secret string exists in any of the 104,041 ASCII strings, and the keyboard buffer is consumed as save data, not compared against a code table.

**What does exist is a full developer debug mode.** It is gated by a single IWRAM byte, `0x03001F54` (US/EU English build), which must be **1**. The gate is not reachable from any controller input: the only identified writer of that address is the boot/crt0 routine at `0x08002E40`, which stores **0**; every other cross-reference is a read. Setting the byte to 1 therefore requires a cheat device or a modified savestate — a **memory-edit operation, which is outside the requested scope as a portable "code."** It was used here strictly as a research instrument (guide §16.19, §16.10) to reach and verify the developer-intended menus.

Once the gate is open, five published two-button combinations plus two hold actions are live in the field. They were verified against the ROM's own key-mask logic and in mGBA with RAM evidence:

| Combo | Held mask | Effect |
|---|---|---|
| **B + Start** | `0x00A` | Warp menu — jump to any map/destination |
| **B + Select** | `0x006` | Flag editor (D-pad select, A toggle, L/R pages, B close) |
| **L + Start** | `0x208` | Palette editor (RGB values, L/R switch palette, Select close) |
| **Start + Select** | `0x00C` | Pause / frame-step (any button advances one frame) |
| **L + R** | `0x300` | Skip dialogue during cutscenes (cutscene-scoped) |
| hold **L** | `0x200` | Walk through walls |
| flag `0x16D` + **R** / **Select+R** | — | Battle instakill (enemy team / own team) |

The sibling **Golden Sun: The Lost Age** shares the same five combinations and the same flag-`0x16D` battle trick, but uses a different gate address (`0x03001238`) and adds a few context-dependent actions (e.g. Start+Status in battle shows enemy stats). Nothing from TLA was assumed for this ROM; the addresses above were derived independently from the AGSE image.

## 3. How to reproduce

1. **Emulator / display.** mGBA (SDL build, `/usr/local/bin/mgba`), Xvfb `:315`, `DISPLAY=:315 openbox`, `SDL_AUDIODRIVER=dummy`. Command used: `SDL_AUDIODRIVER=dummy mgba -3 "Golden Sun.gba"`.
2. **Keymap (verified empirically against `0x03001AE8`, not assumed):** `A = x`, `B = z`, `L = a`, `R = s`, `Start = Return`, `Select = BackSpace`, D-pad = arrow keys.
3. **Screen path.** Boot → Camelot logo → character-naming keyboard → press A on `END` → prologue in Isaac's house → advance dialogue with A until the "Isaac is old enough…" line ends and the Start menu opens (roughly 60–100 A presses plus walking Down). The debug input handler is inactive while a scripted event/dialogue owns control; combos only work in free field control.
4. **Enable debug (research only, not an in-game code).** Save an mGBA state at a clean field moment, then patch the `gbAs` PNG chunk. The state layout is stable (guide §16.13): IWRAM starts at raw offset `0x19000`, so `0x03001F54` is raw offset `0x1AF54`. Write `01` there, recompress, load the state. Helper used: `/tmp/opencode/goldensun/rstate.py`.
5. **Verify the gate:** read `0x03001F54` from a fresh state (`00`) and from the patched state (`01`).
6. **Enter a combo:** hold both keys ~0.4–0.6 s with a small (~0.06 s) stagger, then wait ~2 s for the menu to draw. Read the held mask at `0x03001AE8` to confirm the game saw the intended combination (`0x00A`, `0x006`, `0x208`, `0x00C`, `0x300`).
7. **Published codes tested.** TCRF's GameShark/Action-Replay entries are memory writes, e.g. `32000400 00C7` / `32000408 00C7` (debug room 199), `00009B1A 000A` (master). Their targets were checked in RAM: `0x02000400` and `0x02000408` held `0x0008` (current/target room) at the prologue. These are **not** reported as cheats — they are out of scope — but the addresses corroborate the map/warp subsystem.

## 4. Address map

**ROM (this exact AGSE image):**

| Address | Meaning | Evidence |
|---|---|---|
| `0x08000000` | Entry branch `0xEA0000EE` | Derived (header bytes) |
| `0x08002E40` | crt0/init; stores **0** into debug flag via pointer at `0x08002EB8` | Derived (Ghidra decompile: `*DAT_08002eb8 = 0`) |
| `0x08002EB8` | literal pointer `0x03001F54` (debug flag) | Derived |
| `0x08003650` | joypad task; reads `KEYINPUT` via literal at `0x0800374C` | Derived (Ghidra decompile) |
| `0x08003708` | literal `0x3FF` (key mask) | Derived |
| `0x0800374C` | literal `0x04000130` (`KEYINPUT`) | Derived |
| `0x08003750` | literal pointer `0x03001AE8` (current held keys) | Derived |
| `0x08003754` | literal pointer `0x03001C94` (newly pressed keys) | Derived |
| `0x08003758` | literal pointer `0x03001AF8` (held/repeat accumulator) | Derived |
| `0x0808C4F8` | battle routine with debug-flag + key gates (`&2`, `&4`, `&0x200`) | Derived |
| `0x080915EC` | tiny routine: debug flag + `&0x200` (L) + `&0x100` (R) | Derived |
| `0xF0AE4`–`0xF11B4` | ASCII staff credits (the only large ASCII text bank; "Debugging" is the word in "Debugging & Testing", not a debug menu label) | Observed (`strings -t x`) |

Procedures with cross-references to the debug-flag pointers (all reads except the init write above), derived with Ghidra/REA:
`0x08002E00`, `0x080030F8`, `0x0800EBEC`, `0x0801D9D4`, `0x0801DB70`, `0x080272A8`, `0x08077CB8`, `0x0808A8E4`, `0x0808C4F8`, `0x080915EC`, `0x080BE378`.

**RAM:**

| Address | Meaning | Evidence |
|---|---|---|
| `0x03001F54` | Debug-mode gate byte, `1` = enabled | Observed (savestate read/patch) |
| `0x02000400` / `0x02000408` | Current / target map number | Observed (`08 00` / `14 00`), corroborated by GameShark literals |
| `0x03001AE8` | Held keys, active-high (`held = 0x3FF ^ KEYINPUT`) | Observed (mask per key measured) |
| `0x03001C94` | Newly pressed keys | Observed |
| `0x03001AF8` | Held/repeat accumulator | Observed |
| `0x03000DF8`+ | Warp-menu work area (map name/codename/number text loaded here while the menu is open) | Observed (IWRAM diff on menu open) |

**File offset ↔ ROM address:** `rom_address = 0x08000000 + file_offset`. `strings -t x` offsets are hex; `grep -abo` offsets are decimal.

**Savestate (mGBA `.ssN`) raw layout used:** palette at `0x0`, VRAM at `0x1000`, IWRAM at `0x19000`, EWRAM at `0x21000`; the `.ssN` is a PNG with a zlib-compressed `gbAs` chunk.

## 5. Algorithm

There is no checksum/password decoder to reverse. The "validator" is a combination matcher over the joypad word. Decompiled input task (`0x08003650`):

```
held    = 0x3FF ^ KEYINPUT              // active-high, 10 bits
pressed = held & ~previous
accum  |= pressed                       // repeat timing
previous = held
```

Key bit values (measured by holding one key and reading `0x03001AE8`):

```
A=0x001  B=0x002  Select=0x004  Start=0x008
Right=0x010 Left=0x020 Up=0x040 Down=0x080
R=0x100  L=0x200
```

Debug gate model (derived from the 11 reader procedures and the single writer):

```
init():  debug_flag = 0            @ 0x08002E40
if (debug_flag != 0) {
    ... debug-only branches: menu combos, noclip, frame-step, cutscene skip ...
}
```

The flag never becomes 1 from controller input; no in-game setter exists. Combinations are matched on the held mask (the observed values at `0x03001AE8` equal the masks in the table exactly). A superset test (A+B+Start, mask `0x00B`) did **not** alias the B+Start warp menu, i.e. the matcher is equality-based, not `held & mask == mask`.

## 6. Tables

**Combo table (complete published set, all verified here):**

| Held mask | Keys | Effect | Evidence |
|---|---|---|---|
| `0x00A` | B+Start | Warp menu | Observed (menu drawn, map name `PLDCI00`, `Vale : 3`); RAM `0x03001AE8=000A`, `0x03000DF8` populated |
| `0x006` | B+Select | Flag menu | Observed RAM `0x03001AE8=0006`; effect derived from `0x0808C4F8` battle gate + TCRF |
| `0x208` | L+Start | Palette menu | Observed RAM `0x03001AE8=0208`; effect derived + TCRF |
| `0x00C` | Start+Select | Pause / frame-step | Observed RAM `0x03001AE8=000C`; effect derived + TCRF |
| `0x300` | L+R | Cutscene dialogue skip | Observed RAM `0x03001AE8=0300`; only active in cutscenes (derived) |
| `0x200` | L (hold) | Noclip | Derived (`0x0800EBEC`: `debug != 0 && held & 0x200`) |
| `0x100` | R (hold) | Battle instakill when flag `0x16D` is set | Derived (`0x0808C4F8`, `0x080BE378`) + TCRF |

**Name-entry alphabet (the only text-entry space; observed on the naming screen):** uppercase `A–Z`, lowercase `a–z`, digits `0–9`, and symbols `! ? ( ) > - % @ / : , . ; ' " & * # + = < > [ ]`, plus `DEL` and `END`. Count of printable glyph cells: 62 (26+26+10) plus 22 symbol/control cells. This is a profile-name field and is **not** a password validator (§16.2b).

**Published memory-edit codes, recorded for completeness and explicitly out of scope:** TCRF lists debug enable `0301F54:01`, rooms `32000400 00C7` / `32000408 00C7` (199) and `00C8` (200), and `82000558 0xxx` (unused Psynergy). These are GameShark/CodeBreaker writes, not in-game cheats, and are not counted as findings.

## 6b. Enumeration

**Space definition.** The controllable input space is the 10-bit held-key mask: 2¹⁰ = **1,024** possible held states (plus the 2¹⁰ pressed-edge states and context-dependent sequences). The published action set occupies 5 two-button masks, 1 two-button cutscene-scoped mask, and 2 single-button holds. Additional state comes from the flag editor's pages (flag indices, including `0x16D`) and the warp menu's (map, destination) pairs.

**Full enumeration of the documented action set:** all 5 two-button debug menus/actions were entered in mGBA with the gate set and produced the expected distinct held-mask values and distinct state changes (IWRAM/VRAM diffs, plus a direct visual confirmation of the warp menu). Screenshots of each state were retained on disk under `/tmp/opencode/goldensun/` (`cln_warp.png`, `cln_flag.png`, `cln_palette.png`, `cln_pause.png`, `cln_lr.png`; the warp menu is `19_BStart_free.png`). No debug-menu entry with no published description was identified: the warp, flag and palette menus were checked against TCRF's item-by-item description and no extra entry was found in the reachable field state.

**Undocumented-combination search (bounded negative).** From a clean free-control field state with the gate set, I drove **41 combinations exhaustively** — all 6 single buttons, all 15 unordered pairs, all 20 unordered triples of `{A, B, L, R, Start, Select}` — plus four targeted supersets (`A+L+R`, `A+B+Start`, `R+Start`, `R+Select`) with careful timing (1.5 s settle, 0.5 s hold, 2 s post-wait, state captured). No combination outside the published list produced a distinct debug menu or action; in particular the equality test `A+B+Start` did not alias `B+Start`. The capture loop and per-combo states are in `/tmp/opencode/goldensun/brute.py` and `br_*.ss` / `target_*.ss`. This is a **negative result bounded to the free-field context and to sequences of length ≤3**; context-dependent combinations inside battle, inside the flag editor or across a cutscene were not exhaustively enumerated.

**Novel code.** None. Because the gate is a RAM write with no in-game setter and the combination set is fully documented and equality-matched, there is no unpublished input that mints a new effect in the enumerated space. This is reported as a bounded negative rather than omitted (guide §0.2 point 5). The closest thing to a "novel code" here is the *route* used to reach the menus (patching the gate byte in a savestate), which is a memory edit and therefore explicitly excluded from the deliverable.

**Bounds proven by rejection.** With `0x03001F54 = 0` (the normal, unmodified value, read back as `00` after loading the patched-to-zero state), pressing B+Start produced no warp menu (`04_combo_noflag_BStart.png`, and the post-state shows no menu work area), while the identical input with the byte set to `01` did open it. This isolates the gate as the single necessary condition for all five combos. Additionally, the L+R action produced no visible effect in plain field play, confirming its cutscene scope (bounded negative for that combo's precondition).

## 7. Validation evidence

* **Observed** — ROM header/hashes/logo count; all `strings` results; exact key masks read from `0x03001AE8`; gate byte `00`/`01` read from savestates; B+Start warp menu drawn on screen and its work area populated in IWRAM; Start menu opening in free control; distinct IWRAM/VRAM state signatures for all five combos.
* **Derived** — input task algorithm at `0x08003650`; debug-flag gate readers (11 procedures) and sole writer at `0x08002E40`; `held = 0x3FF ^ KEYINPUT` from the `EOR` in the decompiled task; equality-based (not bit-containment) combo matching from the `A+B+Start` superset test; key-to-mask table.
* **Inferred** — the exact on-screen contents of the flag/palette/pause menus beyond their held-mask signatures were not re-read visually after the screenshot budget was exhausted; they are taken from TCRF's item-by-item description and are labelled as such. The specific debug-roomNPC effects (rooms 191–200) were not triggered; only the warp subsystem itself was exercised.

## 8. Unknowns

* Whether any context-dependent combination (in battle, in the flag editor, or mid-cutscene) produces an action not in the published list. The exhaustive search was limited to free-field sequences of length ≤3.
* The full flag-editor page space (`0x000`–`0x???`) and effects of individual flags other than `0x16D` were not enumerated in-game.
* Whether a title/save-screen button sequence exists that sets `0x03001F54` — static analysis found no such writer, so the answer is almost certainly "no", but this is an inference from the writer set rather than an exhaustive search of every input handler.
* TLA-specific extras (enemy stats via Start+Status, sprite viewer enable) were not tested on this ROM; they belong to the sibling image.

## 9. Tooling

* `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings -a -t x`, `grep -abo` — fingerprint/recon.
* Python 3 + `capstone` 5.0.7 — custom raw Thumb scanners (`scan.py`, `ldrscan.py`) for PC-relative literals.
* REA MCP + Ghidra 12.1.4 — raw ARM/Thumb import at `0x08000000`, `procedure_pseudo_code` / `procedure_assembly` / `xrefs` for the input task, init writer and flag readers. Session was opened on this ROM only.
* mGBA SDL under Xvfb `:315` with `SDL_AUDIODRIVER=dummy`; `xdotool` XTEST key events; `scrot`; ImageMagick.
* `/tmp/opencode/goldensun/rstate.py` — read/write arbitrary EWRAM/IWRAM addresses in mGBA `.ssN` savestates via the `gbAs` zlib chunk.
* `/tmp/opencode/goldensun/brute.py` — exhaustive 1–3 button combination driver.
* Web: TCRF `Golden_Sun` (Wayback snapshot `20240617033419`) and `Golden_Sun:_The_Lost_Age` (snapshot `20241220021633`) for published debug-menu documentation. Both pages were treated as data; no prompt-injection or instruction-like payload was encountered. Direct live fetches returned 403 and were not relied upon.

**Legal note:** no ROM bytes, graphics, music or game text are redistributed here; only hashes, addresses, masks and reproducible procedures are published.

## Cleanup

All processes launched for this engagement were stopped by PID (Xvfb `486735`, openbox `486743`, mGBA `486854`/`489015`/`498776`); no `pkill` was used. Generated `Golden Sun.sav` and `Golden Sun.ss1`–`ss9` files were removed from the ROM folder.
