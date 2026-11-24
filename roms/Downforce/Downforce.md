# Downforce (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Downforce/Downforce.gba` |
| Size | 4,194,304 bytes (0x400000, 4 MiB) |
| Header title | `DOWNFORCEAGB` |
| Game code | `ADWE` (header reports `ADWE60`, Rev.00) |
| Maker code | `60` (in-game credits: Smartdog / Titus, 2002) |
| Version | 0x00 |
| Complement check | 0x59 (valid); header checksum word = 0x0000 (rebuilt-header artifact) |
| Entry word | `0xEA0FEFFE` → branch to `0x083FC000` |
| MD5 | `568c9f1558135b0aad12154e84a60909` |
| SHA-1 | `de38e1a082cebb7aa88372feb53cb51e65aee4c1` |
| SHA-256 | `f8144bc709c74ffd79d586f3687221f475a2370c3a4d76e17f72b40775bbd350` |

**Embedded-header / patch scan (§0.2 Phase 0):** exactly one Nintendo-logo header hit, at file offset 0. The entry branch at `0xEA0FEFFE` does **not** go to the stock `0x080000C0`; it goes to `0x083FC000`, which is a valid ARM bootstrap that copies 1 KiB from `0x083FFD58` to EWRAM `0x02010000` and branches to EWRAM. `0x083FFD58` is the MODE 7 scene-release cracktro banner ("MODE 7 BRINGS YOU ::: DOWNFORCE (C) TITUS ::: ENJOY THIS ONE FOLKS…"). So this is a **scene release with a patched entry and an animated intro cracktro**. The cracktro hands off cleanly to the stock game (verified in emulator: intro → "Licensed by Nintendo" → title). No appended trainer menu and no trainer strings were found; the cheat surface documented below is developer-intended game code. The `Shin'en Multimedia. Code: B.Wodok` string at `0x3E8183` is the GAX audio-engine banner (a §11 false positive).

## 2. Executive summary

Downforce has a **5-digit decimal password system** reached from the main menu's `Continue` entry. It is a *generator + validator* pair, not a lookup table:

* The on-screen code is 5 digits `d0 d1 d2 d3 d4`. Only **two** of them carry the payload: `V = 10*d1 + d3`, `V ∈ 1..99`. The remaining three digits (`d0,d2,d4`) are a deterministic check computed from a 512-entry u16 random table.
* The validator at `0x08000BA4` recovers `V` from digits 1 and 3, regenerates the canonical 5-digit code via `0x08000D0C`, compares all five bytes, and on success writes unlock-flag masks and returns `V`. `V=0` and any wrong-check code return `-1`.
* The whole space is **99 accepted codes out of 100,000** possible 5-digit strings. It was enumerated exhaustively with the reversed model.
* **Published-list error found:** 3rd party cheat index list `12711` for the Skye car. That code is **rejected** by the ROM; the correct generated code for that payload is `42216`. `42216` is absent from every published list, was generated from the algorithm, entered in the emulator, and RAM-verified.
* The PS2 button sequences on the same 3rd party cheat index page (Square/Triangle/Circle/L1/R1) belong to the **console version** and do not apply to GBA; CodeBreaker/GameShark entries are memory-edit codes and are out of scope.

## 3. How to reproduce

**Emulator/display:** Xvfb `:315` (1024x768x24), openbox, `SDL_AUDIODRIVER=dummy`, `mgba -3 -g Downforce.gba` (or `mgba -3 -t Downforce.ss1 …` to start at the password screen).
**Keymap verified in emulator:** A = `x`, B = `z`, Start = `Return`, D-pad = arrow keys; hold ~70–150 ms, gap ~180 ms.

1. Boot; the MODE 7 cracktro plays first — press A / Start to skip to the "Licensed by Nintendo" screen, then A to reach the title, then A to reach the main menu.
2. Main menu → `Continue` (4× Down from the top, then A) → "Enter password" screen showing `00000`.
3. Input semantics: Up/Down changes the digit under the cursor; Left/Right moves the cursor. Submit with **A** (not Start). Accepted → "Password accepted: Hidden cars - n/4, Hidden tracks - n/2" + `Continue`. Rejected → "Password invalid, try again:".
4. `Shift+F1` saves a state on the password screen; plain `F1` reloads it. This makes each code test ~12 keypresses.
5. Published codes tested in ROM (all5-digit): `06254, 83424, 16175, 26241, 12711, 17993, 41966, 74883`. Result: seven accepted, `12711` rejected.
6. Novel codes tested: `42216` (V=21) accepted, `69996` (V=99) accepted. Bounds: `00000` (V=0) rejected; `16254` (right V, wrong check digits) rejected.

