# Batman: Vengeance (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Batman: Vengeance/Batman: Vengeance.gba` |
| Size | 8,388,608 bytes (8 MiB) |
| Header title (`0xA0`) | `BATMAN-VENGE` |
| Game code (`0xAC`) | `ABTE` |
| Maker code (`0xB0`) | `41` |
| Software version (`0xBC`) | `0x00` |
| Fixed byte (`0xB2`) | `0x96` |
| Entry branch (`0x00`) | `0xEA00002E` → `0x080000C0` |
| MD5 | `06a6d7cd07281747cfe0300700a960fd` |
| SHA-1 | `cde073ffbe21deabdfb8a6d47eb16db14068f468` |
| SHA-256 | `760a9f3d9c6f8117b274c5435edfa7c5c7caeeb3ce6d8b197035ec442686b074` |

**Embedded-header scan.** The 156-byte Nintendo logo occurs exactly once, at file
offset `0x0004`. There is no second GBA image, multiboot stub or concatenated
game in the 8 MiB. No `PATCH`/IPS patch header or flash-cart signature is present
(`IPS` at `0xEB275` and `XG2` at `0x3C15EB` are coincidental bytes inside
compressed/graphics data).

**Header patch note.** The header has been rewritten after the title bytes were
fixed:

* complement check `0xBD` = `0x7B`; computed value from `0xA0..0xBC` = `0x77`
  (delta +4);
* header checksum at `0xBE` = `0x0000`; the value the Nintendo formula expects
  for this header is `0x7B` — i.e. the expected checksum sits in the complement
  byte and the checksum field was zeroed.

The game boots and runs normally; this is a post-build header edit (the classic
signature of a header/checksum tool writing the wrong field), not a gameplay
patch. Recorded so another dump/revision can be compared. All addresses below
are for **this exact file**.

## 2. Executive summary

Batman: Vengeance (GBA) has a developer-intended password system on the
`STORY MODE → PASSWORD` and `ADVANCE MODE` screens. It is **not** a plaintext
string table: the ROM stores 53 fixed 8-character records at
`0x08069614`, each byte biased by a per-position constant. `strings` and a
literal search therefore find only the dialogue hints, never the table. The
validator at
`0x08004088` walks all 53 records, compares character-by-character (space
records require an empty slot), and then dispatches the matching record index
at `0x08004100`.

The published level lists are complete and correct:

* story levels 2–21 (`GOTHAM`, `BATMAN`, `BARBARA`, `GRAYSON`, `ROBIN`, `TIM`,
  `BATGIRL`, `FRIES`, `VICTOR`, `ALFRED`, `CATWOMAN`, `JAMES`, `DRAKE`,
  `HARVEY`, `SELINA`, `BATARANG`, `BRUCE`, `QUINZEL`, `JACK`, `EDWARD`);
* Advance Mode levels 1–16 (`ARKHAM`, `WAYNE`, `AMY`, `NYGMA`, `CARRIE`,
  `WESKER`, `BULLOCK`, `GORDON`, `JONES`, `OSWALD`, `TALIA`, `MONTOYA`,
  `SCARFACE`, `CREEPER`, `DENT`, `KYLE`).

Three published story codes (`GRAYSON`, `ALFRED`, `BATARANG`) have no
uppercase ASCII copy anywhere in the ROM and no `new password:` dialogue hint
(`ALFRED` appears only as the mixed-case name "Alfred" in dialogue, which a
case-insensitive search would hit). They exist only in the biased table.
`ALFRED` was entered in the emulator and starts level 11, proving the decode.

Beyond the published list the same table contains ten special records:

* published: `NORA` (cinema player), `LSMRTG` (unlimited smoke bombs),
  `CREDITS` (credits);
* **not published**: `QPMTRL` (hidden team photo), `PSCLCTT` (freezes the
  Advance-Mode timer at `9:99`), `HOWDEYDO` (hidden developer-photo slideshow),
  `LHSBST` and `JQSLGS` (same cheat bit), `GLMTKVN` (third ammo counter → 255),
  `MRCLVLRL` (all four cheat bits at once).

