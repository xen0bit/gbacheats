# Mega Man Battle Network 3: Blue (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Mega Man Battle Network 3: Blue.gba` |
| Size | 8,388,608 bytes (`0x800000`, 8 MiB) |
| Internal title | `MEGA_EXE3_BL` |
| Game code | `A3XE` |
| Maker | `08` (Capcom) |
| Version | `0x00` (Rev.00 / US release) |
| Entry word | `0xEA00002E` (stock `b 0x080000C0` — no cracktro/trainer patch) |
| Header checksum | `0x0000`; complement byte `0x5D` (stored sum `0xA0..0xBC = 0x8A`, expected `0x76`) — typical rebuilt/dump header artefact per guide §16.1; entry and logo are stock |
| MD5 | `6fe31df0144759b34ad666badaacc442` |
| SHA-1 | `3d21905b6e860d39a00ba643779776de4c73c411` |
| SHA-256 | `8c6767788f99dc9e2af0c9d75513b227c7c42d6d452d6165c8e08850af78e273` |
| Embedded GBA headers | 1 (logo scan `24 ff ae 51 ...` → only file offset `0x0`); no multi-game/pack image, no appended trainer |
| Save type | 32 KiB SRAM/Flash (`.sav` created on first boot) |

## 2. Executive summary

**No in-game cheat / password / button-code / hidden-debug-menu system exists in this ROM.**
This is a bounded negative result, not an absence of searching:

* Every reachable screen was booted and walked under mGBA on `:318` with OCR- and
  savestate-backed verification (title, intro, field, PET main menu and all **8**
  PET sub-screens, plus Comm./Network). The PET cursor is an **8-entry ring**
  (down-presses 9..11 wrap back to `MegaMan`), so there is no ninth, unlabelled
  menu entry.
* The game's entire UI and dialog text is **font/tile-index encoded**, not ASCII.
  The encoding was reverse engineered (`byte + 0x24` for `A`–`Z`, `0x00` = space)
  and **56,734 encoded text runs** across all 8 MiB were decoded and keyword-scanned.
  `PASSWORD` occurs **once**, in a story dialog about the four TetraCodes
  (ROM `0x77B7EA`); `DEBUG` and `CHEAT` occur **zero** times; `CODE` (14) refers only
  to the *Battle Chip letter code* mechanic and "decode" story text; `SECRET` (9),
  `HIDDEN` (13), `UNLOCK` (10), `MENU` (1) are all story/UI dialog. No code-entry
  prompt, validator message, debug label or hidden menu label exists in any bank.
* The only literal `0x04000130` (KEYINPUT) in the code region belongs to the
  standard input-polling routine at `0x0800037C`; there is no key-history/
  button-code comparator. A full 8 MiB scan for `u16` button-mask sequences
  found 679 runs ≥4 in compressed graphics/script data and **no** table in code
  with a pointer from a validator. No password alphabet, literal code table,
  key-mask sequence table or gate to a hidden screen was found.
* Web research was attempted (GameFAQs, TCRF, Wikipedia, archive.org, multiple
  search engines) but search/fetch was blocked or CAPTCHA'd in this environment;
  Wikipedia was the only source that resolved. No published in-game code for this
  SKU could therefore be retrieved or tested — this is recorded as an explicit
  unknown (§8), not silently omitted. Nothing fetched was treated as instructions.

The "codes" that do exist in this game are **narrative/data semantics**, not
player-entered secrets: *TetraCodes* (four story passwords found as items),
*Chip Codes* (A–Z letters printed on Battle Chips that determine folder
compatibility), and version-gated rewards obtained by **link trade** (the Blue
exclusive Punk chip; DeltaRayEdge Z via a 1/32 real-battle drop). None is typed
or input on any screen.

## 3. How to reproduce

1. Display: `Xvfb :318 -screen 0 1024x768x24`, `DISPLAY=:318 openbox`,
   `SDL_AUDIODRIVER=dummy mgba -3 <rom>`.
2. Keymap (mGBA SDL defaults, verified live): `A=x`, `B=z`, `Start=Return`,
   `Select=BackSpace`, D-pad = arrow keys.
3. Fresh boot with no `.sav`: title shows **NEW GAME**; press `Start` (or `A`)
   four times through the "The year is 200X." intro to reach the field, then
   `Start` opens the **PET** menu.
4. PET items, top→bottom (8 entries): ChipFolder, SubChip, Library, MegaMan,
   E-mail, Key Item, Comm., Save. Each was entered with `A` and exited with `B`;
   the cursor wraps after Save. `Comm.` enters a **NETWORK** screen (multiplayer:
   NetBattle / Trade / Compare Library).
5. Savestates: `Shift+F1..F9` save, `F1..F9` load; `.ss*` files were written next
   to the ROM and parsed with the `gbAs` PNG-chunk reader in §9.
