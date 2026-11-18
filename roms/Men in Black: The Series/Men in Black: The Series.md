# Men in Black: The Series (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Men in Black: The Series.gba` |
| Size | 4,194,304 bytes (0x400000, 4 MiB) |
| Header title | `MIBTHESERIES` |
| Game code | `AMIE` |
| Maker code | `4Z` |
| Version / complement / checksum | `0x00` / `0x23` / `0x0000` |
| Fixed byte 0xB2 | `0x96` (correct) |
| Entry word | `0xEA00002E` → `0x080000C0` (stock crt0, **not** patched) |
| Embedded GBA headers | Exactly one Nintendo-logo hit, at file `0x0`. No multiboot/trainer sub-image. |
| MD5 | `7a7d4faca339a80bf99e96df67c9ff24` |
| SHA-1 | `6815f0910c5020ce7f0198dcbcb6e607f92ffa97` |
| SHA-256 | `3c77e312487efbd58ceed19679c22cb9468ecfad1e5cdd8e429b25c92d0d67b7` |

Credits strings identify Crave Entertainment (publisher) and David A. Palmer Productions
(developer). The ROM is a normal licensed retail image; no patch/trainer was found.

## 2. Executive summary

The game has a **developer-intended in-game password system**. On the title screen,
`START GAME` leads to an `ENTER PASSWORD` screen with an 8-character on-screen keyboard.
The accepted set is **exactly nine 8-character strings** stored as two contiguous,
fixed-stride ROM tables — there is no checksum, PRNG, or algorithmic password generator.

* Input alphabet: **space + 21 consonants** `BCDFGHJKLMNPQRSTVWXYZ` (22 symbols).
  The UI skips vowels: `A` maps to space, and `E/I/O/U` are stepped over.
* Level table at `0x083441D6`: 6 entries (slot 0 = eight spaces = Episode 1;
  slots 1–5 = Episodes 2–6).
* Cheat table at `0x08344206`: 3 entries (invincibility / infinite ammo / all weapons).
* Validator: `FUN_08003AF8` at `0x08003AF8` performs two linear 8-byte `strcmp`-style
  scans (6 entries, then 3). A match writes the level index to `0x0300022C` or sets one
  of three flag bytes at `0x03005D58..5A`; a miss shows "Incorrect Password".

All eight nonblank codes agree with published GameFAQs/CheatCC/GameRevolution lists
(one site's `FCHTRMNS` is a typo for `FGHTRMNS`). GBC-only numeric codes (`0601`,
`2409`, `1943`, …) do **not** occur in this GBA image — different SKU (§16.11).

**Novel, unpublished findings (§0.2):**
1. The **blank eight-space password** is accepted and routes to Episode 1. Published
   lists say Episode 1 needs "no password", so this accepted input is absent from them.
   Verified in-game and by RAM (level byte `0x00`, briefing "ZED ISN'T TOO PLEASED").
2. **Cheats persist across level-code entry**: entering all three cheat codes followed
   by `NNTNDWNY` yields Episode 6 with flags `01 01 01` at `0x03005D58..5A`. No
   published list documents this combination.

No hidden debug menu was found in the searched spaces (complete ASCII text bank,
keyword sweep, 22-entry screen dispatch table, and all reachable menus).

## 3. How to reproduce

```bash
Xvfb :316 -screen 0 1024x768x24 &
DISPLAY=:316 openbox &
DISPLAY=:316 SDL_AUDIODRIVER=dummy mgba -3 "Men in Black: The Series.gba" &
```

mGBA SDL keymap used: `A`=`x`, `B`=`z`, `L`=`a`, `R`=`s`, `Start`=`Return`,
`Select`=`BackSpace`, D-pad = arrow keys. Hold keys ≥50 ms.

Menu path (all screens reached with RAM/screenshot evidence):

1. Legal scroll → title `MEN IN BLACK: THE SERIES` → `Return` (Start).
2. Main menu: `START GAME` / `OPTIONS` / `CREDITS`.
   * `OPTIONS`: `SOUND EFFECTS`, `MUSIC`, `LIVES`, `BACK` — exactly 4 rows; no hidden entry.
   * `CREDITS`: scrolling credits; ASCII credits bank at `0x33F0A0`.
3. `START GAME` → `A` → **`ENTER PASSWORD`** screen. Save state to slot 1 (`Shift+F1`);
   `F1` restores it for each experiment.
   * `Left`/`Right` select one of 8 character slots; `Up`/`Down` change the letter;
     `A` immediately confirms (no auto-advance). `Start` begins a new game.
4. Valid level code → briefing screen → gameplay (`Start` pauses: `Continue` /
   `Restart Level` / `Exit`, exactly 3 rows). Invalid code → black
   "Incorrect Password" screen (state `0x0A`).

Example code entry: for `FGHTRMNS`, set slots 0..7 via `Up` presses
(F=4, G=5, H=6, T=16, R=14, M=10, N=11, S=15 from blank), pressing `Right` between
slots, then `A`.

## 4. Address map

