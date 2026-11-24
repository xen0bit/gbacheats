# Super Mario World: Super Mario Advance 2 (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Super Mario World: Super Mario Advance 2/Super Mario World: Super Mario Advance 2.gba` |
| Size | 4,194,304 bytes (`0x400000`) |
| Header title | `SUPER MARIOB` (12-byte field) |
| Game code / maker | `AA2E` / `01` (Nintendo), version `0x00` |
| Entry word | `0xEA00002E` — stock `b 0x080000C0` (no cracktro/trainer patch) |
| Complement / checksum | `0x8E` / `0x0000` |
| MD5 | `2f660377581b7e48c06131f56c791b72` |
| SHA-1 | `5101ddf223d1d918928fe1f306b63a42ada14a5e` |
| SHA-256 | `63d9fff04c635990a5c205a99ea64bfa698aa5cb9ec1333360063bbee949a4f3` |

Revision check: the build-date string at file `0x12EE7C` is `01-12-06 09:33:10`, which 3rd party cheat index lists for the **US/Australia** build — consistent with game code `AA2E`. All addresses below are for this exact image.

## 2. Executive summary

This game has **one** developer-intended button code: on the intro screen (the balloon flying over Yoshi's Island, before the *Super Mario Advance 2* title screen), press

> **Right, Select, Left, L, R, Select**

to reveal a build-date banner: `VER. 01-12-06 09:33` (the ROM string carries seconds, `09:33:10`, but the display stops at minutes). The code was found from 3rd party cheat indexes recon, located as a literal `u16` mask table at file `0xD45D0` / ROM `0x080D45D0`, and reversed to a single progressive exact-match validator at ROM `0x08002E30`.

There is **no password system, no on-screen alphabet/keyboard, and no hidden debug menu** in this SKU. The GBA-specific entries on 3rd party cheat indexes are progression-gated unlockables (96-exit warp, coloured Yoshi, EXTRA world, stars) and glitches, not codes. The one CodeBreaker-style "Press Start+L+R" hint found on a fan wiki is a cheat-device activation condition, not an in-game trigger, and is out of scope.

The validator, its RAM flag, and its rejection boundaries were confirmed in mGBA with savestate RAM diffs. A novel 6-press combination (published code with the final `Select` replaced by `B`) was generated, entered, and rejected with RAM evidence; the complete press space was enumerated offline (1,000,000 possible 6-press sequences, exactly 1 accepted).

## 3. How to reproduce

* Emulator: mGBA 0.10.5, `SDL_AUDIODRIVER=dummy`, Xvfb `:319`, 3× scale.
* Keymap (mGBA SDL default): `A`=`x`, `B`=`z`, `L`=`a`, `R`=`s`, `Select`=`BackSpace`, `Start`=`Return`, D-pad = arrow keys. Hold each key ~130 ms with ~120 ms gaps; the validator compares the *exact* held-mask, so press one button at a time.
* Boot the ROM and stay on the first intro scene (balloon with an `M` over the island).
* Press **Right → Select → Left → L → R → Select**. The intro scene switches to the close-up with Mario/Luigi/Peach and prints `VER. 01-12-06 09:33` along the bottom (screenshot `code1.png` / `s_after.png` in `/tmp/sma2/`). The banner disappears as the intro resumes; it is a one-shot flag.
* To repeat experiments: `Shift+F1` saves, `F1` loads (mGBA writes `.ss1`…`.ss10` into the ROM folder). `novel5.ss4` / `novel6.ss5` in the work dir capture the intermediate and rejected states.

Screens walked (each advanced by key input and screenshotted): balloon intro (code screen) → sepia intro → SMA2 title (`Single Player`/`Multiplayer`) → "CHOOSE A GAME" (Super Mario World / Mario Bros., both top-scores 0, no password field) → story dialogs → first playable Yoshi's House scene. No other code-entry surface appeared on any of them.

## 4. Address map

All ROM addresses are `0x08000000 + file offset`; RAM addresses are GBA bus addresses.

| Item | ROM / file | RAM | Notes |
|---|---|---|---|
| Button-mask table | `0x080D45D0` / `0xD45D0` | — | 6 × `u16` active-high masks: `0x10,0x04,0x20,0x200,0x100,0x04` |
| Validator function | `0x08002E30` / `0x2E30` | — | Thumb; prologue `0x2E30`, `bx lr` at `0x2FDC` |
| Literal: table pointer | `0x08002EB8` / `0x2EB8` | — | `0x080D45D0` in validator's literal pool |
| Build-date display branch | `0x08002ECE`–`0x08002FCC` | — | Checks flag, builds 14 sprite records from the string |
| Build-date string | `0x0812EE7C` / `0x12EE7C` | — | ASCII `01-12-06 09:33:10\0` (confirmed literally in ROM) |
| Literal: string pointer | `0x08002F90` / `0x2F90` | — | `0x0812EE7C` (also present in data block at `0xD45EC`) |
| Descriptor data block | `0x080D45DC` / `0xD45DC` | — | `0x03002340`, `0x03007A38`, `&table`, `0x03002F88`, `&string`, `0x03002F90`, `0x03002BC2`, `0x03002B96` |
| Scene-handler pointer table | `0x080D4BA0` / `0xD4BA0` | — | `0x08002E31` (Thumb pointer to validator) |
| Current button mask | — | `0x03002B96` (`u16`) | Active-high; read with `ldrh` by validator |
| Reset byte | — | `0x03002BC2` (`u8`) | Written 0 on validator entry (0 in all sampled states) |
| Scene-state global pointer | — | `0x03007A38` (`u32*`) | Observed value `0x030040E8` in all savestates |
| Accept flag | — | `0x030042BF` = `state+0x1D7` (`u8`) | **0 → 1** on acceptance; observed |
| Progress index | — | `0x030042C0` = `state+0x1D8` (`u8`) | 0…6; observed 5 after five correct presses |
| Scene subtype byte | — | `state+0x14` | Must be ≤10 for display branch (code compares `#10`) |

Savestate layout used for RAM reads: `.ss*` PNG → zlib-decompress the `gbAs` chunk → 397,312-byte raw state; IWRAM (`0x03000000…`) starts at raw offset `0x19000`, so `state_ptr` is at raw `0x20A38` and the flag at raw `0x1D0E8+0x1D7`.

## 5. Algorithm

```
; ROM 0x08002E30 (Thumb)
state = *(u32*)0x03007A38
*(u8*)0x03002BC2 = 0
index = state[0x1D8]
if state[0x1D7] != 0: return              ; already triggered
if ((*(u16*)0x03002B96) & 0x03FF) == 0: return
expected = *(u16*)(0x080D45D0 + index*2)
if (*(u16*)0x03002B96) != expected:
    *(u8*)(state+0x1D8) = 0               ; mismatch -> reset
    return
index++
if index != 6: return
state[0x1D7] = 1                          ; accepted
state[0x1D8] = 0
```

The display branch (`0x08002ECE`) reads `state[0x1D7]`; when nonzero and `state[0x14] <= 10`, it writes 8-byte OAM records for 14 characters from `0x0812EE7C`, producing the visible `VER. DD-MM-YY HH:MM` banner. Semantics: **held buttons, exact mask match, one button per step, non-repeating.**

## 6. Tables

Button mask values (`~KEYINPUT & 0x3FF` convention):

| Mask | Button |
|---:|---|
| `0x001` | A |
| `0x002` | B |
| `0x004` | Select |
| `0x008` | Start |
| `0x010` | Right |
| `0x020` | Left |
| `0x040` | Up |
| `0x080` | Down |
| `0x100` | R |
| `0x200` | L |

Code table at `0x080D45D0` — the single entry:

| Step | Mask | Button |
|---:|---:|---|
| 0 | `0x010` | Right |
| 1 | `0x004` | Select |
| 2 | `0x020` | Left |
| 3 | `0x200` | L |
| 4 | `0x100` | R |
| 5 | `0x004` | Select |

Build-date strings in this image (only the first is present): `0x12EE7C` = `01-12-06 09:33:10` (US/AU). Other regional strings from 3rd party cheat indexes (`0x12C8A8` JP, `0x12DD64` CN, `0x13E91C` EU) are **not** in this ROM at those offsets — this is the US build.

Other notable data: `0x080D6220`–`0x080D623E` is a generic descending list of all ten button masks (`L,R,Down,Up,Left,Right,Select,Start,B,A`), used by UI/input display code, **not** a code table (no validator references it).

## 6b. Enumeration

**Space definition.** The code system is a single fixed-length button sequence. Each of the 6 steps accepts exactly one value from the 10-button mask set; there is no checksum, wildcard, alias, or variable length. Total representable 6-press sequences: `10^6 = 1,000,000`; exactly **1** is accepted. The only state produced is the one-shot flag `state+0x1D7 = 1` (build-date display).

**Validator model.** Reimplemented in Python from `0x08002E30`: accept iff `seq[i] == table[i]` for all `i∈[0,6)`, evaluated as exact active-high masks. Exhaustive run over all `10^6` sequences: **1 accepted**, the published sequence; lengths 1–5 and 7–8 yield 0 (the trigger requires `index == 6`). This is a closed set, not a sample.

**Novel combination generated, entered, and RAM-verified (rejected).**
Generated sequence: **Right, Select, Left, L, R, B** — differs from the published code only in the last press, and appears in no published list (3rd party cheat indexes/3rd party cheat index list no GBA code at all beyond the build-date sequence). Entered on the real intro screen after reloading `Shift+F1` state.

| State | `state+0x1D7` flag | `state+0x1D8` index | Visible build-date banner |
|---|---:|---:|---|
| before code (`state_before.ss1`) | 0 | 0 | no |
| published code (`state_after.ss2`) | **1** | 0 | **yes** (`VER. 01-12-06 09:33`) |
| novel: 5 correct presses (`novel5.ss4`) | 0 | **5** | no |
| novel: wrong 6th `B` (`novel6.ss5`) | 0 | **0** (reset) | no |

The index reaching 5 proves the first five presses were accepted; the reset to 0 on the sixth proves the validator requires the exact final `Select`; the flag remaining 0 proves no effect fired. This is the in-game acceptance/rejection boundary, observed in RAM, not inferred from the table alone.

**Bounds proven by rejection.**
* Wrong final button (above): rejected, index reset 5 → 0.
* Truncated input (5 presses): flag stays 0, index rests at 5 — no trigger at any length < 6.
* Simultaneous extra buttons: validator compares the whole `u16` mask for equality, so a combined mask (e.g. `Right|Select = 0x14`) cannot satisfy any step; this is derived from `cmp r0,r1` at `0x08002E82`.
* One-shot: with flag=1, the entry check at `0x08002E5C` skips all further matching.

**Bounded negative for other button codes / debug menus.**
* An exhaustive pointer scan found **13** 4-byte-aligned pointers to runs of ≥3 consecutive valid `u16` button masks. Twelve are coincidental byte patterns inside unrelated instruction streams (spot-disassembled at `0x08013028`, `0x0806DE90`, `0x0807AB78`, `0x0805D570` — none is a real table reference). The only true code reference is `0x2EB8 → 0x080D45D0`. Therefore exactly one button-code validator exists in the image.
* The validator's table holds exactly 6 entries; there is no action-dispatch branch after the prefix — the sole effect is the flag write at `0x08002EA0`. There are no undocumented action branches to enumerate.
* Screen walk: intro, title, game select, story, and first gameplay screen contain no password/keyboard/cheat entry UI; the build-date banner is the only code-driven screen change.
* Published-source review: 3rd party cheat index lists only the build-date sequence (plus progression glitches/unused stages); 3rd party cheat indexes' 55 entries for this SKU are glitches, unlockables and secrets, with its "Codes" section entries tagged SNES; 3rd party cheat index lists the same unlockables. No other GBA button code is documented.

## 7. Validation evidence

* **Observed (emulator):** build-date banner appears on screen after `Right,Select,Left,L,R,Select` (`code1.png`, `s_after.png`); no banner after the novel near-miss (`novel_rejected.png`). Savestate RAM diffs: flag `0→1` for the published code, flag `0`/index `5→0` for the novel code. Screen walk screenshots `walk_*.png`.
* **Derived (disassembly):** table contents and exact-match validator at `0x08002E30`; literal pointers at `0x2EB8`/`0x2F90`; Thumb function pointer `0x08002E31` at `0xD4BA0`; display branch reading the flag and the ASCII string.
* **Derived (literals):** the build-date string `01-12-06 09:33:10` exists at file `0x12EE7C` and matches the visible banner's date/time to the minute.
* **Inferred / not exercised:** that the flag is consumed only by the build-date display branch (the branch was read, not breakpoint-traced). The meaning of the zeroed byte `0x03002BC2` is unknown (0 in all sampled states).

## 8. Unknowns

* Whether any progression-gated feature (96-exit warp, EXTRA world, Luigi availability) is driven by a separate code path was not exhaustively reversed — those are save/progress flags, not in-game codes, and are out of scope.
* The GDB stub was unreliable (memory access failures / port closing after first client); RAM evidence was obtained by savestate diffing instead. No live breakpoint trace of the flag reader was performed.
* Only the US/`AA2E` revision was analysed; other regional builds have different build-date strings and different code offsets.

## 9. Tooling

* `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings` for Phase 0.
* Python 3 + `struct`/`zlib` for pointer/BL scans, button-mask run enumeration, exhaustive space check, and savestate `gbAs` extraction/diff.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for disassembly.
* Capstone 5.0.7 (available; literal-load scanning cross-checked against objdump).
* Web recon: 3rd party cheat index cheats (via Wayback Machine), 3rd party cheat indexes. Fetched pages were treated strictly as data.
* mGBA 0.10.5 under Xvfb `:319` + openbox, `SDL_AUDIODRIVER=dummy`; xdotool XTEST input; scrot screenshots.
* Work artifacts in `/tmp/sma2/` (`code1.png`, `s_after.png`, `novel_rejected.png`, `state_*.ss*`, `novel*.ss*`, `walk_*.png`). No ROM or copyrighted assets are redistributed in this report.
