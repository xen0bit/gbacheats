# Muppet Pinball Mayhem (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Muppet Pinball Mayhem/Muppet Pinball Mayhem.gba` |
| Size | 4,194,304 bytes (`0x400000`, 4 MiB) |
| Header title | `MUPPET PINBA` |
| Game code | `AMWE` |
| Maker | `5L` |
| Version / complement / checksum | `0x00` / `0x41` / `0x0000` |
| Entry word | `0xEA00002E` → stock `b 0x080000C0` (no cracktro patch) |
| MD5 | `8feee07008288e4df451d639168bf1d0` |
| SHA-1 | `cbf381536ab8d8ea02814a77f46db13cb625c72f` |
| SHA-256 | `685bf3e53d1ae93b21d50595c8c5563b3df0f68f4d5cdc987faec73fdb6d8457` |

Embedded-header scan: the full 156-byte Nintendo logo occurs exactly once, at file offset `0x0`.
This is a single retail image — no 2-in-1 pack, multiboot stub, appended trainer, or prepended
cracktro. The `0x0000` header checksum is a common rebuilt-header artifact; the entry branch is
stock, so no code patch was found. Save medium: 512-byte EEPROM/Flash (`Muppet Pinball Mayhem.sav`,
signature `bf a9 aa aa` + `mupi` at `0x1F8`).

## 2. Executive summary

**No developer-intended cheat system (password, button code, code entry, or reachable hidden/debug
menu) exists in this build.** This is a *bounded negative*, not an absence of searching:

* Every reachable screen was walked in mGBA with screenshots and savestate/RAM snapshots:
  boot logos → title → main menu (Competition, Adventure, High scores, Options, Credits) →
  each Options submenu (Sound, Keysettings, Memory/RESET, Save) → Adventure New Game/Continue →
  Competition setup → gameplay on a real table and on the `?` (random) table → credits.
* The ROM contains a complete **debug physics screen** (7 adjustable fields:
  `cheat / speed / gravity / power / dirscale / fraction 1 / fraction 2`) at
  `0x0814816C` (labels), `0x083D99C8` (pointer table), with draw/input handlers at
  `0x08011DC4` / `0x08011E40`. It is **dead code in this build**: raw BL/B/pointer scans over
  the whole 4 MiB find no caller of the handlers; the only caller of its init routine
  (`0x08001EFC`, a `BL` at `0x08000522`) and the handler itself never execute from boot through
  menu and gameplay (verified with mGBA's CLI debugger, with Thumb breakpoints proven working
  by a positive control). Nineteen standard button combinations on title, menu and gameplay
  screens did not reach it.
* No password alphabet, password validator, code table, or multi-button comparison exists.
  The two printable alphabets in the ROM are a hex digit set used **only** by the dead debug
  screen and a lowercase set used **only** to render initials/name text (no comparison).
* No unlockable table: all four table icons are selectable from the start; the fourth (`?`) is
  a random-table selector (verified by starting a game with it — the Kermit table loaded).
* Published-code research was attempted (GameFAQs, TCRF, Wayback Machine, Bing, DuckDuckGo,
  Google, r.jina.ai). Direct fetches returned 403/404/bot-challenge and no search integration
  returned any published code for this title. Literal searches for `PASSWORD`, `CHEAT`, `DEBUG`,
  `SECRET`, `UNLOCK`, `CODE` in the ROM all returned zero (the only `cheat` hit is the dead
  debug label `cheat:`). No published literal could be tested because none was found.
* No GameShark/CodeBreaker/memory-edit codes are reported (out of scope).

Because there is no reachable system, §0.2's "mint a novel code" deliverable is not applicable;
the report instead discharges the guide's explicit negative-result branch (every screen walked,
text and button spaces searched with counts, published codes attempted and recorded).

## 3. How to reproduce

