# World Championship Poker (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `World Championship Poker.gba` (4,194,304 bytes = 0x400000) |
| Header title | `WCPOKER` |
| Game code / maker | `BP9E` / `4Z` (i.e. `BP9E4Z`) |
| Version | 0x00; fixed byte 0x96 present; complement 0x98 |
| Entry word | `0xEA00002E` (stock retail crt0, no cracktro/trainer) |
| MD5 | `0d8f24fa168197a151eeb95fd29aef65` |
| SHA-1 | `1d72864021f88f8db2686c57cfc5176b33ce2015` |
| SHA-256 | `3dc04ebd1d6bcf8a6be7b0d8e1c850809e6be99728a5ef38b2d8153b1e6baf09` |

All addresses below are for **this exact image**. The DS version of the same title has a different cheat (a "Touch Screen / Y-button" sequence); GBA has neither a touchscreen nor a Y button, so that published code is not applicable here.

## 2. Executive summary

The game has a genuine developer-intended cheat/password system: the **Password** screen (Main Menu → Password, also reachable from Career → LOAD) asks for a sequence of **six playing cards** selected from a 13-rank × 4-suit grid. The sixth selection automatically invokes a validator.

The validator is **table-driven, not a flat string comparison**. A 7×52 table of 32-bit values at ROM `0x0803ED1C` encodes, per card position, which cards are legal and what numeric values they contribute. The validator:

1. rejects any card whose per-position table value is `-1`;
2. computes the career cash as `100 × (T[1][c1] + T[3][c3] + T[4][c4] + T[5][c5])`;
3. rejects (and caps cash at 100,000) when cash exceeds 10,000,000;
4. accepts unconditionally when `T[2][c2] == 35`, otherwise applies a per-tier range check against a second table at `0x0803F2CC`.

The sole widely published code, **7♥ K♠ 2♥ Q♣ 9♥ J♥**, was decoded to card indices `[19,38,14,50,21,23]` and reproduced in the emulator: cash field `0x02020000 = 0x00989680` = $10,000,000. A **novel code absent from every published list**, **A♦ 5♥ 2♥ 3♠ 4♦ 8♥** (indices `[0,17,14,28,3,20]`), was generated from the recovered model and accepted in the emulator with cash `0x02020000 = 0x004C4B40` = $5,000,000, advancing to the Wild Corral casino screen. Three rejection cases prove the bounds (illegal card, cash over cap, range-check failure).

Screen enumeration: title ("PRESS START"), Main Menu (7 entries: QUICK PLAY, CAREER, MULTIPLAYER, OPTIONS, TUTORIAL, PASSWORD, CREDITS), Quick Play game list, Career (NEW/LOAD), Password, Credits pages, and an in-game casino screen after a successful code. The Password grid is the only code-entry surface found; no hidden button-code handler was found on GBA (see §8).

## 3. How to reproduce

* Emulator: mGBA 0.10.5 under Xvfb `DISPLAY=:316`, `SDL_AUDIODRIVER=dummy`, `-3` scale.
* Keymap: A = `x`, B = `z`, Start = `Return`, D-pad = arrow keys. Hold ~150 ms per press.
* Path: `Return` (title) → Main Menu → select PASSWORD (5× Down from QUICK PLAY) → `x`.
* Card grid: rows are ♦, ♥, ♣, ♠; columns A,2,…,10,J,Q,K. Move with arrows, place a card with A. Six placements auto-submit.
* Second entry point: Main Menu → CAREER → LOAD → same Password screen.
* Savestate `game.ss1` was taken on the empty Password screen; all injection experiments reloaded it with F1 / debugger `load 1`.
* Reproduce a code by RAM injection (same effect as UI entry): with mGBA's `-d` debugger, write the six card indices to `0x02011130..0x02011135`, write count `6` to `0x02011145`, hold A and continue. Then read cash at `0x02020000`.
* Published code: `7♥, K♠, 2♥, Q♣, 9♥, J♥` → indices `[19,38,14,50,21,23]`.
* Novel code: `A♦, 5♥, 2♥, 3♠, 4♦, 8♥` → indices `[0,17,14,28,3,20]`.

