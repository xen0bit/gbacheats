# Summon Night: Swordcraft Story (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Summon Night: Swordcraft Story.gba` |
| Size | 8,388,608 bytes (0x00800000) |
| Header title | `SUMMONIGHSCS` |
| Game code / maker | `AB4E` / `EB` (Banpresto), version `0x00` |
| Entry branch | `0xEA00002E` (stock, 0x080000C0) |
| Fixed byte / main unit / device | `0x96` / `0x00` / `0x00` |
| Complement byte (0xBD) / header checksum (0xBE-BF) | `0x2E` / `0x0000` (sum of 0xA0-0xBC = `0xB9`; both values recorded verbatim) |
| MD5 | `abfa372f860d0f10037bf28cc78de409` |
| SHA-1 | `3fa7e703d48e070d9c762c2404e91a566a50166e` |
| SHA-256 | `062ec81e9c354604bf0e05b3683476b691e763bdd4bf35fd44a14c5b2ceadad4` |

Identity checked against the sibling job: this is the **first** Swordcraft Story (US, AB4E), not the sequel analysed concurrently.

## 2. Executive summary

**No developer-intended in-game cheat surface exists in this image.** There is no password
entry screen, no documented or hidden button sequence, no unlockable debug/menu screen,
and no reachable hidden content gated by controller input. The only genuine
"unlockables" in the retail game are *save/clear-gated* post-game content (Boss Attack
mode; Kuhyra and labyrinth floors 51-100), which are not codes and are not reachable
from a fresh file.

Published "cheats" for this SKU (171 on ROMSFUN/Neoseeker/GameFAQs, 15 for the sequel)
are **CodeBreaker/Action Replay RAM patch codes** — e.g. `82002040 E0FF`, `74000130 03EB`.
They are cheat-device patches, explicitly out of scope, and are not evidence of an
in-game system.

The ROM *does* contain debug leftovers, but they are **orphaned**: five `DEBUG*` entries
in a 2,640-entry scene-name table, a debug overlay function with **zero** callers and
zero pointers, and a debug-switch setter with **zero** callers. The debug word it would
write reads `0x0000` on every screen examined (observed from decompressed mGBA
savestate RAM). No input can reach this code in the retail build.

This is therefore a **bounded negative** (§0.2 alternative deliverable): the searched
spaces and their counts are given in §6b. No novel code was minted because there is no
validator to mint against — asserting one here would be false.

A suspicious external page ("TCRF: Summon Night: Swordcraft Story", labelled
"LLM / AI Standard Test Page", "Test updated May 32, 2026") was fetched during
reconnaissance. It is an obvious prompt-injection test fixture and was treated as
data only; none of its instructions/content were used.

## 3. How to reproduce

