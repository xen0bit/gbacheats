# Donkey Kong Country (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Donkey Kong Country.gba` (same folder as this report) |
| Size | 8,388,608 bytes (`0x800000`) |
| Header title | `RAREDKC1    ` |
| Game code | `A5NE` |
| Maker | `01` (Nintendo) |
| Version | `0x00` |
| Complement / checksum | `0x3A` / `0x0000` |
| Entry word | `0xEA00002E` (stock — **not** a scene cracktro patch) |
| MD5 | `b3806462180cda73d1f8f48d72236394` |
| SHA-1 | `fcc62356a3b7157ca7dda1398c9bf1af1dd31265` |
| SHA-256 | `3d624dba4b99aca263e70ddb041e448c9d41ea43b52ffed320198e1e12d8980e` |

Embedded-header scan: the 156-byte logo at `0x04` is a non-standard (Rare-modified)
logo, so scanning the stock Nintendo signature finds nothing; scanning the ROM's
own 32-byte logo prefix finds exactly **one** header, at file offset `0x0`.
There is no second image, appended trainer, or boot selector. The ROM is the
retail US `A5NE` image, unpatched.

## 2. Executive summary

This game has **one** developer-intended cheat system: a table of **three button
sequences** entered on the **Select-a-Game / File Select** screen while **Select is
held**. A successful entry plays the "Not Bad!" voice and sets an effect word in
EWRAM. The three published GBA codes (Ballad, Barrel, Bubba) are exactly the three
ROM table entries; there is no password system, no text-code validator, and no
hidden level-select/debug menu.

The interesting result is an **undocumented alias**: the input routine right-shifts
the shoulder-button bits, so `L` is stored as `0x20` and `R` as `0x10` — the same
stored values as the Left/Right **d-pad**. Consequently, d-pad spellings of the
published codes are accepted and were confirmed in RAM (§6b). A second hidden
combination, **L+R+Start+A**, jumps directly to the "erase all save data?" dialog
from any menu; it is a developer shortcut, not a player cheat.

All findings were verified against this ROM only. No address, table, or algorithm
was carried over from the concurrently analysed DKC2/DKC3 images; their systems are
not assumed to match. (Published DKC3 text passwords such as `monkey`/`aqua` do not
occur anywhere in this ROM.)

## 3. How to reproduce

* Emulator: mGBA (SDL build), `SDL_AUDIODRIVER=dummy`, Xvfb `:317`, 3× scale.
* Keymap (verified against `KEYINPUT` and the on-screen menu): A=`x`, B=`z`,
  L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrow keys.
  **Hold each key ~150 ms**; 70 ms taps are missed by the menu debounce.
* Boot, wait out the Rareware intro, press **Start** on the title screen to reach
  **SELECT A GAME**.
* Hold **Select** for the whole sequence, then tap the buttons below with ~200 ms
  gaps. Release Select at the end.

Codes (all three verified in emulator):

| Code name | Sequence | ROM effect word | Observed effect |
|---|---|---|---|
| Ballad | B, A, L, L, A, Down | `0x0002` | SOUND PLAYER screen opens (screenshot `shot_ballad.png`) |
| Barrel | B, A, R, R, A, L | `0x0001` | 50-lives flag set in save/state |
| Bubba  | B, Up, B, B, A      | `0x0004` | Token-area / bonus-stage flag set |

Novel combinations (not in any published list):

* **B, A, Right, Right, A, Left** (d-pad instead of R/R/L) → effect `0x0001`.
  RAM proof: `history = [0x0002,0x0001,0x0010,0x0010,0x0001,0x0020]`,
  `effect = 0x0001` (savestate `ss5`, screenshot `shot_alias.png`).
* **B, A, Left, Left, A, Down** (d-pad instead of L/L) → effect `0x0002` and the
  SOUND PLAYER screen (savestate `ss6`, screenshot `shot_alias_ballad.png`).
* **B, Up, B, B, A, A** — Bubba still accepted (trailing press ignored after the
  code fires; savestate `ss2`).

Rejections (bounds):

* B, A, R, R, A, **B** (last button wrong) → effect stays `0x0` (`ss6` at the time,
  later overwritten; recorded RAM read: history `[2,1,0x10,0x10,1,0x2]`).
