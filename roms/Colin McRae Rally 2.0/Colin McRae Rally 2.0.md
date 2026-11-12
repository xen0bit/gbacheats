# Colin McRae Rally 2.0 (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Colin McRae Rally 2.0.gba` |
| Size | 4,194,304 bytes (4 MiB) |
| Header title | `MCRAE RALLY2` |
| Game code / maker | `ACME` / `41` |
| Version | 0x00 |
| Complement check | 0x98 (valid for bytes 0xA0–0xBC) |
| Header checksum | `0x0000` (rebuilt-header artefact; complement is intact) |
| Entry word | `0xEA00002E` (stock ARM branch to `0x080000C0`; no cracktro) |
| MD5 | `6d0aef7b4a8ab01db3c27284df771a81` |
| SHA-1 | `c29cb5e9843816369164a6f60486dc920a86bc6b` |
| SHA-256 | `6fc48562ddfdc3297a39922e43fd440bae8e035084937a814133199cea72f04c` |
| Developer / publisher | Spellbound / Ubi Soft (GBA SKU, 2002) |

A second complete GBA header is embedded at file `0x3A8020` (logo at `0x3A8024`,
title `MCRAE RALLY2`, code `ACME`, entry `0xEA000061` → `0x083A80E4`). It is the
single-pak link (multiboot) slave image, not a second playable game; its code is an
ARM link stub and it is never booted from the cartridge header. No trainer, patch,
or appended executable was found.

## 2. Executive summary

**This GBA SKU has no password, cheat-code, or hidden debug-menu system.**
The front end is a closed, data-driven set of 32 screens whose complete widget
inventory is present in ROM and was enumerated (218 text-bearing widgets; §6).
The only user text input in the whole game is a **three-character driver name
tag** on the profile/car-select screen. Its input handler accepts exactly
`A–Z`, `.` and space (28 symbols), refuses a leading space, and stops at three
characters (buffer `0x030045F4`, length word `0x030045F2`, handler `0x08008FF4`).
There is no comparison of that buffer with any constant and no flag write
downstream of it; the accept handler only copies the three bytes into the
profile record at `0x020287xx`.

The widely published Colin McRae Rally 2.0 name codes (`ONECAREFULOWNER`,
`GREATNEWS`, `ALLTHEBUTTONS`, `RORRIMSKCART`, …) are **PC/PlayStation driver-name
codes**. All 33 published literals were searched in this image in ASCII,
upper-case, lower-case, UTF-16LE/BE and 5-bit packed form: **0 of 33 occur**.
They are also inexpressible on this SKU: every published code is 6–16
characters, while the only text field accepts at most 3.

The game’s developer-intended extras are **unlockables earned by championship
results** (9 cars, 6 rally countries, 6 arcade circuits, 3 difficulty levels),
not codes. The only hidden front-end item is an unlisted `credits` entry on the
main menu (`0x1F0F8C`, zero draw size, handler `0x08008DF5`).

## 3. How to reproduce

* Emulator: mGBA 0.10.5 SDL (`mgba -3`), `SDL_AUDIODRIVER=dummy`, Xvfb `:259`.
* Keymap used: A = `x`, B = `z`, Start = `Return`, Select = `BackSpace`,
  L = `a`, R = `s`, d-pad = arrows. Verified against `KEYINPUT` (`0x04000130`):
  idle `0x3FF`, Start held `0x3F7`.
* Static work: `strings -t x -n 4`, Capstone/`objdump -M force-thumb`, and a
  Python parser for the front-end tables at `0x1F0000`.
* Relevant searches (all from the ROM directory):

```bash
strings -t x -n 4 "Colin McRae Rally 2.0.gba" | grep -iE \
  "password|cheat|debug|secret|unlock|gallery|triche|schummel|kennwort"
grep -abo "ONECAREFULOWNER" "Colin McRae Rally 2.0.gba"   # no hit
```

* Front-end table: screen vector at file `0x1EEA04`; widget records from
  `0x1F0000`; keyboard at `0x1F2074`; name field at `0x1F2008`.

## 4. Address map

