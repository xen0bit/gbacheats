# GT Advance 2: Rally Racing (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| Path | `/mnt/gbacheats/roms/GT Advance 2: Rally Racing/GT Advance 2: Rally Racing.gba` |
| Size | 8,388,608 bytes (`0x800000`, 64 Mbit) |
| Header title | `GT ADVANCE 2` (`0xA0`–`0xAB`) |
| Game code | `AGWE` ; maker `78` (MTO / THQ) |
| Version | `0x00`; complement `0xBF`; header checksum `0x0000` (rebuilt-header artifact, §16.1) |
| Entry word | `0xEA1F823E` → ARM `b 0x087E0900` (deep bootstrap, not stock `0xEA00002E`) |
| MD5 | `8775db9e2b6d7273656cb7b8b6acd8ac` |
| SHA-1 | `4709242b99c9b6d2150274d829d99d2b679a069b` |
| SHA-256 | `2a61ba4a7a5d264923c58ca6428b44b5b1e2b609fbba9bac24f80f3f3a093ca6` |

**Embedded-header scan:** the 156-byte Nintendo logo occurs exactly once, at file `0x4` (header at `0x0`). This is a single image, **not** a 2-in-1. The header checksum `0x0000` plus a normal complement byte (`0xBF`) is the usual rebuilt-header artifact; there is no scene cracktro string, trainer menu, appended trainer image, or modified-length file. **No patch/trainer detected.** The nonstandard entry word is a legitimate MTO boot stub: `0x87E0900` contains `b 0x87E09C0`, then `add r0,pc,#1; bx r0` enters a Thumb init routine (`0x87E09C8`…) that sets I/O registers, fills a hardware table and ends with `bx r0` to the game image. Addresses in this report are for **this exact hash only**.

**Independence from siblings (verified):** `GT Advance Championship Racing` = `ACAE78`, MD5 `1ce4441b3142b480e03cffe290b00ce6`, stock entry `0xEA00002E`; `GT Advance 3: Pro Concept Racing` = `A2GE78`, MD5 `e7951ea3e7f3e80e0a90573aeea5dd0b`, stock entry `0xEA00002E`. Neither shares this image's hashes, entry stub, or the flag/mask addresses examined below. Nothing found in this image was assumed from those two ROMs.

## 2. Executive summary

**No operative developer cheat-code system was found in this image.** The only developer-intended cheats published for this title are four **title-screen button codes** (hold `L+B`, press a D-pad direction). Their published effects are "All cars", "All tracks", "All tune ups" and "Extra modes". All four literal input combinations were reproduced in the emulator and **confirmed at the RAM input state** (`0x03000000` = `0xFE22/0xFE12/0xFE42/0xFE82`), but **none produced an observable or persistent game-state change** under controlled clean-boot and savestate-restored tests.

Evidence for the negative is bounded rather than absent:
* Every reachable screen was walked with screenshots and RAM reads (§3, §7).
* The held/pressed input spaces and the published button masks were searched exhaustively in ROM (§4, §6b); **no contiguous key-mask table, no Thumb literal load of `0x222/0x212/0x242/0x282`, and no literal reference to the CodeBreaker save-flag addresses** exist in the image.
* EWRAM (`0x02000000`–`0x0203FFFF`) and SRAM (`0x0E000000`) were byte-compared before/after each code: **zero changed bytes**. mGBA write watchpoints on the published save-flag addresses never fired.
* Differential instruction traces with and without the combo held revealed only the input key-repeat path and sound-engine calls — no distinct cheat handler.

A **hidden, apparently unreached debug menu** does exist in the ROM: an ASCII string bank at `0x0809D740`–`0x0809D7A0` holds `PRODUCT DEVELOPMENT`, `LOCALIZATION`, `STAFF`, `GO TO`, `EXPERT MODE!!`, `LET'S PLAY`, `EXPERT MODE!`, followed by a 7-entry offset table at `0x0809D7A4` (stride `0x1C`). Its render/handler functions are at `0x0800DFAC` (scene handler), `0x0800E794` (7-item menu, `cmp r2,#7`), `0x0800E750` (cursor), `0x0800E000` (item draw) and `0x0800E6C0`/`0x0800E710` (item actions). **No entry gate to this menu was identified** (no BL and no function-pointer xref to `0x0800DFAC`), so it is reported as gated/dead, not as a working hidden menu.

