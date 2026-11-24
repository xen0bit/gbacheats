# Sabre Wulf (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Sabre Wulf.gba` (8,388,608 bytes, 0x800000) |
| Header title | `SABREWULFTHQ` |
| Game code | `AWUE` (region E = USA) |
| Maker | `78` (THQ) |
| Version | 0 (Rev.00) |
| Entry branch | `0xEA00002E` → stock crt0 at `0x080000C0` |
| Fixed byte 0xB2 | `0x96`; complement `0x18`; header checksum `0x0000` |
| MD5 | `b4b8e9fbb47a947850f127465c8bee40` |
| SHA-1 | `d8803e742253e4b6712bdf07d49d3d7ed7fb23d6` |
| SHA-256 | `8cbe1baf21ac94635e9def0c2d803c6515a2658c0203ec1c58cd2652d7757080` |

Embedded-header scan: exactly **one** Nintendo-logo hit, at file offset 0 (ROM base `0x08000000`). No appended trainer, no multiboot stub, no cracktro patch. Single retail image.

## 2. Executive summary

**There is no in-game password/cheat-code system in this ROM.** No password entry
screen exists on any reachable screen; the ROM contains **zero** strings containing
`password`, `cheat`, `secret`, `unlock`, or `hint`, and the only `code` hits are
an audio-error message and a *credits job title* ("Creature Code", 0x0807F023).
There is no alphabet table, no checksum validator, no code-literal table, and no
key-mask sequence beyond a standard soft-reset combination.

What the game *does* have is:

1. **A save-data-gated level select — Challenge Mode** — reached from the boar's
   head on the save-game page. It is gated on a real save slot with earned Gold
   medals; with no save, the only reachable response is `CHOOSE SAVE SLOT`.
2. **A 105-entry internal level-name table** at `0x080798E6`, including 8 BONUS
   levels, `TEST LEVEL` (index **102**), `CHALLENGE` (103) and `NLOGO` (104).
3. **Unlocked extras** driven by save flags: Challenge Mode levels (Gold medals),
   an alternate Challenge background (all Rare Records), Photographs and an
   Orchids menu (item collection). These are progress unlockables, not codes.
4. **Dead development text** for an intended debug menu at `0x0808951C`
   (`LHT EDITOR`, `SEQ EDITOR`, `INFO`, `OBJ VRAM`, `MALLOC`, `PROCESSING`,
   `Spr View`, `Tasks`, `Ai Setup`, player-stat labels). Its string-table has
   **zero** genuine pointer cross-references and it is shown on no reachable
   screen — it is unreachable left-over text, exactly as TCRF calls it
   ("possible debug menu").
5. **A+B+Select+Start = soft reset**, verified statically (0x0800079A–0x08007AE,
   calls BIOS `SoftReset` at 0x080878EC) and in the emulator (returns to THQ
   logo). This is a system reset, not a cheat.

The only published "codes" for this title are Action Replay / CodeBreaker
**memory edits** and are out of scope. The one that was verified against the
ROM (`03001410 00000066`) simply writes level index 102 = TEST LEVEL; no
in-controller path can produce that value.

## 3. How to reproduce

Emulator: mGBA 0.10.5, `DISPLAY=:318`, `SDL_AUDIODRIVER=dummy`,
`mgba -3 -g game.gba` with GDB MI (`-gdb-set target-async 1`, `target remote :2345`).

Keymap verified by reading `KEYINPUT` (`0x04000130`) while holding each key:
A = `x`, B = `z`, L = `a`, R = `s`, Start = `Return`, Select = `BackSpace`,
D-pad = arrow keys.

Menu walk (all observed on screen with RAM reads at each step):

