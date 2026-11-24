# Mission: Impossible – Operation Surma (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Mission: Impossible – Operation Surma.gba` |
| Size | 4,194,304 bytes (`0x400000`) |
| Header title | `MIMPOSSIBLE` |
| Game code | `AIHE` (rev `00`) |
| Maker | `70` (Atari) |
| Entry word | `0xEA00002E` — stock `b 0x080000C0` |
| Version | `0x00` |
| MD5 | `6ce6741e0a522351047b79851cd2d651` |
| SHA-1 | `50e09660f2d9588f8cad8c43fca719cc78006e1a` |
| SHA-256 | `9bb0e2f8573a7ef64f73f65abd05c14e537c08264348417169cc32561dcdf876` |

Phase 0 result: exactly **one** GBA header (Nintendo logo at file `0x4`, header at `0x0`). No appended trainer, no cracktro, no multiboot stub, no second image. Stored header checksum `0x0000` (computed `0x0571`) and complement byte `0x8F` (computed `0xA8`) are the normal rebuilt-header artifact; the entry branch is untouched stock. The GBA port is by **M4 Limited**, a different engine from the console versions by Paradigm.

## 2. Executive summary

This ROM has **no password/cheat-text entry system at all**. All text is font/tile-indexed; there is no ASCII or UTF string bank (28,088 `strings` entries at `-n 4`, zero keyword hits). What it does have is:

1. **A developer button code: `A + B + SELECT + START` (simultaneous, edge-triggered) performs a full soft reset** to the legal screen. This is a single, exact-match chord hardcoded in the game's only key-read function at `0x08002E18`; the check is `held == 0x0F` at `0x08002E34`. Adding *any* other held button prevents it. Confirmed in mGBA with RAM evidence and rejection bounds.
2. **A built-in mission/level-select screen**: main menu → LOAD GAME → `-MISSIONS-` → `SELECT MISSION:` listing five missions. Level 1 is selectable; Levels 2–5 are greyed and skipped by the D-pad (progress-gated). This is the GBA equivalent of the console "Levels" option, but it is reachable through the normal UI without any code.
3. The widely published *"highlight Jasmine Curry in Profiles, hold L+R+Y+X (or B+Y)"* level-select code is a **GameCube/PS2/Xbox** code for the Paradigm engine. The GBA SKU has no "Profiles" menu and no such chord; it does not apply. Every published **GBA** code found on the web is an Action Replay / CodeBreaker / GameShark memory-edit code and is out of scope for this engagement.

## 3. How to reproduce

* Emulator: mGBA (`mgba -3`), `SDL_AUDIODRIVER=dummy`, Xvfb `:317` + openbox. Keymap A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows.
* Boot → Atari splash → legal/copyright screen → language select (English / Français / Español) → **PRESS START** → main menu.
* Main menu items: `NEW GAME`, `LOAD GAME`, `SFX ON`, `MUSIC ON`. (Four items only — there is no `Profiles` or `Levels` entry.)
* Mission select: choose `LOAD GAME` (enabled once a save exists) → `-MISSIONS-` → `SELECT MISSION:` → `Level 1: Sansara Prison` (usable), `Level 2: Embassy Row`, `Level 3: Yugarian Embassy`, `Level 4: Surma HQ`, `Level 5: Algo's Mansion` (all four dimmed and skipped).
* **Reset code**: on any screen, press and hold `A+B+Select+Start` together. Observed: screen immediately cuts to the white legal/copyright screen, then language select on Start. Held-mask requirement is exact.
* RAM evidence: mGBA `.ss1` savestates are PNGs with a zlib `gbAs` chunk. Decompressed length `0x61000`; IWRAM at raw `0x19000` (→ GBA `0x03000000`), EWRAM at raw `0x21000` (→ GBA `0x02000000`). Key state: `0x03006110` = newly-pressed mask (u16), `0x03006112` = held mask (u16), both active-high bits `A=1,B=2,Select=4,Start=8,Right=0x10,Left=0x20,Up=0x40,Down=0x80,R=0x100,L=0x200`.

## 4. Address map

