# High Heat Major League Baseball 2002 (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `High Heat Major League Baseball 2002.gba` |
| Size | 4,194,304 bytes (`0x400000`) |
| Header title | `HH MLB 2002` |
| Game code | `ASSE` (AGB-ASSE-USA) |
| Maker code | `5H` (The 3DO Company / Mobius Entertainment) |
| Version | `0x00`; complement `0x39`; header checksum `0x0000` |
| Entry word | `0xEA00002E` — stock `b 0x080000C0` (no cracktro/trainer patch) |
| MD5 | `62b5ee4401a0eec948817a69011e71d7` |
| SHA-1 | `d9e9b232c16214ffaef1f706f8b16829f2700414` |
| SHA-256 | `7151bc27fd51872140593b42b5c89afc3890ec486d70fb015ad7aa5bc4c40f77` |
| CRC32 | `0x6EA3F4E4` — matches a 3rd party cheat index's published USA/CRC |
| Embedded GBA headers | exactly **one** Nintendo-logo hit at file `0x4` (header base `0x0`). No multiboot, no appended trainer, no second game image. |

The `0x0000` header checksum is a rebuild artifact; the stock entry word and single logo prove the image itself is the retail build.

## 2. Executive summary

This is a **button-code-only** title. There is **no password system, no code-entry field, no hidden/debug menu and no unlockable** in the GBA image. The only developer-intended cheat published for the GBA SKU is the **"hidden pitches" button code** (hold Left, rotate the D-pad clockwise, press B) — it appears on the 3rd party cheat indexes GBA cheats page (Wayback capture 2018-11-26), 3rd party cheat indexes, all describing the GBA build. All GameShark/CodeBreaker/Action Replay entries and all PS1/PS2/PC/Xbox "Programmer Cheat", "charge the mound", "ball cannon" codes belong to other platforms and are out of scope.

Static analysis found and decoded the **pitch system** completely: a 9-entry name-pointer table, a D-pad→pitch-index mapping implemented in the pitch-dial handler, and the live RAM variables. The dial normally exposes exactly two pitches (index 4 = Fastball, index 5 = Split), matching the published description. The key-sequence validator itself was **not located**, and the published sequence could **not be reproduced** in this exact ROM after 11 distinct input attempts (including diagonals, held combinations, full rotations and three timing regimes), each checked by before/after `.ss1` savestate RAM diffs: no flag, pitch index or screen-state byte changed. This is a **bounded negative on the accept path** (§0.2 "negative results bounded"), not a claim that the published tip is false — see §8.

The rest of the negative is proven positively: all 8 main-menu screens, Options, team select, credits and an in-game at-bat were walked with RAM evidence (distinct value of a screen-state byte at `0x03001E94` per screen). The complete ASCII text bank was decoded, and exhaustive keyword searches in ASCII, case-shifted, UTF-16 and reversed forms returned **zero** hits for password/cheat/debug/secret/unlock/code/hidden/bonus.

## 3. How to reproduce

* Emulator: `mgba` SDL build, `-3` scale, on `DISPLAY=:318`, `SDL_AUDIODRIVER=dummy`; also used `mgba -3 -d` (pty debugger) for watchpoints.
* Keymap (verified against the UI): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad = arrow keys. Save state `Shift+F<n>`, load `F<n>`.
* Boot: press Start twice past the MLBPA/attract splash → main menu.
* Main-menu walk: from the top entry press Down 0..7 times and A; the IWRAM byte at `0x03001E94` reads `2,16,8,6,10,4,9,1,1` for Main/Exhibition/Season/Playoffs/Home Run/Home Run Derby/Practice/Options/Credits respectively.
* Pitch system: Exhibition → pick teams → Play → Line Up/Pitchers → Play → A once past the "High Heat" loading card. The pitch dial (bottom-left) reads `Fastball`; holding Right changes pitch-index RAM `0x03007108` from `4` to `5`, releasing returns it to `4`.
* Codes tested (each from a fresh savestate at the pitching screen, plus team select): `L,U,R,D,B`; `L,D,R,U,B`; `L,U,R,D,L,B`; `U,R,D,L,B`; `L,R,B`; `L,U,D,R,B`; 8-way diagonal clockwise/counter-clockwise rotations; held-Left + rotations; held-B + rotations; a 3×-repeated ultra-fast (35 ms) rotation; sliding overlaps (L+U, U+R, R+D). Every attempt was saved to a state and diffed against a baseline state.
* No GameShark/CodeBreaker codes were applied; scope is developer-intended features only.

