# Phil of the Future (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Phil of the Future/Phil of the Future.gba` |
| Size | 8,388,608 bytes (`0x800000`) |
| Header title | `PHILOFUTURE` |
| Game code / maker | `BFXE` / `4Q` |
| Version | `0x00` (Rev.00); main unit `0`, device `0` |
| Entry branch | `0xEA00002E` (stock `b 0xC0` — no cracktro/trainer patch) |
| Header checksum | `0x0000`; complement byte `0x50` (sum `0xA0..0xBD` = `0xE7`, not 0) → header was rebuilt; per guide §16.1 this is a header-edit artifact, not a game patch |
| Embedded headers | Nintendo-logo scan: **1** hit, at file `0x0` → single monolithic image, no multi-game shell |
| MD5 | `8dd015022218c0df89bdd4a1a1fc4e7b` |
| SHA-1 | `ba123af9938484cf1e2ea0fd191c75c90078f035` |
| SHA-256 | `b97766a8f736bc1888130c75d66fea2ad150b0c64cf38792681bb00faa620c49` |
| Developer / publisher | Handheld Games / Buena Vista Games, 2006 (from GameFAQs/LaunchBox) |

Save medium observed: 512-byte EEPROM-style save; first bytes `0a 6c 65 48 64 6e 61 48` = length byte + `Handheld` reversed. Not a code system.

## 2. Executive summary

**There is no in-game password, button code, cheat menu, or unlockable-code system in this ROM.** No code literal, no entry surface, no validator, no key-mask sequence table, and no published codes exist. The game is a linear mission-based platformer with a four-item title menu (New Game / Continue / Options / Credits), an in-game pause screen whose only action is "return to main menu", and a 512-byte battery save.

The ROM *does* contain leftovers of an unfinished **hidden "Debug Menu"** and a **"LEVEL SELECT"** text/menu bank:

* The title-menu string table at `0x081ede48` has a fifth slot, `"Debug Menu"` at `0x081ede70`, and the menu-dispatch state machine at `0x0806fc9c` even has a `case 4` branch at `0x0807021c`.
* However, initialization (`0x0806fa84`) only enables items 0–3, the item-ID table at IWRAM `0x03002680` holds `[0,1,2,3,0,0]` (index 4 has **no allocated ID**), and the cursor at IWRAM `0x030046AC` is hard-wrapped to `0..3` by `0x0806ffbe..0x0806ffd6`. Ghidra enumerated all **22** xrefs to the cursor; none in the title path writes `4`. A savestate with the cursor/item-ID/enable bit forced to 4 produced **no visible Debug Menu screen**.
* `"LEVEL SELECT"` (`0x081f0ae4`) and `"MAIN MENU"` (`0x081f0ac8`) live in a script/data bank (`0x0854ad00`, pointers at `0x0854ad0c`/`0x0854ad14`) with **no direct code xref** and no path from any walked screen.

Classification per guide §16.3: **cut/dead feature**, not a gated or live system. No code can be minted because no code format exists; the negative is bounded by full screen enumeration, text/alphabet counts, button-sequence tests, literal scans, and the published-source check.

## 3. How to reproduce

