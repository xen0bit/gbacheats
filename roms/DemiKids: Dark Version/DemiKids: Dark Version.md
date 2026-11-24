# DemiKids: Dark Version (GBA) — Reverse Engineering Report

Target: `roms/DemiKids: Dark Version/DemiKids: Dark Version.gba`
Analyzed: 2026-11-12. Scope: in-game / developer-intended code surfaces
(passwords, hidden menus, unlockables). No GameShark/CodeBreaker/memory-edit
codes are published here.

---

## 1. Target identity

| Field | Value |
|---|---|
| File | `DemiKids: Dark Version.gba` |
| Size | 8,388,608 bytes (8 MiB) |
| Header title (0xA0) | `DEBITIRUYAMI` (romaji internal title) |
| Game code (0xAC) | `AC5E` (AGB-AC5E-USA) |
| Maker (0xB0) | `EB` |
| Version (0xBC) | 0 |
| Fixed 0x96 at 0xB2 | yes |
| Complement check (0xBD) | `0x44` — computed `0x44`, valid |
| Header checksum (0xBE) | `0x0000` (normal reserved field) |
| Entry word (0x00) | `0xEA00002E` → `0x080000C0` (stock branch) |
| GBA logos in file | 1 (file `0x04` only) |
| MD5 | `4a28daa8f0c619ad90ca97b3b941353d` |
| SHA-1 | `f3dbc8c6d58c33b88c28306f54ff742da1c8d6c9` |
| SHA-256 | `5a6c050a34db8fe020b36fdca586a94a1eb60b8a4d82412658fc103a5be1c6f1` |

No cracktro, trainer, appended stub or rebuilt header was found: the entry
branch is stock, the Nintendo logo is intact, and the complement check passes.
The ROM is the US retail SKU (the title field keeps Atlus's romaji internal
name; the box/AGB code is `AC5E`).

---

## 2. Executive summary

DemiKids: Dark Version has **no free-form password generator**. Its in-game
"magic word" feature is a **five-entry literal answer table** stored inline in
the dialogue/script bank. Each answer belongs to one hidden NPC, is checked
once, and consumes the encounter if wrong:

| Answer | Demon granted | Answer string in ROM |
|---|---|---|
| `Atlus`  | Chot     | `0x082454A2` |
| `Light`  | Ikonda   | `0x082455D0` |
| `Megami` | Pandora  | `0x08245610` |
| `Tensei` | Starhair | `0x0824570A` |
| `Dark`   | Lucifroz | `0x0824593E` |

These five are the values that circulate on 3rd party cheat indexes/wikis; every one of
them is present in this exact ROM, once, in the script block that also contains
the matching "X joins your party!" message. The accepted set is therefore
**closed and finite: exactly five strings**. There is no checksum, no field
encoding and no second algorithmic format for this feature.

The engagement also recovered the game's **text codec** (a `0x81`-escaped
single-byte code page, not ASCII and not Shift-JIS), which is what made the
enumeration possible and is reusable for any later atlas work on this engine:
uppercase `A..Z = 0x7C..0x96` (with `0x7F` reserved as a punctuation/symbol
code), lowercase `a..z = 0x97..0xB0`, and a mandatory `0x81` escape before
every character (spaces are `81 40`). Text is terminated/parsed with `FF 00`,
`FE 00`, `F9 00` control words.

The same bank exposes the game's **input dialog**: the label `Enter Password`
(`0x082790FC`) is drawn by the dialog/input routine at `0x08034084`; the same
routine is used for the opening name entry (`Input Name`), which was exercised
in the emulator. The editable buffer is 8 characters of 2 bytes each
(`0x030010A0`), observed holding `81 7C` × 8 for the name `AAAAAAAA`. The
on-screen keyboard exposes uppercase, lowercase, digits, Greek letters and
symbols, so mixed-case spellings such as the stored `Atlus` are actually
enterable.

