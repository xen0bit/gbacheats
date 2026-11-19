# Scooby-Doo! Unmasked (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Scooby-Doo! Unmasked.gba` |
| Size | 8,388,608 bytes (0x800000) |
| Header title | `SCOOBYUN` |
| Game code | `B25E` (`B25E78`, Rev. 00) |
| Maker | `78` |
| Version | 0 |
| `file` ID | `Game Boy Advance ROM image: "SCOOBYUN" (B25E78, Rev.00)` |
| Build tag on legal screen | `(s05)` |
| MD5 | `803ff345f4df60a7f00db44fd25730bc` |
| SHA-1 | `6851a6088cccafcd8f1e49a31546aac6b27ca076` |
| SHA-256 | `841cfc2e5bd6ba402f3e17a379c670a616361bf2df1288361fbbb6a4a45199eb` |

### Phase 0 / header scan

* Entry word `0xEA00002E` = stock ARM `b 0xC0` — **not** a cracktro-patched entry.
* Header checksum stored `0x0000` (computed over `0xA0..0xBC` = `0x65`), complement byte stored
  `0x82` (expected `0x9A`). Header has been rebuilt/edited (scene-release style), §16.1.
* The 156-byte logo at header `0x04` is **not** the standard Nintendo logo (only the first
  4 bytes `24 FF AE 51` match). A scan for the real 16-byte prefix
  `24 ff ae 51 69 a7 56 2e 08 39 42 39 5b 3d 52 04` found **zero** hits.
* Exactly **one** GBA header/logo (`24 ff ae 51`) in the whole 8 MiB image, at `0x0`.
  No concatenated second image, no appended trainer header. No patch/trainer observed.

## 2. Executive summary

The game has a **checksum-validated 8-symbol progress-password system** on its main-menu
`PASSWORD` screen and in the in-game pause menu. The on-screen keyboard is a 3×11 grid of
**32 distinct symbols** — `BCDFGHJKLMNPQRSTVWXZ0123456789!?` — so a code is 8×5 = **40 bits**,
giving `32^8 = 2^40 = 1,099,511,627,776` representable strings.

**None** of the 97 collected published password literals (GameFAQs, supercheats,
cheatingdome, GameGenie, jeuxvideo) occurs anywhere in the ROM as ASCII — the accepted set is
computed by an algorithm, not a lookup table. A published code (`LJL7FW?R`, "Level 1
Complete") was entered on the real screen and **accepted** (game started with 1 clue found,
observed in emulator and in savestate). A non-published input (`BCDFGHJK`) was **rejected**
(all eight entered glyphs turned red). Mutating the last symbol of a valid code over all 32
symbols produced exactly one accepted value (the original `R`), proving the final symbol is
checksum-constrained. Mutating the first symbol to `B` and sweeping all 32 final symbols
produced **zero** accepted codes, proving the check is not confined to a single final symbol.

A **hidden developer scene-select** was found statically: the scene-name bank at ROM
`0x080428EC` lists `Fx Player`, `Music Player`, `Obj Viewer`, `MultiBoot Test`, `Asset
Viewer`, `Password`, `Title Screen`, `Normal Boot`, 18 `Episode`/`Hub`/`Splash`/`Cutscene`
scenes, `Food Puzzle 01..03`, `Trap 01..03`, `Ride 01..03`, `Boss 01..04`. Its dispatch is
gated by a byte at RAM `0x02014AC4`, read at ROM `0x0804F10`, which is `0x00` in every
captured savestate; the only literal xrefs to it (`0x08004F44`, `0x080122EC`, `0x0803CBB8`,
`0x0803CC28`) either read it or reset it to zero. No in-game setter path was found, so this
is a **gated feature** (§16.3/§16.20), not a reachable cheat.

The validator algorithm itself (field layout / checksum function) was **not** recovered: the
plausible GF(2)/Caesar-key/weighted-sum models were all statistically rejected against the
91 well-formed published codes. This is an explicit unresolved item (§8), not a silent
omission. The generated password shown by the pause menu is a genuine discovery, but the
sign font is stylised and the two OCR readings obtained could not be re-entered successfully;
reported as bounded unknown.

## 3. How to reproduce

### Emulator / display

```
DISPLAY=:316 SDL_AUDIODRIVER=dummy
openbox &
Xvfb :316 -screen 0 1024x768x24 &
mgba -3 "<rom>"          # /usr/local/bin/mgba 0.10.5
```

