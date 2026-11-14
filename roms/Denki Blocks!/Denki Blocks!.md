# Denki Blocks! (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Denki Blocks!/Denki Blocks!.gba` |
| Size | 4,194,304 bytes (4 MiB) |
| Header title | `DENKIBLOCKS!` (12 bytes, no padding) |
| Game code | `ADBE` |
| Maker code | `5G` |
| Unit / device / version | 0 / 0 / 0 |
| Entry word | `0xEA00002E` (stock crt0 branch) |
| Complement byte | `0x7F` (recomputed = `0x7F`, valid) |
| Header checksum word | `0x0000` (recomputed = `0x0581`; invalid) |
| MD5 | `8b7a6c21e2619dbfb5064c76d074f582` |
| SHA-1 | `4ed60ea5a72e44b0014a4db1553fd5daf1f6339d` |
| SHA-256 | `693368f79ede129b6bde2b635737de9bcaf178e806230e97db9e2eabf6e1c90b` |

**Embedded GBA-image scan.** Searching the whole 4 MiB for the 156-byte Nintendo
logo (`24 ff ae 51 …`) returns exactly one hit, at file offset `0x4` (the primary
header). There is no second image, no multiboot stub, no concatenated pack and no
appended trainer. The first 4 KiB is the normal crt0/IRQ stub
(`0x080000C0`–`0x080001E8`, ARM), so the ROM is not a cracktro build.

The only header anomaly is the zero checksum word with a *correct* complement
byte: the classic artifact of a header that was rebuilt by a dumper/tool after
the fact, not a gameplay patch. Nothing else in the first 4 KiB is non-stock.

This image is the **US (Majesco) SKU**: the first-run language screen offers
only two flags (USA / Spain), even though the ROM carries text banks for five
European languages plus a second English bank (see §4.3).

## 2. Executive summary

Denki Blocks! has **no password, no button-code, and no in-game cheat system.**

* The complete text corpus was decoded and enumerated: **7 banks × 635 strings =
  4,445 strings**. A normalised keyword scan over all of them yields **0 hits**
  for `PASSWORD`, `PASSW`, `CHEAT`, `DEBUG`, `SECRET`, `UNLOCK`, `CODE`,
  `LEVEL SELECT` and `SOUND TEST`.
* The only keyboard-like input surface in the game is **Player Name Entry**
  (a 7-slot profile name). Its charset is a plain alphabet (locale-dependent:
  A–Z for English, A–Z plus Ñ/Ö/Ü for Spanish), and the buffer is only rendered
  in Player Select / rankings — no expected-name table, no rejection message and
  no comparison against the typed buffer was found.
* The only code-shaped artifact is a **hidden developer TEST menu** (screen
  state `0x31`) whose strings are `TEST`, `MUSIC TEST`, `NOISE TEST`,
  `STOP MUSIC / NOISE` and **`ACTIVATE ALL FEATURES`**. It is **dead code**:
  its draw handler has exactly one reference (dispatch-table slot 47 ⇒ state
  49), the screen-state variable has exactly three writers, and the single
  "set next screen" function is called from 50 sites whose constant and
  table-derived values never include `0x31`. No input path can request it.
* What the game *does* have is an **unlockable economy**: Denki Stars are
  awarded for Bonus Shapes and Three-of-a-Kind, and are spent on the 25
  Club "Special Puzzles"; eight Tournament rankings award trophies. All of
  that is save-flag progression, not a code system (and it is gated by a
  star-balance check, which was exercised and rejected on screen).

Therefore the deliverable for §0.2 is a *bounded negative*: the full text
space, the full screen-state space, the full button-input surface and the
published-code space were each enumerated, and the one hidden menu found is
proved unreachable rather than merely un-found.

## 3. How to reproduce

```bash
cd /tmp/opencode/denkiblocks
cp "/mnt/gbacheats/roms/Denki Blocks!/Denki Blocks!.gba" denki.gba
Xvfb :301 -screen 0 1024x768x24 &
DISPLAY=:301 openbox &
DISPLAY=:301 SDL_AUDIODRIVER=dummy mgba -3 denki.gba &
W=$(DISPLAY=:301 xdotool search --name mGBA | head -1)
DISPLAY=:301 xdotool windowfocus "$W"
```

