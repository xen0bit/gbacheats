# Rayman 10th Anniversary – Rayman Advance & Rayman 3 (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Rayman 10th Anniversary - Rayman Advance & Rayman 3.gba` |
| Size | 16,777,216 bytes (`0x01000000`, 16 MiB) |
| Header title / code / maker / version | `RAYMAN 10TH` / `BX5E` / `41` / `0` (rev.00) |
| Header entry | `0xEA00002E` (stock ARM branch to header+`0xC0`) |
| Fixed byte / complement / checksum | `0x96` / `0xF3` / `0x0000` |
| MD5 | `5087e6801cf5269976968026127a3288` |
| SHA-1 | `1983c17260f5707b26702c3ab1b6c86332365e05` |
| SHA-256 | `504a09717ad1cd37cb27da31f1ef9e034236684d5ecf62feba707c84f8486b2b` |

**Embedded GBA-header scan** (exact 156-byte Nintendo logo at header+4) found **three** headers:

| File offset | Linked base | Title | Game code | Maker | Interpretation |
|---:|---:|---|---|---|---|
| `0x000000` | `0x08000000` | `RAYMAN 10TH` | `BX5E` | `41` | compilation boot shell / common engine |
| `0x0B3F80` | `0x080B3F80` | `RAYMAN` | `ARYE` | `41` | Rayman Advance half |
| `0x09941A8` | `0x089941A8` | *(blank)* | `AGBJ` | `01` | Rayman 3 half (title bytes patched to NUL by the pack) |

All three have the stock `0xEA00002E` entry word; no appended trainer, no cracktro, no patched entry point was observed. The two playable halves are not 8 MiB-aligned; bases were derived from the logo hits, not assumed. Code/strings from Rayman Advance live between `0x0B3F80` and `0x9941A8`; Rayman 3 code/data lives from `0x9941A8` to EOF. A shared/common engine (input, menus, text rendering) lives in the shell region near `0x0`.

## 2. Executive summary

**Rayman Advance has a genuine developer-intended button-code system** with exactly six 6-press sequences, entered while the in-game quit/pause confirmation is on screen. The sequences are stored as active-high GBA key masks at ROM `0x083EEEA0` (36 halfwords, 6×6). A single validator at `0x080BDD48` implements a strict "next key must differ from previous key" state machine with a 0xFF idle sentinel, then dispatches through a **six-entry** jump table at `0x080BDDF0`. All six branches were enumerated statically and verified in the emulator by write watchpoints (and visually for 99 lives). The whole accepted space is those six strings — there is no generator and no seventh branch, so no novel *accepted* sequence exists; this is proven by the table size and the `cmp r0,#5` / `cmp r1,#5` bounds in the validator, plus rejected near-miss inputs.

A separate world-map combination (published as Select+B+R twice, "all electoons") was observed to call `0x080DBD74` → `0x080CBF98`, which mutates the 24-byte world-map progress array at `0x0200CFA0` and the counter at `0x0200C5D8`. A control input (Select+B twice) produced zero RAM changes. The exact semantic label of the array is inferred, not visually confirmed.

**Rayman 3** has four published world-map codes (held Select + button sequence) and a published main-menu debug chord. In this 16 MiB compilation, literal searches over the whole image found **no** copy of any published code sequence (u8/u16/u32, active-high/active-low/held-Select forms, key-index encoding), and the debug chord produced no state change at either the main menu or the save-slot screen. The world-map screen itself is gated behind story progression (it is the hub reached after completing a level), so in-game code entry could not be performed from a fresh save in this session; this is reported as a **gated feature** with the gate and the bounded search recorded, not as "no cheats".

Published PS1/GBC Rayman passwords (`942KV7N9XD`, `CH5G4mS1jD`, etc.) belong to other SKUs and are **not** accepted by either GBA half; the `/password/` string bank at file `0x351F6C`–`0x356630` is PC/PS1 debug leftovers in the Rayman Advance half (it mentions memory cards, joysticks and the X button), not a GBA entry screen.

## 3. How to reproduce

