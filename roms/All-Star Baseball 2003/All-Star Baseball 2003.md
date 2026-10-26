# All-Star Baseball 2003 (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/All-Star Baseball 2003/All-Star Baseball 2003.gba` |
| Size | 4,194,304 bytes (4 MiB) |
| Header title (0xA0–0xAB) | `ALLSTAR 2003` |
| Game code (0xAC–0xAF) | `AA3E` |
| Maker code (0xB0–0xB1) | `51` (Acclaim) |
| Fixed byte 0xB2 | `0x96` |
| Main unit / device (0xB3/0xB4) | `0x00` / `0x00` |
| Software version (0xBC) | `0` |
| Complement check (0xBD) | `0xF9` (recomputed over 0xA0–0xBC: matches) |
| Header checksum (0xBE–0xBF) | `0x0000` (stored; not validated by the game) |
| Entry branch (0x00) | `0xEA00002E` (ARM branch to `0x080000C0`) |
| Embedded GBA-header scan | Nintendo logo (156 bytes at 0x04) occurs **once**, at file offset `0x4` → one GBA image, not a multi-game cart |
| MD5 | `0b2772662e6df22bd3e5dbb84d9d9e55` |
| SHA-1 | `ebcc0100a6d62f1bbe359fe9cc4baa3c61fb213f` |
| SHA-256 | `02cf8855f20deefb33d27a6e9f853a8985713bb42ab4121d905f8ecb00371ea5` |

All ROM addresses below are `0x08000000 + file_offset`. The 4 MiB image is
mirrored at `0x0A000000`/`0x0C000000`.

## 2. Executive summary

**This revision has no password system, no code-entry keypad, and no reachable
cheat or debug menu.** The game saves progress on the cartridge (mGBA created a
32 KiB `All-Star Baseball 2003.sav`); “Continue season” / “Continue series”
read that save, not a password.

The front end is Acclaim’s FELIB engine (same family as *Aggressive Inline* GBA,
but a different build). It ships 61 screen layouts (`layout\sc*.LBN`) and a
225-string text database (`text\baseball.tdb`), both decoded below. A full scan
of the text database and every screen layout found:

* **No** string containing `password`, `passcode`, `cheat`, `debug`, `secret`,
  `classic` or level-select, in ASCII or in the UTF-16 text DB. (The ROM does
  carry printf-style debug logging, e.g. `DIVE CATCH for player %d (%s)!!!` at
  `0x08043FD0`, but there is no debug menu or debug console.)
* Four text-DB strings that are never referenced by any of the 26 text-by-ID
  call sites and are absent from all 61 layouts:
  **161 `Tweak`**, **162 `All Your Baseball Are Belong To Us`**,
  **163 `Parameter`**, **164 `Value`**. These are dead text from a removed
  developer screen. (The “All your base…” joke survives in this game as a
  ballpark sign, per the GameCube FAQ, but the four strings have no code path.)
* No key-sequence validator. There is no table of cheat key masks, no
   comparison against the combined `0x0120`/`0x0180` (`R+Left` / `R+Down`)
   mask, and no literal pool or immediate sequence that builds one.

The published GBA “cheat” list was tested item by item. The only real input it
describes is **Select**, which toggles the hatched hit cursor on/off
(`0x03002DBD`), i.e. a display control, not a cheat. **L** at the team-select
screen does not open a cheat menu, **L+R** does not change uniforms, and the
`R+Left/R+Right, R+Down` “home run” lines have no implementation in this ROM
(they paraphrase the console version’s R-button pitch-location guess).

Negative result, bounded: 30+ screens/menus walked, 69,904 ASCII runs and 225
UTF-16 text-DB strings classified, 61 layouts inspected, the 71-entry screen
table enumerated (60 handlers, 11 null slots), and every published code entered
in mGBA. No accepted code exists, so no code could be minted. §6b states the
searched spaces and the rejection evidence.

## 3. How to reproduce

### Emulator and display

```bash
mkdir -p /tmp/opencode/asb2003
Xvfb :132 -screen 0 1024x768x24 &
DISPLAY=:132 openbox &
cd "/mnt/gbacheats/roms/All-Star Baseball 2003"
DISPLAY=:132 SDL_AUDIODRIVER=dummy mgba -3 "All-Star Baseball 2003.gba" &
```

mGBA SDL default keymap used here:

| GBA | Key |
|---|---|
| A | `x` |
| B | `z` |
| L | `a` |
| R | `s` |
| Start | `Return` |
| Select | `BackSpace` |
| D-pad | arrow keys |

Screenshots were taken with `scrot` and cropped with
`convert shot.png -crop 720x480+152+144 +repage out.png`.
Savestates: `Shift+F1`…`Shift+F10` save, `F1`…`F10` load. Savestate 1 was the
Single Player menu, 2 an in-game at-bat, 3 the main menu, 4/5 Batting Practice.

### Menu path walked (all observed; see `evidence/`)

```
Boot logos
Title ("Press Start")                      evidence/01_title.png
Main menu                                  evidence/02_main_menu.png
 |- Single player                          evidence/03_single_player.png
 |   |- Quick Game -> team select          evidence/04_quick_game_team_select.png
 |   |    -> gameplay -> pause -> Game options / Change controls / Quit
 |   |- Exhibition -> team select
 |   |- All-Star Game -> AL/NL + difficulty
 |   |- Batting Practice -> setup          evidence/06_batting_practice.png
 |   |- Home Run Derby -> setup            evidence/07_hrd_setup.png
 |   |    -> player select (AL/NL lists)   evidence/08_hrd_player_select.png
 |   |    -> derby game -> pause
 |   |- Season -> season type (8 entries)  evidence/13_season_type.png
 |   |    -> season main (Play next / Schedule / Standings / Statistics /
 |   |       Team management)              evidence/12_team_management.png
 |   |       -> Schedule (game list), Standings (table), Statistics (table)
 |   |       -> Team management -> Set lineup -> Sub player/Swap order, Swap position
 |   |- World Series -> team select -> Playoffs main
 |- Multiplayer -> 2P LINK-UP (no link)    evidence/14_multiplayer_link.png
 |- Trading cards                          evidence/09_trading_cards.png
 |- Options                                evidence/05_game_options.png
 |- Credits                                evidence/15_credits.png
```

Every screen above was opened with the d-pad/A and B was used to walk back.
No screen in this list is a password, code, cheat or developer menu.

### Savestate RAM mapping (used for the observations below)

mGBA writes a PNG whose `gbAs` chunk is a zlib stream. Decompressed state is
397,312 bytes; the memory blocks are:

| State offset | GBA memory |
|---:|---|
| `0x19000` | IWRAM `0x03000000`–`0x03007FFF` |
| `0x21000` | EWRAM `0x02000000`–`0x0203FFFF` |

The first two words of the file-system globals confirm the mapping:
`0x03003870` and `0x03003874` both hold the ROM directory address
`0x0804C4C0`.

### Codes/inputs tested in the emulator

| Input | Where | Result |
|---|---|---|
| `L` | Quick Game / Exhibition / All-Star team select; HRD setup; pause; title | No menu. Only the animated sponsor banner at top-right changes. |
| `L+R` held | Team-select then start; and in-game | No uniform change (same away gray / home white kits). `evidence/04`, `evidence/11`. |
| `Select` | Batting Practice and Quick Game, before a pitch | Toggles the hatched hit cursor: visible at `0x03002DBD = 1`, gone at `0`. RAM diff and screenshots: `evidence/17_select_cursor_on.png`, `evidence/18_select_cursor_off.png`. |
| `R+Left`, `R+Down` | At bat (RH and LH batters) | No state change, no home run; no `0x0120`/`0x0180` mask exists in the ROM. |
| `R+Right`, `R+Down` | At bat (RH batter) | Same. |
| `A` during credits | Credits screen | No visible change. No “commentary” string/asset exists in the ROM. |
| `Up,Up,Down,Down,Left,Right,Left,Right,B,A` | Title | No effect. |
| `L,L,B,B,R,R,L,R` | Title | No effect. |
| `Up,Down,Up,Down,Left,Right,B,R` | Title | No effect. |
| `L` at pause / `Select` at team select | — | No effect. |

The published gameplay lines are therefore either normal controls (Select) or
console-version paraphrases (R + direction). They are not secret codes.

## 4. Address map

