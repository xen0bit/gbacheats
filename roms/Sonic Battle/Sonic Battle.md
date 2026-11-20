# Sonic Battle (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Sonic Battle.gba` (16,777,216 bytes / 0x01000000) |
| Header title | `SONICBATTLE` |
| Game code / maker | `BSBE` / `78` (PAL, Rev.00) |
| `file(1)` | `"SONICBATTLE" (BSBE78, Rev.00)` |
| Version / complement / checksum | 0x00 / 0x8E / 0x0000 |
| Entry branch | `0xEA00002E` → `0x080000C0` (stock crt0, no cracktro/trainer patch) |
| MD5 | `100579ef01225c620560f88e65ca423a` |
| SHA-1 | `8cf4fbbe73f6b1907ab9997caab4c4e7d9708937` |
| SHA-256 | `536c7d7bdb37862c79d048c351b0c61ffe8380c71e1be8b15d537549272b72a9` |

Phase 0 embedded-header scan: two 156-byte Nintendo logos exist. The second,
at file offset `0xEEB690`, is a separate multiboot/test image titled
`AGB TEST PRG` (code `AGBJ`, maker `8P`, entry `0xEA000013`); it is not a
trainer and is not the running game (no boot selector, stock entry word).
No Scene cracktro or appended cheat device was found.

## 2. Executive summary

The game has one developer-intended cheat surface: **five-symbol passwords
entered at the SONICTEAM building in Emerl's Story**, each awarding a combo
card. There is no other password, button-code, or hidden debug menu in the
shipped retail image.

The system is a **closed, exact-match lookup table**, not an algorithm:

* Input is five glyph codes from the on-screen keyboard's 62 usable symbols
  (10 digits + 26 capitals + 26 lowercase). Keyboard row table:
  `0x08EDCC3C` (35 rows × 10 cells; rows 20–26 are the ASCII page,
  glyphs `0x80`–`0xBD`; `0x338` is the empty cell).
* The validator at **`sub_080368DC` / `0x080368DC`** pads the input with
  `0xFFFE`, then walks exactly `gUnk_08158672` = **9** pointers at
  `0x08EDCCE8`, comparing all five glyphs literally. There is no checksum,
  PRNG, arithmetic, alias mapping, or generated-code path.
* All nine literals are present verbatim (as 5 × u16 glyph codes + `0xFFFE`)
  at `0x081585F4`–`0x0815865F` (12-byte stride). All nine published codes
  are correct — no published typo or region mismatch was found.
* On match, flag bit `gUnk_0807163C[n]` (bits `0x1`..`0x100`) is OR'ed into
  the save word at `0x03002110+0x4DC` = `0x030025EC`, card record
  `gUnk_08158660[n]` (`0xEE` + 8n) is incremented, and the award screen is
  entered. On mismatch the failure handler `0x08036D1D` runs and no save bit
  changes.

Because the accepted set is a nine-entry table, **no unpublished accepted
code can exist**. This is the bounded negative result of §6b, not an
untested case: the table count is 9, the tenth pointer slot is not a glyph
string, and a novel code entered on the real screen was rejected with the
save flag word staying zero.

## 3. How to reproduce

1. mGBA 0.10.5 under Xvfb `:316`, `SDL_AUDIODRIVER=dummy`, `-3` scale.
   Window origin was `(154,184)`; crop `720x480+154+184`.
2. Default SDL keymap: A = `x`, B = `z`, L = `a`, R = `s`,
   Start = `Return`, Select = `BackSpace`, D-pad = arrows. Hold ≈100 ms.
3. **Normal path:** clear Shadow's episode, start Emerl's episode, go to
   Central City → SONICTEAM building → choose the password entry → type a
   5-symbol code → Start. (The story gate was not replayed in this run; see
   §8. The screen itself was reached and exercised directly, below.)
4. **Lab path used for verification (disclosed):** the password/name UI is
   the same screen; the byte at `0x03005380` selects password mode
   (1 = validate, 0 = save name). With the mGBA `-d` pty debugger, break at
   the name-entry screen and write `w/1 0x03005380 0x01`, then continue.
   Enter symbols with the on-screen keyboard and press Start. This reaches
   the identical validator and award/failure screens without replaying the
   story; all key presses and all RAM checks were made on the real screen.
5. Verified codes (all nine; exact case): `75619`, `OTrOI`, `yU3Da`,
   `ArmIa`, `AhnVo`, `alogK`, `ZAhan`, `tSueT`, `EkiTa`.
   Novel negative test: `aaaaa`.

## 4. Address map

