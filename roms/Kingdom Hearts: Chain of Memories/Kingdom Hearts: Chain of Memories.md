# Kingdom Hearts: Chain of Memories (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Kingdom Hearts: Chain of Memories.gba` |
| Size | 33,554,432 bytes (32 MiB) |
| Header title | `KINGDOMHEART` |
| Game code | `B8CE` (serial `AGB-B8CE-USA`, region char `E` = USA) |
| Maker code | `GD` |
| Revision / version | 0x00 |
| Entry branch | `0xEA00002E` (stock branch to `0x080000C0`; no cracktro) |
| Fixed byte | `0x96` |
| Complement / checksum | `0x47` / `0x0000` |
| MD5 | `f7b81e3f3bb3b02d973fc6f145ad4416` |
| SHA-1 | `10729bd884f8fdca7a310b6d606c52e46657aa48` |
| SHA-256 | `6f6e7b61bb7b6ef7e2bea6e9dd01e70570a715835cc3713abe86186fd2c4e28d` |

Embedded-header scan: the 16-byte Nintendo-logo signature occurs **once**, at file offset
`0x4`. This is a single-image retail ROM — no multi-game cart, no appended trainer, and no
scene cracktro. No GameShark/CodeBreaker/Action-Replay signature bytes were found in the image.

## 2. Executive summary

**There is no in-game cheat system in this title.** No password screen, password alphabet,
password validator, button-code matcher, or unlockable cheat code exists that a player can
reach through the game's own input surface. The game has no password entry UI; it uses a
battery-backed save (32 KiB SRAM/Flash) with three file slots and a file-select screen.

The game *does* ship an extensive **developer debug menu**, but it is **gated behind a RAM
value that no in-game input ever writes**. The only published activation is an **external
CodeBreaker memory patch** (`3203493C 0006` for US/JP), which is a memory-edit code and
therefore **outside the scope of this engagement**. Per guide §16.3 this is a *gated feature*,
not a code system: the code and label table are present and registered in the shipped ROM
(shipped-artifact evidence), there is a real mode dispatcher that reads the gate byte, and
every in-game path to it was searched and ruled out.

Consequently §0.2's "mint an unpublished code and enter it" requirement is **not applicable**:
there is no code space to enumerate. The negative is bounded instead by (a) full screen
enumeration, (b) counted text/button-space searches, and (c) direct tests of the gate and of
all published material. Full details are in §6b.

Published codes from the web were all **GameShark / CodeBreaker / Action Replay memory
edits** (infinite HP, max cards, "press Select+L+R for all cards", the debug-menu gate, etc.).
None is a developer-intended password or button code, and all are out of scope. No PS2
(`Re:Chain of Memories`) code was found being misapplied to this GBA ROM.

## 3. How to reproduce

* Emulator: mGBA SDL (`mgba -3 <rom>`), `DISPLAY=:316`, `SDL_AUDIODRIVER=dummy`,
  Xvfb `:316` + openbox. Default keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
  Select=`BackSpace`, D-pad=arrows. Note: **do not run this ROM with `mgba -g` on a shared
  host** — port 2345 is single-owner; a foreign GDB stub makes the core render black.
  Use savestates for RAM inspection instead (see §9).
* Menu path walked: title (PRESS START) → title menu (NEW GAME, plus L/R brightness) →
  FILE 1/2 select ("Select a file to use.") → opening cutscene → field/dialogue →
  tutorial battle with card HUD → system reset ("Licensed by Nintendo") screen.
* Input note: long holds (>0.2 s) double-step in some menus; 60–90 ms taps move one slot.
  Opening dialogue advances on A; the whole intro is several minutes of scripted dialogue.
* Codes/activations tested:
  * Gate byte at `0x0203493C` set to `0x06` once via debugger — read back `0x0006`, but
    the new-game init overwrote it (`0x0001` in-game). No menu appeared.
  * Gate byte patched in a raw savestate (`gbAs` chunk, state offset `0x5593C`) to `0x06`,
    reloaded mid-battle — byte stayed `0x06` (verified by re-reading a state) but **no
    visual/menu change**. The gate therefore must be set continuously *before and during*
    new-game initialization, exactly as a cheat device does.
  * mGBA cheat file (both `3203493C 0006` CodeBreaker form and `0203493C:06` VBA form)
    loaded with `-c` — verified the file loads (boot logos render) but mGBA's per-frame
    refresh timing did not reproduce the device's effect on scenario selection (normal
    intro played). This is a harness-timing limitation, not a game finding.
  * Nine button combinations at the title menu (L+R+Start, L+R+Select, L+R+A, L+R+B,
    A+B+Start+Select, L+R+Up+Down, Start+Select, all six, and the Konami sequence) —
    none opened a hidden screen; L/R only changed brightness and the Konami/all-button
    sets produced the documented system reset.

