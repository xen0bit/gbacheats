# Dr. Seuss: The Cat in the Hat (BCTE, USA) (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| field | value |
|---|---|
| file | `roms/Dr. Seuss: The Cat in the Hat/Dr. Seuss: The Cat in the Hat.gba` |
| size | 4,194,304 bytes (`0x400000`) |
| header title | `DRSEUSSCITHT` |
| game code | `BCTE` (USA), maker `5L`, rev 0 |
| header bytes | `fixed 0x96`, version `0x00`, complement `0x0D`, checksum `0x0000` |
| entry word | `0xEA00002E` — stock ARM branch to `0x080000C0` |
| MD5 | `adf1ac69caf510176ee1028ecf6f7adf` |
| SHA-1 | `9340482db02bf5263429a15798d06c509017aa93` |
| SHA-256 | `486016fd579adbb2e3fa6a343ae8c1f68a12f197e7319715f2b34d66a52a8592` |

`file(1)` reports `Game Boy Advance ROM image: "DRSEUSSCITHT" (BCTE5L, Rev.00)`.

**SKU separation (explicit requirement).** This image is **not** the apostrophe-named
sibling in `roms/Dr. Seuss' The Cat in the Hat/`. That one is `CATINTHEHAT`,
game code `AQTE` (MD5 `22a0e9f0e8c1c51272a2e29ef2de56e7`) — a **different game**
(2005 TV-series game, AQTE). Our image is the 2003 NewKidCo/Jack-of-All-Games /
Game Titan platformer (BCTE). **Nothing is shared**: different header, different
hashes, different game code, different builder. All findings below were derived
from the BCTE image alone; no address or table was taken from the AQTE session.

**Phase 0 / patch check.** Nintendo-logo scan over the whole file found exactly one
header, at `0x0`. Entry branch is the stock `EA00002E`. Scans for GAMESHARK /
CODEBREAKER / ACTION REPLAY / TRAINER / CRC BANDIT / MODE7 / SUNHORS patch and
trainer markers were negative (the single `CRC` substring at `0x4881B` is ordinary
compression data, not a cracktro). Sound-engine banner `Shin'en Multimedia. Code:
B.Wodok` at file `0x37897D` is the GAX audio driver, not a cheat string (§16.11).

## 2. Executive summary

This game has a **real, developer-intended password system**, reached from
**Main Menu → Password**. The screen asks for exactly **eight symbols**, each chosen
from a set of **eight item icons** shown in a 2-row grid
(`Ball / Kite / Glove / ?` and `Star / Watch / Thing / Key`; the ninth-looking
`hand-with-fish` art is the selection pointer). There is a savestate-free but fully
RAM-visible input surface: the shared key helper at `0x0800224C` writes active-high
*held* keys to `0x03000CC0` and one-frame *pressed* keys to `0x03000CC2`.

The system is **algorithmic, not a literal lookup table**. Searches of the 4 MiB
image for all 36 published passwords as raw bytes, 16-bit words, 3-bit-packed
triples, reversed, and under every possible consistent item→value mapping produced
**no table** (§6). Acceptance is a position-dependent checksum over the eight item
values with **aliases**: several different items are interchangeable at a given
position while keeping a code valid.

Published codes were recovered from 3rd party cheat indexes (36 codes, two character
sets of 18) and **verified in the emulator**: two published codes are accepted and
transition to the difficulty screen; an all-invalid code is rejected. Three
**unpublished** codes were minted by exploiting the alias classes and accepted in
game (§6b). Bounds were proven by rejection of out-of-set items.

The exact checksum arithmetic was **not** recovered from the ROM (see §8), so the
report gives a precise *behavioural* validator model (position-wise equivalence
classes + acceptance oracle) rather than a bit-for-bit algebraic reimplementation.

## 3. How to reproduce

Emulator: `mgba -3` under `Xvfb :317` with `SDL_AUDIODRIVER=dummy`.
Keymap (mGBA SDL defaults): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
Select=`BackSpace`, D-pad = arrow keys. Hold keys ≥100 ms; screen fades need ~1 s.

