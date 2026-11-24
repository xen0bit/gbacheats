# High Heat Major League Baseball 2003 (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `High Heat Major League Baseball 2003.gba` |
| Size | 4,194,304 bytes (4 MiB) |
| Header title | `HH MLB 2003` (`0xA0`) |
| Game code | `AHHE` (`0xAC`), maker `5H` (`0xB0`) |
| Version | `0x00` (`0xBC`) |
| Entry word | `0xEA00002E` — stock crt0 branch, not a cracktro patch |
| Complement / checksum | stored `0x4E` / `0x0000` (needed `0x67` / `0xA175`): rebuilt-header artifact (§16.1); no trainer or appended image |
| Embedded GBA headers | exactly one Nintendo-logo hit (file `0x04`) |
| MD5 | `22d31d959de4e87160ba308c95386799` |
| SHA-1 | `9eaee2c694b0be651be0e319df1c18fdbd721267` |
| SHA-256 | `bfaaefa6369572b37eb7470f59303f55c41cb5a048dd3ac385520e5093a1fe56` |
| Publisher/developer (external) | Mobius Entertainment / 3DO, GBA release 2002-03-05 |

Save hardware marker `EEPROM_V122` at file `0x62B20` (an EEPROM save image is created by mGBA at runtime).

## 2. Executive summary

**There is no developer-intended cheat system in this GBA image.** The evidence is closed, not merely "not found":

* There is no password entry screen, code alphabet, code table, validator, or hidden debug menu on any reachable screen.
* The full English text bank (file `0x5DDC8`–`0x62BFF`, 467 plausible multi-word ASCII strings) was extracted and reviewed: zero occurrences of *password / cheat / code / secret / unlock / hidden / debug* in ASCII, `+0x20`/`-0x20` shifted ASCII, UTF-16LE/BE, or any single-byte XOR (1..255).
* Every menu, submenu, in-game HUD and pause screen was walked with RAM-state evidence (digests in §7). All 8 top-level menu items, OPTIONS (6 items), the pause menu (9 items), team/lineup selection, Season, Playoffs, Home Run Derby, Practice, Credits and Link Game were visited. No hidden entry appears, and scrolling each list reaches its end and wraps.
* Button-code investigation: only **3** direct references to `KEYINPUT` (`0x04000130`) exist in the whole 4 MiB image, all inside the generic input routine. Its three test helpers have **36** BL call sites total; the only four-call cluster (`0x0800A96C`–`0x0800A99C`) is an ordinary menu D-pad handler (masks `0x20,0x10,0x40,0x80`). No sequence matcher, ring-buffer comparison, or action dispatcher for a cheat sequence exists. Four common combos (`L+R+Start`, `Start+Select`, `A+B+Select+Start`, Konami order) were pressed on the title screen and produced no hidden screen.
* The one plausible "hidden" item, a **31st team "Mobius Mercenaries"**, is provably unreachable by controller input: the team cycler at `0x080074B4` wraps at index 29, and the entry's filter byte `0x10` lies outside the complete reachable filter-key set `{2,3,4,5,6,7,8,9,10,11}` produced by the league/division selector tables. It is dead/leftover developer content, not an unlockable.
* Published codes: the archived 3rd party cheat indexes GBA page (game id **557704**) states verbatim **"No cheats - Be the first to submit one!"** and **"We Have No FAQs/Guides/Maps"**. CDX queries for archived cheat pages on 3rd party cheat indexes, cheatsguy, gamewinners and 3rd party cheat indexes returned no relevant URLs. Codes advertised for the GameCube/PS2/PC versions are console SKUs and are out of scope for this GBA image (and are memory-edit/GameShark style, excluded by the brief).
* §16.19's "call the validator as an oracle" technique is inapplicable: no validator function or code-accept path exists in this ROM to call.

