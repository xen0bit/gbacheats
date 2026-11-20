# The Urbz: Sims in the City (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `The Urbz: Sims in the City.gba` |
| Size | 33,554,432 bytes (`0x02000000`, 32 MiB) |
| Header title | `THE URBZ AGB` |
| Game code / maker | `BOCE` / `69` |
| Revision | `0x00` |
| Entry word | `0xEA00002E` → stock GBA crt0 branch to `0x080000C0` (no cracktro/trainer patch) |
| Header complement / checksum | `0x9B` / `0x0000` (rebuilt-header artifact, not a modification signal per guide §16.1) |
| MD5 | `0821eea9bf87804ec1d700ec458a04e5` |
| SHA-1 | `8efd27375d1f92b43fe0d1c93a63c08b7a259acc` |
| SHA-256 | `60ee5a1720b5a61f62fb11e501b9e4f6596478469942be88b395ae0a76bf06dd` |
| `file` identification | Game Boy Advance ROM image: "THE URBZ AGB" (BOCE69, Rev.00) |

All addresses below are for this exact image. ROM addresses = `0x08000000 + file offset` for the
first 16 MiB; addresses of the form `0x09xxxxxx` in this image are the 0x09 mirror and map to
file offset `0x01000000 + (addr - 0x09000000)`.

## 2. Executive summary

**Result: no in-game password, button-code, cheat-code entry, or hidden/debug menu was found in
this GBA SKU, and the searches that were performed were bounded and counted (§6b).** This is a
*gated/absent-system negative*, not "not tested": the title and creation screen trees were walked
with screenshots, the game text was shown to be compressed/custom-encoded (so a plain `strings`
negative would be invalid), and the input/validator surface was searched statically with exact
counts.

The one genuine debug leftover is an ASCII Sim-template name **`CheaterX`** at ROM
`0x080724A0`, copied as a 16-byte name into a Sim object at `0x08023964` (`memcpy` via
`0x0806DA4C`, length 16). It is a data-table entry, not a code, a validator, or a UI prompt.

Web reconnaissance produced no usable data: the websearch integration returned "No search
results found" for every query, and direct fetches of GameFAQs, IGN, and TCRF all returned HTTP
403. No published code could be recovered or checked; this is recorded as a limitation, not as
evidence of absence.

## 3. How to reproduce

* Emulator: mGBA 0.10.5, `mgba -3` under Xvfb `:317`, `SDL_AUDIODRIVER=dummy`, 1024×768 screen.
  Window is 720×480 at `(152,144)`; screenshots are of the whole window.
* Keymap (verified): A = `x`, B = `z`, Start = `Return`, Select = `BackSpace`, D-pad = arrow
  keys. Inputs were held 60–150 ms because shorter taps were missed.
* mGBA savestates: `Shift+F1..F5` save, `F1..F5` load. States live next to the ROM
  (`*.ss1`..`*.ss5`) and were removed at cleanup.
* Deterministic route used:
  * Language screen → A on `English` → copyright/license screens → A → "Press START" → Start.
  * Title menu (4 entries, horizontal selector): `Load-an-Urb`, `Create-an-Urb`, `Minigames`,
    `Options`.
  * `Options` → `Music Volume`, `SFX Volume`, `Language`, `Credits` (4 entries).
  * `Create-an-Urb` → `Name Your Urb` (on-screen keyboard A–Z, 0–9, `Done`) → `Create-a-Bod`
    (Gender, Skin Tone, Hair Style, Hair Color, `OK`) → `The Threads` (Shirt Style, Shirt Color,
    Sleeve Color, Overshirt Color, Pants, Shoes, `OK`) → `Questions` (personality quiz, 4 answers
    each) → `Rep Group` / `My Kizzles` (`OK`, then "Are you sure you want this Urb?" Yes/No) →
    "Behold!" transition → gameplay (conversation with NPC Kris Thistle).
  * `Load-an-Urb` was reached but no save slot was created during this engagement, so it was not
    expanded.
  * A gameplay conversation was reached and observed; the in-game pause menu was **not** reached
    (see §8).
