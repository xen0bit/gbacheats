# Battle B-Daman: Fire Spirits! (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Battle B-Daman: Fire Spirits!/Battle B-Daman: Fire Spirits!.gba` |
| Size | 8,388,608 bytes (8 MiB, `0x800000`) |
| Header title | `BB-DAMA2FIRE` |
| Game code / maker | `BBME` / `EB` |
| Version | 0 |
| Header complement (`0xBD`) | `0x98` (valid) |
| Header checksum (`0xBE`) | stored `0x0000`, computed `0xFA98` — **field zeroed/patched** |
| Entry branch (`0x00`) | `0xEA00002E` (ARM branch to `0x080000C0`) |
| Fixed `0x96` (`0xB2`) | present |
| MD5 | `e1b689a5776e8e35840e3a676fa11853` |
| SHA-1 | `d57084c399bbd4b37d145b712ff6ca22db9b1c49` |
| SHA-256 | `14c61976e2b634640ab60a38f7baaac3ae3b7de8b6d142d17321afc89138ff14` |

A scan for the 156-byte Nintendo logo finds exactly one header (file offset `0x00`): a single
GBA image, no multiboot/second header. The build banner
`BATTLE B-DAMAN 04/06/23 18:00` is at file `0x3B618C` (ROM `0x083B618C`).
No other patch was detected; the header checksum is the only anomalous field.

## 2. Executive summary

The game has one developer-intended code system: **Zero Codes**, entered at
*Parts Shop → Input Zero Code*. It is a plaintext table of **23 NUL-terminated phrases**
stored in the game's custom 8-bit text encoding at ROM `0x083FC2C3` (pointer table
`0x083FCC3C`). Each phrase is mapped by index to a reward list at `0x083BD484`
(type 1 = B-Dabucks, type 2 = part id, type 3 = B-Daman id). Comparison is an
**exact, case-sensitive, full-string match**; the "already entered" flag prevents
re-collection.

The entry field has a **pass-dependent length cap**. The pass-level byte
`0x0203A8EC` indexes a table at `0x080CF720` = `{10, 13, 15}`; the resulting maximum
is stored at `0x0203CB21` and enforced when the field is full. At the starting
Bronze pass the field accepts exactly 10 characters, which is why only the six
Bronze phrases (all exactly 10 characters) are reachable at that point. Silver
phrases are 12–13 characters and Gold phrases 15, matching the 13/15 caps.

The published lists (GameFAQs archive, SuperCheats) contain **all 23 table entries**;
the only published code absent from the ROM is `HIDDEN SWORD` (11 chars, absent
literally, and its 10-char prefix is rejected). Consequently **the entire accepted
space is published**: there is no unpublished Zero Code to mint. This report proves
that as a closed enumeration rather than a failed search (see §6b).

A developer debug-menu subsystem also survives in the ROM (mode-select labels,
`MODE DEBUG`, `YOSHIDA DEBUG`, `SHOP DEBUG`, `ALL SET`, `SET PARTS`, … at
`0x083BD918`–`0x083BDBF1`, menu table `0x083BDCEC`). It is not reachable from the
retail menus or from the boot button combinations tested (§8).

## 3. How to reproduce

Emulator: mGBA (SDL) 0.10.x under Xvfb `:178`, `SDL_AUDIODRIVER=dummy`, 3× scale.

Default mGBA SDL keymap used: A = `x`, B = `z`, Start = `Return`, Select =
`BackSpace`, D-pad = arrows, L/R = `a`/`s`.

Exact path used (US ROM, fresh boot):

1. Title screen (`PUSH START`) → `Return`.
2. Main menu: `B-Daworld` / `System Settings`. Choose `B-Daworld` (`x`).
3. Play/skip the intro (A advances dialogue; the intro tutorial battle is part of
   the story). After the town loads, the top tabs are `MOVE / TALK / TOOLBOX / HINT`.