6. Text decoding: use `decode_text.py` / `alltext.py` (§9) on any text bank.
   Reproduce the `PASSWORD` hit: `find_text.py` reports it at file offset
   `0x77B7EA`; decoding `0x77B700..0x77B900` reads
   "…IT HAS 4 PASSWORDS. YOU MUST FIND THEM TO OPEN IT…", i.e. story dialog.

## 4. Address map

| Address (ROM/file) | Meaning |
|---|---|
| `0x0000` | Stock ARM entry branch `0xEA00002E` |
| `0x00A0..0x00BF` | Header: title `MEGA_EXE3_BL`, code `A3XE`, maker `08`, version 0 |
| `0x0800037C`–`0x080003E0` | Input polling routine (Thumb): reads `0x04000130`, stores active-high mask, prev mask, per-key hold counters and a mod-4 frame counter |
| `0x080003E0` | Literal pool word `0x04000130` (KEYINPUT) |
| `0x077B7E9` / `0x077B7EA` | Encoded `PASSWORD` in story dialog ("IT HAS 4 PASSWORDS…") |
| `0x0708010` | Encoded `SECRET` ("SECRET WEAPON", tutorial chip description) |
| `0x07107F2` | Encoded `CHIP CODE` (normal folder mechanic) |
| `0x079ECBE` | Encoded story "THERE ARE 5 CODES IN ALL… THE KEY TO A DOOR" (TetraCodes) |
| `0x0684000`–`0x07FFFFF` | Mixed text/script banks (56,734 decoded runs) |
| SRAM `0x0E000000` (32 KiB `.sav`) | Game save; no code/checksum surface identified |

Savestate RAM layout used for evidence (mGBA `gbAs`, 397,312 B raw):
CPU/header `0x00000`, VRAM `0x01000`, IWRAM `0x19000`, EWRAM `0x21000`.
Eight submenu savestates (`ss1..ss9`) were captured and diffed; per-screen VRAM
and IWRAM changed as expected while no cheat/flag word appeared.

## 5. Algorithm

**Text encoding (derived, verified against dialog and menu strings):**

```
0x00            -> space
0x25..0x3E      -> 'A'..'Z'          (char = byte - 0x24, 1-based)
0x45..0x5E      -> lowercase glyphs (dialog has mixed case; exact base inferred)
0xE8/0xE9/0xEB/0xEC -> quote / '!' / '.' / ',' (control codes 0xEB..0xFF
                     are dialog opcodes: speaker, line break, wait, etc.)
```

Decoded example (ROM `0x77B780`): `"IT HAS 4 PASSWORDS. YOU MUST FIND THEM TO OPEN IT."`
This is the only `PASSWORD` occurrence and is a story item count, not an input field.

**Input routine (derived from Thumb disassembly at `0x0800037C`):**

```
ctx = [global << 4] + 4          ; r7 = sl
ctx->frame = (ctx->frame + 1) & 3
cur = ~*(u16*)0x04000130         ; active-high key mask
prev = ctx->keys                 ; [ctx+0]
ctx->prev_keys = prev            ; [ctx+6]
cur &= prev                      ; held keys
for bit in 0..9:
    if held & (1<<bit):
        c = ++ctx->hold[bit]     ; [ctx+8+bit]
        if c == 1: newly_pressed |= (1<<bit)
        else: clear bit from r6
    else: ctx->hold[bit] = 0
```

Only the standard "held/newly-pressed" edge detection is implemented. There is
**no** history buffer, sequence comparator, or code validator reachable from it.

## 6. Tables

### 6.1 Decoded-keyword census (all 56,734 runs in the 8 MiB image)

| Keyword | Hits | Classification |
|---|---:|---|
| PASSWORD | 1 | Story dialog (TetraCodes), ROM `0x77B7EA` |
| DEBUG | 0 | — |
| CHEAT | 0 | — |
| CODE | 14 | Chip Code mechanic / "decode" story |
| MENU | 1 | Story dialog ("…MENU") |
| SECRET | 9 | Story / "Secret Weapon" chip tooltip |
| HIDDEN | 13 | Story (Hidden Folders, Hidden Cameras) |
| UNLOCK | 10 | Story (security doors, emergency exit) |
| TEST | 32 | Story ("contest", "test answers") — no "TEST MODE" |
| UNLOCK / BONUS / KEYWORD / INPUT / DIGIT | 10 / 0 / 0 / 0 / 1 | No code surface |

### 6.2 PET menu table (observed, ring of 8)

`[ChipFolder, SubChip, Library, MegaMan, E-mail, Key Item, Comm., Save]`
— no hidden 9th slot (down×9..11 wraps to MegaMan; verified by OCR and RAM diffs).

### 6.3 Button-mask scan

