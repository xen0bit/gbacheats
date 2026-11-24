# Dragon Ball Z: Collectible Card Game (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Dragon Ball Z: Collectible Card Game.gba` |
| Size | 8,388,608 bytes (0x800000) |
| Header title | `DBZCARDGAME1` |
| Game code | `ADZE` (AGB-ADZE-USA), maker `70`, version `0x00` |
| Header checksum | 0x0000 (normal); complement byte 0x81 |
| Entry word | `0xEA00002E` → stock branch to 0x080000C0 |
| MD5 | `8ee261b598c4c1189dfaaa3361697c5f` |
| SHA-1 | `338e4ed81071fa6c55ca7ca3bbbdf84bc3ba8855` |
| SHA-256 | `4cd9ad352ead5b83473ff9fa9c9515da38923c0ea3d31fd60f7723a818327514` |
| CRC32 (mGBA/gamehacking.org) | `F6124D7F` (matches the `f6124d7f` word in the mGBA savestate header) |
| Builder | ImaginEngine; published by Infogrames (2002) |

**Phase 0:** `file` reports a GBA ROM; the full-file Nintendo-logo scan found exactly **one** logo, at file offset 0x4 (header 0x0). There is **no embedded second image, no appended trainer, and no patch/cracktro**: the entry word is the stock `0xEA00002E`, not the Mode7/SUNHORS patched variants seen in some releases. The 32 KiB `.sav` is Flash RAM created by mGBA. A scene release named `(U)(Mode7)` exists but this image is not it.

## 2. Executive summary

**There is no password/cheat-code entry system in this game.** No published source lists a GBA password for it; GameFAQs/VGChartz/ChapterCheats list only *save-bit unlockables* and five gameplay hints. The widely circulated "codes" are GameShark / Action Replay / CodeBreaker RAM patches (e.g. `9CEA5335CF51 7E5840BA58E5` "Unlock All Cards", `77A97429 99D7 00807045 790A` "Have All Characters Unlocked") and are explicitly out of scope. All menus were walked on the real ROM; the only text-entry field is **Options → Name Entry**, and it was proven to be a label, not a validator (entering `TRUNKS` unlocked nothing).

The genuine developer-intended feature is a **Flash-save bitfield that unlocks 9 hidden main personalities across 13 selectable slots**. The fresh save has 4 characters (Goku, Gohan, Frieza, Garlic Jr.); the other 9 slots show `?`. A 15-word array at Flash `0x48..0x84` (EWRAM `0x02008F10..0x02008F4C`) holds the state: **9 words gate one character slot each (nonzero = unlocked), 6 words are unrelated**. Each word is a 32-bit counter/flag — any nonzero value works (1, 2, and 0xFFFFFFFF were all tested), i.e. it is not a strict single-bit mask.

The save has a CRC-32 over `sav[0x08..0x34D0)` stored little-endian at `sav+0x34D0`; the table is at ROM `0x0806BC74` and the routine at `0x080332B4`. Editing a save without fixing this CRC makes the game discard it and reinitialise with defaults (observed: a name-only edit without CRC update was rejected and overwritten).

All 9 hidden characters were unlocked **without satisfying any published win condition**, by editing the 15-word array with a correct CRC, then entering the game and selecting an unlocked character (Trunks) through the real UI into the deck-select screen. Bounds were proven: setting *every* flag word to `0xFFFFFFFF` yields exactly 13 characters — no hidden 14th slot — and each word, when set alone, unlocks exactly one slot.

The analysis is independent of *Dragon Ball GT: Transformation* and *Buu's Fury* (queues 249/250). This image is a distinct ImaginEngine script-VM title (hundreds of `SC*`/`On*` script-handler strings at ROM `0x4DAEC..0x4FA1C`); no shared identifier, table, magic, address, or code sequence with those games was found in this ROM. Nothing is shared on the evidence available here.

## 3. How to reproduce

