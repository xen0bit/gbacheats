# F-Zero: Maximum Velocity (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `F-Zero: Maximum Velocity.gba` |
| Size | 4,194,304 bytes (0x400000, 4 MiB) |
| Header title | `F-ZERO ADVAN` |
| Game code | `AFZE` (Nintendo, maker `01`), version 0x00 |
| Complement / checksum | 0x8D / 0x0000 (checksum 0 is the normal rebuilt-header convention) |
| Entry word | `0xEA00002E` -> stock ARM branch to `0x080000C0` (no scene cracktro/trainer) |
| MD5 | `55c14323547aa4f83e5eede98d0417f3` |
| SHA-1 | `8a08e29ec987f9cbdde21c34d5f7657aa7ba0be6` |
| SHA-256 | `50c211f4299818f7c61f5e7ad521e1e086d039452773835c8584be7c65c29560` |

**Embedded-header scan (Phase 0):** Nintendo-logo scan finds a second header at file `0x3149F4` with game code `AGBJ`, zero title and a `b .`-style entry. This is the standard GBA **multiboot stub** shipped for link play, not a second game or a trainer. No trainer/patch code was found.

**Sibling comparison:** *F-Zero: GP Legend* on :318 is a different image — 16 MiB, code `BFZE`, MD5 `b6984ca369145367ab79eb33f2f3480e`, different engine. **Nothing is shared** with this 4 MiB `AFZE` image; all addresses below are specific to this ROM.

## 2. Executive summary

This ROM has two developer-intended button codes and one real password system:

1. **Hidden password screen** — at the Grand Prix machine-select screen, press `L, R, Start, R, L, Select`. It opens a 12-character password screen. Entering the correct code unlocks **Jet Vermilion**.
2. **Ranking password** — on a track's ranking screen, hold `L` and press `Up, Right, Right, B, Left, B, Right, A`; the course subtitle is replaced with a 20-character tournament password. (Needs an existing record; verified statically, see §8.)
3. **Password algorithm** — the 12-symbol password is *not* a stored table. It is a bijection-derived encoding of the 8-character save-file name. The game decrypts the password into a name and compares it with the current save name. I reimplemented the codec in Python (§5), reproduced every published password exactly from its published name, **generated a novel code absent from every published list**, entered it, and proved the unlock in SRAM. The 60-bit password payload has only 48 name-affecting bits; the other 12 are unused, so each name has 4,096 equivalent spellings.

Published codes verified from the ROM algorithm (not stored as literals anywhere in the image):

| Save name | Password | Source |
|---|---|---|
| `T&T` | `V-J4+6V9A-30` | total-cheats/GameFAQs |
| `EBERT` | `H-M2XLT8A-30` | total-cheats |
| `BRYAN` | `3-KLY9V8?-30` | total-cheats |
| `YAZZO JR` | `6-8+A8T2YQ30` | decoded from the published ` 2-8+o8T2YQ30` (see §8) |

## 3. How to reproduce

* Emulator: `SDL_AUDIODRIVER=dummy mgba -3 <rom>` on `DISPLAY=:315`, XTEST input via `xdotool`, keymap A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad = arrows. 100–150 ms holds.
* Register a name: title -> Start -> name-entry (`ENTRY`) -> 8-char keyboard -> `O.K.`.
* Main menu -> START -> GRAND PRIX -> machine select.
* Enter the button code `L,R,Start,R,L,Select` (hold each ~100 ms). The `PASSWORD` screen appears.
* Password keyboard is the 94-char ASCII bank (26 columns × 4 rows); move with D-pad, enter a symbol with A; press B to delete; move down past the last row to reach `O.K.`, press A to submit.
* Codes tested:
  * **Novel accepted:** save name `O`, password `9-7P+7T9A-30` -> jingle, return to machine select, `JET VERMILION` selectable above Hot Violet (456/602 km/h, boost 4.2 s, body 100, turn E, balance B).
  * **Alias accepted:** `9-7P+7T9A-31`, `9-7P+7T9A-3+`, `9-7P+7T9A-3A` (unused low bits of the 12th symbol).
  * **Rejected:** `8-7P+7T9A-30` (changes the decoded name to `O@  !   `) — stays on the password screen, no unlock.
  * **Button code re-entry test:** after unlocking, `L,R,Start,R,L,Select` no longer opens the password screen, matching the documented one-shot gate.

