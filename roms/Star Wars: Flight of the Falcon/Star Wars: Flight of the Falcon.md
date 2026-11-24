# Star Wars: Flight of the Falcon (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Star Wars: Flight of the Falcon.gba` |
| Size | 8,388,608 bytes (0x00800000) |
| Header title | `STARWARSFOTF` |
| Game code / maker | `BSWE` / `78` |
| Version | 0x00 |
| Complement / checksum | 0x0B / 0x0000 |
| Entry word | `0xEA00002E` (stock crt0 — no cracktro/trainer at entry) |
| MD5 | `a6cc5b4377dc7396fa275113e1b958b4` |
| SHA-1 | `4ce7c96146456b10db85d7bf4a6b0f588ea370b9` |
| SHA-256 | `9566b376af6225ab5283f4abe2e0a024020282e644d6ed3eb5811417f78c44a1` |

Developer Pocket Studios / THQ, 2003. `file(1)` identifies it as a clean retail GBA image.

## 2. Executive summary

The game has **two developer-intended cheat surfaces**, both reached through the same
four-character entry buffer at `0x03006BD0`:

1. **A seven-entry hard-coded cheat table** (`SPVD`, `M0NG`, `BL0B`, `FVNK`, `G0G0`,
   `G00N`, `F4C3`) at `0x085C9788`. These are compared literally by `strcmp`-class code
   and are **gated**: bit 15 (`0x8000`) of the global state word at `0x03006DE0` must
   be set. Published sources state this gate is opened by a pause-menu button code
   (hold L+R, then Up, Right, A, Start, A, Down, A, Start, Start). The gate bit itself
   was **derived from the ROM** (the validator tests it before ever reading the cheat
   table); the button sequence is published-only and was not confirmed with key input.
2. **An algorithmic four-symbol chapter-password system** — the real finding. It is
   always active, has a 32-symbol alphabet (21 consonants + `0`–`9` + `?`), a scattered
   checksum, four 32-bit XOR key rows, and packs its decoded payload into three
   small fields at `0x03006DE0`. The whole space was enumerated offline (1,048,576
   inputs → 15,486 accepted → 968 distinct states), and a **novel accepted code
   `QRZZ`** was minted and verified by calling the ROM's own validator with RAM
   read-back (state `(episode=7, field2=10, field3=10)`; accept marker `13` at
   `0x03006ECC`). Rejection bounds were proven with a bad-checksum code and a
   valid-checksum but out-of-range code — both leave the accept marker at zero.

No GameShark/Action Replay/CodeBreaker codes are reproduced here as cheats; the
libretro AR codes found during recon are out of scope.

## 3. How to reproduce

### Emulator and tooling
* mGBA 0.10.5 SDL, `Xvfb :315`, `SDL_AUDIODRIVER=dummy`, 3× scale.
* Host tools: `gdb-multiarch`, `arm-none-eabi-objdump -M force-thumb`, Python 3 +
  Capstone 5.0.7.
* mGBA's `-g` GDB stub was unusable (port 2345 already held by another session), so
  dynamic work used mGBA's `-d` command-line debugger through a PTY bridge
  (`/tmp/falcon/dbg_bridge.py`) and savestate RAM read-back.

### Screen walk (observed)
Legal screen → title (`PRESS START`) → high-score table (`Top 5 Pilots`; `SELECT`
opens `IMPORT / EXPORT / RESET`) → main menu (`NEW GAME / PASSWORD / OPTIONS`;
the main menu is reached with `SELECT` from the high-score table). The menu's L/R
shoulder keys and the high-score submenus were exercised; the `PASSWORD` menu item
is listed in the game's own text bank at `0x08504B18` with the help strings
`Enter Chapter Password` (`0x08504DD4`) and `Unlock previously completed chapters.`
(`0x08504E38`).

**Limitation (stated explicitly):** the on-screen four-symbol keyboard was not
driven to completion, because the menu transition/key-repeat behaviour in headless
SDL made repeatable entry unreliable. Instead, per guide §16.19, the ROM's own
validator was called directly with the candidate code and the resulting RAM state
was read from a savestate. This is a ROM-side validation, not a visual UI capture.

### Reproducing a ROM-side validation
The validator takes no useful arguments: it reads the four input bytes from
`0x03006BD0` and writes results to `0x03006DE0`/`0x03006ECC`. With mGBA `-d`
paused at reset:

```
w/r cpsr 0x3f                 @ ensure Thumb mode
w/4 0x03006BD0 0x5A5A5251     @ e.g. "QRZZ" little-endian
w/r r14 0x08508183            @ lr = Thumb "b ." at file 0x508182
w/r r15 0x08483559            @ pc = validator|1
c
```

