# The Powerpuff Girls: Him and Seek (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `The Powerpuff Girls: Him and Seek.gba` |
| Size | 8,388,608 bytes (0x800000, 8 MiB) |
| Header title | `PPG HIM N SE` |
| Game code / maker | `AP5E` / `6L` (i.e. `AP5E6L`), `file(1)` reports `AP5E6L, Rev.00` |
| Fixed byte / unit / device | `0x96` / `0x00` / `0x00` |
| Version / complement / header checksum | `0x00` / `0xB9` / `0x0000` |
| Entry word | `0xEA00002E` — the stock GBA branch (no cracktro/trainer patch; §16.1) |
| MD5 | `e5911e8365d3fe871c7d58560a302938` |
| SHA-1 | `bcf894b5819169640329c93178f5c8727d3d812e` |
| SHA-256 | `56178d2c872f99049ff4edbbff39e57b64c13a9f82e1fd51568d00233869f0e4` |

Save hardware: 512-byte EEPROM. Magic `C0 DE 60 0D` little-endian (`0xC0DE600D`) at
EEPROM `0x04` and `0x1C`; three 0x18-byte slot records, flag byte at slot+4
(EEPROM `0x08`, `0x20`, `0x38`).

Web recon (GameFAQs 403, Google/DuckDuckGo blocked/empty) produced **no published
code list** for this SKU. Nothing in the ROM matches the console/PC Powerpuff
Titles' code lore; per §16.11 no title+platform assumption was made.

## 2. Executive summary

**There is no in-game code system in this build.** No password-entry screen, no
on-screen alphabet/keyboard widget, no button-code table, and no developer
shortcut code exist. The word "password" in the game is an **inventory item**
(text index 62) that opens the Boogie Man's door — a normal quest object, not a
typed code. The one debug-looking string, *"did you know there is a cheat mode
in the game?"*, is a hint-NPC line in the script bank and has no associated
input handler.

What the ROM **does** contain is a complete **unused debug-menu string set**
(13 labels: `sound test`, `music test`, `sfx test`, `next section`, `next level`,
`level id`, `section id`, `spawn id`, `go to`, `slow-mo`, …) in the ordinary text
table, plus a **four-bit unlock flag system in the save record**. The flags are
written only by the game's ending sequence and by item-collection checks, never
by a controller matcher. They unlock arcade games/title options, not a cheat
menu. Reaching the debug strings is therefore a **bounded negative** (§0.2,
§16.3, §16.21), documented with counts in §6b.

A save-bit mint (`0x08`/`0x0F` in EEPROM slot+4) was entered into the emulator;
it changes save state but **does not** add the debug entries. A careful A/B test
also showed that the `ARCADE` title entry is *not* gated by bit 3 — it appears
with any completed save — so that observation is reported as save-state gating,
not as a cheat code (§16.18).

## 3. How to reproduce

* Emulator: mGBA 0.10.5 SDL, `SDL_AUDIODRIVER=dummy`, Xvfb `:315`, openbox, `-3`.
  Keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, arrows.
* Boot → BAM! splash → title. On a blank save the title ring is
  `OPTIONS / NEW GAME / CONTINUE(dim)`. With any completed save it becomes
  `OPTIONS / NEW GAME / CONTINUE / ARCADE`.
* Key path walked: `OPTIONS` (MUSIC/SFX/BACK); `NEW GAME` → slot → intro cutscenes
  (hold A) → Pokey Oaks classroom; `Select` opens Scavenger Hunt List with three
  tabs (`INVENTORY`, `CHECKLIST`, `MAP`); `Start` opens pause menu
  (`CONTINUE / SAVE GAME / SOUND / SLEEP MODE / QUIT GAME`); `ARCADE` shows
  `BOOGIE FRIGHTS FEVER` and a second cabinet, both **"OUT OF ORDER"**.
* Code-entry attempts: 17 button combinations on the title/pause/in-game screens
  (`L+R`, `L+R+A/B/Start/Select`, `L+R+A+B`, `Start+Select`, `A+B`, `Up+Down`,
  `Left+Right`, `L+A`, `R+B`, `L/R+Start/Select`, Konami sequence). All rejected /
  no new screen or flag.
* Save-bit mint: patch EEPROM `0x08` and `0x20` from `0x00` to `0x08`, then `0x0F`;
  reboot. Screenshots `flag_menu.png`, `arc_all.png`, `arc_browse2.png`,
  `g5_sound.png`, `ab_menu1.png` in the work dir `/tmp/opencode/powerpuffseek/`.
