# Disney's Atlantis: The Lost Empire (GBA) — Reverse Engineering Report

## 1. Target identity

| Item | Value |
|---|---|
| File | `roms/Disney's Atlantis: The Lost Empire/Disney's Atlantis: The Lost Empire.gba` |
| Size | 4,194,304 bytes (4 MiB) |
| Header title | `ATLANTIS` (0xA0, NUL padded) |
| Game code | `ATLE` |
| Maker code | `78` (THQ) |
| Software version | `0x00` (Rev.00) |
| Entry word | `0xEA00002E` (stock `b 0x080000C0`, not a cracktro) |
| Complement check | stored `0x5C`, computed `0x5C` (valid) |
| Header checksum field | `0x0000` (rebuilt-header artifact; complement byte is the reliable signal) |
| MD5 | `b56f85ff2f37c51acd2e2561abbccb64` |
| SHA-1 | `10d77cb1f9cb1f6670367dda9b6a88909e39b322` |
| SHA-256 | `230fe03e2645503c2657144df8085ad7eca03a62b812f01e9c49158c830046f9` |

Embedded-header scan: exactly one 156-byte Nintendo logo hit (file `0x4`), so this is a
single image, not a 2-in-1 pack. No trainer/cracktro text or appended menu was found.
Strings identify 3d6 Games Inc. / THQ, build string `JULY 18 2001`. mGBA creates a
0-byte `.sav`: the game is password-based, not battery-save based.

## 2. Executive summary

The game has a developer-intended **8-character password system** on the
`CONTINUE` path. It encodes progress into a base-26 integer: level, crystal
progress, continues, shard/runes count, music volume, sound volume, A/B swap and a
cheat flag, plus an 8-bit check.

* Alphabet (26 symbols, ROM `0x08344192`): `BCDFGHJKLMNPQRSTVWXYZ34679`
  (vowels and `0,1,2,5,8` are deliberately absent).
* Decoded value `v` is the big-endian base-26 number of the eight symbols.
  `v % 201` must equal `H(v / 201) % 200`, where `H` is an 11-round
  `key ^= low32; ror64 3` hash seeded with `0xDBF0DEAD`.
* Payload (`v / 201`) is mixed-radix:
  `F24(2) F18(801) F10(20) F14(9) F0C(11) F08(11) F04(2) F1C(9)`.
* Semantic bounds (checked after the checksum): `F1C <= level-1` and
  `F18 <= crystals available in all previous levels`.

The input space is `26^8 = 208,827,064,576` strings. Exactly **212,001,680** of
them are accepted (per-level counts in §6b), i.e. about 0.1015 %.

Published lists were checked against the ROM. Three published codes cannot even
be typed (they use symbols absent from the alphabet) and one — the famous
"Infinite weapons" code — has a checksum typo: the ROM's literal is
`K4MFCNPG`, not `K4MFCPNG`. The ROM's own code is accepted; the published
spelling is rejected.

Novel, unpublished codes were minted, entered and verified (screen + RAM):

* `DF4NBHFP` — Level 8 with **CONTINUES 20** (published codes only ever encode 3).
* `DFVX69Z3` — Level 8 with **MUSIC 5 / SOUND OFF / SWAP BUTTONS ON**
  (every published code encodes 10/10/off).
* `HJRGKQ3L` — Level 8 at the exact crystal-index boundary `F18 = 535`.
* `K4MFCNPG` — the ROM literal cheat, accepted and sets the cheat flag byte.

No button-code system and no hidden/debug menu were found; every reachable screen
was walked, and the static/text search spaces are stated in §7.

## 3. How to reproduce

Emulator: `mgba 0.10.5`, SDL frontend under `Xvfb :319`, `SDL_AUDIODRIVER=dummy`.
Default SDL keymap: **A = `x`, B = `z`, Start = `Return`, Select = `BackSpace`,
D-pad = arrows, L = `a`, R = `s`**. Hold keys ~60–150 ms; the password field
accepts one step per press.

Menu path:

1. Boot → title screen (`PRESS START`) → **Start**.
2. `MAIN MENU`: `NEW GAME / CONTINUE / OPTIONS`.
   * `NEW GAME` → Level 1 (`PRESTON WHITMORE'S MANSION`).
   * `OPTIONS` → `MUSIC / SOUND / SWAP BUTTONS / GAME CREDITS`.
3. **Down** to `CONTINUE` → **Start** → `ENTER PASSWORD` (8 cells).
4. In the password screen: **Left/Right** move the cell (wraps at the ends),
   **Up/Down** change the symbol (Down advances, Up rewinds; 26 steps wrap
   `9 → B`), **Start** submits, **B** returns to the main menu.
5. A valid code opens the level intro (`LEVEL n`, objective, level crystal total,
   `PRESS START`); **Start** enters the level. An invalid code shows
   `INVALID PASSWORD`.

Savestate workflow used: a snapshot of the untouched password screen
(`BBBBBBBB`, cursor in cell 1) in mGBA slot 1. `F1` reloads it, so each test is
type-code → Start instead of replaying the intro. mGBA `Shift+F1..F8` saved the
evidence states; the `.ss*` PNGs contain a zlib `gbAs` chunk (397,312 bytes,
IWRAM at `0x19000`, EWRAM at `0x21000`) that was decoded to read RAM.

Codes tested in the emulator (all with the exact key path above):

| Code | Purpose | Result |
|---|---|---|
| `DFVYPJ3S` | published Level 8 | accepted → `LEVEL 8`, crystals 120 |
| `JPKDJCCR` | published Level 10 | accepted → `LEVEL 10` |
| `K4MFCNPG` | ROM literal cheat | accepted, flag byte `0x03001A13 = 1` |
| `K4MFCPNG` | published "infinite weapons" spelling | rejected → `INVALID PASSWORD` |
| `DF4NBHFP` | novel (continues 20) | accepted → `CONTINUES 20` |
| `DFVX69Z3` | novel (music/sound/swap) | accepted → `MUSIC 5`, `SOUND OFF`, `SWAP ON` |
| `DF4NBHPK` | `F1C = 8` at level 8 | rejected → `INVALID PASSWORD` |
| `HJRGKQ3L` | `F18 = 535` boundary | accepted → `LEVEL 8` |
| `HJYZX46N` | `F18 = 536` | rejected → `INVALID PASSWORD` |
| `DFVYPH7N` | `F1C = 0` | accepted → `LEVEL 8` |

## 4. Address map

ROM address = `0x08000000 + file_offset`. RAM addresses are absolute.

| Address | Kind | Meaning |
|---|---|---|
| `0x08344192` | ROM string | password alphabet `BCDFGHJKLMNPQRSTVWXYZ34679` |
| `0x08344300` | ROM string | `K4MFCNPG` (the only literal cheat code in the image) |
| `0x08346AD8` | ROM table | level records, 36 bytes each, ID at `+0`, crystal total `+0x08`, shard flag `+0x0C` |
| `0x083DC700` | ROM table | UI message/pointer table; `Invalid Password` pointer at `0x083DC990` |
| `0x0818B798` | Thumb func | **password validator** (called with `r0 = menu_obj + 0x504`) |
| `0x08189C90` | call site | validator call from the menu state machine; `-1` = invalid |
| `0x0818BDE4` | Thumb func | decode 8 digits at `0x02000024` → 64-bit base-26 value `v` |
| `0x0818BD54` | Thumb func | `v % 201` (check field) |
| `0x0818BD68` | Thumb func | checksum hash `H(v / 201)`, key `0xDBF0DEAD`, 11 rounds, `ror64 3`, then `% 200` |
| `0x0818BB14` | Thumb func | split payload into the nine mixed-radix fields |
| `0x0818BCE0` | Thumb func | semantic range check + apply gate |
| `0x0818BCB0`, `0x0818BCC8` | Thumb funcs | bound calls using level table sums `0x08190E64` (crystals) / `0x08190E40` (shard levels) |
| `0x0818BC4C` | Thumb func | write decoded fields into the game struct |
| `0x0818B8FC` | Thumb func | **encoder**: live game state → password value (then checksum) |
| `0x0818BD2C` | Thumb func | 8 numeric digits → alphabet string |
| `0x0818BDAC` | Thumb func | 64-bit value → 8 base-26 digits |
| `0x0818D880` | Thumb func | `ENTER PASSWORD` screen update/draw |
| `0x02000024` | EWRAM | the 8 input digits, one `u32` each (observed while entering; read by the validator) |
| `0x03001A08` | IWRAM | game/progress struct base |
| `0x03001A0A` | IWRAM `u16` | `F18` crystal-progress index |
| `0x03001A0E` | IWRAM byte | `F1C` shard/runes value |
| `0x03001A10` | IWRAM byte | continues (1..20) |
| `0x03001A11` | IWRAM byte | level (2..10) |
| `0x03001A13` | IWRAM byte | cheat/bonus flag (0/1) |
| `0x03001A20` | IWRAM `u32` | music volume (0..10) |
| `0x03001A24` | IWRAM `u32` | sound volume (0..10) |
| `0x03001A28` | IWRAM `u32` | swap A/B (0/1) |