Then press `Shift+F2` to dump a savestate and decompress its `gbAs` PNG chunk;
read `0x03006DE0` and `0x03006ECC` at raw-state offsets `0x1FDE0` and `0x1FECC`.
A non-zero value at `0x03006ECC` (7, 10 or 13) is the accept marker.

Observed results (all confirmed on this exact ROM):

| Code | `0x03006DE0` (raw) | `0x03006ECC` | Outcome |
|---|---:|---:|---|
| `TGHK` (known) | `0x080A0000` | `13` | accepted, decoded `(0,10,8)` |
| `QRZZ` (novel) | `0x0A000A07` | `13` | accepted, decoded `(7,10,10)` |
| `TGHJ` (bad checksum) | `0x00000000` | `0` | rejected |
| `BWR8` (checksum ok, field3 out of range) | `0x080D0002` | `0` | rejected |
| `82V2` (published PEZ code) | `0x00000000` | `0` | rejected by this image's validator |
| `CJSG` | `0x00000000` | `13` | accepted, decodes to all-zero state |

Note: `BWR8` still has its flag bytes written — the game writes them *before* the
range check at `0x08483952`; the accept marker is the authoritative accept signal.

## 4. Address map

### File offset ↔ ROM address
`rom_address = 0x08000000 + file_offset`. All ROM addresses below are file
offsets + `0x08000000`.

| Address | Meaning |
|---|---|
| `0x08483558` | Main password/cheat validator (Thumb) |
| `0x08483006` | The single `BL` call site to the validator; result dispatched at `0x0848300A` |
| `0x084833F0`–`0x08483966` | Checksum, XOR decode and flag packing |
| `0x08483952`–`0x08483968` | Range checks: `byte+3<=10`, `byte+2<=10`, `halfword<=7` |
| `0x084838A8` / `0x084838FC` / `0x08483950` | Stores of the three decoded fields |
| `0x084839D2`/`0x084839E0`/`0x084839EC` | Writes `7`/`10`/`13` to `0x03006ECC` (accept marker) |
| `0x085C9254` | XOR key table: 4 rows × 40-byte stride, 4 words used per row |
| `0x085C9770` | Cheat alphabet `BCDFGHJKLMNPQRSTVWXYZ`, NUL-padded, length 21 |
| `0x085C9788` | Seven 8-byte cheat strings (SPVD, M0NG, BL0B, FVNK, G0G0, G00N, F4C3) |
| `0x085C97CC` | Parallel pointer table to those seven strings |
| `0x08504B18`, `0x08504DD4`, `0x08504E38`, `0x08505702`, `0x08505734` | UI text: `Password`, `Enter Chapter Password`, `Unlock previously completed chapters.`, `Password`, `Invalid` |
| `0x085C75FC` | `INVALID CHEAT PICKUP` (unrelated pickup message) |
| `0x0701215`–`0x07029C3` | Font/tile-index text tables (why plain `strings` finds few UI labels) |
| `0x03006BD0` | Four-byte password input buffer (IWRAM) |
| `0x03006DE0` | Global state word: bit 15 = cheat gate; low halfword + bytes 2,3 = decoded password fields |
| `0x03006ECC` | Accept marker / scene: `0` reject, `7`/`10`/`13` on accept |

Savestate translation (mGBA 0.10.5, verified against the `gbAs` chunk): IWRAM base
`0x19000`, so `0x03006BD0 → raw 0x1FBD0`, `0x03006DE0 → raw 0x1FDE0`,
`0x03006ECC → raw 0x1FECC`. CPU GPRs start at raw `0x20` (r7 at `0x3C`, lr at
`0x58`, pc at `0x5C`, CPSR at `0x60`).

## 5. Algorithm

### 5.1 Symbol alphabet (32 symbols, 5 bits each)

| Value | Symbols |
|---|---|
| 0–20 | `B C D F G H J K L M N P Q R S T V W X Y Z` (consonants, from table at `0x085C9770`) |
| 21–30 | `0 1 2 3 4 5 6 7 8 9` (decoded as `ASCII - 27`) |
| 31 | `?` |

Any `A`–`Z` not in the consonant table (i.e. a vowel) fails the symbol lookup;
this is why the published `TSJO` (contains `O`) and `G00N`/`M0NG` etc. are not
chapter passwords. The last five entries are `90`–`9A` = 21..30, i.e. `0`..`9`.

### 5.2 Decoder (precise enough to reimplement)

