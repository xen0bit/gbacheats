# WWE Road to WrestleMania X8 (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `WWE Road to WrestleMania X8.gba` |
| Size | 4,194,304 bytes (`0x400000`) |
| Header title | `WWE_RTWM_X8` (NUL-padded) |
| Game code | `AW8E` (USA), maker `78` (THQ), version `0x00` |
| `file(1)` | `Game Boy Advance ROM image: "WWE_RTWM_X8" (AW8E78, Rev.00)` |
| MD5 | `a208e2f994a69fd8f137b71253534433` |
| SHA-1 | `643e12700404d6b4814e061c7100aecf267a878f` |
| SHA-256 | `9cac8f2f27d859862219bf35adaf799d86eb36fd21af4c28502d680960333bb6` |
| Header checksum / complement | `0x0000` / `0x42` |
| Entry word | `0xEA0FD03E` → branch to `0x0803F4100` |

**Scene-release note (guide §16.1).** Boot shows a cracktro: "Game supplied by: Mick Burns (GGG) / released on: Oct 04th, 2002", followed by the Natsume "DREAM CREATOR" logo. The stock entry branch was repointed from `0x080000C0` to a relocated crt0 copy at file offset `0x3F4100` (`bytes 12 00 a0 e3 00 f0 29 e1 ...`, same instruction stream as `0xC0`). The ROM then runs normally and controller input works. No trainer menu was observed; all data below is from the game proper. Analysis used a byte-identical copy in `/tmp/wwex8/wwex8.gba` (MD5 verified) so the ROM folder stayed clean.

## 2. Executive summary

**Bounded negative: this title has no in-game/developer-intended cheat surface.** There is no password entry screen, no code validator, no button-code sequence table, and no hidden/debug menu reachable by any controller input found. Every "cheat" published on the web for this SKU is an external GameShark/CodeBreaker/Action Replay code (infinite special, max stamina, etc.) — explicitly out of scope — or a gameplay unlockable in the Shopzone.

What the ROM *does* contain, and what was verified:

- A **15-wrestler selectable roster** (confirmed by cycling the whole select screen) and **102 Shopzone merchandise items** unlocked only by save data (fresh save → empty shop).
- A **16th, unreachable name slot `AUSTIN`** in the ROM's name table at `0x08255F5A` (slot 1). The game's 15-byte roster-order table at `0x082560BA` excludes index 1. This is cut content (guide §16.3), **not** a cheat, unlockable, or reachable debug character — no input path to it exists in the build.
- Internal match-type labels (`SINGLE_MATCH`, `TAG_MATCH`, …) and a `vs / AUDIENCE / SATISFACTION / TOTAL POINT` match-setup handler at `0x080425B4`. These are reachable normal-match UI, not a debug menu.
- The global key-state struct and scene dispatcher were located and used as RAM ground truth for all input tests.

## 3. How to reproduce

**Emulator**: mGBA 0.10.5 under Xvfb `:318`, `SDL_AUDIODRIVER=dummy`, `-3 -g` (GDB stub was occupied by another agent, so RAM evidence used savestates — see §9).
**Keymap (verified)**: A = `x`, B = `z`, L = `a`, R = `s`, Start = `Return`, Select = `BackSpace`, D-pad = arrow keys. Hold 60–100 ms (150 ms double-steps menus).

**Menu paths walked (all reachable tooltips/screens)**:

```
Title ("PRESS START")
└── Main menu: Single Play / Multi Play / Data / Options
    ├── Single Play → Challenge Mode / Exhibition Mode
    │   └── Challenge → Championship / King of the Ring / Royal Rumble /
    │       Gauntlet / Pay Per View → NEW GAME / CONTINUE → Select Superstar
    ├── Multi Play       (cursor moves; requires link cable, no local screen)
    ├── Data → SUPERSTARS / TITLE HISTORY / GAUNTLET RANKING / SHOPZONE
    └── Options → Difficulty / Entrances / Flash / BGM / SPX / Credits / EXIT
```

