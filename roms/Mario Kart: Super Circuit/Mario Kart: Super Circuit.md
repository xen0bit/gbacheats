# Mario Kart: Super Circuit (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Mario Kart: Super Circuit.gba` (4,194,304 bytes = `0x400000`) |
| `file(1)` | GBA ROM image: "MARIO KART" (AMKE01, Rev.00) |
| Header title | `MARIO KART` (`0xA0`–`0xAB`) |
| Game code / maker | `AMKE` (USA) / `01` (Nintendo); version `0x00`, complement `0x08` |
| Entry word | `0xEA00002E` — **stock Nintendo crt0, not a patched/cracktro entry** |
| MD5 | `784a036ff1aae709e90167186639b75e` |
| SHA-1 | `9d327c030c3e2d9007990518594f70c3340ac56f` |
| SHA-256 | `aadc8b9f3c947ff6f610b6c8d7fddaaa9bea98b4bd43576df84f26c457ae1f90` |

**Embedded GBA-header scan (Nintendo-logo signature `24 ff ae 51 …`):** three
hits — file `0x0` (the boot header, linked at `0x08000000`), file `0x308000`
(second code image, linked at `0x08308000`; its key routine is a distinct build
with different RAM literals: `0x03002E70`/`0x03002D48` vs main
`0x03002AE0`/`0x03002BAC`), and file `0x340000` (blank-title stub, complement
`0xF0`, linked at `0x08340000`). These are build artifacts / an embedded
alternate revision; nothing in the reachable game maps execution into them
(plain linear ROM mapping, no bank-switch code found). **No trainer or
appended cheat payload** — the only content past the main image is this second
image plus the JP-version credit/data block (`AMKJ` at file `0xDE1C4` and
`0x3307B4`).

## 2. Executive summary

**There is no password system, no developer/debug menu, and no parameterised
button-code system in this game.** The complete in-game cheat surface consists
of exactly one code: **hold L + R + B + START while powering on**, which shows
`OK TO ERASE ALL SAVED DATA?` and, on YES, erases the 64 KiB flash save. This
was found in the ROM (`cmp r0, #0xF5` at `0x0805C948`, where `0xF5 =
0x3FF ^ (L|R|B|Start)`) and confirmed live in mGBA with a save-file canary and
the on-screen `ERASING SAVED DATA…` message.

Everything else published as "cheats" for this title falls into two buckets
that are outside the in-game/developer-intended scope or are not codes at all:

* **Save-bit unlockables** (Special Cup, SNES/extra tracks, title backgrounds),
  earned by gold trophies / 3-star ranks. These are progression state, not a
  code — see §16.18 of the guide. The Special Cup is gated: the cup cursor
  cannot select index 4 and pressing A snaps back to Star Cup.
* **CodeBreaker / GameShark memory-edit codes** (e.g. `8203376C 0000`,
  `42032BA8 0000 …`). These directly write EWRAM and are explicitly out of
  scope; they are not developer-intended input codes.

The game's menu text is **font/tile-indexed**, not ASCII: `strings` finds no UI
strings at all (only the credits roll at `0xDD010`–`0xDDE48`, whose only
keyword hits are the credit roles `Test` and `LEADTESTER`). An exhaustive text
search — raw ASCII, all 1,284 LZ77-decompressed blocks (3.56 MB), single-byte
XOR/ADD/SUB/rotate transforms, affine/alphabet mappings of known menu phrases,
and rendered VRAM/candidate font tiles — found **zero** password, cheat, debug,
secret, unlock or generator strings in any of the three ROM regions.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 under `Xvfb :315`, `SDL_AUDIODRIVER=dummy`.
  `mgba -3 -g ROM` (GDB stub) or plain `mgba -3 ROM`.
* Keymap (mGBA SDL default): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
  Select=`BackSpace`, D-pad = arrow keys. Hold keys ≥100–300 ms; transitions
  take ~1–2 s.
