# Driver 2 Advance (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Driver 2 Advance/Driver 2 Advance.gba` |
| Size | 8,388,608 bytes (`0x800000`) |
| Header title | `DRIVER2ADV` |
| Game code | `ADUE` (region USA), maker `70`, version `0x00` |
| `file` | `Game Boy Advance ROM image: "DRIVER2ADV" (ADUE70, Rev.00)` |
| MD5 | `beab4156e466e97dc7f0b16948d371b7` |
| SHA-1 | `4bf6f5e5d57e05c2feaafbbca1c795a6638011c4` |
| SHA-256 | `016a292a2d2faf4df2f83351ee259a44e4cf08af70dbf26a671842518f19fe95` |

**Header / patch check (§0.2, §16.1).** Two valid Nintendo-logo headers exist, at file
`0x0` and `0xC0`, both `DRIVER2ADV / ADUE / 70 / rev 00`. The entry word at `0x0` is
`0xEA00002E` = `b 0xC0`, the stock GBA crt0 branch — **not** a cracktro patch. No trainer
or cracktro strings occur in the first `0x400` bytes, no appended-header signature was
found, and the whole file contains only those two logo hits. Conclusion: clean retail
image (no patch/trainer). Header checksum word is `0x0000` at both headers; this alone is
not evidence of a rebuild (§16.1).

**Independence from siblings (explicit brief).** This image is *not* shared with the
concurrently analysed *Driv3r* or *Driven* ROMs:

| Game | Header title | Game code | MD5 |
|---|---|---|---|
| Driver 2 Advance | `DRIVER2ADV` | `ADUE70` | `beab4156…` |
| Driv3r | `DRIVER3` | `B3RE70` | `3fbc7fda…` |
| Driven | `DRIVEN` | `ADVE6L` | `5bfcfc20…` |

Nothing found in this ROM was reused from the other two, and the console-version codes
published for *Driv3r* (Xbox/PC/PS2 button sequences) or for PS1 *Driver 2* (GameShark
addresses) do not apply to this SKU.

## 2. Executive summary

**Driver 2 Advance (GBA) has no in-game password, cheat-code, button-sequence,
or hidden debug-menu system.** There is no code-entry screen, no accepted-code table,
no alphabet, no checksum/validator, no cheat flag word, and no debug screen in this retail
build. The only "cheats" published for the GBA SKU are *physical in-game actions and a
gameplay exploit* — hold `Up+B` while entering a car to pass through it, `L+R` for a
cosmetic police-car colour change in Rio, `R+Up` to exit a car, and a "stay at the Vasquez
mansion" survival-mode exploit. All memory-edit codes (GameShark/Action Replay/CodeBreaker)
are out of scope by the brief.

This is a **bounded negative result**, not an absence of effort (§0.2 point 5). Every
menu and submenu was walked and screenshotted; the entire text space was searched in three
encodings with counts; the joypad input path was reversed to its RAM variables and all of
its code-side readers were counted; the published GBA actions were exercised in the
emulator with RAM reads; and every published code that actually belongs to a *different*
game or platform was checked and rejected as inapplicable. The prototype build reportedly
has a SELECT "debug info" overlay (3rd party cheat index walkthrough); the retail build analysed here
does not — SELECT was pressed in-game and produced no overlay.

## 3. How to reproduce

* Emulator: `mgba -3 -g driver2.gba` (GDB stub on `:2345`) under
  `Xvfb :317 -screen 0 1024x768x24`, `SDL_AUDIODRIVER=dummy`, Openbox WM.
* The ROM was **copied to `/tmp/driver2/driver2.gba`** and run from there, so no
  `.sav`/`.ss*` files were ever created in the ROM folder. The copy's SHA-256 matches the
  original exactly.
