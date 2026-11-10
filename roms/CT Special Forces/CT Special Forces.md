# CT Special Forces (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/CT Special Forces/CT Special Forces.gba` |
| Size | 4,194,304 bytes (4 MiB, `0x400000`) |
| Header title | `CT SPECIAL F` (`0xA0`, 12 bytes, no NUL padding) |
| Game code | `AC7E` (`0xAC`) |
| Maker code | `FL` (`0xB0`) |
| Version | 0 (`0xBC`) |
| Complement check | `0xA1` (`0xBD`, valid for the header bytes) |
| Header checksum | `0x0000` (`0xBE`) — same as every other dump in this collection; not evidence of tampering |
| Entry | `0xEA00002E` → `0x080000C0` (stock GBA branch) |
| MD5 | `bb8477087e3d927af99cd3263c66f7cf` |
| SHA-1 | `ab151206c142dbcdb4f2ea9877d6bcd2c89b8b55` |
| SHA-256 | `39db513da49f2b448467bd42a46aa8025a1ad108812e519c4a080e0ea5cbb0a8` |

Embedded-header scan: the 156-byte Nintendo logo occurs exactly once, at file
`0x4`; no second image, no multi-game shell. The first 4 KiB contain the stock
crt0 (mode/IRQ setup, `0x080000C0`), no cracktro and no trainer strings. The
6-language boot menu (English/Français/Deutsch/Español/Italiano/Nederlands)
identifies this as the European release (`AC7E`).

## 2. Executive summary

CT Special Forces has exactly one in-game code surface: a **4-digit dial
password screen** reached from the main menu (`Password`). Each of the four
dials cycles `0`–`9`, so the input space is `10^4 = 10,000`.

The game does **not** compute or checksum the number. It compares the four
dial values, in order, against a literal 7-entry table of 4-byte digit tuples
at ROM `0x08366FF4` (file `0x366FF4`). Each entry is a world/character
shortcut:

* four entries (0202, 1407, 2704, 0108) select world 1–4 and then show
  "Select your character" (both characters available);
* three entries (1608, 2111, 1705) select world 2/3/4 and skip the character
  screen. The table stores only the four digits — no character field — so the
  mission uses the character state already carried by the session (our
  no-select runs without a prior Owl run rendered Raptor).

Every accepted code starts **Level 1** of its world. The world map draws one
radar marker per world stage (1/2/3/4 markers for worlds 1/2/3/4), with the
crosshair on Level 1.

Published lists disagree on the world-2 "both characters" code. GameFAQs,
SuperCheats, CheatCC, id.wikibooks and the CT Special Force wiki print **1408**;
older mirrors (Neoseeker, ggmania, cheats42) print **1407**. This ROM's table
contains **1407**, and the game accepts 1407 while rejecting 1408 with "Wrong
Password". The ROM therefore sides with the mirrors: 1407 works and the code
printed by GameFAQs/TCRF-era wikis does not.

No button-code table, debug menu, sound test, or second password system was
found. The main menu has four items, Options has only Music/Sfx/Credits, Pause
has only Resume/Quit (with an A/B confirmation), Challenge is the link
multiplayer waiting room, and the title screen is "Press Start" only.

## 3. How to reproduce

Emulator: mGBA SDL 0.10.5 (`/usr/games/mgba`), 3× scale, under
`Xvfb :221` + `openbox`, `SDL_AUDIODRIVER=dummy`.

Default mGBA SDL keymap used throughout:

| GBA | key |
|---|---|
| A | `x` |
| B | `z` |
| L | `a` |
| R | `s` |
| Start | `Return` |
| Select | `BackSpace` |
| D-pad | arrow keys |

Path to the code screen:

1. Boot; the L.S.P. logo appears. Press `Return` (or wait) for the language
   screen, then `x` on English.
2. Title screen: wait for **Press Start**, press `Return`.
3. Main menu: `Mission / Challenge / Password / Options`. Move down twice to
   **Password**, press `x`.
4. On the dial screen, **Up/Down selects a dial** and **Left/Right changes its
   value 0–9 (wraps)**. `x` (A) submits. A wrong code shows **Wrong Password**
   and resets all four dials to `0`.
