# Bookworm (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Bookworm/Bookworm.gba` |
| Size | 4,194,304 bytes (4 MiB, `0x400000`) |
| Header title | `BOOKWORM` |
| Game code | `BKWE` |
| Maker code | `5G` |
| Software version | 0 (Rev.00) |
| Entry word | `0xEA00002E` (stock `b 0x080000C0`) |
| Fixed byte `0xB2` | `0x96` |
| Complement check | `0x3C` |
| Header checksum | `0x0000` (normal artifact of a rebuilt header; complement is sane) |
| MD5 | `c64b677831500e85222d85c70e2d23b6` |
| SHA-1 | `c45d588f8aade81152ae789d62316db9138452b8` |
| SHA-256 | `3a0ab3e7ff4d9e2c2ebcfe3367787175c1ce8b38447c86c12278392da2367780` |

Embedded-header scan: the 156-byte Nintendo logo occurs exactly once, at file offset `0x4` (header base `0x0`). This is a single-image cartridge: no 2-in-1 shell, no second header, no appended trainer, no cracktro. The first 4 KiB are the stock crt0; the tail of the ROM is `0xFF` padding.

## 2. Executive summary

**This build has no in-game password, button-code, or hidden/debug-menu system.** The conclusion is bounded by exhaustive static enumeration of the ROM's only input path plus a walked menu inventory, not by a failed search:

* All keypad input in the 4 MiB image is read at **three** `ldrh` sites, all inside one routine at `0x08002DB8`. The only other way to obtain key state would be a literal `0x04000130`, which does not occur anywhere in the ROM, or a `0x04000100 + 0x30` construction, which also does not occur.
* That routine edge-detects each of the ten buttons and dispatches to callbacks installed per screen at `0x03002954` (direction repeat), `0x03002958` (release) and `0x0300295C` (press). There are **four** distinct callback sets (title, file-select/menus, gameplay, name entry). Three of the four press callbacks are a bare `bx lr`; the only real one (`0x0800D0A0`) acts on A alone. No callback keeps a press history, ring buffer, or chord mask. A multi-button sequence therefore has nowhere to be matched.
* The only text-entry surface is the profile name field. It offers exactly the 62 alphanumeric symbols `abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789` (literal at `0x151DB0`) plus `del`/`end` cells, and caps at 8 characters. The name buffer `0x03004A97` is referenced only by the name-entry code; the copied profile record at `0x03004A20` is used for display/save/high-score comparison of *scores*, never of name bytes. The ROM contains **two `strcmp` calls in total** (`0x0801EC28`, `0x0801EC34`), both in the decimal-number parser comparing against `"C"` and `"."`. No user string is ever compared with a constant.
* Published lists agree there is nothing to publish: VGChartz lists **0 cheats**, SuperCheats has no GBA cheats/codes (only FAQs), GameFAQs has no cheats page for this title (and no Wayback snapshot of one), and TCRF documents **only the hidden development text**, no codes or debug menu. There is consequently no published code to test; every candidate surface was tested directly.

The one genuinely hidden, developer-authored artifact is the **default high-score / "Best Words" table**, which contains PopCap staff handles instead of player names: `Alison/Nick/John/Jeff/Pamela` (5,000–1,000 points) and `Warpig/Bfiete/Tuco/Sen/Don` tagged `design/code/test/art/biz` (500–100 points). `High Scores → B Reset → Yes` restores these rows. It is an easter egg, not a cheat: it changes no gameplay state. The second developer artifact is the large trace-printf string block at `0x0F6BB8`–`0x0F7C00`, documented by TCRF and also present here; those strings are unconditional logging, not a menu.

## 3. How to reproduce

Emulator: mGBA 0.10.5 (SDL front-end, `/usr/games/mgba`), Xvfb `:201` 1024×768×24, `SDL_AUDIODRIVER=dummy`, scale `-3`. Default mGBA SDL keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows. Keys must be held ≥150–200 ms; 70 ms taps are dropped by the menu code.

```
Xvfb :201 -screen 0 1024x768x24 &
DISPLAY=:201 openbox &
DISPLAY=:201 SDL_AUDIODRIVER=dummy mgba -3 roms/Bookworm/Bookworm.gba &
DISPLAY=:201 xdotool windowfocus $(DISPLAY=:201 xdotool search --name mGBA | head -1)
```

