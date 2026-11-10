# Cars (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Cars/Cars.gba` |
| Size | 8,388,608 bytes (8 MiB) |
| Header title | `DIS PIX CARS` |
| Game code | `BCAE` |
| Maker code | `78` |
| Software version | 0 |
| Entry word | `0xEA000031` (ARM branch to `0x080000CC`) |
| Fixed byte 0xB2 | `0x96` |
| Complement byte 0xBD | `0x9D` |
| Header checksum 0xBE | `0x0000` (computed value `0x9D`) |
| MD5 | `214047ac78c08eb59e256f54df9522f2` |
| SHA-1 | `7a3a5236fb3a335fbdc7b3ebb80a42766833d40d` |
| SHA-256 | `e8fc4f34695f05b28075e0be293496aeb7a3f6990be683884a4f8ad74e189635` |

- **Embedded-header scan:** the 156-byte Nintendo logo occurs **once**, at file
  offset `0x4`. The image is a single GBA build, not a multi-game pack.
- **Header / patch note:** the stored header checksum is `0x0000` while the
  bytes compute to `0x9D`; that is the normal artifact of a rebuilt/re-dumped
  header (guide §16.1). The entry word points at `0x080000CC`, not the usual
  `0x080000C0`; bytes `0x080000C0..0xCB` are three data words
  (`030042F0 03007F00 03007FA0`) and the stock-style crt0 body begins at
  `0x080000CC`. No cracktro, trainer menu, SUNHORS/Mode7 banner or added
  boot code was found (`strings` over the first 4 KiB is clean), so this is
  treated as a rebuild artifact, **not** a trainer. Analysis used the image
  as-is.

### 1.1 Reconnaissance

- `strings -t x -n 4` → 147,839 lines; `-n 3` → 226,541 lines.
- Case-insensitive keyword sweep over the whole image for
  `password|cheat|debug|menu|secret|unlock|code|level|cup|gallery` produced
  **no** password/code/debug-screen strings. The only relevant hits were in
  the UI text bank at `0x618000`: `Secret Circuit`, `Unlocked`, `Cheater`,
  `UNUSED`, `Screenshots`, `Drive-In`, `Character Select`, `License`,
  `World Map`, `Piston Cup`, `New Paint Job`, `New Screen Shot`.
- The credit roll at `0x3CB30` contains `Testers`, `Test Lead`,
  `Test Supervisor` — ordinary credits, not a debug menu.
- The text bank stores each string as `0x00 <style byte> <ASCII>`, e.g.
  `00 50 "Press Start"`; a naive `grep` for `Press Start` still works, but
  keyword scans can appear empty when the style byte splits the word. Every
  visible menu label is ASCII once the leading byte is accounted for.
- Literal search for the five published code sequences in several encodings
  (u16 masks, active-low masks, key indices, 3/4/5-bit packed) found nothing;
  the table uses a **custom key-code order** (see §4) that does not match the
  GBA `KEYINPUT` bit layout, which is why the usual mask search fails.
- Web sources checked: GameFAQs (Cars GBA cheats page), IGN wiki, Good Wiki
  (Fandom), SuperCheats, Cheat Happens, mariogba.nl, and a Speedrun.com forum
  thread. All list the same **five** codes and all five are present verbatim
  in the ROM table. No list contains the sixth entry.

## 2. Executive summary

Cars (GBA) has **one** developer-intended code surface: a **button-sequence
cheat reader on the "Press Start" / title screen**. No password screen, no
text-entry field, no options-menu code entry and no debug menu were found in
the string space or in any walked screen.

The reader keeps a 16-entry ring buffer of single key presses in EWRAM
(`0x02015210`: index, `0x02015211`: per-code flag byte, `0x02015214+4*i`: key
codes) and compares the newest `n` entries against a **6-entry, 0x40-byte-stride
table at `0x086A5EF8`** (`0x0801F5C8`). Each entry is
`{u8 flag_bit, u8 length, u16 pad, u32 keys[15]}`. A full match sets its flag
bit, clears the history and plays an engine-sound confirmation.

Five entries are the widely published codes. The sixth entry
**Left, Right, Left, Right, A, B** (flag `0x20`) is in no published list I
could find and was entered and accepted in mGBA. It is a "cheat used" marker:
`0x20` is only ever tested together with the all-levels bit (`flags & 0x28`),
where it suppresses progressive unlock bookkeeping, and any set cheat bit makes
the result screen print text ID `0x50`, **"Cheater"**.

