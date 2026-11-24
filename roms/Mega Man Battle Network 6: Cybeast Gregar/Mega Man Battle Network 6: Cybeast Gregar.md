# Mega Man Battle Network 6: Cybeast Gregar (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

> **SKIPPED / DEFERRED — entry systems found but not in-game confirmed (coordinator decision).**
> Under §0.2 this report does **not** meet the dynamic-confirmation bar: two real player code
> systems were found and verified in ROM (10-button `{A,B,L,R}` Navi Customizer compression
> commands and 8-digit Number Trader codes, with literals located in the tile-indexed text bank
> decoded via bn6-utf8.tbl), but both entry screens are **story-gated** on a fresh save (PET menu
> has no NaviCust row, house exit blocked by the "talk to Mom and Dad" event, Central Town chip
> shop later), so no code was entered and accepted in-game and no in-game rejection bounds were
> produced. Per coordinator authorization, MMBN titles whose validator/code-entry surface is
> blocked by a story gate are documented here and **skipped rather than retried or indexed**.
> The code tables, exact RAM addresses and minimal steps to finish the test are recorded below.
> This report is intentionally left out of the completed-reports table and listed under Skipped ROMs in the top-level `README.md`.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Mega Man Battle Network 6: Cybeast Gregar.gba` |
| Size | 8,388,608 bytes (`0x800000`) |
| Header title | `MEGAMAN6_GXX` |
| Game code | `BR5E` (maker `08`, Capcom) |
| Version | `0x00`; fixed byte `0x96` present; complement `0x59` (recomputed `0x59`, match) |
| Header checksum | `0x0000` (normal for this build; complement is the reliable "header untouched" signal) |
| Entry word | `0xEA000032` → `0x080000D0` (stock Capcom crt0: `mov r0,#0x12; msr CPSR_fc,r0; ldr sp,[pc,#...]` at `0x080000D0`; **not** a scene-release cracktro branch `0xEA00002E`) |
| MD5 | `5acc75848bb1ffd3d6d8705554ee333d` |
| SHA-1 | `89fe0bac4fd3d2ab1d2ca35e87ef8b1294a84cd6` |
| SHA-256 | `572e113eeb53bb29cd9ff8acb9db265cfd48c5e509c8d0e6420b58e71e442cf2` |

**Embedded-header scan:** the full 156-byte Nintendo logo from offset `0x04` occurs exactly **once** in the image (at `0x04`). No multiboot stub, no appended second header, no trainer. Tail of file is all `0xFF` (no appended trainer data). This is a single, clean retail US image.

Build stamp (TCRF, US Gregar): `REXE6 G 20060110a US` at file offset `0x03F754`, text at `0x1519C8`. The visible title screen reads "©CAPCOM CO., LTD. 2005".

**Independence from the sibling image** ( analysed concurrently on display `:318`): the Falzar file is a *different* ROM — `MEGAMAN6_FXX`, code `BR6E`, SHA-256 `a37c1028adb72082b51e142321fa437967bc54b6f46730a53f6581ad455ad670`. Every address, hash, literal offset and RAM value in this report was derived from the Gregar bytes above. No Falzar-based address was carried over. The engines are related (the community `bn6f` disassembly notes that Gregar's PET-region code is Falzar's shifted by `0x1DDC`), so *structure* is shared, but this report does not rely on that.

Note: the shared REA/Ghidra MCP session was switched to the Falzar image by the concurrent agent during this engagement; all conclusions here therefore come from local `objdump`, Python/Capstone, and mGBA evidence against the Gregar file. The fetched TCRF page was checked for prompt-injection payloads and none was found in the retrieved text; its contents were treated strictly as data.

## 2. Executive summary

This ROM contains **two genuine, developer-intended, player-facing code systems** plus one *non-player* debug-text set:

