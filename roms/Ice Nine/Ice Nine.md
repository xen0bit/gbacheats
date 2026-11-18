# Ice Nine (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Ice Nine/Ice Nine.gba` |
| Size | 8,388,608 bytes (0x800000, 8 MiB) |
| Header title | `ICE NINE` |
| Game code | `AR3E` |
| Maker | `6L` |
| Version | 0x00 |
| Fixed 0x96 | present at 0xB2 |
| Complement byte | 0xA9 (calculated 0xC2 — **mismatch**; header checksum stored 0x0000, calculated 0x8096) |
| Entry word | 0xEA000030 → ARM branch to 0x080000C8 (stock-looking crt0, no cracktro branch) |
| Embedded GBA headers | exactly 1 (Nintendo logo at file 0x04 only) |
| MD5 | `b15b6cb642868b1b92031a10e5a68dd7` |
| SHA-1 | `47cae2872f85d2dd56967c34f9160838166a47a6` |
| SHA-256 | `5966d11dd20bbd4946996ab7e414d32b630b5214eecdaff7b0792a89a78a5cba` |

Developer/engine strings: `TORUS GAMES`, `BAM! ENTERTAINMENT`, `FPS Engine Team`;
multi-language script (En/Fr/De/Es/It) at file 0x70000+. The header byte mismatch
(§16.1) indicates a rebuilt/edited header, but there is no appended trainer, no
cracktro entry patch, and no second GBA header. GameHacking.org lists CRC32
`14C23257` / serial `AGB-AR3E-USA` for the same SKU.

## 2. Executive summary

Ice Nine is a commercial first-person shooter (Torus Games / BAM! Entertainment)
with **no password/code-entry screen and no printable cheat-code table**. The
developer-intended cheat surface consists of:

1. **Button combos.** The in-game Options/Controls screen documents
   `L+R+D-pad` free-look, `L+R+Up/Down` zoom, `Select+A` holster/unholster,
   `Select+B` night vision, plus standard movement/fire/jump/pause-map bindings.
   A further, *undocumented* combo is published by GameFAQs/supercheats/gamegenie:
   **hold `L + R + SELECT + B` for two seconds at a locked door** → a "Trust No
   One" voice, a one-second black-and-white screen flash, and the door becomes
   enterable without its switch. This is the only genuine hidden button cheat.
2. **Save-bit unlockables.** Completing the first 15 missions unlocks bonus
   missions (any difficulty except Initiate) and a cheat menu with unlimited
   health/ammo and mission select plus Veteran difficulty (Graduate). These are
   progression flags in the 512-byte EEPROM save, not input codes (§16.18).

No GameShark/CodeBreaker codes are in scope. GameHacking.org's "Skip Mission
[L+B]" etc. are memory-edit cheats and were deliberately not investigated.

The whole reachable UI was walked on the real ROM (language select, title,
intro/credits, mission dialogue, gameplay HUD, pause menu with Map/Mission
Brief, a controls screen, and the mission briefing screen with Save/Continue/
Quit). No password/cheat/level-select entry surface exists.

## 3. How to reproduce

* Emulator: `mgba -3` under Xvfb `DISPLAY=:319`, `SDL_AUDIODRIVER=dummy`.
  Keymap used: GBA `A=x`, `B=z`, `L=a`, `R=s`, `Start=Return`, `Select=BackSpace`,
  D-pad = arrow keys.
* Fresh boot → **Select Language** (choose English with A) → boot animation →
  **"ICE NINE / Press Start"** title. Press Start → scrolling credits/
  briefing; press Start repeatedly to skip → "Mission 1: Down on the Farm /
  Save / Continue / Quit" → Continue → in-game dialogue (A to advance) →
  gameplay HUD (health 100, armour, kills/civilians counters, knife in hand).
* Pause with Start → **Map / Mission Brief, Resume, Options, Controls, Quit**.
  Moving down two notches to Options and pressing A opens the controls-diagram
  screen (Type A/B sensitivity, free-look/zoom/holster/night-vision legend).
  B returns to gameplay.
* Combo verification: in gameplay, hold `a`+`s`+`BackSpace`+`z` (L+R+Select+B).
  The active-high held-key mask in IWRAM becomes exactly `0x0306`.
* Published GameFAQs codes tested verbatim against the ROM: `L,R,SELECT,B
  (hold two seconds)` — literal mask verified, effect requires being at a
  locked door (see §8). No password string from any published list exists in
  the ROM because the game has no password system.

## 4. Address map

