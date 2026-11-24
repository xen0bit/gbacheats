# Tiger Woods PGA Tour Golf (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Tiger Woods PGA Tour Golf/Tiger Woods PGA Tour Golf.gba` |
| Size | 8,388,608 bytes (`0x800000`) |
| Header title | `TIGER WOODS` (offset `0xA0`) |
| Game code | `AT5E` (offset `0xAC`) |
| Maker code | `20` (offset `0xB0`) |
| Fixed byte | `0x96` at `0xB2` (OK) |
| Version | `0x00` (`0xBC`); complement `0xB9` (`0xBD`); header checksum `0x0000` (`0xBE`) |
| Entry word | `0xEA00002E` → `0x080000C0` (stock, not a cracktro) |
| MD5 | `1040f372f0d2ed64f01e582dffa6d89b` |
| SHA-1 | `88b204b7b51995e41459b532580b3956d7db55ad` |
| SHA-256 | `c9b4028a2b68cecc5d011a0cfbe035572d8ec7e5629bffa5897883d8b28b115c` |
| Engine/publisher | Rebellion Developments; Destination Software / EA Sports, 2002 |

This is the **2002 Rebellion GBA title** (also sold as *Tiger Woods PGA Tour 2002* on GBA), **not** the EA/Visual Concepts *Tiger Woods PGA Tour 2004* GBA SKU. The two titles' published code lists are not interchangeable (Lesson 16.11).

## 2. Executive summary

**This SKU has no in-game code surface.** There is no password entry screen, no button-code table, no debug menu and no cheat validator. The only published cheat is a **save-based unlockable** — "Snake", obtained by defending the Open Style Championship title five times (GameFAQs, VGChartz, Cheatbook, GGmania all give this one item and nothing else). No password codes are published for this SKU at all.

The widely circulated Tiger Woods password lists (`THEKITCHENSINK`, `ALLTHETRACKS`, `CANYOUPICKONE`, `4REDSHIRTS`, …) belong to *Tiger Woods PGA Tour 2004* and other platforms. **All 60 published strings tested are absent from this ROM** (the three incidental substring hits — `XON` inside `FAXON`, `SS`, `TB` — are ordinary text/graphics bytes, not codes). A contemporary review of this exact game explicitly states the developers "avoided a password system" and used a battery save.