- Emulator: `mgba` (SDL build, `/usr/local/bin/mgba`) under `Xvfb :316`; `SDL_AUDIODRIVER=dummy`. Keymap A=`x`, B=`z`, Start=`Return`, L=`a`, R=`s`, D-pad = arrow keys. Hold ~120–200 ms; menus need a release between presses.
- Boot path with a save present: skip the ~6 splash screens with A presses, **Start** (once on the splash, once on the title), then main menu → Play → 1 Player → New Game → **Choose Character**.
- Menus walked (all on the real ROM, screenshots on disk): title "Press Start"; Main Menu (Play, Deck Building, *Trading Arena* greyed, Options); Play Menu (1 Player, *2 Player* greyed, Tutorial); Player Menu (New Game, *Continue* greyed on a fresh save); Choose Character (7 Heroes + 6 Villains); Options Menu (Name Entry, Music, SFX, Erase Data, Credits); Name Entry (A–Z, 0–9, `@ # $ % & ? ! -` keyboard); Select A Deck; in-match pause was reached by starting a match from an unlocked character. No hidden/debug screen surfaced on any of these.
- Published codes tested: none is an in-game code. The GameShark/Action Replay/CodeBreaker strings above were searched as literals in the ROM and are absent as UI text; they are external RAM patches, not developer-intended cheats.
- Save-edit reproduction (analysis technique, not a cheat code): copy the ROM and its `.sav` to a scratch dir; patch bytes; recompute the CRC over `sav[0x08:0x34D0)` with the table at `0x0806BC74`; write it to `sav+0x34D0`; boot. To unlock all 9, set 15 bytes at `sav+0x48` (actually the low byte of each of the 15 32-bit words) to `0x01`.

## 4. Address map

| Item | ROM / Flash address | RAM address | Notes |
|---|---|---|---|
| Header title / code | 0x0000A0 / 0x0000AC | — | `DBZCARDGAME1` / `ADZE` |
| Script-handler name bank | 0x0804DAEC–0x0804FA1C | — | `On*`, `SC*` names (debug leftovers, not a menu) |
| `DBZInit` magic literal | 0x08055860 | — | checked by validator at 0x08031F98 |
| Version strings | 0x08050A04 / 0x08050A1C | — | `DBZ1.0`, `DBZ-CCG-GBA-1` |
| Menu strings | 0x08050C4C / 0x08050C58 / 0x08050CC4 | — | `Main Menu`, `Continue`, `undefined` |
| New-save initialiser | 0x0800277C | — | memsets 0x34C8 bytes, writes signature `0xBEEFFEEB`, zeroes 15 words at struct+0x40 |
| Save validation / load | 0x08002880 | — | compares computed CRC with stored CRC; on mismatch calls 0x0800277C |
| CRC-32 routine | 0x080332B4 | — | `crc=0xFFFFFFFF; crc=(crc>>8)^table[(crc^byte)&0xFF]` |
| CRC-32 table (256×u32) | 0x0806BC74 | — | standard reflected CRC-32 table |
| Save struct base | Flash `0x08` | EWRAM `0x02008ED0` | length `0x34C8` |
| Player name | Flash `0x0C` | EWRAM `0x02008ED4` | 8-byte label, no validator |
| Unlock/status word array (15×u32) | Flash `0x48..0x84` | EWRAM `0x02008F10..0x02008F4C` | 9 character gates + 6 other fields |
| Save CRC | Flash `0x34D0` | EWRAM `0x0200C398` | u32 LE, result of 0x080332B4 over Flash `0x08..0x34D0` |

Savestate RAM mapping (mGBA `.ss1` = PNG with zlib `gbAs` chunk): IWRAM at state `0x19000`, EWRAM at state `0x21000`. Flash `0x08`↔state `0x29ED0`. This was verified by patching state `0x29ED0` and reading back `0x12345678` at EWRAM `0x02008ED0` in mGBA's CLI debugger (the GDB stub on port 2345 was occupied by a sibling session; `-d` on a PTY was used instead).

## 5. Algorithm

Save validation (`0x08002880`), derived from Thumb disassembly:

```
read 0x34C8 bytes from Flash offset 0x00 into save_struct @ EWRAM 0x02008ED0
computed = crc32_table(data = save_struct[0x00 : 0x34C8])   # routine 0x080332B4
stored   = u32_le(Flash[0x34C8])                            # = sav+0x34D0
if computed == stored: valid; else: new_save()              # 0x0800277C
```

CRC is the standard reflected CRC-32 with initial `0xFFFFFFFF`, **no final complement**, table at `0x0806BC74`. For the shipped save, `CRC(Flash[0x08:0x34D0]) == 0xC09FAFCB`, which is stored at `Flash+0x34D0`.

Unlock gate (derived from 15 single-word boot experiments + screenshots):

```
for each of 15 words w[i] at Flash 0x48 + 4*i:
    char_slot unlock = (w[i] != 0)      # any nonzero value; not bit-specific
```

