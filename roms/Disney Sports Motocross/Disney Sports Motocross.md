# Disney Sports Motocross (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Disney Sports Motocross/Disney Sports Motocross.gba` |
| Size | 16,777,216 bytes (16 MiB) |
| Header title | `DS_MOTOCROSS` (0xA0–0xAB) |
| Game code | `AOME` |
| Maker code | `A4` (Konami) |
| Software version | 0x00 |
| Fixed byte 0xB2 | 0x96 |
| Complement check 0xBD | **0xFB = valid** (recomputed 0xFB) |
| Header checksum 0xBE | 0x0000 (standard computation 0xF9FB) — header was rebuilt |
| Entry word 0x00 | `0xEA3F8BFE` = `b 0x08FE3000` — **patched**, not the stock `0xEA00002E` |
| Nintendo logo | exactly one copy, at 0x04 |
| MD5 | `8286fe852aeaaca5837bd130acc1dbbe` |
| SHA-1 | `1f263f851f7abc83f27cbe6ac95a9b7540040255` |
| SHA-256 | `6d9a346d5c969ee50aa485cf86d1a097a636ec8e3ac1a9aab3ac7e0f3048ab0c` |

**The image is a scene release with a VENOM cracktro** (observed, screenshot
`shot_00.png`): “VENOM PRESENTS ON 1/26/2003 / DISNEY SPORTS MOTOCROSS (C)
KONAMI”, “GREETINGS TO OUR FRIENDS IN CRIME”, “INTRO CREDITS: CODE ZAEIFELD,
GRAPHICS MR SNOWMAN, CHIPTUNE MOTH”. The patched entry branches to an ARM
loader at `0x08FE3000` which decompresses `0x6400` bytes from `0x08FE33F4` to
`0x02000000`, sets DISPCNT/BG0CNT and `bx` to `0x020000C0`
(`0x08FE3018`–`0x08FE3044`). The intro runs there; when it finishes, control
returns to the cartridge image and the game boots normally through the **stock**
ARM crt0 at `0x080000C0` (verified: the crt0 code at 0xC0 is intact and the game
reaches the Disney Interactive logo, title and menus). There is no trainer menu
or patched game code — the patch is a boot-time wrapper only. Analysis and all
addresses below are of the stock game image at `0x08000000`.

Save memory: 512-byte EEPROM (mGBA created a 512-byte `.sav`; the image opens
`00 62 78 74 4d 73 6e 44` = `\0` + `DnsMtxb` reversed — the save record magic
is `DnsMtxb` at `0x02001740`).

## 2. Executive summary

**There is no password, no button cheat code, and no developer debug menu in
this ROM.** The game has **zero text-entry surfaces**: the whole menu tree was
walked (21 screens) and the only text on screen is drawn from font-tile codes.
No screen accepts typed characters, so there is no validator to reverse and no
code space to enumerate. This is a bounded negative: the search space is
defined and tested in §6b.

What the ROM *does* contain is a complete, developer-intended **hidden options
gate** and an **item unlock system**:

1. **Two hidden Options rows.** On a fresh save the Options page shows
   `BGM`, `Reset save data?`, `? ? ?`, `? ? ?`, `EXIT`. Two save bits — u16
   bit0 at **`0x020017A8`** and **`0x020017AA`** — replace the two `? ? ?` rows
   with **`Credits?`** (NO/YES; YES plays the full staff roll) and
   **`Sound Test`** (a 1–12 track selector). The two bits are **aliases**: the
   Options initialiser at `0x08022FA0` shows the rows if *either* bit is set
   (`0x08022FB2`/`0x08022FBC`, both tested separately). The published
   CodeBreaker code only names `0x020017A8`; `0x020017AA` and the row labels
   are not in any published list.
