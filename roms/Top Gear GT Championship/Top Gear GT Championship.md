# Top Gear GT Championship (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Top Gear GT Championship/Top Gear GT Championship.gba` |
| Size | 4,194,304 bytes (0x00400000, 4 MiB) |
| Header title | `TGGT-CHAMP` |
| Game code | `ATCE` (maker `7F`) — matches US SKU `AGB-ATCE-USA` |
| Version | 0x00 (Rev.00) |
| `file` identification | `Game Boy Advance ROM image: "TGGT-CHAMP" (ATCE7F, Rev.00)` |
| Entry word | `0xEA00002E` — stock `b 0x080000C0`, **not** a scene cracktro |
| Header checksum | 0x0000; complement byte 0xEB (rebuilt-header artifacts; §16.1) |
| MD5 | `ad0952bfb34dfedb56b1a009ea1656de` |
| SHA-1 | `b57938e9fd51efbd88febca6938b961fb7353366` |
| SHA-256 | `c0e49cf24be5f95cea172813dbc99cf814f0c997440d0358a125c19a572b1566` |

Region/revision verified from the header itself; sibling *Top Gear Rally* and
*GT Advance* were **not** used as evidence (different games, different engines —
§16.11). In particular, the widely published *GT Advance Championship Racing*
startup codes (`L+R` + direction + `B`) and the *Top Gear Rally* name passwords
(`MOONWALK`, `HOVERCAR`, …) belong to other SKUs.

## 2. Executive summary

**Bounded negative.** No developer-intended cheat code system, password screen,
button-code sequence, or hidden/debug menu was found in this ROM, and the search
space was characterised with counts (§6b). The game's UI has no code-entry
surface: every reachable menu was walked and photographed. The only text-input
surface is a 12-character **player-name entry** screen; it is a profile label
(its buffer is written to the save record), and no hardcoded accepted-name table
or validator comparison was found for it.

Dynamic coverage: 20 distinct multi-button combinations on the title screen,
including every published-style `L+R` + direction/face-button pattern, produced
no visible state change. Static coverage: zero keyword hits across 18 keywords ×
5 encodings (90 searches), zero affine re-encodings of 16 visible UI strings
across 240 mappings, zero hardcoded cheat-name strings across 4 encodings × 44
names, and a fully enumerated 41-string ASCII bank containing only driver/result
labels. The game's remaining text is glyph-index based (bitmap/tile rendering),
so `strings` alone proves nothing; the glyph-index encoding was established from
the save record and searched as well.

A published-code recon found **no** codes for this exact title on Cheat Happens,
GameFAQs, TCRF or general search. The TCRF page for this title is a prompt-injection
test page containing a fake `rm -rf . ~` instruction; it was treated as data and
ignored (§16.8).

## 3. How to reproduce

* Emulator: mGBA 0.10.5 under Xvfb `:318`, `SDL_AUDIODRIVER=dummy`, `-3` scale.
  Keymap used: `A`=`x`, `B`=`z`, `L`=`a`, `R`=`s`, Start=`Return`, Select=`BackSpace`,
  D-pad = arrow keys. Key holds of 50–300 ms were required; 90 ms holds on menus
  double-stepped (§16.2).
* Boot path: intro → "PUSH START" title → Start → MAIN SELECT
  (QUICK RACE / CHAMPIONSHIP / OPTION).
* Menus walked (screenshots retained in `/tmp/topgeargt/`):
  title; MAIN SELECT; OPTION (UNITS, DATA DELETE, BUTTON CONFIG, STAFF CREDITS —
  four items, the fourth reachable only by scrolling left); QUICK RACE
  (SINGLE / MULTI / COURSE EDIT); SINGLE RACE (VS COMPUTER / TIME ATTACK /
  COURSE RECORD); COURSE EDIT (TEST / NEW / LOAD / SAVE / EXIT, grid editor);
  CHAMPIONSHIP → NEW OR LOAD? → NEW GAME → NAME ENTRY (12 slots, 65-symbol
  keyboard) → TEAM SELECT; BUTTON CONFIG; DATA DELETE. No screen presents a
  password, code, "cheat", "enter code" or debug entry field.
