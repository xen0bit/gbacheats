# Boktai: The Sun is in Your Hand (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Boktai: The Sun is in Your Hand/Boktai: The Sun is in Your Hand.gba` |
| Size | 16,777,216 bytes (0x1000000) |
| Header title | `BOKTAI` |
| Game code | `U3IE` (USA) |
| Maker code | `A4` (Konami) |
| Version | 0x00 |
| Entry word | `0xEA00002E` (ARM branch at 0x08000000) |
| Complement check | 0x0C stored, 0x0C computed (valid) |
| Header checksum | **0x0000 stored, 0x59A4 computed** (field zeroed) |
| MD5 | `ff75c62ab690410cc8fca24204d783e9` |
| SHA-1 | `7164326283df46a3941ec7b6ceca889cbc40e660` |
| SHA-256 | `aad4eaf0b3ab9f80ffb3a5346d6607b2e2ea12f8e5f3851d2edd1306a4f7a8cd` |

The ROM contains exactly one Nintendo logo (file 0x04) and one GBA header; no
multi-game shell, no second image, no trainer banner, no IPS/patch marker
strings. The header checksum field is zeroed while the complement check is
valid; this is an anomaly of the supplied image (a dump/rebuild artifact), not
a gameplay patch. The end of the 16 MiB image is zero padding.

## 2. Executive summary

Boktai 1 has **no general password / code-entry system**. The only
developer-intended cheat code in the game is the classic **Konami button
sequence on the stone inscription in the Abyss**, which spawns one Life Fruit
chest. It is a **single fixed 10-press sequence**, not a table of codes and not
a checksummed code space:

```
Up, Up, Down, Down, Left, Right, Left, Right, B, A
```

The sequence is hard-coded in bytecode, not in a data table:
script **0x82A6** at ROM `0x08EC1679` calls engine function **0x7935
(`InitArray`)** with ten u8 values `40 40 80 80 20 10 20 10 02 01`, then calls
script **0xB6B2**, which installs a zone callback for zone **0xA67B**. The
callback keeps a progress index; when the tenth correct press arrives it sets a
flag and spawns a chest at `(0x0E40, 0x0100, 0x1240)`. Zone 0xA67B is in
collision map file **0x6CFA** and spans x `0x2900..0x3500`, y `0x0200..0x0C00`,
z `0..64`.

Other code-like systems were checked and are **not** cheat systems:

* **Top-floor passcode** (Bloodrust Mansion / Dark Castle text): a 4-digit
  numeric lock whose accepted value is the **current in-game clock time**
  (`HHMM`, 0000–2359). It is a story puzzle, not a published cheat list; 1,440
  time values exist, one valid at any instant.
* **End-game result password**: generated after clearing the game and entered
  on Konami's 2003 website, not in the ROM; there is no in-ROM entry screen or
  validator.
* **Sound Test**: an unlockable main-menu entry (`SOUND`) granted by collecting
  all **30 Silver Coins**; no code needed.

No hidden/debug menu was found. The only debug leftovers are source file names
and assert strings (`mask_test_00`, `sub01_00`, `enemy.c`, `bokuact.c`,
`mummyact.c`, …) in the 0x1DD7xx–0x1DDAxx region.

**In-game test status (important):** the Abyss was reached in mGBA using a
legitimate late-game save (Solar Tree, after Delusion Forest) plus a
save-position test harness. The exact 10-press sequence was entered in the
Abyss entrance map (map 0x120 = 288) in the first pass; in the second pass the
zone was located exactly (see below) but **could still not be stood in**. A
third pass (2026-10-26) corrected the second pass's main claim: a map-289
arrival is **not** a dead hang — the room renders and the map init script
completes — but the engine never creates the **player actor**, so the game
stays in the scripted arrival state (camera bound to the room's NPC, input
ignored, zone callback never serviced). The chest is therefore still
**unobserved**; see §6b and §8 for the exact evidence and the fields tested.

Second-pass result (2026-10-26, see §6b): zone **0xA67B is in map 289's live
collision map** at `x 0x0D00–0x1300`, `z 0x0F00–0x1400`, height 0–32, so the
scripted chest spawn `(0x0E40,0x0100,0x1240)` **is inside the zone** (the
`0x2900..0x3500` bounds quoted in the first pass come from collision map
0x6CFA, which is *not* the map the hint room loads). Script 0x82A6 was also
observed running on a map-289 load: the ten masks appear at Scratch+0x20C
(`0x0203F20C`) and the progress index at Scratch+0x216 (`0x0203F216`).

The published sequence is nevertheless confirmed byte-for-byte in the ROM and
the validator/effect are fully mapped (see §5–§6b).

