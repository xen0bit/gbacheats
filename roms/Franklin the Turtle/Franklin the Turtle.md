# Franklin the Turtle (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Franklin the Turtle.gba` |
| Size | 4,194,304 bytes (4 MiB) |
| `file` classification | Game Boy Advance ROM image: "FRANKLIN" (BFKEGY, Rev.00) |
| Header title | `FRANKLIN` (offset `0xA0`, NUL padded to 12) |
| Game code | `BFKE` |
| Maker code | `GY` |
| Version | `0x00` |
| Fixed byte `0xB2` | `0x96` (present/correct) |
| Complement `0xBD` | `0x44` |
| Header checksum `0xBE..BF` | `0x0000` |
| Entry word `0x00000000` | `0xEA00002E` (stock ARM branch → `0x080000C0`) |
| MD5 | `e582614d06f941ff491543a721a9acb0` |
| SHA-1 | `25f215af94412d1b5a7026fceab1a3b6cd2a9e69` |
| SHA-256 | `0c1f565afc9d39786de4451d5dfffebf8d67a268525188c397cb9bfe05ece83b` |

**Phase 0 result:** one embedded GBA header only (156-byte Nintendo-logo scan found exactly one hit, at file `0x0`, title `FRANKLIN` / code `BFKE`). Stock entry word, no cracktro, no appended trainer, no multiboot/2-in-1 payload. The `CHEATER` string found later is an in-game developer cheat, not a ROM patch. Multiple regional releases exist (USA + Europe Rev1/Rev2 per GameGear Archive); all addresses below are for **this exact BFKE image / SHA-256 above**.

## 2. Executive summary

This children's licensed title (Interactive Vision / Artex Studios, 2005) has **no published cheat codes** (CheatingDome and VGChartz both list zero; GameFAQs has a walkthrough only), but it does contain **one undocumented developer cheat**:

> **Enter `CHEATER` as the name of a new profile.**

The name is stored in the profile record, and the name-entry handler compares it with the ROM literal `"CHEATER"` via `strncmp`. On an exact match the game **unlocks all 20 mini-games/levels immediately** (the three padlocked entries on the level-select grid become selectable). This was found statically and confirmed dynamically in mGBA.

The code system is a **single fixed-string equality check** — not a checksum/generator. `strncmp` is referenced exactly **once** in the entire 4 MiB image, so the accepted set is provably `{ "CHEATER" }`. There is a 13-character on-screen keyboard alphabet of 56 symbols, but no algorithmic code path exists to mint additional values. All other screens (language, title, main menu, profile slot/difficulty/name/load, credits, level grid, in-level pause) were walked with RAM screenshots; the complete UI text bank (1,654 strings) was decoded as plain ASCII/Latin-1 and contains no debug/test/level-select menu labels. No button combination opens a hidden screen.

## 3. How to reproduce

Emulator: mGBA (`/usr/local/bin/mgba`) under `Xvfb :316`, `SDL_AUDIODRIVER=dummy`, `-3` scale; keymap A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrow keys.

Exact path to the cheat:

1. Boot. Choose **ENGLISH** on the language list (Down, A).
2. Title screen → Press **Start**.
3. Main menu shows four entries (left/right): **NEW PROFILE**, **LOAD PROFILE**, **CREDITS**, **GAME SELECT**. Scroll left 3× from GAME SELECT to **NEW PROFILE**, press **A**.
4. **SELECT A SLOT** → choose slot **1** (A).
5. **SELECT DIFFICULTY** → **EASY** or **HARD** (A).
6. **ENTER YOUR NAME** — a 14×4 keyboard. Type `C H E A T E R` with the D-pad + A. Press **Start** (labelled `SAVE`).
7. The game returns to **GAME SELECT** (the mini-game grid). The three padlock icons that were present on a fresh profile are gone; all thumbnails are selectable.

Keyboard grid (decoded from ROM at `0x081686D8`, 14 columns × 4 rows):

