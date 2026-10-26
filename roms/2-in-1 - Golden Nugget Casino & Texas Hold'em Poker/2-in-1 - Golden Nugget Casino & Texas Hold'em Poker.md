# 2-in-1: Golden Nugget Casino & Texas Hold'em Poker (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/2-in-1 - Golden Nugget Casino & Texas Hold'em Poker/2-in-1 - Golden Nugget Casino & Texas Hold'em Poker.gba` |
| Size | 8,388,608 bytes (8 MiB) |
| MD5 | `291c1aa5d30affeb56ecd802b9e8d012` |
| SHA-1 | `e0aaeecbe1d52611ca633a45b19cb4d7b4651b0e` |
| SHA-256 | `509b939eff057accbe094449be2382e12ee3e2793ec5e807498b7996d55ad52b` |
| Image A header (0x0) | title `CASINO/HOLDM`, game code `BWCE`, maker `5G`, version 0, entry `0xEA00002E` |
| Image B header (0x400000) | title `TEXAS HOLDEM`, game code `BXAE`, maker `5G`, version 0, entry `0xEA00002E` |
| Extra logo hit | 0x1A800: stub header (blank title, logo present, `b .` entry); not a playable image |

The file is a two-image compilation. Image A runs at `0x08000000`, image B at
`0x08400000`. Both Nintendo logos are present, both complement checks are valid,
and both halves have their own code and data banks. All addresses below are ROM
addresses in the concatenated image unless marked as a file offset.

## 2. Executive summary

**The prior triage claim (“no cheats; tournament password display only”) is wrong.**
It is disproved twice over: Golden Nugget Casino has a **bankroll password
entry** (not a display), and Texas Hold'em has a **career/tournament password
entry** in addition to the tournament-result display. The GBA manual for Golden
Nugget Casino documents “The Password Entry Screen allows you to enter a
password and resume play with …” (scanned manual, gamegear.net mirror).

* **Golden Nugget Casino (image A) has a full bankroll password system.** It is
  reachable from the casino lobby: `PASSWORD` (bottom centre). The screen uses a
  13-character code over a 64-symbol alphabet in two pages (page 1 is the
  32-symbol uppercase/digit page, page 2 is the 32-symbol lowercase/punctuation
  page, toggled with **Select**). The code packs three little-endian 6-bit fields:
  bankroll (24 bits), credit (18 bits) and a reserved/debit field (18 bits), plus
  three 6-bit check characters. The generator is at `0x0801B9EC`; the two
  alphabet tables are at `0x0809B7AD` and `0x0809B7D2`.
* The published money codes on GameFAQs/mariogba were verified: `$500,000`
  (`Bg5cv#dbbbxbY`) gave `Player Money: $500000` on the Blackjack screen, and
  `$8,527,030` (`1XCBv#dbbbxbM`) was accepted and regenerated into the password
  field.
* A **novel code not present in any published list**, `BPRDv#dbbbxb3`
  (`$9,100,000`), was entered and produced `Player Money: $9100000`.
* A second novel code, `!!!!v#dbbbxb=` (`$16,777,215`, the 24-bit maximum), was
  accepted and triggered the game's **“You're a Multi-Millionaire — Time to
  retire!”** ending.
* Bounds were proven by rejection: changing the last check character
  (`BPRDv#dbbbxb4`) left the bankroll at `$2000`; a one-character password was
  also rejected.
* **Texas Hold'em (image B) also has an in-game password entry**:
  `CAREER MODE → CONTINUE CAREER → ENTER PASSWORD`. It is a 20-cell field over a
  36-key keyboard (digits, consonants, and five arrow/blank glyphs at the vowel
  positions; **Select** does not switch a page here). The published Reno
  “play as Phil” code `XDC4345F668WV<TSRN` was typed as
  `XDC4345F668WV◀TSRN` and accepted; the resulting career is **PHIL** at the
  Reno tournament with `$9,350` and `$50/$100` blinds.
