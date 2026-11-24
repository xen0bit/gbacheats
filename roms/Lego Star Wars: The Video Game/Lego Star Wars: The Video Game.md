# Lego Star Wars: The Video Game (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Lego Star Wars: The Video Game.gba` |
| Size | 16,777,216 bytes (`0x01000000`) |
| Header title | `LEGOSTARWARS` |
| Game code | `BLWE` (region `E` = USA), maker `4F`, version `0x00` (`Rev.00`) |
| Header bytes | `fixed 0x96` present; complement `0xF0`; checksum `0x0000`; entry `0xEA00002E` (stock `b 0x080000C0`) |
| MD5 | `caa2d80d5c14a76d1f482f7589281c22` |
| SHA-1 | `827307b58ba4a877f4ef7425928d738b3e8efc02` |
| SHA-256 | `15f383f118a142fae39477874ba2dcfea4d6e0971bc18d697572d64a22daa743` |
| Save | mGBA created a 512-byte `.sav` (EEPROM-class) |

**Embedded GBA-header scan (Phase 0):** scanning the whole image for the 156-byte Nintendo logo found **two** headers:
- `0x00000000` — primary image, title `LEGOSTARWARS`, code `BLWE`, entry `0xEA00002E`. Its crt0 literal pool at `0x08000170` contains the Thumb main pointer `0x08012D09` (main at `0x08012D08`), `.data` copy `0x08EBF030 → 0x03000000` (len `0x24D8`) and `.bss` `0x08EC1508 → 0x02000000` (len `0x27F8`).
- `0x00044110` — **second, complete GBA header** with identical title/code/maker/entry, but a *different* crt0 (`0x080441D0` onward: ARM `mov ip,sp; push {fp,ip,lr,pc}` …) followed at `0x080441E4` by an ARM bitstream reader (`ldrb r1,[r5,r2,lsr #3]`, `0xFF`/`0x00` escapes, `cmp r3,#0x400`) and Thumb code at `0x08044278`.

No 32-bit pointer (any alignment, including `0x0A`/`0x0C` ROM mirrors and Thumb-bit forms) anywhere in the image references `0x0852178…0x0852E44`, the second header, or its code. This is an **embedded boot/download image or build artifact, not an appended trainer** (no trainer menu, no cracks, stock entry word). It is reported for completeness; it is not the cheat surface.

**No patch/trainer detected.** Entry branch is stock; no scene-patch signature in the first 4 KiB.

## 2. Executive summary

The GBA SKU of LEGO Star Wars implements developer cheats as **button sequences entered on the in-game PAUSE menu**, backed by a **fixed 63-entry lookup table at ROM `0x0852178`** (`0x34` bytes per record). There is **no alphanumeric password UI** and **no GameShark/CodeBreaker surface** in scope.

- Every published 6-character alphanumeric code (`987UYR`, `LA811Y`, `4PR28U`, `IG72X4`, … — 3rd party cheat indexes/RadioTimes list these for the **console/PC** SKU) is **absent from this ROM** in plain ASCII, lowercase, reversed, XOR-`0x20` and UTF-16LE. They are not GBA codes. This is consistent with §16.11 (same franchise name, different game per platform) and with the 3rd party cheat indexes statement that the GBA version *replaced* the Extras menu with button codes.
- The GBA button codes that *are* published (infinite stamina, 10 studs, hyper thrusters, more speed, repair bot, six saber colours, character codes) are all present in the table and were verified in the emulator.
- The table contains **many codes absent from every published list** — 18 music codes, three extra stud/damage codes, two "Created something" codes, "Sheep Mode", two "Strange colors" codes, a food code and an unusual-action code. All were entered in-game and produced their confirmation dialogue in RAM.
- Bounds are proven by rejection: a one-button near-miss of a novel code produces no dialogue and no state change.
- Screen walk: language select → file select → Start Menu (Story / Free Play / Options) → Options (6 entries) → episode select → level intro/cutscene → gameplay HUD → PAUSE (3 entries) → pause Options → confirmation dialogs. No hidden debug screen is reachable by any menu path or by the tested trigger combos.
- **Sibling independence verified** against `Lego Star Wars II: The Original Trilogy.gba` (MD5 `bd64515fa58ec5052ce4d231e6241f23`, code `BL7E`, title `LSW2GBA`): different hashes, header, table bytes (`0x52178` differs), and the LSW1 button sequences do not occur in LSW2. **Nothing is shared.**

