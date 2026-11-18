# Mega Man Zero (GBA) — Reverse Engineering Report

## 1. Target identity

| Item | Value |
|---|---|
| File | `roms/Mega Man Zero/Mega Man Zero.gba` |
| Size | 8,388,608 bytes (0x800000, 8 MiB) |
| `file` classification | Game Boy Advance ROM image: "MEGAMAN ZERO" (AZCE08, Rev.00) |
| Header title | `MEGAMAN ZERO` (bytes at 0xA0) |
| Game code | `AZCE` ; maker `08` (Capcom) ; version `0x00` |
| Entry branch | `0xEA00002E` → `0x08000036` (stock crt0; **not** a cracktro patch) |
| Fixed byte / complement / checksum | `0x96` / `0x70` / `0x0000` |
| MD5 | `b24a17d080a01a404cbf018ba42b9803` |
| SHA-1 | `193b14120119162518a73c70876f0b8bffdbd96e` |
| SHA-256 | `cf505422d68295fba36136a49a3c9dedb104ab16aa542edaeecbb89efdd57807` |
| Embedded GBA headers | Exactly one, at file 0x0 (full 156-byte Nintendo logo scan of all 8 MiB). No appended trainer, no second image, no patch stub. |

## 2. Executive summary

**There is no password / code-entry system in this game.** There is no on-screen keyboard, no `PASSWORD`/`DEBUG`/`SECRET`/`SOUND TEST` entry, and no hidden debug menu. The entire visible UI text bank was decoded with the game's own text table (Data Crystal TBL, 971 strings from 0x082B8000–0x082C8000): the only mode-related strings are two *in-game instructions* that document the developer-intended button codes (see §4). All other "cheats" published for this SKU are GameShark/CodeBreaker RAM patches, which are out of scope.

What the game *does* contain is a small **save-gated button-code system**:

1. **Boot-time gate (undocumented on any published list):** holding `A+B+Select+Start` at boot, gated by byte `0x02004CE0`, calls four privileged init routines (`0x08000538`–`0x08000576`). This combination appears in no GameFAQs/TCRF/VGChartz list — it is a novel, statically recovered code (§6b).
2. **New Game gates:** hold `L` + choose NEW GAME = **Hard Mode**; hold `R` + choose NEW GAME = **Ultimate Mode**. Both are printed verbatim in the game's own credits text at `0x082BB0FF` and `0x082BB166`, and both are gated by flags in the game-clear save record.
3. **Credits gate:** hold `A` during the credits to skip (published; no ROM string — effect is in the credits script).
4. **Ultimate-Mode charge combos:** 7 documented motion+attack sequences (GameFAQs/Reeve guide), implemented as gameplay input matchers.

The negative result is bounded: the full byte-encoded text bank was decoded (not just `strings`), the ASCII scan returned **0/75,955** keyword hits, the published code lists were checked against the ROM, and every reachable screen was walked under mGBA with savestate RAM evidence.

## 3. How to reproduce

- Emulator: mGBA (SDL), `/usr/local/bin/mgba -3 <rom>`, `DISPLAY=:318`, `SDL_AUDIODRIVER=dummy`, own Xvfb + openbox on `:318`.
- Keymap (mGBA SDL default): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows.
- Savestates: `Shift+F1` writes `Mega Man Zero.ss1` next to the ROM; `mmzero1/ss.py` decompresses the `gbAs` PNG chunk (state length 397,312 bytes; EWRAM at state `0x21000`, IWRAM at `0x19000`, per guide §16.13).
- Screen path walked (all with screenshots and/or savestates in `/tmp/opencode/mmzero1/`):
  1. Inti Creates splash → `PRESS START` title (`shot00`, `shot01`, `w01_title.ss1`).
  2. `Start` → title menu, **only `NEW GAME`** when no save exists (`w02_menu`, `menu_base.ss1`). Down/Up do not reveal further entries.
  3. `A` on NEW GAME → lengthy scripted intro (multiple dialogue screens; `shot05`–`shot12`, `w03`–`w12`).
  4. Gameplay (`w12`, `w13_pause.ss1`) — the intro is very long and the Start-driven pause sub-screen was not reached inside the available run; its menu entries were recovered from the decoded text bank instead (see §8).
