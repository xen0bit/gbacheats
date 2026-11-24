# Connect Four / Perfection / Trouble (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Connect Four - Perfection - Trouble.gba` |
| Size | 4,194,304 bytes (0x400000, 4 MiB) |
| Header title (0xA0) | `CONNECT4COMP` |
| Game code (0xAC) | `B65E` |
| Maker code (0xB0) | `20` (DSI Games / Destination Software) |
| Software version (0xBC) | 0 |
| Complement check (0xBD) | `0x90` — **valid** (computed `(-0x19 - sum(0xA0..0xBC)) & 0xFF = 0x90`) |
| Header checksum (0xBE) | stored `0x0000`; GBATEK-style value would be `0x0090` — rebuilt-header artifact, see §7 |
| Entry word (0x00) | `0xEA00002E` (`b 0x080000C0`, stock Nintendo/GCC branch) |
| Embedded GBA headers | exactly **one** Nintendo-logo hit, at file 0x000000 → single image, not a concatenated multi-ROM |
| MD5 | `9bb3381caedebff8da5304112fc9039d` |
| SHA-1 | `8348577753b79bfdad998c75c1fda0d6569f240e` |
| SHA-256 | `a72bad45358bb1764a2e418d774733cdb4eac6109ab037aeb822d3a2287ef07e` |

Patch/trainer check (guide §16.1): the entry word is the stock GCC branch, the
crt0 at `0x080000C0` is the standard Nintendo/GCC startup (`msr CPSR, #0x12/0x1F`,
`ldr sp`, call `main` at `0x080002CC`), the first 4 KiB contains no cracktro
strings or appended menu, and the Nintendo logo is intact. The only header
anomaly is the zero 16-bit header checksum, which is a rebuild artifact, not a
trainer. No patch was applied for analysis.

## 2. Executive summary

**This SKU has no password, button-code, cheat-menu, debug-menu or unlockable
system.** It is a 2005 three-game compilation (Gravity-i / DSI Games) whose
entire "cheat surface" is the ordinary menu tree: game select, per-game
menu/options (difficulty, round timer, player count, game variant, SFX, music),
and in-game play.

Evidence, in one paragraph: the complete ASCII inventory of the 4 MiB image
contains **zero** occurrences of `password`, `passcode`, `cheat`, `debug`,
`secret`, `unlock`, `code`, `level`, `bonus`, `extra`, `credits`, or
`sound test` (36,932 printable runs scanned). The only input alphabet in the
ROM is a 37-symbol high-score name-entry alphabet at `0x1100E6`
(`-ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789`), and its buffer `0x03000BFC` is read
only by the initials-entry/draw code (two references), never compared against a
secret — it is a label field, not a validator (guide §16.2b). The joypad reader
is `0x08005630` (complemented `KEYINPUT`, edge word `0x03001D54`, held word
`0x03001CE8`); every one of its 32 handler sites tests a **single** button mask
(A/B/Select/Start/D-pad) and no two-button or sequence comparison exists. A
search for 16-bit key-mask tables over the whole image found **no** table of
three or more distinct key masks; all such byte runs are immediate operands
inside instruction streams. Screen enumeration found the game-select hub
(`0x08000960`, selection index 0–2 written to `0x03001158` at `0x08000ABE`),
three game modules (`0x08001BCC`, `0x080024A0`, `0x08002A2C`), and no hidden or
debug screen. One genuinely unreachable screen exists: a six-language selector
at `0x080005D0` that has **no caller, branch or pointer anywhere in the ROM**
(language is therefore fixed), plus several unused text descriptors
(`GAME SELECT!`, `NUMBER OF GAMES`, `BEST OF 1/3/5`, `PLAY AGAIN?`,
`PAUSE MENU`, `RESUME`, `WON!`, `YES/NO`, `SELECT PLAYER`) that no code
references. There is also no save hardware in use: mGBA keeps the `.sav` at
0 bytes and the 4-entry score/name table is re-initialised unconditionally at
boot.

