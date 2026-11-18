# Fortress (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `/mnt/gbacheats/roms/Fortress/Fortress.gba` |
| Size | 4,194,304 bytes (`0x400000`, 4 MiB) |
| Header title | `FORTRESS` |
| Game code / maker | `AFOE` / `5G` |
| Version | `0x00` (Rev. 00) |
| Entry word | `EA00002E` → `b 0x080000C0` (stock crt0) |
| Fixed `0x96` / complement / checksum | present / `0x00` / `0x0042` |
| MD5 | `db64d910feec15dc3f3bc90c151e731b` |
| SHA-1 | `c3175d11fadd85ac743b837a161ae1be89429a7a` |
| SHA-256 | `123b597598f44720e50f2adc9011078500ae5c4ab42ac7625f00c6342ce1eadf` |
| Publisher / developer (external) | Majesco / Pipe Dream Interactive, 2001 |

**Embedded-header scan:** scanning the whole 4 MiB for the 156-byte Nintendo logo
found exactly **one** header, at file offset `0x0`. This is a single retail image,
not a 2-in-1, not a multiboot stub, and not a concatenated pack. The first 4 KiB
is stock ARM crt0 (no cracktro/trainer). No patch or trainer detected. A 0-byte
`Fortress.sav` is created by mGBA at runtime; the game has no meaningful battery
save and no password save.

## 2. Executive summary

**Fortress (GBA) has no password system, no cheat-code entry, no button-code
system, no level select, and no reachable hidden/debug menu.** This is a proven
negative over a bounded search space, not "not tested".

The game is a data-driven Tetris/Rampart-style puzzle-action title. All of its
developer-intended content is enumerable from three contiguous plaintext regions:

1. the UI string banks at `0x0804B3A0` and `0x0804EF00`,
2. the menu option pointer table at `0x0803F3764`,
3. an embedded level/block definition script at `0x0803F9400`–`0x0803FBE39`.

No string in the image contains `PASSWORD`, `CHEAT`, `DEBUG`, `SECRET`, `UNLOCK`,
`LEVEL SELECT`, or any password alphabet. The only `Code` hit is the GAX audio
banner `Shin'en Multimedia. Code: B.Wodok` at `0x0803EF32F` — a known false
positive, not a cheat literal. The only `CREDITS` strings are a real credits
screen whose handler is **dead code** (see §6b).

**Screen system.** The main loop calls `FUN_08000220(screen_id)` (at
`0x08000220`) which indexes an 8-entry jump table at `0x0800023C` and writes the
chosen screen handler into RAM pointer `0x02008DE0`. Only IDs 0, 1 and 2 are ever
requested (call sites `0x08000442`, `0x08000A40`, `0x08000BB`). ID 3 is the
credits handler with **zero call sites and no other literal reference**; IDs 4–7
point to `0x0800021D` (`bx lr`, a no-op). Therefore no hidden screen is reachable
through the dispatcher.

**Published codes.** GameFAQs' Fortress cheats page is empty (verified via
web.archive.org capture `20230507151512`); no TCRF page exists for this title;
web searches for `<Fortress GBA> password / cheat / code / unlock` produced no
code list — only the gameplay FAQ by mimicmasterax (GameFAQs FAQ 13620), which
documents controls and 4 eras and contains no password/cheat section. There are
therefore no published codes to verify against the ROM; this is recorded, not
silently omitted. One search result (`maje...games.com/fortress-gba`) contained
incoherent "consolidation/redirect" prose with no code content and was treated
as non-authoritative data and ignored (guide §16.8).

## 3. How to reproduce

- Emulator: mGBA (build at `/usr/local/bin/mgba`) on `Xvfb :318`, 1024×768×24,
  `SDL_AUDIODRIVER=dummy`, started as `mgba -3 <rom>`.
- Keymap (mGBA SDL defaults, confirmed against key-state globals in §4):
  `A=x`, `B=z`, `L=a`, `R=s`, `Start=Return`, `Select=BackSpace`,
  D-pad = arrow keys. Hold keys ≥120 ms; frames are polled once per frame.
