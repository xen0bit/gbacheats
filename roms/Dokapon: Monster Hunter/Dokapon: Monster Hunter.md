# Dokapon: Monster Hunter (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Dokapon: Monster Hunter/Dokapon: Monster Hunter.gba` |
| Size | 8,388,608 bytes (8 MiB); meaningful data `0x000000–0x62FFFF`; `0x630000–0x7FFFFF` is 0x00 fill |
| Header title (`0xA0`) | `DOKAPON` |
| Game code (`0xAC`) | `ADQE` (USA) |
| Maker (`0xB0`) | `7M` |
| Version (`0xBC`) | 0x00 |
| Complement (`0xBD`) | 0xA6 — matches `-(sum(0xA0..0xBC)+0x19) & 0xFF` |
| Header checksum (`0xBE`) | 0x0000 (common artifact of a rebuilt header; complement byte is correct) |
| Entry word (`0x00`) | `0xEA00002E` (stock ARM branch to `0x080000C0`) |
| MD5 | `936a8172335ffc3391d182e909942d76` |
| SHA-1 | `280f9e01a3caee74bc9fde55e6326005ddba5196` |
| SHA-256 | `07f77eb7c45147f6c17051af6a15e9773ba15bdb2b7c9b8a7f7c6d5dd65b1f8c` |

Embedded-header scan: exactly **one** 156-byte Nintendo logo hit (file offset `0x4`), so this is a
single game image, not a 2-in-1 pack. The entry branch, crt0 at `0x080000C0` and the literal
`0x080031C5` (main) at `0x08000100` are stock; no cracktro, trainer, or appended payload.
The ROM contains **no ASCII text at all** (see §2/§5) — the absence of a cracktro banner is
therefore proven by the intact entry/crt0 rather than by a string scan.

## 2. Executive summary

The retail US image contains **no password, cheat-code, or menu-code system**. There is no
text-input screen, no validator, no code alphabet, and no hard-coded code table. Every menu
reachable from the title and from the in-game pause menu was walked (§3, §7):

* title (`PRESS START`, ©2001 Asmik Ace/TYCOON) — no button combination has any effect (§6b);
* main menu — `Continue` / `Start` / `Delete`;
* file select — `File1`/`File2`, name `POPONSA`, LV, Quest, Time;
* new-game intro (dialogue only; the line “write your name on this adventurer test application
  form” is narrative — no name-entry keyboard or text field exists), guild-master test, field;
* pause — `item` / `arms` / `change` / `system`;
* system submenu — `Diary` (= save: “Put adventure in diary? Yes/No”), `Flash` (battle-animation
  ON/OFF), `Mss` (message speed Fast/Normal/Slow), `Album` (W-weapons/Shields/Monsters), `Skill`
  (W-skills/S-skills/S-supports).

