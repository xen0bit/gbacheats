# Disney's Cinderella: Magical Dreams (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Disney's Cinderella: Magical Dreams.gba` |
| Size | 8,388,608 bytes (8 MiB) |
| Header title | `CINDBCDE` (0x00 padded) |
| Game code | `BCDE` |
| Maker code | `4Q` |
| Software version | 0 |
| Complement check (0xBD) | `0x92` (matches computed value) |
| Header checksum (0xBE) | `0x0000` |
| Entry word (0x00) | `0xEA00007E` → `0x08000200` |
| ARM branch at 0x080000C0 | `b 0x08000200` |
| MD5 | `e0dceb3ee3be70e72b425fdf455c7237` |
| SHA-1 | `1682d023933bf758c78ce2c18b503efd4f0803b9` |
| SHA-256 | `d0c1f9e77211b3be4e18b731d417627fe6c5dcde6b4306b2d2437d28c9b3ee68` |
| Developer / publisher | Culture Brain / Buena Vista Interactive (GameFAQs entry) |

Phase 0 checks:

* A scan for the 156-byte Nintendo logo found **exactly one** hit (file offset `0x4`), so this is a single GBA image, not a multi-game pack, and no second header is present.
* The entry at `0x08000200` is a normal SDK-style ARM crt0 (stack setup for IRQ/SYS, `CpuSet`-style copy loop at `0x08000250`, then main). It is not a cracktro stub and there is no appended trainer menu. No `SUNHORS`, `MODE7`, `CRC BANDIT` or similar strings.
* Header complement byte is correct; the `0x0000` 16-bit header checksum field is common in retail dumps and is not, by itself, evidence of a rebuild.

## 2. Executive summary

The game has a **developer button-code cheat system**, not a password system:

* Holding **L + R** on the main menu (verified with New Game and Options selected; the dispatcher call is item-independent) opens a `Cheats` overlay. No in-game menu or prompt points at this overlay; it is reachable only by the button combination (published cheat sites describe it as part of the New Game path).
* Pressing **A** on that overlay arms a five-slot entry mode. The five slots are drawn as small crown icons.
* Each accepted code is exactly **five button presses** from the alphabet `{A, B, L, R}`. The full input space is therefore `4^5 = 1024`.
* The ROM contains one 45-byte table at ROM `0x0842386` (file `0x42386`) holding **nine** 5-character strings. The validator is a fixed exact-match lookup over those nine entries, then sets bit *i* of a 32-bit flag word for the matching entry *i*.
* All nine entries are published: the archived GameFAQs cheat page (Wayback capture 2020-02-15) and SuperCheats `#13939` list the same nine sequences. VGChartz lists 0 cheats. The ROM table order is the published *name* order, not the order the fan sites list them in. Every published literal is byte-for-byte present in the ROM.
* The accepted set is **9 of 1024**, with 1015 rejections. Because the accept test is an exact nine-entry table lookup (no generator, no checksum, no second alphabet), **no unpublished accepted code can exist**. This is proven below rather than asserted.
* Unlock bits are RAM-only in the menu object (`0x03007EA4`); entering a code did not write the 512-byte SRAM image. Cheats must be re-entered after a power cycle unless a later game save serialises the menu object (not established here).
* Effects observed: bit 0 sets lives to 99, bit 1 fills the vitality meter, bit 5 makes Select skip a level, bit 8 populates the Movie Clips gallery with the 15 clips. Bit 3's name is shown on unlock. Bits 2, 4, 6, 7 names are in the ROM; their isolated effects were not observed on level 1.

No password screen, no text-entry keyboard, no debug menu and no sound-test/debug strings exist in the image (section 6b gives the searched spaces and counts).

## 3. How to reproduce

### Emulator and keymap

* mGBA 0.10.5 SDL, Xvfb `:322`, `SDL_AUDIODRIVER=dummy`.
* Default SDL keymap used: **A = `x`, B = `z`, L = `a`, R = `s`, Start = `Return`, Select = `BackSpace`, D-pad = arrow keys**.
* Hold each key 60–100 ms; give menus 1–2 s to finish fading. Pressing L+R while the main menu is still fading in is ignored.

### Exact path to the cheat screen

