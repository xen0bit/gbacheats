# Mega Man Battle Network 5: Team Colonel (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

> **SKIPPED / DEFERRED — entry system found but not in-game confirmed (coordinator decision).**
> Under §0.2 this report does **not** meet the dynamic-confirmation bar: a genuine
> Numberman/Number Trader lotto system was found with 51 published eight-digit codes (algorithmic,
> no ROM literals), and the input reader / scene table / soft-reset gate were reversed, but the
> shop screen is **story-gated behind the first Liberation Mission**, so no code was entered
> in-game, the validator was not located, and no novel code or rejection bounds were produced.
> Per coordinator authorization, MMBN titles whose validator/code-entry surface is blocked by a
> story gate are documented here and **skipped rather than retried or indexed**. The 51 codes
> and the exact gate are recorded below. This report is intentionally left out of the completed-reports table and listed under Skipped ROMs in the top-level `README.md`.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Mega Man Battle Network 5: Team Colonel.gba` |
| Size | 8,388,608 bytes (8 MiB) |
| Header title | `MEGAMAN5_TC_` |
| Game code / maker | `BRKE` / `08` (Capcom), Rev. 00 |
| `file(1)` | `Game Boy Advance ROM image: "MEGAMAN5_TC_" (BRKE08, Rev.00)` |
| Entry word | `0xEA000032` → `0x080000D0` (stock crt0, no cracktro) |
| Fixed byte `0xB2` / complement `0xBD` / checksum | `0x96` / `0x45` / `0x0000` |
| MD5 | `68d79f7c8f41f7c8009f3b85119cb1c6` |
| SHA-1 | `5f472f78d8de2df01d5039e045c043cb40969a39` |
| SHA-256 | `d4b7aefc3918c9f801c84cfd1322c2cdbb9d13c2e3271b3c3f8f9927480f2633` |
| Build tag (ASCII, `0x0803DF80`) | `REXE5TOK 20041006 US` |
| Embedded GBA headers | exactly 1 (at file offset `0x0`) |

**Phase 0 verdict:** stock, single-image retail ROM; no patch, trainer, or appended
data. The `0x0000` header checksum is the usual rebuilt-header artifact; the
complement byte `0x45` is present.

## 2. Executive summary

This ROM has a genuine developer-intended in-game cheat system: the **Number
Trader / Numberman Lotto** machine inside Higsby's chip shop. Entering an
8-decimal-digit code at that machine awards a Battle Chip, Sub Chip, NaviCust
part, or Key Item. A complete published list of **51** codes exists
(The Rockman EXE Zone wiki, corroborated by GameRevolution, IGN, Neoseeker,
SuperCheats); these are listed in §6.

The 51 codes are **not stored literally in the ROM** — exhaustive searches for
each code as ASCII, `+0x20`/`-0x20` shifted bytes, u32 little/big-endian, BCD
(4-byte and nibble-reversed), 16-bit halves, UTF-16, all 256 single-byte XOR/add
keys, and inside all 393 decompressible LZ77 blocks returned **zero** hits. The
award is therefore computed by an algorithm (as in BN3's Number Trader), not by
a plaintext comparison table. Input alphabet is decimal digits `0`–`9`, length
exactly 8, so the theoretical input space is **10^8 = 100,000,000** codes.
Only 51 are published, so unadvertised accepted values plausibly exist (cf. the
BN4 "Z Saver" lotto number found by digging through code, TREZ 2022).

A second published input system exists — button codes (battle-chip slash
sequences and NaviCust "compression" codes, §6), plus the standard GBA
`A+B+Start+Select` soft reset, whose validator was **located and disassembled**
at `0x0800043C` (mask `0x0F` = A|B|Select|Start).

**Honest limitation (see §8):** the Number Trader validator function was not
identified, so no novel 8-digit code could be minted, entered, and RAM-verified,
and the in-game rejection bounds were not exercised. Everything else in this
report is reproducible. The screen is gated behind the first Liberation Mission;
the playable build reached the tutorial (Lan's room → Net → first virus battle)
but not Higsby's shop, so all code-entry claims remain **derived/static**, not
**observed in-game**.

## 3. How to reproduce

* Emulator: `mgba -3 game.gba` on `Xvfb :319`, `SDL_AUDIODRIVER=dummy`.
* Keymap (mGBA SDL default): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
  Select=`BackSpace`, D-pad = arrow keys. Hold 100–250 ms; 40–80 ms double-steps.
* Screen path observed: title (`PRESS START`) → title menu (`NEW GAME`) → intro
  dialog → Lan's room (PET via Start) → kitchen/living room → computer → Net.
* PET menu (RAM-verified, scene state byte at EWRAM `0x0200B160`):
  `Chip Folder`, `Sub Chip`, `Library`, `MegaMan`, `E-Mail`, `Key Item`,
  `Comm`, `Save`, `EXIT`. All top-level entries were opened; none exposes a
  password or code field. `Sub Chip` shows `MiniEnrg/FullEnrg/SneakRun/Untrap/
  LocEnemy/Unlocker`, which are exactly the Sub Chip categories the lotto codes
  award — confirming the shop machine, not the PET, is the entry surface.
* Soft reset: hold `A+B+Start+Select` on any screen → returns to title
  (observed repeatedly; §4).
* Published input: after the first Liberation Mission, enter an 8-digit code at
  the Numberman machine next to the Chip Trader in Higsby's shop (all web
  sources agree on this location).

## 4. Address map

| Address (ROM) | Meaning | Evidence |
|---|---|---|
| `0x08000000` | `b 0x080000D0`, ARM entry (crt0) | Derived (objdump) |
| `0x0800034C` | 17-entry scene-handler pointer table (`{0x0802FFE5, 0x08004C99, …, 0x0813CEFB}`); indexed by the scene byte in the global scene struct | Derived (disasm of main loop `0x08002BC`..`0x0800340`) |
| `0x08002FC` | `bl 0x08003D4` — key read inside main loop | Derived |
| `0x08003D4`–`0x0800437` | Input reader: reads `KEYINPUT` literal `0x08000438` = `0x04000130`; writes active-high held at struct `+0`, pressed at `+2`, held at `+4`, previous at `+6`, 18 hold-counters at `+8..+0x19` | Derived |
| `0x08000438` | Thumb literal `0x04000130` (KEYINPUT) | Derived |
| `0x0800043C`–`0x0800482` | **Soft-reset gate**: `if ((held & 0x0F)==0x0F && (pressed & 0x0F)!=0) { FUN_0800023C(); FUN_08000484(); FUN_0803DABC(); }` — A+B+Select+Start | Derived (objdump + Ghidra pseudocode) + Observed in emulator |
| `0x08000800` | Scene/state setter (`FUN_0814C6B0`) | Derived |
| `0x0800B54`–`0x0800B70` | `u32` decimal powers `10^7 … 10^0` (`0x00989680 … 1`) | Derived (data) |
| `0x0800B74` / `0x0800B78` | `99999999` / `0x99999999` (8-digit input bound / mask) | Derived (data) |
| `0x0803D2C0`–`0x0803D2F0` | Pointer table to debug/SIO format strings: `ID(%D)`, `PL NUM(%D)`, `SIO WAIT`, `SIO OFF`, `SIO ON`, `SIO ERROR`, `SIO ERROR2`, `ST:0x%X`, `RNO:0x%X`, `RECV:%X` | Derived (data) |
| `0x0803DF80` | Build string `REXE5TOK 20041006 US` | Derived |
| `0x0803EBB2`, `0x0803EBCE` | Debug strings `MESS %D`, `MESS %D *` | Derived |
| `0x081BC67C` | `RFU-MBOOT`; `0x081BC688` `NINTENDOSio32ID_030820` (link/multiboot stub) | Derived |
| `0x0803BFD0` / `0x0803BFE6` | Title-scene init / sub-state dispatcher; sub-state table at `0x0803C000` | Derived |
| `0x0803C0A0` | Title sub-state 6: name-entry keyboard handler (codes `0x61`, `0x70`–`0x75`, `0x80`… = ASCII-ish glyph codes), **not** a password field | Derived |

**RAM (savestate-verified, mGBA `.ss1` `gbAs` chunk):**

| GBA address | Value / meaning | Evidence |
|---|---|---|
| `0x0200A440` | Global struct `sl` (GDB r10) | Observed (GDB) |
| `0x0200B160` | `[sl+0]` → scene-state struct; byte `0` = scene index (`0` title, `4` Net/world) | Observed (savestate diff) |
| `0x0200AF50` | `[sl+4]` → input-state struct (same layout as §4 input reader) | Observed |
| `0x03007CFC` | Initial SP | Observed (savestate/GDB) |

Savestate layout for this 8 MiB image: `gbAs` chunk = 397,312 bytes (`0x61000`);
IWRAM at state `0x19000`, EWRAM at state `0x21000` (GBA `0x02000000` ↔ state
`0x21000`), VRAM at `0x1000`.

## 5. Algorithm

### 5.1 Soft reset (fully reversed)

```
held  = ~KEYINPUT & 0x3FF          (input struct +0)
press = held & ~previous           (input struct +2)
if (scene_struct->gatecounter-- <= 1)
    if ((held & 0x0F) == 0x0F && (press & 0x0F) != 0):
        reset_audio(); full_reinit(); clear_input(); gatecounter = 10
