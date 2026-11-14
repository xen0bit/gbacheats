# Dinotopia: The Timestone Pirates (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Dinotopia: The Timestone Pirates/Dinotopia: The Timestone Pirates.gba` |
| Size | 8,388,608 bytes (0x800000) |
| Header title | `DINOTOPIA` |
| Game code / maker | `AD3E` / `6S` (TDK Mediactive) |
| Software version | 0 |
| MD5 | `51de5ab8ad89e3fe2f5d1a270b690474` |
| SHA-1 | `6519b9a55ed4fc34a97f6733f7b9efb46a34445c` |
| SHA-256 | `6ff1e625f5e27b10b0e838b97c23ff17c15f9cea81a8fa5734f3c782a21f131b` |
| Entry word | `0xEA1D94FE` → branch to `0x08765400` (inside an appended intro) |
| Complement byte | stored `0x24`, expected `0xD4` (header edited) |
| Header checksum | `0x0000` (rebuilt header) |

**The image is not the stock retail dump.** `0x08765400` is an appended
cracktro/loader block: ARM stub `ldr sp,[pc,#60]; add r0,pc,#1; bx r0`,
literal pointer `0x080000C0` at `0x08765464`, and the ASCII banner at
`0x08768EFB`:

```
MODE 7 IS PROUD / TO PRESENT YOU / DINOTOPIA / (C) TDK MEDIA
RELEASED ON / MAY 2ND, 2002 ... 'BACK FROM THE DEAD' BY AFTERMATH
GRAPHICS BY: MOONLORD
```

The stock crt0 at `0x080000C0` is intact (`mov r0,#0xD2; msr CPSR; ...`).
For analysis a copy was made with only four bytes restored
(`0x00: 0xEA00002E`, recalculated complement `0xD4` and header checksum
`0x0024`); that copy boots straight to the stock crt0 and is byte-identical
elsewhere. Analysis-copy hashes: MD5 `ce4016153daadd27c5ffde0f13d6e243`,
SHA-1 `d330438ead732aa95a9eb4f8a87c0d6e26dcb7dc`.

The cracktro is a scene-release loader, **not** an in-game cheat; it adds no
input surface to the game itself and was excluded from the cheat search.

## 2. Executive summary

The game has **no password system, no code alphabet, and no debug menu text**.
It has exactly **two 10-press button codes**, both present verbatim in the ROM
and both already published:

* **Code B (level select)** — `Up Up Down Down Left Right A Left Right B`,
  entered on the title screen. Press Start, choose Credits, let the credits
  finish: the game loads a walkable farm level-select screen with numbered
  doors (published by GameFAQs/cheats42 as "Level Select").
* **Code A (stage skip)** — `Down Down Up Up Right Left B Right Left A`,
  the button-wise mirror of B. It sets the same debug flag that the level-select
  route sets; in-game the pause menu then skips one scene when Select is
  pressed (published by GameFAQs as "Enable Stage Skip").

Both codes are the **complete accepted set**. The matcher is a 10-step
fixed-prefix state machine over six tracked buttons (A, B, Right, Left, Up,
Down); Start/Select/L/R are ignored. The full tracked input space is
`6^10 = 60,466,176` sequences and exactly **2** are accepted — one referenced
key-mask table in the whole ROM contains exactly those two sequences
(20 bytes at `0x0850FE60`). There is therefore **no novel code to mint**: the
space is closed, and the report proves that by exhaustive table scan plus
in-game rejection of mutated sequences.

What *is* unpublished is the **effect** of the debug flag the codes set:

* Pause → **Select** advances the scene record by exactly one (stage skip).
* Pause → **R** increments the stored life/retry counter, one per press,
  clamped at 100 (`0x64`). Published notes mention only Select.
* With the flag clear, both inputs do nothing (both directions tested).
* Holding L+R+Select while entering either sequence is accepted (those three
  unmasked buttons are ignored by the matcher) — an input alias, not a new code.

## 3. How to reproduce

Emulator/keymap used: mGBA (SDL) under `Xvfb :308`, `SDL_AUDIODRIVER=dummy`,
3× scale; default SDL map A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
Select=`BackSpace`, D-pad = arrows. Hold 100–150 ms per press, 150–200 ms gap;
the game polls edge-triggered input once per frame.

1. Boot the analysis copy (or the retail image after its MODE 7 intro).
   First boot shows **Languages** (English/Français/Español/Nederlands/Deutsch/
   Italiano). Choose English → title screen (`Press Start`).
