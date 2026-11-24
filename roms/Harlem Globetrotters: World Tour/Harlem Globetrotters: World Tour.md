# Harlem Globetrotters: World Tour (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

Queue position 345. Work dir `/tmp/harlem`. Analysis target:
`roms/Harlem Globetrotters: World Tour/Harlem Globetrotters: World Tour.gba`
(the brief's filename `Harlem Globetrotters.gba` does not exist; the ROM in the
folder carries the full title).

## 1. Target identity

| Field | Value |
|---|---|
| Size | 4,194,304 bytes (0x400000, 4 MiB) |
| Header title | `HARLEMTROTER` (0xA0–0xAB, 12 bytes) |
| Game code / maker | `BHNE` / `20` (`file` identifies "BHNE20, Rev.00") |
| Version / complement / checksum | `0x00` / `0x39` / `0x0000` (rebuilt-header artifact; §16.1) |
| Entry word | `0xEA00002E` → `0x080000C0`, stock (no cracktro/trainer patch) |
| Embedded headers | **1** (Nintendo-logo scan over the whole file; not a multigame pack) |
| MD5 | `6d61c02022243c2f815e071f4a209f08` |
| SHA-1 | `01b4041c2f7d340b9c98d018c6d10c4eb7bfa81d` |
| SHA-256 | `06fbcafb47a1eb50f5350d58f10634b7c4e53350682ac7c885c5ed7c89db2621` |

Credits string at `0x08146628` names Full Fat / Destination Software — consistent
with the header maker code.

## 2. Executive summary

The game ships a **6-character password system**, exposed as the third game mode
on the main menu ("Enter Password"). It is a *coded* (checksum) system, not a
lookup of a few presets: the on-screen keyboard is a 31-symbol alphabet
`BCDFGHJKLMNPQRSTVWXYZ0123456789` (file `0x142ED8`, ROM `0x08142ED8`), each
character contributes a 5-bit index, characters 0–3 carry a 15-bit payload plus
a parity bit, and characters 4–5 carry a 6-bit checksum. A short Thumb validator
at `0x08100D48` checks `((c4>>4)|(c5<<1)) == ((c0^c1^c2^c3)&0x3F)`; an encoder
at `0x08100CD4` reverses it. I reimplemented both, enumerated the whole space
(887,503,681 possible strings, **14,314,576** accepted), minted a novel code
**`X3TD1F`** that appears in no published list, entered it on the real screen and
observed **"PASSWORD OK!"**, and proved the bounds with `X3TB2G` →
**"PASSWORD INVALID!"**. The built-in default `X3TB2D` is itself valid.

No debug menu, button cheat sequence, trainer patch, or GameShark-style surface
was found (search bounds in §8). The many `%d` debug-print strings in the image
(e.g. `TeamsUnlocked = %d`) are printf leftovers, not a reachable menu.

## 3. How to reproduce

* Emulator: `mgba -3 <rom>` under `Xvfb :316`, `SDL_AUDIODRIVER=dummy`.
  Keymap (mGBA SDL default): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
  Select=`BackSpace`, D-pad = arrow keys. Hold keys **20 ms** with ~150 ms gaps:
  longer holds cause double-steps on the password wheel (measured, §8).
* Path (verified): health screen → A ×8 → license screen → A ×8 → title →
  START → "SELECT GAME MODE" → RIGHT ×2 → "ENTER PASSWORD" → A.
  A faster route is to load savestate slot 1 (`F1`); the prepared slot is in the
  work dir as `A.ss1` (not shipped with the report).
* Password screen shows six slots. LEFT/RIGHT move the cursor; **UP decrements**,
  **DOWN increments** the selected character modulo 32 (observed in GDB: buffer
  byte `0x12 → 0x11 → 0x10` after successive UPs). Press A to submit; a valid
  code shows "PASSWORD OK!" for ~2 s then returns to the menu; an invalid one
  shows "PASSWORD INVALID!".
* Codes tested in-game:
  * `X3TB2D` (built-in default) — **accepted** ("PASSWORD OK!").
  * `X3TD1F` (novel, generated) — **accepted** ("PASSWORD OK!").
  * `X3TB2G` (bad checksum) — **rejected** ("PASSWORD INVALID!").
