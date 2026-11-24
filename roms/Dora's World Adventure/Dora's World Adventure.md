# Dora's World Adventure (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Dora's World Adventure.gba` |
| Size | 4,194,304 bytes (0x400000, 4 MiB) |
| Header title | `DORA WORLD A` |
| Game code | `BXPE` |
| Maker | `54` |
| Software version | `0x00` (Rev.00) |
| Entry word | `0xEA00002E` — stock branch to `0x080000C0` |
| Fixed byte `0xB2` | `0x96` |
| Header checksum / complement | `0x0000` / `0x8A` (common retail-build quirk, not a patch indicator) |
| MD5 | `81df4456e398f87e893c522810cc8cda` |
| SHA-1 | `bb071a3aaa24fa904ea01de13931a3e2a0a8b5a5` |
| SHA-256 | `c4d8cd30ec12e313dc057f2f74004901518c4c05381603ecfda9f5fba7b9e452` |

**Phase 0 scan.** A whole-image search for the 156-byte Nintendo logo finds **exactly one** header, at file offset `0x0` (ROM `0x08000000`); no 2-in-1/multiboot sub-image, no appended trainer. No `TRAINER`, `CRACK`, `CRC BANDIT`, `GameShark`, `Action Replay` or `CHEAT` marker occurs in the image. Boot shows Nintendo → health-and-safety → © 2006 Global Star Software / Take-Two → Global Star "GS" splash → Nick Jr. → title. Conclusion: **unmodified retail dump, no scene cracktro or trainer.** All addresses below are for this exact hash only.

**Engine distinction (important).** This title is `BXPE`, maker `54`, Global Star Software. It is **not** the ImaginEngine build used by *Dora the Explorer: Super Star Adventures* (`BDOE`, maker `9G`, localised ASCII string bank at `0x080C2AAC`, 54-state dispatch table at `0x0804B7B8`). Here `strings` finds **no** readable text at all — the UI is drawn from a custom bitmap font addressed by tile index (the health warning, title and menus are all rendered from font tiles). Consequently none of the sibling's addresses, string IDs or dead Debug-menu findings carry over; this analysis was done independently.

## 2. Executive summary

**Bounded negative: there is no in-game / developer-intended cheat that a player can reach with a controller in this retail build.** The result is a proven statement about the searched spaces, not "not tested":

1. **No password / serial-code system.** No password text, alphabet table, validator or code-entry screen exists. `strings -t x -n 4` returns 64,731 lines, but case-insensitive keyword classification finds **0** occurrences of `password`, `cheat`, `secret`, `unlock`, `debug`, `level select` and `menu`; the single `code` hit (`0x080B3C20`, inside `[[jcode...`) is graphics/data noise. Ghidra's complete defined-string inventory (448 strings) is likewise entirely 4bpp graphics coincidences (`DDDD`, `ffff`, `UUUU`, …), not text. There are 5,822 uppercase/digit runs, all graphics data. No `0123456789ABCDEF`-style code alphabet appears except a library hex-printing constant at `0x08019884`.
2. **No button code.** Byte searches for the Konami sequence (forward and reverse), `A,B,A,B` and `U,D,A,B` as `u16` *and* `u8`, in both active-high (`A=1…L=0x200`) and active-low encodings, return **0 hits** in all 4 MiB. The game's input layer is a generic pad library (below); no game-code consumer reads the 6-entry key-history buffer at `0x03004324` (all xrefs to it are inside the library at `0x0800C000–0x0800F000`). Twelve button sequences pressed on the title screen (Konami, Konami reverse, `L+R+Start`, `L+R+A+B`, `A,B,A,B`, `U,D,A,B`, `Start+Select`, 8×A, `L+R+Start+A+B`, `B,A,B,A`, `U,U,D,D`) produced **only** the ordinary title→map/cutscene transitions — no flag, screen or menu change.
3. **No hidden / debug screen.** The complete reachable menu surface is: title (2 items), world-map mini-game select (multiple pages), story cutscenes, minigame gameplay, and pause (a `PAUSE` overlay with **no** menu items). There is no Options item anywhere. A savestate oracle over the identified screen-state word (`0x03003424`) forced to `0x00..0x0F` produced only the title screen (the word is a derived menu index, not the screen selector), so no hidden screen was exposed. No debug strings exist to label one.
4. **Published codes.** Web searches of 3rd party cheat index-style aggregators and archived pages found **zero** GBA cheats/password lists for this title (direct 3rd party cheat indexes `403`, archived guess `404`, 3rd party cheat indexes `403`; search-result evidence is uniformly "no cheats"). No published literal exists to verify against the ROM.

