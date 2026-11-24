# Sega Rally Championship (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Sega Rally Championship/Sega Rally Championship.gba` |
| Size | 8,388,608 bytes (`0x800000`) |
| Header title | `SEGA RALLY` |
| Game code | `AYLE` (`AYLE8P`, Rev. 00) |
| Maker | `8P` (Sega) |
| Version byte / complement / checksum | `0x00` / `0xDA` / `0x0000` |
| Entry word | `0xEA00002E` → `b 0x080000C0` (stock crt0) |
| MD5 | `f4326bde4b5e9f53f5fc58ce24d7b137` |
| SHA-1 | `5ec86056ccef168b57be8e609aada2b1da11f733` |
| SHA-256 | `f1f5c54f4a6c509200121860b2aa0fa07e1a1d01e1cdb8a4232f12e7cf74ba46` |

**Phase 0 result:** one Nintendo logo / GBA header only (scan of all 156-byte logo matches found exactly one, at file `0x0`). No patch, cracktro, appended trainer or second image. The first 4 KiB is a normal ARM crt0 (`0x080000C0`: CPSR setup, stack pointers `0x03007F60`/`0x03007FA0`, `bx` into Thumb `0x0800027D`). Save memory is present (32 KiB `.sav` created on first boot).

## 2. Executive summary

**There is no in-game cheat-code system in this GBA build.** The only published codes for the SKU are eight *CodeBreaker* cheat-device codes (out of scope: they are memory patches, not developer-intended inputs). The GameFAQs "GBA cheats" page actually contains two *N-Gage* unlockables (Special Cup / World Cup obtained by finishing 1st), mislabeled under the GBA entry; there is no published GBA password, button code or debug menu.

Every reachable screen was walked with the emulator (title → name entry → single/multi → mode select → EXTRA/SHOP/RC RALLY/GALLERY → RECORDS → OPTIONS → CHAMPIONSHIP cup select → TIME ATTACK track/car select → race/pause), and all 40 name-entry input combinations of interest were bounded statically. The only user-input recogniser in the ROM is a *default-name canonicaliser* at `0x0802C50C`: it compares the 8-byte name to exactly two entries (`XXX`, `SEX`) of the 4-entry table at `0x0810860C` and rewrites the buffer to the canonical padded spelling. Its caller (`0x0802BD94`) **ignores the return value**, so no flag, unlock or cheat is driven by it.

The real progression surface is two ordinary save-state systems, not codes:

* A **cup unlock counter** at IWRAM `0x030005C4` (init `1`, max `5`) incremented after a championship win by `0x080155D2`; the 5 cup labels live at `0x081069A8` with 24-byte stride (Amateur, Sprint, National, World, Special). The published CodeBreaker "Access All Cups" code simply writes `5` to this byte.
* **RP-funded shop purchases**: RP counter at `0x03000604` (init `0`), extras flags at `0x030005B0/B2/B4`; SHOP has CUP ENTRY / COURSE / CAR / GALLERY categories, RC RALLY and GALLERY both show `NO ITEM` on a fresh save.

A button-mask table scan found **zero** button-code validators: 264 contiguous `u16` runs of single-key masks exist, only 11 have any pointer/LDR xref, and all 11 are UI control-configuration data or repetitive filler (details in §6b). Common debug combinations (`L+R+Start`, `L+R+A+B`, `Select+Start`, etc.) were pressed on the title screen and produced no new screen. §6b gives the counts that bound this negative result.

## 3. How to reproduce

Environment: mGBA 0.10.5 (`/usr/local/bin/mgba`), Xvfb `:318`, `SDL_AUDIODRIVER=dummy`, OpenBox window manager, `xdotool` XTEST input. Default SDL keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrow keys. Tap length 60–200 ms (150 ms+ double-steps some menus).

