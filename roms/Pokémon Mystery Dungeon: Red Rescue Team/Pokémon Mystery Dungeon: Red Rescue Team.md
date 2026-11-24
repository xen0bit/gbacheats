# Pokémon Mystery Dungeon: Red Rescue Team (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Pokémon Mystery Dungeon: Red Rescue Team.gba` |
| Size | 33,554,432 bytes (0x02000000, 32 MiB / 256 Mbit) |
| Header title | `POKE DUNGEON` |
| Game code / maker | `B24E` / `01` (Nintendo), `file` reports `(B24E01, Rev.00)` |
| Version / fixed / main unit | 0x00 / 0x96 / 0x00 |
| Entry word | `0xEA00002E` (stock ARM branch — **not** a scene cracktro patch, §16.1) |
| Header checksum / complement | `0x0000` / `0xA4` (logo checksum not recomputed in this dump; no patch evidence — the SHA-1 matches the official `pret/pmd-red` decomp target byte-for-byte) |
| MD5 | `2100cf6f17e12cd34f1513647dfa506b` |
| SHA-1 | `9f4cfc5b5f4859d17169a485462e977c7aac2b89` |
| SHA-256 | `ad316814c77ed083734d816ebcde2ece390efae8d15bcb6c66d7c2862d82eb68` |

**Embedded-header scan:** exactly one Nintendo logo, at file `0x4` (ROM `0x08000004`). No multiboot stub, no concatenated second image, no appended trainer. This is the retail USA revision 0 image.

**Ground-truth source:** `pret/pmd-red` (git clone, master) builds a GBA ROM with SHA-1 identical to the target. Every function address below is a GBA address from that decomp, independently verified against the raw ROM by PC-relative literal loads, BL target scans, and `arm-none-eabi-objdump -M force-thumb`.

## 2. Executive summary

This game has a **developer-intended, fully algorithmic password system** — *Wonder Mail* — plus two related mail-password systems (SOS/AOK/Thank-You Mail) and a **dead/ungated-in-retail Debug Mode** whose strings and handlers are present but whose menu entry has no controller-reachable path.

Wonder Mail is not a lookup table: it is a 24-symbol base-32 code with a positional checksum and a 93-bit packed mission payload. The ROM contains the alphabet table, a 24-entry permutation, the pack/unpack routines, the checksum loop, the field reader/writer, and a semantic validator. I reimplemented the whole path in Python, cross-checked it against 5 clean published codes, minted a code absent from every published list, entered it on the real Wonder Mail screen in mGBA, and proved its effect in the saved RAM bit-pattern. Bounds were proven by rejection at both validator layers.

A second code surface (54-symbol SOS/AOK/Thank-You Mail codes, 270-bit alphabet space) was recovered from the same routines; it is gated behind an in-game faint/rescue flow, so it is documented structurally rather than entered.

The Debug Menu ("Dungeons / Field / Field Map / Field Script / Debug Menu / Storage / h-open") is **not reachable by any in-game input** in this retail build: the menu-action enum and handlers exist, but no reachable menu table emits `MENU_DEBUG`. Published methods to reach it use a GameShark device and are out of scope.

No GameShark/CodeBreaker/memory-edit codes are reported as cheats.

## 3. How to reproduce

- **Emulator:** mGBA (SDL), `DISPLAY=:315`, `SDL_AUDIODRIVER=dummy`, `Xvfb :315 -screen 0 1024x768x24`, `openbox`, `mgba -3 <rom>`.
- **Keymap (mGBA SDL default):** A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad = arrow keys. Holds of 70–150 ms; 10 ms taps are missed.
- **Reach the screen:** the Wonder Mail entry is only shown once a save exists. Create one by starting a new game and using `Start → Other → Quicksave or Give Up → Quicksave → Yes`, then reset. Main menu then reads: Continue / Delete Save Data / Adventure Log / Friend Rescue / Trade Items / **Wonder Mail**. Select Wonder Mail → confirm the instruction text → the 24-slot password keypad appears with the cursor on `N`.
- **Entering symbols:** the keypad is driven from the game's own `sLayoutInfo[0][85]` adjacency graph (`decomp/src/naming_screen.c:181`). Each entry is `{up, down, left, right, x, y, colorType, letter}`; BFS from the initial position 9 produces a D-pad path to each target symbol, then A inserts it. `Start` jumps to the `END` key; A confirms.
- **Codes used in this report:**
  - Published anchor (3rd party cheat indexes): `F ? 4 N + W T ? ? + 6 N F R ? J F ? 6 6 8 5 ? W` — accepted, "Received the Wonder Mail!".
  - **Novel (not in any published list):** `F ? C N + W F ? ? + 6 N F R ? J F ? 6 6 8 5 ? W` — accepted; changes the reward from `rewardType=0` (MONEY, 77 Poke) to `rewardType=3` (ITEM_EXTRA, item 77 = MAX_ELIXIR), all other fields identical.
  - Bounds A (bad checksum): same as novel but last symbol `W`→`6` — rejected, "This password is incorrect. Would you like to enter it again?".
  - Bounds B (valid checksum, semantic out-of-range): `F ? H N + W 0 ? ? + 6 N F R ? J F ? 6 6 8 5 ? W` — `rewardType=4` (BLANK_4); checksum valid but rejected by `IsValidWonderMail`.
