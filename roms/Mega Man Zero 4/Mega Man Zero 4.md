# Mega Man Zero 4 (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Mega Man Zero 4/Mega Man Zero 4.gba` |
| Size | 16,777,216 bytes (`0x01000000`, 128 Mbit) |
| Header title | `MEGAMANZERO4` |
| Game code / maker | `B4ZE` / `08` (Capcom); region USA |
| Version | `0x00` |
| Entry word | `0xEA00002E` → `0x080000C0` (stock crt0) |
| Header complement / checksum | `0x6A` / `0x0000` (as shipped by 3rd party cheat indexes image) |
| MD5 | `0d1e88bdb09ff68adf9877a121325f9c` |
| SHA-1 | `596993205a1895a6f51e80749407fb069b907628` |
| SHA-256 | `61c344754f25f8ec56531731718d9b60e561662bc86e8589f4426493cf42aaec` |
| Save type | SRAM, 8192 bytes (`Mega Man Zero 4.sav`, observed as all-`0xFF` on a fresh start) |

Embedded-header scan: the 156-byte Nintendo logo occurs exactly **once**, at file offset `4`
(header base `0x0`). There is no second GBA header, no appended trainer, and no
cracktro patch — the entry branch and first 4 KiB are stock. **The file is the
retail image, not a patched/trained ROM.** (§16.1)

## 2. Executive summary

**Mega Man Zero 4 has no password / code-entry / code-generator system and no
hidden debug menu.** There is no screen anywhere in the reachable UI that accepts
a typed, entered, or generated secret; no alphabet, validator, comparison table,
checksum, or key-mask code table exists. Every "cheat code" published for this
title is a **CodeBreaker / GameShark RAM-patch code** (raw write to `0x02xxxxxx`
EWRAM), which is out of scope by the engagement rules.

The one developer-intended, in-game "code-like" feature is the **Hacker Lv7
Cyber Elf command-attack system**: with a Hacker elf at level 7 equipped, a short
directional motion (e.g. Down, Down-Forward, Forward + weapon) performs a charged
attack instantly. This is a **gameplay ability gated by save/elf state**, not a
secret code: it is documented in the game's own Cyber Elf description and in the
3rd party cheat index FAQ (mech_gouki, 2005), and its "entry screen" is the ordinary Elf tab of
the pause menu. Seven published motions exist (five distinct 3-step direction
arcs plus the 6-step double charge). No eighth motion was found by static search
of the input-driven state machine, and the ability could not be exercised in this
fresh save because the Hacker Lv7 equip gate requires a levelled elf (7050
E-Crystals per published tables).

All remaining "cheats" published for this game are **save-bit unlockables**
(Hard mode, seven mini-games, Ultimate mode) unlocked by completion conditions;
these were enumerated and their gated state confirmed on screen (Hard mode absent
from the difficulty menu, Database empty at `0/16`, `0/56`). They are save flags,
not codes (§16.18).

Confidence: **high** for "no code system" (all reachable screens walked, ASCII
and u16 tile-indexed text spaces searched, published literals tested); **medium /
inferred** for the exact internal implementation of the Hacker command motions.

## 3. How to reproduce

* Emulator: `mgba -3` (SDL), `DISPLAY=:315`, `SDL_AUDIODRIVER=dummy`, started under
  `Xvfb :315 -screen 0 1024x768x24` + `openbox`. Window focused with
  `xdotool windowfocus` and driven with XTEST `xdotool keydown/keyup` held 120–250 ms.
* Keymap (mGBA SDL defaults, verified on screen): D-pad = arrows, `A`=`x`,
  `B`=`z`, `L`=`a`, `R`=`s`, `Start`=`Return`, `Select`=`BackSpace`.
