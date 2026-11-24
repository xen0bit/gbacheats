# David Beckham Soccer (GBA) — Reverse Engineering Report

## 1. Target identity

| Item | Value |
|---|---|
| File | `roms/David Beckham Soccer/David Beckham Soccer.gba` |
| Size | 4,194,304 bytes (4 MiB) |
| Header title | `DAVID BECKHA` (12 bytes, `0xA0`) |
| Game code / maker / version | `ABQE` / `5G` / `00` |
| MD5 | `9af9f7652dfbd45d06b50a6925ee18f6` |
| SHA-1 | `98e58464f852958e0ccaf7250fe8fb8990b84b3c` |
| SHA-256 | `506a3b9d2f5ed6af8ee3150172b8b467fee34389c1ba6bbff0e81bbab5b9adb4` |
| Entry word | `0xEA00002E` (stock `b +0xB8` → `0x080000C0`) |
| Fixed byte `0xB2` / complement `0xBD` | `0x96` / `0x96` |
| Stored header checksum `0xBE` | `0x0000`; recomputed value `0x0096` |
| Save type | EEPROM 4 kbit (mGBA creates a 512-byte `.sav`; matches the 3rd party cheat index database entry "Eeprom v122 - 4 kbit") |

**Patch / trainer check.** The embedded GBA-header scan (Nintendo logo at `+4`) finds exactly one
header, at file offset 0. The entry branch is the stock one, the fixed byte and complement byte are
correct, and the first 4 KiB is the normal ARM crt0 (`0x08000000`–`0x080001C0`) followed by Thumb
code. No cracktro, no appended trainer and no second executable image. The only header anomaly is
that the 16-bit header checksum field is zero while the computed checksum is `0x0096`; with the
complement byte intact this is the well-known "rebuilt header" artifact, not evidence of code
patching.

## 2. Executive summary

**This GBA build has no reachable password entry, no button code, no unlock code and no hidden debug
menu.** The word "Password" *is* present in the ROM — in all five localised text tables, at runtime
text id **23** (table index 24) — but it is referenced by **no** screen descriptor, **no** menu entry
list and **no** UI element block. It is a localised string retained from the shared text database,
not a live feature.

The game is a Yoyo Entertainment / Rage soccer title that renders everything into a **mode-4
8bpp bitmap framebuffer** (`DISPCNT = 0x1444`, page selected by bit 4) and saves progress to
**4 kbit EEPROM**, so the password mechanism used by the PlayStation 2 / PC version of the same
license ("Continue Game → Password") was not carried into the GBA SKU. The GBA "New Game / Continue
Game" menu exists (descriptor `0x081BD394`, list ids 152/153) but contains no password entry.

The pause menu is `Game Paused → Continue / Quit` (Continue = text id 22, Quit = id 148). The Options
screen is `Fouls: On/Off`, `Throw ins: On/Off`, `Game Time: 5/10/15/20/2 Mins`. No
Hex keyboard, no code field, no "enter password" prompt exists in the UI resource set.

The single published GBA "cheat" found (3rd party cheat indexes: *win five games in a row to unlock World Cup
mode*) is not an input code; the ROM contains no World Cup mode label in any menu list, so the claim
could not be tied to any UI in this image and is recorded as unverified.

## 3. How to reproduce

Emulator: mGBA 0.10 SDL, `-3`, `SDL_AUDIODRIVER=dummy`, on `Xvfb :282` with openbox.
Keymap used: `x`=A, `z`=B, `Return`=Start, `BackSpace`=Select, arrow keys = D-pad.
Hold keys for 250–350 ms; the game debounces and ignores taps shorter than ~100 ms.

Boot path (observed):

1. Nintendo logo → **language select** (text ids 124 = English, 127 = Español). `A` selects.
2. Attract/title screen; `Start` enters the **Main Menu**.
3. Main Menu items (observed): Friendly Mode, Competition Mode, Season Mode, Train With Beckham,
   Options, The David Beckham Story.