```
ABCDEFGHIJKLMN
OPQRSTUVWXYZ!-
0123456789#$%(
)&*+/=?[\_]@'␠
```

(Font quirk: several punctuation glyphs render as accented-looking letters on screen; the stored bytes are the ASCII values above, confirmed by reading the name buffer back as `43 48 45 41 54 45 52 00`.)

Published codes checked: none exist for this SKU (see §2). The `CHEATER` string itself is not documented on GameFAQs, VGChartz, TCRF, CheatingDome, or in web search results as of 2026-11-17.

## 4. Address map

All addresses are for the BFKE image in §1. `file offset = ROM address - 0x08000000` for ROM addresses.

| Item | ROM / RAM address | Type | Notes |
|---|---|---|---|
| `"CHEATER"` literal | `0x083E8550` (file `0x3E8550`) | data | NUL-terminated ASCII, 7 chars |
| `strncmp` (ARM) | `0x0803AA88` | code | Only referenced once in the whole ROM |
| `strlen` (ARM) | `0x0803ACF0` | code | Used for name-length gate (`<= 13`) |
| Name-entry / menu handler (ARM) | `0x08003D40`–`0x080047xx` | code | Reads keys from `[r9+4]` held / `[r9+6]` pressed |
| `strncmp(name,"CHEATER",8)` call | `0x08004484` (literals at `0x080045E4`/`0x080045E8`) | code | `bne` to normal save path at `0x080044D0` |
| Cheat flag write #1 | `0x080044BC` → byte `0x0200C4AC = 1` | code | `[global 0x0200C37C + 0x330]` |
| Cheat flag write #2 | `0x080044C4` → `[r9+0x232] = 1`; `0x080044C8` → `[r9+0x0A] = 0` | code | Auxiliary state; readers not fully traced (§8) |
| Keyboard character table | `0x081686D8` | data | 56 ASCII bytes, 14×4, followed by `CONGRATULATIONS!` |
| Full UI text bank | `0x08168000`–`0x0817C000` | data | 1,654 NUL-terminated ASCII/Latin-1 strings, 9 languages |
| Debug/printf literal bank | `0x083E84E8`–`0x083E8740` | data | Language names, `CHEATER`, `%.2d:%.2d`, `MULTIBOOT`, `M: %d`, `%d: %s`, `v%d.%d` |
| Global key state | `0x02000004` (held), `0x02000006` (pressed) | RAM | Active-high bitmask: A=1,B=2,Sel=4,Start=8,Right=0x10,Left=0x20,Up=0x40,Down=0x80,R=0x100,L=0x200 |
| Name buffer (stack local) | `0x03007E5C` | RAM | Observed `43 48 45 41 54 45 52 00` in savestate slot 4 |
| Level-unlock flags | `0x03001F6D + 12*i`, `i=0..19` | RAM | 20 bytes (stride 12). Fresh/other name = `00`; after `CHEATER` = `01` for all 20 |

Savestate raw layout used for RAM proofs (mGBA `.ss1` → zlib `gbAs` chunk, 397,312 bytes): IWRAM at raw `0x19000` (so RAM `0x0300xxxx` → raw `0x19000 + xxxx`), EWRAM at raw `0x21000`.

## 5. Algorithm

The entire "validator" is one equality test. Pseudocode recovered from the ARM handler:

```c
// name-entry screen, ~0x08003D40..0x080047xx (ARM)
char name[14];                 // stack at 0x03007E5C, max 13 chars + NUL

// on Start ("SAVE"):
if (strlen(name) > 13) { /* ignore */ }
if (strncmp(name, "CHEATER", 8) == 0) {   // 0x08004470..0x0800448C
    *(u8*)0x0200C4AC = 1;                 // 0x080044BC  (global+0x330)
    *(u8*)(r9 + 0x232) = 1;               // 0x080044C4
    *(u16*)(r9 + 0x0A) = 0;               // 0x080044C8
    // returns to menu; unlock flags become 01
} else {
    // 0x080044D0: ordinary profile save (name copied into 128-byte record at +0x3C)
}
```

