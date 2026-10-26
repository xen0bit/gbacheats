# 2 Games in 1 — Scooby-Doo! Mystery Mayhem & Scooby-Doo! and the Cyber Chase (GBA) — RE Report

Report generated from a local ROM analysis on 2026-10-24; progress-password
work completed 2026-10-26.
Methodology: [`GBA_REVERSE_ENGINEERING_GUIDE.md`](../../GBA_REVERSE_ENGINEERING_GUIDE.md)

Scope note: **in-game / developer-intended cheats only.**
GameShark/CodeBreaker/RAM-patch codes are out of scope.

---

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/2 Games in 1 - Scooby-Doo! - Mystery Mayhem & Scooby-Doo! and the Cyber Chase/2 Games in 1 - Scooby-Doo! - Mystery Mayhem & Scooby-Doo! and the Cyber Chase.gba` |
| Size | 8 MiB (`0x800000`) |
| Header title | `SD_CC&MH_EFG` |
| Game code | `BCVE` |
| Maker code | `78` |
| Software version | `0` |
| MD5 | `7bd5ae371d67113ad2c01109607b418b` |
| SHA-1 | `78e1ac7414be6eba0c016d191df34e954a1d3bb6` |
| SHA-256 | `c1b8c1ba5ab376563a91829ac4e8801382219854919e96208070a1ff5dbb0ada` |

### Layout

| Range | Contents |
|---|---|
| `0x000000`–`0x3FFFFF` | Mystery Mayhem image (header `SD_CC&MH_EFG`, `BCVE`) |
| `0x400000`–`0x7FFFFF` | Cyber Chase image (header `SCOOBY CYBER`, `ASDE`, maker `01`) |

The boot selector ("SCOOBY DOO MYSTERY MAYHEM" / "SCOOBY DOO AND THE CYBER CHASE")
is in the first image; the shared shell menu (New Game / Load Game / Options /
Credits) is what `Start` opens, and it launches each game's own menu.

All addresses below are ROM addresses in the 8 MiB image (`0x08400000` = file
`0x400000`). Subtract `0x400000` to compare with the standalone 4 MiB Cyber
Chase build (which differs slightly, MD5 `1e3fd614dc43edbbf9df51262057f2cc`).

---

## 2. Executive summary

The **Cyber Chase** half has **two independent code systems on the same
password screen**, both using the same 32-symbol alphabet:

1. **Special codes** — 15 literal `strcmp` strings (`GL@D1@TR`, `CHTMD2`, …).
   They set flags, or store a level/checkpoint id and a message id, and start a
   level or scene directly.
2. **Progress passwords** — 8 symbols, 40 bits, with a per-column Caesar key and
   **six interleaved even-parity bits**. They restore a score, a level
   checkpoint, a 2-bit area and eight scene flags. This system is now fully
   reversed and reimplemented (`codec.py` below); every published code decodes,
   and a previously unpublished **arcade** progress password (`2747#VBB`) was
   minted and confirmed in mGBA.

Key facts:

* Alphabet `BCDFGHJKLMNPQRSTVWXYZ123456789@#` (32 symbols at `0x087FAE1C`;
  the on-screen grid shows the same symbols as capitals, the script text at
  `0x42F580` spells them lowercase).
* 8 symbols × 5 bits = 40 bits. Bits 0–33 are data; bits 34–39 are six
  even-parity bits over sliding 6-bit windows.
* Per-column keys `[10,5,8,5,12,14,3,2]` (8 × `u32` at `0x087FAE3C`) are
  *added* mod 32 when decoding and *subtracted* when encoding.
* Payload: score (20 bits), level/checkpoint (4 bits), area (2 bits), five scene
  flags (5 bits) and three object-spawn flags (3 bits) = 34 data bits.
* Level/checkpoint ids 1–12 map to the six levels (table in §6.4); 0 and 13–15
  are format-valid but have no checkpoint (the dispatch table only covers 0–12).
* All seven published codes are accepted by the ROM; no code typo was
  found. The only typo in the published material is the label
  "PERHISTORIC JUNGLE" (the code `L4M9@VZS` is correct). The public list has no
  arcade progress password — `2747#VBB` fills that gap.

