# Tom Clancy's Splinter Cell: Pandora Tomorrow (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Item | Value |
|---|---|
| File | `Tom Clancy's Splinter Cell: Pandora Tomorrow.gba` |
| Size | 8,388,608 bytes (0x800000) |
| Header title | `TOM CLANCY'S` |
| Game code | `BSLE` |
| Maker | `41` |
| Fixed byte / main unit / device | `0x96` / `0x00` / `0x00` |
| Version / complement / checksum | `0x00` / `0x82` / `0x0000` |
| Entry word | `0xEA00002E` (standard `b 0x080000C0`) |
| MD5 | `f7b81f0a57db7206a0f2486491f8a99d` |
| SHA-1 | `56343ba81d3b83941541e682be19c34119dffff9` |
| SHA-256 | `b5ebb6f404433057361f8b883d8d650ad8727f0f8930e9ef6aa0c0bfc2c45919` |

`file(1)` identifies a single GBA image, PAL English build. Phase 0 found one
header, no appended/multiboot image and no scene cracktro; the entry word and
fixed byte are stock. All addresses below are for **this exact hash**.

## 2. Executive summary

**Bounded negative (guide §16.3 case 1): this retail ROM contains no
in-game cheat system.** There is no published password list for a menu, no
button-code matcher, no hidden/debug menu and no code-driven unlock. The only
code-like surface is the **three-character save-slot identifier** entered on the
SELECT GAME screen (`---` → `A A A` by default). It is a save label, not a
validator:

* its alphabet is `A–Z` + `0–9` (36 symbols; Up/Down cycle with wraparound);
* two *arbitrary* values, `Q6Z` and `AAA`, were accepted on the real screen and
  each immediately created a playable CONTINUE/ERASE save slot;
* the bytes typed are stored verbatim (reversed) in the 512-byte SRAM save at
  file offset `0x0C` — `Q6Z` → `5A 36 51`;
* the only comparison the menu makes against the buffer is `byte == 0x2D`
  (`'-'`), i.e. an **empty-slot test** at `0x0805CB84`. No comparison against a
  fixed code, checksum or expected string exists (per §16.2b this excludes the
  field from the cheat space).

Everything the web calls a "password" for this SKU is a **story puzzle
solution**, not a cheat: GameFAQs' 14 entries are 3 turret wire orders and 11
binary-computer codes; the Splinter Cell Wiki adds one more computer code
(Embassy 1 = `3`). They are fixed per-location values revealed by NPCs and
compared to the computer puzzle's own state — there is no player-mintable code
space behind them and no list of codes accepted at a menu.

A retained debug overlay exists (`Level ID:  %d` at `0x080AFDA8`, printer at
`0x08042678`, flag byte at `0x03001020`) but no reachable input sets it; all
gate combinations pressed in the emulator produced no screen change.

Because no validator exists, §0.2's "mint a novel code" deliverable is replaced
by the bounded negative and counts in §6b.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 (SDL), `SDL_AUDIODRIVER=dummy`, Xvfb `:318` + openbox,
  `-3` scale. **Run under a renamed binary** (`./mgba-pandora` symlink): other
  agents in this workspace run `pkill -x mgba`, which otherwise kills this
  session's emulator.
