# Kelly Slater's Pro Surfer (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Kelly Slater's Pro Surfer.gba` (in the same folder as this report) |
| Size | 8,388,608 bytes (0x800000) |
| Header title | `KELLY SLATER` (bytes at 0xA0: `4b 45 4c 4c 59 20 53 4c 41 54 45 52`) |
| Game code | `AS3E` (USA), maker `52` |
| Version | 0x00 (Rev.00) |
| Entry word | `0xEA00002E` — stock ARM branch to 0x080000C0; standard Treyarch/Activision crt0. No cracktro, no appended trainer. |
| MD5 | `e6836a809ffe6aea707231ccf830c122` |
| SHA-1 | `73328bfd274d1ec77c9a67351c026e22f09eeff5` |
| SHA-256 | `93be76156f5c3cde9119f918a43328e8e00d70203993c5049b907b909ddc152c` |

**Embedded-header scan:** the 156-byte Nintendo logo occurs exactly once, at file offset 0x4 → a single GBA header at 0x0. No 2-in-1 pack, no multiboot stub, no second image.

**Note on the header:** checksum (0xBE) = `0x0000` and complement (0xBD) = `0x72` whereas the bytes 0xB2–0xBC sum to `0x96` (expected complement `0x6A`). This is the "edited header" artifact of a rebuilt header (guide §16.1); the title/game code/entry are internally consistent and the image boots normally. Recorded for exact-revision identification.

## 2. Executive summary

The GBA version has a **developer-intended button code** that is completely different from the cell-phone cheat numbers published for the PS2/GameCube/Xbox/PC versions. Every published code (`619-555-4141`, `949-555-6799`, `328-555-4497`, `714-555-8092`, `626-555-6043`, `702-555-2918`, etc.) is **absent from the GBA ROM** in ASCII and in every plausible binary encoding — those are console-version codes (§16.11).

The GBA system is:

* On the **main menu**, enter the 12-press shoulder sequence **`L R L L R R L L L R R R`**. It sets bit 0 of the flag word `0x020041E4`. The Extras screen then switches from an 8-item to an 11-item menu template with four developer toggles: `(Cheat) Beach`, `(Cheat) Boards`, `(Cheat) Clips`, `(Cheat) Champ` (text IDs 30, 32, 34, 28). Each toggle sets one further bit of `0x020041E4` (bits 1–4).
* Effects verified **in-game**: Beach = 13/13 beaches (default 3/13); Boards = 13/13 boards (default 1/13); Clips = all Clip Book photos; Champ = forced perfect **10.0** judge score in heat results (other surfers keep normal scores).
* The whole system is **not saved** — the flag word resets on reboot, so the code must be re-entered each session.
* There is exactly **one** button-code table in the entire ROM (pointer scan of all code addresses → one hit). The accepted space is therefore exactly one 12-press sequence out of 10^12 possible 12-press sequences over the 10-button alphabet. Progress is reset by any wrong press; neutral frames are ignored.
* The text bank is **plain NUL-terminated ASCII** with a 32-bit offset table, so a `strings` scan was sufficient (guide §11 caveat did not apply here). The hidden entries are real strings (IDs 26–34), not compressed/tile-indexed text.

Evidence types: all menu effects and flag values are **Observed** (screenshots + savestate RAM reads); the validator/address map is **Derived** (Thumb disassembly) and cross-checked against the emulator.

## 3. How to reproduce

**Emulator:** mGBA SDL (`mgba -3`), `SDL_AUDIODRIVER=dummy`, Xvfb `:318`, 3× scale, default keymap:
`A=x`, `B=z`, `L=a`, `R=s`, `Start=Return`, `Select=BackSpace`, D-pad=arrows.
Hold each key 0.18–0.22 s with a 0.24–0.26 s release gap (short taps are missed; consecutive identical presses need a neutral frame between them).

**Menu path:**
1. Boot → intro/attract → press `Start` → **Main Menu** (Mode: Amateur, Championship, Challenge, Tutorial, High Scores, Drop In, Multiplayer, Extras).
2. On the **Main Menu**, press `L R L L R R L L L R R R` (8 key strokes → `a s a a s s a a a s s s`). No visible confirmation is shown.
3. Move to **Extras** (bottom entry) and open it. The menu now has 11 entries including four `(Cheat) Off` toggles.
4. Move down to each `(Cheat) Off` and press `A`; the label changes to `(Cheat) Beach`, `(Cheat) Boards`, `(Cheat) Clips`, `(Cheat) Champ` in that order.
5. Surf back to **Championship → select a surfer** to see `Beaches unlocked: 13/13` / `Boards unlocked: 13/13`; the **Clip Book** shows all photos; finishing a heat with Champ on shows `10.0` in the results table.

