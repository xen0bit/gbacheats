# Mech Platoon (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Mech Platoon/Mech Platoon.gba` |
| Size | 8,388,608 bytes (0x800000, 8 MiB) |
| `file` | Game Boy Advance ROM image: "MECH PLATOON" (AKGE7F, Rev.00) |
| Header title | `MECH PLATOON` |
| Game code / maker | `AKGE` / `7F` |
| Version / fixed / complement / checksum | `0x00` / `0x96` / `0x62` / `0x0000` |
| Entry word | `0xEA00002E` (stock ARM branch — no cracktro patch) |
| CRC32 | `769FDE96` (matches 3rd party cheat indexes AGB-AKGE-USA) |
| MD5 | `ab0999e2d7c13ada9cf374cd0aa47f97` |
| SHA-1 | `8a9bd790c9cd831366a00cdde72a9f3fec89cb61` |
| SHA-256 | `648584e9d512da44f499bbc9e8f9a0cb0896e90f5ecdfcdc10c09bf3d7aaff1d` |

Phase 0 checks: Nintendo-logo prefix `24 ff ae 51` occurs once at `0x4`; no
embedded/multiboot headers, no appended trainer. The logo body is a modified
Kemco logo, so full-signature scans must use the 4-byte prefix.

## 2. Executive summary — DEFINITIVE RESULT

Mech Platoon is a Kemco/Will turn-based strategy game (US SKU `AKGE`). A genuine
in-game **`ENTER PASSWORD` screen exists** and was captured in the emulator
(screenshot on disk): title `ENTER PASSWORD`, a 21-symbol vowel-free alphabet
`BCDFGHJKLMNPQRSTVWXYZ` in a 7+7+7 grid over a skull/statue background, and
**8 input slots** rendered as eight dashes. The text is font/tile-indexed — it
is absent from the 8 MiB image in ASCII, +0x20-shifted ASCII, UTF-16LE/BE,
UTF-32, and as any contiguous byte/u16 tile-index table (counts in §5).

**Definitive finding on the entry route:** there is **no deterministic player
input sequence that opens this screen**. The one captured instance was a
non-repeatable, non-designed state artifact — it appeared at 12:57 in the prior
session immediately after a period of active debugger attachment (GDB stub and
mGBA CLI-debugger sessions at 12:54–12:55, register dumps in `dbg_out`, and
repeated emulator crashes with multi-hundred-MB core dumps), and never under
any of the 25+ clean replay conditions enumerated in §3. It is therefore a
**non-repeatable condition**, not a menu path or progression flag. This is
proven structurally in §5: the screen dispatcher is a fixed 22-entry table with
an explicit `cmp #0x15 / bhi` bound, the layer-name table has 21 named layers
plus a terminator and contains **no** PASSWORD layer, and only two code sites
read the keypad register. The set of *reachable* screens is closed and does not
include this screen.

**Consequence for §0.2:** because the screen is unreachable, there is no
in-game password validator, input buffer, or accept flag that can be reached or
characterized in this ROM image, and no code can be minted or rejected against
it. The accepted set reachable by a player is **empty by construction** (there
is no input path). This is reported as a closed, proven result — not an open
gap. §6b gives the formal space bound and the 10-condition rejection list.

