# World Tennis Stars (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/World Tennis Stars/World Tennis Stars.gba` |
| Size | 4,194,304 bytes (`0x400000`) |
| Header title | `WORLD TENNIS` (`0xA0`) |
| Game code | `AWCE` (`0xAC`) |
| Maker code | `7M` (`0xB0`) |
| Version / complement / checksum | `0x00` / `0x34` / `0x0000` |
| Fixed byte / main unit / device | `0x96` / `0x00` / `0x00` |
| Entry word | `0xEA00002E` — stock GBA branch, no cracktro patch (§16.1) |
| MD5 | `b705e04f4571cc9e8801900b4e0243fd` |
| SHA-1 | `c668815a2ccf0bc6c3816d0947218661437449bc` |
| SHA-256 | `73494978a3e873dcfa5847b73cd9ff5154181b0aff302460c1bcedd282a25811` |
| Publisher (observed) | Ignition Entertainment Limited, © 2002 (boot logo); AIA credits |

All addresses below are for this exact hash.

## 2. Executive summary

**Bounded negative: this retail GBA image contains no developer-intended cheat system.**
There is no password screen, no cheat-code entry UI, no alphabet or checksum table, no
published/latent password list, no hidden or debug menu, and no unlockable character,
court or mode. The complete reachable screen set was walked in mGBA with screenshots,
and the complete set of UI text (both ASCII banks plus the tile/bitmap-encoded text
banks) was enumerated. Every interactive choice is available from a fresh boot.

One real button combination exists: holding **A+B+Select+Start** anywhere sets the IWRAM
flag word at `0x03001C9C` to `1` (proved by savestate RAM read, §7). It is a generic
input helper called from 25 sites including the main loop — most likely a soft-reset /
quit signal — not a cheat. No reader of that flag was found in the ROM, and no visible
game state changes when it is set (other than the ordinary effect of holding Start).

Web reconnaissance of published codes returned no data: search engines gave generic
fallback results, GameFAQs/TCRF returned HTTP 403, and archive lookups 404'd. This is
recorded as *recon attempted, no codes obtained*, not as evidence of absence.

## 3. How to reproduce

```
Xvfb :315 -screen 0 1024x768x24 &
openbox --display :315 &
DISPLAY=:315 SDL_AUDIODRIVER=dummy mgba -3 game.gba &
```
(the copy `game.gba` in `/tmp/opencode/worldtennisstars` is byte-identical to the ROM;
all `.sav`/`.ss*` artifacts were kept in that work dir, none in the ROM folder).

mGBA SDL keymap used: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`,
D-pad = arrow keys. Keys held 120–300 ms.

Menu path actually walked (all screenshots in `/tmp/opencode/worldtennisstars/`):

1. `s_intro_skip.png` — Ignition logo → character select
2. `s_mainmenu.png` — MAIN MENU: **Singles / Championship Mode / Options / Head To Head** (4 entries)
3. `s_walk2.png`, `char_1.png`…`char_3.png`, `down_1.png`, `down_2.png` — Singles character select; the 2×3 grid cycles through exactly 6 characters (VIKKI, DANNY, JIM, KARL, NAOMI, SU)
4. `court_1.png`…`court_10.png` — COURT SELECT: **USA / ENGLAND / HAWAII / BELGIUM / JAPAN / PERU**, wraps after 6
5. `s_champ2.png` — gameplay (GAMES / SCORE HUD)
6. `s_pause.png` — PAUSED: RESUME / QUIT
7. `s_options.png` — OPTIONS: Difficulty / Music / SoundFX / Sets To Win / CREDITS (5 entries)
8. `s_credits.png`, `cf_montage.png` — 4 tile-encoded credit screens, developer crew only
9. `s_headtohead2.png` — HEAD 2 HEAD: "CONNECTING....." / "CANCEL"
10. `s_afterquit.png` — QUIT returns to the WORLD TENNIS STARS title

Combo test: `combo_state.py` holds A+B+Select+Start, then saves slot 3; `state3.bin`
is the decompressed `gbAs` chunk of `game.ss3`.

Published-code recon (all attempted, no results): GameFAQs cheats page (403),
TCRF (403), DuckDuckGo (bot challenge), Bing/Google (generic "world" fallback only),
Wayback Machine snapshot (404), cheatsguru (transport error).

## 4. Address map

| Address (ROM/asset) | Meaning |
|---|---|
| `0x08000000` | Entry branch `0xEA00002E`, stock crt0 |
| `0x08000410` | crt0 main pointer `0x08008559` (Thumb, → `0x08008558`) |
| `0x08001ABC` | Joypad reader: reads `0x04000130`, inverts to active-high, writes held `0x03000D54` and pressed `0x03000EE8` |
| `0x08008CA0`–`0x08008E44` | ASCII UI text bank A (menus, score, player names) |
| `0x0800B8C0`–`0x0800B8F0` | Pointer table into graphics/menu assets |
| `0x0800B8F4`–`0x0800B9C8` | ASCII UI text bank B (menu labels, link messages, Poor/Average/Good) |
| `0x0800B980`–`0x0800B9AC` | Pointer table → option strings in bank A (Difficulty/Music/SoundFX/Sets/Credits) |
| `0x080008F0` | Setter: `0x03001C9C = 1` |
| `0x080008FC` | Clearer: `0x03001C9C = 0` (no callers found) |
| `0x080084D8` | Button-combination gate (A+B+Select+Start), 25 BL xrefs |
| `0x08008558` | `main()` — sets up subsystems, then main loop |
| `0x08008660` | Main loop: `BL 0x08003B70`; `BL 0x080084D8` (gate) each frame |
| `0x08009E4` | Gate side-effect: clears state words at `0x0301230+0xDC` and `+0x10C` |
| `0x366398` / `0x3840AC` | Asset directory group names `TennisTitles` / `TennisMenu` (audio only) |
| `0xAE54` | `MultiSio010918` — link-library version string |

RAM (IWRAM, active high; key bits A=1 B=2 Select=4 Start=8 … L=0x200):

| Address | Meaning | Idle | Combo held |
|---|---|---|---|
| `0x03000D54` | held keys (upper bits `0xFC00` set by inversion) | `0xFC00` | `0xFC0F` |
| `0x03000EE8` | newly-pressed keys | `0x0000` | edge consumed by save |
| `0x03000F18` | input-context flag (gate selects branch) | `0x0000` | `0x0000` |
| `0x03001D14` / `0x03002D80` | alternate-context key buffers | `0` / `0xFC00` | `0` / `0xFC0F` |
| `0x03001C9C` | combo flag written by gate | `0x0000` | **`0x0001`** |

Savestate layout used for RAM reads: `game.ss1/ss2/ss3` are PNGs with a zlib `gbAs`
chunk; decompressed length 397,312 bytes; IWRAM begins at file offset `0x19000`
(so `0x0300xxxx` → `0x19000 + 0xxxxx`).

## 5. Algorithm

No password/checksum algorithm exists. The only algorithmic input handling found is the
button gate, which in Thumb pseudocode is:

```c
// 0x080084D8 — called every frame from main loop and from 24 UI sites
u16 held    = *(u16*)0x03000D54;   // active-high, upper 6 bits also set
u16 pressed = *(u16*)0x03000EE8;
u16 flag    = *(u16*)0x03000F18;   // input context selector

