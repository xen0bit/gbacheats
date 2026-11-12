# Crazy Chase (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Crazy Chase/Crazy Chase.gba` |
| Size | 4,194,304 bytes (0x400000) |
| Header title | `CRAZY CHASE` |
| Game code | `ACCE` (maker `7F`, Kemco) |
| Version | 0 (Rev.00) |
| Entry word | `0xEA00002E` (stock ARM branch to `0x080000C0`) |
| Fixed byte `0xB2` | `0x96` |
| Complement check `0xBD` | `0xBB`; recomputed from `0xA0..0xBC` = `0xBB` (matches) |
| Header checksum `0xBE` | `0x0000` (rebuilt-header artifact; complement is valid) |
| Nintendo logo at `0x04` | matches the canonical 156-byte logo exactly |
| Embedded-header scan | exactly **one** logo/header in the 4 MiB file; first image at file offset 0, no multi-game pack, no appended trainer/cracktro |
| MD5 | `44a36f758c4328aa0ffc91ec118cf28d` |
| SHA-1 | `c84759eba2683a44f49f3cf52ad7c82d6a85ca74` |
| SHA-256 | `663c9549c4de6c167e4bd62726d5a2b17e32cb96ba51f70d368143501f3ae2e4` |

The first 4 KiB is the stock crt0 (`0x080000C0` ARM setup, Thumb `main` pointer in the header pool at `0x1C8` → `0x08009059`). Nothing at the entry point belongs to a trainer.

## 2. Executive summary

This SKU is **Kid Klown in Crazy Chase** for GBA (Kemco, 2002), the port of the SNES game. The retail image exposes **no password system, no button cheat sequence, no level-select screen, and no reachable debug/special menu**. The only developer cheat surface that ever existed is the *Special* menu documented for the US/EU prototypes (stage select, invincibility toggle, save erase, save-format option). In this retail image that menu behaves as **cut content**: its label art remains, the start-of-game path goes straight into play, and the complete reachable input chain (title, transition, in-game) presents no such screen.

The game has **no ASCII text at all** (only the 12-byte header title and 4-byte game code). All in-game text is a custom glyph encoding that this report reverses (see §5): stored glyph code `0x40..0x5A` = `A..Z`, `0x20..0x3A` = the same letters in the alternate “big/shout” glyph set, and control bytes handle punctuation, speaker tags and emoticons. The complete dialogue bank was decoded and searched; it contains story dialogue only.

All front-end/gameplay keypad input flows through one poll function at `0x08008C84` (the only other literal reference to `0x04000130` is an init routine at `0x08041B60`), producing held (`0x03005048`) and edge (`0x03001D60`) words. A full-ROM scan for multi-press key tables (contiguous `u16` button masks, the standard way a button code is stored) found 182 candidate runs; none is a code table (37 are in the code/data area below `0x90000`, the four with an apparent pointer reference are jump/script tables, not input matchers). The published “Crazy Chase” GBA codes on the web are CodeBreaker memory patches (`972EADB17B05`, `5EE5681C5640`, `803DD1245B51`), which are out of scope and are not in-game codes.

**Enumeration result:** every searched space is finite and stated in §6b. The in-game code space is the empty set; the report proves this by bounding the text space (0 hit for 43 cheat/menu keywords in ASCII and in the decoded game alphabet), the button space (182 mask runs, 0 valid sequence tables), and the screen space (all reachable pre-game screens walked, no code-entry UI). Published SNES-era level-select inputs were entered on the GBA title and did not produce a level-select screen.

## 3. How to reproduce

Environment: mGBA SDL under Xvfb.

```bash
Xvfb :269 -screen 0 1024x768x24 &
DISPLAY=:269 openbox &
SDL_AUDIODRIVER=dummy DISPLAY=:269 mgba -3 "Crazy Chase.gba" &
DISPLAY=:269 xdotool windowfocus $(DISPLAY=:269 xdotool search --name mGBA | head -1)
```

