# BattleBots: Design & Destroy (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/BattleBots: Design & Destroy/BattleBots: Design & Destroy.gba` |
| Size | 4,194,304 bytes (4 MiB / 32 Mbit) |
| Header title | `BATTLEBOTSDD` |
| Game code | `BBDE` |
| Maker code | `5G` |
| Software version | 0 |
| Entry | `0xEA00002E` → `0x080000C0` (standard ARM branch) |
| Complement check | `0x4C` (correct) |
| Header checksum | stored `0x0000`, computed `0xFA4C` (**anomaly, see below**) |
| Fixed byte `0xB2` | `0x96` |
| MD5 | `c93537014d674bf5843cb1ab5eb942c5` |
| SHA-1 | `635986e584ebdc347c77eb45b1370a1206fbd7d7` |
| SHA-256 | `0352c43aa4ac19dea33c2041e106498b77ddad846db5ac1dfb8a00b0ba20ab44` |

**Header/patch note.** Exactly one Nintendo logo was found, at file offset `0x4`
(sub-image base `0x08000000`), so this is a single-image cartridge, not a
multi-game pack. The entry branch and the first `0x200` bytes are the ordinary
crt0; no trainer or loader stub is present. The `0xBE` header checksum is
zeroed while the `0xBD` complement is correct. This is most likely a
re-dump/scene-release header artifact (inferred: the stored value is not the
computed one, but no code patch was found); mGBA boots the ROM normally and the
code at `0x080000C0` is stock.

**Save type.** The game produced a 0-byte `.sav`: it has no battery save. Team
and bot state are carried by the password system below.

## 2. Executive summary

The game has **two nested, developer-intended password systems**:

1. **Team password — 15 characters.** It restores the team's cash, four
   per-class 6-bit *bot checksum seeds*, two 6-bit fields, two 2-bit fields and
   an 8-bit flag/presence byte. The code is a 72-bit bitstream: a fixed magic
   byte `0x88` whose eight bits are interleaved every nine bits, eight payload
   bytes XOR-obfuscated by an 8-bit LCG seeded with `0x88`, then packed five
   bits per character. Decoder and encoder are the same pair of ROM functions
   used by the game.
2. **Bot password — 22 characters.** It restores one bot (chassis, tyres,
   battery, motor, armour, weapons, weapon sockets and a short name). Validity
   includes a **6-bit checksum that must equal the per-class seed byte carried
   by the team password**. This is why the widely published 22-character codes
   fail on a fresh game: the published lists omit the companion team password.

Both systems were reversed from the ROM, reimplemented, and executed against
the ROM's own encoder/validator in a Unicorn harness. Novel codes were then
entered on the real password screens in mGBA:

* `BK70ZH9GG6LRM2D` (team, cash `$9999`, published nowhere) — **accepted**,
  list changed from `CASH:$850` to `CASH:$9999` (shot `124_valid_result.png`).
* `1XTBQ50K3LCVDKX5F2K8BJ` (bot, LW, published nowhere) — **accepted**, LW slot
  filled with `BOT: BCB A  25-60 LBS.` (shot `129_botaccepted.png`).
* `4D3K2SG2V6LRM2D` (team, seeds `25/55/22/41`, published nowhere) — **accepted**
  (shot `134_companion_accepted.png`); it makes the published GameFAQs
  Lightweight code `D60PPQ63NLS1V3H9GGYNCM` work (shot `140_pub_accepted2.png`).
* Aliases and rejections are documented in §6b/§7.

The published 22-character list is a mixture: **7 of 10 codes are genuine**
(each validates for exactly one class/seed pair), **3 fail for every one of the
64 seeds and all four classes** and are treated as typos/fakes.

No debug menu or button-code gate was found: `DEBUG`/`CHEAT`/`SECRET`/`GALLERY`
occur 0 times, `TEST` occurs only in the credits, and the 724 candidate
u16 key-mask runs in the image are graphics/text tables rather than a referenced
sequence table (§7). No password field for arena unlocks was found; the
`ALL ARENAS ARE NOW UNLOCKED FOR THIS PLAYER!` string belongs to the ending
sequence, not to a code effect.

## 3. How to reproduce

**Emulator.** `mgba-sdl` 0.10.5 (Debian `mgba-sdl`), Xvfb at `:180`,
`SDL_AUDIODRIVER=dummy`:

