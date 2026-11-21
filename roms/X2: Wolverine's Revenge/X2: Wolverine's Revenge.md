# X2: Wolverine's Revenge (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `X2: Wolverine's Revenge.gba` (8,388,608 bytes / 8 MiB) |
| Header title | `X2 WOLVERINE` |
| Game code / maker | `AWVE` / `52` (EU, rev 0x00) |
| Entry word | `0xEA00002E` (stock `b 0xC0` — retail image, not a cracktro) |
| Header checksum | `0x0000`, complement `0x52` (normal rebuilt-header artifact) |
| MD5 | `69662d33f665b2e00e4f95aa75b16a6a` |
| SHA-1 | `dc2e861013a9b6a65b9bcd122f070c8f55d1471b` |
| SHA-256 | `26eac12f29b1bec1cd0f206c3a050dc50b8be91a210b19f210a2176df5308f40` |

`file(1)` reports `Game Boy Advance ROM image: "X2 WOLVERINE" (AWVE52, Rev.00)`.

## 2. Executive summary

This game has **no password/code-entry screen**. Its developer-intended cheat surface is a
**button-code system** entered on the **Slot Select** screen: hold **L** and press a fixed
7-symbol sequence drawn from the alphabet `{r,l,u,d,s}` (Right, Left, Up, Down, Select).

The system was fully reversed:

* A capture hook (`0x08008204`) records each L-gated press into a **7-byte ring buffer**
  (sentinel `0x2D`) in a cheat-manager object and calls the validator (`0x08007FD0`).
* The validator compares the 7-byte buffer with a table of **5 hard-coded NUL-terminated
  strings** at `0x08031E68`. All five match the published GameFAQs/Cheat Happens lists.
  Table slots 0 and 2 are NULL (dead flags), so the accepted set is **exactly 5**.
* Because the buffer is a mod-7 ring, **any sequence whose last seven presses equal one of
  the five codes is accepted** — an unlimited family of unpublished aliases. I minted one
  (`L + Up, Right×7`, an 8-press sequence) and verified it in the emulator: it produced
  **99 lives** exactly like the published `L + Right×7` code, while the no-code control and
  an invalid `L + Left×7` both leave lives at **3**.
* The ROM also contains **unused/debug menus** ("level skip", "cheats", "level select",
  acts 1–8, danger 1–8, "select controls", "sleep") and a screen-state byte at
  `0x020038CD` (TCRF values 0x05/0x0A/0x0B). Those screens are gated behind a debug
  state variable, not reachable by any tested controller input; they are documented in §8.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 under Xvfb, `SDL_AUDIODRIVER=dummy`, scale 3×.
* Keymap (verified against `KEYINPUT` `0x04000130`): A=`x`, B=`z`, L=`a`, R=`s`,
  Start=`Return`, Select=`BackSpace`, D-pad=arrows. Holding `a` clears key bit 9 (L);
  holding `x` clears bit 0 (A).
* Path: boot → press Start through the Marvel/intro screens → **SELECT A SLOT**.
  Hold L and press the sequence; **release L between attempts**. Start a new game to see
  the effect on the HUD (lives counter at top-left, `xNN`).
* Codes tested (all confirmed accepted unless noted):
  * `L + Right×7` → 100 lives (HUD shows `x99`) — published, confirmed.
  * `L + Up, Right×7` (8 presses; novel alias) → `x99` — **novel, confirmed**.
  * `L + Left×7` → rejected (Slot Select info panel still reads `LIVES: 3`).
  * No code → `x3` lives (control).

## 4. Address map

All addresses are GBA bus addresses; file offset = address − `0x08000000`.