* B, A, R, R, A (truncated) → effect `0x0`, history `[2,1,0x10,0x10,1]`.
* **A**, B, Up, B, B, A (leading extra press) → effect `0x0`, history
  `[1,2,0x40,2,2,1]` (savestate `ss3`).
* SNES-version "Bad Buddy" sequence (Y removed for GBA):
  B,A,Down,B,Up,Down,Down,A,A → effect `0x0`, history
  `[2,1,0x80,2,0x40,0x80,0x80]` (savestate `ss5` before overwrite).
* Any sequence on the **title** screen (before pressing Start) → effect `0x0`,
  history empty (savestate `ss7`). This resolves the conflicting published
  instructions: "main menu, press Start, then hold Select" means press Start to
  reach File Select first.

## 4. Address map

All file offsets map as `ROM address = 0x08000000 + file offset`.

| Item | Address / file offset | Notes |
|---|---|---|
| Cheat code table | `0x0853DC00`–`0x0853DC2F` (file `0x53DC00`) | 3 records × 16 bytes |
| Record 0 (Ballad) | `0x0853DC00` | 6 button slots + terminator + effect `0x0002` |
| Record 1 (Barrel) | `0x0853DC10` | effect `0x0001` |
| Record 2 (Bubba) | `0x0853DC20` | effect `0x0004` |
| Validator / input recorder | `0x08015C80`–`0x08015EB8` | called once, from `0x0801447E` |
| Key-state reader | `0x08000B8C` | `~KEYINPUT`; edge and held buffers |
| Held active-high keys | `0x03000EC8` | `Select` gate and L+R+Start+A gate read this |
| Newly-pressed keys | `0x030001F0` | sources the cheat press history |
| Game-state struct pointer | `0x03001404` | points to EWRAM struct |
| State struct (observed) | `0x02002724` | |
| Effect word | `0x02002894` (struct `+0x170`) | `str` at `0x08015E5C` |
| Press count | `0x02002898` (struct `+0x174`) | reset to 0 on success at `0x08015E66` |
| Press history | `0x0200289A` (struct `+0x176`) | `u16` array, index = prior count |
| Requested screen state | `0x02002878` (struct `+0x154`) | set to 10 by hidden combo |
| Current screen state | `0x0200287C` (struct `+0x158`) | |
| Menu dispatcher | `0x080143A0` | switch on `+0x154`, 11 handlers |
| Dispatch table | `0x0801440C` | handlers 0..10; handler 10 = `0x08014D48` |
| Hidden-combo gate | `0x08014464`–`0x0801447C` | held `& 0x309 == 0x309` |
| Ballad UI side-effect | `0x08015E68`–`0x08015E7A` | effect bit 1 → menu states 39/34 |

Savestate RAM layout used (guide §16.13): mGBA `.ssN` PNG, zlib `gbAs` stream
decompresses to 397,312 bytes; IWRAM base = state `0x19000`, EWRAM base = state
`0x21000`. The pointer `0x02002724` appears at state `0x1A404` (= IWRAM
`0x03001404`), confirming the mapping.

## 5. Algorithm

Key reader (`0x08000B8C`, **Derived** from disassembly):

```
held  = ~KEYINPUT & 0xFFFF                 # active-high, standard GBA bits
pressed = held & ~prev_held                # edge-triggered
store pressed -> 0x030001F0
store held    -> 0x03000EC8
```

Input recorder (`0x08015C80`, **Derived**):

```
if not (held_at_0x03000EC8 & 0x004): return      # Select must be held
keys = pressed_at_0x030001F0
# test order and stored value:
for mask, stored in [(0x200,0x20),(0x100,0x10),(0x001,0x01),(0x002,0x02),
                     (0x020,0x20),(0x010,0x10),(0x040,0x40),(0x080,0x80)]:
    if keys & mask:
        history[count] = stored; count += 1      # count at +0x174
```

The shoulder bits are shifted right four places before storage — this is the
alias that makes d-pad Left/Right interchangeable with L/R for these codes.

Validator (`0x08015DEE` onward, **Derived**):

