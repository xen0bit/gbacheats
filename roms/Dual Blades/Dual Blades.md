# Dual Blades (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Dual Blades.gba` (4,194,304 bytes / 0x400000) |
| `file` ID | Game Boy Advance ROM image: "DUAL BLADES" (AB9E5N, Rev.00) |
| Header title | `DUAL BLADES` (0xA0) |
| Game code | `AB9E` (0xAC), maker `5N` (0xB0) |
| Version | 0x00 (0xBC); complement 0xDC; header checksum 0x0000 |
| Entry word | `0xEA00002E` = stock `b 0x080000C0` crt0 (§16.1: not a cracktro) |
| Dev string | `DualBlades12July2002Mast19` at file 0x1C0 |
| Embedded headers | exactly **one** Nintendo-logo hit, at file 0x4 → single retail image, not a multicart, no appended trainer (no `TRAINER`/`GAMESHARK`/`CODEBREAKER` strings) |
| MD5 | `efa8473a8125181965f08156c95cc6bb` |
| SHA-1 | `b37c522b48e80d93231b491b025663f1624e3d75` |
| SHA-256 | `8ee449d6c8cade380f1d795ada1106cddb9f7eb66cdce0f15ce2e8dcc12dd850` |

Only GBA SKU exists (Vivid Image / Metro3D, 2002, NA+EU); no console version, so no cross-platform code contamination is possible. An external Venom +4 **trainer** exists for this game, but it is a ROM patch, not an in-game cheat — explicitly out of scope.

## 2. Executive summary

This is a **button-code / unlockable** game, not a password game. There is no code-entry screen and no password validator: the ROM contains **zero** occurrences of "password", "cheat", or "enter code", and every menu was walked without finding such a screen.

The one developer-intended input cheat that is real and confirmed in this exact ROM is the **Impossible difficulty button code** on the Options screen: with the cursor on `Difficulty`, press D-pad **← ← ← ← → → ← → then B**. On a cleared save the difficulty cycle contains only Easy/Normal/Hard/Deadly; after the code a fifth value, **Impossible**, appears and stays selectable. This is repeatedly RAM/screen verified below.

A second class of content — Alperen as a playable fighter and the Counter/Crazy/Transform/Maximum modes in the EXTRAS menu — is **save-flag gated unlockable content** (§16.18), reached by completing game modes, not by a typed code. The published per-character "EX version" sequences are completion-gated; one was attempted and produced no unlock (reported as gated, not as a code).

No hidden debug screen exists. The ASCII strings that look like debug leftovers (`TRAINING MENU`, `FIGHT MENU`, `VS MENU`, `EXTRAS`, `BACKUP OPTIONS`, `Dual Blades SGM`, `BASIC COMBINATIONS`) are the game's ordinary menu-name/save-message table at file `0x309DD0–0x309F50` (36 NUL-terminated labels), not a debug menu.

**Deliverables for §0.2:** code space = a fixed-length 9-press sequence over the 10 GBA button masks; an **undocumented accepted sequence** (extra leading `A`) was generated and confirmed in-game; bounds were proven by six rejected in-game inputs.

## 3. How to reproduce

Emulator: `mgba -3 -d` (CLI debugger over PTY) on `Xvfb :315`, `SDL_AUDIODRIVER=dummy`, 1024×768 root, window managed by `openbox`. A byte-identical copy of the ROM was run from `/tmp/dualblades/DualBlades.gba` so no emulator artifacts were written into the ROM folder.

mGBA SDL keymap (RAM-verified by reading `0x04000130` while holding each key):

| GBA | key | active-high mask |
|---|---|---|
| A | `x` | 0x001 |
| B | `z` | 0x002 |
| Select | `BackSpace` | 0x004 |
| Start | `Return` | 0x008 |
| Right | `Right` | 0x010 |
| Left | `Left` | 0x020 |
| Up | `Up` | 0x040 |
| Down | `Down` | 0x080 |
| R | `s` | 0x100 |
| L | `a` | 0x200 |

**Exact menu path:** title → `START` → ARCADE character select → `B` → main menu → `DOWN`×4 → `OPTIONS` → `A`. Cursor is on `Difficulty`. (The title menu drops into an attract demo after a few idle seconds; use immediate input or `load`/`save` slots.)

**Code entry:** press `LEFT,LEFT,LEFT,LEFT,RIGHT,RIGHT,LEFT,RIGHT,B` with ~60 ms holds and ~40 ms gaps. A successful code **consumes the final B** (the Options screen stays up); a failed code lets B exit Options. Then press `RIGHT` repeatedly on `Difficulty` to reveal Impossible.