| Item | Address (ROM / RAM) | Evidence |
|---|---|---|
| Password/name input handler + validator | `0x080368DC` (`sub_080368DC`, length `0x408`) | Derived (decomp match) + observed |
| Input glyph buffer (5 halfwords + `0xFFFE`) | `0x03005200` | Observed (`x/2`: `0087 0085 0086 0081 0089 FFFE`) |
| Password-count byte | `0x08158672` = `0x09` | Derived |
| Password pointer table (9 entries) | `0x08EDCCE8` .. `0x08EDCD08` | Derived |
| Password literal strings (9 × 12 B) | `0x081585F4` .. `0x0815865F` | Derived |
| Card record IDs (u16[9]) | `0x08158660` | Derived |
| Unlock flag masks (u32[9]) | `0x0807163C` | Derived |
| Save block base | `0x03002110` | Derived |
| Password-clear flag word (save +0x4DC) | `0x030025EC` | Observed before/after |
| Per-entry counts (save +0x120) | `0x03002230` + id | Derived |
| Keyboard row pointer table | `0x08EDCC3C` (35 rows × 10 cells) | Derived |
| 1bpp font bitmaps / advance table | `0x08071B7C` / `0x0807173C` | Derived (rendered to confirm glyph codes) |
| Award block (`fn,id,id,id,unkA,unkB`) | `0x03005330` | Observed |
| Password-mode flag | `0x03005380` | Observed (written 0→1) |
| Success/failure fade handlers | `0x08036D4C` / `0x08036D1C` | Derived |
| Award display | `0x080402B0` | Derived + observed |

## 5. Algorithm

Precise reimplementation of `sub_080368DC` (password branch):

```c
if (pressed & START) {
    if (password_mode) {                       // byte 0x03005380 != 0
        for (i = cursor_len; i <= 5; i++) input[i] = 0xFFFE;
        for (n = 0; n < *(u8*)0x08158672; n++) {   // n = 0..8
            s = password_ptr[n];                   // 0x08EDCCE8[n]
            t = input;                             // 0x03005200
            for (i = 0; i <= 5 && s[i] == t[i]; i++) {
                if (s[i] == 0xFFFE) {              // all five matched
                    id = card_id[n];               // 0x08158660[n]
                    if ((save_bits & flag_mask[n]) == 0) {  // 0x0807163C[n]
                        if (save_count[id] == 0xFF) save_count[id] = 0;
                        if (save_count[id] > 8) break;
                        save_bits |= flag_mask[n];
                        save_count[id]++;
                        award.fn = 0x080402B0;
                        award.id0 = award.id1 = award.id2 = id;
                        award.unkA = 1; award.unkB = 0;
                        actor.state = 0x08036D4C;   // success fade
                        return;
                    }
                }
            }
        }
        actor.state = 0x08036D1C;                 // failure fade
    }
    ... // non-password branch simply stores the typed name and exits
}
```

## 6. Tables

### 6.1 Complete accepted set (the entire table)

| # | Literal | Glyph codes (u16 LE) | ROM address | Flag bit (save +0x4DC) | Card id | Award |
|---:|---|---|---|---|---|---|
| 0 | `75619` | 87 85 86 81 89 | `0x081585F4` | `0x001` | `0x0EE` | Sonic combo |
| 1 | `OTrOI` | 98 9D B5 98 92 | `0x08158600` | `0x002` | `0x0F6` | Tails combo |
| 2 | `yU3Da` | BC 9E 83 8D A4 | `0x0815860C` | `0x004` | `0x0FE` | Knuckles combo |
| 3 | `ArmIa` | 8A B5 B0 92 A4 | `0x08158618` | `0x008` | `0x106` | Shadow combo |
| 4 | `AhnVo` | 8A AB B1 9F B2 | `0x08158624` | `0x010` | `0x10E` | Rouge combo |
| 5 | `alogK` | A4 AF B2 AA 94 | `0x08158630` | `0x020` | `0x116` | Amy combo |
| 6 | `ZAhan` | A3 8A AB A4 B1 | `0x0815863C` | `0x040` | `0x11E` | Cream combo |
| 7 | `tSueT` | B7 9C B8 A8 9D | `0x08158648` | `0x080` | `0x126` | E-102 combo |
| 8 | `EkiTa` | 8E AE AC 9D A4 | `0x08158654` | `0x100` | `0x12E` | Chaos combo |

Every entry is terminated by `FF FE`. `0x08158660[9]` =
`{00EE,00F6,00FE,0106,010E,0116,011E,0126,012E}`;
`0x0807163C[9]` = `{1,2,4,8,0x10,0x20,0x40,0x80,0x100}`.

### 6.2 Glyph alphabet (keyboard rows 20–26 of `0x08EDCC3C`)

`0-9` → `0x80-0x89`; `A-Z` → `0x8A-0xA3`; `a-z` → `0xA4-0xBD`;
empty cell → `0x0338`. 62 usable symbols; the keyboard has 35 pages of 10
cells (350 cells), the other pages being Japanese kana/punctuation.