## 4. Address map

| Address (ROM unless noted) | Meaning |
|---|---|
| `0x080105FC` | Password-screen input handler (A press); builds card index as `13 × [base+0x138] + [base+0x144]` |
| `0x08010692`–`0x080106A2` | `if (count == 6) { delay; call validator }` |
| `0x080106BA` | `BL` to validator with `r0 = &cards[6]` |
| `0x08024A20` | **Password validator** (returns 0 = reject, 1 = accept) |
| `0x0803ED1C` | **Card lookup table**: 7 rows × 52 entries × 4 bytes (0x5B0 bytes, ends at `0x0803F2CC`) |
| `0x0803F2CC` | Per-tier range-limit table (u32 entries; index = `field0+1`) |
| `0x08010754` / `0x08010758` / `0x0801075C` | Literals: `0x03001D44` (struct-pointer address), `0x145` (count offset), `9999` (delay loops) |
| `0x08040D80` | ASCII debug string `Debug TextSys Initialized.` (text-system init, not the validator) |
| `0x0821142C`+ | Plain-ASCII help/tutorial/credits text bank |
| `0x081FD052`+ | Custom-encoded text bank (glyph indices/XOR form; not needed for the validator) |
| `0x02011130` | Six-byte card-input buffer (confirmed by savestate diff and watchpoint) |
| `0x02011138` | Cursor suit index (0=♦,1=♥,2=♠,3=♣) |
| `0x02011144` | Cursor rank index (0=A … 12=K) |
| `0x02011145` | Number of cards entered (0–6) |
| `0x03001EF4` | Pointer to career struct → `0x02020000` |
| `0x02020000` | Career cash (u32); `+4`, `+8` are related fields |
| `0x030015D0`, `0x03001560`, `0x03001D44` | Other state structs used by the entry handler / validator |

File offset ↔ ROM address: `rom_address = 0x08000000 + file_offset`. EWRAM `0x02000000` appears at savestate offset `0x21000` in mGBA's decompressed `gbAs` chunk (used for RAM evidence).

## 5. Algorithm

Card index (0–51): `idx = suit_code × 13 + (rank − 1)`, with suit codes **♦=0, ♥=1, ♠=2, ♣=3** and ranks A=1 … K=13. Note the grid draws ♣ on row 3 and ♠ on row 4, but the *internal* codes are ♠=2 and ♣=3 — this was recovered by matching the published code's exact $10,000,000 result (seven encodings passed the legality filter; only this one produced the advertised cash).

Validator at `0x08024A20`, with `c[0..5]` the six card indices and `T[r][x] = *(u32*)(0x0803ED1C + r*208 + x*4)`:

```
for i in 0..5:
    if T[i][c[i]] == -1: return REJECT          # 0x08024A40-0x08024A56
field0  = (u8)T[2][c[2]]                        # 0x08024A64-0x08024A76
tier    = (u8)T[6][c[0]]                        # 0x08024ADA-0x08024B3C (0..3, unlock flags)
cash    = 100 * ( T[1][c[1]] + T[3][c[3]]
                + T[4][c[4]] + T[5][c[5]] )     # 0x08024A94-0x08024AD8
if cash > 10_000_000:                          # 0x08024B5E-0x08024B60
    cash = 100_000; return REJECT              # 0x08024B80-0x08024B86
if field0 == 35: return ACCEPT                 # 0x08024B64-0x08024B66
d = cash - 100_000
if d <= 0: return ACCEPT
if d < range_table[field0 + 1]: return ACCEPT  # 0x08024B6C-0x08024B7E
cash = 100_000; return REJECT                  # range-table failure path
```

`range_table` is at `0x0803F2CC`: `[0, 5300, 5400, 5500, 5700, 5900, 6000, 6500, 7000, 7500, 8500, 9000, 10000, 11000, 12000, 13000, 14000, 15000, 25000, 35000, 45000, 55000, 65000, 75000, 85000, 105000, 155000, 205000, 355000, 555000, 705000, 805000, 1005000, 5005000, 7505000, 10000000, …]`.