4. `MOVE` → location list → `Parts Shop`.
5. Shop menu: `Buy Parts`, `Sell Parts`, `Input Zero Code`.
6. `Input Zero Code` opens the 6×15 on-screen keyboard (screenshot
   `Battle B-Daman Fire Spirits - zero code keyboard.png`).
7. Spell the code, move to `END` (bottom-right) and press A.

Savestate used for the tests: `game.ss3` (the empty Zero Code screen, Bronze pass).
`game.ss2` is the shop menu. The debugger tests used the mGBA command-line
debugger (`mgba -d`); no savestate was modified.

Codes entered and effects observed (all screenshots next to this report):

| Code | Result |
|---|---|
| `GO YAMATO!` | `You received 1500 ₿!` |
| `HEY TOMMI!` | `You received 2000 ₿!` |
| `B-DAFIRING` | `You received 3000 ₿!` |
| `SHOOT IT!!` | `You got Saber Barrel!`, `L-Shield Stand!`, `R-Shield Stand!` |
| `THE BOTTLE` | `You got PlasticBottle Mag II!` |
| `HARD TEETH` | `You got Balance Core!` …; B-Daman collection becomes 2/2 with `Cheesy Mouse Special` |

Rejection/negative tests: `REVIVAL OF` (the exact 10-char prefix of a 15-char
table entry) → `Error! Zero code is incorrect.`; `go yamato!` → rejected;
`GOYAMATO!` → rejected; `REVX`, `ZZZZ`, `HIDDEN SWO` → rejected; entering
`HARD TEETH` twice → `That Zero Code has already been entered.`

## 4. Address map

All addresses are ROM `0x08xxxxxx` unless marked EWRAM.

| Address | Size | Meaning |
|---|---:|---|
| `0x083FC2C3`–`0x083FC3FC` | 313 | 23 NUL-terminated Zero Code phrases (custom text encoding) |
| `0x083FCC3C`–`0x083FCC97` | 92 | 23 × u32 pointers to the phrases (NULL at `0x083FCC98`) |
| `0x083BD484`–`0x083BD4DF` | 92 | 23 × u32 pointers to reward lists |
| `0x083BD268`–`0x083BD47C` | 532 | reward lists, `{u16 type, u16 value}` pairs, terminated by `0x0000` |
| `0x080CF720` | 12 | u32 pass-length table `{10, 13, 15}` |
| `0x083FCA70` | 360 | 90 × u32 keyboard glyph pointers, index `col*6 + row-1` |
| `0x083FC02F`… | 6×15 | keyboard row character strings (A–Z, a–z, 0–9, I–X, `-!'",.`, space) |
| `0x083FCD7C`…`0x083FCDC0` | — | Zero Code UI message pointer table (`Zero Code entered!`, `Error.`, `Loading completed.`, `That Zero Code has already been entered.`, …) |
| `0x0806CDFC` | ~0x150 | ROM reference implementation of the Zero Code validator (see caveat below) |
| `0x08066668` | ~0x60 | Zero Code screen setup: reads pass level, writes max length |
| `0x080668xx`–`0x08066Bxx` | — | Zero Code keyboard input/append handler; enforces max length |
| `0x08077C3C` | — | debug mode-select UI (labels at `0x083BD918`); no BL/pointer caller found |
| `0x083BDCEC` | — | debug menu label-pointer table; handlers at `0x083BDD20` (`0x0807A7F5`, …) |
| `0x0203A8EC` | 1 | EWRAM: pass level (0 = Bronze, 1 = Silver, 2 = Gold) |
| `0x0203A8ED` | 23 | EWRAM: “code already entered” flags used by the ROM reference validator |
| `0x0203CAFC` | — | EWRAM: Zero Code UI context base |
| `0x0203CB04` | 16 | EWRAM: input string buffer (encoded) |
| `0x0203CB20` | 1 | EWRAM: current input length (`base+0x1C`) |
| `0x0203CB21` | 1 | EWRAM: maximum input length (`base+0x1D`), normally 10/13/15 |
| `0x0203CB6C` | — | EWRAM: 11..16-byte copy of the submitted string (BIOS `CpuSet` from `0x0203CB04`) |
| `0x0203CBF4` | 4 | EWRAM: reward-pointer global used by the ROM reference validator |
| `0x0203CBF8` | 4 | EWRAM: message-pointer global used by the Zero Code UI |

