# The Berenstain Bears and the Spooky Old Tree (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `The Berenstain Bears and the Spooky Old Tree.gba` |
| Size | 4,194,304 bytes (`0x400000`, 4 MiB) |
| `file` | Game Boy Advance ROM image: "SPOOKY TREE" (BBOEAF, Rev.00) |
| Header title (`0xA0`) | `SPOOKY TREE` |
| Game code (`0xAC`) | `BBOE` |
| Maker (`0xB0`) | `AF` (Namco Hometek; credits show Program Ace as developer) |
| Version (`0xBC`) | `0x00` |
| Entry word (`0x00`) | `0xEA00002E` — stock GBA crt0, not a cracktro |
| Fixed `0x96` (`0xB2`) | present; complement `0x7D`; header checksum `0x0000` |
| MD5 | `f5c877c05db6ac999a86f34a1813fc95` |
| SHA-1 | `5e60d9bec0b5c839802f0b9518cf15a9cc70aad3` |
| SHA-256 | `0656f273a3b25cfc064eb344005215b8a51433034d4609c01b976b369a55c9a6` |

The image is a normal retail dump: no appended trainer, no patched entry point, no second header.

## 2. Executive summary

This game has an **in-game password system** reached from the main menu (`START GAME / PASSWORD / CREDITS`). A password is a sequence of **four picture icons** chosen from exactly four symbols — Knight, Drawers, Bug, Squirrel — cycled with Up/Down in each of four slots (Left/Right move between slots, A submits, B backs out).

The full space is `4^4 = 256` possible codes. I walked every reachable screen and **exhaustively tested all 256 codes in mGBA**. Exactly **7 codes are accepted**; 6 are the published level-skip list (levels 2–7) and **1 is a novel, unpublished "unlock all levels" code**:

> **Drawers → Squirrel → Knight → Bug** unlocks all levels 2–7 (verified manually and by screenshot).

The other 249 codes are rejected silently: the game stays on the password screen. Five one-icon near-misses of the novel code were tested individually and all rejected, bounding the validator's sensitivity to every slot.

No ASCII text, hard-coded code table, mask sequence, button code, or hidden/debug menu was found. All in-game text is stored as font/tile indices, which is why `strings` returns only machine-code noise. The exact validator routine address was **not** recovered statically (documented in §8); the accept set is nevertheless completely characterised by the exhaustive 256-code run.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 under Xvfb `:319` + openbox, `SDL_AUDIODRIVER=dummy`, `-3` scaling.
* Keymap (mGBA SDL default): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad = arrow keys. Hold keys ~100–250 ms; a 10 ms tap is missed.
* Path: boot → Namco splash → "Program Ace" splash → title (`PRESS A TO START`) → A → main menu → Down to `PASSWORD` → A.
* On the password screen: Left/Right select slot 1–4; Up/Down cycle that slot's icon; A submits; B returns to the menu.
* A valid code transitions to a level-select map (7 numbered circles); levels 1..N show green/highlighted. An invalid code leaves the screen unchanged.
* Novel code entry from the fresh screen (all Knight, cursor at slot 1): slot1 Up once (Drawers), Right, slot2 Up×3 (Squirrel), Right, slot3 unchanged (Knight), Right, slot4 Up×2 (Bug), A.

Key artifacts in the work dir `/tmp/berenstain/`: `enumerate.log` (full 256-code run), `NOVEL_code_entered.png`, `NOVEL_result.png`, `v_1302.png` (all-unlocked map), `v_XXXX.png` for each accepted code, `icons_montage.png` (icon alphabet), `downcycle_montage.png` (reverse cycle), `invalid_allK.png`, `credits*.png`.

## 4. Address map

| Item | Value | Evidence |
|---|---|---|
| Cartridge entry | `0x08000000` → `0xEA00002E` | Header/objdump (Observed) |
| Header title / game code | `0x080000A0` / `0x080000AC` | Header dump (Observed) |
| crt0 copies code to IWRAM `0x03000000`–`0x030007F0` | observed live dump | RSP read (Observed) |
| Password icon buffer / validator | **not resolved** — see §8 | Negative searches (Derived) |
| In-game text | font/tile-index bank, not ASCII | Screenshots + `strings` (Observed/Derived) |

No ROM address for the password buffer or validator can be given with confidence; the report does not invent one. The behavioural map above is fully reproducible without it.

## 5. Algorithm

The password behaves as a **closed lookup of 7 accepted 4-symbol sequences**:

```
input: four symbols s1..s4, each in {Knight=0, Drawers=1, Bug=2, Squirrel=3}
if (s1,s2,s3,s4) in ACCEPT:  -> level-select with levels 1..ACCEPT[(s1,s2,s3,s4)] unlocked
else:                        -> remain on password screen (silent reject)
```