## 4. Address map

File offsets are ROM addresses minus `0x08000000`.

| Item | ROM address | File offset | Evidence |
|---|---|---|---|
| Gate byte (`u8`/`u16` mode variable) | — | — | EWRAM `0x0203493C` |
| Gate literal (pointer to `0x0203493C`) | `0x0805E900` | `0x5E900` | Derived: literal scan |
| Gate literal (2nd pool) | `0x0805EEF0` | `0x5EEF0` | Derived |
| Gate literal (3rd pool) | `0x0805F074` | `0x5F074` | Derived |
| Mode dispatcher (reads `[gate]-1`, 5 cases) | `0x0805EEB0` | `0x5EEB0` | Derived: disassembly |
| Dispatch jump table (5 entries) | `0x0805EEF8` | `0x5EEF8` | Derived: `0x805EF0C/14/1C/38/58` |
| Clear-to-zero writer (`strh 0` to gate) | `0x0805E8B8` | `0x5E8B8` | Derived |
| EU gate address `0x020348DC` literals | `0x0810704`, `0x08107C8` | `0x10704`, `0x107C8` | Derived (not used by this USA build) |
| Mode registry (`mode_*` records) | `0x09ECEB40` | `0xECEB40` | Derived: pointer table |
| `mode_battle` name / handlers | `0x08126624` / `0x080099D1`,`0x0800A4BD`,`0x0800A5A5` | — | Derived |
| `mode_chkbtl` name / handlers | `0x081283B4` / `0x0800A609`,`0x0800A775`,`0x0800AB81` | — | Derived |
| **`mode_debug` name / handlers** | `0x08128580` / `0x0800AC35`,`0x0800AD91`,`0x0800B2E5` | `0x128580` | Observed (shipped bytes) |
| Debug menu labels (full-width Shift-JIS) | `0x08128418`–`0x08128580` | `0x128418`–`0x128580` | Observed |
| `Event_Debug` / `mode_eventselect` names | `0x09033F9C` / `0x09033F1C` | `0x1033F9C` / `0x1033F1C` | Observed |
| UTF-16LE dialogue text bank (14,942 strings) | from `0x0159DE4` (e.g. "Select a file to use." @ `0x0159E1E`) | `0x159DE4` | Observed |
| Font glyph-index tables (ASCII→tile) | `0x0183FC00`–`0x0183FC80`, `0x01A5B182`, `0x01A5B262` | — | Derived |
| Save data | SRAM/Flash `0x0E000000` (32 KiB in emulator `.sav`) | — | Observed |

## 5. Algorithm

The only game-side structure relevant to hidden features is the task-mode gate. Pseudocode
recovered from `0x0805EEB0` (Thumb):

```
mode = *(u16*)0x0203493C;          // literal @0x0805EEF0
idx  = mode - 1;
if (idx > 4) goto default;         // bhi 0x0805EF78 -- values 0 and >=6 fall here
jump table @0x0805EEF8: [0x805EF0C, 0x805EF14, 0x805EF1C, 0x805EF38, 0x805EF58]
case 1: ... store 0xe ; case 2: ... store 0xa ; case 3: ... ;
default: store 3 and run common init
```

`0x0805E8B4`–`0x0805E8F8` is a reset/init helper that clears the gate (`strh 0` at
`0x0805E8B8`) along with a block of neighbouring globals. `0x0203493C` is a 16-bit mode word;
normal title/filedselect value is `0x0000` and in-game value is `0x0001` (both observed via
savestate RAM reads). The CodeBreaker code writes **8-bit** `0x06` to the low byte.

The debug task is a *separate* registered mode in the table at `0x09ECEB40` (records of
`{name_ptr, handler1, handler2, handler3}` for `mode_battle`, `mode_chkbtl`, `mode_debug`).
Its init routine at `0x0800AC34` allocates a menu object (`movs r0,#0x24` → allocator) and
loads the label table at `0x08128418`. The mode word that selects this registered task is the
one the external patch changes; no in-game input routine was found that writes `6` to it.

## 6. Tables

### 6.1 Debug menu label table (shipped ROM, full-width Shift-JIS)

