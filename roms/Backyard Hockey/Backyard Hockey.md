# Backyard Hockey (GBA) — Reverse Engineering Report

Status: complete. Scope: in-game / developer-intended cheats only (passwords,
button codes, hidden/debug menus, unlockables). No GameShark, CodeBreaker,
Action Replay or other memory-edit codes are proposed or relied on.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Backyard Hockey/Backyard Hockey.gba` |
| Size | 4,194,304 bytes (4 MiB, `0x400000`, 32 Mbit) |
| Header title (`0xA0`) | `BACKYARD HCY` |
| Game code (`0xAC`) | `BYHE` |
| Maker (`0xB0`) | `70` (Atari) |
| Version (`0xBC`) | `00` |
| Fixed byte `0xB2` | `0x96` ✔ |
| Entry (`0x00`) | `0xEA00002E` → ARM branch to `0x080000C0` |
| Complement check (`0xBD`) | `0x7D` (computed `0x7D` ✔) |
| Header checksum (`0xBE`) | `0x0000` (computed `0x7D` ✘) |
| MD5 | `ce57edc0645572af5244e3e24b586133` |
| SHA-1 | `4829aa329e21d9c4822c3df66426b59a7690baa4` |
| SHA-256 | `48d5399eb8664fd6e31f727a09b6bc7f2c369b2dbb3edb60a93f97702d1403be` |

Embedded-header scan (search the whole file for the exact 156-byte Nintendo
logo at `0x04`–`0x9F`): **one hit**, at file `0x04`. This is a single-image
cartridge, not a multi-game pack and not a multiboot stub. There is no second
GBA header anywhere in the 4 MiB.

The image boots with the stock ARM branch and crt0 at `0x080000C0`. The only
header anomaly is the checksum word at `0xBE`, which is zero instead of `0x7D`;
the complement check is correct and mGBA boots the ROM normally. This looks
like a header patch or a dump artefact, not a trainer: the entry, logo, title,
code and reset vector are untouched, and the rest of the image behaves as one
consistent retail build throughout the analysis.

## 2. Executive summary

**Backyard Hockey (GBA) has no in-game password, button-code, or coach-name
cheat system, and no reachable debug/cheat menu.** The result is a bounded
negative, established by text search, table search, structural analysis of the
only name-entry screen, and a walk of every reachable menu.

The facts that decide it:

* The strings `password`, `passcode`, `cheat`, `debug`, `unlock`, `goodie` and
  `code` occur **zero** times in the whole ROM (case-insensitive). `secret`
  occurs once, as the roster nickname `"SECRET WEAPON"` at `0x064558`
  (Pete Wheeler's nickname), not as a password.
* The only text-entry screen found in the game is the **season coach name**.
  Its on-screen keyboard is 26 letters `A`–`Z` plus `OK` and `DELETE`; there is
  no SPACE cell, and the field accepts **at most 7 characters** (typing 9
  leaves 7).
* There is **no comparator** for that name in the ROM. The name is written to
  the coach name field at `0x030059B4`, packed into the save block at
  `0x030009CB` (5 bits per letter) and decoded again for display. The only
  readers are the screen renderer and the save packer; no table compare,
  `strcmp`/`strstr` call, hash or checksum over the name exists. Consequently
  the accepted set is empty and no code can be minted.
* No button-code table exists. The engine's familiar 10-button letter table
  (Backyard Basketball style: `u d l r a b s t m v`) is absent: the whole ROM
  contains only **two** NUL-terminated lowercase button-letter runs, `dub`
  (`0x121051`) and `bdv` (`0x144850`), neither a table. A scan for `u16`
  key-mask arrays (active-high and active-low) and for the documented
  Backyard Basketball sequences returns no candidate.
* The published GBA page's code sections are **PC contributions**. The three
  coach names (`Ikan Trace`, `Ivanna Tipe`, `Mike McMeeting`) are 10–14
  characters including a space, so they cannot be typed into a 7-letter A–Z
  field; the three player names (`Beverly Backstop`, `Buddy Cheque`,
  `Lemon Boy`) have no entry screen at all, because the GBA Custom Player
  screen uses a 15-item preset nickname spinner and no keyboard. The GBA-only
  published entries are **unlockables**, not codes: Mr. Schinkel's Pool (win
  Mr. Clankey's Cast-Iron Cup in Season Mode) and Tech State University (make
  the playoffs in Season Mode). Those are progression rewards.
* Every menu reachable without a second GBA/link cable was walked: title,
  main menu, Play Now (difficulty, submenu, rink, team, puck toss, player
  cards), Single Game (difficulty, rink, 30-team select, puck toss, player
  select, custom player), Season Play (coach sign-in, 2 slots, name keyboard,
  difficulty, rink, team, draft, save, matchup), Practice (3-on-1, Air
  Hockey), Multiplayer (head-to-head, air hockey), Options, Credits, and the
  pause/quit menus. No hidden screen appeared.

Because the accepted set is empty, the "novel code" deliverable for this
engagement is the **proof of absence**, not a generated string; §6b states the
space, the exhaustive structural search and the rejected inputs.

## 3. How to reproduce

Emulator: mGBA 0.10.5 SDL (`/usr/games/mgba`), 3× scale, headless Xvfb.

```bash
Xvfb :158 -screen 0 1024x768x24 &
DISPLAY=:158 openbox &
DISPLAY=:158 SDL_AUDIODRIVER=dummy /usr/games/mgba -3 \
  "roms/Backyard Hockey/Backyard Hockey.gba" &