* Keymap verified: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`,
  D-pad = arrow keys. Hold ≥100 ms for menu presses.
* Path walked (screenshots in `/tmp/pandora/`, prefix `walk_`, `gate_`,
  `title`, `opt_`, `code_`, `aaa_`, `boot`):
  1. Ubi Soft / NSA / binary-rain intro → title + language flags (US/ES/FR); A = English.
  2. Main menu **SELECT GAME / OPTIONS**; OPTIONS → **MUSIC / SFX / CREDITS** (MUSIC is an ON/OFF toggle, CREDITS scrolls).
  3. SELECT GAME → 3 slots (`---`); A on empty slot → 3-char entry (`A A A`, first char selected).
  4. Left/Right moves the cursor; Up/Down cycles the character. Measured cycle
     from `A`: `A → 9 → 8 → … → 1 → 0 → Z → Y → … → B → A` (36 states).
  5. A three times commits. `Q6Z` and `AAA` were both accepted; slot changed from
     `---` to the entered value and then offered **CONTINUE / ERASE**.
  6. CONTINUE → **SELECT MISSION** (TRAINING and EMBASSY 1 unlocked on a fresh
     save; later thumbnails are noise/locked) → briefing → gameplay.
  7. In gameplay: Start → **INVENTORY** (VISION / NORMAL, WEAPON / ASSAULT
     RIFLE, ABORT MISSION); L → **MISSION OBJECTIVES**; ABORT MISSION → YES/NO
     confirm; Start → return.
  8. Debug gates pressed with no effect: L, R, Select on title and main menu;
     L, R, Select and L+R+Start held in INVENTORY.
* Codes tested on screen: `Q6Z` (accepted), `AAA` (accepted), and the `---`
  empty sentinel (routes to the NEW-game handler, not a validator).

## 4. Address map

File offset = ROM address − `0x08000000`.

| Address | Meaning |
|---|---|
| `0x0853B4`–`0x085430` | English UI text records: `OPTIONS`, `SELECT GAME`, `SFX`, `MUSIC`, `OFF`, `ON`, `PRESS A TO SELECT`, `NEW`, `ERASE`, `CONTINUE` |
| `0x085434`–`0x085530` | mission-name pointer table: `SELECT MISSION`, `TRAINING`, `EMBASSY 1`, `EMBASSY 2`, `SUBWAY`, `CRYOGENIC`, `SAULNIER`, `JERUSALEM`, `WAREHOUSE`, `SHIPYARD`, `SUBMARINE`, `TV STATION`, `SAULNIER CRYOGENIC` |
| `0x0838AC`, `0x0839E4` | dialogue `D:...CODE IS 052651733373889.`, `P:...THE CODE IS 127.` (story codes, not cheats) |
| `0x0805CB7A`–`0x0805CB86` | menu handler: literal `0x0805CB94` = `0x03000F40`; `ldrb r0,[base+index*8]`; `cmp r0,#0x2D` (`'-'`) → empty-slot branch. Only check of the 3-char field (Derived from watchpoint PC `0x0805CB86`) |
| `0x03000F30` | main game-state struct pointer (468 literal references; common global) |
| `0x03000F40` | save-slot code buffer, IWRAM: 3 chars + NUL per slot, 8-byte stride (`0x03000F40`, `48`, `50`). Savestate raw offset `0x19F40`: `51 36 5A 00` (`Q6Z`) followed by `01 01 00 00` and two `---` slots |
| `0x03001020` | struct+`0xF0` debug flag tested by `0x08042704` (`ldrb`; `lsls #30`; `bge` skips debug work). No writer found |
| `0x080AFDA8` | debug string `Level ID:  %d`; pointer at `0x080426B0`; printer function `0x08042678` |
| `0x08077148` / `0x08077160` | joypad update: `pressed = KEYINPUT ^ held`, `held = KEYINPUT` (active-low) |
| `0x08078704` / `0x08078720` | second `KEYINPUT` reader (link/IRQ test, `and #0x0F`) |
| SRAM `.sav` `0x00`–`0x2F` | slot 0 record: `00 01 BA AD`, magic `00 22 44 55`, code **byte-reversed** at `+0x0C` (`5A 36 51`), used flag `+0x0F` = `01`; slots at `0x30` stride begin `00 00 BB AA 00 22 44 55` when empty |

Only **four** literal references to `0x04000130` exist in the whole image
(the two routines above); there is no third input consumer that could implement
a button code.

## 5. Algorithm (observed input path; no validator)

```
code entry (screen):
  chars[3] initialized = "AAA"
  Left/Right  -> cursor = (cursor ± 1) mod 3
  Up/Down     -> index = (index ± 1) mod 36 ; symbol = SYMBOLS[index]
  A           -> advance cursor; on third A commit
commit:
  if chars[0] == '-':  NEW_GAME          ; only check (0x0805CB84, cmp #0x2D)
  else:                SAVE_SLOT(chars)  ; stored verbatim, no checksum
save:
  sram[slot*0x30 + 0x0C .. +0x0E] = reverse(bytes(chars))   ; observed
  sram[slot*0x30 + 0x0F] = 0x01                             ; observed
```

`SYMBOLS` (measured from the on-screen cycle, not a ROM ASCII string):

```
index:  0 1 2 ... 24 25 26 27 28 29 30 31 32 33 34 35
symbol: A B C ...  Y  Z  0  1  2  3  4  5  6  7  8  9
```

Down decrements the index modulo 36 (from `A` the observed sequence is
`9,8,…,0,Z,Y,…,B,A`); Up increments. No hash, XOR, permutation, key table or
comparison against a target code was found on this path.

## 6. Tables

