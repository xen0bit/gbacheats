# The Tower SP (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `The Tower SP.gba` (US / BTRE) |
| Size | 8,388,608 bytes (0x00800000) |
| Header title | `THE TOWER SP` |
| Game code / maker | `BTRE` / `8P` |
| Version / complement / checksum | `0x00` / `0x47` / `0x0000` |
| Entry word | `0xEA00002E` (stock crt0 branch — **not** a scene cracktro) |
| MD5 | `8e825b6048a72649a9b672858bfc388c` |
| SHA-1 | `5e338f55b4d2604f381165cc693e4d774c82aedb` |
| SHA-256 | `5bbd6bf8c34aa40534cd7cf9b08110fd180fdf700c44b2f2d565705d2213c469` |

Build strings (all **Observed** in ROM bytes): `Ver2005-12-02` at file `0x1C0`,
`THE TOWER Ver042501` at `0xD5C84`, `THE TOWER Ver050701` at `0xE72C4`.
These are exactly the US offsets listed on TCRF, so the image is the US Rev.00 build.
`file(1)` agrees: `Game Boy Advance ROM image: "THE TOWER SP" (BTRE8P, Rev.00)`.

## 2. Executive summary

**No developer-intended cheat system exists in this ROM.** There is no password
screen, no code-entry field, no button-code table, no hidden/debug menu reachable
by controller input, and no published in-game code list for this SKU. The game is
a management simulation; its only "unlockable" (the *Commercial Building*
scenario) is ordinary progress state in the battery save, reached by achieving a
TOWER rating, not a cheat. Word of mouth about "secret" content reduces to
(a) a movie-genre string `Secret Spy` at `0x0E7EEC` and (b) leftover debug text and
data that have no reachable input path.

The negative is **bounded, not assumed**: every reachable screen was walked in
mGBA with screenshots; the full 8 MiB was searched for code-system keywords in
four encodings (0 applicable hits); no password alphabet exists; a raw scan for
button-mask sequences found 782 plausible windows, all inside text/audio data
with no code xref; and the debug-only scenario/item data was located and traced
to a gate (scenario ID 10 / unused text records) that no retail menu path writes.
See §6b for the counts and the enumeration proof.

## 3. How to reproduce

* Emulator: mGBA 0.10.5, `DISPLAY=:318 SDL_AUDIODRIVER=dummy mgba -3 <rom>`.
  mGBA SDL keymap used: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
  Select=`BackSpace`, D-pad = arrow keys. Input verified live (cursor moves,
  menus open). Note: do **not** attach a GDB client and then exit it without
  `continue` — mGBA pauses the core on attach and it stays paused.
* Boot path: title → Start → intro slideshow (Start skips) → Yama dialogue
  (A = `x`) → CEO Room lecture (Start → "Leave Yama's lecture?" → Yes) →
  main game. A save can be made from Start → Sys. Menu → Save; after a save
  exists the title menu offers `Start a new game` / `Continue a saved game`.
* No code was entered because no code entry surface exists. Button combos
  tested on the title screen: `L+R`, `L+R+Select`, `L+R+Start`,
  `Start+Select`, `B,B,B,B`, D-pad `Up,Up,Down,Down` and
  `Left,Right,Left,Right`, and a Konami-style
  `Up,Up,Down,Down,Left,Right,Left,Right,B,A`. None produced a new screen;
  screenshots `cb_*.png` / `codeprobe_*.png` remain on the title screen.
* Text is plain ASCII in this game (with `0x81 0xA1` decoration markers around
  menu titles), so `strings -t x` is a valid text scan; the "decode the font
  bank before a negative" precaution was still applied — see §6b.

## 4. Address map

| Address (ROM/file) | Meaning | Evidence |
|---|---|---|
| `0x08000000` / `0x000000` | Header, stock entry `0xEA00002E` | Observed |
| `0x08000778` | Input routine: reads KEYINPUT via literal `0x04000130` at `0x080007A0`, XOR `0x03FF` → active-high held `0x02000002`; pressed `0x02000004`; previous `0x02000000` | Derived (Thumb disassembly) |
| `0x0807B4D0` | Stores current state pointer into global `0x02008FC0` | Derived |
| `0x0807B5CC`, `0x0807B5FC`, `0x0807B644`, `0x0807B674`, `0x0807B69C` | Accessors that read scenario ID from `*0x02008FC0` and **special-case value 10** with a fallback table at `0x02008FC4`/`C6`/`CC` | Derived |
| `0x0807BB2C` / `0x0807BB44` | Scenario-name accessors indexing pointer table `0x0836F3FC` | Derived |
| `0x0836F3FC`–`0x0836F424` | Scenario name pointer table: indices 7=`Com Bld.`, 8=`Gen. Office Bld.`, 9=`Tutorial`, **10=`Debug Construction`**; indices 0–6 point to a data blob `0x0836F468` | Observed + Derived |
| `0x08369688` | `(This text is temporary)` | Observed |
| `0x083696A4` | `Unusable in normal mode` | Observed |
| `0x083696BC` | `Items for Debugging` | Observed |
| `0x083696D0` | `§1Debug§1` category title (0x81 0xA1 markers) | Observed |
| `0x0836B4B0` | Plain string `Debug` | Observed |
| `0x0836F428` | `Debug Construction` | Observed |
| File `0x36AC60`, `0x36ACB8` | Last two real records of the 0x58-byte item table; their final text fields include `  $100,000` and `Debug` | Observed / Derived |
| `0x08371E9E` | 12-byte-stride per-scenario byte table indexed by scenario ID (read by accessors at `0x0807B4DC`/`0x0807B510`) | Derived |
| `0x0E7EEC` | `Secret Spy` — a movie genre/item name in a list of film genres, **not** a cheat | Observed |