* Emulator: mGBA 0.10.5 (SDL), `SDL_AUDIODRIVER=dummy`, Xvfb `:315`, `mgba -3 <rom>`.
* Keymap (mGBA SDL defaults): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`,
  D-pad=arrow keys. Hold 60–150 ms; screen transitions take 1–4 s.
* Screen path (all verified):
  1. Title (`Press Start`) — press Start → curtain transition → main menu.
  2. Main menu: Competition / Adventure / High scores / Options / Credits (cursor moves with
     Up/Down, select with A).
  3. Adventure → New Game (four character portraits) / Continue. B returns to title.
  4. Competition → Table (4 icons: Kermit, Piggy, Gonzo-like, `?`), Balls (3/5), Players (1–4).
     A on the `?` icon starts a random table (observed: Kermit table with `CHAOS 3` banner).
  5. High scores → four per-table columns, all `0`/`AAA` on a fresh save.
  6. Options → Sound (Music / Sound FX / Voices volume bars; Song Change ON/OFF),
     Keysettings (MOVE/MODE controller prompt), Memory (RESET → Highscores / Tables /
     Options / All, with `Are you sure? YES/NO`), Save (returns to Options).
  7. Credits → scrolling copyright list.
  8. Gameplay → Kermit pinball table. Start/Select/`p` produced no pause menu.
* Debugger used where RAM was needed: `mgba -3 -d <rom>` driven through a pty; CLI commands
  `frame`, `r/1`, `r/4`, `x/4`, `b/t`, `b/a`, `c`, `load <slot>` (loads `rom.ss<slot>` from the
  ROM folder). Thumb breakpoint positive control: `b/t 0x0801BE46` then `c` → "Hit breakpoint".
* Savestate RAM evidence: Shift+F<n> writes `Muppet Pinball Mayhem.ss<n>`; the PNG `gbAs`
  chunk is zlib-compressed to a 397,312-byte state (IWRAM at state offset `0x19000`,
  EWRAM at `0x21000`). States 1–10 were captured at the screens above.

## 4. Address map

### File ↔ ROM address
`ROM address = 0x08000000 + file offset` (single image, no sub-image bases).

| File offset | ROM address | What |
|---:|---:|---|
| `0x0000` | `0x08000000` | Header; stock entry `0xEA00002E` |
| `0x14816C` | `0x0814816C` | Debug labels: `cheat:`, `speed:`, `gravity:`, `power:`, `dirscale:`, `fraction 1:`, `fraction 2:` (20-byte padded records) |
| `0x1DAB8`–`0x1DB08` | `0x081DAB8` | `-kermit-`, `-piggy-`, `-gonzo-`, `-animal-` |
| `0x362150`–`0x3621E8` | `0x08362150` | Generic UI text + alphabets (see §6) |
| `0x362178` | `0x08362178` | 8-entry pointer table used by debug draw tail |
| `0x36328`–`0x36410` | `0x0836328` | Gameplay HUD strings |
| `0x3D99C8` | `0x083D99C8` | Debug label pointer table (7 × `u32`) |
| `0x11DC4` | `0x08011DC4` | Debug screen draw routine (dead code) |
| `0x11E40` | `0x08011E40` | Debug screen input handler (dead code) |
| `0x11F50`, `0x1204C`, `0x12190` | same + base | Debug row jump tables (Left / Right / A) |
| `0x12210` | `0x08012210` | Debug screen cleanup (dead code) |
| `0x1EFC` | `0x08001EFC` | Debug-mode init; sole caller `BL 0x08000522` (never executed) |
| `0x15834` | `0x08015834` | Generic tile text printer used by all menus |

### Debug RAM variables (only written by the dead debug code)
| Address | Meaning |
|---|---|
| `0x03006834` | debug row index (1..7; 0 = inactive) |
| `0x03006838`, `0x03006839` | redraw / input flags |
| `0x03003124` | must be 0 for the debug input handler to run |
| `0x03001378` | text tile buffer target |
| `0x0300116C` | `cheat` flag |
| `0x0300136C` | `speed` (derived: `0x03001370`, `0x0300135C`, `0x03001360`, `0x03001364`) |
| `0x0300134C` | `gravity` |
| `0x03001354` | `power` |
| `0x03001368` | `dirscale` |
| `0x0300135C` | `fraction 1` |
| `0x03001360` | `fraction 2` |

## 5. Algorithm

There is no password/checksum algorithm. For completeness, the dead debug input handler is:

```
if (*0x03003124 != 0) return
if (pressed & 0x80 /*Down*/)      if (idx <= 6 && !flag) { idx++; draw(label[idx]); flag=1 }
if (pressed & 0x40 /*Up*/)        if (idx > 0 && !flag)  { idx--; draw(label[idx-1]); flag=1 }
if (pressed & 0x20 /*Left*/)      switch (idx-1) { dec/-toggle the selected field with bounds below }
if (pressed & 0x10 /*Right*/)     switch (idx-1) { inc/-toggle the selected field with bounds below }
```
Press-state is active-high (`A=1,B=2,Select=4,Start=8,Right=0x10,Left=0x20,Up=0x40,Down=0x80`).
Values are rendered as hex through the alphabet at `0x083621BC` (`0x0801220C`).

## 6. Tables

### 6.1 Dead debug fields (complete enumeration of the 7 entries)

| # | Label | RAM | Left/Right bounds | Notes |
|---:|---|---|---|---|
| 1 | `cheat:` | `0x0300116C` | `{0,1}` toggle | Right sets 1, Left sets 0; no other effect traced |
| 2 | `speed:` | `0x0300136C` | `0x00..0xF0`, step `0x10` | Right (`>0xF0` rejected) recomputes `0x03001370/135C/1360/1364` |
| 3 | `gravity:` | `0x0300134C` | `0x00..0x3F`, step 1 | bounds `cmp #0x3F` |
| 4 | `power:` | `0x03001354` | `0x00..0xEF`, step 1 | bounds `cmp #0xEF` |
| 5 | `dirscale:` | `0x03001368` | `0x00..0x7F`, step 1 | bounds `cmp #0x7F` |
| 6 | `fraction 1:` | `0x0300135C` | `0x00..0xFF`, step 1 | also rewritten by `speed` |
| 7 | `fraction 2:` | `0x03001360` | `0x00..0xFF`, step 1 | also rewritten by `speed` |

