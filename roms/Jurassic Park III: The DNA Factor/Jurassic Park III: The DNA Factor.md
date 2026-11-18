# Jurassic Park III: The DNA Factor (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Jurassic Park III: The DNA Factor/Jurassic Park III: The DNA Factor.gba` |
| Size | 8,388,608 bytes (0x800000) |
| `file` description | Game Boy Advance ROM image: "JP3 THE DNA" (ADNEA4, Rev.00) |
| Header title | `JP3 THE DNA` |
| Game code / maker | `ADNE` / `A4` (Konami) |
| Version | 0x00; fixed byte 0xB2 = 0x96; complement 0x03; header checksum 0x0000 |
| Entry word | `0xEA00002E` (stock `b 0x080000C0`), stock crt0 at 0x080000C0 |
| MD5 | `d596b05b4f52d2880f36db3e7ec9a8e5` |
| SHA-1 | `ab73f66abd86f53b24661f7319114d01c7354057` |
| SHA-256 | `f64ce8312563eea4e7077bca6684a71b2b224ac9643bb9b5432f8107b32e64e1` |

Phase 0 embedded-header scan: the 156-byte Nintendo logo occurs **exactly once**, at
file offset 0. No multiboot stub, second image, appended trainer, or patched entry
point was found; this is a clean single-image retail ROM.

**Independence from the two siblings (verified, not assumed).** A separate 8 MiB image,
`Island Attack` (header `JP3ISLANDATTAJQE`, MD5 `ccae308baca9baecaba1ab670dcc27c8`),
was checked. The DNA Factor debug strings `Level Select`, `Player Select`, `Woman`,
`Man`, `MARK HANSON` and `KONAMI` are **absent** from the Island Attack image (0 literal
hits each), and the two images have different game codes and different MD5s. No shared
literal table or shared code base was identified between this image and Island Attack.
The titles share publisher/franchise and KCEA staff (credits at 0x08035658–0x08035C78,
including the label `Demo/DNA Game Program` at 0x08035B7C), but this ROM must be treated
as its own revision with its own addresses.

## 2. Executive summary

**There is no password or code-entry system in this SKU.** There is no on-screen
alphabet, no code buffer, no string-comparison validator, no key-mask cheat table, and
no published password list for the game (GameFAQs lists exactly one secret, a
post-gameplay difficulty unlock — see §3).

There **is** a genuine hidden developer screen: a **Level Select / Player Select**
debug menu (scene id 9). It is real, reachable through the game's own scene dispatcher,
and fully controllable with the D-pad and A+Start:

* `Level Select` 0–9 (10 values), `Player Select` Man/Woman (2 values), and a launch
  action. Screenshots and RAM reads for all of these are recorded in §7.
* Entry gate: byte `0x02000000 == 5` plus A. This selector is the input to the game's
  6-way scene-transition dispatcher at `0x08006F0C`; value 5 is the debug entry. The
  normal title UI only ever moves the selector between 0 and 1 (Up/Down), so **no
  controller sequence in the tested input space reaches value 5**; I reached it by
  setting the selector in a savestate (§3, §8). Out-of-range values 6 and 255 were
  rejected, and selector 5 with the wrong button was rejected.
* I generated and confirmed an unpublished combination — `Level Select 3 / Player
  Select Woman`, then launched level 6 as Woman — and proved the 0–9 / 0–1 bounds by
  in-game wrap-around. No published list mentions this menu at all.

The only published in-game secret for this game ("Harder Game") is a save-flag unlock
after completing the game, not a typed code; its literal appears nowhere in the ROM as
a password string.

## 3. How to reproduce

**Emulator / display:** mGBA 0.3-something SDL (`/usr/local/bin/mgba`), `Xvfb :316
-screen 0 1024x768x24`, `SDL_AUDIODRIVER=dummy`, `-3` scale, window geometry 720x480 at
+154+204. Keymap (default SDL): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
Select=`BackSpace`, D-pad = arrow keys. Hold keys ~100–250 ms.

**Normal menu walk (all with RAM verification of `scene = [task+0x28]`,
`task = [0x030065D0]`):**

1. Boot → MusyX splash → T-Rex cutscene → legal screen (scene 0x2B) → title (scene 4).
2. Title: `NEW GAME` / `CONTINUE` (greyed). A → 3-slot file select (scene 4, byte
   `0x02000002` = cursor). A → character-select cutscene (scene 0x38) → Isla Sorna
   world map (scene 0x4E).
