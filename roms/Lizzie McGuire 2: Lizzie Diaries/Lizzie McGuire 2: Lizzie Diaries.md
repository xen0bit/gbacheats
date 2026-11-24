# Lizzie McGuire 2: Lizzie Diaries (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Lizzie McGuire 2: Lizzie Diaries.gba` |
| Size | 4,194,304 bytes (0x00400000) |
| Header title | `LIZZIE 2` |
| Game code / maker | `BL2E` / `4Q` |
| Version | 0x00 |
| Build stamp | `Jul 26 2004 10:31:50` at 0x0801B29CC — the **original** 2004 build (TCRF distinguishes a 2005 re-release whose debug text is at 0x08033AB8) |
| MD5 | `5f98ec175e2c67d3ba28504c1706dc07` |
| SHA-1 | `7ace37aec21c058aa98e3de12140cb691c070e00` |
| SHA-256 | `15d02967a647e3a04c9d067bb4ee2692c9a0e7d13b9703dbd029b58a68196bf5` |

**Embedded-header / patch scan (Phase 0).** The 156-byte Nintendo logo occurs exactly once, at file offset 0x00000004. There is no second/third GBA header, no multi-game pack, no appended trainer, and no cheat-patch signature. Entry word is `0xEA00002E` (`b 0x080000C0`), the stock GBA branch; the first 4 KiB is ordinary crt0 code. The fixed byte at 0xB2 is `0x96`. Header checksum is `0x0000` and complement byte `0x9E`, i.e. a rebuilt header — the usual scene-release artifact (guide §16.1); no evidence of a cracktro or patched code path. Conclusion: **licensed retail image, no trainer/patch**.

## 2. Executive summary

**There is no reachable in-game cheat, password, level-select, or button-code system in this ROM.** The main menu has only New Game, Load Game (disabled until a save exists), Options and Credits. Options contains Sound FX, Music and Language. The pause menu contains Continue, Options, Quit. No screen offers a code-entry field, and the decoded UI text bank contains zero occurrences of *password*, *cheat*, *secret*, *level select*, or *debug*.

The game **does** ship an unfinished developer debug menu. Its data is complete: a 22–24-entry table at 0x081B3690 with entries "02_01_A"…"02_01_L", "Fx Player", "Music Player", "Obj Viewer", "Asset Viewer", "Credits", "Normal Boot", and Mall/School/Beach in locked and `[UNLOCKED]` variants, plus a viewer-text bank at 0x0801B2B28 and a six-entry function-pointer table at 0x08030EB0. TCRF itself lists the game as *"To investigate — see if the debug menu can be accessed"*. This report closes that question negatively: a whole-ROM pointer scan and Ghidra xrefs show **no code or data outside the table itself ever references it** (0 external references to 0x081B3690, 0 to 0x08030EB0, 0 to any of the 22 entry addresses, 0 to the "Normal Boot" string). Six boot-time button combinations and eleven title-screen combinations and six pause-screen combinations were entered in the emulator; none reached the debug menu. This is a dead-feature/false-start result (guide §16.3 category 2), not an untested one.

The only other comparison routine found, `FUN_08028578` at 0x08028578, is an **"A2MY" save-record integrity check** (4-byte tag compare + 16-byte checksum), not a code validator. Save-based collectibles/unlocks exist in the text bank but no controller input reaches them.

## 3. How to reproduce

* Emulator: mGBA (SDL), `SDL_AUDIODRIVER=dummy`, `Xvfb :315 -screen 0 1024x768x24`, window manager `openbox`. Command: `mgba -3 "…/Lizzie McGuire 2: Lizzie Diaries.gba"`.
* Verified keymap (X11 XTEST to the focused mGBA window): **A = `x`**, **B = `z`**, **Start = `Return`**, **Select = `BackSpace`**, D-pad = arrow keys, L = `a`, R = `s`.
* **Hold keys ≈60 ms.** 150 ms holds double-step menus via X key repeat (guide §16.2); this was observed directly and corrected.
* Boot to title takes ~20–25 s under this heavily loaded host; wait for `PRESS START` rather than assuming a key failed.