| Address (ROM) | Contents |
|---|---|
| `0x080000C0` | stock crt0 (ARM) |
| `0x08002DD0` | keypad poll: reads `0x04000130`, `eor 0x03FF`, stores held/new at `0x020280BC` / `0x020280BE` |
| `0x08008FF4` | name-field append handler (alphabet/length check) |
| `0x080090A4` | name-field delete handler |
| `0x08009464` | name-field accept: copies 3 bytes into profile records |
| `0x08008DF5` | hidden `credits` action on the main menu |
| `0x081EEA04` | 32-entry screen descriptor vector |
| `0x081F0ED4` | main-menu screen struct (widgets from `0x1F0EEC`) |
| `0x081F1128` | Rally mode-select screen |
| `0x081F1344` | Arcade mode-select screen |
| `0x081F1680` | number-of-players screen |
| `0x081F2498` | car-select + name-entry screen (keyboard `0x1F2070`) |
| `0x081F2960` | transmission screen |
| `0x081F2B04` | country select |
| `0x081F2D58` | stage select |
| `0x081F2F98` | difficulty select |
| `0x081F313C` | New / Load |
| `0x081F335C` | Options |
| `0x081F3210` | Controls |
| `0x08234EC0`–`0x08236350` | English UI string bank |
| `0x082363B4`–`0x082378FF` | French UI string bank |
| `0x08237900`–`0x08238C00` | German UI string bank |
| `0x08236140` | `YOU HAVE UNLOCKED\n %s` |
| RAM `0x020280A0` | input state block (`+0x1C` held, `+0x1E` new) |
| RAM `0x030045EC` | first-key flag for the name field |
| RAM `0x030045F2` | name length counter (0–3) |
| RAM `0x030045F4` | 3-byte name buffer (also bound to `0x1F2030/50/68` 1-char widgets) |
| RAM `0x020287xx` | profile name slots written by the accept handler |

## 5. Algorithm (name field)

```
append(char c):                       # 0x08008FF4
    if key_state == first_press:      # [0x030045EC] bit 0
        [0x030045F2] = 0              # clear length
        [0x030045EC] |= 1
    n = [0x030045F2]
    if n == 0 and c == ' ': return    # no leading space
    if n <= 2:
        [0x030045F2] = n + 1
        [0x030045F4 + n] = c
    # n == 3: writes are ignored; control key returns UI to accept state

accept():                              # 0x08009464
    for slot in 0..3:
        p = 0x02028700 + slot*0x40
        p[3] = byte0; p[2] |= 0x41
        ...
    # no comparison, no game-flag write
```

Input space: 28 symbols (`A`–`Z`, `.`, ` `), lengths 1–3, leading space
forbidden → `28 + 784 + 21952 − (1 + 28 + 784) = 21,951` accepted strings
(plus the empty string left by the delete key). The field is a label, not a
validator: no `strcmp`/`memcmp` against a constant exists for the buffer, and
its only consumer is the profile record.

## 6. Tables

### 6.1 Name-keypad (file `0x1F2074`, stride `0x1C`)

| Index | Symbol | Handler |
|---:|---|---|
| 0–25 | `A`–`Z` (0x41–0x5A) | append `0x08008FF5` |
| 26 | `.` (0x2E) | append |
| 27 | space (0x20) | append (rejected when length 0) |
| 28 | control (char 0x00, flags 3) | accept `0x08009445` |
| 29 | control (char 0x00, flags 0) | delete `0x080090A5` |

### 6.2 Front-end screens (all 32, from `0x081EEA04`)

`Main menu`, `Rally mode`, `Arcade mode`, `Players`, `Car/name select`,
`Transmission`, `Country select`, `Stage select`, `Difficulty`, `New/Load`,
`Options`, `Controls`, `High scores`, plus the in-race pause/service/HUD,
link-error, results/trophy and multi-player hand-off screens. The main menu
contains `Single Pak Link`, `rally`, `arcade`, `options`, and the hidden
`credits` record. No screen contains a password/cheat/debug widget.

### 6.3 Cars (file `0x1F0220`, 9 pointers)

Ford Focus, Mitsubishi Lancer, Toyota Corolla, Subaru Impreza, Ford Puma,
Lancia Integrale, Lancia Stratos, Ford Cosworth, Mitsubishi Lancer Evo.
Stats (from `0x2355E0`): Focus 300 bhp/1230 kg 4WD; Lancer 300/1260 4WD;
Corolla 300/1230 4WD; Impreza 300/1230 4WD; Integrale 345/1149 4WD;
Cosworth 320/1190 RWD; Stratos 500/900 RWD; Puma 300/1040 4WD.

### 6.4 Countries (file `0x1F05E0`)

Finland, France, Sweden, Australia, Kenya, United Kingdom; three difficulty
levels (Novice, Intermediate, Expert). Cars and stages are awarded by
championship placement (`FINISH IN THE TOP 6 TO QUALIFY…`, gold/silver/bronze
trophy strings at `0x2360E0`–`0x2361E0`, `YOU HAVE UNLOCKED` at `0x236140`).
These are game-progress rewards, not codes.

## 6b. Enumeration

* **Code/password space: empty.** No hard-coded code table, no generator, no
  decoder, no entry screen. Search space: all 4 MiB for
  `password|passw|cheat|code|debug|secret|triche|schummel|kennwort` (ASCII,
  lower-case and upper-case) → 0 hits; 218 front-end text widgets → 0 code
  fields; 32 screen descriptors → 0 code screens.
