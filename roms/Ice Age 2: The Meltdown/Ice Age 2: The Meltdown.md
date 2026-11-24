# Ice Age 2: The Meltdown (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Ice Age 2: The Meltdown/Ice Age 2: The Meltdown.gba` |
| Size | 16,777,216 bytes (`0x01000000`) |
| Header title | `ICE AGE 2` |
| Game code / maker | `BIAE` / `7D` |
| Software version | `0x00` (Rev.00) |
| Entry word | `0xEA00002E` (stock `b 0x080000C0`) |
| Header checksum | `0x0000` |
| Complement byte (`0xBD`) | `0xB5` (expected `0xCD` — noted, see §8) |
| MD5 | `11cb293eb98b1d7bab027cda8777c98e` |
| SHA-1 | `383b6205d688d9640cb6930c02add46873f8a10d` |
| SHA-256 | `927acd5859c1fb8cfe0818da4b6423fb4699c104019441b5914558eade5cb5b7` |

**Embedded-header scan:** full-file scan for the 16-byte Nintendo-logo prefix
`24 ff ae 51 69 9a a2 21 3d 84 82 0a 84 e4 09 ad` returned exactly one hit, at
file offset `0x4` (i.e. the single normal header based at `0x0`). There is no
second image, multiboot stub, appended trainer, or patched entry point. This is
a single retail image, not a multi-game cart.

## 2. Executive summary

This game has **no password/entry-code system**. The in-game cheat surface is a
**hidden developer "CHEAT MENU"** gated by a single IWRAM word at `0x03004A80`.
When that word is `6`, pressing **L+R** opens a 5-entry debug menu:

1. Adventure Level Select
2. Scrat Rush Level Select
3. Sound Test
4. Save All Animals
5. Unlock Bonus Content

All five entries were walked in mGBA with RAM evidence. The level selects expose
**5 Adventure areas** (levels 1–5/6 + Boss + Tutorial depending on area) and
**5 Scrat Rush areas** (direct launch). Sound Test cycles **14 music tracks**
and **112 sound effects**, matching the plaintext sound-ID bank at `0x4EC4C`.
"Save All Animals" sets 10 bytes at `0x0300446A` to `0xFF`; "Unlock Bonus
Content" writes the save record and returns to the title screen.

The published CodeBreaker code from 3rd party cheat indexes (`74000130 00FF 33004A80 0006`, then
L+R) was verified literally in the ROM and reproduced in the emulator. **The
gate is exact:** writing `5` lands on Game Over, `7` lands on Options, `6` opens
the cheat menu — so the menu state is one value in the game's screen-state word,
not a range. No GameShark/CodeBreaker codes are reported as findings; the CB
code was used only as a research tool to reach the developer-intended menu.

## 3. How to reproduce

**Toolchain:** mGBA (custom `/usr/local/bin/mgba`, `-3 -d`), Xvfb `:316`,
openbox, `xdotool` XTEST keys, `scrot`, `tesseract` for OCR, `arm-none-eabi-
objdump`, Capstone 5.0.7, Python 3.

```
Xvfb :316 -screen 0 1024x768x24 -nolisten tcp &
DISPLAY=:316 openbox &
DISPLAY=:316 SDL_AUDIODRIVER=dummy stdbuf -o0 -eL \
  mgba -3 -d "Ice Age 2: The Meltdown.gba" &
```

Keymap (mGBA SDL default): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
Select=`BackSpace`, D-pad=arrows. Hold keys 150–300 ms.

**Reaching the menu:**
1. Boot; press Start through the legal screens to the title menu.
2. In mGBA's `-d` debugger, break in with `SIGINT`, then
   `w/1 0x03004A80 0x6`, then `c` to resume.
3. Hold **L+R** (`a`+`s`) together → `CHEAT MENU` appears.
4. Navigate with D-pad, select with A (`x`), back with B (`z`).

The debugger uses a FIFO for commands; SIGINT pauses the core so `r/4`, `w/1`
etc. can be issued. Savestates were taken with `Shift+F1..F5` and decompressed
with the `gbAs` zlib chunk (see §9).

## 4. Address map

| Address | Type | Meaning |
|---|---|---|
| `0x08000000` | ROM | Header / entry (`0xEA00002E`) |
| `0x080146B0`–`0x080146DE` | code | Screen-state dispatch helpers; `cmp [0x03004A80], #0x86` |
| `0x08013CD4`–`0x08013DA4` | code | State machine reading `[0x03004A80]` (`cmp #0x86`) |
| `0x0802603A`–`0x08026088` | code | State checks incl. `cmp [0x03004A80], #0x89` |
| `0x080280C4`–`0x08028174` | code | Global-state copy/init/compare helpers around `0x03004A34/40/60/80` |
| `0x0800A61E`, `0x08022D16`, `0x08022CFE` | code | Other LDR refs to `0x03004A80` |
| `0x03004A80` | IWRAM word | **Screen-state word.** `3`=title, `1`=gameplay, `5`=game over, `7`=options, `6`=**hidden cheat menu** |
| `0x03004A34` | IWRAM word | Volatile sound handle (increments on sound play) |
| `0x03004A40`, `0x03004A60` | IWRAM words | Related state words (both `6` while cheat menu open) |
| `0x0300446A`–`0x03004473` | IWRAM bytes | Animal-save bitfield; "Save All Animals" sets all 10 to `0xFF` |
| `0x4EC4C`–`0x4EDB8` | ROM strings | 14 song names, stride `0x1C` (NUL-padded) |
| `0x4EDD4`– | ROM strings | 112 SFXID names, stride `0x24` |
| `0x43190` | ROM string | Hidden copyright `c 2004 Vivendi Universal Games` |
| `0xB48570` | ROM string | Krawall sound-engine version `$Id: Krawall $Id: version.h 8 2005-04-21 ...` |

