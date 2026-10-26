# Blades of Thunder (GBA) — Reverse Engineering Report

Report generated from a local ROM analysis on 2026-10-26.
Methodology: [`GBA_REVERSE_ENGINEERING_GUIDE.md`](../../GBA_REVERSE_ENGINEERING_GUIDE.md)

---

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Blades of Thunder/Blades of Thunder.gba` |
| Size | 8 MiB (`0x800000`) |
| Header title | `BLADESOFTHDR` |
| Game code | `BBHE` |
| Maker code | `7V` |
| Software version | `0` |
| MD5 | `2164e4c57a166869961fa1b428fd6ded` |
| SHA-1 | `ce371c336edb5e961878223936de61c40ccb4a97` |
| SHA-256 | `10185cf2a77c8be78ba7657d648c25b0d7c19ec7514b177a62637fb5e451a80c` |

ROM addresses below are `0x08000000 + file_offset`. All findings are tied to
this exact hash; another revision may differ.

**Embedded-header scan.** The 156-byte Nintendo logo occurs exactly once, at
file offset `0x4`; there is a single GBA header at `0x0`. This is not a
multi-game cartridge.

**Header integrity / patch note.** The header is *not* standard:

* complement check at `0xBD` is `0x41`; the computed value is `0x73`;
* header checksum at `0xBE` is `0x0000`; the computed value is `0xFA41`.

The rest of the image is a normal 8 MiB GBA build and the game boots its own
intro (no trainer menu, no "press X for cheats" screen, no scene-group intro).
The invalid header therefore records that the file was altered after mastering
(or is a non-standard dump); it does not add a cheat path. All addresses in
this report were verified against the bytes of this file.

---

## 2. Executive summary

The game has **one developer-intended cheat system**: the `LEVEL CODE` entry on
the title screen. It is a 4-digit decimal password screen with four slots.

* Input space: `0000`–`9999` (`10^4 = 10,000`), alphabet `0`–`9`, fixed length 4.
* The validator is a **closed 30-entry comparison tree**, not a checksum or a
  generator. It converts the four ASCII digits to one decimal integer and
  compares that integer against exactly 30 constants.
* The 30 constants are **10 levels × 3 difficulties**. A match writes
  `difficulty` to `0x03005E48` and `level` to `0x03005E4C`; every other value
  is rejected (return `-1`) and the screen shows no confirmation.
* The full 10,000-value space was executed against the real ARM validator in
  Unicorn: exactly 30 values return `1`. All 30 were then entered in mGBA and
  show the `PRESS (A) TO BEGIN` prompt; `0000`, `1111`, `4266` and `9999`
  show none and `A` is a no-op.

The 30 codes are also the complete list published on GameFAQs (archived
2018-11-26, contributor Cloud20390). The public list is **correct and complete**
for the code values, with one labelling error: its three `Level F` rows are all
marked `easy`. The ROM and RAM prove the actual assignment is:

| Level F code | Published label | Actual |
|---|---|---|
| `9598` | easy | easy (`0x03005E48 = 0`) |
| `1884` | easy | medium (`0x03005E48 = 1`) |
| `9864` | easy | hard (`0x03005E48 = 2`) |

Consequently there is **no accepted code outside the 30**. A novel accepted
value cannot be minted for this title; the space is closed and this is proven by
exhaustion, not inferred. The only unpublished *meaning* is the corrected
difficulty of `1884`/`9864`; `9864` was re-entered as the hard Level F code and
confirmed in game (`difficulty = 2`, `level = 10`, Atlantis/ocean mission).

No button-code system, no hidden debug menu and no second password table were
found. The other screens are ordinary menus: title (New Game / Options /
Credits / Level Code), options (Sound FX and Music sliders only), credits,
difficulty selection (Easy / Medium / Hard), mission briefing and the in-game
pause menu (Resume / Restart / Quit).

---

## 3. How to reproduce

Emulator used: mGBA 0.10.5 (SDL frontend) on Xvfb `:187`, 1024×768×24,
`SDL_AUDIODRIVER=dummy`, scale `-3`.

Default mGBA SDL keymap: `A = x`, `B = z`, `Start = Return`, `Select =
BackSpace`, `L = a`, `R = s`, arrows for the D-pad.

1. Boot the ROM. The intro is a text crawl; press `Start` once and wait about
   three seconds for the title screen.
2. Title screen: `Down` ×3 highlights `LEVEL CODE`; press `A` (`x`).
3. Entry screen: `Up`/`Down` change the selected digit, `Left`/`Right` move
   between the four slots, `A` submits, `B` cancels. Digits wrap `0`↔`9`.
4. Enter a valid code from §6. The line `PRESS (A) TO BEGIN` appears at the
   bottom of the screen as soon as the fourth digit makes the code valid.
   Press `A` to open the briefing, then `A` again to start the mission.
5. Enter `4266`, `1111`, `0000` or `9999`: no prompt appears and `A` does
   nothing.

A savestate at the empty entry screen (`0000`) is kept as
`Blades of Thunder.ss2`; loading it with `F2` makes each test six keypresses.

**Automated test used for §6b.** For each code: load the `0000` savestate, type
the four digits, screenshot. The valid prompt occupies the bottom strip
(`x 140–580`, `y 405–460`). All 30 valid codes produced **2772** near-white
pixels in that strip; the four invalid codes produced **0**. This distinguishes
acceptance from rejection without relying on OCR.

---

## 4. Address map

All addresses are ROM addresses (`file offset + 0x08000000`) unless marked RAM.

| Address | Kind | Meaning |
|---:|---|---|
| `0x080174F0` | ARM code | **Code validator.** Reads 4 ASCII digits at `0x03005E50`, computes the decimal value, 30-way comparison tree. Returns `1` on match, `-1` otherwise. |
| `0x08017A88` | ARM code | Entry-screen draw/update wrapper. Calls the validator and draws `PRESS (A) TO BEGIN` when it returns `1`. |
| `0x08017BF8` | ARM code | Entry-screen initialiser (display mode, font, buffer `0000`). |
| `0x08018000` | ARM code | Entry-screen input handler. `Left/Right` move the cursor, `Up/Down` change a digit, `A` calls `0x080174F0`, `B` cancels. |
| `0x080181CC` | ARM code | Valid-code path: calls `0x08017184`, `0x080140A0`, then `0x080145E0` with `level-1`; sets the next screen handler. |
| `0x08018E00` | ARM code | Input engine: copies `0x04000130` (active-low keypad) to `0x03006258`, keeps the previous frame in `0x0300625A`, clears the register. |
| `0x08018E34` | ARM code | “Newly pressed” test: returns `1` iff `mask & current` and not `mask & previous`. |
| `0x0806AF750` | data | ASCII `LEVEL CODE ` (11 chars + NUL). |
| `0x0806AF75C` | data | First code string `9598`; the 30 codes are 8-byte records (`4 ASCII digits + NUL + 3 pad`). |
| `0x0806AF764` | data | ASCII `PRESS START` (the post-mission screen uses it, not the entry prompt). |
| `0x0806AF770` | data | Codes 2–30, records of 8 bytes, ending at `0x0806AF857`. |
| `0x0806D88` | data | Pointer to `LEVEL CODE `; `0x0806D8C` → `9598`; `0x0806D90` → `PRESS START`; `0x0806DA0`–`0x0806E10` → the remaining 29 code strings. |
| `0x03005E48` | IWRAM (byte) | **Difficulty** written by the validator: 0 easy, 1 medium, 2 hard. |
| `0x03005E4C` | IWRAM (byte) | **Level** written by the validator: 1–10 (`10` is shown as `Level F`). |
| `0x03005E50` | IWRAM (4 bytes) | Input buffer, ASCII digits (`39 35 39 38` for `9598`). |
| `0x03005E54` | IWRAM (byte) | Scratch digit / previous value used by the entry handler. |
| `0x03005E56` | IWRAM (byte) | Cursor position 0–3. |
| `0x030058E4` | IWRAM (byte) | Validation status: valid path leaves 0; invalid path writes 4 or 5 before returning `-1`. |
| `0x03005916` | IWRAM (byte) | Level index `level-1` on the briefing/start path. |
| `0x03006258` | IWRAM (halfword) | Current keypad state (active-low). |
| `0x0300625A` | IWRAM (halfword) | Previous-frame keypad state. |

The code table is the only run of adjacent 4-digit ASCII tokens in the ROM
(§9). There is no second table and no algorithmic encoder.

---

## 5. Algorithm

### 5.1 Entry and validation

```
b0..b3 = bytes at 0x03005E50           ; ASCII '0'..'9'
v = (b0-'0')*1000 + (b1-'0')*100 + (b2-'0')*10 + (b3-'0')