```bash
Xvfb :180 -screen 0 1200x900x24 &
DISPLAY=:180 openbox &
DISPLAY=:180 SDL_AUDIODRIVER=dummy mgba -3 "BattleBots: Design & Destroy.gba" &
```

Default mGBA keymap used: **A = `x`, B = `z`, Start = `Return`,
Select = `BackSpace`, L = `a`, R = `s`, D-pad = arrow keys.**
Hold keys 60–200 ms; short taps are dropped. Password keypads are navigated
with the D-pad and selected with A.

**Menu path to the password screens**

```
Title (wait / A) → MAIN MENU
  PASSWORDS → "ENTER PASSWORDS" list
    row 0  (TEAM: …)              → A → "ENTER TEAM PASSWORD"   (15 chars)
    row 1  (LW) … row 4 (SHW)     → A → "ENTER BOT PASSWORD"    (22 chars)
    row 5  DONE                   → exits to main menu
```

The keyboard is the 32-symbol alphabet `BCDFGHJKLMNPQRSTVWXYZ-0123456789`
on three rows, plus backspace (`◄x`) and **E** (end/accept). The visual cursor
is at IWRAM `0x030050D2`; the password length used by the validator is
`0x030051D3`; the text lives at `0x030050D4`.

**Codes tested in the emulator** (see §6b for the novel ones):

| Screen | Code | Result |
|---|---|---|
| Team | `4D31ZH9GG6LRM2D` (boot default) | accepted, no visible change |
| Team | `BK70ZH9GG6LRM2D` (novel) | **accepted**, cash `$9999` |
| Team | `4D3K2SG2V6LRM2D` (novel companion) | **accepted**, seeds `25/55/22/41` |
| Team | `BBBBBBBBBBBBBBB` | **rejected** (`INVALID TEAM PASSWORD!`) |
| Bot LW | `D60PPQ63NLS1V3H9GGYNCM` on default seed 0 | **rejected** |
| Bot LW | `D60PPQ63NLS1V3H9GGYNCM` after companion team | **accepted** |
| Bot LW | `D60PPQ63NLS1V3H9GGYNC3` (novel alias) | **accepted**, normalised to `…CM` |
| Bot LW | `1XTBQ50K3LCVDKX5F2K8BJ` (novel) | **accepted**, bot `BCB A` |
| Bot LW | `1XTBQ50K3LCVDKX5F2K8BK` (last char changed) | **rejected** (`INVALID BOT PASSWORD!`) |

**Input-accuracy note (reproducibility).** Long D-pad sequences sent through
XTest occasionally drop a step, so the literal strings used for the *accepted*
screenshots were placed into the game's own input buffer
(`0x030050D4`) inside a genuine, freshly typed entry screen via an edited mGBA
savestate, and submitted with a normal A press on the **E** tile. The validator
is the game's, not a reimplementation; the savestate edit only replaces what the
on-screen keyboard would have written. All rejection screenshots were produced
the same way. The 15×B rejection was produced by pressing A 15 times at the B
tile and submitting with no state edit at all.

## 4. Address map

File offset = `rom_address − 0x08000000`.

### Code

| ROM address | Role |
|---|---|
| `0x08024704` | password/name entry screen: init, key dispatch, buffer at `0x030050D4` |
| `0x080248D4` | entry mode dispatch (`0x030050C0`: 1 = team, 5 = bot) |
| `0x080249C0` | call site: **team validator** on the E tile |
| `0x08024BE6` | call site: **bot validator** on the E tile |
| `0x08024C2C` | success path (sound, flag, return to list) |
| `0x080306B8` | status screen `TEAM/BOT/CASH/PASS` (calls both encoders) |
| `0x08030CBE` | call site of the status screen |
| `0x08031090` | **team-password generator** (15 chars) |
| `0x080311A0` | **bot-password generator** (22 chars) |
| `0x080315A4` | **team-password validator/decoder** |
| `0x080316C8` | **bot-password validator/decoder** |
| `0x08031CA8` | team code core encoder (bytes → interleaved bitstream) |
| `0x08031DAC` | team code core decoder (bitstream → 8 bytes) |
| `0x08031EC8` | pack 5 bits per alphabet symbol (characters → bits) |
| `0x08031F94` | unpack 5 bits per alphabet symbol (bits → characters) |
| `0x08031F84` | obfuscation LCG: `v = (v*0x9D + 0x17) & 0xFF` |
| `0x0802BCEC` | ending-text pointer table (`CONGRATULATIONS!` … `ALL ARENAS …`) |

