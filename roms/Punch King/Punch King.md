# Punch King (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Punch King.gba` (8,388,608 bytes = 0x800000) |
| Header title | `PUNCH KING` (0xA0) |
| Game code | `APGE` (0xAC), maker `51` (0xB0) — USA release, Rev. 00 |
| Version / complement / checksum | `0x00` / `0x07` / `0x0000` |
| Entry word | `0xEA1F5EFE` → branch target `0x087D7C00` |
| MD5 | `ddb458b12ca0a684bfab8cebc98c9774` |
| SHA-1 | `803ca50712f08f71b1398abb72325d79fe73f810` |
| SHA-256 | `3e2816fbf585f41883aa17f44514423ba30c1c98da93b189d6ccc461624af752` |

**Embedded-header scan (§0.2/§16.1):** exactly **one** Nintendo-logo hit (file `0x00000004`, ROM `0x08000004`) — a single GBA image, no multi-game pack, no appended trainer. The unusual entry vector is a **scene cracktro bootstrap**: code at `0x087D7C00` sets `sp = 0x03007F00`, branches to Thumb at `0x087D7C0C`, which LZ-decompresses 0x3A74 bytes from `0x087D7D2C` into EWRAM `0x02000000`, calls the decompressed intro, DMA-copies 0x8000 bytes from `0x087D7C3C` back to `0x02000000`, then `bx 0x080000C0` into the stock crt0. Boot text observed: `GBA//US//64MBS SUPPLIED BY: BARONESS / GREETINGS TO ALL OF MODE7`. This is a repack intro, **not** an in-game cheat or trainer menu; ignore it for cheat purposes (it also swallows all input while it plays — wait ~25–30 s or boot from a title savestate).

## 2. Executive summary

**Punch King (GBA) has no developer-intended in-game cheat code system: no password screen, no password validator/table, no on-screen keyboard, no button-code sequence matcher, and no hidden debug menu.** The game's entire interactive surface is a normal arcade boxing game: title → 4-item main menu → 3-item Options (including a *Music Test* developer/QA option) → Arcade/VS/Survival modes → character/arena selection → fight → pause (Resume/Exit). The only unlockable content is boxer progression stored in the cart save (`.sav`), which is ordinary gameplay progress, not a code (§16.18).

All visible text is **plain ASCII** in a bank at file `0x7B4000–0x7B5DF0`; there is no tile-indexed text bank to decode (verified: every rendered label — `MUSIC TEST:`, `CHOOSE OPPONENT`, `ARENA`, `PAUSE`, `SELECT BOXER` — has a literal `strings` hit). A developer-only assertion-failure screen exists at `0x087B5C70`, but no reachable input path leads to it.

Every published "cheat" for this SKU is a GameShark/CodeBreaker/Xploder **RAM patch** (e.g. `Unlock All Fighters 17DB5664 753A`, `BB7B 9D6E 0EEE`, `Infinite health 6725 6B21 4F13`) — explicitly out of scope. The archived 3rd party cheat index cheats page for this game contains **zero** entries.

Because no code system exists, §0.2's "generate a novel code" deliverable is replaced by its mandated negative-result form: full menu/screen enumeration with RAM evidence, plus a bounded search of the strings/tables/key-mask space. No novel code was minted because there is nothing to mint into.

## 3. How to reproduce

* Emulator: `mgba -3 "Punch King.gba"` under `Xvfb :317`, `SDL_AUDIODRIVER=dummy`; keymap A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows. Verify with `KEYINPUT` at `0x04000130` (active-low; held A read `0x03FE` vs idle `0x03FF`).
* To skip the Mode7 intro, save a state on the title screen (`Shift+F1`) and relaunch with `mgba -3 -t <state> "Punch King.gba"` (plain F1 load was unreliable in this SDL build).
* Walk: Start → Main Menu (Arcade / VS Fight / Survival / Options). Options → Music Test (Left/Right cycles 12 tracks), Volume, Credits. Arcade → story dialogue → VS/GET READY → fight → Start → PAUSE (`A RESUME`, `B EXIT`). VS Fight → CHOOSE OPPONENT. Survival → ARENA map select (Left/Right cycles 12 arenas).
* RAM evidence: launch mGBA with `-g`, attach `gdb-multiarch`, `set architecture arm`, `target remote :2345`. Screen-id oracle: byte at IWRAM `0x030005B0` (mirrored at `0x030005B4`). Alternatively decompress `.ss1` savestates: PNG `gbAs` chunk → `zlib.decompress`; layout for this 8 MiB ROM is total `0x61000` bytes, IWRAM at raw `0x19000` → GBA `0x03000000`, EWRAM at raw `0x21000` → GBA `0x02000000`, VRAM at raw `0x1000`.

## 4. Address map