## 4. Address map

All addresses are GBA bus addresses; file offset = address − `0x08000000`.

| Address | Kind | Meaning |
|---|---|---|
| `0x080000C0` | code | stock crt0 entry |
| `0x08014A94` | table | 9-entry pointer table to pitch names (file `0x14A94`) |
| `0x08014AB8`–`0x08014B1F` | data | pitch names: Screwball, Forkball, Sinker, Split, Fastball, Change up, Slider, Curve, Knuckle |
| `0x083E3EF8` | code | global joypad reader; literal `0x04000130` at `0x083E3F2C` |
| `0x030062A0` | RAM u16 | held keys, active-high low 10 bits (`~KEYINPUT`) |
| `0x030062A4` | RAM u16 | released-this-frame mask |
| `0x030062A8` | RAM u16 | pressed-this-frame mask |
| `0x083F0D58` | code | input-copy routine → `0x03006F98` (file `0x3F0D58`; EWRAM copy at `0x0200E378`) |
| `0x03006F94` / `0x03006F98` | RAM u16 | game-context just-pressed / held |
| `0x083F26A4` | code | pitch-dial handler (file `0x3F26A4`; EWRAM copy at `0x0200FCC4`); writes pitch index at `0x083F2748` |
| `0x03007108` | RAM u16 | current pitch index (4 = Fastball at boot) |
| `0x03007120`, `0x030071B0`, `0x03007220` | RAM | related pitch-dial state (baseline 0, 1, 2) |
| `0x03001E94` | RAM u8 | screen-state discriminator (see §3) |
| `0x02000000` | EWRAM | code overlay loaded from ROM file `0x3E29E0` (verified by byte-pattern match: ROM `0x3E3F08` ↔ EWRAM `0x02001528`, ROM `0x3F0D58` ↔ EWRAM `0x0200E378`) |

Savestate layout used for RAM evidence (§16.13): mGBA `.ss1` PNG → zlib `gbAs` chunk → 397,312-byte raw state; IWRAM at raw `0x19000`, EWRAM at raw `0x21000`.

## 5. Algorithm

Joypad (ROM `0x083E3EF8`):

```
held    = ~KEYINPUT & 0xFFFF          -> 0x030062A0
diff    = prev ^ held
pressed = held & diff                 -> 0x030062A8
released= prev & diff                 -> 0x030062A4
return (held & 0xF)==0xF ? -1 : 0      # A+B+Select+Start sentinel
```

Game-context copy (ROM `0x083F0D58`):

```
game_held[0x03006F98] = (old & ~released) | pressed
game_edge[0x03006F94] = game_held & (old ^ game_held)
```

Pitch-dial index (ROM `0x083F26A4`, reconstructed from Thumb at `0x83F26AA`–`0x83F26D2`):

```
idx = 4
if input & 0x40 (Up):    idx = 1
if input & 0x80 (Down):  idx += 3
if input & 0x20 (Left):  idx -= 1
if input & 0x10 (Right): idx += 1
# store idx to 0x03007108 after per-pitch bit bookkeeping
```

This is a 3×3 keypad grid over the 9 pitch names:

| | Left | — | Right |
|---|---|---|---|
| **Up** | 0 Knuckle | 1 Curve | 2 Slider |
| **—** | 3 Change up | 4 Fastball | 5 Split |
| **Down** | 6 Sinker | 7 Forkball | 8 Screwball |