* **The Texas codec is now fully reversed.** It is a fixed 18-character record
  over the alphabet `ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789`: five base-36 digits
  of bankroll, one tournament digit, an 11-character name field (length digit +
  literal name + `A` padding) and a checksum digit equal to the sum of the
  ASCII bytes of the first 17 characters mod 36. The visible code is the record
  passed through a position-dependent Caesar shift,
  `out[i] = alphabet[(value[i] - 3 - i) mod 36]`. All eight published codes
  decode and re-encode exactly. A **novel** code `4ATK364012XWVUTSRQ` was
  typed on the on-screen keyboard and produced the career **ACE** with
  `$777,777`; two invalid inputs (wrong checksum and a 17-character field) were
  rejected with the career unchanged.

## 3. How to reproduce

Emulator: mGBA 0.10.5 SDL under `Xvfb :109` (1024×768×24), `openbox`,
`SDL_AUDIODRIVER=dummy`, 3× scale. Window focused with
`xdotool windowactivate`. Default mGBA keymap: **A = x**, **B = z**,
**Start = Return**, **Select = BackSpace**, D-pad = arrows. A 100–400 ms hold is
needed; shorter taps are dropped by the game.

### Golden Nugget Casino

1. Boot the ROM; at `Choose a game` press **Start** (Return) to select Golden
   Nugget.
2. At `Player Sign In` accept the default name with **A** (x).
3. The ATM screen appears. **A** opens the casino lobby.
4. Move down to `PASSWORD` and press **A**. The screen is `Password`, with a
   prefilled 13-character code (for the initial `$2000` state:
   `v&bbv#dbbbxbF`).
5. Entry model: the first key pressed clears the prefilled field and starts a
   new code. D-pad moves the key cursor; **A** types the highlighted character;
   **Select** toggles page 1/page 2; the bottom-right `OK` submits.
6. A valid code returns to the lobby. `A` on the lobby's current item shows the
   credits; **Left + A** from there enters Blackjack, whose header shows
   `Player Money: $…`.

The GN input script used is `typepw.py` in `/tmp/opencode/nugget`; the Texas
driver is `typepass.py` in `/tmp/opencode/nugget2` (see §9); both drive the
cursor with short taps and verify each key by the on-screen cursor colour.

### Texas Hold'em Poker

1. At `Choose a game`, move right and press **Start** to boot Texas Hold'em.
2. Press **Start** at the title screen.
3. `CHOOSE GAME TYPE → CAREER MODE`. On a fresh boot this opens `ENTER NAME`;
   accept the default `PLAYER1` with **A** to create a career, then back out to
   `CHOOSE GAME TYPE` with **B** and select `CAREER MODE` again. The menu now
   offers `NEW CAREER` / `CONTINUE CAREER` (the cursor moves with a longer
   D-pad hold, ~0.5–1 s).
4. `CONTINUE CAREER → ENTER PASSWORD`. The field is 20 cells; type 18
   characters, leave the last two cells blank, move the cursor to `OK`
   (from the `M` key press **Down**; `OK` is at the bottom right) and press
   **A**. A valid code returns to the career menu / `CAREER INFO` with the new
   career loaded. `B` leaves the password screen and re-shows the previous
   code in the field.
5. The keyboard's vowels are drawn as glyphs but store ASCII: ▲=A, ▶=E, ▼=I,
   ■=O (blank/space), ◀=U. There is a delete key to the left of `OK`.

The Texas input driver is `typepass.py` in `/tmp/opencode/nugget2`; the codec
is `txpass.py`.

## 4. Address map

### Image A — Golden Nugget Casino (base 0x08000000)

| Address | Meaning |
|---|---|
| `0x0801B9EC` | Password screen / generator function (Thumb). Sets up the field and writes the 13 characters. |
| `0x0801BB0E` | Loop writing field 1 (bankroll): 4 × 6 bits, little-endian base 64. |
| `0x0801BB74` | Loop writing field 2 (credit): 3 × 6 bits. |
| `0x0801BBDC` | Loop writing field 3 (reserved): 3 × 6 bits. |
| `0x0801BC2C` | Check character 10: `(0x40 - sum(field2)) & 0x3F`. |
| `0x0801BD06` | Check character 11: `(0x40 - sum(field3)) & 0x3F`. |
| `0x0801BD46` | Check character 12: `(0x40 - (sum(field1)+sum(field2)+sum(field3))) & 0x3F`. |
| `0x0809B7AD` | Page-2 alphabet, 32 bytes: `bcdfghjklmnpqrstvwxyz<=>?%/+#@-&` |
| `0x0809B7D2` | Page-1 alphabet, 32 bytes: `BCDFGHJKLMNPQRSTVWXYZ0123456789!` |
| `0x03005230` | Password character buffer (13 bytes + terminator). |
| `0x0300347C` | 32-bit field-1 value (bankroll). |
| `0x03003614` | 32-bit field-2 value (credit). |
| `0x03003480` | 32-bit field-3 value (reserved/debit). |
| `0x03008840`, `0x0300BC50` | 16-bit checksum accumulators referenced by the generator. |

