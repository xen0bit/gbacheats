# Millipede / Super Breakout / Lunar Lander (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Millipede - Super Breakout - Lunar Lander.gba` |
| Size | 4,194,304 bytes (0x400000) |
| Header title | `MILLIPEDECOM` |
| Game code / maker | `B62E` / `20` (Destination Software / DSI Games, Gravity-i) |
| Version | 0x00 |
| Entry word | `0xEA00002E` (stock ARM `b 0x080000C0` — no cracktro) |
| Fixed 0x96 / complement | `0x96` / `0x8C` |
| Header checksum | `0x0000` (normal rebuilt-header artifact; complement intact) |
| MD5 | `1739ddafb47c12da4709e9529c103d68` |
| SHA-1 | `a520e5fc2fe3605c58ef4844f7fccfe7f8ddf5d1` |
| SHA-256 | `c0ffe65ffa6c612cdfe71c00207928fc346ab14b1bf5751a3c47a6d08ab8776c` |

**Phase 0**: `file` reports a single GBA image. A full scan of the entire 4 MiB for the
156-byte Nintendo logo found exactly **one** header (file 0x0), so this is a single
integrated compilation, *not* a concatenated 3-in-1 multi-image pack. No appended
trainer, patch stub, or second header exists. The three component games
(Millipede, Super Breakout, Lunar Lander) share one shell/UI; there is no per-game
ROM base to chase. The embedded OCR-style name `MILLIPEDECOM` and `B62E` identify
the exact SKU used for all addresses below.

## 2. Executive summary

**No in-game cheat system exists in this ROM.** There is no password entry, no
button-code sequence, no hidden debug/level-select screen, and no unlockable path.
This is a defensible negative, not an absence of searching:

* The complete UI text bank was decoded (it is NUL-terminated ASCII, not
  tile-indexed) and every string was classified. It contains only title/menu,
  language, options, pause, high-score and attract labels — no `PASSWORD`,
  `CHEAT`, `CODE`, `DEBUG`, `SECRET`, `UNLOCK`, `LEVEL SELECT` or similar.
* No published GBA codes exist for this title. GameFAQs (`gba/929037`), VGChartz,
  CheatHappens, CheatingDome, Gbafun and The Video Games Museum all report zero
  cheats. There is no TCRF page. The only web hits are the manual, which documents
  ordinary configuration (starting score, ball count/game type, fuel, missions) and
  one Super Breakout Game Boy (not GBA) hint.
* Exhaustive button-space probing (every single key and every ordered 2-key pair
  on title, game-select, mission-select and pause screens; ~400 states diffed in
  RAM) found **no** transition to any screen other than the normal documented ones.
* The only "configuration" surfaces are developer-intended options: Millipede
  starting score, Lunar Lander's 4-mission selector, the Millipede pausescreen
  L+R quit prompt, and the shell's language/player/game-count settings. None of
  these is a cheat or an unlockable; all are reachable with no prerequisite.

The high-score initials field is the only text-entry surface. Per guide §16.2b it
was examined by its consumer: it is a 3-letter score label handled at
`0x08014300` (buffer `0x02000424`), with no comparison against any constant code
table. It is not a password field.

## 3. How to reproduce

* Emulator: `mgba 0.10.5` (SDL), `SDL_AUDIODRIVER=dummy`, display `:315`, `mgba -3`.
* Keymap (verified by reading `KEYINPUT` at savestate offset `0x530`):
  A=`x` (`0x03FE`), B=`z` (`0x03FD`), L=`a` (`0x01FF`), R=`s` (`0x02FF`),
  Start=`Return` (`0x03F7`), Select=`BackSpace` (`0x03FB`),
  D-pad=`Up/Down/Left/Right`. Hold 120–300 ms.
* Boot → DSI Games splash → Gravity-i splash → title (`PRESS START`).
* `Start` → game carousel. `Left`/`Right` cycles Millipede → Lunar Lander →
  Super Breakout. `Up`/`Down` moves the hand between `PLAY`/`OPTIONS`;
  `A` launches the game.
* Millipede launched: attract (`HIGH SCORES`) → `Start` → `SELECT STARTING SCORE`
  (`00 / 15000 / 30000 / 45000`; `Left`/`Right` changes, `A`/fire starts).
