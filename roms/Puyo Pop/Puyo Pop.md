# Puyo Pop (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `/mnt/gbacheats/roms/Puyo Pop/Puyo Pop.gba` |
| Size | 8,388,608 bytes (0x800000, 8 MiB) |
| Header title | `PUYO POP` |
| Game code | `APYE` |
| Maker code | `78` (THQ) |
| Version | 0x00 |
| Fixed byte | 0x96 (valid) |
| Entry word | `0xEA00002E` — **stock** (no cracktro/trainer patch) |
| Header checksum | `0x0000` (normal unused field); complement byte `0x57` |
| MD5 | `3ee8e61dfe10bbfc15f51fd52eef8e14` |
| SHA-1 | `338702ea961b17c46a1deb960f5d0df19d7912f9` |
| SHA-256 | `dedbf64eebeac72a2a536e367bd9e4a2eac5a771594a2aaa248c6d8596549850` |
| Identity | International release of Sega/Sonic Team/Caret House *Puyo Pop* (JP: *Minna de Puyo Puyo*), US release 2002-02-11. **Not** *Puyo Pop Fever*. |

Embedded-header scan (156-byte Nintendo logo, §2) found **two** headers:
* file `0x000000` / ROM `0x08000000` — the playable international game above.
* file `0x5689AC` / ROM `0x085689AC` — title `PUYO POP`, code `APYE`, maker `8P`, entry `0xEA000011`; surrounded by a multiboot-style request block (values `0x10/0x20/0x40...` at `0x568980`). This is an embedded multiboot/link sub-image, not a second game, trainer, or patch. All addresses in this report refer to the first image.

## 2. Executive summary

**There is no password system, no on-screen code-entry field, and no button-code system in this ROM.** This is a **negative result about a bounded, enumerated search space**, not an "I did not look hard enough" result:

* The main state machine has **39 dispatch states** (`0x00`–`0x26`, table at `0x08020660`); every reachable menu/gameplay screen was walked on mGBA with screenshots and live RAM reads. There is no password screen and no debug menu among them.
* `strings -t x -n 4` yields 79,706 items but **zero readable English words** — all text is pre-rendered into VRAM glyph tiles (the font/text bank is a bitmap-rendered tile atlas, not an ASCII or tile-index string bank). Menu labels were decoded from live frames/screenshots (`SELECT MODE`, `SINGLE/DOUBLE/EVERYBODY/ENDLESS PUYO POP`, `OPTIONS`, `DIFFICULTY`, `MESSAGE SPEED`, `ROUNDS`, `RANKING`, `GALLERY`, `LANGUAGE`, `RETURN TO DEFAULT`, `RETURN`, `ENDLESS PUYO POP / TOKOTON / NORMAL MODE / TASK MODE`, `NAME ENTRY`, gameplay HUD `LEVEL/PUYO/MAX CHAINS`). Literal searches for `password|cheat|code|debug|secret|unlock|level` found no code-related strings; the only real ASCII is the header.
* 8 published/common button sequences × 2 encodings (u16/u8) × 2 orders = **32 raw mask searches** found no plausible code table. Three codes were also entered live (see §7) and rejected.
* TCRF's GBA *Puyo Pop* page documents only unused sounds and regional differences — **no debug menu or cheat**.

What the game *does* have is a **save-flag unlockable system** (in scope, §0.2 "unlockables"): six areas gated by sign items, two hidden characters, and a hidden Sound Test behind Gallery card 18. These are stored in the 512-byte SRAM and deserialized into named RAM variables. The published "Unlock All Levels: `03000268 000000FF`" Gameshark code was verified to target the genuine area-unlock bitmask (`0x03000268`), but as a memory-edit code it is **out of scope** for reporting as a usable cheat; the in-game unlock routes are documented below.

## 3. How to reproduce

Emulator: `SDL_AUDIODRIVER=dummy mgba -3 "Puyo Pop.gba"` on `DISPLAY=:315`.
Keymap (mGBA SDL defaults): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows. Hold keys 90–200 ms.