1. Boot. Language screen: choose `English` with A.
2. Wait for the title screen (`Press START`). **L+R does nothing here** (checked).
3. Press Start. Main menu: `New Game`, `Load Game`, `Movie Clips`, `Scrapbook`, `Options`.
4. On a main-menu item (**verified with New Game and Options**; the dispatcher call at `0x08022384` is item-independent), **hold L and R together for ~0.5 s**. The `Cheats` overlay appears with `0 cheats unlocked`, left/right arrows, and `select A` / `back B`.
5. Press **A once** to arm entry. Nothing changes on screen until you press a button; then a crown icon appears in the five-slot row (top-left). The first A is the arming press and is **not** part of the code.
6. Press the five code buttons. Example: **L, R, A, B, L** → `1 cheat unlocked`, `Invincible Cinderella`.
7. After any five-press attempt (accepted or rejected) the entry mode disarms. Press **A again** to enter another code.
8. **B** on the overlay (while disarmed) returns to the main menu.

### Screen enumeration (Phase 2)

Screens actually walked on `:322`:

* Title: `Press START`, copyright line. L+R does nothing; no button code.
* Main menu: `New Game`, `Load Game`, `Movie Clips`, `Scrapbook`, `Options`.
* New Game / Load Game: a three-slot scroll (`New Game` ×3 when empty).
* Movie Clips: `No movies unlocked` with no cheats; with Movie Galore it shows a thumbnail and `Movie 1`, and the ROM's text bank contains `Movie 1`…`Movie 15`.
* Scrapbook: one empty page drawn as a black card with a `?`, no entries.
* Options: `Music` slider, `Sound Effects` slider, `Language`, `Credits`, `back`.
* Cheats overlay: count, unlocked-name display, left/right arrows, `select A` / `back B`, five crown entry slots.
* Pause: `Pause` / `Resume` / `Quit`; L+R does nothing here.

There is **no level-select screen, no sound-test, no password screen and no debug menu**. Level Skip (bit 5) is the only level jump. Scrapbook/movie entries are progression unlocks stored in save data, not an input-code surface.

### Public code sources checked

* GameFAQs cheat page, Wayback capture `20200215095949` of `https://gamefaqs.gamespot.com/gba/925931-disneys-cinderella-magical-dreams/cheats` — all nine sequences.
* SuperCheats cheat `#13939` (`supercheats.com/gameboyadvance/disneys-cinderella-magical-dreams/13939/cheat-codes/`) — all nine sequences.
* VGChartz game 26506 cheats page — “Total cheats available: 0”.
* Direct GameFAQs fetch returned 403; the Wayback capture above was used instead. The SuperCheats text was fetched directly.

Every one of the nine published literals is present in the ROM table at `0x0842386`.

### Codes tested (all accepted; see section 6)

| Cheat | Buttons | Bit | Result |
|---|---|---|---|
| Endless Tries | A B L R B | 0 (0x001) | lives counter becomes 99 |
| Maximum Vitality | B L R L A | 1 (0x002) | vitality meter full length |
| Double Cheese | R R L L A | 2 (0x004) | unlock confirmed (effect not isolated) |
| Invincible Cinderella | L R A B L | 3 (0x008) | name shown; effect inferred |
| Invincible Mice | L L L R L | 4 (0x010) | unlock confirmed (effect not isolated) |
| Level Skip | B R B A L | 5 (0x020) | Select during play advances to next level |
| Stable Magic | A B L B A | 6 (0x040) | unlock confirmed (effect not isolated) |
| Dancing Princess | B L R B B | 7 (0x080) | unlock confirmed; no visible change on level 1 |
| Movie Galore | R L A L R | 8 (0x100) | Movie Clips lists Movie 1–15 |

### Rejected inputs tested in-emulator

| Input | Why it should fail | RAM flags after |
|---|---|---|
| `A A A A A` | not in table | `0x00000000` |
| `L R A B B` | one button off from `LRABL` | `0x00000000` |
| `L R A B` (four presses) | length != 5 | `0x00000000` |
| `A L R A B` | leading A included in the five | `0x00000000` |
| Start inserted then `LRABL` | Start is not in the alphabet | `0x00000008` (Start ignored) |
| Select inserted then `LRABL` | Select is not in the alphabet | `0x00000008` (Select ignored) |
| `AAAAA` then `A LRABL` | re-arm after a failed attempt | `0x00000008` |
| `AAAAA` then `LRABL` | no re-arm; presses go to list navigation | `0x00000000` |