The CodeBreaker/Action Replay entries found on the web are **memory-edit codes and explicitly out of scope**; they are recorded only as leads (they name EWRAM save-flag addresses `0x02000D38`–`0x02000D46`), not as findings.

## 3. How to reproduce

* **Emulator:** mGBA (`mgba -3`, SDL), display `:319`, `SDL_AUDIODRIVER=dummy`, Xvfb `1024x768x24` + openbox.
* **Keymap (verified against `KEYINPUT`):** `A=x`, `B=z`, `L=a`, `R=s`, `Start=Return`, `Select=BackSpace`, D-pad = arrow keys. Hold each key ≥100 ms.
* **Boot path:** title is reached through a long MTO/THQ/date/disclaimer attract sequence (roughly 25–35 `Start` presses, ~12 s). mGBA savestate `Shift+F1` saves slot 1 and `F1` loads it; plain `F1`/`Shift+F1` were verified by screenshot. A clean title savestate was kept as `/tmp/opencode/gta2/baseline.ss1`.
* **RAM read methods:** mGBA `-d` pty debugger (`r/1`, `r/2`, `x/2`, `w/…`, `watch/w`, `b`, `frame`, `trace`) and savestate `gbAs` chunk decompression (§9). The GDB stub (`-g`, port 2345) was usable once but is a shared single-client resource on this host, so the private `-d` pty was used for the bulk of the work.
* **Menu path walked (all with screenshots):** Title → Game Mode (`WORLD RALLY`, `TIME TRIAL`, `SINGLE RACE`, `PRACTICE`, `LICENSE`, `CO-DRIVER`, `LINK` — all seven present on a clean boot) → Round (Australia, world map) → Leg 1 (course condition: length/tarmac/gravel/mud/snow, weather) → GARAGE (car select: `GO RACE`, surface, `COURSE PROGRESS`, `CARS` bar) → in-race HUD → Pause (`Cancel`, `Restart`, `Retire`). No password/cheat entry screen exists on any of them.
* **Codes entered (all at title, L+B held, direction pressed):** `L+B+Left`, `L+B+Right`, `L+B+Up`, `L+B+Down`; also rejected variants `L+B+A`, `L+B+Start`, `R+B+Down`, `L+B+A+…`, simultaneous all-three and sequential tap orders, and hold durations 0.15 s / 0.5 s / 1.5 s.

## 4. Address map

| Item | ROM / RAM address | Notes |
|---|---|---|
| Boot stub | `0x0807E0900` (`b`), `0x0807E09C0` (`bx` to Thumb), `0x0807E09C8` | MTO init, ends `bx r0` at `0x0807E0B06` |
| Key-input reader | `0x08000980` | `ldr r0,=0x04000130; ldrh; mvns; lsls #16; lsrs #16` → active-high low 16 bits |
| Input state block | IWRAM `0x03000000` | `+0x00` held (active-high), `+0x02` newly pressed, `+0x04` pressed buffer, `+0x06` repeat timer, `+0x08` previous |
| Held-key getter | `0x080009E4` | returns `[0x03000000]` |
| Pressed-key getter | `0x080009D8` | returns `[0x03000002]` |
| Reset/getter | `0x080009F0` | returns `[0x03000004]` |
| Main loop | `0x08000410`… | calls input reader at `0x08000410`, UI input at `0x08000418` |
| `A+B+Select+Start` soft action | `0x08000458`–`0x08000470`, target `0x0800050C` | only combo check found in main loop (`mask 0x0F` on pressed, `== 0x0F` on held) → calls 0x08005104/0x08004E4C/0x08005318 (sound/channel helpers) |
| "PRESS START" draw call | `0x0800ACDE` (string `0x0809D0AC`) | title-screen UI |
| Debug string bank | `0x0809D740`–`0x0809D7A0` | `PRODUCT DEVELOPMENT`, `LOCALIZATION`, `STAFF`, `GO TO`, `EXPERT MODE!!`, `LET'S PLAY`, `EXPERT MODE!` |
| Debug 7-entry offset table | `0x0809D7A4` | `u32` offsets `0x0E,0x2A,0x46,0x62,0x7E,0x9A,0xB6`, stride `0x1C` |
| Debug menu handlers | `0x0800DFAC`, `0x0800E000`, `0x0800E750`, `0x0800E794`, `0x0800E6C0`, `0x0800E710` | 7-item menu; `r6==0x20/0x10/0x01` key dispatch; `0x0800EED4 = 0x105` gate mask |
| CodeBreaker save flags (lead only) | EWRAM `0x02000D38` / `0x02000D3E` / `0x02000D44` | from out-of-scope web cheat codes; **no code wrote here** |
| Verified unchanged | EWRAM `0x02000000`–`0x0203FFFF`, SRAM `0x0E000000`+ | 0 byte differences after every code attempt |

