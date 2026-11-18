# Justice League: Chronicles (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Justice League: Chronicles.gba` |
| Size | 8,388,608 bytes (0x800000) |
| Header title | `JUSTICE LEAG` (12-byte field, space/NUL padded) |
| Game code | `BJLE` |
| Maker code | `5D` |
| Version | 0x00 (`file`: `BJLE5D, Rev.00`) |
| Entry word | `0xEA00002E` — stock GBA branch to 0x080000C0; no cracktro/patch |
| MD5 | `1b953a635c3b51aecc8d74a5dee826cd` |
| SHA-1 | `f14a43b51d27ab5cca63ab71b0fdacb0afa1deb9` |
| SHA-256 | `24fab66030e31443e5d29ac4917d6545fee785e8e65bc8037cfb7f407773e45a` |

Phase 0 notes: the 156-byte Nintendo logo occurs exactly once, at file 0x4 — this is a **single game image**, not a multigame cart. Header checksum at 0xBE is `0x0000` and the complement byte at 0xBD is `0x6b` (the usual rebuilt-header artifact of §16.1); no trainer, appended menu, or patched entry was found. Developer is **Full Fat** (credits at 0x77F5C8/0x77F5D8), publisher Midway. This is a different SKU/engine from *Justice League Heroes: The Flash* (the other GBA title in the set): different header code, different developer, no shared strings/code; the published *Heroes: The Flash* button codes do not apply and were not found in this image.

## 2. Executive summary

**There is no in-game password, cheat-code, button-code, or reachable debug menu in this build.** The only player-facing unlockables are save-data progression flags: the three story episodes are unlocked in sequence, Combat-Simulator practice levels are gated by a `LOCKED` flag, and the published "J'onn J'onzz" unlock is obtained by completing all three story modes (a save-bit setter, not a code — §16.18).

The ROM does retain a **large debug/logging string bank** (tweak menu, `cheat mode activated`, `unlockLevel %x`, `debug eeprom structure`, etc.) and dormant debug handler functions. Static caller analysis shows these functions have **zero** BL callers, zero 32-bit literal pointers and zero Thumb-bit function-pointer entries — they are dead code (§16.3, case 2). The one cheat-activation path is additionally gated on a tweak variable that is `0` in every observed state while its target constant is `6`, so no reachable input can set it. A 100-entry button-history buffer exists (0x030045B0) but has no consumer that compares it against a code sequence; the generic sequence-detector helpers (0x080A2430 / 0x080A2478) likewise have no callers.

The negative is bounded: all reachable screens were walked with RAM snapshots, the entire ASCII text bank was searched for `password`/`cheat`/`secret`/`unlock`/`level select` (and the +0x20, UTF-16LE variants), and all published material was checked. `password` occurs **0 times** in any encoding.

## 3. How to reproduce

* Emulator: mGBA (`/usr/local/bin/mgba`), `DISPLAY=:318`, `SDL_AUDIODRIVER=dummy`, Xvfb :318 + openbox, `-3` scale. GBA keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad arrows. Use 50–60 ms holds for menus (150 ms double-steps on several screens, §16.2).
* Menu path: title → **Start** → LOAD/SAVE (3 slots, all `NEW GAME` on a fresh .sav) → **A** → GAME MENU. From GAME MENU: STORY MODE (episode `Dark Winter`), WATCHTOWER COMBAT SIMULATOR (→ SELECT CHARACTER → COMBAT SIMULATOR level list with `LOCKED` entries), MULTIPLAYER (→ SELECT CHARACTER), OPTIONS (`MUSIC VOLUME`, `SFX VOLUME`, `CREDITS`), HERO BIOGRAPHY (read-only bios), HIGH SCORES. In gameplay, **Start** → PAUSE (`RESUME`/`EXIT`).
* Codes tested: none published to test beyond the J'onn J'onzz unlockable (save-bit, not an entered code). Common title-screen button sequences (Konami-style, L+R+Start, U/D/L/R combos with B/A) were pressed — no hidden screen appeared.
* RAM evidence: savestates (`Shift+F1`) were taken at every screen. `.ss1` is a PNG with a zlib `gbAs` chunk (raw length 397,312); IWRAM maps to chunk offset 0x19000 (= 0x03000000) and EWRAM to 0x21000 (= 0x02000000).

## 4. Address map

