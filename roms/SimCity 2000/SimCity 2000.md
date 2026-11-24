# SimCity 2000 (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/SimCity 2000/SimCity 2000.gba` |
| Size | 4,194,304 bytes (0x400000) |
| Header title | `SIMCITY 2000` |
| Game code | `A5CE` (USA region letter `E`) |
| Maker code | `20` |
| Version | 0x00 |
| Fixed byte 0x96 | present (0x96) |
| Entry word | `0xEA00002E` → branch to `0x080000C0` (stock crt0, **not** a scene cracktro) |
| Header checksum | stored `0x0000`, complement `0xED`; computed sum of `0xA0..0xBC` = `0x04FA`. `~0x12 = 0xED`, so the complement implies an original checksum low byte of `0x12`. This is a rebuilt/edited header (guide §16.1), not evidence of a trainer. |
| MD5 | `139b7e51d2f49dffeede13e464bafeea` |
| SHA-1 | `8999c32301ef811da086e9599d7e7d6cf1533a70` |
| SHA-256 | `02a951f2918e13052f4b28844106093a28a3f9c78739434b1e49a2839babc333` |

**Embedded-header / patch scan:** a 156-byte Nintendo-logo scan over the whole image returns exactly **one** hit, at file offset `0x4` (the normal header). There is no second GBA image, no multiboot stub and no appended trainer header. Publisher/developer per the 3rd party cheat indexes game detail: Full Fat / Destination Software, 13 Nov 2003.

## 2. Executive summary

**There is no in-game/developer-intended cheat system in this ROM.** No password screen, no published GBA code, no live button-code matcher and no hidden/debug menu exists. This is a **bounded negative**, not "not tested": the reachable screen graph was walked exhaustively with RAM (savestate) evidence, every one of the game's selector lists was enumerated to its wrap point, the only text-entry surface was proven to be a label field, and the engine's dormant button-combo machinery was proven unreachable by three independent zero counts.

Key findings:

1. **No published codes to verify.** The archived 3rd party cheat indexes *cheats* page for this exact GBA SKU is empty ("Know Something We Don't? You can submit new cheats…"), and the 3rd party cheat index walkthrough states "As far as I know, there are no secret codes or cheats." All other search hits (`priscilla`, `Noah`, `1123`, `5656`, etc.) belong to the **PC/SNES/J2ME/PS** versions and are absent from this ROM under ASCII, +0x20, UTF-16 and 5/6-bit packings (§16.11/§16.7).
2. **The only keyboard is a name-entry label.** City/mayor names are typed on a 38-cell on-screen keyboard (0-9 A-Z `.` `?` backspace OK). The buffer is IWRAM `0x030006A0` (16 bytes, stored lowercase, rendered as capitals). All 12 static code references to it pass it to a byte-copy routine at `0x08062C40` (verified: `ldrb`/`strb` loop to NUL) — **never** to a comparator. Per §16.2b this is a label, not a validator.
3. **A button-combo matcher exists but is dead code.** `0x0809DA3C` implements "all bits of a key mask seen within 65 frames" against the held-key global `0x03003790`. It has **0** BL callers, **0** 32-bit literals (including the Thumb-bit `addr|1` form) and **0** PC-relative literal loads. The associated key-recording init functions (`0x0809D8CC`, `0x0809D930`, `0x0809D950`, `0x0809D968`) likewise have 0 BL callers. Live game code only tests single key bits (e.g. `0x08064B96` masks `0x08` = Start; `0x08067358` masks `0x01` = A). Undocumented button combos pressed on the title screen produce no new screen (§16.3 "dead code", §16.21 three-count test).
4. **No hidden menus.** Every reachable screen was walked (see §7). Title Options = MUSIC ON / SOUND ON / BACK only. Pause = header "PAUSED" + CONTINUE / OPTIONS / QUIT (the apparently blank row was just the un-rendered header). Options has exactly 3 pages and the disaster list exactly 8 entries. The scenario list has exactly 4 entries and the map list exactly 4.
5. **"TOP SECRET" / "Eiffel Tower" / "Military base" are building names**, not cheat strings (ASCII text bank `0x08392370`-`0x08392410`, in DE/ES/FR/EN). The ASCII strings at `0x083815C8`+ and `0x083BCE7C`+ are generic engine assertions (string/actor/VRAM errors), not debug-menu labels.
6. **Rewards are progression-gated, not codes.** Mayor's House (5,000), City Hall (20,000), Statue (35,000), Military Base (80,000) are population-milestone unlocks in the city save — §16.18 explicitly says a save-bit unlock is not a code.