Default SDL keymap: A=`x`, B=`z`, Start=`Return`, Select=`BackSpace`, D-pad = arrows.
Menu navigation needs **short** holds (30–60 ms); 120–150 ms double-steps (§16.2).
Window focus via `xdotool windowactivate $(xdotool search --name mGBA | head -1)`.
Screenshots via `scrot -o`. Hold A ≈ 60 ms when selecting a keyboard cell.

### Boot path

1. Legal screen — press A ~6×; WB logo — press A ~3×; THQ — press A ~3×; title — Start.
2. Main menu `NEW GAME / PASSWORD / OPTIONS / CREDITS` (screenshot `menu_sel_password2.png`).
3. Down ×1 → `PASSWORD`, A → on-screen keyboard (`password_screen.png`).
4. Cursor starts on `B` (row 0, col 0). Grid rows:
   `B C D F G H J K L M N` / `P Q R S T V W X Z 0 1` / `2 3 4 5 6 7 8 9 ! ? OK`.
   Move with arrows, A selects a symbol. After 8 symbols, move to `OK` and press A.
5. `LJL7FW?R` → accepted; game starts with Velma: "Hi Scooby. I see you've found a clue…"
   (`valid_after_submit.png`).
6. `BCDFGHJK` → rejected; all glyphs red (`after_ok.png`).
7. In game: Start → pause menu `CONTINUE / PASSWORD / OPTIONS / QUIT`
   (`pause_menu2.png`). Select `PASSWORD` → wooden sign with a green generated 8-symbol
   password (`pause_password.png`).

### Save states

mGBA `Shift+F1..F9` creates `.ssN` files in the ROM folder; `F1..F9` reloads. Useful slots:
slot 1 = main menu, slot 2 = clean password screen, slot 9 = pause/password sign.

### Codes tested (in-game, on the real screen)

| Code | Result | Evidence |
|---|---|---|
| `LJL7FW?R` | **accepted** — Level 1 / Workshop 2 with 1 clue | `valid_after_submit.png`, `typed_LJL7FW?R.png` |
| `V4T18HFV` | **accepted** — starts Haunted House hub | `v4t_pause.png` |
| `XRG0Z9NR` | **accepted** — Caveman Defeated | `xrg_ingame.png`, `xrg_pause_pwd.png` |
| `BCDFGHJK` | rejected (red glyphs) | `after_ok.png` |
| `7CG810N4`, `7CG819N4`, `7CGB19N4`, `7CGB10N4`, `J7JF1P09`, `J7JF1P08` | rejected (OCR candidates for generated sign) — see §8 | `bt_*.png`, `gen_*.png` |
| 97 published literals | 0 literal ROM hits; 4 contain `O`/`Y` (out of alphabet) and 2 are 7 chars — published typos | `pubcodes.py`, `pubcodes.txt` |

## 4. Address map

File offset `F` ↔ ROM address `0x08000000 + F`.

| ROM address / file offset | Meaning | Evidence |
|---|---|---|
| `0x08000000` / `0x000000` | Header; entry `b 0xC0`; edited logo/checksum | Derived (header parse) |
| `0x0804B3C` / `0x004B3C` | Input-state update: computes held/changed/pressed/released; struct base `0x0200C320` from literal at `0x0804C94` | Derived (Thumb disasm) |
| `0x0804C7E` / `0x004C7E` | Reads `KEYINPUT` (`0x04000130`), masks `0x3FF`, calls `0x0804B3C` | Derived |
| `0x0804F10` / `0x004F10` | **Debug scene-select dispatch**: reads flag byte at `0x02014AC4`, indexes table `0x08154BD8` ×4 and dispatches | Derived |
| `0x080428EC` / `0x0428EC` | Scene name `"Password"` (inside scene-name bank `0x08042300..0x08042910`) | Observed (strings/xxd) |
| `0x08154BAC` / `0x154BAC` | Scene-table record whose name pointer is `"Password"`; 28-byte stride records | Derived (pointer scan) |
| `0x08509D00` region | Hot trace region during A-press processing | Observed (debugger `trace`) |
| `0x0200C320` | Input state struct (held +0, current +2, changed +4, pressed +6, released +8) | Derived |
| `0x02014AC4` | Hidden debug scene-select flag — `0x00` in all 5 captured states | Observed (savestate byte `0x35AC4`) |
| `0x02016E70..0x02016E90` | Static 1-based keyboard-index/font table (`00 01 02 … 09 0a…`) — **not** the typed-code buffer | Observed (savestate) |
| `0x7D2814` / `0x07D2814` | `"Password"` resource block (`Name="Password\0"`, font/tile pointers) | Observed |
| `0x7E0000..0x7FFFFF` | Large text bank (`COSTUME`, `LEVEL`, `UNLOCKED`, `SECRET`, `CHARACTERS`, `VILLAIN`, `MENUS`) | Observed (strings) |