**Input tests performed** (scene pointer at IWRAM `0x03001600` read from savestates before/after):
- Title screen: `L+R`, `L+R+A`, `L+R+B`, `L+R+Up`, `L+R+Down`, `L+R+Left`, `L+R+Right`, `L+R+Select`, Konami (`↑↑↓↓←→←→BA`), `A+B+Start`. First nine left the scene pointer at `0x080591C5` (title); `A+B+Start` advanced normally to `0x0802382D` (main menu).
- Character select: same L+R family plus `Start+Select+A+B` (the last is the emulator's standard GBA reset, not a game cheat), `L+R+A+B`. No change in selected wrestler or scene.
- Boot with `L+R+Start+Select+A+B` held: normal reset to the WWE logo, no debug screen.
- `Start+Select+A+B` is the GBA system reset implemented by mGBA; it is not an in-game code.

## 4. Address map

| Address (ROM unless noted) | Meaning | Evidence |
|---|---|---|
| `0x08000000` | Entry branch → `0x0803F4100` (scene crt0) | Observed (header bytes) |
| `0x080000C0` | Stock crt0 (still present) | Derived (disassembly) |
| `0x080003F0` | **Key-input handler** | Derived |
| `0x08000418` | literal `0x04000130` (KEYINPUT) | Derived |
| `0x0800041C` | literal `0x03001600` (global context) | Derived |
| `0x080591C5` | Title-screen scene handler | Observed (savestate RAM) |
| `0x0802382D` | Main-menu scene handler | Observed (savestate RAM) |
| `0x0802AAB5` | Character-select scene handler | Observed (savestate RAM) |
| `0x08026300`–`0x08026426` | Character-select initializer; copies all 16 names | Derived |
| `0x080425B4` | Match-setup / "vs" screen initializer | Derived |
| `0x08250E80`–`0x08252794` | 102 Shopzone item names, 0x3C-byte stride | Observed (credits/Shopzone text bank) |
| `0x082528CC`–`0x08253F3E` | 109 credits strings (ASCII) | Observed (credits screen) |
| `0x082557E0`–`0x082558BC` | `1-`…`5-`, `SINGLE_MATCH`, `TAG_MATCH`, `CAGE_MATCH`, `TRIPLE_THREAT_MATCH`, `FATAL_4_WAY_MATCH`, `ELIMINATION_MATCH`, `HANDICAP_MATCH`, `RUMBERJACK_MATCH`, `vs`, `AUDIENCE`, `SATISFACTION`, `TOTAL POINT` | Derived (literal pool at `0x8042820`) |
| `0x082558F0`–`0x08255928` | 15 match-handler function pointers (Thumb-bit set) | Derived |
| `0x08255F5A`–`0x08256048` | 16 wrestler names, 15-byte stride (slot 1 = `AUSTIN`) | Observed |
| `0x082560BA` | **15-byte roster order table** (excludes index 1) | Derived |
| `0x08256130`, `0x082561A9` | Font glyph-index tables (even/odd character sets), not password alphabets | Derived |
| IWRAM `0x03001600` | Global context + scene function pointer (`ldr` at +0x0 each frame) | Observed |
| IWRAM `0x0300160E` | **Held keys**, active-high (u16) | Observed (Right press → `0x0010`) |
| IWRAM `0x03001610` | Newly pressed keys (u16) | Derived |
| IWRAM `0x03001612` | Last pressed mask (u16) | Derived |
| IWRAM `0x03001614` | Idle frame counter (caps at 30) | Derived |

**Savestate layout used**: `wwex8.ss*` is PNG with a `gbAs` chunk; zlib-decompress gives 397,312 raw bytes. IWRAM begins at file offset `0x19000`, so IWRAM `0x03001600` is raw-state offset `0x1A600`.

## 5. Algorithm

No password/cheat validator exists to reimplement. The only relevant algorithm is the input sampler, fully recovered at `0x080003F0`:

```
held_raw = ldrh(0x04000130)                 # active-low hardware keys
held     = (~held_raw) & 0xFFFF             # active-high mask, 0..0x3FF
pressed  = held & ~context[0x0E]            # edge-triggered
context[0x10] = pressed
context[0x0E] = held
context[0x12] = pressed ? pressed : context[0x12]   # last pressed
context[0x14] = pressed ? 0 : min(context[0x14]+1, 30)
```

Key-mask convention (active-high): `A=0x001, B=0x002, Select=0x004, Start=0x008, Right=0x010, Left=0x020, Up=0x040, Down=0x080, R=0x100, L=0x200`.

The roster-order table at `0x082560BA` is the 15 bytes
`00 02 0D 03 04 05 06 0E 0B 07 0C 09 0A 0F 08` — i.e. wrestler IDs in select order. Index 1 (`AUSTIN`) is absent; the select loop is hard-bounded to 15 entries.

## 6. Tables

**Wrestler name table, `0x08255F5A`, 16 × 15 bytes:**
`ROCK, AUSTIN, TRIPLE H, UNDERTAKER, ANGLE, JERICHO, KANE, EDGE, TEST, BUBBA, D-VON, RVD, BOOKER T, HOGAN, NASH, CHRISTIAN`.

**Selectable (15), in select order:** The Rock, Triple H, Hollywood Hogan, Undertaker, Kurt Angle, Chris Jericho, Kane, Kevin Nash, Rob Van Dam, Edge, Booker T, Bubba Ray Dudley, D-Von Dudley, Christian, Test. (Observed by cycling the screen; matches published rosters.)

**Shopzone:** 102 item names at `0x08250E80` (0x3C stride); all gated by EEPROM save bits. Save type is 512-byte EEPROM (`wwex8.sav` created by mGBA).

**Font/glyph tables:** `0x08256130` (`0..0x33` with holes) and `0x082561A9` (odd sequence) are glyph-index maps for the ASCII font used on the credits and data screens; they are not a code alphabet. All visible menu labels ("PRESS START", "Single Play", "Challenge Mode", etc.) are pre-rendered tile art with no ASCII literal anywhere in the ROM — confirmed by searching ASCII, `+0x20`-shifted, UTF-16LE/BE and reversed encodings for `PRESS START`, `PASSWORD`, `CHEAT`, `DEBUG`, `SECRET`, `UNLOCK` (0 hits).

## 6b. Enumeration

This title has **no code space to enumerate**. Per guide §0.2, a bounded negative must state the search spaces and counts; those are given here.

**1. Screen space (walked with screenshots/RAM):** 12 distinct screens enumerated — Title, Main menu, Single Play submenu, Challenge submenu, New Game/Continue, Select Superstar (15 entries), Match-setup/VS (static), Options (7 entries), Credits, Data submenu (4 entries), Shopzone, Multi Play (cursor only, link-cable gated). No 5th main-menu item, no unlabelled menu slot, no code-entry field, no hidden character. **Count of reachable menu items: 4 main + 2 single-play + 5 challenge + 4 data + 7 options = 22**, all labelled and exercised.

**2. Input space (button codes):** Input sampler found at `0x080003F0` with active-high masks; 21 controller combinations tested (§3) with the scene pointer at `0x03001600` read from savestates after each. **Result: 0 scene changes attributable to a code.** A raw u16 mask-table scan returned 7,506 candidate runs, but **all 7,506 were false positives** — misaligned reads of 32-bit IWRAM pointer data (e.g. at `0x080264B0` the bytes `38 00 00 03` read as the "mask" `0x300` are actually the IWRAM address `0x03000038`). **Number of genuine button-mask comparison tables: 0.** Boot with `L+R+Start+Select+A+B` held: no debug screen.

**3. Text/alphabet space:** ASCII text bank `0x08250E80`–`0x08253F3E` decoded into **296 strings** (102 shop items, 109 credits strings, 15 internal match labels + misc). Cheat-related keyword hits: **0** (`Special Thanks`, `Test T-Shirt`, `WrestleMania X8 Special` are the only `special/test` matches, all innocuous). Font glyph tables at `0x08256130`/`0x082561A9` contain only digit/letter index runs — no password symbol alphabet. **Alphabets suitable for a password system: 0.**

**4. Validator space:** Thumb PC-relative literal scan for `KEYINPUT (0x04000130)` → **0 code references** (only the 2 literal-pool words at `0x08000418` and the scene-intro copy at `0x083FFA00`); ARM `ldr [base,#0x130]` scan → **0 real instructions**; BL/xref scan for a string-comparison validator over the isolated text bank → **0 callers outside the credits/data render paths**. Function-pointer table scan → **803 runs of ≥5 pointers, all compiler-generated switch jump tables** (e.g. `0x0805C918`, `0x0805EB2C`, `0x0805F02C`); none is a hidden scene/cheat dispatcher. Debug-menu strings: **0**.

**5. Novel code / rejection bounds:** Not applicable — there is no code format, no alphabet, no checksum, and no entry surface; therefore no novel code can be minted and no out-of-range input can be rejected. This is a **bounded negative**, not an untested gap: the counts above bound the search to the entire ASCII text bank, every reachable menu item, 21 input combinations against the live scene pointer, and all 803 function-pointer tables. The 16th wrestler slot exists but is excluded by a hard 15-byte table (`0x082560BA`) with no writer that can be influenced by input — it is cut content, not a hidden unlock.

**6. Unlockables (in scope, but gameplay-gated):** 102 Shopzone items and title-history/gauntlet-ranking data are stored in the 512-byte EEPROM save. The Shopzone is empty on a fresh save and fills via match results; no controller sequence or code was found that sets those bits. These are developer-intended progression rewards, not cheats.

**7. Web recon:** Searches of 3rd party cheat indexes and others returned only external GameShark/CodeBreaker codes and gameplay-unlock lists. **Published in-game passwords/button codes: 0.** (One fetched wiki page asserted "No cheats or unlockables available"; treated as a lead, not authority. No prompt-injection payload was encountered; fetched content was treated as data.)

## 7. Validation evidence

- **Observed**: emulator screenshots of every screen in §3; 15-character cycle; empty Shopzone; credits text; title/main/select scene pointers read from decompressed savestates; held-key mask `0x0010` after pressing Right.
- **Derived**: input-handler pseudocode from `objdump -M force-thumb` at `0x080003F0`; name table, roster-order table, item-count and pointer-table classification from byte-level scans; 16-name copy loop at `0x08026330` with `r4=15` (16 iterations).
- **Inferred**: AUSTIN is leftover cut content rather than a deliberately hidden unlock — supported by its exclusion from the 15-byte order table and the absence of any writer reachable from input, but the original developers' intent was not documented.

## 8. Unknowns

- **Multi Play** screens require up to 4 link cables and were not entered; no evidence of cheats there, but that specific surface is untested.
- In-match pause menu and post-match screens were not walked (gameplay, not code entry).
- Whether AUSTIN's portrait/AI assets beyond the name string remain in the ROM was not exhaustively checked; irrelevant to reachability since the select table excludes him.
- The GDB stub on port 2345 was occupied by another agent, so all RAM evidence came from savestate diffs rather than live watchpoints; this did not limit any conclusion.

## 9. Tooling

- `strings -t x -n 4`, `xxd`, `grep -abo` for the ASCII bank.
- Python scripts in `/tmp/wwex8/`: `scan_ldr.py`, `scan_input.py`, `ssdiff.py` (PNG `gbAs` zlibState extractor + byte diff), plus inline pointer/mask/BL scanners.
- `arm-none-eabi-objdump -M force-thumb` for the input handler and scene initializers.
- mGBA 0.10.5 (`-3 -g`) under Xvfb `:318` + openbox; `xdotool` XTEST input; `scrot`/ImageMagick `montage` for screen enumeration.
- Cleanup: only own PIDs killed by number (Xvfb `:318` and the mGBA instance launched from the workdir); workdir `.sav`/`.ss*` files are outside the ROM folder. No other agent's process or display was touched.

## 10. Legal note

No ROM image or copyrighted assets are redistributed in this report; only hashes, addresses, counts and the author's own tooling are published.
