# Elf: The Movie (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Elf: The Movie/Elf: The Movie.gba` |
| Size | 4,194,304 bytes (4 MiB, `0x400000`) |
| `file` | Game Boy Advance ROM image: "ELF" (BELE4Z, Rev.00) |
| Header title | `ELF` (12-byte field `ELF\0\0\0\0\0\0\0`) |
| Game code | `BELE` |
| Maker | `4Z` |
| Version | `0x00` |
| Fixed byte `0x96` | present (`0x96`) |
| Entry branch | `0xEA00002E` (stock crt0 -> `0x080000C0`) |
| Header checksum | `0x0000` (rebuilt-header artifact per §16.1), complement `0xD4` |
| MD5 | `1fe0aa775a55230c0cf8236f4376dbe9` |
| SHA-1 | `06b313920e7adc05a0f4c968d05f9db70926c0ab` |
| SHA-256 | `d23dcb39c58356f71220a986dba9fdf709a5c137c58644fec524ee1f08c06062` |

Embedded-header scan: exactly **one** Nintendo logo (header at file `0x0`). No trainer, no multi-game pack, no cracktro patch — retail single image. (Derived: §Phase 0 scan.)

## 2. Executive summary

The game has a genuine developer-intended **5-letter password system** on
`Story Mode → Enter Code`. The on-screen alphabet is the 21 consonants
`BCDFGHJKLMNPQRSTVWXYZ` (no vowels), and each code letter is stored as a
0-based index into that alphabet (not as ASCII) in an IWRAM buffer at
`0x300145A`. The validator at `0x0801C7A0` is fully reversible:

* it packs the first four indices into a 15-bit-ish word,
* checks a 3-bit checksum derived from a constant `0x303B`,
* and on success dispatches through a 14-entry jump table keyed by the fifth
  letter to write result fields into the state struct at `0x3001420`.

All eight published codes found on 3rd party cheat indexes
satisfy the recovered checksum, so the model is validated against the real
published list. Two **novel**, never-published codes were generated and both
were accepted on the real `Enter Code` screen in mGBA with RAM proof:

* **`GBBBC`** → the icicle-cave level hint screen; validator fields
  `+8=4, +12=2, +16=20`.
* **`JBBBF`** → a Santa workshop cutscene; validator fields
  `+8=13, +12=1, +16=30`.

Invalid codes (`BBBBB`, `ZZZZZ`) are rejected in-game (immediate return to the
Main Menu) and rejected by the oracle, proving the checksum bounds.

Exact space: `21^5 = 4,084,101` strings; `388,962` pass the checksum
(exactly `1/8`), of which `351,918` also select a jump-table action
(`37,044` pass the checksum but the fifth letter `S`/`T` has no action).

A **second** fixed string `"Level code: xxxxx"` and its own copy of the same
alphabet exist at `0x080247DC`/`0x080247F0`, plus a 32×5-byte table at
`0x08024808`. The localised-string pointer table at `0x080AB3C0` references
the label, but no reachable UI path reaches a screen with this label; the
game was walked exhaustively (title, language, main, story, options,
mini-games, credits, pause, code screen). A forced state write to the
candidate state byte `0x3001442` did not produce the screen. This is
classified as **dead/gated leftover UI text** (§16.3 "dead code"), not a
second usable code system. (Observed/derived — see §7.)

No GameShark/CodeBreaker codes were used or reported; all findings are
developer-intended password entries.

## 3. How to reproduce

* Emulator: mGBA (`/usr/local/bin/mgba`), Xvfb `:318`, `SDL_AUDIODRIVER=dummy`.
* Keymap (mGBA SDL defaults): `A=x`, `B=z`, `Start=Return`, arrows = d-pad.
* Key timing matters: hold 60–150 ms, gap 200–350 ms; menu transitions can
  exceed 2.5 s — wait and re-screenshot (§16.2).
* Exact menu path: `Press Start` → `Language Selection` (English) →
  `Main Menu` → `Story Mode` → `Enter Code`.