| Item | ROM file offset / address | Evidence |
|---|---|---|
| GBA header | 0x000–0x0BF | Observed (xxd) |
| Entry point (ARM) | 0x080000C8 | Derived (0xEA000030) |
| Script/dialogue bank (ASCII + control codes `\C \B \J \P \U \x \f \k \O \S`) | file 0x70000–0x72400+ | Observed (strings) |
| "Press Start" title string | file 0x0706F9A (`0x08706F9A`) | Observed |
| Credits block | file 0x0700AC4 | Observed |
| Night-vision hint strings | file 0x070B5F3, 0x070CD1D | Observed |
| Key-input literal `0x04000130` (UI handler) | file 0x03B80 | Derived |
| **UI input handler** (active-high held/pressed) | **`0x08003B68`** | Derived (objdump) |
| UI held mask | IWRAM `0x0300001E` | Derived |
| UI pressed mask | IWRAM `0x03000020` | Derived |
| Key-input literal `0x04000130` (gameplay handler) | file 0x17520 | Derived |
| **Gameplay input handler** | **`0x080174E4`** | Derived (objdump) |
| **Gameplay active-high held mask** | **IWRAM `0x03000EF8`** | Observed (debugger `r/2`) |
| Gameplay edge masks | IWRAM `0x03000EFC`, `0x03000F00` | Derived |
| EWRAM key-binding struct (Up/Down/L/R, etc.) | `0x0200004C` | Observed (debugger dump) |
| Generic flag word read by sound dispatcher | IWRAM `0x03000ED4` | Derived |
| Button-combo config readers | `0x08026C0C`, `0x08026C86` etc. | Derived |
| Misc. held-mask readers (enumerated by read watchpoint) | `0x08026C14`, `0x080296F6`, … | Observed (watchpoint) |
| Save data | EEPROM, 512 bytes (`Ice Nine.sav`), all `0xFF` on a fresh start | Observed |

File offset → ROM address is `0x08000000 + offset`. All addresses in this
report were re-read from the analyzed image with the exact hash in §1.

## 5. Algorithm

Button-combo input model (derived from `0x08003B68` and `0x080174E4`):

```
raw = ldrh(0x04000130)          ; GBA KEYINPUT, active-low, 10 bits
held_active_high = (~raw) & 0x3FF
pressed = held_active_high & ~previous_held
stored at: gameplay held = 0x03000EF8 (u16)
```

Key-bit mask (standard GBA):

```
A=0x001  B=0x002  Select=0x004  Start=0x008
Right=0x010  Left=0x020  Up=0x040  Down=0x080
R=0x100  L=0x200
```

Observed mask values (debugger, core paused one second into the hold):

| Combo pressed | KEYINPUT (active-low) | Held mask at 0x03000EF8 |
|---|---|---|
| L+R+Select+B (published door code) | 0x00F9 | **0x0306** |
| L+R+Select+A (undocumented) | 0x00FA | 0x0305 |
| L+R+Select+Start (undocumented) | 0x00F3 | 0x030C |
| Select+L (control test) | 0x01FB | 0x0204 |
| none | 0x03FF | 0x0000 |

The published trigger is therefore the exact active-high mask `0x0306`
(L=0x200 | R=0x100 | Select=0x004 | B=0x002), held for ~2 s. No literal
`0x0306` comparison is present in the Thumb code; the game checks individual
key bits against a configurable EWRAM key map (base `0x0200004C`) and uses a
duration counter, consistent with the README-style published descriptions.

## 6. Tables

**Published in-game cheats (all from GameFAQs archived 2018, supercheats,
gamegenie, Neoseeker walkthrough):**

| Effect | Trigger | ROM verification |
|---|---|---|
| Pass locked doors without the switch | Hold `L,R,SELECT,B` 2 s at door; "Trust No One" voice + B&W flash | **Mask 0x306 verified in RAM**; effect gated on door proximity (see §8) |
| Cheat menu: unlimited health, unlimited ammo, mission select | Beat first 15 missions on **Graduate**, then Start Game | Save-bit unlock; no input code |
| Veteran difficulty | Beat first 15 missions on Graduate; Start Game → past cheat menu → choose Veteran | Save-bit unlock; no input code |
| 3 bonus missions | Beat first 15 missions on any difficulty except Initiate | Save-bit unlock; no input code |

**Documented button combos (read from the in-game Options/Controls screen):**

| Action | Buttons |
|---|---|
| Free look | `L + R + D-pad` |
| Zoom | `L + R`, then Up/Down |
| Holster / Unholster | `Select + A` |
| Night vision | `Select + B` |
| Pause / Map | `Start` |
| Change weapon / Jump / Fire | mapped on-screen (Type A/B layout) |

**Unverified published material:** GameHacking.org's `GameShark/CodeBreaker`
entries (Master Code, "Access All Cheats+Missions", "Skip Mission [L+B]",
etc.) are memory-edit cheats and are out of scope; none were entered.

## 6b. Enumeration

**Button-code space.** The entry surface is the 10-bit GBA keypad
(2^10 = 1024 simultaneous mask values). Every reachable screen was walked and
the complete set of documented/undocumented actions was enumerated from the
in-game controls legend and published sources (table in §6): 8 documented
actions plus 1 undocumented hold-combo (0x306, 2 s at a door). The combo
validator is bit-based (no code table), so there is no printable code list to
exhaust.

