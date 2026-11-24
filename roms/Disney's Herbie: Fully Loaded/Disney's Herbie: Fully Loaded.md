# Disney's Herbie: Fully Loaded (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Disney's Herbie: Fully Loaded/Disney's Herbie: Fully Loaded.gba` |
| Size | 8,388,608 bytes (0x800000, exactly 8 MiB, no appended data) |
| Header title | `HERBIE FL` (0x00-padded) |
| Game code | `B8FE` (0xAC) |
| Maker code | `4Q` (0xB0) — Buena Vista / Disney |
| Software version | 0 (0xBC) |
| Main unit / device | 0x00 / 0x00 |
| Entry word | `0xEA00002E` → 0x080000C0 (stock ARM branch) |
| Complement check | 0x66 (0xBD) — **correct** for 0xA0–0xBC |
| Header checksum | stored `0x0000` (0xBE); recomputes to `0x009A` |
| Nintendo logo | canonical, single hit at file 0x4 — one image, not a multicart |
| Save hardware | EEPROM 512 B ("EEPROM_V124" driver at 0x799328), `.sav` created on demand |
| MD5 | `9824d54e798f7985d620b41abd722993` |
| SHA-1 | `6a9d8f05a8517a92d1908a8a5845c128bf42a573` |
| SHA-256 | `e6ebc443c1e7d9f6c2244613d96f14ae20df5448b269fc13f27c27ae3ccca920` |

**Patch/trainer check.** The entry branch is the stock `b 0x080000C0`; 0x080000C0 is a
normal ARM crt0 (register clear, CPSR/SP setup, IRQ vector install, jump through the
0x080004A4 literal = `0x08013571`, i.e. `main` at 0x08013570 Thumb). No cracktro, no
trainer menu, no second header, no appended payload. The only header anomaly is the
zeroed header checksum with a *correct* complement byte — the classic artefact of a
rebuilt/re-dumped header (§16.1 of the guide), not a modified program.

## 2. Executive summary

**This GBA SKU has no password, no keypad/code-entry screen, no button code, and no
reachable debug menu.** It is a Climax Studios (GBA) racing title whose only
in-game progress currency is the EEPROM save. What the game *does* have is a fully
gated unlock system, and this report enumerates it exactly.

Findings in order of importance:

1. **Screen/state space enumerated.** The engine keeps a 61-entry task descriptor
   table in EWRAM at 0x02000000 (pointer at 0x03000004), 12 bytes per entry, entered
   by `0x08013B44(id)`. 38 entries are live, 23 are zero, and the table ends with
   `0xFFFFFFFF` at index 61. Every screen reachable from the title was walked and its
   current task index read from RAM (see §4/§6).
2. **No code-entry surface.** The whole ROM contains zero occurrences of
   `PASSWORD`, `CHEAT`, `DEBUG`, `SECRET` (case-insensitive); the localized string
   table (0x079AA60, 24 bytes/record, 6 language pointers) contains no alphabet,
   keypad, name-entry, or "enter code" UI. The published material that exists for
   this SKU (archived GameFAQs cheats page, Almar's Guides, Cheat Happens,
   GameHacking.org, CheatCodes.com) is **only** Action Replay / CodeBreaker
   memory patches ("Unlock All Tracks 2ADDE25E BF09C48B", master code
   e59de6a7/b3668f3f/4d0fdd7c/a7c40c64); the archived GameFAQs cheat page itself
   lists no entries at all. Those are memory-write codes, not in-game codes, and
   are out of scope. Their literal text and opcode words are absent from the ROM
   (0 occurrences each), as expected for host-side patches.
3. **Exactly one input reader.** Only one routine reads `KEYINPUT`
   (0x04000130): `0x08004BC4`. It stores a 10-bit held mask at 0x030004BC,
   computes the new-press mask in a register (it is not stored as a mask) and
   writes ten per-button held bytes plus ten per-button new-press bytes. A
   complete scan of every literal reference to all 20 flags
   (90 sites) shows only single-frame menu/gameplay checks — **no sequence matcher,
   no prefix+action dispatcher, no mask table** (§6b bounds).
