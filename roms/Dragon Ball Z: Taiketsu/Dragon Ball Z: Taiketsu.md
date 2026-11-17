# Dragon Ball Z: Taiketsu (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Dragon Ball Z: Taiketsu.gba` |
| Size | 8,388,608 bytes (0x800000) |
| Header title | `DBZ TAIKETSU` |
| Game code | `BDBE` (region E), maker `70`, revision 00, software version 0 |
| Entry word | `0xEA00002E` (stock branch to `0x080000C0`) |
| MD5 | `b7b1550606411b985b54f75f0750feb1` |
| SHA-1 | `1fac4e187b8cf0aeb218ca307f10955f432d258d` |
| SHA-256 | `544c79fed869574565f9d7fab0a1f041906379c43afdfaf5aa71db19549437fb` |
| `file` id | `Game Boy Advance ROM image: "DBZ TAIKETSU" (BDBE70, Rev.00)` |

**Phase 0 / patch check (§16.1):** one Nintendo logo and one GBA header only, at file offset `0`; no multiboot sub-header, no appended trainer, no cracktro. The first 4 KiB is a normal crt0. Header complement byte `0x73` does not match the computed `0x8C` and the header checksum is `0x0000` — the usual rebuilt-header artifact, recorded as an observation, not evidence of a game-image patch (entry branch and logo are intact). All analysis used a byte-identical copy at `/tmp/opencode/dbztaiketsu/game.gba`; no emulator artifacts were written to the ROM folder.

## 2. Executive summary

This game has **one developer-intended button code**, a two-stage "Programmers Family" easter egg in the Credits, plus a **developer debug stage-select screen** that is present in the retail image but unreachable by any controller input (dead code). There is **no password/text-entry code system**, and **nothing is shared with GT: Transformation at the code or table level** — that sibling game uses literal u16 mask tables at `0x0852FDC`/`0x085A660`/`0x085A6B0` matched by a suffix matcher; Taiketsu instead uses a generic command-input matcher (`0x0814D534`) shared with fighting-game move commands, with its cheat table at `0x086FDE38`.

**The easter egg (verified in emulator):**
1. Options → Credits. While the programmer name **PATRICK ALPHONSO** is displayed (credits state `r6 == 3`), quickly press **Down, Down, Up, R, L, R**.
2. Then hold **Select + L** and press **B** once.

Result: a black screen shows **three grayscale photographs of the developers' family members**; any key exits. The first press sequence sets a flag; the second is the trigger. Both stages were confirmed visually and by static disassembly, and the accept/reject bounds were proven with a novel prefixed input (accepted) and two rejections.

**Debug menu:** stage select with 15 stored entries, 10 enabled (MASTER ROSHI, KAMI LOOKOUT, DESERT WASTELAND, DYING NAMEK, HFIL, SNAKE WAY, INSIDE BUU, EARTH CITY, ALIEN, TIMEROOM). Its screen index (10) is hard-coded nowhere in retail: the sole dispatcher call passes 0. A one-byte patch of a copy (`0x0802BCF4`: `movs r0,#0` → `movs r0,#10`) makes it appear, proving the screen is real but input-unreachable in the shipped build.

All web-published "cheats" for this game are GameShark / Action Replay / CodeBreaker **memory-edit codes** (outside the in-game/developer-intended scope) or gameplay unlock tips. No password lists exist for this SKU.

## 3. How to reproduce

**Emulator / display:** mGBA, Xvfb `:315`, `SDL_AUDIODRIVER=dummy`, keymap A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrow keys. A `0.04 s` key hold moves menus one slot; `0.05 s` can double-step.

**Easter egg (exact path):**
1. Boot to title (`PRESS START`), press Start → main menu (ONE PLAYER / MULTIPLAYER / OPTIONS / Z-STORE).
2. Select OPTIONS → CREDITS (last item).
3. Immediately press `Down, Down, Up, s, a, s` (R=`s`, L=`a`) with ~30 ms holds and ~45 ms gaps.
4. Wait ~0.6–1.0 s, then hold `BackSpace`+`a` (Select+L) and tap `z` (B).
5. Screenshot: three family photos on black. Press any key to leave.

