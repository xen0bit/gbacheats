# Spirit: Stallion of the Cimarron — Search For Homeland (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Spirit: Stallion of the Cimarron - Search For Homeland.gba` |
| Size | `0x400000` (4,194,304 bytes / 4 MiB) |
| Header title | `SPIRIT: STAL` |
| Game code | `AC6E` (AGB-AC6E-USA) |
| Maker | `78` |
| Version | `0x00` (Rev.00) |
| Header fixed byte | `0x96` ✓ |
| Header checksum | `0x0000`; complement byte `0x7A` (sum `0xA0..0xBC` = `0x6D`, so a correct complement would be `0x93`) — rebuilt-header artifact, not a game change |
| Entry word | `0xEA00002E` → stock `0x080000C0` crt0 (no cracktro patch) |
| MD5 | `9b5b46ff73e5746f753747b79d2afd66` |
| SHA-1 | `220791a2a4db7d45fc6fb0bd259cf7a8d24e3a6d` |
| SHA-256 | `37c379885fd3a85e8b54b7c6de13c4cfc31232d78f5e4cfa5bdc717ccf3a3af4` |

Embedded-header scan: exactly **one** 156-byte Nintendo logo hit (file `0x4`, header `0x0`). No multiboot stub, second image, appended trainer, or cheat device. Save type: password based; the `.sav` created by mGBA stayed 0 bytes throughout. No GameShark/CodeBreaker/Action Replay codes are analyzed in this report (those found on the web are cheat-device patches, out of scope).

## 2. Executive summary

The game has a genuine in-game **14-character password system** (two 7-character words) reached from the title screen via **Start → Continue Game → A**. There is no level-select menu, no button code, and no reachable debug menu; the only hidden/debug-looking data in the image is dead leftover runtime strings with zero code references.

Passwords are **algorithmic, not a lookup table** — none of the published strings occur literally in the ROM (ASCII or case-shifted). The screen is a 3-row × 11-column letter grid of exactly **32 symbols**:

```
b c d f g h j k l m n
p q r s t v w x y z B
C D F G H J K L M N
```

Each character is a 5-bit index (0..31); 14 characters give a 70-bit code. `FUN_080122C8` converts the two 7-character buffers through a tile→index inverse (`FUN_0801289C`), reconstructs eight 8-bit sub-values by subtracting an 8-bit base `chk` assembled from characters 9, 12 and 10 of the code, checks three conditions, and then writes a set of decoded fields into the game-state record. A checksum pass is *necessary but not sufficient*: further game-state range checks can reject a checksum-valid code.

I reimplemented the decoder in Python; it agrees with **23 of 31** published codes (the other 8 published "Part I/II/Complete" codes from one site have a checksum inconsistent with this USA image and are recorded as unverified). A single-character mutation of a published code that sets the unadvertised field value **F0 = 0** — `bFghjjdNqdCCjm` — was accepted in the emulator and produced a **different game state** (`0x0200AFD3 = 0x0E`) from the published level-1 password (`0x08`). An out-of-range/bad-checksum code `bNghjjdNqzCCjm` was rejected in-game and RAM showed the validator rolling the entry cursor back from 14 to 13 without changing game state.

## 3. How to reproduce

Emulator: mGBA 0.10.5 under Xvfb, `SDL_AUDIODRIVER=dummy`, default SDL keymap (A = `x`, B = `z`, L = `a`, R = `s`, Start = `Return`, Select = `BackSpace`, D-pad = arrow keys), 100–150 ms key holds.

Menu path to the password screen (note the cursor is clamped, so **Down** once, not Up, selects Continue Game):

1. Title "Press START" → `Return`.
2. Main menu `Start New Game / Continue Game / Options` → `Down` once → `x`.
3. "Enter Your Password" grid appears. Navigate with the D-pad and press `x` to select each letter. Type 14 letters; the 14th press runs the validator automatically.
4. `B` deletes the last letter. A valid code transitions straight into gameplay; an invalid code returns the cursor to slot 13 and leaves the screen up.

Codes used in this report:

| Code | Purpose | Result |
|---|---|---|
| `dFghjjdNqdCCjm` | published level-1 password | accepted; `0x0200AFD3` 1→8 |
| `bFghjjdNqdCCjm` | **novel**, F0 = 0 (never published) | accepted; `0x0200AFD3` 1→14 |
| `bNghjjdNqzCCjm` | out-of-range checksum (val1 ≥ chk, bit mismatch) | rejected; `0x0200AFD3` stays 1, cursor 14→13 |
| `FbMCrlxDtFxNGy`, `FbKMFrjDtvjNch` | checksum-valid but semantically out of range | rejected (bounds proof) |