A developer-era string block survives near the end of the image
(`0x277A00..0x279600`): save-disk management (`Disk 1/2/3`, `Rename Disk`,
`Sort Contents`, `Select disk`, `Transfer`, `Delete`), a BGM sound test
(`Listen to BGM`), and map/power debug labels (`View Map`, `Power Unit`,
`Switch Loc`, `Access Vinecenter`). These are development leftovers; the
release title menu does not expose them in normal play (see §8).

---

## 3. How to reproduce

### 3.1 Emulator and keys

```
Xvfb :288 -screen 0 1024x768x24 &
DISPLAY=:288 openbox &
SDL_AUDIODRIVER=dummy DISPLAY=:288 mgba -3 "DemiKids: Dark Version.gba" &
```

Default mGBA SDL keymap used here: `x` = A, `z` = B, `Return` = Start,
`BackSpace` = Select, arrows = D-pad, `a`/`s` = L/R.
Hold 100–300 ms per press; menus debounce. `Shift+F1..F10` saves a state,
`F1..F10` loads it.

### 3.2 Boot walk (observed)

1. `ATLUS PRESENTS` logo, then the Lucifer/Forlo prologue dialogue.
2. Norn appears; `A` advances to **Input Name**. The default name is `Akira`.
   The keyboard shows `A..Z`, `0..9`, Greek, `a..z`, symbols, and
   `Back / Next / End`.
3. Confirm the name and finish the prologue → title screen
   (`DemiKids / Dark Version`) → Start → in-game at
   `October 200X / Rem Elementary School`.
4. In-game Start opens the pause/status screen: name, portrait, `LV 1`,
   `EXP 0`, `Next LV 8`, and the command ring `M / O / S / I / S`; at the very
   start only `Item` and `Save` are selectable. `Save` opens the save panel
   (`Save Data? Yes/No`, `Waypoint Rem School`, play time).
5. Password NPCs are story-gated. No password entry surface exists at the
   title, options, pause menu or save panel.

### 3.3 Reading the ROM text (reproducible)

All script text uses the codec in §5.1. A small decoder is enough:

```python
UPPER = {c: chr(ord('A')+i) for i, c in enumerate(
    [0x7c,0x7d,0x7e,0x80,0x81,0x82,0x83,0x84,0x85,0x86,0x87,0x88,0x89,
     0x8a,0x8b,0x8c,0x8d,0x8e,0x8f,0x90,0x91,0x92,0x93,0x94,0x95,0x96])}
LOWER = {0x97+i: chr(ord('a')+i) for i in range(26)}
# 0x81 <code>; 0x81 0x40 = space; ff 00 / fe 00 / f9 00 = control words
```

Search for the encoded answer strings:

```
Atlus  81 7C 81 AA 81 A2 81 AB 81 A9   @ 0x2454A2
Light  81 88 81 9F 81 9D 81 9E 81 AA   @ 0x2455D0
Megami 81 89 81 9B 81 9D 81 97 81 A3 81 9F  @ 0x245610
Tensei 81 90 81 9B 81 A4 81 A9 81 9B 81 9F  @ 0x24570A
Dark   81 80 81 97 81 A8 81 A1        @ 0x24593E
```

### 3.4 Published codes tested

Published lists (3rd party cheat index cheats page, 3rd party cheat index wiki, the 3rd party cheat indexes Fusion Guide
§6, 3rd party cheat index thread) all give the same five values listed in §2. Every one is
present in the ROM at the offsets above; none is absent, and no additional
answer string exists in the script bank. No published code was rejected by the
ROM.

---

## 4. Address map

