# Tak and the Power of Juju (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Tak and the Power of Juju.gba` |
| Size | 8,388,608 bytes (`0x800000`) |
| Header title | `TAK&JUJUENG` |
| Game code | `BJUE` |
| Maker code | `78` (THQ) |
| Version | `0x00` |
| Fixed byte / complement / checksum | `0x96` / `0x9E` / `0x0000` |
| Entry word | `0xEA00002E` (standard `b 0x080000C0`) |
| MD5 | `438be22c9e03529e2a03779a00d17b62` |
| SHA-1 | `6d34590d88c541650a7bd2e17a338de82c5e84cb` |
| SHA-256 | `b1dea3c30fd2d2d3c9602eeb0b7b9b60e313707084a8ce667d52f11c94fac6bb` |

The header checksum is `0x0000`, a common rebuilt-header artifact (guide §16.1).
The widely published cheats for this title are PS2/GameCube button sequences, not
GBA codes (§16.11); no GBA password list exists in four web searches.

## 2. Executive summary

The ROM contains a complete **password UI string set** — a `Password` menu item, a
`Level Password` screen with the prompt `Press A to add a letter, B to erase`, and
the result messages `Password accepted` / `Invalid password`. This pass recovered
the game's **text-rendering system exactly** (§4/§5), enumerated **all 20 call sites**
of the text renderer, mapped every reachable screen to the text IDs it draws, and
showed that **none of the password text IDs is ever supplied to the renderer by any
reachable screen**. The password screen is therefore a **dead/gated UI in this GBA
build**: the strings survive in the text bank, but the screen-state handler that
would consume them is not reachable from any retail input path.

Consequently **no validator, input buffer, alphabet, checksum or accepted table was
isolated, and no code was minted or entered**. This is not a harness failure: §6b/§8
give the byte-level gate, the exact renderer call-site inventory, the reachable
screen enumeration and the bounded negative over the searched spaces. The prior
report's claim that UI text is "a 16-bit offset bank at base `0x47E000` with a
400-entry table at `0x294398`" is **corrected** here (§4).

## 3. How to reproduce

* Emulator: mGBA 0.10.5, Xvfb `:319`, openbox, `SDL_AUDIODRIVER=dummy`, `-3` scale.
* Keymap verified by observation: `A = x`, `B = z`, `Start = Return`, `Select =
  BackSpace`, `L = a`, `R = s`, D-pad = arrow keys.
* Boot sequence (observed, ~86 s): THQ Presents (0 s) → story text pages (2–48 s) →
  blank starfield (50–52 s) → jungle demo (54–70 s; Nick/Helixe logos at 66–70 s) →
  **title screen** `PRESS START` (78–86 s). Pressing `A` repeatedly at the story
  skips directly to gameplay.
* Reachable screens (all confirmed by screenshot + GDB breakpoint trace):
  1. **Title** `PRESS START` — reached by `Start` from gameplay.
  2. **Save-slot / NEW GAME** screen — `Start` at title; Tak is the cursor;
     `Left`/`Right` moves between "NEW GAME" and three tombstone slots. With no save
     it shows `NEW GAME` and `empty`; with a save it shows CONTINUE / COPY / ERASE
     (text IDs 6/7/8).
  3. **Gameplay** — `A` on "NEW GAME" or on a save slot.
  4. **Pause menu** `Continue` / `Quit` (text IDs 26/27) — `Start` during gameplay;
     `B` closes it. `A` on `Quit` → confirmation `Are you sure / you want to quit? /
     Yes / No` (IDs 28–31).
  None of these screens is the `Level Password` screen.
* Debugger: mGBA GDB stub (`-g`, port 2345) driven by a hand-written Python GDB
  remote client (`/tmp/takjuju2/gdbclient.py`, `gdb_ctrl.py`). The GDB stub
  halts on connect, so the controller holds one socket open and uses `send_only('c')`
  plus raw `0x03` to run/interrupt without dropping the session. `Z0,80109c8,2` sets
  a Thumb breakpoint at the text renderer; each stop is read with `g` and `r0` (the
  text ID) logged. mGBA's CLI debugger (`-d`) was also used through a FIFO/pipe
  controller; it processes commands only when the core is halted.
* Savestates: mGBA `.ss1`–`.ss8`; the `gbAs` PNG chunk is zlib-decompressed to a
  397,312-byte raw state with IWRAM at raw `0x19000` and EWRAM at raw `0x21000`
  (`/tmp/takjuju2/ssdecode.py`).

## 4. Address map