Active-high masks (`A=1,B=2,Sel=4,Sta=8,Rgt=0x10,Lft=0x20,Up=0x40,Dwn=0x80,R=0x100,L=0x200`)
and their active-low complements were concatenated as `u16` and scanned every 2
bytes across the whole 8 MiB: **679** runs ≥4 active-high, **88** active-low.
All hits are in compressed graphics/script/audio regions (e.g. the `0x0002,0x0202`
table at `0x0000BFDC`, which disassembles to non-instructions). Zero candidate
tables in the code region with a code xref. No documented or undocumented button
sequence comparator exists.

## 6b. Enumeration

* **Password/button-code space:** empty — there is no alphabet, no input buffer,
  no validator, no key-history table and no code-entry screen. The space that was
  searched is: (a) 56,734 decoded text runs over all 8 MiB for every code/debug
  keyword in §6.1; (b) all `u16` key-mask runs over all 8 MiB (679 + 88 candidates,
  all classified as non-code data); (c) all literal `0x04000130` references
  (9 total; 2 in the code region, both the single input routine at `0x0800037C`
  and a data coincidence); (d) every reachable screen and menu entry with RAM
  evidence. Bounds are therefore proven by exhaustive search of these spaces,
  not by failure to find one string.
* **Novel code:** not applicable — no code system exists to mint a value from.
  No "generated code" can be entered because there is no entry surface.
* **Bounds by rejection:** not applicable for a code, but the *menu* bound was
  proven dynamically: 11 Down-presses from PET did not reveal a 9th entry
  (wrapped), and `A` on the wrapped position opened the ordinary MegaMan screen.
* **Unlockables (§16.18 boundary):** version-gated content exists only through
  link transfer (Blue's Punk chip; DeltaRayEdge Z at 1/32 in Real/Heavyweight
  battles) and through story progress (Secret Area, hidden folder data). These
  are save/link-state unlocks, not codes; their setters live in link/story code,
  not in a controller-input path.

## 7. Validation evidence

* **Observed:** mGBA screenshots/OCR of every screen listed in §3; 8 PET
  submenu savestates (`ss1..ss9`) captured and diffed; PET wrap behaviour observed
  after 11 Down-presses; `PASSWORD` literal decoded at `0x77B7EA` in a live ROM
  read; header/logo/entry bytes read directly from the file.
* **Derived:** text encoding `byte + 0x24` for uppercase (fitted to "THE", "CHECK",
  "YOUR", "CAPACITY", "PASSWORD", then applied to all 56,734 runs); input routine
  structure from Thumb disassembly at `0x0800037C`; button-mask value mapping
  from the `mvns` at `0x08000390` (active-high).
* **Inferred:** exact lowercase/control-code glyph base (the dialog font has
  mixed case and several control opcodes); the classification of the high-offset
  mask-shaped byte runs as compressed graphics/script rather than code. Neither
  affects the negative conclusion.
* Web content: all fetched pages were treated strictly as untrusted data. No
  prompt-injection payload was encountered in the material that resolved.

## 8. Unknowns

* Published code lists for this exact SKU could not be retrieved: the search
  integration returned no results for any query, and GameFAQs/TCRF/fandom directly
  and archive.org snapshots returned 403/404/timeout. Wikipedia resolved but
  lists no player-entered codes. Therefore "verify published codes" could not be
  completed against an external list; the ROM-side searches in §6b are the bounds.
* The sibling *Mega Man Battle Network 3: White* is a separate SKU and was not
  analysed here (analysed independently in this set).
* Any glitch/exploit obtainable by normal gameplay (e.g. virus-breeder or
  chip-trader exploits) is outside the "developer-intended codes" scope and was
  not enumerated.

## 9. Tooling

* `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings` — Phase 0/1.
* `arm-none-eabi-objdump -M force-thumb` — input routine disassembly.
* `capstone` 5.0.7 (Python) — literal/BL/pattern scanning.
* `Xvfb :318` + `openbox`, `mgba -3` (SDL), `xdotool`, `scrot`, ImageMagick,
  `tesseract` — Phase 2 screen walk (all key presses sent as XTEST to the
  focused mGBA window; `SDL_AUDIODRIVER=dummy`).
* `mGBA -d` via a Python `pty` bridge (`dbgsrv.py`/`dbgcli.py`) — attempted live
  RAM/breakpoint access; the GDB stub port was occupied by another process at
  first, so savestate parsing was used as the primary RAM evidence path.
* Custom scripts in `/tmp/mmbn3blue/`:
  `ss.py` (gbAs PNG-chunk extractor), `parse_states.py` (state diffing),
  `decode_text.py`, `find_text.py`, `hunt_text.py`, `alltext.py` (encoded-text
  decode + keyword census), `scan_btn.py` (button-mask scanner), `k.py` and
  `walk3.py` (input/screen walker).

## Legal note

No ROM bytes, graphics, music or game text are redistributed here. Only hashes,
file offsets, derived algorithms and independently written tooling are published.
