# The Hobbit: The Prelude to the Lord of the Rings (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/The Hobbit: The Prelude to the Lord of the Rings/The Hobbit: The Prelude to the Lord of the Rings.gba` |
| Size | 8,388,608 bytes (0x800000, 8 MiB) |
| Header title (`0xA0`) | `HOBBIT US` |
| Game code (`0xAC`) | `AH9E` |
| Maker (`0xB0`) | `7D` |
| Version (`0xBC`) | `0x00` (Rev. 00) |
| Fixed `0x96` at `0xB2` | present (stock) |
| Complement `0xBD` | `0x4F` |
| Header checksum `0xBE` | `0x0000` (normal rebuilt-header artifact, §16.1) |
| Entry branch `0x00` | `0xEA00002E` → `b 0xC0` (stock; no cracktro/trainer patch) |
| MD5 | `03aaa67fcb972ec6bce6f1c6863026da` |
| SHA-1 | `70d04d6d3ab8a1bfc4fa1a26d55cd4f73f84d479` |
| SHA-256 | `b911978db02a94500eeb82dfce1d8ef13dd2bc69075b8bedf4daad18f1b2c9a2` |

`file(1)` reports `Game Boy Advance ROM image: "HOBBIT US" (AH9E7D, Rev.00)`. The Saffire
logo plays on first boot; `DEVELOPED BY SAFFIRE, INC.` appears in the in-game credits
(`0x0831ACB4`). This is the same Saffire engine family as *LEGO Bionicle*, which **does**
have name-coded cheats — so the name-entry surface was treated as the primary candidate
before the negative was accepted (§16.11).

## 2. Executive summary

**No developer-intended cheat code system, button code, or reachable hidden/debug menu exists
in this retail image.** The game is save-based (SRAM), not password-based.

The only code-shaped surface is a **name-entry keyboard** on the New Game flow. It accepts
36 symbols (`A`–`Z`, `1`–`9`, `0`) into a 9-character buffer. An exhaustive static search
found **no table of accepted names and no validator over that buffer**: the only `strcmp`
literals referenced from code are `BILBO` (the pre-filled default player name) and `ELROND`
(a *story* word, see below). A novel name `AZQX74` and the special word `ELROND` were both
entered on the real screen; both produced an ordinary new game (§6b). The name field is a
**label**, not a validator (§16.2b).

A single developer-planted *in-story* password does exist: **`ELROND`**. The game itself
hints it ("THANK YOU! HERE IS MY SECRET: USE ELROND'S NAME AND YOU MAY CROSS THE BRIDGE.",
`0x08345250`). `0x080407CC`–`0x08040824` calls `strcmp(0x03005DB8, "ELROND")`, where
`0x03005DB8` is a separate 6-character **spoken-word buffer**, and on a match sets a flag
and runs a 90-frame event. This is a story puzzle solution, not a cheat/unlock code; its
bridge effect is **Derived**, not observed (the bridge was not played through).

`SOUND TEST` / `SOUND MENU` strings survive in the localized UI bank, but they are **dead
data**: 0 code xrefs, 0 BL references, 0 32-bit pointers (including Thumb-bit and RAM forms),
and no menu item on any reachable screen selects them (§16.3 / §16.21). `SELECT+L+R` is the
documented sleep-mode combo, and `A+B+Start+Select` is a soft reset to the credits/title —
neither is a cheat.

## 3. How to reproduce

* Emulator: `mgba -3` (0.10.5) under `Xvfb :316` + `openbox`, `SDL_AUDIODRIVER=dummy`.
* GBA keymap (mGBA SDL): `A`=`x`, `B`=`z`, `L`=`a`, `R`=`s`, `Start`=`Return`,
  `Select`=`BackSpace`, D-pad = arrow keys. Holds of 60–150 ms; 100–900 ms gaps.
* Screen path (fresh save): boot → Sierra splash → Saffire splash (first boot) → title
  `PRESS START` → `PLAY GAME` → three `NEW GAME` slots → slot 1 → **name keyboard** →
  type a name → `DONE` (4× Down from `A`, then `A`) → story map → intro dialogue → gameplay.
  Pause with `Start`: `RESUME / GO TO LAST SAVE / OPTIONS / SLEEP MODE`; `OPTIONS` →
  `SOUND FX / MUSIC / BACK`.
* Codes/names entered on the real screen: `ELROND`, `AZQX74`, `BILBO` (default), `A`.
  Each was followed by `DONE` and the resulting screen captured.
* RAM evidence: mGBA `.ss1` savestates were decoded by extracting the zlib `gbAs` PNG chunk
  (§16.13). Raw state is 397,312 bytes; IWRAM begins at raw `0x19000`, EWRAM at `0x21000`.
  The name buffer sits at raw `0x1A4D0` → IWRAM `0x030014D0`. Typing `A` changed
  `raw[0x1A4D0]` from `0x20` to `0x41`, proving the mapping (observed).
* Web recon (§3.4) was attempted but was unproductive: GameFAQs, TCRF and CheatCC returned
  HTTP 403; the search integration returned no results for eight queries; Google/Bing via a
  real browser returned bot challenges. No published code list was available to verify, so
  the negative rests on ROM-internal enumeration (§6b).

