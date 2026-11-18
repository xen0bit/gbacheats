# Midnight Club: Street Racing (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Midnight Club: Street Racing.gba` |
| Size | 4,194,304 bytes (`0x400000`) |
| Header title | `MIDNIGHTCLUB` |
| Game code | `AMQE` (Europe), maker `20`, version `0x00` |
| Header bytes | fixed `0x96` at `0xB2`, complement `0x51`, checksum `0x0000` (normal rebuilt-header artifact) |
| Entry word | `0xEA00002E` — stock branch to `0x080000C0`; **no cracktro / trainer patch** |
| Embedded headers | Exactly one Nintendo-logo hit (file `0x4`) — not a multi-game cart |
| MD5 | `3a2206f7fdcb36034d9fff753964f201` |
| SHA-1 | `66be392d9fb84d39df31ed8c8779cc58612dd4ac` |
| SHA-256 | `0e9bae7465ab4fee35ac5e0c11d8a14a457b660b844be0663466638bff1dd621` |

## 2. Executive summary

The game has a developer-intended **4-letter passcode system** on the
`CAREER OPTIONS → Passcode` screen (alphabet `A`–`Z`, four slots, `DEL` and
`END` cells). It is a **closed lookup table**, not a checksum algorithm:

* The validator at `0x08005130` compares the four entered bytes with each of
  **exactly 11** records in a table at `0x08106A3C` (8-byte stride,
  `{code_ptr, effect_script_ptr}`, terminated by `0xFFFFFFFF` at
  `0x08106A94`). On a match it executes a short bytecode script that sets
  progress/unlock flag bytes, and returns 1; otherwise 0.
* All 11 codes in the ROM (`AGEM MPBA CLSB PLCB TMNS LAPC LGKG GTBP NIML
  NYRA AEHC`) are already present in published GameFAQs / GameGenie /
  ChapterCheats / A2Z lists. **There is no unpublished accepted code**: the
  space is closed at 11 of 26^4 = 456,976 possible strings (§6b).
* In emulator: `AGEM` and `NIML` were typed on the real screen, RAM-verified
  (`0x03003B38` buffer, `0x03003B34` count), accepted (game advanced to
  `VEHICLE SELECT`). `AAAA`, `AGEN`, `AGEX`, `ZZZZ` were rejected (screen stays
  on Passcode Entry, buffer reset to `0x1A`), proving the bounds.
* No hidden/debug menu, no GBA button-code table, and no second algorithmic
  password format exist in this image. The published "Infinite
  Countermeasures … Y, Y, X, Z, Z" text uses PlayStation face-button names
  and has no GBA code surface here.

## 3. How to reproduce

Emulator: mGBA (SDL), `Xvfb :316`, keymap A=`x`, B=`z`, L=`a`, R=`s`,
Start=`Return`, Select=`BackSpace`, D-pad=arrows.

Menu path:
1. `PRESS START` title → Start.
2. `MAIN SELECT` → Down → `Career` → A.
3. `CAREER OPTIONS` → Down → `Passcode` ("UNLOCK IT") → A.
4. `PASSCODE ENTRY`: letters A–Z laid out as 13 columns × 2 rows;
   `Right`/`Left` move by 1 (0–25), `Down` adds 13, `DEL`=26, `END`=27.
   Press `A` on a letter to fill the next slot (internal values 0–25).
5. After 4 slots, navigate to `END` (index 27) and press `A`.
6. Accepted → game switches to `VEHICLE SELECT`. Rejected → stays on
   Passcode Entry with the four slots cleared.

Observed examples (typed via XTEST, not memory-edited):
* `AGEM` → buffer bytes `00 06 04 0C` at `0x03003B38`, count 4 → **accepted**.
* `NIML` → buffer `0D 08 0C 0B` → **accepted**.
* `AAAA` → buffer `00 00 00 00` → **rejected**.
* `AGEN` (one letter off a valid code) → **rejected**.

