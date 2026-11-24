# Disney Sports Skateboarding (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Disney Sports Skateboarding/Disney Sports Skateboarding.gba` |
| Size | 16,777,216 bytes (16 MiB) |
| Header title | `DS-SKATE-U` |
| Game code | `A4DE` (serial AGB-A4DE-USA) |
| Maker code | `A4` (Konami) |
| Software version | 0x00 (Rev.00) |
| Fixed byte 0xB2 | 0x96 |
| Complement check 0xBD | 0x20 — computed 0x1C, **mismatch** |
| Header checksum 0xBE | 0x0000 — standard computation gives 0x00E0 |
| Entry word 0x00 | `0xEA00002E` — stock ARM branch to 0x080000C0 |
| Nintendo logo | one copy at 0x04; no second header anywhere in the file |
| MD5 | `2694632a5422d0c1553e298458798797` |
| SHA-1 | `d8148c320229afe460ae1277fb99ef6ca9f62ea0` |
| SHA-256 | `ad64cff510dd8592df5391b104eec715b6a2a691b1407369c2f6bbac21e8e54f` |

The complement byte and the zeroed header checksum are the usual artifacts of a
rebuilt header (§16.1); the entry word, the Nintendo logo and the first 4 KiB of
crt0 are stock, so this is a retail image with an edited header record, **not** a
trainer or cracktro. No `SUNHORS` / `CRC BANDIT` / `MODE7` / `CRACK` / `TRAINER`
/ `PARADOX` / `EURASIA` markers occur in the file. mGBA auto-detected
**512-byte EEPROM** and created a 512-byte `.sav` that stayed all-`0xFF`
throughout: the unlock flags in this report are **RAM state, not saved data**.

## 2. Executive summary

**This ROM has a real, fully reversible button-code system with exactly two
accepted codes — one published, one not published anywhere.**

1. The title screen ("Press Start") runs a **two-row NFA sequence matcher** over
   the last ten *newly pressed* buttons. It is not a table lookup and not a
   prefix index: a 22-byte state vector at `0x02007068` holds two independent
   progress chains, and each recorded press advances whichever chain it fits.
   A chain that reaches its last two states sets a bit in the global flag word
   `0x02008110`.
2. **Code A (published, verified):** `Up Up Down Down Left Left Left Right B A`
   → sets bit 9 (`0x0200`) of `0x02008110` → unlocks Mickey's third board
   **ANGER HARNESSED** (SPD/JMP/AIR bars visibly higher than the two stock
   boards). Every published page found (3rd party cheat indexes) lists this sequence, with two different labels
   ("Hidden board" and "Bonus level") that turn out to be the same code.
3. **Code B (unpublished, this report):** `Up Up Down Down L R L R R A`
   (shoulder buttons L and R, not the d-pad) → sets bit 12 (`0x1000`) of
   `0x02008110` → unlocks the third board **M.M.**. No published list for this
   SKU mentions L/R at all, and every list reproduces the d-pad code A instead.
4. Exhaustive enumeration over the matcher (state-graph search, §6b) shows the
   accepted set is **exactly two** 10-press sequences. Every other 10-press
   input is rejected, including one-button variants, the published 7-press
   "bonus level" variant, and Code B re-typed with d-pad Left/Right instead of
   L/R — all four rejections were verified in the emulator by reading the flag
   word back (it stays `0x0003`).
5. **No KCEK debug framework.** The sibling *Disney Sports Basketball* carries
   `AGB SYSTEM Ver3.00 BY KCEK`, `L+R+START SOFT RESET`,
   `L+R+SELECT MEM+DMA DEBUG` and a debug page table. This ROM contains **zero**
   occurrences of `KCEK`, `AGB SYSTEM`, `SOFT RESET`, `MEM+DMA`, `DEBUG`,
   `PASSWORD`, `CHEAT`, `SECRET`, `UNLOCK`, `HIDDEN` in ASCII, case-swapped
   ASCII, UTF-16LE and UTF-16BE (20 keyword families × 4 encodings, §6b.1), and
   **zero** literal references to the sibling gate addresses `0x02000430` /
   `0x0200FA60`. `L+R+SELECT` is inert at boot, on the title and in game (three
   states). `L+R+START` does restart the intro/attract sequence, but it exposes
   no debug surface, no page table and no memory viewer — it is the game's own
   restart, not a KCEK debug dispatch.
