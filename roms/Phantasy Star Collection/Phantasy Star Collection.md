# Phantasy Star Collection (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Phantasy Star Collection.gba` (8,388,608 bytes = 0x800000) |
| Header title | `PHANTASYSTAR` (0x080000A0) |
| Game code / maker | `AYCE` / `78` (serial AGB-AYCE-USA; CRC32 `E5A7FE17` matches the published USA image) |
| Version / complement / checksum | 0x00 / 0x1E / 0x0000 (rebuilt-header artifact; §16.1) |
| MD5 | `af7e218eb4a7f28f1887b3504647854e` |
| SHA-1 | `9f2dc591c9b1526f9f965b1c375fb4ea7101fd16` |
| SHA-256 | `6747a17af7ccb082bab1f2a8ed7d88952ab93879d93173b12331b1e5e8ec1c4e` |
| Save hardware | SRAM, 8 KiB (`Phantasy Star Collection.sav`, 8192 bytes, blank `0xFF` at first boot) |

**Embedded GBA headers (Nintendo-logo scan, 4 hits):** sub-image base is derived from the logo hit, not
from a fixed offset (§5.4b).

| Base (ROM addr) | Title | Role | Identification evidence |
|---|---|---|---|
| 0x08000000 | `PHANTASYSTAR` / AYCE / 78 | Digital Eclipse shell + game-select | credits ASCII at 0x08017C48 |
| 0x08080000 | blank / 01 | **Phantasy Star III** | text bank reversed in ROM: `Laya-Orakio` @0x0EE890r, `Aron,welcome` @0x0F35EAr, `Wren-type` @0x0F7545r |
| 0x08390000 | blank / 01 | **Phantasy Star II** | reversed `SEGA MEGA DRIVE (C)SEGA 1990.JAN PHANTASY STAR 2` @0x3D3C74, `PHANTASY STAR 2` @0x3D360B |
| 0x08738000 | `PHANTASYSTAR` / 01 | **Phantasy Star I** | item names @0x77A077 (`WOODCANE`, `SHT.SWD`,…), `TMR SEGA` @0x77A2C4, dialogue @0x77A592+ |

PS IV is not present — consistent with the documented GBA three-game compilation.
No patch/trainer code was found: the entry word is the stock `0xEA00002E`, and the
first 4 KiB is a normal crt0 (no cracktro signature, §16.1).

## 2. Executive summary

There is **no password/code-entry system** anywhere in this cartridge. All three
games use battery-backed SRAM save slots (PS1: `START`/`CONTINUE`; PS2: `NEW GAME`/
`CONTINUE`/`ERASE GAME`, two slots; PS3: four-position save check plus a text-speed
option). A whole-ROM literal search for `PASSWORD`, `CHEAT`, `DEBUG`, `UNLOCK`,
`BONUS`, `GALLERY`, `OPTION`, `MASTER CODE` in ASCII, reversed ASCII, `+0x20`
shifted ASCII and UTF-16LE returned **0 hits**; the only `SECRET` hits (2) are the
PS1 inventory item and a dialogue word. The shell's UI labels are baked into
graphics (its two 96-byte font tables at 0x0802E900 / 0x0802E9AC do not decode any
stored string), so the negative rests on screen enumeration plus the ASCII text
bank at 0x08017C48, which contains only the credits.

The one genuine **developer-intended button code** is the **game selector** on the
"Phantasy Star" title screen: **Up** and **Down** change the selected game, and
**Select** is an undocumented alias for Down. This is the published "press Up or
Down when the picture of Phantasy Star appears" code; it was verified statically
(the exact key-mask branches and the game-index variable) and dynamically in mGBA,
including wraparound, the undocumented Select alias, and rejection of all other
inputs. An additional undocumented combo, **A+B+Select+Start**, returns to the
"Phantasy Star Collection — Press Start" splash.