## 3. How to reproduce

**Emulator / display**

```
Xvfb :194 -screen 0 1024x768x24 &
DISPLAY=:194 openbox &
DISPLAY=:194 SDL_AUDIODRIVER=dummy mgba-qt -3 game.gba &
```

mGBA 0.10.5 Qt, window 720×500 (720×480 game area + menu bar). Default keymap:

| GBA | Key |
|---|---|
| A | `x` |
| B | `z` |
| L | `a` |
| R | `s` |
| Start | `Return` |
| Select | `BackSpace` |
| D-pad | arrow keys |

Hold keys 200–400 ms; menus debounce. Capture with
`import -window 0x400006 out.png` and crop 720×480 at +0,+20.

**Solar sensor:** mGBA Qt `Tools → Sensors` (`Alt+T`, Down×2, Enter) exposes
`Light sensor Brightness 0..140` and an RTC (`System time` / `Fixed time`). Set
brightness 140 and a daytime fixed time if a sun path is needed. The Abyss
rooms used here are indoor/dark and showed 0 bars, so the sensor does not block
menu or code testing.

**Menus walked (all reachable without a save):**

* Title: `GAME START` ↔ `OPTIONS` ↔ `LINK` (horizontal; `SOUND` is absent
  until the 30-coin unlock). Start/A at the logo brings up the menu.
* Options: `TIME SETTING`, `SOLAR SENSOR SETTING`, `BASICS` (inline list:
  LOOK AROUND, …, END), `EXPLANATION` (inline list starting THE SOLAR SENSOR).
* Game Start: DATA.1/DATA.2, `START` / `DELETE`; empty slots create data.
* New-game flow: PLAYER NAME (A–Z, a–z, `. , ' - / _`, END), REGION SETTING,
  DIFFICULTY SETTING (Easy / Normal 1 / Normal 2 / Hard; Hard locked until
  clear), CONFIRM SETTING.
* Pause (`Start`): `SAVE`, `SLEEP`, `OPTIONS` (CONTROLS / TEXT SPEED / MARKER),
  `CANCEL`.
* Select menu: `ITEM` → `WEAPON` (sub-tabs `LENS`, `BATTERY`, `FRAME`,
  `GRENADE`) → `MAP` → `ITEM`; L/R (`a`/`s`) cycles.
* Link: Item Exchange / Link Battle / Emblem Resonance (link-cable only).
* First boot also: solar-sensor setup, time setting, caution pages.

Screenshots (work dir `/tmp/opencode/boktai1`): `shot0.png`, `s1.png`,
`s2.png`, `s8.png`, `mr1.png`–`mr3.png`, `opt0.png`, `basics0.png`,
`name1.png`, `reg0.png`, `diff0.png`, `conf0.png`, `pmenu1.png`,
`imenu1.png`, `tab1.png`, `tab2.png`, and Abyss shots `w14.png`, `amap.png`,
`darkmap4.png`, `code2.png`.

**Late-game save used for the Abyss:** GameFAQs save 13291 (Dark_Forte,
"after Delusion Forest", Solar Tree, Hard, 03:52), a SharkPort/GameShark
container. The container payload starts at 0x5A (header length varies) and is a
64 KiB SRAM/hardware-order image; the game reads slot 2 (`DATA.2 = Hatikan`).
The 8 KiB EEPROM image is the first 0x2000 bytes of that payload. A second
save (8837, BBEG, "right before the final battle", `DATA.1 = Django`, Dark
Castle 12F, Hard 04:25) was used to enumerate the endgame menus.

**Abyss access (test harness, not a published cheat):** two working recipes.
The first pass used the DATA.2 tab; the second pass found the tab navigation
fragile and instead **copies the Hatikan slot-2 block set into slot 1** and
loads `DATA.1` (the default tab), which avoids tab switching entirely.

*Slot-1 copy recipe (verified):* take the 0x2000-byte EEPROM image, convert
hardware→logical with an 8-byte-chunk reversal, copy slot 2's header (0x200,
0x28 B), World (0xDC0, 0x400), Stat (0x1200, 0x418) and extra (0x1A40, 0x168)
to slot 1 (0xC0 / 0x340 / 0x780 / 0x1840), warp slot 1, rebuild checksums, and
convert back. A slot whose header area ID (header+0x18, i.e. 0x218 for slot 2 /
0xD8 for slot 1) is left at the old value while the Stat map is changed is
shown as `NO DATA`; set both to the same area (28 = Abyss).

Warp fields (logical layout; slot 1 / slot 2):

