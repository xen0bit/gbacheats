# WarioWare, Inc.: Mega Microgames! (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `WarioWare, Inc.: Mega Microgames!.gba` |
| Size | 8,388,608 bytes (`0x800000`) |
| Header title | `WARIOWAREINC` |
| Game code | `AZWE` (USA), maker `01` (Nintendo), version `0x00` |
| `file(1)` | "Game Boy Advance ROM image (AZWE01, Rev.00)" |
| Entry word | `0xEA00002E` (stock ARM branch — no cracktro/trainer patch) |
| Fixed byte / complement / checksum | `0x96` / `0x2E` / `0x0000` |
| MD5 | `a2d26dc774cec9a0b47388a5dd727b03` |
| SHA-1 | `3f556448d290fa5406d6ed367fee16cc02387ad3` |
| SHA-256 | `c09be39a09b37f6a84849dee0a6f4ce2bd0f2bc06cfe3a64ca8e7834eebb2724` |

All offsets below are file offsets; `ROM address = 0x08000000 + file offset`.

## 2. Executive summary

**Bounded negative: this retail US image has no in-game code system.** There is no
password entry screen, no cheat/button-code sequence, and no reachable debug or
sound-test menu. The only text-entry surface is the first-boot **name entry**
screen; its buffer is a save/high-score label, not a validator input. Every
reachable screen was walked in mGBA, and 56 button-combination / sequence tests
on the title and main menus produced no undocumented screen or state change.

The apparent "hidden" content is a **250-entry microgame definition table** at
`0x083A50E0` whose entries carry developer/instruction strings at
`0x080F6BE4..0x080F7780` (names such as `REST WARIO2`, `LP. 3D TEST`,
`F ZERO`, `SUPER MARIO`, `METROID`). These strings are *live data* — the table is
read by the normal microgame launcher at `0x08008F00..0x0800910C` — not a hidden
menu. TCRF (archived) independently documents only **cheating-device RAM pokes**
(e.g. game number `0x2F` at `0x03000E61` for the cut "Block Fever" game); those
are AR/GameShark-class writes and are **out of scope** for this engagement.

Conclusion (evidence types in §7): no in-game password/button-code/debug-menu
cheat exists in AZWE01. The negative is bounded by an exhaustive string/pointer
survey and by the input enumeration in §6b.

## 3. How to reproduce

* Emulator: mGBA 0.10.5, `Xvfb :316`, `SDL_AUDIODRIVER=dummy`, `-3` scale.
  Keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`,
  D-pad = arrow keys. Holds of 100–150 ms; state loads with `F2`/`F3`.
* Boot: couch splash → Start → (first boot only) "PRESS START" title → Start →
  "Diamond City – 200X" intro → main menu. With save data present, boot goes
  straight through the intro to the main menu.
* Name entry: press **R** → "Trust Wario?" (`Sure!` / `No way!`) → random name →
  "How about this?" (`OK?` / `No way!` / `R Button Again`) → "Which?" (gender).
  This is the game's random-name generator, not a code.
* Main menu tabs: Games (folder tree), Grid (4×3 microgame grid), Options
  (`View Epilogues`, `Change Names`, `Clear data` — all greyed out on a blank
  save). Start inside a stage → boombox/minigame → pause menu `CONTINUE`/`EXIT`
  → results `Retry`/`Exit`.
* Savestate used for input tests: slot 2 (main menu) and slot 3 (title screen),
  taken in the work dir `/tmp/opencode/warioware/` so the ROM folder stayed clean.

## 4. Address map

| Item | Address / range | Evidence |
|---|---|---|
| Key reader (reads `0x04000130`, computes pressed/held) | `0x08000F80–0x08001004` (Thumb) | Derived — objdump |
| Key-state globals | `0x03003FC0`, `0x03003FC4`, `0x03003FC8`, `0x03003FF4`, `0x03004884` | Derived — literal pools at `0x08000FB4..0x08001008` |
| **Microgame definition table** | `0x083A50E0–0x083A6080` = 250 × 16 bytes | Derived — 250 consecutive exact pointers found |
| Microgame/instruction name bank | `0x080F6BE4–0x080F7780` | Derived — byte dump + 250 pointer targets |
| Microgame launcher (index×16 → table → code ptr) | `0x08008F00–0x0800910C` | Derived — objdump |
| Game-number byte (external/cheat-device write target) | `0x03000E61` | Derived (`lsl #14; lsr #22` at `0x08008FB8`) + TCRF |
| Audio development text (file names) | `0x083F3C16–0x083FA3CF` | Derived + TCRF "Development Text" |
| SRAM save | 32 KiB, magic `MIW` at `0x00`, encoded player name at `0x10` | Observed — `game.sav` |

