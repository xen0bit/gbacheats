# NBA Jam 2002 (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/NBA Jam 2002/NBA Jam 2002.gba` |
| Size | 4,194,304 bytes (0x400000) |
| Header title | `NBA JAM 2002` |
| Game code / maker | `ABNE` / `51` (Acclaim) |
| Version | 0x00; complement byte 0x28; header checksum 0x0000 |
| Entry word | `0xEA00002E` — stock ARM branch to 0x080000C0 (no cracktro/patch) |
| Embedded headers | exactly one Nintendo-logo-style header at file 0x0000; no multi-game image, no appended trainer |
| MD5 | `17ece80a2d8609e513776e67ef0ecb15` |
| SHA-1 | `38de98758669b120b895661bec3882c3474cf47e` |
| SHA-256 | `b3c532ae4493f16a7901e3aaaca9b39fb3dbbaf0ab2cd0c16ea27b3a212629d4` |

Note: the 156-byte logo at header+4 is a non-standard variant (`24 ff ae 51 69 9a a2 21 …` rather than the usual `24 ff ae 51 69 4a 0f 3b …`). The entry word is stock and the image is a single 4 MiB ROM. Recorded for revision fingerprinting only; it did not affect analysis.

## 2. Executive summary

This GBA SKU has a genuine developer-intended **12-character password system**, not a button-code system. It has two layers:

1. **Three hard-coded unlock codes** stored as plaintext in a custom display-code encoding at ROM `0x083EA99E`, `0x083EA9AB`, `0x083EA9B8`. They unlock the Rookie Team, All-Star Team and special courts. Verified on the real screen.
2. **An algorithmic season/playoffs progress code**. The 12 symbols are 4-bit values; ten payload symbols encode a 16-bit field `A` and a 24-bit field `B` that are unpacked into the season-state struct. The last two symbols are an 8-bit checksum `((sum % 255) + 38) & 0xFF`, where `sum` is `A` plus seven bit-fields of `B`. A final gate requires `B bit0` to match the entry screen's mode (0 = Season, 1 = Playoffs).

The algorithms were reimplemented offline in Python, cross-checked against every published code, and used to mint a novel code **`GFDCCDFGHJNJ`** that appears in no published list. It was entered on the Season password screen, accepted, and produced a demonstrably different season state. Bounds were proven by rejection: a one-symbol checksum corruption (`GFDCCDFGHJNC`) and a valid code entered on the wrong-mode screen were both rejected with `INVALID PASSWORD`.

Exact RAM proof: at the checksum comparison the decoded state struct at IWRAM `0x03007D3C` held `21 43 69 a0 0e a6` — `A=0x4321`, decoded fields `0xa0/0x0e`, checksum `0xa6` — with `r0 == r1 == 0xA6000000` and `r5=1` (accept). For the published code the same address held `68 97 81 07 04 45` (`A=0x9768`, checksum `0x45`).

No GBA button codes, hidden/debug menus, or secret characters were found; the negative is bounded by a full screen walk and a static key-mask table scan (details in §7/§8).

## 3. How to reproduce

* Emulator: mGBA (SDL), `DISPLAY=:317`, `SDL_AUDIODRIVER=dummy`, `-3`.
* Keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows.
* Path to the entry screen: main menu → **SEASON GAME** (or **PLAYOFFS**) → **PASSWORD**. Screen shows 12 slots defaulting to `B`; Up/Down changes the letter, Left/Right moves the cursor, A submits.
* Alphabet (16 symbols, in order): `B C D F G H J K L M N P Q R S T`. Vowels A/E/I/O/U are absent.
* Codes tested (all accepted unless noted):
  * `LHNGBKBBBHKC` → `ROOKIE TEAM UNLOCKED`
  * `LHNGBTBBBHTL` → `ALL STAR TEAM UNLOCKED` (3rd party cheat indexes call this "All NBA Team")
  * `LHNGGDBLBJGT` → `COURTS UNLOCKED`
  * `MKJLBFQBLDGH` → `PASSWORD ACCEPTED` on the **Season** password screen (published as "Playoffs as Toronto Raptors"); `INVALID PASSWORD` on the Playoffs password screen (mode gate)
  * `GFDCCDFGHJNJ` (novel) → `PASSWORD ACCEPTED`, distinct season state
  * `GFDCCDFGHJNC` (bad checksum) → `INVALID PASSWORD`
  * Title-screen button sequences (A/B alternation, L/R alternation, Konami-style d-pad+BA) produced no visible or state change.
