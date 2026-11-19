# Pirates of the Caribbean: Dead Man's Chest (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Pirates of the Caribbean: Dead Man's Chest.gba` |
| Size | 16,777,216 bytes (`0x01000000`) |
| Header title | `PIRATESDMC` |
| Game code | `B8QE` |
| Maker code | `4Q` |
| Version | `0x00`; complement byte `0xD0`; header checksum `0x0000` |
| Entry word | `0xEA00002E` (stock `b 0x080000C0`) |
| MD5 | `c13785f8c7f0342d4c96c294e600e338` |
| SHA-1 | `3a11c76edaad8fa0845b7da55e8ed26e26e09883` |
| SHA-256 | `55c61cd0ab12c4c8e1cd4f7888f8f54e0f977816b17b789ef0706b319c495cae` |

**Embedded-header scan:** scanning the entire image for the 156-byte Nintendo logo
found exactly **one** header, at file offset `0x0` (ROM base `0x08000000`). There is
no multiboot half, no appended trainer, and the entry branch is the stock branch,
so this is a clean retail image. Developer splash in-game: Amaze Entertainment;
publisher Buena Vista Games (matches GameFAQs metadata).

**Important revision note:** the worked example in `GBA_REVERSE_ENGINEERING_GUIDE.md`
§12 is a *different* game (Pirates of the Caribbean: The Curse of the Black Pearl).
None of §12's addresses (`0x080098A4`, `0x4A500`, `0x19F82C`, `0x0855D884`, …) apply
here; this report was derived from the B8QE image from scratch.

## 2. Executive summary

The game has a **six-button cheat-code system** reached by pausing in-game and
pressing **Select**, which draws `Enter Cheat Code.` over the pause menu. Codes are
not text passwords: they are six presses whose GBA key masks are converted to small
integer tokens, buffered, and compared against a **10-entry table of six `u32`
tokens each**.

The exact table lives at ROM `0x08070B84` (240 bytes, 10 × 24-byte records) and is
read by the matcher at `0x0801620C`, which dispatches effects through a 10-way jump
table at `0x08016314`. Nine of the ten records correspond to the codes published on
GameFAQs/GameRanks/CheatingDome/SuperCheats/GamersTemple. **The tenth record
(index 8, `0x08070C44`) is not in any published list.** It was entered in mGBA and
produced a distinct, reproducible RAM effect (`0x03004994 |= 0x40`), while all
near-miss and out-of-table inputs were rejected.

A second, *generated* novel spelling is also accepted because the input conversion
aliases **Select and Down to the same token `0x2B`**: `Up, Select, Select, Select,
Select, Up` is accepted with the same effect and appears in no published list.

All in-game surfaces were walked (language select, splash/copyright, title, main
menu, Options with every setting, Credits, gameplay, pause, cheat prompt). No
separate debug/level-select screen exists. UI text is font/tile-indexed (a plain
`strings` scan finds only script/engine labels), so screens were enumerated by
observation plus RAM state rather than by assuming the absence of ASCII text.

## 3. How to reproduce

* Emulator: mGBA under Xvfb (`Xvfb :318 -screen 0 1024x768x24`, `openbox`,
  `SDL_AUDIODRIVER=dummy`, `mgba -3`). Keymap used: A=`x`, B=`z`, L=`a`, R=`s`,
  Start=`Return`, Select=`BackSpace`, D-pad=arrow keys. Verified with a savestate
  taken while holding `a`: `KEYINPUT` at state offset `0x530` reads `0x01FF`
  (= `0x3FF ^ 0x200`), confirming `a` is GBA L.
* Boot path: language `English` → Amaze/Disney splash → title art → `Press Start`
  → main menu. `A` = New Game; hold/skip dialogue with `A`; `Start` = pause;
  `Select` on pause = `Enter Cheat Code.` prompt.
* Savestate workflow: save at the prompt (`Shift+F1`), enter a six-press sequence,
  save to another slot, decompress the `gbAs` PNG chunk and diff. Raw state layout
  for this 16 MiB ROM: IWRAM `0x03000000` at raw offset `0x19000` (32 KiB), EWRAM
  `0x02000000` at raw offset `0x21000` (256 KiB); total state 397,312 bytes.
* Codes tested in emulator (exact press order, ~100 ms hold / ~140–200 ms gap):
  published codes in §6, plus novel `Up, Down, Down, Down, Down, Up` and its
  alias spelling `Up, Select, Select, Select, Select, Up`.
* Rejection tests: `A,A,A,A,A,A`; `Up,Down,Down,Down,Down,Left`;
  `Right,Down,Down,Down,Down,Up`; and a five-press truncation.

## 4. Address map

File offset → ROM address: `+0x08000000`.

