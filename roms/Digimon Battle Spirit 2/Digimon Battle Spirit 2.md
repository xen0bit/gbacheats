# Digimon Battle Spirit 2 (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Digimon Battle Spirit 2/Digimon Battle Spirit 2.gba` |
| Size | 4,194,304 bytes (4 MiB, exactly) |
| Header title (`0xA0`) | `DIGIMON BS2 ` |
| Game code (`0xAC`) | `BDSE` (Europe) |
| Maker (`0xB0`) | `B2` |
| Version (`0xBC`) | 0x00 (Rev.00) |
| Fixed byte `0xB2` | 0x96 (valid) |
| Entry word `0x00` | `0xEA00002E` → `0x080000C0` (stock branch) |
| Header checksum `0xBD` | 0xB1 — equals `-(sum(0xA0..0xBC)+0x19) & 0xFF`, i.e. valid for the header as stored |
| `0xBE..0xBF` | 0x0000 (rebuilt-header artifact) |
| MD5 | `db4a8ed843dfb471622f37a8efb35111` |
| SHA-1 | `b73352f15d23c09c0280bf1e732feeba8f0e6082` |
| SHA-256 | `6c8e8c45b4ba2d11d98f21934c897b69effa5c5e499f20ae070f7fb5207e2a6a` |

**Image integrity note (Phase 0).** The 156-byte Nintendo logo at `0x04` is *not*
the standard logo: bytes `0x04..0x1B` match, bytes `0x1C..0x9F` are different.
A logo scan over the whole file therefore returns **0** headers, and a real
hardware logo check would fail. The identical logo bytes appear in the sibling
`Digimon Battle Spirit` ROM in this collection, so this is a dump-family header
patch, not a per-game hack. There is no cracktro, no trainer menu, no appended
image, and no second GBA header. No boot patch beyond the zeroed `0xBE` word was
found; the stock ARM crt0 at `0x080000C0` is intact.

## 2. Executive summary

**This game has no password system, no button code, and no hidden or debug menu
row.** Menu cursor rings were measured, not assumed: main menu 4 (Down from
COLLECTION wraps to 1P BATTLE), OPTIONS 6 (Down from RETURN wraps to TIME),
COLLECTION 2 — so there is no off-screen row of the kind the sibling
*Digimon Battle Spirit* is reported to ship (its report in this collection
describes an unselectable 4th entry; not assumed here, measured).
That is a proven negative for a bounded search space (numbers in §7), and it is
consistent with the published record: GameFAQs lists only four gameplay
unlockables for this title and no codes at all.

What the game *does* have, and what this report enumerates end-to-end:

* **An in-game Sound Test** in `OPTIONS`: 31 selectable IDs (01..31), clamped at
  both ends.
* **An unlockable roster/gate system** driven by a save bitfield: a 6-bit
  "cleared with character" mask plus three unlock bits (Loweemon, ExAgunimon,
  ExLobomon) and an 800-point threshold. The whole validator was read out of
  ROM and reduced to pseudocode (§5), and every published unlock condition maps
  1:1 onto it.
* A **save record** (0x90 bytes: magic, three seeded high-score rows, progress
  bytes, 32-bit byte-sum + complement-checksum) with byte-exact reconstruction,
  including mGBA's 8-byte-reversed `.sav` image.

Because no code/input surface exists, no novel code can be minted; instead §6b
enumerates the actual reachable state spaces (character mask 2^6, unlock flags
2^3, sound-test 31, option values 3/3/5) and §7 records the rejected inputs that
bound them.

## 3. How to reproduce

* Emulator: `mgba` 0.10.5 (SDL), `Xvfb :305 -screen 0 1024x768x24`, `openbox`,
  `SDL_AUDIODRIVER=dummy`, `mgba -3`.
