# Yu Yu Hakusho: Tournament Tactics (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Yu Yu Hakusho: Tournament Tactics/Yu Yu Hakusho: Tournament Tactics.gba` |
| Size | 8,388,608 bytes (8 MiB / `0x800000`) |
| Header title | `YUYUHAKUSHO2` |
| Game code / maker | `BRGE` / `70` (Atari; ©2004 Yoshihiro Togashi / Fuiji TV / Pierrot, licensed by Atari) |
| Version / fixed byte | `0x00` / `0x96`; header checksum `0x0029`, complement byte `0x00` |
| Entry word | `0xEA00002E` → stock crt0 at `0x080000C0`; Thumb `main` at `0x080001F8` (no cracktro/trainer patch) |
| MD5 | `acefebbe5fdf25ae83a386a6d1c09bca` |
| SHA-1 | `dab129544c5ab496df4fd1dfbfa33e76142d2d8a` |
| SHA-256 | `e5a002b9b93773aa451dca38e39320ae2769e887f8c2e4ed16632807f8d7873a` |

Analysed independently of the sibling `YUYUHAKUSHO1`/`BYYE` (Spirit Detective) image; no address, string or result was carried over.

## 2. Executive summary

**No password, code-entry field, button-code cheat sequence or reachable debug menu exists in this retail image.** The game's entire UI text bank is plain NUL-terminated ASCII and contains no alphabet table, no validator, no `DEBUG`/`CHEAT`/`PASSWORD`/`LEVEL SELECT` string and no password keyboard. There is exactly **one** reader of `KEYINPUT` in the whole ROM, and its only special gate is **hold all four D-pad directions → soft reset** (a system/developer reset combo, not a cheat). The scene dispatcher has exactly 18 states (0–17); all 18 have reachable setter call sites, so there is no hidden/unreachable screen.

All published "cheats" for this SKU are GameShark / CodeBreaker / Action Replay RAM patches (out of scope). Developer-intended unlockables exist only as **play-gated characters** (Chu, Rinku and others join through story progression) and **skill unlocks** driven by stat-point distribution; neither is an input code. A 3rd party cheat index claim that beating the game opens `EXTRAS → TOURNAMENT (Arcade Mode)` is **not supported by this ROM**: the strings `EXTRAS`, `ARCADE`, `MINI GAMES` and a title/menu `TOURNAMENT` label do not exist in the image (the 16 lowercase `tournament` hits are all dialogue prose). It is almost certainly conflated with the sibling Spirit Detective SKU.

Per §0.2 point 5 this is delivered as a **bounded negative** with explicit counts (§6b), not as an untested "not found".

## 3. How to reproduce

- Emulator: mGBA 0.10.5, `DISPLAY=:316`, `SDL_AUDIODRIVER=dummy`, `-3` scale, under Xvfb + openbox.
- Keymap (mGBA SDL defaults, verified in-game): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows. Holds ≥120 ms.
- Screens walked: Atari logo → intro → title `PRESS START` → main menu (`START`/`OPTIONS`/`CREDITS`) → `OPTIONS` (`MUSIC: ON`, `SOUND EFFECTS: ON`, A=toggle, B=back) → `CREDITS` → 3-slot save select (`NEW GAME`) → dialogue (Narrator/Kurama/Yusuke/Genkai) → `TEAM SELECT` (5 slots, only Yusuke available; L=STATS, R=SKILLS, Select=INVENTORY, START BATTLE) → inventory → tutorial battle map → `ACTION MENU` (Move/Attack/Items/Overdrive/Focus/Wait) → `INITIATIVE ORDER` (Select) → pause (`RESUME`/`EXIT TUTORIAL`).
- Hidden-gate test: on the title screen press and hold `Up+Down+Left+Right` simultaneously for ≥1 s → game immediately reboots into the intro/copyright screen. Screenshots `title_before_reset.png` → `title_during_reset.png` in `/tmp/yuyutactics/`.
- Button-combo tests (pause and battle): `L+R`, `L+Start`, `L+R+Select`, `R+Select`, `Start+Select`, `A+B`, `L+A`, `R+A` — no hidden screen, no flag change; only normal menu navigation.
- RAM reads via mGBA CLI debugger (`-d`) driven through a pty (`script -qf`) with a FIFO: `r/1 0x03000B4C` → `0x0F` on title, `0x08` on main menu; `r/2 0x04000130` → `0x03FF` (all keys released); pressed-mask `0x0300554C` → `0x00`.