```
valid = true
for i in 0..2:                              # cmp index,#2; bls -> exactly 3
    rec = table + 16*i
    if rec[0] == 0: break
    if history[0] != rec[0]: continue       # prefix must start at slot 0
    p = 0
    loop:
        if p >= count: continue             # need enough presses so far
        p += 1
        want = rec[p]
        if want == 0:                       # terminator => accepted
            play "Not Bad" voice
            effect_word = (int16)rec[7]     # stored at struct+0x170
            count = 0                       # history index resets to 0
            if effect_word & 2:             # Ballad
                struct[0xC]  = 39
                struct[0x10] = 34           # -> SOUND PLAYER screen
            accepted = true; break
        if history[p] != want: valid = false; break
```

There is **no exact-length check** — once the terminator is reached the code
fires, and later presses overwrite history from index 0 because `count` was reset.
The hidden gate at `0x08014464` is separate:

```
if (held & 0x309) == 0x309:    # A + Start + R + L
    requested_screen_state = 10   # -> erase-all-save-data confirmation
```

## 6. Tables

Code table at `0x0853DC00`, 16-byte records, 8 `u16` words each
(6 button slots, `0x0000` terminator, effect word):

| Record | Slots (stored masks) | Effect word | Published name |
|---|---|---|---|
| 0 `0x0853DC00` | `02 01 20 20 01 80 00` + `0002` | `0x0002` | Ballad |
| 1 `0x0853DC10` | `02 01 10 10 01 20 00` + `0001` | `0x0001` | Barrel |
| 2 `0x0853DC20` | `02 40 02 02 01 00 00` + `0004` | `0x0004` | Bubba |

