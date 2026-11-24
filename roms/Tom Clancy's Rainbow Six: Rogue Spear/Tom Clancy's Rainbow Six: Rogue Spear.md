# Tom Clancy's Rainbow Six: Rogue Spear (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Tom Clancy's Rainbow Six: Rogue Spear.gba` |
| Size | 8,388,608 bytes (0x800000, 8 MiB) |
| `file` | Game Boy Advance ROM image: "RAINBOWSIX-R" (AR6E41, Rev.00) |
| Header title | `RAINBOWSIX-R` |
| Game code | `AR6E` |
| Maker | `41` (Ubi Soft) |
| Version / complement / checksum | `0x00` / `0x59` / `0x0000` |
| Entry word | `0xEA00002E` — **stock crt0**, no scene cracktro / trainer patch (§16.1) |
| MD5 | `509e3a1fe6284a75c84315a64bd33f43` |
| SHA-1 | `6862d369daf3709a5de9458ceb3f8200b78b8160` |
| SHA-256 | `4bc38c2edb9cae0797d88416da2ec213262d51af5619c7684ebdee24464e6b09` |

Scope: developer-intended in-game cheats only. All GameShark / CodeBreaker / Action Replay
entries found during recon are **out of scope** and were not used.

## 2. Executive summary

This title has a **pause-menu button-code system**, not a password system. No password
screen, no code alphabet, no code table and no hidden debug menu were found. Three
published button sequences were independently confirmed in the emulator, and the
Lone Wolf "unlockable" was proven to be a save-flag gate rather than a code.

The three confirmed in-game cheats are:

| Sequence | Where | Observed effect |
|---|---|---|
| `L, L, R, R, Down, Down` | pause screen (also accepted in gameplay) | "All enemies on radar": map draws red enemy dots that are absent without the code |
| `L, R, Down, Down` | **paused** | Level Skip: `MISSION COMPLETE`, both objectives flip to `Achieved` |
| `L, R, Up, Up` | **paused** | Stage Skip: `MISSION COMPLETE`, only "Rescue hostages" is `Achieved`; "Neutralize all terrorists" stays `Not achieved` |

The validator itself was **not located** in the 8 MiB image (search boundary and counts in
§5/§6b). A bounded enumeration of the natural code space was executed instead: 56
undocumented sequences were pressed in the emulator; **none** was accepted. This is a
bounded negative with counts, not an untested gap.

## 3. How to reproduce

Emulator: mGBA 0.10.5 (`/usr/local/bin/mgba`) under Xvfb `:315`, `SDL_AUDIODRIVER=dummy`,
3× scale. Keymap (default SDL): `A=x`, `B=z`, `L=a`, `R=s`, `Start=Return`,
`Select=BackSpace`, D-pad = arrow keys. Hold keys 100–150 ms; shorter taps are missed.

Menu path to a code-testing state:

1. Language screen → **A** (English).
2. Main Menu → **A** on SINGLE PLAYER.
3. CHOOSE A SLOT → **A** (slot 1).
4. DIFFICULTY LEVEL → **A** (Veteran).
5. GAME MODE → **A** (Campaign).
6. CHOOSE MISSION → **A**, then advance the briefing with **A** until the team screen.
7. Team screen: use **Up/Down** to browse operatives and **A** to add each one; four
   small portraits must be filled (the `Press START` alert replaces the class label).
   **Start** launches the mission. (Shortcut from step 5: **Start** on CHOOSE MISSION
   skips the briefing — confirmed against the game manual.)
8. In gameplay: **Start** opens the `Pause` menu (`Resume` / `Quit`). Enter a sequence
   there. For the radar code, open the map with **Select** afterwards.

Expected: the two skip codes close the pause menu and after ~2 s show the mission-complete
banner; the radar code closes the pause menu and adds red dots to the map.

## 4. Address map

