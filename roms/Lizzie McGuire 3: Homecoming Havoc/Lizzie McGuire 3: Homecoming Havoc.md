# Lizzie McGuire 3: Homecoming Havoc (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Lizzie McGuire 3: Homecoming Havoc/Lizzie McGuire 3: Homecoming Havoc.gba` |
| Size | 8,388,608 bytes (0x800000) |
| Header title | `LIZMCGUIRE3` |
| Game code / maker | `BL3E` / `4Q` (`file(1)` prints the combined `BL3E4Q`) |
| Revision | 0x00 |
| Entry word | `0xEA00002E` = `b 0x080000C0` (stock) |
| Header complement / checksum | stored `0x98` / `0x0000`; recomputed complement over `0xA0..0xBC` is `0xB1` → header was edited/rebuilt, but no trainer or multi-image patch found |
| MD5 | `aef559ca2b6f1ee37c423b46bb4ff909` |
| SHA-1 | `991f6fa3ea46f00b3a1e553ea89c4aafc4f2e8a6` |
| SHA-256 | `22116dea071553ffa5967a44dfa9815a3ef6a7389da3f479e61113bea16b0327` |

**Embedded-header scan:** a full-file scan for the 156-byte Nintendo logo found exactly **one** hit, at file `0x4` (header base `0x0`). There is no second game image, multiboot stub, appended trainer, or cracktro: the entry branch is the stock `b 0x080000C0`, and the first 4 KiB disassembles as a normal crt0. The header-checksum mismatch is a metadata artifact, not a code patch.

**Sibling check (Lizzie McGuire 2: Lizzie Diaries):** verified independently from the file only (no contact with display :315). It is a different image (4 MiB, title `LIZZIE 2`, code `BL2E`, MD5 `5f98ec175e2c67d3ba28504c1706dc07`). Only 880 shared *non-zero* aligned 16-byte blocks exist, concentrated at low file offsets (generic GBA runtime/library code); there are **no shared RTTI class names**, no shared asset names (`Liz_mainmenuBG.bmp`, `UnlockedGames`, `AimIt:001_ShoveUnderBed` are absent from the sibling), and no shared code/data relevant to cheats. Nothing from that analysis was carried over; the findings below stand on this image alone.

## 2. Executive summary

**There is no in-game cheat, password, button-code, or hidden debug-menu system in this ROM.** No published in-game codes exist for this SKU: the 3rd party cheat index cheat page (archived 2023-03-04) has no entries, 3rd party cheat index lists a single non-cheat gameplay tip ("Easier game" — *read the key words*), and the only numeric "codes" on the web are GameShark memory-edit codes (3rd party cheat indexes: master, 999 tokens, start with high score), which are explicitly out of scope. No password/cheat/secret/unlock/debug literal occurs anywhere in the 8 MiB in ASCII, UTF-16LE, UTF-16BE, or UTF-32.

Every reachable screen was walked to completion with screenshots and RAM confirmation: title → profile select → main menu (Options, Credits, Competition, Trials, Prizes) → Options (Music/SFX) → High Scores → Single Game → Choose Type (10 categories) → Prizes (card exchange) → Competition (cutscene → microgames) → Pause. No hidden or debug entry exists on any of them. The full C++ RTTI class-name set contains 16 `C*Menu`/`C*Mgr`/`C*API` classes and no debug class; the only "test" leftover is a `TestAniGroup` with four `TEST_ANI_ITEMn` resource names (a resource-manifest entry, not a reachable menu).

Static input analysis found a single hardware-key read (`KEYINPUT` literal at `0x08004684`, used once at `0x08004622`), a single logical-button mapping table (`0x0812DA00`, 15 entries), and one button-mask enum table (`0x0813AA40`, referenced only by menu-item binding code at `0x0800AB80`, `0x0800AC6C`, `0x0800B1BC`). A whole-ROM scan for button-mask sequences found 44 runs of five or more consecutive single-bit masks; all are accounted for as those two tables or compressed graphics data — none is a code sequence. No password alphabet occurs anywhere in the ROM. Eight classic button combinations were pressed on the title and pause screens; all produced only known screens.

Because no system exists, §6b reports the **bounded negative** (spaces searched with counts) rather than minted codes.

## 3. How to reproduce

- Emulator: mGBA 0.10.5 under Xvfb `:319`, `SDL_AUDIODRIVER=dummy`, `mgba -3 <rom>`. Window focus with `xdotool windowfocus`; XTEST key events.
- Keymap (mGBA SDL defaults): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad = arrow keys. Hold keys 50–150 ms with 200–350 ms gaps; the menu carousel swallows faster input.
- Path used:
  1. `Return` at "PRESS START" → "CHOOSE A PROFILE" (three profiles: Super Great, So Awesome, The Coolest).
  2. `x` → "MAIN MENU" (carousel: Options, Credits, Competition, Trials, Prizes).
  3. Up/Down to each entry, `x` to open, `z` to return. Options = Music/SFX with D-pad change; Credits = scrolling text; Trials = High Scores / Play! / Single Game; Single Game → "CHOOSE TYPE" with 10 categories; Prizes = token/card exchange.
  4. Competition → hallway cutscene (advance with `x`) → microgame; `Return` → "PAUSE" (Quit Game, Continue, Options).
  5. Button-code rejection tests: on title and pause, pressed Konami (`↑↑↓↓←→←→BA`), L+R+Start, A+B+Start, L+R+Select, A+B+A+B, L+R+L+R, Start+Start, ↑↓↑↓ and A+B+A. None produced a screen outside the enumerated set.