6. Unlockables that are **not** codes: `CUSTOM WISH`, `HEAVE & GO` and
   `DENSE FLIGHT` are further board entries gated by bits 10, 11 and 13 of the
   same flag word. Those bits are set by progression code, not by any input
   sequence; §6b enumerates them as address-verified but **not input-reachable**.

## 3. How to reproduce

Emulator: mGBA 0.10 (`mgba -3`), Xvfb `:314`, `openbox`, `SDL_AUDIODRIVER=dummy`.

```
Xvfb :314 -screen 0 1024x768x24 &
DISPLAY=:314 openbox &
DISPLAY=:314 SDL_AUDIODRIVER=dummy mgba -3 "Disney Sports Skateboarding.gba" &
```

Keys (mGBA SDL defaults): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
Select=`BackSpace`, D-pad arrows. Hold 50–80 ms per press; 20+ frame gaps are
safe.

Boot sequence: Konami logo → Disney Sports Network logo → skydiving intro
(~35 s, **Start skips it**) → title art with a blinking `Press Start`.

### Entering a code

The code is only accepted **on the `Press Start` title screen**. It is *not*
accepted on the New Game / Load menu, in GAME MODE, on PLAYER SELECT, BOARD
SELECT or STAGE SELECT (observed: the same ten presses on the menu screen do
nothing).

1. Let the title settle until `Press Start` is on screen. The title drops into
   an attract demo if left idle; a savestate taken on the title restarts that
   timer, so a savestate at `Press Start` gives a repeatable ~2–4 s window.
2. Type the ten presses with ~70–110 ms spacing (a 60 ms hold and a 60 ms gap
   works; slower is also fine).
3. Nothing appears immediately — the game plays a seven-note confirmation
   jingle (sound ids `0x023A 0x0212 0x0239 0x0246 0x0231 0x0235 0x0200`,
   §5.4) and the flag is set in RAM.
4. `A` opens the New Game / Load menu → New Game → GAME MODE → TRICK ATTACK →
   PLAYER SELECT → BOARD SELECT. The new board is the third entry of the ring.

Exact menu paths used:

| Screen | Path |
|---|---|
| Title | boot, let the intro finish (or Start to skip) |
| Attract demo | title, idle; **Start** enters it, **A** returns to the title |
| Title menu | `A` at `Press Start` → New Game / Load |
| GAME MODE | title menu → New Game → A. Five rows, clamps on the last |
| PLAYER SELECT | GAME MODE → TRICK ATTACK → A. Ring: MICKEY, DONALD, GOOFY, MINNIE |
| BOARD SELECT | PLAYER SELECT → A (2 stock boards; 3 with a code) |
| STAGE SELECT (mode) | PLAYER SELECT → A in the Trick-Attack flow: MOON OF IOTA, URBAN MAYHEM, DREAMLAND FUNPARK, HYSTAIRIA, ABYSSAL GRIND, all `NO ACCESS` on a fresh profile |
| STAGE SELECT (game) | BOARD SELECT → A: TUTORIAL and the stage list, playable |
| Gameplay | STAGE SELECT → A |
| PAUSE | in gameplay, Start: CONTINUE / RETRY / QUIT (3-ring, wraps) |
| OPTION | GAME MODE → OPTION: BGM, BETTING, TRICK, CLEAR/DATA + OK |

Savestates: `Shift+F1`…`Shift+F10` save, `F1`…`F10` load; the `.ssN` files are
PNGs whose `gbAs` chunk is zlib data (EWRAM window at raw offset `0x21000` for
this 16 MiB image). `state.py` in §9 reads them; `patch.py` rewrites one or two
bytes and rebuilds the PNG CRCs.