1. **Navi Customizer "Compression Commands"** — 10-button sequences over `{A, B, L, R}`, entered in the Navi Customizer by highlighting a program piece, holding Right, and inputting the buttons (guide §5.4a pattern). A successful input toggles the piece's compressed state and plays a jingle; per the community wiki, wrong input is silent in BN6 (§16.6 "semantics, not just bytes" applies). The space is `4^10 = 1,048,576` sequences; the published list has ~35 codes (one per usable program, plus a known unusable dummy). **Published literals were located in the ROM** (§6).
2. **Number Trader / Lottery Chip Machine 8-digit codes** — decimal passwords entered on a numeric keypad in the Central Town chip shop. Space `10^8 = 100,000,000`; a 58-code published list was checked and **10 literals were located in the ROM** (§6).
3. **Debug text commands** — TCRF lists ~50 two-byte script commands (`0x47` … `0xFE`, e.g. `C9 = Operate Partner Navi (CHEATER)`, `FE = You got: All Chips`). TCRF explicitly describes them as *normally inaccessible*; they are unused script payloads (guide §16.3 category **dead code**), not a reachable menu or a button code. They are documented here as a negative finding, not advertised as cheats.

Out of scope and therefore deliberately not tested as in-game cheats: all GameShark / CodeBreaker / Action Replay / libretro entries found on Almar's Guides, SuperCheats, Neoseeker, ROMSFUN, GameFAQs and GameHacking.org. Those are memory-edit codes and are excluded by the task scope.

**Important limitation (stated up front, not hidden):** both real code-entry screens are **story-gated**. On a fresh US save the Navi Customizer is absent from the PET menu and only key item `PET` exists; the game blocks leaving the house with "We'll go after you talk to Mom and Dad!". Central Town's chip shop is several chapters away. The entry screens were therefore *not* reached in this session, so the §0.2 requirement "mint a novel code and confirm it on the real screen" could **not** be discharged. This report gives the complete static characterisation, the exact gates, and the precise remaining steps (§8) rather than claiming a confirmation that did not happen.

## 3. How to reproduce

**Emulator / display**

```
export DISPLAY=:315 SDL_AUDIODRIVER=dummy
Xvfb :315 -screen 0 1024x768x24 &
openbox &
mgba -3 -d "…/Mega Man Battle Network 6: Cybeast Gregar.gba"
```

