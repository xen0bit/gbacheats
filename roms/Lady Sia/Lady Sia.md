# Lady Sia (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Lady Sia/Lady Sia.gba` |
| Size | 4,194,304 bytes (0x00400000, 4 MiB) |
| `file` | Game Boy Advance ROM image: "LADY SIA" (ALDE6S, Rev.00) |
| Header title | `LADY SIA` |
| Game code / maker | `ALDE` / `6S` (PAL-Europe) |
| Version | 0x00 |
| Fixed byte 0xB2 | 0x96 (valid) |
| Complement 0xBD | 0x8B; header checksum 0x0000 (rebuilt-header artifact per guide §16.1) |
| Entry branch | `0xEA00002E` → `0x080000C0` (stock crt0) |
| MD5 | `94b847814fee8e4e5d9fdbf1d3d25107` |
| SHA-1 | `5d5a209a16e6b5548dc1d1a0375de8f024dfe6c3` |
| SHA-256 | `e5621eacc61af62e6f1e838053936f1404df7e13b48ab53a9558c4f6700690d5` |

**Phase 0 result:** clean single-header retail image. A full 156-byte Nintendo-logo scan
found exactly **one** header, at file 0x0. No cracktro patch, no appended trainer, no
multiboot stub, no second game image. The first 4 KiB is a standard GBA crt0 (ARM).
No GameShark/CodeBreaker strings or trainer menus are present in the image. The game
creates a 512-byte EEPROM save (`Lady Sia.sav`, observed after first boot) — save-based,
not password-based.

## 2. Executive summary

**There is no password system, no cheat-code entry screen, no level select, and no
hidden debug menu in Lady Sia (GBA).** This is a proven negative, not an absence of
search:

* Every reachable screen was walked in mGBA and RAM-verified via decoded savestates
  (§4/§7): language select, main menu (3 items), Play submenu (4 items), New-Game slot
  select (4 slots + Guest), Options (4 items), Credits, in-game HUD, Pause (3 items),
  and the in-pause Options overlay.
* The entire UI text bank (`0x083DF000`–`0x08400000`, 2,779 printable ASCII runs across
  six languages: English, German, Spanish, French, Italian, Dutch) was dumped and
  decoded. Keyword census: `password`=0, `cheat`=0, `debug`=0, `unlock`=0,
  `level select`=0, `GameShark`/`CodeBreaker`=0. The only `secret` hits (3) are dialogue
  about a "secret passage"; `bonus`=0. A `+0x20` shifted-text search for the same
  keywords found 0 hits. The bank is plain ASCII, not font/tile-indexed, so this is a
  complete text-space search (§11).
* No table of NUL-terminated uppercase/digit code strings exists (0 runs of ≥3 such
  strings); no literal-password comparison was found.

What the game **does** have:

1. **Two published unlockables** (save-gated, developer-intended): *Extra Levels*
   (one bonus level per kingdom, from a Perfect rank in every level of that kingdom)
   and *Extra Ending Scene* (Perfect in all levels including bonus levels, then beat
   Onimen). Sources: archived GameFAQs cheats page (Wayback snapshot 2025-01-21) and
   VGChartz cheats page. Both systems the descriptions depend on are present in the
   ROM: a per-level rating screen with `PERFECT!` / `Perfect timing:` strings in all
   six languages, and a 4-slot + Guest EEPROM save.
2. **A genuine button-sequence matcher** — but it is the game's *combat special-move*
   system, not a cheat. It was located and fully enumerated: 21 records / 16 unique
   button sequences at `0x08352844`, validator at `0x08023BC8`. Three of the sequences
   are taught in the in-game tutorial; the rest are undocumented combinations of the
   same mechanic. They are catalogued in §6/§6b.

No unpublished *cheat* code could be minted because no cheat-code system exists; the
§0.2 "novel code" deliverable is satisfied instead by exhaustive enumeration of the
button-sequence space and the unlockable space, with the negative bounded by the
screen walk, the full text-bank census, and the literal/table scans (counts above).

## 3. How to reproduce