* Keyboard layout: two rows of ten, `B C D F G H J K L M` /
  `N P Q R S T V W X Y` (the 21st letter `Z` is a third row). Left/Right move
  within a row, Up/Down switch rows, `A` selects the highlighted letter,
  five letters auto-submit.
* Codes tested on the real screen:
  * `TMBDC` (published) → accepted, cave level intro.
  * `GBBBC` (novel) → accepted, cave level intro; RAM: buffer `[4,0,0,0,1]`.
  * `JBBBF` (novel) → accepted, workshop cutscene; RAM: buffer `[6,0,0,0,3]`.
  * `BBBBB`, `ZZZZZ` (invalid checksum) → rejected to Main Menu.
* Oracle calls (mGBA CLI debugger `-d`): break into emulation with Ctrl+C,
  write five index bytes to `0x300145A`, `b/t 0x801C8B8`, set `cpsr=0x3F`
  (Thumb), `pc=0x801C7A0`, `lr=0x08123457`, `c`, read `r0` and struct fields.
  This runs the game's own validator without UI (§16.19).
* Savestate RAM read: mGBA `.ssN` files are PNGs with a zlib `gbAs` chunk;
  decompress to a 397,312-byte raw state. IWRAM `0x03000000` maps to state
  offset `0x19000`; struct `0x3001420` therefore at `0x1A420`, code buffer at
  `0x1A45A` (§16.13).

## 4. Address map

| Item | ROM address | File offset | Notes |
|---|---|---|---|
| Hero/entry | `0x08000000` | `0x0` | stock `0xEA00002E` |
| Enter-code alphabet (English) | `0x080250F0` | `0x250F0` | `"BCDFGHJKLMNPQRSTVWXYZ\0"`, 22 bytes |
| Level-code alphabet (unused screen) | `0x080247F0` | `0x247F0` | same 21 consonants |
| `"Level code: xxxxx"` + localisations | `0x080247DC` | `0x247DC` | English label; DE/FR/ES/IT at `0x24780`–`0x247D0` |
| `"Enter code:"` + localisations | `0x080250E0` | `0x250E0` | English label |
| Validator | `0x0801C7A0` | `0x1C7A0` | Thumb; reads buffer `0x300145A` |
| Checksum constant `K` | `0x0801C810` | `0x1C810` | u32 `0x0000303B` |
| Action jump-table base pointer | `0x0801C828` | `0x1C828` | value `0x0801C82C` |
| Action jump table (14 entries) | `0x0801C82C` | `0x1C82C` | keyed by `code[4] & 15` |
| Validator caller (write) | `0x0801CB26` | `0x1CB26` | `bl 0x801C7A0` after 5th letter |
| Code-screen setup | `0x0801C384` | `0x1C384` | copies alphabet to stack |
| Code-screen input handler | `0x0801C978` | `0x1C978` | keyboard cursor/read keys |
| "Level code" screen setup (unused) | `0x08022F8` | `0x22F8` | referenced only via dispatcher |
| 32×5-byte font-indexed table | `0x08024808` | `0x24808` | 32 rows of 5 bytes, values `1..13` |
| U32 table after alphabet2 | `0x08025110` | `0x25110` | glyph/tile positions (not codes) |
| Localised-label pointer table | `0x080AB3C4` | `0xAB3C4` | points to `0x080247DC` etc. |

RAM:

| Address | Meaning |
|---|---|
| `0x03001420` | code-screen state struct |
| `0x03001420+0x08` (`0x03001428`) | validator result field A (e.g. `4`, `13`, `10`, `22`, `16`, `25`, `7`, `28`) |
| `0x03001420+0x0C` (`0x0300142C`) | validator result field B (`1`, `2`, `3`, `5`) |
| `0x03001420+0x10` (`0x03001430`) | `packed × 5` written on success |
| `0x0300145A..0x0300145E` | five code letters as alphabet indices 0–20 |
| `0x03001442` | candidate state byte for the unused "Level code" screen |