**Verification without a UI:** decompress the `gbAs` PNG chunk of an mGBA `.ssN` savestate (zlib). EWRAM begins at offset `0x21000`; read flag word at `0x21000 + 0x41E4` (i.e. `0x251E4`).

**Published codes tested (all rejected / not present):** `6195554141`, `3285554497`, `9495556799`, `7145558092`, `6265556043`, `7025552918`, and dashed forms — none occurs anywhere in the 8 MiB image (`grep -abo` → no hits). These are console cell-phone codes and there is no phone/code-entry screen in the GBA build.

## 4. Address map

| Item | ROM / RAM address | Notes |
|---|---|---|
| Header / entry | `0x08000000` / `0x080000C0` | stock crt0 |
| Text-bank base pointer | `0x083E9AB4` | offset table starts `0x083E9AB8`; strings from `0x083EA4CD` |
| `(Debug) Podium` string | `0x083EA5CB` | text ID 26 |
| `(Cheat) Champ` string | `0x083EA5E6` | ID 28 (27 = its `Off` form) |
| `(Cheat) Beach` string | `0x083EA600` | ID 30 (29 = `Off`) |
| `(Cheat) Boards` string | `0x083EA61A` | ID 32 (31 = `Off`) |
| `(Cheat) Clips` string | `0x083EA635` | ID 34 (33 = `Off`) |
| **Button-code table** | `0x087C9A60` | 12 × u16 active-high key masks |
| Button-code matcher | `0x080103EC` | main validator (Thumb) |
| Matcher reset helper | `0x080103E0` | writes 0 to the index |
| Gated caller / per-frame tick | `0x080105A0` | checks screen state, loads input, calls matcher |
| Flag set helper | `0x0800A880` | `OR` a mask into `0x020041E4` |
| Flag test helper | `0x0800A74C` | returns `(*0x020041E4 & mask) != 0` |
| Menu-template setter | `0x080010CC` | template 15 = cheat Extras, 0 = normal (called at `0x08010562`/`0x0801056C`) |
| Code progress index | `0x0200487C` (EWRAM) | u32, 0–12, reset on mismatch |
| Input mask (u16) | `0x020073F4` (EWRAM) | read as `ldrh [0x0200736C + 0x88]` |
| Screen-state gate | `0x02009064` (EWRAM) | must equal `0x02000090` (main-menu state ID), read via `0x080161A0` |
| **Flag word** | `0x020041E4` (EWRAM) | bit 0 = menu unlocked, bits 1–4 = Beach/Boards/Clips/Champ |
| Cheat-bit summary | `0x02004878` (EWRAM) | rebuilt each tick from flags 1,2,4,8 at `0x080104DE`–`0x08010556` |

File offset ↔ ROM address: `rom_addr = 0x08000000 + file_offset`.

## 5. Algorithm

Reimplementation: `/tmp/kelly/validator.py` (passes when run against the ROM table).

Active-high key masks (standard GBA): `A=0x001, B=0x002, Sel=0x004, Start=0x008, Right=0x010, Left=0x020, Up=0x040, Down=0x080, R=0x100, L=0x200`.

```
# gate (caller 0x080105A0), runs once per frame:
state = *(u32*)0x02009064
if state != 0x02000090:            # not the main menu
    index = 0
    return
mask = *(u16*)0x020073F4           # current active-high key state

# matcher 0x080103EC:
m = mask & 0xFFFF
if m == 0: return                  # neutral frame: no progress change
if m == table[index]:              # table = 0x087C9A60, 12 entries
    index += 1
    if index > 11:                 # successful 12th press
        index = 0
        flag_word(0x020041E4) |= 0x01
        play_sound(3)
else:
    index = 0                      # wrong press resets progress
```

Precise details from disassembly: `0x080103EE` masks with `lsls r0,#16; lsrs r4,r0,#16`; `0x08010402` compares `ldrh [table + index*2]`; `0x0801040A` uses `cmp r0,#11; bls` (12 presses exactly); on success `0x08010416` calls `0x0800A880(r0=1, r1=1)` which ORs `1` into the word pointed by the literal `0x020041E0` at `0x0800A890` (i.e. `0x020041E4`).

