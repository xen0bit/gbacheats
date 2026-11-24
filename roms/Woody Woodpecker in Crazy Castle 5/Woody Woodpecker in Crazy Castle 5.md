# Woody Woodpecker in Crazy Castle 5 (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Woody Woodpecker in Crazy Castle 5.gba` |
| Size | 4,194,304 bytes (0x400000, 4 MiB) |
| Header title | `WWCC5` |
| Game code | `AWWE` |
| Maker | `7F` |
| Version | `0x00` (Rev.00) |
| Fixed byte | `0x96` |
| Complement | `0x37`; header checksum `0x0000` |
| Entry word | `0xEA00002E` (stock crt0 branch to `0x08000268`) — retail image, no cracktro/trainer (guide §16.1) |
| MD5 | `b9b3be20dacbdf7d06b7ee86e73b677a` |
| SHA-1 | `47179baa55cc7c19b16195ff3c85396a0cc466f9` |
| SHA-256 | `5c2aab245a4399277138c9895eb648001268d5737fc6528b8ea5e9a9205df2a9` |
| Developer | Tantalus Interactive (Australia) / KEMCO (Japan), 2002 |

## 2. Executive summary

**Bounded negative: no in-game/developer-intended cheat system was found in this ROM.**
There is no password screen, no on-screen code alphabet, no code validator, no
hard-coded cheat table, no hidden debug/scene-select menu, and no undocumented
button sequence. The only hardwired multi-key combination in the whole input
path is `A+B+Select+Start`, which simply soft-resets the title (observed). The
game's "bonus" content (Wheel of Skill, slot machine, ending art) is reached by
normal play, not by a code.

The negative is *bounded*, not merely unreached: every reachable screen was
walked (§7), the complete ASCII text bank was decoded and keyword-counted (§6),
the font/glyph tables were decoded and shown to be rendering tables rather than
a password alphabet (§4), the ROM was scanned for button-mask tables and code
alphabets (§6b), and all event-listener registrations were enumerated (§6b).
Counts are in §6b.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 under Xvfb `:317`, `SDL_AUDIODRIVER=dummy`, `-3` scale.
  Important: **use `import -window root`, not `scrot`** — `scrot` returns a black
  frame on mGBA's GLX canvas (guide §16.2).
* Keymap (mGBA SDL default): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
  Select=`BackSpace`, D-pad = arrow keys. Hold keys 120–150 ms.
* Path: boot → *Guess Who?!* splash → *Woody Woodpecker* title → `PRESS START`
  → main menu (PLAY / CREDITS / ERASE DATA / MULTIPLAYER) → PLAY →
  (START / TUTORIAL) → story cutscene → level 1.
* GDB stub note: another agent held the single-client stub on port 2345, so RAM
  evidence was gathered with mGBA's `-d` pty debugger driven over a UNIX socket
  (`dbg_server.py` / `dbg.py` in the work dir); `r/1|2|4`, `x/1`, `w/…`, `b`
  and a Ctrl-C break were used. This is the guide's §16.2/§16.13 fallback.

## 4. Address map

| Address (ROM) | Meaning | Evidence |
|---|---|---|
| `0x08000000` | Header; stock entry `0xEA00002E` | Observed (bytes) |
| `0x08000268` | ARM crt0; loads `main` from literal at `0x08000460` | Derived (disassembly) |
| `0x08000460` | Thumb pointer `0x08358CF9` → `main` = `0x08358CF8` | Derived |
| `0x08358CF8` | Engine `main` (init calls + loop) | Derived |
| `0x0835A53C` | Joypad polling / key-state update function | Derived |
| `0x0835A564` | `cmp r2,#0xF` — sole hardwired combo `A+B+Select+Start` → dispatch event 21 | Derived |
| `0x0835AC3C` | Event dispatcher (`r0`=event id, `r1`=payload) | Derived |
| `0x0835ABA0` | Event-listener registration (`r0`=id, `r2`=callback) | Derived |
| `0x03000124` | held keys, active-high (`0x3FF & ~KEYINPUT`) | Derived + observed |
| `0x03000126` | previous held keys | Derived |
| `0x03000128` | newly-pressed keys | Derived |
| `0x0300012A` | newly-released keys | Derived |
| `0x04000130` | KEYINPUT (literal pool at `0x0835A598`) | Derived |
| `0x03001248` | pointer to event-listener table → `0x02000018` | Observed (RAM read) |
| `0x08363000`–`0x08368000` | ASCII text bank (EN/FR/DE story, menus, asset names) | Observed |
| `0x08368170`–`0x08368220` | Font/glyph mapping table A (descending glyph runs) | Observed (hex) |
| `0x08368270`–`0x083682F0` | Font/glyph mapping table B (ascending `0x00..0xAB`) | Observed (hex) |
| `0x0E000000` | 512-byte SRAM save (`game.sav`, initially all `0xFF`) | Observed |