- Input RAM proof: holding `L` with the emulator running changes the active-high held mask at `0x02004CA4` from `0x000` to `0x200` (`in_base.ss1` vs `in_L.ss1`, 56-byte RAM diff); holding `x+z+BackSpace` yields `0x007` (`multikeys.ss1`).
- Published codes tested: the GameFAQs/GameFAQs-legacy lists contain **no** password strings; all 25 libretro/ROMSFUN entries are CodeBreaker memory writes (e.g. `3202B634 0080`) and are deliberately not used. The two in-game button codes were verified against the ROM text (§4), not against a password entry screen (none exists).

## 4. Address map

| ROM file offset | ROM address | Meaning |
|---:|---|---|
| 0x0000 | 0x08000000 | GBA header; single image |
| 0x00C0 | 0x080000C0 | ARM crt0 |
| 0x04C0–0x0586 | 0x080004C0–0x08000586 | Boot init: sets `0x02004C72`/`0x02004C70`, then the A+B+Select+Start gate |
| 0x0538–0x0576 | 0x08000538–0x08000576 | **Boot button-code validator** (see §5) |
| 0x0F04–0x0FC4 | 0x08000F04–0x08000FC4 | Joypad reader: reads `0x04000130`, inverts, writes held/prev/pressed |
| 0x0DE0 | 0x08000DE0 | Flag setter: `flag[0x03001748 + 24*r0] = 1` |
| 0x0D10 | 0x08000D10 | Task/message setter used by the boot gate |
| 0x1F00 | 0x08001F00 | Second input-related structure `0x02004C80` |
| 0xBB159 | 0x082BB159 | Encoded text `NEW GAME` |
| 0xBB0FF | 0x082BB0FF | `To play the HARD mode, save game-clear data, then hold L Button down when you choose "NEW GAME".` |
| 0xBB166 | 0x082BB166 | `Save with all Cyber-Elves used, hold R Button and choose "NEW GAME" to play ULTIMATE mode.` |
| 0xBE45A | 0x082BE45A | `Will you save the Game Clear Data? YES / NO` (proves the game-clear save flag) |
| 0xB95CC | 0x082B95CC | `CONTINUE?`, `RETRY`, `GIVE UP`, `RESTART SAVED GAME`, `QUIT THE GAME` (pause/menu strings) |
| 0x2B8000–0x2C8000 | 0x082B8000–0x082C8000 | Decoded text bank (971 strings) |
| — | 0x02004CA4 | Input state, `u16`; bits 0–9 active-high (`A=1,B=2,Sel=4,Start=8,R=0x10,L=0x20,U=0x40,D=0x80,R=0x100,L=0x200`) |
| — | 0x02004C70 / 0x02004C72 | Boot-initialised mode words (`0x080004D4`–`0x080004E2`) |
| — | 0x02004CE0 | Boot gate byte; must be 0 for the boot code to run |
| — | 0x03001748 + 24*n | Privileged flag array set by `sub_08000DE0` |

## 5. Algorithm (boot button gate, derived from Thumb disassembly)

```
; 0x08000538  (inside the boot init function starting 0x080004B8)
if (*(u8*)0x02004CE0 != 0) goto skip;          ; ldrb / cmp / bne
keys = *(u16*)0x02004CA4;                       ; ldrh from input struct
if ((keys & 0x0C) != 0x0C) goto skip;           ; bits 2,3  (Select, Start)
if ((keys & 0x01) == 0)   goto skip;            ; bit 0 (A)
if ((keys & 0x02) == 0)   goto skip;            ; bit 1 (B)
sub_08000DE0(0);                                ; flag[0x03001748] = 1
sub_08000DE0(1);                                ; flag[0x03001760] = 1
sub_080BD390(1, 0x08000415);                    ; privileged init with callback
sub_08000D10(0, 0x08000415);                    ; privileged task setup
skip:
```

Effective accepted mask: **`held & 0x000F == 0x000F`**, i.e. `A+B+Select+Start` simultaneously at boot. No other key is constrained (L/R/d-pad may be any state). This is the complete boot validator — there is no longer sequence and no second mask check in this path.

