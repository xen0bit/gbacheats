# Dark Arena (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Dark Arena/Dark Arena.gba` |
| Size | 8,388,608 bytes (8 MiB) |
| Header title | `DARK ARENA` |
| Game code | `ADAE` (US) |
| Maker | `5G` |
| Software version | 0 (`Rev.00`) |
| Entry word | `0xEA00002E` (stock ARM `b 0x080000C0`) |
| Complement byte | stored `0x21`, calculated `0x1D` |
| Header checksum | `0x0000` |
| MD5 | `e86c23f445b069b1a0bc27dda5f638b8` |
| SHA-1 | `7d7c2f47affef4b69094536497a9a28db7f347bb` |
| SHA-256 | `4e7cbae8e87b71f851e3f3e0ae9f79324f63172ebd3b4123a45585db47a880a7` |

Only one GBA header (full 156-byte Nintendo logo at file `0x4`) is present. The
entry point and first 4 KiB are the stock crt0; there is no cracktro/trainer
string (`SUNHORS`, `MODE7`, `CRC BANDIT`, `trainer` all absent). The header has
been rebuilt: the official header checksum is zero and the complement byte does
not match the computed value. This is a header artifact, not a gameplay patch.

## 2. Executive summary

Dark Arena's password system is a **closed two-table lookup**, not a
checksum/generator system.

* An 8-character password is entered on screen state `0x19`.
* The validator compares all 8 bytes against one of two 56-slot tables
  (9-byte stride: 8 characters + `@` terminator):
  * normal table `0x08624A19`, used when bit 6 of the special-flag byte is clear;
  * cheat-mode table `0x08624C11`, used when bit 6 is set.
* Indices `0..45` encode level/difficulty: `0` = blank (go to difficulty
  select), `1..15` = easy, `16..30` = medium, `31..45` = hard; the low nibble is
  the 0-based level, and level `15` is the credits/end branch.
* Indices `46..54` are special flags. Index 46..53 XORs one bit of
  `0x03003F43`; index 54 writes `0xBF` (all special flags except cheat mode).
* The input alphabet is generated in code, not stored as a string:
  in normal mode vowels `A E I O U` are skipped (22 symbols: space + 21
  consonants); in cheat mode all 26 letters are allowed (27 symbols).
* The mission-complete password is looked up from the same normal table with
  `index = {1,16,31}[difficulty] + level`; there is no encoder/checksum.

All 108 non-blank table entries are present verbatim in published lists
(GameFAQs, SuperCheats, GameGenie, Cheat Code Central). The only accepted input
that appears in **no** published list is the all-space entry at index 0 (the
"empty password"), which is a real table slot and was entered and RAM-verified.
One published variant is wrong: `SFX` is rejected; the ROM accepts `SFX TEST`.

## 3. How to reproduce

Emulator: mGBA SDL, 3× scale, under `Xvfb :280`; `SDL_AUDIODRIVER=dummy`.

Keymap used: A=`x`, B=`z`, Start=`Return`, Select=`BackSpace`, L=`a`, R=`s`,
D-pad=arrows. Hold keys 150–250 ms; the first key after a state transition can
be swallowed, so always re-read the state byte.

Menu path to the password screen:

1. Boot. State `0x01` (boot) → press Start → `0x03` → press Start → `0x15`
   (title) → press Start → `0x16` (main menu, 3 items).
2. Main menu selection is `0x03002038`: `0` = single player, `1` = link,
   `2` = options. Choose `0` and press A → state `0x19` (password screen).
3. Type the 8 characters with Up/Down and Right; A/Start submits, Select clears,
   B returns to the main menu.

Password test loop used: save a state at `0x19`, type, press A, save, decode the
mGBA `.ss1` (`gbAs` chunk is zlib-compressed; IWRAM at raw offset `0x19000`,
EWRAM at `0x21000`). A rejected code goes to state `0x1A` and copies the typed
bytes to the input buffer; an accepted level code goes to `0x42`.

Key tests (all entered through the real UI):

