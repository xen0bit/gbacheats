# Final Fantasy Tactics Advance (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `/mnt/gbacheats/roms/Final Fantasy Tactics Advance/Final Fantasy Tactics Advance.gba` |
| Size | 16,777,216 bytes (`0x01000000`) |
| Header title | `FFTA_USVER.` (12-byte field; the retail title string was re-tagged — see below) |
| Game code / maker | `AFXE` / `01` (Nintendo), version `0x00`, complement `0x89`, header checksum `0x0000` |
| `file(1)` | `Game Boy Advance ROM image: "FFTA_USVER." (AFXE01, Rev.00)` |
| MD5 | `cd99cdde3d45554c1b36fbeb8863b7bd` |
| SHA-1 | `4ac05441f4de70a4ec3dd932116346c61b8783d9` |
| SHA-256 | `43fc8204c6dceee58828aebc7af0c72eb807e99f35ad641c8bb0a4fa8b6edc19` |

Phase 0 result: entry word `0xEA00002E` (stock `b 0x080000C0` crt0), Nintendo logo at `0x04` intact and byte-identical to the standard 156-byte logo. A full-ROM scan for that logo found **exactly one** header (file `0x0`) — no 2-in-1 image, no appended trainer, no cracktro. The header checksum `0x0000` and the re-tagged title are consistent with an edited/rebuilt header (guide §16.1); the code itself is stock. Last 256 bytes are `0xFF` padding. The in-game title screen displays "FINAL FANTASY TACTICS ADVANCE" / "©2003 SQUARE ENIX ... Licensed to Nintendo", confirming the US SKU.

## 2. Executive summary

**There is no in-game cheat/password/button-code system and no reachable hidden debug menu in this ROM.** The only input surfaces that accept controller text are (a) the three-entry title menu and its colour-mode submenu, (b) the save/load menu, (c) the player/clan **name-entry** screen, and (d) normal battle/menu navigation. The name-entry screen is a label field, not a validator (§16.2b): its alphabet is `A-Z / a-z / . , -` plus a `123` tab, it is pre-filled with `Marche`, and no comparison against user text exists in the decoded text bank or in the `strcmp`/`memcmp`-style scan.

The one developer button code that **does** exist is the **soft reset `A+B+Start+Select`** (active-high key mask `0x000F`), verified in the emulator: it immediately reboots to the Square Enix logo. It is documented publicly (IGN "Quick Reset", CheatCodeCentral "In game reset") and is a system convenience, not a cheat.

Every published "cheat code" for this game is a GameShark / CodeBreaker / Action Replay **memory patch** (encrypted 8-hex-digit codes such as `82001F54 FFFF`, `42000098 03E7`, `D0000020 0004`) — explicitly out of scope and not interpreted by the ROM. No published password list, no published debug button combo, and no password screen exist for this SKU. TCRF's FFTA page lists only unused dialogue and regional differences; the "battlefield select debug menu" documented by TCRF belongs to the **PlayStation** *Final Fantasy Tactics*, a different game.

The game's true unlockables (Expert Missions, Judge Missions, five secret characters, credits) are ordinary **save-flag/progress gates** (§16.18), not codes: nothing in the controller input path writes those flags.

Evidence is threefold: the **entire custom-encoded text bank (2,757 strings over four pointer tables) was decoded** and contains zero debug/cheat/password/warp/test strings; **36 distinct button combinations** were pressed at the title screen with automated screen-difference classification and produced only the plain title, the normal title menu, or the soft reset; and every reachable screen was walked in mGBA with screenshots and savestate RAM snapshots.

## 3. How to reproduce

* Emulator: `mgba -3` (SDL build) on `Xvfb :315`, `SDL_AUDIODRIVER=dummy`, `openbox` WM.
* Keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrow keys. Hold 100–300 ms; key-repeat double-steps at longer holds.
* Deterministic boot: hold `Shift+F1` on the "Push START" title to store a state; `F1` restores it for each input experiment.
* Screen path: title → `Start` → `{NEW GAME, SAVED GAME, COLOR MODE}`; `COLOR MODE` → `{LCD A, LCD B, TV}`; `SAVED GAME` → `{Resume Battle (disabled with no save), Load}`; `NEW GAME` → story → name entry → tutorial snowball battle → `B` → `{Move, Action, Wait, Status}` → `Action` → `{Snowball}`; `Select` shows HELP text. `Start` does **not** open a System Menu during the tutorial battle.
* Soft reset: on any screen hold `x`+`z`+`Return`+`BackSpace` together → Square Enix boot logo.
* Button-combo sweep: for each of 36 combinations, `F1` (restore title) → simultaneous `keydown` of every button → 300 ms → `keyup` → crop the 240×160 viewport → mean-absolute-difference against reference images.
* Text decode: Python scripts `decode.py` / `decode2.py` (§9) read the four pointer tables and apply the charset in §6.