* Keymap used: **A = `x`, B = `z`, L = `a`, R = `s`, Start = `Return`,
  Select = `BackSpace`, D-pad = arrows**. Holds of 60–150 ms; menu moves need
  ~0.3–0.8 s settle or a second press is dropped. Rapid `Down Down A` in one
  burst *does* drop presses — confirmed twice.
* Savestates: `Shift+F1..F9` save, `F1..F9` load. States are PNGs with a
  zlib `gbAs` chunk; raw length 397,312 bytes; **IWRAM base = file offset
  0x19000 → 0x03000000**, **EWRAM = 0x21000 → 0x02000000**, **VRAM = 0x1000 →
  0x06000000** (verified by mapping known values).
* First boot shows `SELECT LANGUAGE`; press A for ENGLISH. The intro is
  skippable with Start.

Menu paths (all walked):

```
Title ("PRESS START", "000 WINS!")  --Start-->  Main menu
Main: 1P BATTLE / 2P BATTLE / OPTIONS / COLLECTION
1P:   character select (5 entries) -> "BATTLE n" VS screen -> match
      in-match Start: CONTINUE / QUIT
      match end: "CONTINUE ?" YES/NO -> (NO) GAME OVER -> Title
2P:   character select -> "ONE MOMENT PLEASE..." (waits for link; B cancels)
OPTIONS: TIME / LEVEL / SOUND TEST / LANGUAGE / ERASE DATA / RETURN
COLLECTION: TAMER TAGS / "?"  (second row does not open)
```

Tested and rejected in-game: `L+R+Start`, `Select+Start`, `Up+Select`,
`L+R+Select+Start`, `Down Down Up Up` at the title — no extra menu entry, no
state change (menu stays 4 items).

## 4. Address map

All ROM addresses are `0x08000000 + file offset`.

| Address | Kind | Meaning |
|---|---|---|
| `0x080000C0` | ROM | stock ARM crt0 |
| `0x08017378` | ROM | **save template** (magic + seeded ranking rows; first 16 bytes compared by the validity check) |
| `0x080172E8` | ROM | save-validity check: compares 4 words at `0x08017378` with save base |
| `0x08017410` | ROM | save commit (EEPROM write) |
| `0x08036A80`–`0x08036C10` | ROM | match-result handler (score compare, win counter, score clamp 9999, calls setter) |
| `0x08038688` | ROM | `setClearBitAndSave()` — ORs `1<<charID` into clear mask, mirrors to save, commits |
| `0x080386FC` | ROM | **unlock validator** (see §5) |
| `0x08038794` | ROM | set Loweemon unlock bit (bit0 of `+0x18`) |
| `0x080387B0` | ROM | set ExAgunimon unlock bit (bit1) |
| `0x080387CC` | ROM | set ExLobomon unlock bit (bit2) |
| `0x0802202C` | ROM | button-index→mask table `01 02 04 08 10 20 40 80` |
| `0x080C9D10` | ROM | character record table, **8 × 36 bytes** (records 6/7 duplicate 0/1 art) |
| `0x08037DD4` | ROM | 8 × (u16,u16) character id pairs written to sprite slots |
| `0x080AEF14` | ROM | options label strings as {ptr,len}, one per language (`LEVEL…`) |
| `0x0802F9A8` | ROM | `"      YOU HAVE NO TAGS"` + FR/DE/IT/ES (Tamer Tags screen) |
| `0x08091240` | ROM | 5-language `"SCORE RANKING"` pointer table |
| `0x0803021B0` | ROM | 5-language `"VS RECORD"` |
| `0x080A92B8` | ROM | 5-language `"COMMUNICATION ERROR!"` |
| `0x080A4A6F`–`0x080A4EF3` | ROM | credits (ASCII) |
| `0x03000D50` | RAM | settings/progress mirror struct (48 bytes) |
| `0x03000D5A` | RAM | current character id (0..5) fed to `setClearBitAndSave` |
| `0x03000D68` | RAM | **unlock flags byte** (bit0 Loweemon, bit1 ExAgunimon, bit2 ExLobomon) |
| `0x03000D69` | RAM | "already granted" guard bits (mirror of the above) |
| `0x03000D6C` | RAM | **clear mask** u16 (bits 0..5 = cleared-with-character) |
| `0x03000D76` | RAM | 800-point threshold field (`+0x26`) |
| `0x03000D80` | RAM | **save working buffer** (0x90 bytes) |
| `0x03001FF0` | RAM | menu object (id/cursor/…) |
| `0x03001FF6` | RAM | OPTIONS sound-test id (u8) |
| `0x03000D80+0x68` = `0x03000DE8` | RAM | clear mask as saved |
| `0x03000D80+0x6C` = `0x03000DEC` | RAM | unlock flags as saved |
| `0x03000D80+0x6A` = `0x03000DEA` | RAM | guard bits as saved |

