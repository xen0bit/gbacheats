# Shrek: Reekin' Havoc (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Shrek: Reekin' Havoc.gba` (8,388,608 bytes = 8 MiB) |
| Header title | `SHREK 3` (title screen: `SHREEK REEKIN' HAVOC`) |
| Game code / maker | `AOIE` / `6S` (TDK Mediactive), version `0x00` |
| Region | Europe, 6 languages (English, Français, Deutsch, Italiano, Español, Nederlands) |
| Entry word | `0xEA0000C2` — stock crt0 branch to `0x080000C0` |
| Header complement / checksum | `0xDA` / `0x0000` (normal rebuild artifact) |
| MD5 | `05d2d50f8aac9d4d6e1889432e197167` |
| SHA-1 | `af0bc8338e49be78ce6e85b59d1ddfca8a10f290` |
| SHA-256 | `55158d0a74d6ec54cbe10e18de751f9e2556c675f1404862adb2a11f8664ed0a` |
| Developer / release | TOSE, 2003 (title screen legal text: "© 2003 DreamWorks … Published and distributed by TDK Mediactive, Inc.") |
| Build tag | ASCII `OptRls` at `0x0804D090`, build date `2003/05/06 16:19:32` at `0x0804D097` |

**Phase 0 result:** single embedded GBA header (Nintendo-logo scan found exactly one hit, at file offset 0). No multiboot/sub-ROM, no scene cracktro, no appended trainer. The first 4 KiB are a normal ARM crt0 (register push, IWRAM/EWRAM setup, BIOS calls) — no patched entry point. This is a genuine development/"Option Release" build that shipped with its debug code intact, not a retail image with a cheat trainer attached.

## 2. Executive summary

**No developer-intended in-game cheat system exists in this ROM.** There is no password entry screen, no button-activation code sequence, no hidden debug menu reachable by controller input, and no unlockable menu entry. This is a **bounded negative** (guide §0.2 point 5 / §16.3), established by:

1. Walking every reachable screen in mGBA (13 distinct screens, §6b) — none offers code entry or a hidden selection.
2. A ROM-wide string/pattern sweep in multiple encodings: zero hits for `PASSWORD`, `CHEAT`, `SECRET`, `LEVEL SELECT`, `GIFT SHOP`, and zero key-mask sequences for the published button combos.
3. The debug menu **does exist as leftover code and data** (3rd party cheat indexes corroborates: "Leftovers from a debug menu that does not appear to be functional anymore"), but its draw routine `0x08015108` and input routine `0x08014BD0` were **never entered** across a full boot→menu→cutscene→gameplay walk plus six distinct boot-time button combos, while a validation breakpoint on the live key handler `0x080004D0` fired immediately. This is a gated/dead feature, not an undiscovered one.

All published "cheats" for this title found on the web are GameShark / CodeBreaker / Action Replay **memory-edit codes** (explicitly out of scope), and the widely published button codes ("10,000 coins", "secret costumes", "enable level select") belong to the **different 2007 game *Shrek the Third*** (Amaze Entertainment) — the §16.11 "same title, different SKU" trap. They are absent from this 2003 TOSE ROM under every encoding checked.

## 3. How to reproduce

- Emulator: mGBA 0.10.5 (`/usr/local/bin/mgba -3 <rom>`), `SDL_AUDIODRIVER=dummy`, Xvfb display `:318`.
- Keymap (mGBA SDL default): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrow keys. Hold keys 150–300 ms.
- Boot path: language select (press A on *English*) → legal/credit screen → title (`PRESS START`) → Start → Main Game / Options.
  - Main Game → New Game → 3 save slots → difficulty (Normal / Hard) → world map → level 1 "Bad Pinocchio" → gameplay → Start pauses.
  - Options → Languages (6), Records (7 pages: Total Score + Levels 1–6), Format game save data (Yes/No).
- Debug breakpoints (mGBA CLI debugger via `-d`, `b/t`): set `0x08015108` and `0x08014BD0`, `c`, then walk all screens and hold any of `L+R`, `L+R+Start`, `Start+Select`, `A+B+Start+Select`, `L+R+A+B`, `Up+Down+L+R` at boot (use `reset`, breakpoints persist). Neither breakpoint ever hits. Validation: `b/t 0x080004D0` hits within one frame ("Hit breakpoint 3 at 0x080004D0").
- Screenshots of every screen are preserved in `/tmp/shrekreek/` (`screens_montage.png`, plus `fresh_menu.png`, `s3.png`, `maingame_flow.png`, `newgame1.png`, `slot1.png`, `diff_right.png`, `s_options.png`, `s_records2.png`, `pause4.png`, `level1.png`, `records_all.png`).

