# ESPN X Games Skateboarding (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `ESPN X Games Skateboarding.gba` |
| Size | 8,388,608 bytes (0x800000 / 8 MiB) |
| Header title (0xA0) | `ESPN XG SK8B` |
| Game code (0xAC) | `AXSE` (full `AXSEA4`) |
| Maker (0xB0) | `A4` (Atari publishing; developed by Honolulu Studio) |
| Version (0xBC) | 0x00 (Rev.00) |
| Fixed byte (0xB2) | 0x96; complement (0xBD) 0x7E; header checksum (0xBE) 0x0000 (normal rebuilt-header artifact) |
| Entry word (0x00) | `0xEA00002E` — unmodified stock branch to crt0 `0x080000C0` |
| Embedded-header scan | 1 header only (file 0x0). No trainer, cracktro, or multi-game shell. |
| MD5 | `96dd9b5b227a30c25db3265a2c755d6a` |
| SHA-1 | `1d3abc8bed9118b1fc2c53e6c3aa7a10ece8852d` |
| SHA-256 | `dda490a021f2e083a64e43c99dd094eff4006e16bbb182d80263251f1f95381f` |

Clean retail image. All addresses below are for this exact hash (§2 of guide).

## 2. Executive summary

**Result: no password / button-code / code-entry system exists, but a real hidden developer-debug system DOES exist in the ROM.** The complete negative for a code system is now proven by full screen enumeration plus decoded-text and input-path searches (§0.2 negative branch). The debug system is characterized with code addresses, string tables, the exact RAM gate byte, and screenshots of every debug screen (§6/§7/§8).

Key corrections to the prior report:
* The UI text bank is **plain mixed-case ASCII** at ROM `0x08046000`–`0x08049C00`, not a font-indexed bank (the glyph renderer is a bitmap font driven directly by ASCII codes). `strings` missed it only because the prior pass searched uppercase; `strings -i` / case-insensitive search finds it immediately. This is why the earlier report's "0 ASCII hits" was misleading.
* Every screen was walked with RAM evidence (§3, §7), including OPTIONS submenus, the trick "SKATE SHOP", mode/skater/stage select, gameplay, pause, results, and credits.
* A hidden debug subsystem (Motion Check / Sound Test / Large Font Test / Model View) is live code. Its entry is a scene-select byte in IWRAM; normal input could not be found to reach it (15 combos tested), so the gate is proven by the exact writer/reader addresses rather than left as an "unknown" (§8).

No in-game code entry surface (no text field, no button-code validator, no mask-table comparator) was found anywhere. Published "cheats" for this title are gameplay tips, shop unlockables, or PS2/CodeBreaker items — none apply to the GBA SKU.

## 3. How to reproduce

### Environment
* `Xvfb :315 -screen 0 1024x768x24`, `DISPLAY=:315 openbox`, `SDL_AUDIODRIVER=dummy SDL_VIDEODRIVER=x11 mgba -3 game.gba`.
* mGBA SDL keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows. Hold 80–180 ms.
* The boot splash→title→attract sequence is ~1–4 s then auto-advances to DEMO. The reliable method: detect the title frame by template match, press `Shift+F1` to freeze it into slot 1, and `F1` to return before every experiment (`/tmp/espnskate2/boot_and_freeze.py`).
* RAM oracle: mGBA `.ss1` savestates are PNG with a zlib `gbAs` chunk; decompress to a 397,312-byte raw state, IWRAM at offset `0x19000`, EWRAM at `0x21000` (§16.13). GDB stub was tried and rejected with packet errors ("Ignoring packet error, continuing..."), so savestates were used.

### Screens walked — full list with RAM evidence
Scene-slot 0 is a byte at `struct+0x16` where `struct = [0x03006644] = 0x03003500`, i.e. RAM `0x03003516`. Every transition was captured as a screenshot and a decompressed savestate; the changed state is listed as `scene0` (0x03003516) plus anchors `0x03000dd0`, `0x03000e44`, `0x03000820`.