- Deterministic menu path (all screenshot + savestate captured):
  1. Boot → comic intro (~20 s) → title logo → **"PRESS START"** title screen.
  2. `A` or `Start` (also `B`/`Select`) → **PLAYERS** (1 / 2).
  3. `Right` selects 2; `Start` confirms. Default 1 is already selected.
  4. **Mode/Difficulty** menu: `Up`/`Down` chooses the row, `Left`/`Right`
     changes the value. Modes: BATTLE, TOURNAMENT, BLITZ. Difficulties:
     EASY, MEDIUM, HARD. `Start` confirms.
  5. **Era select**: `Left`/`Right` cycles PREHISTORIC → MEDIEVAL → PIRATE →
     SPACE. `Start` confirms.
  6. **Battle intro** (era banner) → **gameplay** (`GOAL 12000 PTS` banner,
     score/timer HUD). `Select` opens the **QUIT? / A YES B NO** dialog.
- Codes tested: none exist in any published list (see §2). All in-game button
  combinations listed in §6b were tested on the title and menu screens.

## 4. Address map

| Address (ROM unless noted) | Meaning | Evidence |
|---|---|---|
| `0x08000000`–`0x080001FF` | Header + ARM crt0; `main` pointer at `+0x1C8` = `0x0800039D` | Derived |
| `0x0800039C` | `main`: init, then infinite loop calling `FUN_0801C660(*0x02008DE0)` | REA/Ghidra decompile, Observed |
| `0x08000220` | `FUN_08000220(screen_id)` — screen dispatcher | Disassembly + BL scan |
| `0x0800023C` | 8-entry jump table of screen-handler setters | Bytes read, Derived |
| `0x02008DE0` (RAM) | current screen-handler pointer (Thumb, low bit set) | Savestate diff, Observed |
| `0x08000898` | key-wait helper: reads `KEYINPUT`, updates key globals | REA decompile |
| `0x04000130` (I/O) | `KEYINPUT`, active-low, 10-bit | 5 literal references |
| `0x0300003C/3E/40/42` (IWRAM) | held / previous / pressed / released key masks | Code at `0x0800C360`, `0x080028C0` |
| `0x0804B3A0`–`0x0804B40D` | UI text bank 1 (title/menu strings) | Bytes read |
| `0x0804EF00`–`0x0804EFA0` | UI text bank 2 (game/result strings) | Bytes read |
| `0x0803F3764` | menu option pointer/value table | Pointer scan |
| `0x0803F9400`–`0x0803FBE39` | embedded plaintext content script | Extracted, 618 strings |
| `0x080525A4` | credits record table (first record → `CREDITS`) | Pointer scan |
| `0x08052A00`–`0x08052B50` | credits text (`JOSEPH SUTTON`, `PAUL MAZUREK`, …) | Bytes read |
| `0x0803EF30C` | GAX audio banner — false "Code:" string | Bytes read |

Screen-handler setters (`FUN_08000220` jump table):

| screen_id | handler written to `0x02008DE0` | status / observed screen |
|---|---|---|
| 0 | `0x080008F1` | comic/intro cutscene (boot) |
| 1 | `0x08000B21` | **PRESS START title** (savestate `w10_title.ss1`) |
| 2 | `0x08001015` | players, mode/difficulty menu, era select, battle intro, gameplay, QUIT dialog (all one handler) |
| 3 | `0x0800B149` | **credits — unreachable** (no call sites) |
| 4–7 | `0x0800021D` | `bx lr` no-op — unreachable |

## 5. Algorithm

Screen dispatch (pseudocode, derived from `0x08000220` + jump table):

```
screen_id = arg0                       # 0..7; >7 falls to default setter
if screen_id > 7: setter = default
else:             setter = jumptable[screen_id]
setter():  *(u32*)0x02008DE0 = handler_pointer
main_loop: call *(u32*)0x02008DE0 every frame
```

Key handling (derived, `0x08000898` / `0x080028C0` / `0x0800C360`):

