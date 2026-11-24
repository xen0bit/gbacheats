# The Wild (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/The Wild/The Wild.gba` |
| Size | 8,388,608 bytes (0x800000) |
| Header title | `THE WILD` |
| Game code | `BWLE` |
| Maker code | `4Q` (Buena Vista Games / distributed by Nintendo) |
| Version | 0x00; fixed byte 0x96; complement 0x71; header checksum 0x0000 |
| Entry word | `0xEA00002E` — stock `b 0x080000C0` (not a cracktro; guide §16.1) |
| MD5 | `643dadc449b6b43c78ecad898a0e0c83` |
| SHA-1 | `a7cf830919081655544a7beb2c1a94bdbab6a72e` |
| SHA-256 | `681dcf59f3e34e9857bb0467de4878585a547cf1e4de042454675446b0103a60` |

Developer Climax Studios, 2006, based on the Disney film. Header/ROM identity matches the
retail GBA SKU; no trainer or appended cracktro was found.

## 2. Executive summary

**There is no in-game code system in this SKU.** No password screen, no code-entry widget,
no published password list, and no reachable button-code dispatcher exists. A complete walk
of every reachable screen (boot logo, language select, title, main menu, options, save-slot
selection, select-mode, cutscenes, gameplay, pause menu) shows only New Game, Load Game,
Options, Tutorial, Story, Challenge, Gallery and the four pause entries. Challenge and
Gallery are progression-gated (greyed out). No screen accepts text or a code.

The ROM **does** contain an compiled-in, developer-intended cheat menu (five entries:
"ALL CHEATS ON", two challenge-unlock entries, "INVINCIBILITY", "RESET EVERYTHING") and a
button gate that reacts to A+Start / B+Select. **All of it is dead code**: the cheat-menu
state handler `0x0800a7e4` has zero BL callers, zero literal pointers (direct or Thumb-bit),
zero branch callers, and is absent from the game's state table. Three hardware breakpoints
on the dead block never fired in any screen or after 17 multi-button combinations. This is a
*dead-code* negative (guide §16.3 case 2), not an untested feature.

## 3. How to reproduce

- Emulator: mGBA 0.10.5 under Xvfb `:319`, `SDL_AUDIODRIVER=dummy`, `mgba -3 -d game.gba`.
- Default SDL keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, arrows.
- Path: boot → A at language select → A at "PRESS START" → Main Menu → A at New/Load Game →
  SELECT SAVE SLOT → A → SELECT MODE → A at TUTORIAL → cutscene (mash A) → gameplay →
  Start → PAUSE MENU.
- Debugger (mGBA `-d` pty): `b/t 0x0800a774`, `b/t 0x0800a7e4`, `b/t 0x0800a9d0`,
  then `c`. RAM reads at the frame hook `0x08035920`:
  `r/1 0x0300636d` → `0x00`, `r/1 0x0300636f` → `0x00`, `r/4 0x03005200` → `0x00000000`.
- Button combos tested on Main Menu and in game (held ~250 ms): `L+R`, `L+R+Start`,
  `L+R+A+B`, `B+Select`, `Up+Down+Left+Right`, the 10-press Konami sequence,
  `Start+Select`, `L+R+Up/Down/Left/Right`, `R+A`, `L+A`, `R+B`, `L+B`, `L+R+Select`.
  None opened a menu or hit a breakpoint.

## 4. Address map

| Address (ROM) | Meaning |
|---|---|
| `0x0800a774` | Dead button gate: tests `pressed & 0x9` and (state byte == 6) `pressed & 0x6`; sets `0x03005200 = 1` on the latter |
| `0x0800a6b8` | Dead caller loop of the gate (per-frame) |
| `0x0800a4f0` | Dead enclosing function; **zero** BL/literal/branch callers |
| `0x0800a7e4` | Dead cheat-menu state handler (sets up menu, calls builder and loop) |
| `0x0800a8d0` | Dead cheat-menu main loop (called only from `0x0800a876`) |
| `0x0800a8f4` | Dead 5-way action dispatcher (jump table at `0x0800a904`) |
| `0x0800a91c` / `0x0800a930` / `0x0800a944` | Dead flag writes: `mov byte [0x0300636F], 1 / 1 / 0` |
| `0x0800a95c` | Dead menu input helper (reads halfword at `0x03006A90+0x0C+2*i`) |
| `0x0800a9d0` | Dead cheat-menu builder; title pointer `0x0808d3c4` |
| `0x0808d3c4` | `"- CHEAT MENU -"` |
| `0x087a9540` | 5-entry pointer table of cheat-menu labels (NUL-terminated at `0x087a9554`) |
| `0x0808d350`–`0x0808d3c4` | Cheat labels: RESET EVERYTHING, INVINCIBILITY, two challenge unlocks, ALL CHEATS ON |
| `0x087a9280` | Live debug state-name table: 12-byte records `{handler\|1, name_ptr, state_id}`, states 0x00–0x1b with gaps 0x0d/0x10/0x12; names at `0x0804c6b0`–`0x0804c888` |
| `0x08035920` | Live per-frame input poll: `held = ~KEYINPUT`, `pressed/held/released` at `0x03006A90+4/+0x0C/+0x14` |
| `0x0804e8cc`–`0x0804f3c0` | Live ASCII UI text bank (all menu strings) |
| `0x0809a170`–`0x0809a918` | Debug build banner + 60+ `"debug only"` placeholder entries |
| RAM `0x0300636D/6E/6F` | Dead gate/cheat byte triple (observed `0,0,0` at boot) |
| RAM `0x03005200` | Dead gate output flag (observed `0`) |
| I/O `0x04000130` | KEYINPUT, active-low; observed `0x03FF` (no keys) |