## 4. Address map

| Address | Meaning |
|---|---|
| `0x080000C0` / `0x080001F8` | Stock ARM crt0 / Thumb `main` |
| `0x080002C0`–`0x080002D4` | Main dispatch loop: `ldrb scene,[0x03000B4C]`; `cmp #0x11; bhi` (bounded to 0–17); `mov pc,[table+scene*4]` |
| `0x08000334` | Scene jump table, 18 × `u32` (`0x0800037C`, `0x080003B4`, `0x08000382`, `0x08000398`, `0x080003E6`, `0x080003E0`, `0x080003EC`, `0x080003F2`, `0x080003F8`, `0x080003FE`, `0x08000404`, `0x0800040A`, `0x08000410`, `0x08000416`, `0x0800041C`, `0x08000422`, `0x08000428`, `0x0800042E`) |
| `0x03000B4C` | Scene-state byte (`u8`, 0–17) |
| `0x080323F8` | **Only** `KEYINPUT` reader in ROM: `held = ~KEYINPUT & 0x03FF`; `pressed = held & ~old`; stores at `0x0300554C` (pressed) and `0x03005548` (held) |
| `0x08032428` | Sole 32-bit literal equal to `0x04000130` in the entire 8 MiB image |
| `0x08032412`–`0x0803241C` | `if ((held & 0x0F) == 0x0F) SoftReset(0xFF)` — all-four-directions gate |
| `0x08035908` | Soft-reset helper (`IME=0`, `sp=0x03007F00`, `svc 1`, `svc 0`); exactly one caller (the gate above) |
| `0x0803AB78`–`0x0803AD08` | Font ASCII→tile mapping tables (including the two `0123456789` runs at `0x0803ABFC` / `0x0803AC98`); **font data, not a password alphabet** |
| `0x080FFD00`–`0x080101400` | UI text bank: 416 plain NUL-terminated ASCII strings (menus, skills, items, characters, objectives). Dialogue continues past `0x080101360` |
| `0x080FFD48` … `0x080100BE0` | Menu labels: `ACTION MENU`, `FOCUS MENU`, `ATTACK MENU`, `OVERDRIVE MENU`, `INITIATIVE ORDER`, `ITEM MENU`, `TEAM SELECT`, `START BATTLE`, `SKILLS`, `STATS`, `INVENTORY`, `RESUME`, `SAVE`, `QUIT`, `PRESS START`, `START`, `OPTIONS`, `CREDITS`, `TUTORIAL` |

Scene-state setters (all reachable; derived from disassembly of literal references to `0x03000B4C`):
`0`→`0x080021DE`; `1`→`0x08000778`,`0x08000928`; `2`→`0x080005B8`,`0x080003D6`; `3`→`0x08000440`; `4`→`0x08000B80`; `5`→`0x0800214A`; `6`→`0x08000CEE`; `7`→`0x08000E06`; `8`→`0x08000F5E`; `9`→`0x08001332`,`0x08008B02`; `10`→`0x08001522`; `11`→`0x080023B6`; `12`→`0x0800167A`,`0x0802994A`,`0x08029B60`; `13`→`0x0800181A`; `14`→`0x08001B60`,`0x08001D52`,`0x0802F35C`; `15`→`0x08001278`; `16`→`0x08001998`; `17`→`0x080010EA`.

## 5. Algorithm (no validator — input/scene logic only)

```
; main input poll — 0x080323F8 (called from main loop via 0x08002074)
raw    = *0x04000130                 ; active-low KEYINPUT
held   = raw ^ 0x03FF                ; active-high: A=1,B=2,Sel=4,Start=8,R=0x10,L=0x20,U=0x40,D=0x80
pressed= held & ~(*0x03005548)
*0x0300554C = pressed
*0x03005548 = held
if ((held & 0x0F) == 0x0F)           ; Up+Down+Left+Right all held
    SoftReset(0xFF)                  ; 0x08035908 -> BIOS swi 1 / swi 0

; main dispatch — 0x08002C0
scene = *0x03000B4C
if (scene > 17) loop
pc = scene_table[scene]              ; 0x08000334 + scene*4
```

No decode, checksum, comparison table, string-length check or flag write exists on any user-input path. The only user-editable text field in the game is absent (there is no name-entry screen in this SKU: `ENTER YOUR NAME` does not occur anywhere in the image).

