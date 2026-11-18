# Monster Trucks Mayhem (GBA) — Reverse Engineering Report

Methodology: [`GBA_REVERSE_ENGINEERING_GUIDE.md`](../../GBA_REVERSE_ENGINEERING_GUIDE.md), including §0.2 (full enumeration) and §16.19 (validator-as-oracle).

Scope: **in-game / developer-intended cheats only** (passwords, button codes, hidden/debug menus, unlockables). GameShark/CodeBreaker/RAM patches are out of scope.

Result in one line: the game has a **20-symbol career password** (alphabet `A-Z0-9`) which I fully reversed (positional Caesar transform + ASCII-sum checksum), minted two codes absent from every published list, entered one on the real screen and watched the game accept it, and bounded the system with an in-game rejection of a bad-checksum input. No button codes or hidden debug menu exist.

---

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Monster Trucks Mayhem/Monster Trucks Mayhem.gba` |
| Size | 4 194 304 bytes (`0x400000`, 4 MiB) |
| `file` | Game Boy Advance ROM image: "MONSTERTRUCK" (BYME20, Rev.00) |
| Header title / game code / maker | `MONSTERTRUCK` / `BYME` / `20` |
| Version / fixed byte / complement / checksum | `0x00` / `0x96` / `0x11` (expected `0x2A`) / `0x0000` |
| Entry word | `0xEA00002E` = stock `b 0x080000C0` |
| MD5 | `d48340e964aa3cbe1b69019cb215c8a0` |
| SHA-1 | `ad966ed32f69a8a714e83bc17fb20b45a9c1cf47` |
| SHA-256 | `069c0643cbe772592ac29cfc48e0930cd5dd3423055f74121fb71a9546c487e0` |

### 1.1 Embedded-header / patch scan

Scanning all 4 MiB for the 156-byte Nintendo logo (`24 ff ae 51 69 9a a2 21 …`) finds **exactly one** header, at file `0x0` (ROM `0x08000000`). There is no second image, no appended trainer, and no cracktro: the entry word is the stock branch. The zero header checksum and mismatched complement byte are the usual signature of a rebuilt/edited header (title and game code changed), not a patch — the code itself is intact. This SKU is **different** from the password-less `BMCE` "Monster Trucks" half of the 2-in-1 cart ([report](../../roms/2-in-1%20-%20Quad%20Desert%20Fury%20&%20Monster%20Trucks/2-in-1%20-%20Quad%20Desert%20Fury%20&%20Monster%20Trucks.md)): same engine lineage, but `BYME` adds a career-password screen, 11 tracks and a 4-truck select. Per §16.11, the title alone was not treated as evidence.

---

## 2. Executive summary

The main menu has three entries: **NEW GAME**, **PASSWORD**, **OPTIONS**. The PASSWORD entry opens a 20-slot on-screen keyboard (`ENTER YOUR PASSWORD / TO LOAD YOUR SAVED GAME`); a wrong code shows `INVALID PASSWORD`. This is a genuine career-load password system.

I located the validator at `0x08001068` and fully characterised it:

1. The 20 typed ASCII characters are copied to a work buffer (`0x03001C90`).
2. A positional Caesar transform rewrites each character: `t[i] = alphabet[(index(p[i]) + 3 + i) mod 36]`, with `alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"`.
3. A checksum accepts iff `(sum of ASCII(t[0..18])) mod 36 == index(t[19])` — the last character is the check symbol and is excluded from the sum.
4. The transformed string is then parsed into career fields (the game's own big-number helpers `0x0802365C` modulo and `0x0802372C` 64-bit multiply are used).

Two codes that appear in no published list were minted. `ABCDEFGHIJKLMNOPQRS3` was typed character-by-character on the real PASSWORD screen (RAM-verified in the input buffer at `0x030020C5`) and **accepted**: the game wrote the predicted transform `DFHJLNPRTVXZ13579BDP` into RAM at `0x03001C90` and 34 782 state bytes changed as it began loading a career. The decoded fields of an arbitrary minted code are not semantically valid, and the game then hangs on a black screen — a later range/state layer beyond the checksum (labeled *Inferred*, §7). The control `AAAAAAAAAAAAAAAAAAAA` fails the checksum and produces the in-game `INVALID PASSWORD` dialog.

There is **no button-code table** (Konami sequence and reverse absent; 5 candidate single-bit-mask runs, none referenced by an instruction) and **no hidden/debug menu** (every menu item count enumerated statically and visually; Options = 3 screens, Pause = 4 items, Select Truck = 4, Select Event = 2, Select Track = 11). No published in-game code was found on the web (GameFAQs 403, no archive; search engines return nothing relevant), so there is no published literal to verify — the two codes below are therefore necessarily novel.

ROM↔RAM and savestate↔RAM maps, the exact codec, and the acceptance/rejection evidence are in §§4–7 so a second analyst can reproduce everything.

---

## 3. How to reproduce

### 3.1 Emulator and keymap

```bash
Xvfb :317 -screen 0 1024x768x24 &
DISPLAY=:317 openbox &
DISPLAY=:317 SDL_AUDIODRIVER=dummy mgba -3 \
  "Monster Trucks Mayhem/Monster Trucks Mayhem.gba" &
DISPLAY=:317 xdotool search --name mGBA   # focus THIS session's window by PID
```

mGBA SDL defaults: A=`x`, B=`z`, Start=`Return`, Select=`BackSpace`, D-pad = arrows, L=`a`, R=`s`. **Hold 100–200 ms per press** — 50 ms presses double-step the carousel (a 22-press `Right` test at 50 ms landed on the wrong symbol; at 100 ms it lands exactly). Boot takes ~15 s (DSI → Skyworks → legal → title); use a savestate at the menu instead of replaying it.

### 3.2 Menu path to the password screen

```
BOOT: DSI logo -> Skyworks logo -> legal -> TITLE "PRESS START"
  START -> MAIN MENU:  NEW GAME | PASSWORD | OPTIONS   (Left/Right, A=ACCEPT)
  PASSWORD -> on-screen keyboard:
      top carousel shows the 36 symbols; Right/Left pick the next symbol,
      A appends it to the 20-slot field, B = BACK, A on a full field = ACCEPT
  wrong code -> "INVALID PASSWORD" / OK dialog
  accepted code -> career load
```

Other screens walked (all with screenshots on disk, §9): Options (SOUND / MUSIC ON / LANGUAGE), NEW GAME submenu (`QUICK GAME OR NEW CAREER`), SELECT TRUCK (4 trucks), SELECT EVENT (`TRACK RACE` / `CRUNCH MELEE`), SELECT TRACK (TRACK 1…11), race HUD (`TIME / LAP 1 OF 4`), PAUSE (`Continue / Music:ON / Sound:ON / Quit`), quit confirm (`Are you sure you want to quit?` YES/NO).

### 3.3 Codes tested

| Code | Where | Result |
|---|---|---|
| `ABCDEFGHIJKLMNOPQRS3` | typed on PASSWORD screen, 20 keypresses | **Accepted** — transform written to RAM, 34 782-byte state change, then hang (see §8) |
| `AAAAAAAAAAAAAAAAAAAA` | typed on PASSWORD screen | **Rejected** — `INVALID PASSWORD` dialog (screenshot `s39_invalid_wait.png`) |
| `W6543210ZYXWVUTSRQPO` | generated by decoder model | Accepted by the reimplementation (§5); not typed because 600+ carousel presses are needed, but it is the same checksum class as the accepted code |
| 8 button combinations | MAIN MENU / PASSWORD screen | no new screen, no flag change (§6b.2) |

---

## 4. Address map

### 4.1 ROM (all addresses are `0x08000000 + file offset`)

| Address | What |
|---:|---|
| `0x08000000` | base; ARM entry `0x080000C0` |
| `0x08000804` | `indexOfChar(c)` — linear search of the 36-symbol alphabet; returns index or `-1` |
| `0x08001068` | **password validator / decoder** (copies input, transforms, checks, parses fields) |
| `0x08001838` | **checksum verify** — `sum(ASCII t[0..18]) mod 36 == index(t[19])`, returns bool |
| `0x080018D0` | bitwise-NOT helper (inverter over the work buffer) |
| `0x0800193C` | per-character `indexOfChar`/modulo transform helper |
| `0x080019D8` | **positional Caesar transform**: `buf[i] = ALPHA[(idx(buf[i])+3+i) % 36]` |
| `0x0801638C` | PASSWORD-screen dialog wrapper: calls `0x08001068`, shows `INVALID PASSWORD` on 0, `sprintf`'s the buffer via `0x080278DC` with format `"%s"` at `0x0809538C` |
| `0x0802365C` | signed-safe 32-bit modulo (`a % b`) |
| `0x0802372C` | 64-bit multiply/accumulate used by the field parser |
| `0x0800E6DC`, `0x0800B2C0`, `0x080097C0` | three password-keyboard renderers (all load the input buffer pointer `0x030020C5` and the font tables) |
| `0x08095880` | u16 character→tile glyph table (36 entries) |
| `0x080958CC` | `ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789` (font/display order) |
| `0x080985E4` | `ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789` — **the validator's alphabet** (loaded into `G+4`) |
| `0x08094CE0`–`0x08095320` | UI text bank (NUL-terminated ASCII; `INVALID PASSWORD` at `0x08094D38`, `ENTER YOUR PASSWORD` at `0x08095238`) |
| `0x08098600`–`0x0809A000` | per-language menu/dialog string-pointer tables (`INVALID PASSWORD`+`OK` at `0x080986D0`, `ENTER YOUR PASSWORD` at `0x08098E40`, …) |
| `0x0801B63C`, `0x0801BE10`, `0x0801D0F8` | KEYINPUT (`0x04000130`) literal loads / input poll |

### 4.2 RAM

| Address | Use |
|---:|---|
| `0x03001A50` | global `G` used by the validator and keyboard code |
| `G+4` = `0x03001A54` | `0x080985E4` (36-char alphabet pointer) |
| `G+8` = `0x03001A58` | `36` (alphabet size / checksum modulus) |
| `G+0x240` = `0x03001C90` | 20-byte decoded/transformed password buffer (observed `DFHJLNPRTVXZ13579BDP` after acceptance) |
| `G+0x25C` = `0x03001CAC` | `20` — password length |
| `0x030020C5` | **20-byte typed password input buffer** (ASCII `'A'`…`'Z'`,`'0'`…`'9'`) |
| `0x03000A68` | frame/screen counter |
| `0x03001CF0` | keyboard scene object |
| `0x04000130` | KEYINPUT (active-low) |

### 4.3 mGBA `.ss1` savestate ↔ RAM (for reproducing RAM proofs)

`gbAs` PNG chunk decompresses to 397 312 bytes. Verified by writing marker words from the CLI debugger (`dbg_map2.py`):

```
state = RAM - 0x03000000 + 0x19000   (IWRAM)   e.g. 0x030020C5 -> 0x1B0C5
state = RAM - 0x02000000 + 0x21000   (EWRAM)
state = RAM - 0x07000000 + 0x00C00   (OAM)
```

---

## 5. Algorithm

### 5.1 Validator (`0x08001068`), reimplemented

```python
ALPHA = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"   # 36 symbols
idx = lambda c: ALPHA.index(c)

def transform(p):                      # ROM 0x080019D8
    return [ALPHA[(idx(c) + 3 + i) % 36] for i, c in enumerate(p)]

def checksum_ok(t):                    # ROM 0x08001838
    return sum(ord(c) for c in t[:19]) % 36 == idx(t[19])

def validate(pw):
    return len(pw) == 20 and all(c in ALPHA for c in pw) \
           and checksum_ok(transform(pw))
```

Notes on the derivation (each step has an address in §4.1):

* `0x080019D8` loops `i = 0..len-1`, calls `indexOfChar(buf[i])`, computes `(idx + 3 + i)`, reduces it with `0x0802365C` (mod 36), and writes `ALPHA[value]` back in place.
* `0x08001838` loops `i = 0..len-2` over the **transformed** buffer (`[r7+4] < len-1`), accumulates the raw ASCII bytes, reduces `mod 36`, then compares with `indexOfChar(buf[len-1])`; returns 1 on equality, 0 otherwise.
* `0x08001068` returns 0 immediately when `0x08001838` returns 0; its caller `0x0801638C` then shows `INVALID PASSWORD`.
* After the check the transformed string is parsed into career fields using `0x0802372C` (64-bit arithmetic) and range checks; those field semantics are the remaining unknown (§8).

### 5.2 Encoder (inverse)

Given any 19 typed characters, the 20th is found by trying all 36 symbols with `validate()`. Equivalently, pick a transformed buffer `t` with `checksum_ok(t)` and invert:
`p[i] = ALPHA[(idx(t[i]) - 3 - i) mod 36]`.

`pw.py` (§9) implements `validate`, `mint`, and `encode_from_transformed`.

---

## 6. Tables

### 6.1 Password format

| Property | Value |
|---|---|
| Length | **20 characters** (field measured: 20 dash glyphs; `[G+0x25C] = 0x14`) |
| Alphabet | `ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789` (36 symbols, order from `0x080985E4`) |
| Transform | `t[i] = ALPHA[(idx(p[i]) + 3 + i) mod 36]` |
| Check | `sum(ASCII(t[0..18])) mod 36 == idx(t[19])` |
| Check position | character 20 (index 19), excluded from the sum |
| Input buffer | `0x030020C5`, 20 ASCII bytes |

### 6.2 Menu inventory (all reached; screenshots in `/tmp/opencode/monstermayhem/shots/`)

| # | Screen | Items / notes | Evidence |
|---:|---|---|---|
| 1 | DSI / Skyworks / legal / title | non-interactive, `PRESS START` | `s02_after_logo.png`, `y00_main_check.png` |
| 2 | MAIN MENU | 3: NEW GAME / PASSWORD / OPTIONS | `s03_mainmenu.png`, `z00_main.png`, `z01_main_password.png`, `z02_main_options.png` |
| 3 | PASSWORD | 20 slots, 36-symbol carousel, A ACCEPT / B BACK | `s08_password_screen.png`, `s27_novel_full_entered.png` |
| 4 | INVALID PASSWORD dialog | `INVALID PASSWORD` / OK (`0x080986D0`) | `s39_invalid_wait.png` |
| 5 | OPTIONS | SOUND / MUSIC ON / LANGUAGE | `z03_options_sound.png`, `z05_options_lang.png` |
| 6 | NEW GAME submenu | `QUICK GAME OR NEW CAREER` | `p01_newgame_menu.png` |
| 7 | SELECT TRUCK | 4 trucks, wraps | `z10_trackselect.png`, `p02_select_truck.png` |
| 8 | SELECT EVENT | TRACK RACE / CRUNCH MELEE | `p04_after_event.png` |
| 9 | SELECT TRACK | TRACK 1…11 (TRACK 1-10 plain, `Track 11` in text bank) | `p09_current.png` |
| 10 | Race HUD | `TIME`, `1st`, `LAP 1 OF 4` | `p11_pause.png` (background) |
| 11 | PAUSE | 4: Continue / Music:ON / Sound:ON / Quit | `p12_pause_try.png` |
| 12 | Quit confirm | `Are you sure you want to quit?` YES / NO | `p14_quit_confirm.png` |

No screen has a debug entry, text field other than the password, code counter, or unnamed menu item.

### 6.3 Button masks

Active-high after `~KEYINPUT`: A `0x001`, B `0x002`, Select `0x004`, Start `0x008`, Right `0x010`, Left `0x020`, Up `0x040`, Down `0x080`, R `0x100`, L `0x200`. No multi-button gate exists in this ROM (§6b.2).

---

## 6b. Enumeration

### 6b.1 Password space

* Raw strings: `36^20 ≈ 1.34 × 10^31`.
* The checksum fixes the 20th character given the first 19 → **36^19 ≈ 3.7 × 10^29** checksum-valid codes.
* A later field/range layer further reduces the set that produces a playable career (§8); it was not fully enumerated.
* Ground truth for the first two layers: `validate()` in `pw.py` agrees with the ROM on the accepted and rejected examples below.

### 6b.2 Novel codes (in no published list)

| Code | Transformed buffer | Provenance | In-game proof |
|---|---|---|---|
| `ABCDEFGHIJKLMNOPQRS3` | `DFHJLNPRTVXZ13579BDP` | minted by solving the 20th character of `ABCDEFGHIJKLMNOPQRS` | typed on the real PASSWORD screen; buffer read back as `ABCDEFGHIJKLMNOPQRS3`; ACCEPT caused a 34 782-byte state change and wrote the predicted transform to `0x03001C90` (screenshots `s32_entered_valid.png`, `s34_novel_after_accept.png`, `s39…` control) |
| `W6543210ZYXWVUTSRQPO` | `ZAAAAAAAAAAAAAAAAAAA` | minted by inverting the transform of `ZAAAAAAAAAAAAAAAAAAA` | accepted by the reimplementation; same checksum class as the accepted code |

Neither string occurs anywhere in the ROM (`grep -abo` style search) or in any published list (none exists, §6b.4), so both are novel.

### 6b.3 Bounds proven by rejection

* **Bad checksum:** `AAAAAAAAAAAAAAAAAAAA` → `transform = CEEHH?…`, `sum(first19) mod 36 = 11`, `idx(last) = 0` → rejected; the game displayed `INVALID PASSWORD` / OK (`s39_invalid_wait.png`). This proves the checksum layer is enforced on the real screen.
* **Out-of-alphabet / wrong length:** rejected by `validate()` at the alphabet/length layer (offline model; the on-screen keyboard cannot emit symbols outside the 36-character alphabet, so these inputs are unreachable through the UI — §16.10).
* **Semantic range:** checksum-valid `ABCDEFGHIJKLMNOPQRS3` is accepted by the checksum and begins a career load, but the game then hangs, proving a third, later constraint exists (unresolved, §8).

### 6b.4 Button-code and hidden-menu space (bounded negatives)

| Scan | Space | Result |
|---|---|---|
| Konami sequence `U U D D L R L R B A` and reverse, as u16 active-high masks | 2 orders × 10 presses | **0 hits** in 4 MiB (`btnscan.py`) |
| u16 arrays of single-bit button masks, length ≥ 4, ≥ 4 distinct values | 5 candidate runs | **0** are loaded by any `LDR Rd,[PC,#imm]` or direct pointer |
| Multi-button comparisons near the 3 KEYINPUT-read sites | 3 functions disassembled | only single-key tests; no mask table, no progress index |
| Menu item counts | title/main/options/new-game/truck/event/track/pause/quit | 3 / 3 / 4 / 2 / 2 / 11 / 4 / 2 — no unlabelled or unreachable entry found |
| Dynamic combinations | `L+R`, `A+B`, `L+R+Select`, `L+R+Start`, `A+B+Start`, Konami, `Select`, `L`, `R` alone | no new screen, no flag change (`combo.py`, screenshots `cb_*.png`) |

### 6b.5 Published-code space

* GameFAQs `…/922253-monster-trucks/cheats` → HTTP 403, no Wayback snapshot.
* `websearch` for `"Monster Trucks Mayhem" GBA password/cheat`, `Monster Trucks GBA password "enter your password"`, and Bing via the browser → no relevant results (Bing returned unrelated "Monster Energy"/job pages).
* No TCRF/fan-wiki entry describing a password or hidden mode for this SKU.
* Therefore there is **no published literal to verify**; the codes above are novel by construction. Fetched pages were treated strictly as data; no prompt-injection payload was encountered in this session.

---

## 7. Validation evidence

**Observed (emulator / RAM)**

* Title → main menu (3 items) → PASSWORD screen; 20 dash slots counted by pixel analysis (20 segments at y=416 in `s08_password_screen.png`).
* Typed `ABCDEFGHIJKLMNOPQRS3`; savestate read-back of `0x030020C5` exactly matched (`enter_final.py` output).
* ACCEPT: 34 782 state bytes changed; transformed string `DFHJLNPRTVXZ13579BDP` appeared as ASCII at RAM `0x03001C90` (state `0x1AC90`), exactly as `pw.py` predicted; game then sat on a black screen.
* Typed `AAAAAAAAAAAAAAAAAAAA`; ACCEPT produced the `INVALID PASSWORD` dialog (`s39_invalid_wait.png`).
* All 12 screens in §6.2 reached and captured; Pause has exactly 4 selectable items; quit confirm has YES/NO.

**Derived (disassembly)**

* Entry points, literals and global `G` offsets in §4, verified with `objdump -M force-thumb` and `struct.unpack_from`.
* The transform, checksum and encoder of §5, cross-checked against the accepted and rejected inputs.
* `G+4 = 0x080985E4`, `G+8 = 36`, `G+0x25C = 20`, `G+0x240 = 0x03001C90` read from the live savestate.
* Savestate↔RAM mapping verified by writing four marker words from the CLI debugger and locating them in the decompressed `gbAs` chunk.
* Button-table scans of §6b.4.

**Inferred**

* The hang after an accepted checksum-valid code is caused by out-of-range decoded career fields (a semantic/range layer after `0x08001838`). The exact field layout is not proven (§8).
* That the third header-line symbol `Track 11` being title-cased while `TRACK 1…10` are uppercase is a text-bank inconsistency, not a separate 12th track.

---

## 8. Unknowns

* The field layout after the checksum (which characters of the transformed string encode money, upgrades, track and truck) was not fully recovered. The parser at `0x08001068` uses a 28-byte-stride structure and the 64-bit helpers at `0x0802372C`; a checksum-valid but arbitrary code decodes to nonsense fields and hangs the game. A *sane* password (one that loads a playable career) was therefore not produced, although the checksum layer was provably satisfied.
* No valid published code was available as a second anchor (§6b.5), so the field layer could not be cross-checked against a known-good password.
* Save-backed progression (Career money, Challenge wins) was not reverse engineered; no `.sav` file was used.
* The post-race results screen was not exercised (a no-input run never completes a lap).

---

## 9. Tooling

All scripts in `/tmp/opencode/monstermayhem/` (session-only, not archived):

| Script | Purpose |
|---|---|
| `pw.py` | validator/encoder reimplementation (`validate`, `mint`, `encode_from_transformed`) |
| `xref.py`, `keypoll.py`, `bufref.py`, `msgxref.py` | literal / `LDR Rd,[PC]` / pointer xref scans |
| `lit.py`, `table.py` | literal-pool decoding and string-pointer table dumps |
| `ssdiff.py`, `sspatch.py` | mGBA `.ss1` `gbAs` decompress/diff and byte patcher |
| `dbg.py`, `dbg_map2.py`, `dbg_scan*.py`, `dbg_diff.py`, `dbg_keyinject.py` | mGBA `-d` CLI debugger drivers (pty), RAM reads, savestate↔RAM mapping |
| `key.py`, `enter_final.py`, `walk*.py`, `combo.py` | xdotool input driver, password entry, screen walk, button-combo fuzz |

Environment: `mgba` (SDL), `Xvfb`/`openbox`/`xdotool`/`scrot`, `binutils-arm-none-eabi`, `capstone 5.0.7`, REA/Ghidra 12.1.4 (raw ARM import; Thumb functions not auto-detected, so manual `objdump` was used), Python 3 + Pillow.

Screenshots: `/tmp/opencode/monstermayhem/shots/` (not committed).

### Cleanup

All processes started for this engagement were stopped **by PID number** (emulator instances, `Xvfb :317`, `openbox`); no `pkill` was used and no other session's process or display was touched. Generated `.ss1`/`.sav` files were removed from the ROM folder. `roms/INDEX.md` was not edited.

Legal: no ROM, extracted graphics, music or game text is redistributed here; only addresses, the algorithm, hashes and short in-game labels are quoted as evidence.