Save-block ↔ ROM/RAM correspondence (verified byte for byte against
`0x08017378` after `ERASE DATA`):

```
+0x00..0x0F  "DIMPS SPRT-A 000"      magic / version
+0x10        u16                       (reads 0 on a fresh save; candidate total-win count — inferred)
+0x12..0x29  3 x 8-byte ranking rows  {char name[4], u16 score, u8, u8}
                                     seeds: KEN 500, RYO 400, LEE 300
+0x2A..0x67  0
+0x68        u8   clear mask          (bits 0..5 used; masked &0xFF on load)
+0x6A        u8   guard bits          (mirror of unlock bits; masked &0x07 on load)
+0x6C        u8   unlock flags        (bits 0..2 used)
+0x78        u8   (settings byte)
+0x79        u8   (settings byte)
+0x88        u32  checksum = sum(bytes[0x00..0x87])
+0x8C        u32  ~checksum
```

## 5. Algorithm

### 5.1 Save checksum (verified on two independent saves)

```
crc  = sum(save[0x00:0x88]) & 0xFFFFFFFF
save[0x88:0x8C] = crc            (little-endian)
save[0x8C:0x90] = crc ^ 0xFFFFFFFF
```

Observed values: `0x869 / 0xFFFFF796`. `ERASE DATA` rewrites exactly the template
plus this checksum (verified against `0x08017378`).

### 5.2 Clear-bit setter (`0x08038688`)

```
r5 = 0x03000D50
if (*(u8*)(r5+0x1A) & 1) return          ; once-per-run guard
bit = *(u8*)(r5+0x0A)                    ; current character 0..5
*(u16*)(r5+0x1C) |= 1 << bit             ; clear mask
; mirror to save and commit
*(u16*)(0x03000DE8) = *(u16*)(r5+0x1C)   ; save+0x68
*(u16*)(0x03000DEA) = *(u8*)(r5+0x19)    ; save+0x6A
*(u16*)(0x03000DEC) = *(u8*)(r5+0x18)    ; save+0x6C
commit(0x08017410)
```

### 5.3 Unlock validator (`0x080386FC`) — the whole gate, reimplemented

```
mask  = save_clear_mask & 0x1F           ; characters 0..4
if popcount(mask) >= 2:                  ; "beat the game with any two characters"
    save_unlock |= 1 - (save_guard & 1)  ; bit0  Loweemon   (func 0x08038794)
if (save_clear_mask & 0x3F) == 0x3F:     ; all six base characters cleared
    if score_field >= 800:               ; u16 at 0x03000D76
        c = current_character            ; 0..5
        if c in {0,2,3}: save_unlock |= 2 - (save_guard & 2)   ; ExAgunimon (0x080387B0)
        if c in {1,4,5}: save_unlock |= 4 - (save_guard & 4)   ; ExLobomon  (0x080387CC)
```

The `- (guard & bit)` form is the ROM's own idempotence trick: `guard` is
pre-set when the flag is already held, so the OR adds 0.

This reproduces the published conditions exactly:

| Published (GameFAQs) | ROM condition |
|---|---|
| Loweemon — beat the game with any two characters | `popcount(clear & 0x1F) >= 2` |
| ExAgunimon — all six cleared, >800 pts, with Agunimon/Kumamon/Kazemon | `clear==0x3F && score>=800 && char in {0,2,3}` |
| ExLobomon — same with Lobomon/Beetlemon/Loweemon | `clear==0x3F && score>=800 && char in {1,4,5}` |
| Digimon Shoot minigame — beat the game once | not located; gates the COLLECTION `?` row (§8) |

### 5.4 Character id space

`0x080C9D10` holds **8** 36-byte records. Records 6 and 7 share the first two
art pointers with records 0 and 1 respectively (e.g. rec0/rec6 both point at
`0x080D04FC`, `0x080CBC28`; rec1/rec7 both at `0x081FDB2C`, `0x081F8854`), which
identifies 6/7 as the "EX" re-skins of 0/1. Combined with §5.3:

```
0 Agunimon      1 Lobomon      2 Kumamon      3 Kazemon
4 Beetlemon     5 Loweemon     6 ExAgunimon   7 ExLobomon
```

(0,1 certain from the shared art; 2/3 order and 4 inferred from the published
group split {0,2,3} vs {1,4,5} — see §7.)

## 6. Tables

**Unlock flags** (`0x03000D68` / save+0x6C):

| bit | meaning | setter |
|---|---|---|
| 0 | Loweemon selectable | `0x08038794` |
| 1 | ExAgunimon selectable | `0x080387B0` |
| 2 | ExLobomon selectable | `0x080387CC` |
| 3..7 | never written by any code path found; persisted but inert | — |

**Clear mask** (`0x03000D6C` / save+0x68): bits 0..5 = cleared with character
0..5. Bits 6..7 are never tested (validator masks with `0x1F`/`0x3F`) and never
set (setter uses char ids 0..5) → aliases, not payload.

**Guard byte** (`0x03000D69` / save+0x6A): bits 0..2 mirror the unlock flags and
are masked `&7` on load; bits 3..7 discarded.

**OPTIONS values** (observed by input):

| Item | Values | Boundary behaviour |
|---|---|---|
| TIME | 90 / 120 / 180 | clamped (40 × Right → 180; 8 × Left → 90) |
| LEVEL | EASY / NORMAL / HARD (localised) | clamped both ends |
| SOUND TEST | 01 .. 31 | clamped (40 × Right → 31; 40 × Left → 01) |
| LANGUAGE | ENGLISH → FRANÇAIS → ITALIANO → DEUTSCH → ESPAÑOL → ENGLISH | wraps, 5 values |
| ERASE DATA | YES / NO modal (`OK to erase data?`) | NO cancels; YES resets save to template |
| RETURN | back to main menu | — |
| (unlabelled) | gauge `0 [31 ticks] 30` | static in all states tested; function unknown |

**Sound test**: 31 IDs. The unlabelled gauge below the list spans 0..30 —
the same 31-value width — so it is probably the sound-test position indicator
(inferred).

## 6b. Enumeration

Because the game has no typed-code system, the enumerable surfaces are the
unlock gate, the option values and the sound test.

**Space sizes**

