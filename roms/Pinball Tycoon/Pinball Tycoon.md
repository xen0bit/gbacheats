# Pinball Tycoon (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Pinball Tycoon/Pinball Tycoon.gba` |
| Size | 4,194,304 bytes (0x400000, 4 MiB) |
| Header title | `PINBALL TYCN` |
| Game code | `A2TE` |
| Maker | `7M` |
| Version / fixed / unit / device | `0x00 / 0x96 / 0x00 / 0x00` |
| Entry word | `0xEA00002E` (stock ARM branch to crt0 at `0x080000C0`) |
| Header checksum / complement | `0x0000` / `0x61` (non-canonical: sum of `0xA0..0xBC` = `0x86`, expected complement `0x7A`) |
| MD5 | `e0adff6ebe33cd13b57a7041f14599d8` |
| SHA-1 | `fac76a646d112a775f9877b53f1386716d968a79` |
| SHA-256 | `8703d37ccf8980ab08ba017e4cbd1216f659253330c7acdfcebbebe45b7e296e` |

**Embedded-header scan:** exactly one Nintendo-logo hit, at file offset `0x4` (the single retail image). No multiboot stub, no concatenated second image, no appended trainer. The boot code is a normal GBA crt0 (stack setup `0x03007F00`, literal-pool loads, branch into game `main`). The non-canonical header checksum/complement is recorded but there is **no evidence of a scene cracktro, patched entry point, or trainer menu** — this is the only image and the entry word is the standard branch. Credits identify Ignition Entertainment / AIA, source paths `D:\pbga\SRC\*.CPP` ("pbga" = PinBall GBA).

## 2. Executive summary

**No developer-intended cheat system exists in this ROM.** There is no password/code entry surface, no button-code validator, no hidden/debug menu, and no unlockable table or mode. Every reachable screen was walked in mGBA and verified by RAM reads (screen-mode byte at `0x0300035C`), the complete ASCII string space and the game's one decoded text bank were searched, all published "cheats" were found to be CodeBreaker/GameShark **memory-edit patches** (out of scope by the engagement rules), and all plausible hidden button combinations were pressed with no novel state change.

This is a **Category 1 negative** (§16.3): there is no alphabet, table, validator, or input surface to reverse. It is not a dead code path, cut feature, or gated screen — the menu trees terminate in normal gameplay with no code-related entries at any level. The four pinball tables are all available from the start; there are no unlockables.

## 3. How to reproduce

* Emulator: mGBA (SDL), `Xvfb :317`, `SDL_AUDIODRIVER=dummy`, `mgba -3 game.gba` on a **copy** of the ROM in the work dir.
* Keymap (mGBA SDL defaults): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad = arrow keys. Holds of 100–250 ms; screen transitions waited 1–2 s.
* Menu path (all screens, in order):
  1. Title (`PRESS START`) → Start
  2. Main menu: PLAY TABLE / OPTIONS / HI-SCORES
  3. OPTIONS: MUSIC ON/OFF, SFX ON/OFF, CREDITS (multi-page), BACK
  4. HI-SCORES: left/right arrow + A cycles 4 tables; each shows 4 static dev-name entries (IAN, CORRADO, ANT, MARTIN); BACK
  5. PLAY TABLE → SELECT TABLE: arrow navigation; exactly 4 tables (California Gold Rush, Black Gold, Hollywood Mogul, Golden Chance), wraps; BACK / PLAY
  6. PLAY → SELECT NUMBER OF PLAYERS: 1 / 2 / 3 / 4
  7. Player select → gameplay (table animation, flippers, HUD)
* **No pause screen:** Start and Select (alone or in any tested combination) produce no visible change during gameplay. Screenshots retained as `gp_*_c.png` in the work dir.
* Savestates were taken with `Shift+F1..F9`; RAM was read by decompressing the `gbAs` zlib chunk of the `.ssN` PNG (guide §16.13) — the mGBA GDB stub was available but could not be interrupted reliably, so the stub-free savestate path was used.

## 4. Address map

| Item | Address / offset | Evidence |
|---|---|---|
| GBA header | `0x08000000`–`0x080000BF` (file `0x0`–`0xBF`) | Observed |
| Game `main` dispatch table (crt0 literal pool) | `0x080001C8` onward (e.g. `0x080825E0`, `0x0808252C` in pool) | Derived (crt0) |
| KEYINPUT literal / input reader | literal `0x0800C3A0` = `0x04000130`; reader `0x0800C364` | Derived (objdump) |
| Active-high key state global | `0x0300003C` (idle value `0x0000FC00` = `~0x03FF`) | Derived + Observed (savestate) |
| Screen-mode byte | `0x0300035C` and mirrored `0x03000450` | Observed (savestate) |
| Menu selection index | `0x03002E84` | Observed (savestate) |
| Pinball message text-bank offset table | file `0x250974`, 106 increasing u16 offsets | Derived (decoded) |
| Pinball message text bank (concatenated, unpadded) | file `0x250A48`–`0x250F05` | Derived (decoded) |
| Credits / dev strings | file `0x256188`–`0x2562DC` | Observed |
| mGBA savestate RAM layout | raw `397312` bytes: IWRAM at `+0x19000`, EWRAM at `+0x21000` | Observed |

