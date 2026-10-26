# 2-in-1: Crash Bandicoot Purple & Spyro Orange (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `2-in-1 - Crash Bandicoot Purple - Ripto's Rampage & Spyro Orange - The Cortex Conspiracy.gba` |
| Size | 33,554,432 bytes (32 MiB) |
| Header @ `0x000000` | title `CRA&SPYSPACK`, code `B53E`, maker `7D`, version 0, complement `0x7D`, header checksum `0x0000` |
| Header @ `0x1000000` | title `CRASH PURPLE`, code `BD4E`, maker `7D`, version 0, complement `0x6E`, header checksum `0x0000` |
| MD5 | `50126d4115f7eba81eb206b13b68d726` |
| SHA-1 | `95b5a68962ce552a71d8212850e85d90d2844b40` |
| SHA-256 | `424246a0522d14b4c1d344691363087e2a13bed0aaab1b1262a194dfd4c2f431` |

**Cart layout (multi-game cartridge).** A full Nintendo-logo scan (156-byte logo at
header+4) finds six logo copies, i.e. six GBA headers:

| File offset | Title | Code | Maker | Entry word | Interpretation |
|---:|---|---|---|---|---|
| `0x0000000` | `CRA&SPYSPACK` | `B53E` | `7D` | `0xEA3EEBFE` (nonstandard/out-of-range) | pack header; first image (Spyro Orange), header patched |
| `0x0F69AC4` | `XXXXXXXXXXXX` | `XXXX` | `VV` | `0xEA00002E` | embedded stub image (title/code placeholders) |
| `0x0F8B9FC` | `XXXXXXXXXXXX` | `XXXX` | `VV` | `0xEA00002E` | embedded stub image |
| `0x1000000` | `CRASH PURPLE` | `BD4E` | `7D` | `0xEA00002E` (`b 0x080000C0`) | second image (Crash Purple), full retail header |
| `0x1F077C4` | `XXXXXXXXXXXX` | `XXXX` | `VV` | `0xEA00002E` | embedded stub image |
| `0x1F296D0` | `XXXXXXXXXXXX` | `XXXX` | `VV` | `0xEA00002E` | embedded stub image |

All six headers have a correct complement byte. The two real images are 16 MiB each:
Spyro Orange at `0x08000000`–`0x08FFFFFF`, Crash Purple at `0x09000000`–`0x09FFFFFF`.
A sub-image's absolute address is `0x08000000 + file_offset`, so Crash Purple strings at
file `0x106CAC8` are referenced as `0x0906CAC8` (the second 16 MiB half of the 32 MiB cart).
The four `XXXX/VV` headers sit inside the two images, about 136 KB apart in pairs, and are
GBA-format stub images (multiboot/link stubs) with deliberately placeholder titles and an
infinite-loop entry (`b .`). They are not selectable from the boot selector.

The pack's own first word is not a usable ARM branch; the GBA BIOS enters at `0x080000C0`
regardless, which is why the image still boots.

## 2. Executive summary

Both halves of the cartridge contain a **developer-intended cheat-code entry screen**,
reached from the Mode menu by holding **L + R**. It is not documented anywhere in the game's
UI. Entering a code opens a 10-slot keypad with a 32-symbol alphabet (21 consonants, digits
0–9, and an END/blank glyph) and validates the typed string against a per-half table.

The two tables are plain NUL-terminated ASCII, padded to 4 bytes:

* **Spyro Orange** (`0x0806065C`, 10 entries × 8 bytes): `SH33P`, `SP4RX`, `SPYR0`,
  `P0RT4L`, `G3MZ`, `V1S10NS`, `T4P10C4`, `S0YB34N`, `V4N1LL4`, `B41S0KV`.
  Effects: 100/200 gems, hidden cards, and palette/character reskins
  (Sheep, Sheep Flame, Orange, Orange Spyro, Purple, Gray). All ten were entered in mGBA
  and their on-screen result recorded.
* **Crash Purple** (`0x0906CAC8`, 22 entries, variable length): `CR4SH`, `G3CK0`, `C0FF33`,
  `WH1STL3`, `PH0N3T4G`, `STR4WB3RRY`, `WVMP4FR00T`, `PR3S3NTZ`, `L4MPP0ST`, `SW1NGS3T`,
  `K1LL4Z`, `C4M0`, `CVTZ`, `CR3D1TS`, `ST4CY`, `R0BG`, `C0L1N`, `J0NNY`, `TR4V1S`,
  `SVNB1R`, `J450N`, `BR3NT`.