### Savestate layout (mGBA `.ss1`, 397,312-byte `gbAs` zlib payload)

Header/CPU `0x00000..0x00FFF`; IWRAM `0x01000..0x08FFF` → RAM `0x03000000`;
VRAM `0x09000..0x20FFF` → `0x06000000`; EWRAM `0x21000..0x60FFF` → `0x02000000`.
(Confirmed by reading the typed font table and by the debug flag: `0x02014AC4` maps to
state `0x35AC4`.)

## 5. Algorithm

The on-screen alphabet and code length are proven:

```
ALPHABET = "BCDFGHJKLMNPQRSTVWXZ0123456789!?"     # 32 glyphs, keyboard order
LENGTH   = 8                                       # 8 slots on the entry line
SYMBOL_INDEX = position in ALPHABET (0..31)        # keyboard cells select these
CAPACITY = 32^8 = 2^40
```

Validation is performed when `OK` is pressed. Observed behaviour:

```
validate(code[0..7]):
    if len(code) != 8: reject
    convert each glyph to a 5-bit index via keyboard position
    compute a checksum over the indices (function NOT recovered — see §8)
    on success: decode a progress state and start the corresponding level/hub
    on failure: colour all eight glyphs red and remain on the password screen
```

Models tested and **rejected** against the 91 well-formed published codes (546 equations):

* GF(2)-linear parity relations on raw 5-bit symbol values → matrix rank 41 (full), no relations.
* Cyber-Chase-style per-column Caesar key (`u[i]=(v[i]+k[i])&31`) + six sliding even-parity
  bits, hill-climbed over all 8 keys → best 345/546 equations (≈ random).
* Same scheme with 7 alternative alphabet orderings → best 340/546.
* Weighted sum `Σ w[i]·v[i] mod 32` → best 14/91.
* XOR/sum of first N symbols → last symbol, and pairwise constant differences → chance level.

Therefore the check involves a nonlinear/larger-state transform that the static and oracle
work here did not isolate. The 40-bit capacity and the green/red feedback are the proven parts.

## 6. Tables

### 6.0 Keyboard / alphabet (observed on screen)

```
row 0: B(0)  C(1)  D(2)  F(3)  G(4)  H(5)  J(6)  K(7)  L(8)  M(9)  N(10)
row 1: P(11) Q(12) R(13) S(14) T(15) V(16) W(17) X(18) Z(19) 0(20) 1(21)
row 2: 2(22) 3(23) 4(24) 5(25) 6(26) 7(27) 8(28) 9(29) !(30) ?(31) OK
```

### 6.1 Developer scene bank (ROM `0x08042730..0x08042910`, observed strings)

`Fx Player`, `Music Player`, `Obj Viewer`, `MultiBoot Test`, `Food Puzzle 01/02/03`,
`Boss 01..04`, `Ride 01..03`, `Trap 01..03`, `Cutscene1..3`, `Splash 0..3`, `Hub 0..3`,
`Episode 00_01`, `00_02`, `01_01`, `01_02`, `02_01`, `02_02`, `03_01`, `03_02`,
`Asset Viewer`, `Password`, `Title Screen`, `Normal Boot`.
This is a hidden/developer scene list; the retail main menu labels four entries only.

### 6.2 Menus walked (all reachable, with screenshots)

* Title (`screen_intro.png`), Main menu (`menu_sel_password2.png`).
* `PASSWORD` entry (`password_screen.png`), rejected (`after_ok.png`), accepted (`valid_after_submit.png`).
* `OPTIONS` (`options_screen3.png`): `SOUND FX On`, `MUSIC On`, `LANGUAGE US↔FR`; pressing
  Down from LANGUAGE wraps to SOUND FX — exactly three items, no hidden fourth.
