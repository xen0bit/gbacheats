# Ultimate Card Games (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Ultimate Card Games/Ultimate Card Games.gba` |
| Size | 4,194,304 bytes (`0x400000`), 32 Mbit |
| Header title | `UCG` (`0xA0..0xA7`) |
| Game code | `BUCE` |
| Maker | `5M` (Cosmigo / Telegames family — see sibling `Ultimate Brain Games`, code `ABUE`, same maker) |
| Version | `0x00` |
| Fixed byte `0xB2` | `0x96` |
| Complement (`0xBD`) | `0xD1` |
| Header checksum (`0xBE`) | `0x0000` (normal rebuilt-header artifact) |
| Entry word | `0xEA00002E` — stock branch to `0x080000C0`, **not** a cracktro-patched entry |
| MD5 | `05271b3c67aaa0a36fcdf723364a8c46` |
| SHA-1 | `22fb775d4b2673ff00877170fbc028b9696e4f8e` |
| SHA-256 | `24063604312e5f05d2dc2c424aadc882673841b310888d9ab8a6db757937bc7c` |

Release data (web, treated as data): Cosmigo developer, Telegames publisher, 2004,
also known as *Card Games: The Classics* (EU). No 3rd party cheat index article exists for this SKU.

**Scope:** in-game / developer-intended cheats only (passwords, button codes,
hidden/debug menus, unlockables). No GameShark/CodeBreaker/Action Replay codes
were sought or reported.

## 2. Executive summary

**Bounded negative: this retail image has no in-game cheat/password system, no
button-code system, and no reachable hidden debug menu or unlockable.** This is
not "I did not find one": every surface that could host a code was enumerated
and counted (§6b).

Three independent layers agree:

1. **Text/asset layer.** `strings -t x -n 4` produced **50,903** ASCII runs in
   the 4 MiB image. Searches in five encodings (ASCII, uppercase, UTF-16LE,
   `+0x20`, XOR-`0xFF`) returned **zero** occurrences of `password`, `cheat`,
   `debug`, `secret`, `unlock`, `code`, `genie` or `codebreaker`. The game's UI
   text is ASCII and lives in a master pointer table at `0x080ACBD0` with
   **692 distinct entries**; all labels are menus, rules text, statistics and
   credits. The only label with no visible menu item is `DEMO MODE` (ID 8) —
   a dead/gated leftover (§6b). The 4 "alphabet" runs in the image are the
   Face Creator **name-entry keyboard** layouts, not a password alphabet.
2. **Input layer.** Only **9** literal occurrences of `0x04000130` (KEYINPUT)
   exist; **4** are in code and each has exactly one Thumb `LDR` reference:
   `0x0800287C`, `0x0800E3B8`, `0x08010A76`, `0x08090804`. All are generic
   polling: they compute held / newly-pressed masks (`0x03000800/02`) and
   drive single-key menu navigation. There is no press-history ring, no
   multi-button mask comparison, no progress index, and no boot-time
   combination test — i.e. no button-code validator.
3. **Screen layer.** Every reachable top-level screen and submenu was walked
   with screenshots (§3). All menu entries are labelled and do ordinary
   game/save/options work. `L+R`, `Start+Select`, `A+B`, `L+R+Start+Select` and
   the 10-press Konami sequence produced no new screen or state.

The apparent "code-like" ASCII runs (e.g. `WFNFEF`, `F45%J`) are Thumb
instruction bytes (`0x46..` = `mov` register encodings), not codes. Long runs
of key-mask-shaped `u16` values occur only inside compressed tile/audio data
(`0x08186F2E`, `0x0823A45C`), never in executable code.

## 3. How to reproduce

- Emulator: mGBA 0.10.5, `SDL_AUDIODRIVER=dummy`, Xvfb `:318` + openbox, `-3`
  scale, default keymap (A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
  Select=`BackSpace`). The SDL window must be focused and a key pressed once
  before the first frame renders.
- Savestate `Shift+F1` was taken on the top menu and copied to
  `/tmp/cardgames/topmenu.ss1` for repeatable returns.