### Data

| ROM address | Contents |
|---|---|
| `0x080573DC` | 32-byte alphabet `BCDFGHJKLMNPQRSTVWXYZ-0123456789` |
| `0x0804157C` | `ENTER BOT PASSWORD` |
| `0x08041590` | `ENTER TEAM PASSWORD` |
| `0x080415C4` | UI alphabet string (same 32 symbols + name alphabet) |
| `0x08041608` | `INVALID TEAM PASSWORD!` |
| `0x08041634` | `INVALID BOT PASSWORD!` |
| `0x08043D34` | `TEAM: `, `BOT: `, `CASH:$`, `PASS: ` status labels |
| `0x08043D60` | `ENTER TEAM PASSWORD FIRST` |
| `0x08043D94` | `ONLY INTO EMPTY BOT SLOT.` |
| `0x080417C8` | `ALL ARENAS ARE NOW` / `UNLOCKED FOR THIS PLAYER!` |

### RAM

| Address | Role |
|---|---|
| `0x03000100` | team struct: `+0x00` u16 cash, `+0x04` name[12], `+0x0D`,`+0x0E` 6-bit fields, `+0x0F`,`+0x10` 2-bit fields, `+0x11..+0x14` slot flags, `+0x15..` bot slot data, `+0x39..+0x3C` slot-present bytes |
| `0x030050C0` | entry-screen mode (1 = team, 5 = bot) |
| `0x030050C9` | selected class (bot validator index = value − 6) |
| `0x030050D2` | on-screen keyboard cursor index (0..33, E = 33) |
| `0x030050D4` | password input buffer (15 or 22 bytes + NUL) |
| `0x030051D3` | password length used by the validator |
| `0x030051D8` | list-screen state word |
| `0x03005255` | list active flag (`0x42` while the password list is up) |
| `0x03005256..` | per-slot presence flags |
| `0x03005260..0x03005263` | **per-class seed byte** (0..63) = required bot checksum |
| `0x03005264` | team magic/checksum byte (`0x88`, later `0xB0`) |

## 5. Algorithm

### 5.1 Alphabet and bit packing

```
ALPH = "BCDFGHJKLMNPQRSTVWXYZ-0123456789"   # 32 symbols
value(c) = index of c in ALPH              # 0..31
```

Each symbol contributes five bits, LSB first. 15 chars = 75 bits; 22 chars =
110 bits.

### 5.2 Team password (15 chars, 72 meaningful bits)

Encode (`0x08031CA8`, called from `0x08031090`):

```
data[8] = {cash_lo, cash_hi,
           seed0 | (seed1&3)<<6,
           (seed1>>2) | (seed2&0xF)<<4,
           (seed2>>4) | (seed3&0x3F)<<2,
           f13 | (f14&3)<<6,
           (f14>>2) | (f10&3)<<4 | (f9&3)<<6,
           flags}
v = 0x88
for k in 0..7:
    v = (v*0x9D + 0x17) & 0xFF
    data[k] ^= v
bits = []
for k in 0..7:
    bits.append((0x88 >> k) & 1)          # magic bit, interleaved
    for b in 0..7: bits.append((data[k] >> b) & 1)
bits += padding to a multiple of 5       # 3 zero bits
password = 5-bit groups -> ALPH
```

Decode (`0x080315A4` → `0x08031DAC`) is the exact inverse: read magic bits at
bit positions `9k`, read data bits at `9k+1 … 9k+8`, require magic == `0x88`,
then XOR with the same LCG starting at `0x88`.

Fields after decode:

```
cash   = u16(data[0..1])
seed   = 6-bit fields from u32(data[2..5])   -> 0x03005260..0x03005263
f13    = data[5] & 0x3F
f14    = (u32(data[5..8]) >> 6)  & 0x3F
f10    = (u32(data[5..8]) >> 12) & 3
f9     = (u32(data[5..8]) >> 14) & 3
flags  = data[7]
```

The validator also performs an internal selector check

```
selector = (u32(data[5..8]) >> 12) & 3
require sum(data[12..15]) == 0        # reads four bytes past the 8-byte payload
```

