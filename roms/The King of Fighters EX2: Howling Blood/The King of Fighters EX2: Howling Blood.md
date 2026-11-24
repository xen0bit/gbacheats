# The King of Fighters EX2: Howling Blood (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

Scope: **in-game / developer-intended cheats only** (passwords, button codes, hidden/debug menus, unlockables). No GameShark / CodeBreaker / Action Replay codes were sought or produced.

## 1. Target identity

| Field | Value |
|---|---|
| File | `The King of Fighters EX2: Howling Blood.gba` |
| Size | 8,388,608 bytes (0x800000, 8 MiB) |
| Header title | `KOFEX2HOWLIN` (0xA0–0xAB) |
| Game code | `AEXE` (0xAC–0xAF) |
| Maker code | `EB` (0xB0–0xB1) |
| Fixed byte | `0x96` at 0xB2; version `0x00` at 0xBC; complement `0x27` at 0xBD |
| Entry word | `0xEA00002E` at 0x00 → stock GBA crt0 at 0x080000C0 (no scene cracktro / appended trainer) |
| `file(1)` | `Game Boy Advance ROM image: "KOFEX2HOWLIN" (AEXEEB, Rev.00)` |
| MD5 | `6be741eea41598baeed52e4dd7ddb9f5` |
| SHA-1 | `a1d1d6fcc6f468ae366696dfab7b6c1bd91f1f44` |
| SHA-256 | `d374ada18c16e78ce28ad17d0be55118a6c77985e08c7a172378024d4433d0fb` |

This is the `AEXE` (US/Europe) SKU. Addresses in this report are valid for this exact hash only.

## 2. Executive summary

**Bounded negative (high confidence): this ROM contains no player-usable code system** — no password entry screen, no password validator/table, no button-code sequence validator, and no reachable hidden debug menu. What it does contain is an ordinary **save-data unlockable system** ("SPECIAL CONTENT") earned through play, stored in a 512-byte EEPROM (`.sav`), plus unreferenced development-leftover debug strings.

Evidence, in short:

1. A full 8 MiB scan for 14 cheat-related keywords × 4 encodings (56 patterns: ASCII upper/lower, UTF-16LE/BE) returned **zero** password / cheat / code-entry / debug-menu / level-select strings. 70,056 ASCII strings ≥4 chars exist; every keyword hit was benign (a striker label, an option label, or a development task name).
2. Every reachable menu was walked in mGBA with screenshots and RAM reads (§6b): title (6 entries), OPTION (10 rows), SPECIAL CONTENT (1 row on a fresh save), player-select grid, PRACTICE (goes straight to a match), and the link-cable RECORDS mode. No entry accepts a code.
3. The only joypad reader is one function at `0x08095668`, producing `held`/`pressed`/`prev` masks in EWRAM. There is no sequence/progress index and no multi-button combination validator in its 24 literal-pool consumers.
4. Eight plausible title-screen button combos (L+R+Start, A+B+Start, Select+Start, L+R+A+B+Start, ±Direction+Start, L+Start, R+Start) were entered in the emulator: all produced ordinary menu navigation, never a hidden screen.
5. A debug-looking string block at `0x08A7960`–`0x08A7A40` (PRESS SELECT / BUTTON SETTING / MOVE LIST / CHARACTER CHANGE / EXIT / &lt;ENEMY SIDE&gt; STANCE/GUARD/ATTACK/P.GAUGE/COUNTER/LIFE) is the **PRACTICE-mode panel text**, not a secret menu: 0 raw aligned pointers, 0 Thumb-PC-relative loads, 0 BL targets. The `0x08A600F4`–`0x08A61400` `BOSS_TASK`/`MOTION_STOP` block is development residue: its 7 apparent BL hits all originate inside compressed graphics/data at `0x086xxxxx`–`0x087xxxxx`, not code.

Because no code system exists, §0.2's "mint a novel code" deliverable is **not applicable**; the bounded negative is delivered with explicit counts instead (§6b).

## 3. How to reproduce