4. Friendly Mode → Friendly - Game Type (International / Club) → team list → `A` selects two teams →
   `Play / 2 Teams Selected` → match.
5. Competition Mode → League - Select Type (Knockout / Euro League) → Knockout - Teams
   (8/16/32/64 Teams) → team list (Albania, Argentina, Australia, Austria, …) → Play.
6. Season Mode → Season - Select Type (country list: English … Dutch) → Season Mode - Select Teams
   (Manchester R, Highbury, Liverpool, Leeds, Ipswich, Chelsea, …) → Play.
7. Train With Beckham → Practice - Select Type (Free Kicks, Penalties, Passing, Tackling, Corners).
8. Options → Fouls: On/Off, Throw ins: On/Off, Game Time: 5/10/15/20 Mins.
9. The David Beckham Story → Introduction, The Early Years, Manchester United, Away From The Game,
   Career History, Questions And Answers.
10. In a match, `Start` → **Game Paused** with Continue / Quit.

Because the display is a bitmap, screen text was read from RAM, not from screenshots: mGBA `.ss1`
savestates were parsed (PNG `gbAs` chunk → zlib → 397,312-byte state; VRAM at `0x1000`, IWRAM at
`0x19000`, EWRAM at `0x21000`), the active page taken from `DISPCNT` bit 4, and glyphs matched
against the ROM font at `0x081AA624` (see §9). Examples of decoded lines used as evidence:
`MainMenu`, `FriendlyMode`, `SeasonMode`, `Options`, `Fouls:On`, `Throwins:On`, `GameTime:5Mins`,
`GamePaused`, `Continue`, `Quit`, `Knockout-Teams`, `8Teams`, `64Teams`.

**Codes tested: none exist for this SKU.** No GBA password list was found (see §7), so there is no
literal to enter. The PS2/PC literal lists do not apply to this ROM (different engine and SKU).

## 4. Address map

| Address | Size | Meaning |
|---|---|---|
| `0x080000C0` | — | ARM crt0 entry |
| `0x08000888` | func | joypad reader: `held`, `pressed`, repeat |
| `0x0800C140` | func | char → glyph-index mapping (jump table at `0x0800C158`) |
| `0x0800C4F4` | func | string width in pixels |
| `0x0800C538` | func | draw string at (x,y) into 8bpp framebuffer |
| `0x0800C624` | func | **text id → string pointer resolver** |
| `0x0800C69C` | func | draw string with alignment flags |
| `0x0800C0E4` | func | screen transition/fade manager |
| `0x080102DC` | func | begin screen (stores descriptor) |
| `0x081AA624` | 8192 B | 8×8 font, 128 glyphs, 64 bytes each, ink `0xFE`, shadow `0xFD` |
| `0x081AA5A4` | 128 B | per-glyph advance widths |
| `0x081AF658` | 5×u32 | language → text-table pointer array |
| `0x081AC620` | table | English text table (index 0 → "Main Menu") |
| `0x081AE294` | table | Spanish text table |
| `0x081ACEC8` | table | French text table |
| `0x081AD888` | table | German text table |
| `0x081AEC78` | table | Italian text table |
| `0x081AC684` | u32 | **English "Password" string pointer slot (text id 23)** |
| `0x08018518` | str | `"Password"` |
| `0x0801B650` | str | `"Mot de passe"` |
| `0x0801EA9C` | str | `"Passwort"` |
| `0x08021E3C` | str | `"Contraseña"` |
| `0x08018368` | str | `"0123456789ABCDEF"` (numeric formatter alphabet) |
| `0x0800B1E4` | func | integer→string with base (base 16 uses `0x08018368`) |
| `0x02000000` | u16 | held keys (active high, `~KEYINPUT & 0xFFFF`) |
| `0x02000002` | u16 | newly pressed keys |
| `0x02000004` | u16 | effective keys (edge + 30-frame repeat) |
| `0x02002C05` | u8 | transition state: 0 idle, 1 fade-out, 2 fade-in, 3 active |
| `0x02002C0A` | u8 | language index (0 = English) |
| `0x02004304` | u32 | pointer to current screen descriptor |
| `0x06000000` | 240×160 | mode-4 8bpp framebuffer (page 0; page 1 at +0xA000) |