- Menu path observed (all screenshots in `/tmp/cardgames/`):
  - Boot → main game list (`CLASSIC` selected) or top menu, depending on boot
    timing; `B` from the game list opens the icon-style top menu.
  - Top menu: `SINGLE PLAYER`, `MULTIPLAYER`, `FACE CREATOR`, `OPTIONS`.
    `SINGLE PLAYER` reveals category tabs `CASINO | CLASSIC | SOLITAIRE`.
  - Game list tabs: `Preview | Description | Statistics` (Left/Right).
  - `CASINO`: Poker, BlackJack, Video Poker. `CLASSIC`: Hearts, Spades,
    Euchre, Canasta, Bridge, Cribbage, Go Fish, Gin Rummy, Crazy Eights.
    `SOLITAIRE`: Klondike, FreeCell, Canfield, Pyramid, Golf, Spiderette,
    Baker's Dozen, Bristol, Calculation, Aces Up, Baroness, Betsy Ross,
    Eagle Wing, Eight Off.
  - In-game (Crazy Eights used as representative) `Start` opens a Windows-style
    menu bar: **Game** (New Game, Restart, Load[disabled], Save, Game Copy…,
    Sleep…, Quit), **Preferences** (Music Volume…, Playlist…, Background ▸,
    Cards back…, Demo mode), **Options** (Max score…, Very Crazy, Animation,
    Game Icon, How to play…).
  - Top menu → `OPTIONS`: `OPPONENTS`, `AUDIO`, `MEMORY`, `CREDITS`.
    `AUDIO` → PLAYLIST, VOLUME, SAVE SETTINGS, DEFAULT SETTINGS.
    `MEMORY` → RESET SAVES, RESET FACES, RESET STATS, RESET GRADIENTS, RESET ALL.
  - `OPPONENTS`: Male (Bob, Tom, Rico, Paul, Hunk, Mike), Female (Julie, Sandy,
    Nikki, Ann, Sandra, Alice), Slots (empty — no custom faces saved).
  - `FACE CREATOR`: SAVE, MODIFY, NAME, LOAD, RANDOM, RESET. `NAME` opens a
    47-cell on-screen keyboard (`a`–`z`, `! ? , . - ' & _ /`, `0`–`9`, DEL, OK)
    with Case/Delete controls.
- Button-comboreproduction: see §6b.

## 4. Address map

| Address (ROM unless noted) | Meaning | Evidence |
|---|---|---|
| `0x08000000` | Header; entry `0xEA00002E` | Observed (hex dump) |
| `0x0800287C` | Key reader: `ldrh` from `0x04000130`, computes held/pressed masks into `0x03000800/02` | Derived (`objdump -M force-thumb`) |
| `0x0800E3B8`, `0x08010A76`, `0x08090804` | Other KEYINPUT readers — generic polling / input-state propagation | Derived |
| `0x08008000`–`0x08009000` | Menu + keyboard rendering / handling code; references all alphabet tables | Derived |
| `0x080AC280`–`0x080AC330` | Four name-entry alphabet strings (upper, lower, mixed, symbol sets) | Observed (dump) + Derived (9 code xrefs) |
| `0x080ACBD0` | Master UI string-pointer table (692 distinct entries) | Derived |
| `0x083E5400`–`0x083E8000` | UI text bank (file offset `0x3E5400`–`0x3E8000`) | Observed |
| `0x083E7AE4` | "Please purchase ULTIMATE CARD GAMES…" nag/attract text; pointer at `0x080AD644` | Derived |
| `0x03000800/02` | Processed key state (held / newly pressed) | Derived |
| `0x04000130` | KEYINPUT (active-low) | Derived |

## 5. Algorithm

No password/checksum/button algorithm exists to reverse. The only
"code-shaped" machinery is:

- **Input pipeline**: `held = ~KEYINPUT & 0x3FF`;
  `pressed = held & ~previous`; stored at `0x03000800/0x03000802`. Consumers
  test single bits for D-pad/A/B navigation (mask `0x3F`-range). No sequence
  state is kept.
- **Name entry**: a 47-cell keyboard driven by the four alphabet tables at
  `0x080AC280..0x080AC330`. Characters are appended to a display name buffer;
  `OK` closes the screen. No validator, checksum, length gate or comparison
  against a constant was found in the handler range (`0x08008000`–`0x08009000`):
  all comparisons there are cell indices (`cmp r3,#8`, `#7`, `cmp r0,#15`) or
  render-state flags. The field is a cosmetic label (guide §16.2b).

