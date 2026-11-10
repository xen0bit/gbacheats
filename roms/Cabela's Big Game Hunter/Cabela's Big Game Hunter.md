# Cabela's Big Game Hunter (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Cabela's Big Game Hunter/Cabela's Big Game Hunter.gba` |
| Size | 8,388,608 bytes (8 MiB) |
| Header title | `CABELAS BGH` |
| Game code | `A8HE` |
| Maker code | `52` |
| Software version | 0 |
| Entry word | `0xEA00002E` → `0x080000C0` (stock GBA crt0, ARM) |
| Header complement | `0x08` (valid for bytes `0xA0..0xBC`) |
| Stored header checksum | `0x0000`; computed value `0xF8` |
| MD5 | `b0a0c0fd729544c7fd786a6a4d4b419f` |
| SHA-1 | `f6590b9f069856c1a9e43d19b4b05e3175a97e02` |
| SHA-256 | `2bd88eaa5eea883c5aaff3b6184093d954c118fe37f609470f18f239b8453530` |

Embedded-header scan: exactly **one** Nintendo logo (`24 FF AE 51 …`) at file offset `0x4`; one GBA image; no second/sub-image header, no appended trainer, no cracktro. The stored header checksum of `0x0000` is the usual rebuilt/dumped-header artifact; the complement byte is correct (`0x08`), and the entry branch is the retail `b 0x080000C0`, so the title/code fields are trustworthy.

Developer: ImageBuilder Software, Inc. (boot splash reads **ImageBuilder**); publisher Activision; copyright `©2002 Activision Publishing, Inc.`. This is the 2002 GBA SKU, not the 2005 Adventures title (different engine, different ROM).

Content ends at file `0x79FBB7`; bytes from `0x79FBB8` to `0x7FFFFF` are `0xFF` fill.

## 2. Executive summary

There is **no in-game cheat/password/button-code/debug-menu system in this ROM**.

The complete user-visible surface is:

1. engine splash → title → copyright notice;
2. **Hunt Select** — 16 hunts over four regions (`ALASKA`, `PENNSYLVANIA`, `MONTANA`, `WISCONSIN`), each 1–3 stars where the manual confirms **stars are difficulty, not unlock state**;
3. one description card per hunt;
4. **Firearm Select** — six weapons (`.243`, `.270`, `.338`, `.30-06`, `Shotgun`, `Muzzleloader`);
5. gameplay: **Stalk Mode** (map, hunter = blue dot, animals = red dots, L/R cycles run/walk/crawl, A opens scents/lures, B enters Hunt Mode) and **Hunt Mode** (panorama, L/R rotate, D-pad aims, A fires, B returns to Stalk);
6. **Calls & Scents** (3 items for the moose hunt: Moose Call, Moose Scent, Mask Scent; the set is species-specific);
7. **quit confirmation** (`Are you sure you want to quit?  Press A to quit / Press B to cancel`).

`Select` is not used (the manual says so explicitly and the emulator confirms it). There is no Options screen, no sound/control menu, no password entry, no unlock screen, and no debug menu.

Static evidence agrees with the screen enumeration:

* `strings -n 4` yields 107,353 records; a strict printable-ASCII pass (`0x20..0x7E`) yields 104,970 runs. There are **zero** occurrences of `password`, `cheat`, `debug`, `secret`, `unlock`, `gallery`, `option`, `code`, `stage select`, or `level select` in ASCII, `+0x20`/`-0x20` case shifts, UTF-16LE/BE, or XOR-`0xFF`. (`WARP` appears twice only inside a high-entropy compressed/graphics run at `0xFDB6D`/`0xFDD43`, not as text.)
* All game text is ordinary ASCII and is rendered by `0x08006E84` / `0x08007000` (`char - 32` × 32-byte glyph). Region/animal/weapon strings live plainly at `0x0475A80..0x0475D70` and again at `0x0600AC0..0x0600BB0`. A password screen would therefore have left plaintext labels; none exist.
* The registered screen/action class set is complete and contains no Options/Password/Cheat/Debug class: `TitleAct`, `SelectAct`, `DescriptionAct`, `GunSelectAct`, `HunterAct`, `ShootAct` (+ `ShootDeer/Bear/Elk/Moose/Sheep/Animal`), `CallsAndScentsAct`, `QuitAct`, `WarningAct`, `SummaryAct`, `TrophyAct`, `CongratsAct`.
* There is no button-sequence table: scanning the whole code region (`0x0..0x2C0000`) for u16/u32 arrays of the ten GBA button masks finds **0 plausible sequences**. All 119 u16 mask runs and all 13 u32 mask runs lie at `≥0x408CC8` in graphics/data, not code. The 313 "plausible" byte-level runs are ordinary instruction bytes, not tables.
* The published codes that exist for the *Cabela's* franchise are for other SKUs and are console commands or GameShark/CodeBreaker memory edits (out of scope). Their literals are absent from this image: `bgh_unlockLevels`, `bgh_needMoney`, `bgh_animalfreeze`, `cuckoo`, `nextstand`, `getthere`, `cheat_availableitems`, `Mod_givemission` → 0 occurrences each. GameFAQs' GBA page (game 563171) advertises no cheats, only game information/message board; VGChartz, CheatCC and TCRF have no GBA cheat/password list for this SKU. (Direct GameFAQs fetch returns HTTP 403 to this environment; the no-cheats statement is from the indexed page summary, and no GBA code literals exist to verify in any case.)

The code space is therefore **empty**: alphabet = ∅, length = 0, validator = none, entry surface = none.

## 3. How to reproduce

Emulator: mGBA 0.10.5 (SDL), `Xvfb :224 -screen 0 1024x768x24`, `openbox`, `SDL_AUDIODRIVER=dummy`.

```
Xvfb :224 -screen 0 1024x768x24 &
DISPLAY=:224 openbox &
DISPLAY=:224 SDL_AUDIODRIVER=dummy /usr/games/mgba -3 "Cabela's Big Game Hunter.gba" &
```

Key map used (mGBA SDL defaults): A `x`, B `z`, L `a`, R `s`, Start `Return`, Select `BackSpace`, D-pad arrows. Hold 100–250 ms per press; mGBA needs the window focused (`xdotool windowfocus $(xdotool search --name mGBA)`). The GBA viewport is 720×480 at window offset `+154+184` when the window is at its default position.

Exact paths:

* Boot → splash → title: wait or press A. Title screen: **Press START to begin**.
* START → copyright notice → A → **Hunt Select**.
* Hunt Select: Left/Right cycles 16 entries (verified cycle length 16 by image-hash repeat), A → description.
* Description: A → Firearm Select; B → Hunt Select.
* Firearm Select: Left/Right cycles 6 weapons (cycle length 6), A → Stalk Mode; B → description.
* Stalk Mode: D-pad moves the blue hunter dot; L or R cycles run/walk/crawl (the bottom-left hunter icon changes pose); A → Calls & Scents; B → Hunt Mode; START → quit confirmation.
* Calls & Scents: Left/Right cycles items; A uses the item and returns to Stalk; B cancels.
* Hunt Mode: D-pad aims (reticle recoils upward after a shot); L/R rotate the panorama; A fires; B → Stalk Mode; START → quit confirmation.
* Quit confirmation: A → Hunt Select; B → cancel.
* `Select` (BackSpace) does nothing on title, hunt select, description, gun select, Stalk or Hunt Mode.

Codes tested in the emulator: Konami sequence (`Up Up Down Down Left Right Left Right B A`) at Hunt Select — no effect (the final A simply opened the highlighted hunt description, the same as a normal A press). `L+R+Select` and `A+B+START+SELECT` at the title/copyright — no effect. `Select` alone at every screen — no effect. No published GBA code exists to test; all published franchise literals for other SKUs are absent from the ROM (above).

## 4. Address map

