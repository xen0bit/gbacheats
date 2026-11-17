# Fantastic 4 (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Fantastic 4.gba` (16,777,216 bytes = 0x01000000) |
| Header title | `FANTASTIC4` |
| Game code | `BF4E` (region `E` = USA) |
| Maker | `52` |
| Version | 0x00 (Rev.00) |
| Entry word | `0xEA000030` (normal ARM branch, not a cracktro patch) |
| Fixed 0x96 / main unit / device | `0x96` / `0x00` / `0x00` |
| Complement / header checksum | `0x18` / `0x0000` |
| MD5 | `04105c845973df1d717b2487227f0fb0` |
| SHA-1 | `9673c055a04657a620ad1ed2710c3d33fb2a70a4` |
| SHA-256 | `25fc394e58eb4ae1131c0a173207717efefe101515c634eb7a30464326a73a6e` |

Phase 0 checks: a scan of the whole image for the 156-byte Nintendo logo found
**exactly one** GBA header, at file offset `0x0`; this is a single clean retail
image, not a 2-in-1 pack and not an appended-trainer release. No patch/trainer
was detected. Header checksum `0x0000` with a non-zero complement byte is the
normal rebuilt-header artifact (guide §16.1); the entry word is the stock branch.
Build timestamp embedded in the image: `"Fantastic4 Debug Screen  Built: Apr 19 2005"`.

## 2. Executive summary

This GBA SKU has **no password / text-code system**. It has a **title-screen
button-code system** with exactly **four** input sequences stored in one table.
The one published code — `B, A, Left, Select, A` — opens an in-game **cheat menu**
(LEVEL 01–43 selector, Song selector, Unlimited Health toggle; A starts the game
at the chosen level). The other three sequences are undocumented in any
published list that was checked; they are registered by the same validator but
produce no visible title-screen change.

Also present in the image is a complete internal **"Fantastic4 Debug Screen"**
(Profiling / Slow RAM Usage / Memory Allocation / profile toggles) with its menu
table and constructor intact, but **no caller or pointer to its entry point was
found** — it is dead code in this retail build (guide §16.3, category 2).

Published numbers for the PS2/GameCube/Xbox versions (Infinite Cosmic Power,
"Target"/Barge, HELL level) were verified **absent** from this ROM in every
encoding tested. Action Replay / GameShark codes found on the web are memory
edit codes and are out of scope.

## 3. How to reproduce

* Emulator: `mgba -3 Fantastic 4.gba` under `Xvfb :319` (1024×768×24),
  `SDL_AUDIODRIVER=dummy`, openbox window manager.
* Keymap (mGBA SDL defaults): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
  Select=`BackSpace`, D-pad = arrow keys. Hold ≈90 ms, gap ≈180 ms.
* Boot path (important): logos → **~2.5 minutes of scrolling credits** →
  "PRESS START" title. Do not mistake the intro credits for a code-activated
  screen (this cost several false "code confirmed" readings).
* At the **PRESS START** title, press `B, A, Left, Select, A`. The cheat menu
  overlay appears (LEVEL 01 / Song 00 / Unlimited Health OFF).
* Cheat menu controls (observed): **Up/Down** change LEVEL with wraparound
  (01 → 43 → 42 → … → 01); **A** starts the game at the selected level.
  The Song selector has its own up/down arrows; its exact input mapping was not
  isolated (see §8).
* Main menu (title → Start): `NEW GAME`, `CONTINUE`, `OPTIONS` (3-slot ring;
  Down wraps). `CONTINUE` → `SELECT SLOT`. No password/cheat entry item.
* Screenshots used as evidence are in `/tmp/opencode/fantastic4/`
  (`code1_after2_crop.png`, `level_montage.png`, `mm01_main_crop.png`,
  `mm10_A_crop.png`, `walk05_a2_crop.png`, etc.).

## 4. Address map

All addresses are ROM addresses (`0x08000000 + file offset`) unless marked RAM.