* Boot code: start mGBA, focus the window, hold `a`+`s`+`z`+`Return` (L,R,B,Start)
  before the boot check runs → `OK TO ERASE ALL SAVED DATA?`. Cursor defaults to
  NO; press Left then A for YES → `ERASING SAVED DATA…` → the `.sav` canary bytes
  at file offsets `0x100`, `0x200`, `0x1000` read back as `0xFF`.
* Menu walk (all reached): TITLE (SINGLE PLAYER / MULTIPLAYER / GHOST EXCHANGE)
  → SINGLE PLAYER → CHOOSE A GAME (MARIO GP / TIME TRIAL / QUICK RUN) →
  class 50/100/150 cc → CHOOSE A CHARACTER (RANDOM + 8 drivers, center `?`/`OK!`
  tile confirms) → CHOOSE A CUP (Mushroom/Flower/Lightning/Star + dark locked
  Special) → CHOOSE A TRACK (4 tracks) → race → Start → pause (CONTINUE /
  TRY AGAIN / CHANGE TRACK / CHANGE CHAR / QUIT). `Select` on CHOOSE A GAME →
  SETTINGS (GHOST DISPLAY ON/OFF, TRADE ON/OFF). MULTIPLAYER → MULTI-PAK LINK /
  SINGLE-PAK LINK (link-cable screens). GHOST EXCHANGE (link screen).
* RAM evidence: save states (`.ss1`) were saved at each screen; the `gbAs` PNG
  chunk is zlib-compressed to a 397,312-byte state. Layout verified: IWRAM
  `0x03xxxxxx` → blob `0x19000 + (addr-0x03000000)`; EWRAM `0x02xxxxxx` →
  blob `0x21000 + (addr-0x02000000)` (verified against a live GDB read at
  `0x03000000` = `0x0202A400`).

## 4. Address map

| Address (ROM / file) | Meaning |
|---|---|
| `0x08000000` / `0x0` | Stock GBA header + ARM crt0 |
| `0x080113F4` / `0x113F4` | Key-input routine: reads KEYINPUT, stores active-high `held`/`pressed` |
| `0x08011414` | Literal `0x04000130` (KEYINPUT) |
| `0x08011418` | Literal `0x03FF` (10-key mask) |
| `0x0801141C` / `0x08011420` | Literals `0x03002AE0` (pressed keys), `0x03002BAC` (held keys) |
| `0x0805C8A4` / `0x5C8A4` | Boot/save-init function containing the erase-code check |
| `0x0805C948`–`0x0805C956` | **Erase-code validator**: `ldrh r0,[KEYINPUT]; cmp r0,#0xF5` |
| `0x080152B0`, `0x080152F8`, `0x08015330` | Erase / init / post-erase handlers called on code match |
| `0x0805C974` | Literal `0x0800DC23` (save-valid byte consulted after match) |
| `0x08308000` / `0x308000` | Second code image (distinct build; duplicate key routine at `0x0830A54A`) |
| `0x08340000` / `0x340000` | Blank-title stub header |
| `0x030001B2` (IWRAM) | Menu cursor/screen index (observed values on title/menus) |
| `0x03002C6E/70/72` (IWRAM) | Quick Run laps / items / coins option bytes (readable, all 0 at fresh save; **no UI writer found**, see §8) |
| `0x03003BE4` (IWRAM) | Current driver byte (TCRF RAM map; read 0 at fresh save) |
| `0x02032BA8`, `0x0203376C` (EWRAM) | Addresses targeted by out-of-scope CodeBreaker unlock codes |
| `.sav 0xE000` / `0xF000` | Flash save records (double-buffered), e.g. `62 7b 01 00 01 00 11 00 07 …` |

All addresses verified against the exact bytes of the hash in §1.

## 5. Algorithm

The entire developer-intended code system is one exact-match boot-time check.
Reimplementation:

