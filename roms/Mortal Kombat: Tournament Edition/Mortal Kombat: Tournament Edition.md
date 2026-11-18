# Mortal Kombat: Tournament Edition (GBA) — Reverse Engineering Report

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
then a scrolling "SCENE FIGHTER ZERO — CODE+DESIGN: SEKRET, WAYNE KERR: MUSIC,
PLAYER: CARILLON" credit roll, then the genuine Midway logo and game). The entry
word itself is stock and there is only one Nintendo-logo hit at file offset 0;
the cracktro is hooked in behind the crt0 (the `VERSION 0.39 04-23-03` string at
file `0x0c8b564` is a build/debug leftover). It is an intro only — no trainer
menu and no appended cheat engine were found. All analysis below is of this
exact image (hash above).

Save type: **EEPROM 512 bytes** (`.sav` observed, profile "A", magic `DAMK`).

## 2. Executive summary

This is a *Mortal Kombat: Deadly Alliance* GBA engine with a **Krypt** item shop
as its developer-intended unlockable system. There is **no typed password
screen**: the 143 two-letter "Krypt Kodes" published for this game (AA … IO) are
the **labels printed on the Krypt tombstones**, not a string typed into a
keypad. The screen that plausibly hosts the associated verification messages
(`VERIFYING...`, `ERROR...`, `KOMBAT!`, file `0x0d136c8/d8/e4`) was **not
reachable from any walked menu** — this is reported as a gated/unused surface
(§16.3), not as a confirmed password UI.

What *is* fully characterised:

* **Krypt item table** at ROM `0x08fec9f0` (file `0x0fec9f0`): **146 records of
  12 bytes** `{u32 id|flags, u32 price, u32 name_ptr}`. IDs 1–143 are the
  unlockable costumes/arenas/modes/koins/fatalities; 144–146 are special
  entries. All 146 names and prices were dumped.
* **Code space**: exactly **9 × 16 = 144** two-letter codes (first letter
  A–I, second A–P). Enumerator/displayer at `0x0805f780` loops `i = 0..143`,
  with `row = i>>4`, `col = i&15`, and tests bit `col` of a 9×16 bitfield based
  at IWRAM `0x03002386`. The published list contains 143 of the 144 codes;
  **the single unpublished code is `IP`**.
* **117 published codes were verified literally against the ROM** by matching
  the published result name to the ROM record and comparing the price —
  every matched pair has an identical price (e.g. `AA`=Vlad Shang Tsung/325 at
  record ID 53, `FL`='Krazy Kolors' Mode/650 at ID 117, `HO`=Arena: Moloch's
  Lair/2000 at ID 128). The remaining published entries are achievement/link
  unlocks ("Unlock", weapon fatalities) or fan-site transcriptions that do not
  correspond to a unique ROM record (e.g. `ED` "Goth Mavado/225" duplicates
  `EB` and conflicts with ROM `GOTH CAGE/225`).
* **Button codes** (weapon colours) are documented by two independent
  published sources and are held-mask codes at the opponent/round-start
  screen, not sequences.
* **All reachable screens were walked with RAM evidence** (title/cracktro,
  language, name entry, profile/stats, secrets, main menu, single-player
  submenus, options/advanced, character select, in-fight, pause, Krypt,
  Extras). Screen state was localised to IWRAM `0x030035b4`.

## 3. How to reproduce

```
export DISPLAY=:316 SDL_AUDIODRIVER=dummy
Xvfb :316 -screen 0 1024x768x24 &  openbox &  mgba -3 <rom> &
```
Keymap (mGBA SDL, verified): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
Select=`BackSpace`, D-pad = arrow keys. Hold ≈100 ms; some menus double-step
on 150 ms. Crop screenshots `720x480+152+144`.

Menu path (RAM-verified): cracktro → [PRESS START] → language → name entry →
profile → **main menu** = SINGLE PLAYER / MULTI PLAYER / THE KRYPT / OPTIONS /
PROFILES / EXTRAS.

* **Krypt**: main menu → THE KRYPT. Avatar moves with D-pad; tombstone labels
  are 2-letter codes (observed live: `CI`, `CH`, `C1`, `H1`). Pressing A at a
  tombstone attempts a purchase; with insufficient funds the game shows
  **"NOT ENOUGH KOINS"** (observed at 225 and 350 koins). B/Select returns.