| Address | Meaning |
|---|---|
| `0x080000C0` | ARM crt0 (stock) |
| `0x080001C8` | crt0 literal `0x08000F05` = Thumb `main` |
| `0x08000F04` | `main` |
| `0x08001110` / `0x08001128` | input poll; reads `0x04000130`, XORs `0x03FF` into active-high, builds `{frame, held, pressed}` |
| `0x03000000` | input struct: `+0` frame counter, `+2` held keys, `+4` newly pressed keys |
| `0x03000850` | new-input flag; `0x03000852/54/56` frame/prev/current |
| `0x03000E50` | “Smsh” engine object (`53 6D 73 68`), action/script dispatch |
| `0x03001E00` | 36-entry opcode dispatch table copied from ROM |
| `0x08016CA8..0x08016D34` | ROM source of the 36 Thumb opcode handlers (entry = pointer & ~1) |
| `0x08006E84`, `0x08007000` | ASCII text renderers; glyph index = `char - 32`, 32 bytes/glyph |
| `0x0475A80..0x0475D70` | plaintext trophy/region/weapon string table |
| `0x0600AC0..0x0600BB0` | duplicate of the same string table |
| `0x0475CF8` | `Alaska\0Pennsylvania\0Montana\0Wisconsin` |
| `0x0475D24` | `.243\0.270\0.338\0.30-06\0Shotgun\0Muzzleloader` |
| `0x080209E8` | RTTI name `8TitleAct` |
| `0x080209A8` | RTTI name `9SelectAct` |
| `0x080215DC` | RTTI name `14DescriptionAct` |
| `0x080216CC` | RTTI name `8ShootAct` |
| `0x08017054` | RTTI name `9HunterAct` |
| `0x085647FC` | RTTI name `14GunSelectAct` |
| `0x08475D5C` | RTTI name `10SummaryAct` |
| `0x08600BA4` | RTTI name `9TrophyAct` |
| `0x08708A8C` | RTTI name `10CongratsAct` |
| `0x0856E040` | RTTI name `10WarningAct` |
| `0x085CB97C` | RTTI name `7QuitAct` |
| `0x083B8924` | RTTI name `17CallsAndScentsAct` |
| `0x02000000`, `0x02002000`, `0x0200A000` | EWRAM render buffers |

RAM key masks (from `0x08001128`): A=`0x0001`, B=`0x0002`, Select=`0x0004`, Start=`0x0008`, Right=`0x0010`, Left=`0x0020`, Up=`0x0040`, Down=`0x0080`, R=`0x0100`, L=`0x0200`.

## 5. Algorithm

Not applicable: there is no code/password validator, no alphabet table, no checksum and no encoder/decoder pair.

The only input handling is the generic joypad poll at `0x08001128`, which stores `held = KEYINPUT ^ 0x03FF` and `pressed = held & ~previous` at `0x03000000+2/+4`, then dispatches to the scripted action/opcode engine at `0x03000E50`. The menu/screen logic consumes those bits one press at a time; no sequence matcher, comparison table, rolling index or action-per-prefix dispatcher exists.

## 6. Tables

| Hunt-select entry | Region | Animal(s) | Stars |
|---|---|---|---|
| 1 | Alaska | Moose | 1 |
| 2 | Pennsylvania | Whitetail deer | 1 |
| 3 | Montana | Black bear | 1 |
| 4 | Pennsylvania | Moose | 1 |
| 5 | Alaska | Black bear | 1 |
| 6 | Wisconsin | Whitetail deer | 1 |
| 7 | Wisconsin | Black bear | 1 |
| 8 | Alaska | Bighorn sheep | 2 |
| 9 | Wisconsin | Bear + deer | 2 |
| 10 | Wisconsin | Moose + deer | 2 |
| 11 | Pennsylvania | Elk + deer | 2 |
| 12 | Pennsylvania | Elk + bear | 2 |
| 13 | Montana | Deer + bear | 3 |
| 14 | Alaska | Moose + bighorn sheep | 3 |
| 15 | Montana | Deer + bear | 3 |
| 16 | Montana | Moose + bear | 3 |