```

The mGBA window was at `720x480+153+164`; screenshots were taken with
`import -window root` and cropped `720x480+153+164`.

Default mGBA SDL keymap used:

| GBA | Key |
|---|---|
| A | `x` |
| B | `z` |
| Start | `Return` |
| Select | `BackSpace` |
| L / R | `a` / `s` |
| D-pad | arrow keys |

Hold keys 100–300 ms. Many screens have a transition; wait 2–3 s before
deciding a press was missed.

### 3.1 Menu paths used

```
boot → Atari logo → NHL notice → NHLPA notice → title (Press Start)
  → main menu (7 rows)

PLAY NOW → Difficulty Level → Play Now sub-menu (PLAY / TEAM STRATEGY / OPTIONS)
  PLAY → Rink Select → Team Select (2 conferences, 30 NHL teams)
        → Puck Toss → Player Cards → commentary → game
SINGLE GAME → Difficulty Level → Rink Select → Team Select → Puck Toss
        → Player Select (12 cards + CUSTOM) → Player Cards → commentary → game
SEASON PLAY → Coach Sign In (2 slots, COPY COACH, DELETE COACH, NEW)
        → name keyboard → Difficulty Level → Rink Select → Team Select
        → Player Select → SAVE → matchup → commentary → game
PRACTICE → 3-ON-1 or AIR HOCKEY (difficulty / timer / score / multi-pucks)
MULTIPLAYER → HEAD TO HEAD or AIR HOCKEY → link wait
OPTIONS → 5 toggles
CREDITS → scrolling credits
in game: Start → pause (RESUME / QUIT) → QUIT GAME? (YES / NO)
```

### 3.2 The coach-name test (the only text field)

1. `SEASON PLAY` → `NEW` (second slot if slot 1 exists).
2. The keyboard is `A`–`Z` on four rows, then `OK` and `DELETE`.
3. Typing `IKANTRACE` (9 characters) leaves the display at **7** characters
   (`IKANTR`/`AIKANTR` depending on pre-existing text). The extra presses do
   nothing.
4. `OK` accepts the 7-character name; no message, no unlocked team, no new
   rink. Selecting the coach and entering a season shows the same 30 NHL teams
   on both conference pages.

### 3.3 Test inputs and outcomes

| Input | Entry point | Result |
|---|---|---|
| `IKANTRACE` (9) | coach keyboard | truncated to 7; cannot be submitted as published |
| `IKANTRC` (7, published code truncated) | coach keyboard | accepted as an ordinary coach; no special team/rink/flag; see §6b |
| `IVANNA TIPE`, `MIKE MCMEETING` | coach keyboard | not expressible: space cell absent, length > 7 |
| `BEVERLY BACKSTOP`, `BUDDY CHEQUE`, `LEMON BOY` | Custom Player | not expressible: nickname is a 15-item spinner, there is no text entry |
| `Up Up Down Down A` | season matchup | accepted the screen normally; no visible effect and no cheat screen |
| `Up Up Down Down Left Right Left Right B A` | title, main | no effect; normal title/main remained |
| `L + R + Start` | main | normal PLAY NOW transition, no hidden menu |
| 8th/9th letter | coach keyboard | dropped at 7 (observed) |
| SPACE | coach keyboard | not present as a cell |

Screenshots (work directory `/tmp/opencode/bhockey/shots/`):

* `05_main_c.png` — main menu (7 rows)
* `15_nameentry_c.png` — coach keyboard (A–Z, OK, DELETE; no SPACE)
* `17_ikantrace_c.png` — 9 characters typed, only 7 accepted
* `53_ikantrc_c.png` — 7-character `IKANTRC` coach created
* `56_teamlist_c.png`, `121_teamsel_single_c.png`, `122_west_c.png` —
  the two 15-team conference pages, no special team
* `82_options_c.png` — Options (5 toggles)
* `85_credits2_c.png` — Game Credits
* `62_practice_c.png`, `67_airhockey_pre_c.png`, `68_airhockey_c.png` — Practice
* `72_multi_c.png`, `73_h2h_c.png` — Multiplayer link wait
* `98_custom2_c.png`, `nick_A.png`, `nick_B.png` — Custom Player nickname
  spinner (15 presets, no keyboard)
* `102_uudda_c.png`, `103_aftercode_c.png` — documented button sequence at
  the season matchup, no effect
* `106_konami_title_c.png`, `108_lrstart_c.png` — title/main combo tests

## 4. Address map

All ROM addresses are `0x08000000 + file_offset`. All code is Thumb unless
noted. RAM addresses are IWRAM (`0x03000000`–`0x03007FFF`).

| Item | Address | Notes |
|---|---:|---|
| Text bank base | `0x083ABD70` | Plain NUL-terminated ASCII; coach strings are at `0x083ACBE9` (`Coach Sign In`), `0x083ACC19` (`Create a new coach`), `0x083ACA7F` (`Custom Player`), `0x083ACA8D` (`NICKNAME`) |
| Rink-name pool | `0x083AC94C`–`0x083AC9DE` | 7 names: Dukasana Pond, Squirrel Creek Shopping Ctr, Mr. Schinkel's Pool, Kissling Field, Rectangular Garden, Tech State University, Queen Flaky's Ice Castle |
| Custom nickname pool | `0x083ACAB0`–`0x083ACB49` | 15 presets, see §6.3 |
| Kid roster records | `0x08061C38`+ and `0x08064180`+ | pointer/name table; contains `BEVERLY`/`BACKSTOP`, `BUDDY`/`CHEQUE` and the `"SECRET WEAPON"` nickname at file `0x064558` |
| Coach name array | `0x030059B4` | stride `0x1B8` (440 bytes); 7 ASCII letters + NUL. The entry handler computes it as `0x03005870 + 0x144 + 440*index` (the `0x03005870` is the base of an adjacent u16 table, not the record base) |
| Name-entry append handler | `0x0800C174` | writes `'A' + 7*row + col` to `name[length]` (`0x0800C1E0`/`0x0800C1EC`), NUL-terminates and increments length `0x03000590`; caps at 7 with `cmp r0,#6` at `0x0800C1B8`; OK path calls save `0x0803A930` at `0x0800C2D4`; no comparison |
| Save/profile block | `0x03000978` | 488 bytes; byte 0 is a one's-complement checksum |
| Packed coach name | `0x030009CB` | `0x03000978 + 0x53`, 6 bytes: 5 bits/letter, 7 bits unused at the front, 6 spare bits at the end; `A=0` … `Z=25`, `31=space` |
| Name decoder (packed → ASCII) | `0x08037340` | writes 9 ASCII bytes to `0x03000B60`; only BL callers `0x0800BEFE`, `0x0800C08A`, `0x0800C2FC` |
| Name packer (ASCII → packed) | `0x080376F4` | packs into the save block; a second packer around `0x08038F80` uses the same bit layout for the other profile record |
| Save checksum/flush | `0x0803A930` | sums bytes `0x03000979`..+`0x1E7`, stores `~sum` at `0x03000978`, then calls the save/flush helper |
| Coach-screen draw routine | `0x08009D58`–`0x08009F70` | uses literal pool `0x08009F8C`–`0x08009FA0`, which contains `0x030059B4` at `0x08009F98` |
| Team-ranking loop over the same array | `0x0800A898`+ | reads stat bitfields at record `+0xE8`; does not read the name |
| Input polling (menus) | `0x0804EEA0`, `0x0803D70C` | reads `KEYINPUT` at `0x04000130`; per-player key words at `0x03005EE0`+ |
| Keypad register | `0x04000130` | 3 literal references in the ROM: `0x08019F8C`, `0x0803D764`, `0x0804EF24` |