| ROM file offset | ROM address | Meaning |
|---:|---:|---|
| `0x47EB2C`–`0x47F…` | `0x0847EB2C`– | Plaintext text bank (all menu/dialogue strings) |
| `0x47E9E0` | `0x0847E9E0` | **Language-0 text-ID → u16 offset table** (verified: id 14→`0x08B`, 33→`0x136`, 36→`0x15D`, 39→`0x181`, 40→`0x18A`, 42→`0x194`, 43→`0x19C`) |
| `0x47EB28` | `0x0847EB28` | **Language-0 text bank base**; final string address = `base + offsets[id]` |
| `0x482D40` | `0x08482D40` | Language table: `lang[0] = {ptr 0x0847E9E0, ptr 0x0847EB28}`; langs 1–3 point to other banks |
| `0x109C8` | `0x080109C8` | **Text renderer**: `char* lookup(u32 text_id)` — reads language byte at `0x02082138`, indexes `0x08482D40`, returns `bank + offsets[id]` |
| `0x109EC` | `0x080109EC` | Companion renderer returning a second value |
| `0x2D998` | `0x0802D998` | Keypad reader: reads `KEYINPUT` (`0x04000130`), maps 10 keys to internal indices 1–10, dispatches to `0x0802D818` |
| `0x2D818` | `0x0802D818` | Key-event dispatcher; writes pressed/held state into IWRAM/EWRAM |
| `0x47EB3F` | `0x0847EB3F` | `"Main Menu"` |
| `0x47EBB3` | `0x0847EBB3` | `"Password"` (menu item, text ID 14) |
| `0x47EC5E` | `0x0847EC5E` | `"Level Password"` (text ID 33) |
| `0x47EC85` | `0x0847EC85` | `"Press A to add a"` (text ID 36), `0x47EC96` "letter, B to" (37), `0x47ECA3` "erase" (38) |
| `0x47ECA9`/`0x47ECB2` | `0x0847ECA9`/`0x0847ECB2` | `"Password"` (39) / `"accepted"` (40) |
| `0x47ECBC`/`0x47ECC4` | `0x0847ECBC`/`0x0847ECC4` | `"Invalid"` (42) / `"password"` (43) |
| `0x3DF0C`–`0x3E2CC` | `0x083DF0C`–`0x083E2CC` | Level-name bank: 13 cinematic/special + 38 named levels + `demo_level`/`empty` |
| `0x482BD4`–`0x482D3C` | `0x08482BD4`– | 15 level-info records, 24-byte stride `{u32 0x00020xFF, ptr, ptr, name_ptr, id, 0}` |
| `0x482E60` | `0x08482E60` | Reachable save-slot menu text-ID array `[6,7,8]` (CONTINUE/COPY/ERASE) |
| `0x294398`, `0x2FB2CC`, `0x3D5958` | `0x08…` | **Word-wrap/substring offset tables**, NOT string-ID tables (see §9 correction) |

### Correction to the prior report

The prior report treated `0x294398` as a "400-entry text-ID table, base `0x47E000`".
That reading is wrong. Its entries (`1,9,0x12,0x1b,…` then `0xC85,0xC89,0xC8F,…`)
are offsets **4–9 bytes apart**, i.e. starts of overlapping *word fragments* used for
line wrapping: `0xC85`→`"Press A to add a"`, `0xC89`→`"A to add a"`, `0xC8F`→`" add
a"`. The real string lookup is the `0x080109C8` routine with a **u16** offset table
at `0x47E9E0` and bank base `0x47EB28`. This is why pointer scans missed it: there
is no direct `u32` pointer to any string anywhere in the ROM (0 hits for all five
password strings), and no `u32` pointer to any address in `0x0847E000`–`0x08480000`
except graphics/font structures.

## 5. Algorithm (of the graphics *text system*, not a password validator)

```
char* text_lookup(u32 id):                    # 0x080109C8
    lang = byte[0x02082138]                   # current language index
    entry = u32[0x08482D40 + 4*lang]           # -> {u16* offsets, char* bank}
    offsets = u32[entry]
    bank    = u32[entry+4]
    return bank + u16[offsets + 2*id]
```

Verified against the ROM bytes: language 0's entry is `0x0848069C`, whose struct is
`{0x0847E9E0, 0x0847EB28}`; `id=14` resolves to `"Password"`, `id=33` to
`"Level Password"`, `id=42` to `"Invalid"`. No password validator algorithm can be
given because no routine consumes those IDs (§2, §6b).

## 6. Tables

Password UI text IDs (language 0):

