# Shaman King: Master of Spirits (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Shaman King: Master of Spirits.gba` |
| Size | 16,777,216 bytes (`0x01000000`) |
| Header title | `SHAMAN KING` |
| Game code / maker | `BSOE` / `A4` (USA release, `AGB-BSOE-USA`) |
| Version | `0x00` |
| Entry word | `0xEA00002E` — stock branch to `0x080000C0` |
| Nintendo logo hits | 1, at file `0x4` (single image; no multiboot/2-in-1 shell) |
| MD5 | `1c92edbad07a372ee382d16cf624dc4b` |
| SHA-1 | `4a0fecdf90055fe1934b54d10e47b46ac399aecd` |
| SHA-256 | `a5b7419577ac8ad3d7657f95010bfb6a7a312805ae635c7e1650c7d2b3bc64f9` |

Header complement byte `0xB2`; bytes `0xA0..0xBC` sum to `0x35`, and
`0x35 + 0xB2 = 0xE7`, the standard GBA relation. Header checksum `0x0000` is
normal across this collection (verified against 15 other ROMs). No scene
cracktro, trainer, appended image or patched entry point was found: the first
4 KiB is ordinary ARM crt0 and the logo scan found exactly one header.

Save hardware: 32 KiB battery SRAM (mGBA created a 32,768-byte `.sav`).

## 2. Executive summary

**There is no developer-intended cheat-code system in this ROM.** There is no
password screen, no on-screen keyboard/alphabet, no button-code matcher, no
hidden options screen, no debug/scene/warp menu and no sound test. The game's
entire developer-intended extra-content surface is (a) battery-save data with
three slots and two difficulties and (b) ordinary collectible/story
unlockables (Magatama Beads, Tome Pages, Spirit of Fire, Sword of Light,
spirit combos). None of these is entered as a code.

Every reachable menu screen was walked in mGBA with screenshots and full-RAM
savestate dumps. The menu surface is **closed and countable**: a contiguous
8-entry string-pointer table at ROM `0x0826845C` enumerates all DATA-flow
screens, plus 3 standalone strings (overworld menu, YES/NO confirmation, save
confirmation) — **11 screens total**, all observed. The word immediately after
the 8-entry table (`0x0826847C = 0x20503820`) is not a pointer, so no 9th
screen exists in that table.

Web recon found **no published in-game code** for this SKU: GameFAQs lists only
collectible "Unlockables"; Cheat Happens / ROMSFUN / libretro list Action
Replay/CodeBreaker **memory patches** (out of scope and not in-game codes);
GameFAQs's walkthrough documents only pickups and story events. TCRF has pages
for *Master of Spirits 2* and the PS2 *Funbari Spirits* (cheat-device debug
menus) but not for this GBA title — per guide §16.11 those are different SKUs
and their cheats do not apply. Literal searches for any published code string
find nothing, because there are no in-game codes.

The published collectible unlockables are documented in §6 with their ROM text
addresses, but they are progression pickups, not codes. No code was minted
because no code system exists to mint one from (guide §0.2 "no system" branch).
The negative is bounded by counts and exhaustive table walks (§6b).

## 3. How to reproduce

Emulator: mGBA 0.10.5 under `Xvfb :315`, `SDL_AUDIODRIVER=dummy`, 3× scale.
Keymap (mGBA SDL default): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
Select=`BackSpace`, D-pad = arrow keys. Hold keys ~120 ms; focus the window
with `xdotool windowfocus` before each group of inputs.

Menu path (all screens reached):

1. Wait through the "Licensed by Nintendo", Konami/4KIDS intro and title
   (~20 s) → title screen with **Press Start**.
2. **Start** → **DATA** screen: 3 save slots (`NEW GAME` when empty). L/R on
   this screen are decorative; only Up/Down and A act.
3. **A** on an empty slot → **Select difficulty level**: `Normal` / `Hard`.
4. **A** → story intro → **overworld map** (tutorial text, orange level nodes).
5. **Start** → overworld menu: **SAVE / STATUS / SHOP**.
   - SAVE → "Save game data? YES / NO" → YES writes SRAM and returns.
   - STATUS → tabs **ITEM / STATUS / SPIRIT UNITY** cycled with L/R.
   - SHOP → **Buy / Sell**; Buy shows Sushi 150, Hotdog 400, Hamburger 1000,
     Noodles 3000; Sell shows the empty inventory.
