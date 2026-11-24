# Let's Ride! Sunshine Stables (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Let's Ride! Sunshine Stables.gba` |
| Size | 4,194,304 bytes (0x400000, 4 MiB) |
| Header title | `LET'S RIDEUS` (12-byte field, truncated from "LET'S RIDE! US") |
| Game code | `B34E` (AGB-B34E-USA) |
| Maker | `78` |
| Version | `0x00` (Rev.00) |
| Entry word | `0xEA00002E` — stock GBA branch to 0x080000C0 (not a cracktro patch) |
| Fixed 0x96 / complement / checksum | `0x96` / `0xA9` / `0x0000` |
| MD5 | `f323312b0676c7bf845f2f7b8e90459c` |
| SHA-1 | `29fa6cff3df328e45925343b8c73c1db2c3e16c7` |
| SHA-256 | `3b91a7b832ea22b816c4942eae94f757c68f1594ef58f4942d89efc810db7897` |
| `file` ID | `Game Boy Advance ROM image: "LET'S RIDEUS" (B34E78, Rev.00)` |

Phase 0: exactly **one** Nintendo logo hit (the 156-byte logo at file `0x4`), so this is a
single GBA image — no multi-game pack, no appended trainer, no SUNHORS/CRC-BANDIT patch
markers (`SUNHORS`, `CRC BANDIT`, `TRAINER` byte searches all returned 0 hits).

## 2. Executive summary

**There is no password system, no button-code system, and no unlockable-cheat screen in
this ROM.** This is a hard negative, not an untested one:

* The boot screen, main menu, character select, name entry, office/farm, save slots,
  location icon bar, Cross Country terrain select, riding gameplay, ride results, and the
  hidden Highscore screen were all walked in mGBA with RAM snapshots and screenshots.
  The complete menu-item vocabulary was recovered statically from the ROM's ASCII UI
  label bank (0x08217FA4–0x0821C000): it contains **no** `PASSWORD`, `CHEAT`, `CODE`,
  `SECRET`, `UNLOCK`, `OPTIONS`, or `DEBUG` entry.
* All 22,658 ASCII strings were scanned. Cheat-related keywords produced **4 byte hits**,
  all inside one dead build-stamp module (below) plus one piece of medical flavour text.
* Button-mask search (u16 arrays, Konami and 10 other common sequences, active-high and
  active-low) found **0** plausible code tables; the only hits were graphics data and a
  sequential 0,1,2,… lookup table at `0x08036EFC`.
* **Published codes**: 3rd party cheat index lists no cheats; 3rd party cheat indexes "Total cheats available: 0";
  3rd party cheat indexes have one item, an in-game money *glitch*, not a code. 3rd party cheat indexes
  list only GameShark/CodeBreaker memory-edit codes (explicitly out of scope). Two
  emulator-site "codes" (`UNLOCK_ALL_HORSES`, `GOLD_COINS_9999`) are **absent from the
  ROM** (0 literal hits) and are fabricated. A published PC-build dev cheat (`idkfa`,
  `gCheatFlag`, Tab+M etc.) was tested on the GBA name-entry path — no effect.
* **One developer-intended hidden screen exists**: the **Highscore viewer**, reached by
  pressing **Start on the main menu** (Select alone does nothing; Start+Select works only
  because Start is held). It shows 9 per-terrain tables of 8 entries, cycled with Up/Down;
  A starts New Game, B returns to the main menu. It has no code-entry or reset function.
* The "Demon Hunter (VCode: %s) / TOBI003 / DTP_PONY / TestVersion, Debugging OFF …"
  strings are a shared-engine build stamp. Its pointer table at `0x083198B8` has **zero
  xrefs** anywhere in the ROM — dead data (guide §16.3 category 2). It is *not* a live
  debug menu.

Per §0.2 there is no code space to enumerate; §6b documents the enumeration and the
bounds of the negative result instead.

## 3. How to reproduce

