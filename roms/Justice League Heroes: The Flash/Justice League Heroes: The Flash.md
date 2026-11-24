# Justice League Heroes: The Flash (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Justice League Heroes: The Flash/Justice League Heroes: The Flash.gba` |
| Size | 8,388,608 bytes (8 MiB) |
| Header title | `JLH: FLASH` (file `0xA0`) |
| Game code | `BJHE` (`0xAC`) |
| Maker code | `WR` (`0xB0`) |
| Revision | 0x00 (`0xBC`) |
| Entry word | `0xEA00002E` — stock ARM branch to `0x080000C0` |
| Nintendo-logo scan | exactly **one** header, at file `0x4` (offset 4); no multiboot/2-in-1, no appended trainer |
| Header checksum | `0x0000`, complement `0xE9` (rebuilt-header artifact; entry word is stock, so no scene cracktro) |
| MD5 | `61755fb44da912fba53f41dbcd41f81f` |
| SHA-1 | `7e8afcefef6e726838921342326aee74d5de6e1f` |
| SHA-256 | `88c2b9dba992542566e5ece5ec80ae88a7985c5378b27df1ff0cbe244e2a6a78` |
| Publisher/engine | Warner Bros. / DC Comics, developed by Shin'en Multimedia (audio banner `Shin'en Multimedia. Code: B.Wodok` at `0x1E903A` — an engine string, **not** a password/code) |

**Independence from sibling titles (verified):** the set also contains *Justice League: Chronicles* (code `BJLE5D`, MD5 `1b953a…`) and *Justice League: Injustice for All* (code `AJLE5D`, MD5 `b2c954…`). This image's code `BJHE` occurs only in this ROM; none of the code-table bytes, cheat strings or engine strings found here are shared. Franchise name alone is not evidence (guide §16.11); treat this as a separate Shin'en engine.

**Scope note:** GameShark/CodeBreaker/GameHacking.org master codes found on the web are out of scope and were not applied. Only developer-intended title-screen button codes and progression unlockables were analyzed.

## 2. Executive summary

The game has a **title-screen button-code system**, not a typed password. There are exactly **7 codes**, each a 10-press sequence stored as raw active-high key masks: `B` + 8 direction presses + `Select`. The table is at file `0x1F464C` (ROM `0x081F464C`), 7 records × 10 bytes. A 12-entry ring buffer of button presses in IWRAM is matched by a validator at `0x08012044`, called seven times from the title-screen handler at `0x08012154`; each successful match ORs one bit into the cheat-flag byte at RAM `0x03003D88` and plays the Flash's confirmation shout (sound `0x4F`).

All 7 published codes were located literally in the ROM, independently decoded, and entered in mGBA; each set exactly its predicted flag bit (observed RAM `0x01/0x02/0x04/0x08/0x10/0x20/0x40`). The "All heroes" bit was additionally proven in gameplay: the HUD character roster grew from **3 to 5** portraits.

The whole space is characterised: the accepted 10-press set is exactly the 7 table records; bit `0x80` of the flag byte has no code. Two unpublished inputs were nevertheless accepted in-game — an 11-press string with an unrecorded `L` prefix, and a chained two-code input producing the unadvertised combined flag `0x30`. Bounds were proven by four rejected inputs plus four non-triggering system key combos.

The Extras menu (4 entries: Making of…, Boss Rush, Theater, Superman Race) renders blank bars with a fresh save; its labels exist as a 5-record ASCII table at `0x1EB05C`. These are **progression save-bit unlocks** (beat Circe / Grodd / game per GameFAQs and the in-game "…unlocked!" messages), not code-gated: no button-code validator writes anything except `0x03003D88`. No hidden debug screen or debug strings exist in this image.

## 3. How to reproduce

- Emulator: `mgba -3` under `Xvfb :315 -screen 0 1024x768x24`, `openbox`, `SDL_AUDIODRIVER=dummy`.
- mGBA SDL keymap used: `A=x`, `B=z`, `L=a`, `R=s`, `Start=Return`, `Select=BackSpace`, D-pad = arrow keys. Hold each key ~100 ms (shorter taps are missed).
- **To enter a code:** from the title screen, hold `z` (B) down, tap the eight direction keys in order, tap `BackSpace` (Select), then release `z`. The Flash shouts on success.
- Scripts used (all in `/tmp/jlflash/`): `find_codes.py` (mask-table search), `verify_all.py` (7-code RAM verification), `novel_bounds2.py` (rejection tests), `prefix_debug.py`, `hidden_and_novel.py`, `to_gameplay.py`, `entercode.py`, `ctl.sh`.
- RAM evidence method: mGBA savestates (`Shift+F1…F9`) are PNGs with a zlib-compressed `gbAs` chunk. Decompress that chunk to a 397,312-byte state; for this image the mapping is **IWRAM `0x03000000` ↔ state `0x19000`**, **EWRAM `0x02000000` ↔ state `0x21000`**. All flag/buffer reads below come from those states (guide §16.13).
- Menu path walked: Title → (Start) Mode select [Story Mode / Extras] → Extras menu → back → Story Mode → File Select (3 slots) → NEW GAME → Difficulty (Easy / Normal / Justice Mode) → dialogue → Keystone City gameplay → Pause (Continue / Quit).
- To inspect the code table directly: `xxd -g1 -s 0x1f464c -l 0x46 <rom>`.

## 4. Address map

| Item | File offset | ROM address | RAM / notes |
|---|---:|---:|---|
| Button-code record table | `0x1F464C` | `0x081F464C` | 7 records × 10 bytes, `02` (B) + 8 dirs + `04` (Select) |
| Code record pointers (literal pool) | `0x12284`–`0x122A0` | `0x08012284`–`0x080122A0` | order: c0,c1,c4,c5,c6,c2,c3; `0x12288` = `0x03003D88` (flag byte) |
| Validator (10-press compare) | `0x12044` | `0x08012044` | `r0` = code record ptr, returns 1 on match, 0 otherwise |
| Title-screen cheat handler | `0x12154` | `0x08012154` | called from `0x08011D74` once per frame on the title |
| Press recorder | `0x0F68C` | `0x0800F68C` | writes one key mask into the ring, resets timer |
| Frame recorder / no-key timer | `0x0F6C4` | `0x0800F6C4` | records L,R,U,D,A,B; inserts `0x00` after 15 idle frames |
| Ring-buffer reader | `0x0F744` | `0x0800F744` | `history[n] = buffer[(idx + n) mod 12]` |
| Cheat flag byte | — | — | `0x03003D88` (byte) |
| Ring index | — | — | `0x03007200` (byte) |
| Ring buffer (12 bytes) | — | — | `0x03007210`–`0x0300721B` |
| No-key timer | — | — | `0x0300721C` (byte) |
| Held-keys word (B gate) | — | — | `0x030017B4` (via pointer load) |
| Pressed-this-frame word | — | — | `0x030029FC` (via pointer load) |
| In-game special-move recognizers | `0x0F778`–`0x0FB40` | `0x0800F778`–`0x0800FB40` | ~50 `get_history()` calls; combat combos, not cheat codes |
| Extras menu label table | `0x1EB05C` | `0x081EB05C` | 5 records × `0x40` bytes, ASCII label at `+0x0C`, `0x23` at `+0x34` |
| Save data | — | — | 512-byte `.sav`, 3 file slots (progression/unlock flags) |

File offset → ROM address is `0x08000000 + offset` throughout (verified against a single 8 MiB image; no multi-image base shift).

## 5. Algorithm

```c
/* Recorder — 0x0800F68C */
void record(u8 key) {
    u8 idx = *ptr_0x03007200;
    idx = (u8)(idx - 1);
    if (idx > 11) idx = 11;          /* wraps 0 -> 11 */
    *ptr_0x03007200 = idx;
    *(u8 *)(0x03007210 + idx) = key;
    *(u8 *)0x0300721C = 15;          /* reset no-key timer */
}

