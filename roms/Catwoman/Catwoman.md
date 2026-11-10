# Catwoman (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Catwoman/Catwoman.gba` |
| Size | 8,388,608 bytes (8 MiB, `0x800000`) |
| `file` | `Game Boy Advance ROM image: "CATWOMAN    " (BCWE69, Rev.00)` |
| MD5 | `041cd0228e12f003f9736fdad77cdbf0` |
| SHA-1 | `dc49889caf678e9dfc2465ab55b7019e2d5d0860` |
| SHA-256 | `55860b55712b7fd3a78cf029c6a6bf81f2ddd014a0654d094f6c842278c3ea56` |
| Header title (`0xA0`) | `CATWOMAN    ` |
| Game code (`0xAC`) | `BCWE` |
| Maker code (`0xB0`) | `69` |
| Software version (`0xBC`) | `0x00` |
| Complement byte (`0xBD`) | `0xE7` (valid: recomputed `0xE7`) |
| Header checksum (`0xBE`) | `0x0000` (rebuilt header; computed `0xFAE7`) |
| Entry word (`0x00`) | `0xEA000030` → `0x080000C8` |
| Embedded GBA headers | 1 (Nintendo logo only at file `0x0`) — single game, no multicart |
| Engine strings | `GAX Sound Engine 3.05 (Aug 13 2003)`, `Shin'en Multimedia. Code: B.Wodok` (`0x080B9524`/`0x080B9549`), `GMOD7: CACHE NOT IMPLEMENTED` (`0x080001E0`) |
| Publisher strings (RAM) | `EA GAMES`, `CHALLENGE EVERYTHING`, `CATWOMAN INTERACTIVE GAME`, `2004 ELECTRONIC ARTS INC.`, `DC COMICS`, `WBIE` |

### 1.1 Header / entry anomaly (Phase 0)

The header has been rebuilt: the 16-bit header checksum is `0x0000` (the normal
artifact of a rebuild) and the entry word is `0xEA000030`, not the stock
`0xEA00002E`. The complement byte is intact and correct, so the GBA BIOS accepts
the header (verified by recomputation and by booting).

The cartridge crt0 is linked at `0x080000C8`, i.e. shifted **+8 bytes** from the
standard `0x080000C0`. The eight bytes at `0x080000C0` are:

```
080000C0: 0DFDAB2A   (not a valid crt0 prologue)
080000C4: 000006C3
080000C8: E3A00012   mov r0, #0x12        ; standard crt0 start
080000CC: E129F000   msr CPSR_fc, r0
080000D0: E59FD078   ldr sp, [pc, #0x78]  ; 0x03007FA0
...
08000158: 08030105   .word main (Thumb)
```

The literal pool at `0x08000148`–`0x08000158` and the `main` pointer are
self-consistent at the shifted offset, so the image is a repacked/relinked
release rather than a corrupt dump. No cracktro string, no trainer menu, and no
appended trainer was found; the only patched bytes are the entry word and the
eight skipped bytes at `0x0C0`. This is recorded as a packaging anomaly, not a
cheat.

## 2. Executive summary

**No in-game cheat, password, or unlock code system exists in this GBA SKU, and
the widely published "Catwoman GBA passwords" do not belong to this ROM.**

Three independent lines of evidence:

1. **The published passwords are absent from the image.** All eight published
   level passwords (`K6T@1`, `1QT@@`, `KQYXY`, `1@FVQ`, `K@FVP`, `@JFV4`,
   `KJFZR`, `16TGV`) were searched literally in the ROM (ASCII, reversed, and
   lower-case) and in the running EWRAM/IWRAM. Hit count: **0** in every encoding.
   No password alphabet string (`0123456789…`, `ABCDEFGHIJ…`) exists either.
2. **The GBA game has six levels, not nine.** The level-select names decompressed
   into EWRAM are `1-JEWELRY`, `2-NIGHTCLUB`, `3-FACTORY`, `4-MANSION`,
   `5-PERFORMANCE CENTER`, `6-HEDARE HQ`. The published list is for levels **2–9**,
   i.e. a different edition (the console/PC build). This is the §16.11 failure mode:
   a title-and-platform match is not enough; the literals were checked and are
   absent.
