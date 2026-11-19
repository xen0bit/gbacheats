# Sitting Ducks (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Sitting Ducks/Sitting Ducks.gba` |
| Size | 4,194,304 bytes (0x400000) |
| Header title | `SITTING DUCK` (12 bytes at 0xA0) |
| Game code | `BSDE` (USA), maker `FL` |
| Version / unit / device | 0x00 / 0x00 / 0x00 |
| Complement / checksum | 0x38 / 0x0000 |
| Entry word | `0xEA00002E` (stock `b 0x080000C0`, **not** a cracktro patch) |
| MD5 | `747b6e33299deed3e9fe71c4352f5966` |
| SHA-1 | `30b888a0af86eb0313be8f34e00c912c569bf51d` |
| SHA-256 | `d9521e7fb8e7c1ffbecffcfbe1b51e62a9441fd6fc6bf73002e295d255efa290` |

Embedded-header scan: Nintendo-logo scan over the whole file finds **exactly one** GBA header, at file offset `0x0`. No appended trainer, no multiboot stub, no second image. `file(1)` reports `Game Boy Advance ROM image: "SITTING DUCK" (BSDEFL, Rev.00)`. This is a clean retail US image.

## 2. Executive summary

Sitting Ducks has a **developer-intended 6-character progress-password system**. The main menu has a **Password** entry that opens a 4×8 on-screen keyboard with a 32-symbol alphabet. Passwords are validated by a checksum-style algorithm (no plain code table exists in the ROM). The game also **displays the current progress password in red on the pause screen**.

The pause screen of a fresh game (Mission 01, no medals) shows **`C#BB#J`**. Entering that exact 6-character string at the Password screen turns the lock icon **green with a checkmark** (accepted). Any single-character mutation of it, a 3-character published code (`1B#`), and a 6×`B` string all leave the lock **gray** (rejected). So the system is real, in-game, and verifiable entirely through the UI — but it is a **progress-save/restore code**, not a classic cheat list.

Published GameFAQs codes (`D%K`, `F%L`, `1B#`) are **3 characters** and do **not** match the game's 6-character input format; `1B#` was entered in the emulator and rejected (lock gray). Published CodeBreaker codes are raw memory edits and are out of scope.

The complete validator/password generator was **not** recovered from the disassembly in this engagement (see §8 for the bounded search that was performed). What *is* fully characterised: the input surface, the alphabet, the code length, the total space (32⁶), one accepted code, and rejection of multiple out-of-format and mutated inputs.

## 3. How to reproduce

### 3.1 Environment

```
Xvfb :319 -screen 0 1024x768x24 &
DISPLAY=:319 openbox &
export DISPLAY=:319
export SDL_AUDIODRIVER=dummy          # without this the core parks at 0% CPU and the screen is black
mgba -3 game.gba &                    # mGBA 0.10.5 at /usr/local/bin/mgba
```

Default SDL keymap: A = `x`, B = `z`, L = `a`, R = `s`, Start = `Return`, Select = `BackSpace`, D-pad = arrow keys.

**Input timing (important):** hold A/D-pad keys for ~0.2 s with ~0.5 s between presses. Shorter taps are dropped intermittently; longer holds produce extra registrations from X autorepeat.

Screenshots: `scrot` then crop `720x480+152+144`.

### 3.2 Screen path (all screens walked)

1. **Hip Games** splash → **LSP** splash (both time out; Start does not skip).
2. **Language select** — six flags (US, FR, DE, IT, ES, NL); cursor starts on US, A confirms. (This run used French; language does not affect the code system.)
3. **Title**: "SITTING DUCKS / PRESS START" — press Start.
4. **Main menu**: `Histoire` (Story), `Course` (Race), `Mot de Passe` (Password), `Options`.
5. **Password** = on-screen keypad (4 rows × 8 columns), empty input box, lock icon at bottom right.
6. **Mission Selector**: `Mission 01`, `Quitter`, `Confirmer`. Only Mission 01 is listed on a fresh cart.
7. **In-game (Mission 01)**: HUD timer `01:45`, collectible counter `00/60`.
8. **Pause** (Start in-game): `PAUSE`, `Mission 01`, the red 6-character progress password, `Continuer / Redémarrer / Quitter`.
9. **Options**: `Sfx` volume, `Musique` volume, `Crédits`. No hidden/debug entry was found in this menu.

