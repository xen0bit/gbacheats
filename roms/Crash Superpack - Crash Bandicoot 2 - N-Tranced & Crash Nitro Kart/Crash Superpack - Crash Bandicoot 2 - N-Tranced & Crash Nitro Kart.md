# Crash Superpack – Crash Bandicoot 2: N-Tranced & Crash Nitro Kart (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Crash Superpack - Crash Bandicoot 2 - N-Tranced & Crash Nitro Kart.gba` |
| Size | 16,777,216 bytes (16 MiB / 128 Mbit) |
| MD5 | `3638075a07ad63a813dea97e6ad16d2c` |
| SHA-1 | `23934042b3f7ac414def68246c281e20f735a1d7` |
| SHA-256 | `6c8d6d6b638c48bcc712f9feaf7abf3ec7e913d1c913c40d44577e2724b497ee` |

Two complete GBA images, back to back. The 156-byte Nintendo logo occurs exactly
twice in the file (file `0x4` and `0x800004`), so there is no third image and no
hidden header between them.

| Header | Image base | Title | Code | Maker | Ver | Complement | Hdr checksum | Entry word |
|---|---|---|---|---|---|---|---|---|
| `0x000000` | `0x08000000` | `CRASH S PACK` | `B8AE` | `7D` | 0 | `0xB3` | `0x0000` | `0xEA3FD3FE` → `0x080FF500` |
| `0x800000` | `0x08800000` | `NITRO KART` | `BCNE` | `7D` | 0 | `0xE0` | `0x0000` | `0xEA00002E` → `0x088000C0` |

Both header checksums are `0x0000` (rebuilt-header artifact, guide §16.1). There
is **no cracktro and no trainer**: the first image's entry branch is repointed
into the compilation's own launcher (`0x08FF5000`), the stock CB2 `crt0` at
`0x080000C0` is untouched, and the second image's entry is the stock
`b 0x088000C0`.

### Patch set (image 1 vs the standalone CB2 dump in this collection)

`Crash Bandicoot 2: N-Tranced.gba` (md5 `617b2b2590e2925228dbdb162b05d6f6`)
differs from bytes `0x000000–0x7FFFFF` of this cartridge in **22 bytes only**:

| Offset | Stock | Pack | Meaning |
|---|---|---|---|
| `0x000000–0x000002` | `2E 00 00 EA` | `FE D3 3F EA` | entry → `b 0x080FF500` (launcher) |
| `0x0000A5–0x0000AB` | `32 00 00 00 00 00 00` | `" S PACK"` | title becomes `CRASH S PACK` |
| `0x0000AC–0x0000AD` | `"AC"` | `"B8"` | game code becomes `B8AE` |
| `0x0000BD` | `0x32` | `0xB3` | header complement check |
| `0x0049B08–0x0049B0A` | `AC 00 00` | `FC FF FF` | literal `0x080000AC` → `0x08FFFFFC` |
| `0x0049D14–0x0049D16` | `AC 00 00` | `FC FF FF` | same literal repointed |
| `0x005AF64–0x005AF65` | `08 D1` (`bne`) | `0A E0` (`b`) | unconditional branch in the language/resource selector |
| `0x0FFFFFC–0x0FFFFFE` | — | `"AC8E"` | copy of the stock game code, moved out of the edited header |

The two literal patches exist because the pack overwrote the header bytes that
stock code used to read the game-code string `"AC8E"`; the string is preserved
at the end of image 1 and the two readers are repointed to it. Nothing else in
the CB2 half was modified — every menu table, text table, save routine and
validator address below is therefore byte-identical to the standalone image.

### Image 2

The second half is a **distinct Nitro Kart build**, not a sliced copy of the
standalone `Crash Nitro Kart.gba` (md5 `9e6ff628db81caa74dca356eaadadac9`):
only 2 of 2048 4 KiB pages match, and its string bank sits `0x964` bytes earlier
(e.g. `PRESS START` at `0x0833AF8` here vs `0x08343A2` in the standalone dump).
Title/code/revision are the same (`NITRO KART` / `BCNE` / rev 0), so it is the
same product rebuilt for the compilation (relinked; the launcher occupies the
last `0xB000` bytes of this half).

## 2. Executive summary

This cartridge is **not** a plain concatenation with a stock boot. It contains:

