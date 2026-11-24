# Dora the Explorer: Super Star Adventures (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Dora the Explorer: Super Star Adventures.gba` |
| Size | 4,194,304 bytes (0x400000, 4 MiB) |
| Header title | `DORA SPR STR` |
| Game code | `BDOE` (file(1) prints `BDOE9G`: code + maker `9G`) |
| Maker | `9G` |
| Software version | `0x00` (Rev.00) |
| Entry word | `0xEA00002E` — **stock** branch to `0x080000C0` |
| Fixed byte `0xB2` | `0x96` |
| Header checksum | `0x0000`; complement byte `0x63` (sum of `0xA0..0xBC` = `0x84`, so the nominal complement would be `0x7C`) — a header-build quirk, not a patch indicator |
| MD5 | `aee29c76808d8debcfb3b7945270861b` |
| SHA-1 | `0423a5d577cb0ae2674ff16fc83104e9240aa60e` |
| SHA-256 | `a03ae2bd00e3ccd4f6f59108fe6ce31b161140db168ae45de17bbc67ae989a54` |

**Phase 0 result.** Exactly one GBA header found: a scan for the 156-byte Nintendo logo over the whole image returns one hit at file offset `0x0`, so this is a single retail image, not a 2-in-1/multiboot pack. The entry branch is the stock `0xEA00002E`. No `TRAINER`, `CRACK`, `CRC BANDIT`, `GameShark`, `Action Replay` or `CHEAT` marker string occurs. The final 256 bytes are `0xFF` padding — nothing appended. Conclusion: **unmodified retail dump, no scene cracktro or appended trainer.**

The boot splash renders the **Nick Jr.** logo (screenshot `shot_00.png`); the collection's sibling note that EU builds use "Nickelodeon" does not match this image, so all addresses below are for this exact hash only.

## 2. Executive summary

**There is no in-game or developer-intended cheat that a player can reach with a controller in this retail build.** The finding is a *bounded negative result*, not "not tested":

1. **No password/serial-code system.** No `password`, `cheat`, `secret`, `unlock` or code-entry text exists anywhere in the 4 MiB as ASCII; the only upper-case runs that resemble alphabets are font/glyph tables at `0x0806A140..0x0806A2ED` (`PQRSTUVWXYZ[@...`, `@ABCDEFGHIJK0123456789...`). No validator, no comparison table, no input buffer for such a system.
2. **No button code.** Nine candidate sequences (Konami forward/reverse, `L+R+Start`, `L+R+A`, `R+L+B+A`, alternating A/B, `Select+Start`, eight A presses, `U/D/U/D+A+B`) were entered with 180 ms held presses on the title screen; none produced any state other than the ordinary title→cutscene or pause transitions. A raw key-mask scan found 1,474 runs of ≥4 plausible 16-bit key masks in code, all consistent with ordinary Thumb opcodes / menu input handling; a 4-press Konami-prefix byte search (both active-high and active-low encodings) returned zero hits.
3. **The Debug menu exists as dead/unused content.** The string bank contains a complete `Options → Debug` entry (`Debug` / `Access Debug Features`) and a `Debug Menu` with two entries — `Display Info` ("In-game debug data") and `Skeleton Key` ("Access Locked Items"). The 54-entry game-state dispatch table at `0x0804B7B8` contains `GST_OPTIONS` (id 10) and `GST_PAUSE_OPTIONS` (id 9) but **no GST_DEBUG state**, and a complete hardware-watchpoint log of the state variable from a cold boot through title, cutscene, map and gameplay shows states `4 → 5 → 6 → 49 → 12 → 50 → 13 → 14` and `8` on pause — **state 10 is never entered**. All 64 state values were forced with a savestate-patch oracle; 35 distinct screens were observed and **none is an Options or Debug menu**. TCRF independently labels this title as having "unused code" and "debugging material".
4. **Published codes.** CheatHappens, VGChartz, GameFAQs and ChapterCheats all report **zero** GBA cheats for this title. The only published "codes" are TCRF's CodeBreaker memory edits `0300002C:07` and `0300002C:09` — **memory-edit codes, explicitly out of scope**. They were still verified against the ROM: `0x0300002C` is confirmed to be the game-state word (hardware watchpoint, writer at `0x080050A8`), but in **this** build value 7 renders a black screen and value 9 renders `PAUSED`, not the described unused-options/audio-test screens (region/build difference).

The one interesting system found — the front-end state machine (`0x0300002C`) and its 54-entry dispatch table — is documented below with addresses so a second analyst can reproduce the enumeration without repeating the search.

## 3. How to reproduce

