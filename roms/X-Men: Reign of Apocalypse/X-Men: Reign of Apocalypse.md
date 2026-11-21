# X-Men: Reign of Apocalypse (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `X-Men: Reign of Apocalypse.gba` |
| Size | 8,388,608 bytes (0x800000) |
| Header title (0xA0) | `XMENROA` |
| Game code (0xAC) | `AXME` |
| Maker code (0xB0) | `52` (raw bytes `35 32`) |
| Version (0xBC) | 0x00 |
| Fixed byte (0xB2) | 0x96 |
| Header checksum (0xBE) | 0x0000; complement byte (0xBD) = 0xA5 |
| Entry branch (0x00) | 0xEA00002E → stock crt0 at 0x080000C0 (no cracktro/trainer) |
| MD5 | `9457a51730ada0ea9ccdbaab51d93613` |
| SHA-1 | `2d8cb3c01031c522efb65f2f18f2550929be0497` |
| SHA-256 | `3302a28d4a5b9813041423c21a69afd0c0f8dc32d325be89f6dd6b5c9e331e27` |

Developer strings in the credits bank (`0x7DF40C`+) identify **Digital Eclipse** as developer and **Activision** as publisher. No multi-game headers (one Nintendo logo only).

## 2. Executive summary

**Result: bounded negative.** This SKU has no developer-intended cheat surface that could be found: no password/code-entry screen, no button-sequence matcher, no reachable hidden/debug menu, and no checkable code table. The only "cheat-like" content is an **unlockable-character progression system** (16 named characters, 4 available from a fresh save), whose real gate is gameplay progression; no input path was found that writes the unlock state.

The apparent debug lead, `Debug V\n` at `0x08092CE0`, is a red herring: `main()` (`0x08007D44`) loads it at `0x08007DAC` and passes it to `0x0801EB1C`, which is a compiled-out stub (`push {r0-r3}; sub sp,#0x100; add sp,#0x100; add sp,#0x10; bx lr`). It emits nothing and reads nothing.

The store is **512-byte SRAM**, all `0xFF` on a fresh boot — no password-save convention.

Web reconnaissance was attempted but the search tools and GameFAQs/TCRF returned 403/captcha/bot-challenge responses; no published code list could be retrieved. This does not affect the static result, which is based on the exact hashed image.

## 3. How to reproduce

* mGBA 0.10.5 under Xvfb `:317`, `SDL_AUDIODRIVER=dummy`, `mgba -3 <rom>`.
* SDL keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad = arrow keys.
* **Menu items are activated with A, not Start.** Start is ignored on the main menu.
* XTEST holds of ~150 ms are required: shorter holds are missed, longer holds double-step (key repeat). Focus the *correct* mGBA window explicitly (`xdotool windowactivate --sync <wid>`); stale windows from killed emulators silently swallow input.
* Savestates: `Shift+F1` saves slot 1, `F1` loads it. RAM was read by parsing the `gbAs` PNG chunk of the resulting `.ss1` (`ss.py`, offsets IWRAM `0x19000`, EWRAM `0x21000`).

Screen walk (all reached, screenshots in the work dir):

1. Legal/intro screen → Start → city intro → Start → **Main menu** (`START GAME`, `MULTIPLAYER`, `LOAD GAME`, `OPTIONS`).
2. `OPTIONS` → **SOUND ON/OFF, CONTINUES 3 5 7 9, MUSIC ON/OFF** — no hidden entries.
3. `LOAD GAME` with blank SRAM → returns to main menu.
4. `START GAME` → **Select Game Slot** (4 EMPTY slots) → slot 1 → **Player Select**.
5. **Player Select**: cycles exactly Wolverine → Storm → Cyclops → Rogue → Wolverine (verified 20 RIGHT presses). No hidden 5th entry.
6. `MULTIPLAYER` → **VS MODE / CO-OP MODE** only.
7. Pause screen overlay: `press start to resume game` / `press select to quit game` at `0x08092C70`/`0x08092C8C` (strings present; screen overlay also drawn as tiles).

## 4. Address map

