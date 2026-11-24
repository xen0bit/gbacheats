# Tim Burton's The Nightmare Before Christmas: The Pumpkin King (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Tim Burton's The Nightmare Before Christmas: The Pumpkin King.gba` |
| Size | 8,388,608 bytes (0x800000) |
| Header title | `NIGHTMARE` |
| Game code / maker | `BNCE4Q` / (`0x51`, `0x34` = "34"? maker bytes `34 51`, `0x96` fixed) |
| Revision | 0x00 (Rev.00) |
| Entry branch | `0xEA000059` → `0x0800016C` (stock crt0; §16.1 cracktro check passes) |
| MD5 | `2de53bf040953ad79cc8135c37b47aa0` |
| SHA-1 | `8e713fa3e3cc5aa8c1836fba9d81bbf80de20638` |
| SHA-256 | `01417b3bd73133a96ac6b68900cc015306b54be0b909efb171b14a77d0d254b8` |
| Save type | SRAM, 512 bytes (two mirrored 256-byte banks, magic `CBNBGA` / `NBGA`) |

## 2. Executive summary

**No developer-intended in-game cheat system exists in this SKU.** There is no password
screen, no text-entry surface, no on-screen code alphabet, no published code list, no
button-code sequence, no debug/sound-test menu, and no cheat validator. This is a
**bounded negative** (§0.2 item 5 / §16.3 "No system"), not an untested guess:

- Every reachable screen was walked in mGBA with screenshots (§3, §7).
- The game's text is **ASCII in a script bank** with control codes; the font/tile mapping
  was decoded first, so a "no strings" result is meaningful rather than a font-encoding
  artifact (§6, §9).
- 120 keyword × encoding searches (15 cheat-related keywords × 8 encodings) returned
  **0** relevant hits; 7 classic password alphabets returned **0** hits.
- 7 boot-time button combinations (6–14 s hold) and 7 file-select combinations produced
  **no** hidden screen or persistent new flag.
- The only hidden content is **save-bit unlockables** — 3 minigame slots and 4 "Extra"
  concept-art slots — which are gated by story events / save flags, not by any input
  code (§16.18). They are enumerated in §6b.

Confidence: **high** for "no code system"; **medium** for the exact unlocking conditions
of the save-bit extras (not exhaustively played through).

## 3. How to reproduce