* Analysis was performed on a copy in the work dir, so **no emulator artifacts
  were written into the ROM folder** (verified).

## 4. Address map

All addresses are ROM addresses (`file offset + 0x08000000`) unless noted.

| Address | Meaning |
|---|---|
| `0x08000000` | Entry `0xEA00002E` (stock, Thumb main via crt0 literal) |
| `0x08000CA4` | `getText(index)` — `r0 = *(0x0803865C + 4*index)`; literal at `0x08000CB0` |
| `0x0803865C` | Text pointer table, **216 entries** (0..215); slots `0x0803865C+4*i` |
| `0x08037AA8`–`0x08038640` | NUL-terminated lowercase text bank (item names, areas, UI) |
| `0x080383D0` | index 167 `slow-mo` |
| `0x080383D8` | index 168 `sound test` |
| `0x080383E4` / `0x080383EC` | 169 `music ` / 170 `sfx ` (used by SOUND/OPTIONS) |
| `0x080383F4` / `0x08038400` | 171 `music test ` / 172 `sfx test ` |
| `0x0803840C` / `0x0803841C` | 173 `next section` / 174 `next level` |
| `0x08038428` / `0x08038434` / `0x08038440` | 175 `level id ` / 176 `section id ` / 177 `spawn id ` |
| `0x0803844C` / `0x08038454` | 178 `go to` / 179 `cancel` |
| `0x08037D3C` | index 62 `password` — an inventory item name, not a code |
| `0x08041B30`, `0x08041B84` | Boogie Man door dialogue about the password item |
| `0x0803F230` | `did you know there is a cheat mode in the game?` (script string) |
| `0x08079EB68` | Dialogue record: pointers to `0x0803F230`, `0x0803F260`, `0x0803F278` |
| `0x0803865C` + 4·167…179 | Debug-label pointer slots; **zero** code xrefs outside the table |
| `0x08787878` | u16 sequential ID list `0x00A8,0x00A9,…0x00D7` (168..215); no 32-bit xref found |
| `0x08005D50` / `0x08005D58` | Getter / setter for global flag `G+0x89` ("cheat mode") |
| `0x08005D60` / `0x08005D68` | Getter / setter for `G+0x88` |
| `0x08005D70` / `0x08005D78` | Getter / setter for `G+0x87` |
| `0x08005D80` / `0x08005D88` | Getter / setter for `G+0x86` |
| `0x02000054` | Pointer to global struct `G` (observed `G = 0x02006CC8` at title) |
| `0x02006D4E`–`0x02006D51` | The four flag bytes (`G+0x86..0x89`) |
| `0x02002FF8` | Save-record buffer pointer used by pack/unpack (`+4` = flag byte) |
| `0x0801AB88` | Pack four flags → save byte bits 0..3 |
| `0x0801AC2C` | Unpack save byte bits 0..3 → four flags |
| `0x0803FBE` | Ending path: `setter(G+0x89, 1)` (the only gameplay writer of bit 3) |
| `0x0803FAC` | Gate: scene state ∈ {6,7} **and** `[state+0x230] == 7` |
| `0x0801D91C` | Sound/Options menu constructor; item count 3 or 5 by `[obj+0x28]` |
| `0x0801DAC2` | `ldrb [obj+0x28]; cmp #0; bne` → draw `music test` when flag set |

RAM evidence: mGBA `.ss1` savestates are PNGs with a zlib `gbAs` chunk
(397,312 bytes for this ROM); EWRAM begins at raw `0x21000`, so G and the four
flags were read directly at raw `0x27CC8`/`0x27D4E..0x27D51` (all `0x00` in a
fresh save). Writing the flag bytes into a savestate is **immediately reverted**
by the game's save→flag refresh, which is consistent with there being no
controller-side writer.

## 5. Algorithm / pseudocode

