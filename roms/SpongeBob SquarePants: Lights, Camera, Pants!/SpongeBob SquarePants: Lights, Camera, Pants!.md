# SpongeBob SquarePants: Lights, Camera, Pants! (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `SpongeBob SquarePants: Lights, Camera, Pants!.gba` |
| Size | 4,194,304 bytes (0x400000, 4 MiB) |
| Header title | `SBSPLIGHTS` |
| Game code / maker | `BQQE` / `78` |
| Version | 0x00 |
| Entry word | `0xEA00002E` (stock branch to 0x080000C0 — **retail image, no cracktro/trainer**) |
| Fixed byte / checksum | 0x96 / complement 0xB6, header checksum 0x0000 |
| MD5 | `9a5a6c940bbf141d8c2838cf7c818080` |
| SHA-1 | `4c3c7ae6d1bf3d46bab640911aa2bb9094cc31f2` |
| SHA-256 | `86168d3e0b244383b0d864b24f75bbcd23d5f5120cf8de54e5d9b73b957fd6ea` |
| Embedded build stamp | `BUILD: 050728 1549 (Master)` at ROM `0x0803E6E0` (file `0x3E6E0`) |
| Save type | 512-byte SRAM; three 0x80-byte slots at 0x0/0x80/0x100, magic `6C 56 64 FC 22 DD CD AB` |

Embedded GBA-header scan: exactly **one** Nintendo-logo hit (file offset `0x4`, ROM `0x08000004`). No multi-game cartridge, no appended trainer, no second header (§5.4b). The `.sav` in the ROM folder is a disposable artifact created during this analysis; it contains only fresh/empty slots.

## 2. Executive summary

**This GBA title has no password or button-code cheat system.** It is a WayForward 2D platformer/minigame compilation on a different engine from the GameCube/PS2/Xbox/DS party game of the same name (§16.11). All seven widely published numeric "cheat menu" passwords for the console SKUs (`977548`, `893634`, `338903`, `089870`, `2229074466`, `548709`, `338903`) are **absent from this ROM** in ASCII, reversed ASCII, UTF-16LE, u32LE and u32BE — 36 literal searches, zero hits. 3rd party cheat indexes' GBA cheats page lists only gameplay **unlockables**, which matches the image.

The only developer-intended "cheat" surface is a **hidden debug menu / animation viewer / stage select** that 3rd party cheat indexes say is gated by a RAM byte (`0x030005D4`) written by a CodeBreaker device; the retail build had the `Select+Start` activation combo removed. I verified the combo is dead (goes to the normal File Select), enumerated all three gated scene values and the complete menu contents statically, and showed that forcing the gate byte yields only a black loading screen that falls back to the title — i.e. no usable in-game trigger exists. CodeBreaker/memory-edit codes are explicitly out of scope, so this is reported as a **bounded gated-feature negative**, not as a code.

The real in-scope unlockable system is a **Golden Star shop** at "Gill's Trailer" on the World Map. I enumerated both price tables (Easy and Normal), all 7 shop slots, all 8 unlockable minigames plus the Secret Driving Game, and observed the purchase gate rejecting 0 stars.

## 3. How to reproduce

* Emulator: mGBA 0.10.5, `SDL_AUDIODRIVER=dummy`, Xvfb `:315`, `openbox`, `mgba -3 <rom>`. Default SDL keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrow keys. Hold keys 120 ms.
* Boot sequence takes ~14–20 s (THQ → Nickelodeon → WayForward → title). Use savestates (Shift+F1..F9 save, F1..F9 load) — the title state makes every experiment one keypress.
* Path to every normal screen:
  `Title` →(Start)→ `File Select` →(A)→ `Difficulty Select (Easy/Normal)` →(A)→ long cutscene (mash A) → `Character Select` (Left/Right cycles SpongeBob/Patrick/Squidward/Mr. Krabs) →(A)→ second cutscene (mash A) → `World 1-1 gameplay` →(Start, Right, A)→ `World Map` →(Left/Right)→ `Gill's Trailer` →(A)→ `shop`.
  `Pause` = Start in gameplay (Resume/Quit); Quit returns to the World Map.
* Button combos tried at title (each from a fresh title savestate): `Select+Start`, `L+R+Start`, `L+R`, `L+R+A+B`, `A+B+Select`, `L+R+A+B+Select`, all-directions+Start. Only `A+B+Select+Start` had any effect — reset to the legal/copyright screen. None opened a hidden menu.
* Debug gate test: write `0x02` to RAM `0x030005D4` (mGBA GDB stub or savestate patch), then press Start. This is a **memory edit, not an in-game code**; used only as evidence here.

## 4. Address map

