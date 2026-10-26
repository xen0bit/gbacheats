# Ballistic: Ecks vs. Sever (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Ballistic: Ecks vs. Sever/Ballistic: Ecks vs. Sever.gba` |
| Size | 8,388,608 bytes (0x800000) |
| Header title (0xA0) | `BALLISTIC EC` |
| Game code (0xAC) | `AEEE` |
| Maker code (0xB0) | `6L` |
| Main unit / device | 0x00 / 0x00 |
| Software version (0xBC) | 0x00 |
| Complement check (0xBD) | 0x80 (computed 0x80 — valid) |
| Header word 0xBE | 0x0000 (reserved; normal) |
| Entry word (0x00) | `0xEA00002E` (ARM branch to 0x080000C0) |
| MD5 | `95abf2bd63a3758b6d86e278ee1fca6e` |
| SHA-1 | `d66a33c71466ffb6558ba6381156d14f73c8c6d8` |
| SHA-256 | `f4ce2962ef8e9a87d487787a5aa424cbf6357dde04964f20b1562ef718afabd9` |

Phase 0 scan: the complete 156-byte Nintendo logo occurs **exactly once**, at
file offset `0x4` (header base `0x0`). There is no second header, no shell and
no boot selector: a single 8 MiB image. The reset vector is the stock GBA crt0
(IRQ stack `0x03007FA0`, user stack `0x03007EE0`, main at `0x08001A55`), the
logo is untouched, and the complement check recomputes to the stored value, so
**no patch, trainer or intro is present**.

`file` identifies the image as `"BALLISTIC EC" (AEEE6L, Rev.00)`. This is the
2002 US release titled *Ballistic: Ecks vs. Sever* — the sequel that GameFAQs
catalogs as **“Ballistic: Ecks vs. Sever II”** (“Also known as: Ballistic:
Ecks vs. Sever (US)”). That distinction matters: the widely copied **EX…/S…**
level-password list belongs to the 2001 game *Ecks vs. Sever* and is rejected
by this ROM (see §6b).

Saving: mGBA leaves `Ballistic: Ecks vs. Sever.sav` at **0 bytes** after boot
and gameplay. Progress is carried by passwords; there is no SRAM/Flash/EEPROM
write in the password path.

## 2. Executive summary

* The title menu has four icons: **SINGLE / MULTI / PASSWORD / OPTIONS**. The
  third icon opens a code-entry screen with the 26-letter alphabet
  `ABCDEFGHIJKLMNOPQRSTUVWXYZ`, an entry field, and `ENTER` / `DELETE`
  (`0x080F37F8`, screen built from the widget table at `0x080274CC`).
* The screen recognises **exactly 29 strings**, checked by two independent
  fixed tables; there is no checksum, no arithmetic and no generator:
  * **9 cheat codes** — compared against a 9 × 12-byte table at
    `0x080F648D` by the function at `0x08026C24`. A match sets one bit in the
    u32 cheat-flag word at **`0x02005270`** and prints **`CHEAT ACTIVATED`**.
  * **20 level codes** — compared against a 20 × 16-byte table at
    `0x080F632D` inside the A-button handler at `0x08026D54`
    (loop `0x08026E68`–`0x08026EFA`). A match writes a **level id** to
    `0x02000084`, selects the campaign (`0x02000052 = 0x8001` Ecks /
    `0x8002` Sever), and starts the mission (`0x0802D248`).
* Input is case-folded to lower-case, restricted to `a`–`z`, and **capped at
  9 characters** (append guard `cmp r0,#8; bhi` at `0x080271E0`). A rejected
  submission prints **`INCORRECT PASSWORD`** and leaves the text in place.
* The two tables are complete and closed: every accepted string is one of the
  29, so the accepted space is exactly 29 of
  **5,646,683,826,134** possible non-empty inputs (26 symbols, 1–9 chars).
  Consequently **no unpublished string exists** for this ROM — a bounded
  negative proven in §6b, not an assumption.