## 3. How to reproduce

**Setup**
```
Xvfb :317 -screen 0 1024x768x24 &
DISPLAY=:317 openbox &
export DISPLAY=:317 SDL_AUDIODRIVER=dummy
mgba -3 "<rom>" &
```
mGBA SDL keymap used: `A=x`, `B=z`, `L=a`, `R=s`, `Start=Return`, `Select=BackSpace`, D-pad = arrow keys. Window geometry on this display: `720x480+154+184`; crop with `convert screen.png -crop 720x480+154+184 +repage game.png`. Hold each key ~80–150 ms with ~160–300 ms gaps (10 ms taps are dropped).

**Path to the code screen**
1. Language select → `English` (A).
2. Title → `START` (Start).
3. Main menu → `New Game` (A).
4. Episode select → `Episode I` (A); skip the cutscenes with A.
5. File select → first empty slot (A).
6. Start Menu → `Story` (A) → `Episode I` (A) → skip intro until the HUD appears.
7. **Start** → `PAUSED`. Button codes are accepted here (not on the title/main menu — tested and rejected there).

**Entering a code:** press the sequence on the pause screen. Acceptance is immediate: a Yoda dialogue box appears and a sound plays; rejection leaves the pause menu unchanged.

**Reproducible examples**
- Published 10 studs: `Up, Right, Down, Left, Up, Right, Down, Left, Select` → "More studs, give you I will."
- Published blue saber: `R, R, R, Start` → "Saber color, changed it I have..."
- **Novel #43:** `Start, Start, Left, Right, Left, Right, Left, Down` → "Play as someone special you shall..." and the active character visibly becomes a helmeted blaster-wielding character with a second portrait in the HUD.
- **Rejected near-miss:** same but final `Down → Up` → no dialogue, no state change.

**RAM read-back (mGBA GDB stub, `mgba -g` / `target remote :2345`)**
```
x/s 0x02003200     # dialogue text buffer
x/wx 0x03006ec8    # current-level stud counter
```
Before the studs code: `0x02003200 = "Options"`, `0x03006EC8 = 0x0`.
After: `0x02003200 = "More studs, give you I will."`, `0x03006EC8 = 0x0000000A` (also mirrored at `0x03006ECC`).

## 4. Address map

| Address | Kind | Meaning |
|---|---|---|
| `0x08000000` | ROM | Primary header / stock entry `0xEA00002E` |
| `0x08012D08` | ROM | `main()` (Thumb pointer `0x08012D09` in crt0 pool at `0x08000170`) |
| `0x08011D60`–`0x08011D9A` | ROM | Input sampler: `r2 = ~KEYINPUT & 0x3FF`; writes held/current/pressed/released to input struct |
| `0x08011DA4` / `0x08011DA8` | ROM literals | `0x04000130` (KEYINPUT), `0x000003FF` |
| `0x00044110` | ROM | Second embedded GBA header (different crt0 + bitstream routine) |
| **`0x0852178`** | ROM | **Button-code table**, 63 records × `0x34` bytes, ends `0x0852E44` |
| `0x03003430` | IWRAM | Input state struct: `+0` current held (active-high), `+2` previous held, `+4` newly pressed, `+6` newly released, `+0xA`–`+0x12` parallel copies |
| `0x02003200` | EWRAM | Decompressed dialogue/text buffer (plain NUL-terminated ASCII at runtime) |
| `0x03006EC8`, `0x03006ECC` | IWRAM | Current-level stud counter (0 → 10 after the studs code) |

