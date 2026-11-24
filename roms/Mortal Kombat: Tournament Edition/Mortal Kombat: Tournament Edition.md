# Mortal Kombat: Tournament Edition (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Mortal Kombat: Tournament Edition.gba` |
| Size | 16,777,216 bytes (0x01000000, 16 MiB) — single image, **no embedded second header** |
| Header title | `MKTOURNAMENT` |
| Game code / maker | `AW4E` (region **E** = USA) / `5D` |
| Fixed byte / version | `0x96` / `0x00`; complement `0x22`; header checksum `0x0000` |
| Entry word | `0xEA00002E` → `b 0x080000C0` (stock crt0) |
| MD5 | `943ec8ef80cd5d01ac03e86da6eea28e` |
| SHA-1 | `405be6e00eabdef9d5600341ac5d2854d38002b3` |
| SHA-256 | `82a448e163c3889ae5ad3dbef85694f815734e0a6861b8ea749cc2178f013e96` |

**Patch notice (§16.1).** The boot sequence is a **Mode 7 scene-release cracktro**
("A MODE 7 PRODUCTION / PROUDLY PRESENTS MK TOUR EDITION / 128MBIT - USA VER.",
then a scrolling "SCENE FIGHTER ZERO …" credit roll, then the genuine Midway logo).
The entry word is stock and there is only one Nintendo-logo hit at file offset 0;
the cracktro is hooked in behind the crt0. It is an intro only — no trainer or
appended cheat engine. All analysis below is of this exact image.

Save type: **EEPROM 512 bytes** (`.sav` observed, profile "A", magic `DAMK`).
Fetched web content (3rd party cheat indexes,
fandom) was treated strictly as data; no prompt-injection payload was found.

## 2. Executive summary

This is a *Mortal Kombat: Deadly Alliance* GBA engine with two genuinely distinct
systems, both now closed:

1. **Weapon-colour button codes — CONFIRMED IN GAME (Observed).** Holding the
   documented button mask at the **battle-plan / opponent-intro screen** and
   pressing A changes a weapon-palette halfword in IWRAM. All seven documented
   masks were reproduced with distinct BGR555 colours; undocumented masks are
   rejected. This was the largest prior gap and is now discharged with RAM
   evidence (§7.1).

2. **The 2-letter "Krypt Kodes" — BOUNDED NEGATIVE, PROVEN.** The 143 published
   two-letter codes (AA…IO) are **tombstone coordinate labels in the Krypt**, not
   a typed password system. There is no code-entry widget, no 2-character input
   buffer, no code-string table, and no input router to the 144-cell enumerator.
   The one text-input widget in the game is the profile **name-entry** letter
   grid. The `VERIFYING...`/`ERROR...`/`KOMBAT!` strings are text-bank data with
   **zero code xrefs** (link-verification vocabulary), not a validator's output.
   This is a legitimate bounded negative (§7.2), not an open unknown.

Fully characterised data (retained from the first pass):

* **Krypt item table** at ROM `0x08fec9f0` (file `0x0fec9f0`): 146 records × 12
  bytes `{u32 id|flags, u32 price, u32 name_ptr}`. All 146 names and prices were
  dumped (§6).
* **Code space**: exactly 9 × 16 = 144 two-letter labels (first letter A–I =
  row, second A–P = column). The enumerator at `0x0805f780` loops `i=0..143`,
  `row=i>>4`, `col=i&15`, and tests bit `col` of a 144-bit ownership mask.
  143/144 labels are published; the single unpublished cell is **`IP`** (§6b).
* **117 published code→item pairs verified** against the ROM by name+price;
  every matched pair has an identical price. 26 entries are achievement/link
  unlocks or fan-site transcriptions with no unique ROM record.

## 3. How to reproduce

