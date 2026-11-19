# Sky Dancers (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Sky Dancers/Sky Dancers.gba` |
| Size | 4,194,304 bytes (0x00400000, 4 MiB) |
| Header title | `SKYDANCERS` |
| Game code | `B4DE` |
| Maker code | `4Z` (Crave Entertainment / David A. Palmer Productions / Gravity-i) |
| Version | 0x00 |
| Fixed byte 0xB2 | 0x96 (correct) |
| Header checksum | 0x0000, complement 0xCD — normal commercial header |
| Entry word | `0xEA00002E` → stock `b 0x080000C0`, **no cracktro / patch** |
| Embedded headers | **1** (logo scan over the whole 4 MiB finds only the one at file 0x0) |
| Build tag | `MultiSio010214` at ROM `0x080101B8` |
| MD5 | `fedf94e93a79d35f70ea85a78fdee5aa` |
| SHA-1 | `a757f4a0586081c1058f7e82bbbb5cede2819036` |
| SHA-256 | `1c3991741b04750e2190a5927863673b1ff7d21351ace7308c07929338614a72` |

This is the retail US image, not a trainer or a multi-game pack. No GameShark/CodeBreaker
content was found or used; everything below is developer-intended.

## 2. Executive summary

Sky Dancers has a real, developer-intended **8-character password system** on the main
menu (`MENU → PASSWORD → ENTER PASSWORD`). It is *not* a plain string table: it is a
**direct positional encoding of eight 32-bit progress indices** in IWRAM at
`0x03000000 … 0x0300001C`. Each index selects one letter from a 21-symbol alphabet
`BCDFGHJKLMNPQRSTVWXYZ`, stored as an array of 32-bit words at ROM `0x080A74C0`.

The generator was recovered completely (§4, §5) and reproduces the live pause-screen
password bit-for-bit: with indices `[3,0,3,0,0,0,0,9]` the ROM displays `FBFBBBBM`.

Twenty published level passwords were recovered from CheatCC (§3.4). They are **not
present as ASCII anywhere in the ROM** — confirmed by literal `grep -abo` for all 20 —
because they are generated numerically. All 20 decode cleanly through the recovered
alphabet. One published entry, `TTPBHC2Q`, contains an OCR error: `2` is not in the
alphabet; the correct symbol is `Z` (`TTPBHCZQ`).

The password layout is: six "flag" characters (bitmask progress: dancers, levels,
mini-games, costumes), one progress/sequence character `i6` (0–20), and one check
character `i7`. `i6 + i7` is constant for a given flag vector; the constant is a
weighted sum of the set bits of the six flag indices (§5, §6). A checksum-valid code
with a flag/`i6` combination absent from every published list was minted:
**`TTPBHCBP`** (and a second, `FBFBBBNZ`). The exact accept/reject gate inside the ROM
was not isolated (see §8); the candidate code is therefore reported as *derived*, and
the in-game rejections that **were** observed are recorded in §7.

## 3. How to reproduce

### 3.1 Emulator / display
```
Xvfb :316 -screen 0 1024x768x24 &
DISPLAY=:316 openbox &
DISPLAY=:316 SDL_AUDIODRIVER=dummy mgba -3 -g "Sky Dancers.gba" &
gdb-multiarch  ->  set architecture arm; target remote :2345
```
mGBA GDB stub holds the core at reset until `continue`; issue `c` once after attaching.
Screenshots: `scrot -o <name>.png`; GBA viewport is 720×480 at +154,+184.

Keymap verified by reading `KEYINPUT` (`0x04000130`) while holding each key:
`x`=A (bit0→0x3FE), `z`=B (bit1→0x3FD), `Return`=Start (bit3→0x3F7),
`BackSpace`=Select (bit2→0x3FB), arrows=D-pad. Hold 60–120 ms; 150 ms double-steps menus.

