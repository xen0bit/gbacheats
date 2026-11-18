# Madagascar: Operation Penguin (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Madagascar: Operation Penguin.gba` |
| Size | 8,388,608 bytes (0x800000) |
| Header title | `PENGUINS` |
| Game code / maker | `BM7E` / `52` (Activision), version 0 |
| `file` | Game Boy Advance ROM image "PENGUINS" (BM7E52, Rev.00) |
| MD5 | `87da43aaad7b9fd2b8af57e8e3c71283` |
| SHA-1 | `d9c26b324fe29729b76c028e194dc97adf5bccaa` |
| SHA-256 | `b0cece80fc4620bf669fe60b323e47b8be2a2c8daab674723bbdb672e9d5fddf` |

Phase 0: entry word `0xEA00002E` (stock branch to `0x080000C0`); header checksum `0x0000` with
complement `0x76` (normal rebuilt-header artifact, §16.1). Nintendo-logo scan found **exactly one**
GBA header at file offset `0x0` — a single retail image, no appended trainer, no multiboot stub,
no multi-game pack. No patch/trainer observed.

## 2. Executive summary

The game has a **developer-intended button-code system** with exactly **two** codes, entered during
gameplay while holding SELECT. The engine records button presses into a **10-character circular
buffer** as a custom alphabet (`u r l d R L B` and space), and a validator compares the **last N
characters** of that buffer against a two-entry NUL-terminated string table:

- `uLlRrLdR` — **Christmas / Holiday Mode** (published as Up, L, Left, R, Right, L, Down, R).
  Effect observed: game starts "Mission 0: Christmas Fiasco / Defeat Mr. Chew", the hidden boss
  rematch described by TV Tropes (Christmas tree, snowballs, squeaky-toy medals).
- `LRudRLlr` — **Super Jump** (published as L, R, Up, Down, R, L, Left, Right).
  Effect proven in RAM: flag byte at `0x020065FD` toggles `0x00 -> 0x01`.

Both published codes were found **verbatim in the ROM** and verified live. The cheat flags are
XOR-toggled, so re-entering a code turns it back off. No password/prompt screen exists; the
"Enter Name" keyboard and the medal-based health unlocks are *not* codes (§16.2b, §16.18).
The table contains only two entries, so the accepted 8-press set is **exactly two strings**;
however the validator's *suffix* comparison means any longer press history whose final 8 symbols
match is also accepted — giving a class of unpublished, novel longer codes (§6b).

## 3. How to reproduce