```
export DISPLAY=:319 SDL_AUDIODRIVER=dummy
Xvfb :319 -screen 0 1024x768x24 &  openbox &
mgba -3 -t /tmp/mktournament/ss_charselect.ss1 <rom> &
```
For the RAM experiments the **mGBA command-line debugger** is used:
`mgba -3 -d -t <state> <rom>`; drive it through a pty (script in §9). Keymap
(mGBA SDL, verified via KEYINPUT at `0x04000130`): A=`x`, B=`z`, L=`a`, R=`s`,
Start=`Return`, Select=`BackSpace`, D-pad = arrow keys. `xdotool keydown`
registers in the emulated keypad during debugger `frame` advance; hold is
required (a 10 ms tap can be missed).

**Weapon-colour reproduction (exact, deterministic):**
1. Load `ss_charselect.ss1` (character-select screen) with `-d`.
2. Hold A (`xdotool keydown x`), issue 160 debugger `frame` commands, release A,
   frame 3 → the **battle-plan screen** "BO' RAI CHO VS. JOHNNY CAGE"
   (`wc_*_plan.png`), arena "SARDA RUINS".
3. Hold the modifier mask; press-and-release A **twice** (8 frames each, 4-frame
   gaps) while holding the modifier; keep the modifier held for 60 more frames
   → "ROUND 1" fight (`wc_*_fight.png`), timer 60.
4. Read `x/2 0x03000a38 2` (weapon palette) and `r/1 0x03002087` (index).

**Krypt reproduction:** cracktro → [PRESS START] → language → name entry →
profile → main menu = SINGLE PLAYER / MULTI PLAYER / THE KRYPT / OPTIONS /
PROFILES / EXTRAS. In the Krypt the avatar moves with the D-pad; tombstone
labels are the 2-letter codes; pressing A buys ("NOT ENOUGH KOINS" when short).
PROFILES → LOAD PROFILE → R shows SECRETS (the 144-bit ownership list).

## 4. Address map

| Item | ROM address | File offset | Notes |
|---|---:|---:|---|
| Krypt item table | `0x08fec9f0` | `0x0fec9f0` | 146 × 12 B `{id\|flags, price, name_ptr}` |
| Krypt item names | `0x08d13750`… | `0x0d13750`… | 16-byte slots (`ANIME RAIDEN`, `FINAL SECRET!` at `0x08d141e0`) |
| 144-cell enumerator | `0x0805f768`/`0x0805f780` | `0x05f768`/`0x05f780` | `cmp #143 / bhi`; row=`i>>4`, col=`i&15` |
| Enumerator callers | `0x08060316`, `0x08060fc0`, `0x0806100c`, `0x080610e4` | — | Krypt screen handlers; mode 3 = full list, mode 0 = compact (`0x0805fb2c`) |
| Krypt buy handler | `0x08066050`–`0x080661b6` | `0x066050`… | item lookup, +koin writes, "not enough" draw |
| Name-entry letter grid | `0x0805e140`–`0x0805e220` | `0x05e140`… | only text-input widget; `adds #0x41`, ranges 0–12/13–25/26+ |
| Code-UI messages | `0x08d136c8`, `0x08d136d8`, `0x08d136e4` | `0x0d136c8`… | `VERIFYING...\n`, `ERROR...\n`, `KOMBAT!\n` — **no xrefs** |
| Key-input reads | 84 Thumb LDR sites to `0x04000130` | — | no single shadow input variable |

RAM (from decompressed mGBA `gbAs` state; IWRAM = state `0x19000+`, EWRAM =
`0x21000+`):

| Address | Meaning / evidence |
|---|---|
| `0x03000a38` (u16) | **Weapon palette colour**, BGR555 — direct RAM evidence (§7.1) |
| `0x03002087` (u8) | secondary colour flag (0 or 1) — diffed alongside the palette |
| `0x03002386` | 144-bit Krypt ownership mask (`0xc6 + 2*row + 216*profile`, test `1<<col`) |
| `0x030035b4` | field of a script-state object (magic `Smkh` at `0x030035b0`); written by the script VM at `0x080821d2` |
| `0x030022c0` | profile array base, 216 bytes/profile (`mul #216`, `0xd8`) |
| `0x04000130` | KEYINPUT, active-low; read directly at 84 sites |

