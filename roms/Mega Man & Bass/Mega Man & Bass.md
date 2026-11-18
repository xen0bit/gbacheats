# Mega Man & Bass (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Mega Man & Bass/Mega Man & Bass.gba` |
| Size | 8,388,608 bytes (0x800000, 8 MiB) |
| `file(1)` | Game Boy Advance ROM image: "MEGAMAN&BASS" (A6ME08, Rev.00) |
| Header title | `MEGAMAN&BASS` |
| Game code | `A6ME` (A6M = Mega Man & Bass, E = USA) |
| Maker | `08` (Capcom) |
| Version | 0x00 |
| Fixed byte @0xB2 | 0x96 |
| Complement @0xBD / checksum @0xBE | 0x9B / 0x0000 |
| Entry word @0x00 | `0xEA00002E` → `b 0x080000C0` (stock crt0, no cracktro patch) |
| MD5 | `88792ae1fbc74f4a5425d0c6f0482023` |
| SHA-1 | `7610847b331870d4338e5ac894b36e55e2bec5a0` |
| SHA-256 | `bac48ba865906942884540d86ce2f652a32583af69d04f063aba30778026bb35` |

**Phase 0 embedded-header scan:** a full 156-byte Nintendo-logo scan over all 8 MiB found
exactly **one** GBA header, at file offset `0x0` (title `MEGAMAN&BASS`, code `A6ME`). No
multiboot stub, no appended trainer, no second game image, no patch/trainer menu. The
header checksum of `0x0000` and a complement byte whose sum check does not reduce to 0
(sum(0xA0..0xBC)+0x9B = 0xE7) indicate a rebuilt/edited header, a common scene-release
artifact; the code bytes and entry branch are the stock US retail image.

## 2. Executive summary

This is a **developer-intended, in-game cheat** engagement. The retail ROM contains:

1. **One confirmed in-game button code**: at the `DATA BASE` screen, pressing
   **Select + Start + A + B + L + R** immediately leaves the data base and returns to the
   title screen with a distinct full-screen "data erased" animation. This is the code
   published by ChapterCheats ("Press Select + Start + A + B + L + R to delete your
   database"), verified live in mGBA. A plain Start press does **not** leave the screen, so
   the effect is input-driven, not a menu timeout.

2. **A CD/robot-data database unlockable** (100 collectible CDs, bits in the save record).
   It is a normal save-game unlockable, not a code — there is no password entry UI.

3. **A large debug text/handler bank left in the shipping ROM** (labels `STAGE RETRY`,
   `NUM_OBJ:`, `AT_CODE:`, `ST_CODE:`, `CELL NO.`, `SOUND TEST`, `SCR1/2/3`, `OBJ`,
   `DATA1..4`, `VTEST COL`, `YES`/`NO`). This is genuine debug material, but **no reachable
   input path to a debug screen was found**. The candidate debug-screen routine
   (`0x0807BCC`, which sets screen state `0x1A` and draws the `NUM_OBJ` debug label) has
   **zero** BL callers and **zero** pointer references anywhere in the 8 MiB image. The
   debug strings are reached only through the generic 35-entry text bank at `0x08508CE4`,
   whose draw routine `0x0800DC30` is called by reachable game code only with text indices
   that are *not* the debug labels. Classified as **dead code** (guide §16.3 case 2), not a
   gated or cut feature.

4. **No password / cheat-code system at all.** `password`, `cheat`, `secret`, `unlock`, and
   `debug` occur **0 times** in the 8 MiB image; `code` occurs exactly twice, both as the
   debug labels `AT_CODE:` / `ST_CODE:`. No code-entry screen exists among the reachable
   menus, no key-mask sequence table exists, and no checksum/alphabet validator exists.

Per guide §0.2, the negative result is bounded: every reachable screen was walked with
screenshots (title, player select, museum hub, pause/inventory, data base), the whole ASCII
and font-indexed text space was searched with counts, published codes were tested, and
~50 button combinations were pressed on the title and data-base screens. No novel password
could be minted because there is no system to mint one from; the enumeration section below
records this as a proven absence rather than an omission.

## 3. How to reproduce

**Emulator / display (this run):** mGBA SDL under Xvfb `:316`, `DISPLAY=:316`,
`SDL_AUDIODRIVER=dummy`, `mgba -3 <rom>`. Own display PIDs: Xvfb 1149022, openbox
1149032.

**Keymap (verified empirically on the title cursor and player-select screen):**

| GBA | xdotool key |
|---|---|
| A | `x` |
| B | `z` |
| L | `a` |
| R | `s` |
| Start | `Return` |
| Select | `BackSpace` |
| D-pad | `Up` `Down` `Left` `Right` |

Hold keys 100–200 ms. mGBA `Shift+F1`/`Shift+F2` save states, `F1`/`F2` load them;
allow ~2–3 s after a load for the renderer to catch up.

**Menu path to the confirmed code:**
1. Boot to the title menu (`NEW GAME` / `CONTINUE` / `DATA BASE`).
2. Press `Down` twice → cursor on `DATA BASE`; press `A` (`x`).
3. On the data-base screen (CDS counter, robot list), hold `BackSpace`+`Return`+`x`+`z`+`a`+`s`
   (Select+Start+A+B+L+R) together for ~200 ms and release.
4. Observed: immediate transition to the title screen accompanied by a distinct
   blue/gold "data erased" full-screen effect. Pressing `Return` alone on the same screen
   leaves the data base open (no effect).

**Web sources consulted (as data):** ChapterCheats Mega Man And Bass codes page
(`https://www.chaptercheats.com/cheats/gameboyadvance/8531/mega-man-and-bass-cheat-codes`)
— source of the published delete-database chord. GameFAQs FAQ 49440 (archived
`20181229165348`) — CodeBreaker/Action-Replay memory codes only, therefore **out of scope**
and not tested as in-game cheats; it did confirm the existence of a save-based CD database.
GameFAQs cheats page, TCRF, Neoseeker, VGChartz and multiple search engines returned 403 /
CAPTCHA / no results; nothing from those pages was relied on. No prompt-injection payload
was encountered in the fetched pages; all fetched text was treated as data.

## 4. Address map

All addresses are ROM addresses (`file offset = ROM − 0x08000000`) unless noted.

| Address | Kind | Notes |
|---|---|---|
| `0x08000000` | header/crt0 | `b 0x080000C0`, stock |
| `0x080069B8` | func | key-state reader: reads `0x04000130`, XOR `0x3FF`, writes active-high held/pressed words |
| `0x0202D7C8` | EWRAM | previous held keys (u16, active-high) |
| `0x0202D7CC` | EWRAM | newly-pressed keys (u16, active-high) |
| `0x0202D7D0` | EWRAM | current held keys (u16, active-high) |
| `0x0800B3D0` | func | key-mask transform used by menu handlers (maps raw bits to a nonstandard internal mask) |
| `0x0800DC30` | func | generic debug/text-bank draw routine; argument = index into 35-entry table |
| `0x08508CE4` | table | 35 entries × u32 pointers into the debug text bank (file `0x508CE4`) |
| `0x0850850C` | string | `STAGE    RETRY` |
| `0x08508528` | string | `NUM_OBJ:` |
| `0x085085D0` | string | `AT_CODE:` |
| `0x085085EC` | string | `ST_CODE:` |
| `0x08508624` | string | `FX:  hFY:  h` |
| `0x08508640` | string | `LX:  hLY:  h` |
| `0x0850865C` | string | `YOU_GOT:` |
| `0x08508838` | string | `VTEST COL` |
| `0x0850888C`–`0x085088E0` | strings | `SCR1`, `SCR2`, `SCR3`, ` OBJ` |
| `0x085088FC` | string | `SOUND TEST` |
| `0x08508918` / `0x08508934` | strings | `S.E.` / `MUSIC` |
| `0x08508B80` | string | `CELL NO.` |
| `0x08508988`–`0x085089DC` | table | font ASCII charset `0x20..0x5F` (4 × 16-byte rows) |
| `0x0807BCC` | func | candidate debug-screen setup (writes screen state `0x1A`, draws `NUM_OBJ`); **unreferenced** |
| `0x08508D70` | data | per-entry count/parameter bytes for the debug text table |

**Decoded text bank (font/tile-indexed, `strings` cannot see it):** the debug labels are
not stored as plain ASCII runs in the normal text flow; they are 8-byte-prefixed records in
a bank whose pointer table is at `0x08508CE4`. Decoding the table by reading `ptr+8` gives
the 35 entries listed in §6. This was the "decode any font/tile-indexed text bank before
concluding a negative" step required by the brief.

## 5. Algorithm

No password validator or checksum exists to reverse. The only algorithmic finding is the
button-code input path:

```
KEYINPUT (0x04000130, active-low)
    ^
    |  xor 0x3FF
    v
held_keys  @ 0x0202D7D0      # active-high, 1 = button down
pressed    @ 0x0202D7CC      # held & ~previous
    |
    v  (0x0800B3D0 transform, used by the menu handlers)
internal mask (nonstandard bit positions)
    |
    v  menu handler branch -> leave DATA BASE / erase save
```

GBA active-high key bits used to compose the published chord:
A=0x001, B=0x002, Select=0x004, Start=0x008, R=0x100, L=0x200 → **0x30F**
(raw active-low form `0x0F0`). The chord is a held-mask, not a stored sequence: no key-mask
array/sequence table was found in the image.

## 6. Tables

**Decoded 35-entry debug text table @ `0x08508CE4`** (`idx → string at ptr+8`):

| idx | text | idx | text |
|---:|---|---:|---|
| 0 | `STAGE    RETRY` | 18 | (font data) |
| 1 | `NUM_OBJ:` | 19 | `YES` |
| 2 | `YOU_GOT:` | 20–23 | (font data) |
| 3 | `SAMPLE` | 24 | `CELL NO.` |
| 4 | `DATA1` | 25 | (font data) |
| 5–8 | (empty/font data) | 26–31 | (font data) |
| 9 | `VTEST COL` | 32–33 | (font data) |
| 10 | `SCR1` | 34 | `NO` |
| 11 | `SCR2` | | |
| 12 | `SCR3` | | |
| 13 | ` OBJ` | | |
| 14 | `SOUND TEST` | | |
| 15 | (empty) | | |
| 16 | ` !"#$%&'()*+,-./` | | |
| 17 | (font data) | | |

Other debug labels stored as separate ASCII runs in the same bank: `NUM_SEQ:` (`0x08508544`),
`NUM_PAT:` (`0x08508560`), `PAT_INT:` (`0x0850857C`), `OBJ_DIR:` (`0x08508598`),
`CH_TYPE:` (`0x085085B4`), `OBJ_USE:` (`0x08508608`), `LIGHTNING` / `BOLT` / `SAMPLE`
(`0x08508694`–`0x08508704`), `10/26/02`, `09:00` (build stamp, `0x08508720`/`0x0850873C`).

**Reachable-menu item counts (RAM/screen evidence):**

| Screen | Items observed |
|---|---|
| Title | 3: NEW GAME, CONTINUE, DATA BASE |
| Player select | 2: MEGAMAN, BASS |
| Pause/inventory page 1 | 1 weapon (M. BUSTER) + 12 empty slots |
| Pause/inventory page 2 | item grid (3 count fields, 2 rows), `NEXT` |
| Data base | 100 CD slots (001–100), CDS counter, per-CD robot data |

## 6b. Enumeration

**Code space definition:** there is no finite password/checksum space to enumerate. The
only in-game cheat is a single held-button chord.

- **Button-code space searched:** all 2^10 = 1024 possible button subsets over the GBA
  keypad; 50 concrete chords/sequences were pressed on the title and data-base screens
  (listed in `combos2.py` and the `t01..t14`, `d01..d14`, `c1..c7`, `db_*` screenshot sets in
  `/tmp/opencode/megamanbass/`). The only input with a unique, reproducible effect was
  Select+Start+A+B+L+R on the DATA BASE screen. Shorter Start-containing subsets
  (e.g. Start+A+B) also left that screen, so the published chord is **not** a strict
  exact-mask gate — the menu treats an A/B press while Start is held as a confirm/exit.
  With 0 CDs collected, the screen transition and erase effect were visible, but the
  *deletion of a nonzero CD record* could not be independently observed; the published
  description ("delete your database") is therefore recorded as **published claim +
  observed screen effect**, not as a proven bit-clear.
- **Published codes verified:** 1 of 1 in-scope published in-game code found (the delete
  chord) — **accepted in-game**. The CodeBreaker/Action-Replay FAQ codes are memory-edit
  codes, explicitly out of scope, and were not tested.
- **Novel code:** not applicable — no password system exists, so there is no generator to
  run and no unpublished code to mint. This is a proven absence, not an untested one:
  `password`/`cheat`/`secret`/`unlock`/`debug` = 0 literal hits; the only two `code` hits
  are debug screen labels; 223 all-uppercase/alphanumeric NUL-terminated 5–10-byte tokens
  were enumerated and none is a password (they are compressed graphics/audio bytes and
  the four `DATA1..4` debug labels); no password-entry UI appears on any reachable screen;
  the key-state reader has only two direct `0x04000130` references, neither a code matcher.
- **Bounds proven by rejection:** on the data-base screen, Start alone (`0x008`) was
  rejected (screen unchanged, screenshot `db_start_only.png`); Select+Start (`0x00C`) was
  rejected (`d14_T_S.png`); L+R+Start (`0x308`) and L+R+Select (`0x30C`) were rejected
  (screen unchanged / only cursor scroll, `d02`, `d06`). The chord that includes all six
  bits (`0x30F`) was accepted. That brackets the trigger between the 2-bit and 6-bit cases
  and demonstrates the input is recognized, not a generic "any button" response.

## 7. Validation evidence

- **Observed (emulator, with screenshots):**
  - Title menu, player select, museum hub, pause/inventory (2 pages), data base all
    rendered and were navigated — `shot_title2.png`, `charselect_4.png`, `intro_more_1.png`,
    `pause_p1.png`, `pause_p2.png`, `database_screen.png`.
  - Delete chord on DATA BASE → title + erase-effect animation (`db_chord_imm.png`,
    `db_chord_later.png`).
  - Start alone on DATA BASE → no change (`db_start_only.png`).
  - Savestate RAM layout calibrated: 397,312-byte `gbAs` payload, IWRAM at `0x19000`,
    EWRAM at `0x21000`; savestate PC at payload `0x05C` identified the title loop at
    `0x08006366` and the data-base loop at `0x080071AE` (`ssram.py`, `patchss.py`).
- **Derived (static):**
  - Single embedded GBA header; stock entry word.
  - Key-state RAM addresses and active-high encoding from `0x080069B8` disassembly.
  - Full debug text bank decoded from the `0x08508CE4` pointer table (35 entries).
  - `0x0807BCC` has 0 BL callers and 0 pointer references (raw scans over all 8 MiB at
    2-byte and 4-byte alignment, including Thumb-bit variants).
  - Whole-ROM literal census: 0 `password`, 0 `cheat`, 0 `secret`, 0 `unlock`, 0 `debug`,
    2 `code` (both `AT_CODE:`/`ST_CODE:`), 1 `sound test`.
- **Inferred (low confidence):** the debug bank was a developer feature removed from the
  release build; the "data erased" full-screen effect genuinely clears the CD bitfield.
  Both are plausible but were not exercised on a save with nonzero CDs.

## 8. Unknowns

- Whether the delete chord clears a nonzero CD collection (the test profile had CDS 000);
  proving this requires earning or injecting a CD, which is a gameplay/state-edit operation,
  not an in-game code.
- The exact screen-state value `0x1A` written by the unreferenced `0x0807BCC` was patched
  into a savestate; the emulator entered a normal stage/gameplay state instead of the debug
  menu, so the intended debug layout could not be rendered.
- Some debug-menu handler functions in `0x0804C000–0x0804F000` appear in a large pointer
  table at `0x08505000–0x08507000`; that table was not fully classified (it is dominated by
  script/entity handlers). No reachable entry to a debug screen was found through it.
- No OPTIONS/settings screen was observed on any reachable menu; if one is gated behind
  story progress it was not reached.

## 9. Tooling

- `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings -t x`, `grep -abo`
- `python3` with `capstone`/`keystone-engine`, `struct`, `zlib` — literal/pointer/BL scans,
  text-bank decoder, savestate `gbAs` dumper (`ssram.py`), savestate patcher (`patchss.py`)
- `arm-none-eabi-objdump -D -b binary -marm -M force-thumb --adjust-vma=0x08000000`
- `mgba -3` (SDL) under `Xvfb :316` + `openbox`; `xdotool` XTEST input helpers (`ui.py`,
  `chords.py`, `combos2.py`); `scrot` + ImageMagick `montage` for screen evidence
- `webfetch` via DuckDuckGo HTML and `web.archive.org` CDX for published sources

**Legal note:** no ROM bytes, graphics, audio, or game text assets are redistributed here;
only addresses, hashes, algorithms, and original analysis scripts are published.
