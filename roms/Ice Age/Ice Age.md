# Ice Age (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Ice Age/Ice Age.gba` |
| Size | 4,194,304 bytes (0x400000, 4 MiB) |
| Header title | `ICEAGE` |
| Game code | `AIAE` + maker `41` (`file` prints "AIAE41, Rev.00") |
| Version / complement / checksum | `0x00` / `0x3E` (valid) / `0x0000` |
| Entry word | `0xEA00002E` (stock ARM branch, **not** a cracktro/patched entry) |
| Nintendo-logo hits | exactly one, at header offset `0x0` → single image, **not** a multi-game cart |
| MD5 | `4235dbfac776ac1d3c391c740ce28892` |
| SHA-1 | `4804b2b85f9d5c94bb844c367a4ed3e05cfd3dc5` |
| SHA-256 | `94acd89a91a9b8a9345e65f60568cf020d84219c2e7ab106279df034641d18eb` |
| CRC32 | `0x3FC99714` (matches a 3rd party cheat index's `Ice Age (USA) (En,Fr,Es)`, AGB-AIAE-USA) |

Developer/publisher (from 3rd party cheat indexes archived page): Artificial Mind and Movement / Ubisoft, release 2002-03-18. No trainer, patch, appended image or second header was present. `strings` finds only audio-engine text (`Shin'en Multimedia. Code: B.Wodok`, GAX warnings, and `level1`…`level10`+`levelok` music-track titles © Manfred Linzner) — those `levelN` hits are **audio track names, not level-select data**. All in-game UI text is font/tile-indexed, so no UI string appears as ASCII; the GUI itself (title, options, password keyboard, level select, pause) was walked visually and the text/data bank was decoded from the game's own tables (below).

## 2. Executive summary

The game has a genuine developer-intended **progress-password system** on its title menu (`New Game / Password / Options`). It is fully reversed, not merely matched to a published list:

* Six-letter code, alphabet `B C D F G H J K L M N P Q R S T` (16 symbols, 4 bits each). A 17th on-screen key `V` is reachable but never used by the validator (rejected).
* The game stores each symbol as `nibble + slot_index` in a 6-byte RAM buffer, then runs a checker at ROM `0x08004D80`. Checksum: `n0 = (n1+n2+n3+n4+n5-1) mod 16`. A second, semantic gate requires the packed **level mask** to be a unary value `2^k−1` with `k = 1..10`.
* Fields: `level ∈ 1..10` (unary), `golden-acorn bitmask ∈ 0..0x3FF` (10 bits). All ten acorns plus all ten levels sets an extra bonus-stage bit (`0x400`).
* Five **hard-coded** shortcuts bypass the checksum: `TSLMFD` (ending), `MFKRPH`, `GDQLMD`, `JRCFSM`, `TRJBQG` (four film-art stills). They live as a pointer table at ROM `0x08144D4C` pointing to six-byte strings at `0x08144D2C`.
* Exhaustive enumeration: **10,240 algorithmic codes + 5 hard-coded = 10,245 accepted strings** out of `16^6 = 16,777,216` possible.
* A novel code absent from every published list, **`CCTQCH`** (level 7, acorns 1/3/5), was generated, typed on the real screen and RAM-verified. Bounds were proven by four in-game rejections.
* The sibling *Ice Age 2: The Meltdown* (a different 16 MiB image, code `BIAE`, MD5 `11cb293eb98b1d7bab027cda8777c98e`) shares **none** of this: no Ice Age-1 literal appears in its image and it has no ASCII `password`/`cheat`/`debug` string. The two were verified independently; nothing is shared.

## 3. How to reproduce

Emulator: mGBA under `Xvfb :318`, `SDL_AUDIODRIVER=dummy`, `-3` scale.
Keymap used: `A=x`, `B=z`, `Start=Return`, D-pad = arrow keys, L=`a`, R=`s`. **Hold keys 0.05–0.08 s** (0.12 s double-steps menus in this build).

Path: language `English` → title `New Game / Password / Options` → `Password` → on-screen 3×6 keyboard (row 1 `B C D F G H`, row 2 `J K L M N P`, row 3 `Q R S T V ↵`) → navigate to each letter, `A` to commit (cursor stays on the letter) → `Start` submits. The six entered letters appear in the slots at the bottom; a large orange ✕ is drawn while the checksum fails. A valid code opens `Select level`; `Left/Right` browse the unlocked range, and a golden-acorn icon appears when any acorn flag is set. `B` returns from Password to the title; `Start` in-game opens `PAUSE / Music / Sounds / Quit Level / Back to Game`.

Codes verified live: `PBBQBB` (L2), `QBCQBB`, `SBFQBB`, `DBKQBB`, `NBTQBB`, `PCTQBB`, `RFTQBB`, `CKTQBB`, `MTTQBB`, `NTTTTT`, `TSLMFD`, `MFKRPH`, `GDQLMD`, `JRCFSM`, `TRJBQG`, plus novel `CCTQCH` and four rejected inputs.

Published sources checked: 3rd party cheat index cheats (via `web.archive.org/web/20230528213419/...`, direct fetch 403), 3rd party cheat indexes, 3rd party cheat index-adjacent pages, and the independent generator/article at `607web.nl/ice-age-passwords` and `607web.nl/game-passwords`. The generator's JavaScript was treated as **data** and re-verified byte-for-byte against the ROM (§5). No prompt-injection payload was encountered in the fetched pages.

**Published-code verification:** all 14 six-letter codes above are accepted. 3rd party cheat indexes' `Art Gallery: MSW5` is a **typo/bogus** — `W` and `5` do not exist on the on-screen keyboard (alphabet has no W, no digits), and the literal `MSW5` is absent from the ROM; the real art-gallery codes are `MFKRPH`, `GDQLMD`, `JRCFSM`, `TRJBQG`.

## 4. Address map

File offset `o` ↔ ROM address `0x08000000 + o`.

| ROM address (file) | Meaning |
|---|---|
| `0x08004D80` (`0x4D80`) | **Password validator / decoder** (`push {r4-r6,lr}`; checksum loop `0x08004D84`–`0x08004DAE`; unary level gate `0x08004DDC`–`0x08004E02`; field write-back `0x08004E04`–`0x08004E24`). Returns `0` accept, `1` reject. |
| `0x08004D0C` (`0x4D0C`) | Password-screen state initialiser; writes `0x03004D84` etc. |
| `0x08005B60`–`0x08005DB0` (`0x5B60`–`0x5DB0`) | Password-screen handler: key storage `0x08005C36`–`0x08005C64`, `bl 0x08004D80` at `0x08005C74`, 5-entry hard-code scan `0x08005C80`–`0x08005CEA`, bonus gate `0x08005CEE`–`0x08005D22`. |
| `0x08144D2C` (`0x144D2C`) | Five hard-coded 6-byte code strings, stored as `nibble+i` (see §6). |
| `0x08144D4C` (`0x144D4C`) | Pointer table (5 × u32) to those strings. |
| `0x08144D60`–`0x08144D80` (`0x144D60`…) | Effect/tile tables indexed by which hard-coded code matched. |

| RAM address | Meaning | Evidence |
|---|---|---|
| `0x03005040` (6 bytes) | Input buffer, `buf[i] = nibble_i + i` | Validator literals at `0x08004E30`; store instruction `0x08005C4E` |
| `0x03005048` (u8) | Current slot index 0..5 / key state | Literal `0x08005D64`; `cmp #5` at `0x08005C44` |
| `0x03005050` (u8) | Selected key value (nibble); `17` = the extra `V` key | Literal `0x08005D68`; `cmp #17` at `0x08005C3C` |
| `0x03004D84` (u16) | **Unlocked-level bitmask** — `2^maxLevel−1`, plus bit `0x400` for the bonus stage | Literal `0x08004E34`; store `0x08004E06`; savestate dumps |
| `0x03002A08` (u16) | **Golden-acorn bitmask** (bit *i* = acorn *i+1*) | Literal `0x08004E38`; store `0x08004E24`; savestate dumps |

`0x03004D84` is the same address range used by the Pirates of the Caribbean GBA progress flag in the guide's worked example — here too the whole progress state is a single IWRAM word, read directly from savestates.

## 5. Algorithm

Reimplementation (matches the ROM on every accepted and rejected input tested):

```
symbols = "BCDFGHJKLMNPQRST"            # index = nibble 0..15
# key press with cursor in slot i writes  buf[i] = nibble + i   (i = 0..5)

def decode(chars):
    n = [symbols.index(c) for c in chars]
    if any(c not in symbols): return REJECT              # e.g. the 17th key V
    buf = [n[i] + i for i in range(6)]

    # 0x08004D84..0x08004DAE, all arithmetic on 8-bit bytes
    if ((buf[1]+buf[2]+buf[3]+buf[4]+buf[5]) & 0x0F) != buf[0]:
        return REJECT
    # equivalently, in nibble space: n0 == (n1+n2+n3+n4+n5 - 1) & 0xF

    n1,n2,n3,n4,n5 = buf[1]-1, buf[2]-2, buf[3]-3, buf[4]-4, buf[5]-5
    levelmask = (n1 << 6) | (n2 << 2) | ((n3 >> 2) & 3)   # 0x08004DCE
    # 0x08004DDC..0x08004E02: scan bits 9..0; require a contiguous run of
    # 1s ending at bit 0 -> levelmask == 2^k - 1, k in 1..10
    if levelmask not in {1,3,7,15,31,63,127,255,511,1023}: return REJECT

    acornmask = ((n3 & 3) << 8) | (n4 << 4) | n5           # 0x08004E1A
    # 0x08005CEE: if levelmask == 0x3FF and acornmask == 0x3FF,
    #            levelmask |= 0x400                       (bonus stage)
    # 0x08004E06 / 0x08004E24: write levelmask -> 0x03004D84,
    #                          acornmask -> 0x03002A08
    return ACCEPT, levelmask, acornmask

# checked BEFORE the checksum gate fails, at 0x08005C80..0x08005CEA:
# if buf == one of the five stored 6-byte strings -> its own dedicated effect
```

`k` is the highest playable level: `levelmask = (1<<k)-1` unlocks levels 1..k. The "+15" of the slot indices is why the published checksum appears as `−1 mod 16`. Only `n1`, `n2` and the high two bits of `n3` encode the level; the low two bits of `n3` plus all of `n4`,`n5` encode acorns; `n0` is the checksum. No XOR keys, PRNG or hidden permutation are involved.

## 6. Tables

**Alphabet / key grid** (screen row-major; index = nibble):

| idx | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| char | B | C | D | F | G | H | J | K | L | M | N | P | Q | R | S | T |

A 17th key `V` exists physically but has no nibble in the validator alphabet and is always rejected.

**Hard-coded codes** (ROM `0x08144D2C`, decoded from `nibble+i` bytes):

| Stored bytes | Code | Effect (observed) |
|---|---|---|
| `09 04 09 10 0F 0A` | `MFKRPH` | Film-art still #1 |
| `04 03 0E 0B 0D 07` | `GDQLMD` | Film-art still #2 |
| `06 0E 03 06 12 0E` | `JRCFSM` | Film-art still #3 |
| `0F 0E 08 03 10 09` | `TRJBQG` | Film-art still #4 |
| `0F 0F 0A 0C 07 07` | `TSLMFD` | Ending movie |

**Published algorithmic codes decoded** (all verified in mGBA):

| Code | k | levelmask | acornmask |
|---|---|---|---|
| `PBBQBB` | 2 | 0x003 | 0x000 |
| `QBCQBB` | 3 | 0x007 | 0x000 |
| `SBFQBB` | 4 | 0x00F | 0x000 |
| `DBKQBB` | 5 | 0x01F | 0x000 |
| `NBTQBB` | 6 | 0x03F | 0x000 |
| `PCTQBB` | 7 | 0x07F | 0x000 |
| `RFTQBB` | 8 | 0x0FF | 0x000 |
| `CKTQBB` | 9 | 0x1FF | 0x000 |
| `MTTQBB` | 10 | 0x3FF | 0x000 |
| `NTTTTT` | 10 | 0x7FF (10 + bonus) | 0x3FF |

## 6b. Enumeration

**Space definition.** 6 symbols × 4 bits = 24 bits nominal (`16^6 = 16,777,216` strings). Reserved/unused: the 17th key `V` is outside the alphabet. Accepted space, counted by an exhaustive C reimplementation of the ROM decoder (`/tmp/iceage1/enumerate.c`, full `16^6` sweep):

* **10,240 algorithmic codes** = 10 unary level values × `2^10` acorn masks;
* **5 hard-coded codes** (which deliberately fail the checksum path);
* **total 10,245 accepted strings.**

**Novel code (not on 3rd party cheat indexes, 607web or any wiki):** **`CCTQCH`**

* nibble vector `[1,1,15,12,1,5]`; buffer bytes `[1,2,17,3,4,5]`; checksum `(2+17+3+4+5)&0xF = 1 = n0` ✓
* decodes to `levelmask = 0x07F` (levels 1–7) and `acornmask = 0x015` (acorns 1, 3, 5).
* Entered on the real Password screen (`novel_entered.png`): no ✕, accepted. `Start` → `Select level`; browsing right stops at **07** (`novel_max.png`). RAM read from the resulting savestate: `0x03004D84 = 0x007F`, `0x03002A08 = 0x0015` — exactly the decoded fields. No published source lists this code or this acorn combination (published lists only give the ten zero-acorn level codes and `NTTTTT` for all-acorns/all-levels).

A second novel code was also produced by the model, `HKTQNN` (level 9, acorns 2/4/6/8), confirming generation is general rather than a one-off.

**Bounds proven by rejection** (all four shown in-game, red ✕; `Start` does not leave the Password screen):

| Input | Why it must fail | Result |
|---|---|---|
| `BCTQCH` | wrong checksum (`n0=0`, expected 1) | ✕ rejected |
| `VCTQCH` | `V` is the 17th key, outside the 16-symbol alphabet | ✕ rejected |
| `TCTBBB` | checksum valid, but `levelmask = 0x07C` is not unary (`n3` high bits cleared) | ✕ rejected |
| `DDHQBB` | checksum valid, but `levelmask = 0x097` is not an encoding of any level 1–10 | ✕ rejected |

These separate the checksum layer from the semantic/unary layer and bound the field widths exactly: no out-of-range level, no reserved-bit clearing, and no 17th-symbol spelling is accepted.

## 7. Validation evidence

**Observed** (emulator / savestate RAM reads):
* All menus/screens walked: language select, title (`New Game / Password / Options`), Options (`Music`, `Sounds`, `Credits`, `Back`), Password keyboard, `Select level` (incl. the bone-icon bonus entry after `NTTTTT`), in-game pause (`Music`, `Sounds`, `Quit Level`, `Back to Game`), five hard-code art/ending screens.
* Checksum ✕ appears/disappears live while typing; `Start` accepts only ✓ codes.
* Unlocked-level mask at `0x03004D84`: `0x0001` (empty), `0x0003` (`PBBQBB`), `0x007F` (`PCTQBB`, `CCTQCH`), `0x03FF` (`MTTQBB`), `0x07FF` (`NTTTTT`).
* Acorn mask at `0x03002A08`: `0x000` (none), `0x015` (`CCTQCH`), `0x3FF` (`NTTTTT`).
* Five hard-coded codes each produce a distinct non-Password screen (pixel-difference vs. the Password screen: mean 59–88/255).

**Derived** (ROM bytes/disassembly, verified against observations): validator at `0x08004D80`, decoder field packing `0x08004DBA`–`0x08004E24`, hard-code table `0x08144D2C`/`0x08144D4C`, buffer `0x03005040`, unary level gate, bonus gate `0x08005CEE`, exhaustive count 10,245.

**Inferred / bounded negatives:** no hidden debug screen was found. This is a bounded statement: the title/password/pause menus were enumerated entry by entry; `L+R`, `Select+Start`, `L+R+Start` and `A+B+Start+Select` were pressed on the title (the last only re-entered Password); all 10,245 accepted strings decode to either the level/acorn fields or one of the five documented still/ending effects, so the code space contains no additional screen. UI text is tile-indexed (no ASCII UI strings in the image), so the negative does not rest on `strings` alone — the keyboard alphabet, input buffer and hard-code table were decoded from the ROM's own data. Golden-acorn icons are drawn from the `0x03002A08` mask; individual per-stage collectible screens beyond this mask were not exhaustively played.

## 8. Unknowns

* The exact on-screen *label* text bank (font indices → glyphs) was not fully decoded; navigation used the visible keyboard and the ROM's code tables instead. It is not needed for the code system.
* Effects of individual acorn counts inside a level (as opposed to the final `0x03002A08` mask) were not played through; only the mask was RAM-verified.
* `MFKRPH`/`GDQLMD`/`JRCFSM`/`TRJBQG` were confirmed to display distinct stills, but the exact still subject of each was not catalogued (no assets are redistributed).
* Header checksum is stored as `0x0000` while the computed value is `0x501A`; the complement byte `0x3E` is correct, so this is a normal header artifact rather than a modified header — no patched/trainer code found.

## 9. Tooling

`objdump` (`arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`), Python 3 (savestate `gbAs` zlib chunk parsing, `ssdiff.py`, `render_vram.py`, `pw.py` keyboard driver, `gdbctl.py`/`ptyctl.py` experiments), C (`enumerate.c`, compiled with `gcc -O2`), mGBA SDL (`mgba -3`, `Shift+F1..F9` savestates), Xvfb :318 + openbox, xdotool, scrot/ImageMagick, `strings`/`grep`, web.archive.org and websearch. No REA provider was needed: a raw GBA ROM is fastest with objdump + emulator, per the guide. All generated `.ss*` and `.sav` files were removed from the ROM folder after analysis; no process other than this job's own PIDs was touched.

**Legal note:** no ROM, extracted graphics, music or game text is redistributed here — only hashes, addresses, algorithms, the decoder reimplementation and original example codes.
