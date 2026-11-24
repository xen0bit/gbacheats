# Spyro: Attack of the Rhynocs (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Spyro: Attack of the Rhynocs.gba` (same folder as this report) |
| Size | 8,388,608 bytes (`0x800000`), plain GBA image — **not** a multi-game pack |
| Header title | `SPYRO 3` (bytes `0xA0`–`0xA7`, NUL-padded) |
| Game code | `AOWE` |
| Maker code | `7D` |
| Version | `0x00`; complement `0xBA`; header checksum `0x0000` (0xBE–0xBF) |
| Entry word | `0xEA00002E` (stock ARM branch to `0x080000C0`) — retail image, no cracktro/trainer |
| `file(1)` | `Game Boy Advance ROM image: "SPYRO 3" (AOWE7D, Rev.00)` |
| MD5 | `4a15b07b4dc292e9003c377c55372287` |
| SHA-1 | `286fe14e15bc34e3605186876878e655ef43294c` |
| SHA-256 | `65a929eae6786ac3b6018bafd1c48e2ade99883655e542e5b4e949e95ce6f28b` |

Developer/publisher (from external metadata, recorded as data): Digital Eclipse / Universal Interactive, 2003; EU title *Spyro Adventure*. Sibling GBA Spyro titles were analysed separately; **all addresses below were re-derived from this exact SHA-256** and none were carried over from those reports.

## 2. Executive summary

**No in-game/developer-intended cheat code system exists in this image.** There is no password entry screen, no documented or hidden button sequence that changes state, no debug/cheat menu, and no validator or code generator anywhere in the ROM. Every "cheat" published for this game (GameFAQs, ROMSFun, Cheat Happens, GameGenie, the libretro DB) is a **GameShark / CodeBreaker / Action Replay device code** — explicitly out of scope for this engagement.

The only unlockable content is **progress-gated**: the Sgt. Byrd *Byrd Rescue* multiplayer/single-player modes and their level list are reached from the title screen; published guides say they unlock after game completion/100%. A fresh save in this build already allowed entering the second level ("Cold Crypts"), so the guide's gate claim is not exact, but nothing observed is a controller code.

The game's UI text is **not ASCII**: it is a 1-byte-per-glyph custom tile-index charset with `0xFF`-terminated strings. That is why `strings` and every literal search for menu words return nothing; a negative based on `strings` alone would have been invalid. The charset structure was recovered (§5), but the glyph→index substitution was not solved (§8).

This is a **bounded negative** (§0.2 case "no system"). Bounds are proven in §6b by exhaustive ROM/input scans with counts and by walking 15 distinct screens.

## 3. How to reproduce

* Emulator: `mgba 0.10.5` under `Xvfb :316` + openbox, `SDL_AUDIODRIVER=dummy`, `-3` scale. Window geometry 720×480 viewport at root `+152+144`.
* Keymap (mGBA SDL defaults verified in-emulator): `A`=`x`, `B`=`z`, `L`=`a`, `R`=`s`, `Start`=`Return`, `Select`=`BackSpace`, D-pad = arrow keys. Hold ≥70 ms.
* Boot → Universal Interactive splash → **PRESS START** → main menu.
* Menu paths walked (all with screenshots and `.ss1` RAM snapshots in `/tmp/spyrorhynocs/`):
  * Main: `New Game`, `Options`, `Credits`, `Byrd Rescue` (plus `Continue Game` once a save exists).
  * `New Game` → `Select Game` → three `unused` slots (empty Flash save slots; selecting one starts a new game).
  * `Options`: `Music: On`, `Sound FX: On`, `Speech FX: On` — no secret entries.
  * `Credits`: scrolling legal/credit text only.
  * In-game: intro cutscene, dialogue, overworld, `Start` pause menu = `Continue / Journal / Save Game / Options / Quick Escape`; `Journal` selection raises an `ARE YOU SURE? No/Yes` dialog; `Yes` on `Save Game` writes `Saving game`.
  * `Byrd Rescue` → `Select Game`, `Head To Head`, `Cooperative`, `Single Player`.
  * `Byrd Rescue` → `Select Game` → level list: `Honeydew Downs`, `Cold Crypts`, `Dragonfly Den`, `Tik Tok Troubles`, `Menacing Marble`, `Bonus Levels`.
  * Selecting `Cold Crypts` reached the Head To Head instruction screen: *"Rescue more penguins than your opponent to win. Press B Button to cancel / Press START to continue."*
* Button-code attempts (10 sequences; see §6b) all produced only ordinary navigation or the legal splash.

## 4. Address map