- **Screenshots:** `shot37.png` (empty keypad), `shot38.png` (published accepted), `shot45.png` (novel accepted), `shot62.png` / `shot63.png` (both rejections), `shot34.png` (main menu). Kept on disk in `/tmp/pmdred/`; not redistributed.

## 4. Address map

All addresses are ROM (`0x08xxxxxx`) unless stated. File offset = ROM address − `0x08000000`.

| Address | Size | Meaning |
|---|---|---|
| `0x0803D0D8` | fn | Wonder Mail enable flag getter (`sub_803D0D8`); returns EWRAM `u8 sUnknown_203B408`, initialised 1 — Wonder Mail is enabled by default |
| `0x0803D0F0` | fn | sprite/char byte → 5-bit symbol value (`sub_803D0F0`), indexes `0x080F42F0` |
| `0x0803D100` | fn | 5-bit symbol value → char byte (`sub_803D100`), indexes `0x080F42D0` |
| `0x0803D110` | fn | pack 24 symbols → 15 bytes; returns 0 on any invalid char (`sub_803D110`) |
| `0x0803D1A8` | fn | unpack 15 bytes → 24 symbols (`sub_803D1A8`) |
| `0x0803D204` | fn | SOS/AOK Mail decode (54 symbols → 34 bytes → 260-bit struct) |
| `0x0803D2C0` | fn | SOS/AOK Mail encode |
| `0x0803D358` | fn | **`DecodeWonderMailPassword`** — verified prologue at `0x0803D358`, permutation loop `0x0803D382`–`0x0803D3AC`, literal `0x0803D3FC → 0x080F4426`, BL to `0x0803D110` at `0x0803D3B4`, checksum loop from `0x0803D3BE` |
| `0x0803D414` | fn | Wonder Mail encode (`sub_803D414`) — BL to `0x0803D1A8` at `0x0803D472` |
| `0x080F42D0` | 32 B | value → char byte alphabet |
| `0x080F42F0` | 256 B | char byte → value table (`0xFF` = invalid) |
| `0x080F43F0` | 54 B | SOS/AOK 54-position permutation |
| `0x080F4426` | 26 B | Wonder Mail 24-position permutation (last 2 bytes `0x00` padding) |
| `0x080954F4` | fn | `ReadWonderMailBits` (93-bit field reader; decomp `// arm9.bin::020662A0`) |
| `0x08095438` | fn | `WriteWonderMailBits` (93-bit field writer) |
| `0x080958E8` | fn | `IsValidWonderMail` / `ValidateWonderMail` semantic range checks (decomp `code_80958E8.c:87,102`) |
| `0x0803B3E8` | RAM | `unkStruct_203B3E8`: `+0x01` `PasswordEntryBuffer[24]`, `+0x14` `decodedMail`, `+0x3C0` accepted `WonderMail` |
| `0x0203B490` | RAM | `gUnknown_203B490`: mail slots (4 mailbox + 8 board + 8 job `WonderMail` records), each **93 bits** in the save |
| `0x0803A3xx` | fn | Debug-menu handler (`CreateDebugMenu` / `UpdateDebugMenu`, decomp `debug_menu1.c`); reachable only via `MENU_DEBUG`, which no retail menu table emits |

The decomp source `src/data/code_803D0D8.h` contains all four tables verbatim; each byte pattern was found exactly once in the ROM at the address above (e.g. the 54-byte `gUnknown_80F43F0` pattern occurs only at file `0xF43F0`).

## 5. Algorithm

### 5.1 Decode (`DecodeWonderMailPassword`, 0x0803D358)