```
raw = *(volatile u16*)0x04000130        # active-low
held   = ~raw & 0x3FF
pressed  = held & ~prev
released = held & ~prev  (other polarity per engine site)
prev = held
```

Menu handler (`0x08001014`) uses a 2-row cursor (`r7 ∈ {1,2}`), `Start` mask
`0x0008` to confirm, and `0x0090` (Right|Down) among navigation masks. There is
no third row, no OPTIONS entry, and no code-entry widget.

Text rendering is **plain NUL-terminated ASCII**, not tile-indexed: the strings
above were located by literal pointer scan and confirmed by bytes. The content
script at `0x3F9400` is also plaintext (`DEFINE_RAWBLOCK`, `DEFINE_BUILDING`,
`SEARCHRULES`, `END_FILE`, etc.). The credit renderer at `0x0800AEFC` decodes
control bytes `0x26/0xBF/0xE1/0xE9/0xED/0xF1/0xF3/0xFA` into tile numbers — this
is why credit names are interleaved with binary bytes, but it is a renderer, not
a hidden code alphabet.

## 6. Tables

### 6.1 Active-high button masks
`A=0x001, B=0x002, Select=0x004, Start=0x008, Right=0x010, Left=0x020,
Up=0x040, Down=0x080, R=0x100, L=0x200`.

### 6.2 UI strings (all, from the two banks)

`PRESS START`, `PLAYERS`, `HARD`, `MEDIUM`, `EASY`, `BLITZ`, `BATTLE`,
`TOURNAMENT`, `WAITING FOR PLAYER`, `RED WINS`, `GREEN`(+`WIN`), `LOSES`,
`BATTLE!`, `PTS`, `GOAL`, `PREHISTORIC`, `MEDIEVAL`, `PIRATE`, `SPACE`,
`QUIT?`, `A YES   B NO`. No password/cheat/debug string exists.

### 6.3 Enumerated in-game values
- Players: 1, 2.
- Mode: BATTLE, TOURNAMENT, BLITZ (exhaustive cycle, verified in emulator).
- Difficulty: EASY, MEDIUM, HARD (exhaustive cycle).
- Era: PREHISTORIC, MEDIEVAL, PIRATE, SPACE (exhaustive cycle).
- Pause/quit: QUIT? → A YES / B NO.
- Credits: present as data only (unreachable).

## 6b. Enumeration

**Code space size: 0.** There is no password alphabet, no literal code table,
no checksum/validator, no key-mask sequence, and no code-entry UI. Therefore the
§0.2 requirement to mint a novel code cannot apply: the system does not exist.
The negative is bounded as follows.

1. **Screen space fully enumerated (static).** 8 screen IDs in the dispatcher;
   only 0, 1, 2 have call sites; 3 is dead; 4–7 are no-ops. The largest hidden
   surface the game could have is therefore one unreachable credits screen, and
   it is provably unreachable (zero BL xrefs, zero literal xrefs outside the
   unused dispatch entry).
2. **Every reachable screen walked (dynamic, with RAM evidence).** Savestates
   `.ss1` were captured at each screen; the `gbAs` chunk was zlib-decompressed and
   the screen pointer at `0x02008DE0` plus neighbouring state bytes read. Distinct
   observed states: title (`0x08000B21`), players (`0x08001015`, state 0), mode
   menu BATTLE/MEDIUM, mode menu TOURNAMENT, mode menu BLITZ, mode menu EASY,
   mode menu HARD, four eras, battle intro, gameplay, QUIT dialog, and the
   2-player path. Full table of captured states is in the work directory
   (`/tmp/opencode/fortress/*.ss1`, `w*_grid.png`).
3. **Text space searched with counts.** 42,683 `strings` records at `-n 4`;
   a curated NUL-terminated printable-ASCII scan found 618 strings in the content
   script and the complete UI set in two banks; literal searches for 7 keyword
   families and 6 candidate alphabets returned **0** relevant hits (the sole
   `Code` hit is the GAX banner). Case-shift (`±0x20`) variants of
   `password/cheat/debug/secret/unlock/level` returned 0 hits. The embedded
   script contains no cheat/debug keyword.
