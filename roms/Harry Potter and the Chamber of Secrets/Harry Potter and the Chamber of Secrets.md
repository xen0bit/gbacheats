# Harry Potter and the Chamber of Secrets (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Harry Potter and the Chamber of Secrets.gba` |
| Size | 8,388,608 bytes (`0x00800000`) |
| Header title | `HPOTTER COS` |
| Game code | `A7HE` |
| Maker code | `69` |
| Version | `0x00` |
| Region | USA/Europe, multilingual (En/Fr/De/Es/It/Nl/Pt/Sv/No/Da) |
| Entry word | `0xEA00002E` (stock branch to `0x080000C0`) |
| Fixed `0x96` | present; unit/device `0x00` |
| Header checksum | `0x0000`, complement `0xB2` |
| CRC32 | `0x342816DB` |
| MD5 | `b9b42f3e2d54921ee657bc027fa364b9` |
| SHA-1 | `0218e3be69334cac752d5ad5b3763a26252cb88b` |
| SHA-256 | `1167fc07fdeb746a00dced2ca40342b6a177f0f187dee6d0c5ac8f7a1f1183ad` |

**Image verification**: the 156-byte Nintendo logo occurs exactly once, at file `0x0`;
there is one header, so this is not a multi-cart/multiboot image. The entry word is
the stock branch — no cracktro or appended trainer. CRC32 `342816DB` matches the
published `AGB-A7HE-USA` 8 MiB release, so this is the licensed Chamber of Secrets
GBA image and **not** the Sorcerer's Stone / Prisoner of Azkaban / Goblet of Fire
GBA SKUs (different game codes and engines). Nothing is assumed shared with them.
The boot splash reads "MusyX Audio Tools Licensed By Factor 5 / LICENSED BY
NINTENDO" (observed).