RAM note: the game's live state pointer is the EWRAM word `0x02008FC0`
(bytes `c0 8f 00 02` at several literal pools — easy to misread as
`0x03008FC0`). `0x02008FC4/C6/CC` hold the scenario-10 fallback values used by
the debug-scenario accessors.

## 5. Algorithm

There is no validator to reimplement. The only relevant algorithm is the shared
input sampling routine at `0x0800778`:

```
held    = (u16)(~KEYINPUT) & 0x03FF      @ 0x02000002
pressed = held & ~previous               @ 0x02000004
released= previous & ~held
previous= held                          @ 0x02000000
```

No code consumes a press *history*: the only readers of `pressed` are ordinary
per-frame UI handlers (menus, cursor, construction). No comparison against a
multi-button mask sequence, no code buffer, no checksum routine and no
encoder/decoder pair was found (§6b).

## 6. Tables

### 6.1 Keyword census (full 8 MiB, case-insensitive)

| Keyword | ASCII | lowered `0x61..0x7A → 0x41..0x5A` | UTF-16LE | UTF-16BE |
|---|---:|---:|---:|---:|
| password | 0 | 0 | 0 | 0 |
| cheat | 0 | 0 | 0 | 0 |
| code | 0 | 0 | 0 | 0 |
| unlock | 0 | 0 | 0 | 0 |
| invalid | 0 | 0 | 0 | 0 |
| secret | 1 (`0xE7EEC`) | 0 | 0 | 0 |
| debug | 4 (`0x3696C6`, `0x3696D2`, `0x36B4B0`, `0x36F428`) | 0 | 0 | 0 |

`strings -t x -n 4` produced 75,247 lines. `secret`/`debug` hits were each dumped
with ±100 bytes of context: `Secret Spy` sits between `Dirty Larry` and `009` in
a film-genre list; the four `debug` hits are the leftover text/data described in
§4. No password prompt string exists in any encoding.

### 6.2 Alphabets / font banks

No password alphabet (`ABCDEFGHIJKLMNOPQRSTUVWXYZ`, `0123456789ABC…`, etc.)
appears anywhere. Five `0123456789` hits were dumped: `0xE64BC` is a `printf`
digit table (`0123456789ABCDEF(null)`), `0x7344F8`/`0x734514` are newlib
`vfprintf` base tables, and `0xEFC74`/`0xEFD10` are font glyph-order tables
(`…ABCDEFGHIJK0123456789:; !"#$%&'()*+…`) — none is an input alphabet. This
satisfies the "decode the font/tile text bank before a negative" requirement:
the visible UI text is ASCII plus `0x81A1` decoration, and the only symbol sets
in the ROM are font/printf tables.

### 6.3 Scenario and item leftovers

* Scenario names (file `0x36F424` downward): `Debug Construction`, `Tutorial`,
  `Gen. Office Bld.`, `Com Bld.`. The debug entry is index 10 in the accessor
  table at `0x0836F3FC`; at least five accessor functions branch on `id == 10`.
  The retail mode-select screen has exactly **two** entries
  (`Start a new game`, `Continue a saved game`) and starting a new game goes
  straight into the Tutorial/General Office Building scenario.
* The text bank contains `Items for Debugging`, `Unusable in normal mode` and
  `(This text is temporary)`; each string has exactly **one** pointer, all three
  pointers living in the text-pointer table `0x083695C0`–`0x0836F8`. There are
  **zero** code xrefs to these three strings.
* Two item records at file `0x36AC60` and `0x36ACB8` end in the text `Debug`.
  Their flag dwords (`0x23FFFF02`, `0x0FFFFF02`) contain `0xFFFF` fields unlike
  the normal items (`0x05010102`, `0x14010102`) — consistent with deliberately
  disabled/unusable entries. No need to exploit them for the conclusion; they
  are reported as leftover data, not a cheat.

## 6b. Enumeration

**Result: the in-game-cheat space is empty (0 codes, 0 button sequences, 0
hidden menus).** This is a proven bounded negative, assembled from four
independent bounds:

