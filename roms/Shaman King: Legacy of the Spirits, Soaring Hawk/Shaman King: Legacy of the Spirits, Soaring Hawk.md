# Shaman King: Legacy of the Spirits, Soaring Hawk (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Shaman King: Legacy of the Spirits, Soaring Hawk.gba` |
| Size | 16,777,216 bytes (0x01000000, 16 MiB) — single retail image |
| Header title | `SK LOS HAWK` |
| Game code / maker | `BHLE` / `A4` (Konami) |
| Version / complement / checksum | 0x00 / 0xCA / 0x0000 |
| Entry word | `0xEA00002E` (stock ARM branch to 0x080000C0 — no cracktro) |
| Nintendo-logo hits | 1 (file `0x00000004`) — not a multiboot/2-in-1 pack |
| MD5 | `42c232aaab6f088e339953d94a91e6bb` |
| SHA-1 | `4d95e192b45a7af79028e5fa850a90310a2d1f28` |
| SHA-256 | `a6f8d6b4abf6650256b03999ba574e1346321f80b746328f825002583c6c29e9` |
| CRC32 (external listing) | `798593A5`, serial `AGB-BHLE-USA` |

No `.sav`/`.ss*` artifacts were left in the ROM folder; all work used a copy in `/tmp/shamanhawk`.

## 2. Executive summary

This GBA title has **no password/code-entry screen**. Its one developer-intended cheat is a **title-screen button sequence**:

> **Right, Right, L, Left+R, Down, R, Right, B**

The sequence grants the **Spirit of Fire** at level 1 (published requirement: no more than 19 spirits already held). The published sequence is stored in ROM as a **newest-first** `u16` button-mask array with a `0xFFFF` terminator, and is matched by a **16-entry ring-buffer suffix matcher**. The game records only *pressed* keys (edge-triggered) into a circular buffer in EWRAM; the validator walks backwards through that buffer and forwards through the ROM array.

**Acceptance was confirmed by RAM evidence**: after entering the sequence on the title screen, the match byte at `0x0201F8F1` reads `2` (matched); after entering an undocumented one-button-substitution variant it reads `1` (rejected). The exact mask sequence is visible in the ring buffer at `0x0201F8D0`.

The whole code space is **exactly one accepted sequence**: the table pointer at `0x08DA3EA8` has only one valid sequence pointer (index 0), and the sole caller of the checker tests only index 0. A ROM-wide scan for all referenced `0xFFFF`-terminated `u16` runs found nine candidates, of which only `0x08DA3E94` is a button-mask table (the other eight are incidental data in text/compression banks).

Downstream of the match, the code follows a static path that grants spirit id 24 through `0x08010224`, subject to a "first free slot among 20" check at `0x0800D71C` and a one-shot flag at `0x0201F8C0`. **That grant was derived but not observed**: in all savestates captured after an accepted sequence, the EWRAM spirit table at `0x0201DE50` remained empty and the one-shot flag word remained 0 (this is recorded as an open item in §8, not as a confirmed effect).

Published CodeBreaker/GameShark codes exist for this game; they are cheat-device codes and are **out of scope** for this report.

## 3. How to reproduce

**Emulator**: mGBA 0.10.5 under Xvfb `:316`, `SDL_AUDIODRIVER=dummy`, `-3` scaling.
Work on a **copy** of the ROM so the ROM folder stays clean.

1. Boot to the title screen (`SKAMAN KING / LEGACY OF THE SPIRITS / SOARING HAWK`, `NEW GAME`). Saving a state here makes retries cheap.
2. Default mGBA SDL keymap: A = `x`, B = `z`, L = `a`, R = `s`, Start = `Return`, Select = `BackSpace`, D-pad = arrow keys.
3. Enter, with a ~170 ms hold and ~230 ms gap between presses:

   | # | Button | xdotool keys | Recorded mask |
   |---:|---|---|---|
   | 1 | Right | `Right` | `0x0010` |
   | 2 | Right | `Right` | `0x0010` |
   | 3 | L | `a` | `0x0200` |
   | 4 | Left+R | `keydown Left s` / `keyup Left s` in one XTEST batch | `0x0120` |
   | 5 | Down | `Down` | `0x0080` |
   | 6 | R | `s` | `0x0100` |
   | 7 | Right | `Right` | `0x0010` |
   | 8 | B | `z` | `0x0002` |

   The simultaneous Left+R **must** be sent as one atomic `xdotool keydown Left s` call; two separate `keydown` process launches are occasionally split across frames into `0x0020` + `0x0100` and then fail (this variant was used as the rejection test).
4. Save a state and decompress its `gbAs` PNG chunk (`zlib.decompress`). EWRAM begins at raw-state offset `0x21000`:
   - ring buffer `0x0201F8D0` — 16 `u16` masks, oldest first
   - write index `0x0201F8F0` — should be `8`
   - match byte `0x0201F8F1` — `2` = accepted, `1` = rejected
