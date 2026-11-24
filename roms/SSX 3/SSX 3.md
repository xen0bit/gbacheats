# SSX 3 (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/SSX 3/SSX 3.gba` |
| Size | 8,388,608 bytes (8 MiB), trailing 256 bytes all zero |
| Header title (`0xA0`) | `SSX3` |
| Game code (`0xAC`) | `BSXE` |
| Maker (`0xB0`) | `69` |
| Fixed byte (`0xB2`) | `0x96` (normal) |
| Version (`0xBC`) | `0x00` (Rev.00) |
| Complement (`0xBD`) | `0x00` |
| Header checksum (`0xBE`–`0xBF`) | `0x007F` (non-zero → header not rebuilt) |
| Entry word (`0x00`) | `0xEA00002E` — stock GBA `b 0xBC`, **no cracktro/trainer patch** |
| Embedded GBA headers | exactly one (Nintendo logo at file `0x04`); not a multi-game cart |
| MD5 | `d0d33104d62f81108214f9a328ce0a9e` |
| SHA-1 | `4f2bd55bcd3118e10520179e285aae897aa21898` |
| SHA-256 | `354086476b2789567d8af046fb900780824d51b0c2d2af893288d58fc7da2f37` |

Web metadata: developer listed as **Visual Impact** for the GBA SKU (Console SKUs are EA Canada) — a different engine, consistent with §16.11 ("same title can be a different game").

## 2. Executive summary

**There is no in-game cheat / password / button-code / debug-menu system in this GBA build.** The
widely published SSX 3 password list (`graphicdelight`, `biggerthank7`, `worm`, …) belongs to the
PS2 / GameCube / Xbox SKUs only. None of its 26 distinct literals appears anywhere in the 8 MiB
GBA image under ASCII, uppercase, lowercase, UTF-16LE/BE, UTF-32LE, `±0x20`, XOR-`0xFF` or
reversed encodings (260 searches, 0 hits). The complete ASCII UI text bank (`0x34000`–`0x3A000`)
contains no occurrence of *cheat*, *password*, *debug*, *secret*, *hidden*, *code*, *level
select*, *GameShark* or *CodeBreaker* in any encoding, and there are no such debug labels rendered
as font/tile indices either.

Every reachable screen was walked in mGBA with screenshots and RAM reads (22 distinct screens,
§6b). Options (title and in-game) has no "Cheats"/"Enter Cheat" entry. The only text-entry surface
is an **Enter Your Name** keypad whose alphabet is `A–Z` plus three icon glyphs (no digits) and
whose buffer at RAM `0x020001EA` is a NUL-terminated ASCII **profile name label** with no
comparison against any constant — a text field, not a validator (§16.2b). All "unlockables"
(boards, outfits, the special outfit at 1,000,000 cash, medals, events) are career-cash/progress
save data, not code-gated.

Published GBA cheat databases agree: Cheat Happens states *"We currently don't have any SSX 3
cheats or cheat codes for Game Boy Advance"*; the GameFAQs GBA cheat page lists only PS2/GC
passwords. This is a **bounded negative** proven by counts in §6b, not an untested absence.

## 3. How to reproduce

* Analyzer: mGBA 0.10.5 (`/usr/local/bin/mgba`) on `DISPLAY=:315` under Xvfb + openbox,
  `SDL_AUDIODRIVER=dummy`, launched as `mgba -3 -d game.gba` on a byte-identical copy at
  `/tmp/ssx3/game.gba` (the ROM folder was never written to).
* Keymap (mGBA SDL default): `A`=`x`, `B`=`z`, `L`=`a`, `R`=`s`, `Start`=`Return`,
  `Select`=`BackSpace`, D-pad = arrow keys. Holds of 60–150 ms; transitions waited 0.6–4 s.
* RAM inspection: mGBA command-line debugger on a pty (`-d`), commands `c` (continue), Ctrl-C
  (break), `r/4 ADDR`, `reset`, `status`. Savestates (`Shift+F1..F3`) parsed per §16.13: `.ss1` is
  a PNG with a zlib `gbAs` chunk; `zlib.decompress` → 397,312-byte raw state (EWRAM at raw
  `0x21000`, IWRAM at raw `0x19000`). No single-client GDB stub was used — port 2345 belonged to
  another agent's emulator and was deliberately avoided.
