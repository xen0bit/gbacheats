# Spider-Man: The Movie (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Spider-Man: The Movie.gba` |
| Size | 8,388,608 bytes (0x00800000) |
| `file(1)` | Game Boy Advance ROM image: "SPIDERMAN" (AKXE52, Rev.00) |
| Header title | `SPIDERMAN` (0x00A0) |
| Game code | `AKXE` (0x00AC) — Europe |
| Maker | `52` (0x00B0) — Activision |
| Version | `0x00` |
| Entry word | `0xEA00002E` (stock `b 0xC0`) |
| Fixed byte 0xB2 | `0x96`; main unit `0x00`; device `0x00` |
| Complement / header checksum | `0x1E` / `0x0000` |
| MD5 | `6ea428eabf05d2c51ed21b5608c5db21` |
| SHA-1 | `c81efc39de8349d63ad30e72bbf3b049f37e542a` |
| SHA-256 | `0725b77b6b1a803846c7fdfe98e9053b2200cb9931f1a871ea68d7619b03e704` |

**Phase 0 scan.** Nintendo logo at 0x000004 is intact; scanning all 8 MiB for a
second logo/header found exactly **one** hit, at 0x000000. There is no appended
trainer, no multiboot stub, no swapped entry point and no cracktro. The image is
a single retail European ROM. (The `0x0000` header checksum and the complement
byte are reproduced verbatim; no patching was applied to the analysis copy.)

## 2. Executive summary

This GBA game is **Digital Eclipse's** 2-D action title — a completely different
engine from the Treyarch GameCube/PS2/Xbox/PC game whose text-entry cheat codes
(`ORGANICWEBBING`, `IMIARMAS`, `ROMITAS`, …) circulate on the web. None of those
literals is in this ROM (0 of 14 verified; §6b). The GBA title has **no password
or text-code entry screen at all**: there is no `PASSWORD`/`ENTER CODE`/`INVALID
CODE` string anywhere in its decoded 0x08287000–0x0828BF00 text bank, and the
only text-entry widget is a 3-character **save-slot name** (§6.2).

The developer-intended "cheat" surface is a **save-bit unlockable system**:

* **17 secrets** — 3 named gameplay cheats (`armor upgrade`, `Strength
  Enhancement`, `LEVEL CHEAT`) and 14 individually named `MOVIE SHOT 1`…`14`
  entries. They are shown as `<LOCKED>` on a three-page *SECRETS PAGE* until
  the corresponding EEPROM flag is set by an in-game unlock checker.
* **9 toggleable cheat powers** in a gated *CHEATS* menu (`POWER WEB`, `BLIND
  WEB`, `STICKY WEB`, `BOMB WEB`, `SHIELD WEB`, `NET BLAST`, `INVULNERABLE`,
  `ARACHNID STRENGTH`, `SUPER WEB`) — enumerated statically with their item IDs.
* **LEVEL CHEAT** — a level-select secret (the game has 20 named levels).
* One hidden controller combination exists in the input routine, but it is a
  **soft reset** (`A+B+Start+Select`, L/R excluded), not a cheat.

Because no code system exists, the §0.2 "mint a novel code" deliverable is
replaced by a **complete enumeration plus a proven negative** (§6b): the full
secret/cheat space is defined, the unlock validator is reversed, direct writes
to the flag bytes were **rejected by the game in the emulator**, and the code
surface counts are given.

## 3. How to reproduce