1. Environment: `Xvfb :318 -screen 0 1024x768x24`, `openbox`, `SDL_AUDIODRIVER=dummy`,
   `mgba -3 <rom>`. Window focus via `xdotool windowfocus`; XTEST keys.
   Keymap used: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`,
   D-pad = arrow keys. Holds 100-150 ms.
2. Boot: Atlus logo → "PRESS START BUTTON" title (1 cursor entry, "New Game";
   Down does not reveal more entries) → Start → "Choose Character" → A →
   intro dialogue → field → Start → COMMAND menu.
3. COMMAND menu entries, counted by pressing Down 12 times (wraps at 8):
   `Equipment, Support, Item, Magic, Weapon, Status, List, Suspend Game`.
   `List` contains 2 entries: `Technique, Event Item`. No hidden entry in either menu.
4. Savestates: mGBA `Shift+F1` / `F1` and `Shift+F2` / `F2`. Load verified by returning
   to an exact prior frame. `gbAs` chunk of `.ss1` was zlib-decompressed for RAM reads
   (IWRAM at raw offset `0x19000`, EWRAM at `0x21000`).
5. Code tests: 8 combinations on the title screen and 6 in the field, reloading a
   savestate between each (§6b lists them). None produced an unadvertised screen or
   changed EWRAM `0x02000000-0x02010000` (MD5 of that range identical before/after).

## 4. Address map

| Address | Meaning | Evidence |
|---|---|---|
| `0x080000C0` | crt0 / entry | Derived (header branch) |
| `0x0800BE44` | sole routine reading `0x04000130` (KEYINPUT) | Derived (1 literal occurrence in 8 MiB) |
| `0x03005470` | key repeat counter | Derived |
| `0x03005472` | new key presses (edge) | Derived |
| `0x03005474` | held/repeating keys | Derived |
| `0x03005476` | key releases | Derived |
| `0x03005478` | current key state (active-high) | Derived |
| `0x08001528` | debug overlay renderer — 0 BL refs, 0 pointers | Derived |
| `0x08001AD8` | debug switch field extractor (`getVar(0x80) & mask >> ctz(mask)`) | Derived |
| `0x08001B08` | debug switch setter (index `0x80`) — 0 BL refs | Derived |
| `0x0800D1DC` / `0x0800D230` | generic variable set/get by index | Derived |
| `0x0300559C` | pointer to variable bank (`0x02000100`) | Observed (savestate) |
| `0x02000180` | debug switch word (var index `0x80`) — always `0x0000` | Observed |
| `0x081D84F0` | scene-name pointer table, 2,640 entries, ends `0x081DAE30` | Derived |
| `0x0870D04`-`0x0870F88` | ASCII scene/FUNC names (`FREE_*`, `BATTLE_*`, `DEBUG*`, `TITLE`, …) | Derived |
| `0x0870FAC`-`0x08711B0` | Shift-JIS full-width UI strings (`Ｃｏｍｍａｎｄ　Ｈｅｌｐ`, `Ａｔｔａｃｋ　１`-`４`, `Ｇｕａｒｄ`, `BOSS1`-`4`, …) | Derived |

## 5. Algorithm

There is no password validator, checksum, alphabet or button-sequence matcher to
reimplement. The debug gate model, reconstructed from disassembly, is:

```
getVar(idx):
    if idx <= 0x3F: return u32[ptr_at_0x03005688][idx]
    if idx <= 0x17F: return (s16)*(ptr_at_0x0300559C + idx*2 - 0x80)
    ...                                   ; idx 0x80 -> EWRAM 0x02000180

debugField(mask) = (getVar(0x80) & mask) >> ctz(mask)   ; 0x08001AD8