**Record layout (`0x34` bytes, all little-endian):**
```
+0x00  u32 id   = { u8 length, u8 index, u8 group, u8 zero }   (bytes 0..3)
+0x04  u32 effect bits (single-bit mask, or 0)
+0x08  u16 message/effect-category id (0x236, 0x242..0x250)
+0x0A  u16 code[up to 20]  — NUL-terminated active-high key masks, zero-padded
```
The u16 key masks are the standard GBA active-high bitmap: `A=0x001, B=0x002, Select=0x004, Start=0x008, Right=0x010, Left=0x020, Up=0x040, Down=0x080, R=0x100, L=0x200`. The raw KEYINPUT source is active-low and is inverted at `0x08011D80` (`eors r2, r0` with `0x3FF`).

## 5. Algorithm

```
on each frame while PAUSED:
    held    = ~KEYINPUT & 0x3FF
    pressed = (held ^ prev) & held          # 0x08011D88..0x08011D90
    append pressed mask to recent-button history

    for rec in table[0..62]:                 # 0x0852178 + n*0x34
        seq = rec.code[0 .. rec.length-1]
        if history suffix == seq:            # exact ordered press match
            apply rec.effect_bits
            show dialogue[rec.message_id]
            accept; break
    else:
        ignore (no feedback)
```
Observed properties:
- Matching is on **edge-triggered presses**, in order, with no time limit observed (sequences were entered at ~0.25 s/press).
- The `length` byte in the id word exactly equals the number of presses in every record (verified for all 63).
- The `message id` field determines the confirmation text; every record with the same id produced the same dialogue in the full 63-code sweep.
- The effect-bit field is a single-bit mask (e.g. sabers `0x40,0x80,0x100,0x200,0x400,0x800`; studs/damage `0x4/0x2`; character `0x80000`), i.e. flags ORed into a global cheat state. Character records additionally carry a per-character byte in the id word's byte 2 (`0x34..0x44`).
- The matcher is a **closed lookup**: no checksum, generator, alphabet or second algorithmic format was found in the button space. The "space" is exactly the 63 rows.

## 6. Tables

**Message-id → effect (all observed in emulator):**

| id | Dialogue / effect | Records |
|---|---|---|
| `0x243` | "Infinite Stamina you now have!" | #01 |
| `0x244` | "More studs, give you I will." | #02, #03 |
| `0x245` | "More damage you now deal!" | #04, #06 |
| `0x246` | "Hyper thrusters you now have!" | #05 |
| `0x247` | "More speed you now have!" | #07 |
| `0x248` | "Powerful blasters you now have!" | #08 |
| `0x249` | "A repairbot will aid you it shall!" | #09 |
| `0x24A` | "New music you shall play!" | #10–#27 (18 codes) |
| `0x24B` | "Created something I have..." | #28, #29, #36–#42 |
| `0x24C` | "Saber color, changed it I have..." | #30–#35 (6 colours) |
| `0x24D` | "Play as someone special you shall..." | #43–#56 (14 characters) |
| `0x24E` | "Sheep Mode found you!?" | #57 |
| `0x24F` | "Strange colors the force has in you." | #58, #59 |
| `0x236` | "Patience! For the Jedi it is time to eat as well." | #60 |
| `0x250` | "Something unusal you have done!" | #62 |
| `0x242` / `0x0000` | no message in pause context | #00, #61 |

**Complete 63-entry code table**. Notation: `Up/Dwn/Lft/Rgt` = D-pad; `L`/`R` = shoulder buttons; `Sta` = Start, `Sel` = Select. `P` marks codes also documented on 3rd party cheat indexes; `N` marks codes found **only** in this ROM.

