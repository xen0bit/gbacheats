# Street Racing Syndicate (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Street Racing Syndicate/Street Racing Syndicate.gba` |
| Size | 4,194,304 bytes (0x400000) |
| Header title | `STREETRACING` |
| Game code / maker | `BCZE` / `AF` (Namco Hometek; "AF" maker code) |
| Revision | 00 (`version=0x00`, complement `0x1B`, header checksum `0x0000`) |
| Entry word | `0xEA00002E` — stock `b 0x080000C0`, **not** a patched cracktro |
| Header logo | valid Nintendo logo at `0x00000004`; single header (multi-header logo scan: 0 hits) |
| Developer credit in ROM | `Raylight Studios S.r.l.` / `Blueroses Technologies` (`0x080423DC`–`0x08042428`) |
| MD5 | `3edf62c20e5c70401c3fa78ef6489055` |
| SHA-1 | `4981be37d8cd402de5a80f17f754c207bd5cfea8` |
| SHA-256 | `7f04167ed84b6ab53e921bf4ffb7796a51fec83372e85037456db9f5833503b4` |

**SKU warning (guide §16.11).** The widely published "Up, Down, Left, Right → Enter Cheat" codes for
*Street Racing Syndicate* belong to the Eutechnyx PS2 / Xbox / GameCube / PC builds (the source page
itself carries a PlayStation trademark notice). This GBA build was made by **Raylight Studios**, is a
different codebase, and contains no cheat subsystem. Treating the console code list as a GBA lead is
the trap this report documents.

## 2. Executive summary

**Result: bounded negative.** The GBA ROM `BCZE` has **no in-game/developer-intended cheat system**: no
password or code-entry screen, no code table, no validator, no button-code sequence, no hidden debug
menu. The only on-screen letter entry is the profile-name field, which is a label, not a validator
(guide §16.2b).

Evidence is a closed set of counts, not a failed search:

* The complete UI string table — **294 entries** at pointer table `0x081F4A70` — was decoded entry by
  entry. **0** entries mention CHEAT, PASSWORD, DEBUG, CODE, or LEVEL SELECT. The main-menu entry set is
  exactly {STREET MODE, ARCADE MODE, MULTIPLAYER, OPTIONS}; OPTIONS is exactly {MUSIC, SFX, CREDITS}.
* A raw byte search across all 4 MiB found **0** occurrences of `cheat`, `password`, `debug`,
  `enter cheat`, or `cheat enabled` in any case; **0** occurrences of any of the 9 published codes in
  ASCII, lowercase, `+0x20`, `±1`, XOR, UTF-16LE/BE, bit-reversed, nibble-swapped, or 5-bit-packed
  forms (one affine "hit" was proven to be an alternating-byte pointer table, not a code).
* The process-descriptor table at `0x08042444` has **29 named processes**; **0** are cheat/debug
  screens. The only suspicious name, `SelLevelProcess`, has two **no-op `bx lr`** functions
  (`0x080167D9`, `0x080167DD`) — dead stub code.
* The single 4-step sequence validator found in the ROM (`0x08030748`) was traced by call graph to
  **MPWaitProcess** (`0x0801CDD0`, Thumb pointer at `0x080429F8`, called with args `(1,2,0)`). It
  validates a 4-word **multiplayer link handshake** in EWRAM and reads `JOYCNT`; it is not driven by
  controller input and is not a cheat.
* The central key-state routine (`0x08027448`) keeps only current/previous/raw masks — **no ring
  buffer** of button presses exists. Searches for the Up/Down/Left/Right mask sequence in active-high
  and active-low `u16`/`u8` forms returned **0** hits.
* Dynamic: the published Up/Down/Left/Right input produced **no screen change** in mGBA at three
  different timings; 10 additional hidden-key combinations produced no hidden screen. Every reachable
  screen was walked (§3).

## 3. How to reproduce