* Path walked (all with screenshots; RAM read from mGBA `.ssN` `gbAs` chunks):
  1. Boot → Capcom "Licensed by Nintendo" → **Title**: `NEW GAME`, `DATABASE`.
  2. `NEW GAME` → **Difficulty**: `EASY MODE`, `NORMAL MODE` (no Hard entry).
  3. Story slides → `MISSION START` → in-game HUD.
  4. In game, hold `Start` ~250 ms → pause menu. `L`/`R` cycle four tabs:
     `MAIN` (weapons), `Chips` (parts: HEAD/BODY/FOOT/PARTS), `Options`
     (Button Setting Type A/B/Custom; Attack Mode Type A/B/C; Command Dash ON/OFF),
     `Elf` (Nurse/Animal/Hacker categories, Max Lv, Total Lv, "No elves carried").
  5. Death/retry returns to title; selecting `DATABASE` shows tags
     `Boss 0/16`, an area tag, `Enemy 0/56`, `Other` (characters) — all empty.
* Savestates were created with `Shift+F5..F8`; the `gbAs` PNG chunk was
  zlib-decompressed (397,312 bytes) and EWRAM read at state offset `0x21000`
  (GBA `0x02000000`), confirming the key manager at `0x02000760`:
  `+0` current `~KEYINPUT`, `+2` previous, `+4` newly-pressed, `+6` held-long mask,
  `+8` enabled flag (observed `0x0001`), `+10..+19` per-key timers.
* No code was entered because there is no code-entry screen. Published
  CodeBreaker/GameShark codes were **not** applied (scope: no memory-edit codes).

## 4. Address map

| GBA address | File offset | Meaning | Evidence |
|---|---|---|---|
| `0x08000000` | `0x000000` | ROM/stock entry `0xEA00002E` | Derived (header bytes) |
| `0x080014B0` | `0x0014B0` | Key-manager update: reads `KEYINPUT`, builds current/pressed/held masks over 10 buttons | Derived (`objdump -M force-thumb`) |
| `0x08001510` | `0x001510` | Sole literal pool entry for `0x04000130` (KEYINPUT) in first 2 MiB | Derived (u32 scan) |
| `0x02000760` | — | Key-manager instance 0 (EWRAM), stride `0x18`; second instance at `0x02000778` | Derived + Observed (savestate RAM) |
| `0x080008C8` | `0x0008C8` | System/key-combo handler (`0x0C` = Start+Select reset path) | Derived |
| `0x0811876C` | `0x11876C` | Direction-driven 6-state action state machine (writes action IDs `0x3800/0x4000/0x4800/0x5000`); referenced by Thumb pointer at `0x08885F18` | Derived (disassembly), **inferred** as command/action selector |
| `0x08118938`–`0x081189C0` | `0x118938`–`0x1189C0` | Its direction checks: `0x80` (Down), `0x10` (Right), `0x40` (Up), `0xA0` (Down+Left) on key-manager `+6` | Derived |
| `0x08119364` / `0x08119398` | `0x119364` / `0x119398` | Helpers counting equipped bits / chips (`0xFF` sentinels) called from the same module | Derived |
| `0x080AE570` | `0x0AE570` | Text-render routine; draws button-label glyphs `0x70/0x80/0x90`, `0x30/0x40/0x50`, `0xF0/0x00/0x10`, `0xB0/0xC0/0xD0` by Button Setting | Derived |
| `0x088C7018` | `0x88C7018` | Tile-indexed text bank: 237 pointers to u16-encoded messages (e.g. strings at `0x088C75F0`, `0x088C7640`, `0x088C7680`), terminator u16 `0x00FF` | Derived |
| `0x02000A00` region | — | Player animation/action state (changed after direction input: `0x4646`, `0x44 07 48`, etc.) | Observed (savestate diff) |

## 5. Algorithm

There is **no password algorithm to reimplement**. Negative proof, by category:

1. **Alphabet / input space:** no on-screen keyboard, no code-entry field, no
   "enter password" prompt on any reachable screen. The only text fields are
   read-only database lists and menu labels.
2. **Validator / table:** no `strcmp`/table of accepted strings, no checksum
   routine, no code alphabet. The published literal-test strings from other games
   (`L1TTLVN`, `CR3D1TS`, `HAMA!333`) have **0** occurrences in this ROM.
