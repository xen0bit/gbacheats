# Hot Wheels: Stunt Track Challenge (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Hot Wheels: Stunt Track Challenge.gba` |
| Size | 8,388,608 bytes (0x800000, 8 MiB) |
| Header title | `HOTWHEELSSTC` |
| Game code / maker | `BHEE` / `78` |
| Version | 0 (`0xBC = 0x00`); complement `0x31`, checksum field `0x0000` |
| Entry word | `0xEA00002E` → branch to `0x080000C0` (stock crt0) |
| MD5 | `c328c11773ab3075916f6d2c0735652a` |
| SHA-1 | `3a950fa7f2979ac8b1e2e2eb628267b3146f1da1` |
| SHA-256 | `a02b15cd1734e921e5c66bd4c4962583d1c143e87aedaf391dc8357d5ef9b485` |

Phase 0: one embedded GBA header (Nintendo-logo scan at file offset 0 only). The first
4 KiB are the standard crt0 (`mov r0,#0; ldr r1,=0x03007f00; ...` at 0xC0), so this is
the retail image — no cracktro, no appended trainer. No patch/trainer was applied to
the analyzed copy.

## 2. Executive summary

The game has one in-game cheat surface: a **fixed 52-entry password table** reached from
**OPTIONS → PASSWORD**. The on-screen keypad is the 21 consonants
`BCDFGHJKLMNPQRSTVWXYZ`; a code is exactly 8 characters, terminated by the DONE cell.

The validator (`0x0813A524`) is a plain 8-byte compare over four blocks of records —
it is **not** an algorithmic/checksum generator. The complete accepted set is 52 strings
(30 Game Show, 9 Stunt School, 1 special Champions League race-1, 12 Champions League).
Accepted codes set three IWRAM globals (`0x03002410`, `0x030011F5`, `0x030011F6`) and
the caller at `0x0813A678` unlocks the corresponding race/lesson/cutscene.

Two widely-published codes are **typos** and are rejected by the ROM:
`LLSCSKGQ` (should be `LLSCSFGQ`) and `LLSCFQJC` (should be `LLSCFQJL`). Both corrected
forms were generated from the ROM table, entered, and RAM-verified in the emulator.

A Drome Racers 6-character cheat validator (`0x08121684`, codes `IAMCAR`, `LOGRAV`,
`CUPIUP`, `ALL4ME`, `BIGUNS`, `BIFFIN` at `0x0817DFB0`) is present but is **dead code**:
it has zero BL callers and zero pointer references, and its codes contain vowels that
the 21-symbol keypad cannot produce. It is not reachable in-game. No button-code gate
or hidden debug screen was found; the debug-menu-looking text in `0x793630`, `0x793F3C`,
`0x798B9C`, `0x799BD8` is unreferenced leftover text (TCRF "Unused Text"), consistent
with the guide's "dead code" category (§16.3).

**No unpublished code exists for this system.** The validator is a closed 52-string
lookup, every one of those 52 strings appears in at least one published list, and the
full-space search (below) confirms there is no algorithmic extension. This is a bounded
negative, not an untested one.

## 3. How to reproduce

- Emulator: mGBA SDL (`mgba -3`), `SDL_AUDIODRIVER=dummy`, Xvfb `:318`, Openbox window manager.
- Keymap (mGBA SDL defaults): A=`x`, B=`z`, L=`a`, R=`s`, START=`Return`, SELECT=`BackSpace`, D-pad = arrow keys. Hold keys ~150–200 ms; shorter taps are dropped by this menu system.
- Menu path from power-on: title/main menu → **OPTIONS** (5× Down from GAME SHOW; CHAMPIONS LEAGUE is greyed/skipped while locked) → **PASSWORD**.
- Keypad grid: row 0 `B C D F G H J`, row 1 `K L M N P Q R`, row 2 `S T V W X Y Z`, command row `DELETE / QUIT / DONE`. Move with D-pad, press A per character. After the 8th character, navigate to DONE and press A. Valid codes advance to a cutscene/menu with a RAM flag change; invalid codes are silently ignored (stay on the password screen, no RAM change).
- Verification method: mGBA `.ss1` savestates are PNG files with a zlib-compressed `gbAs` chunk. `zlib.decompress` yields a 397,312-byte (0x61000) raw state; IWRAM is at raw `0x19000` (GBA `0x03000000`), EWRAM at `0x21000` (GBA `0x02000000`). I patched the two input-buffer copies at GBA `0x03003D5C` / `0x03003DFC` (raw `0x1CD5C` / `0x1CDFC`) to set codes exactly, then submitted with DONE.
- Published pages consulted (archived via web.archive.org because GameFAQs/TCRF return 403):
  - GameFAQs cheats: `https://gamefaqs.gamespot.com/gba/920566-hot-wheels-stunt-track-challenge/cheats`
  - GameFAQs board "EVERY Password for the game...": `.../boards/920566-hot-wheels-stunt-track-challenge/62356812`
  - GameFAQs guide (SpeedDeoxys) `faqs/79675/unlocks-and-codes`
  - TCRF `https://tcrf.net/Hot_Wheels:_Stunt_Track_Challenge_(Game_Boy_Advance)` and `/Unused_Text`
  No prompt-injection payload was found in the fetched pages; all fetched text was treated as data.

