# Teen Titans (GBA) — Reverse Engineering Report

## 1. Target identity

| Item | Value |
|---|---|
| File | `Teen Titans.gba` |
| Size | 8,388,608 bytes (0x800000) |
| Header title | `TEENTITANS` |
| Game code | `BBLE` |
| Maker | `5G` (Majesco) |
| Version | 0 (`file(1)` reports `Rev.00`) |
| Entry word | `0xEA00002E` — stock branch to `0x080000C0` |
| Fixed byte `0x96` | present; complement `0xC1`; header checksum `0x0000` |
| MD5 | `148c4190c830886bece41eb380ea3533` |
| SHA-1 | `94bf3fc459321450ff2b1e75a0b98efacffd2d0b` |
| SHA-256 | `04241087037a1117928eb4936869d79b296d64a030b75cd572042725df3914c6` |

**Phase 0:** exactly one Nintendo-logo header at file `0x0`; no appended image, no
multiboot stub, no cracktro/trainer. The ASCII string `GAX Sound Engine 3.05A`
(file `0x19220C`) and `Shin'en Multimedia. Code: B.Wodok` (`0x192232`) are the
audio-driver banner, **not** a cheat. Build stamp in the image is `Aug 15 2005
14:42:47` (TCRF mirror, independently consistent with the 2005 retail date).

Analysis was performed **independently** of the sibling *Teen Titans 2* job.

## 2. Executive summary

There is **no developer-intended password or button-code system in this GBA SKU**.
The reachable in-game "cheat" surface is entirely **completion-gated unlockables**
in the Extras/Bonus screen:

* Extras menu (all five languages) contains `ASSET VIEWER`, `BIOCARDS`, `CHEATS`,
  `MUSIC`, `SFX`. At 0% completion only `Biocards` is live; the others render red
  (locked). The `CHEATS` item is reachable only after the corresponding completion
  threshold is met. Its effect messages are `UNLIMITED HP`, `UNLIMITED PP`,
  `WARP TO POSITION <n>`, and `YOUR STRENGTH INCREASED BY <n>`.
* A full **developer debug menu data table** (19 records) and its ASCII label bank
  survive in the retail image: `Obj Viewer`, `Music Player`, `Fx Player`,
  `Mission - Tutorial`, `Mission - 01`…`Mission - 06`, `Gizmo`, `Jinx`,
  `Mammoth`, `Brother Blood`, `Normal Boot`, `Missions ->`, `Bosses ->`,
  `Asset Viewer ->`, `Prototype`. TCRF explicitly states that whether it can be
  accessed "needs investigation". This report shows the gate bits are **ROM
  constants that are zero in every normal scene configuration**, with no runtime
  writer found — a bounded *gated/cut feature* negative, not "not tested".
* No published password/button code exists for the GBA version. GameFAQs, TCRF,
  ChapterCheats, CheatingDome and VGChartz list only completion unlockables. The
  button-sequence cheats published for *Teen Titans* belong to the **PS2 / GC /
  Xbox** SKUs (same developer, different engine) and were verified **absent** from
  this GBA image under every encoding tried. The one Substack "New codes" index
  entry for *Teen Titans* is likewise PS2/GC/Xbox, not GBA.

Because the accepted set is empty for a code/password surface, the deliverable is
a **bounded negative with counts** (§6b) plus a complete enumeration of the
unlockable cheat surface. No novel code could be minted: there is no validator to
reverse. This is not a confirmation of the public list.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 (SDL), `SDL_AUDIODRIVER=dummy`, Xvfb `:318` + openbox,
  `-3` scale. Window crop used throughout: `720x480+154+184`.
* Keymap (mGBA SDL default): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
  Select=`BackSpace`, D-pad = arrow keys. Hold 80–150 ms.
* Boot: intro logos → title (`Press Start`) → save select (`New`, `No 1`, `No 2`).
  Starting `New` runs a Mission-1 banner, a save-icon tutorial, then gameplay.