Keymap used (mGBA SDL defaults): **A = `x`, B = `z`, L = `a`, R = `s`,
Start = `Return`, Select = `BackSpace`, D-pad = arrows.** Hold keys 120–350 ms;
the title screen in particular ignores a very short Start press.

Menu path used for every observation below:

```
boot → language (USA / Spain) → Character Select → Player Name Entry (B = back,
or navigate to the bottom-right END cell and press A) → Player Select →
title ("PRESS START" / "Pulsa START" → A or Start) → Mode Select
  ├─ Aprendizaje/Training  → Lesson Select (4×7 lesson grid)
  ├─ Solo → Torneo/Tournament → Puzzle Island map → stage intro → puzzle
  │        └─ Start in a puzzle → Pause: Continuar / Reiniciar / Salir
  ├─ Varios/Versus (Islanders, Guests, Link, Battle, All Change, Race)
  └─ El Club → Trophies / Special Puzzles / Extra!
                 └─ Special Puzzles: 5×5 grid, locked cells reject with
                    "YOU DON'T HAVE ENOUGH DENKI STARS FOR THIS PUZZLE."
```

There is **no settings/options screen** in this title. `OPTIONS` appears in the
string table only as `PERFECTO. OPTIONS` / `WORKOUT OPTIONS` / `BATTLE OPTIONS`
/ `ALL CHANGE. OPTIONS` / `RACE OPTIONS` — per-mode rule summaries, not a
settings menu. The only choice-screen is the one-time first-run language
selector (USA / Spain); sound and volume have no UI at all, which is exactly
why the unused developer `MUSIC TEST / NOISE TEST` menu exists.

Reproduction notes:

* A fresh save is needed to see the language/character/name flow; with a save
  present it boots to Player Select.
* `-t state.ss1` loads an mGBA savestate (PNG with a zlib `gbAs` chunk); the
  raw layout used for RAM reads was IWRAM at `0x19000` and EWRAM at `0x21000`,
  so `0x03006AF8` is readable at state offset `0x1FAF8`.
* A RAM proof was taken by writing a savestate while a key was held and reading
  the key-state word: holding `Return` gives `held = 0xFC08` at `0x03001420`
  (bit 3 = Start, upper bits are the unused KEYINPUT padding).

## 4. Address map

### 4.1 Boot / input

| Address | Meaning |
|---|---|
| `0x080000C0` | ARM crt0 (stock) |
| `0x0800176C` | key poll: `held = ~KEYINPUT & 0x3FFF` → `0x03001420`; `pressed = held & ~prev` → `0x03001422` |
| `0x080019F8` | single-mask hold/auto-repeat helper (`held & 0x3FF == mask`, 15-frame arm, then every 5 frames); **not** a sequence matcher |
| `0x08001798`…`0x080019F0` | per-button "is held / is pressed" helpers (Up, Down, Left, Right, A, B, L, R, Start, Select) |
| `0x0800A054` | `set_next_screen(id)`: `[0x03006AEC] = id & 0xFF`, `byte[0x030031A5] = 1`, `byte[0x03006B20] = 1` |
| `0x08009C2C` | screen-state updater: copies `[0x03006AEC]` into `[0x03006AF8]` (0x08009C7E), resets per-screen bookkeeping |
| `0x08009FDC` | hard reset path: `[0x03006AF8] = 0x53` (out-of-range sentinel) |
| `0x0800BA50` | special transition that writes `4` to `[0x03006AEC]` |

### 4.2 Screen-state machine