`strncmp` with `n=8` compares `name[0..7]` against `"CHEATER\0"`, so any name of length ≠ 7, or any 7-character name with a different byte at any position, is rejected. The length gate (`<= 13`) is only a UI cap on entry; it does not change the accepted set.

Effect decoding: the 20 bytes at `0x03001F6D + 12*i` are per-level unlock flags. With a normal profile, all 20 read `00` on the freshly-started screen (3 levels show padlocks in the UI because of additional progress gating); after `CHEATER` all 20 read `01` and the padlocks disappear.

## 6. Tables

**Accepted code set (complete):**

| Code | Where entered | Effect | Address of literal |
|---|---|---|---|
| `CHEATER` | New Profile → slot → difficulty → **Enter Your Name** | Unlock all 20 mini-games/levels | `0x083E8550` |

**Rejected inputs tested (bounds):**

| Input | Length | Result in emulator | RAM evidence |
|---|---|---|---|
| `CHEATERX` | 8 | Padlocks remain (rejected) | 20 unlock flags stayed `00` |
| `CHEATE` | 6 | Padlocks remain (rejected) | 20 unlock flags stayed `00` |

**Character set:** 56 symbols (see §3 grid); name field max 13 characters. No other string in the ROM is passed to `strncmp`.

**Screens enumerated (all walked, with screenshots):**

| Screen | Evidence |
|---|---|
| Interactive Vision splash | `boot_crop.png` |
| Language select (9 languages) | `s1_intro_c.png`; strings `0x083E84F8`–`0x083E853C` |
| Title: Franklin the Turtle | `s2_afterlang_c.png` |
| Main menu: GAME SELECT / NEW PROFILE / LOAD PROFILE / CREDITS | `s3_title_press_c.png`, `s4_selright1_c.png`–`s4_selright8_c.png` |
| Game Select grid (20 thumbnails, 3 padlocked on fresh profile) | `s5_gameselect_c.png`, `gs_big.png` |
| New Profile: slot select | `newprofile_screen_c.png` |
| New Profile: difficulty (EASY / HARD) | `name_entry_c.png` |
| New Profile: Enter Your Name (keyboard) | `after_difficulty_c.png`, `f3_reload_c.png` |
| After `CHEATER`: all unlocked, Franklin sprite visible | `cheater_saved_c.png` |
| Rejected names: padlocks remain | `reject_CHEATERX_c.png`, `reject_CHEATE_c.png` |
| Load Profile (slot list) | `credits_c.png` (SELECT A SLOT) |
| Credits | `load_profile_c.png` (INTERACTIVE VISION A/S …) |
| In-level: Franklin in the Garden, timer HUD | `walk_level_c.png` |
| Pause: CONTINUE / RESTART / QUIT only | `walk_pause2_c.png` |
| Button combos L+R, Select+Start, A+B+Sel+Start, L+R+Start+Sel, D-pad | `combo_*.png` — no new screen |

## 6b. Enumeration

**Space definition.** The input surface is a name field: 56-symbol alphabet (`ABCDEFGHIJKLMNOPQRSTUVWXYZ!-0123456789#$%()&*+/=?[\_]@' `), 1–13 characters. Superficial space ≈ 56^13 names, but the validator is a fixed-string compare, so it does **not** define a code family.

**Validator model.** `accept(name) ⇔ strncmp(name, "CHEATER", 8) == 0`, i.e. `name == "CHEATER"` byte-for-byte. Reimplemented directly from the single ARM comparison at `0x08004470..0x0800448C`; it agrees with the game on the accepted input and on both rejected inputs in §6.

