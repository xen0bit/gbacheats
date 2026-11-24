# The Legend of Zelda: A Link to the Past (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `The Legend of Zelda: A Link to the Past.gba` |
| Size | 8,388,608 bytes (`0x800000`) |
| Header title | `GBAZELDA` |
| Game code | `AZLE` |
| Maker | `01` (Nintendo); port developed by Capcom |
| Revision | `Rev.00` (software version byte `0x00`) |
| Entry word | `0xEA00002E` (stock, unmodified — §16.1 clean) |
| Fixed byte `0x96` | present; complement `0x8A`; header checksum `0x0000` |
| MD5 | `3287ca66e5cc285a9fe3a922051e84c6` |
| SHA-1 | `a272055abbbf6c26b0cd54c87395d01699589161` |
| SHA-256 | `f328f8f07d736288a00c80d31cc1630f3aa02aaf20efdcba73d31dae832b5d76` |

This is the **USA** SKU (complement `0x8A`, CRC32 `8E91CD13` per Data Crystal). All addresses below are for this exact image.

## 2. Executive summary

**Bounded negative for in-game cheats.** This GBA port has no password screen, no
button-code sequence table, and no reachable hidden/debug menu. The only
free-text input surface in the entire game is the **save-file name-entry keyboard**
(reached on a new game); its validator at `0x08010AA4` checks only that the name is
non-empty and has no embedded spaces. A novel name (`AAAAAA`) and the famous SNES
name-cheat `ZELDA` were both typed, committed, and shown to produce only the normal
"Now saving…" → file-select flow, with no state change.

Everything the web calls a "cheat" for this title is either (a) GameShark /
CodeBreaker / Pro Action Replay device codes — explicitly out of scope — or
(b) **save-bit-gated unlockables** earned by gameplay (§6). The sole "DEBUG" string in
the image (`0x0642070`, `NOA ENGINEERING DEBUG TEAM`) is a credits-roll staff joke,
not a debug feature.

All reachable screens were walked in mGBA with screenshots and RAM reads (§3, §7).
The negative is proven over the searched spaces with explicit counts (§6b), not by
absence of a single string.

A TCRF fetch returned the "This page is not intended for humans / instructions are
only for LLMs" troll text (§16.8); it was treated as data and ignored. The useful
recon came from Data Crystal's notes page and the standard cheat aggregators.

## 3. How to reproduce

- Emulator: mGBA 0.10.5, `mgba -3 ROM`, `SDL_AUDIODRIVER=dummy`, Xvfb `:315` +
  openbox. A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad =
  arrow keys. Holds of 40–120 ms; 45–70 ms for the on-screen keyboards (longer
  double-steps a cursor).
- **Reachable screens walked** (screenshot + RAM evidence):
  1. Nintendo/Capcom splash → title "PRESS START".
  2. **ENTER A NAME** — 5-row keyboard (§6), ABC/abc, backspace, END.
  3. **CHOOSE A FILE** — 3 slots, OPTIONS, COPY, ERASE.
  4. **OPTIONS** — only `MESSAGE SPEED` (SLOW/NORMAL/FAST) and
     `ADJUST BRIGHTNESS` (DARK/NORMAL/BRIGHT).
  5. **CHOOSE A GAME** — A Link to the Past / Four Swords.
  6. Intro story, then in-game Hyrule Castle → Zelda's cell → free play.
  7. **In-game pause menu** — exactly three entries: Continue Game / Save / Sleep.
     SELECT does nothing there; no hidden subscreen.
  8. **Four Swords** — warns "This is a Multi-Pak multiplayer game…", then
     playable solo with an intro cutscene; no code/menu surface observed.
- Name-code test: type `ZELDA` (cursor up/down/left/right + A per letter), select
  END, press A. Observed "Now saving… Do not turn power off." and then the normal
  file-select screen with the name `ZELDA`. Repeat with `AAAAAA` — identical.
- Button test: on file-select pressed
  `L R Up Up Down Down Left Right B A Start Select`; the only visible result was
  normal navigation into OPTIONS. A savestate diff before/after (§9) showed only
  routine CPU/VRAM/OAM state churn (5,740 bytes), no persistent cheat flag.

