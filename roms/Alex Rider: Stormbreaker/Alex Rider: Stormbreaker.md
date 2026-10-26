# Alex Rider: Stormbreaker (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Alex Rider: Stormbreaker.gba` |
| Size | 4,194,304 bytes (4 MiB, `0x400000`) |
| Header title | `ALEX RIDER` |
| Game code | `BAWE` (Europe, multilingual) |
| Maker code | `78` |
| Software version | 0 |
| Entry branch | `0xEA00002E` (ARM, → `0x080000C0`) |
| MD5 | `4b5aee04f0f61c5ef9343524bd2ac1d4` |
| SHA-1 | `e9ba9d340701173ccd3a4d279630e1541ed96a73` |
| SHA-256 | `16117cd914b7088936c827cdeb7dbe5be382148a77add40fdd1c6a63f9667f98` |

Embedded-header scan: the 156-byte Nintendo logo occurs exactly once, at file
offset `0x4` (header base `0x0`). This is a single GBA image, not a
multi-game cartridge. Header bytes `0xB2 = 0x96`, complement `0xBD = 0x03`.

## 2. Executive summary

The game has one developer-intended cheat system, reached from **Main Menu →
Cheats**. It is a **10-slot table of fixed passphrases**, not a password
generator:

* Slots `0..9` each own one expected string. Four are personal names
  (`JESSICA PARKER`, `VICTORIA PARR`, `SARYL HIRSCH`, `RENATO CELANI`) and six
  are seven-digit numbers (`6943059`, `9603717`, `6894098`, `5204025`,
  `4298359`, `9785711`).
* The player types the string on an on-screen keypad. The typeable alphabet is
  38 symbols: `A–Z`, `0–9`, `!` and space (the space key is drawn as `-`), plus
  backspace and enter. Only upper case exists.
* The validator is a strict `strcmp(input, expected)` against the English text
  bank, **slot-bound**: a correct code entered under the wrong cheat name is
  rejected.
* On success the slot's RAM record becomes `{unlocked, enabled}` and a green
  tick appears next to the code; on failure the field is blanked and no tick is
  shown. Pressing A on an already-unlocked slot toggles its `enabled` byte.
* Enabled slots are summed into a bitmask at `0x0200018C` (bit *i* = slot *i*),
  which gameplay code tests.
* Unlocks live in EWRAM for the session. The 512-byte EEPROM image was still
  blank (`0xFF`) after testing, so persistence across a power cycle is **not
  proven** (see §8).

The table is the **entire** code space. There is no second, algorithmic format,
no checksum, no encoder/decoder pair, and no hidden 11th entry: the u16
code-ID table at `0x0837A9A2` contains exactly ten entries and ends where the
keypad alphabet begins. All ten strings are already on the published GBA cheat
lists, so **no unpublished valid code exists for this ROM**. This is a bounded
negative, not a failure to search: §6b enumerates the whole space and proves the
bound with five in-game rejections. Five other "cheat-like" surfaces that would
matter on other titles (password screen, level select, debug menu, gallery,
sound test) are absent from the 4 MiB image by string count (§6b, §7).

## 3. How to reproduce

Emulator: mGBA 0.10.5 SDL (`/usr/games/mgba`), 3× scale, under
`Xvfb :129` + `openbox`, `SDL_AUDIODRIVER=dummy`.

Default SDL keymap used throughout: **A = `x`**, **B = `z`**, **Start =
`Return`**, **Select = `BackSpace`**, D-pad = arrows. Hold every key ≥ 100 ms;
the keypad ignores a tap shorter than a frame.

Reach the cheat screen:

1. Boot. Title screen: “Press START”. Press Start.
2. Main Menu has three entries: `New Game`, `Options`, `Cheats`.
3. Select `Cheats` and press A. The entry screen appears: 8×5 keypad on top,
   the selected cheat name and the code field below.
4. **Selecting a slot:** while the name is shown, Up/Down changes the slot
   (wraps 9→0). On an *empty* slot, A moves focus to the keypad and clears the
   field. On an *already unlocked* slot, A toggles `Enabled?`.
5. **Typing:** D-pad moves the keypad cursor (5 rows × 8 columns, wrapping),
   A types the highlighted symbol. Position `(4,5)` is the space key (glyph
   `-`), `(4,6)` is backspace, `(4,7)` is enter/accept.