Mystery Mayhem has no password strings and no ASCII cheat text; only
memory-editing codes exist publicly, so it was not analysed further.

---

## 3. How to reproduce

```bash
sudo apt-get install -y mgba-sdl xvfb xdotool imagemagick openbox
Xvfb :198 -screen 0 1024x768x24 &
DISPLAY=:198 openbox &
DISPLAY=:198 SDL_AUDIODRIVER=dummy mgba -3 "2 Games in 1 - ....gba" &
```

Keymap: A=`x`, B=`z`, Start=`Return`, Select=`BackSpace`, D-pad arrows.
Hold ~180 ms. `openbox` is needed for key delivery; capture with
`import -window <wid>`.

### Path to the Cyber Chase password screen

```
Boot selector: Right -> SCOOBY DOO AND THE CYBER CHASE, A
 -> THQ / WB / Creations logos -> title
 -> Start  -> MAIN MENU (NEW GAME / PASSWORD / OPTIONS)
 -> Down, A -> PASSWORD grid (Select = try password)
```

The title screen needs `Start` after the "Press Start" prompt appears; pressing
`Start` during the logo sequence is ignored.

### Password-screen navigation (for hand entry)

The 32 symbols are drawn as eight 4-symbol columns. Reading the grid:

```
column:  0    1    2    3    4    5    6    7
row 0:   B    C    D    F    G    H    J    K
row 1:   L    M    N    P    Q    R    S    T
row 2:   V    W    X    Y    Z    1    2    3
row 3:   4    5    6    7    8    9    @    #
```

`Right`/`Left` move one column, `Up`/`Down` one row (edges clamp), `A` appends
the highlighted symbol and the cursor stays put, `B` deletes. `Select` submits.

### Codes exercised

| Input | Observed |
|---|---|
| `4J172VBQ` + Select | accepted; hub starts, score `030050`; level select cursor on COLISEUM |
| `MXP#2VBL` + Select | accepted; hub score `151283` |
| `QWC85VBS` + Select | accepted; level select cursor on OCEAN CHASE |
| `CHBB5VBX` + Select | accepted; hub score `172363` |
| `L4M9@VZS` + Select | accepted; level select cursor on PREHISTORIC JUNGLE |
| `JVR89VBN` + Select | accepted; level select cursor on SNOW CHASE |
| `X@X#V7FF` + Select | accepted; level select cursor on BOARDWALK |
| `2747#VBB` + Select | accepted; level select cursor on ARCADE; arcade starts |
| `2747#VBC` + Select | rejected → MAIN MENU (bad parity) |
| `2747#VB` (7 chars) + Select | rejected → MAIN MENU (length) |
| `2747CVBB` (level 13) + Select | accepted by the checksum, but no checkpoint is applied |
| `CHTMD2` + Select | `0x03001AB0` changed `0` → `1` (cheat mode on) |

---

## 4. Address map

| ROM address | What |
|---:|---|
| `0x08409130` | password input handler: length-8 progress path and special-code path |
| `0x0841CD20` | progress-password validator (decode + key-add + parity) → 0/1 |
| `0x0841CD5C` | char → alphabet index (linear search over 32 bytes) |
| `0x0841CBA8` | 8 chars → packed 40-bit symbol buffer (and re-render) |
| `0x0841CAB8` | add per-column keys (decode direction) |
| `0x0841C9C8` | subtract per-column keys (encode direction) |
| `0x0841C8B8` | parity verify (six check bits) |
| `0x0841C7A4` | parity insert (encoder) |
| `0x0841C50C` | encoder: player state → 8-char password |
| `0x0841C6C4` | apply decoded progress payload to player state |
| `0x0841C0F0` | level id → spawn area (`+0x164`) + flag mask (`+0x168`); 13-entry jump table at `0x0841C134` |
| `0x0841C278` | special-code chain (`strcmp` per code) |
| `0x087FAE1C` | 32-byte progress alphabet |
| `0x087FAE3C` | 8 × `u32` per-column keys |
| `0x0840A294` | in-game combo check: held `0x200` (L) + pressed `0x004` (Select) + cheat flag |