| Address | Meaning |
|---|---|
| `0x03006AF8` | current screen id (2 … 0x52) |
| `0x03006AEC` | pending/next screen id |
| `0x03006AF4` | last screen *type* (used to detect a type change) |
| `0x03006B20` | "screen changed" flag |
| `0x03007230` | pointer to the current per-type struct |
| `0x08019C1A` | dispatch: `id-2`, bound `0x50`, jump table `0x08019C3C` (81 entries, ids 2–0x52) |
| `0x080384C4` | screen table, 12-byte entries `{script_ptr, type, 0}`, 83 entries (ids 0–82) |
| `0x08037C7C` | per-type struct table, stride 40 bytes, field `[1]` = menu/script pointer |
| `0x08019A84` | "enter screen": type compare, table lookup, struct pointer store, init call |
| `0x08019628` | generic menu renderer (12-byte item structs, string id at +0) |
| `0x0800DB70` | localised string resolver (7 branches) |

Reachable states observed (RAM-verified via savestates):

| State | Screen |
|---|---|
| `0x0E` (14) | title |
| `0x0F` (15) | Mode Select |
| `0x10` (16) | Solo Game Select |
| `0x2A` (42) | Lesson Select (training grid) |
| `0x2B` (43) | The Club menu |
| `0x2D` (45) | Trophies |
| `0x2E` (46) | Special Puzzles grid |
| `0x47` (71) | Puzzle Island / Tournament map |
| `0x48` (72) | stage intro / wizard cutscene |
| `0x4F` (79) | lesson/puzzle gameplay |

### 4.3 Localised text banks

`0x0800DB70` selects one of seven (offset-table, base) pairs on the language
byte at `0x03003424`. Each table holds **635 little-endian u32 offsets** into
its bank; string bytes are NUL-terminated. Control bytes `0x00`–`0x1F` are
spaces/punctuation, `0x20`–`0x3F` are letters `A`–`Z` shifted by −0x1F, `0x40`–
`0x7A` are plain ASCII, `0x80`–`0x9F` are accented glyphs.

| # | Language | Offset table | Text base |
|---|---|---|---|
| 0 | English (EU) | `0x0802C7C0` | `0x083B358D` |
| 1 | French | `0x0802D1AC` | `0x083BA2DF` |
| 2 | Italian | `0x0802DB98` | `0x083C17CD` |
| 3 | German | `0x0802E584` | `0x083C8147` |
| 4 | Spanish | `0x0802EF70` | `0x083CF42A` |
| 5 | English (US) | `0x0802F95C` | `0x083D6655` |
| 6 | unused/alternate bank | `0x08030348` | `0x083DD39E` |

The US language screen offers only banks 0/5 (English) and 4 (Spanish); the
French, Italian and German banks are shipped but not selectable in this SKU.

### 4.4 Screen-name table

`0x083B35D0`–`0x083B37F9` holds string ids 1–41, a block of **41 screen/menu
labels** at the head of the English bank (id 0 is the title tagline):

```
PRESS START · PLAYER SELECT · CLEAR PLAYER? · CHARACTER SELECT ·
PLAYER NAME ENTRY · MODE SELECT · SOLO GAME SELECT · RANKING SELECT ·
PUZZLE SELECT · PERFECTO. OPTIONS · PERFECTO. RESULTS · WORKOUT OPTIONS ·
WORKOUT RESULTS · OPPONENT SELECT · ISLANDER SELECT · GUEST SELECT ·
LINKED PLAYERS · VERSUS GAME SELECT · BATTLE OPTIONS · BATTLE STATISTICS ·
BATTLE RESULTS · ALL CHANGE. OPTIONS · ALL CHANGE. STATISTICS ·
ALL CHANGE. RESULTS · RACE OPTIONS · RACE STATISTICS · RACE RESULTS ·
LESSON SELECT · THE CLUB · RECORDS · TROPHIES · PAUSED · MEETING POINT ·
OK. · BACK · MOVES · TIME · MOVES PAR · TIME PAR · BEST MOVES · BEST TIME
```

### 4.5 Hidden TEST screen (dead)