1. **A compilation launcher** at `0x08FF5000` (inside the tail of the Nitro Kart
   image, which is `0xFF` padding in the standalone dump). It plays a short
   intro (observed ≈8–9 s after power-on), then a two-page picker. **Left and Right both toggle
   the page** (the handler is a plain XOR 1, not directional), and **A or Start
   launches**. The launch target is proven in code: `sel == 0` → `0x080000C0`
   (CB2), `sel != 0` → `0x088000C0` (Nitro Kart). No other button has a handler.

2. **The only button-code system in the cartridge** is Nitro Kart's boot-time
   "Crash Party USA" gate. In code it is a single `KEYINPUT & 0x300` test
   (`0x0881B76C–0x0881B778`). Because it uses `BICS` (mask AND NOT keys), the
   **trigger is L *or* R**, not L *and* R: any key state with at least one of the
   two pressed passes. When it passes, the game LZ77-decompresses an embedded
   **multiboot GBA ROM titled `CRASH-PARTY`** (245,048 bytes) into EWRAM
   `0x02000000`, sets the BIOS multiboot flag and soft-resets into it.

3. **Nitro Kart's in-game CHEATS screen** is an unlock list, not a code entry:
   `NONE / ARTILLERY / TURBO / R/C KART / LUNAR`, plus a `GCN LINK` entry.
   The four named cheats are the complete set in the ROM; they are granted by
   winning gem cups or by the GameCube link, not by input.

4. **Crash Bandicoot 2 has no code surface at all** (confirmed on this image,
   not assumed): 4 `KEYINPUT` literal sites, zero referenced button-sequence
   tables, no password/cheat strings, no debug strings. Its only hidden state is
   the link-transfer unlock byte: five multiplayer characters as bits in the
   save record, written only by the link receive routine.

**Cart-specific correction to the published GBA cheat list:** "hold L+R when
turning on the game" does **not** work as written on this cartridge — the
launcher owns the boot and ignores L/R (they are not even in its key array;
verified 0x030008B0). The working procedure is: select the Nitro Kart page, then
hold **L, R (or both)** while pressing A/Start. That confirm-while-holding
procedure is not in any published list. The gate's OR semantics also settle a
contradiction between published lists: most say "press L and R together", one
3rd party cheat indexes line says "hold L or R" — the ROM proves the OR reading, and `L` alone
or `R` alone is accepted.

## 3. How to reproduce

### Harness

```bash
Xvfb :268 -screen 0 1024x768x24 &
DISPLAY=:268 openbox &
export DISPLAY=:268 SDL_AUDIODRIVER=dummy
mgba -3 game.gba &            # mGBA 0.10.5 SDL
```

Keymap used (mGBA SDL defaults): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
Select=`BackSpace`, D-pad=arrows. Hold 70–120 ms; 300–500 ms for boot-time
holds. No screenshots were used anywhere in this analysis — every observation is
a RAM read from an mGBA savestate or from the build-in debugger.

### Reading RAM without a debugger

`Shift+F1` writes `game.ss1`, a PNG whose `gbAs` chunk is a zlib stream; after
`zlib.decompress` it is **397,312 bytes (`0x61000`)** laid out as:

| Range | Block |
|---|---|
| `0x00000–0x00FFF` | state header (CPU/IO/etc.) |
| `0x01000–0x18FFF` | VRAM (`0x06000000`) |
| `0x19000–0x20FFF` | IWRAM (`0x03000000`) |
| `0x21000–0x60FFF` | EWRAM (`0x02000000`) |

Verified by finding the launcher's IRQ vector: IWRAM `+0x7FFC` (`0x03007FFC`)
holds `0x03000040`, the handler copied from ROM `0x08FF503C`; IWRAM `+0x0000`
holds the 14-entry table the launcher writes at `0x03000000`.

### Menu path (observed)

1. Power on → launcher intro. Any key skips it; A/Start at this point launches
   page 0.
2. Picker: Left **or** Right toggles the page (`0x0300085C` 0↔1); A or Start
   launches.
3. Page 0 → Crash Bandicoot 2 `crt0` at `0x080000C0`; page 1 → Nitro Kart
   `crt0` at `0x088000C0`.
4. Nitro Kart title `PRESS START` → Start is accepted and the front-end state
   changes (full menu inventory in §6).
5. Crash Party USA: on the Nitro Kart page, hold `L` (or `R`, or both) and press
   A/Start; keep the hold ~1 s.

