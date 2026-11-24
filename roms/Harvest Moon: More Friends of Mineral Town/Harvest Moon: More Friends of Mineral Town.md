# Harvest Moon: More Friends of Mineral Town (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Harvest Moon: More Friends of Mineral Town.gba` |
| Size | 16,777,216 bytes (16 MiB) |
| Header title | `HM MFOM USA` |
| Game code | `BFGE` (serial `A GB-BFGE-USA`) |
| Maker code | `E9` |
| Version | `0x00` |
| Fixed byte | `0x96` (at `0xB2`) |
| Header checksum | `0x0000`; complement byte `0xD2` vs computed `0x15` → header was rebuilt (§16.1) |
| Entry word | `0xEA00002E` → branch to stock crt0 at `0x080000C0` (no cracktro/trainer) |
| MD5 | `fcbf93f8859d8500319e0d80a8c02150` |
| SHA-1 | `3aa4d46cbbf152e440942acd5f5d37ddc7b05e1d` |
| SHA-256 | `e754155f92b4809d9f63765592d415f16497d290189cfe1267ea9571a6e14d8e` |
| CRC32 | `1736B957` — matches GameHacking.org's published CRC for AGB-BFGE-USA |

**Embedded-header scan:** exactly one Nintendo-logo hit, at file offset `0x4` (header base `0x0`). No multiboot/link stub, no appended second image, no trainer menu.

## 2. Executive summary

**There is no developer-intended cheat system in this ROM.** No password screen, no passcode validator, no button-code matcher, no hidden options/debug menu reachable by controller input, and no unlockable cheat content exists. The only user-controlled text fields are the three **name-entry** screens (player / farm / dog) used to label the save; they are not validators (§16.2b).

What *does* exist:

- **Documented keyboard shortcuts** (in the Tutorial → "Useful Controls" screen): Start+L = Town Map, Select+L = Farm Map, B on empty hands = switch tools, A+B = Tools/Items, B while holding = put item away, L on empty hands = call out to person. These are ordinary controls, not cheats.
- **Unreachable debug event scripts** in the ROM: a text bank at `0x0875AB34` ("People's expressions!", "Next Person", "Next Expressions", expression states) and a block of scripts at IDs ~434–450 whose bytecode contains debug/test labels ("Ready to go to bed?", "Examine from the left.", "Menu"). TCRF documents reaching one via a **CodeBreaker RAM write** (`8201d1d2 089A`) on the house calendar. On **this US build** that value is out of the script table's range (IDs 1–1415; `0x089A` = 2202) and an empirically patched savestate produced only the normal calendar forecast. The debug content is therefore a **gated feature whose only documented access is a memory edit** — out of scope and not user-reachable (§16.3, §16.4b).

