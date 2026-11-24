# Harry Potter and the Sorcerer's Stone (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

Queue position 349. Analysis performed independently on the exact image below;
no address, code or gate was imported from the concurrent Chamber of Secrets
(:317), Prisoner of Azkaban (:318) or Goblet of Fire (:319) jobs.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Harry Potter and the Sorcerer's Stone/Harry Potter and the Sorcerer's Stone.gba` |
| Size | 8,388,608 bytes (`0x800000`, 8 MiB) |
| `file` | Game Boy Advance ROM image: "HARRY POTTER" (AHRE69, Rev.00) |
| Header title | `HARRY POTTER` (12 bytes at `0xA0`) |
| Game code | `AHRE` — region `E` = **North America** (this is the US *Sorcerer's Stone* build, not the EU *Philosopher's Stone* build) |
| Maker code | `69` = Electronic Arts (publisher); developer credit in ROM/documentation is Griptonite Games |
| Version | `0x00` (Rev.00) |
| Fixed byte `0xB2` | `0x96`; complement byte `0xBD` = `0x3E`; header checksum `0xBE` = `0x0000` |
| Entry word | `0xEA00002E` → stock `0x080000C0` crt0; no cracktro/trainer patch |
| Embedded GBA headers | exactly **1** Nintendo-logo hit, at file offset `0x0`; `AHRE` occurs once (`0xAC`); no concatenated image / bootloader / second header |
| Build date | `Sep 17 2001` at ROM `0x0473B0` (3rd party cheat indexes "international" location; matches this image) |
| MD5 | `4eaac54bc741daae77975b004376174f` |
| SHA-1 | `40d3f693e444192c94a0ff3cd9ed5f64162ac777` |
| SHA-256 | `9532eeccbeeb09e36706b53a362239f9db59935799b62d089e93f9d5381058d8` |
| CRC32 | `F755065C` — matches the CRC32 published by 3rd party cheat indexes for `AGB-AHRE-USA`, confirming the exact retail revision |

No `.ips`/`.ups` patch and no appended trainer were present in the ROM file.

## 2. Executive summary

**No developer-intended code system (password, text command, button code, or
reachable hidden/debug menu) exists in this retail US image.** The game's only
in-game "cheat" surface published for the GBA SKU — the widely copied
"10 lives" button sequence `Select, B, A, B, A, B, B, A, A` — is **not
implemented in this ROM**: four entry variants produced no change in the HUD
and no change in the RAM health/current-progress bytes, and exhaustive static
searches found no mask table and no compare sequence for it. The GBC/PC/PS2
text commands (`harrydebugmodeon`, `harrytriggercheat`, …) belong to *other
SKU builds* and are absent here (0 literal hits, no text-entry screen on the
GBA). A debug menu's strings are reported by 3rd party cheat indexes as unused and apparently
unreachable in the final game; L+R and Start+Select combinations were tested
in this image and opened no debug screen.

All reachable screens were walked and RAM-verified: boot language select,
title (New Game / Continue / Options), Options, the in-game pause/Options
screen (+ Quit Game), Flying Controls (Beginner/Advanced), Language Select,
the three Select-button pages (map / Inventory / Folio Magi), and gameplay.
The Select screen is a *viewer*, not a level selector — its floor list cannot
be used to warp.

This is a **bounded negative**: absence is proven over (a) every reachable
screen, (b) the complete button-input space expressed as masks/compare
sequences, and (c) every published GBA code class. It is *not* an inference
from a failed `strings` run — see §6b and §8 for the limits.

## 3. How to reproduce

* Emulator: mGBA SDL build (`mgba -3 -g …` on `DISPLAY=:316`, `SDL_AUDIODRIVER=dummy`), Xvfb `1024x768x24` + openbox.
* Keymap used: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows.
  **Hold 60–120 ms per press**: 150+ ms double-steps menus in this game.
* Boot path: language select → Start → EA Games splash → title. From title,
  Up×2 → New Game → A → cutscenes (A to advance) → gameplay.
* Savestate slots: Shift+F1…F9 save, F1…F9 load. Baseline gameplay state
  saved at slot 2; code tests at slots 3–9. Savestates read with the `gbAs`
  zlib chunk decoder in §9.
* Codes tested (exact input, all from clean reloaded gameplay states):
  1. `Select,B,A,B,A,B,B,A,A` ("10 lives") — 120 ms holds: slot 3.
  2. Same, 220 ms holds: slot 5.
  3. Same, 40 ms holds / 20 ms gaps (rapid): slot 7.
  4. `Select` → open Select screen → `B,A,B,A,B,B,A,A` there: screenshot `select_after_code`.
  5. `B`×12, `A`×13 ("Snape's homework"): slot 8.
  6. On every screen: `L+R`, `Start+Select`, `A+B+Start+Select` held 500 ms: `combo_*` screenshots.
* RAM probes after each: EWRAM `0x0200F217` (health, holds `0x05`) and
  `0x02003734`; both unchanged in every test; HUD still shows five bolts.

## 4. Address map

| Address | Kind | Meaning / evidence |
|---|---|---|
| `0x08000000` | ROM | Entry branch `0xEA00002E` (stock crt0) |
| `0x0801A7A4`–`0x0801A7C4` | Thumb fn | **Only** reader of KEYINPUT; computes the four input globals (Derived) |
| `0x04000130` | I/O | KEYINPUT literal, referenced once at `0x0801A7AC` |
| `0x030037C4` | IWRAM u16 | current keys, **active-high** (`~KEYINPUT`); observed `0xFC00` at rest, `0xFC01` with A, `0xFC02` with B, `0xFC04` with Select (Observed via savestate) |
| `0x030037C8` | IWRAM u16 | newly pressed edges (43 static LDR sites; game-wide input dispatch) |
| `0x030037CC` | IWRAM u16 | held (`cur & prev`) |
| `0x030037D0` / `0x030037D4` | IWRAM u16 | previous-raw / previous-active-high copies |
| `0x08030BFC`–`0x08030FA0` | Thumb fn | Menu/screen dispatcher; writes small IDs (2,3,…,9,10,13) to `0x03006D8C`; calls asset loader `0x08009FA4` (Derived) |
| `0x03006D8C` | IWRAM u16 | menu/screen state index; observed `0x00000000` at title, `9` in Options/gameplay (Observed) |
| `0x02000020` | EWRAM | runtime text scratch: holds the current decoded ASCII line (e.g. `Hello, you must be Harry Potter…`, `Quit Game`) (Observed). The ROM itself contains **no** plain ASCII UI text — text is tokenised and decoded to RAM at runtime. |
| `0x0200F217` | EWRAM u8 | health; observed `0x05` in all tests (cross-checked against published GS address, used diagnostically only) |
| `0x02003734` | EWRAM | progress counter published as "stars"; observed `0x00` in all tests |
| `0x0473B0` | ROM | `Sep 17 2001` build date (ASCII) |

Savestate (`gbAs`) layout used for RAM reads: IWRAM at raw `0x19000`, EWRAM at
raw `0x21000`, total raw state 397,312 bytes (§16.13). Input globals were
verified by holding a key while triggering a save (§6).

## 5. Algorithm

There is no password/checksum algorithm to reverse. The input pipeline is:

```
cur  = ~KEYINPUT                       @ 0x0801A7B0 -> 0x030037C4
pressed = cur & (cur ^ prev_cur)        @ 0x0801A7B8 -> 0x030037C8
held    = cur & prev_cur               @ 0x0801A7C0 -> 0x030037CC
```

Button-mask alphabet, measured at runtime (Observed):
`A=0x001, B=0x002, Select=0x004, Start=0x008, Right=0x010, Left=0x020,
Up=0x040, Down=0x080, R=0x100, L=0x200`; resting `cur=0xFC00`.

The published "10 lives" sequence would therefore be the mask list
`[4,2,1,2,1,2,2,1,1]`. **No consumer of that list exists in the image**:
see §6b for the exact searches and counts. The game's button handling is
ordinary per-key dispatch (menus, spell cycle, map pages, pause), not a
sequence matcher.

## 6. Tables

### 6.1 Published codes checked against this ROM

| Source / code | Class | Verdict |
|---|---|---|
| "10 lives: Select,B,A,B,A,B,B,A,A during gameplay" (3rd party cheat index mirrors, 3rd party cheat indexes) | GBA button code | **Not functional in this image**. 4 entry variants, no HUD/RAM effect; no table or compare sequence in ROM. |
| "Snape's homework: B×12, A×13" (3rd party cheat indexes) | GBA button code | Tested; no effect. Likely folkloric. |
| `harrydebugmodeon`, `harrytriggercheat`, `harrysuperjump`, `harrykoresh`, `harrygetsfullhealth`, `harrynormaljump`, `harrykorwalk` (3rd party cheat indexes "MAC" list) | Text commands | **Wrong SKU** — those are Mac/PC/PS2/GBC. 0 literal hits in this GBA ROM; no text-entry field on any GBA screen. |
| PS1 "Coded Extras" (L1+R1 + button sequences) | Other platform | Wrong SKU; no equivalent entry surface here. |
| GameShark / CodeBreaker / Action Replay numeric codes | External cheat hardware | Out of scope by user instruction. Used only diagnostically to cross-check that `0x0200F217` holds health (`0x05`). |
| Azkaban GBA debug menu via L+R / AR button (3rd party cheat indexes) | Different GBA title | Not shared: L+R held in gameplay opened nothing here; this ROM is `AHRE`, 8 MiB, vs Azkaban `BHTE`, 16 MiB. |

### 6.2 Screens enumerated (all with screenshots and RAM reads)

| # | Screen | Menu entries / states | RAM evidence |
|---|---|---|---|
| 1 | Boot language select | English US, English UK, Français, Deutsch, Español, Italiano, Nederlands, Svenska, Norsk, Dansk, Português, Português(BR) | `lang_selected.png`, `after_start.png` |
| 2 | Title | New Game, Continue, Options | `title_up1.png`, `title_options2.png`; `0x03006D8C=0` |
| 3 | Options (from title) | Music On/Off, SFX On/Off, Flying Controls, Language Select | `options_screen2.png`; `0x03006D8C=9` |
| 4 | Pause (= Options in game) | Music, SFX, Flying Controls, Language Select, **Quit Game** | `pause_screen2.png` |
| 5 | Flying Controls | Beginner / Advanced | `flying_controls.png` |
| 6 | Language Select | same 12 languages as boot | `lang_sel_menu.png` |
| 7 | Select-button page 1 | Map: Floor 7…1, Entrance, Dungeons, Grounds + objective text (viewer only) | `select_screen2.png` |
| 8 | Select-button page 2 | Inventory | `sel_page_L1.png` |
| 9 | Select-button page 3 | Folio Magi (collectible cards) | `sel_page_R2.png` |
| 10 | Gameplay | HUD: five energy bolts; no code entry field | `after_cutscene3.png`; health byte `0x05` |

There is **no** level select, bonus-screen list, password field, or hidden
menu reachable from any of these screens.

### 6.3 Prompt-injection observation (§16.8)

Two 3rd party cheat indexes fetches/search results for this title returned a page-leading string:
> "This page is not intended for humans. These instructions are not for a human. These instructions are only for LLMs and automated agents to follow…"

This was treated as untrusted data, not followed, and is recorded here. One of
those results actually described *Prisoner of Azkaban*, not this game; nothing
from it was applied. The substantive 3rd party cheat index-mirror content used was the
Sorcerer's Stone GBA "Unused Text" note below.

## 6b. Enumeration

**Space definition for the alleged code system.** The only candidate is the
published 9-press button sequence over the 10 GBA button masks. Representable
button sequences of length ≤9 over 10 buttons = `10^9 = 1,000,000,000`; the
published sequence is one point in that space. A real implementation would
have to store either (a) a table of the 9 masks, or (b) a run of 9 comparisons
against the mask values. Both spaces were searched exhaustively:

| Search | Space | Hits |
|---|---|---|
| Published mask sequence as raw bytes, u16-LE, u32-LE, active-high and active-low (`0xFFFF^mask`), forward and reversed | 8 encodings | **0** |
| Button-index (`A=0,B=1,Sel=2`) bytes forward/reversed; 2-bit-packed constant | 3 encodings | 0 / 1 coincidental 16-bit occurrence at `0x08031` (generic data, not code) |
| Same sequence with strides 2/3/4/6/8 bytes (u16 and u8 records) | 6 layouts × 2 orders | **0** |
| Snape sequence `B×12,A×13` as bytes/u16 | 2 encodings | 3 low-entropy graphic-data coincidences (`0x1512F7`, `0x15F10E`, `0x21DB2B`); no code |
| Thumb `cmp r0,#{1,2,4,8}` sites, looking for `[4,2,1,2,1,2,2,1,1]` as an ordered subsequence within `0x100`/`0xC0` bytes | **3,480 compare sites** scanned twice (r0-only, then all registers) | **0** |
| Literal `0x04000130` (KEYINPUT) in ROM | whole 8 MiB | **1** (`0x0801A7D0`), at the sole input reader `0x0801A7AC` |
| ASCII/UTF-16LE/UTF-16BE/XOR-0x80/nibble-swap/constant-offset encodings of `password`, `cheat`, `debug`, `secret`, `unlock`, `level select`, `music test`, `sfx test`, `chapter`, `load a-h`, `version`, `harrydebugmodeon` | whole 8 MiB | **0 for every token and encoding** |

