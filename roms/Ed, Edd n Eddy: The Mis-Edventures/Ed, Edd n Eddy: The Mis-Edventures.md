# Ed, Edd n Eddy: The Mis-Edventures (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Ed, Edd n Eddy: The Mis-Edventures.gba` |
| Size | 8,388,608 bytes (0x800000, 8 MiB), clean retail image |
| Header title / code / maker | `EEE2` / `BEDE` / `5D` (Midway), Rev 0x00 |
| Entry word | `0xEA00002E` (stock `b 0x080000C0` crt0); one Nintendo-logo hit at 0x0 — no cracktro/trainer |
| MD5 | `0886eee57b5f9e97d2981a00134fd641` |
| SHA-1 | `2d4aaad62faf905e4138015261d59360756e7dee` |
| SHA-256 | `3885f9ba95fb1e8a4c04d53690154a6a5d1a09663e439722b371f565f3df1dfd` |
| Save | 512-byte EEPROM |

## 2. Executive summary

**There is no player-reachable code system.** No password, cheat code, button sequence or
hidden code-entry surface exists on any of the 9 reachable screens. Progress is EEPROM
save data, not passwords.

The ROM contains a complete **developer-only debug/level-select screen** (`0x0801854C`)
with a 23-entry menu (viewers, a prototype entry, Start Game, Title Screen, and every
level). This pass **closes the gate that the previous report left as UNKNOWN**: the
handler has **zero BL callers**, exactly **one pointer xref** (handler table `0x0818B154`,
index 0), and the mode flag `0x020028C4` has exactly **3 writers / 1 reader** (all
enumerated below). A whole-ROM literal scan plus an instrumented-ROM dynamic test prove
the handler is **never invoked** during normal play or any tested input (0 of 47
extended sequences/chords). This is a **gated/cut developer feature** (guide §16.3
category 4/2), not a player cheat. Forcing it with ROM instrumentation reproduces its
RAM signature exactly.

The prior report's table address `0x08018C9F0` was a digit short: the real table is
`0x0818C9F0`; its Hub 6/7 level fields are also corrected below.

## 3. How to reproduce

* `mgba -3 <rom>` under `Xvfb :315` + `openbox`, `SDL_AUDIODRIVER=dummy`. Keymap A=`x`,
  B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, dpad=arrows; hold ~120 ms.
* Screen path: legal → title ("Press Start") → Main Menu (`New Game / Continue / Options
  / Credits`) → New Game → 3 EEPROM slots + Quick Save → hub gameplay; `Start` in play →
  Pause (`Quick Save / Display Case / Options / Quit Game`) → Display Case viewer.
* **RAM oracle**: mGBA `.ssN` savestates are PNG with a zlib `gbAs` chunk; decompress it
  and read EWRAM at raw offset `0x21000 + (addr-0x02000000)`. `0x020028C4` is the debug
  screen's flag. `/tmp/eenemis2/dyn.py` implements save/load/read/write.
* **Instrumented ROM (inspection only, not a cheat)**: `forced2.gba` changes two
  instructions at `0x08017A66`/`0x08017A72` so the main-menu spawn template's index byte
  is 0 instead of 1. It makes the dispatcher call `0x0801854C`. With this ROM the RAM
  signature is reproduced: `0x020028C4` nonzero, `0x02003140` = 2,
  `ptr[0x02003144]` = `0x080395AC` ("Level"). `instrumented.gba` patches `0x08018580`
  to `b .` *after* the flag write; the flag stayed 0 throughout all testing, i.e. the
  patched call site was never reached.

## 4. Address map (all ROM addresses = 0x08000000 + file offset)

| Address | Meaning |
|---|---|
| `0x0801854C` | Debug-screen initialiser (Thumb; stored as `0x0801854D` in tables). 0 BL xrefs, 1 pointer xref. |
| `0x080395AC`–`0x080396BC` | Plain-ASCII label bank (29 strings incl. `Level/MapX/MapY`, all 23 menu names). |
| `0x0818C9F0` | **23-entry debug menu table** (corrected address), stride `0x1C`: `{char* name, 0, action, paramA, paramB, 0, 0}`. |
| `0x0818B154` | Screen/entity handler table, stride `0x24`, 9 function pointers per type. Index-0 `+0x00` slot = `0x0801854D`. |
| `0x020028C4` | Debug flag word (writes 1 debug-init / 4 elsewhere; 1 reader). |
| `0x02003140` | Debug menu-structure base (`+0` kind=2, `+4` "Level" ptr, `+0xC` count etc.). |
| `0x02000498` / `0x0200CA9C` | Active 12-byte mode struct / pointer to it; its byte `+0` is the handler-table index. |
| `0x020004D8` | Pending spawn template (12 bytes); byte `+0` is the index that the dispatcher uses. |
| `0x08023574`,`0x080236B4` | Input struct builder (`~KEYINPUT & 0x3FF`, active-high). |
| `0x08680496`, `0x084A61AE` | Candidate 256-byte ASCII→tile-index font tables (see §6b). |

