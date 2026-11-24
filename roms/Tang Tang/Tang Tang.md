# Tang Tang (GBA) — Reverse Engineering Report

> Scope: in-game / developer-intended cheats only (passwords, button codes, hidden
> debug menus, unlockables). Cheat-device codes (GameShark / CodeBreaker / Action
> Replay) are recorded as reconnaissance only and were **not** applied.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Tang Tang/Tang Tang.gba` |
| Size | 4,194,304 bytes (`0x400000`) |
| Header title | `TANG TANG` |
| Game code | `ATAE` |
| Maker code | `54` |
| Version | `0x00` |
| Fixed byte `0xB2` | `0x96` |
| Entry word | `0xEA00002E` (stock ARM branch to crt0) |
| Header checksum | `0x0000` |
| Complement byte `0xBD` | stored `0x59`; computed over `0xA0..0xBC` = `0x72` (header anomaly; recorded, not interpreted as a crack) |
| Nintendo logo | exactly one hit at file `0x4` → single image, not a multi-game pack |
| MD5 | `b8f6082b8f1a88b9dab0565ca19a2e64` |
| SHA-1 | `e39f7f1851a662a422d31f2b5de94704a6ac6fe7` |
| SHA-256 | `9516720fb776c6e88a196884ece798360358f7ce32c91fcdfd34b056d1132b3d` |

The SHA-1 matches the base ROM used by the 2026 *Tang Tang QoL* romhack
(3rd party cheat indexes/hacks/9901), confirming this is the stock USA revision, not a
trained/cracked image.

## 2. Executive summary

**No in-game cheat-code system exists in this ROM.** There is no password entry
screen, no button sequence, no unlockable/debug menu reachable by controller
input, and no name/code text field. Every reachable screen was walked in mGBA
and photographed; the complete ASCII UI text bank was decoded; the input path
was reversed down to the mask comparisons in every menu handler; and the
developer debug-menu data that *does* survive in the image was shown to be
**dead code** (orphaned entry function with zero callers).

What looks like "cheats" on the web is entirely cheat-device territory
(GameShark / Gameshark SP / CodeBreaker / Action Replay / AR MAX). Those codes
write RAM addresses directly and are out of scope. The one *in-game-looking*
thing published for this title — the *QoL hack's* `L+R+Select` service menu — is
explicitly a **new** feature added by that 2026 hack, not a built-in secret; the
stock ROM ignores `L+R+Select`.

The surviving debug material (SPLITE/FONT/BACK/SOUND TEST labels, hidden
difficulty and mode strings, a hex alphabet) is real but unreachable: its setup
function `0x08012FF0` has **zero** BL references, **zero** 32-bit pointers
(including the Thumb-bit form), and **zero** PC-relative literal loads; its four
label strings likewise have zero xrefs. This is a **bounded gated/dead-feature
negative**, not "not tested".

## 3. How to reproduce

* Emulator: mGBA 0.10.5 under Xvfb `:315`, `SDL_AUDIODRIVER=dummy`, `-3` scale.
* Keymap (mGBA SDL default): D-pad = arrows, A = `x`, B = `z`, Start = `Return`,
  Select = `BackSpace`, L = `a`, R = `s`.
* Boot path: logo → RANKING → title (`PLAY GAME` / `CONTINUE` / `CONFIGURE`).
  `CONFIGURE` shows exactly four options: SOUND, HOW TO, LIVES (3), CONTINUES (3).
  `PLAY GAME` → tutorial demo → SOLDIER SELECT (4 characters) → gameplay.
  Start in gameplay toggles a plain `PAUSED` overlay (no hidden entries).
* Savestate `Shift+F1` / `F1` was used to return to a fixed screen for every
  experiment. The `Tang Tang.ss1` artifact was removed from the ROM folder at
  the end (see Cleanup).
* Buttons tested as simultaneous chords on title, configure, soldier-select and
  the frozen pause screen: `L+R+Select`, `L+R+Start`, `L+R`, `Start+Select`,
  `A+B+Start+Select`, `L+R+A/B`, `L+R+Up/Down`, `L+Up+A`, `R+Down+B`,
  `L+R+Up+Down+Left+Right`, the Konami sequence
  (`↑↑↓↓←→←→BA`), and `Select+A/B/Up`, `L/R+Start`. None produced a menu,
  screen change, or RAM flag beyond the normal action of the A/Start keys.
* TIME OVER / HIGH SCORE were reached by injecting small values into the
  savestate at `0x02003920` (timer) and `0x020073D0` (score). **These two
  screens were reached via injected RAM state, not by retail button input**;
  this is labeled as such and is used only for screen enumeration.

## 4. Address map

### File ↔ ROM address
`rom_address = 0x08000000 + file_offset` (single 4 MiB image).

| Address (ROM) | Content |
|---|---|
| `0x08000000` | ARM entry / crt0; `main` Thumb pointer `0x08012975` in literal at `0x1C0` |
| `0x08012AB0` | input poll: reads `0x04000130`, computes held/pressed |
| `0x0801234C` | CONFIGURE menu handler |
| `0x08012734` | title menu handler |
| `0x080122EC` | TIME OVER handler |
| `0x08012E4C` | debug font-test renderer (orphan) |
| `0x08012F4C` | debug split-test renderer (orphan) |
| `0x08012FF0` | **debug screen setup (orphan; 0 callers)** |
| `0x08022E6C` | boot/ranking handler (checks Start only) |
| `0x080E4228..0x080E4364` | ASCII UI text bank (24 NUL-terminated strings) |
| `0x0818F140..0x0818F2EC` | debug menu data bank (see §6) |

### RAM (observed / derived)

| Address | Meaning | Evidence |
|---|---|---|
| `0x04000130` | `KEYINPUT`, active-low | literal at `0x08012AF4` |
| `0x0200023C` | `u16` **pressed** (edge = new & ~old) | `strh` at `0x08012ACA` |
| `0x0200152C` | `u16` **held**, active-high | `strh` at `0x08012ACE` |
| `0x020014E0` | lives (byte) | 9 literal refs; GS/CB "infinite lives" writes here |
| `0x0200273C` | power bolts | 10 literal refs; published CB writes here |
| `0x02003920` | `u16` level timer | compared to 0 at `0x080175BE` before TIME OVER; GS "unlimited time = 0x03E8" writes here |
| `0x020073D0` | 32-bit score | 11 literal refs; CB max-score writes here |

Savestate layout used for RAM evidence (mGBA `gbAs` chunk, 397,312 bytes):
IWRAM at raw `0x19000`, EWRAM at raw `0x21000`. EWRAM offset formula:
`raw = 0x21000 + (addr - 0x02000000)`.

## 5. Algorithm

There is no password/checksum/button-code algorithm to reverse. The relevant
algorithm is the **input-model**, which was recovered exactly:

```
poll_input():                      # 0x08012AB0
    raw  = ~KEYINPUT & 0x3FF       # active-high mask
    held = *(u16*)0x0200152C
    *(u16*)0x0200023C = raw & ~held   # pressed edges
    *(u16*)0x0200152C = raw            # held
    if (*(u8*)0x02003C20 == 0):
        *(u16*)0x02007348 = pressed   # copies for the menu handlers
        *(u16*)0x020073DC = held