* Emulator: mGBA 0.10.5 under Xvfb `:315`, `SDL_AUDIODRIVER=dummy`, `-3` scaling.
* Keymap (mGBA SDL default): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`,
  D-pad=arrow keys. Hold keys 100–200 ms; menus debounce and can double-step on shorter holds.
* Boot path: `Start` through the Namco / Raylight logos → profile screen → `A` on **LOAD PROFILE**
  (or New Profile → name → Confirm Name → SAVING DATA) → **MAIN MENU**.
* Cheat-sequence attempts at MAIN MENU (Street Mode highlighted):
  * `Up,Down,Left,Right` with 150 ms holds (3×),
  * same with 60 ms holds,
  * same with ~0 ms gaps,
  * from each of the four menu cursor positions.
  * Result: no transition, no "Enter Cheat" screen, no confirmation text.
* Hidden-combo sweep at MAIN MENU: `L+R`, `Start+Select`, `A+B`, `L+R+Start`, `L+R+Select`,
  `↑↑↓↓←→←→`, `Select`, `L`, `R`, `Start`. Result: no hidden screen; `Start` returns to the profile
  screen, all others leave the menu unchanged.
* Screenshots (kept in the analysis work dir, not redistributed): `s_mainmenu.png`, `scr_options_inside.png`,
  `scr_pause_menu2.png`, `scr_after_progress.png`, `s_cheat_attempt2.png`, `combo_0.png`–`combo_9.png`.

## 4. Address map

| Address | Meaning | Evidence |
|---|---|---|
| `0x08000000` | Stock ARM entry `0xEA00002E` → `0x080000C0` | Derived (header bytes) |
| `0x080005E4` | `ldr r0,=0x04000130; ldrh r0,[r0]; eors r1,r0` — once-per-frame `KEYINPUT` read, mask `0x03FF` | Derived (disassembly) |
| `0x08027448` | Key-state updater: `[+0]` current, `[+2]` previous, `[+4]` timer, `[+8]` optional remap table, `[+12]` raw. **No history buffer.** | Derived |
| `0x08030748` | 4-word sequence validator — EWRAM table `0x02003B9A`, counter `0x02003BA2`, reads `JOYCNT` (`0x04000128`) | Derived |
| `0x0801CDD0` | **MPWaitProcess** update; `bl 0x08030748` at `0x0801CED0` with `(r0=1,r1=2,r2=0)`; Thumb ptr `0x0801CDD1` at `0x080429F8` | Derived |
| `0x080423DC`–`0x08042A48` | 29 process descriptors (name string, self-name pointer, 7 function pointers, `0x00000000` terminator; record length 0x34–0x38 depending on name padding) | Derived |
| `0x08042A18` | `SelLevelProcess` descriptor; its two functions `0x080167D9` / `0x080167DD` are `bx lr` | Derived |
| `0x08043120`–`0x08044400` | ASCII UI text bank (strings referenced by ID) | Derived + observed on screen |
| `0x081F4A70` | UI string pointer table, 294 valid entries (entry 294 = `0x081F4A70` self-reference terminates it) | Derived |
| `0x02003B9A` / `0x02003BA2` / `0x02003BA3` | EWRAM multiplayer handshake words (not cheat state) | Derived |

## 5. Algorithm

Not applicable — no validator exists. The central input path is:

```
KEYINPUT (0x04000130, active-low)
  -> ~mask 0x03FF                       @ 0x080005E4
  -> key_state_update(current, mask)   @ 0x08027448
       stores current/previous/raw only; no press-history array
  -> each process reads current/previous from its own global