## 4. Address map

| Address | Kind | Meaning |
|---|---|---|
| `0x0801820E8`–`0x080195D88` | ROM | Encrypted BMG-style message bank (US key `l0ZxE8SjYv3#RhaX`) |
| `0x0800BBA0` / `0x0800BBD4` | ROM/Thumb | KEYINPUT readers (`ldrh` of `0x04000130`); compute held/pressed |
| `0x0800BBC4` / `0x0800BBD0` | ROM | Literal pool: `0x04000130`, mask `0x03FF` |
| `0x03000510` | IWRAM | `held` button mask (u16, active-low inverted) |
| `0x03000BD0` | IWRAM | `pressed` (newly-pressed) button mask (u16) |
| `0x0200B250` | EWRAM | Save-slot struct base (30 literal references in ROM) |
| `0x0200B258` | EWRAM | Current file name buffer (base+8, up to ~6 chars + NUL) |
| `0x08010AA4` | ROM/Thumb | **Name validator** (watchpoint hit at `0x08010ABE`) |
| `0x03000000` | IWRAM | Active save header `S4FT` + name (e.g. `S4FT 00 01 01 01 00 06 AAAAAA`) |
| `0x08067CBC` | ROM/Thumb | Four Swords save integrity/CRC routine; magic `S4FT` at `0x08067E5C` |
| SRAM `0x40/0x50/0x60`, `0x90`, `0xB0` | Flash | `TINI` slot headers (3 ALttP slots + backups) |
| SRAM `0x70`, `0xE8` | Flash | `TF4S` Four Swords blocks; `KNIL` ("LINK" byte-reversed) at `0xEC` |
| SRAM `0x58A`, `0x158A` | Flash | Saved name copies (stride `0x1000`) |

Savestate layout used (mGBA `gbAs` chunk): IWRAM at state offset `0x19000`,
EWRAM at `0x21000` (so EWRAM `0x0200B258` → state `0x2C258`), 397,312-byte state.

## 5. Algorithm

**Name validation (derived from `0x08010AA4`, Thumb):**

```
slot_base = 0x0200B250
name      = slot_base + 8
i = selected_slot (byte at IWRAM 0x03000004)
bad = 0; n = 0
c = name[i*64]
if c == 0: goto done                    # empty -> error path 0x8010AEA
if c == 0x20:                           # leading spaces skipped, counted
    do { n++; c = name[i*64 + n] } while (c == 0x20 || c != 0)
    if c != 0: bad = 1                  # any non-space after a space
else: bad = 1
done:
if bad: show_message(8); ...            # rejection
else:   normal save / start-game flow
```

The function reads exactly the name bytes; there is **no comparison against any
cheat constant** (no `strcmp`, no per-character `cmp rX,#imm` against a secret
string, no flag write on a name match).

**Text-bank decryption (reimplemented; used to decode all 426 messages before the
negative):** US key `KEY = b"l0ZxE8SjYv3#RhaX"`, for each absolute offset `p` in
`[0x1820E8,0x195D88)`, with `rel = p-0x1820E8`, `low8 = rel & 0xFF`,
`nib = rel & 0x0F`:

```
v = ((low8 - KEY[15-nib]) ^ rom[p]) & 0xFF
if rel >= 0x2B: v = (v - rom[p-0x2B]) & 0xFF
out = ((v - low8) ^ KEY[nib]) & 0xFF
```

Messages are plain ASCII + BMG `0x1A` escapes, terminated by `0x7F`, text starting
at bank+`0x770`.

## 6. Tables

**Name-entry keyboard alphabet** (observed on screen; 66 glyph keys):

| Row | Symbols |
|---|---|
| 0 | `A B C D E F G H I J K L M` (13) |
| 1 | `N O P Q R S T U V W X Y Z` (13) |
| 2 | `À Á Â Ä Æ Ç È É Ê Ë Ì Í Î Ð` (14) |
| 3 | `Ñ Ò Ó Ô Õ Œ Ù Ú Û Ü · - : ! ?` (14) |
| 4 | `0 1 2 3 4 5 6 7 8 9 , .` (12) |