```
`0x0F` = A(0x1)|B(0x2)|Select(0x4)|Start(0x8). This is the standard GBA soft
reset, **not** an unlockable cheat.

### 5.2 Number Trader (partially reversed)

* Input: exactly 8 decimal digits at the Higsby's-shop machine.
* The accepted set is algorithmic, not a literal table (§2, §7).
* Space: 100,000,000 possible 8-digit strings; 51 published accepted values.
* A 7-by-10 brute force over linear checksum hypotheses
  `check = (Σ wᵢ·dᵢ + c) mod m` for `m ∈ {7,9,10,11,13,16}` fit at most
  22/51 codes — i.e. the check digit is **not** a simple linear function of the
  digits. Candidate non-linear structures (PRNG/permutation, item-ID hash)
  remain open.
* No generator function was found by PC-relative literal, BL, pointer, or LZ77
  scans; the validator's address is unknown.

## 6. Tables

### 6.1 Published Numberman / Lotto codes (51, GBA + DS-shared)

Source: The Rockman EXE Zone wiki, `Lotto_Numbers_(MMBN5)` (retrieved 2026-11-18;
no embedded instructions/payload). Cross-checked against GameRevolution, IGN,
Neoseeker, SuperCheats and Cheat Index snippets. These are the *in-game codes*
for this title, not GameShark/CodeBreaker values.

| # | Item | Code |
|---:|---|---|
| 1 | Battle Chip AntiElec * | 35607360 |
| 2 | Battle Chip AntiFire * | 73877466 |
| 3 | Battle Chip AntiNavi V | 05068930 |
| 4 | Battle Chip AntiRecv P | 44213168 |
| 5 | Battle Chip AntiSwrd R | 10386794 |
| 6 | Battle Chip AntiWatr * | 25465278 |
| 7 | Battle Chip AntiWood * | 10133670 |
| 8 | NaviCust AttckMAX (Yellow) | 63231870 |
| 9 | NaviCust Beat (Blue) | 79877132 |
| 10 | NaviCust BodyPack (Green) | 30112002 |
| 11 | Battle Chip BugFix * | 50364410 |
| 12 | NaviCust BustPack (Blue) | 80246758 |
| 13 | NaviCust ChargMAX (White) | 87412146 |
| 14 | NaviCust Custom2 (Blue) | 15595587 |
| 15 | Battle Chip CusVolt3 G | 07765623 |
| 16 | Battle Chip DarkInvs * | 68799876 |
| 17 | Battle Chip DjangoSP D | 91098051 |
| 18 | Battle Chip FstGauge * | 83143652 |
| 19 | Sub Chip FullEnrg | 12118790 |
| 20 | Sub Chip FullEnrg | 90914896 |
| 21 | Battle Chip Geddon3 V | 52052687 |
| 22 | Battle Chip GrabRvng P | 68942679 |
| 23 | Battle Chip GunDelS3 O | 35321321 |
| 24 | NaviCust HP+50 (Yellow) | 31084443 |
| 25 | NaviCust HP+200 (Pink) | 90630807 |
| 26 | NaviCust HP+300 (Pink) | 48785625 |
| 27 | NaviCust HP+300 (White) | 13926561 |
| 28 | NaviCust HP+400 (Pink) | 03419893 |
| 29 | NaviCust HP+400 (Yellow) | 45654128 |
| 30 | NaviCust HP+500 (Pink) | 50906652 |
| 31 | NaviCust HP+500 (White) | 72846472 |
| 32 | Sub Chip LocEnemy | 29789661 |
| 33 | Sub Chip LocEnemy | 46551130 |
| 34 | Sub Chip LocEnemy | 52533649 |
| 35 | NaviCust MegFldr2 (Green) | 97513648 |
| 36 | Battle Chip Recov300 Y | 18746897 |
| 37 | NaviCust Rush (Yellow) | 09609807 |
| 38 | Sub Chip SneakRun | 57950199 |
| 39 | Sub Chip SneakRun | 64892292 |
| 40 | NaviCust SoulT+1 (Yellow) | 28256341 |
| 41 | NaviCust SpeedMAX (Pink) | 36695497 |
| 42 | Key Item SpinBlue | 12541883 |
| 43 | Key Item SpinGrn | 78987728 |
| 44 | Key Item SpinRed | 30356451 |
| 45 | Battle Chip Static S | 48958798 |
| 46 | NaviCust Tango (Green) | 54288793 |
| 47 | Sub Chip Unlocker | 28706568 |
| 48 | Sub Chip Unlocker | 64664560 |
| 49 | Sub Chip Unlocker | 73978713 |
| 50 | Sub Chip Untrap | 00798216 |
| 51 | Sub Chip Untrap | 34513460 |

DS-only codes (e.g. `99428938` AreaGrab *, `91182599` DarkRecovery *,
`39285712` ChaosL X, `85375720` TP Chip) were **excluded**: they are documented
as exclusive to *Mega Man Battle Network 5: Double Team* (DS), not this GBA
image. No published code was verified in-game.

### 6.2 Button codes (published, ROM verification incomplete)

From Neoseeker / Cheat Code Central (Team Colonel cheats pages):

* Battle-chip special slashes (enter during/for the named chip):
  `CrossSwrd Slash: Down, Right, Up`;
  `Double LifeSrd Slash: Up, B, Down, B, Up, B`;
  `Super Sonic Boom: Left, B, Right, B`.
* NaviCust compression: enter the Navi Customizer, highlight a NaviCust
  Program, **hold Right** and press the listed button combination to shrink it
  by one block; repeat to decompress.
* Soft reset: `A+B+Start+Select` — **ROM-verified** (§5.1).

Search for the published slash sequences as `u16` active-high key masks
(`D=0x80,R=0x10,U=0x40`; `U,B,D,B,U,B = 40 02 80 02 40 02`;
`L,B,R,B = 20 02 10 02`) and as one byte per press found **no** matching table
in this ROM. They are recorded as unverified rather than asserted.

### 6.3 Input state struct (GBA `0x0200AF50`)

| Offset | Width | Meaning |
|---:|---:|---|
| `+0` | u16 | held keys, active-high (`A=1,B=2,Sel=4,Start=8,R=0x10,L=0x20,U=0x40,D=0x80,Rtr=0x100,Ltr=0x200`) |
| `+2` | u16 | newly pressed this frame |
| `+4` | u16 | held across two frames |
| `+6` | u16 | previous held |
| `+8..+0x19` | 18 bytes | per-key hold counters (saturate at 16) |

## 7. Validation evidence

**Observed (emulator / GDB / savestate):**
* Title, PET menu, Chip Folder (30/30 chips, Cannon/AirShot), Library, Sub Chip
  (MiniEnrg/FullEnrg/SneakRun/Untrap/LocEnemy/Unlocker lists), MegaMan status,
  Lan's room, kitchen, living room, Net, first virus encounter, title menu.
* `A+B+Start+Select` returns to title; repeated from multiple screens.
* GDB r10 = `0x0200A440`; `[r10] = 0x0200B160`; scene byte = `0` (title) / `4`
  (Net). GDB breakpoint at `0x080002FC` hit with `lr = 0x080008E3`.
* All 51 published codes absent from the ROM under every encoding tried.

**Derived (disassembly / Ghidra decompiler):**
* Input reader at `0x08003D4`, soft-reset gate at `0x0800043C`, scene table at
  `0x0800034C`, title-scene dispatcher at `0x0803BFE6`, debug/SIO string table
  at `0x0803D2C0`.
* Scene 8's sub-state 6 (`0x0803C0A0`) handles **name entry**, not a password.

**Inferred:**
* The Number Trader award is algorithmic (strong: no literal table exists in
  the ROM under any searched encoding, and the sibling BN titles use the same
  algorithmic Number Trader).
* Unadvertised accepted 8-digit codes probably exist, by analogy with BN4's
  discovered Z Saver code. Not proven.

**Prompt-injection note:** fetched web pages were treated as data. The TREZ
wiki page and Brave result snippets contained no embedded instructions; no
"decode key", payment request, or tool directive was followed. GameFAQs,
Neoseeker, TCRF and IGN direct fetches returned 403 and were not used.

## 8. Unknowns

1. **Validator address and algorithm for the Number Trader** — not located.
   The entry screen is gated behind the first Liberation Mission and was not
   reached; no code was entered in-game.
2. **No novel code generated / no in-game success or rejection proof** — the
   mandatory §0.2 enumeration deliverable is therefore *not* satisfied for
   this engagement. This is stated explicitly rather than claimed as tested.
3. Button-code tables for the slash/compression sequences were not found; the
   published sequences remain unverified against this ROM.
4. Whether the debug/SIO strings at `0x0803D2C0` are reachable via any input
   (no code reference to the table was found by 2- or 4-aligned pointer scans,
   suggesting dead debug code).
5. Decoded font/tile text bank: not exhaustively dumped. This does **not**
   underpin a negative conclusion here — a positive system (Number Trader) was
   found by other means.

## 9. Tooling

* `file`, `md5sum`, `sha1sum`, `sha256sum`, `strings -t x`, `xxd`, `grep -abo`
  for Phase 0/1.
* `arm-none-eabi-objdump -M force-thumb/-M force-arm` and Capstone 5.0.7 for
  disassembly; `keystone-engine` installed.
* Ghidra 12.1.4 via `reverse-engineer-anything` MCP (`open_binary`,
  `procedure_pseudo_code`, `binary_overview`, `list_strings`) — note the shared
  REA session was switched to another ROM by a concurrent agent mid-run, so
  REA results were cross-checked with objdump.
* `mgba` SDL under `Xvfb :319` + `openbox`; `xdotool` XTEST input; `scrot`/
  `import -window <id>` capture; ImageMagick `montage` for contact sheets.
* `gdb-multiarch` against mGBA's GDB stub on port 2345 (breakpoint at
  `0x080002FC` worked; `interrupt` did not, so breakpoints were used to halt).
* Custom scripts in `/tmp/mmbn5colonel/`: `press.py` (keymap helper),
  `ss.py` (mGBA `gbAs` savestate RAM reader), `scan.py`, `dis.py`, `lzscan.py`
  (GBA LZ77 decompressor + code search), `brute`/`brute2` (checksum search),
  `scenes.py` (savestate scene-byte patcher).

## 10. Legal note

No ROM bytes, graphics, audio, or extracted game assets are reproduced here.
Only hashes, addresses, algorithms, and our own observations are published.