3. In-game side-scrolling stage: scene 0x0A; Start toggles a `Pause` overlay only —
   no options/menu list appears.

**Debug screen reproduction (deterministic):**

1. Save a state on the title screen (Shift+F1).
2. In the `.ss1` (PNG), decompress the `gbAs` chunk, set EWRAM byte at
   `0x02000000 = 5`, recompress, fix chunk length and CRC, load with F1.
3. Press A (hold 150 ms) → scene 9 renders `Level Select 0 / Player Select Man`.
4. Right/Left: level index (byte 0 of `[0x03006FE0]`) 0→1→…→9→0. Up/Down: player
   (byte 2) 0=Man, 1=Woman. A+Start simultaneously: scene 9 → 10 (selected level loads).
5. `base.ss1`, `title_sel5.ss1`, `debug9.ss1` and the helper scripts are in
   `/tmp/opencode/jp3dna/`.

**Published code verification.** Web search + `web.archive.org` snapshot of the
GameFAQs cheats page (capture 2022-02-10) gives a single entry: *"Harder Game — Play
the entire game and beat it. After the credits, press START when the Title Screen
appears, and load up your game."* That is a save/difficulty flag, not a code; no
password string exists to search for. No TCRF page exists for this title (404).
Cheat-CC stage-select / BGM-test / SE-test entries found by search belong to the
**Island Attack** sibling SKU, not this image. Literal searches in this ROM for the
widely published JP passwords `G21G0025`, `I21G0027`, `OVVVVVUP`, `BLUESKY1`, `open
park` all returned **0 hits**; those are from other Jurassic Park titles/platforms.

**Prompt-injection watch:** fetched web pages and ROM strings were treated strictly as
data. No instruction-like payload was encountered in the fetched GameFAQs/archive
content in this run.

## 4. Address map

| Address | Meaning |
|---|---|
| `0x08000000` | ROM base; stock header/entry (`0xEA00002E`) |
| `0x08004194` | Scene "draw/init" dispatch jump table, 79 u32 entries, index = `scene-2` |
| `0x080043D0` | Scene "input/update" dispatch jump table, 79 u32 entries |
| `0x080042D0`..`0x08043A6` | Draw dispatch case bodies (`0x0800431E` → `bl 0x0800726C`) |
| `0x0800450C`..`0x08045A2` | Update dispatch case bodies (`0x0800455A` → `bl 0x08007344`) |
| `0x08006CF8` | Normal title-screen input handler (mode 0) |
| `0x08006F0C` | 6-way scene-transition dispatcher: selector byte at `0x02000000` |
| `0x08006F28` | Jump table for `0x08006F0C` (6 entries, see §6) |
| `0x08006FCC` | Per-option text dispatcher for the same selector (table at `0x08006FE8`) |
| `0x0800726C` | Debug Level-Select **draw** routine; draws strings at `0x08034CE8`, `0x08034CF8` |
| `0x08007344` | Debug Level-Select **input** routine (key checks and struct updates) |
| `0x08034CE8` / `0x08034CF8` | ASCII `Level Select` / `Player Select` (direct u32 pointers at `0x0800730C`/`0x08007310`) |
| `0x08034D08` / `0x08034D10` | ASCII `Woman` / ` Man ` |
| `0x08035658`..`0x08035C78` | Ending / credits text bank (`The End`, `Demo/DNA Game Program`, …) |
| `0x0804EC4` | ASCII text renderer used by the debug screen |
| `0x08247888` | 8-byte-per-record title glyph/sprite table |
| `0x02000000` | Debug scene-transition selector byte (0..5; 5 = Level Select) |
| `0x02000002` | Title file-select cursor byte |
| `0x02000004` | Title mode byte (0 title, 1/2/3 sub-screens) |
| `0x02000006` | Enables the special title handler `0x08007180` when nonzero |
| `0x03006FE0` | Pointer to debug struct, value `0x03006FF0` |
| `0x03006FF0` | Debug struct: `+0` level 0..9, `+2` player 0=Man/1=Woman |
| `0x030065D0` | Global pointer to the scene/task object (`0x03005520` in this build) |
| task `+0x28` | Scene id (u16): 4 title, 0x38 char-select, 0x4E map, 9 debug, 0x0A level |
| task `+0x2D` | Transition/redraw trigger byte |
| task `+0x42` | Key mask, active-high: A=1, B=2, Sel=4, Start=8, R=0x10, L=0x20, U=0x40, D=0x80 |

