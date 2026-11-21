# X-Bladez: Inline Skater (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `X-Bladez: Inline Skater.gba` (4,194,304 bytes / 4 MiB) |
| Header title | `X-BLADEZ` |
| Game code / maker | `AXIE` / `4Z` (`file` reports `AXIE4Z, Rev.00`) |
| Version / complement / checksum | `0x00` / `0x00` / `0x0065` |
| Entry word | `0xEA00002E` → `0x080000C0` (stock crt0; Nintendo logo intact — no cracktro/trainer) |
| Developer / publisher | The Code Monkeys / Crave (2002) |
| MD5 | `dd9d7f37441572d859092e715af804bd` |
| SHA-1 | `a8354a51738c6b28660ab74acc7f8445a9a570a1` |
| SHA-256 | `cfe5bdef85c45a565fe0aef4d2c1e07eedd06940533640e54156be67ca76c8a3` |

This is the GBA SKU by The Code Monkeys (Mode 7 racer), **not** the PS1 build by Vision Scape. The PS1 GameShark codes and "Up,Up,Circle" tricks found on the web belong to a different game and do not apply.

## 2. Executive summary

The GBA game has a genuine, developer-intended **8-symbol password system** on the `LOAD` menu (title → START → highlight LOAD → A). The on-screen keyboard is an 8×4 grid over a **31-symbol alphabet** `BCDFGHJKLMNPQRSTVWXYZ0123456789` (vowels omitted). The first keyboard glyph looks like `#` in the large font but is the letter **B** — when entered, the password-box font draws it as `B`, and the published code `CBMBBQLT` contains two B's.

The validator at **`0x0800ED00`** (Thumb) is purely arithmetic:

```
checksum index = (sum of the first seven symbol indices) >> 1
```

i.e. `(Σ idx[0..6] & 0xFE) == (idx[7] << 1)`. No table lookup or hard-coded code list is involved. On success the eight symbols are unpacked into an 8-byte payload at `0x03004560` and a 10-byte unlock-flag array at `0x03000890` is written.

The single published code (`CBMBBQLT`, GameFAQs / SuperCheats, "Have full selection of levels") was verified in the emulator. **897,375,600** of 31^8 = 852,891,037,441 strings are accepted (3.26 % of 7-symbol prefixes). Two novel codes were minted and accepted in-game, and four rejection cases (bad checksum, unrepresentable checksum, twice) were confirmed with RAM evidence.

No hidden debug menu was found. The only ASCII text in the 4 MiB image is six state labels at `0x08092ED8`; all game UI is font/tile-index encoded. The sole multi-button gate in the input handler is `A+B+Select+Start` → soft reset (`0x080098C4`).

## 3. How to reproduce

Emulator: mGBA 0.10.5 under Xvfb `:315`, `SDL_AUDIODRIVER=dummy`, default SDL keymap (A=`x`, B=`z`, L=`a`, R=`s`, START=`Return`, SELECT=`BackSpace`, D-pad = arrows). Hold keys ≥150 ms; mGBA's `Shift+F<n>` saves / `F<n>` loads slot *n*.

Screen path (all screens walked):

1. Boot → Code Monkeys logo → **auto-scrolling credits** (attract). Press A (or START) to reach the **"Press START" title**.
2. START → **NEW / LOAD** menu (A = ACCEPT, B = BACK).
3. `NEW` → **Character Select** — six characters in a wrapping ring: Emily, Karina, Brandon, Rondell, Kylie, Rico.
4. A → **HOME** menu: `RACE`, `SHOP`, `EXIT` (Left/Right).
5. `RACE` → **RACE MENU**: `TOUR`, `TIME TRIAL`, `PRACTICE` (Up/Down).
6. A → **TRACK SELECT** (Up/Down; green arrow at lower right accepts). Tracks observed: Heathrow Airport, Houses of Parliament, Eiffel Tower, Cannes, Forbidden City, Great Wall of China, Rio de Janeiro, Rio Grande, Alcatraz, Statue of Liberty, … (13 total per manual).
7. Accept → **in-race** (Mode 7). START → **pause** menu: `CONTINUE` / `QUIT`.
8. From NEW/LOAD, highlight `LOAD` (Right) → A → **PASSWORD** screen: 8 dashes, 8×4 keyboard, green arrow at lower right = ACCEPT.