## 3. How to reproduce

**Emulator / environment**

```
Xvfb :318 -screen 0 1024x768x24 &
DISPLAY=:318 openbox &
export DISPLAY=:318 SDL_AUDIODRIVER=dummy
/usr/local/bin/mgba -3 "roms/SimCity 2000/SimCity 2000.gba"
```

mGBA SDL keymap used: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad = arrow keys. Hold keys 50–150 ms (long holds double-step menus). Window focus via `xdotool windowfocus` on the window found by `xdotool search --name mGBA`.

**RAM evidence method (§16.13):** the mGBA GDB stub on this build proved unreliable after a client disconnect (`-g` halts the core at reset; `interrupt` fails with "Cannot execute this command while the target is running"). Instead, snapshots were taken with `Shift+F1` and the `.ss1` PNG's zlib-compressed `gbAs` chunk decompressed with `ss.py`. The 397,312-byte state has IWRAM at `0x19000` (so IWRAM `0x030006A0` → state offset `0x196A0`) and EWRAM at `0x21000`.

**Screen path walked (all with screenshots + savestates in `/tmp/simcity2000`):**

```
Title (START / OPTIONS)
 ├─ OPTIONS → MUSIC ON, SOUND ON, BACK                    [s06_title_options]
 └─ START → NEW CITY / SCENARIO / LOAD GAME               [s07/s08]
     ├─ SCENARIO → 4-entry carousel (on-screen Up/Down+OK) [s02,s04_scn2,s04_scn_3,s04_scn_4]
     ├─ NEW CITY → "Please select a map" 4-entry carousel  [s09,s10_map_*,s31_map_*]
     │   → city-name keyboard → mayor-name keyboard        [s11..s13]
     │   → Year 1900/1950/2000/2050 × Funds 20k/10k/10k Bond [s14]
     │   → in-game → disaster newspaper → Pause            [s15..s19]
     │       ├─ OPTIONS page 1: speed, Auto Budget, Auto Goto Disasters
     │       ├─ page 2: Disasters + 8-entry list (Fire, Meltdown, Air crash,
     │       │           Tornado, Earthquake, Monster, Microwave, Rioters) [s20..s22]
     │       └─ page 3: In game help, save slot ("Empty slot"), Save [s23]
     │       ├─ SELECT toggles HUD/special-map overlays [s25..s27]
     │       ├─ L toggles bottom tool bar; left icons select build categories [s28..s30]
     │       └─ QUIT → "Are you sure?" Yes/No [quit1c]
     └─ LOAD GAME → save-slot UI (same control as Options page 3, "Empty slot")
```

**Combo tests (all negative):** on the title screen, simultaneous `L+R` (`a+s`), `L+R+Start`, `L+R+B+Start` and an arrow/A/B sequence were held 250 ms and screens captured (`combos.png`). All left the same START/OPTIONS title; no new menu, no flag change.

**Published literals tested:** none exist for this SKU; searches for `priscilla`, `noah`, `atlas`, `FZIHRP`, `5656`, `1123` in the ROM returned only incidental substrings ("meteor", "Power", "arc") in ordinary text.

## 4. Address map

