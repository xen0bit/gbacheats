# SpongeBob SquarePants: SuperSponge (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `SpongeBob SquarePants: SuperSponge.gba` |
| Size | 4,194,304 bytes (4 MiB) |
| Header title | `SBSP SS` |
| Game code | `ASPE` (region **E** / Europe) |
| Maker code | `0x78` (THQ) |
| Version / complement / checksum | `0x00` / `0xBB` / `0x0000` |
| Entry word | `0xEA00002E` → stock crt0 at `0x080000C0` (not a cracktro/patched image) |
| MD5 | `c2bfa5c822f33eaed02ad2f94a0414b4` |
| SHA-1 | `b67caab6316a8478129f43672572277f411f211d` |
| SHA-256 | `e4e37b9b4213ffd3f309dcf418d0dbe191f2aac4674d90de7b2214df802b8cf0` |

`file(1)` classifies it as `ASPE78, Rev.00`. All addresses below were verified against **this exact image** (a byte-identical copy was used for emulation so no `.sav`/`.ss*` files touched the ROM folder).

## 2. Executive summary

The only developer-intended cheat surface is a **4-letter password** system on the main menu (`Enter A Password`). It is a **closed lookup table of exactly 20 hard-coded strings** — there is no checksum, no arithmetic generator and no hidden extra code. The on-screen alphabet is the 21 consonants `BCDFGHJKLMNPQRSTVWXYZ` (`A` and the vowels are not selectable), so the input space is `21^4 = 194,481`; exactly 20 inputs are accepted and 194,461 are rejected.

The validator at `0x08014A60` compares four raw ASCII bytes against a 20-entry pointer table at `0x080272AC4`, returning table index `0..19` (which drives level unlocking) or `-1` (`Invalid Password`). Because the accepted set is exactly the table, **no novel/unpublished code can exist** — this is a bounded negative, proven by disassembly, offline enumeration of the whole space, and in-game accept/reject tests (§6b).

Findings that correct the published record:

* The ROM's level-19 password is **`JRST`**, not `JAST`. `JAST` appears in GameFAQs, Neoseeker, CheatCC and others; it is **rejected** by the game (`A` is not even in the alphabet). `JRST` is accepted.
* The widely copied "Level Passwords PS" list (`KVNF`, `WKGA`, `DFVJ`, `WMCV`, `XNAD`, `HPJQ`, `QGAV`, `PVHS`, ...) is **not present in this GBA image** in any encoding; it belongs to the PlayStation SKU. Only the `BGNR … WMBT` set is in the ROM.
* `WMBT` (index 19) accepts and unlocks/selects all 20 levels — the published "level select" claim is confirmed.

No button-code table, no hidden/debug menu and no second validator entry point were found. Unused text-bank strings `Level Select`, `Music Test`, `SFX Test` have no code pointers and never appeared on any walked screen.

## 3. How to reproduce

### Emulator
`Xvfb :319 -screen 0 1280x960x24`, `openbox`, `SDL_AUDIODRIVER=dummy mgba -3 ./game.gba`.
mGBA SDL keymap used: **A = `x`, B = `z`, Start = `Return`, D-pad = arrows**. Hold keys 150–250 ms; `xdotool windowactivate --sync` then `windowfocus` before sending keys.

### Menu path
Boot → title (`Press START`) → `Return` → Main Menu:
`Start New Game` / `Enter A Password` / `Options Menu` / `Credits` (exactly 4 entries; see §4).
`Enter A Password` → `A` → 4-slot entry screen → set each letter with Up/Down → `A` commits and advances → after the 4th letter the game validates.

### Deterministic input for tests
Typing on-screen is subject to key-repeat, so acceptance tests used savestate patching. The live input buffer is at IWRAM `0x03006ED9` (4 ASCII bytes), cursor at `0x03006EDE`, current-letter index at `0x03006EDF`. A patched state (`patch_ss.py`) sets the four bytes, sets cursor `= 3` and letter index `= alphabet_index(code[3])`; one `A` press then submits the exact code. This is still an in-game submission through the normal UI handler.