## 4. Address map

All ROM addresses are `0x08000000 + file offset`.

| Address | Meaning | Evidence |
|---|---|---|
| `0x08305964` | Keyboard char-pointer table: 36 entries, `ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890` (1-char NUL strings) | Derived: pointer run; refs at `0x08041474`, `0x080465B4` |
| `0x08320740`–`0x08320790` | Keyboard row label strings (`A B C D…`, `U V W X…`, etc.) | Derived: byte dump |
| `0x0832079C` | Default player name `"BILBO"` | Derived: literal + refs `0x0804A188`, `0x0804A4EC` |
| `0x0831F620` | Story password string `"ELROND"` | Derived: literal + refs `0x080407FC`/`0x080400` region |
| `0x0806A6D4` | `strcmp(const char*, const char*)` (word-at-a-time then byte) | Derived: disassembly |
| `0x080407D0`, `0x0804081C` | `strcmp(0x03005DB8, "ELROND")`; match sets flag + 90-frame event | Derived: disassembly + literal reads |
| `0x0804A4D4` | `strcmp(0x03005DD0 /*player name*/, "BILBO")` → default-name UI path (`0x0804AA08`) | Derived |
| `0x0806D320`, `0x0806D32C` | `strcmp` against 1-char strings `0x087E77B0` / `0x087E77A8` (parser constants) | Derived |
| `0x080413C0`–`0x08041500`, `0x08046480`–`0x0806660` | Keyboard input/render handlers (char table lookup, cursor, 10-char cap) | Derived |
| `0x083099FC` | Localized UI text table: 43 records × `0x1C` bytes; each = 5 pointers (EN/ES/FR/DE/IT) + `0x0835006C` + `1` | Derived: pointer-pattern walk |
| `0x08309CF0` | Table record 27 = `SOUND TEST` (and record 28 `SOUND MENU`, 29 `OPTIONS`, 30 `PLAY GAME`) | Derived |
| `0x030014D0` | IWRAM name-entry buffer, 9 chars + NUL (raw ss1 `0x1A4D0`) | Observed: typed `A` → `0x41` |
| `0x03005DB8` | Spoken-word buffer (6 chars) used by the ELROND check | Derived |
| `0x03005DD0` | Saved player-name string (10 chars) | Derived |
| `0x04000130` | KEYINPUT; read in crt0/input init at `0x08000490`, `0x08000824`, `0x080008F8`, `0x08000E60` | Derived |

## 5. Algorithm / pseudocode

Name entry (Derived from `0x080413C0`, `0x08046480`):

```
alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"   # 36 symbols, @0x08305964
buf = @0x030014D0                                   # 9 bytes + NUL
on_key(char):
    if char == SPACE: backspace
    elif char == row_sep: next row
    else: buf[len++] = char; if len > 9: wrap
on_DONE: copy buf -> save player name @0x03005DD0; continue normal New Game
```

There is **no validation branch** on `buf`: it is never compared with a code table. The
only byte comparisons against a name-like buffer are the two `strcmp` sites in §4, both
against fixed literals (`BILBO`, `ELROND`) in unrelated UI/story handlers.

Story word check (Derived, `0x080407CC`):

```
if strcmp(@0x03005DB8, "ELROND") == 0:
    flag = 1; ui_byte = 1; event(0x1D, 0); delay(90 frames)
elif scene_state == 6 and strcmp(...) != 0:
    event(0x63); delay(20 frames); flag = 1
```

## 6. Tables

| Table / item | Address | Size | Notes |
|---|---|---|---|
| Keyboard alphabet | `0x08305964` | 36 pointers | `A`–`Z`,`1`–`9`,`0`; digits are **1..9,0** (screen order), not `0..9` |
| Name buffer | IWRAM `0x030014D0` | 9 chars + NUL | Default `BILBO` pre-filled by bar-store at `0x08059AE`–`0x0805A1E` |
| `strcmp` literals in code | — | 2 name-like | `ELROND` (`0x0831F620`), `BILBO` (`0x0832079C`); plus 1-char parser constants |
| Spoken-word buffer | IWRAM `0x03005DB8` | 6 chars | ELROND story check |
| UI text bank | `0x083099FC` | 43 × `0x1C` | 5 languages + 2 fillers per record |
| Reachable menu items | — | title 1 (`PRESS START`); main 3; OPTIONS 3; MAP 0; slots 3; keyboard 38 cells; pause 4; pause OPTIONS 3 | full enumeration in §6b |

## 6b. Enumeration

**Requirement (§0.2): bounded negative with counts.** The accepted set of *cheat* inputs
is empty; the counts below define the searched spaces.