2. **A 47-item unlock array.** `0x02001748` holds 47 u16 “owned” flags
   (ids 0–46; `cmp r1,#46` at `0x08025678`). Item 0 is the default `No Item`;
   the rest are bike parts (engines, turbo chambers, outfits/riders). The
   Item List screen draws 16 cells per page (5+5+5+1 ring) with a `1/4` page
   label; item names/stats appear in the info panel (e.g. `Rocket Engine II`).
3. **Gates are progress bits, not codes.** Exhaustive Thumb BL scans over the
   whole image find exactly two callers for each option-bit setter and they are
   the **ending/staff-roll path**: the ending scene script `0x08113924` is
   compared at `0x080212A4`, its event routine `0x08020D88` unlocks all 47 items
   (event index 0) and sets the three option bits (event index 1, calls at
   `0x08020E26`–`0x08020E2E`), and the credits state machine `0x080178D0` sets
   them again at `0x0801794E`/`0x08017992`/`0x08017A0A`. No input handler
   references those setters (no function pointers to them exist either).
4. **No KCEK `AGB SYSTEM` debug framework.** Unlike sibling *Disney Sports
   Basketball* (which carries `AGB SYSTEM Ver3.00`, `L+R+START SOFT RESET`,
   `L+R+SELECT MEM+DMA DEBUG`, a debug page table and mode warps), this image
   contains none of those strings in any encoding and both documented combos
   are inert here (**observed**: title and Options, held 0.5 s). Its only
   “framework” strings are the Nintendo EEPROM library marker `EEPROM_V122`
   (`0x11AA70`) and a font table.

## 3. How to reproduce

Emulator: mGBA 0.10 (`mgba -3`), Xvfb `:313` + openbox, `SDL_AUDIODRIVER=dummy`.
Keys (mGBA SDL default): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
Select=`BackSpace`, D-pad arrows. Hold 150–350 ms; this game drops very short
taps (60 ms taps moved the cursor only ~1 in 3).

```
Xvfb :313 -screen 0 1280x1024x24 &
DISPLAY=:313 openbox &
DISPLAY=:313 SDL_AUDIODRIVER=dummy mgba -3 "Disney Sports Motocross.gba" &
```

| Screen | Exact path |
|---|---|
| VENOM intro | boot; press Start (Return) repeatedly to page through it |
| Title | after the intro: `Press START` |
| Main menu | Start → ring of 5: Single Player, MultiPlayer, Items, Records, Options (B here returns to title) |
| Single Player | Main → Single Player: Challenge Cup, Score Attack, Time Attack, Exhibition, Minigame, Tutorial (6) |
| Records | Main → Records: Challenge Cup, Score Attack, Time Attack rankings (3) |
| Items | Main → Items: Gift Item, Item List (2) |
| Options | Main → Options: BGM (ON/OFF), Reset save data? (NO/YES), `? ? ?`, `? ? ?`, EXIT |
| Team Select | any race mode → Select a team (5-team ring) |
| Item Select | team → Select an item (16-cell grid, `ItemList 1/4`) |
| Stage Select | item → Select a stage (7-course ring) |
| Race / pause | stage → race; Start → Continue / Retry / Back |
| Tutorial | Single Player → Tutorial: 12 lessons |
| MultiPlayer | Main → MultiPlayer → `Checking data on connected Game Boy Advance` (link-gated) |

Savestates: `Shift+F1`…`Shift+F9` save, `F1`…`F9` load. `.ssN` files are PNGs
with a zlib `gbAs` chunk (397,312 bytes; EWRAM at raw `0x21000`, IWRAM at
`0x19000`). Flag/row experiments below were made by editing the uncompressed
state and rebuilding the PNG CRC (tool `state_edit.py`), and are labelled as
debugger evidence, not as user-reachable cheats.

## 4. Address map

`ROM address = 0x08000000 + file offset`.

