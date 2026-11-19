# Pac-Man World 2 (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Pac-Man World 2.gba` |
| Size | 4,194,304 bytes (0x400000, 4 MiB) |
| `file` | Game Boy Advance ROM image: "PAC WORLD 2" (B2CEAF, Rev.00) |
| Header title | `PAC WORLD 2` |
| Game code | `B2CE` |
| Maker | `AF` |
| Version | 0x00 |
| Entry word | `0xEA00002E` (stock `b 0x080000C0`) |
| MD5 | `86e6497272f39b19af6750d699569531` |
| SHA-1 | `a3da2ad5cf120cb53e663c2290eb8872f5650ba7` |
| SHA-256 | `d8879efe1cddb0a481566a06a9210eeba6f0ec15f7304c3ec492bc3c6276d458` |

Credits strings at 0x0809F828+ identify developer **Full Fat** and publisher **Namco / DSI**.
Phase 0 embedded-header scan: exactly one Nintendo logo (file 0x4), no multiboot halves,
no appended trainer, entry branch is the stock CRT0 branch (§16.1 patch/cracktro checks pass).
Header checksum (0xBE) and complement (0xBD) are both `0x00` (expected complement 0x6A),
a benign rebuilt-header artifact; the BIOS does not validate it for cartridge images.

## 2. Executive summary

The GBA version has a **developer-intended password system** (no password list is stored in
the ROM — every published code is algorithmic). It is reached from **title → PASSWORD** and
uses an 8-character on-screen keyboard. The password is a 32-bit packed word encoded 4 bits
per character with a 16-symbol alphabet `BDSTQRFNLMZPWHVJ` at 0x08093368. The on-screen
keyboard offers 22 symbols (`BCDFGHJKLMNPQRSTVWXZ?_` at 0x08093320) plus backspace/enter;
the 6 extra symbols (`C G K X ? _`) can be typed but can never form a valid code.

The validator at **0x080466A0** checks a 6-bit XOR checksum and five range/gating rules.
Its complete accepted space is **10,092,544 codes** out of 16^8 = 4,294,967,296 possible
alphabet strings. Two novel codes absent from every published list were minted, entered on
the real screen and RAM-verified:

* `DDBBBBQQ` — level 17, currentLevel 0: opens all 17 levels (opened-level bitmask becomes
  `0x0001FFFF`), starts Pac-Village at 50% — exercises the `special spooky check` branch.
* `TQBBBWPT` — level 3 with `maze = 15` (published `TQBBBBQB` has `maze = 0`): starts Tree
  Tops, maze RAM byte becomes `0x0F`.

Bounds were proven by six in-game rejections (all show `PASSWORD INVALID`). Three published
codes were proven wrong/inapplicable to this SKU. No button-code system, hidden menu reachable
from the walked screens, or GameShark/CodeBreaker content was found. A "cheat enabled all
level open" debug flag exists in dead code (see §8).

## 3. How to reproduce

Emulator: mGBA (SDL), `Xvfb :319`, `SDL_AUDIODRIVER=dummy`, keymap A=`x`, B=`z`,
Start=`Return`, D-pad = arrow keys. Hold keys ~60–150 ms; menu highlights blink, so verify
the screen by screenshot after each transition.

1. Boot; press Start through the Namco/Full Fat logos and the (unskippable) intro cinematic
   until the title menu shows START / PASSWORD / OPTIONS.
2. Down once from START, press A → **PASSWORD** screen (8×3 keyboard, entered text at bottom).
3. Navigate the grid with the D-pad, press A per letter, then select the `↵` cell (row 3,
   column 8) and press A to submit. `←` (row 3, column 7) is backspace.
4. Saved state used for repeatable tests: mGBA slot 1 (`Shift+F1` saves, `F1` loads) taken
   on the empty PASSWORD screen.
5. Codes tested (see §6b/§7 for results): published `TQBBBBQB`, `LVBBBBWT`, `RLBBBBQB`;
   novel `DDBBBBQQ`, `TQBBBWPT`; rejected `TBBBBBQB`, `TDBBBBWQ`, `RZBBBBBB`,
   `RBBBBBQD`, `BDVJJPNW`, `BJJJJPPJ`.

## 4. Address map

File offset = ROM address − 0x08000000.