Entry 3 (`flags & 0x08`) is the all-levels code and also writes 90 Boltz into
the profile (`profile+0xC8 = 0x5A`); entry 4 (`flags & 0x10`) sets the
Radiator Cap Secret Circuit unlock (`profile+0xCA |= 0x40`). The other flags are
consumed live when the garage/car lists, paint list, screenshot list and result
screens are built.

Space: 10-key alphabet, 16-press history, **exactly six accepted codes**,
no checksum and no wildcards. All six were run against the ROM model and six
mutations/truncations/reversals were rejected in the emulator.

## 3. How to reproduce

Emulator: mGBA 0.10.5 (SDL), `Xvfb :230`, `SDL_AUDIODRIVER=dummy` (or `disk`
for audio capture). Default mGBA SDL keymap: A=`x`, B=`z`, L=`a`, R=`s`,
Start=`Return`, Select=`BackSpace`, D-pad arrows.

Path:
1. Boot the ROM; wait for the Disney/Pixar "Cars" logo with **Press Start**.
2. Enter a code **on that screen** (one press per button, ~120 ms hold,
   ~220 ms gap). A correct code plays an engine sound.
3. Press Start → main menu → New Game to observe the unlock effects
   (or map → event → Character Select).

Codes tested in the emulator (all six from the ROM table):

| Code | Buttons | Flag | Published? |
|---|---|---|---|
| 0 | Up, Up, Left, Right, Right, Left, Down, Down | `0x01` | yes (all car colours) |
| 1 | Right, Down, Right, B | `0x02` | yes (all cars) |
| 2 | Left, Down, Right, A | `0x04` | yes (all Drive-In screenshots) |
| 3 | Up, Up, Down, Down, Left, Right, Left, Right, B, A | `0x08` | yes (90 Boltz + all levels) |
| 4 | Left, Left, Right, Right, B, B, A | `0x10` | yes (Radiator Cap Secret Circuit) |
| 5 | **Left, Right, Left, Right, A, B** | `0x20` | **no — found in ROM only** |

Verification anchors:
- `Left Right Left Right A B` → flag byte `0x02015211 = 0x20`, history index
  reset to 0, engine-sound burst in the recorded audio.
- `Up Up Down Down Left Right Left Right B A` → `0x02015211 = 0x08` and
  `0x02015BF8` (profile+`0xC8`) becomes `0x5A` (90 Boltz).
- `Left Left Right Right B B A` → `0x02015211 = 0x10` and `0x02015BFA`
  (profile+`0xCA`) becomes `0x41` (bit `0x40` set).
- Rejections (flag stays `0x00`, history not cleared): one wrong last button,
  truncated code, reversed code, all-levels with `B` instead of `A`, and 16
  junk presses. See §6b.

