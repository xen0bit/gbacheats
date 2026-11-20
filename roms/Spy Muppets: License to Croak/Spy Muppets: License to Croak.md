# Spy Muppets: License to Croak (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Spy Muppets: License to Croak/Spy Muppets: License to Croak.gba` |
| Size | 8,388,608 bytes (`0x800000`) |
| Header title | `SPY MUPPETS` |
| Game code / maker | `BSSE` / `6S` |
| Version | `0x00` (Rev.00) |
| Entry word | `0xEA00002E` (stock `b 0x080000C0`, no cracktro) |
| Fixed byte / complement / checksum | `0x96` / `0x51` / `0x0000` |
| Nintendo-logo hits | 1 (file `0x4`) — single image, not a multi-game pack |
| MD5 | `905067b56274608b4be2e805491b624d` |
| SHA-1 | `c6971a3e9282df988b24e9af4ac0d42a9b59d0c6` |
| SHA-256 | `609709c5c74fd12fbafa73e26bf0ce1559fe6bc152ff1bb179cc29999331e623` |

## 2. Executive summary

The game has a real, developer-intended **5-symbol password system** reached from the
title menu via **CONTINUE**. The on-screen keyboard offers exactly the 32 symbols
`B C D F G H J K / L M N P Q R S T / V W X Y Z 0 1 2 / 3 4 5 6 7 8 9 ?`.

The ROM contains a complete validator, encoder and decoder:

- **Validator** `0x08002304` — accepts a 5-character password iff, with alphabet
  indices `c0..c4`, `S = c0+c1+c2`, `(c3 & 3) == (S & 3)` and
  `c4 == ((S ^ 0xFC) & 0x1F)`. Rejects the blank sentinel `"xxxxx"`.
- **Encoder** `0x08002270` — builds codes from a 5-field state
  (`A, C, D, slot, B`) plus the same checks.
- **Decoder / apply** `0x08002394` — after validation writes the extracted fields
  to EWRAM and IWRAM and sets three "unlock" flag bytes when `A`, `C` or `D` exceed 3.

Public recon found exactly one published password, `LLGGL` ("Final boss",
ChapterCheats). It is valid and verified in the ROM and emulator. It is **not** the
deliverable: the format permits **262,144 valid spellings** mapping to **131,072
distinct decoded states**. I generated and entered several codes absent from every
published list, including `nlgjn` (changes field `A` from 4 to 5, RAM-verified),
`llgzl` (proves an unused/aliased bit) and `???rc` (maximum field values), and
proved rejection with bad-checksum inputs (`llggb`, `BLGGL`).

No button codes, debug menus, or other cheat surfaces were found: the full 8 MiB
text bank has zero hits for `debug`, `cheat`, `level select`, `wireframe`, and every
reachable screen was walked (§8).

## 3. How to reproduce

- Emulator: mGBA 0.10.5 under Xvfb `:317` + openbox, `SDL_AUDIODRIVER=dummy`,
  `mgba -3 <rom>`. Default SDL keymap (A=`x`, B=`z`, Start=`Return`, arrows).
- Screens: title → **Start** → main menu (`NEW GAME / CONTINUE / CREDITS`) →
  select **CONTINUE** → 5-slot password grid. Enter 5 symbols with the D-pad + A;
  the 5th A submits automatically. The back-arrow cell (row 4, col 3) deletes.
- Note: the emulator's language was Spanish, so acceptance shows
  `MODO DE CUENTA / MODO DE ACTIVIDAD` and rejection shows
  `CONTRASEÑA NO VALIDA`; English equivalents are in the string bank at
  `0x084A1E80+` (`bad password` at `0x084A1F08`).
- Codes tested (all typed on the real in-game keyboard):
  - `LLGGL` (published) — accepted → mode select.
  - `nlgjn` (novel) — accepted → mode select; RAM field `A` = 5.
  - `llgzl` (novel alias) — accepted; identical decoded fields to `LLGGL`.
  - `???rc` (novel max-field) — accepted; `A=15, C=15, D=31, B=3, slot=3`.
  - `llggb`, `BLGGL` — rejected with invalid-password message.

## 4. Address map

All ROM addresses are `0x08000000 + file offset`.

| Address (ROM) | File | Meaning |
|---|---|---|
| `0x08002304` | `0x2304` | Password validator, `int validate(char* code)` → 1/0 |
| `0x08002270` | `0x2270` | Password encoder from state fields |
| `0x08002394` | `0x2394` | Decode/apply password to game state (called on accept) |
| `0x0800A22C` | `0xA22C` | Password-entry screen state machine (grid cursor, A/B, submit) |
| `0x08007B3C` | `0x7B3C` | Password-screen UI builder/renderer |
| `0x0800A3DA` | `0xA3DA` | Displays string ID 14 "bad password" on rejection |
| `0x08007CEE`, `0x0800AD0C` | `0x7CEE`, `0xAD0C` | Displays string ID 36 "password" |
| `0x08002738` | `0x2738` | `char* get_text(u16 id)`; language table selected by RAM `0x020000CC` |
| `0x084A3140` | `0x4A3140` | English UI string-pointer table (`id*4`); other 5 languages follow |
| `0x084A1E5C` | `0x4A1E5C` | Password alphabet, lowercase ASCII, NUL-terminated |
| `0x084A1E54` | `0x4A1E54` | `"xxxxx"` blank-code sentinel |
| `0x084C9858` | `0x4C9858` | 16-bit char table for the on-screen grid (rows 0-3 × cols 0-7; row 4 = controls) |
| `0x020050CC` | — | Decoded password state struct base (EWRAM; confirmed by savestate diff) |
| `0x02004BA4` | — | Three byte flags set when `A>3`, `C>3`, `D>3` respectively |
| `0x03001464` | — | IWRAM copy of field `B` |

