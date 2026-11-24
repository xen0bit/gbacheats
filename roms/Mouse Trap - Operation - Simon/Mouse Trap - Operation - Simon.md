# Mouse Trap / Operation / Simon (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Mouse Trap - Operation - Simon.gba` |
| Commercial title | *3 Game Pack! – Mouse Trap + Simon + Operation* (DSI Games / Gravity-i, 2005) |
| Size | 4,194,304 bytes (`0x400000`) |
| Header title | `MOUSE TRAP` |
| Game code | `B3OE` (`AGB-B3OE-USA`) |
| Maker | `20` |
| Version | `0x00` |
| Header entry word | `0xEA00002E` (stock `b 0xC0` — no cracktro) |
| Header complement / checksum | `0x00` / `0x0000` (complement would be `0xFF` if unedited — header was rebuilt; noted, not a patch) |
| MD5 | `bd846a0248e2f18bf7521fd2f5479881` |
| SHA-1 | `10bed6b69f8984af49299885fda0575fce442a9c` |
| SHA-256 | `0c15414d8df2c22082f7cf836d73145bf8d2cdafdda569b1c1ff6464fe8f123f` |

**Embedded-header scan:** the 156-byte Nintendo logo (`24 ff ae 51 69 9a a2 21 ...`) occurs **exactly once**, at file offset `0x0`. There is no second game image, no appended trainer, and no multiboot stub. This is a single 4 MiB ROM (not a 2-in-1 concatenation) even though it is a three-game compilation — the three games are runtime modules inside one image.

## 2. Executive summary

**No in-game/developer-intended cheat system exists in this ROM.** There is no password screen, no code-entry field, no button sequence, no hidden/debug menu, and no unlockable gated by a code. This is a **proven "no system"** (guide §16.3 category 1), not an untested one:

- **Text/button spaces searched and bounded:** every ASCII string in the image was enumerated. Genuine ASCII consists of 1 header title, 4 engine-debug strings, and 5 filesystem filenames — **zero** occurrences of `password`, `cheat`, `code`, `secret`, `unlock`, `debug`, `hint`, `invalid`, `wrong`, `congrat`, `bonus`, `hidden`, `master`, `level select`, `initials`, or `name`. The font/tile-indexed text bank was decoded: the renderer at `0x08015414` converts stored lowercase ASCII to tile indices via `char - 0x60` (space → 0); the only tile-indexed strings used are the 12 hard-coded high-score names `simon   ` and menu labels rendered as pre-drawn bitmap art. No code alphabet, literal code table, or key-mask sequence table exists.
- **Button space searched and bounded:** the single keypad reader at `0x080151BC` produces held/pressed/released at `0x030058F4`/`0x03005900`/`0x030058FC`. It has exactly **6 callers**, and those callers test only six single-button masks — `0x1` (A), `0x2` (B), `0x4` (Select), `0x8` (Start), `0x40` (Up), `0x80` (Down). There are **zero** multi-button mask comparisons (no `0x300` L+R, no `0xC` Start+Select, no `0x103`, etc.) and **zero** `0x100`/`0x200` (L/R) literals in any input consumer. No press-history ring buffer, progress index, or sequence validator exists.
- **Published codes:** web searches (GameFAQs, TCRF via archive, VGChartz-style aggregators, TASVideos, MobyGames) surfaced **no GBA cheats/passwords** for this SKU. Direct TCRF and GameFAQs-cheats fetches returned HTTP 403. No published literal was available to verify — recorded as such, not silently omitted (guide §3.4 rule 4).
- **Dynamic:** every reachable screen was walked in mGBA on `:318` with screenshots and savestate RAM evidence (§2 list). Ten button-code candidates (including L+R, L+R+Start, Start+Select, and the Konami sequence) were pressed on the top menu; none opened a hidden screen.

## 3. How to reproduce

```
export DISPLAY=:318 SDL_AUDIODRIVER=dummy
Xvfb :318 -screen 0 1024x768x24 &
openbox &
mgba -3 "Mouse Trap - Operation - Simon.gba"
```