Screen descriptors (43 distinct, all referenced by literal pools in `0x08011800`–`0x08012A00`):
`0x081B401C`, `43E4`, `47AC`, `4B74`, `4F3C` (main menu), `5304`, `56CC`, `5A94`, `5E5C`,
`6224`, `65EC` (options), `69B4`, `6D7C`, `7144`, `750C`, `78D4`, `7C9C`, `8064`, `842C`, `87F4`,
`8BBC`, `8F84`, `934C`, `9714`, `9ADC`, `9EA4`, `A26C`, `A634`, `A9FC`, `ADC4`, `B18C`, `B554`,
`B91C`, `BCE4`, `BC0AC`, `BC474`, `BC83C`, `BCC04`, `BCFCC` (pause), `BD394` (New Game/Continue),
`BD75C`, `BD980`, `BDDBC`.

## 5. Algorithm

### 5.1 Text id → string

```
resolve(id):                                  # 0x0800C624
    lang = *(u8*)0x02002C0A
    base = *(u32*)(0x081AF658 + 4*lang)       # 0x081AC624 for English
    return *(u32*)(base + 4*id)               # base points at table[1]
```

Therefore runtime **id n selects table entry n+1**. The main menu list `{1,2,3,4,5,54}` maps to
Friendly Mode, Competition Mode, Season Mode, Train With Beckham, Options, The David Beckham Story —
matching the observed screen. "Password" is table entry 24, so its runtime id is **23**.

### 5.2 Screen state machine

* `0x02004304` holds the active descriptor pointer (ROM).
* `0x080102DC(descriptor)` stores it, resets `0x0200430C`, sets brightness and transition state 1.
* `0x0800C0E4` fades 15→0 (state 1), then 0→15 (state 2), then sets state 0 and
  `0x0200430C = 1`; the caller then loads the next screen.
* Descriptors contain an 8-byte element marker `00 FF FF FF FF 00 00 00`, then typed element
  records (menu item type `0x06` carries a `u16` text id at `+0x10` and a Thumb handler pointer at
  `+0x18`). 131 such markers exist in `0x081B4F6C`–`0x081BDDBC`.

### 5.3 Why the hex alphabet exists

`"0123456789ABCDEF"` (`0x08018368`) is referenced exactly once, from the literal pool at
`0x0800B244`, by the base-N integer formatter at `0x0800B1E4` (called by the printf-like formatter
at `0x0800B250`). It is a **numeric display alphabet**, not an input keyboard: there is no second
reference, no key cursor, and no 16-slot selector in any descriptor.

## 6. Tables

### 6.1 Localised "Password" label

| Language | Table base | Entry 24 | String |
|---|---|---|---|
| English | `0x081AC620` | `0x08018518` | `Password` |
| Spanish | `0x081AE294` | `0x08021E3C` | `Contraseña` |
| French | `0x081ACEC8` | `0x0801B650` | `Mot de passe` |
| German | `0x081AD888` | `0x0801EA9C` | `Passwort` |
| Italian | `0x081AEC78` | `0x08018518` | `Password` (untranslated) |

### 6.2 Menu entry lists (u16, `0xFFFF` terminated)