### Codes / inputs tested

| Input at the picker | Result |
|---|---|
| A / Start | launch selected page |
| Left / Right | flip page (both are XOR-1 handlers) |
| B, Select, Up, Down, L, R | no effect (skip intro when still in intro) |

| Input at Nitro Kart launch | Result |
|---|---|
| (none) + A | normal Nitro Kart boot |
| Up+Down+Select + A | normal Nitro Kart boot (rejection bound) |
| L + A | **Crash Party USA** |
| R + A | **Crash Party USA** |
| L+R + A | **Crash Party USA** (published combination) |
| L+R+Select + A | **Crash Party USA** (unpublished superset) |
| L+R held from power-on, no confirm | launcher only (published procedure fails) |

## 4. Address map

| ROM/RAM address | Meaning |
|---|---|
| `0x08000000` | image-1 header; `b 0x08FF5000` |
| `0x080000C0` | stock CB2 ARM crt0 (unchanged) |
| `0x08003000` | CB2 `partner_type = byte[save+0x1F9] >> 4` |
| `0x080030EC` | CB2 `test_bit(save,bit)` → `byte[save+0x1FA] & bit` |
| `0x08003124` | CB2 `set_bit(save,bit)` → `byte[save+0x1FA] \|= bit` + checksum `0x08002FDC` |
| `0x08003CC0`,`0x08003CE4`,`0x08003DB6`,`0x08003DC2`,`0x08003DCE`,`0x08003DDA` | all six `set_bit` call sites (link receive) |
| `0x0800448C–0x0800473C` | CB2 link results screen |
| `0x0800452E/45BA/463E/46C2` | `test_bit 0x02/0x08/0x04/0x10` branches |
| `0x081D5C04` | CB2 191-entry text-id table |
| `0x081D4430–0x081D4478` | `unlocked neo cortex / dingodile / tiny / n. gin / megamix` (ids 89–93) |
| `0x087FBD58` | developer block referencing `crash 1 <-> crash 2`, `crash 2 <-> crash 3` |
| `0x087FBD18` | developer config word (0 in this dump; see §8) |
| `0x08C5BA60` | Nitro Kart: LZ77 blob of the Crash Party multiboot image |
| `0x0881B734` | Nitro Kart boot routine that contains the L/R gate |
| `0x0881B768–0x0881B778` | `cmp r5,#0x1F` / `KEYINPUT & 0x300` / branch |
| `0x0882B5E0` | BIOS-style decompression dispatcher (type 1 = LZ77) |
| `0x08830994` | soft-reset helper: IME=0, `[0x03007FFA]=1`, `RegisterRamReset(0xFE)`, `SoftReset` |
| `0x08FF5000` | launcher ARM reset stub |
| `0x08FF503C` | launcher IRQ handler (copied to `0x03000040`) |
| `0x08FF529C` | launcher main |
| `0x08FF54BC` | picker handler: `sel ^= 1`, leave-flag=1 |
| `0x08FF54D4` | picker handler: confirm/launch |
| `0x08FF54EC` | launcher: `bx 0x080000C0` (sel 0) / `bx 0x088000C0` (sel 1) |
| `0x08FF5654` | launcher key poll (`ldr 0x04000130` at `0x08FF5656`) |
| `0x08FFC9B8` | picker page-0 descriptor (size `0x3700`) |
| `0x08FFF528` | picker page-1 descriptor (size `0x5100`) |
| `0x03000000` | 14-entry launcher IRQ table (all entries = `0x08FF5565`, i.e. `bx lr`) |
| `0x03000840` | launcher page struct `{desc, 0x02000000, size, ...}` |
| `0x03000858` | launcher leave-flag |
| `0x0300085C` | **selected page** |
| `0x03000860 + 4*i` | **per-key handler table** (`i` = 0..9, null = no action) |
| `0x030008B0 + 4*i` | launcher key state (`9` idle, `2` held) |
| `0x03007FFC` | IRQ vector (`0x03000040` while the launcher runs) |
| `0x02000000` | Crash Party multiboot image destination |

## 5. Algorithm

### 5.1 Launcher

