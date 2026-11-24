# Super Street Fighter II Turbo Revival (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Super Street Fighter II Turbo Revival/Super Street Fighter II Turbo Revival.gba` |
| Size | 8,388,608 bytes (0x00800000) |
| Header title | `SSF2TREVIVAL` |
| Game code | `AXRE` |
| Maker code | `08` (Capcom) |
| Version | `0x00`; fixed byte `0x96` present; complement `0x2E`; header checksum `0x0000` |
| Entry word | `0xEA00002E` → `0x080000C0` (stock crt0, no cracktro/trainer prefix) |
| MD5 | `7a36a7486ef2c534111ee417b8acf9b7` |
| SHA-1 | `00b0508e2774d0bbcb8f0994766cb362e62d7537` |
| SHA-256 | `99715f1704dfa5d1b08c8bf7766abdda0ff00c4f530e9baa12ff146aae4807a5` |

All addresses below are for this exact build (`AXRE`, Rev.00). File offset = ROM address − `0x08000000`.

## 2. Executive summary

This ROM has **no developer-intended password/code entry surface** that could be located or confirmed. The entire 8 MiB image was searched for the two published GBA button sequences (the "Konami" easy-special code and the Capcom-logo Survival code) in six encodings, in forward and reverse order; there are **zero full-sequence hits** (§6b). The only button-mask sequences that do exist in the image are Capcom's **special-move command tables** at `0x0844C89C` and `0x084532C0`, which contain direction masks only (`0x10/0x20/0x40/0x80`) and are referenced by 27 and 15 pointer-table entries respectively — these are move inputs, not cheats.

What *is* present and confirmed:

* A live 8-slot keyboard history at EWRAM `0x02005E70` (observed with GDB: holding R+Up+Start produced `0x0148` in slots 0–5; `KEYINPUT` read `0x02B7`). The input handler at ROM `0x080004B0` computes active-high `~KEYINPUT & 0x3FF`, derives pressed/released masks, and shifts the history.
* VS-point state at EWRAM `0x020071C8` (observed as `0x00000000` on a fresh save); the image contains a numeric literal table at `0x0845AB80` holding `0x1388` (5,000), `0x1F40` (8,000) and `0x2710` (10,000), matching the published unlock thresholds.
* Nine selectable character colours at the character-select screen, chosen by the button used to confirm the character (published behaviour; the selection screen was walked and the colour-changing confirm was exercised, but individual colours were not exhaustively pixel-verified — see §8).

Published web codes were treated strictly as data. They were *not* confirmed in the emulator; every one remains unverified for this build.

## 3. How to reproduce

**Toolchain:** mGBA 0.10.5 (`/usr/local/bin/mgba`), Xvfb `:319` + openbox, `SDL_AUDIODRIVER=dummy`, gdb-multiarch, `xdotool`, `scrot`, ImageMagick, arm-none-eabi-objdump, Python 3 + Capstone 5.0.7. No packages were installed during this run.

```
Xvfb :319 -screen 0 1024x768x24 &
DISPLAY=:319 openbox &
DISPLAY=:319 SDL_AUDIODRIVER=dummy mgba -g -3 <rom> &
```

mGBA SDL keymap used: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad = arrow keys. **Important:** `xdotool windowactivate --sync <mGBA window>` is required before each input batch; without it XTEST events were silently dropped. Hold 60–120 ms; longer holds double-step the title/menu cursors.

Screen walk (screenshots saved in `/tmp/ssf2turbo/`):

