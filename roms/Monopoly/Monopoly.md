# Monopoly (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Monopoly/Monopoly.gba` |
| Size | 4,194,304 bytes (`0x400000`), 4 MiB |
| Header title | `MONOPOLY` |
| Game code | `BUME` |
| Maker | `20` |
| Version | `0x00` (Rev.00) |
| Entry branch | `0xEA00002E` (stock ARM branch to crt0) |
| Fixed `0x96` | present; Nintendo logo intact; complement check `0x49` valid |
| Header checksum | `0x0000` (normal rebuilt-header artifact) |
| MD5 | `ce55f087d1ed4ab12a5bad411dae1113` |
| SHA-1 | `81314b9ffe3c4da5060de098ee1394ecef6fe9ad` |
| SHA-256 | `3a8e53c4076734e6d7e0654d6362fffeef0a0792114aca9eb7701beee5d3c7b0` |
| Identified SKU | GameFAQs `gba/926475` — Destination Software / DSI Games, 2004; Fullfat engine; `file(1)` reports `"MONOPOLY" (BUME20, Rev.00)` |

Embedded-header scan: one Nintendo-logo hit at file `0x0` only. No second image, no appended trainer, no scene cracktro patch, no GameShark/CodeBreaker host. The ROM is the retail image.

## 2. Executive summary

**No developer-intended cheat system exists in this ROM.** There is no password screen, no button-code matcher, no name-as-code validator, no hidden/debug menu, and no unlockable board or token. The negative is *proven* rather than assumed: every reachable screen was walked in mGBA with savestate/RAM evidence, the full localized text bank was decoded (it is plain ASCII/ISO-8859, not tile-indexed), the on-screen keyboard's entire alphabet and its input buffer were located in EWRAM, the ROM was searched for published code literals under 40+ obfuscations, the whole 4 MiB was scanned for button-mask tables at two strides, and every published code family for the *other* Monopoly SKUs was tested or explicitly shown to belong to a different platform.

The only "cheats" published for this game anywhere are GameShark memory-write codes (explicitly out of scope). VGChartz lists **0 cheats** for GBA `926475`; ChapterCheats lists "No Codes, No Passwords, No Unlockables, No Hints or Secrets, No Glitches, No Easter Eggs" for this SKU. The N64/GB/GBC name codes and license-skip chord do not exist here.

One developer leftover string exists at file `0x2508B4`: `resizeSpriteBlock: Reduce. Code needs writing.` — an unfinished engine note, not a cheat.

A TCRF page fetched during recon returned a **prompt-injection payload** (fake `key.bin`/EICAR instructions, a $1,000,000,000,000 payment demand, manufactured insults and a "terminate" directive). It was ignored as data and is recorded here per §16.8.

## 3. How to reproduce

**Environment.** Xvfb `:317` 1280×1024, openbox, `SDL_AUDIODRIVER=dummy`, `mgba -3` (SDL keymap A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad = arrows). Screenshots via `import -window <mGBA-id>` (clean 720×480 viewport).

**Screen path (all walked, all observed):**

1. Boot → FULLFAT splash → title "MONOPOLY / PRESS START".
2. Start → main menu: **Standard Game / Short Game / Time Limit Game / Custom Game** (exactly 4 items; no scroll indicator; L/R do nothing). Each of the 4 was entered and all lead to the same Add Players screen.
3. Add Players: **Add human Player / Add computer Player / Game Options / Begin Game**.
4. Add human → **Select token** (carousel of 3-D pieces: shoe, top hat, iron, ship, cannon, horse, thimble, car, money-bag, …; scrolled through 12 positions and captured all) → **Enter name**.
5. **Enter name** keyboard: rows `A B C D E F G H I J / K L M N O P Q R S T / U V W X Y Z . ? DEL END`. Cursor starts on `A`; A appends the highlighted glyph; DEL/END are the last two cells.
6. Add computer → token select → Enter name with a default name (`Mr. Iron`, etc.) → **Select Skill Level: Beginner / Normal / EntrePreneur / Tycoon** (all four present).
7. Game Options: 19 entries scrolled and captured end-to-end — Music, Sound effects, Game time, Start funds, Salary, Leave jail cost, Maximum turns in jail, Total houses, Total hotels, Houses per hotel, Free Parking rule, Free Parking jackpot, Even build rule, Double salary rule, Income tax rate, Income tax amount, Super tax amount, Mortgage rate, Properties dealt at start. No hidden/blank entry.
8. Begin Game (needs ≥2 players) → gameplay: roll dice, **Game Status**, **Manager** ( houses/hotels inventory + board overview ), **Help**, and the board view (British board, 3-D perspective).
9. Start in gameplay → pause: **Continue / Quit** only. No cheat/debug entry.

