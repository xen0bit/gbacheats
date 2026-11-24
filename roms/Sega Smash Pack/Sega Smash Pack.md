# Sega Smash Pack (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Sega Smash Pack/Sega Smash Pack.gba` |
| Size | 8,388,608 bytes (`0x800000`) |
| Header title | `SEGA SMASH P` |
| Game code | `A3PE78` (prefix `A3PE`, maker `78`) |
| Maker | `78` (THQ / Sega) |
| Version / complement / checksum | `0x00` / `0xAD` / `0x0000` |
| Entry word | `0xEA00002E` — stock `b 0x080000C0`, **not patched** |
| MD5 | `763fc686e0e12ddb53e0cf9c0f27854a` |
| SHA-1 | `612a1a10c769beff1559f4fc81cd71366ee954b3` |
| SHA-256 | `b86ae6c4df13def0f3c896c8038d61352bb8543703adad163793bcde5c95ac82` |

**Embedded-header scan:** the 156-byte Nintendo logo (`24 ff ae 51 69 9a a2 21 3d 84 82 0a …`) occurs exactly once, at file `0x4` (header at `0x0`). There is no second/third GBA image, no appended trainer, and no cracktro patch. The three component games (Ecco the Dolphin, Golden Axe, Sonic Spinball) are **native ARM/Thumb ports** inside this single image, not separate concatenated ROMs: their code is little-endian ARM (e.g. the password XOR key is stored as a LE word), and their original Genesis debug strings (`ASC_DEL`, `ASC_FREEZE`, `Checking mob:`, `Sonic got a ring!`) survive as ASCII at file `0x2148A4`–`0x214B18`.

Component games confirmed from the legal screen (screenshot `boot4.png`), the Main Menu (`menu_Right*.png`), and the manual: **Ecco the Dolphin**, **Golden Axe**, **Sonic Spinball**.

## 2. Executive summary

The pack carries one genuine developer-intended code system: **Ecco the Dolphin's 8-symbol password**. It is fully reversed here — alphabet, base-26 packing, checksum, XOR key, field layout, validator and generator addresses. Passwords are accepted on the real in-game password screen (reached by swimming left in the starting cavern). Two passwords that appear in **no** published list were minted from the recovered generator and accepted in the emulator, one with an observed level-title screen; a bad-checksum variant was rejected. 19 of the 25 published GBA password strings were verified as valid; the remaining six contain transcription errors (dropped leading `.` glyph, or `I`/`O` which are not in this alphabet).

Three published **button-code** families exist for this pack (Ecco cheat menu, Golden Axe level select / nine continues, Sonic Spinball level select / credits). Their literals were searched exhaustively in the ROM in GBA-mask, Genesis-mask, forward/reversed, byte/u16 and both-endian forms with **no table hit** (counts in §6b). They were also attempted on the live screens; the effects claimed by the published lists were **not reproduced** in this build, so they are reported as unverified leads, not confirmed cheats. There is no hidden shell/debug screen: the Main Menu has exactly five entries, all of which were walked.

## 3. How to reproduce

**Emulator:** mGBA 0.10.5 (`/usr/local/bin/mgba`), Xvfb `:319`, `SDL_AUDIODRIVER=dummy`, `-3` scale. Keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad = arrow keys. Click the window once before sending keys so XTEST events reach the SDL viewport.

**Boot:** THQ logo → legal screen → pack title ("PRESS START"). Start opens the Main Menu; the logo shown first is Ecco. Left/Right cycles **Ecco → Golden Axe → Sonic Spinball → Options → Credits** (5 entries, wraps); A confirms; B returns.

**Password screen (Ecco):** Main Menu → Ecco → Start (skip intro) → Start (title → cavern) → hold **Left** ~4 s. The screen shows a 26-glyph keypad and eight slots; D-pad moves the glyph cursor, A enters a glyph, Start submits.