| Item | File offset | ROM address | Notes |
|---|---:|---:|---|
| Header / entry | `0x000000` | `0x08000000` | Entry `0xEA1F5EFE` |
| Cracktro loader | `0x7D7C00` | `0x087D7C00` | ARM→Thumb decompressor, jumps to `0x080000C0` |
| Game crt0 | `0x0000C0` | `0x080000C0` | Stock ARM startup |
| Screen-state setter | `0x1371C4` | `0x081371C4` | Writes screen id to `0x030005B0/B4`; 40 BL call sites |
| Input poller (live) | `0x13A858` | `0x0813A858` | `ldr r0,=0x04000130; ldrh; mvns; & 0xFFFF` → active-high mask |
| Input init / reset | `0x13A9B8` | `0x0813A9B8` | Clears 10 button-state structs |
| Dead input reader | `0x1330B8` | `0x081330B8` | Reads KEYINPUT, XOR `0x03FF`; **0 BL xrefs** (library leftover) |
| Text bank (ASCII) | `0x7B4000–0x7B5DF0` | `0x087B4000–0x087B5DF0` | All UI/dialogue/credits strings |
| Assertion-failure debug text | `0x7B5C70` | `0x087B5C70` | Developer leftover, unreachable |
| Arena name pointer table | `0x14A924` | `0x0814A924` | 12 entries, reverse order |
| Boxer name pointer table | `0x14B738` | `0x0814B738` | 12 entries, reverse order |
| Music track pointer table | `0x14B5D0` etc. | `0x0814B5D0` | 12 tracks (table interleaved with other UI pointers) |
| AI move-pattern table | `0x143570+` | `0x08143570+` | 5-char button strings (`J`, `U`, `g`, `x`, `-`, …) — AI behaviour, **not** codes |
| Screen id (RAM) | — | `0x030005B0` / `0x030005B4` | u8 duplicated |
| Key state (RAM) | — | `0x03004740`, `0x03004840`, `0x03004844`, `0x0300484C` | held / new / old / edge masks |
| Key history (RAM) | — | `0x03004850` (ptr), `0x03004854` (count) | generic input history, no secret comparison found |

## 5. Algorithm

There is no password/checksum algorithm to reimplement. The relevant algorithm is the screen state machine:

* `SetScreenState(u8 id)` at `0x081371C4` writes the id to `0x030005B0` and an adjacent field, frees the previous screen's allocations, and dispatches the new screen.
* 40 BL call sites were enumerated; the immediate ids written are exactly
  `{7, 8, 9, 14, 15, 18, 19, 20, 21, 22, 23, 24, 25, 26, 38}` (a handful of callers pass a computed id).
* Observed live values (savestate byte at raw `0x19000+0x5B0`):
  `7 = Title`, `8 = Options` (Music Test sub-screen keeps 8), `9 = Main menu`, `14 = Survival arena select`, `38 = Arcade dialogue/VS intro`, `50 = VS "GET READY"`, `255 = Fight/Pause`.
* Input is polled at `0x0813A858` into an active-high 16-bit mask (`~KEYINPUT & 0xFFFF`, later masked to `0x3FF`); edge mask and 10-slot per-button history are maintained in IWRAM. No code compares this history against a constant sequence table (search described in §6b).

## 6. Tables

**Main menu (4 items):** Arcade Mode, VS. Fight, Survival Mode, Options. Down at the last item does not wrap.

**Options (3 items, wraps):** Music Test: `<track>`, Volume: `IIII`, Credits.

**Pause (2 items):** `A RESUME`, `B EXIT`. No hidden third entry (see §6b).

**Music Test tracks (12):** Punch King!, America, Russia, Poland, Africa, Australia, Egypt, Japan, India, Mexico, China, England. Pointer table starts at file `0x14B5A0`/`0x14B5D0`.

**Arenas (12):** Tower Bridge London, Jade Pagoda Beijing, Aztec Temple Mexico, Taj Mahal Agra, High Street Kyoto, The Sphinx Giza, Sydney Harbor, Savanna Botswana, Nussboym Steelworks Warsaw, Red Square Moscow, San Francisco Arena, Area 52 (file `0x14A924`).

**Boxers (12 selectable):** Henry Jameson, Wan Jab Lo, Antonio Chavez, Indra Bing, Basho Ishibashi, Tuten Kha Boom, Mick Ayers, Afrika Bambattaya, Otto van Pummelyu, Ivan Tanokyablokov, Bucky Booth, Walter-687 (file `0x14B738`). Tiger Armstrong is the player character (name string at `0x087B4A08`). The manual states up to 12 boxers are unlocked through Arcade progression — save-data progress, not a code.

**Key-mask convention:** `~KEYINPUT & 0x3FF`; A=1, B=2, Select=4, Start=8, Right=0x10, Left=0x20, Up=0x40, Down=0x80, R=0x100, L=0x200.

## 6b. Enumeration

**Search space checked (bounded negative result):**