All of those were entered through the real password screen and their effects
were observed (screenshots in `/tmp/opencode/vengeance/evidence/`, section 9).
Bounds are proven by
in-game rejection of `FLYMODE` (a typeable table record deliberately routed to
the invalid path) and of `ZZZZZZZ` (absent from the table), and by the fact that
six table records contain the digit `1`, which the A–Z keyboard cannot produce.

## 3. How to reproduce

**Emulator.** mGBA 0.10.5 SDL (`/usr/games/mgba`) under Xvfb, 3× scale,
`SDL_AUDIODRIVER=dummy`. A savestate at the password screen makes each test
eight letters plus one confirm.

**Keymap (mGBA SDL default):**

| GBA | key |
|---|---|
| A | `x` |
| B | `z` |
| L | `a` |
| R | `s` |
| Start | `Return` |
| Select | `BackSpace` |
| D-pad | arrow keys |

**Menu path.**

1. Boot → language screen (`ENGLISH` / `FRANCAIS` / `ESPANOL`) → A.
2. Intro movie → main menu `STORY MODE` / `ADVANCE MODE`.
3. Story: A on `STORY MODE` → submenu `NEW GAME` / `PASSWORD`; choose
   `PASSWORD`.
4. Advance: main menu → `ADVANCE MODE` → password screen directly (no
   `NEW GAME` submenu).
5. Password screen: 3×9 letter grid (`A`–`I`, `J`–`R`, `S`–`Z`), a delete arrow
   at row 3 column 9, and an `OK` cell below it. Eight input slots.
   The `OK` cell is reached by `Up` from `I` or `Down` from the delete arrow;
   `A` on `OK` submits, `B` cancels. After typing, move the highlight to the
   delete arrow (row 3, column 9) and press `Down` to select `OK`, then `A`.
   Follow the white highlight, not the vertical text caret.
6. In-game, `Start` opens the pause menu (`CONTINUE` / `QUIT`) which also
   displays the current level's password on the bottom line
   (`PASSWORD: GOTHAM` at level 2). This is the intended way for a player to
   recover the next code and is itself evidence that the codes are
   developer-intended.

**Codes entered in the emulator during this analysis (all through the UI):**

| Code | Result observed |
|---|---|
| `GOTHAM` | starts story level 2 |
| `CATWOMAN` | starts story level 12 (8 letters) |
| `ALFRED` | starts story level 11 (code has no ASCII copy in ROM) |
| `ARKHAM` | starts Advance Mode level 1, timer `2:45` |
| `CREDITS` | credits roll |
| `NORA` | cinema player starts (Joker/Harley scene) |
| `LSMRTG` | returns to menu, cheat flag `0x02` |
| `LHSBST` | returns to menu, cheat flag `0x01` |
| `JQSLGS` | returns to menu, cheat flag `0x01` |
| `GLMTKVN` | returns to menu, cheat flag `0x04` |
| `MRCLVLRL` | returns to menu, cheat flag `0x0F` |
| `PSCLCTT` | returns to menu, cheat flag `0x08`; later Advance timer shows `9:99` frozen |
| `HOWDEYDO` | developer-photo slideshow, then logo, then main menu |
| `QPMTRL` | team photo; `Start` → credits |
| `FLYMODE` | **rejected**, password screen remains, no flag |
| `ZZZZZZZ` | **rejected**, password screen remains, no flag |

Screenshots for these are listed in section 9.

**Published sources checked.** GameFAQs' GBA cheats page (fetched through the
2023 Wayback snapshot; the live page returns 403), IGN's GBA cheats wiki and
Neoseeker (both 403 to direct fetch, snippets read), Project Cheat Codes, and
The Cutting Room Floor (Wayback snapshot). They list the 20 story and 16
Advance level passwords plus `NORA`, `LSMRTG` and `CREDITS`; TCRF additionally
documents an unused non-English `BOBKANE` hint that it says returns invalid.
Every one of the 39 listed working strings is present in the table at
`0x08069614`; `BOBKANE` is **not** a table record (consistent with TCRF's
"invalid"). Three of the level strings (`GRAYSON`, `ALFRED`, `BATARANG`) have
no plaintext copy in the ROM, which is why a literal search alone suggests they
are fake; the table decode and the in-game `ALFRED` test disprove that.
Searches for `HOWDEYDO`, `QPMTRL`, `PSCLCTT`, `LHSBST`, `GLMTKVN`, `MRCLVLRL`
and `JQSLGS` returned no results, and TCRF does not mention them, so the seven
novel codes below are absent from the published lists.

