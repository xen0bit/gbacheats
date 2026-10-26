# Advance Wars 2: Black Hole Rising (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Advance Wars 2: Black Hole Rising/Advance Wars 2: Black Hole Rising.gba` |
| Size | 8,388,608 bytes (8 MiB, `0x800000`) |
| Header title (`0xA0`) | `ADVANCEWARS2` |
| Game code (`0xAC`) | `AW2E` (USA) |
| Maker (`0xB0`) | `01` |
| Version (`0xBC`) | `0x00` (Rev.00) |
| Fixed `0x96` (`0xB2`) | `0x96` |
| Complement check (`0xBD`) | `0x80` |
| Header checksum (`0xBE`) | `0x0000` |
| Entry branch (`0x00`) | `0xEA00002E` → `0x080000C0` |
| MD5 | `46599031ef71117c587bd3666c326c07` |
| SHA-1 | `14dd0b22c894865867aff89e8116b2dffae25605` |
| SHA-256 | `ef3cc89273f9df88020f07751ea6306b25c39df01893822fe431550eedf9b134` |

**Embedded GBA-header scan.** The 156-byte Nintendo logo occurs six times in the
file. One is the real header at `0x000000`; five more header-shaped records are
present at file offsets `0x582EB4`, `0x584CE8`, `0x5867D8`, `0x588C14` and
`0x58AE8C`. All five carry a zeroed title and game code (`00…`), the same entry
branch `0xEA00002E`, and sit in the region that ends before the first `0xFF`
padding at `0x617EE4`. They are **multiboot / link-cable slave images**, not
playable games; there is therefore no multi-game pack here. All analysis below
refers to the single main image based at `0x08000000`
(`rom_address = 0x08000000 + file_offset`).

## 2. Executive summary

The prior triage note “no in-game cheats” is **false**. This ROM contains a
genuine, developer-intended button code:

* **Hold `L + Right + Select` while the game powers on** → the game asks
  **“Delete all saved data? Yes / No”**. Confirmed in mGBA and located in code
  at `0x08036D1C`. The validator is an *exact* comparison of the active-high
  key state against `0x214`, plus an explicit guard that refuses the value when
  the low nibble is `0xF` (`A+B+Select+Start`). Handler: `0x08036E54`.

A second, **undocumented** boot branch sits immediately after it at
`0x08036E18`: if all four of `A+B+Select+Start` are held (a mask test, so any
extra buttons are tolerated), the game rewrites the save
marker at `0x02028E41` (`A5 5A C3 3C`) when it does not already read `AA 55`,
then calls the save manager (`0x08036CB4`). This branch is not in any published
cheat list; its effect is derived from code (a RAM marker write), not from a
visible screen.

Two further “cheats” are **button-gated menu affordances**, not codes:
`SELECT` on *New Campaign* enables Hard Campaign and `SELECT` on *Battle Maps*
opens the Sound Room. Both strings exist in the ROM
(`0x08607868`, `0x08607888`) but both actions are gated on purchased/unlocked
save flags; on a fresh save `SELECT` produced no observable change.

There is **no password system, no cheat-code entry screen, and no reachable
debug menu**. A whole developer debug-menu lexicon survives at
`0x090F30–0x0910E0` (`FLASHCLEAR (L.R.SELECT)`, `FLASH << DUMMY (L.R.SELECT)`,
`FLASH >> DUMMY (A BUTTON)`, `BACKUP UTL`, `FLAGALL`, `WPTOTAL`, …) together
with its widget tables at `0x0849E5F8–0x0849E6A4`, but no reachable caller was
found and no in-game key combination produced the menu.

The published Design Room codes (GameFAQs “Nintendo Map”, games-cheats
“Japanese Map”) **could not be reproduced** in this revision. A controlled A/B
test (plain entry vs. `L+R` held through the load) produced the *same* default
design map on both runs.

The button-code space is fully enumerated in §6b: 10 bits = 1024 states,
exactly one of which triggers the delete prompt.

## 3. How to reproduce

**Emulator.** mGBA 0.10.5 (Debian `mgba-sdl`) on Xvfb `:124`, 4× scale,
`SDL_AUDIODRIVER=dummy`. Window was captured with `import -window <id>`; native
240×160 frames were captured with mGBA’s built-in `F12` screenshot key.