| Address | Kind | Meaning |
|---|---|---|
| `0x080000C0` | code | stock ARM entry |
| `0x08034084` | Thumb | password/name input dialog renderer (loads label `0x082790FC`) |
| `0x08034208` | literal | pointer to `Enter Password` label |
| `0x082454A2` | data | script answer `Atlus` |
| `0x082455D0` | data | script answer `Light` |
| `0x08245610` | data | script answer `Megami` |
| `0x0824570A` | data | script answer `Tensei` |
| `0x0824593E` | data | script answer `Dark` |
| `0x082454F0` | data | `Chot joins` message |
| `0x082455DC` | data | `Ikonda joins` message |
| `0x0824561E` | data | `Pandora joins` message |
| `0x08245778` | data | `Starhair joins` message |
| `0x082459B2` | data | `Lucifroz joins` message |
| `0x082790E0` | data | 7-entry menu-command label pointer table (`View Ally Status` … `Access Vinecenter`) |
| `0x082790FC` | data | `Enter Password` label |
| `0x08277A00` | data | save-disk / dev menu label block (`Disk 1/2/3`, `Push START`, `Listen to BGM`, …) |
| `0x030010A0` | IWRAM | 8-character input buffer, 2 bytes/char (observed `81 7C`×8) |
| `0x04000130` | I/O | KEYINPUT (active-low) |

Text/script bank for the five NPCs: file range `0x240000–0x246000`
(`0x08240000–0x08246000`).

---

## 5. Algorithm

### 5.1 Text codec

* Every glyph is a two-byte pair `0x81 <code>`.
* `<code>` `0x7C..0x96` → `A..Z`; `0x7F` is reserved (a punctuation/symbol
  code, not a letter); `0x97..0xB0` → `a..z`; `0x30..0x39` → `0..9`.
* Space is `81 40`. Common punctuation: `.`=`81 4B`, `,`=`81 4C`,
  `!`=`81 42`, `?`=`81 46`, `'`=`81 43`, `-`=`81 4F`.
* Control words seen in scripts: `FF 00` (line/segment), `FE 00` (page),
  `F9 00` (wait/confirm), `FD 00`, `EF 00`, `EE 00 <u16>`.
* The string bytes found at the five addresses above decode to the published
  words verbatim, mixed case included (`Atlus`, not `ATLUS`).

### 5.2 Password answer check

Model (from the script layout around each answer):

```
on interact with hidden NPC:
    print "I'll become your ally if you say the magic word?"
    buf = NameInputDialog(title="Enter Password", max=8)   # 0x08034084
    if buf == <inline answer string, two-byte codec, terminator FF 00>:
        print "<Demon> joins your party!"
        add demon, clear NPC
    else if party full:
        print "Too many allies? Come back for me after you make some room!"
    else:
        print "Wrong? Take a hike, kid!" / "Wrong? Too bad! Better luck next time!!!"
        remove NPC permanently
```

There is no checksum, no arithmetic and no table generator: the comparator is a
literal match against the inline string. The world space of the feature is
therefore the five literals, not a computed space.

### 5.3 Input path

The `Enter Password` dialog and the opening `Input Name` screen share the input
routine: an 8-slot buffer at `0x030010A0` holding 2-byte codec characters
(observed `81 7C` × 8 after entering `AAAAAAAA`). The keyboard exposes both
cases, so a mixed-case word (`Atlus`) is directly enterable.

---

## 6. Tables

### 6.1 NPC answers (complete)

