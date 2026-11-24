# Konami Collector's Series: Arcade Advanced (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Konami Collector's Series: Arcade Advanced.gba` |
| Size | 4,194,304 bytes (0x400000) |
| `file` | Game Boy Advance ROM image: "KCS ARCADE" (AKCEA4, Rev.00) |
| Header title | `KCS ARCADE` (0x080000A0) |
| Game code | `AKCE` (0x080000AC) |
| Maker | `A4` (0x080000B0) |
| Version | 0x00; complement 0x27; header checksum 0x0000 |
| Entry word | `0xEA00002E` (stock ARM branch → 0x080000C0); no cracktro/trainer patch |
| MD5 | `e879e454a201eeeb31a942406048501a` |
| SHA-1 | `58bbf8c1e13e4dc594fdfe5357b4ceeab1dc0348` |
| SHA-256 | `c4a9b63ebabd8065fecd05aae245b3f7b3f656b0fd589df9983dad40b75393c7` |

**Embedded header scan (Nintendo-logo signature, 156 bytes at header+4):** five hits —
`0x000000` (main image), `0x309814`, `0x33AD4C`, `0x373574`, `0x3B1D34`.
All five carry the same title/code/entry word; the four at high offsets are the
multiboot/link "Multi Game Pak VS" images, not separate retail ROMs (confirmed in the
emulator: the `EXIT A BUTTON / NOT PREPARED` link-wait screen is drawn from that bank).

**Component games (6), from the `SELECT A GAME` screen:** Frogger, Scramble, Time Pilot,
Gyruss, Yie Ar Kung Fu, Rush'n Attack.

## 2. Executive summary

The cart contains **one shared in-game button code**, the classic Konami code, and no
password system, no alpha-numeric cheat entry, and no hidden debug menu. It is
implemented once in the main image (validator `0x08011348`, table `0x0804A354`) and
called from six per-game handlers, one per component game. Entering
`↑ ↑ ↓ ↓ ← → ← → B A` sets a single global completion flag in IWRAM
(`0x03007983`: `0x00 → 0x01`) and queues sound effect `0x9E` — the audible "ring"
described by GameFAQs. Each game reads that flag to apply its own reward
(extra lives / extra level / extra fights / enhanced graphics / autofire).

**Novel / unpublished finding:** the same code also works on the *compilation's global
game-select screen*, not just on each game's player-count menu as every published
list states. This was entered in the emulator and RAM-verified (flag `0x03007983`
flipped, sound `0x9E` queued). The accepted-input space is otherwise closed: the
table's only other tail (Select, Start) is unreachable because the progress index
always starts at 0 and the completion flag gates further input. Bounds were proven
by three in-game rejections (wrong final button, reverse code, Select+Start).

## 3. How to reproduce

