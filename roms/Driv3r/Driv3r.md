# Driv3r (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Driv3r/Driv3r.gba` |
| Size | 8,388,608 bytes (0x800000, 8 MiB) |
| Header title | `DRIVER3` |
| Game code | `B3RE` (USA, AGB-B3RE-USA) |
| Maker | `70` (Atari) |
| Version | 0x00 |
| `file` id | Game Boy Advance ROM image: "DRIVER3" (B3RE70, Rev.00) |
| MD5 | `3fbc7fda7d0bbaa03ec037e710cf1dd8` |
| SHA-1 | `df2238fc239bdd0226a1b39deef06fa521eae48e` |
| SHA-256 | `86dbaa89aaaad0aebf3c6d2a8d0f5f722905139ed43423d3bc5aa349fc9445e5` |
| CRC32 | `0x6C66CFBE` — exact match to GameHacking.org USA AGB-B3RE-USA (EU AGB-B3RP is `B617B354`) |

**Phase 0 / header scan.** One Nintendo-logo hit only (file `0x0`) → single GBA image, no appended
trainer, no multiboot stub, no 2-in-1 pack. Entry word `0xEA00002E` is the stock `b 0x080000C0`
crt0 branch — **not** a scene cracktro patch (guide §16.1). Header complement byte `0xBD = 0xDF`
does not reconcile with the summed bytes (`0x08 + 0xDF = 0xE7`); header checksum word is `0x0000`.
This is a common retail-header anomaly and, with a stock entry word and one logo, is not evidence
of a patch. No patch/trainer detected.

## 2. Executive summary

**Driv3r GBA (AGB-B3RE-USA) has no in-game cheat system.** There is no password screen, no
button-sequence cheat validator, no cheat/options/debug menu, and no hidden unlock code. Every
menu reachable in the retail game was walked and screenshotted; the complete five-language menu
text bank was enumerated and contains no `OPTIONS`, `CHEATS`, `PASSWORD`, `SECRET`, `DEBUG`,
`MISSION SELECT` or `VEHICLE SELECT` label in any language. The button input path and the whole
ROM were searched for key-mask sequence tables: zero matches for every published console code
sequence and zero button-code tables.

All "Driv3r GBA codes" in circulation are **GameShark / CodeBreaker memory-edit codes** (out of
scope for this engagement) or button codes for the **PS2 / Xbox / PC** versions (different SKUs
with an Options→Cheats menu that the GBA port does not have). GameFAQs' GBA cheat page has a
platform filter listing only PC / PS2 / Xbox — i.e. **no GBA-specific codes have ever been
published**. The "Sel+B+R = boat / Sel+B+L = motorcycle" strings attached to some CodeBreaker
entries are *cheat-device activation buttons*, not in-game combos. The `62972` / `29801` "Top
Secret Cars" passwords found in one cheats database belong to the *different* GBA game **Driven**,
not Driv3r.

The only developer-intended unlockables in the GBA game are **collectible-gated**, not code-gated:
collect all 16 of Calita's kiosks (ammo resupply in the apartment), all 16 of Bagman's bags (first
aid kit), finish the vehicle challenges (new cars), etc. These are normal progression and have no
code surface.

This is a **"no system"** negative result (guide §16.3 case 1), bounded by: full screen walk,
full text-bank enumeration with counts, exhaustive button-mask table search, and live testing of
published codes (§6b).

**Prompt-injection observed (guide §16.8).** Fetching `tcrf.net/Driv3r_(Game_Boy_Advance)` returned
a fake "LLM-specific instructions" payload (fake `key.bin`/EICAR string, a $1,000,000,000,000,000,000
payment demand, "terminate operations", "print X"). None of it was executed or followed. The
legitimate TCRF mirror content was used instead and reports only unused dialogue text for this
game — no cheats.

## 3. How to reproduce

