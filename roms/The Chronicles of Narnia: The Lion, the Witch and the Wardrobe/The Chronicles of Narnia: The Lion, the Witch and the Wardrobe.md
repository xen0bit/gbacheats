# The Chronicles of Narnia: The Lion, the Witch and the Wardrobe (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `The Chronicles of Narnia: The Lion, the Witch and the Wardrobe.gba` |
| Size | 16,777,216 bytes (0x01000000) |
| Header title | `NARNIA LWW` |
| Game code / maker | `B2WE4Q` / `4Q` (Buena Vista Games), revision 0x00 |
| Entry word | `0xEA00002E` → branch to `0x080000C0` (stock CRT0, §16.1 clean) |
| Header checksum | `0x00E9`, complement `0x00` |
| MD5 | `291b90df9403047a5064a1a2e71ed430` |
| SHA-1 | `fea89a96320771ba69354f5452610327aad49ec0` |
| SHA-256 | `33f3b74cebf9b1577cfbc8967fb7769529d8e458ae2d081784a4885d710df7b6` |

## 2. Executive summary

This game has a **developer-intended 6-button cheat system**, not a password system. There is no on-screen keyboard and no password text field. All visible UI text is stored as font/tile indices, so `strings` finds no in-game labels at all (only the 12-byte header) — this is the §11 "not ASCII" case, not evidence of a missing feature.

The system is a **closed, hard-coded table of exactly 12 six-press sequences** at ROM `0x0804C1C4` (12 × 6 × 4 bytes). Each press is converted to a prime-number token; a per-position weighted checksum must match a parallel 12-entry checksum table at `0x0804C190`, then the six tokens must match the corresponding code row. There is no algorithmic generator — but the key mapping contains a deliberate alias: **Down and Select both map to the token `0x2B` (43)**. This makes `2^k` button spellings per code, most of which appear in no published list.

A novel spelling — **Up, R (shoulder), Select, Left, Left, Right (D-pad)** — was entered in-game, accepted (RAM flag `0x03004180` bit 2 set), and produced the visible "Chapter 2 / Edmund and the White Witch" banner. A wrong-button variant was rejected with the flag unchanged, proving the bounds.

**Important correction to published lists:** several widely copied lists write `Right`/`Left` where the game actually requires the shoulder buttons **R**/`L`. The correct unlock-all-chapters opener is shoulder **R**, shoulder **L**, not D-pad. The published "interchangeable Down/Select" note is real and is explained by the shared token.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 under Xvfb `:318`, `SDL_AUDIODRIVER=dummy`, window focus via `xdotool windowfocus` + XTEST keys, 90–100 ms holds.
* Keymap verified by reading `KEYINPUT`-derived state at `0x03004110`: `x`=A(1), `z`=B(2), `BackSpace`=Select(4), `Return`=Start(8), arrows=D-pad (Right 0x10, Left 0x20, Up 0x40, Down 0x80), `s`=R(0x100), `a`=L(0x200).
* Menu path: language → English (A); legal splash (A); title (Start); main menu → New Game → Chapter Select → A → advance dialogue with A until playable.
* **Code entry condition (observed):** scene word at `0x03004610` must be `0x11` (17, normal gameplay) for codes 1–11, or `0x0A` (10, Chapter Select) for code 0. It is `0x01` while the "Pause" overlay is up, so published advice to "pause then enter" is unreliable in this build — unpause first. Wait until dialogue is finished; keys pressed during dialogue are consumed.
* Savestate technique: `Shift+F1..F9` then decompress the PNG `gbAs` chunk (zlib) to a 397,312-byte image; IWRAM starts at raw `0x19000`, so `0x03003540` is raw `0x1C540`, `0x03004180` is raw `0x1D180`, `0x03004610` is raw `0x1D610`.

### Codes tested in emulator

| Sequence | Result |
|---|---|
| `Up, R, Down, Left, Left, Right` (published skip-chapter, correct shoulder R) | Accepted; Chapter 2 banner shown (Observed) |
| `Up, R, Select, Left, Left, Right` (**novel**) | Accepted; Chapter 2 banner shown (Observed) |
| `Up, Right(D-pad), Down, Left, Left, Right` (published list with wrong button) | Rejected; flag stayed 0, no chapter change (Observed) |
| `R, L, Up, Up, Left, Right` at Chapter Select | Validator accepted, flags `0x03003560=1`, `0x03004178=0x10` set; chapters did not visibly unlock in this session (Observed RAM; visible effect Inferred/unconfirmed) |

## 4. Address map