1. `bootseq1.png` — Nintendo licence screen ("SUPER STREETFIGHTER2 TURBO REVIVAL / LICENSED BY NINTENDO").
2. `bootseq6.png` — CAPCOM logo. The published Survival code (`Up Down Left Right Left Down Up B A Start`) was entered here with 45 ms holds (`capcom_after.png`); no visible acknowledgement.
3. `menu11.png` / `capcom_after.png` — "PRESS START" attract/title carousel. Two Start presses are needed to reach the menu: one exits attract mode, one acts on the title prompt.
4. `menu15.png` / `mm_final.png` — **MODE MENU**: exactly four entries, `ARCADE`, `TRAINING`, `OPTION`, `V.S.`, and a `VS. POINT` counter.
5. `option1.png` — character select (reached from ARCADE): 16 portraits, 1P cursor; `csgrid2.png` and `r2grid.png` enumerate both rows.
6. `at_ryu.png` / `fight1.png` — game-speed screen: `NORMAL`, `TURBO 1`, `TURBO 2`, `TURBO 3`.
7. `pause2.png` — VS screen ("NEXT", country/character banners).
8. `fight3.png` / `konami_fight.png` — live fight with HUD. The published "Konami" easy-special code was entered during a live fight with 45 ms holds; no visible acknowledgement (`konami_fight.png`).
9. `akuma_try.png` — character-select dwell sequence (Ryu/T.Hawk/Guile/Cammy/Ryu, ~3.3 s each) plus `Start+A+B+L`; produced the speed-select screen, not an Akuma silhouette. The dwell sequence was not completed on the exact intended portraits (off-by-one navigation, see §8).

Savestate workflow: `Shift+F1`/`Shift+F2` write `.ss1`/`.ss2` beside the ROM; `state.py` decompresses the PNG `gbAs` chunk (IWRAM at raw `0x19000`, EWRAM at `0x21000`) for RAM diffs. GDB stub was usable for single snapshots (attach → `x`/`dump` → `continue`); it closed after prolonged gameplay, so savestate diffs were the fallback.

## 4. Address map

| Address | Kind | Evidence | Note |
|---|---|---|---|
| `0x08000000` | ROM | Derived | Entry branch `0xEA00002E` |
| `0x080004B0`–`0x08000560` | Thumb code | Derived (objdump `-M force-thumb`) | Global input handler |
| `0x04000130` | I/O | Derived/Observed | `KEYINPUT`, active-low; handler XORs with `0x3FF` |
| `0x02005E70` | EWRAM | Observed (GDB `find`) | 8 halfwords: held, pressed, released, then 5 older held values |
| `0x02005E7E` | EWRAM | Observed | Second copy of current held mask |
| `0x0844C89C`–`0x0844C90A` | ROM table | Derived | 56 direction-mask halfwords; special-move commands |
| `0x084532C0`–`0x084532F0` | ROM table | Derived | 24 direction-mask halfwords; special-move commands |
| `0x0802EC00`–`0x08030800` | ROM pointer table | Derived | 27 pointers into the `0x0844C8xx` command block |
| `0x08047C00`–`0x0804A200` | ROM pointer table | Derived | 15 pointers into the `0x084532xx` command block |
| `0x020071C8` | EWRAM | Observed | VS-point counter, `0x00000000` on fresh data |
| `0x0845AB70`–`0x0845ABA0` | ROM literal table | Derived | `100,200,500,1000,2000,6000,8000,10000,20000,30000,100000,1000000` |
| `0x0845AB80` | ROM literal | Derived | `0x1388` = 5,000 (published Akuma threshold) |
| `0x0845AB88` | ROM literal | Derived | `0x1F40` = 8,000 (published art-gallery threshold) |
| `0x0845AB8C` | ROM literal | Derived | `0x2710` = 10,000 (near published Shin-Akuma 9,999) |

## 5. Algorithm

Input handler (ROM `0x080004BC`, derived from Thumb disassembly):

```
old = history[0]
held = ~KEYINPUT & 0x3FF
history[0] = held
history[2] = held & ~old          # pressed edge
history[4] = old & ~held          # released edge
for i = 6,8,10,12,14: history[i] = history[i-6]   # 8-deep held history
```

Button mask convention confirmed live: `A=0x001, B=0x002, Select=0x004, Start=0x008,
Right=0x010, Left=0x020, Up=0x040, Down=0x080, R=0x100, L=0x200`.