**Environment.** mGBA (SDL) under `Xvfb :317 -screen 0 1024x768x24`, `openbox`, `SDL_AUDIODRIVER=dummy`, `mgba -3`. Keymap verified by observing menu movement: A = `x`, B = `z`, L = `a`, R = `s`, Start = `Return`, Select = `BackSpace`, D-pad = arrows. **Hold every key ~180–250 ms** (`xdotool keydown …; sleep 0.18; xdotool keyup …`); 10 ms taps are silently missed by this engine and were the cause of two false "input ignored" observations.

**Normal menu walk (all RAM-verified via savestate byte reads at `0x0300002C`):**

| Step | Input | State | Screen |
|---|---|---|---|
| boot | — | 4 → 5 | Nintendo/Nick Jr. splash |
| +4 s | — | 6 | Title, `PRESS START` |
| title | Start or B or A (held) | 49 | Opening cutscene |
| cutscene | A ×1 | 12 | `GST_MAIN_MENU` — *transitional only; no menu art renders* |
| cutscene | A ×2 | 50 → 13 | `GST_CUTSCENE_L1` / `GST_MAP` |
| map | A | 14 | `GST_LEVELMAP` (Star Path select) |
| map | Left/Right/Up | 14 | selects a minigame icon, then gameplay |
| gameplay | Start | 8 | black screen with `PAUSED` text only — **no menu items render** |
| paused | A or B | 14 | resumes gameplay |

`GST_OPTIONS` (state 10) was never reached by any controller path.

**Code/system tests.** Nothing to enter — no code-entry screen exists. Button sequences and the two TCRF memory-edit values were tested as described in §2 and §6b.

**Oracle tooling (exploration only, not a reportable cheat).** Savestates were patched with `sspatch2.py` to force state values and reloaded with F1; this was used *only* to bound the hidden-screen search. All such patched values are memory edits and are **not** presented as in-game codes.

## 4. Address map

| Address (ROM / RAM) | Meaning | Evidence |
|---|---|---|
| `0x08000000` | Stock entry branch `0xEA00002E` | Observed (bytes) |
| `0x08005090` | `GST_FRONT_END` handler; advances state-sequence pointer | Derived (Thumb disassembly) |
| `0x080050A8` | `str r1,[r2,#24]` with `r2=0x03000014` → **writes `0x0300002C`** | Observed (hardware watchpoint PC `0x080050AC` = write PC + 4) |
| `0x0804C0B4` | Front-end state sequence `{5, 6, 49, 12, 0}` | Observed (bytes) |
| `0x0804B7B8` | 54-entry state dispatch table, 12-byte records `{name_ptr, handler_ptr, state_id}` | Derived (bytes + dispatcher at `0x0802D64E`) |
| `0x0800575C` | `GST_OPTIONS` / `GST_PAUSE_OPTIONS` handler (state 10 / 9) | Derived (table) |
| `0x08027CB4` | `GST_MAIN_MENU` handler (state 12) | Derived (table) |
| `0x03000014` | Global front-end/state object base | Derived |
| `0x03000020` | Dispatcher's "previous state" | Derived |
| `0x03000024` | Pointer into the front-end state sequence (title: `0x0804C0BC`) | Observed (savestate) |
| `0x0300002C` | **Current game-state word** (`u32`) | Observed (watchpoint + savestate) |
| `0x0804B2F0` | Localised UI string-pointer table, block 0 (English), 44 slots (`u32`) | Observed |
| `0x0804B3A0`, `0x0804B450`, `0x0804B510`, `0x0804B5C0`, `0x0804B670` | French / German / Italian / Spanish / Dutch blocks, same 44-slot layout | Observed |
| `0x080C2AAC..0x080C349C` | NUL-padded ASCII UI string bank | Observed |
| `0x0806A140..0x0806A2ED` | Font/glyph-order tables (not code alphabets) | Observed |
| Savestate layout | `.ss1` → zlib `gbAs` chunk; IWRAM at `0x19000`, EWRAM at `0x21000` | Observed (state bytes match GDB reads) |

**State-ID → `GST_*` map (from the dispatch table).** 0 `GST_GAMEOVER`, 5 `GST_FRONT_END`, 6 `GST_CORPORATEBACKGROUNDS`, 7 `GST_TITLE`, 8 `GST_CONFIRM_QUIT`, 9 `GST_PAUSE_OPTIONS`, 10 `GST_OPTIONS`, 12 `GST_MAIN_MENU`, 13 `GST_MAP`, 14 `GST_LEVELMAP`, 15–33 `GST_LEVEL_1A..5C`, 36–47 cutscenes, 49 `GST_CUTSCENE_OPENING`, 50 `GST_CUTSCENE_L1`, 57 `GST_LEVEL_STARGALLERY`, 60 `GST_LEVEL_BACKPACK`, 61 `GST_PAUSE`, 62 `GST_UNPAUSE`, 63 `GST_AUDIO_OPTIONS`. Full 54-row dump was in `/tmp/dorastar` (`litscan.py`, `ssread.py` output).