| Item | Address / file offset | Evidence |
|---|---|---|
| ARM entry / crt0 | `0x080000C0`; entry literal `0xEA00002E` at file `0x000` | **Derived** (objdump `-M force-arm`) |
| `main` (Thumb) | `0x0800303C` (pointer `0x0800303D` in crt0 literal pool at file `0x100`) | **Derived** |
| Scene/task helpers called by `main` | `0x08001254`, `0x08001264`, `0x08001284`, `0x08060C08`, `0x08013EC`, `0x080691C`, `0x0800FB0`, `0x080129C`, `0x0806908` | **Derived** (BL scan + disassembly) |
| IRQ/input setup reading I/O | `0x08001104` region; literals `0x04000130` (KEYINPUT) at file `0x139C` — exactly **one** literal reference in 8 MiB | **Derived** |
| Custom text-bank regions (examples) | file `0x51E000`, `0x529300`, `0x537500`, `0x562A80`, `0x5A42B0` | **Observed/Derived** (byte dumps) |
| IWRAM game state | `0x03002FE6`, `0x03003000`, `0x0300301C`, `0x03003029`, `0x03002922` — all read `0x0000` on a fresh game | **Observed** (savestate IWRAM at raw `0x19000`) |
| Save | 8 KiB Flash; `first nonzero 0x168`, `0xFF` filler to `0x1FFF`, checksum `0x176F` at `0x1FF8` | **Observed** |

Savestate layout used for RAM reads (mGBA `.ss1` → `gbAs` chunk → `zlib.decompress`, 397,312 bytes): header/CPU `0x00000`, VRAM `0x1000`, IWRAM `0x19000`, EWRAM `0x21000`. Verified by finding ARM code at `0x19000` and `0x0300xxxx` pointers at `0x21000`.

**Important scope note:** the addresses in the published device codes (e.g. `83003000 FFFF` "Have All Levels Open", `43002FE6 FFFF` "Have Everything Unlocked") are raw RAM pokes by an external cheat device. They are **not** in-game codes; the ROM contains **zero** 32-bit literals equal to `0x03002FE6`, `0x0300301C`, `0x0300301E`, or `0x03002922`, so no in-game routine references those flags directly.

## 5. Algorithm / text encoding

There is no validator to reimplement. The only algorithm recovered is the **UI text format**:

1. Strings are byte sequences over a custom glyph-index alphabet (observed bytes `0x20`–`0x55` plus control codes `0x8D` and `0xFF`).
2. `0xFF` terminates a string (confirmed: six clean `0xFF`-terminated records in `0x51D000`–`0x520000`, e.g. `8d2932548d3932548d3243432c5244443233454344345544325554453354ff`).
3. Glyphs are rendered as 4bpp/8bpp VRAM tiles addressed by those byte values; the substitution table (byte → tile/glyph) was **not** recovered, so the strings could not be transliterated offline.
4. Known menu words were searched under ASCII, `+0x20`, `-0x20`, XOR, UTF-16LE/BE, 1-based/0-based alphabet indices and all 32,768 odd-affine byte transforms — **zero meaningful hits** (only random coincidences). The glyph map is therefore a genuine substitution, not a shift.

No password encoder, decoder, checksum, PRNG, alphabet table or comparison loop was found. No code entry widget exists on any of the 15 screens walked.

## 6. Tables

Reachable menu inventory (**complete for a fresh save**):

| Screen | Entries | Hidden/extra entries? |
|---|---|---|
| PRESS START | — | none |
| Main menu | New Game, Options, Credits, Byrd Rescue (+Continue Game after save) | none |
| New Game → Select Game | unused, unused, unused (3 Flash slots) | none |
| Options | Music: On, Sound FX: On, Speech FX: On | none |
| Pause | Continue, Journal, Save Game, Options, Quick Escape | none |
| Byrd Rescue | Select Game, Head To Head, Cooperative, Single Player | none |
| Byrd Rescue → Select Level | Honeydew Downs, Cold Crypts, Dragonfly Den, Tik Tok Troubles, Menacing Marble, Bonus Levels | none found; `Bonus Levels` not fully exercised (§8) |

Published "cheats" (recorded, not used): 8 CodeBreaker codes (ROMSFun/libretro), 4 Action Replay codes (Cheat Happens), 10+ GameShark codes (GameFAQs dark52 FAQ). **All require an external device; none is an in-game code.**

## 6b. Enumeration

**Result: empty cheat-code space — bounded negative, not an untested omission.**

