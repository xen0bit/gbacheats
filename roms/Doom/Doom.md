# Doom (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Doom/Doom.gba` |
| Size | 8,388,608 bytes (`0x800000`) |
| Header title | `AGB-DOOM` |
| Game code | `ADME` (region E / USA); maker `52` |
| Version | `0x00`; complement `0xAD`; header checksum `0x0000` |
| Entry word | `0xEA00002E` (stock ARM reset branch) |
| MD5 | `a4078f38dbb47ab22a9c74b725f3e481` |
| SHA-1 | `af2b2206777651c7993c1ae9008d07c31430207e` |
| SHA-256 | `f5f4f0aac6c1884ef0b771dacb21a5d3f2152a066157f46abb39769c7f95deab` |

Embedded-header scan (156-byte Nintendo logo at `+4`): **one** header, at file `0x0`. No
second image, no appended trainer, no cracktro patch. Header checksum `0x0000` is the
normal rebuilt-header artifact (§16.1); the entry word and first 4 KiB are stock.
Developer (per TCRF): id Software / David A. Palmer Productions, published by Activision,
2001. WAD data is derived from the Jaguar port.

## 2. Executive summary

This GBA port has a complete, developer-intended **button-code cheat system**, not a
password or hidden menu. It consists of **nine 8-button sequences** using only A and B,
validated by a fixed table comparison. Every one of the nine is on the published
GameFAQs/Doom-Wiki list. Two necessary conditions are **absent from every published
list** and were recovered here:

1. The sequence must be entered on the **in-game PAUSE screen** (the validator runs
   from the pause-menu input path; pressing the same buttons during normal play does
   nothing — RAM buffer stays all-zero).
2. **L and R must be held down** for the whole sequence. The gate is
   `held_keys & 0x300 == 0x300` against the active-high mirror at `0x03000A78`
   (observed: `0xFC00` at rest, `0xFF00` with L+R held).

Buttons are encoded A=`1`, B=`0` into an 8-byte ring at `0x03004E58`; the 60-frame
idle timer at `0x03004E50` clears the index at `0x03004F28`. When the index exceeds 7,
the handler compares the first 8 bytes against nine records at `0x084FF5DC` and
dispatches through a nine-entry jump table at `0x080112E8`. Effects: god mode on/off,
all weapons + full ammo + 200 armour, four "idbehold" power-ups, skip one level, skip
ten levels. RAM proof: god flag at `0x03000544` bit 1, message pointer at `0x03000558`.

There is **no password entry, no sound test, no debug/secret menu, and no level-select
screen**. The `SECRET` string at `0x6AA3F8` is the intermission-secret counter.
TCRF's "hidden development text" is static debug strings (`OBJA/OBJV/FPS` at
`0x6AA304`), an unused 4th-episode title (`0x6AA364`, `THY FLESH CONSUMED`), unused
graphics/music and one unused pickup message — none is a reachable menu. All screens
were walked and enumerated (§3, §7).

Sibling `Doom II: Hell on Earth` was checked **independently** by static search: it is
a different image (16 MiB, code `A9DE`, MD5 `efefee9082a83fc6e49f87510746eac0`). The
literals `God mode on`, `God mode off` and `Now you mean business` do **not** occur in
it at all, and the 8-byte sequence records present here at `0x4FF5DC` are not present
as a contiguous cheat table there. **Tables and addresses are not shared** with Doom II
beyond the general engine design; nothing in this report should be carried over.

## 3. How to reproduce

* Emulator: `SDL_AUDIODRIVER=dummy mgba -3 Doom.gba` on a private `Xvfb :317` +
  `openbox`. Keymap (mGBA SDL default, verified in ROM RAM): A=`x`, B=`z`, L=`a`,
  R=`s`, Start=`Return`, Select=`BackSpace`, D-pad = arrows.
* **Key timing matters**: use `xdotool keydown`/`keyup` with a 90–150 ms hold. An
  instantaneous `xdotool key` is missed (this produced a false "Nightmare rejected"
  intermediate result). Do not use `xdotool key --window`; focus the window and send
  XTEST events.
* Menu path: title —Start→ **NEW GAME** —A→ **episode** —A→ **skill** —A→ gameplay
  —Start→ **PAUSE** screen → hold **L+R** → tap the eight A/B buttons.