* Lunar Lander launched: attract/demo (`PRESS A BUTTON TO START`) → `A` →
  `Select Your Mission` (4 entries; `Left`/`Right`) → `A` → gameplay.
* Super Breakout launched: attract (`HIGH SCORE`) → `A` → `PRESS A BUTTON TO
  SERVE` → `A` → gameplay.
* In-game: `Start` pauses. Millipede shows `GAME PAUSED`; holding `L+R` over the
  pause screen reveals an additional `QUIT? PRESS A BUTTON TO QUIT OR B BUTTON
  TO RESUME GAME` overlay (observed; A/B did not cause a screen change in our
  tests — see §8). Super Breakout shows `PAUSED` on `Start`.

**Proof technique**: mGBA `.ss1` savestates were captured at every screen, the
`gbAs` PNG chunk was zlib-decompressed to a 397,312-byte raw state, and IWRAM was
mapped at file offset `0x19000` (GBA `0x03000000`) and EWRAM at `0x21000`
(GBA `0x02000000`). `KEYINPUT` sits at raw offset `0x530`. Every screen change was
confirmed by a byte diff, not by screenshots alone.

## 4. Address map

| What | Address / range | Evidence |
|---|---|---|
| GBA header | `0x08000000`–`0x080000C0` | Observed (hex dump) |
| Localized UI pointer table | `0x0803E7EC`–`0x0803F4A8`, 12-byte records `{u32 text_ptr, u32 flag, u32 rgb}` | Derived (pointer decode; 6 languages) |
| Millipede attract / starting-score strings | pointers at file `0x13DC0`, `0x144A8`, `0x13E74` | Derived (Thumb/ARM literal pools) |
| Initials-entry handler | `0x08014300` (character adjust), strings `0x081CC464`, `0x081CC4D4`, `0x081CC4F0` | Derived (ARM disassembly) |
| Initials/score buffer | `0x02000424` (`ldrh` in handler) | Derived |
| ASCII text bank | `0x1CB928`–`0x1CC57C` (file) = `0x081CB928`–`0x081CC57C` | Observed (hex dump) |
| IWRAM in savestate | raw `0x19000` = GBA `0x03000000` | Derived/Observed (state diff) |
| EWRAM in savestate | raw `0x21000` = GBA `0x02000000` | Derived/Observed |
| `KEYINPUT` in savestate | raw `0x530` (`0x03FF` idle, active-low) | Observed (per-key capture) |
| "in shell menu" byte | `0x030005E0` = `0x00` title/gameplay, `0x01` carousel | Observed (diff) |
| Mission index (LL) | `0x03007DE8` = 0..3, saturates at 3 | Observed (8 states) |

Note: `0x03000600` was initially suspected to be a game index but was shown to be
a rapidly advancing frame/timer counter (16-bit value increasing ~0x84 per sample
across mission captures); it is **not** used as a game-state proof.

## 5. Algorithm

There is no validator/password algorithm to reimplement. The only algorithmic
behaviour of interest is the bounded mission selector:

```
mission_index (u8 @ 0x03007DE8)
  Right  -> mission_index = min(mission_index + 1, 3)
  Left   -> mission_index = max(mission_index - 1, 0)
  A      -> start mission mission_index (leaves screen)
  0 = TRAINING   (Light Gravity, Friction From Atmosphere, Controlled Rotation)
  1 = CADET      (Moderate Gravity, No Friction, Controlled Rotation)
  2 = PRIME      (Strong Gravity, No Friction, Controlled Rotation)
  3 = COMMAND    (Moderate Gravity, No Friction, Rotation Momentum)
```

The initials handler (`0x08014300`) converts an entered glyph byte with
`if (c & 0x40) c += 26`-style arithmetic and writes into a 3-character buffer;
it never compares the buffer to a constant. There is no checksum and no code
table.

## 6. Tables

**Complete UI text bank** (`0x081CB928`–`0x081CC57C`, 6 languages each, NUL-padded):