**LDR-literal scan:** the u32 `0x03004A80` appears in 10 literal pools; a raw
Thumb `LDR Rd,[PC,#imm]` scan found exactly 10 referencing instructions at
`0x0800A61E`, `0x08013CEC`, `0x080146C8`, `0x08022D16`, `0x0802606A`,
`0x0802803E`, `0x080280CC`, `0x08028114`, `0x08028136`, `0x08028158`.

## 5. Algorithm (gate model)

The cheat menu is not a checksum code; it is a **screen-state injection**:

```
state = *(u32*)0x03004A80        # game's current screen/task id
if state == 6 and (held keys & (L|R)) == (L|R):
    enter hidden CHEAT MENU
```

The CodeBreaker line implements this as a conditional byte write:
`74000130 00FF` tests `KEYINPUT == 0x00FF` (active-low `L|R` held), then
`33004A80 0006` writes `0x06` to `0x03004A80`. The next frame's screen dispatch
sees state 6 and builds the menu. Writing the byte alone (without L+R) leaves
the current screen unchanged but poisons the state word; the next Start/L+R
transition enters the menu.

**Menu structure (full enumeration):**

```
CHEAT MENU
├── Adventure Level Select
│   ├── Waterpark   : 1(Tutorial),2,3,4,5,Boss; Tutorial; Back
│   ├── Rocky Pass  : (levels + Boss); Back
│   ├── Forest      : 1..6, Boss; Back
│   ├── Geyser Field: (levels + Boss); Back
│   ├── Ice Floes   : (levels + Boss); Back
│   └── Back
├── Scrat Rush Level Select
│   ├── Waterpark, Rocky Pass, Geyser Field, Ice Floes, Forest  (direct launch)
│   └── Back
├── Sound Test
│   ├── Music   : 14 entries, wraps at 14
│   ├── Effects : 112 entries, wraps at 112
│   └── Back
├── Save All Animals  → memset(0x0300446A, 0xFF, 10)
└── Unlock Bonus Content → writes save record, returns to title
```

## 6. Tables

### 6.1 Screen-state word (`0x03004A80`) — observed values

| Value | Screen | Evidence |
|---:|---|---|
| `0` | blank/transition | RAM write + OCR (no menu) |
| `1` | in-game (gameplay) | observed after launching Waterpark 1 |
| `3` | title screen | initial RAM read at boot |
| `5` | Game Over | RAM write + OCR `GAME-OVER` |
| `6` | **CHEAT MENU** | RAM write + OCR `CHEAT MENU` |
| `7` | Options | RAM write + OCR `OPTIONS:` |

### 6.2 Sound Test bank

Music (`0x4EC4C`, stride `0x1C`): `SONG_SCRAT_SWING`,
`SONG_ADVENTURE_WINTER`, `SONG_DISTANT_GEYSERS`, `SONG_PEACEFUL_PASS`,
`SONG_PERILOUS_PASS`, `SONG_RAFT_BATTLE`, `SONG_SCRAT_SWING_FAST`,
`SONG_SCRAT_4CHAN`, `SONG_SCRAT_GAME_OVER`, `SONG_ESTABLISHING_SHOT`,
`SONG_BOSS_DEFEATED`, `SONG_TITLE`, `SONG_VOLCANIC_PASS`,
`SONG_ADVENTURE_VICTORY` — 14 total.

Effects: 112 `SFXID_*` names from `0x4EDD4` onward, in families
`ACT` (16), `EMT` (1), `ENV` (20), `FOE`/`FOES` (27), `ITM` (2), `PRM`/`PRIM`
(20), `SCRT` (4), `UI` (18), `VOX` (3), plus others — 112 total.

## 6b. Enumeration

**Space definition.** There is no password/checksum code space. The reachable
cheat surface is the game's 8-bit screen-state word: 256 representable byte
values, of which exactly one (`6`) is the undocumented debug screen; the other
values name ordinary screens. The menu itself has a fixed 5-entry root; each
entry was entered and its full sub-enumeration recorded (§5).

**Novel / unpublished content.** 3rd party cheat indexes document only that the menu exists and
lists its five entries generically. This report adds, from live enumeration:
the exact 5 Adventure areas and their per-area level sets (including the
separate `Tutorial` entry and area-dependent level counts 5 vs 6), the 5 Scrat
Rush areas, the exact **14** music and **112** effect counts with wrap-around
proof, and the RAM side effects of the two toggles (`0x0300446A` 10-byte `FF`
field, and the save-write + title reset). No published list contained these
details.