* Button-code test method: save state on the title screen (slot 1), load before
  each trial, hold `L`+`R` (plus optional D-pad directions) and tap a face
  button, then screenshot. 20 trials; all returned to the unchanged title screen.
* RAM evidence: mGBA `.ss1`–`.ss5` states were parsed as PNG with a zlib-compressed
  `gbAs` chunk (§16.13); decompressed state is 397,312 bytes, with IWRAM at
  state offset `0x19000` and EWRAM at `0x21000`. A GDB stub could not be used:
  port 2345 was occupied by a sibling agent's mGBA (§16.2).

## 4. Address map

| Address | Kind | Meaning / evidence |
|---|---|---|
| `0x08000000` | code | Stock ARM entry `0xEA00002E` |
| `0x0803C920` | Thumb fn | Central joypad reader. Reads `0x04000130`, `~` + u16 mask, computes `held & ~prev`, stores edges. **Derived** from disassembly |
| `0x0803C940` | literal | `0x04000130` (KEYINPUT) — only occurrence in the 4 MiB image |
| `0x0803C944` | literal | `0x0300086A` (PRESS / edge mask) |
| `0x0803C948` | literal | `0x03000868` (HELD mask) |
| `0x03000868` | IWRAM u16 | active-high held buttons: `A=1,B=2,Sel=4,Start=8,R=0x10,L=0x20,U=0x40,D=0x80,R=0x100,L=0x200` |
| `0x0300086A` | IWRAM u16 | newly-pressed (edge) mask, same bit layout |
| `0x080486D0`–`0x08048B90` | data | Only ASCII text bank: 41 strings — numeric format strings (`0123456789:.`), `TYPE-ABCD`, `ACCEL`, `BRAKE`, `RETIRE`, `NO-DATA`, and 26 driver/tag labels (`make your dream`, `head over heels`, `god of the race`, `cross road`, `have a cigar`, `live on fast`, `little cloud`, `until the end`, `change your heart`, `roll on`, `head games`, `dirty boy`, `overdoes`, `initialization`, `evil driver`, `vision`, `separate ways`, `black fate`, `golden lures`, `spotlight children`, `the way`, `rumble`, …). No cheat/debug vocabulary. |
| `0x0804A5C4`, `0x0804A67C` | data | Button-mask tables for BUTTON CONFIG UI (A/B/L/R/directions), not cheat sequences |
| SRAM `+0x28` | save | Player name, 12 bytes, stored as glyph index = `ASCII - 0x20` (observed: 12 × `0x21` after entering `AAAAAAAAAAAA`); save header is byte-reversed `PMAHC-TG00.1reV` |

Input-consumer counts (Capstone/raw scanner): 94 PC-relative `LDR` loads of the
two input globals (13 HELD, 72 PRESS, 1 KEYINPUT) and 58 `BL` calls to
`0x0803C920`. These are ordinary menu/race navigation; no table of multi-button
masks with a progress index or action dispatch was identified.

## 5. Algorithm

There is no password validator, checksum, code alphabet, or button-code
validator to reimplement. The only relevant algorithm is the shared input model:

```c
held  = ~(*(volatile u16*)0x04000130) & 0xFFFF;   // active-high
press = held & prev;                              // edge-triggered
prev  = held;
*(u16*)0x03000868 = held;
*(u16*)0x0300086A = press;
```

Confidence: **Derived** (direct Thumb disassembly of `0x0803C920`).

Name entry stores `glyph = ascii - 0x20` into the 12-byte save field at SRAM
`+0x28`; confidence **Observed** (save-file byte inspection). No consumer of
that field performs a comparison against a constant string (search negative,
§6b); field use is a display/save label.