(The exact animal pairing of entries 13/15 is read from the portrait; both are 3-star Montana combos. The list has exactly 16 entries — proven by image-hash cycle repeat — and all are selectable from the first boot; there are no locked/greyed rows.)

| Weapon | Description |
|---|---|
| `.243` | bolt action, all-round small/medium game |
| `.270` | bolt action, most distances |
| `.338` | long-range large game |
| `.30-06` | pump action, deer |
| `Shotgun` | 12-gauge autoloading, deer |
| `Muzzleloader` | black powder, powerful but short range |

Calls & Scents for the Alaska moose hunt: `Moose Call`, `Moose Scent`, `Mask Scent`.

Button masks: see §4. No mask table is stored in the ROM (see §6b).

## 6b. Enumeration

**Space definition.** There is no code space. No input field exists for a password, code, button sequence or hidden menu. The only text-entry-like surface in the game is the menu cursor, and the only comparisons against user input are the ordinary menu event tests (A/B/START/LEFT/RIGHT) and the gameplay aim/fire tests. Therefore:

* alphabet = ∅
* length = 0
* checksum width = 0
* reserved bits = n/a
* representable values = **0**

**Search space actually examined (bounds).**

| Space | Size examined | Result |
|---|---|---|
| Printable ASCII runs ≥4 (`strings -n 4` / strict `0x20..0x7E`) | 107,353 / 104,970 | 0 real hits for password/cheat/debug/secret/unlock/gallery/option/code/warp/level-select/stage-select |
| Keyword encodings | ASCII, lower, upper, `+0x20`, `-0x20`, UTF-16LE, UTF-16BE, XOR-`0xFF` (11 words × 2 cases + shifts) | 0 hits except `WARP` twice in compressed bytes `0xFDB6D/0xFDD43` |
| u16 button-mask arrays in code `0x0..0x2C0000` | whole region, runs ≥4, masks and masks+`0`/`0xFFFF` | 0 plausible sequences |
| u32 button-mask arrays in code | whole region, runs ≥3 | 0 |
| u8 button-mask runs | whole region | 4,029 raw runs, 313 length/diversity candidates; all are instruction bytes, none a table |
| Registered action classes | all type-name registrations | 11 screen classes + 6 `Shoot*` subclasses; no Options/Password/Cheat/Debug class |
| Menu screens walked | title, copyright, 16 hunt entries, 16 description cards, 6 weapons, Stalk, Hunt, Calls & Scents, quit | all reachable UI walked |
| Published GBA codes | GameFAQs GBA page, VGChartz, CheatCC, TCRF | none published |
| Published other-SKU literals | 9 PC/console command strings | 0 occurrences in ROM |

**Novel code.** None can be minted, because there is no acceptor. The equivalent deliverable for a negative engagement is the bounded proof above: a second analyst can re-run the same scans and re-walk the same screens. In the emulator, every code-like input tested (Konami, `L+R+Select`, `A+B+START+SELECT`, `Select` at every screen) produced no hidden screen and no state change beyond normal menu navigation.

**Bounds proven by rejection.** The system rejects every possible input by construction: there is no screen that accepts a code, no function that compares a user string to a stored string, and no mask table that could match a sequence. This is stronger than a checksum rejection — the input path does not exist.

## 7. Validation evidence

**Observed (emulator / screenshots):**

