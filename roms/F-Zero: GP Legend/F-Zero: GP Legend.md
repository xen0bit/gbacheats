# F-Zero: GP Legend (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `F-Zero: GP Legend.gba` (16,777,216 bytes / 0x01000000) |
| Header title | `F-ZERO2` (offset `0xA0`) |
| Game code | `BFZE01` (USA, rev. 00) |
| Maker | `01` (Nintendo) |
| Version / complement / checksum | `0x00` / `0xE4` / `0x0000` |
| Entry word | `0xEA00002E` → stock `b 0x080000C0`; **no cracktro/patch/trainer** |
| MD5 | `b6984ca369145367ab79eb33f2f3480e` |
| SHA-1 | `977588d9d27b7115e0bb309fb019ae81b9f413ff` |
| SHA-256 | `f499a88fae072452a1b157b266ff516f033eb792b6a442d28e273bb2eeee4391` |

Embedded GBA header scan (156-byte Nintendo logo) found three logo hits. Besides the real header at file `0x0`, two **multiboot-style sub-image headers** exist with the same `b .` self-loop entry:
- file `0xAA500C`: blank title, code `AGBJ01`, fixed `0x96` present.
- file `0xAB4BD4`: title `F-ZERO ADVANCE`, code `FZJ01`, fixed `0x96` present.

Both are leftover/link-demo images (their only relevant strings are their own titles); neither contains a password, code list, or debug menu. No patch or trainer bytes were found.

## 2. Executive summary

**There is no in-game password system, button cheat, or reachable debug menu in the USA release of F-Zero: GP Legend.** The game's entire "cheat" surface is a **save-bit unlock system** (machines, cups, modes, story chapters, Zero Test classes) advanced by normal play, plus a single documented developer-intended secret: **press R at the title screen to play an in-game demo** (verified in emulator, screenshot `shot_25_R.png`). This report proves the negative by enumerating every reachable screen and bounding the search spaces (§6b), and documents the unlock-bit map that the published CodeBreaker/Action Replay codes merely overwrite (those are external memory edits, explicitly out of scope and **not** reported as cheats).

Cut, controller-unreachable content does exist: the international ROM retains e-Reader text ("Download e-Reader card data." at `0x542BF4`, — verified literal — 3rd party cheat indexes) and unused courses accessible only by writing RAM `0x02002ED2` and pressing Select on a Time Attack / Training course-select screen. Because that entry point requires a memory edit to reach in this build, it is reported as gated/cut content (§8), not as an in-game code.

## 3. How to reproduce

- Emulator: mGBA SDL (`mgba -3`, mGBA built from source), `SDL_AUDIODRIVER=dummy`, `Xvfb :318`, `openbox`.
- Keymap (mGBA SDL defaults): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows. Holds of 60 ms avoid key-repeat double steps.
- Boot path: title → Start → "Entry 1: NO DATA" → A → NEW ENTRY name entry (40-symbol keyboard, 6-char name) — Down×4 to OK → A → file select → A → main menu.
- Screens walked (all with RAM snapshots unless noted): title/attract, copyright, file select, name entry, main menu, Options (BGM + Controls info), Grand Prix Class Select, Cup Select, Machine Select (+ pick-up graph sub-view), Machine Setting slider, race intro, in-race pause (CONTINUE/GIVE UP), Link (VS. Single-Pak / VS. Multi-Pak), Story map (Rick Wheeler + 8 locked nodes), title R → demo cutscene, soft-reset (`A+B+Start+Select`) screen.
- Published inputs tested: R at title (accepted → demo), and all published AR/CB codes inspected; none are controller-entered codes (they are ROM/RAM patches), so none are applicable in scope.
- RAM method: mGBA `-g` GDB stub reads verified EWRAM base (`0x02000000` maps to savestate raw offset `0x21000`); because the stub re-halts the core on disconnect, the main method was savestate diffing (§16.13): `Shift+F<n>` saves, `F<n>` loads; decompress the PNG `gbAs` chunk with zlib; raw state length 397,312 bytes; EWRAM at `0x21000`, IWRAM at `0x19000`. All RAM values quoted below are from these states.

