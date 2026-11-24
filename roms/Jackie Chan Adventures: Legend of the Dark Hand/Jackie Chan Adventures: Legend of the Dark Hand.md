# Jackie Chan Adventures: Legend of the Dark Hand (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Jackie Chan Adventures: Legend of the Dark Hand.gba` |
| Size | 4,194,304 bytes (4 MiB, 0x400000) |
| Header title | `JACKIECHANDH` |
| Game code / maker | `AJCE` / `52` |
| Version byte | `0x00` (Rev.00) |
| Entry word | `0xEA000030` (stock crt0 branch to 0x080000C0) |
| Header fixed byte | `0x96` @0xB2; complement `0x8A` @0xBD; checksum `0x0000` @0xBE |
| MD5 | `863bb2f057959ec7b21aa0174c817fa9` |
| SHA-1 | `f6f5c7bc566269530ddb13b76fc3d05cc22c11e3` |
| SHA-256 | `d44670b727cbe6c39473e722022ccf05f30ff9cbac10d0276d3e32f8bd443374` |

Embedded-header scan (156-byte Nintendo logo `24 ff ae 51 69 9a a2 21 3d 84 82 0a`) found **exactly one** GBA header at file 0x0. No second game image, no appended trainer, no patched entry point. `0x0000` header checksum plus complement `0x8A` is a rebuilt-header artifact (§16.1), not evidence of a trainer; the code paths are unmodified stock crt0.

## 2. Executive summary

The game has **one** developer-intended cheat surface: a **button-code system on the title screen** ("Press Start"). The engine registers **exactly five** button sequences at boot of the title screen; entering any of them unlocks a hidden **"SECTION 13" menu** (NEW GAME / TRAINING / OPTIONS / CONTINUE) instead of going straight into the opening cutscene. The publicly documented code — hold **R**, press **B, A, Left, Down, Up, Right** — is record #1 and was verified both literally in ROM and in the emulator.

Four further records are **not in any published list** (3rd party cheat index list only the one code). They were enumerated from the ROM table, generated as key presses, entered in the emulator, and each produced the unlock menu. The complete space is therefore small and closed: 5 records, each `{u16 hold-mask, u16 sequence…, 0xFFFF terminator}`.

A **password UI** exists in the image (PASSCSR / PASSBUT / PASSDIG / INTPASSDIGIT entities, a 4×32 character grid and a 0x0801B518 screen driver) but **no accepted password literal or encoder/decoder table** was found, and no reachable screen displays it: CONTINUE on the unlocked menu is inert with a blank (0xFF-filled) 512-byte SRAM. The report treats this as a **gated/unreachable feature**, not as "no code system" — the button codes are real and working. The game's on-screen text is **font/tile-indexed** (§11), so `strings` finds only debug entity names; a tile-index table at file `0x22330..0x22386` (byte values `0x0A..0x3F`) was located and decoded.

No GameShark/CodeBreaker codes are reported (out of scope); the published CodeBreaker/Action Replay lists found on the web are memory patch codes, not in-game cheats.

## 3. How to reproduce

* Emulator: `mgba 0.10.5` under `Xvfb :318 -screen 0 1024x768x24`, `SDL_AUDIODRIVER=dummy`, launched `mgba -3 <rom>`; window cropped `720x480+152+144`.
* Keymap verified by reading active-high key masks at `0x03004FD4` while holding each key:

  | GBA | key | mask | GBA | key | mask |
  |---|---|---|---|---|---|
  | A | `x` | `0x001` | Right | `Right` | `0x010` |
  | B | `z` | `0x002` | Left | `Left` | `0x020` |
  | Select | `BackSpace` | `0x004` | Up | `Up` | `0x040` |
  | Start | `Return` | `0x008` | Down | `Down` | `0x080` |
  | R | `s` | `0x100` | L | `a` | `0x200` |

* Path: boot → legal screen → **Start** → title ("PRESS START"). If an attract/demo plays, press Start to return to the title (demos ignore input).
* Enter a code at the title, then press **Start**. Success = the "SECTION 13" menu appears; failure = the opening cutscene appears.
* Published code tested: hold `s` (R), tap `z x Left Down Up Right`, release R, Start → SECTION 13 menu (screenshot `code1_startc.png`, `unlocked_menu_raw.bin`).
* Menu navigation: cursor is RAM `0x03000BE8`, values 0..3, **no wrap** (at 3, Down does nothing). 0=NEW GAME, 1=TRAINING, 2=OPTIONS, 3=CONTINUE. OPTIONS/difficulty → EASY/MEDIUM/HARD → gameplay. In gameplay Start → Pause (music icon / Back / Quit); Quit → "Quit?"/Yes/No confirm.