## 5. Algorithm / pseudocode

```
# Krypt list rendering (derived from 0x0805f780)
for i in 0..143:                         # 9 rows x 16 cols
    row, col = i >> 4, i & 15
    owned = (mask[0x03002386 + 0xc6 + 2*row + 216*profile] >> col) & 1
    rec = record_with_id_low_byte(i)     # 12-byte records at 0x08fec9f0
    draw(rec.name)                       # via 0x0806ec00
# on BUY (A):
if koins(profile) < rec.price: draw("NOT ENOUGH KOINS")   # observed
koins -= rec.price; set_bit(i); apply_effect(rec.id)

# Weapon colour (Observed; battle-plan screen, A confirm required):
on A-confirm at battle-plan:
    keys = ~KEYINPUT & 0x3FF
    if keys matches Up+A  -> palette[0x03000a38] = 0x7C00  (blue)
    elif keys matches R   -> palette = 0x001F               (red)
    elif keys matches L   -> palette = 0x03FF               (yellow)
    elif keys matches L+R -> palette = 0x021F               (brown/orange)
    elif keys matches Up+L-> palette = 0x0BA3               (green)
    elif keys matches Up+R-> palette = 0x4010               (purple)
    elif keys matches Up+L+R -> palette = 0x0000            (black)
    else: palette unchanged (default 0xFFFF)
# Unspecified bits are ignored: Down+L+A still yields yellow (0x03FF).
```

## 6. Tables

**Krypt records (abridged; full dump in `/tmp/mktournament/krypt_table.txt`).**
Record stride 12; low byte of field 0 = sequential item ID with flag bits in the
high half (`0x100` on some costumes, `0xFF00` on achievement/link items).

| id | price | name (ROM string) |
|---:|---:|---|
| 1 | 200 | ANIME RAIDEN |
| 8 | 450 | REAPER RAIDEN |
| 53 | 325 | VLAD SHANG TSUNG |
| 65 | 200 | ANIME CYRAX |
| 70 | 350 | CYCLONE CYRAX |
| 104 | 500 | 'VB' MODE |
| 105 | 1000 | 'THERMAL' MODE |
| 107 | 1275 | 'CLASSIC' MODE |
| 108 | 1000 | 'NIGHT VISION' MODE |
| 109 | 15000 | FREE TEST YOUR MIGHT |
| 110 | 12000 | FREE TEST YOUR SIGHT |
| 111 | 750 | SELECT ARCADE MODE ARENA |
| 117 | 650 | 'KRAZY KOLORS' MODE |
| 118–123 | 25/50/100/125/250/500 | +50/+100/+200/+250/+500/+300 GOLD KOINS |
| 124–128 | 1500/1550/1250/850/2000 | ARENA: THE ARMORY / LUNG HAI TEMPLE / KUATAN PALACE / ACID BATH / MOLOCH'S LAIR |
| 129–143 | 855…2020 | WPN FATALITY: … (per character) |
| 144 | 5000 | FINAL SECRET! |
| 145 | 999999 | NO ITEM ASSIGNED |
| 146 | — | MEHRSPIELER (localised leftover) |

**Weapon-colour table (all values Observed in IWRAM at `0x03000a38`, u16 BGR555):**

| Documented held mask | Palette halfword | Colour | `0x03002087` |
|---|---:|---|---:|
| none (default) | `0xFFFF` | default/white | 0x00 |
| Up + A | `0x7C00` | blue | 0x00 |
| R (+A) | `0x001F` | red | 0x01 |
| L (+A) | `0x03FF` | yellow | 0x00 |
| R + L | `0x021F` | brown/orange | 0x01 |
| Up + L | `0x0BA3` | green | 0x00 |
| Up + R | `0x4010` | purple | 0x01 |
| Up + R + L | `0x0000` | black | 0x01 |

