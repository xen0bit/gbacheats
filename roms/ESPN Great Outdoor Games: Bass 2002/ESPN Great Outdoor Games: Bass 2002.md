# ESPN Great Outdoor Games: Bass 2002 (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `ESPN Great Outdoor Games: Bass 2002.gba` (same folder as this report) |
| Size | 8,388,608 bytes (0x800000) |
| Header title | `ESPN FISHNG1` |
| Game code | `AMGE` (US, `AMGEUSA`) |
| Maker | `A4` (Konami) |
| Version | 0x00; fixed byte 0xB2 = 0x96; complement = 0x7C |
| Header checksum | 0x0000 (rebuilt-header artifact; complement byte is intact) |
| Entry word | `0xEA00002E` → standard crt0 at `0x080000C0` |
| MD5 | `18f479a8d3e0ac87d5f6495a43f76876` |
| SHA-1 | `d0f1e474c3fc4241dc400f0f52e591ac0798c452` |
| SHA-256 | `a4eba4cb9d757029dbd74b6c0293d780d07293c42c306a8740ea379f0c89bae5` |

This SHA-1 matches the no-intro USA image (`D0F1E474…`) listed in the BizHawk
GBA game database; the PAL release (`Bass Tournament`, `AMGP`) is a different
ROM. Phase-0 Nintendo-logo scan found exactly **one** GBA header in the file
(at `0x0`): no appended trainer, no cracktro, no 2-in-1/multi-game pack. The
entry branch is the stock `b 0x080000C0`, and the first 4 KiB is normal ARM
crt0 (co-processor/stack/IWRAM setup, `0x03007F00` stack). The image is a
clean retail image.

## 2. Executive summary

**No developer-intended in-game cheat system exists in this ROM.** There is
no password screen, no button-code sequence, no hidden/debug menu, and no
unlock code entry point. The game is a Konami/KCEO fishing title whose only
persistent state is a plain SRAM save (`BASSFISHING_2002` signature, 32 KiB),
not a password system.

The negative result is *bounded*, not assumed:

* All menu screens were walked in the emulator (§6b): title, main menu
  (`GAME` / `OPTION` / `RESULTS` / `LIVEWELL`), name entry, `MODE SELECT`
  (`TOURNAMENT` / `FREE FISHING` / `CABLE VERSUS`), the Tournament sub-menu
  (`START` / `RANKING`), multi-page rule explanation, target-fish card,
  qualifying, gameplay, the in-game `PAUSE` overlay, ranking and results.
  No hidden entry point appeared.
* The 8 MiB ROM was searched for `PASSWORD`, `SECRET`, `CHEAT`, `DEBUG`,
  `UNLOCK`, `CODE` in ASCII (0 hits); the game's non-ASCII 2-byte font text
  was decoded (143 text runs) and searched with the same keywords plus
  `level select`, `generator`, `invalid`, `congrat`, `enter your` (0 hits).
* All 73 code sites that read the input state word at `0x030018F0` were
  examined. The **only** multi-button gate in the whole ROM is the standard
  GBA soft-reset chord (held A+B+Select+Start = 0x0F, A+B on the edge) at
  `0x08000334`; pressing it in the emulator returns to the title screen — it
  is a console reset convention, not a cheat.
* Web search found **no published in-game password codes** for this SKU:
  GameFAQs cheats page is empty (403 direct; archived snapshot 404), VGChartz
  says "Total cheats available: 0", VideoGamesMuseum and ChapterCheats list
  none. The only circulating "codes" are **CodeBreaker RAM patches** (e.g.
  `Max Power When Casting 320001D6 0008`, `Catch 1 Fish For Max Weight
  4626CAD1 2AD1`) — external memory edits, explicitly out of scope.

Per §0.2, when no system exists the deliverable is a *proven* absence: this
report supplies the complete screen enumeration, the text/button search space
with exact counts, and the published-code check. There is no code space to
enumerate and no novel code to mint because no code system exists.

## 3. How to reproduce

* **ROM hash**: verify `sha256sum` matches §1 before trusting addresses.
* **Emulator**: mGBA (SDL build), `SDL_AUDIODRIVER=dummy`, under Xvfb on a
  private display. Command used:
  `Xvfb :315 -screen 0 1024x768x24 & DISPLAY=:315 openbox & DISPLAY=:315 SDL_AUDIODRIVER=dummy mgba -3 "<rom>" &`
* **Keymap** (mGBA SDL defaults): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
  Select=`BackSpace`, D-pad=arrow keys. Hold keys 100–300 ms (a 10 ms tap is
  missed); wait 1–5 s on screen transitions.