* In gameplay: Start opens the pause menu — `Stats`, `Options`, `Extras`,
  `Save Game` (greyed), `Quit Game`. `Options` = Language / Music / SFX.
  `Extras` = Biocards (blue/live), SFX, Music, Asset Viewer (red/locked). The
  cursor wraps at four entries; no fifth entry appears at 0% completion.
* Savestates: `Shift+F1`/`F2` (mGBA slot 1/2). States were saved at the main menu
  and at the Extras screen. mGBA `.ss2` is a PNG with a zlib `gbAs` chunk; the
  decompressed 397,312-byte state places EWRAM at state offset `0x21000`.
* Key RAM observation: the live save mirror is at EWRAM `0x02003280` (state
  `0x24280`); bytes `41 32 43 58` = ASCII `A2CX` at `0x02003288` — the same magic
  stored byte-reversed as `58 43 32 41` (`XC2A`) in SRAM offset `0x0C`.

## 4. Address map

All offsets are **file offsets**; ROM address = `0x08000000 + file offset`.

| Item | File offset | ROM address | Notes |
|---|---:|---|---|
| Stock crt0 / entry | `0x00000000` | `0x08000000` | `b 0x080000C0` |
| Save validator | — | `0x08033CC4` | calls checker at `0x08033D58` |
| Save magic / checksum data | `0x199768` | `0x08199768` | `0x04070305`, then `41 32 43 58` = `A2CX`, then pointer list |
| Save byte-checksum helper | — | `0x08033DA8` | 16-bit byte sum used by validator |
| Debug HUD init (stores `Level`/`MapX`/`MapY` labels) | — | `0x0802F7B4` | referenced as Thumb ptr `0x0802F7B5` in table at ROM `0x08197348` |
| Debug HUD bits (read from config) | — | `0x08030536`–`0x08030582` | `ldrh [r0,#20]`, test `&1` and `&2`; both 0 in normal play |
| Scene-config pointer global | EWRAM | `0x02003714` | held `0x08730134` at Extras screen; `[cfg+0x14]` u16 = 0x0000 |
| ASCII debug label bank | `0x573F4`–`0x57530` | `0x080573F4`–`0x08057530` | 24 strings, incl. 12 ROM pointers at `0x57550`–`0x57588` |
| Debug menu definition table | `0x199558`–`0x199768` | `0x08199558`–`0x08199768` | 19 records × 0x1C; fields `[0]=action ptr`, `[4]=params`, `[0x14]=label ptr` |
| Debug-menu label pointers | `0x19956C`–`0x199764` | `0x0819956C`–`0x08199764` | 19 pointers, stride 0x1C |
| Extras labels (English text bank) | `0x7396D0`–`0x739728` | `0x087396D0`–`0x08739728` | `ASSET VIEWER`, `BIOCARDS`, `CHEATS`, `MUSIC`, `SFX` |
| `DEBUG CHEATS` string | `0x739640` | `0x08739640` | header `03 00 C9 00 00 00 00 00` |
| Cheat-effect strings | `0x739774`–`0x7399F8` | `0x08739774`–`0x087399F8` | `YOUR STRENGTH INCREASED BY`, `UNLIMITED HP`, `UNLIMITED PP`, `WARP TO POSITION`, `YES` |
| Unlock-requirement strings | `0x737648`–`0x738010` | `0x08737648`–`0x08738010` | 25+ strings incl. 25/50/75% completion |
| Pause-menu labels | `0x73B078`–`0x73B0D0` | `0x0873B078`–`0x0873B0D0` | EXTRAS, OPTIONS, QUIT GAME, SAVE GAME, STATS |
| Save mirror in EWRAM | — | `0x02003280` | SRAM image, magic `A2CX` at `+8`, byte-reversed vs `.sav` |

Debug menu table contents (label → encoded params):