Special-code string table (not a fixed 8-byte stride — entries are 8-byte
NUL-padded strings with 4-byte alignment gaps):

| Code | File offset | ROM address |
|---|---:|---:|
| `GL@D1@TR` | `0x4305A8` | `0x084305A8` |
| `JVNGLDVP` | `0x4305B4` | `0x084305B4` |
| `SPL@SH` | `0x4305C0` | `0x084305C0` |
| `1C3R@LLY` | `0x4305C8` | `0x084305C8` |
| `BSYDTH3C` | `0x4305D4` | `0x084305D4` |
| `@MVZM3NT` | `0x4305E0` | `0x084305E0` |
| `1CR33P3R` | `0x4305EC` | `0x084305EC` |
| `GH@TRGHL` | `0x4305F8` | `0x084305F8` |
| `1R@NFYC3` | `0x430604` | `0x08430604` |
| `WH@DNN1T` | `0x430610` | `0x08430610` |
| `PSKYK1DS` | `0x43061C` | `0x0843061C` |
| `VRSN1` | `0x430628` | `0x08430628` |
| `VRSN2` | `0x430630` | `0x08430630` |
| `CHTMD1` | `0x430638` | `0x08430638` |
| `CHTMD2` | `0x430640` | `0x08430640` |

RAM (2-in-1 build; player-state base `0x02006EA0`, which is also the 8-byte
password text buffer at `base+0`):

| Address | Use |
|---|---|
| `0x03001AB0` | cheat-mode flag (set by `CHTMD1`/`CHTMD2`) |
| `0x03001228` | version-display flag (`VRSN1` = 0, `VRSN2` = 1) |
| `state+0x104` | score, the 6-digit HUD counter (20 bits) |
| `state+0x19C` | level/checkpoint id (4 bits) |
| `state+0x1A0` | area/sub field (2 bits) |
| `state+0x138` | five scene flags (bits 0–4) |
| `state+0x1A4/0x1A8/0x1AC` | three object-spawn flags |
| `state+0x164` | spawn area, derived from the level id |
| `state+0x168` | level-derived flag mask |
| `0x02006EA0` | state base; bytes 0–7 are the entered password |

State-field addresses are relative to `0x02006EA0`. They were verified both by
reading `state+0x104` after code entry and by reading the on-screen counter.

---

## 5. Algorithm

### 5.1 Progress passwords

```c
// character values: idx = position of ch in "BCDFGHJKLMNPQRSTVWXYZ123456789@#"
// decode
u64 p = 0;
for (i = 0; i < 8; i++)
    p |= ((u32)(idx[i] + key[i]) & 31) << (5*i);   // key[] = {10,5,8,5,12,14,3,2}

bool valid = true;
for (i = 0; i < 6; i++) {
    int start = (i == 5) ? 30 : 6*i;
    int n     = (i == 5) ?  4 : 6;
    int check = (p >> (39 - i)) & 1;
    if (check != (popcount((p >> start) & ((1<<n)-1)) & 1))
        valid = false;
}
```

`p` bits 0–33 are data, bits 34–39 are the parity bits. The encoder runs the
same steps backwards: build the 34 data bits, compute the six parity bits and
write them at bits 39..34, then subtract the keys and index the alphabet.

Field layout:

| Bits | Field | Stored at |
|---|---|---|
| 0–19 | score (20 bits) | `state+0x104` |
| 20–23 | level/checkpoint id | `state+0x19C` |
| 24–25 | area/sub (2 bits) | `state+0x1A0` |
| 26,27,29,28,30 | scene flags 0–4 | `state+0x138` |
| 31 | object flag A | `state+0x1A4` |
| 32 | object flag B | `state+0x1A8` |
| 33 | object flag C | `state+0x1AC` |

Note the bit order of the five scene flags: flag bit 0→payload bit 26, 1→27,
2→29, 3→28, 4→30. After decoding, the game runs `0x0841C0F0`, which converts
the level id into a spawn area (`+0x164`) and a level-derived mask (`+0x168`).