**Clean baseline:** OPTIONS → `BackUP...` → `Clear Data` → `Yes` resets unlock flags. Baseline cycle is Easy/Normal/Hard/Deadly (artifact `clean_cycle.png`); after the code it is …Deadly → **Impossible** → Easy… (artifacts `ok_cycle.png`, `cyc_now.png`, `v4c_*.png`).

Published sources consulted: GameFAQs FAQ by Kuno (2002-11-28, "Cheats: as of yet there aren't any"), gmania, games-cheats.org, cheatingdome.com, VGChartz, spmoves.com. The gmania/VGChartz wording resolves the ambiguity in the cheatingdome shorthand: the nine presses are **D-pad Left/Right**, not shoulder L/R (the shoulder interpretation was tested first and rejected — `shot_07`…`shot_12`).

## 4. Address map

| Address | Meaning | Evidence |
|---|---|---|
| `0x08000000` | crt0 entry (`b 0x080000C0`) | derived, header + disassembly |
| `0x0800A178` | input sampler: `held = ~KEYINPUT & 0x3FF`; `pressed = held & ~prev` | derived, Thumb disassembly |
| `0x0800A17A` | `ldr r0,[pc,#0x1C]` → literal `0x04000130` (KEYINPUT) at pool `0x0800A198` | derived |
| `0x0800A18E` | `strh pressed` to `*0x03001AF8`; `0x0800A190` `strh held` to `*0x03001AF0` | derived |
| `0x03001AF0` / `0x03001AF8` | IWRAM halfwords: active-high **held** / **pressed** mask | derived + observed via `r/2` |
| `0x04000130` | KEYINPUT, active-low; idle `0x03FF` | observed |
| `0x08309DD0–0x08309F50` | menu-name / save-message ASCII table (`TRAINING MENU`, `EXTRAS`, `Dual Blades SGM`, …) | derived, `xxd` |
| `0x0830A812–0x0830A88A` | difficulty-name labels at 0x18 stride: `Difficulty, Easy, Normal, Hard, Deadly, Impossible` | derived, `strings` |
| `0x08013A18` | code ref to `0x08309DD0` (`TRAINING MENU`) | derived |
| `0x0801435C` | code ref to `0x08309E60` (`EXTRAS`) — EXTRAS menu builder; entry gating read at `0x080143E0` | derived |
| `0x08311A10–0x08311A8C` | unlock notification strings (`Alperen_is Selectable!`, `Mega Move_Activated!`, `Crazy Mode_Activated!`, `Transform Mode_Activated!`, `Counter Mode_Activated!`) | derived, `strings` |
| `0x083A4E28` | sole u16-structure hit for the code pattern; lies in a graphics/palette region — **not** a code table | derived, rejected |
| SRAM `0x0E000000` | read `0xFFFF…` while running; game keeps its working save in EWRAM/IWRAM and writes the 512-byte `.sav` on save/exit | observed |

File-offset → ROM address: `0x08000000 + file_offset`. `strings -t x` reports hex file offsets; e.g. `strings` hit `30a88a` → `0x0830A88A` (the earlier mistaken `0x080A88A` search returned nothing — recorded so the next analyst does not repeat it).

## 5. Algorithm

Input sampling (derived from `0x0800A178`):

```
held   = (~KEYINPUT) & 0x3FF        ; active high
pressed = held & previous_held
*0x03001AF8 = pressed               ; edge mask for this frame
*0x03001AF0 = held                  ; for next-frame edge detection
```

The Impossible unlock is a **fixed-length button-sequence match** performed in the Options screen's input handler, not a password/checksum system. Observed semantics:

* expected sequence (active-high masks): `0x20,0x20,0x20,0x20,0x10,0x10,0x20,0x10,0x02`;
* matcher is **suffix/rolling-history** tolerant: one extra press *before* the sequence (`A`) and extra presses *after* it (`B`, `A`) are accepted;
* it is **not** tolerant of a wrong length (`3×Left`, missing final press), a wrong final button (`A` instead of `B`), or prefix buttons that change menu context (`B`, `Up`);
* success sets a persistent unlock bit that adds `Impossible` (index 4) to the difficulty selector and consumes the terminating `B` press;
* the literal sequence is **not stored as a contiguous u16/u32/u8 table in the ROM** (all encodings searched — see §6b). The matcher therefore uses a counter/shift-register construction whose code address was not isolated; this is stated as an unknown, not papered over.