## 4. Address map

| Address (ROM/file) | Meaning |
|---|---|
| `0x08000000` / `0x000000` | Header; entry branch to 0xC0 |
| `0x0813A504` | 8-byte password comparator (`state+0x48` vs candidate string) |
| `0x0813A524` | Main password validator: 4 table walks, returns 0/1/3 |
| `0x0813A678` | Caller: maps validator return to unlocks/cutscenes/save writes |
| `0x0817F804` | Game Show table, 30 records × 12 B: `{char* pwd, u32 area, u32 event}` |
| `0x0817F978` | Stunt School table, 9 records × 12 B: `{char* pwd, u32 0, u32 level}` |
| `0x0817F9F0` | Inline string `CLJJBGLQ` (special case in validator) |
| `0x0817F9FC` | Champions League table, 12 records × 12 B: `{char* pwd, u32 race, u32 0}` |
| `0x0879A958`–`0x0879ABB0` | Plaintext password strings, 8 chars + 4 pad, 12-B stride (52 entries) |
| `0x08121664` | Leftover Drome Racers 6-byte comparator (dead) |
| `0x08121684` | Leftover Drome Racers cheat dispatcher (dead) |
| `0x0817DFB0`–`0x0817DFD8` | Leftover Drome Racers codes `CUPIUP`, `ALL4ME`, `BIFFIN`, `BIGUNS`, `LOGRAV`, `IAMCAR` |
| `0x0879A930` | `INCORRECT` string (password/other UI) |
| `0x08793630`, `0x08793654`, `0x08793F3C`, `0x0879401C` | Debug-menu leftover labels (`TEST TRACK`, `Champions League Intro`, `Game Show Intro`, `All Sunt Tests Completed Outro`, `Challenge Brifing`, `Race Intro`) — no xref |
| `0x03003D5C`, `0x03003DFC` (RAM) | Password input buffer copies (IWRAM) |
| `0x03002410` (RAM) | Validator global A (mode/area/level) |
| `0x030011F5`, `0x030011F6` (RAM) | Validator globals B/C (race or area+event) |

File offset ↔ ROM address = `0x08000000 + file_offset` (single-header image).

## 5. Algorithm

Validator pseudocode (Thumb, `0x0813A524`):

```text
if [state+0x108] != 0: return 0          # already-consumed guard
input = *(state+0x48)                    # 8-byte input buffer
for rec in GameShowTable[0..29]:        # 0x0817F804, 12-byte stride
    if input[0:8] == rec.pwd[0:8]:
        [0x03002410] = rec.area          # u8
        [0x030011F5] = rec.event         # u8
        return 1
for rec in StuntSchoolTable[0..8]:      # 0x0817F978
    if input == rec.pwd:
        [0x03002410] = rec.level
        return 3
if input == "CLJJBGLQ":                 # 0x0817F9F0
    [0x03002410] = 8; [0x030011F5] = 0; return 3
for rec in ChampionsLeagueTable[0..11]: # 0x0817F9FC
    if input == rec.pwd:
        [0x030011F5] = rec.race; return 3
return 0
```

`0x0813A504` compares bytes 0..7 (loop bound `cmp r1,#7; ble`), i.e. exact 8-byte
equality — no case folding, no wildcard, no checksum, no tile-index aliasing.

## 6. Tables

