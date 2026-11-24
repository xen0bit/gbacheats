# Drome Racers (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Drome Racers/Drome Racers.gba` |
| Size | 8,388,608 bytes (0x800000, 8 MiB) |
| Header title | `LEGO DROME R` |
| Game code | `AOEE` (region: USA/Europe combined) |
| Maker | `78` (ASCII in header; publisher Atari per box art) |
| Version | 0x00 (Rev.00) |
| Entry word | `0xEA00002E` — stock GBA `b 0x080000C0` |
| Header checksum | `0x0000`; complement byte `0x98` |
| MD5 | `9f39a0635363f9e534a4b48c64d52322` |
| SHA-1 | `bf810c4a61b03d3d76063633695e45fdd9f789f7` |
| SHA-256 | `0cb044d28fce4f56ae808284b6e37423d55735e3551ef0470efa4867920c9202` |

**Phase 0 result (Observed):** single retail image. A full-file scan for the 156-byte
Nintendo logo found exactly one GBA header (file offset `0x4`, header base `0x0`).
No second/sub-image header, no appended trainer, no cracktro strings
(`gameshark`/`crc bandit`/`trainer`/`sunhors` absent), stock entry branch, tail is
zero-filled. Nothing to restore on a copy.

## 2. Executive summary

The game has a **developer-intended "Enter Code" screen** reached by pressing
**Select at the main menu**. It is a flat lookup, not a checksum algorithm:

* The screen offers **6 slots** and a **38-symbol keyboard** (A–Z, 0–9, `!`, `"`).
* The validator at **`0x080958f8`** is an exact 6-byte compare of the input buffer
  against a hardcoded 6-byte string; there is no checksum, bit-packing, PRNG, or
  generator.
* The dispatcher at **`0x08095918`** calls that validator **8 times**, referencing
  exactly **6 strings** in a record table at **`0x080e4fa0`**.
* The accepted set is therefore **exactly 6 codes**, all of which are already in
  every published GBA list: `CUPIUP`, `ALL4ME`, `BIFFIN`, `BIGUNS`, `LOGRAV`,
  `IAMCAR`.
* **No novel/unpublished code can exist.** This is a mathematically closed set,
  proven two ways (static call-site enumeration + exhaustive execution of the
  validator over all 38⁶ = 3,010,936,384 inputs). §6b documents this negative
  result instead of fabricating a seventh code.
* All six codes were entered on the real screen in mGBA and each produced a
  distinct, RAM-verified state change. A near-miss (`ALL4MF`) was rejected with
  zero effect, proving the bounds.
* Console-version button codes (PC/PS2/GameCube sequences ending in F6/F9/
  Enter/Circle/Square/X) are **not** in this GBA image. No key-mask table and no
  hidden debug menu were found.

## 3. How to reproduce

Emulator: `mgba -3` (SDL build), `DISPLAY=:318`, `SDL_AUDIODRIVER=dummy`.
Keymap (mGBA SDL defaults): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
Select=`BackSpace`, D-pad=arrow keys. Hold keys ~70 ms.

1. Boot. `PRESS START` title → Press Start → (if prompted) enter any 3-character
   name on the `ENTER NAME` screen (this is a *name* field, not a code field) →
   main menu.
2. At the **main menu press Select** → `ENTER CODE: ______` screen.
3. Navigate the on-screen keyboard with the D-pad (cursor starts on `A`); press A
   to insert the highlighted character. Insert all 6 characters, then the focus
   jumps to `OK`; press A to submit. Acceptance closes the screen and returns to
   the main menu. Rejection also closes the screen but changes no flag.
4. Codes tested (all accepted):

   | Code | Published effect |
   |---|---|
   | `ALL4ME` | Unlock all teams |
   | `CUPIUP` | Unlock all tracks and cups |
   | `BIFFIN` | Maximum upgrades for all cars |
   | `LOGRAV` | Low gravity |
   | `IAMCAR` | Weird/alternate sound effects |
   | `BIGUNS` | "Combines all of the above" (see §6 for the precise scope) |

5. Negative tests: `AAAAAA`, `ALL4MF` (one character off a valid code) — both
   returned to the main menu with all effect RAM unchanged from baseline.