Public code lists: none exist for this title (see §7), so there is no published
code to verify and no code space to enumerate. The negative result is bounded
in §6b by the exact text, key, table and screen spaces that were searched.

## 3. How to reproduce

Emulator: mGBA 0.10.5 (SDL), `Xvfb :261` 1024x768x24 + openbox, `SDL_AUDIODRIVER=dummy`.
Default SDL keymap used: A = `x`, B = `z`, Start = `Return`, Select = `BackSpace`,
D-pad = arrows, L = `a`, R = `s`. Savestates: Shift+F1 save, F1 load.

Boot and menu path (reproducible with the above keys):

1. Boot → DSI/Gravity-i splash image `0x124CEC` (exact full-screen match).
2. `Start` → second splash image `0x111CEC` (exact match).
3. `Start` → **game-select hub**, background `0x17BDEC`, index stored in
   register then written to `0x03001158` (`Up`/`Down` clamp at 0/2,
   `A` confirms, `0x08000ABE`).
   - index 0 → Connect Four (`0x03001158 = 0`, module `0x08001BCC`)
   - index 1 → Perfection (`0x03001158 = 1`, module `0x080024A0`)
   - index 2 → Trouble (`0x03001158 = 2`, module `0x08002A2C`)
4. Each module: its own "PRESS START" screen (`0x1354EC` / `0x018EE4` /
   `0x0FACE4`), `Start` → its menu (shared background `0x13ECEC` /
   module-specific), `A` → play. All three reach a mode-0 tile gameplay
   screen with `0x03002E44 = 1` (players).
5. Module 0 menu items in draw order: ONE PLAYER, TWO PLAYER, OPTIONS, QUIT
   (descriptors `0x08110E7C`, `0x08110F0C`, `0x08111074`, `0x081110BC`).
   Cursor 0..3; OPTIONS enters the option state; QUIT returns to the hub
   (verified: hub image `0x17BDEC` re-appears, `0x03001158 = 0`).
6. Module 0 options in draw order: EASY/NORMAL/HARD GAME, SFX ON/OFF,
   MUSIC ON/OFF, BACK (descriptors `0x0811174C/94/DC`,
   `0x08110D14/5C`, `0x08110DA4/DEC`, `0x081112B4`).

RAM-verified option effects (savestate diff before/after each `A`):

| Selection | RAM address | observed change |
|---|---|---|
| module 0 difficulty | `0x03002EAC` | 1 → 2 (cursor 0 + A) |
| module 0 SFX | `0x03002EB8` | 1 → 0 |
| module 0 MUSIC | `0x030012B8` | 1 → 0, and 0 → 1 |
| Trouble (module 2) variant | `0x0300114C` | 0 → 1 (CLASSIC → NO SIX) |
| Trouble (module 2) MUSIC | `0x030012B8` | 1 → 0 |

Difficulty is bounded to 0..2 by `cmp #2` in the handler (`0x0800209A`);
the three values map to EASY/NORMAL/HARD labels.

Game starts observed (all three, mode-0 gameplay after selecting ONE PLAYER):

| Selection | `0x03001158` | `0x03002E44` | DISPCNT after start | framebuffer source |
|---|---|---|---|---|
| Connect Four | 0 | 1 | `0x1340` (mode 0) | `0x1949EC` |
| Perfection | 1 | 1 | `0x1340` (mode 0) | `0x0B8E4` (font/tile region) |
| Trouble | 2 | 1 | `0x1140` (mode 0) | `0x0CBEE4` |

(Other option rows follow the same engine shape: module 1's menu accept
(`0x08002912`) starts a 1-player game on cursor 0, opens options on cursor 1 and
quits on cursor 2; its option accept (`0x0800295C`) cycles the round timer
`0x03002E38` 0..5 (labels PLAY 35/40/45/50/55/60 SECONDS), then SFX
`0x03002EB8`, MUSIC `0x030012B8`, BACK. Module 2's menu accept (`0x08002ED2`)
starts with a player count from `0x03001CEC` (0..3 → 1..4 players), opens
options on cursor 1 and quits on cursor 2; its option accept (`0x08002F9C`)
cycles the game variant `0x0300114C` (0..1 = CLASSIC / NO SIX GAME), player
count `0x03001CEC` (0..3), SFX `0x03002EB8`, MUSIC `0x030012B8`, BACK.)