## 4. Address map

File offset = ROM address − `0x08000000`.

### ROM

| Address | Contents |
|---|---|
| `0x08069614`–`0x080697BB` | password table, 53 × 8 bytes (424 bytes); `char = byte − K[pos]`, `K` = `21 14 09 0B 17 45 3C 0A` |
| `0x08003A30` | table character accessor `get_char(entry, pos)`; switch on `pos`, jump table `0x08003A48` |
| `0x08003B14` | password-screen render/init routine |
| `0x08003CCC` | letter-grid input handler (cursor index rules) |
| `0x08003E00` | caret/delete handling (max 8, `0xFF` padding) |
| `0x08003F9C` | `OK`-cell input handler; A calls the validator |
| `0x08004088` | **validator**: loops entries 0–52 and characters 0–7 |
| `0x08004100` | **action dispatch** on the matched entry index |
| `0x080049CE` etc. | scene code that tests cheat bit `0x08` |
| `0x080078B8` | countdown/timer routine; skips decrement when bit `0x08` is set |
| `0x0800A8C0` | per-frame cheat application to the player struct (bits 0,1,2,7) |
| `0x08069B00` | English dialogue/text bank; `Sir, take note of the new password:` at `0x08069BE4` |
| `0x08069BDC` | string `GOTHAM` (text only, not used by the validator) |
| `0x0807A190` | string `CREDITS` inside the credits text (`0x0807A000` region) |
| `0x0806A2FB`, `0x0806AD36`, `0x0806B484`, `0x0806BCEC`, `0x0806C570` | five non-English text banks (French, German, Dutch, Italian, Spanish); each holds 34 `new password:` hint lines, although only English/French/Spanish are selectable |

### RAM

| Address | Meaning |
|---|---|
| `0x03000000` | cursor cell index (0–26 letters, 27 = `OK`) |
| `0x03000008`–`0x0300000F` | 8-byte input; letter index 0–25, `0xFF` = empty |
| `0x03000010` | input length (0–8) |
| `0x03003D90` | scene request struct; `+0x0C` = scene id, `+0x10` = result |
| `0x03003DA8` | requested level (entry index + 1) |
| `0x03003DB0` | menu/state struct |
| `0x03003DCC` | **cheat flag byte** (`0x03003DB0 + 0x1C`) |
| `0x03004244` | pointer to the player struct |
| `0x03000018` | player struct (default): `+9` = 5, `+10` = 1, `+11` = 255, `+12` = 3, `+13` = 1 (active) |
| `0x03004300` | countdown struct; `+0x10..+0x12` = 24-bit timer, `+0x15` = low-time sound flag |

Scene ids observed: `15` developer photos, `17` main menu, `20` password
screen, `31` story intro cutscene, `34` level load, `40` credits, `41` cinema
player, `42` team photo.

## 5. Algorithm

### 5.1 Character encoding

The table stores one record per code, eight bytes. The byte for character
position `p` is `ASCII(char) + K[p]` (mod 256), with

```
K = [0x21, 0x14, 0x09, 0x0B, 0x17, 0x45, 0x3C, 0x0A]
```

so `byte − K[p]` yields an ASCII uppercase letter or `0x20` (space padding).
This is why `grep GOTHAM` finds only the dialogue text, never the table.
`0x08003A30` implements this as a jump table on `p`; each case loads
`0x08069614 + entry*8 + p` and subtracts its constant.

### 5.2 Validator (`0x08004088`)