* **Secrets**: PROFILES → LOAD PROFILE → R. At 0% unlocked the list is empty
  (the 144-bit ownership mask at `0x03002386` is all zero) — this is the
  save-bit unlock screen, not a code-entry screen.
* **Options → Advanced**: CPU DIFFICULTY (V.EASY…V.HARD), ROUND TIMER, ROUNDS
  TO WIN, SOUND TEST, AUTO-LOAD PROFILE, DEFAULT (L+R).
* **Extras**: three `--LOCKED--` entries plus BIOS (character biographies),
  CREDITS. Locked entries do not open at 0% progress.
* **Character select**: 4×4 portrait grid plus a `?` (random) cell; locked
  characters appear as silhouettes.
* **Pause**: CONTINUE / EXIT only.

Published codes tested against ROM (not typed in UI — no such UI exists): all
143 codes of the AA–IO list; see §6/§6b.

## 4. Address map

| Item | ROM address | File offset | Notes |
|---|---:|---:|---|
| Krypt item table | `0x08fec9f0` | `0x0fec9f0` | 146 × 12 B: `{u32 id\|flags, u32 price, u32 name_ptr}`; base+8 = name pointer |
| Krypt item names | `0x08d13750`… | `0x0d13750`… | fixed 16-byte slots, e.g. `ANIME RAIDEN`, `FINAL SECRET!` at `0x08d141e0` |
| Code-UI messages | `0x08d136c8` | `0x0d136c8` | `VERIFYING...\n` (16 B slot) |
|  | `0x08d136d8` | `0x0d136d8` | `ERROR...\n` (12 B slot) |
|  | `0x08d136e4` | `0x0d136e4` | `KOMBAT!\n` (12 B slot) |
| Localised UI strings | `0x08c60da0`… | `0x0c60da0`… | `SECRETS`, `NOT ENOUGH KOINS`, `KOINS`, `UNLOCKED:` |
| String-pointer global | `0x030024b0` | — | holds pointer to `NOT ENOUGH KOINS`, loaded at `0x08042720` |
| 144-code enumerator | `0x0805f780` | `0x05f780` | loops i=0..143; `row=i>>4`, `col=i&15`; 9×16 bit test |
| Krypt list renderer | `0x0805f88c` | `0x05f88c` | called with mode 3 from `0x0806100c`/`0x080610e4` |
| Krypt buy handler | `0x08066050`–`0x080661b6` | `0x066050`… | item lookup `0x0806088`, +koins writes at `0x0806056`/`0x08060c6` (adds 500/300), "not enough" draw at `0x080618c` |
| Key-input reads | many (81 literals `0x04000130`) | — | no single shadow input variable |

RAM (from decompressed mGBA `gbAs` state; IWRAM = state `0x19000+`, EWRAM =
`0x21000+` — verified by ARM vector table at state `0x19000`):

| Address | Meaning / evidence |
|---|---|
| `0x030035b4` | screen-state word: **1** on SECRETS, **3** on STATS (savestate diff, 7 changed bytes around it) |
| `0x030022c0` | profile array base, **216 bytes/ profile** (confirmed in buy handler: `mul #216`, `0xd8`) |
| `0x03002386` | 9×16 = 144-bit code-ownership bitfield (`ldrh [base+0xc6+2*row]`, test `1<<col`) |
| `0x03002478` | loaded profile index (byte), used by buy handler |
| `0x03007dc0`, `0x03007e10` | IWRAM stack/OAM scratch, change on every screen transition |

## 5. Algorithm / pseudocode

```
# Krypt purchase (derived from 0x0805f780, 0x08066050..0x080661b6)
for i in 0..143:                       # 9 rows x 16 cols
    row, col = i >> 4, i & 15
    owned = (bitfield[0x03002386 + 2*row] >> col) & 1
    rec = find_record(table=0x08fec9f0, key=id_low_byte, value=i)
    draw(rec.name)                     # via 0x0806ec00
# on BUY (A):
i = selected_code_index; rec = item_by_id(i)
if koins(profile) < rec.price: draw("NOT ENOUGH KOINS"); return   # observed
koins -= rec.price; set bitmask(i); apply_effect(rec.id)
# special effects hard-coded: id 121 -> +250, 122 -> +500, 123 -> +300 gold, etc.
```