* What was *not* published anywhere is the model around the strings: the two
  tables, the 9-bit cheat flag word and bit assignment, the level ids
  `1…10` / `21…30`, the character word, the 9-character cap, and the fact
  that a level code can be combined with all nine cheats. This report supplies
  that model and the in-game evidence.
* Published-list verification: the 29 strings match the GameFAQs “Ballistic:
  Ecks vs. Sever II” cheat/password list (archived 2022-02-04) and the IGN
  page (archived 2017-03-23) **exactly**, including the cheat effects. The
  EX…/S… list for the 2001 game is disproved in-emulator: `EXTREME` and the
  other first-game words are rejected, and `SACROSANCT` cannot even be typed
  (10 chars > cap).
* Novel artefact delivered: the **all-cheats state** (`0x02005270 = 0x1FF`,
  all nine bits set in one session, read from RAM through the GDB stub) used
  with the mission-9 password **`SPECTRE`**. The resulting mission shows the
  combined effect (HUD 100 health, 100 ammo that does not drop when firing,
  and the three-weapon strip). No published list documents the combination.

## 3. How to reproduce

Emulator: mGBA 0.10.5 (SDL), 3× scale, headless `Xvfb :164` + `openbox`,
`SDL_AUDIODRIVER=dummy`.

Default mGBA SDL keymap used: **A = `x`**, **B = `z`**, **L = `a`**,
**R = `s`**, **Start = `Return`**, **Select = `BackSpace`**, D-pad = arrows.
Save state slot *n* with **Shift+F*n***, load with **F*n***.

Exact path:

1. Boot → BAM logo → `BALLISTIC / ECKS vs SEVER` title → **Start**.
2. Main menu (icon row): **SINGLE / MULTI / PASSWORD / OPTIONS**.
   Press **Right ×2** from SINGLE to reach PASSWORD, then **A**.
3. Password screen:
   * **Left/Right** move the letter cursor `A…Z` (wraps).
   * **A** appends the highlighted letter (max 9; the 10th press is ignored).
   * **Down** moves focus to `ENTER`; **Down** again to `DELETE`.
   * **A** on ENTER submits; **A** on DELETE erases one character.
   * **Up** returns to the letter row; **B** leaves the screen.
   * Success (cheat) → `CHEAT ACTIVATED`; success (level) → briefing /
     objectives; failure → `INCORRECT PASSWORD`.
4. In-game **Start** opens the pause menu: `CONTINUE / OBJECTIVES / SOUND /
   CONTRAST / RESTART LEVEL / EXIT GAME`. The cheat bits are plain EWRAM at
   `0x02005270` and the ROM writes no save, so they persist for the life of the
   boot (observed: password screen → mission) and are lost on power cycle.

Recommended test codes: `DEATHWISH` (cheat), `TIGER` (Ecks level 5),
`RAVEN` (Sever level 2), `EXTREME` (must be rejected).

### 3.1 Input-timing note (reproducibility)

The menu edge detector can miss or double a synthetic keypress under load.
Every key press in the successful runs used a 0.11–0.20 s hold with a
0.11–0.30 s gap. The letter cursor is deterministic and wraps, so a code can
be typed open-loop as “move `(target-current) mod 26` steps right, then A”.
One long session produced a single spurious rejection of `DEATHWISH` while the
screen showed the correct text; it was not reproducible (the same code was
accepted before and after, and the comparator is stateless — see §5), so it is
attributed to a dropped input edge, not to game logic.

### 3.2 Static search counts (bounded negative work)