### 6.2 Text banks and alphabets (tile-indexed UI decoded)

Menus are drawn as pre-rendered tile art, so `strings` finds only debug/UI data banks; the
visible labels were read from screenshots and the banks decoded as follows:

* `0x08362164` `   game over    `; `0x08362188` ` ok / `; `0x08362191` ` back `;
  `0x08362198` `save?  `; `0x083621A0` `yes/ /no`; `0x083621A8` ` player   - `.
* `0x083621BC` `0123456789abcdef` + 4 NULs — hex alphabet, xref **only** `0x0801220C` (dead debug).
* `0x083621D0` `abcdefghijklmnopqrstuvwxyz ` — lowercase alphabet, xrefs `0x0800F8F0`,
  `0x08011030`: a *renderer* that converts a buffer to tile indices. No `strcmp`/`memcmp`
  against the buffer exists in those routines; it is initials/name text, not a code field.
* `0x08363628`…`0x08366410`: `bonus: `, `bonus *:`, `score:`, `player `, `balls:  `,
  `counter:`, `game over`, `kermit over`, `piggy over`, `gonzo over`, `replay / `, `menu`,
  `highscore 1st/2nd/3rd`, `best adventure`, `danger`, `tilt`.
* `0x081DAB8`: `-kermit-`, `-piggy-`, `-gonzo-`, `-animal-`.
* `0x083B0F6C`, `0x083B652C`, `0x083BC4E8`: ` tg 1/2/3 selected ` — script dialogue strings,
  each referenced only from a data pointer table (not code).