* Diagnostic tooling: `xdotool` XTEST input; `scrot` screenshots; mGBA CLI debugger (`mgba -d`,
  driven over a pty) for `x/1` memory reads, Thumb breakpoints (`break/t`) and write watchpoints
  (`watch/w`); savestate `gbAs` chunks decompressed with `zlib` for RAM dumps/diffs.

## 4. Address map

| Address | Kind | Meaning / evidence |
|---|---|---|
| `0x080000C0` | code | Stock ARM crt0 entry |
| `0x08027AA0` | code | Custom decompression routine (entropy/LZ-style, 8-bit flag bytes, u16 code table); writes decompressed bytes |
| `0x08027B30` | code | `strb r3,[r0]` inside that decompressor — confirmed by write watchpoint on `0x02002820` |
| `0x08027E4C`, `0x08027E78` | code | Input-manager init / polling |
| `0x08027ED4` | code | KEYINPUT read: `ldr r0,[0x08027F08]` = `0x04000130`, `eors r0,#0x3FF` → active-high |
| `0x08027F08`, `0x08027F0C` | literals | `0x04000130` (KEYINPUT), `0x000003FF` (button mask) |
| `0x08023964` | code | `ldr r1,[pc]` → `0x080724A0`; `bl 0x0806DA4C` with `r2=16`: copies the `CheaterX` name |
| `0x08061B0C` | code | Text-load caller: loads compressed-bank pointer from IWRAM global, `r2=0x800`, calls `0x08027AA0` |
| `0x080724A0` | data | ASCII `CheaterX\0\0\0\0` — 16-byte Sim name field in a template/record table |
| `0x08072770` | data | 16-byte direction lookup table (used by input helper at `0x08027F60`) |
| `0x02001258` | RAM | Font lookup table: bytes `0x20..0x7F` (ASCII 0x20–0x7F → glyph index `char-0x20`); tail filled with `0x7F` |
| `0x02002820` | RAM | Decompressed text scratch buffer (2048 B). Confirmed by watchpoint and savestate: title state holds `Press START\0`, `ctronic Arts Inc.\n`, `All Rights Reserved.\0`; name-entry state holds the editable name plus `Done`. |
| `0x03004800` | RAM | Input-state base. `+0x10` held (active-high), `+0x12` previous, `+0x14` pressed (edge), `+0x16` released; 4 controller groups at `+0x10/+0x18/+0x20/+0x28`, stride 8. |
| `0x03006308` | RAM | Source u16 array for the 3 virtual controller groups |
| `0x03005ED0` | RAM/IWRAM | `URBZ0011` (build/save signature string, also present in ROM) |

Savestate raw layout (mGBA `gbAs`, 397,312 B): header/CPU `0x00000`, VRAM `0x01000`,
IWRAM `0x19000`, EWRAM `0x21000` — matches guide §16.13.

## 5. Algorithm

There is no validator to reimplement. The relevant reverse-engineered mechanisms are:

**Input model** (derived from `0x08027E78`–`0x08027EF0`):
```
raw = ldrh(0x04000130)
held  = ~raw & 0x3FF                 # active-high, A=1 B=2 Select=4 Start=8
prev  = old_held
pressed  = held  & (held ^ prev)
released = prev  & (held ^ prev)
```
Button masks are therefore `A=0x001, B=0x002, Select=0x004, Start=0x008, Right=0x010,
Left=0x020, Up=0x040, Down=0x080, R=0x100, L=0x200`. The three virtual controller groups are
read from the u16 array at `0x03006308`.

**Text model** (derived + observed):
```
ROM compressed bank --[0x08027AA0, 0x08061B0C]--> EWRAM 0x02002820 (<=0x800 bytes, ASCII)
visible glyph = font_table[ascii - 0x20]      # font table at 0x02001258
```
This is why `strings` on the ROM finds no UI text: the banks are compressed and the glyphs are
font-indexed. (Observed: all 14 tested UI strings were absent from the ROM as ASCII and as
`ascii-0x20` glyph-index bytes.)

## 6. Tables