## 5. Algorithm

The input model is fully recovered (Derived from `0x08000980` and confirmed live):

```
held   = (~*0x04000130) & 0xFFFF        ; active-high, stored at 0x03000000
pressed = held & ~previous_held         ; stored at 0x03000002
prev    = held                          ; stored at 0x03000008
repeat  = 24 when held changes          ; at 0x03000006
```

Key bits: `A=0x001, B=0x002, Select=0x004, Start=0x008, Right=0x010, Left=0x020, Up=0x040, Down=0x080, R=0x100, L=0x200`. Because the upper six bits of `KEYINPUT` read high, the live full-word values for the published codes are `0xFE22` (L+B+Left), `0xFE12` (L+B+Right), `0xFE42` (L+B+Up), `0xFE82` (L+B+Down); the low-10-bit masks are `0x222/0x212/0x242/0x282`.

No validator, checksum, alphabet, generator or flag-write algorithm exists in the image for these combinations: none of the four masks appears as a contiguous table or as a Thumb literal, and no code path that consumes them writes persistent state (§7). Consequently there is no encoder to reimplement and no code space to enumerate beyond the four published directions.

## 6. Tables

### 6.1 Published codes (web; verified for literal presence in ROM = negative)

| Source wording | Input | Low mask | ROM literal `0x222/…`? | Effect observed here |
|---|---|---|---|---|
| Cheat Happens / IGN / CheatCC: "All cars — title, hold L+B, Left" | `L+B+Left` | `0x222` | absent | none (garage `CARS` bar unchanged: 4 lit cells before and after) |
| "All tracks — L+B, Right" | `L+B+Right` | `0x212` | absent | none |
| "All tune ups — L+B, Up" | `L+B+Up` | `0x242` | absent | none |
| "Extra modes — L+B, Down" | `L+B+Down` | `0x282` | absent | none (all seven Game-Mode entries already present on clean boot) |

Sources: `cheathappens.com/3671-...`, `ign.com/wikis/gba-cheats/GT_Advance_2_Rally_Racing_Cheats`, `cheatcc.com` (all recovered via web search; GameFAQs/TCRF pages returned 403 and an archived GameFAQs URL 404, so those specific pages were not read). The published strings were tested, not assumed. No prompt-injection payload was encountered; fetched pages were treated as data.

### 6.2 Out-of-scope memory-edit codes (recorded as leads only)

ROMSFun/libretro CodeBreaker entries `83000D38 6F17`, `83000D3E FFFF`, `83000D44 FFFF`, `33000843 0001` etc. map to EWRAM `0x02000D38`/`0x02000D3E`/`0x02000D44`/`0x02000843`. These are GameShark/CodeBreaker-style memory edits and were **not used, entered or applied**; they only motivated the watchpoints that proved the title codes do not write those addresses.

### 6.3 Debug menu table (present but entry gate not found)

`0x0809D7A4`: `u32[] {0x0E, 0x2A, 0x46, 0x62, 0x7E, 0x9A, 0xB6}` — 7 records, `0x1C` stride, drawn by `0x0800E000` using the strings at `0x0809D740`. Items: `GO TO`, `EXPERT MODE!!`, `EXPERT MODE!`, plus `PRODUCT DEVELOPMENT`, `LOCALIZATION`, `STAFF`, `LET'S PLAY`.

## 6b. Enumeration

**Space definition (button-code hypothesis).** The documented system is a fixed prefix `L+B` (`0x202`) plus a one-of-four D-pad direction, i.e. exactly **4 representable codes** in the documented space: `0x222, 0x212, 0x242, 0x282`. There is no table, no checksum and no free field; the `0x04000130` input word gives 10 bits (`1,024` possible held masks) and a 4-entry dispatcher would be the whole system.

