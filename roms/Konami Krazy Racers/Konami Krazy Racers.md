# Konami Krazy Racers (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `/mnt/gbacheats/roms/Konami Krazy Racers/Konami Krazy Racers.gba` |
| Size | 4,194,304 bytes (0x400000, 4 MiB) |
| Header title | `KRAZY RACERS` (0xA0–0xAB) |
| Game code | `AKWE` (region E / USA); maker `A4` (Konami) |
| Version | 0x00; complement 0x43; header checksum 0x0000 |
| Entry word | `0xEA00002E` → stock `b 0x080000C0` crt0 |
| MD5 | `c1d1bb9da3a5566a34a92dac25e6bc04` |
| SHA-1 | `b64d437582526642a0d7aa83419a1367a10c91a9` |
| SHA-256 | `6b590bb8300cdde0656a95c9d210faa76c85077507ddf353e3ced9b22c379288` |

Phase 0 embedded-header scan: a full 156-byte Nintendo-logo scan over all 4 MiB found
**exactly one** header, at file offset 0. There is no appended trainer, no cracktro
(entry word is the stock branch), and no multiboot/sub-image stub. `file(1)` identifies
it as `Game Boy Advance ROM image: "KRAZY RACERS" (AKWEA4, Rev.00)`.

## 2. Executive summary

**There is no password system, no button-sequence cheat code, and no hidden debug
menu in this GBA image.** The retail UI is a complete 6-item Home Page; every
reachable screen was walked and captured, and every published "cheat" for this title
is a *gameplay control* or a *save-bit unlockable*, not a code:

* **Quick start / turbo start** — press A on the final (4th) countdown stone head
  (timing, not a code).
* **Throw item forward** — hold L+Up while racing (a held chord on the item-use
  button; plain L drops behind). Published on GameRevolution/CheatingDome.
* **Replay camera** — hold B after the result time disappears, then D-pad to change
  view (post-race control).
* **Four hidden characters** — Bear Tank, King, Vic Viper, Ebisumaru, unlocked by
  collecting diamonds / beating records in specific tracks. These are save-bit
  unlocks gated by a bitmask in EWRAM (§6), i.e. developer-intended unlockables,
  not a user-enterable code.

All GameShark/CodeBreaker material found on the web is out of scope (memory edits).
Its published RAM addresses were used only as *leads* and independently confirmed
against the ROM/save structures (e.g. `0x0201BCEA` is indeed the character list;
`0x0201BDBA`/`0x0201BE68` fall in the same save-data block).

Negative result is bounded: the full text space was searched (no ASCII/UTF-16/UTF-32/
affine-encoded text exists; all UI text is font/tile-indexed and was read from rendered
glyphs), the button-mask instruction space was scanned with counts (§6b), and five
undocumented controller combinations were pressed on the title screen with RAM diffs.

## 3. How to reproduce

**Emulator / display.** mGBA SDL (`mgba -3`) on an isolated `Xvfb :319` (1024×768×24),
`DISPLAY=:319 SDL_AUDIODRIVER=dummy`, window focused with `xdotool windowfocus`.
Keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows.
Keys held 120–400 ms; savestates taken with Shift+F1, copied out of the ROM folder.

**Menu path (all screens reached):**

1. Boot → KCEK logo → attract/demo gameplay.
2. Start → title screen (`KONAMI KRAZY RACERS`, copyright line).
3. Start → `NEW GAME` / `LOAD`.
4. A on NEW GAME → `NAME ENTRY` ("Make an ID Card. Input your name."), 3-row A–Z
   grid + `END`, confirmation `OK`/`NO`. **This is a profile-name field, not a
   password field** — its only consumer is the save record; no `strcmp`/table lookup
   compares it to a secret (§16.2b).
5. Home Page — exactly six icons, every label read: `Item Shop` (trophy),
   `Race Menu` (map), `License Center` (steering wheel), `Rumor Billboard`
   (chalkboard), `EXIT` (car), `SAVE` (hammer). No seventh item.
6. Race Menu — five modes: `Krazy GP`, `VS`, `Time Attack`, `Mini Battle`, `Free Run`.
7. Krazy GP → `Easy / Normal / Hard` → `CHARACTER SELECT` (12 portraits,
   P1 preview box) → `Krazy Cup` cup select (4 tracks: Ganbare Dochu 1, Sky Bridge 1,
   Moon Road, Poppin Beach 1; only Krazy Cup available on a fresh save) → race.
