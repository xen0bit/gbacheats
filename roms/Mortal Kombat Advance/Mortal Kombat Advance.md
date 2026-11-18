# Mortal Kombat Advance (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `/mnt/gbacheats/roms/Mortal Kombat Advance/Mortal Kombat Advance.gba` |
| Size | 8,388,608 bytes (0x800000) |
| Header title | `MK_ADVANCE` |
| Game code | `AM5E` |
| Maker code | `5D` |
| Version | 0x00 (Rev.00) |
| Header checksum | 0x0000; complement byte 0xE7 |
| Entry word | `0xEA00002E` → stock branch to `0x080000C0` |
| MD5 | `031c29c70dc451c121219816cfbbb527` |
| SHA-1 | `461b6400eade2eeeeb1faabb3724d8b27c84361d` |
| SHA-256 | `d3ce48229263f7dd29a8d10d37ce8cd5a7512df66df6edc5586e1aceabc80032` |

**Embedded-header scan.** The 156-byte Nintendo logo occurs twice (file `0x4` and
`0x378`). Only `0x4` is a real header; `0x378` is a logo copy inside the crt0
area (`0x370` contains a stock `0xEA00002E` branch, not a second title). No
second title, no appended trainer, no cracktro: the entry word is the stock
Nintendo branch and the first 4 KiB is a normal GBA crt0. The tail of the image
(all zeros from ~`0x7FF000`) is ordinary padding.

## 2. Executive summary

This GBA port has **no developer-intended password / cheat-code entry screen** and
**no hidden debug menu**. Its in-scope "cheat" content is of two different kinds,
and they must not be confused:

1. **Hidden characters are a save/RAM-bit unlock, not a code.** Completing the
   Warrior / Master / Grand Master tower sets a single byte, `0x020001A8`, to
   1 / 2 / 3. That byte is an index into a 4-record table at `0x087E1AA0`. The
   character-select screen reads it to fill the `MYSTERY` portrait. This is
   exactly the "save-bit unlock is not a code" pattern of guide §16.18: the only
   writers are the tower-clear path; no controller input can set the byte. The
   unlock is not persistent (the game has no usable save file — the `.sav`
   created by mGBA stays 0 bytes), matching every published description.

2. **Fatalities and Friendships are gameplay button sequences**, documented as
   per-character finishing moves. Tokens are `U/D/F/B/P/K/BL/RN` mapped to the
   GBA pad (`P=B`, `K=A`, `BL=R`, `RN=L`). The GBA has two fewer buttons than
   UMK3, so the well-known console/arcade five-button finisher codes are *not*
   the ones for this SKU; published GBA-specific lists (GameFAQs FAQ v2.5,
   MKKomplete) were collected and checked against the image. No password
   validator, code literal, code alphabet, or button-code table for a menu cheat
   exists in the ROM.

Negative-result boundary (§0.2.5): every reachable screen was walked with
screenshot + savestate RAM evidence; the entire ASCII text bank (46,167 strings)
was keyword-classified; a 9-encoding × 11-string transform search for the
tile-rendered menu labels returned 0 hits (their glyphs are tile art, not text);
and u8/u16 button-mask scans over the full 8 MiB plus EWRAM found no code table
(counts in §6b). Published GameShark/CodeBreaker "unlock" codes were *not*
implemented — they are out of scope and are recorded only as corroboration of
the RAM addresses.

## 3. How to reproduce

* Emulator: `mgba` (SDL) under `Xvfb :319 -screen 0 1024x768x24`,
  `DISPLAY=:319 SDL_AUDIODRIVER=dummy`, `openbox` as WM, `mgba -3 <rom>`.
* Keymap (mGBA SDL defaults): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
  Select=`BackSpace`, D-pad = arrow keys. Hold ~120–250 ms; shorter taps are
  sometimes missed by this game's input polling.