```
reset:  ARM stub at 0x08FF5000
        copy 0x08FF503C (0x200 words) -> 0x03000040; [0x03007FFC] = 0x03000040
        fill 0x03000000..0x03000037 with 0x08FF5565   ; 14 IRQ slots, all no-op
        WAITCNT = 0x4014
        intro pages (descriptors 0x08FF93E4, 0x08FF9F20, ...) for ~8–9 s
        a key press skips the intro
menu:   page struct = {desc, dst=0x02000000, size, ...}
        sel = 0  -> desc 0x08FFC9B8, size 0x3700
        sel = 1  -> desc 0x08FFF528, size 0x5100
        every frame: poll 10 buttons into 0x030008B0 + 4*i
                     dispatch through 0x03000860 + 4*i
handlers: 0x08FF54BC (Left, Right)  : sel ^= 1 ; leave = 1
          0x08FF54D4 (A, Start)     : launch sequence
launch: IME=0; IE=0; DISPSTAT=0
        if sel == 0: BX 0x080000C0
        else:        BX 0x088000C0
```

Note the intro and menu are separate states: during the intro *any* key advances
to the menu, and A/Start still confirms the current page (observed page 0).

### 5.2 Nitro Kart boot gate (Crash Party USA)

```
0x0881B734 (called from crt0 at 0x08800162):
    r5 = f(0x08821594)
    if r5 == 0x1F: goto party
    keys = KEYINPUT                     ; 0x0881B76C
    if (0x300 & ~keys) != 0: goto party ; L or R pressed
    return                              ; no L/R: continue normal boot
party:
    decompress(0x08C5BA60 -> 0x02000000)  ; type 1 LZ77, 245,048 bytes
    soft_reset(0xFE)                    ; [0x03007FFA]=1 then SWI 0
```

`0x08830994` is `RegisterRamReset(0xFE)` followed by `SoftReset` with the BIOS
multiboot word set, so the BIOS boots the EWRAM image at `0x02000000` while
EWRAM (bit 0 of the reset mask) is preserved.

### 5.3 CB2 unlock bits

```
partner = byte[save+0x1F9] >> 4
if partner == 1: set_bit(save,0x01)                 ; 0x08003CC0
if partner == 3: set_bit(save,0xFF)                 ; 0x08003CE4
; link-progress pass over up to four files (0x08003D0C):
level 1 -> set_bit 0x02
level 2 -> set_bit 0x08
level 3 -> set_bit 0x04
level 4 -> set_bit 0x10
```

`set_bit` ORs into `save+0x1FA` and recomputes the 508-byte save checksum
(`0x08002FDC`). No input handler, menu or validator calls it.

## 6. Tables

### 6.1 Launcher enumeration

| Page | Descriptor | Size | Boot target |
|---|---|---|---|
| 0 | `0x08FFC9B8` | `0x3700` | `0x080000C0` (Crash Bandicoot 2) |
| 1 | `0x08FFF528` | `0x5100` | `0x088000C0` (Nitro Kart) |

Key index → mask → handler (from `0x08FF5654` and `0x03000860`):

| i | Button | KEYINPUT mask | Handler |
|---|---|---|---|
| 0 | A | `0x001` | `0x08FF54D4` (launch) |
| 1 | B | `0x002` | 0 |
| 2 | Select | `0x004` | 0 |
| 3 | Start | `0x008` | `0x08FF54D4` (launch) |
| 4 | Up | `0x040` | 0 |
| 5 | Down | `0x080` | 0 |
| 6 | Right | `0x010` | `0x08FF54BC` (flip) |
| 7 | Left | `0x020` | `0x08FF54BC` (flip) |
| 8 | R | `0x100` | 0 |
| 9 | L | `0x200` | 0 |

### 6.2 Nitro Kart front-end inventory (from the ROM's own string block)