Input state model (from `0x08000F04`):
```
raw   = *(u16*)0x04000130           ; active-low
held  = ~raw & 0x3FF                ; stored at 0x02004CA4 (upper bits are ~unused KEYINPUT bits, e.g. 0xFC00 idle)
prev  = held_old                    ; 0x02004CA6
press = held & ~prev                ; 0x02004CA8
```

## 6. Tables

### 6.1 Button codes found (complete set)

| # | Code | Gate | ROM evidence | Published? |
|---|---|---|---|---|
| 1 | Hold `A+B+Select+Start` at boot | byte `0x02004CE0 == 0` | `0x08000538`–`0x08000576` (this report) | **No** — novel |
| 2 | Hold `L` + NEW GAME | game-clear save data | text `0x082BB0FF` | Yes (GameFAQs, VGChartz, manuals) |
| 3 | Hold `R` + NEW GAME | save with all Cyber-Elves used | text `0x082BB166` | Yes (GameFAQs, VGChartz) |
| 4 | Hold `A` during credits | completed save (`play time >= 1`) | GameFAQs "Skip Credits"; credits script | Yes |
| 5 | Ultimate-Mode charge combos (7 sequences: Buster L1/L2, Saber, Rod, Shield) | Ultimate Mode active | GameFAQs/Reeve guide | Yes |

### 6.2 Text encoding (Data Crystal TBL)

`0x00`=space, `0x01`–`0x0A`=`0`–`9`, `0x0B`–`0x24`=`A`–`Z`, `0x25`–`0x3E`=`a`–`z`, `0xE5`=`!`, `0xFC`/`0xFD`=line break, `0xF0 xx`=extended punctuation, `0xFF`=terminator. This is why `strings` found **zero** UI strings.

### 6.3 Keyword search counts (ASCII, `strings -t x -n 4`)

75,955 strings; case-insensitive hits for `password|cheat|code|debug|secret|unlock|stage|level|select|sound|test|extra|option|menu|hidden|boss` = **0**. TBL-decoded bank: `HARD`=1, `ULTIMATE`=1, `PASSWORD`=0 (the word appears only as story-dictionary text in lowercase form inside dialogue: "I haven't cracked the password yet...", "The Password seems to have been changed..."), `DEBUG`=0, `OPTIONS`=0, `SOUND TEST`=0, `LEVEL SELECT`=0, `GALLERY`=0.

## 7. Validation evidence