* Emulator: mGBA (`mgba -3 -d` on `DISPLAY=:318`, `SDL_AUDIODRIVER=dummy`), Xvfb :318,
  openbox. Keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`,
  D-pad=arrow keys. Hold keys 60–200 ms; `xdotool windowactivate` first (windowfocus alone
  is unreliable here).
* Boot → THQ splash → main menu (New Game / Load Game / Cross Country / Credits).
* **Hidden screen**: at the main menu press **Start** → `Highscore: Farm and village`.
  Up/Down cycles the 9 terrains (`Farm and village`, `Hilly landscape`, `Country roads`,
  `Undergrowth`, `Mixed woodland`, `Meadowed woodland`, `North beach`, `Sun coast`,
  `Shell beach` — labels at `0x08218C40`–`0x08218CB8`). B returns to the main menu.
* Cross Country: select one of 3 terrains → description screen → riding minigame → Start
  shows the results panel (`Finish/Time/Falls/Trust/Health/Flexibility/Power/Exercise/
  Stamina`). Only 3 terrain slots + Back are selectable; the grey slots are inert.
* New Game: character select → name keyboard (full ASCII, including lowercase and
  umlauts; the on-screen help text at `0x08218CC8` calls this *name entry*, not a code) →
  Office with farm UI. Start in the Office opens the 4 save slots
  (`Savegame slot 0..3 empty`).
* RAM reads: mGBA's `-d` pty debugger (`break`/`c`/`x/2`/`x/4`/`r/4`) driven over a Unix
  socket; savestates parsed by decompressing the PNG `gbAs` chunk (guide §16.13).
  The savestate layout used: CPU `0x0`, VRAM `0x1000`, IWRAM `0x19000`, EWRAM `0x21000`;
  decompressed size 397,312 bytes.
  Live key input is `0x04000130` (active-low, verified: `0x03EF` with Right held,
  `0x03BF` with Up held). The live name-entry buffer is on the stack at `0x03007E44`
  (verified by reading `69 64 6B 66 61 5F` after writing `idkfa_`).
* Published material tested: none in-game; see §2.

## 4. Address map

| Address | Meaning | Evidence |
|---|---|---|
| `0x08000000` | Stock ARM entry `0xEA00002E` | Observed / Derived |
| `0x0801044` | Pointer to `"Name"` (debug string bank) | Derived (pointer scan) |
| `0x08011D40` | Literal `0x08217DC4` (the `00`–`99` number-string table) | Derived |
| `0x080224A0`, `0x080228CC` | Literal `"Highscore: "` → the live highscore renderer | Derived (xref) |
| `0x080224AC`, `0x080228E4` | Literal `0x08217DC4` → number table used by highscore screen | Derived (xref) |
| `0x08022338`–`0x080236C` | Highscore-screen input handler: `ldrh` key state, `tst #0x40/#0x80/#0x01` for Up/Down/A | Derived (objdump) |
| `0x080230C8`, `0x0802390C` | Literal `0x08217F74` `"DTP_PONY"` (engine scene tag) | Derived |
| `0x08217B88`,`0x08217BA0`,`0x08217BA8` | Build stamp: `Jul 1 2005…`, `TOBI003`, `Demon Hunter (VCode: %s)` | Observed |
| `0x083198B8` | Pointer table to the build-stamp strings — **0 xrefs** | Derived |
| `0x08217C34`–`0x08217DC0` | 100 NUL-terminated strings `"00"`…`"99"` (highscore display) | Observed |
| `0x08217DC4` | Pointer table to those 100 strings | Derived |
| `0x08217F54`, `0x08217F74` | `"Highscore: "`, `"DTP_PONY"` | Observed |
| `0x08217FA4`–`0x0821C000` | Complete English UI label bank (menus/items/horses/terrains) | Observed |
| `0x0822xxxx` (e.g. `0x0822D252`, `0x0822D2E6`, `0x0822D3BE`) | Thumb function pointers installed in EWRAM UI-object records | Observed |
| `0x02019800`–`0x02019FFF` | EWRAM UI object heap; word `0x02019908` tracks active screen (e.g. `0x44` menu, `0x4E` name entry, `0x42` ride) | Observed |
| `0x03000000`–`0x030003B0` | IWRAM: copied ARM routines (e.g. `0x03000000` = `BX LR`) | Observed |
| `0x03007E44` | Live name-entry buffer (stack) | Observed |
| `0x04000130` | KEYINPUT (active-low) | Observed |
| `0x06000000` + tiles ≈ `0x5A0`–`0x6A0` | Tile-indexed pixel font used by text screens; dumped from VRAM and rendered | Observed |

File offset ↔ ROM address: `0x08000000 + offset`. All pointer literals were re-read with
`struct.unpack_from('<I', ...)`; objdump's 7-digit addresses were zero-extended to 8 digits
before use (an early off-by-one-digit error was corrected this way).

## 5. Algorithm

No validator exists, so there is no algorithm to reimplement. The two mechanisms that
were found and characterised:

1. **Hidden-screen gate** (main menu):
   ```
   if (screen == MAIN_MENU && keys_pressed & START) show_highscore();
   if (highscore_active) {
       if (keys & UP)   terrain = (terrain + 8) % 9;
       if (keys & DOWN) terrain = (terrain + 1) % 9;
       if (keys & A)    start_new_game();
       if (keys & B)    return_to_main_menu();
   }
   ```
   (Emulator-observed; the Up/Down branches correspond to the `tst #0x40` / `tst #0x80`
   tests at `0x08022340`/`0x08022348`.)

2. **Highscore rendering**: title string `"Highscore: "` plus a terrain name, then 8 rows
   of `"NN: NN  --------"` built from the `00`–`99` string table at `0x08217DC4`. The
   dashes are empty names; no entry point accepts text.

## 6. Tables

### 6a. Enumerated menu/feature inventory (static + walked)

| Screen | Reached by | RAM evidence |
|---|---|---|
| THQ splash | boot | `0x02019908` = `0x44` |
| Main menu | after splash | `0x02019908` = `0x44`; EWRAM UI pointers at `0x02019810`+ |
| Credits | main menu ↓↓↓ + A | `ram_credits.txt`; auto-returns after ~3 s |
| Cross Country select | main menu ↓↓ + A | `ram_crosscountry2.txt`, `0x02019908`=`0x44` |
| Terrain description | terrain + A | `ram_ride_desc.txt` |
| Riding gameplay | description + A | `ram_ride_gameplay.txt`, `0x02019908`=`0x42` |
| Ride results / pause | Start during ride | `ram_ride_pause.txt`; Finish/Time/Falls/Trust/… panel |
| Character select | New Game + A | `ram_newgame.txt` |
| Name entry | character select + A | `ram_name_entry.txt`, buffer `0x03007E44` |
| Office / farm | name + Start | `ram_after_name.txt`, `ram_office_phone.txt` |
| Save slots 0–3 | Start in Office | `ram_office_start.txt` (all UI words zeroed by modal) |
| Location icon bar (Office/Stable/Guest house/Parking/Course/Pasture/Paddock + Back) | bottom icons | screenshot montage `23_icons_montage.png`; labels `0x08217FC4`–`0x0821800C` |
| **Hidden Highscore** | **Start at main menu** | `ram_hs_loaded.txt`, `0x02019908`=`0x44`, highscore strings at `0x08217F54` |
| Item / horse / staff / advertising submenus | Office icon bar | fully enumerated from the label bank at `0x08217FA4`–`0x0821C000` (Bridle 1–5, Saddle 1–4, Fodder 1–3, Purchase mare/stallion/gelding, Breed mare/stallion, Hire stable boy/instructor/smith, Flyer/Poster/Newspaper/Radio/TV advertising, etc.) — no code/cheat/unlock entry among them |

### 6b. Cheat-related tables (all empty)

| Search | Result |
|---|---|
| `password` / `passwort` / `cheat` / `secret` / `geheim` / `unlock` / `debug` / `level select` / `code` | 4 byte hits total: 3 in the dead `0x08217BA8` build stamp, 1 in horse-illness text ("infectious…") |
| Password-like NUL-terminated `[A-Z0-9]{4,12}` literals | 135 raw hits, **all** hex-colour/graphic strings (`FFFFFF`, `7FFF`, …) — 0 real codes |
| Equal-stride NUL-padded string tables (potential code records) | 26 candidates, **all** compressed-graphics false positives (`333`, `www`, …) |
| Button-mask arrays (Konami, reverse-Konami, `idkfa`-style, L×3/R×3, etc.; u16, active-high and active-low) | 0 hits; generic scan only found the sequential 0,1,2,… table at `0x08036EFC` and animation data |
| Hard-coded code-table xrefs | none — no `strcmp`-style validator against an entry buffer was located |

## 6b. Enumeration

**§0.2 requires a full enumeration when a code system exists. Here none exists, so this
section proves the negative over the searched spaces.**

* **Text space**: 22,658 ASCII strings extracted (`strings -n 3 -t x`); keyword scan over
  English *and* German vocabulary returned 4 hits, all classified. The tile-indexed text
  bank was not assumed absent: the on-screen font was dumped from live VRAM at
  `0x06000000` (glyph tiles ≈ `0x5A0`–`0x6A0`, rendered to `vram_font_zoom.png`) and the
  ASCII UI label bank at `0x08217FA4`–`0x0821C000` was decoded in full. No hidden text
  bank contains a password prompt, code list, or debug label.