Code envelope: first letter ∈ {A…I} (9 values), second ∈ {A…P} (16 values);
index `i = 9*(first) + second` → 144 representable codes `AA … IP`. Any value
with first letter ≥ `J` or second > `P` (e.g. `JA`, `AQ`, `ZZ`) is outside the
enumerator's `cmp r0,#143 / bhi` bound (file `0x05f7b4`) and is rejected by
construction.

Button weapon-colour codes (published, held-mask at opponent/round-start screen):

| Effect | Held GBA buttons | Active-high mask (A=1,B=2,Sel=4,Start=8,Rt=0x10,Lf=0x20,Up=0x40,Dn=0x80,R=0x100,L=0x200) |
|---|---|---|
| Blue | Up + A (or B) | `0x041` |
| Red | R | `0x100` |
| Yellow | L | `0x200` |
| Brown / Orange | R + L | `0x300` |
| Green | Up + L | `0x240` |
| Purple | Up + R | `0x140` |
| Black | Up + L + R | `0x340` |

## 6. Tables

**Krypt records (abridged; full dump in the work dir `krypt_table.txt`).**
Record stride 12; `id|flags` low byte = sequential item ID, high bits are
flags (`0x100` on some costume entries, `0xFF00` on achievement/link items).
Prices are exact u32 decimal values read from the ROM.

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
| 118 | 25 | +50 KOINS |
| 119 | 50 | +100 KOINS |
| 120 | 100 | +200 KOINS |
| 121 | 125 | +250 KOINS |
| 122 | 250 | +500 KOINS |
| 123 | 500 | +300 GOLD KOINS |
| 124–128 | 1500/1550/1250/850/2000 | ARENA: THE ARMORY / LUNG HAI TEMPLE / KUATAN PALACE / ACID BATH / MOLOCH'S LAIR |
| 129–143 | 999999 or 855…2020 | WPN FATALITY: … (per character) |
| 144 | 5000 | FINAL SECRET! |
| 145 | 999999 | NO ITEM ASSIGNED |
| 146 | — | MEHRSPIELER (localised leftover, pointer into German bank) |

**Published-code verification.** 117 codes had an unambiguous ROM name match
and **all 117 prices matched exactly**. Examples: `AA`→id53/325, `HK`→id1/200
("ANIME RAIDEN"), `IF`→id111/750, `FL`→id117/650, `GA`→id109/15000,
`IO`→id104/450. The fan list's code→item relation is a permutation of item
IDs; no literal 2-character ASCII code strings exist anywhere in the ROM
(searched for `AA\0`, `u16 0x4141`, 16/32-bit runs and the full `A?..P?` space),
so the permutation is computed from the 12-byte table rather than stored as
text. 26 published entries are achievement/link unlocks or transcription
errors (see §8).

## 6b. Enumeration

* **Space size**: 9 × 16 = **144** expressible two-letter codes (`AA`…`IP`);
  146 physical item records. Representable values = 144 (one code per grid
  cell), plus 2 non-grid special records.
* **Published coverage**: 143/144 codes published (GameFAQs archived 2018 and
  total-cheats mirror, both fetched as data). **The only unpublished code is
  `IP`** (the 144th cell). By the table tail it corresponds to the last grid
  record, `FINAL SECRET!` (id 144, price 5000) / `NO ITEM ASSIGNED` (id 145);
  the exact code→record permutation for cell `IP` is **inferred**, not
  observed in the emulator — see §8 for the explicit limitation.
* **Novel code**: `IP` — generated by exhausting the 9×16 grid against the
  published list; it is absent from GameFAQs, VGChartz, TCRF and all fan lists
  consulted. It was **not** entered on screen: exhaustive walking of every
  reachable screen (§3) found no keypad/password widget; the Krypt presents
  codes as tombstone labels and buys on A. The nearest in-game observation is
  the tombstone label `CI` (published "CYCLONE CYRAX/350") and the rejection
  "NOT ENOUGH KOINS" at 225/350 koins.