* Emulator: mGBA (`SDL_AUDIODRIVER=dummy mgba -3 <rom>`), Xvfb `:315`, 1024×768×24.
* SDL keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`,
  D-pad=arrow keys. Hold each key ~120 ms, gap ~160 ms.
* Boot: Nintendo → MusyX → Konami logo → attract demos → title screen. Press
  **Start**, then **Start** again → `SELECT A GAME`.
* **Per-game path (published):** highlight any game (A), press **Start** to reach its
  player-count menu, then press `↑ ↑ ↓ ↓ ← → ← → B A`. A chime confirms.
* **Novel path (this report):** on `SELECT A GAME` itself press
  `↑ ↑ ↓ ↓ ← → ← → B A` — chime confirms; the flag is global and applies to
  whichever game is started next.
* RAM proof: save an mGBA savestate (Shift+F#) before and after the sequence,
  decompress the PNG `gbAs` chunk with zlib, and read IWRAM offset
  `0x7970` (pointer → `0x03007980`), then byte `+3` of that struct at raw state
  offset `0x20983`. Before `00`, after `01`. Sound queue at state offset
  `0x1D3CC`: `ff ff ff ff` → `9e 00 00 00`.
* Published codes tested: GameFAQs (all six games + addendum), CheatCC
  (Rush'n Attack "Up×2, Down×2, Left, Right, Left, Right, B, A, Start"), IGN.
  Every literal matches the ROM table. GameFAQs/IGN live pages 403; verified via
  Wayback snapshot `20260202024624` of the GameFAQs cheats page.

## 4. Address map

| Address (ROM unless noted) | Meaning |
|---|---|
| `0x08000000` | Main GBA header / ARM entry |
| `0x08011348` | **Konami-code validator** (Thumb). Called 6× |
| `0x08011368` | Literal: `0x0804A354` (code table pointer) |
| `0x0801136C` | Literal: `0x03007970` (pointer to state struct) |
| `0x080113A4` | Literal: `0x000003FF` (key mask) |
| `0x0804A354` | **Code table** (u16, active-high key masks, zero-terminated), 14 entries |
| `0x0831C2A0`, `0x0834F36C`, `0x0838AD98`, `0x083C9E38` | Byte-identical copies of the table in the four multiboot images |
| `0x08014B1A`, `0x0801FA16`, `0x080233E8`, `0x0802DC16`, `0x080319A8`, `0x08039C30` | The six `BL` call sites (one per game) |
| `0x0802DC08`, `0x0802F12C`, `0x080319C4`, `0x080320AE`, `0x08038A84`, `0x08038D1C`, `0x08039C1C` | Readers of the completion flag (per-game reward logic) |
| `0x03007970` (IWRAM) | Pointer to global state struct → `0x03007980` |
| `0x03007980` | State struct: `+0` game index (5 = Rush'n Attack), `+1` player count, `+2` level/menu index, `+3` **code-complete flag**, `+4` **progress index**, `+5` player count |
| `0x03006AB8` (IWRAM) | Pointer to input struct (`0x03005360`); `+0x52` holds the current `~KEYINPUT & 0x3FF` mask |
| `0x030053CC` | Sound-effect queue; `9E` = confirmation chime |

No password alphabet, literal password table, key permutation, or checksum exists in
this image. `strings -t x -n 4` yields only ~340 lines, almost all in the four
multiboot images; the only meaningful plaintext is the shared UI bank around
`0x0804A300–0x0804A700` (`YOU LOSE`, `YOU WIN`, `1 ST`, `PTS`, `A BUTTON`,
`NOT PREPARED`, the two Konami copyrights). In-game labels are drawn from
font/tile-index arrays that follow those strings (e.g. `07 08 09 0A 0B 08 09 0B
06 09` and the `0x077B,0x0782,0x0789,…` stride-7 glyph-index table at
`0x0804A36E`), which is why `strings` finds no menu text.

## 5. Algorithm

The validator at `0x08011348`, reconstructed from Thumb disassembly:

```
table = 0x0804A354
st    = *(u32*)0x03007970          // -> 0x03007980
reward = 0
if (table[st.byte4] == 1) reward = 0x80   // next expected key is A
if (table[st.byte4] == 2) reward = 0x40   // next expected key is B (branch unreachable)
if (st.byte3 != 0) return reward          // already completed -> gate
key = *(u16*)(*(u32*)0x03006AB8 + 0x52) & 0x3FF
if (key != 0):
    expected = table[st.byte4]
    if (key == expected) st.byte4++        // advance one press
    else st.byte4 = st.byte3               // mismatch -> reset to 0
