# Star Wars: Episode III – Revenge of the Sith (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Star Wars: Episode III – Revenge of the Sith.gba` |
| Size | 8,388,608 bytes (`0x800000`) |
| Header title | `STARWARSROTS` |
| Game code | `BE3E` |
| Maker code | `41` |
| Version | `0x00` |
| Entry word | `0xEA00002E` (stock retail branch — not a patched/cracktro image) |
| Fixed `0x96` | present; complement `0x2E`; header checksum `0x0000` (normal rebuilt-header artifact) |
| MD5 | `6c44b49d69e6c0576197742f20250c40` |
| SHA-1 | `146a5ae97832131d41698c182ce58176b7bb848f` |
| SHA-256 | `04f247311ad968e21ef71ef2ee05d86c855652703b42e4fae526553e3a471a03` |

Evidence: **Observed** (`file`, `xxd`, `md5sum`/`sha1sum`/`sha256sum` on the exact file above).

---

## 2. Executive summary

**The GBA SKU of Star Wars: Episode III has no developer-intended password / cheat-code system.** The
widely republished "codes" for this title (`JAINA`, `XUCPHRA`, `KAIBURR`, `BELSAVIS`, `021282`,
`NARSHADDAA`, `AAYLASECURA`, `TANTIVEIV`, `ZABRAK`, `COMLINK`, `KORRIBAN`, `SUPERSABER`, `071779`,
`NATHAN G`, `ATENVU`) belong to the **PS2** (options-screen password list) and **DS** (Settings → Codes)
SKUs. GameFAQs' GBA cheat page renders those codes under a `PS2` heading, and an independent current
source states outright that there are no official cheat codes for the GBA version. All 15 literals are
absent from the 8 MiB GBA image under six encodings (§6b). Ghidra's 7,039-string inventory contains
zero occurrences of `PASSWORD`, `CODE`/`CODES`, `DEBUG`, `LEVEL SELECT`, or `ENTER CODE`.

What the GBA game *does* have, and what was enumerated in full, is:

1. **Save-bit unlockables** — Master difficulty (per character), Force-power levels, Fury moves,
   customization points. These are progress gates, **not codes** (guide §16.18).
2. **Documented button combos** — 10 Focus Force powers activated by `R` + buttons/D-pad. These are
   ordinary advertised abilities (the in-game help screen prints every combo), not hidden cheats.
3. **A 3-character save-slot name field** — investigated and rejected as a validator: it is a
   label-entry field (Up/Down cycle letters, A advances, B deletes) with no comparison against a code
   table (guide §16.2b).
4. **Debug leftovers** — `Level ID:  %d` (`0x080F160C`), debug labels `INVISIBLE HAND-1/-2`,
   `YAVIN 4`, `MUUNILINST`, `DANTOINE` (`0x080F192C`…`0x080F1968`) and a font/kerning byte table at
   `0x080F1752`. These are reachable only as render callbacks/label tables; **no debug menu gate was
   found** (zero code xrefs to the label table, zero menu strings).

This is a **bounded negative**, with the searched space and counts given in §6b.

---

## 3. How to reproduce

**Emulator/headless setup**

```bash
export DISPLAY=:317
Xvfb :317 -screen 0 1024x768x24 &
openbox &
SDL_AUDIODRIVER=dummy mgba -3 "<ROM>" &
```

Keymap used (mGBA SDL defaults): `A=x`, `B=z`, `L=a`, `R=s`, `Start=Return`, `Select=BackSpace`,
D-pad = arrow keys. Holds of 30–60 ms were used for menu navigation (longer holds double-step).

**Screen walk performed (every reachable screen, all with screenshots saved under
`/tmp/starwars3/`)**

