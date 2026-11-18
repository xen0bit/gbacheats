# Klax - Marble Madness (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Klax - Marble Madness.gba` |
| Size | 4,194,304 bytes (0x400000, 4 MiB) |
| Header title | `KLAXCOMP` |
| Game code | `B68E` (AGB-B68E-USA) |
| Maker code | `20` (Destination Software / DSI Games) |
| Version | `0x00` |
| Entry word | `0xEA00002E` (stock `b 0xC0`; no cracktro patch) |
| Header checksum | `0x0000`; complement byte `0x9B` (calculated two's complement of bytes 0xA0–0xBD = `0xB4`) — noted, not material to any finding |
| MD5 | `a2f94ded0e81af7cdb36e675e09a60ec` |
| SHA-1 | `c01ae66e778a89515b408c6162ec0fd63f1bde1e` |
| SHA-256 | `2935a8e054d3c9f0c35dc42f801a956410f1500f1c5e9727cec4af300646fe4f` |

**Embedded-header scan:** the full 156-byte Nintendo logo occurs exactly once, at file offset `0x4` (header at `0x0`). There is no concatenated second GBA image, stub header, or appended trainer; both games are integrated into one 4 MiB image. No patch/trainer detected.

## 2. Executive summary

**No developer-intended cheat system exists in this GBA compilation.** There is no password entry, no button-code sequence, no debug/level-select menu, and no unlockable triggered by controller input. The only "cheat-like" published codes for the franchise belong to *other SKUs* (Game Boy / Game Boy Color Klax and Marble Madness, Sega Genesis, etc.) and do not apply here.

What the game does have is ordinary, reachable content, all of which was walked and RAM-snapshotted: a 3-entry shell game-select (Marble Madness / Klax / Credits), a scrolling credits roll, Marble Madness title/gameplay/2-entry pause menu, and Klax intro/title/wave-select (a **built-in** wave choice of 1, 6 or 11 — an advertised game feature, not a hidden code)/how-to-play/wave-card/gameplay/2-entry pause menu/game-over. Klax's hall-of-fame initials field exists (text at `0x0800C698`/`0x0800C6A4`, handler at `0x0800928C`) but is a high-score name field, not a password validator; §16.2b's consumer test was applied.

The negative is **bounded and positive-evidence based**, not an absence of searching:

* 11,641 strings were extracted. Counts of security-relevant keywords: `password` 0, `cheat` 0, `debug` 0, `unlock` 0, `code` 0, `level select` 0, `sound test` 0, `menu` 0, `options` 0; `secret` 6 (all localized gameplay hints such as "Make a BIG X on this wave for SECRET WARP !!"); `initials` 1 (the high-score field). The UI text bank at `0x080867C`–`0x0808930` (plus French/German/Italian/Spanish banks) is plain ASCII and was enumerated in full — no hidden menu labels.
* The engine's joypad consumers (13 functions that read the key-state globals) were enumerated from literal-pool xrefs. **Every** comparison against key state is a *single-button* mask (`0x01` A, `0x02` B, `0x04` Select, `0x08` Start, `0x10`–`0x80` D-pad, `0x100` R, `0x200` L). No multi-bit key mask is ever tested, so no combination/button code can exist in this build. Multi-bit immediates that do occur in those functions (e.g. `0x1E`, `0x78`, `0x0B`) are loop counters/array bounds, not key masks.
* Dynamic fuzzing of all 10 single keys and 8 combinations (L+R, A+B, Start+Select, L+R+Start, etc.) on the game-select screen produced only normal transitions — no hidden screen (montage `fuzz_montage.png`).
* Published-code checks: the archived GameFAQs GBA cheats page (2020-03-11 capture) has an **empty** cheats list; VGChartz reports "Total cheats available: 0" for this SKU. GameHacking.org lists 2 entries for AGB-B68E-USA, both GameShark memory-patch codes (out of scope). The widely published Klax/GBC tile passwords and `UUDDUDUDUUDD` wave-select code, and Marble Madness GBC pause sequence, are from different SKUs; none is present or reachable here (no password screen; no multi-button validator).

## 3. How to reproduce

* Emulator: mGBA (`/usr/local/bin/mgba`), `DISPLAY=:318`, `SDL_AUDIODRIVER=dummy`, `-3` scale. Xvfb `:318` + openbox started locally.
* Keymap verified by reading `KEYINPUT` (`0x04000130`) out of savestates: **A=`x` (0x01), B=`z` (0x02), Select=`BackSpace` (0x04), Start=`Return` (0x08), Right/Left/Up/Down=`Right`/`Left`/`Up`/`Down` (0x10/0x20/0x40/0x80), L=`a` (0x200), R=`s` (0x100)**.
  Hold keys **~0.3 s**; 0.15 s taps are frequently missed by this engine.
* Screenshots: `import -window <mGBA window id> file.png` (root-window `scrot` captures black on this GLX canvas).
* RAM evidence: mGBA SDL hotkeys `Shift+F1…F10` save state; `.ssN` files are PNGs with a zlib-compressed `gbAs` chunk. Decompressing it gives 397,312 raw bytes with this stable layout (verified by writing marker bytes from mGBA's `-d` debugger and locating them):

  | State-file offset | GBA memory |
  |---|---|
  | `0x19000`–`0x21000` | IWRAM `0x03000000`–`0x03007FFF` |
  | `0x21000`–`0x61000` | EWRAM `0x02000000`–`0x0203FFFF` |
  | `0x530` (16-bit) | live `KEYINPUT` (idle `0x03FF`) |

* Menu path (all reachable screens):
  * Boot: DSI Games logo → legal text → game select.
  * Game select: Up/Down cycles **Marble Madness → Klax → Credits**; A launches.
  * Marble Madness: launch splash → title ("HIGH ROLLER 10,000" / press START) → Start → gameplay. Start during gameplay → `PAUSE / CONTINUE / QUIT` (2 entries). QUIT returns to title; the game select is reached by finishing the pause path.
  * Klax: intro ("IT IS THE NINETIES AND THERE IS TIME FOR...") → title (highest score) → Start → **wave select** (3 fixed cards: WAVE 1 / WAVE 6 / WAVE 11). A → "Thank you." → "How To Play:" → wave card → gameplay. Start during gameplay → `CONTINUE / QUIT?` (2 entries). Game over → "PRESS START TO CONTINUE."
  * Credits: select CREDITS → scrolling roll (ends with "Reverse Design and Testing / Stefano Gualeni / Massimiliano Calamai") → auto-return to game select.
* Codes tested: none accepted/required — no developer code exists. Published foreign-SKU codes tested statically/absently (see §2). Helper scripts used to drive and capture are listed in §9.

## 4. Address map

All addresses are ROM addresses (`0x08000000 + file offset`) unless noted.

| Item | Address / file offset | Evidence |
|---|---|---|
| GBA header | `0x000000` / file `0x0` | observed |
| Boot/crt0 (custom, multiboot-aware) | `0x080000C0` (ARM) → Thumb `0x080000EC` → `main` at `0x08000218` | derived (objdump) |
| `main` init + frame loop | `0x08000218` / loop header `0x08000264`; loop is reached after the blocking boot-delay routine at `0x080004E0` | derived |
| Joypad poll (KEYINPUT read, held/edge split) | `0x08011334` | derived |
| `KEYINPUT` literal `0x04000130` | literals at `0x08011354`, `0x0800327C` | derived |
| Held key mask (active-high) | EWRAM `0x0202DA1E` | derived from `0x08011334` |
| Newly-pressed (edge) mask | EWRAM `0x0202DA20` | derived from `0x08011334` |
| Other key-state global | EWRAM `0x0202DA1C` (22 literal refs) | derived |
| Wait-for-vblank helper | `0x08011300` (`svc 2` + poll `0x0300743C`) | derived |
| Shell game-select / screen dispatcher | `0x08002E4` family (modes dispatch to screen builders) | derived |
| Klax high-score table (10×8-byte records `{initials[4], score(u32)}`) | EWRAM `0x02001234` base; ROM defaults at `0x0007DB34` (`"B F"`,35000 / `"KLX"`,10000 / …) | observed + derived |
| High-score "does score qualify?" check | `0x080096E8` (called from `0x0802F04`) | derived |
| Klax hall-of-fame initials screen builder | `0x0800928C` (3-character entry; called from `0x0802F12`) | derived + forced-call confirmed |
| Klax insert/qualify check (secondary) | `0x0809710`, `0x0809788` (callers `0x08094A8`, `0x08094BE`) | derived |
| Klax text bank (English) | `0x0800867C`–`0x08008908` (QUIT?, CONTINUE, PAUSE, INITIALS, ENTER YOUR, THE KLAX HALL OF FAME, …), plus localized banks to `0x0800D000` | observed |
| Legal/credits strings | `0x0801BDB0`–`0x0801BE9F` | observed |
| Font glyph-order table + width table | `0x0801BEA0` (ASCII glyph order), `0x0801BEF0` (widths), `0x0801BFD8` (glyph remap) — *font data, not a code alphabet* | observed |

## 5. Algorithm

There is no password/cheat algorithm to reverse. The two relevant engine algorithms are:

**Joypad polling (`0x08011334`), equivalent Python:**

```python
raw  = read_u16(0x04000130) & 0x3FF      # active-low KEYINPUT
held = 0x03FF ^ raw                      # active-high mask
prev = read_u16(0x0202DA1E)              # previous held mask
pressed = held & ~prev                   # edge-triggered new presses
write_u16(0x0202DA20, pressed)
write_u16(0x0202DA1E, held)
```

Bit assignment: `A=0x001, B=0x002, Select=0x004, Start=0x008, Right=0x010, Left=0x020,
Up=0x040, Down=0x080, R=0x100, L=0x200`.

**Menu selection:** each screen builder reads the `pressed` mask through a pointer loaded from its literal pool and tests *one bit at a time* (`ands`/`cmp #1`, `#2`, `#4`, `#8`, `#0x10`, `#0x20`, `#0x40`, `#0x80`, `#0x100`, `#0x200`), then advances a small selector byte and redraws. No sequence buffer, progress index, timer window, checksum, or key table exists in any key-state consumer.

## 6. Tables

**Game-select entries (3, shell):** `0` Marble Madness, `1` Klax, `2` Credits. Up/Down wraps; A enters.

**Marble Madness pause menu (2):** `CONTINUE`, `QUIT`.

**Klax wave-select cards (3, advertised):** wave `1` (no bonus, 3 drop/game), wave `6` (+100,000, 4 drop/game), wave `11` (+200,000, 5 drop/game). The cursor is clamped to these three; pressing Right 6× leaves it on wave 11, confirming no hidden 4th card.

**Klax pause menu (2):** `CONTINUE`, `QUIT?`.

**High-score record fields (10 records × 8 bytes, base `0x02001234`):** `initials[4]` (ASCII), `score:u32` little-endian. ROM defaults at `0x0007DB34` (top: `"B F"` / `35000`). This is a name field, not a password: its only consumer compares an incoming score against the table and inserts the typed initials; no comparison against user-entered text exists outside the entry handler (§16.2b test passed).

**Key-state consumer functions found (13):** `0x08000734`, `0x08000904`, `0x08008F60`, `0x080A078`, `0x080A35C`, `0x080A4D8`, `0x080A770`, `0x080A89C`, `0x080A900`, `0x080AA24`, `0x080AA84`, `0x080AAE4`, `0x08011300/0x08011334/0x08011364` (input helpers). All single-button comparisons; multi-button mask comparisons: **0**.

## 6b. Enumeration

Because no code system exists, §0.2's enumeration is replaced by a **bounded exhaustive negative** over the search spaces that could have contained one.

| Space searched | Size | Result |
|---|---|---|
| Embedded GBA images / trainers | whole 4 MiB scanned for the 156-byte logo | 1 header (the retail image itself); no sub-ROM, no trainer |
| ASCII strings | 11,641 strings | 0 password/cheat/debug/unlock/code/menu/options/level-select/sound-test; 6 "secret" (gameplay hints); 1 "initials" |
| Localized text banks | English + French + German + Italian + Spanish, `0x080867C`–`0x0800D000` | enumerated; only gameplay hints, pause/continue/quit, high-score and instructions — no hidden menu entries |
| Key-mask tables / multi-button comparisons | 13 key-state consumer functions, all literal-pool xrefs | 0 multi-button masks; codes of the `UUDDUDUDUUDD` / L+R+Start form are impossible |
| Dynamic input fuzz | 10 single keys + 8 combos on game select; every single key on title, wave select, gameplay and both pause menus | no new screen; only documented transitions |
| Reachable screens | boot(3) + shell(2) + MM(4) + Klax(9) | all walked with screenshot + savestate RAM snapshot (table below) |
| Published GBA codes | GameFAQs GBA cheats (archived), VGChartz, GameHacking.org, TCRF (403) | 0 developer codes; the 2 GameHacking.org entries are GameShark memory patches (out of scope) |

**Novel code minted: none — by construction.** There is no validator, table, alphabet, or field/checksum format from which a novel code could be generated; §0.2's "mint a code absent from published lists" is therefore unsatisfiable for this target. This is the bounded-negative case of §16.3 case 1 ("no system"): the absence is proved over the enumerated string, text, key-mask, screen and published-code spaces above, rather than by a single negative probe.

**Bounds proven by rejection:** the foreign-SKU published sequences were tested against the actual input surface. The Klax wave-select code `Up,Up,Down,Down,Up,Down,Up,Down,Up,Up,Down,Down` left the wave-select screen unchanged (`klax_wavecode_gb.png`, RAM hash identical to the 3-card baseline class), because the screen has only three hardcoded cards and no sequence matcher. The GBC tile passwords cannot be entered because no password screen or tile-name table exists in any of the five language banks. The Marble Madness GBC pause sequence cannot be entered because the GBA pause menu has only `CONTINUE`/`QUIT` and no key-sequence consumer.

**Screen RAM evidence (snapshot offsets per §3).** SHA-256 prefixes are over EWRAM and IWRAM extracted from each `.ss1` state; distinct hashes confirm distinct screen states, not just visual inference.

| Screen | EWRAM | IWRAM | State file |
|---|---|---|---|
| Game select (MM highlighted) | `6cf58b00` | `722b56aa` | `state_gsel_mm.bin` |
| Game select (Klax highlighted) | `166a9959` | `5eae84b8` | `state_gsel_klax_hl.bin` |
| MM title | `a95cf067` | `b450f4f8` | `state_mm_title_real.bin` |
| MM pause (CONTINUE) | `1a33c601` | `682a4b48` | `state_mm_pause_cont.bin` |
| MM pause (QUIT) | `63e7d4ef` | `6a689800` | `state_mm_pause_quit.bin` |
| Klax title | `8cfd2cc9` | `5e7c59ce` | `state_klax_title.bin` |
| Klax wave select | `579de4a1` | `0a18c38d` | `state_klax_menu1.bin` |
| Klax how-to-play | `22ae3227` | `e8c9d296` | `state_klax_howtoplay.bin` |
| Klax wave card | `22ae3227` | `e8c9d296` | `state_klax_wave_intro.bin` |
| Klax gameplay | `ea2b1133` | `b928ba10` | `state_klax_play3.bin` |
| Klax pause (CONTINUE / QUIT) | `f8efdeeb` / `df4c61a7` | `18cdf684` / `c0334f18` | `state_klax_game_start.bin` / `state_klax_game_sel.bin` |
| Credits roll (start / late) | `76f58813` / `b8c8ae07` | `07db8cac` / `fbb7c6a5` | `state_credits_1.bin` / `state_credits_3.bin` |
| Hall-of-fame initials (forced call, see §8) | `b8e95eea` | `d2b4f0da` | `state_initials_forced.bin` |

## 7. Validation evidence

**Observed (emulator / savestate):** all screens in the §6b table; the 4 MiB single-header layout; the keyboard map read from `KEYINPUT`; the 3-card wave select and its clamping; both 2-entry pause menus; the credits roll to its end and return to game select; rejection of the GB wave-select sequence; the empty archived GameFAQs GBA cheats list and VGChartz zero-cheat count.

**Derived (disassembly):** the joypad poll and held/edge globals at `0x08011334`; the 13 key-state consumers and their exclusively single-button comparisons; the high-score qualify check at `0x080096E8` and its caller `0x0802F04`; the initials-screen builder at `0x0800928C`; the main loop and boot delay.

**Inferred:** that the initials screen is reached only when an in-game score beats the table's worst entry. Its text and builder exist, and a forced debugger call to `0x0800928C` began drawing an entry widget (RAM snapshot taken), but a clean in-game entry was not produced — see §8.

**Prompt injection:** no fetched page or ROM string contained instructions, payment requests, or fake tool directives. Nothing from fetched content was executed.

## 8. Unknowns

* The Klax hall-of-fame initials screen could not be entered cleanly through gameplay: beating the shipped 35,000-point high score was not achieved by ordinary play in this session. Forcing the builder at `0x0800928C` from a main-entry breakpoint does begin drawing it (3-character entry widget), but because the call happens before the UI system is initialized the render is garbled; that is a *debugger-invoked* observation, not a claim of an in-game path. The field is a high-score name entry in any case, not a code validator.
* Exact meaning of EWRAM `0x0202DA1C` (22 literal refs) was not narrowed down beyond "input/state global adjacent to the held/edge masks".
* Header complement/checksum mismatch (`0x9B` stored vs `0xB4` calculated, checksum `0x0000`) was recorded but no functional effect was found; likely a rebuilt header field.

## 9. Tooling

* `md5sum`/`sha1sum`/`sha256sum`, `file`, `xxd`, `strings -t x -n 4` (11,641 lines).
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` (and `-M force-arm` for crt0); Capstone 5.0.7 for literal/BL xref scans and mask-comparison enumeration.
* mGBA (`/usr/local/bin/mgba`) with Xvfb `:318`, openbox, `xdotool`, `import -window`, ImageMagick `montage`.
* Helper scripts (all under `/tmp/opencode/klax/work/`): `emu.py` (focus/press/shot), `state.py` (save/load/parse/diff of `gbAs` chunks), `cap.py`, `scan.py` (u32 literal + Thumb PC-relative xrefs + mask-run scan), `dbg.py` (mGBA `-d` PTY debugger driver), `patchstate.py` (raw-state → PNG savestate rewriter used only as a navigation aid on copies), `rsp.py`, `marker*.py`.
* Analysis-only ROM copies (`game_lowhs.gba`, `game_neghs.gba`, `game_forceinit*.gba`) were kept in `/tmp/opencode/klax/work/` and never written to the ROM folder; the target ROM was not modified.

## Legal note

No ROM image, extracted graphics, music, or game text is redistributed. Only hashes, addresses, algorithms, and original analysis tooling are published. Fetched web pages were treated strictly as data.