| Search | Space | Result |
|---|---|---|
| `strings -t x -n 4` over whole ROM | 74,348 strings | Zero hits for `password`, `unlock`, `secret`, `code`, `cheat` as UI/validator text. Only "cheat" hit is story dialogue at `0x7B2CF8` ("…he doesn't cheat!"). "Character Prototyping"/"Character Animations" at `0x7B531C`/`0x7B5360` are **credits role labels**, not a debug menu. |
| Literal known-code search | whole 8 MiB | No published in-game code literal exists to search; all web-listed codes are RAM patches (excluded). |
| Password alphabet / on-screen keyboard | all screens | No text-entry or symbol-selection surface found on any of the ~15 states. |
| Key-mask sequence tables (`u16` runs of single bits, §5.4a) | whole 8 MiB | 16,419 runs of length ≥4; all fall inside graphics/animation data or the AI move-string tables (ASCII letters), none is a button sequence compared by code. No multi-bit combination table (e.g. L+R=0x300) adjacent to a validator. |
| KEYINPUT xrefs | whole ROM | 4 literals: `0x1330C4` (one reader, **0 callers**), `0x13A8FC`/`0x13AA38` (live poller initializer pools), `0x7D7ECB` (cracktro). No hidden gate. |
| Screen-state setter xrefs | 40 call sites | Immediate ids enumerated above; no unlabelled "debug" id, and no input branch selects an unlisted id. |
| Button-combo oracle tests | title/menu screen | L+R, L+R+Start, L+R+Select, Start+Select, Konami sequence, A-B-A-B, Select+A+B, L+R+Down+Select — screen-state byte stayed in the known set (7/9/14/15/38); no hidden screen appeared. |
| Published-code verification | web | 3rd party cheat index cheats page (Wayback 2022-05-07) has **no entries**; 3rd party cheat index list only GameShark/CodeBreaker RAM patches (out of scope). |

**Complete-set statements:** exactly 4 main-menu items, 3 Options items, 2 pause items, 12 boxers, 12 arenas, 12 music tracks, and a screen-state space of 15 immediate ids (+ 255 for combat) were counted from pointer tables and the setter's call sites. Because no code system exists, no novel code was generated and no rejection test applies; the negative is proven over the searched space above rather than by an accepted/rejected code pair.

## 7. Validation evidence

* **Observed (emulator):** every screen listed in §3, screenshotted; keymap confirmed via `0x04000130`; screen-state byte values in §5 read from uncompressed `.ss1` RAM (e.g. `st_title.ss1` → 7, `st_fmenu.ss1` → 9, `st_foptions.ss1` → 8, `st_survival.ss1` → 14, `st_farcade.ss1` → 38, `st_fvs.ss1` → 50, `st_ffight.ss1`/`st_fpause.ss1` → 255). Diffs between savestates confirm RAM changes of 3,728–5,604 bytes per screen transition.
* **Observed (static):** table counts from literal pointer tables; 1 Nintendo-logo hit; 15 immediate screen ids from 40 BL call sites; 0 BL xrefs to the dead input reader.
* **Derived:** cracktro flow from the decompressor disassembly at `0x087D7C00–0x087D7D30` and the final `bx 0x080000C0`; `~KEYINPUT & 0x3FF` mask from `0x0813A858`.
* **Inferred:** the 12-boxer/12-arena/12-track tables are complete because the pointer runs terminate at non-pointer values; a save-data unlock mechanism is inferred from the manual text and the presence of a `.sav`, not from a decoded save format.

## 8. Unknowns

* The save-data unlock format (which bits record the 12 boxers) was not decoded; it is gameplay progression and not a code surface.
* A few screen-state ids (18–26, 15) were enumerated statically but not individually screenshotted (transient battle/result states). None is referenced by a hidden input branch.
* The exact effect of the developer assertion-failure screen at `0x087B5C70` was not triggered; no reachable input path to it was found.

## 9. Tooling

* `arm-none-eabi-objdump -M force-thumb` for raw disassembly; Python `struct`/Capstone-style literal and BL scanners (`blscan.py`, `keyscan.py`).
* `strings -t x -n 4`; `grep -abo` literal searches; custom PNG `gbAs`/zlib savestate decoder (`ss.py`) for RAM reads.
* mGBA SDL under `Xvfb :317` + `openbox`, `xdotool` XTEST input, `scrot` + ImageMagick crops, `tesseract` for label OCR.
* mGBA `-g` GDB stub with `gdb-multiarch` (`set architecture arm`) for `KEYINPUT` verification; `-d` pty debugger evaluated and rejected as unreliable for live reads.
* Web: Wayback Machine snapshot of the 3rd party cheat index cheats page (2022-05-07) and search-result snippets from 3rd party cheat indexes.
* No ROM or copyrighted assets were redistributed. This report intentionally does **not** update `roms/INDEX.md` (per brief).