| ID | String | ROM address |
|---:|---|---|
| 14 | `Password` (menu item) | `0x0847EBB3` |
| 33 | `Level Password` | `0x0847EC5E` |
| 36 | `Press A to add a` | `0x0847EC85` |
| 37 | `letter, B to` | `0x0847EC96` |
| 38 | `erase` | `0x0847ECA3` |
| 39 | `Password` | `0x0847ECA9` |
| 40 | `accepted` | `0x0847ECB2` |
| 42 | `Invalid` | `0x0847ECBC` |
| 43 | `password` | `0x0847ECC4` |

Reachable menu text IDs (GDB breakpoint trace + screenshots): `5` (NEW GAME),
`6` (CONTINUE), `7` (COPY), `8` (ERASE), `26` (Continue), `27` (Quit), `28`–`31`
(quit confirmation), `3`, `13`, `32`. **None of 14/33/36–43 is in this set.**

## 6b. Enumeration

### Code-space definition

Because no validator was isolated, the representable password space cannot be
stated. No alphabet, length, checksum, accepted table or generator exists in the
analysed code. No novel code was generated, entered or RAM-verified, and no in-game
rejection of an out-of-range value was observed. §0.2 cannot be satisfied for this
target; the following is the **bounded negative with the exact gate**, per §0.2
item 5 and §16.3 category 4.

### The gate, at byte level

1. **All renderer call sites enumerated.** A raw Thumb `BL` scan over all 8,388,608
   bytes found exactly **20** calls to `0x080109C8`:
   `0x800DA54, 0x800DB06, 0x800DDDA, 0x800FF12, 0x800FF36, 0x801003C, 0x80103BE,
   0x8015D92, 0x8015DD6, 0x8015E28, 0x8015EB4, 0x8015F10, 0x8015F5E, 0x80186AA,
   0x80186CE, 0x8018744, 0x801876E, 0x801878C, 0x80187AA, 0x8023FBE`.
   Disassembling each shows the text ID loaded as an **immediate**:
   `3, 5, 13, 26, 27, 28, 29, 30, 31, 32` — plus data-driven loads from structs.
   **No call site loads 14, 33, 36, 37, 38, 39, 40, 42 or 43.**
2. **Every data-driven text-ID array found holds only reachable IDs.** The save-slot
   menu array at `0x08482E60` is bytes `[6,7,8]`; nearby arrays at `0x08482E40`
   hold `[9,10,1,2,11,12,1,2,6,7,8]`. A whole-ROM search for a `u32` array
   containing 14/33/36–43 adjacent to each other returned **0** tables (all hits
   were graphics data).
3. **Runtime confirmation.** With a Thumb breakpoint on the renderer and GDB
   logging `r0` at every hit, navigating all reachable screens produced only IDs
   `6, 7, 8` (save-slot menu) and `26, 27, 28–31` (pause/quit). The `Level Password`
   screen was never drawn.
4. **Physical input enumeration.** Every button at the save-slot screen (`A, B, L,
   R, Select, Up, Down, Left, Right, Start`) was tested with screenshots
   (`contact_keys.png`); at the title screen `A` and `Start` were confirmed, and a
   second full button sweep was attempted (its screen state was not re-confirmed,
   so it is not counted as proof). The confirmed transitions are title ↔ gameplay,
   gameplay → save-slot, save-slot → gameplay, and gameplay → pause →
   quit-confirmation.
   Published button cheats (3rd party cheat indexes PS2/GBA sequences) and `L+R+Start` were also
   tried and produced no menu change.
5. **No table to mint from.** No plaintext password table, no custom password
   alphabet, no checksum constant and no level-code record exists in the image
   (search counts below). The 15 level-info records carry `id` fields
   `7,9,13,14,5,9,17,9,2,3,9,12,0,22,2` with no password/checksum field.

Therefore the exact gate is: *the password UI strings are present in the language-0
text bank, but no screen-state handler in this build ever supplies their text IDs to
the renderer, and no retail button path reaches such a handler.* The `Password`
feature is dead/gated content. A future analyst could revisit a different regional
build or a prototype where the handler exists.

### Search ledger

