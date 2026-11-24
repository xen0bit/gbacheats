# Yu-Gi-Oh! Worldwide Edition: Stairway to the Destined Duel (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Yu-Gi-Oh! Worldwide Edition: Stairway to the Destined Duel.gba` |
| Size | 16,777,216 bytes (0x01000000 / 128 Mbit) |
| Header title (0xA0) | `YUGIOHWWE` |
| Game code (0xAC) | `AYWE` |
| Maker (0xB0) | `A4` (Konami) |
| Version (0xBC) | 0x00 |
| Header checksum (0xBE) | 0x0000; complement byte (0xBD) = 0xDE |
| Entry word | `0xEA00002E` → stock crt0 at 0x080000C0 |
| CRC32 | `39B5E771` — matches Data Crystal's **USA** revision (AYWE); JP `A7054D60`, EU `ACA6FFC6` differ |
| MD5 | `1e52d66f5f8a7c4f207d80ba4fccf55e` |
| SHA-1 | `53d4ae06d1b605f8925c53d6c585478d73ff55c0` |
| SHA-256 | `c4c3ef5c8980996be049a3b6efd1c99b165e565405e040ea428801a14b8c8aa9` |

The 156-byte Nintendo logo at file offset 0x04 is nonstandard (patched dump), but the crt0 at 0x080000C0 disassembles as clean stock ARM code and the image boots normally in mGBA 0.10.5. All analysis was done on a byte-identical copy in `/tmp/worldwide/game.gba`; the ROM folder was left untouched.

## 2. Executive summary

The only in-game cheat surface is the **8-digit card Password** system (`PASS WORD` under `MISC`), which the game implements as a **fixed lookup table**, not a checksum algorithm. Entering a code converts the eight digits to four packed BCD bytes and linearly searches a 1087-entry table at ROM `0x0834500`; a hit returns the table index, which the caller uses to add that card to the player's Trunk.

The table contains **1026 real passwords**, **60 `FF FF FF FF` no-password entries**, and one unused all-zero sentinel at index 0. The 1026 passwords are **exactly** the 1026 codes on the published fan list (verified as a set-equality test); there is no algorithmic generator, no hidden debug password, and no second code format. The accepted set is therefore a provably closed set of 1026 codes out of 100,000,000 possible eight-digit inputs.

Every published "cheat" for this title (24 entries in libretro/GameFAQs/GameHacking.org) is a **CodeBreaker / GameShark / AR RAM-patch code** for a cheats device, explicitly out of scope. No in-game button code or debug menu was found (bounded search recorded in §6b).

Two accepted codes were confirmed on the real screen with the awarded card rendered: `11714098` → *30,000-Year White Turtle*, `89631139` → *Blue-Eyes White Dragon*. Three rejected inputs establish bounds: `12345678`, `00000000` (the ROM sentinel), and `49587386` (a GameFAQs typo for `49587396`).

## 3. How to reproduce

**Emulator**: mGBA 0.10.5, `SDL_AUDIODRIVER=dummy`, Xvfb `:317`, openbox, `mgba -3`. Game is 3× scaled (720×480 window with 240×160 viewport at +154,+184 in a 1024×768 root).

**Keymap** (mGBA SDL defaults): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrow keys. Use ~70–150 ms holds; shorter taps are dropped. `windowactivate --sync` is required (plain `windowfocus` fails under openbox).

**Menu path to the password screen**:
1. Title → `Continue` (or play through New Game); this lands on the Battle City map.
2. Press **R** → sub-menu (`DECK & TRUNK`, `MISC`, `LINK DUEL`, `OPTION`).
3. Right → `MISC` → **A** → `TRADE`, `PASS WORD`.
4. Right → `PASS WORD` → **A**.

**Password keypad** (displayed on screen):

```
7 8 9        <- row 0
4 5 6        <- row 1
1 2 3        <- row 2
0   GET CARD <- row 3
```

Cursor starts on `0`. Move with the D-pad, press **A** to enter a digit. After the **8th** digit the keypad cursor automatically moves to `GET CARD`; pressing **A** again submits. (The orange "last key" highlight can linger on a number key — the authoritative state is the control byte in §4.)

**Savestate workflow**: Shift+F2 saves slot 2 (clean password screen), F2 reloads it; Shift+F3/F5 save states with a code entered. Each test therefore costs two keypresses rather than a menu replay.