3. **There is no password/cheat surface in the strings.** `PASSWORD`, `CHEAT`,
   `CODE`, `INVALID`, `LEVEL SELECT`, `STAGE SELECT`, `OPTIONS`, `GALLERY`,
   `COSTUME`, `GADGET`, `UNLOCK` occur **0 times** in the ROM, EWRAM and IWRAM.
   The only `PASS` hits are dialogue ("A SECRET PASSAGE"), the only `SECRET` hits
   are the same dialogue, and the only `DEBUG`/`BONUS`/`FREE CAM`/`NEXT LEVEL`
   hits are a 7-language debug-menu text blob that no code references (see §6).

A debug-menu-like text blob **does** exist in the ROM (`0x083DDC29`, 7 language
copies) with labels such as `NEXT LEVEL`, `SECRET`, `FREE CAM`, `CUTSCENES`,
`INVINCIBLE`, `TERMINATOR`, `DEBUG`, `BONUS`, `WALL`. It is **dead data**: the
only 32-bit pointer into its range (`0x084CA896 → 0x083DEA55`) is a false positive
inside a data table (the bytes disassemble as nonsense), and the strings never
appear in RAM. It is not reachable by any input.

## 3. How to reproduce

```bash
# identity
md5sum / sha1sum / sha256sum roms/Catwoman/Catwoman.gba
xxd -l 0x200 roms/Catwoman/Catwoman.gba

# literal check of every published password (all return nothing)
for p in 'K6T@1' '1QT@@' 'KQYXY' '1@FVQ' 'K@FVP' '@JFV4' 'KJFZR' '16TGV'; do
  grep -abo "$p" roms/Catwoman/Catwoman.gba
done

# emulator
Xvfb :238 -screen 0 1024x768x24 &
DISPLAY=:238 openbox &
DISPLAY=:238 SDL_AUDIODRIVER=dummy mgba -3 roms/Catwoman/Catwoman.gba &
# focus the mGBA window, then use xdotool XTEST keys
```

Note on input: with mGBA 0.10.5 SDL on this Xvfb host, `xdotool key` alone does
not reach the game. A mouse click on the mGBA window is required before keys are
seen; even then delivery was unreliable (see §8). All dynamic claims below were
therefore cross-checked against RAM/VRAM dumps, not against keypress alone.

## 4. Address map

| Address | Meaning |
|---|---|
| `0x08000000` | entry branch `b 0x080000C8` (patched; stock would be `0x080000C0`) |
| `0x080000C0` | 8 skipped bytes `0x0DFDAB2A`, `0x000006C3` |
| `0x080000C8` | crt0 (SVC/system stack setup, IWRAM/VRAM/PAL clear, `main` call) |
| `0x08000148`–`0x08000158` | crt0 literal pool; `0x08000158 = 0x08030105` (Thumb `main`) |
| `0x08030104` | `main` (Thumb) |
| `0x080B9524` | `GAX Sound Engine 3.05` banner |
| `0x080001E0` | `GMOD7: CACHE NOT IMPLEMENTED` assertion text |
| `0x082E3C4`–`0x082E5A0` | input/keypad helper region (literal `0x04000130` at `0x082E444` is an instruction-aligned false positive) |
| `0x083877A6` | dialogue text blob, English (`THIS KITTY LIKE TO PLAY.…`), 7 language copies |
| `0x083DDC29` | **debug-menu text blob**, English (`NEXT LEVEL`, `SECRET`, `FREE CAM`, …) |
| `0x083DE1F6`, `0x083DE7E4`, `0x083DEDF5`, `0x083DF422`, `0x083DFA31`, `0x083DFFA2` | the other six language copies of the same debug blob |
| `0x083D835E` | area-name blob (`ROOFTOP`, `BUILDING`, `MIDNIGHT`, `CLUB`, `LEAP`, `ENTRANCE`, `LOBBY`, `BOX`) |
| `0x087F66B2` | menu-string blob, English (`US ENGLISH`, `CONTINUE SAVED GAME`, …), 7 language copies |
| `0x020028B6` | EWRAM: decompressed menu-string blob (runtime) |
| `0x02002843`+ | EWRAM: string offset table (55 entries) |
| `0x02002100` | EWRAM: game global state (magic `3XAG` at `+4`, GAX sound-engine state) |

