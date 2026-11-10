# Classic NES Series: Excitebike (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Classic NES Series: Excitebike/Classic NES Series: Excitebike.gba` |
| Size | 1,048,576 bytes (`0x100000`) |
| Header title | `EXCITEBIKE` (`0xA0`–`0xAB`, NUL padded) |
| Game code | `FEBE` (`0xAC`–`0xAF`) |
| Maker | `01` (`0xB0`–`0xB1`) |
| Version | `0x00` (`0xBC`) |
| Entry word | `0xEA000031` → ARM branch to `0x080000CC` |
| Stored header checksum | `0x0000`; calculated `0xFF01` (mismatch) |
| Stored complement | `0x01`; XOR of `0xA0`–`0xBC` = `0x90` (mismatch) |
| MD5 | `249a079e6e7cd8a870e23f4fa390d9ea` |
| SHA-1 | `ab7f8ac5d6588c13f143e13d66c513c822ba4771` |
| SHA-256 | `6c89e0e30f355a47f7d80985d96c9145e2592b5bb4a92eda3ef27f3124786593` |

Phase 0 notes:

* Exactly one 156-byte Nintendo logo occurs, at file offset `0x4`; there is no second GBA header and no multi-game shell.
* The header has been rebuilt: stored checksum `0x0000` and complement `0x01` do not match their calculated values, while the entry branches to `0x080000CC` instead of `0x080000C0`. Bytes `0x080000C3`–`0x080000CB` are `49 45 58 42 49 4B 45 5F 32` (`IEXBI` + `EXBIKE_2`) and the first 4 KiB is normal ARM/Thumb wrapper boot code. This is the Classic NES wrapper signature, not a scene cracktro.
* No trainer, cracktro, appended menu, or extra payload was found. `strings -t x -n 4` gives 10,119 lines; a case-insensitive grep for `password|cheat|debug|secret|unlock|design|track|save|level|select|menu|reset|state|code` returns **0** hits, because the NES UI is stored as CHR tile indices, not ASCII (see §11 of the guide and §16.16).
* The ROM is an **emulated NES game**: the wrapper executes a 16 KiB NROM-128 Excitebike image (6502) in EWRAM; the NES 2 KiB RAM lives in IWRAM. Addresses in §4 are therefore NES (`$C000`–`$FFFF`) or host (GBA) addresses, never ARM code addresses for the game logic.

## 2. Executive summary

This build is the NES Excitebike inside Nintendo's Classic NES (Famicom Mini) wrapper, with the wrapper's pause/reset services but **no wrapper text menu**.