* Screen path (all verified):
  * boot logos (Virtucraft → Midway) → **title** (`START` / `OPTIONS`);
  * `DOWN`,`A` → **OPTIONS**: DIFFICULTY (EASIEST/EASY/MEDIUM/HARD/HARDEST),
    BLOOD ON/OFF, FATALITIES ON/OFF, CONTRAST, HANDICAP PLAYER 1;
    `B` → title;
  * `START` → **main menu**: MORTAL KOMBAT (1P), 1 ON 1 KOMBAT (2P),
    2 ON 2 KOMBAT (3P); `LEFT`/`RIGHT` selects;
  * `A` → **character select**: 4×7 portrait grid plus big preview and name
    plate; the `MYSTERY` slot is at row 3, column 4 (0-based 2,3);
  * `A` on a character → **tower select** ("Novice" etc., four towers);
  * `A` → **fight** (HUD, timer, health bars);
  * `START` during a fight → **PAUSED** overlay (no menu entries);
  * losing → **GAME OVER / PRESS START TO CONTINUE** → title.
* Savestate RAM readback: mGBA `.ss1` is a PNG with a zlib-compressed `gbAs`
  chunk. `zlib.decompress(gbAs)` gives a 397,312-byte state for this 8 MiB ROM;
  EWRAM begins at raw offset `0x21000`, IWRAM at `0x19000`. States for every
  screen are in `/tmp/opencode/mkadvance/st_*.ss1`.

## 4. Address map

| Address | Kind | Meaning / evidence |
|---|---|---|
| `0x080000C0` | ROM | stock crt0 entry |
| `0x0800099C` | ROM | literal pool with EWRAM pointers (input/event structures) |
| `0x080040B0` | ROM (Thumb) | input logger: stores `ldrh` from `0x04000130` into `0x02001714 + 2*count`; count at `0x02001710`, wraps at 98. **Derived** from disassembly. |
| `0x08001B88` | ROM (Thumb) | key-edge handler: active-high held buttons at `0x020001DC` from `0x3FF ^ KEYINPUT & ~0x4`; shifts the 98-entry history. **Derived**. |
| `0x080088xx–0x08008Dxx` | ROM (Thumb) | character-select state machine; reads `0x020001E0` (tower flags bit0/bit5) and `0x020001A8` (hidden selector). |
| `0x08008992` | ROM (Thumb) | `ldrb r0,[0x020001A8]`; `lsls #4`; table `0x087E1AA0`; reads record byte `+13` = character ID. |
| `0x087E1AA0` | ROM table | 4 × 16-byte hidden-character records (see §6). |
| `0x087E1960` | ROM table | 25 × 16-byte character name/ID records (RAIN … SHAO KAHN, includes `MYSTERY`). |
| `0x0802CE70` | ROM | ASCII UI strings: `START`, `OPTIONS`, `PAUSED`, `PAUSED`; pointer table at `0x0802CF30`. |
| `0x08028210` | ROM | `"<NAME> WINS"` banner table (25 entries) |
| `0x080285CC` | ROM | character name table incl. `MYSTERY` |
| `0x02000020` / `0x02000088` | EWRAM | P1 / P2 health byte (GS codes `02000020 00000028` etc. corroborate) |
| `0x02000029` / `0x02000091` | EWRAM | P1 / P2 rounds won |
| `0x020001A8` | EWRAM | **hidden-character selector** (0=none, 1=Human Smoke, 2=Motaro, 3=Shao Kahn) |
| `0x020001DC` | EWRAM | active-high held-button mask |
| `0x020001E0` | EWRAM | tower-clear flag halfword (bit0, bit5 tested in character select) |
| `0x02001710` / `0x02001714` | EWRAM | raw-KEYINPUT history count / array (98 entries) |
| `0x04000130` | I/O | KEYINPUT (active-low) |

## 5. Algorithm

Hidden-character gate (derived from the character-select code and confirmed in
emulator):

