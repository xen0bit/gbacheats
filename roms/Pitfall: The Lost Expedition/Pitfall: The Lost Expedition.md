# Pitfall: The Lost Expedition (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Pitfall: The Lost Expedition/Pitfall: The Lost Expedition.gba` |
| Size | 8,388,608 bytes (0x00800000, 8 MiB) |
| `file` identification | Game Boy Advance ROM image: "PITFALL" (BPHE52, Rev.00) |
| Header title | `PITFALL` |
| Game code | `BPHE` |
| Maker code | `52` |
| Fixed byte (0xB2) | `0x96` (valid) |
| Software version | `0x00` |
| Complement check (0xBD) | `0xBF`; header checksum (0xBE) = `0x0000` (nonstandard but retail-typical; not a rebuild indicator here) |
| Entry word | `0xEA000030` → target `0x080000C8` — **stock crt0 branch**, not the `0xEA00002E` scene cracktro signature |
| Embedded GBA headers (Nintendo logo scan) | **1** (at file 0x0); no second image, no appended trainer |
| MD5 | `e1b65755d37a64d3ab7605d5dac86b56` |
| SHA-1 | `edb205a04e694786f8159ac99fb4bfd72e34e4e3` |
| SHA-256 | `36e5243a4852542b78acbc1f3d592d3b792c6b328ff19f6e57aff5d4c8382e2f` |

No patch/trainer detected: entry branch is stock, a single Nintendo logo exists, and debug strings are compiled into the retail image itself.

## 2. Executive summary

The game has **one** developer-intended cheat system: a single 6-press title-screen button code that unlocks a **Special** menu under Options. The published code is correct and was verified in ROM, in RAM, and in the emulator:

> At the "PRESS START" title screen press **B, A, Down, Left, A, Down**. "PRESS START" flashes green, and Options → Special becomes selectable.

The ROM stores the code as six active-high 16-bit keypad masks at `0x080B60F4`, terminated by `0xFFFF`. Exactly one code is registered (RAM count verified = 1). The matcher at `0x0809E74C` compares the **last N entries of a 32-slot ring buffer of newly-pressed key masks** against the stored sequence. The unlocked menu exposes four entries: three toggles (**All Heroic Abilities**, **Unlimited Health**, **Unlimited Ammo**) and a **Start Level** selector (7 worlds × 5 levels = 35 entries). The unlock is **RAM-only** — it resets on power cycle; the 512-byte `.sav` holds settings, not the cheat flag.

The ROM also contains a complete unused **Pitfall Debug Screen** (strings at `0x080B46A4`–`0x080B48F0`, renderer at `0x08069DF8`, "Entity Options:" renderer at `0x0809DA18`). It has **zero BL/pointer xrefs**, no UI entry, and no input path; it is classified as dead developer code, not a reachable hidden menu.

Console (GC/PS2/Xbox) button codes published for the same title are a *different SKU* and do not apply. CodeBreaker/GameShark codes are memory edits and out of scope.

## 3. How to reproduce

* Emulator: mGBA (system binary), `DISPLAY=:319`, `SDL_AUDIODRIVER=dummy`, 3× scale.
* Keymap (mGBA SDL default): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows. Hold each key 100–200 ms.
* Boot sequence: legal screen (~4 s) → black → Activision logo → Torus Games logo → **PITFALL / PRESS START** (~14 s after launch). The title then times out into a demo; enter the code before that.
* **Harness caveat (guide §16.2):** the first key edge after the title screen is detected can be dropped. Send a harmless dummy press (Select) first, or send the six-press code twice. With that prefix, the unlock is 100% reproducible.
* Menu path after unlock: Start → Options (cursor: Music → Sound → **Special**, now gold) → A.
  * Special grid: `All Heroic Abilities | Unlimited Health` (top row), `Start Level | Unlimited Ammo` (bottom row). D-pad moves between cells, A toggles / enters.
  * Toggling any item flips its red ✗ to a green ✓.
  * Start Level → two independent selectors: left = world name, right = Level 1–5.
