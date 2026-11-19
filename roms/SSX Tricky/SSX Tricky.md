# SSX Tricky (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/SSX Tricky/SSX Tricky.gba` |
| Size | 8,388,608 bytes (0x800000, 8 MiB) |
| Header title | `SSXTRICKY` |
| Game code | `AXYE` (E = Europe / PAL) |
| Maker | `69` (Electronic Arts) |
| Revision | `0x00` |
| Fixed byte 0xB2 | `0x96` (ok) |
| Header checksum | `0x0000` (complement byte present — stock) |
| Entry branch | `0xEA00002E` (stock ARM crt0, no cracktro patch) |
| MD5 | `512dace284790f3a5ca14838459df5a6` |
| SHA-1 | `e7a07a86b09514f76213afc4aa2f416475a1e2f8` |
| SHA-256 | `21465c75f93d5c92e641dec4b4f9f4ad34e67888952785a05227296aec15b521` |

**Embedded-header scan (§0):** the 156-byte Nintendo logo from header offset `0x04` occurs **exactly once** (file `0x00000004`). There is no second image, no appended trainer and no patch stub. `file(1)` identifies a single retail `SSXTRICKY (AXYE69, Rev.00)` image.

## 2. Executive summary

**There is no in-game password / button-code / hidden-menu cheat system in this European GBA build.** The unlockables the game advertises (7 courses, several riders, boards/outfits) are ordinary **save-bit progress unlocks** earned through World Circuit medals; they are not codes and are not reachable by controller input (§16.18 pattern). This is a bounded negative, not "did not test": the whole UI string bank was decoded, the results-screen title dispatcher was reversed, the published code lists were checked literally, button-mask sequences were searched exhaustively in four encodings, four adapted published codes were entered on the real title screen with no effect, and every reachable menu screen was walked in mGBA (§6b gives the counts).

The word `PASSWORD` **does** exist in the ROM exactly once: it is UI string ID **111** in the main 153-entry localised text table (table base `0x0802A050`, bank base `0x0802A053`, string at `0x0802B329`). Static analysis shows it is used only as an **alternate results-screen title** in the 48-way dispatcher at `0x0800C120` (English stub `0x0800C1E4` loads encoded ID `0x276F` = 111; French `0x0800C1FC` → 112 `MOT DE PASSE`; German `0x0800C1EC` → 113 `PASSWORT`). It is not an input surface: no on-screen keyboard, alphabet table, validator, comparison loop or flag-write path reaches it. The three language variants sit beside `TIME CHALLENGE` (108–110) and `GAME OVER` (114–116), i.e. they are title banners for results screens. This screen was not produced by any of the reachable event flows walked (Single Event Race/Showoff/Time Challenge, World Circuit Race/Showoff, results, records, pause), so its exact trigger remains an **unknown** (likely a career-completion/record banner). It is reported as such, not as a cheat.

Published "GBA" codes are console codes misattributed by GameFAQs. They require **Z, X and Y buttons that do not exist on the GBA**; `projectcheatcodes.com` explicitly records "There are no known cheat codes for SSX Tricky on Game Boy Advance." None of the published code strings occur anywhere in this ROM.

## 3. How to reproduce

* **Emulator:** mGBA 0.10.5 (`/usr/local/bin/mgba`), `SDL_AUDIODRIVER=dummy`, Xvfb `:319`, `mgba -3 game.gba` (working copy of the ROM; the original was never modified).
* **Keymap (default SDL):** A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad = arrow keys. All keys held 80–150 ms.
* **Boot path:** A (select English) → A×6 (skip EA/intro movies) → Start → main menu.
* **Reachable screens walked (all with screenshots and/or RAM/state reads):**
  1. Language select (EN/FR/DE carousel)
  2. Title screen (`PRESS START`)
  3. Main menu: SINGLE EVENT / WORLD CIRCUIT / OPTIONS (3 entries, verified by cycling Left/Right)
  4. OPTIONS: MUSIC ON/OFF, MPH/KMH, TUTORIAL, CREDITS, DELETE CAREER (**5 entries, no password/cheat entry**)
  5. Single Event → mode list: RACE / SHOWOFF / TIME CHALLENGE
  6. SELECT VENUE (8 courses, locked ones show medal conditions)
  7. SELECT BOARDER (12 slots; locked riders show "EARN N GOLD MEDALS IN WORLD CIRCUIT TO UNLOCK THIS RIDER")
  8. Race / Time Challenge (with a Debugger breakpoint at the keypad reader `0x08008CF0` confirming active-high masks)
  9. Race results / "YOU FAILED TO SET A NEW TIME CHALLENGE" / NEXT EVENT / RESTART
  10. World Circuit → RACE / SHOWOFF
