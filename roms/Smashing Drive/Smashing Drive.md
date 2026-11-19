# Smashing Drive (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Smashing Drive/Smashing Drive.gba` |
| Size | 8,388,608 bytes (0x00800000) |
| Header title | `SMASHDRIVE` |
| Game code / maker | `BSVE` / `AF` |
| Version / complement / checksum | 0 / 0xA4 / 0x0000 |
| Entry word | 0xEA00002E (stock ARM branch to 0x080000C0) |
| Embedded GBA headers | exactly one (Nintendo logo at file 0x4); **no** multiboot image, scene cracktro or appended trainer |
| MD5 | `5e2e52c6bc979aa50efb59d9386faf08` |
| SHA-1 | `bb47246dc6882037daa778fcdfdaf34e8715e7fb` |
| SHA-256 | `74704e6b13200d855d347102c0b5b684a3210d4fa58c9e6ab2f7815317af145d` |

Header hygiene: complement check fails (computed 0xBC vs stored 0xA4) and header checksum is
0x0000 — normal for a rebuilt/retailed header (guide §16.1). The entry branch and single logo
show the game code itself is unpatched. Developer strings name Raylight Studios / DSI Games.

## 2. Executive summary

The game has a genuine, developer-intended **4-character level-unlock password system**, reached
from **Options → Password**. It is algorithmic, not a lookup table, and is fully reversed here:

* Alphabet: `BCDFGHJKLMNPQRSTVWXYZ0123456789?` (32 symbols, values 0–31).
* A code is three data characters followed by one checksum character; the checksum is the sum of
  the three 5-bit data values modulo 32.
* The first three characters pack into a 15-bit word (5 bits each). Four bit fields are extracted
  from it. The code is accepted only when the checksum matches **and** field 1 equals field 3.
* The accepted code writes `min(field1+1, 4)` to EWRAM `0x020007F5`, which unlocks the arcade
  shift (2 = Rush Hour, 3 = Night Owl, 4 = Dusk & Wired / "All Tracks"). There is no code for
  level 1 (Early Bird), which is the default.

The public GameFAQs list (`1DC4`, `M2CC`, `PXB&`) was verified against the ROM and in the
emulator. **`PXB&` is a transcription error: the game rejects it; `PXB8` is the correct code.**
There is an in-game *generator* (0x080053BC) that mints a fresh valid password whenever the game
offers "To unlock level … use this password:"; it randomises the two non-semantic fields, which is
why 2,048 distinct spellings exist for only three outcomes.

Two novel, never-published codes were minted, typed on the real screen and RAM-verified:
**`BVBV`** (Rush Hour, byte = 0x02) and **`BWCX`** (All Tracks, byte = 0x04). Bounds were proven
by four in-game rejections (bad checksum, field mismatch, invalid character).

No button-code system, hidden controller sequence, or reachable debug menu exists. `MPDebugProcess`
is registered but its three functions are all `bx lr` stubs; "Stereo" and "Music test" are orphan
strings in the text bank with no reachable menu entry (the Options dispatch has exactly five
slots).

## 3. How to reproduce

**Emulator**: mGBA 0.10.5 under Xvfb `:315`, 3× scale, `SDL_AUDIODRIVER=dummy`.
Window geometry: client area at screen `(154,184)` size `720×480`; screenshots cropped with
`convert -crop 720x480+154+184`.

**Keymap (verified)**: A = `x`, B = `z`, Start = `Return`, d-pad = arrow keys.
`Shift+F7` saves / `F7` loads a state; savestates land in the ROM folder as `Smashing Drive.ss7`.

**Menu path** (timing matters — allow ~1 s per transition; single 40–60 ms taps, not long holds):

1. Boot; `Return` skips the intro and again at the "Press Start" title.
2. Main menu: press `Right` once, then `x` → **OPTIONS** (menu: Music, Sound FX, Rankings,
   Password, Credits).
3. From the F6 options state, press `Down` three times (one item per press, verified by image
   diff) to highlight **Password**, then `x` → "Enter Password" screen.
4. Password entry: `Up`/`Down` cycles the character in the current slot (`Up` from blank steps
   B, C, D, …), `Left`/`Right` moves between the four slots, `x` submits, `z` backs out.
5. Result: green "Password Allowed!" or red "Wrong Password".

**Codes tested in-game** (all entered on the real screen):

