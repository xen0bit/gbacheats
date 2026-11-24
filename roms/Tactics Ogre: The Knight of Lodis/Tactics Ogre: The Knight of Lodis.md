# Tactics Ogre: The Knight of Lodis (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Tactics Ogre: The Knight of Lodis/Tactics Ogre: The Knight of Lodis.gba` |
| Size | 8,388,608 bytes (0x800000) |
| Header title | `TACTICSOGRE` |
| Game code / maker | `ATOE` / `EB` (USA, `AGB-ATOE-USA`) |
| Revision | 0x00 |
| Entry word | `0xEA00002E` → stock `0x080000C0` (no cracktro) |
| MD5 | `5d4f385e4e1cfa4a057d0ac828993906` |
| SHA-1 | `85a46320a31f16f5c6dda27fc094edd078dbe43d` |
| SHA-256 | `c5b439c2530331f38e7a6e16857f58c554f270019641f825ac060f4e7866bae4` |

## 2. Executive summary

This game has **two developer-intended secret codes, both entered as the 8-character protagonist / hired-character name** at the new-game naming screen:

| Name typed | Effect | Verified in emulator |
|---|---|---|
| `MUSIC.ON` | Opens the **Music Mode** track-test menu (31 tracks) | Yes — prompt + menu observed |
| `DEL.DATA` | Offers **"Delete all data?"** | Yes — prompt observed |

The codes are **not ASCII**. The game's name charset maps each on-screen keyboard symbol to a small integer (`A`=0x00 … `Z`=0x19, `a`=0x1A … `z`=0x33, `0`=0x34 … `9`=0x3D, symbols 0x3E+). The two names are stored as **9-byte records** (8 encoded symbols + `0xFF`) in a contiguous table at ROM `0x08613A46`. The validator at `0x0812F578`/`0x0812F5D2` performs exactly two 9-byte `memcmp`s against those literals; a match sets a state flag and routes to the corresponding confirmation dialog.

There is **no algorithmic/generated code system and no hidden third code** on this screen: the accepted set is exactly these two 8-symbol names (§6b proves the bound). The published "Deneb" secret is a **different mechanism** — a preset-name/gameplay transformation, not a name-code accepted by this validator (see §8).

All GameShark/CodeBreaker/Action Replay material found on the web was **excluded from scope** and not used.

## 3. How to reproduce

- Emulator: mGBA 0.10.5 under Xvfb `:317`, `SDL_AUDIODRIVER=dummy`, `-3` scale, GDB stub only for reconnaissance.
- Keymap (SDL default): A=`x`, B=`z`, Start=`Return`, Select=`BackSpace`, D-pad = arrow keys.
- Path: boot → advance the long opening dialogue with repeated `x` (~2,500 presses, or load the supplied state) → the screen titled "Enter name." appears with an 8-slot field and a 10-row on-screen keyboard.
- **D-pad navigation wraps** at both row and column edges (10×10 grid); this matters when scripting input — a clamping model silently mistypes names.
- Type `MUSIC.ON`, then press **Start (Return)** — Start, not the `[END]` cell, submits the name.
  - Expect: `CHECK — Your game can't be resumed once Music Menu is opened. Continue?` → Yes → **Music Mode** menu.
- Type `DEL.DATA`, press Start → `CHECK — Delete all data?` (choose No to keep the save).
- Negative control: type `MUSICXON` (period replaced by `X`), press Start → ordinary `Is the name "MUSICXON" OK?` confirmation, no secret prompt.
- A savestate parked on the empty name screen is reproduced by extracting `gbAs` from any `.ss1`, or by simply replaying the intro.

## 4. Address map

| Item | Address | Evidence |
|---|---|---|
| Secret-code table | ROM `0x08613A46` … `0x08613A57` (18 bytes) | Derived: literal `0x08613A46` at `0x0812F5BC`, second record at `+9` |
| Record 1 — `DEL.DATA` | `0x08613A46`: `03 04 0B 40 03 00 13 00 FF` | Derived (literal bytes) |
| Record 2 — `MUSIC.ON` | `0x08613A4F`: `0C 14 12 08 02 40 0E 0D FF` | Derived (literal bytes) |
| `memcmp` helper | `0x0815B678` (r0=a, r1=b, r2=len; returns 0 on equal) | Derived (disassembly) |
| Name-normalisation + secret check | `0x0812F45A` … `0x0812F62C` | Derived |
| Compare 1 (`DEL.DATA`) | `0x0812F580` (`r2=9`) → on match sets struct `+0x5A = 1` at `0x0812F590` | Derived + Observed prompt |
| Compare 2 (`MUSIC.ON`) | `0x0812F5D2` (`r2=9`) → on match sets struct `+0x5E = 2` at `0x0812F5E2` | Derived + Observed menu |
| Third `memcmp` | `0x0812F720`, 16-byte compare in a 32×0x68-byte unit table at EWRAM `0x02000000` (+0x60 name, +0x7E active flag) | Derived; **not** a code check — unit-name lookup |
| Entered-name buffer | 16 bytes at game-state struct `+0x4A`; in mGBA savestate (0.10.5) the 8 visible symbols appear at raw state offset **`0x4AC92`** (EWRAM, nominally `0x02029C92` under the standard `EWRAM@0x21000` state layout) | Observed: bytes matched the typed name exactly for 4 different names |
| Preset-name string table | `0x08623E1C` … (81 names, `0xFF`-terminated, encoded with the same charset) | Derived |
| Preset-name pointer table | `0x086254D8` (81 × u32); Deneb = index 17 → `0x08623E97`: `03 1E 27 1E 1B` | Derived |