| Search | Scope | Result |
|---|---|---|
| ASCII runs `len >= 4` | whole 8 MiB | 37,928 |
| runs containing `password` | whole ROM | 4 — `password errata`, `incorrect password`, `password`, `password:` (all UI) |
| runs containing `cheat` | whole ROM | 30 — 3 × “cheat activated” (IT/DE/EN) + 27 × “Cheat uncovered!” (EN/DE/IT) |
| runs containing `code` | whole ROM | 9 — the French “Code de triche d…” message bank |
| runs containing `secret` | whole ROM | 7 — mission prose only (“Find the secret entrance…”, “top secret information…”) |
| `debug`, `unlock`, `passcode`, `level select`, `sound test` | whole ROM | **0** |
| literal search for the 22 level words + 6 MP words of the 2001 game | whole ROM | **0 hits** for every string |
| literal search for the 29 accepted strings | whole ROM | only the 20 level names (one table) and the 9 cheat names (one table + 27 message copies) |
| all 32-bit literals in code pointing into ROM | file `0x0`–`0x100000` | 3,619 distinct targets; 49 fixed-stride word-table candidates; exactly **2** are code tables |
| 2-byte runs of ≥5 key masks (0x001…0x200) | whole ROM | 3,496 candidates, dominated by audio waveform/graphics data; none referenced by the menu/password code |
| KEYINPUT (`0x04000130`) literal reads | whole ROM | one executed site: `0x0802EBE4` (the other five hits are literal-pool/data occurrences) |

### 3.3 Web recon

| Source | Content | Used how |
|---|---|---|
| GameFAQs 561533, “Ballistic: Ecks vs. Sever II” cheats (archived 2022-02-04) | complete 29-entry list: 9 cheat codes + 20 level codes | every string checked against the ROM tables; all 29 present, no typos |
| GameFAQs 537159, “Ecks vs. Sever” (2001) cheats (archived 2022-02-09) | 11 Ecks `EX…` + 11 Sever `S…` level words, 6 MP words | literal search in this ROM: 0 hits; `EXTREME` entered and rejected |
| IGN cheats wiki (archived 2017-03-23) | partial list (Raven, Firefly, covey, tiger + 7 cheat codes) | agrees with GameFAQs; missing `hornblow`/`mybigun` and most level codes |
| TCRF “Ecks vs. Sever” | only CodeBreaker codes to view early splash screens (memory-edit, out of scope) | no in-game password list |
| VGChartz / general search | no password list for this title (discussion only) | no additional codes to verify |

GameFAQs and IGN return 403 to direct fetches; the archived snapshots above
were fetched through `web.archive.org`.

## 4. Address map

All addresses are ROM addresses (file offset + `0x08000000`) for this exact
revision. RAM addresses are unbanked EWRAM addresses.

### Password screen

| Address | Role |
|---|---|
| `0x08020004` … | front-end screen framework (state tables, fades, text) |
| `0x08026C24` | **cheat-code matcher**: input `0x0200D450` vs 9 × 12 table |
| `0x08026C38` | cheat match hit: `*0x02005270 \|= 1 << index`, return 1 |
| `0x08026C94` | screen input handler (delete / cursor / focus) |
| `0x08026D54` | screen input handler containing the **level-code matcher** |
| `0x08026E40`–`0x08026EFA` | level compare loop (20 × 16-byte table, 10 bytes compared) |
| `0x08026F04`–`0x08026F30` | level accept: character word, level id, call starter |
| `0x08026F44` | ENTER path: calls `0x08026C24`; failure → text record `0x080F365C` |
| `0x08026F94` | success path: text record `0x080F3728` (`CHEAT ACTIVATED`) |
| `0x08026CF8`–`0x08026D02` | DELETE: `len--`, `buffer[len] = 0` (length at `0x0200017C`) |
| `0x080271E0` | append guard: `cmp r0,#8; bhi` → **max 9 characters** |
| `0x080274CC` | widget table for the password screen (references `0x080F37E4`) |
| `0x0802D248` | **level starter / dispatcher** (jump table at `0x0802D27C`) |
| `0x0802DF38` | an unreferenced duplicate of the level matcher (no BL/pointer to it found) |
| `0x0802EBE4` | the game's **only** KEYINPUT read: `held = ~KEYINPUT & 0x3FF` |

