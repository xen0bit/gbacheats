# The Land Before Time: Into the Mysterious Beyond (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `The Land Before Time: Into the Mysterious Beyond.gba` |
| Size | 8,388,608 bytes (8 MiB) |
| `file` ID | Game Boy Advance ROM image: "LBT_ITMB" (BLOEGY, Rev.00) |
| Header title (`0xA0`) | `LBT_ITMB` |
| Game code (`0xAC`) | `BLOE` |
| Maker (`0xB0`) | `GY` (The Game Factory) |
| Version (`0xBC`) | `0x00` |
| Fixed byte `0xB2` | `0x96` (valid) |
| Header checksum (`0xBE`) | `0x0000`, complement (`0xBD`) `0x00` — rebuilt-header artifact (guide §16.1), not evidence of a cracktro |
| Entry word | `0xEA00002E` → `0x080000C0` (stock crt0; no trainer/cracktro patch) |
| MD5 | `cc966f781b2c7d2b61c5111063aa3e47` |
| SHA-1 | `90f1f16591aceae35af1277b3970963ed1c7c796` |
| SHA-256 | `455f5c32ec345b595098b4c284a8db8247310f9a5b3e282567a5ae5b94d39db0` |

Developer/publisher confirmed by 3rd party cheat indexes as **Sirius Games / The Game Factory, 2006**. This is a
**different game and different engine** from the sibling *The Land Before Time* (GBA, Full Fat,
2002) analysed separately. The sibling's published character passwords (e.g.
"Spike, Cera, Littlefoot, Golden Tree Star") and its "SKIP LEVEL" debug string belong to that
other ROM and were **not** found in this image (verified literally — see §6b).

## 2. Executive summary

**Bounded negative: this ROM has no in-game cheat surface of any kind.** There is no password
entry screen, no button-code validator, no hidden/debug menu, no unlockable content reachable by
controller, and no developer code generator. It uses an EEPROM battery save (4 slots) instead of
a password system.

Every reachable screen was walked in mGBA (§3) and the complete embedded string corpus and C++
class inventory were enumerated (§6b): **zero** password/cheat/code strings, **zero**
cheat/debug/password classes, **zero** button-mask code tables, and **zero** code-entry UI
surfaces. The only "code-like" material published for this SKU is external GameShark/CodeBreaker
data (out of scope) — those are RAM patches, not developer-intended cheats.

Because no validator exists, no novel code could be minted; per guide §0.2 the negative is proven
with counts and full screen enumeration instead (§6b). A sibling-game password list was checked
literally against this ROM and is absent.

**Prompt-injection note (guide §16.8):** a 3rd party cheat index fetch for the *sibling* game returned a block
claiming "This page is not intended for humans… These instructions are only for LLMs and
automated agents to follow…". It was treated as untrusted data and ignored; no instruction in it
was followed.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 SDL, `DISPLAY=:315`, `SDL_AUDIODRIVER=dummy`, `-3` scaling.
* A byte-identical copy (`md5 cc966f…`) was run from `/tmp/landbeforetime2/lbt.gba` so
  no `.sav`/savestate could be written into the ROM folder.