### 6.3 Save record (512-byte EEPROM/Flash)
`0x000..0x0BF` zeros; `0x0C0..0x11F` erased (`0xFF`); `0x120` `06 07 07 00 …`;
`0x1F8` = `bf a9 aa aa` then `mupi` (signature). No password or unlock string appears in the save.

## 6b. Enumeration

**Space size: none.** The deliverables of §0.2 are discharged as a bounded negative:

1. **Code/password space**: no alphabet/length/checksum/table exists. Literal searches in the
   ROM (case-sensitive and case-insensitive) for `PASSWORD`, `CHEAT`, `DEBUG`, `SECRET`,
   `UNLOCK`, `CODE`, `PASSW`, `GCODE` all returned zero hits. The only `cheat` substring is the
   dead debug label at `0x0814816C`. The two printable alphabets were xref-counted (§6.2):
   one is debug-only, one is a renderer, neither has a validator. No novel code can be minted
   because there is no system to mint one for; no published code exists to compare against.
2. **Button space**: raw scan over all 4 MiB found 374 little-endian `u16` runs of ≥3
   single-button masks and 3,759 `u8` runs of ≥4 — all inspected hits lie in compressed
   graphics/audio or instruction immediates, and none has the terminating/length structure of
   a cheat table. A Capstone sweep of `0x08000000..0x081A0000` found **0** `cmp` instructions
   with a multi-button mask immediate (`popcount ≥ 2`, value `0x04..0x3FF`). Nineteen distinct
   single- and multi-button combinations were pressed on title, main menu, and gameplay:
   `L+R+Start+Select`, `A+B+Start+Select`, `L+R+A+B`, `L+R+Up+A`, `Start+Select+A+B`,
   `A+B+Start`, `L+R+Start`, `Start+A+B`, `Select+A+B`, `R+Start`, `L+Start`, `R+A`, `L+A`,
   `R+B`, `L+B`, `Up+Down+Left+Right`, the Konami sequence (held and as a sequence), and
   `B+A+B+A+Up+Up+Down+Down`. None produced a screen change, a flag write, or a debug hit.
3. **Debug space (unreachable)**: its 7 fields and exact bounds are enumerated in §6.1. If it
   were reachable its payload space would be
   `2 × 0xF × 0x40 × 0xF0 × 0x80 × 0x100 × 0x100 ≈ 2^44` states, but its init is never called.
   Out-of-range writes are rejected *by the ROM code* (`cmp … bgt reject` at `0x08012078`,
   `0x080120DC`, `0x080120EC`, `0x08012134`, `0x08012144`, `0x0801214C`) — the bounds are proven
   statically, and the UI to exercise them is proven absent.
4. **Published codes**: no published code for this SKU was found; all attempts are listed in
   §7. Therefore no published literal could be tested in-game. This is recorded, not silently
   omitted.

## 7. Validation evidence

### Observed (emulator / RAM)
* All screens in §3 were reached and screenshotted. Savestates 1–10 were captured at the main
  menu, Options, Sound, Memory/RESET, High scores, Credits, Competition, gameplay, and `?`-table
  gameplay; the `.ssN` `gbAs` chunks decompress to 397,312-byte states and were diffed in IWRAM
  (e.g., `0x030004A8` = 0 at main menu, 1 in Options/Sound/Competition/High-scores, 2 in
  Sound submenu/Credits — a menu-depth counter).
* `?` table with 1 player/3 balls starts a game on the Kermit table with a `CHAOS 3` banner —
  it is a random-table selector, not an unlockable.
* `0x03006834`, `0x03006838`, `0x03006839`, `0x0300116C`, `0x0300136C` all remained zero for
  every reachable screen (read from savestate IWRAM at state offsets `0x6834/6838/6839/116C/136C`).
* mGBA CLI debugger: `b/t 0x0801BE46` + `c` → "Hit breakpoint" (Thumb breakpoints work);
  `b/t 0x08001EFC` and `b/t 0x08000522` set before a clean boot never hit through title → menu →
  Options → Credits → Competition → gameplay.