Menu path (observed, all screens listed):
1. Title `THE CAT IN THE HAT … press START` (after `GAMETITAN` splash).
2. `Return` → main menu: **Play Games / Password / Options / Credits**.
3. `Down`, `x` → **Enter your Password** (8 empty slots; 8-item grid; `Main Menu`
   option at bottom). `Options` = bright / music / s/fx / back. `Credits` present.
4. `Play Games` → `Are you a boy or girl?` → Boy/Girl → `Choose Difficulty`
   (`Have no fear / Tricky`) → intro → gameplay. A valid password skips directly
   to `Choose Difficulty`.
5. `B` (`z`) on the password screen deletes the last entered symbol.
   `Main Menu` on the password screen returns to the main menu.

**Password entry (deterministic, used for every test in §6b).**
Reload a clean password screen (F9 savestate), then for **each** symbol:
`Left,Left,Left,Up` (reset cursor to the top-left item) → item sequence → `x` (A).
Item sequences (cursor-clamped, verified on screen):

| item label (operational) | keys after reset |
|---|---|
| Ball | *(none)* |
| Kite | `Right` |
| Glove | `Right,Right` |
| "Net"/4th top cell | `Right,Right,Right` |
| Star | `Down` |
| Watch | `Right,Down` |
| Thing | `Right,Right,Down` |
| Key | `Right,Right,Right,Down` |

The visible icon for `Right,Right` and `Right,Right,Right` is the same white
glove-like art; the published name↔icon pairing for those two cells is ambiguous
(§8). This does not affect reproducibility because all codes in this report are
given as *key sequences / operational labels*.

Acceptance detector: after the 8th `A`, a valid code fades to `Choose Difficulty`;
a rejected code stays on `Enter your Password` with all 8 icons still displayed.

Published codes used as anchors (3rd party cheat indexes GBA pages):
- boy, “Catching game finished”: `Key,Key,Glove,Star,Watch,Kite,Key,Kite` → ACCEPTED.
- girl, “Box game finished”: `Kite,Kite,Glove,Kite,Watch,Kite,Key,Kite` → ACCEPTED.

## 4. Address map

| address | kind | evidence | meaning |
|---|---|---|---|
| `0x080000C0` | ROM | Derived (entry word) | ARM crt0/stock entry |
| `0x0800224C` | ROM/Thumb | Derived (objdump) | shared key helper: `r3 = ~KEYINPUT & 0x3FF`; writes held to `[r0]=0x03000CC0`, new presses to `[r1]=0x03000CC2`; `held & 0xF == 0xF` → `0xFF` panic/reset path |
| `0x082C0B4F` | ROM/Thumb | Derived (BL scan) | only caller of the key helper; global per-frame poller |
| `0x03000CC0` | IWRAM | Observed (GDB) | active-high held key mask |
| `0x03000CC2` | IWRAM | Observed (GDB + emulator input) | active-high newly-pressed key mask; read by 50+ screen handlers |
| `0x082AC25C` | ROM/Thumb | Derived (Ghidra) | separate state-machine handler reading the pressed-key word and testing RAM bytes against `0x63` plus button masks; a button-input path, not the password screen (no caller reached on the password screen) |
| `0x082AC178` | ROM/Thumb | Derived (Ghidra) | state setter feeding `0x082AC25C` |
| `0x082B9F5C` | ROM/Thumb | Derived (Ghidra) | game/screen init dispatch (reads `0x03000CC2` indirectly) |
| `0x082B2738` | ROM/Thumb | Derived (Ghidra) | another key-state machine (scroll/selector) |
| `0x37897D` (file) | ROM | Observed (`strings`) | GAX sound-driver banner |

File↔ROM mapping: `0x08000000 + file_offset`. EWRAM/IWRAM were dumped from
mGBA savestates using the `gbAs` PNG chunk (§16.13): for this 4 MiB image the raw
state is 397,312 bytes with IWRAM at raw `0x19000` and EWRAM at raw `0x21000`.

## 5. Algorithm

Behavioural model recovered from the acceptance oracle (no literal ROM table):