**Codes tested**:

| Code | Result |
|---|---|
| `11714098` | Accepted — *30,000-Year White Turtle* card rendered |
| `89631139` | Accepted — *Blue-Eyes White Dragon* card rendered |
| `12345678` | Rejected — display cleared, right panel empty |
| `00000000` | Rejected — display cleared, right panel empty |
| `49587386` | Rejected (GameFAQs typo) — display cleared, right panel empty |

## 4. Address map

All addresses are GBA bus addresses; file offset = address − `0x08000000`.

| Address | File offset | Meaning |
|---|---|---|
| `0x080000C0` | `0x0000C0` | Stock ARM crt0 entry |
| `0x08091364` | `0x091364` | **Password validator** (`push {r4,r5,lr}`) |
| `0x080913B8` | `0x0913B8` | Literal `0x0201F8B0` (input buffer) |
| `0x080913BC` | `0x0913BC` | Literal `0x0834500` (password table base) |
| `0x080913D4` | `0x0913D4` | Literal `0x43E` = 1086 (loop bound) |
| `0x08091534` | `0x091534` | Password screen main handler |
| `0x080916AE` | `0x0916AE` | Digit insertion / GET CARD dispatch |
| `0x08091738` | `0x091738` | GET CARD branch: memcpy + validator call |
| `0x08088C74` | `0x088C74` | `memcpy` used to copy 8 digits to `buffer+8` |
| `0x081763BC` | `0x1763BC` | Keypad cursor table (11 × 8 bytes, indices 0–10 = keys `0`..`9`,`GET CARD`) |
| `0x0834500` | `0x834500` | **Password table**, 1087 × 4 bytes, ends `0x08355FC` |
| `0x0201F8B0` | — | 8 input digit bytes (values 0–9), EWRAM |
| `0x0201F8B8` | — | 8-byte copy read by the validator |
| `0x0201F8C0` | — | Control byte: bits 7:4 = keypad button index (0–9 digit, 10 = GET CARD), bits 3:0 = display cursor (0–7) |
| `0x0201F8C2` | — | 16-bit validator result written by the caller |

**Savestate RAM mapping** (mGBA `.ss*` PNG with zlib `gbAs` chunk, raw length 397,312): raw `0x408B0` = EWRAM `0x0201F8B0`; raw `0x408C0` = `0x0201F8C0`. (Consistent with guide §16.13: EWRAM starts at raw `0x21000`.)

Card-name strings are ASCII at `0x385564` onward, 0x40-byte stride, in the game's internal (Japanese-name-derived) order — *not* the alphabetical order of published lists. Password UI labels (`PASS WORD`, `GET CARD`) do **not** exist as ASCII anywhere in the ROM; they are drawn from a font/tile bank (guide §11), which is why the initial `strings` recon found no password label.

## 5. Algorithm

**Digit packing** (validator `0x08091364`): for `i = 0..3`, `packed[i] = (digit[2i] << 4) | digit[2i+1]`, stored as four bytes on the stack. This is ordinary packed BCD, big-nibble-first, e.g. `11714098` → `11 71 40 98`.

**Validation** (pseudocode, exact):

```c
// r0 ignored; function loads its own pointer
uint8_t *src = (uint8_t*)0x0201F8B8;   // caller memcpy'd 8 digits here
uint8_t packed[4];
for (i = 0; i < 4; i++) packed[i] = (src[2*i] << 4) | src[2*i+1];

for (i = 0; i <= 1086; i++) {
    uint8_t *row = (uint8_t*)0x0834500 + 4*i;
    if (row[0]==packed[0] && row[1]==packed[1] &&
        row[2]==packed[2] && row[3]==packed[3])
        return (uint16_t)i;            // hit
}
return 0;                               // not found
```

Properties: no checksum, no arithmetic transform, no XOR key, no permutation. Comparison is byte-exact, so any input outside the table is rejected. Index 0 (`00000000`) and "not found" both return 0; every real password lives at index ≥ 1, so a 0 result is treated as failure by the caller.