### 4.1 Savestate ↔ RAM mapping (mGBA 0.10.5)

A savestate is a PNG whose `gbAs` chunk is a zlib stream of 397,312 bytes:

```
0x00000–0x19000  VRAM (0x18000) + palette/OAM/IO
0x19000–0x21000  IWRAM (0x03000000–0x03007FFF)
0x21000–0x61000  EWRAM (0x02000000–0x0203FFFF)
```

so `RAM 0x0300xxxx → state 0x19000 + xxxx`. The packed name at
`0x030009CB` is at state `0x199CB`; the save block `0x03000978` at `0x19978`.

## 5. Algorithm

### 5.1 Coach-name storage and display

The name is entered as ASCII into the current coach record:

```
name = 0x030059B4 + slot*0x1B8       # +0x1B8 = 440 bytes
name[0..6] = 'A'..'Z'                # up to 7, NUL padded
length counter = 0x03000590          # append refused when length > 6
row/col        = 0x0300058E / 0x0300058D
```

The entry handler reaches the same address as `0x03005870 + 0x144 + 440*index`;
`0x03005870` is the base of an adjacent u16 table and `+0x144` lands exactly on
`0x030059B4`.

On save, `0x080376F4` packs the letters into a 5-bit field:

```
name_value(c) = 0 if c == ' ' else c - 'A'      # 0..25, 31 = space
bitstream: 7 unused zero bits, then 7 * 5 bits, LSB-first per letter
packed[0..5] = the 48-bit little-endian bitstream
```