* Emulator: `mgba` (SDL), `DISPLAY=:318`, `SDL_AUDIODRIVER=dummy`, `Xvfb :318 -screen 0 1280x960x24`, `openbox`. We copied the ROM to `/tmp/rayman10/game.gba` so no emulator artifacts touch the ROM folder.
* Keymap (mGBA SDL): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrow keys. Hold 90–120 ms per press; savestates: `Shift+F1` save, `F1` load (and `mgba -t <state> game.gba` to boot into a saved screen).
* Boot → "PRESS START" → Start → picture-frame game select → left picture = Rayman Advance, right = Rayman 3.
* **Rayman Advance path to the code screen:** Start → choose language (A) → Sound options (A) → "CHOOSE A GAME" → A on an EMPTY slot (creates `AAA`, 5 lives) → Start → cutscene (A to skip) → world map → A → A to skip the level intro → gameplay → **Start** opens "DO YOU REALLY WANT TO QUIT THE GAME?" — this is the pause/quit dialog on which the six codes are entered. Enter the 6 presses, then B selects NO/return to play (note: some code prefixes move the YES/NO cursor; check the screen before pressing B).
* Verified 99-lives code on that screen: **Left, Right, Down, Right, Left, R** → HUD changes from `x05` to `x99` (screenshots `s27_ra_code99.png`, `s28_ra_lives99.png`).
* **Watchpoint recipe (mGBA CLI debugger `-d`):** start with `-d -t <state>`, at the paused prompt run `watch/w <addr>` then `c`, press the sequence, and read the `Hit watchpoint … r15: …` line from the debugger log. This produced the PC/flag evidence in §5–§6.
* **Rayman 3 path:** right picture → intro → language (A) → main menu (SINGLE PLAYER / MULTIPLAYER / OPTIONS) → SINGLE PLAYER → link screen (use SINGLE PAK LINK is *not* the offline path) → save slots → A on a slot → intro cutscene → level 1. Pause = Start (CONTINUE / SLEEP MODE / QUIT); QUIT→YES returns to the **main menu**, not the world map. The world map was not reached from a fresh save.

## 4. Address map

File offset `F` ↔ ROM address `0x08000000 + F`.

| Item | ROM / file address | RAM | Evidence |
|---|---|---|---|
| RA cheat sequence table (6×6 u16 masks) | file `0x3EEEA0` = `0x083EEEA0` | — | watchpoint `r6 = 0x083EEEA0` |
| RA validator entry | `0x080BDD48` (file `0xBDD48`) | — | BL caller `0x080FFB24`; watchpoint PC `0x080BDE94` |
| RA first-key/literal pool | `0x080BDD80`–`0x080BDDC2` | — | `0x02000094`, `0x02031540`, `0x083EEEA0`, `0x020010EC` |
| RA dispatch jump table (6 entries) | `0x080BDDF0` | — | `ldr r1,=0x080BDDF0; ldr r0,[r0]` |
| RA handlers 0..5 | `0x80BDE08 / 14 / 1C / 44 / 58 / 6C` | — | disassembly |
| RA progress byte | — | `0x02000094` (`0xFF`=idle) | watchpoint, literal `0x080BDD80` |
| RA current code index | — | `0x020010EC` | watchpoint `r7` |
| RA active-low key state | — | `0x02031540` | validator `ldrh` |
| RA lives / tings base | — | `0x0200CF60` (`+6` = 25-ting counter) | watchpoints `0x0200CF66`, `0x0200CF60` |
| RA invincibility toggle | — | `0x02000030` | watchpoint |
| RA powers bitfield | — | `0x02009FA4` / `+1` | watchpoint |
| RA level-unlock toggle | — | `0x02001100` | watchpoint |
| RA health byte | — | `0x0200DDB4` | watchpoint |
| RA world-map code chain | `0x080DBD74` → `BL 0x080CBF98` | `0x0200CFA0..B7`, `0x0200C5D8` | watchpoints |
| RA debug-menu gate (leftover) | `0x080BDF00` (called `0x080B9CE6`) | `0x0200C5C0` | disassembly, not triggered |
| R3 key state (active-low) | — | `0x03000E94` | savestate held-key diff (`0xFC00`→`0xFD05` for Select+R+A) |
| R3 lives | — | `0x0203FFF6` | gameplay savestate shows `0x03` |
| R3 common key pointer literal | `0x080001B4` = `0x03000E90` | — | crt0 literal pool |
| Text bank with PC/PS1 leftovers | file `0x351E80`–`0x356630` | — | ASCII strings with `/…/` and `-I` suffixes |