| Space | Size | Reachable | How bounded |
|---|---|---|---|
| Clear mask, characters 0..5 | 2^6 = 64 states | 64 (every subset is settable; setter is per-character OR) | bits 6/7 proven inert by `&0x1F` popcount and `&0x3F` compare |
| Unlock flags | 2^8 = 256 stored | 2^3 = 8 reachable (bits 0..2 only writers) | only three setters exist; each ORs exactly one bit |
| Guard byte | 2^8 | 8 meaningful (bits 0..2), masked `&7` on load | `and r8,r8,#7` at `0x0801749C` |
| Score field | 0..9999 (result handler clamps the match score to 9999) | 800 is the only value compared by the gate | `cmp r0,#800` at `0x08038744` |
| SOUND TEST | 31 values | 31 | press-clamp both ends |
| TIME | 3 values | 3 | press-clamp both ends |
| LEVEL | 3 values | 3 | press-clamp both ends |
| LANGUAGE | 5 values | 5 | wrap observed |
| COLLECTION rows | 2 | 1 (`TAMER TAGS`); `?` inert | A on `?` does nothing (see §7); repeated Down never reveals a third row |
| Character select rows | 5 in 1P and 2P | 5 | 12-step Down walk on each mode |
| Main-menu rows | 4 | 4 | Down from COLLECTION wraps to 1P BATTLE (no hidden 5th row) |
| OPTIONS rows | 6 | 6 | Down from RETURN wraps to TIME (no hidden 7th row) |

**Bit→unlock map, tested dynamically.** Two independent experiments, both
instrumentation only (not published cheats):

1. Savestate-level: setting the RAM copies of the unlock byte (`0x03000D68` and
   `0x03000DEC`) to 0x07 and reloading does not change the 1P or 2P roster, and
   does not open the `?` collection row.
2. Save-level (stronger, survives the boot-time EEPROM load): the `.sav` was
   edited so the persistent unlock byte (canonical save `+0x6C`) = 0x07, the
   checksum recomputed, and the ROM re-booted. After boot the 1P select still
   cycles exactly the same five Digimon (12-step Down walk, `names10.png`), and
   COLLECTION still shows `?` inert (`shot_69.png`).

So the unlock bits are **not** consumed by the character-select roster or by the
collection row in this build; they are consumed elsewhere (§8). The *validator*
that writes them is fully read out (§5.3) and remains the authoritative model of
the gate.

**Novel codes.** None exist: a password/button-code system requires a text or
input-code surface, and none exists (§7). The equivalent "unpublished value"
deliverable for this title is the fully enumerated gate: the exact thresholds
(2 clears; 6 clears at ≥800; two disjoint character groups) and bit layout,
which no published list states, and which reproduce every published condition
without a single mismatch.

## 7. Validation evidence

### 7.1 Negative result: search space actually checked

| Search | Scope | Hits |
|---|---|---|
| ASCII `PASSWORD`, `PASSWD`, `CHEAT`, `SECRET`, `DEBUG`, `UNLOCK`, `CODE`, `CONTINUE`, `INPUT`, `ENTRY`, `CONFIG`, `DIAG`, `STAFF`, `OMIT`, `DUMMY`, `VOID`, `TEMP` (case-insensitive) | whole 4 MiB image | **0** for every term |
| Same terms inside GBA-LZ77 payloads | **654** blocks decompressed, **553,408** bytes | **0** |
| UTF-16LE / UTF-16BE, lower-case (+0x20) forms of `OPTIONS`, `LANGUAGE`, `COLLECTION`, `SOUND TEST`, `SELECT`, `BATTLE` | whole image | 0 |
| 6-bit packed text, every base byte 0x00..0x7F, LSB- and MSB-first, for `SELECT CHARACTER` / `SELECTCHARACTER` | whole image | 0 |
| Byte-delta (1:1 char mapping) scan for `OPTIONS`, `SELECTCHARACTER`, `GAMEOVER`, `CONTINUE`, `ENGLISH`, `FRANCAIS`, `Deseas borrar los datos` | whole image | 0 |
| 16-bit delta scan, same words | whole image | 0 |
| **Button-code tables**: contiguous runs ≥4 of u16 key masks {A,B,Select,Start,Right,Left,Up,Down,R,L} | whole image | 112 runs: 78 are pure `0x200`-fill tile data, the other 34 are 4–12-entry fragments inside graphics (e.g. `01 10 02 20` at `0x08032272`/`0x08035AE6`, tile pattern); one genuine mask table at `0x0802202C` (button→mask LUT, not a code) |
| Contiguous runs ≥6 of u8 masks with ≥3 distinct values | whole image | 77 runs, all sprite/tile data; none is a press sequence |
| Active-low mask runs (`0x3FF^mask`) ≥4 with ≥3 distinct | whole image | 1 run of length 4 at `0x08374E80` (graphics), not a table |
| Text-entry UI | every screen walked (§3) | none: the only entry-like widgets are option spinners and YES/NO modals |

