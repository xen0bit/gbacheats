# DemiKids: Light Version (GBA) — Reverse Engineering Report

Target: `/mnt/gbacheats/roms/DemiKids: Light Version/DemiKids: Light Version.gba`
Analyzed: 2026-11-14. Scope: in-game / developer-intended code surfaces
(passwords, button codes, hidden menus, unlockables). No GameShark /
CodeBreaker / memory-edit codes are published here.

---

## 1. Target identity

| Field | Value |
|---|---|
| File | `DemiKids: Light Version.gba` |
| Size | 8,388,608 bytes (8 MiB) |
| Header title (0xA0) | `DEBITIRUHIKA` (Atlus romaji internal title) |
| Game code (0xAC) | `AL4E` (AGB-AL4E-USA) |
| Maker (0xB0) | `EB` |
| Version (0xBC) | 0 |
| Fixed 0x96 at 0xB2 | yes |
| Complement check (0xBD) | `0x4F` — computed `0x4F`, valid |
| Header checksum (0xBE) | `0x0000` (normal reserved/rebuilt-header field) |
| Entry word (0x00) | `0xEA00002E` → `0x080000C0` (stock branch) |
| GBA logos in file | 1 (file `0x04` only) |
| MD5 | `f87a7dc67415d1f4c16cc430fcf98d9d` |
| SHA-1 | `8bc80eb5f08bfa83597483390b18092d9a12700d` |
| SHA-256 | `ef4c3e3d2147505a1a61ed3e2c3220c8c23caa2231502a39dfae9c209eff0d0f` |

No cracktro, trainer, appended stub or rebuilt code was found: the entry branch
is stock, the Nintendo logo is intact, the complement check passes and the
first 4 KiB are ordinary ARM crt0 code. The file is the US retail SKU; the
header keeps Atlus's romaji internal title. This is a **different SKU from the
sibling Dark Version** (Game code `AC5E`, title `DEBITIRUYAMI`), so no address
or table was carried over from the Dark report without re-verification.

---

## 2. Executive summary

DemiKids: Light Version has **no free-form password generator and no checksum
code space**. Its in-game "magic word" feature is the same closed set of five
literal answers as the Dark Version, each answer belonging to one hidden NPC.
The **content of the answer set is identical** to the Dark Version; **every
address, the array order and the script table are different** (see §6c).

| Answer | Demon granted | Light answer script | Light join script |
|---|---|---|---|
| `Atlus`  | Chot     | `0x08248FB0` (script id `0x293`) | `0x08248FBC` (`0x298`) |
| `Light`  | Ikonda   | `0x08246478` (`0x294`) | `0x082464C6` (`0x299`) |
| `Tensei` | Starhair | `0x082465E0` (`0x295`) | `0x08246648` (`0x29A`) |
| `Dark`   | Lucifroz | `0x082466BA` (`0x296`) | `0x082466C4` (`0x29B`) |
| `Megami` | Pandora  | `0x082466FC` (`0x297`) | `0x0824670A` (`0x29C`) |

The five words are **standalone one-word scripts** in the game's global script
pointer table at `0x0824B674` (4,566 entries). They occupy ids `0x293`–`0x297`
in the order Atlus, Light, Tensei, Dark, Megami, and are immediately followed by
the five matching "joins your party" scripts at ids `0x298`–`0x29C` in the same
order. That adjacency proves the word→demon binding without relying on any
published list.

The engagement also recovered the engine's text codec (`0x81 <code>` pairs; the
keyboard's glyph codes), the script-bytecode interpreter (Thumb function
`0x0803063C`, opcode dispatch table `0x080306D4`, string-variable opcode `0xEE`
handled at `0x080310DA`), and the name/password keyboard screen that draws the
`Enter Password` label (`0x0827CA10`, draw function `0x08034034`). Two of the
five NPC dialogue groups print the joining demon's name from the demon-name
table `0x0824D504` (indices `0x38`=Starhair, `0x39`=Lucifroz) via the `0xEE`
opcode instead of hard-coding it; they are the same five NPCs, not extra
words.