| ROM address / file offset | Meaning |
|---|---|
| `0x08000000` / `0x0` | Header + ARM crt0; `main` literal at `0x13C` → `0x0802851C` |
| `0x0802C7B8` / `0x2C7B8` | Hardware key poll: reads `0x04000130`, negates, writes IWRAM |
| `0x03003ACC` (RAM) | Held keys, active-high (`u16`, left of the pair) |
| `0x03003AD0` (RAM) | Newly-pressed keys (`u16`) |
| `0x08029A2C` / `0x2A2C` | Getter: newly-pressed keys for player index (reads `0x03000270 + 2*i`) |
| `0x08029A3C` / `0x2A3C` | Getter: held keys for player index (reads `0x03000278 + 2*i`) |
| `0x03000270` (RAM) | 4 × `u16` new-press array (players 1–4) |
| `0x03000278` (RAM) | 4 × `u16` held-key array |
| `0x03000280` (RAM) | 4 × `u16` previous-held array |
| `0x03000E84` (RAM) | Gameplay mirror of the held-key word |
| `0x08015A3C` / `0x15A3C` | In-game cursor/menu handler; `0x08015A60` tests `new & 4` (Select) |
| `0x03002DA0` (RAM) | Gameplay cursor/HUD state struct |
| `0x03002DBD` (RAM) | `+0x1D` hit-cursor display flag; toggled by Select, read at `0x08016C9A`, `0x0801CB60` |
| `0x0804C4C0` / `0x4C4C0` | FELIB file-system directory: `u32 count=502`, `u32 hash_mult=10`, then 16-byte entries |
| entry layout | `u32 hash`, `u32 0`, `u32 size`, `u32 offset` (offset relative to ROM `0x0804C4C0`) |
| `0x08132228` / `0x132228` | `TDBI` text database: magic, `u32 version=2`, `u32 size=0x190E`, `u32 0`, `u32 count=225` |
| `0x0813223C` / `0x13223C` | 225 × (`u16 id`, `u16 char_offset`); strings base `0x081325C0` (offset in `u16` units) |
| `0x083C4564` | 71 × `char*` screen-layout names (`layout\sc00.LBN` … `layout\sc70.LBN`) |
| `0x083C46F4` | 71 × Thumb handler pointers; 60 non-null, 11 null (indices 5,37,38,54,55,56,61,62,63,69,70) |
| `0x083C4884` | 4 × `u16` link-input merge order: `0040 0080 0001 0002` (Up,Down,A,B) — **not** a cheat table; used at `0x08007934` |
| `0x08042D28`–`0x080433xx` | ASCII credits block (`!header` / ` name` lines) |
| `0x08048BA8` | HRD player names (`Mike Bordick`), data table pointers at `0x083D4CD4` |

Layout blobs: 61 of the 71 names resolve through the directory; the 10 whose
name has no data are `sc37, sc38, sc54, sc55, sc56, sc61, sc62, sc63, sc69,
sc70` (the handler table is also null for these plus `sc05`).

## 5. Algorithm

### 5.1 FELIB file lookup (derived)

```
dir = 0x0804C4C0
count = u32[dir+0]          # 502
mult  = u32[dir+4]          # 10
h = 0
for c in name:
    if 'A' <= c <= 'Z': c += 0x20      # case fold
    h = (h * mult + c) & 0xFFFFFFFF
binary-search dir+8 .. dir+8+count*16 for entry.hash == h
size = entry.size ; data = 0x0804C4C0 + entry.offset
```

Verified: `text\baseball.tdb` → hash `0x4DCD59CA`, size `0x1912`,
offset `0x0E5D68` → file `0x132228` (`TDBI`). `layout\sc00.LBN` → size `2348`,
file `0x1E4688`.

### 5.2 Text database (derived)

```
if rom[0:4] != "TDBI": fail
count = u32[0x04]
table = 0x14
strings = table + count*4
for each (id, off16):
    ptr = strings + off16*2
    text = UTF-16LE until 0x0000
```

The 225 strings include menu labels, stat abbreviations, in-game prompts and
the HRD/Season/World-Series text. The only alphabet runs are ids 13/14
(`ABCDEFGHIJKLM`, `NOPQRSTUVWXYZ`); no code path reads them as a
code keypad; the C runtime hex tables at `0x049920`/`0x049940` are libc.

### 5.3 Input path (derived + observed)

```
every frame: 0x04000130 -> ~value
  held   = value                     (0x03003ACC)
  new    = held & ~previous          (0x03003AD0)
  arrays at 0x03000278 (held) / 0x03000270 (new), indexed by player
gameplay reads them through 0x08029A3C (held) / 0x08029A2C (new)
```

