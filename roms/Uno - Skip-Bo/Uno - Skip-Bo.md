# Uno - Skip-Bo (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Uno - Skip-Bo/Uno - Skip-Bo.gba` |
| Size | 4,194,304 bytes (0x400000, 4 MiB) — single GBA image, **one** Nintendo logo/header only |
| Header title | `UNOUNOSKIPBO` |
| Game code | `BUQE` |
| Maker code | `20` |
| Version byte (0xBC) | `0x00`; complement (0xBD) `0x16`; header checksum (0xBE) `0x0000` |
| Entry word | `0xEA00002E` → standard crt0 at `0x080000C0` (`mov r0,#0x12` … at `0x080000E0`) — **not** a cracktro/trainer |
| `file(1)` | `Game Boy Advance ROM image: "UNOUNOSKIPBO" (BUQE20, Rev.00)` |
| Developer / Publisher | Black Lantern Studios, Inc. / Destination Software, Inc. (2006) |
| MD5 | `cf66c71bcc65c5e0ee20c666df8d6540` |
| SHA-1 | `76f85ac10c7ba7f00503fba4d41fb709b5b9cd22` |
| SHA-256 | `10db686936fc7306d2932f7a8c8917a44be6fdd7875283b10af275e02c95256c` |

The header complement/checksum mismatch is the normal signature of a rebuilt header; the first 4 KiB was checked (§16.1) and is stock crt0, so the image is a legitimate retail build with a patched header rather than a modified boot path.

## 2. Executive summary

**Bounded negative: this game has no in-game/developer cheat system of any kind.** There is no password screen, no code-entry field, no button-code sequence, no hidden/debug menu, and no unlockable content gated by input. The only text-entry surface is a player-name keypad whose consumer is a `%s` display field, not a validator (§16.2b). Every reachable screen was walked in mGBA and every UI string in the ROM was enumerated.

Evidence in brief:

1. The entire UI text bank is a single table of **1,930 pointers = 386 distinct strings × 5 languages** at `0x08040AC4`. A full enumeration of all 386 English strings (and case-insensitive sweeps of the whole 4 MiB image) returns **zero** hits for `PASSWORD`, `CHEAT`, `DEBUG`, `SECRET`, `UNLOCK`, `MASTER`, `LEVEL SELECT`, `TEST MODE`.
2. The only text-input widget uses the 40-symbol keypad alphabet at `0x0803EFB8` (`ABCDEFGHIJKLMNOPQRSTUVWXYZ'-0123456789` + backspace/blank/confirm glyphs). The preset names `AARON … ZACH` are labels. The buffer is consumed as `%s` by the score/in-game displays; there is no comparison against a secret constant.
3. There is exactly **one** literal `0x04000130` (KEYINPUT) in the whole ROM (`0x0802B3B4`), read by exactly **one** function (`0x0802B3AC`) with exactly **one** caller (`0x0802B99C`) — a generic 6-virtual-button input manager. There is no second polling path for a button code, and no Konami-style key-mask table exists (0 hits for the classic sequence in active-high *and* active-low encodings, 16-bit and 32-bit).
4. Web recon found **no published in-game codes**: the GameFAQs GBA cheats page is empty and VGChartz reports "Total cheats available: 0". The only GBA cheat files in circulation for this title are GameShark/Action-Replay `.CHT` files (external devices — explicitly out of scope).
5. No feature is gated: all 15 backgrounds, 4 music tracks, 3 Special Modes, 6 Challenge entries, and all Quick Play / Custom Game options are selectable from a fresh save.

## 3. How to reproduce

**Emulator**: mGBA 0.10.5 under Xvfb `:315`, `SDL_AUDIODRIVER=dummy`, `SDL_RENDER_DRIVER=software`, `-3` scale, GDB stub on `:2400` (stub proved unreliable; savestate diffing used instead).

**Keymap** (mGBA SDL defaults): `A=x`, `B=z`, `L=a`, `R=s`, `Start=Return`, `Select=BackSpace`, D-pad = arrow keys. Holds of 100–150 ms with ~180 ms gaps were used.