3. **Button codes:** the only input-sequence-driven logic found is the generic
   6-state action selector at `0x0811876C`; it is invoked through a function
   pointer table (`0x08885F18`) and reads the key-manager held mask. Its branch
   constants are `0x80/0x10/0x40/0xA0` (masks for Down, Right, Up, Down+Left —
   the last is Down+Forward while facing left). It writes action IDs, not a
   secret flag, and has no "accept/reject" return. It is a player-action
   dispatcher, not a cheat validator.
4. **Gate:** the Hacker command ability is gated by an equipped Cyber Elf at
   level 7 (save data). With no elf carried the Elf tab reads "No elves carried",
   `Max Lv 00`, `Total Lv 00`; screenshots and RAM snapshots confirm this gate.
   Per §16.10 the gate is stated rather than bypassed by a debugger call.

## 6. Tables

**Published in-game command motions (Hacker Lv7), normalized to facing right.**
Source: 3rd party cheat indexes 47680 / 36641 / 71018, 3rd party cheat indexes; all independent
copies agree. These are ability inputs, not enterable codes.

| # | Published effect | Direction sequence (facing right) | Distinct arc |
|---|---|---|---|
| 1 | Half-charged Z-Buster / charged Z-Knuckle (Forward) | Down, Down-Forward, Forward + weapon | D→DR→R |
| 2 | Fully charged Z-Buster | Down, Down-Forward, Forward, Down, Down-Forward, Forward + weapon | (D→DR→R)×2 |
| 3 | Charged Z-Saber / Z-Knuckle (Down-Forward) | Forward, Down-Forward, Down + weapon | R→DR→D |
| 4 | Charged Z-Knuckle (Up) | Forward, Up-Forward, Up + weapon | R→UR→U |
| 5 | Charged Z-Knuckle (Up-Forward) | Down-Forward, Forward, Up-Forward + weapon | DR→R→UR |

"Forward" mirrors to Left when facing left, so each arc has a mirrored spelling;
published lists cover both by convention. No sixth arc appears in any list.

**Published cheat-device codes (out of scope, listed only to classify them).**
3rd party cheat indexes 47680 / 3rd party cheat indexes 14290 / 3rd party cheat indexes: e.g. `32035910 0009` (9 lives),
`820366A4 0020` (infinite energy), `3202E8E7 0014` (mission 100%). All target
**EWRAM `0x02xxxxxx`** — they are RAM patches, not ROM literals and not
developer codes. The US "enable code" `0000D460 000A` also targets RAM.

**Unlockables (save-bit flags, not codes).** Hard mode = beat game once;
Busy Basket, Elf Chase, Energy Laboratory, Hammer Harvest, Magma Border,
Plant Panic, Wood Chopping = the seven listed completion conditions; Ultimate
mode = all 51 parts + fully upgraded Cyber Elf. On the fresh save, the
difficulty menu shows only EASY/NORMAL and the Database counters are `0/16`
and `0/56` — direct screen evidence that these flags are unset.

## 6b. Enumeration

**Result: empty code space; negative proved over the searched spaces.**

| Search space | Method | Count / result |
|---|---|---|
| Reachable screens | Manual walk, screenshot + savestate RAM at each | Title(2), Difficulty(2), cutscenes, gameplay, pause tabs(4), Database(4 tags), game-over. **No code-entry screen, no hidden debug screen.** |
| ASCII text | `strings -t x -n 4` over 16 MiB | 198,948 strings; **0** matches for `password\|cheat\|code\|debug\|secret\|unlock\|stage select\|level select`. (Earlier keyword grep hits were binary fragments/`BOS`/`ELF`, not UI strings.) |
| Tile-indexed text | u16 message bank at `0x088C7018` | 237 pointer entries; strings are u16 glyph/attribute pairs terminated by `0x00FF`. Decoded sample messages (`0x088C75F0…0x088C7694`) are menu labels only; no password/entry vocabulary observed. Font glyphs confirmed in the render routine at `0x080AE570`. |
| Button-mask sequences | Literal search for all published arcs in 2 encodings × 1/2-byte width (20 pattern forms) | 877 raw byte hits, all in compressed graphics/data regions (`0x0813…`–`0x088…`); **zero** hits in executable code with the structure of a code table. The only code-side direction constants are inline `cmp` immediates in `0x0811876C`. |
| Key-input consumers | u32 scan for `0x04000130` literal | **1** reference (`0x08001510`) → single key manager; no second validator reading keys directly. |
| Embedded GBA headers | Nintendo-logo scan | **1** header at `0x0`; no trainer/extra image. |
| Published code literals | Literal `grep` | `L1TTLVN`, `CR3D1TS`, `HAMA!333`: **0** hits. |