Menu path (all screens observed):
1. Language select (`ENGLISH` / `日本語`) → pick ENGLISH → "Now saving" → SEGA splash → "CREATED BY SONIC TEAM" splash → title (`PRESS START`).
2. Start → `SELECT MODE`: SINGLE / DOUBLE / EVERYBODY / ENDLESS PUYO POP / OPTIONS.
3. OPTIONS: DIFFICULTY=NORMAL, MESSAGE SPEED=NORMAL, ROUNDS=2, RANKING=HAJIMARI FOREST, GALLERY=1, LANGUAGE=ENGLISH, RETURN TO DEFAULT, RETURN.
4. GALLERY shows card `01 ARLE NADJA`; the card selector is capped at the unlocked count (fresh save = 1); RIGHT/LEFT/DOWN all stay on card 01.
5. ENDLESS PUYO POP → `TOKOTON / NORMAL MODE` and `TASK MODE` selectors → gameplay (HUD `LEVEL 5 / PUYO 0 / MAX CHAINS 0`), then `NAME ENTRY` high-score screen (names `A / PAMOT / SPODE / BAROM / MUMMY`).
6. Pause/game-over transitions were exercised; no hidden menu appeared.

RAM access: mGBA `-d` CLI debugger via a FIFO held open by a small TCP server (`dbgserver.py`), with a Thumb breakpoint at the per-frame dispatch `0x08020612` so RAM could be read deterministically each frame. `r/2 0x03004D90` = scene state; `x/N` dumps; `w/4` writes for cause-effect tests.

Published codes tested live (all **rejected**, no visual/RAM change):
* `UP, DOWN, SELECT, A` at title screen and at Endless mode select (character-select code from *Puyo Pop Fever*) — no effect.
* Hold `SELECT` + `UP, DOWN, LEFT, RIGHT` in Gallery (Fever "unlock all characters/cutscenes") — no effect.
* `L + R + SELECT` during a match (Fever "KO all CPUs") — no effect; score/level unchanged.

## 4. Address map

| Address | Kind | Meaning / evidence |
|---|---|---|
| `0x08000000` | ROM | Entry ARM branch `0xEA00002E`; stock crt0 |
| `0x08000108` | ROM (ARM) | IRQ handler (VBlank dispatch) |
| `0x080205A0` | ROM (Thumb) | `main()` (called via crt0 literal `0x080205A1`) |
| `0x08020612` | ROM (Thumb) | Per-frame state dispatch: `ldrh r0,[0x03004D90]`, `cmp r0,#0x26`, jump through table |
| `0x08020660` | ROM | 39-entry u32 jump table for states `0x00`–`0x26` |
| `0x03004D90` | IWRAM u16 | Current scene state (observed `0x06` splash, `0x08` menus, `0x1B/0x1C` title/attract) |
| `0x03004DBE` | IWRAM u16 | Menu cursor (observed `0x04`→`0x05` when moving GALLERY→LANGUAGE) |
| `0x0E000000` | SRAM, 512 B | Save image. Bytes are stored as 16-bit words with swapped bytes relative to RAM |
| `0x03003CB4` | IWRAM | SRAM work buffer (byte-swapped copy; `buffer[0:8] = 50 55 59 4f 4d 31 00 01` = SRAM[0:8] reversed) |
| `0x0801F1AC` | ROM (Thumb) | Save deserializer: DMA-copies 13 chunks from `0x03003CC0` into named RAM variables |
| `0x08020010` | ROM (Thumb) | DMA copy helper (`src=r0, dst=r1, bytes=r2`) |
| `0x03000256` | IWRAM u16 | Save field at SRAM `0x1B6` (value `0x0001`) |
| `0x0300025C` | IWRAM u32 | Save field at SRAM `0x1B8` (value `0x00017EFF`) |
| **`0x03000268`** | IWRAM u32 | **Unlocked-areas bitmask**, from SRAM `0x1BC` (big-endian u16); fresh save = `1` (Hajimari Forest only). Written `1` at boot by `0x08015A8`; written again by deserializer `0x0801F226`. Confirmed by live watchpoint and by the published Gameshark address |
| `0x03000508` | IWRAM u32 | Save field at SRAM `0x1C0` (0) |
| `0x03000520` | IWRAM, 24 B | Save field at SRAM `0x1C4` (first byte `01`) — candidate gallery/character flag array |
| `0x03004D9C` | IWRAM u32 | Save field at SRAM `0x1DC` (1) |
| `0x085689AC` | ROM | Embedded multiboot header (see §1) |