## 5. Algorithm

```
# charset (subset)
A=0x00..Z=0x19, a=0x1A..z=0x33, 0=0x34..9=0x3D, punctuation 0x3E..0x54

validator(state):
    buf = state.name_buffer[0x4A .. 0x59]        # 16 bytes
    normalise(buf):                               # 0x0812F45A..0x0812F562
        find first 0xFF; OR all following slots with 0xFF (pad)
        skip 0x89 markers, left-compact, re-pad
    if memcmp(buf, table[0..9], 9) == 0:          # DEL.DATA
        state[0x5A] = 1; show "Delete all data?"; return
    if memcmp(buf, table[9..18], 9) == 0:         # MUSIC.ON
        state[0x5E] = 2; show music-menu warning; return
    # otherwise: normal "Is the name ... OK?" confirmation
```

No checksum, XOR, key table, PRNG or generator exists on this path. The two comparisons are literal and exhaustive.

## 6. Tables

### 6.1 Charset mapping (keyboard grid, wrap-around 10×10)

Row 0 `A B C D E F G H I J` = 0x00–0x09; row 1 `K..T` = 0x0A–0x13; row 2 `U..Z` = 0x14–0x19;
row 3 `a..j` = 0x1A–0x23; row 4 `k..t` = 0x24–0x2D; row 5 `u..z` = 0x2E–0x33;
row 6 `0..9` = 0x34–0x3D; row 7 `! ? . ; : & - % '` ≈ 0x3E–0x46; row 8 `( ) < > + - * / = "` ≈ 0x47–0x50; row 9 punctuation ≈ 0x51–0x54.
The `.` used by both codes is 0x40 (row 7, column 2) — RAM-verified.

### 6.2 All secret codes (complete)

| # | ROM offset | 9-byte record | Typed name | Effect |
|---|---|---|---|---|
| 1 | `0x613A46` | `03 04 0B 40 03 00 13 00 FF` | `DEL.DATA` | delete-all-data confirmation |
| 2 | `0x613A4F` | `0C 14 12 08 02 40 0E 0D FF` | `MUSIC.ON` | Music Mode menu |

### 6.3 Music Mode menu (complete, 31 entries)

`01` Battle BGM (REZON), `02` Battle BGM1 (YmoH.S), `03` Battle BGM2 (YmoH.S), `04` Battle BGM4 (REZON), `05` Battle BGM5 (REZON), `06` Battle BGM7 (REZON), `07` Battle BGM8 (REZON), `08` **locked** (`??????????`, red), `09` Training (REZON), `10` World Map (REZON), `11` Game Over (REZON), `12` Stage Clear (REZON), `13` Gloomy (REZON), `14` Sudden Change (YmoH.S), `15` Official Business (REZON), `16` Conversation (YmoH.S), `17` Flashback (REZON), `18` Meanwhile… (YmoH.S), `19` Heroine's Theme (REZON), `20` Mermaid Legend (YmoH.S), `21` Sacred Spear (REZON), `22` Character Making (YmoH.S), `23` Interlude (REZON), `24` Opening Theme (YmoH.S), `25` **locked**, `26` **locked**, `27` **locked**, `28` Overture (YmoH.S), `29` **locked**, `30` **locked**, `31` Quest Mode (REZON).
Composer credits as rendered: `REZON` and `YmoH.S`. Six entries (08, 25, 26, 27, 29, 30) remain masked until the game is beaten, matching the published note that "more music is unlocked" after clearing. The list stops at 31 (further Down presses do not add entries).

## 6b. Enumeration

**Space definition.** The entry field is 8 symbols over an ~85-symbol on-screen alphabet (26 upper + 26 lower + 10 digits + ~23 punctuation; codes use values 0x00–0x54), i.e. roughly `85^8 ≈ 2.7 × 10^15` representable strings. The validator compares a fixed **9-byte** image (8 symbols + `0xFF` pad), so length is fixed at exactly 8 — shorter and longer names cannot match.

**Accepted set (complete): exactly 2 of those ~2.7 × 10^15 strings** — `MUSIC.ON` and `DEL.DATA`.

**Proof of the bound (counts, not inference):**
1. The code table occupies the contiguous 18-byte span `0x613A46`–`0x613A57`: two 8-byte records, each followed by one `0xFF`. The next word at `0x613A58` (`01 00 00 00…`) is a different data structure, not a code record.
2. The validator contains exactly **two** 9-byte `memcmp` calls against these literals (`0x0812F580`, `0x0812F5D2`). A third `memcmp` at `0x0812F720` is a 16-byte comparison in a 32-entry × 0x68-byte *unit* table (active-unit name lookup), and is reached from a different state-machine branch — it is not a code check.
3. No generator, checksum, XOR key, PRNG or per-character arithmetic exists on either accepted path; both are literal comparisons. Therefore no code outside the two literals can be accepted by this screen.

