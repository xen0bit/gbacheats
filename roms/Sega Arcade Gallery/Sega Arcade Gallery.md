# Sega Arcade Gallery (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Sega Arcade Gallery.gba` |
| Size | 8,388,608 bytes (0x800000) |
| Header title | `SEGA ARCADE` |
| Game code | `AYPE` (USA SKU per cartreader CRC list) |
| Maker | `78` (THQ) |
| Version | 0x00; fixed byte 0x96; complement 0xD3; header checksum 0x0000 |
| Entry word | `0xEA06EF8B` (ARM `b` into crt0 at 0x0806EFB0) |
| CRC32 | `3B8FFDF4` (matches *SEGA Arcade Gallery (USA)* in sanni/cartreader `sd/gba.txt`) |
| MD5 | `0bb34790a91d40f7afc437c528102496` |
| SHA-1 | `6ce77309c2caacf466f9a2c37c3fe84e4ce23242` |
| SHA-256 | `de0e0152d55666b29cd2d414761852b7ae7645189a0db7c5e920ecb331c9eb82` |

**Phase 0 image scan:** scanning all 0x800000 bytes for the 156-byte Nintendo logo prefix
`24 ff ae 51 69 9a a2 21` returns exactly **one** hit, at file offset 0x4. There is no
second embedded GBA header, no appended trainer, no cracktro, and no patch/trainer
menu. The four component games are compiled into one executable image (shared shell at
`0x081C0000`–`0x081E0000`, per-game modules above `0x081E0000`), **not** concatenated
ROMs. Header checksum `0x0000` with complement `0xD3` is the normal rebuilt-header
artifact described in guide §16.1; the entry branch is a valid ARM branch, not a cracktro.

Component games identified from the ROM's own credit/name strings and on-screen art:

| ROM copyright string | File offset | Game |
|---|---|---|
| `PROGRAM YU SUZUKI 1986 SEP` / `SEGA 1986` | 0x2149D9 / 0x2149F5 | **Out Run** |
| `fSEGA 1992` | 0x214CFE | **OutRunners**-style 1992 game data (music/course strings) |
| `fSEGA 1985` | 0x2154F3 | **Space Harrier** (stage names MOOT/GEEZA/…/ABSYMBEL) |
| `fSEGA 1987` | 0x215BDB | **After Burner** / **Super Hang-On** data |

The released four games (confirmed by the game-select art and 3rd party cheat indexes) are
After Burner (1987), Out Run (1986), Space Harrier (1985) and Super Hang-On (1987).

---

## 2. Executive summary

This cart has **one in-game, developer-intended cheat system**, not a password system.
It is a **button-code entered inside the credits sequence**, reached through a hidden
title-screen option:

1. At any game's title screen hold **L + R + Select and tap Up**. The top option bar
   changes from `PLAY` to `SHOW CREDITS` (observed, screenshot `gate_after_screen.png`).
2. Select `SHOW CREDITS`. The credits scroll as letter-bubbles. During credit entries
   **1, 2 and 3** press the code; the game checks the *credit entry index* as well as
   the button mask.
3. The published sequence (3rd party cheat indexes) is
   **Left, Right, Left, Right → Up, Down → A**, which toggles a global flag: infinite
   time in Out Run / Super Hang-On, infinite continues in After Burner / Space Harrier.
   Entering it again disables it (different voice sample).

I located the validator at **`0x081C1220`** and its two 4-byte-record code tables at
**`0x08352C2C`** and **`0x08352C4C`**. Table 1 is byte-for-byte the published code.
**Table 2 is a second, mirrored sequence that appears in no published list**:
`Right, Left, Right, Left → Down, Up → B`. It writes a separate flag byte. This is the
novel code delivered by §0.2.

There is no password screen, no GameShark/CodeBreaker-style surface to reverse, no
debug-level select, and no fourth hidden option beyond `SHOW CREDITS`: the gate tests
and the two code tables fully characterise the in-game cheat surface.

---

## 3. How to reproduce

