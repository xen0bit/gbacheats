# Ecks vs. Sever (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Ecks vs. Sever/Ecks vs. Sever.gba` |
| Size | 8,388,608 bytes (0x800000) |
| `file` | Game Boy Advance ROM image: "ECKS VSE SEV" (AESE6L, Rev.00) |
| Header title | `ECKS VSE SEV` |
| Game code | `AESE` |
| Maker | `6L` (BAM! Entertainment) |
| Version / complement / checksum | `0x00` / `0x6F` / `0x0000` |
| Entry word | `0xEA00002E` — stock `b 0x080000C0`, **not** a scene cracktro |
| MD5 | `6e76914fa33b3436079ac16ecf778d15` |
| SHA-1 | `cf1d42089bec9b6c9dac7c6dfb7cd28c0cca2b51` |
| SHA-256 | `1d0bac82ca1abb3fe07603a0fcf93473e7b4d59aa39ce00e2b1bdfdafe2a28e8` |

**Phase 0 / patch check.** Exactly one Nintendo-logo hit (header at file `0x0`) — this is a single retail image, not a multi-game cart. First 4 KiB is a normal crt0 (`0x080000C0`: `mov r12,#0x12; msr CPSR_c,r12; ldr sp,=0x03007F00 ...`), no appended trainer or patched entry. Header checksum `0x0000` is the normal rebuilt-header artifact; no patch/trainer was detected.

## 2. Executive summary

The only developer-intended cheat system in this game is a **fixed password table** with **exactly 28 accepted strings**, entered on a 12-slot on-screen keyboard. There is no checksum, no generator, no algorithmic second format, and no button code that unlocks content. Two tables live back-to-back in ROM: 22 single-player level passwords at `0x087A1E16` and 6 multiplayer unlock passwords at `0x087A1F76`. The validator is a literal 12-byte compare against each 16-byte record (§4–5).

Every one of the 28 codes is already published (3rd party cheat indexes, FPS Wiki), and every published literal was verified in the ROM. **Consequently no unpublished password exists to mint** — §0.2's "generate a novel code" deliverable is impossible for this title, and this report proves the closed set instead (§6b): the validator was reimplemented exhaustively, all 28 entries verified accepted, 1,000,000 random in-alphabet inputs rejected, and in-game rejection shown for unknown, near-miss and over-long inputs.

A debug text bank for six features (`COLLISION`, `TIMING`, `INVULNERABLE`, `GOTO LEVEL`, `CYCLE CAMERA`, `PRINT`) exists at string IDs 143–148, but no reachable menu draws it and several button-code guesses failed; it is reported as a gated/cut debug overlay, not as a usable cheat (§8). The published "Special Character Views" (L/R rotate the model on the character-select screen) was confirmed in the emulator.

Published-list defects found: 3rd party cheat indexes prints `EXHONERATE` where the ROM has `EXONERATE`; FPS Wiki prints `SEETH` where the ROM has `SEETHE`. All console-version / sequel codes (`DEATHWISH`, `TOOLEDUP`, `BIGPOCKET`, `OOHSTOPIT`, `ACMEBANGS`, `COLDFEET`, `DOYOUCME`, `SMOKEY`, `BUTTERFLY`, `COVEY`, `TIGER`) are **absent** from this GBA image — they belong to the PS2/Xbox/PC game or to *Ballistic: Ecks vs. Sever II* (§16.11).

## 3. How to reproduce