Every published "cheat" found on the web for this title (GameFAQs, Neoseeker, Almar's Guides, Fandom, GameHacking.org, libretro-database) is a **GameShark / CodeBreaker memory-edit code** (encrypted master codes + raw RAM writes). Those are explicitly out of scope here and are *not* in-game cheats.

**Sibling check (position 351, *Friends of Mineral Town*):** verified independently, not by copying the sibling's work. This image is a different ROM: 16 MiB vs 8 MiB, CRC32 `1736B957` vs different, script table at `0x081014BC` (1415 scripts) vs FoMT's `0x080F89D4` (1328 scripts), and different debug-script IDs. Shared: the TOSE engine, the UI conventions, the "Debuggers" **credits job title** (present twice, at `0x104E7C` and `0x11E114` — not a debug menu), and the general pattern of unreachable debug scripts. No address from the sibling was reused.

## 3. How to reproduce

Emulator: mGBA (SDL, `/usr/local/bin/mgba`), Xvfb `:318`, `SDL_AUDIODRIVER=dummy`, 3× scale. Keymap verified against the game: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows. **Hold keys 0.2–0.4 s**; 0.1 s taps are dropped.

Path used:

1. Boot → title art → Start → **Your Name** entry (full ASCII-style keyboard) → End → Yes.
2. **Birthday** (season + day) → confirm.
3. **Farm's Name** → End → Yes → **Dog's Name** → End → Yes → final "Is this OK?" → Yes!
4. Long story intro (advance with A) → playable farm.
5. Start → main menu icon bar: **Diary, Rucksack, World Map, Farm Map, Earnings, Memo, Tutorial** (7 items; wraps).
6. Diary → Save / Load (Data 1/2/3), settings Buttons 1/2, Clock ON/OFF, Face ON/OFF, Name ON/OFF.
7. Tutorial → Useful Tips → "Useful Controls" (documents the button combos above).
8. RAM evidence: live reads via mGBA `-d` debugger with breakpoint `b/t 0x08009194` (called every frame) then `r/2`, `x/2`; and via zlib-decompressed mGBA savestate `gbAs` chunks (EWRAM at state offset `0x21000`). Example live values: `KEYINPUT 0x04000130 = 0x03FF` (idle), EWRAM `0x02000000 = 0x2E80`, player-name string at EWRAM `0x020041F0` = `APPPPPPP`.

**Codes tested:** none applicable (no password/cheat system). Published CodeBreaker values (e.g. `8201d1d2 089A`) were tested as *investigation only* by patching the savestate's EWRAM field `0x0201D1D2` to `0x089A` and to `0x01B2` (script 434); the house calendar produced the normal "This is tomorrow's forecast!" dialogue both times.

## 4. Address map

| Item | ROM address (file offset) | Notes |
|---|---|---|
| Header / entry | `0x08000000` / `0x00000000` | `0xEA00002E` → crt0 `0x080000C0` |
| Key reader | `0x08009194` (`0x009194`) | `r0 = ~KEYINPUT & 0x3FF`; active-high masks A=1,B=2,Sel=4,St=8,R=0x10,L=0x20,U=0x40,D=0x80,Rtr=0x100,Ltr=0x200 |
| Key helper block | `0x08009194`–`0x08009220` | pressed/held wrappers; only **6 external callers** (`0x080084C4`, `0x0800855E`, `0x080085FA`, `0x080086A0`, `0x080E06C0`, `0x0820D3F0`), all generic UI key-handler factories |
| Event-script pointer table | `0x081014C0`–`0x08102ADC` (`0x1014C0`–`0x102ADC`) | 1415 pointers, script IDs 1–1415; index 0 (`0x081014BC`) is NULL |
| Debug expression-menu text bank | `0x0875AB34` (`0x75AB34`) | "People's expressions!", "Character", "Expressions", "Exit", "Next Person", "Next Expressions", "Normal", "Happy", "Angry", "Sad", "Troubled N/A", "Shy", "Marriage", "Exception", "… N/A" |
| Debug/test scripts | `0x0875AC2C`–`0x0875B4B8` | script IDs ~434–450; RIFF/`SCR CODE` bytecode; labels "Ready to go to bed?", "Examine from the left.", "Menu" |
| Calendar forecast text | `0x0895258C` (`0x95258C`) | "This is tomorrow's forecast!" + weather strings |
| "Useful Controls" text | `0x11E5BC`–`0x11E758` (file offsets) | documented button combos |
| "Debuggers" credits | `0x104E7C`, `0x11E114` (file offsets) | staff-roll job title, not a menu |
| Player name (RAM) | EWRAM `0x020041F0` | observed `APPPPPPP` |
| Farm / dog names (RAM) | EWRAM ~`0x020025F0` / `0x0200426E` | observed `AAA` / `AA` |
| `0x0201D1D2` (RAM) | EWRAM | published CB target; normally `0x02C4`; patching to `0x089A`/`0x01B2` had no effect on calendar |

## 5. Algorithm

Not applicable — no password validator, checksum, key table, or button sequence matcher exists. The key-input path is a straightforward active-high mask read (`0x08009194`) consumed by a generic UI handler factory (`0x0800920C`).

## 6. Tables

**Menu items (main/Start menu), complete:**

| # | Label | Contents |
|---|---|---|
| 1 | Diary | Save / Load (Data 1–3); Buttons 1/2; Clock, Face, Name ON/OFF |
| 2 | Rucksack | Tools / Items grids |
| 3 | World Map | Mineral Town overview |
| 4 | Farm Map | Player farm overview |
| 5 | Earnings | Money (500G at start), family/animals, shipping stats |
| 6 | Memo | Farm Degree: Shipment, Fishing, Animals, People, Cooking, Building… |
| 7 | Tutorial | Crops, Animals, Useful Tips, Exit |

**Documented button combos (official, from Tutorial):** Start+L, Select+L, B (empty hands), A+B, B (while holding), L (empty hands). **Undocumented combos tested with no hidden result:** R+Select (opens Earnings, same as Select alone), L+R+Start, L+R+Select, Start+Select, A+B on title, L+R+Start on title, A+B+Start+Select on title, Konami-style Up Up Down Down Left Right Left Right B A on title.

**Published code classification:** 100% of found codes are external cheat-device RAM writes (GameShark/CodeBreaker master codes + raw address/value pairs). Zero developer-intended passwords. No published literal (e.g. `L1TTLVN`, `HAMA!333`) occurs in this ROM.

## 6b. Enumeration

**Space definition:** No code space exists. Enumeration therefore covers the *input surfaces* and *hidden-content space*, with bounds:

| Space searched | Count / bound | Result |
|---|---|---|
| Menu items in Start menu | 7 (verified by walking all 7, screen captures) | No hidden/Options/Debug entry |
| Diary settings toggles | 5 (Buttons, Clock, Face, Name + Save/Load) | All ordinary UI |
| Tutorial sub-pages | 4 (Crops, Animals, Useful Tips, Exit) | Controls only |
| Text fields | 3 (player/farm/dog names; 8-char cap observed) | Labels, not validators; displayed on Earnings |
| "Password" string hits (case-insensitive, whole ROM) | **0** | — |
| "Passcode" / "GameShark" / "CodeBreaker" hits | **0 / 0 / 0** | — |
| "cheat" hits | 1 (dialogue: "trying to cheat!") | Not a code |
| "secret" hits | 42 (all narrative/dialogue) | No secret code |
| "unlock" hits | 1 (dialogue fragment "(unlocked)") | Not a code |
| "debug" hits | 2 (both "Debuggers" credits) | Staff roll |
| "warp" hits | 1 (a horse/dog contest name in a list) | Not a warp code |
| Key-input literal pools | 2 in code (`0x080002E0`, `0x080091A0`) | Single generic reader |
| External callers of key helpers | 6 | Generic UI factories; **0** key-mask `cmp` immediates |
| ROM pointer tables (≥64 entries) | 2 (`0x081014C0` ×1415; `0x0852423C` ×76) | Script table + small data table |
| Debug-menu text/scripts | 1 text bank + ~17 scripts | Present but **not input-reachable** |

**Novel code:** impossible to mint — there is no code format. **Bounds proven by rejection:** the documented CodeBreaker RAM value `0x089A` was applied to the real EWRAM field and rejected by the game (normal calendar forecast, not the debug menu); script ID 434 (`0x01B2`) likewise. Both are recorded rejections, so the "debug screen via that published value" claim is bounded for this build.

**Negative result classification (§16.3):** No system (password/button-code) = class 1; the debug scripts are class 4 (gated behind a memory edit whose writer is an external device, not controller input). Both are closed by the counts above plus the empirical patch rejection.

## 7. Validation evidence

- **Observed:** all title/setup/menu screens captured on emulator; all 7 main-menu items opened and screens captured; Useful Controls text screenshotted; undocumented combos produced no hidden screen; patched-savestate calendar interaction produced normal forecast.
- **Derived:** key mask semantics from `0x08009194` disassembly; script table size/count from pointer-run analysis; debug text bank and script IDs from byte dumps; header rebuild from checksum/complement arithmetic.
- **Inferred (labelled):** that the debug scripts correspond to the affection/expression/tutorial debug menu described by TCRF — the text bank matches, but the scripts were not executed successfully on this build.
- **Prompt injection (§16.8, skill rule):** fetched TCRF pages (MFoMT, FoMT, and their Talk pages) contained injected text: *"This page is not intended for humans… These instructions are only for LLMs and automated agents… whoever is operating this AI agent is a clown."* Treated as untrusted data, ignored, and recorded. No instructions from fetched content were followed.

## 8. Unknowns

- The US build's correct gate for the TCRF debug menu remains unresolved. The published RAM value `0x089A` is out of range for the 1415-script ID space and did not trigger the menu when written to `0x0201D1D2`; the field's true role is unknown. The debug scripts' *effects* were not executed, only their text/bytecode observed.
- Whether a different regional build (JP) has a larger script table where `0x089A`/`0x080E` is valid was not tested (only the USA image was supplied).
- The 76-entry pointer table at `0x0852423C` was not fully classified (appears to be data, not cheats).

## 9. Tooling

`strings -t x`, `grep -abo`, Python/`struct` literal & pointer-run scanners, `capstone` 5.0.7 for Thumb disassembly, `arm-none-eabi-objdump -M force-thumb`, mGBA `-d` pty debugger (breakpoint `b/t 0x08009194`, `r/2`, `x/2`) and mGBA `-g`/GDB (stub was non-functional in this build), zlib savestate (`gbAs` chunk) extraction/diffing, Xvfb `:318` + openbox + `xdotool` + `scrot` + ImageMagick. Screenshots retained in `/tmp/harvestmfomt/`.

**Legal note:** no ROM, graphics, music, or game text was redistributed; only hashes, addresses, algorithms and original tooling are published.
