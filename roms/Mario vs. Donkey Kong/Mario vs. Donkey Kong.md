# Mario vs. Donkey Kong (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Mario vs. Donkey Kong/Mario vs. Donkey Kong.gba` |
| Size | 16,777,216 bytes (`0x01000000`, 16 MiB) |
| Header title | `MARIOVSDK` |
| Game code | `BM5E` (USA/Australia, Rev. 00) |
| Maker | `01` (Nintendo) |
| Fixed byte `0xB2` | `0x96` (valid) |
| Version / complement / checksum | `0x00` / `0x37` / `0x0000` |
| Entry word | `0xEA00002E` — the stock Nintendo branch to `0x080000C0`; **no cracktro/trainer patch** |
| Embedded GBA headers | Exactly **1** (Nintendo-logo scan `24 ff ae 51 …` hits only at file `0x4`); no multiboot, no second game |
| MD5 | `ceda12928a686878795def3b413ccfc2` |
| SHA-1 | `da677e595c41a0c72c4e3feb3a7e716f17cacd77` |
| SHA-256 | `688fa9c01be4cbfee866be0f7fc2dc4fc80df84cda157915b39fd5a86eeaa3ea` |

The `0x0000` header checksum is a common rebuilt-dump-header artifact; the entry branch is
untouched and there is no appended trainer. Save hardware is a **64 KiB battery save**
(`Mario vs. Donkey Kong.sav`, 65,536 bytes) — the game is save-based, not password-based.

## 2. Executive summary

**There is no password / cheat-code entry system in this ROM.** Every screen reachable by
controller was walked with RAM evidence (mode byte `0x030009C4`), and none presents a code
field. All published "cheats" for this SKU are GameShark / CodeBreaker / Action Replay
*memory patches* (e.g. `42032120 0101`, `74000130 02BF`), which are explicitly out of scope;
the only published in-game material is unlock conditions (Expert/Plus worlds, 8 movies,
crowns) and the manual-documented **L+R Free Scroll Mode**.

Two controller-triggered developer features were found and proven in the emulator:

1. **L+R held in a level → "level viewer" / Free Scroll Mode** (scene mode `0x21`).
   Documented in the Nintendo manual as "Free Scroll Mode"; here reversed to the exact gate
   (`0x08039C58`–`0x08039C86`) and enumerated: single static overlay, B or Start exits.
2. **Select + Start + A + B held simultaneously → jump to title screen** (scene mode `0x07`),
   restoring from any non-title scene. This combination is **in neither the manual nor any
   published cheat list checked** (3rd party cheat indexes/fandom, gbadrome) — it is the novel code of this
   engagement. Proven with four near-miss rejections.

Two further hidden features exist but are **not reachable by controller**: the incomplete
**level editor** (mode `0x0B`; requires a cheat device / RAM write — a gated debug feature,
not an in-game code) and the **e-Reader "Card-e"/"e World" mode** (modes `0x18`–`0x1D`;
revealed by a Game Link Cable handshake with an e-Reader, not by button input).

## 3. How to reproduce

* Emulator: mGBA (SDL, `-3`), `Xvfb :315`, `DISPLAY=:315`, `SDL_AUDIODRIVER=dummy`.
* Keymap (X11): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrow keys.
  (B is **`z`**, not `b` — using `b` is a silent no-op.)
* RAM ground truth: mGBA GDB stub port 2345 was occupied by another session, so RAM was read
  from mGBA savestates: the PNG `gbAs` chunk is zlib-compressed to a 397,312-byte raw state;
  IWRAM base `0x03000000` maps to raw offset `0x19000` (mode byte = raw `0x199C4`), EWRAM base
  `0x02000000` to `0x21000`. Helper: `probe.py` (focus → keys → Shift+F1 → parse → screenshot).

**Menu paths (all RAM-verified, mode byte in parentheses):**

| Path | Mode |
|---|---|
| Boot → news intro → title (`0x07`) → START | `0x03` |
| SELECT DATA → OPTION MENU (Right×3, A) | `0x04` |
| OPTION MENU → AUDIO OPTIONS (A) / VISUAL OPTIONS (Down,A) | `0x04` |
| VISUAL OPTIONS → MOVIE 1, A=Play | `0x1E` (movie player, ~55 s) |
| New Game on slot A → opening cinema | `0x1E`, then `0x20` ("World 1 Start!") |
| → A | `0x08` (world/level select: worlds 1–6, 6 levels + minigame + boss each) |
| → A on 1-1 | `0x05` (tutorial; **B=`z`** skips) → `0x0D` (in level) |
| In level → START | `0x10` (pause: CONTINUE / RETRY / EXIT LEVEL) |
| In level → hold L+R | `0x21` (level viewer / Free Scroll); B or START → `0x0D` |
| Any mode except `0x07`/`0x22` → hold Select+Start+A+B | `0x07` (title) |