The headline discovery is **`SW1NGS3T`**: it starts a complete, otherwise unreachable
**“Spyro Party • USA”** mini-game that is present inside the Crash Purple half — its own
copyright cards, title screen (“START GAME”) and a playable rhythm/bounce stage. `CR3D1TS`
opens the Vicarious Visions credits; `CVTZ` jumps into the Cortex/Ripto story cutscene;
`WH1STL3`/`PH0N3T4G` award the “Mayan Jungle” and “Sewers” trading cards; the gem codes add
100/200/500 wumpa (Crash) or 100/200 gems (Spyro).

Validation is a linear `strcmp` chain, not a checksum: each half has one validator function
(`0x0802F2F0` for Spyro, `0x0903AB84` for Crash) that copies the entry buffer to a stack
string and compares it against every table entry in order. A per-code “already used” flag
makes each code single-use per session/save; a second entry prints “Code already used”.

One genuine defect was found: the keypad is capped at 10 characters and **the ACCEPT/END
cell stops responding once all 10 slots are filled**, so the two 10-character table entries
`STR4WB3RRY` and `WVMP4FR00T` cannot be submitted through the UI as shipped (observed
repeatedly; at ≤9 characters ACCEPT works normally).

No GameShark/CodeBreaker/memory-edit codes were used or are reported here; everything below
is reached through the game's own menus and its own code tables.

## 3. How to reproduce

### Emulator and input

```
Xvfb :106 -screen 0 1280x1024x24 &
DISPLAY=:106 openbox &
DISPLAY=:106 SDL_AUDIODRIVER=dummy mgba -3 <rom>.gba &
```

mGBA SDL default keymap: **A = `x`, B = `z`, L = `a`, R = `s`, Start = `Return`,
Select = `BackSpace`, D-pad = arrows.** Hold keys 80–150 ms; the keypad accepts one action
per press and a 10 ms tap is often lost.

### Reaching the feature

1. Boot. The pack shows a **game selector**: the Spyro Orange logo with yellow arrows.
   Press **Left/Right** to switch the logo to **Crash Purple**, **A** to boot the chosen half.
2. Title screen → **Start**.
3. **Select a Slot** (three “New Game” slots + “Erase a Slot”) → pick the first slot.
4. **Mode menu** (“Story Mode / Party Mode / Trading Cards / Credits”).
5. Hold **L + R together for ~0.5–1 s** on the Mode menu. The cheat keypad opens:
   10 entry slots at the top, an 8×4 symbol grid, “B Back / A Select” (Spyro) or
   “B BACK / A ACCEPT” (Crash).
6. D-pad moves the cursor (wraps at the edges), **A** appends the highlighted symbol,
   **B** deletes the last character. Navigate to the last grid cell (blank/“END” glyph) and
   press **A** to submit. The result screen shows `You entered: <CODE>` plus either the
   effect text, `Invalid Code!` (Spyro) / `CODE NOT RECOGNIZED` (Crash), or
   `CODE ALREADY USED`; **B** returns to the Mode menu.

A savestate on the keypad makes each test 8–16 keypresses. The `auto_codes.py` driver used
here loads a savestate (`F4` / `F6`), walks the grid for a code, presses END, screenshots,
and repeats.

### Codes tested

All 10 Spyro codes and all 22 Crash codes were entered in mGBA; results in §6. Spot checks:
`ZZZZZ` → rejected in both halves; `CR4SH` twice in one session → `CODE ALREADY USED`.

## 4. Address map

`rom_address = 0x08000000 + file_offset`. Half 1 (Spyro) is `0x08000000`–`0x08FFFFFF`;
half 2 (Crash) is `0x09000000`–`0x09FFFFFF`.