No password/checksum validator was found, so there is no algorithm to reimplement. The only
comparison machinery located is the special-move command matcher, whose tables store
plain direction masks (`0x10/0x20/0x40/0x80/0x90/0xA0/0x50/0x60`).

## 6. Tables

**Character-select confirm → colour** (published; screen exercised, colours not individually
pixel-verified): `A` default, `L` alternate, `R` Turbo, `B` SSF2 Short, `Select+A` SSF2
Forward, `Select+L` Roundhouse, `Select+R` SSF2 Start, `Select+B` secret, `Start` Super-Turbo
Jab; holding another attack button for a few seconds selects the eighth colour.

**Observed command-table prefixes** (file offset → ROM address `0x08000000 + offset`):

* `0x44C89C`: `40 80 40 80 10 20 10 20 20 20 10 10 80 80 40 40 80 40 80 40 20 10 20 10 10 10 20 20 …`
* `0x4532C0`: same 24-word prefix.

Both are conventional fighting-game motion inputs, not cheat codes.

**Unlock thresholds** (published, literals present in ROM but their consumer not isolated):
VS points 5,000 → Akuma; 8,000 → art gallery; 9,999 → Shin Akuma; clearing on highest
difficulty → gallery; highest difficulty no-continue → character gallery (R on main menu).

## 6b. Enumeration

**Space definition.** There is no password/code alphabet, length, checksum or lookup table in
this image. The only enumerable *code-like* space found is the direction-mask command space of
the two move tables:

| Table | ROM range | Mask halfwords | Distinct pointer references |
|---|---|---:|---:|
| A | `0x0844C89C`–`0x0844C90A` | 56 | 27 |
| B | `0x084532C0`–`0x084532F0` | 24 | 15 |

Representable direction masks used there: `{0x10,0x20,0x40,0x80,0x50,0x60,0x90,0xA0}` —
8 symbols. At 8 observer slots the raw history space is `0x3FF^8 ≈ 1.1×10^24`; the command
matcher constrains it to the two finite tables above (80 mask entries total, 27+15 = 42
distinct pointer references). No entry in either table contains `A`, `B`, `Select`, `Start`,
`L` or `R`, so neither table can express a published code.

**Search counts (bounded negative).** The whole 8,388,608-byte image was scanned for both
published sequences:

| Sequence | Masks |
|---|---|
| Konami (easy specials) | `40 40 80 80 20 10 20 10 02 01` |
| Capcom-logo (Survival) | `40 80 20 10 20 80 40 02 01 08` |

Encodings tried for each: `u8`, `u16LE`, `u32LE`, active-low complements (`~mask & 0x3FF`),
button-bit indices (`A=0,B=1,Select=2,Start=3,Right=4,Left=5,Up=6,Down=7`), and each in
forward and reversed order — 2 sequences × 6 encodings × 2 directions = **24 full-sequence
 searches, 0 hits in 8,388,608 bytes**. Four-element prefix searches produced these hits:
Konami forward as bytes at `0x0300258` (1) and as halfwords at `0x044C8D4` (1, inside command
table A); Konami reverse as bytes at `0x016910A` (1); Capcom forward as bytes at 17 offsets
and reverse at 6 offsets — all isolated compressed-data coincidences (no 32-bit pointer,
no literal-pool access, no validator context). No full-length sequence exists anywhere.

A Capstone pass over every literal-pointer load of the input struct (`0x02005E70`, 158
instruction sites) found **no function** whose ordered immediate comparisons reproduce either
published sequence (subsequence test with span ≤ 30 comparisons: 0 hits). This is why the
negative is "no in-image press-sequence validator located", not "I did not look".

**Novel codes.** None could be minted: without a validator or a table there is no generator to
invert and nothing to accept a new value. Per §0.2 this is reported as a bounded negative, not
as a positive result.

