# Mega Man Zero 3 (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Mega Man Zero 3/Mega Man Zero 3.gba` |
| Size | 8,388,608 bytes (0x800000) |
| Header title | `MEGAMANZERO3` |
| Game code | `BZ3E` (USA), maker `08` (Capcom) |
| Version / complement / checksum | `0x00` / `0x6C` / `0x0000` |
| Entry word | `0xEA00002E` → `0x080000C0` (stock ARM crt0) |
| MD5 | `aa1d5eeffcd5e4577db9ee6d9b1100f9` |
| SHA-1 | `403a78f2cad93d41e4b0f2e520ce08026531664b` |
| SHA-256 | `067f420fbd4aabc1ccc11adce410ee10c89aae5b9a7473e29b9b45a4ef2b8b0d` |

**Embedded-header scan:** the 156-byte Nintendo logo (`24 ff ae 51 …`) occurs exactly once, at file offset `0`. This is a single, unmodified retail image — no appended trainer, no multi-game shell, no scene cracktro. The only extra file created during analysis was mGBA's 32 KiB SRAM image (`Mega Man Zero 3.sav`), removed at cleanup (§7).

## 2. Executive summary

**No in-game cheat system exists in this build.** There is no password entry screen, no button-code sequence, no sound test / bonus / level-select screen, and no reachable hidden debug menu. The game is a conventional battery-save action platformer: progress, difficulty and extras are SRAM flags, not codes.

Evidence is deliberately bounded (guide §0.2 / §16):

* Every reachable screen was walked in mGBA with screenshots and keypad-RAM confirmation (§7).
* The game's text is **not ASCII** — it is font/tile-indexed. After discovering the mapping, the text banks were fully decoded: UI/menu text is stored as `stored_byte + 0x36 = ASCII` and dialogue as `stored_byte + 0x1C = ASCII`. `strings` therefore finds nothing (the only ASCII run in the whole 8 MiB is the header title).
* An exhaustive scan of the decoded ROM at **all 256 byte offsets** for `PASSWORD`, `CHEAT`, `UNLOCK`, `HIDDEN`, `SOUND TEST`, `BOSS RUSH`, `GALLERY`, `STATUE` returned **zero** occurrences. `DEBUG` occurs once — in the credits roll as `DEBUGGING TEAM` (file `0x371890`), not as a menu. `SECRET` occurs only in ordinary dialogue.
* The keypad/input path was reversed: the input manager at `0x08003194` maintains an active-high state struct at `0x02002130` (+0 held, +2 previous, +4 pressed, +6 released). No consumer of that struct compares it with a multi-button mask or maintains a press-history progress index, i.e. the code signature of a button cheat is absent. Direct searches for the Konami sequence, `L,R,U,D`, and `A,B,Start+Select` as 8/16-bit mask arrays found no hits. The A+B+Select+Start boot code known from *Mega Man Zero* (validator `0x08000538`, `keys & 0x0F == 0x0F`) and *Mega Man Zero 2* does **not** transfer to this SKU: MMZ3 has a single `KEYINPUT` literal at `0x080031F8` (inside the generic input manager), no `ands #0x0F / cmp #0x0F` validator pattern anywhere in ROM, and holding that combination at boot did nothing (§3).

One genuinely interesting negative-adjacent finding: the UI text bank contains a title-menu label **`MINI GAMES`** at file `0x371271` (and its highlighted variant at `0x37127E`) alongside `NEW GAME` (`0x371243`) and `LOAD GAME` (`0x371259`). The shipped title menu draws only **two** rows, and no input tried on the title or menu (D-pad, L/R, Select, A/B, Start; L+R+Start; repeated downs) reveals the third. It is therefore a **gated or cut UI entry in this revision**, not a reachable cheat. This is classified per guide §16.3 as a *gated/cut feature*, with the gate writer not isolated (§8).

Published-code research: GameFAQs, TCRF, VGChartz and general web search were attempted but all were blocked by 403/captcha/bot checks in this environment (§9). No specific published GBA password exists for this title to verify; the ROM-side evidence above is the primary basis for the negative.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 SDL, `SDL_AUDIODRIVER=dummy`, `DISPLAY=:317`, `Xvfb :317 -screen 0 1024x768x24`, `openbox`, `mgba -3 -d <rom>`.
* Default keymap confirmed against `KEYINPUT` (`0x04000130`): idle `0x03FF`; holding `x` (A) gives `0x03FE` — active-low, bit0 = A.
* Boot path: Inti Creates splash → Capcom logo → title `PRESS START`.
  * With an existing SRAM: **Start** opens the title menu directly.
  * With a blank SRAM: **Start** plays the logo/opening movie and then runs an attract demo; pressing **Start** during the demo returns to the title menu.