| Item | Value |
|---|---|
| `CheaterX` | ASCII, 16-byte field at `0x080724A0`; xref `0x08023964` copies it into a Sim object. Only meaningful ASCII identifier in the ROM besides the header and `URBZ0011`. |
| Font table | `0x02001258`: `0x20 + i` for `i = 0..0x5F`, then `0x7F` padding — 96 printable glyphs. |
| Input masks | A `0x001`, B `0x002`, Select `0x004`, Start `0x008`, Right `0x010`, Left `0x020`, Up `0x040`, Down `0x080`, R `0x100`, L `0x200`. Confirmed by the KEYINPUT `eors #0x3FF` and by UI checks of `pressed & 1` (A) at e.g. `0x08015162`, `0x080158C8`, `0x08015B58`. |
| Title menu | 4 entries: Load-an-Urb, Create-an-Urb, Minigames, Options. |
| Options menu | 4 entries: Music Volume, SFX Volume, Language, Credits. |
| Name-entry alphabet | `A`–`Z`, `0`–`9`, `Done` (36 symbols + submit); name field shows 9 slots. This is a character-name field, not a password field (§16.2b). |

## 6b. Enumeration

**Space definition.** No code/password space exists in the searched surfaces. The only bounded
input surface is the 9-character name field with a 36-symbol alphabet
(`36^9 ≈ 1.01e14` spellings). Its consumer is the character-creation flow: the buffer at
`0x02002820` is copied into the Sim object and used for display; no validator, checksum,
`strcmp`/`memcmp` against a constant, or length gate was found on it. It is therefore a *label*,
not a password field (guide §16.2b). The name `CHEATERX` (a ROM debug identifier) was tested by
patching a savestate's EWRAM buffer at `0x02002820` and loading it; the displayed name did not
update from the patched scratch buffer (the game re-renders it from another copy), and no
unlock or special screen appeared. This experiment is reported as inconclusive for the *name
hook hypothesis*, not as a successful code.

**Validator model.** None found. No candidate alphabet table, checksum loop, comparison table,
or code-entry screen was identified in any walked screen.

**Novel code(s).** None generated — there is no code system to mint from. No code appears in any
published list because no published list could be retrieved (all web sources 403 / search tool
returned no results); this is explicitly a limitation.

**Bounds proven by rejection.** No rejected input was observed because no input was accepted:
there is no entry surface to submit a candidate to. The bounded negative below is the deliverable
instead.

**Bounded negative — exact search counts (all on this ROM image):**

| Search | Count | Result |
|---|---|---|
| ASCII strings, `strings -n 5` over all 33,554,432 bytes | 260,945 | Only 3 semantically meaningful hits: header `THE URBZ AGBBOCE69`, `URBZ0011`, `CheaterX`. No `password`, `cheat`, `code`, `debug`, `menu`, `invalid`, `unlock`, or `secret` string. |
| Literal UI strings tested as ASCII and as glyph indices (`ascii-0x20`) | 14 (`Press START`, `Minigames`, `Create-an-Urb`, `Load-an-Urb`, `Name Your Urb`, `All Rights Reserved`, `Electronic Arts`, `Done`, `Gender`, `Skin Tone`, `Hair Style`, `OK`, `Yes`, `No`) | 0 ASCII hits; 0 encoded hits (text banks are compressed). Negative from `strings` alone is therefore invalid and is not used. |
| PC-relative Thumb literal xrefs to input base `0x03004800` in code `0x08000000–0x08090000` | 375 | 3 sites with a simple `ldrh`+immediate-compare mask check; all three are A-button (`mask & 1`) menu/confirm handlers (`0x08015162`, `0x08015946`, `0x080159B8`). No multi-button combination gate. |
| 32-bit literal occurrences of `0x03004800` in ROM | 344 | Same input state; no separate cheat-key state word found. |
| Literal-pool values in `0x100..0x3FF` with >=2 bits set, within `0x300` bytes of an input xref | 514 | Inspected a representative sample; all fall in UI/graphics/script data (e.g. `0x0806E5BC`, `0x0806FC60` sprite/animation scripts), not a key-combination validator. |
| u16 runs of >=4 consecutive button-plausible masks (<=3 bits of `0x3FF`) in code region | 1,100 | All inspected examples are animation/tileset script data around `0x0806E5BC`–`0x0807114A` (e.g. `0x0010,0x0011,0x0012`, `0x0002,0x0003`), not press sequences. |
| ASCII alphabet-like runs (>=24 printable bytes, >=20 distinct) in code region | 30 | All are font/tile/palette arrangements (e.g. `0x08242475`, `0x08247AF9`), not password alphabets. |
| Encoded alphabet-like runs (>=28 bytes in `0x00..0x3F`, >=20 distinct) in code region | 134 | All are graphics/script tables (e.g. `0x0806DD9C`, `0x080E451D`), not password alphabets. |
| Reachable screens walked with screenshots | Title (4 options), Options (4 items), Name-entry, Create-a-Bod (5 items), The Threads (7 items), Questions (4 answers x 5), Rep Group / My Kizzles + confirmation, "Behold!" transition, gameplay dialogue (NPC Kris Thistle) | No code-entry prompt, no cheat menu, no password field, no hidden entry encountered. |