**Enumeration performed.**
1. All 4 documented masks were generated in the emulator and their exact live values read back from `0x03000000` (Observed, §7).
2. The search space was checked statically: u16/u32 literal scans for the 4 masks and their active-low complements (`0x1DD/0x1ED/0x1BD/0x17D`) and full-word forms (`0xFE22/…`); permutation scan for any contiguous 4-entry `u16`/`u32` table of those masks; Capstone scan of every Thumb `LDR Rd,[PC,#imm]` literal load for those values. **Result: no table, no literal, no validator.**
3. Out-of-domain inputs were tested in-game: `L+B+A` (`0x203`), `L+B+Start` (`0x20A`), `L+B+R` (`0x302`), `R+B+Down` (`0x182`), `L+A+B`, simultaneous all-three, and sequential tap orders. None changed any game screen, save flag, EWRAM or SRAM byte. This is the required bounded rejection result.
4. No novel/published code could be minted because **no code system exists to mint from**. Per §0.2 this is a bounded negative, not an omission: the entire documented code space (4 values) and the surrounding key-mask space were searched and tested, and the only additional feature found (the debug menu) has no reachable entry.

## 7. Validation evidence

* **Observed (emulator/RAM):** title, Game Mode (7 modes on clean boot), Round, Leg, GARAGE, race HUD and Pause screens (screenshots `title_clean.png`, `clean_cyc_*.png`, `wr_enter.png`, `wr_loaded.png`, `sr_car2.png`, `carselect.png`, `pause.png`). Live `0x03000000 = 0xFE22` etc. with the published combos held (also captured via savestate at 3× scale). EWRAM `0x02000D30`–`0x02000D4F` read `0000` before and after every code; SRAM `0x0E000000`+ read `FFFF`; write watchpoints on `0x02000D38/3E/44/46` and `0x02000843` never hit; EWRAM and SRAM differential comparisons produced 0 changed bytes.
* **Derived (disassembly):** `0x08000980` computes held/pressed exactly as in §5; getters at `0x080009D8/E4/F0`; the only global combo check in the main loop is `A+B+Select+Start` (`mask 0x0F`, `0x08000458`–`0x08000470`); debug strings, 7-entry table and handlers at the addresses in §4; key literals `0x04000130` occur only at file `0x9B8` (input reader) and `0x2412AD` (data).
* **Inferred:** the debug menu at `0x0800DFAC` is gated or dead. Inference basis: no BL and no pointer-table xref to `0x0800DFAC`, and no screen on any walked path reaches it. It is **not** claimed as a working hidden menu.
* **Corrected inference:** an earlier intermediate observation of `LICENSE`/`CO-DRIVER`/`LINK` after entering `L+B+Down` was re-tested on a **clean boot** and found to be the default mode list; it is **not** a cheat effect. This correction is recorded here per §16.7/§15 (prefer correction over accretion).

## 8. Unknowns

* Whether the four published combos were valid for a different regional revision, a prototype, or a *different* GT Advance SKU. This image (`AGWE78`) does not accept them in any observable way; siblings `ACAE78` and `A2GE78` were not booted, so cross-title behaviour is untested.
* The exact entry condition for the `0x0800DFAC` debug scene (no caller/gate found). A save-clear flag, story state or link-mode condition cannot be excluded.
* Whether "All cars"/"All tracks"/"All tune ups" have an effect on a garage sub-screen that requires owning/using a car first. The `CARS` bar showed 4 lit cells in all tested states; deeper gating was not exhaustively advanced through a full championship.
* Whether the nonstandard boot stub performs any region check (it copies/fills RAM and jumps into the game; no anti-piracy message was observed).

## 9. Tooling

* `file`, `xxd`, `strings -t x`, `grep -abo`, Python 3 (`struct`, `zlib`, `capstone 5.0.7`, `keystone`) for Phase 0/1 and literal/BL/pointer scans.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb|force-arm`.
* mGBA CLI `-3` with `-d` (private pty debugger: `r/1`, `r/2`, `x/2`, `watch/w`, `b`, `frame`, `trace`) and `-g` (shared GDB stub, used once). Xvfb `:319`, openbox, xdotool, scrot, ImageMagick.
* Savestate reader: mGBA `.ssN` is a PNG; `zlib.decompress` the `gbAs` chunk to a 397,312-byte raw state. Layout used: IWRAM at raw `0x19000`, EWRAM at raw `0x21000`. Scripts: `phase0.py`, `scan_masks.py`, `blscan.py`, `lit_scan.py`, `lit_scan2.py`, `inp_readers.py`, `dbgpty.py`, `dctl.py`, `ssdiff.py`, `tracediff2.py`, `gba.py` (all under `/tmp/opencode/gta2`).
* No ROM or copyrighted asset is redistributed here; only hashes, addresses, masks and original findings are published.