**Rejections (Observed, same measurement):** Down+A → `0xFFFF`; Right+A →
`0xFFFF`; Up+A held at character-select instead of battle-plan → `0xFFFF`;
Up+B without A confirm → `0xFFFF`. Down+L+A → `0x03FF` (yellow): bits outside
the recognised masks are ignored. These bound the accepted input space to the
seven documented masks at the documented screen with an A confirm.

## 6b. Enumeration

* **Space size**: 9 × 16 = **144** expressible grid labels (`AA`…`IP`), plus 2
  non-grid special records (ids 145–146). Representable values = 144.
* **Published coverage**: 143/144 (3rd party cheat indexes archived 2018 and mirrors, fetched
  as data). **Only unpublished cell: `IP`**; by the table tail it corresponds to
  `FINAL SECRET!` (id 144, price 5000) / `NO ITEM ASSIGNED` (id 145) — this
  cell→record relation remains **Inferred** (the label is a grid coordinate, not
  a typed value; §7.2).
* **Novel code**: `IP`, generated by exhausting the grid against the published
  list. It was **not typed on screen** because no such widget exists (bounded
  negative, proven in §7.2). The strongest in-game observations are the tombstone
  labels `CI`/`CH` and the "NOT ENOUGH KOINS" rejection when buying.
* **Bounds by rejection**: (a) static — `cmp r0,#143 / bhi` at `0x0805f7b4`
  rejects any index > 143, so `JA`, `AQ`, `ZZ` are unrepresentable; (b) dynamic —
  pressing A at an unaffordable tombstone is rejected with "NOT ENOUGH KOINS";
  (c) weapon-colour rejects listed in §6.

## 7. Validation evidence

### 7.1 Weapon colours — Observed (new work)

Method: mGBA CLI debugger, deterministic `frame` advance with real held
xdotool keys, from `ss_charselect.ss1` (§3). For every combo the sequence
reached the battle-plan screen and then the "ROUND 1" fight (screenshots
`wc_blue_plan.png`, `wc_blue_fight.png`, `wca_*.png` in `/tmp/mktournament2/`).

**RAM diff, blue (Up+A) vs red (R), identical frame counts, IWRAM
`0x03000000`–`0x03007fff`:** only **4 bytes** differ —

```
03000a38  blue=00  red=1f      -> halfword 0x7C00 (BLUE) vs 0x001F (RED)
03000a39  blue=7c  red=00         (BGR555 weapon palette in IWRAM)
03002087  blue=00  red=01      -> secondary colour flag
03007f9c  blue=6c  red=6e      -> stack/code-path artefact
```

`0x03000a38` is a BGR555 halfword: `0x7C00` = pure blue, `0x001F` = pure red.
This is direct graphical-RAM evidence that the held mask changed the weapon
colour, not merely an inference from fight animation. All seven masks were then
read individually (table in §6): each yields the expected BGR555 colour —
including `0x0000` (black) and `0x03FF` (yellow) — while no combo leaves the
default `0xFFFF`. Rejection tests (§6) bound the accepted space.

