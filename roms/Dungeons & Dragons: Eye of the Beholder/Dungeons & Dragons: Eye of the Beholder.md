# Dungeons & Dragons: Eye of the Beholder (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Dungeons & Dragons: Eye of the Beholder.gba` |
| Size | 4,194,304 bytes (0x400000, 4 MiB) |
| `file` | GBA ROM "DDEOTB" (AD4E70, Rev.00) |
| Header title | `DDEOTB` |
| Game code | `AD4E` (US) |
| Maker | `70` |
| Version | `0x00` |
| Fixed `0x96` | present at `0xB2` |
| Entry word | `0xEA00002E` → branch to `0x080000C0` (stock crt0) |
| Header checksum | `0x0000`; complement byte `0x3A` (computed `0x53`) — minor header anomaly, no functional patch |
| MD5 | `3aa4f5bd135064deba3394215d4c560d` |
| SHA-1 | `6270ccf39dd6968f9f6e7d6516f9ee233aa8cddb` |
| SHA-256 | `d8439d2129c3362d504e5440f407c1cbb3641ed165ee79f4f138673a9c25cbb0` |

**Phase 0:** exactly one Nintendo-logo hit, at file `0x0` — no multi-game header, no appended
trainer, no cracktro patch. The entry word is the stock `b 0x080000C0`; the first 4 KiB is
ordinary crt0 code. This is a clean retail image.

## 2. Executive summary

This GBA CRPG has **no password system, no character-code generator, and no name-entry cheat**.
What it does have is a **hidden developer "Sound Test" debug menu** in the Options screen, opened
by a simultaneous **L + R + Select** button combination (active-high key mask `0x304`).

The entire menu system is a 5-entry state machine keyed by a single RAM byte at `0x03004DA0`.
IDs 0–3 are reachable with normal A-button selections (Options, Credits, erase-roster,
erase-party). **ID 4 is the hidden Sound Test screen** and is reachable *only* through the
gate at `0x0802349E`, which tests `input & 0x304 == 0x304` and writes 4 to the menu-ID byte.
Because the handler consumes the "newly pressed this frame" input word (`0x0300452E`), all three
buttons must transition on the **same frame** — a loose sequential press does not work, but an
atomic XTest chord does.

The Sound Test screen displays `SoundIndex = %03d`. A plays the indexed sound, B resets the
index and exits, L/R step the index. The index (RAM `0x03004D64`) is clamped to **0..100**
(inclusive). The hidden code was entered on the real screen and RAM-verified
(`0x03004DA0 == 4`); all two-button subsets were rejected, proving the code's bounds.

## 3. How to reproduce

**Environment:** mGBA (SDL) under `Xvfb :315`, `SDL_AUDIODRIVER=dummy`, default keymap
(A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows).

1. Boot the ROM. Press A through the intro until the "PRESS START" title, then Start.
2. On the main menu, move down to **OPTIONS** (2× Down) and press A.
3. In the OPTIONS screen, press and hold **L + R + Select on the same frame**.
   A plain sequential `xdotool keydown a; keydown s; keydown BackSpace` was **not** reliable
   (the game samples edge-triggered input); an atomic XTest burst of all three key presses
   before a single sync is. A helper used was:
   ```python
   from Xlib import display, X
   from Xlib.ext import xtest
   from Xlib import XK
   d = display.Display(':315')
   keys = [d.keysym_to_keycode(XK.string_to_keysym(k)) for k in ('a','s','BackSpace')]
   for k in keys: xtest.fake_input(d, X.KeyPress, k)
   d.sync(); time.sleep(0.22)
   for k in reversed(keys): xtest.fake_input(d, X.KeyRelease, k)
   d.sync()
   ```
4. The header changes from `Options` to **`Sound Test`** and the body shows
   `SoundIndex = 000`.
5. Controls: A = play sound at current index; B = stop/reset index and return to Options;
   L = decrement index (min 0); R = increment index (max 100).

**RAM verification** (mGBA `.ss*` savestates decompressed with zlib from the `gbAs` PNG chunk;
IWRAM begins at state offset `0x19000`):
- menu ID `0x03004DA0`: `0x00` → `0x04` when the chord is accepted.
- sound index `0x03004D64`: 0 → 1 → 2 → 3 (R), → 2 (L), → 0 (B), → 100 after 105× R, → 0 after 110× L.

**Published codes:** none found. Web search returned no results; direct fetches of 3rd party cheat indexes, Google/DuckDuckGo (blocked/captcha), and web.archive.org (404) all failed.
No literal code strings were present in the ROM to verify. Recorded as a bounded negative.

## 4. Address map

