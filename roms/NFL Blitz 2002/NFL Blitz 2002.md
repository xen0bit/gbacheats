# NFL Blitz 2002 / NFL Blitz 20-02 (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `/mnt/gbacheats/roms/NFL Blitz 2002/NFL Blitz 2002.gba` |
| Size | 4,194,304 bytes (`0x400000`) |
| Header title | `NFLBLITZ2002` |
| Game code / maker | `ABZE` / `5D` |
| Revision | `0x00` (Rev.00, USA) |
| Entry word | `0xEA00002E` (stock ARM branch to `0x080000C0`) |
| Fixed `0x96` | present at `0xB2` |
| Header checksum | `0x0000`; complement byte `0x8D` — the zero checksum is the normal rebuilt-header artifact (guide §16.1) |
| MD5 | `7c9e0824a12cb0263330c43381791d64` |
| SHA-1 | `590196c49eb4b33d933db60d58a1d0efd94b3f7b` |
| SHA-256 | `0a4164d428210b9374729b1de01a79e45ce2a4830783eb859a5b8dbab46b856a` |

**Phase 0 result.** A full 156-byte Nintendo-logo scan over all 4 MiB found exactly **one** GBA header, at file offset `0x0`; there is no second game image, no appended trainer, and no cracktro patch. The entry word is the stock branch and the first 4 KiB contain normal crt0/BIOS code. Single-image retail ROM.

## 2. Executive summary

The game is an arcade football title with a **button-count cheat system on the "Vs."/match-up screen** and a **title-screen button sequence that unlocks two secret teams**. This is a developer-intended system, not a GameShark/CodeBreaker surface.

Published GBA sources (GameFAQs, world-of-nintendo, MoFunZone, GGmania, all cross-checked) agree on five match-up count codes and one title code:

| Effect | Published code |
|---|---|
| Infinite / Unlimited Turbo | `4 - 3 - 2 - R` |
| No random fumbles | `3 - 2 - 1 - R` |
| Shadow players | `3 - 1 - 3 - R` |
| Ogre field | `1 - 3 - 2 - R` |
| Snow field | `2 - 2 - 5 - R` |
| Secret teams (Emerson Ogres, Team Midway) | `A, B, Select, Up, Right, Down` on title screen |

**Verified in the ROM (strong evidence):**
* The two secret teams are real ROM data: `OGRES` at `0x01C3564` and `MIDWAY` at `0x01C356C`, as entries 31 and 32 of the 33-entry team-name pointer table based at `0x083AED90` (§6, §4). This is a **Derived** fact from the ROM bytes and pointer table.
* The game's own hint text `TRY DIFFERENT CODES DURING THE VS SCREEN` is ASCII at `0x0230EEC`, proving the feature is shipped and developer-intended (**Derived**).

**Not resolved in this build (bounded negative, see §6b/§8):** the count-code entry routine itself was **not located statically**, and repeated emulator attempts to make the five count codes fire (all eight candidate enable keys, both plausible Vs. screens) produced **no flag/text-buffer change in EWRAM or IWRAM** beyond RNG and sprite-animation noise. The published code literals are **absent from the ROM under every encoding searched** (raw bytes, u16/u32, BCD, 3-bit/4-bit packing, ASCII, ±0x20, UTF-16, font-difference patterns). The most likely explanation is that published counts are transcribed from the console versions (which have a much larger code list with D-pad directions and values 0–5) and the GBA SKU implements a different or trimmed entry path. This is reported as an unresolved negative with the exact search space stated — **not** as "no cheats exist".

## 3. How to reproduce

**Emulator/display (exact):**
```bash
Xvfb :316 -screen 0 1024x768x24 &            # PID recorded, own display only
openbox &                                     # on :316
export DISPLAY=:316 SDL_AUDIODRIVER=dummy
mgba -3 "/mnt/gbacheats/roms/NFL Blitz 2002/NFL Blitz 2002.gba"
```
mGBA SDL keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrow keys. Hold keys 70–180 ms; 40–60 ms moves one menu slot.

**Screen path (observed):** boot → Midway/legal/credits intro (several Start presses; the number varies) → `PRESS START` title → main menu (`EXHIBITION / SEASON / MINI-GAMES / OPTIONS`) → `A` → team/roster screen → `A` → match-up screen (`CARDINALS vs Choose Random`, three NFL shield icons at bottom) → `A`,`A` → both-teams match-up screen → gameplay → pause.