* **Toolchain:** Debian: `binutils-arm-none-eabi`, `mgba` (SDL), `xvfb`, `openbox`, `xdotool`, `imagemagick`, `scrot`, `gdb-multiarch`, Python 3 + capstone 5.0.7/keystone. No non-distro packages beyond capstone/keystone.
* **Display:** private `Xvfb :317 -screen 0 1024x768x24` + `openbox`; `DISPLAY=:317 SDL_AUDIODRIVER=dummy mgba -3 ROM`. (The assigned `:316` was shared with another emulator whose focus changes dropped keys; a private display was used for key-entry evidence. Only my own PIDs were killed.)
* **mGBA SDL keymap:** A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrow keys. Hold ~50–120 ms; `xdotool windowfocus` (not `--window`).
* **Menu path to the password screen:** Title → `Start` → Main Menu (**SINGLE-PLAYER / MULTI-PLAYER / OPTIONS**, exactly 3 items) → `Down`, `A` → Single-Player submenu (**NEW GAME / PASSWORD**) → `Down`, `A` → password keyboard.
* **Keyboard geometry:** 9 columns × 4 letter rows (`ABCDEFGHI` / `JKLMNOPQR` / `STUVWXYZ0` / `123456789`), plus row 4: **OK at column 0**, **EXIT at column 8**. D-pad moves the cursor; horizontal movement wraps within a row; vertical movement preserves the column. **To reach OK reliably: move horizontally to column 0, then press Down four times** (reaching OK via a high column lands on EXIT).
* **Accept/reject is visually decisive:** press `A` on OK. An accepted code fades to a `Dateline:` game-start screen (Ecks/Sever mission); a rejected code returns to the Single-Player submenu with the typed text still in the buffer. Both are in `shot_51_*` evidence.
* **Codes tested on screen:** accepted — `EXCITE` (Ecks), `SEVERANCE`, `EXPEL` (observed start screens); rejected — `ZZZZZZ`, `EXCITF`, `EXCITEEXCI` (12 characters), `123456`.
* **Reimplementation:** `validator.py` (this work dir) reproduces the 12-byte compare, enumerates all 28 records, and runs the bounded negative search.

## 4. Address map

| Region | ROM / RAM address | Notes |
|---|---|---|
| Password alphabet | `0x087A1DE4` | `"ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"` (36 chars, NUL-terminated) |
| Unlock mask table | `0x087A1E0A` | six u16 masks `[1,5,0x15,2,0x0A,0x2A]` read by the MP-unlock code |
| Single-player password table | `0x087A1E16` | 22 records × 16 bytes; first 12 bytes compared; NUL-padded |
| Multiplayer password table | `0x087A1F76` | 6 records × 16 bytes |
| SP validator loop | `0x08015218`–`0x08015252` | inside handler `0x0801518A` (A-on-OK, screen mode 4) |
| MP validator loop | `0x08015356`–`0x08015386` | A-on-OK, screen mode 20 |
| Password-screen draw / input | `0x08014C00`–`0x08015456` | keyboard layout, cursor 0–37, char entry, OK/EXIT |
| Unlock-flag OR | `0x08014CE8`–`0x08014D04` | `flags \|= mask_table[mp_index]` |
| Unlock message dispatch | `0x08014D5C`–`0x08014E66` | 6 cases print `YOU HAVE UNLOCKED …` |
| Pause-menu draw | `0x08013AF4`–`0x08013C38` | uses string IDs 138,136,154 (and 139/140 for YES/NO) |
| Game-state base | `0x0200B7B0` | result word `+0x36`; unlock flags at `+0x464` = `0x0200BC14` |
| Password input buffer | `0x020128E0` | 12 bytes, ASCII, zero-filled |
| Keyboard cursor | `0x020128F8` | u16, 0–37 (36 letters, 36=OK, 37=EXIT) |
| Screen/mode variable | `0x0201290C` | 0 main menu, 10 submenu/password, 19 gameplay, 20 MP-password, 23 pause, 4 post-accept |
| MP code index | `0x02012968` | set to -1 on reject, `0..5` on MP accept |
| English string-pointer table | `0x087A4948` | 4-byte pointers; five languages listed at `0x087A599C` |
| Debug label strings | `0x087A4B84`–`0x087A4B98` | IDs 143–148 (COLLISION … PRINT) |

File offset ↔ ROM address: `0x08000000 + file_offset` for this single image (no sub-image bases).

## 5. Algorithm

### 5.1 Validator (both screens)