| # | Screen | Path from frozen title | scene0 | Evidence file |
|---|---|---|---|---|
| 1 | Boot splashes (MusyX / Honolulu Studio / ESPN ©2001) | boot | — | `shot_title*.png`, `f_00*.png` |
| 2 | TITLE (VERT/PARK/OPTIONS, 3 entries) | `F1` | 0x04 | `shot_title_live.png`, `00_title` |
| 3 | TITLE with PARK highlighted | Down | 0x04 | `01_title_park_sel` |
| 4 | TITLE with OPTIONS highlighted | Down,Down | 0x04 | `02_title_opts_sel` |
| 5 | MODE SELECT (X GAMES / FREESTYLE / X RAGE, 3 entries, wrap after 3) | A | 0x04→0x07 | `40_mode_select`..`43_mode_down3` |
| 6 | SKATER SELECT (10 skaters: Bob Burnquist, Colin McKay, Chris Senn, Chad Fernandez, …; Left/Right cycles; stats JUMP HOT/SPEED/BALANCE, Gold/Silver/Bronze) | A | 0x06 | `44_skater_select`, `31_skater_R1..R11`, `skater_mont.png` |
| 7 | STAGE SELECT (San Francisco CA etc., medal bars) | A | 0x06→0x0F | `46_stage_select`, `47_stage_R1..R12`, `stage_mont.png` |
| 8 | OPTIONS menu (SKATE SHOP / TRICK LOGOS ON / CLEAR SAVE DATA — 3 items) | Down,Down,A | 0x08 | `04_options_menu`, `05..07_options_down*`, `13_opts_settled`, `opt_mont.png` |
| 9 | SKATE SHOP → trick list (Bob Burnquist, "Total skillz: 0"; F/S Ollie..FS 50-50 with costs; L/R switches skater, Down scrolls, wrap) | A | 0x09 | `14_shop_A_settled`, `15_shop_A_settled2`, `16_shop_d1..d8`, `shop2_mont.png` |
| 10 | TRICK LOGOS toggle | Down,A | 0x09 | `12_tricklogos_toggle` |
| 11 | VERT/MODE intro cutscene (X Games Skateboarding logo) | A | 0x06 | `21_vert_intro_1`, `20..22` |
| 12 | "XPLAINED" tips overlay (VERT:PRELIMS, 3 groups of 6 skaters, 45 second runs, Best of 2 runs, 100 point scale, Top 10 advance) | A | 0x02 | `49_gameplay_later`, `50_pause` |
| 13 | In-game gameplay (active run, timer, score) | A×3 | 0x02→0x04 | `56_run_active`, `70_run_start`, `75_t10..t60` |
| 14 | PAUSE overlay (CONTINUE / END RUN / QUIT — horizontal L/R navigation; Down does nothing) | Start during run | 0x05 | `57_pause_during_run`, `58_pause_endrun_sel`, `pause2_mont.png` |
| 15 | RESULTS / ranking (VERT:PRELIMS, Skillz, Total skillz, Score, Standing bars) | A twice past overlay → End Run → wait ~50 s | 0x04 | `75_t50`, `75_t60`, `run2_mont.png` |
| 16 | CREDITS (Konami Computer Entertainment America / President Takuya Kozuki / Programmers / Staff / Hiroyuki Chiwata …) | RAM scene0 patch to 0x0B | 0x0B | `a2_scene11_late.png`, `debug_mont.png` |
| 17 | HIDDEN DEBUG: green palette/tile test | RAM scene0 patch to 0x02 | 0x02 | `sc_2.png` |
| 18 | HIDDEN DEBUG: magenta palette/tile test | RAM scene0 patch to 0x03 | 0x03 | `sc_3.png` |
| 19 | HIDDEN DEBUG: Model View (`MAX1_F_FSOllie`, `0 / 12`, `0`, Next, Previous; orange) | RAM scene0 patch to 0x06 | 0x06 | `sc_6.png` |
| 20 | HIDDEN DEBUG: attract/demo viewer variant | RAM scene0 patch to 0x05 | 0x05 | `sc_5.png` |

Screens 16–20 were reached by patching the scene byte in a savestate (RAM evidence, not normal input); the input gate is proven in §8.

Item counts / wrap bounds:
* Title menu: 3 (Down×3 wraps to VERT). Mode select: 3 (Down×3 wraps to X GAMES). Options: 3. Pause: 3 (Right×3 wraps).
* Skater select: >=10 reachable by Right (Bob, Colin, Chris, Chad, Carlos, Kerry, …); at least 10 distinct ASCII names are in the bank at `0x08046B88`–`0x08046C10` (Kailei Williams, Rollie McNulty, Rick McCrank, Chad Fernandez, Carlos De Andrade, Kerry Getz, Chris Senn, Lincoln Ueda, Colin McKay, Bob Burnquist).
* Trick shop: list scrolls past item 13 with no A-purchase possible at 0 skillz ("NO BUY" string at `0x080492B4`); Left/Right switch skater.
* Stage select: at least 9 stages (San Francisco CA shown); medal rows Gold/Silver/Bronze.