6. Savestate workflow: save an empty-code-screen state (slot 1), reload it before
   every trial, then diff decompressed `.ssN` `gbAs` chunks (§16.13) against a
   clean baseline produced by submitting an invalid code.

## 4. Address map

All addresses are GBA bus addresses; file offset = address − `0x08000000` for ROM.

| Address | File offset | Meaning |
|---|---|---|
| `0x080e4fa0` | `0xe4fa0` | Code record table: six 8-byte NUL-padded strings, in order `CUPIUP`, `ALL4ME`, `BIFFIN`, `BIGUNS`, `LOGRAV`, `IAMCAR` |
| `0x080e4f9c` | `0xe4f9c` | Thumb pointer `0x08095919` (dispatcher \| 1), immediately before the strings |
| `0x080e4858` | `0xe4858` | `AZ09 /;@[_` — character-class range table (`A-Z`,`0-9`,` -/`,`; -@`,`[-_`) used by a shared text-input helper, **not** part of code validation |
| `0x080958f8` | `0x958f8` | **Validator**: exact 6-byte compare (`r0` = screen struct, reads `[r0+0x48]`; `r1` = table string ptr; returns 1/0) |
| `0x08095918` | `0x95918` | **Dispatcher**: 8 validator calls + effect handlers |
| `0x08095974` | `0x95974` | CUPIUP effect loop (6 records, stride 17, writes `0xFF`) |
| `0x08095aa2` | `0x95aa2` | LOGRAV effect: writes `0x1000` to `0x03000e0c` |
| `0x08095ac4`–`0x08095ae8` | `0x95ac4`– | Literal pool holding pointers to the six code strings |
| `0x03004600` | — | Screen struct base; input buffer at `+0x48` = **`0x03004648`** (Observed: held `41 2d 2d 2d 2d 2d 00` = `A-----` after one keypress) |
| `0x030022ae` | — | IAMCAR sound toggle byte (Observed `0x00 → 0x01`) |
| `0x03000e0c` | — | LOGRAV gravity word (Observed `0x2000 → 0x1000`) |
| `0x0200000c + 17*k` | — | Save-data car/team records; BIFFIN writes upgrade values here; CUPIUP writes `0xFF` at offset `+0x10` for k=0..5 |
| `0x0200007b`, `0x0200007c` | — | ALL4ME team-unlock flags (Observed `0x00 → 0x01`) |

## 5. Algorithm

Validator (`0x080958f8`), faithful C pseudocode:

```c
bool validate(struct Screen *s, const char *code) {
    const unsigned char *in = (const unsigned char *)(s->field_48); // 0x03004648
    for (int i = 0; i <= 5; i++)          // cmp r1,#5 ; ble  -> indices 0..5
        if (in[i] != (unsigned char)code[i]) return false;
    return true;
}
```

Dispatcher (`0x08095918`), faithful pseudocode:

```c
if (validate(s, IAMCAR)) toggle_byte(0x030022ae);       // XOR 1
if (validate(s, LOGRAV)) *(u32*)0x03000e0c = 0x1000;
if (validate(s, CUPIUP)) for (k=0..5) record[0x0200000c+17*k].unlock = 0xFF;
if (validate(s, ALL4ME) || validate(s, BIGUNS)) unlock_all_teams(); // 0x0200007b/7c=1
if (validate(s, BIFFIN) || validate(s, BIGUNS)) set_max_upgrades();
if (validate(s, BIGUNS)) for (k=0..5) record[0x0200000c+17*k].unlock = 0xFF;
```

Key point: there is **no encoding**. The accepted strings are compared byte for
byte with the on-screen input. A `validate()` call is therefore a perfect oracle;
the exhaustive check in §6b used a line-for-line reimplementation of the six-byte
compare.

## 6. Tables

**Accepted codes (complete table at `0x080e4fa0`):**