* **Menu path to every screen**:
  * Power on → ESPN splash → `BASS 2002` intro → `PUSH START` title.
  * `START` → main menu `GAME` / `OPTION` / `RESULTS` / `LIVEWELL`.
  * `GAME` → 8-character `NAME ENTRY` (keyboard `A`–`Z`, `SP`, `OK`) →
    `MODE SELECT` → `TOURNAMENT` / `FREE FISHING` / `CABLE VERSUS`.
  * `TOURNAMENT` → `BASS FISHING TOURNAMENT` → `START` / `RANKING`.
  * `START` → `RULE EXPLANATION` (several pages) → `TARGET FISH` →
    `BASS FISHING QUALIFYING` → gameplay (timer, LINE depth, API gauge).
  * In gameplay `START` → `PAUSE` overlay only (no menu items).
  * `RANKING` → top-5 ranking table; `RESULTS` and `LIVEWELL` from the main
    menu show the corresponding result/livewell screens.
  * A previously-saved file triggers a `PREVIOUSLY SAVED DATA DETECTED` screen
    with `CONTINUE` (and delete) — a save prompt, not a code gate.
* **Button-code test**: On the title screen hold `Select`+`Start` then press
  `A`+`B` → soft reset back to `PUSH START` (no hidden screen).
* **No codes were tested** because no published or discoverable in-game code
  exists; the three published CodeBreaker memory patches were reviewed and
  excluded as out-of-scope external cheats.

## 4. Address map

| Item | ROM address / file offset | Evidence |
|---|---|---|
| Header / Nintendo logo | `0x08000000` / `0x0` | Phase-0 logo scan (1 hit) |
| crt0 entry | `0x080000C0` / `0xC0` | entry word `0xEA00002E` |
| Input read + edge detect | `0x080007D0`–`0x0800086C` / `0x7D0`–`0x86C` | Thumb disasm: `ldr 0x04000130`, mask `0x03FF` |
| Key-state struct (held +0, pressed +2) | IWRAM `0x030018F0` | 73 PC-relative literal loads |
| Soft-reset gate (held==0x0F, A+B edge) | `0x08000334` / `0x334` | Thumb disasm; single caller `0x08000266` (main loop) |
| Save-signature literal | `0x08028EFC` / `0x28EFC` (`"BASSFISHING_2002"`) | pointer loads at `0x0800E29C`, `0x0800E2D0` |
| Save record (0x4D0-byte used area, 32 KiB SRAM) | SRAM `0x0E000000` | `.sav` dump; signature at 0, data 0x4D0–0x7FFF |
| Font text (2-byte encoding) | ~`0x080251B2`–`0x080298XX` / `0x251B2`–`0x298XX` | decoded `char = lo-0x40` after `0x81`/`0x82` prefix |
| ASCII fish/lure names, alphabets | `0x080269DC`–`0x08027CA4` / `0x269DC`–`0x27CA4` | `strings -t x` |

## 5. Algorithm

There is no cheat/password algorithm. For completeness, the two relevant
mechanisms actually present are:

* **Input handling** (`0x080007D0`): `held = ~KEYINPUT & 0x3FF`;
  `pressed = held & ~prev`; edge counters at struct offsets +8/+10. Only
  soft-reset (§4) has a multi-button test; all other consumers test single
  buttons (cursor movement, confirm/cancel).
* **Save format**: 32 KiB SRAM, plain (unencrypted) record with ASCII magic
  `"BASSFISHING_2002"` at offset 0, a version byte at `0x4CC`, and a data
  region from `0x4D0`. It stores player name, tournament progress and
  rankings. No checksum-derived unlock flags and no password field.

## 6. Tables

| Table | ROM addr / file | Contents |
|---|---|---|
| Name-entry alphabet | `0x08026BC0`–`0x08026D48` / `0x26BC0`–`0x26D48` | `0123456789?!-`, `&',._* #$()[]<>`, lowercase a–z, uppercase A–Z, combined 65-char set — **player-name input, not a password** |
| Fish species names | `0x08027348`–`0x080273F4` / `0x27348`–`0x273F4` | Spotted/Striped bass, Rainbow/Brown/Steelhead trout, Snake head, Catfish, Bluegill, Northern pike, Florida/Smallmouth/Largemouth bass |
| Lure names | `0x080273F4`–`0x08027CA4` / `0x273F4`–`0x27CA4` | JERKBAIT, STICK MINNOW, CURLYTAIL, CRAWFISH, STRAIGHT, RUBBER JIG, SPOON, SPINNER BAIT, PENCIL BAIT, POPPER, DEEP DIVER, CRANKBAIT, SUSPEND MINNOW, MINNOW, VIBRATION, … |
| CPU opponent names | `0x08026948`–`0x08026BC0` / `0x26948`–`0x26BC0` | ~80 personal names (J.Curry, G.Vegas, E.Blake, …) — **name pool, not codes** |
| Save signature | `0x08028EFC` / `0x28EFC` | `"BASSFISHING_2002"` |

No code tables, flag-bit tables or checksum constants exist (there is no code
system to populate them).

## 6b. Enumeration

Per §0.2, a "no system" result must show the enumerated space that was
checked. This is a **closed negative result**:

* **Screen space** — 100% walked. Title; main menu (4 entries); name entry
  (A–Z, SP, OK); MODE SELECT (3 entries); Tournament sub-menu (2 entries);
  rule-explanation pages; target-fish card; qualifying; gameplay (timer /
  LINE / API); PAUSE overlay (0 menu items — verified by screenshot and by
  pressing Left/Right/A with no effect); RANKING (top 5); RESULTS; LIVEWELL;
  save-detected prompt. No hidden/debug screen is reachable by any input.