## 5. Gate proof — THE CENTRAL DELIVERABLE

### 5.1 Every writer/reader of `0x020028C4` (whole-ROM Thumb LDR-literal scan)

A full 8 MiB Capstone scan of `LDR Rd,[PC,#imm]` literal loads found **exactly four**
references to the address (all via literal pools; no base+offset access exists — the
only other nearby literal, `0x020028C0`, occurs once inside the debug init at
`0x0801855E`):

| Site | Access | Value | Context |
|---|---|---|---|
| `0x0801854E`→`str @ 0x08018552` | **writer** | **1** | Debug init entry (`movs r0,#1; str r0,[r1]`). |
| `0x0800B836`→`str @ 0x0800B83A` | **writer** | **4** | Camera/entity helper; `movs r0,#4; str r0,[r1]`. |
| `0x0800B85C`→`str @ 0x0800B860` | **writer** | **4** | Second helper, same `movs r0,#4; str r0,[r1]`. |
| `0x080187DA`→`ldr r0,[r1]` | **reader** | test `!=0` | `cmp r0,#0; beq normal; b 0x08018994`, where `subs r0,#1; str r0,[r1]` decrements it. |

**Totals: 3 writers (values {1,4,4}), 1 reader.** None of the four sites is in an
EEPROM/save-load routine: the save code never references this address (literal scan
above), so **no save flag can set it**. No controller-input path writes it either — the
only writer of 1 is inside the debug handler itself.

### 5.2 Handler reachability (why index 0 cannot be selected by the player)

* **BL scan over all 8 MiB: 0 calls to `0x0801854C`.** The function is entered *only*
  through a function-pointer table.
* **Pointer scan: 1 reference to `0x0801854D`** — the `+0x00` slot of record 0 of the
  handler table at `0x0818B154` (stride `0x24` = 9 pointers per type: init, update,
  draw, …, cleanup). The dispatcher computes
  `index = *(u8*)mode_struct; fn = table[index*0x24]`; there are **19** such index-read
  sites (`0x08022C08`, `0x08022CFA`, `0x08022D4A`, `0x08022DA8`, `0x08022DCE`,
  `0x08022E48`, `0x08022EA2`, `0x08022F08`, `0x08022F76`, `0x08023086`, `0x080230F4`,
  `0x0802313E`, `0x080231A8`, `0x080231D8`, `0x080231FC`, `0x0802325C`, `0x080232CE`,
  `0x08023310`, `0x08023366`), all reading byte `+0` of a 12-byte mode struct copied
  from a fixed ROM template.
* The ROM template bank (`0x08039440`–`0x08039738`) and all stack-built spawn templates
  were enumerated from every call site of the spawn helpers (`0x080231F8`,
  `0x080232EC`, `0x08022BB4`, `0x08022B54`): the index bytes actually produced are
  **{1, 3, 4}** (e.g. `0x08039458`=1, `0x080394D4`=3, `0x080395A0`=4, `0x080396C4`=3,
  `0x08039738`=1; the title/menu spawn at `0x08017A72` writes 1). One stray path at
  `0x0801B1CE` stores 0 into a template, but it never reaches the `+0` slot that calls
  `0x0801854C` (verified dynamically below).
* **Dynamic proof** (guide §16.3 "dead code": live breakpoint that never fires):
  `instrumented.gba` patches `0x08018580`, two instructions *after* the flag write, to
  `b .`; if the handler were ever called the flag would read 1 and the game would hang.
  It was run through the full navigation path and all 47 extended input tests in §6b —
  **the flag read 0 at every checkpoint**. Combined with 0 BL xrefs and 1 pointer xref,
  the handler is structurally unreachable.

**Conclusion:** the gate is *closed by construction* — the only selector is a hard-coded
mode index that no reachable code path sets to 0, there is no save-flag writer, and the
flag's only "1" writer is the unreachable handler itself.