6. **Accept:** move to `(4,7)` and press A.
   * Accepted: the field keeps the code and a green tick appears in the box at
     the right; the slot's RAM record becomes `01 01`.
   * Rejected: the field is cleared and the box stays empty; the RAM record is
     unchanged.

The ten accepted inputs (slot → name → code):

| Slot | Cheat name | Accepted code |
|---:|---|---|
| 0 | Infinite Health | `JESSICA PARKER` |
| 1 | One Hit K.O. | `VICTORIA PARR` |
| 2 | Fast Downtimer | `SARYL HIRSCH` |
| 3 | Slow Bullets | `RENATO CELANI` |
| 4 | Extra Enemy Health | `6943059` |
| 5 | Extra Enemy Damage | `9603717` |
| 6 | Undetectable to Bugs | `6894098` |
| 7 | Undetectable to Guards | `5204025` |
| 8 | Dizzy Enemies | `4298359` |
| 9 | Chase Passthrough | `9785711` |

The space in the four names is typed with the key drawn as `-` (position 4,5).

Screenshots referenced below are stored next to this report as
`Alex Rider - *.png` (720×480, the 240×160 viewport at 3×).

## 4. Address map

`rom = 0x08000000 + file_offset`.

| Item | File offset | ROM address | Notes |
|---|---:|---:|---|
| Cheat name text-ID array (10 × u16) | `0x37A98E` | `0x0837A98E` | `0x0C,0x0E,…,0x1E` |
| Cheat code text-ID array (10 × u16) | `0x37A9A2` | `0x0837A9A2` | `0x0D,0x0F,…,0x1F` |
| Keypad symbol table (40 bytes) | `0x37A9B6` | `0x0837A9B6` | `"A–Z0–9! "` + `0x22` + `0x0A` |
| Text bank base | `0x3B9C60` | `0x083B9C60` | bank header, language stride 8 |
| English text offset table | `0x3B9C88` | `0x083B9C88` | `ID*4` → byte offset |
| Cheat entry screen / validator | `0x1FB40`–`0x1FC10` | `0x0801FB40`–`0x0801FC10` | bitmask builder + input handler |
| Keypad char fetch + submit | `0x1FC5E`–`0x1FCF8` | `0x0801FC5E`–`0x0801FCF8` | slot→text ID, `strcmp`, flag write |
| Strict string compare | `0x16864` | `0x08016864` | only caller: `0x0801FCA2` |
| Text-ID resolver | `0x1C210` | `0x0801C210` | `ID → ROM string`, English fallback |
| Cheat state table (EWRAM) | — | `0x02006BE8` + `4*slot` | `{u8 unlocked, u8 enabled, 0, 0}` |
| Keypad cursor row / col | — | `0x02006B37` / `0x02006B36` | 0..4 / 0..7 |
| Selected slot index | — | `0x02006B39` | 0..9, wraps |
| Input buffer | — | `0x02006C18` | NUL-terminated ASCII |
| Enabled bitmask | — | `0x0200018C` | bit *i* = slot *i* |

Code strings (English bank), all NUL-terminated:

| Slot | Text ID | File offset | String |
|---:|---:|---:|---|
| 0 | `0x0D` | `0x3BA1C3` | `JESSICA PARKER` |
| 1 | `0x0F` | `0x3BA1DF` | `VICTORIA PARR` |
| 2 | `0x11` | `0x3BA1FC` | `SARYL HIRSCH` |
| 3 | `0x13` | `0x3BA216` | `RENATO CELANI` |
| 4 | `0x15` | `0x3BA237` | `6943059` |
| 5 | `0x17` | `0x3BA252` | `9603717` |
| 6 | `0x19` | `0x3BA26F` | `6894098` |
| 7 | `0x1B` | `0x3BA28E` | `5204025` |
| 8 | `0x1D` | `0x3BA2A4` | `4298359` |
| 9 | `0x1F` | `0x3BA2BE` | `9785711` |

Keypad table bytes (`0x0837A9B6`):

```
41..5A  A–Z
30..39  0–9
21      '!'
20      space   (rendered as '-' on screen)
22      backspace (handler compares the fetched byte with 0x22)
0A      enter
```