2. **Code B:** at `Press Start`, press `U U D D L R A L R B`.
   RAM check: `0x03000588` becomes `1` (was 0). Press Start → Main Menu →
   Credits. Let the credits run out (~90 s, or hold Tab to fast-forward).
   The farm level-select screen loads; RAM shows scene pointer
   `0x030007F0 = 0x080404B4` (scene 50) and `0x030005C8 = 1`.
   Walk right, climb the first ladder, walk right to the door marked `1`,
   press Up: the scene pointer becomes `0x0803FEF0` (scene record 9) and a
   "Please, Wait" load leads to a city scene (record 9).
3. **Code A:** at the title press `D D U U R L B R L A`.
   RAM check: `0x030005C8` becomes `1` (0x03000588 stays 0). Start → Start Game
   → New Game, reach gameplay, press Start (pause), press Select: the scene
   pointer advances one record (0x0803FECC → 0x0803FEF0 in the tested state).
4. **Undocumented R action:** with `0x030005C8 = 1` in the pause menu, each R
   press adds 1 to `0x030005BC` (clamped at 100); the pause HUD number goes
   5 → 8 after three presses. With `0x030005C8 = 0`, five R presses leave
   `0x030005BC = 6` (no effect).
5. **Rejection:** ten-press sequences with one wrong tracked button (e.g.
   `U U D D L R A L R A`, or `D D U U R L B R L B`) leave both flags at 0.

Savestate RAM reads: mGBA `.ssN` files are PNGs with a zlib-compressed `gbAs`
chunk; the decompressed 397,312-byte state has IWRAM at `0x19000`
(`0x03000000`) and EWRAM at `0x21000` (`0x02000000`).

## 4. Address map

### ROM

| Address | Size | Meaning |
|---|---|---|
| `0x08031DE0`–`0x08031ED6` | 0xF6 | title-screen button-code matcher |
| `0x08031F3C`–`0x08031FA2` | — | title-screen frame handler; calls matcher at `0x08031F78`, Start at `0x08031F88` |
| `0x08031B14` / `0x08031A4C` / `0x08031B60` | — | credits/camera handler chain and post-credits gate |
| `0x08033AE8`–`0x08033BC4` | 0xDC | in-game pause handler (debug branches at `0x08033AF6`) |
| `0x08033924` | — | installs pause handler (called from `0x0800149E`) |
| `0x080341C4` | — | death/game-over path: resets `0x030005BC = 6`, loads scene 47 |
| `0x08001718` | — | reads `0x030005BC`; zero → `0x080341C4` |
| `0x0803FDAC` | 51 × 0x24 | scene record table, slots 0–50 (slot 46 is a zero terminator; 47–50 special); `0x24` stride |
| `0x080404B4` | 1 rec | level-select farm scene (index 50) |
| `0x0804046C` | 1 rec | credits scene (index 48) |
| `0x0850FE60` | 10 bytes | code B key-mask table |
| `0x0850FE6A` | 10 bytes | code A key-mask table |
| `0x08031E60` / `0x08031E64` / `0x08031EBC` | 3 literals | pointers to the two tables |
| `0x0805CDAC` | — | shared level graphics descriptor |
| `0x0850F8EC` | — | dev leftover `Assertion failed:` string |

### RAM (IWRAM)

| Address | Width | Meaning |
|---|---|---|
| `0x030006AC` | u16 | edge-triggered pressed-key bits (`~KEYINPUT & 0x3FF`) |
| `0x0300066C` | u8 | code-family state: 0 none, 1 = B family, 2 = A family |
| `0x03000670` | u8 | press index inside the 10-step sequence |
| `0x03000588` | u8 | code B accepted flag |
| `0x030005C8` | u8 | debug flag (code A directly; also set by the post-credits gate) |
| `0x030005B0` | u32 | scene flags; bit 7 set by farm init |
| `0x030005BC` | u8 | life/retry counter (stored 6 = HUD shows 5; 0 = death path) |
| `0x0300059C` | u32 | current frame handler (Thumb pointer) |
| `0x030007F4` | u32 | next frame handler |
| `0x030007F0` | u32 | current scene record pointer |
| `0x03006C68` | u8 | pending scene id for transition scenes 47–49 |

## 5. Algorithm

### 5.1 Title matcher (`0x08031DE0`)