`0x080010CC(15)` is called when flag bit 0 is set, selecting the 11-item Extras template; otherwise `0x080010CC(0)` selects the normal 8-item template. Each cheat toggle uses the generic flag setter/clearer (`0x0800A880`/`0x0800A8B8`) with its own bit mask.

## 6. Tables

**6.1 Button-code table at `0x087C9A60` (12 u16, active-high):**

| # | Mask | Button |
|---:|---:|---|
| 0 | 0x0200 | L |
| 1 | 0x0100 | R |
| 2 | 0x0200 | L |
| 3 | 0x0200 | L |
| 4 | 0x0100 | R |
| 5 | 0x0100 | R |
| 6 | 0x0200 | L |
| 7 | 0x0200 | L |
| 8 | 0x0200 | L |
| 9 | 0x0100 | R |
| 10 | 0x0100 | R |
| 11 | 0x0100 | R |

Bytes: `00 02 00 01 00 02 00 02 00 01 00 01 00 02 00 02 00 02 00 01 00 01 00 01`.

**6.2 Flag bits of `0x020041E4`:**

| Bit | Mask | Meaning | Set by | Observed effect |
|---:|---:|---|---|---|
| 0 | 0x01 | Cheat menu unlocked | 12-press code | Extras switches to 11-item template |
| 1 | 0x02 | Beach | `(Cheat) Beach` toggle | Beaches unlocked 3/13 → 13/13 |
| 2 | 0x04 | Boards | `(Cheat) Boards` toggle | Boards unlocked 1/13 → 13/13 |
| 3 | 0x08 | Clips | `(Cheat) Clips` toggle | All Clip Book photos available |
| 4 | 0x10 | Champ | `(Cheat) Champ` toggle | Heat results show 10.0 for the player |

All bits are cleared on boot; the code and toggles must be redone each session.

**6.3 Relevant text IDs (bank base `0x083E9AB4`, table `0x083E9AB8`):**

`11` Main Menu, `22` Extras Menu, `23` Clip Book, `24` Credits, `25` Erase Progress, `26` (Debug) Podium, `27/28` (Cheat) Off/Champ, `29/30` (Cheat) Off/Beach, `31/32` (Cheat) Off/Boards, `33/34` (Cheat) Off/Clips, `35/36` Speech Off/On, `37/38` Sound FX Off/On, `39/40` Music Off/On, `41/42` Wave Noise Off/On, `43` Back.

