# Rayman Advance (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Rayman Advance/Rayman Advance.gba` |
| Size | 8,388,608 bytes (0x800000) |
| Header title | `RAYMAN` |
| Game code | `ARYE` |
| Maker | `41` (Ubisoft) |
| Version | 0x00 (Rev.00) |
| Fixed byte 0x96 | present at 0xB2 |
| Header checksum | 0x00F3 (non-zero: retail header) |
| Entry word | `0xEA00002E` → `0x080000C0` (stock crt0) |
| MD5 | `616f80f482ade86d88021b41587aa600` |
| SHA-1 | `ff8a41c781735d2b4fe6cde65e82fb5a68f77f8b` |
| SHA-256 | `412eefc515fe40033e9bac640bc5842e60b531014c563c60659c9e574570fb72` |

Embedded GBA-header scan for the 156-byte Nintendo logo found **exactly one** header, at file 0x0. No multi-game cart, no appended trainer, no cracktro patch. This is an independent analysis; conclusions from the sibling Rayman 3 / 10th-Anniversary reports were not carried over.

## 2. Executive summary

**The developer-intended cheat system is a six-entry button-code ("pause code") system, not a password system.** It is entered while the in-game START prompt ("Do you really want to quit the game?") is displayed. Six 6-button sequences are stored as u16 key masks at ROM `0x08153C68`; a single validator at `0x080051D8` matches them and dispatches through a six-entry function-pointer table at `0x08005280`. All six action branches were enumerated and each effect was verified by RAM diff; one published code and one newly minted (unpublished) 7-press variant were entered in mGBA and confirmed.

**The password screen is a dead, unused feature in this GBA SKU.** The password UI strings exist in the text bank (text IDs 168–175), but the reachable menu tree (title → sound → choose-a-game → world map → level → START quit prompt) contains no password entry point. The codes published on 3rd party cheat indexes under "Rayman Advance / NTSC Passwords" (`942KV7N9XD`, `SD3BKFOOMN`, `J5VLFP58VB`, `J5K!ZZC8MD`, `SM!KV7WSXD`, `SX2!ZP58MD`) are **PlayStation-version codes mislabeled as GBA** (§16.11): none of them appears literally anywhere in the 8 MiB image under ASCII/+0x20/UTF-16, and the PS1 NTSC password tables from RCP do not validate them against this ROM. 3rd party cheat indexes independently describes the GBA password screen as unused and non-working. Every reachable screen was walked with screenshots and RAM reads; the negative is bounded below.

## 3. How to reproduce

- **Emulator:** mGBA 0.10.5 under Xvfb `:315`, `SDL_AUDIODRIVER=dummy`, `-3 -g` (GDB stub on :2345).
- **Keymap (verified by reading `KEYINPUT` 0x04000130 with each key held):** A=`x` (bit0), B=`z` (bit1), Select=`BackSpace` (bit2), Start=`Return` (bit3), L=`a`, R=`s`, D-pad=arrows. Hold each key ~280–300 ms; 80 ms taps are dropped.
- **Path to the code screen:** boot → press A through the Digital Eclipse / Ubisoft / title / sound screens → "Choose a game" → A on a slot → world map → A on a level → A through the level intro → **press Start (Return)**. The screen "DO YOU REALLY WANT TO QUIT THE GAME? YES / NO" is the code-entry context. Enter the sequence there; afterwards press A on NO to resume.
- **Example (published, 99 Lives):** `Left, Right, Down, Right, Left, R`.
- **Novel (unpublished, All Items +25 tings):** `R, R, Up, Left, Right, Left, L` — the duplicate first press is deliberately ignored by the matcher.
- **Rejected example:** `R, Up, Down, Left, Right, Left, L` (wrong third button) — no state change.
- Screenshots saved as `shot01.png` … `shot41.png` in `/tmp/raymanadvance/`; key frames: `shot21` gameplay, `shot24`/`shot28` quit prompt, `shot31` choose-a-game, `shot33` world map, `cur8.png` HUD x99 after the 99-lives code.

## 4. Address map

All addresses are ROM addresses (`0x08000000 + file offset`) unless marked RAM.