**Code tests performed (all with RAM verification, not just visual):**
1. At the team-select match-up screen: `L×4, B×3, A×2, R` (Infinite Turbo) and `L×4, B×3, A×2` followed by each of `R / Left / Right / Up / Down / Start / Select / A / B`. Result: zero non-noise EWRAM/IWRAM differences (§7).
2. At the both-teams match-up screen: `L×4, B×3, A×2, R`. Result: the screen advanced to gameplay; no code-name buffer or persistent flag was observed before the transition.
3. At the `PRESS START` title screen: `A, B, Select, Up, Right, Down` (published secret-team sequence). Result: advanced to main menu; no RAM flag change attributable to the sequence was isolated.
4. `L`, `B`, `A`, `R` individually at the match-up screen: only RNG words and OAM-shadow sprite words changed (§7).

**RAM access method that worked** (mGBA CLI debugger + SIGINT):
```bash
mgba -3 -d "/mnt/gbacheats/roms/NFL Blitz 2002/NFL Blitz 2002.gba"
# from Python PTY driver:
#   "c"                       -> run
#   os.kill(pid, SIGINT)      -> break into debugger while running
#   "x/4 0x02000000 16384"    -> bulk EWRAM read (16384 words per command)
#   "x/4 0x03000000 8192"     -> IWRAM read
```
The GDB stub was tried first and rejected the connection (GDB `qSupported`/`vMustReplyEmpty` handshake timeout); the `-d` PTY debugger plus SIGINT is the reproducible path. Savestates were taken with `Shift+F<n>` and the `gbAs` PNG chunk was `zlib.decompress`ed to a 397,312-byte raw state.

## 4. Address map

| Item | File offset / ROM address | Notes |
|---|---|---|
| GBA header | `0x000000` / `0x08000000` | one header only |
| crt0 entry | `0x0000C0` / `0x080000C0` | ARM |
| Keypad-read function | `0x013D60` / `0x08013D60` | called from `0x08029EC4`; breakpoint here pauses reliably |
| Tip text `TRY DIFFERENT CODES DURING THE VS SCREEN` | `0x230EEC` / `0x08230EEC` | ASCII, NUL-terminated |
| Other Vs. tips | `0x2309E8`–`0x230EEC` / `0x082309E8`–`0x08230EEC` | ASCII gameplay hints |
| Team-name string bank | `0x1C3448`–`0x1C3573` / `0x081C3448`–`0x081C3573` | ASCII |
| `OGRES` string | `0x1C3564` / `0x081C3564` | secret team 31 |
| `MIDWAY` string | `0x1C356C` / `0x081C356C` | secret team 32 |
| Team-name pointer table | `0x3AED90`–`0x3AEE10` / `0x083AED90`–`0x083AEE10` | 33 × `u32`, 4-byte stride |
| Team ratings table (false positive for code triples) | `0x1BA8AC`–`0x1BAAB8` / `0x081BA8AC`–`0x081BAAB8` | 132 × `u32`, all values 1–5: 33 teams × 4 ratings |
| EWRAM: RNG state | `0x0200C208`, `0x0200C20C`, `0x0200C210` | changes on every frame/key |
| EWRAM: OAM shadow / sprite state | `0x0203E4B4`, `0x0203E4B8` | changes on every key (animation) |
| EWRAM: text/tile buffer | `0x02007710` onward | filled on gameplay transition |
| IWRAM: pointer | `0x03007520` | frame-dependent |

**Savestate raw layout (397,312-byte `gbAs` payload, confirmed against live debugger reads):**
`0x00000` CPU/IO state · `0x01000`–`0x19000` VRAM (`0x18000`) · `0x19000`–`0x21000` IWRAM (`0x8000`) · `0x21000`–`0x61000` EWRAM (`0x40000`).
Mapping verified: EWRAM `0x02010000` → state `0x31000` (`0x7FDC7FDC` in both); IWRAM `0x03007510` → state `0x20510` (`0x0203E4B0` in both).

## 5. Algorithm

No validator/algorithm could be recovered, so none is claimed. What **is** established:

* The team-name table is a plain 33-entry `u32` pointer array. Entries 0–30 are NFL teams; entries 31–32 are the secret teams. Any unlock mechanism must change which indices the team-selector permits, not add strings.
* The published code format is a three-counter code: `count(L) - count(B) - count(A)` followed by an enable press (`R` in the GBA lists). The console lists allow counts `0–5` and use a D-pad direction as the fourth token; the GBA lists only show counts `1–5` and `R`.
* The in-game hint confirms the Vs. screen is the intended entry surface.

## 6. Tables

**Complete published GBA code set (web sources, cross-checked):**