## 4. Address map

| ROM address | Meaning |
|---|---|
| `0x08000000` | entry branch `b 0x080000C0` (stock) |
| `0x080000C0` | stock ARM crt0; `main` pointer at header+0x1C8 → `0x080002CC` |
| `0x080002CC` | main loop; state byte dispatch on `0x03001158` at `0x080003B2` |
| `0x08000960` | **game-select hub** (reads `0x03001158`, Up/Down index, `A` confirms) |
| `0x08000ABE` | `strb r7,[0x03001158]` — the only writer of the module selector |
| `0x080005D0` | language-select screen — **no caller / branch / pointer** (dead) |
| `0x08001BCC` | module 0 (Connect Four) front-end |
| `0x080024A0` | module 1 (Perfection) front-end |
| `0x08002A2C` | module 2 (Trouble) front-end |
| `0x08001F60`–`0x08002158` | module 0 menu/options input handler (cursor 0..3) |
| `0x08002048`–`0x08002078` | menu accept: cursor 0→players=1, 1→players=2, 2→options, 3→quit |
| `0x0800208C`–`0x080020F2` | options accept: difficulty/SFX/MUSIC/BACK |
| `0x08005630` | joypad reader: `KEYINPUT` → held `0x03001CE8`, edge `0x03001D54` |
| `0x08004A30` | text-object renderer (descriptor list → glyph display list) |
| `0x080007C10` | bitmap/OBJ text printer (descriptor string → 16x16 glyphs) |
| `0x080078E8` | initials / score-table draw (module 0 results screen) |
| `0x08007980` | score digits draw (divides 4 bytes by 10) |
| `0x0800040C`, `0x08000410` | boot writes: names `"-27<"` → `0x03000154`; bytes `"BYSMEZASLEE"` → `0x03000370` |
| `0x0810FF34` | 12-entry screen-function table used by main states 1/2 |
| `0x081100E6` | 37-symbol alphabet `-A..Z0..9` (high-score initials) |
| `0x0811010B` | ASCII→glyph-index map used by the initials/text printers |
| `0x080B72E4` | 16x16 8bpp glyph table, 0x100 bytes per glyph |
| `0x08110B1C`–`0x08111CE0` | 12-byte text descriptors `{u8 tag, u8 colour, u16 pad, u32 string, u16 1, u16 0}` |

IWRAM state:

| Address | Meaning |
|---|---|
| `0x03001158` | module/game selector (0 = Connect Four, 1 = Perfection, 2 = Trouble) |
| `0x03002E5C` | per-module screen state (0 menu / 1 press-start / 2 options) |
| `0x03002E44` | selected player count (1 or 2; `0xFF` = quit to hub) |
| `0x03002EAC` | AI difficulty 0..2 (EASY/NORMAL/HARD), default 1 |
| `0x03002EB8` | SFX enable, default 1 |
| `0x030012B8` | music enable, default 1 |
| `0x03001D54` | edge-triggered key presses, active-high (`A=1,B=2,Select=4,Start=8,Right=0x10,Left=0x20,Up=0x40,Down=0x80`) |
| `0x03001CE8` | held key state |
| `0x03000BFC` | initials-entry buffer, one 0..36 alphabet index per character |
| `0x03000154` | 4-entry initials/name table seed |
| `0x03000370` | 11-byte score/scratch table seed |

## 5. Algorithm / pseudocode

Game select (`0x08000960`):

```
idx = state[0x03001158]            # initially 0
if pressed & UP   and idx > 0: idx -= 1
if pressed & DOWN and idx < 2: idx += 1
if pressed & A:
    state[0x03001158] = idx        # 0x08000ABE
    restart main dispatch
```

Module 0 menu (`0x08001F60`):

