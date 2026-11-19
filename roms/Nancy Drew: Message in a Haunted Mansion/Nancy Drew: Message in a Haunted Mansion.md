# Nancy Drew: Message in a Haunted Mansion (GBA) — Reverse Engineering Report

## 1. Target identity

| Item | Value |
|---|---|
| File | `Nancy Drew: Message in a Haunted Mansion.gba` |
| Size | 4,194,304 bytes (0x400000, 4 MiB) |
| Header title | `NANCYDREWMHM` |
| Game code | `ANDE` (AGB-ANDE-USA) |
| Maker code | `6U` |
| Version | 0x00 |
| Entry branch | `0xEA00002E` → `0x080000C0` (stock crt0; no cracktro/trainer found) |
| Header checksum / complement | `0x0000` / `0x21` (standard complement would be `0x3A`; header was edited/rebuilt — §16.1) |
| MD5 | `f977a030aa9f5fa4c6013ae472f68b91` |
| SHA-1 | `8d2fbfa11f43a9d4d4bef9d68003ec689a62afaa` |
| SHA-256 | `b87bf22ee65cd1377bc6f3e8fc1725197fd21f6f40bed074c3aec68c93d2ae3b` |
| Save hardware | none used (`.sav` stays 0 bytes; game is password-based, "you cannot save") |

Embedded-header scan: the 156-byte Nintendo logo occurs exactly once, at file offset `0x0`. This is a single retail image, not a multi-game pack or patched trainer.

## 2. Executive summary