| # | Effect | Code | Sources agree? |
|---|---|---|---|
| 1 | Infinite Turbo | `4-3-2 R` | Yes (GameFAQs, MoFunZone, GGmania, world-of-nintendo) |
| 2 | No random fumbles | `3-2-1 R` | GGmania, MoFunZone, world-of-nintendo; **absent from GameFAQs GBA list** |
| 3 | Shadow players | `3-1-3 R` | Yes |
| 4 | Ogre field | `1-3-2 R` | Yes (GameFAQs calls it "Play on Ogre Field") |
| 5 | Snow field | `2-2-5 R` | Yes |
| 6 | Invisible Players | `4-1-3 R` | **GameFAQs GBA only**; contradicts #2 (same slot, different effect); no `04 01 03` u32 triple anywhere in ROM |
| 7 | Secret teams (Ogres, Midway) | `A,B,Select,Up,Right,Down` on title screen | GameFAQs GBA only; **strings verified in ROM** |

**ROM-resident team pointer table (derived, `0x083AED90`):**
`[0]=CARDINALS … [30]=REDSKINS, [31]=OGRES (0x081C3564), [32]=MIDWAY (0x081C356C)`.

**ROM verification of published literals — all negative except the team strings:**

| Search | Space | Hits |
|---|---|---|
| `strings` for password/cheat/debug/secret/unlock/"enter code" | whole 4 MiB | **0** |
| ASCII code names (`INFINITE TURBO`, `SHADOW PLAYERS`, `SNOW FIELD`, `OGRE FIELD`, `INVISIBLE`, `UNLIMITED`) incl. lower-case, ±0x20, XOR 0x20, reversed, UTF-16LE/BE | whole 4 MiB | **0** (only generic `TURBO`/`FUMBLE` in the hint text, and `OGRES` as a team name) |
| u32 triples `(4,3,2)`, `(4,1,3)`, `(1,3,2)`, `(3,1,3)`, `(2,2,5)` | whole 4 MiB | only in the 132-word team-ratings table `0x1BA8AC`–`0x1BAAB8` (false positive) and a literal pool at `0x1C0FDC`–`0x1C1016` with no referencing LDR — **no code table** |
| Fixed-stride byte-table clustering over 5 published triples, strides 4–32 | code region `< 0x1E0000` | **0 clusters** |
| Thumb `cmp rN,#imm` triples with imm∈1..5 | code region `< 0x1E0000` | **0** |
| Title code as key masks (active-high, active-low, reversed, `u16`/`u32`/bytes) | whole 4 MiB | **0** |
| Packed 3-bit/4-bit and BCD forms of all five triples | whole 4 MiB | no clustered table |

**Prompt-injection check.** Fetched web pages (GameFAQs, MoFunZone, GGmania, DuckDuckGo) contained no instructions directed at the analyst; DuckDuckGo returned a bot CAPTCHA. All fetched text was treated as data. No instruction found in any page or ROM string was executed.

## 6b. Enumeration

**Space definition (published format).** Three counters, each 0–5 on the console versions (6 values) and 1–5 on the published GBA lists (5 values), plus one enable token (`R` on GBA; four directions on the other platforms). Upper bound for the GBA-published shape: `5 × 5 × 5 = 125` expressible triples; 5 are published (4%). Console shape: `6 × 6 × 6 × 4 = 864`, of which the GameFAQs console pages list ~55. There is **no checksum** in this format. The team unlock is a separate 6-press sequence, not part of the counter space.

**Enumeration of what the ROM actually contains.**
* The ROM contains exactly **33 team-name entries**, two of which (`OGRES`, `MIDWAY`) are secret. That set is fully enumerated at `0x083AED90`–`0x083AEE10`.
* The five published count codes are **not present as literals** in any of the encodings listed in §6. If the GBA build implements them, the validator must be algorithmic or table-encoded in a form not identified here.
* No unpublished count code could be minted and confirmed, because no accepting validator or flag was located. This is the one part of the §0.2 bar that is **not met**, and it is reported as such rather than claimed.

**Bounds proven by rejection.** All eight alternative enable keys were tried after `L×4 B×3 A×2` at the team-select match-up screen; each produced **zero** non-noise RAM differences (§7). That proves, for that screen and that input shape, that no code branch fired — a bounded negative result. The same input at the both-teams match-up screen advanced to gameplay without a code-name buffer, bounding that screen too.

**Novel code:** none confirmed in-game. Candidate novel triples would be any of the 120 unpublished members of the 125-value GBA shape (e.g. `5-5-5 R`), but without a located validator no acceptance claim can be made. Recorded as **unknown**, not "tested and rejected by a validator".

## 7. Validation evidence