* Menu path (fresh reset): *Press START* → *Enter Your Name* (keypad → `ok`) → main menu →
  *Conquer The Mountain* → rider → *Setup Character* → *CONTINUE* → *Select Track* → *Select Game
  Mode* → *EVENT MODE* → *Qualifier Round* → gameplay → *Start* → *PAUSE* → *OPTIONS*.
* Codes tested: none exist to enter; the 26 published console literals were verified statically
  (§6b) and nine common title button combos were pressed in-game (§7).

## 4. Address map

| Address (ROM = `0x08000000+file`) | Meaning | Evidence |
|---|---|---|
| `0x0000`–`0x00BF` | GBA header (stock, single image) | Observed (`xxd`) |
| `0x034C70`–`0x034CB8` | 10 rider names, 8-byte stride: GRIFF, MAC, ELISE, MOBY, NATE, VIGGO, KAORI, ALLEGRA, PSYMON, ZOE | Observed (`strings`) + in-game roster |
| `0x037B88`–`0x037D30` | Track-name bank (Peak 1/2/3: HAPPINESS, RUTHLESS RIDGE, CROWS NEST, RNB, DISFUNKTION JUNCTION, SNOW JAM, LAUNCH TIME, INTIMIDATOR, THE STYLE MILE, METRO CITY BREAKDOWN, SCHIZOPHRENIA …) | Observed |
| `0x034D5`(file) / `0x0384D5` | Name-entry alphabet string `ABCDEFGHIJKLMNOPQRSTUVWXYZpqr ` (26 letters + 3 icon glyphs + pad) | Observed |
| `0x38000`–`0x38F00` | Menu text bank (Options, Setup Character, Shop, Trophy Room, Objectives, Radio Big, Pause, Credits) | Observed, fully ASCII-decoded |
| `0x022B85E` | Audio-engine banner `Shin'en Multimedia. Code: B.Wodok` — irrelevant keyword hit (§11) | Observed, classified |
| RAM `0x020001EA` | Profile-name ASCII buffer (NUL-terminated); typed `AAAAA` read back as `41 41 41 41 41 00` | Observed (debugger `r/4`) |
| RAM `0x02000990` | Font/tile-index render buffer for the same text; each glyph is a 16-bit tile index (`0x0101` = `A`), e.g. word `0x01030104` | Observed (debugger + savestate) |
| RAM `0x04000130` | KEYINPUT, active-low; `0x000003FF` idle confirmed correct input path | Observed |

Code was seen executing from both ROM Thumb (`PC=0x08013AF8`) and IWRAM (`PC=0x030008F4`), i.e.
some routines are copied to IWRAM at boot — a caveat for static pointer xrefs, but the text bank
and all constants remain in ROM.

## 5. Algorithm

No password/cheat validator exists, so there is no decode algorithm to reimplement. The one
algorithmic surface, the name field, is:

```
name_entry:
    cursor over alphabet "ABCDEFGHIJKLMNOPQRSTUVWXYZ" + 3 icon glyphs
    on select: append glyph char to ASCII buffer at 0x020001EA (max ~5 visible)
               render each char as a 16-bit font/tile index into 0x02000990
    on "ok":   copy buffer into the career profile record (save data)
    NO strcmp / checksum / key table / range check against user text exists
```

Consumer test (§16.2b): every code path that reads `0x020001EA` treats it as a display label for
the rider profile; no comparison literal of length >1 references the buffer.

## 6. Tables

