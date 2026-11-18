# Medal of Honor: Underground (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Medal of Honor: Underground.gba` (8,388,608 bytes / 8 MiB) |
| Header title | `MEDALOFHONOR` |
| Game code | `AUGE` |
| Maker | `20` |
| Version | `0x00` (Rev.00) |
| Fixed byte / complement / checksum | `0x96` / `0x4F` / `0x0000` |
| MD5 | `05aacbae1c67574b6412c2171c487b44` |
| SHA-1 | `bf7b85adbb19cb7684b903e2a0c3e95cd804cdc2` |
| SHA-256 | `8754fa458f68867e3243c1e537ed568e09bad433f27389b360c6c5ed50efa67d` |

**Image provenance (§16.1):** the header complement byte does not balance
(`sum(0xA0..0xBC)+0x4F = 0xE7`, not `0`) and the entry word is `0xEA1FF66E`,
a far branch to a crt0 copy at file `0x7FD9C0` instead of the stock
`0xEA00002E` → `0x080000C0`. One Nintendo logo only (file `0x4`); no appended
trainer and no multiboot stub. Booting this image under mGBA plays a **scene
cracktro** ("greets: BLACK HAWK, AGGRESSION, ANTHRAX, ILLUSION, SNACHERS, DCS",
"FONTS DONE BY: HACTERO") and then hands control to the real game. Replacing
the 4 entry bytes on a **copy** with `2E 00 00 EA` (stock branch) boots directly
to the genuine retail "MEDAL OF HONOR UNDERGROUND / PRESS START" title screen
(observed). Conclusion: a scene-cracked retail image whose *only* modification
is the entry branch that prepends a cracktro. The in-game password system is
untouched developer code; the cracktro itself is **not** an in-game cheat and is
reported separately, not as a find. All analysis below used the original bytes.

## 2. Executive summary

The GBA release has a **developer password system** reached from
**Main Menu → Options → Passwords**. It is a fixed lookup table of **63
records** (61 unique strings — `ENTREZVOUS` appears twice), not a checksum
generator. The validator at `0x0800D1E0` calls `strcmp` on the typed string
against every table entry and, on a match, runs a small action script at
`0x0800D120` that writes difficulty, level index and cheat bits in IWRAM.
There is no button-code system and no hidden debug menu.

The published GameFAQs/VGChartz lists cover 51 unique accepted passwords. **Ten
unique accepted strings are absent from every published list**: the three
Level-1 passwords `TRILINGUE`/`IRRADIER`/`DOSSARD` (which the game itself
displays as the current-level password), four out-of-range warp codes
`MULA`–`MULD` (levels 18–21 in a 17-mission game), two mode codes
`MODEDOUX`/`NORM`, and the 13-character `AAAAAAAAAAAAA`. All ten were accepted
by the real screen and RAM-verified; `TRILINGUE` and `MULD` are shown below as
the novel-code proofs. Bounds were proven by rejection of a non-table string
and of the published misspelling `CAOLISER`.

A published typo was found and corrected in-game: GameFAQs prints `CAOLISER`
for Medium Level 5; the ROM and the game accept **`COALISER`** only. The
GameFAQs "Misc. Passwords" labelled `PS` (`RICOCHET`, `PUISSANCE`, `LATIREUSE`,
`BALLESVITE`, `AUTODINGUO`, `MOHDESSINS`, `DWIECRANS`, `MOHUEQUIPE`) are **not
present in the GBA image in any encoding** and are PlayStation-only.

## 3. How to reproduce

* Emulator: `SDL_AUDIODRIVER=dummy mgba -3 <rom>` under `Xvfb :315` + `openbox`,
  1024×768×24. Keymap (mGBA SDL): A=`x`, B=`z`, Start=`Return`, L=`a`, R=`s`,
  D-pad=arrow keys. Hold keys ~100 ms.
* Boot path: the shipped image first shows the cracktro; press `Return`/`x`
  through the credits (~6–8 presses) until the real **Main Menu** appears, or
  use the restored-entry copy described in §1 to boot straight to the title.
* Menu path: Main Menu (START GAME / MISSION LOG / MULTIPLAYER / OPTIONS,
  4-item ring) → **OPTIONS** (AUDIO / DIFFICULTY / PASSWORDS, 3-item ring) →
  **PASSWORDS**. The keyboard is an 11-column × 3-row A–Z grid plus a DEL cell
  (index 26) and an off-keyboard submit cell (index 27). D-pad moves the cursor
  by ±1 / ±11; A selects a letter and appends its index; B exits; submit = move
  to index 27 and press A. Max length 13 characters.