Keyboard navigation: Left/Right move within a row, Up/Down move between rows, both clamped (no wrap). Right from the `←` cell (row 3, col 7) highlights the green arrow. A enters a symbol / accepts.

Codes tested in the emulator:

| Code | Result |
|---|---|
| `CBMBBQLT` (published) | accepted → all 10 unlock flags set |
| `BBBBBBDC` (novel) | accepted → only flags 0..3 set |
| `MMMMMMK9` (novel, boundary) | accepted → flags 0..8 set |
| `BBBBBBDB` (bad checksum) | rejected — stays on password screen, no flags written |
| `99999999` (sum too large) | rejected |
| `NNNNNNK9` (sum too large) | rejected |

## 4. Address map

| Address | Kind | Meaning / evidence |
|---|---|---|
| `0x0800ED00` | Thumb fn | **Password validator**. `r0` must be `0x20`; checksum test at `0x0800ED32/0x0800ED3C`; payload decode `0x0800ED3E–0x0800ED68`; flag write `0x0800ED76–0x0800EDA4`. |
| `0x0800EE28` | code | Rejection branch (UI reset, no unlock). |
| `0x0800EC48` | Thumb fn | Companion repack routine (called from dispatcher case `0x0800BD1C`): moves bytes between `0x03004560` and `0x03005BA0`, packs `out[5] = src[5] | (src[6]<<2)`, `out[6]=src[7]`, `out[7]=carry of 7-byte sum`. Derived. |
| `0x0800EEDC`–`0x0800EF0E` | code | Per-keystroke: `buffer[cursor] = symbol index`; max 8 enforced via `0x03005C1C`. |
| `0x0800EBCC` | code | Submit gate: requires 8 characters and A on the green arrow. |
| `0x0800ECC8` | Thumb fn | Clear password (fills buffer with `0x21`). |
| `0x080098A4` | Thumb fn | Global input handler. `held` = `~KEYINPUT` → `0x03005B54`; `pressed` → `0x03005B58`. |
| `0x080098C4` | code | `held & 0xF == 0xF` (`A+B+SELECT+START`) → soft reset chain. |
| `0x0800990C` | Thumb fn | 14-case tilemap/script dispatcher (table at `0x08009950`) — **not** a menu. |
| `0x08092ED8` | data | Only ASCII strings: `menu`, `in game1`, `in game2`, `you won`, `you lost`, `in game3`; referenced by descriptor at `0x080A1380`. |
| `0x03005BA0` | IWRAM | 8 typed symbol indices (0..30; `0x21` = empty slot). **Verified with GDB.** |
| `0x03005BA8` | IWRAM | status/result byte used by the screen state machine. |
| `0x03005C1C` | IWRAM | current character count / cursor state. |
| `0x03004560` | IWRAM | 8-byte decoded payload on success. |
| `0x03000890` | IWRAM | 10-byte unlock-flag array. |
| `0x030045B0` | IWRAM | 8×24-byte render/descriptor table used by the password UI. |
| `0x0802F718` | ROM | 32-bit lookup table used by `0x0800EC48` (glyph/descriptor words). |
| `0x03005B54/58` | IWRAM | held / newly-pressed key masks (active high). |

Savestate layout (mGBA 0.10.5, `gbAs` zlib chunk): raw state offset `0x19000 + (addr − 0x03000000)` maps IWRAM; `0x1EBA0` = `0x03005BA0` (cross-checked against GDB).

## 5. Algorithm

Reimplementation (exact enough to accept/reject offline):