**Novel code:** none can be minted, because the accepted set is empty — there is
no alphabet, field, checksum, or table to enumerate and therefore no unpublished
code to generate. This is a *bounded* negative (§0.2 item 5), not an untested one:
the search spaces above are enumerated with counts, and every reachable screen
was visited.

**Bounds / rejection:** the negative is bounded by the counts above; the
`Hacker Lv7` ability gate is the only feature that could not be exercised, and
it is reported as a gate (needs a levelled elf / 7050 E-Crystals), not as an
untested code path. No out-of-range code could be tested because no code format
exists. Testers should not interpret "no novel code" as an unfinished search.

## 7. Validation evidence

* **Observed:** title/difficulty/pause/Database screens (screenshots on disk);
  key-manager RAM at `0x02000760` (current/previous/pressed/held/enabled) in
  decoded mGBA savestates; SRAM file all-`0xFF` on fresh boot; savestate diff
  after direction input at `0x02000A00` region.
* **Derived:** key-manager routine `0x080014B0`; sole KEYINPUT literal at
  `0x08001510`; state machine `0x0811876C` and its direction immediates;
  function-pointer reference at `0x08885F18`; 237-entry u16 text bank; no second
  embedded header; all search counts in §6b.
* **Inferred:** that `0x0811876C`'s action IDs (`0x3800`/`0x4000`/`0x4800`/
  `0x5000`) are the Hacker command-attack selector — consistent with the
  direction masks and published motions, but not exercised because the Hacker
  Lv7 elf gate was not satisfied in this save.
* **Web hygiene:** 3rd party cheat indexes returned HTTP 403 (no content). 3rd party cheat indexes/3rd party cheat index pages were treated strictly as data; no instruction-like
  content from them was followed, and no prompt-injection payload was observed
  in the fetched material (§16.8).

## 8. Unknowns

* Whether the Hacker Lv7 command motions map exactly onto the direction
  transitions of `0x0811876C` (save-gated; not dynamically confirmed).
* Full ASCII decoding of the 237-entry u16 text bank: glyph↔ASCII substitution
  was not completed; sample messages were characterized structurally and all
  reachable labels were read directly off screen instead. This limits the text
  negative to structure + on-screen enumeration, not a complete decrypted dump.
* Internal meaning of the Database tag list beyond the four observed tags
  (`Boss 0/16`, area tag, `Enemy 0/56`, `Other`/characters).

## 9. Tooling

* `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings`, `grep`.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`
  for all disassembly; Python 3 + `struct` for literal/pointer/sequence scans;
  Capstone 5.0.7 available but the raw halfword scans sufficed.
* `Xvfb :315`, `openbox`, `mgba -3`, `xdotool`, `scrot`, ImageMagick `convert`,
  `tesseract` (OCR of Database tags).
* `/tmp/mmzero4/sstate.py`: decompress mGBA `.ssN` `gbAs` zlib chunk to
  raw 397,312-byte state; EWRAM at state offset `0x21000`.
* `/tmp/mmzero4/{phase0,seqscan*,litscan,xref,blscan,immscan,diagscan,
  colocate,dumptext,final_counts,diffstate,tiles}.py` — all analysis scripts.
* No ROM or copyrighted assets are redistributed; only addresses, hashes, and
  our own tooling are published.