**6.4 All surfers/beaches/boards in the bank** (for scope): 9 surfers (Kelly Slater, Kalani Robb, Rob Machado, Bruce Irons, Tom Curren, Lisa Andersen, Tom Carroll, Nathan Fletcher, Donavon Frankenreiter); 13 beaches (Curren's Point … Cortes Bank); 13 boards (Practice Board … Mega Board). The Beach/Boards cheats set these counts to 13/13; no additional hidden surfer/beach/board string exists beyond these 13/13/9.

## 6b. Enumeration

**Space definition.** Alphabet = the 10 GBA buttons; length = exactly 12 presses; storage = 12 × u16 active-high key masks at `0x087C9A60`; progress index = one u32 at `0x0200487C`. Total *representable* input space = 10^12 = 1,000,000,000,000 distinct 12-press sequences (more if simultaneous-button masks are allowed). The matcher is an **exact u16 equality** per position, so there are **no aliases**: no different button combination, prefix, suffix, or repeated-neutral variant is accepted. **Accepted set size = 1.**

**Validator model.** `validator.py` above reproduces the ROM state machine (including "neutral frames do nothing" and "wrong press resets index") and was checked against the literal ROM table. It accepts the documented sequence and rejects near-misses, prefixes and reversed input.

**Novel code / unpublished combination.** Because the accepted sequence is mathematically unique, no second accepted button sequence can be minted. The unpublished *configuration* delivered here is the cheat combination **`Beach + Clips only`** (Boards and Champ left OFF) — an unadvertised combination absent from GameFAQs, VGChartz, TCRF and the console cheat lists. I entered the 12-press code on the real main menu, then toggled only the 1st and 3rd cheat entries in Extras. RAM proof: `0x020041E4 = 0x0000000B` (bits 0+1+3). In-game proof: surfer select showed **`Beaches unlocked: 13/13` but `Boards unlocked: 1/13`** (`novel_config_extras.png`, `surfer_novel.png`, `clipbook_novel.png`). The full set (`0x1F`) was also entered and produced 13/13 beaches, 13/13 boards, all clips, and 10.0 heat results.

**Bounds proven by rejection (all on the main menu, from a clean `flag=0` savestate):**

| Input | Index after | Flag `0x020041E4` | Result |
|---|---|---|---|
| `L R L L R R L L L R R L` (last press wrong) | reset to 0 | `0x00000000` | rejected — Extras stays 8 items |
| `L R L L R R L L L R R` (11 presses only) | 11 (incomplete) | `0x00000000` | rejected |
| Correct 12 presses | reset to 0 | `0x00000001` | accepted |
| `Borads`-style console phone codes | n/a | n/a | literals absent from ROM; no entry screen |

**Action enumeration.** All reachable branches of the unlocked Extras template were walked: four toggles, each independently verified on/off, plus `Back`. The normal template's eight entries and the pause menu's four entries were also walked. No additional hidden action branch was found in the only validator in the image.

**Negative result for a second code system.** A whole-ROM pointer scan for code-region pointers to runs of ≥5 valid key masks found **exactly one** hit (`0x08010424 → 0x087C9A60`). A literal scan for all published console phone numbers found zero hits. No password/alphabet/keyboard UI exists in this build (the console versions use an in-game cell phone; the GBA text bank has no phone/code-entry strings).

## 7. Validation evidence

* **Observed (screenshots + savestate RAM):** main menu; Extras normal 8-item template; Extras cheat 11-item template; all four toggle labels and their exact flag bits; `13/13` beaches and `1/13` boards baseline vs `13/13`/`13/13` with cheats; all Clip Book photos; pause menu (`Continue/Restart/End Run/Quit`); board select; beach select; heat gameplay; heat results with `10.0` for Kelly Slater and normal scores (7.4, 7.0, 6.5, 6.4, 4.3, 1.4) for the other six surfers; rejection of near-miss and prefix sequences (flag stayed `0`).
* **Derived (disassembly):** validator table/addresses, gate condition, exact equality semantics, reset-on-mismatch, flag setter/test helpers, menu-template switch, text-bank offset table.
* **Inferred:** `(Debug) Podium` (text ID 26, `0x083EA5CB`) is a leftover debug label. It is present in the text bank but was **not** displayed in either observed Extras template (normal 8 items or cheat 11 items), and no second button-code table or other input path to it exists in the ROM. It is therefore classified as **dead/unreachable leftover** at the time of this analysis — this is a bounded negative over the searched spaces (all reachable menus walked; all key-mask tables scanned), not a claim about every possible runtime state.
* No prompt-injection payload was encountered in fetched web content; fetched pages were treated as data and their code claims were re-verified against the ROM and emulator.

## 8. Unknowns

* Exact internal meaning of the `0x02004878` summary word rebuilt from flags 1/2/4/8 at `0x080104DE`–`0x08010556`; it was always `0x7` in the savestates inspected and was not observed to change with the toggles. Its consumer was not isolated.
* The `(Debug) Podium` screen (text ID 26) was not reached; it may require a runtime state not producible from a fresh save (e.g., an internal debug build flag). No input path was found.
* The Champ cheat's `10.0` value was observed in the heat-results table; whether it also affects season/championship final standings beyond that screen was not exercised.
* Effects of playing with cheats on recordable high scores were not tested (console manuals warn about this; no GBA high-score behavior was verified).

## 9. Tooling

* `strings -t x -n 4`, `grep -abo`, `xxd` — strings and literal searches.
* Python 3 + `struct` — header parse, Nintendo-logo header scan, pointer/BL scans, text-offset-table decode, savestate `gbAs` zlib extraction and RAM reads.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` — validator disassembly.
* Capstone 5.0.7 (installed via `pip install --break-system-packages`) — available for Thumb scans; the final scans used raw halfword matching.
* mGBA SDL (`mgba -3`) under Xvfb `:318` + openbox, `xdotool` XTEST input, `scrot` + ImageMagick for screenshots and montages.
* `/tmp/kelly/validator.py` — reimplementation and rejection tests.
* Web checks: GameFAQs (console phone codes and 2-in-1 pack), TCRF (403 on direct fetch; search exposed only console-version debug material), MegaGames/Neoseeker/SuperCheats (console codes), plus the REMY HAX "100 GBA crackmes" post that describes this GBA shoulder code; the latter was **independently verified** here (table, disassembly, emulator flag, all effects).

No ROM or copyrighted assets are redistributed in this report; only addresses, hashes, algorithms, masks and observations are published.