## 4. Address map

| Address | Meaning | Evidence |
|---|---|---|
| `0x08000000` | crt0 entry, standard ARM branch `0xEA0000C2` | Derived (disassembly) |
| `0x080003CC`–`0x080003F8` | ARM init loop: iterates the 47-entry init table | Derived |
| `0x08000468` | ARM literal → `0x0804CFC4` (init table base, count `0x2F` = 47) | Derived |
| `0x080004B8`/`0x080004BC` | literals `0x04000130` (KEYINPUT) and `0x000003FF` (all 10 keys) | Derived |
| `0x080004D0` | Thumb key-input handler; copies key state to IWRAM | Observed (breakpoint #3 hit) |
| `0x03001830`, `0x0300185C`, `0x03001860`, `0x03001864` | IWRAM per-key current/press/repeat state buffers | Observed (BP3 registers) |
| `0x0804D090` / `0x0804D097` | Build tag `OptRls` / build date string | Observed (ROM bytes) |
| `0x0804D1D4`–`0x0804D5D8` | "PRESENT FIGURE" debug-overlay text + pointer tables (`0x0804D318`, `0x0804D374`, `0x0804D410`, `0x0804D478`, `0x0804D5C0`) | Derived |
| `0x0804CFC4`–`0x0804D084` | 47-entry init function table (includes debug module init `0x08015F0D`) | Derived |
| `0x08085C78`–`0x08086xxx` | Debug-menu string bank: `Stage Select` … `SaveKill`, `Stage1..10`, `Map1..20`, `StartPos1..21`, `Normal`/`Advance`, `BGM00..18`, `SE00..90` | Observed |
| `0x08014AFC` | Debug-menu item→handler jump table dispatch (11 entries, table at `0x08014DA8`) | Derived |
| `0x08014BD0` | Debug-menu input handler (reads key state, masks `0xF0` D-pad at `0x08014BD6`) | Derived; never executed |
| `0x08015108` | Debug-menu draw/builder function (emits the strings at `0x08085D30`+) | Derived; never executed |
| `0x08015F0C` | Debug module init (registered in the 47-entry boot table — called at boot, but does not display the menu) | Derived |
| `0x0802D000`–`0x0803F000` | Generic debug-UI framework / "present figure" overlay renderer | Derived |

File offset = ROM address − `0x08000000` (flat 8 MiB image).

## 5. Algorithm

There is no password/checksum algorithm to reimplement — no code input surface and no validator exist. The only "algorithmic" content is:

- **Key-state pipeline (live):** `0x080004D0` reads `0x04000130 & 0x3FF` and maintains ten 4-byte key-state records at `0x03001830`+ (current / pressed / repeat counters). All reachable UI consumes this via the engine's standard menu helpers (`0x08046DD0`, `0x08046DD4`, `0x08046DE0`, `0x08046DD8`).
- **Debug dispatcher (dead):** `0x08014BD0` polls the same key state (`and #0xF0` at `0x08014BD6` for D-pad), advances a selected-item index (`cmp #10` → wrap at `0x08014EF4`), and `0x08015108` renders the 11 menu labels from the pointer/immediate literals in its pool (`0x0801530C`–`0x080153C0`). An 11-way jump table at `0x08014DA8` maps the selected item to handlers with return values `{1,3,7,8,11,…}`. None of this is reachable from any input path in the shipped build.

## 6. Tables

**Debug menu text bank (`0x08085C78`+), fully enumerated from the ROM:**

| Group | Entries | Count |
|---|---|---|
| Top level | `Stage Select`, `Map Select`, `Start Select`, `Player Select`, `SPR View`, `Sound Test`, `Kobako`, `FinalResult`, `Language`, `Difficulty`, `SaveKill` | 11 |
| Object Viewer | `Object No.`, `Animation No.`, `Anime Loop ON OFF`, `SHReK`, `Fiona` | 5 |
| Stage/Map/Start values | `Stage1..10`, `Map1..20`, `StartPos1..21` | 51 |
| Difficulty / language | `Normal`, `Advance`; `English`, `French`, `Germany`, `Italian`, `Spanish`, `Netherlandish` | 8 |
| Sound Test | `BGM00..18`, `SE00..90` | 110 |
| Help text | `U/D : Cursor Move`, `L/R : Value Change`, `A : Go Next`/`Restart Animation`/`Play Sound`, `B : Go Back`, `SELECT : Music Stop` | 6 |

**"PRESENT FIGURE" overlay labels (`0x0804D238`+):** `End`, `Language`, `Difficulty`, `MapNo`, `StartNo`, `MaxLife`, `MaxPower`, `NowLife`, `NowPower`, `Combo`, `Score`, `Coins`, `Remains`, `EventList`, `Continue`, `Clear`, `Suicide` (17), plus 8 field labels (`Index`, `Regist`, `Num Tp`, `Num Id`, `Type`, `SubType`, `Posi X`, `Posi Y`) and 7 control hints. All are debug leftovers; none is drawn by any reachable screen.

**Reachable difficulty values:** `Normal` / `Hard` only (debug `Advance` is never selectable). **Reachable levels:** 6 — Bad Pinocchio, Fairy Woods, Sweetsville, Beanstalk Town, Fake Peter Pan, The Ghost of Lord Farquaad — exactly matching the level names in the published CodeBreaker "Always Play Level N" codes (those codes themselves are memory patches and out of scope).

## 6b. Enumeration

**Search space checked (bounded negative):**

- Whole 8 MiB (8,388,608 bytes) scanned with `strings -t x -n 4` (72,110 strings) plus case-insensitive and case-shifted (`+0x20`) variants. Keyword hits for `password|cheat|debug|secret|unlock|code|level select|gift shop`: 2 total, both debug leftovers (`Continue` at `0x0804D350`, `(LEVELFONT)` at `0x0804DD64`). Zero password/cheat UI strings.
- Literal searches (byte, u16-LE, and simple tile-index offsets) for published button-code masks and mnemonics: **0 hits**. Specifically `UpUpDownUpRightLeft`, `LeftLeftUpRightRightUpLeft`, `RightRightDownLeftLeftUpRight` (the 2007 game's coin/costume codes) and `BAABAACA` (a *different* Shrek GBA title's code) are absent as u16 and u8 sequences and as ASCII.
- 47 init functions enumerated from the table at `0x0804CFC4`; 11 debug-menu items + 172 debug-menu value strings enumerated from `0x08085C78`+; 25 debug-overlay labels from `0x0804D238`+.
- Key-mask sequences: none found that resemble a cheat validator; the only key-mask logic is the generic 10-key state machine at `0x080004D0` and the debug menu's own D-pad `0xF0` poll (never executed).

**Every reachable screen enumerated with evidence (13):**

1. Boot legal/credit screen (`fresh_menu` sequence)
2. Language select (6 languages) — `boot2.png`
3. Title `PRESS START` — `fresh_menu.png`
4. Main Game / Options — `s3.png`
5. Main Game submenu: New Game / Continue — `maingame_flow.png`
6. Select Game (3 slots) — `newgame1.png`
7. Select game difficulty (Normal / Hard) — `slot1.png`, `diff_right.png`
8. World map — `map_start.png`
9. Level title card "Level 1 — Bad Pinocchio" — `level1.png`
10. Gameplay / HUD — `pause2.png`
11. Pause — `pause4.png`
12. Options (Languages ×6, Records, Format game save data) — `s_options.png`
13. Format confirmation (Yes / No) and Records pages (Total Score + Levels 1–6) — `s_records.png`, `records_all.png`

None of the 13 presents a password prompt, code pad, button-code display, unlock list, or hidden menu entry. The Records browser wraps after 7 pages (Total Score + 6 levels) — no hidden 7th level.

**Debug menu enumeration and reachability:**

- 11 top-level entries and all sub-value lists are present as ASCII (table above).
- Reachability tested with **two persistent breakpoints** on its draw (`0x08015108`) and input (`0x08014BD0`) routines, across (a) a complete boot→menus→cutscene→world map→level→pause walk (~1.1 billion CPU cycles) and (b) six boot-time multi-button combos with `reset` between each. **0 breakpoint hits.** A control breakpoint on the live key handler (`0x080004D0`) hit within one frame, proving the harness would have detected a hit.
- This is a gated/dead feature (guide §16.3): code and data survive, but no controller path registers a screen transition to it in this build. 3rd party cheat indexes independently describes it as non-functional.

**Novel code / bounds-by-rejection:** Not applicable — §0.2 point 5 governs: with no code system, the deliverable is the bounded negative above. There is no alphabet, checksum, field layout, or validator to mint against, and no input surface on which to submit an out-of-range value. The "bounds" proven here are: (a) all 13 reachable screens enumerated, (b) all 11 debug-menu entries shown to be unreachable by any tested input, (c) all published code literals shown absent from the 8 MiB image.

## 7. Validation evidence

- **Observed:** all 13 screens via mGBA screenshots; key-input handler breakpoint hit with registers (`r1=0x03001860`, `r4=0x0300185C`, `r5=0x03001830`, `r9=0x03001864`); 0 hits on debug-menu breakpoints across full play + 6 boot combos; `.sav` is a 512-byte EEPROM, created by the game.
- **Derived:** header/entry parse; Nintendo-logo scan (single header); init table at `0x0804CFC4` (47 entries) called from ARM `0x080003CC`; debug-menu string→function mapping at `0x0801530C`–`0x080153C0`; 11-way dispatch table at `0x08014DA8`; key-state pipeline at `0x080004D0`.
- **Inferred:** the debug module's init (`0x08015F0C`) runs at boot and likely registers the module, but no scene-select path in the retail build reaches its UI — consistent with the live breakpoint result and with 3rd party cheat indexes. The exact reason it was disabled (compile-time flag `#ifdef`-stripped caller vs. rewritten dispatcher) was not proven.

**Published-code verification (all treated as data, never instructions):**

| Source | Claim | Verdict |
|---|---|---|
| 3rd party cheat indexes | Infinite health, max coins, moon jump, "always play level 2–6", "enable level select", etc. | All are CodeBreaker/GameShark/Action Replay **memory patches** — out of scope. Level names match the ROM's Records screen (verified literal concept), but the codes write RAM directly. |
| 3rd party cheat indexes | "10,000 gold coins" `UUDURL`; "secret costumes" `LLURRUL` / `RRDLLUR` at main menu; Gift Shop unlocks | Belong to the **2007 *Shrek the Third*** (different engine/publisher) — §16.11 trap. Their button-mask sequences and mnemonics are **absent** from this ROM (0 hits). |
| 3rd party cheat indexes | Debug menu leftovers, "does not appear to be functional" | Corroborated by ROM bytes and the live breakpoint enumeration above. |

## 8. Unknowns

- The precise build-time mechanism that disabled the debug menu's caller (there is no reachable writer of a scene transition to it); only the effect (no execution) was proven.
- The 512-byte EEPROM save layout was not decoded (no cheat/unlock depends on it; the Options "Records" and 3-slot structure are the only observable save features).
- Font/tile-indexed retail UI text was enumerated by walking screens rather than by reconstructing the font mapping; byte-pattern searches under several simple index offsets found no encoded password text, and no screen shows an entry UI.

## 9. Tooling

- `strings`, `xxd`, `grep`, `file`, `md5sum`/`sha1sum`/`sha256sum` (Phase 0/1).
- Python 3 + `capstone` for Thumb literal/BL scans and mask-sequence searches (scripts in `/tmp/shrekreek/`).
- `arm-none-eabi-objdump -M force-thumb` / `-M force-arm` for all disassembly.
- mGBA 0.10.5 under Xvfb `:318` + `openbox`, `xdotool` XTEST input, `scrot` screenshots, ImageMagick `convert`/`montage`.
- mGBA **CLI debugger** (`-d`) bridged through a PTY (`pty_dbg.py`, commands via FIFO, SIGINT to break). GDB stub (`-g`) was attempted but mGBA 0.10.5's stub is incompatible with the installed `gdb-multiarch` (`vMustReplyEmpty` / `qSupported` errors); the CLI debugger was used instead (§16.2 stub-free alternative).

**Legal note:** no ROM image or copyrighted assets are redistributed here; only addresses, hashes, and original findings are published.

**Cleanup:** All emulator/display processes started for this job were terminated by their recorded PIDs; generated `.sav`/savestate artifacts in the ROM folder were removed. No `pkill` was used.