| Item | Address (ROM) | Notes |
|---|---|---|
| Button-code sequence table | `0x080822D4`–`0x08082306` | 4 records, `u16` masks, `0xFFFF` terminator |
| Code 1 (published) | `0x080822D4` | `B,A,Left,Select,A` |
| Code 2 (undocumented) | `0x080822E2` | `L,R,Down` |
| Code 3 (undocumented) | `0x080822EC` | `Up,Down,Up,Right` |
| Code 4 (undocumented) | `0x080822F8` | `Left,Right,Left` |
| Associated action data | `0x08082304`, `0x0808230C`, `0x08082314` | `{0xFFFF0000, Thumb fn ptr}` pairs |
| Associated string ptr | `0x0808231C` | `"FadeUpBackgroundState"` |
| Action functions | `0x08016210`, `0x08016434` (empty `bx lr`), `0x080162CC` | `0x080162CC` ORs `0xFFFF` into halfwords `[ptr+6]`, `[ptr+8]` |
| Title object constructor | `0x08015940` | registers the 4 codes via 4 calls to `0x08068D50` |
| Code registration | `0x08068D50` | builds 24-byte observer records |
| Code validator (per frame) | `0x08068DA4` | progress index at record `+0x0C`, timeout at `+0x12` |
| Completion callback | `0x08068EA4` | sets flag bits; returns 1 when the flag word is fully satisfied |
| Debug screen title strings | `0x08080B64`, `0x08080B80`, `0x08080B94` | "Fantastic4 Debug Screen" / "Built: Apr 19 2005" / dashes |
| Debug screen menu string table | `0x080FF26CC`–`0x080FF2710` | Profiling, Slow RAM Usage, Memory Allocation, Back, Enable/Disable, … |
| Debug screen constructor | `0x08000F6C` | creates the debug screen; **no BL/xref found** |
| English UI text bank | `0x080BC789`–`0x080BC8D7` | MAIN MENU, OPTIONS, SELECT LEVEL, PAUSE, … |
| Localized text banks | `0x080FC789` (French) … `0x080FDF00` (Dutch) … | no PASSWORD string in any language |
| Cheat-related RTTI names | `0x0822B487` `UI_CheatFlagsObserver`, `0x0822B4D5` `UI_KeypadObserver`, `0x0822B515` `UI_PasswordCharacter`, `0x0822B52A` `UI_PasswordWatcher` | class names only |
| EWRAM global pointers | `0x02000018` → `0x0200C378`; `0x02000020` → `0x0200A6EC` | Observed with mGBA `-d`: `r/4` reads returned these values |

## 5. Algorithm (button-code validator model)

Key masks are active-high `~KEYINPUT & 0x3FF`:
`A=1, B=2, Select=4, Start=8, Right=0x10, Left=0x20, Up=0x40, Down=0x80, R=0x100, L=0x200`.

```
register(observer, sequence_ptr, param):        # 0x08068D50
    n = count halfwords until 0xFFFF
    rec = observer.records[observer.count++]
    rec = { first: hw[sequence_ptr+0],       # 0x0000
            ptr:   sequence_ptr + 2,          # first button mask
            len:   n,
            progress: 0, timeout: 0, param: param }   # 24 bytes

validate(observer, keys):                       # 0x08068DA4, once per frame
    for rec in observer.records:
        if rec.first != 0 and (keys & rec.first) == 0: continue
        expected = hw[rec.ptr + 2*rec.progress]
        if expected == 0x1000:                  # counter-token
            accepted = (counter == rec.param)
        elif expected & 0x2000:                 # bitmask-token
            accepted = (keys & expected) != 0
            if accepted: keys = keys & expected
        else:
            accepted = (keys == expected)
        if accepted:
            if complete(observer, rec) :        # 0x08068EA4 -> flag word
                rec.progress = 0; rec.timeout = 0
                dispatch(observer, rec.index)   # action / UI effect
        else:
            rec.progress = 0
        rec.timeout = (rec.timeout + 1) & rec.param   # param 0 => timeout
```

The four title-screen records are registered with `param = 0` (no counter or
mask tokens), so they are strict, edge/held-semantics press sequences. The
`0x1000`/`0x2000` token forms are used by a different observer at `0x08038B0C`
for the player character's combo input (sequences at `0x08083664` / `0x0808366C`),
not for cheats.

## 6. Tables

### 6.1 Button codes (complete registered set, 4 entries)

| # | ROM address | Buttons | Published? | Observed effect at PRESS START title |
|---|---|---|---|---|
| 1 | `0x080822D4` | B, A, Left, Select, A | **Yes** (GameFAQs, classicgamehacking, TCRF-adjacent lists) | Cheat menu appears: LEVEL 01, Song 00, Unlimited Health OFF |
| 2 | `0x080822E2` | L, R, Down | No | No visible change (title remains) |
| 3 | `0x080822EC` | Up, Down, Up, Right | No | No visible change (title remains) |
| 4 | `0x080822F8` | Left, Right, Left | No | No visible change (title remains) |