5. A correct code either goes to "Select your character" (0202, 1407, 2704,
   0108) or straight to the world map (1608, 2111, 1705). On the character
   screen `x` confirms the highlighted character (default Stealth Owl). On the
   map, `x` starts the mission briefing.

Fast test loop: save a state on the password screen (`Shift+F2`); plain `F2`
reloads it, so each test is ~20 key presses instead of a menu replay.

## 4. Address map

All ROM addresses are `0x08000000 + file offset`.

| Address | Meaning |
|---|---|
| `0x08366FF4` | 7 × 4-byte password table (the only accepted codes) |
| `0x08366FF4 + 4*i` | entry *i*: four dial digits, one byte each |
| `0x08367318` | 8 × u32 text offsets used by the world-map scene; indices 0–6 are the seven password entries, index 7 (`0x5A78`) is not reachable from the password table |
| `0x0800C0A8` | **validator**: compares 4 dial s16 values against the table, returns index 0–6 or `-1` |
| `0x0800C110` | prefill helper: writes `table[index]` into the four dials |
| `0x0800BC2C` | password scene allocator (allocates `0x1EC` bytes, stores pointer in `*0x03000160`) |
| `0x0800BC80` | password scene entry/init |
| `0x0800BDB0` | password scene per-frame update (dial selection/edit) |
| `0x0800BE04` | A-press branch → `bl 0x0800C0A8` |
| `0x0800BE34` | rejection path: sound 3, zero all dials, show "Wrong Password" |
| `0x0800BE12` | acceptance path: sound 14, store index, return state `0x1C8` |
| `0x0800D964` | world-map scene setup; takes the world index |
| `0x0800D9A0` | `index*4 + 0x08367318` → world-name text offset |
| `0x0801A55C` | input engine: reads `KEYINPUT` (`0x04000130`), stores `keys \| 0xFC00` |
| `0x030038A4` | current raw key word (active-low, `\| 0xFC00`) |
| `0x030038A6` | previous raw key word |
| `0x03000160` | pointer to current scene object (password scene struct) |
| `scene+0x52` | dial 1 value (s16) |
| `scene+0x86` | dial 2 value (s16) |
| `scene+0xBA` | dial 3 value (s16) |
| `scene+0xEE` | dial 4 value (s16) |
| `scene+0x1E0` | currently selected dial row (0–3) |
| `0x0300385E` | last accepted code index (s16), read by the world-map scene |
| `0x0300017C` | scene watchdog word (initialised to `0x1234`; also receives the accepted index) |

Key-edge semantics: the game computes `newly_pressed = previous & ~current`
(active-low raw words), then tests bit 0 for A and bit 1 for B. The dial edits
use the raw current key word.

## 5. Algorithm

```
table[7][4] = {
  {1,6,0,8},   // 0: world 2, no character select
  {2,1,1,1},   // 1: world 3, no character select
  {1,7,0,5},   // 2: world 4, no character select
  {0,2,0,2},   // 3: world 1, character select
  {1,4,0,7},   // 4: world 2, character select   <-- published as 1408
  {2,7,0,4},   // 5: world 3, character select
  {0,1,0,8},   // 6: world 4, character select
}

validate(d0,d1,d2,d3):
    for i in 0..6:
        if d0 == table[i][0] and d1 == table[i][1]
           and d2 == table[i][2] and d3 == table[i][3]:
            return i
    return -1

on A press:
    i = validate(dial1, dial2, dial3, dial4)
    if i < 0:
        play(sound 3)
        dial1..dial4 = 0
        print("Wrong Password")
    else:
        play(sound 14)
        last_index = i          // 0x0300385E and 0x0300017C
        next_scene = 0x1C8      // character select or world map
```

There is **no checksum, no field extraction and no arithmetic** on the digits.
The four dials are opaque labels compared literally; the digits have no
independent meaning outside a table entry. The range check is indirect: the
dials themselves can only hold `0`–`9` (verified: Left on a `0` shows `9`), so
values outside `0..9` are not expressible through the UI.

## 6. Tables