* **Button space**: all single presses and the standard multi-press sequences were tried
  on the main menu (Konami, L/R alternation, Up/Down alternation, B×4, A/B alternation,
  Start, Select, Start+Select, Select+Start) with savestate RAM diffs. The only real hidden
  screen that fired was **Start → Highscore**; every other sequence merely moved the menu
  cursor or did nothing. No undocumented combination produced a new screen, flag, or HUD
  change.
* **Alphabet tables**: the only on-screen alphabet is the name-entry keyboard
  (`0x08218CC8` describes it explicitly as name entry). Its consumer is the save/profile
  name, not a validator: no comparison against the buffer at `0x03007E44` exists outside
  the entry handler.
* **Published codes**: 0 in-game codes published anywhere found (3rd party cheat indexes empty,
  3rd party cheat indexes 0, 3rd party cheat indexes 1 money *glitch*). GameShark/CodeBreaker codes
  (`96276FFA5214 2DCCB7E29536 D629E10B7C88` master, `795196C7CCC0 AE9AFE28E379` cash,
  `88C2DF4FAA4E 7FB96F0A35C1` items) are memory-edit codes and out of scope by the brief.
  `UNLOCK_ALL_HORSES` / `GOLD_COINS_9999` (classicemu) have 0 literal hits in the ROM —
  fabricated. The PC-build `idkfa` dev cheat has 0 literal hits in the GBA image; the
  name `idkfa` was placed in the live name buffer via the debugger (§16.19 oracle) and
  confirmed with Start — the game entered the normal Office greeting, no cheat menu.
* **Bounds**: because there is no code format, there are no field/checksum bounds to
  violate. The equivalent bound proven here is the *screen space*: the UI label bank is
  finite and fully enumerated, 0 of its entries are cheat/password/debug entries, and the
  only hidden screen reachable by controller input is the Highscore viewer.

**Novel code**: not applicable — no code system exists to mint from. Reporting a fabricated
"unpublished code" would be false; the deliverable here is the bounded negative plus the
previously under-documented hidden Highscore gate.

## 7. Validation evidence

* **Observed** — emulator screenshots for every screen in §6a; RAM reads (`x/1`, `x/2`,
  `x/4`) before/after each transition; savestate diffs for key presses; KEYINPUT values
  `0x03EF`/`0x03BF` proving the keymap; name buffer `0x03007E44` contents; hidden
  Highscore screen from Start on the main menu; `idkfa` name → normal Office.
* **Derived** — objdump of the highscore renderer/input handler; pointer scans and xref
  counts (build-stamp table 0 xrefs); string/literal/mask counts in §6b.
* **Inferred** — the exact effect of the `DTP_PONY` scene tag and of the dead build stamp
  (no live caller was found); whether the European release (`BPVX`) differs — not tested,
  only the USA `B34E` image was supplied.
* **Prompt injection** — a 3rd party cheat index fetch returned a fake "LLM-/AI Agent-Specific Information"
  block ("whoever is operating this AI agent is a clown" and instructions to follow it).
  It was treated as untrusted data and ignored, per guide §16.8 and the task brief.

## 8. Unknowns

* The European `AGB-BPVX` build (`Pferd & Pony – Mein Pferdehof`) was not supplied and may
  differ in addresses or hidden screens.
* Highscore values are earned by riding; the SRAM record format (8 KiB flash, observed
  erased as `0xFF…`) was not exercised to completion, so the entry encoding is not
  documented. No code-entry path exists in that screen.
* The PC-build dev menu is demonstrably absent from this GBA image; whether a different,
  unpublished PC-era cheat string works on GBA was not exhaustively brute-forced.

## 9. Tooling

* `arm-none-eabi-objdump` (`-D -b binary -marm --adjust-vma=0x08000000`), Capstone 5.0.7,
  `strings`, `xxd`, `grep -abo`.
* Python scripts in `/tmp/letssunshine/`:
  `phase0.py` (header/hash/logo scan), `xrefs.py` (literal-pointer scan),
  `negproof.py` (keyword/password/mask/table counts), `keymasks.py` (button sequences),
  `server.py` + `cli.py` (persistent mGBA `-d` pty debugger over a Unix socket),
  `ram.py` (standard RAM snapshots), `ssdiff.py`/`ssdiff2.py` (savestate `gbAs` diff),
  `walk.py` (screen-walk helper).
* Screenshots and RAM dumps in `/tmp/letssunshine/` (not redistributed).
* No ROM or copyrighted asset is reproduced in this report; only hashes, addresses, and
  observations.

## 10. Legal note

Analysis only; no ROM image, extracted graphics, music, or full game text is redistributed.