RAM evidence was obtained with mGBA savestates (`.ss1`–`.ss7`), decompressing the PNG `gbAs` chunk (`zlib.decompress`) and diffing the raw 397,312-byte state: EWRAM starts at state offset `0x21000`, IWRAM at `0x19000`. The GDB stub on TCP 2345 was **not usable** because another concurrently running agent owned that port; the savestate-diff method replaced it.

## 4. Address map

| Address (ROM) | Meaning |
|---|---|
| `0x08000000`–`0x080000C0` | ARM crt0 / header |
| `0x08002960` | keypad read: reads `0x04000130`, writes active-high held `0x02001874` and newly-pressed `0x02001876` |
| `0x08002990`, `0x080029AC` | `is_key_pressed(mask)` helper (96 call sites) |
| `0x080122C8` | **password validator** (`FUN_080122C8`) |
| `0x080124A0` | 15-entry jump table indexed by field `F0` (0..14; 15 = no action) |
| `0x08012740` | success/valid flag byte |
| `0x080127D8` | password-screen state machine (tests `0x0200AFD3` ∈ {0,1,0xFF}) |
| `0x08012858` | grid index (0..31) → font tile index |
| `0x0801289C` | font tile index → grid index (inverse) |
| `0x080128E0` | password-screen input handler: grid 3×11, 14 slots, calls validator at slot 14 |
| `0x08012A80`–`0x08012AC0` | validator caller; builds a 64-byte parameter block and passes its tail in r0–r3 |
| `0x08000820` | on-valid hook (`0x02000830` = 0x20, `0x02000834` = 1) |
| `0x0810502C` | screen descriptor `{0x19, 0, 0x080128E1, 0, 0}`; the `0x080128E1` pointer is consumed at `0x080127E8` |
| `0x08104F84`, `0x08104FA0` | dead debug strings `"Your position is %d, %d"`, `"Enemy position..."` (zero xrefs) |

| RAM address | Meaning |
|---|---|
| `0x0200B404`..`0x0200B40A` | password word 1 — 7 font tile indices |
| `0x0200B40E`..`0x0200B414` | password word 2 — 7 font tile indices |
| `0x0200B418` | entry cursor / count (0..14) |
| `0x0200AFD3` | screen/game state: `0x01` = password screen, `0x08` = published L1 level, `0x0E` = novel F0=0 state |
| `0x020019AE` | gate flag for the `mode ≤ 5` check |
| `0x02001984 + 6` | stored `mode` field (player/horse selector) |
| `0x02001874` / `0x02001876` | active-high held / newly pressed key masks |

File offset = ROM address − `0x08000000`.

## 5. Algorithm

All indices below are grid indices (0..31), obtained from the on-screen characters by:
`ALPHA = "bcdfghjklmn" + "pqrstvwxyzB" + "CDFGHJKLMN"`.
The screen stores tile indices (with gaps) via `FUN_08012858`; the validator first maps each back with `FUN_0801289C`.

Let the 14 entered characters be `a0..a6` (first word) and `b0..b6` (second word).

```
chk = ((b0 & 31) << 3) | ((b3 & 3) << 1) | (b2 & 1)          # 8 bits
v0  = (a0 << 3) | (b1 >> 2)
v1  = (a1 << 3) | ((b2 >> 2) & 3)
v2  = (a2 << 3) | (b3 >> 2)
v3  = (a3 << 3) | (b4 >> 2)
v4  = (a4 << 3) | (b5 >> 2)
v5  = (a5 << 3) | (b6 >> 2)
v6  = (a6 << 3) | ((b1 & 3) << 1) | ((b2 >> 1) & 1)
dk  = (vk - chk) & 0xFF                                       # for k = 0..6

# decoded fields (sp offsets in FUN_080122C8)
F0  = d0 >> 4            ; G0  = d0 & 0xF          # level selector, sub-state
P1  = (d1 >> 5) & 3      ; Q1  = d1 & 0x3
mode = ((b3 >> 2) & 3) << 1 | (b6 & 1)
C7  = chk >> 7

# checksum-layer acceptance (all required):
accept = (C7 == ((d1 >> 6) & 1)) and (v1 < chk) and (mode <= 5 or flag != 0)
```

On acceptance the validator stores `mode` and `C7` into the state record, dispatches through the 15-entry table at `0x080124A0` on `F0`, writes `G0` and the nibbles of `d2..d6` into further state bytes, applies four level-conditioned range checks, and finally returns a nonzero value. On failure it returns 0; the screen handler decrements the cursor and redraws.

The inverse (encoder) used to mint `bFghjjdNqdCCjm`: choose the desired `d0`, compute `v0 = (d0 + chk) & 0xFF`, set `a0 = v0 >> 3` and keep `b1 >> 2 = v0 & 7`; all other positions are inherited from a known-valid code. This changes only character 1 of the published level-1 password (`d` → `b`), leaving `chk = 252`, `mode = 3` and every other field intact.

## 6. Tables

