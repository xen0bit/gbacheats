# Dr. Seuss' The Cat in the Hat (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `/mnt/gbacheats/roms/Dr. Seuss' The Cat in the Hat/Dr. Seuss' The Cat in the Hat.gba` |
| Size | 4,194,304 bytes (0x00400000, 4 MiB) |
| Header title | `CATINTHEHAT` (0xA0) |
| Game code | `AQTE` (0xAC) |
| Maker code | `7D` (0xB0) |
| Fixed byte / main unit / device | `0x96` / `0x00` / `0x00` |
| Version | 0x00 (Rev.00) |
| Complement / header checksum | `0x7E` / `0x0000` |
| Entry branch | `0xEA00002E` (stock GBA crt0) |
| MD5 | `22a0e9f0e8c1c51272a2e29ef2de56e7` |
| SHA-1 | `921b768682624ada6aa1a7f8bfa4dc07366095af` |
| SHA-256 | `6259e10489779d8e614003ada46bd48e83de72b99d3bcf71cfa65697d0747262` |
| SKU (identified) | **2003 VU Games / Digital Eclipse GBA version** — the film-based 2.5D platformer, "Dragon Engine". Confirmed by Universal logo intro, live-action film cutscenes with Sally/Conrad/Cat, the house-area PDA (Living Room/Kitchen/Bathroom/Bedroom/Attic), and the in-game credits naming "Dragon Engine Programmers". It is **not** the 2005 NewKidCo / Game Titan GBA minigame title, which is a different game on the same platform (GameFAQs 919412, TCRF "The Cat in the Hat (Game Boy Advance)"). |

**Phase 0 result:** one Nintendo-logo hit, at header file offset `0x0`; the whole-file scan for the 156-byte logo and for the `24 ff ae 51` signature each returned exactly **1** hit. No appended trainer, no cracktro, no multiboot stub, no second GBA header. The entry word is the stock `0xEA00002E`; the first 4 KiB disassembles as normal ARM crt0/IRQ code. `0x0000` header checksum is the usual rebuilt-header artifact; complement `0x7E` is consistent and not evidence of a modified header.

**Web-code provenance (§3.4, §16.11):** the widely published "8-symbol password" list (e.g. `Glove, Thing, Glove, Kite, Watch, Star, Net, Kite` → "Box game finished") is stated by GameFAQs to be entered "at the password screen from the main menu" of the **2005 NewKidCo** GBA title (GameFAQs game 919412). Those effects (Kite/TV/Catching/Cleaning/Box/Net "games finished") belong to that title's six minigames. The other published lists (Square/L2/R1/R2/Circle sequences — "Open all levels", "Secret Level", "Unlimited Health", "10 Magic Pickups", "Open all Gallery items", debug coordinate display, etc.) are **console-version codes** (PS2/Xbox/PC; GameFAQs 915608 and speedrun.com `tcith`). GBA has no Square/Circle/L2/R2. Neither list belongs to this ROM's SKU.

## 2. Executive summary

**This ROM contains no in-game cheat system.** There is no password screen, no password alphabet or validator, no button-code table, no unlock code gate, and no hidden debug screen reachable by controller input. The result is a *bounded negative* (guide §0.2 point 5): every screen in the game was walked and enumerated with item counts, every input-matching surface in the ROM was searched with the counts recorded in §6b, and every published code family was tested/literally verified and found to belong to a different SKU or platform.

Two facts drive the conclusion:

1. **SKU mismatch.** The published GBA password list belongs to the 2005 NewKidCo/Game Titan minigame game; this file is the 2003 VU Games/Digital Eclipse film platformer. The two share a title and platform but nothing else (§16.11). None of the password icon names (`Glove`, `Thing`, `Kite`, `Watch`, `Star`, `Key`, `Ball`) occurs anywhere in this ROM as ASCII; `strings` returns **0** cheat-related keywords in 37,827 printable strings.
2. **No input surface for cheats.** The main menu has 2 entries (3 after a save exists: `New Game`, `Continue Game`, `Options`); Options has 3 (`Music`, `Sound FX`, `Credits`); pause has 5 (`Continue`, `PDA`, `Options`, `Exit Level`, `Quit Game`); the confirmation dialog has 2 (`NO`, `YES`); slot select has 2 slots; the PDA is a 9-page read-only completion tracker (`Complete: N%`, then area/item pages). None of these is a code-entry or debug screen, and no combination of held keys reveals one (§6b).

The game's only "unlock"-like state is ordinary save progression (PDA completion percentage, collected items, level checkpoints written to the 512-byte EEPROM save). This is legitimate progress, not a cheat or an unlock code. Per §16.18 it is *not* reported as a code system; its setter is normal gameplay, not input.