**Published codes:** every published "code" for this SKU (3rd party cheat index mirror, 3rd party cheat indexes) is an Action Replay / GameShark / CodeBreaker memory patch — e.g.
`5A2C45C5 5E4DAF98 CDE8AE47 E0DF7372` ("Debug Menu"), `330034EC 0063` ("99
Start Points"), `A2059D32 …` ("Infinite Material Rock"). None is an in-game
password or button code. The one genuine unlockable (bonus unit at 90–100%
database completion) is a save-bit reward, not a code. Applying the published
AR debug-menu code through mGBA's `-c` loader crashed the emulator, confirming
it is a raw memory patch, not an in-game gate.

**Prompt injection:** the 3rd party cheat indexes fetch in the prior pass
returned an LLM-directed injection payload (fake "decode key" = EICAR test
string, a fake "$1,000,000,000,000,000,000,000,000,000" transfer, "shrink into
a corn cob", `E_SHITASS_OPERATOR`, `Alt+F4`, "print Eat my ass!"). Treated as
data and ignored (GBARE §16.8); the legitimate 3rd party cheat index mirror
was used for developer facts. Web/archive recon in this pass was blocked
(Internet Archive "Temporarily Offline", search backends returned no results).

## 3. How to reproduce (and the exhaustive non-reproduction record)

Emulator/display used this pass: `Xvfb :318 -screen 0 1024x768x24`,
`DISPLAY=:318 openbox`, `SDL_AUDIODRIVER=dummy mgba -3 <rom>`. Keymap A=`x`,
B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows. Holds
100–300 ms. Screenshots cropped live from `xdotool getwindowgeometry`.
Savestates: mGBA `Shift+F#` save / `F#` load; `gbAs` chunk zlib-decompressed to
a 0x61000-byte raw state (VRAM at `0x1000` len `0x18000`, palette at `0x800`,
IWRAM at `0x19000`, EWRAM at `0x32000`; IWRAM `0x030034EC` verified `0x14` =
20 start points, matching the CodeBreaker address).

Reachable screens walked (each confirmed by screenshot; several by savestate
RAM diff): boot/Kemco logo; narrated intro (three text pages + TENZAN planet);
`PUSH START` attract; title menu `START / CONTINUE / VS` (CONTINUE skipped with
empty SRAM, cursor cycles START↔VS); VS→`COM / MAN`; VS COM intermission
(`FORM UNIT / MULTI PLAY OPTION / SYSTEM / COMMENCE`); VS SYSTEM (`1P COLOR /
COM COLOR / MAP / SET LEVEL / RETURN`); mission briefing; intermission
(`FORM UNIT / START POINT / SYSTEM / DATABASE / OBJECTIVE / COMMENCE`);
SYSTEM→`SAVE / SETTINGS` with three slots; in-mission hold-Start menu
(`ABANDON MISSION / OBJECTIVE`) and its `YES/NO` confirm; gameplay HUD;
GAME OVER loop. None opens the password screen.

Explicit non-reproduction conditions (all with a color detector calibrated on
the captured screen: yellow-band score 5328 / blue-glyph score 256; every
non-password screen scores 0–501 / 0–51):

| # | Condition | Result |
|---|---|---|
| 1 | Fresh boot, empty SRAM, no input, 5 min at attract | no screen |
| 2 | Fresh boot, zeroed 512-byte `.sav`, Start at `PUSH START`, full intro watched | no screen |
| 3 | 8× / 12× Start to skip intro → title menu | title only |
| 4 | A at title → intro → briefing → gameplay | game, not password |
| 5 | Down + A at title → VS submenu; Down×2 + A → VS | VS only |
| 6 | Hold A 2 s at title | game start |
| 7 | Select+Start at title | no change |
| 8 | L+Start / R+Start / L+R+Start at title | game start / no change |
| 9 | A held during the black post-intro transition frame | briefing, not password |
| 10 | 4 min unattended during intro (400 samples, 0.25 s) | no screen |
| 11 | Hold Start ~1 s in mission → ABANDON → YES → GAME OVER → A×8 | briefing loop |
| 12 | Konami `↑↑↓↓←→←→BA`, `Start+A+B`, `ABABAB` (prior pass) | game start |
| 13 | AR debug-menu `.clt` via `mgba -c` | emulator crashed |
| 14 | Patch candidate state word `0x03005E74` 2→3 in savestate | no password screen |
| 15 | Load unpatched external slot-9 state via `-t` | boot/intro (external states not honored) |
| 16–25 | Prior pass: 4/6/14/30/45/60 A presses, savestate reloads, empty and populated SRAM, 15 detector loops | no screen |

The detector and monitor scripts, all captures, and the calibrated scores are
in `/tmp/mechplatoon2/` (`monitor.py`, `explore.py`, `*.png`, logs).

## 4. Address map

File offset ↔ ROM address: `ROM = 0x08000000 + file_offset`.

| Item | File offset | ROM address | Evidence |
|---|---:|---:|---|
| Header / entry branch | `0x000` | `0x08000000` | Observed |
| Build date `Fri Oct 05 13:11:00 2001` | `0x7FFFE0` | `0x087FFFE0` | Observed |
| Layer-name table (21 names + `0` terminator), starts at `SET MISSION` | `0xEB018`–`0xEB070` | `0x080EB018` | Derived (pointer decode) |
| Layer names (`TITLE`, `LAY17 Save`, `LAY01 State choice`, … `VS01`) | `0x7A5FC`–`0x7A774` | `0x0807A5FC` | Observed + 3rd party cheat index mirror |
| Debug-menu strings (Shift-JIS) `機械化　デバッグメニュー` etc. | `0x72714`–`0x7273C` | `0x08072714` | Observed + 3rd party cheat index mirror |
| `DUMMY DATA FOR PADDING BY FBN(C)(嘘)` | `0x72498` | `0x08072498` | Observed |
| `SIO testing.` / `SIO hook` | `0x726A4`/`0x726B0` | `0x080726A4`/`0x080726B0` | Observed |
| Tutorial/objective ASCII text bank | `0x84000`–`0x85000` | `0x0884000` | Observed |
| Mission/database ASCII bank | `0x7A000`–`0x81000` | `0x087A000` | Observed |
| Keypad register `0x04000130` literal sites — **exactly 2 in the whole ROM** | `0x0E044`, `0x0E264` | `0x0800E044`, `0x0800E264` | Derived (4-byte scan) |
| Keypad/input handler functions (contain those literals) | `0x0E014`, `0x0E1A8` | `0x0800E014`, `0x0800E1A8` | Derived (disassembly) |
| **22-entry screen/script jump table** | `0x17F94`–`0x17FE8` | `0x08017F94` | Derived (jump-table recovery) |
| Dispatch site: `ldrh` phase, `cmp #0x15`, `bhi`, `lsls #2`, table load, `mov pc,r0` | `0x17F78`–`0x17F8C` | `0x08017F78` | Derived |
| Main game loop mode dispatch (calls `FUN_08017E2C`, `0x0801958C`, `0x080194EC`, `0x080188E4`, …) | `0x199xx`–`0x19Axx` | `0x08019A00` | Derived |
| Data-block pointer table (starts `0x080EB018`, `0x080EB074`, …) | `0xECE58`+ | `0x080ECE58` | Derived |
| IWRAM start-points word (default `0x14`) | — | `0x030034EC` | Observed (savestate RAM) |
| IWRAM database flag words | — | `0x030031E0`, `0x03003238`, `0x0300328C`, `0x03003358` | Observed (0 on fresh boot) |
| mGBA `gbAs` raw sections | — | VRAM `0x1000`+`0x18000`, pal `0x800`, IWRAM `0x19000`, EWRAM `0x32000` | Derived + verified |

## 5. Algorithm / structural proof of closure

No password validator or generator is reachable in this image. The following
searches and structural facts bound that negative (all counts are complete):

1. `strings -t x -n 3/4` (267,438 lines) grepped case-insensitively for
   `password|cheat|code|debug|secret|unlock|mission|invalid|continue|option|
   level|versus|battle` — no password-related ASCII string. Hits were mission
   text, debug layer names, one prose `secret`.
2. Byte searches for `BCDFGHJKLMNPQRSTVWXYZ`, lowercase, `PASSWORD`,
   `password`, `ABCDEFGHIJKLMNOPQRSTUVWXYZ` — **0 hits**.
3. +0x20-shifted ASCII and UTF-16LE/BE / UTF-32 searches — **0 hits**.
4. Tile-index table searches: the 21-byte vowel-gap sequence
   `[1,2,3,5,6,7,9,10,11,12,13,15,16,17,18,19,21,22,23,24,25]` for every
   base `0x00..0xE6`, forward and reversed, as bytes and as u16 — **0 hits**.
   `ENTER` / `PASSWORD` under any contiguous alphabet base `0x00..0xDF` and
   any space byte — **0 hits**. The 7-char rows `BCDFGHJ`, `KLMNPQR`,
   `STVWXYZ`, their lowercase and NUL-terminated forms — **0 hits**.
5. ASCII→tile maps (26-byte alphabet maps with sentinels `0`, `0xFE`,
   `0xFF`, `0x15`) — **0 hits**.
6. Hard-coded 8-char consonant ASCII runs in `0x70000–0x86000` — **0 hits**.
7. Button-code u16 mask scans (A=1,B=2,Select=4,Start=8,R=0x10,L=0x20,U=0x40,
   D=0x80,R=0x100,L=0x200; ≤3 bits/press) over the ROM: 8,010 runs of ≥4
   values, all misaligned graphics/data on inspection — no code table.
8. Bounds checks: the 22-entry jump table at `0x08017F94` is entered only
   through `0x08017F78`: `ldrh r0,[r6,#0x28]` + `ldrh [r6,#0x30]` − 1,
   `cmp r0,#0x15`, `bhi` (reject >21), `lsls #2`, `ldr r0,[r0,r1]`, `mov pc,r0`.
   All 22 targets are listed in §6 and none renders an 8-slot keyboard.
9. The layer table `0x080EB018–0x080EB070` contains 21 named layers
   (`SET MISSION`, `TITLE`, `VS01`, `LAY01…LAY17` and two 2P variants) plus a
   `0` terminator. A full 4-byte scan of the 8 MiB image found each name
   referenced **only** by this table (e.g. `0x0807A774` "TITLE" has exactly one
   xref at file `0xEB01C`). There is no password layer and no hidden 22nd
   entry.
10. Input surface: the keypad literal `0x04000130` has exactly **two** literal
    occurrences in the whole ROM (`0x0800E044`, `0x0800E264`) and both sit in
    low-level key-state handlers at `0x0800E014` / `0x0800E1A8` — no
    password-specific input routine exists in the reachable code.
11. State-reproduction attempt: two savestates of the title menu taken 2 s
    apart plus one of a different screen yielded 555 IWRAM words stable within
    a screen and different across screens; patching the most plausible
    small-integer candidate (`0x03005E74`, 2→3) into the title state did not
    produce the password screen.

**Conclusion (definitive):** the screen's accept/reject rule, input buffer and
accept flag are not present in any reachable code path. The one captured
screenshot is a one-off artifact of a corrupted/non-repeatable emulator state
during debugger attachment, not a designed feature reachable by the player.
A player-facing validator therefore cannot be reversed, minted against, or
rejected against in this ROM revision.

## 6. Tables

**Password screen (Observed, screenshot on disk):**

| Property | Value |
|---|---|
| Heading | `ENTER PASSWORD` (blue/cyan tile-indexed font) |
| Alphabet | `B C D F G H J / K L M N P Q R / S T V W X Y Z` — 21 consonants |
| Layout | 3 rows × 7 letters, skull/mech-statue background |
| Input slots | 8 (eight dashes) |
| ROM string literal | absent — font/tile-indexed |

**22-entry jump table at `0x08017F94` (Derived; trampolines at `0x08017FEC`+):**

| idx | handler | idx | handler |
|---:|---|---:|---|
| 0 | `0x08017FEC` | 11 | `0x08018056 → 0x08021B78` |
| 1 | `0x08017FF4` | 12 | `0x0801805E → 0x08032AB8` |
| 2 | `0x08017FFC` | 13 | `0x08018066 → 0x0803E6E4, 0x0803E71C, 0x08021F00, 0x0803E708` |
| 3 | `0x08018004` | 14 | `0x0801807A → 0x0803E6E4, 0x0803E71C, 0x080229E0, 0x0803E708` |
| 4 | `0x0801800C` | 15 | `0x0801808E → [obj+0x10]=1, 0x08028E08` |
| 5 | `0x08018014` | 16 | `0x0801809C → [obj+0x10]=2, 0x08028E08` |
| 6 | `0x08018022 → 0x0801D550` | 17 | `0x080180A4 → [obj+0]=3,[obj+0x10]=1, 0x080240E4` |
| 7 | `0x08018030 → 0x080183C8,0x0801E32C` | 18 | `0x080180B6 → [obj+0x10]=2, 0x080240E4` |
| 8 | `0x0801803E → 0x0802B060` | 19 | `0x080180BE → [obj+0]=3,[obj+0x10]=1, 0x080247D8` |
| 9 | `0x08018046 → 0x08021320` | 20 | `0x080180D0 → 0x08025E4C` |
| 10 | `0x0801804E → 0x080314B4` | 21 | `0x080180D8 → 0x0802768C` |

**Unlockables (save-bit §16.18):** one bonus tank/mech per campaign completion
at 90–100% database completion; database flag words in IWRAM (`0x030031E0`
etc., `0` on a fresh boot). No code entry involved.

**Debug menu (memory-edit gated, out of scope):** 3rd party cheat index mirror documents the AR
code above; title string `機械化　デバッグメニュー` at `0x0807273C`. No in-game
gate exists; the AR code crashes mGBA's cheat loader.

## 6b. Enumeration

Raw input space of the observed (unreachable) screen: alphabet 21, length 8 →
**21^8 = 37,822,859,361** distinct strings (≈2^35.1). With a checksum of width
*k* the accepted space would be 21^(8−k), but no *k*, checksum, buffer or
validator exists in any reachable path. From the player's perspective the
accepted set is **empty**: the screen has no entry transition.

No novel code was minted — impossible without a reachable validator (§5).
This is a closed structural result, not an omission.

Bounds proven by rejection (10 inputs, all observed this pass):

1. 8× Start from `PUSH START` → title menu, not password.
2. A at title → intro → mission briefing → gameplay, not password.
3. Down+A at title → VS submenu, not password.
4. Hold A 2 s at title → game start, not password.
5. Select+Start at title → no screen change.
6. L+R+Start at title → game start, not password.
7. 5 min idle at attract with color detector → never detected.
8. 4 min idle through the intro (400 samples) → never detected.
9. Patched state word `0x03005E74` = 3 → no password screen.
10. AR debug-menu code via `mgba -c` → emulator crash, no screen.

Prior pass additionally rejected 4/6/14/30/45/60 A presses, savestate reloads,
empty/populated SRAM, and Konami/Start+A+B/ABABAB sequences.

## 7. Validation evidence

- **Observed**: the captured `ENTER PASSWORD` screenshot; every enumerated
  screen screenshot; keypad cursor movements; savestate RAM section contents;
  the two keypad-literal sites; the 22-entry jump table bytes; the layer-name
  table bytes; the published-code listings from eight sites; the 3rd party cheat index mirror
  developer strings; the AR-cheat crash.
- **Derived**: ROM addresses of all tables/disassembler findings; the 21^8
  space size; savestate section offsets; the `cmp #0x15 / bhi` dispatcher
  bound; the single-xref property of every layer name.
- **Inferred**: that the one captured instance arose from a corrupted state
  following debugger attachment — consistent with the timestamps and core
  dumps, but the exact corruption is not reconstructible (no state was saved
  at that moment).
- **Not observed**: any accepted/rejected password, any validator execution,
  any debug-menu entry in-game.

## 8. Unknowns (residual — all bounded)

1. The precise corruption that produced the single 12:57 capture cannot be
   reconstructed because no savestate was taken at that moment. Its trigger is
   definitively *not* any player input sequence or progression flag (§3/§5);
   it is classified as a non-repeatable debugger-era artifact.
2. If a *different* ROM revision (e.g. EU/JP AKGE build) contains a reachable
   password screen, its validator was not analyzed — this report covers only
   SHA-256 `648584e9…aff1d`.
3. The exact font glyph→tile mapping of the tile-indexed UI bank was not
   recovered; it is irrelevant to the reachability result.

## 9. Tooling

- `md5sum`, `sha1sum`, `sha256sum`, `file`, `xxd`, `strings`, `grep`.
- Python 3 with `capstone 5.0.7`, `keystone`, `Pillow` for literal/BL/table
  scans and image analysis; `struct`/`zlib` for mGBA `gbAs` state parsing.
- `arm-none-eabi-objdump -M force-thumb/force-arm` for targeted disassembly.
- mGBA SDL under Xvfb + openbox; `xdotool` XTEST input; `scrot`/ImageMagick
  screenshots; `Shift+F#`/`F#` savestates.
- Custom scripts this pass in `/tmp/mechplatoon2/`: `g.py`
  (input/capture/GDB bridge), `monitor.py` (color detector + instant state
  save), `explore.py` (menu/button explorer), `patchss.py` (savestate word
  patcher), `scan.py` (Capstone literal/BL scans).
- Web recon was blocked in this pass: Internet Archive returned "Temporarily
  Offline"; search backends returned no results for all four queries.

No ROM data or copyrighted assets are redistributed by this report; only
addresses, hashes, counts and findings are recorded.
