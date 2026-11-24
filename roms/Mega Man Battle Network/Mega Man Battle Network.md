# Mega Man Battle Network (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Mega Man Battle Network/Mega Man Battle Network.gba` |
| Size | 8,388,608 bytes (8 MiB) |
| Header title | `MEGAMAN_BN` (0xA0–0xAB) |
| Game code | `AREE` (USA, rev 0) — matches 3rd party cheat indexes USA `AREE`, checksum `E7` |
| Maker | `08` (Capcom) |
| Version / complement / checksum | `00` / `00` / `0x00E7` |
| Entry word | `0xEA00002E` → stock crt0 at `0x080000C0` |
| MD5 | `9ff40cf640575211202b7bda5487abbb` |
| SHA-1 | `a4fbae389654a6611d0597b1e9109cbbd32a132f` |
| SHA-256 | `87bc7257f2f9ed0acc9f4874177e474e3d339d1e23a0b621d2d8edd73c1a09ed` |
| CRC-32 | `1D347971` (published USA value; header checksum `E7` confirms) |
| Build stamp | `ROCKMAN EXE 20010727` at ROM `0x1FBB4` (3rd party cheat indexes US build date) |

**Phase 0 result:** exactly **one** embedded GBA header (Nintendo-logo signature scan over all 8 MiB: hit at file `0x0` only). The entry word is the unmodified stock branch; the 4 KiB crt0 is ordinary ARM reset/clear code. **No scene cracktro, no appended trainer, no patch.** This is the retail USA revision 0 image the published codes refer to.

## 2. Executive summary

**Finding: this ROM contains no in-game / developer-intended cheat code system.** There is no title-screen button code, no password entry that unlocks content, no hard-coded password table, no algorithmic password generator, and no reachable hidden/debug menu. The only in-scope "code-like" surfaces are (a) scripted **2-digit passcode doors** in the school network — story puzzles whose answers are environmental counts — and (b) **save-bit unlockables** (title star, four secret Navis), which are saves, not codes (guide §16.18).

Evidence, in brief:

* **Button codes.** The widely published title codes `L L R L R L R R` (BN2 Hard Mode) and, while holding Left, `R R L R L R L L` (BN3 extra stars) belong to the *sequels*, not BN1 (§16.11). Searched the ROM for both as active-high `u16` key masks, big-endian, and newest-first: **0 hits in every encoding**. No other code table was found. The only multi-button combo present is the documented **software reset** (`Start+Select+A+B`), a system function, not a cheat.
* **Passwords.** The game's text is *not ASCII*: it is font/tile-index encoded (documented table below). I decoded the entire ~0x69–0x74 text bank into 102,726 printable runs. Keyword census: `passcode` 88, `password` 1 (script line "It's password"), `cheat` **0**, `debug` **0**, `unlock` **0**, `menu` **0**, `invalid` **0**. Every "passcode" hit is the school-door puzzle or the WWW-server doors. There are 4 occurrences of the story value `9630` (NumberMan's scripted line), and no alphabetic code strings anywhere. A separate `strings -n 4` pass over the raw ROM produced 54,584 hits with **0** keyword matches (all apparent "password-like" runs are ADPCM audio sample data at 0xB0000–0x120000).
* **Debug material.** 3rd party cheat index lists BN1's development leftovers as build date, "Test message" (76 runs in the decoded bank, e.g. `0x6CBC84`), a demo "bonus dungeon" line (`0x7244C8` — decoded as `This is a bonus\ndungeon.` in the US build), and unused sprites/items — none of which is an input-reachable menu. A `PANEL RETURN !` debug string and its handler cluster exist in code (`0x0806199C` … `0x080619C0`) and are registered as scene-handler index 12 in a handler table at `0x08003240`, but no controller path reaches them and no source documents one. The one documented way to see the demo completion screen is a **Code Breaker memory patch** (`D0000020 0004`, `32006CB8 0010`), explicitly out of scope.
* **Screen walk.** Title, New Game, intro, field, and all eight Sub Screen entries (Folder, Library, MegaMan, Email, Items, Network, Save, Return) were walked with screenshots, and two savestates were diffed for RAM evidence. The only password UI is the passcode door, which is story-gated behind the school chapter; the Net and battle/custom screens are gated behind "do that after school!" (observed in-game) and link battles require a second console. Those gates, not a missing search, bound the negative.