* Pause (in gameplay): Start → Continue / Quit / Music / Sound; Quit → "ARE YOU SURE?" Yes/No.
* Rejection tests: any wrong sixth button, `Up,Up,Down,Down`, and `B,A,Down,A,Select,Select` all leave Special grey.

## 4. Address map

| Item | Address | Type / evidence |
|---|---|---|
| Cheat button-code table (1 record) | ROM `0x080B60F4` (file `0x0B60F4`) | `00 00 02 00 01 00 80 00 20 00 01 00 80 00 FF FF` = `{start:0, B, A, Down, Left, A, Down, END}` — **Observed** (literal search, unique hit) |
| Registration call | ROM `0x08080CCA` | `ldr r1,[pc,#0x80]` loads `0x080B60F4`; `bl 0x0809E704` — **Derived** |
| Register function | ROM `0x0809E704`–`0x0809E744` | Writes one 12-byte entry `{u16 first, u32 mask_ptr, u16 len}`; literal `0x0000FFFF` at `0x0809E748` is the terminator |
| Matcher / ring-buffer writer | ROM `0x0809E74C`–`0x0809E8A0` | Appends pressed mask to ring, then compares last `len` entries backwards — **Derived** + observed via read watchpoint |
| Match side-effect | ROM `0x0809E8A4` | Called on full match; sets the unlock/cheat state |
| Input state base | RAM `0x03000268` | `+6` = held (active-high), `+8` = newly pressed (edge) |
| Input update | ROM `0x0809BE00` | `held = 0x3FF ^ KEYINPUT`; `pressed = held & ~prev`; stores at `0x0300026E/70` |
| Cheat system object | RAM `0x0200C3A0` | `+0x24` = registered count (observed **1**), `+0x28` = entries pointer (`0x02013134` at first boot), `+0x2C` = ring index, `+0x30` = `u16 ring[32]` |
| Debug screen renderer | ROM `0x08069DF8` | Draws "Pitfall Debug Screen" / "Built: Nov 18 2003"; **no xrefs** |
| Debug menu builder | ROM `0x08069E28`, `0x08069E80` | 3-item root menu + 6-item submenu with jump table at `0x08069EA4` |
| Entity-options renderer | ROM `0x0809DA18` | "Entity Options:" / "Flag for deletion" |
| Level/world names | tile-indexed text bank | No ASCII `strings` hit for Keylands/Marshlands/Snow; enumerated visually/OCR instead |

## 5. Algorithm

```
# registration (once, at title-screen state construction)
register(cheat_obj, table):
    first = table[0]                 # 0x0000 = no held-key requirement
    ptr   = &table[1]                # first real mask
    len   = count of u16 until terminator 0xFFFF
    entries[count++] = {first, ptr, len}

# every frame (matcher)
held, pressed = read_keyinput()
if pressed == 0: return               # no update, no match attempt
ring[idx] = pressed                   # 32-entry u16 ring
idx = (idx + 1) & 0x1F
for each entry e:
    if e.first != 0 and (held & e.first) != e.first: continue
    ok = true
    for k in 0 .. e.len-1:
        if ring[(idx - 1 - k) & 0x1F] != e.ptr[k]: ok = false; break
    if ok: unlock_cheat_menu()        # call 0x0809E8A4
```

Key semantics: **edge-triggered, newest-last ring match**; the mask array is compared **backwards**, so the sequence must be the final `len` presses in order. Extra presses after the code do not invalidate it if they are not yet in the last 6 slots, but any differing press among the last 6 rejects it.

Unpacking of the one record:

```
first = 0x0000
masks = [0x0002, 0x0001, 0x0080, 0x0020, 0x0001, 0x0080]
      = [B,      A,      Down,   Left,   A,      Down]
len   = 6
```

## 6. Tables

**Button-mask alphabet (active-high GBA keypad bits):**

| Button | Mask | Button | Mask |
|---|---:|---|---:|
| A | 0x001 | Right | 0x010 |
| B | 0x002 | Left | 0x020 |
| Select | 0x004 | Up | 0x040 |
| Start | 0x008 | Down | 0x080 |
| R | 0x100 | L | 0x200 |

**Registered cheat codes (complete set = 1):**