```c
bool validate(u8 buf[8], u8 len) {          // buf: 0..25 per letter, 0xFF empty
    for (int e = 0; e < 53; e++) {          // r2 = 0..52
        bool ok = true;
        for (int p = 0; p < 8; p++) {       // r7 = 0..7
            u8 c = get_char(e, p);          // 0x08003A30
            if (c == ' ') {
                if (buf[p] != 0xFF) { ok = false; break; }
            } else if (c != buf[p] + 'A') { ok = false; break; }
        }
        if (ok) return dispatch(e);
    }
    beep(0xFF);                             // invalid
    return false;
}
```

The buffer is filled from the screen one letter at a time; empty slots remain
`0xFF`, which is exactly what the space-padding branch expects. This is why
codes of different lengths (3–8) all work against fixed 8-byte records.
Length 9+ is not representable: the input buffer is 8 bytes.

### 5.3 Action dispatch (`0x08004100`)

```c
switch (e) {
case 0 ... 35:  level = e + 1; scene = 34; break;   // story 2-21, Advance 1-16
case 36:        scene = 41; break;                  // NORA  - cinema player
case 37:        scene = 42; break;                  // QPMTRL - team photo
case 38:        cheat_flags |= 0x08; scene = 17; break; // PSCLCTT - timer
case 39:        scene = 15; break;                  // HOWDEYDO - developer photos
case 40 ... 43: beep(0xFF); return false;           // dead records
case 44:        cheat_flags |= 0x02; scene = 17; break; // LSMRTG - smoke bombs
case 45:        cheat_flags |= 0x01; scene = 17; break; // LHSBST
case 46:        cheat_flags |= 0x04; scene = 17; break; // GLMTKVN
case 47:        cheat_flags |= 0x0F; scene = 17; break; // MRCLVLRL - all four
case 48:        cheat_flags |= 0x80; scene = 17; break; // 1IGHTMAN (untypeable)
case 49:        cheat_flags |= 0x01; scene = 17; break; // JQSLGS
case 50 ... 51: beep(0xFF); return false;           // dead records
case 52:        scene = 40; break;                  // CREDITS
}
```

Cheat flags are OR-ed into `0x03003DCC` and stay set for the session. The
per-frame application at `0x0800A8C0` writes the player struct:

| flag | code(s) | effect on player struct | baseline → cheat |
|---|---|---|---|
| `0x01` | `LHSBST`, `JQSLGS` | `+9 = 0xFF` | 5 → 255 |
| `0x02` | `LSMRTG` | `+10 = 0xFF` | 1 → 255 (smoke bombs; matches the published description) |
| `0x04` | `GLMTKVN` | `+12 = 0xFF` | 3 → 255 (third consumable/charge counter) |
| `0x08` | `PSCLCTT` | skips the countdown decrement at `0x080078B8`; scene branches | Advance timer displayed `9:99` and did not move |
| `0x0F` | `MRCLVLRL` | all four above | 5,1,255,3 → 255,255,255,255 |
| `0x80` | `1IGHTMAN` | sets two entity bytes to 1 | record contains `1`; unreachable |

## 6. Tables

### 6.1 Full password table (`0x08069614`, 53 × 8 bytes)

`P` = published, `N` = novel (this report), `X` = rejected/untypeable.
The string column is the exact decoded record (spaces shown for padding).

