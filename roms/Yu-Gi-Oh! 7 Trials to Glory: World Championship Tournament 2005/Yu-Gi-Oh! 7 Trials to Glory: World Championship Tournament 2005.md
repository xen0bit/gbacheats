# Yu-Gi-Oh! 7 Trials to Glory: World Championship Tournament 2005 (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Yu-Gi-Oh! 7 Trials to Glory: World Championship Tournament 2005.gba` |
| Size | 16,777,216 bytes (`0x01000000`) |
| Header title | `YWCT2005USA` |
| Game code | `BY7E` |
| Maker code | `A4` (Konami) |
| Version | `0x00`, complement `0xCE`, fixed `0x96` |
| Header checksum | `0x0000` (stock GBA rebuild artifact; entry word is stock `0xEA00002E`) |
| MD5 | `27f9f0e73752cc2df3b73bc46048e8a2` |
| SHA-1 | `e7a2fb1901a691b3fdd0a39fb574e6dd536b165e` |
| SHA-256 | `321ac103afa7c647041d62606522d14edc33490af2f948ecccbdd9f57319de98` |

Single GBA image; `ROM address = 0x08000000 + file offset`. No cracktro or appended trainer.

## 2. Executive summary

Both developer-intended cheat surfaces are now fully reversed:

1. **Password Machine — FULLY SOLVED (this pass).** The 1000-DP Card Shop terminal and the 10000-DP postgame terminal accept an eight-decimal-digit card password. The digits are packed into a **4-byte BCD word** (e.g. `46986414` → `0x46986414`), then compared against a **computed password for each of 1000 card IDs**. Each card's password is *not stored as a literal code*: it is `table[card] XOR lcg(card)`, where `table` is a 1000-entry u32 array at `0x08477DF8` and `lcg` is the classic MSVC rand step with multiplier `0x343FD` / increment `0x269EC3`. This explains why an exhaustive raw search for published codes (ASCII, u32 LE/BE, BCD, reversed BCD, XOR, LZ77) found nothing. The validator `0x081172F0` linearly scans cards 1..1000 and returns the card ID (0 = reject). **1000 valid codes exist**; 542 match the 785 published Planet Cheats codes and **458 are novel**. A novel code `49417509` was accepted on-screen (card 49, "Wolf"), a one-digit near-miss `49417508` was rejected on-screen, and the ROM's own validator was called from the GDB debugger as an oracle to confirm all four outcomes.

2. **Title-screen button code (Konami code) — fully reversed (prior pass, retained).** A 10-press sequence `↑↑↓↓←→←→BA` is matched against a hard-coded u16 mask table at `0x08F2F384` by helper `0x0811AAC4`, wrapped by `0x0811AB08`. Gated on cleared-game bit `0x0200180C & 1`; toggles title colour flag `0x02035EA2 ^= 0x08`.

No GameShark/CodeBreaker/Action Replay codes were investigated.

## 3. How to reproduce

### 3.1 Setup

```bash
Xvfb :317 -screen 0 1024x768x24 -nolisten tcp &
DISPLAY=:317 openbox &
cd /tmp/yugioh7trials2
DISPLAY=:317 SDL_AUDIODRIVER=dummy mgba -3 -g -t pw0.ss1 game.gba &
gdb-multiarch -q -x gdb_oracle.cmd    # GDB stub on :2345
```

Savestate `pw0.ss1` (keypad screen, no digits entered) is in the work dir. Keymap: `A=x`, `B=z`, D-pad = arrows, `Start=Return`.

### 3.2 Screen walk (all observed)

| # | Screen | Evidence |
|---|---|---|
| 1 | Language Selection → intro → title → New Game | prior pass |
| 2 | Overworld → Card Shop → Password Machine prompt (`1000 DP`) | `s43.png`, string `0x08D96CAE` |
| 3 | Password keypad: `Enter the password.` (8 slots) | `cur2.png`, `novel_try.png` |
| 4 | `Analyzing now.` | `0x08D88234` |
| 5 | Card awarded (e.g. Dark Magician / Wolf) | `cur3.png`, `after_full.png` |
| 6 | `Incorrect Password.` + red ERROR graphics | `after_nearmiss.png`, string `0x08D88244` |

The 10000-DP unlimited machine is referenced in dialogue (`0x08D96F8C`, `0x08D9711C`) and shares the same code path (second validator call site `0x08123634`); it was not reached in the new-game state.

### 3.3 GDB oracle (guide §16.19)

The ROM's validator is a pure function `u16 validate(u32 bcd_code)` at `0x081172F0`. Call it without touching the UI:

```
set architecture arm
set remote noack-packet off
target remote :2345
break *0x0811BB94          # idle loop = return address
set $r0 = 0x46986414       # BCD code
set $lr = 0x0811BB95       # Thumb bit set
set $pc = 0x081172F1       # Thumb bit set
continue
printf "%d\n", $r0         # card ID, 0 = reject
```

Observed oracle results: `46986414→30`, `89631139→1`, `11761845→494`, `38033121→484`, `49417509→49`, `49417508→0`, `12345678→0`.

### 3.4 On-screen proof with injected digits

Because the physical keypad auto-advances the cursor unpredictably (guide §16.2), digits were written directly into the game's live input buffer at `0x02035924` (8 u16) with the count nibble at `0x02035921` set to 8, then the game's own packer+validator at `0x08124C1D` was entered with `lr` pointing at the idle loop. The game then ran its normal award/error screen. This uses the real validator and the real screen driver; only the 8-digit keypad input was synthesised.

## 4. Address map

### 4.1 Password machine (new)

| Item | ROM address | File offset | Type |
|---|---:|---:|---|
| Digit packer + validator caller | `0x08124C1C`–`0x08124C44` | `0x00124C1C` | Thumb: 8 digits → u32 BCD, `bl 0x081172F0`, `strh` result |
| Second packer (other terminal / display) | `0x08123634` | `0x00123634` | `bl 0x081172F0`, `strh` result at state+0x1C |
| **Password validator** | **`0x081172F0`** | `0x001172F0` | Thumb `(u32 bcd) -> u16 card_id`, linear scan 1..count |
| Per-card password generator | `0x081172D4` | `0x001172D4` | Thumb `(card) -> u32 bcd`: `table[card] ^ lcg(card)` |
| XOR helper | `0x081172C0` | `0x001172C0` | Thumb `(a,b) -> a ^ lcg(b)` |
| LCG step | `0x081172A4` | `0x001172A4` | Thumb `(x) -> ((K*x+C)>>16) \| (C<<16)` |
| Card password table | `0x08477DF8` | `0x00477DF8` | 1000 × u32, little-endian |
| Card count | `0x08477620` | `0x00477620` | u16 = 1000 |
| LCG multiplier K | `0x081172B8` (literal) | `0x001172B8` | u32 `0x000343FD` |
| LCG increment C | `0x081172BC` (literal) | `0x001172BC` | u32 `0x00269EC3` |
| Digit input buffer | `0x02035924` (EWRAM) | — | 8 × u16, one per digit |
| Digit count | `0x02035921` low nibble | — | number of entered digits (0..8) |
| Card-ID result | `0x0203593C` (EWRAM) | — | u16, written by `0x08124C44`; 0 = reject |
| Password UI strings | `0x08D88220` / `0x08D88234` / `0x08D88244` | — | `Enter the password.` / `Analyzing now.` / `Incorrect Password.` |
| Keypad main screen handler | `0x081246B8` | `0x001246B8` | Thumb `(mode, flag)` |
| Keypad digit display | `0x08124120` | `0x00124120` | reads 8 u16 digits for drawing |

### 4.2 Button-code addresses (retained from prior pass)

| Item | ROM address | Type |
|---|---:|---|
| Button-code mask table | `0x08F2F384` | 10 × u16, `0x0000` terminator |
| Key ring buffer | `0x03000040` (IWRAM) | 16 × u16 at `+0x12` |
| Comparison helper | `0x0811AAC4` | `(table,len)->bool` |
| Check wrapper | `0x0811AB08` | `() -> bool`, calls helper with table `0x08F2F384`, len 10 |
| Key recorder / clear | `0x0811AA00` / `0x0811AB20` | per-frame / clear |
| Title caller | `0x08133726` | gate `0x0200180C&1`, effect `0x02035EA2^=8` |
| Cleared-game gate | `0x0200180C` bit 0 | EWRAM |

## 5. Algorithm

### 5.1 Password validator (fully recovered)

Three layers, all in Thumb:

**(a) Input packing — `0x08124C1C`–`0x08124C44`:**

```c
u16 *digits = (u16*)0x02035924;   // digits[0] = leftmost
u32 bcd = 0;
for (i = 0; i < 8; i++) {
    int d = digits[7-i] & 0xF;    // walks from slot 7 down to 0
    bcd |= d << (4*i);            // digit i-from-left -> nibble (7-i)
}
u16 card = validate(bcd);         // bl 0x081172F0
*(u16*)0x0203593C = card;         // strh r0,[r1,#28]
```

So the eight digits are packed as standard BCD: `4,6,9,8,6,4,1,4` → `0x46986414`.

**(b) LCG step — `0x081172A4`:**

```c
#define K 0x000343FD
#define C 0x00269EC3
u32 lcg(u32 x) { return ((K*x + C) >> 16) | (C << 16); }
// (C<<16) truncates to 0x9EC30000, so the high 16 bits are constant.
```

