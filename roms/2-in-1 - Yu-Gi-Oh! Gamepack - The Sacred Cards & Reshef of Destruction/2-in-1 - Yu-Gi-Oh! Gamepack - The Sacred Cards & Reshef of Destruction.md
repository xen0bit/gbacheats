# 2-in-1 Yu-Gi-Oh! Gamepack: The Sacred Cards & Reshef of Destruction (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `2-in-1 - Yu-Gi-Oh! Gamepack - The Sacred Cards & Reshef of Destruction.gba` |
| Size | 33,554,432 bytes (32 MiB / 256 Mbit) |
| Header title | `YUGIOH 2IN1` |
| Game code | `BY2E` |
| Maker | `A4` (Konami) |
| Fixed byte 0xB2 | `0x96` |
| Software version | 0 (`Rev.00`) |
| Complement check | `0xDB` |
| Entry | ARM branch at 0x08000000 → 0x080000C0 |
| MD5 | `b288c64ec50625b6b80bc6730efbf190` |
| SHA-1 | `cfa00b4f8a3f2e6400d4816df6ed1bfebf131120` |
| SHA-256 | `b86546b5c52316d96eb54c3c5365c5eba56ffe9f3c46b6341160ecd1e9cf0688` |
| Build string | `100305_DM2in1_KDEH` at file 0x7940 (first image), `100305_DM7_KDEH` in save data (second image) |

### 1.1 Embedded-image scan (Phase 0)

A full scan for the 156-byte Nintendo logo finds **exactly one** header, at file offset 0
(base `0x08000000`). This is not a normal two-header concatenation. It is a single
32 MiB image with a pack shell and **two code bases**:

| Image | File base | ROM base | Evidence |
|---|---:|---:|---|
| Pack shell + *The Sacred Cards* | `0x0000000` | `0x08000000` | single GBA header; Sacred title/intro; code at 0x080E63xx |
| *Reshef of Destruction* | `0x1000000` | `0x09000000` | code at file 0x10B49xx = ROM 0x090B49xx; literals point to 0x09E1462C |

The second image has **no Nintendo logo and no valid header** at 0x1000000 (the bytes
there are Italian card text). The pack shell at 0x0 boots first, draws the two-logo
selector (white bracket = current choice, Up/Down + A), and either continues the first
image or jumps into the second image at base `0x09000000`. This is why a logo scan finds
one header while both games are complete.

## 2. Executive summary

The 8-digit **card password** terminal is a developer-intended code system and is fully
reversed. It is a **plain table lookup**, not an algorithmic code:

* Input is eight decimal digits (0–9) held as eight byte values, not ASCII.
* Each game half has a flat **8-byte-per-slot table** indexed by internal card ID.
  Slot 0 is unused; card ID 1 is Blue-Eyes White Dragon.
* The terminal walks slots from 0 upward:
  * `0F 0F 0F 0F 0F 0F 0F 0F` = end of table → reject;
  * `0F 0F 0F 0F 0F 0F 0F 0E` = no password for this card → skip;
  * an exact 8-byte digit match → grant that slot's card.
* A second, short table at the end of each game holds **special codes** (money, deck
  capacity, story flags). They use the same 8-digit alphabet and are stored after the
  card-table sentinel so the card loop cannot reach them.

The two halves of this pack are **cross-wired at the card-database level**:

* the **Sacred Cards** half uses the **800-card Reshef-order** table at 0x08EBFB70;
* the **Reshef** half uses the **900-card Sacred-order** table at 0x09E1462C, with the
  100 Reshef-exclusive cards appended as IDs 801–900.

That mismatch yields **eight passwords that are present in the ROM but absent from every
published list** for the card they unlock: the published Reshef password guide marks
these cards "(No password)", and the Sacred list does not contain the cards at all.

Counts:

| Half | Slots (IDs) | Passwords | No-password markers |
|---|---:|---:|---:|
| Sacred-title half (0x08EBFB70) | 801 (0–800) | **795** | 6 (IDs 0, 234, 238, 240, 297, 412) |
| Reshef-title half (0x09E1462C) | 901 (0–900) | **893** | 8 (IDs 0, 832, 833, 834, 866, 884, 885, 887) |

The Reshef terminal charges 1,000 Domino per use; the Sacred terminal is free. The
in-game card-grant of a novel code was **not completed** in this session (see §7.3);
everything up to and including the terminal screen, the fee gate, the complete table,
and the validator was observed/derived.

## 3. How to reproduce

### 3.1 Emulator

```bash
Xvfb :117 -screen 0 1280x960x24 &
DISPLAY=:117 openbox &
DISPLAY=:117 SDL_AUDIODRIVER=dummy mgba -3 <rom>.gba &
W=$(DISPLAY=:117 xdotool search --name mGBA | head -1)
DISPLAY=:117 xdotool windowfocus $W
```

Default mGBA SDL keys used: A=`x`, B=`z`, Start=`Return`, Select=`BackSpace`,
L=`a`, R=`s`, D-pad arrows. Hold keys 100–300 ms.

### 3.2 Boot selector

At the dual-logo screen the white bracket starts on **The Sacred Cards**. `Down` moves
it to **Reshef of Destruction**; `A` boots the highlighted game. Both games are complete
inside the one 32 MiB image.

### 3.3 Menus observed

* Pack selector: two stacked logos, bracket cursor (`shot0.png`, `r3.png`).
* Sacred title: `NEW GAME` / `CONTINUE` (`q3.png`).
* Reshef title: `NEW GAME` / `CONTINUE` (`rf1.png`).
* Reshef title `Game Menu` (when a save exists): `Continue`, `Link Duel`,
  `Card Trade` (`rf8.png`, `rf20.png`).
* In-game pause (both games): `Status`, `Trunk`, `Deck` (`menu1.png`, `rmenu1.png`).
* `Link Duel Menu`: `Trunk`, `Deck 40/40`, `Deck Capacity`, `Deck Cost`, `Start`,
  `Exit` (`menu_link.png`).
* Name entry: 8-row on-screen keyboard, A–Z, a–z, 0–9, punctuation (`q3.png`).

### 3.4 Reaching the password terminal

* **Reshef of Destruction**: Clock Tower Square → south to the cafe → west to the GAME
  shop building → enter → the orange **Password Terminal** is on the right wall.
  Dialogue: "Hello. I am the Password Terminal." → "Would you like to enter a
  password?" → Yes/No (`term3.png`, `term5.png`).