4. **The unlock system, reversed end-to-end.** Progress lives in EEPROM as 64
   byte-reversed 8-byte records: `{u16 magic 0xCAFE (even) / 0xFEED (odd),
   u16 w1, u16 w2, u16 check = magic^w1^w2^0xBABE}`. Story slot *s* uses records
   2s and 2s+1; the engine's progress index is `w1 >> 12` of the highest-scoring
   slot (0x08013810/0x08013878), cached at 0x030020E8.
5. **The Championship gate is exactly `progress > 3`.** At 0x080141D0 the menu
   dispatcher loads 0x030020E8, sets target screen 37 (the "Championship Mode is
   still locked…win 4 races in Story Mode" message) and only picks screen 21
   (difficulty select) when the value is ≥ 4. Proven both ways in the emulator:
   value 3 → locked screen; value 4 → difficulty screen; value 4 with a corrupt
   XOR checksum → locked screen (see §6b).
6. **Content tables.** 8 race tracks (string IDs 41–48) and 10 driver slots
   (IDs 30–39: Herbie, Chip, Rusty, Javier, Jackson, then **five** `????`
   placeholders), 3 difficulties, 2 options
   (Music 3-state, Sound effects 2-state), pause = Continue/Quit. Two `?`
   placeholder strings sit inside the main-menu label run (IDs 3 and 5) — evidence
   of two removed menu entries, not of a reachable screen.
7. **Leftover developer text** found and classified: `Legals go here` /
   `Rechtstext` placeholders, an `abcde`/`fghij`/`klmno` font-test triple, and the
   Shin'en GAX banner `Shin'en Multimedia. Code: B.Wodok` (a known false positive
   for "code", §11 of the guide).

**No usable in-game code can be published for this title.** The report therefore
delivers the bounded negative required by §0.2 plus the complete enumeration of the
one system that exists (the save-gated unlock tree).

## 3. How to reproduce

Emulator: mGBA SDL (`mgba -3`) on `Xvfb :324`, `SDL_AUDIODRIVER=dummy`.
Keymap used: `x`=A, `z`=B, `a`=L, `s`=R, `Return`=Start, `BackSpace`=Select,
arrows=D-pad. Hold each key 100–150 ms; menus drop keys pressed back-to-back, so
leave ≥0.5 s between presses and verify each transition with a screenshot.
`Shift+F1` saves state, `F1` loads it.

### 3.1 Screen walk (all observed)

| Step | Input | Screen (task index) |
|---|---|---|
| 1 | boot | Disney Interactive logo → Climax/title |
| 2 | A on title | Main menu (9): Story Mode / Free Race / Championship / Options |
| 3 | Down×3, A | Options (10): Music, Sound effects |
| 4 | A on Music | Music submenu: Always on / Off for races / Always off |
| 5 | B,B, Up×3, A | Story Mode track-select (58) — only Downtown Race |
| 6 | B,B, Up, A | Free Race (21) difficulty: Easy / Hard / Extreme |
| 7 | A | Free Race track-select (23) — only Downtown Race |
| 8 | A | Race (48), 3 laps, HUD `Lap 0/3`, `Pos 5/5` |
| 9 | Start | Pause overlay: `GAME PAUSED` → Continue / Quit |
| 10 | Down, A on pause | `QUIT: ARE YOU SURE?` → Yes / No (2-item ring) |
| 11 | B… A on Championship (fresh save) | Locked message (37) |

Menu ring sizes measured by wrapping: main = 4 (Down from Options returns to
Story), difficulty = 3 (Up stops on Easy), pause = 2 (Down stops on Quit),
options = 2, quit-confirm = 2 (Yes/No).

### 3.2 Reaching a save-gated state without racing

The game loads EEPROM at boot and caches the 64-record table at `[0x03002120]`
(EWRAM). Because EEPROM records are stored **byte-reversed** relative to the RAM
record, a crafted 512-byte `.sav` can present arbitrary progress. This was used
only as an oracle to read the gate and the save layout, exactly like the §16.19
"call the validator" technique; it is not an in-game code and is not presented as
one.

```python
import struct
def rec(magic, w1, w2):
    c = magic ^ w1 ^ w2 ^ 0xBABE
    return struct.pack("<HHHH", magic, w1, w2, c)[::-1]   # EEPROM = reversed
data = bytearray(b'\xff' * 512)          # blank EEPROM
data[0:8]  = rec(0xCAFE, 0x4000, 0x0000) # slot 0 record A: chapter nibble = 4
data[8:16] = rec(0xFEED, 0x0000, 0x0000) # slot 0 record B
open("herbie.sav","wb").write(data)
```

Boot with that file: Championship opens the Easy/Hard/Extreme screen (21) instead
of the locked message (37). With `w1 = 0x3000` (nibble 3) it stays locked; with
`w1 = 0x4000` and a wrong checksum it also stays locked.

## 4. Address map

All ROM addresses are `0x08000000 + file_offset`.

### 4.1 Engine / input

| Address | Meaning |
|---|---|
| 0x080000C0 | ARM crt0; main pointer literal at 0x080004A4 |
| 0x08013570 | `main` (Thumb): IRQ setup, init, then frame loop |
| 0x08013B44 | `switch_screen(id)`: indexes the task table by `id*12`, pushes task |
| 0x02000000 | Task descriptor table (61 × 12 bytes), ptr at 0x03000004 |
| 0x03000000 | Current task pointer (index = (ptr−0x02000000)/12) |
| 0x08004BC4 | **Only** KEYINPUT reader (`ldrh` from 0x04000130) |
| 0x04000130 | KEYINPUT (active low) |
| 0x030004BC | Held mask, active high (`raw ^ 0x3FF`) |
| 0x03000700/0x03000358/0x03000138/0x03000B10/0x030005EC/0x03000B18/0x03000440/0x03001FD8/0x03000578/0x03000B1C | held A,B,Select,Start,Right,Left,Up,Down,R,L (1 byte each) |
| 0x0300057C/0x03001FB0/0x03000538/0x03001EC4/0x030005B4/0x03000C50/0x03000318/0x0300009C/0x030004F8/0x03000240 | new-press A,B,Select,Start,R,L,Right,Left,Up,Down |

### 4.2 Menus / progress

| Address | Meaning |
|---|---|
| 0x08013F59 | Main-menu scene init (screen 9) |
| 0x08013F6D | Generic menu/track-select init (screens 23/24/60) |
| 0x08013FF1 | Story track-select init (screen 58) |
| 0x0801416C | Menu action dispatcher: item id → screen id |
| 0x080141D0 | **Championship gate**: `if ([0x030020E8] > 3) → 21 else → 37` |
| 0x0801422C | Widget helper returning the activated item id (0x3E–0x43) |
| 0x030020E8 | Progress/chapter index (0…), the gate input |
| 0x030020E4 | progress value + 1 (best slot) |
| 0x030020C8 | best slot index + 1, masked to 31 |
| 0x03002120 | Pointer to the 64-record save table in EWRAM |
| 0x03002134 | Per-menu unlock/allowed mask |
| 0x030020FC | Main-menu cursor index |
| 0x08013810 | Compute best slot: loop 32 slots, call 0x08013878 |
| 0x08013878 | Validate slot: read records 2s/2s+1, checksum, magic, extract |
| 0x080138EC | Record checksum: `w0 ^ w1 ^ w2 ^ 0xBABE`, compare to w3 |
| 0x08013924 | Copy 8-byte record *n* from table `[0x03002120]` |
| 0x0801CE84 / 0x0801CEB4 | chapter→track order: `1,2,3,1,2,3,4,5,6,7,8,0` |
| 0x0801CEC0 | track list `1..8` |
| 0x0801CF08 | Cumulative track-bit masks `2,6,14,30,62,126,254,510` |

### 4.3 Text

| Address | Meaning |
|---|---|
| 0x079AA60 | Localized string pointer table, 24 bytes/record |
| — record layout | `[EN, FR, DE, EN, EN, EN]` u32 pointers (ES/IT/NL fall back to EN) |
| 0x0681000–0x0683B00 | String data (ASCII, NUL-terminated) |
| 0x06836F0 | `????` (driver slot) |
| 0x068386C | `Options` |
| 0x06838C0 | `Free Race` |
| 0x0683B00 | `?` placeholder |

## 5. Algorithm

### 5.1 Save record validation (reimplemented from 0x08013878/0x080138EC)

```
record[i] = { u16 magic, u16 w1, u16 w2, u16 check }       # 8 bytes, i in 0..63
valid(r)  = (r.check == (r.magic ^ r.w1 ^ r.w2 ^ 0xBABE))
slot(s)   = (r = record[2s], q = record[2s+1])
            if valid(r) and valid(q) and r.magic == 0xCAFE and q.magic == 0xFEED
                value  = (r.w1 << 16) | q.w2
                count  = r.w1 >> 12            # high nibble
best      = max over s in 0..31 of value   (0x08013810)
progress  = count of the best slot           -> 0x030020E8
```
(`0x030020E4 = value+1`, `0x030020C8 = best_index+1 & 31`.)

On-disk (EEPROM) byte order: each 8-byte record is the byte-reverse of the RAM
record. Blank EEPROM is 0xFF; a blank record fails the magic test and is ignored.

### 5.2 Unlock gate (0x0801416C..0x08014212)

```
activate(item):
  ...
  if item == 0x42:                          # Championship
      target = 37                           # "is still locked" screen
      if [0x030020E8] > 3: target = 21      # difficulty select
  ...
  switch_screen(target)
```
Screen 21 is shared with Free Race; screen 37 is the five-line locked message
(string IDs 101–105).

### 5.3 Chapter → track list

`0x0801CE84` / `0x0801CEB4` hold `1,2,3,1,2,3,4,5,6,7,8,0` (12 chapters → track
ids). Story track-select (screen 58, init 0x08013FF1) uses
`mask = 0x0801CF08[[0x030020E8]]`, i.e. the cumulative bit set
`2,6,14,30,62,126,254,510,…` for chapter 0,1,2,3,4,5,6,7. With chapter 0 only the
first track (Downtown Race) is offered, which reproduces the fresh-save screen.
The exact render rule for the extra tracks is **inferred** (see §8).

## 6. Tables

### 6.1 Localized string IDs proven relevant

| ID | EN text |
|---:|---|
| 0 | Press the A Button to start |
| 1/2/4/6 | Story Mode / Free Race / Championship / Options |
| 3, 5 | `?` (placeholders between menu labels) |
| 7–16 | Music / Sound effects / Always on / Off for races / Always off / On / Off |
| 27–29 | Easy / Hard / Extreme |
| 30–39 | driver slots: 30 Herbie (FR: Choupette), 31 Chip, 32 Rusty, 33 Javier, 34 Jackson, 35–39 `????` |
| 41–48 | Downtown Race, Pro Racing Oval, City Harbor, Desert Race, Boulevard Racing, Mountain valley, Waterfront Race, Amusement Park |
| 244–246 | `abcde`, `fghij`, `klmno` (font-test leftovers) |
| 275–277 | GAME PAUSED, Continue, Quit |
| 413–415 | QUIT: ARE YOU SURE?, Yes, No |
| 86/87 | You have unlocked / a new race track. |
| 91/92/96/97 | Saving unlocked / race: / Unlocked race / saved: |
| 101–105 | Championship Mode / is still locked: to / unlock it, you must / win 4 races in / Story Mode. |

### 6.2 Option values

| Screen | Item | Values |
|---|---|---|
| Options | Music | 0 = Always on, 1 = Off for races, 2 = Always off |
| Options | Sound effects | On / Off |

### 6.3 Progress field

| Field | Width | Notes |
|---|---|---|
| magic | 16 | 0xCAFE even record, 0xFEED odd record |
| w1 | 16 | high nibble = chapter/win count (gate input), low 12 bits free |
| w2 | 16 | second progress word (any value; checksum-covered) |
| check | 16 | XOR of the three words with 0xBABE |

## 6b. Enumeration

**Space definitions.**

* *Typed code space:* **none.** There is no input field, alphabet, length rule or
  checksum for user text. The searched text space is the complete localized string
  table: **425 records × 6 language slots = 2,550 pointers, 233 distinct English
  strings**, 0 of which describe a code/password entry (see §7 for the counts).
  Therefore no novel typed code can exist.
* *Button-code space:* **none.** The engine's entire key-state surface is the
  twenty flag bytes listed in §4.1. All 90 literal references to those flags were
  enumerated; they fall into five clusters (menu widgets 0x08001070–0x08001C6C,
  gameplay/menu logic 0x08004280–0x08004B88, the input writer 0x08004BC4–0x08004C76,
  the held-key ramp 0x08004D7E–0x08004E1A, and one gameplay site 0x0800E5BE).
  (0x03000700 is A-held, not a 10-bit new-press mask; the new-press mask exists
  only transiently in a register at 0x08004BDA.)
  No function retains a press history, compares a sequence, or dispatches on a
  prefix. Multi-button handling in the binary is limited to instantaneous pairs:
  the documented L+R "special trick" (0x080045DE / 0x08004682 read L_new/R_new)
  and A/B held pairs inside the driving/menu logic (0x08004280, 0x08004460,
  0x0800463E). None of these compares an ordered sequence.
* *Save/progress space (the system that does exist):* 64 records × 8 bytes;
  16-bit magic + 16-bit check. For a story slot the *semantic* space used by the
  gate is the 4-bit high nibble of `w1`, i.e. **16 representable chapters**
  (values 0–15). 2^16 checksum-correct spellings exist per (w1,w2) because the
  low 12 bits and w2 are unconstrained by the gate (aliases).

**Novel value minted and confirmed in-game (not in any published list).**
`w1 = 0x4ABC`, `w2 = 0x1234`, correct checksum `0x5228` (EEPROM record
`28 C8 12 34 4A BC CA FE`). This value appears in no FAQ, wiki or cheat list
(none of them describe the save format at all). Observed effect: selecting
Championship opens the Easy/Hard/Extreme screen instead of the locked message.
Screenshot: `g_four_abc.png` (Championship difficulty screen after the crafted
save). This also proves the low 12 bits and w2 are aliases: changing them does not
change the gate outcome.

**Bounds proven by rejection.**

| Input | Expected | Observed |
|---|---|---|
| `w1 = 0x3000` (count 3), valid checksum | locked | screen 37 "Championship Mode is still locked…" (`g_champ_3.png`) |
| `w1 = 0x4000`, checksum field forced to 0x0000 | rejected | screen 37, i.e. record discarded (`g_badck.png`) |
| `w1 = 0x4000`, valid checksum | unlocked | screen 21 (`g_champ2.png`) |
| `w1 = 0x4ABC`, valid checksum | unlocked, same result | screen 21 (`g_four_abc.png`) |

The 3-vs-4 pair is the exact boundary of the `> 3` comparison; the checksum case
proves the validity layer is independent of the value layer.

**Reachable screen IDs read from RAM** (task index = (ptr−0x02000000)/12):
9 main menu, 10 options, 21 difficulty, 23 Free-Race track select, 37 Championship
locked message, 48 race, 58 Story track select. The remaining live entries of the
61-slot table (2,3,4,6,7,8,11,12,13,18,19,20,24,31–36,39–42,47,49–53,59,60) are
**inferred** (from their position around the boot/race flow) to be the boot/logo
sequence, cut-scenes, results/podium and save-prompt scenes; the two `?` menu
strings (IDs 3,5) have no reachable item, and the observed menu ring is 4.

## 7. Validation evidence

### Observed (emulator screenshots, RAM/state reads)

* Full screen walk of every menu (title, main ×4 items, options ×2, music ×3,
  difficulty ×3, story/Free-Race track select, race, pause ×2, Championship lock).
* Main-menu ring wraps at 4 items; options at 2; difficulty at 3; pause at 2.
* Track-select screen does not change with Left/Right/Up/Down (six presses
  recorded) — only the chapter's track is previewed.
* `0x030020E8` = 0 on a fresh/blank save, = 4 with the crafted record, and the
  Championship branch follows it.
* Save table at `[0x03002120]` contains the crafted records byte-reversed; with a
  reversed-order file the game parsed it (wins 4), with the un-reversed file it did
  not (wins 0) — this established the byte order.
* Task index read from `[0x03000000]` at each screen (values in §6b).

### Derived (instruction sequence)

* Single KEYINPUT reader at 0x08004BC4 and the twenty flag addresses.
* Gate comparison `cmp r0,#3 / ble` at 0x080141D6 selecting screen 37 vs 21.
* Save validation (magic 0xCAFE/0xFEED, XOR 0xBABE) at 0x08013878/0x080138EC.
* Task table size 61 with 0xFFFFFFFF terminator; 38 live entries.
* String table geometry (24-byte records, six language pointers).

### Inferred

* The exact track-list render rule for chapters > 0 (the mask table is read at
  0x08013FF8, but the preview/selection UI for extra tracks was not exercised).
* The two `?` menu strings correspond to two removed main-menu entries; the
  dispatcher handles six item IDs (0x3E–0x43) while only four are shown.
* Whether `0x030020E8` is best labelled "chapter" or "story wins" — the code uses
  it as both (order table index and gate input); the text says 4 races.

### Negative evidence with counts

* `strings -t x -n 4` → 164,435 lines. Case-insensitive hits for
  `password|cheat|code|debug|secret|unlock|car|track` = 21. All classified:
  5 real unlock/UI strings (0x683100–0x6833C0), 1 soundtrack credit false positive
  (`Code: B.Wodok`), 1 `????` name, 15 compressed-graphics coincidences.
* `PASSWORD`, `CHEAT`, `DEBUG`, `SECRET`: **0 hits each** in the entire image.
* Full decode of the 425-record string table: the only keyword hits are
  `You have unlocked` (86), `Saving unlocked` (91), `Unlocked race` (96),
  `unlock it, you must` (103) and `Special Thanks` (156) — four unlock messages and
  one credits line. No `enter`, `name`, `keypad` or alphabet label exists.
* `0x04000130`: 2 occurrences (0x4C84 pool of the reader; 0x16BC8 inside a halt
  loop). No second reader, no `KEYINPUT` polling elsewhere.
* Mask-table scan: 18 runs of ≥5 halfwords drawn from the single-button mask set
  `{1,2,4,8,0x10,0x20,0x40,0x80,0x100,0x200}` exist in the image. 16 have no
  literal pointer at all; 0x022E3C is referenced by 0x08012974 and is a signed
  16-bit **sine/cosine table** (angle, mirrored at 0x100−i), and 0x67B7DC lies
  inside a compressed graphics block. None is a cheat/button-code table.
* Published lists: the archived GameFAQs cheats page (Wayback capture 20201009)
  has **no** cheat entries for this game. The only published GBA codes anywhere
  (Almar's Guides, Cheat Happens, GameHacking.org) are Action Replay/CodeBreaker
  memory patches — out of scope, and their ASCII hex and binary opcode words do
  not occur in the image (checked: `2ADDE25E`, `BF09C48B`, `e59de6a7`,
  `b3668f3f` = 0 hits each). TCRF's page documents only the Shin'en GAX credits
  and error strings and lists no debug menu or code. No published in-game
  password/button code exists to test; the negative is therefore bounded by the
  string/table/input space above, not by a list.

## 8. Unknowns

* The full behaviour of the per-chapter track mask (`0x0801CF08`) when reading the
  track-select list was not exercised beyond chapter 0 (only one track shown, and
  Left/Right is inert on that screen in every tested state). The *gate* is proven;
  the *presentation rule* for later tracks is inferred.
* The exact roles of the 30+ live task entries that correspond to cut-scenes,
  results and save prompts were not individually mapped to names; only the seven
  player-facing screens were identified.
* The meaning of the two `?` placeholder menu strings (IDs 3 and 5) is unknown
  beyond "unused label beside the main-menu labels".
* `0x030020E4/C8` are written by 0x08013810 but their consumers were not traced.
* The `abcde`/`fghij`/`klmno` string triple (IDs 244–246) has no identified screen;
  it is most likely a font/kerning test left in the string bank.

## 9. Tooling

* `mgba -3` + `Xvfb :324` + `openbox`, `xdotool` for XTEST input, `import`/`convert`
  for screenshots (`import -window root`, crop 720×480+152+144).
* mGBA savestates (PNG `gbAs` chunk, zlib) parsed with Python to read RAM without a
  debugger: header 0x0, VRAM 0x1000, IWRAM 0x19000, EWRAM 0x21000.
* Python 3 + `capstone` for Thumb literal-pool xref scans; `arm-none-eabi-objdump
  -M force-thumb` for range disassembly.
* Helper scripts (in `/tmp/herbie`): `key.py`/`h.py` (input + state
  capture), inline scripts for string-table decode, record encode/decode, xref
  enumeration and mask scanning. Screenshots (`g_*.png`) were kept in that work
  directory during the engagement; each claim above is also stated in words plus a
  RAM/address fact so it does not depend on the image.

## 10. Legal note

No ROM, graphics, audio or extracted game text is redistributed here. Addresses,
record formats, hashes and reimplemented algorithms only.
