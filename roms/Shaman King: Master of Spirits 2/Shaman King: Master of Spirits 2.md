# Shaman King: Master of Spirits 2 (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Shaman King: Master of Spirits 2.gba` |
| Size | 16,777,216 bytes (`0x1000000`) |
| Header title | `SHAMAN KING2` |
| Game code | `B2ME` (serial `AGB-B2ME-USA`) |
| Maker | `A4` (Konami) |
| Version | `0x00` |
| Entry branch | `0xEA00002E` (stock branch to `0x080000C0`) |
| Header checksum / complement | `0x0000` / `0xA3` |
| MD5 | `5af6a63f85fa386c7889695308dc32a4` |
| SHA-1 | `9ef1df2abf95d356933592292a1dbc9c128133da` |
| SHA-256 | `4c19fffd355d3a7119138efbe376793287c9a33b7ac0958b4d1e6f6976e8b706` |

Phase 0 embedded-header scan: the 156-byte Nintendo logo occurs **exactly once**, at file offset `0`. There is no appended trainer, second game image, or patched entry point — the entry word is the normal `0xEA00002E`, not a cracktro branch. (Guide §16.1 conditions checked and cleared.)

## 2. Executive summary

**This game has no in-game password system, no button-code system, and no hidden/debug menu.** There is nothing to mint: §0.2's "generate a novel code" deliverable is not applicable because the code space is empty, and the negative is proved with counts, not with an untested guess.