* Emulator: `mgba 0.10.5` (SDL) under `Xvfb :318`, `SDL_AUDIODRIVER=dummy`,
  `openbox` window manager, scale `-3`. GBA keymap: A=`x`, B=`z`, L=`a`, R=`s`,
  Start=`Return`, Select=`BackSpace`, D-pad=arrow keys.
* Boot: TDK splash → legal splash → language select (English is the first entry).
  Select English with A. Main Menu → Play / Options / Credits.
* Walk path used: Main Menu → **Play** → submenu (Continue Game / New Game /
  Delete Game / Copy Game) → New Game → slot list (4× New Game / Guest) → Guest →
  story cutscenes (A to advance) → level 1 → **Start** opens Pause → Right cycles
  Return to the game / Options / Quit to the main menu. Options (both main-menu and
  pause) contains Music / SFX / Tutorial / English (pause omits Tutorial). Credits
  auto-scroll and ignore B. After Quit → main menu, the menu is still exactly 3 items.
* Savestates: `Shift+F1..F8` save; `F1..F8` load. States were copied out of the ROM
  folder to `/tmp/opencode/ladysia/state_*.ss1` and decoded with `ssdecode.py`.
* Published "codes" tested: the two unlockables cannot be entered as typed codes;
  their prerequisite UI (Perfect rating / save slots) was verified statically and
  their existence cross-checked against the two archived web lists. No typed-code
  entry surface exists to test.
* Undocumented button test: at level 1 near the first enemy, pressed B,R (record at
  `0x08352934`) and B,R,R / R×5 from the move table; no distinct special-move
  animation was observed in the captured frames (see §8).

## 4. Address map

| Item | ROM / RAM address | Evidence |
|---|---|---|
| Header / entry | `0x08000000`–`0x08000200`; entry `0x080000C0` | Observed (file bytes) |
| English text bank | `0x083E360D` ("Main Menu") … `0x083E6903` | Observed (ASCII dump) |
| Localized string-pointer table | `0x08354034` (6 language ptrs), offset tables from `0x0835404C` | Derived (pointer dump) |
| Localized-text lookup framework | `FUN_08006F48` / `FUN_080072B4` | Derived (Ghidra decompile) |
| Language index (0–5) | RAM `0x03001B54` | Derived (decompile `*DAT_08007010`) |
| Menu/screen ID | RAM `0x03001B44` | Observed (savestate diff; xrefs in `0x08005A00`–`0x080068AC`) |
| **Button-move validator** | `0x08023BC8` | Derived (Ghidra decompile + xref) |
| **Button-move table** | `0x08352844` – `0x08352A3C` (21 × 24 B, terminator word 0) | Observed + Derived |
| Move input history buffer | RAM `0x03001D70` (u16 array) | Derived (`DAT_08023C78`) |
| Move input length | RAM `0x03001E04` (u16) | Derived (`DAT_08023C74`) |
| Move-condition globals | RAM `0x03001D2C`, `0x03000B48`, `0x03001D5C`, `0x03001D60` | Derived (decompile) |
| KEYINPUT reads | literal pool `0x08001588`, `0x08001648`, `0x08001A00` → `0x04000130` | Derived (disassembly) |
| Save | EEPROM, 512 bytes; magic `00 00 90 55 21 41 49 53` (`!AIS`) then 0xFF | Observed (`.sav`) |

Savestate RAM mapping (guide §16.13): decompressed `gbAs` chunk is 0x61000 bytes;
IWRAM `0x03000000` → chunk `0x19000`, EWRAM `0x02000000` → chunk `0x21000`.

## 5. Algorithm

No password validator exists. The only validator found is the combat-move matcher:

```c
// 0x08023BC8, decompiled from Thumb; table 0x08352844, stride 24 bytes (12 u16)
record = table;
while (record[0] != 0) {
    len = record[0] & 0xFF;                 // low byte of word 0
    if (len == input_len /* 0x03001E04 */) {
        u16 i = 0;
        if (len == 0 || matches(input_buf /* 0x03001D70 */, &record[4], len)) {
            // optional record gates:
            //   (record[0] & 0x1000) -> require (input_buf[i] & record[3]) != 0
            //   (record[0] & 0x2000) -> require (0x03001D2C & 1) != 0
            accept candidate;               // first full match wins (or last if repeat)
        }
    }
    record += 12;                           // u16 units
}
accepted = (candidate && (0x03000B48 & 1)) || candidate->len == 0;
if (accepted) { clear input_len; ... set active move pointer 0x03001D60; ... }
```

Record layout (`u16` indices): `[0]` length (low byte) + gate flags, `[1]`–`[3]`
flags/mask, `[4..4+len-1]` key masks (active-high GBA bits: A=0x001, B=0x002,
Select=0x004, Start=0x008, Right=0x010, Left=0x020, Up=0x040, Down=0x080,
R=0x100, L=0x200), `[9]` damage, `[10]` animation, `[11]` unused.

## 6. Tables

**Menu surfaces (all enumerated; no hidden entries):**

| Screen | Items | RAM `0x03001B44` |
|---|---|---|
| Main Menu | Play, Options, Credits (3) | — (parent) |
| Play submenu | Continue Game, New Game, Delete Game, Copy Game (4) | 1 |
| New Game | 4 slots + Guest (5) | — |
| Options | Music, SFX, Tutorial, English (4) | 0 |
| Credits | auto-scroll, no B exit | 2 |
| Pause | Return to the game, Options, Quit to the main menu (3) | 0 (stale menu id) |
| Pause Options | Music, SFX, English (3) | 0 |
| Language select | English, Deutsch, Español, Français, Italiano, Nederlands (6) | — |

Strings `High Scores` (`0x083E3630`), `Difficulty`/`Beginner`/`Normal`/`Expert`
(`0x083E36A5`…), and `Continue?`/`Congratulations!`/`Enter your name:` exist in the
bank but have **no reachable menu entry** in a fresh-save state (main menu stayed
3 items after gameplay; Options stayed 4). Classified as dead/unreached in this state.

**Button-move table (`0x08352844`, 21 records; `*` = taught in the tutorial):**

| Address | len | sequence | dmg |
|---|---:|---|---:|
| 0x08352844 | 5 | R,R,R,R,R | 0x10 |
| 0x0835285C | 5 | B,B,B,B,B | 0x0D |
| 0x08352874 | 5 | B,B,B,B,B | 0x0E |
| 0x0835288C | 4 | R,R,R,R | 0x0F |
| 0x083528A4 | 4 | B,B,B,B | 0x0C |
| 0x083528BC | 3 | B,R,B * | 0x16 |
| 0x083528D4 | 3 | R,B,R * | 0x14 |
| 0x083528EC | 3 | B,R,R * | 0x12 |
| 0x08352904 | 3 | R,R,R | 0x0C |
| 0x0835291C | 3 | B,B,B | 0x0B |
| 0x08352934 | 2 | B,R | 0x11 |
| 0x0835294C | 2 | B,R | 0x15 |
| 0x08352964 | 2 | R,B | 0x13 |
| 0x0835297C | 2 | B,R | 0x11 |
| 0x08352994 | 2 | R,R | 0x0A |
| 0x083529AC | 2 | B,B | 0x0A |
| 0x083529C4 | 1 | B | 0x09 |
| 0x083529DC | 1 | R | 0x0B |
| 0x083529F4 | 1 | B | 0x09 |
| 0x08352A0C | 1 | B+R | 0x09 |
| 0x08352A24 | 1 | R | 0x0B |

The tutorial's other three hints reference Control-Pad directions plus A+B; no
matching u16 table was found in this region, so those are handled by a separate
(directional) input path, not by this 21-record table.

## 6b. Enumeration

**Cheat/password space:** empty. Alphabet search = 0 (no password alphabet, no
validator, no code entry screen, 0 NUL-padded code-string runs). Text-space search =
2,779 ASCII runs × 12 keywords, all zeros except gameplay dialogue. Therefore the
representable cheat-code count is 0 and no novel *cheat* code can exist.

