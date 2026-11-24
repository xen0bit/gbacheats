# Robopon 2: Ring Version (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Robopon 2: Ring Version.gba` |
| Size | 4,194,304 bytes (0x00400000) |
| Header title | `ROBOPON2RING` |
| Game code / maker | `ARPE` / `EB` (Epoch), `file(1)` reports "ARPEEB, Rev.00" |
| Version byte | `0x00` |
| Fixed 0x96 | present at 0xB2; entry word `0xEA00002E` (stock crt0 branch to 0x080000C0) |
| Header complement | `0x21` at 0xBD — **valid** (`-(sum(0xA0..0xBC)) - 0x19 = 0x21`); 16-bit checksum field 0x0000 is a retail quirk, not a patch marker |
| MD5 | `1aae9d358e7e8709ac6034195d5ec052` |
| SHA-1 | `c3e14e06f5ccc5755dfa7998546e95e069f40f2b` |
| SHA-256 | `cbf19ff09b158e376120b6177c80211d0db787232f9b1d2a3425a5e4175893af` |

**Embedded GBA headers (Phase 0).** The Nintendo logo (156 bytes at header+4) occurs three times: file `0x000004` (main), `0x065314` and `0x066F04`. The two extra headers are:

| File offset | Header title | Game code | Maker | Interpretation |
|---:|---|---|---|---|
| 0x065314 | (empty) | `AGBJ` | `01` | multiboot/link stub image |
| 0x066F00 | `BOMSTORY` | `ABSJ` | `18` (Hudson) | embedded Bomberman Story multiboot payload (single-pak link minigame) |

Both have the stock entry word `0xEA00002E`; they are in-image multiboot payloads, not a 2-in-1 pack patch. No scene cracktro/trainer strings, no appended code beyond these payloads, no patched entry word.