| field | slot 1 | slot 2 |
|---|---|---|
| map ID (Stat+0x100) | 0x880 | 0x1300 |
| map init script (Stat+0x10C) | 0x88C | 0x130C |
| area ID (Stat+0x2DC) | 0xA5C | 0x14DC |
| position 3×i16 (Stat+0xF0) | 0x870 | 0x12F0 |
| header area (header+0x18) | 0xD8 | 0x218 |

**Save checksum format (corrected).** The first-pass tool wrote the checksumchunk in the wrong order, which is why copied slots showed `NO DATA`. The game
computes, in the **logical (8-byte-reversed) image**, over the block's
little-endian u16 words:

```
chunk16[0..3] = xor16, sum16, size, 0xFFFF      (LE u16, at the chunk offset)
```

This reproduces all nine chunks of both GameFAQs saves byte-for-byte
(global 0x18, slot headers 0xE8/0x228, World 0x740/0x11C0, Stat 0xB98/0x1618,
extra 0x19A8/0x1BA8).

Set the warp, rebuild the checksums, and write **0x2000 bytes** (mGBA's EEPROM
dump is 0x2000; the GameFAQs files carry a 16-byte container footer). This is
how the second-pass Abyss screenshots were taken. Save edits that also changed
the slot header area without matching the Stat are rejected; keep them equal.

**Third-pass warp values (testing convenience only).** The harness patches
**only the save** — no chest, flag, sequence or script bytes are ever written:

| Field | Value written |
|---|---|
| slot 1 Stat+0x100 (map ID) | `0x0121` (289) |
| slot 1 Stat+0x10C (map init script) | `0x7F89` |
| slot 1 Stat+0x2DC (area) | `0x001C` (28, Abyss) |
| slot 1 Stat+0xF0 (x,y,z) | `0x0E40,0x0000,0x1240` (inside 0xA67B) and five other positions |
| slot 1 header+0x18 (area) | `0x001C` |
| slot 1 blocks | copy of slot 2 (Hatikan) |

The two in-emulator pokes used during the pass (`Scratch+0x18=0x0401`,
`Stat+0x110=0x0A5B`, `Stat+0xF6=6`, `Stat+0xF8=0`) changed nothing and are
recorded as rejected. The Konami sequence was pressed with the normal buttons;
the progress byte was never written by hand.


## 4. Address map

### ROM / files

| Item | Address |
|---|---|
| GBA entry / header | 0x08000000 / file 0x000 |
| MFT headers (11 × 8 bytes) | ROM 0x085B02C4, file 0x5B02C4 |
| Script directory header (id 0x41F5/0xA8D9) | ROM 0x08E0DA84, file 0xE0DA84 |
| Script directory build date | 0x3EA8EAE6 |
| Scripts / strings | 5130 scripts, 4299 strings |
| String data base | file 0xE1BE1C |
| Hint text (string 3781 = 0x0EC5) | file 0xE3CCC6, ROM 0x08E3CCC6 |
| Hint display script 0x58D9 | ROM 0x08EC17B9 |
| Caller 0x49E6 (message-box call) | ROM 0x08EC17A2 |
| Map-289 init script 0x7F89 | ROM 0x08EC1486 |
| Konami setup script 0x82A6 | ROM 0x08EC1679 |
| Zone-callback script 0xB6B2 | ROM 0x08EC16B9 |
| Engine call table | ROM 0x08584C00 |
| Engine 0x7935 `InitArray` | ROM 0x08000B68 |
| Collision-map MFT dir (0xAC2C/0xAF05) | file 0x8ADD0C, 349 files |
| Collision map 0x6CFA (contains zone 0xA67B) | file 0x8ECCB0 |

### Map IDs (wiki-confirmed, used here)

| ID | Name | Init |
|---|---|---|
| 288 | `c05_00` Abyss: Entrance | 0x7F79 |
| 289 | `c05_01` Abyss: Big room with mummy | 0x7F89 |
| 290 | `c05_02` Abyss: Block puzzle | 0x7F99 |
| 291 | `c05_03` Abyss: Two doors | 0x7FA9 |
| 292 | `c05_04` Abyss: Big room after triangle door | 0x7FB9 |
| 293 | `c05_05` Abyss: Trap | 0x7FC9 |
| 294 | `c05_06` Abyss: 3 boks / square key | 0x7FD9 |

### Save (EEPROM 8 KiB)

mGBA writes a **0x2000-byte** EEPROM image. The GameFAQs `.sav` files are
0x2010 bytes: the same 0x2000 image plus a 16-byte (all-0xFF) container footer.
Work in the **logical** image (8-byte-chunk reversal of the hardware order) and
keep exactly 0x2000 bytes when handing the save to mGBA.