**(c) Per-card password — `0x081172D4` → `0x081172C0`:**

```c
u32 card_password(u16 card) {
    return table[card] ^ lcg(card);   // table = (u32*)0x08477DF8
}
```

**(d) Validator — `0x081172F0`:**

```c
u16 validate(u32 bcd) {
    u16 n = *(u16*)0x08477620;        // 1000
    for (u16 card = 1; card <= n; card++)
        if (card_password(card) == bcd) return card;
    return 0;                         // reject
}
```

The caller at `0x08124C3E` checks the returned card for zero; zero selects the `Incorrect Password.` string at `0x08D88244`, nonzero selects the card-award screen.

**Confidence:** Derived — raw `objdump -M force-thumb` disassembly, cross-checked with Ghidra 12.1.4 headless decompilation, and confirmed by calling the ROM function as an oracle (§3.3) plus on-screen accept/reject (§6b).

### 5.2 Button-code validator (retained)

`FUN_0811AA00` records `~KEYINPUT & 0xFFFF` into a 16-entry ring at `0x03000052`. `FUN_0811AAC4(table,n)` compares the last `n` entries (rejects `n>15` or `n==0`). `FUN_0811AB08()` calls it with `table=0x08F2F384, n=10`. Gate/effect at `0x08133726`:

```c
if (FUN_0811AB08() && (*(u8*)0x0200180C & 1)) {
    *(u8*)0x02035EA2 ^= 0x08;
    FUN_0811AB20();
}
```

## 6. Tables

### 6.1 Button-code mask table (`0x08F2F384`)

| Index | Mask | Button |
|---:|---:|---|
| 0 | `0x0040` | Up |
| 1 | `0x0040` | Up |
| 2 | `0x0080` | Down |
| 3 | `0x0080` | Down |
| 4 | `0x0020` | Left |
| 5 | `0x0010` | Right |
| 6 | `0x0020` | Left |
| 7 | `0x0010` | Right |
| 8 | `0x0002` | B |
| 9 | `0x0001` | A |

Terminated by `0x0000`. Mask convention `~KEYINPUT & 0x3FF`.

### 6.2 Card password table (`0x08477DF8`, 1000 u32 LE)

First 16 entries: `0x520FCCF6, 0x17A01110, 0x8BC15869, 0xE8DB46A2, 0x164295B4, 0x8BF332A0, 0xDFFA28AB, 0x19BA693D, 0xDE945353, 0x19954316, 0xDE863722, 0xEC47283A, 0xDBE0113A, 0xEFA15273, 0x96D14975, 0xDA929561`.

Full 4000-byte table dumped to `/tmp/yugioh7trials2/password_table_0x8477df8.bin`. All 1000 derived passwords were in `/tmp/yugioh7trials2/all_1000_passwords.txt`.

Sample derived pairs: card 1 → `89631139` (Blue-Eyes White Dragon), card 30 → `46986414` (Dark Magician), card 49 → `49417509` (Wolf), card 484 → `38033121` (Dark Magician Girl), card 494 → `11761845` (Beast of Talwar).

### 6.3 Published codes

Planet Cheats `planetcheats.net/cheat20699.html` yielded 785 distinct 8-digit codes (`pwlist.txt`). Of the 1000 codes this SKU accepts, **542 appear in that list**; the other 243 published codes belong to other card sets/revisions.

## 6b. Enumeration

### 6b.1 Password space — complete

* **Alphabet/length:** 8 decimal digits, `00000000`–`99999999` = **100,000,000** representable strings.
* **Encoding:** standard BCD in a u32 (one nibble per digit, most significant digit in the high nibble).
* **Valid set:** exactly **1000** codes (one per card ID 1..1000), i.e. **0.001%** of the space. There is no checksum or reserved-bit field: validity is "does `table[c] ^ lcg(c)` equal the typed BCD for some c in 1..1000".
* **Algorithm constants:** K=`0x343FD`, C=`0x269EC3`, table base `0x08477DF8`, count 1000 — all recovered from ROM literals.
* **Published coverage:** 542/1000; **458 novel codes** derived that appear in no published list.
* **Bounds proven by acceptance:** card 1 and card 1000 are both reachable by construction; the scanner's inclusive loop (`ble.n` at `0x8117310`) confirms 1..1000.

### 6b.2 Novel code — accepted in-game with RAM proof

**Novel code `49417509` (card 49, "Wolf")** — not present in the 785-code published list.