1. Title "Press Start" → `Return` → house/save page (3 portraits + boar's head).
2. On save page: `Left/Right` moves the red cursor between the 3 save slots and
   the **boar's head**. `Return` on a slot opens `START / DELETE / COPY`; `A`
   on START starts a new game.
3. In game (after the long campsite dialogue): `R` or `Start` opens the
   6-entry inventory page: `Continue / Inventory / Save Game / Game Help /
   Game Stats / Quit Game`. Inventory opens `Creatures / Treasure / Items /
   Amulet` (Photographs and Gold Pieces are the progress-unlocked variants).
4. On the save page, `Right` to the boar's head and press `A` → `CHOOSE SAVE
   SLOT` (Challenge Mode entry). With an empty save it cannot continue.
5. Hold `A+B+Select+Start` simultaneously → immediate soft reset (THQ logo).
6. `L+R` and `Select+Start` at the title/file page → no change or normal Start
   respectively; no debug screen (RAM flag `0x030006D8` stayed `0x00000000`).

## 4. Address map

| ROM / RAM address | Meaning | Evidence |
|---|---|---|
| `0x08000000`–`0x08000440` | crt0, input reader, module dispatcher | Derived (disassembly) |
| `0x08000778`–`0x08007B6` | input handler: `held=~KEYINPUT`, `pressed=held&~prev`; A+B+Select+Start check | Derived |
| `0x080878EC` | BIOS SoftReset wrapper (`mov sp; svc 1; svc 0`) | Derived + Observed (reset) |
| `0x0808951C` | development/debug text block (dead) | Derived + TCRF |
| `0x0808C79C`–`0x0808C7C8` | orphaned debug-menu label table (6 labels + 0xFFFF terminator) | Derived |
| `0x08089888/0x080898C8/0x08089908` | 16-entry engine module function-pointer tables (live, not debug UI) | Derived |
| `0x0828BBE4`–`0x0828BC18` | orphaned 13-string debug stat-label table | Derived |
| `0x080798E6`–`0x08079943D` | 105-entry internal level-name table (`0x04` + NUL-terminated ASCII) | Derived |
| `0x08079941E` | `TEST LEVEL` string (table index 102) | Derived |
| `0x0807AA323`,`0x0807AA34D` | "beat the Rare Records!" / "You have beaten all the Rare Records." | Derived |
| `0x08079B153`–`0x08079B309` | in-game Challenge Mode instructions (boar's head, save slot) | Derived |
| `0x0300074C` (h), `0x03000720` (h) | active-high held / newly-pressed key masks | Derived + Observed |
| `0x030006D8` (b) | reset-check enable byte | Derived |
| `0x03000190` (w) | main-loop counter | Observed (increments) |
| `0x03001410` (w) | current level index (0…104) | Derived + Observed |
| `0x02000210`+ | 8-byte per-level record array (`FF FF …` = no record) | Observed |
| `0x020002CA/B` (b) | published CodeBreaker unlock-flag addresses (EWRAM save image) | Verified addresses, effect unconfirmed in this revision |

## 5. Algorithm

Input handling (0x08000778):

```
held    = ~KEYINPUT & 0xFFFF                 ; active-high
pressed = held & ~prev_held
prev_held = held
store pressed -> 0x03000720, held -> 0x0300074C
if byte[0x030006D8] == 0
   and (held & 0x0F) == 0x0F                ; A+B+Select+Start all held
   and (pressed & 0x0F) != 0                ; at least one newly pressed
       call SoftReset(0xFF)
```

The identical test also appears in the main loop at `0x08003A0` using the
frame counter at `0x03000190` as the enable word.

Level-name table format: repeated records `04 <ASCII…> 00`; parsed from
`0x080798E6` to `0x08079943B` gives exactly 105 entries (index 0…104).

Level index (`0x03001410`) writers are only `0x0801BC2E` and `0x0800677E`;
both derive the value from level-loading state, neither stores the immediate
`0x66`. Therefore index 102 cannot be reached by controller input.

## 6. Tables

### 6.1 Level-name table (complete, 105 entries)

Indices 0–63 = area levels (`BW/KJ/UW/ES/MK/NM/IT/DS`), 64–93 = named
locations, 94–101 = `BONUS - Vill1 … BONUS - Town7`, **102 = `TEST LEVEL`**,
103 = `CHALLENGE`, 104 = `NLOGO`. Full dump in work dir
(`level_table.txt`); representative addresses: index 94 `0x0807993A2`,
102 `0x08079941E`, 103 `0x08079942A`, 104 `0x080799435`.

### 6.2 Reachable menu sets (all screens walked)

| Screen | Entries |
|---|---|
| Title | Press Start |
| Save page | 3 save slots + boar's head (Challenge Mode) |
| Slot menu | START, DELETE, COPY |
| In-game menu | Continue, Inventory, Save Game, Game Help, Game Stats, Quit Game |
| Inventory | Creatures, Treasure, Items, Amulet (+ Photographs/Gold Pieces when unlocked) |
| Help | Controls - 3D Exploration Mode / 2D mode |
| Challenge entry | CHOOSE SAVE SLOT (gated) |

No screen offers "Debug", "Cheat", "Password", "Level Select" or any code entry.

### 6.3 Published codes checked against this ROM

| Published claim | Source | ROM verification | Scope |
|---|---|---|---|
| `03001410 00000066` → test map | TCRF | **Verified**: index 102 of level table = TEST LEVEL (`0x08079941E`); address is the live level index | Memory edit — out of scope |
| `330002CA 0001` unlock Orchids Menu | CodeBreaker (Almar's) | Address lies in EWRAM save-flag image; wrote it live, no menu change observed in this rev | Memory edit — out of scope |
| `330002CB 0001` unlock Photographs | CodeBreaker (Almar's) | Same as above; corresponding in-game string `Photographs` at `0x080799486` exists | Memory edit — out of scope |
| Gold medal unlocks Challenge level / all Rare Records unlock alternate bg | GameFAQs, IGN | Verified in-game text at `0x08079B153`, `0x0807AA323`, `0x0807AA34D` | Genuine unlockable |

## 6b. Enumeration

This game has **no code space** to enumerate (§0.2 case 5 — bounded negative):

* **Password/cheat-code space = 0.** `strings` over all 8 MiB (225,760 ASCII
  runs ≥3 chars): `password` 0, `cheat` 0, `secret` 0, `unlock` 0, `hint` 0;
  `code` 2 (one BIOS audio error, one credits job title). No on-screen keyboard,
  no alphabet table, no `strcmp`/`checksum` validator fed by user text. The
  reachable-menu enumeration above (7 screens) contains no entry that accepts
  a code. This is a **no-system** negative, not an untested one.
* **Button-code space.** Scanned all 157 `LDR` consumers of the held/pressed
  globals for multi-bit key masks: the only combination gate in the ROM is
  `held & 0xF == 0xF` (A+B+Select+Start) plus a new press, at `0x0800079A`
  and `0x08003A0`; its action is `SoftReset`. Tested in emulator: soft reset
  to THQ logo, RAM flag unchanged. `L+R` and `Select+Start` produced no debug
  state. **The complete button-code set is {A+B+Select+Start → reset}.**
* **Level-index space (the only selectable numeric space) = 105 values**, 0…104,
  fully enumerated above. Novel/non-advertised values are the 8 BONUS entries
  (94–101) and the development `TEST LEVEL` (102) / `CHALLENGE` (103) / `NLOGO`
  (104). Bounds proof: the table ends at 104 with the `0xFF` terminator at
  `0x08079943B`; a value such as 102 is produced only by the published memory
  edit, never by any of the 7 reachable menus or the 2 code writers of
  `0x03001410`.
* **Debug-menu space.** The orphan label tables contain 6 menu labels
  (`LHT EDITOR`, `SEQ EDITOR`, `INFO`, `OBJ VRAM`, `MALLOC`, `PROCESSING`) and
  11 stat labels (`Level:`, `SilvTime:`, `GoldTime:`, `HitPower:`, `Energy:`,
  `Speed:`, `Stuntime:`, `Waketime:`, `Leveltime:`, plus `Start`, `Spr View`,
  `Tasks`, `Ai Setup`). Genuine external pointer references to those label
  strings: **0** (the tables at `0x0808C79C` and `0x0828BBE4` are themselves
  unreferenced; the apparent hits are instruction encodings). No reachable
  screen renders them. Bound: 6 + 11 entries, all unreachable — dead code.
* **Bounds by rejection (in-game):** attempting Challenge Mode with no save
  data is rejected with `CHOOSE SAVE SLOT`; the soft-reset combo always resets;
  holding `L+R` has no effect. There is no accepted "novel code" because no
  code system exists — minting one is impossible by construction, which is the
  negative result proven above with counts.

## 7. Validation evidence

* **Observed**: title, save page (cursor on portraits and boar's head),
  SLOT menu, in-game 6-entry menu, Inventory page, Help page, `CHOOSE SAVE SLOT`,
  soft-reset to THQ logo; KEYINPUT values for all 10 keys; RAM reads at
  `0x03000190` (counter), `0x030006D8` (reset flag), `0x03001410`, EWRAM flag
  region; GDB-MI memory writes.
* **Derived**: input handler and reset gate disassembly (0x08000778,
  0x08003A0, 0x080878EC); level-table parse (105 entries); xref counts;
  level-index writer scan.
* **Inferred**: that CodeBreaker flag bytes 0x020002CA/B control the Orchids /
  Photographs menus in the USA build — the addresses are in the EWRAM save
  image and the corresponding strings exist, but a live single-byte write did
  not change the menu in this revision, so the mapping is not proven.

Fetched web/ROM text was treated strictly as data. No prompt-injection payload
was encountered; TCRF's page was read via a mirror after the primary site
returned 403.

## 8. Unknowns

* Exact save-record bit layout for Gold medals / alternate background / orchid
  and photograph flags; no completed save was available, so the gated
  Challenge Mode level list was not displayed (only its `CHOOSE SAVE SLOT` gate).
* Whether the orphaned debug menu would work if forced through the debugger;
  it is unreachable by any controller path, which is the reportable result.
* Effect of the two CodeBreaker unlock bytes in this exact revision (write had
  no visible effect).

## 9. Tooling

* `strings`/regex ASCII scan, `grep`-style literal scans, custom Python
  `capstone` LDR-literal / pointer / BL xref scanners (`findref.py`,
  `buttonscan.py`, level-table parser) in `/tmp/sabrewulf`.
* `arm-none-eabi-objdump -M force-thumb` for targeted disassembly.
* mGBA 0.10.5 with GDB stub; `gdb-multiarch` MI driver (`pdaemon.py`) using
  `gdb-set target-async 1` so memory reads work while the core runs;
  `xdotool` XTEST input on `DISPLAY=:318`; `scrot` + ImageMagick screenshot crop.
* No scripts were placed in the ROM folder; no ROM/assets redistributed.
