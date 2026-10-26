# Around the World in 80 Days (GBA) — Reverse Engineering Report

Report generated from a local ROM analysis on 2026-10-25.
Methodology: [`GBA_REVERSE_ENGINEERING_GUIDE.md`](../../GBA_REVERSE_ENGINEERING_GUIDE.md)

---

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Around the World in 80 Days/Around the World in 80 Days.gba` |
| Size | 4 MiB (`0x400000`) |
| Header title | `AROUND THE W` (12 bytes, no NUL padding) |
| Game code | `B8DE` |
| Maker code | `FL` |
| Software version | `0` |
| Entry branch | `0xEA00002E` → `0x080000C0` (ARM) |
| Fixed byte `0xB2` | `0x96` (present) |
| Complement check (`0xBD`) | `0x7B` stored, `0x7A` computed |
| Header checksum (`0xBE`) | `0x0000` stored, `0x007B` computed |
| MD5 | `ff81ee924f0b66ca6e1743c056ea0782` |
| SHA-1 | `a3649682ef8a2378767154b37ca854d615305646` |
| SHA-256 | `f3c3586a824ac671c2571b6c73392f1694a7fb425628b166cc482bc0bd72b4a5` |

ROM addresses below are `0x08000000 + file_offset`. All findings are tied to
this exact hash.

**Header/entry integrity.** The 156-byte Nintendo logo is intact and appears
**exactly once** in the file (file offset `0x4`); a full-file logo scan found no
second GBA header, so this is a single-image cartridge, not a multi-game pack.
The entry point and first instructions are a stock Saffire crt0. The complement
byte is one higher than the value computed over `0xA0..0xBC`, and the 16-bit
header checksum field is zeroed. That pattern is consistent with a header field
being rewritten by a dumping/patching tool (title or game-code edit) without a
checksum fix, not with a cracktro: the boot sequence is the retail one
(Walden Media / Hip Games / Saffire logos) and the build stamp `May 17 2004
12:21:14` is present. mGBA ignores the header checksum and boots normally.
No scene/cracktro strings were found (searched for common group names).

---

## 2. Executive summary

The game has **one in-game password system, and it is a full algorithmic
progress code, not a preset table.**

* The Start-screen `PASSWORD` option opens a 16-symbol grid keyboard
  (`B C D F G H J K` / `L M N P Q R S T`, vowels removed). Four symbols are
  entered; the code is exactly 4 characters.
* The validator at `0x080012BC` packs the four symbols as nibbles into a 16-bit
  value and checks three things: a **level/checkpoint index** (`n0`, 0–11), an
  **act/salt field** (3 bits, 0–6), and an **8-bit arithmetic checksum** whose
  value depends on both fields. A **reserved bit (bit 12) must be zero** because
  the comparison is 9 bits wide.
* The accepted space is therefore **12 × 7 = 84 codes** out of 65,536 typeable
  4-symbol strings (0.128 %). The 12 checkpoint codes are public; the other
  **72 codes do not appear in any of the published lists checked** (GameFAQs
  archive, SuperCheats, GameRevolution).
* The game contains both the **validator** and a matching **generator**
  (`0x08001554`). The generator is used by the level-results screen and the
  pause screen; a fresh game's pause screen displays `PASSWORD BHGG`, which the
  reconstructed encoder reproduces exactly.
* On acceptance the game clears the checkpoint flag array, sets flags for
  checkpoints `13..12+n0`, and sets the map/spawn variables — i.e. the password
  is a level warp with progress bookkeeping, not just an unlock.
* A published variant `CLGC` (GameRevolution) is a typo for `CLGG` and is
  rejected by the ROM; this was proven in the emulator.

The 12 published codes were verified at the format level, three of them entered
literally, and **twelve unpublished codes (one per checkpoint, act = 6) were
entered and each loaded the expected level**. Bounds were proven by in-game
rejection of an out-of-range act, an out-of-range level index, a set reserved
bit, a bad checksum, and short input.

No GameShark/CodeBreaker/memory-edit codes are used or documented here.

---

## 3. How to reproduce

### Emulator and input

```bash
Xvfb :144 -screen 0 1280x960x24 &
DISPLAY=:144 openbox &
cd "roms/Around the World in 80 Days"
DISPLAY=:144 SDL_AUDIODRIVER=dummy mgba -3 "Around the World in 80 Days.gba" &
W=$(DISPLAY=:144 xdotool search --name mGBA | tail -1)
DISPLAY=:144 xdotool windowfocus "$W"
```

mGBA 0.10.5 SDL default keymap: **A = `x`, B = `z`, Start = `Return`,
Select = `BackSpace`, L = `a`, R = `s`, D-pad = arrows**. Hold each key
100–200 ms. `F1` loads state slot 1, `Shift+F1` saves it, `Ctrl+R` resets.

The password entry loop used a savestate taken on the empty `PASSWORD` screen
(`Shift+F1`): load with `F1`, type, press A, screenshot.

### Reaching the password screen

```
Title: PRESS START                 -> Return
Main menu: NEW GAME / PASSWORD / OPTIONS
                                    -> Down, A