switch (v) {
case 0x10A9: diff=0; level=1;  return 1;   // 4265
case 0x1B14: diff=1; level=1;  return 1;   // 6932
case 0x07BB: diff=2; level=1;  return 1;   // 1979
... 27 more cases ...
default:
    status = (cursor_at_0x03005E48 == 0) ? 5 : 4;  // 0x030058E4
    return -1;
}
```

The compiler emitted a binary search tree, not a jump table. Each comparison is
`cmp r2, #const` on the decimal value; `beq` goes to that code's leaf, and
`bne`/`bgt` descends. The leaf writes the two bytes and returns `1`; the shared
failure path is at `0x0801773C`. The exact value computation in ARM is:

```
r0 = b[0]; r3 = b[1]; ip = b[2]; r2 = b[3]
r0 = r0*5;  r3 = r3*5;  r3 = r3*5
r2 = r2 + r0*2 + r3*4
ip = ip*125
r2 = r2 + ip*8 - 0xD050          ; 0xD050 = 0x30*1000 + 0x30*100 + 0x30*10 + 0x30
```

so `r2` is exactly the decimal value. The subtraction of `0xD050` removes the
ASCII bias.

### 5.2 What happens on a match

`0x08018000` calls the validator on `A`. On return `1` it branches to
`0x080181CC`:

```
bl 0x08017184            ; screen transition / sound
bl 0x080140A0            ; palette/sprite setup
r0 = byte[0x03005E4C] - 1
bl 0x080145E0            ; store level index, load briefing record
*0x03006E78 = 0x080147D4 ; next state handler
```

`0x080145E0` writes `level-1` to `0x03005916` and uses the record table pointer
at `0x03005918`; the difficulty byte at `0x03005E48` is consumed by the level
loader (confirmed by the New Game difficulty path, which writes the same byte:
easy 0, medium 1, hard 2).

### 5.3 Why there is no second format

The validator reads exactly four bytes and compares the resulting integer to
constants. It reads no checksum, no global table pointer and no other state
except the buffer. It cannot accept a value outside its 30 leaves, and it cannot
generate a code. The input handler clamps each digit to `'0'`–`'9'` before
validation, so alternate byte values cannot be reached through the UI.

---

## 6. Tables

### 6.1 The 30 accepted codes (actual difficulty and level)

| Level | Easy | Medium | Hard |
|---:|---|---|---|
| 1 | `4265` | `6932` | `1979` |
| 2 | `7332` | `3682` | `2034` |
| 3 | `6578` | `5892` | `7809` |
| 4 | `7213` | `4468` | `6776` |
| 5 | `8234` | `1127` | `9054` |
| 6 | `9322` | `9902` | `4311` |
| 7 | `1279` | `2332` | `8282` |
| 8 | `5682` | `8658` | `2468` |
| 9 | `3211` | `7745` | `1410` |
| F (10) | `9598` | `1884` | `9864` |

ROM table order is by difficulty group (easy, medium, hard) and, inside each
group, by descending level F→1. That is why the table starts `9598, 3211,
5682, …, 4265, 1884, …` and the published list (ordered by level) looks
different.

### 6.2 Field layout

| Field | RAM | Width | Values | Meaning |
|---|---|---:|---|---|
| Difficulty | `0x03005E48` | 1 byte | 0,1,2 | easy, medium, hard |
| Level | `0x03005E4C` | 1 byte | 1–10 | level number; 10 displayed as F |
| Digits | `0x03005E50` | 4 bytes | `'0'`–`'9'` | input buffer |
| Status | `0x030058E4` | 1 byte | 0/4/5 | valid / rejected variants |

No checksum, parity, reserved bit or wildcard exists. The only representation
is the decimal value itself.

### 6.3 Published list and the Level F correction

Source: GameFAQs `Blades of Thunder – Cheats`, archived 2018-11-26:
`http://web.archive.org/web/20181126025226/https://gamefaqs.gamespot.com/gba/925884-blades-of-thunder/cheats`
(contributor Cloud20390). Direct GameFAQs access returns HTTP 403; the archive
snapshot was used.

The page lists all 30 code values and labels Levels 1–9 correctly. Its last
three rows are all `Level F(easy)`. The ROM writes difficulty `0,1,2` for
`9598, 1884, 9864` respectively, and the in-game New Game path writes the same
byte for Easy/Medium/Hard; the correct labels are therefore easy / medium /
hard.

---

## 6b. Enumeration

**Space definition.** Alphabet `0`–`9`, length 4, no checksum, no reserved
values: `10^4 = 10,000` representable inputs. The accepted set is a lookup of
30 constants (0.30 % of the space). Table size: 30 strings at
`0x0806AF75C`, 8-byte stride.