| Address | Meaning |
|---|---|
| `0x08019E04` | dispatch handler for state `0x31`; its only body is `bl 0x0801720C` |
| `0x0801720C` | builds and draws the TEST menu: string ids 631/632/633/634 at y = 64/80/96/112, x = 64 |
| `0x083BA29B` | `"TEST"` (string 630) |
| `0x083BA2A0` | `"MUSIC TEST"` (631) |
| `0x083BA2AB` | `"NOISE TEST"` (632) |
| `0x083BA2B6` | `"STOP MUSIC \c NOISE"` (633) |
| `0x083BA2C9` | `"ACTIVATE ALL FEATURES"` (634) |
| `0x080381A4` | type-0x21 struct (field 1 = `0x080373B8`) |
| `0x080373B8` | screen script: `(630,80,16)`, then ids 97/98/94/95/41/40 (TIME TAKEN / MOVES MADE / THINKING TIME / MOVING TIME / BEST TIME / BEST MOVES) |
| `0x080384C4 + 12*49` | screen-table entry 49 = `{0x080372A0, 0x21, 0}` |

### 4.6 Unlock / trophy strings (English bank)

| id | String |
|---|---|
| 289 | `YOU DON'T HAVE ENOUGH DENKI STARS FOR THIS PUZZLE.` |
| 288 | `PLAY SPECIAL PUZZLES MADE IN THE OFFICIAL DENKI BLOCKS. CLUB.` |
| 324 | `WELCOME TO THE OFFICIAL DENKI BLOCKS. CLUB.` |
| 330 | `EACH PLAYER HAS <13><16> PUZZLES. SOLVE ANY <12><16> TO BEAT THE PLAYER AND WIN A TROPHY.` |
| 619/627 | `YOU CAN SWAP DENKI STARS FOR SPECIAL PUZZLES IN THE OFFICIAL DENKI BLOCKS. CLUB.` |
| 618/626 | `… YOU GET SPECIAL DENKI STARS.` |
| 166/167/168 | pause entries: `RETURN TO PLAY.` / `RESET THE PUZZLE TO ITS ORIGINAL STATE.` / `STOP PLAYING.` |

## 5. Algorithm

### 5.1 Screen state machine (the only "menu logic" in the game)

```
frame:
  if byte[0x03006B20]:                 # a screen change was requested
      state = u32[0x03006AEC]          # 0x08009C7E
      ...
  if state < 2 or state > 0x52: goto default
  handler = jump_table[0x08019C3C + 4*(state-2)]
  handler()
```

`set_next_screen(id)` is the only pending-state writer:

```
0x0800A054:
  byte[0x030031A5] = 1
  u32[0x03006AEC]  = id & 0xFF
  byte[0x03006B20] = 1
```

### 5.2 Code input / validator

There is none. No routine reads a character buffer and compares it with a
literal or a table in this image: the only text table is the localised display
bank, and there is no expected-name table or invalid-code message. The only
text-entry screen (Player Name Entry, state 5)
indexes a per-language alphabet (string id 45) and copies the chosen glyphs
into the save record; the buffer is only consumed by the player-list/ranking
renderers. There is no `INVALID` / `INCORRECT` / `CODE` message in any of the
4,445 strings, and no second 32/36-symbol alphabet anywhere in the image.

The only sequence-sensitive input helper in the ROM (`0x080019F8`) matches a
**single exact mask** held for 15 frames (`held & 0x3FF == mask`), i.e. menu
auto-repeat, not a multi-button code; there is no press-history ring buffer.

## 6. Tables

### 6.1 Screen-id domain (81 slots)

Dispatch accepts ids `2 … 0x52`. The reachable set produced by the 50
`set_next_screen` call sites is:

```
constants: 1, 2, 7, 8, 9, 10, 11, 12, 15, 17, 18, 19, 23, 37, 42, 43, 45,
           46, 47, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 71, 72, 73,
           74, 78
table-derived: bytes from 0x0802C0B8+8 and +12 (values 0x01,0x02,0x04,0x05,
           0x0e,0x0f,0x10,0x11,0x14,0x15,0x17…0x2b,0xfe,0xff)
direct stores: 0 (init), 4 (0x0800BA66), 0x53 (reset sentinel, 0x08009FF4)
```

### 6.2 TEST menu entries