No hidden debug menu, sound test, level select, or unlockable was reachable: every
shell and in-game screen was walked with RAM evidence, and each menu's item count
was read from its selector (PS3 pause = 2, PS2 pause = 2, PS2 Start Game = 3,
PS3 option = one 9-way row, shell game select = 3).

## 3. How to reproduce

* Emulator: mGBA (SDL) under `Xvfb :316`, `SDL_AUDIODRIVER=dummy`, 3× scale.
* Keymap (mGBA default): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
  Select=`BackSpace`, D-pad = arrow keys. Hold keys 100–200 ms.
* Boot path: boot logo → SEGA logo → Digital Eclipse credits → legal notice →
  "PHANTASY STAR COLLECTION / PRESS START" splash → **Start** → "PHANTASY STAR"
  logo with planet (game select).
* At game select: **Up** / **Down** / **Select** change the logo; **Start** or **A**
  launches the highlighted game. Read EWRAM `0x0202436C` in a savestate
  (`gbAs` chunk, decompressed) for the index: 0=PS1, 1=PS2, 2=PS3.
* Published code tested: Up/Down at game select (accepted).
* Undocumented inputs tested: Select at game select (accepted, same as Down);
  A+B+Select+Start at game select (returns to splash); Left/Right/L/R/B at game
  select (rejected — index unchanged).
* Savestates used: slot 2 = game select (PS1 highlighted), slot 3 = PS1 title,
  slot 4 = PS2 title, slot 5 = collection splash.

## 4. Address map

| Address | Meaning | Evidence |
|---|---|---|
| 0x08000000 | shell image base / stock entry `0xEA00002E` | header |
| 0x080005E0–0x080006E2 | shell game-select input handler | disassembly |
| 0x08000602 / 0x08000674 | Up mask `0x40` / Down+Select mask `0x84` tests | disassembly |
| 0x08000616–0x0800061E | Up: `index--` | disassembly |
| 0x08000684–0x0800068E | Down/Select: `index++` | disassembly |
| 0x08000690–0x080006A2 | wrap: `<0 → 2`, `>2 → 0` | disassembly |
| 0x080008C0–0x080008DA | A+B+Select+Start (`0x0F`) → return-to-splash | disassembly |
| 0x08017C48 | ASCII credits text bank (single pointer @0x0D20) | pointer scan |
| 0x0802E900 / 0x0802E9AC | shell font index→glyph tables (96 bytes each) | byte dump |
| 0x0202436C | selected game index (0/1/2) | literal @0x08000668, 0x080006D8; RAM diff |
| 0x02024370 | shell's mirrored KEYINPUT (`ldrh`) | literal @0x0800066C; disassembly |
| 0x02024364 | shell's mirrored "pressed" buttons | literal @0x080008E4 |
| 0x03003D98–0x03003D9A | per-logo enable bitmask (PS1/PS2/PS3) | RAM diff on Up |
| 0x0202D08 | PS3 message-scroll-speed setting, 0..8 (default 4 = "5") | RAM diff on Left/Right |
| 0x08080000 / 0x08390000 / 0x08738000 | PS3 / PS2 / PS1 sub-image bases | logo scan |

File offset = ROM address − 0x08000000 for the shell; sub-image strings are at
`0x08000000 + file_offset` because the images are mapped contiguously.

## 5. Algorithm

Shell game-select handler (reimplementation of 0x080005E0):

```
keys = *(u16*)0x02024370              # mirrored KEYINPUT, active-low
idx  = *(u32*)0x0202436C
if keys & 0x40:            # UP
    play_sfx(); idx -= 1
elif keys & 0x84:          # DOWN (0x80) OR SELECT (0x04)
    play_sfx(); idx += 1
if idx < 0: idx = 2
if idx > 2: idx = 0
*(u32*)0x0202436C = idx
for i in 0..2: logo_enable[i] = (idx == i) ? 0x80 : 0x00
```

The hidden reset branch at 0x080008C0:

```
if (*(u16*)0x02024364 & 0x0F) == 0x0F:   # A+B+Select+Start simultaneously
    push_screen_state(); sfx(); call [0x0801883C+16]   # back to collection splash
```

## 6. Tables

**Key masks (shell, active-low):**

| Mask | Buttons | Effect at game select |
|---|---|---|
| 0x40 | Up | index − 1 (wraps) |
| 0x80 | Down | index + 1 (wraps) |
| 0x04 | Select | index + 1 (undocumented alias) |
| 0x08 | Start | launch selected game |
| 0x01 | A | launch selected game |
| 0x0F | A+B+Select+Start | return to collection splash (undocumented) |
| 0x20,0x10,0x200,0x100,0x02 | Left, Right, L, R, B | no effect (rejected) |

**Game index:** 0 = Phantasy Star, 1 = Phantasy Star II, 2 = Phantasy Star III.

**Screen enumeration (all walked, RAM/screenshot evidence):**

| Screen | Entry | Selector read | Result |
|---|---|---|---|
| Boot GBA / SEGA / Digital Eclipse credits / legal | power-on | — | linear, no input branch to hidden screen |
| Collection splash "PRESS START" | after legal or hidden reset | timers only (EW 0x24368) | no menu from any single button |
| Game select (PHANTASY STAR logo) | Start at splash | EW 0x2436C = 0/1/2 | 3 games, 4 images total (shell + 3) |
| PS1 title START/CONTINUE | launch game 0 | cursor 2-way | CONTINUE with blank SRAM does nothing |
| PS1 intro + overworld + battle (observed) | START | — | standard RPG screens |
| PS2 title + intro + "NEW GAME/CONTINUE/ERASE GAME" | launch game 1 | cursor cycles mod 3 | 2 save slots, no password |
| PS2 overworld + PAUSE/CONTINUE/QUIT | new game | cursor cycles mod 2 | no extra entry |
| PS3 credits + save check + "Slow 1…9 Fast" option | launch game 2 | EW 0x0202D08 = 0..8 | one 9-way row |
| PS3 intro + PAUSE/CONTINUE/QUIT | A at option | cursor cycles mod 2 | no extra entry |

**Published-code verification:**

| Source | Claim | Result |
|---|---|---|
| GameFAQs / Cheating Dome | "Press Up or Down when the picture of Phantasy Star appears" to select Episodes 2/3 | **Verified** statically (0x08000602/0x08000674) and in emulator (index 1/2, logo change) |
| GameFAQs | PS2 "Pause + hold B = slow motion"; "mash B to avoid encounters"; item-dup glitches | Classified as gameplay glitches (GameFAQs labels them Secrets/Glitches), not developer code systems; not part of the verified button-code surface |
| ROMSFUN / SuperCheats / GameHacking.org | CodeBreaker/GameShark codes | Out of scope (memory-edit codes), not tested by design |
| GameFAQs "Save State Hacking Guide" references | save-state editing | Out of scope (memory edit), not tested by design |

## 6b. Enumeration

**Space definition.** The button-code system has a single 2-bit state variable
(3 valid values, 0–2) at `0x0202436C`, driven by pressed-key masks. The complete
action space is:

* accepted inputs at game select: Up (decrement), Down (increment), Select
  (increment), Start (launch), A (launch), A+B+Select+Start (splash reset);
* rejected inputs: Left, Right, L, R, B, all single/triple combinations that do
  not match a branch above (index and screen unchanged);
* sequence lengths: 1 press for every action; the state wraps with period 3.

**Novel / unpublished code.** The Select key is **not** in any published list
(GameFAQs says only Up/Down). Pressing **Select alone** at the game select screen
from the default PS1 state moved `0x0202436C` from `0x00` to `0x01` and changed the
logo to "Phantasy Star II" (screenshot `btn_Select_c.png`, savestate RAM read). The
undocumented **A+B+Select+Start** combo was also pressed in-game and returned to
the collection splash (`combo4_after_c.png`). Neither appears in the consulted
GameFAQs/Cheating Dome/VGChartz-style lists.

