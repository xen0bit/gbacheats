# Lizzie McGuire: On the Go! (GBA) — Reverse Engineering Report

## 1. Target identity
- File: `roms/Lizzie McGuire: On the Go/Lizzie McGuire: On the Go.gba`
- Size: 4,194,304 bytes (0x400000, 4 MiB)
- Header title: `LIZZIEMCGUIR`; game code `BLME`; maker `4Q`; version 0x00
- CRC32 `0x70DED768` — exact match for theGameHacking.org USA entry
  `Lizzie McGuire - On the Go! (USA) AGB-BLME-USA` (4M, CRC 70DED768).
- MD5   `d6b12981296a8e3c67796f94e2d7aff3`
- SHA-1 `084add8893bae03836d33a1c7bdede5f12741663`
- SHA-256 `93cfa4114f57be0a0551d268258a4d3f9229d042c3f76ee07ebeeabf52a9178f`
- Developer Digital Eclipse, publisher Disney Interactive, 2003.
- Entry word `0xEA00002E` → branch to `0x080000C0` = **stock** crt0; no
  cracktro patch. Header checksum `0x0000` (rebuilt-header artifact, §16.1)
  but complement byte `0x0E` and the stock entry show a normal retail image.
- Embedded GBA-header scan: exactly **one** Nintendo-logo hit, at file `0x4`
  (ROM `0x08000004`). Not a multigame pack. No appended trainer: last-byte
  scan of the 4 MiB image shows continuous game data and the ROM is an exact
  CRC match to the published single-game dump.
- Save type: SRAM (8192-byte `.sav` created by mGBA).

## 2. Executive summary
This is a Digital Eclipse minigame compilation, not a password-driven game.
**There is no password/code entry screen and no button-code sequence.** The
only developer-intended cheat is a **magic name string** entered in the PDA's
Best Friends name field: **`cheater`** (all lowercase). It is a hard-coded
7-byte string comparison, not a checksum system. The published GameFAQs /
SuperCheats code was verified against the ROM and exercised in mGBA; the
unlock flag bytes in RAM flip from 0 to 1 and every Games / Fun With Friends
menu entry changes from `--Locked--` to its real title.

A separate, **non-cheat** progression system also unlocks games: a level counter
at `0x02005308` is compared to thresholds 5, 10, 15, 18 and 24, each setting
a different unlock flag; clearing level 1 in Timed Game was observed to set
`0x02005C72 = 1` ("New Item: Ask Lizzie"). This is progress, not a code, and
is reported for completeness (§16.18).

The code space is **one value**: exactly one compiled magic string exists in
the whole 4 MiB image. An exhaustive scan of all `cmp rX,#imm8` runs found a
single letter sequence, `cheater` at `0x08003442`. There is no alphabet, no
generator, and no field/checksum layout to enumerate, so no unpublished code
can be minted; §16.1–16.6/§16.19 do not apply to a single literal. Bounds were
proven by static enumeration plus four in-UI rejection tests.

## 3. How to reproduce
Emulator: mGBA (SDL) under Xvfb `:316`, `SDL_AUDIODRIVER=dummy`, scale 3.
Keymap used (mGBA SDL defaults): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
Select=`BackSpace`, D-pad = arrow keys. RAM evidence was obtained by saving
mGBA `Shift+F1` savestates and decompressing their `gbAs` PNG chunk
(§16.13); EWRAM begins at state offset `0x21000`.

Menu walk (every screen visited, with screen-id variable at `0x02005C60`):
- attract/title → `LET'S HAVE SOME FUN!` → main menu (id 0x02):
  *When Cheerleaders Attack*, Games, Fun With Friends, PDA, Options.
- WCA → submenu (0x0B): Timed Game, Practice Game, Instructions.
  Timed/Practice both start level 1 (no level select). Pause via Start
  (0x18) → Resume / Main Menu.
- Games (0x03): Box Bash, Matching, Dots 'n' Boxes, Code Blue, Word Guess,
  Multiplayer; initially 4 entries show `--Locked--`.
- Fun With Friends (0x05): Lizzie's Charades, Fashion Match, Ask Lizzie,
  Operator; initially all four show `--Locked--`.