PASSWORD grid: B C D F G H J K
               L M N P Q R S T      -> arrows to move, A to append,
                                       DELETE removes one, DONE submits,
                                       BACK returns
```

After the fourth symbol the cursor automatically moves to `DONE`; press A to
submit. Two consecutive rejected submissions clear the buffer (observed).

### Grid navigation for typing a code

The 4-slot buffer is indexed by `row*8 + column`, with row 0 = `B C D F G H J K`
and row 1 = `L M N P Q R S T`. `Right/Left` move within a row; `Down/Up` move
between rows/menu. This was confirmed by typing codes and reading the buffer
(`0x030014F8`) in mGBA's GDB stub.

### Codes used in this report

| Code | Meaning | Where |
|---|---|---|
| `BHGG` | published Day 1 London | typed, accepted |
| `CLGG` | published Day 3 Paris | typed, accepted |
| `DCHJ` | published Day 18 Train | typed, accepted |
| `BFGB` | **novel** act 0, London | typed, accepted |
| `BMGQ` | **novel** act 6, London | typed, accepted |
| `CBHQ` … `PSGQ` | **novel** act 6, all 12 checkpoints | typed, accepted |
| `CLGC` | published variant, bad checksum | typed, rejected |
| `BMGS` | act = 7 (out of range) | typed, rejected |
| `MTGB` | level index = 12 (out of range) | typed, rejected |
| `BHGH` | bit 12 set (reserved) | typed, rejected |
| `BHG`, `BH` | length < 4 | typed, rejected |

See §6b for the full enumeration table.

---

## 4. Address map

### ROM

| Item | Address / file offset |
|---|---|
| Validator | `0x080012BC` |
| Validator success dispatch (16-entry jump table) | `0x08001344` (table), handlers `0x08001388`–`0x08001528` |
| Checkpoint-flag setter (used by success path) | `0x0800F220` |
| Flag clear-one / read / clear-all | `0x0800F230` / `0x0800F240` / `0x0800F250` |
| Password generator | `0x08001554` |
| Generator caller, level-results screen | `0x08011356`; act copy at `0x08011354` |
| Generator caller, pause screen | `0x08015DE0` |
| Password screen init / input handler | `0x08001644` / `0x0800194C` |
| Add character / DONE submit / BACK | `0x08001D84` / `0x08001DE4` / `0x08001E70` |
| DELETE menu item / B-button delete | `0x08001E38` / `0x08001E48` |
| Screen widget table (16 grid cells) | file `0x11F8D0`, 8 bytes/cell `{glyph_ptr, x, y}` |
| Empty-slot widgets / menu widgets | file `0x11F950` / `0x11F970` |
| Cell glyphs as u32 ASCII (reverse order) | file `0x126154`–`0x126190` |
| UI text table (`PASSWORD`, `PASSWORD:`, `GAME IS PAUSED`, …) | file `0x121A80`+ , 28-byte records {5 language pointers, `0x01010001`, one field} |
| Build stamp | file `0x14307C` = `12:21:14`, `0x14308C` = `May 17 2004` |
| Unreferenced "I LIKE MONKEYS" text block | file `0x1425E0`–`0x143072` |

### IWRAM / EWRAM variables

| Address | Width | Meaning |
|---|---|---|
| `0x030014F8` | 4 bytes | input buffer, one nibble value (0–15) per symbol |
| `0x03001530` | u8 | input length (0–4) |
| `0x0300151C` | u8 | consecutive-failure counter; >1 clears the buffer |
| `0x030013FC` | u8 | menu cursor: 0 = grid, 1 = DELETE, 2 = DONE, 3 = BACK |
| `0x030014F0` | u8 | grid column 0–7 (row 0/1) |
| `0x03001510` | u8 | grid row 0–1 |
| `0x03004AD4` | u8 | act/salt scratch: written by the validator, read by the generator |
| `0x03004AF0` | u8 | runtime act/story value; initialised to 2; copied into `0x03004AD4` by the results screen only |
| `0x030010DC` | u16 | level/map id after a successful code |
| `0x03001078` | u16 | spawn X (always 0 in the password handlers) |
| `0x0300107C` | u16 | second level coordinate (spawn Y, inferred) |
| `0x02003AE0` | 32-bit entries | progress-flag array; `flag[id]` = byte at `0x02003AE0 + id*4` |

### Checkpoint handlers (validator success path)

`n0` is the entered checkpoint index. Each handler writes the three globals and
then falls into the flag loop that sets flags `13..12+n0` (`n0 = 0` sets none;
`n0 = 11` additionally sets flag 11).

| n0 | flag upper bound `r5` | map id | spawn Y | level (observed) |
|---:|---:|---:|---:|---|
| 0 | (none) | `0x18` | `0x10` | London, England (Day 1) |
| 1 | 13 | `0x24` | `0x18` | Paris, France (Day 3) |
| 2 | 14 | `0x36` | `0x20` | Train (Day 18) |
| 3 | 15 | `0x3A` | `0x28` | Turkey (Day 20) |
| 4 | 16 | `0x10` | `0x30` | India (Day 25) |
| 5 | 17 | `0x0A` | `0x38` | India — wanted poster (Day 25) |
| 6 | 18 | `0x05` | `0x40` | China (Day 40) |
| 7 | 19 | `0x2B` | `0x48` | San Francisco (Day 61) |
| 8 | 20 | `0x41` | `0x50` | Wild West (Day 61) |
| 9 | 21 | `0x38` | `0x50` | Train to New York (Day 61) |
| 10 | 22 | `0x20` | `0x50` | Old Foe |
| 11 | 23 (+ flag 11) | `0x01` | `0x50` | Ending |

---

## 5. Algorithm

### Symbol alphabet

```
index : 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15
glyph : B C D F G H J K L M  N  P  Q  R  S  T
```

The 16 glyphs are stored as four-byte ASCII words at file `0x126154`–`0x126190`
and referenced one by one from the widget table at `0x11F8D0`. Each on-screen
cell maps to exactly one nibble; there are no aliases and no wildcard.

### Validator (`0x080012BC`)

```
validate(buf, len):
  if len != 4: return 0
  v  = buf[0] | buf[1]<<4 | buf[2]<<8 | buf[3]<<12      # 16-bit
  n0 = v & 0x0F
  if n0 > 11: return 0                                  # cmp #11 / bhi
  act = v >> 13                                          # 3 bits
  *(u8*)0x03004AD4 = act
  if act > 6: return 0
  chk = ((act << n0) + n0 + 0x43) & 0xFF                 # 8-bit add
  if chk != ((v >> 4) & 0x1FF): return 0                 # 9-bit compare!
  clear_all_flags()                                      # 0x0800F250
  for id in 13 .. 12+n0: set_flag(id)                    # 0x0800F220
  write map/spawn globals for n0
  return 1