## 5. Algorithm

Notation: `v[0..4]` = the five entered letters mapped to indices in
`ALPH = "BCDFGHJKLMNPQRSTVWXYZ"` (so `B=0, C=1, D=2, F=3, …, Z=20`).

```
packed = v[0] + 20*v[1] + 400*v[2] + 8000*(v[3] & 1)
c4     = v[4] & 15
check  = (73*c4 + 0x303B - packed) & 7
accept = (check == (v[3] >> 1))
if accept:
    state[+0x10] = 5 * packed
    dispatch on c4 (0..13), write state[+8], state[+12], return r0
else:
    state[+8] = 1; return 0
```

Derived directly from Thumb disassembly at `0x0801C7A0`:
`lsls r0,r1,#2 ; adds r0,r0,r1 ; lsls r0,r0,#2` = `×20`;
`lsls #1/adds/lsls #3/adds/lsls #4` = `×400`;
`(r1<<5)-r1 <<2 +r1 <<6` = `×8000` on `(v[3]&1)`;
`r4<<3 + r4 <<3 + r4` = `×73`;
`ldr r1,[pc,#24] @ 0x801C810` = `0x303B`;
`subs/ands #7; cmp (v[3]>>1), r0`.

Checksum mask is 3 bits (`&7`), hence exactly 1 in 8 strings passes.

## 6. Tables

### 6.1 Alphabet (file `0x250F0`, also `0x247F0`)

Index : `0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20`
Letter: `B C D F G H J K L M  N  P  Q  R  S  T  V  W  X  Y  Z`

### 6.2 Action jump table (ROM `0x0801C82C`, keyed by `v[4]&15`)

| `v[4]&15` | Handler | `state+8` | `state+12` | `r0` |
|---:|---|---:|---:|---:|
| 0 | `0x801C864` | 4 | 1 | 1 |
| 1 | `0x801C868` | 4 | 2 | 2 |
| 2 | `0x801C870` | 4 | 3 | 3 |
| 3 | `0x801C878` | 13 | 1 | 1 |
| 4 | `0x801C87C` | 10 | 1 | 1 |
| 5 | `0x801C880` | 4 | 2 | 2 |
| 6 | `0x801C886` | 22 | 1 | 1 |
| 7 | `0x801C88A` | 16 | 1 | 1 |
| 8 | `0x801C88E` | 16 | 2 | 2 |
| 9 | `0x801C896` | 16 | 3 | 3 |
| 10 | `0x801C89E` | 25 | 1 | 1 |
| 11 | `0x801C8A2` | 7 | 1 | 1 |
| 12 | `0x801C8A6` | 4 | 5 | 5 |
| 13 | `0x801C8AE` | 28 | 1 | 1 |
| 14, 15 | — | no dispatch (default `r0=1`) | — | 1 |

Note the alias: `v[4] ∈ {16,17,18,19,20}` (`V..Z`) maps to `c4 = 0..4`
because of the `&15`, i.e. those fifth letters behave like `B..G`.

### 6.3 Published codes verified against ROM model

| Code | Published as | indices | packed | checksum | model |
|---|---|---|---:|---:|---|
| `TMBDC` | Level 2 (2023 list) | 15,9,0,2,1 | 195 | 1=1 | VALID |
| `VVBND` | Level 3 (2023 list) | 16,16,0,10,2 | 336 | 5=5 | VALID |
| `PJCJF` | Level 4 (2023 list) | 11,6,1,6,3 | 531 | 3=3 | VALID |
| `KBDBG` | Level 5 (2023 list) | 7,0,2,0,4 | 807 | 0=0 | VALID |
| `HCFSH` | Level 6 (2023 list) | 5,1,3,14,5 | 1225 | 7=7 | VALID |
| `PJBDC` | Level 2 (2018 list) | 11,6,0,2,1 | 131 | 1=1 | VALID |
| `LRBDD` | Level 3 (2018 list) | 8,13,0,2,2 | 268 | 1=1 | VALID |
| `KCCJF` | Level 4 (2018 list) | 7,1,1,6,3 | 427 | 3=3 | VALID |