if (flag == 0) {
    if ((pressed & 0xF) != 0 && (held & 0xF) == 0xF) goto matched;
} else {
    if ((*(u16*)0x03001D14 & 0xF) && (*(u16*)0x03002D80 & 0xF) == 0xF) goto matched;
    if ((*(u16*)0x03001D16 & 0xF) && (*(u16*)0x03002D82 & 0xF) == 0xF) goto matched;
}
return 0;

matched:
    *(u16*)0x03001C9C = 1;   // BL 0x080008F0
    clear_state_words();     // BL 0x08009E4
    return 1;
```

`0xF` is the active-high mask A|B|Select|Start. This was confirmed dynamically:
with all four keys held, `held=0xFC0F` and `flag_0x1C9C=1`; without the combo both
low nibbles are zero.

## 6. Tables

**Complete referenced ASCII string inventory** (all 60 strings; every one is ordinary
UI/gameplay text — none is a password, cheat, debug label, unlock notice or code prompt):

- Bank A: `MAIN MENU`, `Singles`, `Championship`, `HEAD 2 HEAD`, `5 Sets To Win`,
  `3 Sets To Win`, `1 Set Wins`, `Credits`, `SoundFX On/Off`, `Music On/Off`,
  `Difficulty Hard/Medium/Easy`, `Name:`, `Speed:`, `Power:`, `GAME`, `ADVANTAGE`,
  `DEUCE`, `LOVE`, `40/30/15/0`, `KARL`, `NAOMI`, `JIM`, `SU`, `DANNY`, `VIKKI`,
  `0`–`6`, ` G`, ` A`, `00`, `SETS`, `GAMES`, `SCORE`, `-`, `PAUSED`, `RESUME`,
  `QUIT`, `LINK ERROR !`
- Bank B: `Singles`, `Championship Mode`, `Options`, `Head To Head`,
  `Connecting.....`, `Cancel`, `Connected !`, `Press The A Button!`,
  `Get Ready !`, `Poor`, `Average`, `Good`

**Tile/bitmap-encoded text banks** (no ASCII encoding exists in the ROM — confirmed by
raw, case-insensitive, `+0x20`, XOR-`0x80`, UTF-16LE/BE and simple offset scans):
- COURT SELECT + 6 court names: USA, ENGLAND, HAWAII, BELGIUM, JAPAN, PERU (`court_montage.png`)
- Credits: 4 screens listing Ignition/AIA crew (Jim Bagley, Adrian Scotney, Steve Cowell, Su Bagley, Sergej Krawcenko, Ellen Fuog, Ken Gratz, Shane Takahashi, Vijay Chadha, Eileen Shapiro, Kelly-ann Styles, Peter Rollinson, Danny Chahley, Jay Sreenivasan, Andy Chala, Joy Phieu, …) (`cf_montage.png`, `credit_1.png`)
- Every frame of the credit scroll was captured; no cheat/debug/easter-egg message appears.

**Character roster (6):** VIKKI, DANNY, JIM, KARL, NAOMI, SU. Exactly six portrait cells
(2 columns × 3 rows) and exactly six name strings; grid wraps at 6, no hidden 7th slot.

## 6b. Enumeration

This is a **bounded negative**, not a code-generation result: the accepted cheat space is
empty. Counts that bound the claim:

| Search space checked | Count / result |
|---|---|
| Cheat keywords (`password, cheat, debug, secret, unlock, code, generator, level select, entry, valid, invalid, wrong, correct, congrat, hidden, bonus, special`) × ASCII, `+0x20`, UTF-16LE/BE, whole 4 MiB | **0 hits** for all 17 words in all encodings |
| Password alphabet strings (`A-Z`, `0-9`, `A-Z0-9`, lowercase) | **0 hits** |
| Human-readable word-like ASCII runs anywhere in ROM (full 4 MiB scan) | 2,183 runs; all are the two UI banks, the two audio group names, or compressed-art noise — no hidden message |
| Pointer-referenced UI strings | 60 strings; **0** cheat/password/debug entries |
| Character roster | **6** characters; **0** hidden/unlockable |
| Court roster | **6** courts; **0** hidden/unlockable |
| Main-menu entries | **4**; Options entries **5**; Pause entries **2** — no hidden entry |
| Button-mask table scan, loose masks, whole ROM | 72 candidate runs — all palette/tile/audio false positives |
| Button-mask table scan, strong (direction/shoulder) masks, whole ROM | 38 candidate runs — all false positives |
| Same scan restricted to the code region `0x0000`–`0x9000` (where a real table would live) | **0** candidates |
| Asset directory groups | **2** (`TennisTitles`, `TennisMenu`), 17 `.wav` names, **0** debug/secret assets |
| Save memory | `game.sav` = **0 bytes** after menus, a full match and quit; **0** references to SRAM base `0x0E000000` in the code region — no persistent unlock flags |
| Validator/checksum call sites (`strcmp`/`memcmp`-style comparisons against user input) | No user-input text field exists in any screen; every comparison in the UI code is against fixed menu strings |

**Novel code / rejection bounds:** not applicable — there is no code system to mint or
reject. The equivalent exercise was performed on the only input-combination gate: a
combination *not* documented by any publisher (A+B+Select+Start) was entered on the real
screen and its effect verified in RAM (`0x03001C9C` toggles `0→1`), while the
negative bound was established by the idle RAM read (`0x03001C9C=0`, held low nibble
`0x0`). A visible menu effect was **not** observed, so the gate is classified as a
generic input helper, not a cheat.

## 7. Validation evidence

- **Observed (emulator):** every screen in §3, screenshots preserved on disk; 6
  characters, 6 courts, 4 menu entries, 5 options, 3 pause labels, 4 credit screens.
- **Observed (RAM/savestate):** `held=0xFC0F` and `0x03001C9C=0x0001` with A+B+Select+Start
  held (`state3.bin`); idle `held=0xFC00`, `0x03001C9C=0x0000` (`state1.bin`);
  screen transition changed 3,093 bytes in 49 clusters, including IWRAM `0x19120`–`0x1961F`
  (`state1.bin` vs `state2.bin`).
- **Derived (disassembly):** joypad buffer addresses and active-high encoding
  (`0x08001ABC`); gate condition and mask `0xF` (`0x080084D8`); setter at `0x080008F0`;
  main-loop call site `0x08008664`.
- **Inferred / unknown:** purpose of `0x03001C9C` downstream. A whole-ROM scan found
  only two literal loads of that address, both writers (setter and an uncalled clearer);
  no direct reader was located. A live test produced no visible state change, so the
  most likely reading is a soft-reset/quit signal, but this is **not proven**.
- **Negative results** are bounded by the counts in §6b, not by "I did not find it".
  The tile-encoded text banks were enumerated frame-by-frame before concluding absence.

## 8. Unknowns

- Downstream consumer of `0x03001C9C` (no direct reader found; could be accessed via a
  computed base pointer or a DMA/side path). Its visible effect was nil in the tests run.
- Whether a complete Championship playthrough writes any save data — the 0-byte `.sav`
  and zero SRAM references in code strongly suggest no save at all, but a full 5-set
  championship was not played to completion.
- No published code list was obtainable (all web sources blocked), so "not in any
  published list" could not be checked against an external list; it is moot because no
  code format exists.

## 9. Tooling

`strings -t x`, `grep`, Python scanners (keyword/alphabet/button-mask/partial-offset
searches), `arm-none-eabi-objdump -M force-thumb`, Capstone (LDR-literal and BL xref
scans), mGBA 0.10.5 under Xvfb `:315` with `SDL_AUDIODRIVER=dummy`, `xdotool`, `scrot`,
ImageMagick montage, and mGBA savestates with a Python `gbAs` zlib/diff reader. Scripts
and all evidence images are in `/tmp/opencode/worldtennisstars/` only.

**Legal note:** no ROM image, extracted graphics, music, or game text is redistributed by
this report; only hashes, addresses and original analysis are published.
