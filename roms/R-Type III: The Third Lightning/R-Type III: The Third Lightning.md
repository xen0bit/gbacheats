# R-Type III: The Third Lightning (GBA) — Reverse Engineering Report

## 1. Target identity

| Item | Value |
|---|---|
| File | `R-Type III: The Third Lightning.gba` |
| Size | 4,194,304 bytes (`0x400000`) |
| Header title | `RTYPE III` |
| Game code / maker | `BR3E` / `20` (Europe), version `0x00` |
| Entry word | `0xEA00002E` (stock branch to `0x080000C0`) |
| MD5 | `188e4a01bf62230b7b50eaeb9355bd42` |
| SHA-1 | `a69527bb63e76f72f2e5e471e171e24a3043e2d9` |
| SHA-256 | `0acbd966e7009e80320a517d11184bba8d7703ed1d194b6f23d223828d5ca10c` |

**Phase 0 result:** exactly one Nintendo-logo header (file `0x0`); header complement check valid
(with the standard `-0x19` correction); entry word is the unmodified retail branch. No cracktro,
appended trainer, or second image. The 4 MiB image is the genuine retail ROM.

## 2. Executive summary

The game has a **real, developer-intended password system**, exposed on a dedicated
`ENTER PASSWORD` screen. A password is **5 symbols** from a 32-symbol alphabet
`BCDFGHJKLMNPQRSTVWXYZ0123456789?` (ROM `0x08CFBB8`). The first four symbols carry a
20-bit payload; the fifth is a sum checksum `(v0+v1+v2+v3) mod 32`. The payload is split
into seven bit fields (table `0x0834CA4C`), and a separate XOR-integrity field must equal
the XOR of the other six. Field 3 (bits 7–9, base 1, max 6) is **level minus one**.

The five published GBA passwords were verified against the algorithm (and accepted in
mGBA). They are **not stored as literals** in the ROM — no encryption is involved, the
game computes them. The published button code "R×10, L×N, Start" does **not** work on the
GBA build (verified in emulator).

The whole space was characterised: **27,648** passwords are accepted out of `32^5 =
33,554,432` possible strings (1,048,576 pass the sum checksum; field ranges plus the XOR
check reduce this to 27,648). Levels 2–7 each have exactly 4,608 valid passwords.
A novel, unadvertised level-7 password **`50DS?`** was minted, entered on the real screen,
accepted, and RAM-proven (`0x030043C4 = 0x06`); it loads a level-7 stage with no art (solid
cyan). Bounds were proven by rejecting a bad-checksum string (`50DSB`) and an out-of-range
level-8 string (`54DSF`) whose sum checksum is valid; neither writes the level byte.

`CheatMenuProcess` is a registered but **empty** process (all three function slots are
`bx lr`), and the demo-recorder source-format strings at `0xCFBF8+` have no reachable menu.
No hidden debug screen was found.

## 3. How to reproduce

* Emulator: `SDL_AUDIODRIVER=dummy mgba -3 <rom>` on `Xvfb :316`.
* Keymap (mGBA SDL defaults): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
  Select=`BackSpace`, D-pad = arrow keys. Hold 100–150 ms.
* Boot and press Start through the intro until the **title menu**
  (`NEW GAME` / `RESUME` / `OPTIONS`) is displayed.
  * The title menu is a normal game screen; for repeatability I also returned to it by
    patching the current-process pointer at RAM `0x03005DA0` to `0x0803741C` in an mGBA
    savestate and booting with `-t`. This was a harness convenience only; all codes below
    were entered on the game's own password screen with normal controller input.
* On the title menu: **Right** moves `NEW GAME` → `RESUME`; **Down** selects `OPTIONS`.
* With `RESUME` highlighted, press **A**: the `ENTER PASSWORD` screen opens.
* Password-screen controls: **Up/Down** cycle the character in the selected slot (from the
  empty `x` state, Up yields alphabet index 0 = `B`); **Left/Right** move between the five
  slots; **A** submits (`SET`); **B** deletes (`DELETE`).
* Codes tested (typed on the real screen):

| Code | Expected | Observed |
|---|---|---|
| `5BDGB` | Level 2 (published) | Accepted; gameplay, level byte `0x01` |
| `5WDL0` | Level 6 (published) | Accepted; level byte `0x05` |
| `50DS?` | Level 7 (novel) | Accepted; solid-cyan unimplemented stage, level byte `0x06` |
| `50DSB` | bad checksum | Rejected; returns to title, level byte stays `0x00` |
| `54DSF` | level 8 (out of range), valid sum checksum | Rejected; returns to title, level byte `0x00` |
| R×10, L×3, Start at title | published "level select" | No effect — code is SNES-only |

## 4. Address map