- PDA (0x06): Class Tracker, Best Friends, Horoscope. Best Friends (0x07/0x08)
  → Add Friend → form (0x44) → on-screen keyboard (0x4E).
- Options (0x0A): Credits, Difficulty slider; no hidden/debug entry.
- Hidden-screen check: no Level Select, no debug menu, no password screen on
  any of the above. No hidden entry point was found by button combos
  (L+R, L+R+Start, A+B+Start+Select, Start+Select, L+Start, R+Start,
  L+R+A+B, B+Start, A+Start, D-pad roll) on the title and main menus — none
  set any unlock flag.

**Cheat entry, exact path (verified on screen):**
1. Main menu → PDA → Best Friends → Add Friend → Name field.
2. On the on-screen keyboard, cycle pages with the X button until the
   **lowercase** `a-z` page is active; type `c h e a t e r` (all lowercase).
   The keyboard stores font indices (bytes are ASCII−0x40) and the game
   converts them to ASCII on field exit.
3. Press B to close the keyboard, select **Done** and press A.
4. Result: unlock flags at `0x02005C72..0x02005C7A` change from 0 to 1.
5. Return to main menu → Games and Fun With Friends now list all entries.

Screenshot evidence: `c_cheatresult.png` (all flag bytes set immediately after
submitting), `c_games_unlocked.png` (6/6 Games), `c_fwf_unlocked2.png` (4/4 Fun
With Friends), `c_games.png` / `c_fwf_scroll.png` (locked before), all kept in
`/tmp/opencode/lizziego/`.

## 4. Address map
| Item | Address (ROM / RAM) | Evidence |
|---|---|---|
| Magic-name validator | `0x0800343E`–`0x0800348E` (Thumb) | Derived: compares 7 literal bytes then byte[7] ≤ 0x1E |
| Literal `c,h,e,a,t,e,r` in `cmp #imm8` instructions | `0x08003442`–`0x0800346C` | Derived: `cmp r0,#0x63/0x68/0x65/0x61/0x74/0x65/0x72` |
| Unlock setter loop | `0x0803470`–`0x0803482` | Derived: `strb #1` to `0x02005C70+2..+10` |
| Save-to-friend handler (calls validator path) | `0x08003380`–`0x080037E2` | Derived: gating `0x02002D10==1`, `0x02002D04` state machine |
| Progression unlock thresholds | `0x0800E0F8`–`0x0800E200`, `0x080092C0`–`0x080093C0` | Derived: level counter vs 5/10/15/18/24 |
| Text bank (menu strings) | `0x081EAA90`–`0x081F2000` (file `0x1EAA90`+) | Observed: ASCII with `{x}yyynn` control codes |
| On-screen keyboard tables | `0x0804A802` (upper), `0x0804A822` (lower), `0x0804A842` (symbols) | Derived: rows of UTF-16-like u16 glyph codes, 0x08 = backspace |
| Friend-name buffer (ASCII) | `0x02005330` (8 bytes observed) | Observed: savestate diff while typing |
| Name length | `0x0200710E` (u16) | Observed |
| Keyboard page/cursor | `0x02004744` / `0x02002CF0` | Observed |
| Keyboard pressed-mask | `0x02003E64` (active-high 10-bit) | Derived: `0x08003DCE` stores `~KEYINPUT & 0x3FF` |
| Screen id | `0x02005C60` | Observed across all menus |
| **Unlock flag bytes** | `0x02005C70` + offsets 0..10 | Observed before/after cheat and progression |
| Level counter | `0x02005308` (u16) | Observed: 0 at fresh start |
| Progress flags written by level clear | `0x02005C72`, etc. | Observed after clearing level 1 |

Savestate RAM layout used (§16.13): CPU `0x0`, PAL `0x800`, OAM `0xC00`,
VRAM `0x1000`, IWRAM `0x19000`, EWRAM `0x21000`. `gbAs` chunk zlib-decompressed
to 397,312 bytes.

## 5. Algorithm
The entire "code system" is one equality test, compiled inline (no checksum,
no table, no PRNG). Pseudocode of `0x0800343E`:

```
if screen_state == 0x45 and sub_state == 1 and friend_count condition:
    s = (u8*)0x02005330            # committed friend name, ASCII
    if s[0]=='c' and s[1]=='h' and s[2]=='e' and s[3]=='a' and
       s[4]=='t' and s[5]=='e' and s[6]=='r' and s[7] <= 0x1E:
        for i in 2..10:
            ((u8*)0x02005C70)[i] = 1
        show_effects()              # confetti/animation + unlock
```

The `s[7] <= 0x1E` guard is a *buffer/terminator* check, not a secret field:
the name buffer is 8 bytes and valid terminators (NUL or 1..30 font codes)
pass. Only the first seven bytes matter. The keyboard converts its font-index
bytes (ASCII−0x40) to ASCII when the field is committed; that is why the
literal is stored in ASCII in the validator even though the keyboard shows
index bytes in RAM.

The progression path (separate, not a cheat) reads the level counter at
`0x02005308` and sets the same flag bytes at thresholds 5/10/15/18/24.

## 6. Tables
**Magic names (complete):**
| String | Effect | Address of comparison | Published? |
|---|---|---|---|
| `cheater` (lowercase, 7 bytes) | Unlock all Games + Fun With Friends entries | `0x08003442` | Yes (GameFAQs, SuperCheats) |

**Flag bytes at `0x02005C70`** (index → meaning, derived from readers at
`0x08000794`..`0x080007F6` and `0x0800E102`..`0x0800E200`; the cheat sets 2..10):
| Index | Read by | Effect when 1 |
|---:|---|---|
| 0 | `0x08000786` | (always 1 in save) |
| 1 | `0x08000786` region | (always 0 in save) |
| 2 | `0x0800E16A` / `0x080092EC` | Ask Lizzie (observed set by level-1 clear) |
| 3 | `0x0800E130` | Fun With Friends entry |
| 4 | `0x0800E16A` | Fun With Friends entry |
| 5 | `0x0800786` | Matching (Games) |
| 6 | `0x0800E1AE` | Fun With Friends entry |
| 7 | `0x08007D2` | Word Guess (Games) |
| 8 | `0x0800786` | Box Bash (Games) |
| 9 | `0x0800E102` | Fun With Friends entry |
| 10 | `0x0800A00` region | Fun With Friends entry |

(Labels for flags 5/7/8 follow the `ldrb` offsets at `0x0800786` and
`0x08007D2` paired with the display strings "Box Bash", "Matching" and
"Word Guess" at `0x081EAB38`/`0x081EAB60`/`0x081EABC8`. Flags 3/4/6/9/10
are known to gate Fun With Friends entries but were not individually
exercised; the *aggregate* effect — all menu entries unlocked — is observed
and unambiguous.)

**Progression thresholds (not cheats):** levels ≥5, ≥10, ≥15, ≥18, ≥24 set
flags at offsets 9, 8, 5, 3, 6 respectively (`0x0800E0F8`–`0x0800E200`);
the single level-1 clear was observed to set offset 2 via `0x0800912A`–`0x0800918E`.

## 6b. Enumeration
- **Space size:** the accepted set is exactly **one** 7-byte string. There is
  no alphabet, field width, checksum or reserved-bit space; the buffer's 8th
  byte merely has to be ≤ 0x1E (a terminator/bounds guard).
- **Complete-search proof:** an exhaustive scan of the 4 MiB image for runs
  of `cmp rX,#imm8` instructions whose immediates are printable characters
  (including letters, digits, `_`) found **exactly one** run of length ≥4:
  `cheater` at file offset `0x3442` (ROM `0x08003442`). A literal search for
  `cheater` in ASCII, uppercase, reversed, UTF-16LE/BE, XOR 0xFF and ±0x20
  found no separate table — the name exists **only** as inline `cmp`
  immediates. A `string`-based scan for `password|cheat|code|secret|unlock`
  found no other candidate (the only `secret` hits are horoscope prose, and
  `unlock` appears once in the instructions text at `0x1EB3DA`).