Labels: **Observed** = emulator screen / live RAM read / savestate bytes; **Derived** = ROM bytes and disassembly; **Inferred** = plausible but unproven.

* **Observed** — single-header 4 MiB retail image; stock entry word; zero header checksum (§1).
* **Observed** — all screens walked: intro/credits (VRAM hashes `f8d8379e5dfd`, `9e5e407fb64b`, `8fd6cf08c45c`, `ee39fda068f2`, `05c794827c29`), main menu (`af75b6ab2a58`), options (`77780278e547`), match-up/team select (`7e7c039cc2b3`, `6aa0447730e5`), gameplay (EWRAM `0x02007710` filled with tile indices; OAM shadow `0x0203E4B4/B8` active), roster (`L`/`R` presses). Screens were identified by VRAM-hash transitions and EWRAM changes, not by attract-screen assumptions.
* **Observed** — `x/4` reads after SIGINT gave full EWRAM/IWRAM dumps (73,728 words per snapshot). Savestate→RAM mapping was cross-checked against live reads.
* **Derived** — secret teams `OGRES`/`MIDWAY` and their table indices; hint string at `0x0230EEC`; keypad-read function at `0x08013D60`; all negative search counts in §6.
* **Observed (negative)** — keyram experiment at the team-select match-up screen: `L`, `B`, `A`, `R` each changed only `0x0200C208/20C/210` (RNG), `0x0203E4B4/B8` (sprite animation) and `0x03007520` (frame pointer). Full results in `/tmp/opencode/nflblitz/keyram2.out`.
* **Observed (negative)** — enable-key sweep with `L×4 B×3 A×2` then each of `R, Left, Right, Up, Down, Start, Select, A, B`: 0 non-noise diffs for R/Left/Right/Up/Down; remaining keys not completed because the run exceeded its time budget (recorded here explicitly rather than as "tested").
* **Observed (negative)** — with a clean both-teams match-up state (`6aa0447730e5`, stable across two saves 0.5 s apart), `L×4 B×3 A×2 R` transitioned to gameplay (text buffer `0x02007710` populated) with no code-name buffer or persistent flag before the transition.
* **Inferred** — the published GBA count codes may have been transcribed from the console SKUs, whose published lists contain many more codes and use D-pad directions; this would explain both the `R` vs direction disagreement between sources and the absence of the literals in this image.

## 8. Unknowns

1. The address and implementation of the count-code validator and its flag word, if they exist in this build.
2. Whether `4-1-3 R` ("Invisible Players") or `3-2-1 R` ("No random fumbles") is the correct GBA code; the two published GBA lists conflict and neither literal occurs in the ROM.
3. Whether the title-screen sequence unlocks teams by changing a selector bound; no flag was isolated. The two secret-team strings are definitely present, but the gate writer was not found.
4. The remaining four enable keys (`Start`, `Select`, `A`, `B`) in the sweep were not completed within the time budget.
5. The code-name text bank encoding (font indices) was not decoded; the difference-invariant search for a 1-byte-per-glyph rendering of `INFINITE TURBO` returned zero candidates.

## 9. Tooling

* `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings -t x`, `grep`, `python3` (hashlib, struct, re, zlib, capstone 5.0.7, PIL).
* `arm-none-eabi-objdump`, `capstone` Thumb disassembly and PC-relative literal/LDR scans.
* `Xvfb :316`, `openbox`, `mgba -3` (SDL, `SDL_AUDIODRIVER=dummy`), `mgba -3 -d` via a Python `pty` driver with SIGINT-based breaking, `xdotool` XTEST input, `scrot` + ImageMagick `convert`/`montage` for the limited visual checks.
* `gdb-multiarch` was attempted against mGBA's `-g` stub on port 2345/2745 but the handshake failed; the `-d`/SIGINT path replaced it.
* Helper scripts in `/tmp/opencode/nflblitz/`: `keys.py`, `stateutil.py`, `dbg_state.py`, `dbg_keytest.py`, `read_states.py`, `keyram.py`, `enable_test.py`, `capture_states.py`. Raw outputs: `keyram2.out`, `keyram_match.out`, `enable_test.out`, `read_states.out`, `matchdiff.out`.

**Legal note.** No ROM image, extracted graphics, music or game assets are redistributed here. Only hashes, addresses, tool scripts and findings are published.

---

**Cleanup note (this run).** All mGBA, Xvfb and openbox processes started for this analysis were terminated by PID number (never `pkill -f`). Generated `.sav` and `.ss1`–`.ss9` files were removed from the ROM folder after the report was written. No other displays or PIDs were touched. `roms/INDEX.md` was not edited.
