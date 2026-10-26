# Alienators: Evolution Continues (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Alienators: Evolution Continues/Alienators: Evolution Continues.gba` |
| Size | 4,194,304 bytes (4 MiB, `0x400000`) |
| Header title | `ALIENATORS` (NUL padded) |
| Game code | `AEVE` |
| Maker code | `52` |
| Software version | `00` |
| Entry word | `0xEA00002E` (ARM `b 0x080000C0`) |
| Complement check (`0xBD`) | `0xD7` (valid) |
| Header checksum (`0xBE`) | `0x0000` (recomputed: `0xF61C`) — non-standard; the ROM still boots in mGBA |
| MD5 | `5eba0ef1c24f1b003b3063beb808ce6c` |
| SHA-1 | `fb691c5e21fa388d75497e9090db82dec881e422` |
| SHA-256 | `88465bfb0bde8a9a3df4a6081cc9f8e999fa74c68c1ec91ebc8dfc977be85fd0` |
| CRC32 | `0x0D694CA4` |

Embedded-header scan: the 156-byte Nintendo logo occurs **once**, at file `0x4`
(header `0x0`); a second scan for the GBA header magic/title/code pattern found no
other image. This is a single-image cartridge, not a 2-in-1 pack.

## 2. Executive summary

Alienators uses an **8-character, 16-symbol progress password**. Every symbol is
one nibble; the eight symbols are packed into a 32-bit word, XORed with the
constant `0x571EA60B`, and validated by a **6-bit additive checksum** whose six
bits are scattered through the same bytes (bits 3/4 of byte 0, bits 3/4 of
byte 1, bit 3 of byte 2, bit 1 of byte 3). Of the 2^32 possible input strings,
2^26 (67,108,864) pass the checksum.

The decoded word carries a **26-bit payload**. Six of those bits are the only
ones the game acts on directly:

* `q3[5:2]` — mission index, 4 bits; level = index + 1 (index 0…12 = levels 1…13).
* `q3[7:6]` — mode, 2 bits: `1` = Normal, `2` = Hard (the mode the Options
  screen writes), `3` = a value not offered by Options (used by the published
  "weird level" code), `0` = also accepted.

The remaining 20 payload bits are progress/statistics data produced by the
game's own encoder from gameplay counters.

All 25 published GameFAQs/SuperCheats/Project-Cheat-Codes passwords were verified
against the ROM model; every one passes. Two published-list errors were proven:

* GameFAQs and Project Cheat Codes print `GLPKBKRF` for both Level 11 and Level
  12. `GLPKBKRF` decodes to level index 11 (Level 12) and its in-game briefing
  is the Level 12 "canyonlands 100%" briefing. The real Level 11 code is
  `GLDKBKZF` (SuperCheats has it), whose briefing is the Level 11 air-shaft
  valve mission.
* The "Unlimited Ammo" code `RBJPXCKC` is the Level 1 Normal password with an
  all-zero progress payload; the HUD then shows ∞ ammunition.

**Novel, unpublished codes generated and accepted in-game:**

* `RBJPXCKT` — Level 1, mode 2 (Hard). Not in any published list. It is
  accepted, starts Mission 1 ("Locate access card"), and the pause menu's
  *Current Password* echoes `RBJPXCKT`. Screenshots 06–08.
* `DFTLHBKC` — the repaired form of the password the game itself prints for a
  fresh Normal game (see §6b). Accepted, starts Mission 1. Screenshot 15.

**Bounds proven by the ROM/emulator:** a checksum-invalid code (`MDKMZKCD`) is
rejected and the game stays on the entry screen; codes whose mission index is
outside the mission table (level 14 `RBXPJCCD`, level 15 `RBJRJCTD`, level 16
`RBXRJCMD`) pass the checksum but have an empty briefing — continuing leads to a
black screen (15) or a crash at `0xFFFFFFFE` (16). A code the game *itself* generates for a fresh game
(`DFHLHBHC`/`DFHLHBHT`) is also rejected — its check characters are stale; two
characters repaired to `DFTLHBKC`/`DFTLHBKT` are accepted.