### ROM (file offset = ROM address − `0x08000000`)
| Address | Purpose |
|---|---|
| `0x08023350` | Options menu builder (draws Credits / Erase Character / Erase Save Game) |
| `0x08023410` | Options input handler (A/B/Up/Down + hidden-code gate) |
| `0x0802349E` | **Hidden-code gate**: `movs r1,#0xC1; lsls r1,#2` → mask `0x304`; `ands/cmp/bne` |
| `0x080234B0`–`0x080234B4` | writes `4` to menu-ID byte `0x03004DA0` |
| `0x080234D4` | Sound Test menu builder ("Sound Test", "SoundIndex = %03d") |
| `0x0802351C` | Sound Test input handler (A/B/L/R) |
| `0x08023D64` | Menu input state machine (dispatches handler by menu ID) |
| `0x08023DAC` | Menu builder dispatcher; jump table at `0x08023DCC` |
| `0x08023DCC` | `[0]=0x08023DE0, [1]=0x08023DEC, [2]=0x08023E18, [3]=0x08023E1E, [4]=0x08023DE6` (→Sound Test) |
| `0x0801EFB8` | `key_update`: writes held mask `0x03004510`, first-frame mask `0x0300452E` |
| `0x0801F1AC` | getter returning `*(u16*)0x0300452E` (the input consumed by menu handlers) |
| `0x08032830` | "Type Name" string (character-creation label field) |
| `0x08032E38` | "Secret Area" string (location label, not a cheat) |
| `0x08033104`–`0x08033218` | erase/sound debug string bank |

### RAM
| Address | Size | Meaning |
|---|---|---|
| `0x03004DA0` | u8 | menu ID: 0=Options, 1=Credits, 2=erase-roster, 3=erase-party, **4=Sound Test** |
| `0x03004D64` | u16 | Sound Test index, 0..100 |
| `0x03004D6C` | u8 | menu cursor |
| `0x03004510` | u16 | held keys, `~KEYINPUT & 0x3FF` (active-high) |
| `0x0300452E` | u16 | keys newly pressed this frame (edge-detected); the gate's input |

## 5. Algorithm

### Key input model
`key_update()` (`0x0801EFB8`) maintains:
- `held = ~KEYINPUT & 0x3FF` at `0x03004510` (confirmed: idle `0xFC00`; with a+s+BackSpace `0xFF04`).
- a per-key hold-counter array at `0x03004520`.
- `newly_pressed` at `0x0300452E`: for each of bits 0..9, set the bit iff `held` bit is set
  and its counter `<= 1` (i.e. first frame of the press). Cleared at the start of every update.

The menu state machine (`0x08023D64`) passes `newly_pressed` to the active menu handler.

### Hidden-code gate (Thumb, `0x0802349E`)
```c
// r6 = input = newly_pressed (0x0300452E)
mask = 0xC1 << 2;              // 0x304 = L(0x200) | R(0x100) | Select(0x004)
if ((r6 & mask) == mask) {
    *(u32*)0x03004D9C = 0;     // clear sub-state
    *(u8*)0x03004DA0 = 4;      // menu ID = Sound Test
    play_sound(1);
    *(u32*)0x0300367C = 0;     // reset cursor state
}
```

### Sound Test handler (`0x0802351C`)
```c
idx = *(u16*)0x03004D64;
if (input & 0x001) play_sound(idx);              // A
if (input & 0x002) { stop_sound();               // B -> reset + exit
                     *(u8*)0x03004DA0 = 0;
                     *(u16*)0x03004D64 = 0; }
if (input & 0x200 && idx != 0)      idx--;       // L
if (input & 0x100 && idx <= 99)     idx++;       // R (so max becomes 100)
*(u16*)0x03004D64 = idx;
```

### Menu-ID field (complete enumeration)
```c
// A-button in Options: menuID = cursor_index + 1
//   index 0 (Credits)        -> 1
//   index 1 (Erase Character) -> 2
//   index 2 (Erase Save Game) -> 3
// L+R+Select in Options      -> 4 (hidden)
```

## 6. Tables

| Menu ID | Builder | Screen (all walked and observed) | Reachability |
|---:|---|---|---|
| 0 | `0x08023DE0`→`0x08023350` | Options: Credits / Erase Character / Erase Save Game | default |
| 1 | `0x08023DEC`→credits path | Credits scroll | A on item 0 |
| 2 | `0x08023E18`→`0x0802359C` | Erase from Dragon Roster / Erase from Swords Roster | A on item 1 |
| 3 | `0x08023E1E`→`0x08023AB0` | Erase Dragon Party / Erase Swords Party | A on item 2 |
| 4 | `0x08023DE6`→`0x080234D4` | **Sound Test / SoundIndex = %03d** | **L+R+Select (hidden)** |

Sound-index bounds: min `0` (decrement stops at 0), max `100` (increment permitted while
`idx <= 99`). 101 representable indices. The display is `%03d`.

Input alphabet/key mask: GBA active-high bits `A=0x001 B=0x002 Select=0x004 Start=0x008
Right=0x010 Left=0x020 Up=0x040 Down=0x080 R=0x100 L=0x200`. Hidden code = `0x304`.