6. Reset/reboot after saving → DATA screen now shows a progress bar,
   `NORMAL`, `0%`, play time. **A** on an occupied slot reveals the submenu
   **Continue game / Copy data / Delete data**.
   - Copy data → "Where do you want to copy it to?" → destination slot →
     "Data copied" (or "Ok to overwrite this data?" when the target is used).
   - Delete data → "OK to delete this data?" → "Data deleted".
7. Enter a level from the map, press **Start** during play → the same
   ITEM/STATUS/SPIRIT UNITY screen (the FAQ's "Level menu"; no separate
   in-level option list).
8. Hidden-combo probes on the title and in menus: `L+R+Start`, `L+R+Select`,
   `Select+A+B`, the Konami direction/button sequence, and `A+B+Start+Select`
   (the last is the standard soft reset to the Nintendo license screen). None
   produced a hidden screen.

Screenshots and full-RAM savestates for every step are in
`/tmp/shamanmaster1/` (`s*.png`, `state_*.ss1/.ss2/.ss3`). Helper
scripts: `key.py` (XTEST input), `ss.py` (mGBA `gbAs` savestate decoder),
`scan.py` (static scans). Raw scan output: `scan_out.txt`.

## 4. Address map

File offset = ROM address − `0x08000000` for the first 16 MiB.

| Address | Meaning |
|---|---|
| `0x08000000`..`0x080000BF` | GBA header (stock) |
| `0x080000C0`+ | ARM crt0 / entry |
| `0x0805DE50` | item name `Sword of Light` |
| `0x0805DED4` | item name `Magatama Bead` |
| `0x0805E320` | spirit name `Spirit Of Fire` |
| `0x0805F940`..`0x08060A00` | UI text bank, **plain ASCII** with script control codes `$G`,`$N`,`$R`,`$w`,`$8`,`$9` (decoded in full; see §6) |
| `0x0805F970` / `0x0805F974` | `ON` / `OFF` value-formatting strings (generic menu widget, not an options screen) |
| `0x0805F994` | `  SAVE\n STATUS\n  SHOP` (overworld menu; xref `0x080227A4`) |
| `0x0805F9AC` | `YES\nNO` (xref `0x080228E4`) |
| `0x0805F9B4`..`0x0805FA94` | 8 DATA-flow strings (see table pointer below) |
| `0x080608F4` | `   Save game data?\n...` (save confirmation; xref `0x08038CC8`) |
| `0x0826845C` | **8-entry pointer table** to the DATA-flow strings (file `0x26845C`); next word `0x20503820` is not a pointer |
| `0x0801E5D0` | generic menu *value formatter* (`%s`/`ON`/`OFF`/`%d`/`%0Xh`/`%c`); only 3 BL callers, all in the same widget library `0x0801E6B4`..`0x0801E8A0` |
| `0x08032E20`..`0x08033C80` | DATA-screen state machine; 8 literal pointers to the table above at `0x8032E54`, `0x80332BC`, `0x80333A4`, `0x80336A8`, `0x8033870`, `0x80339FC`, `0x8033C28`, `0x8033C80` |
| `0x02027E8B` (EWRAM) | DATA-screen slot cursor; clamped `0..2` at `0x08032E76`..`0x08032E8E` (`<0 → 2`, `>2 → 0`) |
| `0x02027E8F` (EWRAM) | DATA submenu cursor; same `0..2` clamp at `0x08032EA8`..`0x08032EC0` |
| `0x08032EAE`..`0x08032EB8` | computes `index * 0x5A0` — SRAM save-record stride (observed byte `0x5A0` spacing in the `.sav`) |
| SRAM `+0x70` (u32) | money — read `1000`, matching the on-screen `¥ 1000` |
| SRAM `+0x8A` (u16) | current HP — read `120`, matching `HP 120/120` |
| SRAM `+0x8E` (u16) | current SP — read `80`, matching `SP 80/80` |
| mGBA `.ss1` payload | 397,312-byte zlib `gbAs` chunk; IWRAM at `+0x19000`, EWRAM at `+0x21000` |