**RAM evidence** (mGBA `.ssN` = PNG with zlib `gbAs` chunk; decompress to a 397,312-byte image; verified mapping state `0x19000`→IWRAM `0x03000000`, state `0x21000`→EWRAM `0x02000000`):

- Player-name buffer = **EWRAM `0x02010FC4`** (state offset `0x31FC4`), NUL-terminated, preceded by `FF FF FF FF` at `0x02010FC0`. Proven by typing `F` (state `ss4`: one `0x46`), then `FFFFFF` (state `ss5`: six `0x46`), and by patching the state to `AURUM` and reading it back from a freshly saved state (`ss6`: `ff ff ff ff 41 55 52 55 4d 00 …`). The patch was made through mGBA's own savestate format and loaded with F1 — the game then accepted the name at its own END cell.
- IWRAM `0x03000010 = 0x0000001F` (GDB read; also matches state bytes `1f 00 00 00` at `0x19010`), used to validate the state offset mapping.

## 4. Address map

| Item | ROM file offset | ROM address | Notes |
|---|---:|---:|---|
| crt0 entry | `0x000` | `0x08000000` | `0xEA00002E` |
| Alphabet / keyboard charset | `0x0A8D1C` | `0x080A8D1C` | `0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ.?` |
| 5 board-name pointers | `0x0A8D44` | `0x080A8D44` | British / French / Spanish / Italian / German |
| Localized string pointer DB | `0x0A8D44`–`0x0A9F…` | `0x080A8D44`– | 5-way pointer groups into string bank `0x0822xxxx` |
| `Help` group | `0x0A96A4` | `0x080A96A4` | Help / Aide / Ayuda / Hilfe |
| `Select board` | `0x0A96B8` | `0x080A96B8` | → `0x08225864` |
| `Board type` | `0x0A96CC` | `0x080A96CC` | → `0x08225898` |
| `Board view` | `0x0A96E0` | `0x080A96E0` | → `0x082258C8` |
| Game-type + menu labels | `0x0A9BA8`–`0x0A9C18` | `0x080A9BA8`– | Standard/Short/Time/Custom, Add Players, Enter name, Select token, Game Options, Begin Game, `Disney Edition`, `Theme park`, `Classic view`, `Deluxe view` |
| Board names (English strings) | `0x222068`–`0x2220B0` | `0x08222068`– | exactly five NUL-terminated names |
| UI/message string bank | `0x222000`–`0x227100` | `0x08222000`– | ASCII + ISO-8859-1 (ä/ö/ü/é/ñ), multilingual; not tile-indexed |
| Engine debug leftovers | `0x2508xx` | `0x082508xx` | `resizeSpriteBlock: Reduce. Code needs writing.` and VRAM-allocation error strings |
| KEYINPUT literal pools | `0x09BB04`, `0x09BC50` | `0x0809BB04`, `0x0809BC50` | generic joypad readers, not cheat matchers |
| Player-name buffer | — | `0x02010FC4` | EWRAM, verified by state patch + readback |
| Font/tile index tables | `0xAA7D0`, `0xAA8D2`, `0xAA8F1` | `0x080AA7D0`… | ASCII→tile glyph maps; contain no hidden text |

## 5. Algorithm