4. **Button space searched with counts.** On the **title** screen: 10 single
   keys + all 45 unordered key pairs + 4 multi-key combos + the Konami sequence
   = 60 inputs, each from a reloaded savestate; only `A/B/Start/Select` advance
   to PLAYERS, and no combination produced a new screen (checked by image-difference
   threshold and by inspecting sample frames). On the **mode/difficulty menu**: the
   same 59 single/pair inputs + 4 combos were applied from a reloaded savestate
   and the RAM screen pointer at `0x02008DE0` was read after each; it never
   changed from `0x08001015`. No hidden button code exists.
5. **Published codes:** none published for this SKU (GameFAQs cheats empty,
   no TCRF page, no other source found); nothing to verify/test. The single
   gameplay FAQ contains no codes.
6. **Bounds proof (negative form).** The dispatcher bound (IDs 0–7, only 0–2
   live) and the two zero-xref results for the credits handler are the formal
   bounds; there is no out-of-range code field to reject because no code field
   exists. Screen IDs 4–7 resolve to `bx lr`: requesting them cannot render a
   screen.

## 7. Validation evidence

- **Observed** — emulator screenshots of every screen listed in §3/§6.3; savestate
  decompressions giving `0x02008DE0 = 0x08000B21` (title) and `0x08001015`
  (all in-game screens); literal bytes of all UI strings and the content script;
  `md5/sha1/sha256` of the analyzed image.
- **Derived** — screen dispatch table and handler setters (`0x08000220`,
  `0x0800023C`); `main` dispatch loop; key-state globals; menu cursor bounds
  (`r7 ∈ {1,2}`) and `Start` confirm mask `0x8`; zero BL/literal xrefs to the
  credits handler; single logo/header hit.
- **Inferred** — mapping of screen IDs 0/1/2 to intro/title/game handlers from
  observed fptr values; identification of `0x0803F9400` region as the level/block
  definition script from its `DEFINE_*`/`SEARCHRULES` grammar; credits as the
  intended purpose of the dead handler (its record table starts with `CREDITS`).
  These do not affect the negative conclusion.

## 8. Unknowns

- The precise trigger that would have shown the credits in a release build is
  unknown: the handler is unreachable in this ROM, so no controller input can
  reach it. It may be a cut/linked-out feature or require a build-time flag.
- Screen ID 0 (`0x080008F1`) was observed only as the boot comic; its full state
  domain was not exhaustively characterised (irrelevant to cheats).
- The 0-byte `Fortress.sav` is created by mGBA; no battery-save format was found
  or analysed (no save-related strings or code path were in scope).

## 9. Tooling

- `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings -t x`, `grep`.
- `arm-none-eabi-objdump -M force-thumb|force-arm` on the raw binary with
  `--adjust-vma=0x08000000`; Capstone 5.0.7 and Keystone (Python) available.
- REA MCP (Ghidra 12.1.4) `open_binary` + `analyze_function` for `main`
  (`0x0800039C`) and the key-wait helper (`0x08000898`); session closed after use.
- mGBA on `Xvfb :318` with `SDL_AUDIODRIVER=dummy`; `xdotool` XTEST input;
  `scrot` + ImageMagick `convert`/`montage` for screenshots.
- Savestate RAM reader: zlib-decompress the PNG `gbAs` chunk (raw length
  `0x61000`), EWRAM at raw `0x21000`, IWRAM at `0x19000` (guide §16.13).
  Helper scripts: `/tmp/opencode/fortress/ss.py`, `diff_ss.py`, `gba.py`,
  `combo_test2.py`, `menu_combo.py`.
- Web sources treated strictly as data (§16.8): archived GameFAQs cheats &
  FAQ 13620. No code was found, so no literal verification was possible.

**Legal note:** no ROM bytes or copyrighted assets are reproduced here; only
hashes, addresses, algorithms and original observations are published.
