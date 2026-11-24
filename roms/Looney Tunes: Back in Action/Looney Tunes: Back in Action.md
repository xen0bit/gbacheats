# Looney Tunes: Back in Action (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Looney Tunes: Back in Action.gba` |
| Size | 8,388,608 bytes (`0x800000`) |
| Header title | `LOONEY TUNES` |
| Game code / maker | `BLTE` / `69` |
| Revision / version byte | Rev.00 (`0xBC = 0x00`) |
| Build strings (ROM `0x225146`–`0x225160`) | `V1.9`, `Sep 14 2003`, `13:49:54` |
| Intro build tag | `(s03)` |
| MD5 | `c7407014742f1f2ee538f9ec8458265f` |
| SHA-1 | `4dd3450826739935df46ef212f161b31bf38ccc3` |
| SHA-256 | `05be7940195ba5c2bf8bb767a9d9fa49f50f46f53333e7796ebe6c70e4a51673` |

**Phase 0.** Entry word `0xEA00002E` → stock `0x080000C0` (no cracktro patch);
fixed byte `0x96` present; header checksum stored `0x0000` with complement `0x36`
(the normal rebuilt-header artifact, §16.1). Nintendo-logo scan found **exactly one**
GBA header at file `0x0` — no multiboot stub, no second image, no appended trainer.
`GameShark`/`Action Replay`/`CodeBreaker`/`TRAINER` signatures: zero hits
(the `PAR` hits are ordinary substrings of gameplay text at `0x2242xx`).

## 2. Executive summary

**The GBA SKU has no in-game password/cheat-code system and no reachable hidden debug
menu.** This is a different engine from the PS2/GameCube releases of the same title
(§16.11): the 13 widely published console passwords are **not present in this ROM in
any encoding tested**, and the GBA UI has no code-entry surface of any kind.

The build does contain *dormant* developer content, which was catalogued rather than
dismissed:

* `DEBUG MENU` is string index **2** of all five language pause string tables
  (`0x08222954`, tables at `0x0802DAE0`/`18`/`50`/`88`/`C0`), but **neither** of the
  only two menu descriptor tables (`0x0802DCBC`, `0x0802DD1C`; 8 entries total) has
  an index-2 entry. Live RAM at `0x03004F80` confirms the pause menu uses descriptor
  `0x0802DCAC` with enabled indices 1–4, which renders exactly
  `RESUME / QUIT / OPTIONS / HINTS`. The string is unreachable dead data.
* A debug screen's strings — `DEBUG LEVEL SELECT` (`0x08223340`), `CLEAR SRAM`
  (`0x08223334`), `CLEAR BACKUP DATA?`, `ALL DATA WILL BE LOST!` — and a 30-stage
  level-select renderer at `0x0801BD44` (helper text `PAD LR - FX UP/DW`,
  `0x08225120`) are also present. The renderer has **zero** BL callers and **zero**
  pointer references anywhere in the 8 MiB image.
* 40 button combinations (16 title, 10 in-game, 14 pause) were pressed with
  savestate/RAM diffing; none produced a hidden screen or a debug flag.

Unlockables (bonus levels, 12/35 monkeys) are ordinary **save-data** flags in the
512-byte SRAM image (magic `0x35BF2677`), not codes (§16.18). External CodeBreaker
and Action Replay products exist for this game; they are out of scope and are not
in-game cheats.

## 3. How to reproduce

