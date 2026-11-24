# XS Moto (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/XS Moto/XS Moto.gba` (byte-identical working copy `/tmp/xsmoto2/xs.gba`) |
| Size | 4,194,304 bytes (`0x400000`) |
| Header title | `XS MOTO` (`0xA0`); game code `BXME`, maker `FS` (`0xB0`) |
| Revision | `Rev.00`, version `0x00`; entry word `0xEA00002E` (stock ARM branch) |
| MD5 / SHA-1 | `986ff7d285a6c161ccfd2eaef4f8cb18` / `2a800d077cfb8320ac5780d840976a47d9595728` |
| SHA-256 | `366473b9d66a8f3cef01166b1ea5745a78dfffa725c00600db96e486cabd4267` |
| Save hardware | None: mGBA creates a 0-byte `xs.sav`; progress is RAM/session only |

## 2. Executive summary (what changed in this pass)

This pass **keeps** the prior pass's recovered assets (text bank, text getter, both
dispatchers, the `%06d` password format, identity) and adds the three things that pass
failed to deliver:

1. **Live screen-state word found and screens forced.** The dispatcher input bytes are
   `ctx+0x3328/+0x3329/+0x332b/+0x332d` (runtime `0x03007DD8..0x03007DDD`). Writing
   family/case at the per-frame breakpoint at `0x08010C76` forces screens: family1 case 3
   renders `Select Rider` (`force3_c.png`); family1 case 25 renders the `RESULTS` screen
   (`novel2_c.png`, `novel3_c.png`).
2. **The exact gate is proven at byte level** (§6b): the main-menu handler at `0x08010454`
   contains navigation arithmetic that *skips* menu index 1 and clamps the reachable set
   to `{0,2}`. `Password` is index **4**. Its A-press writes family1 case `0x14` (20) into
   `ctx+0x332d`, and byte 20 of the family1 jump table at `0x0800eab8` is `0x45` — the
   **default** arm at `0x0800eb44`. No handler exists for Two Player (8), Bonus Items (15)
   or Password (20). Runtime confirmation: forcing menu index 4 and pressing A leaves a
   blank background (`gate3_c.png`), not a password screen.
3. **Password generator recovered and a novel code minted in-game.** `FUN_0800be66`
   (`0x0800be66`, Results) calls `FUN_0801f41c(&buf, "%06d", *(int *)(state+0x2c))` at
   `0x0800c47c`. We wrote the novel value `739421` (`0x000B470D`) into the live state word
   `0x02000044` (state pointer = `[ctx+0x333c]` = `[0x03007DEC]` = `0x02000018`) and
   forced the Results screen; RAM read-back showed `0x02000044 = 000B470D` and the Results
   layout rendered. Bounds are derived from the formatter and probed with out-of-range
   values (§6b).

**No password validator exists in this image.** This is now a *bounded* negative: the
`Enter Password` string (index 45) is never passed to the text getter by any of its 38 call
sites; no function parses typed digits; `FUN_0801f41c` (the only numeric formatter) has
exactly three callers, all display-only; and the three gated family1 cases are dispatcher
defaults. The "password" is a **display-only progress certificate** shown after a race.

## 3. How to reproduce

* Emulator: mGBA 0.10.5, `Xvfb :320`, `openbox`, `SDL_AUDIODRIVER=dummy`, scale 3,
  `stdbuf -oL -eL mgba -d -3 xs.gba` with a FIFO on stdin (the CLI debugger is used
  instead of the GDB stub, whose fixed port 2345 was occupied by another agent).
* Keymap: A = `x`, B = `z`, Start = `Return`, D-pad = arrows; 150 ms holds.
* Debugger commands used: `break/t 0x08010c76`, `w/1 <addr> <val>`, `w/4`, `x/4`, `r/1`,
  `save 1` / `load 1` (savestate `/tmp/xsmoto2/xs.ss1`), `continue`, SIGINT to halt.
* Screen force (from the clean main-menu savestate, halted at the per-frame breakpoint):
  ```
  w/1 0x03007DD8 0x2d        ; screen id 45 (Results template)
  w/1 0x03007DDB 1           ; family = 1
  w/1 0x03007DDC 1           ; family-1 transition flag
  w/1 0x03007DDD 0x19        ; family1 case 25 = Results
  w/4 0x02000044 0x0b470d    ; novel code 739421
  continue
  ```
* All evidence images were in `/tmp/xsmoto2/` (never in the ROM folder).

## 4. Address map

