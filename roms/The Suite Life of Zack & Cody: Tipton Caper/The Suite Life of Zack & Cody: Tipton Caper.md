# The Suite Life of Zack & Cody: Tipton Caper (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `The Suite Life of Zack & Cody: Tipton Caper.gba` |
| Size | 8,388,608 bytes (0x800000) |
| Header title | `ZACKANDCODY` |
| Game code | `BZCE` |
| Maker code | `4Q` (Buena Vista Games) |
| Version | 0 (Rev.00) |
| Entry branch | `0xEA00002E` → `0x080000C0` (stock crt0; **not** a scene cracktro) |
| Header checksum / complement | `0x0000` / `0x7D` |
| MD5 | `37811411c46cf9a5ee91b418c6e67930` |
| SHA-1 | `13bd8f4fa4c08b8f1b9d400d0917c0e62cf666fd` |
| SHA-256 | `ef9a36641e738c4ab0605e4f01dd00fb960f203c5d60f8d24b83a8cbb53ee7df` |

Note: my first literal Nintendo-logo comparison used a wrong 156-byte reference and reported
`logo match False`; `file(1)` identifies the image as a valid `ZACKANDCODY (BZCE4Q, Rev.00)`
GBA ROM, and the boot/crt0 bytes at `0x080000C0` are valid ARM, so this was a comparison
error, not a bad image.

## 2. Executive summary

This retail (US, En/Fr) 8 MiB GBA image has **no player-facing password, button code or
cheat-entry screen**. What it *does* contain is a substantial **dormant developer debug
menu**: a 28-entry ASCII debug string bank at `0x08040420`, an 18-entry scene/menu dispatch
at `0x080405F8`, a hidden English menu item `DEBUG CHEATS` at `0x0805E3AB8`, and a complete
menu engine (`0x0801B5C0`, `0x0801B6B4`, `0x0801B7C0`, `0x0802A620`). Its RAM flags
(`0x02003300`, `0x0200CE20`) are **set to 1 at boot** — confirmed by decoding the
zlib-compressed `gbAs` chunk of mGBA savestates — yet no reachable retail screen displays
the menu, and no controller input path that opens it was found.

The only route into the debug scene is a **script-VM command handler** at `0x0801954D`
(table `0x0817F060`, command 5, handler slot +0x18). That handler reads a scene pointer from
`0x02002CD8`; the only two writers of that word are scene-loading routines, not input code.
This is a **gated feature with no reachable retail writer**, not an absent feature and not a
published code. TCRF explicitly lists "Figure out how to access the debug menu" as a *To do*
for this exact game, which agrees with the static result.

Because there is no code system, §0.2's "mint a novel code" deliverable is not applicable.
The bounded negative is delivered instead with explicit counts in §6b/§7: 12 screens walked,
0 code-entry UIs, 0 password strings in 5 encodings across 8 MiB, 2,793 raw key-mask runs
with 0 validator xrefs, 21 button sequences tested with 0 debug-menu openings, and 0
published in-game codes in 5 web sources.

## 3. How to reproduce

* Emulator: mGBA 0.10.5, `SDL_AUDIODRIVER=dummy`, Xvfb `:318`, `mgba -3 <rom>`.
  (Do **not** use `-g` for screen walking here: the GDB stub pauses the core at PC=0 with
  `DISPCNT=0x08000080` (forced blank) and an attempted PC override closed the remote
  connection. Plain SDL is reliable; RAM was read from savestates instead.)