* GDB reproduction: `mgba -g -3 <rom>` (stub on port 2345), `target remote :2345`, breakpoint `*0x801B7A4`; on hit read `x/8bx $r9` and `info registers r0 r1 r4 r5 r6`. The struct base is `r9 == 0x03007D3C`.

## 4. Address map

### ROM (file offset = ROM address − 0x08000000)

| Address | Meaning |
|---|---|
| `0x08000000` | Header; entry branch `0xEA00002E` |
| `0x080193DC` | `strcmp`-like compare of two `0xFF`-terminated byte strings; used for the 3 unlock codes |
| `0x08019420` / `0x08019400` | `strlen` / string-copy helpers for the converted password bytes |
| `0x0802E99C` | unsigned integer modulo helper; called with `(sum, 255)`, returns `sum % 255` in `r0` |
| `0x0801AE00`–`0x0801B0A0` | inverse path: packs season state into 12 display codes when the game *shows* a password |
| `0x0801B0E0` | password entry screen. Args: `r0`=state buffer, `r1`=mode (0=Season, 1=Playoffs), `r2`=flag pointer |
| `0x0801B184` | internal-index → display-code conversion switch, jump table literal at `0x0801B198` → table `0x0801B19C` |
| `0x0801B29C`, `0x0801B38E`, `0x0801B480`, `0x0801B580` | cursor/input switches (Up/Down/Right/Left), tables `0x0801B3A0`, `0x0801B49C`, `0x0801B5A0` |
| `0x0801B636` | submit gate: reads IWRAM `0x03001D58` bit0 (A pressed) |
| `0x0801B64C/65C/66C` | three `strcmp` calls against `0x083EA99E`, `0x083EA9AB`, `0x083EA9B8` |
| `0x0801B67C`–`0x0801B7B8` | algorithmic decoder, field unpack, checksum computation and mode gate |
| `0x0801B7CC/D0/D4` | literals pointing at the 3 stored unlock codes |
| `0x0801B87C/8B0/8E4` | unlock handlers: message + flag write |
| `0x0801CB4A` | caller with `r1=1` (Playoffs password screen) |
| `0x080224B8` | caller with `r1=0` (Season password screen) |
| `0x083EA99E` | code bytes `16 12 18 11 0C 15 0C 0C 0C 12 15 0D FF` → `LHNGBKBBBHKC`, handler writes `0x03002025` and shows `ROOKIE TEAM UNLOCKED` |
| `0x083EA9AB` | bytes `16 12 18 11 0C 1E 0C 0C 0C 12 1E 16 FF` → `LHNGBTBBBHTL`, writes `0x03002024`, `ALL STAR TEAM UNLOCKED` |
| `0x083EA9B8` | bytes `16 12 18 11 11 0E 0C 16 0C 14 11 1E FF` → `LHNGGDBLBJGT`, writes `0x03002026`, `COURTS UNLOCKED` |
| `0x083EAB9C`–`0x083EAC44` | ASCII UI bank: `PASSWORD`, `ENTER PASSWORD`, `INVALID PASSWORD`, `PASSWORD ACCEPTED`, three unlock messages |
| `0x0830EE34`+ | tile-indexed text bank (player/team names, 60 records, pointer table at `0x083EAC48`); not used for any cheat text |

### RAM

| Address | Meaning |
|---|---|
| `0x03007D3C` | decoded season-state struct: `+0` u16 `A`; `+2` u16 (low bits from `B17..21`/`B12..16`, high byte is state byte 3); `+3` u8; `+4` u8; `+5` u8 checksum |
| `0x03002024` / `25` / `26` | unlock flags: All-Star / Rookie / Courts (written by the three handlers) |
| `0x03001D58` | submit flag (bit0 = A pressed on the password screen) |
| `0x04000130` | KEYINPUT (active low) |

Savestate mapping (mGBA `gbAs` chunk, 397,312 bytes): raw `0x19000` = IWRAM base; raw `0x20D3C` corresponds exactly to IWRAM `0x03007D3C`.

## 5. Algorithm

### Symbol encoding

Alphabet `ALPHA = "BCDFGHJKLMNPQRST"`, internal value `p[i] = ALPHA.index(char)+1` (1..16).
The display/glyph code is `letter_ordinal + 10` (vowels skipped): internal 1..16 → `12,13,14,16,17,18,20,21,22,23,24,26,27,28,29,30`. The stored unlock strings use these display codes, which is why a literal ASCII search for the published passwords fails.

### Decoder (exact enough to reimplement)

