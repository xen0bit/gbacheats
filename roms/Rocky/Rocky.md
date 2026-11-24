# Rocky (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Rocky/Rocky.gba` |
| Size | 8,388,608 bytes (0x800000) |
| Header title | `ROCKY BOXING` |
| Game code | `AR8E` (maker `41`), `file(1)` prints `AR8E41` |
| Revision | 0x00 (`Rev.00`) |
| Fixed byte 0xB2 | 0x96 |
| Complement byte 0xBD | 0x6D; header checksum 0x0000 |
| Entry word | `0xEA00002E` (stock `b 0x080000C0`) |
| MD5 | `a0fb0b2ca04e0610ec86eaa0972910bc` |
| SHA-1 | `c532b09c3663eda3a1c49e290877987d41f4d92d` |
| SHA-256 | `308bef618d73cc78b922b64d23bfde6c26bdec2b89b3b98b9996784bd3df1d76` |

Phase 0 result: **single retail image, no patch, no trainer, no multi-game pack.**
A scan of all 8 MiB for the 156-byte Nintendo logo found exactly **one** hit (file 0x0,
ROM 0x08000000). The entry word is the unmodified GBA crt0 branch, not the
`EA00002E`-to-cracktro patch described in guide §16.1. The tail of the image is
zero padding. No appended trainer menu is present.

## 2. Executive summary

This GBA SKU (Virtucraft, 2002) has **no password system and no reachable
button-code / cheat menu**. It is a save-game-driven unlockable design:

* The **only** in-game cheats published for the GBA are completion-gated
  unlockables (Knockout mode after Movie mode; Rocky Statue after Knockout on
  Normal; Apollo Max/"Apollo Statue" after Knockout on Hard; fighters unlocked by
  beating them in Movie mode). I verified these in three independent published
  sources (3rd party cheat indexes) and confirmed the in-game state:
  a fresh save shows KNOCKOUT dark/locked in the main menu and only the first
  four fighters selectable in Exhibition.
* The widely-circulated **button codes** (hold R + a 5–6 press D-pad sequence
  ending in L) are for the **GameCube / Xbox / PS2** SKUs. I searched the GBA
  ROM for all 7 published sequences in 3 encodings (active-high u16, R-held u16,
  active-low u16): **0 literal hits**. I entered the 7 codes on the GBA main menu
  in mGBA: all were rejected as navigation (cursor movement only), never a
  screen change. One of them (R+Up,Down,Down,Left,Left,L) is also the subject of
  a 3rd party cheat index typo — it is listed twice with two different effects.
* The ROM **does contain a complete "CHEAT MENU" text block** in all five
  language banks (English ×2, Spanish, French, German, Italian), with the labels
  `CHEAT MENU`, `SUPER PUNCH`, `INFINITE ENERGY/HEALTH/STAMINA/POWER`, `RANDOM`,
  `DEAD`, `COMBO`, `KILLER COMBO`, `SECRET FIGHTER`, `HIDDEN FIGHTER`.
  This is leftover developer text: the strings have **zero xrefs** in Ghidra,
  their text IDs are referenced only by the generic scrolling-text renderer's
  suffix tables, no code compares any input buffer to them, and no reachable
  screen displays them. Per guide §16.3 this is a *dead-code / cut-feature*
  negative, bounded by counts below.

## 3. How to reproduce

Emulator: mGBA 0.10.5 SDL, `DISPLAY=:315`, `SDL_AUDIODRIVER=dummy`,
`Xvfb :315 -screen 0 1024x768x24`, `openbox`, `mgba -3 <rom>`.
Keymap (mGBA SDL default): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
Select=`BackSpace`, D-pad = arrow keys. Key holds of ~60 ms; 150 ms holds
double-step the menus (guide §16.2).

Screen path, all verified by screenshot and by decoding the `gbAs` chunk of a
mGBA savestate (guide §16.13):

1. Boot → MGM/Ubisoft splash → "ROCKY" animation → language select
   (5 flags, English first). `A` selects.
2. Main menu (6 entries): MOVIE MODE, EXHIBITION, KNOCKOUT (dark/locked),
   VERSUS, LOAD GAME, OPTIONS. Down skips the locked KNOCKOUT entry.
3. OPTIONS (4 entries): MUSIC, SOUND FX, CREDITS, BRIGHTNESS — no cheat entry.
4. LOAD GAME → "CHOOSE OPTION" (5 entries): CHOOSE PLAYER, DELETE PLAYER,
   COPY PLAYER, RENAME PLAYER, plus 8 save slots labelled NEW GAME.
5. MOVIE MODE → same "CHOOSE OPTION"/"CHOOSE PLAYER" (8 slots) → **ENTER NAME**
   (3-character profile name, font-indexed alphabet) → FIGHT / CUT SCENES
   (CUT SCENES dark). This is a **profile name**, not a password field.