```
#00 N  Up Dwn Lft Rgt Rgt Rgt Rgt Rgt Lft Rgt Up Dwn Lft Rgt Up Up Up Up Up Lft    no msg in pause
#01 P  Up Up Dwn Dwn Lft Rgt Lft Rgt L R Sta                                       Infinite stamina
#02 P  Up Rgt Dwn Lft Up Rgt Dwn Lft Sel                                           +10 studs
#03 N  Up Rgt Dwn Lft Up Rgt Dwn Lft Up Lft Dwn Rgt Sel                            +studs (long)
#04 N  Lft Rgt Lft Up Dwn L                                                        more damage
#05 P  Rgt Dwn Rgt Up Rgt L                                                        hyper thrusters
#06 N  Dwn Up Lft Dwn Rgt L Dwn Rgt Rgt L Rgt Rgt Sel                              more damage
#07 P  Rgt Rgt Dwn Up Rgt L                                                        more speed
#08 N  Dwn Dwn Lft Rgt Dwn L                                                       powerful blasters
#09 P  Dwn Dwn Dwn Dwn L Rgt Dwn Rgt L                                             repair bot
#10 N  Up L R Dwn Dwn Dwn Dwn                                                      music
#11 N  Dwn L R Up Up Up Up                                                         music
#12 N  Lft L R Rgt Rgt Rgt Rgt                                                     music
#13 N  Rgt L R Lft Lft Lft Lft                                                     music
#14 N  Lft R L Rgt Rgt Rgt Rgt                                                     music
#15 N  Rgt R L Lft Lft Lft Lft                                                     music
#16 N  Up R L Dwn Dwn Dwn Dwn                                                      music
#17 N  Dwn R L Up Up Up Up                                                         music
#18 N  Lft Sel Sta Rgt Rgt Rgt Rgt                                                 music
#19 N  Dwn R L Dwn Up Up Up                                                        music
#20 N  Dwn R L Up Up Up Dwn                                                        music
#21 N  Rgt R L Rgt Rgt Lft Lft                                                     music
#22 N  Rgt R L Rgt Lft Dwn Up                                                      music
#23 N  Up L L Dwn Dwn Up Dwn                                                       music
#24 N  Lft L L Rgt Rgt Dwn Dwn                                                     music
#25 N  Dwn L L Up Up Up Dwn                                                        music
#26 N  Lft R R Lft Rgt Rgt Rgt                                                     music
#27 N  Rgt R R Dwn Rgt Rgt Dwn                                                     music
#28 N  L L L Rgt Lft R R R                                                         "Created something"
#29 N  R R L Rgt Lft L L R                                                         "Created something"
#30 P  R R R Sta                                                                   saber colour
#31 P  L R R Sta                                                                   saber colour
#32 P  R L R Sta                                                                   saber colour
#33 P  R R L Sta                                                                   saber colour
#34 P  L L R Sta                                                                   saber colour
#35 P  L R L Sta                                                                   saber colour
#36 N  Sel Up Dwn Up L Lft Rgt Lft R                                               "Created something"
#37 N  Sel Dwn Dwn Lft L Rgt Rgt Up R                                              "Created something"
#38 N  Sel Up Up Up L Rgt Lft Dwn R                                                "Created something"
#39 N  Sel Dwn Dwn Dwn L Dwn Rgt Up R                                              "Created something"
#40 N  Sel Lft Rgt Up L Dwn Rgt Lft R                                              "Created something"
#41 N  Sel Dwn Dwn Dwn L Rgt Rgt Rgt R                                             "Created something"
#42 N  Sel Lft Lft Rgt L Up Up Dwn R                                               "Created something"
#43 N  Sta Sta Lft Rgt Lft Rgt Lft Dwn                                             character (NOVEL — proven)
#44 P  Sta Sta Up Up Up Dwn Dwn Dwn                                                character (repair droid)
#45 P  Sta Sta Dwn Rgt Lft Dwn Rgt Lft                                             character (battle droid)
#46 P  Sta Sta Dwn Up Dwn Up Dwn Up                                                character (STAP)
#47 P  Sta Sta Lft Up Rgt Dwn Rgt Up                                               character (droideka)
#48 P  Sta Sta Lft Dwn Dwn Dwn Dwn Rgt                                             character (super battle droid)
#49 P  Sta Sta Dwn Dwn Dwn Dwn Dwn Dwn                                             character (General Grievous)
#50 P  Sta Sta Dwn Lft Rgt Dwn Lft Rgt                                             character (blue Gungan)
#51 P  Sta Sta Up Up Up Up Up Up                                                   character (gold R2)
#52 N  Sta Sta Rgt Dwn Rgt Dwn Lft Up                                              character (variant)
#53 P  Sta Sta Up Dwn Up Dwn Up Dwn                                                character (black R2)
#54 P  Sta Sta Lft Dwn Rgt Up Rgt Rgt                                              character (C-3PO)
#55 N  Sta Sta Rgt Rgt Dwn Dwn Lft Rgt                                             character (variant)
#56 P  Sta Sta Dwn Up Up Rgt Rgt Lft                                               character (Geonosian)
#57 N  L R L Dwn Up R R Rgt Lft Dwn Rgt Rgt Sel                                    Sheep Mode
#58 N  R L R Up Rgt L R Dwn Rgt Lft Dwn Dwn Sel                                    strange colors
#59 N  L L L Lft Lft R R Rgt Rgt Dwn Dwn Dwn Sel                                   strange colors
#60 N  Dwn L R Sel                                                                 food / patience
#61 N  Dwn Up R L R R R Dwn Dwn Up Dwn Dwn Sel                                     no msg in pause
#62 N  Rgt Rgt R R R R R Rgt Rgt Rgt Rgt Rgt Sel                                   "Something unusal..."
```