### Data

| ROM address | Length | Contents |
|---|---|---|
| `0x080F37F8` | 27 | `abcdefghijklmnopqrstuvwxyz\0` (screen alphabet / glyph order) |
| `0x080F3FCC` | 9 | `password` (screen title, EFIGS record) |
| `0x080F3FF4` | 10 | `password:` (entry prompt) |
| `0x080F3714` | 19 | `incorrect password` (rejection text) |
| `0x080F37D4` | 16 | `cheat activated` (acceptance text) |
| **`0x080F632D`** | 320 | **level-code table**, 20 × 16 bytes (see §6.1) |
| **`0x080F648D`** | 108 | **cheat-code table**, 9 × 12 bytes (see §6.2) |
| `0x08100C84` | 9 × 28 | `Cheat uncovered!§CODE` messages (EN; also DE/IT/ES/FR banks at `0x1053EC`, `0x107680`, …) — **not used by the password screen** |
| `0x0802D27C` | 29 × 4 | level-id dispatch table (only ids 0, 4, 7, 20, 24, 28 are special; the rest share the generic path at `0x0802D314`) |

### RAM

| Address | Meaning |
|---|---|
| `0x0200D450` | code input buffer (10 bytes read by both comparators; max 9 written) |
| `0x0200017C` | u32 entry length (incremented on append, decremented on DELETE) |
| **`0x02005270`** | **u32 cheat flag word** — bit *n* = cheat table entry *n* |
| **`0x02000084`** | u16 **level id** (1–10 Ecks, 21–30 Sever) |
| `0x02000052` | u16 campaign selector: `0x8001` = Ecks, `0x8002` = Sever |
| `0x0200C480` | u16 mirror of the selector (0 = Ecks, 1 = Sever) |

Literal pools were read with `struct.unpack_from("<I", …)`: e.g. the cheat
matcher's base is `0x02004E00` (`0x08026C50`), and the flag word is
`base + 0x470 = 0x02005270`.

## 5. Algorithm

### 5.1 Cheat matcher (`0x08026C24`)

```
def match_cheat(buf):                    # buf = NUL-terminated, max 9 chars
    if buf[0] == 0: return -1            # empty entry: no message
    for i in range(9):                   # table 0x080F648D, stride 12
        if bytes(buf[k] for k in range(10)) == TABLE_CHEAT[i][0:10]:
            *(u32*)0x02005270 |= (1 << i)
            return 1
    return 0
```

The comparison is 10 raw bytes (the 9-character maximum plus the terminator),
so only the exact spellings match. There is no state: the function reads only
the buffer and the table, and ORs one bit into the flag word.

### 5.2 Level matcher (inside `0x08026D54`)

```
def match_level(buf):                    # called from the A/ENTER handler
    for i in range(20):                  # table 0x080F632D, stride 16
        if bytes(buf[k] for k in range(10)) == TABLE_LEVEL[i][0:10]:
            if i <= 9:
                ip = i + 1                   # Ecks ids 1..10
                *(u32*)0x02000052 = 0x00008001
                *(u16*)0x0200C480 = 0
            else:
                ip = i + 11                  # Sever ids 21..30
                *(u32*)0x02000052 = 0x00008002
                *(u16*)0x0200C480 = 1
            *(u16*)0x02000084 = ip
            start_level()                    # 0x0802D248
            return
    match_cheat(buf)                         # ENTER path
```

`start_level()` reads the id from `0x02000084` and dispatches through the
jump table at `0x0802D27C`; ids above 28 take the generic path at
`0x0802D314`. The observed relation is

* Ecks: mission = id + 1 (ids 1…10 → missions 2…11),
* Sever: mission = id − 19 (ids 21…30 → missions 2…11).

Mission 1 has no password (it is entered from the character-select/campaign
flow).

### 5.3 Input model