5. Press Start to begin a game if following the published in-game instruction.

**Published-code recon** (treated as data, never instructions): 3rd party cheat index cheat page, 3rd party cheat index FAQ 35598, and Tipland all give the same eight presses; Tipland abbreviates the doubled Right as `Right(2)`. 3rd party cheat indexes and libretro-database list only CodeBreaker codes for this SKU.

## 4. Address map

### ROM (file offset = ROM address − `0x08000000`)

| Address | What |
|---|---|
| `0x08000000` | Header; stock entry branch `0xEA00002E` |
| `0x0801B120` | `check_code(state, index)` — 16-slot ring-buffer suffix matcher (Thumb) |
| `0x0801B1E4` | `check_all_codes()` — sets `state[0x21]`; only index 0 tested |
| `0x0801B238` | reset ring buffer (16×`u16` zero, index/match bytes zero) |
| `0x0801B260` | `record_press(state, mask)` — writes `u16` at `state[2*idx]`, advances signed-byte index mod 16 |
| `0x0801B290` | `get_key_press()` — returns current edge mask from shadow input words |
| `0x0801B2E0` / `0x0801B2D4` / `0x0801B300` | set flag bit / clear all flags / test flag bit (flag word `0x0201F8C0`) |
| `0x08010760` | Title-screen input handler; calls `get_key_press`, `record_press`, `check_all_codes` |
| `0x0801077A`–`0x08010802` | Match branch; scene dispatch; free-slot check; spirit grant; message |
| `0x0800D71C` | Spirit-slot finder: first slot of 20 whose first `u16` is `0xFFFF`, else `0xFF` |
| `0x08010224` | Spirit grant: `(slot, spirit_id, level)`; writes template-derived record |
| `0x0859B4` | Spirit name `Spirit of Fire` (NUL-terminated name bank; pointer at `0x0DA1458`) |
| `0x08DA3E94` | Button sequence, newest-first `u16[8]` + `0xFFFF` terminator at `0x08DA3EA4` |
| `0x08DA3EA8` | Code pointer table `u32[]`; entry[0] = `0x08DA3E94`; entry[1+] are not sequence pointers |

### EWRAM (observed in mGBA / savestate)

| Address | Size | Meaning |
|---|---|---|
| `0x0201F8D0` | 16 × `u16` | Press-history ring, oldest first |
| `0x0201F8F0` | `u8` | Write index (next free ring slot) |
| `0x0201F8F1` | `u8` | Match result: 0 = unchecked, 1 = no match, 2 = matched |
| `0x0201F8C0` | `u32` | One-shot flag word (tested with bit 0) |
| `0x0201DE50` | 20 × 68 bytes | Spirit/party records; first `u16` = `0xFFFF` when empty |
| `0x0201DC10` | 68 bytes | Spirit template used by `0x08010224` |
| `0x0201F640` / `0x0201F644` | `u32` / `u8` | Scene-dispatch state |

Button masks (active-high, `~KEYINPUT & 0x3FF`): A `0x001`, B `0x002`, Select `0x004`, Start `0x008`, Right `0x010`, Left `0x020`, Up `0x040`, Down `0x080`, R `0x100`, L `0x200`. Combined presses are ORed (Left+R = `0x120`).

## 5. Algorithm / pseudocode

```c
// ROM data, all u16 little-endian, NEWEST FIRST
const u16 code0[9] = {0x0002,0x0010,0x0100,0x0080,
                      0x0120,0x0200,0x0010,0x0010,0xFFFF}; // @0x08DA3E94
const u32 code_ptrs[1] = {0x08DA3E94};                     // @0x08DA3EA8

int check_code(struct State *s, int index) {
    const u16 *seq = (const u16*)code_ptrs[index];   // LDR from 0x08DA3EA8 + 4*index
    int back = (s8)(s->write_index - 1);
    if (back < 0) back = 15;                         // 16-entry ring
    for (int i = 0; i < 16; i++) {
        if (seq[i] == 0xFFFF) return 1;              // whole sequence matched
        if (seq[i] != s->ring[back]) return 0;       // mismatch -> reject
        i_advance: ;                                  // i++ in loop
        back--; if (back < 0) back = 15;
    }
    return 0;
}

void check_all_codes(struct State *s) {
    s->match = 0;
    // The compiled loop only ever calls check_code(s, 0):
    // on no-match it sets match = 1 and exits; on match at index 0 it sets match = 2.
    s->match = check_code(s, 0) ? 2 : 1;
}

// Title-screen handler, every frame with a fresh key press:
if (mask = get_key_press()) {
    record_press(s, mask);        // s->ring[s->write_index++] = mask (mod 16)
    check_all_codes(s);
    if (s->match == 2) {
        ... scene dispatch (writes 0x0201F644) ...
        if (!test_flag(0)) {
            int slot = find_first_free_spirit_slot(); // 0..19, or 0xFF
            if ((u8)slot <= 19)
                grant_spirit(slot, 24, 1);           // Spirit of Fire, level 1
            set_flag(0);
            show_message(366);
        }
        reset_ring(s);
    }
}
```

