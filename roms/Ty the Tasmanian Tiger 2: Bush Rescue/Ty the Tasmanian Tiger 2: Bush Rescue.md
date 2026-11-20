# Ty the Tasmanian Tiger 2: Bush Rescue (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Ty the Tasmanian Tiger 2: Bush Rescue.gba` |
| Size | 8,388,608 bytes (`0x00800000`) |
| `file` ID | Game Boy Advance ROM image: "TYBUSHRESCUE" (BTYE69, Rev.00) |
| Header title | `TYBUSHRESCUE` (offset `0xA0`) |
| Game code | `BTYE` (`0xAC`); maker `69` (`0xB0`); fixed `0x96` (`0xB2`) |
| Version | `0x00` (Rev.00); complement `0x00`; header checksum `0x0000` |
| Entry word | `0xEA00002E` — **stock** ARM branch to `0x080000C0` (§16.1: not a patched/cracktro entry) |
| crt0 | Standard ATI-style crt0 at `0x080000C0` (`mov r12,#0; ldr sp,=0x03007F00; ...`) |
| Build string | `Build: 040817-133b` at file `0x7AEB00`; `E3 Demo` at `0x7AEB14` |
| MD5 | `56424a475e1171e608fdaaf3883c3cf9` |
| SHA-1 | `84267ce3d86100688048a8d4f166fa1b2d50e6d5` |
| SHA-256 | `a6e7d7067015ed1f7b930a1838cc30c48a02260bcc5db9cfc57b572ad78a2171` |

SKUs are not interchangeable here: the widely published button codes for this title are for
GameCube / PS2 / Xbox / PC / Switch / PS4 (§16.11). The GBA SKU `BTYE` was verified independently;
no Ty-3 or sibling-session findings were carried over.

## 2. Executive summary

**No developer-intended in-game cheat system (password, button code, or unlockable debug menu)
was found in this GBA image, and the bounded negative below is quantitative rather than
"not found by eye."**

* Web recon recovered the published code set: five 10-press button sequences with the fixed
  prefix `START,START,Y,START,START,Y` and four-press action suffixes, all for **non-GBA**
  platforms. GBA-only cheat pages list **five Action Replay codes only** (out of scope).
* The GBA text bank (245 decoded records, `0x7AE9E8`–`0x7B7FF8`) contains **zero** strings for
  password, cheat, code, secret, unlock, debug, invalid or correct. UI text is ASCII in
  `{u16 len, u16 1, NUL-padded string}` records (button-icon glyph bytes `0x83/0x85/0x8B`),
  so a "no string hit" cannot be blamed on an undecoded font bank. The only debug-ish string
  is `LEVEL SELECT` (`0x7B799C`), plus `Press Select To Exit` (`0x7B7A8C`) — see §8.
* The game's key-input layer was fully decoded (addresses below). A scan of all **135** call
  sites of the edge-triggered key reader found only menu/pause/options navigation; the
  63 clusters have at most 7 calls in any one function, and every examined cluster is a
  cursor handler.
* A structural scan for any button-mask table (u8/u16/u32, active-high **and** active-low,
  plus button-index encodings) returned **39** candidate 10-word runs, **all** of which lie
  in ADPCM/audio sample regions (`0x1CE3EE`, `0x1D055C`, `0x1D53F4`, `0x74C…`, `0x74D…`);
  **0** candidates in executable code. The published suffix `Up,Down,Left,Right` occurs
  **0** times in the ROM as masks or indices in any width.
* Dynamic testing: all reachable screens were walked with screenshots and RAM evidence
  (§7). Six prefix-mapped published codes were entered in gameplay and six common debug
  combos at the menu; none changed state (savestate RAM diffs). The Start-based console
  prefix additionally opens the GBA pause menu, which prevents that syntax being used
  during play on this SKU.

This is a **bounded negative**: the space searched is enumerated with counts in §6b.

## 3. How to reproduce