Each block is `data[size]` followed by an 8-byte checksum chunk. In the logical
image the chunk is four little-endian u16:

```
xor16, sum16, size, 0xFFFF        (sum/xor over the block's LE u16 words)
```

(Equivalently: read the raw/hardware image as big-endian u16 — the chunk is then
`0xFFFF, size, sum16, xor16`.) This reproduces all nine chunks of both GameFAQs
saves byte-for-byte; the first-pass note `ffff, size, sum16, xor16` described
the raw byte order but was implemented in the logical order, which is why copied
slots were rejected as `NO DATA`.

| Block | Data offset | Size | Checksum |
|---|---:|---:|---:|
| Global | 0x0000 | 0x18 | 0x18 |
| Slot 1 header | 0x00C0 | 0x28 | 0xE8 |
| Slot 2 header | 0x0200 | 0x28 | 0x228 |
| Slot 1 World | 0x0340 | 0x400 | 0x740 |
| Slot 1 Stat | 0x0780 | 0x418 | 0xB98 |
| Slot 2 World | 0x0DC0 | 0x400 | 0x11C0 |
| Slot 2 Stat | 0x1200 | 0x418 | 0x1618 |
| Slot 1 extra | 0x1840 | 0x168 | 0x19A8 |
| Slot 2 extra | 0x1A40 | 0x168 | 0x1BA8 |

Slot 2 Stat fields used here: map ID +0x100 (0x1300), init script +0x10C
(0x130C), area ID +0x2DC (0x14DC), position +0xF0 (0x12F0); slot 1 uses
0x880/0x88C/0xA5C/0x870. The GameFAQs container is **hardware byte order**:
each 8-byte doubleword is reversed relative to the logical layout. Convert with
an 8-byte chunk reversal, edit, reverse back, then rebuild checksums with the
corrected tool `/tmp/opencode/boktai2/sav.py` (the first-pass
`/tmp/opencode/boktai1/boksave.py` uses the wrong chunk order).

RAM (wiki, confirmed by GDB): map ID `0x0203D900`, area ID `0x0203DADC`,
position `0x0203D8F0`, keypad held/pressed/released `0x03004450/52/54`,
Scratch `0x0203F000`, World `0x0203E800`, Stat `0x0203D800`.

Additional RAM observed in the second pass:

| Item | Address |
|---|---|
| Konami mask array (10 bytes, written by 0x82A6) | `0x0203F20C` (Scratch+0x20C) |
| Konami progress index (script 0x82A6/0xB6B2) | `0x0203F216` (Scratch+0x216) |
| Live collision map buffer (decompressed, "HP") | `0x0202A404` |
| Keypad shadow written by the game | `0x03004450` |

## 5. Algorithm

### 5.1 Konami button code

Script 0x82A6 (map-289 init, also executed for the hint room):

```
InitArray(indexed-ptr u8, base=Scratch, off=0x020C,
          0x40,0x40,0x80,0x80,0x20,0x10,0x20,0x10,0x02,0x01)
Scratch[0x0216] = 0                    ; progress index
if (World/Scratch flag bit == 0) {
    SetZoneCallback(zone=0xA67B, actor=0xF5EB, mode=0xA5BF, callback=0xB6B2)
    ShowString(0x0EC5)                 ; "Words etched in stone:" + next strings
}
```

Script 0xB6B2 (zone callback, runs while inside zone 0xA67B):

```
if (key_pressed == expected[progress_index]) {
    progress_index++;
    if (progress_index == 9) {          ; tenth key matched
        progress_index = 0;
        if (one-shot flag == 0) {
            one-shot flag = 1;
            SpawnChest(x=0x0E40, y=0x0100, z=0x1240, ...);
        }
    }
} else {
    progress_index = 0;                 ; wrong press resets
}
```

Exact key masks (GBA active-high): Up=0x40, Down=0x80, Left=0x20,
Right=0x10, B=0x02, A=0x01.

The sequence is therefore a **single 10-state automaton**, not a table of
codes. The text on the inscription is only a hint; the validator's data is the
ten-byte array at ROM 0xEC1689.

### 5.2 Top-floor passcode

The text strings at 0xE39C52/0xE39E16/0xE39FD9/0xE3A234/0xE3A2E4 describe a
four-digit `[passcode]` shown by a first-floor hint panel and entered at the
top floor. The accepted value is the **current in-game RTC time** (`HHMM`), not
a fixed table. The strings use four `<VAR=n>` substitutions and one variant
inserts `:` between the second and third digits. Space: 0000–2359 (1,440 valid
times; all 10,000 four-digit inputs are enterable, one matches at any moment).

### 5.3 End-game result password

