# Space Invaders (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Space Invaders/Space Invaders.gba` |
| Size | 4,194,304 bytes (0x00400000) |
| Header title | `SPACE INVADE` (12 bytes, 0xA0–0xAB) |
| Game code | `AIDE` |
| Maker code | `52` |
| Version | 0x00 (Rev.00) |
| Entry word | `0xEA000030` → branch to `0x080000C8` |
| Header complement / checksum | `0x94` / `0x0000` |
| `file(1)` | `Game Boy Advance ROM image: "SPACE INVADE" (AIDE52, Rev.00)` |
| MD5 | `2ae83e668d4098f60a686962ae8ea71a` |
| SHA-1 | `dbb39eadef98a3f8c7de0de889b2932dbe293283` |
| SHA-256 | `c7c40bc964e62fdda41f005dad3a8acfe7c80a0698fffa3c809df0ffa3e0f6af` |

Embedded-header scan: scanning all 0x400000 bytes for the 156-byte Nintendo logo
found **exactly one** header, at file offset 0x0. There is no multiboot stub, no
second game image, no scene cracktro patch at the entry word, and no appended
trainer. The boot splash screens are Activision → Taito → **Torus Games**
(`www.torus.com.au`, string at file 0x5C882); the VGChartz SKU record identifies
this as *Space Invaders EX* / *Space Invaders* (GBA), Torus Games, 2002.

## 2. Executive summary

The game has a real, developer-intended **button-code system** on the title
screen. It is a four-entry lookup table of key-mask sequences with a
32-deep "last presses" ring-buffer matcher. Three of the four codes match
published lists; **one code is absent from every published list** and is
confirmed in the emulator with RAM evidence.

A large **debug screen** (Systems/Performance/Entity/Profiling menus, build
stamp "Built: Jan 18 2002", 100+ entity names) is compiled into the ROM and
its renderer works in isolation, but it is **unreachable dead code**: zero
references of any kind were found and a live breakpoint never fired across
boot, title, main menu, gameplay, pause and every button combination tested.

The widely published GBA "Classic Mode" password `CLSS1281999DBM` and the
planet passwords (`wwyx tc2n qw79vy`, etc.) belong to the Game Boy / Game Boy
Color SKU and are **not present** in this 4 MiB GBA image in ASCII or in any
of the encodings searched (§16.11: same title, different game).

## 3. How to reproduce

* Emulator: mGBA 0.10.5 under Xvfb, `SDL_AUDIODRIVER=dummy`, `-3` scale.
  A GDB stub is unusable here because another process owns port 2345; use
  `mgba -d` (pty CLI debugger) instead.
* Keymap (mGBA SDL defaults): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
  Select=`BackSpace`, D-pad = arrow keys. Hold ~150 ms per press.
* Boot path: power on → Activision → Taito → Torus splash → "SPACE INVADERS /
  PRESS START" title (reachable at ~15 s after launch with no key input).
  Press Start through the wireframe intro/demo to reach the main menu:
  `1 PLAYER / CLASSIC / 2P CO-OPERATIVE / 2P COMPETITIVE / LOAD GAME /
  NORMAL SKILL / CREDITS` (7 items; the selector wraps after CREDITS —
  there are no hidden menu rows).
* To enter a code: at the **"SPACE INVADERS / PRESS START"** title screen,
  press the sequence with ~150 ms holds, then press Start.
* Breakpoint oracle: `mgba -3 -d rom.gba`, then `b/t 0x080278E0`, `c`.
  On a match the debugger stops at `0x080278E2` and prints
  `r3 = <sequence pointer>` and `r1 = <code index 0..3>`. This is the fastest
  way to test accept/reject without watching the screen.

### Codes

| # | Sequence | Published? | Effect |
|---|---|---|---|
| 0 | B, A, Select, Select, B, A, Left, Left | Yes (SuperCheats/GameFAQs) | Cheat menu → level select; observed landing on the **PLUTO** planet intro |
| 1 | Left, A, Select, Select, Up, Up | Yes | Invincibility in Classic Mode (published label; not isolated in-game) |
| 2 | **Left, R, L, Right, Left, R, L, Right** | **No — novel** | Undocumented unlock; accepted with index 2 |
| 3 | B, A, Down, B, A, Down, B, Up, Select | Yes | Maniacal Skill Level (published label; not isolated in-game) |

