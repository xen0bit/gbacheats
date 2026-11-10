# CIMA: The Enemy (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/CIMA: The Enemy/CIMA: The Enemy.gba` |
| Size | 8,388,608 bytes (8 MiB, 0x800000) |
| Header title | `CIMATHEENEMY` (0xA0, 12 bytes, space padded) |
| Game code | `BCME` (USA) |
| Maker code | `E9` (Natsume) |
| Version | 0x00 |
| Entry word | `0xEA00002E` → `0x080000C0` (stock ARM branch) |
| Nintendo logo | Valid at file 0x04 |
| Complement check | `0x43` (valid) |
| Header checksum | `0x0000`; computed `0xFA43` (header rebuilt/zeroed, see §2) |
| Save type | SRAM; mGBA writes an 8 KiB `.sav`; data magic `SAVECIMA` (stored word-reversed) |
| MD5 | `089d28b825c21c8d199cca94f0d9bed8` |
| SHA-1 | `af415d61bbe27b9f4632bf414c07c66a554f3635` |
| SHA-256 | `903ded544b7c187217b2669fe2d03b92587e9530b447e4f6b25284fbf1ac8dd9` |

The header checksum field is zero and the complement is valid, the classic
signature of a rebuilt header. The entry branch, Nintendo logo, title and game
code are intact, and the image boots and plays normally. The 156-byte Nintendo
logo was scanned across the whole file: it occurs once, at file offset 0x04,
so this is a single-header image (no embedded second GBA image or multi-game
shell). No cracktro, trainer, or appended payload was found. Treat it as a
rebuilt-header USA image, not a No-Intro-verified dump.

## 2. Executive summary

**There is no in-game password, cheat-code, button-code, or stage-select
system in this ROM.** The only text-entry surface is the protagonist *name*
field, which is a display name (default `Ark`) written verbatim into the save
and shown in the save/load slot. It is not a validator and not a password.

What *does* exist is developer leftover script data: an unused **boss/room test
menu** (`BOSS SKIP`, `BOSS CHEK`, `dummy`, `DRAGON`, `FAREI`, `FALKEN`, `SOMA`,
`ZENOX`, `ELVIA`, `PIKE`, `P01`–`P04`) embedded in the dialogue/script bank.
TCRF independently documents it as a test-menu leftover, says the text "can be
re-enabled in-game", and states that any remaining functionality is unknown.
No normal input path reaches it in this image.

No unlockable gallery, sound test, boss rush, or level/stage-select mode is
present in the string/menu space either (all such keywords return zero hits).

The GBA codes published for CIMA are all **CodeBreaker memory pokes** (jewel
counters, HP/ATK/DEF, room IDs). They are not in-game codes, are not stored in
the ROM, and are outside this engagement's scope. No GameShark/CodeBreaker
code was used.

## 3. How to reproduce

Emulator: mGBA 0.10.5 SDL (`/usr/games/mgba`), 3× scale, under
`Xvfb :219` + `openbox`, with `SDL_AUDIODRIVER=dummy`.

Keymap used (mGBA SDL defaults):

| GBA | Key |
|---|---|
| A | `x` |
| B | `z` |
| L | `a` |
| R | `s` |
| Start | `Return` |
| Select | `BackSpace` |
| D-pad | arrow keys |

Exact menu path:

1. Boot. The Neverland logo plays. Press **Start** during the logo to skip the
   intro and reach the `Push Start` title.
2. Press **Start** at `Push Start` → title menu: `NEW GAME`, `CONTINUE`.
3. `NEW GAME` → name entry (`Ark`, 64-symbol grid, `End`) → intro.
4. In the field, **Start** opens the four-way ring. Hold **Down** until the
   bottom icon is highlighted (the highlight is a thick white/gold border;
   the icon changes to a pink sword/shield glyph), then press **A** while
   still holding Down → system menu:
   `Save and Continue`, `Save and Quit`, `Go to Entrance`,
   `Go to Title Screen`, `Text Speed Norm./Fast`, and `Sound` (the `Sound`
   row is below the visible 160-line frame in this menu; see §8).
5. `Save and Continue` → `SAVE` slot screen: slot A and slot B (`EMPTY` when
   blank). **A** on an empty slot saves; **A** on a filled slot opens
   `Overwrite? Yes / No`; the game shows `Saving...`.
6. `Save and Quit` → same slot screen → save (`Overwrite? Yes`, `Saving...`).
   In our session the slot screen remained after the write; pressing **B**
   then returned through the Natsume publisher logo to the title (the
   save-and-quit path).