| # | Sequence | Effect | Published? |
|---|---|---|---|
| 1 | B, A, Down, Left, A, Down | Unlock Options → Special | Yes (GameFAQs/Project Cheat Codes) |

**Candidate arrays present in ROM but NOT registered (rejected in emulator):**

| ROM | Sequence | Result |
|---|---|---|
| `0x080B60E8` | Up, Up, Down, Down | locked (rejected) |
| `0x080B6104` | B, A, Down, A, Select, Select | locked (rejected) |

**Special menu (unlocked):**

| Entry | Effect | Default |
|---|---|---|
| All Heroic Abilities | toggles heroic abilities | ✗ off |
| Unlimited Health | toggles health | ✗ off |
| Unlimited Ammo | toggles ammo | ✗ off |
| Start Level | level select | — |

**Level select worlds (7, OCR-derived; one label low confidence):**
Keylands, El Dorado, *"Marklands"/"Barklands" (OCR ambiguous)*, Marshlands, Snow, Cavern, Amazon — wrapping after 7. Levels per world: **1–5** (confirmed by watching the selector wrap 5→1). Total 35 selectable entries.

## 6b. Enumeration

**Space definition.** The button-code space is defined by the register call site and the ROM record, not by guessing:

* Registered-code count = **1** (read from RAM `0x0200C3A0+0x24` in GDB = `0x00000001`).
* Only **one** call site of the register function `0x0809E704` exists in the whole ROM (`0x08080CCA`).
* The single record has `len = 6`, alphabet = the 10 keypad bits above, terminator `0xFFFF`.
* Reachable input space therefore = exactly one 6-press sequence; there is no checksum, no variable length, and no second algorithmic code format.
* Action branches: the Special menu has exactly 4 entries (3 toggles + Start Level). All 4 were walked and exercised. Level select enumerates 7 worlds × 5 levels = 35 entries.

**Published-code verification.** Played `B,A,Down,Left,A,Down` on the title screen → "PRESS START" flashes green, Options → Special changes from grey to gold, and all three toggle tiles flip from red ✗ to green ✓ when selected. ROM literal search for the six masks is unique at `0x080B60F4`. This matches the GameFAQs GBA entry exactly.

**Undocumented combinations pressed (the button-code equivalent of a novel code):**

| Input | Result | Evidence |
|---|---|---|
| `Up,Up,Down,Down` (undocumented array in ROM) | Special remained **grey** | screenshot + grey-pixel detector |
| `B,A,Down,A,Select,Select` (undocumented array in ROM) | Special remained **grey** | screenshot + grey-pixel detector |
| `B,A,Down,Left,A,UP` (one wrong button) | Special remained **grey** | screenshot + grey-pixel detector |
| `B,A,Down,Left,A,Down` (published) | Special became **gold**, menu functional | screenshot + grey-pixel detector (0 grey pixels in Special button region vs 7254 when locked) |

Because the only accepted value is the published one, no unpublished *accepted* code exists to mint; the §0.2 button-code requirement is satisfied by enumerating every action branch and pressing the undocumented combinations, both of which were rejected.

**RAM proof of matcher state.** GDB at the registration breakpoint: `OBJ=0x0200C3A0`, `[OBJ+0x24]=0x00000001`, `[OBJ+0x28]=0x02013134`. Savestate diff right after a code attempt whose first edge was dropped showed the ring buffer at EWRAM `0x0200C3D0` containing `0001 0080 0020 0001 0080` = `A,Down,Left,A,Down` with ring index `5` — direct evidence that the game records edge-pressed masks into a 32-slot ring and that the leading B was lost by the harness. With the dummy prefix, all six presses are present and the code matches.

## 7. Validation evidence

