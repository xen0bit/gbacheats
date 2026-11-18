# NHL Hitz 2003 (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `NHL Hitz 2003.gba` (4,194,304 bytes = `0x400000`) |
| Header title | `NHL HITZ 20\0` (12-byte field) |
| Game code | `AN4E5D` → code `AN4E`, maker `5D` (Midway), NTSC-U |
| Version / complement / checksum | `0x00` / `0x0D` / `0x0000` |
| Entry word | `0xEA00002E` (stock branch to `0x080000C0`) |
| Nintendo logo scan | exactly **one** hit, at file `0x4` → single retail image, no appended trainer, no multiboot/multi-game pack |
| MD5 | `e6b4bd3c5f5b3d57c2e29c4a9b377b26` |
| SHA-1 | `4a88ca2962fdfb7ea1b91b9e2bffe8c69ff96519` |
| SHA-256 | `a49e2ccff45d57f2dd8ae0a0a0c5c2b2365af5d34d6b874bbbdb72ed26201fb8` |

Phase 0 conclusion (**Derived**): clean retail image. The header checksum `0x0000` is the usual rebuilt-header
artifact (§16.1); the complement byte is `0x0D`, the entry word is stock, and the file size is an exact power of
two with one logo. No cracktro/trainer/patch was present, so all addresses below are for this exact revision.

## 2. Executive summary

**There is no developer-intended cheat, password, button-code, or hidden/debug menu in this GBA SKU.**
This is a *closed negative result* (§0.2), not an unfinished search:

* The complete UI text bank (`0x082FC914`–`0x082FD2B4`, plain lowercase ASCII) contains every label drawn by the
  game — credits, all menu items, all option values, all season screens. It contains **zero** occurrences of
  `password`, `cheat`, `code`, `debug`, `secret`, `unlock`, `hidden`, `invalid`, `correct`, `wrong`, `generator`.
  The same negative holds under the `±0x20` letter shift and UTF-16LE/BE/UTF-32 encodings (§11, §16.11).
* Every reachable screen was walked in mGBA with screenshot + savestate-RAM evidence (§4): title → main menu →
  options (Game/Sound/Credits) → exhibition (choose sides → teams → players → jerseys → gameplay → pause →
  Stats/Strategy/Game Options/Sound Options) → season (setup → choose team → Season Central → rosters/calendar/
  standings/options) → link up. No hidden entry, no extra row, no secret screen appeared on any of them.
* The only special input found statically is **A+B+Start+Select held simultaneously** at `0x0800C014`, which calls
  a soft-reset routine at `0x0800B030` (verified in emulator: returns to the Midway splash, RAM flag
  `0x02000888` clears). This is a system reset, not a cheat.
* Static analysis of the keypad path found **no sequence matcher**: three `KEYINPUT` literal references
  (`0x0800A868` input handler, `0x0800C038` reset combo, `0x080104E8` link input); 94 blocks around references to
  the key-state globals contain **no** `cmp`/`and`/`tst` against any key mask (`0x10/0x20/0x40/0x80/0x100/
  0x200/0x300/0x3FF`). Ten common button sequences pressed at the title screen produced no new screen and no
  persistent flag.
* Published material: the only GBA-specific page (Absolut Cheats) lists a single *gameplay hint*
  ("Easy goal" — pass to the opposite winger near the red line for a one-timer; `1-Timers` is a real stat row),
  **not a code**. All unlockables published for this title (Winnipeg Lumberjacks, Rome Gladiators, stadiums,
  jerseys) belong to the **GameCube/PS2/Xbox Franchise mode**, which is a different game (§16.11); no GBA code
  literal from those lists exists in this 4 MiB image. GameFAQs/TCRF/VGChartz yielded no GBA code list.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 (SDL), `SDL_AUDIODRIVER=dummy`, Xvfb `:319`, 3× scale, crop viewport `720x480+153+166`.
* Keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows. Hold keys 60–150 ms.
* Deterministic entry: boot, wait ~15 s for the `PRESS START` title, press `Return`; main menu appears.
  `shift+F1` saves slot 1 (main menu), `shift+F8` saves slot 8 (title), `F1`/`F8` reload. Savestates were kept
  outside the final tree and deleted.
* Menu paths walked (exact):
  * `Options → Game Options` (8 rows; Skill Level cycles Rookie→Pro→All-Star), `→ Sound Options` (Sound FX /
    Music / Voice, all On/Off), `→ Credits`.
  * `Exhibition → choose sides → choose teams` (30 teams; Washington→Anaheim wrap observed),
    `→ choose players` (9 skaters; Kovalchuk→Heatley wrap after 9 presses, RAM-verified via the IWRAM name
    buffer), `→ choose jerseys (team advantage) → gameplay`.
  * In game `Start → Resume / Stats (8 rows) / Strategy (2 rows × 3 values) / Game Options / Sound Options /
    Exit Game`.
  * `Season → Mode{Season,Playoff}, Num Games{82,20,58,…}, Playoff Length{Best-of-7,1 Game,Best-of-5,…} →
    choose your team → Season Central{play game, rosters, calendar, standings, options, main menu}`.
  * `Link Up → Connecting / waiting …`.