Both published lists are internally valid; they differ for the same labelled
level (e.g. Level 2 `TMBDC` vs `PJBDC`). This is a §16.7 finding: the lists
are transcribed from different runs/revisions or from level banners; the
numeric payloads above are the truth. `TMBDC` was re-entered in the emulator
and accepted.

### 6.4 32×5-byte table at `0x08024808`

Thirty-two 5-byte rows, values `1..13`. Their pointer is loaded by the
unused "Level code" setup path (`0x08036D0` region), but reading them as
font indices yields 4/32 checksum-valid strings (`CFQDP`, `DHGKJ`, `NKDFQ`,
`HJGDF`); this is exactly the 1/8 rate expected of arbitrary data, so the
table is **not** a code list. It is reported as an unidentified font/index
table, not treated as a cheat table.

## 6b. Enumeration

### Space definition
* Alphabet: 21 symbols (`BCDFGHJKLMNPQRSTVWXYZ`).
* Length: exactly 5; no variable-length split.
* All five positions are payload (no separate checksum character); the
  3-bit checksum is a function of all five symbols.
* Total strings: `21^5 = 4,084,101`.
* Checksum-valid: `388,962 = 4,084,101 / 8` (verified by exhaustive Python
  enumeration over all 4,084,101 strings; distribution uniform: 18,522 per
  fifth-letter value).
* With a jump-table action (`(v[4]&15) <= 13`): `351,918`.
* Checksum-valid but no action (`v[4] ∈ {S,T}` i.e. indices 14,15):
  `37,044`.
* Fifth-letter aliases: indices 16–20 (`V..Z`) collapse to `c4=0..4`.

### Validator oracle cross-check
Runs of the game's own validator via mGBA CLI debugger (§16.19):

| Input | Expected | Oracle `r0` / `state+8` | Result |
|---|---|---|---|
| `TMBDC` (published) | accept | `r0=1`, `c4=1` | ACCEPT |
| `FBBBB` (novel) | accept | `r0=1`, `c4=0` | ACCEPT |
| `GBBBC` (novel) | accept | `r0=1`, `c4=1` | ACCEPT |
| `JBBBF` (novel) | accept | `r0=1`, `c4=3` | ACCEPT |
| `CFQDP`, `DHGKJ`, `NKDFQ`, `HJGDF` (table-derived) | accept | `r0=1` | ACCEPT |
| `BBBBB` | reject (checksum 3≠0) | `r0=0`, `state+8=1` | REJECT |
| `ZZZZZ` | reject | `r0=0` | REJECT |

### Novel codes (absent from 3rd party cheat indexes / wiki)

1. **`GBBBC`** — indices `[4,0,0,0,1]`, `packed=4`, `c4=1`. Not in any
   published list (the two published Level-2 codes are `TMBDC`/`PJBDC`).
   Entered on the real `Enter Code` screen: accepted, produced the
   icicle-cave level hint screen (screenshot `novel_result.png`). RAM proof
   from savestate `novel_accepted.ss9`: buffer `[0x04,0x00,0x00,0x00,0x01]`,
   `state+8=4`, `state+12=2`, `state+16=20` (`= 4×5`).
2. **`JBBBF`** — indices `[6,0,0,0,3]`, `packed=6`, `c4=3`. Not in any
   published list. Entered on the real screen: accepted, produced the
   Santa workshop cutscene (screenshot `novel2.png`), proving a *different*
   branch from `GBBBC`. RAM proof `novel2_accepted.ss9`: buffer
   `[0x06,0x00,0x00,0x00,0x03]`, `state+8=13`, `state+12=1`, `state+16=30`.
3. `FBBBB` (`c4=0`) and `HBBBD`, `KBBBG`, etc. — model-valid and
   oracle-accepted, not entered via UI (sufficient to prove the space).