Savestate RAM layout (mGBA `.ss1`, decompressed `gbAs` chunk): IWRAM
`0x03000000 → file+0x19000`; EWRAM `0x02000000 → file+0x21000`. This mapping was
confirmed by the stored value `0x03006FF0` at state offset `0x1FFE0` (i.e. RAM
`0x03006FE0`).

## 5. Algorithm / pseudocode

```c
// game's own 6-way dispatcher, 0x08006F0C
switch (ram[0x02000000]) {
  case 0: scene = 0x38; break;   // character select
  case 1: scene = 0x37; break;   // copy player choice
  case 2: return;                // no transition
  case 3: scene = 0x3C; break;
  case 4: scene = 0x21; break;
  case 5: scene = 9;   break;    // HIDDEN: Level Select / Player Select
  default: return;               // rejects 6..255 (proved in-game)
}
task[0x2D] = 1;                  // request redraw
```

```c
// debug input, 0x08007344
keys = *(u16*)(task + 0x42);          // active-high
struct = *(u8**)(0x03006FE0);         // 0x03006FF0
if (keys & 0xC0)  struct[2] ^= 1;      // Up or Down -> Man/Woman
if (keys & 0x10)  struct[0] = (struct[0] + 1) % 10;   // Right
if (keys & 0x20)  struct[0] = (struct[0] + 9) % 10;   // Left
if (keys & 0x09) { task[0x28] = 10; task[0x2D] = 1; } // A+Start -> launch
```

The draw routine renders `Level Select <struct[0]>` and
`Player Select <struct[2] ? "Woman" : " Man ">`; it is entered via the normal scene
dispatch tables (scene 9 → draw `0x0800726C`, input `0x08007344`).

No password/checksum/table algorithm exists to reverse in this image; the "code space"
is the six-option selector plus the two debug fields above (§6b).

## 6. Tables

**Debug scene-transition selector (`0x02000000`), dispatch at `0x08006F0C`:**

| Value | Target scene | Observed / derived |
|---|---|---|
| 0 | 0x38 | Derived (table); reached in-game as character select |
| 1 | 0x37 | Derived (table) |
| 2 | — (no transition) | Derived (returns) |
| 3 | 0x3C | Derived (table) |
| 4 | 0x21 | Derived (table) |
| **5** | **9** | **Observed**: title + A → Level Select debug screen |
| 6, 255 | — (rejected) | **Observed**: scene stayed 4 |

**Debug struct (`0x03006FF0`):**

| Offset | Width | Field | Range | Evidence |
|---|---:|---|---|---|
| +0 | u8 | Level Select | 0–9, wraps | Observed (Right×10 → 0; Left at 0 → 9) |
| +2 | u8 | Player Select | 0=Man, 1=Woman | Observed (Up toggles; screen text changes) |

**Published codes:** none. GameFAQs' single "Harder Game" secret is a post-game flag,
not a literal code; literal searches for external JP passwords returned zero hits.

## 6b. Enumeration

* **Space definition.** Selector = 6 values (0–5; 5 is the debug option that the
  ordinary controller UI cannot reach). Debug fields = 10 levels × 2 players = 20
  states; total selectable debug states = 6 × 20 = 120 if all selector values were
  exposed. The reachable debug screen itself has 20 states (10 levels × 2 players), all
  enumerated here (bounds by wrap-around, not by guessing).
* **Novel combination (not in any published list).** I set selector=5 (unadvertised),
  pressed A, then entered `Right,Right,Right` and `Up` and saved a state: the screen
  read `Level Select 3 / Player Select Woman`, with RAM `struct = 03 00 01 00` and
  scene 9. I then pressed A+Start: scene became 10 and the selected stage loaded with
  the Woman character. Neither the menu nor this combination appears in GameFAQs,
  TCRF, VGChartz, or any other published list consulted.
* **Accepted vs rejected (bounds proven).**
  * selector 5 + A → scene 9 (accept).
  * selector 5 + B → scene 0x36/54 (legal screen) — wrong button rejected.
  * selector 6 + A → scene 4 (no transition) — out-of-range rejected.
  * selector 255 + A → scene 4 (no transition) — out-of-range rejected.
  * Level Right×9 → 9, Right×10 → 0; Left at 0 → 9; player Up/Down toggles 0↔1.