Sources agree on the mechanic and masks: 3rd party cheat indexes ("Enter this at the screen
where they show you who your opponent is. Hold both buttons until the round
begins"), 3rd party cheat indexes. The
battle-plan screen is exactly that screen (`wc_blue_plan.png`).

### 7.2 Code-entry resolution — bounded negative, Observed + Derived

**The 2-letter labels are purchase coordinates, not a password system.** Five
independent lines of evidence:

1. **The 144-cell enumerator is a closed renderer.** `0x0805f780` loops
   `i=0..143` (`cmp #143 / bhi` at `0x0805f7b4`), computes `row=i>>4`,
   `col=i&15`, tests bit `col` of the ownership mask at `0x03002386+0xc6`,
   finds the item record by id and draws its **name** via `0x0806ec00`. It reads
   **no keypad input and no character buffer**. Its only caller is `0x0805f768`,
   reached solely from the Krypt screen handlers (`0x08060316`, `0x08060fc0`,
   `0x0806100c`, `0x080610e4`, mode 3 / mode 0) — a closed call graph with no
   input path (Derived from disassembly + BL scan).

2. **No code-string table exists.** There is no contiguous run of 2-letter
   labels anywhere in the 16 MiB (`AA AB AC …` and all 16-code rows searched;
   no `u16`/`u32` code table). A typed-code validator would require such a table or
   an equivalent letter→index routine; neither exists in the Krypt code.

3. **The "VERIFYING…/ERROR…/KOMBAT!" strings are inert text-bank data.** They
   occur once each at `0x08d136c8/d8/e4` with **zero** literal-word, Thumb-LDR or
   ARM-LDR xrefs (checked exhaustively across the 16 MiB). They are reached, if
   at all, through the game's text-ID bank, and their vocabulary matches the
   link-cable verification screen — not a password validator's accept/reject
   output (Derived, with the zero-xref count as Observed).

4. **The only text-input widget is profile name entry.** `0x0805e140`–`0x0805e220`
   builds glyphs with `adds #0x41` over three letter ranges (0–12, 13–25, 26+)
   — an A–Z grid used for the player name. It has no path to the Krypt item
   table and accepts no 2-letter code (Derived + observed on screen).

5. **Dynamic walk:** every reachable screen was visited with RAM evidence.
   The Krypt shows tombstone labels with a "BUY [A]" prompt and a koin counter;
   A attempts a purchase. The SECRETS screen lists owned items via the 144-bit
   mask and at 0% progress is empty. No screen presents an editable two-character
   field (Observed).

**Conclusion:** the published "Krypt Kode" list is a legend for the tombstone
grid (coordinate = row letter A–I + column letter A–P), not a player-enterable
code system. Consequently no novel code can be typed, and `IP` is documented as
the one unpublished *grid cell*, not an enterable password. This is a legitimate
bounded negative (§0.2): the searched space is the complete screen set, the
complete ROM text/table space, and the complete callers of the only 144-cell
enumerator.

### 7.3 Other evidence
* **Derived**: Krypt record layout and all 146 names/prices; 144-code enumerator
  and bound 143; 9×16 bitfield at `0x03002386`; buy handler's koin writes and
  profile stride 216; 117 exact code/price matches.
* **Inferred (labelled)**: cell `IP` → final item records; the script-VM meaning
  of the `0x030035b4` field; that the inert `VERIFYING…` strings belong to a
  gated link-verification surface.

## 8. Unknowns

1. The exact letter→item-ID permutation used by the published fan list is a
   legend mapping; it is not a stored string table and was not recovered as a
   standalone data structure. It does not affect the bounded-negative conclusion.
2. The specific helper that writes `0x03000a38` was not isolated statically
   (mGBA CLI watchpoints did not fire on `frame` advance); the effect itself is
   fully Observed via RAM.
3. 26 published entries are achievement/link-gated or fan-site typos (e.g. `ED`
   "Goth Mavado/225" is non-unique; several bare "Unlock" rows) and were not
   treated as ROM-verified codes.

## 9. Tooling

`objdump -M force-thumb`, Python 3 + struct/Capstone 5, mGBA SDL and mGBA
**command-line debugger** under Xvfb :319 + openbox, xdotool, scrot/ImageMagick,
mGBA `.ss1` parsing (zlib `gbAs` → 397,312-byte state; IWRAM at `0x19000`,
EWRAM at `0x21000`). Scripts in `/tmp/mktournament2/`: `dbg.py` (pty
driver for the CLI debugger), `wc_experiment.py` / `wc_all.py` (deterministic
held-mask frame experiments), `wc_negative.py` (rejection tests), `findcolourcode*.py`,
`xrefs.py`, `blscan.py`, `keyrefs.py`, `scan_key_sites.py`, `find_wpn*.py`
(mask/xref scans), plus the first-pass `ss.py`, `diffss.py`, `kbd.py`,
`krypt_table.py`, `verify_codes.py` in `/tmp/mktournament/`.

**Legal note:** no ROM bytes or copyrighted assets are redistributed here;
only hashes, addresses, derived tables and the analyst's own tools.