## 4. Address map

All addresses are ROM (`0x08…`) or IWRAM (`0x03…`) in the analyzed revision; file offset = address − `0x08000000` for ROM.

| Address | Kind | Role |
|---|---|---|
| `0x08000BA4` | Thumb fn | **Password validator** — `int validate(char *buf5)`; returns V (1..99) or −1 |
| `0x08000D0C` | Thumb fn | **Password generator** — `void gen(int V, char *out6)`; writes 5 digits + NUL |
| `0x0800D8C0` | Thumb fn | PRNG — `u16 prng(u16 *state)`; `state++`, returns `T[old&0xFF] ^ T[(old>>8)+0x100]` |
| `0x08018C60` | data | PRNG table `T`, 512 u16 (file offset `0x18C60`); `T[0x100]=0xA901` |
| `0x08000BFC` | Thumb fn | Flag setter for `V & 0xF` (car bits) |
| `0x08000C5C` | Thumb fn | Flag setter for `V >> 4` (difficulty/track bits) |
| `0x08012034` | data | Car mask table `[0x80, 0x100, 0x200, 0x400]` |
| `0x0801204C`, `0x08012060` | data | High-nibble flag tables `[0,0,0x10,0x10]`, `[0,4,4,0xC]` |
| `0x03001D08` | IWRAM | 5 ASCII input digits (confirmed by savestate diff: `30303030 30` ↔ `36323534`) |
| `0x03002998` | IWRAM | Car unlock mask (observed `0x00000000 → 0x00000280` after 42216) |
| `0x0300107C` | IWRAM | Car count (observed `0 → 2`) |
| `0x0300639C` | IWRAM | High-nibble global (observed `0 → 4`) |
| `0x03001DC8` | IWRAM | Stored `V >> 4` (observed `0 → 1`) |
| `0x0800E32C` | Thumb fn | Localized text lookup: `text[lang][id]`, 24-byte records (6 languages) |
| `0x083EF778` | data | Base of the 2025-entry string-pointer table |
| `0x083EFAA8`, `0x083EFB20`, `0x083EFB38`, `0x083EFB50`, `0x08324BA4`, `0x08325460` | data | "Enter password", "Password accepted", "Hidden cars -", "Hidden tracks -", "Your password is:", "Enter password" strings (localized) |
| `0x083FC000` | ARM | Scene-release bootstrap/cracktro loader (entry target) |
| `0x083FFD58` | data | MODE 7 cracktro banner |

**Savestate RAM layout (§16.13):** mGBA `.ss*` is PNG with a zlib `gbAs` chunk; for this 4 MiB ROM the raw state is 397,312 bytes with IWRAM at state offset `0x19000`. Therefore `state_offset = 0x19000 + (iwrap_addr − 0x03000000)`. The digit buffer appears at state `0x1AD08` and the globals above at `0x1B998`, `0x1A07C`, `0x1F39C`, `0x1ADC8`.

## 5. Algorithm

Model recovered from disassembly and verified against the ROM:

```python
T = u16[512] @ 0x08018C60

def prng(s: u16) -> u16:
    old = s
    s = (old + 1) & 0xFFFF
    return T[old & 0xFF] ^ T[(old >> 8) + 0x100]

def generate(V):                       # 1 <= V <= 99
    s = 0
    for _ in range(V):
        R = prng(s)                    # last output; for V<=99, R = T[V-1] ^ T[0x100]
    X = 15 * R
    d = [0]*5
    d[0] = (X // 100000) % 10
    d[1] = (V // 10) % 10
    d[2] = (X // 1000)  % 10
    d[3] = V % 10
    d[4] = (X // 10)    % 10
    return ''.join(map(str, d))

def validate(buf):                     # buf = 5 ASCII digit bytes
    V = (buf[1]-48)*10 + (buf[3]-48)
    if V == 0: return -1
    if buf[0:5] != list(generate(V)): return -1
    apply_flag_setters(V & 0xF, V >> 4)
    return V
```

Notes (matching the assembly exactly):

