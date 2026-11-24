# World Poker Tour (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `World Poker Tour.gba` (4,194,304 bytes / 4 MiB) |
| Header title | `WPT2K6` |
| Game code | `B26E` |
| Maker code | `54` (raw bytes `0x35 0x34`) |
| Revision | `00` (`file`: B26E54, Rev.00) |
| Fixed byte / complement / checksum | `0x96` / `0x4B` / `0x0000` |
| Entry word | `0xEA00002E` → `0x080000C0` (stock crt0, **not** a scene-patched image) |
| MD5 | `0c112fda9346a9851fa7cb72d80be501` |
| SHA-1 | `c75851d14a96dea46770945aafeaf9a8f6c12271` |
| SHA-256 | `754ec69e3e63856933bd7138f2c9eca7ece4ff28567feab1c01a4f4b76b8258f` |

All analysis used a byte-identical copy at `/tmp/wpt/wpt.gba` (MD5 re-checked), so no save/state artifacts were written to the ROM folder.

## 2. Executive summary

This game has a **developer-intended button-code cheat system**, not a password or text-code system. Three cheats are published on GameFAQs; all three were verified in the ROM and in mGBA:

| Cheat | Where pressed | Gate | Effect / flag |
|---|---|---|---|
| **Snappy Mode** | Title ("Press Start") screen | `0x0800ED50` | toggles byte `0x03002F10` (0/1); skips all transitions |
| **All-Seeing** | Main Menu → cursor **Options** (menu ID 10) | `0x0800F060` | toggles u32 `0x0300398C`; open-handed poker |
| **Victory** | Main Menu → cursor **Credits** (menu ID 11) | `0x0800F060` | confirm dialog → u32 `0x03003984 = 1`, byte `0x03002F04 = 10`, word `0x03002F00 = -1`; irreversible, unlocks features |

The shared input condition is the same-frame key state: `L+R` held **exactly** (`0x0300` active-high, no other key) plus a newly-pressed edge in `L` or `R`. Two extra L+R consumers exist and are **not** cheats: a profile-delete confirmation (`0x0801C43A`, observed) and a modal-dialog callback (`0x080186EA`, no cheat flag or message write). There is no text-code entry surface; the only on-screen keyboard is a profile-name label field (§8).

A **novel, undocumented combination** — holding **R then pressing L** (reverse of the published "hold L, press R") at Options — was generated and accepted in the emulator (screenshot `f_novel_allseeing.png`, flag `0x0300398C` 0→1). Bounds were proven by 12 rejections (§6b).

## 3. How to reproduce

Emulator: mGBA 0.10.5 under Xvfb `:317`, `SDL_AUDIODRIVER=dummy`, `-3` scale.
Keymap verified from RAM (`0x030014A4`, active-high bits): `x`=A (`0x001`), `z`=B (`0x002`), `BackSpace`=Select (`0x004`), `Return`=Start (`0x008`), Right/Left/Up/Down=`0x010/0x020/0x040/0x080`, `s`=R (`0x100`), `a`=L (`0x200`).

1. Boot to legal screen, press Start through to "Press START"; press L then R (or R then L) → "Cheat Mode! / You have enabled/disabled 'Snappy' Mode". Repeat toggles.
2. Start → Main Menu. Hold `Down` three times to highlight **Options** (RAM `0x03001900 == 0x0A`). Hold L then press R → "You have enabled/disabled the 'All-Seeing' cheat". Repeat toggles.
3. Move down once to **Credits** (`0x03001900 == 0x0B`). Hold L then press R → "You are about to enable the 'Victory' cheat … irreversible" with `No thanks!` / `Yes! Do it!`. Choosing Yes shows successive "Unlocked Feature" messages.
4. Save a state before step 3 (`Shift+F2`) — Victory is irreversible in the save.

Memory evidence was taken from mGBA `.ss1` states: PNG with zlib `gbAs` chunk; IWRAM at raw offset `0x19000`, EWRAM at `0x21000` (guide §16.13). Live key state was additionally captured with a persistent GDB stub and breakpoints that logged all four gates and auto-continued.

## 4. Address map