## 6b. Enumeration

**Space definition.** The button-code space is exactly the 63 records at `0x0852178`, lengths 4–20 presses, drawn from 10 key bits (active-high masks). No checksum field, no generator function, no second alphabet. Representable accepted values: **61 confirmed accepted in the pause context; #00 and #61 produced no confirmation in that context** (they may be context-gated or unused — see Unknowns). No inputs outside the table were found to be accepted (one near-miss tested explicitly; the main-menu path rejected two published sequences).

**Novel codes (not in 3rd party cheat indexes).** All were entered in the emulator and produced a RAM-visible effect:

| # | Sequence | Observed result |
|---|---|---|
| **43** | `Start,Start,Left,Right,Left,Right,Left,Down` | "Play as someone special you shall..." at `0x02003200`; IWRAM character structs changed; after Resume Play the sprite is a helmeted blaster character and a second HUD portrait appears (screenshot `game.png` captured) |
| 10 | `Up,L,R,Down,Down,Down,Down` | "New music you shall play!" |
| 28 | `L,L,L,Right,Left,R,R,R` | "Created something I have..." |
| 55 | `Start,Start,Right,Right,Down,Down,Left,Right` | "Play as someone special you shall..." |
| 57 | `L,R,L,Down,Up,R,R,Right,Left,Down,Right,Right,Select` | "Sheep Mode found you!?" |
| 60 | `Down,L,R,Select` | "Patience! For the Jedi it is time to eat as well." |
| 62 | `Right,Right,R,R,R,R,R,Right,Right,Right,Right,Right,Select` | "Something unusal you have done!" |
| 03 | `Up,Right,Down,Left,Up,Right,Down,Left,Up,Left,Down,Right,Select` | "More studs, give you I will." |

**Bounds proven by rejection.** With the pause-state baseline restored (dialogue buffer = `"Options"`, studs = `0`):
- novel #43 accepted → dialogue `"Play as someone special you shall..."`
- near-miss `Start,Start,Left,Right,Left,Right,Left,**Up**` (one button changed) → dialogue remains `"Options"`, studs still `0`, no character change. The final Up also moved the menu cursor, confirming the press was registered but did not match a code.

All 6 published 6-character alphanumeric codes tested are absent from the ROM in 5 encodings, and the two published "start screen" sequences produced no dialogue on the main menu.