### 6.1 Accepted password table (ROM `0x08366FF4`)

| Idx | Code | World | Observed effect |
|---|---|---|---|
| 0 | **1608** | 2 | "The Arid Desert", Level 1, no character screen; session character (Raptor in our runs) |
| 1 | **2111** | 3 | "The Hostile Jungle", Level 1, no character screen; session character (Raptor in our runs) |
| 2 | **1705** | 4 | "The Forbidden City", Level 1, no character screen; session character (Raptor ground scene in one run, helicopter scene after playing Owl in another) |
| 3 | **0202** | 1 | "Snow Covered Mountains", Level 1, character select (both) |
| 4 | **1407** | 2 | "The Arid Desert", Level 1, character select (both); **not published** |
| 5 | **2704** | 3 | "The Hostile Jungle", Level 1, character select (both) |
| 6 | **0108** | 4 | "The Forbidden City", Level 1, character select (both) |

The cart has no battery save (IGN's 2004 review notes the omission; mGBA wrote
a 0-byte `.sav`), consistent with the password screen being the progress
shortcut rather than a bonus.

The world-map scene displays one green marker per world stage (1 marker for
world 1, 2 for world 2, 3 for world 3, 4 for world 4), with the crosshair on
Level 1. All seven codes enter Level 1; the table has no mid-world level codes.

World-name text-offset table (`0x08367318`, eight entries):
`0x3EC4, 0x3FFC, 0x412C, 0x4264, 0x458C, 0x4778, 0x4964, 0x5A78`.
The first seven are the seven codes' world strings; the eighth is not
reachable through the password validator.

### 6.2 Published list compared with this ROM

The published corpus is split:

* **1408 group** — GameFAQs GBA cheats (archived 2023-03-31): World 1 `0202`,
  World 2 `1408`, World 3 `2704`, World 4 `0108`; Level 2 `1608`, Level 3
  `2111`, Final Level `1705`. Also SuperCheats (2004), CheatCC, id.wikibooks
  "Panduan Game/GBA/CT Special Forces", and the CT Special Force wiki snippet.
* **1407 group** — Neoseeker, ggmania and cheats42 list World 2 as `1407` with
  the same other six codes.
* VGChartz has no cheat page for this title (only for CT Special Forces 2), and
  TCRF has no CT Special Forces (GBA) page (only the sequel); neither carries a
  1407/1408 literal.

ROM table vs GameFAQs group: six of seven literals match; entry index 4 is
`1,4,0,7`, and the published `1408` is rejected by this ROM. The ROM matches the
1407 group exactly. The labels "Level 2/3/Final" in the GameFAQs group describe
worlds, not mid-world levels: 1608/2111/1705 all open Level 1 of worlds 2/3/4.

## 6b. Enumeration

**Space definition.** Four decimal dials, each a complete `0`–`9` cycle
(`0` wraps to `9` with Left; `9` wraps to `0` with Right). No other symbols,
no blank dial, no variable length. Total representable values:
`10 × 10 × 10 × 10 = 10,000`.

**Validator model.** A literal 7-entry lookup, digit-by-digit, first match wins;
otherwise `-1`. Reimplemented in `enumerate.py`; the model accepts exactly the
seven table entries over the whole `0000`–`9999` space and rejects everything
else. The model and the ROM agree on every entry because the ROM's elements
*are* the model (the validator reads the same seven 4-byte records); in
addition, all seven accepts and five rejects were entered on the real screen
(section 7).

**Code absent from GameFAQs / VGChartz / TCRF / the wikis.**

* **`1407`** — index 4. GameFAQs (archived), SuperCheats, CheatCC, id.wikibooks
  and the CT Special Force wiki print `1408`; none of those sources contains
  `1407`. Entered on the password screen: accepted, shows "Select your
  character", then the world map reads **"The Arid Desert" / "Level 1"**, and
  the mission loads the desert level. Screenshots: `code1407.png` (character
  screen), `map1407_full.png` (map), `code1407_game3.png` (desert gameplay).
* Older mirrors (Neoseeker, ggmania, cheats42) do list `1407`; the finding is
  the split corpus, not that no source anywhere ever printed it.