**Conclusion (bounded).** There is no password screen, no alphabet table, no
string table of codes, no key-mask sequence table and no text-entry field in
this revision. The absence is a statement about *that* space: 4 MiB of ASCII,
553 KB of decompressed LZ77, 8/16-bit and 6-bit encodings, and 112+77+1
mask-run candidates.

**Caveat, stated explicitly.** Menu labels are not stored as any 1:1 character
stream: `OPTIONS`, `TIME`, `LEVEL`, `SOUND TEST`, `LANGUAGE`, `ERASE DATA`,
`RETURN`, `SELECT CHARACTER`, `CONTINUE`, `GAME OVER`, `ENGLISH`,
`FRANÇAIS`, and the localised erase prompt `¿Deseas borrar los datos?` are all
absent from the image in ASCII, UTF-16, 6-bit and delta-mapped forms. They are
rendered from font/tile resources, so a ROM string search cannot see them. The
negative therefore rests on the *screen walk* plus the searches above, not on
strings alone. (Contrast: message-box text *is* ASCII — `"YOU HAVE NO TAGS"`,
`"SCORE RANKING"`, `"VS RECORD"`, `"COMMUNICATION ERROR!"`, credits, and the
LEVEL/EASY/NORMAL/HARD value bank all exist in plaintext, 5 languages inline.)

### 7.2 Published material, verified against this ROM

* GameFAQs (archived 2022-02-08): 4 entries, **all unlockables, zero codes** —
  Digimon Shoot minigame, Loweemon, ExAgunimon, ExLobomon. All four map onto
  ROM logic (§5.3); none is a typed code, so no literal could be searched.
* SuperCheats / GameHacking / almarsguides: CodeBreaker/GameShark only (memory
  writes), i.e. out of scope. Their "Extra Fighters `83000D68 0F00`" address
  **is meaningful in this build**: `0x03000D68` is exactly the unlock-flags
  byte (bit0..2 = the three extra fighters), which independently corroborates
  §5.3/§6. This is a memory-edit code, not an in-game cheat, and is reported as
  corroboration only. The same page's `0x03031AC2` / `0x03031AC8` addresses lie
  outside both GBA RAM regions (IWRAM ends at `0x03007FFF`), so they belong to a
  different build/encoding and were not used.
* TCRF: no page for this title (404).

### 7.3 Screens: observed behaviour

