# Barnyard (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Barnyard/Barnyard.gba` |
| Size | 8,388,608 bytes (`0x800000`, 64 Mbit) |
| Header title (0xA0) | `BARNYARD` |
| Game code (0xAC) | `BBYE` (Nintendo reports `AGB-BBYE-USA`) |
| Maker code (0xB0) | `78` (THQ) |
| Software version (0xBC) | `0x00` (Rev. 00) |
| Entry word (0x00) | `0xEA00002E` (ARM branch to `0x080000C0`; standard crt0) |
| Complement check (0xBD) | `0x6D` — **valid** (recomputed `0x6D`) |
| Header checksum (0xBE) | `0x0000` — **invalid** (recomputed `0xBD58`) |
| MD5 | `56c434600bf895c83a485ab8cbe49500` |
| SHA-1 | `7a6e2bf247ba7ac2420a5eef39b77a5d871785b5` |
| SHA-256 | `af94b4d8dc26800d9130e4fd711edbbe4d8f8277a099964848ae1bfaebe11122` |
| Developer / publisher | Halfbrick Studios / THQ (2006) |

**Embedded-header scan.** The 156-byte Nintendo logo occurs exactly once, at file `0x4`
(header base `0x0`). There is no second image, so this is a single-game cartridge, not a
multi-game pack, and every absolute pointer in this report uses
`ROM address = 0x08000000 + file offset`.

**Patch status.** The complement check and logo are intact, the entry word is the stock
crt0 branch, and no IPS/BPS/UPS/xdelta container is present. The one anomaly is the
header checksum field: it is zero instead of the computed `0xBD58`. That is the signature
of a header edit/trim tool rather than a game patch; no code-level modification was found,
and the boot/behaviour described below is self-consistent. File tail is zero padding
(last nonzero byte `0x7FBA2F`, 17,872 trailing zero bytes).

## 2. Executive summary

The GBA build has a single developer-intended cheat entry point: **OPTIONS → `Enter Code:`**,
a four-slot alphanumeric wheel. The wheel holds ASCII and only accepts the 36 symbols
`0-9` then `A-Z`; every other byte is skipped by the increment/decrement loop
(`0x0800D708`). After four characters are dialled, `A` performs one `strcmp` against a
single literal:

```
0x0809A46C: "0T1S"
```

`0T1S` is the **only** accepted code in the whole ROM. On success the game writes a u32
unlock flag at `0x02033D6C`, shows the dialog *“Congratulations! You have unlocked four
new colored cows!”*, and the character-creation colour list grows from **3 to 4** entries
(one extra palette per character, the new entry marked with two stars). The unlock is
written into the save file and survives a power cycle.

The code is not on GameFAQs (its GBA cheats page carries only PS2 and Wii codes), nor in
the official manual (which documents the *feature* — “You are also able to enter your
secret code here to unlock new characters!” — but never prints a value). TCRF could not
be retrieved (403 directly, 503 via the Wayback Machine) and is therefore excluded rather
than claimed as a negative. The cross-platform button codes (PS2 `R1+R2`, Wii `C+Z`,
GameCube `L+Z` sequences) have no
handler in this build: the ROM contains no key-mask sequence table matching them, and
pressing them at the title screen leaves the unlock flag at zero.

Because the validator is a single literal comparison, the code space is exactly
**36⁴ = 1,679,616 strings with 1 accepted value**. There is no checksum and no field
layout to mint from; the “novel code” deliverable is therefore the recovered literal
itself, which is absent from every published list, plus the proof that all of the other
1,679,615 values are rejected.

## 3. How to reproduce

Emulator: mGBA 0.10.5 (`/usr/games/mgba`) under `Xvfb :172` + `openbox`.

```bash
Xvfb :172 -screen 0 1024x768x24 &
DISPLAY=:172 openbox &
DISPLAY=:172 SDL_AUDIODRIVER=dummy mgba -3 "roms/Barnyard/Barnyard.gba" &
W=$(DISPLAY=:172 xdotool search --name mGBA | head -1)
DISPLAY=:172 xdotool windowfocus $W
# screenshots: DISPLAY=:172 import -window $W shot.png   (exactly 720x480 = 3x 240x160)
```

Default mGBA SDL keymap used throughout: **A = `x`, B = `z`, L = `a`, R = `s`,
Start = `Return`, Select = `BackSpace`, D-pad = arrows**. Hold keys 100–300 ms; menu
transitions take 1–3 s.

Exact path to the code screen (from a cold boot, no save needed):

