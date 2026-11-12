# Crash Bandicoot Purple: Ripto's Rampage (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Crash Bandicoot Purple: Ripto's Rampage.gba` |
| Size | 16,777,216 bytes (16 MiB) |
| Header @ `0x000000` | title `CRASH PURPLE`, code `BD4E`, maker `7D`, version 0, complement `0x6E` |
| Entry word | `0xEA00002E` = `b 0x080000C0` (stock branch, no cracktro) |
| Header checksum | stored `0x0000` (rebuilt-header artifact; complement byte is correct) |
| MD5 | `a9c93a07964aa816a8e226ae0c735a41` |
| SHA-1 | `35d1c8c90890bf7ce66306e6c06a3676a723dcf3` |
| SHA-256 | `ef59bc4de5806ba142aa26a7933a23bbfd14d33c4639ca832906b3d0dcd46fce` |

Nintendo-logo scan (156-byte logo at header+4) finds three GBA headers:

| File offset | Title | Code | Maker | Entry | Interpretation |
|---:|---|---|---|---|---|
| `0x000000` | `CRASH PURPLE` | `BD4E` | `7D` | `0xEA00002E` | retail game image |
| `0x0F07BF8` | `XXXXXXXXXXXX` | `XXXX` | `VV` | `0xEA00002E` | embedded multi-boot stub |
| `0x0F29C50` | `XXXXXXXXXXXX` | `XXXX` | `VV` | `0xEA00002E` | embedded multi-boot stub |

The two `XXXX/VV` headers are 136 KB apart inside the image; they are GBA-format stubs with placeholder titles, not alternate games. **No trainer, cracktro or appended code was found.**

This image is *not* byte-identical to the Crash Purple half of the `2-in-1 Crash & Spyro Superpack` image (that half has MD5 `d847123368921901e351431e809cbb40`). All addresses below were verified in THIS image.

## 2. Executive summary

The game has a developer cheat-code entry screen, reached from the **Mode menu by holding L + R**. It opens a 10-slot keypad with a 32-symbol alphabet (21 consonants, digits 0–9, END) and validates the typed string against a **22-entry plaintext table**. There is no checksum, no XOR key, no alphabet permutation and no generator: the validator is a linear `strlcpy` + 22 × `strcmp` chain.

The table at `0x0806AB68` contains, in order:
`CR4SH G3CK0 C0FF33 WH1STL3 PH0N3T4G STR4WB3RRY WVMP4FR00T PR3S3NTZ L4MPP0ST SW1NGS3T K1LL4Z C4M0 CVTZ CR3D1TS ST4CY R0BG C0L1N J0NNY TR4V1S SVNB1R J450N BR3NT`.

Dynamically verified in mGBA:

* **L + R** at the Mode menu opens the keypad; the 8×4 grid was learned by pressing A on 31 cells and reading the entry buffer at `0x0201AF3C`.
* Entering **`TR4V1S`** changes the palette (published effect: grey tint) — palette RAM changed in 45 entries, all in the object-palette bank.
* Entering **`J450N`** is accepted and changes the palette (published effect: green pants) — 43 palette entries changed.
* Entering the **GameFAQs spelling `J45S0N`** produces **no palette change**: it is rejected. The ROM's real entry is `J450N`; IGN and Bandipedia list `J450N` correctly, so this is a GameFAQs transcription error, not a novel code.
* The accepted set is **closed at 22 table entries**: the validator is 22 exact `strcmp`s, and every table entry appears in at least one published list. No unpublished code can be minted for this ROM (see §6b).
* **`SW1NGS3T`** starts the hidden **Spyro Party USA** mini-game; after entry the EWRAM contains a complete `CRASH-PARTY` overlay title block and `Spyro Party USA`, `Interactive Game`, `Start game`, `Session %d`, `Round %d`, `You got a gem!`. The mini-game is embedded and functional, but its strings are not visible to `strings` on the ROM (they are loaded from a compressed bank at run time).
* The 10-character entries **`STR4WB3RRY`** and **`WVMP4FR00T`** cannot be submitted: with all 10 slots filled, the END/ACCEPT cell stops responding (observed: buffer stays `STR4WB3RRY`, no result screen). Deleting one character restores submission. They are in the table, but are unreachable through the retail keypad.

No GameShark/CodeBreaker/memory-edit codes were used.

## 3. How to reproduce