* **Save-slot identifier alphabet (Observed):** 36 symbols `ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789`.
  Space = 36³ = 46,656 strings, all treated identically (label only).
* **Missions (Observed, text bank `0x085480`+):** 12 names listed in §4; only
  TRAINING and EMBASSY 1 are selectable on a fresh save (no code unlocks the rest).
* **Published "passwords" (recon, evidence only — gameplay puzzles, out of cheat scope):**
  * GameFAQs (14): turret wire orders — Jerusalem `GREEN,YELLOW,RED`;
    Shipyards/Warehouse `GREEN,YELLOW,BLUE,RED`; and 11 computer binary codes:
    Embassy 2 `5`, Saulnier `9,2` / `6,8` / `5,3`, Shipyard `1,2,7`,
    Submarine `4,9,7`, TV Station `3,2,8` / `4,6,9` / `2,6,6` / `8,4,1`,
    Warehouse `3,3`.
  * Splinter Cell Wiki (12 computer codes): same 11 plus Embassy 1 `3`.
  * ROM verification: `127` appears literally in four localised dialogue
    strings (`0x0839E4` English, `0x08BAA8` French, `0x09BBC8` Dutch,
    `0x0A3C70` German); the others are script-supplied digits
    (`1:HERE IS THE CODE : 0` at `0x07FFB0` is the format string). None is a
    menu-accepted code and none is stored as an accepted-code table.
* **Debug gates pressed (Observed, no effect):** L / R / Select at title and
  main menu; L / R / Select and L+R+Start in INVENTORY.

## 6b. Enumeration

**Space definition.** The only code-shaped input surface is the 3-character
save-slot field: alphabet `A–Z0–9` (36), length 3, no checksum, no reserved
bits → 36³ = **46,656** representable strings. Every symbol is reachable from
the on-screen keyboard (measured 36-state cycle, §5). The SRAM stores the exact
typed characters reversed, which is the signature of a label, not of an encoded
payload. The only gate is `chars[0] == '-'` (empty marker), checked by the menu
handler at `0x0805CB84`; `---` is the initial empty state and is not user-typed
through the alphabet (the symbol set has no `-`).

**Validator model.** N/A — there is no validator to reimplement. Running the
game's own menu code over the space (§16.9 analogue) is unnecessary because the
accept path does not inspect character values: it copies them into the save and
returns to SELECT MISSION. The debug overlay is the only conditional path near
a code-like state and is gated by a flag byte with no writer in the image.

**Novel code.** None possible — there is no accepted/rejected code set to mint
from. Two arbitrary strings (`Q6Z`, `AAA`) were entered on the real screen and
both produced playable saves (screenshots `code_q7z.png`, `aaa_final.png`);
this is positive proof that no unpublished-value discovery is taking place.
Per the engagement brief, the §0.2 mint deliverable is replaced by the bounded
negative below.

**Bounds proven by rejection / gate tests (Observed).**
* `---` empty slot routes to the NEW-game path; a typed value routes to the
  CONTINUE/ERASE save path — the only two outcomes of the comparison at
  `0x0805CB84`.
* L, R, Select on title and main menu: no screen change (`gate_title_*.png`,
  `gate_menu_*2.png`).
* L, R, Select and L+R+Start held in INVENTORY: still INVENTORY
  (`gate_*_inv.png`, `gate_LRStart_inv.png`).
* No debug overlay appeared at any point; the `Level ID: %d` flag at
  `0x03001020` was never observed set.

**Search space checked (counts, Derived/Observed).**
1. Screens walked: **15** distinct states — intro, title/language, main menu,
   OPTIONS submenu, MUSIC toggle, CREDITS, SELECT GAME slots, 3-char entry,
   slot CONTINUE/ERASE, SELECT MISSION, briefing, gameplay, INVENTORY,
   MISSION OBJECTIVES, ABORT confirm — plus 7 gate-key states.