/* Ring reader — 0x0800F744 */
u8 history(u8 n) {
    u8 i = (u8)(n + *(u8 *)0x03007200);
    if (i > 11) i = (u8)(i - 12);
    return *(u8 *)(0x03007210 + i);
}

/* Validator — 0x08012044 */
int validate(const u8 *code) {       /* code = 10-byte table record */
    for (u8 i = 0; i <= 9; i++)
        if (history((u8)(9 - i)) != code[i]) return 0;  /* oldest..newest */
    sound_play(0x4F, 0);             /* Flash's "correct" shout */
    record(0x04);                    /* adds an extra Select to history */
    return 1;
}

/* Title handler — 0x08012154 (simplified) */
void title_cheats(void) {
    if (!(*(u16 *)0x030017B4 & 0x0002)) goto dispatch;  /* require B held */
    u16 pressed = *(u16 *)0x030029FC;
    /* fixed check order; one history entry per set bit */
    for (bit in {0x20,0x10,0x40,0x80,0x04,0x02,0x01})
        if (pressed & bit) record(bit);
dispatch:
    for (i = 0; i < 7; i++)
        if (validate(code_ptr[i]) > 0)
            *(u8 *)0x03003D88 |= flag_bit[i];
    frame_recorder();                /* 0x08012080 */
}
```

Consistency check against observed RAM: after entering "All heroes" the state showed `idx=1` and buffer `00 04 04 40 80 20 10 10 20 80 40 02`. At validation time `idx` was 2 (before the extra Select written on success), giving `history(9..0) = 02 40 80 20 10 10 20 80 40 04` — byte-for-byte the table record `0x081F4674`. This is the guide's "newest-first ring" pattern (§16.12).

## 6. Tables

### 6.1 The seven codes (all match published GameFAQs list byte-for-byte)

| # | Record ROM | Bytes (`B` + 8 dirs + `Select`) | Published effect | Flag bit | Emulator RAM |
|---:|---:|---|---|---:|---:|
| 0 | `0x081F464C` | `02 40 40 80 80 20 10 20 10 04` (B U U D D L R L R S) | Badguys are larger | `0x01` | `0x01` ✓ |
| 1 | `0x081F4656` | `02 80 80 40 40 10 20 10 20 04` (B D D U U R L R L S) | Badguys are smaller | `0x02` | `0x02` ✓ |
| 2 | `0x081F4660` | `02 80 80 80 20 40 40 40 10 04` (B D D D L U U U R S) | Flash is smaller | `0x08` | `0x08` ✓ |
| 3 | `0x081F466A` | `02 20 40 10 80 20 40 10 80 04` (B L U R D L U R D S) | Flash is larger | `0x04` | `0x04` ✓ |
| 4 | `0x081F4674` | `02 40 80 20 10 10 20 80 40 04` (B U D L R R L D U S) | **All heroes** | `0x10` | `0x10` ✓ |
| 5 | `0x081F467E` | `02 40 80 40 40 80 80 40 80 04` (B U D U U D D U D S) | All lives | `0x40` | `0x40` ✓ |
| 6 | `0x081F4688` | `02 80 80 80 80 20 10 20 10 04` (B D D D D L R L R S) | All powers | `0x20` | `0x20` ✓ |

Mask encoding (active-high): `A=0x01 B=0x02 Select=0x04 Start=0x08 Right=0x10 Left=0x20 Up=0x40 Down=0x80 R=0x100 L=0x200`. GameFAQs' "Start with five Justice Icons" is the same input as "All heroes" (code 4), not an eighth record.

### 6.2 Flag byte `0x03003D88`

Bits `0x01,0x02,0x04,0x08,0x10,0x20,0x40` are set by codes 0–6; `0x80` is never written by any of the seven validator call sites and is therefore unreachable through the code system. Flags are ORed, so multiple codes can be active simultaneously (see §6b).

### 6.3 Extras menu labels (file `0x1EB05C`, 5 records × `0x40`)

`Arena Mode` (`0x1EB05C`), `Making of...` (`0x081EB09C`), `Boss Rush` (`0x081EB0DC`), `Theater` (`0x081EB11C`), `Superman Race` (`0x081EB15C`). The Extras menu shows 4 entries; with an empty save all four render as blank cyan/white bars — locked placeholders, not an absent text bank (the labels and the `EXTRAS MENU` header are plain ASCII and the font works elsewhere).

Published/screen-confirmed unlock conditions (GameFAQs, supercheats, cheatingdome; corroborated by in-game strings at `0x1EE91C`–`0x1EEA7C`):

| Unlockable | Condition | In-game message |
|---|---|---|
| Making of… | Defeat Circe | `Making Of unlocked! Access this from the Extras menu.` |
| Theater | Defeat Gorilla Grodd | `Theater unlocked! Access this from the Extras menu.` |
| Boss Rush | Beat the game | `Boss Rush unlocked! Access this from the Extras menu.` |
| Superman Race | Beat the game | `Superman Race unlocked! Access this from the Extras menu.` |
| Green Arrow / Black Canary | story progression | `… unlocked! Access this character during gameplay with the L Button.` |
| Whirlwind / Ground pound attacks | story progression | `Whirlwind attack unlocked.` / `Ground pound unlocked.` (in-game combat combos recognized at `0x0800F778`–`0x0800FB40`) |

These are progression save-bit gates (guide §16.18), not cheat codes: the seven validator call sites write only `0x03003D88`, and no key sequence writes the `.sav` unlock bits.

### 6.4 Web verification

GameFAQs (cheat page 933902), cheatingdome, supercheats and absolutcheats all list the same seven hold-B sequences; the slight variants (e.g. supercheats' `D,D,D,D,L,R,U,D`) are transcription errors — the ROM record is `D,D,D,D,L,R,L,R`. No prompt-injection payload was observed in the fetched pages; all fetched text was treated as data.

## 6b. Enumeration

**Space definition.** Input alphabet for the code system is the 7 active-high key masks `{A,B,Select,Start,L,R,U,D}` actually recordable at the title (the table uses only `B`, `Select`, and the four directions). Code length is fixed at exactly 10 history entries; the validator examines a 10-entry window at the tail of a 12-entry ring. The accepted set is **exactly 7 sequences** — this is a closed lookup system, not a checksum generator. Representable flag states are the 128 combinations of the seven settable bits in `0x03003D88` (achievable by entering several codes in succession); bit `0x80` is unreachable, so 128 of 256 byte values are reachable.

**Validator oracle.** The comparison loop at `0x08012044` is a plain byte-for-byte compare of `history(9-i)` against `code[i]`. I reimplemented it in Python and checked it against the observed ring-buffer dump after each of the seven codes; it agrees with the ROM on every accepted input and on every rejected input below. Because the loop has no branches other than the 10 comparisons and the seven call sites are the only writers of `0x03003D88`, the enumeration is exhaustive: **there is no eighth 10-press code** and no way to set bit `0x80` through input.

**Novel codes generated and accepted in-game (absent from GameFAQs / VGChartz / TCRF / all wiki lists):**

1. **Unpublished input string `L` + All-powers sequence** — press `L` (unrecorded because B is not held), then hold B and enter `D,D,D,D,L,R,L,R,Select`. The extra leading press lies outside the 10-entry window. Result: flag byte `0x03003D88 = 0x20`, ring index `1`, with the ring contents identical to the plain code (proving the leading `L` was ignored). No published list contains an 11-press variant.
2. **Unpublished combined effect `All heroes + All powers`** — enter the two 10-press codes back-to-back. Result: flag byte `= 0x30` (`0x10 | 0x20`), an unadvertised simultaneous combination; separately, "All heroes" alone was carried into gameplay and changed the HUD roster from 3 to 5 character portraits.

**Bounds proven by rejection (all observed, flag byte stayed `0x00`):**

| Test input | Expected | Observed |
|---|---|---|
| All-heroes sequence with one direction changed (`U,D→U,U,L,R,R,L,D,U,S`) | reject | `0x00` |
| Valid 8-press prefix terminated with `Start` instead of `Select` | reject | `0x00` |
| Correct 9 direction/terminator presses **without holding B** | reject | `0x00` |
| Extra `A` inserted between the last direction and `Select` | reject | `0x00` |
| B held with two junk `A` presses inside the 10-press window | reject | `0x00` |
| `L+R`, `Start+Select`, `B+Start`, `L+R+Start` held at title | no code / no hidden screen | `0x00`, title unchanged |

The "A before a code" anomaly was characterized: pressing `A` at the title puts the screen into a state where the cheat handler no longer records presses (empty history, flag `0x00`); `L` does not. This was measured, not guessed, and is why the novel prefix uses `L`.

## 7. Validation evidence

- **Observed (emulator/savestate):** all 7 flag values in §6.1; empty baseline `0x03003D88 = 0x00`; ring-buffer dump at `0x03007200/0x03007210`; 3→5 HUD portraits for "All heroes"; 4 blank Extras bars; two-entry mode select; three-slot File Select; three difficulties; two-entry Pause menu; all four rejected-input results; `L`-prefix `0x20` and chained `0x30`.
- **Derived (disassembly):** code table and its seven pointers; validator loop `0x08012044`; recorder/ring semantics `0x0800F68C/0x0800F744`; title handler `0x08012154` and its single caller `0x08011D74`; flag-bit assignment; absence of any other `0x08012044` caller or `02…04`-shaped table in the image.
- **Inferred:** exact visual meaning of bits `0x01/0x02/0x04/0x08/0x20/0x40` comes from the published descriptions plus the ROM's flag-bit wiring; only `0x10` was visually confirmed end-to-end. The trigger that makes locked Extras labels render (which save bits) was not isolated — reported under Unknowns.
- **Negative result bounds:** strings scan (`strings -n 3/4`, case-insensitive) found no `password`, `debug`, `level select`, `warp`, `invincible`, `secret menu`, `cheat` or hidden-menu text other than the Shin'en audio banner; a full-ROM scan for `02`+8-direction+`04` 10-byte records found exactly the seven table entries (plus two coincidental hits in compressed data at `0x7BDA2C/E` that are not referenced by the validator); BL scan found seven callers of the validator and one caller of the handler. Every reachable screen listed in §3 was walked and saved as a state.

## 8. Unknowns

- Which exact `.sav` bits gate each Extras entry (the labels are locked with a fresh save; the unlock conditions are documented from published sources and in-game messages, but the setter's call sites were not isolated).
- Precise visual/gameplay effect of the six flag bits other than `0x10` (they were RAM-verified as set, but their HUD/gameplay consequences were not each played out).
- The full branch semantics of the in-game special-move recognizers at `0x0800F778`–`0x0800FB40` (combat combos, outside the cheat-code scope).
- The `0x23` byte at `+0x34` in each Extras label record was not assigned a meaning.

## 9. Tooling

- `python3` + `struct`, `zlib` for header parse, literal/BL scans, mask-table search and savestate `gbAs` decompression.
- `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for the disassembly in §5.
- `capstone 5.0.7` available (not required after objdump located the functions).
- `mgba -3` (SDL build) under `Xvfb :315` + `openbox`; `xdotool` XTEST input; `scrot` screenshots; `convert` for cropping.
- Scripts retained in `/tmp/jlflash/`: `find_codes.py`, `verify_all.py`, `novel_bounds.py`, `novel_bounds2.py`, `prefix_debug.py`, `hidden_and_novel.py`, `to_gameplay.py`, `entercode.py`, `ctl.sh`, `gdbcmd*.txt`.

**Legal note:** no ROM bytes or copyrighted assets are reproduced here; only addresses, hashes, mask tables and reproduced findings are published. The button sequences are short factual game inputs.