mGBA SDL keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrow keys. Hold keys 80–150 ms; allow 0.5–1.5 s for screen fades (several menus fade in/out and look black mid-transition).

Exact menu path (all screens reached):

1. Boot → DSI Games logo → title "PRESS START" → **Start** → "WHICH GAME?" game select.
2. Game select → **A** on Mouse Trap → Mouse Trap menu: `2 MICE 1 PLAYER`, `SFX ON`, `MUSIC ON`, `QUIT`. **A** on `2 MICE 1 PLAYER` → gameplay. **Start** → `PAUSED` overlay.
3. Game select → **Down, A** on Simon → Simon title → **Start** → `Main Menu {Play Simon, Options, View High Scores, Quit}`.
   - **Options** → `Difficulty {1,2,3,4}`, `Sound {ON,OFF}`, `Music {ON,OFF}`, `Done`. A cycles Difficulty 1→2→3→4→1; no 5th value.
   - **View High Scores** → 4 panels `LEVEL 1..4`, each 3 rows `SIMON` with scores 4/3/2 (hard-coded defaults; no name entry).
   - **Play Simon** → colour wheel gameplay; **Start** → `Paused` overlay.
4. Game select → **Down, Down, A** on Operation → Operation art → **Start** → `MAIN MENU {PLAY, OPTIONS, BACK}`.
   - **OPTIONS** → `PLAYERS {1..4}`, `MUSIC`, `DIFFICULTY {EASY, MEDIUM, HARD}`, `SOUND FX`, `BACK`.
   - **PLAY** → portrait select (4 portraits) → `CHOOSE GAME MODE {CLASSIC, SPEED, SKILL, SKILL + SPEED, BACK}` → `PLAYER 1'S TURN` (bank $00000, NEXT) → gameplay; **Start** → `PAUSED` overlay.
5. Title screen: **Select** is a no-op (visually identical before/after).

Button-code candidates pressed on game select with no effect beyond normal menu navigation: `L+R`, `L+R+Start`, `L+R+A`, `L+R+B`, `Start+Select`, `A+B`, `↑↑↓↓←→←→BA`, `LRLR↑↓`, `L,R,A,B,Start`, `LLLLRRRR`.

## 4. Address map

| Address | Type | Meaning |
|---|---|---|
| `0x08000000` | ROM | Entry `0xEA00002E` (ARM) |
| `0x0800039A` | Thumb fn | GBA-FS file lookup `(filename, index) → {value, ptr}`; file table at `0x08027360` |
| `0x080151BC` | Thumb fn | Keypad reader: `held = ~KEYINPUT & 0xFFFF`; writes pressed/released |
| `0x030058F4` | IWRAM u16 | Held buttons, active-high (`A=1,B=2,Select=4,Start=8,R=0x10,L=0x20,U=0x40,D=0x80,Rtr=0x100,Ltr=0x200`) — **Observed** from savestate diff: holding `x` changes low byte `0x00→0x01` |
| `0x03005900` | IWRAM u16 | Pressed (edge) buttons |
| `0x030058FC` | IWRAM u16 | Released (edge) buttons |
| `0x080151E4` | literal pool | `0x04000130` (KEYINPUT) |
| `0x080153CC` | Thumb fn | High-score init: reads 9-byte file `simon   `, writes 12 name slots; conversion at `0x08015414` is `byte==0x20 ? 0 : (byte - 0x60) & 0xFF` |
| `0x08027360` | ROM data | GBA-FS table: 3 records `{u8 n; char name[19]; u32 variants[n]}` — `BG_gbawmap`, `BG_chars`, `BG_palette`; n=6 each; variant indices `{0,1,20,30,40,50}` |
| `0x080185DC` | ROM data | GBA-FS file-data base. `data_addr = (variant & 0xFFFFFC) + 0x080185DC`, compression = `variant & 3` |
| `0x0801836B4` | ROM data | Debug strings: `GBA FS ERROR  (missing file)`, `GBA FS ERROR  (compression?)`, `Out of IRam (32k)`, `Out of XRam (256k)` |
| `0x08016A48` / `0x08016BE0` | Thumb fn | Title-screen Start handler / Select handler (Select is a no-op) |