**Result: empty enumerable code space (0 codes).** Sibling comparison: the concurrently analysed *High Heat MLB 2002* image is a distinct ROM (MD5 `62b5ee4401a0eec948817a69011e71d7`, game code `ASSE`, "Mobius Mercenaries" at `0x11E7C`, `EEPROM_V122` at `0x1540C`). It shares only the developer-team string and save-type marker (same Mobius engine); **nothing about cheats is shared — neither image has any**.

## 3. How to reproduce

* Emulator: `mgba -3 <rom>` under `Xvfb :316`, `SDL_AUDIODRIVER=dummy`, window manager `openbox`.
* Keymap (mGBA SDL defaults): `A=x`, `B=z`, `L=a`, `R=s`, `Start=Return`, `Select=BackSpace`, D-pad = arrow keys. Hold keys 120–250 ms; shorter taps are dropped.
* Boot order: Mobius splash → MLB legal notice → STATS Inc. notice → title (`PRESS START`) → `Return` → main menu.
* Main menu is an 8-item wrapping ring. Index order (verified by pressing Down through a full lap):
  `0 CREDITS`, `1 EXHIBITION`, `2 LINK GAME`, `3 SEASON`, `4 PLAYOFFS`, `5 HOME RUN DERBY`, `6 PRACTICE`, `7 OPTIONS`; select with `x`, back with `z`.
* Reproduce a negative screen check: save a slot-1 state (`Shift+F1`), copy `High Heat Major League Baseball 2003.ss1`, zlib-decompress its `gbAs` PNG chunk and hash the 397,312-byte state; compare with the digests in §7. Reload with `-t <state>` or `F1`.
* Codes tested: none exist to test. Button combos tested: `L+R+Start` (reached main menu, nothing hidden), `Start+Select` (no hidden screen), `A+B+Select+Start` (normal copyright/credits screen), `Up Up Down Down Left Right Left Right B A` (menu navigation only).
* Published-code verification: archive URL
  `https://web.archive.org/web/20181126003843id_/https://gamefaqs.gamespot.com/gba/557704-high-heat-major-league-baseball-2003`
  (fetched 2026-11-18) — "No cheats" as quoted above.

## 4. Address map

| Item | File offset / address | Notes |
|---|---|---|
| Header / title / code | `0x0000` / `0x00A0` / `0x00AC` | single logo hit at `0x04` |
| English text bank | `0x5DDC8`–`0x62BFF` | NUL-terminated mixed-case ASCII, rendered as uppercase via font tile conversion |
| Team names | `0x5DE24`–`0x5E054` | 31 names, last is "Mobius Mercenaries" |
| Team table | `0x0805E068` (file `0x5E068`) | 31 × `{u32 name_ptr, u32 filter_byte}`; index 30 filter = `0x10` |
| Division selector tables | `0x0805DDE0` (`National=1, American=0`) and `0x0805DE0C` (`Central=2, East=4, West=8`) | supply the two filter bytes |
| Team cycler / filter check | `0x080074B4`, bound at `0x080074E2`–`0x080074E8` | `adds r4,#1; cmp r4,#29; ble`; `ldrb r1,[r6,r0+4]; orr; cmp` |
| KEYINPUT references | `0x08000D20`, `0x08001AD4`, `0x08001B38` | only three in the image |
| Input test helpers | `0x08001B50` (held), `0x08001B6C` (pressed), `0x08001B88` (released) | 15 / 20 / 1 BL call sites |
| Key state/history | IWRAM `0x030054D8`, `0x030054E8`, `0x0300181E` | 128-entry history ring; no cheat matcher reads it |
| Save marker | `0x62B20` | `EEPROM_V122` |
| VRAM font | 8bpp tiles loaded on demand; "PRESS START" glyphs at tile indices `0x225`–`0x22F` | tilemap at VRAM `0xBC00` (screen base block 23) |
| Savestate layout | 397,312-byte `gbAs`: IWRAM `+0x19000`, EWRAM `+0x21000`, VRAM `+0x1000` | used for RAM evidence |

File offset → ROM address is `0x08000000 + offset`; no multi-image base adjustments were needed (single header).

## 5. Algorithm