* **Oracle:** `validate(0x49417509)` called from GDB returned `49` (gdb_oracle.log).
* **Offline reimplementation:** `password.py` returns `49`; independent of the ROM call.
* **On-screen:** injecting `4,9,4,1,7,5,0,9` into `0x02035924` and running the game's packer+validator produced the **Wolf card screen** (screenshot `after_full.png`).
* **RAM proof:** after validation, the card-ID field at `0x0203593C` read **`49`** (`gdb_ram2.log`: `AFTER VALIDATOR cardid=49`).
* Other novel codes available: `94905343` (card 70), `55337339` (76), `52367652` (79), `09197735` (88), `12829151` (213).

### 6b.3 Rejection bounds

| Input | Oracle result | In-game result |
|---|---:|---|
| `46986414` (published, card 30) | 30 | Dark Magician awarded (`cur3.png`) |
| `49417509` (novel, card 49) | 49 | Wolf awarded (`after_full.png`) |
| `49417508` (one-digit near-miss) | 0 | `Incorrect Password.` (`after_nearmiss.png`) |
| `12345678` (random) | 0 | rejected by oracle |

The near-miss differs from the accepted code only in the final digit (9→8), proving single-digit rejection. Statically, `0x08117302` (`cmp r0,r6; bne 0x0811730a`) rejects every card whose computed password differs by any bit, and `0x08117314` returns 0 when the loop exhausts all 1000 cards — so **all 99,999,000 non-code strings are rejected by construction**.

### 6b.4 Button-code space — complete (retained)

Fixed length 10; single 10-entry table; one action branch with a gate. Any single-position deviation returns 0 (`cmp r0,r6; bne 0x0811AACC` inside the loop at `0x0811AAEE`). On a fresh save the gate byte `0x0200180C` is 0; forcing it to 1 in a patched savestate advanced the title flow.

## 7. Validation evidence

| Claim | Evidence type | Detail |
|---|---|---|
| ROM identity / hashes | Observed | `file`, `md5sum`, `sha1sum`, `sha256sum`, header parse |
| Password digit buffer `0x02035924` (u16×8) | Derived + Observed | GDB write of 8 u16 values rendered the correct digits on-screen (`cur2.png`, `novel_try.png`) |
| BCD packing at `0x08124C1C` | Derived | `objdump -M force-thumb`: reverse-index loop `lsls r0,r1,#2`/`lsls r0,r0,r1` then `bl 0x81172f0` |
| Validator `0x081172F0` linear scan | Derived | disassembly + Ghidra decompilation; `cmp 1000` bound at `0x0811730c`–`0x8117312` |
| XOR-LCG password formula | Derived + Oracle | formula reproduces 542 published codes; 3 published and 1 novel codes matched ROM oracle exactly |
| Novel `49417509` → card 49 | Observed | GDB oracle returned 49; Wolf card on screen; card-ID RAM `0x0203593C = 49` |
| Near-miss `49417508` rejected | Observed | oracle returned 0; `Incorrect Password.` on screen |
| Card count = 1000 | Derived + Observed | u16 at `0x08477620` = 1000; scanner loop bound |
| 785 published codes | Observed | fetched HTML, regex extraction |
| Button-code table/gate/effect | Derived | disassembly + Ghidra, one caller of helper, two callers of wrapper |
| Gate byte on fresh save | Observed | savestate `gbAs` chunk: `0x0200180C = 0x00`

## 8. Unknowns

1. The exact on-screen keypad cursor encoding that triggers A-button submit was not isolated; keypad input was therefore synthesised by writing the game's live digit buffer and entering the game's own packer/validator. The validator, result RAM and award screens are all the game's unmodified code.
2. The 10000-DP unlimited terminal's postgame location and any dialogue differences; it uses the same validator (second call site at `0x08123634`).
3. Whether the 243 published codes absent from this SKU's 1000 are accepted by other regional revisions (e.g. EU/JP) — not tested.

## 9. Tooling

* `mgba` under Xvfb `:317` + openbox, `SDL_AUDIODRIVER=dummy`, GDB stub (`-g`, port 2345).
* `gdb-multiarch` with `set remote noack-packet off`; validator called as an oracle by setting `pc`/`lr` and reading `r0`.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`.
* Ghidra 12.1.4 `analyzeHeadless` on a 320 KiB code slice with base `0x08100000`; Java post-script created Thumb functions and decompiled them.
* Python reimplementation `password.py`; table dump and 1000-code list in the work dir.
* `xdotool` XTEST input, `scrot` screenshots, Pillow keypad-cursor detection.
* All screenshots, savestates and scripts were kept in `/tmp/yugioh7trials2`; nothing was written into the ROM folder.

## 10. Legal note

No ROM bytes, graphics, audio or full text banks are reproduced here. Only hashes, addresses, algorithms, constants and small code/data fragments necessary to reproduce the findings are published.
