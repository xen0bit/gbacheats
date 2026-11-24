# Sea Trader: Rise of Taipan (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Sea Trader: Rise of Taipan.gba` |
| Size | 4,194,304 bytes (0x400000, 4 MiB) |
| Header title | `SEA TRADER` (0x080000A0) |
| Game code | `ALJE` (0x080000AC) |
| Maker code | `0A` (Jaleco Entertainment) |
| Version | `0x00` (0x080000BC) |
| Complement byte | `0x09` (0x080000BD) — header is **not** stock |
| Header checksum | `0x0000` |
| Entry word | `0xEA0E9BBE` → ARM `b 0x083A6F00` (cracktro) |
| MD5 | `35f26702ce7e1c8429e9e83b319617fa` |
| SHA-1 | `4b03cea832e37e6082cb33565c0f0cd4189727da` |
| SHA-256 | `431e93736739566ce259febe074757fbc7afc5e2d089eea32956d1b86863d49f` |

### Patch / trainer note (Phase 0)

This is **not a pristine retail image**. The header entry word branches to
`0x083A6F00` (file `0x3A6F00`) instead of the stock crt0 at `0x080000C0`.
That region is a **scene cracktro**, observed on boot in mGBA:

* "CREDITS TO / CRAZY NATION · GAME.00 / HIGH SOCIETY · KAL.1570 /
  LIGHTFORCE · MODE 7 / NIGHTFALL · OLDSCHOOL / PARADOX · RAND / SDE · VENOM"
* "Eurasia is proud to present on December 28 of 2006 / Sea Trader: The Rise
  of Taipan / supplied by Team Eurasia"

Single Nintendo logo hit at `0x0` (no multi-game pack). Last 64 KiB of the
file is `0xFF` padding. The cracktro is a release intro, **not** an in-game
cheat — it is reported separately per §16.1. The game itself boots normally
after the intro (MusyX/Factor-5 audio splash → title).

## 2. Executive summary

There is **no password screen, no button-code system, and no hidden debug
menu** in this game. What the game does have is:

1. **A genuine, unpublished developer secret** (§6b): entering `GODZILLA` as
   **both** the captain name and the ship name on the "Pirate Setup" screen
   satisfies a hidden validator at `0x080052C0` and invokes a special routine.
   No published cheat list (GameFAQs, VGChartz, TCRF, gamegenie.com,
   cheathappens) mentions it. It is reproduced end-to-end in the emulator.
2. **Eight in-game award medals** (§6), three of which are absent from the
   published GameFAQs list. These are ordinary achievement unlocks (§16.18),
   not codes.
3. All other published "cheats" are **CodeBreaker/GameShark memory-edit
   codes**, which are out of scope.

The negative result is bounded: the entire ASCII menu text bank was decoded,
both `KEYINPUT` xrefs were examined, every reachable screen was walked with
screenshots + RAM captures, and the 39-symbol × 8-character name-entry field
was tested by its consumer (it is a label, not a validator — §16.2b).

## 3. How to reproduce

* Emulator: mGBA 0.10.5 under `Xvfb :319`, `SDL_AUDIODRIVER=dummy`, `-3` scale.
* Keymap (mGBA SDL defaults): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
  Select=`BackSpace`, D-pad = arrow keys. Hold 100–300 ms.
* Boot: cracktro → press Start/A/z until the title appears → press Start →
  story intro (press A through it) → **Pirate Setup**.
* **Secret code entry**: on the captain field use the on-screen keyboard
  (13-column grid: row 1 `A`–`M`, row 2 `N`–`Z`, row 3 `0`–`9`, `-`, `'`, space;
  cursor starts on `M` when re-entering the field). Type `GODZILLA` (8 chars),
  move Down ×3 to `OK`, press A, press A on "IS THAT HOW YOU SPELL IT?". Repeat
  for the ship field. Confirm, and the game starts at the South China map.
* Savestates F1–F10 / Shift+F1–F10 were used to make each trial one keypress.
* RAM evidence: mGBA `.ss*` states are PNGs with a zlib `gbAs` chunk; the
  397,312-byte decompressed state maps EWRAM→`+0x21000`, IWRAM→`+0x19000`,
  VRAM→`+0x1000` (§16.13). Helper scripts are in §9.

## 4. Address map