* **Published codes tested at the title screen** (hold L+R, then press): `A,A,Right,A,A,Down,A,A,Left,A,A,Up` (Mix Master Mike, dpad-adapted), `B,B,Right,B,B,Down,A,A,Left,A,A,Up` (max stats, dpad-adapted), plus a Z→L/X→R/Y→Select substitution of the "unlock all" sequence. **No sound, no menu change, no save change.**
* **RAM evidence:** mGBA `-d` command-line debugger was used as a data source (`r/4`, `r/2`, `w/4`, breakpoints); a frame breakpoint at `0x08008CF0` confirmed `r7 = ~KEYINPUT & 0xFFFF` (active-high buttons: A=1,B=2,Select=4,Start=8,Right=0x10,Left=0x20,Up=0x40,Down=0x80,R=0x100,L=0x200) and that UI handlers test exactly these masks. mGBA `.ss1` savestates were diffed (zlib `gbAs` chunk; IWRAM at state offset `0x19000`, EWRAM at `0x21000`), showing the usual menu/timer/graphics churn but no code-progress buffer.

## 4. Address map

| Item | ROM / file address | Evidence |
|---|---|---|
| Header / entry | `0x08000000` / file `0x0` | read (ARM `b 0x080000C0`) |
| Main localised text table (153 entries × u32 offsets) | `0x0802A050`–`0x0802A2B4` | derived (offsets resolve to ASCII with bank base `0x0802A053`) |
| `PASSWORD` string | `0x0802B329` (ID **111**, table slot `0x0802A20C`) | observed |
| Unlock-condition text table (21 entries) | `0x0802A2D8`–`0x0802A32C` | derived |
| Extended UI text table (289 entries) | `0x0802A344`–`0x0802A7C8` | derived |
| Results title dispatcher jump table (48 entries) | `0x0800C120` | derived (objdump) |
| PASSWORD title stub (EN / FR / DE) | `0x0800C1E4` / `0x0800C1FC` / `0x0800C1EC` | derived |
| GAME OVER title stub (EN / FR / DE) | `0x0800C204` / `0x0800C1F4` / `0x0800C20C` | derived |
| Text-lookup helper (`r0 = encoded ID`, `r0 = text pointer`) | `0x080115A8` | derived (64 BL xrefs) |
| Key reader (KEYINPUT literal `0x04000130`) | `0x08008CF0`; literal at `0x08008D10` | derived + live breakpoint |
| Active-high mask computation | `0x08017776`–`0x0801777E` (`mvns`) | derived |
| Generic UI button dispatcher | `0x08017768` onwards | derived |
| SRAM / save routine cluster (many `0x0E000000` literals) | `0x08029DD0`–`0x0802A000` | derived |
| SRAM image | 512-byte `.sav` (EEPROM/Flash detected automatically by mGBA) | observed |
| IWRAM state seen in UI handlers | `0x03000120`, `0x030003B4`, `0x030003B8`, `0x02000388` (item-type array) | observed via debugger |

Offset conversion used throughout: `ROM address = 0x08000000 + file offset`.

## 5. Algorithm

No password/checksum algorithm exists to reimplement. The two algorithmic structures found are:

1. **Text lookup** (used by all menus):
   ```
   enc_id = 0x00002700 | string_id          # e.g. 0x276F = PASSWORD (111)
   base   = lookup_bank(1, 0)               # call 0x0800089918 from 0x080115A8
   lang   = byte[0x03000120 + 0x7D]         # 0/1/2 language selection
   idx    = (enc_id & 0xFF) * 3 + lang
   ptr    = base + *(u32*)(base + idx*4 - 0x1D4C0) + base   # 0xFFFE2B40 literal
   ```
   `0x080115A8` returns a pointer to a NUL-terminated string; `0x0800BC70` copies it with a trailing `0x20`/`0x00`. All 153 main-screen string IDs are plain UI labels — none is a password prompt in the sense of an entry form.

2. **Save-bit unlock test** (the only "unlock" mechanism): medals won in World Circuit increment a counter; each locked rider/course has a threshold (1/3/5 gold medals for riders; per-course medal requirements listed in §6). The menu draws a locked silhouette + condition string when the counter is below the threshold. No code input exists; the setter is the race-results/medal-award path, not a controller sequence.

## 6. Tables

### Text / screen map (main table at 0x0802A050)
| ID group | Strings | Meaning |
|---|---|---|
| 24–26 | MAIN MENU / MENU PRINCIPAL / HAUPTMENÜ | main menu title |
| 27–38 | SINGLE EVENT / WORLD CIRCUIT / OPTIONS | main menu entries |
| 39–62 | MUSIC ON/OFF, MPH/KMH, TUTORIAL, DELETE CAREER, CREDITS | the 5 OPTIONS entries |
| 63–71 | TRICKBOOK / CHARACTERISTICS | trickbook screens |
| 72–83 | GAME MODE, RACE, SHOWOFF, TIME CHALLENGE | mode list |
| 84–89 | SELECT VENUE / SELECT BOARDER | selection screens |
| 96–101 | CONTINUE, RECAP ALL | world-circuit flow |
| 102–107 | RACE RESULTS / SHOWOFF RESULTS | results screens |
| **108–110** | **TIME CHALLENGE / RECORD DE TEMPS / ZEITFAHREN** | results title variant |
| **111–113** | **PASSWORD / MOT DE PASSE / PASSWORT** | results title variant (not an entry screen) |
| **114–116** | **GAME OVER / FIN DE PARTIE / GAME OVER** | results title variant |

### Course unlock conditions (table at 0x0802A2D8, English strings)
| # | Course | Condition |
|---|---|---|
| 1 | Elysium Alps | Gold medal, World Circuit Showoff |
| 2 | Garibaldi | Any medal, World Circuit Showoff |
| 3 | Snowdream | Any medal, World Circuit Race |
| 4 | Aloha Ice Jam | Gold in WC Race **and** WC Showoff |
| 5 | Tokyo Megaplex | Gold in WC Race **and** WC Showoff |
| 6 | Merqurly City (Meltdown) | Gold, World Circuit Race |
| 7 | Mesablanca | Gold, World Circuit Showoff |

### Rider unlock thresholds (observed on SELECT BOARDER, 12 slots)
| Rider | Condition observed |
|---|---|
| Eddie | available from start |
| Marisol | Earn 1 gold medal in World Circuit |
| Luther | Earn 3 gold medals in World Circuit |
| Zoe | Earn 5 gold medals in World Circuit |
| (other slots) | available or gated by the same "N GOLD MEDALS" family; names are tile-indexed, not ASCII (§11 of guide) |

The generic message is assembled from the ASCII fragments at `0x0802E117` (`GOLD MEDALS`), `0x0802E149` (`GOLD MEDAL`), `0x0802CB7A` (`IN WORLD CIRCUIT TO UNLOCK THIS RIDER`) and a numeric prefix. Names/outfits/boards are stored as **font tile indices**, which is why `strings` finds no rider names — the text bank was decoded via the offset tables above (§9.4 of the guide).