### Image B — Texas Hold'em Poker (base 0x08400000)

| Address | Meaning |
|---|---|
| `0x0843E9A4` | `CONGRATULATIONS` |
| `0x0843E9B4` | `%s, YOU QUALIFY` |
| `0x0843E9C4` | `FOR %s` |
| `0x0843E9CC` | `PASSWORD` |
| `0x0843E9DC` | `%s, YOU ARE THE` |
| `0x0843E9EC` | `CHAMPION WITH $%d` |
| `0x0840FF60` | Text drawing/format helper used by the qualify screen |
| `0x08406290` | Screen text/DMA setup used by the qualify screen |
| `0x0840634C` | “PASSWORD” display page (reads the generated code) |
| `0x08405E90` + `0x084061D0` | Qualify message page(s) (`CONGRATULATIONS` / `FOR %s`) |
| `0x08414E58` | ENTER PASSWORD key handler: keys 0–9→`0`–`9`, 10–35→`A`–`Z`; key 36 = delete; key 37 = OK (checks length ≠ 0 and sets the submit flag). |
| `0x084157D4` | Career screen state machine; reads the submit flag and calls the tournament/career setup. |
| `0x0841660C` | Tournament setup: copies the current tournament definition into the career object and calls the password decoder. |
| `0x084174B8` | **Password decoder**: `decode(descriptor, input_18chars)` — copies 18 bytes, un-shifts, validates, then parses each field. |
| `0x08417768` | **Checksum validator**: `sum(ASCII(input[0..16])) % 36 == value(input[17])`. |
| `0x08417810` | **Input un-shift**: `value[i] = (index(c[i]) + 3 + i) mod 36`. |
| `0x084177D4` | **Output shift**: `c[i] = alphabet[(value[i] - 3 - i) mod 36]`. |
| `0x084171C8` | `alphabet_index(descriptor, char)` — linear search of the 36-byte alphabet. |
| `0x084171F4` | Generic radix encoder (fields → digit string). |
| `0x08417728` | Checksum writer (same sum as the validator). |
| `0x0841A2CC` / `0x0841A78C` / `0x0841A6BC` | 64-bit divide / multiply / modulo helpers used by the radix codec. |
| `0x087DA020` | Tournament preset table, 5 records of 0x20 bytes: `RIVERBOAT`, `LAKE TAHOE`, `RENO`, `ATLANTIC CITY`, `LAS VEGAS`, plus bankroll/blind fields. |
| `0x087DA0BC` | 36-byte alphabet `ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789` (copied to `0x020000AC`). |
| `0x020000AC` | RAM copy of the 36-byte alphabet. |
| `0x02007CA0` | ENTER PASSWORD screen object. |
| `0x02007EA0` | Field length byte (screen object `+0x200`). |
| `0x02007EA1` | **Password input buffer**, 20 cells (screen object `+0x201`). |
| `0x02007E9C` | Submit flag (screen object `+0x1FC`). |
| `0x020064C8` | Codec descriptor: `+4` alphabet ptr, `+8` alphabet length (36), `+0xC` field-pointer array, `+0x10` field count (3), `+0x14` temporary digit buffer, `+0x18` code length (18). |
| `0x02006540` / `0x02006560` / `0x02006580` | Field descriptors: bankroll (type 0, 5 digits), tournament (type 0, 1 digit), name (type 3, 11 digits). |
| `0x02005398` | Current tournament/career object; name at `+0x109` (`0x020054A1`), bankroll at `+0x118` (`0x020054B0`), tournament index at `+0x11C` (`0x020054B4`). |

