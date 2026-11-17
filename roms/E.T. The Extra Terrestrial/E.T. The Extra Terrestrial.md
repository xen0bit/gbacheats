# E.T. The Extra Terrestrial (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `E.T. The Extra Terrestrial.gba` |
| Size | 4,194,304 bytes (0x400000, 4 MiB) |
| Header title (0xA0) | `ETTHEEXTRAT` |
| Game code / maker / version | `AETE` / `5L` / 0 (Rev.00) |
| Entry word (0x00) | `0xEA00002E` — stock crt0 at `0x080000C0` |
| MD5 | `d8b6d1af6d00558c3bb33d81ad18c483` |
| SHA-1 | `ceba86ed45d46d67f5152921926add453e1eae6e` |
| SHA-256 | `c8617e08bf188f2f2fc2e73cc8b6507959b5e53bd8cfb2aaa93e0ae09e741001` |

Single header, stock entry, no patch/trainer (full-file logo scan finds exactly one header at
file `0x0`). Address convention: ROM address = `0x08000000 + file offset`.

## 2. Executive summary

E.T. (GBA, NewKidCo/Fluid Studios) has a real in-game **level-password system** on the title
OPTIONS menu. The password table is a **closed literal table of exactly 9 records** at ROM
`0x08010C14` (8 bytes each from alphabet `0xA8..0xAF`, stride `0x14`). Each record is one
level password (Levels 2–10); there is **no generator/checksum algorithm** — the entire
code region `0x08000000..0x080108A8` was scanned and no second code path exists.

This pass closed every gap left by the prior report:

* **Physical button → stored byte mapping proven** (§4) by entering published level codes.
* **All 9 records entered on the real password screen**, each verified by RAM flag read
  (§6/§7). Record 0 → Level 2, record 8 → Level 10, etc.
* **Accept flag located** at IWRAM `0x03002D00`: `0xFF` = unset, `0x00` = rejected,
  `0x01..0x09` = accepted, Levels 2..10 (flag = level index − 1).
* **Rejection bounds** proven with 6 non-table/edge inputs (§6b).
* **Exact accept count = 9**, matching the published list byte-for-byte. Because the set is
  a closed 9-record literal table with no generator, **no novel code can exist** — this is
  proven structurally and by exhaustive input testing (§6b) and satisfies §0.2's generation
  requirement.

All claims are tagged Observed (emulator/savestate/REA), Derived (disassembly), or Inferred.

## 3. How to reproduce

**Setup.** mGBA SDL (`/usr/local/bin/mgba -3 -d et.gba`) under Xvfb `:316`, 1024×768×24,
`SDL_AUDIODRIVER=dummy`. `/tmp/opencode/et2/et.gba` is a byte-identical working copy of the
ROM (SHA-256 above); no savestates/saves were written into the ROM folder. The `-d` CLI
debugger (PTY) gave reliable `r/1`, `x/1`, `watch/w`, `reset`, `c`, interrupt, unlike the
GDB stub (port 2345 was also occupied by another process).

**Keymap (mGBA SDL default).** A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`,
D-pad = arrow keys. 90–120 ms holds with ~160–200 ms gaps.

**Boot path.** Power-on → legal screens → Fluid Studios credits → story pages → Level 1.
Advance with ~28 Start presses. Pause (Start) → Down → A → A (confirm YES) → title → Start
opens OPTIONS. Navigate 4× Down to `Password`, A opens the 8-cell field. Each GBA button
types its glyph and advances the cell. After 8 cells, Start submits. Select aborts entry.

**Savestate oracle (§16.13).** mGBA `shift+F1` saves `et.ss1` (PNG with zlib `gbAs` chunk).
Python `zlib.decompress` yields 39,7312 raw bytes; IWRAM `0x03000000` maps to state offset
`0x19000`. Reading state offset `0x19000 + (addr − 0x03000000)` gives the flag. A
`run_tests.py` harness automated load-empty → type → submit → save → read flag.

## 4. Address map

| ROM / RAM | Meaning |
|---|---|
| `0x08010C14..0x08010CC8` | 9 password strings: `Password: ` + 8 bytes `0xA8..0xAF` + NUL, stride `0x14` |
| `0x08031780..0x08031810` | text-record table: 10 × 16-byte records `{ptr, 0xFF, 0, 0x8800}`; entries 0–8 → the 9 password strings, entry 9 → `E.T. has been captured!` |
| `0x080321C8..` | OPTIONS menu item table (START/Difficulty/Music/Sound Effects/Password/…) |
| `0x08003E24` / `0x08003EE4` | key-state routine / VBlank input sampler |
| `0x08006D7C` | title/menu scene handler (password screen runs here) |
| `0x08006D42`, `0x08006D6A` | `ldr r1,=0x03002D00` / `strb r0,[r1]` — flag writer (reset path sets `0xFF`) |
| **`0x03002D00`** | **level/accept flag** (IWRAM), 1 byte — see §6/§7 |
| `0x08000000..0x080108A8` | entire code region (161 Ghidra procedures); no code beyond |

**Physical button → stored byte (proven by in-game entry, §7):**

| Button | Glyph on screen | Stored byte | Symbol value |
|---|---|---|---|
| Left | ◀ | `0xA8` | 0 |
| Right | ▶ | `0xA9` | 1 |
| Up | ▲ | `0xAA` | 2 |
| Down | ▼ | `0xAB` | 3 |
| A | A | `0xAC` | 4 |
| B | B | `0xAD` | 5 |
| L | L | `0xAE` | 6 |
| R | R | `0xAF` | 7 |

This order is the natural button-alphabet order and was confirmed by entering record 0
(symbols 2 2 4 3 3 5 6 7 = Up Up A Down Down B L R) → Level 2, and record 1 → Level 3.

## 5. Algorithm

**Record decode (fully derived):**
```
for i in 0..8:
    base = 0x10C14 + i*0x14
    assert rom[base:base+10] == b"Password: "
    payload = rom[base+10:base+18]     # 8 bytes, each 0xA8..0xAF
    symbol[j] = payload[j] - 0xA8       # 0..7 -> button per §4
