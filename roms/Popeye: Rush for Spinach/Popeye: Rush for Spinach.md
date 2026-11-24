# Popeye: Rush for Spinach (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Popeye: Rush for Spinach/Popeye: Rush for Spinach.gba` |
| Size | 4,194,304 bytes (0x400000) |
| Header title | `POPEYE RFS` |
| Game code | `APOE` (US/Europe) |
| Maker code | `AF` |
| Version | 0x00 |
| MD5 | `a5bf85cd40533d76a1fb2b0b2f8d5b19` |
| SHA-1 | `25ecba1d1d14f497dec7fdc67f6666bb83127077` |
| SHA-256 | `edbe1680f9c15f642de8398e2fe96fdd1855c91f784c0a5b0ca298418c9e5c48` |

**Phase 0 header scan.** Single Nintendo logo at file offset 0x4 → one embedded GBA header, base 0x0; this is not a multigame pack. Entry word is `0xEA000030` (`b 0x080000C8`, not the stock `0xEA00002E → 0xC0`); the 8 bytes at 0x080000C0 are non-code (`CFBFEA0C 00000868`) and standard crt0 begins at 0x080000C8. Header complement byte is 0xC8 where a stock header would be 0xE0/E1, and the 16-bit header checksum is 0x0000 — the signature of a rebuilt/scene header (guide §16.1). No appended trainer data: the file is exactly 4 MiB and no sequence menu is present. The ROM is nonetheless a **pre-release/debug build**: strings at file 0xFA7B4 (ROM 0x080FA7B4) read `POPEYE`, `Mar  8 2005`, `20:34:58`, `<C> WWW;MAGICPOCKETS;COM`, `NOT FOR RELEASE OR PUBLIC PERFORMANCE`, `PRESS ANY KEY TO CONTINUE`. Treat all addresses below as specific to this exact hash.

## 2. Executive summary

This prototype build contains a **developer-intended password system** on `Options → Password`, with a 32-symbol on-screen keyboard and an 8-character entry. The alphabet is stored in plaintext at ROM 0x080FA618 and the entry screen is reachable and fully walkable (see §3 and §4).

Three results:

1. The only widely published 8-character code, **`F4BG*XT5`**, is **accepted** on a fresh state and produces the "Records / 100%" screen (Observed, screenshot `pw_result.png`, RAM buffer `0x03002DEF` = `46 34 42 47 2A 58 54 35`). The other published code, `FJBGWXZF`, is **rejected** on a fresh state (`INVALID PASSWORD`, RAM `0x0203EA4` = `FJBGWXZF`) — recorded as an unverified/incorrect published code for this revision (§16.7).
2. The password-screen handler at **0x080F4F54** contains **two undocumented, XOR-obfuscated fixed-code checks**. The expected byte arrays are at 0x080FA650 (`01 11 77 01 77 13`, key 0x42) and 0x080FA656 (`04 63 08 68 1E 6B 0F`, key 0x56). Decoding `expected[i] ^ (key + i)` yields **`CR3D1T`** (6 chars, "CREDITS") and **`R4P1D0S`** (7 chars, "RAPIDOS"). Neither string appears in any published list. `CR3D1T` was entered on the real screen; the acceptance branch ran (buffer cleared, stage flag set) — see §6b.
3. A hidden development message **`MOD7 ACTIVATED`** exists at 0x080F9AB0 and is loaded as a text argument by the code at 0x080DF522 (`ldr r0,[pc,#84] @ 0x080DF578; bl 0x080037F4`). Its trigger was not reached through the menu (see §8).

## 3. How to reproduce

Emulator: mGBA (SDL build) under Xvfb on `DISPLAY=:318`, `SDL_AUDIODRIVER=dummy`, scale ×3. Key map: A = `x`, B = `z`, L = `a`, R = `s`, Start = `Return`, Select = `Backspace`, D-pad = arrow keys. **Hold keys 0.28–0.35 s; 0.1 s taps are missed on the menu** (the password screen accepts 0.08 s hold). Ensure the mGBA window has X focus (`xdotool windowactivate --sync <id>`) before sending keys; a stale focus is the easiest way to get false "code rejected" results.