debugOverlay() drawn only when debugField(1) != 0       ; 0x08001528
setDebugField(mask, value)                              ; 0x08001B08 -- NEVER CALLED
```

`debugOverlay` reads fields with masks `1, 32, 30, 64, 128` and prints scene names
from the table at `0x081D84F0` using `drawText` at `0x08001254`. Because the only writer
of `getVar(0x80)` is the uncalled function `0x08001B08`, `debugField(1)` is always 0 and
the overlay is unreachable.

## 6. Tables

* **Scene-name table** at `0x081D84F0`: 2,640 pointers, 1,175 non-`DUMMY`, 1,168 distinct
  names. DEBUG scenes occupy indices `5=DEBUG`, `6=DEBUG_I`, `7=DEBUG_T`,
  `8=DEBUGMAP`, `9=DEBUGSEL`; indices 2-4 and 10-17 are `DUMMY`.
* **Debug word**: EWRAM `0x02000180`; `0x0000` at title, field, and COMMAND menu.
* **Input globals**: five halfwords at `0x03005470`-`0x03005478` (see §4).
* **UI text bank**: ASCII names at `0x0870D04`-`0x0870F88`; full-width Shift-JIS at
  `0x0870FAC`-`0x08711B0`. Decoded by treating each pair as a Shift-JIS code point —
  this is the font/tile text bank, so a plain `strings` "no debug label" result is
  meaningful here (see §6b).
* **Published codes (out of scope, recorded for completeness)**: 171 CodeBreaker
  entries (ROMSFUN, Neoseeker, SuperCheats), 15 for SSS2 (libretro .cht) — all RAM
  patches; none is an input sequence.

## 6b. Enumeration

**Space definition / result: the representable "cheat space" is empty for the retail
input path.** Bounded negative, with the exact searched spaces and counts:

| Surface searched | Space checked | Result |
|---|---|---|
| Password text in ROM | whole 8 MiB, ASCII case-insensitive: `PASSWORD` 0, `CHEAT` 0, `SECRET` 0, `MASTER` 0, `SOUND TEST` 0, `LEVEL SELECT` 0; `DEBUG` 5 (all scene names) | No password table/alphabet |
| Shift-JIS text bank | full-width encodings of `DEBUG`, `PASSWORD`, `CHEAT`, `SECRET`, `MENU`, `SOUND`, `TEST`, `MASTER`, `LEVEL`, `SELECT` — 0 hits each; katakana `パスワード`/`デバッグ`/`裏技` — 0 hits; decoded all ≥12-byte Shift-JIS runs in `0x0870D00`-`0x0871200` | No hidden menu/password label |
| Debug scene names | 2,640 table slots; 5 DEBUG entries at indices 5-9 | Names exist, no reachable selector |
| Debug overlay `0x08001528` | full-ROM Thumb BL scan (42,839 BL sites decoded): **0** refs; 32-bit pointer scan incl. Thumb-bit `0x08001529`: **0** refs | Dead code |
| Debug setter `0x08001B08` | full-ROM BL scan: **0** refs; only writer of var `0x80` is at `0x08001B3E` inside that dead function | Debug word cannot be set by input |
| Debug word `0x02000180` | savestate RAM reads at title, field, COMMAND menu: `0x0000` in all | Gate closed (Observed) |
| Button matcher | 1 KEYINPUT reader (`0x0800BE44`); 171 literal references to the five key globals (104+36+2+25+4); no multi-button mask table, no sequence ring buffer, no progress index found | No button-code system |
| Title-screen combos (8 tried) | L+R+Start; L+R+Select+Start; Start+Select; A+B+Start+Select; L+R+A+B; Konami sequence; U/D/L/R; long L+R+Start — each from a title savestate | All either no-op or the normal "New Game" path |
| Field combos (6 tried) | L+R+Start; L+R+Select+Start; Select+Start; L+R+A+B+Right; Up/Down/L/R; A+B+Start — each from a field savestate | All no-op or normal COMMAND menu; EWRAM MD5 `8b3aa629de22` unchanged |
| Reachable menus | title 1 entry; COMMAND 8 entries; List 2 entries | No hidden/unlabelled entries |

Because there is no validator, **no novel code was generated** and there are no
rejection bounds to demonstrate; the deliverable is the counted negative above rather
than a fabricated code. If a future revision exposes the DEBUG scenes, the natural
first experiment is writing `1` to `0x02000180` (via save patch) and observing whether
`0x08001528` becomes live — that would be a *debugger-induced* result, not an in-game
code, and must be labelled as such.

## 7. Validation evidence

* **Observed:** all screenshots (title, character select, field, COMMAND, List,
  combo outcomes); RAM values read from decompressed `gbAs` chunks; EWRAM hash equality
  across six in-field combos; savestate load verified by exact frame return.
* **Derived:** all xref/pointer counts; KEYINPUT reader and key-global semantics;
  debug-word setter/getter reconstruction; 2,640-entry scene table; text-bank decoding.
* **Inferred:** that the five DEBUG scenes were a developer-only facility left in the
  retail image (the strong zero-reference counts make this high-confidence, but no
  live breakpoint confirmation was obtained — see Unknowns).
* **Tooling caveat:** mGBA 0.10.5's GDB stub was single-use/unreliable in this
  environment (packet timeouts, "Cannot execute this command while the target is
  running", "Invalid hex digit"); `-d` console produced no output. RAM evidence was
  therefore collected via savestate diffs as prescribed by guide §16.13.

## 8. Unknowns

* **Battle screen not walked.** Reaching a battle requires progressing the story; no
  battle-specific hidden command was verified. The TITLE/field/menu surfaces — the
  usual hosts for in-game cheats — were fully walked.
* **Post-game content not triggered.** Boss Attack mode and labyrinth 51-100 require a
  completed save; they are clear-flag unlockables, not input cheats, and were not
  exercised in-game.
* **No live breakpoint on the debug overlay.** Static zero-reference counts are strong,
  but a breakpoint that never fires could not be held long enough with this GDB stub.
* The CONSOLE menu labels and full-width text bank were decoded as Shift-JIS pairs;
  the complete 2,640-name table was not translated (only structure/counts were needed).

## 9. Tooling

Scripts in `/tmp/opencode/summonnight1/`: `dis.py` (Capstone Thumb disassembler),
`state.py` (gbAs zlib savestate RAM reader), `ui.py` (xdotool/scrot driver),
`combos.py` (combo test loop), `mgba_console.py`/`testconsole.py` (abandoned `-d`
experiment). Tools: `arm-none-eabi-objdump`, `capstone`, `gdb-multiarch`, `mgba 0.10.5`,
`Xvfb`, `openbox`, `xdotool`, `scrot`, ImageMagick, Python 3. No GameShark/CodeBreaker/
AR code was applied at any point.

## 10. Legal note

No ROM image, extracted graphics, music or game text is redistributed here. Only
hashes, addresses, counts and the author's own analysis scripts are published.