```
Obj Viewer          action=0x08199769  params=0x00070007
Music Player        action=0x08199769  params=0x00080007
Fx Player           action=0x0819976A  params=0x0006B700
Mission - Tutorial  action=0x0819976A  params=0x00060000, 0x80030000
Mission - 01        action=0x0819976A  params=0x00060000, 0x80010000
Mission - 02        action=0x0819976A  params=0x00060000, 0x80050000
Mission - 03        action=0x0819976A  params=0x00060000, 0x80060000
Mission - 04        action=0x0819976A  params=0x00060000, 0x80070000
Mission - 05        action=0x0819976A  params=0x00060000, 0x80020000
Mission - 06        action=0x0819976B  params=0x00060100, 0x80010000
Gizmo               action=0x0819976B  params=0x00065300, 0x80050000
Jinx                action=0x0819976B  params=0x00061B00, 0x80060000
Mammoth             action=0x0819976B  params=0x00062900, 0x80020000
Brother Blood       action=0x08199768  params=0x00064701
Normal Boot         action=0x08199768  params=0
Missions ->>        action=0x08199768
Bosses ->>          action=0x08199768
Asset Viewer ->>    action=0x08199768
Prototype           action=0x08199768  tail data 0x04070305 / "A2CX" / ptr list
```

The four "action" values `0x08199768/69/6A/6B` point into the save-magic/tail
region, i.e. into data rather than executable code; no Thumb `BL`/`BLX` or
executable 32-bit pointer targets any of these records (see §6b).

## 5. Algorithm / data formats

### 5.1 Save format (derived)
* SRAM is 512 bytes. Magic `41 32 43 58` (`A2CX`) at internal offset `+8`; the
  `.sav` image stores it byte-reversed as `58 43 32 41` at SRAM offset `0x0C`.
* Validator at `0x08033CC4` → `0x08033D58` compares four bytes at `[state+8]`
  with the literal at `0x0819976C` (`A2CX`) and computes a 16-bit byte sum over
  16 bytes via `0x08033DA8`; a mismatch calls `0x08033E34` (save rejected/cleared).
* Two 0xA00-byte save slots (stride `0xA8` in the inner copy) follow the header.
* All unlock state (difficulties, Extras, Biocards, completion counters) lives in
  this record. No code entry point reads it as a password.

### 5.2 Text-bank encoding (derived, decoded before any negative)
The tile/text bank is **not ASCII**. Encoding, recovered from the Extras labels:

* Each string is preceded by an 8-byte record header, typically
  `03 00 C8 00 00 00 00 00` (Extras items) or `03 00 C9 00 00 00 00 00`
  (cheat/unlock messages).
* The **first character is stored with `-0x20`** and rendered as a capital:
  bytes `23 48 45 41 54 53` → `0x23+0x20='C'`, then `HEATS` → **`CHEATS`**.
  Likewise `21 53 53 45 54 … 36 49 45 57 45 52` → `ASSET VIEWER`,
  `22 49 4F 43 41 52 44 53` → `BIOCARDS`, `2D 55 53 49 43` → `MUSIC`.
* `FF FC` = space, `FF FE` = string terminator, other `FF xx` = control glyph
  (e.g. `<0D>` punctuation, `<11>`/`12`/`15` digits).
* All five language banks (English `0x737xxx`, French `0x73Cxxx`, Spanish
  `0x741xxx`, German `0x749xxx`, Italian `0x74Exxx`) were decoded; they carry the
  same Extras and CHEATS structure. French `TRICHES`, German `CHEATS<0D>DEBUG`,
  Spanish `TRUCOS`, Italian `CHEAT` all confirm the same menu item.

## 6. Tables

### 6.1 Unlockables (published list verified against ROM strings)
Every published unlock requirement string is present in the ROM text bank, so
the GameFAQs/ChapterCheats lists are verified for this exact image:

| Unlockable | Gate (in-game string) |
|---|---|
| Sound Effects & Voice Test (`SFX`) | `25 PERCENT GAME COMPLETION` (`0x737BF4`) |
| Music Test | `50 PERCENT GAME COMPLETION` (`0x737C1C`) |
| Asset Viewer | `75 PERCENT GAME COMPLETION` (`0x737E48`) |
| Hero difficulty | `COMPLETE ALL MISSIONS AT NORMAL MODE` (`0x7377B4`) |
| Titans difficulty | `COMPLETE ALL MISSIONS AT HERO MODE` (`0x737C88`) |
| Biocards 01–25 | per-mission / per-card / per-difficulty requirements at `0x737648`–`0x738010` (25 distinct strings) |
| `CHEATS` Extras item | string present (`0x7396FC`); exact threshold not printed — **unknown** (§8) |

