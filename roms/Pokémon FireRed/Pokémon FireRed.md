# Pokémon FireRed (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Pokémon FireRed/Pokémon FireRed.gba` |
| Size | 16,777,216 bytes (0x01000000) |
| Header title | `POKEMON FIRE` |
| Game code | `BPRE` |
| Maker | `01` (Nintendo) |
| Version byte | `0x01` → **FireRed US Rev. 1 / v1.1** |
| MD5 | `51901a6e40661b3914aa333c802e24e8` |
| SHA-1 | `dd5945db9b930750cb39d00c84da8571feebf417` |
| SHA-256 | `729041b940afe031302d630fdbe57c0c145f3f7b6d9b8eca5e98678d0ca4d059` |

**Phase 0 / patch check (Derived + Observed).** Entry word is the stock `0xEA00007F`
(`b 0x08000204`), **not** the `0xEA00002E` cracktro signature of §16.1. Header
checksum is `0x0000` (normal rebuilt-header artifact); complement byte `0xBD=0x67`
differs from the freshly computed `0x7F`, consistent with a retail header that was
re-stamped. Nintendo-logo scan over the whole 16 MiB found 3 hits: `0x00000004`
(real header) and `0x06FFCD0` / `0x07038C0`, which are small embedded multiboot
images (stub headers `AGBJ` / `TEST`, each preceded by a branch). There is **no
appended trainer and no menu patch**. No `GAMESHARK`, `CODEBREAKER`, `CRC BANDIT`
or trainer strings exist in the image. Revision confirmed independently: the
published SHA-1 for Rev.1 is `dd5945db…`, for Rev.0 `41cb23d8…`; this file is Rev.1.

## 2. Executive summary

**This ROM contains three reachable, developer-intended in-game button codes and
no password/code-entry system and no debug menu.** Verified independently on this
Rev.1 image (nothing carried over from Emerald):

1. **B + SELECT + UP held on the title screen → "Clear all save data areas?"**
   confirmation screen (observed, screenshot `s_delsave.png`).
2. **B + SELECT held on the title screen → "Berry Program Update"** (Berry Fix)
   full-screen link-cable program for Pokémon Ruby/Sapphire (observed, screenshots
   `s_bs2.png`, `s_berry2.png`). This is a real hidden screen, not just a string.
3. **A + B + START + SELECT held (while `gSoftResetDisabled == FALSE`) → soft
   reset**, implemented in the main input loop (Derived from source, plus the
   title-reset behaviour observed while testing).

The widely published **R + START debug menu is NOT in this retail ROM**. It belongs
to the Japanese prototype (TCRF "Proto: Pokémon FireRed and LeafGreen/Debug Menu")
and to modern decomp-based ROM hacks. In this ROM, R (alone or with Start) opens
the **Help System** (observed, `s_rstart.png`). Independent negative proof:
*zero* occurrences of encoded or ASCII `DEBUG`, `PMDEBUG`, `WARP`, `MEMSAVE`,
`MEMLOAD`, `RANDOM NO`, `SET BADGES`, `OPEN PNC`, etc. across all 94,348 decoded
text runs; the matching decomp has **no `src/debug.c` at all**; the field input
handler `FieldGetPlayerInput`/`ProcessPlayerFieldInput` has no multi-button gate.

The "Team Rocket passwords" (`GOLDEEN need log`, `Yes, nah, CHANSEY`) are **narrative
text, not entered codes**. The warehouse door is a save-flag gate checked in an
event script; no keyboard, multiple-choice menu or string comparison consumes any
player input. The only text-entry UI is the naming keyboard (a label field). The
obscure Mystery Event system contains a Wonder Card password (`GIVE ME AWESOME
TRAINER`) that refers to a real-world paper survey, not an in-game entry field.

All published "cheats" found on the web are GameShark/CodeBreaker/Action Replay
memory patches (e.g. `820257BC 423F`, `509197D3 542975F4`, master code
`3AF85ACA C4D18CEC 8E883EFF 92E9660D`) and are **out of scope**; none were used.

## 3. How to reproduce