Validator notes (all **Derived** from disassembly at `0x0801B120`/`0x0801B1E4`):
* The ROM sequence is stored newest-first; the EWRAM ring is stored oldest-first, hence the validator increments `i` while decrementing `back`.
* The terminator is checked *before* each comparison, so an exact 8-press suffix matches; any extra trailing press makes the suffix differ and rejects.
* `get_key_press()` masks with `0x3FF` and `0xFFF6`, so A and Start are excluded from the cheat history; all other buttons/combinations are accepted.
* `check_all_codes` writes `1` on no match and `2` on match; there is no other result value.

## 6. Tables

### 6.1 The single code table

| Stored order (index) | Chronological press | `u16` mask | ROM address |
|---:|---|---|---|
| 0 (newest) | B (last) | `0x0002` | `0x08DA3E94` |
| 1 | Right | `0x0010` | `0x08DA3E96` |
| 2 | R | `0x0100` | `0x08DA3E98` |
| 3 | Down | `0x0080` | `0x08DA3E9A` |
| 4 | Left+R | `0x0120` | `0x08DA3E9C` |
| 5 | L | `0x0200` | `0x08DA3E9E` |
| 6 | Right | `0x0010` | `0x08DA3EA0` |
| 7 (oldest) | Right (first) | `0x0010` | `0x08DA3EA2` |
| terminator | — | `0xFFFF` | `0x08DA3EA4` |

Pointer to the table: `0x08DA3EA8` → `0x08DA3E94` (found by literal-pointer scan; the reversed byte pattern `02 00 10 00 00 01 80 00 20 01 00 02 10 00 10 00` occurs exactly once in 16 MiB).

### 6.2 Match byte semantics

| `0x0201F8F1` | Meaning |
|---:|---|
| 0 | no check performed yet this session |
| 1 | check performed, sequence did not match |
| 2 | check performed, sequence matched |

### 6.3 Effect gates (derived, not observed)

| Condition | Address / code | Value for grant |
|---|---|---|
| match | `state[0x21]` (`0x0201F8F1`) | `2` |
| one-shot flag | `test_flag(0)` on `0x0201F8C0` | bit 0 clear |
| spirit slots | `0x0800D71C` over `0x0201DE50`, 20 × 68 bytes | first free slot ≤ 19 |
| grant | `0x08010224(slot, 24, 1)` | spirit id 24, level 1 |
| feedback | message 366 via `0x08033364` | — |

## 6b. Enumeration

**Space definition.** The cheat surface is a button-match system, not a checksum code system:
* alphabet: 10 single buttons plus OR-combinations (`0x001`–`0x3FF` subject to the `0xFFF6` mask, i.e. A and Start ignored);
* sequence length: **exactly 8 presses**, followed by the `0xFFFF` sentinel;
* history capacity: **16 presses** (ring buffer at `0x0201F8D0`);
* table size: **1 entry** (`u32` pointer at `0x08DA3EA8`); representable accepted sequences = **1**.

**Completeness argument (bounded).**
1. `check_all_codes` at `0x0801B1E4` is reached by exactly one `BL` call site (`0x08010776`); there are zero 32-bit pointer references to either `0x0801B120` or `0x0801B1E4` (including Thumb-bit variants), so it cannot be dispatched through a table from elsewhere.
2. The compiled `check_all_codes` only calls `check_code(state, 0)`; on no-match it sets the result byte to 1 and returns. Even though the literal pool holds a multi-entry pointer table, no other index is ever tested by retail code.
3. `code_ptrs[1]` onward in `0x08DA3EA8` are `0x00000000`, `0x00000001`, `0x00000003`, `0x0801C059`, … — none points to an `0xFFFF`-terminated mask array.
4. A whole-ROM scan of every aligned `u32` that points into the image, testing whether its target is a run of 2–16 values in `0x001`–`0x3FF` terminated by `0xFFFF`, returned **9** candidates. Eight are incidental data in compressed/text banks (`0x08DC5376`, `0x0884FE8D`, `0x087220ED`, `0x0886BD19`, `0x08770874`, `0x080D670A` ×2, `0x08087012`); only `0x08DA3E94` is a real button table, and it is the one referenced by the validator's literal pool.
5. Therefore **exactly one 8-press sequence is accepted**, and no second, shorter, or undocumented action branch exists in this build.