```

The 9-bit extraction is the subtle part: `lsls r1,r2,#19; lsrs r1,r1,#23`
(`0x08001300`) yields bits 4..12, not bits 4..11. Because `chk` is masked to
8 bits, **bit 12 of `v` must be zero**; setting it makes an otherwise valid code
fail. This was proven with `BHGH` (see §6b).

### Encoder (inverse, used by the game at `0x08001554`)

```
encode(n0, act):
  chk = ((act << n0) + n0 + 0x43) & 0xFF
  v   = (act << 13) | (chk << 4) | n0
  return GRID[v & 15] + GRID[(v>>4)&15] + GRID[(v>>8)&15] + GRID[(v>>12)&15]
```

The generator derives `n0` from the progress flags, not from the level just
loaded:

```
generate():
  n0 = 0
  for id in 13..23: if flag(id) != 0: n0 = id - 12
  act = *(u8*)0x03004AD4
  if act > 6: act = 7                    # helper 0x080012A4; note: 7 is unvalidatable
  ... emit encode(n0, act) into 0x030014F8
```

Two call sites differ:

* **Level-results screen** (`0x08011354`): copies `0x03004AF0` (runtime act)
  into `0x03004AD4` first, then generates. This is the canonical progress code.
* **Pause screen** (`0x08015DE0`): calls the generator **without** that copy, so
  it re-emits the act byte left by the last validated code. After entering a
  salted code the pause password is therefore *self-consistent with the entered
  code*, not with the story act (observed: after `BMGQ`, pause showed `BMGQ`
  while `0x03004AF0` was `2`).