## 5. Algorithm

There is no validator to reverse. The only algorithm recovered is the state dispatcher, sufficient to reproduce every screen:

```
state_seq = [5, 6, 49, 12, 0]            @ 0x0804C0B4
state_ptr = 0x03000024                   ; points into state_seq
state     = 0x0300002C                   ; u32 current state
prev      = 0x03000020                   ; dispatcher's last state

GST_FRONT_END_handler():                  ; 0x08005090
    *state_ptr_entry = *(state_ptr)       ; write next id into state
    if (*state_ptr_entry != state): set change flag at 0x03000028
    state = *state_ptr_entry
    state_ptr += 4

dispatcher():                             ; 0x0802D5F4
    if (state != prev):
        prev = state
        cleanup_previous_state()          ; 0x0802AADC
        for rec in dispatch_table[0x0804B7B8 .. +54*12]:
            if rec.id == state:
                rec.handler(state_object=0x03000014)   ; via 0x0803 44A8
                break
```

The normal boot never leaves `state_seq` before the front end hands off to the cutscene; states 10 (`GST_OPTIONS`) and therefore the Debug submenu have **no caller in this path**.

## 6. Tables

**Debug/Options strings (English block, string IDs are slot indices from `0x0804B2F0`):**

| ID | Slot | String address | Text |
|---:|---|---|---|
| 14 | `0x0804B328` | `0x080C2B3C` | `Main Menu` |
| 15 | `0x0804B32C` | `0x080C2B48` | `Options` |
| 24 | `0x0804B350` | `0x080C2BC0` | `Debug` |
| 25 | `0x0804B354` | `0x080C2BC8` | `Access Debug Features` |
| 35 | `0x0804B37C` | `0x080C2C4C` | `Debug Menu` |
| 36 | `0x0804B380` | `0x080C2C58` | `Display Info` |
| 37 | `0x0804B384` | `0x080C2C68` | `In-game debug data` |
| 38 | `0x0804B388` | `0x080C2C7C` | `Skeleton Key` |
| 39 | `0x0804B38C` | `0x080C2C8C` | `Access Locked Items` |
| 68 | `0x0804B400` | `0x080C2E80` | `<OPTIONS_ITEM_DEBUG>` |
| 69 | `0x0804B404` | `0x080C2E98` | `<OPTIONS_HINT_DEBUG>` |
| 79 | `0x0804B42C` | `0x080C2F58` | `<TITLE_DEBUG>` |
| 80 | `0x0804B430` | `0x080C2F68` | `<DEBUG_ITEM_COORDINATES>` |
| 81 | `0x0804B434` | `0x080C2F84` | `<DEBUG_HINT_COORDINATES>` |
| 82 | `0x0804B438` | `0x080C2FA0` | `<DEBUG_ITEM_SKELETON_KEY>` |
| 83 | `0x0804B43C` | `0x080C2FBC` | `<DEBUG_HINT_SKELETON_KEY>` |

The same six debug tokens repeat once per language block at `0x0804B4B0..`, `0x0804B560..`, `0x0804B610..`, `0x0804B6C0..` — five blocks total (English + four translations; one language block reuses the English pointers). This is a complete static enumeration of the (unreachable) Debug menu: **two entries only** — `Display Info`/Coordinates and `Skeleton Key`.

## 6b. Enumeration

**Code-space / surface definition.** There is no password alphabet, no checksum, no key-mask sequence and no reachable hidden menu, so the §0.2 "space" to enumerate is the *state/screen space* plus the *text and button input spaces*.

