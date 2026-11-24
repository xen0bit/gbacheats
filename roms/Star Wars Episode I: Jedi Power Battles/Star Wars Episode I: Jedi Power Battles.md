# Star Wars Episode I: Jedi Power Battles (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Star Wars Episode I: Jedi Power Battles.gba` |
| Size | 8,388,608 bytes (8 MiB) |
| Header title | `JEDIPOWERBAT` |
| Game code / maker / version | `ASWE` / `78` (THQ) / `0x00` |
| Entry word | `0xEA00002E` → `0x080000C0` (stock retail crt0, no cracktro/trainer) |
| MD5 | `2d2a6725da37285d65c34205d08754d7` |
| SHA-1 | `5d5dbfc9c0ed1f89629114429c93ef1b2e1165e5` |
| SHA-256 | `38a1c78f627712e0df66a1c674671af11a3f659e992fb354639491173afbc34f` |

## 2. Executive summary

The GBA SKU has exactly **one developer-intended cheat surface: the 7-symbol "Resume Game" password system**. It is algorithmic, not a lookup table — no published password occurs literally in ROM. I fully reversed both the validator (`0x080B5D94`) and encoder (`0x080B5EA0`), decoded the 32-symbol keyboard alphabet, and derived the complete 35-bit layout: **28 payload bits (four (level, spare-lives) pairs, one per Jedi) + 7 checksum bits**. The accepted space is **2²⁸−1 = 268,435,455** of 32⁷ strings.

I minted a code absent from every published list (`5NPR0HT` — all four Jedis at level 10 with 5 spare lives), typed it on the real on-screen keyboard, observed **VALID**, and captured RAM evidence at the validator breakpoint (input indices `1A 0A 0B 0D 15 05 0F`, ASCII `"5NPR0HT"`, decoded state `0A 05 0A 05 0A 05 0A 05`, checksum `0x3C`). Rejection bounds were proven in-game with a wrong-checksum code and an all-zero code (both **INVALID**), plus an out-of-domain level field with a correct checksum (accepted — the validator has no semantic range check).

Published button codes found on the web belong to the 2025 remaster and the console SKUs, **not** this GBA build. No button-code matcher, hidden menu, or debug-menu entry point was found on this SKU; see §8 for the bounded negative.

## 3. How to reproduce

- Emulator: mGBA 0.10.5 on Xvfb `:316`, `SDL_AUDIODRIVER=dummy`, scaled 3×.
- Keymap (mGBA SDL default): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, D-pad = arrow keys.
- Path: boot → splash screens → **PRESS START** → Start → main menu → highlight **RESUME GAME** (one Down from NEW GAME) → A → password keyboard.
- Keyboard: 32 symbols in three rows plus a green check (accept) and red X (cancel).
  - Row 0: `B C D F G H J K L M N`
  - Row 1: `P Q R S T V W X Y Z`
  - Row 2: `0 1 2 3 4 5 6 7 8 9 *`
- Cursor index 0..33; Left/Right wrap **within the row**, Up/Down change rows. Navigate to a symbol, press A to ADD; B deletes the last symbol; navigate to the green check and press A to submit.
- Control nuance (important): arrow keys must be **short taps (~30 ms)**. 100 ms holds double-step because the game processes held D-pad state (§16.2).
- Test codes: `5NPR0HT` (novel, accepted), `VMT3XRM`/`5PT80KW` (published, accepted), `6NPR0HT` (bad checksum, rejected), `BBBBBBB` (zero state, rejected), `7YT94KY` (level 12, accepted).
- RAM capture: mGBA command-line debugger (`mgba -3 -d`, driven over a pty) with `break 0x080B5D94` (validator) and `break 0x080B5E7A` (success path), then `r/1 <addr>` / `r/2 <addr>` reads.

## 4. Address map

**ROM (file offset = ROM address − 0x08000000):**