| ROM address | Role |
|---|---|
| 0x08046270 | password-screen character input handler (char codes 7=backspace, 8=enter) |
| 0x080465F8 | **decoder**: 8 chars → packed 32-bit word (uses alphabet at 0x08093368) |
| 0x08046598 | encoder: packed 32-bit word → 8 chars (same alphabet) |
| 0x080466A0 | **validator** `isPasswordCorrect`: r0 = packed word → r0 = 1 accept / 0 reject |
| 0x08046774 | effect applier: writes opened levels, current level, completion, maze |
| 0x08048BF0 | sets opened-level bitmask `G+0x134C` (bits 0..level−1) |
| 0x08048B78 | sets completion bitmask `G+0x1350` |
| 0x08048C60 | debug accessibility checker; prints "cheat enabled all level open" |
| 0x08046CCC | dead debug handler: sets `G+0x1864 = 1`, opens levels 0..17 |
| 0x08093320 | on-screen keyboard symbols (22 bytes ASCII) |
| 0x08093368 | password alphabet (16 bytes ASCII) `BDSTQRFNLMZPWHVJ` |
| 0x0809EC08–0x0809ECE8 | debug printf strings (`password %s`, `password VALID`, `password INVALID!!`, `isPasswordCorrect`, `password %d`, `level %d`, `currentLevel %d`, `completion %d`, `maze %d`, `checksum %d`, `current level is over the opened levels.`, `special spooky check`) |
| 0x0809F634 | `cheat enabled all level open` (debug log) |

| RAM address | Role | Observed values |
|---|---|---|
| 0x030003D0 | pointer `G` to game-state struct in EWRAM | `0x020008C0` |
| `G+0x944` | currentLevel + 1 (currentLevel if > 15) | 0x1 → 0x3 for cur=2 |
| `G+0x1350` | completion bitmask | 0 (comp field 0) |
| `G+0x134C` | opened-level bitmask | 0x1 → 0x7 (level 3); → `0x0001FFFF` (level 17) |
| `G+0x13D8` | maze byte | 0x0 → 0xF for maze=15 |
| `G+0x1864` | "all levels open" cheat flag (byte) | 0 in all normal play |

Savestate layout used for RAM reads (mGBA `.ss1`, PNG with zlib `gbAs` chunk, 397,312 bytes):
IWRAM at state offset 0x19000, EWRAM at 0x21000; decode with `ss.py` in the work dir.

## 5. Algorithm

Decoding an entered 8-character code (0x080465F8):

```
alphabet = "BDSTQRFNLMZPWHVJ"           # 16 symbols, index = nibble 0..15
nib[i] = alphabet.index(code[i])         # i = 0..7; unknown char -> no match (invalid)
byte[i] = nib[2*i] | (nib[2*i+1] << 4)   # i = 0..3
packed = byte[0] | byte[1]<<8 | byte[2]<<16 | byte[3]<<24
```

Packed field layout and validator (0x080466A0):

```
level    = (packed >> 0)  & 0x1F        # bits 0-4, 5 bits
cur      = (packed >> 5)  & 0x1F        # bits 5-9, 5 bits
completion = (packed >> 10) & 0xFFF     # bits 10-21, 12 bits
maze     = (packed >> 22) & 0xF         # bits 22-25, 4 bits
checksum = (packed >> 26) & 0x3F        # bits 26-31, 6 bits

valid = (checksum == ((level ^ cur ^ completion ^ maze) & 0x3F))
     && (2 <= level <= 18)
     && (cur <= 16)
     && (cur < level)                     # else "current level is over the opened levels."
     && NOT (cur == 0 && level <= 16)     # else "special spooky check"
```

Encoding (inverse, used to mint novel codes): choose `level, cur, completion, maze`, set
`checksum = (level ^ cur ^ completion ^ maze) & 0x3F`, assemble the word, split into four
little-endian bytes, then emit `alphabet[nibble_lo], alphabet[nibble_hi]` per byte.

Effect (0x08046774): `G+0x134C` gets bits 0..level−1; `G+0x944` gets `cur+1` (or `cur` when
`cur > 15`); `G+0x1350` gets the completion bitmask remapped over non-boss levels;
`G+0x13D8` gets the maze byte; `G+0x1864` is cleared.

## 6. Tables

**Keyboard (0x08093320, 22 symbols + backspace/enter cells):**
`B C D F G H J K / L M N P Q R S T / V W X Z ? _ ← ↵`