## 3. How to reproduce

Emulator: mGBA 0.10.5 (`/usr/games/mgba`, SDL frontend), `-3` scale, on
`Xvfb :130` + `openbox`, `SDL_AUDIODRIVER=dummy`.

```bash
Xvfb :130 -screen 0 1280x960x24 &
DISPLAY=:130 openbox &
cd /tmp/opencode/alienators
cp "/mnt/gbacheats/roms/Alienators: Evolution Continues/Alienators: Evolution Continues.gba" game.gba
DISPLAY=:130 SDL_AUDIODRIVER=dummy SDL_VIDEODRIVER=x11 /usr/games/mgba -3 game.gba &
```

Keymap (mGBA SDL default): **A = `x`, B = `z`, Start = `Return`, Select =
`BackSpace`, D-pad = arrows, L = `a`, R = `s`.** Hold every key 100–150 ms; the
game polls input once per frame and short taps are lost.

Title menu path: the title menu is `Start Game / Password / Options`.

Password entry: `Down` once, `A`. The screen shows eight diamond slots. The
first directional press initialises every slot to `B` (index 0); the highlighted
slot is the cursor (`0`–`7`). `Up`/`Down` step the symbol through the alphabet
`B C D F G H J K L M P R S T X Z` (wrapping), `Left`/`Right` move the cursor,
`A` accepts, `B` exits.

Enter `RBJPXCKT` from the all-`B` screen:

| slot | char | presses |
|---|---|---|
| 0 | R | Up ×11 |
| 1 | B | (none) |
| 2 | J | Right, Up ×6 |
| 3 | P | Right, Up ×10 |
| 4 | X | Right, Up ×14 |
| 5 | C | Right, Up ×1 |
| 6 | K | Right, Up ×7 |
| 7 | T | Right, Up ×13 |

then `A`. The Mission 1 briefing appears; `A` starts play; `Start` opens the
pause menu; `View Password` displays `RBJPXCKT`.

Tested codes (all entered through the on-screen keyboard unless noted):

| Code | Source | Result |
|---|---|---|
| `MDKMZKCC` | GameFAQs Level 2 | accepted → "Power up generator" |
| `LFKMZCDT` | published Level 2 Hard | accepted → "Power up generator" |
| `GLDKBKZF` | SuperCheats Level 11 | accepted → Level 11 air-shaft-valve briefing |
| `GLPKBKRF` | GameFAQs Level 11/12 | accepted → Level 12 canyonlands briefing (not L11) |
| `RBJPXCKC` | published "Unlimited Ammo" | accepted → Level 1, HUD shows ∞ ammo |
| `RBJPXCKT` | **generated here (novel)** | accepted → Level 1, mode byte `0x80` |
| `RBJPXCKH` | generated here (mode 0) | accepted → Level 1 |
| `DFTLHBKC` | **generated here (repaired fresh-game code)** | accepted → Level 1 |
| `RBXPJCCD` | generated here (level 14) | accepted, empty briefing, no mission data |
| `RBJRJCTD` | generated here (level 15) | accepted, empty briefing, then black screen |
| `RBXRJCMD` | generated here (level 16) | accepted, empty briefing, crash on continue |
| `MDKMZKCD` | corrupted `MDKMZKCC` | **rejected** (stays on entry screen) |
| `DFHLHBHC` | game's own fresh Normal password | **rejected** |
| `DFHLHBHT` | game's own fresh Hard password | **rejected** |

Screenshots are in `shots/` next to this report (01–16).

## 4. Address map

ROM addresses are `0x08000000 + file offset`. The ROM is a single 4 MiB image.

