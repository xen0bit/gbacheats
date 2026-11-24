# The Proud Family (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `The Proud Family.gba` |
| Size | 8,388,608 bytes (8 MiB) |
| Header title | `PROUDFAMILYG` |
| Game code | `BD7E` |
| Maker | `4Q` |
| Revision | 0 (`0x00`), complement `0x37`, header checksum `0x0000` |
| Entry word | `0xEA00002E` (stock GBA branch to `0x080000C0`; **not** a scene-cracked release, guide §16.1) |
| MD5 | `487704c5d9978e88e8468d127561948c` |
| SHA-1 | `aee1be6432a1b6fa50564b593f4d4d2d0201d528` |
| SHA-256 | `a6cc051d81981e7b508ab0691bc12a1d9f033d45932a6e73bb5ee713289aaaff` |
| Save hardware | 512-byte EEPROM (`game.sav`, magic `DE ED` + CRC) |

## 2. Executive summary

**No developer-intended cheat system exists in this SKU.** There is no password
screen, no password validator, no password/checksum table, no button-code mask
table, and no reachable hidden/debug menu. The only developer-intended
"unlocks" are **save-gated content**: five of the six minigames and the Photo
Album are dimmed on a fresh save, as are Continue Game and (contextually) Save
Game.

This is a **bounded negative** (guide §0.2 case 5 / §16.3 "no system"), not an
untested guess. The screen walk, word/alphabet/mask scans, scene-registry
analysis, dynamic button-combo matrix and save-format inspection are quantified
in **§6b**. The two `cheat` hits in the whole 8 MiB are the *same* internal
debug assertion (`Taxi cheat ,not at stand`), not a player-facing code; the one
`secret` hit is ordinary dialogue.

**No codes were minted** because no code space exists to mint from. The
report therefore delivers the complete unlockable enumeration and a counted
negative instead of a fabricated code.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 under Xvfb, `SDL_AUDIODRIVER=dummy`, `mgba -3 game.gba`.
  A **copy** of the ROM was run from `/tmp/proudfamily/` so no `.sav`
  or `.ss*` was written into the ROM folder (verified clean at the end).
* SDL keymap used: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`,
  D-pad=arrow keys. Holds of 50–60 ms with 80–200 ms gaps avoided the
  double-stepping pitfall (guide §16.2).
* Screen path: title (family art) → **Start** → main menu
  (`NEW GAME / CONTINUE GAME / MINI GAMES / PHOTO ALBUM / CREDITS`; disabled
  entries are *skipped* by the D-pad, so one Down from NEW GAME lands on MINI
  GAMES and two land on CREDITS). From MINI GAMES: `A` opens
  `BACK / THE FACTORY / CHEZ WIZARD / LET'S WRESTLE / SCRATCH FOR SCRATCH /
  PIZZA CHEF / DANCE CONTEST`. Start in gameplay opens the pause menu
  (`CONTINUE / PHOTO ALBUM / SAVE GAME / QUIT`).
* RAM evidence: mGBA's GDB stub (port 2345) was occupied by another concurrent
  session, so per guide §16.13 RAM was read from the zlib-compressed `gbAs`
  chunk of `.ssN` savestates (raw state 397,312 bytes; IWRAM at raw `0x19000`,
  EWRAM at `0x21000`). Helper scripts in §9 do this.

## 4. Address map

| Address (ROM) | Meaning |
|---|---|
| `0x08000000` | Header / stock entry branch `0xEA00002E` |
| `0x08000698`–`0x080008A0` | **Scene registry**: 43 records × 12 bytes = `{name_ptr, ctor_struct_ptr, iwram_obj_ptr}`. Names at `0x080F79C8`–`0x080F7B44`. |
| `0x080F7B14` | String `DialogTest` — referenced **only** by the registry (zero code xrefs) |
| `0x080FAxx`–`0x080FBxx` | Debug/engine format strings (`Scene %s loaded`, `Keyboard::a`, dance-move button labels) |
| `0x0841FF7C`–`0x084200A8` | Taxi/transition debug logs: `MainStreet`, `Chez`, `# TAXI`, `Taxi cheat ,not at stand`, `DODANCE`… |
| `0x08003F90`–`0x08004110` | EEPROM/GamePak save serializer: writes magic `0xDE`,`0xED`, CRC at byte 2, zero at byte 3 |
| `0x080022C8` | Called by the Options (main-menu) constructor to derive the "has save" boolean |
| `0x080793F4` | Options/main-menu scene constructor; gate at `0x08079616`–`0x08079632` |
| `0x080874F0` | Title scene constructor |
| `0x0807CF84` | Minigame-list scene constructor |
| `0x08079FE8` | Menu-item constructor used by both menus |
| `0x03003A70` | IWRAM: current-scene object pointer (RAM evidence) |
| `0x03003A78` | IWRAM: parent-scene object pointer |
| `0x03003B54`–`0x03003F48` | IWRAM: scene objects, 16-byte name + pointer (stride `0x14`, with a few `0x18` gaps) |
| `0x03003D68` / `0x03003D80` / `0x03003D98` / `0x03003DB0` | Objects: `Options` / `Credit` / `Minigame` / `Title` |