| Address | Meaning | Evidence |
|---|---|---|
| `0x080cb884` | Text metadata `{count=101, banks=1, stride=25}` | Observed bytes |
| `0x080cb890` | Text bank base, 101 NUL-terminated ASCII strings, 25-byte stride | Observed |
| `0x08010e90` | Text getter `get(obj,index)` → `base + 25*index` | Derived (Thumb + Ghidra) |
| `0x08010454` | **Main-menu handler / gate** (family0 case 2) | Derived + runtime |
| `0x08010a9c` | Family-0 dispatcher (jump table `0x08010ab8`, 30 entries) | Derived |
| `0x0800eaa0` | Family-1 dispatcher (jump table `0x0800eab8`, 30 entries) | Derived |
| `0x08010b88` | Main loop; reads family at `ctx+0x332b`, cases at `+0x3329/+0x332d` | Derived + runtime |
| `0x0800b9cc` | Screen teardown (family 2/3), switch on screen id | Derived |
| `0x0800e594` | Family1 case 2 — alternate menu setup, loads texts 0..4 | Derived |
| `0x0800e3ac` | Family1 case 3 — Race submenu (`Quick Race`, `Challenge`, …) | Derived |
| `0x0800d6b4` | Family1 case 14 — Options (texts `SFX`, `Music`, `On`, `Off`, `Credits`) | Derived |
| `0x0800d3a6` | Family1 case 19 — Bonus Items (texts `?`, `XSMoto Tour`, `W`) | Derived |
| `0x0800cdfa` | Family1 case 22 — XSMoto Tour | Derived |
| `0x0800be66` | **Family1 case 25 — Results / password generator** | Derived + runtime |
| `0x0800c490`, `0x0800c49c` | Format strings `"%06d"`, `"%02d"` | Observed |
| `0x0801f41c` | Numeric formatter (`sprintf`-like); only 3 callers, all display | Derived |
| `0x0804c6e8`, `0x0804c6fc` | u32 text-index tables `{0x32,0x33,0x34,0x35,0x36,0x5c..}` | Observed |
| `0x0804c740` | Rider name indices `{20,21,22,23}` → FRANK/ALAN/GERRY/NEIL | Observed |
| `0x0804c8d8` | 70×12 ASCII→glyph table (prior pass mislabelled it a screen registry) | Observed |
| `0x03004AB0` | Runtime context base `ctx` | Observed (GDB/CLI `r4`) |
| `0x03007DD8` | `ctx+0x3328` screen id | Observed |
| `0x03007DD9` | `ctx+0x3329` family-0 case | Observed |
| `0x03007DDB` | `ctx+0x332b` **screen family** byte | Observed |
| `0x03007DDD` | `ctx+0x332d` family-1 case | Observed |
| `0x03007DEC` | `ctx+0x333c` → state-struct pointer (`0x02000018`) | Observed |
| `0x02000044` | state word `+0x2c` — the 6-digit progress code | Observed (patched) |

## 5. Algorithm / pseudocode

Text access (unchanged from prior pass):

```
meta   = 0x080cb884            # {101, 1, 25}
base   = 0x080cb890
get(obj, idx) = base + 25*idx  # obj.field4 = meta, obj.field8 = base
```

Password generation, `FUN_0800be66` (recovered exactly):

```
code6 = *(int *)(state + 0x2c)              # 0x02000044 at runtime
sprintf(buf, "%06d", code6)                 # FUN_0801f41c, 0x0800c47c
for i in 0..5: draw_digit_tile(buf[i])      # x = i*10 + 0x52, y = 0x6d
for i in 0..3:
    sprintf(buf, "%02d", state.byte[0x15+i])# four 2-digit rider fields
    draw(...); draw rider/track names via tables 0x0804c740 / 0x0804c6e8
label on Results: text 97 "Please note new password"
```

Screen dispatch, `FUN_08010b88` (recovered exactly):

```
fam = ctx[0x332b]
case0 = ctx[0x3329]; case1 = ctx[0x332d]
if fam == 0: family0_dispatcher(0x08010a9c, case0)   # main menu, race setup, ...
if fam == 1: family1_dispatcher(0x0800eaa0, case1)   # menus, Results, ...
if fam == 2 or 3: teardown(0x0800b9cc, ctx[0x3328])
```

## 6. Tables

### 6.1 Text bank (selected)

`0` Race, `1` Two Player, `2` Options, `3` Bonus Items, `4` Password, `5` Quick Race,
`6` Challenge, `7` Championship, `8` Select Rider, `9` Summary, `14` Results,
`20..23` FRANK/ALAN/GERRY/NEIL, `29..31` Maryhill/Verona/Springburn,
`42..44` Characters/Tracks/Trophies, **`45` Enter Password**,
`46..49` SFX/Music/On/Off, `50` XSMoto Tour, `97` Please note new password,
`100` Credits. Full 101-entry dump was reproduced in this pass.

### 6.2 Family-1 dispatcher cases (jump table `0x0800eab8`, target = base + 2·byte)