Published sources checked: 3rd party cheat index cheats (live page + web.archive.org snapshot), 3rd party cheat indexes and its mirror, 3rd party cheat indexes, Japanese guides (3rd party cheat index code list), Nintendo's manual. No prompt-injection payload was encountered; all fetched text was treated as data.

## 3. How to reproduce

Emulator: `mgba -3` under `Xvfb :316 -screen 0 1024x768x24`, `DISPLAY=:316`, `SDL_AUDIODRIVER=dummy`, `openbox` as WM. The mGBA GDB stub (`-g`) and `-d` debugger both halt the core at reset on this build; RAM evidence therefore used **savestate diffs** (§16.13) with `Shift+F1…F9` to save and the `gbAs` PNG chunk decompressed (see `ssdiff.py`, §9). This is a harness detail, not a game finding.

Keymap (verified on the title screen — only `Return` starts the game; x/z/a/s/BackSpace do not):

| GBA | xdotool |
|---|---|
| A | `x` |
| B | `z` |
| L | `a` |
| R | `s` |
| Start | `Return` |
| Select | `BackSpace` |
| D-pad | arrow keys |

Hold keys 80–150 ms. The international title imposes a **~4–5 s delay** after boot before Start is accepted (3rd party cheat index notes the delay); pressing earlier appears to be ignored.

Exact path walked:

1. Boot → wait 5 s → `Return` → title menu `NEW GAME` (no Continue until a save exists).
2. `Return` → intro ("Lan, wak"). Advance with `x`; Start is **consumed while a dialogue box is open**. After the intro (~70 `x` presses), walk Right to the desk, press `x` repeatedly to take the PET ("Lan got an AI Navigation pro…", "Press START").
3. `Return` → Sub Screen: `Folder / Library / MegaMan / Email / Items / Network / Save / Return`. B exits; select each entry and screenshot. The Sub Screen is **gated until Lan takes his PET** — before that, Start does nothing (verified by screenshots and by RAM diffs).
4. `Network` → "You should save!" → Yes → overwrite → "Save complete!" → `Trade / Battle(test) / Battle(real!)`. `Battle(test)` reports "Neither player is read[y]" without a link partner.
5. Attempted jack-in at Lan's PC with R ("You want to jack in? Let's do that after school!") — **Net/story gate**, so no battle/custom screen reachable at this save point.
6. Codes tested: BN2 `L,L,R,L,R,L,R,R` and BN3 `R,R,L,R,L,R,L,L` (not applicable to this ROM — 0 literal hits); school passcodes verified as text, not entered because that screen is story-gated.

## 4. Address map