Exact menu path (all transitions need ~1 s to settle):

1. Boot → license screen → language select. Press `x` twice (first press highlights the flag, second confirms).
2. Demo plays. Press `Return` → "PRESS START" title screen.
3. Press `Return` with a **0.3 s hold** → main menu (`QUICK RUSH`).
4. Press `Right` five times: `QUICK RUSH → ADVENTURE → CHALLENGE → TIME RUSH → TEAM RUSH → OPTIONS`. Press `x` once, then `Down` once to open the options sub-list, then `Down`/`Up` to `PASSWORD`, then `x`.
5. Password grid: rows `01234567 / 89BCDFGH / JKLMNPQR / STVWXZ/*`, cursor starts on `0`. D-pad moves the cursor, A selects a character, B deletes one (and exits when empty), Start submits. Eight selections auto-submit.

Codes tested:

| Input | Result |
|---|---|
| `F4BG*XT5` | Accepted → Records, 100% burst (`pw_result.png`) |
| `F4BG*XT0` | `INVALID PASSWORD` — last character is checked (no alias) |
| `FJBGWXZF` | `INVALID PASSWORD` — published code not valid for this revision |
| `CR3D1T` + Start | Stage-1 acceptance branch (buffer cleared) |
| `CR3D1T` then `R4P1D0S` | Stage-2 check identified statically (§5); UI input path not reliably driven — see §8 |

Screenshots kept on disk in `/tmp/popeye/` (`title2.png`, `s3.png`, `after_start_long2.png`, `menu_main.png`, `walkmenu.png`, `optseq.png`, `pw_full.png`, `pw_result.png`, `pw_entered_F4BG*XT5.png`, `novel_start.png`, `fjresult2.png`, `st1c.png`).

## 4. Address map

File offsets map 1:1 to ROM addresses as `ROM = 0x08000000 + file_offset`.

| Address (ROM) | Meaning |
|---|---|
| 0x08000000 / 0x080000C8 | Entry branch / real crt0 start |
| 0x080F9AB0 | `"MOD7 ACTIVATED\0"` |
| 0x080F9AC0 | `"PACK\0"` |
| 0x080F9AA0 | 4-word table `0x04000008/0xA/0xC/0xE` preceding the MOD7 string |
| 0x080DF522 | Loads 0x080F9AB0 and calls text routine 0x080037F4 |
| 0x080FA5F8–0x080FA617 | Font/tile-index table and u16 glyph indices 0x83–0x8D |
| 0x080FA618 | `"0123456789BCDFGHJKLMNPQRSTVWXZ/*\0"` — 32-symbol password alphabet |
| 0x080FA650 | Obfuscated stage-1 code bytes `01 11 77 01 77 13` (key 0x42) |
| 0x080FA656 | Obfuscated stage-2 code bytes `04 63 08 68 1E 6B 0F` (key 0x56) |
| 0x080F4E60 | Generator: packs game state → 5-bit values → alphabet chars |
| 0x080F4F54 | Password-screen state machine (6-char and 7-char hidden-code checks) |
| 0x080F5374–0x080F53B8 | Stage-1 check: count==6, `input[i] == expected[i] ^ (0x42+i)` |
| 0x080F5408–0x080F5466 | Stage-2 check: count==7, `input[i] == expected[i] ^ (0x56+i)` |
| 0x080F7C0C / 0x080F7C78 | Alphabet char↔5-bit conversion helpers (no direct BL callers found) |
| 0x080E25F8 / 0x080E26C8 | `set_bits` / `get_bits` with byte-swap (ror 16, masks 0xFF00/0x00FF) |
| 0x080FC1A8–0x080FC4C0 | English text bank; strings are `0x04`-prefixed and NUL-terminated |
| 0x03002DEF | 8-byte entered password buffer (IWRAM) |
| 0x03002E28 | Byte flag written to 1 on password-screen entry |
| 0x0203EA4 (savestate raw 0x20EA4) | Temporary stack copy of the submitted 8-char string |