Screens walked: title, main menu (New Game / Credits / Options), Options
(A/B swap only), Credits (scroll + Start exits), New Game intro, world map
(Doc's Challenge; cup/race select is the map event icons), event info
(Goal / Best Time / Boltz / Medals), Character Select with its paint/colour
swatch button (garage/paint surface), in-race HUD, pause menu
(Resume / Retry / Quit), Quit confirmation, race-results path. No password,
code, debug, sound-test, gallery or hidden-menu entry was found in any of
them; the only unlock surface is the title button codes.

## 4. Address map

| ROM address | File offset | Meaning |
|---|---|---|
| `0x08018584` | `0x18584` | title-screen per-frame handler that calls the cheat reader and applies flags |
| `0x0801F530` | `0x1F530` | key-history collector: masks key state, appends to ring, calls matcher; store `(keys & 0x3FF000)` |
| `0x0801F5C8` | `0x1F5C8` | **validator**: scans table, compares newest→oldest, sets flag, clears history |
| `0x0801F680` | `0x1F680` | clear history + flag byte (called from `0x08024642` at new-game reset) |
| `0x0801F694` | `0x1F694` | clear 15 history words + index |
| `0x08024604` | `0x24604` | new-game/session reset; `0x08024642` calls `0x0801F680` |
| `0x08016D34` | `0x16D34` | screen-object getter: `0x02015B30 + 0xCC` = screen id, ×0x4C into table |
| `0x0800FE60` | `0xFE60` | generic per-frame screen tick |
| `0x08039DBC` | `0x39DBC` | screen-table entry for screen **17** (title / Press Start) |
| `0x080398B0` | `0x398B0` | screen-object table, stride `0x4C` |
| `0x0802FF58` | `0x2FF58` | text-ID → string pointer lookup |
| `0x0861A400` | `0x61A400` | text descriptor (`[0]=u32 offset-table ptr table`, `[4]=u32 base-ptr table`) |
| `0x08617E40` | `0x617E40` | English u16 text-offset array |
| `0x0861808A` | `0x61808A` | English text base |
| `0x086A5EF8` | `0x6A5EF8` | **cheat table**, 6 × `0x40` |
| `0x08618000`-ish | `0x618000` | ASCII text bank (control-prefixed strings) |

RAM:

| Address | Meaning |
|---|---|
| `0x02015210` | history index (mod 16), byte |
| `0x02015211` | cheat flag byte (bits 0-5 used) |
| `0x02015214 + 4*i` | key-code ring, i = 0..15 |
| `0x02015200` | engine key state (held/edge flags) |
| `0x02015B30` | current profile / save struct (512 bytes) |
| `0x02015BF4` | profile magic `"CARS"` |
| `0x02015BF8` | Boltz (profile+`0xC8`) |
| `0x02015BFA` | circuit unlocks (profile+`0xCA`; bit `0x40` = secret circuit) |
| `0x02015BFC` | screen id (profile+`0xCC`); `17` = title / Press Start |

Key codes stored in the history (custom order, **not** the hardware bit order):

```
A=0x001000  B=0x002000  L=0x004000  R=0x008000
Start=0x010000  Select=0x020000
Left=0x040000  Right=0x080000  Up=0x100000  Down=0x200000
```

(They are `1 << (12 + id)` with id order `A,B,L,R,Start,Select,Left,Right,Up,Down`;
the direction bits are therefore `0x40000..0x200000`, which is why a naive
search for GBA `KEYINPUT` masks finds nothing.)

## 5. Algorithm

### 5.1 Collector (`0x0801F530`)

```c
uint16_t keys = key_state;              // 0x02015200, already edge-processed
uint32_t v = keys & 0x003FF000;         // literal at 0x0801F55C
if (v == 0x001000 || v == 0x002000 || v == 0x004000 || v == 0x008000 ||
    v == 0x010000 || v == 0x020000 || v == 0x040000 || v == 0x080000 ||
    v == 0x100000 || v == 0x200000) {   // single key only
    uint8_t i = *(u8*)0x02015210;
    *(u8*)0x02015210 = (i + 1) & 0x0F;
    *(u32*)(0x02015214 + 4*i) = v;
}
cheat_check();
```

### 5.2 Validator (`0x0801F5C8`)

```c
uint8_t  idx  = *(u8*)0x02015210;      // next write slot
uint8_t  flag = *(u8*)0x02015211;
for (int e = 0; e < 6; e++) {
    uint8_t *ent = TABLE + e*0x40;    // 0x086A5EF8
    int n = ent[1];                   // length
    if (n == 0) continue;
    int h = (int8_t)(idx - 1);        // newest history slot, signed
    int t = n - 1;                    // table index, newest first
    while (h >= 0 && t >= 0 &&
           history[h & 0x0F] == *(u32*)(ent + 4 + 4*t)) {
        if (t == 0) {                 // full match
            if (!(flag & ent[0])) {
                *(u8*)0x02015211 = flag | ent[0];
                clear_history();      // 0x0801F694
                return 1;             // → engine sound at caller
            }
            clear_history();
            return 0;
        }
        h = (h - 1) & 0x0F;
        t--;
    }
}
return 0;
```

Only the **last `n` presses** matter; any prefix is ignored. A match resets the
history, so codes cannot chain off each other. There is no checksum and no
wildcard.

### 5.3 Flag use

At the title handler (`0x08018584`), after a successful read
(`bl 0x0801F530` → nonzero) the game calls `0x080291CC(0)` (engine SFX) and
then:

- if `flags & 0x08`: `profile+0xC8 = 0x5A` (90 Boltz), call `0x080163AC`;
- if `flags & 0x10`: `profile+0xCA |= 0x40`, call `0x08015FD8`;
- all other bits are consumed later by list/result builders
  (`0x0801EC5E`, `0x0801D6C4`, `0x0801CFAA`, `0x0800FABA`, `0x080163B2`,
  `0x0801664C`, `0x08016F78`, `0x08018912`).

The flag byte is cleared when a new game/session is initialised
(`0x08024642 → 0x0801F680`), which is why the effects of the 90-Boltz and
secret-circuit codes are committed to the profile *immediately* on the title
screen, while the other bits must be read before that reset.

## 6. Tables

### 6.1 Cheat table, `0x086A5EF8` (6 × 0x40)

| # | flag | len | key codes | buttons |
|---|---|---|---|---|
| 0 | `0x01` | 8 | `100000 100000 40000 80000 80000 40000 200000 200000` | Up, Up, Left, Right, Right, Left, Down, Down |
| 1 | `0x02` | 4 | `80000 200000 80000 2000` | Right, Down, Right, B |
| 2 | `0x04` | 4 | `40000 200000 80000 1000` | Left, Down, Right, A |
| 3 | `0x08` | 10 | `100000 100000 200000 200000 40000 80000 40000 80000 2000 1000` | Up, Up, Down, Down, Left, Right, Left, Right, B, A |
| 4 | `0x10` | 7 | `40000 40000 80000 80000 2000 2000 1000` | Left, Left, Right, Right, B, B, A |
| 5 | `0x20` | 6 | `40000 80000 40000 80000 1000 2000` | **Left, Right, Left, Right, A, B** |

All six were dumped from the ROM and all six published entries match the
public lists exactly (GameFAQs, IGN wiki, mariogba.nl, supercheats, Good Wiki).
Entry 5 is absent from every list consulted.

### 6.2 Flag consumers

| Flag | Consumer | Effect |
|---|---|---|
| `0x01` | `0x0801E716`, `0x0801CFAA` | paint/colour list; result/“Cheater” check |
| `0x02` | `0x0801EC5E`, `0x0801ECBE`, `0x0801ED1E` | appends all car records to the garage/car list |
| `0x04` | `0x0801D6C4` | Drive-In screenshot list |
| `0x08` | `0x0801859A` | 90 Boltz into profile+`0xC8` |
| `0x10` | `0x080185B2` | secret circuit bit into profile+`0xCA` |
| `0x20` | `0x0800FABA/FBE6/FCB2`, `0x080163B2`, `0x0801664C`, `0x08016F78`, `0x08018912`, `0x0801D65C` | tested as `flags & 0x28` — “cheat used”, suppresses progressive unlock bookkeeping |
| any | `0x0801CFAA` (`flags & 1 || flags & 0x2E`) | draws text ID `0x50` = **“Cheater”** |

Text ID `0x50` resolves through `0x0802FF58` + `0x08617E40`/`0x0861808A` to
file offset `0x618453`, the ASCII string `Cheater`.

## 6b. Enumeration

**Space definition**

- Alphabet: 10 key tokens (`A, B, L, R, Start, Select, Left, Right, Up, Down`).
- History: 16 slots (`0x02015214..0x02015253`), one token per slot.
- Code lengths in the table: 4, 4, 6, 7, 8, 10.
- No checksum, no reserved bits, no wildcard, no field payload: the table is a
  lookup of exact suffixes.
- Representable 16-press streams: `10^16`; representable *codes*
  (table entries): **6**. Accepted inputs are any prefix followed by one of the
  six sequences; the moment the suffix completes, the code fires.

**Closure proof**

- The matcher is called from exactly one place (`0x0801F5B6` inside
  `0x0801F530`) and the table pointer (`0x086A5EF8`) is loaded once
  (`0x0801F644`). `0x0801F530` is called from exactly one place
  (`0x0801858A`), and the only reference to `0x08018584` is the Thumb pointer
  `0x08018585` stored at `0x0803D51C`; no BL/BLX reaches it. There is no second
  entry point and no second table.
- A scan of the whole ROM for runs of ≥3 little-endian words drawn from the
  ten key codes found exactly the six table runs (plus one unrelated data
  coincidence at `0x086F2B70`, which is a curve table, not a code list).
- The loop bound is six (`cmp r0,#5`), so no seventh entry can be read.

**Novel code (not in any published list)**

```
Left, Right, Left, Right, A, B        flag 0x20, length 6
```

Entered on the Press Start screen in mGBA:
- `0x02015211` becomes `0x20` (savestate byte dump);
- history index resets to 0 (match accepted and cleared);
- recorded audio shows the engine-sound burst (SDL `disk` driver): RMS rises
  from the ~7000 music floor to ~11,200 in the 5.1-6.8 s window after the code;
  an invalid sequence in the same harness shows no burst;
- the code commits no profile bytes at the title screen, unlike entries 3/4.

Its distinct effect is the “cheat used” marker: `0x20` is only consumed by
`flags & 0x28` tests (same path as the all-levels cheat) to suppress
progressive unlock bookkeeping, and, like every cheat bit, it satisfies the
“Cheater” condition at `0x0801CFAA`.

**Bounds proven by rejection** (all in mGBA, flag `0x02015211` read from a
savestate after each attempt):

| Input | Result |
|---|---|
| `Left Right Left Right A B` | **accept**, `flags=0x20`, index 0 |
| `Left Right Left Right A A` | reject, `flags=0x00`, index 6 |
| `Left Right Left Right` (truncated) | reject, `flags=0x00`, index 4 |
| `B A Right Left Right Left` (reversed) | reject, `flags=0x00`, index 6 |
| `Up Up Down Down Left Right Left Right B B` (all-levels, last button wrong) | reject, `flags=0x00`, index 10 |
| 16 junk presses `Up Down Left Right` ×4 | reject, `flags=0x00`, index 0 |

The offline reimplementation (`/tmp/opencode/cars/verify_codes.py`) reproduces
the same accept/reject behaviour for the whole table and for every
single-symbol mutation (0 mutations match).

## 7. Validation evidence

- **Observed**
  - ROM boots to the Cars logo / “Press Start”; mGBA screenshots at each menu.
  - All six table sequences entered one at a time; the matching flag bit in
    `0x02015211` is set and the history clears. Entry 3 additionally sets
    `0x02015BF8 = 0x5A`; entry 4 sets `0x02015BFA |= 0x40`.
  - Entry 5 accepted and audio-confirmed; no published list contains it.
  - Rejected variants leave `0x02015211 = 0x00`.
  - Screen id at the title is 17 (`0x02015BFC`), matching screen-table entry
    `0x08039DBC`.
- **Derived**
  - Table layout, 0x40 stride, 6-entry bound and validator flow from
    `0x0801F5C8` disassembly (validated against accepted codes).
  - Flag consumer map (addresses in §6.2) and text ID `0x50 = "Cheater"`.
  - `0x20` is only ever tested as part of `0x28`/`0x2E`; no code tests it
    alone.
- **Inferred**
  - The engine-noise confirmation is the intended “code accepted” feedback,
    matching the published instructions; confirmed by audio capture for valid
    vs invalid input.
  - The “Cheater” result message is the visible consequence of the flag byte;
    the drawing function (`0x0801CE88` → `0x0801CFAA` → text `0x50`) and its
    text were identified statically (see Unknowns for the gate).

## 8. Unknowns

- **“Cheater” label not observed on-screen with a live cheat flag.** The title
  handler commits flags `0x08/0x10` to the profile immediately, but the whole
  flag byte is cleared by `0x0801F680` at new-game reset, and no savestate
  containing a valid “continue” save could be produced in this session (the
  game writes its 512-byte EEPROM profile only on its own save points; a
  transplanted profile was not accepted as valid). The consumer
  (`0x0801CFAA` → text ID `0x50`) is proven statically and by text-table
  resolution, but the on-screen label is **derived**, not observed.
- The exact result/stats screen that calls `0x0801CE88` was not reached; it is
  the only caller chain that prints text `0x50`.
- Maker code `78` is recorded as-is; no independent publisher lookup was done.

## 9. Tooling

- `arm-none-eabi-objdump` (binutils-arm-none-eabi), Capstone 5.0.7 for scans.
- mGBA 0.10.5 SDL under `Xvfb :230`; `xdotool`, `scrot`; SDL `disk` audio
  driver for the confirmation-sound capture.
- mGBA savestate PNG → `gbAs` zlib chunk decode for RAM checks (EWRAM at
  state offset `0x21000`, so `state[0x21000+addr-0x02000000]`).
- `/tmp/opencode/cars/verify_codes.py` — offline validator + table dump
  (`/tmp/opencode/cars` also holds the screenshots and audio captures).
- Key scan scripts were ad-hoc Python/Capstone: literal-pointer scans for
  `0x02015210`, `0x02015B30`, `0x086A5EF8`, BL scans for `0x0801F530/5C8/680`,
  and a whole-ROM scan for runs of key-code words.

## 10. Legal

No ROM, graphics, audio or game text is redistributed here; only hashes,
addresses, algorithms and short code sequences are published for
interoperability/analysis.