## 4. Address map

| Address (ROM unless noted) | Meaning | Evidence |
|---|---|---|
| `0x0000` | `0xEA00002E`, stock crt0 branch to `0x080000C0` | Derived (bytes) |
| `0x0004`–`0x009F` | Standard Nintendo logo (1 hit ROM-wide) | Derived |
| `0x00A0` / `0x00AC` / `0x00B0` | Title `FFTA_USVER.` / code `AFXE` / maker `01` | Derived |
| `0x08000482`–`0x0800049C` | Thumb key-read routine: `ldrh r2,[0x04000130]`; `r1 = ~r2 & 0x3FF` (active-high); pass to `0x0800221C` | Derived (disassembly) |
| `0x080004A4` / `0x080004A8` / `0x080004AC` | Literal pool: `0x03000000`, `0x04000130`, `0x000003FF` | Derived |
| `0x03000000` (IWRAM) | Active-high key-state word; confirmed `0` in savestate with no keys held | Observed (state diff) |
| `0x00541B4`…`0x00567F0` | Universal string data (767 strings) | Derived |
| `0x005567F0` | Universal string table: 767 × `u32` ROM pointers | Derived |
| `0x00526680` | Item/location-name table: 753 pointers | Derived |
| `0x0055A64C` | Mission-name table: 512 pointers (many `dummy` at the tail) | Derived |
| `0x005680DC` | Random-name table: 725 pointers | Derived |
| Savestate layout | `gbAs` zlib chunk → 397,312-byte state; IWRAM at state offset `0x19000`, EWRAM at `0x21000` | Observed |

No validator, code table, key-mask sequence table, or debug-gate word was found (search boundaries in §6b).

## 5. Algorithm

No password/serial algorithm exists. The only decoding algorithm worth recording is the game's text encoding, required to search the text bank (§6b):

```
byte 0x00              -> end of string
byte 0x01              -> start-of-string control (skip)
byte 0x40, next byte   -> space (the next byte is a width/style argument)
byte 0xB1..0xCA        -> 'A'..'Z'   (c = chr(0x41 + b - 0xB1))
byte 0xCB..0xE4        -> 'a'..'z'   (c = chr(0x61 + b - 0xCB))
byte 0xE5..0xEE        -> '0'..'9'   (confirmed by string 0x26 = "6666" = 01 EB EB EB EB 00)
byte 0x80, next byte X -> second font bank: c = charset(X + 1)
                          (e.g. 80 BC 80 CA 80 D0 80 CE = "Mage")
other bytes            -> control codes / graphics tokens (<XX>)
```

Cross-check: string index `0x02` = `01 BD D3 DD DD D3 D9 D8 00` = "Mission"; `0x01` = `80 C3 80 DE 80 DB 80 D7 40 73 ...` = "Turn Order"; job names `80 C1 80 CE 80 CD 40 73 80 BC 80 CA 80 D0 80 CE` = "Red Mage".

## 6. Tables

### 6.1 Charset (complete, derived + verified against 11 known names/jobs)

| Byte range | Characters |
|---|---|
| `0xB1`–`0xCA` | `ABCDEFGHIJKLMNOPQRSTUVWXYZ` |
| `0xCB`–`0xE4` | `abcdefghijklmnopqrstuvwxyz` |
| `0xE5`–`0xEE` | `0123456789` |
| `0x80 XX` | same table at index `XX+1` (alternate font bank) |
| `0x00`, `0x01`, `0x40 XX` | terminator, start control, space control |

### 6.2 Universal string table — first 40 entries (all menu labels in the game)

`Turn Order, Mission, Law Cards, Options, Flee, Save Now, Laws, Move, Action, Wait, Status, Fight, Snowball, Totema, Combo, Party, Clan, Link, Area List, System, Save, Load, Back, Release, Pardon, Leave, Suspended, Bail, Sentence, Trade, Gossip, Leave, Buy, Sell, Trade Items, List, Back, (6666), Play, Release, Rumors, Missions, ...`

This is the authoritative list of every command the engine can display. There is **no** `Debug`, `Sound Test`, `Battle Test`, `Warp`, `Map`, `Level Select`, `Password`, `Code`, or `Enter Name = password` entry.

### 6.3 Name-entry field (§16.2b negative)

Alphabet visible on screen: `A B C ... Z / a b c ... z / . , -`, plus a `123` tab for digits. Buttons shown: `A: Enter`, `B: Del`, `START: OK`. Pre-filled default `Marche`. It is the clan-leader name written into the save record; it is never compared to a constant. **It is not a password field.**