Screens walked with screenshots on disk in `/tmp/opencode/midnightclub/`:
Rebellion splash, PRESS START title, MAIN SELECT, Extras/GAME OPTIONS
(Biographies, Credits, Music On/Off), CAREER OPTIONS (New, Passcode),
PASSCODE ENTRY, Arcade CITY SELECT (New York, London), WAYPOINT race list
(race 2 shows "Race Locked"), RACE SELECT (Cruise/Head to head/Waypoint),
CRUISE/JOYRIDE, VEHICLE SELECT, LAST CHANCE/Launch, in-race, PAUSE MENU
(Continue / Back to Main Menu). No other screen was reachable.

## 4. Address map

File offset = ROM address − `0x08000000`.

| Address | Meaning |
|---|---|
| `0x08005130` | Passcode validator (`push {r4,r5,lr}`; 4-byte compare loop; returns 1/0) |
| `0x08005140`–`0x08005182` | Core comparator: 4 × `ldrb`/`cmp`, 8-byte record stride, `bl 0x8004E84` on match |
| `0x08007564` | UI "END" handler: `count==4` gate, adds 65 to each buffer byte, calls validator, writes result 5/0, resets buffer |
| `0x0800756E`–`0x08007584` | ASCII conversion loop (`ldrb`/`adds #65`) |
| `0x080074E8` | Reset: sets 4 buffer bytes to `0x1A` (26), count=0 |
| `0x0800751C` | Letter-select handler: writes current letter value into `buffer[count]` |
| `0x08004E8A` | Effect-script VM dispatcher (opcode 0–29, terminator 30) |
| `0x08004EA0` | 30-entry Thumb jump table for script opcodes |
| `0x08004F48`–`0x0805048` | Opcode handlers writing RAM flag bytes (bases `0x03001F90`, `0x03001FF0`, `0x03001FD8`, `0x03001FC4`, `0x03001FE0`, `0x03001FD4`, `0x0300201C`, `0x03001FE4`, `0x03002028`, `0x03002024`, `0x03002020`, `0x0300202C`) |
| `0x08106A3C` | Validator record table (11 × 8 bytes, then `0xFFFFFFFF`) |
| `0x0800EC5C`–`0x0800ECAF` | Code strings: 8-byte stride, `4 ASCII + 4 zero`, reverse order |
| `0x0804C8F4`–`0x0804C94B` | Second copy of the 11 code strings (localized text bank) |
| `0x081067C0`–`0x08106A33` | 11 effect bytecode scripts (one per code) |
| `0x0800ECB4` | 14-entry RAM-copied pointer table initialized by `0x08005184` (UI helpers) |
| `0x03003B34` | RAM: number of entered characters (IWRAM) |
| `0x03003B38` | RAM: 4-byte input buffer, values 0–25 / 0x1A empty |
| `0x030020B0` | RAM: current UI component index (0–25 letters, 26 DEL, 27 END) |
| `0x030020C0 + idx*56 + 44` | RAM: passcode result byte (5 accepted, 0 rejected) |

## 5. Algorithm

Pseudocode recovered from `0x08005130` and `0x08007564`:

```
submit():
    if count != 4: return
    for i in 0..3:
        ascii[i] = buffer[i] + 0x41      # 0..25 -> 'A'..'Z'
    result = validate(ascii)

validate(input):                        # 0x08005130
    table = 0x08106A3C
    for i in 0..:
        rec = *table                    # pointer to 4 ASCII bytes
        if rec == 0xFFFFFFFF: return 0
        if input[0..3] == rec[0..3]:
            script = *(table+4)
            if script == 0xFFFFFFFF: return 0
            run_script(script)          # 0x08004E84
            return 1
        table += 8
    return 0

run_script(p):                          # 0x08004E8A
    while p[0] != 30:
        opcode = p[0]; arg = p[1]; p += 2
        jump_table[opcode](arg)         # writes unlock/progress bytes
```

Key details:
* Comparison is raw bytes, no checksum, no alphabet remapping beyond `+0x41`.
* The alphabet on screen and the stored strings are both plain `A`–`Z`.
* Records are **not** fixed in a string table with a stride guess: the table
  is a pointer table with a `0xFFFFFFFF` sentinel; dumping the raw bytes and
  literal words together was necessary to avoid an off-by-one base.