| ROM address | Bytes | Code | Dispatcher path | Observed RAM effect |
|---|---|---|---|---|
| `0x080e4fa0` | `43 55 50 49 55 50 00 00` | `CUPIUP` | `0x8095968 → 0x8095974` | EWRAM `0x0200001c + 17k` = `0xFF` (k=0..5) |
| `0x080e4fa8` | `41 4c 4c 34 4d 45 00 00` | `ALL4ME` | `0x80959c2 → 0x80959da` | EWRAM `0x0200007b/7c` = `0x01` |
| `0x080e4fb0` | `42 49 46 46 49 4e 00 00` | `BIFFIN` | `0x8095a04 → 0x8095a0e` | EWRAM `0x0200000c + 17k + 1..6` = upgrade values (`45 55 56 54 57 54` for k=0, …) |
| `0x080e4fb8` | `42 49 47 55 4e 53 00 00` | `BIGUNS` | `0x80959d0`, `0x8095a84`, `0x8095a94` | CUPIUP flags + ALL4ME flags + BIFFIN upgrades (see nuance below) |
| `0x080e4fc0` | `4c 4f 47 52 41 56 00 00` | `LOGRAV` | `0x8095958 → 0x8095aa2` | IWRAM `0x03000e0c`: `0x2000 → 0x1000` |
| `0x080e4fc8` | `49 41 4d 43 41 52 00 00` | `IAMCAR` | `0x8095926` | IWRAM `0x030022ae`: `0x00 → 0x01` |

**Alphabet:** 38 symbols — `A B C … Z 0 1 … 9 ! "` — shown on the code-entry
keyboard. Field length: exactly 6 slots.

**Flag values (clean baseline → after code):**

| Address | Width | Clean | Code | After |
|---|---|---|---|---|
| `0x0200001c` (+17k, k=0..5) | 1 byte each | `00` | CUPIUP, BIGUNS | `ff` |
| `0x0200007b`, `0x0200007c` | 1 byte each | `00` | ALL4ME, BIGUNS | `01` |
| `0x0200000c + 17k + 1..6` | 6 bytes | `00` | BIFFIN, BIGUNS | e.g. `45 55 56 54 57 54` |
| `0x03000e0c` | 2 bytes (LE) | `00 20` (=0x2000) | LOGRAV | `00 10` (=0x1000) |
| `0x030022ae` | 1 byte | `00` | IAMCAR | `01` |

**BIGUNS nuance (Derived from the 8 call sites, confirmed in RAM):** BIGUNS is
compared three times and drives the ALL4ME, BIFFIN and CUPIUP paths only. The
IAMCAR and LOGRAV handlers are reached *only* from their own string comparisons.
In the observed post-entry state BIGUNS left `0x030022ae` at `00` and
`0x03000e0c` at `0x2000`. The published "combines all of the above" is therefore
accurate for the three *unlock/upgrade* codes but not for the two physics/sound
toggles. This is a bounded observation (flags read ~1 s after entry at the main
menu), not a claim that the toggles are never touched transiently.

## 6b. Enumeration

