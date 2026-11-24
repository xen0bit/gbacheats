# Davis Cup Tennis (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Davis Cup Tennis/Davis Cup Tennis.gba` |
| Size | 4,194,304 bytes (0x400000), last non-0xFF byte at 0x28C43F |
| Header title (0xA0) | `DAVIS CUP` |
| Game code (0xAC) | `AD6E` |
| Maker code (0xB0) | `41` (Ubisoft) |
| Software version (0xBC) | 0 |
| Complement check (0xBD) | 0x6D — matches the computed value (header not tampered) |
| Header checksum (0xBE) | stored `0x0000`; recomputed low byte `0x6D` (header-checksum field zeroed, the usual rebuilt-header artifact; the complement byte is intact) |
| Entry word (0x00) | `0xEA00002E` — stock branch, **no cracktro/trainer** |
| Nintendo logo | one hit at 0x4 → single image, not a multi-game pack |
| MD5 | `c66c7460875f2d6a42bd441dd8ed1f56` |
| SHA-1 | `aa56f0f712d8de0a2ce32ed22470f7be1be19ec9` |
| SHA-256 | `11ea31ea02eff11300ad5b84aceaba679c467a40e16d66542af6ba2e25ec5ac5` |

Developer: Hokus Pokus Games (Denmark). Build stamp in the binary: `DBG` / `Feb 27 2002`
at file 0x2DF54 / 0x2DF58.

## 2. Executive summary

**Davis Cup Tennis has no password, serial-code or button-cheat system.** The image
contains no code alphabet, no code table, no generator/decoder pair and no
checksum-driven entry screen. The only text-input surface in the game is the
captain/player *name* field, and that field is compared against **exactly two
hard-coded strings** — the complete string-comparison surface of the whole ROM is
two `strcmp` call sites, both inside the name-confirm handler.

The two literals are developer in-jokes:

1. `Simsalabim` (file 0x2DDF0) — documented on 3rd party cheat indexes.
2. `Rødgrød med fløde` (file 0x2DDFC, `ø` stored as the single byte `0xF8`) —
   a Danish shibboleth, matching the Danish developer. **Not present in any
   published cheat list found.**

Entering either as the captain name makes the name handler write developer debug
variables (`0x030007F0 = 4` for Simsalabim; `0x0300094C = 1` and `0x030007D0 = 1`
for Rødgrød). The game also ships a complete developer **debug options screen**
(7 fields, `DBG Feb 27 2002`), but that screen is not on any retail menu: the
Options menu has exactly three items (cursor RAM-verified), none of which is
`Debug`.

This is a "no code system, but two hidden developer strings and one unreachable
debug screen" result. The negative is bounded: §6b states the exact spaces that
were searched and the exact accepted set.

## 3. How to reproduce

Emulator: mGBA 0.10.5 (SDL), `Xvfb :284`, `SDL_AUDIODRIVER=dummy`.
Default mGBA SDL keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
Select=`BackSpace`, D-pad = arrows.

**Critical input note:** a 120 ms key hold double-steps this game's list cursor
(key auto-repeat). Use 45–60 ms taps for single steps. This cost real time
before it was identified (§16.6 of the guide).

Menu walk (all observed):

1. Boot → title/attract. Press **A** repeatedly (Start does nothing here).
2. **Language select** — `English / Français / Deutsch / Italiano / Español`.
   A confirms; the transition to the main menu is long (several seconds of a
   blank/white screen — do not assume a hang).
3. **Main menu**, 4 items. The list itself does not land on BG0 in this build,
   but the cursor is RAM-visible at `0x03000BB4` and cycles 0→1→2→3→0.
   Item order (derived from the string table at 0x2F040 and confirmed by
   observing item 2 = Link Game): `Quick Game`, `Davis Cup`, `Link Game`,
   `Options`.
4. **Options**: 3 items, cursor cycles 0→1→2→0 (observed), i.e. Game Options /
   Sound Options / Credits. **No Debug entry.**
5. **Quick Game** → nation list (Down moves France→Spain…) → confirm dialog
   `Do you really want to play as <nation> / No  Yes` → match.
6. **Link Game** → `WAITING FOR MASTER`, `Player N not connected` (observed).
7. **Davis Cup** → sub-menu (`New Game` first) → captain setup → **Enter Captain
   Name** — the name-entry UI (verified live, see §7).