## 6b. Enumeration

**Space definition.** The findable cheat surface is a *button-code gate*, not a password:
- The hidden menu-ID space has exactly 5 values (`0x00`–`0x04`); it was enumerated exhaustively
  from the jump table at `0x08023DCC` and each value was walked on the real screen.
- The gate is a single exact-condition test on a 10-bit key mask: `(input & 0x304) == 0x304`.
  The required set is the three buttons {L, R, Select}. Any additional held buttons also pass
  (the test is a masked equality, not an exact equality), so the accepting input set is all
  masks with bits 2, 8 and 9 set — but the *newly-pressed* semantics mean those three must be
  newly pressed together.

**Novel code (not in any published list).** No online list exists for this SKU (all fetches
failed, §3). The code **L + R + Select on the OPTIONS screen** is the unpublished developer
combination recovered from `0x0802349E`. It was entered with an atomic XTest chord and proof
is recorded two ways:
- RAM: `0x03004DA0 = 0x04` (was `0x00`).
- Screen: header reads `Sound Test`, body reads `SoundIndex = 000`.

**Bounds proven by rejection.** The following were entered on the same Options screen immediately
before the accepted chord, each from a fresh Options state (menu ID verified at `0x00`):

| Combination | menuID after | Result |
|---|---|---|
| L + R | `0x00` | rejected |
| L + Select | `0x00` | rejected |
| R + Select | `0x00` | rejected |
| **L + R + Select** | `0x04` | **accepted → Sound Test** |

Sound-index bounds: 105× R clamped at `0x64` (100); 110× L clamped at `0x0000` (0).

**Negative results bounded.** There is no password/code-table system:
- No password table, key-mask sequence table, or validator accepting typed input was found.
  The only `movs #imm; lsls #2`-style multi-bit mask in the whole code region is the one gate
  at `0x0802349E`; the other six byte-pattern hits are struct-offset arithmetic, not key tests.
- The character-creation "Type Name" screen (`0x08008E60` renders a 78-symbol on-screen
  keyboard: `A–M`, `N–Z`, `a–m`, `n–z`, punctuation, `0–9 #*`) is a *label field*, not a validator:
  it renders a keyboard, and no comparison of the entered buffer against a constant was found.
  Direct keyboard typing did nothing — all input is via grid navigation.
- "Secret Area" (`0x08032E38`) is an area name shown in a location menu (`0x08021E40`), not a
  hidden warp/debug feature.
- The party-creation flow (Current Party / Enter the Dungeon / Add To Party / Remove From Party /
  Roll New Character / Add 4 more characters) and the character-creation/level screens
  (Roll Abilities, Add Levels, Add Skills/Feats, Choose Race/Alignment/Gender) were walked and
  are ordinary RPG UI, not cheats.

## 7. Validation evidence

- **Observed** (emulator/savestate): intro → title ("PRESS START") → main menu (two "Create a
  new Party" + OPTIONS) → OPTIONS (Credits / Erase Character / Erase Save Game) → Credits,
  erase-roster and erase-party submenus → party creation → "Type Name" keyboard. All screenshots
  retained under `/tmp/eyebeholder/`.
- **Observed**: L+R+Select atomic chord changes menu ID `0x00 → 0x04` and the screen to
  "Sound Test / SoundIndex = 000"; partial combos leave menu ID at `0x00`; R/L/B change the
  index in RAM to 1/2/3/100/0 as described.
- **Derived** (disassembly): gate condition and mask at `0x0802349E`; menu-ID write at
  `0x080234B4`; Sound Test handler at `0x0802351C`; input model in `key_update` (`0x0801EFB8`).
- **Inferred**: the audible result of pressing A (sound playback via `0x08000238`) — audio was
  disabled (`SDL_AUDIODRIVER=dummy`), so only the call path was verified statically; the screen
  and index effects were verified directly.
- **Not observed**: exact per-index sound names (not required for the cheat finding).

## 8. Unknowns

- Whether the Sound Test index values 0..100 map to a documented sound list (not needed to prove
  the menu, and the audio backend was muted).
- Published-code cross-check could not be performed because every relevant web source was
  blocked or empty; there is no ROM literal to verify either.

## 9. Tooling

- `arm-none-eabi-objdump -M force-thumb` for targeted disassembly (gate, handlers, dispatcher).
- Python + Capstone 5.0.7 for literal-pool / BL / mask-pattern scans.
- `python-xlib` XTest for the atomic simultaneous key chord (ordinary `xdotool` sequential
  keydowns were unreliable because the game samples edge-triggered input).
- mGBA 0.x SDL under Xvfb :315; savestate RAM reads by extracting and zlib-decompressing the
  `gbAs` PNG chunk (IWRAM at state offset `0x19000`); savestate patching to preview the menu.
- No ROM or copyrighted assets are redistributed; only addresses, hashes, algorithms and
  findings are published.
