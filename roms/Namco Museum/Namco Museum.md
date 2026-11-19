# Namco Museum (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Namco Museum/Namco Museum.gba` |
| Size | 4,194,304 bytes (0x400000, 4 MiB) |
| Header title | `NAMCOMUSEUM` |
| Game code / maker | `ANME` / `AF` (AGB-ANME-USA, Rev.00) |
| Version / fixed / complement / checksum | 0x00 / 0x96 / 0x5F / 0x0000 |
| Entry word | `0xEA00002E` → `b 0x080000C0` (stock, unpatched) |
| MD5 | `60ac7a006e8a00581b832ceb8a000305` |
| SHA-1 | `01090d75a45eb4ab326c6299646e946afc7d0be9` |
| SHA-256 | `c050b53427fd25dbbd57d04ec34c3010a049672540433dca866287d5226a9f5d` |

**Phase 0 / embedded-header scan.** The 156-byte Nintendo logo occurs exactly once, at file offset `0x4`. There is no second GBA header, multiboot stub, or concatenated image: this is one flat ROM, not a 2-in-1 pack. The entry branch and first 0x200 bytes are the standard ARM crt0; no cracktro, appended trainer, or boot patch was found. The complement byte sum over `0xA0..0xBD` is `0xE7` rather than `0x00` and the header checksum is `0x0000` — a rebuilt/edited-header artifact only; it does not affect the running image (verified: the ROM boots to the stock title screen).

**Component games (confirmed in ROM and on the game-select screen):** Ms. Pac-Man, Pole Position, Dig Dug, Galaga, Galaxian — exactly five. Pac-Man and the "Arrangement"/hidden games advertised on some platform versions of Namco Museum are **not** in this GBA image. This image was verified independently of the sibling *Namco Museum 50th Anniversary* build (different developer, Digital Eclipse, different game code); no code, string, or address from that title was carried over.

## 2. Executive summary

This image has **no password system, no button-code system, no unlockable, and no reachable hidden debug menu**. The only developer-intended configuration surface is an ordinary per-game **SETTINGS** screen (pause → Settings) that exposes arcade DIP-switch-style options (Lives display, Bonus thresholds, Difficulty, qualifying/race times). These are normal options, not cheats, and are fully documented below with addresses and RAM evidence.

A bound was put on each possible "no":