| Address | Contents |
|---|---|
| `0x08000000`–`0x080000FF` | GBA header, patched entry, stock ARM crt0 from 0xC0 |
| `0x08FE3000`–`0x08FE33F4` | VENOM intro loader (decompressor, EWRAM dest 0x02000000) |
| `0x08FE33F4`+ | compressed VENOM intro payload (0x6400 bytes decompressed) |
| `0x08002860` | pad read: `r2 = 0x3FF ^ [0x04000130]`; `[0x030004F6]=r2 & ~prev`, `[0x030004F4]=r2` |
| `0x08002878` | literal pool entry `0x04000130` (file 0x2878) |
| `0x0802BFAC` | glyph converter `(mode 0–4, index)` → font code, table `0x0811A9BC` + bit table `0x0802C050`; no direct caller (reached through a pointer table at `0x0802B930`), usage screen not located |
| `0x0811A920` | font code table (00–0B,10–1B,…,A0–AB) |
| `0x0811AA70` | `EEPROM_V122` |
| `0x08022FA0` | Options screen init (sets object fields, tests the two option bits) |
| `0x02001628` | Options menu object (u16 fields; [0]=0x081143D8 resource) |
| `0x08021xxx` | generic menu/list widget handlers (cursor wrap at `0x080228B8`/`0x080228A4`) |
| `0x02001740` | save record base in EWRAM, 8-byte magic `DnsMtxb` |
| `0x02001748`–`0x020017A5` | 47 × u16 item-owned flags (bit0), ids 0–46 |
| `0x020017A6` | option bit A (u16 bit0) — getter `0x08024DEC`, setter `0x08024DFC`; **getter has no caller** (dead flag) |
| `0x020017A8` | option bit B (u16 bit0) — getter `0x08024E10`, setter `0x08024E20` |
| `0x020017AA` | option bit C (u16 bit0) — getter `0x08024E34`, setter `0x08024E44` |
| `0x020017AC`+ | record/score tables (Challenge Cup entry 1 score 7000 = 0x1B58 at +0x0A) |
| `0x08024DE4` | `item_array_base()` → returns `0x02001748` |
| `0x08023B50` | `item_owned(id)` = bit0 of u16 at `0x02001748 + 2*id` |
| `0x08023B70` | `item_unlock(id)` = set bit0 |
| `0x08024220` | save (de)serialiser: reaches +8 (items), +0x66/+0x68/+0x6A (bits), +0x6C, +0x6E, +0x74 tables |
| `0x0802568E` | race-result award loop: for each id in a result list, if `id <= 46` and not owned → `item_unlock(id)` |
| `0x080174F4` | single-item award after a race |
| `0x08113924` | ending scene script pointer |
| `0x080212A4` | compares scene pointer with `0x08113924`; on match calls `0x08020D88` |
| `0x08020D88` | ending event routine, dispatches on an event index: index 0 unlocks items 0–46 (loop at `0x08020E0C`), index 1 sets bits A/B/C (`0x08020E26`–`0x2E`) |
| `0x080178D0` | credits/staff-roll state machine (8-state jump table at `0x080178F4`); calls set bits at `0x0801794E`, `0x08017992`, `0x08017A0A` |

## 5. Algorithm

### 5.1 No validator

There is no code entry: no keyboard screen, no character buffer, no
`strcmp`/`memcmp` against user text. Menu handlers compare small ids
(`cmp r0,#0..#11`) and single pad bits only (§6b.4). The only “text” input-like
device is the glyph converter at `0x0802BFAC`, whose screen is not in the walked
tree (see §8).

### 5.2 Pad model

```
held  = (~KEYINPUT) & 0x3FF           // 0x030004F4, active-high
new   = held & ~previous              // 0x030004F6
```

Masks: A=1 B=2 Select=4 Start=8 Right=0x10 Left=0x20 Up=0x40 Down=0x80 R=0x100
L=0x200. Cursor handlers use `new` for A/B and `held` for d-pad repeat.

### 5.3 Options gate (precise)