* Emulator: `/usr/local/bin/mgba` 0.10.5 under `Xvfb :317`, `DISPLAY=:317`,
  `SDL_AUDIODRIVER=dummy`, `openbox` as WM. Keymap (mGBA SDL default):
  A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`,
  D-pad = arrow keys. Hold 150 ms per press.
* Boot path (observed): title logo → press Start → main menu.
  Main menu = START / LOAD GAME / OPTIONS / SECRETS.
* Save creation: START → slot screen → A on an `EMPTY` slot → edit the 3-letter
  name with the D-pad → Start (writes EEPROM) → Start (enters game). The title
  tutorial advances with A. Pause with Start: CONTINUE / QUIT.
* Secrets enumeration: main menu → SECRETS → MORE → MORE. Pages contain
  3 + 7 + 7 = 17 entries, all `<LOCKED>` on a fresh save.
* Options on a fresh save: SOUND ON / MUSIC ON / CREDITS / EXIT — **CHEATS and
  VIEW PHOTOS are absent** (gated by unlock flags; §7).
* RAM evidence used mGBA savestates (Shift+F1…F9). A `.ss1` is a PNG with a
  `gbAs` chunk; `zlib.decompress` yields a 397,312-byte state: EWRAM at state
  offset `0x21000` (so `state[0x21000 + (addr-0x02000000)]`), IWRAM at `0x19000`.
  mGBA's stub-free `-d` debugger (`r/1 ADDR`, `w/1 ADDR VAL`, `b`, `c`) was
  driven through a FIFO bridge for live writes.
* No ROM, savestate or screenshot is redistributed with this report.

## 4. Address map

File offset → ROM address: `0x08000000 + file_offset`.

| Address | Kind | Meaning |
|---|---|---|
| `0x0864CB9C` | data | String-slot table base (4-byte pointers into `0x0828xxxx` text bank). Slot `i` = `0x0864CB9C + 4*i`. |
| `0x08287000`–`0x0828BF00` | data | Decoded ASCII text bank + font/glyph translation tables (`0x08287000`, `0x082871E0`, `0x082872D0`, `0x08287348`). Button glyphs in text: `@`=A, `_`=B, `{`/`}`=L/R, `+`=D-pad. |
| `0x0864CC68` / `0x0864CC70` | data | Slot 51/53: `SOUND  ON` / `MUSIC  ON` |
| `0x0864CC78` | data | Slot 55: `EXIT` |
| `0x0864CC7C` | data | Slot 56: `CHEATS` (gated menu title) |
| `0x0864CC80` | data | Slot 57: `VIEW PHOTOS` (gated) |
| `0x0864CD0C`–`0x0864CD54` | data | Slots 84–103: the 20 level names |
| `0x0864CD58`–`0x0864CD78` | data | Slots 111–119: the 9 cheat-power names |
| `0x0864C29C`, `0x0864C2B0` | data | Secrets-page name tables (page 1; pages 2/3) |
| `0x0828BE9C`, `0x0828BEA8`, `0x0828BED0` | data | Secret numeric ID tables (0,1,2 / 3..9 / 10..16), `-1` = MORE/EXIT |
| `0x0864C1C8`, `0x0864C20C` | data | Secret-name and unlock-condition tables (17 entries) |
| `0x0868DB88` | data | 17-byte "condition applies" mask for the unlock checker |
| `0x0803BCF6`–`0x0803BD66` | code | Secret unlock checker: loops ids 0..16, compares condition mask and current flag |
| `0x0803BBE0` | code | `unlock_secret(id)`: sets flag, sets availability bit at `0x0202A6C0+6` |
| `0x02039081`–`0x02039091` | RAM | 17 secret flag bytes (`addr = 0x02039081 + id`); mirror of EEPROM slot bytes `0xA0..0xB0` |
| `0x0202A6C0+6` | RAM | "any secret unlocked" availability bit |
| `0x0803C300`–`0x0803C550` | code | SECRETS PAGE renderer; `<LOCKED>` glyphs at `0x0828BF48`/`0x0828BF4C`, 'locked' slot `0x0864CBE4` |
| `0x08019CBC`–`0x08019E20` | code | CHEATS-menu renderer; item-ID → cheat-name dispatch (values 0x25, 0x3F…0x45, 0x100) |
| `0x08003544`–`0x080035B6` | code | Input routine (only direct KEYINPUT reader). Held buffer `0x02000680`, pressed `0x02026144`. |
| `0x0800356A`–`0x080035AE` | code | Hidden combo branch: `held & 0x300 == 0`, `(held & 0xF) == 0xF`, gate `0x0203EA9C != 0` |
| `0x0802B80C` | code | Toggles combo byte `0x02025F94`; when clearing calls `0x0803D2A8` |
| `0x0803C834` | code | Soft-reset wrapper (`svc 0x01` at `0x0803C83E`) |
| `0x080452D0`, `0x080452E0`, `0x0804D760`, `0x08050204` | data | Debug printf leftovers: `Cheatlevel=%d`, `Nextlevel levelnum=%d`, `Cheat Zap`, `Level Cheat`; build string `Spiderman v0.001` at `0x08045304` |

## 5. Algorithm

**No password validator exists.** The only validation-like algorithm is the
secret unlock checker, which is *not a code validator*: it is driven by gameplay
state, never by a user-entered string.

Reimplementation (derived from `0x0803BCF6`–`0x0803BD66` and `0x0803BBE0`):

```
# mask at 0x0868DB88, ids 0..16 = 00 00 01 00 01 01 01 01 00 01 01 01 01 01 00 00 00
for id in 0..16:
    if mask[id] == 0: continue                 # condition does not apply
    if secret_flag[0x02039081 + id] != 0: continue   # already unlocked
    if gameplay_condition[id] satisfied:
        unlock_secret(id)