| Address (ROM unless noted) | Meaning |
|---|---|
| `0x0000` | Header; single embedded image; stock crt0 branch to `0x080000C0` |
| `0x1FBB4` | ASCII build stamp `ROCKMAN EXE 20010727` |
| `0x6199E` | Debug ASCII string `PANEL RETURN !` (embedded in a code/literal cluster) |
| `0x8003270` | Screen-handler table; entry 12 = Thumb pointer `0x08061931` (the debug cluster dispatcher) |
| `0x8061530` | Dispatcher: `ldrb r0,[r5,#8]`; `ldr r7,=0x08061544`; `bx r7` (4-entry handler table) |
| `0x8061544` | 4-entry Thumb handler table: `0x8061549`, `0x8061555`, `0x80615C9`, `0x80619B5` |
| `0x8061964`, `0x806197E` | Debug panel handlers; called only via the table at `0x8061958` / `0x8061544` |
| `0x8061992` | `ldr r0,=0x0806199C` → `bl 0x08003CC4` (draws `PANEL RETURN !`) |
| `0x6CBC84` | Encoded text `Test message` (76 such runs in the bank) |
| `0x7244C8` | Encoded text `This is a bonus\ndungeon.` (3rd party cheat indexes demo cut-off message, short in US build) |
| `0x70DBD1` | Encoded text `How many chairs are…` (source of door-1 answer 09) |
| `0x7113C4`, `0x71190C` | Encoded text `Input passcode?`, `Passcode accepted.` (4 near-identical door blocks at 0x711…, 0x712…, 0x71E…) |
| `0xD84E2`, `0x11D717`, `0x131E57`, `0x87393C0` | Encoded `9630` (NumberMan script line and data) |
| `0x02000480` (EWRAM) | RAM byte: `0x20` with Sub Screen open, `0x00` in field (savestate diff, §7) |
| `0x02006CB8` (EWRAM) | Address named by the out-of-scope Code Breaker demo-screen patch; the only ROM word referencing it is `0x0800046C` in the crt0 clear/copy table — not a code path |
| Save file | Battery-backed SRAM/Flash; no password save system |

Savestate layout used (mGBA `.ss1`, 397,312-byte decompressed `gbAs` chunk): header/CPU `0x0`, VRAM `0x1000`, IWRAM `0x19000`, EWRAM `0x21000` — consistent with guide §16.13.

Decoded-text font mapping (from the public `RockmanEXEZone/MMBN-Table-Files` `bn1-utf8.tbl`, verified against this ROM by decoding the 3rd party cheat indexes offsets): `0x00`=space, `0x01`–`0x0A`=`0`–`9`, `0x5E`=`-`, `0x5F`–`0x78`=`A`–`Z`, `0x79`–`0x92`=`a`–`z`, `0x93`=`.`; `0xE5 xx` = punctuation/symbol, `0xE8` = newline. This is why plain `strings` finds no game text.

## 5. Algorithm

There is no cheat validator to reimplement. The only algorithmic input surface is the scripted passcode door; its consumer is the game's text script, not a checksum routine. Its behaviour, from the decoded script blocks:

```
on_door_interact(door):
    if door.locked:
        show("Passcode required") ; show("Input passcode?")
        answer = door.answer              # 09 / 30 / 15, or runtime-random for doors 3,4,6,7
        read two digits from keypad
        if input == answer:
            show("Passcode accepted.") ; unlock
        else:
            show("N Passcode too low.") / ("N Passcode too high.")
            # a per-digit "verification error" message also exists (wrong-digit hint)
            # after too many misses on random doors, answer changes and the game says so
            # door 7 additionally requires the Teacher's Passcode item
```

This is a **script comparison**, not a code system: the answers are environmental counts (chairs = 9 → `09`, books = 30 → `30`, doors = 15 → `15`), the random doors are regenerated at runtime, and no value unlocks anything outside the story. The 4-digit `9630` is a *scripted line* NumberMan says while decoding the final door, not a player-entered code.

Button codes, had any existed, would be short arrays of active-high key masks compared against a key-history index (guide §5.4a). No such table, progress index, or action-dispatch chain was found; `KEYINPUT` (`0x04000130`) appears only as data words in graphics/audio tables (`0x81F8E8D` etc.), not in an input-validator literal pool.

## 6. Tables

**Published codes tested, with verification status**