File offset = ROM address − `0x08000000` for all of the above.

## 5. Algorithm

**Live input path (derived):** `0x08035920` computes
`held = ~KEYINPUT & 0xFFFF`, `pressed = held & (held ^ old)`, `released = ~held & (held ^ old)`,
stored at `0x03006A90+4`, `+0x0C`, `+0x14`. No code compares any user-entered string.

**Dead gate (derived, `0x0800a774`):**

```
p = 0x03006A90; i = [p+0x20]; b = halfword[p+0x0C + 2*i]      # input mask
if b & 0x0009:              # A or Start
    show_message(0x02023F20, 0x08773CDC); return 1
if byte[0x0300636D] == 6 and (b & 0x0006):   # B or Select on state 6
    show_message(0x02023F20, 0x08773CDC); byte[0x03005200] = 1; return 1
return 0
```

`0x0300636D = 6` is written in the dead block at `0x080063BE` when input bit `0x80` (R) is
seen. The gate is only called from `0x0800a6E6`, itself only from `0x0800a4F0`, which has no
callers: the chain is unreachable.

**Dead cheat-menu dispatcher (derived, jump table base `0x0800a908`, index 0..4):**

| Index | Label at `0x087a9540` | Target | Effect |
|---|---|---|---|
| 0 | ALL CHEATS ON (`0x0808d3b4`) | `0x0800a91C` | `byte[0x0300636F] = 1` |
| 1 | g_bUnlockedChallenge EVERYTHING (`0x0808d394`) | `0x0800a94E` | **no-op** (returns immediately) |
| 2 | g_bUnlockedChallenge ALL LEVELS (`0x0808d374`) | `0x0800a94E` | **no-op** (returns immediately) |
| 3 | INVINCIBILITY (`0x0808d364`) | `0x0800a930` | `byte[0x0300636F] = 1` |
| 4 | RESET EVERYTHING (`0x0808d350`) | `0x0800a944` | `byte[0x0300636F] = 0` |

All three wired actions hit the same byte, `0x0300636F`; the two challenge-unlock rows are
stubs. There is no encoder, decoder, checksum, alphabet or comparison table anywhere in
this subsystem — it is a five-item menu, not a code validator.

## 6. Tables

- Cheat label pointer table (`0x087a9540`): 5 entries, fully listed in §5.
- Debug state-name table (`0x087a9280`): 28 records for states `0x00`–`0x1b`
  (0x0d, 0x10, 0x12 unused); covers CompanyScreen … ChallengeMenu. The cheat menu has
  **no** record — its handler `0x0800a7e4|1` does not occur in the table.
- Debug string markers: 24+ `"debug only"` placeholders at `0x0809a170`, `0x0809a1f8`–
  `0x0809a460`, `0x0809a66c`–`0x0809a684`, `0x0809a900`–`0x0809a918`, plus
  `0x0804c650`, `0x0806827c`–`0x080682cc`, `0x0808d9e4`–`0x0808da14`, `0x0809a170` etc.
  Build banner `August 11 2005 / 17:09:22 / Release` at `0x0809a18c`.
- Save-game unlockables (`0x0804f15f` "CHALLENGES TO UNLOCK", `0x0804f180` "UNLOCKED",
  `0x0804f19d` "Complete %d challenges…") are chapter/challenge progression flags, not codes.

## 6b. Enumeration