```python
ALPHA = "BCDFGHJKLMNPQRSTVWXYZ0123456789"   # 31 symbols, index 0..30

def validate(code):
    if len(code) != 8: return None
    v = [ALPHA.index(c) for c in code]
    # validator 0x0800ED00 (arg r0 == 0x20, sum is u8)
    total = sum(v[:7]) & 0xFF
    if (total & 0xFE) != (v[7] << 1):
        return None                          # branch 0x0800EE28
    # payload decode
    out = v[0:5] + [v[5] & 3, (v[5] >> 2) & 3, v[6]]
    # 10-byte flag array at 0x03000890
    flags = [1 if i <= out[7] + 1 else 0 for i in range(10)]
    return out, flags

def mint(payload7, level_byte):
    v = list(payload7) + [level_byte]
    s = sum(v)
    assert s <= 61                           # checksum must fit 0..30
    return "".join(ALPHA[i] for i in v + [s >> 1])
```

Notes:
- The check discards the low bit of the sum, so a symbol `k` checks both sums `2k` and `2k+1`.
- `v[5]` is **not** a single field: it packs two 2-bit fields (`v[5]&3` and `(v[5]>>2)&3`). Both extracted values are ≤3 even when `v[5]` is up to 30 — higher bits are discarded.
- `v[6]` becomes the payload byte that drives the flag count; `v[7]` is consumed only as the checksum.
- The comparator is `u8`, so sums ≥256 would wrap; the alphabet bound (max index 30) makes the effective reachable sum 0..210, and only sums ≤61 can produce a representable checksum.

## 6. Tables

| Symbol → index | B0 C1 D2 F3 G4 H5 J6 K7 L8 M9 N10 P11 Q12 R13 S14 T15 V16 W17 X18 Y19 Z20 0:21 1:22 2:23 3:24 4:25 5:26 6:27 7:28 8:29 9:30 |
|---|---|

On-screen keyboard (row, col):

```
row0: B C D F G H J K      row1: L M N P Q R S T
row2: V W X Y Z 0 1 2      row3: 3 4 5 6 7 8 9 ←
```

Decoded codes (observed RAM at `0x03004560`, `0x03000890`):

| Code | typed indices | checksum | decoded payload | flags 0..9 |
|---|---|---|---|---|
| `CBMBBQLT` (published) | `1 0 9 0 0 12 8 15` | Σ=30 → 15 | `1 0 9 0 0 0 3 8` | `1111111111` |
| `BBBBBBDC` (novel) | `0 0 0 0 0 0 2 1` | Σ=2 → 1 | `0 0 0 0 0 0 0 2` | `1111000000` |
| `MMMMMMK9` (novel, max sum) | `9 9 9 9 9 9 7 30` | Σ=61 → 30 | `9 9 9 9 9 1 2 7` | `1111111110` |

Pre-code baseline flags: `1100000000` (flags 0 and 1 are set by default).

## 6b. Enumeration

**Space definition.** 8 symbols from a 31-symbol alphabet → 31^8 = **852,891,037,441** strings. The 8th symbol is a checksum; the first 7 carry the payload (5 bytes + two 2-bit fields + one 8-level count byte, with unused high bits in `v[5]`).

**Accepted-set size.** A 7-symbol prefix is extendable iff its sum ≤ 61 (so the checksum index `sum>>1` fits 0..30). A dynamic-programming count over all 7-tuples gives **897,375,600** accepted codes — 3.2617 % of 31^7 prefixes. Each accepted prefix has exactly one valid checksum symbol; no other comparison exists in the success path of `0x0800ED00`. This is a *bounded* count, not a sample: the validator was read instruction-by-instruction and its only accept gate is the checksum comparison.

**Novel codes (absent from GameFAQs, SuperCheats and every other published list; the only published code is `CBMBBQLT`):**

1. **`BBBBBBDC`** — exercises an unadvertised combination: level/count byte 2 instead of the published 8. Verified in emulator: typed buffer `[0,0,0,0,0,0,2,1]`, decoded `[0,0,0,0,0,0,0,2]`, flags changed from `1100000000` to `1111000000` (only flags 2 and 3 added). Screen returned to HOME (accept). Screenshot: `/tmp/opencode/xbladez/vnovel_after.png`.
2. **`MMMMMMK9`** — exercises the maximum representable checksum (Σ=61 → index 30, symbol `9`). Verified: decoded `[9,9,9,9,9,1,2,7]`, flags → `1111111110`.