### Save deserializer chunk map (`0x0801F1AC`)

Source = `0x03003CB4 + 0x0C` (i.e. SRAM byte offset `0x0C` onward). Each DMA chunk's source offset and destination:

| # | Source offset (from `0x03003CC0`) | SRAM offset | Size | Destination | Observed value |
|---|---:|---:|---:|---|---|
| 1 | 0x000 | 0x0C | 0xA0 | `0x03000364` | — |
| 2 | 0x0A0 | 0xAC | 0x28 | `0x03000404` | — |
| 3 | 0x0C8 | 0xD4 | 0xC8 | `0x0300042C` | — |
| 4 | 0x190 | 0x19C | 6 | `0x030004F4` | — |
| 5 | 0x196 | 0x1A2 | 0xC | `0x0300034C` | — |
| 6 | 0x1A2 | 0x1AE | 4 | `0x03000358` | — |
| 7 | 0x1A6 | 0x1B2 | 4 | `0x0300035C` | — |
| 8 | 0x1AA | 0x1B6 | 2 | `0x03000256` | 0x0001 |
| 9 | 0x1AC | 0x1B8 | 4 | `0x0300025C` | 0x00017EFF |
| 10 | 0x1B0 | 0x1BC | 4 | `0x03000268` | 0x00000001 |
| 11 | 0x1B4 | 0x1C0 | 4 | `0x03000508` | 0 |
| 12 | 0x1B8 | 0x1C4 | 0x18 | `0x03000520` | `01 00 ...` |
| 13 | 0x1D0 | 0x1DC | 4 | `0x03004D9C` | 1 |

Total serialized = 468 bytes of the 512-byte SRAM image.

## 5. Algorithm (save-flag unlockables)

```
boot:
  copy SRAM[0x000..0x1FF] -> IWRAM 0x03003CB4, swapping each 16-bit word's bytes
  init: [0x03000268] = 1                         # 0x08015A8
  if valid_save(0x03003CB4):                      # 0x0801F2E0
      deserialize(0x03003CC0)                    # 0x0801F1AC, DMA chunks in §4
  ...
unlocked_areas = [0x03000268]                     # bit i = area i reachable
```