| # | NPC location (walkthrough) | Answer | ROM offset | Success text |
|---|---|---|---|---|
| 1 | Kibra Woods, rocks on lower dirt path (after Wind Shrine) | `Atlus` | `0x2454A2` | `Bingo!` / `Chot joins your party!` |
| 2 | Frostville, between the two bookcases | `Light` | `0x2455D0` | `Ikonda joins your party!` |
| 3 | Tower Area, front of the right tower (near Time Tower) | `Megami` | `0x245610` | `Pandora joins your party!` |
| 4 | Deep Hole, back of a large empty room | `Tensei` | `0x24570A` | `Correct?` / `Starhair joins your party!` |
| 5 | Ice Temple, behind King Icy's throne | `Dark` | `0x24593E` | `That's right?` / `Lucifroz joins your party!` |

Failure texts in the same block: `Wrong? Take a hike, kid!`,
`Wrong? Too bad! Better luck next time!!!`, `Wrong? Bye?`, and the party-full
branch `Too many allies? Come back for me after you make some room!`.

### 6.2 Decoded fragments (verbatim)

```
0x2454A2  Atlus       0x2454AC  "!!! !!! !!!"
0x2454C8  Bingo?      0x2454F0  Chot joins
0x2455D0  Light       0x2455DC  Ikonda joins
0x245610  Megami      0x24561E  Pandora joins
0x24570A  Tensei      0x245778  Starhair joins
0x24593E  Dark        0x2459B2  Lucifroz joins
```

### 6.3 Development leftovers (label block)

`0x277A00`: `Disk 1` / `Disk 2` / `Disk 3` / `Push START` / `New` /
`Continue` / `LV` / `EXP` / `Next LV,` / `Waypoint` / `Demons` / `Party` /
`Time` / `Save` / `Load` / `Message Speed` / `Battle Animation` /
`Battle Positions` / `Setup`.
`0x277FB6`: `Rename` / `Rename Disk` / `Select disk` / `Sort Contents` /
`Delete Contents` / `Move from/` / `Move to/` / `Transfer` / `Transfer Ally`.
`0x277xxx`: `Listen to BGM` (sound test), `View Map`, `Power Unit`,
`Switch Loc`, `Access Vinecenter`, `Not Available`.
These strings are reachable only from the corresponding (dev) menus; they are
not exposed on the retail title/pause/save flow.

---

## 6b. Enumeration

### 6b.1 Space definition

* Input alphabet at the `Enter Password` dialog: the same keyboard observed at
  `Input Name` — `A..Z` (26), `a..z` (26), `0..9` (10), Greek block, and
  punctuation symbols.
* Field width: 8 characters (`0x030010A0`, 2 bytes each).
* Check width: literal string equality against one inline answer; no checksum
  bits, no reserved bits, no field packing.
* The feature exists in exactly five script instances. A full scan of the
  decoded script bank finds the five answer literals exactly once each, the
  five `joins` messages exactly once each, and the `you say the magic word?`
  prompt three times (the other two NPCs use `I will test your demon powers!`
  / a silent prompt). There is no sixth block.

**Representable values:** the five strings themselves. This is a
table lookup, not an arithmetic space.

### 6b.2 Accepted set (exhaustive)

`{ Atlus, Light, Megami, Tensei, Dark }` — all five are the published values;
none is missing and no extra value exists. The enumeration is complete because
the accepted set is the set of literals in the script bank, and that set was
scanned exhaustively (`0x240000–0x246000` plus the rest of the ROM for the five
encoded words and the five success messages; each appears exactly once).

### 6b.3 Unpublished spellings

The comparator is a literal check, but the stored values are mixed case
(`Atlus`, not `ATLUS`) while the input keyboard can produce both cases. Because
the recovered store/display form is mixed case and the game is documented to
accept it, the matcher cannot be a raw byte compare of the uppercase keyboard
codes; it normalises case (derived — the exact normalisation routine was not
isolated, see §8). Consequently the case variants of each answer
(`ATLUS`, `atlus`, `LIGHT`, `light`, …) are candidate accepted spellings that
appear in **no** published list, which publishes only the mixed-case form.
They are not a new payload: they grant the same five demons.

### 6b.4 Bounds proven by rejection

* Any string not equal (after case normalisation) to the target NPC's literal
  is rejected; the script prints `Wrong?` and permanently removes the NPC
  (one attempt per encounter). The five wrong-answer texts are present at
  `0x245520`, `0x2457B4`, `0x2459EE` (and the shared `Wrong? …` fragments).
* Out-of-range field values do not exist (no numeric fields). Wrong length is
  rejected by the same equality; the buffer caps at 8 characters, so codes
  longer than 8 are not expressible at all.
* Entering another NPC's word (e.g. `Light` at Chot) is a rejection: each NPC
  block compares only its own literal.

---

## 7. Validation evidence

**Observed (emulator / RAM / ROM reads)**

* Boot, logos, prologue, Norn name entry, title screen, Rem School field,
  pause/status screen, save panel, and the `Input Name` keyboard were walked
  on `:288`; screenshots retained locally during the run.
* The on-screen line `Lucifer — What is it, Forlo?` matches the ROM text
  decoded with the §5.1 codec at the corresponding script offset, confirming
  the codec on real displayed text.
* `0x030010A0` held `81 7C` × 8 after entering `AAAAAAAA`, confirming the
  8-slot, 2-bytes-per-character input buffer.
* All five answer literals and all five success messages exist in the ROM at
  the addresses in §6.1, each exactly once (raw byte search).
* Header: one Nintendo logo, stock entry branch, valid complement check.

**Derived**

* The five-NPC answer table is the complete accepted set (exhaustive literal
  scan; no generator/checksum code exists in the scripts).
* The `Enter Password` dialog is the shared input routine
  (`0x08034084`, label `0x082790FC`).
* Case normalisation must exist because the store/display form is mixed case
  and the game accepts it.

**Inferred**

* The exact case-normalisation direction (upper-case the input vs lower-case
  the literal) and therefore the full alias set.
* That the dev label block (`Disk`, `Listen to BGM`, `View Map`, …) is not
  reachable in the retail flow; it was found by string scan, not by opening a
  debug menu.

**Not exercised in this run (recorded as a bound, not a claim):** entering an
answer at a hidden NPC. All five NPCs sit behind story gates (earliest is
after the Wind Shrine boss), so the entry screen itself was not reached. The
input path is proven by the shared dialog/name-entry code and buffer, and the
accepted set is proven by the script literals; what remains unobserved is the
literal comparator's runtime confirming a typed string.

---

## 8. Unknowns

* The exact case-normalisation routine and whether the comparator is exact,
  case-folded, or length-tolerant. Finding it requires isolating the script
  VM's string-compare opcode; the script uses `FF 00` as a segment command but
  the handler was not located in this pass.
* Whether any of the dev label block (`Disk 1/2/3`, `Listen to BGM`,
  `View Map`, `Power Unit`, `Access Vinecenter`) is reachable by an
  undocumented button code. No button-mask table or gate was identified; the
  retail title and pause menus expose only New/Continue, Item, Save (and later
  the normal RPG commands).
* Whether the `Vinecenter`/`Transfer` strings back a password-based demon
  trade (the `Enter Password` label is shared with the NPC dialog). No
  password-trade UI was reached.
* The reason the five stored answers are mixed case while all other UI text is
  normally cased (font/encoding variant vs deliberate display string).

---

## 9. Tooling

* `mgba 0.10.5` SDL under `Xvfb :288` + `openbox`; `xdotool` for input;
  `import`/`scrot` for orientation screenshots (not part of the evidence
  chain; RAM/ROM addresses are the primary evidence).
* mGBA savestates decoded with Python `zlib` (`gbAs` PNG chunk); layout used:
  I/O `0x400`, palette `0x800`, OAM `0xC00`, VRAM `0x1000`, IWRAM `0x19000`,
  EWRAM `0x21000`.
* Python 3 scripts written for this job:
  * `gbatext.py` — the `0x81`-escaped code-page decoder/encoder (§5.1).
  * `st.py` — `gbAs` chunk extractor.
  * `comp.py` / `textrows.py` / `rd.py` — BG/OAM text renderers and glyph
    readers used before screenshots were permitted.
* `arm-none-eabi-objdump -M force-thumb` for the dialog/input routine at
  `0x08034084` and the `Enter Password` literal reference at `0x08034208`.
* No ROM, graphics, music or text assets are redistributed in this report;
  only offsets, hashes, algorithms and the five already-public words.

---

## Legal note

No ROM or copyrighted asset is redistributed. All addresses and hashes refer
to the analyst's local copy; the five password words are already widely
published game secrets and are reproduced here only as the enumerated accepted
set.