* **Text-entry space:** 28 symbols × length 1–3 = 22,764 raw strings; leading
  space and over-length forms are rejected, leaving **21,951** accepted strings.
  This space does not index any game flag.
* **Published-code test:** 33 published PC/PS driver-name codes
  (`onecarefulowner`, `hellocleveland`, `allthebuttons`, `greatnews`, `minime`,
  `evilevo`, `letmewin`, `morrismode`, `gofasterstripes`, `garywildass`,
  `nuttynets`, `wavyourlefts`, `wheelybig`, `boingboingboing`, `shinybuttons`,
  `bouncybouncybouncy`, `curryforme`, `eatthis`, `oohnice`, `offroad`,
  `jobinitaly`, `jimmyscar`, `coolestcar`, `rorrimskcart`, `greatballsof`,
  `rubbertrees`, `easyroller`, `moonlander`, `neuralnightmare`, `rocketfuel`,
  `prunejuice`, `fridayschild`, `turnontheice`) → **0/33 present** in ASCII,
  upper, lower, UTF-16LE/BE, or 5-bit LSB/MSB packing. All are 6–16 characters
  and therefore cannot be expressed by the 3-character field.
* **Bounds proven by rejection (model level):** a fourth character is refused
  by the `n <= 2` guard; a leading space is refused by the `n == 0 && c == ' '`
  test; digits, punctuation other than `.`, and lower-case letters have no
  keypad widget and cannot be entered.
* **Novel value:** the enumeration produces values absent from every published
  list, e.g. `ZQ.` (three legal symbols). It is accepted as a profile tag and
  has no gameplay effect; it is listed here as the novel member of the text
  space, not as a cheat.
* **Hidden content:** main-menu `credits` (`0x1F0F8C`, handler `0x08008DF5`) —
  the only front-end entry with zero draw size and no published description.

## 7. Validation evidence

**Observed**
* ROM boots in mGBA 0.10.5; the 3D intro/attract sequence renders and the
  frame counter at `0x03002FA4` advances at ~62 counts/s for 150 s.
* `KEYINPUT` reads `0x3FF` idle and `0x3F7` with Start held; the ROM’s poll
  routine at `0x08002DD0` performs `0x03FF ^ KEYINPUT` and writes the held/new
  words at `0x020280BC/0x020280BE`.
* The game’s own input mirror is not updated after the first ~10 s in mGBA
  0.10.5 (PC sampled at `0x1C4` in the HLE BIOS, `IE=0x2005`, `IME=1`), i.e. the
  core parks in a BIOS idle path in this build. VBA 1.8 runs the same image with
  PC in ROM (`0x0810B8B0`), confirming the image is not broken.
* VRAM-derived frames (BG0/BG1 4bpp, palette from the savestate) show the title
  artwork and the attract fade; no menu text was reached by scripted Start/A
  input in either emulator, so no in-game keypress claim is made beyond boot.

**Derived**
* The 32-screen table and 218 widgets are read directly from ROM after parsing
  the `0x20`-byte record format and the `0x1EEA04` vector.
* The 3-character limit, 28-symbol alphabet, leading-space rule and buffer
  addresses are derived from the disassembly of `0x08008FF4`, the keyboard
  records at `0x1F2074`, and the three 1-char display widgets at `0x1F2030`.
* The absence of any cheat string/table/screen follows from the complete string
  and widget enumeration, not from a failed search alone.

**Inferred**
* Car/track unlock order and the exact save bits were not isolated; the report
  only states the reward mechanism proved by the trophy/unlock strings and the
  9-car/6-country data tables.

## 8. Unknowns

* Exact EEPROM layout and the per-car/per-stage unlock bytes (the 512-byte
  `.sav` was created by the emulator on boot and remained erased `0xFF`).
* Why mGBA 0.10.5 parks this image in the HLE BIOS at ~10 s; not a ROM defect
  (VBA executes game code), but it blocked an interactive front-end walk in
  that emulator.
* The trigger for the zero-size `credits` main-menu entry (likely a completion
  or button easter egg); its handler is known but not exercised.

## 9. Tooling

* `strings`, `xxd`, `grep -abo`, `arm-none-eabi-objdump`, Capstone 5.
* Python parsers for the front-end widget/screen tables and for the name
  handler; savestate reader for mGBA (`gbAs` zlib chunk) and VBA (`.sgm`) with
  palette/VRAM extraction to ASCII frames (no image files used).
* mGBA 0.10.5 SDL, Xvfb `:259`, openbox, xdotool. VBA 1.8.0 used as a
  second-core cross-check.
* Legal note: no ROM, graphics or game text is redistributed; only addresses,
  algorithms and hashes are reported.