1. `Xvfb :318 -screen 0 1024x768x24 &` then `DISPLAY=:318 openbox &`.
2. `DISPLAY=:318 SDL_AUDIODRIVER=dummy mgba -3 "<rom>" &`; focus the `mGBA` window with `xdotool windowfocus`.
3. `Return` twice from the title → main menu (`SINGLE PLAY`/`MULTI PLAY`); `x` → MODE SELECT (`CHAMPIONSHIP`, `TIME ATTACK`, `EXTRA`, `RECORDS`, `OPTIONS`).
4. From MODE SELECT: Down×2+A → EXTRA (`SHOP`, `RC RALLY`, `GALLERY`, `EXIT`); Down×3+A → RECORDS; Down×4+A → OPTIONS (`GAME SETTINGS`, `BUTTON SETTINGS`, `SOUND SETTINGS`, `EXIT`).
5. Name entry: from the first `PRESS START` screen press `Return` (may need two presses) → `NAME ENTRY` splash → `x` → 40-cell keyboard (`0-9`, `A-Z`, `!`, `?`, `'`, `"` plus `DEL`/`END`). Cursor moves one cell per 60 ms tap; select with `x`. The 8-character name `SEX` was entered and submitted with END; no unlock, flag change or new screen followed.
6. RAM evidence was taken with mGBA savestates (`Shift+F1` save, `F1` load): `.ss1` PNG chunks contain a zlib `gbAs` payload of 397,312 bytes; IWRAM `0x03000000` maps to raw offset `0x19000`, EWRAM `0x02000000` to `0x21000`. The mGBA GDB stub (`-g`) was tried but `continue` fails with "Cannot execute this command while the target is running" in this build (guide §16.13), so savestate diffing was used instead.

## 4. Address map

| ROM address (file offset = addr − `0x08000000`) | Meaning | Evidence |
|---|---|---|
| `0x08000000`–`0x08000100` | ARM crt0 /IRQ vectors; `0x04000130` literal at `0x080006E8` | Derived (objdump) |
| `0x080006C0` | Input poll: `held = 0x3FF ^ KEYINPUT`; `pressed = held & ~old`; writes `0x0300122A`/`0x0300122C` | Derived |
| `0x080155D2`, `0x080155E0` | Writers of cup counter `[0x030005B0+0x14]` (`0x030005C4`) and secondary counter `[+0x15]` | Derived |
| `0x081068A0` | 11 track labels `result:<track>` at 24-byte stride (oval, snow, desert, mountain, metropolis, sandstorm, forest, jungle, isle, village, hillclimb) | Derived |
| `0x081069A8` | 5 cup labels `ranking:<cup> cup` at 24-byte stride (amateur, sprint, national, world, special) | Derived |
| `0x0810860C` | Default-name records: `XXX`, `SEX`, `AMB`, `SRC`, 10-byte stride (8 chars + 2 bytes) | Derived |
| `0x0802C50C` | Name canonicaliser: compares input to entries 0 and 1 only; copies canonical string back; returns 1/0 | Derived |
| `0x0802BD94` | Only BL caller of the canonicaliser; return value unused | Derived |
| `0x08333330`, `0x08333D8` | Two 96-byte font index→tile tables (row order reversed between them) | Derived |
| `0x084D3C08`+ | Text-bank block pointer table; each block `0x214` bytes of `u32` string offsets, 18-byte string slots | Derived |
| `0x084D3920` | Pointer to 12-mask `u16` button-config data at `0x08034C82` (A,B,R,L,R,L,A,B,Up,Down,A,B) — UI data, not a validator | Derived |
| IWRAM `0x030005B0` | Game-state struct base (extras flags at `+0x0/+0x2/+0x4`, cup counter at `+0x14`) | Observed + Derived |
| IWRAM `0x030005C4` | Cups available: `0x01` on fresh save; CodeBreaker "all cups" writes `0x05` | Observed |
| IWRAM `0x030005C6` | Current track index (used to index `0x081068A0` at `0x080248E4`) | Derived |
| IWRAM `0x03000604` | RP counter: `0x0000` on fresh save, matches HUD `0` | Observed |
| IWRAM `0x0300122A`/`0x0300122C` | Key held / key pressed (active-high bits `A=1,B=2,Select=4,Start=8,Right=0x10,Left=0x20,Up=0x40,Down=0x80,R=0x100,L=0x200`) | Derived |

## 5. Algorithm

No password/checksum validator exists. The two state systems are:

```
// championship completion (0x080155B2..0x08015600), Derived
if (flags & 0x10) or (flags & 0x100) or ((state[0x12] & 0xF)==0) return;
max = table[state[0x12] >> 2][0];          // per-mode max cups
cups = state[0x14];                          // 0x030005C4
cups++; state[0x14] = cups;
if (cups >= max) { state[0x14] = 0; state[0x15]++; if (state[0x15] > 2) state[0x15] = 0; }
set bit 0x400 of state[0x0E];                // save flag
...
```