Exact menu path used for every screen in §6b:

1. Boot → PopCap logo → copyright → title (`PRESS START`).
2. **Start** → `CHOOSE A FILE` (3 slots; A=Play, B=Delete).
3. Empty slot + **A** → `Create File` / `Enter your name:` grid.
4. A on a letter appends; B backspaces; `del`/`end` are grid cells selected with A; `end` with ≥1 character creates the profile.
5. **A** on a populated slot → `HOW TO PLAY` (5 pages) → board.
6. In game: **Start** → pause (`Options`: Save Game, New Game, Music Off/On, High Scores, Main Menu); **Select** → `Scramble?`; letters+A → word selection; **B** → deselect.
7. Pause → Save Game → `Game Saving` → `Game Saved`/OK; New Game → `New Game?`; Main Menu → `Leave Game?`; High Scores → `Top Scores`/`Best Words` with `B Reset` and `A Continue`; Reset → `Reset High Scores?`.
8. File select B → `Delete File?` (note inverted labels: **B = No, A = Yes**).

Screenshots (all in `/tmp/opencode/bookworm/shots/`, 720×480 crops of the 240×160 viewport at 3×): `02_title_c.png`, `03_main_c.png`, `04_name_c.png`, `08_menu_c.png`, `09_menu2_c.png`, `10_pause_c.png`, `11_hs_c.png`, `13_mm_c.png`, `23_filesel_c.png`, `27_scramble_c.png`, `28_save_c.png`, `29_saved_c.png`, `30_newgame_c.png`, `33_hs_c.png`, `34_hsreset_c.png`, `37_name10_c.png`, `38_delete_c.png`.

Key test: at the title, nine single buttons (A, B, Select, L, R, Up, Down, Left, Right) and five chords (A+B; L+R+Select; Up+Down+Left+Right; A+B+Select; L+R) produced **no transition**; only Start does. Equivalent Select/Start/L/R/chord sets were pressed on the file-select and pause screens with no effect.

## 4. Address map

All addresses are ROM addresses; file offset = address − `0x08000000`.

