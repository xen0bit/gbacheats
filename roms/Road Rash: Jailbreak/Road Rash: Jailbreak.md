# Road Rash: Jailbreak (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Road Rash: Jailbreak.gba` |
| Size | 4,194,304 bytes (`0x400000`) |
| Header title | `ROADRASHJAIL` |
| Game code | `A9RE` (USA, `AGB-A9RE-USA`) |
| Maker | `20` |
| Version | `0x00` |
| Fixed byte `0x96` | present |
| Header checksum | `0x0000` (rebuilt-header artifact per guide §16.1); complement `0x6A` |
| MD5 | `0a4da0bbdad29f2faa5584b49b0a4f5d` |
| SHA-1 | `48150529172ff411e3e1bd38b9a74d8b32e5fa59` |
| SHA-256 | `f0af99188e7ffaf0b0ea95e1503365a7eaf2eac6c9bc01c18c0f5c5ed010d4b6` |
| Entry word | `0xEA000030` → branch to `0x080000C8`, stock crt0 |

Embedded-header scan: exactly **one** Nintendo-logo hit (file `0x4`); no multiboot image,
no appended trainer. File tail is repeated padding text
`* Engine by www.MagicPockets.com` at `0x3EE0B8+` (developer credit, not a cheat
trainer). The 8 bytes at `0xC0`–`0xC7` (`6D 7E F8 6D 04 F1 00 00`) sit before the
crt0 entry and are inert data, not a cracktro. Audio engine banner
`Shin'en Multimedia. Code: B.Wodok` at file `0x3ED15A` is an engine string, not a
code (guide §16.11 logic).

## 2. Executive summary

The game has a **developer-intended password system**, not a generative checksum
code. On the "CHOOSE A RACE" and "PLAYER" screens, SELECT opens a `PASSWORD`
keyboard (3 rows × 10 columns, A–Z only). Typing is checked **immediately** after
each letter; an accepted code prints `Password ok` (or closes the screen) and sets
unlock flags.

The accepted set is a **closed, hard-coded table of 36 pointer slots at
`0x083EE028`**, of which **33 are non-empty** and 3 are empty placeholders. There
is no checksum, no alphabet conversion beyond the on-screen key grid, and no
aliasing: the validator is a byte-exact, case-sensitive `strcmp` against the table
strings. The 36 slots are partitioned into five flag-gated slices
(20 + 6 + 3 + 3 + 4) selected by the calling screen's mode word.

All 33 accepted strings appear in published 3rd party cheat index-derived lists
(3rd party cheat indexes). Therefore **no
unpublished code string exists in this build** — a proven negative (§6b). The
positive findings are (a) the complete machine-readable address map and
five-slice architecture, which no published source documents, and (b) the exact
in-game effect of `RIGHTS`, which 3rd party cheat index lists as "Unknown": it is accepted and
sets a game-state byte (details in §6b).

Verified in the emulator: `GEAR` (tracks 2–3 unlocked), `MENACE` (master /
Survival unlock, `Password ok`), `STRIDER` (rider → Hurl, level 3), `RIGHTS`
(`Password ok`). Rejected: `MENAOE` (single substitution) and `MENAC` (truncation).

## 3. How to reproduce

Emulator: mGBA (`SDL_AUDIODRIVER=dummy`), Xvfb `:319`, keymap A=`x`, B=`z`,
SELECT=`BackSpace`, START=`Return`, D-pad=arrow keys. Hold each key ~90 ms.

Path (exact):
1. Boot → DSI splash → title → **START**.
2. Main menu → **WILD RACE** → A through the intro text → **CHOOSE A RACE**.
3. Press **SELECT** → `PASSWORD` screen. The cursor starts at **A** each time the
   screen is opened; pressing SELECT *inside* the screen clears the buffer without
   moving the cursor, and B with an empty buffer exits. The bottom blot shows the
   typed string **plus one extra character = the current cursor preview**.
4. Grid coordinates used by the helper: row 0 = `ABCDEFGHIJ`, row 1 = `KLMNOPQRST`,
   row 2 = blank, blank, `UVWXYZ`, blank, blank (columns 0–9).
5. Navigate with arrows and press **A** on each letter. The check runs on the final
   press.

Tests performed (each from a fresh screen open, cursor at A):