`LRABL` alone is the accepted control and produces `0x00000008`.

## 4. Address map

All ROM addresses are `0x08000000 + file_offset`.

| Address | Meaning |
|---:|---|
| `0x0842386` | Cheat table, 45 ASCII chars + NUL (46 bytes copied) |
| `0x0801F84C` | Literal holding `0x0842386` |
| `0x0801F512` | Cheat overlay screen function (background, list, counters, entry) |
| `0x08022384` | Dispatcher call site: menu action `0xFF` calls `0x0801F512` |
| `0x0801F5A2`–`0x0801F5C0` | Bit-count loop over the flag word (bits 0..9 tested) |
| `0x0801F6DC` | Cheat-name text ID = bit index + 22 |
| `0x0801F706`–`0x0801F70E` | `memcpy(sp+0x20, 0x0842386, 0x2E)` |
| `0x0801F73E`–`0x0801F77C` | Decode input to `A/B/L/R` (tests bits 0,1,9,8) |
| `0x0801F782`–`0x0801F79A` | Append character; increment length at `[sp+0x14]`; buffer at `[sp+0x18]` |
| `0x0801F908`–`0x0801F934` | Length check and 9 × 5-character compare loop |
| `0x0801F936`–`0x0801F95A` | `flags \|= 1 << entry_index`; count newly unlocked in `r4` |
| `0x0801F96C`–`0x0801F972` | Reset length = 0, armed = 0 after any 5-press attempt |
| `0x03007E34` | Menu-object base in IWRAM (runtime) |
| `0x03007EA4` | Cheat flag word (menu object + 0x70), IWRAM |
| mGBA `.ss` gbAs raw `0x20EA4` | Same word inside a savestate (`0x19000 + 0x7EA4`) |
| `0x087D99F6` | Text `Endless Tries` (names follow in order) |
| `0x087D9A4E` | Text `Maximum Vitality` |
| `0x087D9AA8` | Text `Double Cheese` |
| `0x087D9AF5` | Text `Invincible Cinderella` |
| `0x087D9B6C` | Text `Invincible Mice` |
| `0x087D9BCC` | Text `Level Skip` |
| `0x087D9C1E` | Text `Stable Magic` |
| `0x087D9C66` | Text `Dancing Princess` |
| `0x087D9CCD` | Text `Movie Galore` |

Runtime proof of the flag pointer:

* Breakpoint at `0x0801F936` (Thumb) after entering `LRABL`: `sp = 0x03006228`.
* The function computes `r3 = sp + 0x1B80`, then `ldr r1, [r3, #0x28]` → address `0x03007DD0`.
* `[0x03007DD0] = 0x03007EA4`, and `[0x03007EA4] = 0x00000008` (bit 3 for entry index 3).
* `0x03007EA4 = 0x03007E34 + 0x70`, matching the dispatcher's `ldr r0,[r4,#0x70]` at `0x0802238C`.

## 5. Algorithm

```
ALPHABET = "ABLR"
TABLE = "ABLRBBLRLARRLLALRABLLLLRLBRBALABLBABLRBBRLALR"   // 9 records of 5
ENTRY_LEN = 5

state:
    armed  : bool           // [sp+8]
    len    : int            // [sp+0x14]
    buf[5] : char           // [sp+0x18]
    flags  : u32            // [menu_obj+0x70], runtime 0x03007EA4
    cooldown : int          // [sp+0x0C]; set to 30 frames after a submission

on_button(c):                       // c is a newly-pressed button
    if not armed:
        if c == A: armed = true; play confirm sound; return
        if c == B: leave overlay; return
        if c in {LEFT, RIGHT}: move list selection (0..9); return
        return

    if cooldown > 0: return

    ch = map(c): A->'A', B->'B', L->'L', R->'R'; else return
    buf[len++] = ch
    if len != 5: return

    matched = -1
    for i in 0..8:
        if memcmp(buf, TABLE[i*5 : i*5+5], 5) == 0:
            matched = i
            break

    if matched >= 0:
        bit = 1 << matched
        if (flags & bit) == 0:
            flags |= bit
            newly_unlocked++
            show "%d cheat(s) unlocked"
    len = 0
    armed = false
    cooldown = 30
```