**Behaviour the published character labels omit.**

* The fan wiki labels `1608`/`2111` as "Raptor" and `1705` as "Stealth Owl", as
  if each code fixed a character. The ROM table has no character field (four
  digit bytes only) and the validator returns only an index, so the label
  cannot be a property of the password alone. Consistent with that, the same
  code produced different scenes in different sessions: `1705` started a
  Raptor ground scene after a Raptor run (`code1705_game.png`), and after
  Stealth Owl was played and the menu re-entered in the same session, `1705`
  started world 4's helicopter scene (`owl_clean.png` → `1705_clean_game.png`).
  The exact state variable carrying the character is reported as unknown.

**Bounds proven by rejection** (all shown "Wrong Password" and re-zeroed the
dials):

| Test | Result | Meaning |
|---|---|---|
| `1408` | rejected | the published code is not in this ROM's table |
| `1406` | rejected | one digit away from accepted 1407; match is exact |
| `9999` | rejected | maximum dial value, no checksum accepts it |
| `0000` | rejected | minimum value |
| `2202` | rejected | digit transposition of 0202 |

**Why there are no further codes.** The validator loops `i = 0..6` and compares
all four digits; `0x0800BE0C` branches to the rejection path only on `-1`. The
only writer that can store a non-zero accepted index at `0x0300385E` is that
same success branch; the other writer (`0x0800BD6C`, in the screen init)
clamps an out-of-range remembered index to 0. A code outside the seven table
rows cannot reach the world/character scene through the UI. The space is
therefore closed: **10,000 inputs, exactly 7 accepts**.

## 7. Validation evidence

**Observed (emulator screenshots / key reads).**

* All seven table codes entered on the real screen; all accepted.
* `1407` accepted, `1408` rejected with "Wrong Password" (`code1408_wrong.png`).
* Session-dependent start for a no-select code: `1705` rendered the Raptor
  ground scene in one run (`code1705_game.png`) and the world-4 helicopter
  scene after Stealth Owl had been played in the same session
  (`owl_clean.png` → `1705_clean_game.png`). The password table carries no
  character field.
* Re-entering the password screen after a valid code prefills the dials with
  the last accepted code (`pw_prefill_0202.png` shows 0202 after playing 0202;
  `pw_prefill_1705.png` shows 1705 after playing 1705), confirming the
  accepted-index persistence and the `0x0800C110` prefill helper.
* `1406`, `9999`, `0000`, `2202` rejected with "Wrong Password".
* Dial wrap `0 → 9` and `9 → 0`; digits are `0`–`9` only.
* Menu enumeration with screenshots: L.S.P. logo, language select, title
  "Press Start", main menu (4 items), character select, world map (worlds
  1–4, Level 1), mission briefing, gameplay (snow, desert, jungle, city),
  pause + quit confirmation, options (Music/Sfx/Credits), credits scroll,
  multiplayer "Waiting Room" (Player 1/Player 2), password screen.
* Pause ignores Select/L/R/D-pad (pixel-identical frames); only A/B act.
* Title ignores the Konami sequence and Select/L/R patterns (no screen change
  beyond background animation). Holding Select through boot still reaches the
  normal language screen; holding L+R+Select through boot skipped the language
  screen and landed on the copyright title screen. No debug screen appeared in
  either case.
* Map D-pad does not move the level marker; the map always shows Level 1 for
  these codes.

**Derived (disassembly).**

* The validator at `0x0800C0A8` compares four s16 fields at scene offsets
  `0x52/0x86/0xBA/0xEE` against `0x08366FF4[i*4 + 0..3]`, loops `i=0..6`,
  returns the index or `-1`.
* The password screen allocates a `0x1EC`-byte scene object, stores its
  pointer at `0x03000160`, and `0x0800C110` prefills the dials from a table
  row when the screen is re-entered with a remembered index.
* The world-map scene indexes `0x08367318` with the accepted index to choose
  the world-name text.
* All UI text is rendered as byte-sized glyph indices through `0x08019A6C`,
  not ASCII — so the `strings` scan is not a complete text search.