## 4. Address map

All addresses are ROM (`0x08……`) or RAM (`0x02…/0x03…`). File offset = ROM address − `0x08000000`.

| Address | Size | Meaning |
|---|---|---|
| `0x080045F8` | fn | Title-screen controller. Registers the 5 codes (BL to `0x0801918C` five times at `0x8004682..0x80046A2`), then checks matches via `0x08019090` at `0x80046D8`. |
| `0x0800471C..0x0800472C` | 5×u32 | Pointer table: `0x083C51FC`, `0x083C521E`, `0x083C5240`, `0x083C520C`, `0x083C522C` (the five code records). |
| `0x080046DC..0x080047E4` | code | Match dispatch: compares returned record pointer to the five pointers and calls `0x08018F94` with id `0x36 / 0x38 / 0x30 / 0x39 / 0x37` respectively. |
| `0x08018F94` | fn | Generic script-action dispatcher; calls `0x0801F434(action_id)`. |
| `0x08019090` | fn | **Button-code validator** (called once per frame). Reads code manager at `r0`, key-globals at `r1`/`r2`; returns matched record pointer or 0. |
| `0x0801918C` | fn | Registers one code into the manager: stores `{u16 mask, u32 sequence_ptr, u16 length}` in a 12-byte entry at manager+4+n*12. |
| `0x08004258` | fn | Generic entity factory used by UI/mission setup. |
| `0x08004980` | fn | Per-frame key update. `0x03004FD0 = pressed & ~held` (edge), `0x03004FD4 = held`, both active-high. |
| `0x083C51FC..0x083C5245` | 5 records | **Button-code table** (see §6). |
| `0x03004FD0 / 0x03004FD4` | u16/u16 | Edge-pressed / held key masks (verified by holding keys and reading savestates). |
| `0x03000BE8` | u8 | Section 13 menu cursor 0..3 (verified: Down increments 0→1→2→3, no wrap). |
| `0x08215354` (file `0x21554`) | 155 names | Entity-name table, NUL-terminated, 4-byte aligned; PASSCSR index 149, PASSBUT 150, PASSDIG 151, INTPASSDIGIT 144, CHEATOPT 148, SAVEGAMESTR 141, QUITCONFIRM 142, CONTINUE 146. |
| `0x083C46B8+` | 12 B/entry | Entity descriptor table `{name_ptr, handler, flags}` in descending entity-id order. PASSDIG handler `0x08008E65`, PASSBUT `0x08008E21`, PASSCSR `0x08008E99`. |
| `0x0801B518` | fn | Password screen main loop; init `0x0801BB0C`, cleanup `0x0801BB7C`. Called from 7 UI handlers (`0x80037A0`, `0x80050C8`, `0x80057A2`, `0x8009016`, `0x800B0CE`, `0x800B8C8`, `0x800DCBE`). |
| `0x0801BF3E..0x0801BF7A` | code | Password grid transpose: 4 rows × 32 columns, byte stride 0x80. |
| `0x030031A0 / 0x030031EC / 0x030031F0 / 0x030031F4` | globals | Password-screen state; `0x030031F0` and `0x030031F4` clamped to [-7,7] at `0x8009E2..0x800A14`. |
| `0x0822330..0x0822386` (file) | bytes | Font/tile-index table, values `0x0A..0x3F` — in-game text is tile-indexed, which is why `strings` missed all UI labels. |

## 5. Algorithm

Recorder / registration (`0x0801918C`), per code record in ROM:

```
record := { u16 hold_mask; u16 seq[1..]; u16 0xFFFF }
register(manager, record):
    n = manager.count++                       ; entry = manager+4+12*n
    entry.mask = *record                      ; first u16
    entry.seq  = record+2                     ; first sequence element
    entry.len  = number of u16 until 0xFFFF   ; computed by the loop at 0x80191A2..0x80191B6
```

Validator (`0x08019090`), called each frame with `pressed = *(u16*)0x03004FD0`, `held = *(u16*)0x03004FD4`:

```
history = u16[32] ring at manager+0xC8 ; index at manager+0xC4
if pressed == 0: return 0                       ; no key event, nothing recorded
history[index] = pressed ; index = (index+1) & 31
for each registered code:
    if code.mask != 0 and (held & code.mask) == 0: continue
    ok = true
    for i in 0 .. code.len-1:                   ; walk most-recent backwards
        if history[(index-1-i) & 31] != code.seq[code.len-1-i]: ok = false; break
    if ok: return record_pointer               ; caller dispatches on this pointer
return 0
```

Caller maps matched record → action id (`0x080046DC`):

```
0x083C51FC -> 0x36    0x083C521E -> 0x38    0x083C5240 -> 0x30
0x083C520C -> 0x39    0x083C522C -> 0x37
```

Names of the action ids were not isolated (see §8). Semantically all five lead to the same visible unlock menu.

## 6. Tables

The five records at `0x083C51FC` (masks are active-high key bits; sequence is one u16 per press):

| # | ROM addr | hold mask (buttons) | sequence (press order) | len | dispatch id | published? |
|---|---|---|---|---:|---:|---|
| 1 | `0x083C51FC` | `0x100` = **R** | B, A, Left, Down, Up, Right | 6 | `0x36` | **YES** (3rd party cheat index-style lists: "hold R and press B, A, Left, Down, Up, Right") |
| 2 | `0x083C520C` | `0x202` = **B+L** | A, Up, Up, Up, Down, Down, Down | 7 | `0x39` | no |
| 3 | `0x083C521E` | `0x201` = **A+L** | B, Left, Up, Right, Down | 5 | `0x38` | no |
| 4 | `0x083C522C` | `0x300` = **R+L** | B, A, Left, A, Right, A, Left, A | 8 | `0x37` | no |
| 5 | `0x083C5240` | `0x000` = none | Start | 1 | `0x30` | no |

Every record ends in `0xFFFF`. A sixth candidate at `0x083C5246` (`0000 274c 0802 …`) is **not** registered — only five pointers exist — and is unrelated data.

## 6b. Enumeration

**Space size (proven closed).** The title controller issues exactly five BLs to the registration function (`0x8004682, 0x800468A, 0x8004692, 0x800469A, 0x80046A2`); a whole-ROM BL scan for `0x0801918C` returns only those five. A whole-ROM BL scan for the validator `0x08019090` returns only one caller (`0x80046D8`, the title controller), so there is no second button-code screen. Records are terminated by the literal `0xFFFF` at `0x80191C8`, and the registration loop counts to that terminator — so the accepted set is exactly the five strings in §6 (sequence length 1–8, hold mask ∈ {0x000,0x100,0x201,0x202,0x300}).

**Novel codes (not on 3rd party cheat indexes / any wiki).** The web search found only record 1 published. Records 2–5 were minted from the ROM table and entered on the real title screen:

* Record 2 (hold B+L, A↑↑↑↓↓↓) — `rec2c.png` → SECTION 13 menu.
* Record 3 (hold A+L, B←↑→↓) — `rec3b_afterc.png` → SECTION 13 menu.
* Record 4 (hold R+L, B A ← A → A ← A) — `rec4b_afterc.png` → SECTION 13 menu.
* Record 5 (Start alone) — `rec5_afterc.png` → SECTION 13 menu.

The published record 1 was re-entered as a control (`code1_startc.png`) and produced the identical screen, so decoder and input path agree.

**RAM proof of the effect.** Savestates taken right after each code record (before Start) and at the unlocked menu show game state changed; the menu cursor was isolated at `0x03000BE8` (0→1→2→3 under successive Down presses, confirmed by decompressed `gbAs` savestate reads). The button code globals `0x03004FD0`/`0x03004FD4` were read directly: holding B+R yielded `held = 0x0102`, and each individual key's mask was read and tabulated in §3. The .sav file stays entirely `0xFF` throughout, proving the unlock is RAM-resident, not a save-bit unlock (§16.18).

**Bounds / rejection.** Two distinct negatives were observed and are reproducible:

1. **Idle/attract state rejects all input** — during the demo (`bare_beforec.png`, "Demo" overlay with score), holding keys leaves `held = 0x0000` and Start only returns to the title; no code is evaluated.
2. **No input at the title does not unlock** — a title state with no code entered goes into the opening cutscene on Start (`nostartc.png`), whereas a registered code goes to the SECTION 13 menu.