```

Menu handlers test only single keys / D-pad directions with `AND`+`CMP`:
* Title `0x08012734`: `0x80` Down, `0x40` Up, `0x01` A. No L/R/Select/Start test.
* CONFIGURE `0x0801234C`: `0x80`, `0x40`, `0x20` (Left), `0x10` (Right), `0x03` (A|B to exit).
* Boot/RANKING `0x08022E6C`: `0x08` (Start) only.
* A generic "any key from mask" helper exists at `0x08022648`
  (`ldrh` pressed, `and r0`, `cmp #0`) and is called with `4` (Select) and `8`
  (Start) from the in-game loop `0x08020F1C` — pause/resume only.

**No code path compares the pressed/held mask against any combination
containing the shoulder bits** `0x100` (R) or `0x200` (L). A full-ROM scan of
every Thumb `LDR Rt,[PC,#imm8*4]` literal whose value lies in `[0,0x3FF]` with
bit 8 or 9 set returned **0 matches**.

### Text/font banks (decoded before the negative)
* ASCII UI bank `0x080E4228..0x080E4364`, 24 strings, decoded in full:
  `RANKING, CONTINUE, TIME OVER, CONFIGURE, SOUND, ON, OFF, HOW TO, LIVES,
  CONTINUES, PLAY GAME, FREE, PRESS B BUTTON, TO BUILD A BLOCK, TO BREAK A
  BLOCK, PRESS A BUTTON, TO JUMP, PRESS DOWN AND A, TO SHOOT, PAUSED, HIGH
  SCORE, THIS WILL OVERWRITE, YOUR PREVIOUS GAME, ARE YOU SURE`.
  None is a code-entry prompt; there is no character grid, cursor glyph set,
  or "enter code/password/name" string anywhere in the 4 MiB.