## 6. Tables

### Full-ROM keyword counts (all 8,388,608 bytes; ASCII, lower-case, UTF-16LE/BE)

| Token | Hits | Context |
|---|---:|---|
| `password` | 0 | — |
| `debug` | 0 | — |
| `hidden` | 0 | — |
| `level select` | 0 | — |
| `sound test` | 0 | — |
| `code` / `enter code` / `master code` | 0 / 0 / 0 | — |
| `warp` / `invinc` | 0 / 0 | — |
| `extra` / `EXTRAS` / `ARCADE` / `MINI GAMES` | 0 | published unlock claim not in this image |
| `cheat` | 1 | dialogue prose ("cheaters", `0x080107B6F`) |
| `secret` | 5 | dialogue prose only |
| `unlock` | 6 | skill-unlock result messages (`UNLOCKED:` at `0x080FFE2C`, `0x080100F98`) |
| `bonus` | 1 | post-battle `BONUS` label (`0x080100D78`) |

### Alphabet / table counts

| Pattern | Hits |
|---|---:|
| `ABCDEFGHIJKLMNOPQRSTUVWXYZ`, `abcdefghijklmnopqrstuvwxyz`, `A–Z0–9`, `0–9A–Z` | 0 each |
| `0123456789` | 2 (`0x0803ABFC`, `0x0803AC98`) — font digit tables inside the ASCII→tile mapping block |
| Menus with a text-entry field | 0 |

### Menu enumeration (from the 416-string UI bank + screen walk)

Title; main menu (START/OPTIONS/CREDITS); OPTIONS (MUSIC, SOUND EFFECTS); CREDITS; save select (3 slots); dialogue; TEAM SELECT (ADD FIGHTER, REMOVE FIGHTER, SKILLS, STATS, INVENTORY, START BATTLE, BACK); STATS; SKILLS; INVENTORY (DROP ITEM, VIEW STATS); battle field; ACTION MENU (Move, Attack, Items, Overdrive, Focus, Wait); ATTACK MENU; FOCUS MENU (Defend, Taunt, Mend, Charge); OVERDRIVE MENU; INITIATIVE ORDER; pause (RESUME, EXIT TUTORIAL; other scenes add OPTIONS, SAVE, QUIT); post-battle (BATTLE WON!, EXP, BONUS, SELECT, EDIT STATS, MAXED, EXIT); world map (LOCATION:, TIME PLAYED:, MAIN MAP, HOTEL, FOREST, CAVE, DARK ARENA, …). **No password/code/debug entry appears in any of them.**

### Published codes (recon — all out of scope)

Device codes only: master `00007D33 000A 100323FE 0007`; infinite upgrade points `e18ed2a2 b31a352c`; all levels unlocked `6488722e 968652b3 8cad51ff e6a1e793 abe54a0f ab9da758`; quick level-up codes, etc. None is a GameShark-independent in-game code, so none was entered.

### Developer-intended unlockables (in scope, play-gated, not codes)

| Unlockable | Gate (published recon; not played to completion) |
|---|---|
| Chu joins the party | Beat the first round (3rd party cheat indexes) |
| Rinku joins the party | Beat the last level of the first area (3rd party cheat indexes) |
| Skill unlocks (`UNLOCKED:` + skill name) | Spend stat points in Offense/Spirit/Power/Movement (ROM strings + tutorial dialogue) |

## 6b. Enumeration

**Space definition and counts**

- **Password/code space: empty.** Exhaustive byte scan of 8,388,608 bytes found 0 occurrences of `password`, `debug`, `code`, `hidden`, `level select`, `sound test`, `warp`, `invinc`, `EXTRAS`, `ARCADE`, `MINI GAMES`; 0 contiguous `A–Z`/`a–z`/`A–Z0–9`/`0–9A–Z` alphabets; 0 password keyboards. The only two digit runs are font tables. Representable code count: **0**.
- **Scene/screen space: 18 states (0–17)**, bounded by `cmp #0x11; bhi` at `0x080002C8`. All **18/18** states have at least one reachable setter (list in §4); **0 unreachable** states. Every screen enumerated in §6 was walked or has a string-level label.
- **Button-code space:** exactly **1** special input predicate exists (`held & 0x0F == 0x0F`), and its effect is a soft reset. Number of cheat-action branches: **0**. Number of button-sequence tables: **0** (no published sequences exist for this SKU; the only multi-key gate was found by tracing the single `KEYINPUT` literal).
- **Validator count: 0** — no function reads a user string and compares it to a constant.