```
alphabet = "abcdefghijklmnopqrstuvwxyz"      # 26 symbols, upper-case on screen
length <= 9
append: if length <= 8: buf[length++] = alphabet[cursor]
delete: if length > 0: length--; buf[length] = 0
```

No checksum, substitution, permutation or key exists anywhere in the path.

## 6. Tables

### 6.1 Level codes (`0x080F632D`, 20 × 16 bytes, lower-case, NUL padded)

| idx | code | level id | campaign | mission | published as |
|---:|---|---:|---|---:|---|
| 0 | `smokey` | 1 | ECKS | 2 | Ecks Level 2 |
| 1 | `butterfly` | 2 | ECKS | 3 | Ecks Level 3 |
| 2 | `covey` | 3 | ECKS | 4 | Ecks Level 4 |
| 3 | `tiger` | 4 | ECKS | 5 | Ecks Level 5 |
| 4 | `hornet` | 5 | ECKS | 6 | Ecks Level 6 |
| 5 | `litterbug` | 6 | ECKS | 7 | Ecks Level 7 |
| 6 | `mustang` | 7 | ECKS | 8 | Ecks Level 8 |
| 7 | `spectre` | 8 | ECKS | 9 | Ecks Level 9 |
| 8 | `nimrod` | 9 | ECKS | 10 | Ecks Level 10 |
| 9 | `spooky` | 10 | ECKS | 11 | Ecks Level 11 |
| 10 | `raven` | 21 | SEVER | 2 | Sever Level 2 |
| 11 | `firefly` | 22 | SEVER | 3 | Sever Level 3 |
| 12 | `bulldog` | 23 | SEVER | 4 | Sever Level 4 |
| 13 | `dragon` | 24 | SEVER | 5 | Sever Level 5 |
| 14 | `loudmouth` | 25 | SEVER | 6 | Sever Level 6 |
| 15 | `stinger` | 26 | SEVER | 7 | Sever Level 7 |
| 16 | `nail` | 27 | SEVER | 8 | Sever Level 8 |
| 17 | `zorro` | 28 | SEVER | 9 | Sever Level 9 |
| 18 | `xray` | 29 | SEVER | 10 | Sever Level 10 |
| 19 | `reddog` | 30 | SEVER | 11 | Sever Level 11 |

The 20 names are also referenced by a front-end data table at `0x0802BD8C`
(which walks the same 16-byte records — consistent with a multiplayer
bot/name list), and the password screen reuses them as level codes. That is
why they read as callsigns rather than as the words used by the 2001 game.

### 6.2 Cheat codes (`0x080F648D`, 9 × 12 bytes) and flag bits

| idx | code | bit | mask | published effect | observed here |
|---:|---|---:|---:|---|---|
| 0 | `deathwish` | 0 | 0x001 | invincibility | flag bit observed; effect not isolated |
| 1 | `bigpocket` | 1 | 0x002 | unlimited ammo | **observed**: ammo 100, unchanged after 5 shots |
| 2 | `tooledup` | 2 | 0x004 | all weapons | **observed**: three-weapon HUD strip vs one without cheats |
| 3 | `coldfeet` | 3 | 0x008 | enemies frozen | flag bit observed; effect not isolated |
| 4 | `oohstopit` | 4 | 0x010 | one-hit kills | flag bit observed; effect not isolated |
| 5 | `mybigun` | 5 | 0x020 | rapid fire (Neosterd) | flag bit observed; effect not isolated |
| 6 | `acmebangs` | 6 | 0x040 | bigger explosions | flag bit observed; effect not isolated |
| 7 | `hornblow` | 7 | 0x080 | alternate sound effects | flag bit observed (audio not captured) |
| 8 | `doyoucme` | 8 | 0x100 | invisibility / enemies ignore you | flag bit observed; effect not isolated |

