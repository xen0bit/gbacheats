# Mobile Suit Gundam Seed: Battle Assault (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Mobile Suit Gundam Seed: Battle Assault.gba` |
| Size | 4,194,304 bytes (0x400000) |
| Header title | `GUNDAMSEED-B` |
| Game code | `BGNE` (Europe), maker `B2`, version `0x00` |
| Entry word | `0xEA00002E` (stock `b 0x080000C0`) |
| MD5 | `20bb7717258c3bd2e87b9b7617e95df2` |
| SHA-1 | `8287d3d336d94a85c5cb22da0fd84918199197e1` |
| SHA-256 | `d7952790a4b82b6d230a4953e4bfe48f6693ddd550f1cf0e7ace74bce95453f8` |

Phase 0: Nintendo-logo scan found exactly one header at file offset 0 (no multigame
cartridge, no appended trainer, no cracktro patch). `.sav` created by mGBA is 0 bytes,
consistent with the game's password-only (no battery) progress system.

## 2. Executive summary

The game has a genuine developer-intended **password system**, reachable from
Main Menu → PASSWORD. It is a 9-symbol code over a 33-character keypad alphabet
(no vowels). I fully reversed the validator at ROM `0x08026440` and its caller at
`0x080255AE`, reimplemented it in Python, and verified the model against all 19
accepted published codes and against deliberately rejected inputs. The password
encodes a 12-bit **progress flag word**, a 4-bit **clear/difficulty field**, and
several smaller fields, protected by a popcount checksum over a constant-offset
32-bit payload.

I verified the published codes in this exact EU ROM, found which published variants
are invalid for it, minted two codes that appear in **no published list** and
confirmed both in the emulator with RAM evidence, and proved the format bounds by
in-game rejection of an out-of-range field and a wrong-checksum code.

No hidden/debug menu exists on any reachable screen; the negative is bounded by a
full screen enumeration and an exhaustive search of the text/button spaces described
in §7.

## 3. How to reproduce

* Emulator: mGBA (`mgba -3`), `DISPLAY=:318`, `SDL_AUDIODRIVER=dummy`, Xvfb :318 +
  openbox. Keymap: A=`x`, B=`z`, Start=`Return`, Select=`BackSpace`,
  arrows=D-pad. `Shift+F1` writes `.ss1`; savestates were decompressed (`gbAs` chunk,
  zlib) and diffed to read RAM.
* Path: boot → press Start through the intro → Main Menu → move to PASSWORD (bottom
  right) → A → type 9 symbols with arrow keys + A → ENTER (the on-screen ENTER key;
  typing 9 symbols alone does **not** submit) → game returns to Main Menu.
* Password screen keypad (verified from the rendered screen), row-major:

  ```
  row0: B C D F G H J K L M N
  row1: P Q R S T V W X Y Z ?
  row2: 0 1 2 3 4 5 6 7 8 9 !
  ```

  33 symbols (vowels A/E/I/O/U omitted). Nine white entry slots.
* Clean reproduction state: `/tmp/gundamseed/clean_password.ss1` (a
  savestate sitting on the empty password screen); `mgba -3 -t clean_password.ss1 ROM`.
* Tooling scripts: `ui.py` (XTEST input + screenshot), `pwlib.py` (keypad navigator),
  `val.py` (validator reimplementation), `gen.py` (encoder), `verify.py`
  (fresh-emulator code test), `ssdiff.py` (savestate RAM diff).

## 4. Address map