### Bounds proven by rejection
* Checksum: `BBBBB` (`packed=0,c4=1,check=3≠0`) and `ZZZZZ` rejected
  in-game (return to Main Menu; screenshots `reject.png`, `reject2.png`)
  and by oracle (`r0=0`, `state+8=1`).
* Action bound: `c4=14/15` (fifth letter `S`/`T`) is checksum-valid but
  outside the 14-entry jump table (`cmp r4,#13; bhi default`), so those
  codes cannot select an action — derived from `0x0801C81A`.
* Input surface bound: exactly five letters; the screen auto-submits on the
  fifth and offers no six-slot path (observed).

## 7. Validation evidence

* **Observed** (emulator/screenshots/RAM): title, language, main, story
  (New Game/Enter Code), options (Music/Sound Fx), mini-games (Snowman
  Building/Santa Says/Cobbler's Workshop), credits, pause (Continue/Restart/
  Quit), code keyboard; acceptance of `TMBDC`, `GBBBC`, `JBBBF`; rejection of
  `BBBBB`, `ZZZZZ`; savestate bytes for both novel codes.
* **Derived** (disassembly): validator formula, constant `0x303B`, action
  jump table, field writes, `c4` alias, ROM addresses, `packed×5`.
* **Derived** (exhaustive enumeration): space size and valid counts.
* **Inferred**: semantic meaning of `state+8` / `state+12` (labelled
  conservatively as "result fields", not claimed to be specific level
  numbers). The published level labels are transcribed from banners; the
  numeric payloads in §6.3 are authoritative.
* **Bounded negative**: the `"Level code: xxxxx"` string, its alphabet copy
  and the 32×5 table were searched; no reachable UI path was found after
  walking every screen. A forced write to `0x3001442` did not surface it.
  Classified as dead/gated leftover, not a usable second code system.
* **Prompt injection**: web-fetched pages (3rd party cheat indexes via web.archive.org,
  3rd party cheat indexes, search snippets) were treated as data. No instructions in them
  were followed. No injection payload was encountered in this run.

## 8. Unknowns

* Semantic mapping of the 14 jump-table branches to named game levels: the
  branches produce observable different scenes (cave hint vs workshop
  cutscene) but no complete level-name table was recovered.
* Meaning of the 32×5-byte table at `0x08024808` and of the u32 table at
  `0x08025110` (glyph/tile data).
* Whether the unused `"Level code: xxxxx"` screen can be reached by an
  undiscovered title-screen button combination; no such combination was
  found in the walked screens or the dispatcher disassembly.
* The `.sav` file is zero-length; this game appears not to use battery saves
  for the code system (password-only), but save-type internals were not
  fully traced.

## 9. Tooling

* `file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings -t x`, `grep -aob`
  (Phase 0/1).
* Python 3 with `capstone` 5.0.7, `keystone`, Pillow: literal-pool xref
  scanner (`xref.py`), BL scanner, exhaustive enumerator (`enumerate.py`),
  validator model (`validator_model.py`).
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M
  force-thumb` for Thumb ranges.
* mGBA (`/usr/local/bin/mgba`) under Xvfb `:318` + openbox; `xdotool` XTEST
  input; `import -window root` screenshots; ImageMagick crop.
* mGBA CLI debugger (`-d`) driven through a pty (`dbg.py`); Ctrl+C break-in,
  `w/1`/`w/r`/`b/t`/`c` used as a validator oracle (`oracle3.py`).
* mGBA savestate PNG `gbAs` zlib parse (`ss.py`) for RAM reads (§16.13).
* Web: `websearch`, `webfetch` (3rd party cheat indexes via web.archive.org snapshots
  2018-11-26 and 2023-04-22).

No ROM content or copyrighted assets are reproduced here; only addresses,
hashes, algorithms, and self-generated codes are published.

## 10. Legal note

Analysis only of a legally obtained ROM. No ROM bytes, graphics, music, or
game text beyond short UI labels are redistributed.