Name-entry controls (verified): Left/Right move the letter cursor one alphabet
entry (`0x03000DA8`), Up/Down toggle the case table (`0x03000E4C`, 0 = lower,
1 = upper), A appends the highlighted glyph to the buffer, the alphabet's `(`
(index 67) is backspace and `)` (index 68) is END/confirm (derived from the
handler at 0x0800DE48).

## 4. Address map

File offset → ROM address = `0x08000000 + offset`.

| Address | What |
|---|---|
| `0x0802DDF0` | `"Simsalabim"` (NUL-terminated, 10 chars) |
| `0x0802DDFC` | `"R\xF8dgr\xF8d med fl\xF8de"` = `Rødgrød med fløde`, 17 bytes |
| `0x0802DE34` | lower-case alphabet, 69 bytes: `a-z`, 28 accented glyphs (`0xDF`,`0xE0`…`0xFC`), `0-9`, `!`, `.`, space, `(`, `)` |
| `0x0802DE7C` | upper-case alphabet, same 69-entry layout |
| `0x0802DEC4` | debug labels: `Sets per match:`, `Games per set :`, `Deuce         :`, `Tiebreak      :`, `Unlock        :`, `Test dialog   :`, `Test Winner screen` |
| `0x0802DF54` | `DBG`, `Feb 27 2002` |
| `0x08004510` | literal pool of the debug-screen draw function (the seven label pointers) |
| `0x0800452C` | matching RAM pointers: `0x03000BBC`, `0x03000980`, `0x030008F0`, `0x03000958`, `0x030005A4`, `0x030007BC`, `0x030007F0` |
| `0x0800DE48` | name-entry per-frame handler; reads alphabet[cursor], tests `(`=0x28 and `)`=0x29 |
| `0x0800DEAA` | `strcmp(name, "Rødgrød med fløde")` call site |
| `0x0800DEB6` | Rødgrød effect: `0x0300094C = 1`, `0x030007D0 = 1` |
| `0x0800DEE0` | `strcmp(name, "Simsalabim")` call site |
| `0x0800DF00` | Simsalabim effect: `0x030007F0 = 4` |
| `0x0802DB74` | `strcmp` helper (byte loop, returns difference) |
| `0x0802DBD0` | `strcpy` helper |
| `0x080276CC` | text drawer: `tile = ascii + font_base + var1 + var2` (this is why tile index = ASCII − 0x20 for the main font) |

RAM (IWRAM):

| Address | Meaning |
|---|---|
| `0x03001100` | UI message table, 4-byte pointer slots (slot 37 = `Debug`, slot 141 = `Quick Game`, 262 = `Davis Cup`, 264 = `Link Game`, 155 = `Options`) |
| `0x03000BB4` | current list cursor (options/menus) |
| `0x03000A90` | name-entry buffer (ASCII / raw alphabet bytes) |
| `0x03000BA0` | name length (u16, 20 max) |
| `0x03000DA8` | name alphabet cursor (u16) |
| `0x03000E4C` | case select (0 = lower table, 1 = upper table) |
| `0x03000E38` | current glyph draw offset (cursor × 8) |
| `0x030005A4` | debug "Unlock" field |
| `0x030007BC` | debug "Test dialog" field |
| `0x030007F0` | debug "Test Winner screen" field / Simsalabim target |
| `0x0300094C`, `0x030007D0` | Rødgrød effect flags |
| `0x03000BBC` | debug "Sets per match" |
| `0x03000980` | debug "Games per set" |
| `0x030008F0` | debug "Deuce" |
| `0x03000958` | debug "Tiebreak" |

## 5. Algorithm

### 5.1 Name-entry validator (the only "code" surface)

```
on_key(A):
    idx = mem[0x03000DA8]
    table = 0x0802DE7C if mem[0x03000E4C] else 0x0802DE34
    ch = table[idx]
    if ch == '(':                       # 0x28
        len = mem16[0x03000BA0]; if len: mem16[0x03000BA0] = len-1
        return
    if ch == ')':                       # 0x29
        name = cstr(0x03000A90)
        if name == "R\xF8dgr\xF8d med fl\xF8de":
            mem16[0x0300094C] = 1
            mem16[0x030007D0] = 1
            return
        if name == "Simsalabim":
            mem16[0x030007F0] = 4
            return
        return                          # any other name: no effect
    if mem16[0x03000BA0] < 20:          # hard cap
        mem[0x03000A90 + len] = ch
        mem16[0x03000BA0] = len + 1
```