| Item | ROM address | File offset | Notes |
|---|---:|---:|---|
| Pack header | `0x08000000` | `0x0` | `CRA&SPYSPACK` / `B53E` |
| Crash header | `0x09000000` | `0x1000000` | `CRASH PURPLE` / `BD4E` |
| Spyro code table (first entry `SH33P`) | `0x0806065C` | `0x6065C` | 10 × 8 bytes, NUL-padded |
| Spyro validator entry | `0x0802F2F0` | `0x2F2F0` | `push {r4-r7,lr}`, `strcpy`, 10 × `strcmp` |
| Spyro `strcmp` | `0x0803C078` | `0x3C078` | word-wise optimized `strcmp` |
| Spyro `strcpy` | `0x0803C0D4` | `0x3C0D4` | used to copy keypad buffer |
| Spyro accept wrapper | `0x0802F680` | `0x2F680` | builds keypad object; calls validator at `0x0802F6CC` |
| Spyro reject text | `0x080D47D4` | `0xD47D4` | `"Invalid Code!"` |
| Spyro accept text | `0x080D47C0` | `0xD47C0` | `"Code Accepted!"` |
| Crash code table (first entry `CR4SH`) | `0x0906CAC8` | `0x106CAC8` | 22 entries, variable length, 4-byte padded |
| Crash validator entry | `0x0903AB84` | `0x103AB84` | copies buffer, 22 × `strcmp`, applies effects |
| Crash `strcmp` | `0x09047F68` | `0x1047F68` | same algorithm as Spyro's |
| Crash `strcpy` | `0x09047FC4` | `0x1047FC4` | |
| Crash accept wrapper | `0x0903B1C4` | `0x103B1C4` | calls validator at `0x0903B1D4` |
| Crash reject text | `0x09075D94` | `0x1075D94` | `0x04` + `"Code not recognized"` |
| Crash “already used” text | `0x09075E44` | `0x1075E44` | `0x04` + `"Code already used"` |
| Crash wumpa template | `0x09075E5C` | `0x1075E5C` | `0x04` + `"Wumpty Wump! %d free wumpa!"` |
| Crash card template | `0x09075E80` | `0x1075E80` | `0x04` + `"Card Smack! You got card: %s"` |
| Crash message-pointer table | `0x090716C0` | `0x10716C0` | array of `char*` used by `0x0903E1D0` |
| “Mayan Jungle” name (used by `WH1STL3`) | `0x09074FFC` | `0x1074FFC` | level/card name table |
| “Sewers” name (used by `PH0N3T4G`) | `0x09075024` | `0x1075024` | level/card name table |
| Keypad input buffer (Crash, observed) | `0x02033F24` | — | 10 ASCII chars + NUL, `-` padding |
| Per-code state record (Crash, observed) | `0x02022390` | — | code bytes + state word |
| Keypad object (Crash, observed) | `0x020316A4` | — | pointer fields into the record above |

Notes on the RAM addresses: they are heap allocations, found by decompressing savestates
(see §9) after entering `CR4SH`; they were stable across all runs in this session but should
be treated as observed instances, not fixed globals.

## 5. Algorithm

### 5.1 Keypad input

```
alphabet (row-major, 8 columns × 4 rows):
  B C D F G H J K        (consonants; vowels A E I O U are absent)
  L M N P Q R S T
  V W X Y Z 0 1 2
  3 4 5 6 7 8 9 END      (END is a blank/box glyph)
buffer[0..9] = 'A'..'Z','0'..'9' characters, padded with '-' (0x2D)
cursor wraps horizontally and vertically; A appends, B deletes one character
END submits only while the buffer is not full (<= 9 characters)
```

The keypad writes plain ASCII into the buffer; savestate dumps show `CR4SH-----` at
`0x02033F24`, i.e. no tile-index translation is involved in the stored code.

### 5.2 Validator (both halves)

```c
int validate(obj *o) {
    char s[?];                       // stack copy of the keypad buffer
    strcpy(s, get_buffer());         // Spyro 0x0803C0D4, Crash 0x09047FC4
    if (strcmp(s, "CODE0") == 0) {   // Spyro 0x0803C078, Crash 0x09047F68
        if (used[0]) return already_used_message();
        used[0] = 1;
        show_message(...); apply_effect_0();
    } else if (strcmp(s, "CODE1") == 0) { ... }
    ...
    else {
        show_message("Invalid Code!");        // Spyro
        show_message("Code not recognized");  // Crash
    }
    return 1;
}
```

`strcmp` is a standard word-at-a-time implementation:

```asm
09047f68  push {r4,r5,lr}
09047f6c  orrs r0,r3 ; ands r0,#3      ; both pointers word aligned?
09047f78  ldr r1,[r2] ; ldr r0,[r3]    ; compare 4 bytes
...
09047fae  ldrb r0,[r2] ; cmp r0,#0     ; tail byte loop
09047fbe  subs r0,r2,r3                ; return difference
```

The “already used” gate in the Crash validator is
`0x0902A2C4(index)` (test) and `0x0902A2D0(index)` (set), called with a per-code index
0,1,2,… in table order; a non-zero test branches to the `0x09075E44` “Code already used”
path. The Spyro validator uses the same pattern with its own indices. The flag lives in RAM
and is reset by reloading an earlier savestate; whether it is written to the battery save
was not proven.