Unlockable modes are a separate, save-flag-driven system (§16.18): the EXTRAS menu at `0x080143xx` builds five rows from bytes in the save record; the notification strings at `0x08311A10+` are emitted by completion handlers. No button input reaches those setters from the screens walked.

## 6. Tables

**Published button codes (all verified against the ROM text/web, then tested in emulator where feasible):**

| Feature | Screen | Sequence | Status |
|---|---|---|---|
| Impossible difficulty | Options / Difficulty | `← ← ← ← → → ← → B` | **CONFIRMED** (multiple runs, clean save) |
| Kanae EX version | Character select, Kanae highlighted | hold `R`, `← ← ↓ ↓ → ↑`, `Start` | published; attempted — no unlock; completion-gated per published note |
| Efe EX | Character select | hold `L`, `↑ ↓ ↑ ↑ ← ←`, `Start` | published, not individually verified (same gated family) |
| Brandon EX | Character select | hold `L`, `↓ ↓ ↑ ↑ B →`, `Start` | published, same gated family |
| Shin EX | Character select | hold `L`, `B B → → ↓ ↓`, `Start` | published, same gated family |
| Duke EX | Character select | hold `R`, `↑ ↑ ↑ B B ↓`, `Start` | published, same gated family |
| Jaman EX | Character select | hold `R`, `↓ ↑ ↓ ↑ → B`, `Start` | published, same gated family |
| Nagasapa EX | Character select | hold `L`, `→ → → ↑ ↑ ↑`, `Start` | published, same gated family |
| Rungard EX | Character select | hold `R`, `B ↓ → → ↓ B`, `Start` | published, same gated family |

**Unlockables (gameplay-gated, not codes):** Counter Mode (clear Arcade with 4 characters), Transform Mode (complete Time Attack), Crazy Mode (complete Survival), Alperen (clear Arcade on Normal+ with all characters), MEGA powers (complete Combo Mode). Corresponding strings are at `0x08311A10+`; the EXTRAS menu builder is `0x080143xx`.

**Menu inventory walked (RAM/screen-verified):** title; main (ARCADE / VS / BATTLE / TRAINING / OPTIONS); ARCADE character select (8 portraits + `?` hidden slot); CHARSELECT→POWER SELECT; TRAINING (`NORMAL MODE`, `COMBO MODE`); OPTIONS (Difficulty, Bouts, Fight Speed, Rage Mode, Healing, Music, Buttons, BackUP…, Exit); BACKUP OPTIONS (Exit, Load Data, Save Data, Auto Save/Load, Clear Data, CLEAR BACKUP?/No/Yes); in-fight HUD; attract/demo. **No code-entry or debug screen exists in any of these.**

## 6b. Enumeration

**Space definition.** The only real cheat is a 9-press sequence over the 10 active-high GBA masks `{0x001,0x002,0x004,0x008,0x010,0x020,0x040,0x080,0x100,0x200}` → 10^9 nominal press strings, but the matcher only accepts the one 9-press suffix `LLLLRRLRB`, with a small alias set around it. There is no field/checksum structure and no password alphabet; therefore no encoder exists to mint an arbitrary "different effect" code. (Every `password|cheat|code|decode|generator|valid` string search returned 0 hits.)

**Literal-table search counts (complete negative result).** Across all 4 MiB:
* published sequences as `u16` LE/BE, `u32` LE/BE, `u8`, button-index `u8`/`u16`, nibble-packed, and with L/R modifier ORed into every press: **0 full-sequence hits**;
* structural scan of all 4,194,304 byte windows for the pattern `A,A,A,A,B,B,A,B,C`: 20 hits, all in graphics/palette regions (e.g. `0x808E8E8`, `0x83CE783`);
* same structural scan over aligned `u16` words restricted to values ≤0x3FF: **1 hit**, `0x083A4E28 = {0,0,0,0,1,1,0,1,0x100}`, in a graphics bank — rejected as a code table;
* ASCII `LLLLRRLRB` and variants: 0 hits.

**Novel code (absent from every published list), generated and confirmed in-game:**

```
A, ←, ←, ←, ←, →, →, ←, →, B        (10 presses; published code with one extra leading A)
```

