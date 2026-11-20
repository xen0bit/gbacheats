# The Ant Bully (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `The Ant Bully.gba` (ROM folder), 8,388,608 bytes (`0x800000`) |
| Header title | `THEANTBULLY` (offset `0xA0`) |
| Game code | `BUYE` (`0xAC`); maker `5D` (`0xB0`); version `0x00` (`0xBC`) |
| Entry branch | `0xEA00002E` → `0x080000C0`; fixed `0x96` at `0xB2`; header checksum `0x0057` |
| `file(1)` | Game Boy Advance ROM image: "THEANTBULLY" (BUYE5D, Rev.00); AGB-BUYE-USA, En/Fr |
| MD5 | `3a64d744d25a221e3f10099a5d55f155` |
| SHA-1 | `368589e9e80c7a7862002b90adf23ac69dcb38c5` |
| SHA-256 | `4f52192abda8957a85cac09e6c94d359a58b620959a7f31e6002f57662aaa274` |

Stock retail image: one Nintendo-logo hit at file `0x4` (single game, not a multigame pack), normal crt0, no cracktro/trainer patch. Queue 140.

## 2. Executive summary

**No in-game password, button-code, or code-entry cheat system exists in this build.** The result is a *bounded negative*, not an untested guess:

1. Every reachable screen was walked in mGBA (title, save-slot, Options, Credits, Extras, gameplay/dialogue, Pause) and none offers a code-entry field or cheat menu.
2. The game's custom text bank was decoded before concluding (§7): it contains no password-entry or "invalid code" strings. What looks like a hint about a "COMMAND WINDOW" is the ordinary weapon/action menu, not a debug feature.
3. Static analysis with Ghidra (1583 procedures, 556 defined strings) found **zero xrefs** to the developer-named debug scene records (`DebugCheats`, `PrototypeMenu`, `AssetViewer`, `Prototype`, `Prototype02`, `Test_Yard`). These are leftover data labels in a sorted scene-record blob; no retail code refers to them.
4. No validator, alphabet table, checksum table, or button-mask code table with code xrefs was found; 12 title-screen and 3 boot-time button combinations produced no hidden screen.
5. The only developer-intended unlockable surface is the **Extras** menu: three bonuses shown as `????` until the player accumulates **25 / 50 / 100 fire crystals** (observed on screen and in the decoded hint text in four languages). The bonuses remain locked in the unmodified retail state; their names are an explicit unknown.

Published "cheats" for this SKU are exclusively encrypted GameShark / CodeBreaker / Action Replay device codes (GameHacking.org, cheat-gba.blogspot, 53lu, supercheats). GameFAQs, VGChartz, ChapterCheats and Project Cheat Codes all report zero in-game codes/cheats/unlockables. Those device codes are outside this report's scope and were not used.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 under Xvfb `:317` (`SDL_AUDIODRIVER=dummy`), scale 3×; keymap A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad = arrows.
* Boot: Midway splash → short intro (~10 s; `Return` skips) → title menu.
* Title menu uses **Left/Right**, A selects, B backs: `New Game` → `Load Game` → `Options` → `Credits` → `Extras`.
* Pause (Start, in-game) uses **Left/Right**: `Map` → `Objectives` → `Save Game` → `Options` → `Quit Game`. (Down/Up are ignored in these menus — a harness quirk that looks like a dead key.)
* Extras: from title press Right ×4, A. Three locked entries `????` with fire-crystal icons `×25`, `×50`, `×100`; only `Back` (B) is available while locked.
* Save format (observed): 512-byte SRAM, three 0x80-byte slots at `0x00/0x80/0x100`, header words `0xD703/0xD603/0xD503/0x9503`, ASCII `IM2A` at slot `+0x08`. Slot data is checksummed: patching slot-1 byte `0x4E` from `0x64` to `0xFF`, or bytes `0x20..0x7F` to `0xFF`, made the slot display `Empty` after reload — confirming rejection of out-of-range save edits.
* All screenshots from this session are in `/tmp/opencode/antbully/` (`titlemenu2.png`, `tm_all.png`, `extras1.png`, `extras_zoom.png`, `pause_all.png`, `pw_all.png`, `options1.png`, `boot_all.png`, etc.). No copyrighted assets are reproduced in this report.

## 4. Address map