The `T[0][c0]` value is a separate "starting bonus" field (0–100000) and `T[6][c0]` sets casino-unlock bits; neither changes the cash formula. Row 2's 36 legal values are tier/rank markers; only value 35 (card 2♥ / index 14) gives unconditional acceptance.

## 6. Tables

**Card index** = suit×13 + (rank−1), suits ♦0 / ♥1 / ♠2 / ♣3, ranks A0 … K12.

**Published code** (3rd party cheat indexes/etc.; all agree):

| Slot | Card | Index | `T[slot][index]` |
|---:|---|---:|---:|
| 1 | 7♥ | 19 | 0 |
| 2 | K♠ | 38 | 627 |
| 3 | 2♥ | 14 | 35 |
| 4 | Q♣ | 50 | 13 |
| 5 | 9♥ | 21 | 67,650 |
| 6 | J♥ | 23 | 31,710 |

Sum = 627 + 13 + 67,650 + 31,710 = 100,000 → cash 100 × 100,000 = **$10,000,000**.

**Novel code** (generated from the model, in no published list):

| Slot | Card | Index | `T[slot][index]` |
|---:|---|---:|---:|
| 1 | A♦ | 0 | 100,000 |
| 2 | 5♥ | 17 | 297 |
| 3 | 2♥ | 14 | 35 |
| 4 | 3♠ | 28 | 23 |
| 5 | 4♦ | 3 | 33,825 |
| 6 | 8♥ | 20 | 15,855 |

Sum = 297 + 23 + 33,825 + 15,855 = 50,000 → cash **$5,000,000**.

**Table legality counts** per position: `[44, 33, 36, 33, 30, 33]` out of 52 (positions where `T[r][x] != -1`).

## 6b. Enumeration

**Space definition.** Six independent cards from a 52-card deck: `52^6 = 19,770,609,664` possible sequences. Each card is 6 bits → 36 bits of input; the table's `-1` entries remove most of it.