Cheat effects whose strings exist in the image (shown when the CHEATS extras item
is used): `UNLIMITED HP`, `UNLIMITED PP`, `WARP TO POSITION <n>`,
`YOUR STRENGTH INCREASED BY <n>`.

### 6.2 Published-code reconciliation
| Source | Claim | GBA verification |
|---|---|---|
| GameFAQs / ChapterCheats / CheatingDome | unlockables only | all requirement strings present |
| TCRF (GBA page) | debug menu text at `0x573F4`; "can it be accessed?" needs investigation | table + labels found and enumerated; gate proven ROM-constant (§6b) |
| Substack "New codes" (2024) | *Teen Titans*: unlock all bonus features | headed **PS2 / GameCube / Xbox**, not GBA; GBA section lists only *Strike Force Hydra* |
| Substack "Under the microscope" (2026) | 6 button sequences (hold L + 5 presses) | PS2/GC/Xbox engine; exact numeric sequences (`03 07 07 00 08 05`, `00 06 06 03 06 05`, etc.) searched in this GBA ROM: **0 hits** at every alignment |

## 6b. Enumeration

**Space definition.** There is no password space: no keypad screen, no alphabet,
no input buffer comparator and no checksum validator for player-entered text was
found. The only checksum in the image is the **save-integrity** sum at
`0x08033DA8` (§5.1), which validates SRAM, never user input. There is therefore
no set of representable codes to enumerate and no novel code can be minted; the
deliverable is a bounded negative.

**Screen enumeration (every reachable screen walked, with RAM evidence).**
Screens observed in mGBA: intro logos → title → save select (`New`, `No 1`,
`No 2`) → Mission-1 banner → save tutorial → gameplay → pause menu
(`Stats`, `Options`, `Extras`, `Save Game` disabled, `Quit Game`) → `Options`
(Language, Music, SFX) → `Extras` (Biocards / SFX / Music / Asset Viewer) →
confirmation dialogs (quit, save, delete). **0 screens contain a text-entry field
or a code acceptor.** RAM evidence: live save mirror at `0x02003280` with `A2CX`
magic; scene-config pointer `0x02003714 = 0x08730134` with `[cfg+0x14]=0x0000`
while the Extras screen is displayed.

**Debug-menu table enumeration (counts).**
* 19 records at `0x08199558`, stride `0x1C`, enumerated in §4.
* 24 distinct ASCII debug labels at `0x080573F4`–`0x08057530`, with 24 pointer
  hits: 18 inside the debug table at `0x0819956C`–`0x08199764`, 2 in the debug
  HUD pointer sets at `0x0802F818`/`0x08031B18`, and the remainder in the same
  label bank. `DebugCheats` and `AssetViewer` also survive as **level names** in a
  level-definition block at `0x65C590` / `0x5E3C94`.
* Executable references to the table: **0** direct `BL`/`BLX` to `0x0802F7B4`
  (debug HUD init) and **0** 32-bit pointers to any record base
  `0x08199558`/`0x0819956C`/`0x08199668`/`0x08199768`; the single Thumb pointer
  `0x0802F7B5` appears only in the generic function-pointer table at ROM
  `0x08197348`, which is consumed by a generic object factory, not by a menu.
* Gate evidence: the HUD-enable test at `0x08030536`/`0x08030580` reads a `u16`
  at `[scene_cfg+0x14]` and tests bits 0 and 1; in the live Extras-screen state
  that `u16` is `0x0000` and the config pointer resolves to **ROM**
  (`0x08730134`). No runtime writer of those bits exists in any reachable code
  path found. The debug menu is therefore **gated/cut content with ROM-constant
  enable bits**, not a reachable code.