Emulator: mGBA 0.10.5 under Xvfb `:318`, `SDL_AUDIODRIVER=dummy`, `-3` scale.
Keymap (mGBA SDL default): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`,
D-pad=arrow keys. Hold keys 100–150 ms; menus debounce.

Screen path actually walked:

1. Language select (`English / Français / Deutsch`) — A to accept.
2. © 2004 Krome Studios legal screen — A/Start.
3. Title screen — Start.
4. Main menu — **NEW GAME**, **OPTIONS** only (2 items).
5. NEW GAME → "Select a save game file" (GAME 1/2/3, ERASE).
6. Intro cutscene → in-game (Currawong).
7. In-game → Start → PAUSED: `CONTINUE`, `EXIT GAME`.
8. Main menu → OPTIONS → Music, Sound, Display (`GBA SP`), Language, Credits.
9. OPTIONS → Credits (scrolling staff roll).

Reproduction of the key findings:

* `strings -t x -n 4 ROM | grep -iE 'password|cheat|debug|code'` → only asset paths
  (`...font...`, `...boss...`), no UI cheat strings.
* Text-bank decoder (Python, in work dir `scan3.py`/inline): parse every 4-byte-aligned
  `{u16 len, u16 1}` at file `0x7A0000`–`0x7B8000`, require printable ASCII + NUL terminator
  → 245 records; term counts in §2.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`
  over `0x080ADF00`–`0x080AE040` shows the key layer (§4).
* mGBA CLI debugger (`mgba -d`) with a write watchpoint:
  `watch/w 0x020047cc` → `continue` → press Down →
  `Hit watchpoint 1 at 0x020047CC: (new value = 0x00000001, old value = 0x00000000)`,
  PC `0x080067EA`, LR `0x080B6BD7`.
* Savestates: `Shift+F1` writes `<rom>.ss1`; states were decompressed by taking the zlib
  `gbAs` PNG chunk (`ssdiff.py`); state layout EWRAM at `0x21000`, IWRAM at `0x19000`.

## 4. Address map

| Address (ROM/file or RAM) | Meaning | Evidence |
|---|---|---|
| `0x08000000` / file `0x000000` | Stock entry `0xEA00002E`, crt0 | Observed (header hex) |
| `0x080ADF94` | `update_keys()` — copies prev→`[0x02009720]`, reads `0x04000130`, stores `~KEYINPUT` to `[0x02009722]`, then loops r4=0..9 incrementing/resetting `u32` hold counters at `0x02009730 + 4*r4` | Derived (disassembly) |
| `0x080ADF20` | `key_pressed_edge(u16 mask)` — returns 1 iff `(prev & mask)==0 && (cur & mask)!=0`; 135 BL call sites | Derived |
| `0x080ADF48` / `0x080ADF68` / `0x080ADF88` | `key_not_held`, `key_held`, `get_current_keys` | Derived |
| `0x02009720` (u16) | previous key state; `0x02009722` current, active-high | Observed (`0xFC00` at idle = `~0x03FF`) |
| `0x02009730` | `u32[10]` per-button hold counters | Derived |
| `0x020047C0` | main-menu struct base (r4 in handler) | Observed (watchpoint registers) |
| `0x020047C4` (`+4`) | screen-state word; `=2` at main menu | Observed |
| `0x020047CC` (`+0xC`) | menu cursor (i8). Two items: value alternates 0/1 | Observed (watchpoint + 6 Down presses) |
| `0x080067C8` | main-menu input handler; Down=`0x80`, Up=`0x40`, A=`1`, B=`2` via `0x080ADF20`; plays sound IDs `0x37`, `0x35`, `0x6A` | Derived |
| `0x08006680`–`0x08006694` | builds menu item descriptors from a pointer table (120-byte records) | Derived |
| `0x080B2A0C`, `0x080B2A00`, `0x080B2A18` | menu-list copy/compare helpers | Derived |
| `0x080B540C` | sound play (`r0`=sound id, `r1`=100, `r2`=8) | Derived |
| `0x7AE9E8`–`0x7B7FF8` (file) | ASCII text bank, 245 records `{u16 len, u16 1, text, NUL pad}` | Observed |
| `0x7AE9EC` (file) | `Build: 040817-133b` | Observed |
| `0x7B799C` (file) | `LEVEL SELECT` text record | Observed |
| `0x7B7A8C` (file) | `Press Select To Exit` text record | Observed |

