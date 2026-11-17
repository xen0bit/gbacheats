# ESPN Final Round Golf 2002 (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `ESPN Final Round Golf 2002.gba` |
| Size | 8,388,608 bytes (0x800000 / 8 MiB) |
| Header title (0xA0) | `ESPN GOLF` |
| Game code (0xAC) | `AGRE` |
| Maker code (0xB0) | `A4` |
| Version (0xBC) | `0` (Rev.00) |
| Fixed byte (0xB2) | `0x96` |
| Complement (0xBD) | `0x3F` |
| Header checksum (0xBE) | `0x0000` (normal rebuilt-header artifact) |
| Entry word (0x00) | `0xEA00002E` (stock branch to 0x080000C0) |
| Nintendo-logo scan | **1 header only** at file 0x0 → no patch, no trainer, no multiboot stub |
| MD5 | `553f4cc7ea38a44642874a8501553e26` |
| SHA-1 | `ecee20b629a38bab7edbc972c70b2c968f50c23c` |
| SHA-256 | `9f3d1c31958c19a8af0730d47b03086a30974a57297ba6246cbd5421ec2535d3` |

The title screen carries `© 2001 Disney`, `© 2001 KONAMI`, and `PRODUCED BY Konami Computer Entertainment Osaka, Inc.`. The archived TCRF page attributes development to Konami Computer Entertainment Nagoya and the US release to 28 Aug 2001; the on-screen Osaka credit is what this exact ROM displays.

## 2. Executive summary

**There is no in-game password code, button code, or player-facing cheat system in this ROM.** No password entry screen exists, no password/cheat/code/secret string exists anywhere in the 8 MiB image, and no button-mask code sequence was found. Every "cheat code" published for this title is an external **GameShark / Action Replay memory edit** (§3.4), which is outside the scope of this engagement.

The one genuine developer-intended hidden feature is a **9-entry debug menu**. It is fully present in the shipping ROM and is gated by a single IWRAM word:

```
debug menu is active  <=>  word at 0x03002528 == 0x1F
```

This was proven by direct RAM injection in mGBA (write `0x1F`, read back `0x1F`, menu appears — `shot_inject.png`, `dbg_menu.png`). The gate is a literal `cmp r0,#0x1F` at ROM `0x08001A8A`; the scene dispatch table at `0x080001F8` maps mode `0x1F` (31) to handler `0x08001A6C`. A code path that *can* write `0x1F` exists at `0x0800F5D2` inside the title-screen state machine, but a live breakpoint there never fired during title/menu navigation, the Konami code, L+R+Start, or L+R+A+B — and no published in-game method of reaching it exists. The only published access method is the GameShark write `03002528:1F` (TCRF), i.e. an external memory edit.

Course/golfer unlocks are **save-data progression flags** (prize money and VS-mode wins), not codes. A hidden profanity string `Fuck Off` is present at file `0x5B455A` (ROM `0x085B455A`) — developer message only, no gameplay effect.

Per §0.2, the "code space" here is the 32-bit scene-mode word at `0x03002528`: **2³² representable values**, exactly **one of which (0x1F) selects the debug menu**. Bounds were proven by injection of `0x01`/`0x02` (normal scenes) vs `0x1F` (debug) and by rejection: values other than `0x1F` do not enter the debug handler.

## 3. How to reproduce

### Environment
- mGBA (SDL), Xvfb `:318`, `SDL_AUDIODRIVER=dummy`, `SDL_VIDEODRIVER=x11`, openbox.
- Keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows.
- Hold keys 0.25–0.4 s (0.1 s taps are dropped); focus with `xdotool windowactivate` + `windowfocus`.

### Menu path (observed)
```
Title (PRESS START) --Start--> MAIN MENU
  MAIN MENU: PLAY GAME / DATA / OPTIONS / LOAD / SAVE
  OPTIONS: SOUND=BGM, WIND=ON, WEATHER=ON
  DATA: REPLAY / STATUS
  STATUS: TOTAL DATA, PACIFIC CC, SEASIDE GC, NORTH HILL GC, EVERGREEN CC, DESERT VAL
  PLAY GAME -> PLAYER SELECT (14 golfers, 2 rows of 7)
            -> GAME SELECT: TOURNAMENT / STROKE / MATCH PLAY / PRACTICE
            -> PRACTICE -> HOLE 1 flyby -> gameplay
```
The in-game Select menu (BGM/SE, Score, Ranking, Give Up, Retire, Reset, Exit) is documented by the archived FAQ (§3.4); no hidden extra entries were found in static analysis. Screenshots of every observed screen are in `/tmp/opencode/espngolf/shot_*.png`.