**Inferred.**

* The three no-character-select codes skip the selector rather than assigning a
  character; the published "(Raptor)/(Stealth Owl)" labels are not encoded in
  the password. The character state carried between scenes produces the
  observed difference. The exact variable that carries it was not isolated;
  the paired gameplay runs are the evidence.
* The `0x08367318` eighth entry (`0x5A78`) is probably an unused/cut world or
  map name; it is not reachable from the password route.

## 8. Unknowns

* Whether a US/JP revision of `AC7E` uses `1408` instead of `1407`. This report
  is about the EU multi-language image hashed above; the six-language boot
  screen and `E` code are the evidence for the SKU.
* The variable/struct field that carries the selected character from the
  character screen into the next mission. The inheritance behaviour is
  observed; its address is outside the password validator and was not needed
  to model the code space.
* A glyph-level search for the words "DEBUG"/"CHEAT"/"SECRET" was not possible
  without decoding the font; the negative for hidden menus rests on walking
  every reachable screen and on the button-mask/table scans below, not on an
  ASCII hit.
* No mid-world level select was found: all codes start Level 1, and the map's
  D-pad does not move the marker. Later levels are reached by play; the
  password table exposes world starts only.

## 9. Negative-search bounds

* `strings -t x -n 4` over the whole 4 MiB: 43,143 strings; zero hits for
  `password|passwd|cheat|code|debug|secret|unlock|level|stage|mission|warp`
  except the Shin'en GAX banner (`GAX Sound Engine 2.3B (Apr 15 2002) ©
  Shin'en Multimedia. Code: B.Wodok`) at `0x3656C8` and a music credit
  (`"maintheme" © Manfred Linzner` at `0x4501E`).
* Published-code literal search in ASCII, raw digit bytes, u16 decimal and u16
  BCD: the only table-shaped hit is the validator table at `0x366FF4`. The
  byte tuple `01 04 00 08` (published 1408) occurs only at `0x95161` and
  `0x952B7`, inside OAM/sprite structures, never in a code table.
* Button-mask scan: every maximal run of ≥3 consecutive little-endian u16
  values drawn from the GBA key set
  `{1,2,4,8,0x10,0x20,0x40,0x80,0x100,0x200}` was enumerated (847 runs).
  Only 9 are referenced by a ROM pointer; each was inspected and is non-input
  data (e.g. the palette-rotation table at `0x0836AF04`, the ID list at
  `0x082DAD3C`, music/level data). No cheat-sequence table was found.
* All screens reachable from the title/menu were walked and captured; no
  hidden or debug entry appeared.

## 10. Tooling / reproducibility

* `keys.py` — Xvfb/XTEST key driver (`xdotool`), screenshot crop
  (`720x480+152+144`).
* `pw_enter.py` — enters a 4-digit code from the zeroed dial state.
* `enumerate.py` — reads the ROM table at `0x366FF4`, validates all 10,000
  inputs, prints the accepted set and the rejected probes.
* mGBA 0.10.5 (SDL), Xvfb `:221`, openbox, scrot, ImageMagick.
* Evidence screenshots (`/tmp/opencode/ctsf1/`): `code1407.png`,
  `code1407_map.png`, `code1407_game3.png`, `code1408_wrong.png`,
  `code1406_wrong.png`, `code9999.png`, `code0000.png`,
  `pw_0202_result.png` (the 2202 rejection), `map0202_full.png`,
  `map1407_full.png`, `map1608_full.png`, `map2111_full.png`,
  `map2704_full.png`, `map0108_full.png`, `code1608_game.png`,
  `code2111_game.png`, `code1705_game.png`, `pause0.png`, `pause_quit.png`,
  `options0.png`, `credits1.png`, `challenge_enter.png`,
  `title_from_menu.png`, `pw_wrap9.png`, `owl_clean.png`,
  `1705_clean_game.png`, `pw_prefill_0202.png`, `pw_prefill_1705.png`.

## 11. Legal note

No ROM, extracted graphics, music or game text is redistributed here. Only
hashes, addresses, the algorithm and the seven short numeric passwords
(already publicly documented for this game) are reported.