- RAM evidence: mGBA CLI debugger (`mgba -3 -d`, SIGINT to break, `r/4 <addr>`) and mGBA `.ss1` savestate diffs (PNG `gbAs` chunk, zlib-decompressed). At the title screen IWRAM `0x030005E4`–`0x03000600` holds a run of ROM pointers (`0x0834FB98`, `0x0834FBD8`, …); after entering the main menu those same slots are reloaded with a different run (`0x083450D8`, `0x08345318`, …) and the profile-select run differs again (`0x08348B58`, …). The debugger's PC at the title idle loop was `0x08019DA2`. These distinct, stable RAM images confirm each screen state independently of the screenshots.
- Published codes tested: none applicable. The three 3rd party cheat index codes are GameShark device codes (not ROM literals and not entered through any in-game UI); no in-game code was found to test.

## 4. Address map

| Address (ROM) | File offset | Meaning | Evidence |
|---|---:|---|---|
| `0x08000000` | 0x0 | Header; stock entry `b 0x080000C0` | Observed (bytes, disassembly) |
| `0x0800460C` | 0x460C | `CAGBInputMgr::Update` — reads `KEYINPUT`, builds active-high mask (`mvns`) | Derived (Thumb disassembly) |
| `0x08004622` / `0x08004684` | 0x4622 / 0x4684 | Sole `KEYINPUT` read / its literal `0x04000130` | Derived (whole-ROM literal scan: 1 hit) |
| `0x0800462C`–`0x080046B0` | 0x462C–0x46B0 | 15-entry translation loop over the button map | Derived |
| `0x0812DA00` | 0x12DA00 | Button map: 15 × `{u16 logical, u16 hw mask}`; A=1, B=2, Right=0x80, Left=0x40, Up=0x20, Down=0x10, R=0x100, L=0x200, Start=0x08, Select=0x04 | Derived (dumped bytes) |
| `0x0813AA40` | 0x13AA40 | Button-mask enum `{1,2,4,8,0x10,0x20,0x40,0x80,0x100,0x200,0x400}`; xrefs only in menu binding code | Derived (dump + pointer scan) |
| `0x0800AC30` | 0xAC30 | Menu-item button-binding check: index `[obj+4]` selects a mask from `0x0813AA40`, `ands` with current input | Derived |
| `0x08012D40`–`0x08013B00` | 0x12D400–0x13B00 | Resource manifest: menu/button/card/category/game item names and bitmap names | Observed (`strings -t x`) |
| `0x0813AA58`+ | 0x13AA58+ | Card name pool (`HappyCard`, `FunCard`, `CoolCard`, …) | Observed |
| `0x080343388`–`0x080360000` | 0x343388–0x360000 | Minigame script identifiers (`AimIt:001_ShoveUnderBed`, `Avoid:013_WaterBalloons`, `MultiMove:056_PrinceCharming`, …) | Observed |
| IWRAM `0x030005E4`–`0x03000600` | — | Per-screen ROM-pointer run used as RAM screen-state witness | Observed (CLI debugger `r/4`) |

## 5. Algorithm

No password/validator algorithm exists. The only input algorithm present is the engine's button translation, which is ordinary and contains no sequence state:

```
mask = ~KEYINPUT & 0x3FF                 // active-high
for i in 0..14:
    (logical, hw) = button_map[i]        // table at 0x0812DA00
    if (hw & mask) != 0:
        set pressed/held bits in input object
        dispatch logical button via 0x0801D948
```

The menu layer binds an action to one logical button using the enum at `0x0813AA40` and tests it with a single `ands`/`cmp`; there is no history buffer, no comparison table, and no accumulated sequence anywhere in the input path.

## 6. Tables

**Reachable screens (complete enumeration from walking + RTTI):**

| Screen | Items | Notes |
|---|---|---|
| Title | PRESS START | — |
| Profile select | Super Great, So Awesome, The Coolest | 3 profiles |
| Main menu | Options, Credits, Competition, Trials, Prizes | 5-item cyclic carousel |
| Options | Music On/Off, SFX On/Off | D-pad to change |
| Credits | Disney Interactive | — |
| Trials | High Scores, Play!, Single Game | 3 items |
| High Scores | 1ST / 2ND / 3RD | all 0 on fresh profile |
| Choose Type | 10 categories | Multi-Tap, Rapid-Tap, Balance, Time-Tap, Aim It, Avoid It, Multi-Move, In Motion, Do It, Hodgepodge |
| Prizes | token balance + cards | cards: Cool, Friendship, Fun, Happy, Hug, Mystery, Pop, Replay, Stumble, Style, Wild, etc. |
| Competition | hallway cutscene → microgames | 10 stages, progression-based, no level-select screen |
| Pause | Quit Game, Continue, Options | 3 items |