Notes derived from the disassembly:

* The character is taken from `0x0802D27C` (edge/pressed state), so a held button does not repeat; one press yields one character.
* Priority for simultaneous buttons is A, then B, then L, then R (`0x0801F748`, `0x0801F758`, `0x0801F768`, `0x0801F778`).
* The table is re-copied from ROM on every overlay entry (`0x0801F706`), so there is no runtime mutation of the table.
* The compare is signed-byte `ldrsb` on both sides; both are positive ASCII, so no alias.
* `matched` is the table record index; the bit number equals the record index. There is no base offset or permutation.
* The overlay can be opened from any main-menu item; the published “select New Game” instruction is a sufficient but not necessary condition. It does not open at the title screen or in the pause menu.

## 6. Tables

### 6.1 Cheat records

ROM `0x0842386`, 46 bytes:

```
41 42 4c 52 42   A B L R B   index 0  bit 0x001  Endless Tries
42 4c 52 4c 41   B L R L A   index 1  bit 0x002  Maximum Vitality
52 52 4c 4c 41   R R L L A   index 2  bit 0x004  Double Cheese
4c 52 41 42 4c   L R A B L   index 3  bit 0x008  Invincible Cinderella
4c 4c 4c 52 4c   L L L R L   index 4  bit 0x010  Invincible Mice
42 52 42 41 4c   B R B A L   index 5  bit 0x020  Level Skip
41 42 4c 42 41   A B L B A   index 6  bit 0x040  Stable Magic
42 4c 52 42 42   B L R B B   index 7  bit 0x080  Dancing Princess
52 4c 41 4c 52   R L A L R   index 8  bit 0x100  Movie Galore
00
```

### 6.2 Flag word

| Bits | Meaning | Evidence |
|---|---|---|
| 0..8 | Cheat unlocked (one bit per record) | table loop bound 9; observed `0x001`, `0x002`, `0x008`, `0x020`, `0x080`, `0x100`, `0x1FF` |
| 9..31 | Unused / no code path sets them | only writer is `flags \|= 1 << index`, index < 9 |

Diagnostic (not a game code): writing `0x000003FF` to `0x03007EA4` in a savestate and re-entering the overlay still displayed `9 cheats unlocked` and no tenth name. The game has no tenth name string; bits 9+ are not a hidden cheat.

### 6.3 UI strings (English bank)

| String | File offset |
|---|---:|
| `Cheats` | `0x7D9530` |
| `%d cheat unlocked` | `0x7D9D21` |
| `%d cheats unlocked` | `0x7D9D8A` |
| `Enter Cheat` | `0x7D9DF9` and `0x7D9E13` |
| `Level %d` | `0x7D9E41` |
| `No movies unlocked` | `0x7DA267` |

`Enter Cheat` exists in the text bank but was not observed on the reachable overlay; the overlay banner reads `Cheats` (both the `MenuBKG_Cheats` background asset and a `Cheats` text string exist).

## 6b. Enumeration

### Space definition

* Alphabet: `{A, B, L, R}` — exactly four symbols. The input decoder tests only key bits 0 (A), 1 (B), 9 (L) and 8 (R) at `0x0801F748`–`0x0801F77C`.
* Length: exactly 5. The compare only runs when the length word equals 5 (`0x0801F90A`), and the append path cannot exceed 5 because any fifth press resets the length.
* Representable values: `4^5 = 1024` button strings.
* Checksum/reserved fields: none. This is a lookup table, not an arithmetic code.
* Table size: 9 records × 5 bytes = 45 bytes plus NUL. The compare loop's upper bound is 9 (`cmp r1,#9` at `0x0801F968`).

### Accepted set (complete)

Exactly the nine records in 6.1. All nine are present in the archived GameFAQs list and in the SuperCheats list; VGChartz has no entries. A scripted comparison of the published name→buttons map against the ROM table returns 9/9 matches, 0 mismatches.

Published order is different (sites list alphabetically or by convenience); table order is the name order used by the game's text IDs (`name_id = bit + 22`).

### Novel code result

**No unpublished accepted code exists.** The proof is structural, not statistical:

1. The only accept path is a 5-byte inline compare of the input characters against one of nine fixed 5-byte slices of `0x0842386`.
2. The slice base is `entry_index * 5`, entry index runs 0..8, and the match sets bit `1 << entry_index`. There is no generator, no key, no checksum, no XOR, no range transform.
3. The whole 8 MiB image contains exactly **one** run of five or more characters from `{A,B,L,R}` that is a code table: the one at `0x42386`, reached by the literal at `0x0801F84C`. The only other `[ABLR]{5,}` byte runs are incidental data (`0x3DA719`, `0x48A309`, `0x48A329`, `0x48F461`); none has a pointer literal anywhere in the image.
4. The table is copied from ROM on every overlay entry; no runtime patch or second table exists.

Therefore the published list is complete. Minting a “novel accepted code” is mathematically impossible for this ROM; the honest deliverable is the exhaustive characterisation and the rejection bounds below. What *is* unpublished is the reachability/entry procedure: the L+R overlay works on every main-menu item (verified on New Game and Options; derived from the dispatcher), A arms a hidden five-slot mode, a failed five-press attempt disarms, and Start/Select are ignored inside a sequence (the decoder has no branch for them). Those behaviours were verified in-emulator and are not in any published list.

Unpublished accepted **input strings** exist only trivially. Because Start, Select and the arming A are not part of the five-character payload, the full press strings `START LRABL`, `SELECT LRABL` and `A LRABL` all unlock bit 3 (`0x03007EA4 = 0x00000008`) while appearing in no published list. They are not new cheats: the validator sees exactly `LRABL`. This is stated so the negative result is not confused with an untested space.

### Search spaces (counts)

| Space | Method | Result |
|---|---|---|
| All printable strings (length ≥ 3) | `strings -t x -n 3`, 81,563 lines | `password` 0, `debug` 0, `secret` 0, `cheat` 10, `code` 4, `unlock` 3, `level` 40 |
| Runs of `[A-B-L-R]` length ≥ 5 | byte scan of all 8 MiB | 5 hits: the real table at `0x42386`; incidental data at `0x3DA719`, `0x48A309`, `0x48A329`, `0x48F461`; no literal points to the incidental runs |
| Runs of `[U-D-L-R-A-B]` length ≥ 5 | byte scan | 1,619 hits, dominated by graphics/data; only the `ABLR` run at `0x42386` is reached by a literal pool |
| u16 key-mask runs (values 1,2,4,8,0x10…0x200) | 8-word sliding window | 769 runs of ≥5, dominated by repeating graphics patterns (0x100/0x80, 0x200/0x80); a direct search for the published sequences as u16 masks found nothing |
| On-screen alphabet / keyboard | literal search for `ABCDEFGHIJKLMNOPQRSTUVWXYZ`, lowercase, `0123456789` | no alphabet string; `0123456789ABCDEF` at `0x2AF38` is the C-library printf digit table |
| Debug / sound-test / level-select strings | case-insensitive string search | no `debug`, `test mode`, `sound test`, `level select`, `gallery` UI strings |

### Bounds proven by rejection

Starting from a clean flag word (`0x00000000`, savestate ss1) and re-loading for each test:

| Candidate | Expected by model | Observed flags | Screen |
|---|---|---|---|
| `AAAAA` | reject | `0x00000000` | stays on overlay |
| `LRABB` | reject (last char wrong) | `0x00000000` | stays |
| `LRAB` | reject (4 < 5) | `0x00000000` | stays |
| `ALRAB` | reject (leading A consumed as arm; five chars are ALRAB) | `0x00000000` | stays |
| `START LRABL` | Start ignored; LRABL accepted | `0x00000008` | `1 cheat unlocked` |
| `AAAAA` + `A` + `LRABL` | first reject, re-arm, accept | `0x00000008` | `1 cheat unlocked` |
| `AAAAA` + `LRABL` | first reject, no re-arm; L/R navigate | `0x00000000` | no unlock |
| `LRABL` | accept | `0x00000008` | `1 cheat unlocked` |
| `LRABL` + `A` + `LRABL` | two accepts, same bit; second is duplicate | `0x00000008` | count stays 1 |

The all-nine run produced `0x000001FF` (bits 0..8) and the overlay reported `9 cheats unlocked`.

### Complete-state evidence

| State | Flags at `0x03007EA4` | Observation |
|---|---|---|
| ss1 (main menu, no codes) | `0x00000000` | overlay `0 cheats unlocked` |
| ss2 (after `LRABL`) | `0x00000008` | `1 cheat unlocked`, `Invincible Cinderella` |
| ss3 (after all nine) | `0x000001FF` | `9 cheats unlocked`, `Movie Galore` |