* Codes tested: none exist to test; published GBA page has only a gameplay hint (no literal to enter).

## 4. Address map

| Address (ROM or RAM) | Meaning | Evidence |
|---|---|---|
| `0x08000000` / file `0x0` | Header; stock entry `0xEA00002E` | Derived |
| `0x082FC134`–`0x082FC90C` | Credits text (ASCII) | Observed (strings) |
| `0x082FC914`–`0x082FD2B4` | **Complete UI text bank** (ASCII lowercase, all menu labels/values) | Observed |
| `0x082FD168`–`0x082FD2B4` | printf/link/debug leftovers (`bad timing`, `cnt>20 b`, `EEPROM error`, `MultiSioSync010918`) | Derived |
| `0x08340869` + `n*0x2AC` | Team record `n` (0..29): city at `+0x0`, nickname at `+0x14`, player records (~`0x38` each, first/last names) from `+0x45`; exactly 30 real NHL teams | Derived |
| `0x0800A820` | Keypad handler: `ldrh` from `0x04000130`, `~KEYINPUT` → held, `new & ~old` → pressed | Derived (objdump) |
| `0x02000000` (u16) | held key mask (active-high) | Derived |
| `0x020008A0` (u16) | newly pressed key mask | Derived |
| `0x02000868` (u16) | key-repeat counter (threshold 39, reset to 9) — *not* a cheat progress index | Derived |
| `0x0800C014`–`0x0800C02A` | `if (0xF & ~KEYINPUT == 0xF) BL 0x0800B030` (A+B+Start+Select) | Derived |
| `0x0800B030` | Soft reset: clears word `0x02000888`, sets byte `0x020008A8 = 3`, waits, reboots | Derived + Observed |
| `0x03000000`+ | IWRAM; text-render buffer at `0x03000002` shows selected player surname suffix (`atley`=Heatley, `berle`=Kaberle, …) | Observed (savestate diff) |

Savestate layout used for RAM proof (§16.13): `NHL Hitz 2003.ssN` is a PNG with a zlib `gbAs` chunk;
decompressed state is 397,312 bytes; IWRAM at state `0x19000`, EWRAM at state `0x21000`
(so RAM `0x02000888` → state `0x21888`).

## 5. Algorithm

No password validator, checksum, key table, or button-sequence automaton exists. The only "algorithm" is
the keypad path:

```
held  = ~KEYINPUT & 0x3FF                       @ 0x0800A838
press = held & ~old_held                        @ 0x0800A844
store held -> 0x02000000 ; press -> 0x020008A0   @ 0x0800A83C/48
if (0xF & ~KEYINPUT) == 0xF: soft_reset()       @ 0x0800C014   ; A+B+Start+Select
```

The 40-frame/9-frame counters at `0x0800A888`/`0x0800A890` implement OS key-repeat, not cheat progress:
they write the held mask to a repeat slot and rewind the counter to 9.

## 6. Tables

* **Team table** — 30 entries, stride `0x2AC`, starting `0x08340869`: Anaheim, Atlanta, Boston, Buffalo,
  Calgary, Carolina, Chicago, Colorado, Columbus, Dallas, Detroit, Edmonton, Florida, Los Angeles, Minnesota,
  Montreal, Nashville, New Jersey, N.Y. Islanders, N.Y. Rangers, Ottawa, Philadelphia, Phoenix, Pittsburgh,
  San Jose, St. Louis, Tampa Bay, Toronto, Vancouver, Washington. No 31st entry exists: pressing Right from
  Washington wraps to Anaheim (Observed), and the roster bank ends after Washington's players.
* **Player selection** — 9 selectable skaters per team (goalies are chosen separately). Names cycles wrap after
  9 presses; the IWRAM name buffer confirmed all nine for Atlanta (Heatley, Kaberle, Kozlov, Bartecko, Rheaume,
  Stefan, Tremblay, Kovalchuk, McEachern). No hidden player value.
* **Game Options rows** — 8: Skill Level {Rookie, Pro, All-Star}; Period {2 mins, …}; Penalties/Fighting/
  Stamina/Auto Replay {On,Off}; Player Select {Manual,Auto}; Mercy Rule {Off,On}. No hidden value.
* **Pause rows** — 6: Resume, Stats, Strategy, Game Options, Sound Options, Exit Game.
* **Strategy rows** — Offensive {Defensive, Normal, Aggressive}; Defensive {Zone, Man on Man, Cherrypick}.
* **Season Central rows** — 6: play game, rosters, calendar, standings, options, main menu.
* **Text search space (bounded)** — 12,880 strings; keyword counts all zero for `password`, `cheat`, `code`,
  `debug`, `secret`, `unlock`, `hidden`, `invalid`, `correct`, `wrong`, `generator`; `enter`=1, `level`=1,
  both in ordinary menu text. Also zero under `+0x20`, `-0x20`, `^0x80`, UTF-16LE/BE, UTF-32.
