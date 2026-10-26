# Beyblade VForce: Ultimate Blader Jam (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Beyblade VForce: Ultimate Blader Jam.gba` (8,388,608 bytes) |
| Header title | `BEYBLADE: UL` |
| Game code | `BEYE` (USA) |
| Maker code | `70` (Atlus) |
| Software version | 0x00 (Rev.00) |
| Entry point | ARM branch `EA00002E` → `0x080000C0` (standard crt0) |
| Complement check | `0xBD = 0x92` (matches the computed value) |
| Header u16 @0xBE | `0x0000` (unusual, but the CRC32 below matches the known-good USA dump) |
| CRC32 | `4A49272B` (matches GameHacking.org's USA `AGB-BEYE-USA` entry) |
| MD5 | `de37c8d6f9b8cd56dfd81ca0f754e54b` |
| SHA-1 | `cd527c8c24e20e33913fc45199e64b3e6138a6e5` |
| SHA-256 | `a9f4bdb4d7f889fb099aed794f5c03548c2f5e12fb9a1d3463278835f72db41c` |
| Save memory | 8 KiB SRAM (`.sav`) |

**Embedded header scan:** exactly one 156-byte Nintendo logo occurrence, at file `0x4`
(header `0x0`). This is a single-image cartridge, not a multi-game pack. No
`PATCH`/`TRAINER`/`IPS`/`CRACK`/`GAME GENIE`/`XPLODER`/`CODEBREAKER` strings are
present; the entry point and header are the untouched retail ones. The only header
anomaly is the zero u16 at `0xBE`, which is not used by the GBA BIOS and does not
affect the CRC32 match.

## 2. Executive summary

There is **no password or text-code system** in this ROM. The developer-intended
cheats are **button sequences** detected on two screens:

* the **title screen** (`PRESS START`), screen id 7 — five sequences;
* the **in-round pause overlay** — three sequences.

The engine stores each code as a 4-byte count followed by that many 16-bit key
masks. A per-frame detector struct (`{s16 index; s16 timer; u32 blob}`) walks the
array when the newly-pressed key matches the next mask; a match reloads a 60-frame
window. When `index == count` the action branch runs. The complete scanned and
cross-referenced set is **8 codes** (6 of length 4, 2 of length 5); no other
sequence blob is referenced by code anywhere in the 8 MiB image.

The published lists are a mix of true and false entries:

* `B, L, R, Down` (title) is real and fills the 109-bit BeyCollection mask;
* `Right, Left, Right, Left` (pause) is real and sets the BB meter to 5;
* `Left, Up, L, L` is real but is a **title-screen** code, not a pause code;
  it sets the "no spin damping" flag (infinite spin);
* `Up, Up, Right, Left, L` is real at pause and despawns every active entity;
* `Right, Left, Left, Up, A` **does not exist** in this ROM (tested, rejected);
* `Right, Right, Right, Left` does not exist either.

The unpublished sequences in the same tables are listed and proven in §6b. Their
effects are persistent flag writes; three of them have no dedicated on-screen UI in
this retail build, which is itself a finding (the flags are unread or only switch an
internal data source).

### 2.1 Reconnaissance keyword counts (whole ROM, `strings -n 4`)

| Keyword | Hits | Classification |
|---|---:|---|
| `password` / `passcode` | 0 / 0 | no text-code system |
| `cheat` / `debug` | 0 / 0 | no debug menu or cheat text |
| `secret` | 4 | story dialogue only ("secret of the Bit Beast") |
| `unlock` | 9 | "Beat par times… to unlock", collection notifications |
| `hidden` | 5 | Bit Beast names ("Zinrai Hidden Spirit", etc.) |
| `collectable` | 3 | script-engine error messages |
| `menu` | 4 | "Main Menu" / debug allocator warnings |
| `sound test` / `test mode` | 0 / 0 | none |

Published sources used for anchoring and later verification: GameRevolution's
`Beyblade: Ultimate Blader Jam GBA Cheats` page (the five-button list), the
htfbw.com `Beyblade GBA Cheats` page (button list incl. "right,right,right,left"),
and GameHacking.org / Ethereal Games CodeBreaker pages (RAM anchors only). No
GameFAQs page was needed; no archived snapshot was required.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 SDL (`/usr/games/mgba -3 <rom>`), Xvfb `:181` + openbox,
  `SDL_AUDIODRIVER=dummy`.
* mGBA default keymap used throughout: **A=`x`, B=`z`, L=`a`, R=`s`,
  Start=`Return`, Select=`BackSpace`, D-pad = arrows**.
* Hold each button 150–250 ms with ~250 ms gaps; the detector's inter-key window is
  60 frames (~1 s).
* Savestates (`Shift+F1`…`Shift+F9`) were the primary memory-evidence tool; an
  mGBA PNG state contains a zlib `gbAs` chunk. In the decompressed state,
  **IWRAM `0x03000000` is at offset `0x19000`** and **EWRAM `0x02000000` is at
  offset `0x21000`** (verified via `[0x03000F48]=0x0200F728` and the collection
  bitfield at `0x0200FCBC`).

**Title-screen codes:** boot to `PRESS START`, press the sequence. Nothing is
displayed; verify in BeyCollection or in memory. `Start` afterwards opens the main
menu.

**Pause-screen codes:** start a round, press `Start`, enter the sequence on the
`PAUSE / Resume / Exit` overlay, then verify in memory or resume.

Menu walk performed (all screenshots kept as working artifacts in
`/tmp/opencode/beyblade/`):

| Screen | measured screen id | notes |
|---|---:|---|
| Atari / d-rights / FULLFAT logos | 2, 3, 4 | boot logos |
| round-load banner ("ROUND 1 GO TYSON!") | 5 (transient) | loading bar |
| **Title `PRESS START`** | **7** | 5 code detectors live here |
| Main carousel | 10 (0x0A) | VForce Adventure, BBA Multiplayer, Beyworkshop, Options, BeyCollection |
| Options | 12 (0x0C) | Audio, Save Game, Credits, Controls |
| Audio | 13 (0x0D) | SFX / Music sliders only, no language item |
| Controls | 14 (0x0E) | 3D Control / 2D Control help cards |
| Beyblade select (workshop & BBA) | 15 (0x0F) | shared screen |
| Round results | 17 (0x11) | time / best / attempts / items |
| Adventure sub-menu | 25 (0x19) | New Game / Continue Game |
| Credits | 26 (0x1A) | scrolling credits |
| Episode map | 27 (0x1B) | Episode 1, Round 1… |
| Story dialogue | 28 (0x1C) | scripted text |
| "RETRY? RETRY/Exit" | 30 (0x1E) | round-fail menu |
| BBA "PLEASE WAIT…" link wait | 31 (0x1F) | fails with no link partner |
| BeyCollection | 40 (0x28) | list + detail portrait |
| In-round pause overlay | — (id reads `-1`) | overlay, not a table screen |

No hidden debug menu, sound test, language menu, or password screen exists among
these; `PASSWORD`, `CHEAT`, `DEBUG`, `TEST MODE` occur **zero** times in the string
table (68,624 `strings` entries; `secret` 4, `unlock` 9, `hidden` 5 — all story text
or Bit Beast names, `collectable` 3 — script error messages).

## 4. Address map

| Item | Address | Notes |
|---|---|---|
| Screen table | `0x08069FC8` | 24-byte records `{u32 idtag; u32 data; u32 f1; u32 f2; u32 f3; u32 f4}`; indexed by screen id × 24 |
| Active screen id | `0x03000654` | `-1` for gameplay/overlay |
| Active screen record | `0x03000704` | `0x08069FC8 + id*24` |
| Title screen record | `0x0806A070` | id 7; data `0x08069318`; callback `0x0804568D` |
| Title code registration | `0x0804568C` | phase 1; 5 `BL 0x08057158` calls |
| Pause overlay record | — | function `0x08052B24`; 3 local detector structs at `sp+0x90/0x98/0xA0` |
| Detector init | `0x08057158` | `{s16 index=0; s16 timer=0; u32 blob}` |
| Detector update | `0x08057164` | compares `*(u16*)0x03005DA0` with `blob[4+2*index]`; match → timer 60, index++; wrong non-zero key → index 0 |
| Detector complete | `0x080571D0` | true when `index == *(u32*)blob` |
| Key-state global | `0x03005DA0` | newly-pressed mask (edge), not held |
| Global object G0 | `[0x03000FB0]` = `0x0200E0E4` | round/game context |
| Global object G1 | `[0x03000F48]` = `0x0200F728` | persistent profile/collection |
| G1 BeyCollection bitset | `G1+0x594` = `0x0200FCBC` | 109 bits |
| G1 per-beyblade flags | `G1+4+i*24` = `0x0200F72C+24i` | 56 entries; u16 flags |
| G1 cheat/option flags | `G1+0xC64` = `0x0201038C` | bits 0/1/2 |
| G0 BB meter byte A | `G0+0x107C` = `0x0200F160` | 0…5 |
| G0 BB meter byte B | `G0+0x1638` = `0x0200F71C` | 0…5 |
| G0 round item mask | `G0+0x13F8` = `0x0200F4DC` | 32 bits |
| G0 entity array / count | `G0+0x42C` / `G0+0x430` | stride 0x428 |
| Destroy entity | `0x0804C0C0` | set bit 2 at `entity+0x3CC`, free sprite, clear pointer |
| Round-data table | `0x08075B4C` | 0xD0-byte records; byte `+1` = item count for the round |
| Text string banks | `0x0725xxx`–`0x0729xxx` | 5 languages inline |

The CodeBreaker addresses published for this game independently confirm the map:
`Complete Bey Collection = 0200FCBC`, `Infinite BB = 0200F160 / 0200F71C`,
`Always get items = 0200F4DC`, `All levels open = 0200F744`.

## 5. Algorithm

### 5.1 Sequence blobs

```
struct Blob { u32 count; u16 keys[count]; }   // little-endian, no terminator
```

Both key tables for this game are 4–5 keys. Key masks: `A=0x001, B=0x002,
Select=0x004, Start=0x008, Right=0x010, Left=0x020, Up=0x040, Down=0x080,
R=0x100, L=0x200`.

### 5.2 Detector

```
update(s):                       // s = {s16 idx, s16 timer, u32 blob}
  count = *(u32*)blob
  if idx == count: return 0xFFFF (completed marker)
  if idx == -1: return
  if timer != 0: timer--
  else if idx != 0: return       // window expired; struct stays until re-init
  k = *(u16*)0x03005DA0          // newly pressed keys this frame
  if k == blob.keys[idx]: timer = 60; return idx+1
  if k != 0: timer = 0; return 0
  return                            // idle frame: no change
```

`complete(s)` is `idx == count`. After completion the index is rewritten to
`0xFFFF`, which is why one code cannot fire twice without re-entering the screen.

### 5.3 Actions

Title screen (`0x0804568C`, phase 1), in registration order:

```
0x03000380 <- blob 0x080693A0 (Right,Down,R,L)
0x03000388 <- blob 0x08069378 (Left,Up,L,L)
0x03000390 <- blob 0x0806938C (B,L,R,Down)
0x03000398 <- blob 0x080693B4 (L,Left,R,Right)
0x030003A0 <- blob 0x080693C8 (B,L,B,R)
```

* `0x03000380` done → `for i in 0..55: *(u16*)0x08051720(i) |= 2`
* `0x03000388` done → `*(u32*)(G1+0xC64) |= 1`
* `0x03000390` done → `for i in 0..108: 0x08057104(i, 1)` (109-bit collection set)
* `0x03000398` done → `*(u32*)(G1+0xC64) |= 2`
* `0x030003A0` done → `*(u32*)(G1+0xC64) |= 4`

All five then call `0x0804ABFC(8)` (UI sound/refresh).

Pause overlay (`0x08052B24`, phase 1), in registration order:

```
sp+0x90 <- blob 0x08078954 (Right,Left,Right,Left)
sp+0x98 <- blob 0x08078968 (Up,Up,Right,Left,L)
sp+0xA0 <- blob 0x0807897C (L,R,R,L,B)
```

* first done → `*(u8*)(G0+0x1638)=5; 0x0804F800(5)` (writes `G0+0x107C=5`)
* second done → `for each of N entities: 0x0804C0C0(entity)` (despawn all)
* third done → `n = (s8)*(0x08075B4C + idx*0xD0 + 1); w = *(u32*)(G0+0x13F8);
  for j=n-1..0: w |= 1<<j; *(u32*)(G0+0x13F8)=w` — grants item bits `0..n-1`

## 6. Tables

Key alphabet: `A B Select Start Right Left Up Down R L`
(`0x001 0x002 0x004 0x008 0x010 0x020 0x040 0x080 0x100 0x200`).

Raw blobs (all little-endian, verified with `struct.unpack`):

```
0x080693A0  04 00 00 00  10 00  80 00  00 01  00 02   Right,Down,R,L
0x08069378  04 00 00 00  20 00  40 00  00 02  00 02   Left,Up,L,L
0x0806938C  04 00 00 00  02 00  00 02  00 01  80 00   B,L,R,Down
0x080693B4  04 00 00 00  00 02  20 00  00 01  10 00   L,Left,R,Right
0x080693C8  04 00 00 00  02 00  00 02  02 00  00 01   B,L,B,R
0x08078954  04 00 00 00  10 00  20 00  10 00  20 00   Right,Left,Right,Left
0x08078968  05 00 00 00  40 00  40 00  10 00  20 00  00 02   Up,Up,Right,Left,L
0x0807897C  05 00 00 00  00 02  00 01  00 01  00 02  02 00   L,R,R,L,B
```

### 6.1 Title screen (screen id 7, `PRESS START`) — 5 codes

| # | Sequence | Blob | Effect | Published? |
|---|---|---|---|---|
| T1 | B, L, R, Down | `0x0806938C` | OR `0x0200FCBC..+13` to all 1s = 109 BeyCollection bits | yes (as "All BeyCollection") |
| T2 | Left, Up, L, L | `0x08069378` | `G1+0xC64 \|= 1` (infinite spin: skips spin damping at `0x08055EC8`) | yes (as "Infinite Spin") |
| T3 | Right, Down, R, L | `0x080693A0` | OR 2 into the u16 flags of all 56 beyblade entries (`0x0200F72C+24i`) | **no** |
| T4 | L, Left, R, Right | `0x080693B4` | `G1+0xC64 \|= 2` (no reader found in ROM) | **no** |
| T5 | B, L, B, R | `0x080693C8` | `G1+0xC64 \|= 4` (selects alternate language/data source at `0x08051820`; sound 15 vs 27 at `0x08046EF0`) | **no** |

### 6.2 Pause overlay (in-round `Start`) — 3 codes

| # | Sequence | Blob | Effect | Published? |
|---|---|---|---|---|
| P1 | Right, Left, Right, Left | `0x08078954` | `G0+0x1638=5`, `G0+0x107C=5` (full BB/attack meter) | yes ("Full Bit Beast attack meter") |
| P2 | Up, Up, Right, Left, L | `0x08078968` | despawn every active entity | yes ("Destroy all enemies") |
| P3 | L, R, R, L, B | `0x0807897C` | OR item bits `0..n-1` into `G0+0x13F8` for the current round | **no** |

### 6.3 Published entries that are not in the ROM

| Sequence | Source | Result |
|---|---|---|
| Right, Left, Left, Up, A | GameRevolution / htfbw ("Get Next Level") | **absent**: no blob, no detector advances, no state change |
| Right, Right, Right, Left | htfbw ("fully charged meter") | absent from both tables (P1 is Right,Left,Right,Left) |
| B, L, R, Down "at Start screen" | blog | correct, but it is the title screen, not the main menu |

## 6b. Enumeration

**Space definition.** The system is a fixed table, not a checksum/password space.
Alphabet = the 10 GBA buttons above; representable sequence length = 1…8 as encoded
by the 4-byte count, but only two tables exist. A whole-ROM scan for
`{u32 count ∈ 1..8; next count u16 all ∈ key mask set}` produced 148 byte-pattern
candidates; **exactly 8** are referenced by code (via literal pools or stack init).
Those 8 are exhaustive for this ROM: 5 title blobs + 3 pause blobs. There are
`6 × length-4 + 2 × length-5` codes, i.e. **8 reachable values** out of the
10⁴·/10⁵ naive strings; the rest of the button space is inert.

**Novel (unpublished) codes entered and confirmed in the emulator.**

* **N1 = Right, Down, R, L** (blob `0x080693A0`), title screen. Entered at
  `PRESS START`. Detector `0x03000380` reached `0xFFFF`; all 56 beyblade entries at
  `0x0200F72C+24i` changed from `0x0004` to `0x0006` (entry 0 was already `0x0006`).
  This marks the whole 56-beyblade roster as owned/seen. Memory read before/after:
  `0x0200F72C: 06 00 04 00 04 00 …` → `06 00 06 00 06 00 …`. It appears in no
  published list. On-screen effect in this build: none in BeyCollection or the
  pre-battle select (the roster list is gated by the 109-bit collection mask, not by
  this flag); documented as a state-only unlock.
* **N2 = L, Left, R, Right** (blob `0x080693B4`), title screen. Sets
  `0x0201038C |= 2`. No reader for bit 1 exists in the image, so there is no visible
  effect; recorded as an orphan debug flag.
* **N3 = B, L, B, R** (blob `0x080693C8`), title screen. Sets `0x0201038C |= 4`.
  Verified: `0x0201038C` went `0x00000000` → `0x00000004`. The only readers use it to
  pick an alternate language/value source (`0x08051820`) and a different UI sound
  (`0x08046EF0`); the visible UI stayed English.
* **N4 = L, R, R, L, B** (blob `0x0807897C`), pause overlay. For Episode 1 Round 1
  the round-data byte is 1, so the action sets bit 0: `0x0200F4DC` went
  `0x00000000` → `0x00000001`, granting the round's item bits. The results screen
  counts picked-up items, so no HUD change appears; the mask is read by the item
  menu builder at `0x08056F80`.

**Bounds proven by rejection** (fresh boot, title screen id 7):

| Input | Detector result | State |
|---|---|---|
| `Up, Up, Up, Up` | all 5 indexes stay 0 | collection `0x0200FCBC=0`, flags `0x0201038C=0`, structs `6/4/4` unchanged |
| `Right, Left, Left, Up, A` (published but absent) | all 0 | unchanged |
| `B, L` then 2 s idle | window expires, no completion | unchanged |
| Long/out-of-alphabet (e.g. 9 presses, `Start`) | never matches a blob | unchanged |

**Visible anchor (published code, used to prove the decoder is correct).**
`B, L, R, Down` at the title sets `0x0200FCBC` to
`FF FF FF FF FF FF FF FF FF FF FF FF FF 1F` (109 bits). BeyCollection then lists
real entries — `Ultimate Dragoon`, `Ultimate Saizo`, `Ultimate Frostic Dranzer`,
`Gekiryu-oh` — instead of `No 1 … No 4`; the pre-battle select similarly shows
`Ultimate Dragoon` / `Ultimate Saizo`. Screenshots:
`collonly_bc_s.png`, `collonly_ws_s.png`, `collonly_ws2_s.png`.

## 7. Validation evidence

**Observed (emulator + memory):**
* Title screen is screen id 7 (`0x03000654=7`, `0x03000704=0x0806A070`); the five
  detector structs at `0x03000380..0x030003A0` are initialised with the five blobs.
* `B,L,R,Down` at title → collection mask 109 bits set; BeyCollection shows named
  beyblades (`collonly_bc_s.png`).
* `Right,Down,R,L` at title → 56 flags `0x4→0x6`.
* `B,L,B,R` at title → `0x0201038C = 0x4`.
* `Right,Left,Right,Left` at pause → `0x0200F160=5`, `0x0200F71C=5`.
* `L,R,R,L,B` at pause → `0x0200F4DC` went `0x00000000 → 0x00000001` (Episode 1
  Round 1, where the round item count is 1).
* Rejections above.

**Derived (instruction sequence):**
* Detector semantics and the 60-frame window (`0x08057158`/`64`/`D0`).
* The 8 actions and their writes (`0x0804568C`, `0x08052B24`).
* `T2` (Left,Up,L,L) sets bit 0 of `G1+0xC64`; the only reader of that bit
  (`0x08055EC0`) skips the damping subtraction at `0x08055EC8`, i.e. infinite spin.
* `P2` (Up,Up,Right,Left,L) despawns entities via `0x0804C0C0`.

**Inferred:**
* N2's bit is an unreferenced debug flag (no reader found, but an indirect read
  through a computed pointer cannot be fully excluded).