| Address | Role |
|---|---|
| `0x08031E68` | Code string table: five 8-byte records (7 chars + NUL) |
| `0x08007FD0` | Validator: copy ring buffer → stack, 7 `strcmp`-style compares, set 7 flag bytes |
| `0x08008178` | Effect dispatcher: reads cheat flags, writes lives / power-up bits |
| `0x08008204` | Capture hook: L-gate test, write pressed ASCII key into ring buffer, call validator |
| `0x0800824C` | Pointer-table writer (`table[index] = ptr`) |
| `0x08008264` | Buffer initialiser (all 7 bytes = `0x2D`) |
| `0x080082DC` | Cheat-manager constructor (installs the 5 code pointers) |
| `0x08010B18` | Global key reader: `held = ~KEYINPUT & 0x3FF`, `pressed = held & ~old` |
| `0x02000650` | Held key word (active-high); byte `+1`, bit 1 = L held |
| `0x0200003C` | Global pointer to cheat-manager object |
| `0x02000084` | Global pointer to game-state struct; lives at `+0x38` (set to 100 by code) |
| `0x08035B00–0x08036280` | Text bank (English strings + self-pointer records) |
| `0x080353D0–0x08035748` | Text-ID → string-pointer table (stride 8) |
| `0x020038CD` | Screen/debug-state byte (TCRF: 0x05, 0x0A, 0x0B) |
| `0x0801E960–0x0801EA96` | Seven menu update hooks that install/call the capture hook |

## 5. Algorithm

```
# capture, called once per frame per menu screen (0x08008204):
key = ascii_code_of_newly_pressed_direction
if (held_keys_high_byte & 0x02) == 0: return      # L must be held (bit 9 of 0x3FF)
buf[index] = key
index = (index + 1) mod 7
validate(manager)                                 # 0x08007FD0

# validate (0x08007FD0):
s = [ buf[(index+k) mod 7] for k in 0..6 ] + [0]   # rotate ring into chronological order
for i in 0..6:
    if table[i] != NULL and strcmp(s, table[i]) == 0:
        flags[i] = (i == 1) ? 1 : ...             # set flag byte at manager+0x1C+i
        play_sound()

# effects (0x08008178), evaluated after flags are set:
if flags[1]: lives = 100                           # write 100 to state+0x38
if flags[3]: state[0x3C] |= 0xFE                   # all seven power-up bits
... (other flags gate further effects)
```

Notes: the validator is a plain exact string compare — no checksum, no bit-packing, no
PRNG. The ring rotation at `0x08007FD8–0x08008064` uses `mod 7` (`0x08000242` thunk) to
read `buf[index+k]`, which is exactly why an arbitrary prefix is harmless once it has been
shifted out.

## 6. Tables

**Code strings** (`0x08031E68`, each 7 chars + NUL):

| Table slot | Offset | String | Effect | Published? |
|---:|---|---|---|---|
| 0 | `0x08031E60` | *(NULL pointer)* | dead flag | — |
| 1 | `0x08031E70` | `rrrrrrr` | 100 lives | Yes (all lists) |
| 2 | — | *(NULL pointer)* | dead flag | — |
| 3 | `0x08031E68` | `rlrlrlr` | all power-ups | Yes |
| 4 | `0x08031E78` | `rudrlss` | regenerate with claws extended | Yes |
| 5 | `0x08031E80` | `sluddud` | infinite double jump | Yes |
| 6 | `0x08031E88` | `dudduds` | invincibility | Yes |

Alphabet mapping: `r`=Right, `l`=Left, `u`=Up, `d`=Down, `s`=Select. All codes are exactly
7 presses; L is a separate held modifier and is not part of the string.

Published sources cross-checked: GameFAQs GBA cheats (The_President, 17/10 votes),
Cheat Happens GBA, SuperCheats, IGN GBA cheats, Vizzed. All five agree; a full-ROM scan for
`[rluds]{7}\0` found **exactly these five** (plus one coincidental hit at `0x7B2AF9` in
non-code data). Console-specific lists (PS2/GameCube/Xbox/PC button combos) do **not**
apply to the GBA SKU.

## 6b. Enumeration

**Space definition.** Alphabet size 5, fixed length 7, one gate bit (L held):
`5^7 = 78,125` distinct 7-press sequences. The validator accepts **exactly 5** of them —
the five strings in §6. The two NULL table slots mean flags 0 and 2 can never be set by
input. There is no checksum and no variable length in the base system.

**Accepted set proven complete.** (1) Exhaustive literal scan of the 8 MiB image for
7-symbol `[rluds]` strings found exactly the five table entries; (2) the validator's
pointer table is initialised with exactly five non-NULL pointers (constructor
`0x080082DC` writes indices 1,3,4,5,6 only); (3) every compare is an exact `strcmp`, so
no other 7-press string can match.

