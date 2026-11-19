# Godzilla: Domination! (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `/mnt/gbacheats/roms/Godzilla: Domination!/Godzilla: Domination!.gba` |
| Size | 4,194,304 bytes (0x400000, 4 MiB) |
| Header title | `GODZILLADOMI` |
| Game code | `AG4E` · Maker `70` · Version `0x00` |
| Fixed byte | `0x96` present at 0xB2; complement `0x6A`; header checksum `0x0000` |
| Entry word | `0xEA00002E` → stock ARM branch to 0x080000C0 |
| MD5 | `fb0b9d0db44ec7de4a534c2849f8b756` |
| SHA-1 | `dfcfc6d1ad2bc629429d9ebaae0e9452efa8d0d6` |
| SHA-256 | `0065899068843a2c729a99897438326b13d478adecec6334d979677eb050a159` |

**Embedded headers (§5.4b scan):** Nintendo-logo scan found two additional headers:
- file `0x49A78` — game code `AGBJ`, maker `01`, blank title, stock entry word: a small multiboot/link-play image (credits contain `*LINK PLAY PROGRAMMING:` at `0x08049138`). Not a second playable game.
- file `0x4C024` — verbatim duplicate of the main `AG4E`/`GODZILLADOMI` header.

No scene-release cracktro or appended trainer was found; this is the retail image.

## 2. Executive summary

There is **no password system, button-code sequence, or unlockable-character input** in this
ROM. The only developer-intended cheat surface is a **hidden debug scene-select menu**, which is
scene index **2** in the game's scene-state machine (IWRAM byte `0x030025F8`, mirrored at
`0x030425F8`). Setting that byte to 2 immediately replaces the current screen with a two-column
list of all **47** in-game scene names.

The published method (TCRF) is the CodeBreaker code `74000130 00FF 330425F8 0002` plus "press
L+R". **The L+R press is not an in-game trigger** — it is the CodeBreaker button-activator
condition for applying the byte write. I proved (screenshot `s_gate2_nolr.png`) that writing
`0x02` to the byte alone opens the menu with no controller input at all. This is a correction to
the published description.

The gate is **closed in the shipping game**: the byte is the general scene-state variable. The
crt0 writes `1` (0x080003E8), and all ten in-game callers of the scene setter (0x08017944)
pass values {3, 8, 11, 12, 13, 15, 16, 23, 41, 45, 46} — **none passes 2**. The other direct
writers pass 0x2C, 0x26–0x28, 0x13, 0x16. No controller path can set the gate; the only way to
reach scene 2 is an external byte write (the published CodeBreaker code). This is a bounded
"gated feature with no in-game setter" result (§16.3), not an untested negative.

## 3. How to reproduce

**Toolchain:** mGBA 0.10.5 under Xvfb `:316`, `SDL_AUDIODRIVER=dummy`, `-d` CLI debugger driven
over a Unix socket (the GDB stub port 2345 was occupied by another session; `-C gdb.port=...`
did not rebind it in this build). Keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, arrows =
D-pad. Screenshots via `scrot`; RAM read via `r/1 <addr>` / savestate `gbAs` decompression.

**Menu path:**

1. Boot → Atari/Infogrames splash → "Press Start" title (scene byte `0x0C`).
2. Start → "CHOOSE A GAME MODE" (Story / VS / Custom / Options).
3. To open the debug screen, from any point write `0x02` to IWRAM `0x030025F8`
   (e.g. debugger `w/1 0x030025F8 2`). The list appears on the next frame; **no L+R needed**.

**Gate-value test (all from the same base state, screenshot per value):**

| Byte written | Observed screen | Result |
|---|---|---|
| `0x00` | black (invalid scene 0) | rejected |
| `0x01` | Atari/Infogrames splash | rejected |
| `0x02` | **debug scene list** | **accepted** |
| `0x03` | Atari/Infogrames splash | rejected |
| `0x0C` | CHOOSE A GAME MODE | rejected |

Evidence: `gate_0.png`, `gate_1.png`, `gate_2.png`, `gate_3.png`, `gate_12.png`;
`s_gate2_nolr.png` proves L+R is unnecessary.

## 4. Address map