## 5. Algorithm

Rayman Advance validator, reconstructed from `0x080BDD48` (Thumb):

```
keys = ldrh [0x02031540]            # active-low KEYINPUT mirror
p    = ldrb [0x02000094]            # 0xFF = idle, else 1..5 = presses matched
m    = keys & 0x3F0                  # only D-pad + L/R (A,B,Select,Start ignored)
if m == 0: return
if p == 0xFF:                        # waiting for first press
    for c in 0..5:                   # c <= 5 check at 0x080BDD7A
        if m == u16[0x083EEEA0 + 12*c]:      # first mask of code c
            [0x020010EC] = c; [0x02000094] = 1; return
    return
c = [0x020010EC]
if m == u16[0x083EEEA0 + 12*c + 2*(p-1)]: return   # same key as previous: debounce
if m == u16[0x083EEEA0 + 12*c + 2*p]:
    [0x02000094] = p+1
    if p+1 <= 5: return
    [0x02000094] = 0xFF
    sound(8)
    dispatch[c]()                    # table at 0x080BDDF0
else:
    [0x02000094] = 0xFF              # wrong key resets progress
```

Consequences (all confirmed by watchpoints): a key must be *released and changed* to advance; the same mask twice in a row is ignored; any out-of-place mask resets to idle; `A/B/Select/Start` presses do not disturb an in-progress cheat.

R3: no equivalent table/validator literal was located; see §8 for the bounded negative.

## 6. Tables

### 6.1 Rayman Advance — complete code space (ROM `0x083EEEA0`, 6 entries × 6 halfwords)

Mask encoding is **active-high** (`~KEYINPUT & 0x3FF`): `A=1, B=2, Sel=4, Start=8, Right=0x10, Left=0x20, Up=0x40, Down=0x80, R=0x100, L=0x200`.

| # | Masks (press order) | Effect | Handler | RAM write (watchpoint-confirmed) |
|---:|---|---|---|---|
| 0 | `Left, Right, Down, Right, Left, R` | 99 lives | `0x080BDE08` | `strh 99` → `0x0200CF60` (HUD `x99` observed) |
| 1 | `Right, Up, Right, Left, Right, R` | Invincibility (toggle) | `0x080BDE14`→`0x080BDE46` | `0x02000030` toggled `0x00→0x01` at `0x080BDE52` |
| 2 | `Down, Left, Right, Left, Up, L` | All powers | `0x080BDE1C` | `0x02009FA4 = 0x87`, `+1` OR `0x05`, PC `0x080BDE36` |
| 3 | `Up, Left, Right, Down, Right, L` | Unlock all levels (toggle) | `0x080BDE44` | `0x02001100` `0x00→0x01` at `0x080BDE54` |
| 4 | `L, Down, Left, Up, Down, R` | Restore health | `0x080BDE58` | `strb [0x0200DDB4] = [0x0200CF60+9]`, PC `0x080BDE64` |
| 5 | `R, Up, Left, Right, Left, L` | +25 blue tings (cap 99) | `0x080BDE6C` | `0x0200CF66` `0x00→0x19` at `0x080BDE90` |

Note the first element of code 0 is **D-pad Left (`0x20`)**, not L-shoulder. Several published lists prepend an L-shoulder or omit it; the ROM table and the in-game test both show the 6-press form above.

### 6.2 Rayman Advance — world-map combination

* Published: highlight a level, press **Select+B+R simultaneously, twice** → "all electoons in that level" (3rd party cheat indexes).
* Observed: from `st_map_pre_ss.ss1`, the chord changed EWRAM `0x0200CFA3`, `0x0200CFA6`…`0x0200CFB8`, `0x0200D018`…`0x0200DA85`, `0x0200C5D8` (`0x0F→0xAF`) and `0x0200DDA9`. Watchpoints put the writer at `0x080CBF98`, called from `0x080DBD78` (`BL 0x080CBF98` with `r0=1`). `0x080CBF98` increments a 24-byte array at `0x0200CFA0` and adds `r0` to the 32-bit word at `0x0200C5D8`.
* Control: holding Select+B only (twice) produced **no** EWRAM or IWRAM difference — the effect is specific to the full chord.
* Confidence: effect **Derived** (writer chain) + **Observed** (RAM deltas); the mapping of the 24-byte array to "electoons per level" is **Inferred**.