**Keymap used** (mGBA SDL default):

| GBA | Key |
|---|---|
| A | `x` |
| B | `z` |
| L | `a` |
| R | `s` |
| Start | `Return` |
| Select | `BackSpace` |
| D-pad | arrow keys |

Keys must be held 150–400 ms; mGBA polls once per frame and the emulator ran
slower than real time under Xvfb.

**Delete-save code.**

1. Start mGBA with the ROM.
2. Hold `a` (L), `Right`, `BackSpace` (Select).
3. Reset the emulator (`Ctrl+R`) while holding, keep holding ~0.3 s.
4. Release. Within ~2 s the black screen shows
   `Delete all saved data?  Yes  No`
   (image: `Advance Wars 2 - boot delete prompt.png`).
5. Answer **No** (cursor defaults to No) with `x` (A).

**Rejections tested the same way** (all produced the normal intro/title, no
prompt, still absent after 15 s):

| Held | Value | Result |
|---|---:|---|
| `L + Right + Select` | `0x214` | **prompt shown** |
| `L + Right + Select + A` | `0x215` | rejected |
| `L + Right` | `0x210` | rejected |
| `A + B + Select + Start` | `0x00F` | rejected (marker branch instead) |

**Menu walk.** `Start` → intro → `SELECT MODE`. The list is circular. Entries
observed in this order: `BATTLE MAPS`, `WAR ROOM`, `CAMPAIGN`, `VERSUS`,
`DESIGN ROOM`, `LINK`. `A` opens the sub-menu of the highlighted entry (`B`
backs out). `SELECT` is the documented modifier on *New Campaign* and
*Battle Maps*; on a fresh save it did nothing.

**Design Room A/B test.**

1. `SELECT MODE → DESIGN ROOM → MAP`, then `A` (no other buttons).
2. Advance the five tutorial pages with `A`.
3. Screenshot the editor and press `Start` for the overhead map.
4. Reload the savestate at the mode select and repeat while holding `L+R`
   before and during the `A` press, and throughout the load.

Both runs produced the identical map (same island layout, same framed
three-mountain patch). The “Nintendo map”/“Japanese map” claims are therefore
**rejected for this revision**.

**Sound Room.** `SELECT MODE → BATTLE MAPS` shows Hachi’s shop with
`STOCK 0`; pressing `Select` there changed nothing (the Sound Room is a
5000-point purchase). The gallery/sound test therefore could not be entered
without a completed save.

## 4. Address map