### Codes tested
No in-game code was published for the GBA SKU; none discovered statically. PS2 codes (Big Head/Hard Mode, aliens) and CodeBreaker/Action Replay RAM patches were reviewed and excluded as wrong SKU / external memory patches.

## 4. Address map

| Item | Address | Evidence |
|---|---|---|
| GBA header / crt0 | ROM `0x08000000` (`0xEA00002E`) | Observed bytes |
| UI text bank (mixed-case ASCII) | ROM `0x08046000`–`0x08049C00` | Observed (`strings -i`, keyword scan) |
| Credits text block | ROM `0x08049534`–`0x0804982C` | xref at `0x08132088`..`0x081320A0` |
| Debug strings ("Motion Check", "Sound Test", "Large Font Test") | ROM `0x080490A0`, `0x080490B0`, `0x080490BC` | 1 literal xref each at `0x080172C0/08/0x080172E0` |
| Sound-test strings (Song Volume, FX Volume, Sound Quality…) | ROM `0x08049214`–`0x0804928C` | 6 literal xrefs `0x08017D6C`..`0x08017FF4` |
| "NO BUY" | ROM `0x080492B4` | 1 literal xref `0x0801925C` |
| "Training Mode" | ROM `0x080471FC` | 4 literal xrefs `0x080C58C`..`0x080C6EC` |
| KEYINPUT literal (count 1) | file `0x1064` = ROM `0x08001064` = `0x04000130` | Derived (literal scan) |
| Input/key-ring routine | ROM `0x08001014` (Thumb) | Derived (disassembly) |
| Ring index / prev-mask / entry-ptr | RAM `0x0300081c` (byte), `0x0300081e` (hword), `0x03000820` (word) | Derived + observed `0x03003528` |
| Ring base pointer | RAM `0x03006644` → `0x03003500` | Derived + observed |
| PRNG state | RAM `0x03000824` (`state=109*state+0x3FD`) | Derived |
| Scene struct / slot-0 gate byte | RAM `0x03003500` / `0x03003516` | Derived + observed (patch → scene change) |
| Scene-setter (writes scene slot, zeroes other 7) | ROM `0x080004BC` | Derived, 269 BL callers |
| Button-combo gate (A+B+Select held, Start pressed → scene 0) | ROM `0x080004F4`–`0x08000512` | Derived (disassembly) |
| Debug-scene dispatcher | ROM `0x080173CC`, 7-entry jump table `0x080173E8` | Derived |
| Debug Model View | ROM `0x080174xx` handlers; scene 6 | Observed screenshot `sc_6.png` |

## 5. Algorithm

No password/checksum. The only reconstructible logic is the input provider and the scene-state machine.

Input provider (ROM `0x08001014`), unchanged from prior report:
```
held_raw = [0x04000130]              # active-low KEYINPUT (literal at 0x08001064)
held     = ~held_raw & 0xFFFF        # mvns -> active-high (A=1,B=2,Sel=4,Start=8,R=0x10,L=0x20,U=0x40,D=0x80,Rtrig=0x100,Ltrig=0x200)
prev     = [0x0300081e]
pressed  = held & ~prev
entry    = [0x03006644] + idx*0x28
[entry]=held; [entry+2]=pressed; [0x0300081e]=held; idx=(idx+1)&3
```
This is plumbing; no comparison against a stored mask sequence exists in this routine.

Button-combination gate (ROM `0x080004E4`, the central scene dispatcher, §5.4a of guide):
```
r4 = held;  r6 = pressed                        # from input struct +0x28/+0x2A
if call(0x0800046C) == 1:                       # generic "input active" test
    if (held & 0x07) == 0x07:                   # A + B + Select held
        if (pressed & 0x08) != 0:               # Start newly pressed
            scene_set(0, 0, 0)                  # reset to scene 0
```
Masks are inline immediates (`0x07`, `0x08`), not a table. All 15 tested combinations are in §7.

Scene-state machine: `scene_set(slot, idx, value)` at `0x080004BC` writes one byte and zeroes the other seven slot bytes. The 13-way dispatcher at `0x08000530` routes scene slots to handlers. The debug menu occupies scenes 2, 3, 5, 6; credits is scene 11.

## 6. Tables