**Novel input combinations tested (absent from every published list):**
`L+R+Select+A` (mask 0x305, held 2.5 s) and `L+R+Select+Start` (mask 0x30C,
held 2.5 s) were entered in the emulator. Both produced **no** visible flash,
voice, or state change, while the published `L+R+Select+B` mask (0x306) was
confirmed to be the exact value the game's input handler stores. This bounds
the undocumented action set: changing one bit of the published combo is
rejected.

**Save-unlock space.** The unlocks are progression flags in the 512-byte
EEPROM save. The condition is a threshold ("15 missions completed on a given
difficulty"), not a typed code; per §16.18 this is not a code system and no
brute-force is applicable. Fresh-boot save is entirely 0xFF.

**No password system:** alphabet search, literal table search, and key-mask
search all returned no code-entry surface; negative bounded by the full screen
walk (§7) and by the ASCII/shifted/UTF-16/font-index searches (§11).

## 7. Validation evidence

*Observed* (emulator / debugger / hex dump):
- Boot → language select → title → intro/credits → mission briefing → dialogue
  → gameplay → pause menu → controls screen; screenshots saved in
  `/tmp/opencode/ice9/` (`s_lang`, `intro4`, `menu5`, `game_play`, `pause`,
  `options_screen`, etc.).
- Held-key mask at `0x03000EF8` = `0x0306` while L+R+Select+B is down; 0x0305 /
  0x030C for the undocumented variants; 0 when idle (mGBA `-d` `r/2`).
- EWRAM key map at `0x0200004C` = `{0x0040, 0x0080, 0x0200, 0x0100, 0x0020,
  0x0010, 0x0002, 0x0001, 0x0004, 0x0008}` (Up/Down/L/R/Left/Right/B/A/Select/
  Start).
- No B&W flash detected in 21 rapid screenshots spanning a 4.2 s hold away from
  any locked door (identical RGB-channel difference 118.53 in every frame).
- Savestate diff (before vs. after 2.6 s combo) changed 64,887 bytes, dominated
  by ordinary frame/animation state; the key-mask offset 0x19EF8 changed as
  expected, no isolated "cheat flag" was attributable.

*Derived* (disassembly):
- Input handlers `0x08003B68` and `0x080174E4`, key-state addresses, and key
  bit mapping (§5).
- All PC-relative literal xrefs to the key-state addresses (17 for
  `0x03000018`, 30 for `0x03000EF8`, 48 for `0x03000EFC`).
- No literal `0x0306` comparison and no contiguous 4-mask L/R/Select/B table in
  the code region; the check is bit/test-and-count based.

*Inferred* (not fully exercised):
- That the 0x306 hold sets a per-door "unlocked" flag and plays sample 0x33/0x34
  (sound IDs seen in the dispatcher at `0x0801352C` and the combo UI code at
  `0x08026C16`), which is consistent with the published "Trust No One" voice
  and flash. The in-game effect itself was not triggered because the test
  location was not a switch-locked door.
- That the cheat menu/Veteran/bonus-mission unlocks are save-bit flags (from
  published descriptions; the save-gate writer was not isolated).

## 8. Unknowns

- The exact locked-door entity and the RAM flag it sets when the 0x306 combo
  fires; consequently the in-game "Trust No One" voice/B&W flash was **not**
  observed on screen (the published code explicitly requires standing at a
  door that normally needs a switch; the tested area was an early-training
  hedge/door area without such a door). This is a gated-effect limitation, not
  an untested input: the input was entered and its mask verified in RAM.
- The specific EEPROM byte/bit offsets for the three progression unlocks; the
  fresh save is all 0xFF, so no unlocked-state save was available to diff.
- Whether any font-indexed menu string (e.g., a hidden debug label) exists that
  uses a non-ASCII encoding not covered by the mappings tried; the visible
  menu set was enumerated visually instead.

## 9. Tooling

* `file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings -t x`, `grep -abo`.
* `arm-none-eabi-objdump -D -b binary -marm -M force-thumb` with
  `--adjust-vma=0x08000000`.
* Python 3 + Capstone 5.0.7: PC-relative literal xref scanner, BL scanner,
  key-mask/literal search (`/tmp/opencode/ice9/*.py`).
* mGBA SDL (`mgba -3 -d`) under Xvfb `:319` + openbox; its pty debugger driven
  through a UNIX-socket bridge (`dbgserver.py`, `dc.py`) for `r/2`, `x/2`, `x/4`,
  `watch/r`, `c` and SIGINT pause. GDB stub was avoided because TCP 2345 was
  held by another analysis session.
* mGBA savestates (`.ss1`–`.ss3`): PNG with zlib `gbAs` chunk; decompressed with
  Python `zlib` and byte-diffed (`ssutil.py`) for RAM evidence.
* `xdotool` XTEST key events, `scrot`, ImageMagick `convert` for screenshots.
* Web: `web.archive.org` snapshot of GameFAQs cheats (2018), live search
  snippets for supercheats/gamegenie/Neoseeker/GameHacking.org. Fetched pages
  were treated as data; no prompt-injection payload was encountered.

## 10. Legal note

No ROM binary or extracted game assets are redistributed. Only hashes,
addresses, input masks, and original analysis notes are published.