**Alphabet / symbol order (5-bit index → character):**

| idx | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| char | b | c | d | f | g | h | j | k | l | m | n | p | q | r | s | t |
| idx | 16 | 17 | 18 | 19 | 20 | 21 | 22 | 23 | 24 | 25 | 26 | 27 | 28 | 29 | 30 | 31 |
| char | v | w | x | y | z | B | C | D | F | G | H | J | K | L | M | N |

There is no digit in the alphabet; the published `1vdNNbH` is an OCR/transcription error for `lvdNNbH` (lowercase L), which passes the decoder.

**Field layout (decoded from `FUN_080122C8`):**

| Field | Source | Width | Observed values |
|---|---|---|---|
| `F0` | `d0 >> 4` | 4 bits | published 1..14; novel 0 |
| `G0` | `d0 & 15` | 4 bits | 4, 5, 7, 15 |
| `chk` bits 6..7 | `b0`, `b3`, `b2` | 2 bits | 60, 124, 188, 252 (all ≡ 60 mod 64) |
| `mode` | `b3>>2` (2 bits), `b6&1` | 3 bits | 2, 3, 6, 7 in valid published codes; 1 rejected by later checks |
| `P1`,`Q1` | `d1` | 2+2 bits | P1 ∈ {2,3}, Q1 ∈ {0,1,2,3} |
| `d2..d6` | `v2..v6 − chk` | 8 bits each | stored as shifted nibbles into the state record |

**Published-code verification against this ROM (USA, AC6E):**

| Source | Codes | Decoder result |
|---|---|---|
| Cheat Happens / absolutcheats / ggmania / cheatbook / mogelpower (13 level codes `dFghjjd…` … `BDChhbj…`) | 13 | all 13 pass; `F0` decodes to 1,2,3,7,8,6,4,5,9,10,11,12,14 (published "level" labels do not match `F0` 1:1) |
| TMQ Horse Game Database (`dFgrrbN…` … `nDCLhDF…`) | 5 | 4 pass verbatim; `1vdNNbH DcMCBLb` passes only after `1`→`l` |
| cheatingdome 14-char "Part I / Complete" list | 13 | first 5 pass; last 8 all have `chk = 60` with `v1 ≥ chk` (borrow fails) ⇒ inconsistent with this USA validator; likely another region or transcription errors. Recorded as unverified, not silently dropped. |

## 6b. Enumeration

**Space definition.** 32 symbols × 14 positions = `32^14 = 1,180,591,620,717,411,303,424` (≈1.18×10²¹) representable strings. There is no lookup table; the accepted set is defined by the validator constraints.

**Exact count at the checksum layer.** The constraints involve only five characters (`b0`, `b2`, `b3`, `b6`, `a1`); the other nine (`a0`, `a2..a6`, `b1`, `b4`, `b5`) are free. Exhaustive enumeration of the five constrained positions gives **6,266,880 / 33,554,432** passing tuples, so:

```
checksum-layer accepted strings = 6,266,880 × 32^9
                                = 220,496,237,756,059,484,160   (18.6767578125 % of 32^14)
```

The game then applies `F0`-dispatch and four level-conditioned range tests, so the finally playable set is a strict subset of that number. (Those later tests are proved to exist by the two rejected checksum-valid codes below; an exact closed-form count of the final subset was not derived — reported as an unknown rather than guessed.)

**Novel code (absent from every published list).** `bFghjjdNqdCCjm` — published level-1 code with character 1 changed from `d` to `b`, setting `F0 = 0`, a value that appears in no published list (published `F0` ∈ 1..14). Verified in-game:

- screenshot `/tmp/spiritstallion/novel_after.png` — game left the password screen and loaded a distinct scene;
- RAM: `0x0200AFD3` `0x01 → 0x0E`, versus `0x01 → 0x08` for the published level-1 password;
- buffers `0x0200B404` = `01 1f 06 07 09 09 03`, `0x0200B40E` = `27 10 03 1c 1c 09 0c`, cursor `0x0200B418 = 0x0E`.

**Bounds proved by rejection.**

| Rejected input | Violated constraint | In-game evidence |
|---|---|---|
| `bNghjjdNqzCCjm` (out-of-range `v1 = 253 ≥ chk = 252`; `d1` bit 6 ≠ `chk` bit 7) | checksum layer | screenshot `reject_after.png`: still on "Enter Your Password", cursor back on slot 13; RAM `0x0200AFD3 = 0x01` unchanged, `0x0200B418 = 0x0D` |
| `FbMCrlxDtFxNGy` (`F0=0`, checksum-valid, `mode=1`) | later game-state checks | password screen retained, `0x0200AFD3 = 0x01`, cursor `0x0D` |
| `FbKMFrjDtvjNch` (`F0=0`, checksum-valid, `mode=3`) | later game-state checks | password screen retained, `0x0200AFD3 = 0x01`, cursor `0x0D` |