1. Wait for the title screen, press **Start**.
2. On *Select a file*, press **Right ×4** to reach `OPTIONS`, press **A**.
3. Press **Down ×3** to `Enter Code:` (the row shows `0 0 0 0`).
4. Press **A** — a hand cursor appears under the first digit.
5. Left/Right select a slot (0–3); Up/Down change the symbol
   (`0→9→A→…→Z→0` going down, the reverse going up).
6. Dial `0` `T` `1` `S`, press **A**.

Correct code: dialog *“Congratulations! You have unlocked four new colored cows!”*
Wrong code: no dialog, the wheel is left on screen, nothing is unlocked.

To see the effect: **A** (dismiss) → **B** (back to file select) → **A** (file 1) →
name entry (A, Down×3, Right×4, A) → *Choose a character* (Right×3 to the 4th cow, A) →
*Choose a color*: **four** swatches, the extra one starred.

Speed-up used in this session: with `Shift+F1..F10` / `F1..F10` savestates, the whole
test loop is one keypress per attempt. mGBA writes `.ssN` PNG savestates containing a
`gbAs` chunk = zlib-deflated core state; the memory layout in that blob is
`0x000–0x400 header, 0x400–0x18400 VRAM, 0x18400–0x18800 palette, 0x18800–0x18C00 OAM,
0x18C00–0x19000 I/O, 0x19000–0x21000 IWRAM (0x03000000), 0x21000–0x61000 EWRAM
(0x02000000)`. This was used to read the unlock flag without a GDB stub.

## 4. Address map

All addresses are ROM addresses (`0x08000000 + file offset`); RAM addresses are absolute.

| Address | Kind | Meaning |
|---|---|---|
| `0x0800C790` | code | Options-screen init (`options_screen.ro`, cursor sprite, prompt) |
| `0x0800C96C` | code | Options-menu update: key decode, item index 0–4, volume/display |
| `0x0800CDF0` | code | **Enter Code** sub-screen update (digit wheel) |
| `0x0800D708` | code | Digit validity predicate: `(c-'0')<=9 || (c-'A')<=25` |
| `0x0800D72C` | code | Redraw one digit (reads buffer + position tables) |
| `0x08092784` | code | `strcmp` used by the validator |
| `0x0809A46C` | data | ASCII literal **`"0T1S"`** (file `0x9A46C`), the only accepted code |
| `0x03000F30` | RAM | Digit buffer, 4 ASCII bytes; `0x03000F34` is set to NUL before the compare |
| `0x03000ED8` | RAM (u16) | Selected digit slot, 0–3 |
| `0x03000EDA` | RAM (u16) | Set to 1 on the first successful unlock (companion flag) |
| `0x02033D6C` | RAM (u32) | **Unlock flag** (0 = 3 colours, 1 = 4 colours) |
| `0x08017922` | code | Flag reader: loop bound `#3` if flag≠0 else `#2` |
| `0x080183CE` | code | Flag reader, same 3/4 pattern (sprite/entity update) |
| `0x080184B0` | code | Flag reader, same 3/4 pattern (sprite creation) |
| `0x080B4F58` | data | Screen-state table entry holding the Thumb pointer `0x0800CDF1` to the code-entry screen |
| `0x78BD40` (file) | data | ASCII UI string `"Enter Code:"` in the string bank (length-prefixed record) |
| `0x0988E0` (file) | data | Resource root name `gba.pak`; manifest of asset names follows |
| `0x099028` (file) | data | Script-VM command-name table (`MinigameUnlock`, `JukeboxPlay`, …) |
| `0x09B758` (file) | data | `MINIGAME_*` identifier table: 26 named IDs + `MINIGAME_UNKNOWN` |
| `0x098F24` (file) | data | `actors\player_1.sp` … `player_4.sp` (the four selectable cows) |

Notes:

* The digit buffer is *not* a fixed string table; it lives in IWRAM and is compared at
  run time. Only four ROM literals reference it (`0x0CEB8`, `0x0CFA0`, `0x0D308`,
  `0x0D770` inside the two options-screen functions), so there is no second entry point.
* The literal at `0x0809A46C` is pointed to exactly once in the whole image (`0x0CFA8`),
  i.e. only the validator loads it.

## 5. Algorithm