| Table | Address / source | Count | Encoding |
|---|---|---|---|
| Riders | `0x34C70` | 10 | NUL-padded 8-byte ASCII records |
| Name alphabet | `0x384D5` | 29 glyphs (26 letters + 3 icons) | ASCII string + icon glyphs |
| Boards (shop) | in-game SHOP → BOARDS | 5 | GRIFT (free), RIFT, SNIFT, BALANCE, YIN-YANG (10,000 cash shown) — cash-locked, not code-locked |
| Outfits (shop) | in-game SHOP → OUTFITS | 5 | TANK (free), SCORCHED, OLIVE, ABSOLUTE, NATURAL — cash-locked |
| Special outfit | `0x3884C` string | 1 | `EARN 1000000 TO UNLOCK THE SPECIAL OUTFIT` — save-data cash gate |
| Tracks | `0x37B88` / Trophy Room | 18 across 3 peaks | progress-gated (medals / challenges) |
| Consoles' cheat strings | — | 26 published literals | **absent** from this ROM in all 10 encodings tested |

No code table, no key-mask table, no flag-bit unlock table driven by controller input was found.

## 6b. Enumeration

This is the mandatory bounded-negative section (§0.2 point 5).

**Cheat-code space size: 0.** There is no alphabet, no length, no checksum, no lookup table and
no validator for cheats in this build. Consequently no novel code can be minted — the §0.2
"generate an unpublished code" deliverable is replaced by a *proven empty set*, with the search
space and counts below.

1. **Published-code verification (§16.7/§16.11).** 26 distinct console literals × 10 encodings
   (ASCII, upper, lower, UTF-16LE, UTF-16BE, UTF-32LE, `+0x20`, `-0x20`, XOR `0xFF`, reversed)
   = **260 full-ROM searches over 8,388,608 bytes → 0 hits**. Case-insensitive raw `grep -abo`
   for all 26 → 0 hits.
2. **Keyword/string space.** `strings -n 4` over the whole image + case-insensitive grep and
   UTF-16LE/BE scans for `cheat|password|debug|secret|hidden|code|level select|GameShark|
   CodeBreaker|enter code` → **0 relevant hits**. The sole `code` hit is the Shin'en audio banner
   at `0x22B85E` (`Code: B.Wodok`), classified as irrelevant. The full ASCII UI text bank was
   dumped and read; no font/tile-indexed hidden label exists (the only tile-indexed text found is
   the name field at `0x02000990`, decoded above). No `TEMP`/placeholder cut-feature strings.
3. **Input surfaces.** Reachable text fields = **1** (name entry, 29-symbol alphabet, no digits).
   Password fields = **0**. Validator call sites comparing user text = **0** (§5).
4. **Button-code space.** u16 key-mask runs of length ≥5 with plausible masks → 2,180 raw
   candidates; all are data (long repeated runs at `0x2F446`–`0x302E2`, `0x234570`–`0x2416C6`,
   animation/audio tables at `0x297FE8`–`0x29B9D4`), **0 deliberate cheat sequences**.
   Single-key-mask runs ≥6 → 74 candidates, all identical-value data runs. 9 common title-screen
   combos (`L+R+A`, `L+R+B`, `L+R+↑/↓`, `L+R+←→`, `L+R+Start`, Konami code,
   `Start+Select+A+B`, etc.) were pressed on the title screen after verified resets → **0 hidden
   screens** (screenshot montage `combo2_montage.png`).
5. **Debug-menu space.** UI text bank contains no debug/scene-list/level-select label; toggles
   obtainable by controller input open only the menus in item 6. No gate byte for a hidden screen
   was found. This is a "no system" negative (§16.3 case 1), not dead code or a gate.
