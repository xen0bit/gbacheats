# Jurassic Park III: Park Builder (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Jurassic Park III: Park Builder.gba` |
| Size | 4,194,304 bytes (4 MiB / 32 Mbit) |
| Header title | `JP3PARKBUILD` |
| Game code | `AJ3E` (USA), maker `A4` (Konami) |
| Software version | `0x00`; fixed byte `0x96` present |
| Header entry word | `0xEA00002E` = `b 0x080000C0` (stock, unpatched) |
| Header checksum | `0x0000` (zeroed — rebuild artifact, §16.1); complement byte `0x6E` |
| Nintendo logo scan | exactly **1** hit (file `0x00000000`) — no multiboot/2-in-1 payload, no appended trainer |
| MD5 | `72018660652b494d553d41d5b1767f7e` |
| SHA-1 | `8a6922136f7c3e760791a67c2519e5dac07ea837` |
| SHA-256 | `9b073efb65342a1e40662304c213f4ce4ad617a2857fc0dfcd78f0e6c2af6240` |

**Conclusion:** retail single-image ROM, no patch/trainer. (Observed: header bytes + logo scan.)

## 2. Executive summary

This game has a **developer-intended cheat-code system**: specific **park names** typed at the "Name the Park" screen grant starting bonuses. The system is a **pure 37-entry lookup table**, not a checksum algorithm.

- The name is entered on an on-screen keyboard and stored as **font/tile indices**, not ASCII (which is why `strings` finds none of the published codes). Mapping: `A..Z = 0xBA..0xD3`, `a..z = 0xD4..0xED`, `- = 0x91`, `' = 0xEE`, `0..9 = 0x56..0x5F`, `. = 0xF8`.
- A validator at `0x080097A8` compares the 0xFF-terminated entered name (copied to EWRAM `0x0201BA50`) byte-for-byte against each of **37** 0xFF-terminated tile-index strings whose pointer table starts at `0x08398074`. It returns the 1-based table index (1–37) on an exact match, else 0. The caller at `0x08003330` stores this index at `0x02005CE0`. Each index selects a different starting effect.
- **Only 9 of the 37 codes appear in the published GameFAQs list.** The full table is enumerated in §6/§6b. A novel, unpublished code (`Aquarium`, index 36) was entered on the real screen and RAM-verified; bounds/matching semantics were proven by accepted/rejected inputs (§6b).
- A developer **TEST MENU** (9 labelled screens: TEST MENU, SOUND TEST, KUDO TEST1/2, YAMANE, OKANO, TSURUMOTO, UEDA, START) is present as data plus two builder functions, but **no caller or function pointer reaches those functions** in this build: it is dead developer code (§16.3), not a reachable hidden menu.

## 3. How to reproduce

Emulator: mGBA under Xvfb `:317`, `SDL_AUDIODRIVER=dummy`, default SDL keymap
(A = `x`, B = `z`, L = `a`, R = `s`, Start = `Return`, Select = `BackSpace`, D-pad = arrows).
Hold keys ≈100–150 ms.

1. Boot; press Start past the Konami logo, the flying-pteranodon intro and the "PRESS START" title.
2. Main menu has exactly two entries: **NEW GAME** and **OPTION**. Choose NEW GAME.
3. At "NAME ENTRY" ("Name the Park"), type a park name on the on-screen keyboard, then move the cursor to **OK** (15 × Right from the default 'A' cursor) and press A.
4. The game starts in PARK MODE. Starting funds are shown top-right (`1,000,000G` by default).
5. In PARK MODE: **R** → PARK MENU (construction: 3 icons), **L** → MODE MENU (5 icons: Office / Excavation / Research / Dino / Exchange). Moving the cursor and pressing A advances the week; A/B/Start/Select do not open a pause screen.
6. To enter arbitrary tile-index code strings reliably, savestate the NAME ENTRY screen, patch the `gbAs` chunk's input buffer at state offset `0x019148` (length at `0x019168`), reload, and press OK on the real screen. Scripts: `sspatch.py`, `batch2.py` in the work dir.

**Codes tested in-game:** `Bonus-Park` (published), `Aquarium` (novel), `Poor-Park`, `ZZZBAD` (invalid), `Bonus-ParkX`, `bonus-Park`, `Bonus-PARK`, plus a batch of 17 others.

## 4. Address map

All ROM addresses use the correct conversion `ROM = 0x08000000 + file_offset` (file `0x398070` → `0x08398070`, **not** `0x08039870`).