Screen paths (all walked and RAM-verified):

| Screen | Input path |
|---|---|
| Title | boot → `PRESS START` |
| Main menu | `Return` at title → New Game / Load Game (dim) / Options / Credits |
| New Game slots | main menu `x` → three "Empty" slots |
| Options | main menu `Down` (Load Game is skipped) → `x` → Sound FX / Music / Language; `x` toggles Sound FX |
| Credits | main menu `Down Down` → `x` |
| Gameplay | main menu `x` → slot 1 `x` → save tutorial → `x` ×12 → side-scrolling level (health bar, `000/100` collectible counter) |
| Pause | `Return` in gameplay → Continue / Options / Quit |

Button-code tests (held from process launch until the title screen, screenshot compared against a title baseline): `L+R+Start`, `L+R+Select`, `Select+Start`, `L+R+A+B`, `Select+A+B`, `A+B+Start` — all 6 ended at the unchanged title screen. At the title screen (11 combos): the same six plus `A+B`, `L+Start`, `R+Start`, `Select+A`, `B+Start`, `Up+Down+Left+Right`, Konami `↑↑↓↓←→←→BA` — all produced only title or the ordinary main menu. At the pause screen (6 combos): `L+R+Start`, `L+R+A+B`, Konami, `Select+Start`, `L+R`, `A+B` — all produced only pause/gameplay.

No published in-game code exists to test: the GameFAQs cheats page for GBA id 920973 contains no submitted codes ("You can submit new cheats…"); TCRF documents only the debug text and leaves its accessibility open. GameHacking.org lists only external GameShark/CodeBreaker ROM patches for this title, which are explicitly out of scope. The GameFAQs page for *Lizzie McGuire: On the Go!* (id 918713) is a **different game** and its mini-game unlock is not applicable.

## 4. Address map

All addresses below are ROM addresses (`file offset + 0x08000000`) unless noted.

| Item | Address | Note |
|---|---|---|
| Header / crt0 | 0x08000000–0x080000C0 | stock entry branch `0xEA00002E` |
| Build stamp | 0x0801B29CC | `Jul 26 2004 10:31:50` (original revision) |
| Viewer text bank | 0x0801B2B28 | `OBJ VIEWER`, `Obj No:`, `Anim No:`, `Anim Mode:`, `Once/Loop/PingPong`, `MUSIC PLAYER`, `Music No:`, `FX PLAYER`, `Fx No:` |
| Button-mask lookup | 0x081B296A | ten u16 masks 1,2,4,…,0x200 (button index → mask), not a cheat |
| Debug text block | 0x08030D88–0x08030EB0 | `Level`, `MapX`, `MapY`, `02_01_A`…`02_01_L`, viewer labels, `[UNLOCKED]` labels, `Normal Boot` |
| Debug menu table | 0x081B3690 | 28-byte records; 22 well-formed entries, two more name slots at 0x081B38F8 / 0x081B3914 |
| "A2MY" header struct | 0x081B3918 | magic `0x594D3241` ("A2MY") at 0x081B391C; type-tag pointers 0x081B3918/19/1A used by menu records |
| Debug function-pointer table | 0x08030EB0 | 0x0805F5C4, 0x08060108, 0x0805C7F4, 0x0805D558, 0x0805E268, 0x0805EBB8 — no xrefs |
| Scene dispatcher | 0x0802746C | `FUN_0802746c`; 42-entry Thumb jump table at 0x08027590; global pointer at 0x08027578 = 0x02009B54 (struct at 0x02000018) |
| View screen handler | 0x08011D80 | called from 0x08011D56; renders the Obj/Music/Fx viewer text |
| Save integrity check | 0x08028578 | compares 4 bytes with `0x081B391C` ("A2MY") then a 16-byte checksum via `FUN_080285C4` |
| Joypad read | 0x08004DC4–0x08004DE6 | literal `0x04000130` at 0x08004DE0; used as a per-frame debugger watchpoint |
| UI text bank | 0x39B000–0x39FDxx | stored as `byte = ASCII − 0x20`; 113,881 strings after transform |
| EWRAM globals | 0x02009B50/54/60, 0x02009C00, 0x0201229C, 0x02012684 | screen state; savestate raw-state words distinguish screens |