```text
input = byte[12] at 0x020128E0            // ASCII chars typed, zero-filled beyond length
if input[0] == 0: reject

// single-player screen (mode 4): 22 entries
for i = 0 .. 21:
    rec = ROM[0x087A1E16 + 16*i + 0 .. +11]
    if input[0..11] == rec[0..11]:
        result = (i <= 10) ? (i + 1) : (10 + i)   // 1..11 Ecks, 21..31 Sever
        store result -> [0x0200B7B0 + 0x36]
        ... set start state; play sound 9; transition to game start
        ACCEPT
// multiplayer screen (mode 20): 6 entries at 0x087A1F76, same compare
//   on match: mp_index=i -> 0x02012968; 0x0201290C=21;
//             flags @0x0200BC14 |= mask_table[i]; show YOU HAVE UNLOCKED <label>
reject: play sound 8; remain on the keyboard screen
```

Key properties (all **Derived** from `objdump -M force-thumb`): there is no hash, XOR, checksum, character substitution, alias conversion or length branch beyond the 12-byte loop. The 16-byte record stride is a layout convenience; the last 4 bytes of every record are zero and are never read. The 12-slot UI can express 36¹² strings, but only the 28 table strings are accepted.

### 5.2 Result-word mapping

Ecks passwords map indices 0–10 → result 1–11 (levels 2–12); Sever passwords map indices 11–21 → results 21–31 (levels 2–12). This is why the result word is not simply the level number (§16.15-style label-vs-payload caution).

### 5.3 Multiplayer unlock masks

`flags @ 0x0200BC14 |= mask_table[index]` with `mask_table = [1, 5, 0x15, 2, 0x0A, 0x2A]`. The masks are cumulative bit groups (bits 0/2/4 for the first group of three codes and 1/3/5 for the second), so codes are progressive unlocks rather than independent toggles.

## 6. Tables

### 6.1 Single-player level passwords (table `0x087A1E16`, 22 entries, stride 16)

| # | Password | Character / level | ROM address | Result word |
|---:|---|---|---|---:|
| 0 | `EXTREME` | Ecks L2 | 0x087A1E16 | 1 |
| 1 | `EXCITE` | Ecks L3 | 0x087A1E26 | 2 |
| 2 | `EXCAVATE` | Ecks L4 | 0x087A1E36 | 3 |
| 3 | `EXCALIBUR` | Ecks L5 | 0x087A1E46 | 4 |
| 4 | `EXTORT` | Ecks L6 | 0x087A1E56 | 5 |
| 5 | `EXPIRE` | Ecks L7 | 0x087A1E66 | 6 |
| 6 | `EXACT` | Ecks L8 | 0x087A1E76 | 7 |
| 7 | `EXHALE` | Ecks L9 | 0x087A1E86 | 8 |
| 8 | `EXHUME` | Ecks L10 | 0x087A1E96 | 9 |
| 9 | `EXONERATE` | Ecks L11 | 0x087A1EA6 | 10 |
| 10 | `EXPEL` | Ecks L12 | 0x087A1EB6 | 11 |
| 11 | `SEVERE` | Sever L2 | 0x087A1EC6 | 21 |
| 12 | `SURVIVE` | Sever L3 | 0x087A1ED6 | 22 |
| 13 | `SAVANT` | Sever L4 | 0x087A1EE6 | 23 |
| 14 | `SUFFER` | Sever L5 | 0x087A1EF6 | 24 |
| 15 | `SULPHER` | Sever L6 | 0x087A1F06 | 25 |
| 16 | `SERVE` | Sever L7 | 0x087A1F16 | 26 |
| 17 | `SEETHE` | Sever L8 | 0x087A1F26 | 27 |
| 18 | `SEVERAL` | Sever L9 | 0x087A1F36 | 28 |
| 19 | `SEVERANCE` | Sever L10 | 0x087A1F46 | 29 |
| 20 | `SAVAGE` | Sever L11 | 0x087A1F56 | 30 |
| 21 | `SACROSANCT` | Sever L12 | 0x087A1F66 | 31 |