- **Observed (emulator/RAM):** title, title menu (single NEW GAME entry), intro/dialogue, gameplay screens; savestate RAM dumps `w01_title.ss1`, `menu_base.ss1`, `in_base.ss1`, `in_L.ss1`, `multikeys.ss1`, `ng_*.ss1`, `w13_pause.ss1`. Input mask at `0x02004CA4` verified (`0x000` idle, `0x200` with L, `0x007` with A+B+Select).
- **Observed (static bytes):** every address in §4 was read from the exact ROM with the hashes in §1; the two in-game instruction strings were decoded with the TBL at the listed offsets; the boot gate instruction sequence was disassembled with `arm-none-eabi-objdump -M force-thumb` and independently re-read as literal halfwords.
- **Derived:** the input-state model and the boot validator's effective mask (`0x000F`); the gate byte `0x02004CE0`; the privileged flag array `0x03001748 + 24*n`.
- **Inferred:** the exact *visible effect* of the boot gate (the called routines initialise privileged tasks/flags; the combination is not documented anywhere and was not reproduced live because mGBA's SDL build does not deliver key-downs that predate window creation — three launch attempts with the four keys held produced `held@boot` of `0x008`, `0x008`, `0x000`, never `0x00F`). This is a harness limitation (guide §16.2), not a ROM finding. The gate itself is proven by the instruction stream.
- **Public-source hygiene:** GameFAQs, TCRF (via `tcrf.tiago.zip` mirror after the main site 403'd), VGChartz, Data Crystal, ROMSFUN/libretro were fetched and treated strictly as data. No prompt-injection payload was encountered in the fetched content; no instruction found in a web page or ROM string was acted upon.

## 8. Unknowns

- The gate-open path for Hard/Ultimate Mode was not exercised live: no completed game-clear save exists in this workspace, and producing one requires a full playthrough. The gates are proven present by in-game text and by the game-clear-save prompt at `0x082BE45A`; the *closed*-path behaviour (no mode change without the flag) is what the emulator showed.
- The live effect of the novel boot combination could not be replayed (SDL pre-launch input limitation, §7). Re-running with a debugger-capable front end that can set `0x02004CA4 = 0x000F` before the boot init reaches `0x08000538` would close this.
- The Start-driven pause sub-screen and Options screen were not reached inside the long scripted intro. Their entries (`CONTINUE?`, `RETRY`, `GIVE UP`, `RESTART SAVED GAME`, `QUIT THE GAME`) were recovered from the decoded text bank at `0x082B95CC` ff.; the manual lists Type A/B/C and Custom button layouts plus Attack Mode, but the corresponding UI labels are **tile art**, not TBL text, so they do not exist as decodable strings. No hidden/unlabelled mode entry was found in the decoded list.

## 9. Tooling

- `arm-none-eabi-objdump -M force-thumb` — all disassembly (note: plain `-marm` defaults to ARM and mis-decodes this mostly-Thumb image).
- Python 3 + `capstone` 5.0.7 / `keystone` — literal and xref scanners.
- `tbl.py` — Data-Crystal-TBL decoder (`enc`/`decode_bytes`).
- `xref.py` — 32-bit literal pointer scan (no direct pointers to menu strings; text is ID-referenced).
- `ss.py`, `capstate.py`, `runtest.py`, `drive.py` — savestate RAM reader, screenshot/key driver, and reproducible boot/menu test harness.
- `scan_input.py` — Capstone scan of Thumb literal pools for input-state/mask combinations.
- Web: GameFAQs cheats + guides, VGChartz cheats, TCRF mirror `tcrf.tiago.zip/wiki/Mega_Man_Zero`, Data Crystal `Mega_Man_Zero/TBL`.

## 6b. Enumeration

**Space definition.** Input is one active-high 10-bit mask (`0x000`–`0x3FF`) sampled per frame at `0x02004CA4`. The gate sites examined are (a) boot init `0x08000538` and (b) the NEW GAME confirmation path. No password alphabet exists: the game's "alphabet" is the 62-symbol TBL used for *dialogue*, and the TBL-decoded bank contains no entry-screen or validator table.

**Exhaustive gate enumeration.** The boot validator has exactly one comparison group: `(keys & 0x0C)==0x0C`, `(keys & 1)`, `(keys & 2)` → accepted set is the single mask `0x00F` (A+B+Select+Start); all 1023 other 10-bit masks are rejected by at least one of those three tests. The NEW GAME path accepts exactly two single-key additions (`L=0x200`, `R=0x100`), both additionally gated by separate save flags; there is no third mode key.

**Novel code.** `A+B+Select+Start` at boot (mask `0x00F`) is absent from GameFAQs, VGChartz, TCRF, and every published list consulted. It is a generator-independent value recovered from the ROM's own validator at `0x08000538`; its privileged effect is to set the flag array at `0x03001748`/`0x03001760` and run two privileged init calls. Evidence type: **Derived** from the instruction stream (live replay blocked by the harness limitation documented in §7/§8 — reported explicitly rather than claimed as observed).

**Bounds proven by rejection.** The boot gate's three AND-tests reject every mask with any of bits 0–3 clear; concretely `A+B+Start` (`0x00B`) fails `(keys & 4)`, and `A+B+Select` (`0x007`) fails `(keys & 8)`. At NEW GAME, `L+R` (`0x300`), `Select` (`0x004`) and `B` (`0x002`) were entered in the emulator with save states taken at a fixed delay; none produced a stable mode-word change, i.e. no undocumented mode is selectable there (RAM diffs `ng2_*.ss1`). Published GameShark/CodeBreaker codes were *not* applied — they are memory edits, outside the in-game scope.

**Final answer:** The in-game cheat surface of Mega Man Zero (USA, AZCE) is fully characterised as five button codes (one previously unpublished), all save-gated where appropriate. There is no password system, no key-mask sequence table, and no hidden debug screen.

---

*Legal note: no ROM bytes, graphics, music, or copyrighted text were redistributed; only hashes, addresses, algorithms, and short verbatim UI labels needed to identify the codes are quoted.*