The in-game handler at `0x08015A3C` reads `new & 4` (Select):

```
if (new & 4):
    flag = 0x03002DBD
    flag ^= 1
```

`0x03002DBD` is read at `0x08016C9A` (draws the hatched contact triangle) and
`0x0801CB60` (HUD visibility). Observed: with flag 1 the hatched triangle is in
the zone; with flag 0 it is gone. This is the real behaviour behind the
published “press Select to hit harder” line.

### 5.4 Why there is no code validator

A password/passcode validator needs at least one of: an input screen with an
alphabet, a table of literal codes, or a checksum over typed symbols. This ROM
has none:

* every top-level mode and each mode's setup/entry screen was walked (table-only
  pages such as Schedule/Standings/Statistics were sampled); none accepts text;
* the only key comparison tables are the link-input merge (`0x083C4884`) and
  the menu cursor handlers;
* the text DB has no `password`/`code`/`cheat` string;
* a pointer scan over every 4-byte ROM pointer whose target starts with ≥3
  key-like `u16` values produced 42 hits; the only real key array is
  `0x083C4884` (Up/Down/A/B, link merge). None is referenced by a validator.
* no `0x0120` or `0x0180` literal/immediate exists; the `R+Left`/`R+Down`
  sequence has nothing to compare against.

## 6. Tables

### 6.1 Text-DB IDs relevant to this engagement

| ID | Text | Where used |
|---:|---|---|
| 13 | `ABCDEFGHIJKLM` | alphabet run (no code use) |
| 14 | `NOPQRSTUVWXYZ` | alphabet run (no code use) |
| 15 | `TEST SCREEN` | **unreferenced** (dev label; never drawn) |
| 16 | `Style:` | HRD setup (shown; no ASCII copy exists) |
| 17 | `Stadium:` | HRD setup (shown; ASCII copy also exists) |
| 18 | `American League:` | HRD player select (shown; ASCII copy exists) |
| 19 | `HOME RUN DERBY^` | HRD title (shown; no ASCII copy exists) |
| 20 | `National League:` | HRD player select (shown; ASCII copy exists) |
| **161** | **`Tweak`** | **unreferenced** |
| **162** | **`All Your Baseball Are Belong To Us`** | **unreferenced** |
| **163** | **`Parameter`** | **unreferenced** |
| **164** | **`Value`** | **unreferenced** |
| 165 | `All Your Cards:` | trading-cards screen |
| 170/171 | `Connect` / `Disconnect` | cards / link |
| 202 | `You unlocked a new trading card!` | card unlock toast |
| 220 | `PRESS START BUTTON` | title |

All 26 text-by-ID setter call sites (`0x08035F7C`) were enumerated; their IDs
are `0x7C/0x7D`, `0x83/0x84`, `0xAA/0xAB`, `0xB2`, `0xD9`, `0x41`–`0x44`, and
the dynamic expressions `0x23+n`, `0x24+n`, `0x25+n`, `0x19+n`. None can
produce 161–164. A byte/word scan of all 61 layouts for those IDs also finds
nothing.

### 6.2 Key masks (GBA active-high)

| Button | Mask | Button | Mask |
|---|---:|---|---:|
| A | `0x001` | Right | `0x010` |
| B | `0x002` | Left | `0x020` |
| Select | `0x004` | Up | `0x040` |
| Start | `0x008` | Down | `0x080` |
| R | `0x100` | L | `0x200` |

The only table of these values in ROM is `0x083C4884` (`0040 0080 0001 0002`),
the link/multi-tap merge order.

### 6.3 Screen-table census

| Item | Count |
|---|---:|
| Screen name slots (`0x083C4564`) | 71 |
| Non-null handler slots (`0x083C46F4`) | 60 |
| Null handler slots | 11 (5,37,38,54,55,56,61,62,63,69,70) |
| Layout names with data in the directory | 61 |
| Layout names without data | 10 (37,38,54,55,56,61,62,63,69,70) |

The 61 extracted layouts were scanned for `tweak`, `param`, `test`: 0 hits.

### 6.4 Published-code verdicts