* Screen walk (all observed, not attract-only): health/safety, license, title,
  main menu (World Tour / Quick Match / Enter Password / Options), Options
  (Period Duration, Difficulty, Music Volume, SFX Volume, Credits), Enter
  Password keypad, team select, opponent select, "GET READY!", live match,
  pause menu ("GAME PAUSED / CONTINUE / QUIT"). Title-screen button combos
  `L+R+Start`, `L+R`, an Up/Down/Left/Right "Konami" sequence, `AABB`, and
  `Select+R+Start` were tried with no new screen.

## 4. Address map

All addresses are GBA ROM addresses unless marked RAM. File offset = address −
`0x08000000`.

| Address | Meaning |
|---|---|
| `0x08100CD4` | Encoder: `(a1,a2,a3) → 6 raw bytes` (Thumb) |
| `0x08100D48` | **Validator**: `(buf, out1, out2, out3) → bool` (Thumb) |
| `0x08100DDC` | Raw 6 bytes → 6 alphabet chars (`0x142ED8` indexed) |
| `0x08100E0C` | `char = alphabet[index]` (index→glyph lookup) |
| `0x08100E8C` | Get localized string by ID (36 = "Password ok!", 37 = "Password invalid!") |
| `0x080FF9BC` | Decode-and-adjust helper (decode, offset fields, re-encode) |
| `0x080FFA1C/34/4C` | Field extractors `arg1` / `arg2` / `arg3` |
| `0x080FFA70` | 2-D table lookup on `(arg2, arg3)` |
| `0x080FFAA4` | Search 52-byte records by `arg1` |
| `0x080FFAE0` | Field-derived count used by password debug screens |
| `0x08103478` | Password-screen text renderer |
| `0x081034EC` | Password-screen constructor |
| `0x081035E0`, `0x08103706` | The two validator call sites on the password screen |
| `0x0810365C` | Input router (bits 0x10/0x20 cursor, 0x40/0x80 character) |
| `0x081038D0` | Character stepper: `buf[slot] = (buf[slot] ± 1) mod 32` |
| `0x142ED8` | 31-symbol alphabet string, `0x9B`-terminated |
| `0x142F84` / `0x142F98` | "Password invalid!" / "Password ok!" |
| `0x143208`, `0x14368C`, `0x145620`, `0x1460DC` | "Enter Password" (localized copies) |
| `0x1447DC`, `0x1447F0`, `0x14480C`, `0x1450D0` | Debug printf leftovers |
| `0x0811EB80` | Font/tile-index table `0x0120..0x0147` (glyphs, **not** the password alphabet) |
| `0x0811EBD8` | 2-D string/record pointer table consumed via `(arg2,arg3)` |
| `0x03000224` (RAM) | Password buffer observed at the validator (GDB); a second call site uses `0x02000CE4` |
| `0x03005AF0` (RAM) | Input/state word; bit 0 gates the password-screen validator |

Key-mask/button-code tables were not found (§8).

## 5. Algorithm

Let the six on-screen characters be `c0..c5`, each an index `0..30` into the
alphabet `B C D F G H J K L M N P Q R S T V W X Y Z 0 1 2 3 4 5 6 7 8 9`
(indices 0..20 letters, 21..30 digits).

**Validate (`0x08100D48`)** — Thumb, exact pseudocode:

```
A = c0 | (c1<<5) | (c2<<10) | ((c3 & 1)<<15)
B = (c3>>1) ^ 0x0C
C = (c4 & 0x0F) ^ 0x07
S = (c4>>4) | (c5<<1)
checksum = (c0 ^ c1 ^ c2 ^ c3) & 0x3F
if S != checksum: return 0
*out1 = A ^ 0x123F          # arg1, 16-bit
*out2 = B                  # arg2, 4-bit after masking
*out3 = C                  # arg3, 4-bit after masking
return 1
```

The three XOR constants are the literal `0x0000123F` at `0x08100D44`, `0x0C`
and `0x07` in the epilogue. The screen calls the validator with all three output
pointers null, so only the boolean matters for acceptance.

**Encode (`0x08100CD4`)** — inverse, used by the game's debug/generator helpers:

```
A = arg1 ^ 0x123F ; B = arg2 ^ 0x0C ; C = arg3 ^ 0x07
c0 = A & 31 ; c1 = (A>>5) & 31 ; c2 = (A>>10) & 31
c3 = (((A>>15)&1) | ((B<<1) & 0xFF)) & 0xFF
S  = (c0 ^ c1 ^ c2 ^ c3) & 0x3F
c4 = ((S&1)<<4) | (C & 0x0F) ; c5 = (S>>1) & 31
```

`0x08100DDC` then renders each `ci` through `alphabet[ci]` and NUL-terminates at
slot 6. The keyboard wraps at **32** (`cmp r2,#31; subs r2,#32` in
`0x081038D0`), so wheel value 31 indexes the alphabet terminator `0x9B` and is
not a legal password character.

Detailed decoding of the *default* code confirms the model: `X3TB2D` =
`[18,24,15,0,23,2]` (read from RAM at the validator breakpoint) →
checksum `18^24^15^0 = 5`, stored `(23>>4)|(2<<1) = 1|4 = 5` → accepted;
payload `arg1 = 16146 ^ 0x123F = 11565`, `arg2 = 12`, `arg3 = 0`.

## 6. Tables

* **Alphabet** (31 symbols, file `0x142ED8`):
  `BCDFGHJKLMNPQRSTVWXYZ0123456789`, terminator `0x9B`.
* **Checksum layout**: 6 bits scattered across `c4` bit 4 and the seven low bits
  of `c5`; the low nibble of `c4` carries the 4-bit `arg3` field (XOR 7).
  `c3` bit 0 carries bit 15 of `arg1`, bits 1–4 of `c3` carry the 4-bit `arg2`
  field (XOR 0x0C). Bits 0–14 of `arg1` are split three ways across `c0,c1,c2`
  (5 bits each, XOR 0x123F over the assembled word).
* **String IDs** (`0x08100E8C`): 36 → "Password ok!", 37 → "Password invalid!".
* **Test vectors** (all entered on-screen, not just computed):

| Code | Raw indices | Computed / stored checksum | Payload `(arg1,arg2,arg3)` | Result |
|---|---|---|---|---|
| `X3TB2D` | 18,24,15,0,23,2 | 5 / 5 | (11565,12,0) | PASSWORD OK! (observed) |
| `X3TD1F` | 18,24,15,2,22,3 | 7 / 7 | (11565,13,1) | PASSWORD OK! (observed) |
| `X3TB2G` | 18,24,15,0,23,4 | 5 / 9 | — | PASSWORD INVALID! (observed) |

## 6b. Enumeration

* **Space definition**: alphabet 31 symbols, fixed length 6 → `31^6 =
  887,503,681` representable strings. The wheel has 32 positions; value 31 is
  the unused terminator slot. Valid codes are checksum-constrained, not a small
  preset table.
* **Accepted set**: exhaustively enumerated over all `31^4 = 923,521` choices of
  `c0..c3` and counted legal `(c4,c5)` pairs: **14,314,576 valid codes**
  (~1.61 % of strings). `c0..c3 < 31` means bit 5 of the XOR is never set, so the
  checksum is always `0..31`. For even S there are 16 legal `(c4,c5)` completions;
  for odd S there are 15 (the `arg3 = 8` value would force `c4 = 31`, invalid).
  Equivalently: 59,582 encodable `arg1` values × 16 `arg2` × 16 `arg3`, minus the
  odd-S `arg3=8` exclusions.
* **Validator model**: the Python reimplementation above agrees with the ROM on
  every tested accepted and rejected input; GDB reads at `0x08100D48` confirmed
  the exact six buffer bytes for each state (§7).
* **Novel code**: `X3TD1F` was generated by changing `c3:0→2`, `c4:23→22`,
  `c5:2→3` from the built-in default and recomputing the checksum. Its payload
  `(arg1=11565, arg2=13, arg3=1)` is an unadvertised field combination — no
  published code list for this SKU was obtainable (§8), and the code is absent
  from the ROM's own default state and from every string in the image. Entered
  with 5 keyboard presses on the real screen: **PASSWORD OK!** (screenshot
  `novel_ok2.png` in the work dir).