| Item | Address |
|---|---|
| Password submit handler (`cmp len,#9`, calls validator) | ROM `0x080255AE` (`0x080255B6` = `BL 0x08026440`) |
| Password validator | ROM `0x08026440` – `0x080267E0` |
| Constant added to packed payload | ROM literal `0x080266E0` = `0xF8A432EB` |
| Mask literal `0x00000FFF` | ROM `0x080266E4` |
| Masks `0xFFFF0000 / 0xFF00FFFF / 0x00FFFFFF / 0x0000FFFF` | ROM `0x080266E8`–`0x080266F6` |
| Raw 9-symbol input buffer (key indices) | IWRAM `0x0300052E` (savestate offset `0x1952E`) |
| Character-count byte (must be 9) | IWRAM `0x0300052B` |
| Output progress struct (written by validator) | IWRAM `0x03007638` |
| `strh` flag word | IWRAM `0x03007638` (16-bit) |
| `strb` byte +2 / +3 / +4 | IWRAM `0x0300763A` / `0x0300763B` / `0x0300763C` |
| `strh` extra word | IWRAM `0x0300763E` |

File offset = ROM address − `0x08000000`. RAM mapping inside decompressed savestate:
IWRAM `0x03000000` → state offset `0x19000`; EWRAM `0x02000000` → `0x21000`.

## 5. Algorithm

Validator `0x08026440`, reimplemented bit-for-bit in `val.py`:

```
k[0..8] = raw keypad indices (0..32) from IWRAM 0x0300052E
for i in 0..8: v[i] = (k[i] - 1) & 0xFF          # byte subtraction
selector = sum( ((v[i] >> 4) & 1) << i for i in 0..5 )   # 6 bits
n[i] = v[i] & 0x0F  (i = 0..7)
payload = sum( n[i] << (28 - 4*i) for i in 0..7 )        # 32-bit
chk = (v[8] & 0x1F) | (((v[7] >> 4) & 1) << 5)          # 6-bit checksum symbol
p   = (payload + 0xF8A432EB) & 0xFFFFFFFF
ip  = (chk - 21) & 0x3F

ACCEPT iff selector == popcount(p) + popcount(ip)        # checksum condition
```

Then field reconstruction and range gates:

```
r6 = (p >> 20) | ((p & 0xF) << 16) | (((p >> 16) & 0xF) << 24)
r7 = ((ip>>4)&3) | (((ip>>2)&3)<<2) | (((ip>>1)&1)<<4) | ((ip&1)<<5) | (((p>>4)&0xFFF)<<16)
hi  = r6 >> 24                       # 0..11 required
flag = r6 & 0xFFFF                   # 12-bit progress word (output)
pcnt = popcount(flag)                # over 12 bits
```

Gates (all derived from `0x080266CE`–`0x0802679C`):

* `hi > 11` → reject. For `hi==8/9/10/11` require `pcnt > 1/3/5/7` respectively.
* `(r7 & 0x0C) == 0x0C` requires `pcnt == 12`.
* If `pcnt <= 2/4/6/8`, then `flag & 0xF00/0xE00/0xC00/0x800` must be zero.
* If `r7 & 0x20`, then bit `hi` of `flag` must be set.
* `r7 & 3 <= 2`; `(r7>>16) <= 0xFFF` (always true by construction).

On success the struct at `0x03007638` is written:
`u16 flag = r6 & 0xFFFF; u8 +2 = 0; u8 +3 = hi; u8 +4 = packed bits; u16 +6 = r7>>16`.

**Aliases found in the input mapping:** `k=0` (`B`) and `k=32` (`!`) both give
`v=0xFF` → same nibble 15 and same bit-4; they are interchangeable at any position.
Position 6's bit-4 is never read (free alias bit).

## 6. Tables

### 6.1 Published-code verification in this EU ROM

Flag read from IWRAM `0x03007638` after ENTER. `0x0000` = rejected.