| Address | Kind | Meaning |
|---|---|---|
| `0x08000000` | header | stock branch `0xEA00002E`; only Nintendo logo at `0x04` |
| `0x08002DB8`–`0x08002FFC` | code (ARM) | the only keypad reader/dispatcher |
| `0x08002DC0` | code | `ldrh r3,[r0]`, `r0 = 0x04000000+0x130` (KEYINPUT read #1) |
| `0x08002E64` | code | `ldrh r3,[r5]`, `r5 = 0x04000000+0x130` (read #2) |
| `0x08002F2C` | code | `ldrh r1,[r4]`, `r4 = 0x04000000+0x130` (read #3) |
| `0x04000130` | I/O | KEYINPUT, active-low; watchpoint fired at PC `0x08002DC8` |
| `0x03002954` | IWRAM | installed direction-repeat callback pointer |
| `0x03002958` | IWRAM | installed release callback pointer |
| `0x0300295C` | IWRAM | installed press callback pointer |
| `0x03004DDA`/`DC`/`DE`/`E0`/`E2`/`E4`/`E7`/`E8` | IWRAM | previous-key word and repeat timers/flags |
| `0x08003128`, `0x08003278` | code | installer, handler set 1 (title) |
| `0x0800317C`, `0x080032E0` | code | installer, handler set 2 (file select / menus) |
| `0x080031D0`, `0x08003348` | code | installer, handler set 3 (gameplay) |
| `0x08003224`, `0x080033B0` | code | installer, handler set 4 (name entry) |
| `0x0801A244` / `0x0801A2A4` / `0x0801A248` | code | set 1 dir / press / release |
| `0x08013C04` / `0x08013CDC` / `0x08013C08` | code | set 2 dir / press / release |
| `0x0800C3C0` / `0x0800D0A0` / `0x0800C890` | code | set 3 dir / press / release |
| `0x080161E4` / `0x08016984` / `0x080163FC` | code | set 4 dir / press / release |
| `0x03004A97` | IWRAM | profile-name text buffer (max 8 chars + NUL) |
| `0x03004A20` | IWRAM | 3 profile records, stride `0x14` (name at +0) |
| `0x080167FC` | code | `cmp r5,#7` — append only if length ≤ 7 |
| `0x08016798` | code | `strlen` call on the name buffer |
| `0x0801688C` | code | `strcpy(profile[slot], namebuf)` |
| `0x151DB0` | data | 62-symbol name alphabet |
| `0x15008B` / `0x1500C0` | data | default Top Scores names / values |
| `0x1500D4` / `0x150106` / `0x150148` | data | default Best Words names / departments / values |
| `0x08013CE0`, `0x08013DA4` | code | loaders that install the two default tables |
| `0x0801EC28`, `0x0801EC34` | code (Thumb) | the ROM's only two `strcmp` calls |
| `0x083DB1F0`, `0x083DB1BC` | data | constants `"C"` and `"."` used by those calls |
| `0x0F6BB8`–`0x0F7C00` | data | developer trace-printf strings (TCRF-documented) |
| `0x151EAD` | data | undecoded 38-byte glyph/substitution table (not referenced by any pointer; see §8) |

## 5. Algorithm

### 5.1 Input dispatcher (`0x08002DB8`)

```
keys = REG_KEYINPUT & 0x3FF          // active-low: 0 = pressed
for i in 0..9:                        // bit 0=A 1=B 2=Select 3=Start 4=Right 5=Left 6=Up 7=Down 8=R 9=L
    m = 1 << i
    held = (keys & m) != 0
    was  = (prev & m) != 0
    if held and not was:  press_cb(m)     // [0x0300295C]
    if was and not held:  release_cb(m)   // [0x03002958]
prev = keys
```

Directions additionally run through a repeat timer (`0x03004DDA`–`0x03004DE4`): the first press is delivered through `press_cb`; after a delay the repeat callback `[0x03002954]` is invoked while held. There is **no array of past presses and no sequence counter** anywhere in the routine or in any installed callback.

### 5.2 Handler sets

| Set | Installed by | Direction | Press | Release | What it can do |
|---|---|---|---|---|---|
| 1 title | `0x08003128`/`0x08003278` | `0x0801A244` `bx lr` | `0x0801A2A4` `bx lr` | `0x0801A248` | Start release only → initialise file select |
| 2 file/menus | `0x0800317C`/`0x080032E0` | `0x08013C04` `bx lr` | `0x08013CDC` `bx lr` | `0x08013C08` | A release only → select/redraw |
| 3 gameplay | `0x080031D0`/`0x08003348` | `0x0800C3C0` | `0x0800D0A0` | `0x0800C890` | A press: pick/submit tile. A/B/Select/Start + D-pad on release |
| 4 name entry | `0x08003224`/`0x080033B0` | `0x080161E4` | `0x08016984` `bx lr` | `0x080163FC` | A = choose/append, B = backspace; D-pad moves the grid |

`0x0800D0A0` begins `cmp r1,#0x10000; bne return` (A) and never examines another mask. `0x0800C890` switches on one mask at a time (`1,2,4,8,0x10,0x20,0x40,0x80`; `0x100/0x200` return). `0x0801A248` accepts only `0x8` (Start); `0x08013C08` only `0x1` (A); `0x080163FC` only `0x1/0x2` (A/B).

### 5.3 Profile-name entry

```
grid[5][13]: rows 0..3 = a..z, A..Z (13 per row); row 4 = 0..9, del, end
cursor = (row, col)
A on a letter: if strlen(buf) <= 7: buf[len] = letter; buf[len+1] = 0
A on del:      if len > 0: buf[--len] = 0
A on end:      if len > 0: strcpy(profile[slot].name, buf); create/start
B:             if len > 0: buf[--len] = 0
```

There is no validator, checksum, table lookup, or comparison after `end`; the string is copied to the profile record and drawn/saved.

## 6. Tables

### 6.1 Name-entry alphabet (`0x151DB0`)

`abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789` — 62 symbols, plus control cells `del` and `end` (indices 62/63 of the 64-cell grid).

### 6.2 Developer default high scores

| Top Scores | Points | Best Words | Department | Points |
|---|---:|---|---|---:|
| Alison | 5,000 | Warpig | design | 500 |
| Nick | 4,000 | Bfiete | code | 400 |
| John | 3,000 | Tuco | test | 300 |
| Jeff | 2,000 | Sen | art | 200 |
| Pamela | 1,000 | Don | biz | 100 |

Names at `0x15008B`, values at `0x1500C0`; second table names at `0x1500D4`, departments at `0x150106`, values at `0x150148`. These are read only by the high-score loader/saver; no gameplay code reads them. Reset restores them.

### 6.3 Buttons recognized (per context)

| Context | A | B | Select | Start | D-pad | L/R |
|---|---|---|---|---|---|---|
| Title | – | – | – | file select | – | – |
| File select | play / new | delete | – | – | select slot | – |
| Name entry | pick/append | backspace | – | – | move cursor | – |
| Gameplay | pick/submit | deselect | scramble prompt | pause | move cursor | – |
| Pause | activate item | – | – | – | move item | – |
| High Scores | continue | reset prompt | – | – | – | – |

## 6b. Enumeration

### 6b.1 Defined spaces

| Space | Definition | Size |
|---|---|---|
| Text input | profile name over 62 alphanumeric symbols, lengths 1–8 | `62^1+…+62^8 = 221,919,451,578,090` ≈ 2.22×10¹⁴ strings |
| Button state | 10 bits (A,B,Select,Start,Right,Left,Up,Down,R,L) | 1,024 held combinations |
| Button input language | arbitrary press/release strings | unbounded, but **no handler stores history**; accepted language collapses to the single-press actions in §6.3 |
| Lookup tables | literal code tables, checksum tables, key/permutation tables | 0 found (see 6b.2) |

### 6b.2 Space searched, with counts

* `strings -t x -n 4` → **97,583** strings. Case-insensitive counts: `password` **0**, `passcode` **0**, `cheat` **0**, `debug` **0**, `secret` **0**, `unlock` **0**, `hidden` **0**; `bonus` **5** (gameplay text: bonus word), `code` **1** (the developer default "Best Words" department at `0x150113`), `level` **2** (debug/format strings), `options` **1** (pause header).
* KEYINPUT address search: literal `0x04000130` **0** occurrences; `add #0x130` from a `0x04000000` base **3** occurrences, all in the dispatcher; `0x04000100 + 0x30` construction **0**. Total key reads: **3**.
* Callback installers: `0x03002954`/`0x03002958`/`0x0300295C` each have **10** writer sites forming **8** installer functions = **4** distinct handler sets. Press callbacks: **4**, of which **3** are `bx lr`. Direction callbacks: **4**, of which **2** are `bx lr`. Release callbacks: **4**, each a single-mask switch.
* String comparison: the ROM has exactly **2** `strcmp` calls (`0x0801EC28`, `0x0801EC34`), both in the floating-point/`atof` path (`"C"`, `"."`). The name buffer `0x03004A97` has **2** code xrefs, both in the name-entry handler; the profile record `0x03004A20` is used for score comparison/display/save, not for name comparison.
* Key-mask sequence scan: aligned u16 runs of ≥4 values drawn from `{1,2,4,8,0x10,0x20,0x40,0x80,0x100,0x200}` over the whole image = **164**; **0** is referenced by a 32-bit code pointer (the one data coincidence was in `0xFF` padding). None lies in executable code next to an input reader. No mask table exists beyond the four 4-pointer installer blocks.
* Debug gates: no `debug` string, no debug menu label, no state selector. The trace-printf block is called unconditionally; TCRF documents it as hidden development text only.

### 6b.3 Novel codes

**None can exist.** There is no comparison, lookup table, checksum, or state write that a typed string or button sequence can satisfy. The deliverable for this ROM is therefore a characterised empty set, not a minted code. The strongest positive control is that the only text entry accepts and stores arbitrary strings (e.g. `abcdefgi`, 8 chars) with no state change, and the title's only accepted input is Start.

### 6b.4 Bounds proven by rejection (observed)

| Test | Input | Result |
|---|---|---|
| Title — all single buttons | A, B, Select, L, R, Up, Down, Left, Right | title unchanged (9/9) |
| Title — chords | A+B, L+R+Select, all four D-pad, A+B+Select, L+R | title unchanged (5/5) |
| Title — accepted input | Start | `CHOOSE A FILE` |
| File select — non-action buttons | Select, Start, L, R, A+B, L+R+Select, Up+Down | screen unchanged |
| Pause — non-action buttons | Select, L, R, Left, Right, A+B, A+B+Select, Left+Right | pause unchanged |
| Name length bound | 10 letter selections (`a`…`j`) | stored name = **8** chars (`abcdefgi` screenshot `37_name10_c.png`); static guard `cmp r5,#7` at `0x080167FC` |
| Name validation | any 8-char string | no message, no flag, no gameplay change (name only appears in the slot list) |

### 6b.5 Published codes tested

No published in-game code exists for this title, so there was nothing to enter and nothing to disprove:

* **VGChartz** Bookworm (GBA) cheats page: “Total cheats available: 0 / No cheats available for this game.”
* **SuperCheats** GBA Bookworm: no cheats/codes; only FAQ/walkthrough links.
* **GameFAQs** GBA 919765: only a word-list FAQ; the cheats URL returns 403 and the Wayback CDX has **no snapshot** of a cheats page for it.
* **TCRF** `Bookworm (Game Boy Advance)`: documents the `0xF6BB8` development text only; no codes, no debug menu.
* **remyhax “100 GBA crackmes”** article: Bookworm is not among the titles with a published or novel in-game code.

## 7. Validation evidence

**Observed (emulator / memory):**
* All §3/§6b screens walked and screenshotted; title-only-Start, name cap 8, save/load dialogs, high-score reset, default developer names.
* mGBA command-debugger watchpoint on `0x04000130` fired at PC `0x08002DC8` with `r0=0x04000130`, `r3=0x3FF`, `lr=0x0800391C`, confirming the dispatcher is the live input path.
* `x/1 0x03004A90` etc. show the name/profile block is ordinary RAM, not a code table.

**Derived (instruction-level):**
* Three and only three KEYINPUT reads; the `0x04000130` literal and the `0x04000100+0x30` construction are absent.
* Four handler sets; press callbacks are no-ops except gameplay A; release callbacks are single-mask switches; no press-history storage.
* Two `strcmp` calls, both in the decimal parser; name buffer xrefs confined to the name-entry handler.
* Append guard `cmp r5,#7` gives max 8 characters.
* Developer default tables are referenced only by the high-score loader/saver.

**Inferred (labelled):**
* The high-score name entry (after beating a default score) reuses handler set 4; not triggered in this session because no score was beaten. It shares the same code path and has no comparator.
* The level-stats and game-over states reuse gameplay handler set 3 (same `0x0800D0A0`/`0x0800C890` installers) and add no input surface; they were not exercised because they require completing/losing a level.

## 8. Unknowns

* The 38-byte table at `0x151EAD` (`>S@ABDRFGEKTHVX456789:;<=QPUJWY?` + index runs) is not referenced by any 32-bit pointer found; it is almost certainly a font/tile or text-decompression mapping, but it was not decoded. It has no code-like structure (no checksum, no fixed-length records).
* The high-score name-entry screen was not observed directly; its handler is the same set 4 and has no name comparison, but the exact prompt was not screenshotted.
* The `SHOWCURTAIN` debug trace (`0x0F7BE4`) and other trace-only paths were not forced; they are logging, not menus.
* A different regional/revision build could differ. All addresses here are for SHA-256 `3a0ab3e7…67780`.

## 9. Tooling

Environment: mGBA 0.10.5 SDL, Xvfb/openbox/scrot/ImageMagick, `arm-none-eabi-objdump`, Capstone 5.0.7, Python 3, `gdb-multiarch` (GDB stub was unusable because another session owned port 2345; mGBA's `-d` command debugger was used instead, with `watch 0x04000130`).

Scripts in `/tmp/opencode/bookworm/scripts/`:
* `k.py`, `key.py`, `title_buttons.py`, `type10.py` — XTEST key drivers.
* `find_keyread3.py` — literal-pool + `ldrh` scan that located the three KEYINPUT reads (the literal `0x04000130` scan itself returns zero).
* `find_add130.py` — enumerates every `add #0x130` (3 hits).
* `mask_scan.py` — u16 mask-run scan (164 runs) plus pointer-reference check (0 code refs).
* `all_strings.txt` — `strings -t x -n 4` dump (97,583 lines).

Key commands:

```
arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 \
  --start-address=0x08002d00 --stop-address=0x08003060 Bookworm.gba
# mGBA command debugger:
mgba -d -3 Bookworm.gba
watch 0x04000130
c
```

## 10. Legal note

No ROM, extracted graphics, audio, or text bank is redistributed. The report contains addresses, algorithms, hashes, short UI labels, and the ROM's own developer placeholder names; screenshots remain in the local analysis work directory.
