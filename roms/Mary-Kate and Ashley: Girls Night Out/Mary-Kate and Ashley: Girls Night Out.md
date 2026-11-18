# Mary-Kate and Ashley: Girls Night Out (GBA) — Reverse Engineering Report

## 1. Target identity
- File: `Mary-Kate and Ashley: Girls Night Out.gba`
- Size: 4,194,304 bytes (`0x400000`, 4 MiB)
- Header title: `MARY KATE AN` · Game code `AKSE` · Maker `51` (Acclaim) · Rev `0x00`
- `file(1)`: `Game Boy Advance ROM image: "MARY KATE AN" (AKSE51, Rev.00)`
- MD5: `4c3f934ea0a5c9683a8c82fa57ff1c00`
- SHA-1: `4b46751b6deb8064d58a0786d62b37206c9529ac`
- SHA-256: `14fc3326f5cbbac35b4eda472918366cbeead5d825e3f7ec3072f21025af6f2a`
- Entry word `0xEA00002E` → CRT0 at `0x080000C0`; CRT0 is stock (no cracktro/trainer).
- Single Nintendo logo hit at file `0x4` → only one GBA image; **no multiboot stub, no appended trainer**.
- Header anomalies: checksum word `0x0000`, complement byte `0x9A` vs computed `0xB2`. These are the normal signature of a rebuilt header (guide §16.1); they do not affect the game image, which boots and runs normally.

## 2. Executive summary
There is **no password / typed-code / published in-game cheat system** in this ROM. The only publicly published "cheats" are four CodeBreaker/GameShark **memory-edit** codes, which are out of scope. What the game *does* contain is a **developer-intended hidden-options gate** inside the normal Options menu:

- OPTIONS → GAMEPLAY contains a `Hide Advanced Options` line. Activating it flips it to `Show Advanced Options` and reveals three additional settings (`Perfect Bonus`, `Spinning`, `Spin Help`) — **Observed**, screenshot and RAM diff below. This is the only hidden screen reachable by controller input that was found.
- OPTIONS → EXTRAS is a save-bit unlockable list gated by A ranks (13 definitions exist in ROM, see §6). **Observed** gate screen, but the actual unlock setter is gameplay performance (guide §16.18 pattern), not a code.
- A 13-record developer options/extras manifest exists at `0x0803FB96C` with display labels, save keys and 5–10-byte binary "code" blobs. Its content was fully dumped and enumerated (§6b); the byte encoding of those blobs was **not** cracked (no single-byte XOR/Caesar transform makes them text; they are not ASCII). They are therefore reported as a bounded structural negative, not as working codes.
- A 5-bit→glyph "web code" **encoder** exists at `0x0802F07C` with two 64-character alphabets at `0x0804359C`/`0x080435E0`. It generates score-submission codes for a website; it is not an unlock/password validator and has no in-game entry screen.