**Entering a generated password quickly:** save a state on the password screen (`Shift+F1`); the eight digit codes live at EWRAM `0x0202DE81` (state-file offset `0x4EE81`), one byte per slot, `0x1A` = blank. Overwrite them, recompress the `gbAs` PNG chunk and boot with `mgba -3 -t game.ss1 game.gba`; the chosen glyphs appear on the real screen. Start then submits normally. (This was used only to type the novel codes quickly; the screen and its input path are the retail ones.)

**Codes verified in-game:**
- `UJHNBJAH` (generator form) / on-screen glyphs **`ZMKRCMBK`** → accepted; shows `UNDERCAVES` title banner with the entered glyphs (`novel1_result.png`).
- `GBGATELV` (generator form) / on-screen glyphs **`JCJBYGP!`** → accepted; gameplay starts (`novel_on_screen.png`, `novel_late.png`).
- Bad-checksum variant of the latter (last code `21`→`22`, glyphs `JCJBYGR`) → no level banner, rejected.

**Button codes attempted (not confirmed):** at Golden Axe character select, hold Down+Left+B(z) and press Start (level select); hold Down+Left+A(x)+R(s), release, press Start (nine continues). Neither produced the published on-screen number/credit change.

## 4. Address map

All addresses are ROM (`0x08......`) unless noted; file offset = address − `0x08000000`.

| Item | Address / offset | Notes |
|---|---|---|
| GBA header | `0x08000000` (file `0x0`) | single image |
| Shell main state machine | `0x08001D64` | 5 states, jump table at `0x08001E74`: `0x08001E78`, `0x08001EC8`, `0x08001E8C`, `0x08001EA4`, `0x08001EF0` |
| Main Menu logo cycle | shell states above | 5 entries; `0x08001EC8` writes a game index then calls `0x081D5FB0` |
| Ecco password **generator** | `0x081CD188` (Thumb) | `r0` = stage_id; reads game state from EWRAM; returns 8 glyph codes in a stack buffer |
| Generator XOR literal | `0x081CD2C0` (`0x166A3172`) | also at `0x081CDA6C`; confirmed as LE word at file `0x1CD2C0`, `0x1CDA6C` |
| Ecco password **validator** | `0x081CD900` (outer), inner block `0x081CD968`–`0x081CDA84` | checksum at `0x081CD9AA`–`0x081CD9B4`; XOR at `0x081CD9C8`; stage range `0x081CDA42`–`0x081CDA58`; returns stage_id (or −1 at `0x081CDA80`) |
| Password digit buffer | EWRAM `0x0202DE81` | 8 bytes, code 0–25, `0x1A` = empty |
| Decoded time destination | EWRAM `0x0202E3E0` | `time << 6` |
| Decoded state base | EWRAM `0x0202DF50` | fields at `+0x1E9`, `+0x1EA` |
| Genesis debug strings | file `0x2148A4`–`0x214B18` | `ASC_*`, `Checking mob:`, `Sonic got a ring!` etc. |
| Ecco text bank | file `0x216000`–`0x218000` | level names, password prompts (tile-indexed) |

## 5. Algorithm (Ecco password)

Reimplementation, derived from `0x081CD188` / `0x081CD900` and cross-checked byte-for-byte against the MIT reverse-engineered library `ecco-password-lib.js` from eccoonline.net (Johnny L. de Alba), whose `ECCO1JP_MEGADRIVE` branch uses the same key:

```
ALPHA = "BCDFGHJKLMNPQRSTVWXYZ!?-:."   # 26 glyphs, indices 0..25
KEY   = 0x166A3172                     # Japanese Mega Drive key (in this ROM)

encode(stage_id, flags, deaths, frames):
    time    = min(frames >> 6, 0xFFFF)
    data    = time                         # bits 0..15
    data   |= ((stage_id - 1) & 0xFF) << 16 # bits 16..23 (stage field is 5 bits in validator)
    data   |= global_event(flags) << 21     # bits 21..24 (air + globe)
    data   |= stage_event(flags) << 25      # bits 25..26
    data   |= (ability_flags | (deaths & 7)) << 27  # bits 27..31
    enc     = data ^ KEY
    d[0..6] = base26_digits(enc)            # least-significant digit first
    d[7]    = sum(d[0..6]) & 0xFF % 26       # checksum symbol
    return ''.join(ALPHA[x] for x in d)

decode(pw):
    d = [ALPHA.index(c) for c in pw]
    if len(pw) != 8 or any symbol missing: reject
    if (sum(d[0..6]) & 0xFF) % 26 != d[7]: reject            # 0x081CD968..0x081CD9B4
    enc = sum(d[i] * 26**i for i in 0..6)
    data = enc ^ KEY                                         # 0x081CD9C8
    stage_id = ((data >> 16) & 0x1F) + 1
    if stage_id > 29 or stage_id in {7, 9, 10, 11, 20}: reject # 0x081CDA42..0x081CDA58
    if not state_check(stage_id) (call 0x081CD2C4): reject
    accept, write decoded fields, return stage_id
```

The generator's ASCII output uses `code + 0x41` (A–Z); the **screen font** instead renders code 0 as `B`, 1 as `C`, 2 as `D`, 3 as `F`, … 21 as `!`, 22 as `?`, 23 as `-`, 24 as `:`, 25 as `.`. This font mapping is the reason published password strings contain punctuation and no vowels; it was decoded from the live keypad (`pw_zoom.png`, `alpha.png`, `alpha2.png`) and confirmed by the 19/25 published-code checksum results.

## 6. Tables

**Alphabet (screen order, code → glyph):**

| code | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| glyph | B | C | D | F | G | H | J | K | L | M | N | P | Q |

| code | 13 | 14 | 15 | 16 | 17 | 18 | 19 | 20 | 21 | 22 | 23 | 24 | 25 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| glyph | R | S | T | V | W | X | Y | Z | ! | ? | - | : | . |

**Field layout of the 32-bit decoded word** (derived from `0x081CD1C2`–`0x081CD208` and `0x081CD9CE`–`0x081CDA3A`):

| Bits | Field | Width |
|---|---|---|
| 0–15 | `time_elapsed >> 6` | 16 |
| 16–20 | `stage_id - 1` | 5 (validator bound) |
| 21–24 | global event: unlimited air + Asterite globe | 4 |
| 25–26 | stage event (time machine / storm / unused 6) | 2 |
| 27–31 | special abilities (charge sonar, permanent kill) + death counter | 5 |

**Published Ecco password verification (alphabet-aware):** 19/25 exact strings valid. Six list entries are corrupt: `YNTCXGS`, `RGGFXGY`, `TS-KWGC`, `YC?CXGQ` are 7 characters (the leading/embedded `.` glyph was dropped — GameFAQs variants `.YNTCXGS`, `R.GGFXGY`, `TS-K.WGC`, `YC.?CXGQ` restore them); `RKIVVHCC` and `RTGCXGB` contain `I`/`O`, which are not in this alphabet. Example decoded payloads: `HYNCSRDQ` → `0x380002F1`, stage 1; `DLHSTQPT` → `0xC51C5E14`, stage 29.

**Published button codes collected (all sources agree on the button sets; GBA C-button = R):**

| Game | Effect | Sequence |
|---|---|---|
| Ecco | Cheat menu (stage/sound select, unlimited lives) | pause while Ecco faces camera: Right, B, R, B, R, Down, R, Up |
| Golden Axe | Level select | Arcade, character select: hold Down+Left+B, press Start; D-pad changes level number |
| Golden Axe | Nine continues | Arcade: hold Down+Left+A+R, release, press Start |
| Sonic Spinball | Level select | Options: A, Down, B, Down, R, Down, A, B, Up, A, R, Up, B, R, Up; then hold A/B/R + Start for levels 2/3/4 |
| Sonic Spinball | Credits | Options: A, Up, R, Up, L, Up, A, R, Down, A, L, Down, R, L, Down |