In-game combo gate (`0x0840A294`):

```c
if ((held & 0x200) && (pressed & 0x004) && *(u32*)0x03001AB0)
    apply_cheat();
```

### 5.2 Special codes

```c
// 0x0841C278, simplified
int try_special(char *in, State *s) {
    if (!strcmp(in, "GL@D1@TR")) { s->level = 1;  s->chk = 0; return 0x0C; }
    if (!strcmp(in, "JVNGLDVP")) { s->level = 6;  s->chk = 0; return 0x17; }
    if (!strcmp(in, "SPL@SH"))   { s->level = 3;  s->chk = 0; return 0x0A; }
    if (!strcmp(in, "1C3R@LLY")) { s->level = 8;  s->chk = 0; return 0x16; }
    if (!strcmp(in, "BSYDTH3C")) { s->level = 11; s->chk = 0; return 0x1E; }
    if (!strcmp(in, "@MVZM3NT")) { s->level = 11; s->chk = 0; return 0x1B; }
    if (!strcmp(in, "1CR33P3R")) { s->level = 1;  s->chk = 0; return 0x19; }
    if (!strcmp(in, "GH@TRGHL")) { s->level = 6;  s->chk = 0; return 0x27; }
    if (!strcmp(in, "1R@NFYC3")) { s->level = 11; s->chk = 0; return 0x23; }
    if (!strcmp(in, "WH@DNN1T")) { s->level = 11; s->chk = 0;
                                   s->f1=s->f2=s->f3=1; return 0x26; }
    if (!strcmp(in, "PSKYK1DS")) { s->level = 11; s->chk = 0;
                                   s->f1=s->f2=s->f3=1;
                                   *(u32*)((u8*)s+0x144) = 0x07AA0000;
                                   return 0x22; }
    if (!strcmp(in, "VRSN1"))    { *(u32*)0x03001228 = 0; return ...; }
    if (!strcmp(in, "VRSN2"))    { *(u32*)0x03001228 = 1; return ...; }
    if (!strcmp(in, "CHTMD1"))   { *(u32*)0x03001AB0 = 1; return 0x4E; }
    if (!strcmp(in, "CHTMD2"))   { *(u32*)0x03001AB0 = 1; return 0x4E; }
    return failure;   // 0xFFFF
}
```

The special-code handler stores the id in `state+0x19C` but **does not** run the
level→area conversion; the caller uses the returned message id to select the
scene (this is why `1R@NFYC3` can start the Old Iron Face boss fight even though
it stores id 11, which the *progress* path treats as Arcade).

---

## 6. Tables

### 6.1 Cyber Chase special codes

| Code | Stored level id | Message id | Effect |
|---|---:|---:|---|
| `GL@D1@TR` | 1 | `0x0C` | Coliseum ("Gladiator") |
| `JVNGLDVP` | 6 | `0x17` | Prehistoric Jungle ("Jungle Deep") |
| `SPL@SH` | 3 | `0x0A` | Ocean Chase ("Splash") |
| `1C3R@LLY` | 8 | `0x16` | Snow Chase ("Ice Rally") |
| `BSYDTH3C` | 11 | `0x1E` | Boardwalk (message id selects the scene) |
| `@MVZM3NT` | 11 | `0x1B` | Arcade ("Amazement") |
| `1CR33P3R` | 1 | `0x19` | Coliseum, Creeper |
| `GH@TRGHL` | 6 | `0x27` | Jungle, Gator Ghoul |
| `1R@NFYC3` | 11 | `0x23` | Boardwalk, Old Iron Face |
| `WH@DNN1T` | 11 | `0x26` | View the ending; sets 3 flags |
| `PSKYK1DS` | 11 | `0x22` | Arcade with everything; 3 flags + float `0x07AA0000` |
| `VRSN1` | — | — | `0x03001228 = 0` |
| `VRSN2` | — | — | `0x03001228 = 1` |
| `CHTMD1` | — | `0x4E` | `0x03001AB0 = 1` |
| `CHTMD2` | — | `0x4E` | `0x03001AB0 = 1` (verified) |