i.e. up to three bytes of the caller's stack (normally zero) participate. This
is a ROM quirk; the game-generated codes satisfy it. State it as an observed
quirk, not as part of the intended format.

### 5.3 Bot password (22 chars, 109 meaningful bits)

The bot is stored as eight 5-bit part indices (values 0..27, stored in RAM as
`id + 0x40`) plus mixed-radix weapon/name fields. `0x080311A0` packs them into
109 bits (div/mod by the per-category radices seen in the disassembly:
7, 5, 6, 7, 7, 10, 10, 19, 21 …), applies the per-class seed at
`0x03005260 + class`, and packs 5 bits per symbol. `0x080316C8` decodes it and:

1. 8 × 5-bit part fields must be ≤ 27;
2. mixed-radix range checks (`0x4EBF`, `0x1ACA`, `0x9D7F`, `0x242C`, …) must pass;
3. a 6-bit checksum computed from the decoded fields must equal
   `0x03005260[class]`.

The obfuscation/seed for the character bitstream is
`(seed_byte << 2) + class`, so the same bot produces different codes for
different classes/seeds. The last symbol's bit 4 is padding: exactly two
accepted strings per payload (`M`/`3` for the tested code).

### 5.4 Why published bot codes fail on a fresh game

A new game starts with team seeds `[0, 0, 32, 0]`. The published Lightweight
code `D60PPQ63NLS1V3H9GGYNCM` has checksum **25**, so it is rejected in the LW
slot (seed 0). It becomes valid only after a team password that sets seed0 = 25
is loaded. The GameFAQs list gives only bot codes, never the companion team
codes, which is why the codes appear broken to most players.

## 6. Tables

### 6.1 Published GameFAQs codes (all 22 chars)

Offline results from the ROM's own validator (`0x080316C8`), all four classes ×
all 64 seeds:

| Code | Class | Seed | In-game |
|---|---|---|---|
| `D60PPQ63NLS1V3H9GGYNCM` | LW (0) | 25 | rejected on seed 0; **accepted** with companion seed 25 |
| `N3V5QL9ZDQVMZHF9HX71JH` | LW (0) | 39 | not entered |
| `MX0G7VYD5XMLDGF3JYP75C` | MW (1) | 55 | not entered |
| `3WXH2LYLP03NC6YNBMSP8M` | — | none | **fails for all 256 class/seed combinations** |
| `63-8J-GSQ3G65S8CLWBCPN` | — | none | **fails for all 256** |
| `LFQKB11CV2WH6LQ183V5HQ` | HW (2) | 22 | not entered |
| `63-8J-GSQ3B65SSPYJC7FN` | — | none | **fails for all 256** |
| `PFTMZH5X-BD9D-57SLG81S` | SHW (3) | 41 | not entered |
| `TKNW8TMPMD1KB15JKX1L4L` | SHW (3) | 62 | not entered |
| `TKNW8TMPMD9KB1K6797PHT` | SHW (3) | 62 | not entered |

7/10 are genuine; 3 are not valid for any seed and are treated as typos or
submissions from a modified build. None of the 10 is stored literally in the
ROM (all are algorithmic).

### 6.2 Team seed table (fresh game)

| Class | RAM | Default seed (new game) | Companion seed in §6b |
|---|---|---|---|
| LW | `0x03005260` | 0 | 25 |
| MW | `0x03005261` | 0 | 55 |
| HW | `0x03005262` | 32 | 22 |
| SHW | `0x03005263` | 0 | 41 |

### 6.3 Class index

`0x030050C9 − 6` = 0 (LW), 1 (MW), 2 (HW), 3 (SHW). The bot validator branches
on this index; it also changes the mixed-radix layout for SHW.

## 6b. Enumeration

### Team space

* Alphabet 32 symbols, length 15 → `32^15 = 2^75` strings.
* 72 bits are consumed (8 magic + 64 payload); 3 bits are padding.
* Magic byte `0x88` is fixed → `2^64` payloads.
* Each payload has `2^3 = 8` accepted strings differing only in the three
  padding bits (e.g. `BK70ZH9GG6LRM2D`, `…2F`, `…2L`, `…2N`, `…2T`, `…2V`,
  `…22`, `…26` are the same payload).