| Offset | Ids | Labels |
|---|---|---|
| `0x081B3E9C` | 1,2,3,4,5,54 | Friendly / Competition / Season / Train / Options / Story |
| `0x081B3EAA` | 62,61 | International / Club |
| `0x081B3EB0` | 11,12,13,14 | 8 / 16 / 32 / 64 Teams |
| `0x081B3EBA` | 139,80 | Knockout / Euro League |
| `0x081B3EC0` | 55–59 | Free Kicks / Penalties / Passing / Tackling / Corners |
| `0x081B3ECC` | 8,9 | Single Player / Link Up |
| `0x081B3ED2` | 64–71 | English … Dutch |
| `0x081B3EE4` | 34–39 | 4-4-2 … 4-5-1 |
| `0x081B3EF2` | 43–53 | 1 … 11 (shirt numbers) |
| `0x081B3FF0` | 116–121 | Story chapters |
| `0x081B3FFC` | 124,127 | English / Español |
| `0x081B4006` | 150,151 | No / Yes |
| `0x081B4016` | 152,153 | New Game / Continue Game |

**No list contains id 23.**

### 6.3 Pause and options

* Pause descriptor `0x081BCFCC`: element `0x06` id 22 = `Continue`; element `0x06` id 148 = `Quit`;
  `Really Quit?` conformation ids 150/151 (`No`/`Yes`).
* Options descriptor `0x081B65EC`: `Fouls:` (id 129) On/Off (133/132), `Throw ins:` On/Off,
  `Game Time:` 2/5/10/15/20 Mins (ids 155,134–137).

## 6b. Enumeration

This engagement's target system is absent, so the deliverable is a **bounded negative** with the
full search space and counts, plus the reason the space is closed.

### 6b.1 Space definition (text/code-label surface)

* Text tables: 5 localised pointer tables, each with the same ~180-entry id space; entry 24 (runtime
  id 23) is the Password label in all five.
* Screen descriptors: **43** distinct descriptors, all reachable from the literal pools of the 31
  screen-entry functions at `0x08011800`–`0x08012A00`.
* UI element blocks: **131** `00 FF FF FF FF 00 00 00` records in the descriptor window, covering
  every element of every descriptor.
* Menu/option lists: **19** u16 lists in the label block `0x081B3E94`–`0x081B4016` (11 of them
  referenced by screen descriptors, §6.2), **160** entries in total.
* Result: **0 / 131 element blocks** and **0 / 19 lists** reference id 23; a `u16 == 0x0017` scan of
  the whole descriptor window `0x081B4000`–`0x081BE000` returns 6 hits, all inside the non-UI score
  table at `0x081BD980`; a scan of every `u16 == 23` followed within 20 bytes by a Thumb code
  pointer returns 0 hits.

### 6b.2 Space definition (button-code surface)

* Key masks: `1,2,4,8,0x10,0x20,0x40,0x80,0x100,0x200`.
* Scan of the full 4 MiB for runs of ≥4 consecutive mask values: **680** candidate runs, of which
  only **2** lie in executable code (`0x8CA`, `0x8CC`) and both are a literal pool
  (`0x02000008`/`0x02000004` misread as masks 8/4). **0 key-mask tables, 0 sequences.**
* Input semantics are edge-triggered with a 30-frame repeat (`0x08000888`), so a possible code would
  have to be visible as a mask table; none exists.

### 6b.3 Space definition (input-alphabet surface)

* Hex alphabets in the image: exactly **1** (`0x08018368`, 16 symbols).
* References: exactly **1** (`0x0800B244`), consumed by the base-16 formatter. No keyboard, no
  selected-symbol cursor, no 16-cell selector in any descriptor, no ASCII→nibble parser
  (`subs #0x30` occurs 14 times in the image; the single code-region hit at `0x130D4` is an address
  subtraction in an unrelated routine, not a character conversion).

### 6b.4 Novel codes

No code can be minted because no validator, table or input field exists. The enumera­tion result is
therefore the **empty set**: 0 accepted codes, 0 published codes, 0 novel codes. The corresponding
"bounds by rejection" is the closed-space proof above: every representable label id in every screen
was checked (131/131 blocks, 19/19 lists), and id 23 occurs in none.

### 6b.5 Published codes checked

* 3rd party cheat indexes GBA cheats page: HTTP 403; Wayback availability API returns no snapshot for
  3rd party cheat indexes.