### 6.2 Password alphabet

```
B C D F G H J K
L M N P Q R S T
V W X Y Z 1 2 3
4 5 6 7 8 9 @ #
```

No vowels and no `0`; `@` replaces `a` and `#` replaces `0`. The on-screen grid
shows this as eight 4-symbol columns (see §3).

### 6.3 Progress-password keys and checksum

| Position | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Key | 10 | 5 | 8 | 5 | 12 | 14 | 3 | 2 |

| Check bit | Stored at | Parity over payload bits |
|---|---:|---|
| 0 | 39 | 0–5 |
| 1 | 38 | 6–11 |
| 2 | 37 | 12–17 |
| 3 | 36 | 18–23 |
| 4 | 35 | 24–29 |
| 5 | 34 | 30–33 (4 bits) |

### 6.4 Level / checkpoint mapping

The 4-bit field is a **checkpoint id**, not the level-select list index. Ids 1
and 2 are Coliseum, 3–5 Ocean Chase, 6, 7 and 10 Prehistoric Jungle, 8–9 Snow
Chase, 11 Arcade and 12 Boardwalk. The published label fixes 2/5/9/10/12; the
special warps fix 1/3/6/8/11; 4 and 7 were checked with minted progress codes
(selecting Ocean/Jungle starts those levels) and sit between their neighbours.

| id | Level | Evidence |
|---:|---|---|
| 1 | Coliseum | `GL@D1@TR` → COLISEUM intro; minted `27471VBB` shows Coliseum as the available level |
| 2 | Coliseum | published `4J172VBQ` / `MXP#2VBL` |
| 3 | Ocean Chase | `SPL@SH` → OCEAN CHASE intro; minted `27473VB@` shows Ocean as available |
| 4 | Ocean Chase | minted `27474VBB`; selecting Ocean starts OCEAN CHASE |
| 5 | Ocean Chase | published `QWC85VBS` / `CHBB5VBX` |
| 6 | Prehistoric Jungle | `JVNGLDVP` / `GH@TRGHL` → JUNGLE / Gator Ghoul; minted `27476VB@` |
| 7 | Prehistoric Jungle | minted `27477VBB`; selecting Jungle starts PREHISTORIC JUNGLE |
| 8 | Snow Chase | `1C3R@LLY` → SNOW CHASE intro; minted `27478VBB` |
| 9 | Snow Chase | published `JVR89VBN` |
| 10 | Prehistoric Jungle | published `L4M9@VZS` |
| 11 | Arcade | `@MVZM3NT` / `PSKYK1DS` → ARCADE; minted `2747#VBB` → arcade |
| 12 | Boardwalk | published `X@X#V7FF` |

Ids 0 and 13–15 have no checkpoint: `0x0841C0F0` has a `cmp #12; bhi` guard and
a 13-entry jump table (index 0 is a no-op), so the id is stored but no spawn
area is applied.

### 6.5 Published progress codes

| Published label | Code | id | score | Status |
|---|---|---:|---:|---|
| Coliseum | `4J172VBQ` | 2 | 30050 | accepted, score matches |
| Ocean Chase | `QWC85VBS` | 5 | 42710 | accepted |
| Prehistoric Jungle | `L4M9@VZS` | 10 | 83890 | accepted |
| Snow Chase | `JVR89VBN` | 9 | 54960 | accepted |
| Boardwalk | `X@X#V7FF` | 12 | 157820 | accepted |
| Coliseum (alt) | `MXP#2VBL` | 2 | 151283 | accepted, score matches |
| Ocean Chase (alt) | `CHBB5VBX` | 5 | 172363 | accepted, score matches |
| **Arcade (new)** | **`2747#VBB`** | **11** | **0** | **accepted, arcade starts** |