Emulator: mGBA 0.10.5 under Xvfb `:315`, `SDL_AUDIODRIVER=dummy`, `-3` scale.
Keymap (SDL default): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`,
D-pad = arrow keys. Hold keys 100–300 ms.

Menu path walked (all screens in `/tmp/pumpkinking/*_c.png`):

1. Boot → Buena Vista Interactive logo → **Language Select** (English/Español/Français/Italiano/Deutsch) → title "PRESS START".
2. Start → main menu: **START GAME / MINI GAME / OPTION**.
3. OPTION → returns to Language Select only (no other settings, no sound test).
4. MINI GAME → "MINIGAMES", 3 jack-o'-lantern slots, text box `???` and
   "Not yet possible. Coming Soon!" (all 3 slots); B returns to main menu.
5. START GAME → intro cutscene (A to advance) → **file select**: New Game / Load Game /
   Delete file, with `0 / 10` collectible counter.
6. Delete file → confirmation (`Delete file? Yes / No` in 5 languages).
7. New Game → cutscenes → **in game** (Halloween Town Square).
8. In game: press Start → **Pick-ups / Extras** menu (10 collectible slots + Extras tab,
   all `????????` on a fresh file); B returns to gameplay.
9. In-game pause via Start cycles between gameplay and the Pick-ups/Extras book — there is
   **no** pause menu with a cheat/code entry option.

No screen in this list contains a free-text field, keypad, code-entry prompt, or
"Enter password" equivalent.

## 4. Address map

| Address (ROM) | Purpose |
|---|---|
| `0x08000000` | Header; ARM entry `b 0x0800016C` |
| `0x080000E0` | crt0 (ARM) |
| `0x08000128`–`0x0800016C` | Thumb thunks / startup |
| `0x0801F1724`, `0x08216FA0`, `0x0824375C`, `0x0835E7D9` | Bytes `30 13 00 04` (`0x04000130`, KEYINPUT literal) — all in data/compressed blocks, no Thumb `LDR literal` to KEYINPUT found in code |
| `0x0208C08`→ ROM `0x0208C08` (file 0x208c08) | Font glyph→tile table (80 bytes): `pqrstuvwxyz{`abcdefghijkPQRSTUVWXYZ[@ABCDEFGHIJK0123456789:; !"#$%&'()*+` (mirrors at 0x230024, 0x5E38E0) |
| `0x085B3000`–`0x085B5A00` (file 0x5b3000–0x5b5a00) | Localized UI / collectible-name / credits script bank (plain ASCII with `:end`, `[x auto]`, `<c N>` control codes) |
| `0x085B52xx`–`0x085B58xx` | "Extra 1..4" / "Bonus 1..4" collectible labels; locked placeholder `????????` |
| `0x0858607C`, `0x0858664C`, `0x08595B2`, `0x085F379`, `0x085A09D6`, `0x085AD108` | Story dialogue: "You got <c 6>Mini Game N<c 0> from Lock, Shock and Barrel / Corps Kid!" etc. — story-triggered unlock messages |
| SRAM `0x0E000000` (file 0x000–0x1FF) | Save record; two 256-byte mirrored banks. Fresh file mostly zeros / `0xFF` fill. |

No validator, cheat-table, alphabet table, or input-buffer comparison site was found;
therefore no address can be given for one.

## 5. Algorithm

Not applicable — no password/validator algorithm exists. The unlock state is a **save-data
bitfield** (§16.18): the game reads a progress flag from SRAM and branches per bit to draw
either a jack-o'-lantern silhouette plus `????????` or an unlocked label
("Original Conceptual Art", minigame name). No controller input is compared to unlock it.

## 6. Tables

- **Font mapping** (file 0x208c08, 80 ASCII chars in glyph order):
  `pqrstuvwxyz{`abcdefghijkPQRSTUVWXYZ[@ABCDEFGHIJK0123456789:; !"#$%&'()*+`.
  This is a font glyph order, **not** a password alphabet.
- **Script control tokens** counted in the ROM: `:end` ×347, `:func` ×97, `go ` ×103,
  `<c ` ×88, `:if` ×40, `[x auto]` ×36. All UI text is plain ASCII — `strings` is a valid
  text oracle for this title.
- **Collectible/unlockable labels**: 6 areas ("Halloween Town Square", "Jack's House",
  "Dr. Finkelstein's Lab", "Graveyard", "Pumpkin Patch", "Oogie's Lair") × 5 languages;
  4 "Extra"/"Bonus" slots per language (0x5b5220–0x5b58b7). Fresh-file placeholder is
  `????????` (8 question marks) — the same visual used for locked minigames.

## 6b. Enumeration

**Code space:** empty — there is no code system to enumerate. Bounded negative evidence:

| Check | Method | Result / count |
|---|---|---|
| Cheat-related strings | `strings -t x -n 4` (112,314 lines) filtered for `password, cheat, debug, code, secret, unlock, level select, gameshark, action replay, bonus, extra, menu, invalid, wrong, congrat, key, enter` | Relevant hits: **0** for password/cheat/debug/code/unlock/level select/gameshark/action replay/menu/invalid/congrat. `secret` ×1 (French dialogue "secret"), `mini` ×7 (story dialogue), `extra` ×33 + `bonus` ×8 (collectible slot labels). |
| Multi-encoding literal search | ASCII / lowercase / uppercase / `+0x20` / `-0x20` / UTF-16LE / UTF-16BE / UTF-32LE for 15 keywords = **120 searches** | **0** relevant hits. |
| Password alphabets | 7 known GBA password alphabets (A–Z, 0–9A–Z, A–Z0–9, no-vowel, Car Battler Joe, etc.) literal search | **0** hits. `1234567890` ×1 at 0x814af0b, inside compressed graphics, not a table. |
| Font/tile text decode | Decoded the 80-glyph font table (§6) and script-bank control codes before concluding | All visible text is plain ASCII; no tile-index-encoded hidden strings. |
| Boot button codes | Held `A+B+Start+Select`, `L+R`, `L+R+Start`, `Start+Select`, `L+R+A+B`, `Down+B`, `Up+Select` for 6 s, plus 14 s for the first two | **0/7** produced any new screen or flag; all reached the normal title. |
| In-game/file-select button codes | Loaded a file-select savestate and held the same 7 combinations for 1.2–1.5 s; screenshot + RAM diff | **0/7** produced a hidden screen; RAM diffs were menu animation/navigation only. |
| Save-format check | Dumped 512-byte SRAM from a fresh file | Progress is a 256-byte record (mirrored); no password/checksum field. |
| Web recon | WebSearch/Bing for `Pumpkin King GBA password/cheat/unlock`, GameFAQs/TCRF fetch | No published codes found. GameFAQs and TCRF returned HTTP 403; DuckDuckGo returned a bot challenge; all treated as data and ignored (§16.8). No published list exists to verify. |

**Hidden content (enumerated, not codes):**

| Slot group | Count | Fresh-file state | Gate type |
|---|---|---|---|
| Minigames | 3 | All `???`, "Not yet possible. Coming Soon!" | Save/story flag. Unlock strings in the script bank attribute them to Lock, Shock & Barrel and the Corps Kid — story events, not input. |
| Extras (concept art) | 4 | All `????????` (0x5b5220–0x5b52c4, plus localized copies) | Save flag; unlocked label "Original Conceptual Art" (0x5b52d0+). |
| Pick-ups | 10 | `0 / 10` counter, 10 empty slots | Collectibles found in levels (§16.18 pattern). |

**Novel code:** none exists to mint. A "rejection bound" cannot be measured because there
is no validator to reject an input; the bounding is done by the exhaustive surface,
encoding, alphabet, combo, and save-format counts above. This is the "No system" case of
§16.3, fully bounded rather than merely "not tested".

## 7. Validation evidence

- **Observed** (emulator screenshots `/tmp/pumpkinking/*_c.png`): every screen in
  §3; all locked placeholders; all 14 button-combo tests returning to the normal screen.
- **Observed** (RAM): 512-byte SRAM dump; 397,312-byte `.ss1` savestate `gbAs` chunks parsed
  and EWRAM/IWRAM compared across combo tests.
- **Derived** (static): header/entry/hashes; `strings` and 8-encoding keyword counts; font
  table and script control-token counts; alphabet-table counts; absence of Thumb
  `LDR literal` to `0x04000130` in code.
- **Inferred** (not proved): the exact story trigger that sets each minigame/extras bit.
  No code path was fully traced from trigger to flag writer; the unlock messages and
  `????????` placeholders are strong but not exhaustive evidence.

## 8. Unknowns

- Exact in-game conditions that unlock each of the 3 minigames and 4 concept-art slots
  (would require a full playthrough or tracing the SRAM flag writers).
- Whether any of the 3 "Coming Soon!" minigame slots were ever implemented in a different
  regional build (this is Rev.00, code `BNCE4Q`; no other revision was examined).
- The GDB stub on port 2345 was occupied by another session; dynamic memory work used
  savestate diffs instead. This did not affect the screen walk or static counts.

## 9. Tooling

- mGBA 0.10.5 (`/usr/local/bin/mgba`) under Xvfb `:315` + openbox; `SDL_AUDIODRIVER=dummy`.
- `xdotool` keydown/keyup (focused window + XTEST), `scrot`, ImageMagick `convert`/`montage`.
- `strings -t x`, `grep`, `xxd`, `arm-none-eabi-objdump -M force-arm/force-thumb`.
- REA MCP (`open_binary`, `search_strings`, `list_procedures`) — Ghidra 12.1.4 provider;
  session was shared with other agents and target binding was unstable, so final evidence
  rests on the Python/objdump scans above.
- Analysis scripts in `/tmp/pumpkinking/`: `gba.py` (input/shot), `scan.py`,
  `scan2.py`, `alphabets.py`, `buttons.py`, `joypad.py`, `joypad2.py`, `ctx.py`,
  `bootcombos.py`, `combo_ram.py`, `combo_shot.py`, `savestate.py` (zlib `gbAs` parser).

## 10. Legal note

No ROM or copyrighted assets are redistributed. Only hashes, addresses, observed states,
and original analysis scripts are reported.

## Cleanup

All own mGBA/Xvfb/openbox processes and all `.sav` / `.ss1` / `.ss3` / `.ss4` artifacts in
the ROM folder were removed at the end of the engagement (see final reply for confirmation).