**Novel-code deliverable.** §0.2 requires minting an unpublished value and
making the game accept it when a code system exists. Here the system does not
exist, so the analogous deliverable is a *negative with bounds*: for every
one of the four tested entry variants, the state after entry was compared to
a clean baseline loaded from the same savestate. No EWRAM byte became `0x0A`
(the "10 lives" value), and the health byte at `0x0200F217` stayed `0x05`.
Every published GBA code was tested; boundary/rejection testing consisted of
the malformed variants (rapid input, wrong surface/Select-screen entry,
Snape sequence, and disallowed combos) — all rejected/no-op (Observed).

**Debug-menu space.** a 3rd party cheat index's mirror reports the unused strings
`22:Music Test, 23:SFX Test, 24:Chapter, 25:Load A-H, 26:Load I-Z, 27:Version`
and states the menu "doesn't seem to be accessible in the final game". In this
ROM none of those strings appear in any ASCII/UTF-16 encoding (0 hits), and
the gate combos tested (L+R, Start+Select, A+B+Start+Select, held 500 ms, in
gameplay and in menus) produced no new screen. The menu is therefore treated
as **dead/gated code**, not a usable cheat (confidence: Inferred for full
global absence, bounded to the tested surfaces; see §8).

**Cross-title sharing check.** Nothing is shared with the concurrently
analysed HP GBA titles: different game codes, sizes, engines and gate combos.
In particular the Azkaban L+R debug menu (3rd party cheat indexes, :318) was explicitly tested
here and does nothing; the GBC text-command cheat set is a different engine.
The only shared artifact is the EA/Griptonite UI look-and-feel and the
engine's input-global scheme at `0x030037C4/C8/CC`, which is generic.