```
cursor = 0
if pressed & UP   and cursor > 0: cursor -= 1
if pressed & DOWN and cursor < 3: cursor += 1
if pressed & A:
    if cursor == 0: players = 1; return START
    if cursor == 1: players = 2; return START
    if cursor == 2: screen = 2 (options); cursor = 0
    if cursor == 3: return QUIT (0xFF)          # back to game-select hub
```

Module 0 options (`0x0800208C`):

```
if pressed & A:
    case cursor:
      0: difficulty = (difficulty + 1) % 3       # 0x03002EAC
      1: sfx ^= 1                                 # 0x03002EB8
      2: music ^= 1; if music == 0 stop BGM       # 0x030012B8
      3: screen = 1 (menu); cursor = 0
```

Initials entry (not a password field): buffer `0x03000BFC` holds alphabet
indices 0..36. Rendering maps index → `alphabet[index]` → glyph index via
`0x0811010B` → 16x16 glyph at `0x080B72E4 + glyph*0x100`. The buffer is not
compared with any constant anywhere (see §6b).

## 6. Tables

### Key masks (active-high, `0x03001D54` / `0x03001CE8`)

| Button | Mask | Observed use |
|---|---|---|
| A | `0x0001` | confirm / accept |
| B | `0x0002` | no B-only action found in any handler |
| Select | `0x0004` | used in the language screen only (dead) |
| Start | `0x0008` | advance title / press-start |
| Right | `0x0010` | language screen only (dead) |
| Left | `0x0020` | language screen only (dead) |
| Up | `0x0040` | cursor up |
| Down | `0x0080` | cursor down |
| R / L | `0x0100/0x0200` | never tested |

Every key test found loads `0x03001D54`, `ands` with a single immediate and
branches on zero. No combined mask (e.g. `0x30`, `0x300`) and no per-frame
sequence/index comparison exists.

### Menu tree and label descriptors

| Screen | Text drawn (descriptor addresses) |
|---|---|
| Game-select hub `0x08000960` | graphical selection (3 games); no text descriptor |
| Language screen `0x080005D0` *(dead)* | `0x0811114C` SELECT LANGUAGE, `0x08111104` ENGLISH .. ESPAÑOL |
| Module 0 title | `0x08110E34` PRESS START |
| Module 0 menu | `0x08110E7C` ONE PLAYER, `0x08110F0C` TWO PLAYER, `0x08111074` OPTIONS, `0x081110BC` QUIT |
| Module 0 options | `0x0811174C` EASY GAME, `0x08111794` NORMAL, `0x081117DC` HARD, `0x08110D14/5C` SFX ON/OFF, `0x08110DA4/DEC` MUSIC ON/OFF, `0x081112B4` BACK |
| Module 1 title/menu/options | `0x08110E34` PRESS START, `0x08110EC4` TWO PLAYER, `0x08111074` OPTIONS, `0x081110BC` QUIT, `0x0811198C` PLAY GAME, `0x08111824..0x08111944` PLAY 35/40/45/50/55 SECONDS, `0x08110D14/5C`, `0x08110DA4/DEC`, `0x081112B4` |
| Module 2 title/menu/options | `0x08110E34` PRESS START, `0x08111AF4` PLAY GAME, `0x08111074` OPTIONS, `0x081110BC` QUIT, `0x08111C5C` CLASSIC GAME, `0x08111CA4` NO SIX GAME, `0x081119D4..0x08111AAC` ONE/TWO/THREE/FOUR PLAYERS, `0x08110D14/5C`, `0x08110DA4/DEC`, `0x081112B4` |

Menu accept dispatch, instruction-level:

- module 0 (`0x08002048`): cursor 0/1 → players 1/2; 2 → options; 3 → quit `0xFF`.
- module 1 (`0x08002912`): cursor 0 → start (players = 1); 1 → options; 2 → quit.
  Options (`0x0800295C`): 0 → round timer `0x03002E38` 0..5; 1 → SFX; 2 → MUSIC; 3 → back.
