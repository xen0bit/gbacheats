# Disney's Peter Pan: Return to Never Land (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Disney's Peter Pan: Return to Never Land.gba` |
| Size | 8,388,608 bytes (8 MiB, `0x800000`) |
| Header title | `PETERPAN RTN` |
| Game code / maker | `APPE` / `4Q` |
| Software version | 0 |
| Complement check (`0xBD`) | `0x33` (recomputed over `0xA0..0xBC` = `0x33`, so the header body is intact) |
| Header checksum (`0xBE`) | `0x0000` (zeroed field; see note below) |
| Entry word | `0xEA00002E` → stock ARM branch to `0x080000C0` |
| MD5 | `d7c540384eff184dbd81292f3f7f8c29` |
| SHA-1 | `57317b9c6c2075b7d39d85d949efb49db85aad13` |
| SHA-256 | `1bb40100cf0f2be218fe47964ae365ab13f9c43dd4923f04deb041c5e6af19e0` |

Header scan: exactly **one** Nintendo logo occurrence in the whole image (`0x24FFAE51…` at file `0x4`),
followed by a normal header, so this is a single 8 MiB image, not a multi-game pack. Entry point,
first 4 KiB (`0x08000000`-`0x08001000`) and the crt0/IRQ stubs are stock ARM code; no cracktro,
trainer, `SUNHORS`/`Mode7`/`CRC BANDIT` strings, and no appended boot menu. `0x0000` in the 16-bit
header-checksum field is the usual artifact of a rebuilt header (GBA ignores it); the complement byte
and the branch word are consistent with a retail-derived image.

## 2. Executive summary

The game has **no battery save**: progress is a **6-character password** shown by the developer's own
password screen (`YOUR CURRENT PASSWORD IS:`). Entry is `CONTINUE GAME` → `ENTER PASSWORD`.

The system is a **lookup table, not a checksum**: 22 records of 8 bytes each. The first six bytes are
symbol indices into a 21-letter alphabet `BCDFGHJKLMNPQRSTVWXYZ` (no vowels); bytes 6 and 7 name the two
*parameter positions*:

* `rec[6]` carries a **4-bit movie-unlock mask** (`0x02005440[0..3]`, one byte per MOVIE 1-4);
* `rec[7]` carries **CONTINUES** (0..4), stored at `0x02004FFC` and shown by OPTIONS → `CONTINUES`.

The validator walks all 22 records, compares the four fixed symbols, and derives the two fields by
subtraction with range checks (`0..15` and `0..4`). One implementation quirk bounds the space: the
comparison of symbol 0 is done before the "skip parameter positions" loop, so for the five records whose
parameter position is 0 the corresponding field is forced to zero.

**Space: 21 symbols, length 6, 22 records → exactly 1,385 distinct accepted codes** out of 85,766,121
representable strings (17 records × 16 masks × 5 counts + 5 records × 1 × 5 counts). The six published
GameFAQs codes all decode and are a small subset (their masks are 0 or 1, so they unlock at most one
movie). Three codes that appear in no published list were generated and accepted in-game, and the
bounds were proven by four in-game rejections (mask 16, count 5, a 5-character string, and the
position-0 quirk). Details in §6b.

## 3. How to reproduce

Emulator: mGBA 0.10 SDL, 3× scale, under Xvfb `:335` + openbox, `SDL_AUDIODRIVER=dummy`.

Default SDL keymap used: **A = `x`**, **B = `z`**, **Start = `Return`**, D-pad arrows.

Menu path:

```
title "PRESS START"  ->  Start/A
main menu            ->  NEW GAME / CONTINUE GAME / OPTIONS / MOVIES
CONTINUE GAME        ->  ENTER PASSWORD screen
password screen      ->  D-pad moves the 7x3 letter grid, A appends a letter,
                         Start submits, B cancels back to the title
accepted code        ->  chest opens, stage loads at the encoded checkpoint
OPTIONS              ->  MUSIC, SFX, DIFFICULTY, CONTINUES
pause (in game)      ->  RESUME / EXIT -> ARE YOU SURE? NO/YES
```

Entry grid (row-major, 7 per row):

```
B C D F G H J
K L M N P Q R
S T V W X Y Z
```

Hold keys 100-150 ms; the menus are edge-triggered on `0x0200073C`, so a 10 ms tap is dropped and a long
hold can double-step the grid cursor. Savestates (Shift+F1…F9 save, F1…F9 load) make each test one
`F`-key plus six letters.

Exact tests used below:

* accepted `ZGWYCR` (published "Ship"), `ZXWYHR`, `BWJSHY`, `BKCDBH`;
* rejected `ZYWYHR`, `ZXWYJR`, `ZGWYC` (5 chars), `TKHDBH`.

## 4. Address map

File offset = ROM address − `0x08000000`.

| ROM address | File off | What |
|---|---|---|
| `0x080000C0` | `0xC0` | stock ARM crt0 entry |
| `0x08000BC4` | `0xBC4` | keypad reader: writes pressed edges `0x0200073C`, released `0x02000740`, held `0x02000730` |
| `0x0800E140` | `0xE140` | "continue used" increment: `0x02004FFC = min(n+1,4)`, then `0x02005434 = 12*n+50` |
| `0x0800FCB0` | `0xFCB0` | OPTIONS screen draw (4 rows incl. CONTINUES value) |
| `0x0800FF80` | `0xFF80` | draw the six entered symbols from `0x0200B4F0` |
| `0x0800FFF4` | `0xFFF4` | draw grid cursor |
| `0x080100D8` | `0x100D8` | grid cursor movement + `0x0200B4F8` selection |
| `0x08010174` | `0x10174` | **password validator** (returns checkpoint id or 0) |
| `0x0801025C` | `0x1025C` | ENTER PASSWORD screen main loop |
| `0x08010480` | `0x10480` | **password encoder** (state → 6 symbols at `0x0200B4E8`) |
| `0x0801055C` | `0x1055C` | "YOUR CURRENT PASSWORD IS:" screen |
| `0x080113BC` | `0x113BC` | MOVIES screen (list + lock check marks) |
| `0x08669DC4` | `0x669DC4` | **record table**, 22 × 8 bytes |
| `0x08669E74` | `0x669E74` | **checkpoint id table**, 22 × u32 |
| `0x08669F24` | `0x669F24` | pointer `"YOUR CURRENT"`; `+4` `"PASSWORD IS:"` |
| `0x08669F2C` | `0x669F2C` | **alphabet**, 21 bytes + NUL: `BCDFGHJKLMNPQRSTVWXYZ` |
| `0x08669F60` | `0x669F60` | MOVIES screen label/marker pointer arrays |

RAM (EWRAM):

| Address | Meaning |
|---|---|
| `0x0200B4F0` | 6 entered symbol **indices** (0..20), written by the grid handler |
| `0x0200B4D8` | number of entered symbols (0..5, max 6) |
| `0x0200B4E8` | encoder output: 6 ASCII symbols of the current password |
| `0x0200B4F8` | currently highlighted symbol index |
| `0x02004FFC` | **CONTINUES** (0..4), written by the validator |
| `0x02005440` | 4 bytes, one per **MOVIE 1-4** unlock flag (validator only sets, never clears) |
| `0x02005434` | derived `12*CONTINUES + 50` (98 when CONTINUES=4) |
| `0x0200B474` | stage entry script PC, initialised to the decoded checkpoint id (observed id+1 after the intro script starts) |
| `0x02004FD8` | current stage number used by the encoder (observed 20/21/22 for checkpoints 27/28/29) |
| `0x02000F68` | screen/state selector written by the password accept path (0 = start stage) |
| `0x02000730/73C/740` | held / pressed-edge / released-edge key words |

## 5. Algorithm

### 5.1 Validator (`0x08010174`)

```c
// alpha = "BCDFGHJKLMNPQRSTVWXYZ"; rec[22][8]; cid[22] (checkpoint ids)
uint32_t validate(uint8_t in[6]) {          // in[] = symbol indices 0..20
  for (int i = 0; i < 22; i++) {
    uint8_t *r = rec[i];
    int pa = r[7];                          // CONTINUES position
    int pb = r[6];                          // movie-mask position
    if (in[0] != r[0]) continue;            // NOTE: symbol 0 is always compared
    int ok = 1;
    for (int p = 1; p <= 5; p++) {
      if (p == pa || p == pb) continue;     // the two parameter slots are free
      if (in[p] != r[p]) { ok = 0; break; }
    }
    if (!ok) continue;
    int cont  = in[pa] - r[pa];
    int flags = in[pb] - r[pb];
    if (cont  < 0 || cont  > 4)  continue;  // range layer
    if (flags < 0 || flags > 15) continue;
    RAM[0x02004FFC] = cont;
    for (int b = 0; b < 4; b++)
      if (flags & (1 << b)) RAM[0x02005440 + b] = 1;   // set-only, no clear
    return cid[i];
  }
  return 0;
}
```

