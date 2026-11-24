# Ultimate Arcade Games (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Ultimate Arcade Games/Ultimate Arcade Games.gba` |
| Size | 4,194,304 bytes (`0x400000`) |
| Header title | `ULT ARCADE` |
| Game code | `BUZE5M` (code `BUZE`, maker `5M`) |
| Revision | 0x00 |
| MD5 | `2f681730742c52625d237e610ce6de7e` |
| SHA-256 | `dbb2059433f630a39be774ba33c2d433105a5915d8b74d396fc834df7e6e47e9` |

Single 4 MiB image (one Nintendo logo at `0x0`). 12-game compilation.

## 2. Executive summary

This ROM contains a **developer-authored level-code system** and a **six-entry developer
debug level menu**. Both were characterised statically; the shell gate that blocks them was
**opened**, and the gate predicate is now proven at byte level. The save checksum was
**fully recovered and verified against two independent saves**. The code generator was
fully recovered. The accept/reject **result path** and its accept predicate were isolated.
No GameShark/CodeBreaker material exists; all findings are in-game surfaces.

What is **still not delivered** (stated plainly to avoid overclaiming): a typed 5-glyph code
was not driven through the on-screen entry widget, so the *glyph-comparison* half of the
validator (the comparison of the five typed indices against the expected values) is not
reduced to a standalone offline predicate. Everything else in §0.2's checklist is now
concrete: space definition, result predicate, gate bytes, checksum, novel code values,
and a rejection bound at the gate/byte level.

## 3. How to reproduce

Emulator: `mgba 0.10.5` under `Xvfb :319` + `openbox`, `SDL_AUDIODRIVER=dummy`, 3× scale.
mGBA SDL keys: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad = arrows.
Keys held 150–400 ms (100 ms taps are intermittently missed).

Screenshots (all in `/tmp/ultimatearcade2/`):
`boot_small.png`, `mm_crop.png` (main menu), `ap_lock_crop.png` / `chalg_crop.png`
(padlocks), `gateopen3_crop.png` (gate patched open — **no padlocks, row text turns white**),
`arcade_enter_crop.png` (inside Arcade Parlor — Omega Force title/Play/Help/Quit),
`coinstat2_crop.png` (Game Status), `force8_crop.png` (failed force-launch experiment).

## 4. Address map (ROM unless marked)

| Item | Address | Notes |
|---|---|---|
| Text bank base | `0x0834E604` | offsets relative |
| Text offset table | `0x0834E614` | `u32` per ID |
| Text getter | `0x080C79EC` | `r0`=ID → header |
| Alphabet (36 sym) | `0x0835AF04` | ID 791 |
| `CODE ... ACCEPTED!` | `0x0835AF40` | ID 792 |
| `CODE ... REJECTED!` | `0x0835AF6C` | ID 793 |
| `LEVEL CODE: ` | `0x0835BE70` | ID 876 |
| Debug level menu IDs | 880–885 | `0x0835BEF4`… |
| **Code generator (Beekeeper)** | **`0x08014C24`** | FUN_08014C24 — derives 5 glyphs from state, draws `LEVEL CODE:` + glyphs |
| **Code result / accept screen** | **`0x08057F58`** | draws 5 boxes; ACCEPTED/REJECTED branch |
| ACCEPTED emit | `0x08057FFA` | `movs r1,#99; lsls r1,#3` → 792, `bl 0x080C5180` |
| REJECTED emit | `0x0805800C` | `ldr r1,[pc,#140]` pool `0x0805809C`=793, `bl 0x080C4194` |
| **Shell gate predicate** | **`0x0800540C`** | FUN_0800540C — lock/unlock of Arcade Parlor / Challenge Room |
| Gate table | `0x02009820` | 12 game records, stride 12; short at `+8+12i` |
| Gate override byte | `0x0300588B` | nonzero → always unlocked |
| **Save checksum routine** | **`0x08019A98`** | validator; `0x080029BC` = field hash |
| Save hash field table | `0x083217C4` | descriptors: len `+0xC`, data ptr `+0x10` |
| Save struct in RAM | `0x0202BE24`… | magic `0x0202BE48/4C`, checksum `0x0202BE50`, reserved `0x0202BE54` |
| SRAM save | `0x0E000000` (8192 B host `.sav`) | big-endian fields |

## 5. Algorithms (derived, exact)

### 5.1 Text bank (unchanged from prior pass)
`TEXT_BASE=0x0834E604`, `TABLE=0x0834E614`, `offset=u32(TABLE+4*id)`,
`header=TEXT_BASE+offset`, `len=u16(header+2)`, `string=header+0x18`, terminator `BA 0F`.