7. After a save, title `CONTINUE` is enabled → **A** opens the `LOAD` slot
   screen (same two slots, header `LOAD`).
8. On `Text Speed`, **A** toggles `Norm.` / `Fast`.

Trigger tests performed for a hidden/debug menu:

* Select at `Push Start`: no effect.
* `L+R+Start` at `Push Start`: same as Start (title menu).
* `L+R+Start` at the title menu: same as Start (selected Continue in our test).
* Konami sequence (`Up Up Down Down Left Right Left Right B A`) at the title
  menu: no hidden item; the final A selected Continue.
* Hold Select at power-on: normal intro, no debug menu.
* Hold `L+R+Select` at power-on: normal intro, no debug menu.
* Hold `L+R+Start` at power-on: skips to `Push Start`, no debug menu.
* Hold `L+R+Select+Start` at power-on: `Push Start`, no debug menu.
* `Select+Start` at `Push Start`: main menu (Start confirmed), no debug menu.
* `Select`, `L`, `R` in the field: no hidden menu (R is the crosshair/command
  button; L is menu/cancel-related only in menus).
* `L+Start` in the field was observed once to return through the publisher
  logo (soft reset/return-to-title path). It is not a cheat.

## 4. Address map

All addresses are GBA ROM addresses (`0x08000000 + file offset`) unless marked
EWRAM/IWRAM.

| Address | Meaning |
|---|---|
| `0x080000C0` | ARM entry (stock crt0) |
| `0x08000B98` | Joypad poll. Reads `0x04000130`, XORs `0x3FF`, stores held/prev/pressed/released. |
| `0x02018C30` | Key-state struct (EWRAM): `+0` held, `+2` previous, `+4` newly pressed, `+6` newly released, `+8` repeat, `+0xA` timer, `+0xC` delay, `+0xE` counter |
| `0x020211B0` | UI/game state struct; `+0x03` language index (0/1/2); `+0x25` system-menu cursor index |
| `0x08070FA0` | Get system-menu / save-screen string: `table[group][index]`, group 0 = EN, 1 = DE, 2 = save-screen |
| `0x08070FC0` | Get area name: `areaTable[lang][areaIndex]` |
| `0x08070FE0` | Get main-menu string: `mainTable[lang][index]` |
| `0x0818ED1C` | System-menu string-pointer table, English (indices 0–13, strings at `0x080DCE67`…) |
| `0x0818ED54` | System-menu string-pointer table, German |
| `0x0818ED8C` | Save/load screen string-pointer table (`SAVE A`, `SAVE B`, `RETURN ROOM`, `RETURN TITLE`, `MESSAGE`, `SOUND`, `SLOW/FAST`, `ON/OFF`, `SAVE`, `LOAD`; strings at `0x080DCF8E`…) |
| `0x0818EDC4` | 3 pointers to the system/save string tables |
| `0x0818EDD0` | English area-name table, 130 × u32 pointers |
| `0x0818EFD8` | German area-name table, 130 × u32 pointers |
| `0x0818F1E0` | Internal/debug area-name table, 130 × u32 pointers (`TRAIN`, `DUNG-A`…`DUNG-P`, `WORLD`) |
| `0x0818F3E8` | 3 pointers to the area-name tables |
| `0x0818F3F4` | Main-menu string table, English (`NEW GAME`, `CONTINUE`, `Language Selection`, `English`, `German`, `FRENCH`, …) |
| `0x0818F438` | Main-menu string table, German |
| `0x0818F47C` | Main-menu string table, French/stub (uppercase English placeholders) |
| `0x0818F4C0` | 3 pointers to the main-menu tables |
| `0x0CA3BA` | System-menu item-index array: `00 01 02 03 04 05 06 07 09 08 0D` |
| `0x08200000` | Dialogue/script bank; first 131 u32 are record offsets |
| `0x08204A0E` | Script record 3 (offset table entry 3); header includes record-relative offset `0x3AE5` |
| `0x082084F3` | Test-menu sub-script start in record 3 (`0x4A0E + 0x3AE5`) |
| `0x08208B90–0x08208DD0` | Test-menu text (`BOSS SKIP`, `DRAGON`, `P01` etc.) |
| `0x08208518` | `NEXT / INI ON / INI OFF` text |
| `0x082086D9` | `DUNG / BOSSbattle TEST` text |
| `0x080C2C84` | Save-module build string `CIMASAVEU v1.00` (file 0xC2C84) |
| `0x0E000000` | SRAM (save data; magic `SAVECIMA`) |