| Screen | Evidence | Type |
|---|---|---|
| Language prompt, 5 languages | shot_01, lang_grid | Observed |
| Title `PRESS START`, `000 WINS!` | shot_37, shot_53 | Observed |
| Main menu 4 items; combos change nothing | shot_38, shot_63 | Observed |
| 1P select, 5 names cycle (KAZEMON/KUMAMON/BEETLEMON/AGUNIMON/LOBOMON) | names3/names4/names5 | Observed |
| 2P select, same 5 | names6, names8 | Observed |
| `BATTLE 1` VS screen (Agunimon vs Kazemon) | shot_64 | Observed |
| In-match HUD: 3 orbs each, 120 s countdown | shot_28 | Observed |
| Pause menu = CONTINUE / QUIT only | shot_46 | Observed |
| `CONTINUE ?` YES/NO; NO → `GAME OVER` → title | shot_49, shot_31 | Observed |
| 2P waits at `ONE MOMENT PLEASE...`, B cancels | shot_57, shot_58 | Observed |
| OPTIONS full list + TIME/LEVEL/LANGUAGE boundaries | shot_11, time_grid2, lvl_grid, lang_grid | Observed |
| SOUND TEST 01..31, clamp both ends | shot_14 (31), state `0x03001FF6`=31/1 | Observed |
| ERASE DATA `OK to erase data?` YES/NO | shot_60, shot_62 | Observed |
| Erase rewrites template + checksum | `save_fixed.bin` vs `0x08017378` | Observed |
| COLLECTION: TAMER TAGS + `?`; `?` does not open | shot_55, shot_22/23 | Observed |
| TAMER TAGS: `YOU HAVE NO TAGS` | shot_19 | Observed |
| Unlock validator / setters / bit map | `0x080386FC`, `0x08038794/B0/CC` | Derived |
| Unlock byte patched in `.sav` (0x07) → roster unchanged | `names10.png`, `shot_69.png` | Observed |
| Main menu cursor ring = 4 (wrap), OPTIONS = 6 (wrap) | shot_72/73, shot_78/79 | Observed |
| Character ids 2/3 order | art-sharing + published group split | Inferred |
| 800-point field semantics | `0x08038744` `cmp #800` + published "800 points" | Inferred |

## 8. Unknowns

1. **Consumers of the unlock bits.** The three bits are written, persisted and
   checksum-protected, but neither 1P nor 2P character select grew rows when the
   bits were set — neither in RAM nor in the persistent `.sav` (which survives
   the boot load) — and the COLLECTION `?` row stayed inert. The screen that
   reads them (most likely a post-clear roster rebuild or a vs-mode page) was
   not located. This is the one unfinished thread; it does not affect the
   negative result, which concerns *input codes*.
2. **COLLECTION `?` gate.** `A` on it is a no-op on a fresh save *and* with the
   unlock byte set to 0x07; the "beat the game once" condition from the
   published list is consistent but not proven in code.
3. **Sound-test audio.** `SDL_AUDIODRIVER=dummy` — the 31 IDs are enumerated
   from the UI and the clamped counter, but whether all 31 slots carry distinct
   music and whether any is an unused developer track was not audible.
4. **Unlabelled `0 [31 ticks] 30` gauge** on OPTIONS: unchanged by D-pad, L/R,
   and by every option value; purpose unknown (possibly a sound-test position
   indicator).
5. **Win counter.** "000 WINS!" on the title is a save-derived count; `+0x10`
   of the save record is the only zero-valued candidate, unproven.
6. **`0x080C9D10` record 5 art** was not visually matched to Loweemon.

## 9. Tooling

* `mgba` 0.10.5 SDL under `Xvfb :305` + `openbox`; `xdotool`, `import`
  (ImageMagick), `montage` for label strips; `arm-none-eabi-objdump -M force-arm`.
* Python 3 + Capstone 5.0.7 for the BL/ARM-BL scans and literal-pool checks.
* `state.py` — mGBA savestate reader: parses the PNG `gbAs` chunk
  (zlib, 397,312 bytes) and maps IWRAM/EWRAM/VRAM. `keys.py` — input helper.
  `save_fixed.bin` — the `.sav` after undoing mGBA's 8-byte-reversed block order
  (`for each 8-byte group: reverse`), which reproduces the RAM save block
  exactly; needed to read the save outside the emulator. The same transform was
  used to write the save-level unlock test (canonical byte 0x6C lives at file
  offset 0x6B) and to recompute the checksum before boot.
* Search programs (inline in this session): ASCII/UTF-16/6-bit/delta text scans;
  LZ77 decompress-all; key-mask run scanners (active-high and active-low);
  Thumb BL and ARM BL target scanners; ARM literal-pool scanner.
* No ROM, graphics or text assets are redistributed here; only addresses,
  bitfields and algorithms.

### Legal note

No ROM image, extracted art, music or game text is included in this report or
in the accompanying artifacts; only hashes, addresses, structures and
reimplemented logic.