| Input | Result |
|---|---|
| `CRSDRPLS` | state `0x42`; `0x03003F40 = 01 01 01 00` (level 1, difficulty 1) |
| `CRSSWRLR` | state `0x42`; `0x03003F40 = 0E 01 04 00` (level 14 = level 15, hard) |
| `GDFGHTBL` | state `0x21`; `0x03003F40 = 0F 01 01 00` (credits slot) |
| `KNGHTSFR` | state stays `0x19`; flag byte `0x01` |
| `NRYRDDS` | state `0x19`; flag byte `0x40` (cheat mode) |
| `S X N` | state `0x19`; flag byte `0xBF` |
| `CRSDRPLS` in cheat mode | rejected, state `0x1A` |
| `CRSDRPLX` in normal mode | rejected, state `0x1A`, input preserved, flags unchanged |
| `A` after cheat mode | accepted, `0x03003F40 = 01 01 01 40` |
| `ALL` in cheat mode | flag byte `0xBF` |
| `PWORD` in cheat mode | flag byte `0x00` (cheat mode toggled off) |
| `SFX` in cheat mode | rejected, state `0x1A` (published typo) |
| `SFX TEST` in cheat mode | accepted, flag byte `0xC0` |
| Empty field (8 spaces) | state `0x1B` (difficulty select); HARD → `0x03003F40 = 00 01 04 00` |

No GameShark/CodeBreaker/memory-edit code is reported or required.

## 4. Address map

File offset to ROM address is `0x08000000 + offset`.

| Item | Address |
|---|---|
| Normal password table (56 × 9 bytes) | `0x08624A19` (file `0x624A19`) |
| Cheat-mode password table (56 × 9) | `0x08624C11` (file `0x624C11`) |
| Password screen draw | `0x08006AE5` |
| Password input + validator | `0x08006B6D` |
| 8-byte compare loop | `0x08006C2C`–`0x08006C5A` |
| Index bound (`cmp r3,#0x37`) | `0x08006D42` |
| Level/difficulty split | `0x08006C5C`–`0x08006C9C` |
| Special flag toggle / 0xBF write | `0x08006CD4`–`0x08006D00` |
| Difficulty screen draw/input | `0x08006D71` / `0x08006E11` |
| Mission-complete password lookup | `0x08007166`–`0x080071A6` |
| Screen-descriptor table (state → handlers) | `0x08623F2C`, stride `0x14`, 5 words/entry |
| Input buffer (8 bytes) | `0x03002010` |
| Display buffer (8 bytes) | `0x03002060` |
| Cursor 0..7 | `0x0300209C` |
| Level / mode / difficulty / special flags | `0x03003F40` / `41` / `42` / `43` |
| Options byte | `0x03003F44` |
| Menu selection | `0x03002038` |
| Screen state | `0x030020A4` (mirror `0x03002034`) |
| Level record pointer | `0x0300227C` → `0x030022D0`; automap word at `+0x30` |
| Level-exit callback cell | `0x03003F70` |
| Version string | `0x0801C1F8` (`"VERSION 1.07@"`) |
| Version secret check | `0x08006408` (key mask `0x300` = L\|R) |
| SFX-test flag test | `0x0800686E` (flag bit 7) |
| SFX sound counter | `0x030020A0` |
| Sound play entry | `0x08014E5C` |
| Level-skip Select check | `0x0800739C`–`0x080073B4` |
| Level-exit callback (skip) | `0x0800A53D` |
| Pause draw / input | `0x080074D1` / `0x080075A9` |
| Map draw / input | `0x08007335` / `0x08007365` |
| Quit-confirm draw / input | `0x08007751` / `0x080077BD` |

## 5. Algorithm

### 5.1 Input

```
buf = 0x03002010, 8 bytes, initialised to 0x20
disp = 0x03002060, cursor = 0x0300209C (0..7), length = 0x0300209C
normal alphabet (bit6 clear):
    space, B C D F G H J K L M N P Q R S T V W X Y Z   (22 symbols)
cheat alphabet (bit6 set):
    space, A B C D E F G H I J K L M N O P Q R S T U V W X Y Z (27 symbols)
Up advances, Down retreats, Right/Left move the cursor,
Select fills all 8 cells with spaces, A/Start submits, B returns to state 0x16.
```