Key masks used by the poll routine (active-high after XOR):

| Button | Mask |
|---|---:|
| A | 1 |
| B | 2 |
| Select | 4 |
| Start | 8 |
| Right | 0x10 |
| Left | 0x20 |
| Up | 0x40 |
| Down | 0x80 |
| R | 0x100 |
| L | 0x200 |

## 5. Algorithm

### 5.1 Input

```
raw  = read16(0x04000130)        ; active-low
held = raw XOR 0x3FF             ; active-high
pressed  = held AND (held XOR prev)
released = prev AND (held XOR prev)
prev = held
```

The menu code consumes `pressed`; there is no held-key sequence matcher and no
sequence table. There is no validator that reads a text buffer.

### 5.2 System menu

The pause/system menu uses the 11-byte index array at `0x0CA3BA`. The visible
six rows are the first six bytes (0–5):

```
item[0] = Save and Continue
item[1] = Save and Quit
item[2] = Go to Entrance
item[3] = Go to Title Screen
item[4] = Text Speed      ; values 6 = Norm., 7 = Fast
item[5] = Sound           ; values 9 = OFF, 8 = ON
item[13] = confirmation text ("Are you sure?")
```

The cursor index lives at `0x020211B0 + 0x25`. The draw code at `0x08060488`
and the action handler around `0x08064E00`–`0x080651C8` implement the list.
`Save and Continue` / `Save and Quit` branch to the slot screen; `Text Speed`
cycles `Norm.`/`Fast`; `Sound` is the clipped sixth row.

### 5.3 Save format

SRAM save data is word-reversed on disk. After reversing each 4-byte word:

```
0x00  "SAVECIMA"   (magic; raw bytes "EVASAMIC")
0x08  ".00"
0x0C  "U v1"       (build "CIMASAVEU v1.00")
0x10  name         (3 bytes in our test: "Ark")
...
```

The name is stored as plain bytes and is rendered back into the save/load slot
(and presumably dialogue text); no comparison, accept/reject, or
checksum-on-name path was found.

### 5.4 Name entry

The name editor is a fixed grid:

```
A B C D E F G H I J K L M N O
P Q R S T U V W X Y Z
a b c d e f g h i j k l m n o
p q r s t u v w x y z
0 1 2 3 4 5 6 7 8 9 ! ?
```

That is 26 + 26 + 10 + 2 = **64 symbols**. Default name `Ark`; `End` and two
arrow controls sit in the left column. The field is display-only; the game
never asks for a password and never rejects a name.

## 6. Tables

### 6.1 Title / main menu

| Index | English |
|---:|---|
| 0 | `NEW GAME` |
| 1 | `CONTINUE` |
| 12 | `Language Selection` (unused) |
| 13 | `English` |
| 14 | `German` |
| 15 | `FRENCH` |

### 6.2 Save/load screen

| String | String address | Pointer-table slot |
|---|---|---|
| `SAVE A` | `0x080DCF8E` | `0x0818ED8C` |
| `SAVE B` | `0x080DCF95` | `0x0818ED90` |
| `RETURN ROOM` | `0x080DCF9C` | `0x0818ED94` |
| `RETURN TITLE` | `0x080DCFA8` | `0x0818ED98` |
| `MESSAGE` | `0x080DCFB5` | `0x0818ED9C` |
| `SOUND` | `0x080DCFBD` | `0x0818EDA0` |
| `SLOW` / `FAST` | `0x080DCFC3` / `0x080DCFC8` | `0x0818EDA4` / `0x0818EDA8` |
| `ON` / `OFF` | `0x080DCFCD` / `0x080DCFD0` | `0x0818EDAC` / `0x0818EDB0` |
| `SAVE` / `LOAD` | `0x080DCFD4` / `0x080DCFD9` | `0x0818EDB4` / `0x0818EDB8` |

Observed save-slot contents: portrait, name (`Ark`), play time
(`00:08:54`), location (`Blue Creek`), or `EMPTY`. The observed slot screen
uses the `SAVE`/`LOAD` header and `EMPTY`/`Overwrite?` text; the
`SAVE A`/`SAVE B`/`RETURN ROOM`/`RETURN TITLE` strings are present in the
module but were not displayed in our session (likely an alternate layout).

### 6.3 Test-menu leftover (unused)

The test menu is a sequence of two-option pages in script record 3, sub-script
`0x084F3` (record-relative `0x3AE5`). Verified strings (file offsets; both
English and unused-German copies exist):