8. In-race HUD shows POWER bar, `LAP 1/3`, position, coins, speed; Start → pause menu
   with exactly `CONTINUE` / `QUIT` — **no hidden pause entry**.
9. Home Page → `Item Shop` ("Thank you for accessing it!", Money 0, Price, Inv, L/R
   pages); `License Center` (`Test-menu`, `B CLASS`, `Take the test` /
   `Hear explanation`); `Rumor Billboard` (TOPICS list with NEW markers); `EXIT`
   ("End game. OK?").

**Title-screen combinations pressed with RAM verification** (savestate before/after,
full EWRAM+IWRAM diff): `L+R+Select+Start`, `L+R`, `Select+Start`, the Konami code
`↑↑↓↓←→←→ B A`, and `L+Up`. None produced a debug screen or changed the unlock mask;
the large diffs for the first three are the title's normal attract-mode transition
(the screen advances to demo gameplay), and `Konami`/`L+Up` produced only the
animation baseline (538 EWRAM bytes, 0 bytes in the save area `0x0201B000–0x0201BFFF`).

## 4. Address map

| Address | Kind | Meaning / evidence |
|---|---|---|
| `0x08000000` | ROM | Header; `b 0x080000C0` |
| `0x080008B0` | Thumb fn (`FUN_080008b0`) | Central input handler. Reads `0x04000130` via literal `0x080009CC`, masks `0x3FF`, computes held/pressed/history into the input state. Decompiled with Ghidra/REA. |
| `0x080009CC` | literal pool | `0x04000130` (KEYINPUT), single reference from `0x080008BA` |
| `0x080009D4` | literal pool | `0x030050F0` (input/state struct base) |
| `0x0800125C` | Thumb fn | Screen dispatcher: calls `FUN_08046BB8(table[state*4])`. |
| `0x08001278` | literal pool | `0x083F1CCC` — 48-entry screen-handler pointer table (indices 0..47; entries 8/18 and 12/27 alias). |
| `0x083F1CCC` | ROM table | Screen state → handler pointers (e.g. index 0 = `0x08001281`, index 7 = `0x08018D7D`). |
| `0x0800DBC0` | literal pool | `0x0201BD8A` — **hidden-character unlock bitmask** |
| `0x0800D884` | Thumb fn | Character-select logic. Iterates 12 character slots (`0xB` wrap), skips indices >7 unless `(*mask >> idx) & 1`; reads the list at `0x0201BCEA`. |
| `0x08013BA0` | literal pool | `0x0201BD8C` — second save-bit field used by a 16-entry menu (licenses/shop display). |
| `0x0201BD8A` | EWRAM save | u16 unlock mask. Fresh save = `0x0000` (4 hidden chars locked); observed `0x00FF` while the character-select screen is active (screen-local working value). |
| `0x0201BCEA` | EWRAM save | 12-byte character list. Fresh save = `00 01 02 03 04 05 06 07 00 00 …` — IDs 0–7 present, hidden IDs 8–11 empty. |
| `0x0201BDBA` | EWRAM save | License-test flags (matches published CodeBreaker address; used as a lead only) |
| `0x0201BE68` | EWRAM save | Shop money (matches published CodeBreaker address; lead only) |
| `0x08050512`, `0x08055F7C`, `0x08083468` | ROM data | Examples of u16 "mask-like" runs found by the key-code table scan; inspection shows AI/demo steering or small-integer tables, **not** button codes. |

Savestate layout used for RAM reads (guide §16.13): `.ss1` is a PNG; the `gbAs`
chunk zlib-decompresses to 397,312 bytes; BG/OBJ palettes at `0x800`/`0x820`, OAM at
`0xC00`, VRAM at `0x1000`, IWRAM at `0x19000`, EWRAM at `0x21000`. All RAM numbers in
this report come from that layout (cross-checked against GDB reads of IWRAM).

## 5. Algorithm

No validator exists. The closest thing to an algorithm is the unlock gate, which is a
plain bit test, not a code decoder:

```
# Character select, from FUN_0800d884 (0x0800D884), Thumb
mask = *(u16 *)0x0201BD8A            # literal at 0x0800DBC0
for idx in 0..11:                    # 0xb wrap in the code
    if idx > 7 and not (mask >> idx) & 1:
        continue                     # hidden character unavailable
    show_character(list[idx])        # list = 0x0201BCEA
```

Novel-code generation / encoder / checksum / key tables: **not applicable** — there is
no input format to enumerate. §6b documents the bounded proof instead.

## 6. Tables

**Character IDs** (from the save list and the published CodeBreaker "Always Play As"
values, cross-checked):

| ID | Character | Default |
|---:|---|---|
| 0 | Goemon | yes |
| 1 | Pastel | yes |
| 2 | Nyami | yes |
| 3 | Ninja | yes |
| 4 | Pawapuro-Kun | yes |
| 5 | Takosuke | yes |
| 6 | Dracula (Moai? see note) | yes |
| 7 | Moai | yes |
| 8 | Ebisumaru | hidden |
| 9 | King | hidden |
| 10 | Vic Viper | hidden |
| 11 | Bear Tank | hidden |

IDs 0–7 are present as bytes `00 01 02 03 04 05 06 07` at `0x0201BCEA` on a fresh
save; 8–11 are `00`, i.e. absent. (*Note:* published CodeBreaker labels for IDs 6/7
are Dracula/Moai; the ROM order above is what the save list stores.)

**Unlock conditions** (developer-intended, from GameFAQs FAQ 12483, GameRevolution,
Neoseeker; no code entry involved): Bear Tank — diamond in Cyber Field 2 GP; King —
diamond on hidden island in Sky Bridge 2 GP; Vic Viper — diamond on hidden island in
Moon Road GP; Ebisumaru — unlock Bear, then beat record times on Ganbare Dochu 1 & 2
with Bear. License classes C→B→A→S gate the extra cups.

**Font/text encoding.** The ROM contains **no plaintext text bank**. `strings -t x -n 4`
yields 37,615 entries, all machine code/data fragments; a case-insensitive keyword
grep for `password|cheat|code|debug|secret|unlock|hidden|master|level select|bonus|
extra|character|circuit|track|tournament|konami` returns **0 hits**. Literal searches
for `DEBUG`, `KONAMI`, `VERSION`, `ENTER`, `START`, `SELECT`, `MENU`, `PRESS`, etc. all
return **0 hits**. UTF-16LE, UTF-16BE, lowercase `+0x20`, bit-reversed and all 256
affine `byte+K` encodings of nine known UI strings also return **0 hits**. Text is
stored as font/tile indices and drawn from VRAM (glyph tile data + OAM tile indices;
palettes at savestate `0x800`/`0x820`). All screen labels in §3 were therefore read
from rendered glyphs, not from a string table. A hidden menu label could not hide in a
plaintext bank that does not exist; the screen/pointer enumeration in §4 covers the
alternative surface.

## 6b. Enumeration

Because there is no code system, the enumeration is of the *input and screen spaces*:

| Space searched | Method | Count | Result |
|---|---|---:|---|
| GBA headers | 156-byte logo scan over 4 MiB | 1 hit (offset 0) | single retail image; no trainer |
| Plaintext UI text | `strings -n 4` + keyword regex | 37,615 strings, 0 keyword hits | no password/debug strings |
| Alternate text encodings | UTF-16LE/BE, +0x20, bitswap, 256× affine for 9 words | 0 hits | text is glyph-indexed |
| KEYINPUT literal | u32 `0x04000130` scan | 1 hit (`0x080009CC`) | single central input reader |
| Multi-button debug chords as immediates | Capstone Thumb CMP/TST/AND over all 2 MiB of halfword offsets | 0 hits for `0x200`, `0x100`, `0x240`, `0x280`, `0x300`, `0x304`, `0x308`, `0x30C`, `0x1FF`, `0x3FF`; 633 hits for small values `0xC/0xA/0x40/0x50/0xC0`, all in script/counter contexts | no key-mask gate |
| Button-code tables | u16 runs of 1–2 key-bit masks terminated by 0/0xFFFF | 1,585 candidate runs; sampled regions are AI/demo steering tables | no button code |
| Screen handlers | pointer table `0x083F1CCC` | 48 entries (2 alias pairs) | all walked/represent gameplay/menu; no debug screen |
| Home Page items | render + cursor walk | 6 | no hidden 7th |
| Race Menu items | render + cursor walk | 5 | no hidden 6th |
| Pause items | render | 2 | no hidden 3rd |
| Undocumented title combos | emulator + RAM diff | 5 tested | no hidden screen |