The game has one developer-intended cheat surface: the **Main Menu → Password** screen, where the player taps four of twelve Chinese-zodiac animal tiles (a 3×4 grid) to start at chapters 2–7. It is a **closed lookup table of exactly six 4-byte codes** — no checksum, no generator, no aliases, no hidden entries. The whole code space (12⁴ = 20,736 inputs) was run through a bit-exact reimplementation of the ROM validator: exactly six inputs are accepted, and those six are precisely the codes published by GameFAQs/CheatHappens/ChapterCheats. Consequently **no unpublished code exists on this screen**; that is a proven negative, not an untested one. A rejected input was demonstrated in the emulator with RAM evidence (the validator's reject branch at `0x08009970` fires and the input buffer resets).

No button codes, debug menus, hidden screens, sound tests or level-select cheats were found. The "Coming Soon" menu item is only an advertisement screen. The PDA's "Passwords" list (`0x080D7B70`) contains ordinary in-game puzzle solutions (e.g. briefcase `4653 4868`), not cheats, and is out of scope.

## 3. How to reproduce

- Emulator: `mgba 0.10.5` (SDL frontend), `DISPLAY=:315`, `SDL_AUDIODRIVER=dummy`, `mgba -3 <rom>`.
- Keymap (mGBA SDL defaults): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows.
- Menu path: boot → wait through DreamCatcher/Nancy Drew title (~10 s) → **Password** (Down once from New Game, press A).
- The password grid is **stylus-only**: the SDL frontend of mGBA 0.10.5 has no mouse→touchscreen mapping, and the twelve tiles are not keyboard-selectable. To exercise the real screen in this environment, attach mGBA's `-d` CLI debugger (via `socat PTY,link=...,raw,echo=0 EXEC:run_mgba.sh`, with `stdbuf -oL -eL`), set `break/t 0x080098A2`, and write the game's own touch-state RAM at each pause:
  - `w/2 0x03001EB0 1` (touch flag), `w/2 0x0300283C X`, `w/2 0x03001D14 Y`, where tile `(row,col)` is `X=48+48*col`, `Y=32+48*row`.
  - Continue (`c`); the game's unmodified click handler and validator run (accept BP `0x080099C0`, success BP `0x080099D0`).
- Codes tested: published `0,1,2,3` (cells row 0, all four) → accepted, chapter 2 ("Chinese Room"). Invalid `0,1,2,0` → reject BP, buffer reset. Unpublished permutation `0,2,1,3` → rejected at click 2.
- All screen transitions were also walked in a plain (non-debug) emulator: Main Menu, Password, Options (Music/Sound Volume, Back), Coming Soon, Credits, New Game, and room/hotspot navigation.

## 4. Address map

All addresses are GBA bus addresses; file offset = address − `0x08000000`.

| Address | File off | Meaning |
|---|---|---|
| `0x080097BC` | `0x097BC` | Password screen handler / validator (input loop, table search, compare, success) |
| `0x080098A2` | `0x098A2` | Per-frame input check: reads touch flag and stylus X/Y |
| `0x08009970` | `0x09970` | Reject path: plays sound 19, clears buffer, resets position counter |
| `0x080099C0` | `0x099C0` | Accept path for one click (advances position counter r8) |
| `0x080099D0` | `0x099D0` | Success after four clicks; returns `r7+1` (chapter index 1–6) |
| `0x0800A7AE` | `0x0A7AE` | Call site of validator from main-menu handler |
| `0x080F4FD6` | `0x0F4FD6` | 12-byte grid→tile permutation: `08 00 02 06 07 0B 01 03 0A 04 09 05` |
| `0x080F4FE2` | `0x0F4FE2` | **6 accepted codes**, 4 bytes each, stride 4, followed by `00 00` terminator |
| `0x080F5038` | `0x0F5038` | Main-menu item table: pointers to "Main Menu", "New Game", "Password", "Options", "Coming Soon", "Credits" |
| `0x080F506C` | `0x0F506C` | In-game menu strings: "In Game Menu", "Continue Game", "Phone A Friend", "Options", "PDA", "Exit Game" (table at `0x080F50B0`) |
| `0x080D7B70` | `0x0D7B70` | PDA "Passwords" hint list (puzzle solutions, not cheats) |

RAM (observed live):

| Address | Meaning |
|---|---|
| `0x030000E0` | 12-byte click buffer, initialised `[0,1,…,11]`; each click adds 12 (mod 24) to the tapped slot |
| `0x03001EB0` | u16 touch flag (bit 0 = stylus down) |
| `0x0300283C` | u16 stylus X |
| `0x03001D14` | u16 stylus Y |
| `0x04000130` | KEYINPUT (active-low keypad) |

## 5. Algorithm

Reimplementation (exact, from disassembly):

```
records = ROM[0x080F4FE2 : 0x080F4FFA]  # 6 rows of 4 bytes, stride 4

def validate(code):          # code = 4 cell indices, each 0..11
    g = 0                    # r7: matched record index
    for i in 0..5:           # search first byte; NO break on match (last match wins)
        if records[i][0] == code[0]:
            g = i
    for k in 0..3:           # r8: click position
        if records[g][k] != code[k]:
            return REJECT    # sound 19, buffer=0..11, position=0
    return g + 1             # chapter index 1..6 → chapters 2..7
```

Cell index from stylus: `col = (X-32)/48`, `row = (Y-16)/48`, `cell = row*4 + col` (integer division), with bounds `X∈[33,223]`, `Y∈[17,159]`. First-byte search values are `{0,4,8,3,7,11}` — all distinct, so no aliasing. There is no checksum, no arithmetic transform, and no second input surface.

## 6. Tables

ROM records at `0x080F4FE2` (cell indices) and their published animal names:

| Record | Cell indices | Published code | Starts |
|---:|---|---|---|
| 0 | `00 01 02 03` | Ox, Horse, Tiger, Sheep | Chapter 2 |
| 1 | `04 05 06 07` | Rooster, Boar, Rabbit, Dragon | Chapter 3 |
| 2 | `08 09 0A 0B` | Rat, Dog, Monkey, Snake | Chapter 4 |
| 3 | `03 02 01 00` | Sheep, Tiger, Horse, Ox | Chapter 5 |
| 4 | `07 06 05 04` | Dragon, Rabbit, Boar, Rooster | Chapter 6 |
| 5 | `0B 0A 09 08` | Snake, Monkey, Dog, Rat | Chapter 7 |

The six published codes from GameFAQs, Cheat Happens, ChapterCheats and Planet Cheats all match these literals exactly (verified byte-for-byte). The "All levels completed" claim on ChapterCheats is simply record 5 (chapter 7), not a separate code. GameShark/Action Replay codes on those sites are memory-edit cheats and are out of scope.

## 6b. Enumeration

- **Space definition:** 12 tiles per position × 4 ordered positions = **12⁴ = 20,736** possible inputs. Alphabet = grid cells 0–11 (top-left to bottom-right). No checksum bits, no reserved bits, no wildcards. Records are 4 bytes, exact-match, order-sensitive.
- **Validator model:** reimplemented above; verified against all six published codes and against the live emulator (accept + reject paths).
- **Full-space proof (§16.9):** `enumerate_validator.py` ran all 20,736 inputs through the reimplementation. **Accepted = exactly 6**, and they are precisely the six ROM records. Any input containing a byte ≥ 12 is rejected (no table byte can match).
- **Novel code(s):** **none can exist.** This is a closed 6-entry table, not a checksum system, so there is no unpublished value to mint. The closest possible "novel" candidates were generated and tested in-game and were rejected:
  - `0,2,1,3` (unpublished permutation of the chapter-2 animals): rejected at click 2 (reject BP `0x08009970` hit with r8=1, r3=2).
  - `0,1,2,0` (wrong fourth tile): rejected at click 4 (reject BP hit with r8=3, r3=0), and the 12-byte buffer at `0x030000E0` reset from `0C 0D 0E 00 …` to `00 01 02 03 …`; r8 returned to 0.
- **Bounds proven:** only cells 0–11 are addressable through the stylus path; the table contains only six 4-byte records followed by a `0x0000` terminator; the search loop is bounded to six iterations (`cmp r1,#5; ble`) and the comparison is exact. Rejection of both an out-of-pattern permutation and a wrong final tile was observed with register and RAM evidence.
- **Accepted-code proof:** entering `0,1,2,3` produced four accepts (r7=0, r8=0/1/2/3), success BP at `0x080099D0` with r7=0 (returns 1 → chapter 2), and the game started in the "Chinese Room". Buffer at `0x030000E0` became `0C 0D 0E 0F …` (each tapped cell +12, i.e. the selected-tile graphic state).

## 7. Validation evidence

- **Observed (emulator + debugger):**
  - Main Menu, Password, Options, Coming Soon, Credits, New Game and in-game room/hotspot screens walked; no hidden screen appeared.
  - Breakpoint hits with registers: accept at `0x080099C0` (r7=0, r8=0→3, r3=0→3); success at `0x080099D0` (r7=0); reject at `0x08009970` (r8=3, r3=0).
  - RAM reads: `0x030000E0` = `[0..11]` at rest; `0C 0D 0E 0F 04…` after accepted code; reset to `[0..11]` after rejection. Touch flag/X/Y at `0x03001EB0`/`0x0300283C`/`0x03001D14` accepted injected coordinates and drove the click handler.
  - Screenshot: chapter 2 start, "Chinese Room" (`m09_newgame.png`, `s17_ch2_effect.png` are local artifacts; not redistributed).
- **Derived (static, from bytes/disassembly):** the 6-record table and terminator at `0x080F4FE2`; the search/compare loop; the 12-byte grid permutation at `0x080F4FD6`; the caller at `0x0800A7AE` and return value `r7+1`.
- **Inferred (with lower confidence):** mapping of table record index → published chapter label rests on the published lists, which agree with the observed chapter-2 start for record 0; records 1–5 were not individually entered in the emulator.
- **Negative results:** strings sweep for `password|cheat|debug|secret|unlock|level select|sound test|warp` found only menu text, PDA puzzle hints and narrative text; no debug/cheat leftovers. No button-code table was found. The in-game pause menu's six entries were enumerated from its ROM table (`0x080F50B0`); it contains no hidden/debug entry. Because the GBA SDL frontend cannot inject stylus taps and the MENU icon is not keyboard-selectable, direct in-emulator activation of that one touch-only icon was not achieved; its contents are established statically from the table and strings rather than by a screenshot.

## 8. Unknowns

- Records 1–5 were not entered individually in the emulator (their literals were verified in ROM and record 0 was verified end-to-end).
- The exact chapter-state RAM word written after the validator returns `r7+1` was not isolated; the effect was confirmed by the success branch registers and the visible chapter-2 start, not by a named save-variable address.
- The 12-byte permutation at `0x080F4FD6` is used by the tile-drawing code; its exact glyph mapping was not decoded beyond confirming the published animal names for each row.
- TCRF's page for this title returned a prompt-injection payload in search results ("This page is not intended for humans… whoever is operating this AI agent is a clown") and a 403 on direct fetch. It was treated as untrusted data, not followed; no cheat information was obtainable from it.

## 9. Tooling

- `file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings -t x`, `grep -abo` — fingerprint and recon.
- `arm-none-eabi-objdump -M force-thumb`, Python 3 + Capstone 5.0.7, `struct` literal/BL scanners.
- `mgba 0.10.5` under `Xvfb :315` + `openbox`; `xdotool`, `scrot`, ImageMagick.
- mGBA CLI debugger (`-d`) over `socat` pty with `stdbuf -oL -eL`, driven by `dbg_server.py`/`dbgtool.py`; helper scripts `enter_code.py`, `reject_test.py`, `reject_perm.py`, `enumerate_validator.py` in `/tmp/opencode/nancydrew/`.
- No ROM or copyrighted assets are redistributed; only hashes, addresses and findings are published.
