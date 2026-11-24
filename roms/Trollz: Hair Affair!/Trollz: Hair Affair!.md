# Trollz: Hair Affair! (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Item | Value |
|---|---|
| File | `Trollz: Hair Affair!.gba` |
| Size | 8,388,608 bytes (0x800000) |
| Header title | `TROLLZHAIRAF` |
| Game code | `BT6E` (AGB-BT6E-USA) |
| Maker | `41` (Ubisoft) |
| Version | 0; complement byte 0x49; header checksum 0 |
| Entry word | `0xEA00002E` — stock branch to 0x080000C0, single header, no cracktro/trainer |
| MD5 | `243cd8ce513da13eeed632a3a8d3d153` |
| SHA-1 | `5ab8bbede98a46bc24d6532f837482c3bbff9762` |
| SHA-256 | `338418cdf2e7daf58db0de5c5be352e76ef79647c9bc04bb3a767d81bd02130f` |

**Phase 0:** one Nintendo-logo header at file 0, entry is the retail branch, complement
is valid. No scene patch or appended trainer was found.

## 2. Executive summary

There are **two distinct code-related surfaces**, and only one is a cheat:

1. **Trollars Codes (not a cheat).** Options → "Trollars Codes" is a *display-only*
   screen for 16 web-redemption codes earned by story/score milestones. The ROM stores
   them ROT13-and-digit-shift obfuscated; a decode routine renders them as `Code: %s`.
   There is no input widget, no comparison against the table and no validator, so these
   are not in-game cheats.

2. **A real, unpublished developer button code.** On the **Options** screen, entering
   the eight shoulder presses **L, R, L, L, R, L, R, R** and then **Select** opens a
   hidden "CHEAT MODE:" menu (build 5706) with two entries: a **Normal / All Unlocked**
   toggle and **Story Jump** (five scenes). The matcher is a strict state machine with
   reset-on-mismatch; the ninth press selects the action (A/B/Select branches exist in
   code, but A and B are consumed by menu navigation, so only Select is reachable from
   the retail UI). The code is absent from every published list checked (3rd party cheat indexes, fan wikis — no GBA codes are published for this title).

The novel code was typed on the real screen in mGBA and confirmed by screenshot and by
RAM read (gate byte `0x0200884b` = 1). All Unlocked was observed to raise the Boom Room
level selector to Level 9.

## 3. How to reproduce

* mGBA 0.10.5 under Xvfb `:316`, `-3`, `SDL_AUDIODRIVER=dummy`; openbox window manager.
* Keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad = arrows.
  Hold ~100 ms with ~300–450 ms between presses.
* Path: boot → legal screen (A) → DAM logo → "Enter Name" (type any name, choose OK) →
  difficulty (A) → help screens (A × several) → **Main Menu**.
* Select **Options** (item 4) and wait for the screen to settle.
* Enter `L R L L R L R R` as eight separate presses, then press **Select**.
  The "CHEAT MODE:" menu appears immediately.
  * `Right`/`Left` on "Normal, All Unlocked" toggles the mode (observed "All Unlocked").
  * `Down` then `A` on "Story Jump" opens a five-entry list: Story Intro, First Day Back,
    Second Day Back, Third Day Back, Ending.
  * `B` backs out.
* With All Unlocked set, Boom Room → Watch the Hair → Level was advanced to **9**
  (observed). The un-modded selector is documented in-game as story-progress limited;
  its exact Normal-mode cap was not measured in this session.
* Rejections (all leave the gate byte at 0): Select alone; only seven prefix presses
  then Select; full prefix then **Start**.

## 4. Address map

File offset = ROM address − 0x08000000.

| Address | Meaning |
|---|---|
| `0x08005BC` | Joypad reader: `held = ~KEYINPUT & 0x3FF` → `0x03001074`; `pressed = held & ~old` → `0x03001076` |
| `0x03001074 / 0x03001076` | Active-high held buttons / newly-pressed edges (`A=1,B=2,Select=4,Start=8,Right=0x10,Left=0x20,Up=0x40,Down=0x80,R=0x100,L=0x200`) |
| `0x0807C1F04` | ROM source of the 8-entry button mask table + `0x0000` terminator |
| `0x03006594` | IWRAM runtime copy of that table (8 × u16) |
| `0x02008844` | Cheat state struct: `+0` u32 table pointer (`0x03006594`), `+4` progress index, `+5` flag from A, `+6` flag from B, `+7` flag from Select (**cheat-menu gate**) |
| `0x08024DB0` | Button-code matcher / ninth-press action dispatcher |
| `0x08024E1C` | Reset routine: installs table pointer and clears index/flags |
| `0x08007764` | `callback_cheat_options` — Options `onvblank`: runs matcher; if `+7` set, pushes `cheat.xml` |
| `0x08007758` | `callback_cheat_options_init` — Options `onpaint`: calls reset |
| `0x080074C8 / 0x08005D04` | `callback_boomroom_cheatmode` / `..._getcheatmode` (All Unlocked toggle) |
| `0x030014DC / 0x03006110` | Cheat-mode active word (1) / mode word (5 = Normal, 0x0D = All Unlocked) |
| `0x080D01A0` | `cheat.xml` menu definition (CHEAT MODE, Normal/All Unlocked, Story Jump) |
| `0x080563C0 / 0x080563DC` | Callback name strings; paired function-address table at `0x08054C10`ff |
| `0x08053D48` | 16-entry reverse-ordered pointer table into the Trollars strings |
| `0x08053D88`–`0x08053E88` | 16 Trollars strings, 16-byte stride (12 chars + 4 zero bytes) |
| `0x08053E88` | u32 rewards: 500, then (25,75,100) × 5, then 0 terminator |
| `0x080732F8 / 0x080733F4` | The 16 unlock-condition strings |
| `0x080249BC` | Trollars display decoder (ROT13 letters; digits ±5) |
| `0x08053EDC` | `Code: %s` format string |

