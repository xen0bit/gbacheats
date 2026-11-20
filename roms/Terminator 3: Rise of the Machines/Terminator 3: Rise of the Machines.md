# Terminator 3: Rise of the Machines (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Terminator 3: Rise of the Machines.gba` |
| Size | 8,388,608 bytes (0x00800000) |
| Header title | `TERMINATOR 3` |
| Game code | `AO3E` |
| Maker code | `70` |
| Version | `0x00` |
| Header checksum | `0x0000` (rebuilt-header artifact; complement byte `0x8A`) |
| Entry word | `0xEA00002E` (stock — no cracktro/trainer patch, §16.1) |
| MD5 | `afa8a9e3d7a2cd86c6ce8331532825b0` |
| SHA-1 | `d7935449c72eb1beb4a9f7e9007855d4357e3155` |
| SHA-256 | `a50aff4c7478692ec04082e9b9e7c4f3b5c3216ff8ff1cb467c92326c56d9009` |

Published GBA codes (GameFAQs, Cheat Happens, mariogba.nl, all agreeing): master/unlock
`HKSGP`; level codes `NRBGB`, `RWHGK`, `NGGGC`, `BMFGT`, `LRHGF`, `NRPGD`,
`RLPGJ`, `LWRGH`, `JGSGF` (Ending). None appears literally anywhere in the ROM —
the system is algorithmic, not a preset table. Console (PS2/Xbox) button codes and
GameShark/CodeBreaker codes are out of scope.

## 2. Executive summary

The game has a real developer password system. The title-screen **PASSWORD** menu
opens a 21-consonant on-screen keypad and a 5-character password field. The password
is an **algorithmic 20-bit code**, not a lookup: each character contributes one
nibble, the top 6 bits are an even-bit checksum, and the low 14 bits are a payload
whose top 8 bits are a **scene ID** gated by a hard-coded 10×10 scene table. All ten
published codes satisfy the model (previously-unreported result); the decoder and
encoder round-trip every one of them.

`HKSGP` was entered on the real screen in mGBA and accepted, unlocking the
**SELECT MISSION** screen (Start during play). A newly minted code, **`VRTGC`**
(payload scene 58 / field 7 / flags 1,0 — absent from every published list), was
entered on the real screen and accepted, producing the "TECH-COM 2032" mission
briefing. Running the ROM's own validator on that buffer in the mGBA CLI debugger
wrote scene `0x3A`, field `7`, flag `1`, flag `0` into the four documented RAM globals —
exact agreement with the offline decoder.

Bounds were proven in two independent ways: `CGTRV` (bad checksum) and `BWLSG`
(checksum-valid but scene 99, absent from the 10×10 table) were both entered on the
real screen and both produced **WRONG PASSWORD**. The accepted space is **2,624
codes** (41 table entries × 64 low-bit combinations) out of 21⁵ = 4,084,101 typable
strings; a checksum-only filter leaves 65,536 codes before the scene gate.

A 7-entry debug-menu label table (`0x0875418C`: PLAY GAME, MULTIPLAYER, PASSWORD,
OPTIONS, MUSIC TEST, SOUND TEST, SPLASH TEST) and a large test-scene name bank
exist, but the reachable title menu draws only the first four entries. No reachable
input was found that extends the count; see §8.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 under Xvfb `:317`, `SDL_AUDIODRIVER=dummy`, `-3` scale.
* Keymap (mGBA SDL defaults): D-pad = arrows, A = `x`, B = `z`, L = `a`, R = `s`,
  Start = `Return`. Hold keys ~60–120 ms (45–70 ms per cursor step; longer holds
  double-step).
* Boot → title → **PASSWORD** (down, down, A) → on-screen keypad (3 rows × 7 letters:
  `BCDFGHJ / KLMNPQR / STVWXYZ`). The cursor begins on `B`; move with the D-pad,
  press A to append a character. The fifth press submits automatically.
* `HKSGP` → accepted, mission briefing "GIVE ME SHELTER"; press A through briefing,
  kill cutscene, then **Start** during play → **SELECT MISSION** grid appears.
* `VRTGC` → accepted, briefing "TECH-COM 2032" with T-X dialogue.
* `CGTRV`, `BWLSG` → **WRONG PASSWORD**.
* Offline decoder/encoder: `/tmp/opencode/terminator3/decode.py` (code in §9).
* mGBA CLI debugger (`mgba -3 -d`) was used as a ground-truth oracle: break at
  `0x0800C2F4`, write five byte indices to `0x020346A0`, set `pc`, `trace` until
  return, then read the globals.