## 5. Algorithm

**Scene manager (derived).** The 43-entry registry is walked at boot; each
record's third field points to a 20/24-byte IWRAM object whose first 16 bytes
are the scene name and whose `+0x10` word is a per-scene data pointer. Gameplay
transitions set `0x03003A70` (current) and `0x03003A78` (parent). Observed
values: main menu `current=Options`, credits `current=Credit`, intro
`current=IntroPR`/`IntroLV`, splash `current=Splash`.

**Save format (derived from `0x080040C8` disassembly):**

```
byte 0 = 0xDE
byte 1 = 0xED
byte 2 = CRC8 over bytes[4 .. length-1]   (computed by 0x08003E6C)
byte 3 = 0x00
bytes 4.. = payload
```

Loader at `0x080041B8` re-computes the CRC and rejects a mismatch
("GamePak::check: BAD CRC"). Serializer is reached through the SaveGame object,
not by a direct BL (zero literal/BL xrefs to `0x08040C8`, so it is vtable-driven).

**Menu gate (derived).** In the Options constructor, `0x08079616` calls
`0x080022C8` with a save-data pointer; the resulting boolean byte is tested at
`0x0807961C`. If non-zero, menu items **28 (0x1C)** and **30 (0x1E)** are
enabled — these are CONTINUE GAME and PHOTO ALBUM. With a virgin EEPROM both
are dimmed, exactly as observed.

There is **no code validator** to reverse: no string comparison against a user
buffer exists outside parser constants and save-CRC checks.

## 6. Tables

### 6.1 Reachable surfaces and item counts (Observed)