* `CREDITS` (`options_screen2.png`, `sel_check.png`): scrolling names, no input-gated entry found.
* In-game pause (`pause_menu2.png`): `CONTINUE / PASSWORD / OPTIONS / QUIT`; `PASSWORD`
  shows a generated 8-symbol code on a wooden sign (`pause_password.png`, `xrg_pause_pwd.png`).
* `Velma's Notebook` mystery minigame (`pause_menu.png`) — reached via the clue delivered by
  `LJL7FW?R`; no cheat entry there.

### 6.3 Published codes verified

97 unique literals were collected from GameFAQs cheats, the VinnyVideo walkthrough
(GameFAQs), supercheats, cheatingdome, jeuxvideo and GameGenie; **0** occur in the ROM as
ASCII (algorithm, not table). Four GameGenie strings contain symbols outside the 32-symbol
alphabet (`LJLYFW?R` has `Y`; `?N5NGNOX`, `OLVM4ZH2`, `QODZF5?R` have `O`) — published
typos/region drift. Two are 7 characters (`8QNWMK0`, `G8CNW3H`) — truncated in publication.
91 are well-formed 8-symbol strings; these were used as the verification corpus.

## 6b. Enumeration

**Space definition (proven):**

| Property | Value | Source |
|---|---|---|
| Alphabet | 32 symbols `BCDFGHJKLMNPQRSTVWXZ0123456789!?` | On-screen keyboard, 3×11 grid |
| Length | exactly 8 symbols | Eight entry slots on the real screen |
| Bits per symbol | 5 (`log2 32`) | Derived from alphabet size |
| Total representable strings | `32^8 = 1,099,511,627,776` (= 2^40) | Derived |
| Accepted subset | algorithmic, `< 2^40`; last symbol is checksum-constrained | Observed last-char sweep |
| Published literals in ROM | 0 of 97 | `grep`/`find` over all 8 MiB |

**Full sweep of the final symbol with a published prefix** (state = password screen with
`LJL7FW?` typed, cursor on `?`; savestate slot 8; for each symbol X, load state, select X,
navigate to OK, submit, screenshot):

```
LJL7FW?B..S : 15/15 rejected
LJL7FW?V..? : 16/16 rejected, EXCEPT LJL7FW?R (the original) -> ACCEPTED
=> of the 32 possible final symbols for this 7-symbol prefix, exactly 1 is accepted.
```

**First-symbol sweep** (prefix `BJL7FW?`, all 32 final symbols): **0/32 accepted**. This
bounds the check as more than a single trailing checksum character.

**Random inputs:** 6 random 8-symbol strings (`LGVK?8!4`, `RJ?C47B8`, `WSJ0CCCB`,
`4R7CS8?S`, `2SS9XC6J`, `PXK17QZX`) — all rejected (automated `F8`+type+OK+screenshot;

`purple=1816` = password screen still present).

**Bounds proven by rejection:** wrong final symbol (`LJL7FW?B` … `LJL7FW?S`, etc.),
out-of-alphabet characters (`Y`, `O` in published strings — not representable by the
on-screen keyboard), wrong length (two published 7-character strings are truncations),
and unrelated random 8-symbol strings.

**Novel-code status:** the in-game pause menu demonstrably *generates* eight-symbol
passwords that differ from the entered code and are not in the 97-literal published corpus
(`7CG819N4`-shape for the `V4T18HFV` state; `J7JF1P0?`-shape for the `XRG0Z9NR` state).
The sign is rendered in a stylised green font that does not pixel-match the keyboard font,
so the exact glyph→symbol transcription could not be confirmed: both OCR candidates
(`7CG819N4`, `J7JF1P09` and their ambiguous `8`/`9`/`B` variants) were rejected on re-entry.
Per §0.2 this is reported as an **unresolved** item, not claimed as a confirmed novel code.
No code absent from every published list was verified as accepted during this engagement.

**Debug-menu enumeration (bounded):** scene names listed in §6.1; the gate byte
`0x02014AC4` is `0x00` in states 1,2,3,6,7 and the only code xrefs read it or write `0`;
no retail input path to a nonzero value was found. This is a gated feature, not an
in-game-accessible cheat.

## 7. Validation evidence