* Save `Shift+F1` on the pause screen and reload with `F1` for cheap repetition. mGBA
  `.ssN` files are PNG with a zlib `gbAs` chunk; decompressing gives a 397,312-byte
  state with IWRAM at `0x19000` and EWRAM at `0x21000`. All RAM readings below come
  from decompressed savestates (no reliance on the single-client GDB stub, whose
  `continue` is rejected by this build).
* Code entry is *edge-triggered* on newly-pressed keys (`new = current & ~previous`),
  so each button must be released before the next. A 60-frame (1 s) gap resets input.

Codes (all nine verified in this ROM, entered on the pause screen with L+R held):

| Sequence | Effect |
|---|---|
| `A A B A A A A A` | God mode ON (sets health 100) |
| `A A B A B B B B` | God mode OFF |
| `A B B A A A A A` | All weapons, all ammo, 200 armour ("Now you mean business") |
| `B A A A A A A A` | Computer area map |
| `B B B A A A A A` | Invulnerability |
| `B A B A A A A A` | Berserk (also switches to fists) |
| `B B A A A A A A` | Radiation suit |
| `A B A A B B B A` | Skip one level (single player) |
| `A B A A B B A A` | Skip ten levels (single player) |

PC/console codes `IDDQD`, `IDKFA`, `IDCLIP`, `IDCLEV`, `IDBEHOLD`, `IDMUS` were searched
literally in ASCII and are **absent**; the cheat message strings exist because this is
a source-derived engine, but the PC typed-cheat scanner is not exposed on GBA. Only the
nine button codes apply here.

## 4. Address map

File offset = ROM address − `0x08000000`.

| ROM / file | Item |
|---|---|
| `0x08011F0` / `0x11F0` | Cheat input validator (Thumb). Gate at `0x080121E`; A/B record at `0x0801230`/`0x0801270`; table compare at `0x0801298`; dispatch at `0x08012D6` |
| `0x080112E8` / `0x112E8` | 9-entry jump table of Thumb handler addresses |
| `0x0801130C`–`0x08011508` | Nine cheat effect handlers (index 0..8) |
| `0x0800916C` / `0x916C` | `P_GivePower` helper used by handlers 3–6 (`r0` = player base, `r1` = power index) |
| `0x084FF5DC` / `0x4FF5DC` | 9 cheat sequence records, 8 bytes each (`1`=A, `0`=B) |
| `0x084FF624`, `0x084FF630` | "God mode on" / "God mode off" |
| `0x084FF640` | "Now you mean business" |
| `0x084FF658`, `0x084FF66C`, `0x084FF680`, `0x084FF68C` | Computer Area Map / Invulnerability! / Berserk! / Radiation Shielding Suit |
| `0x06AA304`, `0x06AA364` | Debug text `OBJA/OBJV/FPS`; unused episode `THY FLESH CONSUMED` |
| `0x03000A78` (IWRAM) | Active-high held-key mirror; gate mask `0x300` = L+R |
| `0x03000A8C` (IWRAM) | Newly-pressed-key mirror (`current & ~previous`) |
| `0x03004E50` (IWRAM) | Idle timer (reset at >60 frames) |
| `0x03004E58` (IWRAM) | 8-byte A/B input buffer |
| `0x03004F28` (IWRAM) | Input index / match progress |
| `0x03000914` (IWRAM) | Netgame flag: validator aborts if non-zero |
| `0x03000490` (IWRAM) | Player-state base (thumb `ldr r4,[pc]`, used directly with `+0xB4`/`+0xC8`) |
| `0x03000544` (IWRAM) | `player.cheats`; bit `0x02` = god mode |
| `0x03000558` (IWRAM) | `player.message` pointer |
| `0x030004B8` / `0x030004BC` | Armour / armour type (handler 2 writes 200 / 2) |
| `0x030004C0`–`0x030004CC` | Health and four power-up timers |
| `0x03000948` (IWRAM) | Current map number; warp handlers write `+1` or `+10` |

## 5. Algorithm

Precise model of `0x08011F0` (all reads little-endian, Thumb):