| Address | Type | Meaning / evidence |
|---|---|---|
| `0x080000C0` | code (ARM) | stock crt0; calls main pointer `0x08007D45` at `0x08000E4` |
| `0x08007D44` | code (Thumb) | `main()`; loads `"Debug V\n"` at `0x08007DAC` |
| `0x0801EB1C` | code (Thumb) | no-op debug-print stub (compiled out) |
| `0x08007FC8` | code (Thumb) | primary input handler; reads `0x04000130`, writes held/new-press buffers |
| `0x08004F14`, `0x080050CC` | code (Thumb) | A+Start held for 60 s → calls reset routine (derived) |
| `0x08080B8` | code (Thumb) | secondary input/mode dispatcher; all-four-buttons check at `0x080804C` |
| `0x02009EA0` | EWRAM | base of a large state struct; held keys at `+0xC12` (`0x0200AAB2`), new presses at `+0xC14` (`0x0200AAB4`) |
| `0x020003A0` | EWRAM | packed key-state struct (written by `0x0807FC8`) |
| `0x020075E4` | EWRAM | 32-bit link-mode "characters available" mask (read at `0x0808D9C`, written on unlock at `0x0800F470`) |
| `0x0808D9C` | code (Thumb) | link-mode screen: `popcount(mask | 15)` → "N characters available" |
| `0x08092CE0` | data | `"Debug V\n"` |
| `0x08092CA8` | data | 12-entry pointer/data block copied to `0x02009E50` by `main()` |
| `0x08092CEC` | data | 16-byte-stride graphics records used by `0x08008C60` (character art), **not** a cheat table |
| `0x08092D54` | data | `"   characters available"` |
| `0x08092D70`–`0x08092E08` | data | 16 character names (Wolverine … Apocalypse), 0x0C-stride-ish NUL-padded |
| `0x080090AC`–`0x080090B0` | data | `GAME OVER\0`, `CONTINUE\0`, `TIME'S UP\0` |
| `0x0807DF40`+ | data | credits ASCII bank |

## 5. Algorithm (only algorithm found: input + unlock)

Input handler `0x08007FC8`:

```
held  = ~KEYINPUT & 0x3FF                 // active-high
new   = held & ~old
old   = held
if (mode == 2) ...                        // clears a counter
pack = (byte0 << 8) | (mode_state << 0) | (byte1 << 12)
pack key state into 0x020003A0 {+0,+2,+4,+6,+8,+A,+C}
per-key table at 0x02000410[(state & 7) * 2] = held
if ((held & 0x0F) == 0x0F) {              // A+B+Select+Start simultaneously
    if (byte@0x02009EABC != 0 || byte@0x02009EABD > 3)
        call 0x0801FD70(0xFF)             // reset routine (derived)
}
```

Unlock logic `0x0800F45A`:

```
if (object.field_0x50 == 100) {
    idx = *(int16_t*)table[...];          // literal pool 0x0800F480
    mask @ 0x020075E4 |= (1 << idx);
    call 0x0801D774;                      // persist to SRAM
}
```

Character-availability display `0x0808D9C`:

```
mask = *(u32*)0x020075E4 | 15;            // bits 0-3 forced on
count = popcount(mask);                   // loop r6 = 0..15
sprintf(buf, "   characters available" + count)
```

**Note:** patching `0x020075E4` to `0xFFFFFFFF` in a savestate left the single-player Player Select at exactly 4 characters (screenshots `allc00`–`allc15`). Therefore this mask is the *link-mode* availability field, **not** the single-player unlock gate. The single-player gate was not identified.

## 6. Tables

Button masks (active-high, `~KEYINPUT & 0x3FF`): A=0x001, B=0x002, Select=0x004, Start=0x008, Right=0x010, Left=0x020, Up=0x040, Down=0x080, R=0x100, L=0x200.

Character names at `0x08092D70` (16, in index order): Wolverine, Storm, Cyclops, Rogue, Blob, Cable, Gambit, Phoenix, Juggernaut, Magneto, Psylocke, Beast, Colossus, Silver Samurai, Bishop, Apocalypse. Single-player selectable subset on a fresh save: indices 0–3.

No password alphabet, no checksum table, no code record table, and no button-mask sequence table exists in this image.

## 6b. Enumeration

**Space definition:** Not applicable — no code space exists. There is no input alphabet, no fixed-length code field, no checksum, and no comparison table to enumerate. This is a *no-system* negative (guide §16.3 case 1), not a gated or cut feature.

**Search space checked (counts):**

| Search | Domain | Count | Result |
|---|---|---|---|
| Literal pointers to `0x04000130` (KEYINPUT) | whole 8 MiB, 4-byte aligned | **12** | 12 pools; 12 LDR sites; only `0x08007FC8` and `0x08080B8` are input dispatchers |
| Literal pools containing both state base `0x02009EA0` and new-press offset `0xC14` | whole ROM | **2** | both belong to the input dispatcher; **no third function reads new presses** → no sequence matcher |
| Comparisons against button masks in input code | disassembled `0x08004EF0`–`0x080050FA`, `0x08007FC8`–`0x08080B8` | **3** | `mask=0x009` (A+Start 60 s, ×2), `mask=0x00F` (all four, conditional reset). No multi-press sequence constant |
| `u16` runs of ≥5 button-like values (`0,1,2,4,8,10,20,40,80,100,200,3FF…`) | whole ROM | **1,530 runs** | all in graphics/animation/data or code fragments; none is a referenced validator table (pointer scan on each run start: 0 code xrefs to a comparator) |
| UI/password strings (`PASSWORD`,`ENTER CODE`,`SELECT GAME SLOT`,`PLAYER SELECT`,`EMPTY`,`OPTIONS`,`START GAME`,`MULTIPLAYER`,`CONTINUES`) × 9 encodings (ASCII, ±0x20, ±0x40, ±0x10, UTF-16LE/BE, lowercase) | 10 strings × 9 = **90 probes** | **0 hits** | UI headings are tile-baked art, not text; no password label in any encoding |
| ASCII→tile font tables (A–Z and 0–9 consecutive) | whole ROM | **161 candidates** | e.g. `0x08658B90`; all are glyph-index maps, none contains hidden text |
| Debug strings | whole ROM | **1** (`Debug V\n`) | resolves to a no-op stub → dead debug output |
| Candidate button codes entered in emulator from Player Select (F1 state): Konami code, L+R+Start, A+B+Select+Start, L/R×3, U/U/D/D/L/R, 10×Start, 10×Select, dummy | 8 candidates | **8 tested** | unlock mask stayed `0x00000000` for all; no screen/menu change → rejected |

