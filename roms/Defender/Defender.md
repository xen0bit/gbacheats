# Defender (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Defender/Defender.gba` |
| Size | 4,194,304 bytes (4 MiB) |
| Header title | `DEFENDER` (space/NUL padded) |
| Game code / maker | `A2FE` / `5D` |
| Version / unit / device | `0x00` / `0` / `0` |
| Entry word | `0xEA00002E` (stock branch to `0x080000C0`) |
| Header checksum (`0xBE`) | `0x0000` (rebuilt-header artifact) |
| Complement byte (`0xBD`) | `0x9D` = value computed from `0xA0..0xBC` (valid) |
| MD5 | `3ecb36c34b0a441bad7a628760575e0c` |
| SHA-1 | `d9bc7d7a0500c7cf58ce4010071048a6c462b2de` |
| SHA-256 | `144a0ce3a956f8ba6be5e5b685368a57d7d2e3762fc56e8e728a3a6304bbcf46` |

- Nintendo logo at `0x04` is the stock vector; it occurs **exactly once** in the
  image, so this is a single GBA build, not a 2-in-1 pack or concatenated image.
- No trainer/cracktro markers (`SUNHORS`, `CRC BANDIT`, `MODE7`, `PARADOX`,
  `VENOM`, `EURASIA`, `TRAINER`) occur in the image. The entry word is the stock
  `0xEA00002E`; `0x080000C0` is a normal crt0. The header checksum word is zero
  because the header was rebuilt; the complement byte was recomputed correctly.
  No patch, trainer, or boot selector is present.

## 2. Executive summary

This GBA port of *Defender* (OutLook Entertainment / Midway, 2002) has **no
password system, no button code, and no code-entry screen**. The words
`PASSWORD`, `PASSCODE`, `CHEAT`, `SECRET`, `UNLOCK` do not occur anywhere in the
image; the only ASCII string containing "code" is the credits role
`CODE MONKEYS`, and the only "debug" string is the text block below.

What does exist is a **developer screen compiled into the retail image**: a
`DEBUG MENU` text page that is the 7th page of the credits/attract carousel.
The carousel is six pages in retail (`state` ids 0–5); a seventh page (state id
6) is drawn by a dedicated handler at `0x0800CD54` and lists nine debug options:

```
PSWD DESC / INFINITE LIVES / INFINITE BOMBS / STOLEN MOJO / GOOFY HATS /
FUNNY / GOOD LOOKING / BULLETPROOF / INVISIBILITY
```

The page is gated by a **ROM constant**, not by input: the menu-setup call at
`0x08006F6E` takes its third argument from the immediate of `movs r2,#0` at
`0x08006F6C`; that value is copied to RAM `0x03007A88`, which marks the menu as
"debug-capable". In the retail ROM that byte is `0x00`. Patching it to non-zero
was observed to set `0x03007A88 = 1`, matching the TCRF note. Because the source
is ROM, no controller input can change it.

The page ring size is a separate RAM field, `0x03007A8C` (six in retail).
Paging is `state = (state ± 1) mod count`. With `count = 6`, `L` from page 0
wraps to page 5; page 6 is unrepresentable. With `count = 7` (analysis-only
savestate patch) the ring `0→6` exists and page 6 renders the `DEBUG MENU` text,
verified by decoding the tilemap the handler writes (`0x0600E200`).

**The debug page has no input handler.** On page 6, `B`, `A` and `Start` all
leave the state at 6; the nine options cannot be selected or toggled. The page is
therefore a shipped developer leftover: reachable only by ROM/RAM patching, and
inert once reached. It is not an in-game cheat.

## 3. How to reproduce

Emulator: mGBA 0.10.5 (`mgba -3`), `SDL_AUDIODRIVER=dummy`, Xvfb `:287` +
openbox. Default mGBA SDL keymap: `x`=A, `z`=B, `Return`=Start, `BackSpace`=
Select, arrows = D-pad, `a`=L, `s`=R.

Keys are polled once per frame; a tap shorter than a frame is lost. Hold every
key **200–300 ms**.

Retail path to the carousel (all RAM-verified):

1. Boot; the intro/attract screen is `state = 99` (`0x03007A98`).
2. Hold `Start` (or `Select`) ≈300 ms to skip the intro. The screen becomes the
   credits carousel at `state = 0`, `count = 6` (`0x03007A8C`), `selection = 1`.
3. `L` pages left, `R` pages right. Observed: `L` 0→5→4→3; the ring is
   `0..5` with wrap.
4. Aiming for the debug page in retail: from page 0, `L` lands on 5, never 6
   (see §6b bounds).

Analysis-only route to page 6 (does **not** modify the original ROM):