| Password | Source | Flag observed | Verdict |
|---|---|---|---|
| `C2?6RSD0L` | 3rd party cheat indexes / FAQ | `0x0FFF` | accepted (all unlock) |
| `WLJK7SD0S` | 3rd party cheat indexes | `0x0FFF` | accepted |
| `W201RSDJ0` | 3rd party cheat indexes | `0x0FFF` | accepted |
| `W20WRSD0J` | 3rd party cheat indexes | `0x0FFF` | accepted |
| `25R!RSD08` | 3rd party cheat indexes | `0x0737` | accepted |
| `?DNWRSD0J` | 3rd party cheat indexes | `0x03A3` | accepted |
| `GGN?RSD00` | 3rd party cheat indexes | `0x02C3` | accepted |
| `DGNYRSD0J` | 3rd party cheat indexes | `0x00C3` | accepted |
| `DVNYRSD00` | 3rd party cheat indexes | `0x0183` | accepted |
| `ZZ7SRSDJ0` | 3rd party cheat indexes | `0x02C7` | accepted |
| `XL4GRSD0J` | 3rd party cheat indexes | `0x0103` | accepted |
| `C64DRSD0J` | 3rd party cheat indexes | `0x0043` | accepted |
| `2GS0RSDJ0` | 3rd party cheat indexes | `0x06C7` | accepted |
| `W2NSRSD0J` | 3rd party cheat indexes | `0x0004` | accepted |
| `CV1FRSDJ0` | 3rd party cheat indexes | `0x0080` | accepted |
| `W2LRRSD0J` | 3rd party cheat indexes | `0x0002` | accepted |
| `C2KQRSD0J` | 3rd party cheat indexes | `0x0001` | accepted |
| `WLKQRSDJ0` | 3rd party cheat indexes | `0x0001` | accepted |
| `CL3RRSD0J` | 3rd party cheat indexes | `0x0003` | accepted |
| `WZMRRSDJ0` | 3rd party cheat indexes | `0x0000` | **rejected** in this EU build |
| `ZHR!RSDJ0` | 3rd party cheat indexes | `0x0000` | **rejected** in this EU build |
| `C2?6RSDO4`, `C2?6RSDOL` | 3rd party cheat indexes | n/a | contain letter `O`; not in the 33-symbol alphabet — transcription errors (should be `0`) |

The README/FAQ "unlock everything" code `C2?6RSD0L` is the only one needed; it sets
`0x0FFF`, makes VERY HARD selectable and exposes all 12 suits (the two whose portrait
is a `?` are Justice and Astray).

### 6.2 Other in-game cheats

* **2P color:** published as "hold Select, press A on the suit at Mobile Suit
  Selection, after clearing that suit's story". This is a developer-intended
  in-game code (not a memory code). Attempted after the all-unlock password; no
  unambiguous color difference was isolated in the captured frame, so no claim of
  reproduction is made here.
* **Unlockables by play:** Astray (4 Normal-mode clears), CGUE (2), Freedom (6),
  Justice (8), Very Hard (12) — consistent with the `hi`/flag fields above.

## 6b. Enumeration

**Space definition.** 9 positions × 33 physical symbols = `33^9 = 46,411,484,401,953`
raw spellings. The validator only uses 5 bits per position (low nibble + bit-4 of
the byte `(k-1)`), so the effective space is `32^9 = 2^45 = 35,184,372,088,832`
distinct validator inputs; a 6-bit checksum condition fixes the selector and removes
a factor of ~64.

**Reachability census** (exhaustive over `flag[0..4095] × hi[0..11] × ip[0..63]`,
with `low16` irrelevant to the gates because `r6` low-16 equals `flag`):

* 16,368 of 49,152 `(flag, hi)` pairs are reachable; 1,503 distinct 12-bit flags.
* 627,120 valid `(flag, hi, ip)` triples → roughly `8.2 × 10^10` accepted 9-symbol
  spellings (each triple has 2^16 free `low16` values and a free alias bit at
  position 6; further `B`/`!` aliases increase this).
* Hi field distribution: hi 0–7 → 1,503 flags each; hi 8 → 1,494;
  hi 9 → 1,382; hi 10 → 1,004; hi 11 → 464.

**Novel codes (absent from 3rd party cheat indexes and all fetched lists):**

| Code | Intended flag | Emulator result (RAM) | Note |
|---|---|---|---|
| `DN3QRSDJ0` | `0x0123`, hi 0 | `0x0123` at `0x03007638` | no published list contains this code |
| `XX6FRSDJ0` | `0x00A5`, hi 7 | `0x00A5`, byte+3 = `0x07` | unadvertised `hi=7` field combination |