The ROM also keeps the Dark Version's style of developer leftovers: a label
block at `0x0827C8E8`–`0x0827CA2E` (`View Ally Status`, `Dismiss Ally`,
`View Demonary`, `Change Ally Order`, `Maps CDs Notes`, `Set Power Unit`,
`Access Vinecenter`, `Enter Password`, `Rand`) and a second block at
`0x0827B796`–`0x0827B97A` (`View Map`, `Listen to BGM`, `Power Unit`,
`Switch Loc`, `Rename Disk`, `Transfer`, `Sort`). No retail menu reaches them
(§7, §8).

---

## 3. How to reproduce

### 3.1 Emulator and keys

```
cp "DemiKids: Light Version.gba" /tmp/opencode/demikidslight/game.gba
Xvfb :300 -screen 0 1024x768x24 &
DISPLAY=:300 openbox &
SDL_AUDIODRIVER=dummy DISPLAY=:300 mgba -3 game.gba &
W=$(DISPLAY=:300 xdotool search --name mGBA | head -1)
DISPLAY=:300 xdotool windowfocus $W
```

Default mGBA SDL keymap used: `x` = A, `z` = B, `Return` = Start,
`BackSpace` = Select, arrows = D-pad, `a`/`s` = L/R. Hold 50–300 ms per press;
menus debounce. `Shift+F1..F10` saves a state, `F1..F10` loads it. `Ctrl+R`
resets. Running from a work copy keeps `.sav`/`.ss*` out of the ROM folder.

### 3.2 Boot / menu path (observed)

1. `ATLUS` logo animation (observed screenshot).
2. Title screen: `DemiKids / Light Version`, © 2000, 2002, 2003 Atlus. `Start`
   goes straight into the prologue — there is no New/Continue/Options menu on
   the title (observed twice: first boot and after reset).
3. Prologue: Amy / castle dialogue, dimensional effect, Norn appears.
4. **Input Name** screen: 8-slot field, `A..Z`, `1..5 / 6..0`, `a..z`, Greek,
   symbols, `Back / Next / End`. The default protagonist name is Jin. This is
   the same keyboard used by the password dialog; the password variant draws
   the `Enter Password` caption from `0x0827CA10`.
5. Scripted battle (Kartu → Cherubim), then the Video Arcade in Rem City, then
   Rem Elementary School.
6. In-game `Start` opens the pause/status screen: name, portrait, `LV 1`,
   `EXP 0`, `Next LV 8`, and the command ring `M / O / S / I / S`. At the start
   only `Item` and `Save` are selectable (observed).
7. `Item` opens the item screen with categories `Heal / Attack / Boost / Other /
   Skill / Relic` and `Recover Items`.
8. `Save` opens the save panel: `Save Data? Yes / No`, `LV 1`, `Demons 0`,
   `Party 0`, `Waypoint Rem School`, play time.
9. No password/code screen is exposed by the title, pause, item or save menus.

### 3.3 Reading the ROM text (reproducible)

```python
codes = [0x7c,0x7d,0x7e] + list(range(0x80,0x97))     # A..Z (0x7F skipped)
UP = {c: chr(ord('A')+i) for i,c in enumerate(codes)}
LO = {0x97+i: chr(ord('a')+i) for i in range(26)}     # a..z
DG = {0x72+i: chr(ord('0')+i) for i in range(10)}     # 0..9
# text = 0x81 <code>; 0x00 0xFF ends a script; 0x00 0xFE newline;
#        0x00 0xF9 page/wait; 0x00 0xFD pause; 0x00 0xEE <u16> string variable
```

Examples (raw bytes in this ROM):