## 5. Algorithm

`0x08024DB0` (observed/disassembled, Thumb):

```c
pressed = *(u16*)0x03001076;          // edge-triggered, active-high
if (!pressed) return;
s = (struct { u32 *table; u8 index, flagA, flagB, flagCheat; }*)0x02008844;

if (s->index > 7) {                   // 9th press: action dispatch
    if (pressed & 0x001) s->flagA = 1;                 // A
    if (pressed & 0x002) { s->flagB = 1; f(3); }       // B -> 0x0801B30C(3)
    if (pressed & 0x004) s->flagCheat = 1;             // Select -> cheat menu
    s->index = 0;
    return;
}
u16 expected = s->table[s->index];    // 8-entry table
s->index = (expected & pressed) ? s->index + 1 : 0;   // mismatch resets progress
```

The Options screen's `onvblank` handler (`0x08007764`) calls this every frame and, when
`flagCheat` is set, pushes `cheat.xml`. The `onpaint` handler resets the struct, so the
gate is re-armed each visit to Options.

Trollars display transform (`0x080249BC`): for each of 12 characters,
`A–M/a–m → +13`, `N–Z/n–z → −13`, digits `0–4 → +5`, `5–9 → −5` (an involution).
The stored strings are the obfuscated form; the player-facing code is the transform.

## 6. Tables

**Button prefix** (u16 masks at `0x0807C1F04`, copied to `0x03006594`):

| index | mask | button |
|---:|---:|---|
| 0 | 0x0200 | L |
| 1 | 0x0100 | R |
| 2 | 0x0200 | L |
| 3 | 0x0200 | L |
| 4 | 0x0100 | R |
| 5 | 0x0200 | L |
| 6 | 0x0100 | R |
| 7 | 0x0100 | R |

**Ninth-press dispatch:** A → flag `+5`; B → flag `+6` (plus call `0x0801B30C(3)`);
Select → flag `+7` = open cheat menu. A and B are consumed by Options menu navigation
before the matcher sees them; Start dispatches but matches no branch.

**Cheat menu (cheat.xml):** `CHEAT MODE:` label; textselect `Normal, All Unlocked`
(`callback_boomroom_getcheatmode` / `callback_boomroom_cheatmode`); `Story Jump` →
`story_jump.xml` with Story Intro / First Day Back / Second Day Back / Third Day Back /
Ending; back arrow pops.

**Trollars codes (16 records).** These are *output* codes for www.trollz.com. The
"stored" column is the ROM string at `0x08053D88+16*i`; the "displayed" column is the
decoded string the game renders (derived from `0x080249BC`), paired with the condition
string and reward from `0x08053E88`.

| i | Stored | Displayed (`Code: %s`) | Condition | Trollars |
|---:|---|---|---|---:|
| 0 | `jx6sr8e46it1` | `wk1fe3r91vg6` | Finished Story Mode | 500 |
| 1 | `7dp3xl94712z` | `2qc8ky49267m` | Watch the Hair! Score 1 | 25 |
| 2 | `zn3108574370` | `ma8653029825` | Watch the Hair! Score 2 | 75 |
| 3 | `a79gj93nz146` | `n24tw48am691` | Watch the Hair! Score 3 | 100 |
| 4 | `uo344744t98e` | `hb899299g43r` | Smarty Trollz Score 1 | 25 |
| 5 | `bp1o2ne6yk47` | `oc6b7ar1lx92` | Smarty Trollz Score 2 | 75 |
| 6 | `a50z8p5nj7az` | `n05m3c0aw2nm` | Smarty Trollz Score 3 | 100 |
| 7 | `z8t3gn906yn3` | `m3g8ta451la8` | Trollz Dance Score 1 | 25 |
| 8 | `o431gb90229p` | `b986to45774c` | Trollz Dance Score 2 | 75 |
| 9 | `gq3718sz791u` | `td8263fm246h` | Trollz Dance Score 3 | 100 |
| 10 | `6ud0991d8ob4` | `1hq5446q3bo9` | Flying Spell Score 1 | 25 |
| 11 | `xn366pa585bi` | `ka811cn030ov` | Flying Spell Score 2 | 75 |
| 12 | `38qp658985yc` | `83dc103430lp` | Flying Spell Score 3 | 100 |
| 13 | `yo858s48ie68` | `lb303f93vr13` | Spell Beadz Score 1 | 25 |
| 14 | `gn490696nu43` | `ta945141ah98` | Spell Beadz Score 2 | 75 |
| 15 | `4b5ir9087cr7` | `9o0ve4532pe2` | Spell Beadz Score 3 | 100 |