Each accepted cheat writes only its own bit (`0x02005270` starts at 0 in a
fresh session); entering all nine yields exactly `0x000001FF`. The order of the
`Cheat uncovered!§CODE` message bank (`0x08100C84`: DOYOUCME, HORNBLOW,
ACMEBANGS, MYBIGUN, OOHSTOPIT, COLDFEET, TOOLEDUP, BIGPOCKET, DEATHWISH) is
the reverse of the table/bit order.

### 6.3 Screen and message IDs

* Title `password` = `0x080F3FCC`; prompt `password:` = `0x080F3FF4`.
* Rejection record = `0x080F365C` → `incorrect password` (`0x080F3714`).
* Cheat acceptance record = `0x080F3728` → `cheat activated` (`0x080F37D4`).
* EFIGS index at `0x0200D968` × 20 bytes selects the language record; the
  five variants are Spanish, Italian, German, French and English.

## 6b. Enumeration

### Space definition

* Alphabet: 26 symbols (`a`–`z`; the screen shows `A`–`Z`, the buffer holds
  lower-case). No digits, space or punctuation; the row is exactly 26 cells.
* Length: 1 to **9** characters. The append path checks `length <= 8` before
  writing, so a 10th character is silently ignored (verified with
  `SACROSANCT`: the field stops at `SACROSANC`).
* No checksum and no generator: acceptance is membership in one of two fixed
  tables. The comparator is closed: 9 cheat entries and 20 level entries.
* Total possible non-empty strings:
  `26 + 26² + … + 26⁹ = 5,646,683,826,134`.
* Accepted strings: **29** (9 + 20), i.e. 0.0000000005 % of the space.

### Published set vs. this ROM

The 29 strings are exactly the list published for this US release (GameFAQs
“Ballistic: Ecks vs. Sever II” cheats page, archived 2022-02-04; IGN cheats
page, archived 2017-03-23). All were checked against the ROM tables
byte-for-byte; no published typo was found.

The *other* list — the 2001 game's `EXTREME / EXCITE / … / EXONERATE` and
`SEVERE / SURVIVE / … / SACROSANCT` words, plus multiplayer passwords such as
`VULNERABLE / VORACIOUS / VENDETTA` — belongs to *Ecks vs. Sever* (2001) and
does not exist in this image (0 literal hits for all 28 strings). Two were
entered in-emulator: **`EXTREME` → INCORRECT PASSWORD** and
**`SACROSANC` (the 9-char truncation of `SACROSANCT`) → INCORRECT PASSWORD**.
The multiplayer words are unenterable here for the same reason: this ROM has
no multiplayer password prompt at all (the only text-entry screen is the
main-menu PASSWORD screen; see §7).

### Generated artefact (not in any published list)

No unpublished *string* can be generated, because the accepted set is the two
tables exactly (see “Bounds”). What is generated and unpublished is the
**state combination**:

| Artefact | Value | In-game proof |
|---|---|---|
| all nine cheat flags in one session | `0x02005270 = 0x000001FF` | GDB log `SUBMIT flags=0x1ff`, `CHEATSET … value_after=0x1ff`; screenshots `v_*.png` |
| all cheats + Ecks mission 9 | `SPECTRE` with flags `0x1FF` | objectives “FOLLOW KAOS THROUGH THE SUBWAY / AVOID CIVILIAN CASUALTIES” → gameplay HUD 100 health, **ammo 100 that does not decrease after five shots**, three-weapon strip (`v_spectre_start.png`, `w1.png`, `w2.png`) |

No published source documents the simultaneous activation of all nine cheats,
nor the composition of a selected mission with the full flag word; the
individual effects in §6.2 are published, the flag model and the combination
are not.

### Bounds proven by rejection

Every input below was typed on the PASSWORD screen and submitted with ENTER.