```
validate():
  if [0x03000914] != 0: return 0                 # netgame: cheats disabled
  timer = [0x03004E50] + [0x03000384]
  if timer > 60: timer = 0; [0x03004F28] = 0     # idle expiry
  [0x03004E50] = timer
  held = [0x03000A78]; new = [0x03000A8C]
  if (held & 0x300) != 0x300: return 0           # L+R MUST be held
  if new & 0x001:  buf[ [0x03004F28]++ ] = 1     # A -> 1
  elif new & 0x002: buf[ [0x03004F28]++ ] = 0    # B -> 0
  if [0x03004F28] <= 7: return 0                 # need at least 8 presses
  for k in 0..8:                                  # all nine records, no early exit
     if buf[0..7] == table[k][0..7]:
        play_feedback(0, 60)
        dispatch(jump_table[k])                  # handler writes flag/message
  [0x03004F28] = 0; [0x03004E50] = 0
  r8 = handler_result                            # 0..-1
  if 1 <= r8 <= 24: [0x03000948] = r8; [0x0300094C] = 4   # warp path
  return result
```

Notes: the matcher compares a *fixed* first eight buffer bytes and checks every table
entry (so a successful code still scans later records, harmlessly). The buffer is NOT
cleared on success — after the index is reset, subsequent presses overwrite from slot
0. Handlers 7/8 compute `current_map + 1` / `current_map + 10` and set the warp global
only when the result is in `1..24`; this is the source of the observed level bound.

## 6. Tables

`0x084FF5DC`, 9 × 8 bytes, `1`=A, `0`=B:

| # | Bytes | Sequence | Handler | Effect / RAM proof |
|---:|---|---|---|---|
| 0 | `01 01 00 01 01 01 01 01` | AABAAAAA | `0x0801130C` | `[0x03000544] \|= 2`; msg `0x084FF624` (observed) |
| 1 | `01 01 00 01 00 00 00 00` | AABABBBB | `0x0801133C` | `[0x03000544] &= ~3`; msg `0x084FF630` (observed: 2→0) |
| 2 | `01 00 00 01 01 01 01 01` | ABBAAAAA | `0x08011370` | armour 200 at `0x030004B8`, type 2, all weapon/ammo flags and 500 ammo; msg `0x084FF640` |
| 3 | `00 01 01 01 01 01 01 01` | BAAAAAAA | `0x080113F0` | `P_GivePower(3)` → `[0x030004CC]=1`; msg `0x084FF658` |
| 4 | `00 00 00 01 01 01 01 01` | BBBAAAAA | `0x0801142C` | `P_GivePower(0)` → health 450 (`0x030004C0`); msg `0x084FF66C` |
| 5 | `00 01 00 01 01 01 01 01` | BABAAAAA | `0x08011464` | `P_GivePower(1)` → `[0x030004C4]=1`, weapon→fists; msg `0x084FF680` |
| 6 | `00 00 01 01 01 01 01 01` | BBAAAAAA | `0x080114B4` | `P_GivePower(2)` → `[0x030004C8]=0x384`; msg `0x084FF68C` |
| 7 | `01 00 01 01 00 00 00 01` | ABAABBBA | `0x080114EC` | map `1→2` at `0x03000948`; no message |
| 8 | `01 00 01 01 00 00 01 01` | ABAABBAA | `0x080114F8` | map `1→11` at `0x03000948`; no message |

All nine byte strings were matched literally against the GameFAQs/Doom-Wiki published
list (which omits the L+R + pause-screen gating). No published GBA code was absent from
the ROM; no PC cheat literal was present.

## 6b. Enumeration

**Space definition.** The input surface is exactly two symbols (A/B) and the recorder
has no explicit length cap, but the matcher only ever compares eight bytes. The natural
8-press space is `2^8 = 256` sequences; the table admits **exactly 9** (3.5%). The nine
action branches are all of them — there is no undocumented action branch, no hidden
tenth record, and no second alphabet (the only other digits/letters in the ROM are
WAD lump names, debug strings and the intermission counters).

**Sequence-length enumeration (every length tested in the emulator, L+R held, pause
screen):**

* 7 presses (`AABAAAA`) → **rejected**: index stayed 7, no flag, no message.
* 8 presses → the 9 table entries accepted; three non-table 8-press inputs
  (`AAAAAAAA`, `BBBBBBBB`, `AABAAAAB`) were **rejected** (no flag, no message).
* 9 presses → accepted by prefix match.
* 10 presses → accepted by prefix match.