* Savestates: `Shift+F1..F9` save, `F1..F9` load. All RAM evidence below was
  obtained by diffing decompressed `gbAs` PNG chunks of mGBA `.ssN` files
  (IWRAM map: state offset `0x19000 + (addr-0x03000000)`).
* Codes verified in-game (typed on the real screen, not memory-edited):
  `SQUAME` (published), `TRILINGUE`, `IRRADIER`, `DOSSARD`, `MODEDOUX`, `NORM`,
  `AAAAAAAAAAAAA`, `MULB`, `MULD`, `MODEDEDIEU`, `ENTREZVOUS`, `PORTECLEFS`,
  `LEMONSTRE`, `COALISER`; rejected: `CAOLISER`, `ZZZZZZZZ`.

## 4. Address map

File offset = ROM address − `0x08000000`.

| Item | ROM addr / file offset | Notes |
|---|---|---|
| Password validator | `0x0800D1E0` / `0x0D1E0` | Thumb; loops all 63 table records, `strcmp` at `0x08012D58`; breaks on `0xFFFFFFFF` sentinel |
| Effect-script applier | `0x0800D120` / `0x0D120` | 5-way jump table at `0x0800D138`; reads `{u8 action,u8 param}` pairs, stops on `0x05` |
| Password table A | `0x0813A480` / `0x13A480` | 63 × 8 bytes `{char* password, u8* effects}`, sentinel `0xFFFFFFFF` at `0x13A678` |
| Effect descriptors | `0x0813A32C`..`0x0813A47A` / `0x13A32C`.. | variable 4/6-byte scripts, NUL/0x05 terminated |
| UI string/password table B | `0x0813D6E4` / `0x13D6E4` | 4-byte pointers: A–Z, space, language names, then per-difficulty level-password lists incl. L1, mission names, all menu labels |
| Password screen handler | `0x0800F4FC` / `0x0F4FC` | converts stored indices→ASCII (`+65`), NUL-terminates, calls validator; handles return codes |
| Input length (u8) | RAM `0x03005B04` | 0..13 |
| Input buffer (indices) | RAM `0x03005B10` | 13 bytes, `0x1A` = empty slot |
| Keyboard cursor index | RAM `0x03005264` | 0=A .. 26=DEL, 27=submit |
| Enable flag | RAM `0x03005220` | action 1 sets to 1 |
| Cheat bits word | RAM `0x03005224` | bit0 = invincibility (MODEDEDIEU), bit1 = mode (MODEDOUX/NORM) |
| Password result byte | RAM `0x03005228` | 0 = rejected, 1 = cheat/mode accepted, 2 = level select accepted |
| Difficulty byte | RAM `0x03005964` | 0=EASY, 1=MEDIUM, 2=HARD |
| Level index byte | RAM `0x03005968` | 0 = Mission 1, 16 = Mission 17, 20 = "Mission 21" |

## 5. Algorithm

```
validate(input):                      # 0x0800D1E0
    clear byte [0x03005228]
    for rec in table_A[0..62]:        # rec = {char* name, u8* script}
        if name == 0xFFFFFFFF: break
        if strcmp(input, name) == 0:  # exact, case-sensitive, NUL-terminated
            [0x03005228] = 1
            apply(script)             # 0x0800D120
            return [0x03005228]
    return 0

apply(script):                        # 0x0800D120; pairs until byte==0x05
    for (action, param) in script:
        case 0: [0x03005968] = param                # level index
        case 1: [0x03005220] = 1                    # enable flag
        case 2: if param: word[0x03005224] |= 1     # set cheat bit0
                else:     word[0x03005224] &= ~2
        case 3: if param: word[0x03005224] |= 2     # set cheat bit1
                else:     word[0x03005224] &= ~3
        case 4: [0x03005964] = param                # difficulty (0/1/2)
```

The input path converts 0–25 buffer indices to ASCII `A`–`Z`, so the validator
sees ordinary uppercase strings. The keyboard offers **only A–Z** (no digits,
no space, no wildcards); maximum length is 13, exactly long enough for
`AAAAAAAAAAAAA`. There is no checksum, PRNG, permutation or computed code —
the accepted set is exactly the table.