- module 2 (`0x08002ED2`): cursor 0 → start with player count
  `0x03001CEC` 0..3 (1..4 players); 1 → options; 2 → quit.
  Options (`0x08002F9C`): 0 → variant `0x0300114C` 0..1 (CLASSIC/NO SIX);
  1 → player count `0x03001CEC`; 2 → SFX; 3 → MUSIC; 4 → back.

### Unreferenced / cut text descriptors (`0x081115xx`–`0x081112xx` group)

`GAME SELECT!` (`0x0811159C`), `NUMBER OF GAMES` (`0x081115E4`),
`BEST OF 1/3/5` (`0x0811162C/74/BC`), `PLAY AGAIN?` (`0x08111704`),
`PAUSE MENU` (`0x08111194`), `RESUME` (`0x081111DC`), `WON!` (`0x08111344`),
`YES/NO` (`0x0811138C/D4`), `SELECT PLAYER` (`0x08111464/AC/F4`).
Every one of these descriptor addresses has **0** references in the ROM
(exact 32-bit literal search), so the corresponding screens are cut.

## 6b. Enumeration

This title has **no code/password space**. The deliverable is therefore the
bounded negative required by guide §0.2(5), with the searched spaces and their
sizes/counts:

**1. Text space (whole ROM, 4,194,304 bytes).**
36,932 printable ASCII runs (length ≥ 4) extracted. Keyword occurrence counts:

| Keyword | Hits |
|---|---|
| password, passcode | 0 |
| cheat | 0 |
| debug | 0 |
| secret | 0 |
| unlock | 0 |
| code | 0 |
| level | 0 |
| bonus, extra, credits, sound test | 0 |

All word-like strings belong to six-language UI text (`0x10ED78`–`0x1102E0`
and the descriptor strings `0x10E000`–`0x110200`), the exceptionally named
"Classic/No Six" Trouble variants, and the 37-symbol initials alphabet.

**2. Alphabet space.** Exactly one alphabet string exists in the image:
`0x1100E6` `-ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789` (37 symbols, 1 hit). No
second/alternate code alphabet, no packed 5/6-bit code table, no XOR/offset
encoded code bank.

**3. Validator space.** The initials buffer `0x03000BFC` has exactly two
references in the whole ROM: `0x08006368` and `0x0800659C`, both inside the
initials-entry/render path. No `strcmp`/`strncmp`/`memcmp` against this buffer
exists, and no other input buffer is compared with data. Accepted-set size = 0
(there is no accepted code set).

**4. Button-code space.** The pressed-key word `0x03001D54` is loaded at 32
handler sites; every site masks exactly one button (table above). A full scan of
2-byte-aligned `u16` values for runs of ≥ 3 key masks with ≥ 2 distinct values
returns **0 hits**; runs of ≥ 4 likewise 0. Byte-run hits in code are immediate
operands, not tables. There is no progress counter/index compared with a key
table, and no "last N presses" ring buffer.

**5. Screen space.** Enumerated statically and walked:

- game-select hub, `0x08000960`, selector domain **{0,1,2}** (Up clamps at 0,
  Down clamps at 2) — all three values entered and confirmed by reading
  `0x03001158`.
- 3 modules at `0x08001BCC` / `0x080024A0` / `0x08002A2C`.
- the 12-entry screen-function table at `0x0810FF34` (entries
  `0x08005D00…0x08006628`), all screen functions accounted for; none draws a
  password/debug prompt.
- one dead screen: language selector at `0x080005D0` with **0** call/branch/
  pointer references; its state index `0x03002A20`, and its two descriptors
  (`SELECT LANGUAGE`, language names), are reachable from no input. This is
  cut content, not a gated feature (no writer of a gate exists).

**6. Novel code / rejection tests.** Not applicable: no entry surface exists
(no password screen, no code keypad, no debug menu). "Rejection" is bounded by
construction: the only 37-symbol field rejects any value > 36 at
`0x08006458` (`cmp r0,#0x24; strb #0x24`), i.e. it clamps initials, and it
feeds no validator. No out-of-range code can be accepted or rejected because
no validator consumes the buffer.