```

The only comparison of a multi-element press sequence is the multiplayer handshake at `0x08030748`:

```
copy u16 words from [0x02003B9A] into stack[0..3]
require (w0>>8)&0xF == 1 and w0>>12 == 1
require w1>>12 == 2, w2>>12 == 3, w3>>12 == 4   # increment counter 0x02003BA2 per match
recount matches, require counter == recount
store (JOYCNT >> 6) & 3 at 0x02003BA3
return 12 on success, 0 or -1 otherwise
```

This routine is reached **only** from the multiplayer-wait process and takes fixed arguments `(1,2,0)`;
no controller-history buffer feeds it. It cannot be a controller cheat.

## 6. Tables

### 6.1 UI string table (complete, 294 entries at `0x081F4A70`)

Representative entries and their screen context:

| IDs | Strings | Screen |
|---|---|---|
| 0–5 | PRESS START, MAIN MENU, STREET MODE, ARCADE MODE, MULTIPLAYER, OPTIONS | title / main menu |
| 6–9 | QUICK RACE, CHECKPOINT, IRON MAN, SPEED TRIAL | arcade mode |
| 10–15 | MUSIC ON/OFF, SFX ON/OFF, CONTROLLER, CREDITS | options |
| 16–24 | LOAD PROFILE, NEW PROFILE, Profile name, SAVE FAILED!, LOADING DATA, SAVING DATA | profile |
| 28–37 | PAUSED, PAUSE MENU, Resume, Progress, Quit Race, Race again, Change Car | pause |
| 38–44 | PROGRESS, CARS, PHOTOS, RACES, CHALLENGES, GIRLS, RATE | progress |
| 74–84 | GARAGE, UPGRADES, COSMETICS, REPAIR, DYNO, COLORS, VYNILS | garage |
| 160–168 | CITY MAP, Crew Meets, ... Quit Game | city map |
| 272–288 | CONNECTION ERROR!, Please wait, Player 1/2, You win!/lose! | multiplayer |
| 289–293 | Invalid Lap, Premi Start, Appuie sur Start, Start drücken, Pulsa Start | race / localisation |

**Cheat/code/debug/level-select entries: 0 of 294.** Note `CONTROLLER` (ID 14) exists in the bank but
is not an options-menu entry — the OPTIONS menu renders exactly 3 rows (observed; Down from CREDITS
wraps to MUSIC). It is a leftover/label string, not a hidden menu.

### 6.2 Process descriptor table (`0x08042444`, 29 entries)

```
Agblogo, ProfileMenu, Mainmenu, Credits, CarSel, CitySel, TrackSel, FirstRace,
Mapmenu, Progress, Garage, Dyno, Showroom, Warehouse, GirlGallery, Girlfriends,
CrewMeet, RespectCh, RespectEnd, StreetCh, Tracks, Pausemenu, RankMenu, EndRace,
SaveError, MPLinkError, MPMenu, MPWait, SelLevel
```

Cheat/debug-named processes: **0 of 29**. `SelLevelProcess` is the only nominally debug-like entry and
is a no-op stub.

### 6.3 Published codes tested (all rejected / absent)

| Code | Published effect | ROM occurrences (all encodings) | In-game result |
|---|---|---|---|
| LETMEGO | 3 police warnings | 0 | no cheat screen reachable |
| FIXITUP | free car repair | 0 | " |
| GORETRO | Pac-Man vinyl | 0 | " |
| GOTPOPO | police V8 interceptor | 0 | " |
| RENESIS | Mazda RX-8 | 0 | " |
| IGOTGST | Mitsubishi Eclipse GS-T | 0 | " |
| SICKGDB | Subaru Impreza S202 STi | 0 | " |
| MYTCGTS | Toyota Celica GT-S | 0 | " |
| SICKJZA | 1996 Toyota Supra RZ | 0 | " |

## 6b. Enumeration

**Space size: 0.** There is no code space to enumerate. The accepted-set cardinality is **0**, proven
by the following bounded counts rather than by absence of effort:

| Search space checked | Count | Hits |
|---|---:|---:|
| UI string-table entries decoded (`0x081F4A70`) | 294 | 0 cheat/code/debug entries |
| Raw `cheat` / `password` / `debug` / `enter cheat` / `cheat enabled` byte strings, case-insensitive | 5 patterns × 4 MiB | 0 each |
| Published codes × encodings (ASCII, lower, +0x20, ±1, XOR1, XOR0x20, UTF-16LE/BE, reversed, bitrev, nibswap, 5-bit A=1/0) | 9 × 12 = 108 tests | 0 valid |
| Process descriptors enumerated | 29 | 0 cheat/debug; 1 dead `SelLevel` stub |
| KEYINPUT literal occurrences in ROM (`0x04000130`) | 4 | 2 in boot loop, 2 in MP validator |
| KEYINPUT-reading functions | 2 | 0 with press history |
| UDLR mask-sequence patterns (active-high/active-low × u16/u8) | 4 | 0 |
| Multi-element sequence validators found | 1 | 0 controller-driven (MP handshake only) |
| D-pad sequences entered in emulator (timings × cursor positions) | ≥12 | 0 transitions |
| Hidden key combinations entered in emulator | 10 | 0 hidden screens |
| Reachable screens walked with screenshots | 9 | 0 code-entry screens |

**Novel code:** none possible — minting requires a validator or a table; neither exists. Per §0.2 this
is reported as a *bounded negative* with the search space and counts above, not as an untested guess.

**Rejection bounds:** every published console code was "rejected" in the sense that the GBA SKU has no
entry surface at all: the required Up/Down/Left/Right gate does not exist (no key-history comparison in
the ROM, no transition in the emulator). Out-of-range/ill-formed inputs cannot be submitted because no
input field exists. The nearest analogue — an attempt to type letters at the main menu — maps to menu
navigation only, and the only letter-entry field (profile name) has no comparison consumer.

**Negative classification (guide §16.3): "No system"** — there is no alphabet, table, validator, or
input surface. It is not dead code (no cheat handlers exist), not a cut feature (no `TEMP` rows), and
not a gated feature (no screen-state gate). The console game's system was simply not ported to this SKU.

## 7. Validation evidence

* **Observed** — mGBA screenshots: boot/Namco/Raylight logos, profile load/name entry, main menu
  (4 rows), options (3 rows, wrap-around confirmed), in-race HUD, pause menu (3 rows), Progress screen,
  no visual change after UDLR or any of 10 hidden combos.
* **Derived** — UI pointer table (294 entries), process descriptors (29), `bx lr` stubs at
  `0x080167D9/DD`, call graph `MPWaitProcess → 0x08030748` with args `(1,2,0)`, central key-state
  struct with no history, all encoding searches with counts above.
* **Inferred** — the console code list was written for Eutechnyx's build; Raylight's GBA port omitted
  the feature. The exact reason (time, platform constraints) is not in the ROM.

## 8. Unknowns

* `CONTROLLER` (string ID 14) is present in the bank but never rendered in OPTIONS on this build. It
  may be a leftover from the console UI; no call site that draws it in a menu was proven.
* The ROM contains a debug-symbol-style process-name table (unusual for a retail build). Whether an
  unreferenced cheat process was removed from *this* revision rather than never included cannot be
  proven from the binary alone; all 29 present descriptors were checked.
* The EWRAM multiplayer handshake at `0x02003B9A` was analysed statically only; its runtime values were
  not dumped (GDB stub on the available mGBA build did not complete connections).
* No attempt was made to synthesise console-version codes via save editing — out of scope (no GBA
  code surface), and no GameShark/CodeBreaker/AR codes were used.

## 9. Tooling

* `file`, `md5sum`, `sha1sum`, `sha256sum` for identity.
* `strings -t x`, `grep -abo`, custom Python scanners for pointers, encodings, and key-mask patterns.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for disassembly.
* mGBA 0.10.5 + Xvfb `:315` + openbox + `xdotool` (XTEST) + `scrot`; Python helper `key.py` and
  `combo.py` in `/tmp/opencode/streetracing/`.
* GDB stub attempted but non-responsive; conclusion rests on static evidence plus emulator observation.

No ROM or copyrighted assets are redistributed in this report; only hashes, addresses, and generated
findings are published.