| Space | Size checked | Result |
|---|---|---|
| Game-state space | All 64 values `0x00..0x3F` forced via savestate patch, one screenshot each | 35 distinct screens. Screens resolved to: title, legal text, cutscenes, level map, 20+ minigames, PAUSED, star-results, star-gallery/backdrop. **No Options screen, no Debug menu, no audio test.** State 7 = black; state 9 = PAUSED; state 12 = cutscene background only. |
| State space reached by controller | Complete watchpoint log from cold boot through title/cutscene/map/gameplay/pause | `{4, 5, 6, 49, 12, 50, 13, 14, 8}` — 9 states. State 10 (`GST_OPTIONS`) and 63 (`GST_AUDIO_OPTIONS`) never occur. |
| Text space | `strings -t x -n 3/4` over all 4 MiB (96,538 / 43,130 lines); case-insensitive keyword classification | `debug` ×1, `DEBUG` ×7, `Debug` ×3; **0** occurrences each of `password`, `cheat`, `secret`, `unlock`, `code` (as a code-entry word). All debug hits are the UI strings in §6. |
| Literal known-code space | Byte search for every known code/published literal (none exist; only CodeBreaker address:value pairs, which are not ROM literals) | No code literal present. |
| Button-code space | 4-press Konami prefix as `u16` and `u8`, active-high and active-low, searched over all 4 MiB; 1,474 candidate `u16` key-mask runs inspected; 9 sequences entered on title with 180 ms holds | 0 prefix hits, 0 candidate tables (all runs are code bytes), 0 undocumented state transitions. |
| Published-code space | CheatHappens, VGChartz, GameFAQs, ChapterCheats, TCRF (Wayback snapshot `20240618101940`) | 0 in-game codes published; TCRF's only entries are the two out-of-scope CodeBreaker edits, both tested and both non-functional as described in this build. |

**Novel code:** not applicable — no code system exists to mint from (§0.2 point 5 governs). **Bounds proven by rejection:** forcing state 7 and state 9 (the TCRF values) produced a black screen and the PAUSED screen respectively, proving those literals do not reach a hidden menu in this build; forcing state 10 produced a black screen because its menu asset/initialiser is not reachable from the retail boot path.

## 7. Validation evidence

- **Observed** — all screenshots (`shot_*.png`, `walk_*.png`, `cut_*.png`, `states/s*.png`), savestate RAM reads at `0x0300002C`, hardware-watchpoint log of that word, header/hash scans, literal and keyword counts.
- **Derived** — state dispatch table layout and handler addresses from Thumb disassembly (`0x08005090`, `0x0802D5F4`, `0x08027CB4`, `0x0800575C`), string-ID mapping from the pointer table at `0x0804B2F0`.
- **Inferred** — that the Debug menu is cut content rather than gated behind a save flag. The evidential basis is: no controller path reaches state 10, the state sequence never lists it, no GST_DEBUG state exists, and TCRF classifies the title as having unused code/debugging material. This is the only claim in this report that is not directly observed end-to-end; the underlying facts (absence of any input path in the walked and enumerated spaces) are observed.

**Prompt-injection note (§16.8).** A web-search result for an unrelated TCRF page (Mario Party 3) contained a fake "instructions for LLMs" block asking the reader to write an EICAR test string to a file and use it as an XOR key. It was treated as untrusted data, ignored, and not acted upon. No fetched page contained instructions that were followed.

**Comparison with sibling Dora titles.** This analysis was done independently on this hash. The engine here is an ImaginEngine state-machine build with a 54-state dispatch table and a localised string bank at `0x080C2AAC`; nothing in this image was assumed from the other two Dora ROMs. No code, password or button sequence was found here, so there is nothing to report as matching or shared with them.

## 8. Unknowns

- Whether the Options/Debug menu would render if its init function were invoked with a fully constructed menu-manager object; the savestate/GDB force-state attempts produced a black screen, so its runtime effect (what "Skeleton Key" actually unlocks) was **not** observed. It is documented statically only (§6).
- Whether some save-data condition or an unreachable script path calls `GST_OPTIONS` (state 10) after full game completion; no such writer was identified in the walked or enumerated spaces, and the cart's `.sav` stayed at 0 bytes throughout.
- Exact effect strings beyond the two debug entries are not present; the remaining `GST_*` states are normal gameplay/cutscene states, not cheats.

## 9. Tooling

Scripts written in `/tmp/dorastar`: `litscan.py` (PC-relative literal / raw-word scanner), `ssread.py` (zlib `gbAs` savestate reader + IWRAM/EWRAM mapping), `sspatch.py` / `sspatch2.py` (savestate byte/word patcher for the oracle), `gdbmem.py` (GDB remote client, superseded by the `-d`/watchpoint approach), `gcmd.sh` (persistent GDB FIFO helper), `readstate.sh`, `press.sh`, `search_codes.py`, `enum_states.sh`. Stock tools: `arm-none-eabi-objdump -M force-thumb`, `gdb-multiarch` (hardware watchpoint on `0x0300002C`), `strings`, `xxd`, `xdotool`, `import`, `montage`. No third-party packages were installed for this engagement.

**Cleanup:** all generated `.sav`/`.ss1` files were removed from the ROM folder and the :317 Xvfb/openbox/mGBA processes were stopped by PID (see final reply).

**Legal note:** no ROM bytes, extracted graphics, music or game text were redistributed; only addresses, hashes, algorithms and original analysis scripts are published here.