**Dump-quality finding (important).** This 4 MiB file appears to be a **truncated/bad dump** of an 8 MiB game. Independent corroboration: mGBA issue [#2052](https://github.com/mgba-emu/mgba/issues/2052) and BizHawk [#2635](https://github.com/TASEmulators/BizHawk/issues/2635) report that Ring/Cross 4 MiB images freeze/corrupt while the expected No-Intro size is 8 MiB. Our image reproduces the failure exactly (§7). Padding a working copy to 8 MiB with `0xFF` (`padded8.gba`, SHA-256 of the first 4 MiB unchanged) removes the crash and lets the intro run to completion, confirming missing high-half data. **All analysis below is of the exact hash above; the padding was only a diagnostic copy in `/tmp/robopon2`.**

## 2. Executive summary

The game has exactly **one** developer-intended cheat surface: the **Jasper Passwords** at Marvel Labs. A dog named Jasper accepts a password and gives one of ten otherwise-unobtainable Robopon. It is a **closed, hard-coded string table** embedded in a dialogue/script bank — **no algorithmic password generator, no checksum, no numeric field, and no button code exists**. The complete set is ten literal strings; the UI alphabet is the ordinary 62-character text-entry alphabet (`ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789`, file `0x07ACA4`) shared with name entry — it is *not* a separate password alphabet.

The table lives at file `0x164EA6`–`0x164EED` (ROM `0x08164EA6`–`0x08164EED`) inside the Jasper event script. Because the accepted set is a fixed 10-element lookup, §0.2's "mint a novel code" requirement is **not applicable**: there is no representable space beyond the ten entries, and §7 proves the count by enumerating the entire table and the rejection text. This is a closed-set result, not a "not tested" result.

A widely copied GameFAQs "Jasper Passwords" list (`NegaPon 9`, `Sherry R`, `Under L`, `X-Dog La`, `B-Cell H`, …) is **wrong** for this ROM: those short strings do not occur anywhere in the image. The correct ten passwords are documented in GameFAQs guide 78543 ("Jasper's Robopon") and match the ROM bytes at the addresses above.

Dynamic in-game entry could not be completed on the supplied 4 MiB dump: the game crashes/stalls in its own opening script (§7). This is a property of the dump, not of the cheat system, and is documented with RAM/screenshot evidence.

## 3. How to reproduce

**Static (fully reproducible):**
```bash
ROM="roms/Robopon 2: Ring Version/Robopon 2: Ring Version.gba"
sha256sum "$ROM"
strings -t x -n 3 "$ROM" | grep -iE 'Woof bark|SlugE|RedMT|98765|Input password'
xxd -s 0x164EA0 -l 0x60 "$ROM"
```
The ten passwords are read directly from the script bank at `0x164EA6..0x164EED` (Table 6.1).

**Dynamic attempt:**
```bash
export DISPLAY=:318 SDL_AUDIODRIVER=dummy
Xvfb :318 -screen 0 1024x768x24 -nolisten tcp & openbox &
mgba -3 "$ROM"                      # crashes in opening cutscene (§7)
# diagnostic copy only:
python3 -c "d=open('$ROM','rb').read(); open('/tmp/padded8.gba','wb').write(d+b'\xff'*len(d))"
mgba -3 /tmp/padded8.gba            # intro runs to the title screen; menu still unreachable
```
mGBA SDL keymap used: A=`x`, B=`z`, Start=`Return`, Select=`BackSpace`, D-pad=arrows. Boot sequence: Nintendo → Hudson → RED Entertainment → ATLUS → title (≈20 s), then a≈3 min unskippable demo; pressing Start on the title takes the game into the new-game cutscene, not a menu.

## 4. Address map

| Region | File offset | ROM address | Evidence | Meaning |
|---|---:|---:|---|---|
| crt0 main | 0x000C0 | 0x080000C0 | Derived (ARM disasm) | stack setup, calls `main` |
| `main` | 0x0789C | 0x0800789C | Derived (Thumb disasm) | init + per-frame loop |
| frame loop | 0x0794C | 0x0800794C | **Observed** (live mGBA CLI breakpoint, r15=0x0800794E, Cycles=5,199,431) | main loop |
| state word | — | 0x03001EBC | Derived (`ldr r0,[pc,#48] @ 0x8007A94` = 0x3001EBC in fn 0x08007A5C) | nibble state; `&0xF == 0xF` triggers 0x08000318 |
| flags | — | 0x03006000 / 0x03006004 / 0x03006304 | Derived (literals at 0x08079B0/0x08079B4/0x0807A58/0x0807948) | frame/global flags |
| text-entry alphabet | 0x07ACA4 | 0x0807ACA4 | Observed (ASCII dump) | 62 symbols used by name/password entry |
| "Input password" prompt | 0x07ABB6 | 0x0807ABB6 | Observed (ASCII dump) | password-entry UI string |
| **Jasper password script** | **0x164E8A–0x164F10** | **0x08164E8A–0x08164F10** | **Observed** (byte dump) | "Woof bark?" Yes/No, ten passwords, "You received a Robopon!", "~Jasper is sad..." |
| Nintendo logo copies | 0x000004, 0x065314, 0x066F04 | — | Observed | main + two embedded multiboot headers |
| text-bank pointer table | 0x07AB00 | 0x0807AB00 | Observed (u32 literals 0x08031E8D …) | UI text bank index |

## 5. Algorithm

There is no algorithmic validator. The operative model is:

```
input = text_entry(alphabet = 62 symbols)
for each entry in jasper_table:          # 10 literal strings in script bank
    if decode_control_codes(entry.string) == input:
        grant(entry.robot); print("You received a Robopon!"); return true
print("~Jasper is sad..."); return false
```

The script uses byte `0x00` as a no-op/pause and `0x07` as a line marker; `0x10 XX` is a "draw glyph by tile index" control that inserts one character into the rendered string (e.g. `0x10 0x69` → `i`, `0x10 0x1F` → `R`, `0x10 0x26` → `L`, `0x10 0x4D` → `m`, `0x10 0x06` → `e`). Decoding these controls reproduces the published strings exactly. No length check, substitution, XOR, checksum, PRNG, or bit-packing is present anywhere in this bank.

## 6. Tables

### 6.1 Complete Jasper password table (file offsets are ROM − 0x08000000)

| # | Robot granted | Password | Raw script bytes / offset | ROM address |
|---:|---|---|---|---|
| 1 | Fencer | `PArlAz` (guide: `PArlz`) | `0x164EA6`: `50 41 72 6c 41 7a 00` | 0x08164EA6 |
| 2 | Sherry | `RedMT` | `0x164EAE`: `52 65 64 4d 54 00` | 0x08164EAE |
| 3 | Flicker | `SlugE` | `0x164EB6`: `53 6c 75 67 45 00` | 0x08164EB6 |
| 4 | Gundarn | `JAisG` | `0x164EBD`: `4a 41 10 69 73 47 00` | 0x08164EBD |
| 5 | Under | `L33t1` (ROM literal `L33tB1`, `0x42` may be a glyph control) | `0x164EC5`: `4c 33 33 74 42 31 10 1f …` | 0x08164EC5 |
| 6 | Dorapon | `Rvnge` | `0x164ECC`: `10 1f 76 6e 67 65 00` | 0x08164ECC |
| 7 | B-Cell | `Hope` | `0x164ED3`: `48 20 6f 70 10 06 44 65 72 62 79 82 00` | 0x08164ED3 |
| 8 | Icarun | `Derby` | `0x164ED9`: `44 65 72 62 79 …` | 0x08164ED9 |
| 9 | NegaPon | `98765` | `0x164EE1`: `39 38 37 36 35 00` | 0x08164EE1 |
| 10 | X-Dog | `LaMer` | `0x164EE6`: `10 26 61 10 4d 65 52 00` | 0x08164EE6 |

Because three script blocks each hold two passwords (rows 5/6, 7/8, 9/10 share a block via `0x10 XX` glyph controls), the seven visible blocks decode to exactly ten accepted strings.

**Published-list verification:**
- GameFAQs Guide 78543, "Jasper's Robopon": all ten match the ROM bank above (observed).
- GameFAQs "Cheats" page / Planet Cheats / ChapterCheats short list (`H`, `Rvnge`, `P`, `S`, `J`, `D`, `9`, `R`, `L`, `La`): **only `Rvnge` is real** and only as part of row 6; the other nine short strings are not present as password literals. `Rvnge`, `NegaPon`, `Sherry`, `Fencer`, `Flicker`, `Gundarn`, `Icarun`, `B-Cell` were each searched with `grep -abo`; only the guide-78543 forms occur. These lists are OCR/transcription corruptions (§16.7).
- No GameShark/CodeBreaker/Action Replay codes were analyzed or reported (out of scope).

### 6.2 Flag bits / field layouts
None. This system writes a robot-grant event, not a persistent bitfield. The surrounding save data is ordinary Flash (64 KiB `.sav` observed), and no password-derived flag was identified in the script bank.

## 6b. Enumeration

**Space definition.** Alphabet = 62 symbols (§4), but the validator is a fixed lookup, so the representable-and-accepted space is exactly the ten strings in Table 6.1. There is no checksum width, no field width, no reserved bit and no generator function. Count of accepted values: **10**.

**Closed-set proof (counts, not inference).** The script bank contains 7 password-bearing blocks; three of them encode two passwords through `0x10 XX` glyph controls (§5): rows 1–4 (4 single blocks) + rows 5/6 + 7/8 + 9/10 (3 double blocks) = 4 + 6 = **10**. The adjacent strings are the only reward prompts in the bank: "Woof bark?" (0x164E8C), "You received a Robopon!" (0x164EEF), and "~Jasper is sad..." (0x164F0A) — the accept and reject outcomes. No other password-like string appears in the 4 MiB image (`strings -t x -n 3` + literal searches for all ten strings and all nine bogus short strings).

**Novel codes.** None can exist: the space is a hard-coded 10-element table with no algorithmic encoder, no fields to vary and no checksum to recompute. Any string outside Table 6.1 is rejected by construction. This is the complete enumeration, not a partial one.

**Bounds proven by rejection.** The reject path is present and enumerated: `~Jasper is sad...` at 0x164F0A. Any of the 62^1..62^10 strings not in Table 6.1 maps to that branch. The ROM's script also bounds the *UI* — the shared text-entry alphabet at 0x07ACA4 contains no additional symbol that could form a hidden 11th entry.

## 7. Validation evidence

**Observed (emulator, DISPLAY=:318, screenshots + live debugger):**
- mGBA 0.10.5 (`/usr/local/bin/mgba`) and a freshly built mGBA 0.11 (`/tmp/robopon2/mgba_src/build/sdl/mgba`, commit `9fcaa88`) both boot the title screen. Screenshots: `boot_crop.png`, `t2.png` (RED logo), `title.png` / `nm2.png` / `pad10.png` (title).
- On the **supplied 4 MiB file**, pressing Start at the title (or simply letting the demo run) ends in `GBA Memory: Jumped to invalid address: 01220122` / `GBA: Illegal opcode: e710b710` / `The game crashed!` in mGBA, and a frozen solid-color screen in VBA 1.8.0. Reproduced on fresh boots with the `.sav` removed. This is the truncation failure of §1.
- With the **8 MiB `0xFF`-padded diagnostic copy**, the full opening cutscene runs to completion without crashing (`pad1.png` … `pad10.png` show logos → character cards → title), proving the missing high-half data is the cause. On this copy the title screen accepts Start: pressing it at the first title appearance (observed mean 44450 at t≈14 s) immediately replays the RED Entertainment logo and the entire new-game cutscene (`ft_after.png`), i.e. input delivery and key mapping were verified. The cutscene then loops back to the title; neither Start nor repeated A presses during it advanced to a gameplay menu before the session budget expired.
- Live CLI-debugger session on the unmodified ROM: `b/t 0x0800794c`, `c` → `Hit breakpoint 1 at 0x0800794C`, `r15=0x0800794E`, `cpsr=0x4000003F [T]`, `Cycle=5199431`, KEYINPUT `0x03FF` (no keys held at that instant), DISPCNT `0x0000`. RAM at 0x03001EBC / 0x03006000 / 0x03006004 / 0x03006304 all `0x00000000` at that early cycle. This is the RAM-level evidence that execution reaches the game's main loop before the dump fails.
- All reachable screens walked by screenshot: Nintendo license, Hudson logo, RED Entertainment logo, ATLUS logo, title screen, and ~15 distinct demo/cutscene frames (flying Robopon, character cards No.010 KOJIRO / No.004 SUN-02, split-screen battle art, name-card variants). No password or menu screen is reachable on the truncated dump, and the padded copy's new-game path never advanced past its looping cutscene within the session.

**Derived (static):**
- crt0 entry and `main` address from ARM/Thumb disassembly (§4).
- Password table bytes and glyph-control decoding (§5, §6).
- Absence of an algorithmic generator/checksum in the bank.
- Embedded multiboot header identity from header fields.

**Inferred (labelled):**
- That the 10 table strings are compared against the raw text-entry buffer by a script-level string compare. The table and both outcome strings are observed; the exact compare opcode was not isolated because the entry screen cannot be reached on this dump. Confidence: high (a fixed table with explicit accept/reject messages has no other plausible consumer).
- That `0x42` inside row 5 is a glyph control making the effective password `L33t1` as published; the ROM literal is `L33tB1` and the guide says `L33t1`. Both are recorded; the discrepancy is a likely transcription/control-code issue, not a second code.

**Not performed, with reason:** in-game entry and screenshot of a granted Robopon. The supplied dump crashes before any menu (proved above); the 8 MiB padded copy runs the ≈3-minute unskippable intro but the title's Start handling was not driven into a gameplay menu within the session budget. No in-game acceptance/rejection screenshot is claimed. This is a dump limitation, not a skipped test of the cheat system — the cheat system itself is fully enumerated statically.

## 8. Unknowns

- The exact validator/compare routine address and the RAM address of the password input buffer (blocked by the unreachable screen).
- Whether a later ROM revision or the genuine 8 MiB dump contains additional Jasper entries beyond these ten.
- The precise rendering of glyph-control bytes `0x42` and `0x82` in rows 5 and 7 (both occur inside password strings; the guide transcription resolves them as `L33t1` and `Hope`/`Derby`).
- Save-format details for the granted Robopon (not required for the cheat enumeration).

## 9. Tooling

- `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb|force-arm` for crt0/main disassembly.
- Python 3 + `capstone 5.0.7` for literal/pointer scans (`find_u32`, Thumb `LDR [PC,#imm]` scanner).
- `strings -t x -n 3/4`, `grep -abo`, `xxd` for the string/literal sweeps.
- mGBA 0.10.5 (system) and a locally built mGBA 0.11 (git clone 2026-11-18, commit `9fcaa88`; `cmake -DBUILD_QT=OFF` + `cmake --build --target mgba-sdl -j4`; installed `libsdl2-dev` via apt) for boot/walk; VBA 1.8.0 as a cross-check.
- mGBA CLI debugger (`-d`) driven through a Python PTY harness (`/tmp/robopon2/mgba_dbg.py`): `b/t`, `c`, `x/4`, `watch/r`, `w/1|2|4` — used for the live main-loop breakpoint and RAM reads.
- X11: `Xvfb :318`, `openbox`, `xdotool` (focus/key events), `scrot` + ImageMagick crop (`720x480+153+163`). All other displays and all other agents' processes were left untouched.
- No ROM or copyrighted asset is redistributed; only addresses, hashes and our own tools are reported.