**Exhaustive validator model.** `blades_enum.py` (beside this report) maps the
ROM at `0x08000000`, IWRAM at `0x03000000`, writes
the four ASCII digits to `0x03005E50`, and executes the real ARM function at
`0x080174F0` in Unicorn until it returns. All 10,000 inputs were run. Exactly
30 returned `1`; the set is identical to §6.1 (30/30). The other 9,970 returned
`-1` and wrote status 4 or 5 to `0x030058E4`.

**In-game verification.** All 30 codes were typed on the title-screen entry
screen. Each showed `PRESS (A) TO BEGIN` (2772 white pixels in the bottom
strip). `0000`, `1111`, `4266` and `9999` showed no prompt (0 white pixels),
and pressing `A` left the screen unchanged. `4266` is a deliberate one-digit
off-by-one from the valid `4265`; `9999`/`0000` are the space bounds; `1111` is
a repeated-digit value with no table match. This is the rejection bound: the
format can express these values, the game rejects them.

**Novel code.** There is **no accepted value outside the 30**; the public list
and the ROM table are the same set. This is a proven closure, not an untested
negative:

* every 4-digit value was executed against the validator;
* the only cluster of five or more adjacent 4-digit tokens in the 8 MiB image is
  the 30-entry table at `0x0806AF75C`;
* the only code-entry screen is the title `LEVEL CODE` screen; no other RAM
  address is compared against four digits.

The closest deliverable to an “unpublished code” is therefore a **corrected
difficulty reading** that appears in no published list:

* `9864` = **hard Level F**. The archived GameFAQs list labels it easy. Entering
  `9864` produced `0x03005E48 = 2` (hard), `0x03005E4C = 10` (Level F), the
  `PRESS (A) TO BEGIN` prompt, and the Atlantis/ocean mission after `A`.
* `1884` = **medium Level F**, likewise mislabelled easy by the published list.

These are new *meanings* for existing values, not new values; the code space
itself is closed. Anyone can reproduce them with `blades_code.py`:
`decode("9864") -> (2, 10)`.

**Bounds proven by rejection.** `4266` (nearest non-code to a valid code),
`9999` (maximum), `0000` (minimum) and `1111` are all rejected in the emulator;
the validator returns `-1` for each in the model as well. No value with a
leading zero, repeated digits or an adjacent-digit change is accepted unless it
is one of the 30 table entries.

---

## 7. Validation evidence

**Observed (emulator screenshots / RAM).**

* Title menu: `NEW GAME`, `OPTIONS`, `CREDITS`, `LEVEL CODE`
  (`title_menu.png`, `menu_levelcode.png`).
* Entry screen: four digit slots, `0000`, cursor movement and digit wrap
  (`levelcode_screen.png`, `lc_up1.png`, `lc_right_up.png`).
* Valid code `4265`: prompt `PRESS (A) TO BEGIN` (`v_4265.png`); all 30 codes
  produced the same prompt (`v_*.png`).
* Invalid `4266`, `9999`, `0000`, `1111`: no prompt; `A` no-op
  (`v_4266.png`, `v_9999.png`, `v_0000.png`, `v_1111.png`).
* `9864`: prompt, then briefing, then the ocean/Atlantis mission
  (`b_m9864.png`, `mission9864_play.png`); savestate RAM
  `0x03005E48 = 02`, `0x03005E4C = 0A`, buffer `39 38 36 34`.
* New Game difficulty: selecting Easy/Medium/Hard writes `0x03005E48 = 0/1/2`;
  savestates `ss6/ss7/ss8` differ at exactly `0x03005E48` and `0x03005E55`.
* Pause menu: `RESUME`, `RESTART`, `QUIT` (`pause2.png`); Quit returns to the
  title (`pause_quit2.png`).
* Options: only `SOUND FX` and `MUSIC` sliders (`options.png`).
* Credits: scrolling text, no input prompts (`credits4.png`).

**Derived (instruction sequence).**

* Validator at `0x080174F0` is a binary comparison tree over the decimal value,
  with 30 equality leaves and one shared `-1` failure path.
* Input engine `0x08018E00`/`0x08018E34`; the entry handler `0x08018000` reads
  `A`, `B`, `Left`, `Right`, `Up`, `Down` and submits on `A`.
* The 30 strings at `0x0806AF75C` are 8-byte records; the pointer array at
  `0x0806DA0` covers entries 2–30.
* The only adjacent 4-digit ASCII cluster in the image is that table (29
  tokens at `0x0806AF770` plus `9598` at `0x0806AF75C`).

**Inferred (not fully exercised).**

* Difficulty is stored and passed to the level loader; the *gameplay* effect
  (enemy count/health) was not isolated. Paused screenshots of Easy/Medium/Hard
  Level 1 are visually identical, which is consistent with difficulty changing
  enemy stats rather than the map.