## 4. Address map

ROM addresses are `0x08000000 + file_offset`.

| Address | Contents |
|---|---|
| `0x000000`–`0x0000FF` | GBA header, stock ARM branch, edited complement/checksum |
| `0x0000C0`–`0x0001FF` | ARM crt0, stock |
| `0x08000D60` | **key reader**: `mvn` of `0x04000130` (literal at `0x08000DD4`), stores `held` at `0x02004D32` and `new-press` at `0x02004D30`; base `0x02001700` |
| `0x080A37EC` | **code encoder**: reads `0x02004D30 & 0x3FF` (literal base `0x02001700` + offset `0x3630`) and maps KEYINPUT bits to the game's 10 code values |
| `0x080A3360` | **history push**: shifts the 10×u16 ring at `0x02007F80` down one slot and writes the newest code to `0x02007F92` |
| `0x080A3390` | **matcher**: clears the 2×11 state array at `0x02007068` and dispatches on each of the 10 history entries |
| `0x0801067C`–`0x080106FA` | **title-screen per-frame driver**: 20-frame debounce word `0x02007FA0`, push, match, then `if (state[10]==1 \|\| state[21]==1) call 0x080A36B8` |
| `0x080A36B8` | **accept handler**: sets flag bit 9 (`0x0200`) for row 0, bit 12 (`0x1000`) for row 1 in `0x02008110`, writes `1` to `0x02006070`/`0x02006074`, plays the jingle |
| `0x080A379C` | **consume/reset**: clears the 22-byte state and the 10-entry history |
| `0x02004D30` | new-press word (active-high, `0x3FF` mask) |
| `0x02004D32` | held-key word |
| `0x02007068`–`0x0200707D` | matcher state: row 0 = `+0..+10`, row 1 = `+11..+21` |
| `0x02007072` | row-0 completion byte (`state[10]`) |
| `0x0200707D` | row-1 completion byte (`state[21]`) |
| `0x02007F80`–`0x02007F92` | 10×u16 input history, oldest first |
| `0x02007FA0` | last-accepted-press frame stamp (20-frame debounce) |
| `0x02008110` | **global flag word.** Stock value `0x0003`. bit 9 = ANGER HARNESSED, bit 10 = CUSTOM WISH, bit 11 = HEAVE & GO, bit 12 = M.M., bit 13 = DENSE FLIGHT |
| `0x02005FA0` | engine struct base (`+0xD0` / `+0xD4` written by the accept handler) |

Sibling debug-gate literals checked and **absent**: `0x02000430` (0 hits),
`0x0200FA60` (0 hits), `0x0200D889` (0 hits); `0x02000240` (1 hit) and
`0x02000270` (13 hits) occur only as data-word coincidences, with no code
context.

## 5. Algorithm

### 5.1 Input path

```
raw   = REG_KEYINPUT (0x04000130)          ; active low
held  = (~raw) & 0x3FF                     ; 0x02004D32
press = held & ~prev_held                  ; 0x02004D30  (edge-triggered)
```

`0x080A37EC` converts the new-press bits to the engine's code alphabet:

| KEYINPUT bit | Button | code value |
|---|---|---|
| 6 | Up | `0x0001` |
| 7 | Down | `0x0002` |
| 5 | Left | `0x0004` |
| 4 | Right | `0x0008` |
| 0 | A | `0x0010` |
| 1 | B | `0x0020` |
| 3 | Start | `0x0040` |
| 2 | Select | `0x0080` |
| 9 | L | `0x0100` |
| 8 | R | `0x0200` |

A non-zero result is pushed into the 10-slot history ring (`0x080A3360`);
`Start` and `Select` are recorded but never advance either chain. The
`0x02007FA0` stamp throttles pushes to one per 20 frames.

### 5.2 Matcher