## 5. Algorithm

```
ALPHABET = "BCDFGHJKLMNPQRSTVWXYZ34679"        # 26 symbols

decode_string(code[8]):
    v = 0
    for ch in code: v = v*26 + index_of(ALPHABET, ch)

hash(x):                                       # x is the payload v/201
    key = 0xDBF0DEAD
    lo, hi = x & 0xFFFFFFFF, x >> 32
    repeat 11:
        key = (key ^ lo) & 0xFFFFFFFF
        lo, hi = ((lo >> 3) | (hi << 29)) & 0xFFFFFFFF, hi >> 3
    return key

validate(code):
    v = decode_string(code)
    if v % 201 != hash(v / 201) % 200: return INVALID     # 0x0818B798 / 0x0818BD68
    p = v / 201
    F1C = p % 9;  p //= 9
    F04 = p % 2;  p //= 2
    F08 = p % 11; p //= 11
    F0C = p % 11; p //= 11
    F14 = p % 9;  p //= 9
    F10 = p % 20; p //= 20
    F18 = p % 801;p //= 801
    F24 = p % 2
    level = F14 + 2
    if F1C > min(level-1, 8): return INVALID              # 0x0818BCE0
    if F18 > min(800, sum(crystals[1..level-1])): return INVALID
    return ACCEPT

encode(fields):
    p = F1C
    p = p*9 + F04
    p = p*11 + F08
    p = p*11 + F0C
    p = p*9 + F14
    p = p*20 + F10
    p = p*801 + F18
    p = p*2 + F24
    v = p*201 + hash(p) % 200
    return 8 base-26 digits of v, most significant first
```

`F1C` is bounded by `level-1`, not by 8, for levels 2..9; for levels 9 and 10 the
level table's shard flags stop at 8, so the bound is 8.

## 6. Tables

### Alphabet

`B C D F G H J K L M N P Q R S T V W X Y Z 3 4 6 7 9` (26 symbols; indices 0..25).

`A E I O U 0 1 2 5 8` are not enterable; the field cycle returns `B` after exactly
26 Down presses and the 27th gives `C` (observed).

### Fields

| Field | Radix | Stored value | Meaning | Evidence |
|---|---:|---|---|---|
| `F14` | 9 | 0..8 | level − 2 (displayed level 2..10) | observed level intros |
| `F10` | 20 | 0..19 | continues − 1 (displayed 1..20) | observed `CONTINUES 20` |
| `F0C` | 11 | 0..10 | music volume | observed options `MUSIC 5` |
| `F08` | 11 | 0..10 | sound volume | observed options `SOUND OFF` |
| `F04` | 2 | 0/1 | swap A/B | observed options `SWAP ON` |
| `F1C` | 9 | 0..8 | shard/runes count; bound `<= level-1` | bound observed by rejection; label inferred |
| `F18` | 801 | 0..800 | crystal-progress index; bound `<= prior-level crystal total` | bound observed; label derived |
| `F24` | 2 | 0/1 | cheat/bonus flag ("infinite weapons/items" in published lists) | flag byte observed; visual effect not isolated |
| check | 201 | 0..199 | `H(payload) % 200` | observed by rejection/acceptance |