* **Bounds by rejection**: `X3TB2G` keeps the first four characters (checksum 5)
  but sets `c5 = 4`, giving stored checksum `9`; the game rejected it with
  **PASSWORD INVALID!** (`bad_msg.png`). This isolates the checksum layer. The
  field range layer is bounded statically: `arg2,arg3 ∈ [0,15]` because `c3>>1
  ≤ 15` and `c4 & 0xF ≤ 15`; values 16+ cannot be represented by the encoder.

## 7. Validation evidence

* **Observed** (emulator/screenshots/RAM): every screen in §3; "PASSWORD OK!"
  for `X3TB2D` and `X3TD1F`; "PASSWORD INVALID!" for `X3TB2G`; GDB breakpoint at
  `0x08100D48` reading `r0 = 0x02000ce4` / `0x03000224` with bytes
  `12 18 0F 00 17 02` and their `-1` response to UP presses (oracle use per
  §16.19). `x/8bx` transcripts were in `/tmp/harlem/gdb3.txt`.
* **Derived** (static, byte-verified): encoder/validator equations, constants,
  alphabet, field widths, code counts, call graph (BL scan found the encoder at
  `0x080FF9A8/0x080FF9FE`, the validator at `0x080FF9D0`, `0x080FFA26`,
  `0x080FFA3E`, `0x080FFA56`, `0x080FFA7A`, `0x081035E0`, `0x08103706`).
* **Inferred**: the decoded `(arg1,arg2,arg3)` triple is consumed by the
  result/debug screens through `0x080FFA70`/`0x080FFAA4`/`0x080FFAE0` and the
  record table at `0x0811EBD8`; the exact user-visible progression effect of a
  particular `arg2/arg3` combination was not isolated to a named unlock flag, so
  it is not claimed. Acceptance itself is fully proven.

Media evidence: screenshots were kept on disk in `/tmp/harlem/`;
none are attached here.

## 8. Unknowns

* **Published codes**: web search returned no usable results (search tool empty;
  DuckDuckGo CAPTCHA; 3rd party cheat indexes 403; Bing returned unrelated pages). No published
  literal could be verified against the ROM. The only code literal reachable
  without a published list is the keyboard's built-in default `X3TB2D`; it is
  valid and is reported as such. Per §16.7 no third-party code is claimed verified.
* **Effect beyond acceptance**: the game shows PASSWORD OK! and returns to the
  main menu after ~2 s; the `.sav` stayed 0 bytes. Whether the decoded payload
  grants session-only unlocks (players/teams) could not be tied to a specific
  named RAM flag. This is a bounded unknown, not a skipped test.
* **Hidden debug menu**: debug printf strings exist (`0x1447DC` etc.) and there
  are password-debug screen constructors (`0x08101D8C`, `0x08102078`), but no
  reachable menu entry or title-screen button code led to them in the enumerated
  screens. Bounded negative: all reachable screens walked; `strings` searched
  for `debug|secret|unlock|cheat|code|menu|hidden`; title combos tested; no menu
  labels beyond the documented options were found. If a debug screen exists it
  is gated by a path not exercised here.
* **Button codes**: no key-mask sequence table was located; none of the tested
  title-screen combos changed state.
* **Font glyph table**: displayed glyphs come from a tile-index region at
  `0x0811EB80`/`0x08145658`, distinct from the 31-character password alphabet;
  the two must not be confused when decoding the buffer.

## 9. Tooling

* `file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings -t x`, `grep`.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`.
* Python 3 + Capstone 5.0.7 for pointer/BL/LDR-literal scans and for the codec
  implementation and exhaustive enumeration.
* `mgba` (SDL, GDB stub `-g`), `Xvfb :316`, `openbox`, `xdotool`, `scrot`,
  ImageMagick `convert`/`montage`, `tesseract` (OCR triage only).
* GDB: `gdb-multiarch`, `target remote :2345`, breakpoint `0x08100D48`,
  `x/8bx $r0` — used as the validator oracle (guide §16.19).
* Helper scripts: `/tmp/harlem/ui.py` (timed XTEST input), `enter.py`,
  `gdb3.cmd` (breakpoint command list).

No ROM, copyrighted graphics, or extracted assets are redistributed in this
report; only addresses, hashes, algorithms and generated codes are published.