* **The Sacred Cards**: the free terminal is the machine in the Card Shop, which is a
  **world-map** destination (southeast). The city exit is guarded ("This area is off
  limits until the Tournament.") until the intro story is advanced (`sac15.png`).
  To start the tournament: challenge (**R**, not A) the five *stationary* duelists in
  Clock Tower Square — in this English build they are **Yugi, Mai, Bonz (spiky hair),
  Underwoods (green hair) and Tsunami**, per the English GameFAQs walkthrough
  (intensive08, v2.0, §6.1). Note that the Japanese-version guide (nycoolboy, DM7)
  names *Weevil / Mako / Rex* instead; those are the wrong five for this ROM and were
  what the fifth and sixth passes chased. Order in the English guide: Yugi (start
  screen) → left to Mai → down to Bonz → left to Underwoods → up to Tsunami → then
  **left to leave the screen**, where Joey appears and the clock rings 9:00. Full
  sequence and evidence in §6b, fifth/seventh pass.

## 4. Address map

All addresses are ROM addresses; file offset = address − base for the half.
Half 1 base `0x08000000`; half 2 base `0x09000000`.

| Object | ROM address | File offset | Notes |
|---|---:|---:|---|
| Pack entry / shell | `0x08000000` | 0x0 | ARM branch to 0x080000C0 |
| Second image base | `0x09000000` | 0x1000000 | headerless |
| Sacred card table | `0x08EBFB70` | 0xEBFB70 | 8-byte slots, sentinel at 0x08EC14A0 |
| Sacred slot-0 / no-password marker | `0x08EBFB70` | 0xEBFB70 | `0F×7 0E` |
| Sacred table sentinel | `0x08EC14A0` | 0xEC14A0 | `0F×8` |
| Sacred special table | `0x08EC1488` | 0xEC1488 | 25410867, 51404976, then sentinel |
| Sacred search function | `0x080E6350` | 0xE6350 | slot loop |
| Sacred terminal entry | `0x080E63B0` | 0xE63B0 | copies input, dispatches |
| Sacred classify (sentinel/skip) | `0x080E6620` | 0xE6620 | 0=end, 1=skip, 2=compare |
| Sacred 8-byte compare | `0x080E6668` | 0xE6668 | returns 10=match, 11=mismatch |
| Sacred special search | `0x080E6538` | 0xE6538 | base 0x08EC1488 |
| Sacred special effect | `0x080E67A0` | 0xE67A0 | sets bit `index` in 0x02031A58 |
| Sacred validator state | `0x020319E0` | — | `{u16 index; u8 result; u8 digits[8]}` |
| Sacred input buffer | `0x0202F290` | — | eight digit bytes |
| Reshef card table | `0x09E1462C` | 0x1E1462C | 8-byte slots, sentinel at 0x09E1627C |
| Reshef table sentinel | `0x09E1627C` | 0x1E1627C | `0F×8` |
| Reshef special table | `0x09E1625C` | 0x1E1625C | 25232415, 62626514, 98025229, sentinel |
| Reshef search function | `0x090B494C` | 0x10B494C | slot loop |
| Reshef terminal entry | `0x090B4A20` | 0x10B4A20 | copies input, dispatches |
| Reshef classify | `0x090B4AF8` | 0x10B4AF8 | 0=end, 1=skip, 2=compare |
| Reshef 8-byte compare | `0x090B49F4` | 0x10B49F4 | 10=match, 11=mismatch |
| Reshef special search | `0x090B4A98` | 0x10B4A98 | base 0x09E1625C |
| Reshef special effect | `0x090B4B40` | 0x10B4B40 | money / capacity / no-op |
| Reshef terminal digit buffer | `0x02038260` | — | eight digit bytes, copied into the validator |
| Reshef validator state | `0x0203AC20` | — | `{u16 index; u8 result; u8 digits[8]}` (digits at +3) |

Result codes: `10` = accepted, `11` = rejected. On rejection the caller plays sound
`0x39` (57); on a card grant it plays sound `0xC9` (201).

## 5. Algorithm

### 5.1 Card-password search (identical in both halves)

```
search(digits[8], table_base, sentinel=0F*8, skip=0F*7 0E):
    for index = 0, 1, 2, ...:
        entry = table_base[index*8 .. index*8+7]
        if entry == sentinel: return REJECT          # result = 11
        if entry == skip:     continue               # no password for this card
        if entry == digits:   return ACCEPT(index)   # result = 10
```

Reimplemented literally, the ROM agrees with the table on accepted and rejected values:
the sentinel ends the search, the skip marker is transparent, and the comparison is a
byte-for-byte compare of **digit values**, not ASCII.

### 5.2 Grant path

```
on ACCEPT(index):
    f_0809B300(index)       # mark/obtain card
    sound(201)
    f_080AF5F4()
    f_080BD5C4(index, 1)    # add card to the deck/trunk flow
```

### 5.3 Special codes (shared alphabet, separate table)

Sacred half, base 0x08EC1488 (2 entries):

| Index | Code | Effect (derived) |
|---:|---|---|
| 0 | `25410867` | sets bit 0 of flag array 0x02031A58; success sound |
| 1 | `51404976` | sets bit 1 of flag array 0x02031A58; success sound |

These are the codes published for Reshef (boss appearance / Ra Phoenix); in the Sacred
half they only set story-flag bits.

Reshef half, base 0x09E1625C (3 entries):

| Index | Code | Effect (derived) |
|---:|---|---|
| 0 | `25232415` | **no effect** (effect function returns immediately) |
| 1 | `62626514` | adds **50,000 Domino** (`f_09099D1C(50000,0)`) |
| 2 | `98025229` | adds **100 Deck Capacity** (`f_0909455C(100)`) |

The published Sacred utility codes (98025229, 62626514) therefore live in the
**Reshef** half of this pack, and the published Reshef codes (25410867, 51404976) live
in the **Sacred** half. This is the same cross-wiring seen in the card tables.

### 5.4 Rejection model

* Eight digits is the entire alphabet; the UI has no way to enter letters.
* A value not present in the table (e.g. `00000000`, `99999999`) reaches the sentinel
  and returns result 11.
* No-password slots (`0F×7 0E`) are skipped, so a code equal to a gap is rejected.
* The special table is consulted only after the card search fails.

## 6. Tables

### 6.1 Card table shape

* Slot size 8 bytes; each byte is one decimal digit 0–9.
* Slot 0 is always `0F 0F 0F 0F 0F 0F 0F 0E` (unused ID 0).
* Index = internal card ID. Examples verified in the ROM and in the in-game trunk/deck:
  * ID 1 = `89631139` Blue-Eyes White Dragon;
  * ID 2 = `15025844` Mystical Elf;
  * ID 3 = `76184692` Hitotsu-me Giant;
  * ID 13 in the Sacred half = `87557188` The Stern Mystic (Reshef order);
  * ID 13 in the Reshef half = `72842870` Tyhone (Sacred order);
  * ID 104 in the Reshef half = `22026707` Curtain of the Dark Ones (seen in the
    in-game Deck screen, `deck1.png`).

### 6.2 Cross-wired databases

* Sacred-title half: table at 0x08EBFB70 is in **Reshef's** card order (verified against
  the Reshef guide: #13 The Stern Mystic 87557188, #103 Baron of the Fiend Sword
  86325596, #110 Ruklamba 28913279).
* Reshef-title half: table at 0x09E1462C is in **Sacred's** card order for IDs 1–800
  (verified against the Sacred list: #13 Tyhone 72842870, #103 Job-change Mirror
  55337339, #104 Curtain 22026707), then IDs 801–900 hold the 100 Reshef-exclusive
  cards (The Stern Mystic, Baron, etc.).

### 6.3 No-password slots

| Half | IDs with `0F×7 0E` |
|---|---|
| Sacred-title | 0, 234, 238, 240, 297, 412 |
| Reshef-title | 0, 832, 833, 834, 866, 884, 885, 887 |

### 6.4 Unpublished card passwords (Sacred-title half)

The published Reshef password guide (hockeyguy8 v1.02) marks the following cards
`Password: (No password)`. The ROM table at 0x08EBFB70 contains a working 8-digit code
for each, and none of these codes appears in that guide or in the Sacred Cards list:

| ID | Code | Card |
|---:|---|---|
| 110 | `28913279` | Ruklamba the Spirit King |
| 151 | `55908887` | Orgoth the Relentless |
| 216 | `81306586` | Nightmare Penguin |
| 435 | `54285230` | Aeris |
| 445 | `80280944` | Giant Rex |
| 502 | `17679043` | Penguin Torpedo |
| 550 | `43063758` | Last Tusk Mammoth |
| 649 | `80558357` | Command Angel |

These are the primary novel results. They are also absent from the Sacred Cards list
because that game's published list stops at 800 entries and does not contain the
Reshef-order cards.

## 6b. Enumeration

### Space definition

| Quantity | Value |
|---|---|
| Alphabet | 10 symbols (`0`–`9`), stored as byte values 0–9 |
| Length | exactly 8 |
| Representable values | 10^8 = 100,000,000 |
| Card table (Sacred half) | 801 slots, 795 password entries, 6 no-password slots |
| Card table (Reshef half) | 901 slots, 893 password entries, 8 no-password slots |
| Special table (Sacred half) | 2 entries |
| Special table (Reshef half) | 3 entries |
| Checksum | none; the system is a pure table lookup |

### Enumeration method

The complete tables were dumped from the ROM at 0x08EBFB70 (801 × 8 bytes up to the
sentinel at 0x08EC14A0) and 0x09E1462C (901 × 8 bytes up to 0x09E1627C). Every slot was
decoded to an 8-digit decimal string, sentinel and skip markers were classified, and the
result was compared against the two published lists. There are no duplicate passwords
within either table.

### Novel passwords (not in any published list)

The eight codes in §6.4 are the novel set for the Sacred-title half. The strongest
single example is **`28913279` → Ruklamba the Spirit King (ID 110)**: the only published
Reshef password guide explicitly says Ruklamba has no password, and the Sacred Cards
list does not include the card at all.

The Reshef-title half's table also contains four passwords in IDs 801–900 that are not
in the published set (`58551308`, `95956346`, `36996508`, `52121290`); these
are the same merged-database entries seen from the other side. The tenth pass
resolved the four codes to card names through the Reshef half's own name
pointer table — a 901-entry array of 4-byte pointers at file `0x1DCE0E8`
(index 1 → Blue-Eyes, index 3 → Hitotsu-Me Giant), each pointing at a
`$0<English name>$1<French>…` record:

| Code | Index | Card (Reshef name table) |
|---|---:|---|
| `58551308` | 823 | **Spear Cretin** |
| `95956346` | 824 | **Shining Angel** |
| `36996508` | 865 | **Dark Magician** |
| `52121290` | 886 | **Spherous Lady** |

`00423705` (index 806) is Gearfried the Iron Knight (guide typo `00423706`).
None of the four codes appears in the published Reshef password list, so any of
them is a valid novel target; `58551308` → Spear Cretin was chosen for the
terminal test. **All four were entered at the free machine and accepted**
(seventeenth pass, §6b): result `0x0A` with indices 823 / 824 / 865 / 886.

### Bounds proven by rejection

| Input | Expected | Basis |
|---|---|---|
| `00000000` | reject (result 11) | reaches sentinel; not in table |
| `99999999` | reject (result 11) | reaches sentinel; not in table |
| a gap slot value | reject | skip marker then sentinel |
| >8 digits | not enterable | UI has exactly 8 slots |
| letters | not enterable | alphabet is 0–9 only |

The ROM-side rejection path was verified statically (result 11, sound 57). **The
in-game rejection was not captured**: the Reshef terminal refused the session before
code entry because it charges 1,000 Domino and the loaded save had 500, showing
"Sorry, but you don't have enough money." (`term6.png`). That is an observed *fee*
gate, not a code rejection.

### In-game status of the novel code

The terminal itself was reached in Reshef (orange machine, "Hello. I am the Password
Terminal.", Yes/No prompt), but the 1,000-Domino fee blocked entry. The Sacred terminal
is free, but its Card Shop is behind the world-map/tournament gate. The final card
grant could not be captured in this session. This is the one requirement in §0.2 that
remains open; the table, validator, alphabet, and novel codes themselves are complete.

### Second pass, 2026-10-25: fee code re-checked, gate re-observed

A later session re-checked the paid half and the free half from a live save.

* **The fee is not in the validator.** The Reshef terminal entry at `0x090B4A20`
  copies the eight input digits from `0x02038260` into `0x0203AC23`, calls the card
  search, then branches on the result byte at `0x0203AC22`. It contains no money test
  or deduction anywhere. The 1,000-Domino charge is imposed by the shop's event
  script (dialogue) *before* the digit screen, which is why the earlier session saw
  "Sorry, but you don't have enough money." with 500 in hand. Consequence: the fee
  cannot be bypassed through any alternate entry into the same function; there is no
  "free card lookup" path in that half's code.
* Card grant path in this half: result `10` → `f(0x09086BF8)(index)`, sound `0x5F`,
  `f(0x09096364)()`, `f(0x0909C088)(index, 1)`. On a non-card match the special table
  is tried; a special hit runs `0x090B4C14(index)` and, if that returns 0,
  `0x090B4BEC(index)` then `0x090B4B40(index)`.
* **Special tables re-read byte for byte** (file offsets, digit values):
  * Sacred half `0x08EC1488`: `25410867`, `51404976`, then `0F×8`. No money code.
  * Reshef half `0x09E1625C`: `25232415`, `62626514` (50,000 Domino), `98025229`
    (+100 Deck Capacity), then `0F×8`.
  The cross-wiring in §5.3 is therefore confirmed: the free (Sacred) terminal has no
  money code, and the money code lives only in the 1,000-Domino terminal.
* **Free-half gate re-observed.** Booting the Sacred half and walking the save's
  Clock Tower Square, the square exit returns the story guard message
  "This area is off limits until the Tournament!" — the same state recorded in
  `sac15.png`. The card shop (and its free machine) is not reachable until the Battle
  City tournament sequence runs.
* **Save state used.** The available 32 KiB save is the starting state in both halves:
  500 Domino, 1600 Deck Capacity, 40-card starter deck. In the Reshef slot the
  collection list sits at save `0x4DA` and is mirrored in EWRAM at `0x0203813E`
  (sorted u16 card IDs); the live money u32 is at `0x02038278` (read 500). No
  duplicate card exists in the collection, so §5.3's "sell a duplicate" route to
  1,000 Domino is not available without winning at least one duel first.

Blocker summary for the one missing item:

| Half | Terminal | Gate that blocked the grant |
|---|---|---|
| Reshef | GAME shop, `0x090B4A20` | 1,000 Domino charged by the shop script; save has 500; only legitimate income is duels and no duel was completed |
| Sacred | Card Shop (free) | "This area is off limits until the Tournament!" — pre-tournament story gate |

The grant/rejection at the terminal therefore remains **unobserved**; the negative is
bounded to those two gates, not to the validator.

### Third pass, 2026-10-25 (later): in-game grant still not reached

A third pass loaded the only usable Reshef savestate (`/tmp/opencode/ygo2/ygo2.ss1`,
which restores the live save at 500 Domino and a 40-card deck, mirrored in EWRAM
`0x0203813E`). Findings from this pass:

* **Live money re-read: 500 Domino** (`0x02038278`), unchanged for the whole pass.
  No duel was completed and no sale was possible, so the figure never approached 1,000.
* The **GAME shop exterior is reachable** in Domino Plaza (the orange "GAME" building
  with the double glass doors, `screenshots/reshef_game_shop_front.png`), but the shop
  *interior* was not entered: the walkable strip in front of that facade dead-ends
  against a planter/wall, and the doors could not be reached from that screen.
  The route given in §3.4 (square → cafe → west) was walked again and ended at this
  facade without a door transition. The terminal therefore could not be re-used.
* **mGBA 0.10.5 GDB stub, corrected:** *memory* writes do apply. Writing
  `0x12345678` to `0x0203FF00` read back correctly. **Register/PC writes do not apply**
  (`set $r0`/`set $pc` read back garbage), so a debugger-invoked call to the Reshef
  terminal entry `0x090B4A20` is still not possible. This corrects the §7.3 note from
  the second pass, which said memory writes failed.
* **Duelists:** no Neo Ghoul or other duelist could be engaged. The story NPCs in
  Domino Plaza only give dialogue ("Are you a duelist?", "You must be a registered
  duelist", "The tournament is nearly starting"); no Yes/No duel prompt was observed.
  The Kaiba Corp crowd and the roadblock guard ("Kaiba Corporation is beyond here",
  "No entry permitted! Get lost!") block that route.
* The emulator was driven through a GDB stub daemon; frequent interrupts during map
  transitions sometimes left the game in a static state, which further slowed the
  walk. Screen-position tracking and savestate reloads were used, but the session
  budget expired before a duel or the shop interior was reached.

**Status: the grant and the rejection remain unobserved in-game.** The money gate is
still 500 < 1,000, so `28913279` could not be entered at the paid terminal. This is a
bounded negative, not a validator result.

### Fourth pass, 2026-10-25: sale route disproved and the requested grant located

A fourth pass re-loaded `ygo2.sav` plus `/tmp/opencode/ygo2/ygo2.ss1` (`ygo2.ss2` is a
second starting state standing beside the "It's not nine o'clock yet." NPC in the
north square). Live reads again gave **500 Domino** at `0x02038278`. Two results close
the plan the pass was asked to execute:

* **Selling cannot reach 1,000 with this save.** The Trunk list at `0x0203813E`
  (save `0x4DA`, u16 array terminated by `0`) holds **38 cards, all unique** — no
  duplicate ID exists anywhere in the list. The manual's Card Shops page (p.18)
  states verbatim: "You cannot sell a card when you only have one copy in your
  Trunk." With a duplicate-free 38-card Trunk there is therefore no card the counter
  is allowed to buy, so this route cannot raise the 500 figure even if the counter is
  reached. Money remains 500. (The counter itself was not reached in this pass;
  §3.4's square → south → west walk was re-run and ended in the park west of the
  street, not at a shop door.)
* **`28913279` is a Sacred-half password and is not in the table the orange terminal
  searches.** The orange (Reshef) terminal entry `0x090B4A20` calls the search at
  `0x090B494C`, whose table literal at file `0x10B49D0` is **`0x09E1462C`** (901
  entries, sentinel `0x09E1627C` = `0F×8`, skip `0x09E16284` = `0F×7 0E`). Index 110 of
  that table is `89987208`; a byte search of the whole ROM finds `28913279` only once,
  at file `0xEBFEE0` = **Sacred table `0x08EBFB70` + 110×8**. The Sacred validator is
  `0x080E6350` (table literal at `0x080E6394` = `0x08EBFB70`, state `0x020319E0`).
  Consequence: entering `28913279` at the orange terminal must produce result **11**
  (sentinel), not result 10 at index 110. The `{u16 index; u8 result; u8 digits[8]}`
  state at `0x0203AC20` cannot show index 110 for this code, because the code is not in
  that half's table. The only terminal that can grant card 110 is the free Sacred
  machine, which writes its state at `0x020319E0` and remains behind the world-map
  tournament gate.

Navigation note for future passes: the two u16 at `0x0203A97C` / `0x0203A97E` track
movement (they advance ~60 units/s and are reset by screen transitions), but they
clamp at screen edges, so they are camera/screen coordinates rather than a full
room-local player position. The plaza's north square, the south street and the park
west of it were re-walked; no door transition into the GAME shop interior was found
before the session budget expired. The nearest interactable NPC in the park gives a
Duelist-Kingdom story dialogue (ROM string at file `0x1E36637`: "I'm taking the prize
money and buying a boat ... But not this time."); the R button produced no duel
prompt on the square NPCs, matching the third pass. No duel was fought, so no prize
money was earned and the money figure stayed at 500.

### Seventh pass pointer

The seventh pass (§7.3) corrected the roster: the five duelists this build asks for are
the *English* set (Yugi, Mai, Bonz, Underwoods, Tsunami), not the Japanese set the
fifth/sixth passes chased, and it located the guarded city exit. It still did not pass
the gate, so `0x020319E0` remained zero.

**Seventh pass, 2026-10-25 (late): English roster, exit guard located, gate still shut**

Replayed from `/tmp/opencode/ygo7/states/sacred_square_gate.ss` (copy in
`/tmp/opencode/ygo8/states/`) with a fresh mGBA 0.10.5 + GDB stub.

* **Input fix (method).** mGBA's SDL window ignores synthetic `xdotool key --window`
  events. Every key must go through XTEST to the focused window
  (`xdotool windowfocus <win>; xdotool keydown/keyup <key>`). Confirmed by reading
  `KEYINPUT` (`0x04000130`) while holding a key: Right → `0x03ef`, Start → `0x03f7`.
  Passes five and six pressed keys with `--window`, so part of their "nothing
  happened" evidence is an input-delivery artifact, not game behaviour.
* **R-challenge works from the savestate.** A four-direction probe (turn in place with
  a 45 ms tap, then **R**) reproduces refusals on the opening screen, including Yugi's
  exact published line: "It's going to start soon." / "You should get lost in the town
  before nine." (`screenshots/sacred_yugi_refusal_seventh.png`). Also captured:
  "It's not nine o'clock yet…", "Hehehe, the Tournament starts at nine. You should pay
  attention to what people tell you.", "Hey, ease up. The Tournament hasn't started
  yet." No refusal wrote any byte in `0x02031A58` (32 bytes, all zero afterwards) or in
  `0x02020000–0x0202FFFF`.
* **The guarded exit is the north/north-west edge, not every edge.** Walking into it
  prints "This area is off limits until the Tournament."
  (`screenshots/sacred_square_exit_guard_seventh.png`), reproduced from several cells,
  including with the use key. Forcing past it lands on the blank static grey screen
  (mean brightness 88, identical frame-to-frame, D-pad and A ignored, pause menu
  still opens) that the fifth pass saw at the north alley — a null/dead room, not a
  world-map transition.
* **Map orientation found by walking.** The screen below the start square is the
  Kaiba Corporation frontage ("Kaiba Corporation … No entry permitted here."), so the
  "left → Mai, down → Bonz" directions in the English guide are relative to the clock
  screen the cutscene leaves you on, and the surrounding 3×2 block is laid out
  differently than the flat 5×5 ASCII map in the guide suggests. Two adjacent screens
  were swept with a 5×5 × 4-direction R probe; neither produced Mai (blonde,
  "Whoa, slow down, baby.") nor Bonz ("I don't like these bright places").
* **Mai reached — the blocker was walking distance.** The first left-screen sweeps
  moved only 2–5 tiles, less than the 15-tile screen width, so they never left the
  start screen. Holding **Left for 5 s** (a full screen) and re-probing found Mai
  Valentine: "Whoa, slow down, baby." / "I'll take you on if the opportunity arises." /
  "See you." — the published English refusal, reproduced in-game with working input.
  This confirms the guide's `left → Mai` step and shows the earlier "no Mai" results
  were a movement-distance bug in the harness, not the game.
* **Bonz not reached.** Two full-screen moves down from Mai's screen (the guide's
  "head down to Bonz") hit only bystander lines ("Hehehe, the Tournament starts at
  nine…", "Sure, we wait… the time comes…"). The Clay-tower map is a 5×5 block of
  screens, so the remaining three need the same full-screen crossing with a probe at
  each area; that is the concrete next step.
* **Where it stopped.** ~3 h of play, five full probe sweeps. The failing step is now
  narrowed to *Bonz → Underwoods → Tsunami*; the 9:00 bell never rang, the world map
  never opened, and the Card Shop was never entered. Yugi's and Mai's refusals are
  both reproduced with this build (`sacred_yugi_refusal_seventh.png`).

**RAM at stop** (GDB stub, `0x020319E0` and collection):

| Address | Value | Meaning |
|---|---|---|
| `0x020319E0` | `00×12` | Sacred validator state, never invoked |
| `0x0202F290` | `00×8` | Sacred digit buffer, empty |
| `0x02031A58` | `00×32` | story-flag window, empty even after refusals |
| `0x0203813E` | 38 u16 IDs, `0x0150,0x0152,0x0189,0x018F,…` | collection; `0x006E` (110) absent |
| `0x0203AC20` | `00×12` | Reshef validator state, never invoked either |

Screenshots added: `sacred_yugi_refusal_seventh.png`,
`sacred_mai_refusal_seventh.png`, `sacred_square_exit_guard_seventh.png`,
`sacred_west_screen_bystander_seventh.png`.

### Eighth pass, 2026-10-25 (night): all five refusals reproduced with portraits,
bell still silent

This pass fixed the capture and RAM tooling and reproduced **all five English-roster
refusals in one session**, then failed to obtain the 9:00 bell.

**Tooling corrections (these invalidate some earlier "black screen" readings).**

* *Capture.* mGBA's SDL canvas on Xvfb is a **DirectColor/GLX visual**; `import -window`
  and `xwd`-style grabs of that window return an all-black 720×480 image (mean 0.00)
  even while the game is visibly running. Fixed by reading the **root** window with
  `XGetImage` (ctypes → `libX11`) and cropping the mGBA window rectangle from
  `xdotool getwindowgeometry`. Every frame in this pass (mean ≈ 187 on the plaza) came
  from that path. Earlier passes that reported "black/frozen" frames should be re-checked
  with this method.
* *Audio.* Without `SDL_AUDIODRIVER=dummy`, mGBA fails to open ALSA "default" and the
  **core thread stays parked at ~0 % CPU** — the window never draws and the emulator is
  effectively frozen. With the dummy driver the same ROM/savestate runs at full speed.
  A black window plus a stalled core is therefore an *environment* artefact, not game
  behaviour.
* *RAM.* mGBA's GDB stub (`-g`, port 2345) is single-client per process and the port was
  already held by another session's emulator; a second attach hangs. RAM was instead
  read through mGBA's **command-line debugger** (`-d`) driven over a pty:
  `r/1|2|4 0xADDR` reads, `save N` / `load N` write/read `game.ssN` checkpoints, and a
  pty `^C` breaks into the prompt. This needs no network port and survives other
  sessions' `pkill -x mgba` if the binary is copied under a unique name (`mgba9`).
* *Input.* Re-confirmed with `KEYINPUT` (`0x04000130`) on the debugger read path:
  idle `0x03FF`, **Right `0x03EF`**, **Start `0x03F7`** (XTEST to the focused window).

**All five refusals, same session, each with the duelist's portrait and the published
refusal shape.**

| Duelist | Screen where challenged | Observed text | Shot |
|---|---|---|---|
| Yugi | opening screen, adjacent to the right | "It's not nine o'clock yet, … I should be going, kid." | `sacred_yugi_refusal_eighth.png` |
| Mai | clock/fountain screen, one screen left | "Whoa, slow down, baby." / "I'll take you on if the opportunity arises." / "See you." | `sacred_mai_refusal_eighth.png` |
| Bonz | café-tables screen, **below** the clock | "Kekeke, check the time." / "Pay attention to the rules or be disqualified." | `sacred_bonz_refusal_eighth.png` |
| Underwoods (Weevil) | shop-street screen, **left** of Bonz | "The Tournament hasn't even started." / "…I'll feast on you the next time we meet." | `sacred_underwoods_refusal_eighth.png` |
| Tsunami (Mako) | bank/NW screen, **up** from Underwoods | "Wait, wait. It's not time yet." / "We'll meet again somewhere in Battle City." | `sacred_tsunami_refusal_eighth.png` |

Method that works: a **45 ms** direction tap turns in place without stepping, then **R**
(`s`). Longer taps (80 ms+) move the player off the adjacent tile and the challenge is
lost. Entering an area, the area's duelist is usually one or two tiles away, not
adjacent; the reliable order is to walk a short step toward the visible duelist and
re-probe. R also fires on ordinary duelists/bystanders ("You shouldn't be so hasty.",
"It's not nine o'clock yet, kid.", "Yeah, I think you'd be a perfect opponent… but it's
not nine o'clock"), so only a **portrait** dialogue identifies a roster duelist.

**The bell did not ring.** With all five challenged, four separate walk-outs from the
clock/fountain screen (5 s each, N/E/S/W, each producing a normal screen transition),
a re-entry to the clock screen, and a 45 s idle wait there produced **no chime, no Joey
appearance and no Kaiba cutscene**. The world map never opened and the Card Shop was
never entered. This is the same wall as the fifth, sixth and seventh passes, now with
all five refusals positively observed rather than inferred — so the blocker is *not*
"which duelists" and *not* input delivery.

**RAM at stop** (debugger reads):

| Address | Value | Meaning |
|---|---|---|
| `0x020319E0` | `00×12` | Sacred validator state, still never invoked |
| `0x0202F290` | `00×8` | Sacred digit buffer, empty |
| `0x02031A58` | `00×32` | story-flag window, all zero |
| `0x0203813E` | 44 u16, `0x00C3,0x0150,0x0152,0x0189,…` | collection; `0x006E` (110) absent |
| `0x0203A97C` | camera/scene pair, changes with every screen | position proxy only |

**Story-flag negative (bounded).** An A/B dump of `0x02030000–0x02031800` (6 KiB) taken
before the first challenge and after the fifth challenge session compared **byte for
byte identical**, and a second A/B over `0x0203A000–0x0203A600` likewise showed no
difference. Caveat: the checkpoints were loaded back through the debugger's `load`, and
load timing could not be proven exact, so this is recorded as *no story counter found in
those two windows*, not as proof that none exists. The practical implication is that the
five "met" flags are not in the obvious EWRAM neighbourhood of `0x02031A58`.

**Where it stopped.** Everything up to and including the fifth refusal is reproducible;
the clock chime / tournament unlock is not. No `28913279` grant and no `00000000`
rejection were produced, because the free machine in the Card Shop is still behind that
gate.



### Tenth pass, 2026-10-25 (late night): a Reshef duel actually starts, but is not won

The tenth pass attacked the money gate from the Reshef half, where a fresh
`NEW GAME` starts at **500 Domino** and duels are not story-gated. It got a duel
to start and exercised its combat engine, but did not win it inside the session
budget, so the 1,000-Domino fee, the `58551308` grant and the `00000000`
rejection are **still unobserved**.

**Corrected live addresses (new game, Reshef half).** The Reshef starting state
does not use the `0x02038xxx` mirror quoted in earlier passes. Verified by reading
through the `-d` debugger and by decoding `save N` savestates offline (the PNG
contains a `gbAs` chunk; zlib-decompressing it yields a 0x61000-byte state whose
**EWRAM is at offset 0x21000**, 0x40000 bytes):

| Object | Address | Observed value |
|---|---|---|
| Money (u32) | `0x0202F2A8` | 500 before and after every duel attempt |
| Deck Capacity (u32) | `0x0202F0FC` | 1600 |
| Player LP (u16) | `0x02031728` | 8000 → 7950 → 7550 → 7400 → 7350 → 7050 → 6750 → 6450 |
| Opponent LP (u16) | `0x0203172A` | 8000 → 7900 |
| Reshef validator state | `0x0203AC20` | `00×12` — never invoked |

The `0x0203813E` collection mirror of the earlier passes reads `00` in this new
game; the only card list that materialises is built during the duel (seen at
`0x0202E2FC`/`0x0202E300` while duelling) and is zero in the city.

**Challenge and duel start (this is new).** In Domino Plaza, a 45 ms direction
tap to face a standalone NPC followed by **R** produced the acceptance line
"I'd love to take on a duel!" and then the ante screen (the Trunk list, with
*Details / Use as Ante / Exit*). Trying to ante a card we own only once answers
"At one-of-a-kind card can't be made an ante."; choosing *Exit* and confirming
"Okay to exit without choosing an ante card?" starts the duel anyway. The duel
opens with "It's my turn.", both players at **8000 LP**, **35-card decks** and a
5-card hand. Screenshot: `screenshots/reshef_duel_tenth.png`.

**Duel-engine facts learned (all observed).**

* One **Normal Summon per turn**. Selecting a hand card with **A** picks it up and
  moves the cursor to the zone row; **A** again places it. Summoned monsters are
  placed face-down in attack position.
* Level 5+ monsters answer **"A single tribute is required."** and cannot be
  placed without a tribute. Doma The Angel (1600/1400), Leogun (1750/1500) and
  Peacock (1700/1500) are all in this class; Lightning Conger (350/750, level 3),
  Jinzo #7 (500/400, level 2), Genin (500/900, level 3), Magician of Faith
  (300/400), Winged Cleaver (700/700, level 2) are summonable.
* On a just-summoned monster, **A** opens the Command Menu
  *Attack / Defend / Tribute / Effect*; *Attack* moves the cursor to a target and
  **A** resolves the battle. This flow was used once successfully (Conger attacked
  a set monster and lost 150 LP; a 400-DEF defender blocked a 300-ATK attacker and
  dealt 100 LP to the opponent).
* **B** on a hand card opens the Sub-Menu *Details / Discard / Turn end*; **B** on
  a field card cancels back to the hand. **L** shows ATK/DEF, **R** shows the
  opponent's hand size.
* The opponent's AI summons/attacks on its own; its face-up monsters carry an
  **E** ("already acted") mark during our turn. With a weak board it grinds LP
  directly, which is what the LP trace above shows.

**Why it was not won.** The starter deck's playable monsters top out around
700 ATK while the level-5 beaters need tributes, and the one-summon-per-turn rule
plus the tribute-selection UI (the field cursor cannot reliably be returned to a
monster after the turn ends) made the ~8,000-LP grind longer than the remaining
budget. The duel was left at 6450 vs 7900 LP; money never moved off 500. Loading
the pre-duel savestate restores the city at 500 Domino, which is the state used
for the address readings above.

### Eleventh pass, 2026-10-25 (late): deterministic duel replay; the turn-1 main phase still cannot be driven

This pass first repaired two tooling errors of the tenth pass, because both change
what a "duel attempt" means:

1. **F1–F10 do not load savestates in this build.** `Shift+F1`…`Shift+F10` *save*
   (`game.ss1`… appear next to the ROM), but plain `F1`/`F5` do nothing, and the
   `-d` debugger has no save/load command at all (its `help` lists only
   `r/1..r/4`, `w/1..w/4`, break/watch). So every "reload the turn state and replay"
   in the tenth pass silently continued the *live* state. A reliable reload is to
   restart the emulator with `-t <state>`; that is exact and repeatable (the same
   key sequence then produces the same picture and the same RAM at every step),
   which is what the table below uses.
2. **The duel text can be read exactly.** OCR on this 240×160 screen is hopeless,
   but the dialog font is a 1-bit bitmap font, so segmenting the text band on blank
   columns and identifying glyphs by bitmap signature decodes any message without
   guessing (`font.py`). That is how the turn banners below were read.

**Duel flow, deterministic replay from `game.ss7`** (turn 1 of a Domino Plaza duel;
8000 LP each, 500 Domino, Conger already on our field from the tenth pass):

| Step | Input | Screen text | RAM |
|---|---|---|---|
| 0 | – | `It's my turn.` | hand @`0x02031612` = 5; LP `0x02031728`/`0x0203172A` = 8000/8000 |
| 1 | A | `It's gg's turn.` | `0x0203172A` 8000 → **7650** (= 8000 − Conger's 350 ATK) |
| 2 | A | (field, no text) | hand 5 → **6** (draw) |
| 3… | A ×20 (1.3 s and 0.5 s gaps) | no text, no change | hand 6; our LP 8000 → 7950 once, then frozen |

`gg` is the *player* name typed at `NEW GAME` in the tenth pass, so the banner order
means the CPU speaks first (`It's my turn.`) and the player's turn is `It's gg's turn.`
— i.e. the savestate is taken on the CPU's (skipped) turn, and the draw in step 2 is
the player's draw. After the draw the game is clearly waiting for the player (the PC
sits in the VBlank/IME wait loop at `0x08098188`–`0x08098190` and the frame counter
advances), but it ignores **A**, **B**, the D-pad, **Start** and **Select**; only
**L** and **R** still act (they toggle ATK/DEF and the opponent-hand overlays, ~460
and ~15,500 changed pixels). The same freeze is reproduced from a fresh
`-t game.ss7` restart, so it is not state drift.

**New RAM map for the duel (all observed).**

| Object | Address | Layout |
|---|---|---|
| Hand size | `0x02031612` | u16 count (5 at duel start, 6 after the player's draw) |
| Hand cards | `0x02031614` | u16 card IDs; round 1 = `0x019a, 0x018b, 0x0261, 0x02b2, 0x01e4`, + `0x0121` after the draw |
| Deck (in play) | `0x020315C0` | 40 u16 card IDs |
| Deck (menu copy) | `0x0202F11A` | 40 u16 card IDs; count `0x28` at `0x0202F118` |
| Card-instance pool | `0x02031390` | 8-byte records `[card id u16][0][status u16][0]`; observed statuses `0x0200` (start), `0x1000` (in hand), `0x1200` (field) |
| Card-data record | `0x02031350` | `[id u16][ATK u16][DEF u16][LP-ish u16]…`; Conger = `0x02A2`, 350/750 (agrees with the tenth pass) |
| Player LP | `0x02031728` | u16 (8000 → 7950 when the CPU attacked an empty board) |
| Second LP/display value | `0x0203172A` | u16; 8000 → 7650 on the first turn transition |

**Three attempts, best margin −50 LP.** Each attempt restarts `-t game.ss7` and then
presses only A (attempt A: 20×1.3 s; attempt B: 20×0.5 s; attempt C: 20 mixed
A/D-pad presses):

| Attempt | LP trace (us / `0x0203172A`) | End | Money |
|---|---|---|---|
| A | 8000/8000 → 7950/7650 → flat | 7950/7650 | 500 |
| B | 8000/8000 → 8000/7650 → 7950/7650 → flat | 7950/7650 | 500 |
| C | 8000/8000 → 8000/7650 → flat | 8000/7650 | 500 |

So the best result is **−50 LP** (one CPU direct attack); the opponent is never
damaged by us in these runs and no card is ever played, because the player's main
phase does not accept input. `0x0202F2A8` stayed **500** in every attempt, the
validator state `0x0203AC20` stayed `00×12`, and the `0x0203813E` collection mirror
stayed all zero. **`58551308` and `00000000` remain unobserved in-game.**

### Twelfth pass, 2026-10-25: the duel **is** drivable on a clean emulator — played to a win

The eleventh pass's conclusion ("the player's main phase takes no input") is a
**tooling artifact**, and this pass retracts it. The test was repeated with the
plain SDL emulator and nothing else:

* `/usr/games/mgba` 0.10.5 (SDL), `-3 -t turn1.ss`, **no `-d`, no GDB stub, no
  RSP server, no pty wrapper** — only `Xvfb :117` + `openbox`.
* Input only through XTEST into the focused window (`xdotool windowactivate`,
  `keydown`, sleep, `keyup`). No debugger writes of any kind.
* RAM read only from **savestates**: `Shift+F<slot>` writes a PNG whose `gbAs`
  chunk zlib-decompresses to the state; EWRAM is at `0x21000`. LP, money, hand
  and card IDs below all come from those files, decoded offline.

With that stack every control works (`x`=A, `z`=B, `Return`=Start, `a`=L,
`s`=R, arrows=D-pad). The rule behind the eleventh pass's "dead" main phase is
narrower than "input is ignored":

| Situation | Behaviour |
|---|---|
| A on your monster that already acted this turn (shows `E`) | **no-op** — this is the state the eleventh pass mistook for a freeze |
| A on an empty zone / empty enemy zone | no-op |
| A on a hand card | picks the card up, cursor moves to a field zone |
| A with a menu/target/text open | confirms |
| B on a card | Sub-Menu `Details / Discard / Turn end`; B also cancels |
| During the CPU turn | A only advances its messages; L/R overlays still toggle |

Also corrected: **key repeat**. A 150 ms hold moves the hand cursor **two** slots
in this menu; ≤70 ms moves exactly one. The eleventh pass's 150 ms presses
therefore also skipped cards.

**Full win, recorded step by step** (fresh `-t turn1.ss`; LP = us / opponent from
`0x02031728` / `0x0203172A`, money from `0x0202F2A8`):

| Action | LP | Note |
|---|---|---|
| start | 8000 / 8000 | hand 5, Conger (350/750) on our field |
| A ×4 (CPU turn 1) | 8000 / 7650 | CPU's Mechanical Spider (400 ATK) attacks Conger (750 DEF) and dies |
| Conger → A → Command Menu → Right → **Tribute** | 8000 / 7650 | the sacrifice must be made **first**: selecting a ★5 card in the hand only answers "A single tribute is required." and then stalls |
| hand → Leogun → A, A, A | 8000 / 7650 | Leogun (1750/1550) is now placeable and is summoned |
| Leogun attacks | 8000 / **6300** | 1750 vs 400 ATK → 1350 battle damage |
| (CPU) | 7900 / 6300 | our Magician of Faith is destroyed |
| Leogun attacks | 7900 / **4950** | −1350 |
| Jinzo #7 (500) attacks directly | 7900 / **4450** | −500 |
| Genin (800) summoned, attacks | 7900 / **3850** | −600 |
| (CPU) | 7900 / 3650 | its attacker dies |
| Leogun attacks directly | 7900 / **1900** | −1750 |
| Winged Cleaver (700) summoned, attacks | 7900 / **1200** | −700 |
| Leogun attacks | 7900 / **0** | "The opponent is out of LP!" |

Screens: `reshef_duel_out_of_lp_clean.png`, `reshef_duel_prize_76.png`.

**The money gate is economic, not mechanical.** Winning pays **76 Domino**
(`76 Domino was obtained.`; `0x0202F2A8` 500 → **576**). The 1,000-Domino terminal
fee therefore still needs roughly six more wins; the Trunk still holds no
duplicate to sell. So `58551308` (Reshef index 823, Spear Cretin) and the
`00000000` rejection remain **unobserved in-game**, now with a clean route to
them (win duels with the tribute-summon line below) rather than an input bug.

**Fastest observed duel line** (the AI sets its summons in defence, so each turn
is mostly board clearing): get any monster out, then tribute it for **Leogun
(1750)**; clear the AI's set monster with the weakest attacker, then attack
directly with the strongest. Two to three attackers per turn is the practical
maximum (one Normal Summon per turn, one attack per monster).

### Thirteenth pass, 2026-10-25: a second clean win from the 576 state — and the prize is **not** a fixed 76

This pass re-attacked the money gate with the twelfth pass's clean stack
(`/tmp/opencode/ygo13`, plain `/usr/games/mgba -3 -t`, XTEST only, no `-d`/GDB/RSP)
and **won a second duel**, but could not start a third.

**Ante flow (confirmed twice, exact inputs).** Facing the standalone NPC with a
45 ms direction tap, **R** opens the duel; the ante screen is the normal `Trunk`
screen with the sub-menu *Details / Use as Ante / Exit*. `A` on a card opens the
sub-menu (a second `A` on *Details* opens the card view; `B` returns). Choosing
*Exit* only closes the sub-menu; the duel starts from **`B` (cancel) on the Trunk
list**, which raises `Is it okay to exit without choosing an ante card?` with the
cursor on **No** — press **Down → A (Yes)** and the duel begins. `A` there
answers No and returns to the Trunk.

**Duel UI mechanics proven this pass (all clean XTEST).**

| Action | Input | Result |
|---|---|---|
| dismiss the turn banner | `A` | banner closes; D-pad is ignored while it is up |
| pick up a hand card | `A` on the card | cursor jumps to the field zone row |
| place it | `A` again | monster is set; shows `facedown` in the status bar |
| open the monster menu | `A` on the placed monster | `Attack / Defend / Tribute / Effect` |
| attack | `A` (Attack) then `A` | target cursor lands on the enemy's set monster; a second `A` resolves the battle |
| direct attack | `A` (Attack) then `A` with the enemy field empty | resolves against LP (−ATK; observed 1700 and 700) |
| tribute | `A` (menu) → `Right` (Tribute) → `A` | sacrifices the monster; then select the 5★ card in the hand and place it |
| end the turn | `B` on an **empty** field zone → `Down` → `A` | `Details / Discard / Turn end`; also shows both decks and LPs |
| `B` on a hand card | — | does nothing in this build (the twelfth-pass note is wrong) |
| `Start` in the duel | — | does nothing |
| key timing | 80–100 ms holds + 0.5–0.7 s gaps | presses below ~70 ms are sometimes dropped; use 100 ms |

**The win (state `evidence_money576.ss`, money 576).** Opening hand was
`Armed Ninja (300/300)`, `Droll Bird (600/500)`, `Sparks` (spell),
`Peacock (1700/1500, ★5)`, `Star Boy (550/500)` — i.e. a **different hand from
the twelfth pass**, so the shuffle is not fixed. Line used: set Droll Bird
(600) → its attack destroyed a set `Shadow Specter (500)` for 100 damage;
next turn **tribute Droll Bird → Peacock (1700)**; then clear the AI's set
monster with any spare attacker and send Peacock (1700) or a drawn
`Phantom Dewan (700/600)` direct. Every CPU turn sets one defensive monster, so
the practical pattern is *clear with the weakest, hit directly with the
strongest*.

LP trace (`0x02031728` / `0x0203172A`, read from `Shift+F` savestates):

| Point | Us / CPU |
|---|---|
| duel start (`game.ss1`) | 7900 / 8000 |
| after first exchanges | 7400 / 7900 |
| Peacock direct | 7400 / 6200 |
| Dewan direct | 7400 / 5500 |
| CPU counter-attack | 7300 / 5200 |
| Peacock + Dewan | 7300 / 4200 → 2500 |
| next turn | 7000 / 1800 → 400 |
| final Dewan direct | **7000 / 0** |

**Prize: 60 Domino, not 76.** After `Duel victory!` the game prints
`Your deck capacity increased by 3!` (1273 → 1276) and then
`60 Domino was obtained.` — `0x0202F2A8` **576 → 636** (decoded offline from
`evidence_money636.ss`). So the twelfth pass's 76 was this opponent's *other*
payout, or the prize varies per duel; **the per-win income cannot be assumed to
be 76**, and 636 + 6×60 = 996 still misses 1,000.

**Why the loop stopped.** The defeated NPC despawned. After the post-duel line
(`Dagnabbit! You tricked me!`) the remaining Domino Plaza / back-street NPCs only
give bystander and story lines (`Where's a wimpy duelist when you need one...`,
`KaibaCorp chartered an entire express train.`, the Kaiba `Duel Express`
cutscene). ~200 probe steps (R and A, 45 ms taps, ante-screen OCR on the
`Trunk / DECK CAPACITY` header) produced **no further ante screen**, so no third
duel could be started in this area. The GAME shop interior was also not reached
from the plaza side (the glass facade with the green `Game shop` sign is a wall;
the green `EXIT` door in the back street is behind a railing).

Consequence: at 636 Domino the 1,000-fee terminal is still shut, so `58551308`
(Reshef index 823, Spear Cretin) and the `00000000` rejection remain
**unobserved in-game** — unchanged from the twelfth pass, now with the duel
itself fully mechanised.

### Fourteenth pass, 2026-10-26: A-talk **and** R-challenge to all five in one
session; the "met" state is per-screen, not a counter; bell still silent

The thirteenth pass proved the duel, not the gate. This pass attacked the gate the
way the English walkthrough says it is passed — **talk with A, then challenge with
R** — and settled where the "met" state lives.

**Method (clean stack, no debugger).** `/tmp/opencode/ygo14`: plain
`/usr/games/mgba -3 -t <state>` on `:117` with `SDL_AUDIODRIVER=dummy`, input only
through XTEST into the focused window, screenshots through the root-window
`XGetImage` path, RAM only from `Shift+F<n>` savestates (`gbAs` → zlib → EWRAM at
state offset `0x21000`). No `-d`, no GDB, no reload between the five talks.

**Actor table (new, and the key to repeatable navigation).** EWRAM holds a
32-byte-per-record actor table at **`0x0203A978`**:

| Field | Offset | Notes |
|---|---|---|
| `u16 id` | +0x00 | `0x19` = player; `0xffff` = empty slot |
| `u16 flags` | +0x02 | animation/state |
| `u16 x`, `u16 y` | +0x04/+0x06 | world coordinates inside one screen (x≈0–118, y≈0–96) |
| `u32 script` | +0x10 | 12-byte script record in the `0x09E2xxxx`–`0x09E3xxxx` story area |

The player is record 0 at `0x0203A978`, so its position pair is exactly the
"scene" pair already quoted in §6b: **x at `0x0203A97C`, y at `0x0203A97E`**.
Keys move one axis each: `Right` = x+, `Left` = x−, `Up` = y−, `Down` = y+.
Walking off an edge wraps to the next screen (x 0↔≈112–118, y 0↔≈96) while keeping
a few units — treating this pair as a live position makes short-step navigation and
fixed-NPC finding deterministic. Each screen has one **stationary** actor (the
story duelist) plus 3–7 wandering actors; chasing the *stationary* record, standing
2–8 units away and facing along the isometric screen direction
(`sdx = dx−dy`, `sdy = (dx+dy)/2`) reproduces the talk every time.

**All five, A then R, one continuous session** (screenshots
`sacred_*_fourteenth.png` in `screenshots/`):

| Order | Duelist | Screen | A-talk | R-challenge |
|---:|---|---|---|---|
| 1 | Yugi | Clock Tower Square (start) | "We should go win some cards, too." | "It's not nine o'clock yet… I should be going, too." |
| 2 | Mai | one screen left | "You were with Joey Wheeler earlier, weren't you? … I'm taking down Wheeler and Yugi. Fufufu…" | "Whoa, slow down, baby." / "I'll take you on if the opportunity arises." / "See you." |
| 3 | Bonz | one screen down | "Hihihi, this Tournament will be short… my ghost deck will spell doom…" | "Hihihi, I hate bright places like this." / "I'll be waiting for you somewhere dark…" |
| 4 | Underwoods (Weevil) | one screen left | "You were chumming around with Yugi, weren't you? You tell Yugi this: I'm going to beat you but good this time." | "Hyohyo… Aren't you impatient? The Tournament hasn't even started. I'll feast on you the next time we meet." |
| 5 | Tsunami (Mako) | up (north) from Underwoods, lane x≈91–96 | "I lost against Yugi and them at Duel Kingdom. But not this time. I'm taking the prize money and buying a boat. I won't let anyone get in my way." | same text on the R press (the refusal page set repeats) |

After the refusal the duelist's record walks to `y = 96` and disappears; the
**stationary record is gone from the next snapshot**. That is the only visible
"met" consequence.

**EWRAM A/B around Mai's A-talk and R-challenge (live, no reload).** Three full
EWRAM dumps (before / after A / after R; kept as `ev_mai_A.bin`, `ev_mai_B.bin`,
`ev_mai_C.bin`), compared by region:

| Region | A-talk changed bytes | R-challenge | control (6 s idle) |
|---|---:|---:|---:|
| `0x02000000–0x0201FFFF` (BG/tilemap) | 14,282 | 2,246 | 491 |
| **`0x02020000–0x02035FFF` (state)** | **0** | **0** | **0** |
| `0x02036000–0x020371FF` (sprite/OAM shadow) | 111 | 78 | 98 |
| **`0x02037200–0x0203A7FF` (state)** | **0** | **0** | **0** |
| `0x0203A800–0x0203BFFF` (actor table + sprite shadow) | 3,056 | 2,952 | 2,954 |
| **`0x0203C000–0x0203FFFF` (state)** | **0** | **0** | **0** |

The tilemap figure is the dialogue box being drawn; the sprite/actor figures are
the same as the idle control. **No "met" counter or flag changes anywhere in EWRAM**
— in particular the known flag array `0x02031A58` stays `00 × 32`, the Sacred
validator state `0x020319E0` stays `00 × 12`, and the collection
`0x0203813E` keeps the same 44 IDs (no `0x006E`). A launch-vs-after-five-talks
diff gives the same answer: 0 bytes changed in `0x02020000–0x02036000` and
`0x02037200–0x0203A800`.

**The bell did not ring.** After all five: exits from Clock Tower Square in four
directions (1.2 s walks; transitions observed — Left→Mai's screen, Right/Up→square,
Down→the Kaiba Corporation street), a 5 s left walk out of Underwoods' screen, and
a talk to the KaibaCorp sign NPC ("Kaiba Corporation is beyond here.") produced
no chime, no Joey, no Kaiba cutscene, no story dialogue and no world map. Input
kept working and the actor tables kept loading normally, so this is a game
condition, not a hang.

**Card Shop is enterable pre-tournament, but shut.** Walking north from the
Underwoods screen at lane x≈91–96 enters the **Card Shop interior** (screenshot
`sacred_cardshop_interior_fourteenth.png`): the free Sacred password machine is on
the left wall, but the shopkeeper says "Hello, welcome. I haven't opened the shop
yet." The room's walkable band at the counter is x 35–77, y 23–29; the machine is
outside it, and A only produces shop lines. So `28913279` (accept → index 110) and
`00000000` (reject → 11) remain **unobserved in-game**.

**Where this leaves the gate.** The requirement is not "which duelists" (all five
A+R are now reproduced) and not input; it is a tournament-unlock condition that is
**not stored in EWRAM** at all. The next test is script-side: the five actor
scripts (0x09E2B0E8/0x09E2B100/0x09E2B118 on the square; 0x09E24158… on Mai's
screen; 0x09E33948… on Bonz's; 0x09E364C4… on Underwoods'; 0x09E3A5CC… on
Tsunami's) and the clock script that gates `0x020319E0` should be read for the
exact condition, and the guide's **order** (Yugi→Mai→Bonz→Underwoods→Tsunami→leave
left) should be replayed once in that order, since the fourteenth pass replayed the
talks in a different order.

Tooling/artifacts: `/tmp/opencode/ygo14/` — `x.py` (XTEST + root `XGetImage`
capture), `ss.py` (`gbAs` decoder, EWRAM at `0x21000`), `nav2.py` (actor-table
reader, world-coordinate chase, screen wrap), `probe.py` (bitset-font OCR of the
dialogue band), `spam.py`, `route.py`, `hunt.py`, `track.py`; states
`evidence_five_talks.ss`, `ev_mai_A/B/C.bin`.

### Fifteenth pass, 2026-10-26: the talks write **nothing** — the bell is a
**map-event**, not a flag/counter

This pass stopped treating the bell as a hidden "met" counter and tested the two
remaining possibilities directly: (a) that some flag/counter really is set, and
(b) that the five talk scripts contain the trigger. Neither is true. The unlock
is a **map/event binding in ROM**, and the five talks cannot affect it.

**1. The talks leave the whole state region byte-identical.** Comparing the
pre-talk state (`ygo14/base.ss`: Clock Tower Square, player `(8,48)`, Yugi id
`0x0001` at `(16,40)` with pages `0x09E2AFEC`/`0x09E2AFF8`) against the
after-all-five state (`ygo14/evidence_five_talks.ss`) gives:

| Range | Changed bytes |
|---|---:|
| `0x02020000–0x0202F000` (state) | **0** |
| `0x0202F000–0x02031000` (save/money/deck block) | **0** |
| `0x02031000–0x02036000` (validator, flag arrays) | **0** |
| `0x02036000–0x02037200` (sprite/OAM shadow) | 127 |
| `0x02037200–0x0203A800` (state) | **0** |
| `0x0203A800–0x0203C000` (actor table + OAM) | 3158 |
| `0x0203C000–0x02040000` (state) | 1 (`0x0203C06C`, unrelated) |

In particular the story-flag array `0x020319A0`, the event-flag array
`0x02031A58`, the Sacred validator state `0x020319E0` and the collection at
`0x0203813E` are all unchanged (all zero / same 44 IDs). **No "met" state exists
anywhere in EWRAM and none can be stored by the talks**, so no talk *order* can
matter — the fourteenth pass's order was not the reason the bell stayed silent.

**2. The five talk pages are terminal.** The dialogue VM (interpreter at
`0x080E2DC4`, state `+0x10` = script base, `+0x14`/`+0x18` = branch-taken /
branch-not-taken page, selector `+0x1e`) reads a page as three `u32`:
`{text base, branch if 0, branch if 1}`. Every A-talk and R-challenge page in
the five blocks is a **straight line**: both branch words are the shared empty
page `0x09EB05B8` (base `0x09EAFDA5`).

| Page | Text base | Branch 0 / 1 | First English line |
|---|---|---|---|
| `0x09E2AFEC` (Yugi id 1, A) | `0x09E26C22` | `0x09EB05B8` / `0x09EB05B8` | "We should go win some cards, too." |
| `0x09E2AFF8` (Yugi, R) | `0x09E26D42` | `0x09EB05B8` / `0x09EB05B8` | "It's not nine o'clock yet… I should be going, too." |
| `0x09E2B0E8` / `0x09E2B0F4` (NPC `0x53`) | `0x09E284B2` / `0x09E287E8` | end / end | "Whoops… The Tournament's about to start." / "It's going to start soon…" |
| `0x09E2B100` / `0x09E2B10C` (NPC `0x2A`) | `0x09E289A2` / `0x09E28CD4` | end / end | "I heard some duelists are playing with their lives." / "It's not the time yet." |
| `0x09E2B118` / `0x09E2B124` (NPC `0x38`) | `0x09E28E2D` / `0x09E291F3` | end / end | "You know Pegasus got beat…" / "Huh? It's not nine yet." |
| `0x09E24158` (Mai block) | `0x09E1EBE6` | end / end | "Whoa, slow down, baby…" |
| `0x09E33948` (Bonz block) | `0x09E31160` | end / end | "Hihihi, this Tournament… ghost deck…" |
| `0x09E364C4` (Underwood block) | `0x09E33A38` | end / end | "You were chumming around with Yugi…" |
| `0x09E3A5CC` (Mako block) | `0x09E365D8` | end / end | "I lost against Yugi and them at Duel Kingdom…" |

There is **no flag-write, no counter and no conditional branch** in any of the
nine pages. (Control codes in the text stream are presentation only: `#4 nn` =
speaker/portrait id, `#0`/`#1` = line breaks, `$0`–`$6` = language sections,
`^n` = layout/portrait, `|n` = deck/LP/fade subcommands.)

**3. The only five-way flag test in the whole VM is dead code and irrelevant.**
`0x080E430C` is a `^`-subcommand handler whose sub-op 0 tests story flags
`0x52,0x53,0x54,0x55,0x56` (`0x080E5C98`, array `0x020319A0`, mask table
`0x08EBFB68` = `80 40 20 10 08 04 02 01`) and sets the branch byte if **all
five** are set. It is **unreachable**: the `^` jump table at `0x080E31AC` has 11
entries but the dispatch at `0x080E319C` is `cmp r0,#9; bls`, so only indices
0–9 can be taken. It was nevertheless tested live: a savestate with those five
bits forced (`0x3E` at `0x020319AA`, confirmed still `3E` after several map
loads) produces the **same** Yugi refusal ("It's not nine o'clock yet…",
`screenshots` in `/tmp/opencode/ygo15/shots/yR_Up.png`), so the five bits do not
gate the duel or the bell.

**4. Where the bell actually lives: a map-event slot.** Each map record in the
actor-table bank is a 20-byte-row actor list terminated by `0xFFFF`, with two
event-script words at fixed offsets `+0x140` / `+0x144`. The Clock Tower Square
has a **tournament-start variant** at `0x09A4F350` (pointed to by the screen
table entry at `0x09E1E258`) whose `+0x140` is **`0x09E2AF80`** — the bell
scene:

```
0x09E2AF80 base 0x09E24428  "Hey, look at that. Everyone's here already."
0x09E2AF8C base 0x09E24450  "Heh, look at all the tourists…"
0x09E2AF98 base 0x09E246F2  "Fellow duelists, welcome to Battle City!
                             Let me explain the Tournament…"
0x09E2AFA4 base 0x09E24727  "…eight winning duelists… six locator cards…"
0x09E2AFB0 base 0x09E25BCC  "It's… Finally starting."
0x09E2AFBC base 0x09E25BFA  branch: 0 → 0x09E2AFC8 / 1 → 0x09E2AFD4
0x09E2AFC8 base 0x09E25F97  "I'll do my best, too."
0x09E2AFD4 base 0x09E2651E  "Hey, don't be so down on yourself, #5…"
0x09E2AFE0 base 0x09E26997  "Yeah, okay… All right, I'm off…"
```

The record also parks the story actors off-screen (`id 1` Yugi at
`x = 0xFFF0` = −16, `y = 40`; `id 4` at −16) and has a second actor list at
`+0x148` for the walk-in crowd. **The square record that the game actually
loads pre-tournament is `0x09A4EDE8`** (actor table read from `base.ss`), and
its `+0x140` / `+0x144` are both **`0`** — no event. Neighbouring records show
the chapter ladder: `0x09A4E948 +0x144 = 0x09E24104` (the new-game Kaiba
cutscene), `0x09A4F350 +0x140 = 0x09E2AF80` (the 9:00 scene), `0x09A4F6A8
+0x140 = 0x09E2B148` ("You took out the Ghouls?…"), the rest `0x09EB05AC`
(empty page).

**Exact condition.** The bell is not gated by a flag, a counter or a talk order.
It is the `+0x140` map-event of the Clock Tower Square record `0x09A4F350`,
i.e. it plays when the game has loaded that **chapter-2 square variant**. The
pre-tournament square (`0x09A4EDE8`) has that slot zero, and no amount of
A-talk/R-challenge changes which record is loaded — the talks are terminal
pages and leave EWRAM bit-identical. The remaining unknown is the code that
advances the square's chapter (the record index), which is a map-load/story
transition outside the five actor scripts; it is not reachable from the talk
data.

Tooling/artifacts: `/tmp/opencode/ygo15/` — `pngstate.py` (decode/patch/re-encode
the PNG `gbAs` savestate), plus copies of `x.py`/`ss.py`/`nav2.py`/`probe.py`;
`full.dis` (24 MB objdump sweep used for the flag/opcode call-site census);
patched states `t_flags.ss`, `t_base_flags.ss`.

### Sixteenth pass, 2026-10-26: the square selector found, the bell **played**,
and the password grant **proven in the terminal UI**

Three things changed this pass. (a) The map/chapter selector is a plain
`(group, index)` pair in EWRAM, so the square variant is now addressable.
(b) Forced to the chapter-2 variant at map-entry time, the 9:00 bell scene plays
in full — screenshots of Kaiba's "Fellow duelists, welcome to Battle City!" and
"Scatter throughout Battle City!" are in `screenshots/sacred_bell_*_sixteenth.png`.
(c) With the shop open, the orange Password Terminal was used through its normal
keypad: a card-110 password was **accepted** (result `0x0A`, index `0x6E`, card
screen "Hero of the East") and `00000000` was **rejected** (result `0x0B`).

**1. How the square record is selected.** The map loader reads two halfwords at
`0x0203A970`:

| EWRAM | Width | Meaning |
|---|---|---|
| `0x0203A970` | u16 | **group** (0–56), index into the 57-entry group directory at ROM `0x09E1E5E8` |
| `0x0203A972` | u16 | **index within the group**; record = `group_dir[group][index]` (u32 pointer array, record stride **`0x1AC`**) |
| `0x0203A974` | u16 | entry/placement argument (third word, usually 0) |

Record layout (confirmed by both file and EWRAM dump): **`+0x00..+0x13F`** up to
16 story-actor entries of **20 bytes** (`id u16, flags u16, x s16, y s16,
pageA u32, pageB u32, u32`) terminated by `0xFFFF`; **`+0x140`/`+0x144`** the two
map-event script pointers; **`+0x148`** a five-entry *spawn table*
(`id 0x19` = player, one slot per entry direction). Layout/tileset for a screen is
selected by *group* only: `0x09E16A60[group]` is copied to `0x0203A970+0x260`.

The Clock Tower Square therefore has two records in **group 1**:

| Screen | Record | `+0x140` event | Actor at `+0x00` |
|---|---|---|---|
| `(group 1, index 0)` — walk-in square | `0x09A4EE4C` | `0x09EB05AC` (empty page) | Yugi id 1 `(16,40)` |
| `(group 1, index 3)` — 9:00 square | `0x09A4F350` | **`0x09E2AF80`** (the bell) | Yugi id 1 `(–16,40)` + ids 4/3 |

This corrects the fifteenth pass in two places. `0x09A4EDE8` is **not** a record:
it is `0x09A4ECA0 + 0x148`, i.e. the *spawn table* of the group-0/index-5 record
`0x09A4ECA0` (a different screen). And the state `base.ss` is already on
**`(1,3)`**, the event-bearing square — the 9:00 event was loaded but not run,
which is why the bell "never rang" while the record looked right.

**2. Map entry, and why the bell does not re-fire.** Screen changes go through
the tiny setter at **`0x090B03D8`** (`strh r0,[0x0203A970]; strh r1,[+2];
strh r2,[+4]`). Its caller **`0x090B2060`** scans a 196-entry, 24-byte-per-entry
transition table at **`0x09184304`**:

```
+0x00 u16 screen id A       +0x14 u16 target index
+0x02 u16 screen id B       +0x16 u16 target group
+0x04 ..+0x12  8 x u16 required story-flag ids (0xFFFF = unused)
```

The square `(1,0)` appears in three entries with flag lists (`0x5E`; `0x10`;
`0x19`) and the walk from the neighbouring fountain screen is one of them. **No
entry in the 196-entry table mentions `(1,3)` at all**, so the 9:00 square is only
reachable by a scripted write, never by a walked transition. That is the real
"chapter" gate: a story script calls the setter with `(1,3)` when the 9:00
condition is met, and normal walking always resolves the square as `(1,0)`.

After the setter, the map-enter routine **`0x090B08FC`** runs: it calls the actor
loader (`0x090B07B0` → `0x090B03E8`, which writes `record+0x140 → 0x0203ABA8`
and the actors into `0x0203A978`) and then calls **`0x090B2154`** with the event
pointer, which executes the 3-word script records inline. So the event fires on
*entry*, not per frame; restoring `base.ss` (already inside the square) never
re-runs it.

**3. The bell scene, observed.** With `(1,3)` selected at the moment of map entry
the event ran in full (every page OCR'd):

> "Hey, look at that. Everyone's here already." … "Heh, look at all the tough
> duelists!" … "Fellow duelists, welcome to Battle City!" … "Let me explain the
> Tournament rules, … The Tournament takes place throughout Domino City … The
> loser must turn over one rare card to the victor … eight winning duelists will
> enter the final round … gathered six locator cards … The Tournament commences
> at nine a.m. sharp. Now, all you duelists… Scatter throughout Battle City!"

Then the crowd walk-in: "It's… Finally starting." / "Joey, I think you should be
careful yourself." / "All right, I'm off." / "Both of you, don't lose until the
finals." Screenshots: `sacred_bell_welcome_sixteenth.png`,
`sacred_bell_scatter_sixteenth.png`, `sacred_bell_finale_sixteenth.png`.

**Testing convenience (state patch, not a cheat code).** The only patch was the
one selector word: the game was paused at the `set_screen` write
(`watch/w 0x0203A972` on the mGBA debugger, hit PC `0x090B03E0`) and
`0x0203A972` was set from `0` to `3` before the map-enter ran. That is exactly
the value the story warp writes; nothing else in EWRAM was changed and the
dialogue/grant below were produced by normal UI input afterwards. The same patch
can be made in a savestate with `pngstate.py` (`patch <src> <dst> 0x0203A972 3`,
i.e. state offset `0x21000 + 0x3A972`) — but a savestate alone cannot force the
map re-entry, so the load step needs a transition or the debugger.

**4. The 9:00 scene sets no flags.** After the scene the story/event windows are
still zero and the collection is unchanged:

| Address | After bell |
|---|---|
| `0x020319A0` (story flags) | `00 × 48` |
| `0x02031A58` (event flags) | `00 × 32` |
| `0x020319E0` (first-image validator) | `00 × 12` |

So the scene is presentation; the state that opens the world is written by the
scripted warp, not by the map event.

**5. The Password Terminal, used through its normal keypad.** The shop interior
with the orange terminal is **`(group 35, index 0)`** (record `0x09A5CE54`;
actor `0x28` at `(60,33)` carries page `0x09E839F0`, English text
"Please enter the 8-digit password."). The keypad is a 3×4 grid
(`7 8 9 / 4 5 6 / 1 2 3 / 0 OK`) with `L`/`R` to move the digit position; A on a
digit writes the current position and advances, A on `OK` submits. The entered
digits land in **`0x02038260`**; the validator state is **`0x0203AC20`** =
`{u16 index; u8 result; u8 digits[8]}`.

| Entered | `0x0203AC20` | Meaning |
|---|---|---|
| `89987208` | `6E 00 0A 08 09 09 08 07 02 00 08` | **index 110, result 10 = ACCEPT** |
| `28913279` | `03 00 0B 02 08 09 01 03 02 07 09` | result 11 = reject (this table) |
| `00000000` | `03 00 0B 00 00 00 00 00 00 00 00` | result 11 = reject |

On `89987208` the game left the keypad and opened the card screen
**"Hero of the East"** (Type Warrior / Earth / Cost 103, "Your Duelist Level is
below the Cost. This can't be put in the Deck.") —
`sacred_card110_hero_of_the_east_sixteenth.png`; the keypad with the valid code is
`sacred_password_89987208_sixteenth.png`, and `00000000` is
`sacred_password_00000000_sixteenth.png`.

**Which code is right for which table.** Slot 110 of the two card tables:

| Table | Slot 110 |
|---|---|
| `0x08EBFB70` (first image) | `28913279` |
| `0x09E1462C` (second image) | **`89987208`** |

The running game (the image with the Battle City bell and the Card Shop) is the
**second** image and uses the second table, so `28913279` is a *different*
half's code and is rejected here — exactly as the fourth pass predicted.

**Half-label correction.** String evidence puts the games the other way round
from §1.1: `Reshef`/`Millennium` text occurs **only in the first image**
(`0x08EC9CE8…`), while `Battle City`/`locator` text occurs **only in the second**
(`0x09E2xxxx…`). The Sacred Cards is therefore the **second** image, and the
validator the task calls "Sacred" (`0x020319E0`) belongs to the **first** image's
terminal code (`0x080E6350`, buffer `0x0202F290`); the Sacred terminal code
(`0x090B494C`) writes `0x0203AC20`/`0x02038260`. The card data in §4 is correct;
only the half names attached to the two validator addresses were swapped.

**Not proven.** The trunk listing sampled after the grant (`Trunk 1829/1600
40/40`) did not show ID `0x006E` between 105 and 123, and no EWRAM u16 list gained
`0x006E`; the grant presentation and the validator are recorded, the storage slot
is not. The exact story script that performs the `(1,3)` warp was not located —
only the transition table that *cannot* reach it.

Tooling/artifacts: `/tmp/opencode/ygo16/` — `pngstate.py`, `x.py`/`ss.py`/
`nav2.py`/`probe.py`, `dbgctl2.py` (mGBA `-d` command-line debugger over a pty:
`watch/w`, `w/2`, `w/r`, `c`), states `game.ss3` (post-grant), `game.ss5`
(rolling), screenshots in `shots/`.

### Seventeenth pass, 2026-10-26: four novel Reshef-order passwords granted at the free machine

The sixteenth pass proved the free terminal works but only with the published
card-110 code. This pass entered the four "other half" codes that §6b listed as
novel (`58551308`, `95956346`, `36996508`, `52121290`) and **all four were
accepted by the free machine**. The swapped-label question is thereby answered
without a table patch: the running image's table `0x09E1462C` really does carry
the Reshef-exclusive tail at IDs 801–900.

**Method (normal UI, no RAM writes).** From `ev_post_grant.ss` (group 35,
index 0; player `(73,24)`) the terminal is actor `0x29` at `(80,24)`, not
`0x28`; its page `0x09E83AB0` resolves to `0x09E838F1` = `$0Please enter the
8-digit#0password.` (`0x28` at `(60,33)` is the card dealer whose first line is
`$0Welcome.` — the sixteenth pass had the two actors swapped). Keypad state is
readable, which makes entry deterministic:

| Addr | Meaning |
|---|---|
| `0x02018800` | keypad struct (`+0` slot index 0–8, `+1` current digit 0–10 where 10 = OK, `+4` cursor animation) |
| `0x02038260` | 8-byte digit buffer (values 0–9), the same buffer the validator reads |
| `0x0203AC20` | validator result `{u16 index; u8 result; u8 digits[8]}` |

L/R (`a`/`s`) move the slot index, the d-pad moves the digit cursor
(`7 8 9 / 4 5 6 / 1 2 3 / 0 OK`), A writes the highlighted digit into the
current slot and advances. Reading `0x02018800` from a savestate after each
press removes all guesswork; a scripted entry of all four codes succeeded with
zero mis-lands (`/tmp/opencode/ygo17/kp.py`).

**Results — every one `result 10`, read from `0x0203AC20`.**

| Entered | `0x0203AC20` | Index | Card (name table) | Screenshot |
|---|---|---|---|---|
| `58551308` | `37 03 0A 05 08 05 05 01 03 00 08` | **823** (`0x0337`) | **Spear Cretin** | `sacred_password_58551308_seventeenth.png`, `sacred_card823_spear_cretin_seventeenth.png` |
| `95956346` | `38 03 0A 09 05 09 05 06 03 04 06` | **824** (`0x0338`) | **Shining Angel** | `/tmp/opencode/ygo17/shots/kp_95956346.png`, `card_95956346.png` |
| `36996508` | `61 03 0A 03 06 09 09 06 05 00 08` | **865** (`0x0361`) | **Dark Magician** | `sacred_card865_dark_magician_seventeenth.png` |
| `52121290` | `76 03 0A 05 02 01 02 01 02 09 00` | **886** (`0x0376`) | **Spherous Lady** | `/tmp/opencode/ygo17/shots/kp_52121290.png`, `card_52121290.png` |

Each accept closed the keypad and opened the card screen; the header showed the
name ("Spear Cretin", "Shining Angel", "Dark Magician", "Spherous Lady"). The
four indices are exactly the ROM slots found offline, and the names come from
the 901-entry name-pointer array at file `0x1DCE0E8` (`0x09DCE0E8`) indexed by
the same ID — index 110 returns "Hero of the East", which matches the
sixteenth pass's observed grant, so the array is aligned with the running table.

**Card storage (new).** After the four grants, the live collection/deck working
arrays hold the new IDs, so the sixteenth pass's "storage slot not found" is
answered for at least the first grant: a u16 list at `0x0203813E` ended
`… 0x02B5, 0x0066, 0x0337`, and `0x0338`/`0x0361`/`0x0376` appear as u16s at
`0x020390F4`, `0x02039144`, `0x0203916E` (mirrored at `0x02037818+`). The
`0x0203813E` window only exposed `0x0337`, so the grant is stored, not just
displayed; which of those arrays is the persistent slot is still open.

**Bounds note.** All four codes are absent from the published Sacred Cards and
Reshef password lists (the Reshef guide marks these four cards "No password"),
so each is a novel grant. `36996508` → Dark Magician is the strongest single
proof: a famous card the published lists give no code for, accepted at the
free machine with index `0x0361` in RAM and the card art/name on screen.

## 7. Validation evidence

### 7.1 Observed

* One GBA header at 0x0; selector boots either game (`r3.png`, `r4.png`, `rf1.png`).
* Sacred title, Reshef title, name entry, pause menu, trunk, deck, link-duel menu
  (`q3.png`, `menu1.png`, `deck1.png`, `menu_link.png`).
* Reshef GAME shop interior with the orange Password Terminal on the right wall
  (`shop2.png`).
* Terminal dialogue and Yes/No prompt (`term3.png`, `term5.png`).
* Fee gate: `Sorry, but you don't have enough money.` (`term6.png`).
* Card IDs/names in the in-game Deck screen match the ROM table (`deck1.png`:
  ID 104 Curtain of the Dark Ones, ID 105 Tomozaurus).
* **The 9:00 bell scene, played in full** after forcing the square selector to
  `(group 1, index 3)` at map entry: "Fellow duelists, welcome to Battle City!",
  the tournament rules, "Scatter throughout Battle City!", and the crowd walk-in
  (`screenshots/sacred_bell_{welcome,scatter,finale}_sixteenth.png`).
* **Password Terminal keypad used end-to-end** in the shop at `(group 35,
  index 0)`: `89987208` → validator `0x0203AC20` = `6E 00 0A` (index 110,
  result 10) and the card screen **"Hero of the East"**
  (`sacred_password_89987208_sixteenth.png`,
  `sacred_card110_hero_of_the_east_sixteenth.png`).
* **Rejections observed**: `28913279` → `03 00 0B …28913279`
  (`sacred_password_28913279_sixteenth.png`) and `00000000` →
  `03 00 0B 00×8` (`sacred_password_00000000_sixteenth.png`), both result 11.
* **Four unpublished passwords granted at the free machine (seventeenth pass)**,
  each with validator `0x0203AC20` = index + result `0x0A` and the card screen:
  `58551308` → index `0x0337` "Spear Cretin"
  (`sacred_password_58551308_seventeenth.png`,
  `sacred_card823_spear_cretin_seventeenth.png`), `95956346` → `0x0338`
  "Shining Angel", `36996508` → `0x0361` **"Dark Magician"**
  (`sacred_card865_dark_magician_seventeenth.png`), `52121290` → `0x0376`
  "Spherous Lady".

### 7.2 Derived

* Table bases, sizes, sentinels, skip markers, and every password.
* The 8-digit digit-value comparison and the 10/11 result codes.
* The special-code effects (50,000 Domino, +100 Deck Capacity, no-op).
* The cross-wired card orders between the two halves.
* The save-format checksum field: 16-bit little-endian sum of bytes at slot+0x110 ..
  slot+0x9CB, stored at slot+0x9CC (verified on four save files; note: this is a
  constant `0x112E` in the tested saves, so the game may use a different validity
  test; see §8).

### 7.3 Not completed

* ~~In-game acceptance of a novel password and screenshot of the received card.~~
  **Done (sixteenth pass)** for card 110 / code `89987208` at the second image's
  validator `0x0203AC20`; the card screen "Hero of the East" was observed. The
  task's `28913279` at `0x020319E0` is the *other* image's table and validator.
  **Done again, with unpublished codes (seventeenth pass)**: `58551308` (823
  Spear Cretin), `95956346` (824 Shining Angel), `36996508` (865 Dark Magician)
  and `52121290` (886 Spherous Lady) all returned result `0x0A` at
  `0x0203AC20` and opened their card screens. The §0.2 requirement is now met
  for four codes that appear in no published list.
* ~~In-game rejection of an out-of-range 8-digit value at the terminal.~~
  **Done (sixteenth pass)**: `00000000` → result `0x0B` and `28913279` →
  result `0x0B` at `0x0203AC20`.

**Status after the seventeenth pass (2026-10-26).** The free Password Terminal in
the group-35 shop accepts unpublished codes: `58551308` (823 Spear Cretin),
`95956346` (824 Shining Angel), `36996508` (865 Dark Magician) and `52121290`
(886 Spherous Lady) all produced `0x0203AC20` result `0x0A` with the matching
index and card screen. This confirms the Reshef-exclusive tail (IDs 801–900)
lives in the running image's table `0x09E1462C`, and resolves the sixteenth
pass's storage question for the first grant (`0x0337` appears in the live u16
collection arrays). The only open items are the scripted `(1,3)` warp and the
full save-format collection write path.

**Status after the sixteenth pass (2026-10-26).** The square selector is EWRAM
`(group, index)` at `0x0203A970`/`0x0203A972` (group directory ROM `0x09E1E5E8`,
record stride `0x1AC`); the 9:00 square is `(1,3) = 0x09A4F350`, whose `+0x140`
event `0x09E2AF80` was **executed and observed**. Walking never selects `(1,3)`
(the 196-entry transition table at `0x09184304` has no `(1,3)` destination and
gates entries on up to eight story flags), so the square variant is a scripted
warp, not a walked transition. With the shop reachable, the terminal accepted a
card-110 password and rejected two others. Remaining: the exact story script that
writes `(1,3)`, and where the granted card is stored (the sampled trunk listing
did not show ID `0x006E`).

**Status after the fifteenth pass (2026-10-26) — superseded in part.** The bell is now located
script-side and the "met flag" theory is dead. The five A-talk/R-challenge pages
(`0x09E2AFEC`/`0x09E2AFF8`, `0x09E2B0E8`/`0x09E2B0F4`, `0x09E2B100`/`0x09E2B10C`,
`0x09E2B118`/`0x09E2B124`, `0x09E24158`, `0x09E33948`, `0x09E364C4`,
`0x09E3A5CC`) are **terminal** three-word records — both branch words are the
empty page `0x09EB05B8` — so they write no flag and cannot branch on one.
Confirmed live: the pre-talk square state (`base.ss`) and the after-five state
(`evidence_five_talks.ss`) differ by **0 bytes** in `0x02020000–0x02036000`,
`0x02037200–0x0203A800` and `0x0203C000–0x0203FFFF`; the flag arrays
`0x020319A0`/`0x02031A58` stay zero. The one five-way test in the dialogue VM
(`0x080E430C` sub-op 0 → flags `0x52`–`0x56` in `0x020319A0`) is unreachable
(`^` sub-table dispatch is `cmp #9` over 11 entries) and, when forced in a
savestate, still yields the "It's not nine o'clock yet" refusal. The 9:00 scene
is the **`+0x140` map-event** (`0x09E2AF80`, bases `0x09E24428` → `0x09E26997`,
Kaiba's "Fellow duelists, welcome to Battle City!") of the square variant
`0x09A4F350`; the pre-tournament square record that is actually loaded,
`0x09A4EDE8`, has that slot **`0`**. So the gate is a **map/chapter switch**,
not a talk flag or counter. `28913279` (accept → index 110) and `00000000`
(reject → 11) therefore remain **unobserved in-game**, still with no way to open
the Card Shop's counter pre-tournament.

**Status after the fourteenth pass (2026-10-26).** The Sacred half's five-duelist
step is now done the way the English walkthrough describes it: **A-talk then
R-challenge to Yugi, Mai, Bonz, Underwoods and Tsunami in one continuous clean
session**, all ten dialogues captured (`screenshots/sacred_*_fourteenth.png`,
§6b fourteenth pass). A repeatable navigation primitive was found — the 32-byte
actor table at `0x0203A978`, with the player at record 0 (`x 0x0203A97C`,
`y 0x0203A97E`) and one stationary story duelist per screen. Two results follow:

* **The "met" state is not a counter.** Full EWRAM A/B dumps around Mai's A-talk
  and R-challenge change **0 bytes** in `0x02020000–0x02035FFF`,
  `0x02037200–0x0203A7FF` and `0x0203C000–0x0203FFFF` (the only diffs are the
  dialogue-box tilemap and the sprite/OAM shadow, identical to a 6 s idle
  control). The only visible consequence of a completed talk is that the duelist's
  actor record walks to `y = 96` and leaves the screen.
* **The 9:00 bell still did not ring**, with all five A+R done: four-direction
  exits from Clock Tower Square, a 5 s left walk out of Underwoods' screen, and a
  talk to the KaibaCorp NPC produced no chime/Joey/Kaiba cutscene, and the world
  map never opened. The Card Shop **is** enterable pre-tournament, but the
  shopkeeper says "I haven't opened the shop yet" and its free password machine is
  outside the counter's walkable band. So `28913279` (accept → index 110) and
  `00000000` (reject → 11) remain **unobserved in-game**.

Remaining work is script-side: read the five actor scripts
(`0x09E2B0E8`/`0x09E2B100`/`0x09E2B118`, `0x09E24158…`, `0x09E33948…`,
`0x09E364C4…`, `0x09E3A5CC…`) and the clock gate for the unlock condition, and
replay the guide's exact order (Yugi→Mai→Bonz→Underwoods→Tsunami→leave left), which
the fourteenth pass did not follow.

**Status after the thirteenth pass (2026-10-25).** A **second** real duel win is
now proven end to end on the clean stack: `Duel victory!` → `Your deck capacity
increased by 3!` → `60 Domino was obtained.` → `0x0202F2A8` **576 → 636**
(`evidence_money636.ss`). The duel line, ante flow and turn-end input are all
mechanised (see §6b, thirteenth pass). The remaining blocker is **finding
duelists**: the beaten NPC despawned and ~200 R/A probes over the Domino Plaza
and back-street screens produced no new ante screen, so the money stopped at
636 < 1,000. `58551308` (Spear Cretin) and `00000000` are therefore still
unobserved in-game; the terminal itself was not reached either (the plaza-side
`Game shop` glass facade and the back-street green door are not enterable from
the tiles walked).

**Tenth pass (2026-10-25, late night): a Reshef duel now provably starts, but was
not won.** The challenge (45 ms tap + **R**) is accepted ("I'd love to take on a
duel!"), the ante screen appears, and the duel runs at 8000 LP / 35-card decks,
with one Normal Summon per turn, tribute rules for 5+ star monsters, and working
attack/defend/turn-end commands. LP moved 8000 → 6450 (us) against 8000 → 7900
(opponent) before the session ended; `0x0202F2A8` stayed **500** throughout.
Because no duel was won and the Trunk has no duplicate to sell, the 1,000-Domino
fee still blocks the terminal, so the `58551308` grant (Reshef index 823,
"Spear Cretin") and the `00000000` rejection remain unobserved. Full detail and
corrected live addresses (`0x0202F2A8` money, `0x0202F0FC` deck capacity,
`0x02031728/0x0203172A` LP) in §6b, tenth pass.

Blocker: Reshef charges 1,000 Domino (loaded save had 500); Sacred's free terminal is
behind the world-map story gate. Attempts to patch the save's 500 field were rejected
by the game's save validation, the shared `.sav` between the two halves made the
`Continue` state unreliable, and a debugger-invoked call to the validator was not
possible because mGBA 0.10.5's GDB stub did not apply memory/PC writes in this setup
(the writes read back as zero). This is reported as a bounded negative, not as success.

**Eleventh pass (2026-10-25, late): duel replay made deterministic, still no win.**
The tenth pass's "reload and retry" never actually reloaded (F1–F10 are not load keys
in this build; only `Shift+Fx` saves, and the debugger has no save/load command), so
this pass rebuilt the method: restart mGBA with `-t <state>` for an exact reset, and
decode the bitmap font instead of OCR-ing it. From `game.ss7` the turn banners now
read `It's my turn.` → `It's gg's turn.` with a draw (hand 5 → 6) and `0x0203172A`
moving 8000 → 7650; the hand/card-instance/deck arrays were mapped (see §6b). Past
that point the player's main phase takes no input at all — A, B, D-pad, Start and
Select are all ignored while L/R still toggle their overlays — so no card is played
and no attack is made. Three attempts gave a best margin of **−50 LP** (8000 → 7950,
opponent unreduced); `0x0202F2A8` stayed **500**, `0x0203AC20` stayed zero. The
1,000-Domino fee therefore still blocks the terminal and both the `58551308` grant
(Reshef index 823, Spear Cretin) and the `00000000` rejection remain **unobserved**.

**Twelfth pass (2026-10-25): the duel is drivable and was won on a clean emulator.**
Plain mGBA 0.10.5 SDL (no debugger/stub) plus XTEST input replays the eleventh pass's
own savestate and plays it to the end: summons, tribute summon, attacks and turn end
all work, and the opponent goes 8000 → 0 at 7900 LP for us ("The opponent is out of
LP!"). The eleventh pass's "main phase ignores input" was the **no-op on an
already-acted monster** (the `E` mark) plus 150 ms holds double-stepping the cursor.
The win pays only **76 Domino** (500 → 576), so the 1,000-Domino fee needs about six
more wins; `58551308` and `00000000` remain unobserved in-game. See §6b, twelfth pass.

Fourth pass (2026-10-25): the two gates are now explained rather than merely observed.
The starting save's Trunk has **38 cards and no duplicate** (`0x0203813E`, save
`0x4DA`), and the manual (p.18) forbids selling a card when only one copy is held, so
the 500 -> 1,000 step is impossible by sale. Separately, `28913279` belongs to the
**Sacred** table (`0x08EBFB70`, index 110) and is absent from the Reshef table
`0x09E1462C` searched by the orange terminal (`0x090B494C`, literal at file
`0x10B49D0`), so the requested "result 10 / index 110" at `0x0203AC20` is not
reachable by that code at all; the same entry there would yield result 11. The correct
observation address for card 110 is the Sacred state `0x020319E0`. See §6b, fourth
pass.

### Fifth pass, 2026-10-25: Sacred route played to the story gate

The free machine was pursued from a clean boot of the Sacred half. The ROM and save were
copied out of `roms/`, the emulator was started **without** the GDB stub, NEW GAME was
chosen (the shared `.sav` holds only the other half's data), and the intro was played
through Kaiba's announcement in Clock Tower Square.

**What the Sacred gate actually is.** The free Password Machine is inside the Card Shop,
and the Card Shop is a *world-map* destination. The world map cannot be left before
9:00, so the gate is the pre-tournament story — not a fee and not the machine. The
published game script and the observed refusals agree on the advancing sequence:

1. Walk the 3×2 Clock Tower Square and **challenge** each of the five anime duelists with
   **R** (A only gives their casual Talk line). Each refuses because it is not nine yet
   and then leaves:
   * Yugi — "It's going to start soon. You should get lost in the town before nine."
     (observed; `screenshots/sacred_yugi_challenge_refusal.png`)
   * Mai — "Whoa, slow down, baby." … "I'll take you on if the opportunity arises." …
     "See you." (observed this session)
   * an unidentified duelist — "You'd make the perfect opponent for me." / "But the
     Tournament hasn't started yet." (observed;
     `screenshots/sacred_duelist_refusal_perfect_opponent.png`)
   * Bonz (south area, near the cafe tables) and Mako (north-west, near a tree) complete
     the five.
2. Go to the central clock area and **attempt to leave it in any direction**. The clock
   chimes, Joey/Yugi/Rex/Weevil/Mai/Kaiba appear, Kaiba declares the tournament, and
   free duels unlock.
3. The world map then lists Card Shop. Enter it and walk to the machine in the back-right
   corner; the Sacred password entry is free.

**How far this pass got / why it stopped.** The challenge mechanic was confirmed working
(two to three of the five refusals were obtained), but the square could not be crossed
reliably enough to collect all five: the 3×2 square is a set of scrolling screens whose
roads are blocked by NPCs and props, and the north alley entrance resolves to a blank,
static 133-grey screen that ignores the D-pad and A while the pause menu still opens
(observed **both with and without** the GDB stub, so it is a game-side stuck scene, not
a debugger artifact). Navigation was stopped there rather than looped.

**RAM baseline at the gate** (read with the GDB stub on the same build, before the
terminal was ever reachable):

| Address | Value | Meaning |
|---|---|---|
| `0x020319E0` | `00×12` | Sacred validator state: index 0, result 0, digits zero — never invoked |
| `0x0202F290` | `00×8` | Sacred digit buffer, empty |
| `0x02031A58` | `00×32` | Story-flag window used by the special codes, empty |
| `0x0203813E` | 38 u16 IDs | Collection (`5001, 5201, 8901, …`); card 110 (`0x006E`) absent |

So the terminal grant of index 110 and the `00000000` rejection remain **unobserved
in-game**. The blocker is the pre-tournament story sequence above, not the table, the
fee, or the machine.


Correction (third pass): the GDB stub **does** apply *memory* writes; only CPU
register/PC writes fail. See §6b, third pass. The remaining blocker is purely the
1,000-Domino fee plus city navigation: the paid terminal was reached only from the
outside, and no duel could be completed to raise the 500 Domino in the save.

Second pass (2026-10-25): both gates were re-confirmed from a live save (see §6b).
The 1,000-Domino charge is confirmed to be shop-script-side, not validator-side
(`0x090B4A20` contains no money logic), so there is no free lookup path in the paid
half. The free half still answers "This area is off limits until the Tournament!" at
the square exit. The starting save has no duplicate cards, so the 1,000 cannot be
raised by selling. The only remaining route is winning duels (paid half) or running
the tournament intro (free half); neither completed inside this session.

Fifth pass (2026-10-25): the Sacred route was played to the pre-tournament gate. The
gate is the five-duelist challenge plus clock-bell sequence described in §6b, not a
fee: challenge Yugi, Mai, Bonz, Weevil and Mako with R, then leave the clock area to
start the tournament and unlock the world map. Two to three refusals were captured
(Yugi and an unidentified duelist this pass, Mai earlier), but all five could not be
collected before the square's blocked roads and a stuck north-alley screen stopped the
pass. `0x020319E0` stayed all zero and the collection contained no card 110, so no
grant and no `00000000` rejection were produced. This remains a bounded negative at
the story gate, not a validator result.

### Sixth pass, 2026-10-25 (evening): R-refusals reproduced, gate still not passed

A sixth pass re-booted the Sacred half from a copy of the ROM and the 500-Domino `.sav`
(`/tmp/opencode/ygo7/`), chose NEW GAME, cleared the name-entry keyboard (the OK button
is the top-right green button, reached by pressing Right from the bottom-right letter
cell), and replayed the prologue: Joey's room → "Okay, let's get going" → Kaiba's full
Battle City / locator-card speech in Clock Tower Square. The intro was then complete and
the player was free in the square.

**The R challenge is real and repeatable.** Pressing **R** facing a duelist gives their
refusal; **A** gives only their casual line. Refusals captured this pass (screen OCR of
the dialogue box, 300–470 px band):

| Speaker | Text |
|---|---|
| Yugi | "It's going to start soon." / "You should get lost in the town before nine." |
| duelist | "Huh? It's not nine yet." / "Let's have a duel after nine, okay?" |
| duelist | "You shouldn't be so hasty." / "I want to begin dueling right away, too." |
| Mai | "Whoa, slow down, baby." / "I'll take you on if the opportunity arises." |
| duelist | "Hey, ease up. The Tournament hasn't started yet." / "Don't jump the gun." |
| duelist | "Whoops... The Tournament's about to start." / "I wouldn't be caught wandering around here." / "You'd be easy pickings for a skilled duelist." |

Artifacts: `screenshots/sacred_mai_refusal_sixth.png`,
`screenshots/sacred_duelist_hasnt_started_sixth.png`.

**New negative: the refusals write no story flag.** A full EWRAM dump was taken before
and after one R refusal ($0x02000000–$0x0203FFFF$, 256 KiB; dumps kept as
`/tmp/opencode/ygo7/snapA.bin` / `snapB.bin`). Differences were confined to the dialogue
text-render buffer (`0x0200D000–0x0200E000`) and the sound mixer (`0x02036xxx`); the
range `0x02020000–0x0202FFFF` changed **zero** bytes and the known story-flag window
`0x02031A58` (32 bytes) stayed all zero. So the "five R challenges" are **not** recorded
as a RAM-visible counter at the time of the refusal. Whatever advances the clock is not
a per-refusal flag in EWRAM.

**New ROM finding about the Card Shop.** Half 2 carries the plain-ASCII dialogue for
both games. At file `0x1E88BEE` the Card Shop clerk says:

> "Hello, welcome. I haven't opened the shop yet. Oh, there is something I should tell
> you. Challenge other duelists by pressing the R Button. That's very important. Don't
> forget it."

So the Card Shop is a *normal building whose interior can be entered before the
tournament* (the clerk is inside and teaches the R button); the fifth pass's "world-map
destination only" model is therefore at least incomplete. Two empty interiors were
entered this pass (mean brightness 133 and 128, 5×72-px corridor with no NPC on OAM) and
were not the shop; the shop door was not located before the session budget expired.

**Where this pass stopped.** No clock chime/cutscene fired on repeated walk-outs from the
square in all four directions (transitions are instant screen swaps, not fades; sampling
the mean during 3–8 s walks found no long black cutscene). No Card-Shop interior with a
clerk/machine was found. `0x020319E0` was never written.

**RAM at stop** (read through the mGBA GDB stub on a savestate of the final state,
`/tmp/opencode/ygo7/states/sacred_after_challenges.ss`):

| Address | Value | Meaning |
|---|---|---|
| `0x020319E0` | `00×12` | Sacred validator state: index 0, result 0, digits zero — never invoked |
| `0x02031A58` | `00×32` | story-flag window, empty |
| `0x0203813E` | 38 u16 IDs `0x0150,0x0152,0x0189,…` | collection; card `0x006E` (110) absent |
| `0x0203A97C` | `0x003C 0x0008` | scene/camera pair at stop |

**Failing step, precisely:** after the intro, find the entrance of the Card Shop (or the
world-map transition) from Clock Tower Square. Two routes were tried — (a) square exits
in all four directions, (b) entering every building door on the top wall of the city
screens — and both ended in ordinary street/empty-building screens. This is a
navigation failure, not a validator result: the terminal was never reached, so neither
`28913279` (accept → index 110) nor `00000000` (reject → result 11) was entered.

### Seventh pass, 2026-10-25 (late): corrected roster, guard located, gate still shut

Full detail in §6b, seventh pass. Summary of what changed and what did not:

* **Corrected roster** (English build): the five are **Yugi, Mai, Bonz, Underwoods,
  Tsunami**, per intensive08's English walkthrough §6.1 — *not* the Weevil/Mako/Rex set
  from the Japanese DM7 guide that passes five and six followed. §3.4 is corrected.
* **Input delivery was partly broken.** mGBA's SDL window ignores `xdotool key --window`
  synthetic events; keys must be sent with XTEST to the focused window. Verified by
  reading `KEYINPUT` at `0x04000130` while holding a key. Some earlier "the game ignored
  the D-pad" observations are therefore tool artifacts.
* **The exit is the north/north-west edge** and prints "This area is off limits until
  the Tournament." (`sacred_square_exit_guard_seventh.png`). Pushing through it produces
  the same blank grey dead room the fifth pass reported (mean brightness 88, frozen
  frame, pause menu still opens).
* **Still not done:** the full five-duelist sequence. This pass reproduced **Yugi's**
  and **Mai's** published refusals in-game with working input
  (`sacred_yugi_refusal_seventh.png`, `sacred_mai_refusal_seventh.png`) and located the
  guarded exit, but Bonz, Underwoods and Tsunami were not reached in sequence, so the
  9:00 bell never rang and the world map never opened. `0x020319E0` stayed `00×12`,
  `0x0203813E` still holds the same 38 cards with no `0x006E`, and `0x0203AC20` was
  never written either.

This remains a **navigation failure at the story gate**, not a validator result. The
remaining requirement in §0.2 (in-game acceptance of a novel password and a screenshot
of the received card, plus the `00000000` rejection) is still open.


Tooling/states kept: `/tmp/opencode/ygo7/` (`t.py` screen/OCR/RAM helpers, `walkR.py`,
`w3.py`, `blobs.py`; `daemon.py`/`rsp.py` GDB RSP bridge with 0x200-byte read chunks —
mGBA's stub rejects 0x400-byte reads; states `sacred_intro_narration.ss`,
`sacred_square_gate.ss`, `sacred_after_challenges.ss`, plus `snapA.bin`/`snapB.bin`, the
before/after EWRAM dumps used for the refusal-flag negative).

### Eighth pass, 2026-10-25 (night): five refusals done, bell still silent

Full detail in §6b, eighth pass. Net effect on §0.2:

* **Fixed:** frame capture (root XGetImage instead of `import -window`, which returns
  black on mGBA's DirectColor/GLX canvas), emulator liveness (`SDL_AUDIODRIVER=dummy`,
  without which the core parks at 0 % CPU), and RAM access (mGBA `-d` command-line
  debugger over a pty — `r/4 0xADDR`, `save`/`load` — instead of the single-client GDB
  stub on port 2345).
* **Done:** all five English-roster refusals reproduced in one session, each with a
  portrait screenshot — Yugi, Mai, Bonz, Underwoods (Weevil), Tsunami (Mako). Method:
  45 ms direction tap (turn in place) + **R**. Longer taps step off the adjacent tile
  and lose the challenge.
* **Not done:** the 9:00 bell. With all five refusals collected, N/E/S/W walk-outs from
  the clock screen, a re-entry and a 45 s idle wait produced no chime, no Joey and no
  Kaiba cutscene; the world map and Card Shop never opened. `0x020319E0`,
  `0x0202F290` and `0x02031A58` all remain zero; the collection has no `0x006E`.
* Consequence: `28913279` (accept → index 110) and `00000000` (reject → 11) are still
  **unobserved in-game**. The grant/rejection requirement of §0.2 remains open; the
  blocker is now precisely "the tournament-unlock trigger" rather than the roster,
  navigation distance, fee, or input delivery.


## 8. Unknowns

* Whether the eight "no password" codes grant the named card in the Sacred half's UI
  exactly as the table implies (the grant call is derived, not observed).
* The exact effect of the Sacred special codes 25410867 / 51404976 in the Sacred half
  (they set flag bits; the flags are read by story scripts, not by the terminal).
* The purpose of Reshef special code 25232415 (no effect in the function).
* The save validity test beyond the 16-bit word at +0x9CC; patching the obvious money
  field caused the save to be treated as empty.
* Whether IDs 823/824/865/886 in the Reshef half are additional novel cards.
* Why the Reshef duel's player main phase ignores every button except L/R in the
  turn-1 state (see §6b, eleventh pass). This — not deck strength — is what blocks a
  first real duel win, and therefore the 1,000-Domino fee and the in-game grant.
* Whether `0x0203172A` is the opponent's LP: it moves 8000 → 7650 (= 8000 − Conger's
  350 ATK) exactly when the first turn transition happens, which fits an opponent LP
  hit by our face-up Conger, but no independent damage event on the opponent was
  produced to confirm it.

## 9. Tooling

* mGBA 0.10.5 SDL (`/usr/games/mgba`), Xvfb :117, openbox, xdotool, scrot.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`.
* Python 3 scripts for: logo/header scan, table dump, published-list diff, save
  checksum check (`/tmp/opencode/yugioh/`).
* Artifacts: `tables.json` (both tables), `reshef_pub.txt` / `sacred_pub.json`
  (published lists), screenshots `*.png` in `/tmp/opencode/yugioh/`.
* Eighth pass tooling (`/tmp/opencode/ygo9/`, works without the GDB port):
  `md.py` drives `mgba9 -d` (a copy of `mgba`) through a pty (`r/4 0xADDR`,
  `save N`/`load N`), `srv.py` + `c.py` expose it over a unix socket, `rawgrab.py`
  reads the root window with `XGetImage` (the only capture that works on the
  DirectColor canvas), `nav.py` has the 45 ms turn + R probe, the 5 s full-screen
  walk, the boustrophedon `sweep()`, and dialogue OCR. Launch with
  `SDL_AUDIODRIVER=dummy DISPLAY=:NNN`.
* Tenth pass tooling (`/tmp/opencode/ygo10/`): same `-d`-over-pty server plus
  **`ssread.py`**, which parses an mGBA `save N` savestate offline: the PNG carries
  a `gbAs` chunk, zlib-decompressing it gives a 0x61000-byte state with
  **IWRAM at 0x19000 and EWRAM at 0x21000** (0x40000 bytes). That makes whole-RAM
  scans and before/after diffs instant and is how the Reshef money/LP addresses
  above were found. Notes: mGBA's GDB stub (`-g`) is single-client and stops
  accepting after the first disconnect, and `-g` and `-d` cannot be combined.
  Joining the Reshef name table (`0x1DCE0E8` pointer array) to the password
  table is the fastest way to name a novel code.
* Eleventh pass tooling (`/tmp/opencode/ygo11/`): `rel.py` restarts mGBA from a
  savestate (`-t`) because **F1–F10 do not load in this build**; `font.py` decodes the
  duel bitmap font (segment the text band on blank columns, identify each glyph by
  bitmap signature, learn new glyphs from one known string); `play.py`/`turn.py`
  drive a replay and print hand/deck/LP from RAM; `read.py` finds any text line on the
  whole screen (it needs a dark background, so it misses bright menu boxes).
* Twelfth pass tooling (`/tmp/opencode/ygo12/`), the **clean** stack used for the
  won duel — no debugger, no stub, no pty:
  `restart.sh` kills only its own PID and starts `/usr/games/mgba -3 -t <state>`;
  `x.py` focuses the window and sends XTEST `keydown`/`keyup` (`press(k, hold, gap)`
  — use `hold=0.07` for one cursor step, `0.12–0.15` elsewhere, because a 150 ms
  hold triggers the menu key repeat and moves two slots); `ss.py` decodes a
  `Shift+F<n>` PNG savestate (`gbAs` chunk → zlib → EWRAM at `0x21000`) and prints
  hand / LP / money / validator state; `nav.py` identifies the selected hand card by
  hashing the bright-pixel mask of the bottom-left name strip (`numpy`), so card
  navigation no longer depends on reading the screen by eye. `step.py` = press +
  save + decode in one call.

## 10. Legal note

No ROM, extracted graphics, audio, or copyrighted text is redistributed here. Only
hashes, addresses, algorithms, counts, and short factual identifiers are published.