```
Xvfb :265 -screen 0 1024x768x24 &
DISPLAY=:265 openbox &
DISPLAY=:265 SDL_AUDIODRIVER=dummy mgba -3 "Crash Bandicoot Purple: Ripto's Rampage.gba" &
```

mGBA 0.10.5 SDL keymap: **A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows**. Hold 60–150 ms; 45–70 ms moves one keypad cell.

Path to the feature:

1. Boot → `Press Start` → Start.
2. Slot select (`LOAD SAVE GAME` / `New Game` / `Erase Game`) → choose a slot with A.
3. Mode menu (`Story Mode / Party Mode / Trading / CREDITS`).
4. Hold **L + R** ≈ 0.9 s → keypad overlay (`You entered: ----------`, 8×4 symbol grid, `back` / `accept`).
5. D-pad moves the grid cursor (B deletes the last slot; A appends the highlighted symbol). Move to the END cell (row 3, col 7) and press A to submit.

Savestates (`Shift+F1`, `.ss1`) make each test a short key sequence; states saved immediately after L+R, after typing, and after submit were parsed with a zlib/PNG `gbAs` reader. All evidence below is text/RAM/address based; no screenshots were used.

Tests performed:

| Input | Result |
|---|---|
| `TR4V1S` | accepted; palette entries 464–510 changed |
| `J450N` | accepted; 43 palette entries changed |
| `J45S0N` (published spelling) | rejected; palette identical to the invalid-code case |
| `ZZZZZ` | rejected |
| `SW1NGS3T` | accepted; Spyro Party USA overlay loaded |
| `CR4SH` | submitted; table branch and `+100` code at `0x08032F0E` derived, see §8 |
| `STR4WB3RRY` (10 chars) | END does not submit; buffer unchanged |
| same string minus one char | submission occurs (result screen) |
| L+R at Mode menu | keypad opens (repeated) |
| L+R held through boot/title | did not start the mini-game in this image |
| Up, Down, L, R, Select at Mode menu (70 ms and 150 ms holds) | did not trigger the credits (no credits text loaded) |

## 4. Address map

`rom_address = 0x08000000 + file_offset`.

| Item | ROM address | File offset | Notes |
|---|---:|---:|---|
| Code table (first entry `CR4SH`) | `0x0806AB68` | `0x6AB68` | 22 NUL-terminated strings, 4-byte padded |
| Table end / next data | `0x0806AC30` | `0x6AC30` | `0x00000030` |
| Validator entry | `0x08032E78` | `0x32E78` | `push {r4-r6,lr}; sub sp,#0xA0`; 22 × `strcmp` |
| Validator wrapper (single-shot gate) | `0x080334B8` | `0x334B8` | checks `[obj+0x44]`, then `bl 0x08032E78` |
| `strcmp` | `0x08047298` | `0x47298` | word-at-a-time comparison |
| String copy/length helper | `0x080472F4` | `0x472F4` | used on the keypad buffer before comparison |
| Keypad buffer (observed) | `0x0201AF3C` | — | 10 ASCII chars, `-` padded |
| Keypad object/overlay data (observed) | `0x0201AF00`–`0x0201AF50` | — | pointers `0x0201AEE8`, `0x0201AF48`, `0x0201AF2C` |
| Reject branch | `0x0803346C` | `0x346C` | message pointer `0x0806F9C8` → `"Code not recognized"` @ `0x080740A1` |
| Used branch | `0x08033074` | `0x3074` | message pointer `0x0806F9E4` → `"Code already used"` @ `0x08074151` |
| `SW1NGS3T` branch | `0x08033204` | `0x3204` | calls `0x0803AE94` (scene/overlay 23) |
| Palette-effect helper | `0x080342A4` | `0x342A4` | called with palette pointer `0x08085E8C`, length `0x100` |
| Script/scene runner | `0x0801F09C` | `0x1F09C` | takes a script pointer (credits script `0x08069378`) |
| Wumpa field setter | `0x08017664` | `0x17664` | `str [r0+0x6c]=r1`, clamps to `0x0F27` |
| Global object used by wumpa branches | `0x02006DE0` | — | literal at `0x080177E8`; first bytes hold last entered code |
| `You entered:` text | `0x0807406C` | `0x7406C` | label record |
| `Code not recognized` | `0x080740A1` | `0x740A1` | record starts with `0x04` |
| `Code already used` | `0x08074151` | `0x74151` | record starts with `0x04` |
| `Wumpty Wump! %d free wumpa!` | `0x08074168` | `0x74168` | record starts with `0x04` |
| `Card Smack! You got card: %s` | `0x0807418D` | `0x7418D` | record starts with `0x04` |
| Party mini-game select strings | `0x0806FD6C` | `0x6FD6C` | `SELECT MINI GAME`, `Choose Mini-Game` @ `0x6FD84` |
| Party/Shop mini-game name table | `0x08072078`–`0x080725F8` | `0x72078` | names listed in §6.3 |
| Hidden test level `Jetpack Test` | `0x08072194` | `0x72194` | one pointer xref: `0x080721CC` (inside the same table) |
| Hidden test level `Crash 2 Test Level : Tiki Torture` | `0x080721A8` | `0x721A8` | same table; no code xref |
| Trading link strings | `0x08072818` | `0x72818` | `Link 2 Game Paks and select from the same world` |
| Trading state strings | `0x080727AC` / `0x080727C4` | `0x727AC` | `Waiting for Trader` / `Trade Successful` |
| Pause menu strings | `0x0806FDD4`–`0x0806FE75` | `0x6FDD4` | `PAUSE`, `Options`, `Resume`, `Restart`, `Quit Game`, `Music`, `Sleep` |
| Header stubs | `0x0F07BF8`, `0x0F29C50` | — | `XXXX`/`VV`, `b 0x080000C0` |