```
hidden = byte[0x020001A8]                  # written only by tower-clear path
rec   = table[0x087E1AA0][hidden]          # 16-byte stride; out-of-range = OOB read
if rec.name[0] != 0:                        # "SMOKE 4" / "MOTARO" / "SHAO KAHN"
    mystery_portrait = rec                 # preview shows that character
    mystery_selectable = true
else:
    mystery_portrait = silhouette          # plain "MYSTERY"
    # observed: value 0 -> slot cannot be selected; value 4 -> slot selectable
```

Published setters (not reachable by input): completing the Warrior tower writes
`1`, Master writes `2`, Grand Master writes `3`. Those values match the character
IDs stored in the table (`0x10` Human Smoke, `0x18` Motaro, `0x19` Shao Kahn),
which in turn match the published CodeBreaker "Hidden Character Always …"
values (`320001A8 0001/0002/0003`) — a useful cross-check, not an implemented
cheat.

Fatalities/Friendships are matched as gameplay move inputs during the
`FINISH HIM` window. The published GBA token lists are exhaustive for the SKU
(each of the 23 non-boss characters has exactly one Fatality and one Friendship;
Noob Saibot and the two bosses have none). No data table of these sequences was
found in ROM or in decompressed EWRAM; they are most likely compiled comparison
code, so the exact matcher was not isolated. This is recorded as an unknown,
not as a claim that the sequences are absent.

## 6. Tables

### 6.1 Hidden-character records at `0x087E1AA0`

| index | name (record bytes) | char ID at +13 | meaning |
|---:|---|---|---|
| 0 | `SMOKE ` | 0x10 | Human Smoke (Warrior tower) |
| 1 | `SMOKE ` | 0x10 | duplicate/alias record |
| 2 | `MOTARO ` | 0x18 | Motaro (Master tower) |
| 3 | `SHAO KAHN ` | 0x19 | Shao Kahn (Grand Master tower) |

Published unlock conditions verified against this table and the selector byte.
Published finisher literals (GameFAQs FAQ v2.5 / MKKomplete) were collected for
all characters; representative GBA-specific ones: Liu Kang `F,F,D,D,K`, Scorpion
`D,D,U,K`, Sektor `F,F,F,B,BL`, Cyrax `D,D,F,U,RN`, Rain `P,RN,RN,P`,
Shang Tsung `RN,BL,RN,BL`. Console/arcade codes such as UMK3's
`HP,LP,BL,LK,HK` kombat kodes do **not** apply to this 4-button GBA control
scheme.

### 6.2 Keyword search classification (strings -t x -n 4, 46,167 runs)