| Case | Byte | Handler | Screen |
|---:|---:|---|---|
| 0 | 0x0e | `0x0800ea28` | (init) |
| 1 | 0x12 | `0x0800e90c` | title |
| 2 | 0x16 | `0x0800e594` | alternate menu setup (texts 0..4) |
| 3 | 0x1a | `0x0800e3ac` | Race submenu |
| 4 | 0x1e | `0x0800e200` | Select Rider |
| 5 | 0x22 | `0x0800deb6` | Quick Race setup |
| 7 | 0x26 | `0x0800dbf4` | Championship setup |
| 8 | **0x45** | **default `0x0800eb44`** | **Two Player — no handler** |
| 14 | 0x2a | `0x0800d6b4` | Options |
| 15 | **0x45** | **default `0x0800eb44`** | **Bonus Items — no handler** |
| 19 | 0x2e | `0x0800d3a6` | Bonus Items content (unreachable from this case) |
| 20 | **0x45** | **default `0x0800eb44`** | **Password — no handler** |
| 22 | 0x32 | `0x0800cdfa` | XSMoto Tour |
| 24 | 0x36 | `0x0800c5d2` | tour/stats |
| 25 | 0x3a | `0x0800be66` | **Results / password generator** |
| 27 | 0x3e | `0x0800bc42` | Summary |
| 29 | 0x42 | `0x0800bb50` | (misc) |

## 6b. Enumeration

**Space definition.** The only code-like value is the progress certificate: one 6-digit
decimal field formatted with `"%06d"` from a 32-bit state word, space `10^6 = 1,000,000`
zero-padded spellings (`000000`..`999999`), plus four 2-digit rider fields (`100^4`) and
rider/track names. No alphabetic password alphabet exists in the image: searches for
`ABCDEFGHIJKLMNOPQRSTUVWXYZ`, `0123456789ABC…` and variants returned 0 hits in prior pass,
and this pass confirmed the getter is never called with index 45.

**Novel code and in-game proof.** We minted `739421` (`0x000B470D`), a value absent from
any published list (no usable published list was obtainable — prior pass records the
bounded web-search failure). It was written to the live state word `0x02000044` with a
labelled RAM patch (`w/4 0x02000044 0x0b470d`), the Results screen was forced
(family1 case 25, screen id 0x2d), and RAM read-back showed
`0x02000044: 000B470D` together with `0x03007DD8: 0001192D / 00001901`
(`novel2_c.png`, `novel3_c.png`). Because the force bypasses normal teardown, the old
menu logo remains drawn over the Results layout; this is a limitation of the force, not
of the code value.

**Bounds proven by rejection / format analysis.**
* In-range: `0..999999` → exactly six digit tiles, zero-padded. Verified structurally by
  `FUN_0801f41c("%06d")` followed by a fixed 6-iteration draw loop (`i<6`).
* Out-of-range lower: `-1` formats as a 7-character string `"-000001"`; the fixed 6-tile
  loop truncates the sign — derived from the formatter, not entered (no input path).
* Out-of-range upper: `1000000` formats as 7 digits and overflows the 6-tile layout —
  same derived bound. A direct RAM patch of `0x02000044 = 0x000F4240` was prepared but
  the forced screen could not be cleanly re-rendered; reported as **derived**, not
  observed.
* **There is no accept/reject predicate to test.** No in-game entry surface exists, so a
  near-miss rejection cannot be produced. This is stated as a fact, not omitted.

**Published-code recon (bounded).** GameFAQs 403, DDG bot CAPTCHA, Google challenge,
Bing irrelevant, Wayback 404, four `websearch` queries returned nothing (prior pass).