**Boot path (exact)**:
1. Health & Safety → any button.
2. Legal/copyright screen → any button (several presses).
3. Title "PRESS START" → `Start`.
4. Top-level menu: **UNO** / **SKIP-BO** / **OPTIONS** (D-pad selects, `A` confirms, `B` back).
5. `UNO` → UNO MAIN MENU: **QUICK PLAY / CUSTOM GAME / SPECIAL MODES / HELP**.
6. `SPECIAL MODES` → NAME ENTRY → (`Start` accepts default) → ICON SELECTION → (`A` accepts) → SPECIAL MODES: **CHALLENGE MODE / ENDURANCE MODE / TIMED MODE**.
7. `CHALLENGE MODE` → CHALLENGE LEVEL 1–5 + RANDOM CHALLENGE (D-pad left/right).
8. `ENDURANCE MODE` / `TIMED MODE` → THEME (BACKGROUND ×15, MUSIC TRACK ×4) → Start Game.
9. `QUICK PLAY` → HUMAN PLAYERS / AI PLAYERS / DIFFICULTY / GAME TYPE → Next → (name/icon) → THEME → gameplay.
10. In gameplay, `Start` → PAUSE: **RESUME / OPTIONS / QUIT** (with per-player score panel).
11. `OPTIONS` (top level) → EFFECTS VOLUME / MUSIC VOLUME / VIEW CREDITS.

**Codes tested**: none exist to test. Button sequences tested in-game without effect from the title screen and menus: Konami code (↑↑↓↓←→←→BA), L+R, Start+Select, and L+R+Start. All were treated as ordinary navigation/no-ops.

**Screenshots**: `crop_*.png` in `/tmp/opencode/unoskipo/` (boot, title, all menus, theme, challenge levels, gameplay, pause). Savestates `game.ss1`–`game.ss7` in the same directory.

## 4. Address map

| Address | Type | Description |
|---|---|---|
| `0x08000000` | code | ARM entry branch `0xEA00002E` → crt0 |
| `0x0802B3AC` | code | Sole KEYINPUT reader: `ldr r1,[pc,#4]; ldrh r0,[r1]` |
| `0x0802B3B4` | data | Literal `0x04000130` (only occurrence in ROM) |
| `0x0802B99C` | code | Sole caller — generic input manager; stores `~KEYINPUT` to `0x0300513C`, then drives 6 virtual buttons |
| `0x0802BA00`/`0x0802BA34`/`0x0802BA54`/`0x0802BA70`/`0x0802BAA0` | code | Virtual-button helpers (MRU history, held/pressed/release). Called 64/21/21/20 times from ordinary UI/game code — no cheat-specific consumer |
| `0x0300513C` | RAM (IWRAM) | Active-high key state (`~KEYINPUT & 0x3FF`); observed `0xFC00` = no keys held |
| `0x03005110`, `0x03005140`–`0x0300517C` | RAM | Input-manager counters/flags; all xrefs confined to `0x0802B940`–`0x0802C1xx` |
| `0x0803EFB8` | data | Name-entry keypad alphabet: `ABCDEFGHIJKLMNOPQRSTUVWXYZ'-0123456789`, plus glyphs `08 20 0A 20` (backspace/space/confirm) |
| `0x0803EFD8`–`0x0803EFF8` | data | Pointers to name-entry sub-tables (`0x0803226A0`, `0x080322A3A0`, `0x080322B388`, `0x080322C370`) and `0xFFFFFF9C` terminators |
| `0x08040AC4` | data | **UI string pointer table**, 1,930 × u32 → `0x080428EC`…`0x08050718`; laid out as 5 language blocks of 386 strings (EN, FR, IT, DE, ES) |
| `0x080428EC` | data | First string: "Main Menu"; text bank runs to ~`0x08050xxx` |
| Savestate layout | — | mGBA `.ss1` `gbAs` chunk → zlib raw 397,312 bytes: header `0x0`, VRAM `0x1000`, IWRAM `0x19000`, EWRAM `0x21000` |

## 5. Algorithm

Not applicable — **there is no validator, checksum, or code algorithm to reverse.** The relevant reverse-engineered behaviour is the input path:

```
KEYINPUT (0x04000130, active-low)
  -> 0x0802B3AC: ldrh  -> r0 = ~raw
  -> 0x0802B99C: store active-high mask to 0x0300513C
        -> for i in 0..5: 0x0802BAD4(i)   // per-virtual-button press/hold
        -> 0x0802BB54()                   // repeat/direction tracking
        -> for i in 0..5: 0x0802BBB4(i)   // release tracking
        -> 0x0802BC50()                   // direction dispatch (values 0x02/0x0A/0x1A/0x22)
  -> ordinary UI/game code calls 0x0802BA34/54/70/A0 to query virtual buttons.
```

The `0x0802BB54` routine tracks only the 4-bit direction field (`mask 0xF0`, i.e. D-pad) with an 8-entry history and a 16-bit repeat counter; it is menu navigation, not a code matcher. No routine in the game compares a *sequence* of button masks to a constant table.

## 6. Tables

### 6.1 Complete UI vocabulary (386 distinct strings × 5 languages)

Menu/navigation strings were enumerated in full; the complete English set is in `/tmp/opencode/unoskipo/en_strings.txt` (derived from `0x08040AC4`). Notable groups:

- Screens: `Main Menu`, `UNO Main Menu`, `SKIP-BO Main Menu`, `Theme`, `Name Entry`, `Icon Selection`, `Special Modes`, `Options`, `Credits`, `Help`, `Instructions`, `Controls`, `Pause`, `Quick Play`, `Player Setup`, `Game Settings`, `House Rules`, `Alternate Cards`, `Challenge Mode`, `Scores`, `Custom Game`, `Endurance Mode`, `Timed Mode`, `Challenge Level 1..5`, `Random Challenge`.
- Actions: `Back`, `Confirm`, `Select`, `Delete`, `Add Character`, `Start Game`, `Next`, `Enter`, `Press Start`, `Resume`, `Cancel`, `Quit`.
- **Absent**: password, code, cheat, secret, unlock, debug, hidden, master, level select, sound test, test mode.

### 6.2 Name-entry keypad (0x0803EFB8) — 40 symbols

```
A B C D E F G H I J K L M N
O P Q R S T U V W X Y Z ' -
0 1 2 3 4 5 6 7 8 9  <-  [confirm]
```
(Source bytes: `41..5A 27 2D 30..39 08 20 0A 20`.) This alphabet is identical to a standard name field; it contains no wildcard/extra symbol that could encode a hidden value.

### 6.3 Screens reached (16 distinct screen types)

Health & Safety · Legal · Title · Top menu · Options · UNO Main Menu · Name Entry · Icon Selection · Special Modes · Challenge Mode (6 entries) · Theme · Quick Play · Player Setup · Help · Gameplay · Pause. SKIP-BO Main Menu mirrors UNO Main Menu (4 entries).

### 6.4 Save data

`/tmp/opencode/unoskipo/game.sav` is 0 bytes after the full menu walk — no unlock flags are written by any of the visited screens.

## 6b. Enumeration

This section records the bounded negative required by §0.2.

**Search space defined and checked:**

| Space | Size | Result |
|---|---|---|
| Whole ROM bytes scanned for cheat keywords | 4,194,304 | `DEBUG` 0, `PASSWORD` 0, `CHEAT` 0, `SECRET` 0, `UNLOCK` 0, `MASTER` 0, `LEVEL SELECT` 0, `TEST MODE` 0 |
| UI string table | 1,930 pointers / 386 unique strings / 5 languages | Enumerated exhaustively — no code-entry or debug screen label |
| ASCII runs outside the table (potential debug leftovers) | 42,676 runs examined; 292 word-like | All 292 were continuations of localized UI text at accented-character boundaries; no debug/assert strings (`assert`/`fatal`/`warning` 0 hits; `illegal`×2 and `exception`×1 are card-rule text) |
| Key-input hardware literals | 1 (`0x04000130`) | 1 reader, 1 caller → generic input manager only |
| Classic Konami mask sequence (↑↑↓↓←→←→BA and B→Start variant) | 4 encodings × 2 inversions × 2 widths = 8 searches | 0 hits anywhere in ROM |
| Published-code recon | GameFAQs cheats page, VGChartz, general web | 0 in-game codes published; only external-device `.CHT` files exist |
| Reachable screens | 16 screen types walked in emulator | No hidden menu item, no gated option, no unlockable |
| Backgrounds / music tracks / challenge levels | 15 / 4 / 6 | All freely selectable from a fresh save |