```
// name canonicalisation (0x0802C50C), Derived
for i in 0..1:                               // ONLY entries 0 ("XXX") and 1 ("SEX")
    for j in 0..7:
        if input[j] != table0x0810860C[i*10+j]: goto next_i
    memcpy(input, &table[i*10], 8); return 1
return 0
// caller 0x0802BD94 discards r0 -> no cheat flag
```

Input decoding (for any future button-code work): `held = 0x3FF ^ *(u16*)0x04000130`, `pressed = held & ~old_held`; the code would compare against the active-high mask list above.

## 6. Tables

**Published GBA codes verified against the ROM (all CodeBreaker / cheat-device; OUT OF SCOPE for this report):**

| Effect | Code | RAM address | Verified in RAM |
|---|---|---|---|
| Enable code | `0000963F 000A / 10005E00 0007` | — | not applied (device code) |
| Always Win Championship | `33002A4B 0001` | `0x03002A4B` | byte exists in IWRAM range |
| Infinite Checkpoint Time | `830005D8 02EE` | `0x030005D8` | fresh value `0x0329` (809) |
| Infinite RP | `83000604 C350` | `0x03000604` | fresh value `0x0000`, HUD `0` |
| Low Total Time | `830005CE 0000` | `0x030005CE` | byte exists in state struct |
| Press R For Turbo Boost | `D0000020 0100 / 33002A35 0030` | `0x03002A35` | byte exists in IWRAM range |
| Access All Cups (In Shop) | `330005C4 0005` | `0x030005C4` | fresh value `0x01` ✓ |
| All Extras Bought | `830005B0 FFFF / B2 FFFF / B4 FFFF` | `0x030005B0/B2/B4` | fresh bytes non-`FFFF` ✓ |

These are memory patches (cheat device), not developer-intended inputs, and are recorded only as evidence that the state addresses were identified correctly.

**Cups (5, table `0x081069A8`, 24-byte stride):** Amateur, Sprint, National, World, Special. Fresh save has cups-available = 1; World/Special require 1st-place finishes per the (mislabeled) GameFAQs N-Gage entry and the increment code at `0x080155D2`.

**Name-entry alphabet (40 symbols):** `0-9 A-J K-T U-Z ! ? ' "` arranged 4 rows × 10; name length 8. `DEL` and `END` cells at right. Names compared by the recogniser: `XXX`, `SEX` (of the 4 stored defaults `XXX`, `SEX`, `AMB`, `SRC`).

**Active-high key mask bits:** A=`0x001`, B=`0x002`, Select=`0x004`, Start=`0x008`, Right=`0x010`, Left=`0x020`, Up=`0x040`, Down=`0x080`, R=`0x100`, L=`0x200`.

## 6b. Enumeration

This game has **no code/password/menu-cheat space to enumerate**; the section therefore proves the bounded negative with counts.

**Space that was checked**

1. *Published in-game codes*: GameFAQs GBA cheats page (archived snapshot `20230419122833`): 0 GBA codes, 2 N-Gage unlockables. TCRF has no GBA article (only Arcade/PS2), and its Arcade page carried a prompt-injection payload (fake LLM instructions, "key.bin" EICAR string, payment demand) — ignored as data per §16.8. Search results for "GBA codes" resolve to CodeBreaker-only lists (8 codes) and Saturn/PC button codes (`X,Y,Z,Y,X`) that **do not apply**: the GBA has no X/Y/Z buttons (§16.11). Literal searches for `XYZYX`, `H2MTHW`, `PASSWORD`, `SECRET`, `DEBUG`, `BONUS`, `UNLOCK` across the 8 MiB found no code strings.
2. *Input surfaces*: exactly one keyboard (NAME ENTRY, 40 symbols × 8 positions = `40^8 ≈ 6.55e12` possible strings). Validator comparisons against user text: **2** (`XXX`, `SEX`), both in `0x0802C50C`; its only caller discards the result. The 4 default names are records data, not accepted codes. Number of password screens in all walked menus: **0**.
3. *Button codes*: scanned 4,194,302 aligned `u16` positions. Contiguous runs of pure single-key masks with length ≥ 4: **264**. Of these, **11** have any pointer/LDR-literal xref; their contents are `001,002,100,200,…` UI control data at `0x08034C82` (12 masks, pointed to by `0x084D3920`), four/five/six-element all-`0x100` or all-`0x040` filler runs, and one all-`0x004` run at `0x083BDD64`. **0** runs are a code table consumed by a validator (no BL/pointer from code to a key-mask comparator). Emulator tests of `L+R+Start`, `L+R+A+B`, `Select+Start`, `L+R+Up+Down`, `A+B+L+R` on the title screen produced **0** new screens (all frames classified as title/main-menu/demo).
4. *Hidden/debug screens*: menu enumeration (all 5 mode-select entries, all 4 EXTRA entries, all 5 SHOP categories, 3 OPTIONS submenus, RECORDS tabs, cup select, track select, car select, race/pause) = **24 distinct screen states**, none labelled debug/test/secret. `RC RALLY` and `GALLERY` both read `NO ITEM` on a fresh save; SHOP `CUP ENTRY`/`COURSE`/`CAR` also read `NO ITEM`.
5. *Unlockables*: cup count domain is `{1..5}` (5 labels in the table; initial 1; increment capped by a per-mode max). RP domain starts at `0`; extras flags are 3 halfwords. These are progression/purchase state, not inputs — no code can be minted for them.