The inverse (`0x08037340`) is used only to draw the name:

```
v = ((b[0] >> 7) & 1) | ((b[1] & 0x0F) << 1)
... five bits per character, A=0, 31=' '
```

Verified against the live game: with `AIKANTR` in the coach slot, IWRAM
`0x030009CB` held `00 80 14 68 33 7E`, which decodes to `AIKANTR`; the save
checksum at `0x03000978` was `0xA5` and `~sum(bytes 1..0x1E7)` was also
`0xA5`.

### 5.2 Why there is no validator

This is the core of the negative result. The name is never compared to
anything:

* The 32-bit value `0x030059B4` occurs nine times in the ROM. One is the pool
  entry at `0x08009F98` used by the coach-slot screen routine. The other eight
  are pools in routines that index the same record array by `0x1B8` and read
  the stat dword at `+0xE8` (team ranking / draft order), not the name bytes
  at `+0`.
* The packed name has no literal pointer of its own. Every access to
  `0x03000978 + 0x53` is one of: the decoder `0x08037340`, the save packer
  `0x080376F4`, the second packer around `0x08038F80`, or a bitfield getter
  `0x0803AA74` for a different 6-bit field selected by the layout flag at
  `0x03000979` bit 0. None compares the name.
* The name-entry handler itself (`0x0800C174`) only appends a letter:
  `name[length] = 'A' + 7*row + col; name[length+1] = 0; length++`, with the
  length cap `cmp r0,#6` at `0x0800C1B8`. Its OK branch calls the save routine
  `0x0803A930` at `0x0800C2D4`; it never compares the typed value to anything.
* The decoder's three call sites all pass the returned ASCII pointer straight
  to the text routine `0x0802B694`. There is no `strcmp`/`strstr`/hash call on
  the name and no comparison loop against a ROM table.