Emulator: mGBA 0.10.5 (`/usr/local/bin/mgba`), `SDL_AUDIODRIVER=dummy`, Xvfb `:317`,
`mgba -3`. Default mGBA keymap: **A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
Select=`BackSpace`, D-pad=arrow keys**. Hold keys 100 ms (10 ms taps are missed).

Boot takes ~12–13 s (THQ logo → SEGA legal → `PRESS START`).

1. `Return` → game select (2×2 grid: After Burner / Out Run / Space Harrier / Super Hang-On).
2. `Right`, `x` → Out Run title (`PLAY` in top bar).
3. Hold `a`+`s`+`BackSpace`, tap `Up`, release → bar reads `SHOW CREDITS`.
4. `x` → credits.
5. During credit entries 1/2/3 enter the code. **Published code:**
   `Left Right Left Right` (entry 1), `Up Down` (entry 2), `A` (= `x`) (entry 3).
   **Novel code:** `Right Left Right Left` (entry 1), `Down Up` (entry 2), `B` (= `z`) (entry 3).
6. `B` (`z`) skips the credits back to the main title. Effects persist across game
   changes until the code is re-entered or power is cycled.

For static reproduction of the addresses:
```bash
arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 \
  --start-address=0x081C1220 --stop-address=0x081C1400 -M force-arm game.gba
```
(Remove `-M force-arm` on builds that reject it; raw disassembly is ARM at these addresses.)

Web source verified: 3rd party cheat indexes
(HTTP 403 on direct fetch; full text recovered from the search-engine indexed copy).

---

## 4. Address map

| Address (ROM / RAM) | Meaning | Evidence |
|---|---|---|
| file 0x0 / `0x08000000` | Only GBA header (logo at +4) | Derived (logo scan) |
| `0x081C1220` | Main-loop top; **cheat validator** (both tables) | Derived (`b 0x81c1220` at 0x081C15C8; disassembly) |
| `0x081C1254`–`0x081C12CC` | Table-1 matcher; toggles flag on full match | Derived |
| `0x081C12D0`–`0x081C133C` | Table-2 matcher; sets flag on full match | Derived |
| `0x081C1650`–`0x081C169C` | Validator literal pool | Derived |
| `0x08352C2C` | Code table 1 (published), 7×4 B + u32 0 terminator | Derived (byte dump) |
| `0x08352C4C` | Code table 2 (unpublished), 7×4 B + u32 0 terminator | Derived (byte dump) |
| `0x08352D6C`–`0x083531CC` | ASCII credits text bank (role/name pairs) | Derived (init literals at 0x081C1854) |
| `0x081C1854` / `0x081C1884` / `0x081C18B0` | Credits init / tick / bubble renderer | Derived |
| `0x03001354` | Key state: `+0` held, `+2` newly-pressed, `+4` released, `+6` repeat | Observed (IWRAM writer at `0x03005C50`; read `0x00000010` while Right held) |
| `0x03002500` | Shared UI/credits/cheat state struct | Derived + observed |
| `0x03002504` | Table-1 current record pointer (init `0x08352C2C`) | Derived + observed (`r/4`) |
| `0x03002508` | Table-2 current record pointer (init `0x08352C4C`) | Derived + observed |
| `0x03002520` | **Credit entry index**; must equal 1/2/3 for the code records | Observed (`r/1` over time) |
| `0x030023C5` | Cheat flag 1 (toggled; sounds 1/27) | Derived |
| `0x030023C6` | Cheat flag 2 (set to 1; sound 2) | Derived |
| `0x04000130` | KEYINPUT; read by IWRAM routine `0x03005C50` | Observed (mGBA watchpoint hit) |

---

## 5. Algorithm

The shell polls keys once per frame. The validator runs every frame as the top of the
main loop. Pseudocode, exactly as the ARM code implements it:

```c
// per frame, from 0x081C1220
key_state = *(u32*)0x03001354;      // held | (pressed << 16)
pressed   = key_state >> 16;        // active-high mask; 0 if no new press
if (pressed == 0) goto check_table2;

// table 1 — 0x081C1254
rec = *(u32**)0x03002504;           // current record pointer
if (*(u8*)(rec+0) == *(u8*)0x03002520 &&   // required credit index
    *(u16*)(rec+2) == pressed) {           // required button mask
    *(u32**)0x03002504 = rec + 4;          // advance
    if (*(u32*)(rec+4) == 0) {             // terminator reached
        u8 f = *(u8*)0x030023C5 ^= 1;      // TOGGLE global cheat flag
        play_sound(f ? 1 : 27);            // voice: congratulate / be careful
    }
} else {
    *(u32**)0x03002504 = (u32*)0x08352C2C; // reset on ANY mismatch
}

check_table2: // 0x081C12D0, identical but pointer 0x03002508, table 0x08352C4C,
              // on success: *(u8*)0x030023C6 = 1; play_sound(2);
```

Consequences (all derived from the disassembly):
* The button masks are **active-high, edge-triggered** (`pressed`, not `held`): a key
  must be released between presses. Two buttons pressed in the same frame yield one
  combined mask and therefore fail.
* The credit-entry index is part of the code: the same press at the wrong entry resets
  the matcher. This is the reason the first four presses must land while entry 1 is
  displayed, the next two while entry 2 is displayed, and the last while entry 3 is
  displayed.
* The two matchers run in parallel, so table 2 is reachable on a retail controller.
* Success on table 1 toggles; success on table 2 only ever sets its flag to 1.

---

## 6. Tables

**Code table 1 — `0x08352C2C` (published code).** Record = `u8 required_credit_index,
u8 unused(0), u16 key_mask`:

| # | required index | mask | button |
|---|---|---|---|
| 0 | 1 | 0x0020 | Left |
| 1 | 1 | 0x0010 | Right |
| 2 | 1 | 0x0020 | Left |
| 3 | 1 | 0x0010 | Right |
| 4 | 2 | 0x0040 | Up |
| 5 | 2 | 0x0080 | Down |
| 6 | 3 | 0x0001 | A |
| 7 | — | 0x0000 | terminator |

Raw bytes: `01 00 20 00 | 01 00 10 00 | 01 00 20 00 | 01 00 10 00 |
02 00 40 00 | 02 00 80 00 | 03 00 01 00 | 00 00 00 00`.

**Code table 2 — `0x08352C4C` (NOT in any published list):**

| # | required index | mask | button |
|---|---|---|---|
| 0 | 1 | 0x0010 | Right |
| 1 | 1 | 0x0020 | Left |
| 2 | 1 | 0x0010 | Right |
| 3 | 1 | 0x0020 | Left |
| 4 | 2 | 0x0080 | Down |
| 5 | 2 | 0x0040 | Up |
| 6 | 3 | 0x0002 | B |
| 7 | — | 0x0000 | terminator |

Raw bytes: `01 00 10 00 | 01 00 20 00 | 01 00 10 00 | 01 00 20 00 |
02 00 80 00 | 02 00 40 00 | 03 00 02 00 | 00 00 00 00`.

**Button masks** (GBA KEYINPUT, active-high): A=0x001, B=0x002, Select=0x004,
Start=0x008, Right=0x010, Left=0x020, Up=0x040, Down=0x080, R=0x100, L=0x200.
Title-screen gate = `L|R|Select|Up = 0x344` held while Up is newly pressed.

**Other title/input special case (derived, not a published cheat):** at
`0x081C1340` the validator reads the low 4 bits of the key word; if `(keys & 0xF)==0xF`
(A+B+Select+Start held) it sets `0x030023B1 = 1` and plays sound 53 three times. No
published source documents this; it is a simultaneous press, not a sequence, and is
reported here for completeness rather than as a usable cheat.

**Credit text bank:** `0x08352D6C`–`0x083531CC`, NUL-separated ASCII role/name pairs
(`LEAD PROGRAMMER`, `STEVE CLARK`, `LEAD ARTIST`, `MARK JONES`, `PROGRAMMER`,
`JASON AUSTIN`, …). Entries 1/2/3 — the code windows — are exactly the first three
visible bubble sets: *LEAD PROGRAMMER / STEVE CLARK*, *LEAD ARTIST / MARK JONES*,
*PROGRAMMER / JASON AUSTIN*. This is why the code windows are the first three sets.