| Address (ROM / file) | Meaning | Evidence |
|---|---|---|
| `0x08003AF8` / `0x3AF8` | `FUN_08003AF8`: password-screen handler **and validator** (decompiled) | Derived (Ghidra) + observed |
| `0x08004218` / `0x4218` | literal → input buffer `0x03004C90` | Derived |
| `0x0800421C` / `0x421C` | literal → level table `0x083441D6` | Derived |
| `0x08004220` / `0x4220` | literal → cheat table `0x08344206` | Derived |
| `0x083441D6` / `0x3441D6` | level table, 6 × 8 bytes (slot 0 = 8 spaces) | Observed bytes |
| `0x08344206` / `0x344206` | cheat table, 3 × 8 bytes | Observed bytes |
| `0x080001D0` / `0x1D0` | main screen dispatcher: `handler = table[state]` | Derived |
| `0x0834A564` / `0x34A564` | screen-handler pointer table, 22 entries (Thumb bit set) | Derived |
| `0x344119`–`0x34421D` | UI text bank: `ON/OFF/OPTIONS/SOUND EFFECTS/MUSIC/LIVES/BACK/ENTER PASSWORD` + tables | Observed |
| `0x33F0A0`–`0x34A3xx` | credits + level story bank (ASCII, `@` = NUL terminator, `nn` = newline) | Observed |

| RAM address | Meaning | Observed values |
|---|---|---|
| `0x03004C90` | 8-byte password input buffer | `FGHTRMNS`, `        `, etc. |
| `0x0300022A` | screen-state byte (index into 22-handler table) | `0x09` password, `0x0A` reject, `0x0B` briefing |
| `0x0300022C` | level index (0..5) written by validator | `0x00` blank code, `0x01` FGHTRMNS, `0x05` NNTNDWNY |
| `0x03005D58` | invincibility flag (byte 0) | `0x01` after LVFRVRDD |
| `0x03005D59` | infinite-ammo flag (byte 1) | `0x01` after NFNTMMDD |
| `0x03005D5A` | all-weapons flag (byte 2) | `0x01` after LLWPNSDD |

## 5. Algorithm

Decompiled validator, precise enough to reimplement:

```c
// state: pressed A or Start on the ENTER PASSWORD screen
if ((keys & (START|A)) != 0) {
    // 1) level table: 6 exact 8-byte comparisons
    for (int i = 0; i < 6; i++)
        if (memcmp(input /*0x03004C90*/, levelTbl[i] /*0x083441D6+i*8*/, 8) == 0)
            break;
    if (i != 6) {
        level_byte(0x0300022C) = i;          // 0..5
        substate(0x03002??)  = 0; ... transition to briefing;
        return;
    }
    // 2) cheat table: 3 exact 8-byte comparisons
    for (int j = 0; j < 3; j++)
        if (memcmp(input, cheatTbl[j] /*0x08344206+j*8*/, 8) == 0)
            break;
    if (j == 3) {
        level_byte = 0;                       // reject
        show "Incorrect Password" (state 0x0A);
        return;
    }
    if      (j == 0) *(u32*)0x03005D58 = 1;   // invincibility
    else if (j == 1) *(u8*)0x03005D59 = 1;   // infinite ammo
    else if (j == 2) *(u8*)0x03005D5A = 1;   // all weapons
    // returns to the password screen, flags persist
}
```

Notes:

* Both loops compare exactly 8 bytes; there is no prefix/partial match.
* The level branch does **not** clear `0x03005D58`, which is why cheats survive a
  subsequent level code (novel combination, §6b).
* The input filter (letter cycler) maps `A`→space and decrements `E/I/O/U`, so the UI
  can only produce `space` + consonants — exactly the characters used by the nine
  stored strings. No case/glyph aliases exist because comparison is on raw ASCII bytes.

## 6. Tables

Accepted strings (ROM bytes, 8 chars each, no NUL — fixed stride):

| # | Table | Code | Effect | RAM proof |
|---|---|---|---|---|
| 0 | level | `        ` (8 spaces) | Episode 1, MIB Headquarters | `0x0300022C = 0x00` |
| 1 | level | `FGHTRMNS` | Episode 2, Forest Landing Site | `0x0300022C = 0x01` |
| 2 | level | `HSDSHSBS` | Episode 3, Alien Technology Lab | published + ROM literal |
| 3 | level | `MXNMSNNG` | Episode 4, Rocket Silo | published + ROM literal |
| 4 | level | `THXBXSCK` | Episode 5, MIB Safe House | published + ROM literal |
| 5 | level | `NNTNDWNY` | Episode 6, Halloween in Manhattan | `0x0300022C = 0x05` |
| 0 | cheat | `LVFRVRDD` | Invincibility | `0x03005D58 = 01 00 00 00` |
| 1 | cheat | `NFNTMMDD` | Infinite ammo | `0x03005D58 = 00 01 00 00` |
| 2 | cheat | `LLWPNSDD` | All weapons | `0x03005D58 = 00 00 01 00` |