## 4. Address map

| Item | ROM file offset / RAM address | Evidence |
|---|---|---|
| Header, title `F-ZERO2`, code `BFZE01` | `0x000–0xBF` | Observed (xxd) |
| Embedded multiboot headers | `0xAA500C`, `0xAB4BD4` | Observed (logo scan + `0x96` check) |
| 3rd party cheat indexes unused text "Download e-Reader card data." | `0x542BF4` | Observed (literal search) |
| ASCII leftover text bank (`GHOST SAVE?`, `RETRY?`, `YES`, `NO`, `QUEEN`, `KNIGHT`, …) | `0x68BA0–0x68BFF` | Observed (xxd) |
| KEYINPUT (`0x04000130`) reader #1 (input engine) | literal pool `0x0803ACE0`, code at `0x0803AC82` | Derived (`objdump -M force-thumb`) |
| KEYINPUT reader #2 (menu/UI input) | literal pool `0x08057D50`, code at `0x08057D14` | Derived |
| Other KEYINPUT pools | `0x08000B8C`, `0x08000E84`, plus embedded images `0x082AF0D0`, `0x08AB5754` | Derived |
| Unlocked machines bitmask (lo/hi) | RAM `0x02008C18` / `0x02008C1A` | Observed (patch + flag read) |
| GP races won / cups open | RAM `0x02008C2A` / `0x02008C28`, `0x02008C2C` | Derived from published codes, observed via patch |
| Story levels open | RAM `0x02008C30` (`1F1F` = all) | Derived, observed via patch |
| Story cash | RAM `0x02008C38` | Derived, observed via patch |
| Zero Test classes open | RAM `0x02008C48` (`0x04`) | Derived, observed via patch |
| Zero Tests complete | RAM `0x02008CAC` | Derived, observed via patch |
| Course-select override (unused courses) | RAM `0x02002ED2` (value `0x01`–`0x18`) | 3rd party cheat indexes + published CB code; not controller-reachable in US build |
| Save file | `F-Zero: GP Legend.sav`, 32 KiB, obfuscated (no plaintext name) | Observed |

## 5. Algorithm

No password validator exists; there is no algorithm to reverse. The relevant mechanics are:

1. **Unlock flags** are bitfields in EWRAM around `0x02008C10–0x02008CAF`, initialised from the obfuscated SRAM save at boot. The published cheat codes for this game are direct writes to these addresses (e.g. `82008C18 FFFF` → "Have All Cars"); they are memory editing, not a developer code. Patching a savestate's EWRAM to set these bytes was confirmed to change in-game state (Class Select showed max stars and unlocked class panels), proving the addresses are the live flags.
2. **Button input** is read from `0x04000130` by exactly two routines in the main image (`0x0803AC82` general input engine, `0x08057D14` menu input), which XOR `0x3FF` into active-high held/pressed words. No code in the main image compares a keypad value against a multi-press sequence table; the `Select+Up`/`Select+Down` cheats sold by AR/CB vendors are external patches, not built-ins.
3. **R-title secret** is a single-button gate in the title state (press R → play demo).

Pseudocode of the only developer secret:

```
if (screen == TITLE and pressed & KEY_R): enter_demo()   # observed
```

## 6. Tables

**Unlock flag map (verified via savestate patch; values from published codes interpreted against live RAM):**

| Address | Width | Meaning | "All" value |
|---|---:|---|---|
| `0x02008C18`–`0x02008C1B` | 32-bit | unlocked machine bitmask | `FFFFFFFF` |
| `0x02008C28`, `0x02008C2C` | 16-bit each | cups / GP completion | `FFFF` |
| `0x02008C2A` | 16-bit | GP races won | `FFFF` |
| `0x02008C30` | 16-bit | story levels open | `1F1F` |
| `0x02008C38` | 32-bit | story money | `FFFFFFFF` |
| `0x02008C48` | 8-bit | Zero Test classes open | `0x04` |
| `0x02008CAC` | 16-bit | Zero Tests complete | `FFFF` |