The tournament password display is a **generated** code: `0x0840634C` reads the
text object at `obj+0x120` and draws it via the radix encoder. The same
encoder/decoder pair is used by the input screen.

No battery-save file was produced by mGBA (the `.sav` stayed 0 bytes), so the
passwords are the game's persistence mechanism for both halves.

## 5. Algorithm — Golden Nugget bankroll password

### 5.1 Alphabet and value mapping

`value → character` is:

```
value  0..31 : "bcdfghjklmnpqrstvwxyz<=>?%/+#@-&"[value]
value 32..63 : "BCDFGHJKLMNPQRSTVWXYZ0123456789!"[value-32]
```

This is the mapping at `0x0801BB74`; the inverse is used below.

### 5.2 Encoding

For a state `(money, credit, reserved)`:

```
f1[i] = (money  >> (6*i)) & 63, i = 0..3     # 24-bit bankroll
f2[i] = (credit >> (6*i)) & 63, i = 0..2     # 18-bit credit
f3[i] = (reserved >> (6*i)) & 63, i = 0..2   # 18-bit reserved/debit

c1 = (0x40 - (sum(f2) & 63)) & 63
c2 = (0x40 - (sum(f3) & 63)) & 63
c3 = (0x40 - ((sum(f1)+sum(f2)+sum(f3)) & 63)) & 63

code = chars(f1[0..3] + f2[0..2] + f3[0..2] + [c1,c2,c3])   # 13 characters
```

The generator writes the first four characters from `0x0300347C`, the next
three from `0x03003614`, the next three from `0x03003480`, and then the three
check characters. `0x40 - x` is the same as `-x mod 64`, so the checks are just
the negated sums.

### 5.3 Decoding / validation

Decode each character to 0..63, split 4+3+3+3, recompute `c1,c2,c3` and require
all three to match. No other range check exists in the generator: every 24-bit
bankroll, 18-bit credit and 18-bit reserved value is representable. The field
widths are the bounds.

### 5.4 Verification against the published list

All seven mariogba/GameFAQs money codes and the default `$2000` code decode to
the stated bankroll and pass the check characters:

| Published code | Decoded money | Credit | Reserved | Checks |
|---|---:|---:|---:|---|
| `v&bbv#dbbbxbF` (default) | 2,000 | 10,000 | 0 | pass |
| `Bg5cv#dbbbxbY` | 500,000 | 10,000 | 0 | pass |
| `bmZfv#dbbbxbx` | 1,000,000 | 10,000 | 0 | pass |
| `bxLkv#dbbbxbw` | 2,000,000 | 10,000 | 0 | pass |
| `b+#pv#dbbbxbv` | 3,000,000 | 10,000 | 0 | pass |
| `bRgyv#dbbbxbs` | 5,000,000 | 10,000 | 0 | pass |
| `!%mJv#dbbbxbp` | 9,999,999 | 10,000 | 0 | pass |
| `b/mJv#dbbbxbm` | 10,000,000 | 10,000 | 0 | pass |
| `1XCBv#dbbbxbM` (GameFAQs) | 8,527,030 | 10,000 | 0 | pass |

Every published GN code is therefore a valid encoding under the reversed
algorithm; no table lookup is involved, and the credit field is fixed at
`10,000` in all published codes.

## 5b. Algorithm — Texas Hold'em career password

### 5b.1 Alphabet and glyph mapping

The keyboard/record alphabet is 36 symbols:

```
ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789      (A=0 … Z=25, 0=26 … 9=35)
```

The screen draws the five vowels with card-style glyphs, but the stored
characters are plain ASCII: `A`=▲, `E`=▶, `I`=▼, `O`=■, `U`=◀. The published
`^` is an `A` and the published `<` is a `U`.

### 5b.2 Direct record (18 digits)

Decoding the entered code first removes a position-dependent shift:

```
D[i] = alphabet[(index(E[i]) + 3 + i) mod 36],  i = 0..17
```

`D` is a fixed 18-character record:

```
D[0..4]   bankroll, 5 base-36 digits, little-endian (36^5 = 60,466,176 states)
D[5]      tournament index: 0 RIVERBOAT, 1 LAKE TAHOE, 2 RENO,
          3 ATLANTIC CITY, 4 LAS VEGAS
D[6..16]  name field, 11 characters:
            D[6] = alphabet[len(name)]      (0..10)
            D[7..6+len] = the name characters themselves (A-Z/0-9)
            remaining characters = 'A' (0) padding
D[17]     checksum = (sum of ASCII bytes D[0..16]) mod 36
```

The name is stored **literally** in the record (it is not a hash or a base-26
number). The checksum is over the raw ASCII bytes, not over the alphabet
values; this is why it is not a simple base-36 digit sum.

### 5b.3 Encoding (state → visible code)

```
build D as above (alphabet[len(name)] + name + 'A' padding)
D[17] = alphabet[sum(D[0..16].encode('ascii')) % 36]
E[i]  = alphabet[(value(D[i]) - 3 - i) mod 36]
```

### 5b.4 Decoding / validation

Undo the shift, then require

```
sum(D[0..16].encode('ascii')) % 36 == value(D[17])
```

Only this checksum is validated. There is no range check on the tournament
digit or on the bankroll: any 18-character string with a matching checksum is
accepted, and the decoded fields are written to the career object at
`0x02005398`.

### 5b.5 Verification against the published list

All eight published Texas codes decode and re-encode exactly under this model:

| Published code | Bankroll | Tour | Name | Checks |
|---|---:|---:|---|---|
| `VB64338F^YL0CLTSR0` | 1,500 | 1 Tahoe | `PLAYER1` | pass |
| `D4B4348F^YL0CLTSR^` | 9,006 | 2 Reno | `PLAYER1` | pass |
| `7<^5358F^YL0CLTSR2` | 54,000 | 3 Atlantic City | `PLAYER1` | pass |
| `763^368F^YL0CLTSR6` | 324,000 | 4 Las Vegas | `PLAYER1` | pass |
| `HP64335F668WV<TSRJ` | 1,990 | 1 Tahoe | `PHIL` | pass |
| `XDC4345F668WV<TSRN` | 9,350 | 2 Reno | `PHIL` | pass |
| `7<^5355F668WV<TSRL` | 54,000 | 3 Atlantic City | `PHIL` | pass |
| `763^365F668WV<TSRP` | 324,000 | 4 Las Vegas | `PHIL` | pass |

The four “Phil” codes are therefore not a separate career type: they differ
from the tournament codes only in the literal name field (and, for Tahoe/Reno,
in the stated bankroll). The opponent (`ROGER`) and the blinds come from the
tournament table entry, not from the password.

## 6. Tables

### 6.1 Golden Nugget published codes and in-game outcome

| Effect | Code | Verified |
|---|---|---|
| $500,000 | `Bg5cv#dbbbxbY` | **Yes** — Blackjack header `Player Money: $500000` (shot 165) |
| $1,000,000 | `bmZfv#dbbbxbx` | Decoder/ROM-verified (checks pass) |
| $2,000,000 | `bxLkv#dbbbxbw` | Decoder/ROM-verified (checks pass) |
| $3,000,000 | `b+#pv#dbbbxbv` | Decoder/ROM-verified (checks pass) |
| $5,000,000 | `bRgyv#dbbbxbs` | Decoder/ROM-verified (checks pass) |
| $9,999,999 | `!%mJv#dbbbxbp` | Decoder/ROM-verified (checks pass) |
| $10,000,000 | `b/mJv#dbbbxbm` | Decoder/ROM-verified (checks pass) |
| $8,527,030 | `1XCBv#dbbbxbM` | **Yes** — accepted and regenerated into the password field (shot 183) |

### 6.2 Texas Hold'em published codes and decoded state

From the archived GameFAQs FAQ (`brian_sulpher`, 2006; true punctuation with
`^` = up arrow/A, `<` = left arrow/U). Every row decodes under §5b:

| Effect | Code | Bankroll | Tour | Name |
|---|---|---:|---:|---|
| Lake Tahoe tournament | `VB64338F^YL0CLTSR0` | 1,500 | 1 | `PLAYER1` |
| Reno tournament | `D4B4348F^YL0CLTSR^` | 9,006 | 2 | `PLAYER1` |
| Atlantic City tournament | `7<^5358F^YL0CLTSR2` | 54,000 | 3 | `PLAYER1` |
| Las Vegas Championship | `763^368F^YL0CLTSR6` | 324,000 | 4 | `PLAYER1` |
| Phil Helmuth, Lake Tahoe | `HP64335F668WV<TSRJ` | 1,990 | 1 | `PHIL` |
| Phil Helmuth, Reno | `XDC4345F668WV<TSRN` | 9,350 | 2 | `PHIL` |
| Phil Helmuth, Atlantic City | `7<^5355F668WV<TSRL` | 54,000 | 3 | `PHIL` |
| Phil Helmuth, Las Vegas | `763^365F668WV<TSRP` | 324,000 | 4 | `PHIL` |

The Texas screen’s key positions (observed from the glyphs): row 1
`A B C D E F G H I J K L M` with `A`=▲ up, `E`=▶ right, `I`=▼ down; row 2
`N O P Q R S T U V W X Y Z` with `O`=■ blank/space and `U`=◀ left.
The published `<` therefore maps to the `U` key and `^` to the `A` key. The
glyphs are only a display substitution; the buffer stores ordinary ASCII
vowels.

**Verified in-game:** `XDC4345F668WV<TSRN` (typed as
`XDC4345F668WV◀TSRN`, 18 characters, two blank cells left unused) was accepted
at `CAREER MODE → CONTINUE CAREER → ENTER PASSWORD`. The career menu returned
and the table header showed **PHIL** with `$9,350`, opponent `ROGER` with
`$8,880`, blinds `$50/$100` — the Reno tournament, not the default `PLAYER1`
career.

**Novel, previously unpublished code:** `4ATK364012XWVUTSRQ` decodes to
bankroll 777,777, tournament 4 (Las Vegas), name `ACE`. It was typed on the
on-screen keyboard and accepted; the table header then showed **ACE** with
`$777,777` (`screenshots/tx_novel_table.png`). The career object at
`0x02005398` contains `04` (tournament) at `+0x11C`, `0x000BDE31` (777,777) at
`+0x118`, and `ACE` at `+0x109`.

## 6b. Enumeration

### Golden Nugget

* **Space:** 13 cells × 64 symbols = **64^13 = 302,231,454,903,657,293,676,544**
  raw strings (2^78). The last three cells are deterministic checks, so the
  validator accepts exactly **64^10 = 2^60 =
  1,152,921,504,606,846,976** codes — one for each 60-bit state. Density: 1 in
  2^18 random 13-symbol strings.
* **Field bounds:** bankroll `0 … 16,777,215` (0xFFFFFF); credit
  `0 … 262,143`; reserved `0 … 262,143`. These are the widths of the 24/18/18-bit
  fields; the format cannot express more.
* **Novel code accepted (not in any published list):**

  | Bankroll | Code | In-game effect |
  |---:|---|---|
  | $9,100,000 | `BPRDv#dbbbxb3` | Blackjack header `Player Money: $9100000` (`screenshots/gn_novel_9100000.png`) |
  | $16,777,215 (max) | `!!!!v#dbbbxb=` | Accepted; triggered the “You're a Multi-Millionaire — Time to retire!” ending |

  `$9,100,000` is absent from the mariogba list, the GameFAQs list and the
  chaptercheats list; it is a pure algorithm output.
* **Bounds proven by rejection:**
  * `BPRDv#dbbbxb4` (same bankroll, last check character incremented by one)
    was rejected; the Blackjack header stayed `Player Money: $2000`.
  * A one-character password `1` was rejected and the screen returned to the
    lobby without changing the state.
  * The maximum expressible bankroll is 0xFFFFFF because field 1 is exactly four
    6-bit characters; a fifth data character cannot exist in the 13-character
    format.

### Texas Hold'em

* **Space:** 20 cells × 36 keys = **36^20 =
  13,367,494,538,843,734,067,838,845,976,576** raw strings. The validator reads
  exactly 18 characters and requires the last to be the checksum of the first
  17, so **36^17 = 286,511,799,958,070,431,838,109,696** strings pass the
  checksum (density 1 in 36). Of those, the distinct *career states* with an
  in-table tournament and a name that fits the 11-digit field are
  `36^5 × 5 × Σ(36^k, k=0..10)` = **1,136,951,587,135,200,117,703,680**
  (bankroll `0..60,466,175`, five tournaments, names of 0–10 alphabet
  characters). The codec is bijective on that set.