Both were generated by inverting the ROM validator (§5), not copied from a list.
The `hi=7` example is the "unadvertised combination" required by §0.2: it sets a
difficulty/clear field that none of the published codes' payloads exercise.

**Bounds proven by rejection (in-game):**

| Code | Mutation | Result |
|---|---|---|
| `B2?6RSD0L` | first symbol of the all-unlock code changed `C`→`B` (wrong checksum selector) | flag `0x0000` — rejected |
| `BCDFGHJKL` | arbitrary 9-symbol string | flag `0x0000` — rejected |
| `C76LRSDJ0` | valid checksum but `hi = 12` (out of the 0..11 field) | flag `0x0000` — rejected, proves the `hi <= 11` bound |
| `25RBRSD08` | `!`→`B` alias substitution in `25R!RSD08` | flag `0x0737` — accepted, proves the alias |

## 7. Validation evidence

* **Observed (emulator):** title, main menu, options submenus, password screen and
  9-slot keyboard, difficulty select (VERY HARD enabled after the all-unlock code),
  Mobile Suit Selection (12 suits; the two `?` portraits are Justice/Astray),
  Command Selection, OS Setting, story dialogue, fight, `1P PAUSE`, VS link
  "Connecting…" / "Connection failed", "NEXT STAGE". RAM flag reads in §6.1/§6b
  came from decompressed `gbAs` savestate chunks before/after ENTER.
* **Derived (static):** validator `0x08026440` and caller `0x080255AE`; all constants
  and gates in §5 were read from Thumb disassembly and literal pools.
* **Inferred:** mapping of the 12-bit flag bits to individual story/unlock flags
  beyond the aggregate `0x0FFF` all-unlock observation; semantics of the `r7`/byte+4
  sub-fields. These are labelled inferred, not observed.
* **Negative-result boundary:** `strings -t x` found only 56,429 runs and essentially
  no game text (the only hits were the header, an isolated `CODE` at `0x199540`,
  `SEED` at `0x29B442`, both inside compressed data). Searches for the keypad
  alphabet, all published passwords, `PASSWORD`, `DEBUG`, `SECRET`, `ENTER`, `EXIT`,
  `OPTIONS` in ASCII, `+0x20` case-shift, UTF-16LE/BE, UTF-32 and every affine
  byte-substitution of ASCII all returned zero usable text-bank hits; an affine
  difference-pattern search for the rendered strings likewise found nothing. Text is
  font/tile-indexed, so absence of a `strings` hit is not evidence of absence of UI.
  The no-hidden-menu conclusion therefore rests on: (a) every reachable screen
  enumerated above, each with a screenshot, and (b) the keypad/pause/title button
  spaces searched — including Konami-style and `L+R+Start+Select` sequences on the
  title screen, which left the title screen unchanged.
* Fetched cheat pages were treated strictly as data; no instruction found in them
  was executed. No prompt-injection payload was encountered in this session.

## 8. Unknowns

* Exact per-bit meaning of the 12-bit flag word (only the all-set and a few partial
  values were observed), and of the `r7`-derived byte at `0x0300763C` / word at
  `0x0300763E`.
* Whether the published Select+A alternate-color code truly changes the palette;
  the single captured frame was not conclusive.
* Why `WZMRRSDJ0` and `ZHR!RSDJ0` are published yet rejected by the EU build —
  most plausibly USA-revision codes or transcription errors; not resolved.

## 9. Tooling

`arm-none-eabi-objdump -M force-thumb`, Capstone (literal/BL scans), Python 3
(`val.py`, `gen.py`, `verify.py`, `pwlib.py`, `ssdiff.py`), mGBA SDL with `Shift+F1`
savestates, Xvfb :318 + openbox, xdotool XTEST input, scrot + ImageMagick.
Web sources: 3rd party cheat index cheats & FAQ (BoringPolitico/Seth0708), 3rd party cheat indexes/libretro list (memory-code addresses used only as leads, not as findings).
No ROM or copyrighted asset is redistributed by this report.
