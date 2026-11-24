# Paws & Claws: Pet Resort (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Paws & Claws: Pet Resort/Paws & Claws: Pet Resort.gba` |
| Size | 4,194,304 bytes (`0x400000`) |
| Header title | `PAWSANDCLAWS` |
| Game code | `BURE` |
| Maker code | `78` |
| Version | `0x00` (Rev. 00) |
| `file`(1) | Game Boy Advance ROM image: "PAWSANDCLAWS" (BURE78, Rev.00) |
| Entry word | `0xEA00002E` → branch to `0x080000C0` |
| MD5 | `b0118c3619b732c172ce9770393d8a06` |
| SHA-1 | `5c75c67dae18bd77ca2bb05a76782a14806d45a7` |
| SHA-256 | `f40310c87c739f33c224f7c6f0f7960511e7aa43879d5dce8fbfc0171687227b` |

Embedded-header scan (full 156-byte Nintendo-logo match): **exactly one** header, at file `0x0`. No second image, no appended trainer, no scene cracktro: the entry word is the stock branch to `0x080000C0` and the crate's first 4 KiB disassembles as normal ARM crt0. Header checksum byte `0x2C` (non-zero) and complement byte `0x00` are a quirk of this build, not a patch signature.

## 2. Executive summary

**There is no developer-intended cheat / password / button-code system in this ROM.** This is a bounded negative, not an absence of searching:

* The only text bank is a 263-string ASCII table at `0x083F7974`. Every string was dumped and decoded (IDs 0–262). None is a password, cheat, debug prompt, level/warp selector or hidden-menu label. `Manfred Trenz - Magic Code` (ID 10) is a developer credit shown on the Credits screen — not a cheat keyword.
* A separate 75-symbol table at `0x083F7374` is the on-screen **keyboard alphabet** for the New Game name-entry field, not a password alphabet. Its consumer (`0x08002800`–`0x080028C0`) only writes characters into a 24-byte name buffer at IWRAM `0x030005E0`; the save/load routines (`0x08009374`, `0x080096C4`) only **copy** that buffer to/from the save record. No code compares it with a constant (§16.2b: it is a label, not a validator).
* The screen-state dispatcher has exactly **22 states (4–25)** via a jump table at `0x080020E8`. Every reachable state was identified from the menu flow / string bank. There is no debug state, no state outside the 22 whose handler is not the default loop.
* Button-code space: the input shadow is at IWRAM `0x030000E0` (active-high, from `KEYINPUT` at `0x04000130` via `0x08000280`). No table of key-mask sequences exists: Konami-style sequences are absent as `u16` and `u8` arrays, and a mask-array scan found only random false positives in code/compressed data. Controlled key presses on the title produced no persistent flag beyond normal menu state.
* Published-code checks: 3rd party cheat index lists **0 cheats** for this exact GBA SKU; 3rd party cheat index lists none; 3rd party cheat indexes have no *Pet Resort* cheat page (only the different SKU *Paws & Claws: Pet Vet*, whose codes `kayoo`, `all buildings`, `money`, `droopy`, `momo` were tested against this ROM in ASCII, upper-case, alphabet-index, UTF-16LE and `+0x20` encodings — none present; the lone ASCII `money` at `0x3FB7D3` is part of the dialogue word "Available money:").

Consequently §0.2's "mint a novel code" deliverable does not apply: no code space exists to enumerate. §6b documents the bounded negative with exact counts.

## 3. How to reproduce

Emulator: mGBA 0.10.5 under `Xvfb :319 -screen 0 1280x900x24`, `openbox`, `SDL_AUDIODRIVER=dummy`, launched as `mgba -3 -g <rom>` (GDB stub port 2345). Keymap (mGBA SDL default): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows; 70–150 ms holds.

Menu paths walked (all screenshots saved in `/tmp/pawsclaws/`):

1. **Boot** → publisher splash (Denaris Entertainment Software / THQ / copyright) → **Title**: NEW GAME / LOAD GAME / RIDE OUT / CREDITS (4 entries, one selection ring).
2. **NEW GAME** → name entry (75-symbol keyboard, 24-char name) → difficulty (Easy / Medium / Difficult) → scenario (6 entries) → story pages → gameplay.
3. **In-game pause** (Start): Pause / Scenario Targets / Save Game / Load Game — a **4-slot ring**; five further drawn buttons are blank and unreachable (Down at index 3 does not advance).
4. **RIDE OUT** → horse-breed select (Haflinger / Pony) → side-scrolling riding mode → pause with 3 entries (Pause / Continue game / Cancel game).
5. **CREDITS** → developer credits (the "Magic Code" line is a credit).
6. **LOAD GAME** → "LOAD SCORE": four save slots, all `EMPTY`, with Back / Load.