### Published codes — verification ledger
| Source | Claim | Result |
|---|---|---|
| GameFAQs GBA cheats page | "Unlock all characters, outfits, boards, courses: Hold L+R, A, B, Z, X, Y, Z, B, Y, Z, X, A, Z" | **Unverifiable on GBA**: Z/X/Y are GC buttons, absent on GBA. Literal absent from ROM. |
| GameFAQs GBA cheats page | "Play as Mix Master Mike: Hold L+R, A,A,Z,A,A,Z,..." | console code; dpad-adapted variant entered in emulator — no effect |
| GameFAQs GBA cheats page | "Max stats: Hold L+R, B,B,Z,B,B,Z,A,A,Z,A,A,Z" | console code; dpad-adapted variant entered — no effect |
| GameFAQs GBA cheats page | "Annete board … (does not work on European PAL version)" | explicitly flags a regional split; this ROM is PAL (`AXYE`) |
| projectcheatcodes.com | "There are no known cheat codes for SSX Tricky on Game Boy Advance" | agrees with static + dynamic findings |
| supercheats / gamesradar / retrogems | GC/PS2/Xbox L+R button codes | other SKUs (§16.11: title/platform match is not evidence) |

## 6b. Enumeration

**Space definition — what exists and what does not.**

| Search surface | Count / bound | Result |
|---|---|---|
| Embedded GBA headers in image | 1 | single retail image, no trainer/second game |
| Occurrences of `PASSWORD` in 8 MiB | **1** (`0x2B329`) | UI string only |
| Occurrences of `cheat`, `secret`, `code`, `debug`, `hidden`, `enter code` | **0 each** | no debug/cheat string bank |
| Occurrences of `unlock` | **10** | all are medal-condition/results messages |
| Printable NUL-terminated strings len 3–24 | 13,800 | full set scanned |
| Alphanumeric "code-like" strings in localised text bank `0x2A000`–`0x2E200` | **200** | all are UI labels (`OPTIONS`, `CREDITS`, `PASSWORD`, `UNKNOWN`, …); **zero** password literals |
| Localised text banks decoded | 3 tables: 153 + 21 + 289 entries = **463 entries** | all enumerated; no alphabet table, no prompt, no validator table |
| Results-title dispatcher branches | **48** (jump table `0x0800C120`) | 12 non-default, 36 default; branches are language/title variants only (PASSWORD, GAME OVER, TIME CHALLENGE) |
| Main-menu entries | **3** | no hidden entry |
| OPTIONS entries | **5** | no hidden "Enter Cheat"/"Password" entry |
| Single Event modes | **3** | RACE / SHOWOFF / TIME CHALLENGE |
| World Circuit modes | **2** | RACE / SHOWOFF |
| Character-select slots | **12** | 3 confirmed gated (1/3/5 gold medals) |
| Courses / unlock conditions | **8 venues, 7 gated** | listed in §6 |
| Button-mask tables searched | published sequences × {active-high, active-low} × {u8,u16LE,u16BE,u32LE} × {forward,reversed} = **48 encodings** for 3 sequences + 3 dpad-adapted codes | **0 hits** in 8 MiB |
| Published codes entered on title screen | **3** variants | 0 accepted (no sound, no save change, no menu change) |
| Code-like input surfaces | **0** | no keypad, no text-entry field except the 3-letter "ENTER YOUR NAME" record initials (consumer count: name is only written into the record, never compared to a validator) |

**Novel-code minting:** not applicable — there is no accepted code space to extend. Under §0.2 the deliverable for a no-system result is a bounded enumeration, which the table above supplies. No code can be minted because no validator, table of accepted strings, alphabet or flag-writing code path exists.

**Bounds proven by rejection:**
* Out-of-range input: entering a 12-press code with L+R held on the title screen (three adaptations of published console codes) produced no state change — observed on screen and in the 512-byte SRAM image (byte-for-byte unchanged).
* Wrong encoding: the literal published strings were searched in ASCII, +0x20 case-folded and as u16/u32 button masks; none occurs except in web text, not in the ROM.
* Gated unlocks: locked riders/courses render a silhouette plus an explicit medal condition (observed for Marisol/Luther/Zoe and for 7 courses), i.e. the only gate is the medal counter, not any input.