| Address | Meaning |
|---|---|
| `0x080B4E00` | Password screen entry/init and frame loop |
| `0x080B503C`, `0x080B51A4`, `0x080B53F4` | Literal pointers to keyboard table `0x087CA188` |
| `0x080B50C4` | Draws the 7 typed symbols |
| `0x080B5144` | Cursor / arrow-key handler (row-wrap rules) |
| `0x080B53C0` | ADD / DEL / ACCEPT / CANCEL handler; calls validator at `0x080B53DA` |
| `0x080B5D94` | **Validator** — decode + checksum; returns `0` accept, `-1` reject |
| `0x080B5EA0` | **Encoder** — 9-byte state → 7 symbols |
| `0x080B5FCC`–`0x080B5FD4` | Encoder literals: source state / output buffer / alphabet table |
| `0x080B60AC` | INVALID display routine |
| `0x080B6120` | VALID display routine |
| `0x0801084C`–`0x08010870` | Copies the 8 decoded bytes into the game's u16 state array at `0x03007A70` |
| `0x087CA178`, `0x087CA180` | ASCII `INVALID\0`, ` VALID \0` |
| `0x087CA188` | **Keyboard/alphabet table**: 32 entries × 8 bytes `{u16 x, u16 y, u16 (ascii\|tile<<8), u16 0}` |
| `0x087CA288`, `0x087CA290` | Special keys: green check (value `0x0300`) and red X (`0x0401`) |
| `0x087CA298`, `0x087CA2A4` | `PASSWORD`, `PRESS START` |
| `0x061D898`–`0x061DB94` | ASCII text bank: `PRESS START`, `NEW GAME`, `RESUME GAME`, `OPTIONS`, `MUSIC OFF/ON`, `SFX OFF/ON`, `PAUSED`, `CONTINUE`, `QUIT GAME`, `Level/Map/Scene/Pause/Fade` |

**IWRAM (observed live):**

| Address | Meaning |
|---|---|
| `0x03007AC0` | 7-byte password **index** buffer (`0xFF` = empty) |
| `0x03007AE8` | 7-byte ASCII display buffer (`'-'` = empty) |
| `0x03007ADC` | cursor (u16, 0..7) |
| `0x03007B00` | selected key index (u16, 0..33) |
| `0x03007B0C` | screen return value (0 accept / −1 cancel) |
| `0x03007AD0` | decoded state: 9 bytes (s0..s7 + checksum) + 3 pad |
| `0x03007B10` | validator's temporary decode buffer |
| `0x030074E8` | input edge flags |

## 5. Algorithm

**Alphabet (index = keyboard position, 0..31):**
`B C D F G H J K L M N P Q R S T V W X Y Z 0 1 2 3 4 5 6 7 8 9 *`
(no vowels; `*` is a real symbol, index 31). Special keys: 32 = green check (submit), 33 = red X (cancel). The keyboard table entry's byte `+4` is the ASCII code; the encoder indexes this same table (`idx << 3`, read byte `+4`).

**Validator (`0x080B5D94`), exact decoder:**

```
p[i] = index of typed char i in ALPHA            # i = 0..6
s0 =  p0 & 0x0F
s1 = ((p0 >> 4) & 1) | ((p1 & 0x03) << 1)
s2 = ((p1 >> 2) & 7) | ((p2 & 0x01) << 3)
s3 =  (p2 >> 1) & 7
s4 = ((p2 >> 4) & 1) | ((p3 & 0x07) << 1)
s5 = ((p3 >> 3) & 3) | ((p4 & 0x01) << 2)
s6 =  (p4 >> 1) & 0x0F
s7 =  p5 & 7
ck = ((p5 >> 3) & 3) | ((p6 & 0x1F) << 2)        # 7-bit checksum

sum = (s0+s1+s2+s3+s4+s5+s6+s7) & 0xFF
accept  <=>  sum != 0  and  sum == ck
```

On accept the 12 bytes at `0x03007B10` are copied to `0x03007AD0` and the function returns `0`; otherwise returns `-1`. Caller (`0x080B53DA`) shows INVALID + error sound on `-1`, else clears two flags, plays sound `15` and calls the VALID display.

**Encoder (`0x080B5EA0`) — inverse, used to mint codes:**

```
ck  = sum(s0..s7) & 0xFF
p0  = (s0 & 15) | ((s1 & 1) << 4)
p1  = ((s1 >> 1) & 3) | ((s2 & 7) << 2)
p2  = ((s2 >> 3) & 1) | ((s3 & 7) << 1) | ((s4 & 1) << 4)
p3  = ((s4 >> 1) & 7) | ((s5 & 3) << 3)
p4  = ((s5 >> 2) & 1) | ((s6 & 15) << 1)
p5  = (s7 & 7) | ((ck & 3) << 3)
p6  = (ck >> 2) & 0x1F
```