No code typo was found in the published lists; the only text typo is the
"PERHISTORIC JUNGLE" label in the GameFAQs guide (the game's own intro reads
"PREHISTORIC JUNGLE", and the code `L4M9@VZS` is correct). The mofunzone page
truncates its table (`Coliseum: MXP`, `Prehistoric Jungle: 5S`); the
reconstructed full codes `MXP#2VBL` and `CHBB5VBX` are valid and accepted, so
that is a page-rendering artifact, not a game typo. The public list contains no
arcade password, which §6b fills.

---

## 6b. Enumeration

### Space

* Alphabet: 32 symbols, length exactly 8 → **32^8 = 2^40 = 1,099,511,627,776**
  possible strings.
* Six parity bits → a random string passes with probability 1/64, so the
  checksum-valid set is **2^34 = 17,179,869,184** codes.
* Of those, the data fields are: score 20 bits, level 4 bits, area 2 bits,
  scene flags 5 bits, object flags 3 bits = 34 bits. Every checksum-valid code
  is accepted by the decoder; only the level id is range-checked later
  (`1..12` meaningful, `0`/`13..15` store without a checkpoint), so
  **12 × 2^30 = 12,884,901,888** codes carry a mapped checkpoint.
* The special-code system is a disjoint literal list of 15 strings (no overlap
  with the 8-symbol progress format because it accepts other lengths).

### Novel code (not in any published list)

**`2747#VBB`** — score 0, checkpoint 11 (Arcade), area 0, default flags.