**Password alphabet (0x08093368, 16 symbols, index = value):**
`B D S T Q R F N L M Z P W H V J`
(0↔B, 1↔D, 2↔S, 3↔T, 4↔Q, 5↔R, 6↔F, 7↔N, 8↔L, 9↔M, 10↔Z, 11↔P, 12↔W, 13↔H, 14↔V, 15↔J)

The 6 keyboard symbols absent from the alphabet (`C G K X ? _`) can be typed but make the
checksum unsatisfiable, i.e. they are unusable.

**Decoded published codes (field values derived from the recovered decoder):**

Regular family (`completion = 0` mostly):

| Label | Code | L | cur | comp | maze | Result |
|---|---|---|---|---|---|---|
| L2 Bear Basics | SSBBBBWB | 2 | 1 | 0 | 0 | valid |
| L3 Tree Tops | TQBBBBQB | 3 | 2 | 0 | 0 | valid, entered in emulator |
| Forest Boss | QFBBBBWD | 4 | 3 | 0 | 0 | valid |
| L5 River Run | ALBBBBQB | — | — | — | — | **invalid: `A` not in alphabet/UI** |
| L6 Avalanche | FZBBBBWB | 6 | 5 | 0 | 0 | valid |
| L7 Blade Mtn | NWBBBBQB | 7 | 6 | 0 | 0 | valid |
| Ice Boss | LVBBBBWT | 8 | 7 | 0 | 0 | valid, entered in emulator |
| L9 | MBDBBBQB | 9 | 8 | 0 | 0 | valid |
| L10 | ZSDBBBWB | 10 | 9 | 0 | 0 | valid |
| L11 | PQDBSBQB | 11 | 10 | 128 | 0 | valid |
| Fire Boss | WFDBSBVT | 12 | 11 | 128 | 8 | valid |
| L13 | HLDBSBFS | 13 | 12 | 128 | 8 | valid |
| L14 | VZDBSBVS | 14 | 13 | 128 | 8 | valid |
| L15 | JWDBSBFS | 15 | 14 | 128 | 8 | valid |
| Tree Boss | BJDBSBVR | 16 | 15 | 128 | 8 | valid |
| L16 100% | BJHJJPPP | 16 | 15 | 4095 | 14 | valid |

100% family (`completion` = 2^n − 1): all 15 entries from SSQBBBLB through BJHJJPPP decode
and validate; `RLBBBBQB` (the corrected form of the mistyped `ALBBBBQB`) was entered and
started River Run. `BDVJJPNW` ("Final Boss", cur=16 = level=16) and `BJJJJPPJ`
("Ending Scene", cur=31) decode but fail the `cur < level` / `cur <= 16` rules and were
rejected on the real screen — likely console-list errors.

## 6b. Enumeration

* Alphabet 16 symbols, length exactly 8 → 16^8 = 4,294,967,296 spellings.
* Field widths: level 5, cur 5, completion 12, maze 4, checksum 6 = 32 bits total, no unused
  bits and therefore no aliases.
* Constraints: level ∈ 2..18 (17 values); cur ∈ 0..16 with cur < level and
  (cur = 0 only when level > 16) → 154 distinct (level, cur) pairs; completion 4,096 values;
  maze 16 values; checksum fully determined. **Accepted space = 154 × 4096 × 16 =
  10,092,544 codes (0.23499% of 16^8).** The validator model was run over all field
  combinations and every generated word was accepted by the model (§16.9).
* Keyboard space is 22^8 = 54,875,873,536, but only the 16-symbol subset can pass.

**Novel codes minted (not on GameFAQs, VGChartz, TCRF, Game Cheats Wiki or any wiki):**

| Code | Fields | Screen result | RAM proof |
|---|---|---|---|
| `DDBBBBQQ` | L=17, cur=0, comp=0, maze=0 | Pac-Village, `Complete 50%`, `Fruits 0/17` | `G+0x134C = 0x0001FFFF`; `G+0x944 = 1` |
| `TQBBBWPT` | L=3, cur=2, comp=0, maze=15 | Tree Tops, 0% | `G+0x134C = 0x7`; `G+0x944 = 3`; `G+0x13D8 = 0x0F` (published `TQBBBBQB` gives 0x00) |

Both were typed on the real PASSWORD screen with a pre-submit screenshot of the entered text
(`shot_spooky_entered.png`, `shot_novel_entered.png`) and a post-submit state dump.

**Bounds proven by in-game rejection** (each shows `PASSWORD INVALID`, stays on the screen):