## 6. Tables

All 11 accepted codes, their ROM record addresses, and decoded effect scripts
(opcode:arg pairs; op 30 terminates):

| Code | Code string @ | Script @ | Effect ops |
|---|---|---|---|
| `AGEM` | `0800EC5C` | `081067C4` | `1B:00 1C:00 17:00` |
| `MPBA` | `0800EC64` | `081069B2` | `14:00`, `02:00`–`02:13`, `01:03`–`01:14`, `16:00 03:03 05:04 07:04 09:02`, `0A:04 0C:04 0E:04 10:01 11:00`, `00:19`–`00:2D` |
| `CLSB` | `0800EC6C` | `08106952` | `14:00`, all `02:00`–`02:13`, `01:03`–`01:0B`, `16:00 03:03 05:04 07:04 09:02`, `00:1B 00:1E 00:21 00:25 00:28 00:2B`, `0E:04 0B:00 0D:00 1A:00`, `01:0F 01:10 01:11` |
| `PLCB` | `0800EC74` | `081068F2` | same core as CLSB, then `00:1A 00:1D 00:20 00:24 00:27 00:2A`, `0C:04 0B:00 0F:00 1A:00`, `01:12 01:13 01:14` |
| `TMNS` | `0800EC7C` | `08106892` | same core as CLSB, then `00:19 00:1C 00:1F 00:23 00:26 00:29`, `0A:04 0D:00 0F:00 1A:00`, `01:0C 01:0D 01:0E` |
| `LAPC` | `0800EC84` | `0810683A` | `14:00`, all `02:00`–`02:13`, `01:03`–`01:0B`, `16:00 03:03 05:04 07:04 09:02 0A:01 0C:01 0E:01 10:00 11:00 00:23 00:24 00:25` |
| `LGKG` | `0800EC8C` | `0810681C` | `14:00 02:02 02:05 02:08 02:0C 02:0F 02:12 07:04 04:01 06:01 19:00 01:09 01:0A 01:0B` |
| `GTBP` | `0800EC94` | `081067FE` | `14:00 02:01 02:04 02:07 02:0B 02:0E 02:11 05:04 04:01 08:01 19:00 01:06 01:07 01:08` |
| `NIML` | `0800EC9C` | `081067E0` | `14:00 02:00 02:03 02:06 02:0A 02:0D 02:10 03:03 06:01 08:01 19:00 01:03 01:04 01:05` |
| `NYRA` | `0800ECA4` | `081067CC` | `14:00 02:0A 00:00 00:0B 00:0C 00:0D 04:01 06:01 08:01` |
| `AEHC` | `0800ECAC` | `081067C0` | `1B:00` |

Opcode semantics (from handlers): `00/01/02` set a byte in an unlock/progress
array to 0/1/2 at `0x03001F90 + arg`; `03`–`09` set a flag to 1 in other
arrays (`0x03001FD4/…`); `0A`–`0E`, `10`, `11`, `16`, `17`, `19`, `1A`, `1B`,
`1C` target further RAM flag arrays; `14`/`15` are setup ops shared by the
"unlock" codes. The scripts match the published effects (per-driver race wins
for NIML/GTBP/LGKG, all-races/London for LAPC, car groups for CLSB/PLCB/TMNS,
global unlock for AGEM/MPBA, initiation skip for NYRA), but note that the
published effect *labels* are secondary evidence; the tables/opcodes above
are primary.

Published-code verification: all 11 literals are present at both
`0xEC5C` and `0x4C8F4`; no published code was absent. GameFAQs' shorter
5-code list is a subset; GameGenie/ChapterCheats/A2Z together cover all 11.

## 6b. Enumeration

**Space definition.** Input: 4 positions × 26 symbols (`A`–`Z`) = 456,976
strings. No checksum field, no reserved bits, no length variants (the UI
gates on `count == 4`). Accepted set: exactly 11 strings (the table at
`0x08106A3C`, terminated by `0xFFFFFFFF` at `0x08106A94`). This is a closed
lookup system: representable space 456,976, accepted space 11.

