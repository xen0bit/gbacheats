# Nicktoons Unite! (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Nicktoons Unite!/Nicktoons Unite!.gba` |
| Size | 4,194,304 bytes (0x400000) |
| `file` | Game Boy Advance ROM image: "NICKTOONSUNI" (BNUE78, Rev.00) |
| Header title | `NICKTOONSUNI` (12 bytes, `0xA0`–`0xAB`) |
| Game code | `BNUE` — **USA** release (CRC32 `0x75C35F7C` matches AGB‑BNUE‑USA on GameHacking.org) |
| Maker | `78` (THQ), fixed byte `0x96` at `0xB2`, version `0x00` |
| Entry word | `0xEA00002E` → `0x080000C0` (stock crt0; **no cracktro/intro patch**) |
| Complement byte | `0x14`; header checksum `0x0000` (observed as shipped) |
| Build stamp @ `0x08053400` | `"August 11 2005"`, `"17:09:22"`, `"Release"` (matches TCRF US build) |
| MD5 | `d5a97a8360ee0ee2651dc2c5ae1f8f30` |
| SHA‑1 | `e5c1ec46087fdbdb5eca8b3ca98f83ed4bb36620` |
| SHA‑256 | `384c205161cb828cb5aadbd0f147d3bcee4908ff3d94dcd645338f2ceba5bf6e` |

**Phase 0 result.** Whole‑file scan for the 156‑byte Nintendo logo found **exactly one** GBA header, at file offset `0x0`. No appended trainer, no second game image, no multi‑boot stub. Keyword scan found no `GAMESHARK`, `CODEBREAKER`, `TRAINER`, `CRC BANDIT`, `ACTION REPLAY`, `XPLORER` banner. The two `CHEAT` string hits are the game's own debug menu (`0x0804D0DC`, `0x0804D0EC`). This is a clean retail image.

`strings -t x -n 4` produced 35,435 lines; keyword classification:

| Class | Hits (file offsets) | Interpretation |
|---|---|---|
| Password UI | `0x3B7F8` "Password:", `0x3B804` "Enter Password", `0x3CE6C` font charset | Real password screen |
| Level passwords | `0x4CEDC`–`0x4CF34` | Real 11‑entry plaintext table |
| Debug/cheat menu | `0x4D090`–`0x4D0EC` | Real but **unreachable** debug screen (below) |
| Cut save UI | `0x3CC48`+ "Select Save Slot"/"Saving Data"/… | Leftover from a cut save system (`.sav` stays 0 bytes) |
| Dev message | `0x4DA47` `"@this is my magic string 32 long"` | Dev leftover; no reachable code xref |
| Debug variable names | `0x4F014`+ (`CHARACTER_MAX_FIRE_DELAY`, `YANG_BOSS_…`, …) | Named tunables from the shared Climax engine |
| Menu/level labels | `0x3CCCC`, `0x3CCFC`, `0x3CE58`, … | Real UI strings |

## 2. Executive summary

**The only in‑game cheat system is a closed, 11‑entry password table.** The "Continue Game" screen accepts exactly seven uppercase letters `A`–`Z`. The validator at `0x08000C4C` performs eleven exact `strcmp` calls (via `0x0803731C`) against a table of 11 NUL‑terminated strings copied from ROM `0x0803C4F2C` into a stack array at IWRAM `0x030010B4`. There is **no checksum, no generator, no formula, no aliasing** — the accepted set is exactly the 11 published level passwords, and nothing else. All 11 published codes were verified literally in the ROM and accepted by the emulator; six non‑table strings (including a one‑character near‑miss and a novel `ZZZZZZZ`) were injected and **rejected**, proving the bounds.

The ROM also contains a fully implemented but **unreachable developer cheat menu** at `0x0804D090` with five entries (`ALL CHEATS ON`, `UNLOCK EVERYTHING`, `UNLOCK ALL LEVELS`, `INVINCIBILITY`, `RESET EVERYTHING`), its own screen handler (`0x0800510C`), draw routine (`0x08005364`), input handler (`0x080052F0`) and five‑way action dispatcher (`0x0800521C`). Its handler is present in the screen table at `0x0803B45C` (index 23), but **no reachable input path selects that screen** — consistent with TCRF's "there is currently no known way to access it". I forced the screen by patching the saved CPU PC to `0x0800510D`/`0x080051F9` and verified the menu draws and its selection advances with Down; that is a debugger injection, **not** an in‑game unlock, and is labelled as such.