* There is no name/string table in the ROM to compare against: the pun coach
  names of the PC build are absent in every encoding tried (raw ASCII,
  `ASCII-0x21`, `ASCII-0x20`, 5-bit packed at all eight bit offsets, and all
  256 constant-delta byte encodings).

A table of accepted strings therefore does not exist, and the accepted set is
empty independent of the 26^7 theoretical name space.

### 5.3 Save integrity is not a code check

`0x0803A930` computes a one's-complement checksum over the save block and
writes it at `0x03000978`. This checks the save data as a whole; it does not
validate a code and has no relation to the coach name beyond covering it as
one field among many. Verified on a live state (stored `0xA5`, computed
`0xA5`).

## 6. Tables

### 6.1 Complete menu tree

| Screen | Items |
|---|---|
| Title | Press Start |
| Main menu | PLAY NOW, SINGLE GAME, SEASON PLAY, PRACTICE, MULTIPLAYER, OPTIONS, CREDITS (7) |
| Play Now | PLAY, TEAM STRATEGY, OPTIONS (3) |
| Difficulty Level | EASY/MEDIUM/HARD; PERIOD TIME SET 2/4/6; FATIGUE ON/OFF; PENALTIES ON/OFF; OFF-SIDES ON/OFF; POWER-UPS ON/OFF; ROCK, PAPER, SCISSORS ON/OFF |
| Rink Select | 7 slots: 5 active, 2 `?` (locked) |
| Team Select | Eastern and Western conferences, 3 divisions each, 30 NHL teams total |
| Player Select | 12 kid cards per page + `CUSTOM`; `L`/`R` cycles, `START` random |
| Player Cards | `PICK ME?` YES/NO, five stat bars |
| Custom Player | NICKNAME, HAIR, HAIR COLOR, BODY, HEAD (all spinners; no text entry) |
| Season Play | 2 coach slots; NEW, COPY COACH, DELETE COACH; name keyboard; difficulty; rink; team; draft; save; matchup |
| Practice | 3-ON-1, AIR HOCKEY |
| Air Hockey options | EASY/MEDIUM/HARD; TIMER 05/07/10/15/OFF; SCORE 05/10/15/20/99; MULTI PUCKS ON/OFF |
| Multiplayer | HEAD TO HEAD, AIR HOCKEY (both end in a link wait) |
| Options | MUSIC, GRAPHIC FX, COMMENTARY, DISPLAY PLAYER NAME, AUTO SAVE (5 toggles) |
| Pause | RESUME, QUIT; QUIT GAME? YES/NO |

No row in any of these screens opens a password, cheat, debug, sound-test or
gallery screen.

### 6.2 Coach-name alphabet and length

* Alphabet: 26 letters `A`–`Z`. No digits, punctuation or space cell.
* Length: 1–7. The 8th and later presses are ignored (observed).
* The save format can represent 7 letters plus a spare 5-bit code (31=space),
  but the entry screen cannot produce a space.

### 6.3 Custom Player nickname presets (15)

`BIG DOG`, `BULLDOZER`, `BUTTERFINGERS`, `CRUSHER`, `CUTIE-PIE`,
`FANCY PANTS`, `MELVIN`, `NOODLES`, `ROCKET`, `SCAREDY CAT`,
`SLOPPY JOE`, `SWEET POTATO`, `SWEETNESS`, `THE GENERAL`, `TUFF SKIN`.

These are selected with Left/Right; no keyboard opens. None of the published
secret-player names is in this list.

### 6.4 Rink names and unlock state

The text bank contains seven rink names; Rink Select shows five active and two
`?` slots. The two GBA-specific published unlockables are:

| Rink | Published GBA unlock condition |
|---|---|
| Mr. Schinkel's Pool | Win Mr. Clankey's Cast-Iron Cup in Season Mode |
| Tech State University | Make the playoffs in Season Mode |

These are progression rewards; they are not entered as codes. The selected
slot's label was read as `RECTANGULAR GARDEN`; the remaining active slot names
are not individually confirmed because the five icons are unlabelled until
selected, but they must be five of the seven names in the text pool, leaving
the two table entries above as the locked pair.

### 6.5 Published codes and what happens to them