Return value: `r0 = 1` on both accept and reject; the on-screen text, not the return value,
distinguishes the cases.

### 5.3 Effects dispatch (Crash, `0x0903AB84`)

Each matched branch follows the same shape:

```
bl 0x9016b18                     ; engine call (audio/UI service)
ldr r0,=msgid ; bl 0x903e1d0     ; resolve text (two-level pointer table)
bl 0x901b300 / 0x9017a70         ; format and draw the message on the UI object
bl 0x902a994 ; ... 0x902a814     ; add N to the wumpa counter (gem codes only)
```

Observed effect parameters: `CR4SH` +100, `G3CK0` +200, `C0FF33` +500 wumpa
(`ldr r1,[r0,#0x6c]` then `adds r1,#100/#0xC8/#0x1F4`).

### 5.4 Special-effect branches

* `SW1NGS3T` (`0x0903AF14`): after the message, calls `0x09001348`, which tears down the
  menu and boots the embedded “Spyro Party • USA” mini-game (title card with its own
  copyright text, then a rhythm stage). This path is what makes the mini-game reachable.
* `CR3D1TS` (`0x0903AFE8`): plays the Vicarious Visions credit card
  (`VICARIOUS VISIONS / WWW.VVISIONS.COM`).
* `CVTZ` (`0x0903AFB8`): switches to a story cutscene (Neo Cortex/Ripto dialogue).
* `WH1STL3` / `PH0N3T4G`: build `"Card Smack! You got card: %s"` with the names
  `Mayan Jungle` (`0x09074FFC`) / `Sewers` (`0x09075024`) taken from the level-name table
  around `0x09074F60`.
* `ST4CY`, `R0BG`, `C0L1N`, `J0NNY`, `TR4V1S`, `SVNB1R`, `J450N`, `BR3NT`: matched but
  produce no message text (they call `0x0900DDCC` with two IDs from the `0x0904A448`
  region, i.e. they set an unlock/name entry silently).

## 6. Tables

### 6.1 Spyro Orange codes (`0x0806065C`, 8-byte stride) — all entered in mGBA

| # | Code | Address | Observed result |
|---:|---|---|---|
| 0 | `SH33P` | `0x0806065C` | “Code Accepted! Sheep Mode Activated!” (enemies become sheep) |
| 1 | `SP4RX` | `0x08060664` | “Orange Mode Activated!” (whole screen turns orange) |
| 2 | `SPYR0` | `0x0806066C` | “Orange Spyro Mode Activated!” (Spyro turns orange) |
| 3 | `P0RT4L` | `0x08060674` | “Purple Mode Activated!” (screen turns purple) |
| 4 | `G3MZ` | `0x0806067C` | “Gray Mode Activated!” (screen turns gray) |
| 5 | `V1S10NS` | `0x08060684` | “You have received 100 gems!” |
| 6 | `T4P10C4` | `0x0806068C` | “You have received 200 gems!” |
| 7 | `S0YB34N` | `0x08060694` | “You have received a hidden card!” |
| 8 | `V4N1LL4` | `0x0806069C` | “You have received a hidden card!” |
| 9 | `B41S0KV` | `0x080606A4` | “Sheep Flame Mode Activated!” |
| — | any other | — | “Invalid Code!” |

### 6.2 Crash Purple codes (`0x0906CAC8`) — all entered in mGBA