From the clean baseline (4 difficulties), entering this sequence left Options open (B consumed) and produced the 5-value cycle including **Impossible**. Evidence: automated tester `variant.py` reported `UNLOCK` for this sequence; screenshots `v4c_0.png … v4c_4.png`. Two further unpublished variants also unlock and were confirmed: published code + trailing `B` (`UNLOCK`) and published code + trailing `A` (`UNLOCK`). (These three spellings are behaviourally identical aliases, §16.4b — not three distinct features.)

**Bounds proven by in-game rejection** (each from the clean baseline, `variant.py` / manual entry):

| Input | Result |
|---|---|
| `← ← ← → → ← → B` (3 Lefts) | reject — final B exited Options, no Impossible |
| `← ← ← ← → → ← → A` (wrong final button) | reject |
| `← ← ← ← → → ← →` (no final press) | reject |
| `B` prefix + published code | reject (B changes menu context first) |
| `↑` prefix + published code | reject (Up changes highlighted field) |
| shoulder `L L L L R R L R B` (wrong button class) | reject |
| Kanae EX sequence from char select | reject / gated (no unlock observed) |

The clean baseline after `Clear Data` showed exactly 4 difficulties; after each accepted sequence it showed exactly 5. This is the in-game accept/reject boundary.

## 7. Validation evidence

* **Observed (emulator + RAM):** KEYINPUT values for all 10 keys via `r/2 0x04000130`; Options/Difficulty cycle before and after `Clear Data` and after each code (`clean_cycle.png`, `ok_cycle.png`, `v4_cycle.png`, `cyc_now.png`); Options stays open when B is consumed vs transitions out when it is not; all menu screens in §6; `0x03001AF0/0x03001AF8` read as 0 with no keys held; SRAM window `0x0E000000` all `0xFF` while running.
* **Derived (disassembly):** input sampler at `0x0800A178` and its two globals; EXTRAS menu builder at `0x080143xx` with a save-byte gate; menu-name table at `0x08309DD0+`; unlock strings at `0x08311A10+`; single GBA header; stock crt0.
* **Inferred (labelled):** matcher implemented as a rolling 9-entry history with suffix tolerance (behaviour fits the alias set but the exact code site was not isolated); unlock persistence lives in the save record, although the `.sav` bytes at 0x00–0x3F were identical across the clean/unlocked states and mGBA only flushes SRAM on save/exit.

## 8. Unknowns

* Exact validator/matcher routine address and the unlock flag's bit/byte offset. Static literal searches for the press masks failed; no breakpoint was obtained on the write, so the matcher internals remain inferred from black-box behaviour. The input sampler and all data addresses are nonetheless exact.
* The save-record layout: 512-byte `.sav`, first 16 bytes are byte-reversed `Dual Blades SGM`, bytes 0x00–0x3F hold settings and a 32-bit checksum at 0x3C; remaining bytes 0xFF. Unlock bit positions were not isolated.
* The 8 per-character EX-version sequences are published but completion-gated; only Kanae's was attempted, with a negative result. Whether some subset is reachable without completion was not proven.
* "MEGA/SECRET POWER" moves (`SECRET_WEAPON`, `SECRET POWER!`, `ETERNAL DARKNESS`, …) are combo-list move names at file `0x30A434+` and `0x3FAxxx`, not cheats; no hidden move-unlock code exists beyond Combo Mode completion.
* No hidden debug screen was found; §16.3 "no system" is the supported classification for a code-entry screen, and §16.18 "gated feature" for unlockables.

## 9. Tooling

* `binutils-arm-none-eabi` (`arm-none-eabi-objdump -M force-thumb`) — disassembly of `0x0800A130–0x0800A1A0`, `0x080142C0–0x08014480`.
* Python 3 + Pillow — header parse, `strings` offset/ROM-address conversion, exhaustive literal/structural code searches (all 4 MiB), savestate `gbAs` zlib parser (`ss.py`), image-diff classifier for Impossible detection.
* Custom `dbgdaemon.py` — persistent mGBA `-d` CLI debugger over a PTY, command file `cmd.txt`, response log `dbgout.txt`. (`-g` on this build exposes GDB RSP on stdio, not TCP 2345 and halts the core; `-d` was used instead.)
* `key.py`, `probekey.py`, `nav.py`, `codetest.py`, `variant.py` — XTEST key injection on `DISPLAY=:315`, KEYINPUT probes, navigation, controlled code tests.
* mGBA savestates `DualBlades.ss1…ss9` in the work dir (all work artifacts are outside the ROM folder).

Legal note: only hashes, addresses, algorithms, and original findings are published here; no ROM bytes or copyrighted assets are redistributed.