plus function keys `ABC`, `abc`, backspace, `END`. Max committed length observed: 6
characters (a 7th typed char overflowed the field in one test; not exhaustively
bounded).

**Unlockables (in scope, but save-bit-gated by gameplay — NOT codes):**

| Unlockable | Gate (from published sources, cross-checked against decrypted messages) | In-bank evidence |
|---|---|---|
| Riddle Quest (ALttP) | collect 10 Triforce Medallions in Four Swords | msg 0395–0402: lumberjack "very good at riddles", basket, reward |
| Hurricane Spin / Blade | complete the Riddle Quest | msg 0402: "teach you my family's secret sword technique … Charge up your sword and press the \ Button many times" |
| Palace of the Four Sword | beat Vaati (Silver Key quest) in Four Swords, then Ganon | msg 0387 "Palace of the Four Sword"; msg 0392 "only true heroes can enter this palace" |
| Four Swords ending tiers / keys | team score 1000+ → Silver, 3000+ → Gold, 5000+ → Hero | Four Swords result screens (not reachable with one local player) |
| Sword Beam in Four Swords | obtain the Master Sword in ALttP | msg "Sword Beam" behaviour; save-flag cross-game |

These are state bits in the `TF4S`/`TINI` save records, written by gameplay events
(medal collection, boss defeat, item acquisition), not by any controller sequence.
Per §16.18 they are unlockables, not a code system; no input path sets them.

**Out of scope / not cheats:** all GameShark/CodeBreaker/AR/PAR entries from
Neoseeker, Supercheats, Almars and StrategyWiki (device RAM patches); the SNES-only
debug names `B` / `BAGE` (require a PAR code and are for the SNES SKU, absent here);
the Chris Houlihan Room (a glitch-triggered emergency room, not an input code).

## 6b. Enumeration

**Code-system space: empty (bounded negative).**

*Text-input space.* The only input surface is the name field: 66 glyph keys × 2
case modes, max ~6 characters → up to roughly `132^6 ≈ 5.3×10^12` names. Every name
is treated identically: validated for format only (§5), then saved. Two
independently chosen names were entered through the real UI:

- `AAAAAA` — a novel string appearing in no published code list. Accepted, normal
  save, no effect (Observed).
- `ZELDA` — the SNES name-cheat lead. Accepted, normal save, no effect (Observed).
  This disproves carrying the SNES name cheat over to this GBA port.

*Button-code space.* Searched and counted:

- 3 raw little-endian occurrences of `0x04000130` in 8 MiB; all 3 are Thumb
  PC-relative literal loads resolving to the two standard input readers at
  `0x0800BBA2` and `0x0800BBD6` plus `0x0806941E`. No fourth reader exists.
- Button-mask sequence scan (u16 and u32, active-high and active-low masks,
  ≥4 consecutive presses): 402 active-high runs, 1 active-low run, 514 runs with
  9-bit masks. **All** hits are literal pools or graphics/audio data (e.g.
  `0x0800BF98` is a pool of constants `0x100/0x200/0x40`, `0x08148xxx` is repeated
  `0x0001/0x0002` data). Zero table-shaped sequences with a terminator and a
  referenced validator.
- A key-history/sequence validator would need to consume `0x03000BD0`
  (`pressed`, 48 ROM literal refs) or `0x03000510` (`held`, 34 refs); all sampled
  sites are ordinary gameplay input handling, not a cheat comparator.

*Text/debug surface.* Counts:

- Raw ROM: `password`=0, `cheat`=0, `codes`=0, `unlock`=0, `generator`=0,
  `invalid`=0; `DEBUG`=1 — the credits line only.
- Decrypted 426-message bank (81,056 bytes): `password`=0, `cheat`=0, `code`=0,
  `unlock`=0, `debug`=0; `secret`=9, all ordinary dialogue ("secret passage",
  "top-secret room", "secret technique", "the secret of my success").
- `strings -t x -n 4` yields 62,141 ASCII runs; exactly 1 matches
  password|cheat|debug|code|secret|unlock|invalid|generator (the credits DEBUG).