| Published code | Source | GBA disposition |
|---|---|---|
| `Ikan Trace` | GameFAQs/VGChartz/SuperCheats, labelled **PC** | Not expressible: 10 chars incl. space; coach field is 7 × A–Z. Truncation `IKANTRC` tested; no special team |
| `Ivanna Tipe` | same | Not expressible (space; 11 chars) |
| `Mike McMeeting` | same | Not expressible (space; 14 chars) |
| `Beverly Backstop` | GameFAQs GBA page, section labelled **PC** | Not expressible: no player-name text entry; Custom Player is a 15-preset spinner |
| `Buddy Cheque` | same | Not expressible |
| `Lemon Boy` | same | Not expressible |
| Mr. Schinkel's Pool | GameFAQs **Rinks (GBA)** | Progression unlockable, not a code |
| Tech State University | GameFAQs **Rinks (GBA)** | Progression unlockable, not a code |

The GBA page's two code sections are explicitly headed `PC`; the only
GBA-specific contribution is the rink unlockables. That matches the ROM: it
contains neither the pun names nor a player-name keyboard.

Published sources checked: GameFAQs GBA page
`gamefaqs.gamespot.com/gba/915416-backyard-hockey/cheats` (direct fetch 403;
text recovered from search snippets and the archived/duplicated PC pages),
Neoseeker and CheatCC Backyard Hockey PC cheat pages, SuperCheats, TCRF's
`Backyard_Hockey` page (unused sounds only), and the GBA manual PDF at
`videogamemanual.com` (scanned; the coach-name limit is visible there and was
confirmed in-game). No GBA-specific password or button-code list was found on
any of them.

## 6b. Enumeration

### 6b.1 Space definition

| Surface | Alphabet / format | Length | Representable values | Accepted values |
|---|---|---|---:|---:|
| Season coach name (UI) | 26 letters `A`–`Z` | 1–7 | `Σ26^k (k=1..7) = 8,353,082,582` | **0** |
| Season coach name (save field) | 5-bit codes, `A=0`..`Z=25`, 31=space | 7 | `26^7 = 8,031,810,176` (2^41 bit patterns) | **0** |
| Custom Player nickname | 15 fixed presets | — | 15 | 15 (presets, not codes) |
| Button-code sequences | 10-button engine alphabet (if a table existed) | 3–29 | not instantiated | **0** tables |
| Published coach/player codes | PC strings | 9–16 incl. spaces | not expressible on GBA | **0** |

There is no checksum, key, XOR mask, permutation or generator for the coach
name. The only arithmetic in the path is the 5-bit packing and the unrelated
save-block checksum. The accepted space is therefore **empty**: no table
exists, and the name is not compared to anything.

### 6b.2 Novel codes

**None exist, and none can be minted**, because the accepted set is empty.
This is not an incomplete search: it follows from the absence of any
name-comparison path (§5.2). The equivalent deliverable for this engagement is
the negative proof itself, bounded by the search counts below and the rejected
inputs in §6b.3.

### 6b.3 Bounds proven by rejection

| Test | Why it is outside any possible GBA code | Observed result |
|---|---|---|
| `IKANTRACE` (9 chars) | Field caps at 7 letters; extra presses are ignored | Display stays at 7 characters (`shots/17_ikantrace_c.png`) |
| `IKANTRC` (7 chars, truncated published name) | No comparator and no table; truncated value is an ordinary name | Coach created, season starts, same 30 NHL teams, no special team/rink (`shots/53_ikantrc_c.png`, `56_teamlist_c.png`) |
| SPACE in a coach name | Keyboard has no space cell | Impossible to input (`shots/15_nameentry_c.png`) |
| `BEVERLY BACKSTOP` as a player name | No player-name text entry exists | Custom Player exposes a 15-item nickname spinner only (`shots/98_custom2_c.png`, `nick_A.png`, `nick_B.png`) |
| `Up Up Down Down A` at matchup | Not in any GBA table (no button table) | Screen accepted normally; no effect (`shots/102_uudda_c.png`, `103_aftercode_c.png`) |
| Konami at title/main | No button table and no hidden menu | Title/main unchanged (`shots/106_konami_title_c.png`) |
| `L + R + Start` at main | No debug gate | Normal PLAY NOW transition (`shots/108_lrstart_c.png`) |
| 8th/9th letter | Length cap | Dropped at 7 |