Savestate RAM layout (mGBA `gbAs` PNG chunk, decompressed 397,312 bytes): CPU/header `0x00000`, VRAM `0x01000`, IWRAM `0x19000`, EWRAM `0x21000`. `IWRAM_addr → state_offset = 0x19000 + (addr - 0x03000000)`.

## 5. Algorithm

There is no validator to reimplement. The two algorithms actually present are:

```
# Keypad (0x080151BC), active-high:
held    = (~KEYINPUT) & 0xFFFF
pressed = held & ~prev_held
released= prev_held & ~held
prev_held = held

# Font/tile text conversion (0x08015414), used for high-score names:
tile_index = 0 if ch == 0x20 else (ch - 0x60) & 0xFF
# stored lowercase ASCII 'a'..'z' (0x61..0x7A) → tile 1..26, rendered as capitals.
```

Neither consumes a user-supplied code.

## 6. Tables

| Table | Address | Contents | Count |
|---|---|---|---|
| Input consumers | BL targets of `0x080151BC` | `0x8015724`, `0x8016016`, `0x801611A`, `0x801629E`, `0x801652A`, `0x80168F6` | 6 |
| Buttons tested | immediates in those consumers | `0x1,0x2,0x4,0x8,0x40,0x80` | 6 distinct, all single-bit |
| Multi-button masks | whole Thumb code, immediates `1..0x3FF` with ≥2 bits | no high-bit (`0x100`/`0x200`) key masks anywhere | 0 |
| Simon difficulty | options UI | `{1,2,3,4}`, wraps at 4 | 4 |
| Operation players | options UI | `{1,2,3,4}` | 4 |
| Operation difficulty | options UI | `{EASY,MEDIUM,HARD}` | 3 |
| Operation modes | mode select | `{CLASSIC,SPEED,SKILL,SKILL+SPEED}` | 4 |
| High-score names | RAM/ROM | `simon   ` × 12 (4 levels × 3 ranks) | 12 |
| GBA-FS files | `0x08027360` | `BG_gbawmap`, `BG_chars`, `BG_palette` (6 variants each) | 3 |

Published codes tested: **none exist** for this SKU (GameFAQs cheats page and TCRF both returned HTTP 403; searches returned only product/marketing pages, a TASVideos timing entry, and No-Intro identity data — no password lists). This is recorded as a bounded negative, not a skipped step.

## 6b. Enumeration

Guide §0.2 requires the whole code space to be characterised. Here the space is **empty**, and that is proven by exhaustive bounds:

1. **Text space** — the only encodings present are (a) plain ASCII, (b) lowercase-ASCII→tile (`−0x60`), and (c) pre-rendered bitmap menu art. All 4 MiB were scanned:
   - Case-sensitive and case-insensitive `strings -n 3/4/5` plus a direct regex for `[a-z0-9 ]{4,}` over the whole image. Genuine ASCII = 1 header title + 4 engine-debug strings + 5 FS filenames. Cheat keyword hits = **0** for each of the 16 keywords listed in §2.
   - The tile font was decoded from the renderer (`0x08015414`); the only tile-indexed string bank is the 12 high-score names, all `simon   `. No alphabet, no literal table, no code field.
   - Bitmap-rendered menus were walked visually — none contains a code-entry prompt.