### 6.4 Button code present

| Code | Mask (active-high) | Effect | Evidence |
|---|---|---|---|
| `A+B+Start+Select` | `0x000F` | Warm reboot to Square Enix logo | Observed (screenshot + 103,675-byte state delta); published by IGN/CheatCC |

### 6.5 Unlockables (progress/save-flag gated, not codes)

From GameFAQs/CheatCC (corroborated by TCRF's unused-dialogue notes): Expert Missions — beat the game once, star appears next to the name; Judge Missions — clear all 300 numbered missions, then visit Bervenia Palace; secret characters Babus (Left Behind + With Babus), Shara (A Maiden's Cry + enter a town), Ritz (Mortal Snow), Cid (all 300 missions), Ezel (Gossip in Card Shop → Reconciliation); Credits — 300 missions + Judge missions. All are things the **game sets** on story/mission completion; no controller input writes them.

## 6b. Enumeration

### Screens walked (all with screenshots retained in `/tmp/opencode/ffta/`)

| # | Screen | Entries observed | RAM/snapshot evidence |
|---|---|---|---|
| 1 | Boot / Square Enix logo | — | `shot_14.png`, `softreset_shot.png` |
| 2 | Title "Push START" | — | `shot_title_baseline.png`; savestate slot 1, IWRAM `0x03000000 = 0` |
| 3 | Title menu | NEW GAME, SAVED GAME, COLOR MODE | `shot_03.png`, `shot_07.png` |
| 4 | COLOR MODE submenu | LCD A, LCD B, TV | `shot_04.png` |
| 5 | SAVED GAME menu | Resume Battle (disabled), Load | `shot_08.png`, `shot_09.png` |
| 6 | Name entry | 26+26+3 symbols + `123` tab | `shot_15.png`, `shot_16.png` |
| 7 | Story / tutorial dialogue | "Hey! That's gender discrimination!", etc. | `shot_13.png`–`shot_22.png` |
| 8 | Tutorial battle (field) | turn counter, HP/MP/JP/WT HUD | `shot_22.png`, `replay_check6.png` |
| 9 | Battle action menu | Move, Action, Wait, Status | `shot_25.png`, `battle2_menu.png` |
| 10 | Action submenu | Snowball (tutorial only) | `shot_27.png` |
| 11 | HELP overlay (Select) | "Determine what action a unit will take." | `battlekey_select.png` |
| 12 | "Repeat lesson?" / notices | Yes/No | `replay_check4.png`, `replay_check5.png` |

`Start` (System Menu) is gated off during the mandatory tutorial battle; its entries were nevertheless obtained from the decoded text bank (`System, Save, Load, Release, Pardon, Leave, Suspended, Bail, Sentence, Options, ...`). The post-tutorial world map / pub / shop / in-game Options screens are reachable only after winning the tutorial; their **complete label set** is enumerated in §6.2 from the 767-string table, so the absence of hidden menu entries there is proven statically.

### Button space (bounded negative)

* Masks derived from `~KEYINPUT & 0x3FF`: A=1, B=2, Sel=4, St=8, Right=0x10, Left=0x20, Up=0x40, Down=0x80, R=0x100, L=0x200.
* **36 combinations** tested at the title: all `C(6,2)=15` pairs of {A,B,L,R,Start,Select}; all 16 triples containing L or R; all 5 quadruples containing L and R; plus 12 manual combinations including `A+B+Start+Select`.
* Automated classification against reference images (`combo_test_results.txt`): 25 combinations → plain title screen (mean abs diff 0.0–0.3), 10 → normal title menu (diff 1.5–4.0), 1 (`A+B+Start+Select`) → reboot. **Zero combinations produced a novel screen** (no image differed from both references by >12 mean-absolute units).
* Conclusion: the title-screen button space contains exactly one special code (soft reset) and no debug entry.

### Text space (bounded negative)

| Table | ROM base | Entries | Decoded |
|---|---|---:|---:|
| Universal strings | `0x005567F0` | 767 | 767 |
| Item/location names | `0x00526680` | 753 | 753 |
| Mission names | `0x0055A64C` | 512 | 512 |
| Random names | `0x005680DC` | 725 | 725 |
| **Total** | | **2,757** | **2,757 (100%)** |

Keyword census over all 2,757 decoded strings: `debug` 0, `password` 0, `cheat` 0, `warp` 0, `sound test` 0, `battle test` 0, `level select` 0, `code` 0, `test` 0, `invalid` 0, `develop` 0, `hidden` 1 (`Hidden Vein`, a mission), `secret` 3 (`Secret Books` item + mission, `Stone Secret` mission), `demo` 2 (substring of `Demon Bell`, `Demon Redux`). `dummy`/`Dummy` placeholders: 110 in the universal table, plus unused mission-name tails — consistent with Data Crystal's published count. `strings -t x -n 4` on the raw ROM produced **zero** English keyword hits (all output is binary/font data), which is why the font decode was mandatory before a negative could be claimed.