| Claim | Type | Evidence |
|---|---|---|
| Header edited, single image, no trainer | Derived | `phase0.py`, `phase0b.py`, xxd `0x0..0x100` |
| 32-symbol alphabet, 8 slots | Observed | `password_screen.png` |
| Published codes not literal in ROM | Derived | `pubcodes.py` (0/97 hits) |
| `LJL7FW?R` accepted | Observed | `typed_LJL7FW?R.png`, `valid_after_submit.png` |
| `BCDFGHJK` rejected | Observed | `after_ok.png` (red glyphs) |
| Final symbol checksum-constrained | Observed | §6b sweep (32 tests, 1 accepted) |
| Changing first symbol breaks code | Observed | §6b first-symbol sweep (32 tests, 0 accepted) |
| OPTIONS has 3 items, LANGUAGE US/FR | Observed | `options_screen3.png`, `opts_lang_fr.png`, `opts_fourth.png` |
| Debug scene-select flag and bank | Derived + Observed | disasm `0x0804F10`, `strings`, savestate byte |
| Generated pause passwords exist | Observed | `pause_password.png`, `xrg_pause_pwd.png` |
| Validator algorithm | **Not proven** | all candidate models statistically rejected (§5) |

## 8. Unknowns

1. **Checksum/field layout of the password decoder** — not recovered. The check is not a
   plain GF(2) parity, not the Cyber-Chase Caesar+sliding-parity scheme (even with alternative
   alphabets), and not a simple weighted sum mod 32. The function that consumes the eight
   keyboard indices was not isolated: no literal pointer to the typed-code buffer exists in
   ROM, and mGBA's GDB stub port 2345 was occupied by another agent's process (single-port
   limitation), while the `-d` pty debugger paused in a scene-transition spin loop
   (`0x080065C6..0x080065D0`) that prevented stepping through an actual OK press.
2. **Exact transcription of the generated pause-menu password** — the sign font differs from
   the keyboard font; two readings were tried and rejected. The generated code *exists* and
   is not a published literal; its string is unresolved.
3. **Debug scene-select reachability** — the gate byte is always 0 and only zero-writers were
   found, but a setter reached via a computed pointer cannot be excluded with absolute
   certainty (no live breakpoint could be placed on it).
4. Field semantics of accepted codes (which level/flags each published code maps to) were
   inferred from the published effect labels plus the observed start scenes, not decoded
   from a recovered payload.

## 9. Tooling

Work dir: `/tmp/opencode/scoobyunmasked`.

| Script | Purpose |
|---|---|
| `phase0.py`, `phase0b.py` | hashes, header parse, logo/header scan |
| `pubcodes.py` | literal verification of 97 published codes |
| `codes_analysis.py`, `gf2.py`, `solve_keys.py`, `solve_keys2.py`, `solve_variants.py`, `solve_weights.py` | published-code corpus, GF(2)/Caesar/weight model fitting |
| `key.py`, `typecode.py`, `bruteforce.py`, `mutate_last.py`, `bf_batch.py` | xdotool key driving, grid navigation, screenshot-based accept/reject oracle |
| `state.py`, `statediff.py`, `find_typed.py`, `find_packed.py`, `state_sections.py`, `vram.py` | `.ss1` `gbAs` zlib extraction and RAM address mapping |
| `dbgbridge.py`, `dbg.py` | persistent bridge to mGBA `-d` pty debugger (stub-free alternative, §16.2) |
| `ptrscan.py`, `scenetable.py`, `find_validator.py`, `scan_thumb.py`, `buf_xref.py`, `keypad_xref.py`, `perm_scan.py` | ROM pointer/literal/Thumb scans |
| `glyphs.py`, `match_glyphs.py`, `match2.py` | OCR attempts on the generated-password sign |

Tools installed/used: `mgba` 0.10.5 (at `/usr/local/bin/mgba`), `xvfb`, `openbox`,
`xdotool`, `scrot`, `gdb-multiarch`, `arm-none-eabi-objdump` (`-M force-thumb`), Python 3
with `capstone` and `Pillow`. `numpy` was absent; pure-PIL image processing was used instead.

No ROM or copyrighted assets are redistributed in this report. All screen captures were
kept in the work directory for verification.

## 10. Legal note

Analysis only. Findings are addresses, hashes, algorithms and observations; no ROM image,
extracted graphics, audio or verbatim game text is published here beyond short UI labels
needed to reproduce navigation.