| Code | Result | Unlock byte after entry |
|---|---|---|
| `M2CC` (published) | Password Allowed! | 0x04 |
| `1DC4` (published) | Password Allowed! | 0x03 |
| `PXB8` (correction of published `PXB&`) | Password Allowed! | 0x02 |
| `PXB&` (as published) | Wrong Password (renders as `PXB?`) | unchanged 0x01 |
| `BVBV` (novel) | Password Allowed! | 0x02 |
| `BWCX` (novel) | Password Allowed! | 0x04 |
| `BVBC` (bad checksum) | Wrong Password | unchanged |
| `BVBW` (valid checksum, field mismatch) | Wrong Password | unchanged |
| `M2C?` (bad checksum) | Wrong Password | unchanged |

**RAM proof**: savestates were saved immediately after each result, the PNG's `gbAs` chunk
zlib-decompressed to a 397,312-byte state, and byte `0x21000 + 0x7F5` (EWRAM `0x020007F5`) read.

## 4. Address map

| Address | Type | Meaning |
|---|---|---|
| `0x08000000` | ROM | Image base; entry branch `0xEA00002E` |
| `0x080324BC`–`0x0803276C` | ROM | UI strings; text-bank pointer table starts `0x086A924C` (ID 0 = "Press Start") |
| `0x0803226C` | ROM | Process name "PasswordProcess"; struct at `0x0803227C` (init 0x08005504, main 0x0800575C) |
| `0x080321E8` | ROM | "OptionsProcess" (init 0x080044E8, main 0x08004194) |
| `0x08032400` | ROM | "MPDebugProcess" — all three handlers `0x08019FC4/0x08019FC8/0x08019FCC` are `bx lr` |
| `0x0803E6B0` | ROM | Password alphabet string (32 symbols + NUL) |
| `0x086AA848` | ROM | Word containing pointer `0x0803E6B0` (alphabet indirection) |
| `0x086A920C` | ROM | Field-descriptor template: 4 × `{u32 id, u32 min, u32 max}` |
| `0x080206D4` | ROM | Codec constructor `(struct*, field_table*, nfields=4, max=4)` |
| `0x08020878` | ROM | Checksum validator + 5-bit packer |
| `0x0801AE94` | ROM | `index_of(char, alphabet)`; returns >31 for a character not in the alphabet |
| `0x080207B8` | ROM | Field getter `(codec*, field_id)` |
| `0x08020734` | ROM | Field setter `(codec*, field_id, value)` |
| `0x0802081C` | ROM | Encoder `(codec*)` → writes NUL-terminated password string |
| `0x08005484` | ROM | Password acceptance: checksum + `field1 == field3` → write unlock byte |
| `0x080053BC` | ROM | Password **generator** (random fields 0/2; level in fields 1/3); called from `0x08017D44` |
| `0x0800575C` / `0x08005504` | ROM | Password screen main / init; input widget `0x08021028` |
| `0x080044E8` | ROM | Options main; 5-entry jump table at `0x0803247C` |
| `0x03006A24` | IWRAM | Live codec struct (pointer to fields, derived widths, count, packed word, N, string buffer) |
| `0x020007F5` | EWRAM | **Unlock/shift byte** (1 = Early Bird, 2 = Rush Hour, 3 = Night Owl, 4 = All Tracks) |
| `0x02000054` | EWRAM | Main-menu selection index (0–3) |

## 5. Algorithm

Precise enough to reimplement (verified against every code tested):

```
ALPHA = "BCDFGHJKLMNPQRSTVWXYZ0123456789?"    # 32 symbols, index = value
val(c) = index of c in ALPHA, or >=32 if absent

checksum_ok(code):
    v = [val(code[0]), val(code[1]), val(code[2])]
    if any(v[i] > 31): return False
    return ((v[0]+v[1]+v[2]) & 31) == val(code[3])

word = v[0] | (v[1]<<5) | (v[2]<<10)          # 15 bits; bits 13-14 unused

# field table at ROM 0x086A920C: (id,min,max) = (0,47,62),(1,1,4),(2,91,98),(3,0,15)
# widths are ceil(log2(max-min+1)) = 4,2,3,4; shifts = 0,4,6,9
f0 = ((word >> 0) & 0xF) + 47
f1 = ((word >> 4) & 0x3) + 1
f2 = ((word >> 6) & 0x7) + 91
f3 = ((word >> 9) & 0xF) + 0

accept(code) = checksum_ok(code) and (f1 == f3)
if accept: unlock_byte = min(f1 + 1, 4)       # stored at 0x020007F5
```