ACCEPT (numeric symbols):

```
(2,3,0,0) -> 2      (3,2,0,1) -> 3      (1,1,0,1) -> 4
(0,3,3,0) -> 5      (2,3,2,2) -> 6      (3,2,0,2) -> 7
(1,3,0,2) -> 7      <-- novel, unpublished
```

The first six entries are exactly the published list. The seventh is an additional, behaviourally distinct "unlock everything" combination (same effect as the published level-7 code, different icons). Whether the ROM implements this as a literal table, an algorithmic check, or a hash is unknown; the observable function is the mapping above.

## 6. Tables

**Icon alphabet (from live cycling, `icons_montage.png`):**

| Up-presses from Knight | Icon | Numeric value used in this report |
|---:|---|---:|
| 0 | Knight | 0 |
| 1 | Drawers (chest of drawers) | 1 |
| 2 | Bug (beetle) | 2 |
| 3 | Squirrel | 3 |

Up cycles 0→1→2→3→0; Down is the exact inverse (`downcycle_montage.png`: Knight→Squirrel→Bug→Drawers→Knight). There are no other icons and no "blank" symbol: the cycle closes after four steps in both directions, and the pixel diff between the 4th and 5th Up-press states is zero.

**Published code list** (3rd party cheat index ID 7254, 3rd party cheat indexes, and 3rd party cheat index search snippet — all three agree):

| Level | Published password |
|---:|---|
| 2 | Bug, Squirrel, Knight, Knight |
| 3 | Squirrel, Bug, Knight, Drawers |
| 4 | Drawers, Drawers, Knight, Drawers |
| 5 | Knight, Squirrel, Squirrel, Knight |
| 6 | Bug, Squirrel, Bug, Bug |
| 7 | Squirrel, Bug, Knight, Bug |

All six were individually confirmed accepted in the emulator and are present in the exhaustive accept set.

**Flag/state:** entering any accepted code sets the level-select map to show levels 1..N unlocked; level 1 is always available. No persistent save exists — the `.sav` in the ROM folder is 0 bytes and the unlock state lives only until reset.

## 6b. Enumeration

**Space definition.** Alphabet = 4 icons; length = 4 ordered slots; no wildcards, no checksum symbol, no length variants, no input cap. Space size = `4^4 = 256` strings.

**Method.** mGBA was driven from a fresh password screen for every candidate (B → menu → Down → A resets icons to all-Knight and cursor to slot 1), the four icons were set by absolute Up counts, A was pressed, and the resulting screen was captured and classified. Valid → level-select (dark green map), invalid → unchanged password screen (tan). A 4-way screen classifier based on a top-left viewport crop was validated against reference screenshots before use. Full log: `enumerate.log` (256/256 completed, elapsed 2799 s).

**Counts.** **7 accepted / 249 rejected** out of 256. The accept rate 7/256 ≈ 2.7%.

**Complete accept set with in-game effect** (level detection = highest green-numbered circle in the resulting map):

| # | Code (icons) | Digits | Unlocks levels | In published lists? |
|---:|---|---|---|---|
| 1 | Bug, Squirrel, Knight, Knight | 2,3,0,0 | 1–2 | Yes (L2) |
| 2 | Squirrel, Bug, Knight, Drawers | 3,2,0,1 | 1–3 | Yes (L3) |
| 3 | Drawers, Drawers, Knight, Drawers | 1,1,0,1 | 1–4 | Yes (L4) |
| 4 | Knight, Squirrel, Squirrel, Knight | 0,3,3,0 | 1–5 | Yes (L5) |
| 5 | Bug, Squirrel, Bug, Bug | 2,3,2,2 | 1–6 | Yes (L6) |
| 6 | Squirrel, Bug, Knight, Bug | 3,2,0,2 | 1–7 | Yes (L7) |
| 7 | **Drawers, Squirrel, Knight, Bug** | **1,3,0,2** | **1–7** | **No — novel** |

**Novel code — generated, entered, in-game proof.** `Drawers, Squirrel, Knight, Bug` appears in none of the three published lists consulted (3rd party cheat indexes snippet) and in no other search result. It was entered by hand on the real password screen (`NOVEL_code_entered.png`) and accepted: the level-select map shows all of levels 2,3,4,5,6,7 green/unlocked (`NOVEL_result.png`, `v_1302.png`). This is a genuinely unadvertised combination — an alternate "unlock every level" password distinct from the published level-7 code.