* **Keypad search space (bounded)** — 3 `0x04000130` literals, 94 disassembled reference blocks to key globals,
  0 key-mask comparisons found; 10 button sequences tested at the title screen with screenshot signatures,
  none produced a new screen or persistent flag.

## 6b. Enumeration

**Space size: 0.** There is no code/password space to enumerate — no alphabet, no length, no checksum, no
acceptance table, no key-mask automaton. Consequently the §0.2 deliverables "generate a novel code" and "prove
bounds by rejection" are **not applicable**: there is no validator to call and no input to reject. The negative
is instead bounded by the counts above:

1. Every reachable screen was enumerated and entered (title, boot splashes, main menu, options×3, exhibition×6
   stages, gameplay, pause×5 sub-screens, season setup, season central×4 sub-screens, link up).
2. The entire text space was searched in five encodings with per-keyword counts (§6).
3. The entire keypad reference space was scanned statically (3 key-read sites; 94 blocks; 0 sequence checks)
   and 10 common sequences were pressed dynamically (Konami, L+R+Start, L+R+Select, A+B+Start+Select, L+R+A+B,
   all directions, Start×3, Select×3, L+R+A+B+Up, B-A-B-A). Only Start (normal navigation) and
   A+B+Start+Select (soft reset, RAM-verified) had any effect.
4. Published codes: none for GBA. The one GBA-specific published hint is a gameplay technique, not a code; the
   widely published unlockables are for other platforms and their literals are absent from this ROM.

This is a **"no system"** result in the §16.3 taxonomy, distinguished from dead code, cut features, and gated
features: there is no orphan handler or unused table to gate.

## 7. Validation evidence

* **Observed** (emulator, screenshots on disk in `/tmp/opencode/nhlhitz/`, savestate RAM): all screens listed in
  §3; 30-team and 9-player wrap; 8 Game Options rows and 3-value Skill Level cycle; 6 pause rows; 2×3 Strategy
  values; 6 Season Central rows; A+B+Start+Select → Midway splash with `0x02000888` transitioning `1→0→1` and
  59,846 state bytes changing; IWRAM `0x03000002` surname suffix changing with each player press.
* **Derived** (objdump, literal decode, savestate parser): single header, stock entry, text-bank extent and
  content, team record stride, keypad globals, `0x0800C014` combo predicate, `0x0800B030` reset routine, no
  key-mask comparisons in 94 reference blocks.
* **Inferred**: that credits text at `0x082FC134` is the roll shown at main-menu Credits (animated display was
  not screenshot-frame-by-frame); that `0x02000868` is key-repeat rather than cheat state (its 39/9 thresholds
  and single write site make this high-confidence but not a full UI-behaviour trace).
* **Limitations**: the GDB stub in this mGBA build kills the emulator on client disconnect, so the §16.19
  validator-as-oracle trick could not be used; it was unnecessary because no validator exists. RAM evidence
  used §16.13 savestate diffing instead. A full 82-game season was not simulated; season-only unlockables would
  have to be save-bit flags, but no unlock/secret string exists in the save/text banks and no published GBA
  unlockable exists to test for (§16.18).

## 8. Unknowns

* Whether an unadvertised *gameplay* technique beyond "one-timer near the red line" exists (out of scope:
  not a code, password, menu, or unlockable).
* Whether the GameCube/PS2/Xbox unlockables were cut from the GBA build intentionally — likely yes, since the GBA
  roster has exactly 30 real NHL teams and no stadium/jersey selection screen; not proven by a cut-flag string.
* The exact set of Num Games values beyond the observed {82, 20, 58} (all in the normal range; no hidden value
  was seen in five Right presses).

## 9. Tooling

* `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings -t x -n 4`, `grep -abo`, Python `struct`.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for keypad routines;
  Capstone 5.0.7 script `keyscan.py` for PC-relative literal xrefs to key globals.
* mGBA 0.10.5 under Xvfb `:319` + openbox; `xdotool` XTEST input; `import`/`convert` screenshots; `tesseract`
  for OCR screening; Python/PIL image signatures for combo screening.
* `ssread.py` — PNG `gbAs` zlib savestate decoder (397,312-byte state; IWRAM `0x19000`, EWRAM `0x21000`) used
  for all RAM evidence; `enum_players.py` for player-name buffer reads; `combos2.py`, `combo_test.py`.
* Web: Brave Search HTML, Absolut Cheats GBA page, GameFAQs/TCRF/VGChartz search results. Fetched pages were
  treated strictly as data; no prompt-injection payload was encountered.

**Legal note:** no ROM bytes, graphics, or copyrighted assets are reproduced here; only hashes, addresses, and
the analyst's own tooling are published.