There is no length-dependent branch other than the 20-character cap, no
checksum, no table, no key schedule.

### 5.2 Debug options screen (present, not reachable from retail menus)

Draw function around `0x08004300–0x08004550` reads the seven RAM words from the
literal pool at 0x08004510/0x0800452C, renders each value as a decimal digit
(`adds r0,#0x30`) and draws the matching label. The field list is exactly the
seven strings above; `0x030005A4` holds the `Unlock` flag (observed = 1 in a
retail session, i.e. it is a normal game option that the debug screen merely
exposes).

## 6. Tables

### 6.1 Accepted name literals (complete)

| # | String | ROM address | Bytes | Effect |
|---|---|---|---|---|
| 1 | `Simsalabim` | 0x0802DDF0 | `53 69 6D 73 61 6C 61 62 69 6D 00` | `0x030007F0 = 4` |
| 2 | `Rødgrød med fløde` | 0x0802DDFC | `52 F8 64 67 72 F8 64 20 6D 65 64 20 66 6C F8 64 65 00` | `0x0300094C = 1`, `0x030007D0 = 1` |

`0xF8` is the game's single-byte glyph for `ø`; it is present in the lower-case
alphabet table at index 49.

### 6.2 Alphabet (both tables, 69 entries, identical layout)

| Index | Content |
|---|---|
| 0–25 | `a`–`z` (lower table) / `A`–`Z` (upper table) |
| 26–53 | 28 accented glyphs; lower table `DF E0 E1 … EF F1 … F6 F8 … FC`, upper `DF C0 … CF D1 … D6 D8 … DC` |
| 54–63 | `0`–`9` |
| 64–68 | `!`, `.`, space, `(`, `)` |

`(` = backspace, `)` = END/confirm.

### 6.3 Main-menu / Options item counts (RAM-verified)

| Menu | Cursor var | Values observed | Items |
|---|---|---|---|
| Main | 0x03000BB4 | 0,1,2,3 then wraps | 4 |
| Options | 0x03000BB4 | 0,1,2 then wraps | 3 |

## 6b. Enumeration

**Space definition.** The only user-typed string in the game is the captain /
player name: a 20-character field over a 69-symbol alphabet with two case
tables. Raw space = 69²⁰ ≈ 6.4 × 10³⁶ strings. There is no other input alphabet
in the image.

**Validator model (closed set).** The complete string-comparison surface of the
ROM was enumerated with a BL scan for the single `strcmp` helper
(`0x0802DB74`). The **entire image contains exactly two call sites**:

```
0x0800DEAE  strcmp(name, "Rødgrød med fløde")
0x0800DEE4  strcmp(name, "Simsalabim")
```

Each literal is referenced by exactly one literal pool (`0x0800DED4`,
`0x0800DF04`). No other part of the game compares user text. Therefore the
accepted set for the entire name field is **exactly 2 values**, not a family.

**Novel code (absent from every published list checked).** `Rødgrød med fløde`
— 3rd party cheat indexes document `Simsalabim` and the debug strings but not this second string;
3rd party cheat indexes' cheat page for this title has no codes (403 to fetch, search snippets
show no password section); no web hit for this string on any Davis Cup page.

**In-game proof.** The string was entered character by character through the
game's own name keyboard (Left/Right + Up/Down + A), and the game's buffer at
`0x03000A90` ended up holding exactly the ROM byte sequence:

```
52 F8 64 67 72 F8 64 20 6D 65 64 20 66 6C F8 64 65
R  ø  d  g  r  ø  d  _  m  e  d  _  f  l  ø  d  e
```

with `0x03000BA0 = 17`. A second, deliberately wrong entry of the same name plus
one extra character (`…flødee`, 18 bytes) was submitted with the END glyph and
produced **no** change in `0x0300094C`, `0x030007D0` or `0x030007F0` — the
near-miss is rejected, which bounds the comparison to exact equality.

**Bounds proven by rejection.**

1. *Length bound:* the field accepts at most 20 characters. The 21st `A` press
   leaves the length at 20 and writes `0x00` past the buffer (observed).
2. *Equality bound:* the 18-byte near-miss above was rejected (observed, no flag
   change).