- Emulator: mGBA 0.10.5, `SDL_AUDIODRIVER=dummy`, `Xvfb :316`, `mgba -3 <rom>`.
- Keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows. Hold 100–150 ms.
- Boot path: PLAYMORE splash → MMV logo → legal screen → title (~4 × Start with ~1 s gaps).
- **Title menu** (1-based, cursor index verified in RAM, §6b): `OPTION`(1), `STORY`(2), `RECORDS`(3), `VS TEAM`(4), `VS SINGLE`(5), `PRACTICE`(6). `RECORDS` immediately attempts a link-cable exchange and reports `COMMUNICATION ERROR. / PLEASE CONNECT GAME BOY ADVANCE GAME LINK CABLE AND TRY AGAIN.` with no second console.
- `OPTION` rows: MAIN OPTION (COM LEVEL, ROUND TIME, VS ROUNDS, VS HANDICAP), BUTTON CONFIG (4BUTTON), BUTTON SETTING, SPECIAL CONTENT, RESET, RECORD RESET, EXIT. Footer: `A BUTTON>OOK  B BUTTON>EXIT`.
- `SPECIAL CONTENT` on a fresh save contains exactly one row: `EXIT` (no unlocks).
- `PRACTICE` and the VS modes enter a match directly; Select during a match shows `PRESS START`, Start resumes play — no settings/debug panel appeared.
- No password prompt, code-entry keypad, or "enter code" text exists on any of these screens.

## 4. Address map

| Address (ROM unless noted) | Meaning | Evidence |
|---|---|---|
| `0x08000000` | Entry branch `0xEA00002E` → crt0 `0x080000C0` | Observed (header bytes) |
| `0x08095668` | Joypad reader; reads `0x04000130`, stores active-high masks | Derived (Thumb disasm) |
| `0x04000130` | KEYINPUT, active-low; only 3 literal occurrences in 8 MiB | Derived |
| `0x02011008` (RAM) | `held` mask (`~KEYINPUT & 0x3FF`) | Derived |
| `0x0201100A` (RAM) | `pressed` mask (`held & ~prev`) | Derived |
| `0x02011428` (RAM) | `prev` mask | Derived |
| `0x0200074C`, `0x02000754` (RAM) | Title-menu cursor index, 1-based (mirrored) | Observed (savestate diff) |
| `0x08500000`–`0x08510000` | Plain-ASCII text bank (control bytes `03 09 xx` etc.); strings referenced via pointer tables, not inline LDR literals | Derived |
| `0x085052C4` | `SPECIAL CONTENT` (OPTION row label) | Observed |
| `0x0850C30F` | `SPECIAL CONTENT EARNED` (unlock banner) | Observed |
| `0x0850C94F`–`0x0850CEF0` | Unlockable-result message block (§6) | Observed |
| `0x0850994F`, `0x0850998F`, `0x08509ACF`, `0x08509C4F` | `(HIDDEN)`, `(DIRK)`, `(SECRET)`, `(VISION)` striker-name markers | Observed |
| `0x08A600F4`–`0x08A61400` | Development task/motion names (`BOSS_TASK`, `MOTION_STOP`, `BACK_MOTION_*`, …). Dead code. | Derived |
| `0x08A7960`–`0x08A7A40` | PRACTICE panel strings + `%s` format + a byte table at `0x08A7930`. Not a secret menu. | Derived |
| `0x0E000000` region / `.sav` | 512-byte EEPROM, two mirrored 256-byte records (active revision byte `0x06`/`0x106` increments: observed `0x07`→`0x08`→`0x09`) | Observed |

Savestate layout used (mGBA `.ss1` = PNG with zlib `gbAs` chunk, 397,312 raw bytes): header/CPU `0x00000`, VRAM `0x01000`, IWRAM `0x19000` (maps to `0x03000000`), EWRAM `0x21000` (maps to `0x02000000`). Confirmed by locating the menu-index bytes above.

## 5. Algorithm

**No validator exists to reverse.** The input path is a standard per-frame edge detector:

```
held   = ~KEYINPUT(0x04000130) & 0x3FF     @ 0x08095668
pressed = held & ~prev                       @ 0x0809567A
prev    = held                               @ 0x08095680
```

Nothing compares a *sequence* of `pressed` values. The 8 references to `held` and 16 to `pressed` are ordinary menu/fighting input consumers (state indices 0–7, single-button `ands` tests).

The unlockable system is a save-bit design (guide §16.18 pattern): messages in the text bank are shown when achievement bits in EEPROM are set. The bits are earned by play; no controller-input path was found that sets them directly.

## 6. Tables