A caveat is important and is reported as such: record 5 accepts **Start alone**, so any test that *ends* by pressing Start from the title will unlock even if the preceding button sequence was wrong (`wrongfast_vc.png` shows the title, `wrongfast_afterc.png` shows the unlocked menu). This is a property of the game's fifth record, not a decoder error — the accepted set is still exactly the five records, and no sixth sequence was found by the two BL scans. A stricter "wrong-sequence rejected at the same screen" experiment is therefore not expressible through this entry path; that is an **unknown**, not a claimed success (§0.2).

**No algorithmic code system.** The password subsystem's only on-screen characters are tile indices, and no password alphabet table of accepted strings and no generator/validator over a symbol space was found (the `strings` keyword hits for "code" are the Shin'en GAX audio banner `0x0837748E` and internal entity names). The space that was searched: all `strings -t x -n 3/4` output (35,688 strings) filtered for password/cheat/code/debug/secret/unlock/level/menu; literal searches for every published code; the complete 155-entry entity name table; the full 12-byte-stride entity descriptor table; and BL/xref scans for the two input-matcher functions.

## 7. Validation evidence

* **Observed** (emulator screenshots + decompressed mGBA savestate RAM reads): legal → title → SECTION 13 menu; all 5 codes accepted; menu cursor RAM 0x03000BE8; key masks at 0x03004FD0/4; SRAM all 0xFF; demo ignores input; pause → Back / Quit → Quit? confirm; difficulty select → gameplay.
* **Derived** (disassembly): the 5-record table, `0xFFFF` terminators, register/check functions, the 12-byte entry layout, the history-ring matcher, the five action ids, the password entity descriptors and 4×32 grid code at `0x0801BF3E`, the font tile-table at `0x0822330`.
* **Inferred**: the semantic meaning of action ids `0x30/0x36/0x37/0x38/0x39` (all produce the same visible menu; per-code flag differences were not isolated); that the password screen is reached only through one of the seven UI handlers at §4 but no player-accessible path to those handlers was found.

Published-code verification: the literal string of the published button sequence is present as key masks exactly once at file `0x3C51FE` (u16 sequence `02 00 01 00 20 00 80 00 40 00 10 00`), immediately preceded by mask `0x0100` (R) and followed by `0xFFFF`. The published "infinite health / lives / moon jump" etc. found on 3rd party cheat indexes are CodeBreaker/Action-Replay memory patches (e.g. `32006218 0064`) and are **not** in-game cheats; they were not tested (out of scope).

## 8. Unknowns

* The exact per-code difference between ids `0x30/0x36/0x37/0x38/0x39` (all five unlock the same visible menu; no isolated flag word was found within the noisy savestate diffs).
* The password screen could not be reached from any walked screen; CONTINUE is inert with an empty 0xFF SRAM. Whether a completed save/link play enables it was not tested.
* No published password strings exist for this SKU to cross-check; the password subsystem may be leftover engine code (§16.3, "dead code" vs "gated feature" not fully separated).
* Strict rejection of a wrong button sequence at the title is masked by record 5 (Start alone), as detailed in §6b.

## 9. Tooling

* `md5sum`/`sha1sum`/`sha256sum`, `file`, `xxd`, `strings -t x`, Python 3 for literal/pointer/BL scans and Thumb LDR literal maths.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for all disassembly.
* `mgba 0.10.5` (`-3`, `-t` for savestate restore), `Xvfb :318`, `openbox`, `xdotool` (XTEST events, 60–160 ms holds), `scrot` + ImageMagick `convert`.
* Savestate RAM reads: mGBA `.ss1` is a PNG with a zlib-compressed `gbAs` chunk; decompressed to 397,312 bytes, IWRAM mapped at state offset `0x19000` (RAM `0x03000000`), EWRAM at `0x21000`. Helper scripts in `/tmp/jackie/` (`ssread.py`, `ss2raw.py`, `snap.sh`, `ram.py`, `key.py`, `keyfast.py`, `testcode.py`, `testcode2.py`, `fasttest.py`).
* mGBA command-line debugger (`mgba -d` with a persistent FIFO writer) was used for live RAM reads and a breakpoint at the per-frame key-update function `0x08004980`; the GDB stub was unavailable because port 2345 was owned by another user's emulator.

Legal note: no ROM data or copyrighted graphics were copied into this report; only hashes, addresses, algorithms, buttons and observed screenshots are documented.