```
a[0..3] = symbol values of the four input characters

# scattered checksum (C is assembled, S is summed)
S = sum((a[i] & 0x1C) >> 2 for i in 0..3) + (a[0]&1) + (a[2]&1) + (a[3]&1)
C = ((a[0]&2) << 2) | ((a[1]&1) << 4) | ((a[1]&2) << 1) | (a[2]&2) | ((a[3]&2) >> 1)
accept only if C == S and 1 <= C <= 30

# key selector
K = ((a[1] & 0x10) >> 3) | ((a[3] & 0x10) >> 4)        # 0..3

# XOR decode (table at 0x085C9254, row K at +40*K, 4 words)
w[i] = (a[i] ^ KEY[K][i]) & 31

# packed fields
lo = 4*(w[0]&1) + 2*((w[0]&16)>>4) + ((w[2]&16)>>4)      # 0..7
b2 = (w[0]&8) | ((w[1]&8)>>1) | ((w[2]&8)>>2) | ((w[3]&8)>>3)   # 0..15
b3 = ((w[0]&4)<<1) | (w[1]&4) | ((w[2]&4)>>1) | ((w[3]&4)>>2)   # 0..15

accept only if lo <= 7 and b2 <= 10 and b3 <= 10
write lo as 16-bit at 0x03006DE0, b2 as byte at +2, b3 as byte at +3
write accept marker to 0x03006ECC: lo==1→7, lo==2→10, else→13
return 1
```

XOR key rows (ROM order, at `0x085C9254 + 40*K`):

| K | word0 | word1 | word2 | word3 |
|---:|---:|---:|---:|---:|
| 0 | 0x03 | 0x07 | 0x0F | 0x05 |
| 1 | 0x13 | 0x1D | 0x0A | 0x15 |
| 2 | 0x05 | 0x0F | 0x07 | 0x03 |
| 3 | 0x1E | 0x19 | 0x0C | 0x16 |

### 5.3 Cheat-code path

If `bit15` of `0x03006DE0` is set, the validator first copies the 21-character
cheat alphabet into a stack buffer and compares the four input bytes against each
of the seven literal strings. Match returns a one-hot flag:

| Code | Return / flag bit | Published effect |
|---|---:|---|
| `SPVD` | `0x0008` | infinite shield |
| `M0NG` | `0x0010` | infinite continues/lives |
| `BL0B` | `0x0020` | unlimited missiles |
| `FVNK` | `0x0040` | unlock all levels |
| `G0G0` | `0x0080` | rapid fire (hold A) |
| `G00N` | `0x0100` | view credits in options |
| `F4C3` | `0x0200` | developer image gallery |

These are genuine in-game codes (hard-coded in the ROM), not cheat-device codes.
The gate bit was located statically; the published button sequence that sets it
was not reproduced dynamically, so the *activation* of this path is reported as
derived/published, not observed.

## 6. Tables

* Chapter passwords (published, all verified against the model and ROM):

| Code | `(lo,b2,b3)` | Published meaning |
|---|---|---|
| `TGHK` | `(0,10,8)` | Episode IV |
| `8TV2` | `(1,10,8)` | Episode V |
| `TSB2` | `(2,10,8)` | Episode VI |
| `RRV2` | `(3,10,8)` | Bonus level |
| `4?6C` | `(3,10,10)` | Unlock all levels and bonus game |
| `48TF` | `(2,10,8)` | Unlimited abilities on chapter 2 (alias of `TSB2` in this encoding) |
| `82V2` | — | Published "unlimited abilities ch.1"; **fails checksum on this image** (rejected) |
| `TSJO` | — | Contains vowel `O`, not in the 32-symbol alphabet; rejected/absent |

`G00N`, `M0NG`, `SPVD`, `G0G0`, `BL0B`, `FVNK`, `F4C3` are cheat-table entries,
not chapter passwords (they fail the chapter checksum by construction).

## 6b. Enumeration

### Space definition
* Alphabet: 32 symbols, 5 bits each; length exactly 4 → **2²⁰ = 1,048,576**
  representable strings.
* Checksum: scattered 5-bit equality `C == S` with `1 ≤ C ≤ 30`.
* Payload: 20 raw bits → three fields `(lo ≤ 7, b2 ≤ 10, b3 ≤ 10)`.
* Key selector `K` is derived from two bits of the raw input (not secret state).

### Exhaustive counts (run of the decoder over all 1,048,576 inputs)
* Pass checksum: **32,766**
* Fail checksum: 1,015,810
* Checksum-pass but fail range: **17,280**
* Fully accepted: **15,486**
* Distinct decoded states `(lo,b2,b3)`: **968** (all 8 × 11 × 11 = 968 combinations
  are reachable)
* Aliasing: 966 states have exactly **16** spellings each; two states have 15 —
  four payload bits (the unused low bits of the decoded words) are ignored by the
  packing. Published pairs such as `TSB2`/`48TF` are such aliases, not typos.

### Novel code (absent from GameFAQs, Cheat Happens, Wookieepedia, ROMSFUN, IGN)
**`QRZZ`** — decodes to `(lo=7, b2=10, b3=10)`, i.e. the maximum episode field and
maximum values of both secondary fields, a combination no published list covers.