## 4. Address map

| Item | Address | Evidence |
|---|---|---|
| Password keypad/entry buffer (5 bytes) | `0x020346A0` (EWRAM) | Derived: literal at `0x080082AC`, `0x0800845C`, `0x0800C378`; observed via debugger reads |
| Entry count | screen struct `+0xD8` | Derived: `0x0800822C`–`0x0808248` |
| Selected keypad index | screen struct `+0xD4` | Derived: `0x080823A` |
| Validator (returns 0/1) | `0x0800C2F4` (Thumb) | Derived + debugger-executed |
| Checksum helper | `0x0800C22C` | Derived |
| Encoder (payload → 5 chars) | `0x0800C258` | Derived; called from `0x08027200` |
| Validator caller (calls it 14× on submit) | `0x0800824C` | Derived |
| Scene-table lookup / gate | `0x0800AB9C` | Derived + traced in debugger |
| Alphabet / font string `-BCDEFGHJKLMNPQRSTVWXYZ\0` | `0x08753BD4` | Derived |
| General keyboard string | `0x08753758` | Derived |
| Scene-ID gate table, 10×10 bytes, `0xFF`=empty | `0x087541AC` | Derived |
| Debug-menu label pointer table (7 entries) | `0x0875418C` | Derived |
| Result scene / level global | `0x0201DF9C` | Derived + observed (`0x3A` after VRTGC) |
| Field global | `0x0201E430` | Derived + observed (`7`) |
| Flag bit0 global | `0x0203B4F4` | Derived + observed (`1`) |
| Flag bit5 global | `0x020358C0` | Derived + observed (`0`) |
| Flag bit5 side-effect word | `0x02035B78` | Derived |
| "WRONG PASSWORD" string | `0x08037FEC` | Derived |
| "SELECT MISSION" string | `0x08038000` | Derived |

## 5. Algorithm

Alphabet (ROM string at `0x08753BD4`, 22 bytes including NUL):

```
index: 0  1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21
char:  -  B C D F G H J K L M  N  P  Q  R  S  T  V  W  X  Y  Z
```

The screen uses indices 1..21 (21 consonants; `-` and `Q` are never emitted —
`Q` is explicitly skipped by both encoder and validator).

**Character ↔ nibble** (position `i` = 0..4, left to right):

```
encode(n, i):  x = n + 1 + 4*(i&1);  if x > 12: x += 1;  return ALPHA[x]
decode(c, i):  x = index(c);  if x > 13: x -= 1;  x -= 1;
               if i&1: x -= 4;  return x        # must land in 0..15
```

**Assembly and checksum** (validator `0x0800C2F4`):

```
acc = 0
for i in 4,3,2,1,0:            # rightmost char becomes the most-significant nibble
    acc = (acc << 4) | decode(buf[i], i)
check = (acc >> 14) & 0x3F     # top 6 bits
payload = acc & 0x3FFF         # low 14 bits
computed = checksum(payload)   # 0x0800C22C
if computed != check: REJECT
```

`checksum(p)` (p is 14-bit): iterate k=0..6, `r = (r | ((p >> 2k) & 1)) << 1`;
return `r & 0x3F`. Equivalently the 5 even bits at positions 4,6,8,10,12
form a 5-bit value shifted left once; **stored checks are always even**.

**Payload fields and scene gate**:

```
scene  = payload >> 6                 # bits 6..13 (8-bit)
field  = (payload >> 1) & 0xF         # bits 1..4
f1     = payload & 1                  # bit 0
f2     = (payload >> 5) & 1           # bit 5
if scene not in SCENE_GRID: REJECT     # 0x0800AB9C; returns its input on a miss
store scene→0x0201DF9C, field→0x0201E430, f1→0x0203B4F4, f2→0x020358C0
set 0x02035B78 = (f2 ? 0 : 0xFFFF)
return 1 (ACCEPT)
```

`SCENE_GRID` is the 10×10 byte table at `0x087541AC`; non-`0xFF` values:
`0, 2, 3, 4, 5, 6, 10, 13, 14, 15, 16, 17, 18, 19, 20, 22, 23, 24, 25, 27,
29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 40, 41, 45, 46, 47, 48, 49, 51, 52, 56, 58` (41 values).