**Button codes / hidden menus.** All single keys and the combinations `L+R`, `L+R+Select`, `L+R+Start`, `Select+Start`, `Start+A`, `Start+Select`, `A+B+Select+Start` were pressed on both the title screen and in gameplay. No new screen appeared; the only state changes were the normal main menu, options, and pause menu. The debug-looking strings at `0x08104F84`/`0x08104FA0` have zero code xrefs in Ghidra, so they are dead data. This is a bounded negative for a button-code or debug-menu system.

## 7. Validation evidence

**Observed (emulator / savestate RAM):**

- All screens walked: title; main menu (3 items); Options (Music, Sound FX, Credits, multi-page); Choose Your Player (male/female); Enter Your Password (3×11 grid); gameplay with tutorial; pause menu (Continue, Restart Level, Quit Level, Quit Game); Select screens 1–3 (Horse Info, Inventory, Special Items).
- Password screen RAM baseline: `0x0200B404..0x0200B414 = 0xFF`, `0x0200B418 = 0x00`, `0x0200AFD3 = 0x01`.
- Published code accepted: `0x0200AFD3 = 0x08`; buffers filled with the expected tile indices; cursor `0x0E`.
- Novel code accepted: `0x0200AFD3 = 0x0E` (different from published).
- Three rejected codes: state remains `0x01`, cursor rolled back to `0x0D`.

**Derived (static analysis, Ghidra + objdump):**

- Password screen input handler `0x080128E0`, validator `0x080122C8`, alphabet helpers `0x08012858`/`0x0801289C`, call site `0x08012AB8`, 15-entry dispatch table `0x080124A0`, state variable `0x0200AFD3`.
- Exact checksum constraint set and the 6,266,880/33,554,432 count.
- One Nintendo logo hit, stock entry branch, no trainer/multiboot image.
- Zero xrefs to debug strings; all gameplay button-combo probes negative.

**Inferred / not fully exercised:**

- Field names `F0`, `G0`, `mode`, `P1`, `Q1` are conservative labels from the bit layout; only `F0` is proven to select a distinct game state (published values give 8; `F0=0` gives 14).
- The exact failed semantic check for the two checksum-valid-but-rejected codes was not isolated to one of the four range tests at `0x08012644`–`0x080126A4` (the value of the `r9` parameter at the call site was not recovered). Reported as a bounded negative, not as a decoder error.
- The 8 inconsistent codes from the "Part I/II/Complete" list may belong to a different regional SKU; that was not tested because only the USA ROM was provided.

## 8. Unknowns

- Exact final accepted-set size after the `F0` dispatch and four level-conditioned range checks (the checksum-layer upper bound is exact).
- Semantic meaning of `G0`, `P1`, `Q1`, `d2..d6`, and the precise `r9` argument used by the validator's range tests.
- Whether `mode` values 0/1/4/5 are ever usable in some game state (all observed valid codes use 2,3,6,7; my two mode-based novel codes were rejected).
- Regional validity of the eight inconsistent "Part" codes (no EU/FR/DE ROM available here).
- No reachable debug menu was found; a gated feature that requires a save-file flag could not be excluded purely statically, but every reachable screen was walked and every key combination tested.

## 9. Tooling

- `md5sum`, `sha1sum`, `sha256sum`, `file`, `xxd`, `strings -t x`, `grep -abo`.
- `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb|force-arm`.
- REA/Ghidra 12.1.4 via the `reverse-engineer-anything` skill: `open_binary` (raw-binary, ARM, base `0x08000000`), `binary_overview`, `xrefs`, `procedure_pseudo_code`, `procedure_assembly`, `read_bytes`; session closed with `close_binary`.
- mGBA 0.10.5 under `Xvfb :315` with `SDL_AUDIODRIVER=dummy`, `openbox`, `xdotool` (XTEST events, 50–150 ms holds), `scrot`.
- Python helpers in `/tmp/spiritstallion/`: `ctl.py` (input/screenshot), `enter_pw.py` (grid navigation and 14-character entry), `decode.py` (published-code decoder), `gen.py` (novel-code solver), `ssdiff.py` (PNG `gbAs` zlib state diff).
- Web sources: Cheat Happens, absolutcheats, ggmania, cheatbook, mogelpower, cheatingdome, TMQ Horse Game Database (incl. scanned English manual OCR via `pdftoppm` + `tesseract` after installing `poppler-utils`), archived GameFAQs guide 22073. TCRF returned 403 and had no archive snapshot; treated as unavailable, not as evidence.

No ROM bytes or copyrighted assets are reproduced in this report beyond short address/hash/algorithm notes and the cheat strings themselves (which are published developer-intended codes).

Legal note: analysis only; the ROM and extracted graphics/music/text are not redistributed.