```
getText(i):  return *(u32*)(0x0803865C + 4*i)      # NUL-terminated lowercase ASCII

# four persistent unlock flags, packed/unpacked in the EEPROM slot flag byte:
save_byte.bit0 = getter(G+0x86)   # set when collectible item 49 obtained (0x8013F56)
save_byte.bit1 = getter(G+0x87)   # set by 0x801E862 (other collectible condition)
save_byte.bit2 = getter(G+0x88)   # set by 0x8013EDA (item/area condition)
save_byte.bit3 = getter(G+0x89)   # set at ending 0x0803FBE ("cheat mode")

ending_gate():
    if scene_state not in {6, 7}: return
    if [game_state + 0x230] != 7: return
    setter(G+0x89, 1)
    unlock_arcade_flags()          # 0x801AA64 -> 0x801AB88
    show_ending_rank(collected_count)  # indices 12/13/14 over 24 items

options_menu_render():
    n = getter(G+0x89) ? 5 : 3
    draw("music ", "sfx ")
    if getter(G+0x89): draw("music test ", "sfx test ")
    draw("back")
```

No checksum, substitution alphabet, key table, PRNG, or input matcher exists in
this ROM: the flag values are plain booleans copied verbatim between EWRAM and
EEPROM.

## 6. Tables

**Text table (216 entries, `0x0803865C`)** — full index list was dumped and
decoded. Relevant subset:

| idx | string | ROM addr | used by code? |
|---:|---|---|---|
| 62 | `password` (item) | `0x08037D3C` | yes — inventory item |
| 167 | `slow-mo` | `0x080383D0` | **no caller** |
| 168 | `sound test` | `0x080383D8` | **no caller** |
| 169 | `music ` | `0x080383E4` | 1 caller (`0x801D9A4`) |
| 170 | `sfx ` | `0x080383EC` | 1 caller (`0x801DA32`) |
| 171 | `music test ` | `0x080383F4` | 1 caller (`0x801DACA`, flag-gated) |
| 172 | `sfx test ` | `0x08038400` | 1 caller (`0x801DB4A`, flag-gated) |
| 173 | `next section` | `0x0803840C` | **no caller** |
| 174 | `next level` | `0x0803841C` | **no caller** |
| 175 | `level id ` | `0x08038428` | **no caller** |
| 176 | `section id ` | `0x08038434` | **no caller** |
| 177 | `spawn id ` | `0x08038440` | **no caller** |
| 178 | `go to` | `0x0803844C` | **no caller** |
| 179 | `cancel` | `0x08038454` | **no caller** |

**Save flag byte** (EEPROM slot+4; three slots at `0x04`, `0x1C`, `0x34`, stride
`0x18`): bit0/bit1/bit2 = three collectible-driven arcade unlocks, bit3 =
"cheat mode". Each is a plain boolean; no checksum on the byte.

**Button masks** (standard GBA, active-high `A=1,B=2,Select=4,Start=8,
Right=0x10,Left=0x20,Up=0x40,Down=0x80,R=0x100,L=0x200`): searched as u16 and
u8 sequences for Konami and for runs of ≥6 single-button presses — zero hits.

## 6b. Enumeration

**Space definition.** There is no code space to enumerate: the only
player-influenced "cheat-like" state is a 4-bit save flag field
(`2^4 = 16` possible states), with the meanings above. The game's *entire* text
space is 216 indices; the developer-debug subset is 13 strings (167–179). No
alphabet, checksum width, password length, or input buffer exists.

**Validator model.** None. No routine reads a player-entered buffer and compares
it to a constant/table. `getText()` is the only string accessor and all 88 of
its call sites were enumerated (see counts below); none passes a player string.

**Novel code.** Not applicable — there is no code format to mint. The closest
experiment was minting the previously-unset save-bit combination `0x08` and
`0x0F`, entering it into the emulator, and re-booting:
* ROM/eeprom accepted the bits (file content verified after reboot),
* the `ARCADE` title entry was present — but an **A/B control** with the bits
  reset to `0x00` while keeping the same completed save showed `ARCADE` still
  present. Therefore `ARCADE` is gated by *having a completed save*, not by
  bit 3 (§16.18: a save-bit unlock is not a code).
* the debug strings did **not** appear anywhere; the game actively rewrites the
  four RAM flags from the save byte, so a savestate RAM patch is reverted.
* both arcade cabinets still display `OUT OF ORDER` with the bits set — the
  individual cabinet unlocks use different collectible conditions
  (`0x8013F56`, `0x8013EDA`, `0x801E862`).

**Bounds proven by rejection / negative searches (all counts are from this ROM):**