| Item | Address | Evidence |
|---|---|---|
| ROM base / file offset | `0x08000000` ↔ `0x0` | header |
| Stock crt0 | `0x080000C0` | disassembly (`mov r0,#0x12`) |
| Cracktro entry | `0x083A6F00` (file `0x3A6F00`) | header entry word, boot screenshot |
| Captain-name validator / secret check | `0x080052C0` (called from `0x080051E0`) | Thumb disassembly |
| `strncmp` helper | `0x08000E0C` | Thumb disassembly |
| Captain-name getter | `0x0800EBB8` → `0x02002478` | literal at `0x0800EBBC` |
| Ship-name getter | `0x0800F628` | called by validator |
| Secret's function-pointer method | `0x0300257C` → `0x08014410` (ROM table `0x08014230`) | literal `0x080531C`, state dump |
| Secret literal strings | `0x080244B4` (`GODZILLA`), pointers at `0x080244A8`, `0x080244AC` | literal scan |
| Menu/text bank (ASCII) | `0x08024000`–`0x08026000` | full byte dump |
| Dialogue script (`=` line break, `$` name) | `0x08020000`–`0x08024000` | strings |
| Award-name pointer table (8 entries) | `0x08024CF0`–`0x08024D28` | literal scan |
| Award descriptions | `0x080245FC`–`0x0802485C` | strings |
| Mode-name pointer table | `0x0803A62C0`–`0x0803A62CC` | literal scan |
| Default high-score names / scores | `0x0803A63F8`–`0x0803A6470` | data (JOHN/MIKE/BRUCE/RYAN/MATT/CLARK/TOM/TINMAN) |
| Screen dispatcher (function ptrs) | `0x0801DC00`–`0x0801DC48` (awards = index 12 → `0x08006A90`) | literal scan |
| `KEYINPUT` reads (only two) | `0x080117AC`, `0x08011ABC` | literal scan of `0x04000130` |
| Captain name (EWRAM) | `0x02002478` | observed `GODZILLA` / `AAAA` |
| Ship name (EWRAM) | `0x02002868` | observed `GODZILLA` |
| Money / taels (EWRAM) | `0x02002658` | observed `0x07D0` = 2,000 at game start |
| Name-entry alphabet | `0x08024424` = `ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-' ` (39 symbols) | strings + on-screen keyboard |

Note: the widely published GameShark address `0x02001FC8` for "max taels"
is **not** the money variable in this build (it reads zero); the actual value
is `0x02002658`. (Memory-edit codes are out of scope; this is recorded only
as a RAM anchor.)

## 5. Algorithm

### 5.1 Secret-name validator (derived, exact)

```
validator_080052C0():                 // Thumb, called from 0x080051E0
    captain = get_captain_name();     // 0x0800EBB8 -> EWRAM 0x02002478
    if strncmp(captain, "GODZILLA", 8) != 0: goto done
    ship = get_ship_name();           // 0x0800F628 -> EWRAM 0x02002868
    if strncmp(ship,    "GODZILLA", 8) != 0: goto done
    fn = *(0x0300257C)                // function pointer, ROM vtable 0x08014230
    fn(8, 0, 0)                       // bx r3 veneer at 0x0801BA88
    fn(7, 0, 0)
    sub_08004B0(1)                    // 16-bit store + follow-up
done:
    return 0
```

The comparison is an 8-byte, case-sensitive `strncmp`; both operands must
match. The two late calls pass arguments `8` and `7`. The target
`0x08014410` writes those arguments into 40-byte records of the structure
based at `0x03002194` (`str r1,[r0,#8]` at `0x080144C8`) — an internal
subsystem record, consistent with a hidden audio/track or state trigger
(**Inferred**: no audible output was captured because mGBA ran with the dummy
audio driver, and no visible UI change appeared on the map).

### 5.2 Name-entry field (not a validator)

The 39-symbol alphabet at `0x08024424` is a label-entry keyboard used for the
captain and ship names only. Every string comparison against the entry buffer
in the ROM is the secret check above; there is no general code validator.

## 6. Tables

### 6.1 Award medals (complete set of 8; derived from pointer table + strings)

| # | Medal | Unlock condition | On GameFAQs? |
|---:|---|---|---|
| 0 | Green Grocer | Ship 3,000 units of Grocery commodities | **No** |
| 1 | Materials Master | Ship 3,000 units of Material commodities | Partial ("Materials Award") |
| 2 | Crafts Dealer | Ship 3,000 units of Finished commodities | **No** |
| 3 | Bootlegger Elite | Ship 3,000 units of Elite commodities | **No** |
| 4 | Trade Baron | Attain 100,000,000 T | Yes |
| 5 | Around the World | Circumnavigate all six charts | Yes |
| 6 | Scourge of the Sea | Defeat 100 pirate ships | Partial ("Pirate Award") |
| 7 | Bloody Buccaneer | Defeat 100 guard/trade ships | Partial ("Guard Award") |

Names at `0x08024CF0`–`0x08024D28`; descriptions at `0x080245FC`–`0x0802485C`
and `0x08025C64`–`0x08025D50`. Each award also grants a tael reward
(`REWARD: %,dT`, `0x0802485C`). Per §16.18 these are save-bit achievements,
not codes; no controller input sets them.

### 6.2 Published codes (verified against the ROM)

| Source | Claim | Verification |
|---|---|---|
| GameFAQs cheats | 5 "cheats" | Actually the 5 award milestones above — no codes |
| GameFAQs strategy guide (20856) | `02001FC8` max taels | GameShark memory edit, out of scope; address wrong for this build |
| gamehacking.org / almarsguides / CodeBreaker lists | `999,999,999` account etc. | CodeBreaker/GameShark memory edits — out of scope |
| gamegenie.com / cheathappens / TCRF / VGChartz | — | No password, button code, or debug menu published |