| Address | Kind | Meaning |
|---|---|---|
| `0x083813EC` | data | 16-symbol alphabet, ASCII: `BCDFGHJKLM PRSTXZ` without the space |
| `0x083858D8` | data | 16-entry pointer table used to draw the selected slot glyph |
| `0x0829098C` | code | **validator** (packed word → checksum → mode/level) |
| `0x08290988` | data | XOR key literal `0x571EA60B` (also at `0x08290A48`) |
| `0x08290738` | code | **encoder** (gameplay statistics → packed password at `+4`) |
| `0x0829AE20` | code | **display** routine: expands packed bytes to 8 alphabet chars |
| `0x08298F34` | code | password-screen input handler (single-press dispatch) |
| `0x08298FBA` | code | `Up` handler: `buf[cursor] = (buf[cursor]+1) & 0xF` |
| `0x08299004` | code | `Down` handler: `buf[cursor] = (buf[cursor]-1) & 0xF` |
| `0x0829904E` / `0x08299074` | code | cursor left / right |
| `0x0829909C` | code | **accept** path: packs 8 nibbles into 4 bytes, calls validator |
| `0x0829AFF2` | code | pause-menu call to the password display |
| `0x08290A64` | code | mission-record loader (stride `0x5A`) |
| `0x08144A9C` | data | mission table base used by `0x08290A64` |
| `0x03001F10` | RAM | password-screen UI struct: `+0` u16 mode result, `+4` u16 sound flag, `+8` u16 cursor, `+0xA` u16 cooldown, `+0xC…+0x13` **8 input bytes** |
| `0x03001F24` | RAM | screen state word (3 = password entry) |
| `0x030016F0` | RAM | session/progress struct |
| `0x030016F0+0…3` | RAM | decoded `q0…q3` (unmasked) |
| `0x030016F0+4…7` | RAM | packed password `P` (what the pause menu displays) |
| `0x030016F0+0x1E` | RAM | flags; bit 0 = "started from password" |
| `0x030016F0+0x24` | RAM | mode (copied from `0x03001F10`) |
| `0x030016F0+0x26` | RAM | mission index `(q3>>2)&0xF` |

Entry-point disassembly anchors (`objdump -M force-thumb` / Capstone):

```
0829909c: ldrb r1,[r4,#0xc]   ; buf[0]
0829909e: movs r2,#0xf
082990a0: ldrb r0,[r4,#0xd]   ; buf[1]
082990a2: lsls r0,r0,#4
082990a4: ands r1,r2
082990a6: orrs r1,r0
082990a8: strb r1,[r5,#4]     ; 0x030016F4  (P byte 0)
...                            ; bytes 1..3 from buf[2..7]
082990d8: bl   0x829098c      ; validator
```

```
08290994: ldr r5,[pc,#0xac]   ; r5 = 0x030016F4
08290996: ldr r3,[r5]         ; r3 = P
08290998: ldr r0,[pc,#0xac]   ; r0 = 0x571EA60B
0829099c: eors r3,r0          ; q = P ^ key
082909a0: str r3,[r7]         ; scratch at 0x030016F0
...
08290a30: cmp r1,r2           ; computed 6-bit sum vs scattered check bits
08290a34: ldrb r0,[r7,#3]     ; q3
08290a38: lsrs r0,r0,#6       ; mode
08290a3a: strh r0,[r1]        ; -> 0x03001F10
08290a3c: strh r0,[r7,#0x24]  ; -> state+0x24
08290a3e: movs r0,#1          ; accept
```

## 5. Algorithm

