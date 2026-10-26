# Battle B-Daman (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Battle B-Daman/Battle B-Daman.gba` |
| Size | 8,388,608 bytes (8 MiB) |
| Header title | `BB-DAMAN` (8 chars + NUL padding) |
| Game code | `BDXE` (USA) |
| Maker code | `EB` |
| Version | `0x00` |
| MD5 | `2b6b408513302519fd0e3fa72a67444b` |
| SHA-1 | `7016e0667201c965b6ae78c114b6cc5cb5ec7ff7` |
| SHA-256 | `3545429459efb6ab54943ec074cbcad253a5642a0caa2a3c361f4f3d287a6229` |

Entry word at `0x00` is `0xEA00002E` (ARM branch to `0x080000C0`).
All 156 bytes of the Nintendo logo are present at `0x04`; a scan of the
whole image found exactly **one** logo/header (base `0x0`). This is a single
GBA image, not a multi-game pack.

**Patch note.** The header is not self-consistent:

* complement check (`0xBD`) stores `0x95`; recomputation over `0xA0..0xBC`
  gives `0x6B`;
* header checksum (`0xBE`) stores `0x0000`; recomputation gives `0x837F`.

A retail Nintendo header cannot fail both checks, and the checksum field is
exactly zero — the classic signature of a header patcher. The visible title
(`BB-DAMAN` rather than the full `BATTLE BDAMAN`) is consistent with the same
edit. Code, string banks and the Zero Code tables analysed below are intact
and internally consistent, so this does not affect the findings. The exact
hash above identifies the patched image; a clean dump would have a different
hash and a valid header.

## 2. Executive summary

Battle B-Daman's "Zero Code" feature is a **fixed 18-entry lookup table**, not
an algorithmic password:

* 18 NUL-terminated coded strings live back-to-back at `0x0838B398`, with an
  18-entry pointer table (`0x0838BC3C`, followed by a NULL word) immediately
  after the string bank. The strings are 10–14 symbols long.
* The shop-facing validator is at `0x08057940`. It copies the input buffer at
  `0x0203D0AC` through a 34-entry control-code expansion table, then compares
  it byte-for-byte against all 18 strings with a plain `strcmp`
  (`0x0805B3F4`). There is no checksum, no generator, and no second numeric
  format in this revision.
* On a match it writes a per-code "already entered" byte at
  `0x0203A8B1 + index`, loads the reward record pointer from
  `0x0834E07C + 4*index`, and sets the UI message to "Zero code accepted!"
  (internally "Loading complete.", slot `0x0838BD58`). A miss sets slot
  `0x0838BD4C` ("Zero code is incorrect."); a repeat sets slot `0x0838BD60`
  ("That Zero code has already been entered.").
* Rewards are small instruction lists of 16-bit `(type,value)` pairs:
  type 1 = B-Dabucks, type 2 = part ID, type 3 = armour-set/SPA set index,
  type 4 = special-attack id.
* **Every published list checked prints the first code as `B-DAMAN`. The ROM
  stores `GO B-DAMAN`.** `B-DAMAN` is rejected; `GO B-DAMAN` is accepted and
  grants 1000 B-Dabucks. `GO B-DAMAN` appears in no published list found
  (GameFAQs and ChapterCheats snippets, VGChartz, B-Daman Wiki/Fandom search),
  so it is a genuinely unpublished accepted code.

No button-code table and no reachable debug menu were found. The developer
debug strings `DEBUG1/2`, `DEBUG1/3`, `SAVECLEAR`, `DEBUG1/5` and the
scene-jump list (`WAZA`, `SINARIO`, `ADVCHRFACE`, `TOOLBOX`, `SHOP`, …) exist
at `0x0834F1A4` and are referenced only by a menu builder at `0x0805B740`;
there is no key-sequence reader for them and they are not reachable from the
retail UI (bounded negative, §6b).

## 3. How to reproduce

### 3.1 Emulator and inputs