Published-code verification: all eight nonblank literals are present verbatim in the
ROM at `0x3441DE` onward. `FCHTRMNS` (CheatCC, blogspot, Planet Cheats) is a typo;
the ROM and GameFAQs/GameRevolution use `FGHTRMNS`. The GameFAQs "View Ending"
effect attributed to `NFNTMMDD` was **not** reproduced (see §8).

## 6b. Enumeration

**Space definition.** Input length is fixed at 8 characters. Reachable alphabet is
22 symbols (space + `BCDFGHJKLMNPQRSTVWXYZ`), i.e. `22^8 = 54,875,817,216` possible
strings. There is no checksum or reserved bit: the validator is a direct comparison
against fixed table entries. **Accepted set size = 9** (6 level + 3 cheat), exactly the
table contents. This is a closed set; §16.9's "run the validator over the whole space"
reduces to proving the two loop bounds (6 and 3) from the decompiled validator, which
was done, plus in-game probes below.

**Novel / unadvertised accepted inputs generated and entered:**

1. **Blank password (`"        "`).** Not listed as a code anywhere (published guides
   say "none" for Episode 1). Entered by confirming the untouched keyboard; accepted →
   Episode 1 briefing "ZED ISN'T TOO PLEASED"; `0x0300022C = 0x00`, flags `000000`.
2. **Combined cheats + level code (unadvertised combination).** Entered in sequence:
   `LVFRVRDD` → `NFNTMMDD` → `LLWPNSDD` → `NNTNDWNY`. After each step RAM read:
   `01 00 00` → `01 01 00` → `01 01 01` → level byte `0x05` with flags still
   `01 01 01`. Result: Episode 6 ("HALLOWEEN IS ALWAYS A TOUGH TIME…") with all
   three cheats simultaneously active. No published list documents combining codes.

**Bounds proven by rejection** (each with `Incorrect Password` screenshot and
`state=0x0A, level=0x00, flags=000000`):

* `FGHTRMNB` — single-character substitution of a valid level code → rejected.
* `BBBBBBBB` — all-first-letter string → rejected.
* `FGHTRMN ` (7 chars + blank slot) — truncated valid code → rejected.

Vowels cannot be entered at all (UI alpha filter), which bounds the reachable space
to the 22-symbol alphabet rather than 26+ letters.

## 7. Validation evidence

* **Observed** (emulator + savestate RAM reads, display :316):
  every menu listed in §3; `FGHTRMNS` → `0x0300022C = 1` and Episode 2 briefing;
  blank password → level 0 and Zed briefing; each of the three cheat codes setting
  its distinct flag byte; the 3-cheat+level-6 combination; three rejected inputs with
  unchanged level/flags; pause menu with 3 entries and no reaction to `Select`;
  Credits screen; no ending after `NFNTMMDD` + `Start`.
* **Derived** (Ghidra decompilation + byte-level disassembly):
  validator structure, two scan bounds (6, 3), literal pointers at `0x4218/421C/4220`,
  flag writes, 22-handler dispatch table at `0x0834A564`, state byte `0x0300022A`.
* **Inferred**: that the GBC "Access Codes"/levitation/Noisy Cricket features described
  on GameFAQs belong to the Game Boy Color SKU — none of their numeric literals
  (`0601`, `2409`, `1943`, `0309`, `3107`, `2710`, `2705`, `1807`) occur in this ROM.

## 8. Unknowns

* The published "View Ending" effect of `NFNTMMDD` was not reproduced by entering the
  code and pressing Start; it may require completing the game with the flag set. Not
  proven either way.
* Screen state `0x14` (20) has special per-frame calls (`FUN_08001E44`,
  `FUN_08001DCC` — graphics/OAM updates) in the dispatcher; its exact in-game trigger
  was not isolated (likely a results/transition screen). It is within the 22-entry
  handler table and no debug label exists for it.
* No full playthrough was performed, so late-game screens (game over, level complete,
  ending movie) were not all visited. No hidden debug menu was found in the searched
  spaces; this is a bounded negative (ASCII text bank fully enumerated; keyword sweep
  found 0 hits for debug/cheat/unlock/level-select; 22 screen handlers inventoried).

## 9. Tooling

* `Xvfb :316`, `openbox`, `mgba -3` (SDL), `xdotool` XTEST input, `scrot`/ImageMagick.
* Savestate RAM reader: `ss.py` (zlib-decompresses mGBA's `gbAs` PNG chunk; IWRAM at
  raw offset `0x19000` for this 4 MiB ROM) — guide §16.13.
* Static: `strings -t x`, `grep -a`, `xxd`, Python `struct`/`capstone` scanners,
  `arm-none-eabi-objdump -M force-thumb`, REA/Ghidra 12.1.4 (`open_binary` raw-binary
  ARM @ `0x08000000`, `procedure_pseudo_code`, `resolve_containing_procedure`,
  `procedure_callers`).
* Web sources checked: GameFAQs, CheatCC, GameRevolution, GGmania, Planet Cheats,
  CheatHappens, gbadamud. Fetched content contained no prompt-injection payloads and
  was treated as data only.

**Legal note:** no ROM bytes, graphics, audio, or full game text are redistributed here;
only hashes, addresses, algorithms, and tool scripts are published.