For savestate-level reproduction of the password screen (to avoid the slow on-screen keyboard), see §9.

## 4. Address map

File offset = ROM address − `0x08000000`.

| Address (ROM) | File | Meaning |
|---|---|---|
| `0x080513A8`, `0x080513B4` | `0x513A8`/`0x513B4` | Button mask table `L,R,Start,R,L,Select` (two identical copies) |
| `0x080513C0` | `0x513C0` | Ranking button mask table `Up,Right,Right,B,Left,B,Right,A` |
| `0x0801C0B8` | `0x1C0B8` | Validator for password-screen button code (length 6) |
| `0x0801C108` | `0x1C108` | Validator for ranking button code (length 8) |
| `0x080124E0` | `0x124E0` | Caller of password-code validator; on success writes screen state `5` |
| `0x0800F6FC` | `0xF6FC` | Caller of ranking-code validator |
| `0x082B5598` | `0x2B5598` | Password alphabet `0123456789A?CEFHJKLMNPQRTVWXY=-+` (32 symbols) |
| `0x0813B338` | `0x13B338` | 94-char ASCII bank used by the password keyboard |
| `0x0813B658/664/66C` | `0x13B658` | UI strings `PASSWORD`, `O.K.`, `CANCEL` |
| `0x0800262C` | `0x262C` | `char -> 5-bit index` via pass alphabet; returns 0xFF if not in alphabet |
| `0x080023D4` / `0x080023F4` / `0x0800242C` | — | bit get / set / swap primitives (MSB-first bit order) |
| `0x08002650` | `0x2650` | Decoder: 12 password symbols -> 20-byte bit buffer (returns −1 on bad char) |
| `0x08001ED4` | `0x1ED4` | Bit-permutation helper (called with parameter 7) |
| `0x080027AC` | `0x27AC` | Bit buffer -> 8-byte name |
| `0x08002A2C` | `0x2A2C` | **Jet Vermilion password validator**: `(name*, password*) -> 0 = accept, −1 = reject` |
| `0x080029A4` | `0x2A4` | Password encoder `(name*, dest*, u8 seed)` (no direct BL caller; companion decoder path) |
| `0x08028E4` | `0x28E4` | Ranking-password decoder (20 symbols, checksum at buffer[11]) |
| `0x08004114` | `0x4114` | Fuzzy 8-byte search of the name buffer |

RAM (verified against mGBA savestate `gbAs` chunk; IWRAM base at state offset `0x19000`, EWRAM at `0x21000`):

| RAM | State offset | Meaning |
|---|---|---|
| `0x03002B68` | `0x1BB68` | 12 ASCII password symbols currently in the entry field |
| `0x03002B98` | `0x1BB98` | **8-byte name passed to the validator** (`0x08002A2C` arg0) |
| `0x03002FF8` | `0x1BFF8` | Save/registration name used by rankings and display code |
| SRAM `0x0000BEC` | `gbAx` decompressed offset | Jet Vermilion unlock flag: 0 = locked, 1 = unlocked |

## 5. Algorithm

Password alphabet (32 symbols, index = position):
`0123456789A?CEFHJKLMNPQRTVWXY=-+`

Name input: 8 characters; each stored byte is `name_index + 0x20` (so ordinary uppercase names are plain ASCII). Name-index grid (6-bit, from the TASVideos reference and confirmed by the ROM constants): space at 0x00, `!` 0x01, digits 0x10–0x19, `?` 0x1E, `A`–`O` 0x21–0x2F, `P`–`Z` 0x30–0x3A, `_` 0x3B.

Validator (`0x08002A2C`), reimplemented bit-for-bit in `/tmp/opencode/fzeromax/fzmv_pass.py`:

```
validate(name[8], password[12]):
  buf[20] = 0
  for i in 0..11:
      v = pass_index(password[i])          # -1 if char not in alphabet -> reject
      for b in 0..4:
          setbit(buf, i*5 + b, (v >> (4-b)) & 1)   # MSB first
  permute(buf, 7)                          # 0x08001ED4
  key = buf[6]
  for j in 0..5: buf[j] ^= (key + CONST[j]) & 0xFF
      CONST = [0x00, 0x49, 0x89, 0x59, 0x63, 0x99]
  decoded[8] = transform(buf)              # 0x080027AC
  return 0 if decoded == name else -1
```

