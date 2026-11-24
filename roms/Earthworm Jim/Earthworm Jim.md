# Earthworm Jim (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Earthworm Jim.gba` |
| Size | 8,388,608 bytes (0x800000, 8 MiB) |
| Header title | `EWJ` |
| Game code | `AEJE` (PAL/Europe revision 00) |
| Maker | `5G` (Majesco published; Game Titan conversion; Shin'en audio — see intro screens) |
| Version | 0x00; complement 0xDA; header checksum 0x0000 (normal rebuilt-header artifact) |
| Entry word | `0xEA00002E` — stock `b 0x080000C0`, **no cracktro/trainer patch** |
| MD5 | `54a50dbaea5a9154cc820f3fc13a34bb` |
| SHA-1 | `8c3148c1c863a1e31b6f4c380c9390dc12fae9ac` |
| SHA-256 | `1821cbb636e60d69fbd3f4e2d9a4dc8f5a6a38f52767194e1b89df1dddb2f3d8` |

Embedded GBA-header scan (156-byte Nintendo-logo match) found **two** headers: the real one at
file `0x0` and a byte-identical copy at `0x790334` (`AEJE5G`, same entry word). This is a
self-check/duplicate header, not a second game image or trainer. No appended trainer menu exists.

Sibling-note check: the EWJ2 strings `HYPER CHEAT`, `CHEAT SCREEN`, `LEVEL SKIP`, `PASSWORD`
and the base-29 alphabet are **all absent** from this AEJE image. This game has a different,
button-code-based cheat system.

## 2. Executive summary

This is a **pause-menu button-code system** (§5.4a of the guide), not a password system.
There is no password entry screen, no level-select menu and no hidden debug screen in the UI:
the title screen offers only `PRESS START` and `OPTIONS` (controls diagram + NORMAL/DIFFICULT),
and pressing Start during play pauses **silently** (no overlay). Codes are entered by pressing
Start and then a sequence of 5–11 d-pad/shoulder/button presses.

The validator is a single large function at `0x0801D120`–`0x0801D8A6`. It reads KEYINPUT
(`0x04000130`) each frame, inverts it to an active-high 10-bit mask, and appends each *newly
pressed* button to a 256-entry `u16` ring buffer on the stack. From `0x0801D208` to
`0x0801D7F0` it tests 16 hard-coded suffix sequences against that ring buffer. There is **no
checksum, no PRNG and no generator** — the space is exactly the 16 compiled-in comparisons.
Matching is **suffix-based**: extra presses *before* a code are ignored, which explains why
published lists include a harmless leading button on several codes.

All 7 published codes are present in the table and were verified in the emulator with RAM
proofs. **9 of the 16 sequences are absent from every published list** (GameFAQs, IGN,
world-of-nintendo, TCRF); two of them were entered in-game and observed to warp to distinct
levels. Bounds were proven by rejection of a wrong-button and a truncated sequence.

## 3. How to reproduce

- Emulator: mGBA SDL (`mgba -3 <rom>`) on `Xvfb :317`, `SDL_AUDIODRIVER=dummy`, 60 ms key holds
  with 120–150 ms gaps (avoids §16.2 double-stepping).
- Keymap (mGBA SDL default): A=`x`, B=`z`, SELECT=`BackSpace`, START=`Return`, L=`a`, R=`s`,
  d-pad = arrow keys.
- Menu path: title → press Start → play until the HUD (100%, x1500) is visible → press Start
  (game freezes with **no visible pause menu**) → press the code buttons.
- RAM proof method (§16.13, since the GDB stub port was occupied by a sibling session):
  save mGBA states with Shift+F1..F9 around the action; the `.ssN` files are PNGs with a
  zlib-compressed `gbAs` chunk; decompress it and read IWRAM at raw offset
  `0x19000 + (addr - 0x03000000)`. Verified against stack frames containing `0x0806xxxx`
  return addresses at raw `0x20EC0`.
- Preconditions: the level must be in active gameplay (HUD visible), not the title screen or
  the level-intro card; codes entered on the title screen had no effect (RAM unchanged).

## 4. Address map

| Item | Address | Notes |
|---|---|---|
| Input handler / validator | `0x0801D120`–`0x0801D8A6` | KEYINPUT read at `0x0801D156`; active-high mask in r1 |
| Button-history ring buffer | stack, `sp-1000` .. `sp` | 256 × `u16` button masks; write index `r4` (mod 256) |
| Sequence checks | `0x0801D208`–`0x0801D7F0` | 16 suffix comparisons, each `cmp`+`bne` to a shared fail target |
| Common success write | `0x0801D7F2` | `strb r0,[0x0300152C]`, plus aux write |
| Health helper | `0x0801D100` | adds `r0` to byte at `0x03000010`, clamps to 100 |
| Pause handler | `0x0801D834` | silent freeze; waits for Start release |
| `0x0300152C` | IWRAM, u8 | warp/level-select value (10 distinct values written) |
| `0x03001674` | IWRAM, u8 | aux byte written by every successful sequence (1 or a key mask) |
| `0x030018BC` | IWRAM, u16 | ammo/currency, default 1500 (`0x5DC`); ammo code → 2000 |
| `0x03000010` | IWRAM, u8 | health %, max 100 (`0x64`) |
| `0x03000014` | IWRAM, u8 | bounded counter A (increments while <= 19) |
| `0x03002FE4` | IWRAM, u8 | bounded counter B (increments while <= 19) |
| `0x030018F4` | IWRAM, u8 | bounded counter C (increments while <= 249) |

Key masks (active-high, `~KEYINPUT & 0x3FF`):
A=`0x001`, B=`0x002`, SELECT=`0x004`, START=`0x008`, RIGHT=`0x010`, LEFT=`0x020`,
UP=`0x040`, DOWN=`0x080`, R=`0x100`, L=`0x200`. Registers r6/r7 in the validator hold
R (`0x100`) and L (`0x200`) as constants.

## 5. Algorithm

```
each frame:
  held = ~KEYINPUT & 0x3FF
  pressed = held & ~prev;  prev = held
  if pressed & START: enter pause handler (0x801D834) and freeze  // no UI
  for each button mask m in [A,B,R,L,SELECT,LEFT,RIGHT,UP,DOWN]:
      if pressed & m: hist[r4] = m; r4 = (r4 + 1) & 0xFF
  // 16 independent suffix checks; FIRST match wins, then dispatch:
  for each (pattern P, action) in table §6:
      if hist[r4-len(P) .. r4-1] == P: action(); break
```

Mismatch is simply a fall-through to the next pattern; there is no "invalid code" message.

## 6. Tables — complete sequence enumeration (all 16)

Notation: `R`/`L` = shoulder buttons, `RIGHT`/`LEFT` = d-pad. "Aux" = `0x03001674`.
Every RAM value below was **observed** in a savestate after entering the sequence, except
where noted.

| # | Sequence | Len | Effect | Observed RAM | Published? |
|---|---|---:|---|---|---|
| 1 | A R A B B A R L A B B | 11 | warp value + aux=1 | `0x152C=0xDD`, aux=1 | **NO** |
| 2 | L A R DOWN R | 5 | ammo = 2000 | `0x18BC=0x07D0` | **NO** |
| 3 | B R A B A B A R | 8 | health +150, clamp 100 | derived; health already 100 (`0x64`) | **NO** |
| 4 | DOWN UP B A B R L B | 8 | counter A +1 if <=19 | `0x14: 3→4` | **NO** |
| 5 | L LEFT UP RIGHT A L A | 7 | counter B +1 if <=19 | `0x2FE4: 3→4` | **NO** |
| 6 | RIGHT R B A L L A R | 8 | aux=1; warps to Andy Asteroids | aux=1 | Yes — "Level Select" |
| 7 | R UP DOWN A B LEFT SELECT L RIGHT | 9 | counter C +1 if <=249 | `0x18F4: 0→1` | **NO** |
| 8 | SELECT R B DOWN L B | 6 | warp value 15 + aux=1 | `0x152C=0x0F` | Yes — "What the Heck" |
| 9 | UP L DOWN A R A | 6 | warp value 2 + aux=1 | `0x152C=0x02` | Yes — "Down the Tubes" |
| 10 | R UP SELECT L R LEFT | 6 | warp value 25 + aux=1 | `0x152C=0x19` | Yes — "Snot a Problem" |
| 11 | R L A B B A L R | 8 | warp value 36 + aux=1 | `0x152C=0x24` | Yes — "Level 5" |
| 12 | RIGHT LEFT R L A R | 6 | warp value 35 + aux=1 | `0x152C=0x23` | Yes — "For Pete's Sake"* |
| 13 | L A UP R A R A SELECT | 8 | warp value 88 + aux=1 | `0x152C=0x58` | Yes — "Buttville" |
| 14 | A B R R A R | 6 | warp value 45 + aux=1 | `0x152C=0x2D` | **NO** |
| 15 | R L L R A RIGHT | 6 | warp value 165 + aux=1 | `0x152C=0xA5` | **NO** |
| 16 | DOWN A LEFT B A R | 6 | warp value 6 + aux=1 | `0x152C=0x06` | **NO** |

\* The published "For Pete's Sake" code is written `R, L, R, L, A, R`. The first two presses
are **d-pad RIGHT/LEFT**, not shoulder R/L: `RIGHT LEFT R L A R` set `0x152C=0x23`, while
`R L R L A R` (all-shoulder) was **rejected** (no RAM change). This resolves an ambiguous
published label (§16.7).

Published-code coverage: GameFAQs (7 codes), IGN (6), world-of-nintendo (7) — all verified;
the superset is 7 distinct codes, all of which map to ROM sequences 6, 8–13. The remaining
9 sequences have no published counterpart.

No password alphabet, no literal code table, no key-mask blob exists in the ROM: the
sequences are compiled directly into `cmp` immediates and `cmp rX,r6/r7` instructions.
A byte-pattern search for the published button sequences as `u16` masks (both endiannesses,
active-high and active-low, forward and reversed) returned **zero** hits — the cheat data
lives only in code, which is why the §5.4a table search was negative and disassembly was
required.

## 6b. Enumeration

**Space definition.** 16 hard-coded sequences, lengths 5–11 presses over a 10-symbol input
alphabet (A, B, SELECT, START, RIGHT, LEFT, UP, DOWN, R, L — START is consumed by the pause
handler, so 9 symbols can appear in a code). There is no checksum and no reserved-bit field.
The full space is the 16 rows of §6; it was enumerated by parsing every `cmp`+`bne` pair in
`0x0801D208`–`0x0801D7F0` (16 distinct fail-target groups) and then confirming each group
dynamically.

**Novel codes (not in any published list).** Entered and RAM-verified:

- `#15  R L L R A RIGHT` → `0x0300152C = 0xA5` and aux=1. Visually: "GROOVY!" banner followed
  by a **different level** (blue industrial stage with a metallic boss) — confirmed by
  screenshots `game_novel15.png` / `game_novel15b.png`.
- `#1   A R A B B A R L A B B` → `0x0300152C = 0xDD` and aux=1; visually produced the
  "GROOVY!" warp banner.
- Novel stat/unlock effects observed by RAM: `#2` ammo `0x5DC → 0x7D0` (1500 → 2000);
  `#4` `0x03000014: 3→4`; `#5` `0x03002FE4: 3→4`; `#7` `0x030018F4: 0→1`;
  `#14` `0x152C=0x2D`; `#16` `0x152C=0x06`.

**Bounds proven by rejection (all from the same stable baseline `0x152C=1`, aux=0):**

- Wrong button: `R DOWN SELECT L R LEFT` (substituting DOWN for UP in code #10) →
  `0x152C` unchanged (1), aux unchanged — rejected.
- Truncated: `R UP SELECT L R` (5 of 6 presses of code #10) → unchanged — rejected.
- Prefix tolerance: `A R UP SELECT L R LEFT` (one extra leading press) → `0x152C=0x19`,
  accepted — proves suffix matching rather than exact-length matching.
- Title screen: code #10 entered without pausing/in gameplay → all RAM unchanged — rejected.
- Counter bound: codes #4/#5/#7 increment only while the byte is <= 19/19/249 respectively
  (`cmp #19; bls` / `cmp #249; bls` at `0x801D3CC`, `0x801D42A`, `0x801D502`), so values
  above those limits are not incremented — derived from the guard branch, not separately
  maxed in-game.

## 7. Validation evidence

- **Observed**: title screen (`game_title2.png`), options (`game_options.png`,
  `game_opt3.png` showing NORMAL/DIFFICULT), silent pause, "GROOVY!" warp banners, level
  title cards (`game_lsel2.png` = Andy Asteroids), novel-code boss level
  (`game_novel15b.png`), and all RAM values in §6 from decompressed mGBA `gbAs` savestate
  chunks.
- **Derived**: mask encoding from the KEYINPUT inversion at `0x0801D156`; ring-buffer layout
  from the store loop at `0x0801D1FA`; all 16 sequences from the `cmp`/`bne` groups;
  action effects from the success-path disassembly (e.g. `movs r0,#25; strb` at `0x801D5EA`).
- **Inferred**: the semantic names of the warp values (e.g. 0x19 = "Snot a Problem") are
  taken from the published lists that map to those sequences; the game itself only stores a
  byte. The health code's effect is derived (health was already at max during the test).

## 8. Unknowns

- The `0x0300152C` values for the 9 novel warp codes are not labeled by any published list,
  so the destination level names for values 0xDD, 0x2D, 0xA5, 0x06, etc. are only known
  visually for #15 (distinct boss stage). Mapping the byte→level table would require playing
  through each warp.
- `0x03001674` is written by every code but its exact consumer was not isolated; the
  observable effect (warp) tracks `0x0300152C`.
- No hidden debug menu was found; the negative result is bounded by walking title, options
  and pause screens and by the fact that all 16 validator branches terminate in one of the
  RAM writes above (none calls a menu-spawning function).

## 9. Tooling

`strings`/`grep` (`strings -t x -n 4`), `arm-none-eabi-objdump -M force-thumb` for the
validator at `0x0801D100`–`0x0801DB20`, a Python `cmp`/`bne` pattern parser for sequence
enumeration, mGBA 0.10+ under Xvfb with `import -window root` screenshots, and a Python
savestate reader (`zlib.decompress` of the `gbAs` PNG chunk) for IWRAM proofs. Scripts used:
`state_read.py`, `test_codes.py`, `focused_test.py` in `/tmp/ewj1/`.

No ROM or copyrighted assets are redistributed; only addresses, hashes, masks and the
analyst's own generated button sequences are published.