### 6.2 Multiplayer unlock passwords (table `0x087A1F76`, 6 entries, stride 16)

| # | Password | ROM address | Mask (`0x087A1E0A`) | `YOU HAVE UNLOCKED` label (string ID) | Published description |
|---:|---|---|---|---|---|
| 0 | `VULNERABLE` | 0x087A1F76 | 0x01 | BOMBKIT MAP (150) | Bombkit mode |
| 1 | `VENDETTA` | 0x087A1F86 | 0x05 | DEATHMATCH MAP (151) | Surveillance DM map |
| 2 | `VIOLATE` | 0x087A1F96 | 0x15 | CHARACTER (153) | DM & Bombkit / playable character |
| 3 | `VORACIOUS` | 0x087A1FA6 | 0x02 | ASSASSINATION MAP (152) | Assassination mode |
| 4 | `VINDICATE` | 0x087A1FB6 | 0x0A | DEATHMATCH MAP (151) | Lobby DM map |
| 5 | `VESUVIUS` | 0x087A1FC6 | 0x2A | CHARACTER (153) | DM & Assassination / playable character |

The `VULNERABLE` string also appears at `0x087B2054` (inside `INVULNERABLE`) and in a story line at `0x087EB695`; only the `0x087A1F76` occurrence is the table record.

### 6.3 Debug text bank (present, not reachable)

String IDs 143–148 at `0x087A4B84`–`0x087A4B98`: `COLLISION`, `TIMING`, `INVULNERABLE`, `GOTO LEVEL`, `CYCLE CAMERA`, `PRINT`. The live pause-menu draw routine (`0x08013AF4`) references only IDs 138 (`GAME PAUSED`), 136 (`QUIT GAME`), 154 (`CONTRAST`) and 139/140 (`YES`/`NO`); no menu that uses 143–148 was observed on any walked screen.

## 6b. Enumeration

**Space definition.** Alphabet = 36 symbols (`A`–`Z`, `0`–`9`, string at `0x087A1DE4`); input field = 12 on-screen slots; comparison width = 12 bytes (`0x08015230: cmp r2,#11`); no checksum, key, permutation or reserved bits. Accepted records: 22 (SP) + 6 (MP) = **28**; each is an NUL-padded ASCII string in a 16-byte record. There is no second algorithmic format: no generator/decoder pair, no arithmetic checksum path, no BL to a code-generating routine exists beside the two compare loops.

**Validator model.** `validator.py` reimplements the exact 12-byte compare and the result mapping. It accepts every one of the 28 table strings with the expected index and result word, and returns reject for all other inputs.

**Bounded negative search (§16.9-style).** 1,000,000 random strings of length 1–12 over the full 36-symbol on-screen alphabet were fed to both validators: **0 accepted**. Combined with the static proof (the only accept branches are the two finite loops) this closes the space at exactly 28 values.

**Novel code — none exists; proof.** Every one of the 28 records was checked literally against the published lists (3rd party cheat index cheats, 3rd party cheat index cheats, FPS Wiki password table, Schlave FAQ): all 28 are documented. Because the accept set is provably the union of two fixed ROM tables with no algorithmic extension, there is **no unpublished password to mint** for this game. This is a closed-set result, not an untested gap: the full space was enumerated (28), all members verified in ROM and on screen, and the negative space bounded as above. (This is the correct outcome for a pure literal-table system; fabricating a "novel" string would be dishonest.)

**Bounds proven by in-game rejection (Observed).** From the password screen, pressing OK for:
* `ZZZZZZ` (in-alphabet but not in table) → returns to submenu, no game start;
* `EXCITF` (one-character near-miss of a valid code) → returns to submenu, no game start;
* `EXCITEEXCI` (12 characters, over the 10-char maximum published length and filling all slots) → returns to submenu, no game start;
* `123456` (in-alphabet digits) → returns to submenu, no game start.