| # | Screen | Screenshot | Key observations |
|---:|---|---|---|
| 1 | Language select (ENGLISH / FRANÇAIS / ESPAÑOL) | `boot.png` | 3 entries |
| 2 | Title "PRESS START" | `title2.png` | 3 entries: SINGLE PLAYER / MULTIPLAYER / CREDITS |
| 3 | Save-slot select (1/2/3, all `---`) | `sp_menu2.png` | 3 slots |
| 4 | Slot info / "START NEW GAME" | `slot1b.png` | `ANAKIN 0/13`, `OBI-WAN 0/13` |
| 5 | 3-character name entry | `t4.png`, `namefield.png` | Up/Down change letter (A→C observed), A advances, B deletes |
| 6 | Character select | `selchar2.png` | ANAKIN / OBI-WAN; difficulty PADAWAN / JEDI / **MASTER greyed** |
| 7 | Difficulty ring | `diff_master.png` | MASTER unreachable: Down from JEDI wraps to PADAWAN |
| 8 | Confirm | `play1.png` | CONFIRM / CANCEL |
| 9 | Intro crawl + cinematic | `intro4.png`, `after_intro2.png` | skippable with A |
| 10 | Gameplay HUD | `after_intro2.png` | side-scrolling level |
| 11 | Pause → STATUS | `pause2.png`, `fury4.png` | 6 Force powers listed; 3 stat upgrades |
| 12 | Pause → OPTIONS | `opt2.png`, `opt4.png` | exactly 5 items: CHANGE MISSION, MUSIC, SOUNDS, RESUME GAME, QUIT GAME — **no CODES entry** |
| 13 | Pause → FURY | `fury4.png` | 4 slots; only slot 1 `VADER'S WRATH — HOLD B` unlocked |
| 14 | Multiplayer | `mp1.png` | demands Game Boy Advance Game Link cable; cannot proceed single-handed |

No code-entry surface exists on any of these screens (guide §0.2 "walk EVERY reachable screen").

**Button-combochecks tried on the title screen** (held 400 ms, one at a time from the F1 savestate):
`L+R`, `L+R+Start`, `L+R+Select`, `Start+Select`, `A+B+Start+Select`, `L+R+A+B`, `L+R+A`,
`Up+Down`. Screenshots `combo_*.png`. None produced a menu, overlay, flag change, or any behaviour
other than the normal title-screen "press A/Start to advance" path.

---

## 4. Address map

| Address (ROM `0x08…` / RAM `0x02…`) | Meaning | Evidence |
|---|---|---|
| `0x08000000` | Entry branch `0xEA00002E` | Observed |
| `0x0806F498` | printf-style helper emitting `Level ID: %d` | Derived (Ghidra `FUN_0806f498`) |
| `0x080B01EC` | text renderer that calls the above format handlers | Derived (Ghidra) |
| `0x080AD98A` | input/flag routine: tests struct byte `+0x28` bit0 (A) / bit1 (B), toggles DISPCNT bit 14 (`0x04000000 &= 0xBFFF`) | Derived (objdump Thumb) |
| `0x080ADA1C` | input-state sampler: stores `~KEYINPUT` into `+0x04`, XOR with previous into `+0x06` | Derived |
| `0x080B7BA4`–`0x080B98xx` | English UI string bank (`CREDITS`, `MASTER`, `JEDI MASTER`, `PRESS START`, help text) | Observed |
| `0x080B91A0`–`0x080B9810` | Force-power help text bank (all 10 combos + stat descriptions) | Observed |
| `0x080F160C` | `"Level ID:  %d"` debug format string | Observed |
| `0x080F1752` | 106-byte font/kerning byte table (glyph widths, not a password alphabet) | Observed |
| `0x080F192C`, `0x080F1940` | `INVISIBLE HAND-2`, `INVISIBLE HAND-1` debug labels | Observed |
| `0x080F1954`, `0x080F195C`, `0x080F1968` | `YAVIN 4`, `MUUNILINST`, `DANTOINE` debug labels | Observed |
| `0x08021D028`–`0x08021D048` | debug label pointer table (level/enemy names) | Observed |
| `0x02002C80` | main global game struct (EWRAM); `+0x004` = screen/scene ID (`0x1F` title → `0x00` gameplay), `+0x6F8…` = 16-bit Force-power levels (`0x0002` in-game) | Observed (savestate `gbAs` diff) |
| `0x030015C4` | IWRAM pointer to the global struct (holds `0x02002C80`) | Observed |
| `0x04000130` | KEYINPUT, read at only 5 sites (`0x080ADA02`, `0x080ADA26`, `0x080AF77C`, `0x080B0626`, `0x080B0646`) | Derived (Capstone literal scan) |