**RTTI class names (complete set found in the image):** `CInputMgr`, `CMainMenu`, `CSoundMgr`, `CPauseMenu`, `CPrizeMenu`, `CGBAGameAPI`, `CAGBInputMgr`, `CGBASoundMgr`, `COptionsMenu`, `CProfileMenu`, `CUseCardMenu`, `CCategoryMenu`, `CChallengeMenu`, `CSingleGameMenu`, `CCompetitionMenu`, `CScrollingSpriteMenu`. No debug/cheat/test class.

## 6b. Enumeration (bounded negative)

Per §0.2, a negative claim must name the spaces searched and the counts:

| Space searched | Result |
|---|---|
| Published in-game codes (3rd party cheat indexes archive, 3rd party cheat indexes, general web) | **0** in-game codes. 3 GameShark codes (out of scope) + 1 gameplay tip. |
| Keyword literals `password`, `cheat`, `secret`, `unlock`, `debug` in ASCII, UTF-16LE, UTF-16BE, UTF-32 | **0** occurrences of each in all four encodings (8 MiB scanned). |
| Password alphabets (`A-Z`, `a-z`, `0-9A-Z`, consonant alphabet, `1234KLMN…`) | **0** occurrences of each. |
| RTTI/menu class names | **16** classes enumerated; **0** debug/cheat/test classes. Only `TestAniGroup` + 4 `TEST_ANI_ITEMn` resource names exist (not a menu). |
| Reachable screens walked | **12** distinct screens (see §6); **0** hidden/debug entries. |
| Whole-ROM button-mask sequence scan (u16 aligned, strict single-bit masks, runs ≥ 5) | **44** runs; all 44 accounted for: the `0x0812DA00` button map, the `0x0813AA40` enum, and coincidental 4bpp graphics bytes. **0** code sequences. |
| `KEYINPUT` (`0x04000130`) literal references | **1** occurrence (`0x08004684`) → single input path; no second cheat-input poller. |
| Button combinations pressed in emulator (title + pause) | **8** combinations; **0** produced an unenumerated screen. |
| Game text encoding | Visible text is baked into background bitmaps (manifest names such as `Liz_mainmenuBG.bmp`, `Liz_pause.bmp`, `Liz_trialsBG.bmp`); there is no tile-indexed text bank carrying cheat/debug strings. `strings` finds only the resource manifest, so the lack of UI strings is expected and not itself evidence of absence — the screen walk closes that gap. |

Since no code system exists, there is no code space to enumerate and no novel code to mint; the honest §0.2 deliverable here is the proven negative above.

## 7. Validation evidence

- **Observed:** every screen in §6 captured on :319; 8 button combinations applied on title/pause; mGBA `.ss1` savestates for title/profile/main/options; CLI-debugger `r/4` RAM reads at title; single `.sav` (512 bytes) generated, confirming a battery-backed profile save rather than a password system.
- **Derived:** input manager and button tables at the addresses in §4; 15-entry translation loop; single `KEYINPUT` read; menu binding check; RTTI class set; one GBA header and stock entry word.
- **Inferred:** the `TestAniGroup`/`TEST_ANI_ITEMn` entries are leftover test assets (no reachable entry was found; this is a resource-manifest observation, not a proven dead-code path). Header complement/checksum mismatch is attributed to a rebuilt header; no patch payload was found, so this does not affect gameplay analysis.
- **Prompt injection:** no fetched page contained a directive that was acted on; all fetched content was treated as data.

## 8. Unknowns

- The exact semantic meaning of the two unmapped logical buttons in the button map (`a=0x04`, `a=0x08` with `hw=0`) was not exercised — no hardware button reaches them, so they cannot carry a code.
- It was not proven that `TestAniGroup` is unreachable by every conceivable runtime state; it is unreachable through all enumerated screens and has no menu class or binding.
- No save-bit unlockables were exhaustively enumerated; §16.18 save bits are not codes, and the task scope excludes them. The `.sav` is 512 bytes and stores profiles/tokens/cards.

## 9. Tooling

- `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings -t x`, `grep`, Python 3 (struct/re/zlib), `arm-none-eabi-objdump -M force-thumb`, Capstone 5.0.7 (used for literal/BL scan design), mGBA 0.10.5 (`-3`, `-d`, `-g`), Xvfb `:319`, openbox, xdotool, scrot, ImageMagick (`convert`, `montage`, `compare`).
- Local scripts in `/tmp/lizzie3/`: `ui.py` (input/screenshot helper), `ssdiff.py` (mGBA `gbAs` savestate decoder/differ), `walkdbg.py` (CLI-debugger RAM dump driver), plus the button-mask and alphabet scanners.
- No ROM or copyrighted asset is redistributed; only addresses, hashes, and findings are reported.