```
; ---- Enter Code screen state (0x0800CDF0) --------------------------------
digits : u8[4]  @ 0x03000F30      ; ASCII, each must satisfy valid()
slot   : u16   @ 0x03000ED8      ; 0..3

valid(c):
    if ((c - '0') & 0xFF) <= 9  : return 1
    if ((c - 'A') & 0xFF) <= 25 : return 1
    return 0

on Right : if (slot < 3) slot++
on Left  : if (slot > 0) slot--
on Down  : do { digits[slot]++ } while (!valid(digits[slot]))   ; wraps Z -> 0
on Up    : do { digits[slot]-- } while (!valid(digits[slot]))   ; wraps 0 -> Z
on B     : leave code mode

on A:
    digits[4] = 0                          ; 0x03000F34, NUL terminator
    if (strcmp(digits, "0T1S") != 0):      ; 0x08092784 vs 0x0809A46C
        draw rejection indicator; leave code mode; return
    if (*(u32*)0x02033D6C == 0):           ; first unlock only
        *(u32*)0x02033D6C = 1
        *(u16*)0x03000EDA = 1
    show "Congratulations! You have unlocked four new colored cows!"
    leave code mode; return
```

The flag is consumed by three loops of the form

```
n = (*(u32*)0x02033D6C != 0) ? 4 : 3;      ; 0x0801792A / 0x080183D4 / 0x080184B6
for (i = 0; i < n; i++) { ...sprite/entity update for cow slot i... }
```

which is what adds the fourth colour swatch.

**Space definition.** Alphabet `0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ`, fixed length 4,
no checksum, no fields, no reserved positions, one literal comparison. Representable
inputs: `36^4 = 1,679,616`. Accepted: exactly **1**. Rejected: **1,679,615**. Lowercase,
punctuation and space are *not representable at all* because the increment/decrement loop
skips them (`valid()` above); the UI therefore cannot express a 5- or 3-character code
either.

## 6. Tables

### 6.1 Code entry UI (observed)

| Row | Options item | Behaviour |
|---|---|---|
| 0 | `Music:` | Left/Right adjust BGM volume |
| 1 | `Sound:` | Left/Right adjust SFX volume |
| 2 | `Display:` | Bright / Normal / Very Bright |
| 3 | `Enter Code:` | four-slot wheel, values `0 0 0 0` |
| 4 | `Credits` | staff roll |

Digit wheel order (verified by stepping): `0 1 2 3 4 5 6 7 8 9 A B C … Z` (36 symbols).
`Up` from `0` lands on `Z`; `Down` from `Z` lands on `0`.

### 6.2 Code literal

| ROM address | File offset | Bytes | String |
|---|---|---|---|
| `0x0809A46C` | `0x9A46C` | `30 54 31 53 00 00 00 00` | `0T1S` |

### 6.3 Unlock flag and companion flags

| Address | Type | Value before | Value after `0T1S` | Consumers |
|---|---|---|---|---|
| `0x02033D6C` | u32 | 0 | 1 | `0x08017922`, `0x080183CE`, `0x080184B0` (+4 more literals in the profile module) |
| `0x03000EDA` | u16 | 0 | 1 | set only on first unlock; purpose not isolated (probably a “new unlock” message latch) |

## 6b. Enumeration

**Space size.** `36^4 = 1,679,616`; accepted values = 1 (the literal `0T1S`); no
checksum, no bit fields. This is a *closed* space, not an algorithmic encoder: there is
nothing to mint, and the validator will accept exactly one string forever.

**Novel code — `0T1S`.** This is the code recovered by reverse engineering and entered in
mGBA. It appears in **no published list**:

* GameFAQs GBA cheats page (archived 2022-10-23): only PS2 `R1+R2` and Wii `C+Z` entries;
  no GBA built-in code.
* Targeted web searches for `"0T1S"` and for Barnyard GBA secret codes return nothing.
* The official manual (scanned, OCR’d locally) documents the screen — *“The Options Menu
  lets you alter your game settings. You are also able to enter your secret code here to
  unlock new characters!”* — but prints no value.
* TCRF was not retrievable (403 direct, 503 on archive), so it is excluded as a source
  rather than treated as a negative.

**In-game proof (observed).** Entering `0 T 1 S` and pressing A produces the dialog

> Congratulations! You have unlocked four new colored cows!

and the *Choose a color* screen for the 4th character then shows **four** swatches; the
fourth is marked with two yellow stars. Before the code the same screen shows **three**
swatches. After saving and power-cycling, the fourth swatch is still present (the flag is
in the save data).

**Bounds proven by rejection (observed).**

| Input | Result |
|---|---|
| `0T1T` | no dialog, no unlock; flag stays 0 |
| `YZYZ` / `YYZY` / `ZS0S` | same silent rejection |
| `ZZZZ` | same silent rejection; flag stays 0 (savestate read) |
| `0t1s`, `0-1S`, `0 1S`, any 3- or 5-char string | **not representable** in the UI (`valid()` rejects the bytes), so no state can submit them |