The vowel skip is at `0x0800A148`–`0x0800A16A`: after storing the incremented
symbol, it rejects `A/E/I/O/U` unless the entry mode argument (`r6`, passed by
`0x08009FEC`) is non-zero. The password screen passes 1 when cheat-mode bit 6 is
set and 0 otherwise, so the published one-letter cheat codes `A`, `E`, `I`, `O`
are only typeable after `NRYRDDS`.

### 5.2 Validator (reimplementation)

```
flags = mem[0x03003F43]
base  = (flags & 0x40) ? 0x08624C11 : 0x08624A19
for i in 0..55:
    if memcmp8(buf, base + 9*i) == 0:
        if i == 0:                       # 8 spaces
            state = 0x1B                 # difficulty screen
            return ACCEPT
        if i <= 45:
            if i <= 15: diff=1; lvl=i & 15
            elif i <= 30: diff=2; lvl=i-15
            else:        diff=4; lvl=i-30
            mem[0x03003F40] = lvl
            mem[0x03003F42] = diff
            if lvl == 15:
                state = 0x21             # end/credits branch
            else:
                state = 0x42             # start level lvl+1
            return ACCEPT
        bit = i - 46
        if bit == 8:                     # index 54: S X N / ALL
            flags = 0xBF
        else:
            flags ^= (1 << bit)          # indices 46..53
        mem[0x03003F43] = flags
        clear_input()
        return ACCEPT
state = 0x1A                             # INCORRECT PASSWORD
return REJECT
```

The two blank slots are index 0; index 55 of each table is nine `0x00` bytes and
is unreachable from the UI (the input buffer is always space-initialised), so it
is a dead comparison slot, not a code.

### 5.3 Password display

```
base = {1:1, 2:16, 4:31}[mem[0x03003F42]]
idx  = base + mem[0x03003F40]
copy8(disp, 0x08624A19 + 9*idx)
copy8(buf , 0x08624A19 + 9*idx)
```

This is why the mission-complete screen always shows the normal table's code
even in cheat mode. Observed: after the level-skip test, level byte 1 produced
`CRSDRPLS` in `0x03002010`.

### 5.4 Special flag bits (`0x03003F43`)

| Bit | Written by (normal table) | Effect |
|---:|---|---|
| 0 | `KNGHTSFR` (idx 46) | all keys |
| 1 | `LMSPLLNG` (47) | all maps |
| 2 | `THRBLDNS` (48) | all weapons |
| 3 | `NDCRSDRT` (49) | infinite ammo |
| 4 | `HLGNDSBR` (50) | infinite health |
| 5 | `NFTRWLLH` (51) | level skip (map + Select) |
| 6 | `NRYRDDS` (52) | cheat-mode table select |
| 7 | `CRSDR` (53) | SFX test flag |
| 0..7 | `S X N` (54) | write `0xBF` (all except bit 6) |

The cheat table maps `KEYS MAPS WEAPONS AMMO HEALTH SKIP PWORD SFX TEST ALL` to
indices 46..54, so `PWORD` is a bit-6 toggle and `ALL` writes `0xBF`.

## 6. Tables

### 6.1 Normal table, `0x08624A19`, index × 9

Index 0 is eight spaces. Easy (index = displayed level 2..15, then credits):

```
 1 CRSDRPLS   2 TKMWTHYB   3 TTLLSFRT   4 STCRSTRD   5 NTLVMLNW
 6 NTTRDTNY   7 RQSTMWTN   8 GTSTNDBY   9 YRSDTFGH  10 TWTHYVRS
11 THYRCLLN  12 GHVTBTHR  13 HLYLNDHS  14 TBFRFGHT  15 GDFGHTBL (credits)
```

Medium (16..30):

```
16 VWHTSRGH  17 TCRSDRLR  18 DFRLMWTH  19 LLYRMGHT  20 WRMRCHNG
21 TLNDFRFR  22 MHMNNCNS  23 YWHLLRTR  24 NFRCHRSN  25 DMSSKWLL
26 TKRRVNGN  27 PGNFRMTF  28 STWCHRST  29 NSRCMNGW  30 THSWRDSH (credits)
```

Hard (31..45):

```
31 LDNHGHNT  32 DBYFTHND  33 CSSRCNHT  34 HNSWLLSN  35 TSTRSTLR
36 STNDRDSW  37 LLRSCRSS  38 LNDTBTTL  39 SRCNHRDS  40 WFLLWRWR
41 RRKNGNWR  42 DNTFGHTW  43 CRRYSGNF  44 CRSSWRLR  45 DSFNGLND (credits)
```