```
p[0..11] in 1..16
A = ((p0-1)<<12)|((p1-1)<<8)|((p2-1)<<4)|(p3-1)          # 16 bits
B = ((p4-1)<<20)|((p5-1)<<16)|((p6-1)<<12)|((p7-1)<<8)|((p8-1)<<4)|(p9-1)   # 24 bits

f0 = (B>>12) & 31
f1 = (B>>7)  & 31
f2 = (B>>4) & 1 | ((B>>5)&3)<<1
f3 = (B>>1) & 7
f4 = B & 1
f5 = (B>>17) & 31
sum = A + f0 + f1 + f2 + f3 + f4 + f5

check = (sum % 255 + 38) & 0xFF
stored = (p10-1)*16 + (p11-1)

ACCEPT iff (stored == check) and (f4 == mode)   # mode: 0=Season, 1=Playoffs
```

On acceptance the ROM unpacks `B` into the state struct: `f1` and `f4` become state byte 3, `f0`/`f2`/`f3`/`f5` become state byte 4 and the low bits of state word 2, and `A` is stored directly. This is what changes the season/playoffs team split shown after entry.

### Encoder (used to mint the novel code)

Choose payload nibbles `p0..p9`, compute `check`, then set
`p10 = (check>>4)+1`, `p11 = (check&15)+1`.

Verified against the published algorithmic code: `MKJLBFQBLDGH` → `A=0x9768`, `B=0x03C082`, `sum=38791`, `38791%255=31`, `31+38=69=0x45`, stored `(5-1)*16+(6-1)=0x45` ✓, `B&1=0` (Season mode) ✓.

## 6. Tables

| Published effect | Password | ROM table address | Encoding |
|---|---|---|---|
| Rookie Team | `LHNGBKBBBHKC` | `0x083EA99E` | 12 display bytes, `0xFF` terminator |
| All Star Team ("All NBA Team") | `LHNGBTBBBHTL` | `0x083EA9AB` | same |
| Beach/Street Courts | `LHNGGDBLBJGT` | `0x083EA9B8` | same |
| Playoffs as Toronto Raptors | `MKJLBFQBLDGH` | not in ROM | algorithmic, Season screen (mode 0) |

Flag bits: `0x03002024`=All-Star, `0x03002025`=Rookie, `0x03002026`=Courts.

## 6b. Enumeration

**Space definition.** 12 symbols × 16 values = 16^12 = 2.8×10^14 raw strings. Ten symbols carry payload; the final two carry an 8-bit checksum. Field widths: `A` 16 bits, `B` 24 bits, checksum 8 bits. There is one reserved/ignored region: `B` bits 22–23 (the top two bits of `p4`) are never used by the checksum or the state unpack, so each decoded state has 4 aliases that differ only in `p4`. The mode gate fixes `B bit0` (`p9` parity).

**Count of accepted strings.** Per mode: `16^4 (p0..p3) × 16 (p4, aliases included) × 16^4 (p5..p8) × 8 (p9 with correct parity) × 1 (unique valid suffix) = 549,755,813,888`. Plus the 3 table codes (which do not satisfy the algorithmic checksum and are checked first). Both Season and Playoffs screens therefore accept enormous spaces; this is a generated progress code, not a small closed table.

**Novel code (not on 3rd party cheat indexes or any other published list):**