* 3rd party cheat indexes GBA page: one entry, "Win five games in a row to unlock World Cup mode" — a
  gameplay condition, not an input code.
* 3rd party cheat indexes: no article for this GBA title; the only search hit is the unrelated *Go! Go! Beckham!*
  GBC/other title.
* 3rd party cheat indexes: 403.
* Verified literals: no published GBA password exists, so there is no literal to search. The
  PS2/PC "Continue Game → Password" lists are for a different SKU (same license, different engine)
  and were not applied.

## 7. Validation evidence

**Observed (RAM/emulator):**
* Boot language screen decoded as `English` / `Español` (font-match OCR of the framebuffer at
  `0x06000000`).
* Main menu decoded as `MainMenu`, `FriendlyMode`, `CompetitionMode`, `SeasonMode`,
  `TrainWithBeckham`, `Options`, `TheDavidBeckhamStory`.
* Options decoded as `Options`, `Fouls:On`, `Throwins:On`, `GameTime:5Mins`.
* In-match `Start` decoded as `GamePaused`, `Continue`, `Quit`.
* Season team list decoded as `SeasonMode-SelectTeams` with club names.
* Knockout screen decoded as `Knockout-Teams`, `8Teams`, `16Teams`, `32Teams`, `64Teams`.
* `0x02004304` tracked through the above transitions; descriptor and list contents read from ROM.

**Derived (static):**
* The text resolver at `0x0800C624` and the id→table mapping (base `0x081AC624`, id n → table n+1).
* The 43 descriptors, 131 element markers and 12 label lists; the zero-reference result for id 23.
* The hex alphabet's single consumer is the integer formatter (`0x0800B1E4`).
* The joypad reader and the absence of any key-mask table.
* The header/entry/complement analysis and the single embedded header.

**Inferred:**
* The Password label was inherited from the shared multi-platform text database and left unused
  because the GBA build saves to 4 kbit EEPROM (New Game / Continue Game) and therefore needs no
  password. This is consistent with all observations but is an inference about developer intent.
* The 3rd party cheat indexes World Cup unlock belongs to another platform/SKU; the GBA image contains
  "World Cup" only inside David Beckham's biography text, never as a menu label.

## 8. Unknowns

* No live screen was found for the `New Game / Continue Game` descriptor (`0x081BD394`); it is
  present in the descriptor set with list ids 152/153 and no password element. Its entry gate
  (save presence) was not exercised because the save was blank; the menu resource itself contains
  no id-23 element, so a password item cannot be produced by it.
* The exact reason the localized Password label was kept in the shipped text bank (planned feature,
  shared database, or removed late) is not derivable from the image.
* Font blitting was modelled from the renderer's pixel writes (ink `0xFE`, shadow `0xFD`); glyphs
  with identical masks would be ambiguous, but every decoded menu line was cross-checked against
  the ROM text table.

## 9. Tooling

* mGBA 0.10 SDL (`-3`, `-d` for breakpoints/reads, savestates via `Shift+F1`), Xvfb `:282`, openbox,
  xdotool, `SDL_AUDIODRIVER=dummy`.
* `parse.py` / `show.py` — decode the `.ss1` `gbAs` zlib chunk (VRAM/IWRAM/EWRAM), read the current
  descriptor at `0x02004304`, its element list and text ids.
* `ocr2.py` — RAM screen reader: extracts the mode-4 framebuffer page, matches 8×8 cells against
  the ROM font at `0x081AA624` (ink `0xFE`, shadow `0xFD`), and prints text lines. No screenshots
  and no image files were used as evidence.
* Ad-hoc Python scanners: header/logo scan, literal and pointer scans, u16 list scanner, element
  marker scanner, key-mask run scanner, Thumb BL scanner, Capstone call-site dump.
* `arm-none-eabi-objdump -M force-thumb` for all code reads.

## 10. Legal note

No ROM, extracted graphics, music or game text is redistributed with this report. Only hashes,
addresses, algorithms, counts and short UI labels needed to identify the screens are published.