```
ALPHABET = "BCDFGHJKLM PRSTXZ"     # 16 symbols, index 0..15 (no space)
KEY      = 0x571EA60B

decode(code):                       # code = 8 alphabet symbols
    n[i] = index of code[i] in ALPHABET
    P    = n0 | n1<<4 | n2<<8 | n3<<12 | n4<<16 | n5<<20 | n6<<24 | n7<<28
    Q    = P ^ KEY                  # little-endian 4 bytes q0..q3
    payload = Q with check bits cleared:
        q0 &= ~0x18; q1 &= ~0x18; q2 &= ~0x08; q3 &= ~0x02
    computed = (q0 + q1 + q2 + q3) & 0x3F          # bytes, 8-bit adds
    stored   = (q0>>3 & 1)       | ((q0>>4 & 1)<<1)
             | ((q1>>3 & 1)<<2)  | ((q1>>4 & 1)<<3)
             | ((q2>>3 & 1)<<4)  | ((q3>>1 & 1)<<5)
    return computed == stored

encode(payload):                     # inverse, used to mint codes
    q0..q3 = payload bytes with the check bits zero
    c = (q0+q1+q2+q3) & 0x3F
    q0 |= (c&1)<<3 | ((c>>1)&1)<<4
    q1 |= ((c>>2)&1)<<3 | ((c>>3)&1)<<4
    q2 |= ((c>>4)&1)<<3
    q3 |= ((c>>5)&1)<<1
    P = (q0 | q1<<8 | q2<<16 | q3<<24) ^ KEY
    return symbols for the eight nibbles of P (low nibble first)
```

Field extraction after a successful check:

```
mission_index = (q3 >> 2) & 0xF     # 0..15 ; level = index + 1 ; >12 unused
mode          = (q3 >> 6) & 0x3     # 1 Normal, 2 Hard, 3 hidden, 0 unused
progress      = 26 payload bits minus those six (20 bits, unlabelled)
```

The validator's only gate is the checksum; it does not range-check the mission
index. The accept path then stores `mode` at `0x03001F10`/`state+0x24` and the
mission-start state machine copies `(q3>>2)&0xF` to `state+0x26` and calls the
mission-record loader.

## 6. Tables

### 6.1 Alphabet (16 symbols = 4 bits)

`B`=0 `C`=1 `D`=2 `F`=3 `G`=4 `H`=5 `J`=6 `K`=7 `L`=8 `M`=9 `P`=10 `R`=11
`S`=12 `T`=13 `X`=14 `Z`=15

### 6.2 Published codes decoded (all pass the checksum)

| Published as | Code | Level idx | Level | Mode |
|---|---|---:|---:|---:|
| Level 2 | `MDKMZKCC` | 1 | 2 | 1 |
| Level 2 (Hard) | `LFKMZCDT` | 1 | 2 | 2 |
| Level 3 | `BHSZSKTC` | 2 | 3 | 1 |
| Level 3 (Hard) | `SRKLKCXT` | 2 | 3 | 2 |
| Level 4 | `ZKTSHKMC` | 3 | 4 | 1 |
| Level 4 (Hard) | `SRZLKCPT` | 3 | 4 | 2 |
| Level 5 | `JLPFDKHB` | 4 | 5 | 1 |
| Level 5 (Hard) | `SRKCKCJS` | 4 | 5 | 2 |
| Level 6 | `HMDBRKCB` | 5 | 6 | 1 |
| Level 6 (Hard) | `SRZKKCBS` | 5 | 6 | 2 |
| Level 7 | `GLDKLKZB` | 6 | 7 | 1 |
| Level 7 (Hard) | `GRSGRCSS` | 6 | 7 | 2 |
| Level 8 | `GLPKLKRB` | 7 | 8 | 1 |
| Level 8 (Hard) | `GPTHLCLS` | 7 | 8 | 2 |
| Level 9 | `GLDJBKKF` | 8 | 9 | 1 |
| Level 9 (Hard) | `GPHGBCGZ` | 8 | 9 | 2 |
| Level 10 | `GLPJBKFF` | 9 | 10 | 1 |
| Level 10 (Hard) | `SRPGBCBZ` | 9 | 10 | 2 |
| Level 11 | `GLDKBKZF` | 10 | 11 | 1 |
| Level 11 (Hard) | `GRFHBCSZ` | 10 | 11 | 2 |
| Level 12 | `GLPKBKRF` | 11 | 12 | 1 |
| Level 12 (Hard) | `GRRHBCLZ` | 11 | 12 | 2 |
| Level 13 | `GLDJLKHD` | 12 | 13 | 1 |
| "Unlimited Ammo" | `RBJPXCKC` | 0 | 1 | 1 |
| "Weird level" | `GLDJKHDM` | 1 | 2 | 3 |