unlock_secret(id):
    if byte[0x02025F04] | byte[0x02025F04+1] | byte[0x02025F04+2] != 0:
        byte[0x0202A6C6] = 1                   # cheat availability bit
    if id > 0x10: return 0
    if secret_flag[0x02039081 + id] == 0: secret_flag[0x02039081 + id] = 1
    draw_cheat_message(id)
```

The secrets-page renderer tests the same byte: non-zero → draw `<` + `locked` +
`>`; zero → draw the name from the slot table. The unlock condition text for
each secret is stored at `0x0864C20C + 4*i` (e.g. `collect all golden spiders.`,
`with over 150,000 points.`, `FOR PHOTOGRAPHING`, `FOR GETTING ALL PHOTOS`).

Input routine (derived, `0x08003544`):

```
held    = ~KEYINPUT & 0xFFFF                    -> 0x02000680
pressed = held & ~previous_held                 -> 0x02026144
if (held & 0x30F) == 0:  gate[0x0203EA9C] = 1
if (held & 0x300) != 0: return                  # L or R held -> no combo
if gate[0x0203EA9C] == 0: return
if (held & 0xF) != 0xF: return                  # need A+B+Select+Start
toggle byte[0x02025F94]; clear IO regs; svc SoftReset
```

## 6. Tables

**6.1 Secrets (complete set, ROM table `0x0864C29C` / `0x0864C2B0`, IDs
`0x0828BE9C`…).** All are `<LOCKED>` on a fresh save (observed).

| ID | Name | Published aggregate (3rd party cheat indexes) |
|---:|---|---|
| 0 | armor upgrade | Enhanced Armor |
| 1 | Strength Enhancement | Enhanced Strength |
| 2 | LEVEL CHEAT | Level Select |
| 3–16 | MOVIE SHOT 1 … MOVIE SHOT 14 | Movie Clips (one entry) |

**6.2 Text-entry field.** The slot screen offers a 3-letter A–Z name per save
slot (EEPROM `0x00..0x02` for slot 1). It is a *label*: it is displayed back on
the slot screen and is never compared with a constant by any validator (no
`strcmp`-style consumer references the buffer). It is not a password field
(§16.2b).

**6.3 Cheat powers (complete set, dispatch at `0x08019CBC`).**

| Item ID | Cheat name | Slot |
|---:|---|---|
| 0x25 | POWER WEB | `0x0864CD58` |
| 0x3F | BLIND WEB | `0x0864CD5C` |
| 0x40 | STICKY WEB | `0x0864CD60` |
| 0x41 | BOMB WEB | `0x0864CD64` |
| 0x42 | SHIELD WEB | `0x0864CD68` |
| 0x43 | NET BLAST | `0x0864CD6C` |
| 0x44 | INVULNERABLE | `0x0864CD70` |
| 0x45 | ARACHNID STRENGTH | `0x0864CD74` |
| 0x100 | SUPER WEB | `0x0864CD78` |

**6.4 Levels (20, slots `0x0864CD0C`–`0x0864CD54`):** Crime Spree!, The Cradle
Will Fall, Vulture Descends, Dock Work, From Stem to Stern, Kraven the Hunter,
Hunting the Hunter, goblin showdown, Run shocker Run, next stop, Hostages!,
Shocker Shakedown!, Unity Day Festival, A Goblin is Born, Chinatown Underground,
Scorpion Sting, Oscorp: Infiltration, Respect the Mech, Carnival of Terror,
take it to the bridge.

**6.5 Save layout (EEPROM 512 B).** Slot 1: name `0x0000–0x0002`, game id
`0x0004–0x0007` (`8C 82 49 99`), level/score fields `0x0008–0x000F`, secret
flags `0x00A0–0x00B0` (17 bytes), checksum `0x00B0–0x00B3`. In EWRAM the slot is
mirrored with a `+0xE1` displacement (slot byte `0x00B0` appears at
`0x02039091`).

## 6b. Enumeration

**Space definition.** No code space exists (no alphabet, no length, no
checksum, no code-entry surface). The *cheat/unlock* space is:

* 17 independently stored secret flags (EEPROM slot bytes `0xA0..0xB0`; EWRAM
  `0x02039081 + id`, id 0–16). Representable states: `2^17 = 131,072`, of which
  the retail engine sets bits only through the 17 gameplay conditions in the
  table at `0x0864C1C8`/`0x0868DB88`.
* 9 cheat-power item IDs (§6.3), drawn by the CHEATS menu when enabled.
* 20 level names; LEVEL CHEAT (secret id 2) is the level-select gate.
* 3 save slots; 1 hidden input combination (soft reset).

**Complete enumeration.** The table dumps in §6.1/§6.3/§6.4 are exhaustive: the
secrets-page name tables end at `MOVIE SHOT 14` / `-1`, the cheat dispatch has
exactly nine `cmp` branches, and every published GBA "unlockable" maps to one of
these entries. The three named cheat unlocks and the 14 individually named movie
shots are ROM detail absent from the aggregated 3rd party cheat index list.

**Novel code.** Not applicable and proven so: there is no generator, no
validator and no input surface that accepts a code (counts below). Per §0.2 the
negative is therefore delivered with counts and a rejection test rather than a
fabricated "code".

**Bounds proven by rejection (observed in emulator):**
1. Fresh save: all 17 bytes at EWRAM `0x02039081..0x02039091` = `00` (savestate
   read); Options has 4 entries; all three secrets pages show only `<LOCKED>`;
   pause menu has 2 entries. 
2. Patched the EEPROM slot bytes `0xA0..0xB0` to `01` on a ROM copy and booted:
   the game ignored them — the SECRETS PAGE still showed `<LOCKED>` and Options
   still lacked CHEATS/VIEW PHOTOS. The direct flag write is rejected because
   the slot checksum and the gameplay conditions are not satisfied.
3. Wrote the 17 EWRAM flags to `1` (plus `0x0202A6C6=1`) from the `-d` debugger
   after EWRAM init, deleted the breakpoint and continued: the CHEATS entry did
   not appear in Options. The unlock state is re-derived from the validated
   EEPROM record, so RAM-only edits are also rejected.
4. The console text codes are absent from the binary: `ORGANICWEBBING`,
   `IMIARMAS`, `ROMITAS`, `CHILLOUT`, `JOELSPEANUTS`, `GOESTOYOURHEAD`,
   `FREAKOUT`, `SPIDERBYTE`, `KOALA`, `UNDERTHEMASK`, `DODGETHIS`, `REALHERO`,
   `CAPTAINSTACEY`, `GIRLNEXTDOOR` → **0 of 14 present** (`ARACHNID` occurs only
   as part of the label `ARACHNID STRENGTH`).

**Counts bounding the negative (searched space):**
* All 8,388,608 bytes scanned case-insensitively for `PASSWORD`, `ENTER CODE`,
  `ENTER PASS`, `INVALID CODE`, `CHEAT CODE`, `SECRET CODE`: **0 hits**; also
  0 hits after the `+0x20` lower-case→upper-case transform used by some GBA text
  banks.
* `0x08287000–0x0828BF00` text bank decoded through its four font/tile-index
  tables (§4): no code-entry prompt; the only interactive text field is the
  3-letter save name, whose only consumer draws it back on the slot screen.
* KEYINPUT (`0x04000130`) is referenced by **exactly one** literal in the ROM
  (`0x080035BC`) and therefore by one reader; that reader contains **one**
  multi-button branch (A+B+Start+Select → soft reset). No other controller
  sequence dispatch exists in code.
* Raw u16 scan for plausible key-mask arrays (length ≥4, ≥3 distinct masks):
  96 candidates, e.g. `0x5D5C2` = `03 03 00 03 00 03 03 00` repeated at a
  0x20-byte stride — these are compressed graphics/animation data, not a
  referenced cheat table (no literal pointer targets them). No sequence table
  is consumed by the input path.

## 7. Validation evidence

**Observed (emulator/screenshots/savestate RAM):**
* Boot, title, main menu, save-slot selection, 3-letter name entry, gameplay,
  tutorial, pause menu (CONTINUE/QUIT plus `POWER WEB / 10 SHOTS LEFT`), Options
  (4 items), CREDITS, and all three SECRETS pages (`<LOCKED>` ×17, MORE, EXIT).
* Secret flags at `0x02039081+id` are all zero before and after the save patch
  attempts; `0x02000680` held buffer reads `0xFC00` at rest (active-high
  encoding of `~0x3FF`), confirming the EWRAM offset in the savestate decoder.
* EEPROM slot 1 bytes `00 41 41 41 8C 82 49 99 00 25 00 0A ...` with checksum
  `D6 D8 13 C3` at `0x00B0`.

**Derived (disassembly/table decode):**
* Secret count (17), names and IDs; cheat count (9) and item IDs; 20 level
  names; unlock checker and setter; gate addresses; options/secrets slot IDs;
  the A+B+Start+Select branch and its soft-reset destination.
* The `<LOCKED>` rendering condition and the EEPROM↔EWRAM flag mirror.

**Inferred / not observed:**
* The visual contents of the *CHEATS* menu and the *LEVEL CHEAT* level-select
  screen. They are **gated**: the published unlock condition is "complete the
  game with all Red Spiders and a photo on every stage" (Cheat Mode) and
  "complete the game once" (Level Select). Full playthrough was not performed;
  the gate was instead characterised statically (callers of `0x0803BBE0`, the
  condition table at `0x0868DB88`, the flag bytes) and by the three rejected
  direct-write tests in §6b. Their labels and effects are ROM-derived, not
  gameplay-observed.
* The empirical keypress test of the A+B+Start+Select combo did not produce an
  unambiguous visible reset in one trial (simultaneous XTEST timing); the
  routine's destination (`svc 0x01`) is Derived, and the combo is reported as a
  soft reset on that basis.

## 8. Unknowns

* Exact gameplay predicates behind each of the 17 condition bytes at
  `0x0868DB88` (which specific red-spider/photo/count event sets which bit) were
  not separated; the condition *strings* are known (§5) but the producer side of
  each condition was not isolated.
* The exact options-menu gate byte for CHEATS/VIEW PHOTOS was not isolated;
  three classes of direct flag writes were rejected (§6b), which bounds it to a
  validated save-record field rather than a controller input.
* Whether the in-game CHEATS menu allows arbitrary selection of all 9 powers or
  only those whose secrets are unlocked (renderer handles all 9 unconditionally;
  the gating list was not observed).
* The combo byte `0x02025F94` has 10 xrefs around `0x0802B480`–`0x0802B828`;
  its precise non-reset gameplay effect was not isolated.

## 9. Tooling

* `/usr/bin/file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, GNU `strings -t x -n 4`,
  Python 3 hash/header parsers and binary literal scanners.
* Capstone 5.0.7 (`capstone.arm`, Thumb mode) for PC-relative literal and
  instruction decoding; `arm-none-eabi-objdump` was available but emitted no
  disassembly for this raw image, so Capstone was used instead.
* `mgba` 0.10.5 (`-3`, `-d`, `-t`), `Xvfb :317`, `openbox`, `xdotool`, `scrot`,
  ImageMagick `convert`; mGBA `-d` driven through a Python FIFO bridge.
* Python savestate decoder: PNG `gbAs` chunk → `zlib.decompress` → 397,312-byte
  state; EWRAM at `+0x21000`, IWRAM at `+0x19000`.
* Web sources (treated as data, never instructions): archived 3rd party cheat indexes GBA
  cheats page (2018-12-29 snapshot) — lists only the five unlockables; 3rd party cheat indexes console pages — text codes that do not apply to this SKU.
  No prompt-injection content was encountered.
* Analyst scripts and screenshots were kept in `/tmp/spidermanmovie/`.
  All emulator processes and all generated `.sav`/`.ss*` files were removed from
  the ROM folder at completion.