## 3. How to reproduce

**Environment.** mGBA (SDL) under `Xvfb :317 -screen 0 1024x768x24`, `openbox`, `SDL_AUDIODRIVER=dummy`, `mgba -3`. Keymap verified on menus: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows. **Hold every key 160–200 ms**; short taps are missed by this engine. GDB stub on TCP 2345 was occupied by a sibling session, so RAM was read from decompressed mGBA `.ss1` savestates (§16.13).

**Menu walk (screenshots on disk in the work dir):**

| Step | Input | Screen | RAM proof |
|---|---|---|---|
| boot | Return ×3–4, wait 4 s | Nick Jr. → title `STORY MODE` / `PLAY ANY GAME` | `0x03003424 = 6`, `0x03003428 = 7` |
| title | Down / Up | highlight toggles between the 2 items; never a third item | — |
| title | A / Start (STORY MODE or PLAY ANY GAME) | opening `¡Vámonos! Let's go!` cutscene ↔ world map | `0x03003424 = 7`, `0x03003428 = 8` |
| world map | Right / Left / A | cycles map pages (Benny, Dora, friends) and enters scenes | same state 7/8 |
| scene | A ×4 | dialogue → balloon minigame gameplay | — |
| gameplay | Start | `PAUSE` overlay only, no menu items | — |
| pause | Start / A / B | resumes gameplay | — |

`Options` does not exist as a menu item on the title, map or pause screens.

**Codes tested.** Twelve title-screen sequences listed in §2/§6b; each test restarted mGBA from a saved title state (`title2.ss1`) so results are independent. No code had any effect beyond normal navigation.

**Oracle tooling (exploration only, not a reportable cheat).** `sspatch.py` rewrote the zlib `gbAs` chunk of a savestate to force `0x03003424` to `0..15`; each was loaded with `-t`. This is a memory edit, not an in-game code, and is not presented as one.

## 4. Address map

| Address | Meaning | Evidence |
|---|---|---|
| `0x08000000` | Stock entry branch `0xEA00002E` | Observed (bytes) |
| `0x0800E4E8` | `ldrh r0,[0x04000130]` — raw KEYINPUT read | Derived (Thumb disassembly) |
| `0x0800EAD8` | Main pad poll; `mvns` active-high key state into `0x0300430C`, then 6+6 key handlers | Derived (BL xrefs: `0x080003D2`, `0x080045A`, `0x8009F3A`, `0x800B28C`, …) |
| `0x0800EB3C` | 6-entry key-history / move-to-front table manager | Derived |
| `0x0800EB70` | "mask in key history" API — 32 game-code callers | Derived (BL scan) |
| `0x0800EB90` | "keys held" API — 18 callers | Derived |
| `0x0800EBAC` | "keys pressed" API — 17 callers | Derived |
| `0x0800EC90` / `0x0800ED8C` | dialogue-input / repeat handling | Derived |
| `0x0300430C` | Active-high key-down word (`~KEYINPUT & 0x3FF` plus high bits) | Observed (savestate = `0xFFFFFC00` idle) |
| `0x03004324` | 6×`u16` key-history table (`1,2,4,8,0x100,0x200` init) | Observed |
| `0x080003B0` | Main title/menu loop; checks mask `0x0A` (`Start+Select`) with a 241-frame idle counter | Derived |
| `0x03003424` | Screen/menu index: `6` title, `7` world map | Observed (savestate diff) |
| `0x03003428` | Companion index: `7` title, `8` world map | Observed |
| Raw savestate | `.ss1` PNG with zlib `gbAs` chunk; 397,312-byte state; IWRAM at raw `0x19000`, EWRAM at `0x21000` | Observed (key-state bytes match GBA addresses) |