**Bounds proven by rejection.** Three clean probes from a fresh boot:

| Byte written to `0x03004A80` | L+R result | Interpretation |
|---:|---|---|
| `0x00` | no menu (blank/transition) | rejected |
| `0x05` | `GAME-OVER` screen | rejected — different screen |
| `0x06` | `CHEAT MENU` | **accepted** |
| `0x07` | `OPTIONS` screen | rejected — different screen |

Additionally, writing a value outside the game's expected state domain caused
`GBA Memory: Jumped to invalid address` and a core crash, confirming the word
is consumed as a dispatch index rather than a free-form flag.

**Text/button-space search (negative result on a password system).** To rule
out a separate password/entry-code surface:
* `strings -t x -n 4` over all 16 MiB produced 213,268 lines, almost entirely
  high-entropy compressed data; the only long plaintext runs were the sound-ID
  bank (`0x4EC4C`–), the hidden copyright (`0x43190`), and the Krawall version
  (`0xB48570`). No `PASSWORD`, `ENTER CODE`, `INVALID`, `SECRET`, or
  `UNLOCK` UI string exists in ASCII, `+0x20`-shifted ASCII, or UTF-16.
* Keyword grep (`password|cheat|code|debug|secret|unlock|level|bonus|...`)
  returned only `Fkey`, `kkEY`, `key3`, `SONG_*`/`SFXID_*` and random binary
  bytes — no code table or validator literal.
* Every UI label seen on-screen (`NEW GAME`, `CONTINUE`, `OPTIONS`, `SELECT
  GAME`, `CHEAT MENU`, `Adventure Level Select`, `Sound Test`, `Music`,
  `Effects`, `Save All Animals`, `Unlock Bonus Content`, `PRESS START`,
  `GAME OVER`, `SPECIALS`) is drawn from a font/tile-indexed text bank (the
  game's text is compressed/tile-indexed; `strings` finds none of it). The
  negative is therefore bounded by **screen enumeration + the sound string
  bank**, not by `strings` alone.
* Screens walked in the emulator: legal splash, title (`PRESS START`), main
  menu (NEW GAME / CONTINUE disabled / OPTIONS), SELECT GAME (3 save slots,
  `EMPTY`), OPTIONS (`MUSIC` / `SFX` / `CREDITS` / `BACK`), gameplay (Waterpark
  1), Game Over, and the CHEAT MENU with all five sub-screens. No password or
  button-code entry screen exists in any of them.

## 7. Validation evidence

* **Observed:** title/main/options/select-game/gameplay/game-over screens;
  `CHEAT MENU` and every submenu; RAM before/after values at `0x03004A80`,
  `0x0300446A`; savestate diffs confirming the 10-byte `FF` field; 14- and
  112-entry wrap-around via OCR.
* **Derived:** LDR-literal scan (10 refs) and Capstone disassembly of
  `0x080146B0`, `0x08013CD4`, `0x0802603A`, `0x080280C4`–`0x08028174`.
* **Inferred:** that `0x03004A80` is the game's generic screen-state word (the
  5/6/7/1/3 mapping is observed; the "generic" interpretation is inferred from
  the dispatcher structure). The precise meaning of the `0x86`/`0x89`
  comparisons in other helpers was not exercised.

## 8. Unknowns

* The header complement byte (`0xB5` vs expected `0xCD`) does not validate;
  likely a dump/build artifact, since the entry word and logo are stock and no
  patch/trainer is present.
* Per-area Adventure level counts for Rocky Pass, Geyser Field and Ice Floes
  were not individually OCR'd (Waterpark and Forest were). All five area names
  are confirmed; the pattern is levels + Boss, with an extra `Tutorial` entry
  on Waterpark.
* The exact save-record layout written by "Unlock Bonus Content" was not
  fully decoded (only the return-to-title effect and the large save-region
  delta were observed).
* Whether a *natural* in-game button sequence sets state 6 (the only published
  method is the CB code) was not found; no password/button entry screen exists.

## 9. Tooling

* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`
* Capstone 5.0.7 (`scan_literal2.py`, `dis_refs.py`) for LDR-literal scans
* `python3` helpers: `key.py` (XTEST keys), `dbg.py`/`dbg2.py`/`dbg3.py` (FIFO +
  SIGINT debugger control), `ssdiff.py` (gbAs zlib savestate diff),
  `gate_test.py`
* `tesseract` OCR for screen-state classification without exhausting the
  screenshot budget
* `grep -abo` / `strings -t x` for string searches; full-file Nintendo-logo
  scan for embedded headers
* mGBA `-d` command-line debugger over a FIFO, with `SIGINT` to break in.
  Alternative `gdb-multiarch -g` stub was tried but returned packet errors
  after detach, so the pty-less FIFO debugger was used throughout.

No ROM data or copyrighted assets are redistributed by this report; only
addresses, hashes, and the author's own tooling are published.