**Space definition:** empty. The accepted-input space is 0 because the game exposes no
code input surface at all: no password field, no on-screen alphabet, no code table, no
checksum, no validator called with user text. Searches for these encodings of
`PASSWORD` / `ENTER CODE` across the full 8 MiB returned **0 hits each**: ASCII upper,
ASCII lower, `+0x20` shifted, UTF-16LE, UTF-16BE, `CONTRASEÑA`, `MOT DE PASSE`, `PASSWORT`.
The complete live text bank (`0x0804e8cc`–`0x0804f3c0`) was read as ASCII; every visible
label is accounted for and none is a code prompt.

**Novel codes:** not applicable — no code generator exists to mint from, and there is no
validator oracle to satisfy. Generating a "novel code" was therefore impossible by
construction, not by failure to find one.

**Reachable-screen enumeration (all screens, screenshots on disk):**

| # | Screen | Entries observed | Code input? |
|---|---|---|---|
| 1 | Buena Vista logo | — | no |
| 2 | Language select | ENGLISH, FRANÇAIS, DEUTSCH, ESPAÑOL | no |
| 3 | Title | PRESS START | no |
| 4 | Main Menu | NEW GAME, LOAD GAME, OPTIONS | no |
| 5 | Options | MUSIC ON, SFX ON, CREDITS | no |
| 6 | Select Save Slot | 3 slots (1 used) | no |
| 7 | Select Mode | TUTORIAL, STORY, CHALLENGE†, GALLERY†, OPTIONS | no |
| 8 | Tutorial cutscenes → gameplay | dialogue + platform level | no |
| 9 | Pause Menu | RETURN TO GAME, RESTART LEVEL, QUIT GAME, OPTIONS | no |

† greyed out / progression-gated.

**Bounds proven by counts (dead-code negative):**

| Count on cheat handler `0x0800a7e4` | Value |
|---|---|
| Thumb BL / B.w callers | **0** |
| 32-bit literal pointers (value and `value\|1`) | **0** |
| Unconditional branch callers | **0** |
| Entries in the 28-record state-name table | **0** |
| Breakpoint hits across 9 screens + 17 button combos | **0** |

Supporting chain counts: `0x0800a774` has 1 BL caller (`0x0800a6e6`), `0x0800a6b8` has
1 BL caller (`0x0800a4f0`), and `0x0800a4f0` itself has **0** callers of any kind. The gate
and the cheat menu are therefore unreachable from any input path. Breakpoints at
`0x0800a774`, `0x0800a7e4`, `0x0800a9d0` remained at 0 hits for the whole walk.

**Button-mask search:** the live input state uses active-high masks (A=1, B=2, Select=4,
Start=8, Right=0x10, Left=0x20, Up=0x40, Down=0x80, R=0x100, L=0x200). A 2-byte scan for
runs of ≥4 consecutive values in `1..0x3FF` found 17,219 candidate runs; all are in
compressed graphic/audio data or sequential asset-index tables, and none has a validator
consumer. No hard-coded button sequence table exists.

## 7. Validation evidence

- **Observed:** all 9 screens above via scrot; save file created only in the ROM *copy* under
  `/tmp/thewild`; RAM at boot `0x0300636D/E/F = 00 00 00`, `0x03005200 = 00000000`,
  KEYINPUT `0x03FF`; zero breakpoint hits on the dead block.
- **Derived:** dead-menu table/dispatcher/gate logic from raw Thumb disassembly and literal
  pools (`struct.unpack_from` used for every literal, avoiding objdump halfword-order errors).
- **Inferred:** the two no-op rows in the cheat dispatcher are unfinished debug features
  (the strings say "unlock" but the jump target is the bare epilogue). This is read from the
  jump table, not exercised in-game, because the menu itself is unreachable.
- **Web recon (treated as data):** GameFAQs lists no cheats for this SKU (the 4-character
  stage passwords found by search belong to *The Wild Thornberrys Movie*, a different game);
  VGChartz reports "Total cheats available: 0"; a CodeBreaker-code page exists but device
  codes are out of scope per the brief.

## 8. Unknowns

- Whether an earlier/prototype build (the embedded `August 11 2005` banner) wired the cheat
  menu into a state table; the shipped image does not.
- The semantic meaning of a non-zero `0x0300636F` (all writes are 0 or 1; no reader was
  isolated because the subsystem is unreachable).
- Whether Challenge/Gallery contents change after 100% completion; those are progression
  unlockables, not cheats, and were not fully played through.

## 9. Tooling

- `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for all
  disassembly; Python `struct.unpack_from` for literal pools and pointer-table dumps.
- Custom Python scanners: literal-pointer scan, Thumb BL/B scan, button-mask run scan,
  multi-encoding string scan.
- mGBA `-d` pty debugger driven by a persistent Python server (`dbgserver.py`), plus
  `xdotool` XTEST input and `scrot` screenshots on Xvfb `:319`.
- No ROM or copyrighted asset is redistributed here; only addresses, hashes and findings.