```
Atlus   81 7C 81 AA 81 A2 81 AB 81 A9 FF 00   @ 0x248FB0
Light   81 88 81 9F 81 9D 81 9E 81 AA FF 00   @ 0x246478
Tensei  81 90 81 9B 81 A4 81 A9 81 9B 81 9F FF 00 @ 0x2465E0
Dark    81 80 81 97 81 A8 81 A1 FF 00         @ 0x2466BA
Megami  81 89 81 9B 81 9D 81 97 81 A3 81 9F FF 00 @ 0x2466FC
```

Hint text (decoded) at `0x24642A`: `Hint: See Nintendo Power
Volume 175,` — the digits are the glyph codes `0x73 0x79 0x77` = `1 7 5`
(digit codes are `0x72..0x7B` = `0..9`). This is the publisher's own pointer to
the issue that printed the words.

### 3.4 Published codes tested

Published lists checked (GameFAQs cheats page, Planet Cheats, IGN wiki,
SuperCheats, VGChartz):

| Source | Words given |
|---|---|
| Planet Cheats (`planetcheats.net/cheat163.html`, fetched) | Chot `ATLUS`, Ikonda `LIGHT`, Lucifroz `DARK`, Pandora `MEGAMI`, Starhair `TENSEI` |
| GameFAQs cheats page (search snippet; page returns 403) | "Get Chot Atlus; Get Ikonda Light …" |
| GameFAQs Fusion Guide (search snippet) | "the passwords for the Light Version are the same as the Dark Version" |
| IGN wiki (Dark page) | lists the same five words with the Dark SKU's NPC labels |

Every one of the five words is present in this ROM as a standalone answer
script at the addresses above; none is absent, and no sixth standalone answer
word exists (§6b). All five are therefore verified against this exact image.
No published code was rejected by the ROM. (The actual typing step at a hidden
NPC is story-gated — see §7 for the exact bound.)

SKU/encoding check (guide §16.11): the header (`AL4E`, `DEBITIRUHIKA`,
`EB`), the Atlus copyright string and the engine's codec strings confirm this
is the Light SKU, not the Dark image. Each word was searched as plain ASCII,
uppercase ASCII, lowercase, UTF-16LE and UTF-16BE: **zero hits in every ASCII
and UTF-16 encoding**. The only hits are the engine's `0x81 <code>` glyph
encoding, which is the format the on-screen keyboard produces. A published
word that had been absent under *all* encodings would have been recorded as a
different SKU/edition; none was.

---

## 4. Address map

| Address | Kind | Meaning |
|---|---|---|
| `0x080000C0` | code | stock ARM entry |
| `0x0803063C` | Thumb | script/text interpreter (`run_script(win, ptr)`) |
| `0x08030696` | code | opcode fetch; `0x00FF` → close handler |
| `0x080306D4` | data | 26-entry jump table for opcodes `0x00E5`–`0x00FE` |
| `0x080310DA` | Thumb | `0xEE` string-variable opcode handler |
| `0x08031608` | Thumb | `0x00FF` end-of-script handler |
| `0x08031970` | Thumb | `run_script_by_id(id)` (indexes table `0x0824B674`) |
| `0x08034034` | Thumb | draws the `Enter Password` input panel (label `0x0827CA10`) |
| `0x080359A4` | Thumb | demon-name getter, byte index into table `0x0824D504` |
| `0x0824B674` | data | global script pointer table, 4,566 entries |
| `0x0824C0B4` | data | entries `0x290`–`0x29C`: prompt, `!!!`, wrong, 5 answers, 5 joins |
| `0x08248FB0` | data | answer `Atlus` (id `0x293`) |
| `0x08246478` | data | answer `Light` (id `0x294`) |
| `0x082465E0` | data | answer `Tensei` (id `0x295`) |
| `0x082466BA` | data | answer `Dark` (id `0x296`) |
| `0x082466FC` | data | answer `Megami` (id `0x297`) |
| `0x08248FBC` | data | `Chot joins your party` (id `0x298`) |
| `0x082464C6` | data | `Ikonda joins your party` (id `0x299`) |
| `0x08246648` | data | `Starhair joins your party` (id `0x29A`) |
| `0x082466C4` | data | `Lucifroz joins your party` (id `0x29B`) |
| `0x0824670A` | data | `Pandora joins your party` (id `0x29C`) |
| `0x082463C6` | data | magic-word prompt (id `0x290`) |
| `0x082464FA` | data | wrong-answer text (id `0x292`) |
| `0x0824CA2C` | data | 12-entry table of the five NPC dialogue groups |
| `0x0824D504` | data | demon-name pointer table (byte indexed; `0x38` Starhair, `0x39` Lucifroz) |
| `0x0827CA10` | data | `Enter Password` label |
| `0x0827CA2E` | data | `Rand` label |
| `0x0827C8E8` | data | dev menu label block (`View Ally Status` … `Access Vinecenter`) |
| `0x0827B796` | data | dev label block (`View Map`, `Listen to BGM`, `Power Unit`, `Switch Loc`, `Rename Disk`) |
| `0x030010A0` | IWRAM | 8-character name record, 2 bytes per glyph (observed `81 86 81 9F 81 A4` = `Jin`) |
| `0x03007E60` | IWRAM | live keyboard buffer, 8 slots × 2 bytes (observed after entry) |
| `0x04000130` | I/O | KEYINPUT (active-low) |