## 5. Algorithm

### 5.1 Keypad

The keypad is an overlay on the Mode menu. Its stored alphabet is a plain ASCII grid, observed cell by cell by pressing A and reading `0x0201AF3C`:

```
row 0 (y=0):  B  C  D  F  G  H  J  K
row 1 (y=1):  L  M  N  P  Q  R  S  T
row 2 (y=2):  V  W  X  Y  Z  0  1  2
row 3 (y=3):  3  4  5  6  7  8  9  END
```

* A appends the highlighted character into `buf[0..9]`; B deletes the last one.
* The buffer is padded with `-` (`0x2D`), e.g. `CR4SH-----`.
* Submission copies the *typed prefix* (up to the current length) to a NUL-terminated stack string, then compares.
* `END` submits only while `len < 10`. With `len == 10` the cell does not respond (observed).
* There is no case folding or glyph remapping: the stored code is the ASCII text.

### 5.2 Validator

`0x08032E78` is a `strlcpy`/`strlen`-style copy followed by a linear comparison chain. Reconstructed:

```c
int validate(obj *o) {
    char s[0xA0];
    copy_string(s, o->buffer);            // typed prefix only
    if (!strcmp(s, "CR4SH")) {
        if (test_used(o, 0)) return show_used();
        set_used(o, 0);
        set_message(...); add_wumpa(100);
    } else if (!strcmp(s, "G3CK0")) {
        if (test_used(o, 1)) return show_used();
        set_used(o, 1);
        set_message(...); add_wumpa(200);
    } else if (!strcmp(s, "C0FF33")) {
        ... add_wumpa(500);
    } else if (!strcmp(s, "WH1STL3")) { ... card("Mayan Jungle"); }
    else if (!strcmp(s, "PH0N3T4G")) { ... card("Sewers"); }
    else if (!strcmp(s, "STR4WB3RRY")) { ... }
    ...
    else if (!strcmp(s, "SW1NGS3T")) { run_scene(23); }   // 0x0803AE94
    else if (!strcmp(s, "CR3D1TS")) { run_scene(credits); } // script 0x08069378
    else if (!strcmp(s, "J450N")) { palette_effect(...); }
    else if (!strcmp(s, "BR3NT")) { palette_effect(...); }
    else show_message("Code not recognized");
    return 1;
}
```

The per-code "used" test/set is a bitfield at `[obj+0x9c]` (`0x08017114` tests bit `r1`, `0x08017120` sets it); the wrapper at `0x080334B8` runs the validator once per keypad object, gated by `[obj+0x44]`.

The special-effect branches share the same shape:

```
bl 0x08034424                  ; detach/replace the current UI
ldr r1,=0x08085E8C             ; palette/effect data
movs r2,#0x100
bl 0x080342A4                  ; apply palette/colour effect
ldr r0,=<script pointer>
bl 0x0801F09C                  ; run scene/script
```

`CR3D1TS`'s script is `0x08069378`; `SW1NGS3T` uses the scene call `0x0803AE94` which passes scene id 23 and triggers the `CRASH-PARTY` overlay.

## 6. Tables

### 6.1 Code table (`0x0806AB68`, exact file bytes)