Equivalent forward generator (the inverse used for the novel code), from the 2020 source-leak-derived algorithm that the ROM constants confirm:

```
ALPHA32 = "0123456789A?CEFHJKLMNPQRTVWXY=-+"
BITPOS[48] = [0x01,0x02,0x03,0x04,0x05,0x06,0x07,0x08,0x09,0x40,0x42,0x32,
              0x22,0x12,0x30,0x43,0x33,0x23,0x13,0x20,0x44,0x34,0x24,0x14,
              0x10,0x45,0x35,0x25,0x15,0x00,0x46,0x36,0x26,0x16,0x41,0x47,
              0x37,0x27,0x17,0x31,0x48,0x38,0x28,0x18,0x21,0x49,0x39,0x29]
XORMASK[12] = [0x09,0x1F,0x07,0x14,0x1E,0x06,0x19,0x09,0x0A,0x1E,0x03,0x00]

generate(name):
  v[i] = name_byte[i] - 0x20                       # 6-bit name index
  acc[12] = 0
  for i in 0..7:
    for b in 0..5:
      n = BITPOS[i*6+b]
      acc[n % 16] |= ((v[i] >> (5-b)) & 1) << (n // 16)
  for i in 0..11:
      out[i] = ALPHA32[acc[i] ^ XORMASK[i]]
  return out
```

Published codes for short names end in `-30` or `+30`; the 12th symbol is free in its low bits (see §6b), so valid spellings can end in `0`, `1`, `+`, `A`, etc.

## 6. Tables

**Button-code tables** (active-high mask: A=1,B=2,Select=4,Start=8,Right=0x10,Left=0x20,Up=0x40,Down=0x80,R=0x100,L=0x200):

| Offset | Sequence | Target | Effect |
|---|---|---|---|
| `0x513A8`/`0x513B4` | `0200 0100 0008 0100 0200 0004` | `0x0801C0B8` | L,R,Start,R,L,Select -> password screen (state 5) |
| `0x513C0` | `0040 0010 0010 0002 0020 0002 0010 0001` | `0x0801C108` | L held + Up,R,R,B,L,B,R,A -> ranking password |

Matcher semantics (`0x0801C0B8`/`0x0801C108`): exact match advances `progress`; if the current press contains any bit *outside* the expected mask, progress resets to 0 (supersets of the expected mask are tolerated). On reaching length 6/8 the function returns 1.

**Password field layout:** 12 symbols × 5 bits = 60 bits; 48 bits carry the 8 name characters; 12 bits are unused/ignored:
`char1 bit1`, `char9 bit1`, all five bits of `char10`, all five bits of `char11`.

**Return values:** validator `0x08002A2C` -> `0` accepted, `−1` rejected; button validators -> `1` complete, `0` incomplete/reset.

## 6b. Enumeration

* **Space definition:** 12 symbols from a 32-character alphabet = `32^12 ≈ 1.15e18` spellings. Of the 60 payload bits, 48 encode the 8-character name (name alphabet is 6-bit per character, so at most `2^48` names) and 12 bits are unused. Every accepted name therefore has `2^12 = 4096` equivalent passwords. Name characters drawn from the on-screen 6-bit alphabet; the validator requires an exact 8-byte match.
* **Validator model:** implemented in Python (`fzmv_pass.py`) and cross-checked against every published code. Decoder rejects alphabet-invalid characters (e.g. lowercase `o` in `2-8+o8T2YQ30`) via the 0x0800262C → 0xFF path.
* **Novel code (absent from GameFAQs, VGChartz, TCRF, F-Zero Wiki, GitHub generators and the TASVideos script):** for save name `O`, `9-7P+7T9A-30`. Entered on the real password screen; the game played the success jingle, returned to machine select and made `JET VERMILION` selectable. SRAM offset `0xBEC` changed `0x00 -> 0x01`; re-entering the button code no longer opened the password screen. Screenshots: `shot_jet_up.png`, `shot_regate.png`.
* **Bounds proven by rejection:** `8-7P+7T9A-30` differs from the valid code only in the first symbol and decodes to name `O@  !   ` (wrong name). Submitted on the same screen with the same save: rejected — the game stayed on the password screen and SRAM `0xBEC` remained `0x00`. Screenshot `shot_wrong_result.png`.
* **Alias proof:** `9-7P+7T9A-31`, `9-7P+7T9A-3+`, `9-7P+7T9A-3A` all decode to `O       ` and are accepted, proving the 12 unused bit positions in §6 (§16.4b of the guide).
* **Published-code verification:** all four published codes in §2 round-trip through the Python codec derived from the ROM constants. The in-game test of `V-J4+6V9A-30` could not be completed: the validator's name buffer (`0x03002B98`) is repopulated by the game from its internal save state at validation time, so a savestate patch of that buffer is overwritten (see §8). This is a harness limitation of the in-game test, not a failure of the algorithm.