The post-clear password is generated for the Konami website (per the 2003
guides). No in-ROM password-entry screen or validator was found: the string
scan has no `PASSWORD`/`CODE` result screen, and the only "password" strings are
the passcode puzzle. It is out of scope for an in-ROM cheat code.

## 6. Tables

### 6.1 Konami sequence (ROM 0xEC1689..0xEC1697)

| # | Button | Mask | mGBA key |
|---:|---|---:|---|
| 1 | Up | 0x40 | Up |
| 2 | Up | 0x40 | Up |
| 3 | Down | 0x80 | Down |
| 4 | Down | 0x80 | Down |
| 5 | Left | 0x20 | Left |
| 6 | Right | 0x10 | Right |
| 7 | Left | 0x20 | Left |
| 8 | Right | 0x10 | Right |
| 9 | B | 0x02 | z |
| 10 | A | 0x01 | x |

### 6.2 Zone 0xA67B (map 289's live collision map)

| Field | Value |
|---|---|
| start x / z | 0x0D00 / 0x0F00 (map-289 live collision map) |
| end x / z | 0x1300 / 0x1400 |
| height range | 0..32 |
| zone ID | 0xA67B |
| actor type | 0xF5EB |
| trigger mode | 0xA5BF (remain) |
| chest spawn | (0x0E40, 0x0100, 0x1240) — **inside** the zone |

The `0x2900..0x3500 / 0x0200..0x0C00`, height 0..64 rectangle in the first-pass
table is the 0xA67B record of collision-map file **0x6CFA** (MFT collision
entry 151). That file is **not** the collision map the hint room loads: map 289
loads its own collision map into EWRAM `0x0202A404`, whose zone list is

| zone | x0..x1 | z0..z1 | height |
|---|---|---|---|
| 0xA67A (room) | 0x0100..0x1100 | 0x0100..0x0E00 | 0..96 |
| **0xA67B** | **0x0D00..0x1300** | **0x0F00..0x1400** | **0..32** |
| 0xCD23 | 0x1000..0x1100 | 0x0300..0x0400 | 16..32 |
| 0xCD24 | 0x0100..0x0200 | 0x0400..0x0500 | 16..32 |
| 0xCD25 | 0x0300..0x0400 | 0x0C00..0x0D00 | 16..32 |
| 0xCD26 | 0x1200..0x1300 | 0x1100..0x1200 | 16..32 |

Height in the zone record is player `y / 8` (a load at `y=0x100` = height 32
matches the 16..32 zones; `y=0` matches the 0..96 room zone). The chest spawn
`(0x0E40, 0x1240)` therefore lies squarely inside 0xA67B, so the zone and the
spawn are consistent — the earlier mismatch was a wrong collision-map
attribution, not a bad spawn.

### 6.3 Sound Test unlockable

Main-menu `SOUND` is added when all 30 Silver Coin flags are set. World struct
coin flags are at RAM 0x0203E8C0 bits 0..29 (save slot 2 World: 0x0DC0 + 0xC0 =
0x0E80). This is an unlockable, not a code.

## 6b. Enumeration

**Space definition.** The only in-game cheat code is the Abyss Konami sequence.
Its space is a **single value**:

* alphabet: the 10 GBA buttons (masks above);
* length: exactly 10 presses;
* table size: 1 (one expected sequence);
* checksum/reserved bits: none;
* branches: one success branch (spawn Life Fruit chest), one failure/reset
  branch.

**Published code verification.** The public code (`Up Up Down Down Left Right
Left Right B A`) is present **byte-for-byte** in the ROM at 0xEC1689 as
`40 40 80 80 20 10 20 10 02 01`. It is not merely a text hint; it is the
validator's array. The hint text at 0xE3CCC6 spells the same sequence, so the
public list is complete and correct for this system.

**Novel code.** Because the space is one fixed sequence, there is **no
unpublished value to mint**. Any different order, length, or substitution is a
different input and must be rejected by the automaton. The only "novel" values
are prefixes and single-press changes; they are **not accepted** by design.
This is a bounded negative statement about this code system, not a failure to
search: the ROM contains one InitArray call for this feature (script 0x82A6)
and one chest spawn (script 0xB6B2), and no other key-sequence table was found
in the script directory.

**In-game observations.**