File offset → ROM address: `0x08000000 + file_offset`.

## 5. Algorithm

There is no password/serial validator in this image. The only reverse-engineered algorithm
is the input path, precise enough to reimplement:

```
update_keys():
    prev = cur                         # [0x02009720] <- [0x02009722]
    cur  = ~KEYINPUT & 0xFFFF          # 0x04000130, active-high
    for b in 0..9:                     # 0x02009730[b]
        hold[b] = hold[b]+1 if (prev & (1<<b)) else 0

key_pressed_edge(mask): return (prev & mask)==0 and (cur & mask)!=0
key_held(mask):         return (prev & mask)!=0 and (cur & mask)!=0
```

Button mask values (active-high): A=`0x001`, B=`0x002`, Select=`0x004`, Start=`0x008`,
Right=`0x010`, Left=`0x020`, Up=`0x040`, Down=`0x080`, R=`0x100`, L=`0x200` (confirmed by
the menu code testing `0x80` for Down and `0x40` for Up at `0x080067CE`/`0x08006824`).

Published code format (non-GBA SKUs only, for reference): 10 presses =
`[Start,Start,Y,Start,Start,Y] + [action×4]`, with a confirmation sound on success.

## 6. Tables

**Text-bank records (decoded, 245 total).** Term counts over all 245 decoded strings:

| Term | Records |
|---|---:|
| password / cheat / code / secret / unlock / invalid / correct / master / konami / debug | 0 each |
| level select | 1 (`0x7B799C`) |
| enter | 2 (both are the name "**Lindsay Parmenter**", i.e. substring `…ent…` — no entry prompt) |
| rang | 32 (item descriptions) |

**Menu enumeration (observed).**

| Screen | Items / fields | RAM evidence |
|---|---|---|
| Main menu | 2: NEW GAME, OPTIONS | cursor `0x020047CC` ∈ {0,1}; state `0x020047C4 = 2` |
| New Game | 3 slots (GAME 1/2/3) + ERASE | screenshots `newgame1.png` |
| Pause | 2: CONTINUE, EXIT GAME | `code_A.png`, `code_R.png` |
| Options | 5: Music, Sound, Display, Language, Credits | `options.png` |
| New Game slot file | per-slot % + NEW/ERASE | `newgame1.png` |