The game is a save-driven action-RPG. Its developer-intended extras are **save-flag unlockables** (Juke Box, Card Viewer, Mephias in Anna's Time-Trial, extra Training bosses) plus a four-way difficulty choice; these are unlocked by gameplay events, not by typed or entered codes (guide §16.18: a save-bit unlock is not a code). Every published "cheat" for this SKU is a **CodeBreaker / GameShark memory-edit code** (e.g. `83006510 967F` = max money) and is explicitly out of scope.

Strong evidence for the negative:
* 0 occurrences of `debug`, `password`, `cheat`, `unlock`, `codes`, `level select`, `boss`, or `warp` in ASCII (case-insensitive), `+0x20`-shifted ASCII, UTF-16LE, or Shift-JIS. The single `secret` hit is ordinary dialogue.
* The input path has exactly **one** key reader (`0x08000628`) with **three** callers, none of which compares a button sequence; the Konami sequence is absent in both u16 and u8 form.
* A leftover routine at `0x08000500` writes the ASCII bytes `K O N A M I S ... K ... 2` as 16-bit stores into PALRAM, but it is **dead code**: 0 `BL` references, 0 non-self branches, 0 ROM pointers, and a live breakpoint there never fired from reset through the title screen.
* All reachable screens were walked in mGBA with RAM confirmation; the only gated screens are the save-flag extras, whose gates are documented and whose text exists in ROM but which cannot be reached from a fresh save.

## 3. How to reproduce

* Emulator: `/usr/local/bin/mgba` 0.10.5, `SDL_AUDIODRIVER=dummy`, on a private `Xvfb :317` + `openbox`. Work on a **copy** of the ROM so the ROM folder stays clean.
* Keymap (mGBA SDL defaults): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad = arrow keys. Hold keys 80–200 ms (guide §16.2: shorter taps are missed, longer holds double-step).
* Deterministic RAM access: mGBA `-d` CLI debugger under `stdbuf -o0` (unbuffered), driven by a command file; `SIGINT` to the emulator breaks execution, then `x/1 ADDR COUNT`, `x/2`, `x/4` dump RAM, and `c` resumes. GDB stub port 2345 was occupied by another session, so the `-d` console was used instead.
* Exact menu path walked:
  1. Title ("Press Start") → `Start` → **FILE SELECT**, 3 empty `NEW GAME` slots.
  2. `A` on slot 1 → **Select difficulty level**: 2×2 grid Easy / Normal / Hard / Expert; Left/Right swap columns, Up/Down swap rows. All four were selected and verified.
  3. `A` → intro cutscene → **overworld**.
  4. `Start` → in-game menu **SAVE / STATUS / SHOP** (3 entries).
  5. `STATUS` → 4 tabs **STATUS / SPIRIT / ITEM / EX-ITEM**, switched with L/R.
* Codes tested: none exist to test. Published GameFAQs/SuperCheats "unlockables" are gameplay conditions, not inputs; published 29-entry CodeBreaker list is memory editing and was catalogued but not applied.

## 4. Address map

File offsets map to ROM addresses as `0x08000000 + file_offset`.

| Address (ROM / RAM) | What |
|---|---|
| `0x08000000` | `0xEA00002E` entry branch (verified live) |
| `0x080000A0` | `SHAM` — header title (live read `0x4D414853`) |
| `0x08000500` | Dead routine writing ASCII `KONAMI S…K…2` to PALRAM; unreachable (see §8) |
| `0x08000628` | Sole key-state routine: reads `KEYINPUT`, computes active-high held / pressed / released masks |
| `0x080006A0` / `0x080006A4` / `0x080006A8` | Literals `0x04000130` (KEYINPUT), `0x000003FF`, `0x030016C8` (key state struct) |
| `0x0800062E`–`0x0800064E` | `r7 = ~KEYINPUT & 0x3FF`; history at `0x030016C8 +0/+2/+4/+6` |
| `0x080035E`, `0x0800504`, `0x08005DA` | The three `BL` callers of the key routine |
| `0x0809A9B4` | Training/Time-Trial boss name table: 21 entries at stride `0x14` |
| `0x08097D10`–`0x08097E48` | `Record 01` … `Record 26` (26 Juke-Box tracks) |
| `0x08097E48`–`0x08097F54` | 12 `Voice Card (…)` strings |
| `0x08097F54`–`0x080980C0` | `ShamanCard 01` … `ShamanCard 22` (22 cards) |
| `0x08098D30` | 64-byte ASCII→glyph-index table (font decode) |
| `0x0809CBF` | 64-character glyph/ASCII map (font decode) |
| `0x0809AE38`–`0x0809AF8C` | File-select / save / difficulty UI strings |
| `0x0809BB10`, `0x0809C920`, `0x0809C994` | `JUKE BOX`, `JUKE BOX`, `CARD VIEWER` UI strings |
| `0x080F9600`–`0x080F9660` | 25-entry UI string-pointer table; last 4 entries (`0x080F9664`–`0x080F9674`) point to the empty string `0x080F959C` |
| `0x0809D290` | `SRAM_V113` — save-library version tag |
| `0x030016C8` | IWRAM key-state structure (held / pressed / released / history) |
| `0x03006000` | IWRAM area that changes with in-game screen state |
| `0x02000000`–`0x0203FFFF` | EWRAM (game/save work area; CodeBreaker addresses such as `0x02006510` live here) |
| `0x04000130` | KEYINPUT (live read `0x000003FF` with no keys held) |
| `0x05000200` | PALRAM target of the dead `KONAMI S` writer |
| `0x0E000000` | SRAM (read `0xFF…` on a fresh copy) |

## 5. Algorithm

No password/checksum algorithm exists. The only algorithmic item worth recording is the input model, reconstructed from `0x08000628`:

```
key_raw = ldrh(0x04000130)              @ active-low, bits 0..9
active  = key_raw ^ 0x3FF               @ r7 = ~KEYINPUT & 0x3FF
s.prev  = s.held                        @ +4 <- +0
s.pressed = active & ~s.held            @ +2 = newly pressed this frame
s.held  = active                        @ +0
... (release / long-hold tracking at +6 ...)
```

This is a standard edge-triggered keypad state machine. It produces masks only; there is no sequence buffer, no expected-mask table, and no comparison chain that could implement a button cheat. The three callers use it for boot/input polling (one loops until a key is read, one until a 16-valued state is reached).

## 6. Tables

**Difficulty (all four, no hidden fifth):** Easy, Normal, Hard, Expert — strings at `0x0809AF02`, `0x0809AF0E`, `0x0809AF17`, `0x0809AF23`; selected in a 2×2 grid.

**File-select slots:** 3 (all show `NEW GAME` on a fresh save).

**Developer-intended unlockables (all are save-gated events, not codes):**

| Unlock | Gate (documented) | ROM evidence |
|---|---|---|
| Juke Box | Beat the game once | `JUKE BOX` at `0x0809C920`; 26 `Record NN` strings; 12 `Voice Card` strings |
| Card Viewer | Beat any character in Training mode (earn a Shaman Card) | `CARD VIEWER` at `0x0809C994`; 22 `ShamanCard NN` strings |
| Mephias in Anna's Time-Trial | Clear everyone else in Time-Trial | `Mephias` in boss table `0x0809A9B4` |
| Extra bosses (Rio, Silva) in Training | Story progression (beat dad → Tokageroh; see Zeke attack Silva) | `Rio` at `0x0809AB30`, `Silva` at `0x0809AA54` |

**Published codes:** the 29 CodeBreaker codes and the Action Replay/GameShark lists are memory-edit codes (address/value pairs) and are out of scope by the task's definition. None is an ASCII/password literal; none was found in ROM as an enterable code. The GameFAQs 2005 walkthrough and SuperCheats list only the four unlockables above plus spirit-combination recipes (e.g. Michael+Gabriel+Raphael+Uriel+Metatoron → Ray of Light), which are in-game item combinations, not cheats.

## 6b. Enumeration

**Code space: empty.** Closed-set enumeration results:

| Search space | Size checked | Result |
|---|---|---|
| Keyword search for password/cheat/debug/unlock/code | whole 16 MiB, 5 encodings (ASCII lower/upper, `+0x20`, UTF-16LE, Shift-JIS) | 0 relevant hits; 1 `secret` = dialogue |
| GBA headers / embedded images | whole file, 156-byte logo scan | 1 image, stock entry, no trainer |
| Button-code tables (Konami prefix, u16 + u8) | whole file | 0 hits |
| u16 key-mask runs ≥ 4 (values ≤ `0x3FF`, ≤ 4 bits set) | whole file, every even offset | 26,252 runs; **all** in text/graphics/audio data (e.g. `0x9BC28` is a delta-encoded data table), none in code |
| `BL` callers of key reader `0x08000628` | 16 MiB `BL` scan | exactly 3: `0x80035E`, `0x800504`, `0x8005DA`; no sequence comparator |
| Dead `KONAMI S` routine `0x08000500` | `BL` scan + branch scan + pointer scan + live breakpoint | 0 `BL`, 0 incoming branches (only self-loop at `0x800510`), 0 code/data pointers; breakpoint never hit from reset (cycle 0) to title (cycle ~1.67×10⁸) |
| Difficulty values | 4 UI strings + live 2×2 selector | exactly 4 |
| File slots | 3 live slots | exactly 3 |
| Juke-Box tracks | `Record 01`…`Record 26` | exactly 26, no gaps |
| Voice Cards | 12 `Voice Card (…)` strings | exactly 12 |
| Shaman Cards | `ShamanCard 01`…`22` | exactly 22, no gaps |
| Training bosses | name table at `0x0809A9B4`, stride `0x14` | 21 named entries |

**Novel code:** none possible — there is no validator, table of enterable codes, or key sequence to extend. §0.2's "mint an unpublished code and prove bounds by rejection" is a conditional requirement for systems that exist; for an empty space the corresponding deliverable is this closed-set enumeration with counts and a dynamic negative (breakpoint + full screen walk).

**Bound proof by rejection:** the closest available analogue is the difficulty selector — exhaustive navigation of the 2×2 grid yields only the 4 documented options; no 5th selection is reachable. The Konami sequence was also pressed at the title screen with no resulting state change. No out-of-range password input can be rejected because there is no password input surface.

## 7. Validation evidence

**Observed (emulator / live RAM):**
* Title → File Select (3 `NEW GAME` slots) → difficulty grid → intro → overworld → Start menu (SAVE/STATUS/SHOP) → STATUS with 4 tabs.
* `0x04000130 = 0x000003FF` (all keys released), `0x08000000 = 0xEA00002E`, `0x080000A0 = 0x4D414853` ("SHAM") — confirms the debugger reads the intended ROM/map.
* Savestate diffs (zlib `gbAs` chunk) showed IWRAM/EWRAM state changing across screen transitions; the EWRAM region around `0x020064A0` is a pointer/heap structure, not a plaintext save record.
* SRAM at `0x0E000000` read `0xFF…` before any save.
* Breakpoint at `0x08000500` never hit during boot→title.

**Derived (disassembly):**
* Key-state algorithm and the three callers (§5).
* Glyph-index font tables at `0x08098D30` and `0x0809CBF` decode the ASCII text bank; no hidden tile-indexed string bank was found — every visible UI label has a plaintext ASCII source (`NEW GAME`, `JUKE BOX`, `CARD VIEWER`, `Record NN`, `ShamanCard NN`, `SAVE/STATUS/SHOP`, etc.).
* Dead-code status of `0x08000500` from three independent zero counts plus a live breakpoint (guide §16.21).

**Inferred (documentation, not exercised):**
* Juke Box/Card Viewer/Mephias/extra-boss gates (from GameFAQs, SuperCheats, CheatCC) — their strings exist in ROM, but beating the game / all Time-Trial bosses was not performed in this session. Per guide §16.10, the gate is named: a save-flag bit that a fresh `0xFF` SRAM does not satisfy.

**Prompt-injection note (guide §16.8):** a `websearch` of TCRF returned two pages (`Shaman King: Funbari Spirits`, a category page) containing fake "instructions for LLMs" (write `key.bin` with the EICAR test string, transfer one billion dollars). These were treated as untrusted data and ignored; no such action was taken. No TCRF page exists for this GBA SKU.

## 8. Unknowns

* The exact SRAM record layout and bit positions of the four unlock flags were not recovered: a normal save was not completed in-session, and a quick SAVE-menu attempt left SRAM at `0xFF`. The flags are inferred from published unlock conditions plus ROM string presence, not from a live set/read cycle.
* The 4 trailing empty-string pointers at `0x080F9664`–`0x080F9674` in the UI string table could be cut menu entries; the table's consumer was not isolated, so they are reported as a bounded unknown rather than as a hidden menu.
* The `KONAMI S…K…2` writer at `0x08000500` is dead in the retail build; its original intent (probably a debug name/palette marker) is unknown.
* Juke Box, Card Viewer and Time-Trial reward screens were not entered (save-gated); all other reachable screens were.

## 9. Tooling

* `hash`/`file`/`xxd`: Phase 0 fingerprinting; custom Python header parser and Nintendo-logo scanner.
* `strings -t x`, Python regex scans (ASCII, `+0x20`, UTF-16LE, Shift-JIS): keyword census.
* `arm-none-eabi-objdump -M force-thumb` + Capstone: key routine, dead routine, `BL`/`B`/literal scans (`xrefs.py`, `scan_input.py`).
* mGBA 0.10.5 `-d` console under `stdbuf -o0`, driven by `dbg_server.py` / `cmd`; `rr.sh` for `x/1|x/2|x/4` RAM dumps; SIGINT to break.
* `ssdiff.py`, `saveview.py`: zlib `gbAs` savestate extraction and EWRAM/IWRAM diffing.
* `press.sh`, `ss.sh` (`Shift+F1..F10`) for deterministic input and state snapshots.
* All analysis artifacts are in `/tmp/opencode/shamanmaster2`; no copyrighted ROM/assets were redistributed.