## 5. Algorithm

```
# entry screen, slot = [0x02006B39] in 0..9
expected_id = u16[0x0837A9A2 + 2*slot]      # 0x0D,0x0F,...,0x1F
expected    = text_resolve(expected_id)     # 0x0801C210

# 0x0801C210: table_base = BANK + ((u32[BANK+8+8*lang] >> 2) << 2)
#              p = table_base + u32[table_base + 4*id]
#              if *p == 0: re-resolve through the English table (BANK+0x28)
# This is why all localized cheat-code entries are empty but still work.

if strcmp(input_buffer, expected) == 0:     # 0x08016864, strict byte compare
        table[slot].unlocked = 1
        table[slot].enabled  = 1
        show green tick, keep the typed code
else:
        clear the input field, no tick
```

`0x08016864` is a plain C `strcmp`:

```
r2 = a; r3 = b
loop:
  if *(r2-1) == 0: return 0        # both strings ended
  c1 = *r2++; c2 = *r3++
  if c1 == c2: goto loop
  return c1 - c2
```

There is **no** case folding, trimming, prefix compare or wildcard on the input
path. (A separate routine `0x080167CC` normalizes the *expected* string —
lower-case → upper-case and UTF-8 accented characters — before comparison; the
English codes are already upper-case, so it is a no-op for them.)

Enable bitmask (`0x0801FB40`), rebuilt when the cheat screen is left:

```
flags = 0
for i in 0..9:
    if table[i].enabled: flags |= 1 << i
[0x0200018C] = flags
```

Observed values: slots 0 and 6 enabled → `0x0041`; slots 0,4,5,6,7,8,9 enabled
→ `0x03F1`, matching the loop exactly.

## 6. Tables

### 6.1 Slot → bit → published effect

| Slot | Bit | Name string | Bit mask |
|---:|---:|---|---:|
| 0 | 0 | Infinite Health | `0x001` |
| 1 | 1 | One Hit K.O. | `0x002` |
| 2 | 2 | Fast Downtimer | `0x004` |
| 3 | 3 | Slow Bullets | `0x008` |
| 4 | 4 | Extra Enemy Health | `0x010` |
| 5 | 5 | Extra Enemy Damage | `0x020` |
| 6 | 6 | Undetectable to Bugs | `0x040` |
| 7 | 7 | Undetectable to Guards | `0x080` |
| 8 | 8 | Dizzy Enemies | `0x100` |
| 9 | 9 | Chase Passthrough | `0x200` |

### 6.2 State record (EWRAM `0x02006BE8 + 4*slot`)

| Offset | Meaning | Evidence |
|---:|---|---|
| +0 | unlocked (1 after a correct code) | write at `0x0801FCAC`; observed |
| +1 | enabled (1 after unlock; toggled by A) | toggle at `0x0801FF5A`; observed |
| +2,+3 | unused (zero) | dumps |

### 6.3 Localization

Four text banks exist in this EU image. Cheat **names** are translated
(French/German/Spanish IDs 12,14,…,30 are non-empty), but all ten **code**
strings (IDs 13,15,…,31) are empty in every non-English bank and fall back to
English at `0x0801C210`. Codes are therefore language-independent. Tables for
languages 4–6 (Italian/Dutch slots) are not populated in this build (their
descriptor points into string data; IDs do not resolve).

## 6b. Enumeration

### Space definition

* Alphabet: 38 typeable symbols, `ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789! `, plus
  backspace and enter. No lower case, no other punctuation.
* Length: whatever the slot's stored string is — 7 digits for slots 4–9,
  11–14 characters for slots 0–3.
* Fields/checksum: **none**. There is no checksum, no selector nibble, no key
  table, no encoder. The strict compare routine at `0x08016864` has exactly one
  caller in the whole ROM, the cheat validator at `0x0801FCA2` (BL scan over
  every halfword).
* Structure: 10 slots × 1 exact expected string each, slot-bound.
* Size of the accepted set: **10** strings. Reserved/unused table cells: none;
  the u16 ID array is exactly 10 entries (`0x0837A9A2`–`0x0837A9B5`) and the
  keypad alphabet starts at `0x0837A9B6`.

### Published-list check