---

## 6b. Enumeration

**Space definition (button-code system, §0.2 equivalent).** There are two independent
code paths, each a 7-press sequence over a 9-button input alphabet
(`A,B,Select,Start,Right,Left,Up,Down,R,L`), with a 3-valued positional gate
(credit index ∈ {1,2,3}) and exact per-position masks. Each table holds exactly 7
records plus a u32 terminator; the validator compares pointer-to-terminator, so the
accepted space of each matcher is **exactly one sequence** — there are no unused
payload bits, wildcards, aliases or variable-length forms. Total accepted sequences
in the entire in-game system: **2** (the two tables). The title gate is one additional
4-button held-combination; §3 tests of the other three single-direction variants
(L+R+Select+Down / Left / Right) produced only the ordinary `OPTIONS` bar or gameplay,
never a hidden option — the gate's search space of 4 direction variants is closed.

**Complete enumeration of both accepted sequences** (table dump above):
1. `L,R,L,R / U,D / A` → toggles `0x030023C5` (published; 3rd party cheat indexes).
2. `R,L,R,L / D,U / B` → sets `0x030023C6 = 1` (**novel**, absent from 3rd party cheat indexes and every published list found in §3 web recon).

**Novel code minted and entered in-game:** `Right, Left, Right, Left` during the
`LEAD PROGRAMMER / STEVE CLARK` bubbles, `Down, Up` during `LEAD ARTIST / MARK JONES`,
`B` during `PROGRAMMER / JASON AUSTIN`. The three credit windows were located by
reading `0x03002520` live in mGBA's debugger: index 1 at ≈8.6–11.8 s, index 2 at
≈13.4–16.6 s, index 3 at ≈18.1–21.3 s after selecting `SHOW CREDITS` (debugger-paused
run), and the corresponding bubble text was confirmed visually
(`varD_credits.png`, `cred_*.png` montage). The published sequence and the novel
sequence were both driven at these measured indices (logs `SENT 1/2/3`), and the
table pointers `0x03002504`/`0x03002508` were read back to observe matcher progress.

**Bounds proven by rejection (derived + harness):**
* Wrong credit index: the first record requires `index == 1`; any press at index 0 or
  ≥4 fails `cmp r0,r1` at `0x081C1278` and resets the table pointer to
  `0x08352C2C` (`0x081C12C4`). The recorded index trace (0→1→2→3→4→…) shows the
  out-of-range values are real and reachable, so the matcher rejects them.
* Wrong mask: `cmp r0,fp` at `0x081C1284`; any other button resets the pointer. The
  mirrored table differs in **every** one of its seven positions, so entering the
  published sequence cannot accidentally satisfy table 2 and vice versa.
* Combined presses: because `fp` is the exact edge mask, two buttons in one frame
  produce a mask absent from both tables and are rejected.
* Terminator: the 8th record is 0; `cmp r0,#0` at `0x081C1298` is the only path to the
  flag write, so no shorter prefix can succeed.

**Negative-result bounds (no other system):** keyword scan of all `strings -t x -n 4`
output (115,774 lines) for `password|cheat|secret|unlock|debug|hidden|code|level select`
returned only `CONTINUE` at `0x215B21`; the only UI strings for hidden functionality are
the localized `SHOW CREDITS` labels at `0x212B49`+. A literal search for the published
code sequence and for 7-press key-mask tables in six encodings (standard/reversed
10-bit/raw-active-low/bit-index × bytes/u16/u32 × forward/reversed) found **only** the
two tables at `0x08352C2C`/`0x08352C4C` — the search space is bounded and the two
results are exhaustive for those encodings. All reachable shell screens were walked
(main title, game select, four game title screens, options, pause/`ARE YOU SURE?`,
high-score initials, credits), so the absence of a password screen is a statement about
the enumerated screens, not an untested guess.