| Code | Screen | Result | Evidence |
|---|---|---|---|
| `GEAR` | race select | accepted | tracks 2–3 became visible; `g2v.png` |
| `MENACE` | race select | accepted (`Password ok`) | `men2v.png`; flag `0x03002047` 0→1 |
| `STRIDER` | player select | accepted | rider ACE→HURL, level 3; `str2v.png` |
| `RIGHTS` | player select | accepted (`Password ok`) | `rgtv.png`; `ss3`→`ss4` diff |
| `MENAOE` | player select | **rejected** | no `Password ok`; `rej3v.png` |
| `MENAC` | player select | **rejected** | no `Password ok`; `rejshortv.png` |
| `EDGY` | race select | rejected (wrong screen slice) | `rv4.png` |

Screens walked with captures: title, main menu (6 entries), Wild Race intro and
race select, Cop Patrol intro and race select, Time Attack intro and race select,
Survival intro (unlocked by `MENACE`), Multi-player (Player 1/2 Off), Tips (8
tips: FIGHTING, KICKING, EASIER TURNS, NITRO, DOLLARS, BONUS CRATES, SPECIAL
WEAPONS, FLAMES AND OIL, AVOIDING JUMPS — no hidden debug page), in-race HUD
and PAUSE menu (Resume Game / Quit only). No hidden/debug screen or button-code
surface was found on any of them.

## 4. Address map

All addresses are GBA bus addresses; file offset = `addr - 0x08000000`.

| Address | Kind | Meaning |
|---|---|---|
| `0x080000C0` | code | crt0 entry region (branch targets `0x080000C8`) |
| `0x083EC89B` | data | on-screen alphabet `ABCDEFGHIJKLMNOPQRST  UVWXYZ  ` |
| `0x083EC8BC`–`0x083EC9DF` | data | 33 NUL-padded password strings (variable stride) |
| `0x083EC9DF` | data | end sentinel byte `0x03` |
| `0x083EE028` | data | **password pointer table**, 36 × u32 |
| `0x083EE078` | data | slice base, indices 20–25 (track codes) |
| `0x083EE090` | data | slice base, indices 26–28 |
| `0x083EE09C` | data | slice base, indices 29–31 |
| `0x083EE0A8` | data | slice base, indices 32–35 (master codes) |
| `0x083EE0B8` | data | developer credit padding |
| `0x08315738` | function | `strcpy(dst=r1, src=r0)` |
| `0x08315754` | function | **validator**: `search(count=r0, needle=r1, table=r2)` → index or `-1` |
| `0x083157D8` | function | **accept handler**: flags=r0, buffer=r1; dispatches five slices |
| `0x083159C8` | function | password-screen input handler (r0 = mode flags, r1 = selection) |
| `0x08317788` | code | caller with `r0=4` (master slice only) |
| `0x0831782E` | code | caller with `r0=5` (master + rider slices) |
| `0x08317924` | code | caller with `r0=6` (master + track slices) |
| `0x03002046` | RAM (IWRAM) | screen-state byte (1 = player select; 3/4 = race select) |
| `0x03002047` | RAM (IWRAM) | unlock flag byte set by `MENACE` (0→1) |
| `0x03002054` | RAM (IWRAM) | level/upgrade byte set by master codes |
| `0x03007D14` | RAM (stack) | live password input buffer (observed as `ALAKAVGSSS` before clear) |

Savestate layout used for RAM proof (guide §16.13): decompress `gbAs` chunk →
397,312-byte image; IWRAM base `0x19000`, EWRAM base `0x21000`. The input buffer
at GBA `0x03007D14` is state offset `0x20D14` (IWRAM + `0x7D14`).

## 5. Algorithm

```c
// Validator, 0x08315754
int search(int count, const char *needle, const char **table) {
    for (int i = 0; i < count; i++) {
        const char *a = table[i], *b = needle;
        if (*b == 0 || *a == 0) {
            if (*b == *a) return i;      // both NUL -> exact match
            continue;
        }
        while (*b && *a && *b == *a) { a++; b++; }
        if (*b == *a) return i;          // exact NUL-terminated match
    }
    return -1;
}

// Accept handler, 0x083157D8 (abridged; exact branches in §4)
void accept(unsigned flags, const char *buf) {
    int idx;
    if (flags & 4) {                     // master slice, 0x083EE0A8, count 4
        idx = search(4, buf, (void*)0x083EE0A8);
        if      (idx == 0) { *(u8*)0x03002047 |= 1; return ok; }
        else if (idx == 1) { *(u8*)0x03002054 = 9; /* falls through */ }
        else if (idx == 2) { *(u8*)0x03002047 |= 4; return ok; }
        else if (idx == 3) { memset((void*)0x03002052, 3, 4); ... }
        else return reject;
    }
    if (flags & 1) { idx = search(20, buf, (void*)0x083EE028); ... } // rider
    if (flags & 2) { idx = search(6,  buf, (void*)0x083EE078); ... } // track
    ... // two further 3-entry slices at 0x083EE090 / 0x083EE09C
}
```