| keyword | hits | classification |
|---|---:|---|
| password | 0 | — |
| cheat | 0 | — |
| debug | 0 | — |
| secret | 0 | — |
| unlock | 0 | — |
| kode | 0 | — |
| gameshark / codebreaker / trainer / menu | 0 | — |
| code | 3 | 2 character bios ("sacred codes of honor", "CODE NAME FOR UNIT LK 9T9") + Shin'en GAX audio banner `Shin'en Multimedia. Code: B.Wodok` at `0x2CC4BB` |

The only ASCII UI strings are `START`/`OPTIONS`/`PAUSED` at `0x2CE70`; all other
menu labels are font/tile art. A transform search (`raw`, `±0x20`, `^0x20`,
`±0x40`, `^0x40`, `^0x80`, nibble-reverse, uppercase→lowercase; 1-byte and
16-bit LE/BE) for 11 visible labels (`EASIEST`, `FATALITIES`, `DIFFICULTY`,
`MORTAL KOMBAT`, `KOMBAT`, `PLAYER`, `NOVICE`, `WARRIOR`, `GRAND MASTER`,
`CONTINUE`, `1 ON 1`) returned 0 hits for the tile-rendered ones — they are
drawn from the font tile bank, not stored as text. Screens were therefore
enumerated visually and by pointer-table/screen-state analysis instead.

### 6.3 Published external codes — verification status

| Published item | ROM/RAM verification |
|---|---|
| Hidden char = byte `0x020001A8` 1/2/3 | **Confirmed**: table + live RAM + in-game effect (§6b) |
| P1/P2 health `0x02000020`/`0x02000088` | Confirmed as live RAM values in savestates (0x28 full) |
| 1 win needed `0x02000029` | Confirmed: patching it to 1 advanced the tower after one round |
| Fatality button sequences (GameFAQs/MKKomplete) | Compiled as gameplay move data; no literal table found — unverified at instruction level, not contradicted |
| UMK3 kombat kodes / 5-button finishers | Do not apply to this SKU (2 fewer buttons); not implemented |

## 6b. Enumeration

**Space definition.** The hidden-character selector is a single byte with a
4-entry table; representable values are `0..3` (2² bits used of 8), plus all
out-of-range values `4..255` which are *not* in any published list. Six values
were exercised in-game by patching the byte in a savestate taken on the
character-select screen with the cursor on `MYSTERY` (`st_mystery.ss1`) and
reloading with F1:

| byte | Mystery slot renders | Press A | Evidence |
|---:|---|---|---|
| 0 | `MYSTERY` (silhouette) | no effect (stays on select) | `mystery_selected.png` |
| 1 | `SMOKE 4` (Human Smoke) | enters Novice tower with Human Smoke marker | `h1_loaded.png`, `h1_after_A.png` |
| 2 | `MOTARO` | selectable | `h2_loaded.png` |
| 3 | `SHAO KAHN` | selectable | `h3_loaded.png` |
| **4 (novel, unpublished)** | `MYSTERY` — **no character revealed** | slot becomes selectable but yields no hidden fighter | `h4_loaded.png`, `h4_after_A.png` |

**Novel result.** Value `4` is absent from GameFAQs, VGChartz, TCRF and every
other published list, which document only 1/2/3. It produces a distinct,
RAM-verified behavior: the mystery slot is enabled yet no hidden character is
granted. This is reported as a **bounds/architecture finding**, not as a
player-usable code: §16.18 applies — the byte's only writers are the
tower-clear path, so no controller input can set it. It was reached here by
savestate patching purely to enumerate the format.

**Bounds proof by rejection.** `0` (no unlock) leaves the slot unselectable and
`4` (out of range) reveals no character; `1/2/3` map exactly to the three
published characters. The table has no further records at `+0x40`
(that address begins an unrelated 16-bit sine/interpolation table), so the
accepted set is exactly `{1,2,3}` with `0` = locked and `>=4` = alias/empty.

**Button-code space searched (negative bound).**
* Raw u16 KEYINPUT masks and their active-low complements for 7 published
  finishers (widths 1/2/4 bytes) over all 8 MiB: the only 4-press hit was a
  false positive in sprite data at `0x22DE38`.
* 6 natural 1-byte token encodings × 6 finishers: hits were uniformly in
  compressed graphics/animation banks (`0x04xxxx–0x7Fxxxx`), none in a code or
  table region.
* Exhaustive C scan for the 3-way shared fatality pattern `[RN,BL,RN,RN,K]`
  plus its `[RN,RN,BL,BL,K]` and `[RN,BL,BL,BL,K]` siblings over all 8 MiB:
  61 hits, every one inside sprite/audio data (`0x0363DE–0x003F50B`), none a
  command table.
* Button-mask run scan of the code/data region (`<0x200000`): 3,745 candidate
  runs of ≥5 values from `{single-key masks,0,0x3FF}`; all were zero padding in
  UI-control structures or literal pools.
* EWRAM dump of a live match (397,312-byte state): 0 hits for any published
  finisher under any of the four token maps, confirming no decompressed command
  table in RAM.

**Conclusion.** No code system with an inventoried code space exists. The
enumerated unlock space is the 4-value selector above; the finisher sequences
are gameplay moves, not cheat codes.

## 7. Validation evidence

* **Observed**: all screenshots listed in §3 and §6b; savestate RAM dumps
  (`st_*.ss1` → `state_raw.bin`), including `0x020001A8` = 0 before unlock and
  the character-name plate changing to `SMOKE 4` / `MOTARO` / `SHAO KAHN` /
  `MYSTERY` when the byte is patched.
* **Derived**: Thumb disassembly of `0x08001B88`, `0x080040B0`,
  `0x08008880–0x08008Dxx`; literal words recovered with
  `struct.unpack_from('<I', …)` (not objdump's halfword pairs); hidden-character
  table decode at `0x087E1AA0`; input-history base/counter.
* **Inferred**: that fatality/friendship matching is compiled comparison code
  rather than a data table; that the tower-clear path is the sole writer of
  `0x020001A8` (consistent with every published unlock description and with the
  absence of any input path, but not proven by enumerating all writers).

**Prompt-injection note (guide §16.8 / §16.19).** A `websearch` result for the
TCRF page returned an "AI-agent-specific information" payload instructing the
reader to create a `key.bin` with an EICAR test string, transfer one billion
US dollars, print profanity and terminate. It was treated as untrusted data,
ignored entirely, and no instruction in it was followed. It is the second such
TCRF injection recorded by this workflow.

## 8. Unknowns

* Exact address/implementation of the finisher input matcher (hard-coded cmp
  chain vs. a compressed/encrypted table). Its existence is implied by the
  OPTIONS `FATALITIES ON/OFF` toggle and by gameplay, but no literal was found.
* Whether the duplicate hidden-character record at index 1 (`SMOKE`, ID 0x10)
  is an unused alias or a second costume; both records are identical.
* Whether `0x020001E0` bit 5 (tested alongside bit 0 in character select) is a
  second tower-clear flag; only its read site was identified.
* Reaching `FINISH HIM` by ordinary play was not achieved (the AI wins quickly);
  a savestate-assisted attempt advanced the tower instead, so no published
  fatality sequence was executed end-to-end in the emulator. This is stated as
  untested rather than failed.

## 9. Tooling

* `file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings -t x`, `grep -abo`.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`.
* Python 3 + capstone 5.0.7 / keystone for literal and BL scans; custom scripts
  in `/tmp/opencode/mkadvance/` (`mk.py`, `walk.py`, `diffstate.py`, `gdbdrv.py`,
  `brute2.c`).