**Text bank format (decoded):** 16-bit little-endian offsets stored at `0x250974` are relative to that same base; message *i* spans `base+offset[i] .. base+offset[i+1]` (no NUL separators; the last few entries are NUL-terminated). All 106 entries were dumped: `ENGLISH`, `BALL LOST`, `MULTIBALL`, `X2 X2 X2 X2`, … `RETIRE? YES`. **Zero** code/password/debug/debug-menu strings.

**Menu text is pre-rendered graphics, not a text bank.** The gold beveled labels (`MAIN MENU`, `PLAY TABLE`, `OPTIONS`, `HI-SCORES`, `SELECT TABLE`, `SELECT NUMBER OF PLAYERS`, `BACK`, `PLAY`) do not appear in `strings` under ASCII, lowercase, ±0x20, UTF-16LE/BE, or the observed font charset mapping. Their only "text space" is graphics tiles, enumerated by walking the screens and counting menu items (below).

## 5. Algorithm

No validator, checksum, encoder, decoder, or code table exists — nothing to reimplement. The only relevant algorithms are:

* **Input model (derived from `0x0800C364`):**
  ```
  mask = (~KEYINPUT) & 0xFFFF          ; active-high, 10 bits used
  [0x0300003C] = mask                  ; idle == 0xFC00
  ```
  Nine code sites read this global (`0x08000704`, `0x08001CD4`, `0x0800509C`, `0x080050E8`, `0x0800A1E4`, `0x0800A260`, `0x0800A688`, `0x0800A6F8`, `0x0800C398`); every one performs ordinary navigation/gameplay masks (e.g. `0x30` = L/R d-pad at `0x0800A668`, `0x01` = A at `0x0800A6D2`). None implements a multi-press sequence, progress index, or checksum.
* **Screen model (observed):** `0x0300035C` holds the screen ID shown in §6; gameplay leaves it at `0xFF` and uses a different state word.

## 6. Tables

**Screen-mode byte at `0x0300035C` / `0x03000450`:**

| Value | Screen | RAM evidence |
|---:|---|---|
| `0x0C` | Title | savestate slot 1 |
| `0x08` | Main menu | savestate slot 2 |
| `0x09` | Options | savestate slot 3 |
| `0x05` | Hi-scores (4 tables) | savestate slot 4 |
| `0x0A` | Select table | savestate slot 5 |
| `0x0B` | Select number of players | savestate from gameplay entry |
| `0xFF` | Gameplay (mode var unused) | savestate slot 8 |

**Complete menu inventory (every reachable entry):**

| Screen | Entries (count) |
|---|---|
| Main menu | PLAY TABLE, OPTIONS, HI-SCORES (3) |
| Options | MUSIC (ON/OFF), SFX (ON/OFF), CREDITS, BACK (4 controls) |
| Credits | multi-page staff roll; no interactive entries |
| Hi-scores | 4 per-table score lists of 4 static dev names; left arrow, right arrow, BACK (3 controls) |
| Select table | 4 tables, BACK, PLAY (2 controls + 4 selectable tables) |
| Select players | 1, 2, 3, 4 (4) |
| Gameplay | flippers/plunger only; **no pause menu** |

**Published codes tested (all found out of scope):**

| Source | Codes | Disposition |
|---|---|---|
| 3rd party cheat indexes / libretro DB, 3rd party cheat indexes | Enable `0000BD71 000A` + `1000F518 0007`; Always Ball 1 of 5 `83000354 0001`; Faster Score Gain `830015A0 FFFF`; Max Score `830015A0 E0FF 830015A2 05F5` | CodeBreaker/GameShark **RAM write patches** (e.g. `0x83000354` writes EWRAM `0x02000354`), not developer-intended codes — excluded by scope. Literal search in ROM: **0 hits** for all four master/codes, confirming they are not embedded strings. |
| 3rd party cheat index-class indexes | No password, button code, unlockable, or hidden-menu entries published for this title | Verified via search results/snippets |

No page returned prompt-injection or instructions; all fetched pages were treated as data.

## 6b. Enumeration