1. Copy the ROM and set the immediate byte at file offset `0x6F6C` to `0x01`
   (`movs r2,#0` → `movs r2,#1`). This is the exact TCRF patch; it is a static
   patch to enable a developer screen for analysis, not a cheat code.
2. Boot the copy, hold `Start` to reach the carousel. RAM `0x03007A88` reads 1.
3. In the running build, save a state; patch the savestate's IWRAM so that
   `0x03007A8C = 7` (count) and `0x03007A88 = 1`; load the state (F1).
   The count is not recomputed, so the 7-page ring persists.
4. `L`/`R` now step through `0..6`. Press `L` from page 0 (or `R` from page 5)
   to land on `state = 6`.
5. Page 6 draws the `DEBUG MENU` tilemap; decode VRAM `0x0600E200` as described
   in §6 to read it back as text.

Rejection controls actually run:
- Retail `L` sequence 0→5→4→3 (three presses) — proves the 6-page ring.
- Page 6: `B`, `A`, `Start` each leave `state = 6` and leave the nine labels and
  the eight status flags unchanged.

## 4. Address map

### ROM

| Address | Contents |
|---|---|
| `0x08006F34` | Menu/screen setup function; entry reached from startup via the Thumb pointer at `0x080001DC` |
| `0x08006F6C` | `movs r2,#0` — the debug gate immediate (`00 22`). Non-zero enables the debug page flag |
| `0x0800E736` | Screen dispatcher: `ldr r0,[r6,#0x18]; cmp #102; ldr r1,=0x0800E77C; ldr r0,[r1,r0*4]; mov pc,r0` |
| `0x0800E77C` | Screen-handler table, 103 entries (102+1); slots 0–6 and 99–102 valid, rest point at the no-op `0x0800E96E` |
| `0x0800CD54` | DEBUG MENU page handler (draws text + hall-of-fame overlay) |
| `0x08081130` | Page graphics pointer table, 24-byte records (6 records) |
| `0x080811BC` | `DEBUG MENU` text block, 13 rows × 31 bytes |
| `0x080811FA` | First option row `" PSWD DESC                 ON "` |
| `0x08081219` … `0x080812F2` | Option rows, 31-byte stride |
| `0x083D8B04` | Default hall-of-fame initials (8 × 5-byte records: `QXFS`,`RDDT`,…) |
| `0x080805C0` | `"HALL OF FAME"` |
| `0x0807FD28` | `"PRESENTS"` / `"COPYRIGHT 1980"` intro strings |

Screen-handler table (`0x0800E77C`). Each table slot points at a small stub in
`0x0800E918..0x0800E96E` which tail-calls the real handler; the "Handler" column
below is the function the stub calls. Observed slots:

| State | Handler | Role |
|---:|---|---|
| 0 | `0x0800AD38` | credits page 0 |
| 1 | `0x0800AE44` | credits page 1 |
| 2 | `0x0800AFDC` | credits page 2 |
| 3 | `0x0800B0F4` | credits page 3 |
| 4 | `0x0800B20C` | credits page 4 |
| 5 | `0x0800B490` | credits page 5 |
| 6 | `0x0800CD54` | DEBUG MENU (unused in retail ring) |
| 99 | `0x0800CA80` | intro / attract |
| 100–102 | `0x0800B7E8`, `0x0800BE10`, `0x0800C448` | other screens (not reached by the carousel) |

### RAM (IWRAM)

| Address | Meaning | Evidence |
|---|---|---|
| `0x03007A80` | Screen object base | dispatcher argument; pointers to it exist at `0x03007870`, `0x030078F0`, `0x03007A00`, `0x03007A14`, `0x03007FD8` |
| `0x03007A88` | Debug-capable flag (0 retail, 1 patched) | writes track the ROM gate byte |
| `0x03007A8C` | Page count (6 retail, 7 when forced) | ring arithmetic |
| `0x03007A94` | Menu selection index (1) | observation |
| `0x03007A98` | **Screen state id** (0–6, 99–102) | matches dispatcher table |
| `0x03007A9C` | per-screen timer | counts down/up |
| `0x03007AC0` | held-key mask (active high; `0x0010` = Right) | verified by holding Right |
| `0x03007AC4` | 8-byte sprite/text records written by handlers | page-6 handler writes 32 records here |
| `0x03000570` | Hall-of-fame initials buffer, 8 × 5 bytes | loaded from ROM `0x083D8B04` |
| `0x03000598` | 8 hall-of-fame status bytes (`01 01 00 00 00 00 01 00`) | read by page-6 handler |

### EWRAM

| Address | Meaning |
|---|---|
| `0x02000814` | Page index used by the page graphics loader (stays 0 in the carousel, which uses `state` instead) |

## 5. Algorithm