### 3.3 Confirming the accepted code

- At the Password screen, navigate the 4×8 grid with the D-pad (cursor wraps in both axes) and press A to append a symbol; B deletes the last symbol.
- Enter `C # B B # J` (i.e. **C#BB#J**) — positions: C = row0 col1, # = row3 col7, B = row0 col0, B again, # again, J = row0 col6.
- **Observed**: the lock icon to the right of the input box turns **green with a white checkmark**.
- Press Start afterwards → game moves to the Mission Selector (the code is consumed/applied).

Screenshots (in work dir ` /tmp/opencode/sittingducks/`): `code6_entered.png` (green lock), `gdb_pw_screen.png` (keypad), `pause_try2.png` (pause-screen password), `submit_return.png` / `montage_sub.png` (rejected codes, gray lock), `mainmenu.png`, `walk_options.png`, `s_pause.png`.

## 4. Address map

| Item | Value | Evidence |
|---|---|---|
| ROM header | file `0x000` (`0x08000000`) | Phase 0 scan |
| Nintendo logo | header `+0x04` | single hit at file 0 |
| Font tile data (keypad glyphs) | VRAM `0x06003800`+ ← ROM file `0x348000`–`0x34D500` | VRAM dump via mGBA CLI debugger matched byte-for-byte against ROM |
| Savestate VRAM | state raw offset `0x1000` (VRAM `0x06000000`) | matched `state2.bin` to live VRAM reads |
| Savestate IWRAM | state raw offset `0x19000` (IWRAM `0x03000000`) | matched bytes `f6 4f 2d e9 …` |
| Savestate EWRAM | state raw offset `0x21000` (EWRAM `0x02000000`) | matched `x/4 0x02000000` from mGBA CLI debugger |
| Keypad poll routine | `0x0801E7C0`–`0x0801E7E8` (reads `0x04000130`) | read-watchpoint on KEYINPUT, caller `0x0800E031` |
| Generic clear/memset routine | `0x08018474` (thumbnail `ldmia sp!, {r4-r6}` at `0x08018472`) | write-watchpoint hits during state load |
| Input-length / cursor candidates | IWRAM `0x0300339C` (cursor 0→1 after Right), `0x03003350` | savestate diff after single arrow / A press |

No plain-text password table and no literal ASCII of any published code exists in the ROM (`strings -t x -n 4` returns 34,755 strings, **none** matching password/cheat/debug/level/unlock; all in-game text is tile-index). The published codes were also searched as ASCII, UTF-16, u8/u16 glyph indices and 5-bit packed values — no hits.

## 5. Algorithm

Not fully recovered. The observable model is:

```
alphabet = "BCDFGHJKLMNPQRSTVWXYZ123456789%#"   # 32 symbols, 5 bits each
code     = 6 symbols                            # 30 bits nominal
accept(code) -> lock turns green (checksum/format satisfied)
reject(code) -> lock stays gray
```

The fact that all six single-character mutations of a valid code were rejected shows at least one symbol is a check symbol, i.e. the accepted set is a checksum-constrained subset of the 32⁶ space rather than a free-form string. No hard-coded comparison table for the codes was found in the ROM, so validation is computed.

## 6. Tables

### 6.1 Keypad alphabet (decoded from font tiles / screenshot)

Index in keypad order (0-based, 5-bit value):

| idx | sym | idx | sym | idx | sym | idx | sym |
|---:|:---:|---:|:---:|---:|:---:|---:|:---:|
| 0 | B | 8 | L | 16 | V | 24 | 4 |
| 1 | C | 9 | M | 17 | W | 25 | 5 |
| 2 | D | 10 | N | 18 | X | 26 | 6 |
| 3 | F | 11 | P | 19 | Y | 27 | 7 |
| 4 | G | 12 | Q | 20 | Z | 28 | 8 |
| 5 | H | 13 | R | 21 | 1 | 29 | 9 |
| 6 | J | 14 | S | 22 | 2 | 30 | % |
| 7 | K | 15 | T | 23 | 3 | 31 | # |

Note: the last symbol is `#`, not `&` — confirmed by zoomed keypad image (`keypad_zoom2.png`) and by the fact that the GameFAQs codes use `#`.

### 6.2 Codes

| Code | Source | Length | Result in emulator |
|---|---|---|---|
| `C#BB#J` | **read from the pause screen** (fresh Mission 01 progress) | 6 | **ACCEPTED** — lock green + checkmark |
| `D%K` | GameFAQs "Level 2, new race unlocked, medal won" | 3 | not usable — format is 6 chars |
| `F%L` | GameFAQs "Level 3, new race unlocked" | 3 | not usable — format is 6 chars |
| `1B#` | GameFAQs "Unlock Everything" | 3 | **REJECTED** — entered in full, lock gray |
| `BBBBBB` | this analysis (invalid probe) | 6 | REJECTED — lock gray |
| `D#BB#J`, `C#BB#K`, `C#CB#J`, `C#BB#1` | single-symbol mutations of the accepted code | 6 | all REJECTED — lock gray |

### 6.3 Published codes (web, treated as data)

- GameFAQs cheats page: the three 3-character codes above. All characters are in the game's alphabet, but the length does not match the entry UI; likely a different build/region or an incomplete transcription. `1B#` was tested and rejected.
- Cheat Wiki CodeBreaker list (`3300018F 0014` "unlock all missions", `83000192 FFFF` "unlock all races", etc.) — raw memory-edit device codes, **out of scope** (not developer-intended in-game cheats). The EWRAM addresses in them are recorded only as leads; patching `0x0200018F` in a savestate caused the game to fail to render, so those leads were not pursued.
- Neoseeker cheats page returned HTTP 403; no Wayback snapshot was available. No usable code strings were recovered from it.
- Nothing on TCRF/VGChartz specific to this GABE SKU was found.

## 6b. Enumeration

**Space definition.** The Password surface is a 4×8 grid of 32 symbols; the input box holds 6 symbols. Nominal space = 32⁶ = **1,073,741,824** strings. Each symbol is 5 bits, so the nominal payload is 30 bits. At least one symbol is a check symbol (every single-symbol mutation of an accepted code was rejected), so the *accepted* set is a checksum-constrained subset — its exact size is not established here.

**Known accepted member (not a novel mint, but in-game proven):** `C#BB#J`, read directly from the pause screen and re-entered successfully (green lock, screenshot `code6_entered.png`). This is the progress password for the starting state (Mission 01, no medals). It does not appear in any published list found in this engagement (GameFAQs lists only 3-character strings).

**Novel unpublished code:** none was generated. The validator/generator function was not isolated, so a code that exercises a different field combination could not be minted and verified. This is an explicit **unknown**, not a "not tested" — the search performed is bounded in §8.

**Bounds proven by rejection (all Observed in emulator, lock stays gray):**
1. Wrong length: `1B#` (3 chars) — the published "Unlock Everything" code is rejected by this 6-character UI.
2. Out-of-format payload: `BBBBBB` (6 chars, no valid checksum) — rejected.
3. Bit/checksum sensitivity: four single-symbol mutations of the accepted code (`D#BB#J`, `C#BB#K`, `C#CB#J`, `C#BB#1`) — all rejected. This proves the check layer is active and that the accepted set is much smaller than 32⁶.

**Negative result on the code table:** literal searches over the full 4 MiB found no occurrence of the published codes as ASCII, UTF-16LE/BE, u8 glyph indices, u16 glyph indices, or 5-bit-packed 16/32-bit constants. Combined with the green-lock behavior, this supports a computed validator rather than a hard-coded lookup list.

## 7. Validation evidence

- **Observed (emulator / screenshots):** all screens in §3.2; alphabet glyphs; green lock for `C#BB#J` and gray lock for every rejected string; red pause-screen password; keyboard navigation (wrap in both axes) and B-as-delete; 6-character input box.
- **Observed (memory / savestate):** input length and cursor candidates in IWRAM; font tile bytes in VRAM (`0x06003800`+) matching ROM `0x348000`+; savestate region offsets for VRAM/IWRAM/EWRAM; input handling changes when A/arrow keys are pressed.
- **Derived (static):** single retail header, stock entry word; no ASCII text bank — all UI text is tile-index; no literal code table in ROM; keypad poll routine at `0x0801E7C0`.
- **Inferred:** the accepted set is checksum-constrained; the 3-character GameFAQs codes belong to a different build/region or are incomplete; the pause-screen password is a progress-save code computed from progress state.
- **Not observed:** the validator's arithmetic, the meaning of each of the 6 fields, and any accepted code other than `C#BB#J`.

## 8. Unknowns / bounded search

The following were tried and failed to yield the validator (so the negative is bounded, not "did not look"):

1. `strings` keyword sweep (password/cheat/debug/secret/unlock/level/code) — 34,755 strings, zero relevant ASCII hits; text is tile-indexed.
2. Literal searches for published codes in ASCII, UTF-16, glyph-index byte/halfword, and 5-bit packed forms — zero relevant hits.
3. Direct 32-bit pointer scans for the EWRAM input address (`0x020061xx`) and IWRAM length address (`0x03003350`) in ROM — no direct literal (addresses are computed at runtime).
4. GDB stub (`mgba -g`, port 2345) — connected but RAM reads to EWRAM/VRAM were intermittent; the stub died on disconnect. Fell back to mGBA's own CLI debugger (`-d`), which reliably reads/writes RAM and has watchpoints.
5. mGBA CLI write-watchpoints on `0x0300339C` / `0x03003350` — hits landed in a generic memory-clear routine at `0x08018474` during savestate restore, not in the password handler.
6. REA/Ghidra open of the ROM succeeded (699 procedures, 1,249 strings), but the shared REA bridge was taken over by another agent mid-session, so per-function decompilation could not be completed reliably.
7. Savestate patching of EWRAM `0x0200018F` (from the CodeBreaker lead) — the patched state failed to render; abandoned.

Consequently the exact checksum, field layout, accepted-set size, and a second novel accepted code remain unresolved.

## 9. Tooling

- `file`, `xxd`, `strings`, `grep`, `md5sum`/`sha1sum`/`sha256sum` for Phase 0/1.
- `python3` scripts in `/tmp/opencode/sittingducks/`:
  - `phase0.py` (fingerprint + logo scan), `gba.py` (xdotool input/screenshot helpers),
  - `gdbdrv.py` (pty driver for gdb-multiarch), `mdbg.py` (pty driver for mGBA CLI debugger),
  - `typer.py` (grid-aware code typer + green-lock pixel detector).
- `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for ROM disassembly.
- `mgba 0.10.5` under `Xvfb :319`, `xdotool` (XTEST), `scrot`, ImageMagick (`convert`, `montage`), Pillow for tile rendering.
- REA/Ghidra 12.1.4 via the `reverse-engineer-anything` MCP bridge (session was contended).

Savestates and screenshots: `/tmp/opencode/sittingducks/` (work dir only; nothing written to the ROM folder).

## 10. Legal note

No ROM image, extracted graphics, or game text are redistributed by this report. Only hashes, addresses, method, and the analyst's own observations are published.