Text blobs are stored as `\x04<string>\x00` records preceded by a
`u16` offset table (base = blob start − 3); the 7 language copies are consecutive.

## 5. Algorithm

Not applicable — no validator, checksum, or code generator was found. The only
"coding" present is the game's localised text storage:

```
blob      = "\x04\x20\x00" + concat( "\x04" + text + "\x00" )
offsets[] = u16 offset of each "\x04" record, relative to (blob_start - 3)
```

The ROM stores the same strings in a *packed* form (records concatenated without
the `\x00`/`\x04` separators and with shared substrings elided) and the game
reconstructs the EWRAM form at runtime. This was confirmed by comparing the ROM
blob at `0x087F66B2` with the EWRAM blob at `0x020028B6`: the EWRAM form is the
fully separated, de-elided version. No password alphabet or checksum participates
in this scheme.

## 6. Tables

### 6.1 Published codes vs. this ROM

| Published | Effect | In ROM? | In EWRAM? |
|---|---|---|---|
| `K6T@1` | Level 2 | no | no |
| `1QT@@` | Level 3 | no | no |
| `KQYXY` | Level 4 | no | no |
| `1@FVQ` | Level 5 | no | no |
| `K@FVP` | Level 6 | no | no |
| `@JFV4` | Level 7 | no | no |
| `KJFZR` | Level 8 | no | no |
| `16TGV` | Level 9 | no | no |

### 6.2 Level table (from RAM, EWRAM `0x020028E7`–`0x02002932`)

`1-JEWELRY`, `2-NIGHTCLUB`, `3-FACTORY`, `4-MANSION`, `5-PERFORMANCE CENTER`,
`6-HEDARE HQ` — six entries. The published list requires ≥9 levels.

### 6.3 String-space search counts (ROM / EWRAM / IWRAM)

```
PASSWORD 0/0/0   CHEAT 0/0/0     CODE 0/0/0      INVALID 0/0/0
LEVEL SELECT 0/0/0   STAGE SELECT 0/0/0   OPTIONS 0/0/0   GALLERY 0/0/0
COSTUME 0/0/0   GADGET 0/0/0   UNLOCK 0/0/0   TERMINATOR 0/0/0
INVINCIBLE 0/0/0   CUTSCENE 0/0/0
PASS 14/0/0 (dialogue "SECRET PASSAGE")   SECRET 6/0/0 (same dialogue)
DEBUG 7/0/0   BONUS 11/0/0   FREE CAM 7/0/0   NEXT LEVEL 7/0/0
   (all 7 hits = the 7 language copies of the debug blob at 0x083DDC29)
```

### 6.4 Debug-menu blob (dead data)

English copy at `0x083DDC29`:

```
\x04 NEXT LEVEL \x00 \x04 SECFREE CAM CUTSCES: INV CIB TERMINATOR DEBUG BONUS
NSSD WALL LOTI SUMEOP CTROSEP MOD QUIT ASIC UNK TAMUS FX IGHT DFF
1-JEWRY 2-NCLUB 3-F 4-MAI 5-PFCE 6-HA HQ NOT YE IMPMY OAU AVE, …
```

The `1-JEWRY 2-NCLUB 3-F 4-MAI 5-PFCE 6-HA` fragment is the packed form of the
six level names (`1-JEWELRY`, `2-NIGHTCLUB`, `3-FACTORY`, `4-MANSION`,
`5-PERFORMANCE CENTER`, `6-HEDARE HQ`), which confirms the blob is a debug/level
menu text resource. It is not reachable: no code pointer targets it and its
strings never enter RAM.

## 6b. Enumeration

**No code/password space exists to enumerate.** The deliverable for a negative
result under §0.2 is a bounded statement about the searched space, which is:

* **Published-code space checked:** 8/8 published passwords, each in 3 encodings
  (ASCII, reversed, lower-case) against the raw ROM and against the runtime
  EWRAM/IWRAM → 0 matches.
* **Password-screen text space checked:** 13 keywords (`PASSWORD`, `PASS`,
  `CHEAT`, `CODE`, `ENTER`, `INVALID`, `WRONG`, `LEVEL SELECT`, `STAGE SELECT`,
  `OPTIONS`, `GALLERY`, `COSTUME`, `GADGET`, `UNLOCK`) over ROM + EWRAM + IWRAM
  → no password screen, no invalid-code message, no unlock/gallery/costume
  surface. A password screen without an "invalid" message is not a plausible
  design, so this is a strong negative.