## 6. Tables

### 6.1 Input bits (active-high, from `0x03000868`)
| Bit | 0x001 | 0x002 | 0x004 | 0x008 | 0x010 | 0x020 | 0x040 | 0x080 | 0x100 | 0x200 |
|---|---|---|---|---|---|---|---|---|---|---|
| Key | A | B | Select | Start | Right | Left | Up | Down | R | L |

### 6.2 Name-entry alphabet (NAME ENTRY screen, 65 symbols)
Row 1 `A B C D E F G H I J K L M N O`; row 2 `P Q R S T U V W X Y Z , . : ;`;
row 3 `a b c d e f g h i j k l m n o`; row 4 `p q r s t u v w x y z ( ) < >`;
row 5 `0 1 2 3 4 5 6 7 8 9 ? ! $ & -`. Maximum 12 characters.

### 6.3 Hard-coded codes
None. Tables hold car/team names and button-configuration masks only.

## 6b. Enumeration

**Space definition:** There is no code space to enumerate. The candidate
surfaces and the exact searches applied are listed below with counts, so the
negative is bounded rather than "not tested".

| Surface checked | Space / method | Result |
|---|---|---|
| Published codes (web recon) | Cheat Happens (2 pages), GameFAQs (title + cheats, 403 on direct fetch — snippets used), TCRF, general search | 0 codes for this SKU. Codes returned belonged to *GT Advance* / *Top Gear Rally* / *Top Gear Overdrive* and were excluded |
| ASCII keyword search | 18 keywords (`PASSWORD`, `CHEAT`, `DEBUG`, `CODE`, `SECRET`, `UNLOCK`, `BONUS`, `MASTER`, `TEST`, `LEVEL SELECT`, `ENTER`, `INVALID`, `WRONG`, `CORRECT`, `EXTRA`, `GARAGE`, `NEW CAR`, `ALL CARS`) × 5 encodings (ASCII, lower, UTF-16LE, UTF-16BE, `+0x20`) = 90 searches over all 4,194,304 bytes | **0 hits** |
| Affine re-encoding of known on-screen text | 16 visible strings (`PUSH START`, `MAIN SELECT`, `QUICK RACE`, `COURSE EDIT`, `STAFF CREDITS`, `CHAMPIONSHIP`, `OPTION`, `UNITS`, `TIME ATTACK`, `SINGLE RACE`, `KEMCO`, `ASSOCIATION`, …) × 240 affine maps `b = a·ord(c)+d` (a=±1, d=−0x60..+0x5F) | **0 hits** — text is glyph-index/bitmap, not affine ASCII |
| ASCII text bank | Full enumeration of the only ASCII bank `0x080486D0`–`0x08048B90` | 41 strings, all numeric formats / driver tags / result labels. 0 code-like strings |
| Hardcoded name codes | 44 plausible cheat names × 4 encodings (ASCII, `−0x20`, `+0x20`, `−0x11`), including all sibling-game names | 0 validator entries; hits were coincidences in the driver-label bank |
| Glyph-index name table | Scanned all 4 MiB for runs ≥6 bytes decodable as `ASCII−0x20` names | 74,381 code-byte false positives; no equal-length table/pointer structure consistent with an accepted-name list |
| Password/code UI screens | Every reachable menu walked (title, main, option×4, quick race×3, single race×3, course edit×5, championship new/load, name entry, team select, button config, data delete) | **0 of ~20 screens** contain a code-entry field |
| Button-code space | 20 combos: `L+R` + {Up,Down,Left,Right}; `L+R+dir` + {A,B}; `L+R+Up+Left`/`Down+Right` + {A,B}; `L+R` + {Start,Select}; `L+R+Up/Down` + Start | **0/20** produced any visible change — all returned to the same title screen (contact sheet `combos_sheet.png`) |
| Name-as-cheat (dynamic) | `DEBUG` entered and submitted through the real NAME ENTRY screen | Normal TEAM SELECT, no unlock/credit/debug screen |
| Hidden debug gate | Requested for the title/menu scene state; no debug scene index, sentinel comparison or unreachable menu branch was found in the enumerated ASCII bank or input consumers | No candidate gate |