**Novel code.** §0.2 asks for an accepted code absent from every published
list. That is **impossible for this system**: the validator has no generator
or checksum, its entire accepted set is the 11-entry table, and all 11 are
already published (GameFAQs, GameGenie, ChapterCheats, A2Z, AbsolutCheats).
No 12th record, no disabled-but-accepted record, and no alias (the four bytes
are compared literally after `+0x41`; every record uses uppercase letters)
exists. The exhaustive enumeration therefore *is* the deliverable, and it is
a bounded negative: 456,976 − 11 = 456,965 strings are rejected by
construction.

**Bounds proven by rejection (in game).** `AAAA`, `AGEN` (one character off
`AGEM`), `AGEX`, and `ZZZZ` were typed on the real Passcode Entry screen and
submitted with END. Each stayed on the passcode screen, with buffer reset to
`1A 1A 1A 1A` and count 0 — i.e. validator returned 0. `AGEN`/`AGEX` prove
that near-misses in an otherwise valid code fail; `AAAA`/`ZZZZ` prove the
bulk of the space fails. A 3-character submission (`AGE`) did not validate
(count 3), proving the length gate.

**Accepted proofs.** `AGEM` and `NIML`, typed via the on-screen keyboard,
were accepted: the game advanced from Passcode Entry to `VEHICLE SELECT`,
and the RAM buffer/count were captured before submission via savestate
`gbAs` chunks (IWRAM base at raw offset `0x19000`; buffer `+0x3B38`, count
`+0x3B34`).

**Button codes / hidden menu.** The pause screen has exactly two entries
(CONTINUE, BACK TO MAIN MENU) and no hidden handler; no key-mask sequence
table was found, and `strings` shows no debug/test/secret menu text. The
widely published "Infinite Countermeasures: pause … Y, Y, X, Z, Z" is a
PlayStation-button description and does not correspond to any GBA code
surface in this ROM. The published "press Select at the start line" tip is a
gameplay trick, not a developer-intended code, and was not counted as a code.

## 7. Validation evidence

* **Observed**: emulator screenshots of every screen listed in §3;
  `AGEM`/`NIML` acceptance (Vehicle Select) and `AAAA`/`AGEN`/`AGEX`/`ZZZZ`
  rejection (Passcode Entry); savestate RAM reads of buffer/count.
* **Derived**: validator loop at `0x08005130`, 11-entry pointer table at
  `0x08106A3C` with `0xFFFFFFFF` terminator, 8-byte stride, `+0x41` ASCII
  conversion, effect script VM and its 30-opcode jump table.
* **Inferred**: semantic labels of opcodes 0x0A–0x1C as unlock/progress
  flags, based on which RAM arrays they write and on published effect
  descriptions; individual flag-bit meanings were not exhaustively mapped.
* No prompt-injection content was followed. The TCRF page returned HTTP 403
  and was not used; all web pages were treated as data.

## 8. Unknowns

* Exact semantic name of each of the ~12 RAM flag arrays written by the
  effect scripts (e.g. which bit is "London unlocked" vs "car group X").
* Whether executing an accepted code on a *completed* save changes anything
  beyond the flag arrays (tests were run on a fresh save).
* No GDB stub was available in the harness build, so the validator was not
  called as a debugger oracle over all 456,976 inputs; the closed-set proof
  rests on the recovered table structure plus sampled in-game tests.

## 9. Tooling

* `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings`, `grep -abo`.
* `arm-none-eabi-objdump -D -b binary -marm -M force-thumb --adjust-vma=0x08000000`.
* Python 3 + Capstone 5.0.7 for Thumb literal/BL scans (scanners in
  `/tmp/opencode/midnightclub/scan*.py`).
* mGBA (SDL) under `Xvfb :316` + `openbox`, `xdotool` XTEST input, `scrot`
  + ImageMagick screenshots.
* Savestate RAM reads: PNG `gbAs` chunk → `zlib.decompress` → raw state;
  IWRAM at raw offset `0x19000` (§16.13). Helper:
  `/tmp/opencode/midnightclub/ss.py`, `one_test*.py`.

No ROM or copyrighted assets are redistributed; only addresses, hashes, and
derived findings are published.