**Published codes (web recon — NOT in this ROM).** Five prefixes `S,S,Y,S,S,Y`, suffixes:
`X,A,X,A` (100,000 Opals); `B,X,B,A` (all Bunyip Keys); `X,B,X,B` (level-1 rangs);
`B,X,B,Y` (Sly's rangs); `Up,Down,Left,Right` (show all collectibles). PS2 substitutes
Triangle for Y, Xbox uses B/A/X/Y variants, PC/NS remap further. **GBA: 0 in-game codes
published; 5 Action Replay codes (excluded by scope).**

## 6b. Enumeration

**Code-space size for this SKU = 0.** There is no password surface, no code table, and no
reachable debug menu, so no novel code can be minted. This section gives the counts that
bound that negative instead.

1. **Input surface** — every reachable screen walked (§3/§6): 9 distinct screens. No screen
   offers a text or symbol entry field. Cursor domain of the only menu with hidden-looking
   strings proven to be 2 by writing Down ×1..×6 and reading `0x020047CC` → alternating
   0/1; a write watchpoint named the sole writer (`0x080067E8`).
2. **Text space** — 245 text records decoded from the bank; 0 matches for password/cheat/
   code/secret/unlock/debug/invalid/correct; 1 `LEVEL SELECT`. The font bank was decoded
   (ASCII + custom icon glyph bytes), so this is a search over actual displayed text, not
   a failed `strings` heuristic.
3. **Button-mask table space** — scanned all `8,388,608` bytes for 10 consecutive values
   drawn from the 10 valid GBA masks (and their active-low complements) in u8, u16 and u32;
   39 candidates, **all** in audio/sample data, **0** in code. The distinctive published
   direction suffix `Up,Down,Left,Right` has **0** occurrences as masks under any width and
   **0** as button indices (0-based or 1-based) in code. No algorithmic validator was found
   among the **135** BL sites to `key_pressed_edge` (63 clusters; largest 7 calls, all menu
   navigation). Conversely, the console fixed-prefix dispatcher model would require either
   a 10-entry mask table or ≥10 key reads in one handler; neither exists.
4. **Dynamic rejection bounds** — 6 direct prefix mappings of the published console code
   (`Y → A, B, L, R, Select, Start`; fast 50 ms taps) were entered in gameplay with a
   savestate before each: all produced only the GBA pause menu when Start was used and no
   RAM effect otherwise; EWRAM diff counts were homogeneous (10,484–10,539 bytes of
   ordinary gameplay drift across all six, IWRAM 1,166–1,205). 6 further debug combos
   (`L,R,L,R,U,D,L,R`; Konami; `Start,L,R,A,B,Select`; `A,A,B,A,A,B,U,D,L,R`; `L,R,Start`;
   `U,D,U,D,L,R,L,R,L,R`) were entered at the menu: no new screen.
5. **Novel code** — not applicable: no code system exists to mint from. Per §0.2 a bounded
   negative is reported instead, with the searched space and counts above.

## 7. Validation evidence

* **Observed** — ROM hash/header/entry word; all 9 screenshots; menu cursor value and its
  write watchpoint (PC `0x080067EA`); key globals `0x02009720 = 0xFC00` with KEYINPUT
  `0x03FF`; 6 prefix-code attempts and 6 menu combos; savestate diffs; text-bank record
  decode; 39 mask candidates; 135 key-press call sites.
* **Derived** — key-update/edge/held algorithms from Thumb disassembly at `0x080ADF00`…
  `0x080AE040`; menu handler structure at `0x080067C8`; file↔ROM offset mapping.
* **Inferred** — that `LEVEL SELECT` text is a leftover/gated feature (string present, no
  UI route found); that the Start-based console prefix is incompatible with the GBA pause
  handler. Neither is claimed as proven.

## 8. Unknowns

* `LEVEL SELECT` (`0x7B799C`) and `Press Select To Exit` (`0x7B7A8C`) exist in the text bank
  but no reachable path to that screen was found. Whether they are dead text, a
  completion-gated unlock requiring a full clear, or a code-gated debug screen was **not**
  proven. Setting the main menu state word `0x020047C4` to 0..48 never produced it
  (49 states captured). 32-bit pointers to the records were absent; a text-ID/bank-base
  reference was not conclusively identified. This is explicitly an open question, not a
  negative claim.
* Audio confirmation for prototype button sequences could not be assessed (`SDL_AUDIODRIVER=dummy`).
* The SRAM save layout (only bytes `0x1988–0x198B`, `0x1A03`, `0x1A05` non-erased after a
  new game) was not fully decoded; a save-bit unlock of level select therefore cannot be
  excluded.
* No full-game completion test was performed (would be needed to test a clear-flag gate).

## 9. Tooling

Scripts in `/tmp/opencode/ty2/` (analysis artifacts, not distributed with the ROM):
`key.py` (xdotool input), `scan_masks.py`, `scan2.py`, `scan3.py`, `scan_table.py`,
`scan_masksets.py` (mask/table scans), `scan_bl.py`, `triage_calls.py` (BL/xref scans),
`scan_keyinput.py` (KEYINPUT literal scan), `ssdiff.py` (mGBA `gbAs` PNG-chunk state
extractor/differ), `ptydbg.py` + `dbgserver.py` (PTY-driven mGBA CLI debugger),
`menutrack.py`, `statescan.py` (RAM/state enumeration), `trycodes.py`, `trycombos.py`.

Tools: mGBA 0.10.5 (`-d` CLI debugger, `-t` savestates), Xvfb + openbox, xdotool, scrot,
ImageMagick, `arm-none-eabi-objdump -M force-thumb`, Python 3 + struct/zlib.
`mgba --help`, `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings`.

No ROM, graphics, music or other copyrighted assets are reproduced in this report; only
hashes, addresses, algorithms and counts are published.