| ROM address | Label (full-width) | ASCII |
|---|---|---|
| `0x08128418` | ＭＡＩＮ | MAIN |
| `0x0812842C` | ＯＢＪＥＣＴ | OBJECT |
| `0x08128440` | ＭＡＰ | MAP |
| `0x08128454` | ＥＦＦＥＣＴ | EFFECT |
| `0x08128468` | ＳＯＵＮＤ | SOUND |
| `0x0812847C` | ＥＶＥＮＴ | EVENT |
| `0x08128490` | ＬＩＮＫ | LINK |
| `0x081284A4` | ＢＡＴＴＬＥ | BATTLE |
| `0x081284B8` | ＰＯＯＨ | POOH |
| `0x081284CC` | ＦＬＡＧ | FLAG |
| `0x081284E0` | ＬＯＧＯ | LOGO |
| `0x081284F4` | ＤＥＬ ＳＡＶＥ | DEL SAVE |
| `0x08128508` | ＯＰＥ ＳＡＶＥ | OPE SAVE |
| `0x0812851C`–`0x0812856C` | ＭＯＶＩＥ１ … ＭＯＶＩＥ５ | MOVIE1–MOVIE5 |

18 entries. This matches TCRF's US/JP debug-menu list exactly. The EU-only additions
(ENDROLL, LANGUAGE, JOURNAL, WORLDSEL, CONTINUE) do **not** appear in this USA image — another
confirmation of the region.

### 6.2 Gate values (observed)

| Value at `0x0203493C` | Where observed | Meaning |
|---|---|---|
| `0x0000` | title screen, title menu | no mode / pre-game |
| `0x0001` | field, battle | normal game mode |
| `0x0006` | only after manual RAM/savestate patch | debug path (external patch only) |

### 6.3 Published material (all out of scope — memory-edit codes)

| Source | Code | Verified in ROM? |
|---|---|---|
| TCRF / KH13 (US/JP debug menu) | `3203493C 0006` → byte `6` @ `0x0203493C` | Yes — RAM literal at `0x0805E900` etc.; shipped debug labels present |
| TCRF (EU debug menu) | `320348DC 0006` → byte `6` @ `0x020348DC` | Literal present (`0x0810704`), but EU-only entries absent; this is the USA build |
| GameFAQs / Neoseeker / SuperCheats / ROMSFUN | "Infinite HP", "Max CP", "All Cards (Select+L+R)", "Gain level (Select+Up)", "Infinite MP", etc. | All GameShark/CodeBreaker/Action-Replay RAM writes; no password/button-code form; out of scope |
| GameFAQs walkthrough | `Start,Select,A,B,L+R = Reset` | Confirmed empirically (system reset screen) — a system function, not a cheat |

Prompt-injection check: all fetched pages (TCRF mirror, GameFAQs, KH13, ROMSFUN,
Neoseeker, SuperCheats, gamehacking.org) were treated strictly as data. No injected
instructions, fake decoder keys, or payment requests were encountered.

## 6b. Enumeration

**Space definition.** There is no password/button-code space to enumerate. The only
hidden-feature state is the single mode word at EWRAM `0x0203493C` (16-bit storage; the
debug patch writes the low byte). Its compiled dispatch covers `1..5` (5 reachable cases);
`0` and `>=6` fall through the `bhi` default at `0x0805EF78`. No on-screen alphabet, literal
code table, key-mask sequence, or validator exists — counted searches below.

**Why this is a complete negative (all four "no" categories from §16.3 checked):**

1. *No system*: ASCII `strings` = 284,367 entries; every password/debug/cheat-keyword hit
   was classified as an asset filename (`*_aob`, `*.acl`), a build/task name
   (`mode_debug`, `mode_chkbtl`, `Event_Debug`, `Event_Debug`, `mode_eventselect`), or an
   unrelated English word. The complete UTF-16LE text bank (14,942 strings, decoded from
   `0x0159DE4` onward) contains **zero** occurrences of "password", "cheat", "debug",
   "unlock", "secret code", or any menu label of that kind. Font/tile-indexed UI was also
   decoded: the label tables are full-width Shift-JIS at `0x08128418`–`0x0812856C`, and
   the ASCII→glyph tables at `0x0183FC00`/`0x01A5B182`/`0x01A5B262` are text renderers, not
   password alphabets. No restricted-input screen exists anywhere in the game.