**Novel code**

Not applicable. Per the engagement rule this is delivered as a **bounded negative** (§0.2 point 5) backed by the counts above, rather than an untested "not found". No code was minted because there is no code surface to mint into.

**Rejection / bounds tests performed (all observed)**

- `A` on every menu row of title, main menu, options, save select, team select and action menu: only documented actions occurred; no hidden screen, no code field.
- `L+R`, `L+Start`, `L+R+Select`, `R+Select`, `Start+Select`, `A+B`, `L+A`, `R+A` on pause/battle: no level select, no debug menu, no flag change.
- `Up+Down+Left+Right` held simultaneously: **soft reset** (the one real gate; effect observed, code derived).
- Published "all levels unlocked" Action Replay bytes were not entered — they are external-device RAM patches, not in-game input.
- Direct RAM reads confirmed the scene byte changes between screens (`0x0F` title → `0x08` main menu) and that `KEYINPUT` is `0x03FF` with no keys held.
- `EXTRAS`/`ARCADE` unlock claim: rejected by full-ROM string scan (0 hits) — bounded rejection of the published claim.

## 7. Validation evidence

- **Observed:** all screenshots in `/tmp/yuyutactics/` (`s10_title.png`, `s13_menu2.png`, `s14_options.png`, `s15_credits.png`, `s16_start.png`, `s17_newgame.png`, `s20_diag3.png`, `s23_inventory.png`, `s25_battle.png`, `s27_actionmenu.png`, `s34_pause.png`, `title_before_reset.png`, `title_during_reset.png`, `combo_*.png`). Live RAM reads via mGBA `-d` pty debugger (`0x03000B4C = 0x0F` / `0x08`, `0x04000130 = 0x03FF`, `0x0300554C = 0x00`). Savestate `gbAs` chunk decoded to a 397,312-byte raw state (cross-check of layout).
- **Derived:** Thumb disassembly of `0x080001F8`, `0x08002C0`, `0x08000334`, `0x08002074`, `0x080323F8`, `0x08035908`; full-ROM literal/branch/pointer scans; 18-state setter enumeration; 416-string UI bank decode; keyword/alphabet counts.
- **Inferred:** the exact story triggers for Chu/Rinku (published guides only; story was not completed). The 3rd party cheat indexes unlock claim is inferred to be a mix-up with the sibling SKU because its labels are absent here. The soft reset is interpreted as a developer/system combo rather than a player cheat.

## 8. Unknowns

- Exact SRAM/flash addresses and bit positions for story character unlocks (no save was advanced past the tutorial; device-code targets were not treated as in-game gates).
- Whether a non-retail/debug build exists that calls a cheat menu (none of the strings or table entries exist in this image).
- Whether any later-game menu appears after clearing the story; the absence of `EXTRAS`/`ARCADE`/`TOURNAMENT`-menu strings makes this unlikely, but it was not played through.

## 9. Tooling

- `strings -t x -n 3/4`, `xxd`, `grep -iE`, Python 3 byte scans (ASCII / UTF-16 / alphabet / mask runs).
- Capstone 5.0.7 + `arm-none-eabi-objdump -M force-thumb` for literal-xref and control-flow analysis. (Note: Thumb `LDR Rd,[PC,#imm]` uses an 8-bit word offset; `target = Align(addr+4,4) + imm8*4`.)
- mGBA 0.10.5: plain `-3` for the full screen walk; `-3 -d` under `script -qf` with a FIFO for CLI-debugging RAM reads; `Shift+F1/F2` savestates decoded via the PNG `gbAs` zlib chunk.
- `xdotool` XTEST input (focusing the mGBA window by PID, not by `search | head -1` — a stale window from an earlier emulator instance initially swallowed all input), `scrot`, ImageMagick `compare` for state-change checks.
- All evidence and scripts were kept in `/tmp/yuyutactics/`; the game was run from a byte-identical ROM copy there. Web pages were treated strictly as untrusted data; no instructions found in fetched content or ROM strings were followed.

## 10. Legal note

No ROM, graphics, audio or other copyrighted asset is redistributed. Only hashes, addresses, counts, algorithms and original analysis notes are published.