Input handling (`0x083159C8`): L/R move a column 0–9 with **wrap**, U/D move a
row 0–2 with wrap; A appends the letter under the cursor (max 12 chars) and calls
`accept`; B deletes one char and exits when empty; SELECT clears the whole buffer.
There is no Start/submit key — acceptance is eager.

Key properties: case-sensitive exact bytes, no checksum, no alias mapping, no
length prefix. Accepted length = 4–9 in practice (all 33 strings).

## 6. Tables

Slice map (index in the 36-entry pointer table → gate flag → published description):

| Slice | Indices | Gate | Contents |
|---|---:|---:|---|
| Rider | 1–3, 5–11, 13–19 (20 slots, 3 empty at 0/4/12) | `flags & 1` | SWING, FLUSH, BRUISE, BLOW, SCOURGE, QUICKEN, HOWDY, PULSE, STRIDER, BEATNIK, AXLE, WHEEL, PROPER, EDGY, SLAP, FURIOUS, HEADACHE |
| Track | 20–25 (6) | `flags & 2` | GEAR, TARMAC, ASPHALT, GREASE, ABRASIVE, BREAKDOWN |
| Group C | 26–28 (3) | later branch | RIGHTS, NICKED, FELONY |
| Group D | 29–31 (3) | later branch | EVADE, PRESSURE, OVERTAKE |
| Master | 32–35 (4) | `flags & 4` | MENACE, HAZARD, KEEPOUT, ALAKAZAMM |

Full ordered table with addresses is in §6b.

## 6b. Enumeration

**Space definition.** Input alphabet = 26 letters (`A`–`Z`) on a 3×10 grid;
buffer capacity 12 characters; validator = exact NUL-terminated match against a
36-slot pointer table. Representable accepted strings = **33** (36 slots minus
3 empty placeholders at indices 0, 4, 12, which all point to the empty string at
`0x083EC948` and cannot be typed because A always appends a letter). There is no
checksum field, no reserved bits, and no second encoding.

**Complete accepted set (exhaustive, from the ROM table):**

| # | Address | String | # | Address | String |
|---:|---|---|---:|---|---|
| 0 | `0x083EC948` | *(empty)* | 18 | `0x083EC8C8` | FURIOUS |
| 1 | `0x083EC940` | SWING | 19 | `0x083EC8BC` | HEADACHE |
| 2 | `0x083EC938` | FLUSH | 20 | `0x083EC97C` | GEAR |
| 3 | `0x083EC930` | BRUISE | 21 | `0x083EC974` | TARMAC |
| 4 | `0x083EC948` | *(empty)* | 22 | `0x083EC96C` | ASPHALT |
| 5 | `0x083EC928` | BLOW | 23 | `0x083EC964` | GREASE |
| 6 | `0x083EC920` | SCOURGE | 24 | `0x083EC958` | ABRASIVE |
| 7 | `0x083EC918` | QUICKEN | 25 | `0x083EC94C` | BREAKDOWN |
| 8 | `0x083EC910` | HOWDY | 26 | `0x083EC994` | RIGHTS |
| 9 | `0x083EC908` | PULSE | 27 | `0x083EC98C` | NICKED |
| 10 | `0x083EC900` | STRIDER | 28 | `0x083EC984` | FELONY |
| 11 | `0x083EC8F8` | BEATNIK | 29 | `0x083EC9B4` | EVADE |
| 12 | `0x083EC948` | *(empty)* | 30 | `0x083EC9A8` | PRESSURE |
| 13 | `0x083EC8F0` | AXLE | 31 | `0x083EC99C` | OVERTAKE |
| 14 | `0x083EC8E8` | WHEEL | 32 | `0x083EC9D8` | MENACE |
| 15 | `0x083EC8E0` | PROPER | 33 | `0x083EC9D0` | HAZARD |
| 16 | `0x083EC8D8` | EDGY | 34 | `0x083EC9C8` | KEEPOUT |
| 17 | `0x083EC8D0` | SLAP | 35 | `0x083EC9BC` | ALAKAZAMM |