Script/text banks used by the feature: file range `0x246000`–`0x24A000`
(`0x08246000`–`0x0824A000`); pointer table and demon-name table at
`0x0824B674`/`0x0824D504`.

---

## 5. Algorithm

### 5.1 Text codec

* Every glyph is a two-byte pair `0x81 <code>`.
* `0x7C..0x96` with `0x7F` skipped → `A..Z` (26 codes:
  `7C,7D,7E,80..96`).
* `0x97..0xB0` → `a..z`.
* `0x72..0x7B` → `0..9`.
* `0x40` → space. Punctuation seen: `0x42` `!`, `0x43` `'`, `0x46` `?`,
  `0x4B` `.`, `0x4C` `,`, `0x4F` `-`, `0x44` `(`, `0x48` `&`.
* Script control words are **little-endian `u16`**: `0x00FF` = end,
  `0x00FE` = newline, `0x00F9` = page/wait, `0x00FD` = pause,
  `0x00EE <u16>` = insert a string variable (see 5.3).

### 5.2 Script interpreter

`0x0803063C` prints one script. It decodes glyphs by default; control words
`0x00E5`–`0x00FE` dispatch through the table at `0x080306D4`; `0x00FF` closes
the box and returns. `0x08031970` is the public "run script id" entry: it
indexes the 4,566-entry pointer table `0x0824B674` and calls the interpreter.
This is the mechanism a second analyst can use to re-render any script in the
table.

### 5.3 The magic-word feature

The feature is a literal-table lookup, not an arithmetic code:

```
on interact with hidden NPC:
    print prompt script          # "I'll become your ally if you say the magic word?"
    print hint script            # optional: "Hint: See Nintendo Power Volume 175,"
    buf = keypad_input(8 chars)  # Enter Password panel, 0x81 <code> glyphs
    if buf == <one-word answer script>:
        print success script     # "!!! !!! !!!" + "Bingo?" / "Very good?" ...
        print "<Demon> joins your party" script
    else if party full:
        print "Too many allies? Come back for me after you make some room!"
    else:
        print "Wrong? Take a hike, kid!" / "Wrong? Too bad! Better luck next time!!!"
```

Evidence for the literal comparator: the five answer texts are **standalone
scripts that consist of exactly one word plus `FF 00`**. They are not sentences
(the noun "Light" occurs in ~100 sentences elsewhere but only once as a
one-word script). The failure/success strings are separate scripts, and the
`Enter Password` panel is the shared 8-slot keyboard.