### Debug-menu access proof (RAM injection; investigation only — NOT an in-game code)
1. Launch `mgba -3 -d <rom>` under Xvfb; the CLI debugger breaks at cycle 0.
2. `continue`, wait for the title screen, press Ctrl-C in the debugger pty.
3. `r/1 0x03002528` → `0x01` (normal title mode).
4. `w/1 0x03002528 0x1F` → `r/1 0x03002528` → `0x1F`.
5. `continue`. The 9-entry debug menu appears (`shot_inject.png`, `dbg_menu.png`).
6. A single write is transient: the title state machine restores the mode word within a couple of seconds. Sustained display therefore requires the external device to re-write the byte every frame — exactly what the published GameShark code does.

### Published codes verified against this ROM
| Source | Claim | ROM verification |
|---|---|---|
| TCRF (archived 2023-12-08) | GameShark `030025281F` (US) enters debug menu | **Confirmed as a RAM gate** by injection above. The literal `0x03002528` does **not** occur anywhere in ROM (literal scan count 0) — it is an IWRAM address written by the external device, not a ROM constant. |
| GameFAQs / cheatcc / supercheats / cheathappens | Seaside $600k or win Pacific CC; Northern Hill $900k; Evergreen $1.7M; Royal Mirage via World Championship | Progression unlocks (save-flag). `NEW COURSE UNLOCKED!` string at `0x20D4C8`; STATUS screen lists 5 courses. Not codes. |
| gamegenie.53lu (EU) / etherealgames (US) | Encrypted Action Replay V3 codes (Max money, Unlock all levels, debug menu) | External memory edits; out of scope. Encrypted AR payloads carry no literal to verify. |
| GameFAQs FAQ 11341 (archived) | Beating tour players in VS unlocks them elsewhere; save/reload "Save Cheat" | Matches observed STATUS/player-select structure. Save/reload is not a code. |

## 4. Address map

| Item | Address | Evidence |
|---|---|---|
| Scene/mode word (gate) | RAM `0x03002528` (IWRAM), 32-bit | `ldr r0,=0x03002520; ldr r0,[r0,#8]` in gate; write-watchpoint hit at `0x080005A0` storing value 2 |
| Input mirror (active-high) | RAM `0x03002770` (halfword) | debug-menu input reads `ldr r0,=0x03002770; ldrh r1,[r0]` at `0x0800F5A6`/`0x0800F5A6` |
| Bootstrap key buffer | RAM `0x03002552` | boot code `0x0800826–0x080082C` stores `~KEYINPUT` there |
| Gate check | ROM `0x08001A8A` | `cmp r0,#0x1F; beq 0x08001A90; b 0x08001E5C` |
| Debug-menu handler | ROM `0x08001A6C` (gate at `0x08001A8A`) | reached via `bl 0x08001A6C` at `0x08002F8` |
| Scene dispatch loop | ROM `0x08001DC–0x08001EE` | `subs r0,#1; cmp r0,#0x30; ldr r0,[table]` |
| Scene dispatch table | ROM `0x080001F8`, 49 entries (modes 1–49) | mode `0x1F` → `0x080002F8` |
| Setter of `mode=0x1F` | ROM `0x0800F5D0–0x0800F5D4` | `ldr r1,=0x03002520; movs r0,#31; str r0,[r1,#8]`; reached from case 8 of table `0x0800F4BC` |
| Title-scene handler | ROM `0x0800F49C–0x0800F5EE` | runs while mode == 49 |
| Debug labels | ROM `0x09FD6AC–0x09FD730` (file `0x1FD6AC–0x1FD730`) | ASCII strings dumped and displayed in-game |
| Course/weather/golfer strings | ROM `0x09FD260–0x09FD564` (file `0x20D260–0x20D564`) | ASCII |
| `NEW COURSE UNLOCKED!` | ROM `0x09FD4C8` (file `0x20D4C8`) | ASCII |
| Developer message `Fuck Off` | ROM `0x085B455A` (file `0x5B455A`) | bytes `46 75 63 6b 20 4f 66 66` |

File offset → ROM address: `ROM = 0x08000000 + file_offset` (single image, base 0).

## 5. Algorithm (gate / pseudocode)