The encoder is the exact inverse: for each of the N=3 data slots take `(word >> 5i) & 31`,
append `ALPHA[...]`, then append `ALPHA[(sum of the 3 values) & 31]` and a NUL. The generator
(0x080053BC) calls field setters with random in-range values for fields 0 and 2 and the current
unlock byte for fields 1 and 3, then the encoder.

Decoded published/novel codes:

| Code | v0,v1,v2,chk | word | f0,f1,f2,f3 | unlock |
|---|---|---|---|---|
| `1DC4` | 22,2,1,25 | 0x456 | 53,2,92,2 | 3 (Night Owl) |
| `M2CC` | 9,23,1,1 | 0x6E9 | 56,3,94,3 | 4 (All Tracks) |
| `PXB8` | 11,18,0,29 | 0x24B | 58,1,92,1 | 2 (Rush Hour) |
| `BVBV` | 0,16,0,16 | 0x200 | 47,1,91,1 | 2 (novel) |
| `BWCX` | 0,17,1,18 | 0x620 | 47,3,91,3 | 4 (novel) |

## 6. Tables

**Password alphabet (ROM 0x0803E6B0):**
`B C D F G H J K L M N P Q R S T V W X Y Z 0 1 2 3 4 5 6 7 8 9 ?` → indices 0…31.

**Field table (ROM 0x086A920C):**

| id | width | bit shift | min | max |
|---:|---:|---:|---:|---:|
| 0 | 4 | 0 | 47 | 62 |
| 1 | 2 | 4 | 1 | 4 |
| 2 | 3 | 6 | 91 | 98 |
| 3 | 4 | 9 | 0 | 15 |

Bits 13–14 of the 15-bit word are unused (alias space).

**Published codes (GameFAQs, archived 2018 snapshot of
`gamefaqs.gamespot.com/gba/922021-smashing-drive/cheats`):** `1DC4`=Night Owl, `M2CC`=All Tracks,
`PXB&`=Rush Hour. All three literals are absent from the ROM as ASCII — they are algorithmic, as
proved by the validator above. `PXB&` contains a character outside the alphabet and is rejected;
`PXB8` is the real code. No other published code list (TCRF/VGChartz) yielded GBA-specific codes;
the widely copied "Extra Money: Y,B,Y,B,X,A,X,A,Down,Up" is a GameCube/Xbox map-screen code and
does not apply to this SKU (the GBA game has no map screen).

## 6b. Enumeration

**Space definition.** 4 characters over a 32-symbol alphabet ⇒ **1,048,576** possible strings.
The checksum reduces this to 32³ = **32,768** checksum-valid strings (each 3-character prefix has
exactly one valid check character). The `field1 == field3` constraint cuts this by a factor of 16
(field 1 has 4 values; field 3 has 16, of which only the 4 equal to field 1 pass), leaving
**exactly 2,048 accepted codes**. This was enumerated exhaustively offline with a reimplementation
of the ROM validator (script `enumerate.py`); field widths/shifts/minima were read from the ROM
table, so the count is derived from the shipped artifact, not guessed.

**Outcome distribution** (2,048 total):

| Unlock byte | Effect | Codes |
|---:|---|---:|
| 2 | Rush Hour | 512 |
| 3 | Night Owl | 512 |
| 4 | Dusk & Wired / All Tracks | 1024 |
| 1 | Early Bird (default) | **0** — no password exists; field 1 has min 1 and the result is `f1+1` |

**Novel codes (absent from every published list).** Both were generated from the decoder, typed
on the real Options→Password screen, and confirmed by screenshot *and* RAM:

* `BVBV` → "Password Allowed!", EWRAM `0x020007F5` = **0x02** (Rush Hour).
* `BWCX` → "Password Allowed!", EWRAM `0x020007F5` = **0x04** (All Tracks).

These exercise the unadvertised alias fields: `BVBV` uses the minimum field 0 (47) and field 2
(91), values the published codes never use.

**Bounds proven by in-game rejection:**

| Test input | Rule violated | Observed |
|---|---|---|
| `BVBC` | checksum: 0+16+0 = 16 → `V`, not `C` | Wrong Password |
| `M2C?` | checksum: 9+23+1 = 33 mod 32 = 1 → `C`, not `?` | Wrong Password |
| `BVBW` | checksum valid (0+16+1=17=`W`) but field 1 = 1, field 3 = 3 | Wrong Password |
| `PXB&` | `&` is not in the 32-symbol alphabet (renders as `?`) | Wrong Password |