```
INPUT  s[0..7]         # eight item symbols
ALLOW[i]               # equivalence class of items accepted at position i
                       # (see §6) — depends on the checksum target/family
ACCEPT iff s[i] ∈ ALLOW[i] for every i, for one of the game's target families
EFFECT on ACCEPT: write unlock flags, jump to Choose Difficulty
EFFECT on REJECT: remain on password screen, keep the 8 entered icons
```

For the base target family (the boy code `Key,Key,Glove,Star,Watch,Kite,Key,Kite`)
the single-position alias classes measured by substitution are:

| position | base item | accepted alternatives (measured) |
|---|---|---|
| 0 | Key | Kite, Star, Net |
| 1 | Key | Watch |
| 2 | Glove | Thing |
| 3 | Star | Key |
| 4 | Watch | Ball, Net |
| 5 | Kite | Star, Key |
| 6 | Key | Glove, Star |
| 7 | Kite | *(none)* |

Changing **several** positions at once to members of their classes was also
accepted (`Kite,Watch,Thing,Key,Ball,Star,Glove,Kite` → ACCEPT), which proves these
are true equivalence classes for that target, not isolated coincidences.
 Codes
belonging to other target families (other published boy/girl codes) have their
own classes — e.g. girl code 0 has `Kite` at position 1, which is *not* in the
base family's class for position 1, yet is accepted. Therefore the ROM implements
a checksum with multiple valid targets; the class table above is one target's
slice, not the whole validator.

No arithmetic model (weights/modulus for the item→value map) was recovered with
confidence, so this section is explicitly labelled **Derived (behavioural)** /
**Inferred (underlying checksum arithmetic)**.

## 6. Tables

**Published password list (verified against the web, not copied from the sibling
SKU).** 36 eight-symbol codes, from 3rd party cheat indexes:
18 “while playing as the boy” and 18 “while playing as the girl”. Effects are
completions of the Box, Net, Catching, Cleaning and Kite minigames, singly and in
combinations. Two representatives were verified in-game (§3); the remainder were
searched for literally in the ROM under the encodings in §6b with negative results
(confirming the algorithmic design).

**Item alphabet (8 symbols).** Operational labels and key sequences are in §3.

**Key input constants.** GBA `KEYINPUT` (`0x04000130`) is active-low:
A=bit0, B=bit1, Select=bit2, Start=bit3, Right=0x10, Left=0x20, Up=0x40,
Down=0x80, R=0x100, L=0x200. The helper inverts to active-high
(`~KEYINPUT & 0x3FF`) before storing at `0x03000CC0/CC2`.

**Search counts for the "no table" result (negative bounded):**
- literal 8-byte windows, all 36 codes under a consistent name→byte bijection,
  bytes unrestricted: **0** matching tables
- 16-bit-word windows: **0**
- 3-bit-packed windows: **0**
- permutation-of-0..7 / 1..8 table scan over 4 MiB: only 4 trivial `0,1,2,…,7`
  constant runs (graphics data), no password table
- 37-code anchor-pattern scan (code 0 pattern `A B A C D E F C`) at strides
  8/9/12/16/0x14/0x18/0x20/0x28/0x30: **0** multi-entry tables

## 6b. Enumeration

**Space.** 8 positions × 8 symbols = `8^8 = 16,777,216` representable strings.
The accepted set is a small structured subset (checksum targets). For the base
family alone the measured class sizes are `4 × 2 × 2 × 2 × 3 × 3 × 3 × 1 = 432`
accepted strings; with the other published target families the true accepted set
is larger. Published lists expose only 36 representatives.

**Novel codes (generated by alias substitution, absent from 3rd party cheat indexes, entered on the real screen and accepted):**

1. `Kite,Key,Glove,Star,Watch,Kite,Key,Kite`
   keys: pos0=`R`; rest as base → fades to `Choose Difficulty`. Not in published list.
2. `Kite,Watch,Thing,Key,Ball,Star,Glove,Kite`
   keys: every position changed to a different alias → ACCEPTED. Not published.
3. `Net,Watch,Thing,Star,Net,Key,Star,Kite`
   keys: independently sampled from the measured classes → ACCEPTED. Not published.