Specials (46..54): `KNGHTSFR`, `LMSPLLNG`, `THRBLDNS`, `NDCRSDRT`,
`HLGNDSBR`, `NFTRWLLH`, `NRYRDDS` (7 chars + space), `CRSDR` (5 + 3 spaces),
`S X N` (internal spaces).

Index 55: `00 00 00 00 00 00 00 00 00` (dead slot).

### 6.2 Cheat table, `0x08624C11`, index × 9

Index 0 is eight spaces. Easy 1..15: `A`..`O` (single letter + 7 spaces);
medium 16..30: `AA`..`OO`; hard 31..45: `AAA`..`OOO`. Index 15/30/45 are the
credits branch. Specials 46..54: `KEYS`, `MAPS`, `WEAPONS`, `AMMO`, `HEALTH`,
`SKIP`, `PWORD`, `SFX TEST`, `ALL` (space-padded to 8). Index 55 is nine
`0x00` bytes.

### 6.3 Screen states observed

| State | Screen | Draw / input |
|---:|---|---|
| `0x15` | title (`PRESS START TO CONTINUE`) | `0x080061E5` / `0x08006371` |
| `0x16` | main menu (3 items) | `0x080063F9` / `0x0800644D` |
| `0x17` | options (5 items) | `0x080065A1` / `0x08006711` |
| `0x18` | credits scroll | `0x08006969` / `0x080069FD` |
| `0x19` | enter password | `0x08006AE5` / `0x08006B6D` |
| `0x1A` | incorrect password | `0x08006EE1` / `0x08006F09` |
| `0x1B` | select difficulty (3 items) | `0x08006D71` / `0x08006E11` |
| `0x1C` | link mode | `0x08007975` / `0x08007A6D` |
| `0x1D` | link lobby / no players | `0x08007B09` / `0x08007B35` |
| `0x21` | end/credits branch | `0x0800927D` / `0x080092AD` |
| `0x3C` | mission complete + `PASSWORD:` | `0x08006F31` / `0x080071CD` |
| `0x3E` | quit confirm (NO/YES) | `0x08007751` / `0x080077BD` |
| `0x3F` | pause (MAP/CONTINUE/QUIT/BRIGHTNESS) | `0x080074D1` / `0x080075A9` |
| `0x40` | map viewer | `0x08007335` / `0x08007365` |
| `0x42` | level start/loading | — |
| `0x43` | active gameplay | — |

Pause selection order was measured with `0x03002038`: `0` = MAP (to `0x40`, only
if the automap bit is set; otherwise the label is `MAP (NOT AVAILABLE)`),
`1` = CONTINUE (to `0x43`), `2` = QUIT GAME (to `0x3E`; `YES` returns to
`0x16`), `3` = BRIGHTNESS (adjusts bits 2–3 of `0x03003F44`).

Options: `0` MUSIC (bit 5 of `0x03003F44`), `1` SOUND FX (bit 4),
`2` BRIGHTNESS (bits 2–3), `3` DEPTH SHADING (bit 6), `4` CREDITS (to `0x18`).

## 6b. Enumeration

### Space definition

* Fixed 8-byte input, exact `memcmp` against 9-byte-strided strings. No checksum,
  no generator, no wildcard, no normalisation.
* Normal table: 56 slots; slot 55 is 9 NUL bytes and unreachable; slots 0..54
  are 55 usable strings (1 blank + 45 level + 9 special).
* Cheat table: the same 56 slots, 55 usable strings (1 blank + 45 level +
  9 special).
* Unique accepted 8-byte strings: **109** = 54 normal-only + 54 cheat-only +
  the all-space string shared by both tables at index 0.
* Naive typed input space: normal `22^8 = 54,875,873,536`; cheat
  `27^8 = 282,429,536,481`. Only the 55 table strings per mode are accepted, so
  the accepted density is `55 / 22^8` and `55 / 27^8`.
* Published coverage: all 108 non-blank strings appear verbatim in the
  GameFAQs / SuperCheats / GameGenie / Cheat Code Central lists. The blank
  (index 0) is absent from every published list.

