# 3-in-1 – Sorry! & Aggravation & Scrabble Junior (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/3-in-1 - Sorry & Aggravation & Scrabble Junior/3-in-1 - Sorry & Aggravation & Scrabble Junior.gba` |
| Size | 4,194,304 bytes (4 MiB, 32 Mbit) |
| MD5 | `74439cfebabb5616fbc00c8f7f9f747e` |
| SHA-1 | `cbc5bb55d4951e884e65ea2cab36957ee51aaadb` |
| SHA-256 | `cd55d7088a3d4bb8c81eae95e01cf38812de260bd43c0198eeb181d7c94f9548` |
| Header title (`0xA0`) | `SCRABBLECOMP` |
| Game code (`0xAC`) | `B67E` |
| Maker code (`0xB0`) | `20` |
| Fixed `0xB2` | `0x96` (OK) |
| Version (`0xBC`) | 0 |
| Entry word (`0x00`) | `EA00002E` → `0x080000C0` (ARM) |
| Complement (`0xBD`) | stored `0x8E`, computed `0x8A` — **invalid** |
| Header checksum (`0xBE`) | stored `0x0000`, computed `0xE61D` — **invalid** |

The header is a synthetic/patched compilation header, not the retail one: the
archived manual for this title is catalogued as `AGB-B65E-USA`, while this image
carries `B67E` and a title naming the compilation (`SCRABBLECOMP`). Both header
checks fail, which is consistent with a rebuilt/pressed multi-game image rather
than a retail header; `file(1)` still prints the title and code, but no region
byte is meaningful.

### Embedded GBA-header scan (multi-game check)

The guide's multi-game procedure (§5.4b) was run over the whole file:

* Nintendo logo (`24 FF AE 51 …`, 156 bytes at header `+0x04`): **1 hit**, at file `0x4` (header `0x0`).
* Second logo prefix `24 FF AE 51`: **1 hit**.
* ARM crt0 signature `12 00 A0 E3 00 F0 29 E1` (`mov r0,#0x12; msr cpsr_cf,r0`): **1 hit**, at file `0xC0`.
* Full-header heuristic scan (`+0xB2 == 0x96` plus valid complement/checksum): **0 hits**; relaxed scan (either check): **0 hits**.

**Conclusion:** this is **one** GBA image at base `0x08000000`, not three
concatenated ROMs and not a shell-plus-images pack. Sorry!, Aggravation and
Scrabble Junior are three modules inside one executable, selected from the
shared hub title screen. All ROM addresses in this report are
`0x08000000 + file_offset`; there are no sub-image bases to add.

## 2. Executive summary

**There is no in-game / developer-intended cheat system in this ROM.** No
password screen, no button code, no debug menu, no unlockable and no hidden
level select exists. This is a negative result, and it is bounded rather than
asserted:

1. The complete UI text resource table contains **194 distinct label strings**
   across six languages (`0x082D84B0`–`0x082D970C`, 392 records). None is
   `PASSWORD`, `CODE`, `CHEAT`, `DEBUG`, `SECRET`, `UNLOCK`, `LEVEL SELECT`,
   `SOUND TEST` or `CREDITS`. The only menus are the ones walked in §3.
2. Every ASCII hit for `password|cheat|code|debug|secret|unlock|hidden|bonus`
   lies inside the **Scrabble dictionary** (100,418 newline-separated words,
   file `0xF4D6C`–`0x1D4AD8`). Every hit is a dictionary lemma surrounded by
   alphabetical neighbours; `code` also matches inside `cacodemonia`
   (`caco**demonia**` contains `codemonia`). Full ±100-byte contexts are in
   `screenshots/keyword_context.log`. This confirms the prior triage: the hits are
   dictionary false positives, and the check was made by context, not by
   keyword match.
3. No password alphabet, no equal-length literal code table and no key-mask
   sequence table exists. A whole-ROM search for runs of ≥3/≥4 consecutive
   `u16` key masks produced 136 and 265 candidates respectively; the
   pointer-bearing ones (2 and 3) are all graphics, object/sprite tables or
   I/O literals (§6.2). A byte-per-press scan produced 2 pointer-bearing
   candidates, both inside graphics. The menu engine tests **one key bit at a
   time**; there is no sequence validator anywhere.