* Boot splash “ImageBuilder”, title screen, copyright page.
* Hunt Select with 16 entries; cycle length 16 measured by pixel-identical frame at step 16 and step 32.
* Firearm Select with 6 weapons; cycle length 6 measured by pixel-identical frame at step 6 and 12.
* Stalk Mode: blue hunter dot moves with D-pad; red animal dot(s); red wind flag; animal-tracker icon top-left; L/R changes the hunter icon between running, crawling and walking poses.
* Hunt Mode: panorama rotates with L/R, reticle moves with D-pad and recoils upward on A; B returns to Stalk Mode.
* Calls & Scents: three items cycle with Left/Right; A uses the selected item and returns to Stalk Mode.
* START in gameplay shows only `Are you sure you want to quit? / Press A to quit / Press B to cancel`.
* Hunt Mode firing was exercised against a deer-sized target on the Pennsylvania hunt: the reticle recoils upward after A, and the top-left animal-tracker icon changed from a tan background to a **red background**, which the manual defines as “wounded animal”. This confirms the fire path and the wounded-state HUD, though the animal was not recovered/killed.
* No response to Select on any screen; no response to Konami or the tested button chords other than normal menu actions.

**Derived (instruction/table evidence):**

* Input path and key masks at `0x08001128` / `0x03000000`.
* ASCII text renderer and plaintext string tables; absence of password/alphabet strings by exhaustive scan.
* Complete action-class inventory from type-name registrations.
* Absence of u16/u32 button-mask tables in the code region.
* Header/entry integrity, single embedded header, no trainer.

**Inferred:**

* `SummaryAct`, `TrophyAct`, `WarningAct` and `CongratsAct` are post-hunt outcome screens (claim/summary, trophy room, out-of-season warning, completion congratulation). Their names, the manual's “Claiming Animals / Trophy Room / Hunting Out of Season” sections, and the class inventory support this; none of them is a cheat or unlock menu.
* The two red-dot markers in Stalk Mode are the animal and the animal-tracker/wounded indicator (manual: “Animals: all animals are represented by red dots”; “Wounded animals will show up with a red background”). The exact dot-to-icon assignment was not needed for the negative cheat result.

## 8. Unknowns

* The claim → summary → trophy-room flow was not completed in this session. The animal was located, Hunt Mode entered, the rifle fired, and the wounded-animal tracker state was observed; a kill/claim was not confirmed. This is an outcome-screen gap, not a cheat-system gap: those classes contain no code entry, no alphabet and no comparisons against user text, and the manual describes them as trophies/warnings only. Every **menu/input surface** (title, hunt select, description, firearm select, Stalk, Hunt, Calls & Scents, quit) was walked; the unreached screens are post-kill outcome views with no input beyond continue.
* The Smsh opcode VM was not fully decoded. It is the engine's action/script interpreter, and no mask table, password string or validator was found in or around it. A hypothetical sequence implemented entirely as script bytecode (with no table and no labels) cannot be excluded by table scanning alone; it is excluded here by the absence of any hidden screen or class and by the dynamic negative tests. This is the one residual static unknown and is stated rather than hidden.
* Save type (EEPROM/Flash) was not determined; the game produced a 0-byte `.sav` because no hunt was completed. No save-backed code format exists in any case (no password/save-code strings or validators).

## 9. Tooling

* `binutils-arm-none-eabi` (objdump, Thumb/ARM), Capstone 5.0.7, Python 3.
* mGBA 0.10.5 SDL under Xvfb `:224` + openbox; `xdotool`, `scrot`, ImageMagick (`convert`, `compare`, `montage`).
* `tesseract-ocr` on the US manual PDF (`videogamemanual.com`) for the control/menu/trophy-room descriptions.
* mGBA PNG savestates parsed with a small Python script (PNG `gbAs` chunk → zlib → mGBA 0x61000 state; EWRAM at `+0x21000`, IWRAM at `+0x19000`, VRAM at `+0x1000`, I/O at `+0x400`).
* Search scripts: printable-string extractor, multi-encoding keyword scan, Thumb PC-relative literal scanner, u8/u16/u32 mask-run scanner, screenshot cycle-hash comparator.
* Working artifacts (not shipped): `/tmp/opencode/cabela/` — screenshots, savestates, scan scripts, cycle frames.

## Legal note

No ROM, extracted graphics, audio or copyrighted text is redistributed. Only hashes, addresses, class names already present in the ROM, short UI labels needed to identify screens, and the analysis are published.