Main/title: `PRESS START`, `SINGLE PLAYER`, `LINK PLAY`, `OPTIONS`,
`HIGH SCORES`, `GARAGE`, `HINTS`, `CHANGE RACER`, `MAIN MENU`.
Pause: `PAUSE`, `RESUME`, `RESTART`, `RETRY`, `WIN RACE`, `QUIT`, `MAIN MENU`,
`GO TO SLEEP?`, `SLEEP`, `CANCEL` (wake text: `PRESS SELECT AND THE L & R
BUTTONS TO WAKE`).
Options (6): `SOUND`, `CONTROLS`, `CHEATS`, `GCN LINK`, `LANGUAGE`, `CREDITS`.
Cheats (5): `NONE`, `ARTILLERY`, `TURBO`, `R/C KART`, `LUNAR`
(strings at `0x0834CD0`, `0x0834CF4`, `0x0834D1C`, `0x0834D40`, `0x0834D68`).
Races: `CHOOSE MODE` (`ADVENTURE`, `TIME TRIAL`, `ARCADE`), `SELECT RACE`
(`CNK CHALLENGE`, `RELIC RACE`), `CHOOSE RACE TYPE` (`SINGLE RACE`, `CUP RACE`,
`QUICK RACE`), `CHOOSE LEVEL` (12 tracks + `VELO'S TRACK`), `SELECT CUP`
(`WUMPA`, `CRYSTAL`, `CRASH`, `NITRO`), `SELECT DIFFICULTY` (`EASY`, `MEDIUM`,
`HARD`), `CHOOSE TEAM` (`BANDICOOT`, `EVIL`).
Roster (`SELECT CHARACTER`): `CRASH`, `COCO`, `CRUNCH`, `NEO CORTEX`, `N.GIN`,
`TINY`, `DINGODILE`, `POLAR`, `N.OXIDE`, `N.TRANCE`, `N.TROPY`, `KRUNK`, `NASH`,
`NORM`, `BIG NORM`, `GEARY`, `VELO`, `FAKE CRASH`, `SPYRO`, `CORTEX`.
No password/code/enter-code screen exists in the Nitro Kart string block; the
only "code" strings are `WEB CODE: %s` / `ENTER CODE AT WWW.VVISIONS.COM`, i.e.
a code *generated for the website*, not typed in.

### 6.3 Crash Party multiboot image (decompressed)

| Field | Value |
|---|---|
| Stored at | ROM `0x08C5BA60`, GBA LZ77 header `10 38 BD 03` |
| Decoded size | `0x3BD38` (245,048 bytes) |
| Loaded to | EWRAM `0x02000000` |
| Entry | `0xEA00002E` (`b 0xC0`) |
| Title (`+0xA0`) | `CRASH-PARTY ` |
| Game code / maker | `0000` / `7D` |
| Fixed byte / version | `0x96` / `0` |
| Complement / checksum | `0xC8` / `0x0000` |
| Copyright text (`+0x7D3`) | `Crash Party USA` / `Interactive Game © 2003` / `Universal Interactive, Inc.` |

The compressed blob is byte-identical to the copy in the standalone Nitro Kart
dump at file `0x45BB18`, i.e. the mini-game is shared content; the title string
`CRASH-PARTY` exists only after decompression, so a plain `strings` scan of the
ROM cannot see it.

### 6.4 CB2 unlock bit map (this image)

| Bit | Set by | Drawn by results screen |
|---|---|---|
| `0x01` | partner type 1 (`0x08003CC0`) | no (id 89 is drawn unconditionally) |
| `0x02` | level 1 (`0x08003DDA`) | yes, id 90 `unlocked dingodile` |
| `0x04` | level 3 (`0x08003DC2`) | yes, id 91 `unlocked tiny` |
| `0x08` | level 2 (`0x08003DCE`) | yes, id 92 `unlocked n. gin` |
| `0x10` | level 4 (`0x08003DB6`) | yes, id 93 `unlocked megamix` |
| `0x20`,`0x40`,`0x80` | partner type 3 writes `0xFF` | no branch — aliases |

Text-id table check: `u32[0x081D5C04 + 4*id]` → id 89 = `0x081D4430`
`unlocked neo cortex`, 90 = `unlocked dingodile`, 91 = `unlocked tiny`,
92 = `unlocked n. gin`, 93 = `unlocked megamix`.

## 6b. Enumeration

### 6b.1 Launcher page space

* Exactly **2** pages (0 and 1); Left and Right are both XOR-1 toggles, so the
  reachable states are `{0,1}` and the transition graph is a 2-cycle.
* Input space = 10 polled buttons (`0x030008B0`, stride 4, values 9=idle,
  2=held; observed Up → index 4 = 2 while held, 9 when released).
* Handler table at `0x03000860`: `[launch, 0, 0, launch, 0, 0, flip, flip, 0, 0]`
  — i.e. **4 action branches, 6 null branches**, matching the dynamic matrix.