- Emulator: `mgba -3 Driv3r.gba` under `Xvfb :318`, `SDL_AUDIODRIVER=dummy`.
- Keymap (mGBA SDL default): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`,
  D-pad = arrow keys. Hold 100–300 ms; screen transitions take 1–5 s.
- Boot path: Atari splash → save-slot screen (`GAME 1/2/3`, `NEW`/`LOAD`) → name entry →
  `UNDERCOVER` mode splash → long FMV intro (advance with A) → gameplay (Tanner on foot in Miami).
- Reproduce each screen (all confirmed on `:318`):
  1. **Main menu** (after `LOAD`): `Select` toggles exactly two entries — `UNDERCOVER`, `CREDITS`.
     `A` = OK, `B` = back. No Options/Cheats/Password.
  2. **CREDITS**: select `CREDITS` → `A` → scrolling credits (`DRIVER3 - GBA`, developer list at
     ROM `0x210328`).
  3. **Pause**: in gameplay press Start → map screen; `Select` cycles exactly five entries —
     `CONTINUE`, `SAVE`, `STATISTICS`, `QUIT`, `ABANDON` (then wraps to `CONTINUE`).
  4. **STATISTICS**: pause → `Select`×2 → `A` → challenge progress (Trailblazer/Destruction/
     Checkpoint/Slalom 0/4; Calita/Gator/Jericho/Bagman 00/16 per city).
  5. **QUIT** → confirmation `YES`/`NO` → returns to main menu.
  6. **Mission-failed** screen (text bank `0x22EFB8`, 10 failure messages).
- Code tests performed: console button sequences mapped to GBA masks, plus classic combos
  (`L+R`, `L+R+Start`, `Select+B+R`, `Select+B+L`, `L,L,A,B,B,R,R`), entered at the main menu and
  in gameplay with screenshots and savestate/RAM-diff verification. Every one either did nothing
  or performed ordinary menu navigation (A/Start = OK, Select = cycle) — no hidden screen, sound,
  flag, or state change.

## 4. Address map

| Item | Address | Note |
|---|---|---|
| GBA header | `0x08000000` | title `DRIVER3`, code `B3RE`, maker `70` |
| crt0 entry branch | `0x08000000` | `0xEA00002E` → `0x080000C0` (ARM) |
| Key-read routine | `0x08004D08`–`0x08004D3C` | ARM. `0x08004D0C` loads KEYINPUT ptr `0x08004D50 = 0x04000130`; `ldrh`, `mvn`, mask 10 bits; computes edge = `new ^ old & new`. |
| `pressed` global (u16, active-high) | `0x0203AB3C` | stored at `0x08004D34`; literal pools at `0x08004D54`, `0x08005B70`, … |
| `held` global (u16, active-high) | `0x0203AB3E` | stored at `0x08004D36`; literals `0x08004D58`, `0x08005AD8`, … |
| Save record in EWRAM | `0x0203CD88` | `driv` magic at `0x0203CD88`; player name `"saveA"` at `0x0203CE08`; mirrors 512-byte `.sav` (magic `vird` at file `0x4`) |
| Save file | `Driv3r.sav` | 512 bytes; EEPROM-style, magic `76 69 72 64 00 00 02 f0` |
| Input/UI handlers (ARM) | `0x08000720`, `0x08000DD4`–`0x08005700` | title/menu/game state machine; only `tst`/`cmp` against ordinary UI masks (`#9`=A\|Start, `#2`=B, `#0x14`/`#0x20`/`#0x34`=D-pad, `#0x100`=R) |
| Credits block | `0x08010328` file | `DRIVER3 - GBA`, developers |
| Menu text bank (5 languages) | `0x0822EE6B`–`0x0822FBB0` file | `NEW`, `GAME 1/2/3:`, `LOAD`, `CONTINUE`, `SAVE`, `STATISTICS`, `QUIT`, `YES NO`, `ABANDON`, `MISSION FAILED`, + French/German/Spanish/Italian equivalents; `0xFF` record delimiter |
| English collectible/unlock text | `0x08210D00`–`0x08210F52` file | kiosks, bags, unlock messages |
| Unused "killable Tommys" text | `0x08210FE7` file | matches TCRF unused-text note |

File offset ↔ ROM address: `0x08000000 + file_offset`. Savestate (`.ss1`) is a PNG with a
zlib `gbAs` chunk → 397,312-byte image; EWRAM at state `0x21000`, IWRAM at `0x19000`
(guide §16.13). RAM address ↔ state offset used here: `state = 0x21000 + (addr - 0x02000000)`.