### 3.2 Screen walk (all reached with screenshots on disk)
1. CRAVE logo → legal text → David A. Palmer / Gravity-i splash → title "PRESS START".
2. Start → `MENU` (PLAY / PASSWORD / TRADE / MINI GAMES / OPTIONS).
3. PASSWORD → `ENTER PASSWORD` with an eight-character editor (`pw_final.png`,
   `clean_pw0.png`, `z_q0.png` … `zdd2.png`).
4. PLAY → story intro ("To free Queen Skyla…", `PRESS START TO SKIP`) → Stage 1 gameplay.
5. Gameplay + Start → `PAUSED` menu: CONTINUE / SFX ON·OFF / MUSIC ON·OFF / ACCESSORIES /
   QUIT, and **the live generated password printed at the bottom** (`paused.png`,
   `pause_pw_zoom.png`: `FBFBBBBM`).
6. TRADE → "PLEASE CONNECT TWO GAME BOY ADVANCE SYSTEMS … LINK CABLE" (`pwscreen.png`).
7. OPTIONS contains SFX/MUSIC toggles and a language selector (ENGLISH, FRANÇAIS,
   DEUTSCH, ITALIANO, ESPAÑOL, NEDERLANDS — string bank `0x0800F10C`–`0x0800F140`).
8. MINI GAMES menu (ANGELICA'S PERFECT AIM, JADE'S SLALOM, CAMILLE'S TREASURE HUNT —
   names at `0x0800F468`/`0x0800F480`/`0x0800F490`, unlocked by progress strings at
   `0x0800FC04`/`0x0800FCE8`/`0x0800FD30`).

### 3.3 Published codes tested
CheatCC list retrieved 2026-11-19 via `r.jina.ai/https://www.cheatcc.com/...` (the site
returns 403 to direct fetches). VGChartz lists 0 cheats. GameFAQs cheats page is blocked
(HTTP 400/403); its search snippet confirms `Stage 03 — TTFBHBXK`, which is item 18 of
the CheatCC list.

## 4. Address map

| Address | Kind | Meaning |
|---|---|---|
| `0x0800CE38` | Thumb fn | **password generator** `gen(mode, attr)` |
| `0x0800CF8C` | literal | `0x03000050` — text-descriptor struct |
| `0x0800CF90` | literal | `0x03005230` — generated password char buffer |
| `0x0800CFAC` | literal | `0x080A74C0` — 21-word alphabet table |
| `0x0800CFB0` | literal | `0x03000000` — base of the 8 progress indices |
| `0x0800CFA8` | literal | `0x03000A9C` — frame/gate counter (`& 31`) |
| `0x0800CFB4` | Thumb fn | text/glyph rendering helper called by `gen` |
| `0x080A74C0` | data | 21 × u32: `0x42,0x43,0x44,0x46 … 0x5A` = `BCDFGHJKLMNPQRSTVWXYZ` |
| `0x03000000..1C` | RAM | 8 × u32 progress indices `i0..i7` |
| `0x03005230` | RAM | 8 chars + NUL of the currently displayed password |
| `0x03000050` | RAM | descriptor: `[0]=0xFF, [1]=attr, [4]=&0x03005230, [8]=1, [9]=1` |
| `0x0800EE38..0x080101B8` | data | English+localized text bank (ASCII, `strings -t x` visible) |
| `0x080101A4` | data | `"PASSWORD ACCEPTED!"` (record pointer at `0x080C9BF4`) |
| `0x080C9BF4` | data | localized message record (12-byte stride, 6 languages) |

## 5. Algorithm