### Level table (`0x08346AD8`, 36-byte records)

| ID | Level | Crystals (+0x08) | Shard flag (+0x0C) | Prior crystal sum used as `F18` bound |
|---:|---:|---:|---:|---:|
| 1 | 1 | 65 | 1 | — |
| 2 | 2 | 22 | 1 | 65 |
| 3 | 3 | 24 | 1 | 87 |
| 4 | 4 | 86 | 1 | 111 |
| 5 | 5 | 59 | 1 | 197 |
| 6 | 6 | 90 | 1 | 256 |
| 7 | 7 | 189 | 1 | 346 |
| 8 | 8 | 120 | 1 | 535 |
| 9 | 9 | 0 | 0 | 655 |
| 10 | 10 | 0 | 0 | 655 |
| 12..17 | — | 0 | 0 | not reachable via password |

Observed confirmation of `+0x08`: Level 2 intro shows crystals 22, Level 8 shows
120, Level 10 shows 0.

### Published codes vs the ROM

| Code | Published label | ROM model | Emulator |
|---|---|---|---|
| `DFVYPJ3S` | Level 8 | valid | **accepted → LEVEL 8** |
| `JPKDJCCR` | Level 10 | valid | **accepted → LEVEL 10** |
| `BJWFTF6P` | Level 2 | valid | not individually typed (validator-verified) |
| `BKGD2WW4` | Level 3 | **impossible** (`2` not in alphabet) | cannot be entered |
| `BJWGSC7L` | Level 3 | valid | validator-verified |
| `BKWNVMMD` | Level 4 | valid | validator-verified |
| `BKWYJSB9` | Level 4 | valid | validator-verified |
| `BVMKDWK9` | Level 5 | valid | validator-verified |
| `BW4YD3X6` | Level 5 | valid | validator-verified |
| `CBZ6NMKR` | Level 6 | valid | validator-verified |
| `CBCLXMLR` | Level 6 | valid | validator-verified |
| `BMQDNPJS` | Level 2 | valid | validator-verified |
| `BRZSGZDY` | Level 3 | valid | validator-verified |
| `BVMJFYLG` | Level 4 | valid | validator-verified |
| `B7JHPMHC` | Level 5 | valid | validator-verified |
| `C6XQLUNF` | Level 6 | **impossible** (`U` not in alphabet) | cannot be entered |
| `COCNQQIY` | Last level | **impossible** (`O`,`I` not in alphabet) | cannot be entered |
| `K4MFCPNG` | Infinite weapons | **bad checksum** | rejected → `INVALID PASSWORD` |
| `K4MFCNPG` | (ROM literal) | valid, `F24=1` | **accepted; `0x03001A13=1`** |

The "2/O/I/U" codes are most plausibly Game Boy Color codes (the GBC game uses
4-character codes such as `XDKV`) or transcription errors; they are not
representable on the GBA keypad.

## 6b. Enumeration

**Input space.** 26 symbols × 8 positions = **208,827,064,576** strings.

**Checksum layer.** For every payload `p` there is exactly one accepted check
value `c = H(p) % 200`, so 628,048,080 payload values are checksum-representable;
all of them fit in 8 base-26 digits because
`628,048,079*201 + 199 = 126,237,664,078 < 26^8`.

**Semantic layer.** The ROM then enforces `F1C <= level-1` and
`F18 <= prior-level crystal total`. Exact accepted counts:

| Level | `F14` | max `F1C` | max `F18` | Accepted codes |
|---:|---:|---:|---:|---:|
| 2 | 0 | 1 | 65 | 1,277,760 |
| 3 | 1 | 2 | 87 | 2,555,520 |
| 4 | 2 | 3 | 111 | 4,336,640 |
| 5 | 3 | 4 | 197 | 9,583,200 |
| 6 | 4 | 5 | 256 | 14,926,560 |
| 7 | 5 | 6 | 346 | 23,512,720 |
| 8 | 6 | 7 | 535 | 41,507,840 |
| 9 | 7 | 8 | 655 | 57,150,720 |
| 10 | 8 | 8 | 655 | 57,150,720 |
| **total** | | | | **212,001,680** |

`C = 2 (F24) × 20 (F10) × 11 (F0C) × 11 (F08) × 2 (F04) = 9680` combinations of the
other fields per level; each row is `C × (maxF1C+1) × (maxF18+1)`.

**Novel code 1 — `DF4NBHFP`** (not in GameFAQs, VGChartz, TCRF or any list checked):
level 8, `F18=218`, `F10=19`, `F1C=7`, volumes 10/10, swap off, cheat 0.
* Entered on the real screen: `LEVEL 8` intro accepted.
* Pause screen: **`CONTINUES 20`** (published codes encode only 3).
* RAM (`ss6`): `0x03001A10=20`, `0x03001A11=8`, `0x03001A0E=7`,
  `0x03001A0A=218`.
* Rejection bound: `DF4NBHPK` (same fields but `F1C=8`) → `INVALID PASSWORD`
  (`F1C <= level-1 = 7`).

**Novel code 2 — `DFVX69Z3`**:
level 8, `F18=218`, `F1C=3`, `F10=2`, `F0C=5`, `F08=0`, `F04=1`.
* Entered: `LEVEL 8` intro accepted.
* Pause → OPTIONS: **MUSIC 5 / SOUND OFF / SWAP BUTTONS ON**. Every published
  code encodes 10/10/off, so this combination is outside every published list.
* RAM (`ss7`): `0x03001A20=5`, `0x03001A24=0`, `0x03001A28=1`.

**Boundary proof.** `HJRGKQ3L` (`F18=535`, the exact maximum for level 8) is
accepted and shows `LEVEL 8`; `HJYZX46N` (`F18=536`) is rejected with
`INVALID PASSWORD`. This proves the `F18` bound is exact, not merely "large
values fail".

**Checksum proof.** `K4MFCPNG` (the spelling printed by GameFAQs/Neoseeker) is
rejected; the ROM literal `K4MFCNPG` is accepted and sets `0x03001A13=1`. The
offline model agrees with both.

**Alphabet bounds.** The field cycles through exactly 26 symbols
(`B … 9 → B`); therefore `BKGD2WW4` (contains `2`), `COCNQQIY` (`O`,`I`) and
`C6XQLUNF` (`U`) cannot be entered at all — the failure is the keypad, before the
validator.

## 7. Validation evidence

**Observed (emulator / RAM):**

* `DFVYPJ3S` → `LEVEL 8`, `JPKDJCCR` → `LEVEL 10`, `K4MFCNPG` → accepted.
* `DF4NBHFP` → `CONTINUES 20`; RAM `0x03001A10=20`.
* `DFVX69Z3` → `MUSIC 5`, `SOUND OFF`, `SWAP ON`; RAM `0x03001A20=5`,
  `0x03001A24=0`, `0x03001A28=1`.
* `DF4NBHPK` (`F1C=8`) and `HJYZX46N` (`F18=536`) → `INVALID PASSWORD`;
  `HJRGKQ3L` (`F18=535`) → accepted.
* `K4MFCPNG` → `INVALID PASSWORD`; `K4MFCNPG` → accepted, `0x03001A13=1`.
* 26-symbol input cycle; all screens listed in §3 walked, including title, main
  menu, options, credits, password entry, level intro, HUD, pause, pause options,
  quit confirmation.
* Savestate diffing was used to read RAM; no GDB stub was needed for the final
  proofs (a GDB session at `0x0818B798`/`0x0818BD98` produced the checksum
  constants and confirmed `v % 201 = 37` vs `H(v/201) % 200 = 37` for
  `DFVYPJ3S`).

