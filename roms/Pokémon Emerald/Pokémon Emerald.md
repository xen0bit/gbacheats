# Pokémon Emerald (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Pokémon Emerald.gba` (same folder as this report) |
| Size | 16,777,216 bytes (`0x01000000`, 16 MiB) |
| Header title / code / maker | `POKEMON EMER` / `BPEE` / `01` (Nintendo), version `0x00` ("Rev.00") |
| Entry branch | `0xEA00007F` (`b 0x204`, stock crt0) |
| Header bytes | fixed `0x96` at `0xB2`; complement byte `0x72`; header checksum `0x0000` (normal for retail Emerald) |
| MD5 | `605b89b67018abcea91e693a4dd25be3` |
| SHA-1 | `f3ae088181bf583e55daf962a92bb46f4f1d07b7` |
| SHA-256 | `a9dec84dfe7f62ab2220bafaef7479da0929d066ece16a6885f6226db19085af` |

This MD5 is the canonical North-American/European Emerald good dump. **No patch or trainer**: the first 4 KiB is stock ARM crt0; no scene cracktro, no appended trainer menu.

Embedded GBA headers: a Nintendo-logo scan (156-byte logo `24 ff ae 51 …`) found **three** hits — `0x0` (the real header) and `0x009A6550` / `0x00AA144` (stub headers with game codes `AGBJ` and `TEST`, empty titles, entries `0xEA00003E` / `0xEA00002E`). These are the retail multiboot/link stubs shipped inside Emerald, not injected patches.

Text is **not ASCII**: the game charset is space=`0x00`, `A`–`Z`=`0xBB`–`0xD4`, `a`–`z`=`0xD5`–`0xEE`, `0`–`9`=`0xEF`–`0xF8`. All text-bank searches below decode with this map (tool `g3text.py`).

## 2. Executive summary

**There is exactly one in-game, developer-intended code-entry surface in retail Emerald: the "questionnaire" Easy Chat phrase system.** At a questionnaire terminal (metatile behaviour `MB_QUESTIONNAIRE`, shop tileset metatile 288 — the terminal found in/near Poké Marts/Pokémon Centres), the player composes a four-word Easy Chat phrase. The ROM contains a single accepted phrase, **`LINK TOGETHER WITH ALL`** (`u16` word IDs `0x0209 0x140B 0x1030 0x102A`, literal table at `0x080597764`, file offset `0x597764`). Entering it sets `VAR_0x8004 = 2`, which makes the NPC set `FLAG_SYS_MYSTERY_GIFT_ENABLE` and unlock the Mystery Gift system. Any other phrase yields `VAR_0x8004 = 0` ("Thank you for taking the time to fill out our questionnaire") — a bounded, provable rejection.

All other leads are negatives, with concrete gates:

* **No debug menu in the retail build.** The 8-page, `R`+`Start` debug menu documented by 3rd party cheat indexes are from the **2020 leaked prototype**, not this ROM. Retail English Emerald contains zero encoded or ASCII occurrences of `DEBUG`, `DEBUG MENU`, `WARP`, `SOUND CHECK`, `FLAGS`, `VARS`; the pokeemerald project states it "reproduces the commercial release … so there's no debug functionality at all." Pressing `R`+`Start` in-game opens only the normal pause menu (observed). a 3rd party cheat index's "patch `0x301AC` → `21 83 0E 08`" Sound Check trick is **Japanese-only** and requires patching the ROM — it is not an in-game action.
* **Main-menu Mystery Gift / Mystery Events entries are present as strings but unreachable.** The strings exist at `0x5E8295`/`0x5E82AF`, but the decomp documents that `Task_MainMenuCheckSaveFile` in this build never selects `HAS_MYSTERY_EVENTS`, and `IsMysteryGiftEnabled()` is false on a fresh save. Observed with a valid save: the main menu has exactly `CONTINUE / NEW GAME / OPTION` (3 entries).
* **The "Poke debug flag at `0x020370C0`" lore is a misidentification.** `0x020370C0` is `VAR_0x8004` (`gSpecialVar_0x8004`), an ordinary script temporary variable; live RAM reads show `0x00000000` at the title and `0x03FF` (the "no value" sentinel) during play. There are zero literal references to the absolute address in the ROM because script vars are accessed through a pointer table. It is not a debug gate.
* **No GameShark/CodeBreaker/memory-edit codes are in scope**; the many published codes are external cheat-device values.