6. EXHIBITION → CHOOSE YOUR FIGHTER / CHOOSE YOUR OPPONENT. On a blank save only
   ROCKY BALBOA, SPIDER RICO, ERNIE ROMAN and DIPPER BROWN are selectable.
7. During a fight: mGBA 0.10.5 exits cleanly on entering the 3D fight scene
   (no log output), so the in-fight PAUSE menu could not be exercised in this
   environment; the PAUSE strings (`PAUSE`, `CONTINUE`, `EXIT`, `a CONTINUE b`,
   `a EXIT b` at 0x72c9e3–0x72ca04) were decoded from the text bank instead.
   This is the one screen not exercised dynamically (see §8).

Button code tested and confirmed: **A+B+Select+Start on any menu screen performs
a soft reset** to the Ubisoft splash. Static origin: input handler
`FUN_08004BE0` at 0x08004BE0, branch at 0x08004D30
`if ((held & 0xF) == 0xF && [0x0200C4CC] != 0)` → DMA setup + reset chain
(`FUN_080054B0`, `FUN_0800824C`, `FUN_0801B80C`, `FUN_08015F40`,
`FUN_0801B7AC`, `FUN_0801D6B0`). This is a system reset, not a cheat.

## 4. Address map

| Item | File offset | ROM address | Evidence |
|---|---|---|---|
| Header / entry | 0x000–0x1FF | 0x08000000 | observed (xxd) |
| crt0 entry branch | 0x000 | 0x08000000 | derived (0xEA00002E) |
| Input handler `FUN_08004BE0` | 0x04BE0 | 0x08004BE0 | derived (Ghidra decompile) |
| KEYINPUT literal pools | 0x04C48/0x04CCC/0x04DE0 | 0x08004C48/… | derived |
| Key history buffer ptr | — | 0x0200C4D4 (RAM) | derived (xrefs at 0x8004C94 etc.) |
| Current active-high key mask | — | 0x0200C4CC (RAM) | derived (xrefs 0x800263E, 0x801A818) |
| Main-loop dispatcher `FUN_080131FC` | 0x131FC | 0x080131FC | derived |
| Main-menu handler jump table | 0x13698 | 0x08013698 | derived (6 entries) |
| Menu-action jump table | 0x1350C | 0x0801350C | derived (35 entries, 6 distinct stubs) |
| English text bank | 0x72ACDD–0x72D195 | 0x0872ACDD | observed (strings + u16 suffix tables) |
| `CHEAT` | 0x72CA40 | 0x0872CA40 | observed, text ID 0x1D63 |
| `MENU` | 0x72CA83 | 0x0872CA83 | observed, text ID 0x1DA6 |
| `SUPER PUNCH` | 0x72CA46/0x72CA4C | 0x0872CA46/C | observed, IDs 0x1D69/0x1D6F |
| `INFINITE ENERGY` | 0x72CA52/0x72CA62 | — | observed, IDs 0x1D75/0x1D85 |
| `SECRET FIGHTER` | 0x72CA9B | — | observed, ID 0x1DBE |
| `HIDDEN FIGHTER` | 0x72CAAA | — | observed, ID 0x1DCD |
| `PAUSE` block | 0x72C9E3–0x72CA04 | — | observed |
| Name-entry alphabet | 0x72CBD8 | 0x0872CBD8 | observed |
| Fighter name table | 0x72AE81–0x72AFAD | — | observed (27 fighters) |
| Spanish cheat block | 0x72EEBD | — | observed |
| French cheat block | 0x73141E | — | observed |
| German cheat block | 0x733AD0 | — | observed |
| Italian cheat block | 0x735EAF | — | observed |
| Scrolling-text suffix tables | 0x37438 / 0x9266E | 0x08037438 / 0x0809266E | derived (u16 text-ID arrays) |
| Save record (Flash, 8 KiB) | `Rocky.sav` 0x00–0x3F | 0x0E000000 | observed (post-save dump) |

Text ID decoding: the English bank base is 0x72ACDD and each string is
NUL-terminated; e.g. 0x72CA40 − 0x72ACDD = 0x1D63, which is exactly the u16
value appearing in the renderer tables at 0x37438 and 0x9266E. This is the
"font/tile-indexed text bank" decoding required by the brief; `strings` alone
would have missed the menu structure.

## 5. Algorithm

No password/checksum validator exists in this ROM. The only input-matching
algorithm is the generic key handler:

```
mode = *(u16*)0x0200C4CC_state            # input mode (0,1,2)
held = ~KEYINPUT(0x04000130) & 0x3FF      # active-high mask
if mode == 0 or 1:
    cur = held ^ 0x3FF ... (filter 0x20/0x40 for movement)
    store cur to 0x02003364 (mode 0) or 0x0200C4CC (mode 1)
    if cur != last: append cur to history buffer @0x0200C4D4, ++length@0x0200C4DA
    if length >= cap: reset history (mode 1)
elif mode == 2:
    ++index@0x0200C4DA; read next u16 from history buffer (replay/demo)
pressed = cur & ~prev;  prev = ~cur        # edge detection at 0x8004D20
if (cur & 0xF) == 0xF and *0x0200C4CC: soft-reset chain
```

This is a **demo record/replay** path, not a code matcher: no ROM function other
than `FUN_08004BE0` itself has an xref to the history buffer (Ghidra xref set:
0x8004C94/0x8004C9C/0x8004CA4/0x8004CB0/0x8004D02/0x8004D0E/0x8004D16), so
no comparator can consume a player-entered sequence.

## 6. Tables

### 6.1 Published GBA "cheats" (all completion-gated; no input code)

| Effect | Condition | Source |
|---|---|---|
| Knockout mode | Complete Movie mode | 3rd party cheat indexes |
| Rocky Statue playable | Complete Knockout on Normal | 3rd party cheat indexes |
| Apollo Max / "Apollo Statue" playable | Complete Knockout on Hard | 3rd party cheat indexes |
| Hidden fighters | Beat them in Movie mode | 3rd party cheat index walkthrough (`abobo_squad`) |

### 6.2 Published console codes — NOT in this ROM

| Effect (GC/XB/PS2) | Sequence (hold R, press…) | ROM literal search |
|---|---|---|
| All boxers/arenas | U,D,D,L,L,L-trigger | absent |
| All + Rocky Statue | R,R,R,L,R,L-trigger | absent |
| Double speed | D,L,U,R,L-trigger | absent |
| Full stats (tourney/exh) | L,U,U,D,R,L-trigger | absent |
| Double punch damage | R,D,L,U,L,L-trigger | absent |
| Max movie stats | R,D,D,U,L,L-trigger | absent |
| Win fight | R,R,L,L,U,L-trigger | absent |

### 6.3 Cheat-menu text IDs (English, base 0x72ACDD)

| String | ID | String | ID |
|---|---|---|---|
| CHEAT | 0x1D63 | MENU | 0x1DA6 |
| SUPER | 0x1D69 | PUNCH | 0x1D6F |
| INFINITE | 0x1D75 | RANDOM | 0x1D7E |
| ENERGY | 0x1D85 | HEALTH | 0x1D8C |
| STAMINA | 0x1D93 | POWER | 0x1D9B |
| DEAD | 0x1DA1 | COMBO | 0x1DAB |
| KILLER COMBO | 0x1DB1 | SECRET FIGHTER | 0x1DBE |
| HIDDEN FIGHTER | 0x1DCD | | |

### 6.4 Fighters present in ROM (0x72AE81, 27 entries)

ROCKY BALBOA, SPIDER RICO, ERNIE ROMAN, DIPPER BROWN, APOLLO CREED,
ROCKY STATUE, APOLLO MAX, MAC LEE GREEN, MAC L GREEN, BILLY SNOW, BUDDY SHAW,
BIG YANK BALL, VITO SOTO, JOE CHAN, CLUBBER LANG, BIG CHUCK SMITH, CHUCK SMITH,
JOE ZACK, BRIAN BUCHANAN, B. BUCHANAN, IVAN DRAGO, PHIL RODGERS, UNION CANE,
TIM SIMMS, TOMMY GUNN, CHAPEL (+ venues begin at 0x72AFAE).

## 6b. Enumeration

**No code space exists to enumerate; the negative is bounded as follows.**

1. **Menu space — fully enumerated.** Main menu = 6 entries (jump table at
   0x08013698 has exactly 6 pointers; pressing Down from OPTIONS wraps to
   MOVIE MODE, so there is no hidden 7th entry). OPTIONS = 4 entries (MUSIC,
   SOUND FX, CREDITS, BRIGHTNESS; wraps). "CHOOSE OPTION" = 5 entries.
   FIGHT/CUT SCENES = 2 entries, CUT SCENES initially dark. Load-game slots = 8.
   No PASSWORD, CHEAT or CODE entry exists anywhere in these menus.
2. **Password space — empty by counts.** `strings` of the whole 8 MiB returns
   `PASSWORD` = 0 hits, `DEBUG` = 0, `UNLOCK` = 0, `KONAMI` = 0; `CHEAT` = 5 and
   `SECRET` = 5, all five each being the same translated text block. There is
   no on-screen keyboard except the 3-character profile name at the ENTER NAME
   screen; its 64-symbol alphabet (0x72CBD8) is a font/tile mapping, and its
   value is written into the 8 KiB save record (observed byte 0x3A = 0x41 'A'
   after entering a name). No ROM function compares that buffer to a constant:
   every `memcmp`/`strcmp`-style site found is a parser constant, not the name.