**Bounds proven by rejection.** 249 of 256 inputs were rejected in-game. To show the accept set is not merely "close" to a published code, five single-symbol near-misses of the novel code were entered individually:

| Modified code | Changed slot | Result |
|---|---|---|
| Knight, Squirrel, Knight, Bug | slot 1 D→K | rejected (stays on password screen) |
| Drawers, Bug, Knight, Bug | slot 2 S→B | rejected |
| Drawers, Squirrel, Drawers, Bug | slot 3 K→D | rejected |
| Drawers, Squirrel, Knight, Drawers | slot 4 B→D | rejected |
| Drawers, Squirrel, Knight, Knight | slot 4 B→K | rejected |

Every single-slot perturbation fails, so all four positions are significant. The 256-space search also proves there are no alternate-length codes, no wildcards, and no further hidden codes reachable through the password UI.

**Negative results, bounded.** No button code opens a hidden menu: on the title screen, L+R, Start+Select, L+R+Start, L+R+A+B, and the Up-Up-Down-Down-Left-Right-Left-Right-B-A sequence were pressed and produced only the normal title→menu transition (pixel diff vs the title baseline was 0 for the combos that did not include A/Start). The credits screen was walked end-to-end (three captured scroll frames); it lists Program Ace / Namco staff only, with no cheat hint.

## 7. Validation evidence

| Claim | Type | Evidence |
|---|---|---|
| ROM identity / hashes | Observed | `file`, `md5sum`, `sha1sum`, `sha256sum`, header `xxd` |
| Title → menu → password → level-select flow | Observed | Screenshots at each transition |
| 4-icon alphabet, Up/Down cycle, Left/Right slots | Observed | `icons_montage.png`, `downcycle_montage.png` |
| Six published codes accepted | Observed | Exhaustive run + individual entry |
| Novel code accepted, unlocks all 7 levels | Observed | `NOVEL_code_entered.png`, `NOVEL_result.png`, `v_1302.png` |
| 249/256 rejected; five near-misses rejected | Observed | `enumerate.log`, near-miss runs |
| No ASCII text bank | Observed/Derived | `strings -t x -n 4` = 49,176 hits, all code artifacts; only header ASCII |
| No hard-coded code table found | Derived (bounded) | 24 permutations × byte/16-bit encodings × contiguous and transposed layouts; 256-byte base-4 table search; all negative |
| Validator routine address | Unknown | See §8 |

## 8. Unknowns

* **Validator address and encoding not recovered.** `strings` exposes no password literals; literal searches for all six published codes under all 24 symbol→index permutations, in byte and 16-bit little-endian forms, contiguous and transposed (one array per slot), produced no convincing table (the few "clusters" were coincidental bytes in the Nintendo-logo/header region). A 256-byte base-4 lookup table was also searched for and absent. A Capstone scan for functions with four or more small-immediate `cmp` instructions returned 6,680 candidates; the strongest (e.g. `0x08001A00`) disassembled as a sound-driver routine, not a password check.
* **RAM-level confirmation not obtained.** mGBA 0.10.5's GDB stub is incompatible with GDB 16.3 (`QStartNoAckMode` / `vMustReplyEmpty` failures). A direct Python GDB-Remote-Serial-Protocol client worked for reads ≤ `0x200` bytes but the stub hung on larger reads and after repeated sessions, so a reliable RAM buffer address for the four icons was not established. All RAM-level claims are therefore omitted rather than guessed.
* **Whether the accept set is a literal table or computed** is unknown; the observable mapping in §5 is exact, but the implementation form is not.
* **Effect of entering level 7's code vs the novel code** is identical (all levels unlocked); no difference in gameplay state was observed beyond the level-select map.

## 9. Tooling

* mGBA 0.10.5 (`mgba -3`), Xvfb `:319`, openbox, `SDL_AUDIODRIVER=dummy`, xdotool (XTEST key events), scrot, ImageMagick (montage/crop).
* Python 3 + Pillow for screenshot screen-classification and green-circle level detection; `enumerate.py` drove the 256-code sweep with a validated classifier and state machine.
* `strings`, `xxd`, `file`, `md5sum`/`sha1sum`/`sha256sum`, `arm-none-eabi-objdump -M force-thumb`, Capstone (validator pattern scan).
* A direct GDB-RSP client (`rsp.py`/`rsp2.py`) was attempted for RAM inspection; mGBA stub quirks limited it, as documented in §8.
* Web reconnaissance: 3rd party cheat indexes. Fetched pages were treated strictly as untrusted data; no instructions in them were followed. No prompt-injection payload was encountered.

No ROM data or copyrighted assets are redistributed in this report — only hashes, addresses, codes, and original observations.