4. Published cheat sources have **no codes** for this title: TCRF documents
   only leftover Scrabble debugging text (error strings), Cheat Happens states
   "We currently don't have any … cheats or cheat codes", ChapterCheats lists
   none, and GameFAQs' cheats page is empty (403 to fetchers; search snippets
   and the other two sources agree). There is nowhere in the game to enter a
   code even if one were published.
5. All three games are available from the hub from first boot; there is no
   unlock flag, no completion gate, and no progress-gated content.

The only developer-intended "secret" content is the TCRF-listed Scrabble
debugging text, which is a **fatal filesystem error path**, not a menu: the
handler at `0x0800B600` prints `GBA FS ERROR (missing file)`, `(compression?)`,
`Out of IRam (32k)`, `Out of XRam (256k)` and then hangs in `b .` at
`0x0800B640`.

## 3. How to reproduce

Emulator: mGBA 0.10.5 SDL (`/usr/games/mgba`), scale 3, `Xvfb :118` +
`openbox`, `SDL_AUDIODRIVER=dummy`. Default mGBA SDL keymap (verified by
reading `0x04000130` while each key was held):

| GBA | Key | KEYINPUT bit |
|---|---|---|
| A | `x` | 0 |
| B | `z` | 1 |
| Select | `BackSpace` | 2 |
| Start | `Return` | 3 |
| Right/Left/Up/Down | arrows | 4/5/6/7 |
| R / L | `s` / `a` | 8 / 9 |

All presses were held 250–400 ms; the menus debounce.

### Boot and hub

1. Reset (`Ctrl+R`). Splash: DSI GAMES → legal/copyright screen (Atari,
   Hasbro, Parker Brothers, "Licensed by NINTENDO") → **hub title**
   (`screenshots/ev01_hub_title.png`).
2. Hub is a three-game selector: **Up/Down** moves the invisible selection,
   **A** enters the selected game. Order: Sorry → Aggravation → Scrabble
   Junior.
   * A on first boot → Sorry (index 0).
   * Down, A → Aggravation (`screenshots/ev08_agg_title.png`).
   * Down, Down, A → Scrabble Junior (`screenshots/ev19_hub_down2_a_enters_scrabble.png`).
   * Left/Right on the hub do nothing.
   * Start/Select/L/R on the hub do nothing (no language menu, no options).

### SORRY!

Path: hub → A → `PRESS START` (`ev02`) → Start → main menu
`PLAY GAME / OPTIONS / QUIT` (`ev03`).

* **OPTIONS**: `ONE PLAYER` (A cycles 1→2→3→4; Left/Right were not observed to
  change it), `SFX ON/OFF`, `MUSIC ON/OFF`, `BACK` (`ev04`). BACK returns to
  the main menu.
* **PLAY GAME**: starts a board immediately with the current options
  (`ev05`).