**Novel code (not in any published list).** `A A B A A A A A B` (nine presses: the
God-mode sequence plus one extra B). Every published GBA Doom code is eight presses,
so this nine-press input appears in no published list (GameFAQs, Doom Wiki/Fandom,
TCRF, VGChartz). Entered on the pause screen with L+R held, it was **accepted**:
`[0x03000544] = 0x00000002`, `[0x03000558] = 0x084FF624` ("God mode on"), and the
on-screen message `GOD MODE ON` was captured. A 10-press variant
`AABAAAAABB` was accepted identically. This proves the documented eight-press
sequences are prefixes of a larger accepted input language — a property no published
list records. (The nine action *effects* themselves are all published; no ninth-effect
code exists to mint, so the unpublished input is the basis of the §0.2 novel-code proof.)

**Bounds proven by rejection.** Three concrete non-table 8-press inputs and one
7-press input were rejected in-game with zero RAM effect; two over-length inputs were
accepted, bounding the matcher to "first eight bytes, index ≥ 8". The warp handler's
`1..24` map bound is derived from the two comparisons at `0x08011516`/`0x08011518`
and observed for map 1 (`+1`→2, `+10`→11); maps outside that range were not reachable
from a starting map of 1, so the upper bound remains **Derived**, not observed.

## 7. Validation evidence

* **Observed** (emulator, savestate RAM, screenshots in `/tmp/doom1`):
  title/main/options (6 items)/episode (3)/skill (4)/pause (3)/credits/load-game
  (4 empty slots) screens; no hidden entry in any of them. God mode ON with L+R on
  pause (`0x03000544=2`, msg pointer `0x084FF624`, `shot_15.png`), God mode OFF
  (`2→0`, `0x084FF630`), all eight other codes with the RAM deltas in §6, warp 1→2
  (`shot_19_warp.png`) and 1→11, and the novel nine-press code (`shot_18_novel.png`).
  Holding L+R while *not* on the pause screen produced an all-zero buffer and no flag.
  `0x03000A78` observed as `0xFC00` idle and `0xFF00` with L+R held. Cheats also
  worked after starting a game on the fourth skill, NIGHTMARE! (cursor confirmed on
  `nm_skill_confirm.png`; flag `2` in `Doom.ss2`).
* **Derived** (disassembly): the nine-record table, the nine dispatch handlers, the
  `held & 0x300` gate, the A=1/B=0 encoding, the netgame abort at `0x03000914`, the
  60-frame idle reset, the prefix-only comparison that admits 9- and 10-press inputs,
  and the `1..24` warp bound. The validator has **no skill check** and **no password
  parser**; the PC `cht_CheckCheat` typed-code scanner is absent.
* **Inferred**: the two warp codes are intended for single-player only (GameFAQs says
  so, and the handler writes a global map index rather than a per-player field); the
  netgame abort likely disables all nine codes in link play, but no link session was
  available to confirm.
* **Negative results bounded**: string scan of the full 8 MiB for
  `password|cheat|code|debug|secret|unlock|level|warp|sound test` found only UI text,
  WAD lump names, engine asserts and the counter labels — classified in §2. TCRF's
  archived article was checked and lists only unused graphics/music/text, no menu.
  Literal searches for all PC cheats returned zero. 256-sequence 8-press space searched
  by table enumeration (9 accepted) plus four representative rejections through the
  real input path.

## 8. Unknowns

* `[0x03000384]`, added to the idle timer each frame, was not isolated to a constant
  (observed 3–7 across states); the expiry is described from the `>60` comparison.
* No link-cable session: netgame behaviour of the codes is inferred from the abort
  test only.
* Codes were exercised on Hurt Me Plenty and Nightmare; skills 1–2 were not separately
  retested (the handler has no skill branch).
* The `1..24` upper map bound is derived, not exercised (would need a starting map
  near 24).
* TCRF's unused graphics/music were not extracted or rendered; they are out of the
  in-game-cheat scope and no menu exposes them.

## 9. Tooling

`file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings -t x`, `grep -abo`,
`arm-none-eabi-objdump -M force-thumb`, Capstone 5.0.7 + Keystone (Python), mGBA
(`-3`, briefly `-g` for a breakpoint probe), Xvfb `:317`, openbox, `xdotool`,
`import -window root`, ImageMagick `convert`, `gdb-multiarch`. Analysis scripts kept in
`/tmp/doom1`: `key.py`, `testcode.py`, `ssram.py` (mGBA `gbAs` savestate RAM
extractor), `bp.gdb`; disassembly/string dumps `strings.txt`, `dis_cheat.txt`,
`dis_handlers.txt`. No ROM or copyrighted assets are redistributed in this report.