| Address | Kind | Meaning |
|---|---|---|
| `0x08153C68` | ROM table | 6 button-code sequences, 6 × u16 masks each, **12-byte stride** (= 72 bytes total, ends `0x08153CB0`) |
| `0x080051D8` | ROM function | Button-code validator (Thumb). Called once from `0x08044F4A` |
| `0x08005280` | ROM table | 6-entry action dispatch (u32 Thumb pointers), indexed by selected code |
| `0x08005298`/`A4`/`AC`/`D4`/`E8`/`FC` | ROM functions | Action handlers 0–5 |
| `0x08044F44` | ROM function | Per-frame caller (pause/quit UI); calls input reader `0x08044B98`, then validator |
| `0x0854ADB4` | ROM table | English script text table, 258 entries; text ID 168 = `/password/`, 169 = `/enter password/`, 173 = `/x : validate password/`, 175 = `/wrong password/` |
| `0x020011FC` | RAM byte | Validator progress (0xFF idle/armed, 1…6 = presses matched) |
| `0x02021E40` | RAM byte | Selected code index (5 = sentinel/none; 0–5 = code) |
| `0x02030E5C` | RAM u16 | Active-high key mask consumed by the validator (`~KEYINPUT & 0x3FF`) |
| `0x0202EEA0` | RAM u16 | Lives (99-lives handler writes 0x63) |
| `0x0202EEA6` | RAM byte | Tings (All-items handler adds 25, capped at 99) |
| `0x0202EEA9` | RAM byte | Maximum health (source for heal handler) |
| `0x0202FCF4` | RAM u16 | Current health (heal handler destination) |
| `0x02001180` | RAM byte | Invincibility toggle |
| `0x0202BEE4`/`+1` | RAM bytes | Ability/flags bitfield (all-powers handler ORs 0x87 / 0x05) |
| `0x02021E58` | RAM byte | Level-select toggle |

## 5. Algorithm

The key-state word `k = ~KEYINPUT & 0x3FF` is masked with `0x3F0` (directions + shoulders only; A/B/Select/Start are ignored). Let `T` be the table at `0x08153C68`, `n` the selected code index, `p` the progress byte at `0x020011FC`.

```
k = key_state & 0x3F0
if k == 0: return                         # no direction/shoulder held
if p == 0xFF:                             # idle: try to arm
    for n in 0..5:                        # bounds: cmp n,#5 ; ble
        if k == u16(T + n*12 + 0):        # first mask only
            selected = n; p = 1; return
    return
# active matching
expected_prev = u16(T + n*12 + (p-1)*2)
if k == expected_prev: return             # repeated/held key: ignore
expected_next = u16(T + n*12 + p*2)
if k != expected_next:
    p = 0xFF; return                      # mismatch: reset, no effect
p = p + 1
if p <= 5: return                         # need 6 presses total
dispatch[n]()                             # action fires
p = 1; selected = 5                       # reset for next code
```

Actions (dispatch table `0x08005280`, index = selected code):

```
0: lives = 99
1: invincible ^= 1
2: powers |= 0x87 ; powers2 |= 0x05
3: level_select ^= 1
4: health = max_health
5: tings = min(tings + 25, 99)
```

The `cmp … #5` / `bls … #5` bounds in the arming loop and the post-completion check prove the space is exactly six codes; there is no 7th branch.

## 6. Tables

Mask encoding: A=0x001, B=0x002, Select=0x004, Start=0x008, Right=0x010, Left=0x020, Up=0x040, Down=0x080, R=0x100, L=0x200.

| # | Table addr | Published sequence | u16 masks | Handler | Effect (RAM-verified) |
|---|---|---|---|---|---|
| 0 | 0x08153C68 | 99 Lives | L,R,D,R,L,R | 0x08005298 | `0x0202EEA0 = 0x63` — HUD x99 (observed) |
| 1 | 0x08153C74 | Invincibility | R,U,R,L,R,R | 0x080052A4 | `0x02001180: 0→1` (observed) |
| 2 | 0x08153C80 | All Powers | D,L,R,L,U,L | 0x080052AC | `0x0202BEE4 = 0x87`, `+1 = 0x05` (observed) |
| 3 | 0x08153C8C | Level Select | U,L,R,D,R,L | 0x080052D4 | `0x02021E58: 0→1` (observed) |
| 4 | 0x08153C98 | Restore Health | L,D,L,U,D,R | 0x080052E8 | `0x0202FCF4: 0x01FF→0x03FF` (observed after deliberately lowering health) |
| 5 | 0x08153CA4 | All Items (+25 tings) | R,U,L,R,L,L | 0x080052FC | `0x0202EEA6: 0x19→0x32` (observed) |

Published but **not verified in this ROM**: "Unlimited Continues" (Up,Down,Right,Left,Start at the continue screen) — no matching u16 table was found; and "All Electoons" (Select+B+R twice on the map screen) — separate combo path, not part of this table. These are reported as unverified rather than assumed.