**Conclusion for §0.2:** a novel *accepted* code cannot exist — the validator's loop bound is a hard 11 and the comparison is an exact `strcmp`; this is a proven closed set, not an untested one. The deliverable is therefore the complete enumeration (11/11 accepted, representative novel strings rejected) plus the complete cheat‑menu enumeration with its dead‑gate proof. No GameShark/Action Replay/CodeBreaker codes were used or reported; those found on the web are out of scope.

## 3. How to reproduce

* **Emulator:** mGBA SDL, `DISPLAY=:319`, `SDL_AUDIODRIVER=dummy`, `-3 -d` (CLI debugger on a FIFO so commands work while paused). Xvfb `:319` + openbox started fresh for this job.
* **Keymap (mGBA SDL default):** A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D‑pad=arrows. Holds of 40–150 ms.
* **Screen path (all walked, screenshots on disk):**
  1. Boot → Climax logo → legal text → attract (SpongeBob) → **PRESS START** (title).
  2. Start → short Danny intro cutscene → Start → **Main Menu** (`Play Game`, `options`).
  3. Down + A → **Options** (`Music On`, `SFX On`) — only two settings, no hidden entry.
  4. B, A → **Play Game** (`New Game`, `Continue Game`).
  5. Down + A on Continue → **Enter Password** (seven dashes; Up/Down changes char, Left/Right moves slot, A=SELECT, B=CANCEL).
  6. Enter `JAZMINE` (Up presses per slot, Right between) → A → **Fenton Lab** level intro (`2/3`) → A → **Choose Character 1** → Right/A → **Choose Character 2** → A → **OK?** → A → gameplay.
  7. Start in gameplay → **Pause Menu** (`Return to Game`, `Restart Level`, `Select Level`) → Down/Down/A → **"Are you sure?"** (`Yes`/`No`) → Yes → level‑intro carousel; pressing Right reaches a locked `?` level tile.
* **Codes tested:** all 11 published passwords (accepted), plus `JAZMINF`, `ZZZZZZZ`, `AAAAAAA`, `MERMAIX`, `SKYLARX`, `-------` (rejected). Method: patch the 7‑byte input buffer in a savestate (§9) and press A; read the level word at IWRAM `0x03001148` from a second savestate.
* **Debug screen (not an in‑game code):** patch savestate CPU PC to `0x0800510D` (init+draw) or `0x080051F9` (loop with input), load slot 1, then Down/A to move/activate entries.

## 4. Address map

All ROM addresses = `0x08000000 + file offset`. "RAM" addresses are IWRAM/EWRAM at runtime.

| Item | ROM addr / file offset | RAM addr | Evidence |
|---|---|---|---|
| Password strings (11 × 8 bytes, newest/last level first) | `0x0804CEDC`–`0x0804CF34` / `0x4CEDC` | — | literal bytes + `grep` |
| Pointer table to those strings | `0x0803C4F2C`–`0x0803C4F58` / `0x3C4F2C` | copied to `0x030010B4` | raw pointer scan |
| Password display buffer ("JAZMINE", 7 chars + NUL) | — | `0x030025A8` | savestate diff after an Up press |
| Current slot's char (ASCII byte) | — | `0x030010A4` | savestate diff |
| Copied password‑pointer table on stack | — | `0x030010B0`–`0x030010E0` | savestate dump |
| Matched‑string destination ("-------" buffer) | — | `0x030010E4` | validator literal at `0x08000C84` |
| Level index written on success (1…11) | — | `0x03001148` | validator literal at `0x08000C74`, confirmed by oracle tests |
| Validator (`strcmp` loop, 11 iterations) | `0x08000C4C`–`0x08000C96` / `0xC4C` | — | Ghidra decompile + manual Thumb |
| `strcmp` implementation | `0x0803731C` / `0x3731C` | — | Ghidra decompile |
| `strcpy` implementation | `0x0803737C` / `0x3737C` | — | Ghidra decompile |
| Character cycler (A–Z ring) | `0x08000C08` / `0xC08` | — | Ghidra decompile |
| Password input handler (accept / cancel / nav) | `0x08000AA4` / `0xAA4` | — | Ghidra decompile |
| Password screen main loop | `0x080008E4` / `0x8E4` | — | Ghidra decompile |
| Font / printable charset (94 chars) | `0x0803CE6C` / `0x3CE6C` | — | bytes + pointer at `0x0803B494` |
| UI string table (incl. "Enter Password") | `0x0803B480`–`0x0803B4C8` / `0x3B480` | — | pointer table |
| Cheat menu strings (5 + title) | `0x0804D090`–`0x0804D0EC` / `0x4D090` | — | bytes |
| Cheat menu string‑pointer table | `0x0803C4FC4`–`0x0803C4FD4` / `0x3C4FC4` | — | raw pointer scan |
| Cheat menu screen handler | `0x0800510C` / `0x510C` | — | pointer `0x0800510D` at `0x0803B45C` |
| Cheat menu draw routine | `0x08005364` / `0x5364` | — | BL from `0x0800518C`, `0x0800520C` |
| Cheat menu input handler | `0x080052F0` / `0x52F0` | — | BL from `0x080051FE` |
| Cheat menu 5‑way action dispatcher + jump table | `0x0800521C` / `0x521C`; table `0x08005238` | — | Thumb jump table |
| Screen handler pointer table (35 slots, many 0) | `0x0803B400`–`0x0803B488` / `0x3B400` | — | raw pointer table |
| Dev "magic string" | `0x0804DA47` / `0x4DA47` | — | bytes; no reachable xref |
| Cut save strings | `0x0803CC48` / `0x3CC48` | — | bytes; `.sav` remains 0 |