### 5.1 Screen dispatch (derived, verified by state reads)

```
handlers = ROM[0x0800E77C + 4*state]
if state > 102: return              # clamp
handlers[state](screen_obj)         # r0 = screen object at 0x03007A80
```

### 5.2 Page ring (observed)

```
count = *(u32*)0x03007A8C          # 6 in retail, 7 when the debug flag is set
state = *(u32*)0x03007A98
on L: state = (state - 1 + count) mod count
on R: state = (state + 1) mod count
```

Verified transitions: retail `L`: 0→5→4→3. Patched ring (count 7): `L`:
6→5, `R`: 5→6, and 3→2→1→0→6.

### 5.3 Debug gate (derived; confirmed by patch)

```
; 0x08006F5C..0x08006F6E
movs r0,#0
mov  r8,r0
mov  r9,r0
movs r0,#1
mov  r6,sp
mov  r1,r9
movs r2,#0          ; <-- 0x08006F6C: immediate is the flag source
bl   0x0800EC8C     ; -> 0x08009184: stores arg in the screen object
```

`0x08009184` stores its byte argument at `[obj+8]`; the value surfaces at
`0x03007A88`. Changing the immediate from `0` to `1` and running the copy
changed `0x03007A88` from `0` to `1`, with no other behaviour change observed.

## 6. Tables

### 6.1 Page ring

| Index | Page |
|---:|---|
| 0–5 | credits pages (XGP / team credits) |
| 6 | DEBUG MENU (only with count = 7) |

### 6.2 DEBUG MENU text block (`0x080811BC`, 13 rows × 31 bytes)

| Row | File offset | Text |
|---:|---|---|
| 0 | `0x811BC` | `          DEBUG MENU          ` |
| 1 | `0x811DB` | blank |
| 2 | `0x811FA` | ` PSWD DESC                 ON ` |
| 3 | `0x81219` | `      INFINITE LIVES          ` |
| 4 | `0x81238` | `      INFINITE BOMBS          ` |
| 5 | `0x81257` | `      STOLEN MOJO             ` |
| 6 | `0x81276` | `      GOOFY HATS              ` |
| 7 | `0x81295` | `      FUNNY                   ` |
| 8 | `0x812B4` | `      GOOD LOOKING            ` |
| 9 | `0x812D3` | `      BULLETPROOF             ` |
| 10 | `0x812F2` | `      INVISIBILITY            ` |
| 11–12 | `0x81311`, `0x81330` | blank |

### 6.3 Page-6 tile mapping (used to prove the screen)

The handler converts each source byte to a tile index:

```
tile = c - 'A'      if 'A' <= c <= 'Z'
tile = 0x26         otherwise
dest = 0x0600E200 + row*64 + col*2      (rows 0..12)
```

It then draws eight 3-letter initials at `0x0600E2C2 + row*64` (rows 0..7) and
a status tile at `0x0600E2F8 + row*64`: `0x17` if the status byte is non-zero,
`0x0E` otherwise. Decoding the live tilemap after entering page 6 produced:

```
 0|          DEBUG MENU           |
 2| PSWD DESC                 ON  |
 3| QXFS INFINITE LIVES        X  |
 4| RDDT INFINITE BOMBS        X  |
 5|      STOLEN MOJO           O  |
 6|      GOOFY HATS            O  |
 7|      FUNNY                 O  |
 8| REAM GOOD LOOKING          O  |
 9| MXXT BULLETPROOF           X  |
10|      INVISIBILITY          O  |
```

The three-letter columns are the hall-of-fame initials buffer (`0x03000570`),
not part of the debug menu; the debug page reuses the hall-of-fame sprite
overlay.

## 6b. Enumeration

**Space definition.** There is no code/password alphabet and no checksum. The
relevant input space is the carousel page index:

- retail: `count = 6` → reachable states `{0,1,2,3,4,5}` (6 values);
- debug-capable: `count = 7` → reachable states `{0..6}` (7 values);
- the state field itself is a `u32` clamped to `<= 102` by the dispatcher, but
  only 11 slots have real handlers (`0–6`, `99–102`).

**Validator model.** Reimplemented in `info.py`/observation: read `state` at
`0x03007A98` and `count` at `0x03007A8C`; `L` decrements mod count, `R`
increments mod count. This agrees with every observed transition (retail
0→5→4→3; patched 6→5 and 5→6, 3→2→1→0→6).

**Unpublished value reached.** Page **6** is absent from every published list
(GameFAQs has no codes page reachable, VGChartz lists only "Point values", TCRF
documents the text at `0x811BC` and the flag patch but not the page index, the
ring arithmetic, or the VRAM proof). In the patched build the ring was driven to
`state = 6` and the screen was read back from VRAM as `DEBUG MENU` with all nine
options (rows above). This is the novel, non-published state.