Evidence for the negative is bounded and counted in §6b/§7: every screen in the 29-record screen registry was enumerated, the text banks were decoded (ASCII menus + the game's font digit table), the single joypad read routine and all 23 of its consumers were surveyed, and a whole-ROM scan for button-mask tables found **zero** plausible sequences. Dynamic tests of undocumented button combinations produced no new screen and no persistent RAM change.

## 3. How to reproduce

* Emulator: `mgba 0.10.5`, `DISPLAY=:316`, `SDL_AUDIODRIVER=dummy`, `Xvfb :316 -screen 0 1024x768x24`, `openbox --sm-disable`; `mgba -3 game.gba` (copy of the ROM in `/tmp/tigergolf`, so no emulator artifacts land in the ROM folder).
* Keymap (mGBA SDL default): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows. **A (not Start) selects menu items**; B goes back. Hold keys ≥60 ms; wait ≥1 s after each transition (the menu renderer draws labels over 2–3 frames).
* Savestates: `Shift+F1` saves, `F1` loads. States used: slot 1 = title, slot 2 = Select Player, slot 3 = Options, slot 4 = Main Menu.
* Screen path walked:
  * Title (`PRESS START`) → Main Menu → `PLAY NOW` (12 challenges, challenge intro → hole 2 at Sawgrass) → `GAMES` (PGA TOUR → 1 PLAYER / PASS AROUND / MULTI-LINK; SHOOTOUT) → `PRACTICE` (ANY HOLE / PUTTING / DRIVING RANGE) → `OPTIONS` (SOUND: SFX ON / MUSIC ON; DIFFICULTY: NOVICE/AMATEUR/PRO; WEATHER: RANDOM/FINE/OVERCAST/STORM with `?` icon; CREDITS: scrolling).
  * Select Player: 12 portraits, 4×3 grid. 11 × Right lands on Vijah Singh (12th); one more Right wraps to Tiger Woods → **exactly 12 selectable players**, no hidden 13th reachable by input.
  * Main Menu Down ×4 wraps to PLAY NOW (4 items); "INSTANT ACTION" is a caption, not a selectable row. Options Down ×4 wraps to SOUND (4 items); "CHANGE CONTROLLER OPTIONS" is an orphan string, never drawn.
* Codes tested: none accepted by the game because no entry surface exists. Button sequences tested on the title screen and on the Main Menu: Konami `↑↑↓↓←→←→BA`, `L+R+Start`, `A+B`, and directional sweeps. All left the screen unchanged or performed only the normal Start action.

## 4. Address map

| Item | Address / range | Type | Notes |
|---|---|---|---|
| Header | `0x000000–0x0000BF` | ROM | stock entry `0xEA00002E` |
| Menu text bank | `0x086DB934–0x086DDD88` | ROM | 117 NUL-terminated English strings at `0x3C` stride; no PASSWORD/CHEAT/DEBUG |
| Screen/menu registry | `0x086E0000–0x086E9B88` | ROM | 29 screen-header records (`nxt==0xF0/0x8C/0x89`); pointers into the text bank |
| Player portraits table | `0x086E567C–0x086E5820` | ROM | 12 records (ids `0x02…0x18` step 2); each → portrait gfx `0x080B…` + name string |
| Extra portrait record | `0x086E5828` | ROM | id `0x1A`, sub-id `0x14`, gfx `0x080BB394`, 32×32; not selectable from the UI |
| Main-menu record | `0x086E0630` | ROM | `"MAIN MENU"`; items at `0x086E06C4`, `0x086E06E8`, `0x086E070C`, `0x086E0730` |
| Joypad read routine | `0x080156A4` (Thumb) | code | `ldrh r0,[0x04000130]`; `r1 = 0x3FF ^ r0` (active-high held) |
| Key state (edge) | `0x03000B88` (u16) | IWRAM | pressed-this-frame mask, written at `0x080156BA` |
| Key state (held) | `0x03004B10` (u16) | IWRAM | held mask, written at `0x080156BC` |
| Font digit→char | `0x08015AF8` (Thumb) | code | 10-entry jump table; error path at `0x08015B3C` |
| Font digit table | `0x085B70D8` | ROM | 128-byte `0x7F…0x00` mapping (the only "alphabet" in the image) |
| Debug strings | `0x0819990`, `0x085B71E0`, `0x085B7208` | ROM | `ERROR: in Ball_PlayStrikeSound`, `*ERROR* - QDmaCopy:DMA buffer overflow`, `ERROR in Font_DigitToChar - Invalid Input (%d)`; no debug menu |
| Save type | 512-byte EEPROM (`EEPROM_V122` at `0x085B7260`) | save | save written after each hole; `.sav` observed as 512 bytes of `0xFF` before first completion |

File offset → ROM address: `+0x08000000`.

## 5. Algorithm

Not applicable: **no validator, checksum, encoder, decoder, password table or key-code state machine exists in this image.** The only input-processing algorithm is the standard edge-detect at `0x080156A4`:

```
held  = ~KEYINPUT & 0x3FF          # active-high
press = held & ~prev_held
[0x03000B88] = press
[0x03004B10] = held
```

All 23 literal references to these two words were inspected (see §7). They are menu navigation, club selection (R/L), swing/stance controls and link/multiplayer handlers. None accumulates an ordered press history or compares a sequence.

## 6. Tables

* **Menu text bank** (`0x086DB934`, 117 strings × `0x3C`): `MAIN MENU`, `PLAY NOW`, `GAMES`, `PRACTICE`, `OPTIONS`, `INSTANT ACTION`, `SELECT GAME MODE`, `SHOOTOUT`, `PGA TOUR`, `MULTIPLAYER`, `SELECT HOLE`, `SELECT PLAYER`, 12 player names (Tiger Woods, Colin Montgomerie, Jesper Parnevik, Justin Leonard, Lee Janzen, Mark Calcavecchia, Notah Begay III, Steve Stricker, Stewart Cink, Stuart Appleby, Brad Faxon, Vijay Singh), `PUTTING`, `ANY HOLE`, `DRIVING RANGE`, `SOUND`, `SFX:`, `MUSIC:`, `OFF`, `FRONT 9`, `BACK 9`, `FINE`, `OVERCAST`, `STORM`, `RANDOM`, `PLAYERS`, `TWO/THREE/FOUR PLAYER`, credits (23 rows), language names (ENGLISH/FRANCAIS/DEUTSCH/ITALIANO/ESPANOL), `CONTINUE`, `START OVER`, `HOLE 1…18`, `DIFFICULTY`, `NOVICE`, `AMATEUR`, `PRO`, link ERROR strings. **No `PASSWORD`, `CODE`, `CHEAT`, `SECRET`, `DEBUG`, `UNLOCK` entry.**
* **Input masks** (GBA active-high): A=1, B=2, Select=4, Start=8, Right=0x10, Left=0x20, Up=0x40, Down=0x80, R=0x100, L=0x200.
* **Published codes for this SKU**: 1 unlockable ("Snake" — win/defend the Open Style Championship five times). 0 password codes.

## 6b. Enumeration

**Space definition.** There is no code space to enumerate: no alphabet, no code length, no checksum width, no lookup table of accepted strings. The only hidden content is a **save-bit/counter unlock** in a 512-byte EEPROM; its published trigger is a gameplay achievement, not a typed or entered code. Consequently §0.2's "mint a novel code" step is *not applicable* — there is no validator to mint for. The corresponding deliverable here is a **bounded negative**, with the searched spaces and counts below.

**Counts that bound the negative**

| Search space | Size checked | Result |
|---|---|---|
| ASCII literal search for `PASSWORD`, `CHEAT`, `SECRET`, `DEBUG`, `UNLOCK`, `CODE`, `GENIE`, `GAMESHARK`, `CODEBREAKER`, `MASTER`, `HIDDEN`, `EXTRA` | 8,388,608 bytes × 4 encodings (plain, lowercase, `+0x20`, `-0x20`) | **0 hits** for all but `BUTTON` (1 hit: "PRESS ANY BUTTON TO CONTINUE") |
| UTF-16LE / UTF-16BE / UTF-32LE versions of the same keywords | full ROM | **0 hits** |
| Literal search for 60 published Tiger Woods codes from other SKUs | full ROM | **0 genuine hits** (3 incidental substrings: `XON` in `FAXON`, `SS`, `TB`) |
| Screen/menu registry (`0x086E0000–0x086E9B88`) | 29 header records, 174 string-bank pointers | **0** password/code/debug screen; complete list in §4 |
| Reachable menus | Main 4 items, Options 4, Games 2, PGA Tour 3, Practice 3, Sound 2, Players 3, selectable golfers 12, holes 18, challenges 12 | all walked; wrap-around confirmed for both 4-item menus and the 12-player grid |
| Joypad state consumers | 16 references to `0x03000B88`, 7 to `0x03004B10` | **0** ordered-sequence comparators; only normal UI/gameplay handling |
| Whole-ROM button-mask table scan (u16, active-high single-key masks, run ≥4) | 92 runs; 3 with all-distinct values (`0x3AEEF0`, `0x6000F4`, `0x6DA650`) | all 3 inspected at byte level: graphics/sprite data, **not** button tables. Active-low complement runs: **0** |
| Debug-leftover strings | full ROM | 3 error strings (§4), **0** debug menu / cheat menu |

**Dynamic rejection tests (bounds).** No code can be *rejected* because there is no entry field; the equivalent bounds test is that undocumented input produces no state change. Konami `↑↑↓↓←→←→BA`, `L+R+Start`, `A+B` and D-pad sweeps were pressed on the title screen and main menu; screenshots before/after were identical (or showed only the ordinary Start → Main Menu transition). A title-state savestate reloaded after each test still showed the same `PRESS START` screen, i.e. no persistent unlock flag was set.

**Novel code:** none generated — impossible by construction. Report type: **proven bounded negative** (no code system), not a partial "not found".

## 7. Validation evidence

* **Observed** — Emulator screenshots (`boot3_crop.png`, `after_start_crop.png`, `options3_crop.png`, `pga_1p2_crop.png`, `player11_crop.png`, `player12_crop.png`, `playnow2_crop.png`, `ingame3_crop.png`, `konami_crop.png`, `lrstart_crop.png`) document every menu reached, the 12-player wrap, and the unchanged screens after button sequences.
* **Observed (RAM)** — mGBA `.ss1` savestates at title/Options/Main Menu were decompressed (`gbAs` zlib chunk, 397,312 bytes; IWRAM at state offset `0x19000`, EWRAM at `0x21000`). Title → Main Menu: **EWRAM diff = 0 bytes**, IWRAM diff = 1,479 bytes (screen/stack state only). GDB remote reads at the title screen returned `[0x03000B88] = 0x0000`, `[0x03004B10] = 0x0000` with no keys held, confirming the key-state words identified statically.
* **Derived** — `0x080156A4` disassembly proves the edge-detect and its two destination addresses; the 23 literal references prove the complete consumer set. The 29-record registry and 117-string bank prove the complete menu vocabulary. The 12-record player table (`0x086E567C–0x086E5820`) plus the observed wrap proves the selectable-roster bound.
* **Inferred** — The "Snake" unlock is presumed to be a bit/counter in the EEPROM save record because the cart uses a 512-byte EEPROM and the only published trigger is a repeated tournament achievement; the exact bit and its setter were not isolated. This is reported as *inferred*, not as a code.

## 8. Unknowns

* The exact EEPROM byte/bit and setter routine for the "Snake" unlock were not isolated; triggering it requires winning five Open Style Championships, which was not played through. Per Lesson 16.18 it is a save-bit unlockable, not a code, and is therefore out of the cheat-code scope.
* The extra 32×32 graphic record at `0x086E5828` (id `0x1A`, gfx `0x080BB394`) has no UI entry; its meaning (candidate hidden art) is unproven.
* The three orphan menu strings ("INSTANT ACTION" as a row label, "CHANGE CONTROLLER OPTIONS", "PGA TOUR#") are unreachable through input; no gate was found that enables them.

## 9. Tooling

* `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings -t x`, `grep -abo`; custom Python scripts for encoding-variant search, literal-pointer search, screen-registry parsing and button-mask run scanning.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for `0x080156A4`, `0x08015AF8`, `0x080D7xx–0x080E3xx`, `0x080B394`.
* GDB remote (`gdb-multiarch`, `target remote localhost:2345`) for RAM reads of the key-state words; mGBA `-d`/`-g` were tried, `-g` used for the memory snapshot.
* `.ss1` PNG/`gbAs` chunk decoded with Python `zlib` for the RAM diff (Lesson 16.13).
* Xvfb `:316` + openbox + `xdotool` XTEST + `scrot`/ImageMagick for screen capture; helper `/tmp/tigergolf/k.py`.

## 10. Legal note

No ROM data or copyrighted graphics/audio are redistributed. Only hashes, addresses, algorithms, counts and original observations are published. The rendered `portrait_*.png` files are analysis artifacts kept only in the private work directory, not in the report.