### Fresh-game behavior

A new game initialises the act to 2 (`0x080048E6`). With no checkpoint flags
set, the generator emits `n0 = 0`, `act = 2` → `BHGG`. This is what the pause
screen displays on a brand-new game, confirming the encoder against the ROM's
own output.

---

## 6. Tables

### 6.1 Published codes verified against the decoder

Sources: GameFAQs GBA cheats page (archived 2018 snapshot), SuperCheats,
GameRevolution. The lists agree on 12 codes except for the Day 3 code
(`CLGG` on GameFAQs/SuperCheats, `CLGC` on GameRevolution).

| Public code | Claimed level | Decoded n0 | Decoded act | ROM-valid? |
|---|---|---:|---:|---|
| `BHGG` | Day 1, London | 0 | 2 | yes |
| `CLGG` | Day 3, Paris | 1 | 2 | yes |
| `DCHJ` | Day 18, Train | 2 | 3 | yes |
| `FSHJ` | Day 20, Turkey | 3 | 3 | yes |
| `GKMN` | Day 25, India | 4 | 5 | yes |
| `HLSN` | Day 25, Wanted in India | 5 | 5 | yes |
| `JMBJ` | Day 40, China | 6 | 3 | yes |
| `KNQN` | Day 61, San Francisco | 7 | 5 | yes |
| `LPGG` | Day 61, Wild West | 8 | 2 | yes |
| `MQGG` | Day 61, Train to New York | 9 | 2 | yes |
| `NRGG` | Old Foe | 10 | 2 | yes |
| `PSGG` | Ending | 11 | 2 | yes |
| `CLGC` | Day 3, Paris (variant) | 1 | 0 | **no** — stored check bits `0x148` ≠ computed `0x44` (bit 12 set) |

`CLGC` is a transcription error; `CLGG` works, `CLGC` is rejected in-game.

None of the published code strings occurs literally anywhere in the ROM
(`grep -abo` empty for all 13), which rules out a plaintext preset table and is
consistent with the algorithmic format.

### 6.2 Complete accepted code space (84 codes)

Rows are the checkpoint index `n0`; columns are the act/salt field. Every entry
is accepted by the ROM. The public codes occupy the act-2, act-3 and act-5
columns; not every entry in those columns is public.