## 6. Tables

**Slot and flag map.** Initial save has the four base characters; the other nine are gated by words below. Visual identification is from the zoomed portraits, cross-checked with the GameFAQs unlock table.

| Flash offset | Word | Slot | Character | Published unlock condition (GameFAQs) |
|---|---:|---|---|---|
| — | — | Hero 1 | Goku | base |
| — | — | Hero 2 | Gohan | base |
| 0x78 | 12 | Hero 3 | **Krillin** | Beat Cell with Guldo |
| 0x54 | 3 | Hero 4 | **Trunks** | Beat Cell with Gohan |
| 0x68 | 8 | Hero 5 | **Piccolo (Hero)** | Beat Cell with Garlic Jr. |
| 0x58 | 4 | Hero 6 | **Nail** | Beat Cell with Goku |
| 0x7C | 13 | Hero 7 | **Vegeta (Hero)** | Beat Cell with King Cold |
| — | — | Villain 1 | Garlic Jr. | base |
| — | — | Villain 2 | Frieza | base |
| 0x74 | 11 | Villain 3 | **Guldo** | Beat Cell with Nail |
| 0x64 | 7 | Villain 4 | **King Cold** | Beat Cell with Frieza |
| 0x5C | 5 | Villain 5 | **Piccolo (Villain)** | Beat Cell with Garlic Jr. |
| 0x80 | 14 | Villain 6 | **Vegeta (Villain)** | Beat Cell with King Cold |
| 0x48, 0x4C, 0x50, 0x60, 0x6C, 0x70 | 0,1,2,6,9,10 | — | no character effect observed | unrelated save fields |

The two Piccolo gates and the two Vegeta gates are separate words even though one published condition unlocks both forms; the game's setter presumably writes both. Two other "cheats" in circulation (`Frieza Smiles card` on VGChartz) are just a mislabelled restatement of the King Cold → Vegeta unlock.

**Published codes verified against the ROM.** No in-game password string exists. Searched literals: `DBZ1.0` (0x08050A04), `DBZ-CCG-GBA-1` (0x08050A1C), `Main Menu`, `Continue`, `undefined`, `DBZInit`, `Yes`, `No`. GameShark/AR/CB code literals are not present as text. The "Have All Cards (1328)" claim matches a 1328-card collection structure in the save around Flash `0x20..0x1480`, but the patch itself is an external RAM cheat, out of scope.

**Text/button-space search counts.** `strings -t x -n 4` produced 92,247 lines. Keyword hits for `password|cheat|secret|code|unlock|debug|hidden|bonus|tournament` were overwhelmingly card names/descriptions; the only out-of-place hits were script-handler names (`OnAICombatEnterDefendUI`, `SCAISelectRemoteAllyToDiscard`, `SCCardHookNNN`, etc.) at `0x804DAEC..0x804FA1C` and the UI strings `Main Menu`, `Continue`, `undefined`, `DBZ1.0`, `DBZ-CCG-GBA-1`. There is **no ASCII password alphabet, no accepted-code table, no button-mask sequence and no key-comparison string** anywhere in the image. On the title screen, 20 consecutive A presses and multiple Start presses produced no state change beyond normal navigation, so no title button code was found.

## 6b. Enumeration

**Space definition.** The unlock array is 15 32-bit words = 60 bytes = 480 bits of save state. Nine words (offsets 0x54, 0x58, 0x5C, 0x64, 0x68, 0x74, 0x78, 0x7C, 0x80) are *character gates*; each is a nonzero/counter field, so the *behavioural* space is 2^9 = **512 reachable character-unlock combinations** (the other six words do not affect the select screen). There are exactly 13 selectable slots (7 Heroes + 6 Villains), 4 base and 9 gated — no 14th hidden character exists in this build.

**Novel state, not in any published list.** A save was crafted with all nine gates nonzero (and CRC repaired) without beating Cell or satisfying any published condition. On a fresh boot the Choose Character screen showed **all 13 portraits** (`sav_48wide.png`; baseline `sav_base6.png` had only 4). Selecting the previously locked Trunks (Hero slot 4) with the real UI advanced to the **Select A Deck** screen (`sel_trunks.png`), proving the unlocked character is playable, not merely drawn. An even narrower novel state — **Guldo alone** (word 11 at Flash `0x74` = 1) — unlocked only Villain slot 3 (`map_11.png`), a configuration no published guide describes. Neither state comes from any GameFAQs/VGChartz/ChapterCheats list.