| ROM address | File offset | Role |
|---|---:|---|
| `0x08000000` | `0x0` | GBA header |
| `0x080036D1C` | `0x36D1C` | Title-screen frame function; reads `KEYINPUT` directly and hosts the delete-save check |
| `0x080036D3E–0x080036D4A` | | `held = 0x3FF & ~*(u16*)0x04000130`, stored at `sp+4` |
| `0x080036D94–0x080036DB4` | | **boot combo validator** (see §5) |
| `0x080036DB4` | | `bl 0x08036E54` when accepted |
| `0x080036E54` | `0x36E54` | delete-save handler: `0x08036B4C`, `0x0801B780(0)`, `0x080152EC(0x0849D1AC,0)` (message box) |
| `0x080036E18–0x080036E44` | `0x36E18` | `A+B+Select+Start` branch; save-marker rewrite |
| `0x08004A010` | `0x4A010` | writes `A5 5A C3 3C` at `0x02028E41` |
| `0x080036CB4` | `0x36CB4` | save manager re-entry |
| `0x08012260` | `0x12260` | VBlank/IRQ key poll → `0x03000040` (prev), `0x03000042` (copy), `0x03000044` (raw), `0x03000046` |
| `0x0801348C` | `0x1348C` | key-state struct updater for `0x03002090` |
| `0x03002090` | RAM | key struct: `+0` held, `+2` new presses, `+4` repeat, `+6` ?, `+8` raw, `+10` ?, `+12/+14` previous |
| `0x03000040…46` | RAM | second key-shadow block written by the IRQ poll |
| `0x04000130` | I/O | `KEYINPUT` (active-low) |
| `0x0607660–0x0609900` | `0x607660` | ASCII menu-caption block (top-level captions, design-room help, map names, CO names) |
| `0x0861288C` | `0x61288C` | text-pointer table, 1375 × `u32`; caption IDs used below are `(0x0861313C + 4·id)` |
| `0x08607660` | | “Fight your way through the story.” (Campaign) |
| `0x08607684` / `0x086076A8` | | Campaign Continue / New |
| `0x086076C0` | | “Battle friends or the computer.” (Versus) |
| `0x0860772C` / `0x08607758` / `0x08607784` | | War Room main / Continue / New |
| `0x086077A4` | | “Shop here with your hard-earned points.” (Battle Maps) |
| `0x086077CC` | | “Create maps and edit the CO colors.” (Design Room) |
| `0x086077F0` / `0x0860781C` | | Design Room Map / CO |
| `0x0860783C` | | Link description |
| `0x08607868` | | **“Press SELECT for Hard Campaign.”** |
| `0x08607888` | | **“Press SELECT for the Sound Room.”** |
| `0x08607DE0` / `0x08607DF0` / `0x08607E00` | | “Design Map 1/2/3” |
| `0x08607E18` / `0x08607E30` | | “Plain” / “Random” |
| `0x08607E38…0x08607EA4` | | fill with sea / plains / mountains / woods |
| `0x08607EC8` | | “Let the computer design a map?” |
| `0x08607EF4` | | “Exit without saving?” |
| `0x61010A` | `0x61010A` | “Delete all saved data?” (save-subsystem text block) |
| `0x061008E` / `0x06100D2` | | “Save current data?” / “Now saving…” |
| `0x16E1CC` | `0x16E1CC` | `-STAFF CREDITS-` (ASCII credit roll, through `0x16E7A4`) |
| `0x05802A4…0x05802F6` | | Link-screen ASCII labels `TEAMS`, `RULES`, `BATTLE*MAPS`, `COLOR*EDIT`, `SELECT*MAP`, `SELECT*MODE`, `SELECT*CO`, `LINK` |
| `0x05826E0` | | `SOUND*ROOM` |
| `0x090F30` | | 45-byte debug glyph strip (`ABCDEFGHLMOPRSTUVWabcdefghi…`) |
| `0x090F8C–0x0910D8` | | **unreachable debug-menu lexicon** (see §6) |
| `0x0849E5F8–0x0849E6A4` | | debug/widget descriptor table (`{handler|1, flags, next, …}`) |

## 5. Algorithm

### 5.1 Key masks

GBA `KEYINPUT` is active-low. The boot code inverts it, so all values here are
active-high “held” masks:

| Button | A | B | Select | Start | Right | Left | Up | Down | R | L |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Mask | `0x001` | `0x002` | `0x004` | `0x008` | `0x010` | `0x020` | `0x040` | `0x080` | `0x100` | `0x200` |

`Delete all saved data` = `L | Right | Select` = `0x200 | 0x010 | 0x004` =
**`0x214`**.

### 5.2 Boot validator (exact disassembly, file offset `0x36D94`)

```
08036d94  2200        movs r2,#0
08036d96  a801        add  r0,sp,#4
08036d98  8801        ldrh r1,[r0,#0]      ; r1 = held
08036d9a  200f        movs r0,#0x0F
08036d9c  4008        ands r0,r1
08036d9e  280f        cmp  r0,#0x0F
08036da0  d006        beq  0x08036db0      ; guard: A+B+Select+Start -> skip
08036da2  a801        add  r0,sp,#4
08036da4  8801        ldrh r1,[r0,#0]
08036da6  2085        movs r0,#0x85
08036da8  0080        lsls r0,r0,#2        ; r0 = 0x214
08036daa  4281        cmp  r1,r0
08036dac  d100        bne  0x08036db0
08036dae  2201        movs r2,#1
08036db0  2a00        cmp  r2,#0
08036db2  d01d        beq  0x08036df0
08036db4  f000f84e    bl   0x08036e54      ; delete-save handler
```

Reimplementation:

```python
def boot_delete_save(held):          # held = (~KEYINPUT) & 0x3FF
    if (held & 0x00F) == 0x00F:      # explicit anti-accident guard
        return False
    return held == 0x214             # exact match, not a mask test
```

Two properties matter:

* The test is **equality**, not `(held & 0x214) == 0x214`. Any extra button
  (A, B, Start, a direction, R) makes the code fail.