* No published list contains an arcade progress password; the only published
  arcade access is the special code `PSKYK1DS` ("At the Arcade with
  Everything"), which is a different format and sets different flags.
* Verified in mGBA: entry → hub → level select (cursor on ARCADE) → select
  ARCADE → arcade intro → arcade gameplay. Screenshots:
  * `screenshots/password_novel_2747_VBB.png`
  * `screenshots/levelselect_arcade_2747_VBB.png`
  * `screenshots/arcade_intro_2747_VBB.png`
  * `screenshots/arcade_gameplay_2747_VBB.png`

### Bounds proven by rejection

| Input | Why it is outside the format | In-game result |
|---|---|---|
| `2747#VBC` | last symbol changed → parity mismatch | rejected, returns to MAIN MENU (`screenshots/rejected_checksum_2747_VBC.png`) |
| `2747#VB` (7 chars) | length ≠ 8 | rejected, returns to MAIN MENU |
| `2747CVBB` | level field 13 (valid checksum, unmapped checkpoint) | accepted by the checksum; no checkpoint applied (dispatch table covers only 0–12) |

The 6-character and 5-character special codes (`SPL@SH`, `VRSN1`) are handled by
the separate literal chain, not by the progress decoder.

---

## 7. Validation evidence

**Observed (emulator, screenshots)**
* The on-screen grid has the 32 symbols arranged as eight 4-symbol columns.
* `4J172VBQ` → hub with score `030050`; level-select cursor on COLISEUM.
* `MXP#2VBL` → score `151283`; `CHBB5VBX` → score `172363`; both equal the
  decoded 20-bit field exactly, confirming the score field.
* `QWC85VBS` → cursor on OCEAN CHASE; `L4M9@VZS` → JUNGLE; `JVR89VBN` → SNOW;
  `X@X#V7FF` → BOARDWALK.
* `2747#VBB` → cursor on ARCADE; ARCADE intro and gameplay.
* `2747#VBC` and 7-character input → MAIN MENU.
* `CHTMD2` → `0x03001AB0` 0 → 1 (GDB).
* Special warps: `GL@D1@TR` → COLISEUM, `SPL@SH` → OCEAN, `JVNGLDVP` →
  JUNGLE, `1C3R@LLY` → SNOW, `@MVZM3NT` → ARCADE, `1R@NFYC3` → Old Iron Face.

**Derived (disassembly)**
* The decoder (`0x0841CD20`), key addition (`0x0841CAB8`), parity
  verification (`0x0841C8B8`), encoder (`0x0841C50C`), checksum insert
  (`0x0841C7A4`), payload→state mapping (`0x0841C6C4`), and level→area
  dispatcher (`0x0841C0F0`) were read instruction by instruction; the codec in
  §9 reproduces every published code byte-for-byte.
* The special-code chain and its 15 string literals.

**Inferred**
* The flag bits at `+0x138`, `+0x1A4`, `+0x1A8`, `+0x1AC` are scene/object
  spawn toggles: `0x08406218` tests the three `+0x1A4`-family flags and spawns
  objects at fixed screen coordinates; `+0x138` is read by the same scene code
  and by the HUD. Their exact per-level meaning is bounded but not named.
* `CHTMD1` and `CHTMD2` are equivalent in this build (same flag, same message).

---

## 8. Unknowns

The progress-password decoder and the level-name mapping are closed; the items
below are outside that scope or bounded to specific consumers.

* Mystery Mayhem: no password system found in strings/scripts; not analysed.
* The shell menu's "Load Game" screen (7 empty boxes) is not explained; it may
  be save slots only.
* Exact per-level meaning of the eight flag bits (`+0x138`, `+0x1A4`, `+0x1A8`,
  `+0x1AC`). They are written by the decoder and consumed by scene/object code
  (e.g. `0x08406218`); they are not needed to restore score/level and every
  published code accepts them in several combinations.
* Full effect list of the in-game combos gated by `0x03001AB0` (only the
  `L + Select` gate at `0x0840A294` was decoded).
* Ids 0 and 13–15 store without a checkpoint; no code using them is meaningful,
  and no crash was observed.

---

## 9. Tooling

`codec.py` (Python 3, no dependencies) is the reference implementation:

```python
ALPHA = "BCDFGHJKLMNPQRSTVWXYZ123456789@#"
KEYS  = [10, 5, 8, 5, 12, 14, 3, 2]
WINDOWS = [(0,6),(6,6),(12,6),(18,6),(24,6),(30,4)]

def parity(x, start, n):
    return bin((x >> start) & ((1 << n) - 1)).count('1') & 1

def encode(A=0, level=0, sub=0, flags138=0, f31=0, f32=0, f33=0):
    p = (A & 0xFFFFF) | ((level & 0xF) << 20) | ((sub & 3) << 24)
    for i, bitpos in enumerate([26, 27, 29, 28, 30]):
        if (flags138 >> i) & 1:
            p |= 1 << bitpos
    p |= (f31 & 1) << 31
    p |= (f32 & 1) << 32
    p |= (f33 & 1) << 33
    for i, (s, n) in enumerate(WINDOWS):
        pos = 39 - i
        p = (p | (1 << pos)) if parity(p, s, n) else (p & ~(1 << pos))
    syms = [((p >> (5*i)) & 31) - KEYS[i] & 31 for i in range(8)]
    return ''.join(ALPHA[s] for s in syms)

def decode(code):
    idx = [ALPHA.index(c) for c in code.upper()]
    syms = [(idx[i] + KEYS[i]) & 31 for i in range(8)]
    p = sum(s << (5*i) for i, s in enumerate(syms))
    ok = all(((p >> (39-i)) & 1) == parity(p, s, n)
             for i, (s, n) in enumerate(WINDOWS))
    return dict(code=code, payload=p, valid=ok, score=p & 0xFFFFF,
                level=(p >> 20) & 0xF, sub=(p >> 24) & 3,
                f31=(p >> 31) & 1, f32=(p >> 32) & 1, f33=(p >> 33) & 1)
```

Other tooling:

| Method | Purpose |
|---|---|
| header scan | split the 8 MiB image into the two 4 MiB games |
| `grep -abo` / `strings` | found `VRSN1`, `CHTMD1/2`, the leetspeak code table |
| script text (`$password_dis`, `$displaypassword`) | recovered the alphabet, Select=submit, and the level-complete password display |
| Thumb disassembly (`objdump -M force-thumb`) | decoded the codec, parity, key table, special chain, level dispatcher |
| mGBA savestates | located the player-state base (`0x02006EA0`); injecting the 8-byte text buffer allowed deterministic code tests |
| xdotool + `import -window` | drove the menus and captured evidence |

No ROM, graphics, or text from the games is redistributed here; only addresses,
algorithms, and short identifiers needed to describe the cheats.