The accept path (`0x0801040C`…) then stores the returned id at `0x0200B474`, clears `0x02000F68`
("start stage"), and returns screen state 5. Return 0 just plays the error cue and stays on the screen.

### 5.2 Encoder (`0x08010480`)

```c
int encode(void) {                    // for the "YOUR CURRENT PASSWORD IS:" screen
  zero(0x0200B4E8, 8);
  int idx = -1;
  for (int i = 0; i < 22; i++) if (cid[i] == RAM[0x02004FD8]) { idx = i; break; }
  if (idx < 0) return 0;             // stage not a password checkpoint
  uint8_t buf[6]; memcpy(buf, rec[idx], 6);
  buf[rec[idx][7]] += RAM[0x02004FFC];                 // CONTINUES
  buf[rec[idx][6]] += flags_from(0x02005440[0..3]);    // movie mask
  for (int i = 0; i < 6; i++) RAM[0x0200B4E8 + i] = alpha[buf[i]];
  return 1;
}
```

Because the encoder does not model the validator's "symbol 0 is always compared" rule, a state whose
record has a parameter at position 0 will print a password that the validator then rejects (see §6b).

## 6. Tables

### 6.1 Record table (`0x08669DC4`, 22 × 8 bytes)

`base` is the code with both fields = 0. `flags@` / `cont@` are `rec[6]` / `rec[7]`.

| idx | checkpoint id | base code | flags@ | cont@ | published label |
|---|---|---|---|---|---|
| 0 | 2 | `BDTJMG` | 1 | 5 | — |
| 1 | 5 | `RGCKYD` | 2 | 5 | Jungle (`RGCKYD`) |
| 2 | 6 | `BFDSCH` | 2 | 3 | — |
| 3 | 7 | `BJWLFQ` | 0 | 4 | — *(flags locked)* |
| 4 | 10 | `PFCMLD` | 1 | 4 | Beach (`PGCMMD`) |
| 5 | 11 | `BHNCJQ` | 0 | 3 | — *(flags locked)* |
| 6 | 12 | `BDCRPG` | 1 | 5 | — |
| 7 | 14 | `CNBDKG` | 2 | 3 | Forest (`CNCGKG`) |
| 8 | 15 | `BKCHSD` | 2 | 5 | — |
| 9 | 16 | `BQYHBD` | 0 | 4 | — *(flags locked)* |
| 10 | 17 | `BFDHPV` | 1 | 2 | — |
| 11 | 19 | `LKMDCQ` | 3 | 4 | TickTock (`LKMFFQ`) |
| 12 | 20 | `BHFDNK` | 2 | 3 | — |
| 13 | 21 | `BDCFHD` | 1 | 2 | — |
| 14 | 23 | `JBKDCD` | 3 | 4 | Forest gold (`JBKFFD`) |
| 15 | 24 | `BQCLFK` | 2 | 4 | — |
| 16 | 25 | `BGMDCR` | 1 | 3 | — |
| 17 | 27 | `ZFWYCR` | 1 | 4 | Ship (`ZGWYCR`) |
| 18 | 28 | `BKCDBH` | 0 | 2 | — *(flags locked)* |
| 19 | 29 | `BDJSCY` | 1 | 4 | — |
| 20 | 30 | `BNCVDW` | 2 | 4 | — |
| 21 | 32 | `BXMDCQ` | 0 | 3 | — *(flags locked)* |

Checkpoint id table (`0x08669E74`):
`2, 5, 6, 7, 10, 11, 12, 14, 15, 16, 17, 19, 20, 21, 23, 24, 25, 27, 28, 29, 30, 32`.

### 6.2 Field layouts

| Field | Position | Width | Range | RAM target | Meaning |
|---|---|---|---|---|---|
| fixed symbols | 4 of 6 | — | — | — | selects checkpoint/record |
| movie mask | `rec[6]` | 4 bits (symbol delta 0..15) | 0..15 | `0x02005440[0..3]` | bit0=MOVIE 1 … bit3=MOVIE 4 |
| continues | `rec[7]` | 3 bits (symbol delta 0..4) | 0..4 | `0x02004FFC` | OPTIONS → CONTINUES |

### 6.3 Published codes (GameFAQs GBA cheats page, fetched via web.archive.org snapshot
`20251112195504`; the live page returns 403)

