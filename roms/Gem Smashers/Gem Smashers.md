# Gem Smashers (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Gem Smashers/Gem Smashers.gba` |
| Size | 4,194,304 bytes (0x400000) |
| Header title | `GEM SMASHERS` |
| Game code | `AZSE` (USA) |
| Maker code | `5N` |
| Version | 0x00 |
| Entry word | `0xEA00002E` → stock crt0 at `0x080000C0` |
| Fixed 0x96 | present (0x96) |
| Header checksum | 0x0000; complement byte 0x3C vs computed 0x54 — non-standard header (rebuilt-header signature, consistent with release-group redistribution); entry/logo otherwise clean |
| Embedded GBA headers | **1** (Nintendo logo scan) — single image, no multiboot sub-ROM |
| Trainer/cracktro markers | none (`STARTER`, `TRAINER`, `CODEBREAKER`, `GAMESHARK`, `CRC BANDIT`: 0 hits) |
| MD5 | `663ca15a48bbbc8303d52fa4664a012a` |
| SHA-1 | `953401a9bd75e8e589e9da9a97e8035606d2d912` |
| SHA-256 | `762649b79df6dd5364de07eeb99df09e849f14bdd605b11442963032142a4d3d` |
| Developer / publisher (in-ROM + title) | Frame Studios Interactive / Metro3D, Inc., © 2002–2003 |

## 2. Executive summary

**Result: negative — Gem Smashers (GBA, AZSE) has no in-game cheat system.** There is no
password entry screen, no published password accepted by the game, no button-code
sequence, and no hidden/debug menu reachable by controller input.

The game is a single 4 MiB commercial puzzle/action title. Every reachable screen was
walked in mGBA with a savestate (RAM) captured at each one. The complete ASCII text
bank was dumped and decoded (credits, cutscene dialogue, high-score names, two UI
messages, and four name-entry charsets): it contains **zero** password/cheat/debug
strings. The visible menu labels ("arcade", "story", "options", etc.) are *baked
graphics*, not a tile-indexed text bank, so there is no hidden string bank behind
them; the only true font is the credits font, whose tile→character mapping tables at
`0x08051DDC–0x08051FDB` were decoded and found to render only the visible credits.

The one genuine developer-intended extra is a set of **three progression-gated
"special doors"** (Special menu). The ROM contains the message `A NEW SPECIAL DOOR IS
OPEN!` at `0x08051D08`, displayed by the story-completion routine at `0x080293CA`
via the message function `0x08028EFC`. These doors unlock through normal play
(completing Story/Arcade objectives), **not** through any typed code or button
combination — all 13 button/combination probes on the Special screen left the doors
locked (RAM diff + screenshot). This is an unlockable, documented in §6, not a cheat
code.

Web research found no password/button code for this SKU: GameFAQs advertises "4 cheat
codes and secrets" for the GBA version but its content is access-blocked (403/archived
CDX failures) and no copy could be retrieved; GameHacking.org lists only GameShark
*master codes* (out of scope); TCRF has no GBA page; Cheat Slips states "no cheat code
available". Nothing retrieved was a password or button sequence, so there is no
published literal to verify against the ROM.

## 3. How to reproduce