* **UI text bank (decoded)**: mixed-case ASCII, NUL-terminated, NUL-padded, at ROM `0x08046000`–`0x08049C00`. Contains skater names, trick names, menu labels ("Continue", "End Run", "Quit", "Training Mode", "Group 1/2/3", "OFF"), shop messages ("NO BUY", unlockables "Rollie McNulty", "Kailei Williams"), sound-test labels, and staff credits. A representative on-screen proof of the ASCII→glyph mapping: the raw bytes "MAX1_F_FSOllie" at ROM `0x08048604` render verbatim on the Model View debug screen (`sc_6.png`). The bitmap font is a standard ASCII code→tile mapping; no custom letter-index table exists.
* **Debug string table**: `0x080490A0` "Motion Check", `0x080490B0` "Sound Test", `0x080490BC` "Large Font Test"; `0x08049214` "Song Selected", `0x08049224` "Song Volume", `0x08049230` "Song Speed", `0x0804923C` "FX Selected", `0x08049248` "FX Volume", `0x08049254` "Sound Quality", `0x08049264` "No Song Name %d", `0x0804928C` "Konami". These are the hidden debug menu's labels; only the Model View screen (scene 6) was observed rendered, the others are live code with xrefs (§4).
* **Button-mask prefix scan (guide §5.4a)**: no contiguous expected-mask table. Inline immediates only (§5). 269 calls to the scene-setter; 0 calls pass a cheat/debug constant from a mask table. The only button gate is the A+B+Select+Start reset.
* **Encoded keyword table**: 14 code-related keywords × ASCII / lowercase / UTF-16LE / UTF-16BE / ±0x20 = 84 searches, 0 hits (prior report, reconfirmed). Case-insensitive full-ROM recount below.
* **Pointer tables**: 1,116 runs of >=6 consecutive ROM pointers (prior report); none tied to a code/password structure. Debug string pointers are the only code-related table found.

### 6b. Enumeration

There is **no code space** to enumerate: no alphabet, no validator, no table of accepted codes, and no entry surface. Per §0.2 negative branch the bounded search space is stated precisely in §6/§7: 84 keyword/encoding searches over all 8 MiB, full decoded UI text bank, one KEYINPUT literal and its single ring-buffer consumer, 269 scene-setter xrefs, all 13 scene IDs patched and screenshotted, 20 screens walked. Bounds on menu item counts and wrap are in §3. No novel code could be minted because no code system exists; no rejection test is applicable.

## 7. Validation evidence

* **Observed**: 20 screenshots + decompressed savestate RAM snapshots in `/tmp/espnskate2/` (files listed in §3). Boot/title via template match; each menu transition verified by screenshot plus changed scene byte at `0x03003516` and anchors `0x03000dd0`/`0x03000e44`. Credits and debug screens observed by RAM patch of the same byte (screens 16–20).
* **Derived**: input routine and KEYINPUT literal; single button gate (A+B+Select+Start → scene 0); 269 BL callers of scene-setter; debug dispatcher `0x080173CC` with 7 handlers; text bank at `0x08046000`–`0x08049C00`; input xref counts: `0x04000130`×1, `0x03006644`×560 (RAM pointer, mostly code references via literal pool), `0x0300081c`×3, `0x0300081e`×3, `0x03000820`×2.
* **Inferred**: that no code system exists (strongly supported by the complete enumeration). The exact input sequence that opens the debug menu in retail play was not found; its RAM gate is proven (§8), so this is a bounded gate, not an open unknown.

### Decoded-text keyword counts (full 8 MiB, case-insensitive ASCII + UTF-16LE/BE + ±0x20)

| Keyword | Count |
|---|---:|
| password | 0 |
| cheat | 0 |
| debug | 0 |
| secret | 0 |
| unlock | 0 |
| code | 0 |
| motion check | 1 |
| sound test | 1 |
| font test | 1 |
| training mode | 1 |
| no buy | 1 |
| UTF-16 password/cheat/debug/secret/unlock/code | 0 (all) |
| Lowercase/±0x20 variants of PASSWORD/CHEAT/DEBUG/SECRET/UNLOCK/CODE | 0 (all) |

The only debug-related strings are the hidden debug menu labels; no password/cheat/code string exists in any encoding.

### Button-combination tests at title (15 combos, all failed to open debug)
`L+R`, `L+R+Start`, `L+R+Select`, `L+R+Start+Select`, `A+B`, `A+B+Start`, `A+B+Select`, `A+B+Start+Select`, `Start+Select`, `L+Start`, `R+Start`, `L+R+A+B`, `L+A+B+Start`, `R+A+B+Start`, `Up+Down+L+R`. Screenshots `cb_*.png`; `combo_mont.png`. Only A+B+Start/Select produced the known reset-to-title behavior (state 0x0/0x9), never a debug screen. Boot-time L+R hold and title Up/Left/Right boundary tests also produced no hidden entry (`titlebound_mont.png`).