* Reached the Abyss in mGBA from the Solar Tree save (after Delusion Forest)
  via a save-position harness; screenshots `w14.png` (Otenko "Full moon
  tonight"), `amap.png` (ABYSS 1F), `darkmap4.png` (map/room), `code2.png`
  (after entering the sequence).
* Entered the exact 10-press sequence with 400 ms holds. **No chest appeared**
  in map 288 (entrance). GDB read the live state: map ID `0x0120` (288), area
  `0x1C` (28), position `(0x05BF, 0x0000, 0x0F41)`. The callback is scoped to
  zone 0xA67B, which map 288 does not contain at all (its collision map has
  0xA67A and three 0xCD2x zones), so the null result is expected.
* **Second pass (2026-10-26).** Working under a clean emulator/daemon (the first
  pass had left two mGBA instances sharing one GDB stub, so "restarts" were
  replaying a stale process), the save harness was rebuilt with the correct
  checksum format and a slot-1 copy of Hatikan. Map 288 then loads and is fully
  playable at `(0x05BF,0,0x0F41)`: walking changes `x/z` in ~0x100 steps,
  `map=288 area=28` throughout, and the pause menu opens. Walking 30 steps
  Up/Right and 12 Down/Left, and a lawnmower sweep of the room, never changed
  the map ID. The 0xCD23 zone tile in map 288 fires a scripted event (map reads
  26 for a frame, then back to 288 at `(0x0200,0x0100,0x051F)`); 0xCD24/0xCD25
  at their height range (y=0x180..0x200) do nothing. None of them transition
  to 289.
* **Map 289 was reached only by save warp.** The zone callback *does* install:
  after a map-289 load the ten masks are at `0x0203F20C` =
  `40 40 80 80 20 10 20 10 02 01` and the counter at `0x0203F216` = 0.
* **Third pass (2026-10-26) — the arrival state was measured, not assumed.**
  The second pass reported "HUD only, flat `#212121`"; that frame is the
  *arrival dialogue* (Otenko "Full moon tonight." then "Moon Beauty is watching
  over you. Make her proud, Hati…"), which is drawn over a black background and
  must be advanced with A. Once the dialogue is dismissed the room **does**
  render, the HUD is live and the map is fully loaded
  (`evidence_map289_room_noplayer.png`,
  `evidence_map289_arrival_dialog.png`). What is missing is the **player
  actor**:

  | Probe | map 288 (save warp) | map 289 (save warp) |
  |---|---|---|
  | room renders | yes | yes |
  | map init script runs | yes (0x7F79) | yes (0x7F89, masks written) |
  | player actor record `type 0xF5EB` in EWRAM | **yes** — type at `0x02005B9C`, pos at `0x02005BA4` | **none** (scan of `0x02004000..0x0200D000`) |
  | live player struct (update cb `0x0811BA3D`) | `0x02006500`, holds the save position | only the NPC `0x02006A48` |
  | save position copied anywhere but Stat | yes (5 copies) | no (Stat `0x0203D8F0` only) |
  | camera | follows the player | follows the **mummy NPC** (screen scrolls with it, no input) |
  | pause/select menu | opens | does not open |
  | `0x0203F216` after the 10-press sequence | — | stays **0** |

  Map 288 in the same harness spawns the player at *any* save position tested
  (`0x05BF,0,0x0F41` and the deliberately bogus `0x0400,0x0200,0x0400` — the
  second pass's "only works from a specific position" is wrong; the working
  case was simply the untouched save). Map 289 was tested at
  `(0x0400,0x0400)`, `(0x0800,0x0100,0x0800)`, `(0x0E40,0x0100,0x1240)`,
  `(0x0B80,0x0100,0x0580)`, `(0x0E40,0,0x1240)` and one repeat with
  `Stat+0x110` set — the player actor is never created in any of them.
  The engine is alive in this state (PC sampling lands in the normal main loop
  and in the IWRAM audio mixer), so this is a *logic* state, not a crash.
* **The only RAM differences between the two arrivals** (same save, same code
  path, dumps at `/tmp/opencode/boktai3/d288b.bin`, `d289b.bin`) are map data:
  `Stat` map/init/pos, `Scratch+0x02` (0x29 vs 0x24), `+0x04` (0x30 vs 0x35),
  `+0x18` (0x0401 vs 0x0001), `+0x3C`, `+0x102`, and a new block of
  script-written words at `Scratch+0xA8..0xDE` (0x0258, 0x0400, 0x0022,
  0x07D0, 0x03E8, 0x0258, 0x0301, 0x000A, 0x0100, 0x0200, 0x000A, 0x03E8)
  plus the mask array at `Scratch+0x20C`. Poking these back to the map-288
  values (`Scratch+0x18=0x0401`), and poking `Stat+0x110=0x0A5B`,
  `Stat+0xF6=6`, `Stat+0xF8=0` did **not** create the player or restore
  control. `Stat+0xF8` is only a frame counter (`Stat+0x0C` ticks), and
  `Stat+0x110` is save data, not runtime state.
* **Structural difference worth chasing next:** map 288's init script calls
  `0xD65B(area=28)` before anything else; map 289's init does not. Script
  0xD65B is two engine calls — `0x839B(param1)` and
  `0x5C9E(var[base 0x80 + 0xDC02])` — i.e. an area/camera resource set-up
  that only the map-288 path performs. This is the best remaining candidate
  for the missing arrival state, but it was **not** proven, because the engine
  calls cannot be reproduced by a RAM poke.

* The 10-press sequence was delivered in the map-289 arrival state (including
  from inside zone 0xA67B at `0x0E40,0,0x1240`) and `0x0203F216` stayed 0: the
  zone callback is installed but never serviced because the player actor it
  tests for (type `0xF5EB`) does not exist.
* Because the counter never leaves 0, the chest effect remains **unobserved**.
  This is a specific, reproducible arrival blocker (see §8), not a missing
  search.

**Bounds.** A partially entered sequence or a wrong button cannot reach the
`progress_index == 9` branch; the failure branch resets the index to 0. A
ten-press sequence with the last button changed (e.g. B,B) also fails the
`key_pressed == expected[9]` test. These are derived from script 0xB6B2 and are
consistent with the observed null result outside the zone.

**Other systems.** The top-floor passcode is a 4-digit RTC equality check
(1,440 valid times), not a published list. The result password is generated for
an external website. The Sound Test is a 30-coin unlockable. No hidden/debug
menu, no "password" entry screen, and no second button-code table were found in
the script directory or the string bank.

## 7. Validation evidence

**Observed**

* ROM hashes/header; one logo; zeroed header checksum.
* Menu screens (title, options, file select, name, region, difficulty, pause,
  item/weapon/map, basics/explanation).
* Abyss arrival in mGBA (`w14.png`, `amap.png`), map name ABYSS 1F, map ID 288,
  area 28, position from GDB.
* Exact Konami sequence entered in the Abyss entrance; no chest (`code2.png`).
* GameFAQs late-game saves load as `DATA.1 = Django` / `DATA.2 = Hatikan`;
  file-select slot validity is sensitive to header edits.
* **Second pass:** map 288 playable at `(0x05BF,0,0x0F41)` (walking moves
  `x/z`, menus open); map 289's live collision map (EWRAM 0x0202A404) holds
  zone 0xA67B at `x 0x0D00..0x1300, z 0x0F00..0x1400, h 0..32`, containing the
  spawn `(0xE40,0x1240)`; the Konami array `40 40 80 80 20 10 20 10 02 01`
  appears at EWRAM 0x0203F20C after a map-289 load, counter 0 at 0x0203F216;
  keypad shadow 0x03004450 still updates and *every* button produced 0 pixel
  change while the arrival dialogue was up. The "room not drawn" part of this
  observation was wrong: the black frame was the arrival dialogue.
* **Third pass (2026-10-26):** dismissing the arrival dialogue with A reveals a
  fully rendered map-289 room (HUD live, room/camera update) — screenshot
  `/tmp/opencode/boktai3/evidence_map289_room_noplayer.png`; the camera follows
  the room's blue NPC, not a player (`evidence_map289_after_seq.png`). EWRAM
  scan `0x02004000..0x0200D000` finds **no** `type 0xF5EB` actor record in map
  289 (six save-warp positions) while the same scan on a map-288 load finds it
  at `0x02005B9C` with the live player struct at `0x02006500`; the save
  position appears at five EWRAM addresses in map 288 and only in the Stat
  block (`0x0203D8F0`) in map 289. Map 288 spawns the player at an arbitrary
  warp position (`0x0400,0x0200,0x0400` tested), so the second pass's
  "map 288 only works from a specific position" is corrected. The 10-press
  sequence in map 289 leaves `0x0203F216` at 0. PC sampling in the map-289
  state shows the normal main loop and IWRAM audio mixer still running.
  Evidence dumps: `/tmp/opencode/boktai3/d288b.bin`, `d289b.bin`
  (EWRAM+IWRAM).
* Save checksum format reproduced byte-for-byte on both GameFAQs saves:
  logical image, LE-u16 `xor,sum,size,0xFFFF` per block.

**Derived**

* The ten expected masks at 0xEC1689 and script 0x82A6's InitArray call.
* Zone 0xA67B / callback 0xB6B2 / progress index / chest spawn.
* Zone bounds for the hint room from map 289's live collision map (0x0D00..
  0x1300 / 0x0F00..0x1400); the 0x6CFA-file bounds are a different map.
* Save block checksum/layout and byte order.
* The passcode is an RTC-time equality check (strings + guide).

**Inferred**

* The hint room belongs to map 289 (`c05_01`), whose init script calls 0x82A6;
  the zone and the chest spawn are consistent inside it.
* The map-289 hang is a failed in-map arrival setup (door/transition state
  missing), not a corrupt save: the init script completes (mask array present)
  and the inputs are still sampled.

* The map-289 arrival is a failed in-map player spawn, not a corrupt save or a
  hang: the map loads, the init script completes (mask array present), the room
  renders, the main loop and input sampling run — but no player actor (type
  0xF5EB) is created, so control and the zone callback never start.
* The missing step is engine-side and map-specific; the best candidate is the
  area/camera set-up that only map 288's init performs via script 0xD65B
  (engine calls 0x839B / 0x5C9E). Unproven.

## 8. Unknowns

* **Blocker (exact):** entering map 289 without its door transition loads the
  map but never spawns the player actor. Evidence: in a map-289 arrival the
  room renders and script 0x82A6 runs (masks at `0x0203F20C`, progress 0 at
  `0x0203F216`), but EWRAM contains no actor record of type `0xF5EB` (Django's
  zone actor type) at any of six warp positions, the save position is present
  only in the Stat block `0x0203D8F0`, the camera tracks the room's NPC, no
  key changes the screen, and `0x0203F216` stays 0 through the full 10-press
  sequence. The same harness spawns the player normally in map 288 at an
  arbitrary position, so the failure is map-289-specific.
* **Arrival-state patch not isolated.** Fields tested and rejected (no effect
  on player spawn or control): `Scratch+0x18` = 0x0401, `Stat+0x110` = 0x0A5B,
  `Stat+0xF6` = 6, `Stat+0xF8` = 0. What the map-289 arrival lacks is a single
  engine-side step, not a patchable flag among these.
* The chest effect in zone 0xA67B therefore remains **unobserved**.
* Map 288's door/exit to map 289 was not found: 30+ step walks in each free
  direction and the map 0xCD23/0xCD25 zone tiles do not change the map ID, and
  no u16 289 reference exists in map 288's collision data.
* The exact map-289 arrival position expected by the door script is unknown.
* The 4-digit passcode screen was not visited; its validator is derived from
  text + guide, not from an in-game entry.
* The end-game result-password format was not dumped; it is generated for a
  dead website and is not an in-ROM code entry.
* Sound Test unlock was not exercised in-game (30 coins).

## 9. Tooling

* mGBA 0.10.5 (`mgba-qt`), Xvfb :194 + openbox, `xdotool`, `scrot`,
  ImageMagick `import`/`convert`, `gdb-multiarch`.
* `/tmp/opencode/boktai1/drv.py` — window focus/keypress/screenshot driver.
* `/tmp/opencode/boktai1/boksave.py` — 8-byte byte-order conversion and block
  checksum rebuild.
* `/tmp/opencode/boktai1/disasm.py` — container-aware Boktai bytecode
  disassembler (uses the script directory at 0x08E0DA84).
* `/tmp/opencode/boktai1/findzone.py` — MFT collision-map walker + GBA LZ77
  decompressor + zone table search.
* Second pass (`/tmp/opencode/boktai2`): `sav.py` (corrected EEPROM checksum,
  hardware↔logical conversion, slot copy, warp), `mkslot1.py` (build a warped
  slot-1 save), `gstub.py` + `rspd.py` (persistent GDB-stub bridge over a unix
  socket; 0x200-byte max reads), `load.py`/`load2.py` (title → file select →
  DATA.1 loader), `bdis.py` (disassembler), `walk.py`, `cap.py`/`capq.py`
  (SDL/Qt window capture).
* Third pass (`/tmp/opencode/boktai3`): `run.sh` (Xvfb :194 + `mgba-qt -g` +
  `rspd.py` GDB-stub bridge), `load3.py`/`settle.py` (boot → file select →
  DATA.1, then advance the arrival dialogue until the frame is stable),
  `dump.py`/`scan.py`/`actors.py` (EWRAM+IWRAM dumps, actor scan by update
  callback and `type 0xF5EB`), `watch2.py` (GDB-RSP write watchpoint with
  PC/LR capture), `bdis2.py` (disassembler that handles the last script),
  `move.py`/`poke.py`/`sample.py` (walk, poke, PC histogram).
* Public references used for cross-checks: Boktai Hacking Wiki (ROM/RAM maps,
  bytecode, script directory, save checksums, collision map), GameFAQs
  guides/cheats, SolDec opcode documentation.

## Legal note

No ROM, extracted graphics/audio, or copyrighted text is redistributed here.
The report contains addresses, hashes, algorithms, and short quotations needed
for identification and reproduction.
