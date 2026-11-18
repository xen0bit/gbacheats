# Mat Hoffman's Pro BMX 2 (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Mat Hoffman's Pro BMX 2.gba` |
| Size | 8,388,608 bytes (0x800000) |
| Header title | `MH PRO2 AGB` |
| Game code | `AH2E` (internal 6-char `AH2E52`) |
| Maker | `52` |
| Version | 0x00 (Rev.00, US) |
| MD5 | `c786f824ed894f22166d4eb801f5f7d4` |
| SHA-1 | `d12bc188404bfb6d012b9ce1cf7302762d934832` |
| SHA-256 | `793ac39fa49bd966d1cbce0e421dbe3de557911b4131286ada6363520ba51ea4` |

**Phase 0 result — clean retail image, no patch/trainer.**
Entry word is `0xEA00002E` (stock `b 0x080000C0`); the first 4 KiB are a normal
crt0 (`mov r1,#0x12; swi 0x29; ldr sp,=0x03007F00; ...`). A 156-byte Nintendo-logo
scan over the whole file found **exactly one** header (file `0x0`, ROM `0x08000000`)
— no multiboot stub, no appended trainer, no second game image.
Header checksum is `0x0000` and complement byte `0x28`, both normal for this build.

## 2. Executive summary

**No developer-intended cheat system (password, on-screen code entry, button-code
sequence, or hidden debug menu) exists in this ROM.** This is a *proven negative*,
not an untested one: every reachable screen was walked in mGBA with screenshots and
savestate/RAM evidence; the only text bank was decoded (the game stores all UI text
as lowercase ASCII with `/` terminators and the font renders uppercase, so `strings`
does show it); the input subsystem was disassembled and the button space was
searched with counts; and six candidate title-screen button sequences were entered
with no state change.

The one code-like data bank in the image (`0x0807F87C`) contains the string
`HGXFP101FLIPPERDIPPERHGX`, fifteen 3-letter codes, and rider names. It **is** used
by the game — it supplies the default high-score initials shown on the Hall of Fame
boards (Oklahoma: `REE 600000`, `JAR 400000`, `STR 200000`, `NRL 100000`, `CIB 50000`
= table entries 4..0 reversed). It is **not** a validator or a cheat table: there are
zero code references to the marker/codes/name strings, no alphabet, no input buffer,
and no comparison loop. Two names in it (`dennis mccoy`, `c.kagy`) are anomalous
relative to the 11-rider selectable roster, but they are labels in that bank, not
unlockable riders — no input path writes the state that would select them.

Progression unlocks in this title (locations/tutorial rounds, "locked", "amateur"/
"semi-pro"/"pro") are **EEPROM save-bit progression**, not codes (guide §16.18).

## 3. How to reproduce