Validator caveat (important for reproduction): `0x0806CDFC` reads `0x083FCC3C`,
`0x083BD484`, `0x0203A8ED` and sets the `Loading completed.` message at
`0x083FCD90`; its disassembly matches every observed success/failure path. However,
mGBA breakpoints at `0x0806CE84` (compare loop) and write watchpoints on
`0x0203A8ED`/`0x0203CBF4` did **not** fire during an accepted submission, while a
control breakpoint at `0x0806699A` did. So the shipping screen almost certainly
executes a separate (script-VM or RAM-resident) implementation that shares the same
tables and messages; `0x0806CDFC` is the complete ROM reference implementation of the
logic, not a proven runtime entry point. The empirical model in §5 is what the ROM
accepts.

## 5. Algorithm

### 5.1 Text encoding

The code table and all Zero Code UI text use an 8-bit game-specific encoding
(not ASCII, not Shift-JIS):

| Byte | Meaning |
|---|---|
| `0x00` | terminator |
| `0x0A` | newline |
| `0x10` | space |
| `0x11`–`0x2A` | `A`–`Z` |
| `0x2B`–`0x44` | `a`–`z` |
| `0x45`–`0x4E` | `0`–`9` |
| `0x4F` | `?` |
| `0x51` | `-` |
| `0x52` | `.` |
| `0x53` | `'` |
| `0x54` | `,` |
| `0x56` | `!` |
| `0x58` | `"` |
| `0x6B`–`0x74` | Roman numerals `I`–`X` (single glyphs) |

This is why `strings` on the ROM finds no Zero Code text: raw ASCII hits were
only the header title and the build banner.

### 5.2 Input

The screen has a 6-row × 15-column keyboard (row order: A–E, F–J, K–O, P–T,
U–Y, Z/`-`/`!`; each row also exposes a–e/f–j/…, digits 0–9 and the I–X
numerals in the third columns). `Return` = backspace, `END` = submit.

The maximum accepted length is computed when the screen opens:

```
pass      = u8[0x0203A8EC]                 ; 0 Bronze, 1 Silver, 2 Gold
maxlen    = u32[0x080CF720 + pass*4]       ; 10, 13, 15
u8[0x0203CB21] = maxlen                    ; base 0x0203CAFC + 0x1D
```

Each accepted key appends one encoded character to `0x0203CB04` and increments
the length byte at `0x0203CB20`; once length >= maxlen the screen stops appending
and focuses `END`. Verified dynamically: at Bronze, `u8[0x0203CB21] = 0x0A`; when
the byte was changed to `0x0F` with the command-line debugger, the same screen
accepted the 15-character `REVIVAL OF EVIL` (screenshots
`… - 15 char code entered.png`, `… - REVIVAL OF EVIL Long Core.png`).

### 5.3 Validation

```
on END:
    copy encoded string 0x0203CB04 -> 0x0203CB6C (BIOS CpuSet, len+NUL)
    for i = 0 .. 22:
        if strcmp(input, code[i]) == 0:        # exact, case-sensitive, full length
            if entered[i]:
                show "That Zero Code has already been entered."
                return FAIL
            entered[i] = 1
            grant(reward_list[i])
            show "Zero Code entered!" / "Loading completed."
            return OK
    show "Error! Zero code is incorrect."
    return FAIL
```

Note that "Zero Code entered!" is an *intermediate* message shown for **every**
submission; the actual verdict is the next box (`Loading completed.` vs
`Error! Zero code is incorrect.`). Testing only the first box produces false
positives — worth knowing for any later session.

`grant()` walks the reward list:

| Type | Meaning | Message |
|---|---|---|
| 1 | `money += value` | `You received <value> ₿!` |
| 2 | add part id `value` | `You got <part name>!` |
| 3 | add B-Daman id `value` | (no separate message observed; appears in B-Danote) |