| # | Code | Address | Published effect (GameFAQs) | Dynamic status |
|---:|---|---|---|---|
| 0 | `CR4SH` | `0x0806AB68` | +100 wumpa | submitted; branch derived (§8) |
| 1 | `G3CK0` | `0x0806AB70` | +200 wumpa | not individually typed |
| 2 | `C0FF33` | `0x0806AB78` | +500 wumpa | not individually typed |
| 3 | `WH1STL3` | `0x0806AB80` | card: Mayan Jungle | table + branch |
| 4 | `PH0N3T4G` | `0x0806AB88` | card: Sewers | table + branch |
| 5 | `STR4WB3RRY` | `0x0806AB94` | bombs on R | **unreachable**: 10 chars |
| 6 | `WVMP4FR00T` | `0x0806ABA0` | purple tint | **unreachable**: 10 chars |
| 7 | `PR3S3NTZ` | `0x0806ABAC` | grey tint | table + branch |
| 8 | `L4MPP0ST` | `0x0806ABB8` | orange tint | table + branch |
| 9 | `SW1NGS3T` | `0x0806ABC4` | Spyro Party USA | **observed** (§6.2) |
| 10 | `K1LL4Z` | `0x0806ABD0` | green pants | table + branch |
| 11 | `C4M0` | `0x0806ABD8` | "Gung ho bandicoot" message | table + branch |
| 12 | `CVTZ` | `0x0806ABE0` | all cutscenes | table + branch |
| 13 | `CR3D1TS` | `0x0806ABE8` | credits | table + branch |
| 14 | `ST4CY` | `0x0806ABF0` | black pants + bombs | table + branch |
| 15 | `R0BG` | `0x0806ABF8` | orange pants | table + branch |
| 16 | `C0L1N` | `0x0806AC00` | orange tint | table + branch |
| 17 | `J0NNY` | `0x0806AC08` | black pants + bombs | table + branch |
| 18 | `TR4V1S` | `0x0806AC10` | grey tint | **observed**: palette change |
| 19 | `SVNB1R` | `0x0806AC18` | bombs on R | table + branch |
| 20 | `J450N` | `0x0806AC20` | green pants | **observed**: palette change |
| 21 | `BR3NT` | `0x0806AC28` | orange pants | table + branch |

Published lists give the entry `J45S0N`; the ROM has `J450N`. `J45S0N` was typed in mGBA and produced no palette change (rejected).

### 6.2 Hidden mini-game (SW1NGS3T)

After `SW1NGS3T`, EWRAM contains:

```
0x020000A0  "CRASH-PARTY 00007D"
0x0200A131  "Spyro Party USA"
0x0200A141  "Interactive Game "
0x0200A159  "Universal Interactive, Inc."
0x0200A179  "Spyro, Crash Bandicoot and related characters"
0x0200A1E9  "Developed by"
0x0200A1F6  "Vicarious Visions, Inc."
0x0200A210  "LICENSED BY NINTENDO"
0x0200A71D  "nederlands"  (language list)
0x0200A93A  "Try again?"
0x0200A965  "Round %d"
0x0200A96E  "Session %d"
```

This is a complete embedded game overlay, not present in the plain ROM string table (its text bank is compressed and loaded only when scene 23 runs). Entering the code is the only route found in this image; holding L+R through boot/title did not trigger it in our tests.

### 6.3 Party/shop mini-game name table (`0x08072078` onward)

The table includes (addresses in parentheses):

`Crash Purple`, `Buy Card 1/3/4/5`, `Shop`, `Spinning Wheel Game 1/2/3`, `Mystery Game 1/2`, `Shell Game 1/2/4` (no 3), **`Jetpack Test` (`0x08072194`)**, **`Crash 2 Test Level : Tiki Torture` (`0x080721A8`)**, `World 1`, `World 1b`, `Grin and Bear it`, `Sheep Stampede`, `Tanks for the Memories`, `Crashin' down the River`, `Chopper Stopper`, `Castle Chaos`, `Bonus: Crate Smash`, `Bonus: Crunch Time`, `Bonus: Freefallin'`, `Jump, Crash, Jump!`, `World 2a/2b`, `Crash and Burn`, `Polar Express`, `Blizzard Ball`, `Sheep Patrol`, `Frigid Waters`, `Bonus: Crate Step`, `Bonus: Crate Smash`, `Tiny Takeover`, `Bonus: Pumpin' Iron`, `World 3a/3b`, `Tankin' over the world`, `Chop 'til you Drop`, `Rocket Power`, `Bat Attack`, `Nina`, `World 4a/4b`, `Sheep Shuttle`, `Up, up, and away`, `Tanks 'R Us`, `Bridge Fight`, `Bats in the Belfry`, `Ripto's Magical Mystery Tour`, `Bonus: Weightlift`, `World 5a`, `Bonus: Crate smash`, `Crash at the Controls`, `Bear with Me`, `Tech Deflect`, `Tank You Come Again`, `Bat to the Future`, `Ballistix`, `Ship Shuffle`.