next = table[st.byte4]
if (next != 0) return reward
st.byte4 = 0; st.byte3 = 1; return reward | 1
```

Input semantics are *edge/pressed* (a held key is registered once), which is why a
~120 ms hold with a gap works. The mask is active-high (`A=0x001, B=0x002,
Select=0x004, Start=0x008, Right=0x010, Left=0x020, Up=0x040, Down=0x080,
R=0x100, L=0x200`) and the comparison is exact — extra simultaneous buttons reject
the press. All six callers mask the return with `& 0xFF` and test `& 1`; on success
they call `sound(0, 0x9E)`. Reward readers test `st.byte3` and typically add an
offset to a per-game table index (e.g. `0x08038D18`: index = `byte2 + 2` when
flag set, `byte2 - 1` otherwise), which is the mechanism behind the extra levels /
extra fights; `0x080319C4` calls `0x08002460` with `r3 = -0x40` when the flag is set.

## 6. Tables

**Code table at `0x0804A354`** (u16 little-endian, active-high masks):

| Index | Mask | Button |
|---:|---:|---|
| 0 | 0x0040 | Up |
| 1 | 0x0040 | Up |
| 2 | 0x0080 | Down |
| 3 | 0x0080 | Down |
| 4 | 0x0020 | Left |
| 5 | 0x0010 | Right |
| 6 | 0x0020 | Left |
| 7 | 0x0010 | Right |
| 8 | 0x0002 | B |
| 9 | 0x0001 | A |
| 10 | 0x0000 | terminator |
| 11 | 0x0004 | Select (unreachable tail) |
| 12 | 0x0008 | Start (unreachable tail) |
| 13 | 0x0000 | terminator |

**Published effects verified against the ROM** (GameFAQs, Wayback 20260202024624):
Frogger — enhanced graphics / bigger frog; Time Pilot — extra level, autofire;
Yie Ar Kung Fu — extra characters in VS mode, two extra fights at tournament end;
Rush'n Attack — extra lives, two extra levels at game end; Gyruss — enhanced
graphics, extra lives, extra level at start, dual gun retained; Scramble —
enhanced graphics. All six use the identical sequence above.

Unverified/out-of-scope: GameFAQs also lists platform-tagged GameShark-style
`POKE` values and an FDS-only Gyruss reverse code (`A B ← → ← → ↓ ↓ ↑ ↑`); the
latter was **tested on this GBA ROM and rejected** (see §7), and `POKE` codes are
memory-edit cheats, excluded by scope.

## 6b. Enumeration

**Space definition.** This is a fixed-table button-code system, not a checksum code.
Alphabet = the 10 GBA button masks; length = 10 presses + zero terminator; no fields,
no checksum, no reserved bits. Table size = 14 u16 (one reachable 10-press code plus
a 2-press unreachable tail), replicated verbatim in all five embedded images.
Representable accepted inputs per state-struct lifetime = **1**. Entry surfaces = 6
per-game player-count menus + 1 global game-select screen = **7 reachable ways to
submit that same input**. Return values: `0x81` (A-ending, the only reachable
success), `0x41` (B-ending reward branch — present in code but no table entry ends
in B, so unreachable), `0x01` (Select/Start tail — unreachable).

**Novel code (not in any published list).** `↑ ↑ ↓ ↓ ← → ← → B A` entered on the
**global `SELECT A GAME` screen** immediately after boot, before choosing a game.
Published sources unanimously require entering it inside each individual game's
player-count menu. Emulator proof: save state before/after; `0x03007983`
`00 → 01` and sound queue `ff ff ff ff → 9e 00 00 00`. The completion flag is
global (the state struct is at a fixed IWRAM address and all six game handlers read
the same byte), so the reward carries into whichever game is launched next.

**Bounds proven by rejection** (all in-game, with RAM reads):

| Trial | Result | RAM evidence |
|---|---|---|
| `↑ ↑ ↓ ↓ ← → ← → B **B**` (wrong final button) | rejected | `0x03007983 = 00`, sound `ff ff ff ff` |
| Reverse code `A B → ← → ← ↓ ↓ ↑ ↑` on Gyruss menu | rejected | `0x03007983 = 00`, sound `ff ff ff ff` |
| `Select, Start` on a fresh screen | rejected | `0x03007983 = 00`, progress never advanced past 0 |
| Valid code on game-select (novel) | **accepted** | `0x03007983 = 01`, sound `9e 00 00 00` |

**Search-space counts backing the negative:** a whole-ROM scan for u16 runs of
1–3FF masks terminated by zero produced 1,926 raw candidates; after filtering to
plausible button-table shape (single-bit masks, no mixed high bytes) the only hits
were the five byte-identical Konami tables above. A direct byte search for the
10-press sequence found exactly five offsets. A literal search found no password
alphabet, no hashed/checksum routine, and no second validator; only one function
(`0x08011348`) contains the `expected == table[progress]` comparison, and it has
exactly six callers.

## 7. Validation evidence

* **Observed (emulator + savestate RAM):** boot sequence, title screen, game-select
  (six titles), each game's player-count menu, in-game screens, and the
  `EXIT A BUTTON / NOT PREPARED` Multi Game Pak VS link wait screen. Code entry on
  Rush'n Attack's player menu and on the global game-select screen both produced
  the chime and the flag flip; the three rejection trials left the flag clear.
  Savestate diffs (zlib `gbAs`, 397,312-byte states) located the struct at
  `0x03007980` via the pointer at `0x03007970` and the sound queue at
  `0x030053CC`.
* **Derived (disassembly):** the validator algorithm, the active-high mask table,
  the 6 callers, the 7 flag readers, the unreachable `0x41` and Select/Start branches,
  and the per-game reward-index adjustment.
* **Inferred (not directly observed):** the exact visual magnitude of each per-game
  reward (e.g. how many extra lives Gyruss/Rush'n Attack receive) was not measured;
  the published effect descriptions are reported as published, and the flag/readers
  are the proof that a reward path is taken. The four high-offset headers are
  interpreted as multiboot VS images based on the `NOT PREPARED` link screen and
  the absence of a second boot path in the main image.

## 8. Unknowns

* Exact numeric values of each game's reward (lives count, level number, sprite
  size) were not isolated to a single RAM word; the shared flag and its readers
  were proven, not the final rendered values.
* The four multiboot images were not individually booted over a link cable; their
  embedded table copies are byte-identical to the main one and appear to be
  compiler-duplicated engine code.
* Whether the flag is cleared on returning to the title screen (it survives a
  game switch in the same session; a fresh boot clears it).

## 9. Tooling

* `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings -t x`.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`
  for the validator and callers; Python + Capstone 5.0.7 for literal/BL scans.
* Python savestate decoder: locate PNG `gbAs` chunk, `zlib.decompress`, diff raw
  state (IWRAM at raw `0x19000`, EWRAM at `0x21000`, VRAM at `0x1000`).
* mGBA under Xvfb `:315` with `SDL_AUDIODRIVER=dummy`; `xdotool` XTEST key helper
  (`/tmp/konamiarcade/key.py`); `scrot` + ImageMagick for screen walks.
* Web: web.archive.org Wayback snapshot of the GameFAQs cheats page (live pages
  returned 403). Fetched page text was treated strictly as data; no embedded
  instructions were followed.

## Legal note

No ROM bytes, graphics, music, or game text are redistributed here — only hashes,
addresses, the input sequence, and derived algorithm notes.