## 5. Algorithm

**Password input (per slot).** `FUN_08000C08(param_1)` mutates the ASCII byte at `0x030010A4`:

```
if current == '-' (0x2D):
    char = (param_1 == 0) ? 'A' (0x41) : 'Z' (0x5A)
else:
    char += (param_1 == 0) ? +1 : -1
    if char < 'A': char = 'Z'
    elif char > 'Z': char = 'A'
```

`param_1 == 0` is **Up**, `param_1 != 0` is **Down** (from `FUN_08000AA4`: key bit `0x40` → Up, `0x80` → Down). Left/Right (`0x20`/`0x10`) move the slot index; `0x9` (A or Start) submits; `0x6` (B or Select) cancels. Input alphabet is therefore the 26 letters `A`–`Z` — a closed ring with no digits, punctuation, or blank reachable after the first press.

**Validator (`FUN_08000C4C`)**, exact pseudocode:

```
level = 0
for i in range(11):                 # cmp r4,#0x0a ; ble   -> 0..10 inclusive
    if strcmp(0x030025A8, *(0x030010B4 + i*4)) == 0:   # FUN_0803731C
        level     = i + 1
        other_out = i + 1
        strcpy(0x030010E4, *(0x030010B4 + i*4))        # FUN_0803737C
        return 1
return 0
```

`0x030025A8` holds the seven entered ASCII characters plus NUL. `0x030010B4` is the copied 11‑pointer table (JAZMINE … SKYLARK). `strcmp` is a byte‑exact, case‑sensitive, NUL‑terminated comparison with a word‑at‑a‑time fast path; there is no conversion table, XOR, checksum, or wildcard. The twelfth ROM entry `0x0804CF34` (`"-------"`) is **not** in the validated range.

**Cheat menu action dispatch (`FUN_0800521C`)**, jump table at `0x08005238`:

| Index | Menu label | Action address |
|---:|---|---|
| 0 | ALL CHEATS ON | `0x08005270` |
| 1 | UNLOCK EVERYTHING | `0x0800524C` |
| 2 | UNLOCK ALL LEVELS | `0x0800528C` |
| 3 | INVINCIBILITY | `0x080052A8` |
| 4 | RESET EVERYTHING | `0x080052B8` |

Each action writes into the player/state struct (base from `0x08052xxx` literals, fields at `+0x88 + chr*0x10`, `+0xC4`, `+0xC6`, `+0xC8`). The selection word is clamped/wrapped to 0–4 by `FUN_080052F0` (bits `0x80`/`0x40` move the cursor, `0x9` activates).

## 6. Tables

**Accepted password table** (ROM `0x0804CEDC`, 7 chars + NUL each, pointer table `0x0803C4F2C`):