### 6.3 Rayman 3 — published codes (web-corroborated, not ROM-literal-verified)

Sources: 3rd party cheat indexes GBA cheat page, 3rd party cheat indexes "List of cheats in Rayman 3 (Game Boy Advance)", 3rd party cheat indexes. All are entered **on the world map while holding Select**:

| Effect | Buttons |
|---|---|
| All powers | `R, A, A, A` |
| 99 lives | `B, B, B, A, A, A` |
| Unlock all levels | `Up, Left, Down, Right, B, A, L, R` |
| 100 % completion + all powers + 99 lives | `Down, Up, Down, Up, A, Left, B, Right` |

Debug mode (main menu / save-slot screen): hold `Left+Up+Select+L+B`; then `Left+Down+Select+Start` (overwrite slot 1), `L+R+Select+Start` (debug info), `L+Left+Select+Start` (region toggle). Prototype-only codes (`L` on title, `L+Select`, `R+Select`) are explicitly **not** in this retail compilation.

ROM verification: literal searches for masks `0x104/0x5/0x5/0x5`, `0x6/0x6/0x6/0x5/0x5/0x5`, the 8-press sequences, active-low forms, byte-index forms (`0=A…9=L`) and 16/32-bit packings found **no** table in the whole 16 MiB image (only isolated hits inside high-entropy compressed data). The debug chord mask `0x266` and its active-low complement `0x199` occur at code-referenced literal positions only in unrelated data (`0x0805F696` loads `0x199` as a non-input argument).

### 6.4 Published-code verification ledger

| Published claim | ROM check | In-game check |
|---|---|---|
| RA 99 lives `Left,Right,Down,Right,Left,R` | literal table `0x083EEEA0`; handler `0x080BDE08` | **Confirmed** (`x05`→`x99`, HUD screenshot) |
| RA invincibility `Right,Up,Right,Left,Right,R` | table entry 1 | **Confirmed** by watchpoint (`0x02000030` 0→1) |
| RA all powers `Down,Left,Right,Left,Up,L` | table entry 2 | **Confirmed** by watchpoint (`0x02009FA4=0x87`) |
| RA unlock all levels `Up,Left,Right,Down,Right,L` | table entry 3 | **Confirmed** by watchpoint (`0x02001100` 0→1) |
| RA +25 tings `R,Up,Left,Right,Left,L` | table entry 5 | **Confirmed** by watchpoint (`0x0200CF66` +25) |
| RA restore health `L,Down,Left,Up,Down,R` | table entry 4 | **Confirmed** by watchpoint (`0x0200DDB4` write) |
| RA "99 lives" variant with leading L-shoulder | absent from table (would reset matcher) | not a valid 6-press form; recorded as a published-list error |
| RA all-electoons map chord | no literal table; writer chain located | RAM effect observed; visual effect inferred |
| R3 four world-map codes | no literal found in 16 MiB | not reached (world map gated) |
| R3 debug chord | no comparator found | no effect at main menu or save slots in this build |
| PS1/GBC passwords | `/password/` bank is PC debug text; no GBA entry screen | not applicable to these SKUs |

## 6b. Enumeration