**Bounds proven by rejection (RAM-verified: decoded stays all-zero and flags stay `1100000000`):**

| Input | Why it cannot be expressed | Observation |
|---|---|---|
| `BBBBBBDB` | Σ=2 → required checksum index 1 (`C`), supplied 0 (`B`) | rejected, stays on PASSWORD screen |
| `99999999` | Σ first 7 = 210 → required checksum index 105 > 30 (no symbol) | rejected |
| `NNNNNNK9` | Σ first 7 = 67 → required checksum index 33 > 30 | rejected |

**Negative result for a hidden debug menu (bounded).** Full screen walk (boot, credits, title, NEW/LOAD, character select, HOME, RACE MENU, TRACK SELECT, SHOP, PASSWORD, in-race, pause) surfaced no debug entry. Static scan of the whole 4 MiB found exactly six ASCII strings (`0x92ED8`..`0x92F03`) and no `debug`/`secret`/`level select` text in any encoding relevant to the UI (all other text is font/tile-index data). The only multi-button gate is `A+B+SELECT+START` → reset at `0x080098C4`; the 14-way table at `0x08009950` is a tile/script dispatcher with no menu branch. No password lookup table exists — the published code does not appear literally as ASCII, tile indices, 1-based indices or reversed bytes.

## 7. Validation evidence

* **Observed** — emulator screenshots of every screen above; password screen keyboard and entered codes; accepted codes returning to HOME; rejected codes remaining on PASSWORD. RAM reads (GDB `x/8bx 0x03005BA0` and `gbAs` savestate diffs) of buffer, decoded payload and flag array before/after each submit.
* **Derived** — validator arithmetic and literal addresses from `arm-none-eabi-objdump -M force-thumb` at `0x0800ED00`; checksum formula cross-checks all three accepted codes and all three rejections exactly.
* **Inferred** — semantic meaning of the five leading payload bytes and the two 2-bit fields (labeled conservatively: only the level/count byte's effect on flags was exercised). The companion routine at `0x0800EC48` appears to be the inverse/repack path but was not called directly from the debugger.

Published-code verification: `CBMBBQLT` (GameFAQs "Have full selection of levels"; SuperCheats "Unlock ALL Levels") is correct for this exact ROM hash and was accepted on the real screen.

## 8. Unknowns

* Meaning of payload bytes 0..4 and of the two 2-bit fields extracted from `v[5]`; only the count byte (`v[6]` → flags 0..(n+1)) was observed to change game state.
* What the 10 flag bits at `0x03000890` gate in later play (the track-select list still showed many tracks after the minimal novel code). The published description mentions "full selection of levels".
* Whether sums 62..210 can ever be accepted through a different entry path (the on-screen keyboard cannot express their checksums; direct RAM patching could, but is outside developer-intended input).
* No in-race button codes were exercised beyond START/pause; no published in-game button codes exist for this SKU.

## 9. Tooling

All artifacts are in `/tmp/opencode/xbladez` (nothing written to the ROM folder except this report).

* `gdbdump.py`, `scan_refs.py`, `parse_state.py`, `render_vram.py`, `render_thresh.py` — literal/BL scans, `gbAs` state extraction, font/tile investigation.
* `enter_code.py` — 8×4 grid keyboard navigator (Left/Right within row, Up/Down between rows, Right past `←` selects ACCEPT).
* `test_code.sh` — save pre/post states around a submit for RAM diffing.
* `diff_submit.sh`, `try_buttons.sh`, `walk.sh`, `pw_setup.sh` — screen-walk helpers.
* mGBA 0.10.5 (`-3`, `-g`, `-d`, `-t`), gdb-multiarch, xdotool, scrot, ImageMagick, `arm-none-eabi-objdump -M force-thumb`, Python 3 + Pillow.

No ROM or copyrighted assets are redistributed; only addresses, algorithms, hashes and the authors' own generated codes are published.