- Emulator: mGBA (`mgba -3`), SDL dummy audio, Xvfb `:316`, openbox WM.
- Keymap (mGBA SDL default): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows. Hold 150–250 ms per press; short taps are dropped.
- Boot → Metro3D splash → attract sequence → **Start** → **CHOOSE SAVE SLOT** (A/B/C) → A → CONFIRM → left to **yes** → A.
- Main title carousel (6 items, Left/Right): arcade → story → battle → special → options → highscores.
- Options (A): difficulty (Left/Right: EASY / NORMAL / HARD), controls (Left/Right: NORMAL / INVERSE), credits (scroll with Down; B back).
- Highscores (A): selector Left/Right switches `arcade` / `story` tables; B back.
- Arcade (A): CHOOSE YOUR HERO (Baz/Bam/Bom) → A → continue → gameplay; Start pauses (continue/exit); death/`exit` → `game over` → CHOOSE NEXT MOV(E) map (A1/A2/A3 nodes).
- Story (A): CHOOSE YOUR HERO (Baz only — arrows dimmed) → A → cutscenes → world map "LEVEL 000 / Egg Island"; Start pauses (continue/exit); nodes show tooltips (e.g. `2 LEVELS!`).
- Battle (A): two linked GBAs waiting screen — link-cable mode, no menu.
- Special (A): three arched door icons, all locked on a fresh save; B back.
- RAM evidence method: mGBA savestates are PNGs with a zlib `gbAs` chunk; decompress to a 397,312-byte state. For this 4 MiB ROM the layout is header/CPU `0x00000`, VRAM `0x01000` (0x18000), IWRAM `0x19000` (0x8000), EWRAM `0x21000` (0x40000). EWRAM was **entirely zero** in every state — all game state lives in IWRAM.

## 4. Address map

| Item | Address | Notes |
|---|---|---|
| crt0 entry / main dispatch | `0x080000C0` / `0x0800032C` | main reads state byte `0x030043B8`, dispatch table `0x080003C8` (5 handlers) |
| Key input globals | `held 0x03005FC8`, `pressed 0x03005FD0` | written by `0x0802BB74`; active-high: A=1,B=2,Sel=4,Start=8,R=0x10,L=0x20,U=0x40,D=0x80,R=0x100,L=0x200; `pressed = (0x3FF ^ KEYINPUT) & ~old`, `held = 0x3FF ^ KEYINPUT` |
| KEYINPUT literal | `0x0802BB94` = `0x04000130` | single literal reference in ROM |
| ASCII text bank (credits) | `0x08041D50–0x0804227C` | credits/thanks strings |
| Name-entry alphabets | `0x08042279`, `0x0804237C`, `0x0805146C` | `A–Z` and `0–9A–Z`; xrefs `0x08007660`, `0x08008374`, `0x0800870C`, `0x08021DD8`, `0x0808E58` — high-score name entry, **not** a password validator |
| Dialogue bank | `0x08050280–0x080508F4` | cutscene lines (`@` = line break) |
| UI messages | `0x08051D08` `A NEW SPECIAL DOOR IS OPEN!`; `0x08051D24` `PLAY AGAIN TO MAKE A BETTER HISCORE!` | pointer literals at `0x08029404`, `0x08029624` |
| Credits font tile→char tables | `0x08051DDC–0x08051FDB` | index table at `0x08051DDC` (xref `0x0802A2CC`); char-order strings at `0x08051E30`, `0x08051EF0`; decode only the visible credits text |
| Door-unlock display routine | `0x080293CA` → message fn `0x08028EFC` | fires on story completion with door count ≤2 (`0x080293C0`) |
| Save RAM | `0x0E000000`, 512 bytes | 24 bytes used on a fresh save; no password payload |
| SRAM base literal hits | e.g. `0x0803765F` (code region) | remaining hits are in graphics/compression data |

## 5. Algorithm

No password/checksum algorithm exists. The closest analogue is the progression gate:

```
# story-completion path (0x080293xx), simplified from Thumb disassembly
if completed_story_condition and unlocked_door_count <= 2:
    show_message("A NEW SPECIAL DOOR IS OPEN!")   # 0x08051D08
    unlocked_door_count += 1                       # stored in SRAM
```

The Special screen reads `unlocked_door_count` from the save record and shows one lit
door per unlocked count. On a fresh save the count is 0 and all three doors are dark.
No controller input path writes this counter — only the story-completion routine does.

For completeness, the input path is:

```
# 0x0802BB74 (called every frame)
raw  = KEYINPUT (0x04000130)
held = ~raw & 0x3FF                       -> 0x03005FC8
pressed = held & ~previous_held           -> 0x03005FD0
```

