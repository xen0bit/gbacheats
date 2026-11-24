# Duke Nukem Advance (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Duke Nukem Advance/Duke Nukem Advance.gba` |
| Size | 8,388,608 bytes (`0x00800000`) |
| Header title | `DUKE NUKEM A` |
| Game code / maker | `AD9E` / `54` (Torus Games), version `0x00` |
| Entry word | `0xEA000030` → stock crt0 at `0x080000C8` |
| Header complement / checksum | `0xBB` / `0x0000` (one's complement of bytes `0xA0..0xBC` computes `0xD3`; header appears rebuilt, but no cracktro/trainer found) |
| MD5 | `dfca43fb18b5ee86b3ecab2631862d6f` |
| SHA-1 | `ef9d2c9910a95e456447ee7288ae5aa659b33ad2` |
| SHA-256 | `f21ccca4632293e409412cf29d5322c136871bf42a03b15b99d4f7dc6b3fab76` |

**Embedded-header scan:** scanning the whole image for the 156-byte Nintendo logo
yields exactly one header, at file offset `0x0`. No multiboot stub, second game,
appended trainer, or patched entry point was found. First 4 KiB is ordinary ARM
crt0. This is the retail single-game image.

## 2. Executive summary

The only developer-intended cheat system in this ROM is a **button code**, not a
typed password. While in the in-game pause menu, hold **L** and press
**Left, Up, A, Up, Left, A, Start, Select** (the "LUAU LASS" sequence hinted in
an in-game radio message). This opens a hidden **CHEATS** screen with a 19-entry
level selector and four toggles: Unlimited Ammo, God Mode, No Clipping, Full
Weapons.

The validator was recovered completely:

* one hard-coded table of **eight** `u16` active-high key masks at ROM
  `0x08030044`;
* an exact-length gate: the code completes only when an 8th correct press is
  registered (`cmp r0,#8`);
* a continuous **L-held** requirement — releasing L between presses resets the
  progress byte;
* a wrong press also resets the progress byte;
* exactly **one** action branch: call `0x080145EC(18)`, which switches to screen
  ID 18 (the CHEATS screen);
* the validator is installed as the update handler for exactly **two** screen
  states (two Thumb pointers in the screen dispatch table), both in-game pause
  variants. The map screen and title screen do not run it.

The published 3rd party cheat index code is correct. The "invincibility" title-screen
code found on the Duke Nukem Wiki (`Up,Down,Down,Left,Right,Left,Up,Up`) is
**not** from this SKU: its mask sequence does not occur anywhere in the ROM and
entering it on the title screen has no effect.

A full enumeration of the code space was performed (§6b), including two novel
undocumented input sequences that the game accepts, and four independent
rejection tests that prove the bounds.

## 3. How to reproduce

* Emulator: mGBA (`mgba -3`, SDL build), Xvfb `:318`, `SDL_AUDIODRIVER=dummy`.
* Keymap (mGBA SDL defaults): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
  Select=`BackSpace`, D-pad=arrow keys. Hold keys 80–150 ms.
* Boot: legal screen → A → title → Start → long intro; **press Start during the
  credits to skip directly to the Difficulty screen**. Select a difficulty,
  press A, skip the following comic with A/fast-forward (Tab) to reach level 1A.
* Press Start to pause (MAP / RESTART / OPTIONS / QUIT), then hold `a` (L) for
  the whole sequence and tap: `Left, Up, x, Up, Left, x, Return, BackSpace`.
  Release L. The CHEATS screen appears.
* On the CHEATS screen: Up/Down choose a row; Left/Right cycle the level or
  toggle a cheat; `A` does **not** toggle anything.
* Savestates (Shift+F1…F9 save, F1…F9 load) were taken at the pause menu
  (slot 4) and at the CHEATS screen (slot 2); the raw `gbAs` chunk
  (`zlib.decompress`) maps IWRAM at raw offset `0x19000`, so IWRAM address
  `0x03000136` is raw byte `0x19136`. That byte is the code-progress oracle.

## 4. Address map

| Item | File offset | ROM / RAM address | Evidence |
|---|---:|---|---|
| Button mask table (8 × u16 LE) | `0x30044` | `0x08030044` | literal pointer at `0x0801164C`; bytes `20 00 40 00 01 00 40 00 20 00 01 00 08 00 04 00` |
| Validator function (Thumb) | `0x115D8` | `0x080115D8` | disassembly; installed as handler via Thumb pointer `0x080115D9` at `0x0803072C` and `0x08030754` |
| Progress byte (oracle) | — | `0x03000136` (IWRAM) | `ldrb`/`strb` in validator; observed 0→1→…→8 |
| Key-state word A | — | `0x03000FE8` (IWRAM) | `ldrh` at `0x080115E2`; L-bit test resets progress |
| Key-state word B | — | `0x03000FE4` (IWRAM) | `ldrh` at `0x08011600`; second L gate; `r3 = [FE8] & [FE4]` is the press combo |
| Gate flag pointer | — | `0x03001284` (IWRAM) | `ldr r0,[ptr]`, `cmp r0,#0` at `0x080115F6`; nonzero skips the cheat check |
| Secondary flag byte | — | `0x030011AC` (IWRAM) | `strb 0` on Right-hold path at `0x0801167A` |
| Cheat-menu open action | `0x145EC` | `0x080145EC` | `movs r0,#18; bl 0x080145EC` at `0x0801634/0x0801636` |
| In-game hint string ("LUAU LASS") | `0x733986` | `0x08733986` | `strings -t x`; "LUAU" literal at file `0x7339D8` |
| Secret discovery strings | `0x7314AE` … `0x736014` | `0x087314AE` … | level secrets, not cheat codes |

## 5. Algorithm

Derived from Thumb disassembly of `0x080115D8`:

```c
// r4 = r0 (screen object); if (r4 == 0) return;
u16 *kfe8 = (u16*)0x03000FE8;   // key-state word A
u16 *kfe4 = (u16*)0x03000FE4;   // key-state word B
u8  *progress = (u8*)0x03000136;
const u16 *table = (const u16*)0x08030044;

if (!(*kfe8 & 0x200)) *progress = 0;          // L released -> reset
if (*(u32**)0x03001284) goto normal_handler;  // gate flag
if (!(*kfe4 & 0x200)) goto normal_handler;    // L not in second word

u16 combo = *kfe8 & *kfe4;                    // current press combination
if (combo) {
    u16 expected = table[*progress];
    if (expected & combo) {                   // at least the expected bit present
        u8 next = *progress + 1;
        *progress = next;
        if (next == 8) open_screen(18);       // CHEATS screen
    } else {
        *progress = 0;                        // wrong press -> reset
    }
}
... normal pause-menu handling ...
```

Two details make the observed behaviour stricter than the bare `AND`:

* the input state is edge-triggered (a press is accepted for one frame only),
  so two buttons pressed on the **same** frame do not both register — a paired
  variant (`Left+Down`, `Up+Right`, …) was rejected with progress 0;
* after completion the progress byte stays at 8 for as long as the CHEATS
  screen is active; re-entering the pause menu requires a fresh code.

Confidence: **derived** (instruction sequence) for the control flow and
addresses; **inferred** for the exact held-vs-edge semantics of the two
`0x03000FEx` words (the writer was not disassembled), but the input behaviour
was confirmed empirically.

## 6. Tables

**6.1 Button mask table, ROM `0x08030044`** (active-high GBA key bits:
A=1, B=2, Select=4, Start=8, Right=0x10, Left=0x20, Up=0x40, Down=0x80,
R=0x100, L=0x200):

| Index | u16 | Button | "LUAU LASS" letter |
|---:|---:|---|---|
| 0 | `0x0020` | Left | (leading "L" is the held shoulder) |
| 1 | `0x0040` | Up | U |
| 2 | `0x0001` | A | A |
| 3 | `0x0040` | Up | U |
| 4 | `0x0020` | Left | L |
| 5 | `0x0001` | A | A |
| 6 | `0x0008` | Start | S |
| 7 | `0x0004` | Select | S |

The next two words in ROM, `0x08030054 = 0x0006` (B+Select) and
`0x08030058 = 0x0004` (Select), are **not** part of this sequence: the
validator terminates at index 8 and never reads beyond `0x08030052`. They
belong to a different data structure (a pointer to `0x08030054` occurs inside a
data blob at `0x08030628`).

**6.2 CHEATS screen rows (observed):**

| Row | Values |
|---|---|
| LEVEL | 19 selectable levels; wraps with period 19; shown as previous/current/next (e.g. `4H / 1A / 1B`) |
| Unlimited Ammo | Off ↔ On |
| God Mode | Off ↔ On |
| No Clipping | Off ↔ On |
| Full Weapons | Off ↔ On |

All four toggles were set On simultaneously and observed in the menu. Pause
menu rows are MAP / RESTART / OPTIONS / QUIT; OPTIONS contains EDIT CONTROL
SETTINGS, AUTO WEAPON SWITCH, CROSS HAIR TYPE, SOUND FX, MUSIC, GAMMA — no
hidden entry.

**6.3 Published codes checked against this ROM:**

| Source | Code | ROM verification | In-game result |
|---|---|---|---|
| 3rd party cheat indexes | Pause + hold L + Left,Up,A,Up,Left,A,Start,Select | literal table at `0x08030044` matches all 8 masks | **accepted**; CHEATS screen opens |
| Duke Nukem Wiki (title-screen "Invincibility" Up,Down,Down,Left,Right,Left,Up,Up) | 8 presses, no L | mask sequence absent from entire 8 MiB; no validator on title screen | **rejected**: progress stays 0, no visible effect |
| 3rd party cheat index FAQ (Beat the Clock timer exploit) | not a button/password code | N/A | out of scope (in-game glitch), recorded for completeness |

## 6b. Enumeration

**Space definition.** The code space is a *fixed-length button sequence*, not a
checksummed password:

* alphabet = the 10 GBA inputs (A, B, Select, Start, L, R, D-pad ×4);
* length = **exactly 8** presses (`cmp r0,#8`), no short/long variants;
* one additional continuous condition: the L shoulder must be held throughout;
* nominal input space 10^8 = 100,000,000 sequences; accepted set has
  **exactly one member**, the table at `0x08030044`;
* one action branch: `open_screen(18)`;
* two screen entry points (two validator handler pointers in the dispatch
  table), both in-game pause states; no title/map/gameplay entry.

**Oracle method (§16.19).** The progress byte at `0x03000136` is the ROM's own
accept/reject oracle. By saving a savestate after each keypress and reading that
byte from the decompressed `gbAs` chunk, every candidate input was classified
without relying on a screenshot. The published sequence produced
`1,2,3,4,5,6,7,8` and opened the CHEATS screen.

**Novel codes (absent from every published list), accepted in-game:**

1. **Leading-press variant:** hold L, press **Down** first, then
   Left, Up, A, Up, Left, A, Start, Select. The extra leading press is rejected
   at index 0 and resets to 0; the following eight presses then advance the
   oracle to **8** and the CHEATS screen opens. Screenshot: `test_novel_lead.png`.
2. **Extra-held-shoulder variant:** hold **L+R** (R is ignored by the gate) and
   enter the published eight presses. Oracle = **8**; CHEATS screen opens.
   (R being held is not part of any published code.)

**Bounds proven by rejection:**

| Test | Oracle after sequence | Result |
|---|---:|---|
| Wrong 3rd press (B instead of A) | 0 | rejected — wrong press resets progress |
| Release L after press 4, then re-hold | 0 | rejected — L must be held continuously |
| No L held at all | 0 | rejected — L gate |
| Same code entered on MAP screen | 0 | rejected — validator not installed there |
| Title-screen "invincibility" code | 0 | rejected — mask sequence not in ROM |
| Two buttons pressed on the same frame per step | 0 | rejected — edge-triggered single-button matcher |
| 28 consecutive Right presses on LEVEL row | level labels repeat at presses 0 and 19 | bounds the level selector to exactly 19 entries |

The accepted set is therefore closed: one 8-press sequence, one gate, one
action; no second/third code exists in the table or in the validator's branches.

## 7. Validation evidence

* **Observed** (emulator): title → difficulty → gameplay → pause → CHEATS screen;
  all five rows and all four ON toggles; level labels wrap after 19 steps;
  novel sequences open the menu; rejection tests do not.
* **Observed** (RAM): progress byte `0x03000136` = 0 before code, 1…8 after
  each correct press, 0 after each rejection; = 8 for both novel variants.
* **Derived** (disassembly): table contents, 8-entry bound, L gate, wrong-press
  reset, action `open_screen(18)`, two handler-table slots.
* **Inferred**: exact held/edge semantics of `0x03000FE4/FE8`; purpose of the
  extra `0x08030054` data pair; whether the cheat flags persist into SRAM
  (the `.sav` was all `0xFF` after the session).

## 8. Unknowns

* The writer of the two `0x03000FEx` key-state words was not disassembled; the
  "edge-triggered" explanation of the paired-button rejection is inferred from
  behaviour, not from that routine.
* The `0x08030054/0x08030058` word pair (`B+Select`, `Select`) is not consumed
  by this validator; a possible second consumer exists in a data blob but was
  not followed. No in-game effect was observed for it.
* Cheat flags' exact RAM addresses and SRAM persistence were not isolated;
  a 2,445-byte savestate diff contained too much runtime noise to attribute
  individual flag bytes. Menu ON/OFF state is visual evidence only.
* No typed-password screen exists in this SKU (no text-entry UI was found on
  any of the walked screens), so no password alphabet/checksum applies.

## 9. Tooling

* `mgba -3` (SDL) under `Xvfb :318` + `openbox`; `xdotool` XTEST input;
  `import -window root` / `scrot` screenshots; Tab = fast-forward.
* Python helpers in `/tmp/duke/`: `gba.py` (input), `ss.py` (zlib
  decompress of mGBA `gbAs` savestate chunk; IWRAM at raw `0x19000`),
  `findmask.py` (key-mask literal scan), `code_tests.py` (oracle-driven
  accept/reject trials).
* `arm-none-eabi-objdump -M force-thumb` for validator disassembly; Capstone
  5.0.7 available. Web sources: 3rd party cheat indexes via `web.archive.org`
  (direct fetches 403). Fetched pages were treated strictly as data.
* No ROM or copyrighted asset is redistributed; only addresses, hashes,
  algorithms and original test procedures are published here.