All codes published for this SKU (GameFAQs, GameHacking.org, Ethereal Games, Almar's Guides) are
GameShark/CodeBreaker/Action Replay **memory-hack codes** (address/value pairs, e.g.
`00006D2E 000A`, `DB5B5915 1512`). They are out of scope here and cannot exist as ROM literals;
none were used or verified as in-game codes. The only GameFAQs “secret” is the post-game
`NewLand` area, a gameplay unlock, not a code.

One genuine hidden developer screen exists: a **seven-category debug menu** at `0x08007A1C`
(categories `Item / Char-btl / Scenario / Event / W-comp / S-comp / Sound`). It is gated by a
save-header halfword `0x6264` at `0x03004C60+0x0A` plus **Select** while the main menu’s internal
state is 1. The boot sanitizer at `0x08006574` preserves `0x6264` but **no code in the ROM writes
it**; retail input never sets the required state. It was therefore entered by a debugger jump for
documentation (§6b), and its first page was observed on screen: `Item 1/190` with entries
`Recover1`, `Recover2`, `Energy1`, …

The most reusable result is the **text encoding**: all UI/dialogue text is 16-bit little-endian
font codes, not ASCII, so ordinary `strings` finds nothing. Mapping:
lowercase `= ASCII + 0x1A`, uppercase `= ASCII − 0x0B`, space `0x0001`, `0xFFFF` end-of-string,
`0x0010` newline, and `0x83xx`/`0x90xx` inline tags (§5).

## 3. How to reproduce

Emulator: mGBA 0.10.2 (SDL) under `Xvfb :345 -screen 0 1024x768x24` + `openbox`,
`SDL_AUDIODRIVER=dummy`. Window captured with `import -window root` and cropped
`720x480+152+144` (3× scale).

Keymap used (mGBA SDL default): **A = `x`, B = `z`, L = `a`, R = `s`, Start = `Return`,
Select = `BackSpace`**, D-pad = arrows. Hold 100–200 ms; the menus debounce.

Exact paths:

1. Boot → title → **Start** → main menu (`Continue/Start/Delete`).
2. `Continue` + A with the retail save loads the field directly (no file screen when one save
   exists); `Start` + A reaches the file-select screen first.
3. In the field: **Start** opens the pause menu; **Right** cycles
   `item → arms → change → system`; A opens the active tab.
4. `system → Diary → A → Yes` writes the 32 KiB SRAM save (`DOKAPON-Q` header at offset 0).

Debug-menu reachability test (all performed with the save-header halfword set to `0x6264` by
byte-patching a copy of the `.sav` at offset `0x0A`, so that the ROM’s own flag test passes):
at the main menu, `A`, `B`, `Select`, `L`, `R`, `Start`, and direction+button combinations were
pressed with the cursor on each of the three items. None opened the debug menu; the ROM’s own
flag branch *was* taken (breakpoint at `0x080071E6` read `r0 = 0x6264`). To document the screen,
PC was set to `0x08007A1D` from mGBA’s CLI debugger (`-d`) at the menu, `r13 = 0x03007C00`.
That is instrumentation, not an in-game route, and is labelled as such in §7.

## 4. Address map

| Address | Meaning |
|---|---|
| `0x04000130` | KEYINPUT (active-low) |
| `0x080008DC` | key-read routine: `pressed = ~KEYINPUT & 0x3FF`, edge/repeat |
| `0x03002564` | key state: `+0` held mask, `+2` new-press mask, `+4` repeat mask, `+6` counter, `+8` delay, `+0xA` interval, `+0xC` previous |
| `0x03001D38` | engine global block (scene/state counters; `+0x1A8` scene value) |
| `0x03004C60` | 0x20-byte save header in IWRAM (copy of SRAM offset 0) |
| `0x03002AB8` | menu/window object used by the main menu |
| `0x0E000000` | SRAM / flash save window (32 KiB `.sav`) |
| `0x0807C680` | ROM save-header template: `"DOKAPON-Q\0\0\0"` + palette/table data |
| `0x08006574` | save-header init/sanitizer (magic compare + `0x6264` allow-list) |
| `0x08007154` | main-menu (`Continue/Start/Delete`) handler |
| `0x080071E2` | `ldrh r0,[0x03004C60+0x0A]` — US-version/debug flag test |
| `0x08007248` | flag-gated A-key path (`0x08006B7C`, `0x080081A0(0x1C)`) |
| `0x0800731E` | flag re-test before the debug entry |
| `0x08007328` | `KEY & 4` (Select) test |
| `0x08007334` | `bl 0x08007A1C` — debug menu entry (only call site) |
| `0x08007A1C` | debug-menu main loop (7 pages) |
| `0x08007B80` | debug page renderer 0 — category list |
| `0x08007DCC` | debug page renderer 1 |
| `0x0800802C` | debug page renderer 2 |
| `0x080081A0` | debug page renderer 3 |
| `0x080082F0` | debug page renderer 4/5 |
| `0x08008584` | debug page renderer 6 |
| `0x08495332` | category label table (7 records, 16-byte stride): `Item \| Char-btl \| Scenario \| Event \| W-comp \| S-comp \| Sound` |
| `0x080B78C0` | item-list record table (12-byte stride) used by the Item page |
| `0x084B35A0` | item stat table (12-byte stride) |
| `0x080A89D4` | item name strings (`Recover1`, `Recover2`, `Energy1`, `Revival`, `Compass`, …) |
| `0x084952FC` | `"{{US VERSION"` label drawn when the gate flag is set |
| `0x084958A0` | main-menu / file-select string bank (`Continue`, `Start`, `Delete`, `File`, `Open`, `Time`, `Poponga`) |
| `0x08494FEC` | Album/Skill help-string bank (`Display weapon guide`, `List of weapon skills`, …) |
| `0x084958BC` | `Continue/Start/Delete` list text pointer |
| text banks | dialogue ~`0x03D000–0x07A000`; menu/debug ~`0x495000–0x49C000` (all 16-bit font codes) |

Function scan notes: `0x08007154` has exactly one BL caller (`0x08003260`); `0x08007A1C` has
exactly one BL caller (`0x08007334`) and no pointer references — so the debug menu has a single
entry edge.

## 5. Algorithm

### 5.1 Input state (0x080008DC)

```
mask = (~*(u16*)0x04000130) & 0x3FF     ; 1=A 2=B 4=Select 8=Start 0x10=Right
                                        ; 0x20=Left 0x40=Up 0x80=Down 0x100=R 0x200=L
st->held = mask
st->new  = mask & ~st->prev
st->prev = mask
; +4/+6/+8/+0xA implement key repeat
```

### 5.2 Text encoding (discovered; required for any string search)

```
u16 code at even offset:
  0x0036..0x004F -> 'A'+ (code-0x36)      ; A..Z
  0x007B..0x0094 -> 'a'+ (code-0x7B)      ; a..z
  0x0050..0x0059 -> '0'+ (code-0x50)      ; digits (observed in menus)
  0x0001 -> ' '   0x000C -> '.'   0x000B -> ','
  0x000D -> '!'   0x0052 -> '?'   0x0053 -> '\''
  0x0010 -> newline
  0xFFFF -> end of string
  0x8300 / 0x8301 / 0x8302 -> inline highlight/colour tags
  0x9000 -> wide/soft space
```

The mapping is not ASCII: `strings`/`grep` on the `.gba` returns zero English words. Decoding the
whole image at 16-bit alignment yields 10,428 readable strings (see §6b).

### 5.3 Save header and the debug gate

Save header at SRAM offset 0 (= IWRAM `0x03004C60`, 0x20 bytes):

```
+0x00  "DOKAPON-Q"    (9 bytes)
+0x09  00
+0x0A  u16 gate/version value   ; 0x0000 in retail saves, 0x6264 = debug/QA marker
+0x0C  u8  valid = 1
+0x18  u32 01 00 00 00
+0x1C  u32 counters/timestamps
```

`0x08006574`:

```
copy 0x20 bytes of header to SRAM 0x0E000000
if (memcmp(header, template@0x0807C680, 10) != 0):
        memset(header, 0, 0x20); memcpy(header, template, 10); header[0x0C] = 1
if (*(u16*)(header+0x0A) != 0x6264) *(u16*)(header+0x0A) = 0
```

Main-menu handler `0x08007154`:

```
if (*(u16*)(0x03004C60+0x0A) != 0) {
        draw_text(0x084952FC, "US VERSION", ...)        ; 0x080071FC
        if (KEY.new & 1) {                              ; A
                sub_08006B7C(1); sub_080081A0(0x1C);
                menu.state = 1;  return;                ; 0x0800726C
        }
}
...
if (menu.state == 1) {
        r = input_handler(menu[0x0E]);
        if (r < 0) redraw;
        if (*(u16*)&menu[0x0E] == 1 &&
            *(u16*)(0x03004C60+0x0A) != 0 &&
            (KEY.held & 4)) {                            ; Select
                sub_08007A1C();                          ; debug menu
        }
}
```

Because the sanitizer only preserves `0x6264` and nothing in the image produces it, the gate is a
debug-save marker, not a player-achievable state. Everything below the `A` branch is dead in a
retail save.

## 6. Tables

### 6.1 Debug-menu categories (0x08495332, 7 × 16-byte records)

| # | Label | Observed content |
|---|---|---|
| 0 | `Item` | item list, counter observed `1/190`; first entries `Recover1`, `Recover2`, `Energy1` |
| 1 | `Char-btl` | character/battle records (renderer `0x08007DCC`) |
| 2 | `Scenario` | scenario records (`0x0800802C`) |
| 3 | `Event` | event-flag list: `BOSS`, `VALTZ`, `COMPASS`, `EXIT`, `WARP`, `JOIN`, `REVIVE`, `VS`, `STARTS`, `WIN`, `OPENING`, `KOBUN` … |
| 4 | `W-comp` | weapon compare/collection page (`0x080082F0`) |
| 5 | `S-comp` | shield compare/collection page (`0x080082F0`) |
| 6 | `Sound` | sound/sound-test page (`0x08008584`) |

### 6.2 Key masks (as read at 0x03002564)

`A=1, B=2, Select=4, Start=8, Right=0x10, Left=0x20, Up=0x40, Down=0x80, R=0x100, L=0x200`
(active-high after `~KEYINPUT & 0x3FF`). The debug gate tests mask `4` — **Select**, not B.

### 6.3 Save header (retail save produced by `Diary → Yes`)

```
00: 44 4f 4b 41 50 4f 4e 2d 51 00 00 00 01 00 00 00   DOKAPON-Q.....
10: 00 00 00 00 00 00 00 00 01 00 00 00 d4 f6 00 00
20: 8f 63 00 00 ...
```

## 6b. Enumeration

**Space definition.** There is no code/password space:

* `validator count = 0`: no `strcmp`/`strncmp`/`memcmp` call site compares a user-entered buffer;
  the only string compares are internal table lookups.
* `entry-screen count = 0`: no screen accepts typed characters; no alphabet/char table exists.
  A scan for any 10+ run of consecutive font codes (a keyboard row would be such a run) finds
  only the font’s own glyph-index table at `0x0807C6E8` (codes `0x20,0x21,0x22,…`), not a keypad.
* The words `PASSWORD`, `CHEAT`, `CODE`, `DEBUG`, `BONUS` occur **0 times** anywhere in the ROM
  under the font encoding (§6b string space).
* Therefore the representable value count for a hypothetical typed code is **0**, and the
  “novel code” requirement has no object. The novel artifacts delivered instead are the text
  encoding (§5.2) and the previously unreported debug menu + gate constant (§6b menu space).

**String space searched.** Whole image decoded at 16-bit alignment = **4,194,304 words /
10,428 strings (`strings -n 4`)**. Case-insensitive counts over the decoded stream:

| token | hits | notes |
|---|---:|---|
| `password` | 0 | none |
| `cheat` | 0 | none |
| `debug` | 0 | none |
| `code` | 0 | none |
| `bonus` | 0 | none |
| `secret` | 1 | dialogue: “keep this a secret from Her Highness Vira” |
| `unlock` | 1 | dialogue: “I thought I unlocked it before” (a door) |
| `hidden` | 1 | monster/character description |
| `sound` | 3 | “Sound” debug label, “sound fun” dialogue ×2 |
| `pass` | 14 | all inside `passed`/`passenger`-type words; none is a password prompt |
| `clear` | 2 | “clearing some”, “clear the obstacles” |

**Button space.** All 10 masks and their complements were scanned as `u16` runs across the
whole image. No run of ≥4 consecutive button masks exists in executable code; the only ≥4 runs
are script/opcode data at `0x072BA0+` (values `0x001 0x010 0x002 0x004`), not key comparisons.
Title-screen matrix (each held 1.2 s, frame-diff vs baseline): `Select` 9,432 px (the blinking
`PRESS START` text — no state change), `L+R` 0 px, `L+R+Start`, `A+B+Start+Select`, `Up+Down`,
`L+R+Select`, `hold B`, `Start+Select`, `A+Start` → all either the normal menu opening or no
change. At the main menu, `A`/`B`/`Select`/`L`/`R` on each of the three items produced only the
normal actions (load, new game, delete prompt, cancel).

**Menu space (hidden screen), enumerated.** Entered via `PC = 0x08007A1D` after the gate flag was
set to `0x6264` in the save header (instrumentation). Observed screens:

1. Category list with 7 rows (labels above); cursor moves with Up/Down.
2. `Right` opens the selected page; the Item page shows the index counter `1/190` and item rows
   (`Recover1`, `Recover2`, `Energy1`, …). Item names come from `0x080A89D4`
   (`Recover1 Recover2 Energy1 Energy2 Revival Compass Homer Antidote CurseOff Light Up Fizzade
   CureAll Store.It Stronger Harder Speeder …`) through the 12-byte record table at `0x080B78C0`.
3. `BackSpace`/`B` returns to the category list; `Left` also returns.

**Bounds proven by rejection.**

* Retail save (`0x03004C60+0x0A == 0`): no combination opens the debug menu; the `0x08007334`
  breakpoint never fires.
* Patched save (`= 0x6264`): the flag branch is taken (breakpoint at `0x080071E6`, `r0 = 0x6264`),
  the `"US VERSION"` label path is entered, yet `A/B/Select/L/R/Start` on all three menu items
  still fails to fire `0x08007334`. This bounds the gate to two conjuncts (flag **and** internal
  state 1) and shows the second conjunct is not reachable from retail input.
* Entering a value other than `0`/`0x6264` is rejected by `0x08006574`, which rewrites the
  halfword to 0 at boot (sanitizer at `0x080065D2`).

## 7. Validation evidence

**Observed** (emulator, screenshots on disk in the work directory):

* title, main menu, file select, intro dialogues, field HUD, pause tabs, system submenu,
  `Diary` save prompt, `Flash` toggle, `Mss` speed, `Album` (`W-weapons/Shields/Monsters`,
  “Display weapon guide”), `Skill` (“List of weapon skills”);
* debug menu category list and Item page `1/190` after the debugger jump;
* the retail save file written by `Diary → Yes` (`DOKAPON-Q` header, 32 KiB);
* the `0x6264` flag present at `0x03004C60+0x0A` in an extracted mGBA savestate;
* breakpoint at `0x080071E6` with `r0 = 0x6264` after the gate flag was patched in.

**Derived** (from disassembly, byte-verified):

* key state layout and mask values (`0x080008DC`);
* text encoding and control codes (verified by decoding menu strings whose on-screen text was
  read by OCR/screenshots);
* save-header layout and the `0x6264` allow-list (`0x08006574`);
* single call edge into the debug menu (`0x08007334 → 0x08007A1C`) and single caller of the menu
  handler (`0x08003260 → 0x08007154`);
* zero password/cheat/debug strings under the font encoding.

**Inferred**:

* the purpose of each debug page beyond Item (the renderers exist and the page labels are in ROM,
  but only the Item page and the category list were displayed);
* that `0x6264` is a QA/debug-save marker rather than a gameplay flag — supported by the boot
  sanitizer allow-list and the absence of any writer, not by a documented QA build.

## 8. Unknowns

* The full 190-entry Item page was not transcribed; only the counter and the first rows were read
  on screen. Names are decodable from `0x080A89D4` / `0x080B78C0` for a follow-up pass.
* Effects of activating an entry (A) on each debug page were not exercised; the menu was reached
  only by debugger jump, so its own input loop state was not the in-game one.
* Whether the Japanese/debug build shipped a save with `0x6264` at header `+0x0A`; no such save
  or build was available.
* Exact meaning of the `0x9000` and `0x8301` text tags (layout/colour) beyond “inline markup”.

## 9. Tooling

* `mgba` 0.10.2 SDL, `Xvfb :345`, `openbox`, `xdotool`, `import`/`convert`, `tesseract`.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`.
* Python 3 + Capstone 5.0.7; custom decoders: `dec3.py` (text), `p0.py` (header),
  `mask.c` (button-mask scan), `ctl*.py` (mGBA CLI-debugger driver over a pty).
* mGBA savestate reader: PNG `gbAs` chunk → zlib → 397,312-byte state; IWRAM at `0x19000`,
  EWRAM at `0x21000`.

## 10. Legal note

No ROM, graphics, audio, or extracted text is redistributed. Only hashes, addresses, algorithms
and short UI labels needed to identify screens are reported.