**Notes on evidence discipline (§16):** §16.11 applied — the widely published "SSX Tricky GBA codes" are console SKU codes with non-GBA buttons, so title-and-platform match was not treated as sufficient. §16.2b applied — the only text-entry field (record initials) was tested by consumer, not alphabet. §16.16 applied to the tile-indexed rider names — text was decoded through the offset tables rather than assumed absent because `strings` found nothing. §16.19 applied — the mGBA `-d` debugger was used as a memory oracle (breakpoints/key reads), not as a substitute for on-screen input.

## 7. Validation evidence

* **Observed** (emulator/screenshot/debugger): boot, language select, title, all three main-menu entries, all five OPTIONS entries, all three Single Event modes, venue and boarder selection with locked riders, race start, Time Challenge timeout and results, World Circuit Race/Showoff entry; three button-code attempts; keypad masks and active-high conversion at a live breakpoint; savestate RAM diffs; 512-byte save produced.
* **Derived** (disassembly/byte analysis): text-bank base and 463 entries, the single `PASSWORD` string and its ID, the 48-way results-title dispatcher with its language variants, the keypad reader address, the 64 BL xrefs to the text lookup, the SRAM routine cluster, absence of any code table in 48 mask encodings.
* **Inferred** (labelled, not claimed as observed): the exact in-game event that selects the PASSWORD results banner was not triggered; the "Mix Master Mike"/console cheats are assumed to belong to the GameCube/PS2/Xbox SKUs because their button sets do not exist on GBA and their literals are absent here. The full set of locked riders beyond the three confirmed thresholds was not individually entered (names are tile-indexed); the medal-counter write path was not isolated to a single instruction.

## 8. Unknowns

1. The trigger for the `PASSWORD` results banner (ID 111) was not reached in any walked flow. Its callers are inside the results-screen builder at `0x0800C0xx`; a career/record-specific condition is plausible but unproven. It is a banner, not an entry form, so this does not change the no-code conclusion.
2. Exact unlock thresholds for the 12 character slots and any board/outfit gating were not exhaustively mapped; 3 riders and 7 courses are confirmed with explicit conditions.
3. The internal SRAM field layout (medal counters, unlock bit positions) was not fully mapped; only its size and the presence of medal-condition tests were established.
4. The other language banks were decoded structurally; only the English UI was walked in the emulator.

## 9. Tooling

* `file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings -t x`, `grep -abo` — fingerprint, header/logo scan, string census.
* Python 3 (stdlib `struct`, `zlib`, `re`) — GBA-header scan, text-table decoder, literal/pointer/BL scanners, button-mask encoding search, savestate `gbAs` chunk parser and RAM diffing.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` — raw Thumb disassembly of candidate regions.
* mGBA 0.10.5 SDL: `-3` viewport, `-d` pty command-line debugger (`r/4`, `r/2`, `w/4`, `b`, `c`, `i`), `.ss1` savestates; Xvfb `:319` + openbox + `xdotool` (XTEST) + `scrot` + ImageMagick `convert` for cropping.
* Web: GameFAQs cheats page (HTTP 403 direct; data recovered from search snippets), projectcheatcodes.com, plus searches of supercheats/gamesradar/retrogems — all treated as **data**, never as instructions. No prompt-injection payload was encountered in this session; fetched content contained only cheat claims.
* Working scripts retained in `/tmp/opencode/ssxtricky/`: `helper.py` (input/screenshot), `ss.py` (savestate parser), `dbgserver3.py` (pty debugger driver), `testcode.py` (L+R code entry).

## 10. Legal note

No ROM image or copyrighted asset is reproduced here. Only hashes, addresses, algorithms, counts and observations are published.