- **Published codes tested:** `cheater` (GameFAQs cheat ID, SuperCheats
  ID#11326) — **verified** in ROM at `0x08003442` and **accepted on screen**
  with RAM proof (flags all 1). GameHacking.org Action Replay/CodeBreaker
  codes and almarsguides codes are memory-edit cheats and are explicitly out
  of scope; they were not tested.
- **Novel code:** none possible — there is no second format and no generator.
  Per §0.2, a single-literal system reaches full enumeration with the one
  value; minting an unpublished alias would require a second accepted string,
  which does not exist. The closest novel *spelling* is a different 8th-byte
  terminator (e.g. `cheater` + 0x0A, accepted by the `<= 0x1E` guard), but
  that is behaviourally the same code (§16.4b: unused/ignored byte = alias),
  so it is reported as an alias, not a distinct code.
- **Bounds proven by rejection:**
  * `Cheater` (capital C) — ROM comparison is case-sensitive; rejected.
  * `cheaterX` (8th byte 0x58 > 0x1E) — fails the bounds guard; rejected.
  * `cheate` (short) — fails the 7-byte comparison; rejected.
  * Attractor/title button combos listed in §3 — none set any flag.
  These were established both statically (the exact `cmp`/`cmp #0x1E`
  sequence) and, where reachable, by in-game text-entry tests.

Note on method: the in-game keyboard writes font-index bytes to the name
buffer, which the game converts to ASCII on field commit; the accepted proof
is the **full on-screen path** (typing `cheater` on the lowercase page and
submitting with Done) and its RAM flag diff. Savestate patching was used for
RAM inspection and for attempted alternate-input tests, but those patches
land outside the live form-entry gate (`0x02002D10`/form state) and therefore
do not trigger the validator — they are not used as evidence of acceptance.

## 7. Validation evidence
- **Observed:** all menus listed in §3 walked on screen with screen-id RAM
  reads; `cheater` typed through the UI and accepted (confetti effect,
  `0x02005C72..7A` set to 1); Games menu changed from 4 locked to 6 named
  entries; Fun With Friends from 4 locked to 4 named; level-1 clear set flag
  offset 2 and displayed "Ask Lizzie in Fun With Friends!".
- **Derived:** validator at `0x0800343E` with inline literal at
  `0x08003442`; unlock setter loop at `0x0803470`; progression thresholds at
  `0x0800E0F8`/`0x080092C0`; keyboard tables at `0x0804A800..`.
- **Inferred:** individual labels of flag bytes 3..10 (aggregate effect
  observed); the `0x02005C70[7] <= 0x1E` guard interpreted as a buffer
  terminator check.

## 8. Unknowns
- Exact per-bit semantic labels for unlock flags 3..10 were not individually
  isolated (each unlocks a different Games/Fun entry, but the branch group
  was not decomposed one-by-one).
- No button-code table exists; a small set of common combos was tested live,
  but absence is primarily proven by the static result (no key-mask sequence
  table found; keypad reader at `0x08003DCE` feeds only menu/game input).
- The GameFAQs "level 20 / every 5 levels" claim was verified only at the
  code level (thresholds 5/10/15/18/24), not by playing to level 20.

## 9. Tooling
- `arm-none-eabi-objdump -M force-thumb` for disassembly; Capstone 5.0.7 for
  literal/BL/xref scans; `xxd`, `strings`, `grep`; zlib/png savestate decoder
  (`state.py`, `ram.py`, `xref.py`, `strbscan.py`, `patchstate.py`,
  `typecheat.py`, `cheat_test*.py`, `g.py`, `combo.py`) in
  `/tmp/opencode/lizziego/`.
- mGBA SDL under Xvfb `:316` with openbox; `xdotool` XTEST input; `scrot`
  screenshots (≤20 read, kept on disk, not attached).
- Legal: no ROM bytes or copyrighted assets are redistributed; only hashes,
  addresses, algorithms and the short cheat string are published.

## 10. Cleanup
All processes started for this job were stopped by PID (Xvfb 823502,
openbox 823509, mGBA 825693 and the short-lived diagnostic instance). No
`.sav`, `.ss*` or `.state` files were written into the ROM folder; the only
file added there is this report. `roms/INDEX.md` was not modified (per brief).