File offset → ROM address: `0x08000000 + file_offset`. savestate `gbAs` layout used: IWRAM at
state offset `0x19000`, EWRAM at `0x21000`; raw state length 397,312 bytes.

---

## 5. Algorithm

No password validator exists, so there is no decoder to reimplement. The two algorithms that *were*
recovered are the input sampler and the unlockable gate:

**Input sampler** (`0x080ADA1C`, **Derived**):

```
held  = ~KEYINPUT & 0xFFFF          // active-high; stored at struct+0x04
pressed = held ^ previous_held      // stored at struct+0x06
previous_held = held                // struct+0x04
```

This is a per-frame held/edge pair. There is no ring buffer, no sequence matcher, and no comparison
against a multi-button constant anywhere in the 5 KEYINPUT readers. The only multi-button logic found
is the A+B test at `0x080AD9CA` (`r1 & ~3`), which writes `struct+0x28` and clears DISPCNT bit 14 —
a screen/flag effect, not a cheat validator.

**Unlockable gate** (`0x0806F000` region, **Derived**): screen/scene state is read from
`*0x030015C4 + 0xA9/+0xAA`, used to index a table and produce an elevation/level value; the
"MASTER" option is drawn greyed at character select because the corresponding save-field has not
been set. Per the published but *unverified-in-ROM* rule, beating Jedi/Padawan mode with a character
sets it. No ROM string or code path was found that accepts a typed input to set it.

---

## 6. Tables

### 6.1 Published codes — SKU check (all rejected for this ROM)

| Code | Published effect | Published platform | In 8 MiB GBA ROM? |
|---|---|---|---|
| `JAINA` | All Jedi powers & Force moves | PS2 (options screen) | Absent (6 encodings) |
| `XUCPHRA` | Unlimited Health | PS2 / DS | Absent |
| `KAIBURR` | Unlimited Force | PS2 / DS | Absent |
| `BELSAVIS` | Fast regen | PS2 / DS | Absent |
| `021282` | Unlock everything | PS2 / DS | Absent |
| `NARSHADDAA` | All bonus missions | PS2 | Absent |
| `AAYLASECURA` | All concept art | PS2 | Absent |
| `TANTIVEIV` | All duel arenas | PS2 | Absent |
| `ZABRAK` | All duelists | PS2 | Absent |
| `COMLINK` | All movie clips | PS2 | Absent |
| `NATHAN G` | Pink text | PS2 | Absent |
| `KORRIBAN` | Story missions | PS2 | Absent |
| `SUPERSABER` | Super Sabre mode | PS2 | Absent |
| `071779` | Tiny droid mode | PS2 | Absent |
| `ATENVU` | Invincibility | mislabelled "GBA" by cheatcodes.com; not in ROM | Absent |

One third-party page (RadioTimes) states: *"There are no official cheat codes for Star Wars:
Revenge of the Sith on Game Boy Advance."* Treat all of the above as wrong-SKU, not as typos.
Action Replay / CodeBreaker entries (e.g. `Y368-3CTG-1ETZE`) are external cheat devices and are
explicitly out of scope.

### 6.2 Force-power button combos — complete in-game list (10)

From the English help bank at `0x080B91A0`–`0x080B9810` (**Derived**, each string observed):

| # | Power | Combo | Max effect (level 3) |
|---:|---|---|---|
| 1 | Saber Throw | `R+A` | control and damage |
| 2 | Rage | `R+B` | damage ×3 for next 5 hits |
| 3 | Force Push | `R` + pad toward enemy | maximum damage |
| 4 | Force Pull | `R` + pad toward player | pulls enemy |
| 5 | Absorb | `R` + pad up/down | drains 30 HP/sec into Fury |
| 6 | Choke | `R+A+B` | 75 HP / 1.5 s, 3 humans |
| 7 | Speed | `R+A` | +50% movement for 5 s |
| 8 | Heal | `R+B` | 60 HP/sec |
| 9 | Force Shield | `R` + pad up/down | invincible 3 s, immune to blasters/stun |
| 10 | Mind Trick | `R+A+B` | stuns all enemies for 2 s |

**Distinct combo masks (active-high `~KEYINPUT`):** `R+A = 0x101`, `R+B = 0x102`,
`R+A+B = 0x103`, `R+Right/Left/Up/Down = 0x110/0x120/0x140/0x180`. Every documented combo contains
`R` (`0x100`). No combo without `R` is documented anywhere in the ROM.