**Input handler** (`0x080916AE`): `c = *(uint8_t*)0x0201F8C0`, `button = c >> 4`, `cursor = c & 15`. If `button <= 9`, write `button` to `0x0201F8B0 + cursor` and advance the display cursor; if `button > 9` (i.e. 10 = GET CARD), jump to `0x08091738`, which calls `memcpy(0x0201F8B8, 0x0201F8B0, 8)` then the validator and stores the returned index at `0x0201F8C2`. D-pad movement uses the 8-byte-per-entry cursor table at `0x081763BC`; entry 10 has x=44,y=100 (the GET CARD button).

## 6. Tables

| Item | Value |
|---|---|
| Accepted format | exactly 8 decimal digits, 0–9, packed BCD into 4 bytes |
| Alphabet | `0123456789` (on-screen keypad only; no letters/symbols) |
| Entry width | 4 bytes = 8 BCD digits; stride 4, no terminator |
| Table entries | 1087 (indices 0–1086 inclusive, bound literal `0x43E`) |
| Table size | 0x10FC bytes (`0x0834500`–`0x08355FC`) |
| Index 0 | `00 00 00 00`, unused sentinel — entering `00000000` is rejected |
| `FF FF FF FF` entries | 60 (56 passwordless cards + 4 tokens, per published FAQ and Yugipedia) |
| Real passwords | 1026 |
| Return value | table index (1–1086) on hit, 0 on miss |

Published-list discrepancy: GameFAQs lists *Ancient Tool* as `49587386`; the ROM table (index 5) stores **`49587396`**, which is what yugioh-world.com lists. Entering `49587386` is rejected — a verified typo in the GameFAQs guide, not a second code.

## 6b. Enumeration

**Space definition**: 8 positions × 10 digits = **10^8 = 100,000,000** possible inputs. The validator packs them into 32 bits and compares against a fixed 1087-row table, so the representable accepted space is at most 1087 values; after removing the 60 `FF` rows and the zero sentinel, it is exactly **1026** values (0.001026 % of all inputs).

**Closed-set proof** (not merely a table dump — the whole table was enumerated and compared):

1. Decoded all 1087 table rows from `0x0834500` into 8-digit strings.
2. Fetched the full published password list (yugioh-world.com, 1026 codes, matching the GameFAQs FAQ count) and extracted every 8-digit number: **1026 codes**.
3. Set comparison: `ROM passwords − published = ∅` and `published − ROM = ∅`. The ROM's only extra decoded strings are `00000000` (unused sentinel) and `15`×8 (the `FF FF FF FF` no-password marker, not a keypad-reachable code). **There is no code absent from every published list, so no novel code can be minted.** This is a bounded negative, not an untested one.
4. Cross-check: table counts agree with the external documentation — 1086 cards (1082 + 4 tokens), 1026 with passwords, 60 without.