* Emulator: mGBA 0.10 (SDL), headless: `Xvfb :317 -screen 0 1024x768x24`, `SDL_AUDIODRIVER=dummy mgba -3 <rom>`. Host display/keymap used: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad = arrow keys.
* GBA viewport crop on this Xvfb: `convert shot.png -crop 720x480+152+166 +repage crop.png`.
* Deterministic path:
  1. Boot → attract/"PRESS START" → press **A** or **Start** → title menu (4 items).
  2. Down/Down + A → **Options** (`Music:On`, `Clear Save`, `Main Menu`). Down×3 + A → **Credits**.
  3. New Game + A×~30 → gameplay (Phil's bedroom, HUD with four "OFF" gadget slots).
  4. **Start** → pause screen (`PAUSED`, `SCORE: 0`, objective, "B Return to main menu"). **B** → "Are you sure? YES/NO" → YES → title menu.
  5. **L** during gameplay produced only story dialogue in the tested early area; no menu appeared.
* RAM reads: mGBA `.ss1` savestates are PNG with a zlib `gbAs` chunk. Decompressed raw layout (verified): EWRAM `0x02000000` → raw `0x21000`; IWRAM `0x03000000` → raw `0x19000`. `Shift+F1..F9` saves, `F1..F9` loads. This gave exact RAM values without a debugger stub (guide §16.13). An mGBA `-d` PTY debugger was also used to drive/reset the core.
* Codes tested: **none exist to test** (§3.4 / web results below). 23 button sequences/combos were tested instead and produced no state change (§6b).

## 4. Address map

| Item | Address / offset | Notes |
|---|---|---|
| Title menu setup | ROM `0x0806fa84` (`0x6fa84`) | Writes five string pointers into EWRAM `0x02017820`; enables items 0–3 only |
| Title menu state machine | ROM `0x0806fc9c` | Screen state `0x030046C0`; dispatch switch on cursor `0x030046AC`; `case 4` at `0x0807021c` |
| Cursor wrap (0..3) | ROM `0x0806ffbe`–`0x0806ffd6` | `if (cursor==3) cursor=0; else cursor++` for Down; symmetric for Up |
| Menu item-enable helper | ROM `0x080e6738` | `FUN(index, enabled)`; no caller passes index 4 |
| EWRAM menu pointer table | `0x02017820` | `+0x00` New Game `0x081ede48`; `+0x04` Continue; `+0x08` Options; `+0x0C` Credits; `+0x10` **Debug Menu** `0x081ede70`; `+0x1C..+0x34` dialog strings |
| IWRAM item-ID table | `0x03002680` | observed `[0,1,2,3,0,0]`: index 4 unallocated |
| IWRAM title cursor | `0x030046AC` | observed `0` at title menu; 22 xrefs total, none write 4 in title path |
| IWRAM screen state | `0x030046C0` | observed `0` at title menu |
| Map whitelist | ROM `0x0806f968` | returns true for map IDs `0x5D,0x5F,0x61,0x63,0x64,0x66,0x68,0x6A,0x6C,0x6D,0x6F,0x71,0x72,0x74,0x76,0x77,0x78,0x7A,0x7C,0x7D,0x7F,0x81,0x82,0x84,0x86,0x88,0x89` — **27** missions; callers `0x08079a8c`, `0x080ce370` (mission/area validity, not a cheat validator) |
| "Debug Menu" string | ROM `0x081ede70` (file `0x1ede70`) | only pointer: `0x0806fc10` |
| "LEVEL SELECT" string | ROM `0x081f0ae4` | pointer in data bank `0x0854ad14` (no code xref) |
| "Select Area" string | ROM `0x081edf04` | pointer `0x080709f8`, used by a level/area selection screen at `0x0807096c` |
| Font/tile LUTs | ROM `0x081f05f0`, `0x081f0600`, … (five 256-byte banks) | ASCII→tile index; confirmed text is ASCII-based, not an undecoded cipher |

## 5. Algorithm

No password/checksum algorithm exists. The only "state machine" relevant to cheats is the title-menu dispatcher:

```
state = *(u32*)0x030046C0
if state == 1: draw "erase data?" variant; handle A/Start
if state == 2: draw dialog variant; A or Start -> state 0
else:                                   # state 0 = title menu
    if key(Up)    and *(u32*)0x030046B0 == 0:
        cursor = (cursor == 0) ? 3 : cursor - 1
    if key(Down)  and *(u32*)0x030046B0 == 0:
        cursor = (cursor == 3) ? 0 : cursor + 1
    if key(A) or key(Start):
        switch (*(u32*)0x030046AC) {
          case 0: new game;  case 1: continue;
          case 2: options;   case 3: credits;
          case 4: /* Debug Menu: FUN_080d1880(...), no reachable input */
        }
```

Reimplementation is unnecessary — the space has 4 reachable indices and one unreachable.

## 6. Tables

* **Title menu reachable entries (4):** index 0 New Game, 1 Continue, 2 Options, 3 Credits.
* **Unreachable slot (1):** index 4 "Debug Menu" (`0x081ede70`) — pointer present, no ID, no enable call, cursor cannot reach 4.
* **Options entries (3):** `Music:On/Off`, `Clear Save`, `Main Menu`.
* **Pause entries (1):** `B — Return to main menu`.
* **Mission-ID whitelist (27 values)** at `0x0806f968` — listed in §4; this validates game areas, not cheat input.
* **Save record:** 512-byte header `0A` + `Handheld`; no unlocked-level flag array identified in the tested bytes.

## 6b. Enumeration

**Space definition.** There is no code space. Characterizing the only candidate:

| Candidate space | Size | Reachable | Bound proof |
|---|---:|---:|---|
| Title-menu cursor values | 5 representable (0–4) | **4** (0–3) | `cmp r0,#3` wrap at `0x0806ffc2`; 22 xrefs to `0x030046AC`, none write 4 in title path; RAM shows cursor 0 after all input tests |
| Menu item-ID table slots | 6 observed | 4 | `0x03002680` = `[0,1,2,3,0,0]` from savestate RAM |
| On-screen password/keyboard surfaces | **0** | 0 | no `password`/`enter`/`cheat` strings; no alphabet table beyond five font LUTs |
| Button-sequence tables | **0** | 0 | 540 mask-like u16 runs of length ≥4 scanned; all are literal pools / asset bytes, none referenced as a key-code table |

**Validator model.** N/A — no validator, checksum, or comparison table exists. The only comparison logic is the 27-value mission whitelist (`0x0806f968`), which is a game-state gate, not user input.

**Novel code.** Impossible by construction: there is no code format to mint. This is the bounded negative required by §0.2, not an omission.

**Bounds proven by rejection.**
* 12 button combos (none, L, R, L+R, Select+Start, A+B, Up+Down, L+R+A, L+R+Start, B+Select, Start, Select) on a fresh title menu: cursor stayed `0x0`, screen state `0x0` in every case (RAM read from savestate slot 5).
* 11 longer sequences incl. Konami code (`↑↑↓↓←→←→BA`), `L+R+Start`, `Start+Select+A+B`, `L+A/R+A`, `XXX ZZZ`: cursor stayed `0x0`; one sequence left only a transient dialog flag (`0x030046B0 = 1`).
* Forced acceptance test (oracle, guide §16.19): patched savestate setting cursor `0x030046AC=4`, item ID `0x03002690=4`, enable byte `0x03002BE5|=1` → loaded → **no Debug Menu screen appeared** (title menu unchanged even after A). Label: **Derived** (static proof) + **Observed** (forced-state screenshot).
* Published codes: none exist to accept/reject (§7).

## 7. Validation evidence

* **Observed** — emulator screenshots: attract screen, 4-item title menu, Options, Credits, gameplay HUD, pause screen, quit-confirm dialog, intro dialogue, L-press dialogue, forced-cursor result.
* **Observed (RAM)** — savestate `gbAs` reads: cursor `0`, screen state `0`, menu pointer `0x081ede48`, item IDs `[0,1,2,3,0,0]`, all 23 button tests leaving cursor `0`.
* **Derived** — Ghidra decompilation of `0x0806fa84`, `0x0806fc9c`, `0x0806f968`, `0x08079a8c`; Capstone literal/BL scans; xref enumeration of `0x030046AC`.
* **Inferred** — the `case 4` branch would display *something* via `FUN_080d1880`; no reachable input and the forced attempt showed nothing, so the intended Debug Menu content is unknown and reported as cut content.
* **Web (external service, treated as data)** — GameFAQs cheats page (archived 2020 capture) contains **no cheats**; Cheat Happens states "no cheats or cheat codes for Game Boy Advance"; no TCRF page exists. Search result snippets contained no password literals. No prompt-injection payload was encountered in the fetched pages.

## 8. Unknowns

* Intended contents of the dead "Debug Menu" / "LEVEL SELECT" screens cannot be exercised: both are unreferenced by any reachable input path. The `case 4` text-box argument is a RAM pointer (`0x030046B8`) whose intended value was never observed.
* Whether a save-data milestone (game completion) unlocks the LEVEL SELECT in a later build; no such flag was found in the tested 512-byte save.
* The exact purpose of the `FUN_080e6738` side-effect on I/O register `0x04000000` was not investigated (unrelated to cheats).

## 9. Tooling

* `file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings -t x`, Python 3.13 + `struct`/`zlib`/`capstone 5.0.7`/`Pillow 13.0.0`.
* `arm-none-eabi-objdump -M force-thumb` for raw range disassembly; REA MCP + Ghidra 12.1.4 (raw-ARM import, base `0x08000000`) for `analyze_function`/`xrefs`.
* mGBA 0.10 SDL (`-3`, `-d` PTY debugger), Xvfb `:317`, openbox, `xdotool`, `scrot`, ImageMagick.
* Helper scripts in `/tmp/philfuture/`: `patch_state.py` (savestate word patcher), `seqtest.py` (button-sequence + RAM harness), `dbg_bridge.py` (mGBA CLI debugger bridge). Capstone BL/literal scanners were one-off inline scripts.
* No ROM or copyrighted asset is redistributed; only hashes, addresses, and derived findings are published.