**Title menu (enumerated, 6/6):** OPTION, STORY, RECORDS(link), VS TEAM, VS SINGLE, PRACTICE.
**OPTION rows (enumerated, 10/10):** COM LEVEL, ROUND TIME, VS ROUNDS, VS HANDICAP, BUTTON CONFIG, BUTTON SETTING, SPECIAL CONTENT, RESET, RECORD RESET, EXIT.
**SPECIAL CONTENT on fresh save (1/1):** EXIT.

**Unlockable outcome messages** (all at `0x0850C3xx`–`0x0850CEF0`, verbatim, `$` = quote mark, `@` = line break):

| ROM address | Message |
|---|---|
| `0x0850C30F` | SPECIAL CONTENT EARNED |
| `0x0850C94F` | SHORTCUT TO PLAYER SELECT / IT CAN SET UP AS AN OPTION. |
| `0x0850C9CF` | $STRIKER$ SET UP OF THE NUMBER OF TIMES / OF THE MAXIMUM USE WAS ATTAINED. |
| `0x0850CA4F` | A SET UP OF THE STATE $POWER GAUGE$ WAS / ATTAINED. |
| `0x0850CACF` | COM LEVEL MAXIMUM INCREASED. |
| `0x0850CB0F` | SOUND TEST MODE ACQUIRED. |
| `0x0850CB4F` | $LONGEST$ COMMAND@INPUT TIME ACQUIRED. / IS NOW USABLE. |
| `0x0850CB8F` | CHALLENGE MODE / TIME ATTACK MODE ACQUIRED. |
| `0x0850CC4F` | ENDLESS MODE ACQUIRED. |
| `0x0850CCCF` | SPECIFIC COMBINATION TEAM IS... / SINOBU(MAD) |
| `0x0850CE0F` | POWER GAUGE MAX MODE@ACQUIRED. |
| `0x0850CE4F` | STORY MODE ON/OFF@HAS BEEN ACQUIRED. SCREEN. |
| `0x0850CECF` | BAO |

Plus hidden-striker markers `(HIDDEN)` / `(DIRK)` / `(SECRET)` / `(VISION)` at `0x0850994F`/`0x0850998F`/`0x08509ACF`/`0x08509C4F`. Count: **13 outcome messages + 4 hidden-name markers**. All are gameplay-earned; none is a typed code.

**Joypad masks (active-high, GBA standard):** A=0x001, B=0x002, Select=0x004, Start=0x008, Right=0x010, Left=0x020, Up=0x040, Down=0x080, R=0x100, L=0x200.

## 6b. Enumeration

This is a **no-code-system** engagement, so the §0.2 deliverables are stated as a bounded negative with counts.

**Search space actually covered**

| Search | Space | Result |
|---|---|---|
| Full-file keyword scan | 8,388,608 bytes × 56 patterns (14 keywords × {ASCII-upper, ASCII-lower, UTF-16LE, UTF-16BE}) | 0 password/cheat/code-entry/debug-menu/level-select strings. 6 benign hits: `BOSS_TASK` (`0x08A60F4`), `MID_BOSS_TEST`, `(HIDDEN)`, `(SECRET)`, `SOUND TEST MODE ACQUIRED.`, `SPECIAL CONTENT EARNED`. |
| ASCII string census | 70,056 strings ≥4 chars | Reviewed all cheat/debug keyword hits in context; none is a code. |
| Text banks decoded before negative | `0x08500000`–`0x08510000` (ASCII with control codes), `0x08A60000`–`0x08AC0000` (debug/motion names) | Decoded; no alphabet, keypad glyph set, or code prompt in either. |
| KEYINPUT literals | 3 occurrences of `0x04000130` in 8 MiB; 1 reader function | No second input path. |
| Input-global literal pools | 8 refs to `held`, 16 to `pressed`, 1 to `prev` | All ordinary menu/gameplay input; no sequence index or length/counter loop. |
| Button-mask data scan | 2,256 runs of ≥3 plausible active-high mask halfwords in the first 4 MiB | All fall inside ARM/Thumb instruction streams or compressed data; none is a referenced code table. |
| Debug-menu string reachability | `0x08A7960`–`0x08A7A40`: 0 raw aligned ptrs, 0 Thumb LDR literals, 0 BL targets (4 unaligned hits in compressed blocks) | Unreachable development text (PRACTICE panel). |
| Debug-task reachability | `0x08A600F4`–`0x08A61400`: 7 BL candidates, all sourced from `0x086xxxxx`–`0x087xxxxx` compressed data; 1 raw ptr inside a data record at `0x080B9224` | Unreachable development residue. |
| Empirical button codes at title | 8 combinations | 8/8 produced normal navigation; 0 hidden screens. |