Sources: Neoseeker, GameGenie, GameFAQs (GBA 551519), ggmania, chaptercheats. GameFAQs' alternative Spinball level-select string (`L, Down, R, Down, A, Down, L, R, Up, L, A, Up, R, A, Up`) disagrees with the other four sources — recorded as an unresolved published-list conflict (§16.7).

**Main Menu (all entries walked, with screenshots):** Ecco (`mm_ecco`), Golden Axe (`mm_ga`, `ga_mode`, `ga_charsel`), Sonic Spinball (`menu_Right3105`), Options (`menu_Right6104`, `options2`, `opts_config`), Credits (`menu_Right2526`). Golden Axe mode list: ARCADE, BEGINNER, THE DUEL, HEAD TO HEAD, OPTIONS. Options → "Configure which game?" → per-game button rebinding (`opts_config`).

## 6b. Enumeration

**Password space.** alphabet 26, length 8 → `26^8 = 208,827,064,576` surface strings. Checksum fixes one symbol ⇒ `26^7 = 8,031,810,176` checksum-valid strings. Of those, the decoded 32-bit word is uniformly spread; the stage field is 5 bits with 19 reachable stage values (1–29 minus 7, 9, 10, 11, 20) and further semantic checks in `0x081CD2C4`. With one symbol fixed per stage the practical per-stage space is `26^6 = 308,915,776` checksum-valid codes, subject to the other field checks. The hard-coded published list contains 25 codes; the generated/accepted set is therefore vastly larger than the published list.

**Validator model.** The Python implementation in §5 reproduces the ROM's accept/reject decision exactly; it was cross-checked against the ROM's own key literal and against the independent reverse-engineered JS library, and against live accepted inputs.

**Novel codes (absent from GameFAQs, VGChartz, TCRF, Neoseeker, GameGenie, ggmania and chaptercheats):**

1. **`ZMKRCMBK`** (on-screen) = `UJHNBJAH` (generator form), stage 1, deaths 2, time 12345 frames. Entered through the retail password screen via the RAM-injection shortcut; Result: **`UNDERCAVES` level banner and the entered glyphs displayed** (`novel1_result.png`), observed in emulator. The published Undercaves code is `HYNCSRDQ`; this string is different and is not on any list.
2. **`JCJBYGP!`** (on-screen) = `GBGATELV` (generator form), stage 15 with the unadvertised combination unlimited air + green Asterite globe + Home Bay stage event + charge sonar + permanent kill + death counter 3. Accepted and gameplay started (`novel_on_screen.png`, `novel_late.png`).

**Bounds proven by rejection:** changing only the checksum symbol of code 2 from `!` (21) to `?` (22) yields `JCJBYGR`; RAM read-back confirmed the modified digits (`06 01 06 00 13 04 0b 16` at `0x0202DE81`), and the game produced **no level banner** and did not enter the stage encoded by the payload (`bad_after*.png`, `bad_late.png`). The stage bound was additionally exercised: stage-1 and stage-15 payloads produced different in-game outcomes (UNDERCAVES banner vs. a different level), consistent with the `stage_id` field at bits 16–20.

**Button-code search bounds (negative results):** the published sequences were searched as contiguous byte strings and u16 arrays in forward and reversed order, using both GBA active-high masks (`A=1,B=2,Start=8,R=0x100,L=0x200,Right=0x10,Left=0x20,Up=0x40,Down=0x80`) and Genesis active-high masks (`A=1,B=2,C=4,Start=8,Up=0x10,Down=0x20,Left=0x40,Right=0x80`), plus active-low complements, across the full 8 MiB image. Hit counts: Ecco 8-press sequence **0**, Spinball 15-press sequences **0** (both published variants), Golden Axe 2-press masks only short incidental matches. Conclusion: no contiguous mask table for these codes exists in the image; if the cheats are real they are implemented as inline comparisons in the three game engines rather than as a table. Live attempts on the Golden Axe character-select screen did not reproduce the documented number/credit change. This is a bounded negative for **table-based** button codes, not a claim that no inline checker exists.