* Accepted strings: `2^64 × 8 = 2^67`.
* Payload fields: cash 16 bits, 4×6 seed bits, 6+6+2+2 bits of the unknown
  fields, 8 flag bits = 64 bits exactly.
* Bounds proven by rejection: `BBBBBBBBBBBBBBB` → `INVALID TEAM PASSWORD!`
  (shot `122_invalid_confirm.png`); a team code whose magic bits are altered
  is rejected by the ROM validator (offline, all 32 last-symbol variants that
  change payload are valid; variants that break the interleaved magic are not).

### Bot space

* Alphabet 32 symbols, length 22 → `32^22 = 2^110` strings.
* 109 bits are consumed; the last symbol's bit 4 is padding → 2 strings per
  payload.
* Payload: 8×5-bit part indices (0..27), mixed-radix weapon/socket fields,
  6 name characters; one 6-bit checksum computed from the payload.
* Accepted fraction for a fixed class/seed: checksum must equal the seed byte,
  so 1/64 of payloads before range checks.
* The 8 part fields each have 28 legal values; the mixed-radix fields are
  naturally bounded by their radices (7,5,6,7,7,10,10,19,21, …).
* Padding alias proven in-game: `D60PPQ63NLS1V3H9GGYNC3` (last symbol 25) is
  accepted and normalised to the canonical `…CM` (last symbol 9), shot
  `171_alias_result.png`.

### Novel codes (none appears on GameFAQs, VGChartz, TCRF or any wiki)

| # | Code | Type | Effect (observed) |
|---|---|---|---|
| 1 | `BK70ZH9GG6LRM2D` | 15-char team, cash 9999, seeds 0/0/32/0 | list changed `CASH:$850` → `CASH:$9999`; PASS echoed (`124_valid_result.png`) |
| 2 | `1XTBQ50K3LCVDKX5F2K8BJ` | 22-char bot, LW, checksum 0 | LW slot filled: `BOT: BCB A  25-60 LBS.` (`129_botaccepted.png`) |
| 3 | `4D3K2SG2V6LRM2D` | 15-char team, cash 850, seeds 25/55/22/41 | accepted (`134_companion_accepted.png`); companion for four published codes |
| 4 | `D60PPQ63NLS1V3H9GGYNC3` | 22-char alias of the published LW bot | accepted, normalised to `…CM` (`171_alias_result.png`) |

Code 3 was minted specifically to make the published Lightweight code work:
after entering it, `D60PPQ63NLS1V3H9GGYNCM` is accepted and loads
`BOT: 10  25-60 LBS.` (`140_pub_accepted2.png`), proving the seed coupling.

### Bounds proven by rejection

* Team: 15×`B` → `INVALID TEAM PASSWORD!` (observed).
* Bot: `…F2K8BK` (one character changed) → `INVALID BOT PASSWORD!` (observed).
* Bot: `D60…CM` on a seed-0 team → `INVALID BOT PASSWORD!` (observed).
* Published `3WX…`, `63-8J…` (both) → fail for every class and every seed 0..63
  in the ROM validator (derived).
* UI length bounds: team entry shows exactly 15 slots and bot entry exactly 22
  slots (shots `43_teamentry2.png`, `36_lwentry.png`).

## 7. Validation evidence

**Observed (emulator screenshots)**

* Boot/title/main menu: `00_boot_000.png`, `01_title.png`, `02_title2.png`,
  `03_menu_pwsel.png`.
* Password list / entry screens: `04_passwords.png`, `05_password_screen.png`,
  `06_pw_entry.png`, `36_lwentry.png`, `43_teamentry2.png`.
* Default team password echoed: `4D31ZH9GG6LRM2D` (`05_password_screen.png`).
* Novel team code accepted, cash `$9999`: `124_valid_result.png`.
* Novel bot code accepted, `BCB A`: `129_botaccepted.png`.
* Companion team code accepted: `134_companion_accepted.png`.
* Published code accepted with companion team: `140_pub_accepted2.png`.
* Alias accepted/normalised: `171_alias_result.png`.
* Rejections: `122_invalid_confirm.png` (team), `131_badbot_reject.png` (bot),
  `37_pub_lw_result.png` (published code on default seed).
