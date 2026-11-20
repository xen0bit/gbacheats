# The Santa Clause 3: The Escape Clause (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `The Santa Clause 3: The Escape Clause.gba` |
| Size | 8,388,608 bytes (8 MiB) |
| Header title | `SANTACLAUSE3` |
| Game code | `B33E` |
| Maker | `4Q` |
| Version | `0x00` |
| Fixed byte `0xB2` | `0x96` |
| Header checksum | `0x7800`; complement byte `0x00` (rebuilt-header artifact) |
| Entry branch | `0xEA00002E` → `0x080000C0` (stock crt0) |
| Publisher splash | Buena Vista Games, © 2006 Disney (observed) |
| MD5 | `b3a719f647a84f5496c0ad97d5de6370` |
| SHA-1 | `2163907f0a197f4164c9b9041fb1175d3c608750` |
| SHA-256 | `8f35bce22bab03c73e7bcdaaa2358a4cdfacf6c169bb69c0c7bd375891771b2d` |

A copy of this exact image was analysed in `/tmp/opencode/santa3/game.gba` (byte-identical). No single-game
published cheat list could be retrieved: web searches for this exact SKU returned no relevant results and
GameFAQs returned HTTP 403. Recon therefore rested on the ROM itself.

## 2. Executive summary

**No developer-intended password, cheat-code entry screen or button-code entry point is reachable in the
retail build.** The game ships with a substantial *dormant* debug subsystem: a Debug menu definition
("Level Select", "Slow Motion", "Replay", "Toggle Debug Keys", plus unreferenced profiling labels) and an
11-press button-code validator with a concrete mask table. Both were located and fully decoded, but the
validator is **never invoked on any reachable screen** — proved by patching a Thumb `bkpt` into it and
walking every screen in mGBA (zero hits). No 32-bit pointer to its owning vtable exists anywhere in ROM or
in live EWRAM/IWRAM. This is a **dead-code negative** (guide §16.3), not "not tested".

The only alphabetic input surface, the `Initial Entry:` screen with alphabet
`ABCDEFGHIJKLMNOPQRSTUVWXYZ_!?$&`, is a kid-profile **name** field (it is followed immediately by `OK`
and `Difficulty Select` in the text bank); no password validator consumes it. It was not reached in the
screen walk because the implemented slot flow goes straight from `New Game` to chapter select, so this
particular claim is **inferred**, not observed.

## 3. How to reproduce

```bash
export DISPLAY=:317 SDL_AUDIODRIVER=dummy
Xvfb :317 -screen 0 1024x768x24 & openbox &
mgba -3 game.gba                      # add -g for the RSP stub (port 2345)
# mGBA SDL keymap: A=x B=z L=a R=s Start=Return Select=BackSpace D-pad=arrows
# Shift+F1..F9 save state, F1..F9 load
```

Screen path (all observed): health & safety → Nintendo license → title ("Press Start") → main menu
(`Play Game` / `Credits`) → `Select Slot` (3 slots, `New Game`, `Erase`, `x0/6` collectible counters) →
`Select Chapter` (6 snow-globes, only chapter 1 lit) → `Select Level` (Northern Expedition / Candy
Caverns / Canadian Bacon / Christmas Town, `00/40`) → story cutscenes → level 1 gameplay →
`Game Paused` (`Resume` / `Quit` / `Sleep`) → `Are You Sure?` (`Quit` / `Back`) → `Sleep` screen
("To exit Sleep press Select + L + R"). The `Credits` screen shows the S3 logo and rolling credits.

Validator reachability test (the decisive experiment):

1. Start `mgba -3 -g game.gba`, connect a GDB RSP client to `127.0.0.1:2345`.
2. Write a Thumb breakpoint over the validator's first halfword:
   `M800b47c,2:00be` (original is `f0b5`).
3. Send `c`, then walk health → title → menu → slot → chapter → level → cutscene → gameplay → pause.
4. The stub never emits a `T05`/`S05` stop packet. Control: writing `00be` at the current PC *does* stop
   immediately (`S05`), so the mechanism works.

## 4. Address map