| n0 | level | act 0 | act 1 | act 2 | act 3 | act 4 | act 5 | act 6 |
|---:|---|---|---|---|---|---|---|---|
| 0 | Day 1 London | BFGB | BGGD | BHGG | BJGJ | BKGL | BLGN | BMGQ |
| 1 | Day 3 Paris | CGGB | CJGD | CLGG | CNGJ | CQGL | CSGN | CBHQ |
| 2 | Day 18 Train | DHGB | DMGD | DRGG | DCHJ | DHHL | DMHN | DRHQ |
| 3 | Day 20 Turkey | FJGB | FSGD | FJHG | FSHJ | FJJL | FSJN | FJKQ |
| 4 | Day 25 India | GKGB | GKHD | GKJG | GKKJ | GKLL | GKMN | GKNQ |
| 5 | Day 25 Wanted in India | HLGB | HLJD | HLLG | HLNJ | HLQL | HLSN | HLBQ |
| 6 | Day 40 China | JMGB | JMLD | JMQG | JMBJ | JMGL | JMLN | JMQQ |
| 7 | Day 61 San Francisco | KNGB | KNQD | KNGG | KNQJ | KNGL | KNQN | KNGQ |
| 8 | Day 61 Wild West | LPGB | LPGD | LPGG | LPGJ | LPGL | LPGN | LPGQ |
| 9 | Day 61 Train to New York | MQGB | MQGD | MQGG | MQGJ | MQGL | MQGN | MQGQ |
| 10 | Old Foe | NRGB | NRGD | NRGG | NRGJ | NRGL | NRGN | NRGQ |
| 11 | Ending | PSGB | PSGD | PSGG | PSGJ | PSGL | PSGN | PSGQ |

The same table is reproduced by the encoder in `pw.py`; a CSV copy is
`enum84.csv` in the work directory.

---

## 6b. Enumeration

### Space definition

| Quantity | Value |
|---|---|
| Input alphabet | 16 symbols (`BCDFGHJKLMNPQRST`) |
| Length | exactly 4 |
| Typeable strings | 16^4 = **65,536** |
| Payload | 4-bit checkpoint index (`n0`, 0–11) + 3-bit act (`0–6`) |
| Checksum | 8 bits, `((act << n0) + n0 + 0x43) & 0xFF` |
| Reserved | bit 12 must be 0 (9-bit comparison) |
| Accepted space | 12 × 7 = **84** (0.128 % of typeable strings) |
| Published subset | 12 (14.3 % of accepted space) |
| Novel subset | **72** |

### Novel codes generated and confirmed in-game

Each row was typed on the grid keyboard and submitted; the screenshot shows the
level intro after acceptance. All 12 use **act = 6**, a salt value absent from
every published list.

| Code | n0 | Level loaded (observed) | Screenshot |
|---|---:|---|---|
| `BMGQ` | 0 | LONDON, ENGLAND | `shots/novel_BMGQ_result.png`, `shots/enum_BMGQ.png` |
| `CBHQ` | 1 | PARIS, FRANCE / DAY 3 | `shots/enum_CBHQ.png` |
| `DRHQ` | 2 | DAY 18 (train) | `shots/enum_DRHQ.png` |
| `FJKQ` | 3 | TURKEY / DAY 20 | `shots/enum_FJKQ.png` |
| `GKNQ` | 4 | INDIA / DAY 25 | `shots/enum_GKNQ.png` |
| `HLBQ` | 5 | WANTED poster (Wanted in India) | `shots/enum_HLBQ.png` |
| `JMQQ` | 6 | CHINA / DAY 40 | `shots/enum_JMQQ.png` |
| `KNGQ` | 7 | DAY 61 SAN FRANCISCO | `shots/enum_KNGQ.png` |
| `LPGQ` | 8 | Wild West stage-coach scene | `shots/enum_LPGQ.png` |
| `MQGQ` | 9 | Train to New York gameplay | `shots/enum_MQGQ.png` |
| `NRGQ` | 10 | Old Foe street confrontation | `shots/enum_NRGQ.png` |
| `PSGQ` | 11 | Ending text (steamer to England) | `shots/enum_PSGQ.png` |