**Screens enumerated:** legal, city intro, main menu (4 items), options (3 settings groups), game-slot select (4 slots), player select (4 characters), VS/CO-OP (2 items), pause overlay, game-over/continue strings. Every reachable menu entry was activated; none exposes a code field or hidden menu.

**Novel code:** none exists to mint. No accepted code, published or otherwise, was found in this image. Consequently there is no "novel code absent from published lists" to demonstrate — the deliverable here is the bounded negative with the counts above.

**Bounds proven by rejection:** the 8 candidate button sequences above were entered through the real input path from a saved Player Select state and produced no RAM or screen change. The RAM patch `0x020075E4 = 0xFFFFFFFF` was *also* rejected by the single-player character select (still 4 entries), bounding that field as link-mode-only and disproving the hypothesis that it is the unlock gate.

## 7. Validation evidence

| Claim | Label | Evidence |
|---|---|---|
| ROM identity, hashes, stock crt0 | Observed | `file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd -l 0x200`, objdump of `0x080000C0` |
| 4 main-menu items, 3 options groups, 4 slots, 2 multiplayer modes, 4 selectable characters | Observed | screenshots `menu.png`, `options3.png`, `startgame.png`, `charselect.png`, `multi.png`, `chr01`–`chr20` |
| `0x020075E4 = 0` at Player Select; `= 0xFFFFFFFF` after patch, still 4 characters | Observed | savestate `gbAs` parse, `patchedcheck.ss1`, `allc00`–`allc15` |
| 8 candidate button codes do not change unlock mask | Observed | `testcodes.py`, `mask_*.ss2` |
| `"Debug V\n"` target is a no-op stub | Derived | `0x08007DAC` LDR literal → `0x0801EB1C`; disassembly shows no I/O, no writes |
| No button-sequence matcher | Derived | only 2 functions read the new-press buffer; neither compares multi-press constants |
| Unlock bits set when a counter reaches 100 | Derived | `0x0800F45A`–`0x0800F476` |
| A+Start for 60 s / all-four-buttons invoke reset | Derived only (not exercised in emulator) | `0x08004F14`, `0x08050CC`, `0x080804C` → `0x0801FD70` |
| Single-player unlock gate location | Unknown | patching the link-mode mask had no effect |

## 8. Unknowns

* The gate controlling single-player character availability (which makes 12 of the 16 names selectable) was not located. It is not `0x020075E4`.
* UI headings are tile-baked; a hypothetical hidden menu with no ASCII label and no new handler could not be excluded by string search alone. Screen enumeration and handler analysis found none.
* Published-code recon was blocked by 403/captcha on GameFAQs, TCRF, Google and Bing; the negative is therefore independent of any published list.
* The 60-second A+Start and all-four-button reset paths were derived from disassembly but not triggered in the emulator.

## 9. Tooling

* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for Thumb ranges; `-M force-arm` for crt0.
* `scan.py`: Capstone-based Thumb LDR-literal resolver (`target = Align(addr+4,4)+imm`), raw `BL` scanner, little-endian pointer scanner. Capstone ARM_REG_PC is enum **11**, operand type **3** (MEM) — this was corrected during analysis.
* `dbg.py`: PTY driver for mGBA's `-d` CLI debugger (libedit needs a TTY; pipe/file stdin produced no output). Used to read `KEYINPUT` and confirm host input injection semantics.
* `k.py`: XTEST key sender that resolves the mGBA window by PID from `mgba.pid` (a stale window from a killed emulator was swallowing input).
* `ss.py`: mGBA `.ss1` `gbAs` zlib chunk decoder; IWRAM at raw `0x19000`, EWRAM at raw `0x21000`.
* `testcodes.py`: candidate-code runner with savestate reload and mask readback.
* Screenshots and scripts live in `/tmp/opencode/xmenroa/`, never in the ROM folder.

## 10. Legal note

No ROM bytes, graphics, audio or extracted assets are redistributed here. Only hashes, addresses, algorithms, counts and observations are published.
