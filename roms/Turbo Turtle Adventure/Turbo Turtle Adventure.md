# Turbo Turtle Adventure (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Turbo Turtle Adventure.gba` |
| Size | 4,194,304 bytes (4 MiB) |
| Header title | `TURBO TURTLE` |
| Game code | `AK3E` |
| Maker code | `5G` (Majesco) |
| Version | `0x00` |
| Entry word | `0xEA00002E` (stock ARM branch, not a cracktro) |
| Developer | Iridon Interactive AB (confirmed by in-game copyright splash and 3rd party cheat indexes) |
| MD5 | `9b72e0259be5e4adddd2fed212c9fde7` |
| SHA-1 | `92aae76deb40a3d63e99c4981dec7e790a67ebca` |
| SHA-256 | `45dcf6823fe4161274c4702129adf0eb2bdf0b4d73897c21808eabccf85b481c` |

Save type: 512-byte EEPROM (mGBA created a 512-byte `.sav`).

## 2. Executive summary

This title has **no password entry screen, no published button-code list, and no reachable
debug menu**. The only developer-intended cheat surface is an **unlockable "Extras" menu**
behind a save-progress gate. Once unlocked it contains three entries: **Sound Test** (25
tracks, including a hidden **Bonus Track**), **Difficulty** (actually the Normal/Hard timer
setting), and **Animation Test** (Intro / Ending).

The gate was reversed to machine precision: `0x0800E388` returns `0` (locked), `1` (progression
flag) or `2` (100 % progress). I minted a crafted flag state (2-bit field 58 = odd value `1`,
progress = `0`) that unlocks Extras on a fresh save — a combination normal play does not
produce. Bounds were proven in-game: the even value `2` is rejected, the value `0` is rejected,
and progress `101` is rejected (the comparison is exact `== 100`).

A bounded negative for a code system is also documented (§7, §8): all 248 UI strings decoded,
all reachable screens walked, all four key-input readers inspected, and button-mask/alphabet
scans counted.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 (`/usr/local/bin/mgba`), Xvfb `:318`, `SDL_AUDIODRIVER=dummy`.
* Keymap (verified by reading KEYINPUT at savestate offset `0x530`):
  `A = x`, `B = z`, `L = a`, `R = s`, `Start = Return`, `Select = BackSpace`, D-pad = arrows.
  **Hold keys ≥ 0.35 s** — this game polls input slowly; a 0.12 s tap is silently missed.
* Menu path: boot → Start → title → **Options** → **Extras**. With a fresh save, Extras is
  inert (A does nothing).
* To unlock without playing: load a patched savestate (see §9) with field 58 set to `1`, or
  break at `0x08011698` in the mGBA CLI debugger and write `w/1 0x0203FE18 0x10`.
* Savestates: mGBA SDL hotkeys `Shift+F1..F4` save, `F1..F4` load; states are written next
  to the ROM. Raw RAM is extracted from the PNG's zlib `gbAs` chunk (EWRAM at raw `0x21000`,
  IWRAM at raw `0x19000`).

## 4. Address map

| ROM / RAM address | Meaning |
|---|---|
| `0x0800E388` | **Unlock gate**. Returns `0` / `1` / `2` (see §5). Called from `0x0800FF12` and `0x08010AF2`. |
| `0x0800E298` | Reads progress word `[row][current_slot]` from `0x0203FE48 + row*0xC`. |
| `0x0800E10C` | Reads a 2-bit field from `flags[current_slot*20 + (id>>2)]`. |
| `0x0800E160`, `0x0800E1F4`, `0x0800E230` | Field setters (2-bit masks `0x03`, `0x30`, `0xC0`). |
| `0x0800E3E4` | Save-slot clear: zeroes 20 flag bytes and the four progress rows. |
| `0x0800E44C` | Text printer: `r0` = text ID → `0x082D2F20 + id*4`. 47 call sites (UI). |
| `0x082D2F20` / `0x082D301C` | UI text-ID tables, 2 banks (English / Swedish), 248 entries total. |
| `0x0814A970`–`0x0814AA30` | 25 sound-track name pointers; **`0x0814A9D0` = "Bonus Track"** (index 12). |
| `0x03000004` | Pointer to global struct; `struct+0x3C` = current save slot (0..2). |
| `0x0203FE0A` | Per-slot flag array: 20 bytes × 3 slots, four 2-bit fields per byte. |
| `0x0203FE48/54/60/6C` | Progress word rows (4 × 3 slots). `== 100` means 100 %. |
| `0x04000130` | KEYINPUT. Only four literal references in ROM: `0x08001A80`, `0x080119E2/FE`, `0x08012202/0A`, `0x08013752`. |