Emulator: mGBA (`/usr/local/bin/mgba`), `SDL_AUDIODRIVER=dummy`, Xvfb `:318`, 3× scale.
Keymap (mGBA SDL defaults): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`,
D-pad = arrow keys. Hold keys ~120 ms.

Path: title screen → **Start Game** → select a slot → **Enter Name** (press Start to accept
default `PENGUIN `) → skip the intro with **A** (0.3 s between presses) → gameplay in the Penguin
Pen → hold **SELECT** and press the sequence.

Tested codes (SELECT + 8 presses):

| Effect | Button sequence | ROM string | Result |
|---|---|---|---|
| Christmas / Mission 0 | Up, L, Left, R, Right, L, Down, R | `uLlRrLdR` | Mission 0: Christmas Fiasco shown; flag toggled |
| Super Jump | L, R, Up, Down, R, L, Left, Right | `LRudRLlr` | `0x020065FD` read `0x00 -> 0x01` |
| Rejected (unknown) | Up×8 | (none) | no flag change, buffer not cleared |
| Rejected (unknown) | Up, R, Down, L, Up, R, Down, L → `uRdLuRdL` | (none) | no flag change, buffer not cleared |

Screenshots kept in `/tmp/opencode/madpenguin/shots/`.

## 4. Address map

File offset = ROM address − `0x08000000` (single flat image).

| Address | Size | Meaning |
|---|---|---|
| `0x0800E7E4` | fn | **Press recorder** `FUN_0800E7E4`: key mask → char, append to buffer |
| `0x0800E5F4` | fn | **Validator** `FUN_0800E5F4`: suffix extract + strcmp + flag toggle |
| `0x08035210` | fn | `strcmp` used by validator |
| `0x08005658` | fn | Input handler: calls recorder when mode gate nonzero |
| `0x080C987C` | 12 B | Code record 0: NUL string `uLlRrLdR` |
| `0x080C9888` | 12 B | Code record 1: NUL string `LRudRLlr` |
| `0x080E7D8` / `0x080E920` | 4 B | Literal pointers to the two code strings (validator pool) |
| `0x080DB3CC/E0/F8` | — | Debug strings `Defeat Section` / `Defeat Section 100%` / `Slow Motion` |
| `0x020065F4` | 8 B | Cheat struct: `u32 codeptr[0]`, `u32 codeptr[1]` (= `0x080C987C`, `0x080C9888` at boot) |
| `0x020065FC` | 1 B | **Christmas flag** (XOR toggle) |
| `0x020065FD` | 1 B | **Super Jump flag** (XOR toggle) |
| `0x02006600` | 4 B | Circular-buffer write index (0..9) |
| `0x02006604` | 10 B | Circular press buffer (characters, `-` = empty) |
| `0x02003F7C` | 4 B | Input mode gate: nonzero while SELECT held in gameplay |

## 5. Algorithm

Recorder (`0x0800E7E4`, verified by Thumb disassembly + decompilation):

```c
// active-high key mask in r1
char c = ' ';                       // default for A / Select / Start / unmapped
switch (mask) {
  case 0x002: c = 'B'; break;       // B
  case 0x010: c = 'r'; break;       // Right
  case 0x020: c = 'l'; break;       // Left
  case 0x040: c = 'u'; break;       // Up
  case 0x080: c = 'd'; break;       // Down
  case 0x100: c = 'R'; break;       // R
  case 0x200: c = 'L'; break;       // L
}
buf[cheat->index] = c;              // buf = 0x02006604
cheat->index = (cheat->index + 1) % 10;
validate(cheat);
```

Validator (`0x0800E5F4`, decompiled):

```c
for (i = 0; i < 2; i++) {
    const char *code = cheat->codeptr[i];      // 0x080C987C / 0x080C9888
    int n = strlen(code);                      // 8 for both
    int start = cheat->index - (n - 10);       // == index + 2 for n=8
    char candidate[12];
    for (j = 0; j < n; j++)
        candidate[j] = buf[(start + j) % 10];  // last n presses, circular
    candidate[n] = 0;
    if (strcmp(candidate, code) == 0) {
        play_sound(0x100);
        *(u8 *)(cheat + 8 + i) ^= 1;           // toggle flag (0x65FC / 0x65FD)
        memset(buf, '-', 10);                  // clear history on success
        show_message(...);
    }
}
```

The recorder is only called from `0x08005658` when `*(u32 *)(0x02003F70 + 0xC) != 0`;
GDB confirmed this word becomes `0x00000004` while SELECT is held during gameplay and `0`
otherwise. During dialogue/cutscene it stays 0 and no presses are recorded.

## 6. Tables

**Button → character alphabet** (8 mapped buttons; 10 game buttons total, the rest map to space):

| Button | mask | char |
|---|---|---|
| A | 0x001 | space |
| B | 0x002 | `B` |
| Select | 0x004 | space |
| Start | 0x008 | space |
| Right | 0x010 | `r` |
| Left | 0x020 | `l` |
| Up | 0x040 | `u` |
| Down | 0x080 | `d` |
| R | 0x100 | `R` |
| L | 0x200 | `L` |

**Code table** — two 12-byte records:

| # | ROM addr | String | GameFAQs published sequence | Effect | Flag |
|---|---|---|---|---|---|
| 0 | `0x080C987C` | `uLlRrLdR` | Up,L,Left,R,Right,L,Down,R | Christmas / Mission 0 | `0x020065FC` |
| 1 | `0x080C9888` | `LRudRLlr` | L,R,Up,Down,R,L,Left,Right | Super Jump | `0x020065FD` |

At boot the two code pointers are materialised in RAM at `0x020065F4`/`0x020065F8` (GDB:
`0x080C987C`, `0x080C9888`). The 10-byte history is initialised to `-` (`0x2D`).

**Name entry** (not a code): alphabet `A-Z _ ! ? ok`, 8-character default `PENGUIN ` (29 input
symbols). Its buffer is consumed only as the save-slot display name (§16.2b).

**Medal unlocks** (not codes): 100 medals → +1 health fish, up to 10; messages at
`0x080DBB64`, `0x080DBE0C`. Save-bit progression, not controller input (§16.18).

## 6b. Enumeration

**Space definition.** The code space is a fixed lookup of **exactly 2** strings of length 8 over
an 8-symbol effective alphabet (`u r l d R L B` + space for unmapped keys). The raw 8-press space
is 8^8 = **16,777,216** histories, of which exactly **2** are accepted — both present in the
published GameFAQs list, and both verified against the ROM bytes. The validator has no checksum,
no field layout, and no generator; the entire table was enumerated from `codeptr[0..1]` and the
validator loop bound (`i < 2`), and cross-checked by running the game's own validator over unknown
inputs (rejections below).

**Novel code.** Because the validator compares only the *last* `strlen(code)` characters of the
10-entry circular buffer, any history of 9 or 10 presses whose final 8 symbols equal a table entry
is accepted even though it is absent from every published list (which give only the 8-press form).
Novel, unpublished code tested in-game:

> **B, B, Up, L, Left, R, Right, L, Down, R** (10 presses after SELECT)
> → internal history `BBuLlRrLdR`, suffix `uLlRrLdR` → accepted as Christmas Mode.

Evidence: the game's own press buffer at `0x02006604` was cleared to `- - - - - - - - - -`
(this only happens on a successful `strcmp` in the validator), and the game entered Mission 0's
intro sequence (`shots/vis_novel_immediate.png`), whereas the preceding gameplay frame had no
dialogue. A shorter 9-press variant (**B, Up, L, Left, R, Right, L, DOWN, R**) was also
crafted/entered; the flag readback was ambiguous because the resulting level transition resets
flags, so the 10-press buffer-clear result is the one claimed.

**Bounds proven by rejection.** Unknown sequences `Up×8` (internal `uuuuuuuu`) and
`Up,R,Down,L,Up,R,Down,L` (internal `uRdLuRdL`) were entered on the real screen: the cheat flags
at `0x020065FC/D` did not change and the buffer was not cleared. These are observed rejections,
not untested guesses. In addition, a press-history injection of a crafted 10-byte buffer with a
non-matching suffix left the flags unchanged, confirming the suffix-exact comparison.

## 7. Validation evidence

- **Observed (emulator)**: title, slot select, name entry, gameplay, pause menu
  (Resume/Slots/Restart Mission/Sound/Sleep/Quit Game) walked on `:318`; Mission 0 title card
  after the Christmas code; Super Jump flag `0x00 -> 0x01` read via GDB; rejections above.
- **Observed (ROM bytes / GDB)**: `uLlRrLdR` at `0x0C987C`, `LRudRLlr` at `0x0C9888`; code
  pointers in RAM at `0x020065F4/F8`; mode gate `0x02003F7C = 4` while SELECT held;
  press buffer contents read as ASCII at `0x02006604`.
- **Derived (disassembly/decompilation)**: mask→char mapping and 10-entry modulo at
  `0x0800E7E4`; suffix extraction, `strcmp`, XOR flag toggle and buffer clear at `0x0800E5F4`;
  exactly 2 loop iterations; gate at `0x08005658`.
- **Inferred**: "Christmas Mode" is the same Holiday Mode described externally (TV Tropes);
  the debug-string menu (`Defeat Section`, `Slow Motion` at `0x080DB3CC/E0/F8`) appears to be
  dead/cut or gated content — no reachable entry was found, and no code xrefs to those pointers
  were observed (only data-table references). The sibling `Madagascar.gba` contains the identical
  three debug strings, confirming they belong to the shared Vicarious Visions engine rather than
  an Operation-Penguin-specific feature.

Fetched web content was treated strictly as data. GameFAQs pages returned 403; the archived
2018 snapshot at `web.archive.org` supplied the two published sequences, which were then verified
against the ROM. No prompt-injection payload was encountered in the pages used.

## 8. Unknowns

- The hidden debug menu implied by `Defeat Section`, `Defeat Section 100%`, `Slow Motion` was
  never reached; its trigger (if any) is unknown. Code xrefs to its string pointers were absent,
  and a save/clear-flag gate could not be excluded. The sibling ROM has the same strings.
- The exact visual/mechanical magnitude of Super Jump was not measured (only the flag toggle
  was read); §16.10 discipline: effect proven as flag state, magnitude inferred.
- Whether the 9-press suffix variant is stable across a level transition was not isolated;
  the 10-press variant's buffer-clear proof is the one relied upon.
- "View Credits" was not exhaustively transcribed; it is an ending/credits sequence reached
  from the title screen, with no cheat surface.
- Reset behaviour of the two flags after a Mission 0 level transition was observed indirectly
  (readback returned to 0) but not traced to its writer.

## 9. Tooling

- `strings -t x`, `grep -abo`, `xxd`, `file`, `md5sum`/`sha1sum`/`sha256sum` for recon.
- `arm-none-eabi-objdump -D -b binary -marm -M force-thumb` for instruction-level confirmation.
- Capstone (Thumb) scanner for PC-relative literals and immediate-compare runs.
- REA/Ghidra (12.1.4, raw-binary ARM load at `0x08000000`): `search_strings`, `xrefs`,
  `list_procedures`, `procedure_pseudo_code`, `procedure_assembly`, `procedure_callers`.
- mGBA under Xvfb `:318` + openbox; `xdotool` XTEST input; `scrot` + ImageMagick crops.
- mGBA GDB stub (`mgba -g`, port 2345) with `gdb-multiarch`: RAM reads, savestate hooking.
- mGBA `.ssN` savestates parsed via Python `zlib` (`gbAs` chunk) per §16.13 for diffing.
- Helper scripts: `/tmp/opencode/madpenguin/gba.py`, `gdbctl.py`.

Legal note: no ROM or copyrighted assets are redistributed here; only hashes, addresses,
algorithms, and tool scripts are published.

## 10. Cleanup

All emulator/display processes started for this engagement were stopped by their recorded PIDs
(Xvfb `:318`, openbox, and every mGBA instance used on `:318`), and generated `.sav`/`.ss*`
files were removed from `roms/Madagascar: Operation Penguin/`. No `pkill` was used.