Space size: **4 sequences**, lengths 5/3/4/3 presses, alphabet = the 10 GBA
button bits. The table is terminated by `0xFFFF` after the fourth sequence and
the next word (`0x0000` at `0x08082304`) is the start of the action-data block,
so the set is closed.

### 6.2 Cheat menu

| Field | Observed values | Control |
|---|---|---|
| LEVEL | 01–43 (wraparound) | Up/Down |
| Song | 00 at entry | mapping not isolated |
| Unlimited Health | OFF at entry | mapping not isolated |
| Start game | — | A |

### 6.3 Negative: console-version codes

| Published code (platform) | Mask sequence searched | Literal present in ROM? |
|---|---|---|
| Infinite Cosmic Power (PS2/Xbox) | `40 01 01 01 20 10 02` | No |
| HELL (GameCube) | `10 10 02 01 20 40 80` | No |
| HELL (PS2/Xbox) | `10 10 01 02 20 40 80` | No |
| Target/Barge (PS2/Xbox/GC) | `01 02 01 80 80 02 40` | No |

## 6b. Enumeration

**Space definition.** The cheat-code surface is a fixed table of 4 button
sequences (§6.1). There is no checksum, no alphabet, no variable-length field:
the representable set is exactly those 4 sequences. All 4 were read out of the
ROM bytes at `0x080822D4`–`0x08082306` and all 4 were pressed on the real title
screen in mGBA (`code1_*` … `code4_*` screenshots).

**Novel codes (absent from every published list checked).** `L, R, Down`,
`Up, Down, Up, Right`, and `Left, Right, Left` are not on GameFAQs, the
classicgamehacking post, 53lu, cheatingdome, absolutcheats, or the archived
lists consulted; the web sources explicitly say "possibly up to 3 more codes
for the same screen", which matches the 3 extra ROM records exactly. These
three were entered on the emulator title screen. They are accepted by the same
validator (same 24-byte records, same completion callback) but produced **no
visible title-screen state change** in the screenshots. A bounded statement is
made in §7: they are real, undocumented registered sequences; any effect they
have is non-visual or requires a game state not reached in this engagement.

**Bounds proven by rejection.** Out-of-space sequences produce no effect:
pressing the 2-button prefix `B, A`, the console-version 7-press sequences, and
arbitrary d-pad combinations at the title all left the title screen unchanged.
The table itself gives the hard bound: the `0xFFFF` terminator at `0x08082300`
followed by the action-data block at `0x08082304` means no 5th sequence can be
registered. The validator's strict `keys == expected` comparison (for `param=0`
records) means any extra/missing/substituted button breaks the match.

**Level-select bounds.** The cheat menu LEVEL field was enumerated directly on
screen: 01 → 43 → 42 → … → 32 over 12 Up presses (`level_montage.png`,
`level_montage2.png`), proving wraparound at both ends of a 1–43 range.

## 7. Validation evidence

* **Observed (emulator / screenshots / RAM reads):**
  * B,A,Left,Select,A at the title → cheat menu (`code1_after2_crop.png`).
  * LEVEL 01 → 43 with Up, 43 → 01 with Down; decrement sequence enumerated to 32.
  * A on the cheat menu → game starts at the selected level (`walk05_a2_crop.png`).
  * Title → Main Menu (NEW GAME / CONTINUE / OPTIONS) → SELECT SLOT
    (`mm01_main_crop.png`, `mm10_A_crop.png`).
  * EWRAM globals read with mGBA `-d` (`frame` + `r/4`):
    `*(0x02000018) = 0x0200C378`, `*(0x02000020) = 0x0200A6EC`.
  * Savestate `save 2` / `save 3` produced valid `gbAs` PNG states whose
    zlib-decompressed 397,312-byte payloads were diffed.
* **Derived (disassembly):**
  * Sequence table bytes and the 4 exact masks at `0x080822D4`–`0x08082300`.
  * Registration by `0x08015940` (4 calls to `0x08068D50`).
  * Validator record layout (24 bytes) and the strict-equality match at
    `0x08068DA4`/`0x08068EA4`.
  * Debug screen constructor `0x08000F6C` and its menu table `0x080FF26CC`.
  * Absence of console codes: literal `u16` mask sequences not found anywhere
    in the 16 MiB image.