* Super Breakout options: `3 BALLS`, `5 BALLS`, `CAVITY`, `DOUBLE`, `PROGRESSIVE`.
* Lunar Lander options: `FUEL 450/600/750/900/1100/1300/1550/1800`.
* Audio: `SFX ON/OFF`, `MUSIC ON/OFF` (+ localized forms).
* Navigation: `PRESS START`, `ONE PLAYER`, `TWO PLAYER`, `PLAY`, `OPTIONS`,
  `SELECT LANGUAGE`, `PAUSE MENU`, `RESUME`, `QUIT`, `BACK`, `OPTIONS MENU`,
  `WON!`, `YES/NO`, `SELECT PLAYER(1/2)`, `GAME SELECT!`, `NUMBER OF GAMES`,
  `BEST OF 1/3/5`, `PLAY AGAIN?`, `VS`.
* Millipede: `HIGH SCORES`, `DRAGONFLY`, `EARWIG`, `INCHWORM`, `DDT BOMB`,
  `MOSQUITO`, `BEETLE`, `SPIDER`, `MILLIPEDE`, `GROWTH`, `SELECT STARTING SCORE`,
  `PRESS FIRE TO START`, `TIME`.
* Initials prompt: `USE DIRECTION PAD TO`, `MAKE LETTER SELECTIONS`,
  `ENTER YOUR INITIALS`.
* In-game: `GAME OVER`, `GAME PAUSED`, `QUIT? PRESS A BUTTON TO QUIT`,
  `OR B BUTTON TO RESUME GAME`.
* Engine leftovers: `GBA FS ERROR (compression?)`, `GBA FS ERROR (missing file)`,
  `Out of IRam (32k)`, `Out of XRam (256k)`, `bg_palette`, `bg_chars`,
  `bg_wmap`, `BMP_height_table`, `ol_gbawmap`, `ol_chars`, `ms_palette`,
  `ms_chars`, `ms_gbawmap`, `v%d.%d`, `MULTIBOOT`, `<NULL>`.
* Two input alphabets only: `0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ` and its
  lowercase twin — used by the initials handler, not a password alphabet.

**Counts** (whole 4 MiB): 13,923 `strings` runs ≥4 chars; all keyword hits for
`password|cheat|secret|unlock|debug|code|hidden|bonus|level select` = 0. 2,459
short alphanumeric runs outside the text bank were inspected — all are
graphics/audio byte noise (tile-indexed sprite art), not text. Localized pointer
table records: 0x0803E7EC–0x0803F4A8 (step 0xC), 6 languages per item.

**Published-code verification**: zero codes exist to verify. Search coverage:
GameFAQs GBA 929037 (main page, no cheats page), VGChartz (0 cheats),
CheatHappens (none), CheatingDome (none), Gbafun (none), Video Games Museum
(none), TCRF (no article). Fetched pages were treated strictly as data; no
prompt-injection content was encountered in this session.

## 6b. Enumeration

Per §0.2, the "code space" is the empty set, and the enumeration is of the
*reachable screen/button space* instead:

1. **Screen space**: 20 distinct states were captured and RAM-differenced:
   title; carousel×3; Millipede attract, starting-score select, gameplay, pause,
   L+R quit-prompt overlay; Super Breakout attract, serve/gameplay, pause;
   Lunar Lander attract, mission select ×4, gameplay, crash/refuel state. Every
   screen has a unique RAM fingerprint (e.g. mission index `0x03007DE8` = 0,1,2,3).
2. **Button space (single press, title)**: 10/10 keys tested from a saved title
   state. Only `Start` changed state (diff 1,677 bytes → carousel); all others
   differed by ≤62 bytes (animation only). No hidden screen.
3. **Button space (ordered pairs)**: 100/100 pairs on title, 100/100 on the
   Lunar Lander game-select screen, 100/100 on the LL mission-select screen and
   100/100 on the Millipede pause screen — 400 state diffs. On title and menu,
   only pairs containing `A` or `Start` left the screen; on mission-select only
   `A`/`Start` left it; on pause nothing left the screen. **Zero** previously
   unseen screens and zero mission-index values outside 0..3 were produced.
4. **Classic/debug combos**: `L+R` held (found: Millipede pause quit prompt),
   `L+R+A`, `L+R+B`, `L+R+Start`, long `Start`, long `Select`, `Start+Select`,
   `A+B` — all tested on the relevant screens; none produced a debug menu,
   level select or unlock.