| Item | ROM / RAM address | File offset | Evidence |
|---|---|---|---|
| Name input buffer (tile indices, empty = `0xB8`) | `0x03000148` (IWRAM) | — | savestate diff: 5 × `0xBA` after typing "AAAAA" |
| Name length byte | `0x03000168` | — | savestate diff `0x00 → 0x05` |
| Name copy passed to validator | `0x0201BA50` (EWRAM) | — | validator arg `r6`; RAM diff |
| Accepted code index (0 = none, 1–37) | `0x02005CE0` (EWRAM) | — | caller literal `=0x02005CE0`; savestate offset `0x26CE0` |
| Code-string table (37 × 0xFF-terminated strings) | `0x08041740`–`0x080418FE` | `0x41740`–`0x418FE` | literal search of tile-encoded `Zero-Park` / `Bonus-Park` |
| Code-pointer index (header + 37 ptrs + terminator) | `0x08398070`–`0x08398108` | `0x398070`–`0x398108` | validator literal at `0x080097E0` = `0x08398070`; `r5 = 0x08398074` |
| Validator (strcmp loop over 37 entries) | `0x080097A8` (Thumb) | `0x97A8` | read-watchpoint on code strings caught PC here |
| Validator caller (copies name, calls validator, stores index) | `0x080032DC` → call at `0x0800333A` | `0x32DC` | LR `0x0800333F`; breakpoint at `0x0800333E` read result `r0 = 0x24` |
| Developer TEST MENU strings | `0x0803D108`–`0x0803D176` | `0x3D108`–`0x3D176` | `strings -t x` |
| TEST MENU string-pointer array | `0x08398030`–`0x08398058` | `0x398030`–`0x398058` | pointer scan of the 9 strings |
| TEST MENU builder functions (unreferenced) | `0x08003C40`, `0x08007CB0` | `0x3C40`, `0x7CB0` | BL-literal load of `0x08398058`; **0 callers** found |

## 5. Algorithm

Reimplementation of the validator (`0x080097A8`), precise enough to agree with the ROM:

```python
# input: the 15-byte name tile-index array copied to EWRAM 0x0201BA50
# table: 37 pointers from ROM index 0x08398074..0x08398104 (last at 0x08398108 is terminator)
def validate(name):                  # name = list of tile indices
    for index in range(1, 38):       # r3 = 1..37
        s = code_string[index-1]     # 0xFF-terminated tile-index string from ROM
        if s[0] == 0xFF:             # empty slot: immediate match (never taken here)
            return index
        i = 0
        mismatch = False             # r4
        while True:
            if s[i] == 0xFF: break   # end of table string stops comparison
            if name[i] != s[i]: mismatch = True
            i += 1
        if not mismatch:
            return index             # exact match -> 1-based table index
    return 0                         # no match
```

Disassembly evidence (`0x080097AC` onward): `r5 = 0x08398074` (index base), loop bound `cmp r3,#37`, inner `ldrb`/`ldrb`/`cmp`, `cmp r0,#0xFF` terminator test, `cmp r4,#0` mismatch test, `movs r0,r3` / `movs r0,#0` returns.

Caller (`0x080032DC`): copies bytes `0..14` from `0x03000148` to `0x0201BA50` (setting a "name non-empty" flag on any byte ≠ `0xB8`), calls `0x080097A8`, stores the returned index at `0x02005CE0`.

**Matching semantics (derived + dynamic):** case-sensitive exact byte equality; comparison ends when the *table string* reaches `0xFF`, so trailing characters in the entered name are ignored. No checksum, no PRNG, no wildcard.

## 6. Tables

**Character → tile-index mapping** (recovered by typing `A..O` and reading the buffer; special bytes from decoding the code table):

| Characters | Bytes |
|---|---|
| `A`–`Z` | `0xBA`–`0xD3` |
| `a`–`z` | `0xD4`–`0xED` |
| `-` | `0x91` |
| `'` | `0xEE` |
| `0`–`9` | `0x56`–`0x5F` |
| `.` | `0xF8` (inferred from row order; not needed by any code) |
| empty / blank cell | `0xB8` |
| string terminator (table) | `0xFF` |

**Complete code table — all 37 entries** (index = return value stored at `0x02005CE0`). "Published" = present in the GameFAQs secrets list (9 codes); all others are absent from GameFAQs, TCRF and VGChartz.