* **Field bounds:** bankroll `0 … 60,466,175` (36^5−1); tournament digit
  `0 … 35` representable, but only `0 … 4` index the five-entry preset table;
  name length `0 … 10` (the length digit itself is one base-36 symbol). The
  validator does **not** range-check the value fields: tournament digit 5 and
  bankroll 60,000,000 were both accepted and stored (career object `+0x11C = 5`,
  `+0x118 = 0x03938700`). The only hard structural bounds are the fixed
  18-byte record and the checksum; a bit-flipped tournament or an
  out-of-table bankroll is not rejected, so the game will index past the preset
  table for digit 5–35. That is a latent out-of-bounds field, not a rejected
  input.
* **Novel code accepted and confirmed in-game:**

  | Bankroll | Tour | Name | Code | Effect |
  |---:|---|---|---|---|
  | 777,777 | 4 (Las Vegas) | `ACE` | `4ATK364012XWVUTSRQ` | Typed on the 36-key screen; career header `ACE` / `$777,777` (`screenshots/tx_novel_table.png`); career object `+0x118 = 0x000BDE31`, `+0x11C = 4`, `+0x109 = "ACE"` |
  | 9,350 | 2 (Reno) | `TEST` | `XDC4345J3GGWVUTSR6` | Accepted; career object name became `TEST` (name-field proof) |
  | 9,350 | 2 (Reno) | `NUGGET` | `XDC4347DJ430EUTSRG` | Accepted; career object name became `NUGGET` |

* **Bounds proven by rejection (career state unchanged both times):**
  * **Bad checksum:** `XDC4345F668WVUTSRM` (Reno/Phil with the last character
    changed from `N` to `M`) leaves the checksum unequal to
    `sum(ASCII(first 17)) % 36`. After OK the game stayed on `ENTER PASSWORD`
    and the career object remained `PHIL` / 9,350 / tournament 2
    (`screenshots/tx_reject_checksum.png`; RAM `0x02007EA1` still held the bad
    string, `0x020054A0` unchanged).
  * **Length out of range:** a 17-character code
    `XDC4345F668WVUTSR` (field length byte `0x11`) was rejected; the screen
    stayed on `ENTER PASSWORD` and the career object kept the values from the
    preceding accepted code (`screenshots/tx_reject_length.png`). The decoder's
    copy loop is fixed at 18 bytes, so the 18th byte is the string terminator
    and the checksum cannot match (inferred from the loop; no separate length
    test was found in the validator).
  * A 19th/20th character is not read by the decoder (it copies exactly 18
    bytes); whether the OK handler would accept a 19-character field with a
    valid 18-byte prefix was not tested, so the two spare cells are documented
    as unused rather than as a rejection bound.
* **Published-list reproduction:** all eight codes in §6.2 decode and re-encode
  exactly; `txpass.py` prints `OK` for every round trip.

## 7. Validation evidence

**Observed (emulator screenshots):** the durable copies referenced from this
report are in `screenshots/` next to this file. The Golden Nugget frames were
captured in the earlier pass (`/tmp/opencode/nugget/shots`); the Texas frames
were captured in the codec pass (`/tmp/opencode/nugget2/shots`).

* `screenshots/gn_published_500000.png` — GN `$500,000` code accepted;
  Blackjack header `Player Money: $500000`.
* `screenshots/gn_novel_9100000.png` — novel GN `$9,100,000` code accepted;
  header `Player Money: $9100000`.
* `screenshots/tx_published_typed.png` — Texas `XDC4345F668WV◀TSRN` in the
  20-cell field.
* `screenshots/tx_phil_reno_table.png` — Texas career `PHIL` `$9350`,
  `ROGER` `$8880`, `$50/$100`.
* `screenshots/tx_novel_typed.png` — novel code `4ATK364012XWVUTSRQ` typed on
  the on-screen keyboard (18/20 cells).