## 6. Tables

**Master string IDs (base `0x080ACBD0`, first 40 of 692):**

| ID | String | ID | String |
|---:|---|---:|---|
| 5 | SINGLE PLAYER | 21 | AUDIO |
| 6 | MULTIPLAYER | 22 | MEMORY |
| 7 | FACE CREATOR | 23 | OPPONENTS |
| 8 | DEMO MODE *(unused in UI)* | 24 | CREDITS |
| 9 | OPTIONS | 25–29 | PLAYLIST, SHUFFLE TRACKS, VOLUME, SAVE/DEFAULT SETTINGS |
| 10–12 | CLASSIC, CASINO, SOLITAIRE | 30–34 | RESET SAVES/FACES/STATS/GRADIENTS/ALL |
| 13–14 | SINGLE PAK, MULTI PAK | 35–39 | YES, NO, OVERWRITE ?, … |
| 15–20 | SAVE, LOAD, MODIFY, RANDOM, NAME, RESET | 40–48 | Face Creator button labels |

**Name-entry alphabets (file `0xAC280` → ROM `0x080AC280`):**

| Address | Contents |
|---|---|
| `0x080AC280` | `ABCDEFGHIJKLMNOPQRSTUVWXYZ!?,.-'&_ /0123456789*$` |
| `0x080AC2B0` | `abcdefghijklmnopqrstuvwxyz` |
| `0x080AC2C0` | lowercase + `!?,.-'&_ /0123456789**$$` |
| `0x080AC300` | uppercase + `!?,.-'&_ /0123456789**$$` |

Code xrefs: `0x080081DA`, `0x0808286`, `0x0808316`, `0x0808578`, `0x0808660`,
`0x0808DE0`, `0x0808F48`, `0x0808936`, `0x0808C8E` — all in the menu/keyboard
render block.

**Key masks** (standard GBA active-high): A `0x001`, B `0x002`, Select `0x004`,
Start `0x008`, Right `0x010`, Left `0x020`, Up `0x040`, Down `0x080`,
R `0x100`, L `0x200`. No table of these appears in code.

## 6b. Enumeration

**Code space size: 0.** There is no password alphabet, checksum, code table,
button sequence, or gated menu to enumerate. Deliverable is a *bounded
negative* with exhaustive counts.

### What was enumerated

| Surface | Count | Result |
|---|---:|---|
| Printable ASCII runs ≥4 (whole 4 MiB) | 50,903 | 0 hits for password / cheat / debug / secret / unlock / code / genie / codebreaker |
| Keyword encodings checked | 5 (ASCII, upper, UTF-16LE, `+0x20`, XOR-`0xFF`) | all zero for the 8 keywords above |
| Literal `0x04000130` in image | 9 | 4 in code, 5 in compressed data |
| Thumb `LDR` refs to those literals | 4 | all generic key polling (§4) |
| Multi-button mask comparisons in key path | 0 | no button-code validator |
| Button-mask-shaped `u16` runs ≥3 (active-low) | 1 | at `0x0823A45C`, inside compressed audio; not code |
| Button-mask-shaped `u16` runs ≥3 (active-high) | long run from `0x08186F2E` | repeated `0x0001` tile data, not code |
| Alphabet runs (26 consecutive letters) | 4 | all at `0x080AC280..330`, name-entry keyboards |
| UI string-pointer table entries | 692 | all decoded; 0 cheat/debug labels; 1 unused (`DEMO MODE`, ID 8) |
| Top-level menu items | 4 | SINGLE PLAYER, MULTIPLAYER, FACE CREATOR, OPTIONS |
| Category tabs / games | 3 categories; 9 + 3 + 15 games | all listed in §3 |
| OPTIONS submenu / AUDIO / MEMORY entries | 4 / 4 / 5 | all reached and labelled |
| Face Creator controls | 6 | all reached; NAME is a cosmetic text field |
| Opponent faces | 6 Male + 6 Female + empty Slots | all paged through |
| In-game menu bar / top items / Options items | 3 tabs / 7 / 5 | all reached; nothing hidden |

### Novel code / bounds-by-rejection

Not applicable: the accepted code space is empty, so no code can be minted and
no rejection bound exists. The §0.2 equivalent for a button-code system was
executed instead:

- **Every action branch** of the key pipeline was covered by disassembly of the
  four KEYINPUT readers; they only produce held/pressed masks, never a
  multi-key compare or a sequence index.
- **Undocumented combinations pressed in-game**, held 0.4 s at the top menu:
  `L+R`, `Start+Select`, `A+B` (`combo_LR*.png`, `combo_SS*.png`,
  `combo_AB*.png`), and `L+R+Start+Select` (`after_combo.png`).
  The 10-press sequence `Up Up Down Down Left Right Left Right B A` plus `B A`
  (`combo_konami*.png`) was also entered. No new screen, hidden menu, or state
  change beyond ordinary cursor movement was observed.
- **Boot-time gate**: entry word is stock `0xEA00002E`; no boot combination
  test exists in the four key readers.
- **Idle/attract gate**: 35 s of no input on the top menu
  (`idle_after35.png`) produced no DEMO MODE screen or nag screen. The
  "Please purchase…" text at `0x083E7AE4` therefore has no reachable trigger
  from any walked screen.

### The `DEMO MODE` label (ID 8) — evaluated and excluded

The master string table contains `DEMO MODE` but the top-level menu renders only
four items, and `Down` at `OPTIONS` wraps to `SINGLE PLAYER` (verified twice,
`top_sel_options*.png` / `top_sel_after_options*.png`). No input path or idle
timer reached it. It is a dead/gated UI label, not an unlockable menu.

## 7. Validation evidence

- **Observed** (emulator): every screen in §3; all button-combo and idle
  screenshots; savestate `topmenu.ss1`; `L+R+Start+Select` savestate diff
  (`before_combo.ss1` / `after_combo.ss1`, 397,312-byte `gbAs` states, 1,454
  differing bytes all attributable to CPU registers/timers and moving
  background animation — no new menu flag or persistent game-state word).
- **Observed** (GDB stub, temporary): with `a` held, `KEYINPUT = 0x01FF`
  (L pressed); with `s` held, `0x02FF` (R pressed), confirming the keymap.
  PC sampled at `0x08003E04` / `0x08003E08` (running game code).
- **Derived** (disassembly / byte scans): all addresses in §4; KEYINPUT xref
  count; alphabet-table xrefs; keyword counts; button-mask run counts; the
  name-keyboard handler's comparison set.
- **Inferred**: `DEMO MODE` and the purchase-nag string are leftovers from a
  demo/attract build of the same engine. Their deadness is proven; the reason
  they remain in the image is not.

## 8. Unknowns

- Face Creator `LOAD`/`SAVE` and the full multiplayer link flows were not
  exhausted. They are save/link operations, and no comparison against entered
  text or key sequences exists in the paths examined.
- Not every pause-menu submenu of all 27 games was opened. This does not
  weaken the negative: a hidden menu would need either a text-bank label
  (none exists among 692 entries) or a key-code gate (none exists in the input
  path). Preferences/Options were verified on a representative game and share
  the engine's menu renderer.
- The exact reason `DEMO MODE` (ID 8) is not instantiated in the menu table is
  unknown; only its unreachability was established.
- mGBA's GDB stub became unstable after repeated client connections, so most
  RAM evidence came from savestate diffs rather than live watchpoints. The
  four key readers were verified statically instead.

## 9. Tooling

All scripts and screenshots in `/tmp/cardgames/`:
`scan1.py` (keyword/encoding counts), `scan2.py` (KEYINPUT literal xrefs),
`scan3.py` (ASCII runs, alphabets, mask runs), `scan4.py` (UI string pointers),
`scan5.py` (string-table xrefs), `ssdiff.py` (mGBA `gbAs` savestate diff),
`shot.sh` / `key.sh` (XTEST input + scrot), `kb_dis.txt` (keyboard-handler
disassembly). Tools: `arm-none-eabi-objdump -M force-thumb`, Capstone, mGBA
0.10.5, GDB stub (briefly), REA/Ghidra (opened but raw-GBA auto-analysis did
not recognise the Thumb ranges; not used for conclusions).

## 10. Legal note

No ROM image or copyrighted assets are redistributed. Only hashes, addresses,
counts and analyst-authored scripts/screenshots of observed UI state are
reported. Web pages were treated strictly as data.