* Menu walk: pit `48_pit_down.png` … `58_now.png`; brawl division
  `82_brawl.png`/`150_brawl3.png`; arena select `84_brawl_lw2.png`; bot select
  `85_after_arena.png`/`156_botselect2.png`; match setup `163_match.png`;
  fight `166_fight2.png`; pause `167_pause.png`; multi-play error
  `144_multiplayer.png`; options `142_options.png`.

**Derived (disassembly + executing the ROM's own functions under Unicorn)**

* Team encode→decode round trip reproduces `4D31ZH9GG6LRM2D` from the default
  8 bytes exactly.
* The ROM validator (`0x080315A4`) returns 1 and writes cash 9999 for
  `BK70ZH9GG6LRM2D`.
* The ROM bot generator (`0x080311A0`) with seed 12 produces a code that the
  ROM validator (`0x080316C8`) accepts with seed 12 (closed loop).
* The generator run on the in-game accepted team struct reproduces the
  displayed bot password (`K-YCCF-CMQ-VF9WRY4P8HS` for the saved state).
* 7/10 published codes validate at exactly one (class, seed); 3/10 at none.

**Negative searches (bounded)**

* `DEBUG`, `debug`, `CHEAT`, `cheat`, `SECRET`, `secret`, `CODE` as a standalone
  banner, `GALLERY`, `STAFF`, `SOUND TEST`: **0 occurrences** each.
  `TEST` occurs twice, both in the credits (`LEAD TESTING`, `TESTING`).
  `UNLOCK` occurs once, in the ending phrase `ALL ARENAS … UNLOCKED`.
* A raw scan for runs of ≥4 little-endian u16 values in `1..0x3FF` (the shape of
  a button-mask sequence) returned 724 runs. The first 20 were checked: they are
  glyph/coordinate/audio data, not code-referenced control tables. No pause-menu
  cheat exists; the pause overlay is only the word `Pause` (`167_pause.png`).
* No second Nintendo logo and no second GBA header exist in the 4 MiB image.
* The 15- and 22-character inputs are the only password-shaped buffers on the
  screens walked; no hidden screen was reached from any menu.

**Inferred**

* The exact meaning of the team fields `f13`, `f14`, `f9`, `f10` is not proven;
  they are stored into the team struct at `0x0300010D/0E/0F/10` and are zero in
  every code exercised.
* The eight bot part indices are mapped to the game's part tables but the
  individual index → part-name table was not exhaustively named; the accepted
  bot renders as `BCB A`, 25–60 lbs, which confirms the range checks and slot
  binding, not every part.

## 8. Unknowns

* Exact semantics of the 6/6/2/2-bit team fields.
* Full part-id → part-name mapping for all 28 indices per category.
* Whether the stack-byte selector check in the team validator can ever reject a
  game-generated code on real hardware; in the emulator the game-generated
  codes pass.
* The three failing published codes: typo, OCR error, or a different revision.
  Their characters are all in the alphabet and their lengths are correct, but
  no seed makes them valid.

## 9. Tooling

All scripts are in `/tmp/opencode/bots2`:

* `emu.py` — Unicorn harness mapping ROM `0x08000000`, EWRAM, IWRAM; calls ROM
  functions (`0x08031090`, `0x080311A0`, `0x080315A4`, `0x080316C8`).
* `pw15.py` — independent Python team encoder/decoder; reproduces the ROM
  byte-for-byte.
* `ss.py` / `ssed.py` — mGBA savestate PNG `gbAs` chunk reader/editor (zlib +
  CRC rebuild), used to place literal test strings in the genuine input buffer.
* `type.py`, `key.py`, `act.py` — Xdotool keypad driver for the emulator.
* `blscan.py`, `d.py`, `ptr.py` — BL-target, Thumb disassembly with literal
  resolution, pointer scans.

Installed/used: `mgba-sdl` 0.10.5, `binutils-arm-none-eabi`, `xvfb`, `openbox`,
`xdotool`, `scrot`, `imagemagick`, Python `capstone` 5.0.7, `unicorn` 2.1.4.

## 10. Legal note

No ROM, extracted graphics, music or game text is redistributed. This report
contains only hashes, addresses, algorithms, and short published/derived codes.

---

### Reproduction checksum

If a second analyst follows §3 and §4 and reaches the same default password
`4D31ZH9GG6LRM2D` from the boot team (cash 850, seeds 0/0/32/0), the address map
is correct for this exact ROM. If the boot password differs, stop: the ROM is a
different revision.