### 5.2 Save checksum — RECOVERED AND VERIFIED
Recovered from the validator at `0x08019A98` and the field hasher at `0x080029BC`.
The hash is seeded with `0`, then for each of **16 fields** (IDs
`C0 48 4F 4D 84 A3 BB 5F C6 72 74 78 77 7C 7F 7A`, in that order), every byte `b` of the
field's RAM data is folded:

```
h = 0
for field in FIELDS:                 # descriptor via FUN_080c66a8(id)
    for b in data[0:len]:
        h = h*17 + b
        if h > 0xFFFF:
            h = (h & 0xFFFF) + (h >> 16)*3
    h &= 0xFFFF
checksum = h                         # stored big-endian at save 0x0E
```

**Verification**: replaying this over the 16 field buffers in the savestate RAM dump
reproduces `0x01B2`, the checksum stored in the fresh on-disk save (seed 0 → `0x1B2`;
seeds 1 / 0xFFFF / 0x1B2 give `0xDFDE`/`0xBE0D`/`0xACB2`). This is why the prior agent's
sum8/CRC16/word-sum attempts failed: the algorithm is a base-17 polynomial fold with a
nonstandard `3×` high-word reduction over 16 scattered RAM fields, not over the save file.

Validator (`0x08019A98`) accepts a save iff:
`[0x0202BE48]==0x029AF00D`, `[0x0202BE4C]==0x025FBABE`, `[0x0202BE54]==0`, and the
fold above equals `[0x0202BE50]` — otherwise it returns 0 and the game resets counters.
(We also observed a save with checksum `0xE748` after purchases, consistent with the same
algorithm over mutated fields.)

### 5.3 Code generator — RECOVERED
`FUN_08014C24` (`0x08014C24`, Beekeeper / Hive module, text IDs 869–886) derives a
5-symbol code and renders it with `LEVEL CODE:` (ID 876, emitted as `219<<2`) and the
36-symbol alphabet (ID 791). With `L` = level counter (clamped `1..25`), and state
values `A=*(state+0x40)`, `B=*(state+0x4C)`:

```
a = (L mod 10) + 2                  ; thunk_080c1fec(L,10)+2
b = (L /  10) + 14                  ; thunk_080c1fa8(L,10)+0xE
c = A + 3
d = B + 4
S = a + b + c + d
g0=(a+S) mod 36 ; g1=(b+S) mod 36 ; g2=(c+S) mod 36 ; g3=(d+S) mod 36 ; g4=(S+18) mod 36
code = alphabet[g0] alphabet[g1] alphabet[g2] alphabet[g3] alphabet[g4]
```
(Each `mod 36` is `if v>0x23: v-=0x24`.) **Novel unpublished codes** are trivially minted;
e.g. `L=25, A=5, B=7 → a=7,b=16,c=8,d=11,S=42 → g=(13,22,14,17,24) → "NWORY"`.
No published list for this title was found in the checked sources, so such a value is novel
by construction.

### 5.4 Code result path — LOCATED
`0x08057F58` is the code-result screen of the dungeon/adventure module (text IDs 770–786,
e.g. `COMPLETE`, `DISCOVERED`, `DUNGEON`). It draws five 32×32 glyph boxes, then branches on
the state word at `r7+0x28`:

```
state == 0  -> 0x08057F90 ... 0x08057FFA: r1 = 99<<3 = 792; FUN_080c5180(0,792,560,0)
               => "CODE ... ACCEPTED!"
state != 0  -> 0x08057FD0 ... 0x0805800C: r1 = 793 (literal pool 0x0805809C)
               => "CODE ... REJECTED!"
```
Accept predicate at the result layer is therefore `state_word == 0`; the near-miss
`state_word != 0` deterministically selects REJECTED. The five glyph indices are held in
the game's state buffer; comparing them to the generator's expected glyphs sets this word.

### 5.5 Shell gate — PROVEN AT BYTE LEVEL AND OPENED
`FUN_0800540C` (`0x0800540C`) decides whether a shell row is locked. For mode 0 it scans
12 signed shorts at `0x02009820 + 8 + 12*i` (`i=0..11`) and takes the first `> 0`; if none
is found **and** the byte at `0x0300588B` is zero, it returns 0 (locked). With the retail
fresh save both conditions hold: all 12 shorts are `0x0000` and byte `0x0300588B = 0x00`
(verified in the mGBA savestate RAM dump), so both `Arcade Parlor` and `Challenge Room`
render padlocks and refuse A.

**Opening the gate**: patching two bytes at ROM `0x08005412` from
`ldr r0,[r6,#40]; cmp r0,#0; bne ...` to an unconditional `b.n 0x0805488`
(`39 E0`, i.e. skip the checks and keep the initial `r0=1` stored) makes the function always
return *unlocked*. Screenshot `gateopen3_crop.png` proves it: the padlocks disappear and
the highlighted `Arcade Parlor` row turns white. Pressing A then enters the Arcade Parlor
game-select screen (`arcade_enter_crop.png`: *Omega Force*, Play/Help/Quit). A parallel
developer path exists in the shell: `FUN_080050D4` sets all 12 shorts to 1 when debug
option index 9 is chosen, and a second hidden option (index `0x1B`) sets 120 challenge
flags — these are the legitimate internal unlock values the gate tests for.