* **In game**: Start shows the `PAUSED` overlay (`ev06`). Over the board a
  `QUIT?` modal with `NO` was observed (`ev07`; the `YES` label exists in the
  table and is the modal's other option); choosing NO returned to the SORRY
  main menu. The pause-menu item set is `RESUME` / `OPTIONS` /
  `QUIT` (strings at `0x082D8B28`…`0x082D8C90`); the menu itself renders
  with a transparent/black background over the board, so only the selected
  item and the `QUIT?` modal are legible in captures.
  Main-menu `QUIT` returns to the hub (there is no separate quit confirmation).
* No other screen exists. Options are 4 items, not paged.

### Aggravation

Path: hub → Down, A → `PRESS START` → Start → main menu
`PLAY / OPTIONS / QUIT` (`ev09`, `ev08`).

* **OPTIONS**: `ONE PLAYER` (A cycles the count; the UI string table covers
  ONE…SIX PLAYERS), `SFX ON/OFF`, `MUSIC ON/OFF`, `BACK` (`ev10`).
* **PLAY**: 6-colour board starts immediately (`ev11`).
* **In game**: Start → `PAUSED` overlay (`ev12`); same pause-menu string set
  as Sorry. No extra screen.
* `BACK` returns to the main menu; main-menu `QUIT` returns to the hub.

### Scrabble Junior

Path: hub → Down, Down, A → Scrabble Junior title (`ev13`) → Start →
main menu (`ev14`):

```
Main Menu
  Play Easy Game
  Play Advanced Game
  Player Setup
  Options
  Quit
```

* **Player Setup** (`ev15`): rows `Player 1` … `Player 4` plus `Done`. The
  observed values are `Player 1 Human`, `Player 2 Easy AI`, `Player 3 OFF`,
  `Player 4 OFF`; the cursor starts on `Done`, and each row's value is
  cycled with A. (Only the labels `Human`, `Easy AI` and `OFF` were observed;
  the engine's AI strength is otherwise selected by Easy/Advanced game entry.)
* **Options** (`ev16`): `Sound ON/OFF`, `Music ON/OFF`, `Done`.
* **Play Easy Game** / **Play Advanced Game** (`ev17`): 15×15 board;
  "Get ready to play. Press A Button to continue." then the board.
* **In-game menu** (`ev18`, Start): five icon buttons (tick, circular arrow,
  `S` disc, `?`, back arrow); the glyphs denote play-word, shuffle, swap,
  help and back (inferred from the icons). No debug, code or level entry.
  `Quit` in the main menu returns to the hub.
* There is no language menu in this engine either.

### Codes tested

None exist to test: no published codes were found and the game exposes no
entry screen. The only literals worth testing were UI words, and no UI screen
accepts text. Button sequences were tested at the hub (see §6b): a
Konami-style `Up Up Down Down Left Right Left Right B A` did nothing except
move the hub selection and enter Scrabble Junior; `L+R+Select` produced a
byte-identical screen (0 changed pixels); Start/Select alone did nothing at
the hub.

## 4. Address map

| ROM address | File offset | Contents |
|---|---|---|
| `0x08000000` | `0x0` | GBA header (patched: title `SCRABBLECOMP`, code `B67E`, checksum invalid) |
| `0x080000C0` | `0xC0` | ARM crt0 (`mov r0,#0x12; msr cpsr_cf`; stack setup; installs IRQ vector at `0x03007FFC`) |
| `0x080000FC` | `0xFC` | ARM IRQ dispatcher (also the BIOS IRQ handler trampoline) |
| `0x08001174` | `0x1174` | Thumb main/init; state byte at `0x03000A44` |
| `0x080014CC` | `0x14CC` | Key-read helper: `held = ~*(u16*)0x04000130`; `pressed = held & ~prev`; stores held at `0x0300490A`, pressed at `0x03004D08` (base literal `0x03004100`, offsets `0x80A`/`0xC08`) |
| `0x08007DB4` | `0x7DB4` | Duplicate of the key-read helper (second engine) |
| `0x0800B600` | `0xB600` | GBA-FS fatal error handler; prints dev text, then `b .` at `0x0800B640` |
| `0x080F4BA0` | `0xF4BA0` | Dev error text: `GBA FS ERROR  (missing file)`, `GBA FS ERROR  (compression?)`, `Out of IRam (32k)`, `Out of XRam (256k)` |
| `0x080F4C08` | `0xF4C08` | Asset names `BG_palette`, `BG_chars`, `BG_gbawmap`; `dictionary`, `cannot find character` |
| `0x080F4D6C` | `0xF4D6C` | **Scrabble dictionary**, newline-separated, `aah` … `zyzzyva` + two-letter list, ends `yo\r\n\x10` at `0x081D4AD8` |
| `0x081D4AD8` | `0x1D4AD8` | End of dictionary; graphics/audio data follows |
| `0x082D84B0` | `0x2D84B0` | UI text table: 392 records of `{u32 style, u32 string_ptr, u32 1}`, 12 bytes each, six language columns; ends `PURPLES WON!` at `0x082D970C` |
| `0x083734B5` | `0x3734B5` | Proportional-font character ramp (` !"#$%…`) used by the Scrabble engine |
| `0x0300490A` (IWRAM) | — | Key **held** word (Derived) |
| `0x03004D08` (IWRAM) | — | Key **pressed-this-frame** word (Derived) |
| `0x04000130` | — | `KEYINPUT` (active-low; `0x03FF` idle) |

UI text table — complete list of distinct labels (English column), in table
order; each label also exists in NL/FR/IT/DE/ES where the screen is localized:

```
PLAYER 1 IS ON REDS!   PLAYER 1 IS ON YELLOWS!   RED TO GO FIRST!
YELLOW TO GO FIRST!    RED WINS!                 YELLOW WINS!
IT'S A DRAW!           SFX ON / SFX OFF           MUSIC ON / MUSIC OFF
PRESS START            ONE PLAYER / PLAY          TWO PLAYER / THREE PLAYER /
FOUR PLAYER            OPTIONS                    QUIT
ENGLISH NEDERLANDS FRANÇAIS ITALIANO DEUTSCH ESPAÑOL   SELECT LANGUAGE
PAUSE MENU             RESUME                     QUIT
BACK                   OPTIONS MENU               WON!
YES / NO               VS                         SELECT PLAYER
SELECT PLAYER 1        SELECT PLAYER 2            0 1 2 3 4 5 6 7
GAME SELECT!           NUMBER OF GAMES            BEST OF 1 / 3 / 5
PLAY AGAIN?            EASY GAME / NORMAL GAME / HARD GAME
PLAY 35/40/45/50/55/60 SECONDS
ONE PLAYER … SIX PLAYERS   PLAY GAME
BLUES WON! REDS WON! YELLOWS WON! GREENS WON! PINKS WON! PURPLES WON!
```

Two things matter for the cheat question:

* The only input surfaces in the whole table are menu items. There is no
  alphabet, keypad, "enter code", "password", "sound test" or "credits" item.
* The language strings (`0x082D8A98`–`0x082D8AE0`) and the series strings
  (`GAME SELECT!`, `NUMBER OF GAMES`, `BEST OF 1/3/5`, `SELECT PLAYER`,
  `EASY/NORMAL/HARD GAME`, `PLAY nn SECONDS`) have **no code xref**: their
  record addresses and text pointers appear only inside the resource table
  itself. They are leftovers from the standalone builds (or the EU build's
  language screen) and are not wired to any reachable screen in this image.
  The filtered table above is therefore the *complete* reachable UI
  vocabulary, not a sample.

## 5. Algorithm

No code/password validator exists. The input pipeline that a cheat would have
to use is:

```
held    = (~*(u16*)0x04000130)            # Thumb helper at 0x080014CC
pressed = held & ~prev
prev    = held
```

The menu engine (e.g. the A-button test at `0x08005DFC`–`0x08005E0E`) reads
one bit of `pressed`/`held`, plays a sound, and changes a menu index; there is
no counter of recent presses, no expected-mask array and no checksum. A
sequence validator would require one of those three things, and none is
present anywhere in the 4 MiB image.

## 6. Tables

### 6.1 Published codes

| Source | Result |
|---|---|
| TCRF (`Sorry!, Aggravation, Scrabble Junior`) | Only "Scrabble Junior Debugging Text" (error strings). No codes, no hidden menus. Verified in ROM at `0x080F4BA0`–`0x080F4D6B`. |
| Cheat Happens (title 40886) | "We currently don't have any … cheats or cheat codes." |
| ChapterCheats (16032) | Cheats page exists, no codes listed. |
| GameFAQs (929026) cheats | 403 to automated fetch; search snippet shows only game info/message board, no code list. No other source (VGChartz, Nintendo wiki) lists any. |

There is therefore **no published code to verify**. §3.4's "known-good anchor"
step is vacuous for this title; the report records that explicitly rather than
silently skipping it.

### 6.2 Key-mask tables

| Scan | Candidates | Pointer-referenced | Classification |
|---|---|---|---|
| `u16` runs ≥3 from `{1,2,4,8,0x10,0x20,0x40,0x80,0x100,0x200}` | 265 | 3 (`0x242320`, `0x2D70C8`, `0x2D70E8`) | graphics/tile data; `0x1D6020` are tile indices, `0x2D70xx` are sprite/object records |
| Same with `{0x10…0x800}` (in case of a remapped mask) | 136 | 2 (`0xB4A2`, `0xBA2A`) | false positives from I/O literals `0x04000008`, `0x04000200` |
| Byte-per-press runs ≥5 | 5,321 | 2 | both graphics (`0x252D5F`, `0x2739DC`) |

No table is referenced by an input validator. This is the guide's §5.4a test
inverted: with no published prefix, every plausible mask run was enumerated
and classified, and none is code.

### 6.3 Dictionary (the reason keyword hits are noise)

| Property | Value |
|---|---|
| File range | `0xF4D6C`–`0x1D4AD8` (ROM `0x08F4D6C`–`0x081D4AD8`) |
| Size | 916,844 bytes |
| Encoding | lowercase ASCII, `\n` separated (`\r\n` in the two-letter tail), `\x10` terminator |
| Words | 100,418 |
| First / last | `aah` / `zyzzyva` (then the sanctioned two-letter list, ending `yo`) |
| Keyword hits inside | 81 exact ASCII hits for the 8 keywords; **all** inside this range |

English/Scrabble word list, alphabetical, includes inflections; that is why
`password`, `passwords`, `cheat`, `cheats`, `cheateries`, `debug`,
`debugging`, `secret`, `secretary`, `unlock`, `hidden`, `bonus`, and `code`
inside `cacodemonia` all appear without being game text.

## 6b. Enumeration

Because there is no code system, enumeration is an enumeration of the *search
space that could have contained one*, plus proof that each bounded space is
empty. This is the §0.2 negative-result form.

### Bounded space 1 — text-entry codes (password / code / cheat)

* **Space:** the complete UI string resource table, 392 records in six language
  columns, `0x082D84B0`–`0x082D970C`. Every label was decoded and listed in §4.
* **Result:** 0 labels denote a password/code/cheat/debug/level-select/credits
  screen. There is no on-screen keyboard, no alphabet string and no text-entry
  widget in any of the 18 walked screens.
* **Why dictionary hits are not codes:** all 81 hits are word-list entries.
  Example contexts (full log in `screenshots/keyword_context.log`):
  * `password` @ `0x1808EE`: `…passport|passports|passway|password|passwords|past|pasta…` (alphabetical neighbours `pass*` → `past*`).
  * `cheat` @ `0x115338`: `…cheapskates|cheat|cheated|cheater|cheateries|cheaters|cheatery|cheating|cheatingly|cheats|check…`.
  * `debug` @ `0x1260C6`: `…debouch|debouched|debug|debugged|debugger|debuggers|debugging|debugs|debunk…`.
  * `code` @ `0x10F488` is the substring `codemonia` inside `cacodemonia`; the real lemma `code` @ `0x1199A5` sits between `coddling` and `coded`.
  * `unlock` @ `0x14CBB8`: `…gunlock|gunlocks|unlock|unlocked|unlocking|unlocks…`.
  A real code table would be a run of equal-length NUL-terminated strings with
  a pointer table (guide §11). A scan for ≥3 consecutive equal-length
  uppercase strings found only the UI text at `0x104A0`–`0x10EFC`; no code
  table exists.

### Bounded space 2 — button codes / hidden menus

* **Space:** all `u16` and byte-per-press key-mask runs in the 4 MiB file
  (scans in §6.2), plus every menu transition the engine can reach.
* **Result:** no sequence table, no progress counter, no hidden screen.
  * `L+R+Select` at the hub: 0 pixels changed.
  * Konami sequence at the hub: only the normal D-pad selection + A entered
    Scrabble Junior (i.e. the sequence was consumed as ordinary navigation).
  * `Start` at the hub: no change; `Select` at the hub: no change. Select is a
    no-op on every screen tested. Start's only roles are the three
    `PRESS START` title screens and toggling the in-game pause overlay; inside
    menus the D-pad moves and A selects. B was a no-op on the screens tested.
* **Menus enumerated (all three games, all reachable screens):**
  * Hub title.
  * Sorry: title → main (PLAY GAME/OPTIONS/QUIT) → options (players/SFX/MUSIC/BACK) → board → PAUSED → pause `QUIT?` modal (NO observed).
  * Aggravation: title → main (PLAY/OPTIONS/QUIT) → options (players/SFX/MUSIC/BACK) → board → PAUSED.
  * Scrabble Junior: title → main (Easy/Advanced/Player Setup/Options/Quit) → Player Setup (4 players + Done) → Options (Sound/Music/Done) → board → in-game 5-icon menu.
  That is 18 distinct screens, all captured (`screenshots/ev01`–`ev19`).

### Bounded space 3 — developer-intended leftovers / debug gates

* **Space:** the whole ROM's dev/error strings and their xrefs.
* **Result:** the only dev text is the TCRF-listed Scrabble FS error block.
  Its xrefs (`0x0800B644`, `0x0800B728`, `0x0800B7E8`, `0x0800B868`,
  `0x0800BE70`, `0x0800BF40`, `0x0800BF50`, `0x0800BF54`, `0x0800C594`,
  `0x0800D780`) are all inside the FS loader/error paths; the missing-file
  handler at `0x0800B600` prints and executes `b .`. No debug flag, no gate,
  no hotkey. The asset names (`BG_palette`, `BG_chars`, `BG_gbawmap`,
  `dictionary`) are filesystem keys, not menu labels.

### Novel code / rejection test

A "novel code" cannot be minted because no code system exists: there is no
alphabet, no length, no field layout and no validator. The equivalent negative
bounds were proven positively:

* An empty/absent entry surface was tested by entering every reachable menu
  item in §3 with A (no text-entry surface appears anywhere).
* The mask-space bound was proven by exhausting all mask runs and verifying
  each pointer-referenced candidate is graphics (`0x242320`, `0x2D70C8`,
  `0x2D70E8`) — a code table would have to be one of these, and none is.

Stating this as a bounded negative is the correct deliverable here per guide
§0.2 item 5; there is no representable code value to accept or reject.

## 7. Validation evidence

**Observed (emulator, mGBA on `:118`):**

* Boot order and the hub selector; every screen and menu in §3, with
  screenshots `screenshots/ev01`–`ev19`.
* `PRESS START` screens for all three games; `PAUSED` overlays in Sorry and
  Aggravation; `QUIT? NO` modal in Sorry over the board.
* Keymap verified by holding each key and reading `0x04000130`
  (A `0x03FE`, B `0x03FD`, Select `0x03FB`, Start `0x03F7`, L `0x01FF`,
  R `0x02FF`, Right `0x03EF`, Left `0x03DF`, Up `0x03BF`, Down `0x037F`).
* `L+R+Select` produced no pixel change; the Konami input only performed
  normal hub navigation.

**Derived (static, bytes verified):**

* Single header / single image; no embedded second or third GBA header or
  logo.
* Dictionary range and word count; all keyword hits are inside it.
* Complete UI string table (392 records, six language columns) and the absence of any
  code/cheat/debug label.
* FS error handler prints the TCRF text and hangs.
* Key helper semantics and the one-bit-at-a-time menu tests.

**Inferred:**

* The exact key that opens the Sorry pause menu's item list (the list renders
  over the board with a transparent/black background; only `PAUSED` and the
  `QUIT? NO` modal were captured). The item set (`RESUME`, `OPTIONS`, `QUIT`)
  is derived from the string table and from the observed QUIT modal returning
  to the main menu.
* The hub's selection is invisible; order Sorry→Aggravation→Scrabble is
  derived from the observed Down-count/entry pairs.

## 8. Unknowns

* Why the header checks are invalid and why the title/code differ from the
  retail `AGB-B65E-USA`: the file is a rebuilt/pressed compilation image. No
  gameplay difference was observed.
* The exact code path of the Sorry pause-menu item list (see Inferred above);
  it does not affect the negative result.
* Whether the dead language/series strings are reachable in another regional
  build. In this image their table records have no code xref, so they are not
  reachable here.

## 9. Tooling

* `mGBA 0.10.5` SDL, `Xvfb :118`, `openbox`, `scrot`, `xdotool`,
  `ImageMagick`.
* `arm-none-eabi-objdump` (`-M force-thumb`), Capstone 5.0.9,
  Python 3 (struct/re/Pillow/numpy).
* Scripts (in `/tmp/opencode/sorry`): `scan_hdr.py`, `hdr_scan2.py`
  (header/logo scan), `shotmax.py` (blink-defeating screenshot composite),
  inline scans for mask runs / equal-length string tables / keyword contexts
  (`keyword_context.log`).
* Screenshots: `screenshots/ev01`–`ev19`.
* No ROM, graphics, audio or extracted text is redistributed here.

### Legal note

Analysis performed on a locally owned ROM image. No copyrighted assets are
included; only hashes, addresses, string *types*, and menu labels already
published by the game's own UI are quoted, plus the short error strings
documented by TCRF.