mGBA SDL keymap verified in-game: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows. `xdotool key --repeat N --delay 70 x` reliably advances dialogue; `keydown`/`sleep 0.12`/`keyup` moves the cursor exactly one slot (the guide's §16.2 double-step warning is real: `--repeat` with a 150 ms hold oversteps menus).

**Walk performed (all in the US Gregar image, screenshots on disk in `/tmp/mmbn6gregar/`)**

| # | Screen | Evidence | RAM at capture |
|---|---|---|---|
| 0 | Title / "NEW GAME" | `00_title_c.png` | — |
| 1 | Intro dialogue ("Sooo, I'm Lan Hikari!") | `03_intro.png` | — |
| 2 | Classroom overworld | `05_after65.png` | — |
| 3 | School exterior | `s_c.png` | — |
| 4 | Lan's bedroom | `s5_c.png` | — |
| 5 | Living room / kitchen | `s9_c.png` | — |
| 6 | **PET main menu** (9 rows: ChipFolder, SubChip, Library, MegaMan, E-Mail, KeyItem, Comm, Save, EXIT) | `s10_c.png` | `0x02001B80=0x18`, `0x0200DF20+4=0x04` |
| 7 | MegaMan STATUS page 1 (HP, Buster Attack/Speed/Charge/Pwr Charge) | `s13_c.png` | `0x02009A30+0=0x0C` |
| 8 | MegaMan STATUS page 2 (Folder limits, PROGRAM slots) | `s14_c.png` | `0x02009A30+0=0x0C` |
| 9 | KeyItem screen — **only item `PET`** | `k1_c.png` | `0x02009A30+0=0x14` |
| 10 | House exit — story dialogue gate | `w5_c.png` | — |

**RAM reads** used mGBA savestates (guide §16.13): save with Shift+F1/F2, take the PNG's `gbAs` chunk, `zlib.decompress` it to 397,312 bytes; for this 8 MiB ROM the layout is IWRAM at file-offset `0x19000` (`0x03000000`–`0x03007FFF`) and EWRAM at `0x21000` (`0x02000000`–`0x0203FFFF`). Verified: the stack frame at `0x03007FD8` in the state holds PC `0x0814F40A` and LR `0x0800098D`, matching the state header's registers.

**Codes tested on-screen:** none — both screens are gated (see §8). The following were tested *statically* instead: all literals in §6; 24 button-mask permutations × 3 encodings × 6 codes; 1,147 LZ77 blocks; the `4^10` and `10^8` space definitions.

## 4. Address map

### Text encoding and banks

| Item | Address (ROM) | Note |
|---|---|---|
| Character table | community `bn6-utf8.tbl` (RockmanEXEZone/MMBN-Table-Files, `done/bn6-utf8.tbl`) | `0x01`–`0x0A` = digits `0`–`9`; `0x0B`–`0x24` = `A`–`Z`; `0x26`–`0x3F` = `a`–`z`; `0xB4`=`[L]`, `0xB5`=`[B]`, `0xB6`=`[R]`, `0xB7`=`[A]`; `0xE0`=END, `0xE9`=newline; `0xE4 xx` = extended glyph |
| "PASSWORD" prompt | `0x0876028B` | decoded from bytes `1A 0B 1D 1D 21 19 1C 0E` |
| "NUMBER"/"TRADER"/"CHIP" | `0x087682AC`, `0x087681BF`, `0x08768206` | Number Trader dialogue |
| "MEGAMAN" | `0x08786C6B` | title/menu text |
| "CYBEAST" | `0x08788474`, `0x087C14EB` | title text |
| Text-archive pointer table | `0x0804458C`–`0x08044C58` and `0x08044CE4`–`0x0804533C` | u32 ROM pointers; only xrefs are from the table itself |
| Password text archive | pointer at `0x080452C0` → `0x08760048` | archive contains the PASSWORD prompt at `+0x243` |
| NaviCust program-name archive | `0x0873C98C` | 75 names, `0x0873C65A` holds the UnderShirt compression-code hint |
| Key-item name archive | `0x0873B938` | entry per key-item id |
| `UNCOMP` debug residual | `0x00002BFA` | only meaningful ASCII `strings` hit |

### Code literals located in this image

See §6 for the full per-code table.

### RAM (verified in this image)

| Address | Meaning | Observed |
|---|---|---|
| `0x02001B80` | GameState, byte 0: `0x04` map, `0x18` PET menu | `0x18` on PET screen |
| `0x02009A30` | PET sub-screen, byte 0: `0x00` folder, `0x04` SubChip, `0x08` Library, `0x0C` MegaMan status, `0x10` E-Mail, `0x14` KeyItem, `0x18` Comm, `0x1C` Save, `0x20` folder editor, `0x24` NaviCustomizer; byte 1 course `0x04` open; `+2` sub-mode in NaviCust (`0x04` list, `0x08` board) | `0x0C` on status, `0x14` on KeyItem |
| `0x0200DF20` | ePETMenuData: `+0` state (`0x10` taking input), `+4` cursor (0–8) | `0x10`, cursor `0x04` |
| `0x0200A272` | `BN6_KEYS_PRESSED` (u16, active-high) | `0x00` at rest |
| `0x02004E0` / `0x02003134` | key-item check bytes (id XOR `0x55`) / counts | only `PET` present on fresh save |
| `0x03007FD8` | idle stack frame with PC/LR | PC `0x0814F40A`, LR `0x0800098D` |

## 5. Algorithm

**Text bank decoding.** Each character is one byte under the table in §4; `0xE4 xx` is a two-byte extended glyph. This is why `strings` finds essentially nothing (guide §11 "Not all text is ASCII"): 87,730 ASCII runs were extracted but keyword grep returned a single incidental hit (`UTUDU5BUg5SUS` at `0x3645B8`). The bank is **not** compressed for the UI strings used here — decoding the raw bytes at the addresses in §4 yields readable English directly.

**Compression-command storage.** The codes are written in *uppercase letters* under the same table, i.e. `A=0x0B, B=0x0C, L=0x16, R=0x1C` — **not** the special button-glyph bytes `0xB4`–`0xB7`. Between letters the hint strings carry formatting/control bytes (`0x00` space, `0x01`, `0x04`, `0x1B`, `0x63`, …), so an exact 10-byte search fails and a `letter .? letter …` regex is required. This is the single reason the straightforward literal searches in the guide's §3.3 returned zero.

**Button-code entry semantics** (from the community wiki, consistent with guide §5.4a/§16.6): hold **Right**, then input exactly 10 presses of A/B/L/R in the Navi Customizer. Same sequence again toggles the piece back (XOR-style toggle, so the code is its own inverse). Wrong input is silent in BN6 (the error sound present in BN5 was removed). This means "no jingle" is a weak rejection oracle; the reliable observable is the program piece's compressed state (its MB footprint on the board).

**Number Trader entry semantics:** 8 decimal digits typed on the in-world keypad; codes are consumed once used ("all Number Trader codes used" is a documented save-file state). The codes are the 8 encoded digits `0x01`–`0x0A` in the text bank, again with occasional interspersed control bytes.

**What was NOT recovered:** the comparison routine itself. Neither code system has a plain hard-coded comparison table in the image under any of the encodings tested (§6), so no offline validator reimplementation can be claimed. The codes live in text archives as *hints*; the accepting table/algorithm is a separate code path that was not isolated before the story gate stopped progress.

## 6. Tables

### 6.1 Compression commands verified in ROM

Encoding: `A=0x0B B=0x0C L=0x16 R=0x1C`; "gap" = one non-letter byte between adjacent letters. Search: 2,097,152-byte image, regex `(letter).?` × 10.

| Code (part) | ROM file offset | Raw bytes |
|---|---|---|
| `RRALLRAABB` (UnderShirt) | `0x73C658` | `1C 00 1C 0B 16 16 1C 0B 0B 0C 63 0C` |
| `ALABBAAABA` (Collector) | `0x761E11` | `0B 16 00 0B 0C 0C 0B 0B 0B 0C 0B` |
| `LRABARBBLR` (OilBody) | `0x78F12A` | `16 1C 0B 0C 01 0B 1C 0C 0C 16 1C` |
| `RALABLBBRB` (FloatShoes) | `0x79052E` | — (gap-2 match) |
| `ALARBRARLB` (Jungle) | `0x79292F` | `0B 16 00 0B 1C 0C 1C 0B 1C 16 0C` |
| `BBARABLARR` (FirstBarrier) | `0x7EA3F4` | `0C 0C 0B 00 1C 0B 0C 16 0B 1C 1C` |
| `RBARALBBBL` (Millionaire) | `0x7EBAAF` | `1C 0C 0B 1C 0B 16 0C 0C 1B 0C 16` |
| `ALAAALLABR` (SlipRunner) | `0x7EC419` | `0B 16 0B 0B 0B 16 16 04 0B 0C 1C` |
| `RRABLRARLA` (ChipShuffle) | `0x7E9143` | — (gap-2 match) |
| `BBBAABAABB` (AutoHeal) | `0x2B1F1E` | — (gap-2 match, lower-confidence) |

Count: **9 of 34 distinct published compression commands** were located with ≤1 interspersed byte; 10 with ≤2. The remainder were not located — their hints are either phrased differently, split across a script control sequence, or simply not present in this US build. This is a *bounded* negative for the searched encodings, not a claim that the codes are invalid.

Full published set (GameFAQs + T REZ wiki, US Gregar) contains, among others: `ABLLAALRBA` SuprArmr, `LBBRBAALRR` Custom1, `RALLAABRBA` Custom2, `ARLALALLAB` MegaFolder1, `LALRBLRLRA` MegaFolder2, `BLBRLLLABA` GigaFolder1, `BBARABLARR` FirstBarrier, `RBBBAAABRL` Shield, `LAABRRLRLR` Reflect, `BLALBRALBA` AntiDamage, `RALABLBBRB` FloatShoes, `ARBABRRBAL` AirShoes, `RRALLRAABB` UnderShirt, `RRABLRARLA` ChipShuffle, `AAALAABLRA` NumberOpening, `BBBABBAARB` SneakRun, `BRBBBBBARR` Battery, `ALARBRARLB` Jungle, `ARAABARRBA` Fish, `LLABLBABLL` Humor, `BABARRLLAB` Poem, `ALAAALLABR` SlipRunner, `BBBAABAABB` AutoHeal, `AALABRALBA` ChargeMAX/SpeedMAX, `LLALLBABBB` ChargeMAX, `RBARALBBBL` Millionaire, `BLBLARLRBB` **dummy** (NaviRuin key item; compresses no part — a documented in-game rejection).

### 6.2 Number Trader / lottery codes verified in ROM

Encoding: digit `d` → byte `d+1` (`0x01`–`0x0A`), 8 digits, gap-2 regex.

| Code | ROM file offset |
|---|---|
| `87341489` (Full Energy) | `0x759BE2` |
| `79459146` (SneakRun) | `0x75A4D8` |
| `59485971` (Untrap) | `0x75B493` |
| `04789479` (Unlocker) | `0x73C600` |
| `82564319` (Unlocker) | `0x783540` |
| `24823665` (HP+200 White) | `0x73C544` |
| `94305487` (ChargeMAX Blue) | `0x73C68B` |
| `32132348` (RushSupport Yellow) | `0x73C5DA` |
| `70741543` (AirSpin3 O) | `0x73C6B6` |
| `09256524` (Spreadgun/Spin Green) | `0x79D92E` |

Count: **10 of 58** published SuperCheats lottery codes located in this image under the searched encoding. The published list also includes `45566783`, `39345472`, `15511679`, `74198795`, `22812406`, `09000465`, `99910954`, `41161139`, `98766899`, `68008194`, `16336487`, `37495453`, `37889678`, `49951337`, `54654618`, `08749780`, `55031325`, `12046210`, `19790420`, `28271002`, `32132348`, `41976910`, `77837421`, `88674125`, `14212857`, `38116449`, `97403000`, `08789369`, `44892547`, `75641392`, `69544569`, `51378085`, `97049899`, `12404002`, `30424514`, `55910601`, `84387543`, `92070765`, `51702791`, `67520179`, `00297421`, `10414878`, `79814666`, `24616497`, `32310827`, `12110031`, `57656595`; these were searched and not found at gap ≤2 (their hints may be absent from the US build; note the list's own comment that Hakushaku/Django codes were removed from the US version).

### 6.3 Debug commands (dead code, not a player cheat)

TCRF, `Mega Man Battle Network 6` → "Debug Text": `47` Cannot Converse, `65` All mail sent, `6F`/`AB`/`AC`/`AD` HP banners, `AE` All mail received, `AF` BOKTAI TRADER DISPLAY, `B5` Green Town Chip Trader SP Display, `B6` Navi Change Box Display, `B7` BugFrag trader display (untranslated Japanese string in the US build), `B8`/`BF` BBS entry, `C0`–`C2` request completion, `C3` Got Rush Food, `C9` Operate Partner Navi (CHEATER), `CA` Virus Battle Set (CHEATER), `CB` Max Virus, `D1` HP Memory, `D3`–`D5` Reg Up, `D8`/`D9`/`DA` Extra Deck/Folder2, `DC`–`E2` minigames, `E6`–`F0` character changes, `F1` Beast/Cross change OK, `F2` ProtoMan, `F4` Hidden Gate Display, `F6` You got PA, `FE` You got: All Chips. Classified per guide §16.3 as **dead code**: no reachable front end was found in the walked screens and TCRF calls them "normally inaccessible".

## 6b. Enumeration

**Compression-command space.** Alphabet `{A,B,L,R}`, fixed length 10, no checksum symbol, toggle semantics → `4^10 = 1,048,576` representable button strings. Published surface: ~35 distinct documented strings (≈0.0033% of the space). **Novel codes generated here** (absent from GameFAQs, T REZ wiki and every ROM literal searched in §6.1):

- `AAAAAAAAAA` — all-A sequence; valid *format*, no known part mapping.
- `LLLLLLLLLL`, `RBRBRBRBRB`, `ABABABABAB` — equally well-formed members of the unused 1,048,541 strings.
- `BLBLARLRBB` is the interesting published edge case: a well-formed code delivered by an in-game key item that compresses **no** NaviCust part. This is the game's own proof that syntactic validity and semantic acceptance are separate layers (guide §16.5/§6.5).

**Number Trader space.** Decimal alphabet, length 8, no documented check digit → `10^8 = 100,000,000` strings. Published surface: 58 codes (≈0.000058%). Novel code generated here: `12345678` (absent from all published lists and from every ROM literal searched in §6.2), plus `00000000` and `99999999` as boundary-form inputs.

**Bounds evidence available statically.** `BLBLARLRBB` is documented as a format-valid but semantically rejected compression code (the game gives it as a key-item hint with no usable part). The all-A/all-zero forms above are format-valid by construction but appear in no ROM hint bank. **Not available:** an in-game accept/reject observation for any novel code, because neither entry screen was reachable (see §8). Per guide §0.2 this is the one acceptance criterion this report does not satisfy, and it is reported as such rather than inferred.

**Counted negative searches** (so the absence claims are bounded, not vague):

| Search | Space checked | Result |
|---|---|---|
| `strings -t x -n 4` + case-insensitive keyword grep | all 8,388,608 bytes, 87,730 strings | 1 incidental hit, no password/cheat/debug UI text |
| Literal published compression codes (ASCII, `±0x20`, XOR-0xFF, UTF-16LE/BE, reversed, encoded-uppercase, encoded-button-glyph) | 34 codes × 10 encodings | 0 exact hits |
| Literal published lottery codes (ASCII, u32 LE/BE, encoded digits) | 58 codes | 0 exact hits |
| Button-mask table brute force (active-high/active-low u16, 24 permutations; 2-bit, 4-bit, 1-byte compact forms) | 6 codes × all listed encodings | 143 coincidental hits, no encoding consistent across ≥2 codes |
| LZ77 decompression scan | 1,147 valid `0x10`-header blocks across the ROM | 0 clean compression or lottery codes |
| ROM-wide A/B/L/R encoded runs | 8,388,608 bytes | 35 runs ≥8; 10 match published codes with ≤1 interspersed byte |
| ROM-wide encoded-digit runs | 8,388,608 bytes | 898 runs ≥8; 10 match published lottery codes at gap ≤2 |
| Embedded GBA headers | full image | exactly 1 |

## 7. Validation evidence

**Observed** (emulator / savestate RAM):
- Title, menu, status, KeyItem and overworld screens listed in §3; screenshots on disk.
- `0x02001B80 = 0x18`, `0x02009A30 = 0x0C` then `0x14`, `0x0200DF20 = 10 04 00 00 03 01 00 00 01 00 04 03 03 01 07`, `0x0200A272 = 0` from decompressed `gbAs` chunks.
- Savestate RAM patch of `0x02009A30` byte 0 to `0x24` (NaviCustomizer) changed the byte but **not** the rendered screen and made B/A unresponsive; reverting to `0x0C` restored input. This is direct evidence that screen state is not a single byte — the sub-screen's handler must be initialised by its own code path. (Guide §16.10: a debugger poke is not a substitute for the screen; recorded as a failed shortcut, not a finding.)
- Clean header, stock crt0, single logo hit, all-`0xFF` tail.

**Derived** (ROM bytes + disassembly):
- The text encoding and the decoded strings/literal offsets in §4 and §6, verified by reading the exact bytes.
- The `4^10` and `10^8` space definitions from the documented input surfaces.
- PET input handler at `0x08120B90`: reads cursor from `[r5,#4]`, exits at cursor ≥8, gates Comm(6)/Save(7) on flag `0x1706`, dispatches sub-screens through `0x081217FE`. Only 9 menu rows exist — NaviCustomizer is not a top-level PET row.
- The savestate layout (IWRAM `0x19000`, EWRAM `0x21000`) verified by matching the stack frame to the state header's PC/LR.

**Inferred** (labelled, not claimed as observed):
- That the published compression codes are genuine in-game sequences rather than fan inventions — supported by their presence in the ROM's text bank, but not confirmed by entering them.
- That the debug commands are dead code — supported by TCRF's wording and the absence of a front end in the walked screens; a live breakpoint on a command handler was not set.
- That the two sibling versions share engine structure but not addresses — supported by the distinct hashes/headers and the community `bn6f` offset-shift note.

## 8. Unknowns

1. **The accepting validators were not located.** No comparison routine or algorithmic table was isolated for either system. A validator model precise enough to run offline (guide §0.2 item 2) is therefore **not delivered**.
2. **No novel code was entered in-game and no RAM effect was observed.** The required §0.2/§7 novel-code acceptance and bounds-by-rejection proof are outstanding. This is the single largest gap.
3. **Exact gate for the Navi Customizer:** fresh save has only key item `PET`, the PET's MegaMan STATUS screen has two pages and no NaviCust row, and the story blocks leaving the house with "We'll go after you talk to Mom and Dad!". Likely unlocked by an early story flag / NaviCust Support Center event; the writer of that flag was not located.
4. **Number Trader gate:** the machine is in the Central Town chip shop; the chapter-1 walkthrough position was not reached.
5. **25 of 34 compression codes and 48 of 58 lottery codes were not found** at gap ≤2 in the searched encodings. Their hint text may use longer control sequences or be absent in the US build.
6. **Debug-command reachability** was not closed by a breakpoint; conclusion rests on TCRF's description plus screen enumeration.

**Minimal steps to complete (reproducible):** advance the story until `0x02009A30` byte 0 can be `0x24` through normal input; verify the NaviCust list at `0x0201DA80` (4 bytes/entry) and mode byte at `0x02009A30+2`; hold Right and input `RRALLRAABB` (UnderShirt, starts installed per the wiki) while watching the piece's MB footprint; then input `AAAAAAAAAA` and record rejection. For the Number Trader, reach Central Town's green machine, enter verified `87341489`, then `12345678`; read GameState zenny at `0x02001B80+0x5C` and the item-flag bytes before/after. Both need a captured savestate at the entry screen so each test costs one keypress.

## 9. Tooling

- `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings -t x`, Python 3.13 (`struct`, `zlib`, `re`, `collections`).
- `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`.
- Capstone 5.0.7 / Keystone (installed; used for encoding searches).
- mGBA (CLI `-d` debugger bridged through a Python `pty` + command-file watcher), Xvfb `:315`, openbox, xdotool, scrot, ImageMagick.
- `patchstate.py` (savestate `gbAs` recompression with CRC fix-up), `key.py` (focus/key/crop helper), `lzsearch.py` (GBA LZ77 decompressor + code search).
- Web sources treated as data: TCRF mirror (fetched clean), GameFAQs cheats (403 direct; search snippets used), T REZ wiki NaviCustomizer page, RockmanEXEZone `bn6-utf8.tbl`, `dism-exe/exe6f` and `saschb2b/Mega-Man-Battle-Network-Cyberworld-Endless` ROM maps. No fetched instruction was executed.

No ROM bytes or copyrighted assets are reproduced in this report beyond short address-anchored byte strings needed to reproduce the search.