*Reachable menus.* Enumerated every screen in §3: name entry, file select
(3 slots + OPTIONS + COPY + ERASE), OPTIONS (2 settings only), Choose-a-Game,
pause (3 entries only), Four Swords entry. No debug menu, no code-entry field, no
unlabelled selectable slot.

**Rejection bounds (derived, not separately exercised in the emulator):**
`0x08010AA4` rejects an empty name (first byte `0`) and any embedded space
(`0x20` followed by a non-NUL) via message 8; both branches are explicit in the
disassembly. For the button-code question there is no validator to reject against —
the bound is the exhaustive input-reader/mask-table/text search above.

**Conclusion:** no novel code can be minted because no code system exists. The
deliverable here is the bounded negative with the enumerated spaces and counts,
plus the name-input experiments (novel `AAAAAA` and `ZELDA`) as empirical proof.

## 7. Validation evidence

| Claim | Evidence type | Detail |
|---|---|---|
| ROM identity / clean header | Observed | `file`, `xxd`, 3 hashes, entry `0xEA00002E`, complement `0x8A` |
| Name buffer at `0x0200B258` | Observed | watchpoint broke at `0x08010ABE` with `r1=0x0200B258`, `r0=0x41`; savestate `AAAAAA` at state `0x2C258` |
| Name validator semantics | Derived | Thumb disassembly `0x08010AA4`–`0x08010B26` |
| `AAAAAA` / `ZELDA` accepted with no effect | Observed | screenshots `zelda_after_end.png`, `zelda_after_end2c.png` |
| Keyboard alphabet (66 keys) | Observed | screenshot `nav10c.png` / `screen03.png` |
| 426 decrypted messages, no cheat text | Derived | reimplemented decryption; keyword counts §6b |
| 3 KEYINPUT literal refs, 0 cheat tables | Derived | corrected Capstone literal-value scan + mask-sequence scan |
| 9 screens enumerated | Observed | `screen01`–`screen28`, `fs01`–`fs07` screenshots |
| 5,740-byte savestate diff = normal churn | Observed | `ss2` vs `ss3` decompressed `gbAs` diff |
| Unlockables are save-bit-gated | Inferred (published) + Observed (reward text in bank) | §6 table; setter call sites not enumerated due to stripped symbols |
| Four Swords requires Multi-Pak | Observed | `fs04.png` warning screen |

## 8. Unknowns

- Four Swords result/ending screens and medal/key counters were not reached: the
  game warns it is Multi-Pak and solo progression through all levels is required.
  The unlockable gates are documented from published sources and the reward text
  is present in the bank, but the precise save-bit offsets and their setter call
  sites were not fully isolated (stripped symbols; CRC-wrapped save blocks).
- The name field's exact maximum length was not exhaustively determined (6 chars
  fit; a 7th was typed once and overflowed visually).
- The empty/space rejection branches of `0x08010AA4` are Derived, not re-entered
  in the emulator.
- Chris Houlihan Room was not triggered (glitch-based, out of scope).

## 9. Tooling

Scripts written in `/tmp/altp` (not shipped with the report):

- `bmg.py` — US text-bank decryptor; wrote `textbank.bin`, `messages.txt`.
- `buttonscan.py` — u16/u32 button-mask run scanner + corrected Capstone
  PC-relative literal-**value** scan (the first pass mistakenly compared the
  literal *address*; corrected count is 3, not 0).
- `dbg_server.py` / `dbg.py` — pty-backed mGBA `-d` debugger bridge over a Unix
  socket; used a watchpoint on `0x0200B258` to find the name validator.
- `ss.py` — extracts and zlib-decompresses the `gbAs` chunk of `.ss1/.ss2/.ss3`.
- `ui.py`, `dumpmem.py`, savestate-diff one-liners.

Note for future runs: another agent's mGBA used `-C gdb.port=2346`, so the GDB stub
port is configurable via `-C` even though `-g` takes no port argument; this avoids
the single-client stub conflict on 2345.

No ROM or copyrighted assets are redistributed here — only addresses, hashes,
algorithms and original observations.
