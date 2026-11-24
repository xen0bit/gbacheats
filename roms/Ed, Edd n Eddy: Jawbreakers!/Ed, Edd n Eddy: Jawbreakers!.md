# Ed, Edd n Eddy: Jawbreakers! (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Ed, Edd n Eddy: Jawbreakers!.gba` |
| Size | 4,194,304 bytes (0x400000) |
| Header title | `ED EDD EDDY` (0x080000A0) |
| Game code | `AE3E` (0x080000AC); `file` reports "AE3E6L, Rev.00" |
| Maker | `6L` (0x080000B0) |
| Version / complement / checksum | `0x00` / `0x15` / `0x0000` (0x080000BC–BF) |
| Fixed 0x96 | present at 0x080000B2 |
| MD5 | `7524d775a328156016649ab46ca62b3e` |
| SHA-1 | `39d7651f09e69a0fe15b9337bb2f3c20678b554a` |
| SHA-256 | `4a2cbac8908478fbe8dbd2f21252632afd0fd87e779b6322b905cb77cdaedc1f` |
| Developer / publisher | Climax Group / BAM! Entertainment (2003) |

**ROM is a scene-patched image, not a pristine retail dump.** The header has been
rebuilt (`checksum 0x0000`, complement `0x15`, which is not `~version`), and the
entry word is `0xEA0FB0FE` rather than the stock `0xEA00002E`: it branches to
`0x083EC400`, a custom boot stub. That stub runs a **EURASIA** cracktro
(observed on screen: "EURASIA", "Intro credits / JUNE_2006 OF SAC / CODE: KAFUGA /
LOGO: M7X / SEE YOU IN THE NEXT RELEASE!", then "EURASIA is proud to present on
march 08 of 2006 Ed Edd n Eddy supplied by TEAM EURASIA"). It jumps back into
the stock crt0 at `0x080000C0`; the game itself is intact. The cracktro is a
release splash, **not** an in-game cheat and not a trainer menu.

Embedded-header scan (156-byte Nintendo logo at each header+4): **exactly one**
hit, at file offset `0x0`. No multi-game pack, no appended second image.

## 2. Executive summary

This ROM has a real, developer-intended **button-code system**. Four 7-press
codes are entered on the "PRESS START" title screen; each toggles an effect and
makes a new **GAME CHEATS** entry appear on the main menu. All four published
codes were verified live in mGBA (not merely found as strings). GAME CHEATS is a
**level select** covering 48 named entries (SCENE 01 … CREDITS, including world
maps, bosses and all 24 playable levels).

Two findings go beyond the published lists:

1. **The published modifier is wrong.** 3rd party cheat indexes all say
   "hold L+R". The game only requires **L held**; R is optional. Holding R alone
   is rejected, and holding L+A or L+Select is accepted. Holding Start while
   entering is rejected because it leaves the title screen.
2. **The matcher is prefix-based, not exact-length.** Appending an extra press
   after a valid 7-press code is accepted; prepending one is rejected. The novel
   8-press code `L + Left,Left,Right,Down,Down,Up,Right,Right` is accepted by the
   game and appears in no published list.

No password/keypad cheat screen, no hidden debug menu, and no alphanumeric
password alphabet were found. The "GAME CHEATS" surface is the whole in-game
cheat system. No GameShark/CodeBreaker codes were used or reported.

**Relation to `Ed, Edd n Eddy: The Mis-Edventures` (queue 280): nothing is
shared.** Different developer (Artificial Mind & Movement vs Climax), different
publisher (Midway vs BAM!), different engine (3D vs 2D), and a different cheat
design (jawbreaker-completion unlocks of Stealth/Damage/Fast Run vs these
title-screen button codes). Several cheat aggregators (3rd party cheat indexes)
misattribute these Jawbreakers button codes to "Mis-Edventures"; that is a
transcription error in those sites, not shared code.

## 3. How to reproduce

**Emulator**: mGBA (SDL, `/usr/local/bin/mgba`) under `Xvfb :318`,
`SDL_AUDIODRIVER=dummy`, `mgba -3 <rom>`. Keymap (mGBA SDL default):
A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows.
Hold each key ~80–100 ms, with ~120 ms between presses.

**Fresh boot from an empty save requires seven Start presses** (2.3 s apart) to
pass the splash chain: EURASIA cracktro → BAM! legal → Cartoon Network
Interactive → Warner Bros. → two black transitions → CLIMAX → title
("PRESS START"). With an existing `.sav` the chain is shorter.

**Code entry**: on the title screen, hold L (or L+R) and press the seven
directions of a code below, one at a time. Success is signalled by the show's
"gibberish" sound (silent under `SDL_AUDIODRIVER=dummy`); the reliable visual
proof is the main menu: press Start once (enters gameplay), then Start again
(quits to main menu). The menu now has **START GAME / OPTIONS / GAME CHEATS**.

**Published codes verified (all accepted):**

| Effect (published name) | Press sequence with L held |
|---|---|
| All Items / Unlimited Items | Left, Left, Down, Right, Right, Up, Left |
| Invincibility / All Protect | Left, Down, Down, Right, Right, Left, Down |
| Jet Packs | Left, Up, Right, Down, Left, Left, Up |
| Level Select | Left, Left, Right, Down, Down, Up, Right |

**Novel code (generated here, in no published list):**

| Code | Result |
|---|---|
| L + Left, Left, Right, Down, Down, Up, Right, **Right** | Accepted; GAME CHEATS appears; level select works |

**Level select proof**: enter Level Select, main menu → GAME CHEATS, press
Right to cycle (`SCENE 01` → `WORLD MAP 01` → `L01 STREET` → … → `CREDITS`),
press A to launch. A run cycled to `SCENE 05` and A started a different level
(objective banner "Return Nazz's…"), proving the selector changes the loaded
level, not just a label.

**Menus walked**: title; main menu (2 entries before any code, 3 after);
OPTIONS (`MUSIC ON`, `SFX ON`, `SKILL NORMAL/HARD` — three entries, no hidden
debug row); GAME CHEATS / level select (one field `LEVEL` with ~48 values,
Left/Right cycles, Up/Down inert); gameplay; quit-to-menu / pause via Start.
No other screen was reachable.

## 4. Address map

All addresses are `0x08000000 + file offset`.

| Address | Meaning | Evidence |
|---|---|---|
| `0x08000000` | GBA header; entry word `0xEA0FB0FE` → `0x083EC400` | Observed (bytes) |
| `0x080000C0` | Stock ARM crt0 (restored to by cracktro) | Derived (disassembly) |
| `0x083EC400` | EURASIA cracktro boot stub; literal pool `"nano"/"main"/"rept"` at `0x083EC498`+ | Derived (ARM disassembly) |
| `0x080004B8` | Key-input helper: reads `0x04000130`, builds active-high mask `~KEYINPUT & 0x3FF`, writes ring buffers at `0x020015A8`/`0x020015B0`, index `0x02001A34` | Derived (Thumb disassembly) |
| `0x083D75D4` | Main-menu string-pointer table: base of five language sub-tables; English sub-table at `0x083D75D4` = {`0x083D7518` START GAME, `0x083D755C` OPTIONS, `0x083D758C` GAME CHEATS} | Derived (u32 table dump) |
| `0x083D7610` | Same table's language-index array (referenced as a literal from Thumb code at `0x08005B20` / `0x08005C5C`) | Derived |
| `0x083CE3A8` | English level-name pointer group header (`0x083CDC80` = "LEVEL"), followed by 48 level/scene/boss/credits names | Derived |
| `0x083CE52C`–`0x083CE534` | Cheat-effect name pointers: `0x083CE2E8` "ALL JETPACKS", `0x083CE32C` "ALL PICKUPS", `0x083CE368` "ALL PROTECT" (each with French/Italian/German/Spanish variants immediately after) | Derived |
| `0x083CDC40`–`0x083CDC70` | 32-symbol table `!#%'),.02479;=?BDFHJMOQSVY[]_acdd` — font/glyph conversion table, **not** a password alphabet (no input field uses it) | Derived |
| `0x0203E370` | "Smsh"/"Tmsh" save block in EWRAM; bytes here vary with the title-screen demo (tokens/timer), so they are **not** the cheat flag | Observed (savestate diff) |
| — | **No contiguous code table found.** Exhaustive literal searches for the four sequences as u8/u16 (LE/BE), active-high/active-low, L-only/L+R, forward/reversed, 2/3/4-bit packed, and fuzzy per-press masks returned zero hits. The validator is therefore inline compares / a state machine, not a ROM lookup table. | Derived (negative search) |

## 5. Algorithm

Behavioural model of the validator (reconstructed from in-game accept/reject
experiments; the exact routine was not isolated in the disassembly):

```
state = 0                       # progress index
on each newly-pressed d-pad direction d while on title screen:
    if held(L) is false: state = 0; continue        # L is mandatory
    if any other non-Shoulder key is held: state = 0; continue
    if d == EXPECTED[state]:                        # per-code state machine
        state += 1
        if state == 7:
            activate(effect for that code)
            state = 0                              # matcher stays armed
    else:
        state = 0                                  # or resync to a shorter prefix
```

Properties proved by experiment:

* **Alphabet**: d-pad only — {Left, Right, Up, Down}; 7 presses.
* **Modifier**: L must be held. R is ignored (optional). A and Select are
  ignored. Start breaks entry because it changes screen.
* **Length / matching**: the first seven presses decide; an 8th and 9th press
  are ignored. A 6-press prefix is rejected. An extra press *before* the code
  is rejected. This is prefix matching with a reset on mismatch.
* **Effects**: four independent toggles; multiple codes can be entered in one
  title session (all four were entered together successfully).

Note §16.12/§16.2 caution: the title screen also runs a playable demo, so
savestate RAM diffs of the save block are dominated by token/timer churn;
that is why the flag was located behaviourally rather than from a stable RAM
byte.

## 6. Tables

**6.1 Button codes** (all verified in emulator; effect names as published):

| # | Effect | L held + presses |
|---|---|---|
| 1 | All Items | L L D R R U L |
| 2 | Invincibility | L D D R R L D |
| 3 | Jet Packs | L U R D L L U |
| 4 | Level Select | L L R D D U R |

**6.2 Level-select values** (48, from the pointer table at `0x083CE3A8`):
SCENE 01, WORLD MAP 01, L01–L04 STREET, SCENE 02, WORLD MAP 02, L05–L08
PLAYGROUND, SCENE 03, BOSS 01, SCENE 04, WORLD MAP 03, L09–L12 WOODS, SCENE 05,
BOSS 02, SCENE 06, WORLD MAP 04, SCENE 07, L13–L16 CONSTRUCTION, SCENE 08,
BOSS 03, SCENE 09, WORLD MAP 05, L17–L20 JUNKYARD, SCENE 10, BOSS 04, SCENE 11,
WORLD MAP 06, L21–L24 TRAILER, BOSS 05, SCENE 12, CREDITS.

**6.3 Options** (main menu → OPTIONS): MUSIC ON/OFF, SFX ON/OFF,
SKILL NORMAL/HARD.

## 6b. Enumeration

**Space definition.** The intended input space is 7-tuples over a 4-symbol
alphabet (d-pad directions) with a required L modifier: `4^7 = 16,384`
distinct 7-press sequences. Under suffix tolerance the effective space is
`sum(4^k for k=7..∞)` (unbounded length), but only the first seven presses are
semantically significant. There is no checksum, no alphabet table, and no
reserved bits. The game exposes exactly four effects (three named cheat
toggles in ROM plus level select).

**Complete accepted set (published, all verified in this image):** the four
sequences in §6.1. Four independent sources (3rd party cheat index wiki, 3rd party cheat indexes) agree on exactly these four; the ROM contains exactly three
cheat-effect name strings plus the level-select field, consistent with four.

**Novel code generated and accepted in-game (not on any published list):**

```
L + Left, Left, Right, Down, Down, Up, Right, Right
```

This is the Level Select code with one extra `Right` appended. It was entered
on a real title screen in mGBA; the main menu grew from two to three entries
(`START GAME / OPTIONS / GAME CHEATS`), and GAME CHEATS launched a selected
level. Evidence: `walk_menu_novel.png`, `lv_select.png`, `lv_started.png` in
`/tmp/eennejaw/` (screenshots retained locally; no assets published).
A second novel variant, the same code with two extra presses
(`…, Right, Right`), was also accepted.

**Bounds proven by in-game rejection** (each from a clean boot/title state):

| Test | Result |
|---|---|
| Published Level Select code with last press changed Up | Rejected (menu stayed at 2 entries) |
| Published code with the 4th press changed | Rejected |
| Correct 7 presses, **no** modifier held | Rejected |
| Correct 7 presses, **R only** held | Rejected |
| Correct 7 presses, 6-press prefix only | Rejected |
| Correct 7 presses with an extra press inserted in the middle | Rejected |
| Correct 7 presses with an extra press **prepended** | Rejected |
| L+A or L+Select held with the correct presses | Accepted (other keys ignored) |
| L+R+Start held | Rejected (Start leaves the title screen) |

**Negative results bounded.** Searched the whole 4 MiB image for: ASCII
`password|cheat|code|debug|secret|unlock|level` hits (classified: UI/menu text,
localised cheat names and level names, plus one font glyph table — no password
prompt); contiguous encodings of all four sequences in u8, u16 LE/BE, active
active-high/active-low, L-only/L+R, forward/reversed, and 2/3/4-bit packed form;
and literal `0x04000130` key-register references (3 hits, all in the input
helper / crt0). No password screen, keypad alphabet, or debug menu exists.

## 7. Validation evidence

* **Observed** — mGBA screenshots and menu state: cracktro splash chain;
  main menu 2→3 entries after each code; GAME CHEATS field cycling
  `SCENE 01`→`WORLD MAP 01`→…→`SCENE 05`; a different level starting with an
  objective banner; OPTIONS entries MUSIC/SFX/SKILL with NORMAL→HARD.
* **Observed** — every accept/reject row in §6b, each from a fresh boot with
  the `.sav` deleted, so no cheat state leaked between tests.
* **Derived** — ROM header/cracktro addresses and disassembly; string/pointer
  tables; the fact that no contiguous code literal exists anywhere in the
  4 MiB image.
* **Inferred** — the state-machine pseudocode in §5 (the exact validator
  routine was not isolated; the model is the minimal one consistent with all
  observed accept/reject behaviour). The significance of the 32-symbol table
  at `0x083CDC40` is inferred to be font/glyph mapping, not a password
  alphabet — it has no input consumer.

## 8. Unknowns

* The exact validator routine address and its per-code expected-value table
  were not isolated. Static literal searches and an immediate-compare scan
  over the low 128 KiB found only unrelated camera/level code; the sequences
  are evidently compiled into inline compares. The behavioural model in §5 is
  therefore inferred, not decompiled.
* Whether a 9th-or-later press can ever re-arm a different code (the matcher
  stays armed after success; only prefix behaviour was tested).
* The precise meaning of the volatile bytes at EWRAM `0x0203E370`–`0x0203E37B`
  (title-demo token/timer state) was not pinned down; they are not the cheat
  flag.
* Whether the three named cheat toggles (ALL JETPACKS/PICKUPS/PROTECT) appear
  as on-screen rows under some other condition — the GAME CHEATS screen showed
  only the LEVEL field in every test, including with all four codes active.

## 9. Tooling

* `file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings -t x`, `grep -iE`.
* Python 3 + `capstone` 5.0.7 for Thumb/ARM disassembly and literal/BL scans;
  `arm-none-eabi-objdump -M force-thumb/-M force-arm` for spot checks.
* Python helpers in `/tmp/eennejaw/`: `key.py` (XTEST key driver),
  `enumerate2.py` (fresh-boot accept/reject harness), `menu_check.py`
  (red-text row-group detector for GAME CHEATS presence), `ssdiff.py`
  (mGBA `gbAs` savestate extractor/diff), `oracle.py`, `menu_walk.py`,
  `level_verify.py`, `options_walk.py`.
* mGBA SDL under `Xvfb :318` + `openbox`; `import -window root` for screenshots.
* Web sources consulted (treated as data, no instructions followed): 3rd party cheat indexes
  cheats, 3rd party cheat index wiki, 3rd party cheat indexes
  FAQ 23710, 3rd party cheat indexes. No prompt-injection payload was encountered in
  the fetched pages.

No ROM content or copyrighted assets are redistributed in this report; only
hashes, addresses, algorithms and the author's own generated code are documented.