### 6.3 Field layout of `q = P ^ 0x571EA60B`

| Byte | Bits | Use |
|---|---|---|
| `q0` | 3, 4 | checksum bits 0, 1 |
| `q0` | 0-2, 5-7 | progress payload (6 bits) |
| `q1` | 3, 4 | checksum bits 2, 3 |
| `q1` | 0-2, 5-7 | progress payload (6 bits) |
| `q2` | 3 | checksum bit 4 |
| `q2` | 0-2, 4-7 | progress payload (7 bits) |
| `q3` | 1 | checksum bit 5 |
| `q3` | 2-5 | mission index (4 bits) |
| `q3` | 6-7 | mode (2 bits) |
| `q3` | 0 | progress payload (1 bit) |

Total payload = 6+6+7+7 = 26 bits; 6 are mission/mode, 20 are progress.

### 6.4 Novel codes

| Code | Level | Mode | Meaning |
|---|---:|---:|---|
| `RBJPXCKT` | 1 | 2 (Hard) | Level 1 in the mode used by the published "(HARD)" set |
| `RBJPXCKH` | 1 | 0 | Level 1, mode 0 (accepted, unused value) |
| `DFTLHBKC` | 1 | 1 (Normal) | repaired fresh-game Normal password |
| `DFTLHBKT` | 1 | 2 (Hard) | repaired fresh-game Hard password |
| `SRFGLCKX` | 13 | 2 (Hard) | level 13 in the Hard mode (empty briefing — no data) |
| `RBXPJCCD` | 14 | 1 (Normal) | out-of-table level (empty briefing) |
| `RBJRJCTD` | 15 | 1 (Normal) | out-of-table level (empty briefing, then black screen) |
| `RBXRJCMD` | 16 | 1 (Normal) | out-of-table level (empty briefing, crash on continue) |

## 6b. Enumeration

### Space definition

* Input alphabet: exactly 16 symbols (the alphabet string at `0x083813EC`); the
  entry screen offers no other characters.
* Length: exactly 8 symbols (8 slots; the accept path packs 8 nibbles).
* Representable inputs: 16^8 = 2^32 = **4,294,967,296**.
* Accepted inputs: 2^26 = **67,108,864** (the six checksum bits are a function
  of the other 26 bits, so exactly 1 in 64 inputs is accepted).
* Payload fields: mission index (4 bits, 16 values), mode (2 bits, 4 values),
  progress (20 bits).
* Mission table: index `0…12` (levels 1…13) has data; indexes `13…15` pass the
  checksum but have no mission record. Mode `1` (Normal) is the only mode with
  a published code for every level; mode `2` has levels 1…12 (level 13 mode 2
  has no data); mode `3` is used by the published weird-level code; mode `0` is
  accepted but not offered by Options.

### Novel code and in-game proof

`RBJPXCKT` (mission index 0, mode 2) is **not present in any published list**
(GameFAQs archive, SuperCheats, Project Cheat Codes, VGChartz, IGN wiki all lack
it; a targeted web search for the literal returns nothing).

1. Entered through the on-screen keyboard — screenshot
   `shots/06_novel_L1hard_entered.png`.
2. `A` accepted it and the game entered the Mission 1 briefing "OK, Ira, you're
   in position. To gain access to the lab, you'll need to find the silver
   passcard…" (`shots/05_level2_briefing.png` is the same screen for `MDKMZKCC`;
   the L1-hard briefing is captured in the run log and the in-game frame
   `shots/07_novel_L1hard_ingame.png`).
3. In game, `Start` → `View Password` displays **`RBJPXCKT`**
   (`shots/08_novel_L1hard_password_readback.png`).
4. RAM check (savestate `game.ss4`, loaded in the mGBA CLI debugger): session
   struct `0x030016F0` contains `00 00 00 80 0B A6 1E D7`, i.e. decoded
   `q3 = 0x80` (mode 2, index 0) and raw packed `P = 0xD71EA60B`. The Normal
   code `RBJPXCKC` gives `q3 = 0x40` in the same struct.