| Address (ROM) | Meaning |
|---|---|
| `0x08002E18` | Only KEYINPUT reader in the whole ROM. Literal `0x04000130` at `0x08002E78`; literal `0x03FF` at `0x08002E7C`. |
| `0x08002E34` | `cmp r0,#15` → `held == 0x0F` (A+B+Select+Start) edge-triggered soft-reset branch. |
| `0x08002E3E`–`0x08002E6C` | Reset body: calls `0x08002A64`, `0x08007524`, `0x0800734C`, clears globals, `0x0801BA10` memcpy, then returns to boot. |
| `0x08002EBC(mask,frames)` | "wait for key held" helper. Only four callers (`0x08009FCC`, `0x08009FE2`, `0x08009FF8`, `0x0800A00E`), all with mask `9` (A+Start) for a timed scene-skip — not a cheat. |
| `0x08002EE4(mask)` | "is any mask bit held" helper; only two internal callers. |
| `0x08005AB8` | Copies key state into input-history struct; base pointer at `0x03002618` (observed `0x02003AC4`), stride `0x3C`, `+4`=pressed, `+6`=held. Pointer is zeroed by the reset. |
| `0x08009EB0`, `0x08009F9C` | Menu/intro state handlers referenced through Thumb pointer tables near `0x08009E98`. |
| `0x080A2D58`–`0x080A2E15` | Font/tile charmap tables; `0x08386814` is the pointer table into them. Text is tile-indexed, hence no ASCII strings. |
| `0x030061F0` | Screen/state word used by menu handlers. |
| `0x030061AC` | `0xFFFF` on the mission-select screen. |
| SRAM | 512 bytes, magic `SSIM` at save offset `0x1FC`. |

## 5. Algorithm

The single input routine, exactly as disassembled at `0x08002E18`:

```
raw     = *(u16*)0x04000130          ; active-low KEYINPUT
held    = 0x3FF ^ raw                ; active-high, 10 buttons
new     = held & ~prev_held          ; edge
prev_held = held
*(u16*)0x03006110 = new
*(u16*)0x03006112 = held
if (held == 0x0F && new != 0)        ; <-- the ONLY chord check in the ROM
        full_soft_reset()
```

The reset is therefore **exact-match** and **edge-triggered**: the chord must be pressed while no other button is held, and at least one of its four buttons must be a fresh press. All other gameplay/menu input is read through the two globals and single-bit helpers; there is no second chord table, no password validator, no key-mask sequence array.

## 6. Tables

Button bits (active-high, from the XOR with `0x3FF`):

| Bit | Button | Bit | Button |
|---:|---|---:|---|
| `0x001` | A | `0x040` | Up |
| `0x002` | B | `0x080` | Down |
| `0x004` | Select | `0x100` | R |
| `0x008` | Start | `0x200` | L |
| `0x010` | Right | | |
| `0x020` | Left | | |

Codes found (complete):

| Code | Effect | Gate |
|---|---|---|
| `A+B+Select+Start` (`held == 0x0F`, fresh press) | Full soft reset → legal screen | Exact match: any extra held button rejects it |

Mission-select table (rendered, five fixed entries):

| Index | Label | Selectable on a fresh save |
|---:|---|---|
| 0 | `Level 1: Sansara Prison` | Yes |
| 1 | `Level 2: Embassy Row` | No (dimmed, cursor skips) |
| 2 | `Level 3: Yugarian Embassy` | No |
| 3 | `Level 4: Surma HQ` | No |
| 4 | `Level 5: Algo's Mansion` | No |

## 6b. Enumeration

**Button-code space.** The held mask is 10 bits, so 1,024 representable chords. Static analysis of the *only* KEYINPUT reader (`0x08002E18`–`0x08002E76`) shows exactly **one** accepted value: `0x0F`. The full set of actions dispatched by chord is `{0x0F → soft reset}`; the space is therefore a singleton and **no novel unpublished chord can exist** — minting one is impossible by construction, which is the complete characterisation required by §0.2 for a hardwired-chord system.

Bounds proven by in-game rejection (main menu, savestate RAM evidence; `histptr` = u32 at `0x03002618`, `0xC43A0002` normally, `0x00000000` after reset; EWRAM diff ≈ 40,910 bytes on reset):

| Input | EWRAM diff | histptr after | Result |
|---|---:|---|---|
| `A+B+Select+Start` | 40,910 | `00000000` | **RESET** |
| R held first, then A+B+Select+Start | 63,795 | `C47C0002` | rejected |
| L held first, then A+B+Select+Start | 63,795 | `C47C0002` | rejected |
| Up held first, then A+B+Select+Start | 112 | `C43A0002` | rejected |
| A+B+Select (no Start) | 63,792 | `C47C0002` | rejected |
| A+B+Start (no Select) | 63,792 | `C47C0002` | rejected |
| A+B only | 63,792 | `C47C0002` | rejected |
| L+R+A+B | 63,792 | `C47C0002` | rejected (starts NEW GAME via A, not a code) |

The first three rejections prove the exact-match bound directly: a superset chord (`0x10F`, `0x20F`, `0x04F`) is refused because `held != 0x0F`.