| Page | Options | File offset |
|---:|---|---|
| 1 | `NEXT` / `BOSS SKIP` / `BOSS CHEK` / `dummy` | `0x208BB4`–`0x208BF8` |
| 2 | `NEXT` / `DRAGON` / `FAREI` | `0x208C10`–`0x208C45` |
| 3 | `NEXT` / `FALKEN` / `SOMA` | `0x208C48`–`0x208C7B` |
| 4 | `NEXT` / `ZENOX` / `ELVIA` | `0x208C80`–`0x208CAC` |
| 5 | `NEXT` / `PIKE` / `TEST` | `0x208CB0`–`0x208CDE` |
| 6 | `NEXT` / `B` / `C` | `0x208CE4`–`0x208D08` |
| 7 | `NEXT` / `E` / `F` | `0x208D0C`–`0x208D2C` |
| 8 | `NEXT` / `G` / `I` | `0x208D30`–`0x208D4C` |
| 9 | `NEXT` / `J` / `K` | `0x208D50`–`0x208D74` |
| 10 | `NEXT` / `P01` / `P02` | `0x208D78`–`0x208DA4` |
| 11 | `P03` / `P04` / `TEST` | `0x208DA8`–`0x208DCC` |

Earlier pages in the same chapter contain `NEXT / INI ON / INI OFF`
(`0x208518`) and `DUNG / BOSSbattle TEST` (`0x2086D9`).

TCRF independently documents the same block as "Test Menu Leftovers", says the
text "can be re-enabled in-game", and notes that any remaining functionality is
unknown.

### 6.4 Published GBA codes (context only, not in-game)