| Item | Address | Type | Notes |
|---|---|---|---|
| Cheat token table | `0x08070B84` | ROM data | 10 records × 24 bytes = 240 B; ends `0x08070C74` |
| Record 0 (invincibility) | `0x08070B84` | ROM | `R,L,Up,Up,Left,Right` |
| Record 8 (**unpublished**) | `0x08070C44` | ROM | `Up,Down,Down,Down,Down,Up` |
| Record 9 (restore grog/food) | `0x08070C5C` | ROM | `A,Select,Left,Down,Right,Up` |
| Key→token conversion / buffer writer | `0x08016110` | Thumb fn | called from key routine `0x0802144E` |
| Matcher (6-token compare) | `0x0801620C` | Thumb fn | loop at `0x08016278`; acceptance at `0x080162B2` |
| Effect dispatcher | `0x08016300` | Thumb fn | `cmp r0,#9`, jump table at `0x08016314` |
| Effect jump table | `0x08016314` | ROM data | 10 pointers: `0x08016318 … 0x08016470` |
| Handler 0 (invincible flag) | `0x08016318` | Thumb fn | toggles `0x10` |
| Handler 1 (magic wind flag) | `0x08016340` | Thumb fn | toggles `0x20` |
| Handler 8 (novel) | `0x08016464` | Thumb fn | pushes literal `1000`, calls `0x0801DBAC(0,2,0,0)` |
| Handler 9 | `0x08016470` | Thumb fn | toggles `0x40` |
| Token buffer | `0x03003C60` | IWRAM | 6 × `u32`; cleared on submit |
| Press counter | `0x03003C78` | IWRAM | 0..6; submission when == 6 |
| Counter/clear helper | `0x03003C7C` | IWRAM | reset byte |
| Cheat flag word | `0x03004994` | IWRAM | `1` initially; bits `0x10/0x20/0x40` observed |
| Game mode word | `0x03004F40` | IWRAM | `5` = in-game; matcher gate requires `5` |
| Screen substate | `0x03004F50` | IWRAM | `4` = cheat prompt open, `1` = closed |
| Input globals | `0x03004AC0`, `0x03004F40` | IWRAM | key-state structs |

## 5. Algorithm

Token conversion (observed by entering each button alone and reading
`0x03003C60`, confirmed by the branch immediates in `0x08016110`):

```
A=23  B=29  Select=43  Start=47  Right=37
Left=31  Up=41  Down=43  R=19  L=17
```

`Select` and `Down` are *aliases* (both token `0x2B`); no other collisions.

Entry and match, reimplemented exactly:

```
on new key press k (game mode == 5):
    tok = TOKEN[k]
    buf[count] = tok            # 0x03003C60 + count*4
    count += 1                  # 0x03003C78
    if count != 6: return
    for idx in 0 .. 9:
        if all(buf[j] == table[idx][j] for j in 0..5):
            if mode == 5: dispatch(idx)     # 0x08016300
            break
    clear buf; count = 0
```

The matcher compares full 32-bit words; each table slot stores the token in its
low halfword with the high halfword zero. The table is a flat array, so the whole
accepted space is **exactly the 10 stored six-token strings**, plus the spellings
made equivalent by the `0x2B` alias. There is no checksum, PRNG, or algebraically
generated code space.

## 6. Tables

Published codes, verified literally in the table (ROM addresses are record starts):

| idx | ROM addr | Sequence (press order) | Published effect |
|---:|---|---|---|
| 0 | `0x08070B84` | R, L, Up, Up, Left, Right | Invincibility |
| 1 | `0x08070B9C` | Up, R, Down, Left, Left, Right | Magic Wind |
| 2 | `0x08070BB4` | Select, R, A, L, Left, Right | Restore health |
| 3 | `0x08070BCC` | Left, A, Left, Select, Down, Down | Exit map to island navigation |
| 4 | `0x08070BE4` | A, L, Select, A, Right, Up | Unlock Rumors |
| 5 | `0x08070BFC` | Right, Left, Left, Down, Up, Select | All ship upgrades |
| 6 | `0x08070C14` | Right, L, Down, A, Left, Select | Jack Sparrow fully upgraded |
| 7 | `0x08070C2C` | A, L, Select, R, Right, Right | 1,000 gold |
| 8 | `0x08070C44` | **Up, Down, Down, Down, Down, Up** | **no published effect** |
| 9 | `0x08070C5C` | A, Select, Left, Down, Right, Up | Restore grog/food |

Notes on published sources:
* GameFAQs (archived 2020 snapshot), CheatingDome, GameRanks, SuperCheats,
  GamersTemple all give the same nine codes. CheatingDome duplicates Magic Wind
  with slightly different wording; that duplicate is the same record (idx 1).
* SuperCheats omits the trailing `Select` from two codes; the ROM table includes
  it. GamersTemple/GameFAQs include it. The ROM is authoritative.
* Published lists disagree on whether `Select` is part of "All ship upgrades" and
  "Jack fully upgraded"; both ROM records do contain `0x2B` as the final token.
* No prompt-injection content was found in the fetched pages; they were treated as
  data only.

Observed effect bits at `0x03004994` (baseline `0x0001`):

