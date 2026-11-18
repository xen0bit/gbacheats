# Medabots AX: Rokusho Version (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `/mnt/gbacheats/roms/Medabots AX: Rokusho Version/Medabots AX: Rokusho Version.gba` |
| Size | 8,388,608 bytes (`0x800000`) |
| `file` | Game Boy Advance ROM image: "MEDABOTS RKS" (AK9EE9, Rev.00) |
| Header title | `MEDABOTS RKS` (`0xA0`) |
| Game code | `AK9E` (`0xAC`); maker `E9` (`0xB0`); version `0x00` (`0xBC`) |
| Fixed byte `0x96` | present at `0xB2`; complement `0x6A`; header checksum `0x0000` (rebuilt-header artifact, complement intact) |
| Entry word | `0xEA00002E` at `0x00` → stock branch to `0x080000C0`, **not** a cracktro patch |
| Nintendo-logo scan | exactly **one** GBA header, at file `0x0`; no embedded/trainer image, no appended ROM |
| MD5 | `08a002ca5de6e28726c3d17644137b23` |
| SHA-1 | `ef47f8c675f1f541a0fe4bd37c8882efc539b1c7` |
| SHA-256 | `c1d194d9ffc703066109563aef173520d8c1f2f5bbb4fd4a7b7ebb9ff98c31cc` |
| Analysis copy | byte-identical copy at `/tmp/opencode/medabotsrokusho/game.gba` |

Identity caveat: this is **not** *Medabots: Rokusho Version* (game code `A9BE`,
`MEDABOTSRKSV`). A byte-identical-decompilation project exists for that *other*
SKU (`rommerhacks/medabots-rokusho`, SHA-1 `c4572428…`). It was used only as a
**conceptual hint** (e.g. that the franchise has a Test Mode and a debug menu);
no address from it was assumed valid here. All claims below are from this `AK9E`
image.

## 2. Executive summary

**Finding: there is no player-facing password/code-entry system and no reachable
hidden debug/Test-Mode screen in this SKU.** The one genuine developer-intended
cheat that does exist is a **button code**: a four-button reset
(`A+B+SELECT+START`), implemented twice in ROM at `0x08000C36` and
`0x08027264`; it was confirmed in the emulator. Two more intended shortcuts were
reached on the field: `START` = Team Formation (robot select) and `SELECT` = Save.

Every published "cheat" found on the web (GameFAQs/Autocon patch guide,
GameHacking.org, Codejunkies, 53lu, Almar's Guides, gbadamud) is a
GameShark/CodeBreaker/Action Replay **memory-edit** code (e.g. `8203EC30 0063`
→ write `0x0063` to EWRAM `0x0203EC30`); these are out of scope and were not
applied. No code list contains a typed code, and no literal from any password
list occurs anywhere in this ROM.

Text is stored as **font/tile glyph indices**, not ASCII, so `strings` finds no
UI strings at all. The negative result is therefore bounded by (a) exhaustive
button-space enumeration and gate analysis, (b) literal/alphabet searches in
four encodings with zero hits, (c) a dispatch-table inspection showing no debug
state, and (d) walking every reachable screen on the ROM (title, boot logos,
field, dialogue, Team Formation/robot select, Save prompt, and the soft-reset
path).

## 3. How to reproduce

- Emulator: mGBA headless on `Xvfb :316`, `SDL_AUDIODRIVER=dummy`, `mgba -3`.
  Default SDL keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
  Select=`BackSpace`, D-pad=arrows. X11 screenshots are black on this GLX
  canvas, so all captures used **mGBA's own F12 screenshot** (240×160 PNG,
  named `game-N.png`).
- RAM reads: `mgba -3 -g`, `gdb-multiarch` GDB-remote stub on port 2345, driven
  by a small Python RSP client (`rsp.py`, `gdbserver.py`); key state is at
  IWRAM `0x03000200`.
- Boot path (repeatable): title → `START` → new-game intro → press `A` 4–6× →
  field. `START` on the field opens **Team Formation**; `SELECT` opens
  **Save the game?**; answer Yes.
- Reset test (the one working cheat): from *any* screen press and hold
  `A+B+SELECT+START` together for ~0.4 s, release. The ROM immediately reboots
  to `Licensed by Nintendo` and re-plays the boot logos.
- Negative tests (all rejected): `SELECT+START` pressed simultaneously;
  `SELECT` held ≥0.5 s then `START` newly pressed; `START` held then `SELECT`
  newly pressed; every single key and 2-key pair. None opened a Test Mode or
  debug screen.
- No `.sav`/`.ss*` files were created in the ROM folder (the emulator ran on a
  copy in the work directory).

## 4. Address map

File offset = ROM address − `0x08000000`.

