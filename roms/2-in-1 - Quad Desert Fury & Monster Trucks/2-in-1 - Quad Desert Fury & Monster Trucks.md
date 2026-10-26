# 2-in-1 — Quad Desert Fury & Monster Trucks (GBA) — Reverse Engineering Report

Methodology: [`GBA_REVERSE_ENGINEERING_GUIDE.md`](../../GBA_REVERSE_ENGINEERING_GUIDE.md)

Scope note: **in-game / developer-intended cheats only** (passwords, button codes,
hidden/debug menus, unlockables). GameShark/CodeBreaker/RAM patches are out of scope.

Result in one line: **both halves and the pack shell were enumerated, scanned and
fuzzed; the cartridge has no in-game code system of any kind.** The earlier
"no in-game cheats" triage is confirmed, and this report is the proof, with the
searched space stated in §6b.

---

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/2-in-1 - Quad Desert Fury & Monster Trucks/2-in-1 - Quad Desert Fury & Monster Trucks.gba` |
| Size | 8 388 608 bytes (`0x800000`, 8 MiB) |
| Header (file `0x0`) | title `TRUCKS/FURY`, code `BWQE`, maker `5G`, version `0` |
| MD5 | `f493e3fe4dbe2b9ecde12ce9590a10e7` |
| SHA-1 | `ac0d3528d5829097c71e819e96440ce125b17470` |
| SHA-256 | `3cce15e2efdd4b398301721646cdd82f13e530676555577a1e3072b59f2a6c8a` |

### 1.1 Cartridge layout — three GBA images

Scanning the whole file for the 156-byte Nintendo logo (`24 ff ae 51 …`) at
logo-relative offset 4 finds **three** GBA headers, not two:

| Image | Header file offset | ROM base | Header title | Game code | Maker | Ver | Used file range |
|---|---:|---:|---|---|---|---:|---|
| A | `0x000000` | `0x08000000` | `TRUCKS/FURY` | `BWQE` | `5G` | 0 | `0x000000`–`0x3F1433` |
| B | `0x3F4000` | `0x083F4000` | `TRUCKS/FURY` | `BWQE` | `5G` | 0 | `0x3F4000`–`0x407727` |
| C | `0x408000` | `0x08408000` | `MONSTERTRUCK` | `BMCE` | `5G` | 0 | `0x408000`–`0x7E8FC7` |

Used ranges = last non-`0xFF` byte before the next image; the tail of each image is
`0xFF` padding.

Identification of each image (evidence type in brackets):

* **A = Quad Desert Fury.** C++ RTTI names for the ATV game at `0x010B48`–`0x010BC8`
  (`7SysTask`, `9SysSprite`, `TRACK TIMES`, `7AtvGame`, `7Vehicle`, `8ThSprite`), and
  the game's title/legal screens. [Derived/Observed]
* **B = the pack's "Choose a game" boot selector.** Only ~79 KiB, no text bank, no
  RTTI; contains the two game logos and a two-item selector state machine at
  `0x083F4280`. Execution was observed at `0x083F44A2`/`0x083F475E` with the shell
  on screen. [Observed]
* **C = Monster Trucks.** Header `MONSTERTRUCK`/`BMCE`, its UI string table at
  `0x08417FE4` and code that references those strings with absolute `0x0841xxxx`
  literals (e.g. `0x08418048` "track 1" is loaded at `0x0841B8CC`), i.e. the image
  is linked at base `0x08408000`. [Derived]

All three header checksum fields are zeroed/invalid (`complement` `0x55`/`0x55`/`0x0D`,
expected `0x2B`/`0x2B`/`0xE3`; header checksum `0x0000`), which is normal for a packer
that rewrites the first header's title. Do not trust header checksums on this cart.

### 1.2 Boot chain (observed with mGBA's CLI debugger)

1. Reset → ARM entry `0x080000C0` (image A crt0).
2. A's crt0 calls `main` at `0x0800111C` (breakpoint hit at **cycle 175**).
3. A's main compares the word at `0x03000000` with the magic `0xA5A5A5A5`. On cold
   boot it does not match, so it loads the pointer at `0x08010E98` (= `0x083F4000`)
   and `bx`es to it (`bl 0x0800207C`, a `bx r0` trampoline).
4. Image B's crt0 runs and calls `main` at `0x083F41EC` (breakpoint hit at **cycle 416**).
   B draws the Majesco logo, then the `Choose a game` screen.
5. Shell confirms on **Start**: B writes `0xA5A5A5A5` to `0x03000000`
   (`0x083F442A: movs r1,#0xC0; lsls r1,#18` → `0x03000000`;
   `0x083F442E: ldr r0,[0x083F4460]` → `0xA5A5A5A5`; `0x083F4430: str r0,[r1]`)
   and restarts at `0x08000000` to launch Quad Desert Fury — A's main is entered a
   second time at cycle 120 545 793 with `[0x03000000] = 0xA5A5A5A5`, so it skips the
   B jump and continues into the game. Selecting Monster Trucks instead jumps to
   `0x08408000` (breakpoint at C's `main`, `0x0840E764`, hit after selecting it).

So the address convention `ROM address = 0x08000000 + file offset` holds for A; B is
linked for `0x083F4000` and C for `0x08408000`.

---

## 2. Executive summary

The cartridge offers **no developer-intended cheat input at all**: no password or
code screen, no button-sequence cheat, no hidden/debug menu, and no unlock code.
All content is available from boot.

* **Quad Desert Fury (A).** Main menu = `Quick Race` / `Challenge Mode` only.
  Quick Race exposes **7 tracks** immediately; Challenge Mode is a sequential
  "win to unlock the next track" progression that needs no code. Pause menu =
  `Continue` / `Music on|off` / `Quit`. No third item, no input field.
* **Monster Trucks (C).** Main menu = `Quick Game` / `Career Mode` only. Quick Game
  exposes **10 tracks** (5 layouts × 2) immediately. Career Mode is a money loop:
  `Mod Shop` (5 upgrades × 6 levels) → `Next Track` (prize money `$400…$800`/`$200…$400`)
  → race. Pause menu = same three items. The complete UI text table of this half is
  enumerated in §6.3 and contains no cheat/password/debug word.
* **Pack shell (B).** Exactly two entries (Quad Desert Fury, Monster Trucks),
  `Up`/`Down` + `Start`; 8 multi-button combinations, including the Konami sequence
  and `L+R+Select`, produced no response (§6.4, §7).
* **Published codes:** none exist. GameFAQs' cheat pages for both games return 403 and
  have no Wayback snapshot; search results for both titles surface only generic
  GameShark `.CHT` archives (out of scope), never an in-game code (§6b.4).

There is therefore **no novel code to mint**: the input surface that the guide's
§0.2 asks us to enumerate does not exist. The equivalent deliverable is the bounded
negative in §6b — the space that was excluded, by format, by string space, by menu and
by public list.

---

## 3. How to reproduce

### 3.1 Emulator

```bash
Xvfb :111 -screen 0 1024x768x24 &
DISPLAY=:111 openbox &
DISPLAY=:111 SDL_AUDIODRIVER=dummy /usr/games/mgba -3 "2-in-1 - Quad Desert Fury & Monster Trucks.gba" &
DISPLAY=:111 xdotool search --name mGBA        # window id
DISPLAY=:111 xdotool windowfocus <wid>
```

Keymap (mGBA SDL defaults, verified by driving the menus): A=`x`, B=`z`,
L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad = arrows. Hold 180 ms;
the games debounce and some transitions take 2–5 s. `Tab` (hold) is mGBA's
fast-forward.

A second instance was launched with `-d` (CLI debugger) under `tmux` for breakpoints
and memory reads; it uses no GDB port, so it does not collide with other sessions.

### 3.2 Menu paths

```
BOOT (cold): Majesco logo -> "Choose a game" (Quad / Monster Trucks)
            Up/Down = move, START = confirm (A/B do nothing)

QUAD DESERT FURY: legal screen -> QUAD title, "Press START" -> START
  main:  Quick Race | Challenge Mode      (Left/Right, A = select)
  Quick Race -> SELECT TRACK 1..7 (Left/Right, A) -> race
  Challenge Mode -> wall of text -> A -> race on track 1
  race: Start -> PAUSE (Continue / Music on / Quit); Quit returns to the menu
        directly (Quad: no confirmation dialog)

MONSTER TRUCKS: legal screen -> title, "PRESS START" -> START
  main:  QUICK GAME | CAREER MODE
  QUICK GAME  -> CHOOSE TRACK 1..10 (Up/Down, A=OKAY, B=BACK) -> race
  CAREER MODE -> MOD SHOP (Engine/Turbo/Tires/Shocks/Nitrous; A BUY, A DONE)
              -> NEXT TRACK (prize money; A OKAY) -> race
  race: Start -> PAUSE (Continue / Music on / Quit); Quit -> confirm Yes/No
```

### 3.3 Experiment loop

Screens were captured with `scrot`; state was snapshotted with `Shift+F1` and restored
with `F1` so every button-combination test started from the identical frame
(`<rom>.ss1`, git-ignored). Combination tests used `xdotool keydown` on all keys,
500 ms hold (2 s for the "hold" case), release, 0.7 s settle, then a pixel diff against
the restored baseline (see `fuzz*.py`, §9).

### 3.4 Codes tested

There are no codes to test. Every published-code search returned nothing (§6b.4), so
the "codes exercised" table is empty by evidence, not by omission. The button
combinations actually pressed are listed in §6.4.

---

## 4. Address map

### 4.1 ROM

| Address | What |
|---:|---|
| `0x08000000` | Image A base; ARM entry `0x080000C0` |
| `0x0800111C` | A `main` (crt0 calls it); warm-boot magic test + shell hand-off |
| `0x0800207C` | `bx r0` trampoline used for the hand-off |
| `0x08010E98` | Data word = `0x083F4000` (pointer to the shell image) |
| `0x0800A2A8` | Input poll: `~KEYINPUT & 0xFFFF` → `0x03000000`/`0x03000002` |
| `0x0800A2C6` | Start-bit (`0x008`) test in the racing input path |
| `0x08010B48`–`0x08010BC8` | Quad RTTI: `7SysTask` `9SysSprite` `TRACK TIMES` `7AtvGame` `7Vehicle` `8ThSprite` |
| `0x083F4000` | Image B base; ARM entry `0x083F40C0`; B `main` `0x083F41EC` |
| `0x083F41D1` | Thumb pointer to B `main` (in B's crt0 literal pool) |
| `0x083F4280` | B shell state machine (cases 0…3) |
| `0x083F442A` | B: writes `0xA5A5A5A5` to `0x03000000` before the Quad relaunch |
| `0x083F4460` | B: literal `0xA5A5A5A5` (warm-boot magic) |
| `0x083F4480` / `0x083F4494` | B: Up (`0x040`) / Down (`0x080`) handlers, each `eors` the 1-bit selection |
| `0x083F4520` | B `KEYINPUT` literal (`0x04000130`) |
| `0x08408000` | Image C base; ARM entry `0x084080C0`; C `main` `0x0840E764` |
| `0x0840B14C` | C main-menu builder (loads the 4 string pointers below) |
| `0x0840B280` | C main-menu table: `0x0841815C` quick game, `0x08418168` career mode, `0x08418174` back, `0x0841817C` select |
| `0x08417FE4` | C UI string table start (`SWAMPLAND`); ends at `0x084181E0` |
| `0x0840A138` | C `KEYINPUT` literal |
| `0x0841B8CC` | Literal `0x08418048` ("track 1"), proving C is linked at `0x08408000` |

### 4.2 RAM / I/O

| Address | Use |
|---:|---|
| `0x03000000` | Input **pressed** mask (u16, active-high `~KEYINPUT`); also the warm-boot magic `0xA5A5A5A5` at boot |
| `0x03000002` | Input **held** mask (u16) |
| `0x03000008` | Shell: selection index (1 bit; 0 = Quad, 1 = Monster Trucks) |
| `0x0300000C` | Shell: menu state variable |
| `0x03000010` | Shell: held-key word it tests (`0x040` Up, `0x080` Down) |
| `0x03000014` | Shell: cursor/scroll shadow written from the selection |
| `0x04000130` | KEYINPUT (active-low) |
| `0x04000000` | DISPCNT — Quad's pause screen runs in **mode 3** (bitmap) |
| `0x06000000` | VRAM / bitmap frame buffer |

Button bits used by the engine (active-high after inversion): A `0x001`, B `0x002`,
Select `0x004`, Start `0x008`, Right `0x010`, Left `0x020`, Up `0x040`, Down `0x080`,
R `0x100`, L `0x200`.

Code sites that read `0x03000000` in image A (complete list from a literal-pool scan,
8 sites):

```
0x08007934  0x08007D32  0x0800A2A8  0x0800A554  0x0800A926
0x0800F3FA  0x0800FF98  0x080101B4
```

`0x0800A2A8` is the writer of the input state in image A (the per-frame poll); image C
has its own poll at `0x0840A1xx` with the same shape. The other A sites are menu/mode
branches that test single bits (e.g. `0x008` = Start); none of them compares the input
against a table, an index, or a stored sequence. (In image B, `0x083F430E`/`0x083F4334`/
`0x083F4360` also touch `0x03000000`, but B uses that word as a **frame timer** — it is
incremented to 120 — and reads its keys from `0x03000010`; B is a separate program that
never uses image A's input struct.)

---

## 5. Algorithm

### 5.1 Input model (derived from `0x0800A2A8`, identical in both halves)

```c
held    = (~REG_KEYINPUT) & 0xFFFF;   // active-high, upper 6 bits always 1
pressed = held & ~prev_held;
prev_held = held;
INPUT.pressed = pressed;              // 0x03000000
INPUT.held    = held;                 // 0x03000002
```

The pressed mask is also copied into the current scene object at `+0x1B0`, which is
what the menu code reads. There is **no sequence matcher**: no bytes are accumulated,
no progress index exists, and no table of expected masks is referenced anywhere
(§6b.2).

### 5.2 Text encoding (needed for the string-space claim)

Monster Trucks and the pack shell use a plain, if unusual, encoding:

* `A`–`Z` are stored as lowercase ASCII `0x61`–`0x7A` (the font draws them as capitals);
* digits, space and punctuation are stored unchanged;
* strings are NUL-terminated and usually 4-byte aligned/padded.

Validator: apply the map `c → c-0x20` for `0x61…0x7A` to the whole ROM, then read the
NUL-separated runs. This reproduces every visible Monster Trucks label exactly, e.g.

```
0x418150 "PRESS START"   0x41815c "QUICK GAME"   0x418168 "CAREER MODE"
0x418184 "CHOOSE TRACK"  0x418090 "TRACK 10"     0x418120 "SEASON 1 COMPLETE"
0x4180d8 "2ND $200"
```

Quad Desert Fury's UI is instead **bitmap-baked**: the game renders in mode 3, its
menu labels are part of the screen art, and no ASCII (or affine/UTF-16) encoding of
`SELECT TRACK`, `PAUSE`, `MUSIC ON`, `QUIT`, `QUAD DESERT FURY` exists anywhere in
the 8 MiB. Its labels are therefore covered by visual enumeration, not by the string
scan (§6b.3).

### 5.3 No validator / no code path

There is no function that (a) reads a character buffer, (b) calls a length or
comparison routine against constants, (c) writes a cheat flag, or (d) returns a
code result. The only input consumers in image A are the sites above; the two menu
paths found are the shell's own state machine (`0x083F4280`) and the engine's
item-list builder (identified in image C at `0x0840B14C`). The main-menu builder in
Monster Trucks loads exactly four string pointers — two selectable items and two
footer labels — so a third/hidden entry cannot be reached by any input.

---

## 6. Tables

### 6.1 Menu inventory (all reached; screenshots in `/tmp/opencode/quad/shots/`)

| # | Screen | Half | Items / notes | Screenshot |
|---:|---|---|---|---|
| 1 | Majesco logo | B | non-interactive | `23_shell.png` |
| 2 | **Choose a game** | B | 2 entries; Up/Down + **Start** | `22_shell_quad.png` |
| 3 | Quad legal/credits | A | 4 s, no input | `27_quad_boot3.png` |
| 4 | Quad title "Press START" | A | Start only | `30_quad_title3.png` |
| 5 | Quad **main menu** | A | Quick Race / Challenge Mode | `31_quad_menu.png`, `33_quad_menu_right.png` |
| 6 | Quad **SELECT TRACK** | A | 1…7, wraps | `q_track_1..7.png`, `35_quad_trackselect.png` |
| 7 | Quad **CHALLENGE MODE** text | A | info screen, A | `40_quad_challenge.png` |
| 8 | Quad race HUD | A | 3 laps | `37_quad_race.png` |
| 9 | Quad **pause** | A | Continue / Music on / Quit | `38_quad_pause.png`, `91_q_pause2.png` |
| 10 | Quad quit (no confirm) | A | no dialog; returns directly to title/main menu (both observed) | `92_q_quitconfirm.png` |
| 11 | MT legal/credits | C | 4 s | `05_after_b.png` |
| 12 | MT title "PRESS START" | C | Start only | `07_mt_intro2.png` |
| 13 | MT **main menu** | C | Quick Game / Career Mode | `08_mt_menu.png` |
| 14 | MT **CHOOSE TRACK** | C | 1…10, wraps | `mt_tracks_montage.png` |
| 15 | MT **MOD SHOP** | C | 5 upgrades, clamps at Nitrous | `85_modshop2.png`, `ms_montage.png` |
| 16 | MT **NEXT TRACK** | C | prize money, A OKAY | `18_mt_career3.png` |
| 17 | MT race HUD | C | 2 laps | `11_mt_race2.png`, `77_mt_race.png` |
| 18 | MT **pause** | C | Continue / Music on / Quit | `12_mt_pause.png` |
| 19 | MT quit confirm | C | "ARE YOU SURE YOU WANT TO QUIT?" Yes / No | `14_after_quit.png` |

No screen contains a text field, keyboard grid, code counter, or unnamed menu entry.
The post-race results panel was not exercised (see §8).

### 6.2 Complete Monster Trucks UI string table (`0x417FE4`–`0x4181E0`)

`SWAMPLAND`, `COOKS COUNTY`, `AMERICAN`, `ORANGE COUNTY`, `CHAMPION`, `ARENA`,
`RACEWAY`, `RACEGROUNDS`, `TRACK 1`…`TRACK 10`, `1ST $400`…`1ST $800`,
`2ND $200`…`2ND $400`, `1/4`, `00:00.0`, `SEASON 1 COMPLETE`, `CAREER EARNINGS`,
`CONTINUE`, `PRESS START`, `QUICK GAME`, `CAREER MODE`, `BACK`, `SELECT`,
`CHOOSE TRACK`, `OKAY`, `AMERICANXRACEWAY`, `NEXT TRACK`, `BUY`, `DONE`,
`MOD SHOP`, `AVAILABLE CASH`, plus C++ RTTI names (`7VEHICLE`, `8THSPRITE`,
`7SYSTASK`, `9SYSSPRITE`, `4GAME`).

That is the entire vocabulary of the half. There is no `PASSWORD`, `CODE`,
`CHEAT`, `DEBUG`, `SECRET`, `UNLOCK`, `HIDDEN`, `BONUS`, `EXTRA` or `ENTER`
string, in this bank or anywhere else (§6b.1).

### 6.3 Button masks

See §4.2. `Start` = `0x008`, `Select` = `0x004`, `L` = `0x200`, `R` = `0x100`.

### 6.4 Combinations pressed in the emulator

Pressed at the shell (each after a fresh boot), at the Monster Trucks main menu and
at the Quad pause screen, with a savestate reload before each test:

| Combination | Shell | MT main | Quad pause |
|---|---|---|---|
| `L+R` | no change | no change (wheel animation only) | no change |
| `L+R+Select` | no change | no change | cursor moved (Select = nav) |
| `L+R+Start` | start selected game | — | unpause (Start) |
| `A+B` | shell: no change; Quad title: same as Start | enters selected item (A) | unpause (A) |
| `A+B+Start` | as Start | as A | unpause |
| `Up Up Down Down Left Right Left Right B A` (Konami) | no reaction; final `B`/`A` only navigate | same; final `A` opens the selected item | same |
| `Select` / `L` / `R` alone | no change | no change | cursor move only |
| `Left+Right`, `Up+Left`, `Down+Right`, `Up+Up+Down+Down` | selection/none | selection/none | cursor/none |
| `L+R+A+B+Select` | no change | no change | unpause |
| Hold `L+R` 2 s | no change | no change | no change |

At the Quad title screen every combination except `Start` (and `A`/`B`, which are
alternate confirm keys there) left the frame pixel-identical.

---

## 6b. Enumeration

**No code system exists, so no code can be minted.** What follows is the bounded
negative: exactly what was excluded, and how.

### 6b.1 Text space (complete ROM, both encodings)

* Raw `strings -t x -n 4` → 89 301 strings; `-n 8` → 28 060.
* Decoded text (ASCII plus the `+0x20` letter map of §5.2) → 87 638 printable runs.
* Case-insensitive search over both for
  `password|passcode|cheat|code|secret|debug|unlock|hidden|bonus|extra|menu|invalid|wrong|correct|enter|option`
  → **0 hits** (only the unrelated header title `TRUCKS/FURY`, RTTI names, and the
  Monster Trucks UI vocabulary of §6.2 exist).
* The Monster Trucks string table was dumped in full (§6.2); it is the complete UI
  vocabulary of that half.
* GBA LZ77 scan of the whole file: only 3 accidental decompressions (sizes 2, 2, 6) —
  no compressed text bank is hiding the words.
* Quad's UI labels are not in any character encoding: exhaustive checks for
  `select track`, `challenge mode`, `pause`, `music`, `quit`, `licensed by nintendo`,
  `quad desert fury` under every single-byte affine map (`+k` and `^k`, k=0…255),
  16-bit and 32-bit per-character cell forms (constant-offset variants), found only
  the Monster Trucks copies. Quad's labels are baked into its bitmap-mode art (§5.2).
  Its screens are therefore covered by enumeration, not by this scan.

### 6b.2 Button-code space

A button cheat needs either a stored mask table or a sequence index. Both were
searched for over the entire 8 MiB:

| Scan | Space | Result |
|---|---|---|
| u16 arrays with all entries in `1…0x3FF`, length ≥4 | 6 088 runs (dominated by graphics); restricting to single-bit masks leaves 81 runs of ≥5 mask entries | none is a plausible code table: after excluding periodic runs, no run has ≥4 distinct single-bit values |
| u16 arrays of single-bit masks (`1,2,4,…,0x200`), zeros allowed | 108 candidate starts | **0** loaded by any `LDR Rd,[PC]` literal, with or without the Thumb bit |
| u8 arrays of single-bit masks, ≥4 entries, ≥3 distinct, non-periodic | 849 runs | 1 incidental 32-bit address match; **0** actually loaded by an instruction |
| u8 arrays of button *indices* `0…9` | 6 892 runs | 20 incidental matches; the one apparent `LDR` (`0x0800FCCA`) loads the pool word `0x05000200` next to the run — the "table" straddles a pointer's high byte and a literal, so it is not a table |
| Konami sequence and its reverse, as u16 masks and as button indices | 2 orders × 2 encodings × 10 presses | **0 hits** |
| Any `cmp`/`ands`/`tst` against a multi-button mask near an input read | all 8 input-reading sites in A disassembled | only single-bit tests (Start/A/B/stick); no multi-key gates |

Interpretation: the representable button space (10 buttons → 1 024 single-frame
masks, any sequence length) is empty **for this ROM**, because no table and no
matcher exists to consume it. This is a static claim about the whole file, and it is
corroborated dynamically by §6.4 (no code reacted to any combination).

### 6b.3 Menu / screen space

19 screens enumerated across the shell and both halves (§6.1), with the item count
confirmed statically where the menu is data-driven:

* shell: 2 items — `Up` and `Down` each `eors` the 1-bit selection at `0x03000008`
  (`0x083F4480`, `0x083F4494`), so a third entry cannot even be represented;
  state machine `0x083F4280` with cases 0…3 (init/logo/menu/launch);
* Monster Trucks main: exactly 2 selectable items + 2 footer labels, from the
  4-pointer table at `0x0840B280`;
* Monster Trucks Mod Shop: 5 items, clamps at Nitrous (no wrap to a 6th);
* tracks: 7 (Quad) / 10 (Monster Trucks), both wrap, no extra index;
* pause, both halves: 3 items;
* no keyboard, no text field, no counter, no unnamed entry.

### 6b.4 Published-code space

| Source | Result |
|---|---|
| GameFAQs `918720-quad-desert-fury/cheats` | HTTP 403; no Wayback snapshot; search snippet shows no cheat section (only "game information and a community message board") |
| GameFAQs `922253-monster-trucks/cheats` | same |
| General web search for both titles + `password`/`cheat`/`code`/`unlock` | no in-game codes; only generic GameShark/CodeBreaker `.CHT` collections for the 2-in-1 (out of scope) |
| TCRF / fan wikis | no entry describing unused or hidden modes for either title |

Every "published" item found is a memory-patch (GameShark) code, not a game input;
there is nothing to re-enter in the emulator and nothing to verify. `roms/INDEX.md`
was not touched.

### 6b.5 Why the negative is conclusive rather than "not found"

1. The games have no entry field anywhere (§6b.3) — a password would need one.
2. The one half that stores text as strings has its **entire** string table dumped,
   with no relevant word (§6b.1/§6.2).
3. A button code would need a table or a matcher; neither exists in 8 MiB (§6b.2).
4. Every menu that could host a hidden entry was opened and its item count proven,
   either visually or from the descriptor table.
5. Published sources offer no code to contradict this.

---

## 7. Validation evidence

**Observed (emulator)**

* Cold boot: Majesco logo → `Choose a game` (2 entries, Start confirms).
* Quad: title, main (2 items), 7-track select with wrap, Challenge Mode text,
  race HUD (3 laps), pause (3 items), quit straight back to the menu (no dialog).
* Monster Trucks: title, main (2 items), 10-track select with wrap, Mod Shop
  (5 upgrades, clamps), Next Track with prize money, race HUD (2 laps), pause,
  quit confirm.
* `0x03000000 = 0xA5A5A5A5` at the second entry into A's main after choosing Quad
  from the shell (debugger read).
* No visual reaction to any of the combinations in §6.4 (pixel-identical frames
  where no navigation key was involved).

**Derived (disassembly / data)**

* Boot chain A → B → (A | C), including the `0x08010E98 → 0x083F4000` hand-off,
  the `0xA5A5A5A5` write at `0x083F442A`–`0x083F4430`, and the warm-boot magic test.
* Three images and their link bases (headers, string literal `0x08418048`, used ranges).
* Text encoding `A–Z → 0x61–0x7A` and the complete Monster Trucks string table.
* Input model at `0x0800A2A8`; the 8 readers of the A input state (plus B's separate
  key word at `0x03000010` and its frame timer at `0x03000000`); no sequence matcher.
* Monster Trucks main menu = 4 pointers (2 items + 2 labels) loaded by `0x0840B14C`.
* Button-table scans of §6b.2, including the "no literal points at the candidate"
  filter.

**Inferred**

* That Quad's menu labels are baked into bitmap-mode screen art: supported by the
  absence of every encoding in ROM and by mode 3, but the art itself was not matched
  byte-for-byte to the frame buffer.
* That `Music on` in the pause overlay is likewise art/two-state art; the words
  `music`/`quit` are not stored as text in either half.

---

## 8. Unknowns

* The post-race **results panel** was not exercised: it needs a race win, and a
  no-input run does not complete a lap on either track (Quad: stuck at `LAP 1 of 3`;
  Monster Trucks: truck wedges on a barrier at `LAP 1/2`). It is a results display,
  not a selectable menu, so it cannot carry a code surface — but it was not seen.
* Quad Desert Fury's label encoding/asset was not identified (bitmap art vs. a
  non-affine glyph table). This does not affect the conclusion, because the screen
  enumeration covers every UI surface.
* Save-backed progression (Challenge Mode wins, Career money) was not reverse
  engineered; no `.sav` data was written during this session. No code is known to
  feed it.
* GameFAQs could not be fetched directly (403) and has no archive snapshot; the
  "no published codes" statement rests on search results and on the absence of any
  code string in the ROM.

---

## 9. Tooling

All scripts in `/tmp/opencode/quad/` (session-only, not archived):

| Script | Purpose |
|---|---|
| `scan0.py` | logo/header scan, hashes, header fields |
| `findldr.py`, `ldrscan.py`, `sweep.py` | Thumb `LDR Rd,[PC,#imm]` scans with correct `Align(PC+4,4)` |
| `blscan.py` | Thumb BL target scan |
| `lzscan.py` | GBA LZ77 decompressor + full-ROM text scan |
| `key.py`, `fuzz.py`, `fuzz2.py`, `fuzz3.py` | xdotool input driver, savestate-restore combination fuzzing, pixel diff |
| `dbg.py` (pty prototype) | mGBA CLI debugger driver; the live session used `tmux` + `send-keys` |

Environment: `mgba-sdl 0.10.5`, `binutils-arm-none-eabi`, `capstone 5.0.7`,
`Xvfb`/`openbox`/`xdotool`/`scrot`, `python3` + Pillow.

Screenshots referenced in §6.1 are in `/tmp/opencode/quad/shots/` (not committed).

Legal: no ROM, extracted graphics, music or game text is redistributed here; only
addresses, algorithms, hashes and the game's own short UI labels are quoted as
evidence.

### Cleanup

Every process started for this engagement was stopped by PID: the `mgba -d` instance
(debugger), the `tmux` session `q`, `openbox` and `Xvfb :111`. No `pkill -f` was used;
no other session's emulator or display was touched.