The player-name and coach-name negatives bound the two published code classes
from both directions: a string can be well formed (or a valid truncation) and
still have no effect, and a published string can be impossible to express at
all.

### 6b.4 Text/table search counts

* `strings -n 4` lines: **24,532**.
* Case-insensitive whole-ROM counts: `password` **0**, `passcode` **0**,
  `cheat` **0**, `debug` **0**, `unlock` **0**, `goodie` **0**, `code` **0**,
  `hidden` **0**, `sound test` **0**. `secret` **1** = roster nickname
  `"SECRET WEAPON"` at `0x064558`; `easter` **1** = the word `EASTERN` in the
  conference label.
* Published literals searched raw, as `ASCII-0x21`, as `ASCII-0x20`, as
  lowercase, as 5-bit packed at all 8 bit offsets (LSB- and MSB-first), and as
  all 256 constant-delta byte encodings: `IKANTRACE`, `IVANNA TIPE`,
  `MIKE MCMEETING`, `LEMON BOY`, `BEVERLY BACKSTOP`, `BUDDY CHEQUE`,
  `BUDDY CHECK` — **no hits**.
* Button-letter table scan: NUL-terminated runs of `u d l r a b s t m v` of
  length 3–9 = **2** (`dub` at `0x121051`, `bdv` at `0x144850`); none has the
  shape of a code table. Uppercase equivalents = 111 runs, all name/data
  fragments (e.g. `STUART`, `STAR`, `LULU`), and **zero** contain three or more
  of `U/D/L/R` followed by `A`.
* `u16` key-mask arrays: runs of ≥4 active-high masks (`1,2,4,...,0x200`) =
  9 hits, all in graphics/table data (e.g. `0x65EA2`, `0x33E7A6`, `0x3AD07A`);
  runs of ≥3 active-low single-button masks (`0x3FE,0x3FD,...`) = 9 hits, all
  sine/cosine-style numeric tables around `0x113374`/`0x115C28`. No run matches
  a plausible cheat sequence, and none of the hits sits in a sequence-table
  structure.
* Original documented Backyard Basketball sequences (`uudda`, `dudua`,
  `ssbbt`, `uulrba`, and the 13 others) are all absent as literals. The
  Basketball table offset `0x133E90` is not a table in this ROM either: the
  bytes there are zero/graphics data, and no 17×10 ASCII block exists anywhere
  in the 4 MiB.

### 6b.5 Hidden/debug menu search

* No `debug`/`cheat`/`unlock` strings and no ASCII text that labels a
  developer/cheat menu anywhere in the ROM.
* Every menu in §6.1 was opened; no extra row appeared. The title and main
  menu were additionally exercised with the Konami sequence and
  `L+R+Start`; neither changed the screen or opened a menu.
* The game has no password screen to hide: no password/passcode strings, no
  entry UI, and the only text field (coach name) has no comparator.

### 6b.6 Unlockables (progression, not codes)

Rink Select shows two `?` slots; the two GBA-specific published unlockables
are Mr. Schinkel's Pool (win the Cast-Iron Cup) and Tech State University
(make the playoffs). These are earned in Season Mode and are outside the
code/password space; they are listed here so the in-game unlockable surface is
accounted for.

## 7. Validation evidence

**Observed (emulator screenshots / memory reads)**

* Every menu listed in §6.1 was opened on `:158`; screenshots referenced in
  §3.3.
* Coach keyboard has 26 letters, OK and DELETE; typing 9 letters leaves 7
  (`shots/17_ikantrace_c.png`).
* `IKANTRC` created a coach, entered a season, and reached Team Select; both
  conferences showed the normal 15-team NHL lists and no special team
  (`shots/53_ikantrc_c.png`, `121_teamsel_single_c.png`, `122_west_c.png`).
* Custom Player exposes the 15-name spinner and no text field
  (`shots/98_custom2_c.png`, `nick_A.png`, `nick_B.png`).
* `Up Up Down Down A` at the season matchup, the Konami sequence at title and
  main, and `L+R+Start` at main produced no cheat/debug state
  (`shots/102_uudda_c.png`, `106_konami_title_c.png`, `108_lrstart_c.png`).