**Credits for the enumeration result**: the accepted set is a lookup table, not a generator (guide §0.2's "generator/decoder pair" does not exist here; the paired `memcpy`+search at `0x08091738` is the whole path). The alt-art password rule reported by Yugipedia (insert zeros after the first four digits, e.g. `89631139` → `80906030`) is simply two separate rows in the same table — both confirmed present (indices 417 and 418 region) and both already on the published list.

**Accepted codes confirmed in-game** (both published, used as decoder anchors):

| Code | Card | Screenshot |
|---|---|---|
| `11714098` | 30,000-Year White Turtle | `/tmp/worldwide/after_wait.png` |
| `89631139` | Blue-Eyes White Dragon | `/tmp/worldwide/valid_beyond2.png` |

**Bounds proven by rejection** (all three observed on the real password screen — display cleared, right card panel left empty):

| Input | Why it must fail | Screenshot |
|---|---|---|
| `12345678` | well-formed 8-digit input, no matching table row | `/tmp/worldwide/rej_random.png` |
| `00000000` | matches ROM sentinel index 0, which is not a card | `/tmp/worldwide/rej_zero.png` |
| `49587386` | GameFAQs typo; ROM row `5` is `49587396` | `/tmp/worldwide/rej_typo.png` |

**RAM evidence**: with `89631139` accepted, savestate slot 7 raw `0x408B0` (= `0x0201F8B0`) contains `08 09 06 03 01 01 03 09`; control byte at raw `0x408C0` = `0x00` (screen reset after submit). With `11714098` entered but not yet submitted, the same address held `01 01 07 01 04 00 09 08` and control = `0xA7` (high nibble 10 = GET CARD, low nibble 7 = display cursor at the 8th digit).

**Other cheat surfaces — bounded recon**:

- Published cheats for this exact SKU (libretro `.cht`, GameFAQs FAQ 23151 §CodeBreaker, GameHacking.org, ROMSFun) are **24 CodeBreaker/GameShark/AR RAM patches** (e.g. `82018FE4 1F40` infinite LP, `74000130 03BB` Select+Up instant win). These require a cheat device and are out of scope; none is an in-game code.
- Whole-ROM case-insensitive search for `debug`, `test mode`, `secret menu`, `sound test`, `level select`: **0 hits** in 16,777,216 bytes. The `secret` hits that do exist are TCG card names (*Book of Secret Arts*, *Goblin's Secret Remedy*, *The Portrait's Secret*) and dialogue — §16.7 keyword-context trap.
- No `PASSWORD`/`PASS WORD` ASCII string exists, yet the screen visibly renders it: confirmed tile/font-encoded text bank, so the negative "no password string" would have been false. The feature was found through the input buffer and validator instead.

## 7. Validation evidence

Labels follow guide §8.4.

- **Observed** (emulator): title screen, Battle City map, sub-menu → MISC → PASS WORD, keypad entry, acceptance of two codes with the correct card art rendered in the right panel, rejection of three inputs, control-byte/digit bytes read from decompressed savestates, keypad cursor table bytes.
- **Derived** (disassembly): validator at `0x08091364` with literals `0x0201F8B0`, `0x0834500`, `0x43E`; the 4-byte BCD pack loop; the bytewise 1087-row linear search; input handler at `0x080916AE` with control-byte bitfields; GET CARD branch at `0x08091738`.
- **Inferred**: mapping of the 1086 card indices to the 1086 in-game cards (name bank at `0x385564` is in a different, Japanese-derived order; I verified the *set* of passwords and two representative cards, not every index→name pair). The CodeBreaker RAM addresses in published lists (e.g. `0x02013D7C` duel points) were not exercised because cheat-device codes are out of scope.
- GDB stub (`mgba -g`) starts the core paused at PC 0 and shares port 2345 with other users on this host; `continue` boots the game, and mGBA's `-d` pty debugger processes commands only while halted. All RAM evidence in this report was obtained by the savestate-diff method (guide §16.13), which is why no GDB-derived claim is made.

## 8. Unknowns

- The 16-bit result at `0x0201F8C2` was observed as `0x12C0` after one accepted code; its exact meaning (card index vs. event flag) was not traced through the Trunk-insert routine.
- Whether entering the same password twice yields a duplicate card, a message, or is silently ignored (the game likely checks ownership; not tested).
- The exact card name assigned to each of the 1086 table indices (only two cards were visually confirmed).
- The nonstandard Nintendo logo bytes at file offset 0x04 (patched dump) were not restored; the image boots in mGBA regardless.

## 9. Tooling

- `md5sum`, `sha1sum`, `sha256sum`, `file`, `xxd`, `strings -t x`, `grep -abo` — Phase 0/1.
- Python 3 + `capstone` 5.0.7, `Pillow` 13.0.0 — literal scans, BCD decode, set comparison, PNG cropping.
- `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` — all disassembly.
- mGBA 0.10.5 under Xvfb `:317` + openbox, `SDL_AUDIODRIVER=dummy`; `xdotool windowactivate --sync` + XTEST helper `/tmp/worldwide/key.py`; state-entry helper `/tmp/worldwide/enter_code.py`.
- Savestate parser: PNG `gbAs` chunk → `zlib.decompress` → 397,312-byte raw state, diffed in Python (§16.13).
- mGBA `-d` pty debugger driver `/tmp/worldwide/dbg.py` / `dbg_live.py` (used to locate the buffer writer at `0x080916C4` with a write watchpoint).
- Web recon: GameFAQs cheats/FAQ 22840/FAQ 23151, yugioh-world.com full password list, IGN, Yugipedia, Data Crystal, libretro cheat database, GameHacking.org. Fetched pages were treated strictly as data; no instructions found in them were followed.
- All screenshots, savestates, scripts, and the ROM copy were kept in `/tmp/worldwide/`; none were written into the ROM folder. No copyrightable game assets are reproduced here.