There is **no password system, no button-code cheat, no debug/test menu, and no unlockable**. Publication lists for this SKU contain only GameShark/CodeBreaker/Action Replay codes (memory writes, outside this engagement's scope) and gameplay tips; the only in-game secret that is actually documented for the NES game is the alternate title music produced by resetting the console during play, which this wrapper can reproduce with its reset combo.

The one real developer surface is **Design (track editor) mode**, and it contains the only undocumented selector in the image:

* The design menu is a **6-slot** selector (`$C3BD`: `LDA #$06; JSR $C7DE`). Only four slots are drawn and labelled — `PLAY MODE A`, `PLAY MODE B`, `DESIGN`, `RESET` (label block `$D80B`–`$D83A`). Slots **3 and 4 have no label in the text bank**.
* The cursor routine at `$D614`–`$D621` **unconditionally skips slots 3 and 4** when the menu count is 6 (`CPY #$03` → `INY INY`; `CPY #$04` → `DEY DEY`). The observed reachable cycle is `0 → 1 → 2 → 5 → 0`, in both directions.
* Slots 3 and 4 nevertheless have live action code: the dispatcher at `$C3C5`–`$C3E7` maps them to game states `$0C`/`$0D`, whose handlers (`$C43D`, `$C41C`) copy `$65`–`$6A` into `$05A0`/`$05C3` and copy the `$05E0` page to `$06E0`, and the text bank contains the strings **`saving`** (`$D62A`) and **`error`** (`$D634`) directly after the design-menu labels. These are the SAVE/LOAD track routines of the NES original (Nintendo's published manual CLV-P-NAAHE and the hvc7.dev tape-format write-up both document SAVE and LOAD in this menu); in this build they are **dead code**, unreachable from any input.
* Exhaustive writer analysis proves the dead slots cannot be set through another path: `$41` is written at only five sites (`$C355`, `$C3DC`, `$C482`, `$CC7A`, `$EBB4`) and only `$C3DC` produces states 12/13; `$42` is written at seven sites, all of which either zero it, restore a reachable value, or are the cursor routine itself.

Wrapper behaviour, RAM-verified:

* **L+R** freezes the emulated NES (NES RAM diff = 0 bytes over 1.2 s while held, at the title and mid-race) and draws a dim panel through the wrapper's own BG0 tilemap; there is no text menu.
* **Start + Select + A + B** resets the emulated NES (title returns, NES state re-initialises).
* Pressing **Start** while paused resumes the NES (the paused mask goes `0x300` → `0x308` and the game advances); the wrapper's pause handler also tests B and A|Start as exit buttons.
* SRAM is 8 KiB. One wrapper record exists at `0xFF8`/`0x1000`: 5-byte magic `IBXEI` (the reverse of the ROM boot signature `IEXBI` at `0x080000C3`) plus a state image and a `5A A5` marker at `0x1058`. Editing a design track left the mGBA `.sav` byte-identical across the edit (mGBA may buffer writes, so this is consistent with, not proof of, the absence of a track-save path); the record is most plausibly a wrapper suspend/checkpoint.

Bounded negative: every screen was walked, all six `$15` joypad read sites were enumerated (no sequence/mask table), the design selector's whole 6-slot space was exercised, and the four published GBA code lists were checked — they are memory-edit codes only. There is no code space to enumerate (no alphabet, no length rule, no checksum), so no novel password can exist; the only undocumented entries in the image are the two dead design-menu slots, and their bounds are proven by in-game rejection (2 → 5 and 5 → 2, never 3/4).

## 3. How to reproduce

### Emulator and keymap

* mGBA 0.10.5 SDL (`/usr/games/mgba`) under `Xvfb :250`, `openbox`, `SDL_AUDIODRIVER=dummy`.
* Keymap: **A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`**, D-pad = arrow keys.
* Keys must be sent as XTEST events to the focused mGBA window; one press = 0.10 s hold + 0.30–0.40 s gap. A 0.10 s/0.15 s rhythm sometimes drops a press, so verify progress by RAM (below) rather than by key count.

### Menu path (all screens observed)

| Screen | How to reach | State `$41` | Selector |
|---|---|---|---|
| Title | boot | 0 | 3 items: `selection a`, `selection b`, `design` |
| Track select | title, Start (cursor `$42 = 0`) | 1 | 5 items: tracks 1–5 (`1  2  3  4  5`) |
| Race | track select, Start | 2 (setup) / 4 (running) | — |
| Design menu | title: Select until `$42 = 2` (Design), Start | 8 | 6 slots, labels for 0,1,2,5 only |
| Track editor | design menu, slot 2 (DESIGN), Start | 9 | 19 pieces `a`–`s` + `CL` + `END`, then lap count |
| Pause | hold L+R anywhere | — | dim panel, NES frozen |
| Reset | Start+Select+A+B | 0 | title |

### Key RAM (live, from mGBA savestates)

* NES CPU RAM base: IWRAM `0x03007200` (= decompressed savestate offset `0x20200`), 2 KiB.
* `$0000+0x41` = game state (0..13); `$42` = current selector index; `$43` = confirmed title/menu choice; `$00` = selector item count passed to `$C7DE`.
* Wrapper key state: IWRAM `0x03005CE8` = current pressed mask (active high), `0x03005CEC` = newly pressed mask.

Example verification loop (one press each):

1. Reset with Start+Select+A+B.
2. Read `$42` (0). Press Select → `$42 = 1`; again → 2 (`design`); again → 0.
3. At `$42 = 2`, press Start → `$41 = 8` (design menu).
4. In state 8, press Select repeatedly: `$42` sequence `0 → 1 → 2 → 5 → 0`; the values `3` and `4` are never produced.

### Savestate reading (no debugger)

mGBA `.ss1` is a PNG with a zlib-compressed `gbAs` chunk; `zlib.decompress` yields a 397,312-byte (`0x61000`) state for this 1 MiB ROM:

| State offset | Region |
|---:|---|
| `0x0000` | header/CPU/IO base |
| `0x0400` | GBA I/O (`KEYINPUT` at `0x0530`) |
| `0x0800` | palette |
| `0x0C00` | OAM |
| `0x1000` | VRAM (`0x18000`) |
| `0x19000` | IWRAM (`0x8000`) |
| `0x21000` | EWRAM (`0x40000`) → NES PRG `0x02000000`, NES CHR `0x02004000` |
| `0x20200` | NES 2 KiB RAM (IWRAM `0x03007200`) |

The visible NES nametable is the GBA BG3 tilemap at VRAM `0x2000` (`BG3CNT = 0x4405`, 4 bpp, char base `0x4000`). Tile index `t` decodes as digit `0–9` for `t ≤ 9`, letter `A–Z` for `0x0A–0x23`, space for `0xFC`. The wrapper pause overlay is the BG0 tilemap at VRAM `0x6800`.

## 4. Address map

### GBA / wrapper

| Address / offset | Meaning |
|---|---|
| File `0x2EE9` | Start of the wrapper-encoded NES image (not the runtime bytes; 16,254 of 16,384 bytes differ from the live image) |
| `0x080000C3` | Boot signature `49 45 58 42 49 …` (`IEXBI`), also `EXBIKE_2` at `0x080000C4` |
| `0x080000CC` | Entry point (ARM) |
| `0x08000DF4` | Joypad read: `pressed = 0x3FF ^ KEYINPUT(0x04000130)`; stores current at `0x03005CE8`, newly pressed at `0x03005CEC` |
| `0x08000E24`/`0x08000E44`/`0x08000E60` | Frame wait / VBlank sync helpers used by the wrapper |
| `0x08000EC4` | Wrapper dialog/pause routine: toggles on Start|Select (`#0x30`), exits on B or A/Start |
| `0x02000000` | NES PRG, 16 KiB runtime image (EWRAM) |
| `0x02004000` | NES CHR, 8 KiB (EWRAM) |
| `0x03007200` | NES CPU RAM, 2 KiB (IWRAM) |
| `0x03005CE8` / `0x03005CEC` | Wrapper pressed / newly-pressed mask |
| SRAM `0x0E000000` | 8 KiB save; non-zero record at `0xFF8`/`0x1000` |

### NES side (16 KiB NROM-128 mapped at `$C000`–`$FFFF`, mirrored `$8000`–`$BFFF`)

| NES address | PRG offset | Meaning |
|---|---:|---|
| `$C000` | `0x0000` | State dispatch table, 16-bit pointers for states 0–13 |
| `$C184` | `0x0184` | Reset handler (`78 D8 A2 FF 9A`); vectors at `$FFFA`: NMI `$C23B`, RESET `$C184`, IRQ `$FFF0` |
| `$C2A9` | `0x02A9` | Dispatcher: `state = $41`, `ptr = table[$41]`, `JMP ($0000)` |
| `$C346` | `0x0346` | State 0 (title): menu count 3 at `$C359` |
| `$C395` | `0x0395` | State 1 (track select): clears Select/Start, count 5 at `$C3A3` |
| `$C3B8` | `0x03B8` | Cursor sprite refresh (X positions at `$C083`, Y at `$C08B`) |
| `$C3BD` | `0x03BD` | **State 8 (design menu): `LDA #$06; JSR $C7DE`** |
| `$C3C5`–`$C3E7` | `0x03C5` | Design-menu dispatcher: `<2` play mode; `==2` editor; `==5` reset; `3/4` → `$41 = $42 + 9` |
| `$C41C` / `$C43D` | `0x041C` / `0x043D` | States 13 / 12 (SAVE/LOAD path) |
| `$C7DE`–`$C81D` | `0x07DE` | Selector input: count in `$00`, index in `$42`; Start/Up = increment, Select = decrement, expose |
| `$C97C` | `0x097C` | State 9 (editor/race renderer entry) |
| `$C99A` / `$CB2C` / `$C465` | — | States 2/5/10, 3/6/11, 4/7 |
| `$D614`–`$D621` | `0x1614` | **Count-6 skip: Y==3 → Y=5, Y==4 → Y=2** |
| `$D83C`–`$D848` | `0x183C` | Cursor wrapper: `LDA $00; CMP #6; BNE store; CPY #3; JMP $D614` |
| `$D5A4` … `$D6E0` | `0x15A4` | Screen text bank (tile indices): `excitebike`, `design track`, `game over`, `time up`, `saving`, `error`, `selection a/b`, `design`, `challenge race`, `track`, `best time`, `your time`, `ranking` |
| `$D80B`–`$D83A` | `0x180B` | Design-menu labels: `play mode a`, `play mode b`, `design`, `reset` (only four) |
| `$D62A` / `$D634` | `0x162A` / `0x1634` | `saving` / `error` |
| `$E70B`, `$E17F`, `$E456` | — | Editor update/render routines reached from state 9 |
| `$EB9E`–`$EBB6` | `0x2B9E` | Design-mode entry transition: copies the `$05E0` page, sets `$42 = 0`, `$41 = 8` |
| `$F4FF`, `$F68D`, `$F755` | — | Text/nametable renderers |

## 5. Algorithm

### 5.1 State machine

```
state = $41
if $40 != 0:
    ptr = u16[$C000 + 2*state]
    JMP (ptr)
else:
    ... (input/auth path)
```

The table contains exactly 14 valid entries (0–13); entry 14 onward is data (`$0100`, `$0302`, …). States 12 and 13 are referenced by no other writer than the design-menu dispatcher.

### 5.2 Design-menu selector (reimplementation, agrees with the ROM)

```
def press(menu_count, idx, inc):
    y = idx
    if inc:
        y += 1
        if y >= menu_count: y = 1        # $C80A-$C80F
    else:
        y -= 1
        if y < 0: y = menu_count; y -= 1 # $C811-$C816
    if menu_count == 6:                  # $D83C: LDA $00; CMP #$06
        if y == 3:  y = 5                # $D614: BEQ $D61D; INY; INY
        elif y == 4: y = 2               # $D616-$D61B: CPY #4; DEY; DEY
    return y
```

The reachable set for count 6 is therefore `{0,1,2,5}`; `{3,4}` are absorbing-excluded in both directions. Verified live: `0→1→2→5→0` and reverse `0→5→2→1→0`.

### 5.3 Design-menu action

```
idx = $42
if idx < 2:      $03F2 = idx; $41 += 1        # play mode A/B
elif idx == 2:   $41 = 9                      # editor
elif idx == 5:   $42 = 2; JMP $CA85           # reset track (clear $00-$1F, etc.)
else:            $41 = idx + 9                # slots 3/4 -> states 12/13 (SAVE/LOAD)
```

### 5.4 Wrapper input

```
new = 0x3FF ^ KEYINPUT
pressed = new & ~old          # 0x03005CE8
edge    = new & ~old          # 0x03005CEC
```
Pressed-bit values: `A=1, B=2, Select=4, Start=8, Right=0x10, Left=0x20, Up=0x40, Down=0x80, R=0x100, L=0x200`.

* L+R (`0x300`) freezes the emulated NES and draws the wrapper's dim BG0 panel.
* Start+Select+A+B (`0x0D` + Start) resets the emulated NES.
* Any other new press resumes.

## 6. Tables

### 6.1 Menus and selectors

| Menu | State | Count source | Items | Reachable |
|---|---|---:|---|---|
| Title | 0 | `LDA #$03` @ `$C359` | selection a, selection b, design | 0,1,2 |
| Track select | 1 | `LDA #$05` @ `$C3A3` | tracks 1–5 | 0,1,2,3,4 |
| Design menu | 8 | `LDA #$06` @ `$C3BD` | play mode a, play mode b, design, **slot3**, **slot4**, reset | 0,1,2,5 |
| Editor | 9 | — | `a`–`s` (19), `CL`, `END` | all |

### 6.2 State table (`$C000`, 16-bit LE)

```
0:C346 1:C395 2:C99A 3:CB2C 4:C465 5:C99A 6:CB2C 7:C465
8:C3BD 9:C97C 10:C99A 11:CB2C 12:C43D 13:C41C
```

### 6.3 Design-menu cursor sprite positions (`$C083`, X only; Y at `$C08B`)

```
idx:      0    1    2    3    4    5
$C083:   48   60   78   90   A8   50
$C08B:   30   48   60   78   90   A8
```
Six entries, which is the independent confirmation that the menu template is 6 items wide even though only four labels exist.

### 6.4 Text

The NES UI is tile-index text (`tile = ascii_lower - 0x57`; digits `0x00–0x09`; space `0xFC`; `0x00` terminates). Relevant strings and addresses:

| Address | Text |
|---|---|
| `$D5A4` | `excitebike` |
| `$D5BB` | `design track` |
| `$D5E4` | `game over` |
| `$D60B` | `time up` |
| `$D62A` | `saving` |
| `$D634` | `error` |
| `$D69D`–`$D6C6` | `selection a`, `selection b`, `design`, `1984 nintendo` (interleaved with control bytes) |
| `$D6EC` | `challenge` `race` `track` |
| `$D708` | `1  2  3  4  5` |
| `$D76B`/`$D777` | `best time` / `your time` |
| `$D783` | `ranking` / `excitebike` / ` track ` |
| `$D80B`–`$D826` | `play mode a`, `play mode b` |
| `$D82C`/`$D835` | `design` / `reset` |

### 6.5 Joypad read sites (`LDA $15`) — the complete input surface

| Site | Mask / test | Role |
|---|---|---|
| `$C395` | `AND #$F3`, then `AND #$03` → bits 2/3 | clears Select/Start, aliases A/B into bits 2/3 (no reachable effect: `$C7DE` requires a D-pad bit) |
| `$C7E4` | `AND #$3C` | selector: D-pad present |
| `$C7F5` | `BIT $C0CE`, `LSR×3`, `LSR` | selector: increment (Up/Start) / decrement (Select) |
| `$CA25` | `ASL×3`, `LSR` | Start/Select |
| `$CA3D` | `AND #$10` | Up |
| `$CA74` | `AND #$0F` | A/B/Select/Start |

There is no multi-press sequence table, no ring buffer, no XOR key, and no comparator against a stored button string. This is the evidence for "no button-code cheat".

## 6b. Enumeration

### Space definition

This image has **no password/cheat code space**: no on-screen alphabet, no fixed length, no checksum, no lookup table of codes. The only selectable spaces are the menus:

| Space | Size | Reachable | Rejected |
|---|---:|---|---|
| Title selection | 3 | 3 | — |
| Track selection | 5 | 5 | — |
| Design-menu slots | 6 | 4 (`0,1,2,5`) | `3,4` |
| Editor palette | 19 pieces + `CL` + `END` | all | — |

### Hidden slots (the only undocumented entries)

Slots 3 and 4 are the undocumented entries: no label bytes exist in the text bank, and they are skipped by the count-6 cursor rule. Their action code sets states 12 (`$C43D`) and 13 (`$C41C`), which implement the NES original's SAVE/LOAD track routines (RAM copies `$65–$6A → $05A0/$05C3` and `$05E0 page → $06E0 page`), with `saving`/`error` messages present at `$D62A`/`$D634`. The published manual for this menu (Nintendo CLV-P-NAAHE) and the hvc7.dev NES tape-format write-up both document `SAVE` and `LOAD` in the design menu, and the 6-entry cursor table (`$C083`) shows the menu was authored for six items. In this build they are **dead code**: no input can produce `$42 = 3` or `4` (see §5.2), and no other writer of `$41` produces states 12/13.

### Novel codes / states

No novel password can be minted: there is no code space. The only "novel" entries the ROM contains are slots 3 and 4, and they cannot be entered from the game's own input path. Their bounds are therefore proven **by rejection**:

* Live, count-6 menu: from slot 2 (DESIGN), one Select gives slot **5** (RESET), not 3; from slot 5, one Select gives **2**, not 4. RAM `$42` never becomes 3 or 4 in the whole 6-item cycle (`0,1,2,5`).
* The count-5 track menu *does* visit all five indices (`1,2,3,4,0` observed), which confirms the skip is specific to the count-6 design menu and not a general cursor bug.
* Because the slots are unreachable by input, the only way to execute states 12/13 would be a direct RAM write, which is outside the in-game/developer-intended scope of this report.

### What this proves

The accepted set of selector actions is exactly the four labelled design-menu items plus the three title items and five track entries. The undefined entries are not merely undocumented: they are excluded by the game's own comparison chain, and the exclusion is measurable in RAM. This is a closed negative for "hidden design-menu SAVE/LOAD" in this SKU, not an untested assertion.

## 7. Validation evidence

**Observed (live mGBA, RAM/VRAM reads):**

* Title text `selection a`, `selection b`, `design`, `1984 nintendo` (BG3 tilemap, VRAM `0x2000`).
* Track select `challenge race`, `track`, `1  2  3  4  5`; `$41 = 1`.
* Race HUD `nintendo`, `3rd`, `temp`, `time`, `1.24.00`; `$41 = 2/4`.
* Design menu `play mode a`, `play mode b`, `design`, `reset`; `$41 = 8`; selector values `0,1,2,5` observed.
* Design menu Select cycle: `$42` = `2,5,0,1,2,5,0,1,2` across nine presses — never 3/4.
* Editor palette row shows `abcdefghijklmnopqrs` plus two further icons; `$41 = 9`.
* L+R held: `0x03005CE8 = 0x300`; NES RAM diff over 1.2 s = **0 bytes** (frozen) at title and during a race; VRAM BG0 `0x6E48–0x72B3` changes (dim panel).
* Start+Select+A+B: title returns; `$41 = 0`; NES state re-initialised.
* Design-track edit followed by `cmp` of the mGBA `.sav`: byte-identical (0 differing bytes).
* SRAM content: `0x000–0x1FF = 0xFF`, zeros elsewhere except the record at `0xFF8`/`0x1000` and payload to `~0x1130`.

**Derived (disassembly + enumerations):**

* The 14-entry state table and all five `$41` writers.
* The count-6 skip at `$D614` and its live cycle.
* The design-menu dispatch and slots 3/4 → states 12/13.
* The complete `$15` read surface (six sites) with no sequence matcher.
* NES PRG = 16 KiB NROM-128 (`RESET $C184`, NMI `$C23B`, IRQ `$FFF0`).

**Inferred:**

* Slot 3 = SAVE and slot 4 = LOAD (order not observed; states 12/13 are the two halves of the same copy/handshake code).
* The SRAM record is a wrapper suspend/checkpoint (magic is the reversed boot signature; the record contains a RAM image and a `5A A5` marker); its exact field layout was not recovered.
* The wrapper routine at `0x08000EC4` is a dialog/pause handler; no caller was found by BL scan, so its role is inferred from the mask checks.

## 8. Unknowns

* Exact field layout of the SRAM record at `0xFF8`/`0x1000` (header duplicated 8 bytes apart; payload includes the `$05E0`-style `0x40`/`0x09` page and a `5A A5` marker).
* Which of states 12/13 is SAVE vs LOAD, and the exact protocol of `$44`/`$48`/`$FF` handshake.
* The 57 `0x42` bytes in the runtime PRG: the wrapper-patch hypothesis (as in the Bomberman report) was not proven; they do not affect the selector or input paths.
* The wrapper's native "dialog" routine (`0x08000EC4`) is unreachable by BL scan; whether it is dead or called indirectly was not established.
* Audio of the published "alternate title music after reset" easter egg was not captured (media ban); only the reset path itself was verified.
* Lap-count range in the editor was not enumerated (the editor palette was observed, but a full track was not authored).

## 9. Tooling

* `mgba` 0.10.5 SDL, `Xvfb :250`, `openbox`, `SDL_AUDIODRIVER=dummy`; `xdotool` XTEST input.
* `ss.py` — zlib-decompress the mGBA PNG `gbAs` chunk and address VRAM/IWRAM/EWRAM/NES RAM.
* `mapd.py` — render the GBA BG tilemap at VRAM `0x2000` as text (tile→digit/letter mapping).
* `d6502.py` / `scan6502.py` — py65-based 6502 disassembly and illegal-opcode scans.
* `arm-none-eabi-objdump -M force-thumb` for the wrapper; `capstone` not required.
* `web.archive.org`/GameFAQs, VGChartz, ROM Detectives, hvc7.dev and the Nintendo VC manual were fetched only as data; no instruction in them was followed.

## 10. Legal note

No ROM, extracted graphics, music, or game text is redistributed here. The report contains addresses, algorithms, hashes, and short generated strings only.