| Address | Meaning | Evidence |
|---|---|---|
| `0x08053410` | Button-mask table, 18 × `u16` | Derived — sole pointer at `0x0800B4CC` |
| `0x0800B47C` | Button-code validator (member fn) | Derived — Thumb ptr `0x0800B47D` at `0x087B4EB0` |
| `0x0800B364` | Cheat action (one-shot) | Derived — `BL` at `0x0800B4FE` |
| `0x0800B3F0`, `0x0800B57C` | Other debug member functions | Derived — vtable `0x087B4E60` / BL at `0x0800B404` |
| `0x087B4E60`, `0x087B4EB0` | Vtable slots holding the debug fns | Derived — no pointer to either vtable found |
| `0x08154DF4`–`0x08154EA0` | Pause/debug menu label strings | Derived/observed |
| `0x087B370C`–`0x087B371C` | Debug menu string-pointer list (5 entries) | Derived |
| `0x081491DC` | "Debug" menu record; string ptr `0x081491F0` → `Debug` | Derived |
| `0x08018580`–`0x08018780` | Pause-menu builder; references the Debug record | Derived |
| `0x08154C00`–`0x08154F40` | UI text bank (ASCII, NUL-terminated) | Derived/observed |
| `0x08154D40`, `0x08154D54`, `0x08154D74` | `Initial Entry:`, alphabet, `Difficulty Select` | Derived |
| `0x03000FF0` | Global pointer to input-state struct | Derived (562 literal refs) |
| `0x020079D8` | Input struct (live): `+0x24` = raw KEYINPUT (`0x3FF` idle) | Observed via RSP |
| `0x02030000` region | EWRAM heap / game objects | Observed |

## 5. Algorithm — button-code validator (`0x0800B47C`)

Reconstructed from Thumb disassembly (`b5f0 … 4708`), register-accurate:

```c
// ctx = r0; offsets are byte offsets into the owning object
u8 *idx = (u8*)(ctx + 0x1C2);   // matched-press counter
u8 *tmr = (u8*)(ctx + 0x1C3);   // frames since last match

void check(void *ctx) {
    if (*idx != 0) (*tmr)++;          // timing starts after the first press
    if (*tmr > 29) { *idx = *tmr = 0; return; }   // 30-frame (0.5 s) inter-press window

    u16 want = TABLE_08053410[*idx];  // u16 little-endian
    Input *in = *(Input**)0x03000FF0;
    u32 held = in->held;              // [in+0], active-high
    u32 press = in->pressed;          // [in+4], active-high, this frame

    if ( ((held & ~want) & ~press) != 0 ) { *idx = *tmr = 0; return; } // extra keys => reset
    if ( (press & want) != 0 || (held & want) == want ) {
        (*idx)++;  *tmr = 0;
        if (*idx > 10) {              // 11 successful presses
            cheat_action(ctx);        // 0x0800B364
            sfx(0x08000230);
            *idx = *tmr = 0;
        }
    }
}
```

`cheat_action` at `0x0800B364` is one-shot (`ctx+0x1C4` guard). It copies/renders a tile block to VRAM
`0x0600D800`/`0x0600F800` from `0x0813E068`/`0x08233F68` via `0x08005D0C`, adds `0x60` to each of
`0x400` `u16` values copied into `[ctx+0x58]` (a tile/palette remap), sets bit 8 of
`*(u16*)(0x03000FF0 + 8)`, and sets `ctx+0x1C4 = 1`. This is a graphics/debug toggle, not an unlock or
password.

Input convention verified independently: the sleep handler at `0x08020A46` tests mask `0x01` for A,
confirming active-high `A=1, B=2, Select=4, Start=8, Right=0x10, Left=0x20, Up=0x40, Down=0x80,
R=0x100, L=0x200`.

## 6. Tables

**Button-mask table `0x08053410`** (18 `u16`, little-endian):

| Index | Mask | Meaning (active-high) |
|---:|---:|---|
| 0–2 | `0x20` ×3 | Left ×3 |
| 3–4 | `0x10` ×2 | Right ×2 |
| 5–7 | `0x80` ×3 | Down ×3 |
| 8–9 | `0x40` ×2 | Up ×2 |
| 10 | `0x04` | Select |
| 11 | `0x00` | — |
| 12 | `0x04` | Select |
| 13 | `0x00` | — |
| 14 | `0x05` | Select+A |
| 15 | `0x00` | — |
| 16 | `0x06` | Select+B |
| 17 | `0x00` | — |

The validator only consumes indices 0–10 before firing; entries 11–17 are not used by this code path.
Preceding data at `0x08053380` is a separate `u8` direction-index sequence (values 1–8), not a code table.

**Debug-menu labels** (ROM offsets; string-pointer list at `0x087B370C`): `Go Back` (`0x08154E40`),
`Level Select` (`0x08154E48`), `Slow Motion` (`0x08154E58`), `Replay` (`0x08154E64`),
`Toggle Debug Keys` (`0x08154E6C`). `Start Profiling` / `Stop Profiling` / `Write Profile`
(`0x08154E80`/`90`/`A0`) exist as text but have **zero** 32-bit pointers in the image — unreferenced
labels.

**Debug key hint** `0x08154F7C`: `A-default Start-go L-print` — describes keys *within* debug mode, not an
activation sequence.