Accepted controls: `EXCITE`, `SEVERANCE`, `EXPEL` each faded to a `Dateline:` game-start screen. RAM-level effect of acceptance was also observed via savestate diffs: after a valid submit the screen-mode word at `0x0201290C` and the game-state word at `0x0200B7B8` transition, while invalid submissions leave the password buffer intact and stay in the keyboard/submenu loop (the exact flag word was too frame-dependent to attribute a stable bit, so this is reported as Observed-transition only).

**Published-list verification / correction.** All 28 literals were searched with `grep -abo` and found in the ROM exactly once in the table regions. Two published typos: 3rd party cheat indexes level 11 for Ecks is printed `EXHONERATE` (ROM: `EXONERATE`); FPS Wiki Sever L8 is printed `SEETH` (ROM: `SEETHE`). Console/sequel cheat strings (§2) have **zero** ROM hits.

## 7. Validation evidence

* **Observed (emulator):** title/main/SP/options/password/character-select/mission-briefing/gameplay/pause screens; keyboard geometry and OK/EXIT placement; L/R rotates the selected character model; password accept → game start, reject → submenu; the six rejection cases above; MP menu requires a link connection ("WAITING FOR CONNECTION").
* **Derived (disassembly):** both validator loops, 12-byte compare, 16-byte stride, 22/6 entry bounds, result-word mapping, unlock mask table and message dispatch, string-table base and IDs, alphabet string, pause-menu draw routine and the fact it does not reference the debug IDs.
* **Inferred:** the precise bit semantics of the six MP unlock masks (bits 0/2/4 and 1/3/5) and which of Mills/Gant is unlocked by `VIOLATE` vs `VESUVIUS` — the message only says `CHARACTER`; the published mapping attributes Mills and Gant to these codes. Debug labels 143–148 are judged a gated/cut development overlay, not a proven-dead set of handlers (a single unreached helper at `0x80243A4` constructs a menu whose title ID is 143; no caller chain from a live screen was proven).

## 8. Unknowns

* Whether the debug bank (IDs 143–148) can be reached by an undiscovered input route — no published route exists, and title-screen guesses (Konami sequence, L+R+Start, Start+Select+A+B, L+R+Select) and pause-screen guesses (L+R, Select+A, Select+B, L+R+A+B) had no effect. Its practical reachability in the retail build is unproven; treat as gated/cut.
* The exact multiplayer unlock screen could not be walked because the build requires a link cable/second console; the MP table, masks and message mapping were derived statically instead, and the six MP literals were verified in ROM.
* The semantic label-to-bit assignment for the MP masks (which bit is Bombkit vs Surveillance vs each character) was not confirmed by an in-game unlock screen.
* The stable RAM flag that distinguishes accept from reject was not isolated: several nearby words change with the transition and with frame counters, so only the visual accept/reject distinction is claimed as Observed.

## 9. Tooling

* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for all disassembly; Capstone 5.0.7 + Keystone for supporting scans; `python3` + `struct` for pointer/literal scans.
* `validator.py` — reimplemented validator + closed-set enumeration + 1e6-input negative search.
* `parse_state.py` — decodes mGBA `.ss*` PNG `gbAs` chunks (zlib) into raw 397,312-byte states; EWRAM base in the raw state is `0x21000` (RAM `0x02000000` ↔ state `0x21000`).
* `game.py`, `typepw.py` — XTEST key helpers and the password-screen navigator (9-column grid; OK = column 0, row 4).
* `dis_14c00.txt`, `dis_pw.txt`, `dis_pw2.txt`, `dis_pause.txt`, `dis_208.txt` — saved disassembly excerpts.
* Screenshots `shot_51_*` (accept/reject matrix), `shot_44_*` (accept transition), `montage_*`, `a4_L`/`a5_R` (character rotation).
* No ROM or copyrighted assets are redistributed; this report contains only hashes, addresses, algorithms and findings.

### Legal note

Analysis only; the ROM and its assets are not redistributed. All published codes are quoted as short strings for documentation.