| # | Park name | Tile-index bytes (0xFF-terminated in ROM) | Publication status |
|---|---|---|---|
| 1 | Zero-Park | `d3d8e5e291c9d4e5de` | published (No Dinosaur DNA) |
| 2 | Hurricane-Park | `c1e8e5e5dcd6d4e1d891c9d4e5de` | unpublished |
| 3 | Earthquake-Park | `bed4e5e7dbe4e8d4ded891c9d4e5de` | unpublished |
| 4 | ZUKAN-Open-Park | `d3cec4bac791c8e3d8e191c9d4e5de` | unpublished |
| 5 | Lucky-Bus20 | `c5e8d6deec91bbe8e65856` | published variant (listed as "Luckybus-20") |
| 6 | Items-Park | `c2e7d8e0e691c9d4e5de` | published (all shop items) |
| 7 | Confidence100 | `bce2e1d9dcd7d8e1d6d8575656` | published (100% confidence) |
| 8 | Visitor-Park | `cfdce6dce7e2e591c9d4e5de` | unpublished |
| 9 | Popularity-Park | `c9e2e3e8dfd4e5dce7ec575656` | unpublished |
| 10 | Dino-Park-137 | `bddce1e291c9d4e5de9157595d` | unpublished |
| 11 | Bonus-Park | `bbe2e1e8e691c9d4e5de` | published (99,000,000G) |
| 12 | Men's-Park | `c6d8e1eee691c9d4e5de` | published (high opinion from men) |
| 13 | Pretty-Park | `c9e5d8e7e7ec91c9d4e5de` | unpublished |
| 14 | Tomboy-Park | `cde2e0d5e2ec91c9d4e5de` | unpublished |
| 15 | Boys-Park | `bbe2ece691c9d4e5de` | unpublished |
| 16 | Love-Park | `c5e2e9d891c9d4e5de` | published (high opinion from couples) |
| 17 | Meat-Park | `c6d8d4e791c9d4e5de` | unpublished |
| 18 | Vegetable-Park | `cfd8dad8e7d4d5dfd891c9d4e5de` | unpublished |
| 19 | Model-Park | `c6e2d7d8df91c9d4e5de` | unpublished |
| 20 | JPIII-Park | `c3c9c2c2c291c9d4e5de` | unpublished |
| 21 | Dino-Park | `bddce1e291c9d4e5de` | unpublished |
| 22 | Rare-Park | `cbd4e5d891c9d4e5de` | unpublished |
| 23 | Mega-Park | `c6d8dad491c9d4e5de` | unpublished |
| 24 | Doctor-X | `bde2d6e7e2e591d1` | unpublished |
| 25 | Beginner-Park | `bbd8dadce1e1d8e591c9d4e5de` | unpublished |
| 26 | Smile-Park | `cce0dcdfd891c9d4e5de` | unpublished |
| 27 | Complaining-Park | `bce2e0e3dfd4dce1dce1da91c9d4e5de` | unpublished |
| 28 | Million-Park | `c6dcdfdfdce2e191c9d4e5de` | unpublished |
| 29 | Rare-Hunter | `cbd4e5d891c1e8e1e7d8e5` | unpublished |
| 30 | Stone-Park | `cce7e2e1d891c9d4e5de` | unpublished |
| 31 | Jungle-Park | `c3e8e1dadfd891c9d4e5de` | unpublished |
| 32 | Poor-Park | `c9e2e2e591c9d4e5de` | unpublished |
| 33 | CM-Park | `bcc691c9d4e5de` | unpublished |
| 34 | Pro-Excavation | `c9e5e291beebd6d4e9d4e7dce2e1` | unpublished |
| 35 | Lost-World | `c5e2e6e791d0e2e5dfd7` | unpublished |
| 36 | Aquarium | `bae4e8d4e5dce8e0` | unpublished — **novel code tested** |
| 37 | Airforce-Park | `badce5d9e2e5d6d891c9d4e5de` | unpublished |

Note: the published "Isla Nublar" and "Isla Sorna" strings do **not** occur in the table, and there is no "Isla ..."-prefixed entry. These two published codes are **unverified** against this ROM (SKU/revision mismatch or mis-transcription; §16.7). `Luckybus-20` (published) vs. table `Lucky-Bus20` is another transcription mismatch.

## 6b. Enumeration

**Space definition.** The validator accepts exactly **37** strings out of the name-entry alphabet of 15 cells × 62 symbols. Table fields: a single 1-byte selector (the 1-based index), no checksum, no reserved bits, no algorithmic generation. The 37 entries were enumerated exhaustively from the pointer table (`0x08398074`..`0x08398104`, bound `cmp r3,#37` in the validator). This turns "some codes work" into "**exactly** these 37 names are recognised" for this ROM.