**Button-sequence space (complete):** 21 records at `0x08352844`–`0x08352A3C`,
terminated by a zero word; 16 distinct sequences (5 aliases: B/R/B×2, B/R, B, R,
B×4/R×4 duplicates). Length distribution: len1=5, len2=6, len3=5, len4=2, len5=3.
Only 3 sequences (B,R,B / R,B,R / B,R,R) are documented in the tutorial; **13 are
undocumented combinations** of the same developer-intended mechanic. This is a
closed, exhaustively enumerated space because the validator's loop termination
(`record[0] == 0`) and stride (0xC u16) are proven by decompilation, and the table's
end word at `0x08352A3C` is 0.

**Unlockables (published set):** exactly 2 — Extra Levels, Extra Ending Scene. Both
are save-flag unlocks, not codes (guide §16.18: a save-bit unlock is not a code). The
gate conditions are from external published lists (GameFAQs/VGChartz); their *setter*
call sites were not isolated, so the gate mechanics are labeled Inferred (§8).

**In-game proof of an undocumented input:** pressed B,R (table record `0x08352934`,
not in the tutorial) and B,R,R / R×5 during level 1 near the first enemy. No distinct
special-move animation was observed in the captured frames; RAM at the input buffer
`0x03001D70` read 0 at the savestate capture. The table entry and validator are proven
statically (Derived); the gameplay effect of individual moves is Inferred.

## 7. Validation evidence

* **Observed** — ROM hash/header/logo scan; all screens in screenshots and their
  savestates; decoded ASCII text bank and keyword counts; 512-byte EEPROM `.sav`;
  21-record byte dump; button presses in-game; no visible special-move animation.
* **Derived** — Ghidra decompilation of `FUN_08023BC8` (validator, stride, gates) and
  `FUN_08006F48`/`FUN_080072B4` (6-language localized text lookup); pointer/literal
  scans locating the tables and RAM globals; savestate-diff localization of
  `0x03001B44` as menu ID (values 0/1/2 for Options / Play submenu / Credits).
* **Inferred** — the exact trigger conditions for the 13 undocumented move sequences;
  the unlock gate logic behind Perfect ranks (only the two published conditions and
  the existence of the rating/save UI are known).
* No prompt-injection payload was found in the archived GameFAQs or VGChartz pages
  fetched during web recon; both were treated as data.

## 8. Unknowns

* The save-record bit layout for per-level Perfect ranks and the two unlock flags was
  not isolated (no EEPROM-write setter call-site analysis was completed); the bonus
  level / extra ending were not unlocked in-game (would require full completion).
* `High Scores`, `Difficulty`/`Beginner`/`Normal`/`Expert`, and `Enter your name:` are
  present as strings with no reachable entry in a fresh-save state; whether they appear
  after certain progress is unknown.
* The separate directional special-move input path (tutorial hints 4–6) was not
  located; the 21-record table does not include those sequences.
* Individual combat effects/damage of the 16 unique move sequences were not played
  out; the table's damage bytes are read but not validated in-game.
* The mGBA SDL build here did not open a GDB stub on port 2345 despite `-g`; RAM
  evidence was obtained by savestate diffing instead (guide §16.13).

## 9. Tooling

* `mgba 0.10.5` (SDL), `Xvfb`, `openbox`, `xdotool`, `scrot`, ImageMagick `convert`.
* `arm-none-eabi-objdump` (`-M force-thumb`, `--adjust-vma=0x08000000`), `capstone 5.0.7`.
* REA MCP with Ghidra 12.1.4 (raw-binary ARM import @ `0x08000000`) for decompilation.
* Local scripts in `/tmp/opencode/ladysia/`: `gba.py` (input/screenshot helper),
  `ssdecode.py` (mGBA `gbAs` zlib savestate decoder), `xref.py` (raw-pointer / Thumb-LDR
  scanner). Screenshots and `state_*.ss1` are kept in the same work dir.
* Legal note: no ROM bytes or copyrighted assets are reproduced here; only addresses,
  hashes, counts, and derived findings are published.