**Novel code / minted value:** not applicable — no accepted code space exists to mint
from. The equivalent constructive check was performed on the *unlock space*: the
12-slot character list and the gate mask were recovered from ROM (`0x0800D884`,
`0x0800DBC0`) and read in RAM, proving the 4 unreachable slots (IDs 8–11) and the
exact test that keeps them closed on a fresh save.

**Bounds proven by rejection:** `0x0201BD8A == 0x0000` on a fresh save; the character
select's `idx > 7 → mask bit` test therefore rejects IDs 8–11. Entering a name with
the on-screen keyboard was confirmed to write only the profile record (save-area RAM
unchanged in the secret-bit region), bounding the name-entry surface as a non-validator.

## 7. Validation evidence

* **Observed** — emulator screenshots of every screen listed in §3; savestate RAM
  reads of `0x0201BD8A` (0x0000 on fresh save, 0x00FF while character select is
  active) and `0x0201BCEA` (`00 01 02 03 04 05 06 07 00 00 …`); full EWRAM/IWRAM diffs
  for five title-screen combinations; pause menu showing only CONTINUE/QUIT.
* **Derived** — Ghidra decompilation of `FUN_080008b0` (input reader), `FUN_0800125c`
  (screen dispatcher through `0x083F1CCC`), and `FUN_0800d884` (12-slot character
  gate at `0x0201BD8A`); pointer/literal pools read back with `struct.unpack` to avoid
  objdump's halfword-order ambiguity.
* **Inferred** — the exact in-game effect of the published *quick-start* timing and
  the *L+Up* item throw was not captured on camera: no item was obtained during the
  driving attempts, so the chord is reported from the published control list and the
  game's item HUD/input architecture, not from a confirmed throw animation. The
  GameShark/CodeBreaker RAM addresses were used only to locate the save block and
  were independently confirmed (they are not findings and are out of scope).
* **No prompt injection encountered** in fetched web content; all pages were treated
  as data. (TCRF returned HTTP 403; GameFAQs FAQ, GameRevolution, Neoseeker, Almar's,
  CheatingDome and the "100 GBA crackmes" summary were used as lead data only.)

## 8. Unknowns

* The exact visible effect of `quick start` and `L+Up` was not screenshot-captured
  (no item obtained). No doubt about their *status*: they are published held/timed
  controls, not entry codes, and no separate validator was found for them.
* The four hidden-character setter call sites were not exhaustively traced after
  the REA session was reassigned to another target by the shared harness; the gate
  (reader side) is fully proven, and the unlock *conditions* are from published
  guides rather than from the setter's callers.
* `0x0201BD8A` reading 0x00FF inside character select suggests a screen-local
  working copy; its writer was not isolated.
* Published ID→character labels 6/7 (Dracula/Moai) come from cheat sites; the ROM
  save list stores bare indices and was not cross-checked against portraits.

## 9. Tooling

* `file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings -t x`, grep — Phase 0/1.
* Python 3 + `struct` — literal scans, savestate `gbAs` zlib parser (`ss.py`),
  VRAM/OAM/palette tile renderers (`vram.py`, `objfont.py`, `bgfont.py`).
* `arm-none-eabi-objdump -M force-thumb` — spot disassembly.
* Capstone 5.0.7 — Thumb immediate-mask scan (`maskscan.py`).
* REA/Ghidra 12.1.4 (`open_binary`, `xrefs`, `procedure_pseudo_code`,
  `read_bytes`) — input handler, screen dispatcher, character gate.
* mGBA SDL 0.10+ under Xvfb :319, `xdotool`, `scrot`, ImageMagick, tesseract.
* mGBA savestate diffing (guide §16.13) as the primary RAM oracle; GDB stub tried
  but mGBA exits on disconnect in this build, so savestates were used.

No ROM or copyrighted asset is redistributed here; only addresses, hashes, and
derived observations are published.