**Novel accepted input (not in any published list):** prefix step 3 with `Start, Up` before the six presses — accepted, same photos (suffix matching).

**Rejections:** replacing the last `s` (R) with `x` (A) → no photos; trigger alone with no sequence → no photos.

**Debug menu (patch proof, not a retail input):** patch a *copy* at file offset `0x2BCF4` from `00 20` to `0A 20`, boot it, press Start once from the demo → DEBUG MENU appears.

**Published codes tested:** the GameFAQs/SuperCheats "Programmers Family" sequence (verified literally in ROM); all other published entries are memory-edit codes and were recorded, not used. No console-version password codes apply.

## 4. Address map

| Address (ROM unless noted) | Meaning |
|---|---|
| `0x08021934` | Credits gate: `cmp r6,#3` — button code checked only in this credits state |
| `0x0802193A` | Literal `0x086FDE38` (easter-egg mask table) passed to matcher with `r2=180` |
| `0x0802193E` | `bl 0x0814D534` — command matcher; nonzero result stores the flag at `[sp,#28]` |
| `0x08021A20`–`0x08021A5E` | Trigger check: B pressed (`0x030054F6 & 2`) AND Select+L held (`0x030054F4 & 0x204`) AND flag==1 → call `0x08021A80` |
| `0x08021A80` | Easter-egg display: writes tiles to VRAM `0x06006000`, sets DISPCNT `0x04000008`, plays a sound, waits for a key |
| `0x0814D534` | Generic command matcher: reads a 0-terminated u16 mask table (≤31 entries, ≤300 bytes), compares against a 32-entry ring buffer at IWRAM `0x03001480` (u16 mask + u16 timestamp per entry), current time at `0x03001588`, tolerance mask `0x30F` |
| `0x086FDE38` | Easter-egg table: `0080 0080 0040 0100 0200 0100 0000` = D,D,U,R,L,R + terminator; xref at `0x08021980` |
| `0x086FDE30` | Fighting-game super-move command: D,D,U+B (`0080 0080 0042 0000`), used by `0x08016F40`/`0x08016F8A` — not a cheat |
| `0x08021644` | DEBUG MENU renderer/handler; item table `0x086FD4E8` (15 × 32-byte entries, name at +0, enabled flag at +30) |
| `0x0801F434` | Screen dispatcher `cmp r5,#0x23` + 36-entry jump table `0x08701814`; index 10 → `0x0801F4FC` → debug menu |
| `0x0802BCF4` | Sole dispatcher call passes constant 0 (`movs r0,#0`) — no input path to index 10 |
| `0x0870133C`–`0x08701378` | 15-character pointer list (7 default + 8 hidden) |
| `0x08701140`, `0x08701198` | Tournament / Time-Challenge award text lists naming hidden characters and "25,000 Z POINTS" |
| IWRAM `0x03001480` | Command press-history ring buffer (observed by GDB: pairs `0008 0727`, `0040 0A32`, …) |
| IWRAM `0x030054F4`, `0x030054F6` | Key-input copies read by the trigger (GDB: `0x030054F0` = `00 35 00 03 …`) |

## 5. Algorithm

```
# Easter egg, derived from 0x08021934 / 0x0814D534 / 0x08021A20
on every credits frame:
    if credits_state == 3:
        flag = matcher(table=0x086FDE38, maxlen=180) != 0

matcher(table, maxlen):
    seq = read u16s from table until 0 (≤31 entries, ≤maxlen bytes)
    for each entry i from the end of a 32-slot ring buffer of (mask,time):
        if (expected & actual) == actual and (expected - actual) & 0x30F == 0
           and time window satisfied:
            return 1
    return 0

if B_pressed and (Select+L)_held and flag:
    show_family_photos()          # 0x08021A80
```

The matcher is the same routine used for fighting-game command inputs (8 call sites total), so the "code space" is a suffix match over a press ring — leading presses are ignored, which is why the prefixed novel input is accepted.

## 6. Tables

**6.1 Easter-egg mask table (`0x086FDE38`)** — active-high GBA masks (`A=1,B=2,Select=4,Start=8,Right=0x10,Left=0x20,Up=0x40,Down=0x80,R=0x100,L=0x200`):