5. **Bounds proof by rejection**: Right pressed 8× on mission select saturates
   at index 3 (COMMAND) — the 5th through 8th presses are rejected by the
   selector; RAM index stays 3. This bounds the mission space at exactly four
   entries and proves there is no hidden fifth mission reachable by input.
6. **Novel code**: not applicable — there is no code system, hence no code to
   mint. The closest analogue, "an unadvertised input combination", was tested:
   `L+R` over the Millipede pause screen produces a QUIT overlay that is *not*
   mentioned anywhere in the manual's button table (the manual says Select
   quits). This is the only undocumented input behaviour found.

## 7. Validation evidence

* **Observed** (emulator + RAM): title/carousel/attract/all option and mission
  screens, the 4-mission saturation, the L+R quit overlay, every key mapping via
  `KEYINPUT`, and the absence of extra screens for all 400 two-key probes.
* **Derived** (static): single-header/patch-free fingerprint; complete ASCII text
  bank and localized pointer table; initials handler at `0x08014300` with buffer
  `0x02000424`; key-mask/literal scans returning no code table.
* **Inferred**: the `QUIT?` overlay is probably the shell's undocumented successor
  to the manual's "Select = Quit" instruction; its A/B action could not be
  driven to a visible transition (see Unknowns).
* No claim here rests on a screenshot alone; each screen transition has a
  corresponding savestate diff.

## 8. Unknowns

* The shell's `PAUSE MENU` / `OPTIONS MENU` strings (and the `FUEL 450..1800`
  and `3/5 BALLS` option strings) are present and referenced by the localized
  table at `0x0803E7EC..`, but no input path from the carousel or in-game pause
  reached a dedicated options screen. `A` on the carousel's `OPTIONS` cursor
  launches the game in this build, where configuration happens via Millipede's
  `SELECT STARTING SCORE` and Lunar Lander's mission select. The fuel and
  ball-count settings may therefore be dead/compiled-in defaults in this SKU, or
  require a condition not met here; this is bounded (400 two-key probes + clean
  boot with deleted `.sav`), not left untested.
* The runtime high-score initials screen was not reached: after scoring ~13k in
  Millipede and ~15 in Lunar Lander we did not beat the attract table's default
  top score of 89173, so no entry was offered. The screen's strings and handler
  are proven statically; only its trigger condition is unexercised.
* On the Millipede pause screen, the L+R `QUIT?` overlay appears, but pressing
  `A`, `B`, `Start`, `Select`, or any 2-key pair while it was shown did not
  change screens in our tests (RAM diff ≤842 bytes). The overlay may be
  decorative/dead in this build, or may require a tighter press-order window
  than our automation produced. It is reported as observed, not as a working
  quit.

## 9. Tooling

* `mgba 0.10.5` with `-3` (SDL, `SDL_AUDIODRIVER=dummy`), `Xvfb :315`,
  `openbox`, `xdotool` (XTEST to the focused window), `scrot`, ImageMagick.
* Python 3 + `capstone` 5.0.7 for literal/BL scans; `binutils-arm-none-eabi`
  (`arm-none-eabi-objdump -M force-thumb` / ARM) for disassembly.
* `sstate.py` — parses mGBA `.ss1` PNG, decompresses `gbAs` chunk with zlib to
  the 397,312-byte raw state; IWRAM at `0x19000`, EWRAM at `0x21000`,
  `KEYINPUT` at `0x530`.
* `gba.py`/`cap.py` — focus, timed key presses, screenshots and state capture;
  `rd.py` — GBA-address reads from saved states; `dbgserver.py`/`dbgcli.py` —
  pty-backed mGBA CLI debugger bridge (used early, superseded by savestate diff
  because the CLI stops processing commands while the core runs).
* Web sources: GameFAQs, VGChartz, CheatHappens, CheatingDome, Gbafun, The Video
  Games Museum, TCRF, and the DSI/Gravity-i manual PDF (gamegear.net).
* No ROM or copyrighted asset is redistributed; only hashes, addresses and
  derived findings are published.
