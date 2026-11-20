# Tron 2.0: Killer App (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Tron 2.0: Killer App/Tron 2.0: Killer App.gba` |
| Size | 16,777,216 bytes (0x01000000, 16 MiB) |
| Header title | `TRON 2.0 KIL` |
| Game code / maker | `BTNE` / `4Q`, version 0x00 |
| Entry word | `0xEA00002E` (stock `b 0x080000C0`; crt0 at 0xC0 is normal — **not** a cracktro) |
| Fixed 0x96 | present; complement byte `0xB0`; header checksum `0x0000` (rebuilt-header artifact, §16.1) |
| MD5 | `5c332a3e712b41e8cf61240034b8d4c4` |
| SHA-1 | `f75bb043c627a5e2df99cbf6b55dda5574738358` |
| SHA-256 | `f6ff155faa1eb321915875c21c82f7bd25d8f42ce6ba780354d197a62e276ea6` |

All addresses below are for this exact image (file offset `F` ↔ ROM address `0x08000000 + F`; flat 16 MiB, no sub-images).

## 2. Executive summary

The game has exactly **three** developer-intended cheats, all entered as **button sequences on the title screen ("PRESS START")**. They are not passwords and there is no password/keypad screen. Each is eight D-pad presses followed by **Select**, which acts as the *trigger* (Select is not part of the stored sequence).

| # | Sequence (then Select) | Published effect | Flag bit |
|---|---|---|---|
| 0 | L L L L U R D D | Unlock all Mini-Games | 0 |
| 1 | U D U D U D U L | Unlock all Battle Mode maps | 1 |
| 2 | R R L L L R R U | Unlock all Chips (and the pause-menu "Cheats" option) | 2 |

The three codes are a 3 × 8 halfword table at `0x080D4C5C`; a single validator at `0x08054D08` compares the last eight recorded key masks against all three entries and **toggles** the corresponding bit in a flag word (re-entering a code turns it back off). All three were entered in mGBA and the flag word was read before/after: `0x00000000 → 0x00000001 → 0x00000003 → 0x00000007`, then re-entering code 0 gave `0x00000006` (toggle confirmed). Six non-published/rejected inputs left the flag unchanged, proving the set is closed (§6b).

Additional text-based unlockables (the 100 Chip list / "Cheat Chips" collected in story mode) are save-bit unlocks, not codes. CodeBreaker/GameShark lists exist on the web but are explicitly out of scope and were not used.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 under Xvfb, `SDL_AUDIODRIVER=dummy`, scale 3×.
* mGBA SDL keymap (verified against `KEYINPUT` `0x04000130`): **A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`**, D-pad = arrow keys. Using X11 keysym `Select` does *nothing* — Select is `BackSpace`.
* Boot to the title screen ("PRESS START"). Do **not** press Start first.
* Hold each direction ~50 ms with ~120 ms gaps; finish with a `BackSpace` tap. A long hold writes the same mask into several ring slots and breaks the sequence.
* The code is accepted silently except for a sound effect; the durable evidence is the flag word.
* RAM read (via mGBA CLI debugger `-d`, driven through a pty; GDB stub port 2345 was occupied by another session):
  * flag word: `[0x03000888] + 0x14D0` = `0x0203D940` in this run (4 bytes).
  * key-history ring: `state + 0x220`, index byte `state + 0x24A`; the live state pointer was `0x0203A0D8` → ring `0x0203A2F8`, index `0x0203A322`.
  * key input global: `0x0300040A` (active-high mask; value `0x04` = Select triggers the check).
* Alternative RAM evidence: mGBA savestates (`save 1` from the debugger) are PNGs with a zlib `gbAs` chunk; decompress to 397,312 bytes, with IWRAM at raw `0x19000` and EWRAM at raw `0x21000`. EWRAM `0x0203D940` maps to raw `0x5E940`.

## 4. Address map

| Item | Address | Evidence |
|---|---|---|
| Button-code table, 3 × 8 `u16` | file `0xD4C5C`–`0xD4C8A` = `0x080D4C5C` | literal pointer at `0x08054D84`; bytes match all three published codes |
| Validator (Thumb) | `0x08054D08` | BL xref from `0x08054E1E`; disassembled |
| Title-screen input handler | `0x08054E10` | breakpoint hit on key press; `r0` = state pointer `0x0203A0D8` |
| `memcpy`-like copy helper | `0x080A61C8` | called with `(sp, 0x080D4C5C, 0x30)` = 48 bytes |
| bit test / set / clear | `0x0800F4A4` / `0x0800F464` / `0x0800F484` | helpers called by validator |
| flag-word pointer global | `0x03000888` → `0x0203C470` | read live; + `0x14D0` = `0x0203D940` |
| key mask global | `0x0300040A` | read via debugger; Select = `0x0004` |
| key-history ring | `state+0x220` … `state+0x22E` (8 × `u16`), index at `state+0x24A` | observed ring `[0x20,0x20,0x20,0x20,0x40,0x10,0x80,0x80]` after entering code 0 |
| sound player | `0x080185F0` | `r0=0x1F` (unlock) / `0x24` (toggle-off) |
| flag-bit menu consumer | `0x08013E20`–`0x08013F2A` | `bl 0x0800F4A4` (test) and set/clear branches |

## 5. Algorithm

Key masks are active-high GBA buttons: `A=1, B=2, Select=4, Start=8, Right=0x10, Left=0x20, Up=0x40, Down=0x80`.

```
# 0x08054E10 (title-screen handler), called when a key is pressed
if key_global == 0x04:            # Select held -> validate
    check_codes(state)
