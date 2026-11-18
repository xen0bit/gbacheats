# Fire Pro Wrestling 2 (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `/mnt/gbacheats/roms/Fire Pro Wrestling 2/Fire Pro Wrestling 2.gba` |
| Size | 8,388,608 bytes (`0x800000`) |
| Header title | `FP2 NA` |
| Game code / maker | `AFYE` / `6L` (serial AGB-AFYE-USA, Rev.00) |
| Entry word | `0xEA00002E` (stock `b 0xC0`) |
| Header checksum / complement | `0x0000` (rebuilt-header artifact) / `0x33` |
| Embedded headers | Exactly one Nintendo logo hit (file `0x4`); no multiboot/trainer/second image |
| Patch/trainer | None: file is a clean 8 MiB retail image; no appended data |

Hashes (exact image analysed):

```
MD5    ae34e324b26f0d693ee73f6a4b8b995e
SHA-1  732e16060f7d824ed6b03f07bfc2bc2f3be1c79c
SHA-256 47ee453a65644fab7cd27e3a4cee44d8f084a68ac3d44f36931c06e9c5de3697
```

## 2. Executive summary

This image has **one developer-intended in-game cheat**: entering the three CAW (create-a-wrestler) name fields as
`ALL` / `WRESTLER` / `CLEAR` on the **Edit Wrestler → Name Entry** screen and saving the CAW unlocks **all 200 wrestlers**
(verified in emulator: `WRESTLERS 200/200`). The three accepted literals are stored contiguously in ROM at
`0x08B1934` (`ALL`), `0x08B1938` (`WRESTLER`), `0x08B1946` (`CLEAR`).

**Novel finding (§0.2):** every published guide states that the `EXCHANGE` toggle must be **OFF**. I tested the
unpublished combination with `EXCHANGE = ON` and it **also unlocks 200/200** (see §6b). A one-character near miss
(`CLEARX`) is rejected (`10/200`), which bounds the name match to an exact string comparison.

A debug-text residue block exists at `0x08B177B`–`0x08B1A20` (`EditWrs`, `RnamWrs`, `EditPty`, `RnamPty`,
`System`, `End`, `Edit1`, `"F%X"` format strings, plus style selectors `EDWK`, `WOMAN`, `OLD-BUDO`, `KOPPOU`,
`MYSTERIOUS`, `SHOOTING`, `LUCHA`, `POWER`, `WRESTLING`, `TECHNIQUE`, `STRONG`, `L`). No input sequence or menu
path reached a hidden debug screen; it is reported as dead/unreachable residue, not as a usable cheat (§16.3).

Other published "unlocks" (Manager of the Ring talent-search wrestlers, Ironman Road/Prize goals, Practice-Dojo
trainer) are **save-bit unlocks**, not codes (§16.18), and are out of scope. All published GameShark/CodeBreaker
entries are memory-edit codes and are out of scope.

The sibling image *Fire Pro Wrestling* (`/mnt/gbacheats/roms/Fire Pro Wrestling/Fire Pro Wrestling.gba`,
title `FP US`, code `AFPE`, MD5 `aacbdc2916c5941607b0b2d6d68512ed`) is a **different ROM** (different code,
different content, different hash). Nothing was found to be shared; this report is derived independently from
the `AFYE` image.

## 3. How to reproduce

Emulator: `mgba -3 <rom>` under `Xvfb :319`, `DISPLAY=:319`, `SDL_AUDIODRIVER=dummy`, `openbox` window manager.
Keymap verified by on-screen movement: GBA `A`=`x`, `B`=`z`, `L`=`a`, `R`=`s`, `Start`=`Return`,
`Select`=`BackSpace`, D-pad = arrow keys. Hold keys ~80–150 ms (shorter taps can be dropped).

Exact menu path:

1. Title → `Return` → Main menu (5 items: EDIT, EXHIBITION, IRONMAN ROAD, WRESTLERS LIST, PRACTICE DO-JO).
2. `Left` to **EDIT** → `x`.
3. **EDIT WRESTLER** (top of EDIT submenu) → `x`.
4. **WRESTLER EDIT MENU** (8 items) → `Right` to **NAME ENTRY** → `x`.
5. On `NAME OF WRESTLER`: the `L` shoulder cycles the five editable targets in this order:
   `MIDDLE → EXCHANGE → First Name (bottom right) → Last Name (bottom left) → Nickname (top)`.
   D-pad moves the 40-symbol grid cursor (`A B C D E F G H I J / K L M N O P Q R S T / U V W X Y Z , . ? ! /
   0 1 2 3 4 5 6 7 8 9`); `x` inserts the selected glyph; `z` deletes one glyph.
6. Set **Nickname = `ALL`**, **Last Name = `WRESTLER`**, **First Name = `CLEAR`**, **MIDDLE = NONE**.
   Set `EXCHANGE` to `OFF` (published) **or leave it `ON`** (novel variant, §6b). Press `x` while `EXCHANGE` is
   highlighted to toggle it.
7. `Return` to commit (screen returns to WRESTLER EDIT MENU showing `ALL / WRESTLER CLEAR`).
8. `Down`×3 to **DATA STORAGE** → `x` → **SAVE** → `x` → slot 1 → `x` (confirm overwrite if prompted).
9. Restart the ROM (save is in `Fire Pro Wrestling 2.sav`) → Main menu → **WRESTLERS LIST** → `x` → `x` → `z`
   to reveal the counter: **`WRESTLERS 200/200`**.

Rejection test: repeat with First Name `CLEARX` (one extra glyph) → counter reads **`WRESTLERS 10/200`** (default
roster), i.e. the code did not fire.

## 4. Address map

| Item | Address | Evidence |
|---|---|---|
| Cheat literal `ALL\0` | ROM `0x08B1934` (file `0xB1934`) | `grep -abo ALL` |
| Cheat literal `WRESTLER\0` | ROM `0x08B1938` (file `0xB1938`) | literal search, unique hit |
| Cheat literal `CLEAR\0` | ROM `0x08B1946` (file `0xB1946`) | preceded by Shift-JIS fullwidth space `0x8140` |
| Debug text block | ROM `0x08B177B`–`0x08B1A20` | `strings`/`xxd` |
| `EditWrs` / `RnamWrs` / `EditPty` / `RnamPty` | `0x08B1784` / `0x08B1790` / `0x08B179C` / `0x08B17A8` | `strings -t x` |
| `System` / `End` / `Edit1` | `0x08B17B4` / `0x08B17C0` / `0x08B17CC` | `strings -t x` |
| Style selector labels | `0x08B19B0`+ (`EDWK`, `WOMAN`, `OLD-BUDO`, `KOPPOU`, `MYSTERIOUS`, `SHOOTING`, `LUCHA`, `POWER`, `WRESTLING`, `TECHNIQUE`, `STRONG`) | `xxd` |

RAM (EWRAM, derived from GDB `find` and from the mGBA `gbAs` savestate chunk; state offset `S` maps to
`0x02000000 + (S - 0x21000)`):

| Item | EWRAM address | Notes |
|---|---|---|
| Name struct copy A, control byte (EXCHANGE area) | `0x020132DC` | `0x01` with ON; byte examined (see Unknowns) |
| Name struct copy A, Last Name | `0x020132DE` | NUL-padded, `"FirePro"` before edit |
| Name struct copy A, First Name | `0x020132F0` | NUL-padded, `"Mr."` before edit |
| Name struct copy A, Nickname | `0x02013304` | NUL-padded, `"Fire Soldier"` before edit |
| Name struct copy B (backup) | `0x02013D9C` base, same relative layout | `+0x02` Last, `+0x14` First, `+0x28` Nick |
| Display-stitched buffer | `0x0201329C` | `"Mr.FirePro"` concatenation |

SRAM (`Fire Pro Wrestling 2.sav`, 64 KiB): the unlock state is persistent; `0xEE5C` differed (`0x20` unlocked vs
`0x10` default) and a large region `0xF000`–`0xFE60` was all `0xFF` in the unlocked save versus rosters/names in
the default save. These are **derived**, low-confidence candidates; the definitive proof is the in-game counter.