| Input | Why it must fail | Observed result |
|---|---|---|
| `EXTREME` | published for the 2001 game; not in either table | `INCORRECT PASSWORD` (`x2.png`) |
| `SACROSANC` | 9-char truncation of `SACROSANCT`; not in either table | `INCORRECT PASSWORD` (`x4.png`) |
| `SACROSANCT` | 10 characters; the cap refuses the 10th | field stops at `SACROSANC` (`x3.png`) |
| `TIGEH` | one letter changed from the valid `TIGER` | `INCORRECT PASSWORD` (`zb.png`) |
| `SPOOK` | prefix of the valid `SPOOKY` | `INCORRECT PASSWORD` (`x7.png`) |
| `DEATHWISX` | one letter changed from the valid `DEATHWISH` | `INCORRECT PASSWORD` (`x5.png`) |

Structural bounds: the alphabet offers only `A`–`Z` (no way to type digits,
spaces or punctuation), and the entry field accepts at most 9 letters. The
code paths are exhaustive: the cheat matcher iterates `i = 0…8`, the level
matcher `i = 0…19`, and both compare 10 bytes including the terminator, so
neither a prefix, a suffix nor a case variant can match.

## 7. Validation evidence

### Observed (emulator)

* Full menu walk: title → four-icon main menu → SINGLE → Ecks/Sever portrait
  select → campaign briefing → in-game HUD → pause menu (6 items) → options
  submenu (contrast / GBA setup / left-right hand / music / FX) → PASSWORD
  screen → MULTI (link “CONNECTING… / WAITING FOR CONNECTION”).
* Password screen: 26-letter row, `ENTER`, `DELETE`, 9-character cap,
  case-folded display (`deathwish` shown as `DEATHWISH`), rejection and
  acceptance messages.
* All 9 cheat codes entered; each produced `CHEAT ACTIVATED` and set its bit
  (`v_deathwish.png` … `v_doyoucme.png`; GDB log in §6b).
* All 20 level codes entered; the GDB breakpoint on the level store returned
  ids `1,2,3,4,5,6,7,8,9,10,21,22,23,24,25,26,27,28,29,30` in table order.
* Mission-start proofs: `BUTTERFLY` → “Meet agent Kaos in the basement /
  Rescue British ambassador” (mission 3); `TIGER` → “THAT WAS SMART WORK WITH
  THE AMBASSADOR…” (mission 5); `SPECTRE` → “Follow Kaos through the subway /
  Avoid civilian casualties” (mission 9); `RAVEN` → Sever “Locate the safe
  house / Pick up the location of the inner compound” (Sever mission 2, Sever
  portrait on the objectives screen). The first three mission numbers match
  the archived GameFAQs walkthrough (file 54234) word-for-word.
* Cheat effects that are visible without audio: `BIGPOCKET` (ammo 100 stays
  100 after firing) and `TOOLEDUP` (three weapons in the HUD instead of one),
  both seen in the all-cheats run; the no-cheat HUD for comparison shows 20
  rounds and one weapon (`m2.png` vs `w1.png`).
* The only executed KEYINPUT literal read in the ROM is `0x0802EBE4`; no
  button-sequence table or progress index was found, and the multiplayer flow
  has no text input.

### Derived (instruction sequence)

* Cheat matcher, bit assignment, 10-byte compare and OR-write (`0x08026C24`).
* Level matcher, 20-entry loop and the `i<=9 ? i+1 : i+11` id mapping
  (`0x08026E40`–`0x08026F30`).
* 9-character cap (`0x080271E0`) and buffer/length addresses.
* The password screen's acceptance/rejection paths select the EFIGS records
  `0x080F3728` / `0x080F365C`.
* `0x0802D248` is the single level starter reached from the accept path.

### Inferred

* The exact combat effect of `DEATHWISH`, `COLDFEET`, `OOHSTOPIT`,
  `MYBIGUN`, `ACMEBANGS`, `HORNBLOW` and `DOYOUCME` is taken from the
  published list; only their flag bits were observed here.
* The `Cheat uncovered!§CODE` message bank is not referenced by the password
  screen; it is probably a leftover from an unlock-by-finding flow, but no
  runtime path to it was demonstrated.

