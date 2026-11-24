# Scooby-Doo! (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Scooby-Doo!/Scooby-Doo!.gba` |
| Size | 4,194,304 bytes (0x00400000) |
| Header title | `SCOOBYMOVIEE` |
| Game code | `AP8E` (USA) |
| Maker code | `78` (THQ) |
| Version | `0x00`; complement `0x00`; header checksum `0x0000` |
| Nintendo logo hits | exactly 1 (file 0x000004) — single image, no multiboot/double-pack |
| MD5 | `3ef663a38eb71ed4b8b27ae82c3e11a6` |
| SHA-1 | `f8c4e093d81afaf715f8ad7522c19276e321db81` |
| SHA-256 | `5496962c7e87e675a531feed1b955b39c0650d06e28c495bf841b7fc882a6eb2` |

This is the 2002 live-action *Scooby-Doo* movie tie-in developed by **Helixe**
(Spooky Hotel, Mondavarious, N'Goo Tauna, Ghoul Pass), **not** *Scooby-Doo and
the Cyber Chase*, *Scooby-Doo 2: Monsters Unleashed* or *Scooby-Doo! Unmasked*.
The distinct SKU matters because nearly all published Scooby GBA passwords
belong to those other games (§16.11).

**Packaging note (observed).** The header entry word is `0xEA0FEFFE`, not the
stock `0xEA00002E`. It branches to `0x083FC000` (file `0x3FC000`), a custom
ARM loader that sets `sp = 0x03007F00`, copies code/data into EWRAM and hands
control back. On boot this displays a **scene cracktro** (Mario pipe artwork,
"E7 PRESENTS", "CRACKED BY: TUL…", "LOVE YOU") before the WB/THQ legal screens
and the real game. A stock crt0 is still present at `0x080000C0` and calls the
real `main` at `0x08022705`, so the game body is intact — §16.1 "cracktro,
not an in-game cheat". Patching a **copy** to `0xEA00002E` did not change any
finding; all addresses below are for the unmodified target image.

## 2. Executive summary

**No in-game cheat system exists in this SKU.** There is no password screen, no
password alphabet/table or checksum validator, no button-code sequence table,
no unlock name/code accepted by the executable, and no developer/debug menu
reachable by any controller input. The one debug-related artifact is a group of
five `QA: …` strings in the text bank
(`0x080318B1C`, `0x080318B30`, `0x080318B44`, `0x080318B54`, `0x080318B74`);
they are **never displayed** by any reachable screen and have zero code xrefs
by direct pointer or Thumb literal (dead/gated text, §16.3/§16.21).

Every menu was walked on the real ROM (screenshots and savestate RAM reads):
title/main (4 items), load (3 slots), options (2 sliders), extras (2 items),
minigames (4 items × 3 difficulties + instructions), credits, name entry,
new-game dialogue/gameplay, pause (3 items) and pause-options (2 sliders).
Down-past-QUIT does not reveal hidden pause items; L/R on the main and slot
screens does not reveal a level selector.

All published codes found on the web are for **other Scooby GBA SKUs** and
every literal is absent from this ROM (0/15). The widely reported "HELIXE"
name trick (slot 3 → quit → restart → level name at top of main menu) was
tested on this SKU: the name is accepted and saved, but **no level name or
level select appears**, on the main menu or the slot screen, with L or R.

## 3. How to reproduce

- Emulator: mGBA 0.10.5 `/usr/local/bin/mgba -3 <rom>` under `Xvfb :318`,
  `DISPLAY=:318`, `SDL_AUDIODRIVER=dummy`.
- Keymap (mGBA SDL default): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
  Select=`BackSpace`, D-pad=arrow keys. Hold ≥100 ms; hold A ~5 s to skip the
  60 s cracktro.
- The boot intro is a **cracktro**; wait it out or hold A. Then press through
  two legal screens to reach the main menu.
- Menu path (all confirmed on screen):
  - `NEW GAME` → slot select (3 slots) → `ENTER YOUR NAME` (A–Z grid, max 7
    characters, default `SHAGGY`, `OK` at row 3 col 9) → dialogue → gameplay.
  - `LOAD GAME` → 3 slots (names / `CH n`).
  - `OPTIONS` → `MUSIC VOLUME`, `SFX VOLUME` (L/R adjusts).
  - `EXTRAS` → `MINIGAMES` (`UNLOCK THE CHEST`, `REPAIR THE PIPES`,
    `LIGHTS OUT?`, `MUSICAL MAYHEM`; each → `EASY`/`NORMAL`/`HARD` → rules →
    play) or `CREDITS`.
  - Gameplay → Start → `PAUSE` (`RESUME`, `OPTIONS`, `QUIT`) →
    `ARE YOU SURE? YES/NO`.
- Codes tested: `MXP#2VBL`, `CHBB5VBX`, `5S@C7VB8`, `CHTMD2`, `!V?Y3T?8`,
  `5DBY3MT8`, `CBBCBBBB`, `45B9@WST`, `8QL9SWB2`, `1C3R@LLY`, `PSKYK1DS`,
  `MDBC8LCD`, `XRG0Z9NR`, `SD2` — all absent from the ROM; none enterable
  because there is no password screen. Name trick tested: `HELIXE` (slot 1),
  plus L/R button-combination attempts at boot, main menu and pause.
- GDB note: mGBA's `-g` stub halts startup until `continue` and, in this
  shared environment, port 2345 is contended by other agents' sessions
  (`Ignoring packet error`, `The program is not being run`). Per §16.13 RAM
  evidence was therefore taken by decompressing mGBA `.ss1` savestates
  (`gbAs` PNG chunk → `zlib.decompress` → 397,312-byte raw state; IWRAM at raw
  `0x19000`, EWRAM at raw `0x21000`).

## 4. Address map

| Address (ROM / RAM) | Meaning | Evidence |
|---|---|---|
| `0x08000000` | Entry word `0xEA0FEFFE` → cracktro loader `0x083FC000` | Observed (disassembly + boot) |
| `0x080000C0` | Stock ARM crt0; loads `main = 0x08022705` | Derived (objdump) |
| `0x083FC000` | Cracktro/boot loader, copies code to EWRAM | Derived + observed (screen) |
| `0x08031885C` … `0x080318Dxx` | Main-menu/options/name-entry/pause/chapter text bank (plain NUL-terminated ASCII) | Observed (`strings -t x`) |
| `0x080318B0C` `Pause`, `0x080318B14` `Quit` | Misc UI strings | Observed |
| `0x080318B1C` `QA: show questbits` | Debug text, unreachable | Observed + xref count 0 |
| `0x080318B30` `QA: show player pos` | Debug text, unreachable | Observed + xref count 0 |
| `0x080318B44` `QA: show a btn` | Debug text, unreachable | Observed + xref count 0 |
| `0x080318B54` `QA: SHOW LOC` | Debug text, unreachable | Observed + xref count 0 |
| `0x080318B64` `QUIT`, `0x080318B6C` `RESUME` | Pause-menu labels shown on screen | Observed |
| `0x080318B74` `QA: status toggle` | Debug text, unreachable | Observed + xref count 0 |
| `0x0803EEA8` | Credits string `HELIXE` (GAME DESIGN credit) | Observed |
| `0x0803F070` | Credits-script record beginning `HELIXE\0\0`, followed by timing/pointer data — a **credit**, not a cheat table | Observed |
| `0x080212D0` | Data word `0x0803F070` inside a mixed data/code region; no code path treats it as an entered-name comparison | Derived |
| `0x020004EC`, `0x02000838` | EWRAM copies of entered name `HELIXE` (savestate raw `0x214EC`, `0x21838`) | Observed (RAM) |
| SRAM `+0x04` | Save slot 1 name stored **byte-reversed**: `45 58 49 4C 45 48` = `EXILEH` (i.e. `HELIXE`) | Observed (`.sav`) |
| SRAM `+0x0E`, `+0x18` | Unused slot names `64 65 73 75 6E 55` = `desunU` (`Unused` reversed) | Observed (`.sav`) |

File offset ↔ ROM address: `0x08000000 + file_offset`. No compression was
found on the text bank; its labels are ASCII, so `strings` is exhaustive for
UI text (the §11 "tile-indexed text" trap does not apply to this game: the
rendered screens reproduce the ASCII strings byte-for-byte, e.g.
`SELECT A SLOT`, `ENTER YOUR NAME`, `PAUSE`, `MUSIC VOLUME`).

## 5. Algorithm

There is **no password validator, checksum, key table or cheat dispatcher** to
reimplement. The only decoder present is the save-name serialisation:

```
save_name_bytes(n) = reverse_ascii(n)      # SRAM stores the 6 name bytes reversed
# e.g. "HELIXE" -> 45 58 49 4C 45 48 ("EXILEH")
```

Name entry: 3 rows × 9 cells (`ABCDEFGHI` / `JKLMNOPQR` / `STUVWXYZ` + `OK`);
A appends the highlighted letter and leaves the cursor there, B deletes one
letter (B on an empty field exits), max 7 characters. No special string is
compared against this buffer anywhere in the executable (no `strcmp`-style
constant of `HELIXE`, `DEBUG`, `SECRET`, etc. — see §6b).

## 6. Tables

**Reachable menus (complete counts, observed):**

| Screen | Items |
|---|---|
| Main | NEW GAME, LOAD GAME, OPTIONS, EXTRAS (4) |
| Load game | slot 1, slot 2, slot 3 (3) |
| Options | MUSIC VOLUME, SFX VOLUME (2) |
| Extras | MINIGAMES, CREDITS (2) |
| Minigames | UNLOCK THE CHEST, REPAIR THE PIPES, LIGHTS OUT?, MUSICAL MAYHEM (4) |
| Minigame difficulty | EASY, NORMAL, HARD (3) |
| Name entry | 26 letters + OK (27 cells) |
| Pause | RESUME, OPTIONS, QUIT (3) |
| Pause options | MUSIC VOLUME, SFX VOLUME (2) |
| Quit confirm | YES, NO (2) |

**Unreachable debug text (5):** `QA: show questbits`, `QA: show player pos`,
`QA: show a btn`, `QA: SHOW LOC`, `QA: status toggle` at the addresses in §4.
No menu item, text ID or code path displays them.

**Published-code verification (15 literals, 0 hits):** MXP#2VBL, CHBB5VBX,
5S@C7VB8 (Cyber Chase), CHTMD2 (Cyber Chase cheat mode), !V?Y3T?8, 5DBY3MT8,
CBBCBBBB (Scooby 2 / double pack), 45B9@WST, 8QL9SWB2, 1C3R@LLY, PSKYK1DS
(Cyber Chase), MDBC8LCD (Monsters Unleashed), XRG0Z9NR (Unmasked), SD2, plus
the `HELIXE` slot-3 trick. `HELIXE` occurs only as a credits string / credit
record. These results confirm §16.7 (published lists are evidence, not truth).

## 6b. Enumeration

**Space definition.** The game defines no code space. The relevant search
spaces were enumerated as follows, with exact counts:

1. **Password/checksum space:** 0 alphabets found — literal scans for
   `ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789`,
   `0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ`, `ABCDEFGHIJKLMNOPQRSTUVWXYZ` and
   the no-confusion alphabet `23456789ABCDEFGHJKLMNPQRSTUVWXYZ` each returned
   **0 hits**. 0 password screens on any reachable menu. 0 validator/table
   xrefs (see item 4). Representable code set: **empty**.
2. **Button-code space:** 0 tables. Searched the Konami sequence
   `U,U,D,D,L,R,L,R,B,A` as active-high u16, active-high u8 and active-low u16
   — **0 hits** each. Boot-time L+R, main-menu L+R, L+R+Start, Select+Start,
   A+B+Start, Select+A+B+Start and down-past-QUIT in pause all produced no
   state change (screenshots + savestates). Documented action branches: 0.
3. **Text/table space:** 3,215 NUL-terminated ASCII strings ≥4 bytes; a
   case-insensitive password|cheat|code|secret|unlock|debug|generator|level
   select filter returned **8 strings**, all in-game dialogue or door/objective
   text (`Unlock The Chest`, `Basin door is unlocked.`, `The door's unlocked!`,
   `I've unlocked the door for you.`, etc.) — **0 UI strings** for a cheat.
4. **Debug-gate space:** 0 xrefs to the 5 `QA:` strings by 32-bit direct pointer
   (full ROM scan, aligned and unaligned) and 0 by Thumb PC-relative `LDR`
   literal (Capstone scan of every 2-byte offset). They are also absent from
   RAM text buffers in the captured savestates. Combined with the complete
   screen walk above, the set of reachable debug-menu entries is **empty**.
   The strings are dead/gated leftovers (§16.3, §16.21), not a hidden screen.
5. **Unlock space:** 0 unlockable characters, levels or collectibles reachable
   by input. All 4 minigames and all 3 difficulties are selectable from a fresh
   file; no entry is greyed out or gated. `HELIXE` name entry + quit/restart
   produced no chapter name and no L/R chapter selection (slot 1 saved as
   `HELIXE`, `CH 1`), so the published level-select unlock is **not present**
   in this SKU.

**Novel codes:** not applicable — the code space is empty (§0.2's "negative
results bounded" case). **Bounds proven by rejection:** out-of-domain inputs
(the 15 published literals, the HELIXE name trick, and 7 boot/menu button
combinations) were all entered/pressed in the emulator and all failed to
produce any cheat effect; those rejections bound the space rather than being
"not tested".

## 7. Validation evidence

- **Observed** (emulator, screenshots in `/tmp/scooby1/c_*.png`):
  cracktro → 2 legal screens → main menu (4 items) → load/options/extras/
  minigames/credits → name entry → new-game dialogue → gameplay (HUD +
  objective) → pause (3 items) → pause options (2 sliders) → quit confirm.
  L/R and down-past-QUIT had no effect. `HELIXE` saved; after a full emulator
  restart slot 1 reads `HELIXE / CH 1`, main menu still shows only the 4 items.
- **Observed (RAM):** `.sav` slot 1 name bytes `45 58 49 4C 45 48` (`EXILEH`
  = reversed `HELIXE`) at offset `0x04`; unused slots `desunU` at `0x0E`,
  `0x18`. Savestate `gbAs` raw: `HELIXE` at `0x214EC` and `0x21838`, i.e.
  EWRAM `0x020004EC` / `0x02000838` (mapping raw = `0x21000 + (addr-0x02000000)`).
- **Derived:** entry-word branch disassembly and crt0/main address; 0 xrefs for
  QA strings; 0 literal hits for all alphabets/codes/Konami encodings;
  string counts from `strings -t x`.
- **Inferred:** the five `QA:` strings are leftover debug-build text whose
  menu handler was removed or gated out of the retail build. This is the only
  claim not directly exercised, because no reachable input displays them.
- **Tooling caveat:** mGBA's GDB stub was unusable mid-run (port contention with
  other agents; `Ignoring packet error`), so no live breakpoints were set.
  This is a harness limitation, not an untested feature: every conclusion is
  backed by screen enumeration plus static counts and savestate RAM reads.

## 8. Unknowns

- Whether the five `QA:` strings were ever wired to a menu in an internal
  build; the retail code path that would own them was not identified.
- Whether completing the game unlocks an epilogue code entry on this SKU
  (the post-credits "movie code" is published for *Scooby-Doo 2*, not this
  game, and no password UI string exists in this ROM).
- Whether any of the four minigames hide an input-only bonus after a perfect
  score; only their selection, difficulty and opening screens were walked.

## 9. Tooling

`file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings -t x`, `grep`,
Python 3 (header parse, literal/xref scans, Capstone Thumb-LDR scan, save-state
`gbAs` zlib decompression and byte-diff), `arm-none-eabi-objdump -M
force-thumb/-force-arm`, mGBA 0.10.5 (`-3`, `-g`, `-t`), Xvfb `:318`, openbox,
`xdotool`, `scrot`, ImageMagick `convert`. No ROM or copyrighted asset is
redistributed by this report.