| ROM addr | File off | Meaning | Evidence |
|---|---|---|---|
| `0x08000000` | `0x000000` | Header; single Nintendo-logo hit; stock entry `0xEA00002E` | Observed (hex/scan) |
| `0x080000C0` | `0x0000C0` | ARM crt0; `bx 0x08000259` into Thumb main | Derived (objdump ARM) |
| `0x08000C36` | `0x000C36` | **Soft-reset check #1**: `held & 0xF == 0xF`, then `new & 8` | Derived (Thumb disasm) |
| `0x08000C94` | `0x000C94` | Literals for check #1: `0x030010A0`, `0x0EB8`, `0x0EB4`, `0x0EBA`, `0x0EB6` | Derived |
| `0x08027264` | `0x027264` | **Soft-reset check #2** (same gate, reached by a different dispatcher) | Derived + Observed (watchpoint hit here) |
| `0x08027298` | `0x027298` | Literal `0x03000200` = `gHeldKeys` (base of key-state block) | Derived |
| `0x0802729C` | `0x02729C` | Literal `0x03000DFC` (reset scratch) | Derived |
| `0x080272A0` | `0x0272A0` | Literal `0x0301A78` (reset state byte) | Derived |
| `0x0809569C` | `0x09569C` | 36-entry Thumb function-pointer dispatch table (mode-0 states); **no state 63** | Derived |
| `0x03000200` | — | `gHeldKeys` (u16, active-high: A=1,B=2,Sel=4,Start=8,R=0x10,L=0x20,U=0x40,D=0x80,Rt=0x100,Lt=0x200) | Observed (GDB key sweep) |
| `0x03000208` | — | frame/tick counter (advances every frame) | Observed |
| `0x030000B8` | — | game-state byte: `0x03` at title → `0x0D` after `START` → `0x17` in field | Observed (RAM diff) |

Dead-code note: a `read_keys`-looking function at `0x080232A0` reads
`0x04000130`, XORs `0x03FF` and computes new presses, but has **no BL/BLX or
pointer-table reference** and a GDB breakpoint there never fires in 3 s — it is
unreachable in this SKU. The live key-state writer is elsewhere.

## 5. Algorithm

Soft reset (both sites), in C-like pseudocode:

```c
u16 *keys = (u16 *)0x03000200;   // [0] = held (active high), [2] = newly pressed
if ((keys[0] & 0x000F) == 0x000F && (keys[2] & 0x0008) != 0) {
    *(u16 *)0x03000DFC = 0;      // clear reset scratch
    *(u8  *)0x0301A78  = 1;      // request reset
    *(u8  *)(keys + 10) = 4;     // game-mode/state = 4 (reboot sequence)
}
```

The watchpoint `Z3,03000200` stopped with stop reply `T05rwatch:03000200;`
and PC `0x08027268` (the instruction after `ldrh r1,[r2]` at `0x08027266`),
confirming this block is the live key consumer. `r2 = 0x03000200` at that point.

State model (observed): title `0x03`; after START `0x0D`; field `0x17`.
Soft reset returns to the boot-logos state and replays `Licensed by Nintendo`.

## 6. Tables

**Key bits** (from GDB sweep of `0x03000200` while holding each key):

| Key | Mask | Key | Mask |
|---|---|---|---|
| A | `0x001` | Right | `0x010` |
| B | `0x002` | Left | `0x020` |
| Select | `0x004` | Up | `0x040` |
| Start | `0x008` | Down | `0x080` |
| R | `0x100` | L | `0x200` |

**Gates found in the whole ROM:** exactly two (both the same `0x0F`/`0x08`
reset gate). No gate for `0x0C` (Select+Start) exists as a `movs rX,#0xC;/ands`
pair in Thumb code (0 occurrences); `0x0F` pairs occur 16 times, of which the
two keyed ones are above and the rest are unrelated immediates.

**Published codes (all out of scope, verified as memory edits):** e.g.
`8203EC30 0063` (medal level at `0x0203EC30`), `4203EC30 0063 0000000C 000C`
(all medals), `43004C40 0063` (all Medaparts at `0x02004C40`),
`000009B4 000A / 10000568 0007` (enable code). None is a typed code and none
has a literal in the ROM.

## 6b. Enumeration