```bash
Xvfb :177 -screen 0 1024x768x24 &
DISPLAY=:177 openbox &
export DISPLAY=:177 SDL_AUDIODRIVER=dummy
/usr/games/mgba -3 "Battle B-Daman.gba"     # 3x scale, 720x480 window
```

mGBA SDL default keymap used: `x`=A, `z`=B, `a`=L, `s`=R, `Return`=Start,
`BackSpace`=Select, arrows=D-pad, `Tab`=fast-forward, `Shift+F1..F10`=save
state, `F1..F10`=load state.

Text is typed-out; hold keys 100–300 ms. Menus need one key press per message.
Yes/No prompts default to **Yes**; story battles are retried while Yes is
chosen, and choosing **No** at "B-Dabattle again?" advances the story (the
rival's "Don't be a coward" line is the story continuation, not a lock).

### 3.2 Menu path walked

1. Boot → Atlus logo → "PUSH START" (`Return`).
2. Story tutorial (long dialogue; A advances) → practice Direct Hit Battle →
   "Practice again? Yes/No" (choose No).
3. Field at B-Daspace. Top bar: `MOVE / TOOLBOX / HINT` (TALK appears in
   towns). `MOVE` opens the destination list: `Enter shop / Cowtoon West /
   Cowtoon East / B-Center` (later entries appear as the story progresses).
4. `TOOLBOX` → `B-Daman / B-Danote / Save`; B-Danote tabs: Characters,
   B-Daman, Parts, Special Attack, Battle Records.
5. `Enter shop` in B-Daspace is the Cat Café interior (Mie); the room menu is
   a door list (`Leave shop` + interaction rows). The Parts Shop is a separate
   story-gated door.
6. Direct Hit Battle reached through the B-Center tournament. The battle HUD,
   timer, HP and B-Daspirit bars are visible; all screenshots below.
7. After the tournament, B-Center gains a `BATTLE` bar entry and its `TALK`
   list contains `CrossScar` and `Gramps` (the parts-shop owner). `Gramps`
   answers "B-Dabattle first, and then ask"; the scene returns to B-Daspace.
   The Parts Shop door itself was still not in any `MOVE` list at this point.

### 3.3 Validator test harness (exact reproduction)

The shop UI is behind the tournament chapter, so the ROM's own validator was
exercised in the running game with the GDB stub. The stock stub only listens on
TCP 2345; this machine has another listener there, so a `bind()` shim moves the
emulator's stub to 2346 (source in §9). No game code or ROM bytes are patched;
the test writes only the RAM input buffer and calls the existing function.

```bash
# build the port shim
gcc -shared -fPIC -o bindhack.so bindhack.c -ldl
DISPLAY=:177 SDL_AUDIODRIVER=dummy LD_PRELOAD=$PWD/bindhack.so \
  /usr/games/mgba -g -3 -t game.ss2 game.gba &
gdb-multiarch -q -x valtests.txt        # target remote :2346
```

The harness installs a 4-instruction ARM stub in EWRAM at `0x0203F800`:

```
ldr r1,[pc,#4] ; bx r1 ; nop ; .word 0x08057941   ; enter Thumb validator
```

with `LR = 0x0203F810`, where a second stub returns to the interrupted PC. For
each test it clears `0x0203A8B1..C2`, writes the encoded string to
`0x0203D0AC`, calls `0x08057940`, stops on return, and reads the flag byte,
`0x0203D12C` (message slot) and `0x0203D128` (reward record).

Observed output (abridged):

```
=== TEST: GO B-DAMAN      flag0=1 flag1=0  msgsig=0838bd58 reward=0834df08
=== TEST: B-DAMAN         flag0=0 flag1=0  msgsig=0838bd4c reward=0834df08
=== TEST: WING NINJA      flag0=0 flag1=1  msgsig=0838bd58 reward=0834df0e
=== TEST: WINGNINJA       flag0=0 flag1=0  msgsig=0838bd4c reward=0834df0e
=== TEST: ANCIENT SPIRIT  flag0=0 flag1=0  msgsig=0838bd58 reward=0834dfe6
=== TEST: GO B-DAMAN X    flag0=0 flag1=0  msgsig=0838bd4c reward=0834dfe6
=== TEST: go b-daman      flag0=0 flag1=0  msgsig=0838bd4c reward=0834dfe6
=== TEST: CATS LOVE FISH  flag0=0 flag1=0  msgsig=0838bd58 reward=0834e076
```

`msgsig=0838bd58` is the success slot ("Loading complete." → then "You got
…"), `0838bd4c` is "Zero code is incorrect.". `ANCIENT SPIRIT`/`CATS LOVE FISH`
successfully set their own flag bytes (indices 13 and 17), which the abbreviated
print did not show.

## 4. Address map

All ROM addresses are `0x08000000 + file_offset`.

| Item | ROM address | File offset |
|---|---|---|
| ARM entry / crt0 | `0x08000000` / `0x080000C0` | `0x0` / `0xC0` |
| Game text bank (custom encoding) | `0x0834F000`–`0x083Axxxx` | `0x34F000`– |
| Zero Code strings (18, NUL-terminated) | `0x0838B398` | `0x38B398` |
| Zero Code pointer table (20 slots, last two NULL) | `0x0838BC3C` | `0x38BC3C` |
| Reward record pointers (18) | `0x0834E07C` | `0x34E07C` |
| Reward records (variable `(u16 type,u16 val)` lists) | `0x0834DF08`…`0x0834E076` | `0x34DF08`… |
| Validator (shop) | `0x08057940` | — |
| Control-code expansion table (34 × `{pattern,replacement}`) | `0x0838BAD0` | `0x38BAD0` |
| `strcmp` used by validator | `0x0805B3F4` | — |
| Append-one-char helper | `0x0805B304` | — |
| Input buffer (canonical code text) | `0x0203D0AC` | EWRAM |
| Already-entered flags (18 bytes) | `0x0203A8B1`–`0x0203A8C2` | EWRAM |
| Reward-record pointer for current code | `0x0203D128` | EWRAM |
| Message slot for current result | `0x0203D12C` | EWRAM |
| Message slots | `0x0838BD44` accepted / `0x0838BD4C` incorrect / `0x0838BD58` loading / `0x0838BD60` already | `0x38BD44`… |
| On-screen keyboard layout (6 rows × 16) | `0x0838B0D0` | `0x38B0D0` |
| Keyboard/text-entry init | `0x08051C58` | — |
| Keyboard/text-entry update | `0x08051D18` | — |
| Debug/scene menu text list | `0x0834F1A4` | `0x34F1A4` |
| Debug/scene menu builder | `0x0805B740` | — |

### 4.1 Text encoding

The game does not use ASCII for UI text. Decoded character table:

| Code | Meaning |
|---:|---|
| `0x00` | end of message |
| `0x0A`/`0x0B`/`0x0C` | line break / control |
| `0x10` | space |
| `0x11`–`0x2A` | `A`–`Z` |
| `0x2B`–`0x44` | `a`–`z` |
| `0x45`–`0x4E` | `0`–`9` |
| `0x4F` | `?` |
| `0x50` | `/` |
| `0x51` | `-` |
| `0x52` | `.` |
| `0x53` | `'` |
| `0x54` | `,` |
| `0x55` | `:` |
| `0x56` | `!` |

This is why `strings` finds no `PASSWORD`, `ZERO`, `CODE` or menu words
anywhere in the 8 MiB: the ASCII keyword scan is a **bounded negative** for
this encoding, not evidence of absence. Decoding the whole ROM with this table
produced the full script, including "Enter Zero Code", "Zero Codes",
"Zero code accepted!", "Zero code is incorrect.", "That Zero code has already
been entered." and all 18 passwords.

## 5. Algorithm

### 5.1 Validator

```
validate(input /* NUL-terminated encoded text at 0x0203D0AC */):
    canon = ""
    p = input
    while *p != 0:
        for i in 0..33:                      # table at 0x0838BAD0
            if strncmp(p, pat[i], 1) == 0:
                append_char(canon, repl[i])  # 0x0805B304
                break
        if i == 34: append_char(canon, p)    # identity fallback
        p += char_len(*p)                    # 1 byte, or 2 for control codes

    for idx in 0..17:
        if strcmp(canon, codes[idx]) == 0:   # 0x0805B3F4, exact bytes
            break

    if idx <= 17:
        if already[idx] != 0:
            message = SLOT_ALREADY            # 0x0838BD60
            return "already entered"
        already[idx] = 1                     # 0x0203A8B1 + idx
        current_reward = reward_ptr[idx]     # 0x0834E07C + 4*idx
        message = SLOT_ACCEPTED              # 0x0838BD58
        return "accepted"
    else:
        message = SLOT_INCORRECT              # 0x0838BD4C
        return "incorrect"
```

The `strcmp` is a plain byte loop; there is no case folding, whitespace
trimming, prefix matching, checksum or numeric decode. The prior
"control-code expansion" pass only rewrites text-control bytes that the
on-screen keyboard does not produce for codes; it does not create aliases
among letters.

### 5.2 Reward records

Each record is a NUL-terminated list of 4-byte entries
`{u16 type, u16 value}`:

* `type 1` — add `value` B-Dabucks;
* `type 2` — grant part ID `value`;
* `type 3` — apply armour/set/SPA set index `value`;
* `type 4` — grant special-attack ID `value`.

The shop displays "You got …" using the same record list; if the player already
owns the part the text "loaded but sold for …" is used.

## 6. Tables

### 6.1 The 18 codes and rewards (ROM order)

| # | Code (ROM, exact) | Reward |
|---:|---|---|
| 0 | `GO B-DAMAN` | 1000 B-Dabucks |
| 1 | `WING NINJA` | 2000 B-Dabucks |
| 2 | `B-DAFIRING` | 3000 B-Dabucks |
| 3 | `HOT FLAMES` | parts 132, 195, 373, SPA 374 |
| 4 | `BIG BARREL` | part 410 |
| 5 | `STEEL BOOT` | part 232 |
| 6 | `A CHICKEN!` | part 281 |
| 7 | `EDGE OF FIRE` | parts 397, 396, 162, 225, 119, 182, 398, set/SPA 29 |
| 8 | `GUST OF WIND` | parts 424, 425, 423, 168, 231, 426, set/SPA 32 |
| 9 | `THE ORIGINAL` | parts 404, 402, 403, 165, 228, 164, 227, 405, set/SPA 4 |
| 10 | `WILD HOWLING` | part 340 |
| 11 | `HIDDEN SWORD` | parts 308, 307, 140, 203, 139, 202, 309, set/SPA 1 |
| 12 | `FROM THE SEA` | parts 235, 236, 107, 170, 237, set/SPA 9 |
| 13 | `ANCIENT SPIRIT` | parts 317, 318, 314, 143, 206, 142, 205, 316, 315, set/SPA 19 |
| 14 | `GREEN ILLUSION` | parts 242, 244, 241, 111, 174, 110, 173, 243, set/SPA 13 |
| 15 | `THUNDER DRAGON` | parts 286, 362, 128, 191, 127, 190, 285, set/SPA 6 |
| 16 | `DARK WINDSTORM` | parts 312, 361, 141, 204, 311, 310, set/SPA 6 |
| 17 | `CATS LOVE FISH` | part 359 |

Published lists split the same 18 records into Bronze (0–6), Silver (7–11)
and Gold (12–17). The ROM's validator does **not** test the pass tier: it only
checks the per-code "already entered" byte. The tier is likely a shop-opening
or list-visibility flag; this was not proven (see §8).

### 6.2 Published-list correction

All fetched published tables (GameFAQs snippet, ChapterCheats Bronze page,
VGChartz, B-Daman Wiki/Fandom search results) print the 1000-B-Dabuck code as
`B-DAMAN`. The ROM string is `GO B-DAMAN` (encoded bytes
`17 1F 10 12 51 14 11 1D 11 1E 00`). The validator accepts only the latter;
`B-DAMAN` and `B-DAMAN` with any padding are rejected.

## 6b. Enumeration

**Space definition.**

* Accepted set: exactly **18** strings, fixed in ROM; NUL-terminated,
  10–14 symbols. Representable accepted values = 18.
* Input alphabet on the text-entry keyboard: 6 rows × 16 columns = 96 cells
  minus blanks/END, containing `A`–`Z`, `a`–`z`, `0`–`9` and punctuation
  (`-`, `'`, `"` ` `, `.`, `,`, `:`, `;`, `!`, `?`, `@`, `<`, `=`, `>`, plus
  quoted marks). Codes actually use only `A`–`Z`, `0`–`9`, space and `-`.
* Length: the validator imposes no length of its own; it compares until NUL.
  The string table's length range is 10–14. The entry screen has a maximum at
  `struct+0x33` (initialised to 0x14 = 20 at `0x08051B98`) and reserves
  row 6, columns > 12 for `Return`/`END`.
* There is **no checksum and no generator**: the space is a lookup, so the
  number of accepted inputs is 18, not a power of two.

**Unpublished code generated and accepted.**

`GO B-DAMAN` (index 0). It is the ROM's first record, is not printed by any
published list checked (they print `B-DAMAN`), and was accepted by the ROM's
own validator in the running game:

* `0x0203A8B1` (already-entered flag 0) changed `0 → 1`;
* `0x0203D128` became `0x0834DF08`, the record `{type 1, value 1000}`;
* `0x0203D12C` became slot `0x0838BD58` (success/loading slot).

**Bounds proven by rejection (same harness, same input buffer).**

| Input | Result | Evidence |
|---|---|---|
| `B-DAMAN` (the published spelling) | rejected | flag0 stayed 0; message slot `0x0838BD4C` |
| `WINGNINJA` (space removed) | rejected | flag1 stayed 0; slot `0x0838BD4C` |
| `GO B-DAMAN X` (15 symbols, over-long/extra field) | rejected | flag0 stayed 0; slot `0x0838BD4C` |
| `go b-daman` (lower-case) | rejected | flag0 stayed 0; slot `0x0838BD4C` |
| `ANCIENT SPIRIT` (14-symbol boundary, valid) | accepted | flag13 set; reward `0x0834DFE6` |
| `CATS LOVE FISH` (14-symbol boundary, valid) | accepted | flag17 set; reward `0x0834E076` |

Re-entry bound: after a successful call the corresponding flag byte is non-zero
and the validator's repeat branch selects `0x0838BD60` ("That Zero code has
already been entered."); clearing the flag restores acceptance, which proves
the byte is the only gate.

**Negative results, bounded.**

* ASCII keyword search over all 8 MiB (`strings`, `grep -abo`) for
  `password|cheat|debug|secret|unlock|code|menu|start|option` returned zero
  true hits because the text encoding is custom; after decoding the whole ROM
  with the table in §4.1, the only code-related strings are the Zero Code ones
  listed above.
* Button-code search: the keypad is read only in `0x08004428` (two literals
  `0x04000130`); the edge/pressed state is written to `0x02039C60/62/64/66/68`
  and those addresses are referenced only by the input routine and data
  pools (6 references to the edge word, all in `0x080044xx`/`0x0800ACBxx`
  pools). There is no compare-against-sequence loop; the Konami sequence as
  both held and active-low masks is absent. No button cheat exists in this
  revision.
* Debug menu: the labels exist, but the only builder is `0x0805B740` and its
  descriptor table (`0x08CC7C0`…) is not referenced by any code pointer found
  (searches for `0x08CC7C0`, `0x08CC800`, `0x08CC81C`, `0x08CC848` returned
  no ROM/code xref). It is dead developer data, not reachable from the retail
  UI.

## 7. Validation evidence

**Observed (emulator, screenshots and memory reads).**

* Boot, title, tutorial, field menus, Toolbox, B-Danote, shop door,
  tournament battle HUD and story scenes were walked and captured:
  `shot0/boot.png` (title), `menu_now.png` (intro), `battle2.png` (tutorial),
  `s2.png` (field bar), `toolbox1.png`, `bdanote1.png`, `shop_up2.png`
  (shop door), `vb1.png` (DHB HUD), `postsave2.png` (post-tournament),
  `postmenu.png` (`MOVE`: Enter shop / Cowtoon West / Cowtoon East / B-Center).
* The validator call results in §3.3 were read from live EWRAM at
  `0x0203A8B1`, `0x0203D128`, `0x0203D12C`, with the input string at
  `0x0203D0AC` exactly as the shop would leave it.
* The reward record bytes at `0x0834DF08` etc. were dumped from the ROM and
  match the type/value model above.

**Derived (disassembly).**

* `0x08057940` loop over 18 pointers at `0x0838BC3C`, `strcmp` at
  `0x0805B3F4`, flag array at `0x0203A8B1`, reward pointer at `0x0834E07C`.
* Control-code expansion table `0x0838BAD0` (34 entries, 8 bytes each) and the
  append helper `0x0805B304`.
* Text-entry screen `0x08051C58`/`0x08051D18` and keyboard map
  `0x0838B0D0`; row/column state at `0x0203D0CC+0x32..0x38`, max 20 at
  `+0x33`, submit at row 6 / col > 12.

**Inferred.**

* The in-game flow is shop menu → "Zero Code" text-entry screen →
  `0x08057940`. The screen init/update functions and the validator are
  consistent with that flow, but the shop door itself was not reached in this
  session because it is gated behind the tournament chapter.
* Pass tier (Bronze/Silver/Gold) is not checked by the validator; it most
  likely gates the shop's list/UI rather than the match itself.

## 8. Unknowns

* The Zero Code text-entry screen was not reached through the retail UI in
  this run (the Parts Shop is story-gated behind the B-Center tournament
  chapter). The ROM's validator was tested directly instead; the on-screen
  "Zero code accepted!" message and the reward grant were not photographed
  in the shop frame.
* The exact UI gate that opens the Parts Shop door (flag/address) was not
  isolated. The location table at `0x08351E9C` has "Parts Shop" entries at
  indices 7, 12, 17 and 22, but the current map's door list did not include
  one before the chapter completed.
* The maximum on-screen input length (struct byte `+0x33` initialised to 20)
  and the `Return`/`END` cell accept logic were derived, not exercised.
* Whether `HOT FLAMES`' type-4 entry is a special attack or a set index is
  inferred from the record shape; the type-3/4 semantics are not proven by a
  grant observation.
* The header patch source is unknown (title shortening and checksum zeroing);
  it does not affect the code tables.

## 9. Tooling

Scripts and artifacts in `/tmp/opencode/bdaman`:

* `phase0.py` — hashes, header parse, Nintendo-logo scan, complement and
  header-checksum recomputation.
* `decode.py` / `dumpstr.py` / `textscan.py` — custom text-encoding decoder,
  string-bank dumper, full-ROM decode and keyword search.
* `key.py` — Xvfb/mGBA focus, key hold helper, cropped screenshots.
* `thumbdis.py` — Capstone Thumb disassembler for arbitrary ROM ranges.
* `gdbcmd1.txt`, `gdsnap*.txt` — RAM dumps.
* `bindhack.c` / `bindhack.so` — `bind()` shim moving mGBA's GDB stub from
  2345 to 2346 (2345 is occupied on the shared host); compiled with
  `gcc -shared -fPIC -o bindhack.so bindhack.c -ldl`.
* `callval3.txt` / `valtests.txt` — ARM stub + validator invocation, with
  acceptance/rejection test matrix and EWRAM reads.

Installed/used: mGBA 0.10.5 (`mgba-sdl`), Xvfb, openbox, xdotool, scrot,
ImageMagick, `gdb-multiarch`, `arm-none-eabi-objdump`, Capstone 5.0.7,
Python 3.13.

Legal note: this report contains addresses, algorithms and hashes only; no ROM
image, graphics, music or text assets are redistributed. Screenshots are
emulator captures used as evidence and are not committed to the repository.