1. **Screen enumeration (Observed).** Every reachable screen was walked in
   mGBA and screenshotted (files in `/tmp/opencode/thetower/`): boot logo
   (`screen_initial.png`), title screen day/night (`screen_title.png`,
   `title_with_save.png`), intro slideshow (`intro_*.png`), Yama dialogue
   (`dlg_after120.png`, `welcome_dialogue_end.png`), CEO Room lecture/info pages
   (`info_Start.png`, `results_A1.png`), gameplay main screen
   (`after_exit_yes2.png`, `gameplay_for_save.png`), Tool Menu and its locked
   tabs (`tool_menu_open.png`, `gameplay_R.png`, `tab_*.png`), Info screens —
   Finances / Find Tenant / CEO Room / Upgrade Info (`main_Select.png`,
   `info_item_*.png`), System Menu — exactly 4 entries `Save / Restart / Cursor
   / Title` (`system_menu.png`), save/load and new-game confirmations
   (`save_confirm.png`, `dialogue_full.png`, `newgame_prompt.png`), mode select —
   exactly 2 entries (`welcome_dialogue_end.png`). **No screen has a text-entry
   field, code pad, password prompt, or unlabelled extra menu slot.**
2. **String/encoding bound (Observed).** 8,388,608 bytes × 4 encodings searched:
   `password`, `cheat`, `code`, `unlock`, `invalid` → 0 hits in all four;
   `secret` → 1 (a film genre); `debug` → 4 (leftover text/data). 75,247 ASCII
   strings inspected. No alphabet string of length ≥ 10 exists other than
   font/`printf` tables.
3. **Button-code bound (Derived).** Raw scan of all 4,194,304 word-aligned
   offsets for 8 consecutive `u16` values in `1..0x3FF` with ≤3 bits set found
   **782** candidate windows (288 below file `0x200000`, 44 in `0x200000..0x300000`,
   450 above). Filtering for windows containing Start/Select/L/R left **326**;
   dumping them showed every one lies in text/audio data (`0xDA2D2`–`0xEB…`,
   e.g. a sine table at `0xE5CC6` and glyph indices at `0xEB594`), **none in a
   code region with a pointer/reference from executable code**. A table with no
   xref cannot be a live input matcher. Live combos in §3 produced no new screen.
4. **Debug gate bound (Derived).** The only debug-labelled content is
   (a) scenario ID 10, `Debug Construction`, and (b) two disabled item records
   plus three unreferenced debug strings. Scenario ID 10 is *read* by the
   accessor block at `0x0807B5CC`–`0x0807B6C8`; the retail path never writes it:
   the scenario ID lives at `*0x02008FC0`, and a scan of all 69 literal
   references to that global found **zero** stores of an immediate 10 to the
   ID field, and **zero** stores to the dereferenced field at all in that block.
   Combined with the two-entry mode-select and four-entry System Menu, no
   controller path reaches the debug scenario. (Guide §16.3 gate category:
   **gated feature with no reachable writer**, not "not tested".)

**Novel-code requirement:** not applicable — there is no code system to mint a
code for. Publishing a fabricated code would be false; the deliverable is the
counted negative above. **Rejection bounds:** likewise not applicable. The
closest bounded rejection evidence is that six button sequences and one
Konami-style sequence were entered on the title screen and all were rejected by
the game (no state change); and that the debug entries carry `0xFFFF` disabled
fields and a scenario ID for which no writer exists.

**Unlockables (observed, not a cheat):** the *Commercial Building* scenario
unlocks after reaching TOWER rating in the General Office Building scenario
(instruction manual p.9; corroborated by period reviews). This is progress state
in the 64 KiB battery save (save header `THE TOWER Ver050701`, 23,376 non-`0xFF`
bytes after one in-game save), i.e. guide §16.18's "save-bit unlock is not a
code".

## 7. Validation evidence

* **Observed** — ROM hashes/header/build strings; every screenshot listed in §6b;
  save file creation and its header; title-screen combo tests; keyboard input
  verified by moving the in-game cursor and opening menus.
* **Derived** — input routine at `0x0800778`; scenario-name table and ID-10
  special-casing at `0x0807B5CC`+; item-record layout; string/pointer xref
  counts; button-mask scan counts.
* **Inferred (low confidence)** — precise semantics of the `0x08371E9E`
  per-scenario byte table and of the `0xFFFF` item flag fields; the debug items
  were never rendered because they cannot be unlocked.

## 8. Unknowns

* Exact meaning of the per-scenario 12-byte table at `0x08371E9E`.
* Whether the two `Debug`-labelled item records ever render under a debug build;
  their `0xFFFF` fields look like deliberate disable markers, but no debug build
  was available.
* GameFAQs' cheat subpage returned HTTP 403 to automated fetch; search snippets,
  the official manual, TCRF and contemporary reviews exposed no in-game code
  list. If a private/print guide lists one, it is not corroborated by any string,
  table or input path in this ROM.

## 9. Tooling

`file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings -t x -n 4`, Python 3
(`struct`, `capstone`, `PIL`), `arm-none-eabi-objdump -M force-thumb`,
`gdb-multiarch` (attach attempt paused the core — abandoned), mGBA 0.10.5,
Xvfb `:318` + openbox, `xdotool` XTEST input, `scrot`, `pdftotext` (manual).
Helper: `/tmp/opencode/thetower/ui.py`. No ROM or copyrighted assets are
reproduced in this report; only hashes, addresses, counts and short labels.