**Bounds proven by rejection.**
- Each of the 15 words was set to `1` alone on a fresh, CRC-correct save and the screen captured (`map_00..map_14.png`): exactly 9 words changed exactly one slot each; the other 6 changed nothing.
- Every flag word set to `0xFFFFFFFF` produced exactly 13 characters — no extra slot, no different portraits (`test_48wide.png`) — bounding the space at 9 gates / 13 slots.
- Word 3 set to `0x02` still unlocked Trunks (`sav_bit1.png`): the gate is "nonzero", not a single fixed bit; bit 1 is not a separate hidden character.
- Name Entry set to `TRUNKS` with a valid CRC unlocked nothing (`sav_namecode.png`): the name field is a label, not a password validator.
- A save edited **without** repairing the CRC was rejected: the game reinitialised it to `DBZInit / Player 1` (verified by re-reading the `.sav` and by the name in a savestate remaining `Player 1`). This proves the CRC gate.
- The greyed *Trading Arena* and *2 Player* entries remained greyed with all 15 words set to 1 (`menu_all1.png` vs `menu_orig.png`, pixel-identical): those are gated by something other than this array and are not unlockable through it.

## 7. Validation evidence

- **Observed (emulator):** all menu screens listed in §3; baseline 4-character vs 13-character select screens; single-word unlock screenshots; Trunks playable into deck select; name-entry non-effect; greyed-menu non-effect; save rejection on bad CRC.
- **Derived (disassembly):** CRC routine/table and validation call path; 15-word zeroing in the new-save initialiser; Flash `0x08` struct base and `0x34D0` CRC location; `DBZInit` validator at 0x08031F98. All literal-pool values were re-read with `struct.unpack_from` before use (avoiding objdump's split-halfword trap).
- **Inferred:** the in-game *setters* of the nine gates are not individually isolated (no direct literal references to the gate addresses; code addresses them via a base pointer). The published win conditions were taken from GameFAQs/ChapterCheats/VGChartz and were not replayed through a full ladder run; the ROM-side proof is that the nine gates are exactly the nine hidden slots and that setting them produces the documented characters. The association of a given published condition with a given word is by character identity from the published table, not by tracing a Cell-victory branch.

## 8. Unknowns

- Exact semantics of the six non-character words (Flash 0x48, 0x4C, 0x50, 0x60, 0x6C, 0x70); likely ladder/"defeated" counters, but no observable in-game effect was found in the screens tested.
- Whether the nine gates are ever written as values >1 by normal play (they accept any nonzero value).
- The gate that enables *Trading Arena* and *2 Player* was not identified; confirmed not to be this 15-word array.
- Full match/pause screens were entered only far enough to confirm character selection and a live match; exhaustive in-match menu enumeration was not performed (no code surface was advertised there).
- No hidden debug menu surfaced; the `SC*`/`On*` strings appear to be script-VM handler names retained in the build, not a reachable menu.

## 9. Tooling

- `strings -t x -n 4` (92,247 lines), `grep -abo`, `xxd`.
- Python + Capstone literal/BL scanners (`scan.py`), `arm-none-eabi-objdump -M force-thumb` for all disassembly.
- mGBA CLI debugger on a PTY (`dbgpty.py`, `oracle.py`) for RAM reads/writes: the GDB stub on port 2345 was held by a sibling session, so `-d` was used; GDB RSP client (`gdbclient.py`) was written but unusable for that reason.
- mGBA savestate parser (`ss.py`): PNG `gbAs` chunk → zlib → 397,312-byte state; EWRAM at state `0x21000`, IWRAM at `0x19000`. State patcher (`patchss.py`, `patch_zeros.py`).
- Save editor (`savpatch.py`) implementing the recovered CRC, plus boot-and-screenshot harness (`savtest.py`, `map_flags.py`) and automated slot-difference detector (`analyze_slots.py`).
- Screenshots kept in `/tmp/dbzccg/` (`sav_base6.png`, `sav_48wide.png`, `map_00..map_14.png`, `sel_trunks.png`, `sav_bit1.png`, `sav_namecode.png`, `menu_*`); none contain redistributable game assets in this report.

**Legal note:** no ROM or copyrighted assets are redistributed here; only hashes, addresses, algorithms, and addresses/offsets are published.