**Reachable-screen enumeration (walked, with evidence):** boot splash chain (4 screens), title (6 entries), OPTION (10 rows), SPECIAL CONTENT (1 row), player-select grid (~30 portraits, ~2 unlocked on a fresh save), 2 VS entry paths, PRACTICE entry, in-match pause prompt, RECORDS link error. Total distinct screens observed: 12. No screen presents a code field.

**RAM evidence (observed, savestate diff):** title cursor at `0x0200074C` and mirror `0x02000754` read `0x01` (OPTION), `0x02` (STORY), `0x03` (RECORDS) across three consecutive savestates after 0, 1 and 2 Down presses. Confirms the menu enumeration is the *real* reachable set, not a guess from rendered text.

**Novel code:** none generated — there is no encoder, validator, alphabet, checksum or code table to feed. Generating a string would be meaningless: the game has no field that consumes one. This is the honest §0.2 outcome for a system with an empty code space (representable code values = **0**).

**Rejection bounds:** not applicable for the same reason. The closest bounded test performed was the `RECORDS` link entry, which rejects standalone use with `COMMUNICATION ERROR` (observed), and the 8 button combos, all of which were "rejected" as cheats by producing only normal navigation. The unlockables are gated by EEPROM state, not by input: the fresh-save SPECIAL CONTENT screen showing exactly `EXIT` is the observed zero-state of that gate.

**Negative classification (guide §16.3):** No system (not dead code / cut feature / gated feature) for password and button-code cheats; gated-feature for unlockables, with the gate being EEPROM play progress. The one apparent "debug menu" is a misclassification risk resolved as ordinary PRACTICE text.

## 7. Validation evidence

- **Observed** — mGBA screenshots of all 12 screens; savestate RAM cursor values `0x01/0x02/0x03` at `0x0200074C`; `.sav` revision counter advancing `0x07`→`0x08`→`0x09`; all 8 button-combo outcomes; SPECIAL CONTENT empty on a fresh save.
- **Derived** — Thumb disassembly of `0x08095668` (input masks and addresses); literal-pointer/BL/LDR counts in §6b; text-bank decoding; savestate `gbAs` layout.
- **Inferred (low confidence, not claimed as fact)** — that each unlock message corresponds to a distinct EEPROM bit; the bit offsets were not isolated. That the `0x08A7xxxx` strings are the PRACTICE panel (strongly supported by their exact labels and zero code references, but the panel itself was not visually reached).

## 8. Unknowns

- EEPROM bit layout / thresholds for the 13 unlockables were not isolated; earning one in a full playthrough was out of scope for this pass.
- The Japanese SKU (`AEXJ`?) and any other revisions were not examined; a region-specific code cannot be excluded, only the analyzed `AEXE` image.
- The exact screen that hosts the unlockable SOUND TEST once earned was not reached.
- No link-cable partner was available, so the RECORDS exchange path was only observed to its error state.

## 9. Tooling

Scripts written in `/tmp/kofex2` (analysis artifacts, not redistributed): `scan_ptrs.py`, `ldr_scan.py`, `ldr_text.py`, `ldr_text2.py`, `scan_debug_refs.py`, `textscan.py`, `textscan2.py`, `maskscan.py`, `reach.py`, `inp_dis.py`, `keyinput_scan.py`, `ss.py`, `ss2.py`, `ui.py`, `combo.py`, `dbg.py`, `dbg_server.py`, `dbgc.py` (plus `dbg_server2.py`/`dbgc2.py`). External tools: `arm-none-eabi-objdump -M force-thumb/-force-arm`, Capstone (Python), `strings`, `xxd`, `grep`, `mGBA 0.10.5`, `Xvfb`, `openbox`, `xdotool`, `scrot`, ImageMagick, `gdb-multiarch` (GDB stub port 2345 was held by another concurrent agent's mGBA, so RAM work used CLI debugger + savestate `gbAs` extraction instead). Web recon: direct GameFAQs/TCRF fetches returned 403 (Cloudflare); Bing via a read-proxy returned only generic KOF results, so no published code list was verified. No fetched page was treated as instructions.

## 10. Legal note

No ROM image, extracted graphics, audio or game text is redistributed here. Only hashes, addresses, counts and short verbatim UI labels (needed to identify screens) are published.