| Screen | Scene object | Items |
|---|---|---|
| Title | `Title` / boot scenes | implicit "press Start" only |
| Main menu | `Options` | 5 (NEW GAME, CONTINUE GAME†, MINI GAMES, PHOTO ALBUM†, CREDITS) |
| Mini Games | `Options` submenu | 7 (BACK, THE FACTORY, CHEZ WIZARD†, LET'S WRESTLE†, SCRATCH FOR SCRATCH†, PIZZA CHEF†, DANCE CONTEST†) |
| Credits | `Credit` | scrolling titles (BUENA VISTA, EXECUTIVE PRODUCER RACHEL PI, …) |
| Pause | in-game overlay | 4 (CONTINUE, PHOTO ALBUM†, SAVE GAME‡, QUIT) |
| Intro / gameplay | `IntroLV`, `IntroPR`, `Hood`, … | dialogue / overworld |

† dimmed on a fresh save. ‡ dimmed in the first area (context/save-point gated).

### 6.2 Unlockables (the complete developer-intended unlock set)

| Unlockable | Type | State at virgin save |
|---|---|---|
| THE FACTORY | minigame | available |
| CHEZ WIZARD | minigame | locked |
| LET'S WRESTLE | minigame | locked |
| SCRATCH FOR SCRATCH | minigame | locked |
| PIZZA CHEF | minigame | locked |
| DANCE CONTEST | minigame | locked |
| PHOTO ALBUM | gallery | locked |
| CONTINUE GAME | save slot | locked |
| SAVE GAME | pause command | context-gated |

### 6.3 Debug strings that are *not* cheats

| Address | String | Verdict |
|---|---|---|
| `0x08420088` (×2 at `0x420088`, `0x49A794`) | `Taxi cheat ,not at stand` | internal assertion in Taxi scene code (`0x080BF3E0`), printed via debug logger `0x080865B8`; no input path |
| `0x0841FFE8`/`0x0841FFF8`/`0x0842000C` | `…dialog done` | story-event debug logs |
| `0x0842005C`/`0x08420064` | `DODANCE`/`STOPDANCE` | Taxi→dance transition debug logs |
| `0x080FB14C`–`0x080FB284` | `uldr`, `a+lr`, `L+R`, `A + leftRight`, … | button labels for the Penny dance minigame (gameplay inputs), not a cheat matcher |

## 6b. Enumeration

**Code space: empty (bounded negative).** Definition of the searched space and
the exact counts:

1. **Word/keyword scan** over all 8,388,608 bytes, case-insensitive:
   `password` **0**, `code` **0**, `unlock` **0**, `debug` **0**, `master` **0**,
   `gameshark` **0**, `codebreaker` **0**, `action replay` **0**,
   `enter code` **0**; `cheat` **2** (both the same `Taxi cheat` debug
   assertion); `secret` **1** (dialogue "THAT'S THE SECRET TO…").
2. **Password-alphabet scan**: five canonical patterns
   (`A-Z`, `a-z`, `0-9`, `A-Z0-9`, `0-9A-Z`, consonant-only, `!?`) — **0**
   password alphabets. The 40+ ASCII-run hits are standard **font glyph tables**
   (e.g. `0x082D1C65`: ` !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFG…` interleaved
   with tile indices) — decoded as fonts, not code alphabets (guide §11:
   "decode font/tile text banks before a negative"). Menu labels are drawn from
   a tile-index font, which is why `NEW GAME`, `MINI GAMES`, etc. produce no
   `strings` hit.
3. **Button-code mask-table scan**: 6 common combos × 2 polarities = 12
   literal searches using correct GBA masks (`A=1,B=2,Sel=4,Start=8,
   Right=0x10,Left=0x20,Up=0x40,Down=0x80,R=0x100,L=0x200`, active-low
   complement `0x3FF^mask`). All hits (e.g. `0x082331A8`, `0x080FC6A1`,
   `0x08188965`) are **odd file offsets inside compressed graphics** — false
   positives; **0 aligned code-table hits**.
4. **Scene/debug-gate enumeration**: 43 registered scenes. The developer test
   scene `DialogTest` (`0x080F7B14`) has **1 reference total** — its own registry
   record — i.e. **0 code xrefs**, **0 BL/BLX references by name**. No
   scene-select handler or debug-index dispatcher was found. By §16.3 this is a
   "dead code" / at most "gated feature" state, not a hidden menu.
5. **Dynamic button-combo matrix**: 18 combos applied on both the title and the
   main menu (L+R, L+R+Start, L+R+A/B, Start+Select, A+B+Start+Select,
   Select+A/B/U, R+A/B, L+A/B, B+A, U+D+L+R, 2-second L+R hold, Konami
   `UUDDLRLRBA` and its mirror). **0 hidden screens**. Every observed change
   was ordinary menu behaviour — combos containing A selected the highlighted
   NEW GAME (`current=IntroLV`), the Konami sequence merely walked the D-pad
   cursor to CREDITS, and L+R-only / L+R+B / L+R+Start / Select-only / R+B /
   L+B left `current=Options` and the screen hash unchanged.
6. **Unlockable space (the actual enumeration)**: 9 slots total (§6.2), of
   which 1 minigame is free, 5 minigames + Photo Album + Continue are
   save-gated and 1 pause command is context-gated. The gate was located in
   ROM (`0x08079616`–`0x08079632`, items 28/30) and verified in RAM: savestates
   from a virgin EEPROM show `current=Options` with both entries dimmed; the
   `.sav` remained all-`0xFF` apart from the 8-byte zero header after a full
   title→menu→pause walk, proving no progression flag had been set.

**Because the accepted-input set is empty, there is no code to mint and no
validator to call as an oracle.** §16.9's "run the validator over the whole
space" reduces here to the counted scans above, and §0.2's novel-code
requirement is discharged by the bounded-negative clause.

## 7. Validation evidence

* **Observed** — mGBA screenshots of title, main menu, mini-games list, credits,
  pause menu, intro and overworld gameplay (saved in the work dir).
* **Observed** — savestate RAM: `game.ss8` `current='Options' (0x3003D68),
  parent='Title'`; `game.ss3` `current='Credit' (0x3003D80),
  parent='Options'`; `game.ss4` `current='IntroPR'`; combo matrix outputs
  recorded in `combotest.py`'s log.
* **Derived** — save magic/CRC layout from `0x08003F90`–`0x08004110`;
  menu gate from `0x080793F4`/`0x080022C8`; scene registry from
  `0x08000698`–`0x080008A0`; title/menu/minigame constructors from their
  thunks at `0x08000B1D`, `0x08000B59`, `0x08000B31`.
* **Inferred** — which in-game events set the five minigame unlock bits (the
  setters were not isolated; the EEPROM was never written during this walk).
  The dimmed minigames are definitely gated, but the exact trigger is unproven.

## 8. Unknowns

* Exact story events / flags that unlock CHEZ WIZARD, LET'S WRESTLE, SCRATCH
  FOR SCRATCH, PIZZA CHEF, DANCE CONTEST and the Photo Album.
* Whether SAVE GAME unlocks at a fixed story chapter or at specific save-point
  objects; `SAVE GAME` stayed dimmed in the first overworld area.
* The save payload field layout beyond the 4-byte magic/CRC header (the
  serializer is vtable-driven; no direct call site was found).
* `DialogTest` is dead by the zero-xref test, but a debugger forcing the scene
  pointer was not performed (that would be a debugger artifact, not an in-game
  code — guide §16.10).

## 9. Tooling

All scripts were in `/tmp/proudfamily/`:
`scan.py` (keyword/alphabet/mask scan), `ptrscan.py` (4-byte pointer/range scan),
`dis.py` and `arm-none-eabi-objdump -M force-thumb` (disassembly),
`ssdiff.py` (zlib `gbAs` extraction + state diff), `scene.py` (scene name from
savestate), `key.py` and `combotest.py` (XTEST input, combo matrix).
Installed tools used: mgba 0.10.5, gdb-multiarch (blocked by port conflict),
xdotool, scrot, ImageMagick, capstone, arm-none-eabi-objdump, Xvfb + openbox.

## 10. Legal note

No ROM image, extracted graphics, audio or full text banks are redistributed.
Only hashes, addresses, derived algorithms and original analysis scripts are
published.