| Region / address | Meaning | Evidence |
|---|---|---|
| `0x08000000` | ROM base; `0x080000C0` stock crt0 entry | header word `0xEA00002E` |
| `0x08381000`–`0x083A0000` | ASCII localized text bank (EN/DE/ES/FR/IT) + engine strings | `strings -t x`; in-game labels match byte-for-byte |
| `0x083815C8`+ | engine string/actor/VRAM assertion messages | e.g. `GetStringPixelLength - invalid pointer` |
| `0x08392370`–`0x08392410` | building/landmark names incl. `STRENG GEHEIM`/`XIMO SECRETO`/`TOP SECRET`, `Eiffel Tower`, power plants | ROM dump; building list in-game |
| `0x0809D540`–`0x0809D9C0` | engine input manager; `0x0809D582` reads `KEYINPUT` literal `0x04000130`, computes `~KEY & 0x3FF` | objdump `-M force-thumb` |
| `0x03003790` | held keys, active-high (A=1,B=2,Select=4,Start=8,Right=0x10,Left=0x20,Up=0x40,Down=0x80,R=0x100,L=0x200) | 50+ game-code literal refs; `0x08064B96` (Start), `0x08067358` (A) |
| `0x03003794`,`0x03003798`,`0x0300379C`,`0x030037A0`–`0x030037AC`, `0x03003690/94/A0` | companion engine key/state globals | literal pool decoded at `0x809D61C`–`0x809D9BC` |
| `0x0809DA3C` | key-combo matcher (mask seen within 65 frames) — **dead code** | disassembly; 0 BL/0 ptr/0 LDR refs |
| `0x0809D8CC` / `0x0809D930` / `0x0809D950` / `0x0809D968` | key-recording/demo helpers — **dead code** | 0 BL callers each |
| `0x08062C40` | `strcpy`-style byte copy used for the name buffer | `ldrb`/`strb` until NUL |
| `0x080635B4` | `StringCompare` (generic strcmp, returns 0/1/-1/2) | debug string at `0x08381FB4` |
| `0x0809A6FC` | engine fatal/assert print | called only from assert sites |
| `0x030006A0` | city-name buffer, 16 bytes (typed lowercase) | savestate string search: `"New city0000000a"` at state `0x196A0` |
| Savestate layout | IWRAM@`0x19000`, EWRAM@`0x21000`, length 397,312 | `ss.py` extraction + known-pointer check |

## 5. Algorithm

No password/serial algorithm exists. For completeness, the dormant combo matcher at `0x0809DA3C` is:

```
struct Combo { u32 start; u32 completion; u16 mask; u16 seen; }
if ((held_keys & combo.mask) == 0) return 0            // 0x809DA46
if (combo.seen == 0) combo.start = frame_counter       // 0x809DA54
if (frame_counter - combo.start > 100) { combo.seen=0; ... }  // 0x809DA5E
combo.seen |= (held_keys & combo.mask)                  // 0x809DA6E
if (combo.seen != combo.mask) return 0                 // 0x809DA7A
if (frame_counter - combo.start > 65) return 0         // 0x809DA84
combo.completion = frame_counter; combo.seen = 0; return 1
```

This is the only key-sequence logic in the image and it has no live call site; it cannot be a cheat in this game.

## 6. Tables

| Table | Count | Values / notes |
|---|---|---|
| Scenarios | 4 | Alien invasion, Mass riots, Earthquake, Nuclear meltdown (wraps 4→1) |
| Maps (new city) | 4 | procedural landscape previews; carousel wraps after 4 |
| Start years | 4 | 1900, 1950, 2000, 2050 |
| Starting funds | 3 | 20,000 / 10,000 / 10k Bond |
| Title Options | 2 toggles | MUSIC ON, SOUND ON (+BACK) |
| In-game Options pages | 3 | page 1 speed+flags; page 2 disasters; page 3 help+save |
| Disasters | 8 | Fire, Meltdown, Air crash, Tornado, Earthquake, Monster, Microwave, Rioters |
| Reward buildings (progression, not codes) | 4 | Mayor's House 5k, City Hall 20k, Statue 35k, Military Base 80k residents |
| On-screen keyboard cells | 38 | 0-9 (10), A-Z (26), `.`, `?`, backspace, OK |
| Accepted passwords / button codes | **0** | see §6b |

## 6b. Enumeration

**Code-system space: empty. There are zero accepted developer codes of any kind.**

Counts that bound the negative:

| Surface checked | Count / result |
|---|---|
| Published GBA codes (3rd party cheat index cheats, walkthrough, web) | **0** — cheats page empty; walkthrough says none |
| Literal code/cheat strings in ROM (`password`, `cheat`, `code`, `secret`, `unlock`, `debug`, PC/SNES codes) | **0** cheat-related; 100% of hits are engine asserts, building names or scenario prose |
| Password/validator entry screens walked | 0 (only the city/mayor name label field) |
| strcmp-family consumers of the name buffer | **0** (all 12 refs → `strcpy` at `0x08062C40`) |
| Key-combo matcher functions with a live caller | **0** of 1 (`0x0809DA3C`: 0 BL, 0 word pointer incl. Thumb bit, 0 LDR literal) |
| Key-recording helpers with a live caller | **0** of 4 |
| Hidden/unlabelled menu rows | **0** ("PAUSED" was a header, not a row) |
| Scenario carousel entries (wrapped) | 4 |
| Map carousel entries (wrapped) | 4 |
| Disaster list entries (scrolled to end) | 8 |
| Options pages (Next exhausted) | 3 |
| Undocumented button combos tested on title | 4, all rejected (no screen/state change) |
| Novel codes minted | **N/A — there is no code system to mint into.** §0.2's "generate a novel code" deliverable is inapplicable; the equivalent bounded negative is delivered above. |

**Bounds proven by rejection:** there is no entry point at which an out-of-range code could be submitted. The nearest analogue — the 16-byte name buffer — accepts arbitrary text but is consumed only as a displayed label; typing a non-alphabetic marker (`'1'`, `'a'`) changed only the string bytes at `0x030006A0..0x030006AF` (savestate diff `s11`→`s12`), never a flag or a screen transition. Button combos on the title changed no persistent state.

**Unlockables enumeration:** the only gated items are the 4 population-based reward buildings (§6), driven by city population in the save record, not by any controller input. With no save advanced past 5,000 residents the Rewards UI offers nothing; this is progress, not a code (§16.18).

## 7. Validation evidence

* **Observed** (emulator/screenshots/savestates): all screens in §3; 4 scenarios, 4 maps, 8 disasters, 3 option pages; title combos unchanged; name buffer typed lowercase `'a'` at state offset `0x196AF`; a tornado triggered after its checkbox was enabled, confirming the disaster list is functional.
* **Derived** (disassembly/static): KEYINPUT read at `0x0809D582`; held-key global `0x03003790`; combo matcher at `0x0809DA3C` and its 0/0/0 caller-pointer counts; name buffer copied by `0x08062C40`, not compared; single-header image (one logo hit); stock crt0 entry word.
* **Inferred**: the newspaper body text uses a distinct low-resolution font bank whose glyphs render garbled in mGBA; the underlying strings were enumerated in ASCII and contain no cheat/debug content, but that specific font mapping was not decoded. Reward thresholds are taken from the published GBA walkthrough and are consistent with the reward names in the text bank; the exact save-bit offsets were not isolated.

## 8. Unknowns

* The newspaper small-print font/tile bank was not decoded; no hidden message was found in any ASCII text bank, and the newspaper is reached only through disasters.
* Exact SRAM offsets of the population/reward fields were not isolated (the 512-byte `.sav` is mostly `0xFF` and stores the city name reversed at `0x0`).
* The mGBA GDB stub was not usable for live register reads after a client disconnect; all RAM claims here come from savestate diffs (§16.13) and static analysis.
* No code system exists, so there is no novel generated code to show; this is stated as a bounded negative rather than an omission.

## 9. Tooling

All scripts in `/tmp/simcity2000`: `phase0.py` (hash/header/logo scan), `allstrings.txt` (`strings -t x -n 4`), `scan.py` (32-bit pointer, Thumb-BL and PC-relative-LDR scanners), `keyscan.py` (key-mask run scanner), `ss.py` (mGBA `gbAs` zlib extractor + RAM diff/hexdump), `snap.sh` (screenshot+savestate helper), `key.py` / `combo.py` (xdotool input), `gdbram.sh` (abandoned GDB dump helper). Disassembly via `arm-none-eabi-objdump -M force-thumb`. Web sources: archived 3rd party cheat index cheats page (empty) and walkthrough 53430 (archived).

**Legal note:** no ROM bytes or copyrighted assets are reproduced here; only hashes, addresses, algorithms and original findings are published.

**Cleanup:** only this agent's PIDs were signalled by number; no `pkill` was used. Generated `SimCity 2000.sav` / `SimCity 2000.ss1` were removed from the ROM folder.