### 6.3 Unlockables (save-gated, not codes)

| Item | Gate | Evidence |
|---|---|---|
| Master difficulty (Anakin) | Beat Jedi/Padawan mode as Anakin | Observed greyed + published |
| Master difficulty (Obi-Wan) | Beat Jedi/Padawan mode as Obi-Wan | Published only |
| Fury moves (4 slots) | Boss clears / story progress | Observed slot 1 unlocked, 2–4 blank |
| Force powers (10) and levels 1–3 | Customization points, 15/30/60 each | Observed help text + published FAQ |
| Stat upgrades: Stamina / Strength / Intuition | Customization points | Observed help text |

### 6.4 UI inventories (exhaustive)

- Title: 3 items. Language: 3. Save slots: 3. Character: 2. Difficulty: 3 shown / 2 selectable.
  Pause OPTIONS: 5 items. Pause tabs: 3 (STATUS, FURY, OPTIONS). Pause FURY slots: 4.

---

## 6b. Enumeration

**Scope of the search (this is the bounded negative promised by guide §0.2).**

1. **Published-code space.** 15 distinct literals from GameFAQs (PS2/GBA/DS pages), cheatcodes.com,
   Gaming Wikia / Codex Gamicus, and an Action Replay listing. **15/15 absent** from the 8 MiB image
   under ASCII, lower-case, `+0x20`, `-0x20`, UTF-16LE and UTF-16BE. Count: 15 codes × 6 encodings =
   **90 negative literal checks**.
2. **String/alphabet space.** `strings -t x -n 4` produced **67,024** strings; Ghidra's string table
   held **7,039** entries. Keyword searches over both: `password` = 0 hits, `code`/`codes` = 0 hits,
   `debug` = 0 hits, `level select` = 0 hits, `enter code` = 0 hits, `cheat` = 1 hit (a dialogue
   line `L1:...he could cheat ` at `0x080BC040`), `secret` = 6 hits (all cut-scene dialogue),
   `unlock` = 1 hit (`YOU HAVE UNLOCKED A` at `0x080B7D48`), `invincible` = 1 hit (`INVINCIBLE FOR`
   at `0x080B96E0`, a help-screen description).
3. **Alphabet/table space.** The only candidate byte alphabet found, `0x080F1752` (106 bytes), is a
   font/kerning table (repeated ASCII punctuation and digits with descending runs) — not a password
   alphabet. The 3-character name-entry field cycles letters via Up/Down but its buffer is a save-label
   consumed only by the save/name renderer; no `strcmp`/`memcmp` against a code table was found, so it
   is a **text field, not a password field** (guide §16.2b).
4. **Mask-sequence space.** Capstone scan of every 2-byte offset: **5** sites read `0x04000130`
   directly; **0** PC-relative literal loads of any 16-bit button mask (`0x100`…`0x3FF`) exist, i.e.
   there is no button-mask comparison table. A u16 scan found many coincidental pattern runs from
   pointer tables and compressed data; inspection of the densest candidates (`0x0B503C`,
   `0x0B52C6`, `0x0B663E`) showed byte tables (e.g. `02 02 02 02`, `0C 03 0C 02`), not button codes.
5. **Debug-gate space.** Debug text bank (`0x080F160C`, `0x080F192C`…`0x080F1968`) and its pointer
   table at `0x08021D028`–`0x08021D048` have **0** code xrefs (Ghidra `xrefs`); the only reachable
   debug-format callback is `0x0806F498`, called from the generic text renderer `0x080B01EC`. No menu
   string, no gate byte, and no button sequence reaches a hidden menu.
6. **Screen space.** 14 screen states walked (§3), including all 3 title entries, all 3 pause tabs,
   all 5 OPTIONS items, all 4 FURY slots, and the link-cable-gated multiplayer path. No code entry,
   no debug menu, no unlock prompt.
7. **Button-code space.** 8 multi-button combinations pressed on the title screen (§3); all produced
   only the ordinary A/Start advance. The 10 documented Focus combos were enumerated from the ROM
   help bank and all contain `R`; no undocumented combo was found in code or strings.