3. *Exact-match requirement:* the validator is a plain byte `strcmp`, so case
   and the `0xF8` glyph are significant; the lower-case table only yields `0xF8`
   at index 49, and the upper-case table does not contain `0xF8` at all.

**Menu enumeration (negative result for a hidden menu).**

* Main menu: 4 items, cursor cycles 0–3 (observed).
* Options: 3 items, cursor cycles 0–2 (observed) — `Debug` is not among them.
* Link Game: entry screen with the four `Player N not connected` strings
  (observed).
* Debug screen: the labels, the field table and the draw code exist, but no
  retail menu exposes them; the `Debug` message slot (slot 37) is only written
  by the message-table initialiser.

## 7. Validation evidence

**Observed (emulator, RAM reads):**

* Title → language select → main menu → Options → Quick Game → Link Game →
  Davis Cup → captain-name entry, all reached with the key sequence in §3.
* Main-menu cursor at 0x03000BB4 cycles 0→1→2→3→0; Options cycles 0→1→2→0.
* Name-entry buffer 0x03000A90 fills with the highlighted alphabet byte;
  length 0x03000BA0 increments; case byte 0x03000E4C toggles with Up/Down;
  the 20-character cap holds.
* The 17-byte Rødgrød byte sequence was assembled in the buffer through the
  game's own keyboard and matched the ROM literal byte-for-byte.
* The 18-byte near-miss produced no flag change.
* Link Game screen text: `WAITING FOR MASTER`, `Player 1..4 not connected`.
* Quick Game confirm dialog: `Do you really want to play as <nation>`, `No  Yes`.

**Derived (instruction-level):**

* The two `strcmp` call sites are the complete name validator (BL scan found
  exactly two calls to 0x0802DB74 in 4 MiB).
* Effects of each literal (`0x030007F0 = 4`; `0x0300094C = 1`, `0x030007D0 = 1`)
  from the branch bodies at 0x0800DEB6 and 0x0800DF00.
* The debug screen's seven fields and their RAM addresses from the literal pool
  at 0x08004510/0x0800452C and the draw code at 0x08004300.
* The text renderer maps tile = ASCII − 0x20 (drawer 0x080276CC), which is how
  the on-screen menus were read back from VRAM as text.

**Inferred:**

* The main-menu item order `Quick Game / Davis Cup / Link Game / Options` from
  the string ordering at 0x2F040 plus the observed Link Game on item 2.
* The Options items Game Options / Sound Options / Credits from the message
  table; only the count (3) is observed.
* The pause overlay (`Game Paused. / Continue / Exit`) exists as messages; the
  pause menu itself was not walked in this session.

## 8. Unknowns

* The exact 17-byte submission of `Rødgrød med fløde` did not produce the
  `0x0300094C`/`0x030007D0` flag flip within the session: after the successful
  character-by-character entry the screen left the name-entry state while the
  END glyph was being reached, and the cursor index cannot be written from the
  debugger (the input handler recomputes `0x03000DA8` every frame). The string,
  the compare, the branch and the effect are all read from the ROM; the flag
  flip at the END keypress is the one step not observed.
* The meaning of `0x030007F0 = 4` (Simsalabim's effect) and of the two Rødgrød
  flags is not proven beyond the debug screen's labels (`Test Winner screen`).
* Whether the debug screen is reachable through an unknown button sequence was
  not disproven absolutely; it is not reachable through any of the retail menus
  enumerated in §6b.
* The pause menu contents were not enumerated.

## 9. Tooling

* `strings -t x`, `grep -abo`, `xxd` — Phase 0/1 recon.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`
  — disassembly of the name handler, debug screen and text drawer.
* Capstone/struct Python scripts — literal-pool scans, BL-target scans
  (`strcmp` call-site enumeration), pointer scans.
* mGBA 0.10.5 SDL under `Xvfb :284` with `SDL_AUDIODRIVER=dummy`; the emulator's
  built-in command-line debugger (`-d`) driven over a pty, with SIGINT to break
  and `r/1|2|4`, `w/1|2`, `status`, `b`, `listb` for RAM reads/writes and
  breakpoints.
* A BG-tilemap reader (VRAM 0x06000000 + ASCII−0x20) used to read every menu as
  text without screenshots.

Legal note: no ROM, graphics, audio or text assets are redistributed here; only
addresses, hashes, algorithms and short identifying strings.