| Address | Type | Meaning |
|---|---|---|
| `0x0800851C` | function | Input poll: `active = 0x3FF & ~KEYINPUT(0x04000130)`; writes `0x030014A4` (current), `0x030014A0` (processed/prev), `0x030014A8` (edge) |
| `0x0800ED28` / gate `0x0800ED50` | function | Title-screen handler, case 0: L+R test, Snappy toggle |
| `0x0800F03C` / gate `0x0800F060` | function | Main-menu handler, case 0: L+R test, menu-ID dispatch (10/11) |
| `0x080186EA` | gate | Modal/UI callback: L+R held ⇒ normal processing, else close modal (`0x8008A18`); **no** cheat write |
| `0x0801C43A` | gate | Profile screen: L+R ⇒ "remove this profile and all its saved progress?" |
| `0x030014A0/A4/A8` | u16 RAM | processed-prev / raw-current / edge key state |
| `0x030018F0`, `+0x10 = 0x03001900` | u32 RAM | Main-menu UI object and selected menu ID (observed 7…11) |
| `0x03002EF0 + 0x20 = 0x03002F10` | u8 RAM | Snappy flag (0 off, 1 on) |
| `0x0300398C` | u32 RAM | All-Seeing flag |
| `0x03003984` | u32 RAM | Victory flag |
| `0x03002F00` / `0x03002F04` | i32/u8 RAM | Victory side effects (`-1`, `10`) |
| `0x0802CCF4` | string | `Cheat Mode!` (4 literal pointers: `0xEDA0`, `0xEDFC`, `0xF0A8`, `0xF10C`) |
| `0x0802CD00/0x0802CD40` | strings | Snappy enable / `OK` (pool `0xEDA4/EDA8`) |
| `0x0802CD44` | string | Snappy disable (pool `0xEE00`) |
| `0x0802CDA8/0x0802CDEC` | strings | All-Seeing enable/disable (pool `0xF0AC`, `0xF110`) |
| `0x0802CE2C/0x0802CE84/0x0802CE90` | strings | Victory prompt / `No thanks!` / `Yes!  Do it!` (pool `0xF118–F120`) |
| `0x0802CEF4…0x0802CF20` | strings | Menu labels Career, Multiplayer, WPT Boot Camp, Options, Credits (pool `0xF3E0`, `0xF458–F464`) |

Text is plain ASCII with leading control bytes (`0x04` = new line/format, `0x8E` = button glyph); the whole cheat-message bank `0x0802CCF4–0x0802CF47` was decoded from bytes and confirmed by literal pointers, so the negative below is not based on an unexamined font/tile bank.

## 5. Algorithm

```text
active = 0x3FF & ~KEYINPUT            # active-high: A1 B2 Sel4 Start8 Rgt10 Left20 Up40 Dn80 R100 L200
edge   = active & ~processed_prev     # gA8; processed keys feed gA0
gate   = (edge & 0x300) != 0 && active == 0x300

main_menu_gate:
    if gate:
        consume edge (store 0 at 0x030014A8)
        id = [0x03001900]              # selected menu item
        if id == 10: toggle u32 0x0300398C; show enable/disable dialog
        if id == 11: show 2-button confirm; on Yes set 0x03003984=1,
                     byte 0x03002F04=10, i32 0x03002F00=-1
        # ids 7,8,9: no action (falls through)

title_gate:
    if gate:
        consume edge; toggle byte 0x03002F10; show Snappy enable/disable dialog
```

`R→L` also satisfies the gate because `edge & 0x300` only requires *one* of the two bits; the exact-equality test on `active` still forbids any third key.

## 6. Tables

**Menu-ID → main-menu L+R action** (proved by RAM `0x03001900` and flag reads):

| ID | Label | Result of L+R |
|---:|---|---|
| 7 | Career | none |
| 8 | Multiplayer | none |
| 9 | WPT Boot Camp | none |
| 10 | Options | toggle All-Seeing (`0x0300398C`) |
| 11 | Credits | Victory confirmation → flag `0x03003984` |

**Accepted key forms** (at an armed screen): L then R; R then L; L+R in one frame. **Rejected**: L alone, R alone, L+R with any other key held.

**Other L+R consumers (not cheats)**: profile screen → delete-profile confirmation (`0x0801C43A`); modal callback `0x080186EA` (no flag/message writes, gated on `[0x03000C00] != 0`).

## 6b. Enumeration

**Space definition.** This is a button-code system, so the "alphabet" is the 10 GBA key bits and the selector is the main-menu cursor. Exact accepted inputs:

- Snappy: title screen, `active == 0x300`, `edge & 0x300 != 0`;
- All-Seeing: menu ID 10, same key condition;
- Victory: menu ID 11, same key condition + explicit "Yes" confirmation.