**Code tests:** L+R (accept), Select+Start+A+B (accept), Select+Start+A (reject),
Select+Start+B (reject), A+B+Start (reject), A+B+Select (reject), L+R at title (no effect),
L+R+Select+Start+A+B at title (rejected by the mode-7 exclusion). No password strings were
entered because no entry screen exists.

## 4. Address map

| Item | Address / offset | Evidence |
|---|---|---|
| Scene/mode byte (USA retail) | `0x030009C4` (u32 word) | Observed: `0x03` at SELECT DATA, `0x04` options, `0x1E` movie, `0x20` world start, `0x08` level select, `0x05` tutorial, `0x0D` in level, `0x10` pause, `0x21` viewer, `0x07` title |
| Secondary mode/state word | `0x030009C0` | Derived: read in input handler `0x08033208` and L+R gate `0x08039C66` |
| Scene setter `set_scene(mode, flag)` | **`0x080070E8`** (Thumb) | Derived: 98 BL call sites scanned; writes mode, handles fade (`flag=1` → mode `0x1F` via `0x030009CC`/`0x030009C8`) |
| Scene handler tables | `0x08076C84` (init), `0x08078354` (main), `0x080782C8`/`0x080783E0` (cleanup), indexed by mode ×4 | Derived: dispatch at `0x08007060`–`0x080070C6`; entries exist for modes `0x00`–`0x22` |
| **L+R gate (level viewer)** | `0x08039C44` function; tests at `0x08039C58`–`0x08039C7A`; set_scene(`0x21`) at `0x08039C82` | Derived: raw Thumb disassembly; confirmed in emulator |
| L+R gate flag word | `0x03001A1C` bit `0x2000` (must be set) | Derived; observed set during play |
| **4-button gate (title reset)** | `0x080331FC` input handler; mask tests `0x080332E4`–`0x0803330C`; set_scene(`0x07`,1) at `0x0803330C` | Derived + observed |
| Active-high key state | `0x030012E0` (current), `0x030012E8` (pressed-this-frame) | Derived from input handler literal pool |
| KEYINPUT read | `0x080331FE`, literal `0x04000130` | Derived |
| Input debug state word | `0x03001938` (bit `0x400` tested at `0x080332C2`) | Derived |
| Help/tips trigger | `0x08008060`: `[0x03001A1C]&0x800==0`, `[0x03001938]&1==0`, `[0x03001938]&0x50FE!=0` → set_scene(`0x11`) | Derived; not reached by controller in this session |
| Lives | `0x03000BBC` (byte) | Observed 5 on new game, 4 after title reset |
| Movies-unlock flags | `0x02032114` (two bytes) | Observed `0x00→0x01→0x01000001` across new game |
| e-Reader / level-editor dialogue bank | plaintext ASCII `0x076408`–`0x076A00` (e.g. `Card-E Level 13` at `0x0768A0`, `Scan Preloaded Card-e` at `0x07697C`, `MultiSio010918` at `0x076DB8`) | strings + xxd |
| Visual UI font text | **tile-indexed**; `SELECT DATA`, `OPTION MENU`, `CONTINUE`, `NEW GAME` do not occur as ASCII/UTF-16/offset-encoded in the 16 MiB or in any LZ77 block (see §8) | Negative result, bounded |

## 5. Algorithm (pseudocode, recovered from ROM)