Every frame `0x080A3390` clears the 22-byte state and re-processes all ten
history slots in order. Each slot dispatches on its code value
(`0x080A33CA`–`0x080A341C`):

```
state: b[0..10]  = row 0 chain (0 = unset, 1 = set)
       b[11..21] = row 1 chain

case U  (0x080A341E): if b0  { b1=1 }  b0=1
                      if b11 { b12=1 } b11=1
case D  (0x080A3434): if b0 { if b1&&b2 {b3=1} ; if b1 {b2=1} }
                      if b11 { if b12&&b13 {b14=1} ; if b12 {b13=1} }
case Lft(0x080A3480): if b0 { if b1..b5 {b6=1}; if b1..b4 {b5=1}; if b1..b3 {b4=1} }
case Rgt(0x080A34EE): if b0 && b1..b6 { b7=1 }
case B  (0x080A35B0): if b0 && b1..b7 { b8=1 }
case A  (0x080A352A): if b0 && b1..b8   { b9=1; b10=1 }
                      if b11 && b12..b19 { b20=1; b21=1 }
case L  (0x080A35E4): if b11 { if b12..b16 {b17=1}; if b12..b14 {b15=1} }
case R  (0x080A3626): if b11 { if b12..b18 {b19=1}; if b12..b17 {b18=1};
                              if b12..b15 {b16=1} }
default (Start, Select): no change
```

The matcher is *monotone*: a symbol never clears a state, and any symbol that
does not fit simply does nothing. Acceptance is therefore a statement about the
**last ten recorded presses only**:

```
accept  <=>  (b10 != 0)  or  (b21 != 0)
```

and the driver reads exactly those two bytes (`0x080106B6`).

### 5.3 Accept handler

```
080A36B8:
  f = *(u16*)0x02008110
  if (state[10]==1 && !(f & 0x0200)) { f |= 0x0200; *(u16*)0x02006070 = 1; jingle(); }
  if (state[21]==1 && !(f & 0x1000)) { f |= 0x1000; *(u16*)0x02006074 = 1; jingle(); }
  *(u16*)0x02008110 = f
```

`jingle()` = `0x080AAA98(0x023A, 0x0212, 0x0239, 0x0246, 0x0231, 0x0235, 0x0200)`
followed by `0x080AA984(0x0217)`. Both rows play the same sound, which is why a
successful entry is only audible, never announced with text.

### 5.4 Why only ten presses

Row 0 requires, in order, `b0` (Up), `b1` (Up), `b2` (Down), `b3` (Down),
`b4` (Left), `b5` (Left), `b6` (Left), `b7` (Right), `b8` (B), `b9/b10` (A) —
each step is only reachable after the previous one, so the ten slots are fully
consumed and the only accepted window is the exact sequence. Row 1 is the same
argument with `b11,b12` (Up,Up), `b13,b14` (Down,Down), `b15` (L), `b16` (R),
`b17` (L), `b18` (R), `b19` (R), `b20/b21` (A). Pressing extra keys before the
code is harmless (they slide out of the window); pressing anything inside it
breaks the chain for that attempt.

## 6. Tables

### 6.1 The two accepted codes

| # | Sequence (press order) | Code values | Row | Flag | Effect |
|---|---|---|---|---|---|
| A | Up, Up, Down, Down, Left, Left, Left, Right, B, A | `01 01 02 02 04 04 04 08 20 10` | 0 | `0x0200` | board **ANGER HARNESSED** |
| B | Up, Up, Down, Down, L, R, L, R, R, A | `01 01 02 02 100 200 100 200 200 10` | 1 | `0x1000` | board **M.M.** |

### 6.2 Flag word `0x02008110` (bit → board)

| bit | mask | board | set by |
|---|---|---|---|
| 9 | `0x0200` | ANGER HARNESSED | code A (title, row 0) |
| 10 | `0x0400` | CUSTOM WISH | progression (not input-reachable) |
| 11 | `0x0800` | HEAVE & GO | progression (not input-reachable) |
| 12 | `0x1000` | M.M. | code B (title, row 1) |
| 13 | `0x2000` | DENSE FLIGHT | progression (not input-reachable) |