A 13th novel confirmation is `BFGB` (act 0, London), which proves the low end of
the act range is accepted: `shots/enum_BFGB.png`.

The pause screen after entering a novel code regenerates the same code, which
double-checks that the generator's inputs (`n0` from flags, act from
`0x03004AD4`) agree with the decoder:

* after `BMGQ`: `PASSWORD BMGQ` (`shots/60_pause_after_BMGQ.png`)
* after `KNGQ`: `PASSWORD KNGQ` (`shots/65_pause_after_KNGQ.png`), with flags
  13..19 set and `0x03004AD4 = 6`
* fresh NEW GAME (no code entered): `PASSWORD BHGG` (`shots/69_fresh_pause.png`),
  matching `encode(0, 2)`

### Bounds proven by rejection

| Test | Code | Why it must fail | Observed result |
|---|---|---|---|
| Act out of range | `BMGS` | act = 7, validator allows 0–6 | stays on password screen (`shots/rej_BMGS_after.png`) |
| Level index out of range | `MTGB` | n0 = 12, validator allows 0–11 | stays on password screen (`shots/rej_MTGB_after.png`) |
| Reserved bit set | `BHGH` | bit 12 = 1; 9-bit checksum compare | stays on password screen; second attempt clears the buffer (`shots/rej2_BHGH_after.png`, `shots/40_bhgh_submit.png`) |
| Bad checksum | `CLGC` | stored check bits `0x148` ≠ computed `0x44` (bit 12 set) | stays on password screen (`shots/rej2_CLGC_after.png`) |
| Too short (3) | `BHG` | length must be 4 | stays on password screen with DONE selected (`shots/rej_BHG3_after.png`) |
| Too short (2) | `BH` | length must be 4 | stays (`shots/rej_BH2_after.png`) |

Positive controls for the same checks: `BHGG` (published, act 2) loads London
(`shots/22_london_ok.png`), `CLGG` loads Paris (`shots/enum_CLGG.png`), `DCHJ`
loads Day 18, and `BFGB`/`BMGQ` load London at acts 0 and 6.

### Published list vs. ROM

All 12 distinct published codes decode as valid under the recovered model and
map to the 12 distinct levels. Three were entered literally (`BHGG`, `CLGG`,
`DCHJ`); the other nine were exercised through their act-6 counterparts, which
have the same `n0` and therefore the same level handler. The 13th published
string (`CLGC`) is invalid in the ROM and is a typo.

---

## 7. Validation evidence

**Observed (emulator / live memory)**

* Main menu, password grid, options, in-game pause, pause options and sleep
  prompt all walked and screenshotted.
* `BHGG` → `LONDON, ENGLAND`; `CLGG` → `PARIS, FRANCE / DAY 3`; `DCHJ` →
  `DAY 18`; 12 novel act-6 codes → all 12 checkpoint intros.
* Rejections listed in §6b stay on the password screen; the buffer is cleared
  after two consecutive failures.
* Buffer read from IWRAM after typing `BHGG`: `00 05 04 04` at `0x030014F8`,
  length 4 at `0x03001530`; after `BMGQ`: `00 09 04 0C`, `0x03004AD4 = 6`,
  `0x03004AF0 = 2`.
* At the generator breakpoint (`0x08001554`) after a `KNGQ` warp:
  `0x03004AD4 = 6`, `0x03004AF0 = 2`, flags 13..19 = 1, output buffer
  `07 0A 04 0C` = `KNGQ`.
* Fresh NEW GAME: pause screen displays `PASSWORD BHGG`.
* Sleep mode: pause → SLEEP MODE → YES shows the "ENTER SLEEP MODE?" prompt and
  the `SELECT+L+R` exit instruction (`shots/57_sleep_prompt.png`).