| Published item | Source | Verdict in this ROM |
|---|---|---|
| Cheat menu: press L at controller selection | GameFAQs GBA page (GC-labelled block) | Not implemented. No cheat text/state, no menu on L at any select screen. |
| Alternate uniforms: hold L+R | GameFAQs GBA page | Not implemented. Kit colours unchanged in-game and at team select. |
| Home runs (LH): R+Left, R+Down | GameFAQs GBA gameplay cheats | Not implemented. No `0x120`/`0x180` compare; entering it changes nothing. |
| Home runs (RH): R+Right, R+Down | GameFAQs GBA gameplay cheats | Not implemented. Same. |
| Hit the ball harder: Select in windup | GameFAQs GBA gameplay cheats | Real input, but it toggles the hit cursor display (`0x03002DBD`), not hit power. |
| Credit / hidden commentary: A during credits | GameFAQs GBA page | No visual/state effect; no “commentary” string or asset. Console-only claim. |

The archived GBA cheats page labels the first block **“Cheat Codes GC”**; those
two lines (cheat menu, alternate uniforms) are GameCube submissions carried on
the GBA page. The only GBA-specific list on that page is “Gameplay Cheats”.
Sources: `gamefaqs.gamespot.com/gba/553545-all-star-baseball-2003/cheats`
(Wayback `20251104183447`) and the GameCube FAQ `faqs/18270` (Wayback
`20190225140436`).

## 6b. Enumeration

### 6b.1 Password / passcode space

| Property | Value |
|---|---|
| Input screen | none (30+ screens walked, no text/keypad entry) |
| Alphabet | none for codes; TDB 13/14 is an alphabet run only |
| Length | n/a |
| Field widths | n/a |
| Checksum | none (no checksum routine over typed symbols found) |
| Reserved bits | n/a |
| Representable accepted values | **0** |

There is no validator to enumerate. A code system cannot be “small but
undocumented” here: the comparison path that would accept a value does not
exist. This is a structural negative, not a list that happened to be short.

### 6b.2 Button-sequence space

| Property | Value |
|---|---|
| Buttons observed by the game | 10 (`A,B,Select,Start,Right,Left,Up,Down,R,L`) |
| Sequence validator | none |
| Code table | none; `0x083C4884` is the link-input merge, not a cheat table |
| Progress counters | no cheat progress byte found; the only Select-triggered counter is `0x03002DBD` (display flag) |
| Accepted hidden sequences | **0** |

Tested and rejected (no effect): three title-screen sequences including the
Konami code and the Aggressive Inline GBA code; L at six select/pause screens;
L+R in-game; R+Left/R+Right+R+Down at bat; A during credits. The only
accepted input found is Select, which is a documented display toggle.

### 6b.3 Text-ID and screen space

| Space | Size | Result |
|---|---:|---|
| Text-DB IDs | 225 | 220 reachable/known; **4 dead** (161–164); id 15 not drawn |
| Text-by-ID call sites | 26 | none can reach 161–164 |
| Layout blobs | 61 | no cheat/test/tweak layout |
| Screen-table slots | 71 | 60 handlers; 11 null; none is a hidden menu |
| ASCII runs ≥4 | 69,904 | 0 password/passcode/cheat/secret/classic/menu strings |

Keyword classification over those runs: `password` 0, `passcode` 0, `cheat` 0,
`debug` 0, `secret` 0, `unlock` 0, `roster` 0, `classic` 0, `menu` 0,
`invalid` 0, `code` 1 (`Code Version: MakeLBN.inf v.%d`, a build-tool
string), `test` 6 (five engine/`MEM_validate` messages and the `!Game Testers`
credits header), `select` 4 (`Selected: %d`, `Selecting *next* batter`,
`fe_select.raw` twice). The printf-style gameplay debug logs
(`DIVE CATCH…`, `Forced offs…`, `Tagged out…`) are engine logging, not a menu.

The four dead strings are the closest thing to “hidden content”: they describe
a developer `Tweak` screen with `Parameter`/`Value` columns, but no code or
layout references them, so they cannot be reached in this build. No novel code
was minted because there is no encoder or validator; the accepted-code set is
empty.

### 6b.4 Bounds by rejection

| Rejected input | Expected if a system existed | Observed |
|---|---|---|
| L at Quick Game team select | cheat menu or list | none; banner animation only |
| L+R held in-game | alternate kit | none; pixels of both kits unchanged |
| R+Left,R+Down at bat | home run | no state change, no contact modification |
| R+Right,R+Down at bat | home run | same |
| A during credits | commentary | no visual/state change |
| `UDUDLRBR` at title | unlock/debug | no effect |
| `LLBBRRLR` at title | unlock/debug | no effect |
| Konami at title | hidden mode | no effect |