Stock value on a fresh profile is `0x0003` (bits 0 and 1 are save/screen flags).

### 6.3 Board ring on a fresh profile

| State | Mickey's ring |
|---|---|
| stock | DUBIOUS AIR (SPD1/JMP1/AIR1), RALLY ROUND (SPD2/JMP2/AIR1) |
| after code A | + ANGER HARNESSED (visibly the strongest of the three) |
| after code B | + M.M. |
| bits 10/11/12/13 all set (savestate proof only) | DUBIOUS AIR, RALLY ROUND, ANGER HARNESSED, CUSTOM WISH, HEAVE & GO, M.M., DENSE FLIGHT |

### 6.4 Menus observed

| Menu | Entries |
|---|---|
| Title | `Press Start` (blinking) |
| Title menu | New Game, Load (2) |
| GAME MODE | TRICK ATTACK, GRIND JAM, FREE SKATE, TIME ATTACK, OPTION (5, clamps) |
| PLAYER SELECT | MICKEY, DONALD, GOOFY, MINNIE (4, clamps) |
| BOARD SELECT | 2 stock + up to 5 flag-gated |
| STAGE SELECT (mode) | MOON OF IOTA, URBAN MAYHEM, DREAMLAND FUNPARK, HYSTAIRIA, ABYSSAL GRIND (5, all `NO ACCESS` on a fresh save) |
| STAGE SELECT (game) | TUTORIAL + stage list, playable |
| PAUSE | CONTINUE, RETRY, QUIT (3, wraps) |
| OPTION | BGM ON/OFF, BETTING DAY/…, TRICK MANUAL/…, CLEAR DATA NO/YES, OK |

## 6b. Enumeration

### 6b.1 Space definition

| Property | Value |
|---|---|
| Alphabet recorded | 10 symbols: Up, Down, Left, Right, A, B, Start, Select, L, R |
| Alphabet that can advance a chain | 8 symbols (Start and Select are recorded but inert) |
| Length | 10 (history window; shorter codes are impossible because each press occupies one slot) |
| Checksum | none — the "check" is the two NFA chains |
| Reserved / unused | Start (`0x40`) and Select (`0x80`) are recorded but never dispatched |
| Representable 10-press windows | 8^10 = 1,073,741,824 |
| **Accepted windows** | **2** (exhaustive state-graph search, §9 `matcher.py`) |

The exhaustive search treats the matcher as a deterministic automaton over the
22 state bits, explores every reachable state at every depth 0–10, and returns
the accepting sequences:

```
Up Up Down Down Left Left Left Right B A     (row 0)
Up Up Down Down L R L R R A                  (row 1)
```

The chain argument in §5.4 proves each row admits exactly one spelling, so the
count is not an artifact of the search bound.

Text / button spaces searched (to bound the "no other system" claim):

| Space | Size | Result |
|---|---|---|
| Whole image, 20 keyword families × 4 encodings | 16 MiB × 4 | 0 hits for `KCEK`, `AGB SYSTEM`, `SOFT RESET`, `MEM+DMA`, `DEBUG`, `PASSWORD`, `CODE`, `SECRET`, `UNLOCK`, `HIDDEN`, `CHEAT`, `BONUS`, `STAGE SELECT`, `COMBO`, `CONTINUE`, `PRESS START`, `PAUSE`, `OPTION`, `TUTORIAL`, `CUSTOM` |
| Key-mask tables | the published sequence in u8/u16/u32, forward and reversed, plus 3–7 entry prefixes and five index encodings | no literal run of 4+ consecutive code entries anywhere in the image |
| `KEYINPUT` literal sites | 7 byte occurrences | 2 in code (`0x080005CC` crt0/init, `0x08000DD4` key reader); 5 are data/compressed-region coincidences with no code context |
| Sibling KCEK gate literals | 5 addresses | 0, 1 (data), 13 (data), 0, 0 — no code context |
| Menus walked | 10 distinct | none has a text field or a code entry |