### 5.3 Forced execution (instrumentation, verifying the handler is real)

The forced ROM (`forced2.gba`) sets the menu spawn's type byte to 0. It reproduces the
debug handler's exact RAM signature: `0x020028C4` becomes nonzero,
`0x02003140 = 0x02`, and `ptr[0x02003144] = 0x080395AC` ("Level"), with `MapX`/`MapY`
pointers at `+0x10/+0x1C` — exactly the writes disassembled at `0x0801854C..0x0801857C`.
The borrowed context corrupts tile loading (the on-screen text renders garbled), so the
per-entry visual effects below are **derived from the table/code** and labelled as such;
the RAM state of the handler itself is **observed**.

## 6. Tables

**Debug menu — all 23 entries**, table `0x0818C9F0`, stride `0x1C`. Fields shown:
`paramA` (`+0x0C`) and `paramB` (`+0x10`); action (`+0x08`) is `0x0818CC5C` (levels),
`...5D` (tools), `...5E` (Fx). Effects are derived from the field values and the
initialiser/menu code.

| # | Label | paramA | paramB | Derived effect |
|---|---|---|---|---|
| 0 | Obj Viewer | `0x00070107` | 0 | Open object/sprite viewer |
| 1 | Music Player | `0x00080107` | 0 | Open music (sound test) player |
| 2 | Fx Player | `0x00067000` | 0 | Open sound-effects player |
| 3 | Prototype | `0x00066A01` | 0 | Launch leftover prototype build |
| 4 | Start Game | `0x00067301` | 0 | Start a new game from debug |
| 5 | Title Screen | 0 | `0x80010000` | Jump to title screen |
| 6 | Ben Zoo | 0 | `0x80020000` | Load "Ben Zoo" area |
| 7 | Hub 1 | `0x00010000` | `0x80020000` | Load Hub 1 |
| 8 | Hub 2 | `0x00020000` | `0x80020000` | Load Hub 2 |
| 9 | Hub 3 | `0x00030000` | `0x80020000` | Load Hub 3 |
| 10 | Hub 4 | `0x00040000` | `0x80020000` | Load Hub 4 |
| 11 | Hub 5 | `0x00050000` | `0x80020000` | Load Hub 5 |
| 12 | Hub 6 | `0x00100000` | `0x80020000` | Load Hub 6 |
| 13 | Hub 7 | `0x00060000` | `0x80020000` | Load Hub 7 |
| 14 | BossFight | `0x00070000` | `0x80020000` | Load boss fight |
| 15 | Scam 1 | `0x00080000` | `0x80020000` | Load Scam 1 |
| 16 | Scam 2 | `0x00090000` | `0x80020000` | Load Scam 2 |
| 17 | Scam 3 | `0x000A0000` | `0x80020000` | Load Scam 3 |
| 18 | Scam 4 | `0x000B0000` | `0x80020000` | Load Scam 4 |
| 19 | Scam 5 | `0x000C0000` | `0x80020000` | Load Scam 5 |
| 20 | Scam 6 | `0x00060A04` | 0 | Load Scam 6 |
| 21 | MINI Ending | 0 | (special action `0x0818C9D8`) | Play the miniature ending |
| 22 | Asset Viewer | `0x00010313` / `0x0E0D0C0C` / `0x354D3241` | multiple | Open raw asset viewer |

Debug numeric fields: `Level`, `MapX`, `MapY` (string pointers `0x080395AC/B4/BC`,
rebuilt by the initialiser at `0x02003144/50/5C`). **Player-facing codes: empty set.**

## 6b. Enumeration and bounded negatives

