# SKIPPED — Drill Dozer (GBA) — §0.2 story gate not closable after two attempts

Two focused reverse-engineering attempts were run on this ROM. The detailed
work is preserved in `Drill Dozer.md` (396 lines, now with `## 6b. Enumeration`)
and scratch artifacts in `/tmp/opencode/drilldozer*`, but the game's code-entry
system could not be brought to the full §0.2 bar, so the report is deliberately
**not indexed** rather than reported as a solved code system.

## What was established
- A real in-game code system is indicated by four independent published-source
  lists (22 accepted values: 3 unlock + 19 effect codes) and by a documented
  order-insensitivity. The exact space was defined: 10,000 ordered 4-digit
  displays collapsing to 715 unordered digit multisets, with 22 published
  accepted values as a lower bound.
- Derived novel codes absent from all published lists were produced by permuting
  published values (`4203` from `2403`, and `9032` from `2094`), predicted
  accepted by the documented order-insensitivity.

## What could NOT be closed (the §0.2 blockers)
- The **validator / code table was not recovered** after exhaustive static
  search: 34 encodings/transforms over the full 8 MiB (raw/BCD/u16/u32/nibble/
  tile-index/permutation/affine/per-position-key/unary/strided/ASCII-separator
  plus a Thumb writer scan) — all apparent clusters were false positives
  (compressed graphics, fonts, jump-table pointers).
- The **code-entry screen was not reached**. It is story-gated behind a Mega Bit
  flag (`0x0203463B = 2`) plus drilling a Super-Hard Block and a door; the room
  state byte `0x02000015` was observed (0x00 title, 0x16 Training Course, 0x18
  pit). Labelled savestate patches (room byte 0x17, X-coordinate sweeps 0-4000
  with drill-down, state-word sweeps, Save-menu Exit) never loaded the target
  room, and writing invalid room bytes crashed the emulator core.
- No on-screen code acceptance, no RAM proof, and no in-game near-miss rejection
  were obtained. The only observed rejection is gate-level (flag-only plus wrong
  position lands in the Skulker pit, not the Enigma Room).

## Decision
Per the audit bar (§0.2), a story-gated code system with no recovered validator,
no emulator-accepted novel code and no dynamic rejection bounds is not a
"Complete" report. After two attempts the remaining gap is a hard story gate
that the available harness cannot drive (savestate forcing crashes the core),
analogous to the MMBN and WinX Club story-gate deferrals. The ROM is documented
here and deferred rather than cycled a third time. A future session with a save
that has the Mega Bit flag and the drilled Super-Hard Block can close it by
entering a published code on the real screen, isolating the comparator, and
proving a near-miss rejection.

Date: 2026-11-22