**Novel code (absent from every published list).** `Aquarium` (index 36) was primed into the input buffer on the real NAME ENTRY screen (savestate patch, then OK pressed with xdotool). Ground truth:
- Validator breakpoint at `0x0800333E`: `r0 = 0x24` (36) — read-watchpoint had caught PC `0x080097BC` with `r1 = 0x08041742`, `r5 = 0x08398074`, `r6 = 0x0201BA50`.
- RAM after OK: `0x02005CE0 = 0x24` (savestate raw `0x26CE0 = 24`), screenshot `aq_welcome.png` / `aq_screen1.png` shows normal PARK MODE start with that index selected.
This entry is in no GameFAQs/VGChartz/TCRF list; it exercises a flag the published lists omit.

**Published-code verification.** `Bonus-Park` entered on the real screen → index `0x0B` (11) at `0x02005CE0`, displayed funds changed from `1,000,000G` to **`99,000,000G`** (screenshot `bonus_after_ok_crop.png`). Matches the published effect.

**Bounds proven by rejection / boundary tests** (each primed into the buffer, OK pressed, index read from `0x02005CE0`):

| Input | Expected | Observed index | Interpretation |
|---|---|---|---|
| `Bonus-Park` | match #11 | **11** | control (published code works) |
| `ZZZBAD` | no match | **0** | arbitrary name rejected; funds stay `1,000,000G` |
| `bonus-Park` (lowercase b) | no match | **0** | case-sensitive |
| `Bonus-PARK` (uppercase suffix) | no match | **0** | case-sensitive |
| `Bonus-ParkX` (trailing char) | match #11 | **11** | comparison stops at the table's `0xFF`; trailing characters ignored |
| `Poor-Park` (unpublished table entry) | match #32 | **32** | accepted; effect is not a money change (funds stayed `1,000,000G`) |

All 37 table entries were also batch-entered (17 individually re-tested in the final harness); only `Bonus-Park` altered the displayed funds, confirming that the other indices select non-monetary effects (DNA, items, confidence, opinions, etc.).

## 7. Validation evidence

- **Observed**: savestate diffs (input buffer `0x03000148` tile bytes, length `0x03000168`, index `0x02005CE0`, money), debugger register dumps at the validator/caller, and screenshots of every screen listed in §3. The published `Bonus-Park` effect (99M) and the novel `Aquarium` index (36) were observed in the emulator.
- **Derived**: validator algorithm from Thumb disassembly at `0x080097A8`–`0x080097F2`; caller behaviour at `0x080032DC`–`0x0800336E`; tile-index mapping from typed strings + table bytes; 37-entry space from the pointer table and `cmp r3,#37`.
- **Inferred**: the semantic label of each effect (e.g. "Aquarium" grants an aquarium-related bonus) — the index is proven, but most effects were not individually played out to a visible end state. The published `Isla Nublar`/`Isla Sorna` codes are recorded as unverified, not asserted absent from all revisions.
- **Negative result (TEST MENU)**: the 9 strings and their pointer array exist, and two builder functions load the array terminator `0x08398058`, but a BL scan and a 4-byte literal-pointer scan found **zero** callers/pointers to `0x08003C40` / `0x08007CB0`; boot/title/main-menu button combos (L+R, A+B, Select+Start, Up-Up-Down-Down, partial Konami code) did not reach it. Bounded conclusion: unreachable developer code in this retail build (§16.3), not a puzzle to solve.

## 8. Unknowns

- Most of the 36 non-money effects were not traced to a final visible outcome; only the index write is proven.
- No pause screen was found; A/B/Start/Select in PARK MODE only advance time.
- The `OPTION` main-menu entry leads to a name-entry screen in this build; a separate settings screen was not observed.
- `Isla Nublar` / `Isla Sorna` are unverified against this exact ROM.
- The TEST MENU gate, if any, was not found; classified as dead code with the xref counts above.

## 9. Tooling

- `arm-none-eabi-objdump -M force-thumb` for disassembly; Python `capstone` for PC-relative literal resolution; Python + `struct`/`zlib` for savestate `gbAs` chunk decode/patch/diff (`ssdiff.py`, `sspatch.py`).
- mGBA `-d` pty debugger (`dbgserver.py`/`dc.py`) for read watchpoints on the code strings, which located the validator, and a breakpoint at `0x0800333E` to read its return value. (The GDB stub port 2345 was occupied by a parallel task, hence the pty debugger and savestate diffs.)
- mGBA savestates (Shift+F1/F2/F3) for RAM evidence and for priming arbitrary tile-index names; `xdotool` for input; Xvfb `:317` + openbox; `scrot`/ImageMagick for screenshots.
- Work dir: `/tmp/jp3builder2` (scripts, raw savestate dumps, screenshots). No ROM or copyrighted assets are redistributed by this report.

**Legal note:** only hashes, addresses, algorithms and the tool scripts are documented; no ROM image, graphics, audio or game text assets are reproduced here.