Savestate layout (mGBA `.ss1`, zlib `gbAs` chunk, 397,312 bytes): EWRAM at state
offset `0x21000`, IWRAM at `0x19000`; therefore EWRAM `0x020050CC` is state offset
`0x260CC` and EWRAM `0x02004BA4` is `0x25BA4`.

## 5. Algorithm

Alphabet (index 0..31): `b c d f g h j k l m n p q r s t v w x y z 0 1 2 3 4 5 6 7 8 9 ?`.

**Validator** (`0x08002304`), derived from Thumb disassembly:

```
if strcmp(code, "xxxxx") == 0: return 0        # blank sentinel
for i in 0..4:
    c[i] = index of code[i] in alphabet        # linear search, 0..31
S = c0 + c1 + c2                               # 32-bit add, max 93
if (c3 & 3) != (S & 3): return 0                # 2-bit check nibble
if c4 != ((S ^ 0xFFFFFFFC) & 0x1F): return 0   # 5-bit checksum (same as (S^0xFC)&31)
return 1
```

Both checks must pass; there is no other length/range test for the 5 entered
symbols (all 32 symbols are enterable on the grid).

**Encoder** (`0x08002270`), from state fields (`A = [st+16]`, `C = [st+20]`,
`D = [st+24]`, `slot = [st+12]`, `B = [st+8]`):

```
i0 = (A << 1) | (B & 1)
i1 = (C << 1) | ((B >> 1) & 1)
i2 = D
S  = i0 + i1 + i2
i3 = (slot << 2) | (S & 3)
i4 = (S ^ 0xFFFFFFFC) & 0x1F
code = alphabet[i0] alphabet[i1] alphabet[i2] alphabet[i3] alphabet[i4]
```

**Decoder / apply** (`0x08002394`) reverses it:

```
c = indices of the five entered characters            # after validate() succeeds
B    = (c0 & 1) | ((c1 & 1) << 1)                      # [st+8], also RAM 0x03001464
slot = (c3 >> 2) & 3                                   # [st+12]
A    = c0 >> 1                                         # [st+16]
C    = c1 >> 1                                         # [st+20]
D    = c2                                              # [st+24]
flags at 0x02004BA4..A6 = (A>3, C>3, D>3)
```

A faithful Python reimplementation is in `/tmp/opencode/spymuppets/pw.py`.

## 6. Tables

| Item | Value |
|---|---|
| Alphabet | `bcdfghjklmnpqrstvwxyz0123456789?` (32 symbols, value = index) |
| Blank code | `xxxxx` (`0x084A1E54`) — rejected before checks |
| Checksum | `c4 = (c0+c1+c2 ^ 0xFC) & 0x1F` |
| Check nibble | `c3 & 3 = (c0+c1+c2) & 3` |
| Unused bits | `c3` bit 4: ignored by decoder (`c3 >> 2 & 3`) → 2 spellings per state |
| Field widths | `A = c0>>1` (0..15), `B = c0&1 \| (c1&1)<<1` (0..3), `C = c1>>1` (0..15), `D = c2` (0..31), `slot = (c3>>2)&3` (0..3) |
| Published list | `LLGGL` = final boss (ChapterCheats, 2007). GameFAQs reports "1 cheat" but the page returned HTTP 403; unverified. |

## 6b. Enumeration

**Space definition.** 5 symbols × 5 bits = 25 bits → `32^5 = 33,554,432`
representable strings. The checksum fixes `c4` (1/32) and the check nibble fixes
2 bits of `c3` (1/4), so exactly `33,554,432 / 128 = 262,144` passwords validate.
This was confirmed both by the closed-form count and by iterating all
`32^3 × 8` combinations in `pw.py`. The decoder discards `c3` bit 4, so the
accepted strings collapse to **131,072 distinct game states** — exactly two
spellings per state. Valid strings are therefore a 1/128 subset, not a short
hard-coded list; no table of accepted codes exists in the ROM.

**Novel codes (absent from every published list; only `LLGGL` is published):**