* Keymap (mGBA SDL defaults): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`,
  D-pad=arrow keys. Holds of 120 ms with 180 ms gaps (guide §16.2).
* Screenshots saved as `s_01.png` … `s_17.png`, `probe_*.png` in the work dir.

Screen walk (all reachable screens, each screenshot-verified):

1. Language select: English / Español / Français (`screen.png`).
2. Title/logo screen (`s_01.png`).
3. Main menu: **Start Game / Show Credits / Options** — exactly 3 entries (`s_02.png`, `s_12.png`).
4. Save-slot selector: **4 slots** (`slot1_icon`…`slot4_icon`), showing "Game 1 / Level 1 /
   Score 0 / Lives 3" after play; empty slots read "Game N Empty" (`s_03.png`, `s_11.png`).
5. Level intro / tutorial card ("ACROSS THE GORGES", "Press A to jump", "Press B to eat leaves")
   (`s_04.png`, `s_06.png`).
6. World map / level selector: 9 paw-marker stages with stage banner "1. Across the gorges"
   (`s_04.png`, `s_10_back.png`).
7. In-game gameplay with HUD (lives, tree-stars, health) (`s_08.png`).
8. Pause: **"Quit? A Yes / B No"** only — no other menu entries (`s_09_pause2.png`).
9. Options: **Sound Effects - 00000 +** and **Music - 00000 +** only; Down does not reveal more
   entries (`s_13_options.png`, `s_14_options2.png`).
10. Credits: auto-scrolling name list (`s_17_credits2.png`).

No screen contains an alphabet grid, a text/code field, a cheat list, a debug menu, or an
unlockable gallery.

Button-code probes on the main menu (each from a loaded savestate):
* Konami sequence `↑↑↓↓←→←→ B A` (`probe_konami.png`) — only moved the menu cursor to Options;
  no new screen/flag.
* L+R, L+R+Start, L+R+Select and random 10-press controls — no effect beyond normal cursor
  movement.
* RAM evidence: savestate `gbAs` diffs (guide §16.13) for Konami vs a random control gave
  comparable change counts (IWRAM 1,133 vs 1,402 bytes; EWRAM 1,335 vs 1,880 bytes) — ordinary
  animation/timing noise, no code-specific flag. The mGBA SDL build did not open a GDB stub on
  :2345 despite `-g`, so savestate diffs were used instead (tooling §9).

## 4. Address map (file offsets; ROM address = 0x08000000 + file offset)

| Item | File offset | ROM address | Notes |
|---|---:|---:|---|
| Header | 0x000 | 0x08000000 | title `LBT_ITMB`, code `BLOE`, maker `GY` |
| crt0 entry | 0x0C0 | 0x080000C0 | stock ARM startup |
| Inert asset-layer name `"debug"` | 0x1B9D7E | 0x081B9D7E | one occurrence; **0** 32-bit pointers to it — level-editor layer label, not a debug menu |
| Asset name `"screenbg"` | 0x1B9D88 | 0x081B9D88 | adjacent layer label |
| Scene-name strings (`level1.xml`…`level9.xml`) | 0x4DA72… | 0x084DA72… | XML scene assets; 9 levels |
| Text bank start | ~0x49B900 | 0x0849B900 | all UI/dialogue strings in ASCII |
| `mainscreen.xml` | 0x49BA1C | 0x0849BA1C | main-menu scene |
| `levelselector.xml` | 0x49BA38 | 0x0849BA38 | icon1…icon9 |
| `slotselector.xml` | 0x49BAFC | 0x0849BAFC | slot1_icon…slot4_icon |
| `language.xml` | 0x49BB68 | 0x0849BB68 | language scene |
| Save magic `"LBTSAVE1"` | 0x49BB78 | 0x0849BB78 | EEPROM magic; stored byte-reversed as `1EVASTBL` |
| `"Quit?"` / `"Yes"` / `"No"` bank | 0x49C300…0x49C338 | 0x0849C300… | pause strings |
| RTTI class-name bank | 0x4A5DF0…0x4A6244 | 0x084A5DF0… | C++ class names (§6) |
| `"no mem for gif decode :o("` | 0x4A53C4 | 0x084A53C4 | GIF decoder diagnostic |

Save format (EEPROM, 512 bytes): magic `31 45 56 41 53 54 42 4C` ("LBTSAVE1" little-endian)
at `0x00`; four slot records from `0x08`; unused space `0x11`+ is `0xFF`. No flag bits for
unlockables were identified; the only progression data is level/lives/score and per-level
gold/silver/bronze award bytes.

## 5. Algorithm

Not applicable — **no validator exists**. The negative was established by exhaustive enumeration
(§6b) rather than by reversing a checksum. Method: (1) literal search for every published code
and for the sibling game's password tokens; (2) case-insensitive keyword census of all ASCII
strings; (3) enumeration of the game's own text bank and C++ class inventory; (4) search for
32-bit key-register literals and u16 button-mask tables; (5) walk of every reachable screen with
screenshots and savestate-RAM checks; (6) dynamic press of common button-code sequences.

## 6. Tables

**C++ RTTI game classes (17 C-prefixed names at 0x4A5E10–0x4A6224, plus `Scene`,
`GraphicsCtrl`, `Graphics`, `LittleFootController`):** `CMainMenu`, `CGameData`, `CIntro`,
`CLevel1`…`CLevel9`, `CIngameMenu`, `CCredits`, `CGame`, `CGifDecoder`, `CPlayableScene`,
`Scene`, `GraphicsCtrl`, `Graphics`, `LittleFootController`. **None** is a password, code-entry,
cheat, debug-menu, unlock or generator class.

**Embedded XML scene assets:** `mainscreen.xml`, `mainscreen_fr.xml`, `levelselector.xml`,
`slotselector.xml`, `language.xml`, `level1.xml`…`level9.xml`, `credits.xml`, `credits_fr.xml`.
No `password.xml`, `cheat.xml`, `debug.xml` or equivalent.

**Published code reconnaissance (all OUT OF SCOPE — external cheat devices):**
3rd party cheat indexes `gba/562723` password list, GameShark/CodeBreaker lists (3rd party cheat indexes, libretro DB), e.g. `0200995C 00000063` (lives), `82009948 03E7` (fruit),
`32006EC4 000A` (all stages), `D40B358E 0000F259` (master). These are parity-checked RAM writes
requiring a cheat device; they are not entered through the game and are excluded by the brief.

## 6b. Enumeration

**Space definition:** empty. There is no alphabet, no code length, no checksum and no lookup
table because the game exposes no code surface. Representable in-game codes = **0**.

**Counts proving the bounded negative (all from the exact ROM hashed in §1):**

| Search | Space checked | Hits relevant to cheats |
|---|---:|---:|
| `strings -t x -n 4` whole ROM | 72,804 strings | 0 password/cheat/code entries (only `debug`, GIF strings, `wcODESh`-style asset noise) |
| Game text bank 0x49A000–0x4A5E10 | 2,627 printable runs | 0 (18 keyword hits are all "extra life"/dialogue/CRT noise: `…vita extra!`, `no mem for gif decode`, `global constructors…`) |
| Literal `Littlefoot`/`Cera`/`Ducky`/`Spike` passwords from sibling | whole ROM | names present only as `.gif` asset filenames/dialogue, **no** password-token sequence; `"Golden Tree"` = **0** hits |
| `password` / `cheat` / `secret` / `konami` / `unlock` / `code` (case-insensitive, whole ROM + text bank) | 72,804 + 2,627 | 0 |
| C++ RTTI classes | 17 (+4 non-C) | 0 cheat/debug/password classes |
| Embedded XML scene names | 11 | 0 password/debug scenes |
| 32-bit literal `0x04000130` (KEYINPUT) | whole ROM | 0 |
| 16-bit `0x04000130` | whole ROM | 0 |
| Key-mask sequence tables (Konami prefix, L/R alternation, u16 mask runs) | whole ROM | 0 genuine tables (only header/logo noise and zero-runs) |
| Pointers to `"debug"`/`"screenbg"` asset names | whole ROM | 0 each — dead level-layer labels, not a reachable menu |
| Reachable screens walked | 10 (§3) | 0 code-entry surfaces |

**Novel codes:** none possible; no validator to mint against. This is the §0.2 "no system"
negative, not a "dead code", "cut feature" or "gated feature" negative (guide §16.3): there is no
alphabet, table, handler or input surface at all.

**Bounds proven by rejection:** not applicable in the password sense. The closest dynamic bounds
are the button probes (§3): documented/common sequences produced only ordinary menu movement and
no distinct RAM flag, with a random-input control for comparison.

**Sibling independence:** the sibling's published passwords were searched literally in this ROM
(`Golden Tree`: 0 hits; no 4-token password UI on any of the 10 screens). The sibling is Full Fat
2002 (different game code, different engine); this ROM is Sirius Games 2006 `BLOE`. The
3rd party cheat indexes password list therefore does not apply here.

## 7. Validation evidence

* **Observed** — mGBA screenshots of all 10 screens; main menu has exactly 3 items; Options 2;
  pause 2; 4 save slots; level select 9 icons; no code entry anywhere. Konami/random probes
  changed nothing but cursor position.
* **Observed** — savestate `gbAs` diffs show no code-specific flag; change counts for Konami and
  control are comparable (§3).
* **Derived** — 72,804-string corpus and 2,627-string text bank contain zero cheat vocabulary;
  17 RTTI classes contain no cheat/debug class; no `0x04000130` literal and no mask-sequence
  table; no pointer to the inert `"debug"` layer name.
* **Inferred** — progression/awards (gold/silver/bronze, "You got the %s award!") are normal
  gameplay rewards, not unlockables; no unlockable content was observed or named in any string.
* **Reported, not followed** — prompt-injection text in a fetched 3rd party cheat index page (§2).

## 8. Unknowns

* The 512-byte EEPROM slot record layout was not exhaustively field-decoded; only the magic and
  the level/lives/score region were observed. No reward bit was shown to unlock content.
* Credits were not scrolled to the very last frame; no cheat-related text appeared in the portion
  viewed, and no such string exists in the text bank.
* The mGBA SDL GDB stub did not listen on :2345; all RAM evidence is from savestate diffs rather
  than live breakpoints.
* A semantic "code" implemented purely as an undocumented physics/input trick (e.g. an unusual
  movement technique) would not be a developer-intended cheat in scope and was not sought.

## 9. Tooling

* `md5sum`/`sha1sum`/`sha256sum`, `file`, `xxd` — Phase 0.
* `strings -t x -n 4`, Python `re`/`struct` — corpus census, literal searches, mask scans.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-arm` — checked the
  one `0x04000000` immediate candidate (false positive: floating-point code).
* mGBA 0.10.5 SDL under Xvfb `:315` + openbox; `xdotool` XTEST input; `scrot` screenshots.
* `ssdiff.py` (this work dir) — extracts the zlib `gbAs` chunk from mGBA `.ssN` PNG savestates
  (397,312 bytes for this 8 MiB ROM) and diffs RAM regions; used for RAM evidence.
* No REA/Ghidra decompilation was needed: the negative is established by enumeration, not by a
  candidate function.

**Legal:** no ROM image, graphics, audio or game text is redistributed here; only hashes,
addresses and findings are published.

**Cleanup:** all processes started for this run were stopped by PID (Xvfb, openbox, mGBA), and
the ROM folder was verified to contain only the `.gba` file (no `.sav`/`.ss*`).