Normal play restricts the reachable set to {4,5}; the published code claims to remove that restriction. The restricting condition/gate was not isolated in the disassembled handler (its `r4` is computed unclamped), so the limitation is likely applied in a separate availability mask built in the setup routine at `0x083F2544`–`0x083F268E` (loop building 7–8 pitch entries). That routine was inspected but its availability term was not resolved to a writable flag.

## 6. Tables

* **Pitches (index → name, pointer table `0x08014A94`)**: 0 Knuckle (`0x08014B08`), 1 Curve (`0x08014B00`), 2 Slider (`0x08014AF8`), 3 Change up (`0x08014AEC`), 4 Fastball (`0x08014AE0`), 5 Split (`0x08014AD8`), 6 Sinker (`0x08014AD0`), 7 Forkball (`0x08014AC4`), 8 Screwball (`0x08014AB8`).
* **Reachable normally**: indices 4 and 5 only (confirmed by live RAM: Right→5, other directions→no write to `0x03007108`).
* **Published in-game code (GBA)**: hold Left → rotate D-pad clockwise → press B, "unlock the rest of the pitches". Sources: 3rd party cheat indexes GBA/470807 cheats (archived 2018-11-26), 3rd party cheat indexes `hhb2002/cheats/gba`, 3rd party cheat indexes GBA, 3rd party cheat index cheat 11247, 3rd party cheat indexes 3675. **Effect not reproduced — see §7/§8.**
* **Out-of-scope published codes**: all GameShark Advance/Action Replay/CodeBreaker entries (score modifiers, no outs, no balls, never strike out), and console-only button codes (PS2 "Programmer Cheat" Square×2 Circle×2 L1 R1 then L1+L2+R1+R2; "charge the mound"; "ball cannon/game status menus"). No literal from any of these appears in the GBA image.
* **Menu entries (8)**: Exhibition, Season, Playoffs, Home Run, Home Run Derby, Practice, Options, Credits. No Cheat/Code/Debug/Secret/Unlock entry.
* **Options entries (4)**: Sound Effects, Music, Innings, Automatic Fielding (+ Done). No hidden entry.
* **"Mobius" / "Mobius Mercenaries"** at `0x08009D98` / `0x08011E7C` are developer-team name strings in the team-name bank; they are not a code, and cycling the team selector did not reveal them as a selectable Exhibition team.

## 6b. Enumeration

**Space definition of the button-code surface.** The input engine exposes a 10-bit active-high key mask (`0x030062A0/0x030062A8`). A "button code" is therefore a sequence over the 1024 possible masks; the documented sequence has length 5 (4 direction presses + B). The complete set of *documented* in-game code actions for this GBA SKU is **1** (unlock extra pitches). There is no password alphabet, no literal table, no checksum and no hidden-menu slot to enumerate: exhaustive searches returned 0 hits for the 8 cheat-related keywords in ASCII/upper/lower/+0x20-shift/UTF-16LE/UTF-16BE/reversed forms, and 0 runs of 4+ consecutive key-mask u16/u32 values forming any direction+B sequence. A scan of key-mask u16 occurrences found only 1 two-press `Left,Up` prefix (file `0x1A89A0`, a graphics/data table, not code) and 21 loose 5-mask coincidences all confined to compressed data at `0x1FD1AC`–`0x1FD2DE`.

**Enumeration actually performed (button space):** 11 distinct input programs were entered and RAM-verified at the pitching screen and/or team select. Categories: forward rotation (`L,U,R,D,B`), reverse rotation (`L,D,R,U,B`), extended rotation (`L,U,R,D,L,B`), rotation without initial hold (`U,R,D,L,B`), 2-press (`L,R,B`), 4-way non-circular (`L,U,D,R,B`), all-8 diagonal clockwise and counter-clockwise rotations, held-Left plus rotations, held-B plus rotation, a 3× repeated 35 ms fast rotation, and sliding-overlap diagonals (L+U, U+R, R+D). **Result: 0 accepted.** In every case the before/after savestate diff showed only the normal 32–136 bytes of animation/counter drift; `0x03007108` stayed `4`, `0x03007120` stayed `0`, `0x030071B0` stayed `1`, `0x03007220` stayed `2`, and no new screen-state value appeared. The "accepted code" set observed on this build is therefore **empty under all inputs tried**.