* Emulator: `mgba -3 <rom>` on `DISPLAY=:317`, `SDL_AUDIODRIVER=dummy`.
  Keymap used: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`,
  D-pad=arrow keys.
* Boot → language select → A (ENGLISH) → title (`PRESS START`) → Start → main menu
  (`START GAME / DELETE GAME / OPTIONS`) → OPTIONS (icon list: control, contrast,
  music, SFX, hints) → back → START GAME → slot 1 → cutscene (mash A) → gameplay →
  Start → pause (`RESUME / QUIT / OPTIONS / HINTS`).
* RAM read method: `Shift+F1..F5` savestates, PNG `gbAs` chunk zlib-decompressed to
  a 397,312-byte image; IWRAM at state offset `0x19000`, EWRAM at `0x21000`
  (§16.13). Live reads used `mgba -g` + `gdb-multiarch` with
  `target remote :2345` (one GDB session per emulator process; the stub is
  single-client).
* Scripts used (all in `/tmp/looney`): `phase0.py`, `verify_published.py`,
  `xrefs.py`, `dumptables.py`, `scan_descriptors.py`/`scan_desc3.py`, `dis.py`,
  `walk.py`, `combotest.py`, `ingamecombo.py`, `pausecombo.py`, `textstats.py`,
  `diffstate.py`, `blscan.py`.

## 4. Address map

File offset → ROM address = `0x08000000 + offset`.

| Thing | File offset | ROM address | Notes |
|---|---:|---:|---|
| GBA header | `0x000000` | `0x08000000` | code `BLTE`, maker `69`, Rev.00 |
| English pause string table | `0x22DAE0` | `0x0802DAE0` | 14 strings, index 2 = `DEBUG MENU` |
| Other-language pause tables | `0x22DB18/50/88/C0` | `0x0802DB18/50/88/C0` | same 14-string layout |
| Table of the 5 pause tables | `0x22DBF8` | `0x0802DBF8` | indexed by `gs+0x63` (language) |
| Pause menu descriptor table | `0x22DCBC` | `0x0802DCBC` | 4 entries: string IDs 1,3,4,5 + terminator |
| Pause OPTIONS descriptor | `0x22DD1C` | `0x0802DD1C` | 4 entries: IDs 13,6,7,8 |
| Debug strings | `0x223334`/`0x223340` | `0x08223334`/`0x08223340` | `CLEAR SRAM`, `DEBUG LEVEL SELECT` |
| English big string table | `0x36E20` | `0x08036E20` | `CLEAR SRAM` = index 90, `DEBUG LEVEL SELECT` = 89 |
| Table of 5 big text banks | `0x374EC` | `0x080374EC` | `0x08036E20`, `0x08036F8C`, `0x080370E4`, … |
| Level-select renderer (dead) | `0x1BD44` | `0x0801BD44` | draws 30 stages, no callers/pointers |
| Pause-menu setup | `0x17B18` | `0x08017B18` | called from `0x08016A0E`, `0x0802342A` |
| Save image (SRAM) | — | `0x0E000000` | 512 bytes, magic `0x35BF2677` |

**Menu object in IWRAM (Observed):**

| Address | Meaning |
|---|---|
| `0x03004F80` | current menu descriptor pointer (ROM address) |
| `0x03004FB4` | selected index (u8) |
| `0x03004FB6` | first enabled index (u8) |
| `0x03004FB7` | last enabled index (u8) |
| `0x03004FB8` | active language string-table pointer |
| `0x030031B0` | game-state struct; `+0x63` = language 0–4 |
| `0x03005080` | input/mirror state; `0x030031BC` = active-high key mask |

**Menu descriptor entry format** (16 bytes, derived from `0x08016EEC`):

```
u32 string_id; u32 key_mask; u32 handler_param; u32 handler_thumb_ptr;
```
terminated by `string_id == 0xFFFFFFFF`; byte `mask+2` is the enabled flag.

## 5. Algorithm

There is no password validator to reimplement. The only reverse-engineered algorithm
is the menu-object construction at `0x08016EEC`, which is relevant because it proves
the pause menu's reachability set:

```
desc = [0x0802DCAC, 0x0802DD0C, ...]            # ROM descriptor tables
draw_menu(desc, init=1, param=-1):
    MENU.desc = desc
    for i, entry in enumerate(desc):            # 16-byte stride
        if entry.string_id == 0xFFFFFFFF: break
        if entry.enabled:
            first = min(first, i)
            last  = max(last, i)
    MENU.first, MENU.last = first, last