### Codes tested in-game

| Code | Result | Evidence (screenshots in `/tmp/spongesuper/`) |
|---|---|---|
| `BGNR` | **Accepted** → chapter/level 1 intro, password echoed as `Password BGNR` in pause menu | `bg_valid.png`, `pause2.png` |
| `JRST` | **Accepted** → level select with Oil Rig selected (level 19) | `jrstc.png` |
| `WMBT` | **Accepted** → all 20 level thumbnails available | `wmbtc.png` |
| `BGNH` (one-letter near miss) | **Rejected** → `Invalid Password` | `rej_bg_0.3.png` |
| `JAST` (published typo, contains non-alphabet `A`) | **Rejected** → `Invalid Password` | `rej_jastx_0.3.png` |
| `BBBB` (well-formed but not in table) | **Rejected** → `Invalid Password` | `after_invalid_a.png` |

## 4. Address map

All ROM addresses are `0x08000000 + file offset`.

| Item | File offset | ROM / RAM address | Notes |
|---|---:|---|---|
| Password strings (20 × 8 bytes: 4 ASCII + 4 zero) | `0x1F264`–`0x1F303` | `0x0801F264`–`0x0801F303` | `WMBT` first (index 19), `BGNR` last (index 0) |
| Password pointer table (20 × u32) | `0x272AC4` | `0x080272AC4` | index 0 → `0x0801F2FC` (`BGNR`), index 19 → `0x0801F264` (`WMBT`) |
| Input alphabet (21 bytes + NUL) | `0x2769C8` | `0x082769C8` | `BCDFGHJKLMNPQRSTVWXYZ` |
| **Validator** | `0x14A60` | `0x08014A60` | 4-byte exact compare loop `0x08014A6A`–`0x08014A9E` |
| Validator caller (password screen submit) | `0x11970` | `0x08011970` | `bl 0x08014A60`; `-1` → invalid state, else unlock + start |
| Letter-input handler | `0x11948` | `0x08011948` | Up/Down wrap at index 21, `A` commits/advances |
| Highest-unlocked-level helper | `0x14A28` | `0x08014A28` | tests 20-bit mask at `0x03003CB0` |
| Unlock bit setter | `0x14938` | `0x08014938` | sets bits in 20-bit mask at `0x0300F30` |
| Post-accept wrapper | `0x14AF0` | `0x08014AF0` | calls validator, stores index to `0x0300F30`, unlocks |
| 4-char input buffer | — | `0x03006ED9` (IWRAM) | raw ASCII, `.` when unfilled |
| Cursor / letter index | — | `0x03006EDE` / `0x03006EDF` | 0-based; letter wraps 0..20 |
| Text bank | `0x2783A8`+ | `0x082783A8`+ | plain ASCII UI strings |
| Main-menu item pointers | `0x11704`–`0x11714` | `0x08011704`–`0x08011714` | 4 items: `Main Menu`, `Start New Game`, `Enter A Password`, `Options Menu`, `Credits` |

Savestate layout used for RAM reads (mGBA `gbAs` zlib chunk, 397,312 bytes): `0x19000` = IWRAM base `0x03000000`, `0x21000` = EWRAM base `0x02000000`.

## 5. Algorithm

Reimplementation of `0x08014A60` (derived from Thumb disassembly):

```python
ALPHA = "BCDFGHJKLMNPQRSTVWXYZ"     # 21 symbols, indices 0..20
TABLE = [read_cstr(p) for p in u32_table(0x080272AC4, 20)]  # index 0..19

def validate(inp4):                 # inp4 = 4 raw ASCII bytes
    for i, s in enumerate(TABLE):
        if inp4[0] != s[0]:
            continue
        matched = 1
        while matched <= 3 and inp4[matched] == s[matched]:
            matched += 1
        if matched == 4:
            return i               # sign-extended 16-bit in ROM
    return -1
```

Caller behaviour (`0x08011970`):

```
idx = validate(buffer)
if idx == -1:
    screen_state[1] = 2      # show "Invalid Password"
else:
    unlock_levels(idx)       # 0x08014938: set bits in 20-bit mask at 0x0300F30
    screen_state[0] = 6      # leave password screen
    show "Select Level" with levels unlocked up to idx
```