| Address (ROM/file) | Meaning | Evidence |
|---|---|---|
| 0x0815FE–0x081612 | "cheat mode activated" path: prints string 0x0877D7D4, sets EWRAM flag `[(0x030011D8)]+0x212` bit 1 | Derived (Thumb disasm) |
| 0x0815E8 | Gate: `r4 = 0x03001260`; calls 0x075D88 then 0x075DF4; requires return `== 1` | Derived |
| 0x075DF4 | Generic 16-bit compare: returns 1 when `*(u16*)arg == *(u16*)(arg->ptr)` | Derived |
| 0x080B5C6C | Target constant for the cheat tweak variable = `6` | Derived |
| 0x081468 | Unreachable debug-menu handler (action cases 0/1/2/7; case 2 = cheat activation) | Derived + negative caller scan |
| 0x0761F8 | Debug save-record dump: prints checksum, unlockLevel, volumes, levels, lives, episode | Derived |
| 0x0768F4 | EEPROM save verify: copies 17-byte magic `JUSTICELEAGUE2V4` (0x0877C9BC) and compares 16 bytes | Derived |
| 0x0877D7D4 | ASCII `cheat mode activated` | Observed (strings) |
| 0x0877C774 / 0x0877C764 | ASCII `unlockLevel %x` / `checksum %x` | Observed |
| 0x08771D00 | ASCII `Couldn't allocate %d bytes for tweak menu display strings` | Observed |
| 0x087F740 | ASCII `debugWaitStart Function call by %s` (debug screen helper, Start-to-continue) | Observed |
| 0x080A21B4 | Input handler; reads KEYINPUT (0x04000130), writes 100-entry history | Derived |
| 0x080A2430 / 0x080A2478 | Generic button-sequence detector helpers — no callers | Derived + negative scan |
| 0x030046A0 / 0x030045A0 / 0x030046AC / 0x030046A4 | Current keypad / previous / pressed / released masks | Observed (savestates) |
| 0x030045B0 / 0x030046B0 / 0x030046B4 | 100-entry button history base / write pointer / remaining count (100) | Observed (savestates) |
| 0x03000D10 | Frame counter used by the 100-frame gesture window | Derived |
| 0x03001260 | Cheat tweak variable: `0` in all states; target `6` | Observed |
| 0x02000432 | Cheat flag byte `[0x030011D8]+0x212` | Observed = 0 in all states |
| Save file 0x00–0x0F | EEPROM magic `JUSTICELEAGUE2V4` (byte-swapped on disk: `LECITSUJ4V2EUGAE`) | Observed |
| Save file 0x78 | Save checksum (0x14F9 on the tested card) | Observed |

## 5. Algorithm

Not applicable — no validator, password algorithm, or key-mask code sequence exists. The only "algorithm" present is the save-data checksum/verify (EEPROM, 16-byte magic compare plus a checksum word), which governs save integrity and progression, not a player-entered code.

For completeness, the dormant cheat gate is:

```
if (tweak_var_0x03001260.current == 6):      # 0x08075DF4(0x03001260) == 1
    print("cheat mode activated")
    *(u8*)(*(u32*)0x030011D8 + 0x212) |= 2   # EWRAM flag at 0x02000432
if (*(u16*)0x030046A0 & 9) != 0: print(debug_msg_13)
```

`current` is `0` in every observed state and no reachable writer was found; the flag byte stays `0`.

## 6. Tables

| Text/structure | Address | Notes |
|---|---|---|
| Game Menu entries | 0x0877DCCC etc. | STORY MODE, WATCHTOWER COMBAT SIMULATOR, MULTIPLAYER, OPTIONS, HERO BIOGRAPHY, HIGH SCORES — all six walked |
| Pause entries | 0x0877D69C/0x0877D6A4 | RESUME, EXIT — both walked |
| Options entries | 0x077DF70–0x077E098 | CREDITS, CHANGE SFX VOLUME, CHANGE MUSIC VOLUME (per language) — three walked |
| Character roster | 0x0877DD30–0x0877DD90 | Superman, Batman, Wonder Woman, Green Lantern, The Flash, Martian Manhunter, Hawkgirl — all selectable in Combat Simulator/Multiplayer on a fresh save |
| Episode list | 0x0877DDA4/0x0877DDB0/0x0877DDC4 | Dark Winter, Savage Time, Trial In Ape City — only Dark Winter initially available |
| Locked-state string | 0x0877DF10 | `LOCKED` shown for gated practice levels |
| Save magic | 0x0877C9BC | `JUSTICELEAGUE2V4` (16 chars + NUL; 17-byte memcpy at 0x076908) |
| Cheat tweak target | 0x080B5C6C | value `6` (never reached) |

## 6b. Enumeration

**Space definition:** None. There is no code alphabet, no code length, no checksum field, and no table of accepted codes — the representable code space is the empty set. The "unlock" space is a set of save-data flags (`unlockLevel`, episode completion bits), which is progression state, not an entered code.

**Validator model:** N/A (no validator). The generic 16-bit comparator at 0x075DF4 is used by the debug/tweak system only, not by any player input path.

**Novel codes:** Cannot be generated — there is no generator, decoder, or accepted-code set. No code appears in any published list because no code system exists. This is a bounded negative, not an untested one:

* **Screen enumeration (all walked, 10 screens, savestate RAM captured):** title/PRESS START, LOAD/SAVE, GAME MENU, STORY MODE + cutscene + gameplay, PAUSE, HIGH SCORES, SELECT CHARACTER (Combat Simulator), COMBAT SIMULATOR level list (`LOCKED`), OPTIONS, BIOGRAPHY, MULTIPLAYER (→ SELECT CHARACTER). No hidden menu entry appeared at any level.
* **Text-space counts (whole 8 MiB):** `password` **0**, `pass word` 0, `secret` 0, `hidden` 0, `level select` 0, `character select` 0 (ASCII, uppercase `+0x20`, and UTF-16LE all zero); `cheat` **1** (debug string only), `unlock` **1** (`unlockLevel %x`, debug), `code` **1** (debug build note), `debug` **6** (all debug logging). The visible menus are plain ASCII (strings at 0x77D690–0x77E110), not tile-indexed, so the ASCII scan covers the text space; the byte-shifted/UTF-16 checks cover the alternate encodings called out in §16.11.
* **Button space:** KEYINPUT (0x04000130) has exactly **2** literal references (0x0A22A4, 0x0A23E8), both inside the input handler at 0x080A21B4, which only builds a 100-entry history buffer (0x030045B0) for normal controls. The only sequence-checking helpers (0x080A2430/0x080A2478) have **0** BL callers and **0** literal pointers; the one consumer pattern at 0x080A249E–0x080A24F0 checks a 100-frame window but is unreachable. Common title-code sequences pressed in-emulator produced no hidden screen.
* **Debug-code reachability:** The cheat handler at 0x081468 and its neighbors (0x081404, 0x0815E8, 0x081638) have **0** BL callers, **0** 32-bit literal pointers, and **0** Thumb-bit pointer entries; the 0x081469 occurrence at file 0xB4391 is inside the unrelated word `0x081469AC`, not a pointer. The gate value is 0 vs target 6, and the cheat flag byte 0x02000432 is 0 in every state. (An attempted live breakpoint test was inconclusive because this mGBA build cannot patch ROM software breakpoints; the static caller/pointer counts are the evidence.)
* **Published codes tested:** GameFAQs and SuperCheats list only the J'onn J'onzz unlock (complete all three story modes) — a save-bit unlock, verified as such in the save format. VGChartz lists two gameplay hints, not codes. TCRF has no page for this title. No password or button code is published for this SKU.

## 7. Validation evidence

* **Observed:** title, all menus, bios, options, character select, locked levels, pause, gameplay, high scores, save file bytes, RAM values from savestates, no reaction to title-screen button sequences.
* **Derived:** dead-code classification of the debug functions from zero xrefs; cheat gate `0 != 6`; EEPROM magic and compare loop; keypad history layout.
* **Inferred:** that Full Fat simply shipped the debug strings/handlers unused (consistent with the credits build). No claim is made about other regions/revisions of this title.
* No prompt-injection content was encountered in fetched pages; fetched material was treated as data only.

## 8. Unknowns

* Exact bit positions of the J'onn J'onzz / episode-completion flags inside the 512-byte EEPROM save were not exhaustively mapped; the `unlockLevel` field at record+4 and the checksum at 0x78 were confirmed, but no save-editor was used (out of scope — memory-edit codes are excluded).
* A live breakpoint proof of dead code was not possible with this mGBA build's ROM breakpoint limitation; the conclusion rests on static caller/pointer counts plus the gate value mismatch.
* Other regional revisions of *Justice League: Chronicles* were not examined; all addresses here are for SHA-256 `24fab660…45a` only.

## 9. Tooling

* `file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings -t x`, `grep -re`, Python `struct`/`re` scans, `arm-none-eabi-objdump -M force-thumb` (raw binary, no `--adjust-vma`: file offset = ROM address), Capstone-style BL/pointer scanners.
* Xvfb :318 + openbox + mGBA `-3`; `xdotool` XTEST input; `scrot` screenshots.
* `ssread.py` (mGBA `.ss1` `gbAs` zlib parser → RAM), `capstate.py`/`diffscan.py` (savestate capture + RAM diff), `gdbmem.py` and `mgba_dbg.py`/`bptest2.py` (attempted GDB/CLI debugger paths). GDB stub wedged on unsupported `qSupported`; CLI debugger could not patch ROM breakpoints — savestate parsing was the reliable RAM oracle.
* Web: GameFAQs cheats page (403, used search snippet), SuperCheats, VGChartz cheats page, TCRF (no page), web search. No downloaded asset redistributed.

**Legal note:** no ROM, save, or copyrighted asset is redistributed here; only hashes, addresses, and the author's scripts are published.