* Emulator: `mGBA` (SDL), `SDL_AUDIODRIVER=dummy`, `Xvfb :315`, `openbox` on :315.
  Keymap used: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`,
  D-pad=arrow keys. Key holds of 50–120 ms (longer holds double-step some menus).
* Boot: title `PRESS START` → main tabs `OPTIONS | SESSIONS | HALL OF FAME`.
  * `OPTIONS → GAME OPTIONS`: MUSIC VOLUME, SOUND FX VOLUME, SCORE DISPLAY ON/OFF,
    MANUALS: OPPOSITES, CREDITS, RESTORE DEFAULTS.
  * `OPTIONS → MEMORY`: SAVE GAME, LOAD GAME (creates a 512-byte `.sav`).
  * `HALL OF FAME`: CLEAR ALL RECORDS, VIEW RECORDS → HIGHEST SESSION SCORES /
    HIGHEST COMBO SCORES / LONGEST COMBO → 8 cities (Oklahoma, Las Vegas, Chicago,
    New Orleans, Los Angeles, Portland, Boston, Hawaii) → 5-entry score board.
  * `SESSIONS`: ROAD TRIP (START NEW / LOAD SAVED, with `ARE YOU SURE? YES/NO`),
    SINGLE SESSION → RIDER SELECT → LOCATION SELECT → play → `PAUSED` (Continue /
    Retry / End Run), FREE RIDE, MULTI PLAYER (HOT SEAT / LINK).
  * `RIDER SELECT` also has `R = BIOS`.
* No screen has a password/name-entry field. No menu has an unlabelled extra entry.
* Button sequences tried on the title screen (each from a saved state, all rejected:
  still `PRESS START`, no new screen or RAM flag):
  `↑↑↓↓←→←→BA`, `L R L R A B`, `L+R+Start`, `B A B A B A`,
  `↑↑↓↓←→←→`, `Select A Select B`, `L L R R ↑ ↓ A B`.
* Web verification attempt: `websearch` returned no results for all queries;
  GameFAQs/TCRF/IGN returned HTTP 403, `r.jina.ai` was blocked or returned site
  homepages, and the Wayback CDX API returned empty sets. No published GBA code
  literal was obtained, so there is no external list to verify against the ROM.
  No prompt-injection payload appeared in any fetched page.

## 4. Address map

| Address | Meaning | Evidence |
|---|---|---|
| `0x08000000` | GBA header, single image, stock entry `0xEA00002E` | Derived (logo scan, disasm) |
| `0x080060DC` | Input update + replay-history recorder (Thumb) | Derived (objdump) |
| `0x080061C4` (pool `0x03002818`) | raw key-state copy (active-low, 16-bit) | Derived |
| `0x080061D8` (pool `0x03000370`) | newly-pressed active-high mask | Derived |
| `0x080061DC` (pool `0x03000388`) | held active-high mask | Derived |
| `0x080061D0` (pool `0x03000374`) | replay mode: 0=off, 1=record, 2=playback | Derived |
| `0x080063E8` | replay-history flush (called at history full) | Derived |
| `0x0806354 / 0x0806398` | start record / start playback (11 / 1 BL callers) | Derived (BL scan) |
| `0x0807F87C` | `HGXFP101FLIPPERDIPPERHGX\0` (24 bytes) | Observed (ROM bytes) |
| `0x0807F898` | 15 default score initials, NUL-terminated at 4-byte stride | Observed + in-game |
| `0x0807F8D8` | 8 long rider names, 16-byte stride | Observed |
| `0x0807F958` | 11 short rider names, 12-byte stride | Observed |
| `0x0807F9DC` onward | PCM-ish sound sample data (not stats) | Observed |
| `0x7EFB58–0x7F3520` | UI text bank; lowercase ASCII, `/` terminator | Observed (decoded) |
| `0x0807F0090` / `0x0807F00EC` | 11 first names / 11 last names of selectable riders | Observed |
| `0x03000370` etc. | input/replay RAM globals (see above) | Derived |
| `0x03000399` | candidate rider index (02→01 when selection changes) | Observed (savestate diff) |
| `.sav` (512 B) | EEPROM; magic `69 32 12 12 BE EF DE AD` at +0; u32 scores from ~+0x12C | Observed |

Savestate layout for this mGBA build: `.ss1` is PNG + zlib `gbAs` chunk, raw state
`0x61000` bytes; IWRAM at raw `0x19000` → `0x03000000`, EWRAM at raw `0x21000` →
`0x02000000`. Verified by cross-reading the same addresses with mGBA's `-d` debugger
`r/4` command on a loaded state.

## 5. Algorithm

No password validator exists to reimplement. The only "algorithm" found is the
input-state mapping in `0x080060DC`:

```
raw = ~KEYINPUT & 0xFFFF                 # active-high
pressed = raw & ~held_prev
held_prev = raw
internal = 0
if raw & 0x40: internal |= 0x01   # Up
if raw & 0x80: internal |= 0x02   # Down
if raw & 0x20: internal |= 0x04   # Left
if raw & 0x10: internal |= 0x08   # Right
if raw & 0x01: internal |= 0x10   # A
if raw & 0x02: internal |= 0x20   # B
if raw & 0x200: internal |= 0x40  # L
if raw & 0x100: internal |= 0x80  # R
store internal; if mode==1 and internal changed:
    append {old,internal} to replay history; when full -> flush (0x080063E8)