| # | Code | Address | Observed result |
|---:|---|---|---|
| 0 | `CR4SH` | `0x0906CAC8` | “Wumpty Wump! 100 free wumpa!” |
| 1 | `G3CK0` | `0x0906CAD0` | “Wumpty Wump! 200 free wumpa!” |
| 2 | `C0FF33` | `0x0906CAD8` | “Wumpty Wump! 500 free wumpa!” |
| 3 | `WH1STL3` | `0x0906CAE0` | “Card Smack! You got card: Mayan Jungle” |
| 4 | `PH0N3T4G` | `0x0906CAE8` | “Card Smack! You got card: Sewers” |
| 5 | `STR4WB3RRY` | `0x0906CAF4` | **not enterable** (10 chars; ACCEPT dead when buffer full) |
| 6 | `WVMP4FR00T` | `0x0906CB00` | **not enterable** (10 chars; same defect) |
| 7 | `PR3S3NTZ` | `0x0906CB0C` | “Kickin' it old skool!” |
| 8 | `L4MPP0ST` | `0x0906CB18` | “Orangilicious!” |
| 9 | `SW1NGS3T` | `0x0906CB24` | starts hidden **Spyro Party • USA** mini-game |
| 10 | `K1LL4Z` | `0x0906CB30` | “Represent” |
| 11 | `C4M0` | `0x0906CB38` | “Gung Ho Bandicoot!” |
| 12 | `CVTZ` | `0x0906CB40` | jumps to Cortex/Ripto story cutscene |
| 13 | `CR3D1TS` | `0x0906CB48` | Vicarious Visions credits card |
| 14 | `ST4CY` | `0x0906CB50` | accepted, silent (no message body) |
| 15 | `R0BG` | `0x0906CB58` | accepted, silent |
| 16 | `C0L1N` | `0x0906CB60` | accepted, silent |
| 17 | `J0NNY` | `0x0906CB68` | accepted, silent |
| 18 | `TR4V1S` | `0x0906CB70` | accepted, silent |
| 19 | `SVNB1R` | `0x0906CB78` | accepted, silent |
| 20 | `J450N` | `0x0906CB80` | accepted, silent |
| 21 | `BR3NT` | `0x0906CB88` | accepted, silent |
| — | any other | — | “CODE NOT RECOGNIZED” |

The 22 entries are not fixed-stride: each string is NUL-terminated and padded to a 4-byte
boundary, so 4-, 6-, 7-, 8- and 10-character codes occupy 4–12 bytes each. Assuming an
8-byte stride produces wrong addresses from entry 5 onward.

### 6.3 Status messages

| Text | Spyro address | Crash address |
|---|---:|---:|
| `Code Accepted!` | `0x080D47C0` | not used (Crash shows only the effect text) |
| `Invalid Code!` / `Code not recognized` | `0x080D47D4` | `0x09075D94` |
| `Code can only be used once!` / `Code already used` | `0x080D47E8` | `0x09075E44` |
| `You have received %d gems!` | `0x080D4808` | — |
| `You have received a hidden card!` | `0x080D4828` | — |
| `Wumpty Wump! %d free wumpa!` | — | `0x09075E5C` |
| `Card Smack! You got card: %s` | — | `0x09075E80` |
| `Sheep Mode Activated!` | `0x080D4874` | — |
| `Sheep Flame Mode Activated!` | `0x080D4890` | — |
| `Orange Mode Activated!` | `0x080D48B0` | — |
| `Gray Mode Activated!` | `0x080D48CC` | — |
| `Purple Mode Activated!` | `0x080D48E8` | — |
| `Orange Spyro Mode Activated!` | `0x080D4850` | — |

## 6b. Enumeration

* **Space size.** Ten character slots over the 32-symbol keypad (`BCDFGHJKLMNPQRSTVWXYZ`,
  `0–9`, `END`) is nominally `32^10 ≈ 1.13×10^15` strings. Acceptance is a pure
  `strcmp` table lookup, so the accepted set is exactly the ROM tables: **10 Spyro
  entries** (fixed 8-byte stride) + **22 Crash entries** (NUL-terminated, 4-byte
  padded, variable stride). There is no checksum, XOR key or alphabet permutation
  (§7), so the rest of the input space is rejected, not transformed.
* **Exhaustive table dump.** Both tables were read end-to-end from the ROM and every
  reachable entry was typed in mGBA. The Crash table includes eight **silently accepted
  staff-name entries** (`ST4CY`, `R0BG`, `C0L1N`, `J0NNY`, `TR4V1S`, `SVNB1R`, `J450N`,
  `BR3NT`) that appear on no published list and print no message; they are accepted
  exactly like the effect codes.
* **Unreachable entries.** Two 10-character table entries, `STR4WB3RRY` and
  `WVMP4FR00T`, cannot be submitted on retail because the keypad's ACCEPT/END cell
  stops responding once all ten slots are filled (observed repeatedly; deleting one
  character restores it). They are in the table, so the validator would accept them.
* **Bounds proven by rejection.** `ZZZZZ` (and strings that are not exact table
  entries) produce `Invalid Code!` / `CODE NOT RECOGNIZED`, and a second use of
  `CR4SH` produces `CODE ALREADY USED`; the input length is bounded by the 10-slot
  buffer.

## 7. Validation evidence

**Observed (mGBA screenshots, this session)**

* The boot game selector switches between the Spyro Orange and Crash Purple logos with
  Left/Right and boots the selected half.