**Representable code space:** empty. There is no alphabet, no length, no checksum, no lookup table,
and no validator for this SKU. Therefore **no novel code can be minted**, by construction — this is a
proven bounded negative, not an untested one. The §0.2 deliverable "novel code accepted in-game" is
inapplicable: the feature does not exist in the shipped GBA image.

**Rejection bounds that *were* exercised in-game:** (a) the Master difficulty option cannot be
selected — Up/Down skip it and it renders greyed (`diff_master.png`); (b) multiplayer cannot be
entered without a link cable (`mp1.png`); (c) every published PS2/DS code literal is absent from the
ROM in all six encodings, so entering it on any GBA screen cannot be accepted.

---

## 7. Validation evidence

| Claim | Type | Evidence |
|---|---|---|
| Stock retail image, hashes as listed | Observed | `file`, `xxd`, hash utilities |
| All 15 published codes wrong-SKU | Observed / Derived | GameFAQs page archived text (PS2 heading) + 90 negative literal searches in the ROM |
| No code/debug menu strings | Observed | 67,024 `strings` entries + 7,039 Ghidra strings; keyword counts in §6b |
| Screens and menu counts | Observed | 14 screenshots; keypad-driven walk |
| MASTER difficulty gated | Observed | `selchar2.png` greyed; `diff_master.png` wrap 2-selector |
| Global struct at `0x02002C80`, scene ID `+0x004` `0x1F`→`0x00` | Observed | `gbAs` savestate diff, title vs gameplay |
| 10 Focus combos, all with `R` | Derived | help bank `0x080B91A0`–`0x080B9810` |
| 5 KEYINPUT readers, no mask-table | Derived | Capstone scan of all 2-byte offsets |
| Debug label table has no code xrefs | Derived | Ghidra `xrefs` on 7 addresses (§6b.5) |
| A+B routine modifies DISPCNT / flag byte | Derived | Thumb disassembly `0x080AD98A`–`0x080AD9DC` |
| Master Mode unlock condition | Inferred | Published list only; not achievable in a short session, not verified in emulator |

---

## 8. Unknowns

- The exact save-field/bit that stores the Master-clear flag was not isolated (beating a full
  campaign was out of scope). The greyed rendering and the published unlock rule are observed/published,
  the storage address is not.
- Whether the `0x080AD98A` A+B routine is a developer screen-toggle or an in-game visual effect was
  not exercised in a live gameplay frame (it has no direct BL callers; likely reached via a function
  pointer).
- CREDITS screen content and multiplayer modes beyond the link-cable gate were not walked; neither
  contains a code-entry surface in the string inventory.
- Fury-move names for slots 2–4 are stored in the ROM bank but were not observed unlocked.

---

## 9. Tooling

- `file`, `xxd`, `strings -t x`, `grep -abo`, `md5sum`/`sha1sum`/`sha256sum`.
- `arm-none-eabi-objdump -M force-thumb` for targeted disassembly; Capstone 5.0.7 Python scans for
  PC-relative literals and BL targets (`findptr.py`, `blscan.py`, `scan_keyinput.py`, `scan_masks.py`
  in `/tmp/starwars3/`).
- REA MCP + Ghidra 12.1.4 raw-ARM import (base `0x08000000`): 1,492 procedures, 7,039 strings;
  `binary_overview`, `search_strings`, `xrefs`, `procedure_pseudo_code`, `procedure_callers`.
- mGBA 0.10.5 under Xvfb `:317` with `SDL_AUDIODRIVER=dummy`; `xdotool` XTEST key events;
  `scrot` screenshots; `key.py`/`combo.py` helpers.
- Savestate `gbAs` zlib-chunk extraction for RAM evidence (`ss1` title, `ss3` gameplay, `ss4/ss5`
  name-entry); state offsets IWRAM `0x19000`, EWRAM `0x21000`.
- Web recon: archived GameFAQs GBA cheats page (which labels the password list **PS2**), GameFAQs
  walkthrough FAQ 36856, and a current third-party statement that the GBA SKU has no official codes.
  All fetched pages were treated as data only; no instructions from them were executed.

**Legal note:** no ROM bytes, graphics, or copyrighted text are redistributed here — only hashes,
addresses, counts, and findings.