Text is plain ASCII drawn through a glyph-index lookup; substituted bytes in
the bank (`^ [ \ ] _ @`) are accented-letter glyphs (e.g. `FRAN[AIS` =
`FRANÇAIS`, `S\LECTION` = `SÉLECTION`, `DR]CKEN` = `DRÜCKEN`,
`L_SCHEN` = `LÖSCHEN`), not code symbols. This was decoded before the negative
was accepted (guide §11 "not all text is ASCII").

## 5. Algorithm

Not applicable — there is no validator, checksum, encoder or decoder in this
ROM. The only algorithmic finding is the input mapping:

```
held   = 0x3FF & ~KEYINPUT                 @0x0835A546-0x0835A54E
pressed = held & (held ^ previous)          @0x0835A554-0x0835A55C
released= ~held & previous                  @0x0835A55E-0x0835A562
if held == 0x0F (A|B|Select|Start):         @0x0835A564
    dispatch_event(21, held)                @0x0835A56A-0x0835A56C
    wait until all keys released            @0x0835A580-0x0835A58A
```

Event 21 has **no registered listener** (§6b); pressing the combination was
observed to return the game to the title splash, i.e. a soft reset, not a cheat.

## 6. Tables

* **Menu tables (observed, in-game):** main menu = exactly 4 items,
  `PLAY → CREDITS → ERASE DATA → MULTIPLAYER → (PLAY …)`, period 4
  (screenshots `final_menu_0..7.png`). PLAY submenu = exactly 2 items,
  `START`, `TUTORIAL` (screens `screen_after_play.png`, `playmenu_1.png`).
* **Key masks:** active-high `A=0x001,B=0x002,Select=0x004,Start=0x008,
  R=0x010,L=0x020,Up=0x040,Down=0x080,Left=0x100,Right=0x200`.
* **Event IDs registered by game code (derived, 48 call sites):** `{0, 2, 3,
  6, 7, 11, 16, 19, 20}`; **21 absent**.
* **ASCII keyword counts over the decoded text bank `0x08363000`–`0x08368000`**

  | Term | Hits |
  |---|---:|
  | PASSWORD / PASS WORD | 0 |
  | CODE | 0 |
  | CHEAT | 0 |
  | SECRET | 0 |
  | DEBUG | 0 |
  | LEVEL SELECT / WARP | 0 |
  | ENTER (as code entry) | 0 (1 hit = "…to **enter** the room.") |
  | UNLOCK | 3 (all "collect 8 keys to unlock the final door") |

## 6b. Enumeration

**Claim: the code space is empty; this is a closed, bounded negative.**

1. **Screen space (fully walked, visually verified).** Boot splash
   (*Guess Who?!*, Tantalus logo), Woody title art, `PRESS START` title,
   main menu (4 items, period 4 — proved by 8 consecutive Down presses with a
   screenshot at every step), PLAY submenu (2 items), story cutscenes
   (house / Mother Nature dialogue), gameplay rooms, pickup/item text-box
   screens, bonus mini-games (Wheel of Skill, slot machine — asset strings
   `art\screens\minigame\wheel.rbh`, `slot.rbh` at `0x08367D88`/`0x08367DF0`),
   level-complete / congratulations screens, game over / continue screen,
   credits and ending (`THE_END` art at `0x08367E9C`). No code-entry field,
   no level-select list, no debug overlay appeared on any screen.

2. **Text space.** `strings -t x -n 4` produced **44,968** ASCII strings over
   the 4 MiB image. The whole on-bank `0x08363000`–`0x08368000` was dumped and
   decoded with the font substitution above; **0** occurrences of
   password/code/cheat/debug/level-select/warp terminology (§6). The
   `+0x20` lowercase-shift trick and UTF-16 checks were also considered: the
   bank is ordinary ASCII, so no encoded variant is being missed.