* Offline model: `S=C=16`, `K=1`, `w=[31,16,30,1]`,
  `lo=7, b2=10, b3=10`, expected flags `0x0A000A07`.
* ROM proof: calling the ROM validator with `QRZZ` in `0x03006BD0` wrote
  `0x03006DE0 = 0x0A000A07` and `0x03006ECC = 13` (accept). Exact match.
* Other generated maximals in the same family: `C4VZ`, `B4V0`, etc.; each has
  15 sibling spellings from the unused bits.

### Bounds proven by rejection
* **Bad checksum:** `TGHJ` (one symbol different from `TGHK`) → `S=8, C=9`;
  ROM wrote no flags and left `0x03006ECC = 0` (reject).
* **Valid checksum, out-of-range field:** `BWR8` → `S=C=16`, decodes to
  `b3=13 > 10`; ROM wrote the pre-check flag bytes (`0x080D0002`) but left
  `0x03006ECC = 0` (reject). This isolates the range layer from the checksum layer.
* **Invalid symbol:** `TSJO` contains `O`, which is not in the 21-consonant table
  nor a digit nor `?`; no symbol value exists, so it can never be accepted.
* **Published-code correction:** `82V2` fails the checksum on this ROM revision
  and is rejected — a bounded, recorded negative.

### Button-code enumeration
Published sources agree on one pause-menu sequence: hold L+R and press
Up, Right, A, Start, A, Down, A, Start, Start. A literal byte/u16 search for that
sequence (with and without the held shoulders, active-low and active-high key
masks, 1- and 2-byte per press) found **no** code table in the first 6 MiB of ROM;
the gate was instead located as bit 15 of `0x03006DE0`, read by the validator at
`0x0848356E`–`0x08483584`. Therefore the button sequence is recorded as a
published lead, and the bounded static statement is: *the cheat table is reachable
only when that bit is set; no second cheat table or alternate gate was found*.

## 7. Validation evidence

* **Observed (emulator):** every screen in §3; the seven cheat strings and the
  alphabet in the ROM image; the four-character buffer retaining `TGHK` at boot;
  the accept/reject RAM results in §3 table from direct ROM-validator calls; the
  savestate layout used for RAM reads.
* **Derived (disassembly):** the whole decoder/checksum/field packing (§5),
  the XOR tables, the gate bit, the exact space and rejection counts (§6b), the
  one-hot cheat flag values, and the single `BL` call site.
* **Inferred / lower confidence:** field *meanings*. `lo` correlates exactly with
  the published episode labels (0=IV, 1=V, 2=VI, 3=bonus), so "episode" is well
  supported; `b2`/`b3` appear to be score/lives/shield-style options, but no
  published code varies them independently, so their semantics are **not proven**.
  The button sequence's authorship is published-only (not re-entered in-game).
* **Not claimed:** no visual screenshot of a novel code being typed on the
  on-screen keyboard was obtained; see the limitation in §3.

### Note on prompt-injection / untrusted data
All fetched web pages and ROM strings were treated as data. No instructions found
in those sources were executed. No suspicious payload was encountered in this run.

## 8. Unknowns

1. Exact semantic labels of decoded fields `b2` and `b3` (0–10 each).
2. The identity of the routine that sets gate bit 15 of `0x03006DE0`; the
   published button sequence was not confirmed dynamically.
3. Whether `0x03006ECC` values 7/10/13 map to different scenes beyond the observed
   accept marker.
4. Why the published `82V2` is invalid on this (BSWE, Rev.00) image — likely a
   different regional revision or a transcription error in the list.
5. The high-score import/export password format (a separate 4-symbol UI exists;
   not reversed here because it is a high-score transfer, not a gameplay cheat).

## 9. Tooling

Scripts written under `/tmp/falcon/`:

| File | Purpose |
|---|---|
| `password_model.py` | Offline decoder/encoder and published-code checks |
| `runval.py` | Restart `-d` debugger, call the ROM validator with a code, read RAM from a savestate |
| `runcaller.py` | Call through the validator's real caller (used for triage) |
| `dbg_bridge.py` | Persistent PTY bridge to mGBA's command-line debugger |
| `patchstate.py`, `patchcaller.py` | Savestate `gbAs` patch/read helpers |
| `k.py` | xdotool key/screenshot helper |

Rebuild environment: `mgba` 0.10.5 (custom build at `/usr/local/bin/mgba`),
`gdb-multiarch`, `arm-none-eabi-objdump`, `xdotool`, `scrot`, Python 3 with
`capstone==5.0.7`. No ROM or copyrighted assets are redistributed; only
addresses, hashes, algorithms and the authors' own scripts are published.

## 10. Legal note

No ROM image, extracted graphics, music, or verbatim game text beyond short UI
labels needed for identification is included in this report.