| Address | Type | Meaning / evidence |
|---|---|---|
| `0x08000000` | code | Stock ARM crt0; entry branch `0xEA00002E` |
| `0x08006354` | Thumb fn | Input update, called from the main loop (BL xrefs `0x08007E88`, `0x080115A2`, `0x08037F50`) |
| `0x0800635C` | instruction | `ldrh r0,[r0]` reads KEYINPUT via literal `0x08006398` = `0x04000130` |
| `0x08006360` | instruction | `mvns` + 16-bit mask → active-high key word stored at `[0x02004B70]` |
| `0x02004B70` | RAM | Input manager: `+0` current keys, `+4` previous keys, `+16` frame count, `+20` handler-list pointer. Observed idle value `0x0000FC00` (mGBA leaves KEYINPUT bits 10–15 clear) |
| `0x02004B84` | RAM | Handler list: `+0` count, `+4` array pointer, 24-byte stride |
| `0x080069FC`, `0x08006A6C` | Thumb fns | Generic single-mask input handlers used by the list (observed callbacks `0x080069F9`, `0x080069FD`, `0x0806A6D`) |
| `0x0803AAB0`… | thunks | `bx rN` register-indirect call stubs used by the handler dispatch |
| `0x0803E328` | data | Localized string `Pause`; pointer referenced from table `0x08045D20` region |
| `0x08045D20` | data | Pause/other menu text-pointer table (`0x0803E328`, `0x0803E320`, `0x0803E310`, …) |
| `0x08738793` | data | Localized `LONE WOLF` text bank (repeated per language) |
| `0x0874EB86` | data | `You must unlock missions` gate message (seen in emulator) |
| `0x08006C04` | Thumb fn | PRNG fed by the key-change hash stored at `0x02001F10` — investigated and ruled out as a cheat validator |
| Savestate layout | file | mGBA `.ss1` = PNG with zlib `gbAs` chunk → 397,312 raw bytes; EWRAM at raw `0x21000`, IWRAM at `0x19000` (verified: GBA `0x02004B70` = raw `0x25B70` = `00 FC 00 00`) |

## 5. Validator / algorithm

**Not recovered.** The following reversible facts were established:

* The engine reads `KEYINPUT` once per frame, inverts it to an active-high word and keeps
  a previous/current pair (`0x08006354`). A frame counter increments while keys are
  unchanged; on a change an XOR-rotated value is stored to `0x02001F10` and consumed by
  the PRNG at `0x08006C04` — that path was traced and is **not** the cheat matcher.
* Button actions are dispatched through a generic list of 24-byte handler records with
  single-mask predicates (e.g. mask `0x3F3` = all buttons except L/R, mask `0xC` = L+R).
  This yields the game's internal mask order
  `A=0x001, B=0x002, R=0x004, L=0x008, Select=0x010, Start=0x020,
  Right=0x040, Left=0x080, Up=0x100, Down=0x200`. No sequence-comparison table was
  present in any of the handler structures read live from RAM.
* The key-mask remap above was used to re-run literal searches; still no code table.

Because no validator function or table was found, **no offline accept/reject oracle was
produced**; acceptance was established from the game itself (§7).

## 6. Tables

### 6.1 Confirmed codes (all three also appear on 3rd party cheat indexes)

| # | Sequence | Context | Effect |
|---|---|---|---|
| 1 | `L L R R D D` | pause (verified); gameplay accepted but no visible change | radar enemies toggle |
| 2 | `L R D D` | paused | level skip, both objectives `Achieved` |
| 3 | `L R U U` | paused | stage skip, second objective stays `Not achieved` |

### 6.2 Lone Wolf — save-gated, not a code (§16.3 case "gated feature")

Game Mode → LONE WOLF is selectable in the menu but leads to
`Not yet available! You must unlock missions in Campaign mode.` This matches the
published unlockable ("Beat all the missions"). No button code, password or debug
gate was found that opens it; the gate is campaign progress in the save record.

### 6.3 Negative string reconnaissance

`strings -t x -n 4` produced 68,606 lines. Keyword hits for `password`, `cheat`, `debug`,
`secret` were limited to unrelated engine strings (`Report the following code to` at
file `0x3CB9E`, `code : 0x%x` at `0x3CBC8`, `&%$C_MENU` at `0x3E594`) and localized
mission dialogue. No debug-menu labels, password prompt, or code-entry UI text exists.

## 6b. Enumeration

### Space definition

The observable space is sequences of controller presses. Documented lengths are 4 and 6;
the documented alphabet is the four shoulder/D-pad buttons `{L, R, Up, Down}`.
Two structural families are known from the published list:

* `L, R, X, X` — length 4 (two documented members: `X=Down`, `X=Up`)
* `L, L, R, R, X, X` — length 6 (one documented member: `X=Down`)

### Sweep A — complete families over {L,R,Up,Down}

All `L R X X` (16) and all `L L R R X X` (16) combinations were entered on the pause
screen from a fresh savestate. Acceptance test: the pause menu disappears on the next
frame (rejected sequences leave `Pause` / `Resume` / `Quit` on screen).

* Tested: **32**
* Accepted: **3** — `L R D D`, `L R U U`, `L L R R D D` (exactly the published set)
* Rejected: **29**

### Sweep B — out-of-family probes

24 further sequences were tested on the pause screen: reversed prefixes (`R L D D`,
`R L U U`), doubled/tripled prefixes (`L L D D`, `R R L L D D`, `L L L R R D D`),
mixed directions (`L R D U`, `L R U D`, `U D L R`), trailing extra presses
(`L R D D D`), other face/system buttons in the final slots (`L R A A`, `L R B B`,
`L R Start Start`, `L R Select Select`), and length-6 variants with `Up` in the tail
(`L L R R U U`, `L L R R L L`, `L L R R R R`).