* `(held & 0xF) == 0xF` is checked *first* and forces the branch away from the
  delete path even though `0x00F != 0x214`; it documents the developer’s intent
  to keep the four-face-buttons combo harmless.

### 5.3 Second boot branch (file offset `0x36E18`)

```
08036e1a  480b  ldr  r0,=0x04000130
08036e1c  8801  ldrh r1,[r0]
08036e1e  4a0b  ldr  r2,=0x000003FF
08036e20  1c10  adds r0,r2,#0
08036e22  4388  bics r0,r1            ; held
08036e24  210f  movs r1,#0x0F
08036e26  4008  ands r0,r1
08036e28  280f  cmp  r0,#0x0F
08036e2a  d10a  bne  0x08036e42      ; requires A+B+Select+Start
08036e2c  4908  ldr  r1,=0x02028E41
08036e2e  7808  ldrb r0,[r1,#0]
08036e30  28aa  cmp  r0,#0xAA
08036e32  d102  bne  0x08036e3a
08036e34  7848  ldrb r0,[r1,#1]
08036e36  2855  cmp  r0,#0x55
08036e38  d001  beq  0x08036e3e
08036e3a  f013f8e9 bl 0x0804a010    ; write A5 5A C3 3C at 0x02028E41
08036e3e  f7ffff39 bl 0x08036cb4    ; save manager
```

```python
def boot_marker_branch(held):
    if (held & 0x00F) != 0x00F:
        return
    if mem[0x02028E41:0x02028E43] != b"\xAA\x55":
        mem[0x02028E41:0x02028E45] = b"\xA5\x5A\xC3\x3C"
    save_manager()
```

### 5.4 Normal input path

The VBlank poll `0x08012260` computes `held = 0x3FF ^ KEYINPUT`, then
`pressed = held & ~previous`, and mirrors both into `0x03000040…46`. The UI
uses a struct at `0x03002090` maintained by `0x0801348C`, which additionally
cancels contradictory pairs (`L+R` → 0, `Up+Down` → 0). Menu-level `SELECT`
handling (Hard Campaign / Sound Room) runs through this path, not through the
boot raw-key checks.

## 6. Tables

### 6.1 Confirmed button actions

| Screen | Input | Effect | Evidence | Status |
|---|---|---|---|---|
| Power-on / title frame | `L+Right+Select` (`0x214`) | “Delete all saved data? Yes/No” | observed + code | **works** |
| Power-on / title frame | `A+B+Select+Start` mask (`held & 0x00F == 0x00F`) | save marker rewrite + save-manager call, only if marker ≠ `AA55` | code-derived | fires for 64 states; no visible screen |
| New Campaign | `SELECT` | Hard Campaign (caption string `…7868`) | string present; no effect on fresh save | gated on purchase bit |
| Battle Maps | `SELECT` | Sound Room (caption string `…7888`) | no effect on fresh save (`STOCK 0`) | gated on purchase bit |
| Sound Room | `SELECT` | gallery/pictures | published; not reachable | unverified |
| Anywhere in-game | `Start+Select+A+B` | published “quick reset” | pressed at campaign intro: no reset | **not present** in this revision |

### 6.2 Main menu and captions (text-pointer table at `0x0861288C`)

| Entry | Caption pointer | Sub-menu |
|---|---|---|
| Campaign | `0x08607660` | Continue `0x08607684`, New `0x086076A8` |
| Versus | `0x086076C0` | Continue `0x086076E0`, New `0x0860770C` |
| Design Room | `0x086077CC` | Map `0x086077F0`, CO `0x0860781C` |
| Link | `0x0860783C` | Single-Pak / Multi-Pak / Trade Maps |
| Battle Maps | `0x086077A4` | shop; `SELECT` → Sound Room hint `0x08607888` |
| War Room | `0x0860772C` | Continue `0x08607758`, New `0x08607784` |

On-screen order (circular): Battle Maps → War Room → Campaign → Versus →
Design Room → Link.

### 6.3 Design Room menus (all strings present in the text bank)