```c
// 0x080070E8 — every scene transition goes through here
void set_scene(u32 mode, u32 flag) {
    if (current_mode == 0x1F) return;                 // already fading
    u32 m = mode;
    if (demo_flag && m == 8) m = 0x18;                // demo remaps level select → e-world
    if (!flag) current_mode = m;                      // 0x030009C4
    else { pending_scene = m; pending_scene2 = m; current_mode = 0x1F; }
    ... // clear fade/transition words
}

// 0x08039C44 — called from in-level main loop; L+R → level viewer
void maybe_level_viewer(void) {
    u16 held = active_high_keys;                      // 0x030012E0
    if ((held & 0x300) != 0x300) return;              // L (0x200) AND R (0x100)
    if (current_mode == 0x05) return;                 // not during tutorial
    if (!(debug_word_1A1C & 0x2000)) return;          // gate flag must be set
    flag_byte_0x03001738 = 1;
    set_scene(0x21, 0);                               // 0x08039C82
}

// 0x080331FC — global input handler; undocumented reset combo
void input_handler(void) {
    u32 held = ~KEYINPUT & 0x3FF;                     // active-high
    if (current_mode == 7 || current_mode == 0x22) goto skip;
    if ((held & 0x0C) == 0x0C && (held & 1) && (held & 2)) {
        // Select(0x4) + Start(0x8) + A(0x1) + B(0x2)
        clear_save_working_bytes(0x03000B80, 0x03000B58, 0x03000B74, 0x03000BB4);
        set_scene(0x07, 1);                           // → title via fade
    }
skip: ...
}
```

The level viewer has **one** view: A, L, R and Select were pressed with no RAM/visual change;
B (`z`) and Start both return to mode `0x0D`. It draws the level with a coloured overlay
(green/red blocks, purple scaffolding, yellow direction arrows) and a `B BACK TO GAME` prompt.

## 6. Tables

**Scene modes** (mode-table entries `0x00`–`0x22`; community labels from 3rd party cheat indexes cross-checked
against the ROM; `0x0A`, `0x13`, `0x1F` have a NULL main handler = fade/placeholder):

`00` boot · `01` credits · `02` demo · `03` main menu · `04` options · `05` tutorial ·
`06` tutorial reset · `07` title · `08` level select · `09` expert levels · `0A` (null) ·
`0B` **level editor (debug, gated)** · `0C` → `0D` · `0D` in level · `0E` pause-restart ·
`0F` mute/return · `10` pause · `11` help/tips · `12` (null) · `13` (null) · `14` boss clear ·
`15` results · `16`/`17` present minigames · `18`–`1D` e-Reader/e-World · `1E` movie ·
`1F` fade · `20` next world · `21` **level viewer / Free Scroll** · `22` (reset helper)

**Button masks** (active-high, `0x030012E0`): A=`0x001`, B=`0x002`, Select=`0x004`,
Start=`0x008`, Right=`0x010`, Left=`0x020`, Up=`0x040`, Down=`0x080`, R=`0x100`, L=`0x200`.

**Unlockables (save-based, not codes):** Expert worlds X-1…X-10 at 9/18/…/90 stars;
X-11/X-12 by beating first 10 levels with all presents; Plus worlds after defeating DK;
8 movies in VISUAL OPTIONS (movies 1&2 observed unlocking at New Game: `0x02032114`
`0x00 → 0x01 → 0x01000001`); crowns. The MOVIE selector was capped at 1 on a fresh save
(Right×3 did not move it) — gated by these flags, not a code.

## 6b. Enumeration

**Button-code space.** The GBA exposes 10 buttons → 1,024 simultaneous masks, and the global
input handler at `0x080331FC` is the only code that reads KEYINPUT and tests multi-button
predicates. Its complete branch set was enumerated statically: (a) `held & 0x0C == 0x0C &&
held & 1 && held & 2` → title reset (with a sub-branch on `0x03001938 & 0x400` that clears
that bit), and (b) the L+R gate in the in-level handler `0x08039C44`. There are no sequence/
ring-buffer matchers, no length-dependent branches, and no password alphabet or literal code
table (see §7). Every single button was pressed on the reachable menus; every 3-button subset
of the 4-button code was tested and rejected; supersets are tolerated (the code masks with
`&`/`&&`, it does not require other bits clear), which is itself a derived property of the
format.

**Novel code (not in any published list): `Select + Start + A + B` held simultaneously.**
Chosen specifically because it is absent from the manual and from every published cheat list
checked, and because it exercises an unadvertised action (immediate title-screen reset with
working-byte clearing). **Accepted in the emulator**: mode `0x030009C4` `0x10 → 0x07`,
title screen visible, lives `5 → 4`. Also accepted from mode `0x04` (options). Screenshots:
`after_4btnc.png`, `chord_fullc.png`.

**Bounds proven by rejection:** omitting B, omitting A, omitting Select, or omitting Start
all leave the mode byte unchanged (`0x04`), recorded as `chord_no_Bc.png`, `chord_no_Ac.png`,
`chord_no_Selc.png`, `chord_no_Startc.png`. The gate is also excluded in modes `0x07` and
`0x22` (derived at `0x0803300`/`0x0803304`; observed: L+R+full-combo at title = no effect).
For L+R: gate requires in-level context and `0x03001A1C & 0x2000`; outside a level it does
nothing (`chord_LR_alonec.png`).