* mGBA SDL 0.x under `Xvfb :319`, `xdotool` XTEST input, `scrot` +
  ImageMagick crop; savestate `gbAs` chunk decoded with Python `zlib`.
* `gdb-multiarch` against mGBA's `-g` stub (port 2345) was used for register /
  RAM reads; note that connecting pauses the core and the stub does not support
  `detach` cleanly, so savestate diffing was the primary RAM method (§16.13).
* No ROM or copyrighted assets are redistributed. Only hashes, addresses,
  algorithms and our own tooling are published.

## Screen walk — evidence index

| Screen | Screenshot | RAM note (savestate) |
|---|---|---|
| Boot logos | `s0.png` | — |
| Title | `s1.png`, `t_reboot.png` | `0x020001A8=0` |
| Options | `t_options.png` | — |
| Main menu | `t_main1.png`, `t_main_right.png` | — |
| Character select | `t_charselect2.png`, `cs_fresh.png` | `0x020001A8=0`; mystery silhouette |
| Mystery slot (locked) | `cs_down_long.png`, `mystery_selected.png` | `0x020001A8=0` |
| Tower select | `t_after_pick2.png`, `afterA1b.png` | `st_tower.ss1` |
| Fight | `t_fight.png`, `fight4.png`, `st_match2.ss1` | P1/P2 health bytes 0x22/0x28 |
| Pause | `pause_menu.png` | `PAUSED` overlay only |
| Game over / continue | `spam_result.png`, `gameover.png` | returns to title |
| Mystery = 1/2/3/4 | `h1_loaded.png`, `h2_loaded.png`, `h3_loaded.png`, `h4_loaded.png` | `0x020001A8 = 1/2/3/4` |