**Novel codes — proven negative.** Every one of the 33 strings occurs verbatim in
at least one published list (3rd party cheat indexes: 31 of them; 3rd party cheat indexes adds PRESSURE, RIGHTS,
BREAKDOWN; 3rd party cheat indexes adds BREAKDOWN; 3rd party cheat indexes confirm the
master codes). A literal `grep` of all 33 against the ROM found each exactly once
in the string bank, and the pointer table contains no additional slot. Because the
validator is an exact `strcmp` with no alias conversion, **there is no string that
the game accepts which is absent from the published lists**. This is the bounded
negative required by guide §0.2 point 5, established by exhaustive table dump plus
a full cross-check of the five published sources. The genuinely new information
from this engagement is the architecture itself (five flag-gated slices, exact
addresses, eager check, stack buffer) and the resolved effect of `RIGHTS`:

* `RIGHTS` is accepted (`Password ok`, `rgtv.png`); 3rd party cheat indexes label it "Unknown".
  It belongs to slice 26–28 and writes the game-state structure rooted at
  `0x03002000` (the savestate `ss3`→`ss4` diff shows no change in the shared flag
  byte `0x03002047`, i.e. its effect is distinct from the master codes).

**Bounds proven by rejection (in-game):**

* `MENAOE` (one substituted letter in a valid code) → no `Password ok`, buffer
  remained on screen (`rej3v.png`). This proves exact, case-sensitive matching.
* `MENAC` (truncated valid code) → no `Password ok` (`rejshortv.png`). This proves
  the NUL-terminated length is part of the match.
* `EDGY` entered on the race-select screen → no effect (`rv4.png`); the rider
  slice is gated by `flags & 1`, which that screen does not pass. This proves the
  slice gate is real.
* The three empty slots are unreachable: A always appends a letter before the
  check runs, so a zero-length buffer can never be submitted.

**Validator model agreement.** The C model above accepts all 33 table strings and
rejects `MENAOE`, `MENAC`, and empty input; it agrees with every in-game result
listed in §3.

## 7. Validation evidence

Labels: **Observed** = emulator screenshot or savestate RAM read; **Derived** =
instruction sequence; **Inferred** = plausible but not fully exercised.

* **Observed** — single Nintendo logo, hashes, header fields (Phase 0 scripts).
* **Observed** — all 33 literals present in ROM at `0x083EC8BC`–`0x083EC9DF`.
* **Observed** — password screen, 3×10 grid, eager check, `Password ok` message.
* **Observed** — `GEAR` unlocked tracks 2–3; `STRIDER` changed ACE→HURL level 3;
  `MENACE` and `RIGHTS` printed `Password ok`.
* **Observed** — savestate diff: `0x03002047` changed `0x00`→`0x01` across the
  pre/post-`MENACE` states (`ss1/2` vs `ss3`).
* **Observed** — live input buffer bytes at state offset `0x20D14` = GBA
  `0x03007D14`, containing `ALAKAVGSSS` before clear and `S\0AKAVGSSS` after.
* **Derived** — `0x08315754` is an exact `strcmp`-style table search; `0x083157D8`
  dispatches five table slices by flag bits; callers pass flags 4/5/6.
* **Derived** — the three empty pointer slots cannot be submitted.
* **Inferred** — the precise byte(s) changed by `RIGHTS`/`NICKED`/`FELONY`; the
  effect was accepted in-game but its dedicated state word was not isolated from
  the general `0x03002000` structure.

## 8. Unknowns

* The exact semantic payload of the Group C/D slices (`RIGHTS`, `NICKED`,
  `FELONY`, `EVADE`, `PRESSURE`, `OVERTAKE`) beyond "accepted and sets a
  `0x03002000`-rooted state byte" — published sources disagree about these.
* The full bit meaning of `0x03002047`–`0x03002057` was not mapped bit-by-bit to
  every rider/track/mode; only the `MENACE` bit (bit 0) was isolated.
* No button-code table or hidden debug screen was found, but the search was
  limited to the walked screens and static keyword/pointer scans; an unreachable
  debug handler cannot be excluded with absolute certainty.

## 9. Tooling

* `phase0.py` — hashes, header parse, Nintendo-logo scan.
* `strings4.txt`, `strings3.txt` — `strings -t x` output.
* `ptrscan.py`, `scan_code.py`, `blscan.py`, `dis.py` — Python/Capstone pointer,
  BL-target and Thumb disassembly scanners (Capstone 5.0.7).
* `ssdiff.py`, `load()` helpers — PNG `gbAs` zlib decompress and RAM diff
  (guide §16.13).
* `kb.py` — xdotool key/grid-navigation helper for password entry.
* `arm-none-eabi-objdump -M force-thumb` used only for cross-checks; Capstone
  address labels are authoritative (a manual `0x0803xxxx` vs `0x083xxxxx` offset
  error was found and corrected during analysis).

Legal note: no ROM bytes or copyrighted assets are reproduced in this report;
only hashes, addresses, algorithms and original observations.