The two test-level names have exactly one pointer reference each (the table entry itself, `0x080721CC`), so no code path in this image targets them directly. The live Party world map showed the worlds `Wumpa Jungle` and `Grin and Bear it`; its warp pads were locked in the fresh save, so the mini-game select never opened. `SELECT MINI GAME` / `Choose Mini-Game` exist at `0x0806FD6C`/`0x0806FD84`.

### 6.4 Link / trading surface

The Trading screen reached from the Mode menu contains the world list and the strings `Link 2 Game Paks and select from the same world` (`0x08072818`), `Waiting for Trader` (`0x080727AC`) and `Trade Successful` (`0x080727C4`). This is a peer-to-peer card trading mode requiring a second cartridge; no code/password is exchanged, and no single-cart unlock is gated on it in the strings or tables examined. The trading card shop/mini-games are the only card unlock route.

## 6b. Enumeration

**Space definition.** Input alphabet is the 32 keypad symbols; input length is 0–10 (END is a cell, not a character), so the nominal string space is `32^10 ≈ 1.13×10^15`. However the validator performs only exact `strcmp` against 22 NUL-terminated constants; there is **no checksum, no key table, no bit packing, no alphabet substitution and no generator** (all 22 literal loads in `0x08032E78`–`0x0803490` resolve inside `0x0806AB68`–`0x0806AC28`). Therefore the accepted set is exactly the table: **22 strings**, and every other input is rejected without transformation.

**Enumeration method.** The table was dumped end-to-end from the ROM (addresses in §6.1); the validator's literal loads were enumerated with a PC-relative literal scanner to prove the set is closed at 22. The keypad grid was enumerated cell-by-cell at run time (31 cells; END handled separately), confirming the alphabet is exactly the 32 ASCII symbols above.

**Novel-code result: none can exist.** The validator is a pure exact-string table lookup (22 × `strcmp`, no checksum, no key, no generator), so the accepted set is exactly the 22 constants at `0x0806AB68`–`0x0806AC28`. Every one of those 22 appears in at least one published list: the GameFAQs page has 22 rows covering the whole table (with one spelling error, `J45S0N` for `J450N`), and IGN/Bandipedia carry the same codes including the correct `J450N`. A value not in the ROM table is rejected regardless of its checksum (there is no checksum to satisfy), so there is **no unpublished accepted code to mint** for this title. The deliverable here is therefore the closure proof plus a corrected published entry, not a forged novelty.

One published-list byte was corrected where it mattered: `J45S0N` was typed in mGBA and produced **zero** effect-palette change (rejected), while `J450N` was accepted and produced a 43-entry palette delta. That is a real game-verified correction to the GameFAQs list, but `J450N` is published elsewhere and is not claimed as novel.

**Bounds proven by rejection.**

* `ZZZZZ` (valid alphabet, wrong string) → submitted, rejected; no palette effect.
* `J45S0N` (published typo) → submitted, rejected; no palette effect.
* `STR4WB3RRY` at 10 characters → END does not submit at all (UI bound); with 9 characters submission works but the string is rejected. This proves the keypad's length bound and makes `STR4WB3RRY` and `WVMP4FR00T` unreachable in the retail UI.
* An 11-character input is not representable (10-slot buffer).

**Negative results, bounded.** No second code entry surface was found: a literal search for `SH33P`, `SP4RX` (the Spyro Orange table) finds nothing in this image; the only `strcmp` chain that consumes the keypad buffer is `0x08032E78`; no checksum/key tables appear in that function. Button codes were searched as `u16` mask sequences for Up/Down/L/R/Select and tested live; they did not trigger the credits path in this image. The boot L+R shortcut was tested and did not start the mini-game; the `SW1NGS3T` password does.

## 7. Validation evidence

**Observed (mGBA, savestate RAM, this image)**

