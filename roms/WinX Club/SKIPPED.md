# SKIPPED — WinX Club (GBA) — §0.2 not closable after three attempts

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

Three focused reverse-engineering attempts were run on this ROM. The detailed
investigation is preserved in `WinX Club.md` (and scratch artifacts in
`/tmp/winxclub*`), but the game's trophy-case "password" could not be
brought to the full §0.2 bar, so it is deliberately **not indexed** rather than
reported as a solved code system.

## What was established (strong, byte-level)
- The 4-digit trophy-case puzzle is real and uses **digit entry**, not an
  inventory item: Brandon's line "I'll give you the password ... It's 0001."
  carries literal ASCII `30 30 30 31` at file `0xD9BD41` and in the other four
  language banks. Known accepted values: `3921` (Cloud Tower) and `0001` (Red
  Fountain).
- Space bounded: 4 decimal digits = 10^4 representable values. Two "You have
  entered the correct code!" strings (file `0xD882C8` / `0xD88504`), zero
  distinct "wrong code" strings. Exhaustive literal searches found `3921`
  absent from ASCII/u16/u32/BCD/permutations across all 16.7 MB.
- The scene/UI gate was fully proven on the third attempt: a system handler
  selector byte at `0x03003C80` dispatches through a pointer table at
  `0x03003C84`; the warp-menu handler (index `0x14`, `0x0800EAB6`) is live at
  `0x03003CD4`; warp destinations are flag-gated by a bit array at
  `0x03003478` (flag `0x37` = Learning Annex/Alfea); and the scene-state byte
  is `0x02033C34` (Gardenia `0x03`, Alfea `0x16`). Patching the selector and
  scene byte in a savestate forced the Alfea display cases onto the screen.

## What could NOT be closed (the §0.2 blockers)
- The native accept comparator for the 4 typed digits was **not isolated** —
  the safe handler scripts (`0xF3D562`, `0xF3D66A`) carry no digit/compare
  constant, and no on-screen numeric keypad was found among the 24 handler
  indices or 39 enumerated scenes.
- No code was entered and accepted in-game, no novel code was minted, and no
  dynamic rejection bound was observed. The forced Alfea cases produced no
  dialog at 16 tested A/B positions (the safe interaction itself stayed
  gated).
- The two published values are therefore catalogued but **not confirmed** by
  this investigation; claiming a novel accepted code would be false.

## Decision
Per the audit bar (§0.2), a reachable-but-uncharacterized code system with no
validator model, no novel accepted code and no rejection bounds is not a
"Complete" report. After three attempts the remaining gap is the safe's input
path, which is story/scene-gated beyond what the available harness could
drive. The ROM is documented here and deferred, not cycled again. A future
session with a working input path to the trophy-case safe can close it: locate
the native 4-digit comparator behind the script opcode, enter `0001`/mint a
novel value, and prove a near-miss rejection.

Date: 2026-11-21