| Claimed code | Source | Verification in this ROM |
|---|---|---|
| `L L R L R L R R` → Hard Mode | BN2 guides (3rd party cheat indexes) | **Not applicable.** 0 mask-sequence hits (u16LE/u16BE/reversed). This code belongs to BN2. |
| Hold Left, `R R L R L R L L` → extra stars | BN3 guides/answers | **Not applicable.** 0 mask-sequence hits. Belongs to BN3. |
| School doors: `09`, `30`, `15` | 3rd party cheat indexes | **Present as puzzle answers** in decoded text (`How many chairs…`, `Passcode accepted.` blocks). Not cheat codes. |
| Doors 3,4,6,7 "randomly generated"; door 7 needs Teacher's Passcode | 3rd party cheat indexes | Consistent with decoded script: repeated hint blocks and a "Passcode has been [changed]" message exist. Runtime-generated, not stored literals. |
| `9630` (NumberMan) | Game script / guide | 4 encoded occurrences in ROM text (`0xD84E2`, `0x11D717`, `0x131E57`, `0x87393C0`). Scripted NPC line, not entered by the player. |
| Start+Select+A+B → software reset | Nintendo manual | System combo; documented, not a cheat. |
| Demo completion screen (Code Breaker `D0000020 0004` / `32006CB8 0010`, press Select) | 3rd party cheat indexes | Exists as cut content; **out of scope** (memory edit, not developer-intended input). |
| `PANEL RETURN !` debug panel | ROM string | Code cluster present, registered as scene handler 12; no in-game entry path found. Label: Inferred dead/handler-only. |

**Search-space census**

| Space searched | Result |
|---|---|
| Embedded GBA headers (156-byte logo scan, 8 MiB) | 1 hit (`0x0`); no multi-game/trainer image |
| Raw ASCII `strings -n 4` | 54,584 strings; `password/cheat/debug/secret/unlock/menu/invalid/continue` → **0** |
| Decoded font-indexed text runs | 102,726 runs; `passcode` 88, `password` 1, `secret` 28, `star` 18, `9630` 4, `cheat` 0, `debug` 0, `unlock` 0, `menu` 0, `invalid` 0, `continue` 0 |
| Button-mask sequences (published codes, 3 encodings + newest-first) | 0 hits each |
| Hard-coded ASCII password/cheat tables | 0 (no equal-length NUL-padded code records outside audio data) |
| Debug gates | 1 code cluster (`0x8061530…0x80619C0`) with no reachable controller path |

## 6b. Enumeration

**Cheat-code space: empty (proven bounded negative).** The three code-system primitives — an input alphabet, a comparison table/validator, and a state write that unlocks content — were each searched and are absent for controller input. The enumeration deliverable is therefore the *bounded negative*, not a minted code.

**The one password surface (school passcode puzzle), fully characterised:**

* **Alphabet:** decimal digits `0`–`9` (font bytes `0x01`–`0x0A`); **length 2** for doors 1–7, **length 4** for the NumberMan door (`9630`). Representable space: **10² = 100** two-digit values, **10⁴ = 10,000** four-digit values.
* **Fixed answers:** door 1 `09`, door 2 `30`, door 5 `15` (published, and each is an environmental count). Doors 3, 4, 6, 7 are **runtime-random**; door 7 additionally requires the Teacher's Passcode. The published list therefore fixes 3 of 100 two-digit values; the other 97 are either unreachable (no door asks for them) or are generated per playthrough.
* **Validator model:** script `cmp` of the input digits against the door's stored answer; feedback strings `too low` / `too high` / per-digit `verification error` / `Improper input` / `Maximum input` / `Passcode accepted.` exist in the decoded bank at `0x711…`, `0x712…`, `0x71E…`. There is no checksum, no XOR key, no permutation table, and no unlock flag written by the validator other than opening the door (story progression).
* **Novel code:** **not applicable** — a "code that appears in no published list" requires a code system with a generator, and this game has none. The closest analogue is a random door's per-playthrough answer, which is by definition unpublished but is generated by the game, not minted from a reversed format. It was **not entered** because the passcode screen is story-gated (observed in-game: "Let's do that after school!"); per §16.10, the gate is reported rather than bypassed with a debugger.
* **Bounds by rejection:** the *format* bounds were proven statically (validator compares a 2-digit decimal input; a wrong digit yields the decoded rejection strings above; no other alphabet symbol is accepted by the input routine). An on-screen rejection test could not be performed without advancing the story to the school chapter; this limitation is stated explicitly rather than claimed as tested.

**Button-code space:** all two-sequel codes tested in three encodings → 0 hits; no progress-index/dispatch chain found; the only combo is the documented system reset. No undocumented combination exists to press because no validator exists.