R/L above are the shoulder buttons (`0x100`/`0x200`), not D-pad.

## 4. Address map

All addresses are ROM (`0x08......`) unless marked RAM. File offset =
ROM address − `0x08000000`.

| Address | Kind | Meaning |
|---|---|---|
| `0x08000000` | header | entry word `0xEA000030` → `0x080000C8` |
| `0x0805C728` | table | cheat record 0: header u16 `0x0000`, sequence at `0x0805C72A` |
| `0x0805C73C` | table | cheat record 1: header `0x0000`, sequence at `0x0805C73E` |
| `0x0805C74C` | table | cheat record 2: header `0x0000`, sequence at `0x0805C74E` (novel code) |
| `0x0805C760` | table | cheat record 3: header `0x0000`, sequence at `0x0805C762` |
| `0x0805C72A`–`0x0805C774` | data | four u16 sequences, each terminated by `0xFFFF` |
| `0x08049B88` | table | four u32 pointers to the record headers above |
| `0x08049A84` | function | registers all four codes (calls `0x080276A8` ×4 at `0x08049B56/60/68/70`) |
| `0x080276A8` | function | registrar: stores `{mask, seq_ptr, length}` into system object at `+36 + i*12` |
| `0x080276F0` | function | **validator**: 32-entry u16 ring buffer at object `+44`, write index at `+40` |
| `0x080278E0` | function | match handler: called with `(system_object, code_index)` |
| `0x02015598` | RAM | observed system object (from debugger `r6` at the match handler) |
| `0x080170C4` | function | debug-screen root renderer — **dead code** |
| `0x08017188`, `0x08017284`, `0x080173E8` | functions | Entity Options / Systems Menu / Performance Menu renderers, called only from `0x080170C4` |
| `0x083C4240` | table | debug menu string-pointer table (copied to EWRAM `0x0200DC00` at runtime) |
| `0x0805ABF8`–`0x0805B4AC` | strings | "Options", "Systems Menu", "Space Invaders Debug Screen", "Built: Jan 18 2002", "Profiling Menu", "Entity Options:", … |
| `0x0805CAA0`–`0x0805CEC7` | strings | entity sprite names (ANGLER, BURSTER, MOTHERSHIP, CL_HISCORE, MAINMENUWINDOW, …) |
| `0x0805C882` | string | `Torus` (engine identification) |

## 5. Algorithm

Key state is active-high: `mask = ~KEYINPUT(0x04000130) & 0x3FF`, so
`A=0x001, B=0x002, Select=0x004, Start=0x008, Right=0x010, Left=0x020,
Up=0x040, Down=0x080, R-shoulder=0x100, L-shoulder=0x200`.

Registration (`0x080276A8`): for each of the four pointers in the table at
`0x08049B88`, count u16 masks until the `0xFFFF` terminator, then write a
12-byte entry into the system object's listener array at `+36 + i*12`:
`{u16 mask = first halfword of record (always 0x0000), u32 *sequence =
record+2, u32 length}`.

Validation (`0x080276F0`), run continuously:

```
mask = current_pressed_mask        # [obj+108] field +0
if mask == 0: return               # no key pressed this frame
ring[ring_index] = mask            # obj+44, 32 u16 slots
ring_index = (ring_index + 1) % 32 # obj+40
for i in 0..num_registered-1:
    entry = obj+36 + i*12
    if entry.mask and not (mask & entry.mask): continue   # gate (never set here)
    ok = True
    for j in 0..entry.length-1:
        if entry.sequence[j] != ring[(ring_index-1-j) % 32]:
            ok = False; break
    if ok: handler(obj, i)          # 0x080278E0
```

The matcher is a **suffix match on the last N pressed masks** (newest first),
so a code works regardless of what was pressed before it, and extra presses
after it do not revoke it. The mask gate is present in the format but all four
records set it to `0x0000`, so no code has an additional held-key requirement.

## 6. Tables

### 6.1 Record headers (all at file offset = ROM − 0x08000000)