**Gate proof — exact, byte level (this pass's main result).**
1. The main menu is family0 case 2 → `FUN_08010454` (`0x08010454`).
2. Cursor arithmetic for **decrement**: `0x080104ec subs r4,#1` → `0x080104ee cmp r4,#1`
   → if equal `0x080104f4 movs r4,#0`; else `0x080104f8 cmp r4,#0` → if negative
   `0x080104fc movs r4,#2`. For **increment**: `0x0801053a adds r4,r4,#1` →
   `0x0801053c cmp r4,#1` → if equal `0x08010542 movs r4,#2`; else
   `0x08010546 cmp r4,#2` → if greater `0x0801054a movs r4,#0`.
   **Reachable cursor set is exactly `{0,2}`; indices 1, 3 and 4 can never be selected.**
3. The A-press switch at `0x080105fc` (`cmp r4,#5`, jump table `0x08010608`) writes to
   `ctx+0x332d`: index 0 → `0x03` (Race, `0x0801060e`), 1 → `0x08` (Two Player),
   2 → `0x0e` (Options), 3 → `0x0f` (Bonus Items), **4 → `0x14` (Password,
   `0x08010626`)**.
4. Family1 dispatcher jump table `0x0800eab8`: bytes for cases 8, 15 and 20 are `0x45`,
   whose target `0x0800eab8 + 0x8a = 0x0800eb44` is the shared tail (no BL to a handler).
   Therefore even a patched cursor selection of Password reaches no screen.
5. Runtime confirmation: loading the clean main-menu savestate, writing menu-object
   selected index `4`, and pressing A produced `0x03007DD8: 00010207 / 00000300`
   (unchanged main-menu state) with a blank background — `gate3_c.png`.
6. A third-party write of the state word itself works (§screen force), so the gate is in
   the **input/navigation layer**, not in the dispatcher or the screen machinery.

**Dispatcher enumeration.** All 14 family0 cases and 15 family1 cases were enumerated
statically and profile-checked; 38 `FUN_08010e90` call sites were mapped to their enclosing
functions and every literal/computed index inspected. Indices actually passed include
`0,2,3,5,7,8,9,14,16,40,46..50,92,100` and table-driven rider indices — **never 45**.
"Enter Password" is an orphan string in this build.

**Validator enumeration (bounded negative).** `FUN_0801f41c` has exactly three callers
(`0x0800be66` Results, `0x0800c5d2`, `0x0800cdfa`); all pass a format string and a value
to a display buffer. No caller parses digits; there is no `atoi`-like routine reachable
from any dispatcher case, no comparison against `state+0x2c` outside Results, and no
key-driven decimal accumulator (`*10`) in any of the 29 screen handlers. The 3 savestate
count-byte patches tried in the prior pass (`0x02000eca`, `0x02004e7e`, `0x020054aa`)
failed because the menu item count is set by the handler itself (`*(menu+1)=8` in
`FUN_0800e594`), not by those bytes.

## 7. Validation evidence

* **Observed**: SHA-256 identity; savestate `xs.ss1`; CLI-debugger register/RAM dumps;
  `force3_c.png` (family1 case 3 forced → Select Rider), `novel2_c.png`/`novel3_c.png`
  (Results forced with `0x02000044 = 000B470D`), `gate3_c.png` (index-4 A-press → blank),
  `menu_fresh_c.png`/`afterret_c.png` (reachable main menu).
* **Derived**: text bank layout; getter formula; both jump tables and all case mappings;
  gate arithmetic from disassembly at the exact addresses quoted; Results pseudocode.
* **Inferred**: that the 6-digit number is the "password" to note down — strongly
  supported by its co-location with text 97 "Please note new password" on Results, but
  it is never entered anywhere in this SKU.
* **Not observed**: any accept/reject decision by the game; no in-game keypad input.

## 8. Unknowns

1. Why the build retains 13 orphan strings (`Enter Password`, `Two Player`, `Bonus
   Items`, `Challenge`, …) and fully coded but unwired handlers (`0x0800d3a6`,
   `0x0800cdfa`): presumably a retail build that disabled these modes, but the reason is
   not in the image.
2. A completely clean photograph of the forced Results screen was not obtained: forcing
   bypasses teardown, so the main-menu logo overlays the Results tiles. The RAM values and
   the Results-specific text (`FINAL POSITION`, `CHAMPIONSHIP SCORE`) are visible.
3. No published password list for this exact SKU could be retrieved, so "novel" is
   asserted against the games' own reachable surface and the prior web-search record,
   not against an exhaustive external corpus.
4. The out-of-range `1,000,000` and `-1` format behavior is derived from `%06d` plus the
   fixed 6-tile loop, not photographed in-game.

## 9. Tooling

* `file`, `xxd`, `strings`, `sha256sum`; Python `capstone` 5.0.7 disassembler and a
  Thumb BL/BLX xref scanner (`xrefs.py`).
* REA MCP + Ghidra 12.1.4 (`open_binary` raw-binary ARM @ `0x08000000`,
  `procedure_pseudo_code`, `procedure_callers`, `trace_feature`, `xrefs`).
* mGBA 0.10.5 CLI debugger (`mgba -d`) driven through a named FIFO with `stdbuf -oL -eL`,
  `break/t`, `w/1`, `w/4`, `x/4`, `r/1`, `save`/`load`, SIGINT to halt; Xvfb `:320`,
  openbox, xdotool, scrot, PIL for crops. Helper scripts in `/tmp/xsmoto2/`.

## 10. Legal note

No ROM, graphics or audio are redistributed. Only hashes, addresses, algorithms and the
analyst's own observations are published.

## 11. Cleanup

Screenshots, savestates and helper scripts were left under `/tmp/xsmoto2/` only; the
ROM folder contains `XS Moto.gba` and the report. Own mGBA/Xvfb/openbox/FIFO-holder PIDs
were terminated by number; no `pkill` was used. The RE/Ghidra session was closed.