There is no password/checksum algorithm to reimplement. The only recovered algorithm worth recording is the team-filter rule, which closes the hidden-team question:

```
league_key  = table_lo[league].value        # {National:1, American:0}  @ 0x0805DDE0
div_key     = table_div[division].value     # {Central:2, East:4, West:8} @ 0x0805DE0C
wanted      = league_key | div_key          # reachable set: {2,3,4,5,6,7,8,9,10,11}
team_index  = (team_index + 1)
if team_index > 29: team_index = 0          # 0x080074E2..0x080074E8
if team_table[team_index].filter == wanted: # 0x080074EC..0x080074E0
    accept team; load name pointer; play sound
else:
    try next index
```

Derived from Thumb disassembly at `0x080074B4`; **Derived** confidence, corroborated by the observed 30-team-only UI.

The text pipeline is: ASCII string from the bank → per-character glyph tile copied into 8bpp VRAM → BG0 tilemap at `0x0600BC00`, which is why `strings` found no menu labels although the visible text is identical (§11 lesson re-confirmed: text is **not** stored as tile indices; the font is loaded on demand).

## 6. Tables

* **Menu ring (8 entries)**: CREDITS, EXHIBITION, LINK GAME, SEASON, PLAYOFFS, HOME RUN DERBY, PRACTICE, OPTIONS — all reached and entered; each wraps.
* **OPTIONS (6)**: Sound Effects, Music, Brightness, Innings, Automatic Fielding, Back. No hidden rows.
* **Pause (9)**: Unpause, Sound Effects, Music, Brightness, Automatic Fielding, Line Up, Pitcher, Defensive Alignment, Quit Game. No hidden rows.
* **Team table (`0x0805E068`)**: 31 entries, indices 0–29 are the 30 MLB clubs with filter bytes in `{2,3,4,5,8,9}`; index 30 = "Mobius Mercenaries", filter `0x10`, name pointer `0x0805E054`. Unreachable (§5).
* **Filter-key set**: `{2,3,4,5,6,7,8,9,10,11}`; `0x10` is not a member.
* **Key masks** (GBA active-low, `~KEYINPUT & 0x3FF`): A=1, B=2, Select=4, Start=8, Right=0x10, Left=0x20, Up=0x40, Down=0x80, R=0x100, L=0x200.

## 6b. Enumeration

**Space definition:** empty. There is no alphabet, no code length, no checksum, no lookup of accepted codes, and no button sequence. Representable developer-intended codes = **0**.

**Complete search spaces and counts (negative bounded):**

| Space searched | Count | Result |
|---|---|---|
| ASCII strings ≥4 chars in whole image | 44,833 raw `strings` lines; 467 plausible English runs ≥8 chars with spaces extracted and reviewed | 0 cheat-related terms |
| Encodings for `password/cheat/secret/unlock/debug/code/hidden` | ASCII, upper, lower, `±0x20`, UTF-16LE, UTF-16BE, XOR 1–255 | 0 meaningful hits (13 short 4-letter XOR coincidences in compressed data, all rejected by context) |
| Team-name table entries | 31 | all enumerated; 1 unreachable leftover |
| Menu items (top level + OPTIONS + pause) | 8 + 6 + 9 | all visited; no hidden/unlabelled action |
| `KEYINPUT` literal references | 3 | only generic input routine |
| Input-helper call sites | 15 + 20 + 1 = 36 | 4-call cluster is a D-pad menu handler; no matcher |
| Button combos on title screen | 4 | no hidden screen |
| Archived cheat pages on 4 aggregators + 3rd party cheat indexes | 1 3rd party cheat index page found | explicitly "No cheats"; no cheat pages archived elsewhere |

**Novel code:** impossible by construction — no code system exists to mint from. This is a proven absence, not an untested feature; §0.2's "generate one unpublished code" deliverable is satisfied by a closed enumeration proving the space has cardinality zero, with every candidate surface counted above.