| Address | Meaning |
|---|---|
| `0x0801B4C8` | Global input handler: reads `0x04000130`, XOR `0x03FF`, edge detection, calls cheat handler when scene ∈ {10,17} |
| `0x08011F4C` | Per-key cheat recorder: maps pressed mask → prime token, updates checksum and 6-slot history, validates at every 6th press |
| `0x08012190`–`0x0801228A` | Validator: checksum lookup then 6-token table comparison, 12 iterations (`cmp r5,#11`) |
| `0x08012298` | Acceptance stub: sets `0x03004624=0xB6`, `0x03004180 \|= 4`, `0x03004620=4`, dispatches effect |
| `0x080122D0` | Jump-table base pointer (`0x080122D4`); 12 handlers: `0x08012304`, `0x08012334`, `0x080123EC`, `0x08012400`, `0x08012458`, `0x0801248E`, `0x08012518`, `0x0801257A`, `0x080125FC`, `0x08012620`, `0x08012804`, `0x0801285C` |
| `0x0804C178` | Weighted position table: `u32[6] = {2,3,5,7,11,13}` |
| `0x0804C190` | Checksum table: 12 `u32` values (see §6) |
| `0x0804C1C4` | Code table: 12 rows × 6 `u32` prime tokens (24-byte stride), ends at `0x0804C2DC` |
| `0x03003540` | 6 × `u32` rolling key-history buffer |
| `0x03003558` | History write index (u8, 0–5; wraps and triggers validation) |
| `0x0300355C` | Accumulated weighted checksum (u32) |
| `0x03003560` | Unlock byte set by code 0 |
| `0x03004178` | Unlock byte set by code 0 (`0x10`) |
| `0x03004180` | Acceptance flag; bit 2 (`0x04`) set for every accepted code |
| `0x030041C0` | Input state struct (+0x10 held, +0x14 pressed, +0x16 released, +0x18 previous) |
| `0x03004610` | Scene word: 17 = gameplay (codes accepted), 10 = Chapter Select, 1 = Pause |
| `0x03004620` / `0x03004624` | Cheat-effect scratch word / byte written on acceptance |

## 5. Algorithm

```
prime = {A:0x17, B:0x1D, Select:0x2B, Start:0x2F, Right:0x25,
         Left:0x1F, Up:0x29, Down:0x2B, R:0x13, L:0x11}   # Select == Down

on_key_press(mask):
    if scene not in {10, 17}: return
    t = prime[mask]; i = history_index
    checksum += t * WEIGHTS[i]           # WEIGHTS = [2,3,5,7,11,13]
    history[i] = t
    history_index = (i + 1) mod 6
    if history_index != 0: return
    match = -1
    for n in 0..11:
        if checksum == CHECKSUM[n] and all(history[j] == CODE[n][j] for j in 0..5):
            match = n; break
    if match >= 0 and (match != 0 or scene == 10) and (match == 0 or scene == 17):
        apply_effect(match)
    checksum = 0; history[:] = 0
```

The checksum is a *pre-filter* (finds the candidate row); the six-token comparison is the actual code. Both must hold. Because Select and Down share `0x2B`, swapping them at any position leaves both the token row and the checksum unchanged.

## 6. Tables

Token legend: `R`/`L` = shoulder buttons; `Right`/`Left` = D-pad; `S/D` = Select or Down (alias).

| # | ROM row | 6-button sequence | Checksum | Published effect |
|---|---|---|---|---|
| 0 | `0x0804C1C4` | R, L, Up, Up, Left, Right | `0x57B` | Unlock all chapters (Chapter Select only) |
| 1 | `0x0804C1DC` | Up, R, S/D, Left, Left, Right | `0x571` | Skip to next chapter |
| 2 | `0x0804C1F4` | S/D, R, A, L, Left, Right | `0x4AF` | Restore health |
| 3 | `0x0804C20C` | Left, A, Left, S/D, S/D, S/D | `0x653` | +5 of each consumable |
| 4 | `0x0804C224` | A, L, S/D, A, Right, Up | `0x585` | Toggle ice mode |
| 5 | `0x0804C23C` | Right, Left, Left, S/D, Up, S/D | `0x661` | Toggle cold system |
| 6 | `0x0804C254` | Right, L, S/D, A, Left, S/D | `0x579` | Toggle invincibility |
| 7 | `0x0804C26C` | A, L, S/D, R, Right, Right | `0x535` | Cycle snow effect |
| 8 | `0x0804C284` | Up, S/D, S/D, S/D, S/D, Up | `0x6C5` | Increase attack ability |
| 9 | `0x0804C29C` | A, S/D, Left, S/D, Right, Up | `0x623` | Toggle armor costume |
| 10 | `0x0804C2B4` | S/D, B, L, S/D, A, Left | `0x4BF` | Undocumented in most lists ("new code") |
| 11 | `0x0804C2CC` | A, A, B, B, L, R | `0x381` | Undocumented in most lists ("new code") |