| idx | ROM addr | decoded | action | status |
|---:|---|---|---|---|
| 0 | `0x08069614` | `GOTHAM  ` | story L2 | P, tested |
| 1 | `0x0806961C` | `BATMAN  ` | story L3 | P |
| 2 | `0x08069624` | `BARBARA ` | story L4 | P |
| 3 | `0x0806962C` | `GRAYSON ` | story L5 | P (no ASCII copy) |
| 4 | `0x08069634` | `ROBIN   ` | story L6 | P |
| 5 | `0x0806963C` | `TIM     ` | story L7 | P |
| 6 | `0x08069644` | `BATGIRL ` | story L8 | P |
| 7 | `0x0806964C` | `FRIES   ` | story L9 | P |
| 8 | `0x08069654` | `VICTOR  ` | story L10 | P |
| 9 | `0x0806965C` | `ALFRED  ` | story L11 | P (no ASCII copy), tested |
| 10 | `0x08069664` | `CATWOMAN` | story L12 | P, tested |
| 11 | `0x0806966C` | `JAMES   ` | story L13 | P |
| 12 | `0x08069674` | `DRAKE   ` | story L14 | P |
| 13 | `0x0806967C` | `HARVEY  ` | story L15 | P |
| 14 | `0x08069684` | `SELINA  ` | story L16 | P |
| 15 | `0x0806968C` | `BATARANG` | story L17 | P (no ASCII copy) |
| 16 | `0x08069694` | `BRUCE   ` | story L18 | P |
| 17 | `0x0806969C` | `QUINZEL ` | story L19 | P |
| 18 | `0x080696A4` | `JACK    ` | story L20 | P |
| 19 | `0x080696AC` | `EDWARD  ` | story L21 | P |
| 20 | `0x080696B4` | `ARKHAM  ` | Advance L1 | P, tested |
| 21 | `0x080696BC` | `WAYNE   ` | Advance L2 | P |
| 22 | `0x080696C4` | `AMY     ` | Advance L3 | P |
| 23 | `0x080696CC` | `NYGMA   ` | Advance L4 | P |
| 24 | `0x080696D4` | `CARRIE  ` | Advance L5 | P |
| 25 | `0x080696DC` | `WESKER  ` | Advance L6 | P |
| 26 | `0x080696E4` | `BULLOCK ` | Advance L7 | P |
| 27 | `0x080696EC` | `GORDON  ` | Advance L8 | P |
| 28 | `0x080696F4` | `JONES   ` | Advance L9 | P |
| 29 | `0x080696FC` | `OSWALD  ` | Advance L10 | P |
| 30 | `0x08069704` | `TALIA   ` | Advance L11 | P |
| 31 | `0x0806970C` | `MONTOYA ` | Advance L12 | P |
| 32 | `0x08069714` | `SCARFACE` | Advance L13 | P |
| 33 | `0x0806971C` | `CREEPER ` | Advance L14 | P |
| 34 | `0x08069724` | `DENT    ` | Advance L15 | P |
| 35 | `0x0806972C` | `KYLE    ` | Advance L16 | P |
| 36 | `0x08069734` | `NORA    ` | scene 41 — cinema player | P, tested |
| 37 | `0x0806973C` | `QPMTRL  ` | scene 42 — hidden team photo | **N**, tested |
| 38 | `0x08069744` | `PSCLCTT ` | cheat bit `0x08` — timer disabled | **N**, tested |
| 39 | `0x0806974C` | `HOWDEYDO` | scene 15 — developer-photo slideshow | **N**, tested |
| 40 | `0x08069754` | `1IRROR  ` | beep (invalid) | X — contains `1` |
| 41 | `0x0806975C` | `FLYMODE ` | beep (invalid) | X — typeable, tested rejected |
| 42 | `0x08069764` | `12345678` | beep (invalid) | X — contains digits |
| 43 | `0x0806976C` | `1HMCFRSB` | beep (invalid) | X — contains `1` |
| 44 | `0x08069774` | `LSMRTG  ` | cheat bit `0x02` | P, tested |
| 45 | `0x0806977C` | `LHSBST  ` | cheat bit `0x01` | **N**, tested |
| 46 | `0x08069784` | `GLMTKVN ` | cheat bit `0x04` | **N**, tested |
| 47 | `0x0806978C` | `MRCLVLRL` | cheat bits `0x0F` | **N**, tested |
| 48 | `0x08069794` | `1IGHTMAN` | cheat bit `0x80` | X — contains `1` |
| 49 | `0x0806979C` | `JQSLGS  ` | cheat bit `0x01` | **N**, tested |
| 50 | `0x080697A4` | `1QSLGS  ` | beep (invalid) | X — contains `1` |
| 51 | `0x080697AC` | `1BNWNL  ` | beep (invalid) | X — contains `1` |
| 52 | `0x080697B4` | `CREDITS ` | scene 40 — credits | P, tested |