## 6b. Enumeration

**Space definition.** Five positions, each drawn from 62 usable glyph codes
→ `62^5 = 916,132,832` representable strings. The validator compares the
five glyphs literally to a fixed table; there is no checksum, no field
layout and no generator. The **complete accepted set has exactly 9 members**
(`*(u8*)0x08158672 == 9`), listed in §6.1.

**Completeness proof.**
1. Static: the validator's only accept path is the `n < count` loop at
   `0x08036920`–`0x08036A1E`; count is the byte `0x08158672` = 9; it reads
   only `0x08EDCCE8[n]` and compares every glyph with `cmp`/`beq`
   (`0x08036940`, `0x08036A14`). No other comparison path, hash or PRNG
   exists in the matched function.
2. Data: the nine pointer slots resolve to the nine strings above. Slot 9
   (`0x08EDCD0C`) points to `0x08159F94` whose bytes
   (`00 00 C0 40 ...`) are not glyph codes — no hidden tenth entry.
3. Empirical: all nine published literals were located in the ROM at the
   predicted 12-byte stride, and code `75619` was accepted on the real
   screen (below). A ten-thousand-code search would find nothing new
   because the table—not a checksum—is the definition of acceptance.

**Novel-code experiment and bounds by rejection.** `aaaaa`
(glyphs `A4 A4 A4 A4 A4`, not in any published list) was typed on the real
password screen and submitted:

| Observation | `75619` (published) | `aaaaa` (novel) |
|---|---|---|
| Input buffer `0x03005200` | `0087 0085 0086 0081 0089 FFFE` | `00A4 00A4 00A4 00A4 00A4 FFFE` |
| Flag word `0x030025EC` | `0x00000001` (bit 0 set) | `0x00000000` |
| Award block `0x03005330` | `080402B1 00EE00EE 010100EE 00000001` | all zero |
| On-screen result | "RARE" card award screen with Sonic | failure transition (no card) |

This is a *bounded* result: because the accept predicate is exact equality
against nine fixed strings, any of the other ~916 million representable
inputs is rejected by the same path; `aaaaa` is a concrete in-game witness.
No unpublished accepted code exists to mint — reporting one would be false.

## 7. Validation evidence

* **Observed** — title/intro/name-entry/mode-select/options/episode-select/
  battle-mode/mini-games/training screens and screenshots; published code
  `75619` accepted with award screen and RAM flag `0x00000001`; novel code
  `aaaaa` rejected with flag word `0`; glyph buffer contents read from
  `0x03005200`; keyboard glyph codes read from `0x03005200` after entering
  known characters; second GBA header at `0xEEB690`.
* **Derived** — validator and data tables from the byte-matching decomp
  `sub_080368DC` (SHA-1 of the ROM matches the decomp's required dump);
  literal table decoded with the rendered 1bpp font; all nine published
  literals located in ROM.
* **Inferred** — the normal story gate for the SONICTEAM building requires
  reaching Emerl's episode (not replayed; the password-mode flag was
  written directly to exercise the same screen). The `0x03002110` save-bit
  names (Sonic/Tails/… combos) are inferred from card-order and character
  names in the same bank, not from an in-game banner.

No prompt-injection content was encountered in the fetched pages or ROM.

## 8. Unknowns

* The story progression path to Emerl's episode was not cleared in this run;
  the password screen was entered via the `0x03005380` mode flag on the
  identical UI. This does not affect the validator result.
* The standard in-battle pause menu was not enumerated separately (a
  navigation attempt landed in a cutscene instead). Static scans of all
  decoded text banks found no `DEBUG`, `MENU`, `PASSWORD`, `CHEAT` labels
  outside ordinary dialogue, and the matched-function inventory contains no
  debug-menu dispatcher; a hidden pause debug menu is therefore unlikely
  but not proven absent by a live walk.
* `counts[id] > 8` guard semantics for already-owned cards were not driven
  to the 9th repeat (the unique flag bit prevents re-award first).

## 9. Tooling

* `/usr/local/bin/mgba` 0.10.5 (Xvfb `:316`, openbox, `SDL_AUDIODRIVER=dummy`),
  `-d` pty debugger driven by `dbgclean.py` (Ctrl-C break, `x/2`, `w/1`, `c`,
  `save`/`load`), `xdotool` key injection, `scrot` + ImageMagick crops.
* Capstone/objdump (`arm-none-eabi-objdump -M force-thumb`), Python scripts
  `ssdiff.py`, `glyphs2.png` font render, `pwtest.py`, `finaltest2.py`.
* External lead only: `nicklesimba/sonic-battle-decomp` and `phase/sbhs`
  (documentation/source, no ROM or assets copied into this report).
* No ROM or copyrighted assets are redistributed; only addresses, hashes,
  and the nine published literals are recorded.