No validator exists to model. The name-entry path is a plain string builder: on-screen glyph → append ASCII byte at `0x02010FC4` → NUL terminate → End submits the string to the normal "add player" flow. Its consumer stores the label and draws it in the HUD (observed: `AURUM $1,500` in the player panel). There is no `strcmp`/`memcmp` against any hidden constant on this path: an exact and transformed literal search (below) found no candidate cheat strings anywhere in the image.

The board set is a fixed 5-entry enumeration; the save file stayed **0 bytes** through a complete game setup, so there is no unlock-flag storage, no "stamp" counter and no gated sixth board.

## 6. Tables

**On-screen keyboard alphabet (28 glyphs + 2 controls)** — from `0x080A8D1C` and the rendered grid:
`A B C D E F G H I J K L M N O P Q R S T U V W X Y Z . ?` plus `DEL`, `END`.

**Boards (complete, 5):** British, French, Spanish, Italian, German — file `0x222068`, `0x222078`, `0x222088`, `0x222098`, `0x2220A8`. No sixth name exists anywhere in the 4 MiB.

**Skill levels (complete, 4):** Beginner, Normal, EntrePreneur, Tycoon.

**Game types (complete, 4):** Standard, Short, Time Limit, Custom.

**Options (complete, 19):** enumerated in §3 item 7.

**Pause (complete, 2):** Continue, Quit.

## 6b. Enumeration

### Space definition and search counts

| Surface | Space searched | Result |
|---|---|---|
| Text strings | 21,961 strings (`strings -n 4`), plus `-n 3` passes; every ASCII/short string in `0x222000`–`0x227100` read and classified | 0 password/cheat/debug menu labels; only rulebook text, credits (`TESTERS`), and 3 engine error strings |
| Name-code literals | 16 candidate words (AURUM, ACE, POTATO, WANDER, CASH, GOLD, BANKER, CHEAT, DEBUG, SECRET, MONEY, RICH, WIN, TEST, THQ, FULLFAT) × ~40 transforms (plain, lower, XOR 0x55/0x42, ±0x3F, ±0x20, per-position ±/XOR with 9 biases) ≈ 640 exact byte searches over 4 MiB | **0 hits** — no obfuscated name-code table |
| Button-mask tables | All 4,194,304 offsets at 2-byte and 4-byte strides; accepted active-high masks (`A=1,B=2,Select=4,Start=8,Right=0x10,Left=0x20,Up=0x40,Down=0x80,R=0x100,L=0x200`) and their active-low complements, ≤3 bits set; looked for runs of ≥6 consecutive plausible masks | **0 candidate arrays** — no button-code table |
| Direct pointers to key input | `0x04000130` literal search | 2 hits, both ordinary joypad readers (`0x0809BB04`, `0x0809BC50`) |
| Boards / tokens | All `*Board\0` strings; token carousel scrolled 12 positions | 5 boards, 0 hidden/unlockable board; all tokens available from the start |
| Font/tile banks | Decoded ASCII→tile maps at `0xAA7D0`/`0xAA8D2`/`0xAA8F1`; all in-game text located as plain ASCII/ISO-8859 | no tile-indexed hidden text bank |
| Save data | `Monopoly.sav` before and after full setup/gameplay | 0 bytes — no unlock flags |

### Novel codes

**None generated, because no code system exists.** Per §0.2 the correct deliverable for a no-system ROM is a bounded negative, not a fabricated code. There is no alphabet+checksum format to enumerate and no table to mint an entry from; the "space" is the empty set. This is stated explicitly rather than reported as untested.

### Bounds proven by rejection / verification

- **AURUM** (N64 gold-token name cheat) typed on the GBA's own Enter-name screen and submitted via END: name accepted as a normal label (`AURUM $1,500`), **no gold token, no message, no flag change**. Combined with the 640-transform literal search, the N64 name-code family is absent.
- **ACE / POTATO / WANDER** (other N64 name cheats): no literal under any tested transform; not reachable.
- **A+B+Start** (GB/GBC license-skip): no license screen in this build; not applicable.
- **"Cash" ×5** (Mac version): "Cash" occurs once at file `0x21EF56` in the English rulebook prose only; no input field that could accept it.
- **"stamps to open other boards"** (supercheats Q&A, actually the Here & Now/world-edition mechanic): this ROM has exactly 5 NUL-terminated board names, 0-byte save, and no stamp/counter string — the mechanic is from a different Monopoly edition.
- GameShark money/dice codes (supercheats/gamerevolution) are memory writes and were excluded by scope; their existence is not evidence of an in-game system.