**Name-entry alphabet** `0x08154D54`: `ABCDEFGHIJKLMNOPQRSTUVWXYZ_!?$&` — 31 symbols (26 letters +
`_ ! ? $ &`).

## 6b. Enumeration

**Code space.** The only cheat-like code system in the image is the button-code table above. Its complete
space is the 11-mask prefix `0x20,0x20,0x20,0x10,0x10,0x80,0x80,0x80,0x40,0x40,0x04` — i.e.

> **Left, Left, Left, Right, Right, Down, Down, Down, Up, Up, Select**

with a 30-frame (~0.5 s) deadline per step, exact-mask semantics (no extra keys held), and a one-shot
action. The remaining 7 table entries are not consumed by this validator. Table size: 18 entries; active
prefix length: 11 presses. There is no password alphabet/code/checksum system anywhere else in the image.

**Novel code.** The 11-press sequence above is the decoded candidate and appears in no published list
(no list exists for this SKU on the accessible web). It was entered on the title screen, the main menu and
during level-1 gameplay, with 70–120 ms holds and 100 ms gaps (well inside the 0.5 s window). **No
state change was observed** on any screen. The reversed-direction variant
(Right×3, Left×2, Up×3, Down×2, Select) was also entered as a rejection control; likewise no effect.
The decisive evidence is the `bkpt` experiment in §3: the validator at `0x0800B47C` is never called on
any of the eight screen classes, and no pointer to its vtable (`0x087B4E60` / `0x087B4EB0`) exists in the
8 MiB image or in live EWRAM/IWRAM. Therefore the code is **not enterable in the retail build** and no
novel *accepted* code can be minted. This is a bounded dead-code result, not an untested hypothesis.

**Bounds proven by rejection.** Wrong sequences, reversed directions and out-of-window timing all leave
the game state unchanged; in the validator itself, `*tmr > 29`, any extra held bit, and a non-matching
mask each reset `*idx`/`*tmr` to zero (derived from `0x800B49E`, `0x800B4BA`, `0x800B4E2`).

**Debug menu enumeration.** Five reachable-by-code labels in the pointer list, plus three unreferenced
profiling labels. The menu record at `0x081491DC` is referenced by the pause-menu builder at
`0x08012A14`, `0x08018620`, `0x0801868C`, `0x080187D4`, but the observed pause menu contains only
`Resume/Quit/Sleep` — the Debug branch is gated and the gate could not be opened by any input tested.

**Name field enumeration.** One text-entry surface (`Initial Entry:`, 31 symbols). It is a profile name
field, not a validator: no `strcmp`/`memcmp` against a constant or flag word could be tied to its buffer,
and no second alphabetic code surface exists in the text bank.

## 7. Validation evidence

- **Observed**: all screens in §3; raw KEYINPUT state `0x3FF` idle at `0x020079FC` (input struct `0x020079D8` + `0x24`); `bkpt` control stop
  (`S05`) and zero stops at the validator; unchanged visuals after both button-code variants.
- **Derived**: every address in §4; the validator pseudocode and mask semantics; the action's VRAM/palette
  writes; the one-shot guard; the debug-menu label list and pointer counts.
- **Inferred**: the `Initial Entry:` field is a name entry rather than a password (documented ordering in
  the text bank, no validator found); the unreferenced profiling labels were intended for a build with
  profiling enabled.

## 8. Unknowns

- The precise gate that would expose the Debug menu record in the pause menu was not isolated; the flag
  byte at `object+0x1A` read by `0x080296C0` and the debug bytes at `ctx+0x1C0/0x1C1/0x1C4` have known
  readers but their reachability from retail input is unproven beyond the breakpoint result.
- The `Initial Entry:` screen itself was not reached in the walk (the implemented `New Game` flow skips
  it). Its consumer was not isolated.
- No published code list could be fetched, so "not in any published list" rests on the absence of any
  findable list for this SKU rather than a comparison against a specific page.

## 9. Tooling

- `strings -t x -n 4`, `xxd`, `grep -abo` for text/pointer recon.
- `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for all disassembly.
- Custom Python helpers in `/tmp/opencode/santa3/`: `xref.py`, `xrefs2.py`, `blscan.py`, `keypad.py`,
  `buttonscan.py`, `rsp.py` (minimal GDB RSP client), `bptest2.py` (breakpoint control), `bp_walk.py`
  (validator reachability walk), `ssdiff.py` (zlib `gbAs` savestate diff), `k.py` (XTEST key helper).
- mGBA 0.10.5 under Xvfb `:317` + openbox, `SDL_AUDIODRIVER=dummy`, `-3`, `-g` where noted.

No ROM or copyrighted asset is redistributed here; only hashes, addresses, and decoded logic are published.