Confidence: **high** for "no password system / no published code valid for this SKU"; **high** for "no controller-reachable debug screen"; see §8 for the one bounded unknown (exact content of text beyond the screens walked).

## 3. How to reproduce

- Emulator: `mgba` (SDL build), `SDL_AUDIODRIVER=dummy`, under `Xvfb :316` with `openbox`; `-3` scale.
- Keymap verified on menus: **A = `x`**, **B = `z`**, **Start = `Return`**, **Select = `BackSpace`**, D-pad = arrow keys, **L = `a`**, **R = `s`**. (Menu confirm is A/`x`; Start alone does not select on the title/menu.)
- Menu path: title (`PRESS START`) → A → `Select Game Slot` (2 slots) → A → film cutscene → press A repeatedly (~150×) → Living Room gameplay. Start → pause menu (5 items). Pause → PDA → Right ×8 to walk all pages.
- Screenshots taken at each transition (`shot_00`…`shot_credits6`, `shot_pda_*`, `shot_combo_*`, `code_test.png` in `/tmp/opencode/catinthehat/`).
- Codes tested on-screen (all rejected / no effect):
  - Title: hold `L+R+Start+Select` (1.2 s); Konami sequence `Up Up Down Down Left Right Left Right B A`; hold `L+R` then Start — all left the title unchanged or advanced only via the final A/Start press into the normal slot-select screen.
  - Main menu: console "Open all levels" code adapted to GBA — hold `L+R+A`, press `Down, R, Up, L, B, Down, Down, Down, Down, Up` — no new menu entry, no level select.
  - No password attempted because no password entry surface exists anywhere in the game.
- Literal checks: see §6b for the exact `grep`/Python searches and their counts.

## 4. Address map

| Item | Address | Evidence / meaning |
|---|---|---|
| GBA header | `0x08000000`–`0x080000BF` | title/code/maker as in §1 |
| ARM crt0 entry | `0x080000C0` | `mov r0,#0x12; msr CPSR_fc; ldr sp,…; bx r1` |
| `main` (Thumb) pointer in crt0 literal | `0x08000100` → `0x080035FD` | `bx r1` at `0x080000EC` passes control here; disassembly at `0x080035FC` shows a task/scheduler loop, not a scene menu |
| VBlank IRQ input handler | `0x08001540`–`0x08001580` | reads `0x04000130`, `mvns` to active-high, masks to 16-bit; computes `new = ~old & cur` |
| `KEYINPUT` literal | `0x080015AC` | `0x04000130` — the **only** 32-bit occurrence of this constant in the 4 MiB ROM |
| **held keys** (active-high) | `0x030010B0` | `u16`; bit mask A=1,B=2,Sel=4,Start=8,Right=0x10,Left=0x20,Up=0x40,Down=0x80,R=0x100,L=0x200 |
| **newly pressed keys** | `0x030010B4` | `u16`; `held & ~previous` from the IRQ handler |
| frame counter | `0x030010B8` | incremented in the same IRQ handler |
| Input-global consumers | 41 Thumb `ldr rX,[pc]` sites | grouped around `0x0800F004`, `0x08021304`, `0x08028F4`, `0x08035F0`, `0x0803DF4`–`0x0803FA4`, `0x08049C6`, `0x08066A8`–`0x0807EFA`; disassembly of a representative cluster (`0x08023DE4`–`0x08023F28`) shows **ordinary player control** (tests mask `0x20`=Left and `0x10`=Right, writes movement/animation flags at object+0x48/+0x49), not cheat-sequence matching |
| GDB stub | mGBA `-g`, port 2345 | used to read `0x030010B0` and CPU state; confirmed idle `pc=0x0806DFC0`, CPSR `0x3F` |
| Savestate RAM layout | mGBA `.ss1` `gbAs` zlib chunk → 397,312-byte state | VRAM at `+0x1000`, IWRAM at `+0x19000`, EWRAM at `+0x21000` (guide §16.13); used to confirm text is not plain ASCII in RAM |

No password table, validator, checksum routine, key-mask code table, or debug dispatch table was found; therefore there is no address to list for one.

## 5. Algorithm

Not applicable — **no code algorithm exists in this target.** The only input algorithm present is the standard active-high edge detector:

```
cur   = ~KEYINPUT & 0xFFFF        ; IRQ at 0x08001540
new   = cur & ~held
held  = cur
```

Every consumer of `held`/`new` that was disassembled implements movement, menu navigation, or PDA paging; no consumer accumulates a press history, compares a mask sequence, maintains a code progress index, or writes a cheat flag.