```c
u16 k = *(u16*)0x030006AC;          // buttons newly pressed this frame
if ((k & 0x00F3) == 0) return;      // ignore Select/Start/L/R-only frames
u8 *state = 0x0300066C, *idx = 0x03000670;

if (*state == 0) {
    if (k & 0x0850FE60[0]) *state = 1;   // Up  -> B family
    if (k & 0x0850FE6A[0]) *state = 2;   // Down-> A family
}
if (k & 0x0850FE60[*idx] && *state == 1) {        // expected B button
    if (++*idx == 10) { palette_fade(0x05000200,...); *idx = 0;
                        *(u8*)0x03000588 = 1; return; }
}
if (k & 0x0850FE6A[*idx] && *state == 2) {        // expected A button
    if (++*idx == 10) { palette_fade(0x05000200,...); *idx = 0;
                        *(u8*)0x030005C8 = 1; return; }
}
*state = 0; *idx = 0;               // any wrong tracked button resets
```

Notes that matter for reproducing it:

* The test is `k & table[i]`, not `k == table[i]`: two tracked buttons pressed
  on the same frame still advance (the key set is OR'ed by the joypad reader).
* Frames that contain only untracked buttons (Select/Start/L/R) hit the early
  `return` and do **not** reset the sequence — this is why a code can be typed
  while L+R+Select are held.
* Start on the title is handled after the matcher (`0x08031F7C`): `k & 8` →
  `0x080014C4` (advance to the next scene, the main menu).

### 5.2 Flags and gates

* `0x03000588 = 1` (code B). The title frame handler skips a palette-fade
  block when it is set (`0x08031F3E`). The credits scene (record 48, handler
  `0x08031A4C`) ends at `0x08031B60`:
  `if (0x03000588) { 0x030005C8 = 1; load_scene(0x32=50); } else load_scene(6);`
  so B alone is the level-select unlock. This was tested both ways
  (§6b bounds).
* `0x030005C8 = 1` (code A directly, or the credits gate). In the pause
  handler `0x08033AE8` it enables two branches:
  * `k & 0x100` (R): `0x030005BC++`, clamp 100 (`0x08033B0E`–`0x08033B20`).
  * `k & 0x004` (Select): `0x08025E74(); 0x08000950();`
    `0x0300059C &= ~3; 0x080014C4();` — advance one scene record
    (`0x08033B6E`–`0x08033B8C`).
  With the flag clear both are skipped (`0x08033AF6`, `beq 0x08033BBC`).

`0x080014C4` is the scene advance: `scene_ptr = [0x030007F0] + 0x24`, then load
record `[scene_ptr+4]` (or `0x0803FDF4` when zero). This is why Select moves
exactly one table record.

## 6. Tables

### 6.1 The two accepted sequences

`0x0850FE60` (code B), 10 bytes, one key mask per press
(active-high `~KEYINPUT`: A=0x01, B=0x02, Select=0x04, Start=0x08,
Right=0x10, Left=0x20, Up=0x40, Down=0x80, R=0x100, L=0x200):

```
40 40 80 80 20 10 01 20 10 02   -> U U D D L R A L R B   (level select)
80 80 40 40 10 20 02 10 20 01   -> D D U U R L B R L A   (stage skip)
```

`0x0850FE6A` is the second row (code A). The two rows are button-wise mirrors
(swap U/D, L/R, A/B); both are intentional dev codes, not a transcription
artifact — both exist as separate literals and separate flag writes.

### 6.2 Flags

| Flag | Set by | Effect |
|---|---|---|
| `0x03000588` | code B completion (`0x08031E54`) | enables post-credits gate → farm; skips title palette fade |
| `0x030005C8` | code A completion (`0x08031EB6`), or post-credits gate (`0x08031BAC`) | pause Select = next scene; pause R = +1 life |
| `0x030005B0` bit 7 | farm init `0x08031D78` | farm scene marker |
| `0x030005BC` | game-over init `6`; pause R `+1`, max 100 | life/retry counter |

### 6.3 Selectable scenes (derived from `0x0803FDAC`)

23 records have the level loader `[+4] = 0x080013ED`:

| scene idx | record | init/update fn @+8 | u16 @+0x0C / +0x10 |
|---:|---|---|---|
| 8 | `0x0803FECC` | `0x0802A07D` | 0x33 / 0x684 |
| 9 | `0x0803FEF0` | `0x0802A0F9` | 0x20 / 0x1D4 |
| 10 | `0x0803FF14` | `0x0802A175` | 0x20 / 0x301 |
| 12 | `0x0803FF5C` | `0x0802A1F1` | 0x4D / 0x20A |
| 14 | `0x0803FFA4` | `0x0803682D` | 0x46 / 0x17F |
| 16 | `0x0803FFEC` | `0x08035AB5` | 0x212 / 0x949 |
| 17 | `0x08040010` | `0x08035C69` | 0x33 / 0x767 |
| 18 | `0x08040034` | `0x08035E91` | 0x21 / 0x9D7 |
| 20 | `0x0804007C` | `0x0803619D` | 0xB6 / 0x7C |
| 21 | `0x080400A0` | `0x0803682D` | 0x46 / 0x17F (shared with 14) |
| 23 | `0x080400E8` | `0x0802A9E5` | 0x58 / 0x58 |
| 24 | `0x0804010C` | `0x0802AA61` | 0x60 / 0x60 |
| 25 | `0x08040130` | `0x0802AADD` | 0x58 / 0x130 |
| 27 | `0x08040178` | `0x0802A515` | 0x290 / 0x1E0 |
| 30 | `0x080401E4` | `0x0802CAB5` | 0x48 / 0x5B4 |
| 31 | `0x08040208` | `0x0802CAB5` | 0x50 / 0x280 (shared with 30) |
| 32 | `0x0804022C` | `0x0802CB55` | 0x68 / 0x1C2 |
| 33 | `0x08040250` | `0x0802C819` | 0x22 / 0xF9 |
| 34 | `0x08040274` | `0x0803682D` | 0x46 / 0x17F (shared with 14/21) |
| 36 | `0x080402BC` | `0x0802FCE5` | 0x78 / 0x778 |
| 37 | `0x080402E0` | `0x0802FED9` | 0x90 / 0x160 |
| 38 | `0x08040304` | `0x08030059` | 0xAF / 0x738 |
| 44 | `0x080403DC` | `0x0802F385` | 0xF3 / 0x87 |

Non-level records are menus/transitions: 5 title (`0x08031ED9`), 6 main menu
(`0x08033049`), 7 options (`0x08032B21`), 48 credits (`0x08031ACD`),
49/50 farm transitions and farm.

### 6.4 Pause menu entries

`Continue`, `Exit Game`, plus the two flag-gated actions (Select = next scene,
R = +1 life). No additional menu rows appear with the flag set — the debug
surface is the two inputs, not hidden text.

## 6b. Enumeration

**Space definition.** Tracked alphabet: `{A,B,Right,Left,Up,Down}` (6 symbols,
mask `0x00F3`). Length: exactly 10. Ignored, non-resetting: `{Start,Select,L,R}`
(only when pressed alone; on the title, Start also advances the scene).
Representable tracked sequences: **6^10 = 60,466,176**. Accepted: **2**
(`U U D D L R A L R B`, `D D U U R L B R L A`). Because the matcher compares
`k & table[i]`, two tracked buttons pressed on the same frame are accepted, but
each frame can only advance one index; the accepted language is therefore
those two sequences with any number of Select/L/R-only frames interleaved
(aliases), not a larger code set.

**Closed-set proof (exhaustive scan).** A whole-ROM scan for byte runs of
power-of-two key masks of length ≥ 5, restricted to runs referenced by a
32-bit little-endian pointer to `0x08000000+offset`, returns exactly **two**
hits: `0x0850FE60` (length 20 = the two 10-byte sequences) and a 5-byte run
`40 08 08 08 01` at `0x08080854`. The latter is a self-pointer inside a
pointer/colour record table (the pointer to it is stored at `0x0808085C`,
inside the same table); it has no reader, is not a sequence (three consecutive
Start masks), and is not an input table. The equivalent u16-mask scan with the
same pointer filter returns only a bitmap table at `0x0850F8DC` next to the
`Assertion failed:` string (not an input table).
No second dispatcher exists. No password alphabet or code-entry screen exists
(no password strings in any of the five languages; every menu was walked):
`password/cheat/debug/secret/unlock` occur **0** times in 81,048 ASCII strings,
in all five languages (`mot de passe`, `Passwort`, `contraseña`, `wachtwoord`,
`codice`, `clave` = 0 each). The only keyword hits are the staff credits
(`Eugene Code`, `Level Design`).

**Novel code: none exists, and that is the result.** The accepted set is a
closed 2-entry table, so any value outside it is rejected and any value inside
it is already published. What was generated and verified instead is the
**unpublished input form and effect**:

| Input | Published? | In-game proof |
|---|---|---|
| Code B + holding L+R+Select | no | `0x03000588 = 1` after entry (savestate read) |
| Code A + holding L+R+Select | no | `0x030005C8 = 1` after entry |
| Pause → R (after A or B route) | no | `0x030005BC` 6→9 after 3 presses; HUD 5→8 |
| Pause → R ×100 | no | counter stops at `0x64` = 100 |
| Pause → Select (after A or B route) | yes ("stage skip") | scene `0x0803FECC` → `0x0803FEF0`; visible new area |

Alias caveat: the L+R+Select variants are aliases of the same two codes
(§16.4b) and are **not** counted as distinct codes; they are reported as an
input-matcher property only.

**Bounds proven by rejection.**

* `U U D D L R A L R A` → `0x03000588 = 0`, `0x030005C8 = 0` (one wrong button
  in the B sequence).
* `D D U U R L B R L B` → `0x030005C8 = 0` (one wrong button in the A sequence).
* Title with no code → credits run to completion → main menu
  (`0x030007F0 = 0x0803FE84`, record 6), `0x030005C8 = 0`; the same credits run
  with code B → farm (`0x030007F0 = 0x080404B4`, record 50),
  `0x030005C8 = 1`. That is the level-select gate in both directions.
* Pause with `0x030005C8 = 0` → five R presses leave `0x030005BC = 6`;
  Select leaves the pause screen unchanged. With the flag set both act.
* Pause R clamp: 100 presses end at `0x030005BC = 100`, not 106.

**Level-select screen (hidden screen).** Scene 50 (`0x080404B4`) is the farm
with ladders and numbered doors. Observed door `1`: pressing Up on its
platform loads scene record 9 (`0x0803FEF0`) via the normal
"Please, Wait" loader. The selectable roster is the 23 level records in §6.3.

## 7. Validation evidence

**Observed (emulator, screenshots/RAM):**

* Both published sequences typed on the title screen set their flags:
  code B → `0x03000588=1` (title handler `0x08031F3D` still active);
  code A → `0x030005C8=1`, `0x03000588=0`.
* Code B → Start → Main Menu → Credits → farm screen (`shot_07`); scene pointer
  `0x080404B4`, `0x030005C8=1`, HUD shows the farm.
* Farm door 1 → "Please, Wait" (`d5.png`) → city level (`d6.png`);
  scene pointer `0x0803FEF0`.
* Pause menu (`shot_17`, `shot_25`) is `Pause / Continue / Exit Game`.
  With code A: Select changed the scene from `0x0803FECC` to `0x0803FEF0`
  (`shot_26`); R changed `0x030005BC` 6→9 and the HUD counter 5→8
  (`p0.png`/`p1crop.png`).
* Without the flag: Select did nothing (`shot_18` vs `shot_17`), five R
  presses left `0x030005BC=6`, and the credits returned to the main menu.
* 100 R presses clamp the counter at 100.
* Mutated sequences leave both flags 0.

**Derived (disassembly):**

* Matcher at `0x08031DE0`; table pointers at `0x08031E60`/`E64`/`EBC`.
* Flag writes at `0x08031E54` (B) and `0x08031EB6` (A).
* Pause debug branches and clamp at `0x08033B0E`–`0x08033B8C`.
* Scene advance (`+0x24`) at `0x080014C4`.
* Post-credits gate at `0x08031B60`; farm init `0x08031D78`.
* Death path and counter reset at `0x08001718` / `0x080341C4`.
* 23 level records and the 0x24 stride of `0x0803FDAC`.

**Inferred:**

* `0x030005BC` is a life/retry counter: it is initialised to 6 at game over,
  tested for zero before the game-over path, and drawn one lower in the HUD.
  The exact display convention (stored-1) is observed, the game-design name is
  inferred.
* Door numbering of the farm maps its doors onto the 23 level records in
  scene-table order; only door 1 was mapped dynamically.

## 8. Unknowns

* The farm's door numbering beyond door 1: the door→scene mapping was proven
  only for door 1 (`0x0803FEF0`); whether every numbered door targets a level
  record or some target cutscene records is not established.
* The exact reason the HUD prints `0x030005BC - 1` rather than the stored value
  (a `lives+1` convention is likely but not proven).
* Whether a save file with progress adds entries to Save Options in a way that
  interacts with the debug flag (no save data was carried between tests).
* No cracktro trainer menu was found in the MODE 7 block (only the intro text
  and loader); only the game's own two codes were analysed.

## 9. Tooling

* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`
* Python 3 + `struct`/`zlib` for literal-pool scans, BL scans, table scans and
  mGBA savestate (`gbAs` chunk) RAM reads; Capstone 5.0.7 available but not
  required.
* mGBA (SDL) on Xvfb `:308`; `xdotool` key driver (`keys.py`, 100–150 ms holds);
  `import -window root` screenshots.
* Whole-ROM referenced-table scan (byte and u16 mask runs, pointer filter) as
  described in §6b.

Screenshots referenced above are kept in the analysis work directory, not in
the ROM folder. No ROM, graphics, music or text assets are redistributed here;
all addresses and tables are factual observations of the binary.