* The renderer `0x08011FF4` maps ASCII to a font tile by `tile = char - 16`
  (small font) and `0x08012050` by `tile = char + 0xB6` (large font) — a linear
  mapping, not a substitution alphabet. The only alphabet table in the image is
  the debug font-test string `0123456789ABCDEF` at `0x0818F26C`.
* The SOLDIER SELECT heading is drawn from tile indices (no ASCII hit), which is
  the known "text is not ASCII" pitfall; it is a fixed label, not an input field.

## 6. Tables

### Debug menu data bank `0x0818F140..0x0818F2EC` (decoded)

| Offset | Content |
|---|---|
| `0x0818F140` | 8 ROM pointers (`0x08045408`, `0x08045208`, `0x0804B208`, `0x0804AC88`, `0x0804AA88`, `0x08050BC8`, `0x08050648`, `0x08050448`) — graphics for the test screens |
| `0x0818F160` | 12-entry `u16` offset table (`0x001A,0x0046,…,0x0106`) consumed by `0x08012F4C` |
| `0x0818F178` | 12 bytes `21 22 25 26 27 23 24 29 2A 2B 2C 2C` |
| `0x0818F184` | `00 01 02 03` / `05 00 00 00` |
| `0x0818F18C` | difficulty strings `NORMAL / EASY / HARD / HARDEST` + pointer table at `0x0818F1AC` |
| `0x0818F1BC..0x0818F22B` | unused option labels: `TYPE 1`, `TYPE 2`, ` ON`, `OFF`, `NORMAL GAME `, `NORMAL `, `REVERSE`, `CHALLENGER COMES`, `1P`, `2P`, `HI`, `TIME`, `CREDITS` |
| `0x0818F22C/23C/24C/25C` | `< SPLITE TEST >`, `< FONT TEST >`, `< BACK TEST >`, `< SOUND TEST >` |
| `0x0818F26C` | `0123456789ABCDEF` (font-test alphabet) |
| `0x0818F280+` | tile/palette bytes for the test screens |
| `0x08192EC0` | multiplayer leftovers: `PUSH 1P OR 2P START BUTTON`, `1/2 PLAYER SELECT…`, `WAIT` |

### Published codes — recon only (cheat devices, out of scope)

| Effect | Code(s) published | In ROM? |
|---|---|---|
| Enable (master) | `0000F407 000A` + `10022670 0007` (CB) | device patch, not in ROM |
| Infinite lives | `320014E0 0003` (CB), `9F51C56F61B57FE6` (GS) | target `0x020014E0` confirmed as lives |
| Infinite time | `82003920 03E8` (CB) | target `0x02003920` confirmed as timer |
| Power bolts | `3200273C 0003` | target `0x0200273C` confirmed |
| Max score | `320073D0 423F` + `320073D2 000F` | target `0x020073D0` confirmed |
| Invincible / super jump / slow / start-on-level | AR/GS variants | device-only |

None of these is an in-game code; none was entered or applied.

## 6b. Enumeration

**Space definition.** There is no password/code space to enumerate. The only
user-supplied symbol space is the four fixed CONFIGURE settings
(SOUND 2 values, HOW TO 2, LIVES/CONTINUES 3 each → 2·2·3·3 = **36** menu
configurations), plus the four-character SOLDIER SELECT (4 choices). No value
in either set is secret, gated, or unlockable; all are visible and selectable
with normal D-pad/A input. The debug bank contains a 16-symbol alphabet
(`0123456789ABCDEF`), but it belongs to the font-test renderer, not to any input
surface, and no validator consumes it.

**Novel code.** Not applicable — a novel code cannot be minted because the game
has no code validator and no code-entry screen. (Guide §0.2 permits a bounded
negative in place of a generated code when no code system exists.)

**Proof of the negative (counts):**
1. **Screens walked (10)**: boot logo, RANKING, title menu, CONFIGURE,
   SOLDIER SELECT, gameplay, PAUSED, TIME OVER, HIGH SCORE, level restart.
   The last three were reached with injected RAM state; the rest by retail input.
   Every screenshot is retained under `shots/`.
2. **UI text decoded**: 24 ASCII strings in `0x080E4228..0x080E4364`, plus the
   font mapping (`char-16` / `char+0xB6`) used for tile-encoded labels.
   Keyword search over the whole 4 MiB: `PASSWORD`=0, `CHEAT`=0, `SECRET`=0,
   `DEBUG`=0, `LEVEL SELECT`=0, `WARP`=0, `SERVICE`=0, `ENTER CODE`=0,
   `ENTER NAME`=0 hits.