* IWRAM `0x030009CB` held `00 80 14 68 33 7E` for `AIKANTR`; the save
  checksum at `0x03000978` was consistent (`0xA5` stored / `0xA5` computed).

**Derived (instruction/table analysis)**

* No name comparator: the entry handler `0x0800C174` only appends
  `'A' + 7*row + col` and calls the save routine on OK; the only ASCII-name
  literal path is the coach-screen draw routine; the packed name is only read
  by the decoder and save packer (§5.2).
* The packed-name bit layout (`5 bits/char`, start bit 7, `A=0`, 31=space) and
  the save checksum routine.
* The 7-letter cap and the 26-letter alphabet from the input screen and from
  the UI behaviour.
* Empty button-code table space: no letter table, no mask array, no
  reference to either as a table.

**Inferred**

* The two `?` rink slots are Mr. Schinkel's Pool and Tech State University,
  from the seven-name text pool and the published GBA unlockables; the two
  locked slots themselves were observed, while the unlock event is documented
  by the published GBA list.
* The header checksum word at `0xBE` was zeroed by a patch/trim rather than a
  deliberate developer setting; the ROM boots and every analysed table is
  consistent with a retail build.

## 8. Unknowns

* The exact origin of the zero header checksum at `0xBE` (patch, trim or dump
  artefact).
* Whether a prototype or a different regional build ever shipped a coach-name
  or button-code table; this image contains neither.
* The exact moment the two locked rinks become selectable during a season;
  the published GBA conditions and the locked-slot UI agree, but the unlock
  message itself is not part of the observed evidence set.
* The per-slot mapping of each `?` to a rink name (each slot is unlabelled
  until selected; the mapping is inferred from the seven-name pool and the
  published pair).

## 9. Tooling

* mGBA 0.10.5 SDL (`/usr/games/mgba`), `-3`, `SDL_AUDIODRIVER=dummy`.
* Xvfb `:158` (1024×768×24), openbox, `xdotool`, `scrot`/`import`,
  ImageMagick.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000
  -M force-thumb`.
* Python 3 (`struct`, `zlib`, `hashlib`, `re`), Capstone for the immediate
  scans.
* Work directory `/tmp/opencode/bhockey`:
  * `p0.py` — size/header/logo/hash identity.
  * `repro.py` — one-shot reproducer (identity, keyword counts, savestate
    name decode, save checksum). Example:
    `python3 repro.py "/mnt/gbacheats/roms/Backyard Hockey/Backyard Hockey.ss5"`
    prints `packed name bytes 00801468337e decoded 'AIKANTR'`.
  * `scan1.py`, `scan2.py`, `packsearch.py`, `scanbtn.py`, `blscan.py` —
    string/packed-name/button-mask/BL scans.
  * `key.py`, `grid.py` — xdotool input helpers; `shot.sh` — screenshot/crop.
  * Savestates `Backyard Hockey.ss1`–`.ss6` (menu, coach slots, name entry,
    matchup) in the ROM folder; they are emulator artefacts, not results.

Minimal reproducer (identity + name field):

```python
import struct, zlib, hashlib
rom = open("Backyard Hockey.gba", "rb").read()
print(len(rom), rom[0xA0:0xAC], rom[0xAC:0xB0], rom[0xBC])
print(hashlib.sha256(rom).hexdigest())

# savestate gbAs chunk -> IWRAM
d = open("Backyard Hockey.ss5", "rb").read()
i = 8
while i < len(d):
    n = struct.unpack(">I", d[i:i+4])[0]; t = d[i+4:i+8]
    if t == b"gbAs":
        ram = zlib.decompress(d[i+8:i+8+n]); break
    i += 12 + n
name = ram[0x19000 + (0x030009CB - 0x03000000):][:6]
bits = [(b >> k) & 1 for b in name for k in range(8)]
print("".join(" " if (v := sum(bits[7+5*j+k] << k for k in range(5))) == 31
              else chr(65 + v) for j in range(7)))
```

Legal note: no ROM, extracted graphics, music or other copyrighted assets are
redistributed here. Only hashes, addresses, algorithms, the short developer
strings needed to identify the menus, and my own screenshots/notes are
published.