## 3. How to reproduce

Emulator: mGBA under `Xvfb :318`, `SDL_AUDIODRIVER=dummy`, window focused with `xdotool windowfocus`. Keymap (mGBA SDL default): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows. Hold keys 100–300 ms.

Menu walk (all observed, screenshots on disk in `/tmp/emerald/`):

1. Boot → title. With no save: `NEW GAME`, `OPTION` (`title.png`). With the in-game save: `CONTINUE`, `NEW GAME`, `OPTION` (`title_saved2.png`) — **no Mystery Gift/Events entries**.
2. `OPTION` → `TEXT SPEED / BATTLE SCENE / BATTLE STYLE / SOUND / BUTTON MODE / FRAME / CANCEL` (7 entries; `opt5.png`).
3. `NEW GAME` → Birch intro → player's house → overworld.
4. Start → pause menu `BAG / AAAAAAAA / SAVE / OPTION / EXIT` (5 entries; `pause1.png`).
5. `BAG` → 5 item pockets + `CLOSE BAG`; player entry → Trainer Card (`bag.png`, `player.png`).
6. Hold `R` and tap `Start` in the overworld → normal pause menu, **no debug menu** (`rstart.png`, `rstart2.png`).
7. `SAVE` writes a 128 KiB Flash save (`Pokémon Emerald.sav`).

To reach the questionnaire in a long game: obtain the Pokédex, go to a Poké Mart/Pokémon Centre with the questionnaire terminal, interact, answer "Yes" to "There is a questionnaire. Would you like to fill it out?", then in the 2×2 Easy Chat screen select the words **LINK / TOGETHER / WITH / ALL** and confirm "Yes". `FLAG_SYS_MYSTERY_GIFT_ENABLE` is then set and "Once you save your game, you can access the MYSTERY GIFT."

## 4. Address map

| Item | Address | Notes |
|---|---|---|
| ROM base | `0x08000000` | file offset + `0x08000000` |
| Phrase literal table | `0x080597764` (file `0x597764`) | 4×`u16` = `09 02 0B 14 30 10 2A 10`; sole occurrence in 16 MiB |
| Questionnaire text bank | `0x273100`–`0x273700` (file) | "There is a questionnaire…", "You know those words…", "You can access the MYSTERY GIFT/EVENT" |
| Mystery Gift word list | `0x59A000`–`0x59C800` (file) | decoded Easy Chat words incl. `TOGETHER` at `0x59AB6F`, `EXCITING` at `0x59C434` |
| Main-menu strings | `0x5E827C` (file) | `NEW GAME@0x5E827C`, `CONTINUE@0x5E8285`, `OPTION@0x5E828E`, `MYSTERY GIFT@0x5E8295`, `MYSTERY GIFT@0x5E82A2`, `MYSTERY EVENTS@0x5E82AF` |
| `VAR_0x8004` / `gSpecialVar_0x8004` | RAM `0x020370C0` | script temp; **not** a debug flag |
| EWRAM in mGBA savestate | state raw offset `0x21000` | `RAM addr = 0x02000000 + (state_off - 0x21000)`; IWRAM at `0x19000` |
| Embedded multiboot headers | `0x009A6550` (`AGBJ`), `0x00AA144` (`TEST`) | retail link stubs |