### Novel code (not in any published list)

The closed-table system has exactly one accepted input outside the published
lists: the **8-space / empty password**, table index 0 of either table.

* Generated value: eight `0x20` bytes (enter nothing; A/Start).
* Entry: state `0x19`, empty field, A. Observed state `0x1B` (difficulty
  select), `0x03002038 = 0`, `0x03003F40 = 00 01 01 00`.
* To exercise the slot's full effect, HARD was selected on the difficulty
  screen (Down twice; `0x03002038 = 2`) and confirmed with A. Observed:
  state `0x42`, `0x03003F40 = 00 01 04 00` → level byte 0 (level 1), difficulty
  byte 4 (hard). The walkthrough mentions pressing A on an empty field as the
  level-1 shortcut, but no published code list records the eight-space password
  as a table entry; the index-0 slot, its two-table presence and the exact
  difficulty word are the unpublished part.
* The same empty input is index 0 of the cheat table; with flag bit 6 set it
  also reaches the difficulty screen (observed after the accidental empty
  submit while cheat mode was on).

### Bounds proven by rejection (all through the real entry screen)

| Test | Why out of bounds | Observed |
|---|---|---|
| `CRSDRPLX` | one character wrong; valid alphabet and length | state `0x1A`; input preserved; flags `0x00` |
| normal `B` | table has no `B` in normal mode (and `A` is not typeable) | state `0x1A`; input `B       ` |
| cheat `P` | single-letter codes exist only `A..O` | state `0x1A`; input `P       ` |
| cheat `CRSDRPLS` | normal-only code; cheat table has no such entry | state `0x1A`; input preserved; flags `0x40` |
| cheat `SFX` | published variant, but table is `SFX TEST` | state `0x1A`; input `SFX     ` |
| index 55 (nine NULs) | unreachable: input is space-initialised and only letters/space are typeable | dead slot; not a code |

Negative result for a second format: the validator has only the two base
pointers above, selected solely by flag bit 6. No other table or generator was
found; the mission-complete display is a table copy, not an encoder.