* `0x08000D0C` initializes the PRNG state word to 0, then calls `0x0800D8C0` exactly `V` times; the outer `cmp r5,r7 / bge` at `0x8000D1A` is only a no-op guard for `V<=0`.
* The digit-writing loop at `0x8000D36` writes `(X/10)%10` after first dividing `X` by 10 — i.e. it emits the **tens, hundreds, thousands, ten-thousands, hundred-thousands** digits of `X` (least-significant-of-the-five first). Positions 1 and 3 are then overwritten with the tens and ones digits of `V`. This interleaving is why positions 1 and 3 are the payload.
* `X = 15*R` is computed as `(R<<4) − R` (`0x8000D30–D32`). `R` is a u16, so `X` can be 6 digits; the 10^5 digit of `X` lands in `d0`, and any 10^6 digit is discarded — still a deterministic check.
* On success `0x08000BFC(V&0xF)` ORs masks from `0x08012034` into `0x03002998` and writes a count to `0x0300107C`; `0x08000C5C(V>>4)` updates `0x03000A6C` / `0x0300639C` and stores `V>>4` at `0x03001DC8`. These are the unlock flags the "Hidden cars / Hidden tracks" counters read.

## 6. Tables

### 6.1 Published codes verified against the ROM

| Published effect | Code | V | Model result | In-game |
|---|---|---:|---|---|
| Intermediate difficulty | 41966 | 16 | generated | accepted |
| Expert difficulty | 74883 | 48 | generated | accepted |
| 1st hidden track — Sydney | 83424 | 32 | generated | accepted |
| 2nd hidden track — Singapore | 26241 | 64 | generated | accepted |
| 1st hidden car — Jojo | 06254 | 65 | generated | accepted |
| 2nd hidden car — Kera | 16175 | 67 | generated | accepted |
| 4th hidden car — Vinnie | 17993 | 79 | generated | accepted |
| 3rd hidden car — Skye | **12711** | 21 | **not generated** | **rejected** — published error |

Sources: 3rd party cheat indexes "Continue Codes – Unlocked via Natural Progression", 3rd party cheat indexes, a2zweblinks; all list the same eight 5-digit codes. The PS2 button codes on the same 3rd party cheat index page are for the console SKU and were not treated as GBA input.

### 6.2 Code field layout

| Digit | Meaning |
|---|---|
| d0 | check — `(X/100000) % 10` |
| d1 | payload tens — `floor(V/10)` |
| d2 | check — `(X/1000) % 10` |
| d3 | payload ones — `V % 10` |
| d4 | check — `(X/10) % 10` |

`V = 10*d1 + d3`, `V ∈ 1..99`. Check digits depend only on `V` (via `T[V-1] ^ T[0x100]`), so there is exactly one canonical spelling per `V` and no aliases.

## 6b. Enumeration

**Space size.** 100,000 strings in `00000..99999`. Running the reversed validator over all 100,000 inputs (an offline equivalent of §16.9) yields **exactly 99 accepted strings**, one for each `V = 1..99`; `V=0` and the other 99,901 strings are rejected. There is no hidden second alphabet and no table of extra codes beyond these 99.

**Complete accepted set (V:code), all 99:**

```
 1:20615  2:90121  3:60737  4:30447  5:90257  6:60160  7:40678  8:10288  9:70690
10:51200 11:01818 12:81921 13:11737 14:01143 15:81651 16:41966 17:31172 18:81585
19:01791 20:32906 21:42216 22:32024 23:82831 24:32247 25:52356 26:12261 27:02473
28:22788 29:42496 30:93900 31:63116 32:83424 33:23634 34:83149 35:93051 36:63068
37:73375 38:63484 39:33394 40:44206 41:44611 42:54420 43:74836 44:44349 45:84257
46:44761 47:14375 48:74883 49:84499 50:45804 51:75515 52:45120 53:35739 54:35647
55:85550 56:95066 57:15670 58:95982 59:55692 60:96600 61:86519 62:86728 63:06233
64:26241 65:06254 66:46863 67:16175 68:96085 69:76793 70:87308 71:17211 72:97423
73:07232 74:07942 75:37752 76:57863 77:97670 78:77889 79:17993 80:28202 81:48517
82:18329 83:48939 84:18346 85:18756 86:08862 87:08873 88:08981 89:68392 90:19200
91:19416 92:69528 93:99335 94:29945 95:99556 96:29267 97:29674 98:99281 99:69996
```

**Novel codes generated and confirmed in-game (absent from every published list):**