The flag was read from the deflated `gbAs` savestate chunk (`EWRAM[0x33D6C]`):
`0` before/after every rejected input, `1` after `0T1S`; the digit buffer read
`30 54 31 53` (`0T1S`) in the accepted state and `00 00 00 00` when untouched.

**Negative results, bounded.**

1. *No second code literal.* A full scan of all 86 `BL` sites that target the `strcmp`
   at `0x08092784` shows exactly one site comparing against a 4-character ROM string
   (`0x0CF10` → `0x0809A46C`). The other 85 compare script-VM property names
   (`level_x`, `invincible_flag`, `sprite_key`, …), file extensions (`pal`, `set`) and
   asset tags — not codes.
2. *No password alphabets/tables.* Searching the ROM for `0-9A-Z` alphabet strings,
   base-36 tables and 4-character NUL-terminated uppercase strings (1,023 candidates)
   found no code table; the wheel alphabet is defined by code, not stored.
3. *No button-code system.* The published console sequences
   (`Up Left Down Right Right Down Left Up`, `Down Down Left Left Left Left Up Left`,
   `Up Right Down Left Left Down Right Up`, …) were searched as u16 key masks, as
   byte-per-press arrays and reversed: **0 hits**. Holding L+R and entering the two Wii
   sequences on the title screen produced no visual change, and a savestate taken
   afterwards still had `0x02033D6C = 0`, with *Choose a color* showing 3 swatches.
   The only code literal that references `KEYINPUT` (`0x04000130`) is the single input
   driver; the one other byte-match for that value lies in script/asset data, not in a
   code path, so there is no second key-sequence consumer.
4. *No debug menu.* Of 80,867 strings (`strings -n 4`) none contain `debug` as UI text;
   the only developer leftovers are the script-VM command names compiled from
   `string_tables\command.str` (`MinigameUnlock`, `MinigameLock`, `JukeboxPlay`, …) and a
   `--- Scenario: %d (%s)` `printf` at file `0x9A264` used by the VM, not a reachable
   screen.
5. *No activities menu screen to walk.* Of 1,316 minigame-related strings, resources are
   limited to intro/completed/high-score art (`interface\minigames_screens\…`); there is
   no minigame-select menu resource or label. Minigames are launched from quest scripts
   through `MinigameInit` / `MinigameEnum` / `MinigameSetScript`; 27 `MINIGAME_*` IDs are
   enumerated at `0x9B758` (26 named entries — `BOWLING, WILD_DANCING, MAILMAN, FRUIT_GRAB, REPAIR, BALLOON,
   SHEEP_HERDING, CHICKEN, POOL, MARBLES, GOLF, FRUIT_SORT, CAR_CHASE, DARTS,
   CROSS_COUNTRY, DRIVING_RANGE, LILLYPAD, TIME_TRIAL, BIKE_RACE, PIPES, DISC,
   RACCOON_SLIDE, SQUIRT_RANGE, MEADOWS_SLIDE, WHACK, SHOWDOWN` + `UNKNOWN`). The
   gallery/jukebox/trophy unlockables are likewise script rewards (`ACTION_GALLERY`,
   `ACTION_JUKEBOX`, `ACTION_TROPHY`; `MSG_NEW_GALLERY`, `MSG_NEW_JUKEBOX`,
   `MSG_NEW_TROPHY`) rather than code-gated content.

**Menus walked (captured next to this report).**

| Screen | Evidence file | Result |
|---|---|---|
| Boot logos → title `Press Start` | `Barnyard - title.png` | reached |
| File select (3 slots, `OPTIONS`, `ERASE`) | `Barnyard - file select.png` | all entries exercised |
| Options (5 items) | `Barnyard - options.png` | all items exercised |
| Enter Code sub-mode | `Barnyard - enter code 0T1S.png` | wheel mechanics verified |
| Name entry | `Barnyard - name entry.png` | A–Z / abc / backspace / Continue / Erase |
| Choose a character | `Barnyard - choose a character.png` | 4 cows |
| Choose a color | `Barnyard - three colors before code.png` (3) vs `Barnyard - four colors after code.png` (4) | **A/B proof** |
| In-game HUD, The Yard / The Barn | `Barnyard - unlocked cow in game.png` | entered and played |
| Pause: Game Menu | `Barnyard - pause menu.png` | Continue / Go to Sleep (disabled) / Save Game / Save and Exit |
| Pause: Inventory | `Barnyard - inventory.png` | empty at chapter 1 |
| Pause: Mission Log | `Barnyard - mission log.png` | “Chapter 1 — Welcome to the farm!” |
| Pause: Farm Map | `Barnyard - farm map.png` | map + player marker |
| Pause: Sound Options | `Barnyard - sound options.png` | Music / Sound |
| Pause: wrap to Game Menu | (`pauseR6.png` in the work dir) | 5 pages total (`L`/`R` cycle) |
| In-game dialog / talk menu | (`npc4.png`, `barn2.png` in the work dir) | choice prompt + advance |
| Credits | `Barnyard - credits.png` | staff roll (Options → Credits) |
| Code rejected | `Barnyard - rejected ZZZZ.png`, `Barnyard - rejected 0T1T.png` | no unlock, screen unchanged |