Savestate layout (mGBA `.ss1` = PNG + zlib `gbAs` chunk, 397,312 raw bytes for this ROM): IWRAM `0x03000000` at raw `0x19000`, EWRAM at raw `0x21000`. The password buffer at raw `0x1BDEF` → `0x03002DEF`.

## 5. Algorithm

**Alphabet → value.** `0x080FA618` defines 32 symbols in order; each entered character maps to its index 0–31 (5 bits), so an 8-character password is a 40-bit word. The conversion routines at 0x080F7C0C / 0x080F7C78 and the bit helpers at 0x080E25F8 / 0x080E26C8 perform the 5-bit packing with a byte-swap (16-bit rotate) at each 32-bit word boundary.

**Generator (0x080F4E60).** Reads progress bytes at 0x03002E50, 0x03002DD8 and an 11-byte array at 0x03002DE4, assembles a bitfield via 0x80F4DD4/0x80F4DFC/0x80F4830 and `set_bits`, then emits `alphabet[get_bits(5, packed, i*5)]` for each of 8 characters. This is why the published codes are not stored literally in the ROM (§3.4): they are algorithmic.

**Hidden fixed-code checks (0x080F4F54).** These are simple, deliberately obfuscated comparisons, independent of game state:

```
stage1_ok(count==6): for i in 0..5:
    assert entered[i] == (expected1[i] ^ (0x42 + i)) & 0xFF   # expected1 @ 0x080FA650
stage2_ok(count==7 and stage1_ok):
    for i in 0..6:
        assert entered[i] == (expected2[i] ^ (0x56 + i)) & 0xFF   # expected2 @ 0x080FA656
```

Decoded expected strings: stage 1 = `CR3D1T`, stage 2 = `R4P1D0S`. On stage-2 success the handler sets its state word to `0x58` and returns; on invalid input it shows `INVALID PASSWORD` and displays the submitted string in the bottom slots.

## 6. Tables

Alphabet (index → char):
`0-9 → 0123456789`, `10-19 → BCDFGHJKLM`, `20-29 → NPQRSTVWXZ`, `30 → /`, `31 → *`.

Published codes verified in this ROM:

| Source | Code | Literal in ROM? | In-game result |
|---|---|---|---|
| 3rd party cheat indexes | `F4BG*XT5` | No (algorithmic) | **Accepted** — 100% Records screen |
| 3rd party cheat indexes | `FJBGWXZF` | No | **Rejected** — INVALID PASSWORD on fresh state |
| AtariAge forum | `KRRKZHNB` | No | Not entered (treated as a progress password, not a super code) |

Undocumented codes recovered from the ROM (in no published list):

| Code | Length | Key | Obfuscated array | Evidence |
|---|---|---|---|---|
| `CR3D1T` | 6 | 0x42 | 0x080FA650 | Derived from the comparator; stage-1 acceptance branch observed |
| `R4P1D0S` | 7 | 0x56 | 0x080FA656 | Derived from the comparator; requires stage 1 first |

## 6b. Enumeration

**Space definition.** Entry surface: 8 positions × 32 symbols = 32^8 = **1,099,511,627,776** representable strings; the payload is 40 bits (8 × 5-bit symbols). Stored-code set: two 6/7-character fixed developer sequences plus at least one algorithmic 8-character progress code family (generator at 0x080F4E60). All published lists combined contain only two 8-character strings; the ROM contains no literal copy of either.

**Novel code.** `CR3D1T` is absent from 3rd party cheat indexes, 3rd party cheat index results for this title; it is recovered directly from the ROM's obfuscated expected-byte array, exercises a mode (developer credits / mod gate) that no published code mentions, and was entered on the real password screen. RAM/screen evidence: after entry + Start, the 8-slot buffer at 0x03002DEF was cleared (all 0x5F/blank) and the handler took the `r7+0x20 = 1` acceptance branch; no `CR3D1T` string remains in RAM (`state_st1_after.ss1`). The paired stage-2 sequence is `R4P1D0S`.