The same values were read live through the mGBA CLI debugger at breakpoint `0x0801F936`; `0x03007EA4 = 0x00000008` after `LRABL`.

## 7. Validation evidence

### Observed (emulator / RAM)

* Overlay opens with L+R on the main menu; title screen L+R does nothing; pause-menu L+R does not open it.
* Five crown slots appear as buttons are pressed after A; `0 cheats unlocked` / `1 cheat unlocked` / `9 cheats unlocked` messages.
* `0x03007EA4` values `0x0`, `0x8`, `0x1FF` after 0, 1 and 9 codes.
* `Endless Tries` (bit 0) changes the lives counter from 3 to 99 on a fresh New Game.
* `Maximum Vitality` (bit 1) makes the vitality meter full-length while lives stay 3.
* `Level Skip` (bit 5): Select during play fades out and loads the next area (first area → sunflower/scarecrow area).
* `Movie Galore` (bit 8): `Movie Clips` changes from `No movies unlocked` to a browsable thumbnail and `Movie 1` (the text bank contains `Movie 1`…`Movie 15`).
* `Dancing Princess` (bit 7) produced no visible change on level 1 (same sprite, lives, meter).
* All nine published literals are accepted; the nine table records are byte-for-byte identical to them.
* Unlocking a code did not modify the 512-byte `cinderella.sav` (`cmp` reports 0 differing bytes before/after one unlock).

### Derived (instruction sequence / table)

* Exact nine-entry validator, bit index = table index, no second format.
* Table address, literal pointer, copy length 0x2E, compare bound 9, reset of length and armed state.
* Alphabet is exactly A/B/L/R; priority A>B>L>R for simultaneous presses.
* The menu dispatcher calls the overlay when the menu action is `0xFF` (`0x08022384`).

### Inferred

* Effects of bits 2 (`Double Cheese`), 3 (`Invincible Cinderella` beyond the name), 4 (`Invincible Mice`), 6 (`Stable Magic`): names are from the ROM text table; isolated gameplay effects were not observed in level 1. Bit 3 is very likely damage immunity by name, but this is labelled inferred.
* Bit 9+ purpose is unknown; the only writer cannot set them, and a diagnostic `0x3FF` state produced no tenth UI entry.
* Persistence of the flag word across an in-game save was not established; unlocking alone did not touch SRAM.

## 8. Unknowns

* Whether an in-game save serialises the menu object at `0x03007E34` (and therefore the cheat bits). The only observed write was the RAM bit set; the 512-byte `.sav` was unchanged at unlock time.
* Isolated effects for bits 2, 4, 6 and 7. Their names and bit positions are proven; their gameplay hooks were not exercised.
* The exact intended purpose of the 10th bit tested by the count loop (`cmp r0,#10`) and of the unused `Enter Cheat` text string. No code path can set bit 9 and no tenth name exists.

## 9. Tooling

* `objdump` (`arm-none-eabi-objdump -M force-thumb`) for the validator and overlay function.
* Capstone 5 for the PC-relative literal scan that located the table pointer.
* mGBA 0.10.5 SDL on Xvfb `:322`, driven with `xdotool`; screenshots with ImageMagick `import`.
* mGBA command-line debugger (`mgba -d`) for `b`, `c`, `r/4`, `status`; breakpoint at `0x0801F936` and `0x0801F5A2`.
* Savestate inspector: mGBA `.ss` PNG `gbAs` chunk, `zlib.decompress`, IWRAM at raw `0x19000`; flag word at raw `0x20EA4`.
* Scripts written for this job: `cheat_space.py` (table extraction + 1024-space enumeration), `trial.py` (one candidate per fresh state, OCR banner gate), `effect.py` (unlock → New Game → HUD), `spatch.py` (diagnostic savestate byte patch), `md.py` (focused mGBA/xdotool driver).
* No GameShark/CodeBreaker codes were used or published. The savestate patch was a diagnostic only, used to test bit 9 and clearly labelled as not a game code.

## 10. Legal note

No ROM, graphics, music or text assets are redistributed. Only hashes, addresses, the game's own nine short cheat strings, and the analysis are published.
