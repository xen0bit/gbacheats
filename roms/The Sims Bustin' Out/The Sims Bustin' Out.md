# The Sims Bustin' Out (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `/mnt/gbacheats/roms/The Sims Bustin' Out/The Sims Bustin' Out.gba` |
| Size | 16,777,216 bytes (16 MiB) |
| Header title | `THE SIMS ADV` (12 bytes at `0xA0`) |
| Game code | `ASIE` |
| Maker code | `69` (Electronic Arts) |
| Version | `0x00` |
| Entry word | `0xEA00002E` → `0x080000C0` (stock, unpatched — guide §16.1) |
| Fixed byte | `0x96` at `0xB2` (present) |
| Header checksum | `0x0000`; complement byte `0x00` (rebuilt-header artifact, guide §16.1) |
| MD5 | `e429ce307fe06dbcd7724552ff0339d7` |
| SHA-1 | `fb5662172fadebf4577f6f6f163741fc041c11e6` |
| SHA-256 | `92ead9ff9467dbc23780e768278fe2e4bf7a0708447a0785770c129a5dbdb06e` |

`file(1)` identifies it as `Game Boy Advance ROM image: "THE SIMS ADV" (ASIE69, Rev.00)`.

## 2. Executive summary

**Bounded negative: this GBA SKU has no developer-intended password, button code, or hidden debug menu.** The title's widely published "cheats" are CodeBreaker/GameShark RAM patches (explicitly out of scope) and button sequences for the **GameCube / PS2 / Xbox** SKUs, which are different games on different hardware (guide §16.11). No literal of any published console button code exists in this ROM when encoded as GBA key masks.

The only alphabetic input surface is the **Create-a-Sim name field** (A–Z, 0–9 keyboard). Per guide §16.2b it is a *label* field, not a validator: its only consumer is the displayed Sim name. There is no "Enter Password", "Enter Code", cheat menu, level select, or debug screen on any reachable screen.

Two important observations for the next analyst:

1. **All in-game UI text is stored in a non-ASCII font/tile encoding.** `strings -t x -n 4` yields 183,025 lines, but *none* of the visible menu labels ("Create-a-Sim", "Options", "Name Your Sim", copyright splash, "Press START") appear as ASCII. The only ASCII strings are debug/diagnostic leftovers of the link-cable library (`Error: Send Overrun`, `Error: Game Code Recv/Send`, `G4ME` at `0x052FC8`–`0x08053094`). A keyword-only `strings` search therefore proves nothing by itself (guide §11 "Not all text is ASCII"); the negative below rests on screen enumeration **plus** decoded VRAM font tiles **plus** whole-ROM pattern searches.
2. **"Game Code" in the ASCII strings refers to the Nintendo GameCube Link protocol, not a cheat code.** The `GCN Link` menu entry opens a "Waiting to connect..." screen; no code is typed there.

Confidence: high for the menu/title/creation surfaces; the in-game gameplay and pause screens were **not** reached (see §8), so the claim for those two screens rests on whole-ROM static searches rather than a screen visit.

## 3. How to reproduce

- Emulator: `mgba` 0.10.5 under `Xvfb :317` + `openbox`, `SDL_AUDIODRIVER=dummy`, `-3` scale.
- Keymap (mGBA SDL defaults): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad = arrow keys. Holds of 60–70 ms with ~180 ms gaps avoided double-stepping (guide §16.2).
- Boot path: language selector (English default) → A → copyright → EA/Maxis splashes → title "Press START" → Start → main menu.
- Screens enumerated (all with screenshots in `/tmp/opencode/simsbustin/`):
  1. Language selector (`English`/`Nederlands`/`Français`/`Deutsch`/`Italiano`/`Español`)
  2. Copyright + "LICENSED BY NINTENDO"
  3. EA Games / Maxis splash
  4. Title screen "Press START"
  5. Main menu: `Create-a-Sim`, `Load-a-Sim` (disabled until a save exists), `Options`, `GCN Link`
  6. `GCN Link` → "Nintendo GameCube Link / Waiting to connect..." (B cancels)
  7. `Options`: `Music Volume`, `SFX Volume`, `Language`, `Credits`
  8. `Credits` (scrolling credits, "ARBITRONITE GAMES")
  9. Create-a-Sim step 1: name entry with A–Z / 0–9 keyboard and `Done`
  10. Create-a-Sim step 2: `Gender`, `Skin Tone`, `Hair Style`, `Hair Color`, `Shirt`, `Pants`, `Shoes`, `OK`
  11. Create-a-Sim step 3: five personality sliders (Messy/Neat, Shy/Outgoing, Lazy/Active, Serious/Playful, Mean/Nice) + zodiac
- Button sequences tested on the main menu (each with a screenshot and hash): console-code analogues `Down,L,B,R,Left,A`; `Down,B,Up,A,R`; `Down,B,R,L,B`; `L,B,A,R,Left`; `L,R,Down,A,B`; plus Konami code, `L+R+Start`, `A+B+Start`, `Select+Start`, `L+R`. **All produced only ordinary menu navigation** (e.g. `L+R+Start` simply selected `Create-a-Sim`; `B+A` at the end of the Konami sequence did the same). No hidden screen or flag change was observed.