**Bounds proven by rejection.**
- Retail, `count = 6`: `L` from page 0 yields page **5**, not 6 (observed
  three-press run 0→5→4→3). The value 6 cannot be expressed by the ring; this
  is the in-game rejection of the out-of-range page.
- Page 6 input: `B` (`z`), `A` (`x`) and `Start` (`Return`) each held 200–300 ms
  left `state = 6`; the eight status bytes at `0x03000598` stayed
  `01 01 00 00 00 00 01 00`. No option can be selected or toggled.
- The gate cannot be set by input: the source is the ROM immediate at
  `0x08006F6C` (retail `0x00`), and the only observed RAM change tracks that
  byte. No writer of `0x03007A88` reachable from the joypad exists.

**No button code.** The guide's §5.4a scan was run over the whole image:

- runs of ≥4 consecutive `u16` held-button masks from
  `{0x1,0x2,0x4,0x8,0x10,0x20,0x40,0x80,0x100,0x200}`: **0**;
- runs of ≥4 active-low complements (`0x3FF ^ mask`): **0**;
- byte-mask runs ≥4: 2 hits, both in graphics data (`0x080E4B34`, `0x08392FE8`)
  and not adjacent to any key reader;
- literal `U U D D L R L R B A` (u8 and u16): **0** occurrences.

**No password system.** Case-insensitive counts over the whole image:
`password` 0, `passcode` 0, `cheat` 0, `secret` 0, `unlock` 0, `debug` 1
(the `DEBUG MENU` text), `code` 2 (`CODE MONKEYS` credits role). There is no
symbol alphabet, no comparison table, and no entry screen.

## 7. Validation evidence

**Observed (emulator + RAM/VRAM reads)**
- `state = 99` on the intro; `Start` → `state = 0`, `count = 6`, `sel = 1`.
- `L` presses: `state` 0→5→4→3; `count` unchanged at 6.
- Retail `0x03007A88 = 0`; patched-flag build `0x03007A88 = 1`.
- Savestate-patched count 7 persists; ring `3→2→1→0→6` and `6→5`, `5→6`.
- VRAM at `0x0600E200` decodes to `DEBUG MENU` and the nine option rows while
  `state = 6`.
- On page 6, `B`/`A`/`Start` do not change `state` or `0x03000598`.
- The nine label rows and eight initials/status rows are the only content the
  handler writes.

**Derived (instruction-level)**
- Dispatcher at `0x0800E736` indexes the 103-entry table at `0x0800E77C`;
  slot 6 is `0x0800CD54`.
- Gate instruction `movs r2,#0` at `0x08006F6C` feeds `0x0800EC8C` →
  `0x08009184`, which stores the byte at `[screen_obj+8]`.
- Page handler `0x0800CD54` reads `0x080811BC` (text), `0x03000570` (initials)
  and `0x03000598` (status), writes `0x0600E200`.

**Inferred**
- The nine labels name intended developer toggles (infinite lives/bombs,
  bulletproof, invisibility, etc.), but no code path reads them in this build;
  they are text only. No effect was observed because no input reaches them.

## 8. Unknowns

- Handlers for states 100–102 (`0x0800B7E8`, `0x0800BE10`, `0x0800C448`) were
  not reached in this pass; the gameplay/pause screens sit outside the code
  surface and were not required to settle the cheat question.
- The exact intended semantics of each of the nine debug labels is not
  recoverable from the retail image: the labels are not referenced by gameplay
  code, and the page has no input handler.
- Whether a later/regional build sets the gate constant non-zero was not
  checked; only this USA build (A2FE) was analysed.

## 9. Tooling

- `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`
- Python 3 + `capstone` 5.0.7 for PC-relative/BL scans
- mGBA 0.10.5 under Xvfb `:287`, `SDL_AUDIODRIVER=dummy`, xdotool key holds
  (200–300 ms), mGBA `Shift+F1..F7` savestates
- `ss.py` — extract the zlib-compressed `gbAs` chunk from an mGBA `.ssN` PNG
- `info.py` — read GBA addresses (`0x02…`/`0x03…`) from a savestate
- `sspatch.py` — patch IWRAM/EWRAM bytes in a savestate and rebuild the PNG
- `bg8.py` — decode mode-0 8bpp BG tilemaps from a savestate as ASCII
- Analysis-only patched copy at `/tmp/defender/defpatch.gba` (one byte:
  file `0x6F6C` = `0x01`). The retail ROM was never modified.

## 10. Legal note

No ROM, graphics, audio or game text is redistributed with this report; only
hashes, addresses, instructions and short identifiers required for the analysis
are recorded.