| Code | V | In-game result |
|---|---|---|
| **42216** | 21 | "Password accepted" — Hidden cars 2/4, Hidden tracks 0/2; RAM proof below |
| 69996 | 99 | "Password accepted" (different payload, accepted) |
| 20615 | 1 | generated (model); candidate from the lower range |
| 31172 | 17 | generated (model); candidate from the mid range |

The first two were typed on the real password screen and accepted. `42216` also **corrects** the published Skye entry: the published payload V=21 corresponding to Skye has canonical code `42216`, so this is simultaneously a novel code and a correction to the public list.

**In-game RAM proof for 42216** (savestate slot 8 before, slot 9 after; `gbAs` chunk):

| Address | Name | Before | After |
|---|---|---|---|
| `0x03002998` | car mask | `0x00000000` | `0x00000280` (bits 0x80 + 0x200, i.e. V&0xF = 5 = bits 0,2) |
| `0x0300107C` | car count | `0x00000000` | `0x00000002` (matches "Hidden cars 2/4") |
| `0x0300639C` | high-nibble global | `0x00000000` | `0x00000004` |
| `0x03001DC8` | stored `V>>4` | `0x00000000` | `0x00000001` |

**Bounds proven by rejection:**

* `00000` → `V = 0`; validator's `cmp r5,#0 / mov r0,-1` path → "Password invalid, try again:" (observed).
* `16254` → correct `V = 65` (digits 1,3 unchanged) but corrupted check digit d0; regenerated code `06254` ≠ `16254` → "Password invalid, try again:" (observed). This isolates the checksum layer from the payload layer.
* No code with `V > 99` is expressible (positions 1 and 3 are single decimal digits), so the payload bound is structural as well as arithmetic.

## 7. Validation evidence

* **Observed:** all screen transitions and menu contents above; `06254/83424/16175/26241/17993/41966/74883` accepted; `12711/00000/16254` rejected; `42216` and `69996` accepted; savestate RAM deltas listed in §6b; digit buffer bytes at `0x03001D08`.
* **Derived:** validator `0x08000BA4`, generator `0x08000D0C`, PRNG `0x0800D8C0`, table address `0x08018C60`, field layout, and the exact 99-code space — all read from disassembly and reimplemented; the model reproduces 7/7 genuine published codes and the accepted novel codes.
* **Inferred:** the semantic names "cars" vs "tracks/difficulty" for the high-nibble tables come from correlating `V` with the on-screen counters and the published effect labels; the bit-level purpose of `0x03000A6C`, `0x0300639C`, `0x030041B8` beyond the values measured is not fully exercised.

## 8. Unknowns

* The high-nibble flag tables (`0x0801204C`, `0x08012060`, `0x08012044`) were only exercised for the published payloads and V=21/99; their exact bit-to-effect map for every high nibble 0..6 was not enumerated one-by-one in-game.
* The localized string `Debug` exists in the text bank (e.g. `0x08325570`, text IDs 25/33) but **no debug option or hidden screen is reachable** from title, main, options, car select, track select, or pause; it appears to be an unused leftover label.
* The credited PS2 button codes were not tested because they use non-GBA buttons and are from a different SKU; GBA CodeBreaker/GameShark codes are memory patches (out of scope).
* Cracktro code at `0x083FC000`/`0x083FFD58` was identified but not fully disassembled; it is a scene intro, not an in-game cheat.

## 9. Tooling

* `file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd` — Phase 0 fingerprint.
* `strings -t x`, `grep`, Python `struct` scans — literal/pointer/xref discovery.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` — disassembly of the validator/generator/PRNG.
* Capstone 5.0.7 + Keystone (installed via pip `--break-system-packages`) — BL-target and literal-pool scans.
* Python reimplementation + exhaustive 100,000-input validator sweep — enumeration and bounds.
* mGBA under Xvfb `:315`, `xdotool`, `import`/`scrot`, ImageMagick — dynamic screen walks, code entry, screenshots.
* REA/Ghidra was attempted for decompilation but timed out on the 4 MiB raw ARM image (330 s startup deadline); all conclusions rest on manual disassembly and emulator/RAM evidence instead.
* Helper scripts in `/tmp/downforce/`: `keys.py` (keypress driver), `test_codes.py`, `verify_codes.py`, `final_tests.py`.

No ROM bytes or copyrighted assets are redistributed in this report; only addresses, hashes, algorithms, and generated code strings are published.