| Published label | Code | Decodes to |
|---|---|---|
| Beach | `PGCMMD` | record 4, checkpoint 10, mask 1, continues 1 |
| Forest | `CNCGKG` | record 7, checkpoint 14, mask 1, continues 2 |
| Jungle | `RGCKYD` | record 1, checkpoint 5, mask 0, continues 0 |
| Ship | `ZGWYCR` | record 17, checkpoint 27, mask 1, continues 0 |
| Beat the forest gold level | `JBKFFD` | record 14, checkpoint 23, mask 1, continues 2 |
| Beat Tick Tock | `LKMFFQ` | record 11, checkpoint 19, mask 1, continues 2 |

None of the six appears as a literal in the image (`grep -abo` = 0 hits each); all six are accepted by
the reimplemented validator, and `ZGWYCR` was additionally entered on the real screen (§7).

## 6b. Enumeration

**Space definition.** Alphabet 21 symbols (`BCDFGHJKLMNPQRSTVWXYZ`, ROM `0x08669F2C`), length 6,
no checksum. Representable strings: `21^6 = 85,766,121`.

**Closed accepted set.** 22 records; each record fixes four symbols and frees two. With both fields
live that is 16 × 5 = 80 codes per record. But the validator compares symbol 0 *before* it skips the
parameter slots, so the five records with a parameter at position 0 (`idx 3, 5, 9, 18, 21`, all with
the movie mask there) can only be entered with mask 0: 5 codes each.

```
17 records x 16 masks x 5 continues = 1,360
 5 records x  1 mask  x 5 continues =    25
                                 total = 1,385 distinct accepted 6-symbol strings
```

A full enumeration of all 22 × 16 × 5 generated strings, deduplicated and fed back through the
reimplemented validator, gives exactly 1,385 distinct codes, with 0 aliases and 0 disagreements
(`model2.py`). So 1,385 of the 85,766,121 representable strings are valid; the other 85,764,736 are
rejected by the format itself.

**Novel codes (absent from GameFAQs/VGChartz/TCRF and from any wiki page checked).**

| Code | Record | Checkpoint | Mask | Continues | In-game result |
|---|---|---|---|---|---|
| `ZXWYHR` | 17 | 27 (Ship) | 15 (all four movies) | 4 | chest opens, stage loads |
| `BWJSHY` | 19 | 29 | 15 (all four movies) | 4 | chest opens, **different stage** loads |
| `BKCDBH` | 18 | 28 | 0 | 0 | chest opens, different stage loads |

`ZXWYHR` and `BWJSHY` are the important ones: the published list never unlocks more than one movie
and never uses the maximum continue count, and checkpoint 29 has no published password at all.

**RAM proof** (mGBA savestate `gbAs` chunk, EWRAM at `0x21000`):

| Code | `0x02005440` | `0x02004FFC` | `0x02005434` | stage |
|---|---|---|---|---|
| `ZGWYCR` (fresh boot) | `01 00 00 00` | `00` | `50` (=12·0+50) | 27 |
| `ZXWYHR` | `01 01 01 01` | `04` | `98` (=12·4+50) | 27 |
| `BWJSHY` (fresh boot) | `01 01 01 01` | `04` | `98` | 29 |
| `BKCDBH` | `01 01 01 01`* | `00` | `50` | 28 |

\* `BKCDBH` was entered after `BWJSHY` in the same boot; the validator only *sets* flag bytes, so the
earlier unlocks persist. A fresh boot with `BKCDBH` alone therefore carries mask 0.

Visual confirmation: after `ZXWYHR`/`BWJSHY`, `MOVIES` shows `MOVIE 1`-`MOVIE 4` each with a green check
mark (the lock markers are the `\x3c`/`\x3e` glyph strings at `0x080D1A8D`/`0x080D1A8F`), OPTIONS shows
`CONTINUES 4`, and selecting `MOVIE 1` starts an animated cutscene. With the published `ZGWYCR` on a
fresh boot only MOVIE 1 is flagged.

**Bounds proven by rejection** (each remained on the `ENTER PASSWORD` screen; an accepted code leaves it
within ~1 s):

| Input | Why it must fail | Result |
|---|---|---|
| `ZYWYHR` | record 17, mask symbol = base+16 (max 15) | rejected |
| `ZXWYJR` | record 17, continues symbol = base+5 (max 4) | rejected |
| `ZGWYC` (5 symbols) | length must be 6 | rejected |
| `TKHDBH` | record 18 with mask 15 at position 0, which is always compared | rejected |
| `BKCDBH` | same record, mask 0 | **accepted** (control) |

The `TKHDBH`/`BKCDBH` pair isolates the position-0 rule: same record, same continues, only the mask
slot at symbol 0 differs. It is also the one behavioural bug worth recording: for checkpoints
7, 11, 16, 28 and 32 the game's own password *display* can print a code the validator rejects, because
the encoder has no position-0 special case.