The GameFAQs/Neoseeker walkthroughs contain no password or button code; their
"secrets" are gameplay hints (hidden items and boss tips). The cheat-device
lists (Almar's Guides, 53lu, JeuxMangas, gbadamud) contain CodeBreaker codes,
e.g.:

```
00000000 0002     enable
100001DE 0007     enable
3201FF84 0063     Max Brown Jewels
3201FF85 0063     Max Blue Jewels
3201FF86 0063     Max Red Jewels
3201FF87 0063     Max White Jewels
32019851 0012     Ark J unlimited health
32019852 0063     Ark J max ATK
32019853 0063     Ark J max DEF
3201A811 0010     Ivy F unlimited health
...
82014230 ????     Character set in room modifier
82025A18 ????     Room modifier
```

All targets are EWRAM (`0x0201xxxx`); these are memory pokes, not strings or
in-game codes. The representative literals checked (`3201FF84`, `32019851`,
`100001DE`, `82025A18`, `3201A811`, `82014230`) have zero hits in the ROM.
They were not used for this analysis.

One published entry is internally inconsistent: "Ivy F Max DEF" is listed as
`32019813 0063`, which is not in Ivy's block (`0x0201A8xx`) and does not match
Ark's DEF either (`0x02019853`). Ivy's health and attack are
`0x0201A811`/`0x0201A812`, so the intended DEF address is almost certainly
`0x0201A813`. This is a list typo of the kind the guide warns about, not an
in-game code.

## 6b. Enumeration

### Space definition

| Potential surface | Size / result |
|---|---|
| Password / passcode / cheat / debug strings | **0 occurrences** of `password`, `passcode`, `cheat`, `debug`, `gallery`, `unlock`, `sound test`, `soundtest`, `level select`, `stage select` in 8 MiB (case-insensitive; also checked `+0x20` / lowercase and UTF-16LE/BE) |
| Text-entry field | 1: the name editor. Alphabet = **64 symbols** (A–Z, a–z, 0–9, `!`, `?`). Observed name length 3 (`Ark`); the maximum field length was not separately measured. For the observed 3 characters the space is `64^3 = 262,144`; display-only, no validator. |
| Button-code table | No sequence table found. 919 u16 runs of key-mask values (length ≥4) and 1,293 byte runs (length ≥6) were enumerated; the candidates inspected are coordinate/UI tables, not key sequences, and no table-driven sequence matcher was found in the input/menu code. |
| System menu | 6 rows defined; 5 visible, 6th (`Sound`) clipped in our captures; 2 save slots, overwrite Yes/No |
| Title menu | 2 items |
| Language screen | 3 options (`English`, `German`, `FRENCH`); unused/stubbed |
| Test menu | 11 pages listed in §6.3; unused script data |

### 6b.0 Screen walk ledger

| Screen | Status |
|---|---|
| Neverland / Natsume publisher logo | Observed |
| `Push Start` title | Observed |
| Title menu (`NEW GAME`, `CONTINUE`) | Observed; Continue greyed/empty before save, enabled after |
| Name entry | Observed (`Ark`, 64-symbol grid, `End`) |
| Field HUD + Start ring | Observed |
| Status/equipment screen | Observed |
| System/pause menu (6 rows) | Observed |
| Save slot screen (`SAVE`, A/B) | Observed |
| Overwrite confirmation | Observed |
| `Saving...` | Observed |
| Load slot screen (`LOAD`) | Observed |
| Game Over | Not reached; fail-state screen, no code surface (strings present) |
| Language Selection | Not reached; unused/stubbed per TCRF |
| Test menu | Not reached; unused script text |

### 6b.1 Literal search counts and classification

`strings -t x -n 4` produced **68,533** printable records. Keyword counts over
the whole 8 MiB (case-insensitive) and their classification:

| Needle | Count | Classification |
|---|---:|---|
| `password` | 0 | — |
| `passcode` | 0 | — |
| `cheat` | 0 | — |
| `debug` | 0 | — |
| `unlock` | 0 | — |
| `gallery` | 0 | — |
| `sound test` / `soundtest` | 0 / 0 | — |
| `level select` / `stage select` | 0 / 0 | — |
| `warp` | 0 | — |
| `secret` | 1 | dialogue at `0x262268` ("to know the secret too") — not a menu |
| `staff` | 1 | credits at `0xCBBEB` (`CIMA The Enemy STAFF`) |
| `code` | 1 | high-entropy/compressed bytes at `0x125E60` — not text |
| `music` | 2 | staff roles at `0xCB9EC` / `0xCBA24` — not a sound test |
| `test` | 50 | substring hits (e.g. "greatest"); the real test-menu block is `0x208B90–0x208DD0` |
| `BOSS SKIP` | 2 | test menu, English + unused-German duplicate |
| `BOSS CHEK` | 2 | test menu, English + unused-German duplicate |
| `dummy` | 4 | `dummy item` help at `0xDC9EC`/`0xDCCE2`; test menu at `0x208BD7`/`0x208BF5` |
| CodeBreaker literals (`3201FF84`, `32019851`, `100001DE`, `82025A18`, …) | 0 | codes are device pokes, never stored |

### Novel code

**None can be generated because no code space exists.** The name field is not
a code (it is stored and displayed, never compared); the test menu is not
reachable by normal input; the only published values are CodeBreaker memory
pokes, which are excluded by scope.

This is a bounded negative for the code space, not an untested claim:

* 68,533 `strings -n 4` records were scanned; the keyword set above returned
  zero password/cheat/debug hits.
* All menu surfaces reachable in normal play were opened and recorded
  (title, main, name entry, field ring, status/item, system/pause, save,
  overwrite, load).
* No hidden menu was opened by the standard triggers in §3.
* The one code-like text block in the ROM is the unused test menu, which TCRF
  also classifies as leftover/unreachable. Its entries are enumerated from the
  ROM (§6.3); their effects are not observable in normal play and are reported
  as unknown, not as an untested reachable screen.

### Bounds by rejection

| Input | Result |
|---|---|
| Select at `Push Start` | No change; no hidden item or screen |
| `L+R+Start` at `Push Start` | Same as Start; no debug menu |
| Konami sequence at title menu | No change; final A selected Continue |
| Select / `L+R+Select` at power-on | Normal intro; no debug menu |
| `L+R+Start` / `L+R+Select+Start` at power-on | `Push Start`; no debug menu |
| `Select+Start` at `Push Start` | Main menu; no debug menu |
| Down past `Text Speed` in system menu | Cursor clamps on `Text Speed`; no seventh item |
| Test-menu text | No normal trigger; no pointer/table entry resolves to it |
| Published CodeBreaker code | Identified as an EWRAM memory poke; literals verified absent from the ROM; not used because memory-edit codes are out of scope |

## 7. Validation evidence

### Observed

* Boot → Neverland logo → intro; Start at the logo reaches `Push Start`.
* Title menu contains exactly `NEW GAME` and `CONTINUE`; Continue is greyed
  until a save exists, then opens the `LOAD` screen.
* Name entry grid with 64 symbols and default `Ark`; `End` starts the game.
* Field ring: Start opens it; holding Down highlights the bottom icon; A opens
  the system menu. R opens the status/equipment screen.
* System menu rows and values as listed; `Text Speed` toggles `Norm.`/`Fast`
  with A.
* Save slot screen: `SAVE`, two slots, `EMPTY`/filled with `Ark`,
  `00:08:54`, `Blue Creek`; `Overwrite? Yes/No`; `Saving...`.
* Save-and-quit write, followed by B, exits through the Natsume publisher logo
  to the title.
* `.sav` contains word-reversed `SAVECIMA` and the name `Ark` at offset 0x10.
* No response to the standard hidden-menu triggers listed in §3.

### Derived

* The input module at `0x08000B98` stores held/pressed/released at
  `0x02018C30`; there is no sequence-table consumer.
* The system menu item list comes from `0x0CA3BA` and the string table
  `0x0818ED1C`.
* The third area-name table (`0x0818F1E0`) is the internal/debug table
  (`TRAIN`, `DUNG-A`…`DUNG-P`, `WORLD`), selected by language index 2; the
  French localization is stubbed, so a language-2 save/load screen would show
  these internal labels.
* The test-menu text is inline in script record 3 at sub-script `0x084F3`; no
  direct pointer/table entry references the individual strings.
* Published GBA codes are CodeBreaker EWRAM pokes; none is stored in the ROM.

### Inferred

* The header was rebuilt by a tool (checksum field zeroed, complement valid);
  the body is the retail USA image. The exact tool/patch is unknown.
* The test menu was a developer boss/room selector; its runtime behaviour
  cannot be observed without editing the script or a gate flag.

### External cross-check

TCRF's CIMA page (mirror `tcrf.tiago.zip/wiki/CIMA-3a_The_Enemy`) lists:
`CIMASAVEU v1.00`, the `Language Selection / English / German / FRENCH`
leftover, the E3-demo text, and the test-menu pages `BOSS SKIP`, `BOSS CHEK`,
`dummy`, `DRAGON`, `FAREI`, `FALKEN`, `SOMA`, `ZENOX`, `ELVIA`, `PIKE`,
`P01`–`P04`. Every test-menu literal listed above, plus `CIMASAVEU v1.00`,
was found at the addresses in §4/§6.3. TCRF says the test-menu text can be
re-enabled in-game and that its functionality is unknown; this matches our
failure to find a normal trigger.

## 8. Unknowns

* The test menu's actual runtime behaviour (unreachable without a patch or a
  gate-flag edit). The text and page structure are known; the effects are not.