The reward list is exactly the data at `0x083BD484`; e.g. index 0 → `(1,1500)`,
index 3 → `(2,408),(2,409),(2,410)`, index 5 → `(3,26)` plus seven parts.

## 6. Tables

### 6.1 The 23 Zero Code entries (ROM order)

Tier is the published pass grouping (Bronze 0–5, Silver 6–14, Gold 15–22);
it also matches the 10/13/15 length caps.

| # | Code (exact) | Len | Tier | Reward list | Published? |
|---:|---|---:|---|---|---|
| 0 | `GO YAMATO!` | 10 | Bronze | 1500 ₿ | Yes (GameFAQs/SuperCheats) |
| 1 | `HEY TOMMI!` | 10 | Bronze | 2000 ₿ | Yes |
| 2 | `B-DAFIRING` | 10 | Bronze | 3000 ₿ | Yes |
| 3 | `SHOOT IT!!` | 10 | Bronze | parts 408,409,410 (Saber Barrel, L/R Shield Stand) | Yes |
| 4 | `THE BOTTLE` | 10 | Bronze | part 411 (PlasticBottle Mag II) | Yes |
| 5 | `HARD TEETH` | 10 | Bronze | B-Daman 26 (Cheesy Mouse) + parts 273–279 | Yes |
| 6 | `VENOMOUS TAIL` | 13 | Silver | B-Daman 10 + parts 325–331 | Yes |
| 7 | `TONS OF BALLS` | 13 | Silver | parts 406,407 | Yes |
| 8 | `GLEAMING FANG` | 13 | Silver | B-Daman 16 + parts 133–136 | Yes |
| 9 | `YOKUSAIMARU!` | 12 | Silver | B-Daman 36 + parts 352–358 | Yes |
| 10 | `A BLOODY BODY` | 13 | Silver | B-Daman 3 + parts 284–288 | Yes |
| 11 | `GUST OF WIND!` | 13 | Silver | B-Daman 6 + parts 118–124 | Yes |
| 12 | `MONGREL FANG!` | 13 | Silver | B-Daman 25 + parts 266–272 | Yes |
| 13 | `SHADOWY ARMOR` | 13 | Silver | B-Daman 17 + parts 201–207 | Yes |
| 14 | `GOLDEN ARMOR!` | 13 | Silver | B-Daman 5 + parts 112–117 | Yes |
| 15 | `REVIVAL OF EVIL` | 15 | Gold | B-Daman 39 (Labyrinth) + parts 374–379 | Yes |
| 16 | `LET'S B-DAFIRE!` | 15 | Gold | B-Daman 41 + parts 388,389,392–394 | Yes |
| 17 | `GIFT FROM ATLUS` | 15 | Gold | B-Daman 21 + parts 229–236 | Yes |
| 18 | `THE SWIFT WINGS` | 15 | Gold | B-Daman 29 + parts 296–302 | Yes |
| 19 | `FEROCIOUS WOLF!` | 15 | Gold | B-Daman 1 + parts 87–93 | Yes |
| 20 | `THE RAZING FIRE` | 15 | Gold | B-Daman 12 + parts 168–174 | Yes |
| 21 | `DEVILISH FIGURE` | 15 | Gold | B-Daman 34 | Yes |
| 22 | `STRONG RED GALE` | 15 | Gold | B-Daman 13 | Yes |

`HIDDEN SWORD` (published as Gold, 11 chars) is **not** in the ROM table and is
not present literally anywhere in the 8 MiB image. Its 10-char prefix
`HIDDEN SWO` is rejected in-game.

### 6.2 Pass table

| Pass level | Pass | Max input | Reachable entries |
|---:|---|---:|---|
| 0 | Bronze | 10 | 0–5 (6 codes) |
| 1 | Silver | 13 | 0–14 (15 codes) |
| 2 | Gold | 15 | 0–22 (23 codes) |

The in-game dialogue confirms the design: it gives the Bronze code
`SHOOT IT!!` (`0x083F648E`), the Silver code `TONS OF BALLS` (`0x083F6A79`) and
the Gold code `DEVILISH FIGURE` (`0x083F6CC0`).