3. **Alphabet/table space.** A regex scan of all 4 MiB for printable runs
   ≥16 chars with ≥16 distinct characters and >85 % alphanumerics returned
   **14** hits; **all 14** are either compressed graphics/audio or the
   font/glyph tables at `0x08368170`/`0x08368270` (§4). None is an input
   alphabet. The glyph tables contain contiguous runs `0x00..0xAB` etc. and
   are demonstrably the ASCII→tile renderer (they line up with the menu
   strings' character set), not a code alphabet. There is no code table.

4. **Button-mask space.** Scanner over the entire ROM for runs of ≥3
   consecutive `u16` values drawn from the 10 single-key masks and their
   pairwise combinations found **1,922** runs; a byte-wise scan for ≥4
   consecutive single-key masks found **1,680** runs. Inspection of the
   longest/highest-entropy examples (e.g. `0x0802B374`, `0x08030074`) shows
   long homogeneous `0x01`/`0x02` fills — compressed art, not key sequences.
   **Zero** runs are referenced by a comparison loop. Static disassembly of
   the sole joypad routine (`0x0835A53C`) shows exactly **one** hardwired
   combo check (`0x0F`), and it dispatches event 21, which has **zero**
   listeners. No mask-sequence matcher exists.

5. **Debug-gate space.** All **48** registrations to event `0x0835ABA0` were
   enumerated with their event IDs (§6). No unusual/debug event is handled.
   There is no save-bit mystery to brute-force: the 512-byte SRAM was all
   `0xFF` before play and the game has no unlock flag comparable to the
   guide's §16.18 cases — the mini-games are ordinary gameplay pickups.

6. **Web/published-code reconnaissance.** Attempted (guide §3.4) via the
   available search integration and direct fetches (GameFAQs, TCRF, Google,
   Bing, DuckDuckGo). Search returned no results for this title; direct
   fetches were 403 / bot-challenge. **No published code could be located or
   verified.** This is recorded as a limitation, not treated as evidence of
   absence; the negative above rests entirely on ROM and emulator evidence.

**Final enumeration statement:** 0 password systems, 0 code alphabets, 0
validators, 0 hard-coded code tables, 0 debug menus, 0 undocumented button
sequences; 1 key combo which is a reset. Therefore no novel code can be
minted, and the guide's novel-code deliverable (§0.2 item 3) is **not
applicable**. The bounded negative is delivered in its place, with the counts
above.

## 7. Validation evidence

* **Observed** — emulator screenshots of every screen listed in §6b item 1
  (kept in `/tmp/woody5/`, not in the ROM folder); RAM reads of key
  state `0x03000124/126/128/12A` and the listener-table pointer at
  `0x03001248`; the SRAM dump; image-diff tests of combos on the title.
* **Derived** — disassembly of crt0/main, `0x0835A53C` input routine, the
  `0x0835A564` combo check, event register/dispatch (`0x0835ABA0`,
  `0x0835AC3C`) and all 48 call sites; xref scans for `0x04000130` and key
  RAM addresses; the ASCII/glyph decode of the text bank.
* **Inferred** — that the 14 alphabet-like runs are compressed data rather
  than tables (supported by their location in known high-entropy asset
  regions and by their homogeneous fill patterns); that event 21's reset
  behaviour is engine-level (supported by its zero listeners).

## 8. Unknowns

* Web-based confirmation of "no published codes" could not be obtained
  because all search/fetch routes were blocked; a human with normal web
  access should re-check GameFAQs/TCRF for this exact SKU (`AWWE`, Rev.00).
* The 1,922 + 1,680 spurious key-mask runs were sampled, not individually
   adjudicated; none had a validator xref, which is the discriminating test.
* Multiplayer screens requiring a second cartridge/link were not entered;
  their ASCII labels (`SINGLE^PAK LINK`, `MULTI^PAK LINK`) are present and no
  code-related strings exist there.

## 9. Tooling

* `file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings`, Python 3 regex
  scanners (`scan_codes.py`, `xref.py`, `find_reg.py`), `arm-none-eabi-objdump
  -M force-thumb`, Xvfb `:317` + openbox, mGBA 0.10.5 (`-3`, `-d`), `xdotool`,
  ImageMagick `import`, Pillow for montages, mGBA pty debugger bridge
  (`dbg_server.py`, `dbg.py`, `ramdump.py`). All artifacts live in
  `/tmp/woody5/`; no ROM or copyrighted asset is redistributed here.

## 10. Legal note

Only hashes, addresses, algorithms and original observations are published.
No ROM image, extracted graphics, music or game text beyond short UI labels is
included.