| id | Label | Column/row in draw code |
|---|---|---|
| 630 | `TEST` | script entry (80,16) — title |
| 631 | `MUSIC TEST` | menu row 0, y=64 |
| 632 | `NOISE TEST` | menu row 1, y=80 |
| 633 | `STOP MUSIC / NOISE` | menu row 2, y=96 |
| 634 | `ACTIVATE ALL FEATURES` | menu row 3, y=112 |

Labels are identical in all five localised banks — the strings were never
translated in FR/IT/DE/ES, another sign of developer-only leftovers.

### 6.3 Player Name Entry alphabet

String id 45 is per-language: `ABCDEFGHIJKLMNOPQRSTUVWXYZ` (English banks
0/5), and the Spanish bank 4 encodes `A…Z` plus `Ñ/Ö/Ü` (visible on screen).
No symbol set beyond the language alphabet is offered, and the field length is
7.

## 6b. Enumeration

**Space definition.** There is no code space to enumerate: the game contains
no password field and no validator, so the "code space" is empty by
construction. What was enumerated instead is every space in which a code could
hide, with exact counts:

1. **Text space — 4,445 strings (7 banks × 635), fully decoded.** Keyword scan
   (`PASSWORD`, `PASSW`, `CHEAT`, `DEBUG`, `SECRET`, `UNLOCK`, `CODE`,
   `LEVEL SELECT`, `SOUND TEST`) = **0 hits**. The 41-entry screen-name table
   (§4.4) names every UI screen, and none of them is a code screen.
2. **Screen-state space — 81 states (2…0x52)**, dispatch table at
   `0x08019C3C`. Ten states were visited and RAM-confirmed (§4.2), and sixteen
   screens were walked visually (title, language, player select, character
   select, name entry, mode select, solo select, training lesson select,
   lesson demo, tournament map, stage intro, puzzle, pause, club, trophies,
   special-puzzle grid). All 81 table slots were decoded; only slot 47
   (state 49) is the TEST menu.
3. **Input space — every key consumer.** 50 `set_next_screen` call sites, all
   resolved to constants or table bytes (§6.1). One single-mask hold helper
   (`0x080019F8`) is the only sequence-like matcher; it is a menu auto-repeat
   and accepts one exact mask, not a sequence. No history buffer exists.
4. **Save/unlock space.** Club Special Puzzles are a 5×5 = **25-cell grid**;
   eight Tournament rankings yield trophies; stars come from Bonus Shapes and
   Three-of-a-Kind. The gate is a star-balance comparison, not a code.

**Novel values generated.** None are possible: with no encoder there is
nothing to mint. The nearest construct is the unreachable TEST menu, whose
"novel" entry (`ACTIVATE ALL FEATURES`) was catalogued but cannot be entered
from any input path — see the rejection proof below.

**Bounds proven by rejection.**

* *Hidden TEST menu — unreachable (dead code).* The draw handler
  `0x0801720C` has exactly one xref: `0x08019E04`, i.e. dispatch slot 47. The
  current screen id is written in only three places: `0x08009C7E`
  (copy of `0x03006AEC`), `0x08009B68` (zero-init) and `0x08009FF4`
  (`0x53` reset). `0x03006AEC` is written only by `0x0800A054`
  (`set_next_screen`) and once with constant `4` at `0x0800BA66`. Of the
  **50** `set_next_screen` call sites, **0** pass `0x31`; the two table-driven
  sites read `0x0802C0B8+8`/`+12`, whose complete value set contains no
  `0x31` (§6.1). All four debug strings (ids 631–634) are referenced only from
  inside `0x0801720C`, and `TEST` (630) only from its screen script
  (`0x080373B8`). A live test that forces `0x03006AF8 = 49` in a savestate
  produces the screen's frame (a Back button appears) but not a reachable
  entry from gameplay, confirming that no normal transition exists.
  **Bounded statement: the TEST screen is present but unreachable; no button
  combination can request state 0x31.**
* *Unlock gate — rejected on screen.* Selecting a locked Club puzzle with
  0 Denki Stars produces the game's own refusal, string 289
  ("YOU DON'T HAVE ENOUGH DENKI STARS FOR THIS PUZZLE."), and no puzzle
  starts. This is the in-game rejection that bounds the unlock system.