RAM evidence: the GDB stub was kept on one persistent connection via a FIFO bridge. Screen state lives at `0x03000558` (`0x09` observed on the LOAD SCORE screen, matching the `cmp #9` at `0x0800315A` that chooses ID 2 "LOAD SCORE" vs ID 3 "SAVE SCORE"). `KEYINPUT` shadow at `0x030000E0` read `0x03FF` (all released) at rest. Full IWRAM/EWRAM dumps were taken at the title and after controlled key sequences (`ram_title.bin`, `ram_ctrl.bin`, `ram_lrsb.bin`, `ram_konami.bin`).

## 4. Address map

| Address (ROM) | Meaning | Evidence |
|---|---|---|
| `0x08000000` | ARM entry / crt0 (stock `0xEA00002E`) | Derived (disassembly) |
| `0x08000280` | key reader: `~KEYINPUT & 0x3FF` → IWRAM `0x030000E0` | Derived |
| `0x080002A0` | key-mask test helper | Derived |
| `0x08002088` | screen-state setter → `0x03000558`, `0x03000534` | Derived |
| `0x080020E8` | 22-entry screen-state jump table (states 4–25) | Derived |
| `0x080021C8` | per-frame input dispatch for the same 22 states | Derived |
| `0x08017214` | `get_string(id)`; 135 BL call sites; base literal `0x083F7970` | Derived |
| `0x08002800`–`0x080028C0` | name-entry keyboard handler; alphabet literal `0x083F7374` | Derived |
| `0x08009374`, `0x080096C4` | save/load copy of the 24-byte name to/from the save record | Derived |
| `0x083F7374` | 75-byte alphabet/glyph table for name entry | Derived |
| `0x083F7970` | pointer to string table | Derived |
| `0x083F7974` | 263-entry string pointer table (IDs 0–262) | Derived |

| Address (RAM) | Meaning | Evidence |
|---|---|---|
| `0x030000E0` | active-high key state shadow (`A=1,B=2,Select=4,Start=8,R=0x10,L=0x20,U=0x40,D=0x80,Rtrig=0x100,Ltrig=0x200`) | Derived + Observed (`0x03FF` idle) |
| `0x0300054C` | name-entry keyboard cursor | Derived |
| `0x03000558` | current screen state (`9` = LOAD SCORE observed) | Derived + Observed |
| `0x03000570` | name length counter | Derived |
| `0x030005E0` | pointer to 24-byte player-name buffer | Derived + Observed |

## 5. Algorithm

No password/checksum algorithm exists. The only input decoder present is the name-entry keyboard:

```
key_index = on-screen cursor position (0..74)
if key_index <= 73:
    name[name_len] = alphabet_0x083F7374[key_index]
    name_len++          (bounded to 20 in UI; buffer cleared over 24 bytes)
elif key_index == 74:   # '<' glyph
    name_len--          (backspace)
```

`alphabet_0x083F7374` (75 bytes, indices 0–74):
`ABCDEFGHIJKLMNOPQRSTUVWXYZ` (0–25), `Ä Ö Ü` (26–28), `!` (29), `abcdefghijklmnopqrstuvwxyz` (30–55), `ä ö ü ß` (56–59), `0123456789` (60–69), `, - . SPACE` (70–73), `<` (74, backspace).

Screen dispatch:
```
state = *(u16*)0x03000558
if 4 <= state <= 25: jump table[state-4] at 0x080020E8
else: default → loop (0x080021BC)
```

## 6. Tables

* **String table** `0x083F7974`, 263 entries (IDs 0–262). Notable: ID 0 combined title menu; IDs 1–5 alternate title labels (`NEW GAME`, `LOAD SCORE`, `SAVE SCORE`, `RIDE OUT`, `CREDITS` — a legacy wording of the save-slot menu, not a hidden screen); ID 8 "Select your score:"; ID 10 credits (contains "Magic Code"); ID 49 3-entry ride pause; ID 52 4-entry in-game pause; IDs 102–107 Scenario 1–6; IDs 231–240 save/load prompts. **No cheat/debug/password entries.**
* **Animal-name tables** at `0x083FBF1C` (17 names) and `0x083FBF6C` (108 names) — cosmetic pet names, not codes.
* **Save slots**: 4 (`1:`–`4:`), all EMPTY in a fresh cart.
* **Scenarios**: 6, all selectable from a new game (no unlock gate).
* **Published franchise codes tested** (from *Pet Vet*, different SKU): `kayoo`, `all buildings`, `money`, `droopy`, `momo` — none present in this ROM under any tested encoding.