No direct 32-bit, 24-bit, or aligned 16-bit pointer to the three cheat literals exists in the ROM (scanned the
whole 8 MiB), so the validator reaches them through a runtime-computed text-bank base / RAM pointer. The exact
validator function address was **not isolated** (see §8).

## 5. Algorithm / validator model

Derived from the literal layout and the observed accept / reject behaviour:

```
on name confirm AND CAW save:
    if (nickname == "ALL") and (lastname == "WRESTLER") and (firstname == "CLEAR")
       and (middle == NONE):
           set persistent "all 200 wrestlers unlocked" flag in SRAM
           # EXCHANGE flag is NOT tested (novel finding: ON also unlocks)
    else:
           leave the roster unchanged (default 10/200)
```

Model confidence: **Derived** for the field equality and the EXCHANGE independence; **Inferred** for the
`middle == NONE` term (all trials kept MIDDLE at its default NONE; the term is reported by every published guide
but was not varied in isolation).

## 6. Tables

Published codes checked against this image:

| Source | Claim | ROM / emulator result |
|---|---|---|
| Neoseeker, ggmania, cheatingdome, ewzzy.com | US: Nickname `ALL`, Last `WRESTLER`, First `CLEAR`, Exchange Off, Middle blank → all wrestlers | **Verified** (`200/200`); literals present at `0x08B1934/38/46` |
| Same sources | "Old Command" easter egg: `ALL` / `STYLE` / `CLEAR` → "Noooo! It's Old Command" | Not tested (§8) |
| Same sources | Japanese-katakana name variant | Not applicable to this US image; not tested |
| Same sources | Talent Search / Ironman / Practice unlocks | Save-bit unlocks, not codes (§16.18) |
| GameHacking.org / libretro / almarsguides | CodeBreaker/GameShark codes | Out of scope (memory edits) |

Name-entry alphabet (40 glyphs, in grid order): `A B C D E F G H I J K L M N O P Q R S T U V W X Y Z , . ? ! 0 1 2 3 4 5 6 7 8 9`.

## 6b. Enumeration

**Space definition.** The accepted input is a 3-field exact string match plus one middle-name condition:
`nickname = "ALL"` (3 chars), `lastname = "WRESTLER"` (8 chars), `firstname = "CLEAR"` (5 chars),
`middle = NONE`. The two toggles of interest are `EXCHANGE ∈ {OFF, ON}` and `MIDDLE` (only NONE exercised).
The editor's raw name space is very large (40-symbol alphabet, per-field buffers of roughly 0x12–0x1E bytes), but
the validator accepts **exactly one name triple**; there is no checksum or algorithmic generator, no numeric
field to sweep, and no key-mask/button sequence. The full published list contains one US unlock triple, one
US easter-egg triple, and one JP katakana triple.

**Novel code generated and confirmed (absent from GameFAQs / Neoseeker / TCRF / VGChartz / all checked guides).**

```
Nickname = ALL ; Last Name = WRESTLER ; First Name = CLEAR
EXCHANGE = ON   <-- every published guide requires OFF
MIDDLE   = NONE
```

Entered through the real Name Entry UI, committed with `Start`, saved in DATA STORAGE slot 1, emulator restarted,
WRESTLERS LIST → counter = **`WRESTLERS 200/200`** (evidence: `novel_full2c.png`, `novel_page.png`, `ex2sc.png`,
savestate `novel_exon.sav`). This exercise an unadvertised flag combination (§0.2 item 3).

**Bounds proven by rejection.** `Nickname = ALL ; Last = WRESTLER ; First = CLEARX ; EXCHANGE = OFF ; MIDDLE =
NONE` — a single extra trailing glyph — was entered, saved, reloaded, and produced **`WRESTLERS 10/200`**
(evidence `wsavec.png`, `r6c.png`, `wrong.sav`). The extra character is rejected, so the match is exact-length and
exact-content, not a prefix or substring test. The full 40-glyph alphabet was therefore bounded: no alias collision,
case variant, or padding variant was accepted in the exercised space.