### 5.1 Generator — fully derived, matches ROM output
```
gen(mode, attr):
    d = 0x03000050
    d[0]=0xFF; d[1]=attr; d[4]=0x03005230; d[8]=1; d[9]=1
    buf = 0x03005230
    for k in 0..7: buf[k] = 0x20                     # spaces
    for i in 0..7:
        if i == mode and (*0x03000A9C & 31) <= 15:  # leave this slot blank
            continue
        v = *(u32*)(0x03000000 + 4*i)
        buf[i] = (u8)alphabet32[v]                   # 0x080A74C0[v*4]
    buf[8] = 0
    clear 0x030022FC / 0x030049F8 / 0x03001500 / 0x03003B6C
    call 0x0800CFB4(d, 0, *0x03003B78)               # render
```
Proof: savestate `pause.ss1` (gz-chunk `gbAs` decompressed to 397,312 bytes; IWRAM at
state+`0x19000`) held indices `[3,0,3,0,0,0,0,9]` and the string `FBFBBBBM` at IWRAM
`0x03005230`; alphabet lookup of those indices is exactly `F B F B B B B M`. A
breakpoint at `0x0800CE38` confirmed entry arguments `mode=0`, `attr=0x50` from the
game-start call site `0x08006194`, and a second call `gen(0xFF,0x60)` from
`0x08006D60` (password screen, no blanked slot).

### 5.2 Password layout derived from the 20 published codes
Alphabet value `v ∈ 0..20`. Decoded vectors (char → v):

| Published | i0 | i1 | i2 | i3 | i4 | i5 | i6 | i7 | meaning |
|---|---|---|---|---|---|---|---|---|---|
| FBFBBBCL | 3 | 0 | 3 | 0 | 0 | 0 | 1 | 8 | L1, 1 dancer |
| FBFBBBDK | 3 | 0 | 3 | 0 | 0 | 0 | 2 | 7 | L2, 1 dancer |
| KBFBBBFD | 7 | 0 | 3 | 0 | 0 | 0 | 3 | 2 | L3, 1 dancer |
| KBFBBBGC | 7 | 0 | 3 | 0 | 0 | 0 | 4 | 1 | L4, 1 dancer |
| KBFBBBHB | 7 | 0 | 3 | 0 | 0 | 0 | 5 | 0 | L1, 2 dancers |
| TBFBBBJK | 15 | 0 | 3 | 0 | 0 | 0 | 6 | 7 | L2, 2 dancers |
| TBFBBBKJ | 15 | 0 | 3 | 0 | 0 | 0 | 7 | 6 | L3, 2 dancers |
| TBFBBBLH | 15 | 0 | 3 | 0 | 0 | 0 | 8 | 5 | L4, 2 dancers |
| TCFBCBMD | 15 | 1 | 3 | 0 | 1 | 0 | 9 | 2 | L1, 2 dancers + 1 minigame |
| TCFBCBNC | 15 | 1 | 3 | 0 | 1 | 0 | 10 | 1 | … |
| TCFBCBPB | 15 | 1 | 3 | 0 | 1 | 0 | 11 | 0 | … |
| TFFBCBQR | 15 | 3 | 3 | 0 | 1 | 0 | 12 | 13 | L1, 3 dancers + 1 minigame |
| TFFBCBRQ | 15 | 3 | 3 | 0 | 1 | 0 | 13 | 12 | … |
| TKFBCBSK | 15 | 7 | 3 | 0 | 1 | 0 | 14 | 7 | … |
| TTFBCBTS | 15 | 15 | 3 | 0 | 1 | 0 | 15 | 14 | … |
| TTFBCBVR | 15 | 15 | 3 | 0 | 1 | 0 | 16 | 13 | … |
| TTFBHBWL | 15 | 15 | 3 | 0 | 5 | 0 | 17 | 8 | 3 dancers + 2 minigames |
| TTFBHBXK | 15 | 15 | 3 | 0 | 5 | 0 | 18 | 7 | … |
| TTPBHBYS | 15 | 15 | 11 | 0 | 5 | 0 | 19 | 14 | … |
| TTPBHCZQ | 15 | 15 | 11 | 0 | 5 | 1 | 20 | 12 | … (published as `…C2Q`) |

`i3` is always 0. `i0`, `i1`, `i2`, `i4`, `i5` are low-bit masks
(3=0b11, 7=0b111, 15=0b1111, 11=0b1011, 5=0b101). `i6` is 1..20 (fresh game = 0).