Published codes decode as follows (payload is the truth; published level *labels*
are approximate, per §16.15):

| Code | acc | check | payload | scene | field | f1 | f2 |
|---|---|---|---|---|---|---|---|
| HKSGP (master) | B0D35 | 44 | 0D35 | 52 | 10 | 1 | 1 |
| NRBGB | 0008A | 00 | 008A | 2 | 5 | 0 | 0 |
| RWHGK | 705CC | 28 | 05CC | 23 | 6 | 0 | 0 |
| NGGGC | 1040A | 04 | 040A | 16 | 5 | 0 | 0 |
| BMFGT | E0350 | 56 | 0350 | 13 | 8 | 0 | 0 |
| LRHGF | 30588 | 12 | 0588 | 22 | 4 | 0 | 0 |
| NRPGD | 20B8A | 08 | 0B8A | 46 | 5 | 0 | 0 |
| RLPGJ | 60B4C | 24 | 0B4C | 45 | 6 | 0 | 0 |
| LWRGH | 50CC8 | 20 | 0CC8 | 51 | 4 | 0 | 0 |
| JGSGF (Ending) | 30D06 | 12 | 0D06 | 52 | 3 | 0 | 0 |

Note `HKSGP` and `JGSGF` share scene 52 and differ only in the low 6 bits — the
master-code effect is carried by `field`/flags, not by the scene.

## 6. Tables

* **Alphabet**: `-BCDEFGHJKLMNPQRSTVWXYZ` at `0x08753BD4` (22 bytes incl. NUL).
  On-screen keypad: 21 consonants, Q drawn but never emitted by the encoder.
* **Scene grid**: 10×10 at `0x087541AC`, values listed in §5. 41 non-empty entries.
* **Debug-menu label pointers** at `0x0875418C`: `PLAY GAME`, `MULTIPLAYER`,
  `PASSWORD`, `OPTIONS`, `MUSIC TEST`, `SOUND TEST`, `SPLASH TEST`.
* **Test-scene name bank** at `0x08037B00`–`0x08038010` (SPLASH TEST, SOUND TEST,
  MUSIC TEST, OPTIONS, PASSWORD, MULTIPLAYER, PLAY GAME, "Really Old Mission 3",
  "Crystal Peak Room 1", "C Peak TX Boss", CRS/graveyard/wasteland room names).
* **Global writes**: see §4.

## 6b. Enumeration

**Space definition.** On-screen alphabet = 21 symbols, length 5 → **21⁵ = 4,084,101**
typable strings. Each string maps to a 20-bit value; the top 6 bits are a check and
the bottom 14 a payload. Checksum accepts 1/64 of all 20-bit words (6-bit check, of
which the low bit is forced even by the even-bit checksum). Payload scene is 8 bits,
of which only the 41 values in `SCENE_GRID` pass the second gate. Low 6 payload bits
are unconstrained by code. Therefore:

```
accepted codes = 41 scenes × 2^6 low-bit combos = 2,624
checksum-only survivors before scene gate = 2^14 = 16,384 payloads
```

(All 16,384 payloads have a unique check-satisfying spelling; the encoder at
`0x0800C258` constructs it. The 41×64 figure assumes no extra semantic check after
the scene lookup — the validator writes the four globals and returns 1, so this is a
**Derived** count from the complete instruction path.)

**Novel code generated and confirmed in-game** (absent from GameFAQs, Cheat Happens,
mariogba.nl and every other published list checked):

* **`VRTGC`** — payload `0x0E8F`, scene **58** (grid row0 col1, unadvertised), field
  7, f1=1, f2=0, check 4/4. Entered on the real PASSWORD screen in mGBA → accepted;
  "TECH-COM 2032" briefing shown (`/tmp/opencode/terminator3/evidence_vrtgc.ss1`,
  screenshot in work dir). **Observed (emulator) + Derived (decoder).**
* RAM proof via the ROM's own validator (mGBA CLI debugger, buffer written at
  `0x020346A0`): `0x0201DF9C=0x3A` (58), `0x0201E430=0x00000007`,
  `0x0203B4F4=0x00000001`, `0x020358C0=0x00000000` — exact match to the offline
  decoder. **Observed (debugger).**