1. **Name-entry space.** Alphabet 36, length 1–9 →
   `sum(36^k, k=1..9) = 1.06 × 10^14` representable strings. The buffer has no validator:
   `strcmp` has exactly **5 call sites in the whole ROM**; the only name-length literals
   compared are `BILBO` and `ELROND`, neither of which is a cheat. No table of accepted
   names exists (a full 8 MiB scan for pointer-runs to short uppercase strings found only
   level/area names, language names, `ELROND`, `BILBO`, and float-formatting constants).
   **Tested on the real screen:** `ELROND` → ordinary new game + normal dialogue; novel
   `AZQX74` → ordinary new game + normal dialogue (screenshots `novel_azqx74.png`,
   `novel_after.png` in `/tmp/hobbit/`); default `BILBO` → normal. No distinct
   effect for any name.
   Therefore the name field is a label, not a code (§16.2b).
2. **Button-code space.** Scanned all of `0x08000000`–`0x081FFFFF` as `u16` runs of
   active-high/active-low GBA key masks: **34 runs of length ≥ 5**, every one an
   instruction-stream/data false positive (e.g. `0x08085C4C`, `0x080872D2`); no entry has
   a terminator or a consuming validator. `SELECT+L+R` is sleep mode (UI strings at
   `0x08312BC`–`0x08312E4`, prompt `0x08313AC`); `A+B+Start+Select` was **observed** to
   soft-reset to the credits/title (`combo_abst.png` in `/tmp/hobbit/`), not to
   open a menu. A Konami-style
   sequence produced no change beyond that reset state.
3. **Hidden/debug menu space.** The full localized UI bank has 43 records; record 27 is
   `SOUND TEST`, record 28 `SOUND MENU`. Counts: **0** 32-bit pointers to
   `0x08309CF0`/`0x08309E24` anywhere in ROM (byte-aligned), **0** in RAM savestate,
   **0** BL/xrefs in Ghidra raw-binary auto-analysis, and **0** reachable menu item on
   every screen walked (title, main, OPTIONS, MAP, slots, keyboard, gameplay HUD, pause,
   pause OPTIONS). These strings are dead developer data (§16.3/§16.21), not a feature.
4. **Reachable screens walked (with RAM evidence via savestate decode):** Sierra splash;
   Saffire splash; title; main menu; OPTIONS; MAP; 3 save slots; name keyboard; story map;
   intro dialogue; gameplay HUD (30/30); pause menu (4 items); pause OPTIONS (3 items);
   collectible-map screen; credits/soft-reset. Every screen's labels come from the decoded
   ASCII UI bank, so "no hidden menu item" is an enumeration result, not a string-scan
   absence (§11 / §16.11).
5. **Developer-intended password (not a cheat):** `ELROND`, 6 characters, compared by
   `strcmp` at `0x0804081C` against the 6-char spoken-word buffer. The game's own hint text
   at `0x08345250` documents it. Its effect at the bridge is **Derived**, not observed;
   reaching that point was out of scope for this pass.

**Novel code requirement:** inapplicable — no code system exists. The closest deliverable
is the novel *name* `AZQX74`, entered and rejected as a cheat (identical normal start),
which bounds the negative: no accepted set exists in the 36^1..9 name space.

## 7. Validation evidence

* **Observed:** all screenshots listed in §3/§6b; typed `A` and `AZQX74` in mGBA; savestate
  raw bytes `raw[0x1A4D0] = 0x20 → 0x41`; menu item counts from rendered screens.
* **Derived:** keyboard alphabet table and its code refs; `strcmp` implementation and all
  5 call sites; the two name-like literals; the 43-record UI table and the dead `SOUND TEST`
  records; the `ELROND` comparison and 90-frame event loop; key-mask run scan.
* **Inferred:** that the `SOUND TEST` records belonged to a developer build that was cut
  from retail; that `ELROND` opens/crosses the bridge as the hint text says (validator read,
  but the bridge was not played through).

## 8. Unknowns

* The exact on-screen effect of a correct `ELROND` at the bridge was not played through.
* The 6-char spoken-word screen's trigger location in the game was not reached; only its
  validator and buffer were located statically.
* Whether any of the 36 keyboard symbols has an alias collision when the buffer is written
  directly by RAM patching (not reachable from the on-screen keyboard).
* Web-based published lists could not be retrieved (403/bot checks), so this report does not
  claim to compare against an external code list; the enumeration is ROM-internal.

## 9. Tooling

* `mgba 0.10.5` (`-3`, `-d`, `-g` tried; GDB stub port 2345 was occupied by another
  session, so `-d` and savestate diffing were used instead), `Xvfb :316`, `openbox`,
  `xdotool` (XTEST), `scrot`, `ImageMagick`.
* `arm-none-eabi-objdump -M force-thumb`, Capstone 5.0.7, REA/Ghidra 12.1.4 raw-binary
  import (base `0x08000000`, architecture ARM; session closed at end).
* Work scripts in `/tmp/hobbit/`: `findptr.py`, `findtext.py`, `scanmasks.py`,
  `ss.py` (savestate `gbAs` extractor), `type_name.py`, `combo.py`, `k.sh`, `shot.sh`.
* No ROM or copyrighted assets are redistributed; only addresses, hashes and findings are published.

## 10. Legal note

No ROM bytes, extracted graphics, or game text were copied into this report beyond short
identifiers needed to document addresses. All findings are reproducible from the address
map and the reproduction steps above.