## 6b. Enumeration

**Space size.** Exactly 6 codes × exactly 6 presses each = six accepted sequences; 6 action branches (dispatch table indices 0–5). The arming loop and completion check are both bounded at 5 (`cmp r1,#5; ble`, `cmp r0,#5; bls`). Button masks use only the 8 direction/shoulder bits (0x3F0); A/B/Start/Select are ignored by the validator. No variable-length or prefix-dispatch codes exist beyond these six.

**Novel code (not in 3rd party cheat indexes, or the Hyncer FAQ):** `R, R, Up, Left, Right, Left, L` — a 7-press variant of All Items with a duplicated first R press. Entered on the game's own quit prompt in mGBA. Result: progress went `FF→1→1→2→3→4→5→1`, selected index reset, and tings at `0x0202EEA6` increased `0x19 → 0x32` (+25). This works because the matcher's `expected_prev` comparison discards a repeated holding key rather than advancing or rejecting (§5). Screenshot evidence and GDB reads are in the work directory.

**Bounds proven by rejection.** `R, Up, Down, Left, Right, Left, L` (correct first two presses, wrong third) was entered on the same screen: tings stayed at `0x32`, progress reset to `1`, and no action handler ran. An earlier test with a wrong first button showed progress staying at `1` and the selected-index sentinel remaining `5` with no state change. This proves the sequence, not just the checksum/table, is validated.

**Password-system negative (bounded).** Searched: `strings -t x -n 4` over the full image for password/cheat/code/debug/secret/unlock/level; literal search for all six published "GBA" passwords (all absent); pointer scans for all password strings (hits only in the five language text tables `0x0854ADB4` … `0x0854C9F4`); a byte-pattern search for the RCP PS1 NTSC display/XOR/hash/translate tables (all absent); and a 32-byte printable-ASCII permutation scan for an alternate GBA alphabet (no candidate). Reachable-screen walk: Digital Eclipse logo → Ubisoft → title → sound options → choose-a-game (COPY/ERASE/START only) → world map → level intro → gameplay → START quit prompt → back to title. No password option is reachable, and no in-game screen displays a password. Conclusion: **no functional password code system exists in this GBA image**; the published "GBA passwords" are PS1 codes.

## 7. Validation evidence

- **Observed:** full menu walk via screenshots; keyboard map via `KEYINPUT` reads; 99 Lives HUD changing x05→x99; RAM diffs for all six handlers; novel 7-press code changing tings 0x19→0x32; rejected sequence leaving tings unchanged.
- **Derived:** validator control flow and the 6-entry table/dispatch bounds from Thumb disassembly at `0x080051D8`–`0x0800529E`; mask encoding from the literal u16 table at `0x08153C68`; handler RAM targets from literal pools at `0x080052A0`–`0x0800530C`.
- **Inferred:** the meaning of the flag bitfields at `0x0202BEE4` (the "All Powers" OR mask 0x87/0x05 was observed, but each individual bit's in-game semantics was not exhaustively played); the "All Electoons" and "Unlimited Continues" combos are published-only.

## 8. Unknowns

- Individual semantics of each bit in the `0x0202BEE4` powers bitfield.
- Whether the disabled password screen can be forced active by a save flag; its screen function and gate were not isolated (the menu walk and string/pointer scans above bound the reachable surface).
- The "Unlimited Continues" and "All Electoons" combos were not instrumented; no matching u16 table was located for the former.
- Health code was verified after deliberately patching health via GDB rather than by taking damage in-game; the handler's effect itself is observed, the trigger path is not.

## 9. Tooling

`strings`, `xxd`, `grep -abo`, `arm-none-eabi-objdump -M force-thumb`, Python 3 + capstone/keystone/Pillow, `Xvfb :315` + `openbox`, mGBA 0.10.5 (`-3 -g`), `xdotool`, `scrot`, ImageMagick, `gdb-multiarch` and a small custom GDB remote-serial daemon (`gdbclient.py`, `gdbd.py`, `g.py`, `onekey.py`, `keymap.py`) used to read/write RAM. External cross-checks: RCP `BinarySerializer.Ray1/Helpers/PS1Password.cs` (PS1 algorithm, does not apply to this SKU), 3rd party cheat index cheats, Hyncer FAQ, 3rd party cheat index mirror. No ROM or copyrighted assets are redistributed; only addresses, hashes, masks, and our own tooling are published.

## 10. Legal note

Analysis only. The ROM and extracted graphics/text are not redistributed.