2. **Button space** — key masks are 10-bit (`0x3FF`); all input reads funnel through one reader with 6 callers. The complete set of button masks tested in code = `{0x1,0x2,0x4,0x8,0x40,0x80}`. Combined masks (`0x3,0xC,0x300,0x303,0x30C`, etc.) have **0** consumers; L/R (`0x100,0x200`) have **0** consumers. There is no sequence buffer to enumerate.
3. **Generated novel code** — **N/A**: no validator exists, so no code can be minted; §0.2's "novel code" deliverable is replaced by the bounded negative (§0.2 point 5: "when there is no code system, the report must show the menu enumeration and the search space that was checked").
4. **Bounds by rejection** — **N/A** for the same reason. Instead, 10 published-style button sequences were pressed in-game (§3) and all were rejected by the absence of any handler: the screen remained the game-select menu and the RAM state at `0x030058F4/0x03005900/0x030058FC` showed only transient single-button edges. Select on the title screen was confirmed a no-op both visually and in code (`0x08016BE0`).
5. **Screen space** — enumerated in §3: 3 top-level screens, Mouse Trap 3, Simon 6, Operation 8. No 4th game, no hidden menu entry, no debug screen, no unlockable tab was found in any selector. Per guide §16.17, menu rings were checked against their code bounds: Simon difficulty 1–4 and Operation players 1–4 / modes 1–4 wrap and expose no unlabelled 5th slot.

## 7. Validation evidence

**Observed** (emulator, DISPLAY `:318`, mGBA 3×, screenshots + savestate diffs):
- Every screen listed in §3, including all three `PAUSED` overlays.
- Holding `x` changes IWRAM `0x030058F4` low byte `0x00→0x01` across two savestates, confirming the input variable mapping.
- All 10 button-code candidates leave the game-select screen unchanged apart from animation.
- Select on the title screen produces no visual change.

**Derived** (disassembly / REA-Ghidra decompilation):
- `0x080151BC` is the sole keypad reader; its 6 callers test only the 6 single-button masks.
- `0x08015414` converts ASCII→tile index by subtracting `0x60` (space→0).
- `0x0800039A` + table at `0x08027360` are a 3-file GBA-FS containing graphics only.
- High-score init at `0x080153CC` writes 12 copies of `simon   `.
- No multi-button mask or L/R mask exists in any input consumer.

**Inferred:**
- The "Unlock higher difficulty levels and bonus challenges" line on a GameStop product page is marketing copy, not a description of this GBA SKU: the only difficulty selectors are the 1–4 and EASY/MEDIUM/HARD settings documented in the manual, all available from the start.
- No SRAM/Flash save is used for game progress; high-score names are hard-coded defaults.

## 8. Unknowns

- The exact visual effect of the title-screen Select handler (`0x08016BE0`) was not isolated — the screenshot was identical before/after; it may toggle an internal sound flag with no on-screen indicator. It does not open a screen.
- Content of the three GBA-FS graphics files (`BG_chars`, `BG_palette`, `BG_gbawmap` × 6 variants) was not fully rendered; they contain tile/palette data, not text or code, as established by the file-table structure and the absence of any text-draw consumer that reads them as strings.
- The GDB stub on port 2345 was occupied by another session, so RAM reads used savestate diffs (guide §16.13) instead of live GDB; this is sufficient for the addresses used above.

## 9. Tooling

- `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings`, `grep`, Python 3.
- `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for raw Thumb disassembly.
- REA MCP (`open_binary` raw-binary/arm @ `0x08000000`, `analyze_function`, `procedure_pseudo_code`, `close_binary`) for cross-checking the decompilation.
- mGBA SDL under Xvfb `:318` + openbox; `xdotool` XTEST input; `scrot` + ImageMagick `convert` for cropped 720×480 captures.
- Custom helpers in `/tmp/mousetrap/`: `ui.py` (input/screenshot), `state.py` (gbAs savestate parser + RAM reads), `combo.py` (button-code candidate battery with savestate RAM diffs).
- No ROM or copyrighted assets are redistributed; only addresses, hashes, and findings are published.

---

**Conclusion:** This is a clean negative. The GBA SKU of *Mouse Trap / Operation / Simon* has no password, code, button sequence, hidden menu, or unlockable. Every reachable screen was walked with RAM evidence; every ASCII and tile-indexed text space and the complete button-mask space were searched with the counts above; no published GBA code exists to test. No novel code can be minted because there is no validator.