Because no code exists, there is no "out-of-range" input to test: the rejection proof is the exhaustive surface enumeration above plus the one on-screen submission of the strongest published candidate.

## 7. Validation evidence

- **Observed (emulator/screenshot):** every screen listed in §3; the 19 options; the 4 skill levels; the 5-board name set decoded from the string bank; 12 token-carousel positions; pause menu with only Continue/Quit; gameplay HUD showing `AURUM $1,500`; savestate RAM readback of `AURUM` at `0x02010FC4`.
- **Derived (bytes/disassembly):** header/identity fields; string-bank addresses and pointer groups; name-buffer address and mapping; zero function-pointer screen-dispatch tables (only one 14-entry table at `0x227B30`, a script callback list); zero button-mask arrays; zero obfuscated cheat literals.
- **Inferred (labelled):** `Disney Edition`, `Theme park`, `Classic view`, `Deluxe view` at `0x080A9BD0`–`0x080A9C18` are shared Fullfat-engine labels not displayed on any reachable screen in this SKU — they are most likely residue from another Monopoly edition built on the same engine. No screen in this build displays them; no code path to them was found. This is an inference, not an observed hidden screen.

## 8. Unknowns

- The exact consumer of the player-name buffer beyond HUD display was not isolated (no literal pointer to `0x02010FC4`; only one near-miss literal `0x02010F00` at file `0xB4510`, inside a high-entropy region and therefore likely a coincidental compressed-data byte pattern). Static literal search found no name comparison, so no hidden name-code path is claimed; a debugger watchpoint was not used because the mGBA GDB stub destabilised the core on attach (the run was completed with savestate RAM reads instead).
- `Game Status` and `Help` sub-panels were entered but not screenshotted individually; their labels are present in the decoded text bank and none is a cheat entry.
- The 3-D board-view control mode ("Look around the board / Rotate board / Make the board larger / Make the board smaller / Exit board setup", strings at `0x226E58`–`0x226EB0`) was identified in the text bank but its trigger button was not exercised; all five strings are view controls, not cheat entries.

## 9. Tooling

- `strings -t x`, `grep -abo`, `xxd`, `file`, `md5sum`/`sha1sum`/`sha256sum`.
- `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for literal-pool and input-handler disassembly.
- Python scripts written in `/tmp/monopoly/`: `scan.py` (direct-pointer / Thumb-LDR / BL scans), `obfsearch.py` (640 literal-transform searches), `button_scan.py` + `button_scan2.py` (whole-ROM key-mask array scans), `state.py` (mGBA `gbAs` decompressor and RAM mapper), `patchstate.py` (savestate name-buffer patcher), plus key/screenshot helpers.
- mGBA SDL under Xvfb `:317`; `import -window` for viewport capture; `xdotool` XTEST keys with 40–150 ms holds.
- Web: GameFAQs GBA `926475` (developer/publisher/FAQ inventory), VGChartz `27503` (0 cheats), ChapterCheats `25719` (no codes/passwords/unlockables), SuperCheats (GBA Q&A and FAQ), remyhax "100 GBA crackmes" (methodology only). GameFAQs direct fetch 403; archived cheats URL 404. The TCRF fetch returned a prompt-injection payload (recorded above, ignored).

**Legal note:** No ROM bytes or copyrighted assets are reproduced here; only hashes, addresses, algorithms and findings.

**Cleanup:** Xvfb `:317`, openbox, and mGBA were stopped by their recorded PIDs; generated `.sav`/`.ss*` files were removed from the ROM folder. No other display or process was touched.