```
input: 24 game-charmap bytes in PasswordEntryBuffer
1. permuted[i] = input[PERM_WM[i]]          for i in 0..23        # 0x0803F4426
2. values[i]   = BYTE_TO_VALUE[permuted[i]]                       # 0x080F42F0
   if any == 0xFF  -> REJECT (invalid character)
3. pack 24 x 5-bit values LSB-first into payload[0..14] (15 bytes)
4. checksum = sum(payload[i] + i for i in 1..14) & 0xFF
   if payload[0] != checksum -> REJECT                            # checksum layer
5. bit-read 12 bytes from payload[1..12] with ReadWonderMailBits  # 93-bit payload
6. call IsValidWonderMail(&decoded) -> range layer; REJECT on false
7. ACCEPT: store WonderMail into mailbox/job list and save
```

`WriteBits`/`ReadBits` (`src/data_serializer.c`) are strictly LSB-first within each byte and advance the byte pointer at bit 8. This matters: the fields are *not* byte-aligned.

### 5.2 Encode (`sub_803D414`, 0x0803D414)

```
payload[1..12] = WriteWonderMailBits(fields)      # 93 bits, remaining 3 bits stay 0
payload[13..14] = 0
payload[0] = sum(payload[i]+i for i in 1..14) & 0xFF
vals[i] = 5-bit chunks of payload (24 of them)
symbols[i] = PERM_WM-inverse applied, then VALUE_TO_BYTE[val]   # 0x080F42D0
```

### 5.3 Field layout (93 bits, LSB-first, in write order)

| Field | Bits | Field | Bits |
|---|---:|---|---:|
| `mailType` | 4 | `rewardType` | 4 |
| `missionType` | 3 | `itemReward` | 8 |
| `unk2` | 4 | `friendAreaReward` | 6 |
| `clientSpecies` | 9 | `seed` | 24 |
| `targetSpecies` | 9 | `dungeonId` | 7 |
| `targetItem` | 8 | `floor` | 7 |

`dungeonId`/`floor` are written by `WriteDungeonLocationBits` (7+7 bits, decomp `src/dungeon_info.c:2526`). Total = 93 bits; 3 padding bits of the 12th data byte are always zero for codes the game generates.

### 5.4 Semantic validator (`ValidateWonderMail`, 0x080958E8)

Observed checks in order: `mailType == 5` (WONDER); `missionType <= 4`; DELIVER_ITEM requires a dungeon that allows items; `unk2 <= 9`; dungeon must be valid and floor `< GetDungeonFloorCount`; client/target species must be non-NONE, `< MONSTER_MAX`, base form, and pass `sub_803C0DC`; item target/reward must not be invalid, thrown, MONEY, or USED_TM; FIND_ITEM requires the item to be findable in that dungeon; `rewardType` not in {4 BLANK_4, 10 END_REWARDS} and `<= 10`; `itemReward` valid item; `friendAreaReward <= FRIEND_AREA_FINAL_ISLAND`; FRIEND_AREA rewards require an unlock condition of `UNLOCK_WONDER_MAIL` plus a compatible dungeon/mission.

### 5.5 SOS/AOK/Thank-You Mail (second system)

`sub_803D204` / `sub_803D2C0`: 54 symbols, same 32-symbol alphabet, permutation `0x080F43F0`, 5-bit packing into 34 bytes (270 bits → 34 bytes), same checksum rule over bytes 1..33, and a 260-bit payload: `mailType:4, dungeonId:7, floor:7, seed:24, clientSpecies:9, unk10:32, playerName:80, item.flags:8, item.quantity:8, item.id:8, unk24:32, unk28:32, rescuesAllowed:8, unk2D:1`. Implemented and round-trip verified (`sosmail.py`). Entry is gated behind an actual faint/rescue, so it was not typed on screen.

## 6. Tables

**Alphabet (value → game char byte), `0x080F42D0`.** Printable forms: `? 6 7 N P R 8 9 F 0 + ♂ S T X Y 4 5 M C H J - K 1 2 ! ♀ 3 … W`. The `♂`, `♀`, and `…` (three-dot ellipsis) are single symbols with charmap bytes `0x85`, `0xBE`, `0xBD` respectively; published FAQ notations `(M)`/`[Male]`/`#`, `(F)`/`[Female]`/`%`, and `(...)` map to these.

**Wonder Mail permutation, `0x080F4426`** (24 entries, `perm[i] = input index`):
`0c 06 13 08 04 0d 0f 09 10 02 14 12 00 15 0b 05 17 03 11 0a 01 0e 16 07`

**SOS permutation, `0x080F43F0`** (54 entries):
`0d 07 19 0f 04 1d 2a 31 08 13 2d 18 0e 1a 1b 29 01 20 21 22 11 33 26 00 35 0a 2b 1f 12 23 2c 17 27 10 1c 30 0b 02 24 09 32 05 28 34 2e 03 1e 0c 25 14 2f 16 06 15`