Reconnaissance bounds: `strings -t x -n 4` produced 114,375 lines. Keyword
counts over that dump were: `password` 4 (the four UI strings `ENTER PASSWORD`,
`PRESS SELECT TO CLEAR PASSWORD`, `PASSWORD:`, `INCORRECT PASSWORD`), `cheat` 0,
`debug` 0, `secret` 1 (story text), `unlock` 0, `hidden` 0, `warp` 0, `level` 4,
`mission` 2, `code` 3 (`PROGRAM CODE`, `CODE RED`, the Shin'en audio banner),
`test` 4 (`TESTING` ×2, `TEST LABS`, `SFX TEST`), `select` 4. The two `god` hits
are compressed-data noise. There is no stored alphabet string; the input
alphabet is generated by the skip-vowel loop. Published literals were checked
against the ROM table: GameFAQs returned HTTP 403 to direct fetch, so its lists
were read from search snippets plus the SuperCheats, GameGenie and Cheat Code
Central mirrors; every non-blank ROM entry matched one of those lists, and the
one divergent published variant (`SFX`) was tested and rejected.

## 7. Validation evidence

**Observed (emulator + RAM reads):**

* Every accepted/rejected result in §3 and §6b (state byte, input buffer
  `0x03002010`, result word `0x03003F40..43`).
* Level code mapping: index 1 → `01 01 01`, index 44 → `0E 01 04`, credits
  index 15 → `0F 01 01` and state `0x21`.
* Flag toggles: `KNGHTSFR`→`01`, `NRYRDDS`→`40`, `S X N`→`BF`, `ALL`→`BF`,
  `PWORD`→`00`, `SFX TEST`→`C0`, `CRSDR`→`80`, `NFTRWLLH`→`20`.
* Vowel rule: normal Up from space produces `B`; cheat-mode Up produces `A`.
* Input buffer remains 8 spaces at boot/reset; Select clears to spaces.
* Version secret: with L held while pressing Start at `0x15`, the main-menu
  frame changes a block of the lower-right text/VRAM layer (first differing
  byte at text-buffer offset `0x884E`); the only added draw in that frame is
  the code's `x=0xE2, y=0x90` draw of `VERSION 1.07`.
* Password display: after advancing one level, `0x03002010` contained
  `CRSDRPLS` (normal table index 1).
* Pause/menu walking: title `0x15`, main `0x16` (3 items), options `0x17`
  (5 items), credits `0x18`, password `0x19`, incorrect `0x1A`, difficulty
  `0x1B` (3 items), link `0x1C`/`0x1D`, pause `0x3F` (4 items), quit confirm
  `0x3E`, map `0x40`, mission complete `0x3C`, end `0x21`, gameplay `0x43`.
* Level-skip path: with the automap bit forced to `0x4D00` in a savestate,
  pause→MAP (`0x40`) + Select produced state `0x3C` (mission complete); A then
  started state `0x42` with level byte incremented 0→1.

**Derived (instruction sequence):**

* Validator model, table selection by bit 6, index→level/difficulty split,
  special-bit XOR and 0xBF write (`0x08006B6D`–`0x08006D00`).
* Display lookup `{1,16,31}[difficulty] + level` and table copy
  (`0x08007166`–`0x080071A6`).
* Version secret condition: `ldrh [0x03000ED8+6] & 0x300` then draw string
  `0x0801C1F8` at `x=0xE2,y=0x90` (`0x08006408`–`0x08006422`).
* Level skip: the map viewer's Select branch at `0x0800739C`–`0x080073B4`
  tests flag bit 5 and would install callback `0x0800A53D` at `0x03003F70`.
  In the observed run Select on the map moved directly to state `0x3C`
  (mission complete) while `0x03003F70` still read `0x08005FD5`, so the exact
  hand-off between that callback cell and the `0x3C` transition is not
  resolved; the ROM's own Select input and the next-level result are observed.
* SFX test: SFX off→on with flag bit 7 set increments counter
  `0x030020A0` (0..0x5E) and calls the sound engine (`0x08006848`–
  `0x08006898`).
* Options bits: `0x03003F44` bit 5 music, bit 4 SFX, bit 6 depth, bits 2–3
  brightness (`0x080067D8`, `0x08006848`, `0x080068BE`, `0x08006920`).

**Inferred:**

* The gameplay consumers of the keys/maps/weapons/ammo/health bits were not
  played through; the bits and their writers are observed, but each downstream
  check was not traced.
* The SFX test's actual audio sample was not audible (dummy audio driver); the
  flag and the counter/sound call are derived. In the counter test the counter
  was already `1` and did not increment across one off→on cycle, so the audible
  result is inferred, not observed.
* The in-game way to set the automap bit (`0x030022D0+0x30` bit `0x100`) is a
  map pickup that was not played; the bit was forced in a savestate only to
  exercise the Select skip. The Select input and the level-complete → next-level
  effect are the ROM's own.

## 8. Unknowns

* Exact in-game trigger that sets the automap word bit `0x100` on each level.
* Perk consumers for each special bit (the flags are proven, the gameplay
  effects are documented by the published lists, not replayed here).
* Whether any level places the map pickup before the pause menu is first
  available.
* The game-over/mission-failed outcome screen was not driven to completion; its
  strings (`MISSION FAILED`, `TRY AGAIN?`) and the `0x3C` retry/password path
  are present, but no code surface differs there.

## 9. Tooling

* `mGBA` SDL (`-3`) under `Xvfb :280` + `openbox`, `SDL_AUDIODRIVER=dummy`.
* `xdotool` for held key events; savestates `Shift+F1`, load `F1`.
* Python 3 scripts in `/tmp/opencode/darkarena`:
  * `typepass.py` — types a password with the correct 22/27-symbol alphabet;
  * `dumpstate.py` — decodes the `.ss1` `gbAs` zlib chunk and prints state,
    buffers, flags and selector;
  * `patchstate.py` — byte-patch helper used only for the labelled automap-gate
    and SFX-flag experiments.
* `capstone`/`arm-none-eabi-objdump -M force-thumb` for the validator and
  screen-handler disassembly; raw BL/pointer scans for cross-references.

## 10. Legal note

No ROM, graphics, audio or other copyrighted asset is redistributed here. Only
addresses, algorithms, flag layouts and the short published password strings
are documented.