* `screenshots/tx_novel_table.png` — the accepted novel career: **ACE** with
  `$777,777` at the table.
* `screenshots/tx_reject_checksum.png` — after OK on
  `XDC4345F668WVUTSRM` (bad checksum) the screen stayed on `ENTER PASSWORD`.
* `screenshots/tx_reject_length.png` — after OK on the 17-character
  `XDC4345F668WVUTSR` the screen stayed on `ENTER PASSWORD`.

**Observed (memory, GDB):**

* Texas input buffer `0x02007EA1` held each submitted string; length byte
  `0x02007EA0` was 18 for accepted codes and 17 for the rejected short code.
* Career object `0x02005398`: after the novel code, name `ACE` at `+0x109`,
  bankroll `0x000BDE31` (777,777) at `+0x118`, tournament `4` at `+0x11C`.
* After both rejections the same object still held the previous career values
  (`PHIL`, 9,350, tournament 2 for the checksum case), proving the state did
  not change.
* The submit flag is `0x02007E9C` (screen object `+0x1FC`); writes to it come
  from `0x08414FD8`, and the consumer at `0x084157C2` calls the career setup
  at `0x084157D4`.

**Derived (instruction-level):**

* Golden Nugget: generator at `0x0801B9EC` (four+three+three 6-bit writes, three
  negated-sum check characters), the two alphabet tables, and the 64-symbol
  mapping. All eight published GN money codes decode consistently.
* Texas: decoder `0x084174B8`, checksum validator `0x08417768`
  (`sum(ASCII(first 17)) % 36`), input un-shift `0x08417810`
  (`+3+i`), output shift `0x084177D4` (`-3-i`), alphabet
  `ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789`. All eight published Texas codes decode
  and re-encode; three independently minted codes were accepted.

**Inferred:** the `reserved` field's game meaning (Golden Nugget) is not named;
the published codes set it to 0. The tournament-5 acceptance shows the Texas
validator trusts the one-digit tournament field; the game's later lookup has no
documented guard.

## 8. Unknowns

* Golden Nugget: the screen's validation routine (called by `OK`) was not
  separately disassembled; the generator and the regenerated prefilled code
  prove the encoding.
* Golden Nugget: the meaning of the 18-bit `reserved` field (field 3) is not
  established. All published codes use 0.
* Texas: the tournament digit is representable over 0–35 but only 0–4 index the
  five preset records. Value 5 was accepted and stored; whether the subsequent
  table lookup reads a valid adjacent record or garbage was not exercised to a
  visible table start.
* Texas: name lengths above 10 would write past the 11-digit name field; that
  overflow was not exercised.
* Texas: the exact 64-bit radix helpers (`0x0841A2CC`, `0x0841A78C`,
  `0x0841A6BC`) were treated as divide/multiply/modulo from their call sites,
  not separately reimplemented.

## 9. Tooling

* `mGBA 0.10.5` (SDL), `Xvfb :109`, `openbox`, `scrot`, ImageMagick
  `import`/`convert`, `xdotool`.
* GNU binutils `arm-none-eabi-objdump` (`-M force-thumb`) for raw disassembly.
* `gdb-multiarch` against the mGBA GDB stub (`mgba -g`, port 2345): hardware
  read/write watchpoints on `0x02007EA1` (input), `0x02007E9C` (submit flag),
  `0x020054A0`/`0x020054B4` (career fields), plus `find` in EWRAM.
* Python 3 + Pillow for the on-screen keyboard cursor feedback.
* `poppler-utils` was installed to test the scanned manual (no extractable
  text).
* Scripts: `/tmp/opencode/nugget2/txpass.py` (encoder/decoder + published-list
  self-test), shipped next to this report as `txpass.py`; `typepass.py` (36-key
  cursor driver and submit), `key.py` (keypress helper).
* Screenshots: `screenshots/` (repo, referenced above); working copies in
  `/tmp/opencode/nugget2/shots` and the earlier `/tmp/opencode/nugget/shots`.

## 10. Legal note

No ROM, extracted graphics, music, or game text is redistributed here. All
addresses, algorithms, tables and generated codes are analytical results. The
screenshots in `screenshots/` are emulator evidence of menu states and the
resulting career headers.