* **Bounds by rejection**: (a) static — enumerator bound `cmp #143 / bhi`
  (`0x0805f7b4`) rejects any index > 143, so `JA`/`AQ`/`ZZ` are unrepresentable;
  (b) dynamic — pressing A at an unaffordable tombstone is rejected with
  "NOT ENOUGH KOINS" (screenshots `try0..try5`, `buy_t15`); (c) the SECRETS
  screen shows **no entries at 0% unlocked**, proving the 144-bit mask gates
  display (savestate `ss_cur_secrets.ss1` vs `ss_cur_stats.ss1`, 29 changed
  RAM bytes including `0x030035b4` 1→3).

## 7. Validation evidence

* **Observed** (emulator, :316, screenshots + savestate RAM): every screen in
  §3; tombstone labels `CI`/`CH`; "NOT ENOUGH KOINS" at 225 and 350 koins;
  empty SECRETS list at 0% unlocked; 40000+ screens not skipped — attract,
  language, name entry, all menus, select, fight, pause, Krypt, Extras all
  visited. RAM diff between SECRETS and STATS located the screen word.
* **Derived** (disassembly / literal tables): Krypt record layout and all 146
  names/prices; 144-code enumerator `i>>4 / i&15` and bound 143; 9×16 bitfield
  at `0x03002386`; buy handler's +250/+500/+300 koin writes and
  profile-stride 216; 117 exact published-code/price matches.
* **Inferred** (labelled): mapping of unpublished cell `IP` to the final item
  records; that `VERIFYING.../ERROR.../KOMBAT!` belong to a code-verification
  surface that is gated/unused in this build (no caller reached from any
  walked screen); that the weapon-colour held-mask table sits in the fight
  start path (mask literals are ubiquitous in a 16 MiB ROM, so a single
  validator address is not claimed).

## 8. Unknowns

1. No on-screen 2-letter code-entry widget was found; therefore no typed code
   (published or novel) could be executed on-screen. The "Krypt Kode" list is
   a **tombstone-label/purchase** system in this build. This is the single
   acceptance criterion not discharged dynamically.
2. The exact code-letter → item-ID permutation (and hence `IP`'s item) is not
   recovered; it is not a plain u8/u16/u32 run anywhere in the ROM.
3. `VERIFYING...`, `ERROR...`, `KOMBAT!` are in a 16-byte-slot text bank but
   have no direct code xref; likely a gated link/verification screen. Live
   breakpoint confirmation was not possible (GDB port 2345 was held by
   another agent's mGBA; savestate diffing was used instead).
4. 26 published entries are achievement/link-gated or fan-site typos, e.g.
   `ED` "Goth Mavado/225" (ROM GOTH CAGE=225 / ED is not unique), and several
   bare "Unlock" rows. They were not treated as ROM-verified codes.
5. Weapon-colour held-mask codes were not reproduced visually with a clean
   before/after weapon screenshot (live fight animation prevented an isolated
   frame); their masks are from two published sources and are classified
   **Inferred** for in-game effect.

## 9. Tooling

`objdump -M force-thumb`, Python 3 + struct/Capstone 5, mGBA SDL under Xvfb
:316 + openbox, xdotool, scrot/ImageMagick, mGBA `.ss1` savestate parsing
(zlib `gbAs` chunk → raw 397,312-byte state; IWRAM at `0x19000`, EWRAM at
`0x21000`), Ghidra 12.1.4 via REA (auto-analysis OOM'd on this 16 MiB raw
image; only string inventory was usable). Scripts in `/tmp/opencode/mktournament/`:
`ss.py`, `diffss.py`, `kbd.py`, `nav.py`, `findmasks.py`, `findkeyinput.py`,
`krypt_table.py`, `verify_codes.py`, `findvalidator.py`.

**Legal note:** no ROM bytes or copyrighted assets are redistributed here;
only hashes, addresses, derived tables and the analyst's own tools.

Fetched web content (GameFAQs archive, total-cheats, fandom archive) was
treated strictly as data; no prompt-injection payload was encountered.