**Published codes tested.** GameFAQs has no cheat page for the GBA SKU,
CheatHappens lists none, and no password list exists for this version. The only
circulating GBA codes are two libretro **CodeBreaker** entries — an enable code
and "Infinite Time" (`83006A2C 0000`) — i.e. emulator memory writes, not
in-game content; they are explicitly out of scope here and were not used as
evidence. No GBC/DS/Gizmondo/PSP password was found to apply: those versions
have no code surface either, and the GBA text space above proves no such
strings ship in this image.

## 7. Validation evidence

**Observed (emulator / RAM):**

* Boot flow, every menu listed in §3, puzzle playfield and the 3-entry pause
  menu (`Continuar/Reiniciar/Salir`) all reached by ordinary input on `:301`.
* Club → Special Puzzles shows a 5×5 grid, a "0" star counter and TIEMPO/MOVES
  PAR; A on a locked cell shows "You don't have enough Denki Stars for t…".
* The Spanish run shows the localised alphabet (Ñ/Ö/Ü) in Player Name Entry
  and the Spanish UI, while the language screen offers only USA/Spain.
* Savestate RAM reads confirm the screen id at `0x03006AF8` for each screen
  (§4.2), and `held = 0xFC08` while `Return` is down.
* Forcing `[0x03006AF8]=49` in an uncompressed savestate makes the screen frame
  (Back button) appear, but no reachable transition does so.

**Derived (instructions):**

* `0x0800A054` is the sole pending-screen writer; `0x08009C7E` copies it into
  the live state.
* Dispatch slot 47 (table entry at `0x08019C3C + 4*47`) is the only reference
  to the TEST-menu draw routine `0x0801720C`; the enum of 50 call sites
  contains no `0x31`.
* The text resolver's seven banks, 635 entries each, were decoded offline; the
  keyword counts in §6b come from those 4,445 strings.
* `0x080019F8` implements a one-mask 15-frame hold, not a sequence.

**Inferred:**

* The labels for the TEST entries are self-describing; the *effect* of
  `ACTIVATE ALL FEATURES` (presumably setting all save/feature bits) was not
  executed, because the screen is unreachable without debugger intervention.
  This is reported as inferred, not observed.
* The 7th text bank appears to be an alternate/unused encoding (its bytes do
  not decode under the same glyph map as banks 0–5) and is not selectable.

## 8. Unknowns

* The exact star price per Club Special Puzzle and the precise star award
  table were not enumerated; the report only proves the gate exists and
  rejects at 0 stars.
* `ACTIVATE ALL FEATURES`' concrete effect is unproven (dead screen).
* The 7th text bank's encoding was not resolved; nothing in the two selectable
  languages references it.
* The Versus sub-menus (Islander Select, Guest Select, Linked Players, Battle /
  All Change / Race options) were not entered: they require 2–4 linked
  consoles. Their labels and rule text are part of the 4,445-string corpus and
  contain no code, password or unlock entry point; only the single-player and
  Club paths were walked.
* Whether a hardware-only debug path (e.g. a dev cartridge build) existed is
  outside the image; this ROM contains no such entry point.

## 9. Tooling

* `mgba` (SDL) under `Xvfb :301`, `xdotool` XTEST input, root-window
  `import` + `convert` crops.
* Python 3 with `capstone` 5.0.7 for Thumb disassembly, BL-target scans,
  literal-pool resolution and register tracking.
* `arm-none-eabi-objdump -M force-thumb` for manual confirmation of every
  quoted instruction range.
* Custom savestate reader (`state.py`, PNG `gbAs` + zlib; IWRAM `0x19000`,
  EWRAM `0x21000`) and patcher (`patchstate.py`) used for RAM reads and the
  state-49 reachability probe.
* Text enumerator (`banks.py`) producing the 4,445-string corpus and keyword
  counts.

**Legal:** no ROM, graphics, audio or text assets are redistributed in this
report; only addresses, algorithms, string identifiers and my own observations
are published.