if key_global != 0:               # record any nonzero key into the 8-slot ring
    i = state[0x24A]
    state[0x220 + 2*i] = key_global
    state[0x24A] = (i + 1) & 7

# 0x08054D08
copy(48 bytes, stack, 0x080D4C5C)     # 3 codes x 8 halfwords
for c in 0 .. 2:
    start = state[0x24A]              # u8
    for j in 0 .. 7:
        if ring[(start+j) & 7] != code[c][j]:
            goto next_c               # mismatch: NO sound, NO ring clear
    # match -> TOGGLE bit c of flag word at [0x03000888]+0x14D0
    if bit(c) == 0: set_bit(c); sound(0x1F)
    else:           clear_bit(c); sound(0x24)
    clear ring[0..7]
```

Notes: the validator is called *before* the current key is stored, which is why Select triggers on the preceding eight presses. The loop bound is `r4+1 <= 2`, i.e. exactly three codes; the copy length `0x30` is exactly 48 bytes. There is no checksum, no alphabet and no variable length — the "code space" is the table itself.

## 6. Tables

### 6.1 Stored code table (`0x080D4C5C`)

| Index | Halfwords (little-endian) | Buttons | Meaning |
|---|---|---|---|
| 0 | `20 20 20 20 40 10 80 80` | L L L L U R D D | All Mini-Games (bit 0) |
| 1 | `40 80 40 80 40 80 40 20` | U D U D U D U L | All Battle Mode maps (bit 1) |
| 2 | `10 10 20 20 20 10 10 40` | R R L L L R R U | All Chips (bit 2) |

Word `0xFFFF` at `0x080D4C8C` follows the table (not part of a code; a separate function at `0x0805FBA8` copies six halfwords from there for unrelated data).

### 6.2 Flag bits (`0x0203D940`)

| Bit | Set by code | Observed |
|---|---|---|
| 0 | LLLLURDDS | `0x0 → 0x1`; re-entry `0x7 → 0x6` |
| 1 | UDUDUDULS | `0x1 → 0x3` |
| 2 | RRLLLRRUS | `0x3 → 0x7` |

### 6.3 Published-code reconciliation

SuperCheats, ChapterCheats and GGmania all list the same three sequences. SuperCheats omits the trailing Select for the All-Chips code while GGmania includes it; the disassembly shows why: Select is the validation trigger and is never one of the eight stored halfwords. CodeBreaker/GameShark lists (Almar's Guides, jeuxmangas) were noted but not used (out of scope). Fetched pages were treated as data; no prompt-injection content was observed.

## 6b. Enumeration

**Space definition.** Input alphabet for the code table = four D-pad masks (`0x10,0x20,0x40,0x80`); length is fixed at 8 presses; trigger = Select (`0x04`), not stored. The number of possible 8-press D-pad sequences is `4^8 = 65,536`; allowing all six D-pad/Start/Select masks gives `6^8 = 1,679,616`. The accepted set is **exactly 3 sequences**: the ROM contains one 48-byte table of three entries, the only 32-bit pointer to it is at `0x08054D84`, and the validator's loop is bounded to `c = 0,1,2`. A targeted scan of the whole 16 MiB for other runs of ≥6 consecutive key-mask halfwords found four candidates; only `0x080D4C5C` is referenced by a pointer (the other three are unrelated data/audio runs at `0x0A6532`, `0x77017A`, `0x770274`). There is no password alphabet, no checksum and no variable-length code path in the reachable UI.

**Novel code and acceptance proof.** All three published codes were minted from the decoder (the table), entered on the real title screen, and verified by RAM reads (§6.2). To exercise an unadvertised combination I also entered sequences that appear in no published list; these are the rejection tests below.

**Bounds proven by rejection.** Emulator halted after each sequence; flag word `0x0203D940` read from RAM. Baseline before this block was `0x00000006` (bits 1 and 2 set, bit 0 cleared):

| Test sequence (Select appended) | Flag after | Result |
|---|---|---|
| `U U U U U U U U` (novel, unpublished) | `0x00000006` | rejected |
| `L L L L U R D U` (one-press near miss) | `0x00000006` | rejected |
| `R L L L U R D D` (one-press near miss) | `0x00000006` | rejected |
| `L L L L U R D D D` (9 presses) | `0x00000006` | rejected — no suffix match |
| `L L L L U R D D` with no Select | `0x00000006` | no validation — Select is required |
| `L L L L U R A D` (A button in sequence) | `0x00000006` | rejected — only the 4 D-pad masks are stored |

These bound the matcher to exact, position-for-position, eight-press D-pad sequences with Select as an exact-mask trigger. Re-entering a published code toggles its bit off (`0x7 → 0x6`), which also bounds the "unlock" semantics to a toggle, not a one-way set.

**Hidden/debug-menu negative.** No debug menu or password entry screen was found on any reachable screen. The only cheat surface is the three title codes plus save-bit chip unlockables (§16.18 pattern: `0x08013E20`–`0x08013F2A` tests the same flag bits with `0x0800F4A4` to include/exclude menu rows; the chip-collect path sets them in normal play). No separate button-code table exists (scan above).

## 7. Validation evidence

* **Observed** (emulator + RAM): three published codes accepted; flag word transitions `0→1→3→7→6`; six rejected sequences leave flag unchanged; live ring buffer held exactly `L,L,L,L,U,R,D,D` after code 0; `KEYINPUT` confirmed BackSpace = Select (`0x03FB`), `x` = A, `z` = B, `Return` = Start.
* **Observed** (screens): title; main menu (Story Mode / Battle Mode / View Clips / Mini-Games / Options); Options submenu (Music, Sound FX, Tutorial, Credits); Story Mode submenu (New Game / Continue Game / Delete Game); Mini-Games selector (Light Cycle / Tank / Recognizer); classic-game list (Tron (1982), Discs of Tron (1983), Firewall, Security, Defragment, View High Scores); character select; chip loadout; gameplay; game-over "Play Again?".
* **Derived** (disassembly): 3-entry table, bounded loop, toggle semantics, ring indexing, trigger semantics, helper bit functions.
* **Inferred** (not played through): the exact visible effect of bit 1 (Battle Mode maps) and the pause-menu "Cheats" row from bit 2 — the flag-bit consumer at `0x08013E20` is consistent with the published descriptions, but the specific maps/rows were not reached in this session. Battle Mode's submenu itself was not successfully opened (the menu cursor could not be pinned down reliably; see Unknowns).
* RAM evidence per screen: savestate snapshots `00_title`, `01_menu`, `03b_minigames`, `classic_list`, `story_sub`, `char_select_done`, `gameplay`, `pause_menu`, etc. in `/tmp/opencode/tron/*.ss1` with decompressed `*.raw`; e.g. title→menu changed 17,287 raw bytes and the flag word stayed `0x07000000` throughout.

## 8. Unknowns

* The main-menu cursor byte was not identified; the same Down/A sequence reached different submenus on different passes (the large/bright text is an animation, not a reliable highlight). Battle Mode's submenu was therefore not opened. Its unlock (bit 1) is proven by RAM, its screen contents are not.
* The in-game pause menu was not reached (Start/Select in the light-cycle segment were consumed as gameplay actions). The pause-menu "Cheats" option of the all-chips code remains an inferred effect from `0x08013E20`.
* The 100-chip list and the "Cheat Chips" counts (1/2/4 per cheat) were not enumerated; these are save-bit unlockables, not button codes.
* `Tron (1982)` appeared dim in the classic-game list; whether it is gated separately was not tested.

## 9. Tooling

* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for the validator and helpers.
* Python + Capstone 5.0.7 for literal/BL scans and the key-mask table scan.
* mGBA 0.10.5 CLI debugger (`-d`) bridged through a Python `pty` + FIFO (`/tmp/opencode/tron/dbg.py`, `harness.py`); `SIGINT` used to halt and `x/1|x/2|x/4` to read RAM. The GDB stub was unusable because port 2345 belonged to another session.
* `xdotool` XTEST key events, `scrot` + ImageMagick `convert`/`montage` for screen evidence.
* Savestate parsing: PNG `gbAs` chunk, `zlib.decompress`, 397,312-byte raw state (IWRAM `0x19000`, EWRAM `0x21000`).

No ROM or copyrighted assets are redistributed in this report — only addresses, hashes, algorithms and observations.