| Code | `A C D slot B` | Result in emulator | RAM evidence (EWRAM `0x020050CC+16` = `A`) |
|---|---|---|---|
| `nlgjn` | `5 4 4 1 0` | Accepted → mode-select screen | `A` changed `4 → 5`; `[st+8..24] = 0,1,5,4,4` |
| `llgzl` | `4 4 4 1 0` | Accepted → mode-select screen | identical fields to `LLGGL` — proves `c3` bit 4 is an alias |
| `???rc` | `15 15 31 3 3` | Accepted → mode-select screen | `B=3, slot=3, A=15, C=15, D=31`; unlock flags `01 01 01` |
| `LLGGL` (published anchor) | `4 4 4 1 0` | Accepted → mode-select screen | `B=0, slot=1, A=4, C=4, D=4` |

Screenshots: `novel_clean.png`, `alias_clean.png`, `maxfield_clean.png`,
`pub_result.png` in `/tmp/opencode/spymuppets`.

**Bounds proven by rejection:**

| Input | Reason | Observed |
|---|---|---|
| `llggb` | `c4` wrong (`0` instead of `8` for `S=20`) | `CONTRASEÑA NO VALIDA`; decoded struct and flags unchanged |
| `BLGGL` | `c3&3 = 0` but `S&3 = 1` | `CONTRASEÑA NO VALIDA` |
| `llgzl` vs `LLGGL` | `c3` bit 4 toggled | both accepted, **same** decoded state — unused bit bounded |
| `???rc` | fields at maxima (15/15/31) | accepted, not rejected; bounds are the encoding widths, with the three extra "unlock" flags set |
| `xxxxx` | blank sentinel in ROM | rejected before checks (`0x0800230E`–`0x0800231C`) |

All five were entered on the real keyboard with savestates taken before and after;
savestate bytes at state offset `0x260CC` (`0x020050CC`) and `0x25BA4`
(`0x02004BA4`) were compared directly. Clean/rejected states read
`B=0, slot=3, A=0, C=0, D=0`, flags `00 00 00`; accepted states read the field
tuples above with flags `01 01 01`.

## 7. Validation evidence

- **Observed**: mGBA screenshots of title, main menu, password grid, invalid
  message, mode-select screen, story cutscene, activity folder list (`REY GAMBA`,
  `PEGGY GALORE`), and snowmobile activity; savestate RAM diffs summarized above.
- **Derived**: validator/encoder/decoder addresses and formulas from
  `arm-none-eabi-objdump -M force-thumb` of `0x08002270`–`0x08002490`, the grid
  char table at `0x084C9858`, the alphabet at `0x084A1E5C`, and the string-ID
  getter at `0x08002738`.
- **Inferred**: the semantic meaning of `A/C/D/B/slot` in terms of specific
  levels/characters is not established; the decoder's field names reflect their
  encoder/decoder roles, and the three flag bytes are named "unlock" from the
  `unlocked:` results label at `0x084A312C`. All accepted codes reach the same
  mode-select screen; the story mode opened at the same intro for `LLGGL` and
  `nlgjn`, so the fields appear to affect the activity/unlock list, not the
  story-mode start (not fully exercised).

## 8. Unknowns

- Field→content mapping (`A`, `C`, `D`, `B`, `slot` to particular activities,
  characters, difficulties or levels) was not finished; the mode-select screen
  and its folder list were only partially enumerated (two folder entries seen:
  `REY GAMBA`, `PEGGY GALORE`, with a 4×4 grid of `????` placeholders).
- The GameFAQs "1 cheat" page was HTTP 403; it may list a code besides `LLGGL`.
  All codes generated here are absent from the one code found on the open web
  (ChapterCheats) and from the ROM's own text/table banks.
- **Bounded negative for other cheat surfaces**: `strings -t x` over all
  8,388,608 bytes found **0** occurrences of `debug`, `level select`, `cheat`,
  `wireframe` (case-insensitive). The only "unlock"-like string is `unlocked:`
  at `0x084A312C`, a results-screen label, not a menu. Every reachable screen
  was walked: title, 3-item main menu, password entry (including invalid and
  accepted paths), mode select, story cutscene, activity folder list and an
  activity. No hidden/debug menu or button-code sequence was observed; no
  button-mask table was identified.

## 9. Tooling

- `mgba` 0.10.5 (`-3`, `-t <state>`, SDL dummy audio), Xvfb `:317`, openbox,
  `xdotool` XTEST input, `scrot` screenshots.
- mGBA `.ss1` parser: `/tmp/opencode/spymuppets/ss.py` (zlib `gbAs` chunk).
- Model/encoder/decoder: `/tmp/opencode/spymuppets/pw.py`.
- Keyboard automation / test harness: `k.py`, `enter.py`, `testcode.py`.
- `arm-none-eabi-objdump -M force-thumb`, Python `struct`/`zlib`.
- Web recon: DuckDuckGo result page, ChapterCheats password page (data only),
  GameFAQs cheats page (403). No fetched text was treated as instructions.
- No ROM or copyrighted assets are redistributed by this report.

## 10. Cleanup

All processes started for this engagement are terminated by PID number only
(`mgba`, Xvfb and openbox instances owned by this session); no `pkill -f` was
used. All `.sav`/`.ss1` artifacts were removed from the ROM folder. Analysis
scripts and screenshots remain in `/tmp/opencode/spymuppets`.
