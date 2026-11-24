# Harry Potter and the Goblet of Fire (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Harry Potter and the Goblet of Fire.gba` |
| Size | 33,554,432 bytes (0x02000000, 32 MiB) |
| Header title | `POTTER G.O.F` |
| Game code | `BH8E` (region `E` = USA) |
| Maker | `69` |
| Version | 0x00 |
| Complement byte | 0xA5 (expected 0xBE from sum of 0xA0–0xBC — header was edited/rebuilt) |
| Header checksum | 0x0000 (scene-release rebuilt-header artifact, guide §16.1) |
| Entry word | 0xEA000030 → branch target 0x000000C8 |
| MD5 | `d228b8cfeda28ba875f3c355f04d53e3` |
| SHA-1 | `951f311d9a99920abdbb9134ac8b9d00dfdb9b0b` |
| SHA-256 | `ae9d6b9dcdf0f7454137c47eceba7e2affc9508e4460d594d3867937f23f8a88` |
| Developer / publisher | Magic Pockets / Electronic Arts, 2005 (ROM credit string at 0x12cc960; 3rd party cheat indexes) |
| Save type | 512-byte EEPROM (`.sav` created by mGBA at first boot) |

**Embedded-header scan:** the full 156-byte Nintendo logo occurs exactly **once**, at file offset 0x0 (ROM address 0x08000000). This is a single retail image, not a multi-game cart (§5.4b). No appended trainer or cracktro was found; the first 4 KiB is a normal ARM crt0 (the `0xEA000030` entry is a plain branch, not a scene cracktro patch). The rebuilt header (checksum 0, bad complement) is the only patched-header signal.

**Independence from the other Harry Potter images (verified):** this image's MD5, size, game code, entry word and header complement all differ from *Harry Potter and the Chamber of Secrets* (8 MiB, code `A7HE`, entry `0xEA00002E`, complement `0xB2`, MD5 `b9b42f3e2d54921ee657bc027fa364b9`) and from the concurrently analysed Prisoner of Azkaban / Sorcerer's Stone / Quidditch World Cup images (different filenames/codes). The maker code `69` is shared, but that is a header-tag coincidence, not shared code: addresses, text banks and engines are distinct. **Nothing is shared with Chamber of Secrets at the cheat/code level.** No fonts, tables, strings or routines were carried over between the two analyses.

## 2. Executive summary

**There is no developer-intended cheat-code system in this GBA image: no password entry screen, no button-code sequence, and no hidden/debug menu.** This is a bounded, evidenced negative (guide §0.2 point 5 / §16.3 "no system").

What the game *does* have is a normal collectible/unlockable progression layer, which is in-scope as "unlockables" but is **not** a code system:

- **71 Tri-Wizard Shields** (hidden in levels) → unlocks **Game Cutscenes** bonus (after an autosave).
- **74 Collector Cards** (found in levels, or bought with jelly beans at Weasleys' Wares) → unlocks **Movie Photo Gallery** bonus.
- **Yule Ball** rhythm minigame: **Music 1–4** and **Beginner / Intermediate / Advanced** difficulties unlock by achieving B-or-better grades (strings at 0x7762b1 / 0x776318; 3rd party cheat index walkthrough §5.5).
- **Mini-Games**, **House Booster card** and additional bonuses unlock via shield/card thresholds (strings at 0x12cd2ec, 0x12cd364, 0x12cd382).
- All of these are save-record bits written by **gameplay events** (pickup, grade threshold, shop purchase), not by any controller-input matcher. The save slot screen itself displays `0/71` shields and `4/74` cards, matching the published totals.

The only special button combination in the binary — **L + R + Select** — is the **documented Sleep-mode hotkey**, not a cheat. It is gated behind `flags & 0x10000` and byte `0x03002730 == 0x55`; forcing that gate in a patched savestate produced the on-screen message *"Sleep mode — To wake up the GBA, press L, R and SELECT simultaneously."* (screenshot `g41.png`). The two `"password"` strings in the ROM are story dialogue about the Prefects' Bathroom password, not a code. The many `"CODE"` strings at 0x1f04xxx are Shin'en GAX audio-chunk identifiers (`Sequence`, `CODE`), keyword false positives (§11).

Published GBA "cheats" are **Action Replay / GameShark memory-edit codes** (3rd party cheat indexes: `badf57721b426ca6` infinite health, `b3fe0ce591f41721` infinite beans) — explicitly out of scope. No password or button code is published for the GBA SKU on 3rd party cheat indexes.

## 3. How to reproduce

- **Emulator:** mGBA 0.10.5 SDL, `SDL_AUDIODRIVER=dummy`, `DISPLAY=:319`, `Xvfb :319 -screen 0 1024x768x24`, `openbox`, `mgba -3 <rom>`.
- **Keymap (verified empirically):** A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrow keys. Hold keys ≥60 ms; Start only opens the pause menu once the intro objective ("Get to the Portkey!") is finished.
- **Screen path (all walked, screenshots on disk in `/tmp/hpgof/`):**
  1. Language select (7 languages) → EA logo → title (`Press START`) → save slots (3) → Select = new game.
  2. Main menu (6 entries, cursor byte `0x020002C8` = 0..5): Single Player, Multiplayer, Options, Folio Universitas, Credits, Bonuses unlocked.
  3. Options (4): Music, Sfx, Light, Sleep mode.
  4. Folio Universitas (8 pages): Quidditch World Cup Composite, Defense Against the Dark Arts, Forbidden Forest, Triwizard–First Task Stadium, Yule Ball, Prefects' Bathroom, Care of Magical Creatures, Triwizard–Second Task Lake.
  5. Credits (roll), Bonuses unlocked ("No bonuses unlocked." on a fresh save).
  6. Single Player → character select (Harry/Ron/Hermione, all available) → stats → intro → gameplay.
  7. Pause (Start; 5 entries, same cursor byte 0..4): Resume, Folio Universitas, Options, Weasleys' Wares, Quit. Wares offers 6 cards for 40–150 beans.
  8. Multiplayer level carousel (4 levels): First Task, Yule Ball, Second Task, Third Task — all selectable on a fresh save. Starting Yule Ball solo gives *"No game found"* (needs a link cable).
- **RAM evidence:** mGBA `.ss1` savestates were decoded (PNG `gbAs` chunk → zlib → 397,312-byte raw state; IWRAM at raw 0x19000, EWRAM at raw 0x21000 — guide §16.13). The main-menu and pause-menu cursor was proven to be EWRAM `0x020002C8` (single-byte diff on each Down press; values 0..5 / 0..4).
- **Published codes tested:** none applicable (no password/button codes published for this SKU). The two Action Replay codes were inspected and classified as out-of-scope memory edits, not entered.

## 4. Address map

| Item | Address / offset | Notes |
|---|---|---|
| ROM header / logo | 0x08000000 | single logo hit; title at 0x080000A0 |
| Text bank (English UI strings) | file 0x12cc700+ | records are `04 <ASCII> 00`; contains Options, Choose level, Beginner/Intermediate/Advanced, Bonus strings, credits |
| Text bank (French copy) | file 0x12d10ce+ | parallel localized records |
| Level-name table | file 0x12cdd80–0x12cdef0 | internal IDs `T3-HUB1` … `LVL12-01`, `FINAL BATTLE`, **`TEST EA`**, **`L08-TEST`**, `WB-LVL01-01`, then 11 chapter names |
| Shield-award script block | file 0x13b3990 | `Shield!`, `$H0`, `Collect Triwizard Shields to unlock bonuses.`, `#22`, `#END` — collectible→flag path |
| Key-input / combo routine | 0x08060200–0x080602A0 (Thumb) | reads `0x04000130`; L+R+Select gate; sets/clears bit 0x00020000 of flags |
| Sleep-mode handler | 0x08060068 (Thumb) | disables IME, writes `KEYCNT` 0x04000132 = 0xC304, loops 240 rows, restores DISPCNT/BG regs |
| Sleep combo literals | 0x08060274 / 0x08060278 / 0x0806027C | `0x030024F0`, `0x03002730`, `0x3FF`; compared mask `0x304` (L+R+Select), gate bit `0x10000` |
| Input globals | IWRAM `0x030024F0` (flags word), `0x03002730` (gate byte, 0x55) | observed in every savestate |
| Menu cursor | EWRAM `0x020002C8` | observed 0..5 main menu, 0..4 pause |
| Shin'en GAX audio "CODE" chunks | file 0x1f04705+ | keyword false positive, not cheats |

## 5. Algorithm

No password algorithm exists. The only input-state machine found is the sleep hotkey:

```
; Thumb, 0x08060234
flags = *(u32*)0x030024F0;
if (flags & 0x10000) {                 // sleep feature enabled (Options)
    if ((s8)*(u8*)0x03002730 == 0x55) // module state magic
        if ((held & 0x3FF) == 0x304)  // L(0x200)+R(0x100)+Select(0x04), exact
            flags |= 0x00020000;
}
if ((flags & 0x00020000) && ((held & 0x3FF) == 0)) {
    sleep_handler_0x08060068();       // enters GBA sleep; shows sleep message
    flags &= ~0x00020000;
}
```

This is edge-triggered (press all three, then release all). Forcing `flags |= 0x10000` in a savestate and pressing the combination produced the sleep-mode message; the gate bit was never observed set in any normal play state, so the standard retail path is the Options "Sleep mode" toggle.

## 6. Tables

- **Menu item counts** (complete enumerations): language 7; main 6; Options 4; Folio 8 pages; pause 5; character 3; Multiplayer levels 4; Wares 6 offers/page; save slots 3.
- **Unlockable set** (all in-scope unlockables; none input-triggered):
  | Unlockable | Condition | Evidence |
  |---|---|---|
  | Game Cutscenes | all 71 Shields + autosave | 0x13b399e string; save slot `0/71`; 3rd party cheat indexes |
  | Movie Photo Gallery | all 74 cards | save slot `4/74`; 3rd party cheat indexes |
  | Music 1–4 / Beginner–Advanced (Yule Ball) | grade thresholds | 0x7762b1, 0x776318, 0x12cc7a0–0x12cc7f0; walkthrough §5.5 |
  | Mini-Games / bonus / House Booster card | shield/card thresholds | 0x12cd2ec, 0x12cd364, 0x12cd382 |
- **Button masks** (GBA active-high): A=0x001, B=0x002, Sel=0x004, Start=0x008, Right=0x010, Left=0x020, Up=0x040, Down=0x080, R=0x100, L=0x200. The only matched combination is 0x304 = L+R+Select (sleep).
- **Unused/dev level IDs:** `TEST EA`, `L08-TEST` appear only as entries in the internal level-name table (0x12cde00–0x12cde0c). They are not selectable from any menu (level select shows the 11 story chapters and 4 multiplayer levels); classified as unused/dev labels (guide §16.3 cut/dead content), not a hidden level select.

## 6b. Enumeration

**This engagement is a bounded negative: the code space is empty, so the enumeration is of the search space and of the unlockable (collectible) space.**

- **Text space searched (counts):** `strings -n 3/4` over all 33,554,432 bytes; keyword hits — `password` **2** (both story dialogue), `cheat` **0**, `debug` **0**, `secret` **0**, `unlock` **24** (all collectible/bonus messages), `code` **28** (all Shin'en audio `CODE`/`Code: B.Wodok`). Re-searched with the `+0x20` lowercase→uppercase shift and UTF-16LE: **0** additional password/cheat/debug/secret hits. The password entry alphabet was searched as `ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789` and variants: **0** occurrences. ASCII alphabet runs are absent → no plaintext code table.
- **Button space searched:** scanned the whole ROM for the 10-press Konami sequence and its reverse as `u16` masks (0 occurrences), for 3-press prefixes (0 occurrences), and for the only 0x04000130 KEYINPUT literal sites (3: 0x08060204, 0x08061ADC, 0x08063CC0). The single input matcher found is L+R+Select = sleep mode. No undocumented action branch exists in that dispatcher (it has exactly one action call, 0x08060068).
- **Screen space:** every reachable screen listed in §3 was entered and screenshotted; no text-entry field, no hidden menu entry, and no unlabelled cursor slot was found. The menu cursor was RAM-verified on both the main menu and pause menu.
- **Code space size:** 0 expressible passwords/button codes. No generator/validator pair, no key-mask table, no checksum, no reserved bits. The "space" is therefore empty and there are no unpublished codes to mint.
- **Unlockable space (characterised, not a code):** 71 Shields + 74 Cards; bonuses at the two full-set thresholds; Yule Ball music×difficulty matrix (4×3) gated by grade; mini-games gated by shield thresholds. Because the setters are gameplay events (script block at 0x13b3990, shop at pause→Wares, grade checks), no controller input can set them outside normal play — the §16.18 "save-bit unlock is not a code" case.
- **Bounds proven by rejection:** entering Multiplayer→Yule Ball without a link cable is rejected with *"No game found"* (screenshot `g54.png`); the fresh save reports *"No bonuses unlocked."* (`g09.png`) and `0/71` shields / `4/74` cards (`g47.png`), i.e. the unlock gates are closed and only collectible progression opens them. The sleep hotkey requires the exact 3-key mask and the 0x55/0x10000 gate; a partial combination does not trigger it.

## 7. Validation evidence

- **Observed (emulator/screenshots/RAM):** all screens in §3; menu cursor `0x020002C8` stepping 0..5 and 0..4; sleep-mode message after forced gate (`g41.png`); *"No game found"* (`g54.png`); save counters `0/71`, `4/74` (`g47.png`); Folio 8 pages; Wares 6 offers.
- **Observed (static bytes):** single Nintendo logo; text bank record format `04 <text> 00`; level-name table with `TEST EA`/`L08-TEST`; Shin'en `CODE` audio chunks.
- **Derived (disassembly):** L+R+Select gate and sleep handler at 0x08060234 / 0x08060068; flag word `0x030024F0`, gate byte `0x03002730`; no other key-input action branch.
- **Inferred:** `TEST EA`/`L08-TEST` are unused dev level labels (present in the name table, absent from every menu); the two `password` strings are story dialogue (context reads "Prefects' Bathroom … Password's…").
- **Negative result confidence:** high for "no password/button-code system, no hidden debug menu" — bounded by complete screen enumeration, full-ROM string/alphabet/mask searches with counts, and verification of all published material.

## 8. Unknowns

- Full playthrough of the single-player Yule Ball "Choose music / Choose level" difficulty screen was not performed (it requires story progression; the Multiplayer route needs a second console). Its existence and grade-gated unlocks are evidenced by the text-bank strings (0x12cc7a0–0x12cc7f0, 0x7762b1, 0x776318) and the 3rd party cheat index walkthrough, not by a screenshot of that specific screen.
- The exact writer of flags bit `0x10000` (the Options "Sleep mode" toggle) was not isolated; the gate was proven by forcing the bit in a patched savestate, which is labelled as a derived/forced test, not normal input.
- No claim is made that every internal script-level name (e.g. `L08-TEST`) is unreachable under every possible save state — only that none appears in any walked menu.

## 9. Tooling

- `arm-none-eabi-objdump -M force-thumb` for input-routine disassembly; Python 3 + Capstone 5.0.7 for literal/xref scans; `strings`, `xxd`, Python `struct`/`zlib` for headers and savestate decoding.
- Custom scripts in `/tmp/hpgof/`: `phase0.py`, `recon.sh`, `dump.py`, `static_scan.py`, `ptrscan.py`, `key.py`, `combo.py`, `savestate.py`, `ssdecode.py`, `ramtool.py`, `patchss.py`.
- mGBA 0.10.5 SDL under Xvfb :319, xdotool/scrot/ImageMagick for input and screenshots.
- Web: 3rd party cheat index cheat/walkthrough pages (via `web.archive.org` snapshots), 3rd party cheat indexes archived cheat page, 3rd party cheat indexes. Fetched pages were treated as data; no prompt-injection payload was observed in this session's fetches.

## Legal note

No ROM, save or copyrighted asset is redistributed here. Only hashes, addresses, algorithms, counts and original analysis scripts are published.