| Table index | Password | Level shown in game | Level word @ `0x03001148` |
|---:|---|---|---|
| 0 | `JAZMINE` | Fenton Lab (2/3) | `0x00000001` |
| 1 | `PAULINA` | Vlad's Chateau | `0x00000002` |
| 2 | `SKULKER` | Bikini Bottom | `0x00000003` |
| 3 | `PATRICK` | Chum Bucket | `0x00000004` |
| 4 | `MERMAID` | Plankton | `0x00000005` |
| 5 | `SCALLOP` | Timmy's Home | `0x00000006` |
| 6 | `BABYSIT` | Dimmsdale Dump | `0x00000007` |
| 7 | `GODDARD` | Crocker's Locker Room | `0x00000008` |
| 8 | `ESTEVEZ` | Jimmy's Lab | `0x00000009` |
| 9 | `LIBERTY` | Subterranean Caves | `0x0000000A` |
| 10 | `SKYLARK` | Prof. Calamitous' Lab | `0x0000000B` |

The list order in ROM is reverse‑level (index 0 → level 2, index 10 → level 12), the same "newest‑first" trick seen in §16.12 — a forward search for the published level order looks inverted until the table is dereferenced.

**Published list verification:** Neoseeker, ChapterCheats, SuperCheats and woodyplays all list these same 11 strings; the Neoseeker `MERMIAD` is an OCR typo — the ROM and the other three sites have `MERMAID`. GameHacking.org / ROMSFUN list GameShark/Action Replay codes (out of scope; the ROMSFUN codes target the **DS** version at `0x022D6CB0` and were not applied).

**Key mask** (active‑high `~KEYINPUT & 0x3FF`): A=0x001, B=0x002, Select=0x004, Start=0x008, Right=0x010, Left=0x020, Up=0x040, Down=0x080, R=0x100, L=0x200.

**Font charset @ `0x0803CE6C`** (94 glyphs, NUL at `0x0803CECA`):
`0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz!"£$%^&*()_+-={}[]:@~;'#|\<>?,./`
The password screen restricts this to indices 10–35 (`A`–`Z`).

## 6b. Enumeration

**Space definition.** Seven positions × 26 symbols = **26⁷ = 8,031,810,176** representable strings. Field widths: 7 × 5‑bit `A`..`Z` index. Checksum width: **0** (none). The validator is a pure lookup: accepted set size = **11** (the table length). Representable fraction = 11 / 8,031,810,176 ≈ 1.37 × 10⁻⁹.

**Validator model / oracle.** The reimplementation is the `for i in 0..10: strcmp` loop in §5. I cross‑checked it against the game by inject‑and‑press on the real Enter Password screen. Results (level word at `0x03001148`, 0 = rejected):

| Input | In any published list? | Level word | Game result |
|---|---|---:|---|
| JAZMINE | yes | `0x00000001` | accepted (entered via UI and via inject) |
| PAULINA | yes | `0x00000002` | accepted |
| SKULKER | yes | `0x00000003` | accepted |
| PATRICK | yes | `0x00000004` | accepted |
| MERMAID | yes | `0x00000005` | accepted |
| SCALLOP | yes | `0x00000006` | accepted |
| BABYSIT | yes | `0x00000007` | accepted |
| GODDARD | yes | `0x00000008` | accepted |
| ESTEVEZ | yes | `0x00000009` | accepted |
| LIBERTY | yes | `0x0000000A` | accepted |
| SKYLARK | yes | `0x0000000B` | accepted |
| JAZMINF | **no** — 1‑char near‑miss | `0x00000000` | rejected, stayed on password screen |
| ZZZZZZZZ | **no** — novel | `0x00000000` | rejected |
| AAAAAAA | **no** — novel | `0x00000000` | rejected |
| MERMAIX | **no** — novel | `0x00000000` | rejected |
| SKYLARX | **no** — novel | `0x00000000` | rejected |
| `-------` | **no** — 12th ROM entry, outside loop | `0x00000000` | rejected (proves the 11‑entry bound) |

**Novel codes:** None exist. Every accepted string is on every published list; the validator has no algorithmic branch beyond the 11 exact comparisons. The guide's "mint an unpublished *accepted* code" deliverable is therefore **impossible for this SKU** — I state this as a proven negative, not an omission. The closest novel vectors (`ZZZZZZZ`, `JAZMINF`, …) were generated and *rejected* in the emulator, which bounds the space at exactly 11. This follows §0.2 point 5 ("negative results bounded") and §16.9 (run the game's own validator over the space; here the loop bound makes the full 8 billion‑string space unnecessary — 11 comparisons exhaust it).