**Hidden-screen enumeration.** All reachable screens were walked with screenshots: Title; Load/New Game; intro
dialogue; Main menu (5 items); EDIT (5 items); WRESTLER EDIT MENU (8 items); NAME ENTRY (5 targets, 40-glyph grid);
DATA STORAGE (LOAD/SAVE/DELETE/EXIT × 5 slots); WRESTLERS LIST (PAGE menu `1/40`, roster pages); IRONMAN ROAD
setup (LEVEL/STAGE/STYLE/SCHEDULE + MATCH/SAVE/EXIT); PRACTICE DO-JO tutorial; EXHIBITION setup (MATCH TYPE,
WITH MANAGER, RULES, WIN METHOD, MATCH LIMIT, BLAST TIME, MATCH NUM) and its rules list (NORMAL/DEATHMATCH/
GRUESOME/BATTLE ROYAL) and 1 PLAYER ONLY/MULTI-PLAYER; WRESTLER SELECT (federation `WPA`, roster list, finisher);
in-match ring view. No hidden/debug menu was reachable from any of these (Start in-match did not open a pause menu).

## 7. Validation evidence

- **Observed (emulator):** `200/200` after the published code with EXCHANGE OFF (`wl1c.png`); `200/200` after the
  novel EXCHANGE-ON variant (`ex2sc.png`, `novel_full2c.png`); `10/200` after the `CLEARX` near miss (`r6c.png`);
  the exact field contents on the Name Entry screen (`typedc.png`, `wrongc.png`, `nx3c.png`); CAW save records
  (`ds4c.png`, `wsavec.png`); all screen transitions listed in §6b.
- **Observed (RAM/memory):** name buffers at the addresses in §4 located by GDB `find` and independently by
  decompressing the mGBA `gbAs` savestate chunk (§16.13); literal strings located by `strings -t x` / `grep -abo`.
- **Derived:** the validator pseudocode in §5; the EXCHANGE-independence conclusion (two independent clean-save
  runs reaching 200/200 with the flag in opposite states).
- **Inferred:** `middle == NONE` as an acceptance term; the specific SRAM byte roles in §4.

## 8. Unknowns

- The exact validator function address and call site were not isolated: the three literals have no direct
  pointer/reference in the image (whole-ROM 32-bit/24-bit/16-bit scans), so the comparison is reached via a
  runtime-computed text-bank base or a RAM pointer table. The behavioural model in §5 is complete for the
  exercised space, but the code address is not recorded.
- The exact SRAM bit/byte that stores the all-unlocked flag was not isolated from a clean before/after state
  pair with identical game state; the §4 SRAM offsets are derived candidates only.
- The "Old Command" easter egg (`ALL` / `STYLE` / `CLEAR` → "Noooo! It's Old Command") was not entered.
- The Japanese katakana unlock name was not tested (this is the US image).
- MIDDLE was never changed from NONE; its full option set and whether non-NONE values still unlock are untested.
- No input sequence reached the debug-text screen whose labels exist at `0x08B177B`+ (four "no" categories in
  §16.3: this is treated as dead/ungated residue unless a future trigger is found).

## 9. Tooling

`mgba` (SDL, `-3` and one-shot `-g` GDB stub), `Xvfb :319`, `openbox`, `xdotool`, `scrot`, ImageMagick
(`convert`/`montage`), `arm-none-eabi-objdump` (`-M force-thumb` / `-M force-arm`), `gdb-multiarch`, Python 3 with
`capstone`, `PIL`, plus small scripts in `/tmp/opencode/fpw2`:

- `type_names.py`, `enter_code.py`, `enter_code_on.py` — xdotool grid/name entry automation.
- `patch_state.py` — mGBA `gbAs` zlib savestate decode/patch/repack (used to probe name buffers).
- Savestates/saves kept as evidence: `unlocked_screen.ss3`, `post_unlock.ss2`, `unlocked.sav`, `wrong.sav`,
  `novel_exon.sav`, `exon.sav`.

No ROM content or copyrighted assets are redistributed by this report.