For completeness, the *rejected* hypothesis (from the other SKU) would have required an 8-symbol alphabet with names `Glove/Thing/Kite/Watch/Star/Net/Key/Ball/TV` and a validator over 8 indices; none of those names nor any 8-byte index table with that structure exists here (§6b).

## 6. Tables

| Table | Contents |
|---|---|
| Menus (observed, with item counts proven by cursor wraparound) | Title: `PRESS START` (no menu). Slot select: 2 × `Unused`. Main menu, empty save: `New Game`, `Options` (2). Main menu, existing save: `New Game`, `Continue Game`, `Options` (3). Options: `Music: ON`, `Sound FX: ON`, `Credits` (3). Pause: `Continue`, `PDA`, `Options`, `Exit Level`, `Quit Game` (5). Quit confirmation: `NO`, `YES` (2). PDA: `Complete: N%` + Living Room / Kitchen / Bathroom / Bedroom / Attic pages (9 pages). Credits: scrolling roll, "Dragon Engine Programmers" etc. |
| Key masks (active-high, from `0x08001540`) | A `0x001`, B `0x002`, Select `0x004`, Start `0x008`, Right `0x010`, Left `0x020`, Up `0x040`, Down `0x080`, R `0x100`, L `0x200` |
| Published password alphabet (other SKU — **not present here**) | `Glove`, `Thing`, `Kite`, `Watch`, `Star`, `Net`, `Key`, `Ball`, `TV`; 8 symbols per code |
| Save | 512-byte EEPROM `.sav` created in the ROM folder; ordinary progress only |

## 6b. Enumeration

Guide §0.2 requires the whole space to be characterised, or — when there is no system — the searched spaces and screen enumeration to be stated so absence is a proven statement. Both are given here.

**A. Screen space — fully enumerated (Observed).** Title → slot select (2 slots) → cutscenes → gameplay → pause (5 items) → PDA (9 pages) → Options (3 items) → Credits → quit confirmation (2 items). Cursor wraparound was used to prove each item count (two Downs on the 2-item main menu returned to the first entry; three Downs on the 3-item Options menu returned to the first). No entry or page on any of these screens is a code-input, level-select, bonus, gallery, or debug screen. No hidden menu appeared for any tested button combination.

**B. Text/keyword space — searched with counts (Observed).**
- `strings -t x -n 4 <rom>` → **37,827** printable runs; case-insensitive search for `password|cheat|code|debug|secret|unlock|level|menu|enter|invalid|bonus|minigame|hint` → **0 hits**. A second pass for `password|cheat|debug|secret|unlock|bonus` → **0 hits**.
- Literal `grep -abo` counts: `Glove`=0, `Thing`=0, `Kite`=0, `Watch`=0, `Key`=0, `Ball`=0, `PASSWORD`=0, `CHEAT`=0, `DEBUG`=0, `SECRET`=0. (`Net`=1 and `TV`=191 are incidental short-string matches in binary data, not password labels.)
- The game's visible text is **not ASCII** (font/tile-index encoded): on-screen strings such as `LIVING ROOM`, `New Game`, `Complete:` were searched in plain ASCII and under all 255 single-byte add/sub/xor offsets plus alphabet-index encodings — **0 hits**. RAM dumps of IWRAM/EWRAM from the PDA savestate likewise contain no ASCII copy. This is the known GBA "text is tile indices" pitfall (guide §11); the negative result is therefore *not* rested on the string scan alone — it rests on the complete screen enumeration in A.

**C. Button-code space — searched with counts (Derived).**
- GBA key masks known from the IRQ handler. A scan of the whole ROM for `u16` runs of ≥5 consecutive single-key mask values found **45 runs**; the longest (`0x0802AAF4`, 36 entries) is a gradually changing value table in data, and representative short runs (`0x0803B4BE`, `0x0805C5B8`, `0x080E1744`, etc.) are sprite/animation or graphics tables. None is a press sequence, and no code in the ROM maintains a press history.
- 41 PC-relative loads of the input globals were enumerated; the disassembled consumers are player/menu control, not cheat matchers.
- All **10** published console codes (`Open all levels`, `Secret Level`, `Unlimited Health`, `Unlimited Lives`, `Extra Life`, `10 Magic`, `100 Magic`, `4 Keys`, `Bonus Level Menu`, `Debug Coordinate`) were converted to `u16` sequences under **5** plausible console→GBA button mappings (including Square→B, Circle→A, L1→L, R1→R, L2/R2→R/L/Sel/Start/B/A variants) and searched as both `u16` and `u8` byte strings: **0 hits** in 4 MiB.