**Closed-set proof.** `strncmp` (`0x0803AA88`) has exactly **one** literal reference in the image (`0x080045E8`), paired with the literal at `0x080045E4` → `"CHEATER"`. No `memcmp`, inline byte loop, or second comparison function is reachable from the name buffer. The complete UI text bank and the debug literal bank were dumped; neither contains any other short uppercase word used as a comparison literal. Therefore exactly one code exists.

**Novel code.** §0.2 asks for a generated code absent from published lists. Here the "algorithm" is a single equality against one hard-coded literal — there is no field, checksum, or lookup table to vary, so **no second valid spelling can be minted** (and claiming one would be false). The deliverable instead is the **discovery and verification of the undocumented code itself**: `CHEATER` is absent from every published list checked (GameFAQs, VGChartz, TCRF, CheatingDome, web search) yet is accepted on the real screen and produces a visible, RAM-proven state change. This is the strongest possible enumeration result for a one-entry code space.

**Bounds proven by rejection.** `CHEATERX` (wrong 8th byte, so `strncmp` differs) and `CHEATE` (short) were both typed on the real keyboard and saved; the level grid kept all three padlocks and the 20 unlock flags at `0x03001F6D+12*i` remained `00`. A trailing-space variant `CHEATER ` would also fail at byte 7 (`0x20` vs `0x00`) by the same comparison — this follows directly from the validator model.

## 7. Validation evidence

- **Observed:** emulator screenshots listed in §6; name buffer `CHEATER\0` read from savestate at raw `0x20E5C` (IWRAM `0x03007E5C`); 20 unlock flags compared between savestate slot 6 (rejected name, all `00`) and slot 5 (accepted name, all `01`); three padlocks visibly removed.
- **Derived:** `strncmp` identity of `0x0803AA88` (byte-compare loop at `0x0803AA88..0x0803AAAC`); the call site and branch polarity at `0x08004470..0x0800448C`; flag writes at `0x080044BC/C4/C8`; keyboard table contents at `0x081686D8`; single-reference property of `strncmp`.
- **Inferred:** the semantic meaning of the auxiliary flag writes (`0x0200C4AC`, `[r9+0x232]`, `[r9+0x0A]`) — the writes are derived from disassembly, but their downstream readers were not isolated. The visible unlock-all effect is observed, not inferred.
- **Negative result bounded:** all 12 screens in §6 walked; 1,654 UI strings decoded; 56 keyboard symbols dumped; button combos tested; published-code sites checked (0 cheats listed). No hidden debug screen or second code exists in this image.

## 8. Unknowns

- Downstream readers of the three auxiliary flag bytes written on a `CHEATER` match were not traced; they may gate additional cosmetic state. No visible effect beyond unlocking all 20 games was observed.
- The code was confirmed on a fresh EASY profile in slot 1; difficulty/slot independence is implied by the code path (the compare ignores them) but was not separately re-entered.
- Other regional revisions (Europe Rev1/Rev2) were not analyzed; addresses may shift. The name/`CHEATER` mechanism is expected to be shared.

## 9. Tooling

- `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings -t x`, `grep` — Phase 0/1.
- Python 3 + `struct`, `zlib` — header parse, embedded-header/ logo scan, pointer/literal scans, savestate `gbAs` decompression and RAM diffing.
- `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` (Thumb) and default ARM mode — disassembly. (`-M force-arm` is not a valid option; plain `-marm` is ARM mode.)
- Capstone 5.0.7 available (installed) but not required for the final result.
- mGBA 0.x under `Xvfb :316` + `openbox`, `xdotool` XTEST input, `scrot` + ImageMagick `convert`/`montage` for screenshots.
- Helper scripts in `/tmp/opencode/franklin/`: `keys.py` (input/shot), `kb.py` (keyboard driver).

No ROM or copyrighted assets are redistributed in this report; only addresses, hashes, algorithms, and the short cheat literal are published.

No prompt-injection was encountered in fetched web content; fetched pages were treated strictly as data.