## 5. Algorithm

There is no validator to reverse. The only recovered system is the input layer and the screen index:

```
KEYINPUT @ 0x04000130 (active-low)
pad_poll():                                  ; 0x0800EAD8
    keys = ~KEYINPUT                         ; active-high
    [0x0300430C] = keys
    for i in 0..5: key_down(i, keys)         ; 0x0800EC10
    dialog_input()                           ; 0x0800EC90
    for i in 0..5: key_hit(i)                ; 0x0800ECF0
    key_repeat()                             ; 0x0800ED8C

key_in_history(ctrl, mask):                  ; 0x0800EB70
    return (history[ctrl] & mask) == mask

main_menu_loop():                            ; 0x080003B0
    pad_poll()
    if key_in_history(0, 0x0A) or key_in_history(2, 0x0A):
        reset_flag = 1                       ; Start+Select reset, not a cheat
    if no input for 241 frames: idle transition
```

No branch anywhere compares a key history against a multi-button cheat table; the sole multi-bit mask found in game code is `0x0A` (`Start+Select`) used for reset.

## 6. Tables

**GBA key masks (active-high)** used by the input library: `A=0x001 B=0x002 Select=0x004 Start=0x008 Right=0x010 Left=0x020 Up=0x040 Down=0x080 R=0x100 L=0x200`.

**Screen index values observed:** `0x03003424`: `6` = title, `7` = world map. `0x03003428`: `7` = title, `8` = world map. No Options/Debug index exists in any walked or forced state.

**No code tables:** password/code/secret/unlock/debug literal counts all `0`; key-mask sequence tables all `0` hits (details in §6b).

## 6b. Enumeration

**§0.2 space definition.** No password alphabet, length, checksum or lookup table exists, and no button-code table or reachable hidden menu exists. The spaces enumerated are therefore the *text*, *button*, *code-literal*, *menu/screen* and *published-code* spaces.

| Space | Size searched | Result |
|---|---|---|
| ASCII text bank | `strings -t x -n 4` = 64,731 lines over all 4 MiB | 0 code-related strings; all apparent hits are graphics. UI uses a tile-index bitmap font, so there is no searchable text bank. |
| Keyword literals (case-insensitive byte count) | 8 keywords × 4 MiB | `password 0, cheat 0, secret 0, unlock 0, debug 0, level select 0, code 1 (graphics), menu 0` |
| Ghidra defined strings | 448 strings (ARM-profile auto-analysis) | 100% graphics coincidences; 0 UI/debug labels |
| Uppercase/digit runs (possible alphabets) | 5,822 runs `[A-Z0-9!?@]{8,}` | all 4bpp tile data; only `0123456789ABCDEF` at `0x08019884` is a real (library hex-print) alphabet, not a password alphabet |
| Known button-code byte tables | Konami fwd/rev, `ABAB`, `U,D,A,B`, `L+R+Start`, `L+R+A+B`, `Start+Select`, 8×A — `u16`+`u8`, active-high+active-low | Konami/ABAB/UDAB: **0 hits**. `LRStart` u16 4, `LRAB` u16 10, `8A` u16 96 — all in graphics/data, none in code. |
| Input-history consumers | all xrefs to `0x03004324` (3) and `0x0300430C` (3) | all inside `0x0800C000–0x0800F000` library; no game cheat validator |
| Button sequences in emulator | 12 sequences on title, from a fixed savestate each | 0 hidden effects; montage `montage_codes.png` shows only normal map/cutscene transitions |
| Reachable screens | title (2 items), world map (paged), cutscenes, gameplay, pause (text only) | 5 screen classes; **no Options, no Debug** |
| Screen-index oracle | `0x03003424` forced to `0x00..0x0F` (16 savestates) | all 16 → title screen only; word is a derived index, no hidden screen exposed |
| Published codes | 4 web searches + direct 3rd party cheat indexes / archived (404) / 3rd party cheat indexes | 0 in-game codes published for this SKU; nothing to verify in ROM |