## 7. Validation evidence

**Observed**
- Boot/menu/gameplay walk on :261 (mGBA 0.10.5): splash `0x124CEC`,
  `0x111CEC`; hub `0x17BDEC`; module titles `0x1354EC`, `0x018EE4`, `0x0FACE4`;
  gameplay mode-0 screens; `0x03001158` = 0/1/2 after selecting the three hub
  entries; `0x03002E44` = 1 after ONE PLAYER; DISPCNT mode changed
  `0x1454`/`0x1444` (mode 4) → `0x1340`/`0x1140` (mode 0) at game start.
- Savestate diffs: difficulty `0x03002EAC` 1→2; SFX `0x03002EB8` 1→0;
  MUSIC `0x030012B8` 1→0 and 0→1.
- Trouble (module 2) options driven at runtime: variant `0x0300114C` 0→1
  (CLASSIC → NO SIX) and MUSIC `0x030012B8` 1→0.
- `.sav` remains 0 bytes after play (no save chip activity); the 4-entry
  name/score table is re-written with defaults at every boot
  (`0x0800040C/0x08000410`).

**Derived**
- `0x08000ABE` is the only writer of `0x03001158`; the hub Up/Down clamp is
  0..2 (three games).
- Module 1 and module 2 menu/option dispatch, including the round-timer
  `0x03002E38` (0..5) and variant `0x0300114C` (0..1), is read directly from the
  handlers at `0x08002912` / `0x0800295C` / `0x08002ED2` / `0x08002F9C`.
- The language screen at `0x080005D0` is unreachable: exhaustive BL/BLX
  target scan, 16-bit branch scan and 32-bit literal-pointer scan each return
  0 callers.
- No key-sequence validator: 32 single-mask readers, zero multi-mask tests,
  zero `u16` key tables.
- No score update path: only boot (`0x0800040C/10`) and the draw routine
  (`0x080078E8/0x08007980`) reference the name/score tables.

**Inferred**
- Modules 1 and 2 share the same engine globals and handler shape as module 0,
  so their SFX/MUSIC toggles write `0x03002EB8` / `0x030012B8` as the code
  shows; only module 0's toggles were individually observed at runtime.
- The header was rebuilt after mastering (16-bit header checksum left 0x0000,
  complement valid); no functional patch.

**Published-code check**
- 3rd party cheat index page for *Connect Four / Perfection / Trouble* explicitly states
  "We currently don't have any ... cheats or cheat codes for Game Boy Advance."
- 3rd party cheat indexes have no cheats page for this SKU (searches return unrelated titles);
  3rd party cheat indexes have no page for it. No published code or password list exists to test,
  and the ROM contains no literal for any candidate string.

## 8. Unknowns

- The four score/name table entries are drawn as initials + 2-digit scores but
  their producer was not found; they may be placeholder/demo data. No
  persistent high-score storage exists.
- Whether the unreferenced `GAME SELECT!`/`BEST OF`/`PAUSE MENU` strings were
  intended for a shared shell in an earlier build; the code is absent, so the
  strings are dead.

## 9. Tooling

- `mGBA 0.10.5` (SDL), `Xvfb :261`, `openbox`, `xdotool`.
- `arm-none-eabi-objdump -M force-thumb`, Capstone 5.0.7 (Python).
- Custom scripts in `/tmp/connect4`:
  `state.py` (mGBA `gbAs` PNG chunk → RAM/VRAM; IWRAM base 0x19000,
  EWRAM base 0x21000, VRAM base 0x1000 for a 4 MiB ROM), `snap.py`
  (RAM/VRAM snapshots and diffs), `rsp.py` (GDB-RSP reader),
  `ident.py` (locate the ROM source of the active mode-4 framebuffer),
  `strrefs.py`, key-mask and BL/literal scanners.
- No screenshots were used; screen identity is from VRAM/ROM matching and
  state variables.

## Legal note

No ROM, graphics, music or extracted text is redistributed. Findings are
addresses, algorithms, state layouts and hashes.