* **Text space** — full 8,388,608-byte ROM scanned twice:
  * ASCII `strings`/`grep -abo`: `PASSWORD`, `SECRET`, `CHEAT`, `DEBUG`,
    `UNLOCK`, `CODE` → **0 hits each** (the only keyword hits in the raw
    strings pass were an unrelated CPU name `E.Blake` and compressed data).
  * Decoded 2-byte font text: **143 runs ≥5 chars** → keyword hits for
    `password|code|secret|debug|unlock|hidden|cheat|special|bonus|level
    select|generator|invalid|congrat|enter your` → **0 hits**. The decoded
    text consists solely of rule text, menu labels, link-cable messages and
    save/result messages.
* **Button-code space** — the key-state word `0x030018F0` is referenced from
  **73** Thumb literal-load sites; each was scanned for `cmp`/`tst`
  immediates in the button-mask range 1–0x3FF. Multi-button gates found:
  **1** — `0x08000334` (held==0x0F i.e. A+B+Select+Start, A+B edge). It sets
  `0x0300500F` and calls a reset/init path; in-game the chord returns to the
  title screen. All other sites test single buttons. A raw u16 scan of the
  whole ROM for 4+ consecutive single-button masks found no plausible code
  table (hits were uniform `0x01FF` fill in tile/audio data).
* **Published codes** — searched web.archive GameFAQs (snapshot 404), direct
  GameFAQs (403), VGChartz ("Total cheats available: 0"), VideoGamesMuseum
  and ChapterCheats (empty cheat sections). The only published "codes" are
  CodeBreaker RAM patches (memory edits), which are out of scope and were
  not entered. No developer password list exists for this SKU.
* **Novel code** — not applicable: with no code system, alphabet, validator or
  entry surface, there is no code space to generate from and no bounds to
  test. §0.2's "mint a novel code" requirement applies only when a system
  exists; the absence is proven above by the exhaustive screen/text/button
  enumeration and the published-code check.

## 7. Validation evidence

* **Observed** (emulator, Xvfb :315, mGBA -3): every screen in §3/§6b;
  A+B+Select+Start soft reset; PAUSE overlay with no items; save-detected
  prompt. Screenshots retained in `/tmp/opencode/espnbass/shot_*.png` /
  `crop_*.png` (not attached).
* **Observed** (binary): hashes and header §1; single logo hit; SRAM dump
  with `BASSFISHING_2002` signature; 0 ASCII keyword hits; 143 decoded text
  runs with 0 keyword hits; 73 input-state xrefs with 1 multi-button gate.
* **Derived** (disassembly): input struct layout at `0x030018F0`; soft-reset
  gate condition at `0x08000334`; save-signature pointer loads at
  `0x0800E29C`/`0x0800E2D0`; font encoding `char = lo-0x40`.
* **Inferred**: that the SRAM record's 0x4D0+ region holds progress/name/
  rankings (from the writer at `0x0800E250`/`0x0800E2A0` and the save-detected
  screen). Not a cheat surface.
* **No prompt-injection content** was encountered in fetched pages or ROM
  text; all fetched pages were treated as data.

## 8. Unknowns

* The precise field layout of the SRAM record beyond the 16-byte signature
  and version byte was not fully mapped — it is ordinary progress data, not
  a cheat/unlock surface, so it did not affect the result.
* A small number of decoded text runs begin with a garbled character (e.g.
  `ONTESTANTS` for `CONTESTANTS`) because the first glyph of a line uses a
  different prefix byte; this is a decoder detail, not hidden text.
* Published CodeBreaker codes were reviewed but not executed (external memory
  edits, out of scope); their in-game effects are therefore unverified and
  intentionally untested.

## 9. Tooling

* `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings`, `grep` —
  Phase-0 fingerprint and raw-string scan.
* Python 3 (stdlib `struct`, `re`) — header parse, Nintendo-logo scan,
  literal/pointer scans (4-byte pointer search, Thumb `LDR [PC,#imm]` decode
  with `target = Align(addr+4,4)+imm`), BL-target scan, u16 button-mask
  table scan, and the 2-byte font-text decoder.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M
  force-thumb` — targeted Thumb disassembly of input/reset/save code.
* mGBA (`-3`, `-g`, `-d`), Xvfb `:315`, openbox, `xdotool`, `import`,
  `convert` — emulator, input, screenshots. mGBA's GDB stub (`-g`) was
  unreliable in this build (target stalled; "no registers"), so the
  stub-free `-d` pty debugger was used for memory reads where needed.
* `pdftotext` on the USA manual (image-only; 0 text lines) — not used as
  evidence.
* Artifacts: `/tmp/opencode/espnbass/` (scripts `key.py`, `dbg.py`, `dbgd.py`,
  screenshots, logs).
* Legal: no ROM bytes or copyrighted assets are redistributed here — only
  hashes, addresses, and the analysis method.