3. **Debug entry xrefs** for `0x08012FF0`: BL hits = **0**, 32-bit pointer hits
   = **0** (also 0 for `0x08012FF1`, the Thumb-bit form), Thumb LDR-literal hits
   = **0**. Same zero counts for its two sub-renderers' external callers
   (`0x08012E4C`, `0x08012F4C` are called only from inside the orphan).
   The four test-label strings each have 0 pointers, 0 BLs, 0 literal loads.
4. **Shoulder-button gates**: Thumb literal loads of any `[0,0x3FF]` constant
   with bit 8 or 9 set = **0**; no menu handler tests `0x100`/`0x200`.
5. **Button-sequence tables**: a scan for runs of ≥3 consecutive `u16` values
   drawn from the 10 key masks (or their active-low complements) returned 297
   runs, all confirmed as coincidental bytes in compressed audio (`
   0x080E2xxx`–`0x080Fxxxx`) or literal-pool addresses (e.g. `0x08026078` =
   `0x00000800/0x00001000/0x00040100`, not masks). None is a validator table.
6. **Controller chords tested**: 18 distinct combinations on title and pause
   (list in §3), all rejected/ignored; only A/Start produced their documented
   behaviour.

**Bounds proven by rejection.** The "rejection" here is behavioural: every
undocumented chord left the same screen and the same RAM state flags; in
particular `L+R+Select` (the *hack's* menu key) does nothing on the stock ROM,
which bounds the "hidden service menu" claim to the hack, not this image.

## 7. Validation evidence

* **Observed** — emulator screenshots of all 10 screens; savestate RAM reads
  confirming the input globals and the timer/lives/score addresses; all 18
  combo tests; HIGH SCORE screen with `AAA 999999` after RAM injection.
* **Derived** — input poll at `0x08012AB0`; mask comparisons in the title /
  CONFIGURE / boot handlers; the debug screen being orphaned (zero xref
  counts); the ASCII→tile font mapping at `0x08011FF4`/`0x08012050`;
  timer/lives/score addresses from their literal-pool references.
* **Inferred** — the debug data bank at `0x0818F140+` was *intended* as a
  developer menu (3rd party cheat indexes independently lists the same strings and flags it
  "needs investigation"); whether it was ever reachable in an earlier build is
  unknown. The TIME OVER → HIGH SCORE → level restart chain was observed only
  from injected state, not from waiting out a real timer.

## 8. Unknowns

* Whether an earlier/prototype build ever wired the debug menu (the retail
  image has no caller; no prototype was available).
* The exact purpose of the `1P/2P`, `REVERSE`, `CHALLENGER COMES`, `TYPE 1/2`
  strings — they are unreachable in the retail UI; likely cut multiplayer /
  difficulty options (3rd party cheat indexes speculates the same).
* The `ARE YOU SURE` / `THIS WILL OVERWRITE` confirmation screen was not
  triggered: the emulated EEPROM held only a high score, not a game-in-progress
  record. It is present in the text bank and its code path exists, but it was
  not photographed.
* The header complement byte mismatch (`0x59` stored vs `0x72` computed) was
  recorded but not investigated further; the stock entry word and single logo
  argue against a modified image.

## 9. Tooling

* `scan.py` — fast 32-bit pointer / Thumb BL / Thumb PC-relative literal scanner.
* `maskscan.py` — literal-load scan for key masks containing L/R bits.
* `seqscan.py` — scan for button-sequence-shaped `u16` runs.
* `dis.sh` — `arm-none-eabi-objdump -D -b binary -marm -M force-thumb` wrapper.
* `ss.py`, `rampoll.py`, `patchss.py` — mGBA `gbAs` savestate decoder, RAM dumps,
  and byte patcher (used for the labeled TIME OVER / HIGH SCORE injections).
* `emu.py`, `combos.py`, `pausecombo.py` — Xvfb/xdotool input and screenshot
  harnesses (display `:315`, 130 ms holds).
* Capstone 5.0.7 (used in an early pass; final scans use the hand-decoded Thumb
  encodings for speed), Pillow for screenshot diffs, Python 3.11.

## 10. Legal note

No ROM bytes, graphics, or game assets are reproduced in this report. Only
hashes, addresses, decoder observations, and original tooling are published.

## Cleanup

All emulator/display processes started for this job were terminated by PID
number (never `pkill -f`), and `Tang Tang.sav` / `Tang Tang.ss1` were removed
from `roms/Tang Tang/`.