## 4. Address map

| Item | Address / offset | Evidence |
|---|---|---|
| GBA header | file `0x000`–`0x1FF` | `xxd` |
| ASCII debug/link strings | file `0x052FC8`–`0x08053094` (ROM `0x08052FC8`–`0x08053094`) | `strings -t x`, `xxd` |
| `G4ME` marker | file `0x08053094` | `xxd` |
| Input handler (KEYINPUT reader) | ROM `0x0801F180`–`0x0801F2FE` | Thumb disassembly (`objdump -M force-thumb`) |
| `KEYINPUT` literals | ROM `0x0801F24C`, `0x0801F2C4` → `0x04000130` | disassembly + literal decode |
| Key-mask constant | ROM `0x0801F250`, `0x0801F2C8` → `0x000003FF` | disassembly |
| Key-state arrays (u16) | IWRAM `0x03004220`, `0x03004228`, `0x03004230`, `0x03004238`, `0x03004248`, `0x03004250`, `0x03004270` | literal pool `0x0801F22C`–`0x0801F300` |
| Key-set index / repeat counter | IWRAM `0x030040E0+0x31`, `0x03004240` | `ldrb` at `0x0801F1DA`, reset at `0x0801F2B2`–`0x0801F2F2` |
| Observed RAM values at menu | `0x03004110 = 0x00000001`, `0x03004238 = 0x1E0B`, `0x03004240 = 0x1E0B`, others `0` | mGBA savestate `gbAs` chunk, IWRAM at state offset `0x19000` (guide §16.13) |
| Font tile bank (dynamic) | VRAM bank 1 = `0x06010000` (savestate offset `0x11000`); glyphs decoded: `Name Your Sim`, `Select`, keyboard A–Z/0–9 | 4bpp tile render, see §9 |
| Keyboard tilemap | VRAM `0x0600F800` (savestate offset `0x10800`); tile indices `0x001`–`0x078` for A–Z, 0–9, `Done` | 32×32 tilemap dump |
| Savestate layout (this build) | raw `gbAs` = 397,312 bytes; VRAM `0x1000`, IWRAM `0x19000`, EWRAM `0x21000` | `python3 sstate.py` |

## 5. Algorithm

No password/validator algorithm exists. The only relevant algorithm is the generic input state machine:

```
; ROM 0x0801F180 (Thumb) — per-frame key processing
cur   = ~KEYINPUT & 0x3FF          ; active-high key mask
held[i]  = cur                     ; 0x03004220 + i*2
pressed[i]  = (cur XOR prev) & cur ; newly pressed
released[i] = (cur XOR prev) & prev
prev = cur
if (keys[ sel ] & 0x03FF) != 0: counter = counter + 1
else: counter = 0; pressed/released arrays cleared
```

This is ordinary per-button edge detection with a repeat counter and a "current key-set" index byte — **not** a sequence matcher. No `strcmp`/`memcmp` against the input buffer, no progress index compared to a mask table, and no flag word written on sequence completion was found.

## 6. Tables

| Table | Location | Contents |
|---|---|---|
| ASCII diagnostic strings | ROM `0x08052FC8`–`0x08053094` | `Error: Send Overrun`, `Recv Overrun`, `Recv CRC`, `Recv Missing Packet`, `Invalid Mode`, `Invalid Command`, `Timeout`, `Game Code Recv`, `Game Code Send`, `None`, `G4ME` — all belong to the GCN-link transport |
| Key-state arrays | IWRAM `0x03004220`–`0x03004278` | 8 u16 arrays of key masks (held/pressed/released by key-set index) |
| Create-a-Sim name keyboard | VRAM tilemap `0x0600F800` | A–Z, 0–9, `Done` — rendered as 8×16 glyph pairs |
| Language table | Options menu | English, Nederlands, Français, Deutsch, Italiano, Español |

No code/password table, no alphabet-to-value table, no checksum table, no debug-menu entry table.

## 6b. Enumeration

**Result: the code space is empty; a bounded negative is proven by the following counts.**