Published in-game unlock routes (GameFAQs, verified against the game's structure):
* WELCOME SIGN → Hajimari Forest (start).
* Beat Seriri in Hajimari Forest → MERCHANT SIGN → Goldtown.
* Beat Nohoho in Goldtown → WARRIOR SIGN → Gachinko Dungeon.
* Beat Draco Centaur in Gachinko Dungeon → CONJURER SIGN → Magical Tower.
* Beat Witch in Magical Tower → MONARCH SIGN → G. Dark Prince Castle.
* Beat Satan-sama twice → DUBIOUS BOOK → FLAME EXPANDER → NOHOHO RUCKSACK → SCALE PENDANT → beat Seriri with the pendant → GODDESS SIGN → Trial Labyrinth (6th area).
* Beat Kaakun in Trial Labyrinth → Curry Calling Bell → play as **Carbunkle**.
* Beat Satan in G. Dark Prince Castle → Dark Prince Mask → play as **Satan-Sama**.
* Beat Kaakun twice in Trial Labyrinth → **CARD 18**; select card 18 in Gallery → hidden **Sound Test** (press A for sound effects).

There is **no password encoder/decoder and no validator** in this ROM: no alphabet table, no key/permutation table, no checksum routine, no comparison against a typed buffer. The `NAME ENTRY` screen is a high-score label field (§16.2b): its buffer feeds the score table shown at `NAME ENTRY`, not a validator.

## 6. Tables

**Game states (39)** — jump table `0x08020660`, indices `0x00`–`0x26`:

| idx | handler | idx | handler | idx | handler |
|---:|---|---:|---|---:|---|
|0|0x080206FC|13|0x08020C48|26|0x08020D98|
|1|0x08020798|14|0x08020DD8|27|0x08020760|
|2|0x080207C0|15|0x08020E3C|28|0x08020768|
|3|0x080207DC|16|0x08020E4A|29|0x08020786|
|4|0x08020800|17|0x08020E7C|30|0x08020774|
|5|0x0802080C|18|0x08020E9C|31|0x0802077A|
|6|0x08020824|19|0x08020F0C|32|0x08020786|
|7|0x0802084C|20|0x08020908|33|0x08020CD8|
|8|0x0802087C|21|0x08020924|34|0x08020CE4|
|9|0x08020978|22|0x0802093C|35|0x08020CF0|
|10|0x08020A40|23|0x08020958|36|0x08020EAA|
|11|0x08020AC4|24|0x08020D1C|37|0x08020ED8|
|12|0x08020BF4|25|0x08020D84|38|0x08020F0C|

Observed states: `0x06` (SEGA/Sonic Team splash + title), `0x08` (all menu screens), `0x1B`, `0x1C` (title/attract), plus gameplay/name-entry states reached from `0x08` handlers. No state renders a password entry or debug list.

**Unlockable inventory** (developer-intended, all gated by play, none by a typed code):

| Item | Gate | Save evidence |
|---|---|---|
| 6 areas (Hajimari Forest … Trial Labyrinth) | Sign items / boss wins | bitmask SRAM `0x1BC` → `0x03000268` |
| Carbunkle (playable) | Curry Calling Bell from Kaakun | flag array `0x03000520` / `0x0300025C` region (exact bit unresolved) |
| Satan-Sama (playable) | Dark Prince Mask from Satan | same region |
| Gallery cards 1..18+ | boss wins / item collection | Gallery count in Options; card 01 shown on fresh save |
| Sound Test | Gallery card 18 (Kaakun ×2) | hidden screen reachable only via card 18 |

**Published code verification:**

| Source | Claim | Verification |
|---|---|---|
| GameFAQs (gba/551521) | 4 cheats/secrets, all gameplay unlocks | Consistent with ROM/save structure; no typed code listed |
| TCRF | No debug menu; only unused sounds + regional differences | Confirmed (archived page) |
| GameFAQs/VGChartz *Puyo Pop Fever* | `UP DOWN SELECT A` character select; hold SELECT+UDLR unlock; L+R+SELECT CPU KO | **Wrong SKU** (different game). Tested in this ROM: all three rejected |
| CodeJunkies / almarsguides Gameshark | "Unlock All Levels `03000268 000000FF`" | Address is genuine (`0x0801F27C` literal; live watchpoint confirms). Memory-edit code — out of scope; documented only as proof of the address |

## 6b. Enumeration

**Code space: empty (0 passwords, 0 button codes, 0 hidden debug screens).** Bounds proven by these counts:

| Search space | Size checked | Result |
|---|---:|---|
| `strings -t x -n 4` whole ROM | 79,706 items | 0 readable words; only header `PUYO POP`/`APYE78` |
| Case-insensitive + `+0x20` letter-shift searches | whole 8 MiB | 0 code/password strings |
| Literal keywords `password/cheat/code/debug/secret/unlock/level/menu/test/option` | whole 8 MiB | 0 code-related hits (only binary noise) |
| Linear char→tile maps (K = −0x60…+0x5F) × 7 known labels | whole 8 MiB | 0 hits |
| XOR with all 256 constants × 6 known labels | whole 8 MiB | 0 hits |
| Button-mask sequences: 8 published/common combos × {u16,u8} × {forward,reversed} | 32 full-ROM searches | 0 plausible code tables (3 coincidental u16 hits in compressed data) |
| Main dispatch states | 39 (0x00–0x26) | no password/debug screen |
| Live button codes | 3 published (Fever) | 0 accepted |
| Reachable menus/screens | 11 distinct (§3) | no code-entry field |

**Save-flag space characterised (the actual unlock system):** 468 serialized bytes; the area bitmask `0x03000268` is 8 bits wide with values `1` (fresh save) through `0x3F` (six documented areas) meaningful; `0xFF` is reachable by a memory edit but is not an in-game code. Fresh-save counts: GALLERY=1, RANKING=HAJIMARI FOREST, areas=1. These numbers bound the negative: no hidden code path exists in the searched spaces, and the only unlock state is save-flag based.

**Novel state demonstration (analysis only, not a reported cheat):** a debugger write of `0x3F` / `0xFF` to `0x03000268` is accepted without checksum rejection (`r/4` reads back the new value; watchpoint at `0x080115BC`/`0x0801F226` confirms the only writers). This proves the bitmask has no validation beyond the save descriptor and that `0x03000268` is the genuine "all levels" flag targeted by the published memory-edit code. It is explicitly **not** an in-game code or a recommended unlock method.

## 7. Validation evidence

* **Observed (screenshots):** language select, "Now saving", both splashes, title, `SELECT MODE`, `OPTIONS`, `GALLERY` card 01 and its cap, `ENDLESS PUYO POP` mode select, gameplay HUD, `NAME ENTRY`. Files: `shot00`–`shot07`, `menu_*`, `options*`, `gallery*`, `gal_*`, `w_*`, `t_*`, `code_*`, `unlock_all_areas.png` in `/tmp/opencode/puyopop/`.
* **Observed (RAM):** `0x03004D90` = `0x06`/`0x08`/`0x1B`/`0x1C` at the corresponding screens; `0x03004DBE` changed `0x04→0x05` on a GALLERY→LANGUAGE cursor move; SRAM `0x0E000000` reads match the `.sav` file; `0x03000268` = `1` on a fresh save and `0xFF` after a debugger write; watchpoints identified both writers of `0x03000268`.
* **Derived (disassembly):** 39-state dispatcher; `main()` at `0x080205A0`; save deserializer at `0x0801F1AC` and its 13-chunk table; init write of `1` at `0x08015A8`; DMA helper at `0x08020010`.
* **Inferred (labeling):** exact bit positions for the Carbunkle/Satan-Sama/Gallery-card flags inside `0x03000520`/`0x0300025C` were not isolated; the *in-game* unlock routes are published and structurally plausible but were not played to completion.
* **Rejected-input evidence:** three published button codes produced no screen change and no relevant RAM change; `GALLERY` remained capped at card 01; `0x03000268` remained `1` throughout normal play.

## 8. Unknowns

* Exact bit layout of `0x03000520` (24-byte array) and `0x0300025C` for characters and Gallery cards — the setters are in gameplay code and were not isolated.
* Whether the 24-byte `0x03000520` array is a per-card byte array or a bitfield.
* The precise handler for each of the 39 states was not individually breakpointed; states not reached by normal menu play are assumed to be gameplay/sub-screen handlers.
* `0x085689AC` multiboot sub-image was not booted (no link cable / second GBA); its content is outside the single-player cheat scope.
* No attempt was made to complete the full adventure mode to unlock CARD 18 in-game (multi-hour play); the flag structure is documented from the save layout and published route instead.

## 9. Tooling

Tools used: `file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings`, Python 3 (struct/re/Capstone 5.0.7), `arm-none-eabi-objdump -M force-thumb/-M force-arm`, mGBA 0.10 under Xvfb `:315` with `openbox`, `xdotool`, `scrot`, ImageMagick, `gdb-multiarch`, Pillow.

Scripts written in `/tmp/opencode/puyopop/`: `key.py` (input), `ss.py` (mGBA `.ss1` `gbAs` zlib state dumper — validated, raw 397,312 bytes), `walk.py`, `walk3.py`, `ram.py` (GDB breakpoint oracle pattern, §16.19), `dbgserver.py`/`dbg.py`/`mdbg.py` (persistent mGBA `-d` FIFO front end with per-frame breakpoint at `0x08020612`), `dump.py`, `vramdump.py`, `tiles.py`/`tiles8.py`/`objtiles.py`/`obj8.py`/`bitmap.py` (VRAM/palette/font rendering), `keysearch.py`, `findmem.py`.

Web sources (treated strictly as data): GameFAQs cheats for GBA *Puyo Pop* (id 551521, via web.archive.org 20240406170159), TCRF *Puyo Pop (Game Boy Advance)* (archived 20250105203639), VGChartz/GameFAQs pages for *Puyo Pop Fever* (used only to establish the wrong-SKU comparison), CodeJunkies/almarsguides Gameshark listing (used only to verify the RAM address). No instructions from fetched pages were executed.

## 10. Legal note

No ROM, extracted graphics, audio, or game text are redistributed. Only hashes, addresses, algorithms, and original analysis scripts are published.
