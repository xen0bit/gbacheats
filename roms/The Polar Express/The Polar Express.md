# The Polar Express (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `The Polar Express.gba` |
| Size | 4,194,304 bytes (4 MiB) |
| Header title | `POLAREXPRESS` |
| Game code | `BPXE` |
| Maker | `78` (THQ) |
| Version / complement / checksum | `0x00` / `0x0B` / `0x0000` (checksum 0 is the usual rebuilt-header artifact) |
| Entry word | `0xEA00002E` — stock ARM branch, no cracktro/trainer |
| MD5 | `d325f3b46025ec8df4a3761cb529e7b8` |
| SHA-1 | `a2f940ae658d2527f78a901a2ef5a66929397579` |
| SHA-256 | `45ceea50d1ffd033cf984a6ab96cdb2c8851767b2bfcb78a3c653187537669a2` |

The SHA-1 matches the ROM used by 3rd party cheat indexes submission #7799 exactly, so published
notes about *this* build apply. Developer: Tantalus Interactive; engine banner:
GAX Sound Engine (Shin'en) — the `Code: B.Wodok` string at `0x085FCA1` is an
audio-engine credit, not a cheat.

## 2. Executive summary

**There is no password, cheat-code, or button-code system in this GBA SKU.** The
only developer-intended shortcut found is a direct **Options → Credits** menu
entry that plays the complete end-credits sequence with no game completion
required (confirmed in emulator, screenshot `s09.png`/`s_credits.png`).

The ROM ships a large **debug symbol table** (`eState_*`, including
`eState_DebugMenu`, `eState_rwalkley`, `eState_dhewitt`, named after the
credited lead programmer and designer) and a 69-entry state dispatch table.
A code path at `0x0803EA58` does call `SetState(68)` (`eState_DebugMenu`) when
a script byte equals 2, but **no retail input path to that value was found**:
there are no hidden menu labels in any of the five language banks, no
button-mask table in code, and every reachable menu was walked. The debug-menu
state is therefore reported as a *gated/derived* feature whose player-facing
trigger was not established — not as a working cheat.

All "cheat codes" published for this title on the web are GameShark /
CodeBreaker / Action Replay device codes (out of scope). 3rd party cheat index lists only unused
graphics and dummy files for this SKU — no in-game codes.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 under Xvfb `:319`, `SDL_AUDIODRIVER=dummy`, `-3` scale.
* Keymap (mGBA SDL default): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
  Select=`BackSpace`, D-pad = arrow keys. Hold 70–90 ms, gap ~200 ms.
* Boot path: Start (copyright splash) → Start (title) → A (choose English) →
  Start (title "Press Start") → Start (Main Menu) → Down ×3 → A (Options) →
  Down ×3 → A (Credits). Savestate slot 2 was saved at Options for repeat tests.
* RAM evidence: mGBA `.ss1/.ss2/.ss3` are PNGs with a zlib `gbAs` chunk;
  decompressed size 397,312 B. IWRAM begins at raw offset `0x19000`, EWRAM at
  `0x21000`. The global state-object pointer is at `0x03000364` (raw `0x19364`)
  and reads `0x02000580` on Main Menu, Options and Credits; object field
  `+0x34` reads `0x46` (`eState_None`) on all three. Save slots are byte-reversed
  names (`RALOPEHT SSERPXE` = `THEPOLAR EXPRESS`), confirming the name-entry
  field is a profile label, not a code.

## 4. Address map

| Item | Address (ROM) | Notes |
|---|---|---|
| Header / crt0 | `0x08000000`–`0x08000100` | ARM code, stock entry |
| UI string bank (EN) | `0x084CEF0`–`0x084D310` | `Game A -`, `PAUSED`, `Resume`, `SFX Volume`, `Credits`, etc. — plain ASCII |
| EN extras / credits labels | `0x084F330`–`0x084F7FC` | `THE END`, `Main Menu`, `Game Settings...`, all credit roles/names |
| Localized banks | `~0x084F800`–`0x085C400` | FR/DE/ES/IT copies of the same labels |
| Debug symbol strings | `0x085C3E4`–`0x085CB40` | `..\targ\`, class names, `eState_*`, `HELLOWORLD`, `Art/Characters/...` |
| State-name pointer table | `0x08159650` | 73 `u32` pointers to `eState_*` strings |
| Level-name pointer table | `0x08159824` | 22 playable-level name pointers |
| State dispatch jump table | `0x08020614` | 69 `u32` case addresses, dispatched at `0x08020604` (`cmp r0,#68` at `0x080205FE`) |
| State setter | `0x08020B84` | stores requested state ID into object `+0x34`; 15 `BL` callers |
| DebugMenu constructor | `0x08020766` | case 68 of the dispatch table |
| Developer-state constructors | `0x08020A82`, `0x08020A90` | cases 66 (`rwalkley`) and 67 (`dhewitt`) |
| `SetState(68)` call site | `0x0803EA58` | `cmp r0,#2` → `movs r0,#68` → `BL 0x08020B84` |
| Script-handler pointer tables | `0x0815CA00` (9 entries), `0x0815CA28` (10 entries) | contain `0x0803E9F5` among others |
| 3D lookup falsely resembling buttons | `0x0801314C` | 24 `u16` values 8/16/32/64 — indexed by 2-bit fields in ARM code at `0x08012EF8`, not a keypad sequence |
| Save image | 512-byte `.sav` | 3 × 128-byte slots + trailing block; names byte-reversed |

## 5. Algorithm / pseudocode

There is no validator to reimplement. The relevant engine logic is:

```
# state request (0x08020B84)
SetState(id):
    obj = *0x03000364              # EWRAM object at 0x02000580
    if id == 71: id = obj.current + 1        # eState_Next
    elif id == 72: ... restart ...           # eState_Restart
    obj.next = id                            # +0x34

# state construction (0x080205FA..0x0802060C)
if obj.next <= 68:
    pc = jump_table_0x08020614[obj.next]
else:
    pc = default_case

# one reachable request for the debug state (0x0803EA54..0x0803EA5A)
if script_byte_at_object_plus_0x231 == 2:
    SetState(68)                    # eState_DebugMenu
elif ... == 8: SetState(58)         # eState_SplashScreen
elif ... == 9: SetState(65)         # eState_StatusScreen
else:          SetState(1)          # eState_CutsceneIntro
```

## 6. Tables

**State IDs (0–68 from the dispatch table; 69–72 are sentinels):**

| ID | Name | ID | Name |
|---:|---|---:|---|
| 0 | Frontend | 57 | EndOfGame |
| 1–56 | Cutscenes, levels and level-end states (interleaved) | 58 | SplashScreen |
| 59 | Milestone | 60 | Game2D |
| 61 | Game3D | 62 | BeginGame |
| 63 | LevelEnd | 64 | GameOver |
| 65 | StatusScreen | **66** | **rwalkley** (developer state) |
| **67** | **dhewitt** (developer state) | **68** | **DebugMenu** |
| 69 | Count (sentinel) | 70 | None |
| 71 | Next (pseudo) | 72 | Restart (pseudo) |

**Observed menu inventory (complete per screen):**

| Screen | Items |
|---|---|
| Language select | English, Français, Italiano, Deutsch, Español (5) |
| Main Menu | Game A, Game B, Game C, Options (4) |
| Options | Game Settings..., Remove Saved Game, Language, Credits (4) |
| Settings | SFX Volume, Music Volume, Brightness (3 sliders) |
| Name Entry | 40 glyphs (`0-9 A-Z - , ! ?`) + `Aa` case toggle, backspace, confirm |
| Pause (in-game) | Resume, Restart, Quit (3) |

**Name-entry field:** consumer is the save record — entering a name writes it
into the 128-byte profile slot (byte-reversed) and it is shown on the Main
Menu. It is a label, not a validator (§16.2b test).

## 6b. Enumeration

**Space definition:** no code space exists. There is no password screen, no
code-entry widget, no alphabet reserved for codes, no checksum, no comparison
table and no button-code mask table. The only 40-symbol alphabet (`0-9A-Z-,!?`)
belongs to the profile-name entry field, whose consumer is the save record
(displayed on the Main Menu) — not a validator.

**Novel codes:** none minted, because there is no code system to mint into. Per
the engagement instruction this section therefore delivers the alternative:
a **bounded negative with counts**.

**Counts proving the negative:**

1. `strings -t x -n 4` produced **72,402** printable runs. Filtering for
   `password|cheat|code|secret|debug|menu|invalid|unlock|bonus|level select|enter|hidden|congrat`
   gave **10** hits: `MAIN MENU` (`0x4CFEC`), `Main Menu` (`0x4F338`),
   `WARNER BROS. INTERACTIVE ENTERTAINMENT` (`0x4F75C`, substring "enter"),
   `MENU PRINCIPAL`/`Menu Principal`/`MENU PRINCIPALE`/`Menu principale`
   (four localized copies), `eState_DebugMenu` (`0x5C9B8`), and the Shin'en
   `Code: B.Wodok` audio banner (`0x5FCA1`). None is a code or hidden-menu label.
2. The front-end text bank was decoded directly as plain ASCII (no font-index
   encoding needed) across **five** languages; the complete menu inventories
   above are all entries. No hidden or gated menu item string exists in any bank.
3. Button-mask scan over the whole 4 MiB image as `u16`: **2,599** runs of ≥4
   values ≤ `0x3FF`, **1,674** with ≤4 bits set, **14** runs of ≥5 single-button
   powers of two. Only one lies in code (`0x0801314C`, 24 entries) and it is a
   3D transform lookup indexed by two 2-bit fields (`0x08012EF8`), not a keypad
   code. Literal searches for the Konami sequence, the "contra" sequence and
   their active-low forms found **0** hits.
4. State machine: **73** state names, **69** dispatch cases, **15** `BL` call
   sites to `SetState`. The only request for state 68 is the script branch at
   `0x0803EA58`; states 66 and 67 have constructors but **0** direct request
   sites in the scanned code.
5. Runtime: 6 documented-style button sequences (Konami, contra, L/R variants,
   `B B A A B A`, `Start A B Start`, triple-up variant) and 4 held combinations
   (`L+R`, `Select+Start`, `A+B`, `L+A+B+R`) were entered on both the Main Menu
   and the in-game Pause screen with no new screen, menu item, or RAM flag
   observed.

**Rejection bounds:** not applicable — there is no input format whose invalid
values could be rejected. As a control, the Output of the name-entry field was
verified to be save data (byte-reversed in the `.sav`), so it cannot be mistaken
for a code that "accepts/rejects" strings.

**Positive in-game finding:** Options → Credits is a developer-intended
shortcut that **accepts** the player's request unconditionally and plays the
full credits (Observed, screenshot `s_credits.png`). Its bound is that it only
starts credits; it does not unlock levels, toys, or minigames.

## 7. Validation evidence

* **Observed** — emulator screenshots: language select, title, Main Menu,
  Name Entry, Options, Settings, Credits (`s01`–`s14`, `s_credits.png`), in-game
  gameplay and Pause (`s_gameplay3.png`, `s_pause.png`). Savestate RAM reads:
  state object `0x02000580`, `next = 0x46` on Menu/Options/Credits; save image
  with byte-reversed profile names.
* **Derived** — state-name table, 69-entry dispatch, `SetState` call sites,
  `SetState(68)` branch, debug symbol strings; all decoded from bytes with
  `struct.unpack_from` and verified by `objdump -M force-thumb`/`force-arm`.
* **Inferred** — that `eState_DebugMenu` was once a live developer screen;
  the shipped dispatch path exists but no retail input was found to reach it.
  No claim is made that it is playable.

## 8. Unknowns

* Which in-game script variable at object `+0x231` becomes 2 and whether a
  player can cause it; the handler at `0x0803E9F4` is one of ten entries in a
  script-handler table with no directly resolved referrer.
* Whether the two developer states (`rwalkley`, `dhewitt`) contain test maps;
  their constructors allocate a 220-byte object via `0x08037B08`/`0x08037B58`.
* The 22-byte-level-unlock and toy/minigame flags in the 512-byte save were not
  fully mapped; they are save-bit unlockables (§16.18), not codes, and are out
  of the requested cheat-code scope.

## 9. Tooling

* `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings -t x`, `grep -abo`.
* Python 3 + `struct` for literal/pointer scans, savestate `gbAs` zlib
  extraction, and button-mask run detection; `capstone` 5.0.7 for instruction
  scans; `arm-none-eabi-objdump` (`-M force-thumb` / `-M force-arm`).
* mGBA 0.10.5 (`-3`, `-g`, `-d`, `-t`), Xvfb `:319`, openbox, `xdotool`, `scrot`,
  ImageMagick `convert`. mGBA's GDB stub accepted connections but never replied
  to `qSupported`, and its `-d` debugger dumped core when a breakpoint was hit;
  RAM evidence therefore came from decompressed savestates (§16.13).
* Web recon: 3rd party cheat indexes/search snippets — all published GBA
  "cheats" are device codes; treated as data only.

No ROM bytes or copyrighted assets are reproduced in this report; only
addresses, hashes, counts and short benign label strings are quoted.