* Launch branches: 2 (`sel==0` → CB2, `sel==1` → Nitro Kart).
* Combined input space is therefore 1024 key states but only the four handlers
  above can act; no launcher state is hidden behind L/R/B/Select/Up/Down.

### 6b.2 Nitro Kart boot gate space

* Predicate: `(KEYINPUT & 0x300) != 0` (plus `r5 == 0x1F` on a second path).
* Alphabet: 10-bit key state; bits 10–15 read as 1 on GBA. There are 1024
  states; 256 have neither L nor R pressed and do not trigger, so **768 of 1024
  states trigger** — every state with L and/or R held; all other buttons are
  don't-care.
* Positive proofs (savestate RAM): `L`, `R`, `L+R`, `L+R+Select` all produce the
  EWRAM image at `0x02000000` (`"CRASH-PARTY"` at EWRAM `+0xA0`) and the same
  IWRAM signature (~356 `0x0200xxxx` code pointers vs 5 ROM pointers).
* Execution proof: the decompressed image is **98.11 %** byte-identical to a
  fresh LZ77 decode; the differing 1.89 % is concentrated in the top four 4 KiB
  blocks (`0x38000–0x3BD38`), i.e. runtime variables/stack inside the image,
  and IWRAM is dominated by return addresses into `0x0200xxxx`.
* Bounds by rejection: no L/R (`Up+Down+Select`) → normal Nitro Kart boot, no
  `CRASH-PARTY` header, 36 EWRAM / 98 ROM pointers; holding `L+R` from power-on
  without confirming leaves the launcher running (sel 0, page-0 descriptor).