```
options_init():                       // 0x08022FA0
  obj = 0x02001628
  u16[obj+0x10] = 16; u16[obj+0x12] = 4; u16[obj+0x14] = 4; u16[obj+0x16] = 0
  if (!bit(0x020017A8) && !bit(0x020017AA)) {
      u16[obj+0x0A] = 0xFFFF          // 0x08022FC6: list start sentinel
      u16[obj+0x0C] = 0xFFFF          // 0x08022FCA: -1
  }
```

With the sentinel in place the two rows still render (`? ? ?`) but A and Right
do nothing (observed). With either bit set the rows render `Credits?` and
`Sound Test` (observed for `+0x68` alone and `+0x6A` alone).

### 5.4 Items

```
owned(id)  = u16[0x02001748 + 2*id] & 1     (0 <= id <= 46)
unlock(id) = u16[0x02001748 + 2*id] |= 1
```

Award path: race result → list of ids → for each, if `id <= 46` and not owned,
`unlock(id)` (`0x0802566E`–`0x08025692`). Ending path: loop 0..46 and
`unlock(id)`, then set bits A/B/C.

### 5.5 Ending / credits

Entering the ending scene (`0x08113924`) triggers `0x08020D88`. The staff roll
is also playable from `Options → Credits? = YES → A` once the gate bit is set;
observed roll: “Sound Programmer / Takashi Ono”, “Music / Yasumasa Kitagawa”,
“Effects / Yasumasa Kitagawa”, “Product Department / Kohei Nuramatsu”, “GUI
Designer / Masanori Nishishita”, “SFX Designers / Masaki Fujita, Satoshi Sakata,
Jun Kominami”, “Modelers”, “Director-Marketing Communications / Cherrie
McKinnon”, “Product Marketing Manager / Erica Mason”, “Producer / Munehisa
Komami”, “Senior Creative Services Manager”, “Rick Naylor” (order as scrolled).
It returns to the Options page.

## 6. Tables

### 6.1 Screens walked (21)

| Screen | Entries |
|---|---|
| VENOM intro | 3 observed pages (presents, greetings, intro credits) |
| Title | `Press START`, ©2003 Disney / Licensed by Nintendo |
| Main menu | Single Player, MultiPlayer, Items, Records, Options |
| Single Player | Challenge Cup, Score Attack, Time Attack, Exhibition, Minigame, Tutorial |
| Records | Challenge Cup, Score Attack, Time Attack |
| Challenge Cup ranking | 5 rows, default names `DSN`, scores 7000/6500/6000/5500/5000, heads Mickey/Minnie/Donald/Goofy/Pete, `Beginner Level` |
| Items | Gift Item (“Connect to another GBA and copy items.”), Item List |
| Item List / Item Select | 16-cell ring (5+5+5+1), `ITEMLIST 1/4`, stat panel SPD/ACC/TRB/BAL/JMP, ENG/FRE/GER/SPA/ITA/JPN tags |
| Options | BGM, Reset save data?, `? ? ?`, `? ? ?`, EXIT → (unlocked) Credits?, Sound Test |
| Reset dialog | “Save data reset / This will erase all saved data. Are you sure?” NO/YES |
| Team Select | 5 teams: SUPERSTARS/Mickey, CHARMERS/Minnie, BELLES/Daisy, SPACENUTS/Goofy, STEAMROLLERS/Pete |
| Stage Select | 7 courses: D.S.N. Stadium, Hillsbank Palsades, Charmers Castle, S.S. Cantankerous, Dreamland Funpark, Moon of Iota, Pete’s Pleasure Ville |
| Race HUD | 5 laps (`FINAL LAP` banner), Turbo (B), Trick (R), score |
| Pause | Continue, Retry, Back |
| Tutorial | 12 lessons (Lesson 1: “Cross the goal line within the time limit!”) |
| MultiPlayer | `Checking data on connected Game Boy Advance` (link only) |
| Credits | staff roll (above) |
| Sound Test | value 1–12 |
| Intro logos | Disney Interactive, Disney Sports Motocross title |