---

## 7. Validation evidence

* **Observed (emulator):** title/game-select/options/credits/pause/high-score screens;
  `L+R+Select+Up` revealing `SHOW CREDITS` (`gate_after_screen.png`, `shot05_aftergate.png`);
  credit bubbles and their exact words (`cred_*.png`, `varD_credits.png`); credit-index
  progression 0→1→2→3→… (`0x03002520` reads); key-state word `0x00000010` while Right
  held; mGBA watchpoint hit on `0x04000130` from IWRAM `0x03005C64`; savestate `gbAs`
  chunks decompressed to 0x61000 bytes for RAM comparison.
* **Derived (disassembly):** the validator entry and both matchers at `0x081C1220`–
  `0x081C133C`; both code tables and their record format; the flag bytes and sound IDs;
  the credit windows gating; the IWRAM key-state struct layout; the credits init/tick/
  render functions; `0x030023C5` xrefs in all four game modules (cheat reaches gameplay).
* **Inferred (labelled):** that flag 1 corresponds to "infinite time / infinite
  continues" exactly as 3rd party cheat indexes state; the game's own credit wording and the sound
  1/27 pair strongly support this but the voice samples were not audible under
  `SDL_AUDIODRIVER=dummy`. The effect of flag 2 (`0x030023C6`) is **not** proven: its
  only other xref is `0x081C2FF8` in the shell; no visible change was captured after
  the mirrored sequence, so the novel code is delivered as *an accepted-by-the-validator
  sequence derived from the ROM*, with its end effect still an unknown.
* **Honest limitation (not claimed as success):** under the pty-attached mGBA debugger,
  driving either 7-press sequence at the measured credit indices did not leave flag
  `0x030023C5`/`0x030023C6` set when read back, and a clean non-debugger run of the
  published sequence still showed the Out Run timer counting 79→71. The validator and
  its exact accepted inputs are proven statically; the in-harness key-edge delivery
  (xdotool→SDL→IWRAM `pressed` word) is the unproven part of that experiment. It is
  reported as a harness/input-semantics gap, not as a ROM result. In particular, the
  guide's §16.2 warning applies: short xdotool taps plus debugger pauses can consume
  the one-frame `pressed` edge before the validator observes it.

---

## 8. Unknowns

1. End effect of flag 2 / sound 2 (novel table-2 sequence). Reachability of the
   sequence is proven; the resulting gameplay change is not.
2. Exact reason the in-harness key edges were not observed by the validator (input
   delivery vs. pause timing). A native GBA/controller run would settle it.
3. Whether the 1992-style stage/music data block at `0x214CFE` is unused cut content
   from an earlier build or a shared music-table holdover; it is not reachable from
   the four-game shell.
4. Voice sample names/IDs for sounds 1, 2 and 27 ("Congratulations", "Be careful!")
   were not extracted from the sound bank.

---

## 9. Tooling

* `file`, `md5sum`, `sha1sum`, `sha256sum`, Python `zlib`/`struct` for CRC32 and header.
* GNU `strings -t x -n 4`, `grep -iE`, `grep -abo`; Python `re` for bank dumps.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000` for ARM ranges;
  Capstone (`CS_MODE_THUMB`/ARM) for PC-relative literal and BL scans.
* mGBA 0.10.5 under Xvfb `:317` (`DISPLAY=:317`, `SDL_AUDIODRIVER=dummy`, `-3`),
  xdotool for input, scrot for frames, ImageMagick `convert`/`montage` for cropping.
* mGBA `-d` pty debugger driven through a FIFO daemon (`dbg_daemon.py`, `ram.py`):
  `r/1|r/4`, `x/1`, `w/1|w/4`, `b/a`, `watch`, `c`, `i`, `reset`; savestate `gbAs`
  zlib-chunk parsing for RAM snapshots (guide §16.13).

All screenshots and helper scripts were kept in `/tmp/segagallery/`; no ROM or
copyrighted assets are redistributed by this report.