**Derived (instruction-level)**

* Validator conditions and the 9-bit checksum comparison (`0x080012BC`).
* Encoder formula and flag-derived checkpoint index (`0x08001554`).
* Success path clears flags (`0x0800F250`) and sets flags `13..12+n0`
  (`0x0800F220`) before writing map/spawn globals.
* Results screen copies `0x03004AF0` into `0x03004AD4`; pause screen does not.

**Inferred**

* The 3-bit field is a story "act" value: it starts at 2, is incremented when
  the 16-bit progress counter at `0x03001508` exceeds `0x4F`, and is stored in
  the save block at `0x03004AF0`. Its exact label (act vs. chapter vs. region)
  is not proven.
* The activation of checkpoints by the password path relies on setting flags
  13..12+n0; why a fresh game does not set the London flag is consistent with
  `n0 = 0` having no flag.

---

## 8. Unknowns

* The precise meaning of the act byte beyond "carried story value". The
  `0x03001508 > 0x4F` increment path was read but not exercised dynamically.
* Whether the act value is ever 7 in normal play. The generator clamps >6 to 7,
  which would produce a code its own validator rejects; the increment code also
  clamps at 6, so this is probably unreachable (latent bug, not observed).
* The IWRAM word at `0x03004ACC`, copied on successful validation, was not
  traced to its consumers.
* Save format: no `.sav` data was written during boot/level-1 play (the created
  file stayed 0 bytes) and the title menu has no CONTINUE entry; long-term
  saving was not exercised, so the cart's save type is not established here.
* The "I LIKE MONKEYS" text block at `0x1425E0` (a well-known Internet copypasta
  followed by `I like monkeys` and the build stamp) has no direct pointer and
  was not reached through any menu; it is reported as embedded but unreferenced,
  not proven unreachable by every script path.
* No button-code system was found in the menus. The bound is: a string scan of
  the whole ROM gives **0** hits for `cheat`, `debug`, `code` and `unlock`; the
  only multi-button combo named anywhere is the sleep-mode `SELECT+L+R`; and the
  password/main/options/pause input handlers keep no sequence counter — their
  only persistent writes are cursor (`0x030013FC`), row/column, buffer, length,
  failure count and the act/flag/map variables. Every menu action is accounted
  for by the decoded jump table. A gameplay-level button-code path (which would
  need its own state machine outside the menus) was not located.

---

## 9. Tooling

* `mgba-sdl` 0.10.5, `Xvfb :144`, `openbox`, `xdotool`, `scrot`,
  ImageMagick (`convert`).
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`
  for the Thumb validator, generator and handlers.
* `gdb-multiarch` over mGBA's GDB stub (`mgba -g`, port 2345) for live RAM
  reads; the stub pauses the emulator on attach, so a FIFO-driven async gdb
  session was used (`continue &` / `interrupt`).
* Python 3 scripts in the work directory: `pw.py` (encoder/decoder + 84-code
  enumeration), `enum84.csv`, `key.py`/`test_code.py`/`loop_codes.py`/`reject.py`
  (X11 input and screenshot automation), `ptr.py`/Capstone scans for pointer and
  literal-load searches.
* Screenshots referenced above are in `/tmp/opencode/atw80/shots/` (analysis
  artifacts; not part of the repository).

**Lesson for the guide.** Two checksum traps showed up here and are worth
generalising: (1) a comparison against a shifted mask can be wider than the
computed check value (`lsls #19; lsrs #23` = 9 bits, not 8), silently requiring
a reserved bit to be zero; and (2) a "salt"/version field can be validated and
carried by a password without selecting the level, so the level mapping must be
read from the dispatch table, not from the whole code value.

---

## Legal note

No ROM, extracted graphics, audio or text bank is redistributed here. The
report contains addresses, hashes, algorithms and independently generated code
strings only. Game text quoted in the analysis (menu labels) is factual
description, not an asset dump.