```c
// IWRAM globals base, held in a literal pool throughout the binary
volatile uint32_t *G = (volatile uint32_t *)0x03002520;
#define MODE G[2]                  // 0x03002528

// main scene dispatcher, ROM 0x080001DC
while (1) {
    uint32_t m = MODE - 1;
    if (m > 0x30) continue;        // modes 1..49 only
    scene_table[m]();              // table @ 0x080001F8
}

// mode 0x1F handler chain: 0x080002F8 -> 0x08001A6C
void debug_menu(void) {
    if (MODE == 0x1F) {            // ROM 0x08001A8A: cmp r0,#0x1F
        init_debug();              // bl 0x0800198C, sound 0xBF
        for (;;) {
            draw_menu(labels, 9);  // HIROSE .. EXIT DEBUGMODE, "TIME:%d", "PRESS START"
            uint16_t k = *(uint16_t *)0x03002770;
            if (k & 0x80) cursor++; // Down
            if (k & 0x40) cursor--; // Up
            ... dispatch cursor 0..8 ...
            // cursor 8 = EXIT DEBUGMODE -> write a non-0x1F mode and return
        }
    }
    goto normal_path;              // 0x08001E5C
}

// the only in-ROM writer of 0x1F, ROM 0x0800F5D0 (title scene, state 8)
MODE = 0x1F;                       // movs r0,#31; str r0,[r1,#8]
```

The active-high key mask is `A=0x01, B=0x02, Select=0x04, Start=0x08, Right=0x10, Left=0x20, Up=0x40, Down=0x80, R=0x100, L=0x200` (from `~KEYINPUT` at `0x04000130`, masked `0x3FF`).

## 6. Tables

### 6.1 Debug-menu entries (ROM `0x09FD6AC`, file `0x1FD6AC`)
| # | Label | Effect (TCRF, archived) |
|---|---|---|
| 0 | HIROSE | Starts Course 1 |
| 1 | KUNIHARU | Starts Course 1 |
| 2 | SOUND TEST | Black screen; any button returns to title |
| 3 | DEMO %d | View all demo cutscenes |
| 4 | BG TEST | Goes to link screen |
| 5 | SCENARIO %d | Start at any scenario |
| 6 | ISHIKAWA | Broken flag editor; L changes unknown flags |
| 7 | USHIDA | Displays a message, resets to title |
| 8 | KANEIII CHAR %d ANIM %d | Character/animation test; Left/Right = CHAR, L/R = ANIM |
| 9 | EXIT DEBUGMODE | Leaves debug mode |

Additional labels: `TIME:%d` (`0x09FD728`), `PRESS START` (`0x09FD730`).

### 6.2 Scene dispatch table (ROM `0x080001F8`)
49 entries, indices 0–48 → modes 1–49. Selected entries:
```
mode 0x01 -> 0x080002BC   mode 0x1C -> 0x080002E6   mode 0x30 -> 0x0800035E
mode 0x02 -> 0x080002C2   mode 0x1D -> 0x080002E0   mode 0x31 -> 0x08000364
mode 0x1E -> 0x080002CE   mode 0x1F -> 0x080002F8  <-- DEBUG
mode 0x20 -> 0x080002F2   mode 0x21 -> 0x080001DC
```

### 6.3 Unlockable content (not codes — save/progression flags)
- Courses (US): Pacific CC (default), Seaside GC, North Hill GC, Evergreen CC, Desert Valley. Unlock by prize money / tournament wins (GameFAQs).
- Golfers: 14 selectable portraits; names in ROM at `0x09FD2D0`: `WILLE, CALLY, JOHN, JEAN, BAJIO, JASON, SHAWN, HENRY, CAIN, STING, YAKEXI, MARTIN, JACK, WILLIE`. Tour golfers unlock by beating them in VS mode.
- Weather labels: `MISTY, SNOWY, FINE2, CLEAR, EVENING3, RAINING, EVENING2, EVENING1, CLOUDY, FINE1` (`0x09FD260`).

## 6b. Enumeration

**Space definition.** The only cheat-relevant state is the 32-bit scene-mode word at `0x03002528`: 2³² = 4,294,967,296 representable values. The dispatch layer bounds *meaningful* modes to 1..49 (49 entries plus a bounds bailout, `cmp r0,#0x30; bhi`), so at most 49 of those values select a scene; exactly **one** (`0x1F`) selects the debug menu. The word is 32-bit (`ldr`/`str`, not byte), though I injected it with `w/1` (byte write) successfully because the upper three bytes are already zero.

**Validator model.** `accepted(mode) == (mode == 0x1F)` for the debug scene, implemented by `0x08001A8A`. Reimplementation: compare the 32-bit word to 31; branch to `0x08001A90` if equal, else `0x08001E5C`. This agrees with both observed inputs: `0x01` → normal title, `0x1F` → debug menu.

**Novel code (§0.2).** The engagement's deliverable is a *developer-intended in-game code*. None exists, so no password can be minted; this is a bounded negative result, not an omission. The closest analogue — forcing a mode the game never assigns through play — was done by RAM injection (`0x1F`), which is the same state the published GameShark edit produces and is therefore **not** a novel in-game code. It is reported as a RAM proof only.