All ten ROM strings are present, character-for-character, in published GBA
lists:

* `https://www.emu-land.net/en/portable/gba/cheats?showid=2378` (all ten,
  name → code pairs)
* `https://www.chaptercheats.com/cheat/gameboyadvance/20142/alex-rider-stormbreaker/code/15152`
  (all ten)
* GameFAQs `gba/932399-alex-rider-stormbreaker/cheats` and Neoseeker GBA page
  (403 to automated fetch; indexed snippets agree with the ten)

No published code is missing from the ROM and no ROM code is missing from the
published set. Numeric codes reused by the **DS**
version (`5204025` = “10,000 Spy Points”, `4298359` = “All shop items half
price” on DS lists) map to different effects on GBA (`Undetectable to Guards`,
`Dizzy Enemies`); the DS effect text must not be carried over.

### Novel code: proven impossible

The guide’s “mint an unpublished code” deliverable cannot be satisfied on this
ROM, and the negative is provable rather than assumed:

1. The accepted set is a literal table, not a function of fields. A novel code
   would have to be a string not in the table, and `strcmp` rejects every such
   string (§5, §6b bounds).
2. The table is complete: ten u16 text IDs, ten name IDs, ten RAM records, ten
   bit positions. There is no 11th ID, no alternate table, and no second
   string-comparison call site anywhere in the ROM.
3. Every one of the ten strings is already published, so even the ten valid
   inputs are not novel.
4. Localization does not add codes: all non-English code entries are empty and
   fall back to the same English strings.

The nearest unpublished *inputs* — a valid code under the wrong slot, the code
with a trailing space, the code with an extra digit, a code made only of `!`,
an empty submission, and the cheat's name instead of its code — were all
entered in the emulator and all rejected, with the RAM record unchanged (§7).
The correct code for the same slot was then accepted, proving the rejections
were not a lockout or an input failure.

### In-game verification of all ten

Each of the ten codes was typed on the real keypad and submitted; after each
submission the corresponding 4-byte record read `01 01`. Evidence: screenshots
for slots 0, 4, 5 and 6 (`Alex Rider - cheat accepted *.png`), plus the
savestate dump for the complete set:

```
slot 0:0101 1:0100 2:0100 3:0100 4:0101
slot 5:0101 6:0101 7:0101 8:0101 9:0101     (ss4: all ten unlocked)
flags 0x03F1  (live read after leaving the screen, slots 0,4,5,6,7,8,9 on)
```

The `00` in slot 1/2/3's second byte is the `enabled` flag, turned off by
pressing A on those unlocked slots; the first byte (`01`, unlocked) is
unchanged.

## 7. Validation evidence

### Observed (emulator screenshots / RAM reads)

* Title, main menu, Options, Sound, Credits, New Game intro, gameplay HUD,
  Pause (Resume / Quit), Quit confirmation (Yes / No) — walked and captured.
* Cheat screen with keypad cursor, typed buffer, green tick on acceptance,
  blank field on rejection.
* RAM: `0x02006BE8` records after every submission; `0x0200018C` = `0x0041`
  and `0x03F1` for two known enable sets.
* Full buffer text read from `0x02006C18` for every typed code, e.g.
  `VICTORIA PARR`, `9603717`, `6894098`.