RAM-evidence artifacts (SHA-256 of the decompressed 397,312-byte state):

| Screen | state file | full-state SHA-256 | IWRAM/EWRAM hash (first 16 hex) |
|---|---|---|---|
| Overworld menu | `state_owmenu.ss1` | `7e0c38d11d28115bd320ddc5875fc50bf3f94e506ac4cd03edc319b248b98e25` | `428b2f134ce1a80b` / `5e86d9a194753623` |
| Status screen | `state_status.ss1` | `fe5ede13e1ee4fd8f2df95d70d8b97a45bacab7af40c63018c947de51b6b01fd` | `0bbd39563fe29d5f` / `d2b567984a6982b0` |
| In-level status | `state_levelstatus.ss1` | `2802fb8787a091356ae255b13abe7fa76eb6be12e79f3b27ce634a61d4f06836` | `324c3f4ed83cee0e` / `43b9c5382fcb136f` |
| Overworld menu, cursor=SAVE | `state_ow_save.ss2` | `ef4befeafad1a4c2b40dc3f55b587ddafbc801785b5550ef914a309f8d67bc21` | — |
| Overworld menu, cursor=STATUS | `state_ow_status.ss3` | `000de27e76572cb302edfd6768d2b1bfc8dd2fdb5b039cb2ce06910c4d9a9712` | — |

All five states are byte-distinct full-RAM captures, so each screen transition
is backed by a reproducible RAM fingerprint rather than a visual inference
alone. Direct SRAM field reads above are the strongest address-level evidence:
the values written by the in-game SAVE action match the HUD exactly.

## 5. Algorithm

There is no password validator, checksum, key table or code generator to
reimplement. The only relevant state machine is the menu:

```
screen_id ∈ {DATA select, difficulty, slot submenu, copy destination,
             overwrite confirm, delete confirm, copied, deleted}
           ∪ {overworld menu, save confirm, status tabs, shop}

slot_cursor  = clamp(slot_cursor + input, 0, 2)     @ 0x08032E76..0x08032E8E
sub_cursor   = clamp(sub_cursor  + input, 0, 2)     @ 0x08032EA8..0x08032EC0
save_record  = SRAM_base + slot_cursor * 0x5A0      @ 0x08032EAE..0x08032EB8
```

The generic widget at `0x0801E5D0` formats a value by an item-type byte:
type 0 → `%s`, type 1 → `ON`/`OFF`, type 2 → `%d`, type 3 → `%0Xh`,
type 4 → `%c`, default → a string pointer table. This is ordinary UI code; the
`ON`/`OFF` strings are not evidence of a settings/cheat screen.

## 6. Tables

**Complete menu-string table at `0x0826845C` (8 entries, all walked):**

| Index | String | Screen observed |
|---|---:|---|
| 0 | `Select data` | DATA slot list (3 slots) |
| 1 | `Select difficulty level\n  Normal\n  Hard` | difficulty select |
| 2 | `  Continue game\n  Copy data\n  Delete data\n` | occupied-slot submenu |
| 3 | `Where do you want\nto copy it to?` | copy destination |
| 4 | `Ok to overwrite this data?\n  Yes\n  No` | overwrite confirm |
| 5 | `OK to delete this data?\n  Yes\n  No` | delete confirm |
| 6 | `Data copied` | copy result |
| 7 | `Data deleted` | delete result |

Standalone menu strings: `0x0805F994` overworld SAVE/STATUS/SHOP,
`0x0805F9AC` YES/NO, `0x080608F4` "Save game data?".

**Decoded UI text bank** (`0x0805F940`..`0x08060A00`): plain ASCII NUL-terminated
strings with inline control markup. Example raw bytes at `0x0805F994`:
`20 20 53 41 56 45 0a 20 53 54 41 54 55 53 0a 20 20 53 48 4f 50 00`
→ `"  SAVE\n STATUS\n  SHOP"`, which is exactly the rendered menu. There is no
tile-index-encoded text bank for menus to decode: an xref search finds direct
32-bit pointers from code to these ASCII bytes (e.g. `0x080227A4` →
`0x0805F994`). Keyword searches covered ASCII, lowercase, and UTF-16LE.