## 7. Validation evidence

**Observed (emulator screenshots / RAM reads)**

* All menus in §3 opened; the key ones are photographed (`evidence/01`–`19`).
* `0x03003ACC`/`0x03003AD0` hold the hardware key word; the per-player arrays
  `0x03000270/78/80` and `0x03000E84` were confirmed by holding A, B and Up in
  three identical savestates (values `1`, `2`, `0x40` at the same addresses).
* Select toggles `0x03002DBD` 1→0 (savestate diff) and the hatched contact
  triangle disappears (`evidence/17` vs `18`).
* The HRD setup/player-select screens show `Style:`, `Stadium:`,
  `American League:`, `National League:` (`evidence/07`, `08`). `Style:` and
  `HOME RUN DERBY` exist only in the UTF-16 TDB (no ASCII copy), so those
  records are proven reachable; the league labels also have ASCII copies.
* Trading cards and credits screens are reachable (`evidence/09`, `15`).

**Derived (instruction/data analysis)**

* TDB header/table layout and the 225 strings.
* FELIB hash function and directory (`mult=10`, 502 entries).
* 26 text-by-ID call sites; none reaches 161–164.
* Screen table 71 slots / 60 handlers / 11 null; 61 layout blobs.
* No combined `0x0120`/`0x0180` comparison constant; the link merge at `0x083C4884` is the
  only key array.
* Select’s handler at `0x08015A60` toggles `0x03002DBD`; readers at
  `0x08016C9A`/`0x0801CB60` draw/HUD-gate the hit cursor.

**Inferred**

* `TEST SCREEN` (15) and the `Tweak` block (161–164) are text left over from
  Acclaim’s developer build; a screen with those labels was removed before this
  GBA revision. The strings survive because the shared `.tdb` was not pruned.
* The published R+direction lines come from the console version’s
  location-guess control; the GBA build has no such cheat.

## 8. Unknowns

* The credits “hidden commentary” claim is audio-only. With
  `SDL_AUDIODRIVER=dummy` there is no audible output; no `commentary` string or
  commentary asset reference exists, so this is reported as a console-version
  claim rather than a GBA feature.
* The exact visual role of the second reader of `0x03002DBD`
  (`0x0801CB60`) was not isolated; it gates HUD visibility in the same cursor
  struct. This does not affect the cheat conclusion.
* Whether the removed `Tweak` screen existed in an earlier GBA prototype is
  unknown; it is not in this ROM’s code or layouts.

## 9. Tooling

* `mgba` 0.10.5 (`/usr/games/mgba`), `Xvfb :132`, `openbox`, `scrot`,
  ImageMagick, `xdotool`, `gdb-multiarch`, `arm-none-eabi-objdump`,
  Python 3 + Capstone.
* Header/hash scan: `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`.
* TDB / FELIB extraction (re-runnable):

```python
import struct
rom = open("All-Star Baseball 2003.gba","rb").read()
DIR = 0x4C4C0
count, mult = struct.unpack_from("<II", rom, DIR)
def h(name):
    v = 0
    for c in name.encode():
        if 0x41 <= c <= 0x5A: c += 0x20
        v = (v*mult + c) & 0xFFFFFFFF
    return v
def lookup(name):
    for i in range(count):
        hh, _, size, off = struct.unpack_from("<IIII", rom, DIR+8+i*16)
        if hh == h(name): return size, DIR+off
size, off = lookup("text\\baseball.tdb")
cnt = struct.unpack_from("<I", rom, off+4)[0]
for k in range(cnt):
    sid, o = struct.unpack_from("<HH", rom, off+0x14+4*k)
    p = off+0x14+cnt*4+o*2
    e = p
    while rom[e] or rom[e+1]: e += 2
    print(sid, rom[p:e].decode("utf-16le"))
```

* Savestate RAM reader: decompress the `gbAs` PNG chunk with `zlib`; IWRAM is at
  `0x19000`, EWRAM at `0x21000` (verified via the file-system pointer
  `0x0804C4C0` at IWRAM `0x03003870`).
* Evidence: `evidence/01_title.png` … `evidence/19_change_controls.png`.

**Legal note.** No ROM, extracted graphics, audio or copyrighted text is
redistributed here; only hashes, addresses, algorithms, short UI labels as
evidence, and the analyst’s own screenshots.