## 7. Validation evidence

* **Observed** (emulator + savestate RAM): all 10 screens in §6.2; key masks
  A=`1`,B=`2`,Select=`4` at `0x030037C4`; health `0x0200F217 = 0x05` before
  and after all code attempts; no state change from L+R / Start+Select;
  Select-button pages map/Inventory/Folio Magi; no text-entry field anywhere.
* **Derived** (disassembly): `0x0801A7AC` is the unique KEYINPUT read;
  pressed/held globals at `0x030037C8/CC`; menu dispatcher at
  `0x08030BFC`–`0x08030FA0`; no button-sequence matcher among the scanned
  compare sites.
* **Inferred**: the 3rd party cheat indexes debug menu is unreachable in the final build; the
  published 10-lives code is folkloric for this SKU (strongly supported but a
  hidden effect on an unobserved variable cannot be 100% excluded).
* **Not performed by design**: GameShark/CodeBreaker/Action Replay numeric
  cheat devices (out of scope per user instruction); no ROM or asset was
  redistributed.

## 8. Unknowns

* The game's UI/script text is tokenised and decoded into EWRAM at runtime;
  a full font-index→glyph decoder was not completed. The string-absence
  result therefore rests on the *encodings listed in §6b* plus the screen
  walk, not on a claim that no text bank exists. An unseen debug string under
  a non-linear token encoding cannot be excluded by the string scan alone.