* Menu map (all walked, screenshots in `/tmp/opencode/mmzero3/`):
  * Title menu: `NEW GAME`, `LOAD GAME` (no third row).
  * In-game pause (Status): `ZERO ×2`, `LEVEL F`, play time, E-Crystals, `Code Name WARRIOR`, MAIN/SUB slots; footers `L → Elf List`, `R → EX Skills`, centre `ESCAPE`.
  * `L` → Elf List: `SATELLITE1`, `SATELLITE2`, `FUSION`, `E-CRYSTALS`, `LIST`; footer `L → Options`, `R → Status`.
  * `L` again → Options: **Button Settings** (TYPE A / TYPE B / CUSTOM; MAIN=B, JUMP=A, DASH=L, SUB=R) and **Attack Mode** (TYPE A/B/C; B=main, R+B=sub). Only two sections — no sound or difficulty settings.
  * `R` from Status → EX Skills: `None learned` (empty because no skills earned yet).
  * `ESCAPE` → gameplay; death → Game Over screen: `CONTINUE`, `RESTART S. GAME`, `QUIT THE GAME` (strings confirmed in text bank at `0x3712E7`, `0x371302`, `0x371334`).
  * Stage-intro cinematics and the intro stage (Residential Area) were played through; stage names are present in the text bank (`AEGIS VOLCANO BASE`, `OCEANIC HWY RUINS`, `OLD RESIDENTIAL`, `AREA X`, etc., starting at `0x36F607`).
* Codes tested: none applicable — no code-entry surface exists. Button tests used: D-pad, A, B, L, R, Select, Start, L+R+Start, repeated Down, and 60–250 press fast-forward sequences. Because sibling titles *Mega Man Zero* and *Mega Man Zero 2* have a boot code (hold A+B+Select+Start, per their separate reports in this collection), that exact combination was also held from the first emulator frame on a clean boot and again through the title transition: it produced only the normal logo/title and the title menu still had **two** rows. No tested input produced a new row or screen.
* Savestate RAM check (mGBA `gbAs` chunk, decompressed with `zlib`; IWRAM at raw `0x19000`, EWRAM at `0x21000`): EWRAM `0x02002130` reads `00 fc 00 fc 00 00 00 00 01 ...`, i.e. `held = ~KEYINPUT = 0xFC00` with no key down and `pressed = 0`, confirming the decoded input struct; no persistent debug flag appeared in IWRAM/EWRAM after the boot-combo attempt.

## 4. Address map

| Item | ROM / RAM address | Notes |
|---|---|---|
| Header / entry | `0x08000000` / `0x080000C0` | single header, stock crt0 |
| `main` (Thumb) | `0x080017CC` | init calls, then task create `0x08002330(r0=1)` |
| Task create / activate | `0x08002330` / `0x080023F4` | 24-byte task records, IWRAM base `0x03001760` |
| Input manager init | `0x0800314C` | two 0x18-byte state structs |
| Input manager | `0x08003194`–`0x08003220` | reads `0x04000130` via literal at `0x080031F8` |
| Input state struct | `0x02002130` (EWRAM) | +0 held (active-high), +2 prev, +4 pressed, +6 released, +8 init flag, +0xA.. per-key counters, +0x14/+0x15 = 24/4 repeat params |
| UI/menu text bank | `0x08036F00`–`0x080389F0` | offset `+0x36` |
| Dialogue text bank | `0x08036F20`–`0x080389F0` | offset `+0x1C` |
| `NEW GAME` / `LOAD GAME` / `MINI GAMES` strings | `0x080371243` / `0x080371259` / `0x080371271` | + highlighted variants `+0xB`/`+0xD` |
| `CONTINUE` / `RESTART` / `QUIT THE GAME` | `0x0803712E7` / `0x080371302` / `0x080371334` | Game Over menu |
| `DEBUGGING TEAM` (credits) | `0x080371890` | false-positive DEBUG hit |
| Stage-name table | `0x08036F607` onward | e.g. `DERELICT SPACECRAFT`, `AEGIS VOLCANO BASE` |
| SRAM save slots | `0x0E00355A`, `0x0E007558` (mirrored in `.sav`) | two 0x4000-apart records |

File offset ↔ ROM address: `addr = 0x08000000 + file_offset`.

## 5. Algorithm

No validator or generator exists — the required algorithm section is the **decoder for the font-indexed text**, which is the only non-trivial encoding found:

```python
# UI / menu strings
ui_text = bytes((b + 0x36) & 0xFF for b in rom_block)
# dialogue strings
dialogue = bytes((b + 0x1C) & 0xFF for b in rom_block)
```

Control bytes in the UI bank: `0x1F` → record marker (renders as '5'), `0xF7` → separator (renders as '-'), `0x00` → space (renders as '6' under the +0x36 transform), `0x01` → highlighted variant marker. In the dialogue bank `0x1C` = space, `0x18` = apostrophe, `0x01` = period, `0x04` = question mark, `0x19` = comma.

Input model (derived from `0x08003194`): `held = ~KEYINPUT & 0x3FF`; `pressed = held & ~previous`; per-key 8-bit counters at `state+0xA` are reloaded from `state+0x14/0x15` (24, 4). No longer history is kept anywhere in this struct.

## 6. Tables