## 5. Algorithm

No password validator, checksum, key table, or decoder exists in this SKU. The only algorithmic
surface relevant to "codes" is the button-input path:

```
; 0x08004D08  (ARM)  called each frame
held_raw = ldrh(0x04000130)          ; active-low
new      = (~held_raw) & 0x3FF       ; active-high 10-bit mask
pressed  = (new ^ old) & new         ; edge-triggered this frame
store pressed -> 0x0203AB3C
store new     -> 0x0203AB3E
```

Active-high mask bit assignment: `A=0x001, B=0x002, Select=0x004, Start=0x008, Right=0x010,
Left=0x020, Up=0x040, Down=0x080, R=0x100, L=0x200`; 10 buttons → 1,024 possible masks.
Every comparison in the ROM against these globals is a UI/menu/gameplay control (a single `tst`
or small D-pad group), not a multi-press sequence matcher — there is no history/shift register,
no expected-sequence table, and no accept/reject flag write.

## 6. Tables

- **Menu label set (all languages, exhaustive)** — English: `NEW`, `GAME 1/2/3:`, `LOAD`,
  `CONTINUE`, `SAVE`, `STATISTICS`, `QUIT`, `YES NO`, `ABANDON`, `MISSION FAILED` + 10 `FAILURE - …`
  strings; French `CREER/CHARGER/CONTINUER/SAUVEGARDER/STATISTIQUES/QUITTER/OUI NON/ABANDONNER`;
  German `ERSTELLEN/LADEN/WEITER/SPEICHERN/STATISTIK/BEENDEN/JA NEIN/AUFGEBEN`; Spanish
  `CREAR/CARGAR/CONTINUAR/GUARDAR/ESTADISTICAS/SALIR/SI NO/ABANDONAR`; Italian
  `CREA/CARICA/CONTINUA/SALVARE/STATISTICHE/ESCI/SI NO/ABBANDONA`. **No** cheat/password/options
  label exists in any language.
- **Screen count:** 12 distinct screens enumerated (splash, save-slot, overwrite confirm, saving,
  mode splash, FMV, gameplay, pause[5], quit-confirm, statistics, mission-failed, credits).
- **Button mask table:** none. Scanned all `~4.19 M` even file offsets for u16/u32 sequences
  matching published codes (active-high *and* active-low) → **0 hits**; scanned for runs of ≥6
  consecutive single-key masks → **0 in code regions** (the few runs found are in compressed
  graphics at `0x17xxxx`/`0x7bxxxx` and are noise).
- **Published GBA "codes" (all out of scope, verified as external):** GameShark/CodeBreaker master
  `948821227AE4 …` plus ~25 entries (Access all Maps, Turbo, Infinite Health, Have all Weapons,
  Have Boat `[Sel+B+R]`, Have Motorcycle `[Sel+B+L]`, Statistics Complete …, Dream Bike, Dream Car,
  Miami car-lot cars). These are cheat-device RAM patches, not in-game inputs; their literals do
  not appear in the ROM (nor should they).
- **Console button codes (verified as other SKUs):** Xbox `L,L,X,Y,Y,R,R` (all weapons) etc.;
  PS2 `R1,L2,Square,Circle,R1,R2,L2` etc.; PC keyboard `B F F5 K 5 7 O` etc. Mapped to GBA masks
  and tested — no effect / just menu navigation.

## 6b. Enumeration

**Space definition.** There is no code space to enumerate: no alphabet, no fixed-length input
field, no checksum, no lookup table, no accept/reject validator (§0.2 items 1–4 are vacuous for
this SKU). The only bounded space searched was the button-input space and the text/menus:

| Space searched | Size | Result |
|---|---|---|
| Distinct in-game screens | 12 (walked live) | no hidden/debug screen reached |
| Main-menu entries | 2 (`UNDERCOVER`, `CREDITS`) | no Cheat/Options/Password |
| Pause-menu entries | 5 (`CONTINUE/SAVE/STATISTICS/QUIT/ABANDON`) | no Cheat/Options |
| Menu text records, 5 languages | 100 % of bank `0x22EE6B`–`0x22FBB0` | 0 cheat/password/debug/secret labels |
| `strings -t x -n 4` whole ROM | 58,648 strings | 46 keyword hits, all dialogue/credits (0 code strings) |
| Button-mask sequence tables | all 4,194,304 u16 offsets | 0 published-code matches; 0 validator tables |
| Button combos tested live | L+R, L+R+Start, Sel+B+R, Sel+B+L, L,L,A,B,B,R,R + console mappings | 0 hidden effects; all plain navigation |

**Novel code / in-game proof.** Not applicable — no code system exists to mint from, so §0.2's
"generate an unpublished code and enter it" requirement is satisfied by its negative-result
branch: the search spaces above are bounded and the absence statement is made about those exact
spaces. **Bounds proven by rejection:** published console sequences and classic combos entered on
the GBA main menu and in gameplay produced no sound, flag, screen, or RAM-state change (only
ordinary A/Select menu navigation), which is the in-game rejection of every candidate "code".

**Unlockables (progression, not codes).** Confirmed in text bank and GameShark descriptions:
16 kiosks → ammo resupply, 16 bags → first-aid kit, vehicle challenges → new cars, mission
rewards → `new wheels`/car-lot delivery (`0x210D00`–`0x210D90`). These require gameplay collection;
no code, password, or button sequence triggers them. The unused "4 remaining Tommys → immunity"
text at `0x210FE7` is dead/unused (TCRF notes it) and has no reachable trigger in the retail game.

## 7. Validation evidence

- **Observed (emulator, `:318`):** all 12 screens and their exact entry sets; Select/A/B navigation;
  no reaction to any tested code sequence; credits roll; statistics values; save-slot behavior.
  Screenshots saved under `/tmp/driv3r/` (not attached).
- **Observed (RAM):** input globals at `0x0203AB3C/3E`; 512-byte `.sav` with `driv`/`saveA`
  record mirrored at EWRAM `0x0203CD88`; savestate diffs after code attempts showed only animation/
  timer noise, no persistent cheat flag.
- **Derived (disassembly):** key-read routine `0x08004D08`; only ordinary UI mask comparisons in
  `0x08000720`–`0x08005700`; no sequence-table xrefs.
- **Derived (static scan):** exhaustive string/button-table searches with the counts in §6b.
- **Inferred:** the console-exclusive cheat menu was removed for the GBA port (consistent with
  the missing Options menu text in all five languages and with GameFAQs' platform filter).
- **External evidence:** GameFAQs / GameHacking.org / TCRF mirror / Almar's Guides / fandom wiki;
  ROM CRC32 matches the USA SKU exactly.

## 8. Unknowns

- No in-game code surface was found. The only not-fully-dynamic item is the claim that *no* button
  combination anywhere triggers a debug screen; the 12 reachable screens and the complete text
  bank were enumerated and the input code searched, but there is no exhaustive proof over all
  2^10 button masks × all game states. Given zero matching tables and no menu text, this residual
  is small and is stated as an inference, not an observation.
- The unused "killable Tommys" text (`0x210FE7`) has no known trigger; reported as dead text per
  TCRF, not exercised.
- Header complement/checksum anomaly noted in §1; cause not investigated (no behavioral impact).

## 9. Tooling

- mGBA (`mgba -3`, and `mgba -3 -g` attempted — GDB stub port 2345 was unavailable/blocked in the
  shared environment), Xvfb `:318`, openbox, xdotool, `import`/scrot.
- `strings -t x`, `xxd`, `grep`, Python 3 + `capstone` 5.0.7 for literal/xref and button-sequence
  scans; `arm-none-eabi-objdump -M force-arm/force-thumb` for disassembly.
- `/tmp/driv3r/ssdiff.py` — mGBA `.ss1` PNG `gbAs` zlib decompress + RAM diff.
- No ROM or copyrighted assets are redistributed in this report.

## 10. Legal note

Only addresses, hashes, algorithms and original analysis are published; no ROM image, graphics,
audio or game text is reproduced beyond short identifiers needed to identify menu entries.