## 8. Unknowns

* Multiplayer lobby screens (team/limit/Deathmatch/Assassination/Bomb setup)
  are reachable only after a successful link connection; with a single emulator
  instance the flow stops at “WAITING FOR CONNECTION”. This ROM contains no
  multiplayer password entry (one text buffer, one password screen), so the
  first game's multiplayer unlock words (`VULNERABLE`, `VORACIOUS`, …) have no
  surface here.
* The individual gameplay effects of seven cheats were not isolated; only
  their bits and the combined all-cheats HUD were observed.
* The credits/results flow (`0x0802D034`, `0x0802D170`, text bank `0x080F65xx`)
  is not a code surface; whether it is reachable without finishing the
  campaign was not tested.
* `0x0802DF38` is a byte-for-byte duplicate of the level matcher with no BL or
  pointer to it; its intended caller is unknown (dead code in this build).
* One automated session produced a spurious `INCORRECT PASSWORD` for the valid
  `DEATHWISH`; it was not reproducible and the comparator is stateless, so it
  is treated as a lost synthetic key event (see §3.1).

## 9. Tooling

Scripts and screenshots are in `/tmp/opencode/ballistic/` (Python 3,
`arm-none-eabi-objdump`, capstone, mGBA 0.10.5, xdotool, scrot/ImageMagick).
`ballistic_pw.py` next to this report is the reimplementation of the accept
decision and of the table→bit/level mapping:

```bash
python3 "Ballistic: Ecks vs. Sever/ballistic_pw.py"          # dump 29 codes
python3 "Ballistic: Ecks vs. Sever/ballistic_pw.py" DEATHWISH TIGER EXTREME
```

Commands used for the static work:

```bash
arm-none-eabi-objdump -D -b binary -marm -M force-thumb \
  --adjust-vma=0x08000000 --start-address=0x08026c24 \
  --stop-address=0x08026f44 "Ballistic: Ecks vs. Sever.gba"
python3 scanptr2.py 0x080F3600 0x080F3900 0x100000   # literal-pool xrefs
python3 blscan.py 0x08026c24                          # BL callers
```

Emulator:

```bash
Xvfb :164 -screen 0 1024x768x24 &
DISPLAY=:164 openbox &
SDL_AUDIODRIVER=dummy DISPLAY=:164 mgba -3 "Ballistic: Ecks vs. Sever.gba" &
```

Key evidence files: `g2.png` (title), `g3.png` (main menu), `h7.png`/`u4.png`
(password screen), `y2.png` (cheat accepted), `x2.png` (EXTREME rejected),
`x3.png` (9-char cap), `x4.png` (SACROSANC rejected), `zb.png` (mutation
rejected), `s1.png`/`zd.png` (mission start), `m3.png` (pause), `o6.png`
(options), `n1.png` (link connect), `v_spectre_start.png`, `w1.png`, `w2.png`
(all-cheats mission), `gdb2.log`/`gdb3.log` (level ids and `0x1FF`).

Legal note: no ROM, graphics, audio or game text is redistributed here; only
addresses, hashes, the algorithm, table contents required for verification,
and my own generated state combinations are published.

## 10. Cleanup

The emulator, Xvfb and window manager started for this analysis were stopped
by explicit PID: mGBA **637478** (also the earlier instances 607056 and
627765 from the same session), openbox **607041**, Xvfb **607018** (`:164`),
and the two `gdb-multiarch` batch helpers **611983** and **622554**, as were
the transient `scrot`/`import` calls.

Verification after teardown: `ps -p 637478,607041,607018` returns nothing,
`pgrep -x Xvfb` no longer lists `:164`, and `pgrep -x mgba` no longer lists
this ROM. No `pkill -x mgba`/`pkill Xvfb` was used, and no other session's
emulator or display was signalled (unrelated `mgba`/`Xvfb` processes belonging
to other analyses were left running and were checked alive after teardown).