## 5. Algorithm

The gate at `0x0800E388` (Thumb) is exactly:

```c
int unlock_level(void) {
    int saved_slot = global->slot;          // [0x03000004]->+0x3C
    for (int row = 0; row < 3; row++)
        if (progress[row][saved_slot] == 100)  // 0x0203FE48 + row*12
            return 2;
    for (int s = 0; s < 3; s++) {
        global->slot = s;
        int v = field(0x3A, s);              // 0x0800E10C(58)
        if (v & 1) { global->slot = saved_slot; return 1; }
    }
    global->slot = saved_slot;
    return 0;
}

int field(int id, int slot) {
    // flags = (byte*)0x0203FE0A; 20 bytes per slot
    byte b = flags[slot*20 + (id >> 2)];
    return (b >> (2 * (id & 3))) & 3;
}
```

`id = 0x3A = 58` → byte index `14`, field `(b & 0x30) >> 4`, i.e. bits 4–5 of
`0x0203FE0A + slot*20 + 14`. **Only odd values (1 or 3) unlock.** The second condition is
an exact `== 100` word comparison (101 fails, proven in §6b).

The caller at `0x08010AF2` reads this level into `r6`; level `0` leaves Extras inert, any
nonzero level draws and enables the Extras menu.

## 6. Tables

**Extras menu (unlocked), in display order**

| Entry | Sub-screen | Contents |
|---|---|---|
| Sound Test | 25-track list | Level Complete, Title Screen, Training Complete, Isle of Mazes, Jungle Ruins Map, Lagoon Map, Glacier Map, Volcano Map, Woodlands Map, Bat Cavern Map, Space Station Map, Credits, **Bonus Track**, Jungle Ruins 1/2, Woodlands 1/2, Glacier 1/2, Space Station 1/2, Volcano, Lagoon 1/2, Bat Cavern |
| Difficulty | Timer Setting | Normal / Hard |
| Animations | Animation Test | Intro / Ending |

The menu is exactly three items and wraps around (verified: Down ×2 returns to Sound Test).
"Gallery"/"Fotoalbum" and "Layout A/B"/"Controls" exist in the text bank but are **not**
exposed on any reachable screen (dead strings, not hidden menu entries).

**Font/tile text**: the region `0x0814AAD8`–`0x0814AC40` is 21-symbol tile-index credit text
(`0x62` = blank, 252 of 368 bytes). It is a font-index string, not a password alphabet.

## 6b. Enumeration

**Space definition.** The unlock gate has two independent predicates over a per-slot save
record:

* `field(58)` is a 2-bit value → 4 spellings `{0,1,2,3}`; the accept set is `{1,3}`
  (2/4 = 50 %). `0` and `2` are rejected.
* Each of the 12 progress words is 32-bit; the accept value is exactly `100` (1/2³²).
  `101`, `99`, `0` are rejected.

**Novel crafted unlock (not in any published list).** No published code list exists for this
title — searched 3rd party cheat indexes (1 "cheat", actually a level-4 FAQ), 3rd party cheat indexes. The crafted value is:

> **Field 58 = 1** (byte `0x0203FE18 = 0x10`), progress words = `0`.

Applied to a fresh savestate, reloaded, then Options → Extras → A: the **Extras screen opens**
(`accept_extras.png`), and scrolling Sound Test 16 presses shows **BONUS TRACK**
(`soundtest_scroll.png`). RAM verification: savestate diff accept-vs-reject shows the only
EWRAM change is `0x0203FE18: 0x10 → 0x20` (`state5.raw` vs `state6.raw`); the IWRAM changes are
rendering state. This combination (odd field with zero completion) is not emitted by any
normal gameplay path — the field setter at `0x0800E1F4` only sets it on the completion path.

**Bounds proven by in-game rejection**