| ROM / RAM address | Meaning | Evidence |
|---|---|---|
| `0x08000000` | ROM base; 4 MiB | header |
| `0x08000494` | literal `0x030025F8` used by crt0 init | disassembly |
| `0x080003E4`–`0x080003E8` | crt0 writes `1` to the scene-state byte | watchpoint + disassembly |
| `0x08017944` | scene-setter `set_scene(u8 id)`; stores id to `0x030025F8` | BL-target scan (10 callers) |
| `0x0800C10A`–`0x0800C136` | debug-list cursor `0x030017F0` ±20, clamped to 49 | disassembly |
| `0x0800C142`–`0x0800C168` | debug-list renderer, 20 rows, string base `0x08031BBC` | disassembly |
| `0x0800C1DC`–`0x0800C1F4` | selection handler: reads cursor, calls scene setter | disassembly |
| `0x08031BDC` | debug-menu string table: **47 entries × 0x20 bytes**, NUL-terminated ASCII | decoded in full |
| `0x080F17C0` | scene descriptor table: 20 records × 12 bytes `{u32 0x0C, u32 name_ptr, u32 data_ptr}` | word dump |
| `0x080F18B0`+ | human-readable scene labels (`Title` … `Ending Two`, incl. `Mystery Boss Stage`) | strings |
| `0x030025F8` (= `0x030425F8` mirror) | scene-state byte; **value 2 = debug menu** | GDB-style watchpoint, RAM read, screenshots |
| `0x030017F0` | debug-list cursor index (0–49); changes with Up/Down | savestate diff + code |
| `0x0300172C` | unrelated counter (initial false lead, not the cursor) | savestate diff |

Savestate layout used for RAM evidence: mGBA `.ssN` PNG → zlib `gbAs` chunk → 397,312-byte
raw state; IWRAM at `+0x19000`, EWRAM at `+0x21000`. `0x030025F8` → raw offset `0x1B5F8`.

## 5. Algorithm

No password validator exists. The gate predicate is a single equality:

```
if (*(u8*)0x030025F8 == 2)  render_scene(DEBUG_SCENE_LIST);
```

`0x030025F8` is the global scene-state index consumed by the scene dispatcher at
`0x0806512` (`subs r0,#1; cmp r0,#0x30; ldr pc,[table,r0<<2]` — valid scenes 1..0x31).
Scene-setter pseudocode (0x08017944):

```
prev_scene = *(u8*)0x030025F8;   // saved to 0x08019... (0x030019CC literal)
*(u8*)0x030025F8 = new_scene;    // r0
*(u8*)0x030017.. = 0;
```

The debug-list renderer reads the 0x20-stride table at `0x08031BBC`, drawing 20 rows per
column; Up/Down changes `0x030017F0`, L/R (code path) adds/subtracts 20 with a cap of 49.

## 6. Tables

### 6.1 Debug menu — complete 47-entry enumeration

Decoded from the ASCII table at `0x08031BDC` (index = entry number, stride 0x20):

| # | Entry | # | Entry | # | Entry |
|---:|---|---:|---|---:|---|
| 0 | ENGLISH | 16 | LADDER LAVA | 32 | WINNER GODZILLA |
| 1 | FRENCH | 17 | LADDER MOON | 33 | WINNER GHIDORAH |
| 2 | GERMAN | 18 | LADDER MARS | 34 | WINNER RODAN |
| 3 | ITALIAN | 19 | LADDER BOSS | 35 | WINNER MECHAGOD |
| 4 | SPANISH | 20 | LAVA | 36 | WINNER MOTHRA |
| 5 | LEGAL | 21 | ICE | 37 | WINNER MEGALON |
| 6 | WAYFORWARD | 22 | ICE2 | 38 | WINNER TANK |
| 7 | LANGUAGES | 23 | MOON | 39 | RESULTS |
| 8 | TITLE | 24 | MARS | 40 | GAMEOVER |
| 9 | MODE | 25 | MARS2 | 41 | MULTIERR |
| 10 | CUSTOM | 26 | CITY | 42 | MULTIBOOT |
| 11 | VERSUS | 27 | BOSS | 43 | MULTIPLAY |
| 12 | SELECT | 28 | BONUS0 | 44 | MULTIBOOT2 |
| 13 | LADDER | 29 | BONUS1 | 45 | MULTIPLAY2 |
| 14 | LADDER CITY | 30 | BONUS2 | 46 | CREDITS |
| 15 | LADDER ICE | 31 | WINNER | | |

The screen draws indices 0–39 as two columns of 20; indices 40–46 exist in the table but were
not observed on the displayed page (cursor VM 0–49).

### 6.2 Scene-descriptor table at 0x080F17C0