**Classification** (guide §16.3): this is **no system** on the walked surfaces, *not* dead code,
a cut feature, or a proven gated feature. The gate classification cannot be asserted because no
candidate handler/table was found at all. One minor gated/unused artifact exists: `CheaterX`
(§6, §4) is a template name with no UI path found.

## 7. Validation evidence

* **Observed** — ROM header/hashes; all screens listed in §3/§6b with screenshots saved under
  `/tmp/opencode/urbz/`; `Press START` / name text and font table read from EWRAM via savestate
  `gbAs` decompression; input masks confirmed against KEYINPUT disassembly and working menu
  navigation; write watchpoint hit at `0x08027B30` when text was decompressed; the `CheaterX`
  name copied by `0x08023964`.
* **Derived** — input-state field layout at `0x03004800`; text-decompression call path
  `0x08061B0C → 0x08027AA0`; font index mapping `ascii - 0x20`; pointer/address conversions for
  the 0x09 mirror; all search counts in §6b.
* **Inferred** — `CheaterX` is a developer test Sim template (its only use is a 16-byte name
  copy into a Sim object); `URBZ0011` is a build/save signature; the 0x09-mirror pointers in the
  Sim template table reference compressed assets. These were not exercised in-game.
* **Not observed** — the in-game pause menu; any unlockable outcome; any published code (web
  blocked).

## 8. Unknowns

* The gameplay dialogue with Kris Thistle did not advance past its second page with A, B, or
  Start (multiple hold durations tried). This blocked reaching the in-game pause menu and any
  menu reachable only during play. A future analyst should resolve this first (possible causes:
  an unlabelled choice in the lower text box, or a required world action before the dialogue
  ends) and enumerate the pause/action menus there.
* `Load-an-Urb` was not expanded (no save slot existed at test time). The `.sav` created during
  this run (65,536 B) was deleted at cleanup, so the slot state is not preserved.
* The compressed text banks were not decompressed wholesale. The custom decompressor at
  `0x08027AA0` was located but not reimplemented; consequently, a cheat-related phrase stored in
  an unloaded bank cannot be excluded. The §6b negative is therefore bounded to the searched
  encodings (ASCII, glyph-index, literal-pool, mask/alphabet tables) and the walked screens,
  exactly as stated.
* Web/public-code reconnaissance failed (search tool returned no results; GameFAQs, IGN, TCRF
  all HTTP 403). Published codes for this exact SKU remain unverified.

## 9. Tooling

* `md5sum`, `sha1sum`, `sha256sum`, `file`, `xxd`, `strings -t x`.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for all
  disassembly; Capstone 5.0.7 Python for literal/BL scans.
* Python scripts written to `/tmp/opencode/urbz/`: `helper.py` (PID-scoped XTEST input + scrot),
  `ss.py` (PNG `gbAs` zlib state parser), `patchss.py` (state patch + PNG rebuild),
  `scan_input.py`, `scan_combo.py`, `scan_masks.py` (input xrefs / mask scans), `dbg.py` (pty
  driver for mGBA's `-d` CLI debugger: `x/1`, `break/t`, `watch/w`).
* mGBA 0.10.5 CLI debugger over pty was used for the write watchpoint and memory reads; the GDB
  stub (`-g`) was tried first but its memory reads returned zeros / packet errors and one instance
  crashed, so it was abandoned in favour of the CLI debugger and savestate diffing (guide §16.13).
* No ROM or copyrighted asset is redistributed by this report.

## 10. Legal note

Findings, addresses, hashes and tool scripts are published; the ROM image and extracted game
artwork/text are not.