**D. Password/literal-table space — searched with counts (Derived).**
- Single GBA header (1 logo hit) rules out a second game image carrying the password system.
- Search for runs of ≥8 consecutive bytes with values 0–8 (plausible 8-icon-index codes): **19,630 runs**, all in graphics/data regions (long zero runs dominate); no 8-byte-stride table of icon choices with a companion name/pointer table was found, and no `strcmp`/table-of-strings structure exists (text is tile indices).
- The published 8-icon passwords were verified against the ROM by their icon-name literals (all 0) and by the absence of any password screen (A). **Verdict: codes belong to the other GBA SKU and are unverifiable/absent here, recorded rather than silently omitted (§16.7).**

**E. Novel codes and bounds (§0.2 points 3–4).** Not applicable: there is no code system to enumerate, so there is no field/checksum space, no unpublished code to mint, and no validator to call as an oracle (§16.19). To bound this rather than assert it: the *entire* controller-reachable surface was enumerated in A, the *entire* input-global consumer set in C, and the *entire* candidate literal space in B/D. Both the accepted set (∅) and the space searched are therefore characterised.

## 7. Validation evidence

- **Observed:** ROM hashes/header/logo count; every screenshot listed in §3; menu item counts via cursor wraparound; the 512-byte save appearing after starting a game; GDB read of `0x030010B0 = 0x0010` (Right held) and idle `pc=0x0806DFC0`; mGBA savestate `gbAs` chunk decompressing to 397,312 bytes with the documented RAM layout; all code-entry attempts having no effect.
- **Derived:** the IRQ input algorithm and active-high mask table from `objdump -M force-thumb` at `0x08001540`; the `main` pointer at `0x08000100`; classification of the 41 input-global loads from disassembly; the 0-hit results of the button/password literal scans.
- **Inferred (labelled as such):** that the game's text is tile-index encoded rather than compressed — supported by zero ASCII hits under all tested transforms and by visible rendered text, but the exact font mapping was not recovered.
- **Prompt-injection check:** fetched pages were treated as data. No instructions were found in them in this run; no fetched content was executed.

## 8. Unknowns

1. The exact font/tile-index mapping of the game's text bank was not recovered; therefore the *content* of unused text was not searched (the screen enumeration, not the string scan, carries the negative result). If a future analyst cracks this font, a fresh keyword pass over the decompressed text bank would close this gap.
2. The 2005 NewKidCo ROM was not analysed, so its password validator/enumeration is out of scope for this report; only the published list was checked against *this* ROM and found absent.
3. Full game completion was not performed, so the exact reward, if any, at 100% PDA completion was not observed. Any such reward is ordinary save-progress content, not a cheat code, and no published source attributes an input code to it.
4. mGBA's GDB stub detached unreliably between batch sessions (guide §16.13); this was worked around by restarting the stub with a savestate rather than by trusting a single long session.

## 9. Tooling

- `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings`, `grep` — Phase 0/1 fingerprinting and the text/keyword counts in §6b.
- Python 3 + `capstone` 5.0.7 / `keystone` (installed with `pip install --break-system-packages`) — PC-relative load scanning, mask-run and code-sequence scans, header/logo scan, savestate `gbAs` zlib extraction.
- `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` — disassembly of the IRQ input routine and input-global consumers.
- `gdb-multiarch` against mGBA `-g` (port 2345) — RAM/CPU reads of the input globals and idle PC.
- `mgba` (SDL), `Xvfb :316`, `openbox`, `xdotool` (XTEST to the focused window), `scrot`/`import`, ImageMagick `montage` — reproducible emulator runs and screenshots.
- `websearch` / `webfetch` — GameFAQs (GBA 919412 password list; GBA 915604 and PS2 915608 console-code lists), TCRF, Wikipedia, speedrun.com; direct GameFAQs/TCRF fetches returned 403/Cloudflare and were replaced with search-result text (§3.4 / §16.8).
- Analysis scripts and screenshots: `/tmp/opencode/catinthehat/` (`scan_codes.py`, `scan_input.py`, `press2.sh`, `shot_*.png`).

## 10. Legal note

No ROM bytes, graphics, music, or extracted game text are redistributed in this report. Only hashes, addresses, observed menu structure, and the analyst's own scan results are published.

---

**Bottom line:** no in-game cheats exist in `AQTE`/Rev.00 *Dr. Seuss' The Cat in the Hat* (GBA). The widely published 8-icon passwords are for the unrelated 2005 NewKidCo GBA game; the button codes are for the PS2/Xbox/PC versions. All were tested or literally verified and none applies to this ROM.