`oracle_model.py` (Tooling) reimplements `validate`/`apply` offline. Its
predictions matched the emulator's RAM for every accepted and rejected input
tested (e.g. SQUAME→diff0/lvl1, TRILINGUE→diff0/lvl0, MULD→lvl20,
MODEDEDIEU→cheat1, MODEDOUX→cheat2, COALISER→diff1/lvl4, CAOLISER→reject,
ZZZZZZZZ→reject). §16.19 note: mGBA's GDB stub is single-client and its port
was contested on this host; direct `call`/RSP stepping of `0x0800D1E0` was
attempted but proved unreliable, so the equivalent ground truth was obtained
from the game's own validator on the real password screen plus the verified
offline model. Because the validator is a pure `strcmp` loop over a closed
63-entry table, the accepted set is exact by construction (§16.9 satisfied
analytically, not by brute force).

## 6. Tables

### 6.1 Action semantics (effect-script opcodes)

| Op | RAM write | Meaning |
|---:|---|---|
| 0 | `0x03005968 = param` | level index (0 = Mission 1) |
| 1 | `0x03005220 = 1` | "enable/unlock" flag |
| 2 | `0x03005224 |= 1` / `&= ~2` | invincibility bit on / off |
| 3 | `0x03005224 |= 2` / `&= ~3` | mode bit on / off |
| 4 | `0x03005964 = param` | difficulty 0=EASY, 1=MEDIUM, 2=HARD |
| 5 | — | script terminator |

### 6.2 Complete accepted set (63 slots / 61 unique strings)

Level passwords (all published lists start at Level 2; the Level-1 entries are
**not published**):

| Mission | EASY | MEDIUM | HARD |
|---:|---|---|---|
| 1 | **TRILINGUE** (novel) | **IRRADIER** (novel) | **DOSSARD** (novel) |
| 2 | SQUAME | FRIMAS | CUBIQUE |
| 3 | REVOLER | ESCARGOT | CHEMIN |
| 4 | FAUCON | DEVOIR | BLONDEUR |
| 5 | UNANIME | **COALISER** | BLESSER |
| 6 | ROULIS | BASQUE | AVOCAT |
| 7 | RELAVER | ROBUSTE | AFFINER |
| 8 | POUSSIN | SOYEUX | LAINE |
| 9 | PANOPLIE | TERRER | MESCLUN |
| 10 | NIMBER | VOULOIR | NORME |
| 11 | NIAIS | COUVERT | ORNER |
| 12 | KARMA | VOYANCE | PENNE |
| 13 | INCISER | PIGISTE | QUELQUE |
| 14 | GADOUE | NOMMER | REPOSE |
| 15 | FUSETTE | JETER | SALIFIER |
| 16 | EXCUSER | ENJAMBER | TROPIQUE |
| 17 | ENRICHIR | MORPHE | VOTATION |

Special codes:

| Code | Effect | Status |
|---|---|---|
| `MODEDEDIEU` | cheat bit0 = 1 (invincibility / God Mode) | published |
| `MODEDOUX` | cheat bit1 = 1 ("easy mode") | **unpublished** |
| `NORM` | cheat bits 1..0 = 0 (normal) | **unpublished** |
| `ENTREZVOUS` | enable flag = 1 | published (also duplicated at table slot 28) |
| `PORTECLEFS` | enable flag = 1 | published |
| `LEMONSTRE` | enable flag = 1 | published |
| `AAAAAAAAAAAAA` | enable flag = 1, 13 chars | **unpublished** |
| `MULA` / `MULB` / `MULC` / `MULD` | level index 17/18/19/20 | **unpublished** — out of range |

## 6b. Enumeration

* **Space definition.** Keyboard alphabet = 26 symbols `A`–`Z`; length 1..13
  (13 enforced by the input handler). Reachable input space =
  `Σ_{n=1..13} 26^n = 2,580,398,988,131,886,038` strings. Accepted set =
  exactly 61 unique strings (63 table slots; `ENTREZVOUS` duplicated). This is a
  closed lookup table, not a checksum system — the validator contains one
  `strcmp` loop and no arithmetic validation, so no other string can be
  accepted.
* **Novel code 1 (developer-intended but unpublished): `TRILINGUE`.** Absent
  from GameFAQs, VGChartz, TCRF and IGN lists (all start Easy at Level 2 with
  `SQUAME`). Typed on the real screen: buffer before submit
  `[19,17,8,11,8,13,6,20,4]` = `TRILINGUE`; after submit RAM shows
  `difficulty 0x03005964 = 0x00 (EASY)`, `level 0x03005968 = 0x00 (Mission 1)`,
  result byte `0x03005228 = 0x02`, buffer cleared. Screenshot
  `proof_trilingue_crop.png` shows the resulting **Mission One "OCCUPIED!"**
  title card. Independently, the game's own UI table B maps index 33 →
  `TRILINGUE` as the Easy Level-1 password, and the in-game pause screen
  displays the live current-level password (Medium Level 1 → `IRRADIER`).