* **Space definition (Rayman Advance):** 6 fixed strings × 6 presses, alphabet = 10 button masks (`A,B,Select,Start,Right,Left,Up,Down,R,L`), of which the validator masks out A/B/Select/Start, leaving 8 effective symbols per press. Raw representable space is `2^30`-ish for arbitrary 6-press strings over the 8 accepted masks, but the validator accepts exactly **6** of them (measured: table count 6, dispatch bound `cmp r0,#5`, first-key loop bound `cmp r1,#5`). Each code toggles or saturates one flag field; there is no numeric payload, checksum or generator.
* **Complete enumeration:** every table entry, every dispatch branch and every handler is listed in §6.1. No unreachable/unlabelled entry exists: indices 0–5 are all referenced by the jump table at `0x080BDDF0`.
* **Novel code:** none can exist for this system — the accepted set is a closed 6-element table with no field to vary. A "novel combination" test was therefore performed as a **negative**: `Left,Right,Down,Right,Left,L` (last press L-shoulder instead of R) and `Left,Left,Left,Left,Left,Left` (control) produced no lives/powers/level/tings writes; re-entering an already active code simply re-runs its handler (no seventh branch). This is the closed-set result required by §0.2, not an omission.
* **Bounds proven by rejection:** wrong final mask → matcher resets to `0xFF` (no effect); pressing a single key repeatedly → held-key debounce at `0x080BDDA4` ignores it (no effect); Select+B-only control chord → zero RAM difference.
* **Rayman 3 space:** bounded by search, not enumerated: all 16 MiB scanned for 4 active-high/active-low forms × 3 integer widths × 2 encodings (mask and key-index) plus the `0x266`/`0x199` debug masks — no code table found; the entry surface is gated behind world-map progression.

## 7. Validation evidence

* **Observed:** boot/title/game-select, Rayman Advance language/sound/save-slot screens, world map, level intro and gameplay, pause/quit dialog, Rayman 3 intro/language/main menu/options/link/save slots/level/pause/quit; HUD `x05`→`x99`; savestate byte diffs; six write-watchpoint hits with PCs. Screenshots on disk: `/tmp/rayman10/s01…s82_*.png` (key ones: `s02_select_c.png`, `s28_ra_lives99_c.png`, `s30_ra_tings_effect_c.png`, `s66_r3_slots_real2_c.png`, `s75_r3_map_c.png`).
* **Derived:** validator disassembly at `0x080BDD48`, dispatch bounds, handler writes, table stride (`12*c`), mask filtering (`and #0x3F0`), world-map writer chain `0x080DBD74`→`0x080CBF98`.
* **Inferred:** semantic label of the 24-byte world-map array; that R3's published codes exist in this compilation (web + absence of literal table is not proof of absence of an algorithmic matcher); that the blank-title `AGBJ` header is the Rayman 3 half.

## 8. Unknowns

1. Rayman 3 world-map validation could not be exercised in-game: the hub is story-gated and QUIT returns to the main menu. A completed-level save (or a link-cable partner) would be needed to reach it; no memory patching was used to bypass this.
2. The exact meaning of the 24-byte `0x0200CFA0` array and `0x0200C5D8` counter is inferred; no visible "all electoons" indicator was captured on the map screen.
3. R3's debug chord and four map codes are published for other Rayman 3 SKUs; no implementation was located in this compilation's image. Whether Ubisoft removed them from the 2-in-1 build, or implemented them algorithmically in a compressed/relocated code path, is unresolved.
4. Save-slot/copy/erase flows and the Multi-Pak Link screens were walked visually but not exhaustively diffed; they contained no published code surface.

## 9. Tooling

* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for raw disassembly; Capstone 5.0.7 / Keystone for literal and BL scans.
* mGBA SDL (`-3`, `-d` CLI debugger, `-t` savestate boot). CLI debugger commands used: `watch/w`, `listw`, `dis`, `r/1`, `r/2`, `r/4`, `x/2`, `c`.
* `Xvfb :318`, `openbox`, `xdotool` XTEST key events, `scrot`, ImageMagick `convert`.
* Python helpers in `/tmp/rayman10/`: `k.py` (keys/screenshots), `ss.py` (zlib `gbAs` savestate decode + RAM dump/diff), `exp.py` (state→keys→state), `watchcode.py`/`watchcombo.py` (reproducible watchpoint experiments), `dbg.py` (FIFO debugger bridge), `all_strings.txt` (full `strings -t x` dump).
* Web search: 3rd party cheat indexes Rayman Advance/Rayman 3/10th Anniversary cheat pages, 3rd party cheat indexes, archived cheat collections. Fetched pages were treated as data; no instruction found in them was executed.

**Legal note:** no ROM or copyrighted asset is redistributed here; only hashes, addresses, algorithms and the analyst's own scripts/screenshots are recorded.