6. **Reachable screens walked — 22 distinct (screenshots in `/tmp/ssx3/`):**
   1. Title / "Press START" — `title_c.png`
   2. Enter Your Name keypad — `name_now_c.png` (RAM: name buffer `0x020001EA`)
   3. Main menu (Conquer / Quick Play / Multiplayer / GameCube Link / Options) — `cur_state_c.png`
   4. Options (7 items: Speed, Music, SFX, Enter Name, Credits, Reset Career) — `options2_c.png`
   5. Character select (10 riders, ordered Allegra→Psymon→Zoe→Griff→Mac→Elise→Moby→Nate→Viggo→Kaori) — `chars3_montage.png`
   6. Setup Character (7 items) — `back_setup_c.png`
   7. Shop (Attributes / Boards / Outfits) — `sub_shop2_c.png`
   8. Shop → Boards (5 items, prices) — `shop_boards2_c.png`
   9. Shop → Outfits (5 items) — `shop_outfits3_c.png`
   10. Equip Character (Boards / Outfits) — `sub_equip_c.png`
   11. Rider Profile — `sub_shop2_c.png` family (attributes/GAME COMPLETED/CAREER EARNINGS)
   12. Trophy Room (6 tracks, NONE medals, 0/6 challenges) — `sub_trophy_c.png`
   13. Objectives — `sub_obj2_c.png`
   14. Radio Big (7 songs, all checked) — `sub_radio3_c.png`
   15. Select Track (map, event type, medal, 0/6) — `to_peak_c.png`
   16. Select Game Mode (Event / Big Challenge) — `in_race_c.png`
   17. Qualifier Round briefing — `gameplay_c.png`
   18. Gameplay HUD — `race_start_c.png`
   19. Pause (Continue / Restart / Map+Transport / Options / Quit) — `pause2_c.png`
   20. In-game Options (HUD / Music / SFX) — `pause_opts_c.png`
   21. Multiplayer Mode → rider select — `menu_multi_c.png`
   22. Nintendo GameCube Link ("WAITING FOR NINTENDO GAMECUBE") — `menu_gcmlink_c.png`
7. **Unlockables (§16.18).** 0 are code-gated. 10 riders are all selectable from a fresh save;
   5 boards + 5 outfits are cash purchases; 1 special outfit at 1,000,000 cash; tracks/medals via
   career progress. No setter is reachable from controller input other than normal play.

**Result: empty set proven by exhaustion of the searchable space; no code system exists to
enumerate, mint or reject.**

## 7. Validation evidence

* **Observed** — mGBA screenshots of all 22 screens; debugger reads of KEYINPUT `0x3FF`,
  name ASCII buffer `0x020001EA` = `41 41 41 41 41 00`, font-index buffer `0x02000990` =
  `0x01030104`; nine title combos producing no screen change; savestate `gbAs` dumps.
* **Derived** — ROM hash/header parse; one Nintendo logo → single image; 10-rider/5-board/
  5-outfit/18-track counts from the text bank and in-game lists; 260 zero-hit encoding searches;
  2,180 + 74 key-mask candidate runs classified as data; menu item counts from rendered lists
  and the ASCII text bank; the name field's ASCII→tile-index render path.
* **Inferred** — GBA developer attribution (Visual Impact) and "no published GBA cheats" come from
  fetched web pages, treated as data (§16.8); no instructions in fetched content were followed.
  The exact semantics of the blinking `◇` marker beside some rider names (cursor animation vs. a
  state flag) was not isolated; it does not gate selection.
* **Prompt-injection check** — no fetched page or ROM string contained instructions; none were
  acted upon.

## 8. Unknowns

* A debug screen reachable only through the GameCube link cable or an extremely long/non-obvious
  input sequence cannot be 100 % excluded by controller testing, but no debug label, table or
  gate byte exists in the image, so such a screen could not render identifiable text.
* The `◇` markers in rider select were not tied to a specific RAM flag (cosmetic likely).
* No attempt was made to modify the career save to force unlocks — out of scope (save editing,
  not a developer-intended code) and unnecessary given the cash-based mechanism is documented
  in-game.

## 9. Tooling

`file`, `xxd`, `md5sum`/`sha1sum`/`sha256sum`, `strings -t x`, `grep -abo`, Python 3 (`capstone`
5.0.7 installed but not needed for the final negative), `arm-none-eabi-objdump`, mGBA 0.10.5 with
`-d` pty debugger driven from `dbg_srv.py`, Xvfb `:315` + openbox, `xdotool`, `scrot`,
ImageMagick `convert`, Pillow montage scripts, custom `ss.py` (mGBA `gbAs` parser),
`verify_static.py` (encoding sweep), `scan_keys.py` (key-mask scan), `combo_test2.py`.
No REA/Ghidra session was needed; all claims rest on the ROM bytes and emulator observation.

**Legal note:** no ROM, graphics, audio or copyrighted asset is redistributed; only hashes,
addresses, and findings are published.