Exhaustive static bound: **4** occurrences of the `0x300` key mask near the key globals across the whole 4 MiB image (`0x0800ED50`, `0x0800F060`, `0x080186EA`, `0x0801C43A`); the two cheat handlers write to exactly 2 flag words + 1 flag byte and reference exactly 4 distinct "Cheat Mode!" message pools. The ASCII cheat-bank scan found exactly 3 cheat messages (plus their enable/disable variants and 1 confirmation). Therefore the reachable cheat set is **exactly 3**, not "at least 3".

**Novel code (not in any published list).** GameFAQs specifies "hold L, press R" for each cheat. We entered the undocumented reverse form on the real screen:

- Main Menu → Options (`0x03001900 = 0x0A`), hold **R** then press **L** → "Cheat Mode! / You have enabled the 'All-Seeing' cheat to play open-handed games." (`f_novel_allseeing.png`), `0x0300398C: 0 → 1`.
- Same reverse form on the title screen toggles Snappy (`f_novel_RL.png`), `0x03002F10: 1 → 0` with the "disabled" message.

L+R pressed in a single frame was also accepted on the title screen (`boot2.png`, Snappy 0→1).

**Bounds proven by rejection** (each verified by screenshot + RAM flag read):

| Rejected input | Screen | Observed |
|---|---|---|
| L+R at menu ID 7 / 8 / 9 | Main Menu | all three flags unchanged (`t7.png`, `t8.png`, `t9.png`) |
| L alone / R alone | Options | `0x0300398C` unchanged |
| L+R while Down held | Options | `0x0300398C` unchanged (extra bit breaks `active == 0x300`) |
| Victory: choose `No thanks!` | Credits | `0x03003984` stays 0 (`t11_prompt.png`) |
| L+R at Multiplayer Setup, Player Type, Select Portrait, Select Game, game table, all 5 pause-menu items | respective screens | no flag change; no gate hit |
| All-Seeing repeated L+R | Options | flag returns to 0 ("disabled" message, `shot18.png`) |
| Snappy repeated L+R | Title | flag returns to 0 (`f_snappy_on.png`) |

## 7. Validation evidence

- **Observed**: every screen transition and message above was captured with `scrot` (evidence in `/tmp/wpt/`); flags read from savestate RAM at the exact addresses in §4; key bits verified by holding each key and reading `0x030014A4`.
- **Derived**: the input routine at `0x0800851C`, the two key gates and their literal pools, the menu-ID dispatch, and the flag/message writes were disassembled with `arm-none-eabi-objdump -M force-thumb` and cross-checked against observed RAM.
- **Inferred**: gate `0x080186EA` is a modal-dismiss UI callback (calls `0x8008A18` when L+R absent; no cheat flag or cheat string anywhere in its path); it was never reached during the screen walk, so its precise screen is unresolved.
- **Not instructions**: all ROM strings and the GameFAQs page were treated as data. No action-parser instructions were found in them.

## 8. Unknowns

- The exact screen that reaches gate `0x080186EA` was not identified; static analysis shows no cheat flag or message write in its path, so it is classified non-cheat with moderate confidence.
- The Career name-entry keyboard (A–Z, space, backspace, DONE) was checked as a possible text-code surface: it is a profile label, not a validator (no comparison against its buffer was found in the cheat handlers). No hidden name-based code is claimed.
- Effect of All-Seeing was verified at the flag/message level, not by playing a full open-handed hand to completion.
- The Action Replay/GameShark codes published for this title are deliberately out of scope.

## 9. Tooling

- `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for all disassembly; Python `struct` literal/BL/pattern scanners (`scan.py`, `scan2.py`, `find_gates.py`, `find_gates2.py`, `find_ldr.py`) in `/tmp/wpt/`.
- mGBA 0.10.5 + Xvfb `:317` + openbox; `xdotool` XTEST input (`k.py`, `tight.py`).
- RAM reads: mGBA `.ss1` `gbAs` zlib chunk parser (`ss.py`, `readflags.sh`); GDB stub batch + persistent command file (`gdbcmds.txt`) that logged all four L+R gates with auto-continue.
- Web recon: GameFAQs "World Poker Tour – Cheats" (three codes above), plus Cheat Happens AR codes (out of scope) — used only as leads, each checked against ROM bytes.

No ROM or copyrighted assets are redistributed here; only hashes, addresses, and original observations are published.