**Space definition.** Alphabet = 38 symbols (`A`–`Z`, `0`–`9`, `!`, `"`); length =
6 (the screen draws exactly six slots and the validator's loop bound is `i <= 5`).
No checksum, no reserved bits, no field substructure. Representable inputs:
**38⁶ = 3,010,936,384**.

**Closed-set proof — static.** The validator has exactly **8** BL call sites
(scan of every Thumb BL in the 8 MiB image): `0x8095926`, `0x8095958`,
`0x8095968`, `0x80959c2`, `0x80959d0`, `0x8095a04`, `0x8095a84`, `0x8095a94`.
Their `r1` literal pointers resolve exclusively to the six strings at
`0x080e4fa0 … 0x080e4fc8`. There is no algorithmic generator, no second table,
and no other code-entry surface ("Enter Name" is a 3-character player-name field
whose buffer is `0x02000004`; no validator reads it).

**Closed-set proof — exhaustive (§16.9).** I compiled a faithful reimplementation
of the ROM's six-byte compare (`tools/enumerate.c`) and ran it over all 38⁶ input
strings (12 s wall-clock with `-O3`):

```
ACCEPT ALL4ME (table index 1)
ACCEPT BIFFIN (table index 2)
ACCEPT BIGUNS (table index 3)
ACCEPT CUPIUP (table index 0)
ACCEPT IAMCAR (table index 5)
ACCEPT LOGRAV (table index 4)
total inputs tested = 3010936384
accepted = 6
```

**Novel code: none exists.** Because the accepted set is exactly six published
strings, the §0.2 "generate a code absent from every published list" deliverable
is unattainable for this image. I report that as a proven negative rather than a
partial result. Every one of the six reachable values is already documented by
GameFAQs, SuperCheats, VictoryCheats and EliteGuias; TCRF's Hot Wheels: Stunt
Track Challenge page independently lists the same six strings as Drome Racers
leftovers. There is no unadvertised difficulty, level, team or flag that a code
can select.

**Bounds proven by rejection (in-game).** `AAAAAA` (all-in-alphabet but not in
the table) and `ALL4MF` (one character off `ALL4ME`) were both submitted on the
real screen. Both closed the code screen and left every effect address at its
clean value (`0x0200007b/7c = 00`, `0x0200001c = 00`, `0x0200000c = 00`,
`0x030022ae = 00`). A valid-checksum/out-of-range style test is not applicable:
this system has no checksum layer and the UI caps input at exactly 6 slots, so a
7-character alias or a reserved-bit payload cannot be expressed.

## 7. Validation evidence

* **Observed** — emulator screenshots (kept on disk): title `PRESS START`;
  `ENTER NAME` (3-char keyboard); main menu (5 icons); `ENTER CODE` (6 slots,
  38-key keyboard); Options (4 icons); Quick Race track select (`Pulse Concept`,
  `Urban Raceway`); in-race `PAUSED` menu (RESUME/SFX/MUSIC/BRIGHTNESS/RETRY
  RACE/QUIT, plus a YES/NO "end your current game" confirmation); all six codes
  accepted; two near-misses rejected.
* **Observed** — RAM reads (decompressed mGBA `.ssN` `gbAs` chunks): input buffer
  at `0x03004648`; the effect table in §6. Each code was tested from the same
  savestate baseline (`ss1` empty code screen) and compared to a clean baseline
  (`ss6` = invalid-code submission).
* **Derived** — validator and dispatcher disassembly at `0x080958f8` /
  `0x08095918`; 8 BL call sites; literal pointers at `0x08095ac4…0x08095ae8`;
  exhaustive enumeration of the 38⁶ space.
* **Inferred** — the semantic labels "low gravity", "weird sound effects", etc.
  come from the published descriptions and ROM UI strings, not from playing a
  full race under each effect. The RAM writes themselves are observed. BIGUNS's
  published "all codes" label is reported as only partly accurate (§6).

## 8. Unknowns

* The exact in-race visual/audio manifestation of LOGRAV and IAMCAR was not
  played through (their flag writes were observed; the physics/sound result is
  inferred from names and published descriptions).
* Whether BIGUNS's LOGRAV/IAMCAR effects, if any, are transient (cleared before
  the main-menu savestate was taken) was not isolated.
* No hidden debug screen or button-code path was found, but an exhaustive
  button-combination search was not performed; the negative rests on (a) zero
  hits for the console sequences `L,R,L,R,U,D,U,D,…` encoded as u16/u8 key masks
  in either polarity or reversed order, (b) no `debug`/`secret`/`cheat menu`
  strings, and (c) walking every menu listed in §7.

## 9. Tooling

* `arm-none-eabi-objdump -M force-thumb --adjust-vma=0x08000000` for validator
  disassembly; a Python Thumb-BL scanner for call-site enumeration; Python
  `struct.find` for literal-pointer scans.
* Python savestate decoder: PNG `gbAs` chunk → `zlib.decompress` → 397,312-byte
  state; EWRAM at state `0x21000`, IWRAM at state `0x19000` (§16.13). This was
  necessary because another session held the default GDB stub port and the `.sav`
  file is not flushed on each code entry.
* `tools/type_code.py` — D-pad navigation driver for the on-screen keyboard
  (grid rows `ABCDEFGHIJKLM` / `NOPQRSTUVWXYZ` / `0123456789!"`); cursor stays on
  the selected key after insertion, so each character is reached by Up/Down then
  Left/Right, then A.
* `tools/enumerate.c` — exhaustive 38⁶ validator oracle (`gcc -O3`).
* `md5sum`, `sha1sum`, `sha256sum`, `strings -t x`, `xxd`, `grep -abo`.

No ROM or copyrighted assets are reproduced in this report; only addresses,
hashes, byte literals for the six short code strings, and my own tooling are
published.