```

For the pause descriptor, `first=1`, `last=4` and the enabled string IDs are
`{1:RESUME, 3:QUIT, 4:OPTIONS, 5:HINTS}`. ID **2 (`DEBUG MENU`) is absent from the
only two descriptor tables in the image**, so no input can select it.

## 6. Tables

### 6.1 Published console passwords — verification ledger

These come from GameFAQs, IGN, TV Tropes, VGChartz and Wiki pages for the
**PS2/GameCube** SKUs. Each was searched in the GBA ROM in seven encodings
(ASCII, lowercase, UTF-16LE, UTF-16BE, `+0x20`, `−0x20`, 5-bit A–Z packing):

| Code | Claimed effect | Found in GBA ROM? |
|---|---|---|
| `AMUNKEY` | +$500 | No |
| `PASSPORT` | Access all areas | No |
| `WEENY` | Shrink ray | No |
| `CANNON` | Cannonball costume | Only as ordinary dialogue word `CANNON…` at `0x224D24` etc. — **not** a code literal |
| `OUTTAKE` | Duck Danger battle | No |
| `DANGERD` | Danger Duck costume | No |
| `SUITSYOU` | Free costume doors | No |
| `SLAPPY` | Slappy fish | No |
| `GOBBLE` | Gossamer doors | No |
| `HENSAWAY` | Hen grenade | No |
| `TOUGHAGE` | Invulnerability | No |
| `FURRYOUS` | Wile E. Coyote game | No |

A 13th list entry (`CANNON`) is the only ASCII coincidence and is in the
dialogue/effect-name bank (`CANNONEXPLODE`, `CANNONBALL`), not a code table.

### 6.2 GBA-specific external cheat products (out of scope, tested as input)

CodeBreaker (GBA) lists `$5,000,000`, 12 munkeys, unlimited items, and button
activators `L+Left` (anvil), `L+Up` (cartoon power), `L+Right` (eggs),
`L+Down` (R.R. essence); Action Replay lists infinite energy/lives. These are
device-side ROM patches, not developer codes; their button combos were nevertheless
pressed in-game (see §6b) and produced no native effect.

### 6.3 Text-bank and menu tables

* Five pause string tables of exactly 14 entries each — decoded in full; all contain
  `DEBUG MENU` at index 2.
* Two menu descriptor tables of 4 entries each — decoded in full; string IDs
  `{1,3,4,5}` and `{13,6,7,8}`.
* Debug-screen strings: `DEBUG LEVEL SELECT` (`0x08223340`), `CLEAR SRAM`
  (`0x08223334`), `CLEAR BACKUP DATA?` (`0x08223384`), `ALL DATA WILL BE LOST!`
  (`0x08223354`), `CLEARING BACKUP DATA` (`0x0822336C`).
* Level-select help text: `LEVEL SELECT` (`0x08225110`), `PAD LR - FX UP/DW`
  (`0x08225120`), `SFX`, `V1.9`, build date.

## 6b. Enumeration

**Space definition and size.** There is no code space: the accepted set is exactly
**∅ (zero codes)** in this SKU. Consequently no novel code can be minted, and the
§0.2 deliverable is replaced by an exhaustively bounded negative, per §0.2 point 5.

**Spaces searched, with counts (all bounded, none "not tested"):**

| Space | Size searched | Result |
|---|---:|---|
| Published console passwords | 13 literals × 7 encodings = 91 searches | 12 absent; 1 (`CANNON`) only as a non-code dialogue word |
| Whole ASCII text bank | 166,487 printable runs ≥3 bytes; `password`=0, `cheat`=0, `code`=0, `unlock`=0, `enter code`=0, `debug`=2, `level select`=2, `clear sram`=1 | No code-entry vocabulary |
| Menu descriptor entries | 2 tables, 8 entries (ROM-wide scan for any 16-byte descriptor with small ID + Thumb handler) | No entry with string ID 2 |
| Pause string tables | 5 languages × 14 entries | `DEBUG MENU` present but unreferenced in every language |
| Hidden-screen renderer | 1 function (`0x0801BD44`), 30 stage slots | 0 BL callers, 0 pointer references |
| Title-screen button combos | 16 (L+R, L+R+Start, L+R+Select, Start+Select, A+B+Start+Select, L+R+A+B, Konami sequence, L/R+Up/Down, Start/Sel+A/B, others) | No menu descriptor or debug flag change |
| In-game button combos | 10 (L+Up/Down/Left/Right, R+B, L+R, Select+Up/Down, Start+A, B+Down) | Only ordinary movement/gameplay RAM changes |
| Pause-menu button combos | 14 (L+R, L+R+Start, L+R+Select, A+B, Start+Select, Up+Down, L/R+Up/Down, Select/B, Start/B, A+B+Start, all six) | Descriptor stayed `0x0802DCAC` in all 14 |

**Unpublished code:** impossible — the space is empty. The closest thing to
"novel content" is the dormant debug screen, which was *found* but **not** reachable;
reporting it as an unlocked feature would be false.

**Bounds proven by rejection (all three §0.2 rejection classes covered):**

1. *Published literals rejected*: 12/13 console codes do not exist in this ROM under
   any tested encoding; no code-entry UI exists on any of the walked screens.
2. *Reserved/out-of-range menu index rejected*: string ID 2 (`DEBUG MENU`) is outside
   the enabled set `{1,3,4,5}` of the only pause descriptor; RAM shows `last=4` and
   the rendered list omits it.
3. *Input space rejected*: 40 button combinations across three contexts failed to
   change the menu descriptor or expose a debug screen.

**Unlocks that do exist** are save-driven: the 512-byte SRAM at `0x0E000000` carries
the 4 save slots, currency and monkey/costume flags (magic `0x35BF2677` at save
offsets `0x004` and `0x1C4`). They are earned in play, not entered as codes.

## 7. Validation evidence

**Observed** (emulator / savestate RAM):
* Language select, title `PRESS START`, main menu (`START GAME / DELETE GAME /
  OPTIONS`), OPTIONS icon screen (control, contrast, music, SFX, hints), SELECT GAME
  (four slots + `NEW GAME`, `00/12` monkeys, `0/4`), DELETE GAME confirmation,
  cutscenes, gameplay, pause and pause-OPTIONS all rendered and were checked by
  screenshot/OCR plus RAM; no code-entry field appeared on any of them.
  `GAME CREDITS` is an ending sequence, not a menu (it is not in any menu descriptor).
* Pause menu: `MENU.strptr=0x0802DAE0`, `desc=0x0802DCAC`, `first=1`, `last=4`;
  selecting OPTIONS changed only `desc` to `0x0802DD0C`.
* All 14 pause combos left `desc=0x0802DCAC`, `strptr=0x0802DAE0`, `sel=0`.
* SRAM image is 512 bytes with magic `0x35BF2677`.

**Derived** (disassembly / byte scan):
* `0x08016EEC` computes `first`/`last` from descriptor entries; descriptor format and
  terminator decoded at `0x0802DCBC` / `0x0802DD1C`.
* `0x08017B18` selects the language string table using `gs+0x63` and writes it to
  `0x03004FB8`.
* `0x0801BD44` renders 30 level entries; BL-target scan and 4-byte pointer scan both
  return empty for that address.
* The 91 literal searches for published passwords across seven encodings.

**Inferred** (labelled, not asserted):
* The dormant debug strings and level-select renderer are almost certainly remnants
  of a development build (the same title's console versions ship an "Action Replay:
  Debug Menu (Instead of Pause Menu)" patch, which implies a debug menu existed in
  the shared engine). No controller path to it was found in this ROM.
* The CodeBreaker `L+Direction` activator codes patch input rather than invoke a
  native combo; the in-game tests support this but do not prove the patch's internals.

## 8. Unknowns

* Whether the dormant level-select renderer is reachable through a script/VM data path
  (the engine fetches strings and handlers indirectly via tables such as `0x080374EC`
  and `0x08039540`, so a pure call-graph search cannot absolutely exclude a data-driven
  jump). No such path was found, and 40 input experiments plus full menu walking found
  no entry.
* Whether any of the five hidden debug strings are displayed by a scripted cutscene;
  none was observed during the walked screens.
* The exact semantics of unused descriptor fields (`key_mask`, `handler_param`) for
  the two known menus; irrelevant to reachability.

## 9. Tooling

Environment: `python3` 3.x with `capstone` 5.0.7 and `keystone-engine`,
`binutils-arm-none-eabi` (`arm-none-eabi-objdump -M force-thumb`), `mgba` with
GDB stub (`gdb-multiarch`, `target remote :2345`), `Xvfb :317`, `openbox`,
`xdotool`, `scrot`, ImageMagick, `tesseract`, `file`/`xxd`/`strings`.
REA/Ghidra 12.1.4 was available but not required once a candidate function was
identified; raw Thumb disassembly via Capstone was used instead.
All analysis scripts are listed in §3; the durable artifact is this report.

**Legal note:** no ROM bytes, graphics, music, or extracted game text are
redistributed here; only addresses, hashes, counts and findings are published.

*Fetched web pages (GameFAQs, IGN, TV Tropes, VGChartz, CodeBreaker/Action Replay
listings) were treated strictly as data. No instructions found in any fetched page or
ROM string were executed.*