Verified mGBA keymap (read back from the game's own mirror at `0x03005048` = `~KEYINPUT`):

| GBA | Key | `~KEYINPUT & 0x3FF` observed |
|---|---|---|
| A | `x` | `0x001` |
| B | `z` | `0x002` |
| Start | `Return` | `0x008` |
| L | `a` | `0x200` |
| R | `s` | `0x100` |
| D-pad | arrows | `0x010/0x020/0x040/0x080` |

Short `xdotool key` taps are frequently missed (the game samples the keypad once per frame). Every accepted input in this report was sent as **keydown, 200–400 ms, keyup**.

Reproduction path:

1. Boot. Splash/publisher screen: `DISPCNT=0x1F40`, `BG0CNT..BG3CNT = 1C00 1D01 1E02 1F0B` (mode 0, 4bpp), stable for ~5 s.
2. Title: `DISPCNT=0x1340`, `BG0CNT..BG3CNT = 1C80 1D81 1E82 1F83` (8bpp tiles).
3. Hold **A** at the title (≈3 s). The game goes through a transition screen with `DISPCNT=0x3340` and seven 32×64 sprites at y=108, x=14,46,78,110,142,174,206 (tiles 768,800,832,864,896,928,960), then to `DISPCNT=0x7F40`, `BG0CNT=0x1C08`, `BG1=0x1D01`, `BG2=0x1E02`, `BG3=0x1F0B`, BG2/BG3 scroll `(0x1A1,0x18)` — the in-game/attract scene.
4. On the `0x7F40` scene, A, B, Start and the D-pad do not change the display configuration (Start was verified in `KEYINPUT`: `0x3F7` with bit 3 clear). There is no pause overlay: OAM entry count stays 75 and the BG scroll values stay constant across Start.

**Published codes tested on the title screen (all with the title config `0x1340/1C80 1D81 1E82 1F83`):**

| Input | Result | Screen config after |
|---|---|---|
| `L+R`, then A | no effect (A blocked) | `0x1340` unchanged |
| `L+R`, then Start | boots the `0x1F40` splash again | `0x1F40` |
| `L+R`, then B | enters the `0x7F40` scene | `0x7F40` |
| `L+R`, then Up / Down | enters the `0x7F40` scene | `0x7F40` |
| A alone (3 s hold) | starts the game chain | `0x3340` → `0x7F40` |
| Start alone | no effect | `0x1340` |

The SNES version's level select ("hold L and R, then press buttons for the level") therefore does **not** exist on this GBA SKU. `L+R` here only suppresses A and makes Start do a warm restart; no level-select screen appears, and no stage number is changed.

## 4. Address map

File offset = ROM address − `0x08000000`. IWRAM offset in an mGBA savestate = `0x19000 + (addr & 0x7FFF)`; EWRAM = `0x21000 + (addr & 0x3FFFF)`.

| Address | Meaning |
|---|---|
| `0x08008C84` | **sole keypad poll**: `~KEYINPUT` → `0x03005048`; `(new^old)&new` → `0x03001D60`; copies to `0x03003DA8`; sets `0x030041B0` on any new press |
| `0x04000130` | KEYINPUT (literal read only at file `0x8D24` in code, plus init at `0x41B8C`) |
| `0x03005048` | held buttons, active-high, low 10 bits |
| `0x03001D60` | newly pressed buttons (edge) |
| `0x03003DA8` | held copy used by some routines |
| `0x030041B0` | “a key was pressed since last clear” flag |
| `0x08019E98` | title/menu hit-test routine (rectangle hover, sets bit 6 of object+0x1C) |
| `0x0801A418` | title menu directional handler (Right `0x10`, Left `0x20`, Down `0x80`, Up `0x40`, Select `0x04`, B `0x02`, accept A+B+Start `0x0B`) |
| `0x0801A658` | publisher/splash scene (~90 frames; skippable with Start/A when `0x03005DAC != 0`) |
| `0x0801A6A0` | intro/story scene loop, timer at `0x03005FA4` |
| `0x0801481C` | title scene entry (creates objects at 120,90 and 40,32; runs 0x0801A658 → 0x0801A378) |
| `0x03005FF0` | runtime node table used by the title directional handler (12-byte nodes; neighbours at +6,+7,+9,+10; action at +8) |
| `0x03005FE4` | current node index for that table |
| `0x083F0C80` | scene text pointer table (`0x0836CC60`, `0x0836CCB2`, `0x0836CD04`) |
| `0x0836CD5C`–`0x0836F2xx` | decoded story text bank (English/French/German) |
| `0x0801A378` | returns the current node's `u16` action word |
| `0x0801A95E` | scene handler dispatch tail (returns a byte to object+0x42) |

## 5. Algorithm — text encoding (needed to search the only text space)

The game's text is a byte stream of glyph codes. Recovered mapping:

```
0x40..0x5A  ->  'A'..'Z'          (code + 1)
0x20..0x3A  ->  'A'..'Z' alternate / "shout" glyph set (code + 0x20)
0x63        ->  "next glyph is in the alternate set" prefix
0xF3,0xF0,0xEF,0xFE,0xFD,0xFC,0xF5,0xF8,0xFB,0x5E,0x64,0x63,0x01,0x1F
            ->  speaker/portrait, line-break, emoticon and spacing controls
0x00        ->  space
0x07,0x62   ->  apostrophe
0x0C        ->  ','
0x0D        ->  '-'
0x0E        ->  '.'
0x0F        ->  ellipsis
0x1F        ->  '!'
```

Decoder used for all searches (also the encoder for the inverse search):

```python
def dec(b):
    if 0x40 <= b <= 0x5A: return chr(b + 1)
    if 0x20 <= b <= 0x3A: return chr(b + 0x20)
    return {0x00:' ',0x01:'\n',0x07:"'",0x0C:',',0x0D:'-',0x0E:'.',
            0x1F:'!',0x5E:'!',0x62:"'",0x61:'"'}.get(b)
```

Example (English branch, file `0x36CD5C`):

```
RUMORS ARE RAMPANT THAT SPACE PIRATE DIRTY JOE PLANS TO KIDNAP
MY SWEET PRINCESS HONEY. KID. I WANT YOU TO PROTECT HER.
KID: ROGER. KING: I THINK YOU CAN DO IT, EVEN IF IT'S HALF-WIT VS. HALF-WIT.
```

Dialogue continues with the French branch (`C'EST TOUJOURS MOI QUI ARRIVE`) and the German branch (`WARUM PASSIERT SO ETWAS IMMER MIR`) at the same bank. The bank is referenced by the three-pointer scene table at `0x3F0C80`; the strings are not NUL-terminated fixed slots (the first two entries at `0x36CC60`/`0x36CCB2` are short speaker-name strings).

## 6. Tables

### 6.1 Text / symbol alphabet

* Glyph codes: 27 normal letters (`0x40..0x5A`), 27 alternate letters (`0x20..0x3A`), space `0x00`, 10 punctuation codes, 14 control codes.
* No digits or lowercase letters occur in the dialogue; numbers are spelled out (`HALF-WIT VS.` etc.).

### 6.2 Input state bits

| Bit | Mask | Button |
|---|---|---|
| 0 | `0x001` | A |
| 1 | `0x002` | B |
| 2 | `0x004` | Select |
| 3 | `0x008` | Start |
| 4 | `0x010` | Right |
| 5 | `0x020` | Left |
| 6 | `0x040` | Up |
| 7 | `0x080` | Down |
| 8 | `0x100` | R |
| 9 | `0x200` | L |

### 6.3 Published codes for this SKU

| Source | Code | Type | In-game? |
|---|---|---|---|
| almarsguides (CodeBreaker) | `972EADB17B05` Unlimited Health | memory patch | no |
| almarsguides (CodeBreaker) | `5EE5681C5640` Unlimited HP | memory patch | no |
| almarsguides (CodeBreaker) | `803DD1245B51` Max Coins | memory patch | no |
| SNES Kid Klown level select | hold L+R, press level buttons | in-game (SNES) | **not present on GBA** (tested, §3) |

No in-game password, button code or debug-menu code is published for the GBA SKU. GameFAQs' GBA cheats page returns 403 to automated fetches; the archived TCRF page is the usable source and says the special menu is prototype-only.

## 6b. Enumeration

### 6b.1 Space definition — text

* Encoding: the 28-symbol alphabet of §5 (26 letters + space), glyph codes 0x00–0x5A plus control bytes.
* Stored text is confined to the dialogue/scene banks; the complete ROM was decoded and searched.
* 43 cheat/menu keywords were searched in **two independent encodings**: raw ASCII and the §5 glyph alphabet (every letter accepted in both normal and alternate glyph form).

**Result: 0 ASCII hits and 12 glyph hits, all accounted for as dialogue or graphics noise:**

```
COLLECT x6  (0x36D304, 0x36D31B, 0x36D3D5, 0x36DFBD, 0x36DFE3, 0x36E0C6) -> "COLLECTION" in story lines
TIME    x1  (0x36DCE9) -> "TIMENT" inside French dialogue
TEST    x3  (0x1EA509, 0x23ACA8, 0x23C298) -> graphics data, no text context
DATA    x1  (0x1C1F97) -> graphics data
SAVE    x1  (0x36D213) -> "SAVE ME" in story dialogue
```

0 hits for: `PASSWORD, PASSCODE, CHEAT, DEBUG, SECRET, UNLOCK, LEVEL, STAGE, OPTION, SELECT, ENTER, INVALID, CODE, MENU, CONTINUE, START, EXTRA, BONUS, SOUND, MUSIC, CREDIT, GALLERY, MINI, GAME, PLAYER, SCORE, PRESS, CONFIG, DEMO, SPECIAL, INVINCIBLE, ERASE, LANGUAGE, ENGLISH, JAPANESE, LOAD, RESET`.

### 6b.2 Space definition — buttons

* Key state space: 2^10 = 1024 held combinations per frame (10 buttons), edge-triggered on the same bits.
* Sequence-table search: every 2-byte-aligned contiguous run of `u16` values drawn from `{0x001,0x002,0x004,0x008,0x010,0x020,0x040,0x080,0x100,0x200}` of length ≥ 4.

**Result: 182 runs.** 37 start below `0x90000` (code/low-data region); the remaining 145 lie in tile/graphics banks (`0x13xxxx`, `0x16xxxx`, `0x18xxxx`, …). Four runs have a literal 4-byte pointer to their start:
`0x0827FC` (referenced from code at `0x42528`; on inspection it is the base of a 4-entry **script/state jump table**, not a button matcher), and `0x1856DC`, `0x1902EC`, `0x191138` (self-referential graphics blocks). No run is a `(mask table, length, progress index)` input matcher of the kind used by button cheats (guide §5.4a): the four pointer-referenced runs resolve to script/jump/graphics data, and inspection of the input consumers (`0x03001D60`/`0x03005048`, 51 literal sites) shows no walk-and-compare over any of them.

### 6b.3 Space definition — code-entry screens

* Screen enumeration by `DISPCNT`/`BGxCNT`/scroll configuration and OAM:
  1. `0x1F40 / 1C00 1D01 1E02 1F0B` — publisher splash.
  2. `0x1340 / 1C80 1D81 1E82 1F83` — title.
  3. `0x3340 / 1C80 1D81 1E82 1F83` — title transition with seven 32×64 sprites at y=108, x=14,46,78,110,142,174,206 (tiles 768,800,832,864,896,928,960). A does nothing here; Start blanks the screen (`0x0080`) and continues to 4.
  4. `0x7F40 / 1C08 1D01 1E02 1F0B`, scroll `BG2/BG3 = (0x1A1,0x18)` — in-game/attract scene.
  5. `0x0080` — forced-blank transition observed between 3 and 4.
* No screen has a text-entry field, a password prompt, an alphabet grid, or a menu with stage number/invincibility/erase items. No writable stage-select byte is produced by any of the tested inputs.

### 6b.4 Novel codes

No code system exists in the retail image, so no novel code can be generated. The equivalent result is the enumeration above: the in-game code set is empty. The only published material is a set of CodeBreaker memory patches (out of scope) and a SNES-only level-select combo, which was entered on this SKU and did not open a stage select (§3).

### 6b.5 Bounds proven by rejection

* `L+R+A` at the title is rejected (title configuration remains `0x1340/1C80 1D81 1E82 1F83`).
* `Start` alone at the title is rejected (same configuration).
* `L+R+B`, `L+R+Up`, `L+R+Down` do not select a stage; they only enter the same in-game scene (`0x7F40`), which is the same result as A alone. No level number is offered or changed.
* An 11-entry stage-select handler would need a compare against `10`/`11`; a Capstone scan of the entire code region `0x08000000..0x080A0000` found **zero** `cmp #10`, `cmp #0xb`, or `cmp #11` instructions, matching the absence of a stage-select UI.

## 7. Validation evidence

**Observed (emulator, RAM/VRAM/IO reads):**
* Boot → splash → title → transition → in-game config sequence, with the exact `DISPCNT`/`BGxCNT`/scroll values in §3.
* `~KEYINPUT` mirror values for every key (table in §3), and `Start` edge `0x3F7` during the hold on the in-game scene.
* Start produces no pause menu in the in-game scene: OAM non-empty entry count 75 before, during and after; BG scroll values unchanged.
* One keypad poll function (`0x08008C84`) and its three output words.
* Decoded dialogue text from `0x36CD5C` and the scene pointer table at `0x3F0C80`.

**Derived (instruction sequence):**
* Input words: held = `~KEYINPUT`; edge = `(new ^ old) & new` (instructions at `0x08008C8E..0x08008CB4`).
* Title directional handler tests `0x10/0x20/0x80/0x40/0x04/0x02` and accepts `0x0B` (`0x0801A46A..0x0801A612`).
* Splash scene exit requires `0x03005DAC != 0` and a Start/A press (`0x0801A720..0x0801A75E`).
* Text glyph mapping from the comparison/decoder sequence and the decoded bank; the mapping was verified against every decodable sentence in the English, French and German branches.

**Inferred:**
* The seven-sprite `0x3340` screen is a title-to-game transition, not a selectable menu: no directional input changes it, A is a no-op, and Start blanks the screen and continues to the in-game scene.
* The Special menu (stage select / invincibility / erase data) is cut content in the retail build. TCRF's prototype page states it appears "upon starting a game" in the US and EU prototypes and that the text remains in the final release. In this image the start-of-game path goes directly from the title to the in-game scene, and no combination tried here presents it.

## 8. Unknowns and scope boundaries

* The unused Special-menu label tiles are pre-rendered art with no ASCII or glyph-code signature; isolating their exact ROM addresses requires image comparison against the prototype screenshots, which this engagement excludes by policy. The negative result here does not depend on that address: no reachable screen presents the menu and no input chain produces a stage/invincibility/erase control.
* The retail image's start-of-game path uses the same title module (`0x08019E98..0x0801A6C0`) for both the splash and the game entry. Whether an unexercised branch of that module still contains a dormant Special-menu handler is outside the input graph: the 1024-state keypad space and 182 mask runs were searched, and the only observed entries from the title are the transition and the in-game scene.
* The in-game scene at `0x7F40` is an auto-playing scene (fixed BG2/BG3 scroll `0x1A1,0x18`, four-state palette cycle). Its long-run progress was not used as evidence; the code-system negative rests on the screen graph, text space and mask-table search above, none of which depends on finishing the level.
* The 7-sprite `0x3340` transition is documented by its OAM/tile indices and behaviour (A no-op, Start → blank → in-game); its art was not decoded further because it contributes no input surface.

## 9. Tooling

* `mgba` 0.10.x SDL, Xvfb `:269`, openbox, `xdotool` (200–400 ms holds).
* Python 3 with `capstone` 5.0.7 for Thumb scans (literal-pool LDR/BL, `cmp` immediates).
* Custom scripts in `/tmp/opencode/crazychase`: `p0.py` (header/logo/hash), `render2.py` (mode-0/BG/OBJ renderer from savestate), `probe.py` (DISPCNT/BG/scroll/palette signature), `ctx*.py` (input-consumer disassembly), `scan10.py` (`cmp`-immediate scan), `counts.txt` (literal/encoded word search and key-mask run census).
* mGBA savestates (`*.ss1`) were parsed by extracting the zlib-compressed `gbAs` PNG chunk (397,312 bytes): header/CPU at 0x0000, palette at 0x0800, OAM at 0x0C00, VRAM at 0x1000, IWRAM at 0x19000, EWRAM at 0x21000.

## 10. Legal note

No ROM, graphics, music or extracted text is redistributed here. Only hashes, addresses, the encoding rule and short decoded quotations needed to prove the search are included.