(The pointer table at `0x08053D48` lists these newest-first: index 0 points at the
string stored last at `0x08053E78`.)

## 6b. Enumeration

**Space definition.** The accepted input is not a string but a button stream. The
prefix is exactly 8 presses from the 10-button GBA alphabet; matching is strict and any
mismatched press resets progress to zero. Therefore the prefix space is 10^8 = 100,000,000
possible sequences and exactly **one** is accepted. The ninth press selects among three
coded action branches (A, B, Select) out of 10 possible buttons; only Select is
reachable through the retail UI, because A/B are interpreted as menu navigation while
the Options screen is active. There is no length tolerance: a correct 8-press prefix
followed by no press leaves `index = 8` but sets no flag, and a wrong press at any point
returns `index` to 0.

The Trollars system is a closed table of exactly **16** output strings (12 characters
from `[0-9a-z]`, stored ROT13/digit-shifted). There is no input alphabet, no validator,
and no comparison against the table anywhere in the ROM; its "space" is the 16 records
above, not a generated code space.

**Novel code (not in any published list).**
`L, R, L, L, R, L, R, R, Select` typed on the Options screen. Web reconnaissance
(3rd party cheat index FAQ/cheats, 3rd party cheat indexes, fan wikis, general searches) found **no
published GBA cheat codes at all** for this title, so this sequence is unpublished.
Observed in mGBA: the "CHEAT MODE: / Normal / Story Jump / BUILD 5706" screen appears
(screenshot `cheatseq10_c.png`), and RAM `0x0200884b` reads `0x01` while the progress
index `0x02008848` returns to `0x00`.

**Bounds proven by rejection** (each tested on the Options screen with a RAM read):

| Test | RAM result | Outcome |
|---|---|---|
| Select alone | index `0x00`, all flags `0x00` | no menu |
| 7 presses (L R L L R L R) + Select | index `0x00` (progress reset on mismatch) | no menu |
| Full prefix + Start | dispatch runs, index `0x00`, no flags set | no menu |
| Full prefix + A / + B | index stays `0x08`, no flags — A/B consumed by the menu | no branch effect in UI |

**Effects enumerated.** Both menu entries were opened and walked: the Normal/All
Unlocked toggle changes `0x03006110` between `0x05` and `0x0D` (observed), and with All
Unlocked the Boom Room Watch-the-Hair level selector reaches **Level 9** (screenshot
`lvl8_c.png`). Story Jump exposes all five listed scenes (screenshot `sj1_c.png`).

## 7. Validation evidence

* **Observed (emulator/screenshots):** title/name/difficulty/main-menu/Options walk;
  Trollars Codes screen showing "Not yet unlocked" and its 16 browsable conditions;
  cheat menu appearance after the novel button code; "All Unlocked" text; Story Jump
  screen and all five entries; Level 9 in Boom Room; rejection outcomes above.
* **Observed (GDB memory reads):** `0x02008844` = `0x03006594` table pointer,
  `0x02008848` progress index 0→8→0, `0x0200884b` = 1 after the Select dispatch,
  `0x03006594` table contents, `0x030014DC` = 1 and `0x03006110` = 5/0x0D.
* **Derived (disassembly):** matcher pseudocode, reset-on-mismatch semantics, A/B
  dispatch branches, `0x08024E1C` reset, `cheat.xml` control list and callbacks,
  Trollars decode transform, 16-record table and reward values.
* **Inferred (not exercised):** the exact visible effect of the A (`+5`) and B (`+6`)
  flags, because their dispatch keys are swallowed by menu navigation; call
  `0x0801B30C(3)` was not observed running in-game.

## 8. Unknowns

* Whether any controller state (e.g. holding a key across a menu transition) can make
  the A/B dispatch branches reachable; they are present in code but were not reached
  from the retail Options screen.
* The Trollars codes could not be observed unlocked in the emulator (All Unlocked does
  not unlock them), so the 16 displayed strings are derived from the decoder rather
  than read off the screen.
* The effect of `0x0801B30C(3)` on the B branch, and the persistent meaning of the
  `+5`/`+6` flags, were not pinned down.

## 9. Tooling

`arm-none-eabi-objdump -M force-thumb`, Capstone (small range disassembler `dis.py`),
GDB stub via `gdb-multiarch` on mGBA port 2345 (interrupted for each RAM read),
Python 3 for string/pointer/literal scans, `xdotool` XTEST input, `scrot` + Pillow for
cropped screenshots. Work directory: `/tmp/trollz`. No GameShark, CodeBreaker
or Action Replay codes were used or reported.

**Legal note:** no ROM image or copyrighted assets are redistributed; only addresses,
algorithms, hashes and original observations are published.