Decomp map (matching `pret/pokeemerald`, used as a reading aid, verified against ROM bytes): `data/scripts/questionnaire.inc`, `src/easy_chat.c` (`sMysteryGiftPhrase`, `SetSpecialEasyChatResult`, `DidPlayerInputMysteryGiftPhrase`), `include/constants/easy_chat.h` (`EC_MASK_BITS = 9`), `src/metatile_behavior.c` (`MB_QUESTIONNAIRE = 0x8F`), `src/main_menu.c`.

## 5. Algorithm

```
# Word IDs: (group << 9) | index
LINK     = (EC_GROUP_TRAINER     << 9) | 9   = 0x0209
TOGETHER = (EC_GROUP_CONDITIONS  << 9) | 11  = 0x140B
WITH     = (EC_GROUP_ENDINGS     << 9) | 48  = 0x1030
ALL      = (EC_GROUP_ENDINGS     << 9) | 42  = 0x102A

# ROM table at 0x080597764 (the only such table in the image)
accepted = [0x0209, 0x140B, 0x1030, 0x102A]

# Validator, called when the player confirms a 4-word Easy Chat phrase
def SetSpecialEasyChatResult(screen_type, current_phrase):
    if screen_type == 20:                      # EASY_CHAT_TYPE_QUESTIONNAIRE
        if list(current_phrase) == accepted:    # IsPhraseDifferentThanPlayerInput == 0
            VAR_0x8004 = 2                      # -> Mystery Gift unlock
        else:
            VAR_0x8004 = 0
    # other screen types set other vars; none set 1 in this build

# Caller (data/scripts/questionnaire.inc)
if VAR_0x8004 == 2: set FLAG_SYS_MYSTERY_GIFT_ENABLE   # "You know those words…"
if VAR_0x8004 == 1: set FLAG_SYS_MYSTERY_EVENT_ENABLE  # DEAD: no producer of 1 in this build
else:               "Thank you for taking the time…"
```
Gates before the flag is set: `FLAG_SYS_POKEDEX_GET` must be set, and the corresponding enable flag must not already be set.

## 6. Tables

| Term | Encoded form / value | Count in ROM (decoded text bank) |
|---|---|---|
| `PASSWORD` | `50 41 53 53 57 4F 52 44` (game charset) | **0** |
| `CHEAT` | game charset | **0** |
| `DEBUG` / `DEBUG MENU` | ASCII and game charset | **0** |
| `WARP` / `SOUND CHECK` / `FLAGS` / `VARS` | game charset | **0** |
| `CODE` | game charset | 1 — `SECRET CODE` at file `0x26D751`, part of the Trick House "Mechadoll" quiz where the game writes a code onto a door (event-generated, not player-entered) |
| `MYSTERY GIFT` / `MYSTERY EVENTS` | game charset | present (`0x5E8295`, `0x5E82AF`) but unreachable as main-menu entries |

Menu-entry counts (all reachable screens walked): title 2 (no save) / 3 (with save); Options 7; pause 5; Bag 5 pockets + close; Trainer Card: 0 selectable cheats.

## 6b. Enumeration

* **Space definition.** The questionnaire is a 4-slot Easy Chat phrase, each slot chosen from the Easy Chat word groups unlocked to the player. There is **no checksum and no field encoding** — it is a direct literal comparison against one hard-coded 4-word array.
* **Complete accepted set.** Exactly one phrase: `LINK TOGETHER WITH ALL` → `VAR_0x8004 = 2` → `FLAG_SYS_MYSTERY_GIFT_ENABLE`. The ROM contains exactly one 8-byte literal with these four word IDs (verified by full 16 MiB scan; only a shift of 9 bits reproduces it, confirming `EC_MASK_BITS = 9`). There is no generator because the space has a single member — the enumeration is therefore complete by construction.
* **Novel/unpublished code.** Not applicable: there is no space of hidden codes to mint. The published 3rd party cheat indexes phrase `MYSTERY EVENT IS EXCITING` encodes to word IDs `{0x143A, 0x1817, 0x100B, 0x200F}`, which do **not** occur anywhere in this ROM — that hint belongs to another edition. The result-1 branch (`FLAG_SYS_MYSTERY_EVENT_ENABLE`) has no accepting phrase in this build and is dead code.
* **Bounds proven by rejection.** Any phrase other than the literal returns `VAR_0x8004 = 0`; the NPC then gives only "Thank you for taking the time to fill out our questionnaire" and sets no flag (decomp `SetSpecialEasyChatResult` + `data/scripts/questionnaire.inc`; the negative is bounded by the single literal table). The `VAR_0x8004 == 1` branch cannot fire: no code path in this build writes 1.
* **Debug-menu bounds.** `R`+`Start`, title-screen key combos, and all visible menu entries were exercised; no hidden screen appeared. The prototype's trigger and labels are absent from the retail text banks (counts above), and the Japanese-only Sound Check needs a ROM patch at `0x301AC`, so the retail-debug-menu space is empty.