**`BYTE_TO_VALUE` (`0x080F42F0`)** — non-`0xFF` entries, byte → value:
`0x21→26, 0x2b→10, 0x2d→22, 0x30→9, 0x31→24, 0x32→25, 0x33→28, 0x34→16, 0x35→17, 0x36→1, 0x37→2, 0x38→6, 0x39→7, 0x3f→0, 0x43→19, 0x46→8, 0x48→20, 0x4a→21, 0x4b→23, 0x4d→18, 0x4e→3, 0x50→4, 0x51→29, 0x52→5, 0x53→12, 0x54→13, 0x57→31, 0x58→14, 0x59→15, 0x85→11, 0xbd→30, 0xbe→27`.

**RewardType enum (from `include/structs/str_mission_rewards.h`):** 0 MONEY, 1 MONEY_EXTRA, 2 ITEM, 3 ITEM_EXTRA, 4 BLANK_4, 5 MONEY1, 6 MONEY1_EXTRA, 7 ITEM1, 8 ITEM1_EXTRA, 9 FRIEND_AREA, 10 END_REWARDS. Valid Wonder Mail rewards = all except 4 and 10.

**Published-code verification (offline decoder as oracle, §16.19):** 5 codes verify cleanly — Roselia (`client=340`, Tiny Woods B3F, MONEY 77), Porygon (`client=283`, `target=137`, Thunderwave B5F), Feebas (`client=374`, Thunderwave B4F), Friend Bow, Joy Ribbon. 7 further published strings fail (a `*` stand-in, `[...]`/lowercase notations, inconsistent `M`/`#` symbols, or outright transcription errors — e.g. the Plusle string decodes to `mailType=7` with a bad checksum). These are recorded as **unverified published strings**, not as ROM bugs (§16.7).

## 6b. Enumeration

### Space definition

| Property | Wonder Mail | SOS/AOK Mail |
|---|---|---|
| Alphabet | 32 symbols, 5 bits each | 32 symbols, 5 bits each |
| Length | 24 symbols (120 bits) | 54 symbols (270 bits) |
| Permutation | 24 entries @ `0x080F4426` | 54 entries @ `0x080F43F0` |
| Checksum | 1 byte, `sum(payload[i]+i)`, i=1..14 | 1 byte, same rule, i=1..33 |
| Raw strings | `32^24 = 2^120 ≈ 1.33e36` | `32^54 = 2^270` |
| Checksum-valid strings | `2^112 ≈ 5.19e33` | `2^262` |
| Packed payload | 93 bits (12 bytes, 3 pad bits zero) | 260 bits (33 bytes, 4 pad bits zero) |
| Canonical generated codes | `2^93 ≈ 9.90e27` before semantic checks | `2^260` before game-state checks |
| Stored record size | 93 bits (verified in `.sav`, stride exactly 93 bits) | n/a (SOS record lives in a different save block) |

For any fixed 93-bit payload there are `2^19` checksum-valid spellings, because the 3 ignored pad bits of byte 12 and bytes 13–14 are not read by `ReadWonderMailBits` but do feed the checksum. The game's own encoder always emits the canonical spelling with those bits zero. Semantic validation (`mailType=5`, species/item/dungeon/range checks) reduces the accepted set below `2^93`; the exact post-semantic cardinality requires the game's item, species and dungeon tables and is not claimed here.

### Novel code (absent from every published list)

`F ? C N + W F ? ? + 6 N F R ? J F ? 6 6 8 5 ? W`

Provenance: decoded the published Roselia code, changed **one field** (`rewardType: 0 → 3`, i.e. 77 Poke → MAX_ELIXIR), recomputed the checksum with the ROM-derived encoder, and confirmed the result is not a substring of any 3rd party cheat indexes/MDFW/3rd party cheat indexes/3rd party cheat index list retrieved. All other 11 fields are byte-identical to the published code.

- Decoder check: `checksum stored == computed` (`0x28 == 0x28`), `rewardType=3`, `itemReward=77` (item 77 = MAX_ELIXIR, `gInvalidItemIDs`-clean, not thrown, not MONEY/USED_TM).
- **In-game proof:** typed on the Wonder Mail screen with the keypad driver → `shot45.png` shows **"Received the Wonder Mail!"**, the same acceptance message as the published code.
- **RAM proof:** after the game's save, the 93-bit packed struct for both mails was located in the `.sav` by bit-pattern scan (`savscan.py`):
  - published: bit offset `176124` (byte `22015`), `rewardType=0`, `itemReward=77`
  - novel: bit offset `176217` (byte `22027`), `rewardType=3`, `itemReward=77`
  - the offsets differ by exactly **93 bits** — one `WonderMail` record — proving both were accepted and stored as consecutive mailbox entries, and that the only difference is the intended field.