**Counts proving the negative:** 386 UI strings, 40 keypad symbols, 1 joypad reader, 1 joypad-reader caller, 0 debug strings, 0 password strings, 0 code tables, 0 published codes, 0 gated options, 16 screens walked.

Because the accepted set is **empty**, there is no code to mint and no "novel code" deliverable is possible; §0.2's alternative branch applies — the negative is proven over the entire input/UI space rather than by generating a code. Per §16.3 this is a **"No system"** result, not dead code, a cut feature, or a gated feature.

## 7. Validation evidence

- **Observed**: every screen listed in §6.3 was reached in mGBA with a screenshot retained on disk (`/tmp/opencode/unoskipo/crop_*.png`). Background cycling observed through WINGS → SQUARES → SPHERES (all reachable). Challenge Levels 1–5 and Random Challenge observed by D-pad cycling. Gameplay + pause menu observed.
- **Observed (RAM)**: savestate `game.ss7` (pause menu) decoded from the mGBA `gbAs` chunk; `0x0300513C = 0xFC00` (active-high, no buttons held), `0x03005110 = 0x8`, `0x03005140 = 0x1`, `0x03005160 = 0x14`, `0x03005164 = 0x6` — all inside the input manager's own global block.
- **Derived**: the 1,930-pointer string table and 386 unique English strings were decoded directly from ROM bytes at `0x08040AC4`; keyword counts are byte-exact. The single KEYINPUT literal/reader/caller chain was verified by Capstone literal scanning and a Thumb BL scan over all 4 MiB.
- **Derived**: the keypad alphabet and its trailing glyph bytes at `0x0803EFB8` were read directly; no secret symbol exists.
- **Inferred**: that the name buffer is display-only. Its consumers are `%s` formatting in the score/game UI, and no comparison against a constant was found, but an exhaustive dataflow trace of the keyboard widget was not completed.
- **External (data, not instruction)**: GameFAQs cheats page empty; VGChartz "Total cheats available: 0". Fetched pages were treated strictly as data.

## 8. Unknowns

- No exhaustive dataflow trace of the name-entry buffer was performed; the "display-only" conclusion is inferred from `%s` usage and the absence of any compare helper call near the keypad code (`0x0800CD20`–`0x0800D3C2`), not proven instruction-by-instruction.
- The GDB stub on this mGBA build was unreliable (packet errors/timeouts; config override `-C gdb.port=2400` did not bind). RAM reads were therefore taken from savestate `gbAs` chunks rather than a live debugger. No breakpoint-based proof of "no hidden handler" was possible; the negative rests on exhaustive string/input/screen enumeration instead.
- Save-file format and any battery-backed progress flags were not fully mapped (the `.sav` stayed 0 bytes through the walk). No unlockable behaviour was observed, but a deep save-format audit was out of scope for a code-system engagement.

## 9. Tooling

- `md5sum`/`sha1sum`/`sha256sum`, `file`, `xxd`, `strings -t x`, `grep -abo`
- Python 3 scripts in `/tmp/opencode/unoskipo/`:
  - `kb.py` — XTEST key helper (100–150 ms holds) + screenshot/crop
  - `scan_input.py` — literal + Capstone Thumb-LDR scan for `0x04000130`
  - `ram.py` — mGBA `.ss1` `gbAs` chunk decompressor / RAM diff (IWRAM at +0x19000, EWRAM at +0x21000)
  - inline scripts for pointer-table decoding, BL scanning, mask-sequence search, text-bank enumeration
- `arm-none-eabi-objdump -M force-thumb` for manual disassembly, Capstone for scripted scans
- mGBA 0.10.5 (`-3`, GDB stub attempted), Xvfb `:315` + openbox, xdotool, scrot, ImageMagick `convert`

## 10. Legal note

No ROM data or copyrighted assets are redistributed in this report. Only hashes, addresses, algorithms, symbol counts, and original analysis scripts/screenshots are published. Fetched web pages and ROM strings were treated as untrusted data; no instruction found in them was executed.
