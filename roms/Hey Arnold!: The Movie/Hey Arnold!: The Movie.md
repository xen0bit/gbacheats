# Hey Arnold!: The Movie (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Hey Arnold!: The Movie/Hey Arnold!: The Movie.gba` |
| Size | 4,194,304 bytes (0x400000) |
| Header title | `HEY ARNOLD!` |
| Game code / maker | `AAEE` / `78` (THQ), revision 0x00 |
| Entry word | `0xEA00002E` — stock ARM `b 0xC0` (§16.1 cracktro patch absent) |
| Embedded GBA headers | 1 (Nintendo logo at file `0x4` only) — no concatenated image, no appended trainer |
| Header checksum / complement | stored `0x0000` / `0xEF` (rebuilt-header artifact; computed `-(sum A0..BD)-0x19 = 0xFA00`, complement `0xEF` matches) |
| MD5 | `a234f8b94fafc111ab29f235361baf50` |
| SHA-1 | `26042bbc068390246b3b01f02571659e08414a64` |
| SHA-256 | `cf1c3a91b99e031dbbc2e66ea25286255df6b41418deba67890db55378f370d0` |

No cheat-device / trainer markers (`CODEBREAKER`, `GAMESHARK`, `TRAINER`, `ACTION REPLAY`, `CRC BANDIT`, …) were found. This is a clean retail image.

## 2. Executive summary

This game has **two developer-intended systems**, both found and exercised:

1. **A 9-symbol password save/unlock system** (the main "Password" menu item and the "Password" option in the in-game Pause menu). There is **no plaintext code table**: published codes do not occur anywhere in the ROM in any case/UTF encoding. The system is algorithmic — a 64-symbol on-screen keyboard maps each character to a 6-bit value; the nine values are stored in an IWRAM buffer; a keyed table transform produces a 32-bit payload plus a 6-bit checksum. The full decoder/encoder was reversed, reimplemented in Python, and used to mint an unpublished code which the game accepted and which its own generator later reproduced.
2. **A button combination on the Area Select (Map) screen** that toggles the hidden playable character Helga. The published sequence was verified with a RAM flag before/after, its toggle routine was located, and several undocumented sequences were tested and rejected.

Published GameFAQs/Cheat-Happens codes were verified against the ROM decoder: 17 of 19 decode cleanly; the two corrupted entries (3-2, 3-3) are transcription errors, and a corrected 3-2 was derived. Area **1-1 is absent from every published list** and was reached with a minted code.

## 3. How to reproduce

- Emulator: `mgba 0.10.5` (SDL), `Xvfb :316`, `SDL_AUDIODRIVER=dummy`, `-3` scale, CLI debugger `-d` driven through a FIFO by `/tmp/opencode/heyarnold/mgba_drv.py`.
- Keymap used: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad = arrow keys. All keys held 120–180 ms.
- Menu path: title → `Start` → `Down`,`A` → **Password** screen. Nine-symbol keyboard: D-pad selects, A uses, B deletes, cursor moves to O.K. when slot 9 is filled; A submits.
- To enter an arbitrary password quickly, write its nine 6-bit values to `0x0300167C..0x03001684` with the debugger (`w/1`) while the cursor is on O.K., then press A.
- Area Select: reach it by submitting any valid password (e.g. `mQJB0Cgxg`), then press Up,Down,Right,Left,Left,Right,Down,Up,Select for Helga.
- Pause screen: during gameplay press Start; it contains Continue / Exit / Retry / Password (Password shows the generated password for current state).
- Scripts: `model.py` (decoder/encoder), `mint.py` (code generation), `gen_cmds.py` (byte-array → debugger writes), `ssdiff.py`/`findbuf.py` (savestate RAM diffs), `findcode.py`/`blscan.py` (xref scans). All in `/tmp/opencode/heyarnold/`.

## 4. Address map

| Address (ROM unless noted) | Meaning |
|---|---|
| `0x0808F280` | `T[64]` — 16-bit keyed offset table used by checksum and decoder |
| `0x08076E38` | "all nine slots filled?" predicate (returns 1 iff none is `0xFF`) |
| `0x08076E80` | **checksum validator** (returns 1 on valid) |
| `0x08076F6C` | **payload decoder / semantic validator** (writes game state, returns 1 on valid) |
| `0x080752C0–0x080754E6` | **in-game password encoder** (game state → nine 6-bit values) |
| `0x08075D90` | password keyboard input handler (writes 6-bit value into buffer slot) |
| `0x08075E38` | O.K. handler: calls `0x08076E38`, `0x08076E80`, `0x08076F6C` in sequence |
| `0x0806A9B0` | Helga toggle: `flag = (counter+1) & 1` |
| `0x0300167C` (RAM IWRAM) | 9-byte password input buffer `b[0..8]` |
| `0x03001668` (RAM IWRAM) | decoded game-state base: `+0` lives, `+1` score, `+4` unlocked mask, `+12` completed mask, `+8/+9/+10/+16/+18` item flags |
| `0x03001AD2` (RAM IWRAM) | Helga enabled flag (0 = Arnold, 1 = Helga) |
| `0x0831622A` | hint string `Input the above button#combination at the#Area Select screen.#` |