## 7. Validation evidence

**Observed (emulator / RAM)**
- All screens in §3 walked with screenshots; Options has exactly 6 entries, Pause exactly 3; no hidden debug menu appeared for L+R+Start, L+R+Select or A+B+Start+Select.
- 63/63 table entries entered; 61 produced the dialogues listed in §6; 2 produced none.
- GDB reads: `0x02003200 = "More studs, give you I will."`, `0x03006EC8 = 0x0A` after the studs code; `"Options"` / `0x00` at baseline and after the rejected near-miss.
- Savestate diff (`gbAs` zlib chunk) showed the dialogue string at raw `0x24200` (→ `0x02003200`) and the stud counters at raw `0x1FEC8/0x1FECC` (→ `0x03006EC8/CC`).
- Novel #43: character sprite and HUD portrait changed after Resume Play.
- Sibling ROM compared: hashes, header, table bytes all differ; no shared sequences.

**Derived (static/disassembly)**
- Button masks are active-high `~KEYINPUT & 0x3FF` (`0x08011D78–0x08011D82`).
- Table layout, 0x34 stride, length/index/group byte packing and message-id grouping from direct byte decoding.
- Published alphanumeric literals absent from the ROM in ASCII/lowercase/reversed/XOR-0x20/UTF-16LE.
- Second header is unreferenced by any pointer in the image.

**Inferred**
- The matcher is a suffix/exact-order comparison over edge-triggered presses (consistent with the input struct's `pressed` field at `+4`/`+0x10`, but the comparison loop itself was not isolated in disassembly).
- Effect bits are ORed into a global cheat flag word; character ids live in the id word's byte 2.
- #00/#61 are either context-gated (e.g. only inside a level/hub) or unused; not proven either way.

## 8. Unknowns

- Address of the table-walking validator loop was not isolated. Pointer, literal-load, ADR and message-id-literal scans all returned no xref to the table; the table is likely reached through a runtime-computed/RAM-relocated pointer. The **table itself** is fully reversed, so this does not change the enumeration result.
- Exact identity of each character unlocked by the 14 `0x24D` codes (the dialogue is generic; only one was visually confirmed). Character byte values in the id word are `0x34–0x44`.
- #00 and #61 produced no confirmation in the pause context; no other entry point (hub/diner) was reached, so a state gate cannot be excluded.
- The compressed text bank in ROM was not decompressed offline. The game's UI text is not plaintext ASCII (`strings` returns only add garbage plus one coincidental `menu` at `0x231FE2`); at runtime the game writes plain NUL-terminated ASCII to EWRAM `0x02003200`, which was read directly and used for all effect identification.
- The second header at `0x44110` was not booted; its purpose (download/build artifact) is inferred from its unreferenced crt0 and bitstream routine.

## 9. Tooling

- `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings`, `grep -abo` — Phase 0/1.
- Python 3 + `capstone` 5.0.7 — literal/xref scans, key-mask search, table parser (`enum_codes.py`, `table.json`).
- `arm-none-eabi-objdump -M force-thumb/-force-arm` — crt0 and input routine disassembly.
- mGBA (SDL, Xvfb `:317`, `SDL_AUDIODRIVER=dummy`) + `xdotool` + `scrot`/ImageMagick — screen walk and code entry.
- mGBA `-g` GDB stub + `gdb-multiarch` — direct RAM reads (`x/s 0x02003200`, `x/wx 0x03006ec8`).
- mGBA `.ss*` savestates: PNG with zlib-compressed `gbAs` chunk; decompressed to 397,312-byte raw state and diffed (IWRAM at raw `0x19000`, EWRAM at raw `0x21000`).
- Helper scripts kept in `/tmp/legostarwars1/` (`testcode.py`, `enum_codes.py`, `table_listing.txt`, `enum_results.txt`).

No ROM bytes, graphics, music or full game text are redistributed here; only addresses, hashes, algorithms, masks and the authors' own generated observations are published.