2. ASCII strings extracted (min length 4): **69,775**. Case-insensitive keyword
   hits in the full 8 MiB: `password` 0, `cheat` 0, `debug` 0, `level select` 0,
   `cheat manager` 0, `invincib` 0, `god mode` 0, `unlimited` 0, `infinite` 0,
   `press l` 0, `master code` 0, `code generator` 0, `enter code` 0,
   `invalid code` 0, `bonus` 0, `unlock all` 0, `quickwarp` 0, `teleport` 0,
   `mission select` 0; `to unlock` 1 (gameplay dialogue "WHAT'S THE CODE TO
   UNLOCK"); `secret` 2 (French/Spanish story dialogue only).
3. Cross-encoding debug-string search: **9 strings × 6 encodings = 54 checks**
   (ASCII, lowercase, UTF-16LE, UTF-16BE, XOR 0x20, +0x20) → **0 hits**.
4. Button-code mask scan: **8 sequences × 2 active levels × 3 widths = 48
   variants** over 8,388,608 bytes; 7,105 raw single/multi-byte hits, all in
   compressed level/audio data with no validator context. The one 2-byte hit
   (L+R+Select active-high, `0x119B9D`) lies in compressed data; no expected-mask
   array exists in the input path.
5. Input-handler analysis: **4** `KEYINPUT` literal references forming **2**
   routines (`0x08077148`, `0x08078704`); **0** progress-index/mask-array
   comparisons; **0** strcmp/memcmp against the 3-char buffer.
6. Code-buffer reads observed live: mGBA read watchpoint at `0x03000F40` hit
   once during menu navigation at PC `0x0805CB86` (`cmp r0,#0x2D`); a GDB byte
   read watchpoint over a further navigation sequence produced **325** hits at
   only **3** distinct PCs, all in IWRAM copy loops (`0x03000378`,
   `0x030004C4`, `0x03000630`) — no code-comparison site.
7. Debug-overlay evidence: 1 format string, 1 pointer, 1 printer, 0 reachable
   setters found — dead/gated code, not a hidden menu.

This is a **no-system negative** (§16.3 case 1), closed by full screen
enumeration, the live watchpoint evidence and the counts above. It is
independently derived for this `BSLE` image; no address or conclusion was
carried over from the separately analysed first Splinter Cell GBA report.

## 7. Validation evidence

* **Observed:** all screenshots listed in §3; acceptance of `Q6Z` and `AAA`;
  SRAM bytes `5A 36 51` at `0x0C`; savestate IWRAM bytes at raw `0x19F40`;
  watchpoint hits and PCs; every gate-key press; all screen transitions.
* **Derived:** menu-handler disassembly at `0x0805CB00`–`0x0805CB94`;
  joypad routines at `0x08077148`/`0x08078704`; debug printer at `0x08042678`;
  string/pointer/pattern scan counts; save-slot stride from the `.sav` layout.
* **Inferred:** that the debug `Level ID` overlay is unreachable in retail play
  (no writer found, no gate pressed successfully); that the published computer
  codes are script-driven puzzle values rather than a code table (only `127`
  has a literal dialogue hit; the rest use a formatter with a runtime digit).

## 8. Unknowns

* The binary-computer puzzle validator itself was not disassembled: its codes
  are gameplay puzzle values revealed by NPCs, not a cheat/menu code surface.
  If a future brief includes in-game puzzle solutions as "codes", the expected
  values live in level scripts (e.g. `01 00 00 00 02 00 00 00 07 00 00 00`
  for Shipyard's `1,2,7` at file `0x77D810`) and would need a separate pass.
* Whether the `Level ID: %d` overlay can be enabled by a cheat device (out of
  scope) — no in-game input was found that writes `0x03001020`.
* The ERASE confirmation dialogue was not captured: a Down/A sequence from the
  slot options entered SELECT MISSION instead; the confirm strings exist at
  `0x085450`–`0x08547C` but were not triggered.

## 9. Tooling

`file`, `md5sum`/`sha1sum`/`sha256sum`, `strings`, `xxd`, Python 3 (`re`,
`struct`, `zlib`, Capstone 5.x), `arm-none-eabi-objdump -M force-thumb`,
mGBA 0.10.5 under Xvfb `:318` with `SDL_AUDIODRIVER=dummy`, `xdotool`, `scrot`,
ImageMagick (`convert`, `montage`), mGBA `-d` command-line debugger and GDB stub
(`gdb-multiarch` read watchpoints). Scripts/artifacts in
`/tmp/pandora/`: `ui.py`, `scan_ldr.py`, `finalscan.py`, `gdbcmd.txt`,
screenshots and decompressed savestate `state_q6z.bin`. No ROM or copyrighted
asset is redistributed; only hashes, addresses and derived findings are published.

## 10. Legal note

Analysis only. No ROM image, extracted graphics, music or game text is
redistributed by this report. All emulator-generated `.sav`/`.ss*` files were
removed from the ROM folder and all analyst-owned processes were stopped.