## 7. Validation evidence

* **Observed** (emulator, :318): title menus (2 and 3 entries), Options (7), pause (5), Bag, Trainer Card, `R`+`Start` → normal pause menu only, save-file creation, decoded text banks, literal table bytes.
* **Observed** (RAM via mGBA `.ss1` `gbAs` chunk): `VAR_0x8004 @ 0x020370C0` = `0x00000000` at the title and `0x03FF` during play; player-name pattern at EWRAM `0x02024A6C`.
* **Derived**: phrase→word-ID encoding, the validator algorithm, result-1 dead branch, main-menu `HAS_MYSTERY_EVENTS` gate, `0x020370C0 = VAR_0x8004`, and the embedded headers being retail link stubs — each from matching decomp source cross-checked against ROM bytes/addresses.
* **Inferred**: that the questionnaire terminal is reached in a Poké Mart/Pokémon Centre (metatile 288 of the `shop` tileset); the scripted story gate prevented reaching the terminal in the fresh 0-badge save used for the menu walk, so the phrase was validated against the ROM's own literal table and validator logic rather than typed on the terminal. This is the one step labelled Derived rather than Observed.
* Web content (3rd party cheat indexes, pokeemerald wiki) was treated strictly as data; no instruction found in fetched pages or ROM strings was followed. One 3rd party cheat indexes fetch returned HTTP 403; the archived copy was used instead.

## 8. Unknowns

* The exact in-game location/warp of the questionnaire terminal was inferred from decomp metatile data, not reached in the emulator during this session; a full playthrough to Pokédex + Poké Mart is needed for an on-screen screenshot of the phrase acceptance.
* `IsMysteryGiftEnabled()` may require a save flag set by an in-game distribution event; on the fresh save it was false, so the `HAS_MYSTERY_GIFT` menu state was not exercised.
* The "Mechadoll / TRICK MASTER" secret-code quiz (`0x26D700`) was decoded but its generated code is consumed by an event script, not a player keypad; no code-entry surface was found for it.

## 9. Tooling

`strings -t x`, `grep -abo`, `xxd`, `arm-none-eabi-objdump -M force-thumb`, Capstone 5.0.7 (`pip install --break-system-packages capstone`), Python stdlib, `curl`/`web.archive.org`, `pret/pokeemerald` matching decomp (source only, as a reference map), mGBA under `Xvfb :318` + `openbox`, `xdotool`, `scrot`, ImageMagick `convert`.

Scripts written in `/tmp/emerald/`: `g3text.py` (charset codec), `dbgserver.py`/`dbgclient.py`/`ram.py` (mGBA `-d` RAM bridge), `ui.sh` (input helper). Savestate RAM extraction used a Python PNG-chunk parser that `zlib.decompress`es the `gbAs` chunk (raw 397,312 bytes; EWRAM at `0x21000`, IWRAM at `0x19000`).

No ROM or copyrighted assets are redistributed here; only addresses, hashes, word IDs, and algorithm descriptions are published.