* **Alphabet space checked:** no run of ≥5 characters restricted to the 15
  symbols used by the published list (`K 6 T @ 1 Q Y X F V 4 J Z R G`) that forms
  a table (the 38 raw hits are random data, not NUL/separated records).
* **Level space checked:** the level table is exactly 6 entries; the published
  list's levels 7–9 do not exist in this SKU, so those passwords cannot be
  expressed by this game at all.
* **Debug-menu space checked:** 1 blob × 7 language copies, all accounted for;
  no code xref, no RAM copy, no input path.

Because there is no system, no novel code can be minted, and no bounds can be
proven by rejection. The rejection evidence is instead: every published code was
tested against the ROM and rejected (absent), and no candidate alphabet yields a
validator.

## 7. Validation evidence

| Claim | Type |
|---|---|
| Header fields, hashes, entry patch, rebuilt checksum | **Observed** (bytes) |
| Complement byte valid, BIOS accepts header | **Derived** (recomputation) + **Observed** (game boots) |
| Published passwords absent from ROM/RAM | **Observed** (literal search, 0 hits) |
| GBA level table = 6 entries | **Observed** (EWRAM string table at `0x020028E7`) |
| No password/cheat UI text anywhere | **Observed** (keyword counts over ROM/EWRAM/IWRAM) |
| Debug blob exists, 7 languages | **Observed** (bytes at `0x083DDC29` + 6 more) |
| Debug blob is dead data | **Derived** (no code pointer; strings never in RAM; only candidate pointer is a data false positive) |
| Game boots to intro then title screen | **Observed** (VRAM decoded to ASCII art; EWRAM string table) |
| Menu navigation by key | **Inferred / not completed** — see §8 |

## 8. Unknowns

* **Menu walk not completed by key input.** With mGBA 0.10.5 SDL on Xvfb `:238`,
  XTEST key delivery was unreliable: a mouse click on the mGBA window is required
  before keys register, and even then only some presses took effect (one
  `Return` advanced the intro to the title screen; subsequent presses produced
  zero VRAM delta). The title screen and the intro logo were decoded from VRAM;
  the main menu, level-select, options and pause screens were **not** reached by
  input in this session. The RAM evidence (level table, absence of any
  password/options strings) is independent of that limitation and is what the
  negative result rests on, but the screen-by-screen walk required by §0.2 item
  5 is not fully demonstrated here.
* **Text de-elision algorithm not fully reversed.** The packed ROM form and the
  EWRAM form were matched by inspection for the menu blob; a byte-exact
  reimplementation of the packer was not written because it is not needed for the
  cheat question.
* **`0x080000C0` eight-byte insertion** is unexplained (repack tool vs. removed
  stub). It does not affect gameplay or the cheat conclusion.
* **Save format / level-unlock flags** were not reversed (no `.sav` content was
  produced; the cart uses a battery save but no unlock flag was observed).

## 9. Tooling

* `arm-none-eabi-objdump` (`-D -b binary -marm --disassembler-options=force-thumb`)
* Python 3 + Capstone/Keystone (available), `struct`/`zlib` for savestate parsing
* mGBA 0.10.5 (`/usr/games/mgba`), Xvfb `:238`, openbox, `xdotool`
* Savestate parser: mGBA `.ss*` = PNG with a zlib `gbAs` chunk; decompresses to
  397,312 bytes (`0x61000`): CPU `0x00000`, palette `0x0800`, OAM `0x0C00`,
  VRAM `0x1000`, IWRAM `0x19000`, EWRAM `0x21000`. Used for all RAM/VRAM evidence
  above (no screenshots were taken; screens were reconstructed from VRAM as text).
* Analysis scripts and state dumps: `/tmp/opencode/catwoman/`
  (`gdbremote.py`, `ssparse.py`, `render.py`, `strings4.txt`, `s*.ss1`, `w*.ss1`,
  `n*.ss1`).

No ROM, asset, or copyrighted material is redistributed by this report; all
findings are addresses, counts, and the analyst's own tooling.