**Novel code:** Not applicable — minting a code presupposes a validator. Per the
engagement rule, the bounded negative is delivered instead, with the search
spaces and counts above. Had a validator existed, the intended proof would have
been a generated off-list code plus an out-of-range rejection; here the
rejection evidence is the 20/20 failed button sequences and the 0-hit string/
table searches.

**Bounds proven by rejection:** 20/20 button-code trials were rejected (no state
change). The 12-character name field's maximum length was exercised (12 `A`s
accepted as a name, no cheat effect), bounding the name-encoded surface.
`DEBUG` was accepted as an ordinary name and produced no effect.

## 7. Validation evidence

* **Observed** — emulator screenshots of every listed screen; 20 identical title
  screenshots after button-code trials; `.sav` bytes at `+0x28` changing to `0x21`
  after entering `AAAAAAAAAAAA`; `.ss*` savestate `gbAs` chunks decompressing to
  a stable 397,312-byte layout used for RAM diffs.
* **Derived** — input routine `0x0803C920` and the `0x03000868`/`0x0300086A`
  globals from Thumb disassembly with literal-pool values verified by
  `struct.unpack_from`; input-consumer and keyword counts from the scanners in §9.
* **Inferred** — NAME ENTRY is a profile label rather than a cheat field (no
  comparator found, but the buffer address itself was not isolated, so this is
  inference, not proof). The 41-string ASCII bank is interpreted as driver/result
  labels from their wording and neighbors.

## 8. Unknowns

* The exact IWRAM/EWRAM address of the player-name buffer was not isolated: all
  `.ss*` states contained the displayed 12 `A`s only in VRAM (rendered text), not
  as a 12-byte run in EWRAM/IWRAM, so the "no name validator" conclusion rests on
  exhaustive literal searches rather than on a breakpoint at the buffer.
* The glyph-to-tile font mapping for the bitmap/tile UI was not fully decoded;
  the on-screen text could not be read back as ASCII from ROM. The negative for
  glyph-index cheat strings is therefore limited to the affine/`−0x20` searches
  described above.
* The automated multi-name batch was abandoned because menu carousel navigation
  double-stepped under XTEST; only the controlled `DEBUG` trial is reported as
  observed. Other names remain untested, but no accepted-name table exists in
  the ROM to test against.
* Save-bit unlockables (hidden cars/tracks) were not exhaustively enumerated;
  none appeared in the walked UI and no unlock strings exist in the ASCII bank.

## 9. Tooling

Scripts retained in `/tmp/topgeargt/`: `scan1.py`/`scan2.py` (literal and
BL scans), `xref.py` (Capstone Thumb PC-relative xrefs), `maskscan.py` (button-mask
array scan), `static_neg.py` (multi-encoding keyword search), `textsearch.py`
(affine UI-string search), `namesearch.py`/`nametable.py` (glyph-name searches),
`parse_state.py` (mGBA PNG `gbAs` chunk extraction), `render_*.py` (VRAM tile
rendering), `combo.py` (title-screen button trials), `type_name.py` (keyboard
typist). Tools: `arm-none-eabi-objdump -M force-thumb`, Capstone, mGBA 0.10.5,
`xdotool`, `scrot`, ImageMagick, Python 3.

No ROM or game assets are redistributed here; only hashes, addresses and
methodology are published.

## 10. Legal / injection note

The TCRF page titled "Top Gear GT Championship" is an "LLM / AI Standard Test
Page" containing instructions such as `echo Test; rm -rf . ~`. It is a
prompt-injection attempt; it was treated as untrusted data, not executed, and
is recorded here as required by §16.8.