| Pointer | Header u16 | Sequence (u16 masks) | Terminator |
|---|---|---|---|
| `0x0805C728` | `0x0000` | `0002 0001 0004 0004 0002 0001 0020 0020` | `FFFF` @ `0x0805C73A` |
| `0x0805C73C` | `0x0000` | `0020 0001 0004 0004 0040 0040` | `FFFF` @ `0x0805C74A` |
| `0x0805C74C` | `0x0000` | `0020 0100 0200 0010 0020 0100 0200 0010` | `FFFF` @ `0x0805C75E` |
| `0x0805C760` | `0x0000` | `0002 0001 0080 0002 0001 0080 0002 0040 0004` | `FFFF` @ `0x0805C774` |

The word `0x00000258` at `0x0805C724` precedes record 0 and is not read by
the cheat registrar (it is outside every registered sequence).

### 6.2 Published-code verification

| Published source | Literal / sequence | Verified? |
|---|---|---|
| SuperCheats / GameFAQs (GBA) | B,A,Sel,Sel,B,A,L,L | Yes — table record 0, matched in emulator |
| SuperCheats / GameFAQs (GBA) | Left,A,Sel,Sel,Up,Up | Yes — record 1, matched in emulator (`r1=1`) |
| SuperCheats / GameFAQs (GBA) | B,A,Down,B,A,Down,B,Up,Sel | Yes — record 3, matched in emulator (`r1=3`) |
| GamesRadar / GameFAQs "9 lives" (Right×3,Down,Circle,Left,Down) | — | Not in table; Circle-button wording belongs to the PS1 version |
| GameFAQs/IGN/Game Boy "CLSS1281999DBM" | absent from ROM | GBC SKU; `grep -abo` and case-insensitive `clss` both zero hits |
| Game Boy level passwords `wwyx tc2n qw79vy` etc. | absent from ROM | GBC SKU, not this image |
| TCRF "To do: debug code" claim | none found | no published trigger; debug renderer is dead code (below) |

Fetched web pages were treated strictly as data; no instruction found in them
was executed.

## 6b. Enumeration

**Space definition.** This is a pure lookup system, not a checksum generator.
The accepted input space is exactly the four u16 sequences referenced by the
pointers at `0x08049B88`–`0x08049B94` (sequences at `0x0805C72A`–`0x0805C774`). Each sequence is 6–9 presses drawn from a 10-symbol
alphabet (A, B, Select, Start, D-pad×4, shoulders×2) with a 16-bit-per-press
encoding and a `0xFFFF` terminator. There is no encoder, no checksum, no
reserved payload bit and no PRNG: the total number of accepted codes is
**exactly four**, enumerated exhaustively above. An "invalid" code is any
sequence not equal to one of these four — there is no larger latent space.

**Complete enumeration (4/4):**

| Index | Pointer | Sequence | In-game proof |
|---|---|---|---|
| 0 | `0x0805C72A` | B,A,Sel,Sel,B,A,L,L | breakpoint hit, `r3=0x0805C72A`, `r1=0`; Start → PLUTO planet intro observed |
| 1 | `0x0805C73E` | Left,A,Sel,Sel,Up,Up | breakpoint hit, `r3=0x0805C73E`, `r1=1` |
| 2 | `0x0805C74E` | Left,R,L,Right,Left,R,L,Right | **breakpoint hit, `r3=0x0805C74E`, `r1=2`** — novel |
| 3 | `0x0805C762` | B,A,Down,B,A,Down,B,Up,Sel | breakpoint hit, `r3=0x0805C762`, `r1=3` |

**Novel code (not in GameFAQs, VGChartz, TCRF, SuperCheats or any wiki):**

```
Left, R-shoulder, L-shoulder, Right, Left, R-shoulder, L-shoulder, Right
```

This is record 2 of the ROM's own table; it is exercised by no published
list. Entered at the title screen of mGBA, it stopped the debugger at
`0x080278E2` with `r3 = 0x0805C74E` and `r1 = 0x00000002` (the index proving
the third entry fired), while `r7 = 1` (match flag). This is ground-truth
acceptance by the game's own validator, not a debugger call substituted for
the screen.