* The sixth system-menu row (`Sound`) is below the visible 160-line frame in
  our captures; the cursor clamped on `Text Speed` when we pressed Down, so
  the Sound value was not read visually. Its strings/values are present in the
  table (`ON` = 8, `OFF` = 9). This is a UI clipping quirk, not a hidden menu.
* The `Language Selection` screen was not reached; TCRF reports it as unused,
  and the French text is stubbed. Its exact trigger (if any) is unknown.
* The save/load module also contains `MESSAGE`, `SOUND`, `SLOW/FAST`, `ON/OFF`
  strings (table `0x0818ED8C`). No page exposing those strings was reached
  from the `SAVE`/`LOAD` slot screens; they may be unused layout leftovers.
* The `Game Over` screen (graphic plus `Continue`/`New Game` strings, table
  `0x0818F3F4`) was not reached; it is a fail-state screen with no code/password
  surface. Its text is present but its exact transition was not exercised.
* The exact header-rebuild tool and the reason for the zeroed header checksum
  are unknown.
* The save checksum/format beyond the word-reversed magic and name offset was
  not reversed (not needed for the cheat question).

## 9. Tooling

* mGBA 0.10.5 SDL, Xvfb `:219`, openbox, `SDL_AUDIODRIVER=dummy`.
* `xdotool`, `scrot`, ImageMagick `convert` for input and screenshots.
* `strings -t x -n 4` (68,533 records), Python 3 byte scans and pointer scans.
* `arm-none-eabi-objdump` 2.44 (`-M force-thumb`) and Capstone 5.0.7 for
  disassembly.
* Static scripts: `phase0.py` (header/hash/logo scan), literal/pointer/u16
  run scans, save-file word-reversal dump.
* No GDB stub was needed; all dynamic checks were done through the emulator
  screen and the SRAM dump.

## 10. Legal note

No ROM, extracted graphics, music, or game text is redistributed here. The
report contains addresses, hashes, algorithm descriptions, and short
identifier strings needed to reproduce the analysis. The ROM and any generated
`.sav`/savestate files remain local and were removed after the session.