* The displayed code after completing a mission was not observed (it would
  require a full mission); the table order suggests the game shows one code per
  level, most likely the easy group.

---

## 8. Unknowns

* The exact gameplay effect of the difficulty byte (beyond the RAM value) was
  not measured. This does not affect the code space.
* Why the header complement/checksum are invalid is unknown; no trainer or
  patch payload was found, and no code path depends on the header bytes.
* The post-mission “level code shown” index was not observed. It does not add
  accepted values: the validator is closed.
* No novel accepted code exists for this title. The only unpublished result is
  the corrected Level F difficulty labels (§6b). This is a bounded negative,
  not a skipped test.

---

## 9. Tooling

Installed/used: `mgba-sdl` 0.10.5, `binutils-arm-none-eabi` (`objdump`),
`gdb-multiarch` (not needed in the final path), `Xvfb`, `openbox`, `xdotool`,
`scrot`, ImageMagick, tesseract 5.5.0, Python 3.13, Capstone 5.0.7,
Unicorn 2.1.4, Pillow.

Scripts (in `/tmp/opencode/blades/`, key ones copied beside the report):

| File | Purpose |
|---|---|
| `ds.py` | Capstone ARM/Thumb disassembler for a ROM range. |
| `enum_validator.py` / `blades_enum.py` | Unicorn execution of `0x080174F0` for all 10,000 inputs; prints the 30 accepted values and the two field bytes. |
| `blades_code.py` | Offline table/decode/encode model (`decode('9864') -> (2,10)`). |
| `entercode.py`, `one.py` | Menu navigation, digit entry, screenshots. |
| `verify_all.py`, `verify_rest.py` | In-game 30-code acceptance + 4-code rejection harness (white-pixel prompt detector). |
| `key.py` | xdotool key helper. |

Screenshots referenced above were captured during this run in
`/tmp/opencode/blades/` (e.g. `title_menu.png`, `levelcode_screen.png`,
`v_4265.png`, `v_4266.png`, `mission9864_play.png`); the durable evidence is
the address map, the validator model and the reproducible input path.

Key emulator commands:

```bash
Xvfb :187 -screen 0 1024x768x24 &
DISPLAY=:187 openbox &
DISPLAY=:187 SDL_AUDIODRIVER=dummy mgba -3 "Blades of Thunder.gba" &
W=$(DISPLAY=:187 xdotool search --name mGBA | head -1)
DISPLAY=:187 xdotool windowfocus "$W"
```

Negative-space counts (for the “no second system” claim):

* `strings -t x -n 4` → 83,040 lines.
* `PASSWORD`, `CHEAT`, `DEBUG`, `SECRET`, `UNLOCK`, `INVALID`, `TO BEGIN`:
  0 literal ASCII hits each.
* `CODE`: 5 hits, all inside `CODENAME`/`LEVEL CODE`; `LEVEL`: 4 hits;
  `MISSION`: 7 hits (score/briefing labels).
* 4-digit ASCII tokens: 2,268; only **one** cluster of ≥5 adjacent tokens — the
  30-entry code table.
* u16 runs of ≥3 button masks: 962 (all inside ARM instruction streams or
  graphics); active-low u16 runs: 71 (all graphics/audio). No mask table with a
  code xref and no per-screen sequence index was found.
* The input poller `0x08018E34` is installed by six UI routines (file offsets
  `0x7718`, `0x147A8`, `0x17FC4`, `0x18204`, `0x18528`, `0x1886C`); the reachable
  screens were walked visually and every one is a normal menu.

**Legal note.** No ROM, extracted graphics, music or text is redistributed
here. Only hashes, addresses, algorithms, the 30 published password strings
and our own tool code are recorded.

---

## 10. Reproduction checklist

- [x] ROM hashed and header parsed; header anomaly recorded.
- [x] Embedded-header scan: one header only.
- [x] Strings searched; no password/cheat/debug strings.
- [x] Published codes located (archived GameFAQs) and all 30 tested in game.
- [x] Every menu walked: title, options, credits, difficulty, briefing, level
      code, pause.
- [x] Validator located, disassembled and reimplemented.
- [x] Whole 10,000-value space executed against the real validator.
- [x] Rejection bounds tested in game (`4266`, `9999`, `0000`, `1111`).
- [x] Novel meaning found and confirmed (`9864` = hard Level F) while proving
      that no novel accepted value exists.
- [x] Report written next to the ROM; `roms/INDEX.md` intentionally not edited.
- [x] Emulator/display processes stopped by PID.