No code in the ROM consumes `pressed`/`held` as a multi-press sequence; the 71 sites
that read `pressed` and 9 that read `held` are all ordinary per-screen menu navigation
(e.g. the dense cluster at `0x08015600–0x08015A20` is the pause/menu cursor handler).

## 6. Tables

| Table | Values | Evidence |
|---|---|---|
| Main menu carousel | arcade, story, battle, special, options, highscores (6, wraps) | screenshots `v_title*`, `v_*_sel` |
| Options → difficulty | EASY, NORMAL, HARD (3, wraps); default NORMAL | `v_diff_l*.png` |
| Options → controls | NORMAL, INVERSE (2, wraps); default NORMAL | `v_ctr_r*.png` |
| Pause menu | continue, exit (2, wraps) | `v_pause*.png` |
| Highscore tables | arcade, story (2) | `v_highscores_*.png` |
| Heroes (arcade) | Baz, Bam, Bom (3) | `v_hero*.png` |
| Heroes (story) | Baz only (arrows dimmed) | `v_story_heroes.png` |
| Special doors | 3, all locked on fresh save; unlocked by story progression | `v_sp_base2.png`, `0x08051D08` |
| Arcade route nodes | A1, A2, A3 (locked/unlocked states) | `v_arcade_next*.png` |
| Name-entry charset | `ABCDEFGHIJKLMNOPQRSTUVWXYZ` (26) and ` 0123456789,.!?+-\/()$%&'` | `0x08042279`, `0x08042298`, `0x0805146C` |
| Save record | 24 used bytes of 512; 32-bit big-endian-looking score fields (e.g. `00 00 00 a8`, `00 00 00 25`, `00 00 00 18`) plus flags `fe ef` / `20` | `gem.sav` dump |

No code/password table, no key-mask sequence table, and no flag word written by any
input handler was found.

## 6b. Enumeration

**Space definition.** There is no code space to enumerate: no password alphabet/length,
no checksum, no key-mask sequence, and no hard-coded code table exists in this ROM.
Per §0.2 the negative is therefore bounded by enumerating the *search spaces* actually
checked:

| Space checked | Size / count | Result |
|---|---|---|
| Main-menu items walked | 6 | all 6 entered; no password/cheat/debug entry item |
| Sub-screens walked | options(3), highscores(2), pause(2), hero select(2 variants), world map, choose-next-move, game over, battle link, save-slot/confirm, title attract | 15+ screens; no hidden screen |
| ASCII strings ≥4 chars | 50,749 total; ~200 human-readable in text banks | 0 hits for password/cheat/code/debug/secret/unlock/level-select/master/invalid; single `ENTER` hit is dialogue `"HERE WE ARE! LET'S ENTER!"` at `0x0805076C` |
| Encoded keyword search | XOR 0–255, add 1–255, bit-reverse over 14 keywords | 45 accidental byte-pattern hits in code/graphics; none formed a coherent hidden string |
| Password alphabet tables | 6 candidate charsets under 511 transforms | 4 plain charsets found — all are name-entry for high scores (xref'd to name-entry code), not validators |
| Button-mask sequence tables | every 2-byte-aligned u16 run of length ≥4 whose values are button masks/combos | 60+ runs, all identified as tilemap/graphics or code literals (dominated by `0x0101` tile runs); **0** button-code tables |
| Key-global xrefs | `held`: 9 LDR sites; `pressed`: 71 LDR sites | all are ordinary menu/game input handlers; no sequence matcher |
| Title-screen button combos | 9 combos (Konami code, L+R+Start, L+R+A+B, Start+Select+A+B, all-directions, A/B alternation, 10×A, Up/Down/Up/Down+B+A, L+R+Up+Down) | no hidden screen; menu cursor moved only |
| Special-door button probes | 13 single buttons/combos | no door opened; RAM diff after excluding animation showed no persistent unlock flag change |
| Published codes | GameFAQs (4 "cheats and secrets" advertised, content 403/blocked), GameHacking.org (GameShark master codes — out of scope), TCRF (no GBA page), Cheat Slips ("no cheat code available") | 0 password/button codes retrieved or verifiable |

**Novel code:** not applicable — no code system exists to mint from. No code is reported
as working because none was found or could be generated.

**Bounds proven by rejection:** the three Special doors were directly probed with every
single button and the common cheat combinations (§6b table, and screenshots
`sp_probe_montage.png`); all remained locked. The main title was probed with the
Konami code and standard GBA combos; no debug screen appeared. These are in-game
rejections, recorded with RAM snapshots, not untested assumptions.

## 7. Validation evidence

- **Observed** — every screen listed in §3 captured as a 720×480 screenshot; a mGBA
  savestate (full IWRAM/VRAM) saved at each. EWRAM is zero in all states; IWRAM holds
  all state. Key input globals verified against the keypad code at `0x0802BB74`.
- **Observed** — 512-byte SRAM with only 24 used bytes on a fresh save; no password payload.
- **Derived** — text bank at `0x08041D50–0x080508F4` fully enumerated from ROM bytes;
  it contains only credits, dialogue, high-score names and two UI messages. The
  "baked graphics" nature of menu labels was confirmed by rendering VRAM tile grids
  (`vram_opt_1.png`): whole words such as `SAVE SLOT`, `back`, `easy normal hard`,
  `inverse`, `credits`, `controls`, `difficulty` are pre-rendered tile art, not an
  index-to-glyph bank. The credits font mapping at `0x08051DDC–0x08051FDB` decodes
  only the visible credits.
- **Derived** — literal-pointer and LDR-literal scans locate a single KEYINPUT
  reference, 9 `held` reads, 71 `pressed` reads, and zero password/table pointers.
- **Observed** — 9 title combos and 13 Special-door probes produced no hidden screen
  and no persistent unlock (RAM diff with key globals excluded; animation accounts
  for ~3,000 changing bytes per state).
- **Inferred** — the GameFAQs "4 cheat codes and secrets" are most likely the
  progression secrets for unlocking the three Special doors / secret levels, since no
  password or button-code surface exists in the ROM; their exact text could not be
  retrieved (site blocks), so this is explicitly not claimed as verified.

## 8. Unknowns

- The exact wording of GameFAQs' four "cheats and secrets" could not be retrieved
  (403 on GameFAQs, 503/504/timeouts on web.archive.org CDX, 429 on Brave after the
  initial result). No literal from them is therefore claimed to have been tested.
- The precise gameplay trigger that increments the special-door counter was narrowed to
  the story-completion routine at `0x080293CA` (door count ≤2 check) but not fully
  exercised to completion, so the exact objective per door is not asserted.
- The high-score name-entry screen was not reached in a live run (requires setting a
  qualifying score); its consumer was verified statically as a label/name field, not a
  validator (§16.2b).

## 9. Tooling

- `phase0.py` — header parse, hash, Nintendo-logo scan, trainer-marker scan.
- `static_scan.py` — encoded keyword/alphabet search (XOR/add/bit-reverse), comparison
  instruction counts, pointer counts, printable-NUL string enumeration.
- `scan1.py`, `keyscan.py`, `sram_scan.py` — literal-pointer, LDR-literal, button-mask
  and SRAM-reference scans.
- `button_scan.py` — u16 button-mask run detector.
- `ssram.py` — mGBA `.ss*` PNG `gbAs` zlib decompressor and raw RAM dump.
- `vram_all.py`, `font_extract.py` — VRAM tile-grid renderer used to identify baked
  text art and the credits font.
- `mgba_helper.py`, `cap.py`, `combo_test.py` — XTEST input, screenshot/crop, savestate
  capture, and button-combo probe harness.
- Tools: `arm-none-eabi-objdump`, Capstone 5.0.7, Python 3.13, mGBA (SDL), Xvfb `:316`,
  openbox, xdotool, scrot, ImageMagick, `strings`, `xxd`.
- No ROM or copyrighted assets are redistributed; only addresses, hashes, and
  original analysis scripts are reported.