### 6.2 Alphabet and field layout

* Alphabet: 26 symbols `A`–`Z`. No digits, by design of the on-screen
  keyboard.
* Record length: 8 characters, space-padded. Input length: 3–8 (shortest
  record is `TIM`/`AMY`; longest records are the 8-letter ones).
* Fields: there is **no checksum and no per-character field packing**. The
  system is a pure 53-entry lookup table; the only "check" is exact
  case-sensitive equality against a record.
* Record encoding: one biased byte per character, constants
  `21 14 09 0B 17 45 3C 0A`.

### 6.3 Cheat flag byte `0x03003DCC`

Bits are set by OR and are cumulative within a session; `MRCLVLRL` sets all
four low bits. They apply from the next level load and are re-applied to the
player struct every frame while the player is active.

## 6b. Enumeration

### Space definition

| Quantity | Value |
|---|---|
| Table records | 53 |
| Record width | 8 characters |
| Alphabet | 26 (`A`–`Z`) |
| Representable input strings (length 1–8, 26 symbols) | 217,180,147,158 |
| Typeable table records | 47 (53 − 6 containing `1`) |
| Typeable records that dispatch to an action | 46 |
| Typeable records routed to the invalid path | 1 (`FLYMODE`) |
| Untypeable records | 6 (`1IRROR`, `12345678`, `1HMCFRSB`, `1IGHTMAN`, `1QSLGS`, `1BNWNL`) |

So the accepted language is a *finite list of 46 effective inputs*, not a
checksum space. Enumerating the whole space means enumerating the 53-record
table, which was fully dumped and decoded (section 6.1), not brute-forcing
26^8 strings: a random 8-letter string has 46/26^8 ≈ 2.1 × 10^-10 chance
of matching.

### Search space checked (negative results, bounded)

* `strings -n 4` over the whole 8 MiB produced 65,054 entries. Case-insensitive
  byte counts: `password` 35 (34 Italian `nuova password:` hints + one English
  `new password` phrase), `cheat` 0, `debug` 0, `code` 0, `secret` 3,
  `unlock` 1, `level` 6, `menu` 1. The French/German/Dutch/Spanish banks use
  their own words (34 hint lines each), so they do not add to the `password`
  count. All non-keyword hits are dialogue instructions.
* There is no 26-character alphabet string in the ROM; the grid order is
  produced by the screen renderer. The alphabet was confirmed from the input
  buffer (0–25) and the eight-slot screen.
* No button-mask cheat sequence, debug menu, or key gate was found. The only
  code-entry surface is the password screen reachable from the main menu and
  from Advance Mode.
* Six of the 53 records are dead because they contain `1`; one typeable record
  (`FLYMODE`) is deliberately routed to the beep path. These are the only
  non-dispatching records.

### Novel codes (not in any published list)

The following decoded records do not appear on GameFAQs, IGN, Neoseeker,
Project Cheat Codes or any wiki searched (sources in section 3). Each was entered through
the real password screen, not written to RAM.

1. **`HOWDEYDO`** (idx 39) — hidden developer-photo slideshow. Two photographs
   of the development team (beer/cans), then the Batman Vengeance logo, then
   the main menu. Scene 15. Proof: `evidence/05_howdeydo_photo1.png`,
   `evidence/06_howdeydo_photo2.png`; RAM `0x03003D90+0x0C = 15`.
2. **`QPMTRL`** (idx 37) — hidden team photo (large group with Batman villains
   in costume); `Start` advances to the credits. Scene 42. Proof:
   `evidence/07_qpmtrl_team_photo.png`; RAM scene = 42.
3. **`MRCLVLRL`** (idx 47) — sets all four cheat bits at once. In level 2 the
   player struct changed from `+9..+12 = 5,1,255,3` to
   `255,255,255,255`. Proof: `evidence/11_mrclvlrl_level_start.png`; state
   dump reproduced in section 7.