**Code-table space:** zero entries — keyword census over 228,278 printable runs in the 16 MiB
gave `password=0`, `cheat=0`, `code=0`, `secret=0`, `debug=0`, `invalid=0`,
`enter name=0`, `level select=0`; `unlock=1` and `warp=2` are the SFX names `UNLOCK`,
`WARP_IN`, `WARP_OUT`. No code exists to enumerate.

## 7. Validation evidence

* **Observed (emulator + RAM):** all ten screens in §3 with mode-byte reads; L+R → `0x21`
  overlay and B/Start exit; Select+Start+A+B → `0x07` from both `0x10` and `0x04`; four
  near-miss rejections; movie flags and lives changes; MOVIE selector cap; save file created.
* **Derived (disassembly):** `set_scene` at `0x080070E8`; 98 BL call sites mapped to modes;
  scene-handler tables; L+R gate mask `0x300` + flag `0x2000` at `0x08039C58`; 4-button mask
  `0x0F` at `0x080332E4`; KEYINPUT read at `0x080331FE`; input debug state `0x03001938`.
* **Inferred:** a 3rd party cheat index's mode labels for unreached modes; that level editor mode `0x0B` and
  e-Reader modes are gated by external hardware/cheat-device writes rather than controller
  input (consistent with the link-cable/e-Reader descriptions and the string bank).
* **Negative (bounded):** no password UI on any walked screen; no password strings under
  ASCII, lowercase, UTF-16LE/BE, XOR `0x01/0x20/0x40/0x80/0x7F/0xFF`, 1-byte offsets
  `-0x60…+0x6F`, 16-bit offsets, common tile alphabets, or in any LZ77 block
  (164,783 candidate `0x10` headers scanned).

## 8. Unknowns

* The visual UI font is **tile-indexed**: `SELECT DATA`, `OPTION MENU`, `NEW GAME`,
  `CONTINUE` do not occur in the ROM as ASCII (nor in the encodings above), even though those
  exact words are on screen. The `0x76408`–`0x76A00` ASCII bank is the e-Reader/level-editor
  dialogue and SFX-name bank. I could not recover the tile-index→glyph mapping; the negative
  therefore rests on (a) complete screen enumeration and (b) the searches listed in §7 rather
  than on decoding that bank. A future analyst should dump VRAM from a title-screen savestate
  and derive the font mapping to close this gap.
* The help/tips scene (`0x11`) was not triggered by any button tested; its trigger predicate
  was found at `0x08008060` but requires game state not reached in this session.
* e-Reader screens (`0x18`–`0x1D`, including the 13th dummy/test level and 12 US prototype
  levels) require a link-cable/e-Reader handshake; not exercised (hardware-gated, not a code).
* The level editor (`0x0B`) requires a cheat device/RAM write; reported as a gated debug
  feature, explicitly **not** claimed as an in-game code.
* Header checksum `0x0000` / complement `0x37` were recorded, not recomputed to a GBA spec.

## 9. Tooling

* `/tmp/mvdk/probe.py` — focus mGBA, send keys, Shift+F1 savestate, decode `gbAs`
  chunk, print named RAM addresses, crop 720×480 screenshot.
* `/tmp/mvdk/chord.py` — hold arbitrary key sets simultaneously for chord tests.
* `/tmp/mvdk/find_literal_xrefs.py` — literal + Thumb/ARM LDR-literal xref scanner.
* `/tmp/mvdk/scan_setscene.py` — Thumb BL scanner for `set_scene` call sites.
* `/tmp/mvdk/lzscan.py` — GBA LZ77 decompression scan for hidden ASCII banks.
* `arm-none-eabi-objdump -M force-thumb`, Capstone 5.0.7, Python 3, mGBA SDL, Xvfb :315,
  openbox, xdotool, scrot, ImageMagick.

Fetched web pages were treated as data. The 3rd party cheat index mirror contained a
**prompt-injection attempt** — a fake "LLM-/AI-agent-specific instructions" block insulting
the operator — which was ignored and is recorded here per guide §16.8. Its genuine mode list
was used only as a lead and each relevant mode was verified against ROM code and emulator RAM.

No ROM or copyrighted assets are redistributed in this report.