Note: the Cup blurb says “all six stages” but Stage Select is a 7-course ring
(wrap after 7 Rights); which six the Cup uses was not exercised (Exhibition was
used to reach the race).

### 6.2 Save flag map

| Offset | Meaning | Evidence |
|---|---|---|
| `+0x08` (0x1748) | 47 item-owned u16 flags, bit0 | fresh save = `[1,0,…]`; setting all 47 fills the Item List |
| `+0x66` (0x17A6) | option bit A, dead (no getter caller) | getter `0x08024DEC` BL-scan = 0 callers |
| `+0x68` (0x17A8) | option bit B (extra options) | getter `0x08024E10` → Options init |
| `+0x6A` (0x17AA) | option bit C (extra options alias) | getter `0x08024E34` → Options init |

**Published-list discrepancy (derived):** CodeBreaker `Unlock All Items`
(`42001748 0001 0000002F 0002`) writes 0x30 = 48 u16 starting at 0x1748, i.e.
`0x1748`…`0x17A6`. Only ids 0–46 are items; the 48th word overwrites option bit
A at `0x020017A6`. The item space is 47, not 48.

## 6b. Enumeration

### 6b.1 Space definition — there is no code space

| Space | Size / definition | Result |
|---|---|---|
| Password alphabets / lengths / checksums | 0 alphabets, 0 lengths, 0 checksum fields | no password system exists |
| Text-entry surfaces (keyboards, name entry) | 0 in the 21-screen tree | no user text buffer |
| Validators | 0 | nothing to reimplement |
| Menus | 21 distinct screens (table above) | all walked |
| Item unlock space | 47 ids (0–46) × 1 bit, base `0x02001748` | enumerated; all-47 test observed |
| Hidden option space | 3 bits at `0x17A6/A8/AA`, only B and C gating, aliases | enumerated by isolated patch |
| Sound Test | 12 values (1–12), wraps 12→1 | enumerated by wrap arithmetic |
| Button-mask sequences | 123 u16 runs ≥4; 2 clean tables | no multi-press validator |
| Key-read sites | 62 literal loads of `0x030004F0` | compare immediates all single-button ids |

Representable values: item state = 2^47; option bits = 2^3 with only two
distinct visible behaviours (hidden rows or not); **code state = 0**.

### 6b.2 Unpublished/undocumented entries found

1. **`Credits?` and `Sound Test` row labels** (not in any published list; the
   only published hint is the CodeBreaker aggregate “Unlock Extra Options”).
2. **The second gate bit `0x020017AA`** (published codes only use `0x020017A8`),
   and the fact that the two are OR-aliases.
3. **The dead third bit `0x020017A6`** (written by the ending and by the
   CodeBreaker “Unlock All Items” overshoot; its getter is never called).
4. **The credits/gate wiring**: ending script `0x08113924` → `0x08020D88` →
   47 item unlocks + 3 option bits, and the credits state machine
   `0x080178D0` repeating the setters.
5. **Item ids 0–46** (47 parts) vs the 48-word save write, and the 4-page /
   16-cell Item List layout.
6. **Default record table**: five `DSN` entries with 7000…5000 (developer
   placeholder, like sibling Basketball’s `KONAMI` rows).

### 6b.3 Bounds proven by rejection

| Test | Input | Result (observed) |
|---|---|---|
| Locked Options rows | A and Right on `? ? ?` on a fresh save | no label change, no screen (init sentinel) |
| Locked item cell | A on a `? ? ?` Item Select cell | nothing happens (selection not confirmed) |
| Out-of-range item id | `cmp r1,#46` at `0x08025678` (derived); ids >46 are skipped by the award loop | 47 = 0x2F cannot be awarded |
| Sound Test range | 40 Right presses from 1 land on 5 (`(1-1+40) mod 12 + 1`) | ring is exactly 12 |
| `L+R+START` (sibling soft reset) | held 0.5 s on title and Options | inert, no reset, flags unchanged |
| `L+R+SELECT` (sibling MEM+DMA debug) | held 0.6 s on title | inert |
| Start+Select, A+B+Select+Start, d-pad chord | title | inert; option bits still 0 afterwards |
| Konami sequence (held and edge forms) | literal u16 scan | not present in the image |
| All-items state | patch 47 flags, reload | Item List page 1 fills with 16 icons; info panel shows a real name (`Rocket Engine II`) |