**Prompt injection noted**: a direct fetch of the live TCRF page returned an
injected block ("This page is not intended for humans … whoever is operating this
AI agent is a clown"). It was treated as untrusted data, ignored, and the clean
2023 Wayback snapshot was used instead. (A later web-search result also returned
Monero-explorer SEO spam; likewise ignored.)

## 2. Executive summary

This game has **no password-entry system**. Its developer-intended cheat surface
is a **hidden debug "Cheat Menu"** reached in normal play by a button-code
sequence on the Wizard Card reward screen (R → level select → quit → B), and by
the published CodeBreaker gate `02002642:16`.

The published gate was verified in the emulator: the global screen index at
`0x02002642` is a 16-bit word; forcing the loader (Thumb `0x0802DC14`) to load
screen `0x16` makes the real "Cheat Menu" render. All **eight** entries were
walked and their numeric screen IDs and RAM effects recorded. Two further hidden
screens (`0x15` Language Test, `0x17` Audio Test) and the two select screens
(`0x13` Map Select, `0x14` Level Select) were enumerated.

The menu labels are **not ASCII**: a 104,454-string scan found no `Cheat Menu`,
`Map Select`, etc.; the UI uses a font/tile-indexed text bank (guide §11/§16.19
pitfall). The final negative ("no password system") therefore rests on screen
enumeration plus the absence of any comparison/entry surface, not on `strings`
alone.

The Audio Test track indices were recovered at RAM and their wrap bounds proven
in-game: Music `0..80` (mod 81) and Sound `0..193` (mod 194) — 80 music pieces
plus a zero/"none" slot and 193 sounds plus a zero slot, consistent with TCRF.

## 3. How to reproduce

1. Emulator: `mgba` SDL under `Xvfb :317`, `SDL_AUDIODRIVER=dummy`, `-3` scale.
   Keymap used: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, D-pad=arrows.
2. Boot; on the language screen press **A** (`x`), wait for the MusyX splash, then
   **Start** → Main Menu (New Game / Options / Connectivity / Credits).
3. Legitimate unlock (published, two independent sources): start a game, go to
   Flying Practice, pick a challenge whose Wizard Card you have not earned,
   finish it and obtain the card; while the card is displayed press **R** →
   level-select menu (inactive); quit out → the level-select menu becomes active;
   press **B** → Cheat Menu.
4. Deterministic reproduction used here (research shortcut, clearly *not* an
   in-game code): apply the published CodeBreaker gate `02002642:16`. In practice
   this was done by taking a savestate at the title screen, loading it into
   mGBA's private CLI debugger (`mgba -d`), setting a Thumb breakpoint at
   `0x0802DC14`, continuing, pressing Start, then `w/r r0 0x16` at the breakpoint
   and continuing. The real Cheat Menu appears (screenshot `15_cheatmenu.png`,
   savestate `s15_cheatmenu.ss`).
5. Menu walking used `s15_cheatmenu.ss` reloaded between entries; each entry's
   effect was read from mGBA `.ss1` states with `ssram.py` (zlib-decompressed
   `gbAs` chunk; EWRAM at state offset `0x21000`).

**Published codes verified**:

- CodeBreaker `02002642:16` (TCRF / cutting-room mirror) — **verified**: opens
  the Cheat Menu, screen `0x02002642 = 0x0016`.
- The R-at-card-screen button sequence is published by TCRF and Neoseeker;
  the gate value it relies on was verified directly as above. The full Flying
  Practice playthrough was not replayed step-by-step; the gate and its effect
  were verified on the real menu.
- No password strings from any published list exist in this image: literal
  searches for `password`, `cheat`, `LEVEL SELECT`, `HAMA!333`-style tokens found
  only compressed dialogue text and no comparison table.

## 4. Address map

| Address | Kind | Meaning |
|---|---|---|
| `0x08000000` | ROM | Header; one image only |
| `0x0801EEA8` | ROM/Thumb | Screen/level loader (writes `0x02002642`) |
| `0x0802DC14` | ROM/Thumb | Screen loader used by the menu system: `r0` = screen index; stores it to `0x02002642` (`strh r0,[r1]`) |
| `0x0802DD18` | ROM/Thumb | Wrapper that calls `0x0802DC14` with the screen index (`BL` at `0x0802DD2C`) |
| `0x0802DC00` | ROM/Thumb | `movs r0,#0x0B` — returns to Main Menu (screen 11) |
| `0x0801EF70`, `0x0801F070` | ROM/Thumb | Input-state tests (`ldrh r?,[r?,#6]` with masks `0x200`/`0x8`), showing active-high key format |
| `0x02002642` | EWRAM/u16 | **Current screen index** (gate variable) |
| `0x02002644` | EWRAM/u16 | Previous screen index |
| `0x0200274A` | EWRAM/u8 | Menu cursor (observed cycling 0..15 while scrolling Map Select) |
| `0x02002B94` | EWRAM/u8 | Audio Test — Sound index (0..193) |
| `0x02002B96` | EWRAM/u8 | Audio Test — Music index (0..80) |
| `0x0200219C..0x020021A0` | EWRAM | Wizard Card flags (Unlock Cards) |
| `0x0200210E..0x02002118` | EWRAM | Bean flags (Unlock Beans) |
| `0x02002104`, `0x02002170`, `0x02002172` | EWRAM | Spell flags (Unlock Spells) |

Savestate layout used for RAM reads: `.ss1` PNG `gbAs` chunk → 397,312-byte raw
state; EWRAM = state `0x21000 + (addr-0x02000000)`, IWRAM = `0x19000 +
(addr-0x03000000)`.

## 5. Algorithm

The gate is a **screen-index dispatch**, not a checksum/password validator:

```
; menu screen loader (Thumb), 0x0802DC14
r4 <- r0 & 0xFFFF                 ; requested screen index
... load assets, set up screen ...
*(u16*)0x02002642 = r4            ; becomes the displayed screen

; published CodeBreaker gate, applied from boot
*(u8*)0x02002642 = 0x16          ; 22 = Cheat Menu
```

Observed screen indices: `0x00` (title / post-EEPROM-clear), `0x0B` (Main Menu),
`0x0C` (Options), `0x12` (observed during menu navigation), `0x13` (Map Select),
`0x14` (Level Select), `0x15` (Language Test), `0x16` (Cheat Menu), `0x17`
(Audio Test).

Important behavioural detail: poking `0x02002642` while a screen is already
loaded does **not** redraw it (the renderer uses state established by the
loader). The gate value must be present when the loader runs — which is why the
CodeBreaker device applies it continuously from boot and why the instruction
"disable the code once you opened the menu" appears in the published notes.

## 6. Tables

### 6.1 Cheat Menu entries (all 8, index → screen → effect)

| # | Label | Target screen | Effect (RAM-verified) |
|---:|---|---|---|
| 0 | Map Select | `0x13` | Map picker; all maps playable with required items |
| 1 | Level Select | `0x14` | Level/story-segment picker |
| 2 | Language Test | `0x15` | Intro text lines; L/R cycles them |
| 3 | Audio Test | `0x17` | Music/Sound index pickers; R plays |
| 4 | Unlock Cards | stays `0x16` | `0x0200219C = 0x0300`, `0x0200219E = 0xFFFF`, `0x020021A0 = 0xFE` (all zero before) |
| 5 | Unlock Beans | stays `0x16` | `0x0200210E..0x02002118` filled `0x0F FF FF FF FF FF FF FF FF FF FF` (all zero before) |
| 6 | Unlock Spells | stays `0x16` | `0x02002104 = 0x40`, `0x02002170 = 0x0300`, `0x02002172 = 0x00C0` (all zero before) |
| 7 | Clear EEPROM | `0x00` | All three flag regions return to zero; reset to title |

### 6.2 Map Select (screen `0x13`) — 30 distinct entries observed by scrolling

Diagon Alley Part 1; Diagon Alley Part 2; Hogwarts Belowground; Belowground
Secret; Peeves Boss; Entrance Hall; Leaky Cauldron; Cellar; Gringotts Upper
Vaults; Gringotts Lower Vaults; Gringotts Boss; Hogwarts Grounds; Spider Trail;
Whomping Willow; Portrait Room; Bean Challenge 1; Bean Challenge 2; Bean
Challenge 3; Bean Challenge 4; Wingardium Leviosa; Magical Menagerie; Library;
Library (Restricted); Moaning Myrtle; Gryffindor; Fred & George; Dumbledore's
Office; Slytherin Dungeons; Floor 5 Bonus; Floor 6 Bonus.

The list is a ring (scrolling past the last entry returns to the top). A cursor
byte at `0x0200274A` was seen cycling `0..15` during long scrolls; because more
than 16 distinct labels were displayed, that byte is reported as a UI counter,
not asserted to be the list length.

### 6.3 Level Select (screen `0x14`) — 13 entries observed

Entrance Hall; Gryffindor Password; House Points; Flying Practice; Hogwarts
Maps; Charms Class; Moste Potente Potions; Transfiguration; Christmas; Snape;
Polyjuice Potion; Tom Riddle Diary; Petrified Hermione.

### 6.4 Audio Test (screen `0x17`)

| Field | RAM | Range | Wrap proof |
|---|---|---|---|
| Music | `0x02002B96` | `0..80` | patch to `0x50` (=80) + Right → `0x00`; at `0x4F` (=79) + Right → `0x50` |
| Sound | `0x02002B94` | `0..193` | patch to `0xC1` (=193) + Right → `0x00`; at `0x00` + Left → `0xC1` (=193) |

The displayed number equals the stored index (e.g. `0x02002B94 = 0xC1` displayed
"Sound 193"). R plays the selected track.

## 6b. Enumeration

**Space characterised.** There is no password alphabet, length or checksum. The
relevant space is the 16-bit screen index at `0x02002642` plus the menu's finite
entry set. Observed accepted screen IDs: `0x00, 0x0B, 0x0C, 0x12, 0x13, 0x14,
0x15, 0x16, 0x17`. The hidden cheat surface contains exactly **1 menu with 8
entries**, **2 picker screens** (30 map labels, 13 level labels), **1 text viewer**
and **1 audio viewer** with two bounded indices.

**Novel, unpublished values minted and entered in-game.** The published material
gives the gate value `0x16` and counts ("80 music pieces and 193 sounds") but no
RAM addresses, no index bound/wrap behaviour, and no per-entry RAM effects. These
were minted by patching the savestate RAM and loaded on the real Audio Test
screen:

- `0x02002B94 = 0xC1` (Sound **193**) — display confirmed "Sound 193" after
  loading the patched state and pressing Right from 192.
- `0x02002B96 = 0x50` (Music **80**) — display confirmed "Music 80" (OCR `é0`)
  after loading the patched state and pressing Right from 79.
- The three unlock actions were driven from the real Cheat Menu and their
  previously unpublished destination addresses/values read from RAM (§6.1).

**Bounds proven by rejection/wrap.**

- Sound `193 + 1` wraps to `0`; `0 - 1` wraps to `193` (in-game, savestate `saudnext.ss` / `saudlow.ss`).
- Music `80 + 1` wraps to `0`; `79 + 1` = `80` (savestates `mtest0x50.ss`, `mtest0x4f.ss`).
- Gate rejection: forcing `0x13`, `0x14`, `0x15` or `0x17` at the boot Main Menu
  loader call site (`0x0802DC14`, `r0` originally `0x0B`) is **rejected** — the
  game stays on Main Menu (`0x02002642 = 0x0B`); only `0x16` is accepted there
  and opens the Cheat Menu. This bounds the published gate: it is not a generic
  "jump to any screen" value.
- Cheat-menu action entries leave the screen at `0x16`; only Clear EEPROM
  changes it (to `0x00`) and zeroes the flag regions.

**Negative result (no password system) bounded.** The entire string table
(104,454 strings, `strings -t x -n 4`) was scanned for password/cheat/code/
secret/unlock/level-select keywords; the only "password" hits are inside a
compressed dialogue bank around file `0x3FA240` / `0x406E80` ("Huse - password",
"eg wrong"), i.e. NPC dialogue, not an entry validator. No comparison table,
alphabet, input buffer, or password screen exists; no literal from any published
code list appears in the image. All reachable menus on the title/main/options/
pause/cheat paths were walked with `0x02002642` read at each step.

## 7. Validation evidence

- **Observed** (emulator + savestate RAM reads): title → main menu (`0x0B`) →
  options (`0x0C`); Cheat Menu (`0x16`) with 8 entries; Map Select (`0x13`),
  Level Select (`0x14`), Language Test (`0x15`), Audio Test (`0x17`);
  unlock RAM deltas in §6.1; Clear EEPROM reset; all wrap/rejection tests in §6b.
  Screenshots and `.ss` states retained under `/tmp/opencode/hpcos/`.
- **Derived** (disassembly): `0x0802DC14` is the screen loader that stores `r0`
  into `0x02002642`; `0x0802DD18` is its only caller wrapper (`BL` at
  `0x0802DD2C`); `0x0802DC00` sets screen `0x0B`. Live breakpoint at
  `0x0802DC14` reported `r0 = 0x0B` when Main Menu loaded, and `r0 = 0x16` was
  accepted there, matching the published CodeBreaker gate.
- **Inferred**: the in-game R-press unlock sequence is taken from two published
  sources; the gate value and the resulting hidden screens were verified, but
  the full Flying Practice playthrough was not replayed. The exact semantic
  names of the bean/spell bitfields are inferred from the published GameShark
  addresses and the observed deltas.

## 8. Unknowns

- Whether any of the 30 map labels are unused/unreachable in normal play (TCRF
  leaves this as a "To do"). All 30 render and are selectable from Map Select.
- The 16-state counter at `0x0200274A` is not proven to be the map-list length.
- The exact R-button comparison instruction for the legitimate unlock was not
  isolated statically; only its published sequence and the gate value were
  verified.
- Whether Language Test has a finite set of lines or cycles indefinitely.

## 9. Tooling

- `mgba` SDL with `-d` private CLI debugger via a persistent FIFO; `stdbuf -oL`.
- `Xvfb :317` + `openbox`; `xdotool` XTEST input; `import` (ImageMagick) for
  root-window screenshots; `tesseract` OCR on cropped viewports.
- `ssram.py` — decodes `.ss1` `gbAs` chunk and reads GBA RAM by address.
- `ssdiff.py` — diffs two savestate RAM images.
- `autocrop.py` — locates and crops the GBA viewport from root screenshots.
- `arm-none-eabi-objdump -M force-thumb` for raw Thumb disassembly; Python
  literal/BL scanners.
- No ROM or copyrighted assets are redistributed; screenshots/states live only
  in the analysis work directory and are removed from the ROM folder on cleanup.