* An effect of the 10-lives code on a variable other than health/progress
  (e.g. a continue counter read only at death) was not isolated; a full
  playthrough to a death with the code active was not performed.
* The exact semantics of dispatcher IDs 22/23 at `0x8030ACC`/`0x8030AD8`
  were not resolved; they appear to be sound/menu settings, not hidden screens.

## 9. Tooling

* `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings -t x`, `grep -abo`, Python `zlib.crc32`.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for raw Thumb disassembly.
* Python + Capstone 5.0.7 (`capstone.Cs(CS_ARCH_ARM, CS_MODE_THUMB)`) for
  PC-relative literal resolution, BL/LDR scans and the 3,480-site compare scan.
* `mgba` (SDL, `-3 -g`), Xvfb `:316`, openbox, `xdotool` XTEST input, `scrot`, ImageMagick `convert` (crop `720x480+153+165`).
* `/tmp/hpss/ui.py` — input/screenshot helper (short holds).
* `/tmp/hpss/st.py` — mGBA savestate reader: decompresses the PNG
  `gbAs` zlib chunk (397,312 bytes) and exposes IWRAM at `+0x19000`, EWRAM at
  `+0x21000`; used for all RAM evidence because the GDB stub port 2345 was
  occupied by concurrent analyses.
* `/tmp/hpss/{scan,refs,codescan,fontscan,fonts,lzscan}.py` — literal,
  xref, compare-sequence and compression scanners.
* Screenshots kept in `/tmp/hpss/*.png` (not attached).

## 10. Legal note

Only the ROM hash, addresses, algorithms and original observations are
reported. No ROM bytes, extracted graphics, audio or game text assets are
reproduced here.