Five dialogue groups are listed in a 12-entry table at `0x0824CA2C`. Two of
the groups (`0x08249160`, `0x0824934E`) parameterise the joining demon's name
with the `0xEE` opcode: `EE 00 38 00` inserts demon-table entry `0x38`
(= `Starhair`) and `EE 00 39 00` inserts `0x39` (= `Lucifroz`). Those two
success scripts render as `Starhair !!! !!! !!! Correct? I'm yours to
command?` and `Lucifroz !!! !!! !!! That's right? I'm officially yours?`.
They are the dynamic-name spellings of the same two NPCs, not additional
words: the answer scripts are still `Tensei` and `Dark`.

`0xEE` argument handling (0x080310DA): `0xFFFF` jumps to `0x08031648`;
`0`, `3`, `4` use the name record `0x030010A0`; `1` uses `0x03001A54`;
`2` uses a runtime string descriptor; any other value is masked to a byte and
looked up in the demon-name table `0x0824D504`.

### 5.4 Input path

The keyboard screen code at `0x08033C00`–`0x08034034` exposes
`A..Z`, `0..9`, `a..z`, Greek and symbols in an 18-column grid, with
`Back / Next / End`. It uses two 8-slot buffers:

* `0x03007E60` — live editing buffer (observed while typing `AATLKI`,
  bytes `81 7C 81 7C 81 90 81 88 81 87 81 85 81 40 81 40`);
* `0x030010A0` — name record (observed `81 86 81 9F 81 A4` = `Jin`, the
  Light Version protagonist).

The password panel variant draws `Enter Password` (`0x0827CA10`) through
`0x08034034`; the name-entry variant draws `Input Name` in the top-right.
Because the field cap is 8 characters, passwords longer than 8 characters are
inexpressible.

---

## 6. Tables

### 6.1 Answer and join scripts (complete, ordered)

| # | id | Answer | bytes | id | Join message |
|---|---|---|---|---|---|
| 0 | `0x293` | `Atlus` | `81 7C 81 AA 81 A2 81 AB 81 A9 FF 00` | `0x298` | Chot |
| 1 | `0x294` | `Light` | `81 88 81 9F 81 9D 81 9E 81 AA FF 00` | `0x299` | Ikonda |
| 2 | `0x295` | `Tensei` | `81 90 81 9B 81 A4 81 A9 81 9B 81 9F FF 00` | `0x29A` | Starhair |
| 3 | `0x296` | `Dark` | `81 80 81 97 81 A8 81 A1 FF 00` | `0x29B` | Lucifroz |
| 4 | `0x297` | `Megami` | `81 89 81 9B 81 9D 81 97 81 A3 81 9F FF 00` | `0x29C` | Pandora |

The order of the answer array and of the join array is identical, which is the
structural proof of the pairing. Human-readable dialogue blocks:

```
0x248F76  "Shouldn't you be in school?"        (Chot lead-in, no hint)
0x248FB0  "Atlus"                              (answer script 0x293)
0x248FBC  "Chot joins your party"
0x2463C6  "I'll become your ally if you say the magic word?"
0x24642A  "Hint: See Nintendo Power Volume 175,"
0x246478  "Light"                              (answer script 0x294)
0x2464C6  "Ikonda joins your party"
0x246532  same prompt + hint
0x2465E0  "Tensei"                             (answer script 0x295)
0x246648  "Starhair joins your party"
0x2466BA  "Dark"  / 0x2466C4 "Lucifroz joins"  (answer 0x296 / join 0x29B)
0x2466FC  "Megami" / 0x24670A "Pandora joins"  (answer 0x297 / join 0x29C)
0x249160  generic Starhair dialogue group (EE 00 38 00)
0x24934E  generic Lucifroz dialogue group (EE 00 39 00)
```

Failure strings: `Wrong? Take a hike, kid!` (`0x2464FA`), `Wrong!!! Please come
again!`, `Wrong? Too bad! Better luck next time!!!`, `Too many allies? Come
back for me after you make some room!` (shared).