* **Inferred (not fully exercised):**
  * The three action function pointers at `0x08082304/0C/14` are the action
    handlers associated with codes 2–4; `0x080162CC` sets a 16-bit cheat-flag
    word but no in-game effect of that word was played through.
  * The Song and Unlimited Health controls exist visually but their input
    mapping was not isolated.
* **Negative results bounded:**
  * *No password system:* `strings`/`grep` found no PASSWORD text in the
    English bank (`0x080BC789`–`0x080BC8D7`) or any localized bank; the only
    "password" occurrences in the whole 16 MiB are the two RTTI class names
    `UI_PasswordCharacter`/`UI_PasswordWatcher` at `0x0822B515`/`0x0822B52A`,
    which belong to the in-game "hack puzzle" keypad (dialogue strings describe
    selecting circuit objects), not a code-entry screen. Main menu has 3 items,
    none for passwords.
  * *Debug screen is dead code:* BL scan and full-image pointer scan found
    **0 callers and 0 pointers** to `0x08000F6C`; the strings and menu table
    exist but nothing reaches the constructor in this build (guide §16.3 #2).
  * *Console codes absent:* 4 published sequences searched as `u16` byte patterns,
    0 hits (table §6.3).
  * *Search counts (strings):* keyword scan over the full ROM produced ~40
    relevant hits; after classifying, 1 debug-screen cluster, 6 cheat/password
    RTTI names, 4 state-machine class names, and the rest game dialogue/level
    data. A whole-ROM `u16`-pattern scan for `0x0000 <masks> 0xFFFF` found 393
    candidates; only the 4 at `0x080822D4`… are in the title object's table
    (the others are state-machine transition data at `0x08083600`+ and level
    data at `0x022B000`+).

## 8. Unknowns

* Exact input mapping for the Song selector and the Unlimited Health toggle
  inside the cheat menu (their graphics and up/down arrows were observed, but
  no key combination changed them in the trials performed).
* Whether codes 2–4 have a non-visual effect (e.g., setting an internal flag
  consumed later in gameplay). They are definitely registered; no in-game
  consequence was demonstrated.
* The purpose of the empty action `0x08016434` and the detailed semantics of
  the 16-bit word written by `0x080162CC`.
* Whether the debug screen can be reached from a state not explored (e.g., a
  specific save flag or a link-cable event); no caller exists in the static
  call graph, so this is unlikely.
* mGBA's `-t` loaded `menu_state.ss1` reliably but silently failed on states
  captured at the title screen; title-state experiments therefore used fresh
  boots. This is a harness quirk, not a game finding.

## 9. Tooling

* `file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings`, `grep` — Phase 0/1.
* `capstone` 5.0.7 (Python) for Thumb PC-relative/BL scans;
  `arm-none-eabi-objdump -M force-thumb` for targeted disassembly.
* `mgba` (SDL) under `Xvfb :319` + openbox; `xdotool` XTEST input; `scrot`/
  `import`/`convert`/`montage`/`tesseract` for screenshots and OCR.
* mGBA CLI debugger (`mgba -d`, piped through a FIFO with `stdbuf -o0`):
  `frame`, `r/4`, `x/4`, `save 2/3` for RAM reads and savestate generation.
  (The GDB stub on port 2345 was unavailable — held by a sibling session —
  so the stub-free `-d` debugger was used per guide §16.2/§16.13.)
* Savestate analysis: zlib-decompress the PNG `gbAs` chunk (397,312-byte state)
  and diff bytes (§16.13).
* Helper scripts in `/tmp/opencode/fantastic4/`:
  `phase0.py`, `keys.py`, `batch_codes.py`, `level_enum.py`,
  `cheat_controls.py`, `test_from_menu.py`, `mainmenu_walk.py`,
  `pause_walk.py`, `ssdiff.py`, `launch_dbg5.sh`.
* Web sources: GameFAQs cheat page (2005-06-27), classicgamehacking.com
  (2012-04-21), 53lu, cheatingdome, absolutcheats. Fetched pages were treated
  as data; no prompt-injection payload was encountered in this engagement.

*Legal note:* no ROM image or copyrighted game asset is redistributed here;
only addresses, hashes, and original observations are published.