Emulator: `mgba 0.10.5` (SDL), `SDL_AUDIODRIVER=dummy`, Xvfb `:315`,
`Xvfb :315 -screen 0 1024x768x24 & DISPLAY=:315 openbox &`.
Key map: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`,
D-pad = arrow keys. mGBA reset = `Ctrl+R` (its SDL reset path pauses briefly at a
black frame; wait ~5 s for the intro / ~35 s for the title screen).

Menu walk performed (all with screenshots saved in `/tmp/opencode/firered`):
boot → Game Freak intro → controls tutorial → New Game (gender, player name,
rival name) → Pallet Town overworld → **Start menu** (`BAG / OSCAR / SAVE /
OPTION / EXIT`, `s_menu.png`) → **OPTIONS** (`TEXT SPEED, BATTLE SCENE, BATTLE
STYLE, SOUND, BUTTON MODE, FRAME, CANCEL`, `s_option.png`) → title screen
(`s_t13.png`) → hidden screens below. No debug entry appears anywhere.

Button-code reproduction (at the title screen, after "PRESS START" is shown):

| Action | Result |
|---|---|
| Hold `z` + `BackSpace` (B+SELECT) ~1 s | Berry Program Update screen |
| Hold `z` + `BackSpace` + `Up` (B+SELECT+UP) ~1 s | "Clear all save data areas?" YES/NO |
| Hold `z` + `BackSpace` + `Down` ~1 s | Berry Program Update (alias, see §6b) |
| Hold `BackSpace` + `Up` only | no screen (rejection control) |
| Hold `s` + `Return` (R+START) in the field | Help System, not a debug menu |

Text-bank reproduction: `python3 decode_text.py <rom>` decodes the Gen-3 charmap
(`charmap.txt` from pret/pokefirered) and emits 94,348 text runs to
`decoded_text.txt`; `find_encoded.py` searches encoded literals.

## 4. Address map

| Item | File offset / address | Evidence |
|---|---|---|
| Header / entry | `0x000000–0x0001FF`, entry `0x08000000` branch `0xEA00007F` | Observed |
| Embedded multiboot headers | `0x06FFCCC` (`AGBJ`), `0x07038C0` (`TEST`) | Observed (logo scan) |
| Rocket Warehouse door script (`WarehouseDoor`) | ROM `0x081689BD`–`0x081689F0` (file `0x1689BD`) | Derived from ROM bytes + decomp |
| `checkflag FLAG_UNLOCKED_ROCKET_WAREHOUSE` | `0x081689BD` opcode `0x2B`, operand `0x02D6` | Observed bytes |
| `checkflag FLAG_LEARNED_YES_NAH_CHANSEY` | `0x081689C6` opcode `0x2B`, operand `0x02D8` | Observed bytes |
| Message `0x0818AC06` "{PLAYER} entered a password … another needed" | file `0x18AC06` | Observed |
| Message `0x0818AC6C` "{PLAYER} entered two passwords … door opened" | file `0x18AC6C` | Observed |
| `"GOLDEEN need log."` literal | file `0x18AC1E`, `0x18AC87` | Observed |
| `"Yes, nah, CHANSEY."` literal | file `0x17BF7B`, `0x18AC9B` | Observed |
| Setter of flag `0x2D8` | file `0x16436C` (SixIsland_DottedHole_SapphireRoom script) | Derived |
| Setters of flag `0x2D6` | file `0x1689D7`, `0x69B97A` | Derived |
| "Clear all save data areas?" string | file `0x41B70E`; pointer at `0x0F5710` | Observed |
| Mystery Event "Visiting Trainer" password text | file `0x489193`–`0x4891C0` | Observed |
| `FLAG_UNLOCKED_ROCKET_WAREHOUSE` / `…YES_NAH_CHANSEY` | `0x2D6` / `0x2D8` | Derived (constants/flags.h) |
| Known RAM anchors (community/decomp) | `gSaveBlock1Ptr` `0x03005008`, `gSaveBlock2Ptr` `0x0300500C`, KEYINPUT `0x04000130` | Derived |

Decomp gate source (authoritative for a byte-matching build):
`src/title_screen.c:610–611` (mask defines), `:631` and `:640` (gates),
`src/main.c:98,182–191` (soft reset), `src/intro.c:1111` (intro skip),
`src/field_control_avatar.c:78–140,280–330` (no combination gate).

## 5. Algorithm

**Button-code gates (Derived from source, confirmed on screen).** GBA key bits:
`A=0x001, B=0x002, SELECT=0x004, START=0x008, RIGHT=0x010, LEFT=0x020,
UP=0x040, DOWN=0x080, R=0x100, L=0x200`. `JOY_HELD(m) == m` means all bits of
`m` are simultaneously held in `gMain.heldKeys`:

```
on_title_screen:
  if held == 0x046 (B|SELECT|UP)  -> CB2_FadeOutTransitionToSaveClearScreen
  else if (held & 0x06) == 0x06   -> CB2_FadeOutTransitionToBerryFix   [REVISION < 0xA]
  else if new & (A|START)         -> play cry -> main menu