**Derived (instruction sequence / tables):**

* Validator, hash, mixed-radix decode, semantic gate, apply and encoder
  addresses and pseudocode in §4–§5.
* `v = Σ digit_i·26^(7-i)`; digits at `0x02000024`; alphabet at `0x08344192`.
* Level records at `0x08346AD8` and the exact per-level counts.
* Encoder at `0x0818B8FC` reads the live struct at `0x03001A08` and rebuilds the
  same mixed-radix value, confirming the field↔state mapping independently of
  the decoder.

**Inferred:**

* `F1C` = shard/runes count (bound `<= level-1`, story text "SHARDS OF THE
  KING'S CRYSTAL", level 10 objective "MATCH THE RUNES").
* `F18` = crystal-progress index (bound equals prior-level crystal totals).
* `F24` = cheat/bonus flag; published as "Infinite weapons/items".

**Negative spaces checked:**

* `strings -t x -n 4` over the whole ROM: password/`INVALID PASSWORD`/`ENTER
  PASSWORD`/`Main Menu`/`Bonus`/`Crystals`/`Continues`/`Runes`/`Health` exist;
  no `debug`, `cheat`, `sound test`, `gallery` or unlock-menu string exists
  (the only "Testers"/"SECRETS" hits are credits and dialogue).
* Only one literal code exists in the image (`K4MFCNPG`); all other accepted
  codes are algorithmic.
* Button-code scan: every 2-byte window was checked for runs of ≥4 consecutive
  10-bit GBA key masks; 47 runs were found, all repeated-value data in
  audio/script regions (e.g. `0x154964` is 22×`0x0008`), with no validator,
  no pointer table and no pause/title handler. No button-code system.
* Menu state machine at `0x08189BB8` (12 entries) maps only to the screens
  walked; no unreachable/hidden state was found.

## 8. Unknowns

* `F1C`'s visible in-game representation (shard/runes counter) was not located
  on a HUD; its numeric effect and the exact bound are proven, the label is
  inferred from the bound and the game's story text.
* `F18`'s exact use (crystal bitmap index vs. collected count) was not isolated
  visually; its exact bound is proven by acceptance/rejection.
* `F24`'s gameplay effect ("infinite weapons/items") was not exhausted in play:
  the code is accepted and the flag byte `0x03001A13` is set, but level 2 offers
  no weapon/ammo HUD element to observe depletion. The published label is
  treated as unverified, not as an observation.
* Levels 11–17 exist as level-table records (IDs 12–17, zero crystals) but the
  password's `F14` radix caps the selectable level at 10; whether they are
  reachable by any other route was not investigated.
* Published codes listed as "validator-verified" in §6 were checked against the
  reimplemented ROM validator and field bounds, not all typed individually in
  the emulator; the four that matter (two level codes, the cheat, the typo)
  were typed.

## 9. Tooling

* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`
* `python3` + `capstone 5.0.7` for literal/BL scans.
* `/tmp/opencode/atlantis/scan.py` — literal pointer scan.
* `/tmp/opencode/atlantis/blscan.py` — Thumb BL target scan.
* `/tmp/opencode/atlantis/pw.py` — validator/encoder model (the code in §5).
* `/tmp/opencode/atlantis/type2.py` — reproducible key injection
  (`xdotool`, 60/80 ms hold/gap).
* Savestate reader: parse the PNG chunks, `zlib.decompress` the `gbAs` chunk;
  IWRAM `0x19000`, EWRAM `0x21000`.
* mGBA 0.10.5, Xvfb, openbox, scrot/ImageMagick. Screenshots and savestates were
  kept only in `/tmp/opencode/atlantis` as working evidence; nothing from the
  ROM (graphics, text, audio) is redistributed here.

## 10. Legal note

No ROM, extracted graphics, audio or copyrighted text is redistributed. Only
hashes, addresses, algorithm structure, field layouts and newly generated codes
are published above.