## 7. Validation evidence

**Observed** (emulator, RAM, screenshots):

* `ENTER PASSWORD` screen with the 21-letter grid; `Start to Accept` / `B Button to Cancel`.
* `PGCMMD`-style codes are not stored as literals; the six published codes were typed/decoded and one
  (`ZGWYCR`) entered on the real screen: chest animation, Ship stage, `0x02005440 = 01 00 00 00`,
  `0x02004FFC = 0`.
* `ZXWYHR`, `BWJSHY`, `BKCDBH` accepted; RAM values above; `BWJSHY`/`BKCDBH` load different stages.
* Rejections of `ZYWYHR`, `ZXWYJR`, `ZGWYC`, `TKHDBH` (screen unchanged after Start).
* OPTIONS displays `CONTINUES 4` after a code with field 4, and a different (non-4, non-3) digit after
  a code with field 1.
* MOVIES screen check marks for all four movies; `MOVIE 1` playback starts.
* MENU enumeration: Disney logo → title (`PRESS START`) → main menu (NEW GAME / CONTINUE GAME /
  OPTIONS / MOVIES) → password entry; in-game pause (RESUME / EXIT → ARE YOU SURE? NO/YES); OPTIONS
  (MUSIC, SFX, DIFFICULTY, CONTINUES); MOVIES list.

**Derived** (instruction-level):

* decoder at `0x08010174`, encoder at `0x08010480`, table/alphabet addresses and field mapping;
* 1,385-code closed set and the position-0 constraint (verified by the `TKHDBH`/`BKCDBH` pair);
* `0x02005434 = 12*n+50` written next to the continue increment (`0x0800E140`);
* key handling is edge-triggered (`0x08000BC4` writes `pressed = cur & ~prev` to `0x0200073C`).

**Inferred**:

* Field names "movie mask" and "continues" are inferred from the MOVIES screen and the OPTIONS row,
  not from symbol names; the 4 mask bits map 1:1 to MOVIE 1-4 (confirmed by all-4 and 1-flag samples).
* The checkpoint ids are stage-entry script indices; they are ordered like story progress but were not
  matched to stage names (the game shows no stage-name text).
* `0x0200B474` is initialised to the decoded id and then advanced by the script interpreter
  (`0x0800DA80` increments it); the sampled value was always id+1.

**Negative results, bounded.**

* No second password/keypad consumer: the input buffer `0x0200B4F0` is referenced only by the entry
  screen (`0x0FFB8`, `0x0FFF0`, `0x103A0`) and the validator (`0x10230`); the encoder output
  `0x0200B4E8` only by the encoder and the password-display screen.
* No button-code system found: the Konami sequence (and its reverse) appears nowhere as u16 masks or
  bytes; 3,490 raw 6+-symbol alphabet runs and 7,112 raw key-mask runs were scanned and none sits in a
  code path (they are graphics/script data); every menu handler read is a single edge-triggered mask
  (Start/A/B/directions) with no press history array — the only persistent "input" in RAM is the 6-slot
  password buffer.
* No debug/level-select leftovers: 0 hits for `debug`, `cheat`, `code`, `secret`; the only `unlock`
  strings are the four movie messages; no hidden menu beyond the password screen and MOVIES.
* No trainer/cracktro: entry word, crt0 and first 4 KiB are stock.

## 8. Unknowns

* Mapping of the 22 checkpoint ids to the game's stage names; only the six published labels are known.
* Why the encoder's stage number (`0x02004FD8`) was 20/21/22 for checkpoints 27/28/29, and whether a
  stage whose number is not in the checkpoint table (22 was observed) makes the password screen print
  nothing.
* The exact role of `0x02005434` beyond the observed `12*n+50` formula (likely a continue-screen timer).
* Whether the movie mask is ever cleared by any code path (the validator only sets it; a session-wide
  accumulator was observed).

## 9. Tooling

* `mgba` 0.10 SDL under `Xvfb :335` + `openbox`; `xdotool` for XTEST key events; `import`/`convert`
  (ImageMagick) for screenshots; Pillow + NumPy for screen comparison.
* mGBA `gbAs` PNG savestate chunk → `zlib.decompress` → 397,312-byte state; EWRAM at `0x21000`,
  IWRAM at `0x19000` (`readstate.py`).
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`.
* Python model/encoder/verifier (`model2.py`) and entry automation (`enter.py`); ROM copies and states
  were generated only under `/tmp/peterpan`.

No ROM, graphics, music or extracted text is redistributed here; only addresses, algorithms and
self-generated example codes.