**Bounds proof by rejection.**

* Left, Right, L, R and B each left the index at `0x00` and the screen unchanged
  (`btn_Left/Right/L/R/B_c.png`).
* Up×3 from 0 gave `0x00 → 0x02 → 0x01 → 0x00`; Down×3 gave
  `0x00 → 0x01 → 0x02 → 0x00` (`bnd_*.png` + RAM reads). No 4th game exists; the
  shell sets up exactly four images (collection logo + three games) at
  0x080056E–0x080059A.
* The PS3 option is a closed 9-value space: Left from 0 wrapped to 8, Right from
  8 wrapped to 0; read-back of `0x0202D08` confirmed all nine values exactly once
  (`ps3_opt_left/right`).
* Menu bounds: PS2 Start Game and both pause menus were walked past their last
  entry and wrapped to the first; no hidden item was revealed.

**Negative-result boundary.** The whole 8 MiB was searched for password/debug
keywords under four encodings (counts in §2), all reachable screens were walked,
and the shell's only ASCII text bank (0x08017C48, one pointer) and both font
tables were inspected. No password validator, key-mask sequence table beyond the
documented selector, code table, or debug-menu entry exists in this surface.

## 7. Validation evidence

| Claim | Type | Evidence |
|---|---|---|
| Game index at 0x0202436C, 3 values | Observed | savestate `gbAs` RAM reads: `ct_title=00`, `ct_down2=01`, `ct_up=02`; logo screenshots |
| Up/Down/Select branches and masks | Derived | Thumb disassembly 0x08000602/0x08000674; literals verified with `struct.unpack_from` |
| Undocumented Select alias | Observed | `btn_Select_c.png` (PS2 logo) + index `0x01` |
| Undocumented A+B+Select+Start reset | Observed | `combo4_after_c.png` (collection splash) |
| Wraparound bounds | Observed | `bnd_*.png` + index read-back |
| No password system | Derived + bounded negative | 0 hits for 8 keywords × 4 encodings; 4 images; 8 KiB SRAM; all screens enumerated |
| PS3 speed option 0..8 | Observed | `ps3_opt*.png` + EW 0x0202D08 read-back |
| Component games | Derived | reversed Genesis header strings and item/dialogue banks at each sub-image base |

Evidence files (`/tmp/phantasystar/`): `ct_*.raw`, `bnd_*.png`,
`btn_*.png`, `combo*.png`, `ps1_*.png`, `ps2_*.png`, `ps3_*.png`, `all_strings.txt`.

## 8. Unknowns

* The original Genesis-era 68000 code inside each sub-image was not exhaustively
  disassembled for cut features from the original cartridges; the engagement
  boundary is the GBA shell and the reachable in-game surfaces listed in §6.
* Shell UI text is rasterised into image data rather than stored as decodable
  strings; the negative in §6b is therefore based on the enumerated input surface
  and the ASCII credit bank, not on a complete string table of UI labels.
* The PS2 "hold B in pause" item is a published gameplay glitch (GameFAQs
  classifies it as a Secret), not a developer code path; it was not required to
  characterise the button-code system, which is fully enumerated above.

## 9. Tooling

* `strings -t x -n 4`, `grep -abo`, Python byte/pointer scans, Capstone 5.0.7
  Thumb literal scanning, `arm-none-eabi-objdump -M force-thumb`.
* mGBA SDL (`mgba -3`) under `Xvfb :316` + `openbox`, `xdotool` XTEST input,
  `scrot` + ImageMagick crops.
* Savestate RAM reader: mGBA `.ss1` PNG `gbAs` chunk → `zlib.decompress` →
  397,312-byte state; IWRAM at raw `0x19000`, EWRAM at `0x21000` (§16.13).
* No ROM or copyrighted assets are redistributed; only addresses, hashes,
  algorithms and observations are published.