**Debug menu space:** one handler cluster and one debug string; zero documented in-game triggers; the single documented reveal is a Code Breaker RAM patch (out of scope).

## 7. Validation evidence

* **Observed (emulator):** title `PRESS START` → `NEW GAME`; intro and PET acquisition; Sub Screen with all eight entries (screenshots `sub_open2_c.png`, `walk_montage.png`, `sub_*.png`); Network menu with `Trade / Battle(test) / Battle(real!)` and "Neither player is read[y]"; PC jack-in refused with "Let's do that after school!"; dialogue consuming Start until closed. Savestate diff of Sub Screen-open vs field: EWRAM `0x02000480` changes `0x20 → 0x00` (75 differing bytes total in EWRAM, `game.ss1` vs `game.ss2`).
* **Observed (static):** single header/stock entry; build stamp at `0x1FBB4`; decoded `Test message` at `0x6CBC84` and `This is a bonus\ndungeon.` at `0x7244C8` (independent confirmation of the 3rd party cheat indexes offsets, so the font table is correct); `PANEL RETURN !` at `0x6199E` loaded by `ldr r0,[pc,#28]` at `0x8061992`; handler pointer `0x08061931` at `0x8003270`.
* **Derived:** BN2/BN3 button codes absent in all searched encodings; keyword census over 102,726 decoded runs; 0 ASCII keyword hits over 54,584 strings; Sub Screen gated on PET pickup (Start ineffective before, effective after).
* **Inferred:** the `0x8061530…0x80619C0` cluster is a development/debug panel — it is wired as scene handler 12 and prints a debug label, but no reachable controller path was identified. The demo completion screen is cut content reachable only by memory edit.

## 8. Unknowns

* Battle, Custom Screen, and pause-menu screens were not walked: the Net is story-gated ("after school") and link battles need a second GBA. This does not affect the code-system conclusion (no code surface lives on those screens in any published description), but it is a stated coverage limit.
* Whether scene-handler index 12 (the `PANEL RETURN !` cluster) has any in-game trigger was not proven either way; no trigger is documented in 3rd party cheat indexes, and no BL/xref from gameplay code was found. It is reported as Inferred dead/handler-only.
* The school passcode screen was not reached in-game; its rejection behaviour is derived from decoded script strings, not observed. The puzzle's random-door RNG and the exact per-digit "verification error" rule were not reversed because they are story logic, not a cheat system.
* The guide's general lesson about "no system" bounds applies here: the negative is proven for the searched spaces (screens reached, decoded text bank, button encodings, ASCII strings), not for hypothetical story content beyond the first chapter.

## 9. Tooling

* `decode_text.py` — implements the BN1 font mapping; decoded 102,726 runs into `decoded_text.txt` and produced the keyword census.
* `scan.py` — direct-word, Thumb-LDR-literal, and button-mask encodings scans (BN2/BN3 sequences, software reset).
* `ssdiff.py` — parses mGBA `.ss1` PNG `gbAs` zlib chunk and diffs EWRAM/IWRAM/header for RAM evidence (guide §16.13).
* `arm-none-eabi-objdump -M force-thumb` for the `0x8061530…0x80619C0` cluster and `0x80034A4` dispatcher.
* `xdotool` driver `k.py` (80–150 ms holds); `scrot` + ImageMagick crops; screenshots retained under `/tmp/mmbn1/`.
* Public font table: `RockmanEXEZone/MMBN-Table-Files` `done/bn1-utf8.tbl` (fetched as data and validated against 3rd party cheat indexes offsets in this ROM).
* Environment installed/used: system `binutils-arm-none-eabi`, `mgba`, `xvfb`, `openbox`, `xdotool`, `scrot`, `imagemagick`, Python 3 + `capstone`/`keystone` (already present; nothing non-obvious added).

## 10. Legal note

No ROM image or copyrighted asset is redistributed here. Only hashes, addresses, algorithms, search counts, and original observations are published.