20 records `{0x0C, name_ptr, data_ptr}`; the names are the human-readable scene labels:
`Title`, `Godzilla Stage`, `Rodan Stage`, `MechaGodzilla Stage`, `King Ghidora Stage`,
`Mothra Stage`, `Megalon Stage`, **`Mystery Boss Stage`**, `Credits`, `Bonus Round`,
`Monster Select`, `Before Battle`, `Stage Results`, `Next Challenge`, `Boss Location`,
`Continue`, `Game Over`, `Final Results`, `Ending One`, `Ending Two`.

### 6.3 No code tables

`strings -t x -n 4` (48,245 lines) was searched for `password|cheat|code|debug|secret|unlock|character|fighter|hidden|menu|boss|costume`.
The only relevant hits are credits text and the scene tables above. A literal search for the
published CodeBreaker value `0x030425F8` found **no** 32-bit constant in the ROM — the gate is
an ordinary runtime variable, not a cheat string table. No password alphabet, key-mask sequence,
or validator call site exists.

## 6b. Enumeration

* **Debug scene list:** exactly **47** entries (indices 0–46) in the stride-0x20 ASCII table at
  `0x08031BDC`, fully transcribed in §6.1. The screen displays only indices 0–39 as two columns
  of 20; indices 40–46 exist in the table but were not observed on the displayed page (cursor VM
  is 0–49, so their selectability is unproven).
* **Scene-descriptor table:** exactly **20** records at `0x080F17C0` (§6.2), including
  `Mystery Boss Stage`; this is the closed set of scenes the dispatcher can name.
* **Gate byte domain:** `0x030025F8` is a general scene index. Proven bounds: `0x02` is the only
  value that opens the debug list; `0x00` → black, `0x01`/`0x03` → splash, `0x0C` → mode select.
  `crt0` writes `0x01`, and none of the 10 callers of the scene setter `0x08017944` (nor the 4
  direct writers) ever writes `0x02`, so the accepted value is unreachable by controller input in
  retail.
* **Code space:** **empty**. The 48,245-line string census yields only credits text and the two
  scene tables; no password alphabet, key-mask sequence, validator call site, or literal
  `0x030425F8` constant exists. The sole published access is an out-of-scope CodeBreaker RAM write,
  whose `L+R` is the cheat device's activation condition, not a game input.
* **Accepted-input set:** none in scope. The debug scene list is gated by a RAM value that no
  in-game path writes; the confirm-input-to-scene transition is inferred from handler
  `0x0800C1DC` but was not observed (§8), so no player-enterable code is claimed.

## 7. Validation evidence

- **Observed:** gate byte at title/mode-select = `0x0C`; setting it to `0x02` produces the debug
  list with no input (`s_gate2_nolr.png`); values 0/1/3/0x0C do not (`gate_*.png`); cursor moves
  under Up/Down and `0x030017F0` changes (`s_after4down.png`, savestate diff).
- **Derived:** gate predicate and scene dispatcher from Thumb disassembly; 47-entry table decoded
  from `0x08031BDC`; no writer passes 2 from the 10 setter callers + 4 direct writers.
- **Inferred:** the `AGBJ` header at `0x49A78` is a multiboot link-play image (based on its
  header shape and the `*LINK PLAY PROGRAMMING:` credit).
- **Unresolved / tooling limitation:** pressing A/Start/L/R/B/Select on the debug list did not
  produce a visible scene jump in my runs (screenshots `btn_c_*.png`); the selection handler at
  `0x0800C1DC` implies it should, so the exact activation input remains *inferred, not observed*.
  Some normal scenes rendered as dot-patterns when reached via savestate load into a fresh
  instance (`s_story_select.png`) — a savestate/VRAM artifact of the analysis method, not a
  claim about the game.

## 8. Unknowns

- The exact confirm input that turns a highlighted debug-list row into a scene jump (the handler
  exists; I could not observe the transition).
- Whether indices 40–46 are selectable from the displayed page.
- The purpose of the `AGBJ` multiboot payload's own menu.

## 9. Tooling

- `arm-none-eabi-objdump -M force-thumb` for targeted disassembly; Python + Capstone for literal
  and BL-target scans; `strings -t x`; Python zlib decoder for mGBA `.ssN` `gbAs` chunks.
- `dbg_server.py` / `dbg.py` / `key2.py`: persistent mGBA `-d` pty debugger over a Unix socket,
  with RAM read/write, breakpoints and watchpoints. `gate_test.py`, `scene_enum.py`, `enum_all.py`
  automated the gate-value/enumeration experiments.
- No ROM or copyrighted graphics are redistributed; only addresses, hashes and findings here.