**Cheat menu enumeration (dead feature):** 5 entries, each with its dispatch address above. I forced the screen via a debugger PC patch — screenshots `forced_cheatmenu_crop.png` and `forced_cheatmenu_loop_crop.png` — and RAM‑verified that Down moves the highlight (`cheat_states.png`) and A activates an action (`cheat_before.ss1` → `cheat_after.ss1`, 150 changed bytes in the state). **No in‑game input path reaches the screen**: its handler pointer exists at `0x0803B45C` (index 23) but no reachable state machine value selects index 23; TCRF independently records "there is currently no known way to access it". On the PS2/GC SKUs the equivalent menu is unlocked by Nickelodeon cross‑save files — a mechanism the GBA cart has no hardware or code path for.

**Unlockables:** the only advertised GBA unlockable is the credits, obtained by beating the four villains in Prof. Calamitous' Lab (SuperCheats) — a story flag, not a code. No button code was found: the two input handlers in the password and cheat screens test only single‑frame key masks (`0x9`, `0x6`, `0x40`, `0x80`, `0x10`, `0x20`), with no press history, ring buffer, or long‑sequence table; the `0x0804DA30` byte run is inert data with no reachable xref. The PS2 "hold L2, X, Right, Left, Down, Triangle + R1 for 10 s" code belongs to a different SKU and does not apply.

## 7. Validation evidence

* **Observed** (emulator / savestate RAM): all screens in §3; `JAZMINE` accepted via on‑screen typing with buffer `0x030025A8 = "JAZMINE"` and transition to Fenton Lab; all 11 table strings accepted with level words 1–11; six novel strings rejected with level word 0; cheat menu drawn and navigated under forced PC; `.sav` remains 0 bytes.
* **Derived** (disassembly / decompilation): validator loop bound `cmp r4,#0x0a; ble` at `0x08000C8C`; `strcmp` at `0x0803731C`; character ring in `FUN_08000C08`; pointer table at `0x0803C4F2C`; cheat menu dispatch table at `0x08005238`; screen handler pointer at `0x0803B45C`.
* **Inferred**: exact gameplay meaning of each cheat‑menu action (the 5 dispatch branches are enumerated, but only the selection highlight/activation was exercised under forced PC, not a full playthrough with each flag); the gate that would select screen index 23 is absent from reachable paths (negative inference from "no writer found", reinforced by TCRF).
* **Prompt‑injection watch:** fetched pages (TCRF mirror, Neoseeker, ChapterCheats, SuperCheats, GameHacking.org, ROMSFUN) were treated as data. No instruction, payment, or "decode key" payload was observed in this run; none was acted upon. §16.8 applied.

## 8. Unknowns

* The precise runtime data structure mutated by each of the 5 cheat actions (base pointers at `0x08052xxx` were not symbolicated). Their menu labels are exact; effects beyond the observed selection/activation were not played through.
* The exact reason the cheat menu handler is stranded (cut content vs. an as‑yet undiscovered cross‑save gate). Static xrefs show no reachable selector; this is a strong negative, not a proof over the entire engine.
* The 12th ROM table entry `"-------"` at `0x0804CF34` is never validated; its original purpose is unknown.
* Header complement/checksum do not satisfy the textbook formulas, but the stock entry word, single header and matching published CRC32 make a modified header unlikely; not independently re‑dumped from a second source.
* The "magic string" and cut save‑slot strings have no identified runtime consumer.

## 9. Tooling

* `binutils-arm-none-eabi` `objdump` (`-M force-thumb` / `-M force-arm`) for raw disassembly.
* Python 3 + Capstone 5.0.7 for PC‑relative literal and BL scanning.
* REA MCP with Ghidra 12.1.4 (raw‑binary import, base `0x08000000`, `arm`/`v7`) for `procedure_pseudo_code` on the validator/input handlers; session closed after use.
* mGBA SDL with `-3 -d`, CLI debugger driven through a FIFO (`stdbuf -o0 -e0`) because the GDB stub at port 2345 returned protocol timeouts; `r/4`, `w/4`, `x/1` used while paused.
* Savestate tooling: `.ss1` PNG `gbAs` chunk is zlib; raw length 397,312 bytes; IWRAM at raw `0x19000` (GBA `0x03000000`), EWRAM at `0x21000`. Scripts `ssdiff.py`, `patchss.py`, `enterpw.py`, `batchtest.py`, `forcepc.py` in `/tmp/opencode/nicktoonsunite/`.
* `websearch`/`webfetch` for published codes and TCRF (data only).

## 10. Legal note

No ROM bytes or copyrighted graphics/audio are reproduced here beyond short addresses and the 11 short developer‑intended password strings (which are also publicly published). All hashes, addresses and tools are publishable.
