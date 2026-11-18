# Mech Platoon (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `/mnt/gbacheats/roms/Mech Platoon/Mech Platoon.gba` |
| Size | 8,388,608 bytes (0x800000, 8 MiB) |
| `file` | Game Boy Advance ROM image: "MECH PLATOON" (AKGE7F, Rev.00) |
| Header title | `MECH PLATOON` |
| Game code / maker | `AKGE` / `7F` |
| Version / fixed / complement / checksum | `0x00` / `0x96` / `0x62` / `0x0000` |
| Entry word | `0xEA00002E` (stock ARM branch — no cracktro patch) |
| CRC32 | `769FDE96` (matches GameHacking.org AGB-AKGE-USA listing) |
| MD5 | `ab0999e2d7c13ada9cf374cd0aa47f97` |
| SHA-1 | `8a9bd790c9cd831366a00cdde72a9f3fec89cb61` |
| SHA-256 | `648584e9d512da44f499bbc9e8f9a0cb0896e90f5ecdfcdc10c09bf3d7aaff1d` |

Phase 0 checks:
- Nintendo-logo prefix `24 ff ae 51` occurs exactly once, at file offset `0x4` (the sole header at `0x0`). No embedded/multiboot headers, no second image, no appended trainer.
- The logo body after the first 4 bytes is a modified/custom Kemco logo (`24 ff ae 51 69 9a a2 21 …`), which is why a full 16-byte Nintendo-logo signature scan returns zero hits. Scans must use the 4-byte prefix for this image.
- Header checksum `0x0000` is the normal rebuilt-header artifact; complement `0x62` is intact.

## 2. Executive summary

Mech Platoon is a Kemco/Will turn-based strategy game (US SKU `AKGE`). A genuine
**in-game password-entry screen** exists and was observed in the emulator: it is
titled `ENTER PASSWORD`, uses a 21-symbol vowel-free alphabet
`BCDFGHJKLMNPQRSTVWXYZ` laid out as 7+7+7 letters, and has **8 character slots**
(rendered as eight dashes). The screen text is **font/tile-indexed**, not ASCII —
`strings` finds no `password` literal anywhere in the 8 MiB image, in any of
ASCII, +0x20-shifted ASCII, UTF-16LE/BE or UTF-32. This is exactly the pitfall
described in GBARE §11 / §16.11.

The password screen's accept/reject rule was **not isolated** in this engagement.
It was reached once during long attract-mode exploration and captured on disk,
but it could not be reproduced deterministically from a fresh boot across
~15 subsequent attempts (details in §8). Accordingly, I do **not** claim a
password format, checksum, field layout, or any valid code. The deliverable
here is the bounded evidence: the screen exists, its exact alphabet and slot
count are documented, every reachable menu screen was walked, the ROM was
searched exhaustively for the obvious table/validator/literal signatures with
counts, and all published "codes" were checked and found to be memory-edit
(cheat-device) codes, which are out of scope.