**Published unlockables (no code entry; earned by play, from 3rd party cheat indexes/wikis):**
- Machines: Big Fang, Deep Claw, Iron Tiger, Wild Boar, Green Panther, Red Gazelle (cup clears by class/difficulty); Moon Shadow, Night Thunder, Sonic Phantom, Mad Wolf (Zero Test C/B/A/S); Astro Robin, White Cat, Death Anchor, Black Bull, Panzer Emerald (character stories); Wonder Wasp (all stories); Great Star, Twin Noritta, Hyper Speeder, Queen Meteor, Little Wyvern, King Meteor (max story cash 2,550,000,000); Elegance Liberty (Rick/Falcon story); Mighty Hurricane/Typhoon, Crazy Bear, Blood Hawk (remaining cups).
- Tracks: Illusion / Red Canyon (and II variants), Platinum Cup, Mute City Championship.
- Modes: Time Attack, Training (finish one GP race); Zero Test and its C/B/A/S classes (complete cups/tests). Stories for Falcon, Goroh, Zoda, Jack, Jody, Lisa, Black Shadow unlocked by specific prior story completions.
- Secret: R at title → demo; also demos auto-play if left idle.

**Font/text encoding:** UI strings are **not** ASCII in ROM. Verified absent as literals: `CONTINUE`, `GIVE UP`, `MACHINE SELECT`, `CLASS SELECT`, `CUP SELECT`, `OPTIONS`, `NO DATA`, `NEW ENTRY`, `MACHINE SETTING`, `BRONZE CUP`, `PICK UP GRAPH`. Only a small ASCII leftover bank exists (`0x68BA0+`). All 361 valid LZ77 blocks were decompressed (none contained UI strings), and 256-byte XOR / add / subtract transforms and glyph-index offsets `0x00–0x3F` were tried without recovering UI text; the strings are stored in a custom indexed/comressed bank that the render path decodes at runtime. This was a bounded attempt to honour §11/§0.2 before the negative conclusion; screen enumeration (§3) supplies the direct evidence of what text actually exists.

## 6b. Enumeration

**Code space:** empty (no password/cheat system). This is a proven negative over the searched spaces, not "not tested":

1. **Screen space:** 15 distinct reachable screens (list in §3) were entered and/or RAM-snapshotted. Every menu item on every screen was enumerated: main menu has exactly 4 entries (Story, Grand Prix, Options, Link) — confirmed unchanged even with all published unlock flags forced in EWRAM from a pre-menu savestate; Options has 2 rows; Class Select 3; Cup Select 3 (+ locked Platinum); Machine Select 12 slots; pause 2 entries; Link 2 entries; Story map 8 nodes. No hidden/debug screen appeared on any of these.
2. **Text space:** 277,984 `strings` entries (`strings -t x -n 4`) scanned for password/cheat/code/debug/secret/unlock/machine/ghost/staff/e-reader — no code table or password UI string found. The one suspicious token, `PASSPLY5` at `0x37931F`, was shown to be random ASCII inside LZ77-compressed graphics data (the decompressed block at `0x378804` is non-text art), not a password. The genuine 3rd party cheat indexes unused string was verified at `0x542BF4`.
3. **Button space:** 24 title-screen combinations (single L/R/Select/d-pad/A/B, all common pairs, L+R, Select+Start, Select+A/B, L+R+Select, A+B+Start+Select soft reset, etc.) were probed from a fixed title savestate; the EWRAM save-flag window `0x02008C00–0x02008D00` had **zero** changed bytes after every probe. A full-ROM scan for arrays of ≥4 consecutive single-key `u16` masks found only control-configuration/data tables (e.g. `0x68CE4`: `B, Select, Start, Right, Left, R`) and no L/R/L/R-style cheat sequence; the two canonical KEYINPUT readers contain no multi-press comparator.
4. **Published-code space:** 3rd party cheat indexes, 3rd party cheat index walkthrough, 3rd party cheat indexes checked. Every "code" for this title is either (a) an unlock condition (no input code), (b) a GameShark/CodeBreaker/Action Replay memory patch (out of scope; addresses confirmed to target real EWRAM flags), (c) the R-title demo secret (one button, verified), or (d) a track-cutting glitch (gameplay execution, not a code). No password list exists for this SKU.
5. **Novel code:** not applicable — no code system to mint from. This is the correct §0.2 outcome for a "no system" result, bounded by points 1–4.