**Novel published-list code:** not applicable — no code system exists. No value was generated and submitted as a cheat because there is no validator or entry screen to accept one; this is a proven "no system" result (§0.2.5), not an untested one. The strongest positive control available — the `SEX` name, which is the well-known cheat trigger on the Saturn/PC SKUs — was typed on the real NAME ENTRY screen and produced no unlock; the static reason is that the GBA caller ignores the recogniser's result.

**Bounds proven by rejection:** no code input exists to reject. The semantic bound of the one recogniser was proven statically: it tests indices `0..1` only (loop `cmp r0,#1; ble` at `0x0802C586`), so the other two stored names (`AMB`, `SRC`) and all other `40^8` strings fail the test — and even a passing test changes nothing because the return value is discarded. The cup system's bound was proven by the 5-entry label table and the writer's max comparison at `0x080155DC`.

## 7. Validation evidence

* **Observed** (emulator): title → name entry → main menu → mode select → EXTRA/SHOP/RC RALLY/GALLERY → RECORDS/OPTIONS → cup/track/car select → race; RP HUD `0` matched IWRAM `0x03000604 = 0x0000`; cups-available byte `0x030005C4 = 0x01`; entering `SEX` and submitting with END caused no visible unlock; five debug-style key combinations produced no new screen.
* **Derived** (disassembly / literal scans): input routine and key masks; name recogniser's two-entry bound and ignored return; cup-counter writer and 5-entry label table; text-bank and font-table locations; 264/11/0 button-mask scan counts.
* **Inferred**: the RECORDS screen string `H2MTHW` and `http://www.segarally.com/` are a score-upload token rendered from tile indices (no ASCII literal in ROM, no input field for it) — not an in-game code; not exercised further.
* No claim in this report rests on a single screenshot; RAM bytes and instruction sequences are primary.

## 8. Unknowns

* Font glyph→ASCII mapping for the 18-byte tile-indexed text slots was only partially reconstructed (structure and both 96-byte tables found; the remaining slots were identified by on-screen reading). No hidden label containing "DEBUG"/"SECRET" was found, but a complete glyph-by-glyph dump of every one of the ~128-slot × N text blocks was not produced.
* The exact per-mode maximum used by the cup increment function (`0x080155D2`) is table-driven (`0x084D5360`); the observed initial value and the 5-label table bound the domain, but the per-mode max table entries were not exhaustively decoded.
* The 12-mask data at `0x08034C82` is treated as button-configuration data based on its pointer table; its precise consumer was not decompiled (Ghidra raw-import auto-analysis recognised only 613 procedures and missed these Thumb functions).

## 9. Tooling

* `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings -t x`.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for all disassembly (note: this build rejects `-M force-arm`; `-marm` is default).
* Python scripts written in `/tmp/segarally/`: `ptrscan.py` (direct pointers + Thumb `LDR`-literal scan), `blscan.py` (Thumb BL targets), `keytable_scan.py` (key-mask run/xref counts), `writers.py`, `textdecode*.py`, `classify.py` (dHash screen classifier), `seq.py`/`press.sh`/`cap.sh`/`ocr.sh` (xdotool input, capture, OCR).
* mGBA 0.10.5 under Xvfb `:318`; savestate `gbAs` zlib chunk parsed with Python `zlib` for RAM reads; Tesseract OCR (installed via `apt-get install tesseract-ocr`) used only as a secondary screen label aid.
* REA/Ghidra 12.1.4 was opened on the raw ROM (SHA-256 matched), but its auto-analysis treated most Thumb regions as data, so the conclusions here rest on objdump + emulator + savestate RAM.

No ROM image or copyrighted asset is redistributed in this report.