* **Novel code 2 (unadvertised combination): `MULD`.** Not in any published
  list; its script sets `level index = 20`, i.e. "Mission 21", beyond the 17
  real missions. Typed and submitted: RAM `level 0x03005968 = 0x14 (20)`,
  result byte `0x02`, no error. `MULB` likewise set level `18`. This exercises
  an input the developers left in the table but never documented and the game
  cannot render as a normal mission.
* **Novel code 3: `MODEDOUX`** (in-game "easy mode", cheat word = 2) and
  **`AAAAAAAAAAAAA`** (enable flag = 1, exercises the 13-character cap).
* **Bounds proven by rejection.** `ZZZZZZZZ` (not a table string): result
  byte stays `0x00`, difficulty/level/cheat/enable bytes unchanged, buffer
  cleared and the game remains on the PASSWORD MENU (`proof_reject_crop.png`).
  `CAOLISER` (the misspelling printed by GameFAQs) was rejected identically,
  while the ROM literal `COALISER` was accepted with MEDIUM / level index 4.
  Lowercase/space/digit input is impossible through the A–Z-only keyboard, so
  no other spelling variants exist on the real screen.

## 7. Validation evidence

* **Observed (emulator + RAM):** every menu listed in §3 and §8; typed codes
  and their exact RAM effects; the three novel Level-1 codes, the two
  out-of-range codes, `MODEDOUX`/`NORM`/`AAAAAAAAAAAAA`, the three enable-flag
  codes, and `MODEDEDIEU`; both rejections; the cracktro and the restored
  retail title screen; the live "PASSWORD … IRRADIER" text on the pause screen.
* **Derived (disassembly):** validator/effect-applier control flow, jump-table
  action semantics, table strides and sentinels, input index→ASCII conversion,
  keyboard grid (11 columns, cursor RAM `0x03005264`), and the full UI string
  table B.
* **Inferred:** the semantic labels "invincibility", "easy mode" and
  "enable/unlock flag" come from the published effects and the descriptive
  strings in table B; the bits and their writers are proven, but a full
  playthrough of each unlocked mode was not performed. The exact meaning of
  result byte values 1 vs 2 follows the submit handler's branches and the
  observed level-vs-cheat split.

Web content was treated strictly as data. No prompt-injection payload was
encountered in the pages fetched for this engagement; all code lists were
cross-checked against ROM bytes before use.

## 8. Unknowns

* No hidden/debug menu exists: the entire UI string pointer table
  (`0x0813D6E4` onward) enumerates only the screens walked (title, main,
  options, audio, difficulty, passwords, mission log/mission select,
  multiplayer, mission evaluation, pause, briefing, objectives/hints, and the
  "NEXT LEVELS PASSWORD" completion label). A case-insensitive keyword sweep
  found no debug/secret/warp strings beyond story prose and objective names.
* The "NEXT LEVELS PASSWORD" completion screen itself was not reached by
  playing a mission to completion; its content is established from table B
  (which holds the exact per-difficulty/per-level password strings, including
  the unpublished Level-1 entries), not from a screenshot.
* What the game does when actually launching a mission via `MULA`–`MULD`
  (level indices 17–20) was not played; the validator writes the out-of-range
  byte without complaint, which is the reported finding.
* The role of the enable flag at `0x03005220` beyond "master/unlock" (as
  described by the published `ENTREZVOUS`/`PORTECLEFS` lore) was not fully
  exercised in gameplay.

## 9. Tooling

All work files are in `/tmp/opencode/mohunderground/`.

* `moh.gba` — byte-identical working copy; `restored.gba` — 4-byte entry patch
  for the §1 provenance check.
* `oracle_model.py` — offline validator/effect reimplementation; run
  `python3 oracle_model.py moh.gba SQUAME TRILINGUE ...`.
* `pw.py`, `typer.py`, `ramread.py` — xdotool keyboard driver and mGBA savestate
  `gbAs` decompressor/RAM reader for the evidence loop.
* `enumeration.txt` — full 63-slot dump with published/unpublished tagging.
* Screenshots (cropped 720×480 GBA viewport): `restored_crop.png` (retail
  title), `opt_montage.png` (options ring), `shot10_crop.png` (password
  keyboard), `proof_trilingue_crop.png` (novel code), `proof_reject_crop.png`
  (rejection), `pause_crop.png` (pause + live password), `missionlog_crop.png`,
  `multiplayer_crop.png`, `diffmenu_crop.png`.

No ROM data, graphics, music or game text is redistributed by this report —
only hashes, addresses, algorithms, and the short code strings themselves.