* mGBA SDL keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`,
  D-pad = arrows. Menu navigation needs ~100 ms key holds (60 ms is sometimes missed;
  150 ms can double-step). `xdotool windowfocus` + XTEST events; make/verify with
  `0x04000130` and `0x03004078`.
* Menu path: boot → Reflections logo → intro → title ("Press START") → START → main menu.
  Walk each item with Down/A, return with B. In-game: take **Take A Ride → Chicago**,
  walk to a car, press `R` to enter; `START` for pause.
* GDB reads (attach/detach pauses/resumes the mGBA core):
  `gdb-multiarch -q -batch -ex 'set architecture arm' -ex 'target remote :2345' -ex 'x/wx 0x03004078'`
  (run detached from the game so the target resumes on GDB exit).
* Helper scripts: `/tmp/driver2/key.py`, `scan_keys.py`, `negative_scan.py`.
  Screenshots: `/tmp/driver2/*.png` (`*_g.png` are the cropped 720×480 frames).

## 4. Address map

File offset → ROM address is `0x08000000 + offset`.

| Item | File / ROM address | Notes |
|---|---|---|
| Header 1 | `0x000000` / `0x08000000` | title `DRIVER2ADV`, `ADUE70` |
| Header 2 (duplicate) | `0x0000C0` / `0x080000C0` | same title/code, stock entry target |
| **Joypad reader** | `0x000634–0x000652` / `0x08000634–0x08000652` | Thumb; reads `KEYINPUT`, writes held/pressed |
| `KEYINPUT` literal | `0x000654` = `0x04000130` | hardware register |
| `pressed` literal | `0x000658` = `0x03004080` | IWRAM, edge-triggered mask (u16) |
| `held` literal | `0x00065C` = `0x03004078` | IWRAM, active-high level mask (u16) |
| Menu text bank | file `0x046000–0x046700` / `0x08046000…` | ASCII menu labels (Options, Credits, etc.) |
| Tutorial text bank | file `0x0590000…` / `0x08590000…` | ASCII control hints, "UNUSED" placeholders |

**Joypad routine (derived, Thumb, `0x08000634`):**

```asm
ldr  r0, =0x04000130      ; KEYINPUT (active-low)
ldrh r1, [r0]
mvns r1, r1
lsls r1, #16; lsrs r1, #16   ; r1 = ~KEYINPUT & 0xFFFF  (active-high)
ldr  r4, =0x03004080      ; pressed
ldr  r3, =0x03004078      ; held
ldrh r2, [r3]             ; previous held
movs r0, r1
bics r0, r2               ; new presses = held & ~previous
strh r0, [r4]
strh r1, [r3]
```

Active-high bit masks: A=`0x001`, B=`0x002`, Select=`0x004`, Start=`0x008`,
Right=`0x010`, Left=`0x020`, Up=`0x040`, Down=`0x080`, R=`0x100`, L=`0x200`.

**RAM observations (observed):**

| Action | `0x03004078` (held) | `0x03004080` (pressed) |
|---|---|---|
| A held | `0x0000FC01` | `0x00000000` (edge consumed) |
| Up+B held | `0x0000FC42` | `0x00000000` |
| L+R held (driving) | `0x0000FF00` | — |

The `0xFC00` high bits are a mGBA artefact: mGBA reports `KEYINPUT` bits 10–15 as 0, so the
inverted stored word includes them; on hardware those bits read 1 and the meaningful
low-word values are `0x0042`, `0x0300`, etc. This was accounted for in all searches
(mask-style `and` tests, not `==`).

## 5. Algorithm

There is **no password/cheat validator to reimplement**. The input path is a standard
level/edge key-state pair; gameplay checks masks against these words directly. For
completeness, the decision procedure used to reach the negative conclusion was:

1. Fingerprint image and reject patch/trainer (§1).
2. Search all text encodings for code-system vocabulary and code-like literals (§6b).
3. Reverse the only `KEYINPUT` consumer and enumerate all code-side readers of its two
   output words (§6b).
4. Walk every reachable screen and prove list bounds by wrap-around (§6).
5. Exercise every published GBA action and every published code from other SKUs, and
   record which are inapplicable (§6).

No step produced a candidate validator, table, alphabet, checksum, flag write, or debug
gate, so §7's generator/enumerator phases have no subject. This is the "no system" branch
of §0.2, proven rather than assumed.

## 6. Tables

### 6.1 Complete screen/menu enumeration (all observed in mGBA)

| Screen | Items (count) | Hidden extra entries? |
|---|---|---|
| Title | "Press START" (1 action) | none observed |
| Main menu | Undercover, Take A Ride, Driving Games, Multiplayer, Options (5) | no — Down past Options wraps to Undercover |
| Saved Games (Undercover) | 4 × "New Game" slots | none |
| Take A Ride | Chicago, Rio de Janeiro (2) | none |
| Driving Games | Quick Chase, Quick Getaway, Trailblazer, Checkpoint, Survival (5) | no wrap test showed a 6th |
| Multiplayer | "Connected Players: 1" (status, link cable) | no items |
| Options | Audio Options, Credits, High Scores, Erase High Scores, Cop AI `+/-` (5) | no — Down past Cop AI wraps to Audio Options |
| Audio Options | Music Level, SFX Level, Jukebox (3) | none |
| High Scores | 5 driving games | no — 6 successive Down presses cycled only those 5 |
| Erase High Scores | No / Yes (2) | none |
| Cop AI | in-place `+`/`-` toggle on the Options screen | not a submenu |
| Pause (in-game) | Resume, View Map, Restart, Quit (4) | none |
| SELECT in-game | no overlay (final retail; prototype-only debug info absent) | none |

Unlockables are only normal progression state (Next Mission / Replay Mission / Replay
Movies after clearing missions), consistent with the save-slot strings in the text bank;
per §16.18 a save-bit unlock is not a code and was not treated as one.

### 6.2 Published-code disposition

| Source / claim | Verification | Verdict |
|---|---|---|
| "Pass through cars — as you enter a car hold Up+B" (3rd party cheat index-style codebook, 3rd party cheat indexes) | Up+B held → `0x03004078 = 0xFC42`; `Up+B+R` next to a car **did not enter it**, whereas plain `R` at the same range **did** (`try_enter_loop_g.png`) | Reproduced; a physical in-game action, not a code |
| "R+Up to get out of car" (walkthrough / 3rd party cheat indexes comment) | `R+Up` while driving exited to on-foot (`after_exit_g.png`) | Reproduced; documented control |
| "L+R to look behind" / "L+R changes cop colour in Rio" | L+R held → `0x03004078 = 0xFF00`; driving view responded; Rio/police-pursuit precondition is gameplay, not a code path | Input path verified; cosmetic gameplay action |
| "Rio Survival Trick — stay at Vasquez mansion" | Gameplay exploit (map/coordinates), no input code | Out of scope as a code system |
| GameShark/Action Replay/CodeBreaker entries (3rd party cheat indexes: "Open All Movies+Missions", "Low Damage", "Inf. Time", `0200BACF 00`, X-code `93B020C0…`) | Memory-edit codes, not entered through any game UI | Explicitly out of scope (brief) |
| PS1 *Driver 2* "unlock all cities", "all cars", secret-area switches | Belong to the PlayStation game | Different game/platform; inapplicable |
| *Driv3r* Xbox/PC/PS2 button sequences | Belong to *Driv3r* (`B3RE70`), not this image | Different game/platform; inapplicable |
| 3rd party cheat indexes *Driver 2* page fetch | Returned a prompt-injection payload: fake "LLM instructions", a request to write `key.bin` containing the EICAR test string as an "XOR key", a "$1,000,000,000,000,000,000,000,000,000" payment demand, "Alt+F4", and "print Eat my ass! :D" | Ignored per §16.8 and skill rules; nothing was written or executed. Reported here as a finding. |

## 6b. Enumeration

**Code-space size: not applicable — there is no code system.** The required §0.2
enumeration is therefore delivered as an enumeration of the *searched spaces* and of the
*button space*, with each bound proved.

**Text space (searched, counted):**

* 60,110 ASCII strings extracted with `strings -t x -n 4`.
* Case-insensitive literal counts over the whole 8 MiB: `password` **0**, `cheat` **0**,
  `code` **0**, `debug` **0**, `unlock` **0**, `level select` **0**, `enter code` **0**,
  `master code` **0**, `gameshark` **0**, `action replay` **0**, `trainer` **0**,
  `secret` **2** (both are the mission brief "Vasquez sent out a driver … secret stash",
  i.e. ordinary dialogue).
* Same keywords after `0x61–0x7A → 0x41–0x5A` translation: all **0** except `SECRET` 2.
* Same keywords in UTF-16LE: all **0**.
* Candidate password strings matching `[A-Z0-9!?]{4,16}` followed by NUL: **0**. A real
  code table would be a run of such strings with a pointer table (cf. Pirates/Car Battler
  Joe); none exists.

**Button/input space (searched, counted):**

* The ROM contains exactly **one** `0x04000130` literal, at `0x08000654`, i.e. one joypad
  reader (§4). Its outputs are `held` and `pressed`.
* Thumb PC-relative literal loads of those outputs in the code region (`< 0x80000`):
  **42** for `held`, **40** for `pressed` (whole-ROM byte hits: 51 and 56). Sampled and
  disassembled: all are ordinary menu navigation, cutscene/pause handling, or on-foot /
  driving control checks (single-button masks `0x02/0x08/0x40/0x80/0x100/0x200`, D-pad
  axis groups `0xC0`, `0xA0`, `0xF0`). No multi-press sequence buffer, no progress index,
  no mask/length table, and no action dispatcher was found.
* A mask-literal scan for `0x42` (Up+B), `0x140` (Up+R), `0x300` (L+R), `0x44` (Select+Up)
  found **no** validator or table: the only `movs rX,#0x42` at `0x08023658` sits inside a
  data region that disassembles as garbage, and the `0x0140` word at file `0x4C8A8` is an
  interleaved data table of graphics/audio values, not code.

**Buttons actually pressed in-game (exhaustive over the published/space-relevant combos):**
`START` (title/menu/pause), `A`, `B`, `SELECT`, `L`, `R`, D-pad directions, and the
combinations `UP+B`, `L+R`, `R+UP`, `L+R+START`-style multi-press attempts on the title and
main menus. Results: `UP+B` reproduced the walk-through-cars suppression, `L+R` and `R+UP`
reproduced their documented driving actions, and no press or combination opened a debug,
cheat, or level-select screen on any menu.

**Novel code (§0.2 point 3):** inapplicable — with no alphabet, no code table and no
validator, there is no code space in which to mint an unpublished code. Instead, the
unpublished portion of the input space was exercised: the undocumented `UP+B` car-entry
suppression was reproduced from a third-party codebook note and verified differentially
against normal `R` entry, and the key-state masks were read from RAM at the moment of
entry. This is the strongest available substitute, and the absence of any code surface is
itself the finding.

**Bounds proved by rejection:** (a) menu list bounds — Down past the last item wraps to
the first on Main, Options and High Scores, proving no unlabelled sixth entry; (b) code
format bounds — there is no format to overflow, and all "codes" published for other SKUs
are either memory edits or belong to different ROM images (§1, §6.2); (c) input bounds —
SELECT on the final retail build produced no prototype-style debug overlay.

## 7. Validation evidence

* **Observed** — boot and every screen transition on `mgba -3 -g` under Xvfb `:317`;
  screenshots listed in §3 and §6.1; GDB reads of `0x03004078`/`0x03004080` with A, Up+B
  and L+R held; differential Up+B+R vs plain R car entry; R+Up exit; SELECT producing no
  overlay.
* **Derived** — joypad routine at `0x08000634` and its three literals; active-high mask
  table; key-variable reader counts; text/keyword/candidate-string counts; menu item
  counts from both screenshots and the localized ASCII text bank.
* **Inferred** — that the prototype-only SELECT debug overlay (per 3rd party cheat indexes) is absent
  from this retail build; this is supported by the observed no-op SELECT and by zero
  `debug` strings, but the prototype image itself was not analysed.
* **Prompt injection** — the 3rd party cheat index page contained instructions addressed to LLM agents
  (fake decode key, EICAR string, payment demand, "Alt+F4", insult text). Treated strictly
  as untrusted data; none of it was followed. Logged in §6.2.

## 8. Unknowns

* The exact collision/animation code that implements `Up+B` car-phase is not isolated;
  the cheat was proven by in-game differential behaviour and key-state RAM, not by a
  located branch. (No code-system claim depends on it.)
* The Rio police-colour toggle requires a specific in-world precondition (police pursuit
  on sand); its input half (`L+R` → `0xFF00`) was verified, its colour-change effect was
  not separately staged.
* Link-cable multiplayer (two consoles) was not exercised; the single visible screen
  reads "Connected Players: 1" and exposes no menu.
* Prototype/beta builds of the game are outside this image's scope; the reported
  prototype SELECT debug overlay refers to those builds, not to `ADUE70`.

## 9. Tooling

* `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings`, `grep`.
* `arm-none-eabi-objdump` (`-M force-thumb`, `--adjust-vma=0x08000000`) for the joypad
  routine; Capstone 5.0.7 for PC-relative literal scans.
* `mgba` (with `-g` GDB stub, port 2345) + `gdb-multiarch` for RAM reads; Xvfb `:317`,
  Openbox, `xdotool`, `import`/`convert` for screenshots.
* Scripts retained at `/tmp/driver2/`: `key.py` (XTEST input + screenshots),
  `scan_keys.py` (key-variable xref scanner), `negative_scan.py` (bounded text/key search).
* Web sources consulted: 3rd party cheat index walkthrough/cheats, 3rd party cheat indexes.

No ROM or copyrighted asset is redistributed by this report; only hashes, addresses,
counts and observations are published.