**Bounds proven by rejection.** With a live breakpoint on the match handler,
the near-miss `Left, R, L, Right, Left, R, L, Up` (only the final press changed
from Right to Up) produced **no breakpoint hit** at the title screen (title
state confirmed by screenshot), even though the first seven presses are an
exact prefix of the novel code. Changing any single press therefore fails the
suffix comparison. `Left, R, L, Right, Left, R, L, Left` was likewise not
accepted. This closes the space: the format has no tolerance, no wildcard and
no alternate spelling.

**Dead debug screen — bounded negative.** The debug renderer at `0x080170C4`
and its three submenu functions were checked with four independent xref
methods: 32-bit pointer scan (with and without the Thumb bit), Thumb `BL`/`BLX`
scan, Thumb `LDR [PC]` literal-*value* scan, and ARM `B`/`BL` scan. Results:
`0, 0, 0, 0` for `0x080170C4`; the only xref anywhere in that cluster is the
title string `0x0805AC38` referenced from the renderer's own literal pool at
`0x08017104`. A live breakpoint at `0x080170C4` was then held through a full
boot with L+R+Start+Select held, the title screen, the seven-item main menu,
four button-combination tests, 1-player gameplay and the pause screen: **zero
hits**. This is a §16.3 "dead code" finding with both static and dynamic
bounds, not an untested screen.

## 7. Validation evidence

* **Observed** (emulator screenshots / debugger reads):
  * Activision/Taito/Torus splashes, title screen, 7-item main menu,
    wireframe intro, attract "DEMO MODE" gameplay, planet-intro screen.
  * Code 0 → `PLUTO` level intro after Start.
  * Breakpoint register dumps at `0x080278E2` for all four codes, with
    `r3` equal to the expected sequence pointer and `r1` equal to 0/1/2/3.
  * Near-miss sequences produced no breakpoint hit at a confirmed title screen.
  * Breakpoint at `0x080170C4` never hit.
* **Derived** (disassembly): sequence encoding, ring-buffer matcher, terminator,
  mask gate, 12-byte listener records, pointer table, dead-code xref counts.
* **Inferred** (not isolated in-game): the precise gameplay effect of codes
  1 and 2; published labels ("Invincibility In Classic Mode", "Maniacal Skill
  Level") are taken from the fetched page and are consistent with the code
  index dispatch but were not played through. The effect of code 2 (novel) is
  likewise unlabelled; a savestate diff isolated EWRAM churn near the cheat
  manager object (`0x0201583D`, `0x0201590D`) but animation noise prevented a
  clean one-byte flag identification.
* **Negative**: published GBC passwords absent from this SKU; debug screen
  unreachable.

## 8. Unknowns

* Meaning of the u32 `0x00000258` at `0x0805C724` (not consumed by the cheat
  registrar).
* Exact effect/flag of novel code index 2; no visible change at the title or
  an added main-menu row, so the effect is likely a persistent gameplay flag.
* The debug screen *would* render if `0x080170C4` were called directly, but no
  retail input path reaches it; its menu entries are therefore documented as
  present-but-unreachable, not as working cheats.
* No high-score-initials edit was exercised (normal UI feature, not a cheat
  surface); the on-screen text is font/tile-indexed, so ASCII `strings`
  cannot enumerate it.

## 9. Tooling

* `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings -t x`, `grep -abo`.
* Python scripts in `/tmp/opencode/spaceinvaders/`:
  `scan_headers.py` (logo scan), `ptrscan.py` (4-byte pointers),
  `blscan.py` (Thumb BL), `ldrscan.py`/`xrefscan.py` (literal-value and xref
  counts), `keysearch.py` (key-mask sequence search — this found the table),
  `mgdbg.py`/`verifycode.py`/`verify3.py`/`verify24.py`/`rejecttest.py`/
  `dbgdynamic.py` (mGBA `-d` pty driver + breakpoint oracle),
  `ssdecode.py`/`ramdiff.py`/`controldiff.py` (savestate `gbAs` zlib diff).
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`.
* `Xvfb :315`, `openbox`, `xdotool` (XTEST), `scrot`.
* Legal note: no ROM bytes, graphics, music or game text are redistributed here;
  only hashes, addresses, algorithms and the author's own button sequences.