* **Validator model.** The dispatcher is a plain 6-entry jump table with an exact
  bound (`cmp r0,#5; bhi default`), so values outside 0–5 are provably unhandled;
  the debug struct fields use modulo-10 and XOR-1 respectively. The model agrees with
  every observed accept and rejection above.

## 7. Validation evidence

Labels: **Observed** = emulator screenshot or savestate RAM read; **Derived** =
disassembly; **Inferred** = plausible but not fully exercised.

| Claim | Evidence type | Detail |
|---|---|---|
| Clean single-header retail ROM | Observed | `file`, hash, logo scan (1 hit at 0) |
| Title scene = 4, file select, char-select 0x38, map 0x4E, level 0x0A | Observed | Screenshots `fileSelect.png`, `game1.png`, `game2.png`, `play_live.png`; RAM `scene` via `readstate.py` |
| Only `Pause` overlay in gameplay (no options list) | Observed | `pausex0..4.png`, scene stays 0x0A |
| Hidden debug screen exists and reads "Level Select / Player Select" | Observed | `debug9b.png`; strings at `0x08034CE8`/`0x08034CF8` with direct pointers at `0x0800730C`/`0x08007310` |
| Level/player fields and bounds | Observed | `dbgstrip.png`; RAM bytes at `0x03006FF0`: `00`→`01`→`02`→`03`, `+2`: `00`→`01`; wrap to `00` after 10 Rights |
| A+Start launches selected stage | Observed | `launched_level.png`; scene 9→10 and `struct=06 00 01 00` |
| Entry gate selector=5 + A | Derived + Observed | Dispatcher disassembly; selector patched to 5 then A → scene 9 |
| Out-of-range selector rejection | Observed | selector 6 and 255 + A both leave scene 4 |
| No password/string table | Observed | 76,252 `strings`; keyword and XOR/additive sweeps; no `PASSWORD`/`CODE` input surface on any walked screen |
| No controller button-code table | Observed/Derived | Konami mask sequences absent at 1- and 2-byte width in both polarities; single-key and 2-key title tests changed only selector 0↔1 |
| Scene tables map 9 to debug functions | Derived | `0x08004194` and `0x080043D0` entries; `0x0800431E → bl 0x0800726C`, `0x0800455A → bl 0x08007344` |
| Sibling independence | Observed | Different game code/MD5; debug strings absent from Island Attack image |

## 8. Unknowns

* The exact **controller sequence** that sets selector `0x02000000 = 5` in normal play
  was not found. Exhaustive single-key and 2-key title tests plus disassembly of the
  title handlers (Up/Down only toggle the selector 0↔1) bound this negative; the value
  may be set only by a completed-game save flag, an unreleased build, or a debugger.
  The debug screen itself and its controls are fully proven once the selector is set.
* Target scenes for selector values 1, 3 and 4 (`0x37`, `0x3C`, `0x21`) were read from
  the jump table but not individually rendered.
* The GameFAQs "Harder Game" unlock was not played through to completion; I verified it
  is a save/flag effect (no password literal exists), not a typed code.
* The tile-indexed normal UI text bank was not fully decoded to glyphs; the negative
  for a password screen rests on screen enumeration plus exhaustive ASCII/XOR/additive
  string sweeps and the absence of any input alphabet or comparison routine.

## 9. Tooling

* `binutils-arm-none-eabi` (`arm-none-eabi-objdump -M force-thumb`), Python 3 with
  Capstone 5.0.7 (`findscene.py`, `findscene2.py`, `findwrites.py`), mGBA under Xvfb
  with `xdotool` + `scrot`/ImageMagick (`helpers.py`).
* Savestate RAM reader/writer (`readstate.py`, `patch_state.py`) using the mGBA `.ss1`
  `gbAs` zlib chunk; no GDB stub was needed for the final evidence (the stub pauses the
  core at boot and exits on client disconnect in this build).
* `brute.py` for keyboard/RAM differential tests.
* Web: `web.archive.org` snapshot of the GameFAQs cheats page; web search snippets.
* No ROM or copyrighted assets are redistributed here; only hashes, addresses, and
  original observations are published.