**Field meaning** (from published codes + live state, high confidence): the 8 bytes are four `(level, spare_lives)` pairs, one per character, in order: `(s0,s1)` Obi-Wan, `(s2,s3)` Qui-Gon, `(s4,s5)` Mace Windu, `(s6,s7)` Darth Maul. Level is stored as `level−1` (`0`=level 1, `9`=level 10, `10`="all levels"/unlocked). Confirmed by published per-character level ladders (e.g. Obi-Wan L2..L10 only vary `s0` = 1..9; Maul ladders only vary `s6`).

**Cursor rules (`0x080B5144`)** — rows are `0..10`, `11..20`, `21..31`, `32..33`:
- `right(10)=0`, `right(20)=11`, `right(31)=21`, `right(33)=32` (wrap within row).
- `left(0)=10`, `left(11)=20`, `left(21)=31`, `left(32)=33`, `left(33)=32`.
- `down(10)=20`, `down(20)=31`, `down(21..25)=32`, `down(26..31)=33`, else `+11`.
- `up(11)=0`, `up(21)=11`, `up(32)=24`, `up(33)=28`, else `−11`.
(The `left(11)=20` wrap is a real quirk — `bgt` compares the decremented value against the row start, so leaving row 1 to the left wraps to its **last** key.)

## 6. Tables

**Alphabet index → ASCII:** `0:B 1:C 2:D 3:F 4:G 5:H 6:J 7:K 8:L 9:M 10:N 11:P 12:Q 13:R 14:S 15:T 16:V 17:W 18:X 19:Y 20:Z 21:0 22:1 23:2 24:3 25:4 26:5 27:6 28:7 29:8 30:9 31:*`

**Field widths:** `level` fields s0,s2,s4,s6 = 4 bits (0..15); `lives` fields s1,s3,s5,s7 = 3 bits (0..7); checksum = 7 bits (0..127). Max possible sum = 4×15+4×7 = 88, so the checksum always fits.

**Published codes verified against my decoder (44/44 pass):** GameFAQs (`VMT3XRM`, `NMH0YQR`, `MBJ3BYG`, `4MF0ZLP`, `5PT80KW`, Maul/Obi-Wan/Qui-Gon ladders), Cheat Happens / GameGenie Maul and Mace ladders (`VCJ0D2J`…`VCJ0XYK`, `VC1LCGF`…`VCJGCPH`). None appear literally in ROM — they are generator outputs. Action Replay / CodeBreaker / GameShark codes from the same pages are cheat-device codes and are **out of scope**.

## 6b. Enumeration

**Space definition.** 7 symbols × 5 bits = 35 bits → 32⁷ = **34,359,738,368** possible strings. The decoder partitions those into 28 payload bits + 7 checksum bits, so there are 2²⁸ = **268,435,456** payload states. Since max sum = 88 < 128, every payload has exactly one representable checksum. Acceptance additionally requires `sum != 0`, excluding the single all-zero payload. Therefore **exactly 268,435,455 strings are accepted** (no reserved/unused bits — the 35 bits are fully accounted for).

**Validator model validated.** Python reimplementation (`codec.py`) decodes and re-encodes all 44 published codes byte-for-byte (e.g. `5PT80KW` → `[10,7,10,7,10,7,10,7]`, ck 68; `VMT3XRM` → `[0,3,10,7,0,3,9,5]`, ck 37), and rejects garbage.

**Novel code (absent from every published list).** `5NPR0HT`, payload `[10,5,10,5,10,5,10,5]` ck `0x3C` — all four Jedis at "all levels" with **5 spare lives** (published `5PT80KW` uses 7). Generated with the encoder, then typed on the real on-screen keyboard in mGBA:
- Screen after submit: **VALID** (`t_result_5NPR0HT.png`).
- RAM at validator breakpoint `0x080B5D94`: input indices `1A 0A 0B 0D 15 05 0F` (= `5,N,P,R,0,H,T`); ASCII buffer `"5NPR0HT\0"`.
- RAM at success breakpoint `0x080B5E7A`: decoded state `0A 05 0A 05 0A 05 0A 05 3C 00 00 00`, i.e. exactly the minted payload and checksum; register `r4 = 0x3C`.
- Downstream: VALID → PLAYER SELECT (Obi-Wan/Qui-Gon/Mace/Maul) → LEVEL SELECT with levels 1–10 and **FINAL BATTLE** available → level intro → gameplay.