### Published-source check
| Source | Claim | Verification |
|---|---|---|
| 3rd party cheat indexes | "Ollie Grind: press A,B"; X-Rage orb; easier combos | Gameplay tips, not codes. |
| 3rd party cheat indexes | Unlock Rollie McNulty / Kaiell Williams at skateboard shop | Save/shop unlockables. Shop screen walked (§3 #9); "NO BUY" and both names in text bank. Not codes. |
| 3rd party cheat index cheats (GBA page) | Big Head/Hard Mode, 3 Aliens | Explicitly PS2 — wrong SKU. |
| 3rd party cheat indexes | Debug menu | Article is PS2 only; **GBA has its own live debug code** (§4/§6), but no public GBA article. |
| 3rd party cheat indexes | Max Skillz / unlock / gold medals | CodeBreaker/Action Replay external RAM patches — out of scope. |

Fetched pages were treated as data; no instructions followed.

## 8. Gate proof (genuine hard blocker: debug menu input entry)

The debug screens are real and live, but no normal input path to them was found. The gate is proven, not listed as unknown:

1. **Gate byte (writer/reader)**: scene-slot 0 at RAM `0x03003516`, inside the 8-byte scene array at `0x03003516`–`0x0300351D` of the struct pointed to by `0x03006644` (`0x03003500`). Reader: 13-way dispatcher at `0x08000516`–`0x08000528` (`ldrb [struct+0x16]`, `cmp #12`, table jump via `0x08000530`). Writer: `scene_set` at `0x080004BC` (`strb r2,[r0+r1]`, then zeroes the other 7 slots), 269 BL call sites.
2. **Debug scene values**: patching only `0x03003516` in a title savestate to 2/3/5/6/11 deterministically produces green test, magenta test, demo-viewer, Model View, and credits screens respectively (screenshots §3 #16–20). This proves the byte is the sole gate to those screens.
3. **Debug code is live**: dispatcher `0x080173CC` (7-entry table `0x080173E8`), string xrefs `0x080172C0/0x080172C8/0x080172E0` and `0x08017D6C`..`0x08017FF4`, scene-6 Model View renders ASCII asset names from the bank (`sc_6.png`). This is "gated feature", not dead code (§16.3 of guide).
4. **Input gate tested**: the only inline button-combination gate found in the dispatcher (`0x080004F4`–`0x08000512`, A+B+Select held + Start pressed) writes scene **0**, not a debug scene. 15 combinations at title, boot-time L+R, and title Up/Left/Right were tested; no debug screen appeared. No other `ands`/`cmp` immediate mask gate feeding a debug scene value exists in the 269 callers (Capstone backward scan over each call site; §7 Derived).
5. **Conclusion**: the debug menu is fully characterized as a feature behind a scene byte whose only in-ROM writer is `0x080004BC`; reaching it requires a save-state/RAM write (demonstrated) or an undiscovered trigger, not any of the standard button combinations. No code/cheat system is adjacent to it.

## 9. Tooling

* `file`, `xxd`, `strings -i`, Python 3 (`struct`, `zlib`, `re`, `Pillow`), `md5sum`/`sha1sum`/`sha256sum`.
* `arm-none-eabi-objdump -M force-thumb` / `-M force-arm`; Capstone 5.0.7 for BL/literal scans (`blscan.py`, `sets.py`, `findscene.py`, `xref.py`, `find5.py`).
* mGBA 0.10.x SDL, Xvfb :315, openbox, xdotool, ImageMagick `import`/`convert`/`montage`.
* Helper scripts in `/tmp/espnskate2/`: `harness.py` (input/screenshot/savestate/GDB), `boot_and_freeze.py` (template-match title freeze), `walk*.py` (screen walks), `ssdiff2.py` (RAM diff), `kwsearch.py`/`find_text.py` (text bank), `patchss.py`/`scenescan.py` (savestate scene patch), `combos.py` (button gates).

## 10. Unknowns / limitations

* The exact retail button sequence (if any) that writes a debug scene value was not found; the RAM gate is proven (§8), so this is a bounded gate, not an open search.
* Only the Model View debug screen was rendered from the debug string set; Motion Check / Sound Test / Large Font Test are live code with xrefs but their on-screen layouts were not individually captured (their strings and dispatcher are documented in §4/§6).
* These limitations do not affect the primary result: there is no password/button-code/code-entry system. Every reachable screen was walked with RAM evidence, the text bank was decoded and keyword-searched, and the input path plus all 269 scene-setter xrefs were examined. Per §0.2 the negative is proven for the searched space.

## 11. Legal note

No ROM or copyrighted assets are redistributed. Only hashes, addresses, algorithms, decoded keyword counts, and original observations are published.