A second novel code, `DFTLHBKC`, was derived from the game's own fresh-game
password `DFHLHBHC`: its payload is `[0x21,0x23,0x13,0x40]` but its check field
is `0x33` where the checksum over that payload is `0x17`; recomputing the check
characters gives `DFTLHBKC`, which the game accepts and uses to start Mission 1
(`shots/14_freshgame_generated_password.png` shows the game's `DFHLHBHC`,
`shots/15_repaired_code_accepted.png` shows the accepted repaired code). The
Hard variant `DFTLHBKT` is likewise accepted and starts Mission 1
(`shots/16_repaired_hard_accepted.png`).

### Bounds proven by rejection / failure

| Test | Value | Result |
|---|---|---|
| One-character change to a valid code | `MDKMZKCD` (from `MDKMZKCC`) | **rejected**; screen stays on Password (`shots/09_bad_checksum_rejected.png`) |
| Game-generated fresh Normal code | `DFHLHBHC` | **rejected** |
| Game-generated fresh Hard code | `DFHLHBHT` | **rejected** |
| Out-of-table level 14 | `RBXPJCCD` (index 13) | checksum accepts; **empty briefing**, no mission text (`shots/10_level14_empty_briefing.png`) |
| Out-of-table level 15 | `RBJRJCTD` (index 14) | checksum accepts; empty briefing, then a **black screen** (`shots/11_level15_black.png`) |
| Out-of-table level 16 | `RBXRJCMD` (index 15) | checksum accepts; empty briefing, then `A` crashes the core: `GBA Memory: Jumped to invalid address: FFFFFFFE`, `GBA: Illegal opcode: 0000b710` (`shots/11_level16_empty_briefing.png`) |
| Index 15 in mode 3 | `RBXRJCMP` | same empty briefing and crash |

The checksum is therefore the *only* gate the entry screen applies; the mission
index is not range-checked, and the mission table is 13 records deep.

### Published list corrections (proven in the emulator)

* `GLPKBKRF` decodes to index 11 → Level 12, and its briefing is the Level 12
  "dot every I … canyonlands … 100%" text (`shots/13_level12_GLPKBKRF.png`).
  The lists that print it for Level 11 are wrong.
* `GLDKBKZF` decodes to index 10 → Level 11, and its briefing is the Level 11
  "close the air-shaft valve" text (`shots/12_level11_GLDKBKZF.png`).
* `RBJPXCKC` decodes to Level 1 with an all-zero 20-bit progress field; the
  in-game HUD shows ∞ ammunition, which is what the "Unlimited Ammo" submission
  describes.

## 7. Validation evidence

**Observed (emulator, screenshots/RAM):**

* Title menu (`01`), password screen with 8 slots (`02`), Options with
  Difficulty/Music/SoundFX (`03`), pause menu with 5 entries (`04`).
* `MDKMZKCC` accepted → Level 2 briefing (`05`); `LFKMZCDT` accepted → same
  briefing.
* `GLDKBKZF` → Level 11 briefing; `GLPKBKRF` → Level 12 briefing (`12`,`13`).
* `RBJPXCKT` accepted → Mission 1, pause readback `RBJPXCKT` (`06`–`08`).
* `MDKMZKCD` rejected (`09`); `RBXPJCCD` empty briefing (`10`); `RBJRJCTD`
  empty briefing then black screen; `RBXRJCMD` empty briefing then crash (`11`).
* Fresh-game `Current Password` values `DFHLHBHC` (Normal) and `DFHLHBHT`
  (Hard) (`14`); both rejected on entry; repaired `DFTLHBKC` accepted (`15`)
  and repaired `DFTLHBKT` accepted (`16`).