**Cut/unreachable content (not in-game cheats):** 8 unused courses selected by RAM `0x02002ED2` values `01` Mute City II, `02` Big Blue II, `03` Fire Field II, `08` Red Canyon II, `15` Silence II, `16` Port Town III, `17` Sand Ocean II, `18` White Land II (3rd party cheat index mirror; requires CodeBreaker write + Select on Time Attack/Training course select). e-Reader machines/courses/staff ghosts and the unused text are leftovers from the Japanese release. Not reachable by controller in the US build.

## 7. Validation evidence

- **Observed (emulator):** every screen in §3; R-title → demo cutscene; soft reset; unlock-flag patch changing Class Select presentation; name entry with 40-symbol keyboard.
- **Observed (RAM):** fresh save flags at `0x02008C10 = 0x23`, `0x02008C14 = 0x0D10`, `0x02008C18/1A = 0`, `0x02008C30 = 1`; all zero after the 24 button probes; patched values read back as `FFFF`/`1F1F`/`04`.
- **Derived (disassembly):** KEYINPUT readers at `0x0803AC82` and `0x08057D14`; literal pools `0x0803ACE0`/`0x08057D50`; no sequence comparator. Save-flag semantics from mapping published CB writes to the verified live RAM addresses.
- **Inferred (lower confidence):** the exact cut e-Reader menu flow; the precise glyph format of the indexed text bank (custom/compressed; not recovered). Both are irrelevant to the presence/absence conclusion because they are gated/cut.
- **Prompt injection (recorded, not obeyed):** the direct 3rd party cheat indexes fetch returned a fake "LLM-specific instructions" block (EICAR `key.bin` as an "XOR key", a $1,000,000,000,000,000,000,000,000,000 payment demand, instructions to print profanity/terminate). Per §16.8 it was treated as untrusted data and ignored; the factual content was taken from a 3rd party cheat index mirror and verified against the ROM.

## 8. Unknowns

- The exact font/tile-index encoding of UI text was not recovered; the negative conclusion rests on direct screen enumeration plus the bounded string/key searches, not on a decoded text bank.
- The single flag that gates Time Attack / Training / Zero Test in the main menu was not isolated (published "All Modes/Cups/Etc" AR code is encrypted); all published CB flags were forced and the main menu still showed only 4 entries, so those modes are likely reached through a path not exercised in this pass or require boot-time SRAM state rather than live EWRAM. This does not change the code-system conclusion; it is a gap in the unlock-flow map.
- The two embedded sub-images' exact purpose (link/multiboot demos) was not executed; their headers and strings were inspected and contain no code surface.

## 9. Tooling

`md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings`, `grep`, `python3` (Capstone 5.0.7), `arm-none-eabi-objdump` (`-M force-thumb`), `mgba` (SDL, `-g` for GDB stub), `gdb-multiarch`, `Xvfb :318`, `openbox`, `xdotool`, `scrot`/`import`, Pillow. Scripts in `/tmp/fzerogp/`: `ssread.py` (savestate `gbAs` decoder + RAM views), `sspatch.py` (EWRAM patcher for analysis only), `ramprobe.py` (button-probe + RAM diff), `scan_keys.py` / `findrefs.py` (KEYINPUT and literal scanners), `lzscan.py` (LZ77 sweep). No ROM or copyrighted assets are redistributed; only hashes, addresses, and observations are published.