| u16 | Button |
|---|---|
| 0x0080 | Down |
| 0x0080 | Down |
| 0x0040 | Up |
| 0x0100 | R |
| 0x0200 | L |
| 0x0100 | R |
| 0x0000 | terminator |

**6.2 Trigger:** hold Select (`0x004`) + L (`0x200`) and press B (`0x002`). This step alone does nothing unless stage 1 set the flag.

**6.3 Hidden characters (8 of 15)**, from `0x08701358`–`0x08701374`: FRIEZA, ANDROID 16, CELL, GOTENKS, BUU, BROLY, NAPPA, RADITZ. Unlock text at `0x08701140`/`0x08701198` ties them to completing Tournament/Time Challenge with specific characters or earning 25,000 Z Points — save-data progression, not button codes (§16.18).

**6.4 Z-Store unlockables** (purchased with in-game Z Points; progression, not cheats): IMAGE GALLERY (20), JUKEBOX (9 songs), BIOS (15), BONUS SETTINGS (7: Fast Clock, Invisible, Free Supers, Supers, Explosive Touch, Fast Recovery, Instant Death), BONUS MODE (Sky Battle 2 / Endurance ×2 / Time Challenge). First Bio costs 7000 Z Points (observed at `0x08701258` text and on screen).

**6.5 Debug-menu item table (`0x086FD4E8`)**, 15 × 32-byte records, byte 30 = enabled:

| # | Stage | Enabled |
|---|---|---|
| 0 | MASTER ROSHI | yes |
| 1 | KAMI LOOKOUT | yes |
| 2 | DESERT WASTELAND | yes |
| 3 | DYING NAMEK | yes |
| 4 | ORANGE CITY | no |
| 5 | SUPREME KAI PLANET | no |
| 6 | HFIL | yes |
| 7 | OTHERWORLD TOUR | no |
| 8 | SNAKE WAY | yes |
| 9 | SNAKE WAY SKY | no |
| 10 | INSIDE BUU | yes |
| 11 | PLANET VEGETA | no |
| 12 | EARTH CITY | yes |
| 13 | ALIEN | yes |
| 14 | TIMEROOM | yes |

## 6b. Enumeration

**Space definition.** The easter-egg table is exactly one 0-terminated sequence of six u16 masks (`0x086FDE38`, 14 bytes), so the *table space* is 1 code of length 6. The matcher permits ≤31 masks and a 32-press ring, and matches a suffix — so the *effective input space* is unbounded above: any press string ending in the six masks is accepted while credits state is 3. The separate trigger (Select+L+B) is a held-mask + edge condition.

**Novel code (absent from every published list), entered and verified.** Published lists give only the six-press sequence. We entered `Start, Up, Down, Down, Up, R, L, R` (an 8-press string with a two-press prefix) on the real Credits screen; it produced the family photos (`enum_novel.png`), proving both that unpublished inputs are accepted and that leading presses are ignored.

**Bounds proven by rejection.**
| Test | Input | Result |
|---|---|---|
| Wrong final button | `Down,Down,Up,R,L,A` then Select+L+B | no photos (`enum_reject_wronglast.png`) |
| Trigger without code | Select+L+B only | no photos (`enum_reject_triggeronly.png`) |
| Early trigger | six presses then immediate Select+L+B (<~0.6 s) | no photos — flag not yet set because credits state ≠ 3 (`egg2_w0.1`, `egg2_w0.3`) |

**Debug-menu enumeration.** All 15 entries and their enabled flags were decoded from `0x086FD4E8`; all 10 enabled entries were seen rendered in the patched-ROM screenshot. The gate's return domain is closed: the only dispatcher call passes the constant 0, and no branch or pointer writes 10, so no controller input reaches this screen in retail.