**Published collectible unlockables** (GameFAQs / Cheating Dome, cross-checked
against the ROM's item/spirit-name bank and in-game descriptions). These are
progression pickups/story events, **not codes**:

| Unlockable | Condition | ROM text address |
|---|---|---|
| Increase HP | collect four Magatama Beads | `0x0805DED4` |
| Increase Spirit Bar | collect four Tome Pages | (item bank `0x0805E000` area) |
| Tome Page | defeat any boss | (item bank) |
| Spirit #67, Spirit of Fire | beat the game | `0x0805E320` |
| Sword of Light + Celestial Slash | after defeating Eliza, visit the inn | `0x0805DE50` |
| Exploder Kick (spirit combo) | equip Lee Pai-Long + Shaolin | combo text `0x0805E6A8`+ |
| Ultra Cavalry Charge (combo) | Black Raven at bottom of Spirit Unity, Bason in L | combo text `0x0805E6A8`+ |
| Difficulty Normal / Hard | chosen at new game | `0x0805FA6C` |

Shop inventory (4 items, observed in BUY): Sushi ¥150 (recover 20 HP),
Hotdog ¥400, Hamburger ¥1000, Noodles ¥3000.

**Out of scope, recorded for completeness:** all web-published "cheats" are
memory patches (GameShark/Action Replay/CodeBreaker), e.g. `83002310 FFFF`
(65535 Yen → EWRAM `0x02002310`), `830022BA 270F` (Max HP → `0x020022BA`),
`33002358 0063` (Leaves → `0x02002358`). They require an external cheat device
and are not developer-intended in-game inputs; none appears as a literal in
the ROM.

## 6b. Enumeration

**Space definition.** The representable in-game cheat-code space is
**0 codes**: there is no alphabet, no code length, no checksum field, no
key-mask sequence table and no input buffer for a code. The complete
developer-intended input surface is:

- 11 menu screens: 8 from the closed pointer table at `0x0826845C` + 3
  standalone strings;
- 3 save slots (cursor clamped `0..2`, code `0x08032E76`..`0x08032E8E`);
- 2 difficulties (`Normal`, `Hard` at `0x0805FA84`/`0x0805FA8D`);
- 3 status tabs and 2 shop modes;
- 7 published collectible unlockables (§6), all pickup/story-gated.

**Validator model.** N/A — no validator exists. The only comparisons against
user input are the menu cursor bounds (`0..2`) and save-slot index arithmetic;
there is no string comparison against any entered text. There is no name-entry
or code-entry field anywhere in the menu enumeration, and no `ENTER NAME`,
`PASSWORD`, `CODE` or `NAME ENTRY` string in any encoding.

**Novel code.** N/A. With a zero-size code space there is no unpublished code
to mint; this is the guide §0.2 / §16.3 **"no system"** negative. The
deliverable for that branch is the bounded proof below.

**Bounds proved by rejection / exhaustive search:**

| Test | Result |
|---|---|
| All 8 entries of the menu pointer table | walked in emulator; entry 9 is not a pointer (`0x20503820`) |
| `PASSWORD`, `CHEAT`, `DEBUG`, `UNLOCK`, `ENTER CODE`, `MASTER CODE`, `LEVEL SELECT`, `SOUND TEST`, `WARP`, `GALLERY`, `BONUS`, `TRAINING`, `NAME ENTRY` in ASCII, lowercase and UTF-16LE | 0 hits; only `secret` (dialogue "secret art", `0x0805?` / `0xEE1E2D`) and lowercase `training` (dialogue) occur, all narrative text |
| Password-alphabet-shaped ASCII runs (≥12 chars, ≥8 distinct symbols) | 0; all 40 sample hits are compressed tile/audio data (`UUUU...`, `2DDD...`) |
| u16 key-mask-sequence tables (runs ≥6 values ≤`0x3FF`) | 31 candidates, all in `0x0805A2F6`..`0x0805DB7C` script data with values `0x366`–`0x39F` and alternating zeros — text/tile IDs, not GBA button masks; none forms a button sequence |
| Thumb `BL` scan for a validator/generator | no code-entry handler, no code comparison routine; the only 3 BL callers of the menu widget at `0x0801E5D0` are within the same generic widget library |
| Button combos on title/menus | `L+R+Start`, `L+R+Select`, `Select+A+B`, Konami sequence, `A+B+Start+Select` (soft reset) — no hidden screen; combos containing Start behave as ordinary Start |
| Published code literals | none exist for this SKU; every published "cheat" is an external memory patch or a collectible condition |

This is a bounded statement about the exact analyzed image: hash
`a5b7419577ac8ad3d7657f95010bfb6a7a312805ae635c7e1650c7d2b3bc64f9`.

## 7. Validation evidence

- **Observed**: title, DATA (empty and saved slots), difficulty select,
  overworld map, overworld SAVE/STATUS/SHOP, save YES/NO confirmation, STATUS
  with 3 tabs, SHOP Buy/Sell and 4 items, slot submenu (Continue/Copy/Delete),
  copy destination, overwrite/delete confirmations, "Data copied"/"Data
  deleted", in-level gameplay and its pause/status screen. Screenshots
  `s42`–`s61` and `s70`–`s78` on disk; full-RAM savestates hashed in §4.
- **Observed (RAM)**: after the in-game SAVE action, SRAM `0x70` = `1000`
  (money), `0x8A` = `120` (HP), `0x8E` = `80` (SP), matching the rendered HUD
  exactly; saved slots appear at stride `0x5A0` in the 32 KiB `.sav`.
- **Derived**: 8-entry menu string table and its "no 9th entry" boundary;
  cursor clamps `0..2`; save-record stride `0x5A0`; all menu text is ASCII with
  control markup; the `ON`/`OFF` strings belong to a generic value formatter.
- **Inferred (labelled)**: the exact semantics of unused bytes in each
  `0x5A0` save record were not needed for the code question and were not fully
  decoded; the soft reset on `A+B+Start+Select` is inferred from the observed
  return to the Nintendo license screen.

Tool limitation: mGBA 0.10.5's GDB stub accepted one client and the core
exited on disconnect, so live GDB reads were not repeatable (guide §16.2/16.13).
RAM evidence therefore uses full savestate dumps plus the battery-SRAM file,
both decoded with `ss.py`.

## 8. Unknowns

- The bit-level layout of collectible flags inside the `0x5A0`-byte save record
  was not mapped; the unlockables are documented from their published
  conditions and the game's own item/spirit text, not from a save-bit decoder.
  This does not affect the code-system conclusion.
- Exact narrative trigger for each Magatama Bead / Tome Page pickup location
  was not enumerated (gameplay collection, not an input code).
- No hidden debug surface was found, so there is no gate/writer to trace.

## 9. Tooling

- `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`
  for Thumb disassembly of the DATA-screen state machine and menu widget.
- Python + Capstone for PC-relative literal resolution, BL-target scans and
  4-byte pointer scans; raw `bytes.find` scans for keyword/alphabet/key-mask
  patterns (`scan.py`, output `scan_out.txt`).
- `ss.py` — decodes mGBA `.ss1` PNG `gbAs` zlib chunk into 397,312 raw bytes
  and dumps IWRAM/EWRAM windows; used for all RAM fingerprints.
- `key.py` — XTEST key driver for reproducible menu navigation on `:315`.
- mGBA 0.10.5, Xvfb `:315`, openbox, xdotool, scrot (all launched and torn down
  by PID for this job only).
- Web sources consulted as data only: GameFAQs cheats/FAQ/release data,
  Cheating Dome, ROMSFUN/libretro cheat list, MobyGames, TCRF (different SKUs).
  No fetched page contained instructions that were followed.

**Legal note:** no ROM bytes, graphics or audio are redistributed here — only
hashes, addresses, decoded UI strings and original analysis scripts.