3. **Button-code space — empty by counts.** Seven published sequences × 3
   key-mask encodings = 21 literal searches over 8 MiB: **0 hits**. A raw scan
   of all code below 0x70000 for runs of ≥4 consecutive u16 single-button masks
   found exactly **one** run (`0x1FE7E: 0x200 0x200 0x200 0x200`), i.e. no code
   table. The only input state machine (`FUN_08004BE0`) has 1 reader of its key
   history outside itself, and that reader is the UI/menu caller, not a
   comparator. A+B+Select+Start is the only non-navigation combo and it is a
   soft reset (observed).
4. **Cheat-menu text — dead code.** Ghidra reports **0 xrefs** to 0x0872CA40
   (`CHEAT`) and no code reference to text IDs 0x1D63–0x1DD8 outside the generic
   suffix tables at 0x37438/0x9266E and 0x452E80+. Searches for u16 menu-item
   pairs (`CHEAT MENU`, `SUPER PUNCH`, `INFINITE ENERGY`, `KILLER COMBO`,
   `SECRET HIDDEN`) found only one coincidental hit inside compressed data.
   Therefore the strings cannot be reached by any in-game input.
5. **Novel code:** not applicable — there is no generator or validator to mint
   from. Per §0.2, a "no system" result is closed by the four bounded searches
   above rather than by generating a code.
6. **Bounds by rejection:** the published console codes were entered on the
   GBA main menu and rejected (no unlock), and A+B+Select+Start was confirmed
   to be a reset rather than an unlock, so the set of reachable input-driven
   effects is `{navigation, soft reset}`.

## 7. Validation evidence

* **Observed:** ROM identity/hashes/header; one Nintendo-logo hit; zero hits for
  all published-code literals; mGBA screenshots of language select, main menu
  (KNOCKOUT dark), OPTIONS (4 items), LOAD GAME "CHOOSE OPTION" (5 items),
  CHOOSE PLAYER (8 slots), ENTER NAME (3 chars), FIGHT/CUT SCENES (CUT SCENES
  dark), CHOOSE YOUR FIGHTER/OPPONENT (4 fighters on a blank save), Ubisoft
  splash after A+B+Select+Start; decoded `gbAs` savestate (397,312 bytes,
  IWRAM at 0x19000, EWRAM at 0x21000); blank and post-name 8 KiB save dumps.
* **Derived:** text-bank base 0x72ACDD and all text IDs in §6.3; dead-code status
  (0 xrefs); 6-entry and 35-entry jump tables; input-handler logic at
  0x08004BE0; 27 fighter names at 0x72AE81.
* **Inferred:** that the CHEAT MENU strings are a cut developer feature (the
  strings and their renderer metadata exist but no route reaches them); that
  fights fail under mGBA 0.10.5 due to emulator incompatibility rather than
  game logic.

## 8. Unknowns

* In-fight PAUSE menu was not displayed dynamically: mGBA 0.10.5 exits cleanly
  when the 3D fight scene starts, at all scales tested (-1 and -3). Its strings
  were decoded but no button behaviour inside it was exercised.
* The exact save-bit offsets that gate Rocky Statue / Apollo Max / Knockout were
  not isolated: reaching them requires completing Movie/Knockout mode, which is
  impractical in this environment.
* The translated Spanish/French/German/Italian cheat blocks were located but
  only the English block was decoded field-by-field (identical labels).

## 9. Tooling

`file`, `xxd`, `strings`, `grep`, `md5sum`, `sha1sum`, `sha256sum`,
`arm-none-eabi-objdump -M force-thumb`, `capstone 5.0.7`, `Ghidra 12.1.4`
(via REA MCP `open_binary`/`analyze_function`/`xrefs`), `gdb-multiarch`
(stub tried; flaky — savestate diffing used instead), `Xvfb`, `openbox`,
`xdotool`, `scrot`, ImageMagick, `tesseract`, `mGBA 0.10.5 SDL`.

Helper scripts in `/tmp/rocky/`: `key.py` (XTEST input), `brute.py`
(button-code entry + screenshot diff), `ssdecode.py` (PNG `gbAs` zlib decode).

No ROM or copyrighted asset is redistributed by this report.

## 10. Cleanup

All generated `Rocky.sav`, `Rocky.ss1` files were removed from
`roms/Rocky/`; my Xvfb :315, openbox and mgba PIDs were terminated by number.
`roms/INDEX.md` was not modified (per task instruction).