**Rejection bounds.** The two published codes were *entered* in the emulator (Capcom logo:
`capcom_after.png`; live fight: `konami_fight.png`). Neither produced an on-screen
acknowledgement or a persistent, isolated RAM change: savestate diffs before/after each
attempt were dominated by animation (IWRAM 1,616 changed bytes; EWRAM 3,525 changed bytes)
and no single stable flag could be attributed to the input. This bounds the claim to
"no visible acceptance under the tested timing"; it does not prove the codes are absent from
every revision or that a faster/held-input variant could not work.

**Screen enumeration.** Every reachable screen was walked: licence → Capcom logo → attract →
PRESS START → MODE MENU (4 entries, all visited) → ARCADE → character select (16 portraits,
both rows captured) → speed select (4 entries) → VS → live fight → TRAINING/OPTION/V.S. menu
entries present. No password entry field, debug menu, hidden mode slot, or code prompt was
observed on any of them.

## 7. Validation evidence

* **Observed** — GDB reads of `KEYINPUT = 0x02B7` and history slots `0x0148` at
  `0x02005E70`–`0x02005E7C`; VS points `0x00000000` at `0x020071C8`; all screenshots listed
  in §3; savestate diffs giving the changed-byte counts in §6b.
* **Derived** — Thumb disassembly of `0x080004B0` (history update), literal scans and pointer
  counts for both command tables, header parse, hash computation.
* **Inferred** — that the `0x0845AB80` threshold literals are the VS-point unlock thresholds;
  the consumer was not isolated. Published colour-select mapping is from the web only.
* **Unverified** — every published code (Konami easy specials, Capcom-logo Survival,
  dwell-to-Akuma, 5,000/8,000/9,999-point unlocks). No fetched page was treated as an
  instruction; all ROM/page text was handled as data.

## 8. Unknowns

* Whether a faster or held-button variant of the published Konami/Capcom codes exists: the
  tests used 45–60 ms per press, which may miss an edge-triggered matcher; the dwell-sequence
  test ended one portrait off its intended target (Ken instead of Ryu), so the Akuma dwell
  code was not cleanly exercised.
* Which code consumes VS points at `0x020071C8` and writes the unlock flags. The literal
  thresholds are present, but the reader was not isolated; the save-bit unlocks were therefore
  not reversed (§16.18 of the guide applies: these are not button codes).
* Whether the game's tile-based text bank contains an unreferenced code/debug label. ASCII
  `strings -n 4` yields 90,452 lines but **zero** matches for `password|cheat|debug|easy|
  survival|gallery|gouki|akuma`; the visible UI is tile-rendered, so that string count is not
  by itself proof of absence (the screen walk in §6b is the binding evidence).
* No second algorithmic password format was found beside the move-command tables (the guide's
  usual "compare the input alphabet with the stored strings" test has no code-surface alphabet
  to compare here).

## 9. Tooling

Scripts and captures kept in `/tmp/ssf2turbo/`:

* `k.py` — xdotool key/screenshot helper (DISPLAY `:319`).
* `state.py` — mGBA `.ss1` PNG `gbAs` decompressor and RAM dump helper.
* `cs_state.ss1` — savestate at character select; `bootseq*.png`, `mm_final.png`, `csgrid2.png`,
  `r2grid.png`, `fight3.png`, `konami_fight.png`, `akuma_try.png` — key screenshots.
* `b_ewram.bin`/`a_ewram.bin`, `b_iwram.bin`/`a_iwram.bin` — GDB RAM dumps used for the diffs.

Commands: `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`;
Capstone Thumb scans for literal loads and immediate-comparison subsequences; `strings -t x`,
`grep -abo`, `xxd`, standard hash tools.

## 10. Legal note

No ROM bytes, graphics, audio or extracted assets are redistributed here. Only hashes,
addresses, observed RAM values and original screenshots of the running game are recorded.

## 11. Cleanup

All processes started for this run were stopped by their recorded PIDs (Xvfb, openbox, mGBA,
GDB, FIFO holders); no `pkill -f` was used. Generated `.sav` and `.ss*` files were removed
from the ROM folder.