### 6b.2 Novel codes (not in any published list)

**Code B — `Up, Up, Down, Down, L, R, L, R, R, A`** unlocks the **M.M.** board.

* Not in any published list: the lists found (3rd party cheat indexes, 3rd party cheat index mirrors and the VisualBoyAdvance ROM page)
  all reproduce code A with d-pad buttons only; none mentions the shoulder
  buttons for this game.
* Entered through the actual title screen (no RAM patch): the flag word
  `0x02008110` reads `0x1003` immediately after the tenth press, and the board
  ring gains `M.M.` as its third entry.
* It exercises the *second* row of the NFA, which is the unadvertised half of
  the system.

### 6b.3 Bounds proven by rejection (RAM read-back, all from a clean title state)

| Test input | Expected | Observed flag word |
|---|---|---|
| Up, Up, Down, Down, Left, Left, Left, Right, **B, B** (wrong last button) | reject | `0x0003` ✔ |
| Up, Up, Down, Down, Right, B, A (the published "Bonus level" 7-press variant) | reject | `0x0003` ✔ |
| Up, Up, Down, Down, **Left, Right**, Left, Right, Right, A (code B with d-pad instead of L/R) | reject | `0x0003` ✔ |
| **Down, Down, Up, Up**, Left, Left, Left, Right, B, A (first four swapped) | reject | `0x0003` ✔ |
| Up, Up, Down, Down, Left, Left, Left, Right, B, A | accept | `0x0203` ✔ |
| Up, Up, Down, Down, L, R, L, R, R, A | accept | `0x1003` ✔ |

The third row is the sharpest bound: it proves the matcher distinguishes the
shoulder L/R (`0x0100`/`0x0200`) from the d-pad Left/Right (`0x0004`/`0x0008`),
so the two rows are genuinely different code spaces and not one code with
aliases.

### 6b.4 Frame/screenspace bounds

* Codes are accepted **only** on the `Press Start` title screen. The same ten
  presses on the New Game / Load menu, GAME MODE, PLAYER SELECT, BOARD SELECT
  and STAGE SELECT leave the flag at `0x0003` (observed on the menu screen).
* The title's idle timer switches to the attract demo after a few seconds; the
  code must be completed before that (a savestate on `Press Start` restarts the
  timer and gives a repeatable window — the §16.12 pattern).
* `L+R+START` and `L+R+SELECT` do not open any page table, memory viewer or DMA
  window; there is no KCEK banner string to render one.

### 6b.5 Published claims tested

| Claim | Source | Test | Result |
|---|---|---|---|
| "Hidden board: on the code menu, enter Up,Up,Down,Down,Left,Left,Left,Right,B,A" | 3rd party cheat indexes, VisualBoyAdvance ROM page | typed on the `Press Start` title | **works** — ANGER HARNESSED, flag `0x0203`. There is no separate "code menu": the matcher only runs on the title |
| "Bonus level: press Up(2), Down(2), Left(3), Right, B, A at the code screen" | 3rd party cheat indexes | typed as the 7-press variant | **rejected** (flag `0x0003`); it is a truncated transcription of code A, and code A's effect is a board, not a level |
| "At the title screen … press up,up,down,down,left,left,left,right,B,A; you'll hear a signal … a powered-up board called Anger Harnessed" | 3rd party cheat indexes | typed on the GBA title | **works on GBA** — same code A, same board name; the GC-page entry is a mis-filed GBA code |
| GameShark / CodeBreaker address lists | various | out of scope | used only as address hints; none of the listed addresses matched this ROM's flag word |

## 7. Validation evidence

**Observed (emulator, screenshots, RAM reads):**