* Rejections (buffer in RAM, record unchanged, no tick):
  * `JESSICA PARKER` on slot 6 (valid code, wrong slot)
  * `6894098 ` (trailing space)
  * `68940980` (extra digit)
  * `!!!`
  * empty field + enter
  * `INFINITE HEALTH` (the cheat's own name, upper-cased)
* Immediately after those rejections, `6894098` on slot 6 was accepted
  (`01 01` + tick), proving no lockout.

### Derived (instruction sequence)

* `0x08016864` is strict `strcmp`; only caller is `0x0801FCA2`.
* `0x0801C210` is the text-ID resolver with English fallback for empty
  localized entries.
* `0x0801FB40` builds the enable bitmask as `Σ 1<<slot`.
* Table addresses and text IDs from the code/pointer walk (§4).

### Inferred (not individually exercised)

* Which gameplay routine consumes each bit, and the exact strength/duration of
  each effect. The name strings and the bit loop establish the mapping; the
  effects themselves were not each played through combat.
* EEPROM persistence of unlocks. The `.sav` was still `0xFF`-filled after
  testing; unlocks were confirmed only within the running session. The game
  writes EEPROM at transmission/save points, which were not reached.

### Negative string search (space bounded)

Case-insensitive counts over the whole 4 MiB image:

| Term | Hits | Classification |
|---|---:|---|
| `password` (any case) | 0 | no password system |
| `debug` | 0 | no debug menu |
| `gallery` | 0 | no gallery |
| `sound test` | 0 | no sound-test menu |
| `level select` | 0 | no level select |
| `unlock` | 2 | engine “Handle already unlocked”, UI “Cheat Unlocked” |
| `cheat` | 12 | 6 English + 6 German UI strings |
| `code` | 15 | cheat UI (EN/DE), plus engine error strings (“Invalid error code”, …) |

The only cheat-related text in the image is the entry screen's vocabulary
(`Cheats`, `Enter Cheats`, `Cheat Codes`, `Cheat Name`, `Cheat Code`,
`Enabled?`, `Cheat Unlocked`) and the ten code strings; the rest of the
`Cheat *` strings are column headers for the unlocked list view.

### Menus enumerated

| Screen | Reached | Notes |
|---|---|---|
| Title (“Press START”) | yes | `Alex Rider - title.png` |
| Main Menu | yes | New Game / Options / Cheats; no fourth entry in this state |
| Options | yes | Sound, Credits |
| Sound | yes | Music Volume, SFX Volume (bar widgets) |
| Credits | yes | scrolling Razorback Developments credits |
| Cheats / Enter Cheats | yes | 8×5 keypad + slot name + field; all ten slots walked |
| New Game intro | yes | vehicle/helicopter intro, dialogue boxes |
| Gameplay HUD | yes | health 100, inventory icon |
| Pause | yes | tutorial pause: Resume, Quit |
| Quit confirmation | yes | “Are you sure?” Yes / No |
| Level select / mission select | absent | 0 string hits; menu builder has no such entry |
| Gallery / extras | absent | 0 string hits |
| Debug menu | absent | 0 string hits |
| Sound test | absent | 0 string hits |

## 8. Unknowns

* **EEPROM persistence.** Unlocks survived menu round-trips (RAM) but the 512-byte
  `.sav` was never written during the session; whether they survive a save
  point / power cycle is not proven. The save type is EEPROM (`EEPROM_V124`
  string at `0x3B9C24`).
* **Per-cheat gameplay effects.** The bit mapping is derived; each effect was not
  individually played. “Infinite Health” was enabled (`0x0200018C` bit 0) in a
  live level but no damage was taken before the session ended.
* **Mission pause / Mission Failed menu.** The text bank contains `Restart
  Level`, `Reload`, `Options`, `Training` (IDs 45–48) and the banners `Mission
  Failed`, `Mission Complete`, `Game Over`; these belong to the mission-failure
  / mission-pause flow, which was not reached (the opened pause was the tutorial
  pause, which offers only Resume/Quit). No cheat functionality is attached to
  them. The `Language` setting (ID 43) is likewise only in that unreached
  Options screen; the boot/main-menu Options has Sound/Credits only.
* **Italian/Dutch banks.** IDs do not resolve in this build; only EN/FR/DE/ES
  banks are populated.

## 9. Tooling

* mGBA 0.10.5 SDL, Xvfb, openbox, xdotool, ImageMagick `import`.
* Python 3 (`struct`, `zlib`) for ROM table walking and for parsing mGBA
  savestates. mGBA savestates are PNG containers; the `gbAs` chunk is
  zlib-compressed `GBASerializedState` (0x61000 bytes; EWRAM at state offset
  `0x21000`, IWRAM at `0x19000`).
* `alexrider_cheats.py` (next to this report) re-extracts the identity, the
  ten-slot table, the keypad alphabet and — given an `.ss*` file — the RAM
  cheat records and enable bitmask.
* No GDB stub was needed; the gdb port was held by another session's emulator,
  so state was read from savestates instead.

## 10. Legal note

Only hashes, addresses, structural findings and the ten already-published
passphrases are recorded here. No ROM, graphics, audio or bulk game text is
redistributed; screenshots are of menu states.