**Mission-select space.** Five entries, one initially selectable. Moving Down four times from Level 1 leaves the cursor on Level 1 (screenshot `mission_lvl5_selected.png`), proving Levels 2–5 are not reachable on a fresh save. Chords tested on this screen (`L+R+A+B`, `L+R+A`, `L+R+B`, `L+R+Start+Select`, `L+R+Up+Down`, `L+R+Start`, `L+R+Select`, `A+B+Select+Start`) produced no additional selectable rows; A/B simply perform the normal menu actions (start mission / go back). Unlock is progress/save based, not input based.

**Published-code verification.** Every GBA code on 3rd party cheat indexes are an Action Replay or CodeBreaker memory-edit code (e.g. infinite health `32003B4C 007C`, stop timer `32003C98 0003`) — out of scope. The only in-game code published anywhere for this title is the console level-select chord (`L+R+Y+X` GameCube, `L+R+B+Y` Xbox/PS2, with "Jasmine Curry" highlight). It was tested in its GBA-plausible forms (`L+R+A+B`, `L+R+A`, `L+R+B`, reversed order) on the main menu and mission-select screen; no hidden row or screen appeared. The GBA build has no Profiles menu at all, so the prerequisite for that code does not exist in this SKU. No prompt-injection was encountered in fetched pages; all fetched text was treated as data.

## 7. Validation evidence

* **Derived** — `0x08002E18` disassembly: sole `KEYINPUT` read (`ldr r0,[pc,#0x58] @ 0x8002E78` = `0x04000130`); `eors r0,r1` with `0x03FF` produces active-high `held`; `cmp r0,#15` at `0x08002E34` gates the only special branch. No other chord check exists in this function or in the input helpers (`0x08002EBC`, `0x08002EE4`) — the latter's only four callers all pass mask `9`.
* **Observed** — emulator screenshots: `t02_after_abss.png` (legal screen after chord), `missions_01.png` (five-mission select), `mission_lvl5_selected.png` (cursor cannot leave Level 1), `walk_*.png` (all main-menu options and toggles), `load_01.png` (LOAD GAME screen). Savestate RAM diffs: `state_before_reset.raw` vs `state_after_reset.raw` (IWRAM 2,158 bytes, EWRAM 40,910 bytes changed; input-history pointer cleared).
* **Inferred** — Levels 2–5 unlock by completing earlier missions (save-progress flag); the 512-byte SRAM with `SSIM` magic holds the progress, but the exact flag bit was not isolated. The significance of the `0x08002EBC(9, N)` A+Start timed skip is inferred to be an intro/cutscene skip.

## 8. Unknowns

* Exact SRAM layout / bit position that unlocks mission rows 2–5; not isolated because completing a mission was not performed.
* Whether the `A+B+Select+Start` reset is exposed to players or is purely a leftover developer/debug function (behaviour is proven; intent is inferred).
* The `0x08002EBC(mask=9)` caller at `0x08009F9C` is a specific scene handler; its exact in-game trigger was not exercised.
* Font charmap at `0x080A2D58`–`0x080A2E15` was decoded only far enough to read the rendered VRAM glyph tiles for the visited screens; the full glyph↔code table was not transcribed.

## 9. Tooling

* `strings -a -t x -n 3/4/5/8`, `xxd`, `grep -abo` — text reconnaissance (all encodings negative).
* Python + Capstone 5.0.7 — PC-relative literal scans for `0x04000130`, key-global xrefs, BL caller scans, mask-immediate census.
* `arm-none-eabi-objdump -M force-thumb` — disassembly of `0x08002E18`, `0x08009E80`–`0x0800A520`, `0x080034B4`, `0x0800606C`.
* Pillow — rendered VRAM tiles from savestate raw state to decode the tile-indexed font (read `NEW GAME`, `LOAD GAME`, `SFX ON`, `MUSIC ON`, `MISSION: IMPOSSIBLE`, `SELECT MISSION:`, all five level names).
* Python savestate extractor (`zlib.decompress` of the PNG `gbAs` chunk) for IWRAM/EWRAM RAM evidence and before/after diffs.
* mGBA under Xvfb `:317` + openbox with `SDL_AUDIODRIVER=dummy`; `xdotool` XTEST input helpers.
* Web sources: 3rd party cheat indexes, 3rd party cheat index walkthrough, Multiplayer.it — used only to find and classify published codes.
* Cleanup: all emulator processes were terminated by PID (`mgba`, `openbox`, `Xvfb` on `:317`); all generated `.sav` and `.ss1`–`.ss9` files were removed from the ROM folder. `roms/INDEX.md` was not modified.