**Undocumented combination pressed in the emulator (the button-code equivalent of a novel code).** Because the accepted set has cardinality 1, no *accepted* novel sequence can exist; the required novelty test is an undocumented combination that reaches the same decoder and is rejected. I entered:

> Right, Right, L, **Left** (R omitted), Down, R, Right, B

using separate `xdotool keydown` calls for the third and fourth presses, which the game split into two edges. Savestate RAM (`game.ss4`) showed:
* ring buffer = `0x0010, 0x0010, 0x0200, 0x0020, 0x0100, 0x0080, 0x0100, 0x0010, 0x0002`, write index `9`;
* match byte = **`1`** (rejected).

A second variant with the L and Left+R presses swapped (recorded `0x0200` then `0x0020`/`0x0100`) also produced match = `1`. These are the required rejection bounds: any substitution, omission, or splitting of the combined press fails. Evidence files: `code_immediate.png`, `game.ss2`, `game.ss3`, `game.ss4`, `game.ss5` in `/tmp/shamanhawk`.

**Accepted-sequence proof (game.ss5 / game.ss2).** Ring exactly `0x0010,0x0010,0x0200,0x0120,0x0080,0x0100,0x0010,0x0002`, write index `8`, match byte **`2`**. This is the developer-intended sequence entered through the real on-screen input path.

## 7. Validation evidence

| Claim | Type | Evidence |
|---|---|---|
| ROM identity / hashes | **Observed** | `file`, `md5sum`/`sha1sum`/`sha256sum`, header parse, single logo hit |
| Published sequence matches ROM table | **Observed** | literal byte-pattern search found exactly one hit at file `0xDA3E94`; reverse order stored newest-first |
| Validator is a ring-buffer matcher | **Derived** | `0x0801B120`/`0x0801B1E4` disassembly: ring index arithmetic mod 16, `0xFFFF` terminator compare, `state[0x21]` writes 1/2 |
| On-screen entry is accepted | **Observed** | savestate diff: ring holds exact 8 masks, match byte = 2 (`game.ss2`, `game.ss5`) |
| Undocumented combination is rejected | **Observed** | savestate diff: match byte = 1 with one mask substituted (`game.ss3`, `game.ss4`) |
| Only one code exists | **Derived** | single BL caller, single valid pointer-table entry, ROM-wide referenced-sequence scan = 9 candidates with only one plausible table |
| Effect path grants spirit 24 / level 1 and gates on ≤19 spirits | **Derived** | `0x080107DA`–`0x080107FC`, `0x0800D71C`, `0x08010224`, `0x08033364`; name `Spirit of Fire` at `0x0859B4` |
| Spirit table actually changes after the code | **Not observed** | see §8 |

## 8. Unknowns

* **Effect not observed in RAM.** In every accepted-sequence savestate (`game.ss2`, `game.ss5`) the 20 spirit slots at `0x0201DE50` remained `0xFFFF` and the flag word at `0x0201F8C0` remained `0x00000000`. Diagnostic ROM patches that forced the match branch, bypassed the scene dispatchers, and wrote marker bytes at the set-flag call site also failed to change EWRAM. This means the downstream grant has **not** been reproduced here even though the match byte proves the validator accepted the input. Possible explanations (untested): the effect is gated by a second scene-state condition not identified in `0x0801078C`–`0x080107AC`, or the grant is applied to save memory only when a New Game is confirmed. The published instruction ("press Start and visit your spirit list") was attempted, but the in-game spirit-list menu could not be reached because the starting area repeatedly enters an NPC dialogue; that screen walk remains incomplete.
* The exact in-game wording of message 366 was not decoded from the text bank.
* Whether the code remains usable a second time after the one-shot flag is set (the code path sets flag 0 at `0x080107F0`, but the observed flag never became set).

## 9. Tooling

* `md5sum`, `sha1sum`, `sha256sum`, `file`, `strings`, `grep -abo` — Phase 0/1.
* Python 3 scripts (in `/tmp/shamanhawk`): header parse, Nintendo-logo scan, byte-pattern search, `u16`/`u32` literal-pool dumps, BL scanner, referenced-sequence scan, savestate `gbAs` zlib decompression and EWRAM diff.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` — all disassembly.
* mGBA 0.10.5 (`-3`), Xvfb `:316`, openbox, xdotool (XTEST), scrot — dynamic validation.
* GDB stub (`mgba -g`, `gdb-multiarch`) was tried but proved unreliable on this build (stale stub, `Ignoring packet error`, target hanging); all RAM reads therefore used savestate decompression (guide §16.13).
* Diagnostic patched copies (`game_patch.gba`) were confined to the work directory and are not shipped.

No ROM or copyrighted assets are redistributed; only addresses, hashes, algorithms, and our own observations are published.