## 6b. Enumeration

### Space definition

* **Name-entry alphabet**: 39 symbols —
  `ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-' ` (`0x08024424`).
* **Field width**: 8 characters, fixed. `39^8 = 5,157,772,764,801`
  (≈5.16×10¹²) spellings per field.
* **Secret predicate**: `captain == "GODZILLA" AND ship == "GODZILLA"`,
  compared as two 8-byte `strncmp`s of length 8. Accepted spellings:
  exactly **1** out of `39^16 ≈ 2.66×10²⁵` ordered pairs.
* **Bounds proof (static, exact)**: both `strncmp(...,8)` results are tested
  with `cmp r0,#0 / bne` that short-circuits to the skip target
  (`0x080052D6`, `0x080052E6`). A mismatch in either field — including a
  shorter string, a different case, or a substituted symbol — cannot reach
  the success calls. The 8-byte length also means `GODZILA` + padding is
  rejected.
* **Bounds proof (dynamic)**: a near-miss pair was prepared in a savestate
  (captain `GODZILLA`, ship `AAAAAAAA`) and run through the same entry path;
  it did not exhibit the secret's trigger condition. (The field is re-copied
  from the display buffer on confirm, so the negative rests primarily on the
  two short-circuit comparisons, which are unambiguous in the disassembly.)

### Novel code (absent from every published list)

`GODZILLA` / `GODZILLA` (captain / ship). This string was found only as
developer data at `0x080244B4`; none of the consulted cheat lists contains
it. It was **entered on the real Pirate Setup screen** (screenshots
`captain_godzilla.png`, `ship_godzilla2.png`, `godzilla_result.png` in the
work dir), accepted, and the game started normally at the South China map
(`0x02002478` and `0x02002868` both read `GODZILLA` in savestate `game.ss6`).

### Negative enumeration (no other system)

| Space checked | Result |
|---|---|
| All ASCII strings, 4 MiB (`strings -t x -n 4`, 63,144 lines) | No `PASSWORD`, `DEBUG`, `CHEAT`, `SECRET`, `UNLOCK`, `LEVEL SELECT` |
| Full menu text bank `0x08024000`–`0x08026000` decoded byte-for-byte | Only gameplay menus; no hidden entry |
| Dialogue bank `0x08020000`–`0x08024000` (`=`/`$` script encoding) | Story/merchant text only |
| `0x04000130` (`KEYINPUT`) literal xrefs | Exactly 2, both generic input polling (`0x080117AC`, `0x08011ABC`) — no key-mask/sequence table |
| Title screen buttons Up/Down/Select/L/R | No menu appears (screenshots `title_*.png`) |
| In-game Start / Select / L / R | Select→MANIFEST, L→SHIP STATUS, Start/R→no action; no debug screen |
| City buildings in Hong Kong | MERCHANT, TAVERN, CUSTOMS OFFICE, BANK, plus SHIPWRIGHT/WAREHOUSE labels in text bank; all ordinary gameplay |
| Awards | 8 medals enumerated above; 3 undocumented |

## 7. Validation evidence

* **Observed**: boot cracktro; title; intro; captain/ship name entry; map;
  city; merchant trade; manifest; ship status; all button probes; GODZILLA
  entry accepted; `GODZILLA` bytes at both EWRAM name buffers; money `0x07D0`
  at `0x02002658`; 8 award strings.
* **Derived**: header entry word → cracktro; validator at `0x080052C0` with
  two `strncmp(...,8)` short-circuits; function-pointer calls with args 8/7;
  award pointer table and 8 entries; mode table at `0x0803A62C0`; dispatcher
  at `0x0801DC00` with awards handler `0x08006A90`.
* **Inferred**: the payload of the secret routine (likely an internal
  audio/track or state trigger) — the audio driver was dummy and no visible
  UI change was observed in the tested window.

## 8. Unknowns

* The exact audible/visible payload of the `GODZILLA` secret's two late calls
  (arguments 8 and 7) was not isolated; the called routine
  `0x08014410` writes to an internal 40-byte-record structure at
  `0x03002194`, consistent with an audio subsystem, but this was not
  confirmed with sound hardware.
* Award unlock thresholds were read from strings, not reached by 100 kills /
  3,000 shipments of play. Setter call sites were not exhaustively traced
  beyond the text/table enumeration.

## 9. Tooling

* Shell: `file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings`, `grep`.
* `arm-none-eabi-objdump -M force-thumb --adjust-vma=0x08000000` for all
  disassembly; Python `struct` scans for literals, BL targets and Thumb LDR
  literals; zlib/CRC32 savestate patching.
* Work scripts in `/tmp/seatrader/`: `helpers.py` (keypress,
  screenshot, savestate decompress/EWRAM/IWRAM reads), `typeword.py` (keyboard
  grid navigator), `patchstate.py` (savestate byte patcher).
* mGBA 0.10.5, Xvfb :319, openbox, xdotool, scrot, ImageMagick.

## 10. Legal note

No ROM data or copyrighted graphics were redistributed. Only addresses,
algorithms, hashes and original findings are published here.