1. **Alphabet surface** — exactly one: the Create-a-Sim name keyboard (26 letters + 10 digits). It is consumed as a display label (the entered text is drawn in the top bar of the appearance/personality screens); no comparison against it exists. By guide §16.2b this is a text field, not a password field.
2. **String search space** — 183,025 `strings -t x -n 4` lines searched case-insensitively for `cheat`, `password`, `debug`, `secret`, `unlock`, `bonus`, `gnome`: **0 hits**. Additional whole-ROM binary searches for those words in ASCII, uppercase, `+0x20`, `-0x20`, UTF-16LE and UTF-16BE: **0 hits**. (The only ASCII hits are the 10 link-protocol diagnostics listed in §6.)
3. **Button-code table search space** — 11 published console button sequences (GameCube/PS2 Cheat Gnome, unlock-all-objects/locations/skins/socials, team photo, fill motives, money), each encoded as GBA key masks under several plausible platform→GBA mappings, searched as contiguous `u16` and `u32` arrays over all 16,777,216 bytes: **0 hits**.
4. **Generic mask-sequence scan** — all 2-byte-aligned positions scanned for runs of consecutive single-button masks from `{0x001,0x002,0x004,0x008,0x010,0x020,0x040,0x080,0x100,0x200}`: 1,902 runs of length ≥4 found; **every run was repeated identical values** (e.g. `0x002 0x002 0x002 …`), i.e. compressed graphics/audio data, not a cheat table. No run of 5+ *distinct* button masks exists.
5. **Instruction scan** — Thumb `CMP Rd,#imm8` where `imm8` is a key mask: 6,670 instructions in 4,712 groups; inspected the multi-instruction groups — all were ordinary menu/A-B/Start navigation. No sequence-progress compare-and-set pattern.
6. **Emulator enumeration** — 11 reachable screens walked (§3), 10 candidate button sequences pressed on the main menu; **0 hidden screens, 0 new menu entries, 0 unexpected state changes**.
7. **Novel code / rejection bounds** — not applicable: there is no validator to mint a code for, and no code entry UI in which to test a rejection. Per §0.2 this is reported as a *bounded negative* (no system in the searched space), not as an untested feature.

**What would falsify this:** a save file enabling in-game gameplay/pause screens (§8), a GCN Link cable session, or a debug build with a different header hash. Any of those would require re-running the enumeration.

## 7. Validation evidence

- **Observed** (emulator): all 11 screens in §3, each with a screenshot; 10 button sequences with before/after screenshots; disabled `Load-a-Sim`; "Waiting to connect..." on GCN Link; keyboard layout; font glyphs decoded from VRAM.
- **Observed** (savestate RAM): IWRAM key-state values in §4; tilemap `0x0600F800` contents; VRAM bank-1 font glyphs.
- **Derived** (disassembly): input handler at `0x0801F180`; RAM addresses in its literal pool; absence of a sequence matcher in the CMP scan.
- **Derived** (static scans): the six counts in §6b.
- **Inferred**: that the ASCII "Game Code" strings are link-protocol terminology; supported by their location among transport error strings and by the GCN Link screen, but the transfer itself was not exercised (no cable/simulated GCN host).
- **Not observed**: in-game gameplay, pause menu, status screen, and any post-creation confirmation screen (§8). This is the principal gap.

### Reproduction artifacts

Work dir `/tmp/opencode/simsbustin/`: `kb.py` (input helper), `sstate.py` (gbAs extractor), `render4.py`, `renderfont.py`, `fontbank.py` (font renderers), `findmap.py` (tilemap locator), `buttonscan.c`, `codesearch.py`, `cmpscan.py`, `findkeyinput.py`, `findkey_arm.py`, `xref.py`, `histogram.py`, `lzscan.py`, `patternscan.c`, `cipherfind.c`, plus all screenshots (`boot.png`, `menu1.png`, `options3.png`, `cas_start.png`, `cas_next2.png`, `code_*.png`, …).

## 8. Unknowns

1. **Gameplay and pause menu were not reached.** The Create-a-Sim personality screen's confirmation control could not be driven: D-pad cycles only the five trait rows and the zodiac row; Start, Select, L, R, L+R, A+B, L+A and R+A all failed to advance. Published guides describe a following "Do you want this Sim? Yes/No" screen, so one more screen and the in-game menus exist but were not visited. Whole-ROM static searches (§6b) cover their code, but a save-enabled run would be needed for a screen-level confirmation.
2. **The custom text bank was not fully decoded.** Glyphs are generated into VRAM bank 1 at runtime and are not present verbatim in ROM (32-byte tile data for `N`, `a`, `m`, `Select` had zero ROM matches). I decoded the glyphs actually rendered on screen (name entry, keyboard, menu labels) and found no cheat text, but a compressed offline text bank, if any, was not exhaustively enumerated.
3. **`Heidi Shadows`, a secret NPC/seller described by contemporary guides as an unlockable, was not encountered** — it requires in-game travel/time and therefore depends on Unknown 1. This is gameplay content, not a code.
4. The link-protocol "Game Code" transfer was not exercised; no GCN host was available.

## 9. Tooling

- `mgba` 0.10.5 (`-3`, and briefly `-g` — that instance crashed after a GDB `interrupt`, so the stub was abandoned in favour of savestate diffs), `gdb-multiarch`, `xdotool`, `scrot`, `openbox`, `Xvfb :317`.
- `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for the input handler.
- Python 3 with `capstone` 5.0.7 for literal/BL/CMP scans; Pillow for tile rendering; custom C scanners for button runs and repeat-pattern matching; `zlib` for `gbAs` extraction (guide §16.13).
- No ROM or copyrighted assets are redistributed; this report contains only hashes, addresses, algorithms, and counts.

## 10. Cleanup

All processes started for this engagement (mGBA PID 635899; earlier mGBA PIDs 631334/631336 and 634378; Xvfb PID 631290; openbox PID 631294) were terminated by PID number, and every `.sav` / `.ss1` artifact was removed from the ROM folder. No `pkill -f` was used and no other agent's processes were touched.