`File / Help / Intel / Fill / End` (observed). Sub-items available in the
string table: `Design Map 1/2/3`, `Plain`, `Random`, fill-with-`sea`/`plains`/
`mountains`/`woods`, `Let the computer design a map?`, `Exit without saving?`,
`Entry`, `Intel`, plus the five tutorial pages (`Welcome to the map designer!`,
`We’ll provide you with all the tools…`, `If you need instructions…`,
`Press SELECT and then choose Help.`, `Help contains control explanations…`,
`Enjoy!`).

### 6.4 Unreachable debug-menu lexicon (`0x090F8C–0x0910D8`)

```
ON / OFF            FLAG CONTROL   FLAG
  FLASH               SAVEDATA     FLAGALL
  WPTOTAL             WP           Y / G / B
  NEWTANK R           EDIT
  FLASHCLEAR     (L.R.SELECT)
  FLASH << DUMMY (L.R.SELECT)
  FLASH >> DUMMY (A BUTTON)
BACKUP UTL
```

The same region contains an ASCII glyph strip (`0x090F30`, used by the
in-ROM text renderer at `0x0803A86C`) and widget descriptors
(`0x0849E5F8–0x0849E6A4`, e.g. `{0x0803AD49, 0x10000, 0x0849E640, 0x1D0000}`).
The handlers (`0x0803ABDD`, `0x0803ACF1`, `0x0803AD49`, `0x0803AF01`,
`0x0803AF71`, `0x0803AFA1`, `0x0803B0ED`, `0x0803B119`) are only referenced
from inside this cluster or through the internal table; no `BL`, function
pointer or screen-state entry from a reachable menu targets the table root.
Pressing `L+R+Select` inside the map designer produced no effect
(`editor_lr_select.png`), so the `FLASHCLEAR (L.R.SELECT)` label does not
describe a retail trigger.

## 6b. Enumeration

**Space definition.** The boot validator sees exactly 10 key bits
(`A,B,Select,Start,Right,Left,Up,Down,R,L`), so the input space is
`2^10 = 1024` states. There is no sequence, no length field, no alphabet and no
checksum; the comparison is a single equality against a 16-bit literal
(`0x214`) after a 64-value guard.

**Validator.** §5.2. It is total and deterministic: for each of the 1024
values it returns accept (1) or reject (0). Reimplemented offline in
`out/bootcheck.py`.

**Complete accepted set.**

| Value | Combo | Accepts delete path? | Notes |
|---|---:|---|---|
| `0x214` | L+Right+Select | **yes** | the only accepted value |
| any value with `(held & 0x00F) == 0x00F` (64 states) | A+B+Select+Start + anything | no | diverted by the low-nibble guard; runs §5.3 instead |
| all other 959 values | — | no | equality fails |

There is **one** accepted delete code, so the space cannot express a “novel”
second one; the interesting unadvertised branch is the mask path in §5.3,
which is absent from GameFAQs/VGChartz/TCRF/cheatingdome lists. It is *derived*
from the disassembly (marker write `A5 5A C3 3C` at `0x02028E41`, then the save
manager); it could not be given a visible screenshot because the branch changes
save metadata rather than a screen. Its bound is explicit and two-sided:
`(held & 0x00F) == 0x00F` **and** marker ≠ `AA 55`. The 64 accepted mask
values were enumerated exhaustively by `out/bootcheck.py`.

**Bounds proven by rejection (observed in mGBA).** Each was held through a
`Ctrl+R` reset and observed for ≥15 s:

* `L+Right+Select+A` = `0x215` → no prompt (extra bit breaks equality).
* `L+Right` = `0x210` → no prompt (missing Select).
* `A+B+Select+Start` = `0x00F` → no prompt (guard diverts; marker branch runs).

**Negative results, bounded.**

* **Password system:** `strings -n 5` yields 63,015 lines; case-insensitive
  counts: `password`=0, `passwd`=0, `passwort`=0, `cheat`=0, `debug`=0,
  `unlock`=0, `soundtest`=0, `jukebox`=0. `code` occurs twice (story text
  “some sort of code name?”), `secret` three times (story text), `staff`
  once (`-STAFF CREDITS-` at `0x16E1CC`). The UI text bank
  `0x0607700–0x0609900` contains every menu caption and no password/cheat
  screen, and the menu walk reached every top-level mode and sub-mode.
* **Design Room codes:** two controlled entries (plain vs `L+R`) produced the
  identical map; `A+L+R` at the Map/CO selector did not blank the screen.
  Recorded as rejected for `AW2E01` Rev.00, not merely “untested”.