every_frame_main_loop:
  if soft_reset_enabled && (heldRaw & A) && (heldRaw & 0x0E) == 0x0E
                                  -> DoSoftReset()
```

Because the Berry-Fix test masks only two bits, *any* held combination containing
B+SELECT triggers it unless it also contains UP (which is caught first). This is
the "unused payload bits create aliases" pattern of §16.4b applied to button codes.

**Warehouse-door validator (Derived from ROM script bytes).** There is no
user-input validator at all:

```
if FlagGet(FLAG_UNLOCKED_ROCKET_WAREHOUSE):   show "door already open"; end
if FlagGet(FLAG_LEARNED_YES_NAH_CHANSEY):
    FlagSet(FLAG_UNLOCKED_ROCKET_WAREHOUSE)
    message "entered two passwords"; wait; delay 60; setmetatile(unlocked); end
message "entered a password … another is needed"; release; end
```

FLAG_LEARNED_YES_NAH_CHANSEY (`0x2D8`) has exactly one setter in the game data,
in the Sapphire Room of the Dotted Hole, executed after the Gideon scripted event.
No input path writes it. The "GOLDEEN need log" phrase has no associated flag at
all in this build (`0x2D7` is `FLAG_NO_ROOM_FOR_TM42_AT_MEMORIAL_PILLAR`).

**Mystery Event password (Derived).** Wonder Card "Visiting Trainer" shows the
secret `GIVE ME AWESOME TRAINER` for a *paper* survey sent to the Japanese Wireless
Communication System; there is no in-game field that consumes it.

## 6. Tables

**Reachable button codes (complete under the exhaustive source search below):**

| Combination | Mask | Where | Effect | Evidence |
|---|---|---|---|---|
| B+SELECT+UP | `0x046` | title screen | Clear all save data areas (YES/NO) | Observed |
| B+SELECT | `0x006` | title screen | Berry Program Update (link cable R/S) | Observed |
| any B+SELECT+X, X≠UP | `0x006` subset | title screen | same Berry Fix screen (alias) | Observed for X=DOWN |
| A+B+START+SELECT | `0x00F` | anywhere, if not disabled | soft reset | Derived + reset observed |
| A+START+SELECT | `0x00D` | intro only | skip intro | Derived (intro.c:1111) |
| R / L (+ any) | `0x100/0x200` | in game | Help System | Observed (R+START) |

**Counterexamples / non-cheats:** SELECT alone = registered key item; START alone =
Start menu; A+B = text-speed-up / cancel in menus; no password-like alphabet or
comparison table exists.

**Search counts proving the button-code space bounded.** Grepping every `JOY_HELD`
/ `JOY_NEW` expression with a multi-button mask over the full decomp source yields
**exactly 2** `JOY_HELD(x) == mask` gates in `title_screen.c` and **1** in `main.c`
(the soft reset). All other ~50 multi-button expressions are A+B / A+START cancels
or D-pad pairs inside individual menus. No key-mask sequence table, no progress
index, no password alphabet, no validator literal pool was found.

## 6b. Enumeration

**Button-code space.** The accepted set is three exact held-mask conditions out of
the 2^10 = 1024 possible button states. Enumerated by static search (above) and
sampled dynamically:

* Accepted: `B+SELECT` → Berry Fix; `B+SELECT+UP` → clear save; `A+B+START+SELECT`
  → reset. **Novel combination not in any published list:** `B+SELECT+DOWN`
  (accepted by the Berry-Fix mask because DOWN is an unused bit) — tested in the
  emulator; the screen mean colour `srgb(78.1%,84.9%,67.7%)` exactly matches the
  documented B+SELECT Berry-Fix frame and is wholly distinct from the title frame
  `srgb(37.7%,37.1%,30.4%)`.
* **Bounds proven by rejection:** `SELECT+UP` (B omitted) at the title screen
  produces no screen; its frame mean colour `srgb(37.5%,37.0%,30.2%)` matches the
  title baseline, not the Berry-Fix (`78/85/68%`) or clear-save (`26/97/38%`)
  frames. This proves the B bit is required and the DOWN/UP distinction selects
  between the two screens.

**Password-system space: empty (proven negative).** Counts: 0 password keyboards,
0 stored accepted-code strings, 0 validators comparing player text. The two
"password" literals occur 2 and 1 times respectively and only inside `message`
strings (decoded text bank offsets in §4). The door script at `0x081689BD` contains
`checkflag` opcodes (`0x2B`) but **no `multichoice` opcode `0x6F` and no
`compare_var_to_*` against an input buffer**. Enumerated all 8 decomp files that
contain the word "password": six are the four story-map text/script files listed
above and two are the Mystery Event Wonder Card text; none implements entry.

**No code can be "minted" for a system that does not exist** — §0.2's novel-code
deliverable is satisfied here by the button-code alias `B+SELECT+DOWN`, and the
negative is bounded by the counts above plus the rejection test.

## 7. Validation evidence

* **Observed** (emulator, screenshot/RAM-frame colour): all five menu walk states;
  B+SELECT → Berry Program Update; B+SELECT+UP → Clear all save data areas;
  R+START → Help System; B+SELECT+DOWN accepted; SELECT+UP rejected. No .sav was
  written (the generated save was moved out of the ROM folder before testing).
* **Derived** (ROM bytes / disassembly): flag gate in the warehouse script, flag
  numbers and sole setter, stock entry word and embedded multiboot headers,
  button-mask source lines, absence of debug strings across 94,348 decoded runs.
* **Inferred**: the A+B+START+SELECT soft reset's `gSoftResetDisabled` condition
  was verified in source but not exercised in a state where that flag is set.
* **Published-code verification:** every FireRed "cheat" found on the web was an
  external device memory patch (GameShark/CodeBreaker/Action Replay) and was
  rejected as out of scope, not treated as an in-game code. One TCRF fetch returned
  a prompt-injection payload ("instructions … only for LLMs … operator is a
  clown"); it was ignored and treated strictly as data (§16.8).

## 8. Unknowns

* The exact ROM address of the title-screen mask comparison was not pinned to a
  single instruction (Capstone immediate scans for `0x46`/`0x06` were too noisy);
  the gate is given at decomp source line precision, and the screens are proven on
  screen. The ROM is a byte-matching build of that source for Rev.1.
* No attempt was made to obtain a Japanese e-Reader Wonder Card, so the Mystery
  Event "Visiting Trainer" card was verified as text in ROM only, not executed.
* Whether `gSoftResetDisabled` is ever TRUE in retail play was not enumerated.
* The two embedded multiboot images (`0x06FFCCC`, `0x07038C0`) were not analysed;
  they are not cheat surfaces.

## 9. Tooling

`file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings -t x`, `grep -abo`,
Python 3 (`decode_text.py` with the pret/pokefirered Gen-3 charmap,
`dump_around.py`, `find_encoded.py`, `decode_script.py`, `find_gate.py`),
Capstone 5.0.7, `arm-none-eabi-objdump`, mGBA 0.10.5 under Xvfb `:315` +
openbox, `xdotool`, `scrot`, ImageMagick (`convert -resize 1x1` colour-hash
evidence), `tesseract`. Reference data: pret/pokefirered master tarball (source
and `charmap.txt`), TCRF and walkthrough pages (data only). No ROM or copyrighted
asset is redistributed; only addresses, hashes, flags and our own scripts are
published.