Input letters are converted through the alphabet table before being written to the buffer (`0x08011960`–`0x08011964`), and the index wraps at 21 (`0x0801193E`). Only the 21 consonants can be entered with the pad.

No checksum, XOR, permutation, PRNG or second format exists: the only two `bl` call sites of the validator are `0x08011970` (password screen) and `0x08014AF2` (its own post-accept wrapper), both on the same screen.

## 6. Tables

### 6.1 Complete accepted password table (ROM truth)

| Index | Password | Level (published label) | String address |
|---:|---|---|---|
| 0 | `BGNR` | 1 — Jelly Fields | `0x0801F2FC` |
| 1 | `CLMB` | 2 — Sandy's Tree Dome | `0x0801F2F4` |
| 2 | `KYNF` | 3 — Fish Hooks Park | `0x0801F2EC` |
| 3 | `WKGR` | 4 — Downtown Bikini Bottom | `0x0801F2E4` |
| 4 | `PFYJ` | 5 — Cavernous Canyons | `0x0801F2DC` |
| 5 | `NGPS` | 6 — Thermal Tunnels | `0x0801F2D4` |
| 6 | `WMCY` | 7 — Acrid Air Pockets | `0x0801F2CC` |
| 7 | `XNRP` | 8 — Lava Fields | `0x0801F2C4` |
| 8 | `HDJQ` | 9 — Precipice Canyon | `0x0801F2BC` |
| 9 | `QHDG` | 10 — Desert Wasteland | `0x0801F2B4` |
| 10 | `WFXM` | 11 — Kelpazoic Jungle | `0x0801F2AC` |
| 11 | `MNTL` | 12 — Inside the Whale | `0x0801F2A4` |
| 12 | `QGRV` | 13 — Road to the Bottom of Rock Bottom | `0x0801F29C` |
| 13 | `LXHK` | 14 — Lonely Souls | `0x0801F294` |
| 14 | `HGCD` | 15 — Graveyard | `0x0801F28C` |
| 15 | `CNXK` | 16 — Last Stop | `0x0801F284` |
| 16 | `LKKV` | 17 — Jelly Fields | `0x0801F27C` |
| 17 | `PYHS` | 18 — Man Ray's Lair | `0x0801F274` |
| 18 | **`JRST`** | 19 — Oil Rig | `0x0801F26C` |
| 19 | `WMBT` | 20 — Canning Factory / unlock all | `0x0801F264` |

### 6.2 Alphabet and field layout

* Symbols: `B C D F G H J K L M N P Q R S T V W X Y Z` (21; indices 0–20).
* Length: 4 symbols, raw ASCII bytes, no terminator in the buffer.
* No checksum field, no reserved bits, no aliases (the 20 strings are distinct and pairwise non-prefix).

## 6b. Enumeration

**Space definition.** Alphabet 21 symbols × 4 positions = `21^4 = 194,481` representable strings. The validator is an exact 20-string membership test, so the accepted set is **exactly 20** and the rejected set is **194,461**.

**Validator model.** Reproduced in `enumerate.py`; the ROM pointer table was dereferenced directly and the model's accept set equals the table (`table == accepted set: True`). Every published "Set A" code is present; the alternate "PS" list is absent from the image.

**Novel codes.** None exist and none can be minted. The validator at `0x08014A60` enumerates indices `0..19` and returns `-1` otherwise; there is no generator, checksum or arithmetic path that could produce an out-of-table accepted value. This is a *bounded negative* rather than an incomplete search:
1. Static: the loop bound is `cmp r4,#19; ble` (`0x08014A98`–`0x08014A9A`) and the only success exit requires `r2 == 4` after a full 4-byte match against one of those 20 strings; the failure exit is `movs r0,#1; negs r0` → `-1` (`0x08014A9C`).
2. Dynamic: two in-table codes (`BGNR`, `JRST`, `WMBT`) were submitted through the real UI and accepted; three out-of-table values (`BGNH`, `BBBB`, `JAST`) produced `Invalid Password`.
3. Exhaustive offline: all 194,481 alphabet strings were evaluated against the recovered validator; exactly the 20 table entries pass.