* L+R at the Mode menu opens the keypad; repeated on four separate runs.
* Keypad alphabet grid sampled by pressing A on 31 cells and reading `0x0201AF3C`; buffer is `-`-padded ASCII.
* `TR4V1S` accepted; palette entries 464–510 changed to a desaturated green/grey ramp (palette RAM `0x05000000`, mirrored in `.ss1` at offset `0x800`).
* `J450N` accepted; 43 palette entries changed relative to the invalid-code state.
* `J45S0N` and `ZZZZZ` submitted but produced no effect-palette change (rejected).
* `SW1NGS3T` accepted; EWRAM loaded the `Spyro Party USA` / `CRASH-PARTY 00007D` overlay and mini-game strings (§6.2).
* 10-character buffer: pressing END left the buffer and screen unchanged; deleting one character allowed submission.
* Mode menu, Trading world list (`Wumpa Jungle`, `Grin and Bear it`, link strings) and Party world map reached; Party warp pads locked in a fresh save.
* Title (`Press Start`), slot select (`LOAD SAVE GAME`, `New Game`, `Erase Game`) reached.

**Derived (disassembly)**

* `0x08032E78` is a copy + 22 × `strcmp` validator; all 22 literal pointers are in `0x0806AB68`–`0x0806AC28`.
* Per-code used bits at `[obj+0x9c]` via `0x08017114`/`0x08017120`; wrapper once-per-object gate at `0x080334B8` (`[obj+0x44]`).
* `CR4SH`/`G3CK0`/`C0FF33` add 100/200/500 to `[obj+0x6c]` (`0x08032F0E`, `0x08032F7A`, `0x08032FD8`), then call `0x08017664`.
* `SW1NGS3T` calls `0x0803AE94` (scene id 23); `CR3D1TS` runs script `0x08069378`.
* Palette/screen branches call `0x08034424`, `0x080342A4(0x08085E8C, 0x100)`, then a script function.
* The 10-character strings exist in the table; the keypad buffer is 10 slots and the accept cell is length-gated.

**Inferred**

* Effect labels in §6.1 are the published GameFAQs labels; only `TR4V1S`, `J450N`, `SW1NGS3T` were positively observed here.
* `CR4SH` wumpa `+100` is derived from the branch but was not isolated in RAM: the state diff after submitting it showed no `+100` field, so the counter is outside the heap region compared, or the branch was gated by a previously set used bit. This is explicitly an unresolved dynamic check, not a rejection.
* `J450N`'s 43-entry palette delta is consistent with the published "green pants" effect (object palette), but the exact affected sprite was not visually inspected (media ban).
* The Mode menu's Story Mode entry did not transition from a freshly created slot with synthetic input in this harness; Party and Trading did. The cause (save-initialisation gate vs. harness timing) was not isolated; the pause/options screens therefore were not reached, but their strings (`PAUSE`, `Resume`, `Restart`, `Quit Game`, `Options`, `Music`, `Sleep`) exist at `0x0806FDD4`–`0x0806FE75`.

## 8. Unknowns

* Exact RAM address of the persistent wumpa counter; the `+100` path is derived but not observed as a numeric delta.
* Whether the used bits persist in the 512-byte EEPROM save after a power cycle (they are in RAM and are reset by a savestate load).
* Whether `STR4WB3RRY` / `WVMP4FR00T` are reachable by a link-mode or patched path; the strings and handler branches exist but the retail keypad cannot submit 10 characters.
* What the Story Mode gate is in a freshly created save, and whether the pause/options screens behave as the string inventory suggests.
* Whether the two `XXXX/VV` stub images are used by any multi-boot route; they were not executed.
* Whether `J450N`'s palette change affects only the player sprite or the whole scene.

## 9. Tooling

* `mGBA 0.10.5` (SDL) under `Xvfb :265` + `openbox`, driven by `xdotool`; window selected by PID, not by name.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for the validator, branches and palette calls.
* Python 3: PC-relative literal scanner, pointer scan, keypad driver, `.ss1` parser (PNG `gbAs` chunk → `zlib.decompress` → 397,312-byte state; IWRAM `0x19000`, EWRAM `0x21000`, palette `0x800`).
* `parse_ss.py`, `drive.py`, `enter.py` in `/tmp/opencode/crashpurple`.

## 10. Legal note

Only hashes, addresses, algorithms, short code strings and behavior are published. No ROM, graphics, audio or extended game text is redistributed. The ROM is required to reproduce the dynamic steps.