2. *Dead code*: the debug menu is **not** dead — it is registered in the mode table at
   `0x09ECEB40` with three real handlers and a full label table, so it is real developer
   content.
3. *Cut feature*: not a placeholder — labels are complete and internally consistent.
4. *Gated feature*: the gate is the RAM byte `0x0203493C`. Its only writers are the game's
   own reset/init code (values `0`/`1`) and the external patch (value `6`). Nine button
   combinations at the title and save screens produced no gate change and no debug screen.

**Novel code requirement.** Not applicable — no code system exists. No unpublished code was
minted because there is nothing to mint; this is a bounded negative, not a partial result.

**Bounds proven by rejection.**
* Gate value `6` entered as a one-shot RAM write was overwritten by game init (rejected).
* Gate value `6` patched into a live savestate was accepted as data (byte read back `0x06`)
  but produced no menu — proving the gate alone is not sufficient mid-game; the value must
  be present *before/during* new-game scenario selection, i.e. via continuous external
  injection. This is the documented CodeBreaker behaviour.
* All nine title-screen button sequences were rejected by the game (no hidden screen).
* `L+R+Start` etc. produce only brightness/system-reset effects, bounding the input surface.

**Screen enumeration (all reachable screens walked, each with a screenshot in the work dir
and RAM reads where meaningful):** title, title menu, file select, opening cutscene/dialogue,
field, card-battle tutorial screen, and the system-reset/license screen. No other screen is
reachable without completing the game; the "options" surface on the title is only a
brightness slider (L/R), and the main in-game menu (Start) and pause screens are ordinary
gameplay menus with no cheat/debug entries.

## 7. Validation evidence

* **Observed**: ROM hash/header; single embedded header; 284,367 ASCII strings; 14,942
  UTF-16LE strings; Shift-JIS debug label table and full `mode_*` registry in shipped bytes;
  savestate RAM reads of the gate byte (`0x0000` title, `0x0001` in-game, `0x0006` after
  patch); all screenshots; all nine button-combo results; published-code literal verification.
* **Derived**: mode dispatcher and `bhi` bound at `0x0805EEB0`; 5-entry jump table;
  clear-to-zero writer at `0x0805E8B8`; register/table structure at `0x09ECEB40`; debug init
  at `0x0800AC34`; the four "no system / dead / cut / gated" classification.
* **Inferred**: that the debug menu's *visual contents* match TCRF exactly (the shipped
  label table matches, but the menu itself was never displayed because the required
  continuous external write is out of scope and mGBA's cheat timing did not reproduce it).
  This is explicitly labelled as inferred, not observed.

## 8. Unknowns

* The exact debug-menu screen was not displayed in emulation. Reaching it requires a
  continuous pre-new-game memory write (a CodeBreaker device or an equivalent hook), which
  is a memory-edit technique excluded by the engagement scope.
* The precise instruction that writes `0x0001` to the gate during new-game initialization was
  not isolated. Only four static literal references to `0x0203493C` exist; the writer likely
  reaches the byte through a computed struct pointer (e.g. from the `0x02034890` region next
  to the mode registry). This does not affect the negative conclusion: no input path was found.
* Whether completing the game unlocks any cosmetic extra (e.g. a special movie) beyond the
  documented unlockables (Riku scenario, boss cards) was not tested; those unlockables are
  save-flag progression, not cheats (guide §16.18), and are out of scope.

## 9. Tooling

* `file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings -t x`, `grep -abo`.
* Python 3 with `capstone`/`keystone`; custom scripts in `/tmp/opencode/khcom/`:
  `helper.py` (xdotool input + scrot + crop), `sram.py` (savestate `gbAs` zlib-decompress and
  RAM read; EWRAM at state `+0x21000`, IWRAM at `+0x19000`), `patch_state.py` (savestate
  byte patch + CRC rewrite), `gq.py`/`gdbserver.py` (GDB bridge; abandoned due to port conflict).
* `arm-none-eabi-objdump -M force-thumb` and Capstone for disassembly; REA/Ghidra was tried
  on a 36 KiB extracted window but raw-binary auto-analysis did not recognize the Thumb
  functions (guide §5.5 caveat), so all disassembly claims rest on manual Capstone decoding.
* mGBA SDL 0.10 under Xvfb `:316` + openbox; `SDL_AUDIODRIVER=dummy`.

## 10. Legal note

No ROM bytes, graphics, audio, or full text banks are redistributed here. Only addresses,
hashes, algorithms, short label strings, and analysis scripts are published, all derived from
a legally inspected copy.