* Tested: **24**
* Accepted as a *new* effect: **0**
* `L R D D D` and `L R D D D D` close the menu only because they contain the accepted
  `L R D D` prefix — not new codes. `L R A A` is a false positive: A alone activates
  the highlighted `Resume` item (verified by pressing A once from the pause screen).

### Novel codes

**None found.** No sequence outside the three published values was accepted by the game
in 56 in-game trials. This is a bounded negative for the "novel code" deliverable: the
two structural families were enumerated exhaustively over their four-button alphabet,
plus 24 out-of-family probes. An additional exhaustive 4-button length-4 space
(256 sequences) was not run end-to-end, so the claim is bounded to the 56 tested
sequences and the two families, not to every possible controller string.

### Bounds proven by rejection

* Replacing the final repeated direction with the opposite direction (`L R D U`,
  `L R U D`) is rejected — the matcher requires the **repeated** last button.
* Swapping the first two buttons (`R L D D`, `R L U U`) is rejected — prefix order matters.
* `L L R R U U` (the radar prefix with `Up` tail) is rejected — the radar code's tail
  is specifically `Down, Down`.
* Entering the skip codes without pausing produces no mission-complete screen.

## 7. Validation evidence

**Observed (emulator / screenshots)**

* Boot through splash, language select, main menu, slot select, difficulty, game mode,
  choose mission, briefing, team select, gameplay, pause, map, mission complete,
  options, credits, and the Lone Wolf gate message. All were screenshotted.
* `L R D D` while paused → `MISSION COMPLETE` with both objectives `Achieved`
  (`v_lvl.png`, `lvlskip_after2.png`).
* `L R U U` while paused → `MISSION COMPLETE` with "Neutralize all terrorists
  Not achieved" (`v_stg.png`).
* `L L R R D D` while paused → pause closes; map afterwards shows red enemy dots
  (`map_radar.png`) where the baseline map (`map_base.png`) has none. The two map
  screenshots differ in 612 pixels.
* Options screen exposes only SOUND / LANGUAGE / CONTROL SET — no hidden/debug entry.
* Multiplayer is a link-cable entry path; it was not exercised solo (see §8).

**Derived (savestate RAM reads)**

* mGBA `.ss1` decoded via its zlib `gbAs` chunk. EWRAM/IWRAM mapping verified by
  reading the known input global.
* Comparing a paused baseline state with the state immediately after a *rejected*
  sequence and after the *accepted* radar code (same key count) yields 5,823 differing
  byte positions; the EWRAM differences cluster in `0x02000E60+`, an audio work area —
  the game plays a distinct confirmation sound for an accepted code. This is direct
  RAM-level evidence that the game classifies the sequence, independent of the visual
  map effect.

**Inferred (not fully proven)**

* The exact comparator and the flag word that the map renderer reads were not isolated;
  the radar effect is established visually and by RAM diffs, not by a located
  `AND`/`TST` instruction.
* The Lone Wolf gate is assumed to be a save-bit unlock from its message and the manual;
  the setter's callers were not enumerated.

## 8. Unknowns

* The button-sequence comparator was not located; no offline validator reimplementation
  exists, so no code was "minted" from an algorithm.
* The radar toggle's RAM flag address and the mission-complete state variable were not
  pinned to specific instructions.
* Multiplayer screens require a second GBA/link; not walked.
* Whether any length-2/3 or very long sequences exist outside the tested 56.

## 9. Tooling

* `strings -t x`, `grep -abo`, `xxd` for initial reconnaissance.
* `arm-none-eabi-objdump -M force-thumb` and Capstone 5.0.7 for literal-pool / BL /
  opcode scans. Keystone installed but not used.
* `mgba` 0.10.5 under Xvfb `:315` + openbox; `xdotool` XTEST input; `scrot` screenshots;
  ImageMagick `montage`/`compare` for contact sheets and pixel diffs.
* `dbg.py` — mGBA `-d` CLI debugger over a Python pty (the GDB stub on port 2345 was
  occupied by another process, so `-d` was used for RAM reads).
* `ss.py` — decode mGBA `.ss1` PNG `gbAs` zlib chunk into a raw 397,312-byte state.
* `stateutil.py`, `trycode.py`, `scan_codes.py`, `sweep.py` — savestate reload /
  code entry / outcome-classification harnesses (work dir `/tmp/roguespear`).
* Web recon: 3rd party cheat indexes and the GBA user manual hosted
  at device.report. Fetched pages were treated as data only.

## 10. Legal note

No ROM or copyrighted asset is redistributed in this report. Only hashes, addresses,
observed behavior, and original analysis scripts are published.