## 6b. Enumeration

**Space definition.** The code space is a closed lookup, not a checksum/field
format:

* alphabet: the 80 keyboard symbols (`A–Z`, `a–z`, `0–9`, `I–X`, space,
  `-`, `!`, `'`, `"`, `,`, `.`);
* length: 1–15, but only up to `maxlen` is *storable* (10/13/15 by pass);
* acceptance: exact case-sensitive equality with one of the 23 NUL-terminated
  table strings (no prefixes, no case folding, no space normalization);
* number of representable *accepted* values: **23** (the table entries);
  the rest of the 80^n input space is rejected.

**Reachable set.** At the starting Bronze pass, `maxlen = 10`, so the reachable
set is exactly the six 10-character Bronze entries (indices 0–5). The Silver
(`maxlen = 13`) and Gold (`maxlen = 15`) sets follow from the same table and setup
code (indices 0–14 and 0–22); those pass levels were not earned in this session,
so the Silver/Gold reachability is derived, not observed. The cap mechanism
itself was proven by the patched-byte test below.

**Novel codes.** None is possible. The accepted set is the 23 table strings; a
line-by-line comparison with the archived GameFAQs list (2020-04-06 capture) and
SuperCheats shows every one of the 23 is published, and the only extra published
entry (`HIDDEN SWORD`) is absent from the ROM. We therefore did not fabricate a
"novel" string: any string outside the table is rejected, and any string inside it
is already published. The negative is bounded by the enumeration above, not by a
failed search.

**Bounds proven by rejection (observed in mGBA):**

| Input | Why it must fail | Result |
|---|---|---|
| `REVIVAL OF` (10) | exact 10-char prefix of the 15-char entry #15 | `Error! Zero code is incorrect.` |
| `go yamato!` | case differs from table | rejected |
| `GOYAMATO!` | space removed | rejected |
| `GO ` (3) | no 3-char table entry | rejected |
| `REVX` (4) | wrong 4th character | rejected |
| `GIFTX` (5) | wrong 5th character | rejected |
| `HIDDEN SWO` (10) | `HIDDEN SWORD` is not in the ROM | rejected |
| `HARD TEETH` twice | entered flag set | `That Zero Code has already been entered.` |
| 11th..15th characters at Bronze | `maxlen = 10` | characters not stored; field stays at 10 |
| `REVIVAL OF EVIL` at Bronze | 15 chars > cap | only `REVIVAL OF` stored, rejected |