Savestate RAM evidence (raw `gbAs` chunk, §16.13): word at raw 0x1D048 is `0x00000000` on the main-menu state and `0x00000001` on the New-Game/options/pause/gameplay states; word at raw 0x204D8 is `0x00000000` on the main menu and `0x3004B5C`/`0x3004BA4` once a game is loaded. This confirms screen transitions are backed by distinct RAM state rather than being only visual differences.

## 5. Algorithm

### 5.1 Debug-menu record format (data, not code)

Each record at `0x081B3690 + 0x1C·i`:

```
+0x00  u32  name pointer (ASCII string, e.g. 0x08030E5C "Mall")
+0x04  u32  0 (or a secondary data pointer for Credits)
+0x08  u32  type tag: 0x081B3918 / 0x081B3919 / 0x081B391A
+0x0C  u32  flags: {u16 scene/param, u16 group} — see §6
+0x10..0x1B zero
```

The viewer labels resolve through a separate text bank at 0x0801B2B28; the six function pointers at 0x08030EB0 were evidently intended as the action handlers but are never loaded.

### 5.2 Scene dispatcher (live code)

`FUN_0802746C` reads a byte at `*(0x02009B54) + 1`, subtracts 2, and if `< 0x2A` calls `jump_table[byte-2]()` from the 42-entry table at 0x08027590; otherwise it calls `FUN_08013854()`. This is the engine's real screen/system dispatch. The debug-menu table is **not** reached by this path: no entry of the jump table leads to 0x081B3690 or 0x08030EB0.

### 5.3 "A2MY" integrity check (the only validator-like routine)

```
u5 = 0
for k in 0..3:
    if *(char*)(struct+k+4) != *(char*)(0x081B391C+k): u5 = 1
s1 = *(u16*)struct; *(u16*)struct = 0
s3 = FUN_080285C4(struct, 0x10)      // 16-byte checksum
if s3 != s1: u5 = 1
return u5                            // 0 = intact, 1 = corrupt
```

This validates a save record's magic and checksum. It compares constant data to a struct — it never compares a user-entered buffer — so it is not a password validator (guide §16.2b).

### 5.4 Text encoding

The UI text bank is ASCII shifted down by 0x20 (`'C'` → `0x23`). Decoding `b -> b+0x20` for `0x21 <= b <= 0x5F` over the whole ROM yields readable `New Game`, `Options`, `Continue`, `Pause`, `Restart`, `Empty`, `COLLECTIBLES`, etc. This is the +0x20 case from guide §11: a plain `strings` search alone would have reported "no UI text".

## 6. Tables

### 6.1 Debug menu table (0x081B3690, unreachable)