**Bounds proven by in-game rejection / acceptance:**

| Input | Change | Expected | Observed |
|---|---|---|---|
| `6NPR0HT` | first symbol 5→6 (payload 11, checksum left at 60) | checksum failure | **INVALID** |
| `BBBBBBB` | all-zero payload → `sum=0` | zero-sum guard | **INVALID** |
| `7YT94KY` | level fields = 12 (outside advertised 0..10), correct checksum 76 | no semantic check | **VALID** — validator accepts out-of-domain level; gameplay effect of level 12 not exercised |
| level field = 15 | maximum 4-bit value | checksum-valid | accepted by model/validator (derived; not typed in-game) |

The last two rows separate the two layers: the checksum layer is fully proven, while the game's later semantic range handling of level values >10 is an unknown (§8).

## 7. Validation evidence

- **Observed:** all listed screenshots and RAM reads (mGBA + pty debugger breakpoints at `0x080B5D94`, `0x080B5E7A`); VALID/INVALID screens; PLAYER SELECT / LEVEL SELECT / PAUSED screens; 60 fps input double-stepping with 100 ms holds.
- **Derived:** encoder/validator bit layouts from disassembly of `0x080B5D94`/`0x080B5EA0`; cursor transition table from `0x080B5144`; field semantics from decoding published ladders; acceptance count from the proven field widths.
- **Inferred:** mapping of the four (level, lives) pairs to specific Jedi names rests on published per-character ladders; the exact behaviour of level values 11–15 during play was not played through.

## 8. Unknowns

- Gameplay behaviour of checksum-valid but out-of-domain payloads (level 12–15, lives >7) was not played to completion; the validator accepts them but no screenshot of the resulting stage exists.
- The engine text bank contains `Level / Map / Scene / Pause / Fade` at `0x0861DB78`–`0x0861DB8C` with single code xrefs (`0x8010200`, `0x80110D8`, `0x80117B0`, `0x80119A8`). No reachable menu item invoked them during the full screen walk; I did not run a three-count dead-code proof, so whether an engine-internal debug overlay is reachable by an unadvertised input remains formally unproven (low likelihood).
- **Bounded negative for button codes / hidden menus:** web recon of GBA-specific sources (GameFAQs, Cheat Happens, GamesRadar, GameGenie, Almars) lists only the passwords above plus GameShark/ActionReplay/CodeBreaker device codes. Button codes indexed by search engines (`Up Down Up L1 R1 L1`, big-head, radar, PvP, etc.) belong to the 2025 PS5/PS4/Switch remaster and to the Dreamcast/PS2 SKUs — a different SKU (§16.11). A full ASCII sweep found no `DEBUG`, `TEST MENU`, `BIG HEAD`, `RADAR`, `CHECKPOINT` or `Jedi Power Battles On` strings. Every reachable screen was walked (boot splashes, title, 3-item main menu, 2-item OPTIONS, 34-key password keyboard, VALID/INVALID, 4-character PLAYER SELECT, LEVEL SELECT 1–10 + FINAL BATTLE, level intro, gameplay, PAUSED with CONTINUE/QUIT GAME). No button-code surface or hidden menu entry was found on this GBA SKU.

## 9. Tooling

Scripts in `/tmp/jedipower/`: `codec.py` (decode/encode/validate), `scan.py`/`scan2.py` (literal-pointer scans), `model.py`/`fields.py` (published-code decode), `run_code.py` (exact cursor model + BFS pathing), `typeit.py` (30 ms-tap UI driver), `ramev.py`/`decstate.py` (breakpoint RAM capture), `testcode.py` (accept/reject tests), `walkopts.py`/`walkgame.py`/`walknew.py` (screen walks), `mgba_pty.py` (pty wrapper for `mgba -d`). Tools: mGBA 0.10.5 (`-d` pty debugger; `-g` was unavailable due to a port held by another agent), `xdotool`, `scrot`, PIL, `arm-none-eabi-objdump -M force-thumb`, capstone/Python. No ROM or copyrighted assets were redistributed; only hashes, addresses, algorithms and generated codes are published.