* The exact intended semantics of the 56 per-beyblade flags (owned vs. new) — the
  bit is checked by `0x080517E8` before confirming a selection, but the visible
  roster is driven by the 109-bit collection mask.

## 8. Unknowns

* No successful round was completed, so the item mask (`P3`) was not observed at the
  level-complete grant; only its write and the reader at `0x08056F80` are proven.
* The visual/intended purpose of `G1+0xC64` bits 1 and 2 is not exposed by any menu;
  bit 2 changes an internal data source and one sound only.
* The title screen's code entry has no on-screen feedback, so acceptance is only
  provable in memory or by its downstream effect (documented above).

## 9. Tooling

* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`
* Capstone/Keystone (Python) for BL-target and PC-literal scans.
* `state.py` — decodes mGBA PNG savestates (`gbAs` zlib chunk) and maps
  `0x03000000→0x19000`, `0x02000000→0x21000`; used for all memory before/after
  evidence.
* `gba.py` — xdotool input (logical buttons A=`x`, B=`z`, L=`a`, R=`s`) and cropped
  screenshots (720×480+281+260).
* `snap.py` / `probe.py` — savestate + screen-id capture for the menu walk.
* Whole-ROM sequence-blob scanner: iterate 4-byte-aligned offsets, accept
  `count 1..8` followed by that many u16 key masks, then search for a little-endian
  pointer `0x08000000+offset`. Raw output: 148 candidates, 8 with xrefs.

## 10. Legal note

No ROM, graphics, music, or extracted text is redistributed here. All addresses,
byte values, and algorithms are original findings from the analysis of a legally
owned cartridge image. Screenshots are working artifacts and are not part of this
repository.