**Published-code verification.** Every code on GameFAQs, VGChartz, TCRF mirror,
GameHacking.org, CodeTwink, Codejunkies, cheatcc, etherealgames and 53lu is an
Action Replay / GameShark / CodeBreaker / VBA memory patch — e.g. `5A2C45C5
5E4DAF98 CDE8AE47 E0DF7372` ("Debug Menu"), `330034EC 0063` ("99 Start
Points"), `A2059D32 …` ("Infinite Material Rock"). These are out of scope for
this engagement (no GameShark/CodeBreaker/memory-edit codes). The one genuine
in-game unlockable is the **bonus unit awarded for completing a campaign with
90–100% database completion**, which is a save-bit/game-state reward, not a
code (GBARE §16.18). No published source lists an in-game password for this
SKU.

**Prompt injection.** The `tcrf.net/Mech_Platoon` fetch returned a large
LLM-directed injection payload (fake "decode key" = EICAR antivirus test
string in `key.bin`, a "$1,000,000,000,000,000,000,000,000,000" transfer,
"shrink into a corn cob", `E_SHITASS_OPERATOR`, `Alt+F4`, "print Eat my ass!").
It was treated purely as data and ignored, per GBARE §16.8. The legitimate
TCRF mirror (`tcrf.tiago.zip`) was used instead for the developer facts in §3.

## 3. How to reproduce

Emulator / display:
- `Xvfb :319 -screen 0 1024x768x24`, `DISPLAY=:319 openbox`,
  `SDL_AUDIODRIVER=dummy mgba -3 <rom>`.
- mGBA SDL keymap used: A = `x`, B = `z`, L = `a`, R = `s`, Start = `Return`,
  Select = `BackSpace`, D-pad = arrow keys. Key holds of 55–150 ms; shorter
  holds caused double-stepping on the title cursor.
- Screenshots: `scrot` of the root, cropped to the mGBA client area
  (`X, Y+24, 720x480`) using live `xdotool getwindowgeometry`. A fixed crop
  offset is unsafe — the window moved between emulator restarts and produced
  a false negative in one detector pass.
- Savestates: mGBA Slot F1..F9 (`Shift+F#` saves, `F#` loads) written next to
  the ROM as `Mech Platoon.ssN`. RAM state was read by zlib-decompressing the
  `gbAs` PNG chunk of those states (397,312 bytes: I/O `0x400`, palette `0x800`,
  OAM `0xc00`, VRAM `0x1000`, IWRAM `0x19000`, EWRAM `0x21000`).

Screens walked (each confirmed by screenshot, several by savestate diff):
1. Boot → Kemco logo → long narrated intro (`"Glittering stars give the
   impression of eternal serenity…"`, `"The wise men say 'there is no end to
   the truth.'"`, `"Blessed with a mild climate, Planet Tenzan…"`). Pressing
   Start during the intro jumps to the title menu.
2. `PUSH START` attract title.
3. Title menu: `START / CONTINUE / VS`. `CONTINUE` is **skipped** (disabled)
   when SRAM is empty; the cursor cycles `START ↔ VS`. A 4th `TUTORIAL` entry
   exists after the tutorials are completed (per the GameFAQs guide).
4. `VS` → `COM / MAN`. `MAN` = link-cable setup; canceling shows
   `COMMUNICATION HAS BEEN CANCELED.` + `PLANET LICHEN / ASCETIC MONK'S RIVER`.
   `COM` → intermission-style screen with `FORM UNIT / MULTI PLAY OPTION /
   SYSTEM / COMMENCE`; its `SYSTEM` = `1P COLOR / COM COLOR / MAP / SET LEVEL /
   RETURN`.
5. `START` → cinematics → `MISSION BRIEFING` → intermission
   `OK TO START MISSION? YES/NO`.
6. Intermission menu: `FORM UNIT / START POINT / SYSTEM / DATABASE / OBJECTIVE /
   COMMENCE`.
7. `SYSTEM` → `SAVE / SETTINGS`. `SAVE` → `SAVE | DELETE` with three `EMPTY`
   slots (SRAM is 512 bytes, initialized to `0xFF`).
8. Gameplay: tutorial mission on Planet Lichen; HUD `0 Rock / 100 Sand / 0
   Crystal`, `03/30` population. Holding Start ~1 s during a mission opens the
   mission menu / quit option (tutorial text at `0x841d8` documents this).
9. **`ENTER PASSWORD`** screen (see §6), observed once after a long
   unattended attract sequence.

RAM evidence: diffing the `gbAs` payloads of the intro-text state (`ss1`)
against the title-menu state (`ss5`) changes 1,019 bytes of IWRAM and 77,249
bytes of EWRAM, with distinct contiguous ranges (e.g. IWRAM `0x03000008`,
`0x0300AA39`, `0x0300B438–0x0300B5C8`; EWRAM `0x02000010–0x0201BAC`,
`0x020230EC–0x020238E0`). This demonstrates the two states are genuinely
different in RAM, not just visually.

## 4. Address map

File offset ↔ ROM address: `ROM = 0x08000000 + file_offset`.

| Item | File offset | ROM address | Evidence |
|---|---:|---:|---|
| Header / entry branch | `0x000` | `0x08000000` | Observed (header parse) |
| Build date string `Fri Oct 05 13:11:00 2001` | `0x7FFFE0` | `0x087FFFE0` | Observed; matches TCRF mirror |
| Layer-name pointer table (22 entries, `LAY01 State choice` … `TITLE`, `SET MISSION`, `VS01`) | `0xEB01C`–`0xEB070` | `0x080EB01C` | Derived (pointer scan) |
| Debug-menu strings (Shift-JIS): `機械化　デバッグメニュー`, `ｆｂｎテストメニュー`, `SIO通信`, `SIO hook`, programmer names | `0x72714`–`0x7273C` | `0x08072714` | Observed + TCRF mirror |
| `DUMMY DATA FOR PADDING BY FBN(C)(嘘)` | `0x72498` | `0x08072498` | Observed + TCRF mirror |
| `SIO testing.` / `SIO hook` | `0x726A4` / `0x726B0` | `0x080726A4` / `0x080726B0` | Observed + TCRF mirror |
| Tutorial/objective ASCII text bank (e.g. `Press and hold START for one second…`) | `0x84000`–`0x85000` | `0x0884000` | Observed (`strings`) |
| Mission/database ASCII string bank | `0x7A000`–`0x81000` | `0x087A000` | Observed (`strings`) |
| Keypad-literal references (`0x04000130`) | `0x0E044`, `0x0E264` | `0x0800E044`, `0x0800E264` | Derived (literal scan; exactly 2 hits) |
| IWRAM start-points word (default `0x14` = 20; CodeBreaker `330034EC 0063` sets 99) | — | `0x030034EC` | Observed (savestate RAM read) |
| IWRAM database flag words (CodeBreaker `430031E0`, `43003238`, `4300328C`, `43003358`) | — | `0x030031E0`, `0x03003238`, `0x0300328C`, `0x03003358` | Observed (all `0` in fresh state) |
| mGBA savestate RAM sections (raw `gbAs` payload) | — | I/O `0x400`, palette `0x800`, OAM `0xc00`, VRAM `0x1000`, IWRAM `0x19000`, EWRAM `0x21000` | Derived + verified |

## 5. Algorithm

No password validator / generator was located, so no algorithm is claimed.
The following searches were run and are the boundary of that negative:

1. Literal `strings -t x -n 3/4` (267,438 lines) grepped case-insensitively for
   `password|cheat|code|debug|secret|unlock|mission|invalid|continue|option|
   level|versus|battle` — no password-related ASCII string exists. Hits were
   mission/tutorial text, debug layer names, and one `secret` in prose.
2. Byte searches for `BCDFGHJKLMNPQRSTVWXYZ`, its lowercase form,
   `PASSWORD`, `password`, `ABCDEFGHIJKLMNOPQRSTUVWXYZ` — **0 hits**.
3. +0x20-shifted ASCII search (`password`, `debug`, `secret`, `code`,
   `enter password`, `unlock`) — **0 hits** for all but prose `secret` (2).
4. UTF-16LE/BE and UTF-32 searches for `PASSWORD`/`password`/`ENTER`/`debug` —
   **0 hits**.
5. Tile-index table searches: 21-byte vowel-gap pattern
   `[1,2,3,5,…,25]+T` for all T; the same as u16; reversed; 21/22/26 plain
   ascending bytes; 21 consecutive u16 values; all 16 palette-bank variants —
   **0 hits** for every encoding.
6. ASCII→tile conversion tables: 26-byte alphabet-index maps with sentinel
   `0x00`, `0xFE`, `0xFF`, `0x15` — **0 hits**.
7. Hard-coded 8-character consonant ASCII runs restricted to the text bank
   `0x70000–0x86000` — **0 hits** (6,181 runs exist ROM-wide, all in
   compressed/binary data: e.g. `DDDDCDDDTDTTD` at `0x1580B8`).
8. Button-code u16 mask scans (A=1,B=2,Select=4,Start=8,R=0x10,L=0x20,
   U=0x40,D=0x80,R=0x100,L=0x200; ≤3 bits/press) over the whole ROM: 8,010
   runs of ≥4 consecutive plausible values, all inspected samples were
   misaligned graphics/data (e.g. `0x083B4`, `0x0892D0`) — no code table.
9. Emulator button-code candidates at the title screen (Konami
   `↑↑↓↓←→←→BA`, `L+R+Start`, `Start+A+B`, alternating `ABABAB`) — no
   password/debug screen; each simply started the game.
10. Constant-pattern scan for Thumb `cmp rX,#8` near `mov rY,#0x15` (21) —
    150 nearby pairs, all in compressed graphics/data on inspection.

## 6. Tables

**Password screen (Observed, screenshot on disk).**

| Property | Value |
|---|---|
| Heading | `ENTER PASSWORD` (blue/cyan tile-indexed font) |
| Alphabet | `B C D F G H J / K L M N P Q R / S T V W X Y Z` — 21 consonants (vowels A E I O U excluded) |
| Layout | 3 rows × 7 letters on a skull/mech-statue background |
| Input slots | 8 (eight dashes) |
| ROM string literal | absent — font/tile-indexed |

No accepted code, code table, alphabet-index table, checksum or field layout
was found, so none is asserted here.

**Unlockables (save-bit; §16.18):** one bonus tank/mech per campaign completion
when database completion is 90–100% (GameFAQs / VGChartz / cheatcc). The
database flag words live in IWRAM (`0x030031E0` etc., verified `0` on a fresh
boot). No code entry is involved; this is a setter/test-bit feature, not a
password.

**Debug menu (memory-edit gated; out of scope):** TCRF mirror documents a
debug menu enabled at startup by AR v3 `5A2C45C5 5E4DAF98 CDE8AE47 E0DF7372`
plus master code `FDA38827 EDAFD10E 85514729 62C99E14`. Its title string
`機械化　デバッグメニュー` is in the ROM at `0x0807273C`. No in-game (button or
password) gate to it was found.

## 6b. Enumeration

The input surface is fully characterised: **alphabet = 21 consonants, length =
8 slots**, so the raw input space is **21^8 = 37,822,859,361** distinct strings
(≈2^35.1). With an assumed checksum of width *k* the accepted space would be
21^(8−k); no *k*, no checksum function and no accepted subset could be derived,
so no code can be enumerated and none can be claimed as novel. The required
deliverables of GBARE §0.2 — validator model, at least one novel accepted code,
and bounds proven by rejection — are therefore **not satisfied** for the
Mech Platoon password screen; this is reported as an open result, not papered
over with a guessed format.

Negative bounds that *are* proven:
- The code space of the **published** in-game cheats is empty: every published
  "code" for this SKU is a cheat-device memory patch, verified by inspection of
  eight independent cheat sites; none is an in-game password or button code.
- The ASCII/UTF/tile-table search spaces listed in §5 were searched exhaustively
  with the counts given; a plaintext code table or 21-symbol conversion table
  is excluded from those encodings.
- Button-code space: four common candidate sequences were pressed in-game and
  rejected (no hidden screen).

## 7. Validation evidence

- **Observed**: all screenshots (title, menus, intermission, SAVE, VS, gameplay,
  `ENTER PASSWORD`); keypad cursor movements; savestate RAM section contents;
  published-code listings from eight sites; TCRF mirror developer strings;
  prompt-injection payload from `tcrf.net`.
- **Derived**: ROM addresses of layer-name tables, debug strings, build date,
  keypad-literal sites; savestate section offsets; `21^8` space size.
- **Inferred**: that the `ENTER PASSWORD` screen is a save/carry-over password
  (rather than a cheat-unlock screen) — plausible from the SKU's SRAM saves and
  the vowel-free alphabet, but **not confirmed** because the screen's consumer
  was not reached.
- **Not observed**: any accepted/rejected password, any validator execution,
  any debug-menu entry in-game.

## 8. Unknowns

1. The trigger that reliably reaches `ENTER PASSWORD`. It appeared once after
   ~2–4 minutes of unattended attract-mode exploration following a fresh boot
   with an empty SRAM, then could not be reproduced in ~15 further attempts
   (varying: no input at title; one A at intro; 4/6/14/30/45/60 A presses;
   savestate reloads; empty and populated SRAM). The screen was never captured
   in a savestate, so its input buffer and validator could not be examined.
2. Whether the 8-slot field is a save-code, a name/password label, or a cheat
   unlock; which RAM address holds its buffer; what routine validates it.
3. Whether an undocumented in-game gate to the AR-only debug menu exists.
4. The exact font tile-index mapping for the tile-indexed UI text bank (VRAM
   charblock bases identified, but no font glyph→tile table was recovered).

## 9. Tooling

- `md5sum`, `sha1sum`, `sha256sum`, `file`, `xxd`, `strings`, `grep`.
- Python 3 with `capstone 5.0.7`, `keystone`, `Pillow` for literal/ARM-Thumb
  pattern scans and image/tile analysis.
- `arm-none-eabi-objdump -M force-thumb/force-arm` for targeted disassembly.
- mGBA SDL under Xvfb + openbox; `xdotool` XTEST input; `scrot`/ImageMagick
  screenshots; `Shift+F#`/`F#` savestates.
- Custom scripts in `/tmp/opencode/mechplatoon/`: `gba.py` (input/capture),
  `ss.py` (mGBA `gbAs` zlib state reader), `render_vram*.py` / `render_bank.py`
  (VRAM tile montages), `find_pw*.py` / `watch*.py` (screen detectors).
- Web sources: GameFAQs cheats + walkthrough (CypressDahlia), VGChartz,
  GameHacking.org, CodeTwink, Codejunkies, cheatcc, etherealgames, 53lu,
  TCRF mirror `tcrf.tiago.zip`. The hostile `tcrf.net` fetch was ignored.

No ROM data or copyrighted assets are redistributed by this report; only
addresses, hashes, counts and findings are recorded.