**Bounds proven by rejection.**
- `F4BG*XT0` (one symbol changed in the last position) → `INVALID PASSWORD` on screen and the string `F4BG*XT0` present in the stack copy at 0x0203EA4 — proves the 8th character is significant and that no trivial trailing-symbol alias exists.
- `FJBGWXZF` (published, wrong for this revision) → `INVALID PASSWORD` with the exact string in RAM — proves the rejection is the game's validator, not a mistyped input.
- The stage-1 comparator bounds the count to exactly 6 (`cmp r0,#6` at 0x080F5376) and stage 2 to exactly 7 (`cmp r0,#7` at 0x080F5410); an 8-character submission cannot reach either branch.

**Coverage limit.** The 5-bit payload decoder has no direct BL callers (0x080F7C0C/0x080F7C78 are uncalled in this image), so the complete set of *algorithmic* 8-character codes was not enumerated offline; the deliverable above is the full enumeration of the *fixed-code* surface plus one verified algorithmic code.

## 7. Validation evidence

- **Observed**: all menu screens (screenshots listed in §3); `F4BG*XT5` → 100% Records screen; password buffer `0x03002DEF = 46 34 42 47 2A 58 54 35` in `state_pw_result.ss1`; `F4BG*XT0` and `FJBGWXZF` → INVALID PASSWORD with their exact strings in RAM; stage-1 entry clears the buffer.
- **Derived**: the obfuscation keys and both hidden codes are decoded directly from comparator instructions at 0x080F5374–0x080F5466 and the literal arrays they load (0x080FA650/0x080FA656); the generator's state-byte reads at 0x080F4E60; the MOD7 message pointer at 0x080DF522.
- **Inferred**: that `CR3D1T` is a "credits/mod" gate rather than a simple score code (the message it ultimately prints was not observed); that stage 2 arms a further development feature. These are labelled inference, not observation.
- No Ghidra/REA decompilation was usable: raw-ARM auto-analysis does not recognise this ROM's Thumb functions (guide §5.5/§11), so all code claims were verified with `arm-none-eabi-objdump -M force-thumb` against the exact bytes.

## 8. Unknowns

- The stage-2 UI sequence could not be driven reliably: the on-screen cursor advances/wraps in a way that made scripted multi-character entry land on wrong symbols after stage 1 accepted (the entered 7-character strings differed from `R4P1D0S`). The stage-2 *check* and its expected bytes are proven statically; its in-game effect is not observed.
- `MOD7 ACTIVATED` is proven to be a loadable message, but no input path to it was found among the six menu entries or the password codes tested. It may be gated by a link/transfer event or a different prototype build path (guide §16.3/§16.18).
- The full 40-bit algorithmic code family (valid checksum set) was not enumerated; only the published `F4BG*XT5` was executed. `FJBGWXZF` may be valid only after specific progress or in a different region/revision.
- `KRRKZHNB` (AtariAge) was not entered; it is likely a level-completion password rather than an options-screen code.

## 9. Tooling

`strings -t x`, `grep -abo`, `xxd`, `arm-none-eabi-objdump -M force-thumb`, Python 3 + capstone 5.0.7 (xref/BL scanners `xref.py`, `blscan.py`), mGBA SDL under Xvfb `:318` with `SDL_AUDIODRIVER=dummy`, `xdotool`/`scrot`/ImageMagick, mGBA `-d` console debugger (`watch/r 0x03002DEF`) and GDB stub (`gdb-multiarch`) for RAM reads, custom `ssdiff.py` (zlib-decompress mGBA `.ss1` `gbAs` chunk) and `enterpw.py` (grid navigation helper). REA/Ghidra 12.1.4 was opened but not used for decompilation because Thumb functions were not recognised. No ROM or copyrighted asset is redistributed; only addresses, hashes and derived code strings are published.