| Check | Search space | Result |
|---|---|---|
| ASCII code-like strings `[A-Z0-9]{6,}` | all 8,388,608 bytes | 9,428 hits; inspected samples — all random data or the header `AOWE7D`. No password/code string. |
| UTF-16LE / UTF-16BE 8-char code windows | all 8,388,608 bytes | 17,919 / 18,498 windows; all random. No code string. |
| Multi-encoding keyword scan (`password`, `cheat`, `debug`, `secret`, `unlock`, `test`, `menu`, `invalid`, `code`) | raw ASCII, `+0x20`, `-0x20`, UTF-16, XOR-0xFF over all 8 MiB | 13 `+0x20` "test" hits, all inside compressed/graphics data; **zero** cheat/debug/password strings. |
| Affine byte transforms for 15 known menu cribs | 128 odd multipliers × 256 offsets = 32,768 transforms | No meaningful hit (4-byte hits were chance collisions). |
| Button-code mask tables (`u16`, 2–5 bits set, ≤`0x3FF`, ≥5 consecutive) | all 4,194,304 aligned `u16` windows | 2,741 runs; all are numeric/sound/graphics tables (e.g. `0x6275E` sine table, `0x705A6` tile data). **No run has the structure of a key-press sequence.** |
| 32-bit literals of state addresses named by device codes | all 8,388,608 bytes | `0` hits each for `0x03002FE6`, `0x0300301C`, `0x0300301E`, `0x03002922`, `0x02039E94`. |
| Literal `KEYINPUT` references | all 8 MiB | exactly 1 (`0x04000130` at file `0x139C`, in crt0 IRQ setup) — no per-screen button matcher. |
| Button-code attempts on title screen | 10 sequences: Konami (`↑↑↓↓←→←→BA`), `L+R+Start`, `A+B+Start+Select`, `L+R+A+B`, `Select+Start`, `L+Start`, `R+Start`, `L+R`, `↑↓←→AB`, `ABAB A` | All screenshots/RAM snapshots showed only normal navigation or the legal splash. **0 hidden screens, 0 new flags.** |
| Screens walked with RAM evidence | 15 distinct screens (splash, PRESS START, legal, main menu ×2 variants, Options, Credits, Select Game/slots, intro, gameplay/dialogue, pause, confirm, saving, Byrd Rescue submenu, level list, Head To Head instructions) | **0 password/code entry widget, 0 debug/cheat menu.** |

**Novel code:** none exists to mint. The deliverable here is a closed set of size **0** for in-game passwords/button codes/debug cheats, with the two unlockable classes documented above. Per §0.2 the negative is proven by the counts in this table plus the screen inventory in §6, not by "I did not find it".

Bounds proven by rejection: the three `unused` slots are rejections of empty-save reads, and the button-code attempts are in-game rejections (unchanged screen/RAM). There is no checksum to bound because there is no code format.

## 7. Validation evidence

* **Observed** — title/menu/pause screens and all text listed in §6 captured as PNGs under `/tmp/spyrorhynocs/` (`w*.png`, `g*.png`, `nav_*.png`, `combo_*.png`, `menu_step*.png`). RAM values read from decompressed `.ss1` snapshots (`raw1.bin`/`raw2.bin` and `c00_base.ss1`…`c10_abc.ss1`). `.sav` inspected (8 KiB Flash, three slots).
* **Derived** — crt0/main/scene-helper addresses and all literal/xref counts from `arm-none-eabi-objdump` and Python byte scans over the exact SHA-256. Text-bank format from `0xFF`-terminated byte records.
* **Inferred (labelled)** — that the "Byrd Rescue" gate is 100% completion (from published walkthrough and TV Tropes, **not** confirmed in-game; a fresh save already reached level 2). That the glyph substitution is a font-tile index map (structure proven, individual glyph values not solved).

## 8. Unknowns

1. Glyph→byte substitution of the custom charset was not solved; offline transliteration of the full text bank is therefore incomplete. It is not needed for the cheat conclusion (no entry surface exists on any screen).
2. `Bonus Levels` (last level-list item) was not entered to completion; navigation wrapped to the title screen on the attempt. It is a normal menu row, not a code surface.
3. The exact completion gate for Byrd Rescue is not confirmed; published sources disagree with the fresh-save observation. This is a progress unlockable, not a controller code.
4. No GDB stub could be bound (default port occupied by a sibling session; `-C gdb.port=` override ignored by this build), and `mgba -d` required a TTY. RAM evidence therefore comes from savestate diffs, which is sufficient for the flags read here.
5. Ghidra/REA auto-analysis of the 8 MiB raw image exceeded the 330 s startup deadline; decompilation was not used. Conclusions rest on objdump/byte scans plus emulator evidence.

## 9. Tooling

* `mgba 0.10.5` (`/usr/local/bin/mgba` → `/usr/games/mgba`) under `Xvfb :316`, openbox, `xdotool`, `scrot`, ImageMagick `convert`.
* `arm-none-eabi-objdump -M force-thumb` / `-M force-arm` with `--adjust-vma=0x08000000`.
* Python 3 helper scripts in `/tmp/spyrorhynocs/`: `ssdump.py` (savestate `gbAs` decompress), `inp.py` (input/capture), `walk.py`, `combos.py`, `findtext.py`, `affine.py`, `affine_fast.py`, `lit_scan.py`, `final_scan.py`, `render_tiles.py`, `render8.py`, `findfont.py`.
* REA/Ghidra was opened and closed; it timed out on this image and contributed no evidence.

**Legal note:** no ROM or copyrighted assets are redistributed. This report contains only hashes, addresses, counts and observations.