* mGBA debugger RAM: `0x030016F0` = `00 00 00 40 0B A6 1E 17` for `RBJPXCKC`
  and `00 00 00 80 0B A6 1E D7` for `RBJPXCKT`; input buffer `0x03001F1C…23`
  changes exactly as the on-screen slots change.

**Derived (instruction-level):**

* The 8 nibbles are packed low-nibble-first into `0x030016F4…F7` at
  `0x0829099C`–`0x082909D8`.
* The validator at `0x0829098C` XORs with `0x571EA60B`, extracts the six check
  bits, masks them out, sums the four masked bytes and compares the low six
  bits; on success it stores `q3>>6` at `0x03001F10` and `state+0x24`.
* The mission index is `(q3>>2)&0xF`, copied to `state+0x26` at `0x0829009A`
  and passed to the mission loader `0x08290A64` (table `0x08144A9C`, stride
  `0x5A`) at `0x082901AE`/`0x082903CE`.
* The encoder at `0x08290738` builds the packed password from gameplay counters
  and is called from the mission-start state machine (`0x08290082`,
  `0x082903A0`).
* The display routine at `0x0829AE20` reads `0x030016F0+4…7`, splits each byte
  into nibbles and indexes the alphabet at `0x083813EC`.

**Inferred:**

* Mode 2 is "Hard": the Options screen offers Normal/Hard, and the game's own
  fresh-game encoder changes only the two mode bits of the password when
  difficulty is switched (`DFHLHBHC` ↔ `DFHLHBHT`). The gameplay effect of mode
  2 (enemy health/damage) was not isolated; the field's role as the difficulty
  selector is derived, not measured in combat.
* The 20 unlabelled progress bits are gameplay statistics; the encoder compares
  counters at the stats struct (`+0x2E,+0x32,+0x36,+0x3A,+0x3E,+0x42`) against
  threshold tables before packing bits 0/1/2 of each output byte.

## 8. Unknowns

* The meaning of each of the 20 progress bits (weapon/ammo/objective counters) is
  not individually labelled; only the mission and mode fields are exercised.
* Mode 3's gameplay effect (the published "weird level" glitch) was not
  reproduced beyond accepting the code; mode 0 is accepted but no Options value
  selects it.
* Why the fresh-game `Current Password` carries a stale check field: the encoder
  at `0x08290738` computes the correct checksum from the bytes it packs, yet the
  bytes the pause menu displays for a fresh game fail the validator. The most
  likely explanation is that the packed bytes are re-displayed after later state
  edits, but the exact write ordering was not traced. The repair experiment
  (`DFTLHBKC`) proves the display/entry mapping itself is correct.
* The header checksum word at `0xBE` is zero rather than the computed `0xF61C`;
  the ROM is otherwise coherent and boots. This may be a dump/repack artifact.

## 9. Tooling

* `mGBA 0.10.5` SDL + `Xvfb :130` + `openbox` + `xdotool` + `scrot`/ImageMagick
  `import`.
* `mGBA` built-in CLI debugger (`mgba -d`, `stdbuf -oL`): breakpoints, read/write
  watchpoints, `x/1 addr len` memory dumps, `frame`/`c`. Used to prove writes to
  the input buffer and to dump IWRAM/EWRAM from savestates (`game.ss1`–`ss4`).
* Python 3 + Capstone 5.0.7 for Thumb disassembly and literal-pool scans.
* `strings -t x -n 4` for recon; literal search for every published code.
* `alienators_pw.py` (next to this report) implements `decode()`/`encode()` and
  reproduces every published code.

Commands used to reproduce the static results:

```bash
md5sum game.gba; sha1sum game.gba; sha256sum game.gba
strings -t x -n 4 game.gba | grep -iE "password|debug|secret|sound|test|cheat"
grep -abo "MDKMZKCC" game.gba        # no hit: codes are not stored literally
python3 alienators_pw.py MDKMZKCC LFKMZCDT GLDKBKZF GLPKBKRF RBJPXCKC
```

Legal note: no ROM, graphics, music or game text is redistributed; only hashes,
addresses, algorithms and our own generated codes are published.