**Novel generated code.** Exploiting the mod-7 ring: any sequence whose **last seven**
presses are a valid code is accepted, so the accepted language is
`Σ* · {rrrrrrr, rlrlrlr, rudrlss, sluddud, dudduds}` — an infinite family of unpublished
codes. I generated and entered:

```
L + Up, Right, Right, Right, Right, Right, Right, Right     (8 presses)
```

This string appears in **no** published list. Result: **HUD shows `x99` lives**, identical
to the published `L + Right×7`; screenshot `novel_gameplay2.png` (work dir).

**Bounds proven by rejection.**

* Wrong symbol: `L + Left×7` → no effect; Slot Select save-info panel reads `LIVES: 3`
  (`reject_menu.png`). This is a valid-length, L-gated input that fails the table compare.
* No modifier: a run with no code → `x3` lives (`control_gameplay.png`). The L gate at
  `0x0800821A` is the reason; the static test `held_high_byte & 0x02` covers it.
* Wrong length: the buffer is initialised to sentinel `0x2D` (`0x08008264`), so a 6-press
  prefix cannot match any NUL-terminated 7-char table string.

## 7. Validation evidence

* **Observed** (mGBA screenshots, all in `/tmp/opencode/x2wolverine/`):
  `after_100lives.png`→`gameplay.png` (`x99`), `novel_gameplay2.png` (`x99`),
  `control_gameplay.png` (`x3`), `reject_menu.png` (`LIVES: 3`), `final_state.png` (`x3`).
* **Observed** (GDB stub, `KEYINPUT`): holding `a` → `0x01FF` (L, bit 9 clear); holding
  `x` → `0x03FE` (A, bit 0 clear).
* **Derived** (disassembly, byte-verified): code table at `0x08031E68`; capture/validator/
  effect chain at `0x08008204 / 0x08007FD0 / 0x08008178`; ring-buffer sentinel and mod-7
  rotation; the L-gate test; the five-pointer initialisation.
* **Inferred**: the exact semantic names of flags 2, 4, 5, 6 (effect code beyond
  `0x080081F6` was not fully traced). The character labels `r/l/u/d/s` are inferred from
  the caller immediates (`0x72/0x6C/0x75/0x64/0x73`) and confirmed by the matching effects.

## 8. Unknowns

* **Debug screens (gated, not code-derived).** The text bank contains `level skip`,
  `cheats`, `level select`, `act 1..8`, `danger 1..8`, `select controls`, `sleep`,
  `press R + L + select to wake`, and unlock messages (`super-hero mode unlocked!`,
  `secret gallery unlocked!`, `danger room %d unlocked`). TCRF and a published emulator
  walkthrough state that writing `0x05`, `0x0A`, `0x0B` to `0x020038CD` opens SELECT
  CONTROLS, LEVEL SKIP and SLEEP respectively. Those are **Action-Replay-style RAM writes,
  not in-game button codes** and are out of scope; I did not find a controller path that
  writes that byte, and no tested input reached those screens. They are reported as
  gated/unused content, not as cheats.
* No password screen, alphabet table, or checksum validator exists in this SKU; the
  "codes" frequently published for other platforms use buttons (Triangle/Circle/Y) that
  do not exist on the GBA and were verified absent from the ROM.
* The effect of flags 2/4/5/6 beyond the two traced effects was not exhaustively exercised.

## 9. Tooling

`strings -t x`, Python byte/pointer scanners (`find_codes*.py`, `pointers.py`,
`find_live_strings.py`, `find_refs*.py`), `arm-none-eabi-objdump -M force-thumb`,
Capstone scanner, mGBA 0.10.5 (SDL + GDB stub), GDB `multiarch`, `xdotool`, `scrot`,
`convert`. Savestate chunks were inspected by parsing PNG `gbAs` chunks with `zlib`.
No ROM or copyrighted assets are redistributed; only addresses, hashes, algorithms and
original screenshots are published.

## 10. Cleanup

All emulator/GDB processes started for this engagement were terminated by PID, and all
`.sav`/`.ss*` files generated in the ROM folder were removed. Screenshots and analysis
scripts remain only in `/tmp/opencode/x2wolverine/`.