```

This is a **demo/replay recorder**, not a cheat matcher: its mode/idx/pointer globals
(`0x03000374..0x03000388`) have code references only inside `0x08006000–0x08006600`,
and its start functions are called from 11 places as a replay feature (the pause
menu offers replay viewing). No branch compares the history against a constant.

## 6. Tables

**Default high-score initials at `0x0807F898`** (4-byte stride, NUL-terminated),
in ROM order: `cib, nrl, str, jar, ree, kof, nik, tom, jon, rob, ves, eli, nit, nfi, byi`.
Display order on the Oklahoma board is reversed for the top five (`ree, jar, str,
nrl, cib` with scores `600000, 400000, 200000, 100000, 50000`) — confirmed on screen.

**Rider name bank** at `0x0807F8D8` (16-byte stride): `simon tabron`, `kevin robinson`,
`dennis mccoy`, `rick thorne`, `joe kowalski`, `cory nastazio`, `mike escamilla`,
`mat hoffman`. At `0x0807F958` (12-byte stride): `s.kimbrough`, `n.wessel`,
`r.alcantara`, `c.kagy`, `s.tabron`, `k.robinson`, `r.thorne`, `j.kowalski`,
`c.nastazio`, `m.escamilla`, `m.hoffman`. The selectable roster is instead built from
the 11 first names + 11 last names at `0x7F0090`/`0x7F00EC` (Seth Kimbrough, Nate
Wessel, Ruben Alcantara, Day Smith, Simon Tabron, Kevin Robinson, Rick Thorne, Joe
Kowalski, Cory Nastazio, Mike Escamilla, Mat Hoffman). The `c.kagy` / `dennis mccoy`
labels are therefore not roster entries.

**Internal button masks:** UP=01, DOWN=02, LEFT=04, RIGHT=08, A=10, B=20, L=40, R=80.

## 6b. Enumeration

Per guide §0.2, a negative result is bounded by characterising the searched space:

1. **Screen space (walked, 15+ screens, RAM/savestate backed):** title; main tabs
   OPTIONS / SESSIONS / HALL OF FAME; GAME OPTIONS (6 entries); MEMORY (2 entries);
   HALL OF FAME (2 entries) → 3 record categories → 8 cities → score boards;
   ROAD TRIP (2 entries + confirm); SINGLE SESSION → RIDER SELECT → LOCATION SELECT
   → gameplay → PAUSE (3 entries); FREE RIDE; MULTI PLAYER (HOT SEAT / LINK);
   RIDER SELECT BIOS. Every menu label was decoded from the text bank; no hidden or
   unlabelled selectable entry was found.
2. **Text/string space:** 46,540 strings (`strings -n 4`) and 95,104 (`-n 3`) were
   scanned. All 10 case-insensitive hits for `password|cheat|code|debug|secret|
   unlock|rider|hidden|invalid|menu` were classified: 7 were ordinary menu/bio text
   ("select rider", "found the secret to unreal", "few riders are pushing street",
   etc.), 1 was a `001 LINK ERROR` debug leftover with no menu, 1 was `rider select`,
   and 1 was the text-bank string `press a to continue`. Zero hits for a password
   prompt, code-entry prompt, debug menu, or unlock code. A separate dump of the
   font/tile-indexed bank at `0x7EFB58–0x7F3520` decoded every menu label (the bank
   stores lowercase; the font renders uppercase — this is why a naive uppercase
   `strings` search can miss the UI).
3. **Code-table space:** 15 default-initial strings at `0x0807F898` (4-byte stride,
   fully enumerated above); 8 long + 11 short name strings; zero validator tables.
   Alphabet search: `ABCDEFGHIJKLMNOPQRSTUVWXYZ`, lowercase, `0123456789`, and
   combined alphabets — **0 hits** in the 8 MiB image. No `strcmp`/`memcmp` table of
   accepted codes.
4. **Button space:** internal masks are 8 single buttons (256 one-frame
   combinations including 0). A raw u16 scan of all code regions for runs of ≥6
   consecutive single-button masks found **56** runs; every one is a repeated
   single-value data pattern (e.g. `01 01 01 01…` in `0x080A6660`), none is a
   multi-button code sequence. The only input-history consumer is the replay
   subsystem at `0x08006000–0x08006600`, which has no constant-comparison branch.
   Seven multi-press title-screen sequences (listed in §3) were entered against a
   saved state: all left the title screen unchanged (`PRESS START`), proving
   rejection for the tested space. No hidden debug screen was reached.
5. **Published codes:** no published GBA password/button code could be retrieved
   (all sources blocked; see §3), so no external literal exists to test. The
   in-ROM literal table we did find (`0x0807F898`) was verified in-game as the
   default scoreboard names, closing the only candidate.
6. **Novel code / bounds:** not applicable — there is no code system to mint from.
   Bounds are instead proven by (a) zero code references to the marker/initials
   table, (b) zero alphabet/comparison tables, (c) rejection of every tested button
   combination, and (d) full screen enumeration showing no input field.

## 7. Validation evidence

* **Observed** — ROM bytes and hashes; decoded text bank; high-score board on the
  Oklahoma screen showing the reversed 3-letter defaults; all menu screenshots;
  all title-screen sequence tests; 512-byte `.sav` after SAVE GAME; savestate RAM
  diffs (e.g. `0x03000399: 02→01` on rider change); Ghidra xref count 0 for the
  marker/code/name addresses; web fetches and their errors.
* **Derived** — stock header/entry from disassembly; input mask mapping from
  `0x080060DC`; replay-mode semantics from the mode writers and BL caller counts
  (11 record starts, 1 playback start); savestate RAM layout cross-checked between
  the decompressed `gbAs` chunk and mGBA's `-d` `r/4` reads.
* **Inferred** — that `c.kagy` / `dennis mccoy` are development leftovers (their
  labels exist but no input path reaches a selection state for them); that the
  progression locks are save-bit based rather than code-gated. No inference is
  presented as an observation.

## 8. Unknowns

* The exact semantic role of the `HGXFP101FLIPPERDIPPERHGX` marker is not proven;
  only its data neighbours and the in-game use of the adjacent initials are.
  Ghidra reports no references to it.
* Web verification of published codes was impossible from this environment, so
  the report cannot cite a fetched public list; the ROM-side search space is
  bounded instead.
* A code gated behind a save-file state that cannot be reached without completing
  the game (e.g. a very late unlock) was not exhaustively played through; the
  save-bit/unlock surface was characterised statically (guide §16.18) rather than
  by completing all objectives.
* `0x03000399` is a strong rider-index candidate from a 2-state diff, not a named
  symbol; no three-state monotonicity test was performed.

## 9. Tooling

* `file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings`, `grep` — Phase 0/1.
* `arm-none-eabi-objdump -M force-thumb`, Capstone 5.0.7, custom Python scanners
  (`phase0.py`, `dumptext.py`, `xrefs.py`, `litscan.py`, `keyptr.py`, `ramxref.py`,
  `blscan.py`, `btnscan.py`, `btnscan2.py`, `cmp_scan.py`) in `/tmp/opencode/mathoffman2`.
* REA MCP Ghidra 12.1.4 raw-ARM import (`open_binary`, `xrefs`) for reference counts.
* mGBA SDL under Xvfb :315 + openbox; `xdotool` XTEST input; `scrot`/ImageMagick
  screenshots; `tesseract` OCR for secondary screen checks.
* mGBA `-d` command-line debugger via a named-FIFO stdin, and `.ss1` savestate
  parsing (`ss.py`, `ss2.py`, `diffss.py`) for RAM evidence.
* No copyrighted asset is redistributed; only hashes, addresses, and findings are
  published.