**Novel codes.** None can exist: the accepted set is a closed 2-element lookup table, and both elements are already published (tacticsogre.com "Secrets", ChapterCheats, Neoseeker). Per §0.2 this is reported as a **bounded negative**, not glossed over. Every other name I tried (including `CDEFGHIJ`, `MUSICXON`, `AAAAAAAA`) produced the ordinary name-confirmation dialog.

**Novel evidence produced anyway.** Although no novel *code* is possible, four *unpublished representational facts* were established and RAM-verified:
- the exact 8-symbol→byte encoding of the name buffer (no published source documents it);
- the exact ROM location and binary layout of the code table;
- the exact validator pair and their flag destinations (`+0x5A`, `+0x5E`);
- the complete 31-entry Music Mode list with its six post-game-locked slots.

**Rejection bounds (tested in-game):**
- `MUSICXON` — one symbol changed (`.`→`X`), correct length, otherwise identical bytes → **rejected**: only `Is the name "MUSICXON" OK?` appeared; no music prompt, no flag. RAM read of its buffer was the expected 8 encoded bytes.
- `CDEFGHIJ` and `AAAAAAAA` — rejected (ordinary confirmation).
- Truncated names (`<8` symbols) were not separately submitted, but the validator's fixed `r2=9` compare against a record whose 9th byte is `0xFF` proves they cannot match.

## 7. Validation evidence

- **Observed (emulator):** `MUSIC.ON` → CHECK dialog → Music Mode menu with 31 tracks; `DEL.DATA` → "Delete all data?"; `MUSICXON` → normal name confirmation. Screenshots: `s39_musicon_end.png`, `s44_musicmenu.png`, `s45_music_9_crop.png`, `s47_15_crop.png`, `s52_deldata_prompt.png`, `s55_nearmiss_result.png` (work dir `/tmp/tacticsogre`).
- **Observed (RAM):** savestate `gbAs` chunk decoded with `ss.py`; raw state offset `0x4AC92` read back as
  - `CDEFGHIJ` → `02 03 04 05 06 07 08 09`
  - `MUSIC.ON` → `0C 14 12 08 02 40 0E 0D`
  - `DEL.DATA` → `03 04 0B 40 03 00 13 00`
  - `MUSICXON` → `0C 14 12 08 02 17 0E 0D`
  Exactly the intended symbols — this is what established the charset mapping before any ROM search.
- **Derived (disassembly):** table bytes, literal pointers, `memcmp` helper, flag writes (`+0x5A=1`, `+0x5E=2`), 32-unit lookup at `0x0812F720`.
- **Inferred:** the absolute EWRAM address of the name buffer (`0x02029C92`) follows from the savestate's standard `EWRAM@0x21000` layout and the validator's `+0x4A` offset; the raw savestate offset is the directly observed quantity. The composer names are read from the rendered menu, not from a music-metadata table.

## 8. Unknowns

- **Deneb secret (published):** naming a recruited female soldier `Deneb` and changing her to Witch is claimed to transform her. Static evidence: `Deneb` is preset-name **index 17** (`0x08623E97`: `03 1E 27 1E 1B`) in the 81-entry table at `0x086254D8`, and a third 16-byte `memcmp` at `0x0812F720` scans 32 active unit structs. I did not play to the recruit/class-change screen, so the transformation itself is **unverified** and I do not claim it as an accepted *code* on the naming screen.
- The six locked Music Mode slots (08, 25, 26, 27, 29, 30) require a completed save; their titles were not revealed.
- The `0x89` "skip marker" handled by the name normaliser was not produced through the UI; its exact UI origin is unknown.
- No code system exists outside the naming screen within the scope searched (button sequences and hidden top-level menus were not found in the keyword/table scans; the only in-game secrets published for this SKU are the name codes and the Deneb gameplay secret).

## 9. Tooling

- `ss.py` — extracts the zlib `gbAs` chunk from mGBA `.ss1` PNG savestates (raw state is 397,312 bytes; EWRAM at state offset `0x21000`).
- `mkstate.py` — rewrites a raw state into a `.ss1` template (PNG chunk CRC recomputed) for fast return to the naming screen.
- `kb.py`, `enter_name.py` — XTEST key helpers for display `:317`; `enter_name.py` contains the full keyboard grid (its first version assumed clamping; D-pad actually wraps).
- `gdbrsp.py`, `gdbd.py` — minimal GDB-RSP client/daemon; the mGBA GDB stub proved single-client and fragile across reconnects, so savestate diffs were the primary RAM method.
- `arm-none-eabi-objdump -M force-thumb`, Capstone-free raw scans via Python, `strings`, `xxd`, `grep -abo`.
- Environment: Xvfb `:317` + openbox, `SDL_AUDIODRIVER=dummy`, mGBA 0.10.5. No copyrighted assets are reproduced; only offsets, hashes, byte encodings and algorithm descriptions are published.
