# Dragon Ball Z: The Legacy of Goku (GBA) — Reverse Engineering Report

## 1. Target identity

| Property | Value |
|---|---|
| File | `roms/Dragon Ball Z: The Legacy of Goku/Dragon Ball Z: The Legacy of Goku.gba` |
| Size | 8,388,608 bytes (0x800000, 8 MiB) |
| `file(1)` | Game Boy Advance ROM image: "DBZ LGCYGOKU" (ALGE70, Rev.00) |
| Header title / code / maker / version | `DBZ LGCYGOKU` / `ALGE` / `70` / 0 |
| Entry word | `0xEA00002E` (stock `b 0x080000C0`) |
| Fixed 0x96 / complement / checksum | `0x96` / `0x6C` / `0x0000` |
| MD5 | `3100fc5a4427a7b0cc20b861134e60f2` |
| SHA-1 | `a3c8c76742f11fc6a3f6e3fcca20992458cac0b5` |
| SHA-256 | `3ba9919e26704b0f5fdc2bfabc7f7a0404c71413761d38abcd94224c3bd4b1b9` |

**Phase 0:** Nintendo-logo scan over all 8 MiB found **exactly one** GBA header, at file offset 0x4
(header base 0x0). This is a genuine **standalone** image, not a multi-game cart, and no
appended trainer/cracktro is present (stock entry branch; no extra logo/header). The `.sav`
created by mGBA is 512 bytes (EEPROM).

**Relationship to the combo-cart report.** The earlier report for
`2-in-1 - Dragon Ball Z Gamepack - The Legacy of Goku I & II` analysed a different, 16 MiB
build whose LOG1 half sits at file 0x40000 (ROM base 0x08040000). The same five debug-menu
strings exist in both, but byte-for-byte comparison shows ~7.1 million differing bytes and
**non-constant offsets** (e.g. `Go To Map`: standalone file 0x5C2D8C vs combo 0x602F50,
Δ=0x401C4; `Text Speed`: 0x53A9E8 vs 0x57AD14, Δ=0x4032C). **None of the combo report's
addresses apply here**; everything below was re-derived from this image. The combo finding
itself (5 rows, chord, two entry points) is **confirmed** here, with two corrections: the
pause menu has **7** entries (an extra `Credits` row), and the buttons are **edge-triggered**
(one step per press), not level-triggered per frame.

## 2. Executive summary

This standalone LOG1 image has **no password/passcode system and no on-screen code entry**.
It has **three developer-intended input codes**, all verified against the ROM and on the
real screens:

1. **Debug menu** — on the Options screen, cursor on `Text Speed`, hold **L+R+Up** and press
   **A**. Works from both title Options and in-game pause→Options. The menu has **five** rows:
   `Go To Map`, `Sprite Viewer`, `Play SFX`, `Play Music`, `Show Image`. Published lists name
   only four rows and use different labels ("Level Select, Sound Test, Sprite Viewer, Photo
   Gallery"). Bounds: map 42 entries, SFX 31, music 18, images 15 — all clamped in code and
   proven by in-game rejection.

2. **Invincibility** — during the intro movie press **Up, Down, Left, Right, B, A**. A generic
   ring-buffer matcher (`0x0800A6B2`) checks the last six key presses against the u16 table at
   `0x08011462`; on a match its caller (`0x080048FA`) plays SFX 7 and writes `1` to the flag
   at `0x03000C18`. The damage routine at `0x080073D8` reads this flag and returns the
   "no damage" result while it is set. RAM proof: flag `0x00 → 0x01` on the correct sequence,
   `0x00` for five wrong sequences (including the widely published **A-then-B** variant,
   which this ROM rejects).

3. **In-game reset** — **A+B+R+L+Start+Select** soft-resets to the boot/legal screen
   (published on CheatingDome; verified here).

A **third, unpublished hard-coded 4-press sequence** (`Left, Right, A, B`, table
`0x0800FE42`) exists with a handler at `0x08003B4`, but no BL, branch, or 32-bit pointer to
that handler exists in the image, and it produced no observable effect on any screen tested;
it is reported as an unwired/dead handler (§8).

## 3. How to reproduce

```
Xvfb :318 -screen 0 1024x768x24 &
DISPLAY=:318 openbox &
DISPLAY=:318 SDL_AUDIODRIVER=dummy mgba -3 "<ROM>" &
```

mGBA 0.10.x SDL keymap (verified on these screens): A=`x`, B=`z`, L=`a`, R=`s`,
Start=`Return`, Select=`BackSpace`, D-pad=arrows. Hold keys ~120–200 ms.

**Debug menu (title path):** boot → Start through the Webfoot splash, legal screen and intro
(~30–45 s) → title ("Press Start") → Start → main menu (New Game/Continue/Options) →
Down×2 → A (Options, cursor on `Text Speed`) → hold `a`+`s`+`Up`, tap `x`. The five-row
debug menu appears.

**Debug menu (in-game path):** from a started game press Start → pause
(Quests/Inventory/Attacks/Save/Options/Credits/Exit) → Down×4 → A → same chord. Values
persist between the two entry points.

**Debug menu controls:** Up/Down move the row cursor; Left/Right decrement/increment the
selected row's number (one step per press); A executes; B/Select/Start do not leave the
menu or the gallery (reset required). Executing `Go To Map` warps into the game; executing
`Show Image` opens the full-screen gallery (also no cancel path).

**Invincibility:** on a fresh boot, during the intro movie (verified at the snowy
Goku-vs-Raditz scene ~8 s after the first Start), press Up, Down, Left, Right, `z` (B), `x`
(A). Read `u8 [0x03000C18]`: 0 before, 1 after.

**In-game reset:** hold `x`+`z`+`s`+`a`+`Return`+`BackSpace` for ~0.4 s → soft reset.

Screenshots were captured with `import -window root` and cropped `720x480+154+170` to the
3× GBA viewport. Savestates (`Shift+F<n>` save, `F<n>` load) were used for every comparison;
mGBA `.ss*` files are PNG with a zlib `gbAs` chunk: decompressing yields a 397,312-byte raw
state with IWRAM at raw `0x19000` (address `0x03000000`) and EWRAM at raw `0x21000`
(address `0x02000000`).

## 4. Address map

All addresses are GBA ROM addresses (file offset = address − 0x08000000).

### General / input

| Address | Meaning |
|---|---|
| `0x08000000` | header, `DBZ LGCYGOKU` / `ALGE` / `70`, rev 0 |
| `0x03003D10` | key-state struct (u32 pointer stored at `0x0800A6EC`): `[+0]` head index, `[+4]` count u16, `[+0xC..+0x13]` 8-byte ring buffer of press masks |
| `0x03003D14` | processed key halfword (A=bit0, B=bit1, Left=bit4, Right=bit5, Up=bit6, Down=bit7, R=bit8, L=bit9) |
| `0x03003D1C`–`0x03003D23` | 8-entry key-press ring buffer (active-high masks) |

### Debug menu

| Address | Meaning |
|---|---|
| **`0x08000C02`** | **debug-menu per-frame handler (Thumb)**; `push {r3,r4,r5,lr}`; `r0` = menu object (`[+4]`=row, `[+5]`=map, `[+6]`=SFX, `[+7]`=music, `[+8]`=image) |
| `0x08000C24` | `cmp r0,#5` and 5-word jump table at `0x08000C34` (`u16` half-offsets `5,0x24,0x2C,0x4B,0x96`) |
| `0x08000C3E` | row 0 body — `Go To Map` |
| `0x08000C7C` | row 1 body — `Sprite Viewer` |
| `0x08000C8C` | row 2 body — `Play SFX` |
| `0x08000CCA` | row 3 body — `Play Music` (also volume keys) |
| `0x08000D60` | row 4 body — `Show Image` |
| `0x08000C5A` | `cmp r1,#41` — map clamp (42 entries) |
| `0x08000CA8` | `cmp r1,#30` — SFX clamp (31 entries) |
| `0x08000CE6` | `cmp r1,#17` — music clamp (18 entries) |
| `0x08000D7C` | `cmp r1,#14` — image clamp (15 entries) |
| `0x08000E20` | literal `0x03003D14` — key-state halfword |
| `0x08000E24` | literal `0x081CA09C` — map pointer table (42 × u32) |
| `0x08000E28` | literal `0x030007F4` — sprite-viewer state |
| `0x08000E2C` | literal `0x085C0B0C` — SFX table (31 × 12 bytes) |
| `0x08000E30` | literal `0x08591F3C` — music table (18 × 12 bytes) |
| `0x08000E34/E38/E3C/E40` | `0x03003CFE / 0x03003CFD / 0x03003CFF / 0x03003D02` — volume/flag bytes |
| `0x08000E44/E48/E4C` | `0x03003B64 / 0x03003B60 / 0x03003B70` — gallery state |
| `0x0800FEAC` | debug-menu descriptor header `{1,3,0x12,0x13,5,0}` |
| `0x0800FEB8`–`0x0800FEC8` | five u32 item pointers (order: Map, Sprite, SFX, Music, Image) |
| `0x085C2D6C / 84 / 98 / AC / C0` | item records `{04,id,00,00,ptr}` for Sprite / Map / SFX / Music / Image |
| `0x085C2D74 / 8C / A0 / B4 / C8` | ASCII labels `Sprite Viewer` / `Go To Map` / `Play SFX` / `Play Music` / `Show Image` |
| `0x0853A9BC / 9D4 / 9E8` | Options ASCII strings `Music Volume` / `SFX Volume` / `Text Speed` |

### Button codes

| Address | Meaning |
|---|---|
| `0x08011462` | invincibility sequence, 6 × u16 active-high masks: `0x40,0x80,0x20,0x10,0x02,0x01` |
| **`0x0800A6B2`** | **generic ring-buffer validator** `check(u16 len, u16* table)` → 1 on match, 0 otherwise |
| `0x080048FA` | invincibility caller: `check(6, 0x08011462)`; on match plays SFX 7 (`bl 0x0800ACFE`) and stores `1` to `[0x03000C18]` (pointer at `0x080049A8`) |
| `0x03000C18` | invincibility flag (u8): 0 = normal, 1 = invincible |
| `0x080073D8` | damage routine reads the flag (`ldr r1,[pc] @ 0x080075F8` → `0x03000C18`; `cmp r0,#0` → return 2 = no damage when set and player state == 1) |
| `0x0800FE42` | second (unwired) sequence, 4 × u16 masks: `0x20,0x10,0x01,0x02` = Left,Right,A,B |
| `0x08003B4` | handler for the 4-press table: sets `[obj+4]=0xF4`, `[obj+5]=2` (no xrefs found) |

## 5. Algorithm

### 5.1 Debug-menu gate

A screen-transition check, not a table lookup. With the Options screen active and the cursor
on `Text Speed`, the processed key word must contain **L|R|Up|A** = `0x0200|0x0100|0x0040|
0x0001 = 0x0341`. The Up first moves the cursor to `Exit`; the held L/R are the gate.
Rejected neighbours (all observed): `L+R+A` (`0x0301`) only changes Text Speed; `L+R+Down+A`
(`0x0381`) moves the cursor; `L+Up+A` and `Up+A` exit Options to the pause menu.

### 5.2 Debug-menu handler (`0x08000C02`)

```
keys = *(u16*)0x03003D14
switch (menu->row) {                       # row = byte [obj+4], 0..4
 case 0:  # Go To Map
   if (keys & LEFT)  and map  > 0:  map--  # byte [obj+5]
   if (keys & RIGHT) and map  < 41: map++
   if (keys & A): p = *(u32*)(0x081CA09C + map*4); warp(p->mapdata + 0x28)
 case 1:  if (keys & A): open_sprite_viewer(0x030007F4)
 case 2:  # Play SFX  (byte [obj+6], clamp 30)
   ... if (keys & A): play_sfx(0x085C0B0C + 12*sfx)
 case 3:  # Play Music (byte [obj+7], clamp 17)
   ... if (keys & A): play_music(0x08591F3C + 12*mus)
   if (keys & B): volume_down(); if (keys & R/L): volume_up(); ...
 case 4:  # Show Image (byte [obj+8], clamp 14)
   ... if (keys & A): show_image(img)       # uses 0x03003B60/64/70
}
```

The displayed map number is 1-based (counter 0 shows `01`); SFX/music/image numbers are
0-based. In this build Left/Right are **edge-triggered**: holding Right for 0.8 s advances
the counter by one, so each press must be released. The published combo report's
"level-triggered per-frame" behaviour does not apply to this image.

### 5.3 Button-sequence validator (`0x0800A6B2`)

```
check(len, table):
    s = *(void**)0x0800A6EC                 # 0x03003D10
    if s->count == 0: return 0
    i = s->head - 1;  if i < 0: i = 7        # 8-entry ring
    for j = len-1 down to 0:
        if table[j] != s->ring[i]: return 0  # table entries are u16, ring entries u8
        i -= 1;  if i < 0: i = 7
    return 1
```

The ring is filled by the game's normal key-processing code (active-high masks). The
validator is generic; a whole-ROM BL scan found **exactly two callers** (§6b).

## 6. Tables

### 6.1 Debug-menu rows (confirmed by strings + emulator)

| Row | Label | Pointer | Action | Counter / bound | Display |
|---:|---|---|---|---|---|
| 0 | `Go To Map` | `0x085C2D84` | warp to map table entry | 0..41 (`cmp #41`) | 1..42 |
| 1 | `Sprite Viewer` | `0x085C2D6C` | character animation viewer | viewer-internal | — |
| 2 | `Play SFX` | `0x085C2D98` | play SFX-table entry | 0..30 (`cmp #30`) | 0..30 |
| 3 | `Play Music` | `0x085C2DAC` | play music-table entry | 0..17 (`cmp #17`) | 0..17 |
| 4 | `Show Image` | `0x085C2DC0` | full-screen gallery | 0..14 (`cmp #14`) | 0..14 |

The map table has 42 entries (`0x081CA09C`), SFX 31 (`0x085C0B0C`), music 18
(`0x08591F3C`). The five labels are plain ASCII (unlike most in-game UI, which is
font/tile-encoded), which is why `strings` finds them.

### 6.2 Button-code literals

| Code | Length | Table (ROM) | Masks | Effect |
|---|---:|---|---|---|
| Invincibility | 6 | `0x08011462` | Up,Down,Left,Right,B,A | flag `0x03000C18` = 1, SFX 7, no damage |
| 4-press (unwired) | 4 | `0x0800FE42` | Left,Right,A,B | handler `0x08003B4`: counter=0xF4, state=2 |
| Reset chord | 6 simultaneous | — | A+B+R+L+Start+Select (`0x30F`) | soft reset to legal screen |

### 6.3 Menu enumeration (observed)

* Title (Press Start) → main menu: `New Game / Continue / Options`.
* Options: `Text Speed / Music Volume / SFX Volume / Exit` (values Low/04/08).
* Pause (Start in game): `Quests / Inventory / Attacks / Save / Options / Credits / Exit`
  — **7 rows** (the combo report lists 6, omitting `Credits`); status panel shows
  Level, Experience, To Next Level, HP, Ki, Time.
* Debug menu: the five rows above, plus `Sprite Viewer` (list of ~character animation-set
  names such as `armyguy1..4`, `ass1..3`, `boy1..3`, `bubbles`, `bulma`, `burter`, … with a
  live sprite preview) and the `Show Image` gallery (15 full-screen illustrations).
* No character/mode select, no hidden-character screen, no unlockable menu, no password
  entry, no sound-test reachable from a normal menu.

## 6b. Enumeration

### 6b.1 Space definition

**There is no password alphabet, no literal password table, and no checksum.** The entire
input surface is button input:

* **Gate space:** one exact 10-bit mask, `0x0341`, evaluated on the Options screen with the
  cursor on `Text Speed`. Neighbouring masks are rejected (§5.1).
* **Debug-menu value space:** 42 + 31 + 18 + 15 = **106 concrete selections** plus the
  scrollable sprite viewer. Each counter's domain is exactly its table length and is clamped
  by the handler's `cmp` instructions, so no larger index is representable through the UI.
* **Button-sequence space:** an 8-entry ring of active-high masks; two hard-coded tables are
  passed to the single validator (`len=6` invincibility, `len=4` unwired). The validator has
  **exactly two callers** (whole-ROM Thumb-BL scan), so the 6-press and 4-press sequences are
  the complete set of validator-based button codes in this image. The soft-reset chord is a
  separate all-at-once mask check.

### 6b.2 Novel selections / codes (absent from published lists)

No published source gives numeric debug values; the following were minted here and confirmed
on screen:

| Selection | Value | Result (observed) |
|---|---:|---|
| `Go To Map` | 42 (last) | warp into the rocky platform area (Kami's Lookout) with Goku Lv1, HP 105 / Ki 100 |
| `Show Image` | 08 | Goku riding the Flying Nimbus over clouds |
| `Show Image` | 14 (last) | clamps at 14; RIGHT is a no-op |
| Debug rows 2 & 3 | — | `Play SFX` and `Play Music` are **separate** unpublished entries (published lists collapse them into one "Sound Test") |

The invincibility table's exact ordering (**B before A**) corrects the widely published
"Up, Down, Left, Right, A, B" variant (CheatingDome / "Unlimited live"), which this ROM
rejects (§6b.3).

### 6b.3 Bounds proven by rejection

| Test | Result | Evidence |
|---|---|---|
| Invincibility correct `U,D,L,R,B,A` | flag `0x00 → 0x01`; ring = `40 80 20 10 02 01` | savestate RAM read |
| Wrong order `D,U,R,L,B,A` | flag stays `0x00`; ring = `80 40 10 20 02 01` | savestate RAM read |
| Missing final A (`U,D,L,R,B`) | flag `0x00` | savestate RAM read |
| Reversed (`A,B,R,L,D,U`) | flag `0x00` | savestate RAM read |
| Published A-then-B variant (`U,D,L,R,A,B`) | flag `0x00`; ring = `40 80 20 10 01 02` | savestate RAM read |
| `Show Image` = 14, press RIGHT | stays 14 | screenshot `img14_bound2_crop.png` |
| `Go To Map` = 42, press RIGHT | stays 42 | screenshot `map42_extra_crop.png` |
| `Go To Map` = 01, press LEFT | stays 01 (minimum) | screenshot `map_min.png` |
| L+R+A (no Up) on Text Speed | no debug menu; Text Speed Low→Medium | `gate_LRA_crop.png` |
| L+R+Down+A | no debug menu; cursor → Music Volume | `gate_LRDA_crop.png` |
| L+Up+A / Up+A | no debug menu; Options closes | `gate_LUA_crop.png`, `gate_UA_crop.png` |
| B alone on main menu | returns to title — proves the earlier 4-press "return" was normal B behaviour, not the unwired code | `after_B_wait_crop.png` |
| In-game reset chord | soft reset to boot/legal screen | `reset_after_crop.png` |

The handler clamps (`cmp #41 / #30 / #17 / #14`) independently bound all four counters.

### 6b.4 Excluded space (bounded negative)

* **ASCII keyword scan, whole 8 MiB** (case-insensitive): `password`, `passcode`, `cheat`,
  `secret`, `unlock`, `code`, `debug`, `sound test`, `level select`, `hercule`, `scouter`,
  `text window`, `gameshark`, `codebreaker`, `invincib`, `enter code`, `keyword`, `keyword`
  → **0 hits each**. `+0x20` shifted-case and UTF-16LE scans for the same words → 0 hits.
  The only cheat-relevant ASCII is the five debug-menu labels and the Options labels.
* **Literal tables:** `0x0340` occurs 393 times as u16 and 5 times as u32 (generic data);
  `0x0341` occurs 548/4 times — none in a menu key-mask table. The 6-mask invincibility
  literal occurs **exactly once** (0x08011462). Uppercase/digit runs ≥6: 5,129; inspection of
  the longest shows compressed 4bpp tile data, not password strings.
* **Menu walk:** every reachable screen was visited (§6.3). No password entry, no shop code,
  no character/mode select, no unlockable list, no link/multiplayer screen.
* **Published codes checked:** GameFAQs "Debug Menu" chord — **correct** (contents undercount
  rows); GameFAQs/CheatingDome "Invincibility U,D,L,R,B,A" — **correct**; CheatingDome
  "Unlimited live … U,D,L,R,A,B" — **rejected on this ROM**; CheatingDome "In-game reset
  A+B+R+L+Start+Select" — **correct**; TCRF "Debug Mode" (highlight Exit, L+R+Up+A) —
  equivalent and correct; TCRF regional notes (European `language`/CodeBreaker LOG2 details)
  — not applicable to this US standalone image; RPGClassics encrypted GameShark codes —
  out of scope (memory-edit codes).

## 7. Validation evidence

| # | Claim | Type | Evidence |
|---:|---|---|---|
| 1 | Standalone single-header 8 MiB US image | Observed + Derived | logo scan (1 hit), header dump, hashes, `file(1)` |
| 2 | Combo addresses do not transfer | Derived | byte comparison (~7.1 M diffs, non-constant string shifts) |
| 3 | L+R+Up+A on Text Speed opens 5-row debug menu | **Observed** | `dbg1_crop.png`, `pause_dbg_crop.png` |
| 4 | Both title and pause Options are entry points | **Observed** | `dbg1_crop.png`, `pause_dbg_crop.png` |
| 5 | Handler `0x08000C02`, 5-way jump table, clamps 41/30/17/14 | Derived | `objdump -M force-thumb`, literals at 0x08000E20..E4C |
| 6 | Map 42 warps; image 08 renders; image clamps at 14 | **Observed** | `warp42_crop.png`, `img14_exec_crop.png`, `img14_bound2_crop.png` |
| 7 | Pause menu has 7 rows incl. Credits | **Observed** | `pause0_crop.png` |
| 8 | Invincibility masks at 0x08011462, validator 0x0800A6B2, setter 0x080048FA, flag 0x03000C18 | Derived | disassembly + literal pool |
| 9 | Correct sequence sets flag 1; 5 wrong sequences leave it 0 | **Observed** | savestate RAM reads (§6b.3) |
| 10 | Flag read by damage routine → no-damage result | Derived | `0x080073D8`: `cmp r0,#0` → return 2 |
| 11 | Reset chord soft-resets | **Observed** | `reset_after_crop.png` |
| 12 | No password system | Derived from bounded search | §6b.4 keyword/table scans + full menu walk |
| 13 | Second 4-press table is unwired in this build | Observed + Derived | no BL/B/u32 xref to `0x08003B4`; no effect on title/menu/sprite/gallery |

## 8. Unknowns

1. **Effect of the 4-press table (`Left,Right,A,B`, handler `0x08003B4`).** The handler code
   would set a screen object's counter to `0xF4` and state to `2`, then transition via
   `0x0800CFEE(r1=0x08337218)` and `0x08009744`, but a whole-ROM scan found **no** BL, B, or
   32-bit pointer to the handler, and pressing the sequence on the title, main menu, and
   sprite viewer produced no change. It is probably dead/unwired in this standalone build;
   an indirect (computed) call cannot be completely excluded.
2. **Exact audible output of the SFX/music rows.** mGBA ran with `SDL_AUDIODRIVER=dummy`; the
   menu action and table lookup are observed, the emitted sound is not.
3. **Full sprite-viewer list count.** Labels are font/tile-encoded; the viewer was scrolled
   in-game (screenshot `sprite_viewer_crop.png`) but the complete entry count was not
   extracted statically.
4. **Long-term behaviour of the invincibility flag.** The flag is proven to be set and to be
   read by the damage routine (return 2 = no damage); a full enemy-fight round trip was not
   played, and the published note that it fails on Snake Way spikes was not re-tested.
5. **Header checksum 0x0000.** Complement byte is `0x6C`; no patch/trainer was found, but the
   zero checksum is recorded as an identity detail rather than interpreted.

## 9. Tooling

* mGBA 0.10.x (SDL), Xvfb `:318`, openbox, `xdotool`, `import`/ImageMagick; a private copy
  named `mgba-logoku1` was used so sibling sessions' process cleanup could not target it.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`.
* Python 3 + capstone 5.0.7 for PC-relative literal, BL/B-target and byte-pattern scans.
* `savestate.py` (zlib-decompresses the `gbAs` PNG chunk) for IWRAM/EWRAM RAM proofs;
  `gba.py` (XTEST keypress/screenshot/crop helpers) in `/tmp/opencode/logoku1/`.
* Screenshots: up to ~20 720×480 crops in `/tmp/opencode/logoku1/`; key files named in §7.

## 10. Legal note

No ROM, extracted graphics, music, or game text is redistributed. Only hashes, addresses,
short UI labels needed to identify rows, and this analyst's own screenshots/notes are
included.