| # | Name | Type ptr | Flags (u32) |
|---:|---|---|---|
| 1 | `02_01_A` | 0x081B391A | 0x001B0400 |
| 2 | `02_01_B` | 0x081B391A | 0x001B0500 |
| 3 | `02_01_C` | 0x081B391A | 0x001B0600 |
| 4 | `02_01_D` | 0x081B391A | 0x001B0700 |
| 5 | `02_01_E` | 0x081B391A | 0x001B0800 |
| 6 | `02_01_F` | 0x081B391A | 0x001B0900 |
| 7 | `02_01_G` | 0x081B391A | 0x001B0A00 |
| 8 | `02_01_H` | 0x081B391A | 0x001B0B00 |
| 9 | `02_01_I` | 0x081B391A | 0x001B0C00 |
| 10 | `02_01_J` | 0x081B391A | 0x001B0D00 |
| 11 | `02_01_K` | 0x081B391A | 0x001B0E00 |
| 12 | `02_01_L` | 0x081B3919 | 0x001B0105 |
| 13 | `Obj Viewer` | 0x081B3919 | 0x001C0105 |
| 14 | `Music Player` | 0x081B3919 | 0x001D0105 |
| 15 | `Fx Player` | 0x081B3918 | 0x00001F08 |
| 16 | `Normal Boot` | 0x081B3918 | 0x00001B00 |
| 17 | `Beach` | 0x081B3918 | 0x00221B00 |
| 18 | `Beach [UNLOCKED]` | 0x081B3918 | 0x00001E00 |
| 19 | `School` | 0x081B3918 | 0x00221E00 |
| 20 | `School [UNLOCKED]` | 0x081B3918 | 0x00001D00 |
| 21 | `Mall` | 0x081B3918 | 0x00221D00 |
| 22 | `Mall [UNLOCKED]` | 0x081B3918 | 0x00000503 |
| 23 | `Credits` (0x081B38F8) | 0x081B3918 (+4 = 0x081B37C8) | 0x00000000 |
| 24 | `Asset Viewer` (0x081B3914) | overlaps the trailing magic struct | — |

The `0x22` high byte marks the locked variant of a location; the low half (0x1B00/0x1D00/0x1E00) is the location/scene id (Normal Boot / Mall / School / Beach respectively). Field naming is **derived from the data layout**, not from executed code.

### 6.2 Reachable menu inventories (Observed)

* Title: `PRESS START` only.
* Main menu: New Game, Load Game (dim), Options, Credits.
* New Game: three `Empty` slots.
* Options: Sound FX (ON/OFF), Music (ON/OFF), Language.
* Credits: scrolling staff roll.
* Pause: Continue, Options, Quit.
* Gameplay HUD: health bar, collectible counter `nnn/100`.

### 6.3 Text-bank keyword census (decoded, 113,881 strings)

| Term | Hits | Classification |
|---|---:|---|
| `password` | 0 | — |
| `cheat` | 0 | — |
| `secret` | 0 | — |
| `level select` | 0 | — |
| `debug` | 0 | — |
| `unlock` | 3 | all three are debug-menu `[UNLOCKED]` labels |
| `code` | 1 | `Shin'en Multimedia. Code: B.Wodok` — audio-driver banner (guide §11) |
| `menu` | 1 | asset name `menu01` |
| `options` | 4 | real Options menu labels (English/French) |
| `collectible(s)` | 5 | gameplay objective text, not a code surface |
| `bonus` / `extras` | 2 / 1 | re-release bonus/menu text, no entry UI found |

### 6.4 Button-space census

* Boot combos tested: 6 (see §3), all → title.
* Title combos tested: 11 (see §3), all → title/main menu.
* Pause combos tested: 6 (see §3), all → pause/gameplay.
* Whole-ROM `u16` scans: 10,223 runs of ≥3 values in `[1,0x3FF]`; 109 runs of ≥4 consecutive single-button masks. Both counts are dominated by Thumb/ARM instruction encodings and compressed graphics (e.g. 0x1E32xx–0x1E3Cxx). The only structured hit is the legitimate button-index→mask table at 0x081B296A (`1,2,4,…,0x200`). No cheat key-mask sequence or press-history dispatcher exists.

## 6b. Enumeration

**No code system exists, so there is no code space to enumerate.** This is a bounded negative, not an omission:

1. **Space definition** — N/A. No password alphabet, no keyboard screen, no checksum word, no hard-coded code table, and no button-code mask table were found. The two candidate tables are a level/menu list (0x081B3690, 24 name slots maximum) and a button-index→mask lookup (0x081B296A, 10 entries). The only validator (`FUN_08028578`) validates a fixed 4-byte tag/16-byte save checksum, not user input.
2. **Validator model** — N/A; the save-integrity routine is fully modeled in §5.3 and accepts no user-supplied value. The scene dispatcher (§5.2) has a fully enumerated 42-slot jump table, none of whose entries reach the debug data.
3. **Novel code** — none minted, because there is no generator, alphabet, or accept/reject surface. This is the correct outcome for a game with no code system; guide §0.2's generation step applies to title/level/menu engagements only where a system exists.
4. **Bounds proved by rejection** — the 23 button combinations listed in §3/§6.4 were *entered* and rejected by the game (no state change beyond normal menu navigation). The complete 24-slot debug table was rejected structurally: 0 external references from code or data, 0 references to its function-pointer table, 0 references to its strings except from inside the table. A code-space bound does not exist to overrun; the menu-space bound is the enumerated inventories in §6.2 (4 main-menu items, 3 options, 3 pause items, 3 save slots), each visited with a screenshot and savestate RAM evidence.
5. **Debug-table enumeration** — all 24 name pointers and their record bytes were dumped (§6.1). Every one is unreachable from any input; the "Normal Boot" entry would be the exit from that menu, which confirms the menu was designed to replace normal boot but was never wired up.

## 7. Validation evidence

* **Observed** — screenshots of every reachable screen (title, main menu, New Game slots, Options, Credits, gameplay, pause); four boot combos and two more boot combos reaching the unchanged title; eleven title combos and six pause combos producing only normal screens; savestate `gbAs` words differing per screen (§4); all 72,545 raw `strings` and 113,881 decoded strings inspected for keywords.
* **Derived** — the 24-slot debug table layout and flag semantics; the 42-slot scene-dispatch jump table; the A2MY save-integrity algorithm; the ASCII−0x20 text encoding; the xref/pointer counts proving the debug data is orphaned; the button-mask scan counts.
* **Inferred** — that the debug menu was intended to boot into arbitrary levels/viewers (the entry names and `Normal Boot` make this highly likely) but was cut before release. Not observed executing.

No prompt-injection payload was found in the fetched TCRF/GameFAQs pages; the fetched GameFAQs snippet and GameHacking.org listing were treated as data only. No fetched page instructed any download or code execution.

## 8. Unknowns

* Whether an extremely unusual boot sequence (longer than six tested combinations, or a specific held D-pad sequence) reaches the debug menu cannot be proven by finite testing; the static result (zero references to the table from any code) is the stronger argument and makes any such path impossible without self-modifying or computed pointers, of which none were found.
* The exact semantics of the `flags` u32 in the menu records (0x1B00/0x1D00/0x1E00 location ids, 0x22 locked marker) are derived from data patterns, not from an executed renderer.
* Save-based `COLLECTIBLES`/`Extras` content exists in the text bank but its unlock conditions and whether a completed save exposes an extra screen were not exhaustively played through; no input path to a code-entry screen exists in any case.
* No ROM or copyrighted asset is reproduced here; addresses, hashes, and the analyst-written model only are published.

## 9. Tooling

* `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings`, `grep` for Phase 0/1.
* Python 3 scripts in `/tmp/lizzie2/`: `gba.py` (XTEST input, ~60 ms holds), `walk.py` (screenshot + savestate capture), `ss.py` (zlib-decompress the mGBA `.ss1` `gbAs` chunk), `combo.py` (boot-combo sweeps), `dbg_server.py`/`dbg.py`/`snap.py` (mGBA `-d` CLI debugger via pty).
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for raw disassembly.
* REA/Ghidra 12.1.4 (raw-binary import, ARM base 0x08000000): `xrefs`, `resolve_containing_procedure`, `procedure_pseudo_code`, `procedure_callers`.
* mGBA 0.x SDL (`-3`, `-g`, `-d`), Xvfb `:315`, openbox, `xdotool`, `scrot`, ImageMagick `compare -metric AE` for screen-change detection.
* Text transform: `b + 0x20` for `0x21 <= b <= 0x5F` applied to the ROM bytes before `strings`.