### 5.3 Check relation
For a fixed flag vector, `i6 + i7` is constant (integer, not just mod 21):
9, 5, 13, 11, 25, 21, 29, 25, 33, 32 for the ten distinct flag groups above; the
fresh game 0+9=9 matches the first group exactly.

Define `f(v)` over set bits with weights `w0=-1, w1=14, w2=-4, w3=8`:
```
f(v) = Σ w[b] for each set bit b of v
const = -17 + f(i0)+f(i1)+f(i2)+f(i4)+f(i5)
i7   = (const - i6) mod 21
```
This reproduces **all 21 data points** (20 published codes + the fresh-game password)
exactly. Indices actually observed use only bits 0–3; weights for bits ≥4 are unknown
(§8). A simple linear model in the digit values (`Σ a_j·i_j mod 21`) was tested and is
**inconsistent**, so the bit-level model above is the correct description of the data.

## 6. Tables

* **Alphabet** (21 symbols, index → char, ROM `0x080A74C0`):
  `0:B 1:C 2:D 3:F 4:G 5:H 6:J 7:K 8:L 9:M 10:N 11:P 12:Q 13:R 14:S 15:T 16:V 17:W 18:X 19:Y 20:Z`
  (No vowels, no digits. Any published code containing a digit is an OCR error.)
* **Flag fields**: `i0` = dancers (3/7/15 → 1/2/3), `i1` = levels-cleared mask
  (0/1/3/7/15), `i2` = minigame mask (3/11), `i4` = costume/accessory mask (0/1/5),
  `i5` = final flag (0/1), `i3` = reserved (always 0), `i6` = progress 0–20,
  `i7` = check character.
* **Message bank**: 12-byte records `{char* text, u16, u16}` in 6-language groups;
  `"PASSWORD ACCEPTED!"` at `0x080101A4`.

## 6b. Enumeration

**Representable space.** 8 positions × 21 symbols = 21^8 = **37,822,859,361**
distinct strings. With the field model, only 5 flag fields + `i6` (0–20) + one check
character are free; the observed accepted set is the 20 published progress states plus
the fresh state (`FBFBBBBM`, `i6=0`), i.e. **21 known-valid states** — a tiny, fully
enumerated subset of the string space.

**Published set complete.** CheatCC lists 20 codes, GameFAQs' snippet agrees
(`TTFBHBXK`), VGChartz lists none. All 20 literals are **absent from the ROM as ASCII**
(verified individually), proving they are generated, not tabled. One transcription
error found and corrected: `TTPBHC2Q` → `TTPBHCZQ` (`2` ∉ alphabet).

**Novel codes minted (absent from every list checked):**
1. `TTPBHCBP` — indices `[15,15,11,0,5,1,0,11]`. Highest progress flags (3 dancers,
   2 minigames, final flag) but `i6=0` instead of the published `i6=20`;
   `i7=(32-0) mod 21=11=P`. Checksum-valid by the model of §5.3, never published.
2. `FBFBBBNZ` — indices `[3,0,3,0,0,0,10,20]`. Fresh/dancer-1 flags with the
   unpublished `i6=10`; `i7=(9-10) mod 21=20=Z`. Checksum-valid by the model.

**Bounds proven by rejection (observed):**
* The alphabet has exactly 21 entries — word 21 of the table at `0x080A74C0` is `0`
  and every later word is `0`; indices ≥21 cannot denote a letter, so any character
  outside `BCDFGHJKLMNPQRSTVWXYZ` (including the published `2`) is unrepresentable.
  This is a static, bounded negative from the table dump.
* At the live `ENTER PASSWORD` screen, submitting the default `BBBBBBBB` returned to
  `MENU` with no `"PASSWORD ACCEPTED!"` message and with the progress indices still
  all zero (GDB `x/8wx 0x03000000`) — an observed rejection.
* Writing the literal `FBFBBBCL` into `0x03005230` and submitting likewise returned
  to `MENU` with no state change (indices `[20,1,0,0,0,0,0,0]`, not the code's
  `[3,0,3,0,0,0,1,8]`) — an observed rejection of a RAM-injected, non-UI code path.