| Search | Space checked | Result |
|---|---|---|
| Published codes (web) | 4 searches + 3rd party cheat indexes GBA cheats page + 3rd party cheat indexes/NEO walker | **0** GBA password codes; all published cheats are console button sequences |
| `strings -t x -n 4` | whole 8,388,608-byte ROM | 76,317 strings; password-related hits: **7** |
| Custom 26-letter alphabet | every byte of all 8,388,608 bytes | **3** hits, all standard C-library tables at `0x7A0FF`, `0x7B1FF`, `0x7C0E1` |
| Direct `u32` pointer to any of 5 password strings | whole ROM | **0** hits |
| `u32` pointer into `0x0847E000`–`0x08480000` | whole ROM | **0** string pointers; only font/graphics structures |
| Thumb `BL` to text renderer `0x080109C8` | whole ROM, every 2 bytes | **20** sites; IDs used: `3,5,13,26,27,28–31,32` + data-driven; **0** password IDs |
| Runtime renderer breakpoint | all reachable screens (GDB) | IDs `6,7,8,26,27,28–31`; **0** password IDs |
| Password text-ID arrays (`u16`/`u32`) | whole ROM | **0** tables containing 14/33/36–43 |
| Screens walked | boot story, THQ/Nick/Helixe logos, title, save-slot, gameplay, pause, quit-confirmation | **7** screen types; `Level Password` **not reached** |
| Level-name bank | `0x3DF0C`–`0x3E2CC` | 13 special + 38 named levels + `demo_level`/`empty` |
| Level-info records | `0x482BD4`–`0x482D3C` | **15** records, 24-byte stride; no password/checksum field |

## 7. Validation evidence

* **Observed:** ROM hashes/header (§1); all strings, tables and IDs (§4/§6); seven
  screen types across repeated boot cycles and every button at title/save-slot;
  GDB-stub register and memory reads; GDB breakpoint log of renderer text IDs;
  savestate RAM diffs (`.ss1`–`.ss8`, decoded to 397,312-byte raw states).
* **Derived:** text-lookup algorithm and language table (§5) from the instruction
  sequence at `0x080109C8` plus byte dumps; the 20 renderer call sites from a full
  Thumb `BL` scan verified with `objdump -M force-thumb`; the correction of the
  `0x294398` table from its 4–9-byte fragment offsets and the actual string bytes.
* **Inferred:** that the Password screen is deliberately gated/dead code rather than
  accidentally deleted — the strings, text IDs and offset-table entries all survive
  intact, but no renderer call supplies them. This is a bounded negative over the
  code and input spaces listed in §6b, not a claim about all possible builds.

## 8. Unknowns

* Whether any non-retail build of this title exposes a working `Level Password`
  screen and validator.
* The semantic meaning of the `id` fields in the 15 level-info records.
* No validator, input buffer, alphabet, checksum, accepted table, novel code,
  rejection-bound test or in-code RAM effect was produced — see §6b for the exact
  gate and the bounded negative.

## 9. Tooling

* `strings -t x -n 4`, `xxd`, `grep -abo`, `arm-none-eabi-objdump -M force-thumb`,
  Python 3 + struct, Capstone, REA/Ghidra (`open_binary`, `search_strings`, `xrefs`,
  `procedure_pseudo_code`, `procedure_callers`).
* mGBA 0.10.5 with Xvfb `:319` + openbox, `SDL_AUDIODRIVER=dummy`, `-3` scale.
* GDB-stub tooling written in this engagement (all under `/tmp/takjuju2/`):
  `gdbclient.py` (minimal GDB remote protocol client: `m`/`M`/`g`/`Z0`/`c`/raw-`0x03`),
  `gdb_ctrl.py` (persistent file-driven controller), `gdb_session.py`,
  `trace_text.py`, `ssdecode.py` (zlib `gbAs` savestate decoder), `capture_loop.py`,
  `dcmd.sh`. Screenshots: `contact.png`, `contact_tr.png`, `slots_explore.png`,
  `title_keys.png`, `pm_keys.png`, `states_check2.png`, etc.
* Web recon via `websearch`/`webfetch` (3rd party cheat index cheats/walkthrough returned 403;
  3rd party cheat indexes/NEO searches yielded console button sequences only).

## 10. Legal note

No ROM bytes, extracted graphics, music or game text are redistributed here. Only
hashes, file offsets, addresses, algorithms and findings are published.

## 11. Cleanup

All processes started for this engagement were stopped by numeric PID (never
`pkill -f` on the target name): mGBA `-g` (PID 467586), its GDB controller
(467584), earlier mGBA/CLI-debugger instances (452119, 452214/452215, 452502,
453558, 453797, 453883, 454054/454052, 456400, 460055, 460613, 462144, 462702,
466066, 467586), Xvfb `:319` (449370) and openbox (449382). Every generated
`.sav`, `.ss1`–`.ss8` and `.ss*.raw` file was removed from the ROM folder; only
`Tak and the Power of Juju.gba` and this report remain there. Processes owned by
other analysts (TMNT, Tekken Advance, Terminator 3) were left untouched.