**Bounds proven by rejection:** the game cannot accept a code because no entry path exists. The closest analogue — selecting team 30 — is rejected by two independent mechanisms observed in the code: the `cmp r4,#29` wrap and the impossible filter byte `0x10` (§5). Pressing every menu direction through a full lap returns to the start rather than exposing a hidden row.

**§16.19 oracle:** not applicable — no validator exists to call from the debugger.

## 7. Validation evidence

**Observed** (emulator, screenshots and savestate RAM digests — 397,312-byte `gbAs` state, SHA-256 prefixes):

| Screen | State SHA-256 (16 hex) | IWRAM SHA-256 (16 hex) |
|---|---|---|
| Title (`PRESS START`) | `7be8a84625ce653f` | `0d3ffc517dbd3393` |
| Main menu | `d748d76122909a30` | `f104c4cbd81c0a6b` |
| CREDITS | `3e4d3e0ce78ef858` | `5ffa174557a67135` |
| EXHIBITION team select | `8c3a7c92e0b03cfb` | `ce20f911492593d2` |
| In-game lineup / scoreboard | `57cf6eae9a528e80` | — |
| Pause menu | `8597d857546f5794` | `fa9952d2e3d185be` |
| SEASON | `bd206ff028ab64af` | `b533472dae82fa55` |
| PLAYOFFS | `2e1c6c4960575df6` | `aead7c97c4637426` |
| HOME RUN DERBY | `08a9e88a83ae9a6a` | `3280c09224f96dc4` |
| PRACTICE | `9e96b014f22ede68` | `100ed7878a52045a` |
| OPTIONS (live GDB RAM dump) | — | `c6b111fb27bba3a1` |

Also Observed: "No Connection..." in LINK GAME; 30-team-only cycling in the UI; `EEPROM_V122` save file created; 3rd party cheat indexes "No cheats" page text.

**Derived:** the wrap-at-29 and filter-byte exclusion proving team 30 unreachable; the ASCII→tile font pipeline; the three input helpers' semantics; the text-bank bounds.

**Inferred:** that "Mobius Mercenaries" is leftover developer content (it is certainly unreachable; its *purpose* is not exercised by any code path found).

## 8. Unknowns

* No functional unknowns relevant to cheats. The purpose of the unused 31st team and of the `128`-entry key-history ring buffer (used by the generic input layer) was not attributed to a gameplay feature; neither is a code surface.
* Non-cheat gameplay behavior (pitching, season simulation) was not reverse engineered — out of scope.
* Some cheat-aggregator sites could not be reached (403 / CAPTCHA / Wayback 429); however the 3rd party cheat indexes GBA page, which normally carries a `/cheats` tab when codes exist, explicitly reports none, and CDX searches found no archived cheat pages for this title on the other four sites.

## 9. Tooling

* `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings`, `grep` for Phase 0/1.
* Python 3 with `capstone` 5.0.7 and Pillow 13.0.1: custom scripts `xref.py` (direct/Thumb-literal pointer scan), `blscan.py` (Thumb BL scanner), `parse_state.py` (`gbAs` zlib state parser), `render_tiles.py` / `tilemap.py` (8bpp VRAM font and tilemap decoding), plus inline scanners for encodings, text runs and key masks. Scripts were in `/tmp/highheat03/`.
* `arm-none-eabi-objdump -M force-thumb` for the team cycler and input helpers.
* `mgba -3` (GDB stub `-g` used early for live RAM/VRAM dumps), `Xvfb :316`, `openbox`, `xdotool`, `scrot`, `convert`, `tesseract` for Phase 2 screen walking.
* `curl` + Python HTML-to-text for archived 3rd party cheat indexes and Wayback CDX queries.
* No ROM or copyrighted assets are redistributed; only hashes, addresses, algorithms and observations are published.

### Legal / cleanup note

All generated emulator artifacts (`*.sav`, `*.ss1`) in the ROM folder were removed at the end of the run. Only the analysis processes owned by this session (PIDs recorded in `/tmp/highheat03/*.pid`) were terminated, by PID number; no `pkill` was used and no other display/session was touched.