* Keymap verified by observation: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`,
  D-pad=arrow keys. Hold 100–300 ms; mGBA savestates: Shift+F1/F2 save, F1/F2 load.
* Boot path: language select (A) → health & safety (A) → A2M logo → title (Start) → main menu.
* New game path: New Game → slot 1 → A → "Episode 1" card → ~40 A presses through dialogue
  → top-down gameplay. Pause = Start.
* Every screen listed in §7 was reached and screenshotted; screenshots are kept in
  `/tmp/suitelife/*.png` (not redistributed).
* Savestate RAM decoding: mGBA `.ssN` is PNG with a zlib `gbAs` chunk. `zlib.decompress`
  yields 397,312 bytes; EWRAM starts at raw offset `0x21000`, so
  `raw[0x21000 + (addr - 0x02000000)]` is RAM byte `addr`.

## 4. Address map (all ROM offsets are file offsets; add `0x08000000` for ROM addresses)

| Item | File offset / ROM address | Evidence |
|---|---|---|
| Debug ASCII string bank | `0x040420`–`0x0405E8` | Derived — `strings`/`xxd` |
| Debug overlay field table | `0x017F670`–`0x017F800` | Derived — 16-byte records `{str_ptr, 0, handler, params}` |
| Scene/action pointer table | `0x0405F8`–`0x04063C` | Derived — 17 pointers `0x080EDAF8`…`0x080F3968` |
| English `DEBUG CHEATS` menu entry | `0x05E3AB8` | Derived — `$EBUG\xff\xfc#HEATS\xff\xfe` |
| French `MODES DEBUG` menu entry | `0x05EB1D4` | Derived — `#ODES\xff\xfcDEBUG\xff\xfe` |
| Debug menu initialiser | `0x0801B5C0` | Derived — disassembly |
| Menu entry populator (18 slots) | `0x0801B6B4` | Derived |
| Set debug selection (`idx<=17`) | `0x0801B7C0` | Derived — BLs at `0x08016582`, `0x08018E1C` (script handlers) |
| Script handler opening debug scene | `0x0801954D` | Derived — table `0x0817F060`, cmd 5 slot +0x18 |
| Debug scene dispatcher | `0x0802A620` | Derived — tests `0x0200CE20 & 1`, indexes `0x0405F8` |
| 8-slot arrays / comparator | `0x020004F8`, `0x02000508`; helpers `0x0802A3EC`, `0x0802A40C`, `0x0802A428`, `0x0802A44C` | Derived |
| Debug flag A | `0x02003300` (byte) | **Observed** = `0x01` in menu and gameplay savestates |
| Debug flag B | `0x0200CE20` (byte) | **Observed** = `0x01` |
| Debug menu selection | `0x02003308` (byte) | **Observed** = `0x02`/`0x11`; gate `idx<=17` |
| Debug menu object | `0x02003390` | **Observed** = `0x03005F80, 0x00000C00, 0x3D993D99, …` |
| Scene pointer used by debug loader | `0x02002CD8` | Derived — only 2 writers (`0x080194EC`, `0x08019568`), both scene loaders |
| `DebugCheats` label | `0x04AD344` | Derived — ASCII symbol in a debug variable-name/data bank |

`main()` is `0x0802B05D`: the crt0 literal pool at `0x08000110` is `0x0802B05D`, and
`main` → `0x0802AFD8` → `0x0801B5C0`, which is why both debug flags are 1 from boot.

## 5. Algorithm / gate model

```
main (0x0802B05D)
  -> 0x0802AFD8
     -> 0x0801B5C0 (debug-menu init):
          *0x02003300 = 1
          *0x0200CE20 = 1
          *0x02003308 = 0
          build 18 menu entries from table @0x080405F8 (via 0x0801B6B4)
          call 0x0801B7E4, IME=0 around init then IME=1

0x0801954D (script-VM handler, table 0x0817F060 cmd 5 slot +0x18)
  r0 = *0x02002CD8
  bl 0x08027EB8        ; scene switch
  bl 0x0802A898
  bl 0x0801B5C0        ; (re)initialise debug menu
  bl 0x08025FC0(2)

0x0802A620 (debug dispatch/update)
  if !(*0x0200CE20 & 1): return
  idx = *0x02003308
  if table[0x080405F8 + idx*4] == 0:
       *0x0200B7E0 = 1; maybe bl 0x0803AFB8
  else:
       *0x0200B7E0 = 0; maybe bl 0x0803AFC8
  ... sum of 8 halfwords at 0x020004F8 / 0x02000508 ...
```

The gate is therefore **not** a key-code validator: it is a script-VM command. No code that
writes `*0x02002CD8` or issues that script command is reachable from any input handler found
in the walked screens. `0x0802A44C` compares two 8-entry halfword arrays and is the nearest
thing to a "code check", but it has **zero BL callers** and lives inside the debug scene
engine (dead-with-respect-to-retail-input).

## 6. Tables

### 6a. Debug string bank (file `0x040420`; ROM `0x08040420`)

| Index | String | Meaning (inferred) |
|---:|---|---|
| 0 | `Level` | coordinate/level overlay field |
| 1 | `MapX` | coordinate overlay field |
| 2 | `MapY` | coordinate overlay field |
| 3 | `Debug Point` | debug marker overlay |
| 4 | `Prototype` | prototype scene |
| 5 | `Fx Player` | effects viewer |
| 6 | `Music Player` | sound test |
| 7 | `Obj Viewer` | object viewer |
| 8–11 | `First Playable Room 04/03/02/01` | early build rooms |
| 12–14 | `Sub-Goal 03/02/01` | sub-goal scenes |
| 15 | `Extro` | ending scene |
| 16 | `Boss` | boss scene |
| 17 | `Game Complete` | completion scene |
| 18–22 | `Episode 05/04/03/02/01 ->>` | episode scene links |
| 23 | `Asset Viewer   ->>` | asset viewer link |
| 24 | `Episodes       ->>` | episode list link |
| 25 | `First Playable ->>` | first-playable link |
| 26 | `Prototypes     ->>` | prototype list link |
| 27 | `Normal Boot` | return to retail boot |

The overlay field records at `0x017F670` pair these strings with handlers `0x0817FAF9`,
`0x0817FAFB`, `0x0817FAFD`, `0x0817FAFE` and parameter words such as `0x000B0107`,
`0x00107D00`, `0x00130600` — i.e. a "draw debug field #N" dispatcher.

## 6b. Enumeration

**Code-space characterisation:** there is no password/button-code space to enumerate.

| Checked surface | Count | Result |
|---|---:|---|
| Player-facing code-entry screens across all walked screens | 12 screens | 0 found |
| `PASSWORD` / `ENTER CODE` / `CHEAT CODE` strings, ASCII, case-insensitive, uppercase-tile-shift (`0x61..0x7A`→`0x41..0x5A`), UTF-16LE/BE, UTF-32, across 0x800000 bytes | 5 encodings × 8 MiB | 0 hits; the only letter-like hits are `KEYCARD`, `BYPASS`, `PASSAGE`, `SECRET` in **dialogue**, which are physical in-game keycards/passages, not codes |
| Raw runs of ≥4 consecutive u16 key-mask values (active-high `A=1,B=2,Select=4,Start=8,R=0x10,L=0x20,U=0x40,D=0x80,R=0x100,L=0x200`) | 2,793 candidate runs | 0 had a validator xref in the code region; every hit was inside script/text or compressed data (typical false positive: repeating `0x0008,0x020B` at `0x020927` etc.) |
| `0x04000130` (KEYINPUT) literal-pool references in code (`<0x600000`) | 2 (`0x02A2D8`, `0x03AE20`) | both are ordinary input-shadow reads, no sequence matcher |
| Button sequences/combos actually pressed on title, main menu, gameplay and pause menu | 21 | 0 opened any debug menu; `A+B+Start+Select` soft-resets to the language screen (a master reset, not a cheat) |
| Published in-game codes across TCRF, GameFAQs (GBA + DS), GameHacking.org, ROMSFUN, GBAtemp | 5 sources | 0 in-game codes; only cheat-device (CodeBreaker/AR) memory patches, explicitly out of scope |
| Scene-pointer writers for the only debug-loader input (`0x02002CD8`) | 2 | both are scene allocators (`0x080194EC`, `0x08019568`), neither is an input handler |

**Debug-menu contents enumerated (static, because the menu cannot be opened by retail input):**
28 string-bank entries above, of which 18 are the selectable scene slots indexed by
`0x02003308` (`idx<=17` at `0x0801B7CE`): `Level`, `MapX`, `MapY`, `Debug Point`,
`Prototype`, `Fx Player`, `Music Player`, `Obj Viewer`, `First Playable Room 04/03/02/01`,
`Sub-Goal 03/02/01`, `Extro`, `Boss`, `Game Complete` (17) plus the null slot 0. The second
group of 10 (`Episode 01–05`, `Asset Viewer`, `Episodes`, `First Playable`, `Prototypes`,
`Normal Boot`) are submenu links rendered by the `->>` marker. The hidden English menu label
is literally `DEBUG CHEATS` (`0x0805E3AB8`), French `MODES DEBUG` (`0x0805EB1D4`); neither
string appears on any of the 12 reachable screens.

**Novel code:** none exists to mint. There is no alphabet, no checksum, no validator and no
code-entry UI; the format space is empty, so "generate a code absent from published lists"
is undefined rather than failed. The §0.2 alternative — a bounded negative with counts — is
delivered by the table above. **Rejection bounds** were probed by entering every tested
button combination and confirming on-screen that neither the pause menu, main menu nor
gameplay gains a `DEBUG`/`DEBUG CHEATS` entry, and by confirming in RAM that
`0x02003308` only takes values `0x00` (after reset/debug init) or `0x11` and never a value
that selects a debug scene during retail play.

**Unlockables (not codes):** keycards (4), photo-album fragments, alternate outfits and the
DS GBA-slot old-save bonus are ordinary progression/save state, stored in the 512-byte
EEPROM `.sav`; they are collected in-game and are not cheat codes.

## 7. Validation evidence

* **Observed** — all 12 screens walked in mGBA with screenshots; `0x02003300=0x01`,
  `0x0200CE20=0x01`, `0x02003308=0x02/0x11`, `0x02003390` contents decoded from real
  savestates; `A+B+Start+Select` soft-reset; 21 button sequences produced no debug screen.
* **Derived** — static disassembly of `0x0801B5C0`, `0x0801B6B4`, `0x0801B7C0`,
  `0x0801954D`, `0x0802A620`, `0x0802A3EC`–`0x0802A44C`; string/text-bank decode at
  `0x08040420` and `0x0805E3AB8`; crt0 → `main` = `0x0802B05D` from the literal at
  `0x08000110`; xref counts for `0x02002CD8`, `0x02003300`, `0x0405F8`, `0x04000130`.
* **Inferred** — that the 18 slots correspond one-to-one with the first 18 debug strings and
  that `0x02003308` is the selected slot; the menu's on-screen appearance was never rendered
  because no retail input reaches it. The GDB direct-call attempt to render it (`pc=0x0801954D`,
  `lr=0x0801B6DB`) closed the remote connection and showed only the language screen, so it
  is **not** counted as an observation.
* **Web content treated as data** — all fetched pages were read as evidence only; no
  instruction or "decode key" found in them was followed. No prompt-injection payload was
  encountered in this session.

## 8. Unknowns

* The script-VM command that reaches `0x0801954D` was not located in any reachable script
  stream; the game's scripts are in a custom compiled format and were not fully parsed. The
  negative is therefore bounded to "no retail input path found during the full screen walk
  plus static xref analysis", not an absolute proof for every possible script byte string.
* The exact on-screen layout/effect of each of the 18 debug scenes is inferred from the
  string bank and handler table, not observed.
* The `DebugCheats` variable at `0x0200BFxx` was not read live; it is a debug symbol label in
  a data bank (`0x04AD344`), not a game flag we exercised.
* A possible GBA-slot/DS link unlock exists in the sibling DS game, but it is an input to the
  *DS* game, not an in-game code in this GBA image; it was not attempted (hardware absent).

## 9. Tooling

* `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings`, `grep -abo` (Phase 0/recon).
* Python 3 + `capstone` for literal/BL/xref scans; `arm-none-eabi-objdump -M force-thumb`
  for disassembly; custom `key.py`, `combo_test.py` for XTEST input; Python zlib/PNG parser
  for `gbAs` savestate RAM decoding.
* mGBA 0.10.5 under Xvfb `:318` + openbox, `SDL_AUDIODRIVER=dummy`, `xdotool`, `scrot`.
* No ROM or copyrighted asset is redistributed; only hashes, addresses, algorithms and our
  own analysis scripts/screenshots are reported.

## 10. Cleanup

All processes started for this engagement were terminated by numeric PID and all `.sav` /
`.ss1`–`.ss4` artifacts were removed from the ROM folder (see final reply).