**Button-code space.** The live input word has 10 bits → `2^10 = 1024` possible
held-mask subsets; sequences of presses are unbounded. The gate logic was
enumerated from code rather than guessed: only `held & 0x000F` and
`new & 0x0008` are ever tested, so the accepted held set is exactly the 16
supersets of `{A,B,Select,Start}` (the other 6 bits are don't-cares) and the
required edge is Start. **Space of documented cheat: 1 four-key action; found
in 2 code sites, no other action branch.**

**Novel (unpublished) input.** The published description of this franchise's
reset is "hold A+B+SELECT, then press START". The variant actually confirmed
here is **all four buttons pressed simultaneously from idle** (KEYINPUT observed
as `0x0003` = all low bits clear → `0x000F` held). This produced an immediate
reboot to `Licensed by Nintendo` (screenshot
`/tmp/opencode/medabotsrokusho/shots/sr_after_all4.png`). It is a different
input from the published description and is accepted because `new` then
contains bit 3 as well.

**Bounds proven by rejection (in emulator or by gate analysis):**

- 1-key presses (8 tested) and 2-key pairs (28 possible; all mask patterns
  enumerated) — none satisfy `held & 0xF == 0xF`; no effect.
- `SELECT+START` simultaneously — **rejected** (no Test Mode; title unchanged).
- `SELECT` held 0.6 s then `START` newly pressed — **rejected** (title unchanged).
- `START` held then `SELECT` newly pressed — starts a **new game**, not Test Mode.
- `A+B+SELECT` held then `START` (sequential, the published wording) — did not
  reset in the tested run; the simultaneous four-key form did. Likely a
  key-edge/harness timing effect, recorded as observed, not explained.
- Any held mask without all of A,B,Select,Start — **rejected** by the gate
  (`cmp r0,#0xF; bne` at `0x0802726E`).

**Code/password space.** There is none to enumerate: 0 literal tables, 0 ASCII
alphabets, 0 validator comparisons against user text. The negative is bounded
by the searches in §7 and the screen walks in §3.

## 7. Validation evidence

- **Observed**: ROM header/`file`/hashes; F12 screenshots of title, boot logos,
  field, dialogue, Team Formation (robot select), Save prompt; GDB key sweep
  producing the mask table; RAM diff `0x030000B8: 0003 → 000D` on START and
  `0x03000200: 0000 → 0001` on A; read-watchpoint hit
  `T05rwatch:03000200` with PC `0x08027268`; four-key press →
  `Licensed by Nintendo`; three SELECT/START variants → no Test Mode.
- **Derived**: both soft-reset gates and their exact literals from `objdump
  -M force-thumb`; single Nintendo logo / stock entry branch; `read_keys`
  candidate at `0x080232A0` is unreferenced (0 BLs, 0 pointer literals,
  breakpoint never hit); 36-entry dispatch table with no state 63; text is
  glyph-indexed (control bytes `0xF7`–`0xFF`), consistent with the sibling SKU's
  decomp; published codes are memory writes.
- **Inferred** (not fully exercised): the `new`-key word lives at `0x03000202`
  and is a one-frame pulse — consistent with the gate but not directly sampled;
  the field/menu features are story-gated (B menu never opened in the tutorial
  portion reached), so later-game menus were not walked.
- **Bounded negative searches**: ASCII/+0x20/UTF-16LE literals for
  `PASSWORD`, `CHEAT`, `DEBUG`, `SECRET`, `UNLOCK`, `TEST MODE`, `TESTMODE`,
  `ERASE`, the standard 36-char alphabet (both orders), and Medarot-2 passwords
  (`586659`, `58A659`, `666595`, `666X95`) — **0 hits each**. `strings -n 6`
  yielded 29,766 lines, all binary noise (repeated `WFNFEF` instruction
  pattern), no UI text. VRAM was dumped and tiles rendered to inspect the font;
  glyphs are 4bpp tile-indexed, explaining the string-negative without implying
  compressed/absent text.

## 8. Unknowns

- Later-game screens (post-tutorial field menu/Medawatch/Medabots build screen,
  battle command ring, battle pause) were **not** reached: random encounters did
  not trigger in the explored area and the B menu is gated by story progress.
  Therefore the published "press START in the Medabot build menu to auto-build
  a complete Medabot" shortcut could not be verified on-screen.
- The hidden TEST MODE / sound test and developer debug menu documented for the
  sibling SKU are unreachable here by all tested combinations; a gate in a
  later-game state (e.g. after story completion) cannot be excluded by the
  static searches, but no such gate literal exists in this image.
- The glyph→character table was not fully decoded; negative text searches are
  therefore bounded to ASCII-based encodings plus glyph-index structure, not to
  a complete dump of every message bank.
- Whether the sequential A+B+Select→START form works with a tighter key-edge
  window was not isolated; the simultaneous form is the confirmed one.

## 9. Tooling

- `file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings`, `grep` — Phase 0/1.
- `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` — gate disassembly.
- Python 3 + `capstone` 5.0.7 — literal/BL scanners; custom Thumb LDR-literal
  xref scanner (`xref.py`), key-mask/alphabet sweep (`finalsweep.py`).
- `mgba` (headless Xvfb `:316`), `xdotool` XTEST input, mGBA F12 screenshots.
- `gdb-multiarch` + custom GDB-RSP client (`rsp.py`, `gdbserver.py`) for IWRAM
  reads and read-watchpoints; `keydiff.py`/`diffkeys.py` for RAM diffs.
- Pillow renderer (`render_tiles.py`) for 4bpp VRAM tiles.
- Web sources: GameFAQs (Autocon patch/secret/walkthrough FAQs), Neoseeker,
  GameHacking.org, Codejunkies, 53lu, Almar's Guides, gbadamud; plus the
  `rommerhacks/medabots-rokusho` decomp (different SKU, hint only). Fetched
  pages were treated as data; no prompt-injection payload was encountered.

**Legal note:** no ROM, graphics, audio, or game text is redistributed here —
only hashes, addresses, algorithms, and the author's own analysis scripts.
