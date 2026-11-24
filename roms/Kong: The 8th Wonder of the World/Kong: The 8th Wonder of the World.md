# Kong: The 8th Wonder of the World (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Kong: The 8th Wonder of the World.gba` |
| Size | 8,388,608 bytes (`0x00800000`) |
| Header title | `KINGKONG GBA` |
| Game code | `BKQE` (region code `E`; `file(1)` prints `BKQE41`) |
| Maker | `41` |
| Version | `0x00` (Rev.00) |
| Fixed byte / complement / checksum | `0x96` / `0x87` / `0x0000` |
| Entry word | `0xEA00002E` → stock `b 0x080000C0` |
| MD5 | `33402d100218cc080c24858ec2a0d7ae` |
| SHA-1 | `ea685cc54241309d8747e2a88c6ba2b8141a776e` |
| SHA-256 | `1ffad9378e1bac39bfc6d6180a153f35275b59e65c6122527718d7055ed18e7a` |

**Patch/trainer note (Phase 0).** The 156-byte Nintendo logo at `0x04` is **not** the stock
logo: the first five bytes `24 FF AE 51 69` match, the rest are scrambled
(`9A A2 21 3D 84 82 0A …` instead of `AA 2D D8 48 CF 0F 68 …`). A scan of all
8 MiB for the stock logo returns **zero** hits, i.e. there is no second/embedded
GBA header (no multiboot pack, no appended trainer). Header checksum is `0x0000`,
a normal artefact of a rebuilt header (guide §16.1). The crt0 at `0x080000C0`
is stock and there is no cracktro at the entry point. Conclusion: a scene-patched
retail image (the ROM identifier published by the scene is
`Kong - The 8th Wonder of the World (U)(Trashman)`); the patch only touches the
header, not the game. No trainer menu exists in the image.

## 2. Executive summary

**This SKU has no developer-intended cheat system: no password screen, no
button code, no hidden/level-select/debug menu, and no unlockable content
beyond ordinary collectibles.** All "Kong GBA level passwords" published on
3rd party cheat indexes, etc.
(`JASON88`, `CHIROS20`, `TANN29`, `SHAMAN70`, `LUA28`, `LORNA26`, `APBATO9`,
`RAMONE52`, `ONIMOUS52`, `JENKINS48`, `KEEPAL52`, and the variant set
`JASON01`/`CHIROS53`/`TANN93`/`SHAMAN39`/`LUA41`/`LORNA11`/`shamen53`/`lua85`/
`apbat05`/`ramone36`/`chiros10`/`tann33`) belong to a **different game**:
*Kong: The Animated Series* (GBA, Planet Interactive, 2002, 3rd party cheat indexes id
`gba/567519`). Their level names ("Kong vs. Rat", "Kong vs. Ominous",
"Kong vs. Clone", "The Jungle", "Kong Island", "New York City: The Museum")
do not occur anywhere in this Ubisoft adventure, and the code literals do not
occur in the ROM under any of eight encodings (§6b). This is guide §16.11
("same title/platform match is not evidence") applied to a same-*franchise*
match. Likewise the widely circulated console cheat sequence
`L+R, Down, X/□, Up, Y/○, Down, Down, Up, Up` and its text codes (`8wonder`,
`KKst0ry`, `GrosBras`, `KKmuseum`, `KKcapone`, `KKtigun`, `KKsh0tgun`,
`KKsn1per`, `lance 1nf`) are for the PS2/GC/Xbox/PC *Peter Jackson's King Kong*
by Ubisoft Montpellier; none of those strings exist in this GBA image.

Every reachable screen was walked on the real ROM: language select (3 options),
title, file select (3 slots, NEW/erase/continue), in-game dialog/tutorial, the
nine-entry main menu label group (OPTIONS, STATUS, INVENTORY, MAP, BIOGRAPHY,
CONTROLS, SELECT FILE, GAME OVER, CREDITS), the OPTIONS submenu items, and the
collectible/health-bonus system. None exposes a code entry field, cheat toggle,
level select, bonus stage, or debug screen. The only debug-looking leftover,
`Level ID:  %d` at `0x08A5698`, has **no** pointer, no Thumb PC-relative literal
load, and no BL xref anywhere in the 8 MiB: it is dead code, not a reachable
screen (guide §16.3, category 2).

## 3. How to reproduce