### Bounds proven by rejection (both emulator, both visible in screenshots)

1. **Checksum layer** — `F ? C N + W F ? ? + 6 N F R ? J F ? 6 6 8 5 ? 6` (last symbol changed, checksum not recomputed): decoder reports `stored 0x08 / computed 0xEA`; emulator: `shot62.png` "This password is incorrect. Would you like to enter it again?" — **REJECTED**.
2. **Semantic layer** — `F ? H N + W 0 ? ? + 6 N F R ? J F ? 6 6 8 5 ? W`: decoder reports a **valid** checksum (`0x28 == 0x28`) but `rewardType=4` (BLANK_4), which `ValidateWonderMail` explicitly forbids; emulator: `shot63.png` the same "incorrect" rejection — **REJECTED**. This isolates the second validator layer from the checksum.

### Button codes / hidden menus

No in-game button code unlocks anything. The Debug Mode handlers and all 7 menu entries (`Dungeons`, `Field`, `Field Map`, `Field Script`, `Debug Menu`, `Storage`, `h-open`, plus an unlabelled action 10) exist in `src/debug_menu1.c` / `src/data/debug_menu1.h`, but `MENU_DEBUG` is only dispatched from `main_menu1.c` when `sMainMenu->nextMenu == MENU_DEBUG`; no reachable `MenuItem` in `SetMainMenuItems()` (`src/main_menu2.c:218`) carries that action. The observed retail main menu has exactly 6 entries and no Debug Mode. Published ways to reach it require a GameShark device (`74000130 03BB …`, Select+Up), i.e. an external memory write — out of scope and not an in-game cheat. This is a **dead/gated feature** (§16.3), closed by call-path analysis plus a full walk of every reachable screen, not by a string absence.

## 7. Validation evidence

- **Observed (emulator):** health warning → title → main menu with/without save; all 6 main-menu entries; Wonder Mail keypad with 24 slots; acceptance of one published and one novel code; rejection of two out-of-bound codes; save-RAM bit patterns for both accepted codes. Screenshots `shot01`–`shot63` on disk.
- **Derived (ROM/decomp):** every table byte pattern found exactly once at its stated address; `DecodeWonderMailPassword` prologue, permutation loop, literal `0x0803D3FC → 0x080F4426`, BL to `0x0803D110`, and checksum loop disassembled and matched to `code_803D0D8.c`; decomp SHA-1 identical to target; keypad adjacency graph taken from `sLayoutInfo` and used successfully to type all codes.
- **Inferred:** field *names* follow the decomp (`unk2` still has no confirmed semantic label — it is probably a difficulty/mission-variant byte); the precise post-semantic accepted-set cardinality; the SOS/AOK system's runtime behaviour (decoder/encoder recovered and round-tripped, but no SOS code was typed because the feature is gated behind an in-game faint).

## 8. Unknowns

- Exact number of codes passing `ValidateWonderMail` after all table lookups (would require enumerating the game's item/species/dungeon/friend-area tables).
- `unk2` semantic meaning (4-bit field, validated to `<= 9`).
- The 7 published strings that fail the checksum are treated as transcription errors; their intended payloads were not reconstructed.
- SOS/AOK/Thank-You Mail codes were decoded/encoded offline but not entered in-game; the rescue-state gate was not advanced.
- The debug menu's in-game screen contents were enumerated from source, not observed in the emulator (no in-game path exists).

## 9. Tooling

- `pret/pmd-red` decomp (cloned to `/tmp/pmdred/decomp`) — exact matching SHA-1.
- `wondermail.py` — full Wonder Mail decoder/encoder (alphabet, permutation, checksum, 93-bit fields); `sosmail.py` — 54-symbol SOS codec; `savscan.py` — bit-level `.sav` record locator; `drive_kb.py` — keypad navigation from the game's own layout graph; `ui.py` / `goto_pw.py` — mGBA input helpers.
- `arm-none-eabi-objdump -M force-thumb`, Python 3 + capstone 5.0.7, `xdotool`, `scrot`, ImageMagick, `gdb-multiarch` (connected once to confirm the `-g` stub halts at reset; not needed for the result).
- All scripts were kept in `/tmp/pmdred/`. No ROM or copyrighted asset is redistributed; only hashes, addresses, algorithms and our own generated codes are published.