**Novel code:** not applicable — no code system exists to mint from (§0.2 point 5 governs). **Bounds proven by rejection:** the byte-level `0` hits for every standard key-mask sequence, the `0` keyword/literal counts, the 12 in-game sequences with no state change, and the 16-value forced-state oracle all bound the negative to the spaces enumerated above. There is no accepted-code space to test an out-of-range value against.

## 7. Validation evidence

- **Observed** — hashes/header; single Nintendo-logo header hit; `strings`/keyword/Ghidra/alphabet counts; key-mask byte-search counts; savestate RAM reads (`0x0300430C`, `0x03004324`, `0x03003424/28`); all screenshots and the two montages; 12 button-code tests; process cleanup.
- **Derived** — input-library function roles and API xref counts from Thumb disassembly and BL scans; `0x080003B0` main-loop mask `0x0A` and 241-frame counter; screen-index meaning from savestate diff.
- **Inferred** — that the title's UI text is a tile-index bitmap font (supported by zero ASCII text anywhere plus the rendered custom font); that no unreachable debug handler exists (supported by zero debug strings and zero reachable/gated screen, but an unreferenced, unlabelled handler cannot be excluded by black-box enumeration).

**Prompt-injection note (§16.8).** All fetched web pages and ROM strings were treated as data. No fetched page, search snippet or ROM text contained an instruction attempt; nothing found was acted upon.

**Comparison with siblings.** Verified independently on this hash. The three *Dora the Explorer* titles are a different engine (ImaginEngine; maker `9G`/`5L`, localised ASCII banks) and nothing from their analysis was assumed here. *Dora's World Adventure* is a Global Star Software build (maker `54`) with a bitmap-font UI. Result: no code, password, button sequence or reachable debug menu in this title, matching the bounded-negative outcome reported for *Super Star Adventures* but for entirely different reasons (no string bank at all here, versus that title's dead Debug menu). No mechanism is shared between the two.

## 8. Unknowns

- The bitmap font's character↔tile mapping was not decoded, so the exact byte encoding of on-screen words is not listed. The negative does not depend on it: keyword, Ghidra-string and alphabet searches plus full screen enumeration bound the search regardless of text encoding.
- Whether an unreferenced, unlabelled debug handler exists in code cannot be excluded by black-box enumeration; no string, screen or input path ever exposes one. Ghidra's ARM-mode auto-analysis resolved only 402 functions (Thumb is not fully profiled), so a static "all functions" claim is not made.
- Save data was 0 bytes throughout; no EEPROM/Flash code path was isolated. Unlockable collectibles (stars seen on the map) are ordinary gameplay progress, not developer-intended cheats.

## 9. Tooling

Scripts in `/tmp/doraworld`: `scan1.py`/`scan2.py` (KEYINPUT literal + Thumb LDR xrefs), `blscan.py`/`apixref.py`/`xrefkeys.py` (BL/xref and input-global consumer scans), `static_scan.py` (save-type, key-mask, alphabet, keyword counts), `ssread.py` (zlib `gbAs` savestate reader), `sspatch.py` (savestate word patcher), `test_codes.sh` (12-sequence title-screen harness), `enum_states.sh` (16-value screen-index oracle), `press.sh` (key helper). Stock tools: `arm-none-eabi-objdump -M force-thumb`, Capstone 5.0.7, Ghidra 12.1.4 via REA, `strings`, `xxd`, `xdotool`, `import`, `montage`. No third-party packages were installed for this engagement.

**Cleanup:** all generated `.sav`, `.raw` and `.ss1`–`.ss9` files were removed from the ROM folder; the :317 Xvfb/openbox/mGBA processes were stopped by PID; sibling sessions on :315 and :316 were left untouched.

**Legal note:** no ROM bytes, extracted graphics, music or game text were redistributed; only addresses, hashes, counts, algorithms and original analysis scripts are published here.