| Code entered | Flag after |
|---|---|
| Invincibility (idx 0) | `0x0011` (bit `0x10` set) |
| Magic Wind (idx 1) | `0x0021` (bit `0x20` set) |
| Novel (idx 8) | `0x0041` (bit `0x40` set) |
| All other published codes tested | `0x0001` (they act on other state, not this word) |

## 6b. Enumeration

**Space definition.** Alphabet = 10 GBA buttons, but the effective token alphabet
has **9 distinct values** (`{17,19,23,29,31,37,41,43,47}`) because
`Select ≡ Down = 43`. Length is fixed at exactly 6 presses; there is no checksum
or reserved bit. The matcher's loop bound (`cmp r4,#9`) and the table's 10 × 24-byte
extent were both checked, so the accepted set is closed at **10 records**. Counting
alias spellings, the number of accepted press strings is larger: any record
containing token `0x2B` has `2^(number of 0x2B positions)` accepted spellings.

**Novel codes (absent from every published list):**
1. `Up, Down, Down, Down, Down, Up` (table index 8, ROM `0x08070C44`).
2. `Up, Select, Select, Select, Select, Up` — a *generated* alias spelling, not
   stored in the ROM, derived from the `Select/Down` collision.

**In-game proof (Observed, savestate RAM).** Both were entered at the cheat prompt
starting from the same baseline state. `0x03004994` changed from `0x0001` to
`0x0041` on both runs; the press counter at `0x03003C78` returned to `0` and the
buffer was cleared, i.e., the game processed and accepted the six presses. The
novel code's handler at `0x08016464` was identified statically: it pushes the
literal `1000` and calls `0x0801DBAC(0,2,0,0)` before playing sound `0x15`.

**Bounds proven by rejection (Observed):**

| Sequence | Result |
|---|---|
| `A,A,A,A,A,A` (no table record) | `0x03004994` stays `0x0001` — rejected |
| `Up,Down,Down,Down,Down,Left` (one press wrong) | stays `0x0001` — rejected |
| `Right,Down,Down,Down,Down,Up` (one press wrong) | stays `0x0001` — rejected |
| `Up,Down,Down,Down,Down` (5 presses) | counter stays `5`, flag `0x0001` — no submission |
| `Up,Select,Select,Select,Select,Up` (alias) | `0x0041` — accepted (alias bound demonstrated) |

This proves the exact length (6), exact token order, and the single alias pair.

## 7. Validation evidence

* **Observed:** all menu screens visited in mGBA; `Enter Cheat Code.` prompt shown
  after Select; button→token mapping read from IWRAM after each individual press;
  all 9 published codes plus the novel code entered in the emulator; flag word
  `0x03004994` read from decompressed savestates before/after; all rejection tests.
* **Derived:** token table and 10-record count from ROM `0x08070B84` and the matcher
  loop bounds; dispatch targets from the jump table at `0x08016314`; alias collision
  from the two branches writing `0x2B` in `0x08016110` and confirmed dynamically.
* **Inferred:** the exact gameplay label of table index 8. Its handler calls an
  inventory/stat adjuster with amount `1000`, but the full in-game consequence was
  not played through; the persistent flag bit `0x40` is the verified effect.
* **Negative search bounded:** `strings -t x -n 4` over the whole ROM (181,081
  strings) found no password/cheat/debug literal; all menu text is font/tile-indexed.
  Literal searches for the nine published codes as button masks in u8/u16/u32,
  forward and reversed, found no plaintext table until the correct token encoding
  was recovered from RAM. There is no level-select or hidden debug screen on any
  walked path (title, main, Options incl. all settings and Credits, gameplay, pause,
  cheat prompt).

## 8. Unknowns

* The precise gameplay meaning of novel index 8's effect (bit `0x40`); handler
  `0x08016464` calls `0x0801DBAC(0,2,0,0)` with amount 1000, whose exact stat/item
  slot was not exhaustively played out.
* Whether bit `0x40` is also set transiently by any published code between frames;
  only the stable post-submit state was sampled.
* `Load Game` slot contents were not inspected (no save file was used during the
  walk; the game auto-created a 512-byte `.sav`).

## 9. Tooling

* `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings`, `grep`.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`.
* Capstone 5.0.7 PC-relative literal scanner (`lit_scan2.py`) for pointer xrefs.
* mGBA under Xvfb + openbox; `xdotool` XTEST input; `scrot`/ImageMagick for captures.
* mGBA GDB stub (`gdb-multiarch`) — hardware watchpoints worked, software
  breakpoints did not fire in this stub, so watchpoints were used as the oracle.
* Savestate `gbAs` zlib extraction/diff (`zlib.decompress`) for RAM evidence.
* Python helpers in `/tmp/opencode/piratesdmc/`: `gba.py`, `lit_scan2.py`,
  `find_table*.py`, `find_index_table.py`, `watch*.gdb`.

Legal note: no ROM bytes or copyrighted assets are reproduced here; only hashes,
addresses, algorithms, and the author's own findings are published.