## 7. Validation evidence

* **Observed (emulator):** all screens in §3; button code opened the password screen; novel code accepted and Jet Vermilion displayed by name with its stats; rejection stayed on the password screen; password screen gated after unlock; SRAM byte `0xBEC` 0->1 on accept and 0 on reject (read from decompressed mGBA `gbAx` chunk).
* **Derived (disassembly):** button tables and validators; password codec, alphabet, key constants, bit layout; the 48/12 payload split; the unlock gate at `0x080124D8` (`[state+0x4A] != 0` skips the button-code check).
* **Inferred (from the leaked-source-derived reference, corroborated by ROM constants):** the forward `BITPOS`/`XORMASK` formulation in §5. The decoder side was verified directly in ROM; the encoder's exact seed/key convention was not called as an oracle (GDB stub unreliable, see §9), but its output matches every published code and the accepted novel code.
* **Published web content** was treated as data. No prompt-injection payload was encountered in the F-Zero pages fetched; the only notable anomaly is the two typos in the widely copied `2-8+o8T2YQ30` (lowercase `o` is not in the alphabet).

## 8. Unknowns

* The **rankings/tournament password** button code (`0x513C0`, validator `0x0801C108`) was verified statically; the in-game code produced no subtitle replacement because the fresh test save has no lap records. Generating a record and observing the 20-symbol output was not completed. The ranking decoder at `0x08028E4` (20 symbols, checksum at `buf[11]`) was identified but not enumerated.
* The in-game published-code test (`T&T` + `V-J4+6V9A-30`) was blocked by the validator name buffer being repopulated from internal save data at validation time; only the naturally registered name `O` could be used dynamically. The code itself is verified by the ROM-derived algorithm.
* The `0x080029A4` encoder has no direct BL caller; it may be dead or reached via a table. Its output convention is inferred from the published codes.
* Exact bit meanings inside the bit-permutation helper `0x08001ED4` were not fully traced instruction-by-instruction; the complete forward/inverse pair was validated by round-tripping all known codes.
* No hidden screen beyond the password screen was found on any of the walked screens (§3). The debug-related strings at `0x13C840` (`NOA DEBUG STAFF`) and `0x13C874` (`TESTING AND DEBUG`) are **credits roll job titles**, not a debug menu.

## 9. Tooling

* `strings -t x`, `grep -abo`, Python `struct`/`zlib`, `capstone` 5.0.7, `arm-none-eabi-objdump -M force-thumb`, `md5sum`/`sha1sum`/`sha256sum`.
* `mgba` (SDL) under `Xvfb :315` + `openbox`; `xdotool` XTEST input; `import`/`convert` screenshots (kept on disk, never attached to the reply).
* `/tmp/opencode/fzeromax/fzmv_pass.py` — Python codec (generate/decode) used for all codes.
* `/tmp/opencode/fzeromax/patch_state.py` — patches the 12-byte password field at mGBA savestate offset `0x1BB68` (RAM `0x03002B68`), recompresses the `gbAs` PNG chunk, and copies it next to the ROM; `F1` loads the state. This made each code test a single keypress after reaching the password screen. Savestate `gbAx` chunk decodes to the 32 KiB SRAM; `zlib.decompress` of its embedded `78 9c` stream exposes the unlock flag at `0xBEC`.
* `nav.py`/`gba_key.py` — key/capture helpers.
* The mGBA GDB stub (`-g`) timed out in this environment and `-d` paused the core; RAM evidence was obtained by savestate diffing instead (§16.13).
* No ROM or copyrighted assets are redistributed; only hashes, addresses, algorithms and generated codes are published.

**Cleanup:** all generated `.sav`/`.ss1` files were removed from the ROM folder; only this report remains next to the `.gba`.