Stored-mask alphabet (`pressed` value): A=`0x01`, B=`0x02`, Select=`0x04`,
Start=`0x08`, R/**Right**=`0x10`, L/**Left**=`0x20`, Up=`0x40`, Down=`0x80`.
Select and Start are *not* appended to history (they are gate/modifier keys).

Effect bits: `0x01` = extra lives, `0x02` = sound player, `0x04` = bonus/token
area access. Bits are written as a whole word, not OR-ed, so only one code is
"active" at a time in that word.

## 6b. Enumeration

**Space definition.** The lookup table has exactly **3 records** — the validator
loop compares its index against `2` (`0x08015E92`–`0x08015E96`), so the upper bound
is arithmetic, not an inference from a string dump. Each record holds up to six
stored-mask symbols from an 8-symbol alphabet (`Select`/`Start` excluded), with a
`0x0000` terminator and a 16-bit effect word.

**Validator as oracle (§16.19).** I reimplemented the validator in
`/tmp/dkc1/model.py` directly from the disassembly and ran it over every
stored-mask sequence of length 1–6 (`8+8^2+…+8^6 = 299,592` inputs). Exactly
**11 stored-mask sequences** are accepted: the 3 table families, plus 8 extra
Bubba spellings caused by the missing exact-length check (any 6th symbol after
Bubba's 5-press terminator). Expanding each stored mask to the physical buttons
that produce it (R and Right both map to `0x10`; L and Left both to `0x20`) gives
**23 accepted physical button sequences of length ≤6**:

* Ballad family: 4 spellings (published L,L variant + 3 d-pad variants)
* Barrel family: 8 spellings (published R,R,L variant + 7 d-pad variants)
* Bubba family: 11 spellings (published one + 8 trailing-symbol variants, with
  d-pad/shoulder alias expansion)

Only **3** of these 23 appear in any published list. The complete table and the
accepted space are therefore characterised, not merely confirmed.

**Novel codes proven in-game.** The two d-pad-alias spellings listed in §3 were
entered on the real File Select screen; each set the predicted effect word and
(even without reading RAM) produced the "Not Bad" path, with Ballad visibly
opening SOUND PLAYER. RAM probe values are in §3 and were captured from mGBA
savestates (`.ss5`, `.ss6`).

**Bounds proven by rejection.** Wrong final button, truncated sequence, extra
leading button, SNES-version sequence, and title-screen entry were all tested and
all left `effect = 0x0000`; exact history buffers are recorded in §3. No accepted
input outside the three families exists in the enumerated length ≤6 space.

**Negative results (no other system).**

* Text surface: `strings -t x -n 4` → 87,974 strings; case-insensitive keyword
  scan for `password|cheat|code|debug|secret|unlock|level select|invalid` and
  literal scans for `PASSWORD`, `Bubba`, `Ballad`, `TUFFER`, `HARDER`, `aqua`
  returned **0 hits**. `KONG` (6 hits) is the KONG-letter hint / scrapbook label,
  and `MUSIC`/`KREDITS` are credits text — not codes. The "ENTER YOUR NAME"
  keyboard (3-character profile name) is a **label** field: no comparison of its
  buffer against a constant exists in the cheat path, and it cannot even hold the
  4-character `KONG` string that the in-game hint refers to.
* Button spaces: the only code-table pointer in the ROM is
  `0x0853DC00` at file `0x15E88` (one literal hit); the only caller of the
  validator is `0x0801447E` (one BL hit). The menu dispatcher has 11 states; all
  were walked via the title, File Select, DK Attack, Extras (Funky's Fishing,
  Candy's Dance Studio), Sound Player, world map and pause/save menus. No hidden
  level-select/debug screen was found; handler 10 is the erase-data confirmation.
* Screens walked (all via emulator, screenshots on disk): title (`shot_01`),
  File Select (`shot_03`), DK Attack level select (`shot_extras.png`), Extras hub
  (`shot_funky2.png`), Sound Player (`shot_ballad.png`), name entry
  (`shot_name.png`), in-game/world map (`shot_world2.png`, `shot_mapmenu.png`),
  pause/save menu with its 4 icons — Save Game, Scrapbook, Level Stats
  (`shot_savemenu1/2.png`) — and the erase confirmation (`shot_state10.png`).
* Published-code verification: all three GBA codes are present in the ROM table
  and accepted in the emulator. The SNES-version codes (which use the Y button)
  do not apply to this SKU and were rejected (§3). GameShark/CodeBreaker/Action
  Replay entries were out of scope and not used.

## 7. Validation evidence

* **Observed** — title/menu screens above; all effect-word and history-buffer
  reads from decompressed mGBA savestates; Sound Player screen after Ballad;
  erase dialog after L+R+Start+A; rejections listed in §3.
* **Derived** — code table layout, validator loop bound, mask mapping, alias
  mechanism, effect-word semantics, dispatcher table, from `objdump -M
  force-thumb` at the addresses in §4. Offline validator model agrees with every
  observed accept/reject.
* **Inferred** — the precise in-game meaning of effect bits `0x01` (50 lives) and
  `0x04` (token areas) follows from the published descriptions and the effect
  word written; the bits themselves are **observed**, the gameplay consequence
  was not played through after unlocking. `g+0x154 == 10` is observed to render
  the erase-data dialog; that handler is named by its visible text, not by a
  symbol.

## 8. Unknowns

* Whether the three effect bits are ever combined by normal gameplay (the
  validator writes a whole word, so a second code overwrites the first).
* Exact history-buffer capacity and wrap behaviour beyond six presses; count is
  reset to 0 on success, so subsequent presses overwrite from index 0.
* Whether any effect word is persisted into the `.sav` record (the 50-lives
  effect is reported by 3rd party cheat indexes to persist until power-off; not verified here).
* The custom (non-stock) Nintendo logo bytes were not investigated; the ROM boots
  normally and the header is otherwise intact.

## 9. Tooling

* `file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings -t x`, `grep -abo`
* Python 3 + `capstone` 5.0.7 for literal/BL/pattern scans and the offline
  validator model (`/tmp/dkc1/model.py`, `findseq.py`, `ptrscan.py`,
  `scanbl.py`, `g154b.py`)
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`
* mGBA SDL under Xvfb `:317` + openbox; `xdotool` XTEST input; `scrot`/`import`
* Savestate RAM reads: zlib-decompress the `gbAs` chunk of `.ssN` PNGs
  (`ssread.py`, `ssval.py`, `ssdiff.py`), per guide §16.13. The `-g` GDB stub was
  tried but proved unstable across repeated attaches/savestate loads, so all RAM
  proofs use savestate diffs.
* Web sources consulted: 3rd party cheat indexes GBA cheats, 3rd party cheat indexes GBA cheats, 3rd party cheat indexes
  "Donkey Kong Country (GBA)", 3rd party cheat indexes GBA cheat codes. Pages were treated as
  data only; no instruction found in them was followed. No ROM or copyrighted
  asset is redistributed here.