| Address (ROM unless noted) | File offset | Meaning |
|---|---:|---|
| `0x08000000` | 0x0 | Retail entry branch `0xEA00002E` |
| `0x0803E6E0` | 0x3E6E0 | `BUILD: 050728 1549 (Master)` |
| `0x0803E6AC` | 0x3E6AC | `DUMMY_PLAYER_OBJ failed!` (debug overlay) |
| `0x0803E700` / `0x0803E710` | 0x3E700 / 0x3E710 | `(Page 1 of 2)` / `(Page 2 of 2)` (debug utilities) |
| `0x0803E724`–`0x0803E854` | 0x3E724– | `World x Stars (xxx)`, `Level x Slates (xxx)`, `Difficulty: x`, `L Shoulder: World`, `R Shoulder: Level`, `Select: Difficulty`, `D-Pad L-R: Stars`, `D-Pad U-D: Slates`, `A Button: Start WxLx`, `B Button: Back to Menu`, `EASY`/`NORMAL` — the "Set World-Lvl" debug utility overlay (ASCII, no tile decode needed) |
| `0x0803E85C`–`0x0803E8D4` | 0x3E85C– | `wAnimID: %d`, `wObjMax %d`, `frame:%d`, `Frame:%d Cuts:%d Mem:%d` — "CHECK ANIMS" overlay |
| `0x08122000`–`0x08123500` | 0x122000– | Developer menu string bank, fixed `0x24`-byte records. Examples: `Screens` `0x0812237C`, `LEGAL` `0x081223A0`, `TITLE` `0x08122454`, `LOAD MENU` `0x08122478`, `CHAR. SELECT` `0x081224E4`, `CREDITS` `0x0812252C`, `Language` `0x08122598`, `Utilities:` `0x08122628`, `Set World-Lvl` `0x0812264C`, `CHECK ANIMS` `0x08122670`, `Unlockables` `0x081226DC`, `New Game` `0x081228D0`, `World 1-1` `0x08122910`, `Complete!` `0x08122E50` |
| `0x08168B84` | 0x168B84 | **Normal-mode shop prices**, `u16[6] = {10, 150, 300, 450, 600, 750}` |
| `0x08168B90` | 0x168B90 | **Easy-mode shop prices**, `u16[9] = {50, 0, 10, 50, 100, 150, 200, 250, 50}` |
| `0x08128410` | 0x128410 | `GIL: How're you doing team? I'll trade you items for your Golden Stars.` |
| `0x08128530` | 0x128530 | `GIL: This is a secret mini-game! What lies inside? Nobody knows!` |
| `0x08128610` | 0x128610 | `GIL: Not enough stars!` |
| `0x08128670` | 0x128670 | `GIL: Thank you!` |
| `0x08128750` / `0x081287B0` | 0x128750 / 0x1287B0 | `This returns you to the Control Room.` / `Sorry this item is unavailable.` |
| `0x08129A90`–`0x08129CD0` | 0x129A90– | `You have a new HIGH SCORE!`, `High Score:`, `Your Score:` (minigame result strings) |
| `0x0812AD70`–`0x0812AFB0` | 0x12AD70– | Unlock messages: Long Jump, Mermalair Training Room, Burger Bounce, Collection Game, Manray Chase, `Secret Driving Game!` |
| `0x08123210`–`0x081232F0` | 0x123210– | `You've unlocked Mrs. Puff's Driving School!`, `...Bikini Bottom minigame!`, `...Krusty Krab minigame!` |
| `0x08120F82` | 0x120F82 | `Shin'en Multimedia. Code: B.Wodok` — **audio-engine banner, not a cheat** (§16.11 keyword trap) |
| `0x080073F0` | 0x73F0 | Thumb function: `set_gate_byte(u8 v, u16)` — stores `v` to RAM `0x030005D4` (`ldr r1,[pc]; strb r4,[r1]`) |
| `0x08015AA4`, `0x08015AB4`, `0x08015ABE`, `0x08015AD6` | — | Gate-value comparisons: `cmp r0,#6` (stage select), `#5` (animation test), `#2` (debug menu), `#6`; mirrored at `0x080178E2`–`0x08017906` |
| `0x08015BB0`, `0x080138C4`, `0x0801D6A4` | — | Writers that clear the gate byte to 0 after a scene change |
| RAM `0x030005D4` | — | Gate / scene byte (CodeBreaker target `330005D4`) |
| RAM `0x03000658` | — | Pointer to scene struct; scene id at `[ptr+8]` (comparisons above) |