### 6b.4 Negative results, bounded

* **Strings.** `strings -n 4` = 138,362 lines. Literal search for `password`,
  `passwd`, `cheat`, `debug`, `secret`, `unlock`, `hidden`, `menu`,
  `sound test`, `credits`, `staff`, `config`, `option` in ASCII, upper,
  `+/-0x20`, UTF-16LE and UTF-16BE: **0 hits** each. The single `CODE` hit is
  inside a graphics run at `0x1F60CE` (`…CKEHCODEC=AB…`), not text. The game’s
  UI text is stored as font-tile codes, not ASCII, so this scan alone cannot
  enumerate menus — that is why the screen walk above is the primary evidence.
* **Text fields.** No keyboard/name-entry screen exists in the walked tree; the
  only text-like bank is the credits (tile-coded) and the fixed record initials
  `DSN`. A glyph converter exists at `0x0802BFAC` but its screen was not found
  (see §8).
* **Button codes.** Scanned every aligned u16 run of ≥4 masks drawn from
  {1,2,4,8,10,20,40,80,100,200}: 123 runs, of which only two are clean tables —
  `0x080329FC` (10 masks in d-pad/face/shoulder/start order, referenced by
  `0x08002A38`/`0x08002A94`; a button-icon order table) and `0x08032E40` (ascending bit
  order, unreferenced). No run is a multi-press code sequence, and no code
  compares the held word with a combined mask. The `L+R+START` byte match at
  `0x32A08` is the tail of the icon table, not a validator.
* **Key handlers.** 62 code sites load `0x030004F0`; their compare immediates
  are single ids (0,1,2,3,4,5,9,10,11, 0x10,0x20,0x40,0x80) — cursor/menu
  semantics, never a multi-button code.
* **Debug gates.** No `AGB SYSTEM`, `DEBUG MENU`, `PAGE`, `MEM+DMA`, `SOFT
  RESET` strings or tables; both sibling combos inert; no mode-warp launcher
  code (the sibling’s `stores mode to 0x0200D5C0+0x24A0` pattern is absent).

### 6b.5 Novel, unpublished values (the deliverable)

No code could be minted because no code system exists. The equivalent novel
artifact is the **undocumented gate state**, generated and observed in-game:

| Value | Effect observed |
|---|---|
| `0x020017A8 = 1` (patch) → Options | rows become `Credits? NO` and `Sound Test 1` |
| `0x020017AA = 1` alone | same two rows (alias proven) |
| `Credits? = YES` + A | full staff roll plays and returns |
| `Sound Test` + Right ×10 | 1→11; ×20 more → 7; ×10 more → 5 (12-value ring) |
| all 47 item flags = 1 | Item List 1/4 becomes a full 16-icon grid; name `Rocket Engine II` |

These mappings (labels, the second bit, the alias, the 12-track range, the
47-item space) appear in no published list; the only published value,
`0x020017A8`, is only an aggregate “Unlock Extra Options” memory code and is
used here as an address hint, not as a cheat.

## 7. Validation evidence

**Observed (emulator + savestate RAM reads):**
* VENOM intro, Disney logo, title, all 21 screens, 5-team ring, 7-course ring,
  pause menu, 12-lesson tutorial, 5-lap race with `FINAL LAP`, race returns to
  main menu (no initials screen appeared), records `DSN` defaults.