### 6.2 Demon-name table (used by `EE`)

`0x0824D504`, 70 pointers, byte indexed. Relevant entries:

```
0x30 Quazir   0x31 ???      0x32 Kibra    0x33 Bludkap  0x34 Oberon
0x35 Andromus 0x36 Sister   0x37 Kyme     0x38 Starhair 0x39 Lucifroz
0x3A Pandora  0x3B Chot     0x3C.. DEV placeholders
```

### 6.3 Developer leftovers (labels only, no retail entry point)

`0x0827C8E8`–`0x0827CA2E`: `Demon types!`, `View Ally Status`, `Dismiss Ally`,
`View Demonary`, `Change Ally Order`, `Maps CDs Notes`, `Set Power Unit`,
`Access Vinecenter`, `Enter Password`, `Rand`.
`0x0827B796`–`0x0827B97A`: `View Map`, `Listen to BGM`, `View Info`,
`Not Available`, `Power Unit`, `L/R Button`, `Switch Loc`, `Summon`, `View`,
`Disk`, `Transfer`, `Sort`, `Rename Disk`.
A block of one-word `DEV` scripts (399 entries, ids `0x555`+) also survives in
the script table, the usual Atlus placeholder pattern for cut strings.

---

## 6b. Enumeration

### 6b.1 Space definition

* **Alphabet at the password panel**: the shared keyboard — 26 uppercase, 26
  lowercase, 10 digits, a Greek block and a symbol block (observed on the
  `Input Name` instance of the same screen).
* **Field width**: 8 glyphs, 2 bytes per glyph (`0x03007E60` live buffer;
  `0x030010A0` record). A 9th character cannot be entered.
* **Check width**: none. There is no checksum, no reserved bit and no numeric
  field. The check is literal equality against a one-word script.
* **Representable values**: the five literals. This is a table lookup, so
  "space size" is 5, not a product of field widths.

### 6b.2 Exhaustive accepted set

`{ Atlus, Light, Tensei, Dark, Megami }` — exactly the five published values,
in table ids `0x293`–`0x297`, each paired in order with joins `0x298`–`0x29C`.
There is no sixth answer.

### 6b.3 Closure proof (counts, so absence is bounded)

The global script table `0x0824B674` was scanned entry by entry (4,566
entries):

| Scan | Count |
|---|---|
| Scripts that are a single word + `FF 00` (letters/digits, 1–12 glyphs) | 563 |
| … `DEV` placeholders | 399 |
| … `Dummy` | 4 |
| … single-letter `r` (credits) | 103 |
| … remaining map/location/credits words | 52 |
| … magic-word answers | **5** |
| Scripts containing `say the magic word` | 4 (2 literal + 2 generic-name groups) |
| Scripts containing `See Nintendo Power` | 4 (Light) vs 3 (Dark) |
| `EE 00 38 00` / `EE 00 39 00` in the magic-word region | 4 each (the generic groups) |

The 52 non-answer words are map/location names (`Hermit`, `Clinic`,
`Frostville`, `Valhalla`, …) and credits labels (`Producer`, `Director`,
`Sound`, …); none is an answer word. The `DEV` and `Dummy` entries are cut
strings (Atlus placeholders), not code words.

### 6b.4 Bounds proven by rejection

* Any non-matching string takes the failure branch: the ROM contains the
  wrong-answer scripts `Wrong? Take a hike, kid!` and `Wrong? Too bad! Better
  luck next time!!!` immediately after the answer scripts. A wrong answer
  consumes the NPC (one attempt per encounter).
* **Length bound**: the panel accepts 8 glyphs; a 9-character word is
  inexpressible.
* **Per-NPC bound**: each NPC compares only its own word. Entering `Light` at
  Chot is the failure branch; the five join scripts are distinct.
* **No field/range layer**: because no answer carries a numeric payload, there
  is no out-of-range value to construct; the whole rejection surface is the
  equality test.