| Input | Result | Evidence |
|---|---|---|
| field 58 = `0` (fresh save) | A on Extras does nothing | `extras_try2.png` |
| field 58 = `2` (byte `0x20`) | A on Extras does nothing | `reject_after_A.png` |
| field 58 = `1` (byte `0x10`) | Extras opens | `accept_extras.png` |
| field 58 = `3` (byte `0x30`) + progress `100` | Extras opens, Bonus Track reachable | `extras_unlocked2.png`, `soundtest_scroll.png` |
| progress word = `101` (0x65) | A on Extras does nothing | `bound101.png` |

**Bounded negative (no code system).** Counts: 248 UI strings decoded from the text-ID
table (both language banks) — **0** occurrences of `PASSWORD`, `PASS WORD`, `CHEAT`,
`ENTER CODE`, `SECRET CODE`, `LEVEL SELECT`, `DEBUG MENU` (case-insensitive) anywhere in the
4 MiB image. All screens walked with screenshots and RAM evidence: 4 boot/logo/copyright
screens, title, Choose a Game (3 slots + Erase), Options, Extras + 3 sub-screens, 25-entry
Sound Test, Training hint screen (1/10), gameplay with HUD, and all menu wrap-arounds. Only
**4** KEYINPUT literal readers exist; disassembly shows none accumulates or compares a button
sequence. A scan for runs of ≥4 button-mask `u16` values found 977 candidates, all in graphics
and level data (no validator xref); no known sequence (Konami code, L+R, UUDD) appears in any
encoding. No on-screen alphabet/keyboard exists. Conclusion: **no password or button-code
system exists in this SKU**; the bounded negative is about the whole reachable UI plus the
static table/string space counted above.

## 7. Validation evidence

* **Observed (emulator):** Extras inert on fresh save; opens with crafted field; Bonus Track
  listed; three Extras entries; all sub-screens; rejections listed in §6b. Screenshots named
  above were in `/tmp/turboturtle/`.
* **Observed (RAM):** savestate `gbAs` chunks; EWRAM gate bytes at raw `0x60E18`
  (`0x0203FE18`); IWRAM/EWRAM diffs between accept and reject states.
* **Derived (disassembly):** `0x0800E388` gate, `0x0800E10C` 2-bit field extraction,
  `0x0800E298` progress lookup, callers at `0x0800FF12`/`0x08010AF2`, 25-track pointer table
  at `0x0814A970`.
* **Inferred:** field 58's semantic label (a completion flag) is inferred from the setter call
  path; its exact in-game trigger was not played through. The `Gallery`/`Layout A/B` strings
  are inferred dead because no reachable screen draws them; this was not proven by a
  breakpoint-never-fires test.

## 8. Unknowns

* The exact gameplay action that sets field 58 and the 100 % progress words (would require a
  full playthrough).
* Whether "Gallery"/"Fotoalbum" is a cut feature from an earlier build.
* Whether the Bonus Track is gated additionally by a value beyond opening Extras (it is
  listed and selectable after the gate is open; its audio was not recorded).
* No pause menu appeared on Start during gameplay; if one exists on another input it was not
  reached.

## 9. Tooling

* `strings -t x -n 4` for the UI text banks; Python `struct` scans for literal pointers,
  Thumb `BL`/LDR PC-relative references, and button-mask runs.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for all
  disassembly.
* mGBA CLI debugger (`mgba -3 -d`) over a Python pty harness (`dbg_daemon.py`, `dbg.py`): a
  breakpoint at `0x08011698` yields a halted prompt; commands are only executed while halted
  (Ctrl-C alone prints a snapshot and resumes).
* `state.py` extracts the zlib `gbAs` chunk from `.ssN` PNG savestates; `patchstate.py` patches
  EWRAM bytes and rebuilds the PNG for deterministic accept/reject tests.
* Web recon: 3rd party cheat indexes/1712M. Fetched pages were treated as data only; no instructions in them were
  followed. No prompt-injection content was encountered.

**Legal note:** no ROM bytes, graphics, music or extracted assets are reproduced here — only
addresses, hashes, algorithms and original observations.

---

*Coordinator note: this report intentionally does not edit `roms/INDEX.md` or the guide.*