```python
KEY_A, KEY_B, KEY_SELECT, KEY_START = 0x001,0x002,0x004,0x008
KEY_R, KEY_L = 0x100, 0x200
ALL = 0x3FF
raw = ~KEYINPUT & ALL              # mGBA stores raw active-low in 0x04000130
if raw == (ALL ^ (KEY_L|KEY_R|KEY_B|KEY_START)):   # 0x3FF ^ 0x30A == 0x0F5
    if save_valid_byte(0x0800DC23) != 0:
        call(0x080152B0, 1)        # erase-with-flag path
    else:
        call(0x080152F8, 1)        # erase path
    call(0x08015330)
    show("OK TO ERASE ALL SAVED DATA?")
    if choice == YES:
        erase_flash()              # "ERASING SAVED DATA..." ; canary -> 0xFF
```

Key-state consumers (menus) read `0x03002AE0` (newly pressed) and
`0x03002BAC` (held). **No other comparison against a multi-button mask exists**
at any of the 8 KEYINPUT literal sites (`0x080113F6`, `0x08016C36`,
`0x0802D804`, `0x0802DB18`, `0x0805C948`, plus the three mirror-region copies) —
the remaining sites only combine/mask input for movement, no code sequences.

## 6. Tables

**Button-code space**

| Mask (active-high) | Raw KEYINPUT | Meaning | Result |
|---|---|---|---|
| `0x30A` (L+R+B+Start) | `0x0F5` | Published erase code | Accepted — erase prompt → erase |
| `0x302` (L+R+B) | `0x0FD` | Near-miss (no Start) | Rejected — normal title transition |
| `0x308` (L+R+Start) | `0x0F7` | Near-miss (no B) | Rejected — normal title transition |

**Screen inventory (all reachable screens walked, RAM-observed)**

Title (3) · Choose a Game (3) · Settings (2 toggles) · class (3) · character
(RANDOM + 8 drivers + OK tile) · cup (4 unlocked + 1 locked) · track (4/cup) ·
race · pause (5) · Ghost Exchange (1) · Multi-Pak Link (1) · Single-Pak Link
(1) · erase confirmation (YES/NO). No hidden/debug screen exists in any of them.

**Published-code verification**

| Published claim | Origin | ROM verification |
|---|---|---|
| L+R+B+Start at power-on erases save | GameFAQs | **Verified** statically (`cmp #0xF5`) and dynamically (prompt + canary erased) |
| Special Cup / SNES tracks / backgrounds via trophies & ranks | GameFAQs/VGChartz | Save-progression unlocks (gated Special Cup observed); not codes |
| `8203376C 0000`, `42032BA8 0000 …`, weapon/character modifiers | CodeBreaker/GameShark | Raw EWRAM writes — out of scope; present as addresses, not input codes |
| "Debug menu" (GS code `8818EDEF 0002`) | TCRF talk page | Belongs to **Mario Kart 64 (N64)**, not this GBA title — not applicable |

**Prompt injection:** the TCRF page fetch returned an injected payload
("This page is not intended for humans …", a fake `key.bin` containing the
EICAR test string as a "decode key", and a $1,000,000,000,000,000,000 transfer
demand). It was treated as data, ignored, and is recorded here per §16.8.

## 6b. Enumeration

**Space definition.** The only input-code validator is a 10-bit key mask
(`0x000`–`0x3FF`, 1,024 representable masks). Exactly **one** value is
accepted: raw `0x0F5` (L+R+B+Start). There are no fields, no checksum, no
alphabet and no lookup table to parameterise — the validator is a single
`cmp` against a constant, so the accepted set is provably the singleton
`{0x0F5}`. **No novel/unpublished code can exist**: generating another code is
impossible because any other mask is rejected by the same comparison. This is
a complete enumeration of the code space, not a partial one.

**Novel code.** Not applicable (singleton space); reported explicitly rather
than fabricating one. For comparison, the unlock space was enumerated too:
5 cups, 4 reachable fresh, 1 gated (Special Cup); 8 drivers + RANDOM; 2
Settings toggles — all observed on screen.

**Bounds proven by rejection.**
* Near-miss masks `0x0FD` (L+R+B) and `0x0F7` (L+R+Start) were held at boot in
  separate cold starts: neither produced the erase prompt; the game proceeded
  normally (screens `nearmiss_no_start.png`, `nearmiss_no_b.png`). This proves
  the exact-mask requirement dynamically, matching `cmp r0,#0xF5` statically.