Alphabet (keypad order, 21 symbols): `BCDFGHJKLMNPQRSTVWXYZ`.
Code length: 8. Space: `21^8 = 37,822,859,361` strings; only 52 are accepted.

Published code families (all 52 verified present in the ROM at `0x79A958`+):

- Game Show (30): `HWGSPSBB`, `JJCRTVBZ`, `JJSCFQCX`, `JJSCRBDV`, `JJCRDBFS`,
  `SLSCSFGQ`, `SLSCFQHN`, `SLCRBNJL`, `SLSCTBKJ`, `SLCRNHLG`,
  `BBSCFQMD`, `BBCRWCNB`, `BBSCCCPY`, `BBSCFSQW`, `BBCRMDRT`,
  `TKSCTBSR`, `TKSCSFTP`, `TKCRJSVM`, `TKSCFQWK`, `TKCRGFXH`,
  `ZGSCRBYF`, `ZGCRSSZC`, `ZGSCFSBZ`, `ZGSCFQCX`, `ZGCRSMDV`,
  `LLSCTBFS`, `LLSCSFGQ`, `LLCRFMHN`, `LLSCFQJL`, `LLCRVBKJ`.
- Stunt School (9): `SSLTRQVZ`, `SSLRSPTY`, `SSLFTNSX`, `SSLVVMRW`, `SSLXWLQV`,
  `SSLSXKPT`, `SSLGYJNS`, `SSLNZHMR`, `SSLTBGLQ`.
- Champions League (12 + 1): `CLJJBGLQ` (inline), `CLJJCFKP`, `CLSLDDJN`,
  `CLSLFCHM`, `CLBBGBGL`, `CLBBHZFK`, `CLTKJYDJ`, `CLTKKXCH`, `CLZGLWBG`,
  `CLZGMVZF`, `CLLLNTYD`, `CLLLPSXC`, `CLFNQRWB`.

Flag/global map (from validator disassembly + RAM diffs):

| Code family | Return | RAM effect |
|---|---|---|
| Game Show | 1 | `0x03002410` = area (0..5), `0x030011F5` = event (0..4) |
| Stunt School | 3 | `0x03002410` = level index; unlock bits in EWRAM `0x0300xxxx` |
| Champions League | 3 | `0x030011F5` = race number (1..13) |

Published-code verification results (literal search + emulator entry):

| Published code | In ROM? | Emulator result |
|---|---|---|
| `CLBBHZFK` | yes (`0x79AB5C`) | accepted; CL intro cutscene; RAM `0x030011F5` 0x00→0x06 |
| `LLSCFQJL` | yes (`0x79AAA8`) | accepted; RAM `0x030011F5=0x05`, `0x030011F6=0x03` |
| `LLSCSFGQ` | yes (`0x79AA90`) | accepted; RAM `0x030011F5=0x05`, `0x030011F6=0x01` |
| `JJCRTVBZ` | yes (`0x79A964`) | accepted; RAM `0x030011F5=0x00`, `0x030011F6=0x01` |
| `SSLNZHMR` | yes (`0x79AB14`) | accepted; Stunt School champion outro; RAM `0x03002410=0x07` |
| `LLSCSKGQ` | **no** | rejected (no RAM change, stays on password screen) |
| `LLSCFQJC` | **no** | rejected (no RAM change, stays on password screen) |
| `HWGSPSBB` | yes (`0x79A958`) | present; TCRF notes it is functionally useless (first-stage unlock) |
| `SMASHMOUTH` (2-in-1 / PC code) | no | unrelated SKU; not applicable |
| Drome Racers 6-letter codes | yes, but dead | unreachable (validator has no callers; vowels not on keypad) |

## 6b. Enumeration

**Space definition.** 8 symbols from a 21-character consonant alphabet. The validator
does not compute anything from the symbols; it compares the 8 bytes against a fixed
table. Therefore the representable space is `21^8 = 37,822,859,361` strings and the
accepted set is exactly the 52 table entries (space definition, §0.2).

**Whole-space proof.** Because the accept path is an exact 8-byte compare against four
contiguous record tables, the accepted language is the union of those 52 literal
strings — there is no hidden algorithmic branch. An offline scan of the entire ROM for
8-consonant strings in the code/text regions (`0x790000–0x7A0000`, `0x17F000–0x180000`)
found **exactly 52** code-like strings (plus one compressed-data false positive
`DDDDDDDD`), matching the four record groups. A pointer scan found only the four table
bases referenced by `0x0813A524`; there is no fifth table and no generator function.