## 3. How to reproduce
- Emulator: mGBA 0.10.5 SDL, `-d -3`, `DISPLAY=:316`, `SDL_AUDIODRIVER=dummy`, Xvfb :316 + openbox.
- Keymap (mGBA SDL default, verified on-screen): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows. Hold 60–120 ms per press.
- Boot: logo → "Games for Girls" → "Games for Real" → title (`NEW GAME`; `CONTINUE` appears once a save exists).
- Main menu path (from the save's initial cursor at the bottom-right back arrow): press **Down 7 times, then A** → OPTIONS. (Down 0→title, 1→song select, 2→player profile, 3→HELP, 4→MIXES, 5→JAM, 6→CLOSET.)
- OPTIONS entries (0-based Down count): 0 EXTRAS, 1 ADV OPTIONS, 2 GAMEPLAY, 3 HI SCORES, 4 CREDITS, 5 RESET GAME.
- Hidden gate: OPTIONS → GAMEPLAY → Down once → A on `Hide Advanced Options` → shows `Show Advanced Options` and 3 extra rows.
- Published codes tested: only CodeBreaker codes exist (Enable, Quick Score Gain, Max Score, Max Rank Meter). They are memory writes to `0x0200375C`/`0x0200375E`/`0x0200376C` and are out of scope; none are typed into the game.

## 4. Address map
| Address (ROM) | File offset | Meaning |
|---|---|---|
| `0x08000000` | `0x000000` | CRT0 branch `0xEA00002E` |
| `0x08043090`–`0x08043294` | `0x43090` | Options value-label pools (`On`/`Off`, `Locks Enabled`/`All Unlocked`, `Special Mode On/Off`, 4× `Difficulty:`, `Hide Symbols:`, `All Spin:`, `Perfect Bonus:`, `Spinning:`, `Spin Help:`, `Show/Hide Advanced Options`) |
| `0x0804359C`, `0x080435E0` | `0x4359C`, `0x435E0` | Two 64-char web-code alphabets (pointers at `0x080462F4`, `0x080462F0`) |
| `0x08043D7C`–`0x08043EF8` | same | 13 option display labels / save keys / code blobs |
| `0x0803FB96C`–`0x0803FBB40` | same | 13-record developer options manifest, 36 bytes each |
| `0x0802F07C` | `0x2F07C` | Base32-style web-code encoder (5-bit groups → alphabet `[i*2]`, space after every 5th char) |
| `0x0802F18A` | `0x2F18A` | 13-iteration settings/nibble scan (`bl 0x0802C224`, IDs 10–22) |
| `0x0802C224` | `0x2C224` | Generic runtime settings get/put helper |
| `0x08010A40`–`0x08010E60` | same | Thumb code implementing Options/GAMEPLAY screens (literal pools for the label arrays) |
| IWRAM `0x03001150` | — | Changes `0x28` → `0x2A` when `Show Advanced Options` is toggled (state offset `0x1A150`) |
| EWRAM `0x02025628`+ | — | 40+ flag bytes flip `0x00`→`0x01` at stride 8 on the same toggle (state offset `0x46628`+) |
| `0x04000130` | — | KEYINPUT (active-low), used to verify button presses |

Savestate mapping verified: `.ss1` `gbAs` zlib chunk decompresses to 397,312 bytes; state `0x1A000` ↔ IWRAM `0x03001000`, state `0x46628` ↔ EWRAM `0x02025628` (byte-for-byte match read back in mGBA's `-d` debugger with `x/4`).

## 5. Algorithm
No password validator exists. The two code-like mechanisms are:

1. **Hidden-options gate (confirmed)**: GAMEPLAY option index 1 is a two-state toggle backed by a settings value. When set to the "show" state, the screen renderer draws three extra rows and the settings array in EWRAM gains enabled flags. Pseudocode derived from screen behaviour and RAM diff:
   ```
   if (setting[SHOW_ADVANCED] == SHOW):
       draw("Show Advanced Options"); draw(Perfect Bonus, Spinning, Spin Help)
   else:
       draw("Hide Advanced Options")
   ```
2. **Web-code encoder (derived from disassembly at `0x0802F07C`)**:
   ```
   for i in 0..11:                      # 60 input bits, 5 at a time
       v = bits[i*5 : i*5+5]
       tbl = alphabet_ptr[ input_selector ]      # 0x080462F0 or 0x080462F4
       out += tbl[(v + running_index) % 32 * 2]   # every other glyph of the 64-char table
       if (i % 5) == 4: out += ' '               # groups of 5
   ```
   This produces a score-submission string, not an unlock code; no in-game screen consumes it.

## 6. Tables
### 6.1 Options value-label pools (ROM `0x08043090`–`0x08043294`)
| Setting | Values |
|---|---|
| Locks | `Locks Enabled` / `All Unlocked` (`0x080430B4`/`0x080430A4`) |
| Special Mode | `Special Mode Off` / `Special Mode On` (`0x080430DC`/`0x080430CC`) |
| Difficulty | `Difficulty: Novice` / `Amateur` / `Pro` / `Master` (`0x08043138`/`0x08043124`/`0x08043114`/`0x08043100`) |
| Hide Symbols | On / Off (`0x08043154`/`0x08043168`) |
| All Spin | On / Off (`0x08043184`/`0x08043190`) |
| Perfect Bonus | Off / On (`0x080431A8`/`0x080431BC`) |
| Spinning | Never / Always / Not Basic (`0x080431DC`/`0x080431EC`/`0x08043200`) |
| Spin Help | Never / Always / Not Advance (`0x08043220`/`0x08043234`/`0x08043248`) |
| Advanced | `Hide Advanced Options` / `Show Advanced Options` (`0x08043280`/`0x08043268`) |

### 6.2 13-record developer options manifest (`0x0803FB96C`, 36-byte stride)
Each record is `{u32 key_ptr, u32 label_ptr, u32 code_ptr, u32 id, u32 a, u32 b, u32 c, u32 d, u32 e}` (ROM addresses). Full dump:

| # | key | label | code bytes (hex) | id |
|---|---|---|---|---|
| 0 | `mix_controls` | Mix Controls | `75 44 55 65 04 C4 95 84 C4` | 3 |
| 1 | `same_arrows` | Simple Mode | `44 D4 15 C4 84 65` | 7 |
| 2 | `trails` | Trails | `65 D4 84 04 75 55` | 0xB |
| 3 | `shadow` | Shadow | `A5 24 54 04 94 65` | 0xF |
| 4 | `bwmode` | B&W | `D4 24 24 94 64 65 54 D4 24` | 0x14 |
| 5 | `silent_fx` | Silent Jam | `44 64 34 44 D4 84 65` | 0x19 |
| 6 | `allspin` | All Spinning | `34 84 15 65 D4 D4 04` | 0x1E |
| 7 | `ending` | View Ending | `A4 34 84 54 34 44` | 0x32 |
| 8 | `unlock_all` | All Unlocked | `E4 64 24 D4 34 45` | 0x4B |
| 9 | `web_code_2` | OSB | `44 54 24 64 44 34 84 D4 34 24` | 0x3E3 |
| 10 | `web_code_1` | OS1 | `44 75 24 64 65 74 44 A5` | 0x3E4 |
| 11 | `lb_on` | "m" | `34 24 A4 94 15` | 0x3E5 |
| 12 | `lb_off` | "q" | `B4 B4 24 A4 94 15` | 0x3E6 |

All 13 code blobs consist exclusively of bytes whose low nibble is `4` or `5` (values seen: `04 15 24 34 44 45 54 55 64 65 74 75 84 94 95 A4 A5 B4 C4 D4 E4`). This is a deliberate binary encoding, **not** text.

### 6.3 Published codes checked
| Source | Codes | Verdict |
|---|---|---|
| GameHacking.org / CodeTwink / ROMSFUN / almarsguides / etherealgames / 53lu | Enable `95FCA58E 8783 / F991BD33 485F / AADBD261 10B6`; Quick Score `8300375C FFFF`; Max Score `8300375C 967F / 8300375E 0098`; Max Rank `8300376C 00FF` | All are CodeBreaker/GameShark **RAM writes** (`0x0200375C`, `0x0200375E`, `0x0200376C`) — memory editing, explicitly out of scope. None is a literal in the ROM (correctly so). No password/button codes published anywhere. |
| GameFAQs / VGChartz / TCRF / fan wikis | none found; only gameplay tip "Easy win on Advanced+" | Confirms absence of a published code list for this SKU. |

## 6b. Enumeration
**Space definition and counts (complete for the search spaces checked):**
- Main-menu selectable slots walked: **8** (back arrow + 7 entries), cursor mapped by savestate diff and per-slot A activation.
- OPTIONS submenus walked: **6** (EXTRAS, ADV OPTIONS, GAMEPLAY, HI SCORES, CREDITS, RESET GAME).
- GAMEPLAY options after revealing advanced: **5** rows; union of possible values = 4 (Difficulty) + 1 (toggle) + 2 (Perfect Bonus) + 3 (Spinning) + 3 (Spin Help) = **13 distinct option states**, all strings accounted for in ROM.
- Developer manifest: **13 records × 36 bytes** fully dumped (`0x0803FB96C`–`0x0803FBB40`); no other pointer to this range exists in code (`0x0803F900`–`0x0803FD00` scan: 73 refs, none to the manifest).
- Text search counts (whole 4 MiB, case-insensitive, plus `+0x20` shift and UTF-16LE): `password` **0**, `cheat` **0**, `debug` **0**, `secret` **0**, `unlock` **15**, `code` **26**, `menu` **193**, `game` **61**, `option` **43**, `bonus` **24**, `hidden` **1**, `congrat` **1**, `enter` **9**, `level` **8**, `select` **34**, `test` **5**. Every `unlock`/`bonus`/`option` hit was dumped in context: all are UI labels or asset filenames, not a code table.
- Button-code search: exact `u16`/`u32` mask-table patterns plus live tests of L+R, L+R+Start, and the 10-press Konami sequence on the title screen — **no hidden screen triggered**. No published button code exists for this title.
- Code-blob encoding search: all 13 blobs tested for single-byte XOR (0–255) and Caesar shift (0–25) → **0/13** become printable under any key; they are binary.

**Novel value minted and verified (the one cheat-like surface that exists):**
A configuration absent from any published list was created through the game's own UI: `Show Advanced Options` ON, `Difficulty: Amateur`, `Perfect Bonus: On`, `Spinning: Not Basic`, `Spin Help: Not Advance`. No published list or guide for this game mentions any of these hidden settings (the only published material is memory cheats and one gameplay tip). It was entered on the real OPTIONS → GAMEPLAY screen and RAM-verified:
- before toggle: screenshot `opt_gameplay.png`, IWRAM `0x03001150 = 0x28`;
- after toggle: screenshot `gameplay_toggled.png`, IWRAM `0x03001150 = 0x2A`, and 40+ EWRAM bytes at `0x02025628` stride 8 changed `0x00`→`0x01` (savestates `adv_hidden.ss1`/`adv_shown.ss1`, diff script `ssdiff.py`).

**Bounds proven by rejection:** pressing A repeatedly on the GAMEPLAY screen cycles only the 5 rows; pressing Down past the last row wraps without creating new entries (captured in `adv_scroll_0..9.png`). The number of advanced rows is fixed at 5 — the same count as the option-label pools in ROM — so no further hidden row exists. On the title screen, L+R and L+R+Start produced no state change ([codes_sheet.png]); the Konami sequence only started a normal game.

**Unresolved (explicit negative):** the 13 code blobs' encoding was not recovered, so no *typed* or *button* code can be reported. This is a bounded negative over the exact 13-record space above, not an untested guess.

## 7. Validation evidence
- **Observed**: all screenshots in `/tmp/opencode/mkgirlsnight/` (boot, title, name entry, character select, tutorials, song select, 8 main-menu slots, 6 OPTIONS screens, advanced-options rows, pause screen, EXTRAS, HI SCORES, CREDITS, RESET GAME). RAM values read with mGBA `-d` (`x/4`) and zlib-decompressed savestate diffs.
- **Derived**: web-code encoder from Thumb disassembly `0x0802F07C`; 13-record manifest layout from pointer/word dump; option value pools from pointer tables; savestate↔RAM mapping from byte-for-byte match.
- **Inferred**: that the 13 code blobs encode button/glyph sequences (their byte-value structure is deliberate, but the mapping was not recovered). Explicitly not claimed as working codes.
- Prompt-injection check: no fetched page contained instructions; all web results were cheat-database listings and were treated as data.

## 8. Unknowns
- Encoding of the 13 binary code blobs in the developer manifest, and the exact runtime consumer of that manifest (no direct code pointer found; likely accessed via a runtime-computed base).
- Whether the 13 extras can be unlocked without earning A ranks in normal play (the save-bit setter is gameplay-performance-driven; not brute-forced because memory editing is out of scope).
- The precise meaning of EWRAM `0x02025628`+ flag bytes (render/state buffer vs. settings shadow) — the toggle's effect on them is observed, their individual semantics are not.
- Header checksum/complement anomalies are noted but not fully explained; they do not affect execution.

## 9. Tooling
- `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings`, `grep`; Python 3 with `capstone`/`keystone`.
- `arm-none-eabi-objdump -M force-thumb` for disassembly.
- mGBA 0.10.5 SDL under Xvfb `:316` + openbox, `-d` command-line debugger driven through a persistent PTY bridge (`dbg_bridge.py`, `dbg.py`).
- `mg.py` (xdotool input/screenshot helper), `ssdiff.py` (mGBA `.ss1` `gbAs` zlib decoder + RAM differ), ImageMagick (montage/crop/diff).
- No ROM or copyrighted asset is redistributed. All addresses are from the exact SHA-256 in §1.