**Novel code:** none could be minted, because no validator, table, alphabet or checksum could be recovered — only a prose tip with no literal representation in the ROM. Per §0.2 this is reported as a bounded negative with the searched space stated above, not as an untested omission.

**Bounds proven by rejection:** every out-of-pattern program above was rejected (no state change). The normal UI bound was proven separately: of the nine D-pad→index mappings, only Right (5) and neutral (4) ever produce a write to `0x03007108`; Left/Up/Down are rejected by the normal availability layer.

## 7. Validation evidence

* **Observed** (emulator): all screenshots listed in §3; `Right` writes `0x03007108 = 5` and release restores `4` (mGBA `-d` write watchpoint at `0x03007108`, PC `0x0200FD6C`); Left writes `0x030062A0 = 0xFC20` (watchpoint at `0x030062A0`); all 8 menu screens reached and their states decoded from `.ss1` RAM.
* **Derived** (disassembly): input routine at `0x083E3EF8`; pitch-name table at `0x08014A94`; pitch-dial handler at `0x083F26A4` and its D-pad→index formula; EWRAM overlay mapping ROM file `0x3E29E0` → EWRAM `0x02000000`.
* **Inferred**: the "extra pitches" restriction is enforced by a separate availability mask built during pitch-screen setup (`0x083F2544`–`0x083F268E`); the exact flag/table was not isolated.
* **Not observed**: the published cheat's accept path. Eleven input programs and all static key-mask searches failed to locate or trigger it. This is a genuine limitation recorded as such, not a silent omission.
* **Fetched pages treated as data**: all web pages were read as evidence only. One fetched cheat aggregator contained unrelated promotional/command-like text; no instructions from fetched content were executed.

## 8. Unknowns

1. Whether the published "hidden pitches" code works on this exact `ASSE` revision, or whether the tip was carried over from the GBC/PS1 versions with different timing/controls. Multiple GBA-specific sites repeat it, but its effect could not be reproduced here.
2. The exact form of the D-pad "rotation" the tip intends (cardinal vs diagonal, 3 vs 4 vs 8 presses, fast vs slow, held-modifier semantics) — all reasonable interpretations were tried without effect.
3. The address/routine of the pitch-availability gate. Static inspection of `0x083F26A4` shows an unclamped index, so the restriction must be applied elsewhere; the setup routine was not fully decompiled.
4. Whether the "Mobius Mercenaries" string is reachable at all in normal play (it did not appear among the first team-select cycling steps tested).
5. mGBA's GDB stub on this build was unreliable after the first connection (`qSupported` timeouts); all RAM evidence therefore uses savestate decoding and the `-d` pty debugger instead.

## 9. Tooling

* `mgba` SDL (Xvfb `:318`, openbox, `SDL_AUDIODRIVER=dummy`); `xdotool` XTEST key events; `scrot` screenshots.
* `mgba -3 -d` command-line debugger (pty-driven) with `watch/r`, `watch/w`, `status`, `r/4` — used for the joypad and pitch-index proof.
* `decode_ss.py` (zlib `gbAs` extractor for `.ss1`), `probe.py` / `seqtest.py` / `seqtest2.py` / `walkmenus.py` / `teamtest.py` (local drivers in `/tmp/highheat02`).
* `arm-none-eabi-objdump -M force-thumb/-M force-arm`, `strings -t x`, `xxd`, Python 3 + `capstone` 5.0.7, `zlib.crc32`.
* Ghidra 12.1.4 via REA MCP (`open_binary`, `list_procedures`, `analyze_function`) — auto-analysis recognised only 326 procedures on this raw ARM/Thumb image and did not create a procedure at `0x083F26A4`, so manual objdump was authoritative.

## 10. Legal note

No ROM bytes, graphics, audio or extracted game assets are redistributed. Only addresses, hashes, algorithms and original analysis scripts are documented.