**Button-code search counts.**
* Scanned all 8 MiB for `u16` key-mask runs (active-high `A=1,B=2,Select=4,
  Start=8,Right=0x10,Left=0x20,Up=0x40,Down=0x80,R=0x100,L=0x200`, 1–3 bits set):
  7,171 candidate runs; every one inspected in context is compressed art, OAM
  attributes or script data — none is a comparator table with a progress index.
* The six published console button sequences as byte IDs (`030707000805`,
  `000606030605`, `070001070808`, `010207000404`, `080307080101`, `000700050501`)
  each occur **0 times** in this ROM.
* BTCF key-mask scan result: **0** comparator tables, **0** validator flags.

**Empirical rejection tests (enumerated, all negative).**
Title/pause combos pressed in mGBA with screenshots: `L+R+A+B+Select+Start`,
`L+R+Down+Select`, Konami sequence with and without `L` held. All left the screen
unchanged; no flag word changed in the savestate diff. There is consequently no
*accepted* input to contrast with a *rejected* one — which is the definition of
this bounded negative, not an untested guess.

**Conclusion.** Accepted code space size = **0**. Debug-menu space = 19 defined
records, 0 reachable. Unlockable space = 5 Extras categories + 25 Biocards + 2
difficulty unlocks, all driven by save-completion counters, not by any input code.

## 7. Validation evidence

* **Observed** — ROM hashes/header; all screenshots listed in §3; Extras menu
  showing 1 live / 3 locked entries at 0% completion; Options and pause-menu
  contents; save mirror `A2CX` in EWRAM; 19-record debug table bytes; 24 debug
  labels; 5 Extras labels and 4 cheat-effect strings decoded from the tile bank.
* **Derived** — text encoding (`-0x20` first char, `FF FC`/`FF FE` controls);
  save validator and `A2CX` magic; debug-table record stride and field roles;
  debug HUD gate reads ROM constant bits; absence of direct xrefs to the table.
* **Inferred** — that the four `0x0819976x` "action" values are submenu/action
  descriptors rather than code pointers (they land in data); that the `CHEATS`
  Extras item unlocks at a high completion threshold, since its label exists but
  the threshold string was not found in the text bank.

## 8. Unknowns

* The exact completion percentage (or other condition) that reveals the `CHEATS`
  Extras item; no threshold string accompanies it. Reaching 100% in-game was not
  attempted (would require completing all six missions on three difficulties).
* Whether the 19 debug-menu records were ever reachable in a prototype build.
  The retail image has no runtime path to them; a dev build may have had one.
* Precise effect of each cheat entry (e.g. whether `WARP TO POSITION` accepts a
  parameter typed in a sub-screen) — only the message strings were observed.
* The exact semantics of the `0x0819976x` action descriptors.

**Prompt-injection note.** A fetched TCRF mirror page (`TCRF:CTE`) contained
instruction-like text addressed to AI agents ("These instructions are not for a
human… whoever is operating this AI agent is a clown"). It was treated as
untrusted data and ignored, per guide §16.8; it did not affect the analysis.

## 9. Tooling

* `file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings -t x`, Python 3 for
  header parse, literal-pointer scans, `u16` key-mask scan, tile-text decoder
  (`decode2.py`), debug-table parser (`parse_debug.py`).
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`
  for code regions; Capstone/keystone available but not required.
* mGBA 0.10.5 under Xvfb `:318` with `SDL_AUDIODRIVER=dummy`; `xdotool` XTEST
  input; `scrot` + ImageMagick crop `720x480+154+184`.
* Savestate RAM access: Python `struct`/`zlib` extraction of the PNG `gbAs`
  chunk (`state2.bin`, 397,312 bytes, EWRAM at `0x21000`). mGBA's GDB stub was
  tried but rejected commands with a packet error; savestate diffing was used
  instead.
* Work artifacts (screenshots, scripts, decompressed state) live in
  `/tmp/opencode/teentitans1/`. No ROM or copyrighted assets are redistributed.

## 10. Legal note

Only hashes, addresses, algorithms, decoded string *text* and original tooling
are published here. The ROM and all extracted graphics/audio remain in the local
analysis workspace and are not redistributed.