| Address (ROM unless noted) | Role |
|---|---|
| `0x08007C68` | Password **generator** — initialises field struct and sets 7 fields from game state, then encodes |
| `0x08007D50` | Password **validator** — decodes, extracts 7 fields, checks XOR relation, writes level/state |
| `0x080312B4` | Field-struct initialiser `(struct, field_table, 7 fields, 4 payload chars)` |
| `0x08031408` | Encode packed fields → 4 symbols + sum check symbol |
| `0x08031468` | Decode 5 symbols → packed word; verifies sum checksum; returns 1/0 |
| `0x08031318` / `0x080313A0` | Set / get one bit field |
| `0x0834CA4C` | Field descriptor table, 7 × 12-byte records `{bit-index/id, base, max}` |
| `0x0803760C`, `0x08037628` | Generator / validator jump tables (7 cases each) |
| `0x08CFBB8` | 32-symbol alphabet `BCDFGHJKLMNPQRSTVWXYZ0123456789?` |
| `0x08034CB4C` | UI string pointer table; `+0x54`=`Password Allowed!`, `+0x58`=`Wrong Password` |
| `0x08037360`–`0x08037518` | Process records (name + 6 function pointers each) |
| `0x08037410` | `PasswordProcess` record (init `0x08008120`, main `0x08007E7C`) |
| `0x08037464` | `CheatMenuProcess` record — slots `0x08008B7D/79/75` all `bx lr` (dead) |
| `0x03005DCC` (RAM) | Password struct: `+0` field table, `+4` width table, `+8`=7, `+12` packed word, `+16`=4, `+20` five characters + NUL |
| `0x030043C4` (RAM) | Level byte (`level - 1`) written by the validator |
| `0x03005DA0` (RAM) | Current-process function-table pointer |

## 5. Algorithm

Alphabet (index = value, 0..31):

```
B C D F G H J K L M N P Q R S T V W X Y Z 0 1 2 3 4 5 6 7 8 9 ?
0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
```

Decode / validate (ROM `0x08031468`, `0x08007D50`):

```
values[i] = index_of(char[i])          # i = 0..4 ; invalid char -> reject
packed = values[0] | values[1]<<5 | values[2]<<10 | values[3]<<15 | values[4]<<20
if (sum(values[0..3]) & 31) != values[4]: reject        # sum checksum
# field table (bit_width, base, max) in order:
F = [(2,0,3),(2,0,2),(3,0,7),(3,1,6),(4,0,15),(2,0,2),(3,0,7)]
offsets = 0,2,4,7,10,14,16
for each (w,b,m),off:
    v = ((packed >> off) & ((1<<w)-1)) + b
    if v > m: reject                    # range layer
    field[k] = v
if field[6] != field[0]^...^field[5]: reject           # XOR integrity layer
write field[3] to level byte 0x030043C4 ; start game
```

Encode (ROM `0x08007C68`, `0x08031408`): pack `stored = field - base` at the offsets above,
emit four symbols from the low 20 bits (5 bits each), then append
`alphabet[sum(values[0..3]) & 31]`.

Field 3 is level minus one; `max=6` therefore caps legitimate passwords at **level 7**
(levels 2–7). The other fields are game-state settings (force/device/weapon configuration);
their exact semantics were not fully resolved (see §8).

## 6. Tables