## 5. Algorithm

Let `b[0..8]` be the nine 6-bit keyboard values, `K = b[8]`.

```
T = 64-entry u16 table at 0x0808F280   (values 0..255, monotonically increasing)

// decoder transform (0x08076F6C) and checksum (0x08076E80) share:
for i in 0..6:  p[i] = (b[i] + T[(K + i) mod 64]) & 0x3F

// checksum (0x08076E80):
sum  = Σ p[0..6]
v7   = (b[7] + T[(K + 7) mod 64]) & 0x3F
valid_checksum = (v7 == (sum & 0x3F))

// payload (0x08076F6C):
payload32 = p[0] | p[1]<<6 | p[2]<<12 | p[3]<<18 | p[4]<<24 | (p[5]&3)<<30
aux       = ((p[5] & 0x3C) >> 2) | (p[6] << 4)

level   = payload & 0x1F          ; must be <= 20
mask    = (payload >> 5) & 0xFFF  ; completed-level mask (consistency-checked)
score   = (payload >> 25) & 0x7F  ; must be <= 99
lives   = aux & 0xF               ; must be 1..9
flags   = (aux >> 4) & 0x1FF      ; only bits 0..4 are consumed by state writes
```

Bits 17–24 of `payload32` are **unused** (aliases: 256 spellings per state). The encoder is the exact inverse (subtract `T` entries mod 64, recompute `b[7]` from the sum). Byte-level reimplementation is in `model.py`; it reproduces 17/19 published codes exactly and accepts/rejects in agreement with the ROM.

## 6. Tables

**Keyboard alphabet (64 symbols, index = 6-bit value), read from the password screen:**

```
 0..14  b c d f g h j k l m n p q r s
15..29  t v w x y z B C D F G H J K L
30..44  M N P Q R S T V W X Y Z 1 2 3
45..59  4 5 6 7 8 9 0 ! ? $ % & # + -
60..63  < > : .
```
(Vowels are omitted; `&` is the "and" glyph noted by GameFAQs.)

**T table (first/last entries):** `T[0]=0, T[1]=6, T[2]=12, … T[62]=255, T[63]=255`; full 64-entry dump is in `dumptable.py` output / `model.py`.

**Published area passwords (GameFAQs + Cheat Happens), decoded:**

| Area | Password | level | mask | score | lives |
|---|---|---|---|---|---|
| 1-2 | `mQJB0Cgxg` | 2 | 0x001 | 82 | 3 |
| 1-3 | `Vfcc#z>X-` | 3 | 0x003 | 28 | 5 |
| 1-4 | `&BtrYyly7` | 4 | 0x007 | 46 | 2 |
| 2-1 | `x6SMLJvcG` | 5 | 0x00F | 66 | 1 |
| 2-2 | `n5Gycvd5t` | 6 | 0x01F | 26 | 2 |
| 2-3 | `wfNGVylPs` | 7 | 0x03F | 73 | 1 |
| 2-4 | `ZN+!36QY.` | 8 | 0x03F | 31 | 2 |
| 3-1 | `Qw5YS6?pD` | 9 | 0x0BF | 32 | 4 |
| 3-2 | `s:Ky2zd0t` (corrected) | 10 | 0x1BF | 15 | 3 |
| 3-3 | published forms corrupt | 11 | — | — | — |
| 3-4 | `5Kk9?r46B` | 12 | 0x7BF | 36 | 9 |
| 4-1 | `>1WfSP%XN` | 13 | 0xFBF | 50 | 9 |
| 4-2 | `m!sllSk+j` | 14 | 0xFBF | 99 | 9 |
| 4-3 | `LjPK00GSf` | 15 | 0xFBF | 15 | 9 |
| 4-4 | `4D87Rl0MC` | 16 | 0xFBF | 61 | 9 |
| 5-1 | `c1jnpQ%-N` | 17 | 0xFBF | 70 | 9 |
| 5-2 | `w&xKCW>mv` | 18 | 0xFBF | 7 | 9 |
| 5-3 | `7D8qYmM6C` | 19 | 0xFBF | 64 | 9 |
| 5-4 | `fXc-bz1Sl` | 20 | 0xFBF | 5 | 9 |

Published-list defects: GameFAQs 3-2 (`:Ky2zd0t`) and 3-3 (`+Xm`) are truncated; Cheat Happens' 9-char `s:ky2zd0t` and `+xm<qb28l` still fail the checksum. Single-character repair search finds `s:Ky2zd0t` (level 10, key `K=3`, consistent mask `0x1BF`) as the unique plausible 3-2 correction. Area **1-1** is not published.

**Button code:** at Area Select, `Up,Down,Right,Left,Left,Right,Down,Up,Select` toggles Helga (`0x03001AD2` 0↔1). The sprite changes on the map and in-stage dialogue is attributed to HELGA.

## 6b. Enumeration