**Bounds proven by rejection.**
* One-character substitution of a valid code (`BGNR` → `BGNH`) → `Invalid Password` (`rej_bg_0.3.png`).
* Well-formed but unlisted `BBBB` → `Invalid Password`.
* Published-but-wrong `JAST` (letter `A` is outside the 21-symbol alphabet, cannot even be entered with the pad; patched raw) → `Invalid Password` (`rej_jastx_0.3.png`). Correct ROM value `JRST` → accepted.
* Published "PS" variants (`KVNF`, `WKGA`, `DFVJ`, `WMCV`, `XNAD`, `HPJQ`, `QGAV`, `PVHS`) were searched literally in the ROM and are all absent — the GBA image uses `KYNF`, `WKGR`, `PFYJ`, `WMCY`, `XNRP`, `HDJQ`, `QGRV`, `PYHS`.

**Unlockable.** `WMBT` sets the full 20-bit unlocked-level mask (observed: all 20 thumbnails on the Select Level screen, `wmbtc.png`); lower-index codes unlock a prefix (e.g. `JRST` shows Oil Rig with later slots still `?`).

## 7. Validation evidence

* **Observed (emulator):** THQ/Nickelodeon boot → title → 4-item Main Menu; password screen `B...` with 21-letter cycling; `BGNR`, `JRST`, `WMBT` accepted and shown in level intro/pause (`Password BGNR`); `BGNH`, `BBBB`, `JAST` → `Invalid Password`; Options Menu (2 items), Controller Options, Sound Options, Credits, level-select screen, gameplay and pause menu (`Continue / Quit Level / Quit Game`) all walked.
* **Observed (RAM):** savestate diff of one Down press located the input buffer region; watchpoint on `0x03003CD4` caught the input timer handler; watchpoint on ROM `0x0801F264` caught the validator with `r3 = 0x0801F264`, `r4 = 19`, return address `0x08011975`; buffer contents `B...` / `C...` matched the displayed text.
* **Derived (disassembly):** validator loop, 20-entry table, 21-symbol alphabet at `0x082769C8`, caller's accept/reject branches, unlock bit setter.
* **Derived (enumeration):** all 194,481 inputs evaluated offline; accept set = table.
* **Inferred (not exercised):** the exact semantics of the 20-bit unlock mask at `0x0300F30` beyond the visible thumbnails; the purpose of the unused `Level Select` / `Music Test` / `SFX Test` strings (likely cut content).

## 8. Unknowns

* Why `Level Select`, `Music Test` and `SFX Test` survive in the text bank: no 32-bit pointer (with or without Thumb bit) to `0x082783E0`, `0x082784C0` or `0x082784CC` exists in the ROM, and no reachable screen displayed them. Treated as dead/cut text, not a hidden menu.
* The "extra balloon / helmet" gameplay secret in Sandy's Tree Dome is a level item, not a code; not exhaustively retraced here.
* No SRAM save format was analysed; password effects are written to IWRAM bitfields.

## 9. Tooling

* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for all disassembly.
* Python: `enumerate.py` (pointer-table dereference + full-space enumeration), `patch_ss.py` (mGBA `gbAs` zlib-chunk patcher), `ss.py` (savestate extract/diff), `enter_code.py` (xdotool keyboard helper), `dbgserver.py` + `dbg.py` (PTY front-end for mGBA `-d`, used because the GDB stub port 2345 was occupied by another session's emulator).
* mGBA 0.10.5, Xvfb :319, openbox, xdotool, scrot, gdb-multiarch (unused after stub conflict).
* Cleanup: only this job's PIDs were killed by number; the working ROM copy and all savestates/screenshots were kept in `/tmp/spongesuper`. The ROM folder contains only the original `.gba`.
* No ROM or copyrighted assets are redistributed here; only addresses, hashes, algorithms and the game's own 4-letter codes are published.