* Title, attract demo (Start enters, A leaves), title menu, GAME MODE (5 rows,
  clamps), PLAYER SELECT (MICKEY → DONALD → GOOFY → MINNIE, clamps), BOARD
  SELECT (DUBIOUS AIR / RALLY ROUND), STAGE SELECT (5 stages, all `NO ACCESS`
  on a fresh profile; the in-game stage select offers TUTORIAL and is
  playable), PAUSE (CONTINUE / RETRY / QUIT, Down from QUIT wraps), OPTION
  (4 settings + OK).
* Code A entered by buttons on the title: the drawn board ring becomes
  DUBIOUS AIR, RALLY ROUND, **ANGER HARNESSED**; the flag word reads `0x0203`.
* Code B entered by buttons on the title: the ring becomes DUBIOUS AIR, RALLY
  ROUND, **M.M.**; the flag word reads `0x1003`.
* Four rejection inputs (§6b.3) leave the flag word at `0x0003`.
* `L+R+SELECT` inert at boot (held through the Konami and DSN logos), on the
  title and in gameplay. `L+R+START` restarts the intro/attract sequence
  (observed from the attract demo and from inside the intro), but produces no
  debug surface.
* Savestate reads: stock `0x02008110 = 0x0003`; history ring at `0x02007F80`
  shows exactly the typed presses, newest at `0x02007F92`; new-press word at
  `0x02004D30` returns to `0` after each edge.

**Derived (disassembly):**

* Key reader `0x08000D60`, encoder `0x080A37EC`, history push `0x080A3360`,
  matcher `0x080A3390`, driver `0x0801067C`, handler `0x080A36B8`,
  consume/reset `0x080A379C` — all read and reconciled with live RAM.
* The case-by-case state transitions in §5.2 are transcribed instruction by
  instruction from the `0x080A341E`–`0x080A36A4` blocks.
* Flag bits 10, 11 and 12 and 13 were each isolated by patching a single byte of
  the flag word in a savestate at BOARD SELECT; each adds exactly one named
  board entry (CUSTOM WISH, HEAVE & GO, M.M., DENSE FLIGHT). These are address
  proofs, not cheats.

**Inferred:**

* Which progression event sets bits 10, 11 and 13. The boards exist and are
  fully modelled; the writer was not traced to a gameplay routine. By analogy
  with the sibling titles they are challenge/clear rewards.
* The exact player-visible meaning of "M.M." (a Mickey board variant, judging by
  the art and the shared ring with Mickey's other boards).

## 8. Unknowns

* The save-bit layout of the 512-byte EEPROM image; the `.sav` stayed all-`0xFF`
  through every menu action, so the two cheat flags are confirmed to be **RAM
  only** and do not persist across a power cycle.
* The progression writers of flag bits 10, 11 and 13.
* Whether the attract demo's characters/boards change once a code has been
  entered (the demo was only observed before and after a code, not compared
  frame-by-frame).
* `LOAD` on the title menu could not be exercised: no save record exists, and
  the game never wrote one during this session.

## 9. Tooling

* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`
* Python 3 + `capstone` 5.0.7 (literal-site scans, bit-extract idiom search)
* `state.py` — read mGBA `.ssN` PNG `gbAs` chunks (zlib); EWRAM window at raw
  `0x21000`, IWRAM at `0x19000`; `dump` / `diff` modes
* `patch.py` — rewrite 1–2 bytes in a savestate and rebuild the PNG chunk CRCs
* `matcher.py` — bit-exact model of `0x080A3390` plus the exhaustive
  state-graph enumeration; it reproduces both accepted codes and rejects every
  variant tested in the emulator
* `keys.py` — xdotool key/combo/screenshot helper (50–120 ms holds)
* ImageMagick `import`/`convert`/`montage` for screen and ring captures
* No ROM patch, no cheat device, no memory-edit code was used; the `.gba` was
  never modified. Savestate byte patches are labelled as debugger evidence
  wherever they are cited.

## 10. Legal note

No ROM, graphics, music or extracted text is redistributed. Only hashes,
addresses, table layouts, the recovered algorithm and the analyst's own note
are published here.