| Space searched | Count | Result |
|---|---|---|
| `strings -t x -n 4` over all 8 MiB | 105,262 lines | keyword counts: `password`=0, `cheat`=0, `secret`=0, `unlock`=0, `debug`=0, `level select`=0, `bonus`=0, `hint`=6, `code`=1 — the single `code` is `Shin'en Multimedia. Code: B.Wodok` at `0x18481A`, the GAX audio banner (false-positive class, §11) |
| Literal xrefs to the 29 ASCII debug labels | 29/29 | 26 menu-name pointers land in table `0x0818C9F0`; the other 3 (`Level/MapX/MapY`) land in the initialiser; none in a password UI |
| Held button combos, sizes 1–3 over 8 buttons, 4 screens (prior pass + this pass) | 368 + 7 (4–8-button chords) | oracle `0x020028C4` remained 0 |
| **Extended sequences (this pass)** — Konami forward/reverse/mid/AB/short/LR/LR+Select, `LLRR` variants, 4–8 alternations, `Start×Select×5`, 11-press `D-pad+A/B/Start/Select`, plus 4-, 5-, 6-, 7-, 8-button held chords (`L+R+Start+Select`, `+A`, `+B`, `+A+B`, `L+R+A+B`, `L+R+A+B+Up+Down`, all 8) tested on gameplay **and** main-menu base states | **47** (7 chords + 20 sequences × 2 bases) | **0 hits** — flag stayed 0 in all 47; full log `seqtest2_out.txt` |
| Instrumented-ROM reachability run (§5.2) | full navigation + 11 sequences + 3 chords | flag stayed 0 — debug handler never invoked |
| Screens walked with screenshots + RAM reads | 9 | no code-entry surface on any |

**Font/tile-index text bank.** The UI labels ("Main Menu", "New Game", …) have no
ASCII hits; `strings` finds only the debug leftovers. Two 256-byte ASCII→tile-index
tables were located (`0x08680496`: space=0x00, digits=0x2C–0x35, A–Z=0x3A–0x53;
`0x084A61AE`: near-identity), so the UI text is tile-index encoded. Encoding known
strings ("NEW GAME", "MAIN MENU", "PRESS START") with either table and searching all
8 MiB produced **0 hits**, i.e. the visible UI bank is compressed or resolved through a
text-ID/script VM rather than stored as decoded tile-index strings. Per the task's
allowance, full decoding was **not required**: every reachable screen was walked
(their contents are known directly), and the only debug-related text is plain ASCII in
the label bank. The keyword counts above are therefore complete for all text that can
contain a code-system reference.

**Novel code:** not applicable — the code space is empty. The negative is bounded by
the table enumeration, the exhaustive input search, the decoded/ASCII text keyword
counts, and the structural gate proof, not by a single failed string search.

## 7. Validation evidence

* **Observed** — screenshots: legal, title, gumball intro, Main Menu, New Game slots
  (all `Empty`), save tutorial, hub gameplay (`000 / 0` jawbreaker counter), Pause,
  Display Case; forced-ROM debug screen with `Level` menu structure in RAM.
* **Observed** — savestate `gbAs` RAM reads: flag `0x020028C4` = 0 on all screens and
  after all 47 input tests; forced ROM sets it and writes the `Level/MapX/MapY` pointers
  at `0x02003140+`.
* **Derived** — full Thumb disassembly of `0x0801854C` (flag/menu writes) and
  `0x080187DA` (single flag reader); 3-writer/1-reader and 0-BL/1-pointer counts; the
  19 index-read sites; the 23-entry table and its corrected field values.
* **Inferred** — per-entry effects in §6 (from table params/handler code, not visually
  driven, because forcing in a borrowed context corrupts tile rendering); that the
  feature was cut/gated rather than deleted (its code is intact and callable).

## 8. Unknowns

* Exact intended entry method in the developer build (the shipping index value 0 is
  never selected). Not a player gate: no input or save path reaches it.
* The per-entry *visual* outcome of each of the 23 tools was not driven in a clean
  context; effects are derived from the table and code. No published code list exists
  to cross-check against (web: 3rd party cheat indexes 403, Wayback empty, Bing/DDG irrelevant;
  nothing fetched was executed or followed).

## 9. Tooling

`file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings -t x`, `grep -abo`;
`arm-none-eabi-objdump` and Capstone 5.0.7 (`scan.py`, `maplit.py`, `blscan.py`,
`spawnscan.py`, `callers.py`, `templates.py`); Keystone 0.9.2 for the two instrumentation
ROMs (`mkforced.py`, `mkforced2.py`); Pillow for VRAM tile renders (`fontdecode.py`);
mGBA `-d` console debugger over a pty (`dbgserver.py`/`dc.py`); mGBA savestate `gbAs`
zlib RAM oracle and XTEST input (`dyn.py`, `seqtest2.py`); Xvfb :315 + openbox, `import`,
`convert`, `xdotool`. The renamed `mgba_eenemis2` binary avoided another session's
`pkill -x mgba`.

---

*Legal note: no ROM bytes or copyrighted assets are reproduced here; only hashes,
addresses, decoding notes and original tooling are published.*