* Every reachable screen was walked in mGBA with screenshots and savestate/RAM confirmation (title → credits → five-game select → each game's attract/banner → gameplay → pause → Settings → Tips → game over → attract loop).
* The complete menu tables were recovered statically (`0x080A6880`–`0x080A6E40`): 4 pause entries, 6 distinct settings menus, 40+ option-value pointers. Every entry's label and record layout is known; no unlabelled or hidden entry exists in these tables.
* Text was searched in ASCII, in `+0x20`-shifted form, and in the arcade banks' custom encoding (`@` = space, `?` = terminator). The one font/alphabet bank (`0x0809B17E`, 46 symbols) and the digit parser that uses it (`0x0802F398`) were reverse engineered and shown to be **score rendering / high-score-initials display**, not a password validator.
* All key-input paths were mapped: the single KEYINPUT literal (`0x080580EC`) and the derived `held`/`pressed` globals; seven published button-code sequences were searched as u16 and byte masks in the ROM with zero hits, and the documented Galaga timer code plus four combination codes were pressed on the live title/attract screens with no effect.
* Every published GBA "cheat" found on the web is an **Action Replay / GameShark memory patch** (master code `BD86B55A…` plus per-game lives/timer codes). None is an in-game code, and none is in scope for this report. The ROM contains none of these literals because they are external patch codes, not game data.
* The Dig Dug arcade self-test strings (`RAM OK`, `ROM OK`, `UPRIGHT`, `RANK`, `SOUND`, `BISLPS-…`) and their render routine (`0x08013C8C`) exist, but the screen is not reachable from any walked screen or tested input combination; it is a leftover from the arcade source, labelled **dead/gated — not reachable through controller input in the walked space**.

## 3. How to reproduce

* Emulator: `mgba 0.10.5` (SDL build) under `Xvfb :319 -screen 0 1024x768x24`, `openbox`, `SDL_AUDIODRIVER=dummy`. Use `-s 2` (frameskip 2) — without it this build crashed during long Ms. Pac-Man/Galaga sessions in this container; with it every walk completed. Window geometry for 3× scale: content at screen `+153+164`, 720×480.
* Keymap (mGBA SDL default): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows. Hold 150–300 ms; wait for the title's **PRESS START** to be fully drawn (~8–10 s after boot) before pressing Start — earlier presses are ignored.
* Minimal reproducible paths:
  * **Game select:** boot → wait for title → `Start` → five logos cycle with Left/Right; `A` enters a game's attract/banner.
  * **Pause / settings / tips:** enter any game → `Start` → `CONTINUE / SETTINGS / TIPS / MAIN MENU`; `Down`/`Up` move the cursor, `A` selects, `B` returns. Galaga SETTINGS: `LIVES` (read-only, 3), `BONUS` (`Left`/`Right` adjust REST threshold; observed 60K/70K/80K), `DONE`. Ms. Pac-Man SETTINGS additionally offers `1st`, `2nd`, `Rest`, `Difficulty`; Pole Position SETTINGS offers `Qualifying Diff`, `Qualify Time`, `Goal After Laps`, `Extended Time`.
  * **Gameplay/initials:** on Ms. Pac-Man's select banner press `A` to enter the attract, then `A` during the maze to start a game (`READY!`, 3 lives). Let the ghosts kill the player three times; game over shows `GAME OVER` and returns to the attract loop — **no initials prompt appeared** at any point.
* Input reachability was proven by saving a state with `Shift+F1` while holding a key and reading the recorded `KEYINPUT`: with Start held the state word at `gbAs+0x530` is `0x3F7`; with Right held it is `0x3EF`; released it is `0x3FF`.
* Savestate RAM mapping (verified by cross-checking live debugger reads): for this 4 MiB ROM the decompressed `gbAs` PNG chunk is 397,312 bytes; `state[0x21000 + (addr−0x02000000)]` is EWRAM and `state[0x19000 + (addr−0x03000000)]` is IWRAM. `state[0x530]` is KEYINPUT.

## 4. Address map

| Item | ROM / RAM address | Notes |
|---|---|---|
| Header / crt0 | `0x08000000` / entry `0x080000C0` | single header; stock branch |
| Central input reader | `0x080580CC`–`0x080580EA` | reads `0x04000130`, inverts, computes pressed/held |
| KEYINPUT literal pool word | `0x080580EC` = `0x04000130` | only 32-bit occurrence of that address |
| Derived input globals | `0x02024618` (previous held), `0x0202461A` (pressed) | written by `strh` at `0x080580E2/E4` |
| Menu tables (pause + settings) | `0x080A6880`–`0x080A6E40` | 16-byte records `{type, value, 0, string_ptr}` |
| Menu label bank | `0x0807CA38`–`0x0807CAF0` | `Main Menu`, `Continue`, `Settings`, `Tips`, `Done`, `Lives`, `Bonus`, `Difficulty`, `Extended Time`, … |
| Option-value string bank | `0x0807CB0C`–`0x0807D…` | `None/4000/5000/7000`, `Easy/Normal/Hard/Expert/8-Hard/Easy-1`, `100K/120K/150K`, … |
| Dig Dug high-score/initials strings | `0x0808AE20`–`0x0808AF40` | `AAA`, `1ST..5TH`, `ENTER YOUR INITIALS`, `RAM OK`, `ROM OK`, `UPRIGHT` |
| Galaxian text bank (custom encoding) | `0x080A94B0`–`0x080A9660` | `@`=space, `?`=terminator; decoded (see §6) |
| Pole Position text bank | `0x080EC3F1`–`0x080EC6D0` | includes three `ENTER YOUR INITIALS` strings |
| Font alphabet | `0x0809B17E` | 46 bytes: `0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ ????%.?!?` |
| Alphabet mapper | `0x0802F406`–`0x0802F412` | index → alphabet byte |
| Score digit parser | `0x0802F398`–`0x0802F404` | 6 BCD digits, skips `0x24` (`$`) blank |
| Score/name routine callers | `0x0802F28A`, `0x0802F384` (→ parser); `0x08027DBC`, `0x080315F2` (→ `0x0802F380`) | buffer `0x0201945E` → result at IWRAM `0x03001BE8` |
| Galaga BONUS REST index (RAM) | `0x02002E58` | observed 1→2→0 for 70K→80K→60K |
| Dig Dug self-test render | `0x08013C8C`, caller `0x08013BC2` | strings at `0x0808AEA0` etc.; no reachable caller found |
| Savestate KEYINPUT | chunk offset `0x530` | verified 0x3FF / 0x3F7 / 0x3EF |

## 5. Algorithm

**Input handling (derived from disassembly at `0x080580CC`):**

```
held_raw = ldrh(0x04000130)            # active-low
held     = (~held_raw) & 0xFFFF        # active-high: A=1 B=2 Sel=4 Start=8
                                      # Right=0x10 Left=0x20 Up=0x40 Down=0x80 R=0x100 L=0x200
pressed  = held & ~prev
prev     = held
store pressed -> 0x0202461A ; store prev -> 0x02024618
```

Every menu and game in this shell consumes these globals; there is no second input path and no multi-press history buffer in the searched space.

**Score/name display (derived from `0x0802F398`):**

```
v = 0
for c in six_bytes_at(0x0201945E):     # c0..c5, BCD digit 0..9 or 0x24='$' blank
    if c != 0x24: v = v*10 + c
return v*10
```

`0x0802F406` maps a 0..45 index through the 46-symbol table at `0x0809B17E`. Together these render the arcade score and the fixed high-score initials — they do **not** validate user input. This is why the "alphabet" looks like a password alphabet but is not one.

**Menu records (derived from the static table at `0x080A6880`):**

```
struct MenuItem { u32 type; u32 value; u32 reserved; u32 label_ptr; };
# type 0x00 = read-only label, 0x03 = adjustable option, 0x0B/0x40 = command
# menus are terminated by an all-zero record
```

## 6. Tables

**Pause menu (`0x080A6960`…):** `Continue` (cmd), `Settings` (cmd), `Tips` (cmd), `Main Menu` (cmd).

**Settings menus (each terminated by zero record):**

| Base | Items | Game (by observed structure) |
|---|---|---|
| `0x080A6A60` | Lives(label), Bonus(adjust), Done | Galaxian-type |
| `0x080A6AE0` | Lives(label), Bonus, Done | Galaga-type (observed live) |
| `0x080A6B60` | Lives(label), Bonus, Done | Dig Dug-type |
| `0x080A6BE0` | Lives, Bonus, 1st, Rest, Done | Pole Position-type |
| `0x080A6CA0` | Lives, Bonus, 1st, 2nd, Rest, Difficulty, Done | Ms. Pac-Man-type |
| `0x080A6DA0` | Qualifying Diff, Qualify Time, Goal After Laps, Extended Time, Done | Pole Position race setup |

**Font alphabet (`0x0809B17E`, length 46):** indices 0–9 `0-9`, 10–35 `A-Z`, 36 space, 37–40 four symbol placeholders, 41 `%`, 42 `.`, 43 `?`, 44 `!`, 45 `?`. It is referenced only by `0x0802F414`.

**Decoded arcade text banks:** Galaxian (`0x080A94B0`+), with `@`→space and `?`→end, yields `GAME OVER`, `PUSH BUTTON A OR B`, `PLAYER ONE/TWO`, `HIGH SCORE`, `CREDIT`, `BONUS GALAXIP FOR 00`, `CONVOY CHARGER`, `SCORE ADVANCE TABLE`, `MISSION DESTROY ALIENS`, `WE ARE THE GALAXIANS`, `FREE PLAY`, `PAUSE`, `© 1979 1999 NAMCO LTD`. Pole Position (`0x080EC3F1`+) yields `PASSING BONUS 50`, `TIME BONUS 200`, `EXTENDED PLAY!`, `ENTER YOUR INITIALS`, `THE PAST 300 GAMES RECORD`, `FASTEST LAP`, `AVERAGE SPEED`, `PRIZE WINNERS`, `NO. SCORE TIME NAME`. No hidden message or code hint appears in either bank.

**Published codes tested (all rejected as out of scope / absent as in-game data):**

| Source | Code | Result |
|---|---|---|
| GameFAQs / Codejunkies GBA | Master `(M) BD86B55A 6B4F2EBE 734499E3 1E4426A9` | Action Replay master patch; not game data |
| GameFAQs / Codejunkies GBA | Galaxian Lives `EA907865 9F51C018`, Ms Pacman Lives `EE03A379 B803F5BD`, Pole Position Timer `A25437D1 1F86033C`, Dig Dug Lives `5DBE33A0 C2F8F2DC`, Galaga Lives `4CB1B5B4 BCF1DB3E` | Action Replay memory patches; not in-game codes |
| GameFAQs (other platforms) | Galaga Arrangement timer `Left Right Left Right Up Down Up Down` | Literal not in ROM (searched as u16 and byte masks); pressing it on the live Galaga attract produced no change |
| GameFAQs (GB/other) | `L+R+Start+Select`, `L+R`, `A+B`, `Start+Select` on title/attract | No hidden screen; `Start+Select` only invokes the normal pause menu |

## 6b. Enumeration

This engagement is a **bounded negative**; §0.2's enum deliverable is therefore the complete enumeration of the searched spaces and the rejection tests, not a minted password.

**Space enumeration (what was actually counted):**

1. **Screen space:** 8 screen classes walked with evidence — boot logos, title, credits, five-entry game select, per-game attract/banner, gameplay (Ms. Pac-Man and Dig Dug exercised), pause submenu (4 entries), Settings (6 distinct tables, 40+ option records), Tips, game-over/attract loop. No sixth game, Arrangement mode, gallery, sound test, or debug entry exists in any walked screen or in the 16-byte-record menu tables.
2. **Text/alphabet space:** 31,380 ASCII strings scanned. Keyword families `password|cheat|code|debug|secret|unlock|initial|high score|bonus|hidden|menu` classified: menu/UI labels, arcade self-test leftovers, and score/initials display text only. Two non-ASCII/custom text banks decoded in full (§6); one 46-symbol font alphabet recovered and its two consumers disassembled. No user-entered code string is compared to any table.
3. **Button-mask space:** the single input path (`0x080580CC`, one KEYINPUT literal) was located; seven published sequences (Galaga timer `L,R,L,R,U,D,U,D`, Konami `U,U,D,D,L,R,L,R,B,A`, and four shorter prefix variants) were searched as u16 little-endian and one-byte-per-press arrays across all 4 MiB — zero hits. Four live combination tests on title/attract produced no hidden screen.
4. **Unlock space:** the ROM has no battery save (0-byte `.sav` created by mGBA); no SRAM/Flash unlock flag structure exists. The menu tables contain no gated entry. Dig Dug's self-test render (`0x08013C8C`) is triggered only from a routine at `0x08013BC2` whose gate flags were never observed set by any walked screen or tested input; classified dead/unreachable in the reachable input space.
5. **Published-code space:** all seven distinct published GBA codes were located and classified as external Action Replay memory patches; zero in-game codes exist for this SKU on the consulted sources (GameFAQs GBA 516671, archived GameFAQs, TCRF, Codejunkies, 53lu, Cheat Happens).

**Bounds proven by rejection (observed):**

* Start pressed before the title is fully drawn is ignored — the accepted input window is bounded by the title animation (observed repeatedly; key reachability proved by KEYINPUT `0x3F7`).
* Ms. Pac-Man game over at score 120 with HIGH 120 records the score but **rejects the initials prompt** — the flow returns to attract with no entry screen, bounding the "high-score name generator" easter egg (a SNES-version feature) as absent here.
* Galaga BONUS REST was driven 70K → 80K → 60K with `Right`/`Left` and RAM-verified at `0x02002E58` = 1 → 2 → 0; the cursor wraps from `DONE` back to the first item rather than leaving the screen. Values outside the displayed set are unreachable by the on-screen control (the option is a finite index, not an arbitrary numeric entry).
* The published Galaga timer button code and L+R+Start+Select were rejected on the live title/attract screens (no state or screen change, verified by screenshots).

No novel code could be minted because there is no validator/table to invert; the enumeration above is the complete deliverable for this negative result.

## 7. Validation evidence

* **Observed:** screenshots of every screen class (work dir `/tmp/opencode/namcomuseum/`: `s_menu.png`, `sel_montage.png`, `f3_m.png`, `w_mont.png`, `r2_m.png`, `bonus_m.png`, `tips_m.png`, `go_m.png`, `goafter_m.png`, `dbg_m.png`, `code_m.png`); savestate RAM reads (KEYINPUT at `gbAs+0x530`, EWRAM maps verified against live debugger reads); mGBA crash reproduced without `-s 2` and eliminated with it.
* **Derived:** input globals and menu record layout from Thumb disassembly; score parser and alphabet mapper from `0x0802F398`/`0x0802F406`; menu tables from the 16-byte record pointers at `0x080A68xx`; savestate→GBA address mapping confirmed by matching live reads.
* **Inferred (clearly labelled):** the Dig Dug self-test screen is dead/gated because no caller from a reachable screen was found and no tested input reaches it — the gate flag itself was not exhaustively proven over all possible RAM states.

## 8. Unknowns

* The exact bit meaning of the Dig Dug self-test gate byte at `0x0200E4A4` (`0xF020` mask at `0x08013BEC`) was not fully resolved; only the absence of a reachable trigger was demonstrated.
* Pole Position's initials entry (`0x080EC457`, `0x080EC645`, `0x080EC696`) was not triggered in a live race — reaching it requires a qualifying lap, which is a gameplay-skill gate rather than a code gate. Its strings were decoded and its presence is recorded; no attempt was made to force it by patching race state, to keep the evidence within the walked input space.
* Whether mGBA's crashes without frameskip are an emulator bug or an artifact of this container was not isolated; `-s 2` made all walks reproducible.

## 9. Tooling

* `file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings -t x`, custom Python header/logo scanner (`phase0.py`).
* `arm-none-eabi-objdump -M force-thumb` for all disassembly; Capstone 5.0.7 / Keystone for literal and BL scanning.
* mGBA 0.10.5 under Xvfb :319 + openbox; `xdotool` XTEST input; `scrot` + ImageMagick crops/montages.
* Savestate RAM reader: Python PNG `gbAs` chunk zlib-decompress (`ss.py`), with verified EWRAM/IWRAM offsets; mGBA `-d` pty debugger used once to validate the mapping.
* Web: GameFAQs (live and web.archive.org), TCRF, Codejunkies, 53lu, Cheat Happens, Wikipedia, arcade-history — treated strictly as data; no instructions found in fetched content were followed.

**Legal note:** no ROM bytes, graphics, music, or extracted assets are redistributed here — only hashes, addresses, decoded control text, and analysis artifacts.

**Cleanup:** all processes started for this job (Xvfb :319, openbox, mGBA, debugger daemon) were terminated by PID, and all generated `.sav` / `.ss1` files were removed from the ROM folder. No other display or process was touched.