**Space definition.** Input space = 64^9 ≈ 2.88×10^16 (2^54) symbol strings. Meaningful payload fields: 5-bit level (≤20) + 12-bit completed mask + 7-bit score (≤99) + 4-bit lives (1..9) + 5 item flags + 6-bit key = ~39 bits; the 6-bit checksum constrains one symbol. Unused payload bits 17–24 give 256 aliases per state, so published "duplicates" are expected and were not counted as distinct codes.

**Validator model.** `model.py` implements the checksum, transform, payload layout, and all semantic range checks (§5). Cross-checks: it exactly reproduces 17 published codes, rejects the two corrupted published forms, and agrees with the game on accepted *and* rejected minted inputs.

**Novel codes (no published list).**
- **`c+!5-:Jkb`** — level 1 (1-1; absent from GameFAQs, Cheat Happens, TCRF, VGChartz), lives 7, score 42, key 0. Entered via RAM buffer + O.K. **Accepted.** RAM after acceptance: `0x03001668=0x07` (7 lives), `0x03001669=0x2A` (42 score), `0x0300166C=0x00000001` (level-1 unlocked), `0x03001674=0`. Screens: AREA SELECT "Arnold's Street", STAGE SELECT, stage intro `1-1 Arnold's street. OBJECTIVE You must find all five of Arnold's friends.`, and gameplay. The game's own Pause→Password screen later displayed **`c+!5-:Jkb`**, independently confirming the encoder.
- `mQJB0WgRg` — published 1-2 payload with lives changed 3→7 (novel stat combination); decoder-valid. Generated and validated offline.
- `1G%5h4Lrb` — level 10 with a different key (novel keying of a published level); decoder-valid.

**Bounds proven by rejection.**
- `?Gy5ZVJsb` (level index 21, out of range, checksum-valid): submitted at the password screen → **rejected**, slots cleared to `?`, screen unchanged (`badlevel.png`).
- `c+!5-:Jkb` with only `b[7]` changed `0x07→0x08` (wrong checksum): **rejected** (`badcheck.png`).
- Button code: reverse sequence, 8-press prefix (no Select), random 6-press, 6-press `Up,Down,Right,Left,A,B`, `Up,Down,Right,Left,Select,Start`, and published sequence + extra A — all left `0x03001AD2` at 0 (no effect). Published sequence toggles 0→1 and 1→0.

## 7. Validation evidence

- **Observed** (emulator/screenshots/RAM): title menu, password keyboard, area select, stage select, stage intro, gameplay/dialogue, pause menu, pause-password display; Helga sprite change; novel code acceptance and RAM field values; both rejections; button-code flag toggles; game-generated password matching the minted code.
- **Derived** (disassembly): checksum and decoder equations, keyed table `T`, payload bit layout, input handler and buffer address, encoder, toggle routine.
- **Inferred**: exact meaning of the five item-flag bits (icons shown in Pause menu: shoe, skateboard, teeth, tomato, basketball, golden tomato) — written to state `+8..+18` but each individual bit's gameplay effect was not exhaustively tested. The "hint" string at `0x0831622A` was located but the exact screen that displays it was not reached; its adjacent data (`00 01 03 02 04 05` at `0x08316224`) was tested as several button combinations with no effect.

## 8. Unknowns

- No standalone button-mask table was isolated for the Helga combination. Exhaustive literal searches over standard/inverted/swapped/raw u8/u16/u32 encodings, forward and reversed, found no 3-press prefix in ROM; the matcher appears to compare a runtime press history against immediate constants. Consequently, **completeness of the button-code set is not proven** — the published code is verified and several alternatives are rejected, but untested sequences could exist. (§16.3: this is "no table found", not proof of "no other codes".)
- The 3-3 published password could not be uniquely repaired (seven single-character candidates decode to level 11 with differing masks); the correct form was not confirmed in-game.
- Bits 17–24 of the password payload are aliases; bit-level semantics of the five item flags remain labelled by effect only.
- No hidden debug menu exists by string evidence: a case-insensitive keyword scan of the whole 4 MiB ROM (9 hits) found only dialogue/credits text and no `debug`/`test menu` string.

## 9. Tooling

- `python3`, `capstone 5.0.7`, `keystone`, `arm-none-eabi-objdump -M force-thumb`, `mgba 0.10.5 -d` CLI debugger driven by `pexpect` over a FIFO (`mgba_drv.py`), `Xvfb :316` + `openbox`, `xdotool`, `scrot`, ImageMagick, `gdb-multiarch` (GDB stub compiled out of this mgba build; CLI debugger used instead).
- Savestate RAM extraction: zlib-decompress the PNG `gbAs` chunk to a 397,312-byte image; IWRAM at state `0x19000`, EWRAM at `0x21000`.
- Analysis scripts: `phase0.py`, `phase1*.py`, `verify_literals.py`, `findbuf.py`, `findcode.py`, `blscan.py`, `model.py`, `mint.py`, `gen_cmds.py`, `dumptable.py`, `btn*.py`.

**Legal note:** no ROM data or copyrighted assets are redistributed; only addresses, hashes, algorithms, and the analyst's own scripts/tooling are documented.