So both layers — the checksum and the semantic field equality — are independently bounded, and
the alphabet boundary is demonstrated too.

**Button-code / hidden-menu enumeration.** No key-mask sequence table exists for the GBA SKU
(no button-code strings; the GameCube fan page's sequences are for a different platform). The
Options screen has exactly five dispatch slots (`0x0803247C`, handlers `0x08004788`, `...47D8`,
`...47F8`, `...482C`, `...4868`) matching the five visible entries. `MPDebugProcess` is a
registered process whose three handlers at `0x08019FC4`, `0x08019FC8`, `0x08019FCC` are all
`bx lr` — a live stub with no content. "Stereo" (text ID 21) and "Music test" (text ID 24) survive
in the text bank but no reachable menu draws them; with a five-slot dispatch and all five slots
walked, that is a bounded "cut string" negative.

## 7. Validation evidence

**Observed (emulator / savestate RAM):**
* All screens walked: Raylight/BlueRoses splashes, "Press Start" title, main menu (Arcade /
  Survival / Head to Head / Options), Working Shift select (Rush Hour/Night Owl/Dusk & Wired
  initially crossed out), Options (Music OFF / Sound FX ON / Rankings / Password / Credits),
  Rankings (best-times and points tables per shift), scrolling Credits, gameplay HUD
  (BEST RIDE / RIDE TIME / MAX SPEED / DAMAGE), pause ("Game Paused", Continue Game, Exit Game),
  the Enter Password screen, and both result messages.
* Password entry mechanics: `Up` from blank walks B, C, …; `Right` advances the slot; `x`
  submits; `z` backs out — verified frame by frame.
* All 9 code tests in §3; unlock byte read from decompressed savestates after `M2CC` (0x04),
  `1DC4` (0x03), `PXB8` (0x02), `BVBV` (0x02), `BWCX` (0x04).

**Derived (static, Ghidra decompilation + objdump):**
* Every address in §4; the alphabet string and its pointer; the four-field table; checksum and
  field-equality logic; the generator's use of random field 0/2; the five-entry Options dispatch;
  the empty MPDebug handlers.
* Published literals absent from ROM as ASCII, proving an algorithmic rather than table system.

**Inferred (lower confidence):**
* Field 0 (47–62) and field 2 (91–98) are probably score/statistics-related payload fields. The
  generator randomises them, so they do not affect the unlock; their exact in-game meaning was
  not exercised.
* The exact trigger condition for the "To unlock level … use this password:" dialog
  (`FUN_0801832C` at 0x08017D2E) was not reached in play; the generator call and the dialog's
  text IDs (9/10) are proved statically.

## 8. Unknowns

* Exact semantic meaning of fields 0 and 2 (they are randomised by the generator and ignored by
  the unlock logic).
* The precise gameplay event that opens the in-game password-display dialog.
* Whether "Stereo"/"Music test" were ever reachable in another regional build (this is the US
  `BSVE` revision 0); they are dead in this image.
* The header was rebuilt (bad complement, zero checksum), but no code patch or trainer was found.

## 9. Tooling

* `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings -t x`, `grep -abo` for Phase 0/1.
* Python scripts in `/tmp/opencode/smashingdrive/`: `phase0.py`, `ptrscan.py`, `lits.py`,
  `enumerate.py` (the validator reimplementation and exhaustive count), `ssdiff.py` (zlib-decompress
  the mGBA `gbAs` savestate chunk and diff/extract RAM), `enter.py`, `batch.py`, `effect.py`
  (automated password entry), `blscan.py`.
* `arm-none-eabi-objdump -M force-thumb` for raw Thumb disassembly; REA's Ghidra provider for
  decompilation of `0x08005484`, `0x0800575C`, `0x08020878`, `0x080207B8`, `0x08020734`,
  `0x0802081C`, `0x080206D4`, `0x08021028`, `0x08005504`.
* mGBA 0.10.5 + Xvfb `:315` + openbox + `xdotool`/`scrot`; SDL audio disabled with
  `SDL_AUDIODRIVER=dummy`. The GDB stub was unreliable in this build, so RAM reads used
  savestate decompression (guide §16.13) instead.
* Web: archived GameFAQs cheat page via `web.archive.org` (snippet used as a lead, then verified
  in ROM and emulator). Fetched pages were treated as data only.

No copyrighted ROM data or assets are redistributed here — only addresses, algorithms, hashes and
our own generated codes.