* **Sound test / credits button code:** no sound-test screen exists before
  purchase; the credit roll is data (`0x16E1CC`) shown by the campaign ending.
  No button sequence in the 1024-state space addresses them (the only
  boot-time consumers are the `0x214` equality and the `0x00F` mask branch).

## 7. Validation evidence

**Observed (emulator, native 240×160 frames):**

* `Advance Wars 2 - boot delete prompt.png` — `Delete all saved data? Yes No`
  after holding L+Right+Select at reset.
* `Advance Wars 2 - main menu.png` — SELECT MODE with Campaign and
  Continue/New.
* `Advance Wars 2 - design room.png` — Design Room selected, Map/CO sub-menu.
* `Advance Wars 2 - battle maps shop.png` — Hachi’s shop, `STOCK 0`; `Select`
  did nothing.
* `link_menu.png` (SINGLE-PAK / MULTI-PAK / TRADE MAPS), `war_room_sel.png`,
  `versus_map.png` (SELECT MAP list), `editor_lr_select.png` (L+R+Select in
  the designer: no effect), `abst_start_reject.png` (A+B+Start+Select at boot:
  intro plays, no prompt) — under `/tmp/opencode/aw2/evidence/`.
* Rejection runs `0x215`, `0x210`, `0x00F`: no prompt at 8 s or 15 s.

**Derived (disassembly, `arm-none-eabi-objdump -M force-thumb`):**

* The validator at `0x08036D94` (bytes `2200 a801 8801 200f 4008 280f d006
  a801 8801 2085 0080 4281 d100 2201`), handler call at `0x08036DB4`.
* The `0x00F` branch and marker write at `0x08036E18` / `0x0804A010`.
* Input mask handling and `L+R`/`Up+Down` cancellation at `0x0801348C`.
* All UI captions and the Sound Room / Hard Campaign strings at the addresses
  in §4.

**Inferred:**

* That `0x02028E41` is the save-presence marker and that the `0x00F` branch is
  a developer “initialize save metadata” shortcut; the write itself is proven,
  its persistent meaning is not.
* That the debug-menu lexicon is dead code from a development build. It has no
  reachable caller, but “no caller” is a static statement about the code paths
  found, not a proof about every possible runtime dispatch.

## 8. Unknowns

* Hard Campaign / Sound Room could not be entered: both need Hachi’s shop
  purchases (1000 / 5000 points) which require playing the campaign. Their
  `SELECT` handlers are therefore documented from strings and caption IDs, not
  from an observed entry.
* The Sound Room `SELECT`-to-gallery behaviour is published but untested.
* The exact semantic of the 4-byte marker at `0x02028E41` (`AA 55` vs
  `A5 5A C3 3C`) and whether the `0x00F` branch ever runs in normal play.
* Whether the `0x090F30` debug-menu cluster is reachable through a runtime
  dispatch table not found statically. No key combination tried reached it.
* The published “Nintendo map”/“Japanese map” may exist in another region or
  revision; they do not reproduce on this USA Rev.00 image.

## 9. Tooling

* `mGBA 0.10.5` (`mgba-sdl`), `Xvfb :124`, `openbox`, `xdotool`, `scrot`,
  ImageMagick `import`, `arm-none-eabi-objdump`.
* `python3` with `capstone 5.0.7` (used for ad-hoc literal/BL scans).
* Scripts/artifacts in `/tmp/opencode/aw2/`:
  * `key.py` — input/screenshot helper (window capture + native F12 frames).
  * `out/strings5.txt` — `strings -t x -n 5` of the ROM (63,015 entries).
  * `out/keyscan.py` — naive button-mask byte search.
  * `out/xref.py` — little-endian literal/pointer cross-reference helper.
  * `out/bootcheck.py` — reimplementation of §5.2/§5.3.
  * `shots/`, `evidence/` — emulator frames referenced above.
* Savestates `…ss1`, `…ss2` were used to return to the mode-select menu; both
  are emulator-generated and git-ignored.

## Legal note

No ROM, extracted graphics, music or copyrighted text is redistributed here.
Only hashes, addresses, short quoted UI labels needed to identify the feature,
and the analyst’s own screenshots are included.