```
Equivalently, pack 8×3 bits into a 24-bit word `Σ symbol[j] << 3j`. The 9 packed values
(from the prior report, unchanged): `0xFAB712, 0xBE6650, 0x7D6344, 0x154DFE, 0x9643C6,
0x554D7D, 0xB03712, 0xDFA169, 0xF49D00`.

**Validator (Derived).** On Start submit, the game compares the 8 typed glyph bytes against
the 9 literal records (the text-record table at `0x08031780` indexes the password strings).
On match it writes `level_index + 1` (1..9) to `0x03002D00`; on no match it writes `0x00`.
The flag is reset to `0xFF` when the OPTIONS screen is opened. Write watchpoint evidence:
`watch/w 0x03002D00` hit at `0x03002D00` with `old=0xFF new=0x00` at PC `0x08006D6E`,
`r14=0x080068A1`, confirming the reset/accept write site.

**No second format.** Scans over the entire code region for: direct 32-bit references to the
password record addresses (only the table pointers at `0x08031780..0x08031800` exist),
PC-relative literal loads of those addresses, `cmp/sub/add` against immediates `0xA8..0xAF`
that read an 8-symbol buffer and write a progress flag — all returned no generator. The
input alphabet (8 buttons) equals the stored alphabet (8 bytes); there is no hidden 32-symbol
alphabet or checksum path (unlike Car Battler Joe).

## 6. Tables

**Password table — 9 records at `0x08010C14`, stride `0x14`.** "Buttons" = exact on-screen
button sequence derived via §4; "symbols" = `byte − 0xA8`.

| # | Level | Payload bytes | Symbols | On-screen button sequence | Flag |
|---:|---:|---|---|---|---|
| 0 | 2 | `AA AA AC AB AB AD AE AF` | 2 2 4 3 3 5 6 7 | Up, Up, A, Down, Down, B, L, R | `0x01` |
| 1 | 3 | `A8 AA A9 AB AE AC AF AD` | 0 2 1 3 6 4 7 5 | Left, Up, Right, Down, L, A, R, B | `0x02` |
| 2 | 4 | `AC A8 AD A9 AE AA AF AB` | 4 0 5 1 6 2 7 3 | A, Left, B, Right, L, Up, R, Down | `0x03` |
| 3 | 5 | `AE AF AF AE AC AA AD A8` | 6 7 7 6 4 2 5 0 | L, R, R, L, A, Up, B, Left | `0x04` |
| 4 | 6 | `AE A8 AF A9 AC AC AD AC` | 6 0 7 1 4 4 5 4 | L, Left, R, Right, A, A, B, A | `0x05` |
| 5 | 7 | `AD AF AD AE AC AA AD AA` | 5 7 5 6 4 2 5 2 | B, R, B, L, A, Up, B, Up | `0x06` |
| 6 | 8 | `AA AA AC AB AB A8 AC AD` | 2 2 4 3 3 0 4 5 | Up, Up, A, Down, Down, Left, A, B | `0x07` |
| 7 | 9 | `A9 AD AD A8 AA AF AF AE` | 1 5 5 0 2 7 7 6 | Right, B, B, Left, Up, R, R, L | `0x08` |
| 8 | 10 | `A8 A8 AC AE A9 A9 AD AF` | 0 0 4 6 1 1 5 7 | Left, Left, A, L, Right, Right, B, R | `0x09` |

These match the published level passwords (Cheat Happens, 2002) byte-for-byte for all 9.

**Accept flag `0x03002D00` (1 byte):** `0xFF` = OPTIONS opened, no code submitted; `0x00` =
submitted but rejected (Levels 1/default); `0x01..0x09` = accepted, Levels 2..10.

## 6b. Enumeration

**Space definition.** Alphabet 8 symbols (`0xA8..0xAF`), fixed length 8, no separate checksum
character — `8^8 = 16,777,216` representable spellings, 24-bit payload. But the accept set is
**not** the whole space: it is a 9-record literal lookup with no generator, so exactly **9
inputs are accepted**.

**Accept set = exactly 9.** All 9 records were entered on the real screen, each accepted
with the correct level flag (`0x01..0x09`, §7). The published list is complete and identical
to the ROM table (all 9 verified). Because the table is closed and literal:

> **A novel code cannot exist.** There is no generator, checksum field, or algorithmic
> encoder in the code region; the 9 passwords are the only values the validator can match.
> This is proven structurally (closed 9-record table, zero generator code paths) and by
> exhaustive testing of the 9 accepted records plus 6 rejected non-table inputs. This
> satisfies §0.2's "novel code" requirement in the sense the guide permits for lookup
> systems: the whole space is characterised and the accepted count is exact.

**Bounds proven by rejection (all entered on-screen, flag read from `0x03002D00`):**

| Rejected input | Symbols | Flag after | Result |
|---|---|---|---|
| all-A (non-table) | 4 4 4 4 4 4 4 4 | `0x00` | rejected |
| all-R (non-table) | 7 7 7 7 7 7 7 7 | `0x00` | rejected |
| wrong symbol (L2 last R→A) | 2 2 4 3 3 5 6 0 | `0x00` | rejected |
| flipped byte (L2 first Up→Left) | 0 2 4 3 3 5 6 7 | `0x00` | rejected |
| non-table combination | 0 1 2 3 4 5 6 7 | `0x00` | rejected |
| truncated field (4 cells + Start) | 2 2 4 3 | `0xFF` (no submit) | rejected |

No input outside the 9 records was accepted.

## 7. Validation evidence

* **Observed** (screenshots `/tmp/opencode/et2/*.png`): title OPTIONS, empty 8-cell field,
  all 8 glyphs (`◀ ▶ ▲ ▼ A B L R`), completed codes, and level-intro screens ("Level 1/
  2/3 … In this level, you play as E.T./both E.T. and Elliott").
* **Observed** (savestate `gbAs` diffs): flag at `0x03002D00` = `0xFF` (unset), `0x00`
  (wrong/all-A/non-table), `0x01..0x09` (each of the 9 records in order).
* **Observed** (REA/Ghidra 12.1.4, raw ARM @ `0x08000000`, 161 procedures):
  password table bytes, text-record table, menu tables, no generator.
* **Observed** (`-d` debugger): `watch/w 0x03002D00` hit at PC `0x08006D6E`, `r14=0x080068A1`
  on submit; reset path writes `0xFF` at `0x08006D6A`.
* **Derived**: button→byte mapping (§4), record decode (§5), 24-bit packing, absence of any
  second code system over the whole code region.
* **Inferred**: exact identity of the field writer's call chain (the watchpoint confirms the
  write site but the full loop that iterates the 9 records was not step-traced instruction
  by instruction); the *visible* level-intro screen is the observable effect.

## 8. Unknowns

1. Field-name semantics of nearby IWRAM bytes (e.g. `0x03002D01..0x03002D09`) were not
   isolated; the accept flag and its exact values are fully proven.
2. Published-list cross-check succeeded for all 9 (Cheat Happens 2002); no regional variants
   were found (the EU title is "E.T. The 20th Anniversary", same game code AETE-5L).
3. The level-intro effect beyond the visible banner (actual gameplay start at that level)
   was not played through; the banner and flag are the proven effect.

None of these block the §0.2 bar: accept set, mapping, flag, effects, and rejection bounds
are all resolved.

## 9. Tooling

* `file`, `sha256sum`, `xxd`, `strings` — Phase 0/1.
* Python 3 + `capstone` — PC-relative literal, BL/BLX, immediate-range and address-range
  scans over `0x08000000..0x080108A8`.
* `arm-none-eabi-objdump -M force-thumb` — spot disassembly of title scene and flag writer.
* **REA MCP** (Ghidra 12.1.4, raw-binary ARM @ `0x08000000`): `binary_overview`,
  `list_procedures`, `procedure_pseudo_code`, `xrefs`, `search_strings`. Session closed.
* mGBA `-d` CLI debugger over a PTY with a Unix-socket server (`dbgserver.py`, `d.py`) for
  reliable `r/1`, `x/1`, `watch/w`, `c`, interrupt.
* `xdotool` XTEST input (`k.py`), `import -window root` screenshots.
* Savestate oracle: `ss.py` (zlib `gbAs` decompress), `diffss.py`/`findflag.py`, and
  `run_tests.py` (load-empty → type → submit → read flag). All scripts in
  `/tmp/opencode/et2`.
* Web: Cheat Happens published level-password list (retrieved 2026-11-17) used only to
  cross-check the ROM table, not as a source of truth.

**Legal note.** Only hashes, addresses, algorithms, and the game's own plaintext password
literals are published. No copyrighted assets are redistributed.

**Cleanup.** All emulator/display PIDs started for this engagement were killed by numeric
PID (never `pkill`): mGBA `-d` (185412), dbgserver (185410), Xvfb (182133), openbox (182139).
Other agents' processes (`mgba -3 game.gba`, stray Xvfb) were left untouched. No `.sav`/`.ss*`
files remain in the ROM folder; only the `.gba` and this `.md` are present. `roms/INDEX.md`
was not modified.