4. **`PSCLCTT`** (idx 38) — sets cheat bit `0x08`. In Advance Mode the timer,
   normally `2:45` counting down (`evidence/10_advance_timer_normal_2_45.png`),
   displays `9:99` and is frozen for at least 4 s
   (`evidence/08_psclctt_timer_9_99.png`,
   `evidence/09_psclctt_timer_after_4s.png`). RAM scene = 34, flag = 8.
5. **`LHSBST`** (idx 45) and **`JQSLGS`** (idx 49) — both set bit `0x01`;
   player `+9` becomes 255 (baseline 5): unlimited first ammo counter.
6. **`GLMTKVN`** (idx 46) — sets bit `0x04`; player `+12` becomes 255
   (baseline 3).

`LSMRTG` (idx 44, published) was confirmed as bit `0x02`: player `+10`
becomes 255 (baseline 1), the smoke-bomb counter, which matches its published
description.

### Bounds proven by rejection

| Input | Type | Result |
|---|---|---|
| `FLYMODE` | table record idx 41, typeable, 7 letters | **Rejected**: after `OK`, the password screen remains, `0x03003DCC` stays 0, scene stays 20 (`evidence/13_flymode_reject.png`) |
| `ZZZZZZZ` | not in table, 7 letters | **Rejected**: same behaviour (`evidence/14_zzzzzz_reject.png`) |
| `1IGHTMAN`, `1QSLGS`, `1BNWNL`, `1IRROR`, `12345678`, `1HMCFRSB` | table records containing `1` | **Not expressible**: the UI has only A–Z and the validator only accepts `buf[i]+'A'`; six records are dead |
| 9+ letters | length bound | Not expressible: 8-byte buffer / 8-slot screen |

The distinction between "the table contains X" and "the game can use X" is
important: `FLYMODE` proves the dispatch layer is a separate gate from the
comparison, and the digit records prove the input alphabet is a real bound.
The shortest accepted inputs are 3 letters (`TIM`, `AMY`); a 1- or 2-letter
string cannot match any record and is rejected.

## 7. Validation evidence

### Observed (emulator screenshots / savestate memory)

* `STORY MODE → PASSWORD` screen exists; 26-letter grid, delete cell, `OK`
  cell, 8 slots (`evidence/01_password_screen.png`).
* `GOTHAM` starts level 2 (`evidence/02_gotham_level2.png`); `CATWOMAN` starts
  level 12; `ALFRED` (no uppercase or hint copy in ROM) starts level 11
  (`evidence/15_alfred_level11.png`); `ARKHAM` starts Advance Mode level 1
  with a `2:45` timer (`evidence/10_advance_timer_normal_2_45.png`).
* Pause menu displays `PASSWORD: GOTHAM` for level 2
  (`evidence/12_pause_password_display.png`).
* `CREDITS` rolls the credits (`evidence/03_credits_code.png`).
* `NORA` starts the cinema player (Joker/Harley scene,
  `evidence/04_nora_cinema.png`, scene 41).
* `HOWDEYDO` shows the developer photos (`evidence/05...`, `06...`, scene 15);
  `QPMTRL` shows the team photo (`evidence/07...`, scene 42).
* `PSCLCTT` makes the Advance Mode timer read `9:99` and stay there
  (`evidence/08...`, `09...`); without it the same screen counts down from
  `2:45`.
* Savestate RAM reads (IWRAM at `0x03000000`):
  * baseline level 2: player `0x03000018`, `+9..+12 = 5,1,255,3`;
  * after `LHSBST`: `255,1,255,3`;
  * after `LSMRTG`: `5,255,255,3` (flag byte 2);
  * after `GLMTKVN`: `5,1,255,255` (flag byte 4);
  * after `MRCLVLRL`: `255,255,255,255` (flag byte 15);
  * after `PSCLCTT`: flag byte 8, no player-field change.
* `FLYMODE` and `ZZZZZZZ` leave flag byte 0 and scene 20.

### Derived (instruction sequence)

* Table decode constants from the jump table at `0x08003A48`; validator loop
  and space/`0xFF` rule from `0x08004088`; dispatch tree from `0x08004100`.