**Novel-code result — bounded negative.** I could not mint a code absent from every
published list, because none exists. The union of the GameFAQs cheats page (51 codes),
the GameFAQs "direct copy from the ROM" board post (51 codes), the SpeedDeoxys FAQ, and
TCRF covers all 52 ROM entries. The two corrections I derived from the ROM table —
`LLSCSFGQ` and `LLSCFQJL` — are absent from the *primary* GameFAQs cheats page (which
prints the rejected typos `LLSCSKGQ` / `LLSCFQJC`) but do appear in the GameFAQs board
post and the SpeedDeoxys FAQ, so they are not truly unpublished. Both were nevertheless
generated from the ROM table, entered on the real password screen, and RAM-verified;
this is the strongest novel-code evidence this closed system permits.

**Bounds proven by rejection.** Three syntactically valid 8-consonant strings that are
not table entries were submitted on the real screen: `BBBBBBBB`, `LLSCSKGQ`, and
`LLSCFQJC`. In every case the game stayed on the password screen and all three globals
(`0x03002410`, `0x030011F5`, `0x030011F6`) remained `0x00`. This proves the boundary:
valid alphabet + correct length is necessary but not sufficient; membership in the
52-string table is required.

## 7. Validation evidence

- **Derived (disassembly):** validator table walks, exact 8-byte comparator, return values, global writes, table addresses. Verified with `objdump -M force-thumb` against raw bytes.
- **Observed (emulator + RAM):** all 52 codes present as literals; 5 accepted codes produced screenshot states and RAM deltas; 3 rejected strings produced no RAM delta. RAM was read from decompressed mGBA `gbAs` savestate chunks, not inferred from screenshots alone.
- **Observed (screens walked with RAM snapshots):** title/main menu (`0x03002410=0`, `0x030011F5=0`), OPTIONS, PASSWORD, SETTINGS, CREDITS, Game Show episode select (Ep1 available, Ep2 shows `LOCKED`), Stunt School `SELECT LESSON` (Basic Driving visible), ARCADE, MULTIPLAYER, Champions League (greyed/locked). Pause/HUD screens exist as text (`PAUSED`, `Resume`, `Quit Race`, `Quit To Menu` at `0x7944FC`+) and were observed in the string bank; a full race was not played for this report, so the in-race pause state is labeled **inferred** rather than observed.
- **Inferred:** exact semantic labels of some unlock bits in `0x0300xxxx`; the guide's rule that label prose is not ground truth was followed — RAM values are reported instead.

## 8. Unknowns

- Whether the leftover debug-menu text corresponds to a reachable screen behind a gate we did not find. The code that would display it (`0x08121684` dispatcher and screen-registration thunks `0x081217EC`/`0x081217FC`) has no callers or pointers, so within the searched space the answer is "no reachable screen"; an unexamined launch-time RAM flag remains theoretically possible but no writer/gate was found.
- Whether `SSLNZHMR` sets `0x03002410=0x07` as a level index (published label "Level 9") or as a completion flag; the caller was not fully decompiled past the unlock writes.
- The in-race pause screen was not entered (see §7).
- `INCORRECT` (`0x0879A930`) is present in the UI text bank but was not observed on rejection — rejection is silent on this screen.

## 9. Tooling

- `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings`, `grep` for Phase 0/1.
- `arm-none-eabi-objdump -D -b binary -marm -M force-thumb --adjust-vma=0x08000000` and Capstone 5.0.7 for disassembly/scans.
- Python scripts in `/tmp/hwstunt/`: `scan_refs.py` (literal pointer scan), `pw.py` (keypad navigation), `ss.py` / `patchss.py` (savestate parse/patch), `submit.py` (code submission + RAM read), `walk.py` (screen walk), `dbgsrv.py`/`dbg.py` (attempted `-d` PTY debugger).
- mGBA SDL under `Xvfb :318` + Openbox; `xdotool` with explicit keydown/keyup holds; `import`/`convert` for screenshots, `tesseract` for OCR.
- Web: `websearch` + `webfetch` via `web.archive.org` snapshots (direct GameFAQs/TCRF fetches are 403).

No ROM bytes or copyrighted assets are redistributed in this report; only addresses, hashes, and the author-generated analysis scripts are documented.