### Published-code verification

Every code found by web search (GameFAQs FAQ 26118/25621/40618, CheatCC, Ethereal Games, 53lu, ROMSFUN, supercheats) is a GameShark/CodeBreaker/Action-Replay **memory patch** or an encrypted 12-hex PAR3 code. Examples verified against the ROM text: `82001F54 FFFF` (money), `42000098 03E7` (HP), `D0000020 0004` (Select-to-win), `74000130 00FF` (L+R weaken enemies), master code `000037AE 000A / 10000488 0007`. None is a literal in the ROM (they are external patch instructions), none is in scope, and none was applied. **No password literal, no published debug combo, and no PS2/console-version code applies to this SKU.** The one published button code (`A+B+Start+Select`) was entered and confirmed.

### Cross-check with sibling sessions (independent)

TCRF documents an extensive debug menu for *Final Fantasy IV Advance* (TOSE engine, debug room reached by memory patch) and unused text for *Final Fantasy I & II: Dawn of Souls*. Those are different engines/SKUs; nothing found here is shared with the GBA titles analysed on `:316`/`:317`. The PS1 *Final Fantasy Tactics* battlefield debug menu likewise does not exist in this GBA image.

## 7. Validation evidence

* **Observed** — title/title-menu/colour-mode/save-load/name-entry/battle/help screens (screenshots listed in §6b); soft reset to Square Enix logo on `A+B+Start+Select`; 36-combo classification with no novel screen; savestate `gbAs` IWRAM `0x03000000 = 0x00000000` at rest and a 103,675-byte state change across reboot; single Nintendo logo / single GBA header; full custom text bank decoded.
* **Derived** — key-read routine and active-high mask at `0x08000482`/`0x080004A4`–`AC` (Thumb disassembly); charset mapping (verified against 11 published names and 4 menu strings); four pointer tables and entry counts; soft-reset mask `0x000F`; absence of any hidden command in the 767-entry universal table.
* **Inferred** — the post-tutorial System Menu/Options contents are inferred from the decoded table rather than from a live visit (tutorial battle gates `Start`); the unlockable flags are inferred to be save-record bits rather than code-triggered, because no input path writes them and no code surface exists. Both are reported as inference, not observation.

## 8. Unknowns

* The world-map/pub/shop and in-game Options screens were not visited in the emulator; the mandatory tutorial battle gates them and winning it requires a full playthrough. Their label inventory is complete from the text bank, so the "no hidden entry" claim for those screens rests on static rather than visual evidence.
* The exact save-record bit offsets for the five secret characters / mission unlocks were not isolated; §16.18-style setter-call-site enumeration was not completed. They are progress-gated by the game's own design; no code path was found that a player could invoke.
* The 110 `Dummy` strings are genuinely placeholder text (decoded to the literal word "Dummy"); no hidden payload was recovered from them.
* The header title field was re-tagged to `FFTA_USVER.` and its checksum/complement are inconsistent with a pristine Nintendo header; the dumped image is nevertheless functional and code-identical at the entry point.

## 9. Tooling

* `mgba -3` (SDL) + `Xvfb :315` + `openbox`, `xdotool` XTEST input, `import -window root` screenshots.
* `decode.py` / `decode2.py` — Python charset decoders for the four pointer tables (output `decoded_full.txt`, 2,757 rows). `keyscan.py`, `buttonscan.py` — Capstone/raw Thumb scans for `KEYINPUT` literals and key-mask comparisons. `combo_test.py` + PIL/numpy — 36-combo sweep with image-difference classification. `savestate.py` — parse mGBA `.ss1` PNG, zlib-decompress `gbAs` chunk, diff IWRAM. `objdump -M force-thumb` for the key routine at `0x08000482`.
* Web sources: TCRF FFTA page (archived 2023-11-27), Data Crystal FFTA ROM map / string tables, GameFAQs FAQs 26118/25621/40618 and cheats page, CheatCC, Ethereal Games, 53lu, IGN GBA cheats.
* No ROM or copyrighted asset is redistributed; only hashes, addresses, algorithms, and my own scripts are reported.

---

**Bottom line:** no password, no button-code beyond `A+B+Start+Select` (soft reset), no hidden/debug menu, and no unlockable obtainable by player input. Developer-intended unlockables are progress flags. All GameShark/CodeBreaker material is external memory patching and out of scope.