* **Observed** — title/legal/intro/main menu/Options/Special/level-select/pause/quit-confirm screens walked on mGBA with screenshots; public code unlocks Special; three toggles flip ✗→✓; world cycle and level 1–5 wrap; wrong and undocumented codes rejected; save file (`Pitfall: The Lost Expedition.sav`, 512 B) exists but cheat unlock does not survive a power cycle; L+R+Start on title leads to the *normal* main menu.
* **Derived** — code table, registration function, matcher, ring-buffer semantics, and input-state addresses from disassembly (Capstone) and literal/xref scans; the "first press dropped" explanation from savestate RAM contents.
* **Inferred** — exact semantic meanings of the EWRAM bytes that change when a toggle is flipped (savestate diffs showed candidate fields at `0x030002C4` and `0x0200C058/0x0200C05A`, but a second-toggle diff did not isolate a clean bit mapping); the low-confidence world name from OCR.

**Hidden debug screen — bounded negative.** Strings `Pitfall Debug Screen`, `Built: Nov 18 2003`, `Main Menu`, `Profiling`, `Slow RAM Usage`, `Profile Menu`, `Disable`, `Enable`, `Profile Information`, and `Entity Options:` exist in the image (e.g. `0x080B46A4`, `0x080B46BC`, `0x080B4720`, `0x0807E8864`). The renderer at `0x08069DF8` has **no** Thumb BL caller and **no** 32-bit pointer (any alignment, with or without Thumb bit) anywhere in the 8 MiB; the menu builders at `0x08069E28`/`0x08069E80` show a 3-item root and 6-item submenu but are likewise unreferenced. No menu screen walked (title, main, Options, Special, level select, pause) offers a debug entry, and the only input matcher is the single 6-button code. L+R+Start on the title screen produced the ordinary menu. Conclusion: **dead developer code (guide §16.3, category 2)**, not a reachable hidden menu. This is a bounded statement about BL/pointer xrefs, the registered-code count, and every screen walked.

**Published codes checked for other SKUs.** GC/PS2/Xbox codes (hold L+R then button sequences: Bottomless Canteen, Classic Pitfall, Hyper Punch, Play as Nicole, Pitfall II, etc.) appear on GameFAQs/IGN/TCRF-style lists but belong to the console SKU and are not present as code tables in this GBA image. The GBA-specific published code is the one verified above. The five libretro CodeBreaker codes from ROMSFUN are memory-edit cheats and are out of scope.

## 8. Unknowns

* One of the seven level-select world labels is OCR-ambiguous (`Marklands`/`Barklands`); the count of 7 was established by observing wrap-around, but that single label is not certain.
* The precise RAM word/bit layout of the three cheat toggles was not isolated: savestate diffs contain many frame-dependent changes and a clean toggle→bit mapping was not proven. The toggles' *effects* were observed visually, not tied to a proven flag address.
* Whether the dead debug screen was ever reachable in an earlier/prototype build is unknown; only this retail image (hash above) was analyzed.
* "PRESS START turns green" was reported by the published guide and implied by the unlock, but no green-text frame was captured in the screenshot burst (the text blinks); the authoritative proof used here is the Special button state.

## 9. Tooling

* `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings` — Phase 0/1 fingerprinting.
* `capstone` 5.0.7 (`/tmp/opencode/pitfall/dis.py`) — raw Thumb disassembly at chosen ROM addresses; raw BL/xref scanners (`xrefs.py`, `find_debug.py`, `find_code.py`).
* `gdb-multiarch` with mGBA `-g` stub — breakpoint at `0x0809E704`, register/RAM reads, hardware read watchpoint that located the matcher at `0x0809E798`.
* Savestate parser (`/tmp/opencode/pitfall/state.py`) — decompresses mGBA PNG `gbAs` zlib chunk (397,312-byte state; IWRAM at `0x19000`, EWRAM at `0x21000`) for RAM diffing.
* `xdotool` + `scrot` + ImageMagick on `Xvfb :319` with `openbox`; `SDL_AUDIODRIVER=dummy`.
* `tesseract` for the tile-indexed level-select labels; pixel-count detectors in `try_code.py`/`reject.py` for locked-vs-unlocked state.
* Helper scripts: `ctl.py`, `enter_code.py`, `unlock.py`, `reject.py`, `enum_levels.py`, `codes_block.py`, `phase0.py`.

All analysis artifacts live in `/tmp/opencode/pitfall/`. No ROM or copyrighted assets are redistributed by this report.