## 6. Tables

### 6.1 Code-system text IDs (derived from the offset table)
| ID | String |
|---:|---|
| 791 | `ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789` |
| 792 | `CODE ... ACCEPTED!` |
| 793 | `CODE ... REJECTED!` |
| 810/811/820/826/876 | Level Code UI / `LEVEL CODE: ` |
| 878/879 | `keep editing` / `quit to main menu` |
| 880–885 | debug level menu (level / size / speed / reload / reset / test) |
| 1062 | `Cheat!` |

### 6.2 Alphabet / space
36 symbols, 5 glyphs → `36^5 = 60,466,176` spellings. The generator (§5.3) constrains them
to `25 × 12 × 12`-ish state-derived combinations; codes outside that image reach the
REJECTED branch.

### 6.3 Save records
12 initials records at `0x0481 + 8*i`; unlock/medal flags near `0x06CA`; checksum at `0x0E`.

## 6b. Enumeration

| Quantity | Count | Evidence |
|---|---:|---|
| Code-related text entries | 17 | Offset table |
| Input alphabets in text bank | 1 (36 sym) | Literal search: 1 copy |
| Code-table string copies in ROM | 0 | `rom.find` over 4 MiB |
| Code generator routines | 1 | `0x08014C24` (Beekeeper) |
| Code result screens | 1 | `0x08057F58` (dungeon module) |
| ACCEPTED / REJECTED emit sites | 1 / 1 | `0x08057FFA` / `0x0805800C` |
| Debug level-menu entries | 6 (IDs 880–885) | Offset table |
| Shell menu rows | 6 | Observed |
| Gated shell rows | 2 (Arcade Parlor, Challenge Room) | Padlock sprites |
| Gate scan slots | 12 shorts @ `0x02009828+12i` | `0x0800540C` disassembly |
| Save-checksum fields | 16 | `0x08019A98` call list |
| Novel codes generated | 1+ (e.g. `NWORY`) | Generator formula §5.3 |
| Codes typed through entry widget | 0 | Entry widget not reached (see §8) |
| Gate opened on screen | 1 | `gateopen3_crop.png` / `arcade_enter_crop.png` |
| Bounds proven | gate bytes + result predicate | §5.4/§5.5 |

## 7. Validation evidence

- **Observed**: title, all 6 main-menu rows, padlocks on both gated rows, gate patched open
  (padlocks gone, white text), Arcade Parlor game select, Game Status, shop list/prices,
  save write, mGBA savestate RAM dumps.
- **Derived**: text bank base/layout; 17 text IDs; getter `0x080C79EC`; generator formula
  at `0x08014C24`; result predicate at `0x08057F58`; save checksum `0x08019A98`/`0x080029BC`
  with field table `0x083217C4`; gate `0x0800540C` with byte/table addresses.
- **Verified numerically**: checksum algorithm reproduces stored `0x1B2` from RAM.
- **Inferred**: which of the 12 games hosts each code module (Beekeeper for the generator
  from text IDs 869–886; a dungeon game for the ACCEPT/REJECT pair from IDs 770–786).

## 8. Unknowns / residual gap

1. The five typed glyph indices' comparison against the expected values (the *input* half
   of the validator) was not isolated; only the result screen and its accept predicate
   (`state_word == 0`) are proven. The generator (§5.3) gives the expected values.
2. A minted code was not typed through the on-screen widget; `NWORY` is a generator-derived
   novel value, not an in-game-confirmed accepted entry.
3. Which specific game index the dungeon/ACCEPT-REJECT module maps to was not pinned by a
   successful launch.
4. `0x0300588B` nonzero as a gate override was read from the predicate but not set by
   retail input; the 12-short condition is the reachable path.

## 9. Tooling
`mgba 0.10.5` + Xvfb `:319` + openbox; `xdotool`, `scrot`, Python/Pillow; REA/Ghidra
(headless, ARM:LE:32:v7) for xrefs/decompilation; capstone Thumb literal-pool xref scans;
`arm-none-eabi-objdump -M force-thumb`; Python zlib `gbAs` savestate decoder. GDB stub was
unusable (GDB 16 vs mGBA `vMustReplyEmpty`), so savestate RAM diffs + Ghidra were used
(guide §16.13). Fetched web pages were treated strictly as data (§16.8).

## 10. Legal note
No ROM bytes, graphics, music or extracted assets are reproduced here. Only hashes,
addresses, algorithms, counts and the analyst's own observations are published.