### 6b.5 Novel code / unpublished values

There is no generator and no payload, so — unlike a checksum password system —
**no accepted code can exist that is absent from the published list**: the
accepted set *is* the five literals. The strongest novel-form candidates are
case aliases of the same words (`ATLUS`, `atlus`, …), because the keyboard
offers both cases and the stored forms are mixed case while the published
lists print uppercase (Planet Cheats prints `ATLUS` and is documented as
working). That alias behaviour is reported as **inferred**, not observed: the
case-normalisation routine was not isolated and no NPC could be reached to
type the alias (§7). It is not a new payload; it grants the same five demons.

This is a bounded negative result about the whole feature: 4,566 scripts
enumerated, five answers found, zero generators, zero checksums, zero numeric
fields.

---

## 6c. Sibling SKU comparison (Light vs Dark)

Verified against `/mnt/gbacheats/roms/DemiKids: Dark Version/DemiKids: Dark
Version.gba` (SHA-256 `5a6c050a34db8fe020b36fdca586a94a1eb60b8a4d82412658fc103a5be1c6f1`).

| Aspect | Light | Dark | Same? |
|---|---|---|---|
| Game code / internal title | `AL4E` / `DEBITIRUHIKA` | `AC5E` / `DEBITIRUYAMI` | different |
| Answer set (content) | Atlus, Light, Tensei, Dark, Megami | Atlus, Light, Megami, Tensei, Dark | **identical set** |
| Addresses | `0x248FB0`, `0x246478`, `0x2465E0`, `0x2466BA`, `0x2466FC` | `0x2454A2`, `0x2455D0`, `0x245610`, `0x24570A`, `0x24593E` | different |
| Answer array order | Atlus, Light, **Tensei**, Dark, Megami | Atlus, Light, **Megami**, Tensei, Dark | different |
| Join array order | Chot, Ikonda, Starhair, Lucifroz, Pandora | Chot, Ikonda, Pandora, Starhair, Lucifroz | different |
| Global script table | `0x0824B674`, 4,566 entries | different table/base | different |
| `See Nintendo Power` hints | 4 | 3 | different |
| Generic `EE 00 38/39` dialogue | present at `0x249160`/`0x24934E` | present elsewhere (`0x22041A`, `0x22B936`, `0x23AF78`…) | both have it, different sites |
| Text codec / keyboard / buffer | `0x81 <code>`, 8×2-byte | same | **identical engine** |

So: **the Light Version answer table is content-identical to the Dark Version
(five literal words, same meaning and same demon binding), but it is not the
same table**: every address, the array order and the script-pointer table
differ. The shared codec and the five-word set are the only constants.

---

## 7. Validation evidence

**Observed (emulator / RAM / ROM reads)**

* Boot, ATLUS logo, title screen (`DemiKids / Light Version`), prologue,
  `Input Name`, scripted battle, arcade, school, pause/status, item screen and
  save panel were walked on `:300` (screenshots retained locally during the
  run; not attached).
* The name screen accepted `AATLKI`; Norn addressed the player by that name and
  the in-game pause screen showed it, proving the typed glyphs are stored and
  used as-is.
* `0x03007E60` held `81 7C 81 7C 81 90 81 88 81 87 81 85 81 40 81 40`
  (`AATLKI`) after entry, and `0x030010A0` held `81 86 81 9F 81 A4` (`Jin`),
  confirming 8-slot, 2-bytes-per-glyph storage.
* All five answer byte strings and all five join strings exist at the addresses
  in §6.1 and decode to the published words.
* Header: one Nintendo logo, stock entry branch, valid complement check.
* Script table `0x0824B674` contains ids `0x290`–`0x29C` exactly as listed; the
  answer scripts are one word + `FF 00`.

**Derived**

* The accepted set is exactly the five one-word scripts (exhaustive script
  enumeration; no generator, checksum or numeric field).