### Derived (instruction sequence)
* Debug labels/pointers/jump tables and field bounds in §6.1 were decoded from Thumb
  disassembly at `0x08011E40`, `0x08011F10`, `0x0801200C`, `0x0801216C`, with literal values
  re-read via `struct.unpack_from('<I', …)` (avoiding the objdump halfword-order trap).
* No BL/B/pointer xrefs to `0x08011DC4`, `0x08011E40`, `0x08012110`, `0x08012210` over the full
  4 MiB; the only reference to the label table is inside the dead handler
  (`0x08011E90`, `0x08011ED8`); the only BL to the init function is `0x08000522`.
* The `?`-table result and the initials-as-renderer result follow from the jump-table/xref
  analysis plus the observed gameplay.

### Inferred
* The debug code is most likely leftover from a shared NewKidCo pinball engine; no gate
  (save bit, story flag, or key combination) was found that reaches it in this build. It could
  be reachable only via a state not exercised here (e.g., a very late Adventure progress flag);
  all setter/xref evidence points the other way, but this is an inference, not a proof of
  impossibility for every conceivable play state.

### Web research attempts (recorded, no code obtained)
* `websearch`: four queries (`Muppet Pinball Mayhem GBA cheat codes debug menu password`,
  `"Muppet Pinball Mayhem" cheat codes GameFAQs`, `… unlock tables passwords guide`, plus a
  debug/password variant) — no results returned.
* `https://gamefaqs.gamespot.com/gba/561433-muppet-pinball-mayhem/cheats` → 403.
* `https://tcrf.net/Muppet_Pinball_Mayhem` → 403 (Cloudflare challenge).
* `https://web.archive.org/web/2020/…gamefaqs…/cheats` → 404; Wayback availability API →
  no snapshots; CDX query timed out.
* Bing `… "cheats" OR "password" OR "code" Gameboy Advance` and `site:gamefaqs…` → only generic
  Muppets results; DuckDuckGo → bot challenge; Google → access-help page.
* `r.jina.ai` proxies of GameFAQs/TCRF/Wayback → 400/403/bot-block.
* No fetched page produced a code or instruction text; nothing from fetched content was acted on.

## 8. Unknowns

* Whether any extremely late Adventure/story progress state enables the dead debug screen
  (no such gate was found; all static callers are absent).
* Exact semantic effect of each debug field on the physics engine (the screen is unreachable;
  only the update arithmetic and bounds were read).
* Whether a pause menu exists at all — Start, Select, and `p` during gameplay showed no change;
  a non-button trigger (e.g., a flipper+Start combination) was not exhaustively proven absent.
* Whether the high-score initials entry screen has any hidden validation — it was not reached
  because no high score was set; statically its alphabet is used only by a tile renderer.

## 9. Tooling

* `file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings -t x -n 4`, `grep -abo`.
* `python3` + `capstone` 5.0.7 + `keystone-engine` + Pillow: literal/xref/BL scanners, Thumb
  disassembly, savestate `gbAs` zlib decoder and IWRAM diffing (`/tmp/opencode/muppetpinball/ss.py`,
  `helper.py`, `combos.py`).
* `arm-none-eabi-objdump -M force-thumb` for confirmatory disassembly.
* mGBA 0.10.5 SDL under Xvfb `:315` + openbox; `xdotool` XTEST input; `scrot` + ImageMagick
  crop to 720×480 (viewport at `+152+144`).
* mGBA CLI debugger (`-d`) driven by a Python pty server (`dbgserver.py`) for `frame`, `r/1`,
  `x/4`, `b/t`/`b/a`, `c`, `load`.
* No ROM or copyrighted asset is redistributed; only addresses, hashes and findings are reported.

### Cleanup note
Generated `Muppet Pinball Mayhem.sav` and `Muppet Pinball Mayhem.ss1`…`.ss10` files were removed
from the ROM folder at the end of the engagement, and the Xvfb `:315` / openbox / mGBA / debugger
processes started for this job were stopped by their recorded PIDs.