| Item | File offset / ROM address | Note |
|---|---|---|
| Header | `0x000–0x0BF` | `BUYE`, rev 0 |
| Keypad literal + reader | `0x43104` → `0x08043104`; caller `0x080430E8` | reads `KEYINPUT` `0x04000130`, masks `0x03FF`, inverts |
| Second keypad literal | `0x539F8` → `0x080539F8`; reader `0x08053996` | edge/XOR input handling |
| Scene-name blob | `0x3E41C8–0x57B648` | 54 alphabetically sorted named records |
| `DebugCheats` record | name `0x3E4644`, record `0x3E463C` | 0 code xrefs |
| `PrototypeMenu` record | name `0x44C854`, record `0x44C84C` | 0 code xrefs |
| `AssetViewer` / `Prototype` / `Prototype02` / `Test_Yard` | `0x3E41C8` / `0x444DF0` / `0x44C70C` / `0x455264` | 0 code xrefs |
| `MenuMain` / `StartMenu` records | `0x440580` / `0x450498` | only scene records with any raw-pointer hits (1 each, both in data) |
| Generic button index→mask table | `0x65EB8C` → `0x0865EB8C`: `0,1,2,4,8,0x10,0x20,0x40,0x80,0x100,0x200,0` | 0 code xrefs |
| 4-byte-per-press groups | `0x65EB58–0x65EB8B` | 12 groups (e.g. `01 04 10 40`, `02 04 08 20`), 0 xrefs, UI icon data |
| English text bank | `0x580000–0x5C8000` | custom encoding (see §6) |
| Extras hint (EN) | `0x588994` | `COLLECT FIRE CRYSTALS TO UNLOCK BONUS IN THE EXTRAS MENU` |
| Same hint FR / ES / IT | `0x597640` / `0x5A5D54` / `0x5C2580` | localized copies |
| `19 32 64` byte run | `0x154CE4` | only literal 25/50/100 run found; 0 code xrefs; inside an item-stat table — **not** proven to be the Extras thresholds |

## 5. Algorithm

There is no password validator to reimplement. The only algorithmic artifact characterized is the text-bank encoding used to prove the negative:

* Text is stored as a byte stream with 8-byte record headers (`02 00 L 00 00 00 00 00`, `L` = a length hint).
* `FF FC` = space, `FF FE` = line break; punctuation is single-byte (`0x0E` `.`, `0x0C` `,`, `0x1F` `?`, `0x07` apostrophe).
* The first byte of each record's text is `ASCII - 0x20` (e.g. `0x23`→`C`, `0x25`→`E`, `0x30`→`P`), the rest are plain ASCII.
* `80 B3`–`80 BE` are button-glyph tokens (A/B/L/R/etc.), which is how the weapon tutorial text refers to buttons.
* Decoder: `/tmp/opencode/antbully/decode_text.py`, `dump_text.py`.

Save-slot rejection was tested empirically (§3) rather than by reversing a checksum routine; the checksum function itself was not isolated (see §8).

## 6. Tables

* **Scene records (54 total, sorted)**: `AssetViewer`, `Credits`, `DebugCheats`, `EndCutscene`, `EndMural`, `Exterminator`, `GenericRoom`, `GenericRoomJungleEnt`, `Hiil_Southbridge`, `Hill_*` (15), `House_Kitchen`, `Inside_Frog`, `LanguageSelect`, `Legal`, `Legal_Pal`, `MenuMain`, `Midway`, `Prototype`, `Prototype02`, `PrototypeMenu`, `Splash01`, `StartMenu`, `Test_Yard`, `Yard_*` (~20). Each record has an 8-byte type header (`01 01` room, `02 00`/`02 08` cutscene, `03 00` menu, `04 00` splash, `05 00` house) followed by the NUL-terminated name and variable-length data. The six debug/prototype-named records are of the ordinary `01 01` room type.
* **Extras unlock table (observed, values only)**: thresholds `25`, `50`, `100` fire crystals; three locked entries rendered `????`. Tile icons are fire crystals (same icon as the HUD counter that read `0` at game start).
* **GBA button masks** (from `0x0865EB8C`): A=`0x001`, B=`0x002`, Select=`0x004`, Start=`0x008`, Right=`0x010`, Left=`0x020`, Up=`0x040`, Down=`0x080`, R=`0x100`, L=`0x200`.
* **Decoded text evidence** (all four languages, first-letter shift applied): EN `0x588994`, FR `0x597640`, ES `0x5A5D54`, IT `0x5C2580`. The "COMMAND WINDOW" lines at `0x5888FC`, `0x588B20`, `0x588C24`–`0x588DBC` describe selecting Seed Bomb/Fire/Bridge/Dig Hole/Push/Transport/Follow/Hold — the normal action menu, not a cheat menu.

## 6b. Enumeration

**Code/password space:** empty. There is no alphabet, no input surface, no table of accepted codes, and no validator in any reachable screen or in code with xrefs. Therefore no novel code can be minted and this is reported as a *proven bounded negative* with the counts below, not as an omission.

**Enumerated unlockable space (Extras):** 3 bonuses gated by fire-crystal totals 25, 50, 100. Because the gate is a monotonically increasing counter, only 4 of the 2³ = 8 possible unlocked bit patterns are reachable by normal play: `000` (0–24), `100` (25–49), `110` (50–99), `111` (100+). The non-monotonic patterns (`001`, `010`, `011`, `101`) cannot occur. Observed state on a fresh save: `000` — all three entries rendered `????`.