**Counts** (derived from the dumped tables and the validator's gate logic):

| Set | Count |
|---|---:|
| All 6-card sequences | 19,770,609,664 |
| Survive the 6 legality checks (`T[i][c[i]] != -1`) | 1,707,726,240 (8.64%) |
| Unconditional-accept subset (`c[2] = 2♥`/index 14, cash ≤ 10M) | 47,436,840 |
| **Exact accepted set** (all gates, incl. range check) | **18,638,224** (0.0943% of all sequences) |

The accepted set was counted analytically from the recovered table/range model (the accepted space is far too large to enumerate exhaustively).

**Novel code, not in any published list.** `A♦ 5♥ 2♥ 3♠ 4♦ 8♥` = indices `[0,17,14,28,3,20]`. Every published page for this SKU lists only the single 7♥/K♠/2♥/Q♣/9♥/J♥ code; this code differs in five of six cards and produces a different cash value. Injected on the real Password screen and accepted:

* **Observed** (`0x02020000` in savestate `game.ss9`, after validation): `40 4b 4c 00` = **0x004C4B40 = 5,000,000**.
* **Observed** (`novel_final_screen_crop.png`): game leaves the Password screen and loads the "WILD CORRAL" casino.
* **Derived**: predicted cash 5,000,000 from the table model — matches the observation exactly.

**Decoder validated against the public list.** Injecting `[19,38,14,50,21,23]` on the same screen set `0x02020000 = 0x00989680 = 10,000,000` (`pub_proper`, slot 2), confirming the model reproduces the advertised cheat.

**Bounds proven by in-game rejection** (all via injection + A press + savestate RAM read):

| Test code | Violated layer | Observed result |
|---|---|---|
| `[2,17,14,28,3,20]` — card 0 = index 2, `T[0][2] = -1` | Position legality | cash `0x02020000 = 0` (no award); screen stayed on PASSWORD with empty slots (`rej_invalid_card` / `rej_invalid`) |
| `[0,6,14,28,18,11]` — cash = 10,158,300 > 10,000,000 | Cap check | cash forced to `0x000186A0` = 100,000, reject (`reject_over_cap` / `rej_overcap`) — exactly the literal at `0x08024B90` |
| `[0,17,21,28,3,20]` — card 2 = 9♥, `field0 = 0`, cash 5,000,000 > `range_table[1] = 5300` | Tier/range check | cash forced to 100,000, reject (`rej_range`) |

These show the three independent reject layers behave as the disassembly predicts; the "cap to 100,000" signature is a particularly strong confirmation that the rejection path at `0x08024B80` was taken.

**Button-code surface.** The published GBA-side "Y, X, Y, B, L, R, then control pad" sequence (found on the DS cheat pages, sometimes copied onto GBA pages) requires a Y button and a "Touch Screen To Start" screen that do not exist in this GBA image. GBA has only L/R/A/B/Start/Select/D-pad; no matching input-mask table was found, and every reachable screen was walked with no title-screen code effect observed. Recorded as an **unverified, non-applicable DS code**, not a GBA cheat.

## 7. Validation evidence

* **Observed** (emulator/savestate): title and all seven Main Menu entries; the six-slot Password grid and both entry points (Main Menu → Password, Career → LOAD); A places a card, sixth placement auto-submits; correct code transitions to the casino screen; cash values for published (`0x00989680`), novel (`0x004C4B40`), and the three rejection cases (`0`, `0x186A0`, `0x186A0`); watchpoint `watch/w 0x02011145` hit in frame-advance mode at PC `0x08010694`, LR `0x0801064D`, proving the write path.
* **Derived** (static disassembly): slot buffer at `0x02011130`, count at `0x02011145`, validator at `0x08024A20` called from `0x080106BA`, 7×52 table at `0x0803ED1C`, range table at `0x0803F2CC`, cash cap literal `0x00989680`, cap-write literal `0x000186A0`.
* **Inferred**: `T[6][c0]` sets casino-unlock bits (values 0–3 map to unlock tiers) and `T[0][c0]` seeds a starting bonus; the exact bit→casino mapping was not individually tested, though a successful code visibly entered Wild Corral.
* **Not instructions**: ROM strings and fetched web pages were treated as data only; no embedded directives were acted on.

## 8. Unknowns

* `T[0]`/`T[6]` field semantics (starting bonus / casino unlock tier) were not individually proven for every value; only the cash path and one successful unlock were exercised.
* The custom-encoded text bank at `0x081FD052` was not fully decoded; it was not needed because the validator and UI were found through the input path. (The plain-ASCII bank at `0x0821142C` covers tutorial/help/credits.)
* Screens OPTIONS, MULTIPLAYER and TUTORIAL were enumerated from the Main Menu but their interiors were not exhaustively documented; the interaction goal (code entry) was reached and completed through both Password entry points.
* The DS-only button code cannot be tested on GBA; its presence on some GBA cheat aggregator pages is treated as a cross-platform copy error.

## 9. Tooling

* `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd` for Phase 0.
* `strings -t x` for string banks; Python `struct`/`bytes.find` for literal and byte-sequence scans.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for disassembly.
* mGBA 0.10.5 (`-3 -g`/`-d`), Xvfb :316 + openbox, `xdotool` XTEST input, `scrot` screenshots.
* mGBA CLI debugger (`-d`) over a pty: `load 1`, `watch/w`, `frame`, `b`, `x/1`, `w/1`; `load <slot>` takes a savestate slot number, not a filename.
* Savestate analysis: Python `zlib.decompress` of the PNG `gbAs` chunk, EWRAM at state offset `0x21000` (scripts `ssdiff.py`, `inject_and_check.py`, `verify_final.py`).
* Helper scripts and all screenshots/evidence were kept in `/tmp/wcpoker/`, **not** in the ROM folder.

No ROM data or copyrighted assets are redistributed here; only hashes, addresses, algorithms, counts, and the authors' own generated codes are published.