* Published-list reconciliation: the dominant wording ("press L and R
  together") is a proper subset; one published line already says "hold L or R",
  which the ROM confirms. Genuinely absent from every published list are the
  **cartridge-specific confirm-while-holding procedure** and the **L+R+Select**
  superset — both confirmed to start Crash Party USA.

### 6b.3 CB2 unlock-byte space

* 8-bit field at save record `+0x1FA`; meaningful bits `0x1F`.
* Setter domain: `{0x01, 0xFF, 0x02, 0x04, 0x08, 0x10}` from six call sites, all
  inside the link receive/result code `0x08003C80–0x08003DE0`. No menu, input
  handler, or validator calls `set_bit` (BL scan: exactly 6 callers).
* Display domain: id 89 unconditional + bits `0x02,0x04,0x08,0x10` conditional;
  `0x20/0x40/0x80` are set only by the `0xFF` write and have no branch, so they
  are aliases, not hidden characters.

### 6b.4 Published-list verification

* Nitro Kart GBA "Crash Party USA – Hold L+R when turning on the game"
  (3rd party cheat indexes / Nintendo Wiki / 3rd party cheat indexes): the gate exists in the ROM at
  `0x0881B76C`, but the *procedure* fails in this cartridge because the launcher
  runs first. The working equivalent is documented in §3, and the OR semantics
  make the published L+R a proper subset of the accepted inputs.
* Nitro Kart GBA "Unlock Cheats GBA: Artillery (Blue Gem Cup), Lunar (Purple),
  R/C Kart (Green), Turbo (Red)" and "GCN link unlocks all four + N. Oxide,
  N. Tropy, Spyro": the ROM contains exactly these four cheat names plus the
  `GCN LINK` entry and the congratulation strings (`YOU HAVE UNLOCKED TONS OF
  GOODIES!`, `ARTILLERY CHEAT`, `TURBO CHEAT`, `R/C KART CHEAT`, `LUNAR CHEAT`).
  No code entry screen exists; the list is save-gated, not input-gated.
* CB2 N-Tranced sibling codes: no password/cheat literals exist in image 1
  (ASCII scan of the whole half); `KEYINPUT` literal sites = 4
  (`0x08000900`, `0x08046310`, `0x08047EE0`, `0x08047F5C`), all in the UI/key
  latch; zero of the 29 key-mask runs found by the sequence scan are referenced
  by any literal pointer, so they are data, not a cheat table.

### 6b.5 Search spaces checked (negative-result bounds)

| Space | Extent | Result |
|---|---|---|
| Strings `password/cheat/code/debug/secret/unlock/level` | whole 16 MiB | only CNK `CHEATS`/`* CHEAT`/`WEB CODE` + CB2 `unlocked …`; no password screen |
| Button-sequence tables (runs ≥6 of valid masks, ≥3 distinct) | whole ROM | 29 candidates, 0 referenced by code → data |
| `KEYINPUT` literal `0x04000130` | whole ROM | 10 sites: 4 CB2 UI, 4 CNK code, 1 launcher, 2 data |
| 32-symbol alphabets (password keypads) | whole ROM | none in a UI context (uppercase runs are tile data) |
| Debug keyword strings | whole ROM | 0 `debug`; CNK `test*` strings are GAX music track names (`"UiTheme_test1"`, `"Earth_test1"`, …) |
| Embedded GBA headers | whole file | 2 (the two images); Crash Party header only after LZ77 decode |

## 7. Validation evidence

**Observed (emulator RAM/state)**
* Launcher runs from `0x08FF5000` and its state lives at `0x03000840/58/5C/B0`;
  sel toggles 0→1 on Left and 1→0 on Right; A/Start boots CB2 on page 0 and
  Nitro Kart on page 1 (CB2 state shows `0x0804xxxx/0x084Fxxxx` execution;
  Nitro Kart shows `0x0880xxxx`).
* Key array value transitions `9 → 2` for a held Up while the launcher is up.
* `CRASH-PARTY` image built in EWRAM for L, R, L+R and L+R+Select; absent for
  the negative controls.
* Image/EWRAM match 98.11 % with runtime writes in its upper blocks; IWRAM
  contains ~356 `0x0200xxxx` pointers in party mode vs 36–47 in normal boot.
* Published "hold L+R from power-on" leaves the launcher at page 0.

**Derived (instruction sequence)**
* Launcher launch targets `0x080000C0` / `0x088000C0`; handler table contents;
  XOR-1 flip handler; the `KEYINPUT & 0x300` gate and `BICS` OR semantics.
* Decompression type 1 (LZ77) dispatcher at `0x0882B5E0`; reset helper
  `0x08830994`.
* CB2 bit map, setter call sites, results-screen branches and text ids; the
  22-byte integration patch list.
* Nitro Kart options/cheats inventory and roster from the ROM's string block.

**Inferred**
* CB2 link "level 1–4" progression semantics behind `0x08003D0C` (the helper
  checks at `0x08003408/14/20/28` were not traced to their save fields).
* Nitro Kart `r5 == 0x1F` second condition on the party gate (link state).
* The four `CHEATS` entries are independent on/off toggles rather than a
  one-of-five selector (list has a `NONE` entry; published text describes them
  as toggles).

## 8. Unknowns

* The exact content of the two intro descriptors `0x08FF93E4` / `0x08FF9F20`
  (their data is staged through `0x02000000`; the bytes at the descriptor
  addresses are zero in ROM, so the descriptor is an indirect page key, not a
  raw asset pointer).
* The purpose of the `0x005AF64` branch patch: it forces one of the two
  resource banks (`0x087F52C0` instead of the `r0==4` path to `0x087F52B4`);
  whether that is language, region or font selection was not isolated.
* The developer block at `0x087FBD00` (including `crash 1 <-> crash 2`,
  `crash 2 <-> crash 3` and a `0xFFFFFFFF/0x0800Exxx` callback table) has no
  literal pointer anywhere in the 16 MiB and was not found in RAM in the
  observed title state; it is treated as dead developer data, not a menu.
* Save type (EEPROM/Flash/SRAM) was not exercised; no save was written, so the
  on-cart persistence of the unlock byte was not re-read after a power cycle.

## 9. Tooling

* mGBA 0.10.5 SDL (`/usr/local/bin/mgba`), Xvfb `:268`, openbox, xdotool.
* `arm-none-eabi-objdump` and Capstone (Thumb/ARM) for all disassembly.
* Helper scripts kept in `/tmp/crashsuperpack/`:
  `ss.py` (PNG `gbAs` → raw state), `dyn.py` (launch/focus/tap/savestate +
  RAM summary), `lz77.py` (GBA LZ77 decoder used to reproduce the Crash Party
  image), `dis.py` (literal-resolving disassembler).
* mGBA `-d` command-line debugger used for `x/4` memory reads and `status`
  (RAM addresses above are live addresses, not savestate offsets).

## 10. Legal note

No ROM, extracted graphics, audio or text is redistributed here. The embedded
mini-game is described by its header fields and by an independently written
LZ77 decoder; the payload itself is not included.