### Microgame record layout (16 bytes)

```
+0x00  u32  codeptr    (e.g. 0x083CB918)
+0x04  u32  dataptr     (e.g. 0x083FE768)
+0x08  u8   type        (1..6)
+0x09  u8   duration    (0x05,0x0A,0x0F,0x14,0x19,0x1E = 5..30)
+0x0A  u16  flags/zero
+0x0C  u32  nameptr     into 0x080F6BE4..0x080F7780
```

Entries are stored newest-name-first: entry 0 → `0x080F7770`, entry 249
(`0x083A6070`) → `0x080F6BE4` (`REST WARIO2`). Type-byte histogram over all 250
entries: `0x01`=70, `0x0A`=51, `0x14`=45, `0x19`=18, `0xA04`=15, `0x504`=11,
etc. The launcher at `0x080090DE` extracts bits 8..15 of the game-state word,
multiplies by 16, loads the record's code pointer and dispatches to
`0x08009E20` / `0x0800986C`.

## 5. Algorithm

No validator exists to reverse. The only algorithmic content relevant to
"cheats" is the microgame selection path:

```
game_no = *(u8*)0x03000E61                  ; set by normal stage logic
rec = &table[game_no]                        ; 0x083A50E0 + game_no*16
init_microgame(rec->codeptr, rec->dataptr)   ; via 0x08009E20 / 0x0800986C
show_instruction_text(rec->nameptr)         ; Shift-JIS/ASCII tile text
```

The name-entry buffer is written to SRAM at offset `0x10` in a 16-bit
glyph-code encoding and read back for on-screen display. No `strcmp`/checksum
consumes it as an accept/reject decision (Inferred from the absence of any
comparison constant and from the exhaustive string/pointer survey — see §6b).

## 6. Tables

### 6.1 Enumerated screen inventory (all reachable screens)

| # | Screen | Trigger | Cheat surface |
|---|---|---|---|
| 1 | Couch splash | boot | none |
| 2 | "PRESS START" title | Start on splash (first boot) | 26 combos + 5 sequences tested |
| 3 | Name entry | Start on title | R = random-name generator ("Trust Wario?") |
| 4 | Intro cutscene ("Diamond City – 200X", etc.) | confirm name | none |
| 5 | Pause menu (`CONTINUE` / `EXIT`) | Start in stage | none |
| 6 | Main menu → Games | intro end | 25 combos tested |
| 7 | Main menu → Grid | D-pad right | none |
| 8 | Main menu → Options | D-pad right ×2 | 3 locked entries |
| 9 | Boombox / Introduction stage minigame | start first stage | none |
| 10 | Results (`Retry` / `Exit`) | lose a microgame | none |

### 6.2 Microgame name/instruction bank (250 entries, selected samples)

`0x080F6BE4` `REST WARIO2` · `0x080F6BF0` `REST DRIBBLE` · `0x080F6C54`
`LP. 3D TEST` · `0x080F6E00` `L. ENTER COMMAND` · `0x080F6F24` `F ZERO` ·
`0x080F6F2C` `WARIO CAR` · `0x080F6F3C` `ICE CLIMBER` · `0x080F7040`
`STOMACH` · `0x080F71FC` `SUPER MARIO` · `0x080F7238` `ZELDA CAVE` ·
`0x080F7274` `SHOOTING` · `0x080F7280` `METROID` · `0x080F72A8` `SUPERMAN` ·
`0x080F74DC` `TENNIS` · `0x080F7518` `FROG JUMP ( DUMMY )` · `0x080F7678`
`TETRIS?` · `0x080F7770` `KILL VIRUSES`.

Full list is contiguous in ROM between the two bounds; the 250-entry pointer
table gives the exact record order. Names use Shift-JIS glyph codes (`0x81xx` /
`0x82xx`) for icon characters embedded in otherwise-ASCII text.

### 6.3 Out-of-scope related finding (not an in-game cheat)

Archived TCRF and the table above agree that cut games exist and are selectable
only by writing `0x03000E61` from a cheat device: `0x2F` Block Fever, `0x5E`
F1 Race, `0x66` Pong, `0xE5` Ping-Pong VS. This is a debugger/AR-class RAM write,
**not** an in-game password, button code, or menu, and is reported only as
corroboration of the table's meaning. No such write was performed.

## 6b. Enumeration

**Space definition:** There is no code space to enumerate — no password
alphabet, length, checksum, or code table exists. The bounded negative is
established by the following counts:

1. **String survey:** `strings -t x -n 4` → **85,698** strings. Of these,
   **1,341** are the audio development file-name list at `0x083F3C16..0x083FA3CF`
   and **244–250** are the microgame name/instruction bank at
   `0x080F6BE4..0x080F7780`. A case-insensitive regex over all 85,698 for
   `password|cheat|sound test|debug menu|level select|enter code|secret code|
   master code|unlock code` returned **0 hits**. (The only `code`-like hits are
   the sound-bank names `BRASS_H_Code`, `s_BASIC_PAUSE_ON/OFF` — audio assets.)
2. **Pointer/table survey:** The 250-entry microgame table is the only
   structured table whose members are human-readable names. **5** code sites
   reference its base (`0x08008A08`, `0x08008F4E`, `0x08008FB6`, `0x080090DE`,
   `0x08013BD2`); all are the normal launcher/score path. **0** hidden-menu or
   validator handlers were found.
3. **Input surface survey:** **1** text-entry UI exists (first-boot name
   entry). It has no accept/reject comparison: the entered glyph codes are
   stored in SRAM and drawn as a label. **0** password/checksum routines.
4. **Button-code enumeration:** **25** simultaneous button combinations on the
   main menu, **26** on the title screen, and **5** published-style sequences
   (Konami-style, L/R variants, repeated Start/A/B) were entered from
   savestates with before/after screenshot diffs. All changes were ordinary
   navigation (menu cursor, Start→intro, soft-reset to title). **0** undocumented
   screens or state changes.
5. **Rejection bounds / negative proof:** Because no code format exists, "bad
   checksum" and "out-of-range field" rejection tests are not applicable. The
   bound is instead the exhaustive searches above plus the complete screen walk
   (§6.1). Per guide §0.2 / §16.3 this is a *"no system"* negative, not "dead
   code", "cut feature", or "gated feature", and it is closed by counts, not by
   absence of effort.

**Novel code:** none minted — there is no code system to mint into. No value
from any published cheat list was needed or tested as an in-game code.

## 7. Validation evidence

* **Observed** — emulator screenshots in `/tmp/opencode/warioware/`
  (`boot4.png`, `title_after_start.png`, `menu1.png`, `main_menu3.png`,
  `options_screen.png`, `grid_screen.png`, `name_r_chance.png`,
  `name_trust_result.png`, `after_exit.png`, `intro3_9.png`, `skip_try.png`,
  `bf_*.png`, `tf_*.png`, `ts_*.png`). Keymap confirmed by visible cursor
  movement and screen transitions; savestate diffs confirmed state loads.
* **Observed** — SRAM dump `game.sav` (32 KiB, `MIW` magic).
* **Derived** — ROM addresses, hashes, header fields, 250-entry table and record
  layout, launcher disassembly, 5 xrefs, string counts (Python + `objdump` +
  Capstone).
* **Derived (external, data only)** — archived TCRF page confirms only
  cheating-device RAM pokes for cut games; treated as a lead, not instructions.
* **Inferred** — the name-entry buffer is a label rather than a validator input.
  This follows from the zero-hit keyword/pointer/comparison survey; no direct
  data-flow proof of every read of that buffer was produced.

## 8. Unknowns

* Whether some later regional revision (e.g. EUR `AZWP`) has a different menu
  structure. Only `AZWE01` Rev.00 was analyzed.
* Whether clearing all stages unlocks a "sound test" or extra Options entry.
  The Options entries were locked on a blank save and were not unlocked by
  normal play within this engagement; however, no such string exists in the
  ROM in any scanned encoding, so an unlockable sound-test screen is unlikely.
* The exact semantic names of some cut microgames (`LP. GOMA ( Dummy )`, etc.)
  and the high halfword of each record's `+0x0A` field were not characterized.
* Web search integrations returned no results and Cloudflare blocked direct
  fetches; recon relied on an archived TCRF snapshot reached via `curl`.

## 9. Tooling

* `file`, `md5sum`, `sha1sum`, `sha256sum`, `strings -t x -n 4`, `xxd`.
* `arm-none-eabi-objdump -M force-thumb/-M force-arm` for manual disassembly.
* Python 3 + Capstone for PC-relative literal / pointer scans; Pillow for
  screenshot diffing. Scripts in `/tmp/opencode/warioware/`:
  `key.py`, `combo_test.py`, `bruteforce.py`, `bruteforce_title.py`.
* mGBA 0.10.5 with Xvfb `:316`, openbox, `xdotool` XTEST input, `scrot`.
* REA/Ghidra was opened but the shared MCP session was taken over by another
  concurrent target mid-analysis; xrefs were therefore re-derived with local
  Python scripts. Ghidra procedure info was only usable for one function before
  the switch (`FUN_08008E88`, a bitstream reader — not a validator).

## 10. Legal note

No ROM image, graphics, music, or extracted game assets are redistributed here.
Only hashes, addresses, algorithms, counts, and analyst-authored observations
are published.