**Bounds proven by rejection.**
- `0x01` (title, observed default) and `0x02` (boot/loading, observed writer at `0x080005A0`) → normal scenes, **no debug menu**.
- `0x1F` injected → debug menu appears (9 entries, `dbg_menu.png`).
- Live Thumb breakpoint at the in-ROM setter `0x0800F5D2`: **never hit** during (a) 18 s idle at the title, (b) full main/options/data/status/game-select/player-select navigation, (c) Konami code `↑↑↓↓←→←→BA`, (d) `L+R+Start`, (e) `L+R+A+B`. Therefore no tested controller input reaches the only in-ROM assignment of `0x1F`.
- No alternative assignment of `0x1F` to the mode word was found: a byte-pattern scan of all 8 MiB for `movs r?,#0x1F` within 24 bytes of a `str r?,[r?,#8]` produced 15 candidates; the only one writing the globals base was `0x0800F5D2` (above). The other 14 are unrelated register traffic (e.g. `0x0812B66E`, `0x08249090` operate on other bases).

**Negative-result search space (counts).**
| Search | Count | Result |
|---|---|---|
| ASCII `password` / `pass word` / `cheat` / `code` / `secret` / `enter ` / `invalid` | 0 / 0 / 0 / 0 / 0 / 0 / 0 | no password surface |
| ASCII `debug` | 1 | `EXIT DEBUGMODE` @ `0x1FD714` |
| ASCII `unlock` | 1 | `NEW COURSE UNLOCKED!` @ `0x20D4D5` |
| ASCII `congrat` | 1 | `CONGRATULATIONS!` @ `0x20D4E2` |
| Embedded Nintendo logos / GBA headers | 1 | single image; no trainer/patch |
| Literal word `0x03002528` in ROM | 0 | gate address is RAM-only |
| Konami-code mask sequence (u16-LE, u8, and reversed) | 0 / 0 / 0 | no button cheat table |
| `movs r?,#0x1F` near `str r?,[r?,#8]` | 15 | 1 relevant (setter); 14 unrelated |

## 7. Validation evidence

- **Observed** (emulator/RAM): title and all main-menu screens; debug menu displayed after `w/1 0x03002528 0x1F` with value read back `0x1F` (`shot_inject.png`, `dbg_menu.png`); mode reads `0x01` at title and `0x02` after injection decays; breakpoint at `0x0800F5D2` never hit under all tested inputs; single embedded header; dev-message bytes at `0x5B455A`.
- **Derived** (disassembly): gate `cmp r0,#0x1F` at `0x08001A8A`; 49-entry scene table at `0x080001F8`; debug handler chain `0x080002F8` → `0x08001A6C`; setter `0x0800F5D0–0x0800F5D4`; bootstrap input mirror at `0x03002552`; debug-menu input read at `0x03002770`.
- **Inferred**: the nine menu-item *effects* are taken from the archived TCRF page, not individually re-entered; the exact controller path (if any) that drives the title state machine to case 8 was not identified, only shown to be absent from all tested inputs.

## 8. Unknowns

- Whether some untested, deliberately obscure controller input (e.g. a link-cable event, a specific save state, or a long multi-button sequence on a specific frame) drives the title handler to state 8 and sets `mode=0x1F`. All standard inputs and the documented Konami code were tested without success; the published record lists only the GameShark write.
- The exact semantics of developer-menu entries 3–8 beyond their labels; ISHIKAWA's "unknown flags" were not individually mapped.
- The save-record bit layout for course/golfer unlocks was not dumped; the unlock *behaviour* is documented by the FAQ and visible in STATUS, but the bit offsets are not reported here.
- The in-game Select menu's entries are documented by the archived FAQ; an exhaustive in-hole pause walk was not captured.

## 9. Tooling

- `file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings -t x`, for Phase 0/1.
- Python 3 + `capstone` 5.0.7: literal scans, `ldr`-pool resolution, mode-table dump, byte-pattern searches.
- `arm-none-eabi-objdump -M force-thumb` with `--adjust-vma=0x08000000` for all disassembly.
- mGBA SDL under Xvfb `:318` + openbox; `xdotool` (XTEST) for input; `import -window root` for screenshots.
- mGBA CLI debugger (`mgba -d` via PTY): `r/1`, `w/1`, `break/t`, `watch/w`, `continue`, Ctrl-C — used as the RAM oracle (§16.19).
- Web: archived TCRF page (2023-12-08 capture), archived GameFAQs FAQ 11341 (2018 capture), plus search-result snippets from GameFAQs/cheatcc/supercheats/cheathappens/53lu/etherealgames for published-code verification. Fetched pages were treated as data; no instructions in them were executed.

**Legal note:** no ROM image, extracted graphics, or copyrighted assets are redistributed. Only hashes, addresses, algorithms, and original observations are published.