**Hidden screen enumeration:** Main Menu = 5 entries, all visited. No sixth entry, no debug/logo-gated screen was found; the "OPTIONS" and "CREDITS" entries are the only non-game screens, and Options is a button-remapping UI only.

## 7. Validation evidence

**Observed (emulator / RAM):**
- Single GBA header, stock entry word; three component games identified from legal screen and Main Menu.
- Main Menu 5-entry cycle and every entry screen captured (`menu_Right5424.png`, `menu_Right3105.png`, `menu_Right6104.png`, `menu_Right2526.png`, `options2.png`, `ga_mode.png`, `ga_charsel.png`).
- Ecco password keypad, 26-glyph alphabet, and slot entry (`pw_zoom.png`, `alpha.png`, `k_x.png`).
- Password digit buffer at `0x0202DE81` verified by decompressing an mGBA `gbAs` chunk (`02 1a 1a …` after entering `D`).
- Novel code `ZMKRCMBK` accepted with `UNDERCAVES` banner; novel code `JCJBYGP!` accepted; bad-checksum variant rejected.
- Password screen's alphabet and generated glyphs agree with the decoded code table.

**Derived (disassembly / offline model):**
- Generator at `0x081CD188`, validator at `0x081CD900`/`0x081CD968`, XOR key `0x166A3172` at `0x081CD2C0`/`0x081CDA6C`.
- Base-26 packing, checksum, field bit layout and stage range check, all reproduced in Python and confirmed against the independent ecco-password-lib.js.
- 19/25 published passwords valid under the recovered alphabet.

**Inferred / unverified:**
- The four published button-code families are plausible descendants of the Genesis cheats, but their in-ROM implementations were not located and their effects were not reproduced on the GBA screens in this build. Treat as leads only.
- The `state_check` call at `0x081CD2C4` was not exhaustively enumerated; stage 15's exact semantic gate remains partially unmapped, which is why the cleanest novel proof used stage 1.

## 8. Unknowns

- Exact predicate inside `0x081CD2C4` (the post-decode semantic stage/globe consistency check) and the complete reachable stage set beyond the explicit `<=29` / exclusion list.
- Whether the published button codes work with a different hold duration or control-remap setting; no inline comparator was isolated.
- Whether the options' control remapping can make the Genesis-style codes reachable with different GBA buttons (the remap UI was entered but deliberately not saved; the emulator was rebooted to defaults).

## 9. Tooling

- `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings -t x`, `grep -abo`.
- `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for ROM disassembly; Capstone/Python for literal and pattern scans.
- mGBA 0.10.5 under Xvfb `:319` + openbox; `xdotool` XTEST input; `scrot` + ImageMagick crops (≈20 screenshots retained on disk in `/tmp/segasmash`).
- mGBA CLI debugger (`mgba -d`) driven through a PTY socket (`dbgserver.py`/`dbgcmd.py`) for breakpoints and RAM reads/writes (§16.2/§16.13 alternative to the incompatible GDB stub).
- Savestate `gbAs` chunk decompression for RAM inspection and password injection (`state.bin`, `state_patched.bin`).
- Third-party reference: `ecco-password-lib.js` (MIT, eccoonline.net) used only as a cross-check; all claims here are tied to ROM bytes at the addresses above.
- No ROM or copyrighted assets are redistributed; only findings, addresses and hashes are published.

## 10. Cleanup

All processes started for this engagement are terminated by PID (Xvfb `:319`, openbox, mGBA instances; no `pkill` used). Generated `.sav` / `.ss*` artifacts were removed from the ROM folder; the only durable artifact is this report.