## 6b. Enumeration

This title has **no code system**, so the enumeration deliverable is the proof of the negative:

| Search space | Method | Count / result |
|---|---|---|
| All strings, ASCII 3+ chars | `strings -t x -n 3` over 4 MiB | 0 cheat/debug/password/level-select keywords; only "Magic Code" (developer credit) and gameplay words |
| String bank | Dumped 263 IDs from `0x083F7974` | 263/263 decoded; 0 cheat/debug entries |
| Font / tile-indexed text | Located and decoded the only glyph table `0x083F7374` (75 symbols) | 75/75 decoded; it is the name-entry alphabet, not a code alphabet |
| Name-field consumers | All 5 literal refs to name-buffer pointer `0x030005E0` disassembled | 0 comparisons; only buffer writes and save copies → label, not validator (§16.2b) |
| Typed-cheat literals | 5 published *Pet Vet* codes × 5 encodings (ASCII, upper, alphabet-index, UTF-16LE, `+0x20`) | 0 real hits (1 incidental "money" inside dialogue "Available money:") |
| Button-code tables | Konami sequence (u16 + u8) and its reverse; strict single-mask arrays ≥5 | 0 hits; all mask-array hits were misaligned code/compressed-data noise |
| Screen states | Jump table `0x080020E8` | exactly 22 states (4–25); every one maps to a menu/save/gameplay handler; no debug state |
| Menus | Visually walked with RAM reads | Title 4 entries; name-entry; difficulty 3; scenario 6 (all available); in-game pause 4 selectable + 5 unreachable blanks; ride breed 2; ride pause 3; credits; LOAD SCORE 4 slots |
| Published-code sites | 3rd party cheat indexes, web search | 0 codes for this SKU; *Pet Vet* codes belong to a different title and are absent here |

**Bounds proven by rejection:** there is no code entry surface to accept or reject a value. The nearest negative bounds are structural: (a) the pause selector refuses to move past index 3 (Down held at "Load Game" leaves the highlight unchanged), so its five blank rows are unreachable; (b) all 6 scenarios are selectable immediately, so there is no locked/unlockable scenario to mint; (c) screen states outside 4–25 take the default loop, so no hidden screen can be entered by state manipulation through any reachable menu.

No novel code was generated because no validator, table, alphabet or entry surface for one exists; §0.2's "mint and confirm a code" requirement applies to code systems only.

## 7. Validation evidence

* **Observed**: screenshots of every screen listed in §3; `0x03000558 = 0x09` on LOAD SCORE; `KEYINPUT = 0x03FF` at rest; RAM dumps before/after key sequences; full 4 MiB hash/header scan.
* **Derived**: all addresses in §4; 263-string and 75-symbol tables; 22-state jump table; name-field consumer analysis; key-mask and literal searches.
* **Inferred**: that scenarios/blank pause rows are intentionally placeholders (their labels and selector bounds strongly indicate it, but no developer statement exists).
* **Prompt injection**: none encountered in fetched pages (3rd party cheat indexes snippets were treated as data only).

## 8. Unknowns

* The five blank pause-menu rows: they are unreachable in the tested scenario. They may be filled in other game states, but no code path or string ID for them exists in the 263-string bank, so their intended content remains unknown.
* IDs 1–5 (legacy "LOAD/SAVE SCORE" title labels) are used, but the title menu renders ID 0; the exact build reason for the duplicate labels is unknown.
* In-game action menus (Administration / Dealer / Pen Expansion / Animal Overview / Animal Lexicon / Food Chamber / Clean Pen) were enumerated from the string bank (IDs 53–79) and the manual, not exhaustively clicked through; none contains a cheat/debug label.

## 9. Tooling

`file`, `md5sum`, `sha1sum`, `sha256sum`, `strings`, `xxd`, `grep`, `python3`, `capstone 5.0.7`, `binutils-arm-none-eabi` (`arm-none-eabi-objdump -M force-thumb`), mGBA 0.10.5 with GDB stub, `gdb-multiarch`, Xvfb, openbox, xdotool, scrot, ImageMagick. Analysis scripts in `/tmp/pawsclaws/`: `header_scan.py`, `xref.py`, `findlit.py`, `pcldr.py`, `blxref.py`, `maskscan.py`, `maskscan2.py`, `rsp.py`, `bridge.py`, `dumpram.py`, `restart.sh`.

No cheats were applied and no game assets are redistributed.