**Novel codes:** none exist to generate; no published in-game code list exists to be a member of. The nearest positive artifact — the 25/50/100 unlockable — was found independently of any web list and is documented above with its in-game evidence.

**Bounds proven by rejection (counts):**

| Test | Count | Result (Observed) |
|---|---|---|
| Title-menu button combos: L+R; Start+Select; A+B; L+R+Start; L+R+Select; A+B+Start+Select; Select+A+B; Up+Down+A+B; L+R+A+B; Select+Start; R+Start; L+Start | 12 | No hidden screen or menu entry appeared |
| Boot-time holds: L+R+Start+Select; L+R; Start+Select (6 s each from power-on) | 3 | Only the normal Midway splash / intro; no debug menu |
| Save-slot edits: byte `0x4E`→`0xFF`; bytes `0x20..0x7F`→`0xFF` | 2 | Slot displayed `Empty` after reload — out-of-range data rejected |
| Ghidra xrefs to the six debug-named scene records | 6 addresses queried | 0 xrefs each |
| Ghidra xrefs to candidate threshold literal `0x08154CE4` and to the button-mask tables | 4 addresses queried | 0 xrefs each |
| ASCII strings matching `password|cheat|code|unlock|debug|generator|invalid` (excluding localized dialogue and the debug scene labels) | 1 (`DebugCheats`) | No validator/password string |

**Space-size statement for the negative:** the search covered all 8 MiB of ROM for (a) ASCII and `+0x20`-shifted password/code strings, (b) 32-bit pointers to scene records and to `0x04000130`, (c) u16/byte button-mask sequences with ≥4 distinct masks (16 u16 runs, 55,975 byte runs — all either zero-fill, generic mask maps, or unreferenced asset data), and (d) the entire decoded script text bank (`0x580000–0x5C8000`, 568 short records enumerated). No code-system component was found in that space.

## 7. Validation evidence

* **Observed** (mGBA screenshots, `/tmp/opencode/antbully/`): all reachable screens listed in §3; Extras `????` with ×25/×50/×100; Options volume/language; Pause items; rejection of patched saves (`Empty` slot); no effect from 15 button combos.
* **Observed** (Ghidra 12.1.4 via REA): 1583 procedures, 556 defined strings; zero xrefs to debug scene names, threshold candidate, and mask tables; two readers of `KEYINPUT`.
* **Derived** (byte-level): scene-record layout and the 54-name sorted list; text-bank encoding; save-slot layout; button-mask table.
* **Inferred**: that the six debug/prototype-named scene records are unreleased developer leftovers. The 25/50/100 run at `0x154CE4` is labelled a coincidence (item-stat table, no xrefs), not the Extras thresholds.
* **Rejected/false leads (resolved)**: "PRESS [button] TO DISPLAY THE COMMAND WINDOW AND SELECT START NOW" — decoded to the weapon/action menu tutorial. Shin'en Multimedia banner at `0x13F3DE` — audio-engine credit, not a code.

## 8. Unknowns

* The names and effects of the three Extras bonuses could not be revealed: unlocking requires accumulating 25/50/100 fire crystals in normal play, which was not completed, and save-patch attempts were rejected by the slot checksum (which was not reverse-engineered). The names are not present in the decoded text bank.
* The save-slot checksum algorithm was not isolated; only its rejection behavior was observed.
* Whether any of the debug-named scene records can be reached through a non-retail path (e.g. a build flag, link transfer, or a debugger-forced scene switch) was not tested; the claim is restricted to retail input and to the zero-xref static result.

## 9. Tooling

* `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings`, Python 3 (`struct`, `re`).
* Xvfb `:317` + openbox; mGBA 0.10.5 (`-3`); `xdotool` XTEST key events with 35–120 ms holds; `scrot`, ImageMagick for crops.
* Ghidra 12.1.4 through REA MCP (`open_binary` raw-binary/ARM @ `0x08000000`, `binary_overview`, `xrefs`, `resolve_containing_procedure`, `close_binary`).
* `arm-none-eabi-objdump -M force-thumb` for the keypad readers; custom scripts `/tmp/opencode/antbully/decode_text.py`, `dump_text.py`, `combotest.sh`, `bootcombo.sh`.
* Web recon (treated strictly as data): GameFAQs, VGChartz, Project Cheat Codes, GameHacking.org, GameFAQs cheats, ChapterCheats, cheat-gba.blogspot. One TCRF fetch returned 403; no instructions from any fetched page were followed.

No ROM image or extracted assets are redistributed here; only hashes, addresses, algorithms and observations are published.