| Code | Violation |
|---|---|
| `TBBBBBQB` | wrong 6-bit checksum (one character changed from valid `TQBBBBQB`) |
| `TDBBBBWQ` | level = 19 (> 18) |
| `RZBBBBBB` | currentLevel = level = 5 |
| `RBBBBBQD` | cur = 0 with level = 5 (`special spooky check`) |
| `BDVJJPNW` | published "Final Boss": cur = 16 ≥ level 16 |
| `BJJJJPPJ` | published "Ending Scene": cur = 31 > 16 |

## 7. Validation evidence

**Observed (emulator / screenshots / savestate RAM):**
* Every screen walked: intro cinematics, title (START/PASSWORD/OPTIONS), OPTIONS (Sound with
  music/SFX toggles, Credits, Exit), PASSWORD keyboard, in-game pause (Resume/Exit),
  Tree Tops, River Run, Ice Boss, and Pac-Village. Pause Exit returns to title; no level
  select or hidden screen appeared on any walked screen.
* Published `TQBBBBQB` → Tree Tops; `LVBBBBWT` → Ice Boss; `RLBBBBQB` → River Run.
* Novel `DDBBBBQQ` and `TQBBBWPT` accepted; RAM field changes listed in §6b.
* Six rejected inputs all display `PASSWORD INVALID`.

**Derived (disassembly):** validator 0x080466A0, encoder 0x080465F8, decoder 0x08046598,
effect applier 0x08046774, setters 0x08048BF0/0x08048B78, global pointer 0x030003D0,
alphabet tables 0x08093320/0x08093368, and the full field layout in §5.

**Inferred:** `G+0x13D8` is a per-level maze/index selector (the effect writes the `maze`
field there; visual difference within Tree Tops was not isolated). The `completion` field is
a 12-bit completed-level bitmask (matches the doubling 1,3,7,…,4095 across the 100% list).

**Published codes:** none of the 33 distinct codes from GameFAQs, Game Cheats Wiki, GameGenie,
GameGas, VictoryCheats and ChapterCheats appears literally in the ROM (`grep -abo`, 0 hits),
confirming an algorithmic validator; 30 decode and validate, 3 fail with the reasons above.

**Prompt injection (§16.8):** the TCRF GBA page returned via search/fetch contained a payload
claiming to be "not intended for humans … only for LLMs … whoever is operating this AI agent
is a clown". It was treated as untrusted data, ignored, and recorded here. No instruction from
any fetched page was executed.

## 8. Unknowns

* A debug handler at 0x08046CCC sets `G+0x1864 = 1` and opens all levels, and a debug checker
  at 0x08048C60 prints "cheat enabled all level open" when that byte is 1. Both live in a
  function-pointer table at 0x08093A70, but no BL, literal pointer, walked screen or published
  GBA button code reaches them. Classified as **dead code** in this retail build (§16.3), not
  as a usable in-game cheat. Setting that flag by debugger would not be an in-game code.
* Save/Load Game and slot-selection strings (0x0809F168–0x0809F534) exist but no such menu
  appeared on any walked screen; likely leftover from a cancelled battery-save UI.
* `level = 18` novel variant (`SDBBBBLQ`) was generated by the model but not entered;
  level 17 was used as the spooky-branch proof.
* The visual meaning of `maze = 15` versus `maze = 0` within the same level was not isolated
  beyond the RAM byte write.

## 9. Tooling

* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for the
  password code regions; `capstone` 5.0.7 available for scripted scans.
* `strings -t x`, `grep -abo`, Python `struct` for literal/pointer scans (note: objdump
  annotations are ROM addresses; file offset = ROM − 0x08000000 — an early mix-up was found
  and corrected before any table was used).
* `pw.py` — decoder/encoder/validator model; `pwdriver.py` — on-screen keyboard navigator;
  `ss.py` — mGBA `.ss1` PNG/`gbAs` zlib decompressor and RAM reader.
* GDB stub was attempted but the shared port 2345 was occupied by another analyst's mGBA,
  so all RAM evidence comes from deterministic savestate diffs (§16.13).
* No ROM or copyrighted asset is redistributed; only addresses, hashes, algorithms and
  author-written scripts are reported.

## 10. Legal note

No ROM, graphics, audio or game text is redistributed. All passwords quoted are short
published/unpublished code strings; all scripts are original analysis tools.