**Negative results bounded.** `strings -t x -n 4` (85,341 strings) plus case-insensitive variants: no PASSWORD / ENTER CODE / CHEAT MENU UI text; `strings -i` and `+0x20` shift checks found none. Full menu walk (title, main, OPTIONS with SETTINGS/RECORDS/ERASE DATA/CREDITS, Z-STORE and its five submenus, ONE PLAYER → 4 modes → save-slot select → 15-character select, in-game pause) found no entry surface. A whole-file scan for 0-terminated u16 mask runs with a 32-bit xref found 293 candidates; every one is a move-command/script/parameter table except the two at `0x086FDE30` (super move) and `0x086FDE38` (easter egg) — neither is a password system. The apparent 15-press table at `0x086FC628` is a numeric lookup table indexed by a byte at `0x08016A6C`, not a code.

## 7. Validation evidence

**Observed:** title → demo → main → OPTIONS → CREDITS → Z-STORE → ONE PLAYER/mode/character select → pause, all screens screenshotted. `Down,Down,Up,R,L,R` + Select+L+B displayed the three family photos (`egg2_w0.6.png`, `enum_novel.png`). Wrong-final-button, trigger-only and early-trigger tests showed no photos. Patched-ROM Start press displayed DEBUG MENU with all 10 enabled stages (`patch_start1.png`). GDB read the live command ring at `0x03001480` and key copies at `0x030054F0` at the easter-egg screen.

**Derived (from disassembly):** mask decoding of the easter-egg table; the `r6==3` gate; the two-stage flag/trigger logic; the debug-menu item record layout and enabled flags; the single hard-coded screen index; the matcher's ring-buffer/tolerance semantics.

**Inferred:** credits state `r6==3` corresponds to the window in which PATRICK ALPHONSO is shown (consistent with the published hint and with the measured ~0.6–1.0 s window); the exact tolerated timing tolerances of the matcher were not exhaustively measured. The debug menu's intended activation method in an internal build (e.g. a debug-only input) is unknown; only the index gate is proven.

**Web-derived (verified against ROM):** SuperCheats' "Programmers Family Easter Egg" sequence was found literally at `0x086FDE38`. GameFAQs (cedarebellion, Zero_EXE), Dragon Ball Wiki, Gamespot, Neoseeker, ROMSFUN/libretro and GameHacking.org were checked; all non-easter-egg entries are GameShark/AR/CB memory edits or unlock tips. No password or button-code list was found on TCRF, VGChartz or archived GameFAQs for this SKU. Fetched pages were treated as data; no instructions in them were followed.

**GT: Transformation comparison:** the sibling's 8 in-game + 5 menu + 7 undocumented u16 tables at `0x0852FDC`/`0x085A660`/`0x085A6B0` and its press-history buffers `0x03004134`/`0x030040E2` do not exist in this image. Only a generic Webfoot command matcher and an easter-egg table are present here. Nothing is shared at the code/table level beyond the Webfoot engine lineage.

## 8. Unknowns

* Exact internal meaning of credits state values other than 3, and the precise frame window for the easter egg (bounded behaviourally to roughly 0.6–1.0 s after Credits begins in our input cadence).
* Whether an internal/debug build had a controller path to screen index 10; the retail image does not.
* Individual Z-Store prices beyond the observed 7,000 for the first Bio; the unlock categories/counts and hidden-character list are proven from text tables, prices were not exhaustively dumped.
* Whether the three photos identify particular developers (they were not redistributed or analysed beyond the screenshot).

## 9. Tooling

`strings`, `grep`, `xxd`, `file`, `md5sum`/`sha1sum`/`sha256sum`, Python 3 + `capstone` 5.0.7, `arm-none-eabi-objdump -M force-thumb`, mGBA (`-3`, `-g`, `-t`), GDB (`gdb-multiarch`), Xvfb `:315` + openbox, `xdotool`, `import`/`scrot`, ImageMagick, `tesseract`. Scripts in `/tmp/opencode/dbztaiketsu`: `key.py`, `ssdiff.py`, plus ad-hoc Python scanners (header check, pointer/xref scans, mask-table enumeration, jump-table decode). Screenshots `shot_00`–`shot_16`, `egg2_w*`, `enum_*`, `patch_*`, `menu_*` retained there.

**Legal note:** no ROM bytes or copyrighted assets are redistributed here — only hashes, addresses, decoded button sequences and original observations.