| Keyword | Hits across all 256 byte offsets | Interpretation |
|---|---|---|
| PASSWORD | 0 | no password UI or data |
| CHEAT | 0 | — |
| DEBUG | 1 (`0x371890`, +0x36) | credits: `DEBUGGING TEAM` |
| SECRET | 3 (`0x37D2F9`, `0x37E24C`, `0x37F452`, +0x1C) | dialogue only |
| SOUND / SOUND TEST | 4 / 0 | credits + dialogue; no sound-test menu |
| UNLOCK, HIDDEN, BOSS RUSH, GALLERY, STATUE | 0 | — |
| MINI GAMES | 1 (`0x371271`, +0x36) | title-menu label, not rendered in this build |

Menu vocabulary decoded from the UI bank (`0x371243`–`0x37148F`): `NEW GAME`, `LOAD GAME`, `MINI GAMES`, `PLEASE WAIT`, `B BUTTON CANCEL`, `DISK IS UNREAD`, `LINK TERMINATED`, `CONTINUE`, `RESTART`, `SAVE`, `GAME`, `QUIT THE GAME`, `ZERO`, `CIEL`, `COPY X`, `HARPUIA`, `FEFNIR`, `LEVIATHAN`, `PHANTOM`, `STAFF`. The character names belong to cutscene/name-display text, not a character-select cheat.

## 6b. Enumeration

Guide §0.2 requires the *whole space* to be characterised. The characterisation here is the **negative** one:

* **Input surfaces enumerated:** 2 title-menu rows rendered, 3 labels present in the text bank, 7 in-game menu screens, 3 Game Over rows, 2 option sections, 4 Elf-List rows, 1 EX-Skills list (empty). Every one was entered on the real screen.
* **Button-code space searched:** all single D-pad/face/shoulder keys and the L+R+Start combination on the title and menu; mask-array searches for the Konami sequence (both U-first and D-first), `L,R,U,D`, and `Start,Select,A,B` as u8/u16 arrays — **0 hits**. The input struct at `0x02002130` retains no multi-press history suitable for such a code.
* **Password space searched:** decoded text at every one of 256 byte shifts; `PASSWORD`/`CHEAT` produce **0 hits**. No on-screen alphabet/keypad was ever displayed. There is no table to enumerate and no validator to oracle — §16.19 was considered but there is no candidate function to call.
* **Novel code:** not applicable — no code system exists. The closest novel observation is the unrendered `MINI GAMES` label (§2), which is a cut/gated feature rather than a code and therefore cannot be "minted" or entered.
* **Bounds proven by rejection:** `MINI GAMES` was probed with all plausible input combinations and remained unrendered (rejection), which bounds the title menu at two selectable entries in this build. No generated value was accepted because no value can be entered.

## 7. Validation evidence

* **Observed (emulator):** all screens in §3, screenshots `title_clean`, `menu4`, `pausemenu`, `elflist`, `options2`, `ex2`, `stage_end`, etc. in `/tmp/opencode/mmzero3/`.
* **Observed (RAM):** `0x04000130` = `0x03FF` idle and `0x03FE` with A held, read through mGBA's `-d` debugger (which required `c` then a `frame` step because the CLI debugger pauses execution while at its prompt).
* **Derived:** input manager structure and lack of key-history consumer (disassembly `0x08003194`–`0x08003220`, Capstone + `arm-none-eabi-objdump -M force-thumb`); text encoding offsets; all address-map entries.
* **Inferred:** that `MINI GAMES` is gated on a save/story flag (or cut) rather than a button code — several inputs failed, and the game is SRAM-driven, but the exact gate writer was not isolated.
* No screenshots are attached to this reply; RAM/address evidence is primary.

## 8. Unknowns

* The writer of the gate that hides the third title-menu row (`MINI GAMES`) was not found. Its label is present at `0x080371271` with a highlighted variant, so it is likely set after a full clear or by an unused debug flag. Enumerating the SRAM flag would require beating the game or a full save-format reversal.
* The mission-select ("Trans Server") screen was not reached in gameplay; the intro stage was played but the run ended in Game Over before the hub. Mission/stage names were nevertheless recovered from the text bank (`0x36F607` onward), which bounds that screen's vocabulary.
* Published-code verification could not be performed because all web sources were blocked (§9). No published GBA password for this title is known to exist.

## 9. Tooling

* `md5sum`, `sha1sum`, `sha256sum`, `file`, `xxd`, Python 3 (`struct`, `re`, `capstone 5.0.7`).
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` and custom Capstone helpers `dis.py`, `dis2.py` in the work dir.
* mGBA 0.10.5 with `-d` CLI debugger driven through a pty (`ptyctl.py`, `key.py`) on `DISPLAY=:317`; Xvfb + openbox.
* Web attempts (all blocked): `websearch` (no results), GameFAQs (403), TCRF (403/CAPTCHA), Google/Bing/DuckDuckGo (captcha or irrelevant results), `r.jina.ai` proxies (blocked). No content from these was treated as instructions; nothing suspicious was followed.

## 10. Legal note

No ROM, save data, or copyrighted graphics are redistributed. Only hashes, addresses, decoding methods, and original screenshots kept outside the repository were produced.