* The gated Special Cup: moving the cursor past Star Cup does not select it,
  and A on that position returns to Star Cup (`special_cup_A.png`) — the
  selection bound is 0..3 until the save bit is set.
* Erase confirmation defaults to NO; only an explicit YES path performs the
  flash erase (canary check above).

**Text/button search space (bounded negative).** ROM regions scanned: main
`0x0`–`0x308000`, second image `0x308000`–`0x340000`, third region
`0x340000`–`0x400000`. Keywords `password|cheat|debug|secret|unlock|generator|
code|gold|master|test`: main 2 hits (`Test`, `LEADTESTER`, both credits roles),
second 0, third 0. 28,837 / 1,497 / 1,988 ASCII strings respectively; 1,284
LZ77 blocks decompressed (3.56 MB), 0 keyword hits; 256 single-byte
XOR/ADD/SUB + 14 rotate transforms and 65,536 affine/alphabet mappings of
"CHOOSE A CUP", "CHOOSE A GAME", "TIME TRIAL", "QUICK RUN", "MUSHROOM",
"SINGLE PLAYER" and the erase prompts: 0 hits (text is font/tile-indexed).
VRAM tile sheets and 11 statistically font-like compressed blocks were
rendered; none contained a password/debug text bank. Button space: 8 KEYINPUT
reader sites × all nearby `cmp` immediates → 1 multi-button comparison.

## 7. Validation evidence

* **Observed:** title/menu/pause/Settings/link/erase screens (screenshots on
  disk); erase prompt and `ERASING SAVED DATA…`; `.sav` canaries `0x100/0x200/
  0x1000` = `0xAB` → `0xFF` after YES; both near-miss boots produced no prompt;
  Special Cup A-snap-back; savestate RAM reads (cursor `0x030001B2`, Quick Run
  option bytes `0x03002C6E/70/72`); live GDB read `0x03000000 = 0x0202A400`
  matching the savestate layout.
* **Derived:** `0xF5 = 0x3FF ^ 0x30A` from the `cmp` at `0x0805C94E`; exact-mask
  singleton space; key-state addresses from the literal pool at `0x08011414`;
  savestate offset mapping.
* **Inferred:** the second/third headers are build artifacts / embedded
  alternate revision; purpose not exercised (they are not reachable by normal
  ROM mapping). Quick Run option bytes are real RAM fields but their UI writer
  was not located.

## 8. Unknowns

* No UI path was found that writes the Quick Run laps/items/coins bytes
  (`0x03002C6E/70/72`) — they are documented in TCRF's RAM map and existed as
  zeros in every savestate. Any such screen is either gated by link mode or is
  a leftover; not proven either way.
* The exact role of the embedded second image and blank stub header is not
  proven (no reachable code maps there). JP-version credit strings (`AMKJ`)
  appear in both images.
* Save-bit semantics for the unlockables were not fully enumerated to the
  §16.18 standard (test/setter call-site census): the gated Special Cup was
  proven live, but a complete bit→message map for SNES tracks/backgrounds was
  not derived. These are progression state, not codes, so this does not affect
  the cheat-surface conclusion.

## 9. Tooling

* `arm-none-eabi-objdump -M force-thumb` / `-M force-arm` for ROM disassembly;
  Capstone 5.0.7 + Python for PC-relative literal and KEYINPUT-reader scans.
* `strings -t x`, `grep -abo`, custom LZ77 decompressor (`lz.py`).
* mGBA 0.10.5 + Xvfb `:315` + xdotool; savestate `gbAs` zlib extraction and
  RAM reads (`ss.py`, `gba.py`); mGBA GDB stub (single-connection limitation
  worked around by savestate diffs, per §16.13).
* Screenshots kept on disk in `/tmp/mariokart/`; not redistributed.
* No ROM or copyrighted assets are included in this report; only addresses,
  hashes, algorithms, and observed results.
