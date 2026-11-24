# NASCAR Heat 2002 (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/NASCAR Heat 2002/NASCAR Heat 2002.gba` |
| Size | 4,194,304 bytes (0x400000) |
| Header title | `NASCAR HEAT` |
| Game code | `ANHE` (AGB-ANHE-USA) |
| Maker | `70` (Infogrames) |
| Version | 0 (Rev.00) |
| Entry word | `0xEA00002E` → `0x080000C0` (stock crt0, no cracktro/trainer) |
| Fixed byte 0x96 | present; complement `0xD4`; header checksum `0x0000` |
| MD5 | `2fb73b874bbf4119e5cbf17b8ceae9c1` |
| SHA-1 | `0eb1fa43d8b0f8a6fb1e3ac04f7bba92c7cbac96` |
| SHA-256 | `814356b2bc6b542d9134c01291739a584ea11f92948bc62469611856375ed628` |

**Embedded-header scan (Phase 0).** The 156-byte Nintendo logo occurs twice: at file `0x0` (the game) and at `0x363EE8`. The second is a **multiboot/link stub**, not a playable game: empty title, game code `0000`, maker `01`, entry `0xEA00002E` but the code at `+0xC0` (`0x363FA8`) is `11 00 00 EA` (`b .`, self-loop). It is the single-pak link transfer payload (the GBA manual's "Multi-Boot" mode). No patch or trainer bytes were found.

A matching community decompilation exists (`github.com/shohamc1/heat2002`) whose target SHA-1 is exactly this ROM's; it was used only as a cross-check — every claim below was re-verified against the raw ROM bytes and the emulator.

## 2. Executive summary

**There is no reachable in-game cheat on this GBA SKU.** The ROM contains a complete, fully implemented 5-digit password screen (`PASSWORD ENTRY` / `PASSWORD ACCEPTED` / `PASSWORD REJECTED`, plus `TOP SECRET CARS`, `RADIO CONTROL CAR/MENU`, `GHOST CAR` strings), a validator, and a 5-entry code table. **All of it is unreachable dead code**: there is no `BL`, tail-call `b`, function pointer (byte-aligned scan over the whole 4 MiB), or data reference to the password screen at `0x080132F8`; the matching decomp places it in `src/dead/` and classifies it a cut feature. The on-screen alphabet, menu dispatch, and RAM walk confirm that no menu path leads to it.

The game's cheat flags (`gCheatFlags`, 8 bytes at `0x0202EEC0`) have no live writer: the only writer is the dead password routine; live code only loads/saves them. Consequently no controller input can set a cheat flag — this is the **dead-code** case of the "no" taxonomy (guide §16.3), not a gated or cut-string-only feature.

Published PS2 button codes (e.g. `Up,Up,Up,Left,Right,Circle,Triangle`) are for the PS2 game by Monster Games; their key-mask sequences do **not** occur in this GBA image under any encoding checked, and the mapped sequences had no effect in-game. The widely circulated 5-digit codes `29801 / 07913 / 62972` are labelled as "Driven" codes on cheat sites but happen to match three of this ROM's five dead-table entries exactly; two further table entries (`16200`, `81395`) are absent from every published list found.

Bottom line: the code *system* is fully characterised (§6b), but **no code can be entered on any reachable screen**, so no in-game effect can be produced by developer-intended input.

## 3. How to reproduce

- Emulator: mGBA 0.10.5 SDL, `DISPLAY=:316`, `SDL_AUDIODRIVER=dummy`, `Xvfb :316 -screen 0 1024x768x24`, `openbox`, `mgba -3 <rom>`.
- Keymap (mGBA SDL default): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrow keys. Holds of 70–150 ms.
- Boot → title (`PRESS START`) → Start → **Main Menu** (rows: Arcade Mode, Single Race, Beat The Heat, Multiplayer, Time Trial, Career Mode, Options). No "Top Secret Cars" row exists in the GBA build.
- Walked with savestate+RAM evidence: main menu cursors 0–6 (`gMainMenuCursor` `0x0202EDD4` read 0..6 from `gbAs` states), Options (6 rows), Multiplayer (Multi-Pak/Single-Pak), Beat The Heat (4 categories, 4 challenges in Easy), driver select (8 selectable of 12 roster slots), track select (12 slots; cursor sequence 1→11 with slot 7 as the Michigan/Intl-Speedway dual entry), Career team select, in-race HUD, pause menu (PAUSED/CONTINUE/EXIT).
- Savestates: Shift+F1 writes `<rom>.ss1`; the `gbAs` PNG chunk zlib-decompresses to a 397,312-byte state. For this 4 MiB ROM, EWRAM begins at state offset `0x21000`; read `state[0x21000 + (addr-0x02000000)]`.
- Codes/combos tested in-game: PS2 master/credits sequences mapped to GBA buttons, `L+R+Start`, `L+R+A+B+Select`, all four directions, `A+B+Select+Start`. All left `gCheatFlags` at `00 00 00 00 00 00 00 00` and `gCheatCodeDials` at `00 00 00 00 00`.

## 4. Address map

File offset = ROM address − `0x08000000`.

| Item | File offset | ROM address | Notes |
|---|---:|---:|---|
| Game header | `0x0` | `0x08000000` | `ANHE`, Rev 00 |
| Multiboot stub header | `0x363EE8` | `0x08363EE8` | link payload, `b .` at +0xC0 |
| Cheat digit sequences | `0x3FE064` | `0x083FE064` | 4×5 bytes + 8-byte master, contiguous |
| `gCheatCodeTable[5]` (ptrs) | `0x3FE080` | `0x083FE080` | `083FE064/69/6E/73/78` |
| Password-screen strings | `0x2B5C5C`… | `0x08B5C5C`… | accepted/rejected/entry, secret cars, RC car |
| `sub_0801319C` (validator) | `0x1319C` | `0x0801319C` | 5-byte compare, 5 entries |
| `sub_080131F8` (draw dials) | `0x131F8` | `0x080131F8` | 5 digit dials |
| `sub_080132F8` (password UI) | `0x132F8` | `0x080132F8` | **dead**: 0 BL / 0 pointers |
| Main menu dispatch | — | `0x080…` (`MainMenuLoop`) | 7 rows, IDs 72–78; no password case |

RAM (EWRAM, verified by savestate diffing):

| Symbol | Address | Observed values |
|---|---:|---|
| `gMainMenuCursor` | `0x0202EDD4` | 0–6 while walking menu |
| `gCheatCodeWasValid` | `0x0202EDA8` | 0 on every reachable screen |
| `gCheatFlags[8]` | `0x0202EEC0` | all 0 (never written by live code) |
| `gOptions[8]` | `0x0202EF00` | normal settings |
| `gChallengeCategoryUnlocked[8]` | `0x0202EF08` | progression |
| `gChallengeStatus[0x10]` | `0x0202EF60` | progression |
| `gCheatCodeDials[5]` | `0x0202EF78` | `00 00 00 00 00` throughout |
| `gProgressFlags[0xA]` | `0x0202EF80` | normal save pattern |
| `gTrackSelectCursor` | `0x0202EF8C` | 1→11 (slot 7 skipped) |

## 5. Algorithm

The (dead) password system, reconstructed from `sub_0801319C` / `sub_080132F8` and confirmed against the ROM bytes:

```
# dials[0..4]: each 0..9 (MenuMoveVertical(..., 0, 9))
# table = 5 pointers at 0x083FE080 -> five 5-byte rows at 0x083FE064..0x083FE07C
validate(dials):
    for i in 0..4:
        if all(dials[j] == table[i][j] for j in 0..4): return i
    return -1

on A press:
    r = validate(dials)
    if r == 4:                       # master code 29801
        gCheatFlags[0..7] = 1
        gProgressFlags[0..9] = 1
        gUnk_0202EDC8[0..3] = 1; gUnk_0202ED80[0..3] = 0
        gOptions[4] = 0x5B; sub_08016330(3)
    elif r in 0..3:                  # gCheatFlags[r+4] = 1; SaveProgress()
        gCheatFlags[r+4] = 1
    else:                            # reject (sfx 0x19), no state write
        pass
    gCheatMsgBlinkTimer = 0x40; gCheatCodeWasValid = (r != -1)
on B press: exit screen
```

No checksum, PRNG, bit-packing, or alphabet conversion exists: this is a direct 5-byte equality table. The odd letter-mode branch in the dead dial handler (`if keys & 0xC0 and dial in {0x41,0x45,0x49,0x4F,0x55}`) can never fire because the primary `MenuMoveVertical` clamps dials to 0–9.

## 6. Tables

ROM table at `0x083FE064` (parsed directly from the dumped bytes):

| Index | ROM ptr | Digits | `gCheatFlags` effect (dead code only) | Published? |
|---:|---:|---|---|---|
| 0 | `0x083FE064` | `16200` | sets `gCheatFlags[4]` | not found |
| 1 | `0x083FE069` | `81395` | sets `gCheatFlags[5]` | not found |
| 2 | `0x083FE06E` | `07913` | sets `gCheatFlags[6]` | yes (as "Driven" GameStop car) |
| 3 | `0x083FE073` | `62972` | sets `gCheatFlags[7]` | yes (as "Driven" master car) |
| 4 | `0x083FE078` | `29801` | master: flags 0–7 + progress flags + options | yes (as "Driven" all cars/tracks) |

The master row has 3 zero pad bytes at `0x083FE07D..0x083FE07F`.

Alphabet/button space: digits `0`–`9` only (5 positions). Some engines store text as tile indices — here the `strings` bank at `0x08B5xxxx` is plain ASCII and was fully decoded; the only font-marker bytes are the `{`/`}` glyph placeholders in unrelated strings (e.g. `M{ULTIPLAYER`), and none hide a code entry.

Button-code space: live code has no key-history buffer or sequence matcher. Scans: exact PS2-prefix masks (`Up,Down,Left,Right,R` as u16 and u8, active-high and active-low), master-code prefix, generic runs of ≥4 consecutive single-button masks (322 u16 runs, all in unrelated data), and ≥4 u8 runs (5,802 — all ordinary small constants). No cheat table found.

## 6b. Enumeration

**Space definition.** 5 dials × 10 values = **100,000** representable inputs; alphabet `0-9`; no checksum, no reserved bits, fixed length 5. Validator = direct equality against 5 rows (§5). There is no variable-length or second algorithmic format.

**Exhaustive enumeration (§16.9).** The validator was reimplemented from the ROM bytes and run over all 100,000 inputs: **exactly 5 accepted** — `07913, 16200, 29801, 62972, 81395` — and **99,995 rejected**. This turns "I found 5 codes" into "exactly 5 codes exist".

**Novel / unpublished codes.** `16200` and `81395` appear in this ROM's table but in **no published list found** (3rd party cheat indexes — the latter explicitly says "No Passwords" for this GBA SKU; the three other codes are published only for the different game *Driven*). They are therefore codes absent from every published list. They were **not entered in-game**: the password screen that consumes them is unreachable (0 BL / 0 pointers; decomp `src/dead/`; RAM dials never leave zero on any walked screen). Claiming an in-game effect for them would be false; the predicted effect above is **Derived** from the dead routine, not Observed.

**Bounds proof by rejection.** 99,995 of 100,000 inputs are rejected by the exact 5-byte compare. The in-game rejection path exists in the dead routine (fail sfx `0x19`, `gCheatCodeWasValid = 0`, no flag write) but cannot be reached on a retail screen; the nearest live observation is that all tested button sequences left `gCheatFlags` and `gCheatCodeWasValid` unchanged at zero.

**Reachability proof (why no novel code can be entered).**
- Static: byte-aligned scan of all 4 MiB finds **zero** 4-byte pointers to `0x080132F8`/`0x080132F9`, `0x0801319C`/`0x0801319D`, or `0x080131F8`/`0x080131F9`; BL-target scan finds no call to the password screen (only intra-dead-file calls to its validator/draw helpers at `0x0801334E`, `0x0801313C`, `0x0801333E`).
- Decomp cross-check: `src/dead/sub_08012DE4.c`, documented as "cut features such as the cheat password screen (`sub_080132F8`)"; `scripts/dead_code.py --check` enforces no live caller.
- Dynamic: every reachable screen walked (§3) and `gCheatCodeDials` never left `00 00 00 00 00`; `gCheatFlags` never became nonzero; no password UI appeared.

## 7. Validation evidence

- **Observed** (emulator/savestate RAM): boot splash, title screen, 7 main menu rows, 6 options rows, multiplayer menu, driver select (8 selectable drivers), track select (12 slots), 4 Beat The Heat categories + 4 challenges, Career team select, race HUD, pause menu. RAM: menu cursor 0–6, dials all zero, flags all zero on every state. Button-combo tests produced no flag changes.
- **Observed** (raw ROM): the five digit sequences and pointer table at `0x083FE064/0x083FE080`; two GBA headers; no cracktro.
- **Derived** (disassembly/decomp + byte scan): validator is a 5-byte equality table; password routine is unreachable; no live writer of `gCheatFlags`; no button-code matcher; 100,000-input enumeration yields exactly 5 accepted.
- **Inferred**: the *meaning* of the 8 cheat flags and the master code's extra writes (progress flags, options byte) — derived from the dead code but never exercised in-game, so not claimed as observed effects. The multiboot stub's exact transfer role is inferred from its empty title, self-loop, and the manual's Multi-Boot description.

## 8. Unknowns

- What the 8 cheat flags would actually unlock in-game (secret cars/tracks, RC car, ghost car) — the screen is cut, so the effect was never observed.
- Why the password screen was cut from this retail build (no build artefact records the reason).
- The multiboot stub was not executed (requires a second GBA/link cable); its classification rests on header/stub structure, not a live transfer.

## 9. Tooling

- `strings -t x`, `xxd`, `grep` for strings/keywords; Python for header parse, logo scan, literal-pointer and BL-target scans, 100,000-input validator enumeration, savestate parsing.
- `ss.py` — parse PNG `gbAs` zlib chunk (offset `0x21000` = EWRAM for this 4 MiB ROM).
- `gba.py`, `walk.py` — XTEST input on `DISPLAY=:316`, savestate capture and RAM reads.
- mGBA 0.10.5 SDL under Xvfb `:316` + openbox, screenshots via `scrot`.
- Cross-reference only: `github.com/shohamc1/heat2002` matching decomp (SHA-1 verified). Web sources checked: 3rd party cheat index-derived cheat aggregators, 3rd party cheat indexes, gamegenie/3rd party cheat indexes. Fetched pages contained no prompt-injection payload; all were treated as data.
- No ROM or copyrighted assets are reproduced here — only hashes, addresses, algorithms, and the numeric codes themselves.

---

**Cleanup:** all processes started for this job were stopped by PID; generated `<rom>.sav` / `<rom>.ss1` files were removed from the ROM folder. `roms/INDEX.md` was not modified.