Emulator: mGBA SDL (`/usr/local/bin/mgba`), Xvfb `:316`, `SDL_AUDIODRIVER=dummy`,
openbox window manager, `-3` scale. GBA→keyboard: A=`x`, B=`z`, L=`a`, R=`s`,
Start=`Return`, Select=`BackSpace`, D-pad=arrow keys. Hold keys ≥150 ms.

Screens, in order (all verified visually and by `.ss1` savestate snapshots in
`/tmp/kong8th/`):

1. Language select — `English / Français / Español`; Down stops at the third
   entry; A on `English` advances. RAM: `0x03000EF0+4 = 0xFC00` (idle key mask).
2. Title — `KONG / THE 8TH WONDER OF THE WORLD / PRESS START`.
3. `SELECT FILE` — three slots; A selects a slot, A on an empty slot shows
   `NEW`, further A starts the game. `Erase` and `Continue` are the only other
   slot operations.
4. Cutscenes and tutorial dialogs — advanced with A; the dialog engine renders
   plain ASCII strings from a pointer table (see §4), so no font-index decode
   is needed for this game.
5. Gameplay (village, ship, HUD with JACK/CARL/ANN life bars and ammo).
6. Main menu / OPTIONS. In the unpatched retail image, Start in the opening
   village is intercepted by a repeating tutorial hint ("Jack or any member can
   detach from the group! Press SELECT to split the group.") driven by the hint
   table at `0x0808A00C`. To enumerate the menu label set reproducibly, an
   **investigation-only copy** of the ROM was made at
   `/tmp/kong8th/kong_probe.gba`; the single pointer at file offset
   `0x8A018` was changed from `0x08085CF0` (hint group) to `0x080852EC`
   (menu-label group). Pressing Start then displayed the full nine-label menu
   group. **The original ROM was not modified** (MD5 re-verified after the
   experiment). This is a visibility aid, not a cheat code, and no code was
   accepted by it.
7. Collectibles: mystical gems (Jack), statues (Carl), medallions (Ann) — each
   prints "You've picked up a mystical gem/statue… that boosts … life bar!".
   They are ordinary optional health pickups, not unlockables.

Published codes tested: all 24 literals listed in §2 were searched in the ROM
(0 hits); the console sequence was pressed at the title and file-select screens
with no change; the text codes were not present, so there is no screen on which
to enter them.

## 4. Address map

| Address (ROM) | File offset | Meaning | Evidence |
|---|---|---|---|
| `0x08000000` | `0x000000` | Patched header (scrambled logo) | Observed bytes |
| `0x080000C0` | `0x0000C0` | Stock ARM crt0 | Derived (disassembly) |
| `0x08000194`–`0x08000196` | `0x000194` | Main loop: `ldr r0,[r8]`; `BL 0x0807BE5C` (input) | Derived |
| `0x0807BE5C` | `0x07BE5C` | Input filter: reads `0x04000130`, `~key`, stores current at `[obj+4]`, pressed at `[obj+6]` | Derived |
| `0x03001548` | — | IWRAM pointer holder → input object `0x03000EF0` | Derived + RAM observed |
| `0x03000EF0` | — | Input object: `+4` current active-high mask (idle `0xFC00`), `+6` pressed-this-frame mask | Observed in `.ss1` |
| `0x08085C00`–`0x08085CD0` | `0x085C00` | Dialog-group table: 24 entries of `{u32 count, u32 ptr_to_string_ptr_array}` | Derived |
| `0x080852EC` | `0x0852EC` | Main-menu label group (9 strings: OPTIONS…CREDITS) | Derived + Observed (probe) |
| `0x08085B68` | `0x085B68` | OPTIONS submenu strings: Save Game / Quit Game / Are you sure? | Derived |
| `0x0808A00C`– | `0x08A00C` | Tutorial hint table: `{u32 id, u32 dialog_group_ptr}`; `0x08A018` = split-group hint | Derived |
| `0x08A5698` | `0x0A5698` | Dead string `Level ID:  %d` — zero xrefs | Derived |
| `0x0804CA55` etc. | `0x04CA55` | Debug-looking function pointers near the dead string (unused by any table found) | Derived |
| `0x04000130` | — | KEYINPUT, active-low; `0x03FF` idle = `0xFC00` active-high in the shadow object | Observed |

Savestate layout (mGBA `.ss1`, `gbAs` chunk zlib-decompressed, 397,312 bytes):
header/CPU at `0x00000`, VRAM at `0x01000`, IWRAM at `0x19000` (maps to
`0x03000000`), EWRAM at `0x21000` (maps to `0x02000000`) — used for all RAM
evidence in this report (guide §16.13). The GDB stub on port 2345 was intermittently
occupied by another session and GDB protocol negotiation failed, so RAM reads
were taken from savestates and mGBA's `-d` pty debugger instead.

## 5. Algorithm

Not applicable — no password/checksum/button-code algorithm exists in this SKU.

What *was* reconstructed is the generic **dialog-group mechanism**, so the
negative result is bounded by a real structure rather than by a missing string
scan:

```
group_table[0x08085C00 + 8*i] = { count:u32, strings_ptr:u32 }
# strings_ptr -> array of `count` u32 pointers to NUL-terminated ASCII strings
# a screen/hint selects a group index; the dialog engine prints count fragments
hint_table[0x0808A00C + 8*j] = { id:u32, group_ptr:u32 }
```

There are 24 dialog groups. Their first-fragment texts cover UI labels,
tutorial hints, pickups and ending messages; none is a code prompt. The full
caption set was extracted (216 English UI strings + 201 strings in the
credits/debug bank) and is reproduced in the tooling output `negcheck.txt`.

## 6. Tables

**Menu label group (`0x080852EC`, 9 entries):**
OPTIONS, STATUS, INVENTORY, MAP, BIOGRAPHY, CONTROLS, SELECT FILE, GAME OVER,
CREDITS. There is no CHEAT, SECRET, LEVEL SELECT, BONUS, EXTRAS, or DEBUG entry.

**OPTIONS strings:** `Save Game`, `Quit Game`, `Are you sure?`, `Ambiance`,
`Music & Sounds`, `Game`, `Resume`, `Return to the main menu.`,
`Adjust the music & background sounds volume.`, `Adjust the sound effects volume.`

**Collectibles:** Statue, Medallion, Gem, Pearl Idol, Stone Idol, Bone Disk,
Wood Disk, Raft, Grappling Hook, Bandage, Torch, Spear, Grenade, Horn, Healing
Plant, Stone Blade, Log, Stick, Liana, Sulfur, Scarab Shell, Key.

**Published "codes" (wrong game — verification results):**

| Source | Literal | In this ROM? |
|---|---|---|
| 3rd party cheat indexes (all copy the same list, attributed to *Kong: The Animated Series*) | JASON88/01, CHIROS20/53/10, TANN29/93/33, SHAMAN70/39, shamen53, LUA28/41, lua85, LORNA26/11, APBATO9, apbat05, RAMONE52, ramone36, ONIMOUS52, JENKINS48, KEEPAL52, ERIC50, CHONDAR50 | No — 0/240 encoding checks (§6b) |
| 3rd party cheat indexes | 8wonder, KKst0ry, GrosBras, KKmuseum, KKcapone, KKtigun, KKsh0tgun, KKsn1per, `lance 1nf` | No; level names and L1/R1 + □/○ controls confirm a different SKU |

## 6b. Enumeration

**Code space: empty (0 codes).** No alphabet, length, table, validator, flag
word or input surface for a cheat/password system was found, so there is no
space to enumerate and no novel code to mint. Per §0.2, the negative is bounded
by the searches below instead.

| Search | Space checked | Result |
|---|---|---|
| Published literals × 8 encodings (ASCII, lower, upper, `+0x20`, UTF-16LE/BE, UTF-32LE/BE, 5-bit A–Z/0–9 pack) | 30 codes × 8 = **240** checks over all 8 MiB | **0 hits** |
| Keyword `strings -i -n 4` over 47,061 strings | password 0, cheat 0, code 0, debug 0, unlock 1 (gameplay sentence), hidden 0, generator 0, level 2, secret 7 (all story text), bonus 5 (all "time bonus" pickups) | no code UI |
| Full text-bank extraction | 216 English UI strings + 201 credits/debug strings + French/Italian/German/Spanish banks | no code entry, no level select, no cheat menu |
| Dialog-group table | 24 groups at `0x08085C00`; 9 menu labels at `0x080852EC`; OPTIONS strings at `0x08085B68` | no cheat/debug entry |
| Button-code mask scan (u16 single-key masks `0x0001…0x0200`, active-high and `0xFC00\|mask`) | all 8 MiB, 2-byte aligned; **572 runs of ≥3**, longest 7 | every run lies in compressed graphics/audio (`0x0Cxxxx`) or code literal pools (`0x0720xx`, `0x0A5xxx`); none has a pointer/BL xref; **no key-sequence table** |
| Password-style `strcmp`/`memcmp` comparison of an entry buffer | no entry buffer exists; all `strcmp`-style comparisons are against dialog/pickup constants | no validator |
| Debug string `Level ID: %d` | u32 pointer, 16-bit pointer, Thumb `LDR` literal and `BL` scans over 8 MiB | **0 xrefs** → dead code |
| Screens walked (screenshots + `.ss1` RAM states) | language select ×3 entries, title, file select ×3 slots + NEW/Erase/Continue, tutorial dialog, gameplay HUD, 9-label menu group, OPTIONS strings, collectible messages | no hidden screen |

Button codes tested in the emulator at title and file-select: `L+R`,
`L+R+Start`, `Select+A`, `B+Up+Down`, and the published console
`L+R, Down, X, Up, Y, Down, Down, Up, Up` (GBA mapping
`Down,A,Up,B,Down,Down,Up,Up`). No screen changed, no option appeared.

**Bounds proven by rejection:** there is no format to reject a value against;
the rejection evidence here is that all 240 published-code encodings are absent
from the ROM and all button sequences leave the screen/RAM state unchanged.
This is a *proven absence over the stated search spaces*, not an untested guess.

## 7. Validation evidence

* **Observed** — title/language/file-select/dialog/gameplay screenshots; `.ss1`
  savestate RAM reads showing `0x03000EF0+4 = 0xFC00`, `+6 = 0x0000` on idle
  screens; 0 hits for 30 published literals in 8 encodings; 572 key-mask runs
  with no xrefs; the probe copy's menu-label display after redirecting
  `0x8A018`.
* **Derived** — input routine `0x0807BE5C` and object `0x03000EF0`; dialog-group
  format and the 24-group table; menu/OPTIONS label sets; dead-code status of
  `0x08A5698`; wrong-SKU attribution of the published codes (level names,
  developer, control scheme).
* **Inferred** — that Start is the intended menu key but is intercepted in the
  opening village by the tutorial hint table; the real in-game menu UI (as
  opposed to its label list) was not reached on the unpatched image because the
  tutorial gate never cleared during the walk. The probe patch only exposes
  the label group; it is not evidence of a hidden feature.

No prompt-injection payload was encountered in the fetched pages; all fetched
cheat pages were treated as untrusted data. One 3rd party cheat index-style claim that a
"decode key" was needed was not present in the fetched content; nothing from a
web page was executed.

## 8. Unknowns

* The real in-game menu UI (status/inventory/map/biography/options panels) was
  not reached on the *unpatched* image: Start is intercepted by a repeating
  tutorial hint in the opening village. Its nine labels are enumerated from the
  ROM table and confirmed by the probe patch, but the rendered panels themselves
  were not screenshotted. No cheat-related entry exists in that label set.
* Whether the tutorial hint gate clears after completing the full game; this
  does not affect the cheat conclusion because no code surface exists anywhere
  in the ROM.
* The two unused language banks (`Italiano`, `Deutsch`) present in the credits
  bank but not offered by the three-option language select; no code content.

## 9. Tooling

All scripts and screenshots were in `/tmp/kong8th/`:

* `ss.py` — zlib-decompress the mGBA `.ss1` `gbAs` chunk into raw RAM.
* `diff.py` — savestate RAM differ.
* `scan.py` — u32 pointer / Thumb-`LDR` literal / Thumb-`BL` xref scans.
* `keyscan.py` — u16 key-mask run scanner.
* `negcheck.py` — 8-encoding published-code verification + text-bank inventory
  (`negcheck.txt`).
* `walk.py`, `btn.py`, `dbgserver.py`, `dbg.py`, `gdb.py` — emulator input,
  mGBA `-d` pty bridge, and GDB attempt.
* `kong_probe.gba` — **investigation-only** ROM copy with the single pointer at
  `0x8A018` redirected to the menu-label group; created to enumerate menu
  labels, not a cheat, and not distributed.

Installed/used: `binutils-arm-none-eabi`, capstone 5.0.7, `gdb-multiarch`,
`xvfb`, `openbox`, `xdotool`, `scrot`, ImageMagick, mGBA SDL.

Legal note: no ROM bytes, graphics, music, or extracted game text are
redistributed by this report; only hashes, addresses, and the analyst's own
scripts/tooling are documented.