## 7. Validation evidence

**Observed** (emulator / GDB / savestate):
* All screens of §3.2, screenshotted on disk (`mainmenu.png`, `pwscreen.png`,
  `pw_final.png`, `paused.png`, `pause_pw_zoom.png`, `gdb_pause2.png`, …).
* `KEYINPUT` values confirming the keymap (§3.1).
* Pause-screen password `FBFBBBBM` and its IWRAM backing bytes
  `46 42 46 42 42 42 42 4D 00` at `0x03005230` (`pause_state.bin`).
* Generator breakpoint at `0x0800CE38` with `r0=0,r1=0x50,lr=0x08006199`;
  second call `gen(0xFF,0x60)` from `0x08006D60`; literal pool read with Capstone
  (not `objdump`'s split-halfword display).
* Hardware watchpoint on `0x03005231` firing inside the generator at `0x0800CE70`
  (`'B' → ' '`), proving the space/cursor byte is written by `gen`.
* The two in-game rejections in §6b.

**Derived** (disassembly / arithmetic):
* `gen()` pseudocode and the alphabet table at `0x080A74C0`.
* Password = `alphabet32[*(u32*)(0x03000000+4*i)]` for `i=0..7`.
* All 20 decoded index vectors and the checksum model of §5.3.
* Novel codes `TTPBHCBP` and `FBFBBBNZ`.

**Inferred:**
* Field *names* (dancers / levels / minigames / costumes) come from the published
  status labels and the unlock strings; the numeric bit positions are derived, the
  semantics are inferred.
* That `i5` is a "final" flag and `i3` is reserved (always 0 in all 21 samples).

## 8. Unknowns

* The exact **validator/accept branch** was not isolated: no ASCII literal, pointer, or
  BL to the alphabet table other than the generator was found, and the accept path
  could not be reached from the entry screen with the codes tried. The two novel codes
  are therefore **checksum-valid derivations, not observed acceptances**. This is the
  one deliverable from §0.2 that remains open.
* The on-screen editor's key semantics (a stray glyph/letter wheel beside the 8
  characters) were not fully mapped; Left/Right/Up/Down were observed to change the
  displayed characters, but not to a reproducible chosen value.
* Checksum weights for index bits 4+ are unconstrained by the sample (all flag values
  use bits 0–3).
* Whether `i6` values other than 0–20, or flag combinations other than the ten groups,
  are accepted by the game's semantic range layer.

## 9. Tooling

* `file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings -t x`, `grep -abo`.
* Python 3 + Capstone 5.0.7 for literal-pool decoding (`Align(addr+4,4)+disp`) and
  Thumb BL scans; `arm-none-eabi-objdump -M force-thumb` for cross-checks.
* mGBA 0.10.5 (`/usr/local/bin/mgba`) under `Xvfb :316` + `openbox`,
  `SDL_AUDIODRIVER=dummy`; `xdotool` XTEST input; `scrot` screenshots.
* `gdb-multiarch` against the mGBA GDB stub (`:2345`) for RAM reads, breakpoints and
  hardware watchpoints; mGBA `-d` CLI debugger as a cross-check.
* Savestate forensics: PNG `gbAs` chunk → `zlib.decompress` → 397,312-byte state;
  IWRAM at +`0x19000`, EWRAM at +`0x21000`, VRAM at +`0x1000`.
* Scripts left in `/tmp/opencode/skydancers/`: `key.py`, `gdbcmd.py`, `scanram2.py`,
  `dumpdiff.py`, `solve2.py`, `pause_state.bin`, and the screenshots referenced above.
* Web: CheatCC via `r.jina.ai`; web.archive.org had no snapshot for GameFAQs/CheatMasters.
  Fetched pages were treated strictly as data (§16.8); no instruction found in them
  was acted upon.

## 10. Legal note

No ROM, extracted graphic, or copyrighted asset is redistributed. Only hashes,
addresses, algorithms, derived codes and observations are published.