* Options page on a fresh save: two `? ? ?` rows, A/Right inert.
* Patched `0x020017A8` and (separately) `0x020017AA`: both rows show
  `Credits?` / `Sound Test`; Credits plays the staff roll; Sound Test is 1–12.
* Patching all 47 item flags fills the Item List and shows real item names.
* `L+R+START`, `L+R+SELECT`, Start+Select, A+B+Select+Start and d-pad chords on
  the title do nothing; `0x020017A6/A8/AA` read back 0 after that session.
* RAM: fresh save `0x02001748 = [1,0,0,…]`; `0x020017A6/A8/AA = 0`; after load
  the same; the `.sav` is 512 bytes starting `00 62 78 74 4d 73 6e 44`.

**Derived (disassembly):**
* Stock crt0 at `0x080000C0`; VENOM loader at `0x08FE3000` (entry 0xEA3F8BFE).
* Pad routine `0x08002860` and state `0x030004F4/6`.
* Options init/gate `0x08022FA0`; save accessors `0x08024DE4…0x08024E44`;
  item owned/unlock `0x08023B50`/`0x08023B70`; award loop `0x0802568E`.
* Endgame wiring `0x08113924 → 0x080212A4 → 0x08020D88`; credits state machine
  `0x080178D0` with setter calls at `0x0801794E/92/A0A`.
* BL scans: exactly 2 call sites for each option setter; no function pointers
  to any setter.
* 47-item bound (`cmp #46`) and 48-word CodeBreaker overshoot into `0x17A6`.

**Inferred:**
* The two option bits are “game cleared / credits watched” milestones set by the
  ending; the exact story condition that reaches `0x08113924` was not replayed
  (would require winning the six-stage Challenge Cup).
* `0x020017A6` is a stale third milestone bit (getter unreferenced).

## 8. Unknowns

* **Item List page switching.** Page label `1/4` is drawn; no input (L, R,
  Left, Right, Up, Down, Select, Start, A, B, with 60–350 ms holds) changed it,
  including with all 47 items owned. The label is likely a fixed template and
  the grid a 16-item ring, but page mechanics were not proven.
* **Glyph converter `0x0802BFAC`.** A 5-mode character mapper (table
  `0x0811A9BC`, selection table `0x0802C050`) exists and is reached only through
  a pointer table at `0x0802B930`; no screen in the walked tree uses it. It may
  back a record-break initials entry that never appeared because our 0-score
  race did not beat the 7000 default. Any such field would be a display name,
  not a validator.
* **Save encoding/checksum.** The 512-byte EEPROM image is obfuscated
  (`DnsMtxb` magic reversed with a leading 0x00 followed by scrambled bytes);
  the serializer at `0x08024220` was located but not reimplemented.
* **Which six of the seven courses the Challenge Cup uses**, and the story flag
  that starts the ending (only its script pointer `0x08113924` is known).
* **Menu text encoding.** UI strings are font-tile codes; the code↔glyph map
  was not fully decoded (only the converter and font table addresses are known).

## 9. Tooling

* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`
* Python 3 + Capstone 5.0.7 (BL/BLX scans, literal-pool scans, mask-run scan)
* `state_edit.py` — read/patch mGBA `.ssN` `gbAs` zlib chunk (EWRAM at raw
  `0x21000`, IWRAM at `0x19000`), rebuild PNG chunk CRCs
* `diff.py` — EWRAM/state diff for cursor/flag discovery
* `blx.py` — exhaustive Thumb BL target scan
* `k.py` / `combo.py` — xdotool key and simultaneous-combo helpers
* mGBA 0.10, Xvfb `:313`, openbox, ImageMagick `import`/`convert`
* ROM was never modified; all patches were applied to savestate copies.

## 10. Legal note

No ROM, graphics, music, or extracted text is redistributed. Only hashes,
addresses, table layouts, observed behaviour and the analyst’s own notes are
recorded here. The VENOM intro is described only as a distribution artifact and
is not endorsed or reproduced.