`GFDCCDFGHJNJ`
* Generated from `A=0x4321`, `B=0x123456`, `sum=17213`, `17213%255=128`, `check=0xA6` → suffix `NJ`.
* Entered on the Season password screen → `PASSWORD ACCEPTED` (screenshot `novel_submit1.png`) and a distinct "SEASON FIRST HALF" team split (Home: Mavericks, Heat, Cavaliers, Raptors, Nets, Grizzlies, T'wolves, Rockets, Sonics, 76ers; Road: Kings, Wizards, Spurs, Magic — screenshot `novel_effect4.png`), demonstrably different from the published code's split.
* RAM proof (GDB breakpoint `0x0801B7A4`): `r9=0x03007D3C`, bytes `21 43 69 a0 0e a6`, `r0==r1==0xA6000000`, `r5=1`.

**Bounds proven by rejection:**
1. `GFDCCDFGHJNC` — identical payload, last symbol changed so stored checksum is `0xA2` instead of `0xA6` → `INVALID PASSWORD` (screenshot `badchecksum_submit1.png`). Proves the 8-bit checksum layer.
2. `MKJLBFQBLDGH` — checksum-valid and accepted on the Season screen, but `B&1=0` while the Playoffs screen passes mode `1` → `INVALID PASSWORD` there (screenshot `playoffs_pub_submit1.png`). Proves the mode-gate layer.
3. The 3 table codes all fail the algorithmic checksum (e.g. `LHNGBTBBBHTL`: computed `0x6A` vs stored `0xF8`), proving they are a separate hard-coded list, not checksum-generated values.

## 7. Validation evidence

**Observed** (emulator screenshots / GDB reads):
* All 16 screens listed in §8 were reached and captured; menu item labels recorded.
* All four published codes produced the stated messages; three distinct unlock banners and `PASSWORD ACCEPTED`.
* Novel code accepted with a distinct season state; two rejection cases observed.
* GDB: `0x03007D3C` contents and `r0/r1/r5` at `0x0801B7A4` and `0x0801B7B6`; `r9` base address.
* Savestate diff between the novel and published accepted states reproduced the exact `A` and checksum bytes computed offline.

**Derived** (disassembly):
* Checksum formula, field bit positions, mode gate, display-code jump tables, unlock flag addresses, caller mode arguments, modulo helper at `0x0802E99C`.
* Every published code was checked against the derived formula; the algorithmic one matches exactly.

**Inferred:**
* The semantic meaning of individual `B` bit-fields (team/record/quarter etc.) was not labelled; only their effect on the displayed season team split was observed. The 4-way `p4` aliasing is derived from unused bit positions, not separately typed into the UI.

**Prompt injection:** fetched web pages (3rd party cheat indexes, etc.) contained no instructions-directed-at-the-agent; all were treated as data. No action was taken on any embedded text.

## 8. Unknowns

* Exact game-side meaning of each unpacked `B` field (win/loss counts, opponent slot, etc.) — the ROM writes them into the season struct, but only the resulting team split was observed.
* The tile-indexed text bank at `0x0830EE34`+ (60 records) was inspected; it is a name-data bank, not a cheat/menu bank. Its font mapping was not fully decoded, but no negative conclusion in this report depends on it — every screen was walked directly and all cheat UI text was found as ASCII at `0x083EAB9C`+.
* No battery-persistent unlock state was examined beyond the IWRAM flag addresses; the generated `.sav` was 0 bytes and unlock banners were observed in-session.

### Screens walked (RAM/screenshot evidence)
DC Studios splash; title / PRESS START; main menu (SEASON GAME, PLAYOFFS, QUICK GAME, JAM MODE, HORSE MODE, PRACTICE MODE, OPTIONS); PLAYOFFS submenu (NEW GAME, PASSWORD); SEASON submenu (NEW GAME, PASSWORD); password entry (both modes); OPTIONS (Difficulty, SFX, Music, Advanced, Credits, Continue) and its rolling Credits screen; ADVANCED OPTIONS (Player Switch, Shot Timer, Quarter Length, Continue); CHOOSE YOUR TEAM (29-team scrollable list); PLAYER LINE UP / VERSUS stats; TODAY'S GAME matchup; gameplay; Game Paused (A Quit / B Resume / Select Timeout); SEASON FIRST HALF team-split screen; and all result screens (3 unlock banners, PASSWORD ACCEPTED, INVALID PASSWORD). No hidden/debug screen was reached by any of these paths or by button sequences.

### Button-code negative (bounded)
* No published GBA button code exists: web search found only arcade/SNES initials+button codes, PS2/Xbox icon codes, and CodeBreaker/Action-Replay memory cheats (out of scope).
* Static scan of the whole 4 MiB for `u16` button-mask runs (active-high masks `0x001,0x002,0x004,0x008,0x010,0x020,0x040,0x080,0x100,0x200`): 221 runs of length ≥4, of which only 27 had ≥3 distinct values; all are alternating `0x100/0x80` graphics/data patterns in high ROM regions, with no validator or plausible multi-press sequence table.
* Title screen: four button sequences pressed and screens compared — no menu or state appeared.
* Pause screen: only the three documented actions; no hidden entry.

## 9. Tooling

* `arm-none-eabi-objdump -M force-thumb` for disassembly; Python + `struct` for literal pools/jump tables.
* `pwmodel.py` — decoder/encoder and checksum, included as the reimplementation above.
* `typ.py`/`gba.py` — xdotool automation (hold 60 ms, gap 160 ms; shorter holds caused duplicated/dropped presses).
* mGBA GDB stub (`-g`, port 2345) for the validator-as-oracle RAM proof.
* mGBA `.ssN` savestates: PNG with zlib `gbAs` chunk; `zlib.decompress` + byte diff (IWRAM base at raw `0x19000`).

## 10. Legal note

No ROM, extracted graphics, audio, or copyrighted assets are redistributed. Only hashes, addresses, algorithms, and self-generated codes are published.