Published level passwords (GameFAQs / IGN / Supercheats / ChapterCheats — all agree except
IGN's `5hhlQ`/`5wdlo`, which are case/O-vs-0 transcriptions of the same 5 symbols):

| Level | Password | Decoded fields `[f0..f6]` |
|---|---|---|
| 2 | `5bdgb` | `[2,2,1,1,2,0,2]` |
| 3 | `5hhlq` | `[2,2,3,2,5,0,4]` |
| 4 | `5mglt` | `[2,2,3,3,4,0,4]` |
| 5 | `5rflx` | `[2,2,3,4,3,0,4]` |
| 6 | `5wdl0` | `[2,2,3,5,2,0,4]` |

None of these strings appears literally in the ROM (searched ASCII, upper/lower, and
packed 5/6-bit forms): the game generates them algorithmically. IGN's `5hhlQ` and `5wdlo`
decode identically because `Q`=`q` in this case-insensitive alphabet and `o` is not a
member (final digit `0` is the only valid symbol).

## 6b. Enumeration

**Space size.** `32^5 = 33,554,432` five-symbol strings. Sum checksum ⇒ `32^4 =
1,048,576` candidates. Exhaustively running the field-range + XOR validator over all
1,048,576 payloads (offline reimplementation, cross-checked against five published codes
and the ROM's own decoder) yields **exactly 27,648 accepted passwords**:

| `f3` (level−1) | accepted passwords |
|---|---|
| 1 (level 2) | 4,608 |
| 2 (level 3) | 4,608 |
| 3 (level 4) | 4,608 |
| 4 (level 5) | 4,608 |
| 5 (level 6) | 4,608 |
| 6 (level 7) | 4,608 |

**Novel code.** `50DS?` — fields `[2,2,3,6,2,0,7]`. It appears in no published list;
published material stops at level 6. Entered on the real `ENTER PASSWORD` screen: accepted,
level byte `0x030043C4` changed `0x00 → 0x06`, and the game loaded the unimplemented level-7
stage (solid cyan, no tile data). Other level-7 variants generated and decoder-verified:
`50BN4`, `50CL3`, `50FQ9`, `50GD0`, `50HBZ`, `50JJ6`, `50KG5`.

**Bounds proven by rejection.**

* `50DSB` — identical payload to the novel code but with the checksum symbol changed
  (`B`=0 instead of `?`=31). Sum check fails: the game returns to the title menu and
  `0x030043C4` stays `0x00`; the packed word remains `0x00070ABA` (checksum symbol stored
  but payload not committed).
* `54DSF` — sum checksum **valid** (`26+25+2+14=67 ≡ 3`, last symbol `F`=3) but field 3
  decodes to `7`, above its `max=6`. Rejected; level byte stays `0x00`. This isolates the
  field-range layer from the checksum layer.

RAM evidence (mGBA savestates, `gbAs` chunk decompressed):

```
state              packed@0x03005DCC+12   chars@+20        level byte @0x030043C4
before entry       00000000               ......           0x00
after 5BDGB        1a080200               "5BDGB\0"        0x01   (level 2)
after 5WDL0        3a0a5401               "5WDL0\0"        0x05   (level 6)
after 50DS?        ba0af701               "50DS?\0"        0x06   (level 7, novel)
after 50DSB        ba0a0700 (0x00070ABA)  "50DSB\0"        0x00   (rejected)
after 54DSF        3a0b3700 (0x00370B3A)  "54DSF\0"        0x00   (rejected)
```

## 7. Validation evidence

* **Observed** — `ENTER PASSWORD` screen with 5 slots; `5BDGB` typed and screenshot;
  gameplay after acceptance; level-7 solid-cyan stage after `50DS?`; title-menu return
  after both rejections; force-select screen; pause screen; title menu; published
  R×10/L/Start button code having no effect.
* **Observed (RAM)** — password character buffer, packed word, and level byte as tabled
  above; password struct initialised to field table `0x0834CA4C` and width table
  `0x020087E0` on the password screen.
* **Derived** — validator/generator/encoder/decoder disassembly at the addresses in §4;
  checksum formula (confirmed against all five published codes and the novel code);
  exhaustive count of 27,648 accepted passwords.
* **Inferred** — meanings of fields 0,1,2,4,5 (force/device/weapon state); they correlate
  with the published codes but were not independently mapped to specific in-game options.

## 8. Unknowns

* Exact semantics of fields 0, 1, 2, 4 and 5 (only field 3 = level−1 was proven by RAM).
* The literal `Wrong Password` / `Password Allowed!` message was not captured on screen;
  in practice rejection returns to the title menu and acceptance starts gameplay.
* The `OPTIONS` title-menu entry leads to the weapon/force select screen in this build;
  the English/Italian option lists in the string bank (`Music`, `Sound FX`, `Credits`,
  `Music test`, `Exit`) were not reached through any controller path tried.
* `CheatMenuProcess` is dead code (three `bx lr` slots). The demo-recorder format strings
  at `0xCFBF8+` have no reachable menu; no hidden debug screen was found.
* No patch/trainer was present; no GameShark/CodeBreaker codes were used or reported.

## 9. Tooling

* `arm-none-eabi-objdump -M force-thumb` for raw GBA disassembly; `capstone` 5.0.7 for
  scans; Python scripts `/tmp/opencode/rtype3/pw.py` (encoder/decoder),
  `ssread.py` (mGBA `.ss1` `gbAs` zlib RAM reader), `sspatch.py` (savestate word patcher),
  `enterfull.py` (XTEST password entry), `key.py`.
* Ghidra 12.1.4 via the `rea` MCP/CLI was tried, but the shared REA session was hijacked
  by another concurrent analysis, so all findings here rest on objdump + savestate RAM.
* Media: ≤20 screenshots were reviewed on disk; none are attached to this report.
* Legal: no ROM bytes or copyrighted assets are reproduced here — only hashes, addresses,
  algorithms, and codes authored/verified during this analysis.

## 10. Cleanup

All processes started for this engagement were stopped by PID (Xvfb :316, Openbox, mGBA),
generated `.sav`, `.ss1`–`.ss7` and the stray `cmds` file were removed from the ROM folder.