## 7. Validation evidence

**Observed (emulator).**

* `0T1S` accepted: dialog *“Congratulations! You have unlocked four new colored cows!”*
  (`Barnyard - code accepted.png`).
* Before the code, *Choose a color* for character 4 offers 3 swatches
  (`Barnyard - three colors before code.png`); after the code it offers 4, the fourth
  starred (`Barnyard - four colors after code.png`).
* `0T1T`, `YZYZ`, `YYZY`, `ZS0S`, `ZZZZ` all rejected silently: options screen returns
  unchanged, no dialog, no unlock (`Barnyard - rejected 0T1T.png`,
  `Barnyard - rejected ZZZZ.png`).
* Savestate memory reads: `0x02033D6C = 0` before/after rejects, `= 1` after `0T1S`;
  digit buffer `0x03000F30 = "0T1S"`.
* Published console button sequences at the title screen changed nothing; flag stayed 0.
* Saving the game and power-cycling preserved the 4-colour option.

**Derived (disassembly).**

* Only one code literal exists (`0x0809A46C`), compared at `0x0800CF10`.
* The digit alphabet and both wrap rules come from `0x0800D708` + the loop at
  `0x0800CE7E`/`0x0800CECA`.
* The 3-vs-4 colour count comes from `ldr r0,[0x02033D6C]` / `cmp #3` / `cmp #2` at
  `0x08017924`, `0x080183CE`, `0x080184B0`.
* The “first unlock only” gate is `if (flag == 0) { flag = 1; 0x03000EDA = 1; }`
  at `0x0800CF18`–`0x0800CF2A`.

**Inferred.**

* The extra colour applies to all four characters (“four new colored cows”); only
  character 4 was exercised end-to-end, the other three follow from the per-character
  loop being flag-bounded.
* The unlock is persisted through the game's own save (mGBA writes an 8 KiB `.sav`); the
  game reports “Saving. Do not turn the power off…” and the flag survived a restart, but
  the exact save offset and media type (SRAM vs Flash) were not determined.
* `0x03000EDA` is a “new unlock” message latch; it is written 1 but no reader was traced.

## 8. Unknowns

* Exact offset of `0x02033D6C` inside the 8 KiB `.sav` image (the profile block was not
  parsed; persistence is proven behaviourally only).
* Purpose of `0x03000EDA`; no reader located.
* Whether the 4th colour has any gameplay effect beyond appearance: it is cosmetic by
  construction — the selection picks a palette resource named
  `palettes\sprites\player_%d_%.2d.pal` (file `0x99600`), i.e. character index + colour
  index — but only the appearance was observed in play.
* The rejection indicator drawn at `0x0800CFD4` (text id `0x23`, colour `35`) is a silent
  visual cue; its exact glyph/animation was not identified — no message text is shown.
* TCRF’s page could not be fetched (403/503), so unused-content claims are limited to
  what this ROM’s own tables show.

## 9. Tooling

* `mGBA 0.10.5` (`mgba-sdl`) on `Xvfb :172` + `openbox`; `xdotool`, `scrot`/`import`,
  ImageMagick.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`.
* Python 3 + Capstone 5.0.7 for the Thumb `BL` scan (86 `strcmp` call sites) and literal
  resolution.
* Custom scripts in `/tmp/opencode/barnyard/`:
  `phase0.py` (hashes/header/logo scan), `ptrscan.py` (ROM pointer scan),
  `keysearch.py` (button-mask sequence scan), `helper.py` (key/screenshot harness),
  `enter_code.py` (menu navigation + wheel entry), plus a PNG-savestate parser
  (`gbAs` → zlib → IWRAM/EWRAM window).
* `pdftoppm` + `tesseract` to OCR the scanned USA manual (24 pages) and confirm the
  feature is documented but the code value is not.

## 10. Legal note

No ROM, extracted graphics, audio or text is redistributed. All addresses, algorithms
and the recovered literal are published here. The PNGs next to this report are menu
screenshots taken to prove the observed behaviour (the same convention as the other
reports in `roms/`).