**Other mintable novel codes from the same generator** (not published):
`BGBGB` (scene 0, all fields zero), `JGJGC` (scene 24), `VKTGM` (scene 56, field 15,
f1=f2=1), `VGBGB` (scene 0, field 15). Each satisfies the checksum and scene gate
offline; only `VRTGC` was entered in-game.

**Bounds proven by rejection (in-game, on the real screen):**

| Input | Property | Result |
|---|---|---|
| `CGTRV` | my earlier buggy encoder output: checksum 62 vs required 4 | WRONG PASSWORD |
| `VWLSG` / `BWLSG` | checksum **valid** (18/18), scene **99** not in SCENE_GRID | WRONG PASSWORD |
| `VWVVK` | checksum valid, scene **255** (beyond the 8-bit grid domain) | rejected offline by gate model |

The `BWLSG` result isolates the second (scene) gate: the checksum passed, so the
rejection came from `0x0800AB9C` returning its input for a non-grid scene. This is a
bounded negative, not "not tested".

**Published-list verification.** All 10 published codes satisfy the checksum and
scene gates and the encoder reproduces each byte-for-byte (§5 table). `HKSGP` was
entered in-game and accepted; it unlocks the 10-thumbnail SELECT MISSION grid
(reached with Start during play). `HKSGP`'s decoded payload is scene 52 with field
10/f1=1/f2=1, while `JGSGF` (Ending) is scene 52 with field 3/f1=0/f2=0 — the
published "level" labels are therefore not the payload field (§16.15).

## 7. Validation evidence

* **Observed**: title menu (4 items), PASSWORD keypad, SELECT MISSION 10-thumbnail
  grid, MULTIPLAYER link-cable prompt, "GIVE ME SHELTER" and "TECH-COM 2032"
  briefings, in-game HUD, WRONG PASSWORD after `CGTRV`/`BWLSG`; RAM values read via
  mGBA CLI debugger after executing the real validator; check that mGBA savestates
  (`gbAs` zlib chunk, 397,312-byte raw state) were produced for both accepted codes.
* **Derived**: entire validator/encoder/checksum/scene-gate model, all addresses,
  41-entry scene set, 2,624-code count, all 10 published codes' payloads.
* **Inferred**: precise meanings of `field`, `f1`, `f2` (they gate mission
  presentation / unlock state; `f2` writes `0x02035B78`, which appears related to
  the "BONUS"/"LOCKED" UI strings). The exact per-field visual effect was not
  isolated for every combination.

## 8. Unknowns / bounded negatives

* **Debug menu — gated/bounded negative.** The 7-label table at `0x0875418C` and a
  large test-scene name bank are real and the title-menu drawer at `0x0808FCC` loops
  over a count stored at screen-struct `+0xC4`, initialized to **4** at
  `0x0808EE6`. Its dispatch at `0x0808DC8` handles indices `0..5` (`cmp r0,#5;
  bhi`), i.e. at most PLAY GAME…SOUND TEST; index 6 (SPLASH TEST) has no branch in
  that dispatcher. I walked every reachable title item and tried `L+R+Start`; the
  menu stayed at 4 entries and no test screen appeared. Therefore, on the retail
  path exercised, the debug entries are **dead/gated content** (§16.3 cases 2/4),
  not an obtainable in-game cheat. I did not prove that no save-flag or unreached
  code path can raise the count.
* `field`/flags → exact gameplay side effects beyond the two observed briefings.
* Whether any of the other 32 unadvertised scene IDs produce distinct bonus art;
  only scene 58 was entered in-game.
* Console-version button cheats and all GameShark/CodeBreaker codes are explicitly
  out of scope.

## 9. Tooling

* `strings -t x`, `xxd`, `grep -abo`, `arm-none-eabi-objdump -M force-thumb`, Capstone
  (BL/literal scans), Python 3 decoder/encoder:
  `/tmp/opencode/terminator3/decode.py`, model search `brute_model.py`,
  input driver `enter.py`.
* mGBA 0.10.5 under Xvfb `:317` + openbox; `xdotool` XTEST input; `scrot` screenshots.
* mGBA CLI debugger (`mgba -3 -d`, driven through a PTY by
  `/tmp/opencode/terminator3/dbgserver.py`) for RAM reads and as validator oracle.
* No ROM or copyrighted assets are redistributed; only hashes, addresses, algorithms
  and self-generated codes are published.