* Cheat-bit writes and player-field offsets from `0x0800A8C0`; timer skip from
  `0x080078B8`; scene ids from the dispatch.
* No checksum exists: every branch of the validator is an equality test; there
  is no `eor`/`and`/`add` over the input before comparison.
* Six records contain ASCII `1` (0x31) after decoding; the UI can only produce
  0–25, so they are unreachable.

### Inferred

* The exact gameplay label of the `+9` and `+12` counters (first and third
  consumable/charge slots). The `+10` slot is proven to be smoke bombs by the
  published `LSMRTG` description and by the HUD count going 1 → 0 when a smoke
  bomb is thrown. `+9` and `+12` behave identically but were not matched to a
  named weapon in the HUD.
* `0x08` freezes the timer; whether the value is initialised to 999 or clamped
  to `9:99` by the display was not isolated (both are consistent with the
  observed `9:99`).
* The digit records (`1IRROR`, `1IGHTMAN`, …) look like placeholders/corrupted
  developer strings (`MIRROR`, `NIGHTMAN`), but this is speculation.

## 8. Unknowns

* The named weapon/ability of player offsets `+9` and `+12`. The offsets,
  bit-to-offset mapping and values are proven; only the in-game labels are not.
* Whether `QPMTRL` has more than the one team photo (only one was shown; Start
  moved to credits). `HOWDEYDO` had two photos and then the logo.
* Whether the six digit-leading records were ever reachable in a debug build.
  In this ROM they are dead.
* The precise reason the header checksum/complement pair was rewritten.

## 9. Tooling

* `mgba` 0.10.5 (SDL) under `Xvfb :176` with `SDL_AUDIODRIVER=dummy`;
  screenshots with `scrot` and `ImageMagick convert`.
* `arm-none-eabi-objdump -M force-thumb` for the validator/dispatch/timer code.
* Python 3 + Capstone 5.0.7 for the literal-pool and flag-test scans.
* mGBA savestates are PNG files with a zlib `gbAs` chunk; the 0x61000-byte
  serialized state has IWRAM at `0x19000` and EWRAM at `0x21000`. A small
  parser was used to read `0x03000000`, `0x03000008`, `0x03003DCC`,
  `0x03004244` and the timer struct.
* Decoder/validator reimplementation: `/tmp/opencode/vengeance/bv.py`
  (`python3 bv.py CODE` prints matching entry indices; `python3 bv.py` dumps
  all 53 records). It reproduces `GOTHAM→[0]`, `CATWOMAN→[10]`,
  `HOWDEYDO→[39]`, `FLYMODE→[41]`, `ZZZZZZZ→[]`.
* Evidence kept outside the repository at
  `/tmp/opencode/vengeance/evidence/`:
  `01_password_screen.png`, `02_gotham_level2.png`, `03_credits_code.png`,
  `04_nora_cinema.png`, `05_howdeydo_photo1.png`, `06_howdeydo_photo2.png`,
  `07_qpmtrl_team_photo.png`, `08_psclctt_timer_9_99.png`,
  `09_psclctt_timer_after_4s.png`, `10_advance_timer_normal_2_45.png`,
  `11_mrclvlrl_level_start.png`, `12_pause_password_display.png`,
  `13_flymode_reject.png`, `14_zzzzzz_reject.png`, `15_alfred_level11.png`,
  `table_dump.txt`.

### Legal note

No ROM, extracted graphics, music or text is redistributed here. The report
contains only hashes, addresses, the decoded password strings (already
published for the 36 level codes and the three published specials), the derived
algorithm, and my own descriptions of observed screens.

### General lesson worth folding into the guide

A password table can be deliberately biased per character position (here
`byte = ASCII + K[pos]`). A literal `grep` for published passwords then finds
only dialogue text, and an "absent" published code (`ALFRED`, `GRAYSON`,
`BATARANG`) looks fake. Before concluding a table does not exist, find the
validator and dump its comparison table; decode with the constants recovered
from the accessor's jump table. Conversely, a record that is present in the
table is not necessarily usable: check the dispatch switch and the input
alphabet (`FLYMODE` and the `1…` records are the proof).