| Search | Space checked | Result |
|---|---|---|
| Reachable screens walked | splash, intro, title, options, new-game slots, continue slots, classroom, dialogue, inventory (3 tabs), pause (5 items), sound submenu, arcade | 12 screen classes; **no code-entry widget** |
| `getText` call sites | all **88** BL sites | immediate indices used: {5,6,7,14–21,73,89–92,94–108,112–114,120,169,170,171,172,188–206,208–211,213–215}; **0** calls with 167, 168, 173–179 |
| 32-bit pointers to debug string slots `0x0803865C+4·167…179` | 13 slots | **0** code xrefs (only the table itself holds the string pointers) |
| Pointer to ID list `0x08787878` | whole 8 MiB, exact 32-bit | **0** hits |
| Alphabet / code literals | 12 patterns (`ABCDEFGHIJKLMNOPQRSTUVWXYZ`, `0123456789`, `ENTER CODE`, `ENTER PASSWORD`, `DEBUG`, `SECRET`, `GOD`, `INVINCIBLE`, …) | **0** hits |
| Button-code tables | Konami sequence in 4 encodings; u16 runs of ≥6 single-button masks in first 0x40000 | **0** hits |
| Button combos pressed in emulator | 17 combinations (see §3) | **0** new screens/flags |
| Flag setter call sites | 8 total (2 per flag) | 4 in save pack/unpack, 4 in ending/collectible logic; **0** in any input handler |
| `did you know … cheat mode` dialogue | 1 record | hint text only; no handler |

**Conclusion (bounded negative).** With every reachable screen walked, all 216
text indices decoded, all 88 text callers counted, all four flag writers counted,
and all alphabet/button-mask searches returning zero, the debug labels at
indices 167–179 are **unused developer leftovers** in this retail image (dead
code, §16.3 case 2). The only development-intended unlocks are save-bit progress
rewards. No password, button code, or hidden menu can be entered by a player.

## 7. Validation evidence

* **Observed** (emulator/screenshots): title with and without a save; OPTIONS
  3-item menu; pause 5-item menu; inventory's three tabs; ARCADE screen with both
  cabinets `OUT OF ORDER`; 17 button combos with no effect; EEPROM byte patches
  `0x00 → 0x08 → 0x0F → 0x00` and the resulting boots; RAM flag bytes `0x00` in
  a title savestate and their reversion after a savestate patch.
* **Derived** (disassembly): `getText` at `0x08000CA4`; the 216-entry table;
  setter/getter pairs and their exact call-site counts; the ending gate at
  `0x0803FAC`/`0x0803FBE`; save bit packing at `0x0801AB88`/`0x0801AC2C`.
* **Inferred** (not fully exercised): the exact in-game actions that set bits
  0–2 (item IDs 49/18 and an area/flag condition) were read from code but not
  played to completion; the natural trigger for `[state+0x230] == 7` is the
  scavenger-hunt ending, but a full winning playthrough was not performed. The
  debug menu's *intended* actions (`next level`, `go to`, …) are inferred from
  their labels only and were never reached.

## 8. Unknowns

* Whether an earlier/prototype build of this game shipped with the debug menu
  enabled — this 8 MiB retail image (`AP5E6L`, rev 00) does not.
* Which exact collectible/ending combination sets `[state+0x230] = 7`; the gate
  was reverse-engineered but not driven by gameplay.
* Why the game rewrites `G+0x86..0x89` from the save byte every frame (likely a
  per-frame save sync), which prevented holding a debugger/savestate patch.
* No published code list could be fetched (403/captcha), so "not in any
  published list" could not be compared against a list; the negative rests on
  ROM-wide searches instead.

## 9. Tooling

* `file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings -t x`, Python 3
  (struct/re/capstone/Pillow) for pointer, literal, BL and mask scans.
* `arm-none-eabi-objdump -M force-thumb` for targeted disassembly;
  `thumb_dis.txt` (full 0x08000000–0x08037000 Thumb dump) in the work dir.
* mGBA 0.10.5 SDL under Xvfb `:315` + openbox; `xdotool` XTEST input, `scrot`
  screenshots; `.ss1` PNG savestates decompressed with Python `zlib` for RAM
  evidence (guide §16.13). mGBA `-d` CLI debugger was also exercised.
* Working scripts: `scan_ptrs.py`, `blscan.py`, `dump_ptrtab.py`, `findidx.py`,
  `combos.py`, `ui.py` in `/tmp/opencode/powerpuffseek/`.
* No ROM or copyrighted assets are redistributed by this report.

## 10. Cleanup

All processes launched for this engagement were terminated by PID number only
(no `pkill`/`pkill -f`). The ROM folder contains only the `.gba` — no `.sav` or
`.ss*` artifacts were created there (all emulator files stayed in the work dir).