Savestate RAM mapping (mGBA `.ss1`, zlib `gbAs` chunk, 397,312 bytes): IWRAM `0x03000000`–`0x03007FFF` is state bytes `0x19000`–`0x21000`, EWRAM follows at `0x21000` (§16.13). Title→File Select changed 43,807 state bytes total, 3,386 of them in the IWRAM region (e.g. state `0x190E8`: `0x80 0xAC 0x1C` → `0x6C 0x13 0x1B`), proving which RAM window holds screen state. (mGBA's GDB stub in this build returns 0 for most RAM reads but reads ROM/I/O correctly; savestate diffing was the reliable RAM oracle.)

## 5. Algorithm

There is **no password validator to reimplement**. The relevant algorithms are:

1. **Shop price selection (derived from the two literal tables and observed on screen):**
   ```
   price[difficulty][i] = (difficulty==Normal) ? normal_prices[i] : easy_prices[i]
   normal_prices = [10, 150, 300, 450, 600, 750]   # 0x08168B84
   easy_prices   = [10,  50, 100, 150, 200, 250]   # 0x08168B90 (+ leading 50/0 terminator data)
   ```
   The five paid minigames are ×3 more expensive on Normal. The 10-star item is an extra life (price invariant). Slot 7 shows `--` (no item) and is not purchasable.
2. **Purchase gate (observed):** `if stars < price -> "GIL: Not enough stars!"` / on the final slot `"Keep collecting those Golden Stars!"`. With 0 stars every item was rejected.
3. **Debug gate (derived):** `scene == 2` → debug menu, `5` → animation test, `6` → stage select; the scene byte is set by `0x080073F0` and cleared by several scene-exit paths. No in-game input path sets 2/5/6: the published `Select+Start` trigger was removed from the retail build (3rd party cheat indexes + observed), and forcing the byte externally produced only a black load that reverted to title (observed).

## 6. Tables

**Shop slots (observed in both difficulties, Easy prices first):**

| Slot | Icon before purchase | Easy | Normal | Identity (from unlock strings / 3rd party cheat indexes GBA page) |
|---:|---|---:|---:|---|
| 1 | extra-life | 10 | 10 | Extra life (`GIL: This is an extra life.`) |
| 2 | `?` | 50 | 150 | Long Jump |
| 3 | `?` | 100 | 300 | Mermalair Training Room ("Merma Unlock") |
| 4 | `?` | 150 | 450 | Burger Bounce |
| 5 | `?` | 200 | 600 | Collection Game |
| 6 | `?` | 250 | 750 | Manray Chase / Police Chase |
| 7 | dimmed lock | `--` | `--` | no item / end of table |

The icons are deliberately tile-indexed `?` placeholders until bought (this is the "font/tile-indexed text bank" case, §11); the names are recovered from the ASCII unlock-message bank at `0x0812AD70`–`0x0812AFB0`, not from the shop tiles.

**Unlockable minigames (complete set, 9):**

| # | Name | Method | Evidence |
|---:|---|---|---|
| 1 | Long Jump | buy 50/150 stars | shop table + unlock string 0x12AD70 |
| 2 | Merma Unlock (Mermalair Training Room) | buy 100/300 stars | shop table + 0x12ADD0 |
| 3 | Burger Bounce | buy 150/450 stars | shop table + 0x12AE30 |
| 4 | Collect Game (Collection) | buy 200/600 stars | shop table + 0x12AE90 |
| 5 | Police Chase (Manray Chase) | buy 250/750 stars | shop table + 0x12AEF0 |
| 6 | DrivingSchool | complete Mermalair stage 2 | unlock string 0x123210; debug `Unlockables` list 0x1227D8 |
| 7 | Bikini Bottom | unlock string / debug list 0x1227FC | — |
| 8 | Krusty Krab | complete S.S. Rest Home stage 3 | unlock string 0x1232D0; debug list 0x122820 |
| 9 | Secret Driving Game | **view the Credits to the end** | 0x12AF50 / 0x12AF90; 3rd party cheat indexes GBA page |

Roles (Lookout, Motorcycle Cop, Stand-In, Waiter) are awarded for clearing specific stages; they are cutscene roles, not cheats.

**Published console-SKU codes — verification ledger (all ABSENT from this ROM):**

| Code | ASCII | reversed | UTF-16LE | u32LE | u32BE |
|---|---|---|---|---|---|
| `977548` | 0 | 0 | 0 | 0 | 0 |
| `893634` | 0 | 0 | 0 | 0 | 0 |
| `338903` | 0 | 0 | 0 | 0 | 0 |
| `089870` | 0 | 0 | 0 | 0 | 0 |
| `2229074466` | 0 | 0 | 0 | 0 | 0 |
| `548709` | 0 | 0 | 0 | 0 | 0 |

## 6b. Enumeration

**Space definition / counts.** There is no code space to enumerate. The bounded search that establishes this:

| Search space checked | Size | Result |
|---|---:|---|
| `strings -t x -n 4` keyword hits for password/cheat/code/secret/unlock/debug | 72,949 lines scanned | 0 password/cheat validators; 1 `Code:` hit = Shin'en audio banner; all `unlock` hits are gameplay unlock messages |
| Console-SKU numeric code literals × encodings (§6 table) | 6 codes × 6 encodings = **36 searches** | **0 hits** |
| Embedded GBA headers (Nintendo-logo scan) | whole 4 MiB | **1** (single retail image) |
| Hidden button combos at title | **7** distinct combos | 0 hidden menus; 1 reset to legal screen |
| Debug scene values gated by RAM `0x030005D4` | **3** values: 2 (menu), 5 (anim test), 6 (stage select) | all require external memory write; retail combo removed; forced value yields black screen then title |
| Debug menu entries (developer-intended, from `0x08122000` bank + 3rd party cheat indexes) | **Page 1: 5 headers + 20 stages; Page 2: 11 screens + 8 utilities** | 44 entries enumerated, none reachable by in-game input |
| Shop slots | **7** (6 priced + 1 terminator) × 2 difficulty tables | fully enumerated; observed in-game in both modes |
| Unlockable minigames | **9** | fully enumerated (5 purchased, 3 stage-cleared, 1 credits) |

**Novel code (§0.2): not applicable — the game has no code system.** The analogous novel result is the previously unpublished **Normal-mode price set**: the published 3rd party cheat index list gives only the Easy-mode values (50/100/150/200/250). I derived `10/150/300/450/600/750` from ROM `0x08168B84`, predicted Normal mode would be exactly ×3, selected Normal in-game and **observed** every price on the shop screen. This combination appears in no cheat list I found.

**Bounds proven by rejection (observed):**
* 0 Golden Stars → every shop item rejected (`GIL: Not enough stars!` / `Keep collecting those Golden Stars!`). The purchase path is gated on the star counter.
* Map entries `Final Game`, `Driving School`, `Mini Game 1–5`, `Sound Stage`, `Goo Lagoon`, `S.S. Rest Home`, `Krusty Krab` all display `Locked` and do not open when A is pressed — gated by save bits / star purchases.
* Debug gate: forcing `0x030005D4 = 2` externally does **not** produce a usable menu in the retail image (black load → title), so `2/5/6` are out-of-band values with no in-game producer.
* `Select+Start` (the documented prototype trigger) was pressed at the title screen and produced the ordinary File Select — the combo is removed in this build.

**High-score screens:** the strings `You have a new HIGH SCORE!` / `High Score:` / `Your Score:` exist at `0x08129A90`–`0x08129CD0`, but the screens that display them are inside the star-gated minigames. With 0 stars I could not enter a minigame, so the high-score *screen* was not observed; this is a bounded gated negative (purchase gate proven by rejection above), not an untested feature.

## 7. Validation evidence

* **Observed (emulator):** every screen in the reproduction path; both shop price sets; "Not enough stars!"/"Keep collecting those Golden Stars!"; `Locked` map entries; all 7 button combos; external gate write → black screen → title; savestate RAM diffs between screens.
* **Derived (disassembly):** gate setter `0x080073F0`, gate comparisons `0x08015AA4`/`0x080178E2`, scene struct pointer `0x03000658`, the two price tables, the `0x24`-byte debug-menu string records, the debug-overlay strings and build stamp.
* **Inferred / external (data, not instructions):** a 3rd party cheat index's description of the three CodeBreaker-gated scenes and the removed combo; 3rd party cheat indexes GBA unlockable list. Fetched pages were treated strictly as untrusted data. No prompt-injection payload was encountered.
* **Confidence:** high for "no password/button-code system in this GBA SKU"; high for the shop/unlockable enumeration; medium for the exact identity of unlockable slots 7–8 (names come from the debug string bank and unlock messages, not from an observed purchase).

## 8. Unknowns

* The exact save-bit offsets for the 9 unlockables — the disposable `.sav` contains only empty slots; I did not accumulate 50+ Golden Stars to observe a purchase writing a bit.
* Whether one could reach a high-score screen by fully playing/clearing a stage to earn stars (not done; the gate was proven instead).
* Whether the debug-menu scene could be made to render by holding the gate byte with a real CodeBreaker device — out of scope, and a one-shot RAM write produced only a black screen.

## 9. Tooling

* `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings -t x`, `grep -abo`, Python 3 (`struct`, `zlib`, `PIL`).
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for Thumb disassembly; Capstone for PC-relative literal and immediate-compare scans.
* `webfetch`/`websearch` for 3rd party cheat index pages; all fetched content treated as untrusted data.
* mGBA 0.10.5 under Xvfb `:315` + openbox; `xdotool` XTEST input; `scrot` screenshots; savestate `gbAs`/zlib patcher (`patchstate.py`) and GDB-remote client (`gdbrc.py`) written in `/tmp/spongelights/`.
* Legal: no ROM or copyrighted assets are redistributed; only addresses, hashes, algorithms and findings are published. Analyzer processes and generated `.sav`/`.ss*` artifacts were removed at the end (see final reply).