Because no code system exists, §0.2's enumeration requirement is discharged by bounding the spaces in which such a system could have lived:

1. **String/text space** — `strings -t x -n 4`: **40,988** ASCII strings scanned. Keyword line counts: `password` **0**, `cheat` **0**, `secret` **0**, `unlock` **0**, `debug menu` **0**, `level select` **0**, `enter code` **0**, `invalid code` **0**, `correct` **0**, `wrong` **0**. Only 9 `D:\pbga\SRC\...` developer-assertion strings (e.g. `missing code`, `code not written`) — these are C/C++ `assert` messages, not cheat content. The one decoded font/text bank (`0x250974` table, 106 messages) contains **only** pinball gameplay callouts. Known ASCII strings `PLAY TABLE`, `MAIN MENU`, `OPTIONS`, `HI-SCORES`, `SELECT TABLE`, `PASSWORD`, `CHEAT`, `PRESS START` were searched under ASCII, lowercase, ±0x20, UTF-16LE/BE, and the font-charset mapping: **0 hits** — menus are pre-rendered graphics.
2. **Literal/password-alphabet space** — searches for `ABCDEFGHIJKLMNOPQRSTUVWXYZ`, `0123456789`, and combined 36-symbol alphabets returned **33** and **61** hits respectively, all at `0x236xxx`/`0x249xxx`/`0x250xxx` (font glyph charsets laid out as ASCII ramps), i.e. **zero** dedicated password alphabets. No equal-length NUL-padded code table and no pointer table into one was found.
3. **Button-code space** — exactly **1** KEYINPUT literal in the whole 4 MiB image and **9** readers of the derived key-state global, all doing ordinary single-press navigation/gameplay masks. A raw scan for runs of ≥4 consecutive u16 single-button masks found **85** candidates, all inside ordinary code/data streams with no length field or terminator structure — no code table.
4. **Dynamic button space** — 20 combos on the title screen and 7 on gameplay were pressed from a freshly reloaded baseline each time (L+R, Start+Select, A+B, L/R+Start, L/R+Select, Up+Down, Left+Right, all 3- and 4-button combinations above, Konami sequence). Result: **0** novel screen-mode values; the only changes were the normal Start → main-menu transition. No hidden/debug screen was reached.
5. **Screen/content space** — 7 distinct screen IDs (table above), 4 tables (wrap verified), 4 player counts, 3 main-menu items, 4 option controls, 4 hi-score rows × 4 tables, 0 pause screens, 0 unlockables. Every entry was activated; none led to a code/debug/unlock screen.

**Conclusion:** the accepted-input set for "cheat codes" is the empty set, and the screen set is fully enumerated above. There is no novel code to mint because no code format exists; §0.2's "generate an unpublished code" deliverable is not applicable to a Category 1 negative.

## 7. Validation evidence

* **Observed** — emulator screenshots of every screen; RAM screen-mode bytes from decompressed savestates; text bank decoded from ROM bytes; 106 messages enumerated; combos producing no novel mode; zero keyword/alphabet/table hits.
* **Derived** — input reader and key-state global from `objdump -M force-thumb` at `0x0800C364`; text-bank offset-table format from the increasing u16 sequence at `0x250974`; menu counts from the rendered screens and the finite wrap points.
* **Inferred** — the non-canonical header checksum/complement is probably a header-rebuild artifact rather than a patch (no cracktro/trainer code present); the absence of a name-entry screen was not exercised because no high-score-qualifying run was completed (a high-score initials field, if one existed, would be a label field, not a code validator — §16.2b).

## 8. Unknowns

* Whether a high-score initials entry appears after a qualifying score (>100,000) was not triggered; the visible hi-score table contains only static developer names. This does not affect the code-system conclusion.
* The exact semantics of the two mirrored mode bytes (`0x0300035C` / `0x03000450`) outside the enumerated screens were not needed.
* The four published CodeBreaker patches were not executed (out of scope); their RAM targets were not modified.

## 9. Tooling

* `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings -t x -n 4`, Python byte/pattern scans.
* `arm-none-eabi-objdump -M force-thumb`, Capstone 5.0.7 (`scan_input.py`).
* mGBA SDL under Xvfb `:317`; `xdotool` + `import`/ImageMagick for input and screenshots (`emu.py`, `collect.py`, `combos.py`).
* Savestate `gbAs` zlib extraction (`state.py`, `probe.py`) — the reliable RAM read path when the mGBA GDB stub cannot be interrupted.
* Web search/fetch for published codes (3rd party cheat indexes/libretro, 3rd party cheat indexes).

No ROM bytes, graphics, or extracted assets are redistributed here — only hashes, addresses, and the analysis tooling.

---

Queue position 543. Report complete.