* Mode menu → L+R opens the keypad in both halves (distinct skins: gold for Spyro,
  blue/space for Crash).
* Every code in §6.1 and §6.2 was typed through the keypad and the resulting screen
  recorded; the effect text quoted above is verbatim from those screens.
* `ZZZZZ` produces `Invalid Code!` (Spyro) and `CODE NOT RECOGNIZED` (Crash).
* Entering `CR4SH`, returning with B, reopening the keypad and entering `CR4SH` again
  produces `CODE ALREADY USED`.
* `SW1NGS3T` leads, through two copyright cards, to a **“Spyro Party • USA”** title screen
  with “START GAME” and an animated playable stage (Spyro, note track, beat ring) — an
  entire hidden mini-game inside the Crash Purple half.
* `CR3D1TS` shows the Vicarious Visions/`WWW.VVISIONS.COM` credit card.
* `CVTZ` cuts to the Cortex/Ripto dialogue scene.
* Party Mode shows a locked-pad world map (“WUMPA JUNGLE / GRIN AND BEAR IT”,
  “BONUS WORLD / JUMP, CRASH, JUMP!”); Trading Cards shows “VIEW CARDS / TRADE CARDS”.
* Savestate dump after entering `CR4SH`: buffer `CR4SH-----` at `0x02033F24`, plus a
  per-code record containing `CR4SH` at `0x02022390`.

**Derived (disassembly)**

* Both validators are `strcpy` + a linear `strcmp` chain, one comparison per table entry;
  the order of the comparisons follows the table order exactly (call-site literals
  `0x0806065C…0x080606A4` and `0x0906CAC8…0x0906CB88`).
* Per-code “used” indices 0,1,2,… are tested with `0x0902A2C4` and set with `0x0902A2D0`;
  the rejection text is `0x09075E44`.
* Gem/wumpa effects are integer adds to the counter at `[obj+0x6C]`.
* The keypad stores ASCII and pads with `-`; there is no checksum, no XOR key, no alphabet
  permutation. Any string that exactly matches a table entry is accepted.
* 10-character entries exist in the Crash table (`STR4WB3RRY`, `WVMP4FR00T`).

**Inferred**

* `ST4CY`, `R0BG`, `C0L1N`, `J0NNY`, `TR4V1S`, `SVNB1R`, `J450N`, `BR3NT` are staff-name
  codes that silently add a name/flag (they call `0x0900DDCC` with IDs from `0x0904A448`
  and print no text). The exact unlock was not observed.
* The four `XXXX/VV` headers are multiboot/link stub images (not reachable from the
  selector); their content was not executed.
* The pack was built by patching a boot selector into the Spyro image and replacing its
  header; the Crash image keeps its retail header.

## 8. Unknowns

* What `ST4CY`, `R0BG`, `C0L1N`, `J0NNY`, `TR4V1S`, `SVNB1R`, `J450N`, `BR3NT` actually
  change (credits names? card unlocks? flags).
* Whether the “already used” flags persist in the battery save after a power cycle; they
  are definitely in RAM and are cleared by loading a savestate.
* Whether `STR4WB3RRY` / `WVMP4FR00T` can be reached by any other route (e.g. a link-mode
  code path or a patched build). The strings are present and the handler branches exist,
  but the retail keypad cannot submit 10 characters.
* The exact purpose of the four embedded `VV` stub images.
* The full Spyro Party USA mini-game content (only the title and first stage were played).

## 9. Tooling

* `mGBA 0.10.5` (SDL) under `Xvfb :106` + `openbox`, driven with `xdotool` and `scrot`.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`.
* Python 3 + `capstone` for BL-target scans, PC-relative literal scans and call-site
  string extraction (`calls.py`, `map3.py`).
* `scripts` used here: `p0.py` (header/hash scan), `ptr2.py` (pointer scan), `calls.py`
  (BL scan + literal/string resolution), `auto_codes.py` / `slow_code.py` (keypad driver),
  `parse_ss.py` (PNG `gbAs` chunk → zlib → 397,312-byte state; EWRAM at offset `0x8100`
  maps to `0x02000000`).
* Savestate parsing detail: mGBA `.ssN` files are PNGs whose `gbAs` chunk is zlib-deflated
  state; EWRAM/IWRAM can be searched directly for typed strings.

## 10. Legal note

Only hashes, addresses, algorithms, table contents (short cheat strings) and behavior are
published here. No ROM, graphics, audio or extended game text is redistributed. The ROM is
required to reproduce the dynamic steps.