* The answer→demon mapping is fixed by the identical order of the answer array
  (`0x293`–`0x297`) and the join array (`0x298`–`0x29C`).
* The `EE 00 38/39` groups are dynamic-name variants of the Starhair/Lucifroz
  dialogues, not extra words.
* The keyboard screen is the password input path (the `Enter Password` label is
  drawn by `0x08034034`, which the keyboard screen calls).
* The dev label blocks are not reachable from the retail title/pause/item/save
  menus: those menus were walked to their leaves and contain no such entry.
  The labels sit in a shared menu-descriptor region at `0x080F5xxx` (the
  descriptor tables at `0x080F5594`/`0x080F55FC` are consumed by generic menu
  code, and the `Enter Password`/`Rand` label pointers are stored at
  `0x080F513C`/`0x080F558C`), so their presence does not by itself imply a
  live retail screen; the apparent self-references in `0x2F1Bxx`/`0x3096xx`
  are coincidence inside compressed data.

**Inferred**

* Case-insensitive matching (uppercase published forms work while the stored
  forms are mixed case). The exact normalisation routine was not isolated.
* That the `M / O / S` ring entries become selectable later in the story; at
  `LV 1` only `Item` and `Save` respond.

**Bound (recorded, not a claim):** no hidden NPC was reachable in this run.
All five sit behind story gates (the earliest is after the Wind Shrine boss in
the Dark walkthrough; the Light Version's chapter flow is equivalent), so the
password panel was exercised only through its shared name-entry instance. The
accepted set is proven by the script table, which is the complete definition of
the feature; what remains unobserved is a typed literal at an NPC, not the
contents of the set.

---

## 8. Unknowns

* The exact case-normalisation code (upper-casing the input vs lower-casing the
  literal), and therefore the full alias set.
* The event-VM opcode that consumes the typed buffer and selects the answer
  script for a given NPC (the NPC event data, not the text printer, holds the
  binding; the text side is fully mapped).
* Whether the two generic-name dialogue groups are alternate map instances or
  the only instances of the Starhair/Lucifroz NPCs.
* Whether any dev label block is reachable by an undocumented button sequence.
  No button-mask table was found (§6b.3): a scan for runs of 4+ active-low
  key masks (`0x001..0x200`) found 59 runs, all inside animation/sprite data
  (`0x0EC1xx`, `0x1013xx`, …), and the Konami sequence in both active-high and
  active-low encodings has zero hits.

---

## 9. Tooling

* `mgba 0.10.x` SDL under `Xvfb :300` + `openbox`; `xdotool` for input;
  `import`/`scrot` for orientation screenshots (RAM/ROM addresses remain the
  primary evidence).
* mGBA savestates decoded with Python `zlib` (`gbAs` PNG chunk); layout used:
  IWRAM at `0x19000`, EWRAM at `0x21000`.
* Python 3 scripts written for this job:
  * `dec.py` — `0x81`-escaped code-page decoder/encoder and run lister.
  * `find.py` — encoded-literal search with counts.
  * `wordscripts.py` — walks the 4,566-entry script table and classifies
    one-word scripts (the closure proof).
  * `hdr.py` — header/logo/hash check.
  * `st.py` — `gbAs` chunk extractor and IWRAM/EWRAM reader.
  * `keys.py` — XTEST key helper.
* `arm-none-eabi-objdump -M force-thumb` for the interpreter
  (`0x0803063C`), opcode dispatch (`0x080306D4`), `EE` handler
  (`0x080310DA`), demon-name getter (`0x080359A4`) and the password panel
  (`0x08034034`).
* No ROM, graphics, music or text assets are redistributed in this report;
  only offsets, hashes, algorithms and the five already-published words.

---

## Legal note

No ROM or copyrighted asset is redistributed. All addresses and hashes refer to
the analyst's local copy; the five password words are already widely published
game secrets and are reproduced here only as the enumerated accepted set. The
ROM was analyzed from a work copy; the original ROM folder was left containing
only the `.gba`.