**Cap mechanism proven.** The max-length byte `0x0203CB21` was observed as
`0x0A` at Bronze; setting it to `0x0F` with the command-line debugger let the
**unmodified** ROM accept the full 15-character `REVIVAL OF EVIL` and grant
`Long Core` (part 374, the first item of entry #15's reward list). This is a
test-harness change to a documented state byte, not a cheat code, and it proves
that the table/validator beyond 10 characters is live and correct.

**Screens walked (count).** Title; main menu (2 items); System Settings
(Message Speed 1–8, Reset Data, Return); story intro/tutorial battle;
town tabs MOVE / TALK / TOOLBOX / HINT; location list; shop menu
(Buy/Sell/Input Zero Code); Buy category list and part detail; Sell list;
Zero Code keyboard; Toolbox (B-Daman customise, B-Danote with Characters /
B-Daman / Parts / Special Attack / Battle Records, Save dialog). No additional
password/cheat/unlock screen was found.

**Text/button space searched (counts).** Raw `strings -n 4` over the ROM:
`password` 0, `cheat` 0, `debug` 0, `secret` 0, `unlock` 0, `code` 0 — the
game text is encoded. After decoding the full ROM with the charmap in §5.1
(38,269 printable runs): `password` 1, `cheat` 5 (all story dialogue, e.g.
"you cheated, man."), `debug` 9 (all debug-menu labels), `secret` 18 (story
"Secret Arena"), `unlock` 0, `code` 19, `zero code` 16. Only the Zero Code
screen is a code-entry surface.

## 7. Validation evidence

**Observed** (emulator, screenshots next to this report):
* Full menu path to the Zero Code keyboard; keyboard layout 6×15.
* Six Bronze codes accepted with the exact reward messages; baseline B-Danote
  counts are Parts 8/8 and B-Daman 1/2 (screenshot), and after `HARD TEETH`
  the B-Daman list is 2/2 with `Cheesy Mouse Special`. `THE BOTTLE` produced
  `You got PlasticBottle Mag II!` (the magazine row was 0/0 in the baseline).
* Rejections in §6b, including lowercase, space removal, prefixes, wrong chars.
* `That Zero Code has already been entered.` on a repeat.
* Max-length byte `0x0A` at Bronze; `REVIVAL OF EVIL` accepted and `Long Core`
  granted after setting it to `0x0F`.

**Derived** (ROM data/disassembly):
* 23 code strings, pointer table, tier lengths, reward table and the
  `{10,13,15}` pass table, all read directly from the bytes and independently
  cross-checked against the observed rewards.
* The input setup at `0x08066668` computes `maxlen = table[pass]` and stores it at
  `0x0203CB21`; the append handler increments the length at `0x0203CB20` and stops
  at `maxlen`.
* The ROM reference validator at `0x0806CDFC` implements the exact-match,
  entered-flag and reward-pointer logic; its message table is at `0x083FCD7C`.

**Inferred / not fully proven:**
* The live validation entry point: breakpoints at `0x0806CE84` and writes to
  `0x0203A8ED`/`0x0203CBF4` did not fire, so the live path may be a script-VM or
  RAM-resident copy using the same tables (§4 caveat).
* The Silver/Gold pass acquisition points and that they raise the cap in normal
  play; we proved the cap mechanism by patching the state byte, not by earning
  the pass.
* The debug-menu trigger.

## 8. Unknowns

1. **Live validator address.** The ROM contains a complete implementation at
   `0x0806CDFC`, but runtime breakpoints there did not hit; the actual call site
   (script VM or RAM copy) was not isolated. Behaviour is fully characterized
   regardless.
2. **Pass-level setter.** `0x0203A8EC` is read by the Zero Code setup but the
   story event that writes it (Bronze→Silver→Gold) was not exercised; reaching
   Gold normally requires a long playthrough.
3. **Debug menu.** The mode-select labels/handlers exist (`0x083BD918`,
   `0x083BDCEC`, `0x08077C3C`) but no caller or boot key combination was found.
   Tested and failed: hold L+R+Start, Select+Start, L+R+Select+Start, A+B+Start,
   Up+Down+L+R, L+R+Up+Down+Select through boot; Select×3/×5 then Start; B,A,B,A;
   L+R+Select then Start. It is most likely compiled-in dead code or gated by a
   development save flag.
4. **The `HIDDEN SWORD` publication** is not in the ROM; whether it ever existed
   in a prototype is unknown.

## 9. Tooling

* `mGBA` SDL 0.10.x, `Xvfb :178`, `openbox`, `xdotool`, `scrot`/ImageMagick.
* `arm-none-eabi-objdump -M force-thumb` for the 0x0806CDFC / 0x08066668 /
  0x08077C3C ranges.
* Python 3 scripts in `/tmp/opencode/bdaman2`:
  * `text_decode` logic → `text_all.txt` (full decoded text dump),
  * `cursor.py` (screenshot-driven keyboard cursor + cell map),
  * `key.py` (X key injection and crop),
  * `dbg*.py` (mGBA command-line debugger automation: watchpoints/breakpoints,
    max-length byte patch),
  * reward-table parser (one-off, output in §6.1).
* `pextract` not used; the mGBA `-g` GDB stub was avoided because another session
  holds port 2345 — the `-d` command-line debugger was used instead.

## Legal note

No ROM, extracted graphics, music, or game text is redistributed. Only addresses,
algorithms, hashes, and screenshots of menu states produced by the game itself are
documented here.