All 12 rows satisfy `checksum == Σ token[j] × WEIGHTS[j]`, verified in Python (`decode.py`). Rows 10 and 11 match the two "new codes" on classicgamehacking.com, confirming the table is the same SKU.

Published sources consulted (data only): supercheats.com, cheathappens.com, classicgamehacking.com, gamerstemple.com, gamehacking.org, etherealgames.com, almarsguides.com. Action Replay / CodeBreaker / GameShark codes from those pages are **out of scope** and were not used.

## 6b. Enumeration

**Space definition.** Input domain is 10 buttons × 6 presses = 1,000,000 possible sequences; the on-screen token alphabet is 9 distinct primes because Select≡Down, so at most 9^6 = 531,441 distinct token sequences. The accepted set is **exactly 12 rows**, bounded three ways: (a) the validator loop is `cmp r5,#11` (0–11), (b) the checksum table has 12 entries, (c) the code table ends at `0x0804C2DC` and is followed immediately by unrelated byte tables. No password/button-code keyboard screen exists; there is nothing else to enumerate.

**Novel code (not in any published list):** `Up, R(shoulder), Select, Left, Left, Right(D-pad)`.
Every published spelling of this effect uses **Down** (or, incorrectly, D-pad Right) at press 3; none uses **Select**. Because `prime[Select] == prime[Down] == 0x2B`, the token row and checksum are identical to code #1 (`0x571`).
* In-game proof: history filled `[0x29,0x13,0x2B,0x1F,0x1F,0x25]`, checksum reached `0x390` after five presses, then `0x03004180` became `0x04` on the sixth (Observed via savestate diff), and the "Chapter 2 / Edmund and the White Witch" banner appeared (Observed, screenshot `novel3.png`).
* Other unpublished aliases are available for codes 3, 5, 6, 8, 9 by mixing Select/Down at the `S/D` positions (e.g. `Left, A, Left, Select, Select, Down` for code 3).

**Bounds proven by rejection:** `Up, Right(D-pad), Down, Left, Left, Right` — the spelling given by supercheats/cheathappens — produced checksum increments `0x52 → 0xC1 → 0x198 → 0x271 → 0x3C6` (final would be `0x5A7`, absent from the checksum table). `0x03004180` remained `0x00`, history reset, no chapter change (Observed, screenshot `rejected.png`). This bounds both the shoulder-vs-D-pad distinction and the checksum filter.

**Screen walk (RAM-backed):** language select → legal → title → main menu (New Game / Load Game / Multiplayer / Options) → Chapter Select (scene `0x0A`) → gameplay (scene `0x11`) → Pause (scene `0x01`) → item menu (scene `0x08`) → "No Skills." / "No Items." overlays. No password entry field, hidden debug menu, or additional code surface was found on any reachable screen. All 12 validator dispatch branches are accounted for above.

## 7. Validation evidence

* **Observed:** ROM hashes/header; all byte/table dumps; emulator screenshots for title, chapter select, pause, items, skills, Chapter 2 banner; key masks verified by holding each key and reading `0x03004110`; savestate RAM values for history, checksum, acceptance flag and scene word; acceptance and rejection above.
* **Derived:** key→prime mapping, weighted checksum formula, 12-row table decode, caller/scene gating from disassembly (`0x0801B4C8`, `0x08011F4C`, `0x08012190`), dispatch table of 12 effect handlers.
* **Inferred:** effect names for rows 0, 2–11 (from published lists and handler dispatch; only row 1 was visually confirmed). The all-chapters code's flag writes were observed but its visible chapter-unlock effect was not reproduced in-session, so it stays Inferred.

## 8. Unknowns

* Whether code 0 additionally requires a "beat the game once" save flag: its RAM flags were set but the Chapter Select UI did not change in this session.
* Exact visible outcome of rows 2–11 was not individually played out; only row 1 and the novel alias were exercised.
* No debug menu was found; a wiki claim of hidden content was not relied upon.
* The prime token set was recovered empirically for all 10 buttons; its design rationale is unknown.

## 9. Tooling

`strings`, `xxd`, `grep`, `arm-none-eabi-objdump -M force-thumb`, Capstone, Python 3 scripts in `/tmp/opencode/narnia/` (`find_tables.py`, `scan_cmp2.py`, `find_codes.py`, `keymap2.py`, `decode.py`, `verify_code.py`, `state.py`), mGBA 0.10.5 + Xvfb `:318` + openbox, xdotool, scrot, zlib savestate `gbAs` chunk decoder, Ghidra 12.1.4 via REA (`resolve_containing_procedure`, `procedure_pseudo_code`, `procedure_callers`).

No ROM or copyrighted assets are redistributed here; only hashes, addresses and derived algorithms are published.