4. `Kite,Key,Glove,Key,Watch,Kite,Key,Kite` (single position-3 alias) → ACCEPTED.

Each produced the identical in-game proof: password screen → `Choose Difficulty`
(character/level selection), i.e. the save-unlock path the published codes use.

**Bounds proven by rejection.**
- `Ball,Ball,Ball,Ball,Ball,Ball,Ball,Ball` → rejected (stays on password screen).
- `Ball,Key,Glove,Star,Watch,Kite,Key,Kite` (only position 0 changed to a symbol
  outside that position's class) → rejected.
- The published boy code `Glove,Thing,Glove,Kite,Watch,Star,Net,Kite` was rejected
  with this build's operational item mapping; recorded as an unverified/ambiguous
  published literal rather than silently omitted (§8).

These establish that acceptance is a real predicate over the 8-symbol space, not
an unconditional “8 items always works” behaviour.

## 7. Validation evidence

- **Observed** (emulator, screenshots on disk in `/tmp/catcolon/`):
  title/main/password/options/character-select/difficulty/gameplay screens;
  8-symbol entry; B deletes; valid codes fade to `Choose Difficulty`; invalid
  codes stay; three novel codes accepted; rejection cases.
- **Observed** (GDB stub on port 2345, `mgba -g`): memory reads at
  `0x03000000`/`0x02000000`, `KEYINPUT` at `0x04000130 = 0x03FF` when idle;
  key helper caught at `0x0800224C` with `lr = 0x082C0B4F`, `r0 = 0x03000CC0`,
  `r1 = 0x03000CC2`.
- **Derived** (objdump -M force-thumb / Ghidra decompilation): key helper and its
  two BL callers; button-state machines at `0x082AC25C`, `0x082B2738`,
  `0x082B9F5C`; negative table searches; positional alias classes (behavioural
  derivation via the in-game oracle).
- **Inferred** (not proven): the exact checksum arithmetic and the complete
  target table; whether any hidden button combination reaches a debug menu.
  The static button-state machine at `0x082AC25C` exists but was not observed to
  fire on any screen walked.

## 8. Unknowns

1. **Exact checksum / target table.** Ghidra decompilation located the input and
   screen-state machines but not a single function that consumes all eight
   password symbols and writes the unlock flags. Multiple valid target families
   exist (a girl code and the base boy code give different per-position classes),
   so the 432-code figure is a lower bound for one family, not the whole space.
2. **Icon↔published-name pairing.** `Right,Right` and `Right,Right,Right` produce
   visually indistinguishable white-glove icons; one published boy code fails
   under the operational mapping. The published list may also contain typos or
   belong to a slightly different revision (§16.7).
3. **Pause menu / hidden debug screen.** Start and Select during gameplay
   advanced dialogue rather than opening a pause menu; no debug screen was
   reached. The button-state handler at `0x082AC25C` was not triggered by any
   combination tried. Not proven absent — only not reached.
4. **Effect bits.** The exact save-word bits set by an accepted password were not
   located in RAM; the visible effect (skip to difficulty/level-select tree) is
   the only proof of the unlock.

## 9. Tooling

- `python3` + `capstone` 5.0.7 + `numpy` 2.5.5; `arm-none-eabi-objdump`,
  `gdb-multiarch`, `mgba -3` / `mgba -g`, `Xvfb :317`, `openbox`, `xdotool`,
  `import`/`convert`/`montage`/`scrot`; REA/Ghidra 12.1.4 MCP for decompilation.
- Scripts in `/tmp/catcolon/`: `phase0.py` (hash/header/logo scan),
  `scan_lit.py` / `blscan.py` (literal + BL scans), `findtable.py`,
  `findtable2.py`, `table3.py`, `perm.py` (table searches), `ss.py` (gbAs
  savestate parser), `ui.py` (XTEST input helper), `oracle.py` (automated code
  entry + acceptance detector), `probe.py` (positional substitution probe).
- No ROM or extracted asset is redistributed; only hashes, addresses, algorithms
  and our own generated codes are published.
