# Mega Man Battle Network 5: Team Protoman (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

> **SKIPPED / DEFERRED — entry systems found but not in-game confirmed (coordinator decision).**
> Under §0.2 this report does **not** meet the dynamic-confirmation bar: two genuine cheat
> systems exist per published sources (48 eight-digit Numberman Lotto passwords and ~20
> ten-button Navi Customizer compression codes, both algorithmic with all published literals
> absent from the ROM), but the Numberman machine and Navi Customizer are **story-gated** and
> were not reached from a fresh save, so no code was entered in-game, the validator address was
> not found, and no novel code or rejection bounds were produced. Per coordinator authorization,
> MMBN titles whose validator/code-entry surface is blocked by a story gate are documented here
> and **skipped rather than retried or indexed**. The full code tables and gate are recorded
> below. This report is intentionally left out of the completed-reports table and listed under Skipped ROMs in the top-level `README.md`.

Queue position 462. Analysis date 2026-11-18. All addresses below are **ROM addresses**
(`0x08000000 + file offset`) unless labelled "file". ROM analysed is the exact image
whose hashes are recorded in §1; no other revision is assumed.

---

## 1. Target identity

| Field | Value |
|---|---|
| File | `Mega Man Battle Network 5: Team Protoman.gba` |
| Size | 8,388,608 bytes (0x800000) |
| `file` | Game Boy Advance ROM image: "MEGAMAN5_TP_" (BRBE08, Rev.00) |
| Header title (0xA0) | `MEGAMAN5_TP_` |
| Game code (0xAC) | `BRBE` |
| Maker (0xB0) | `08` (Capcom) |
| Version (0xBC) | `0x00` |
| Entry branch (0x00) | `0xEA000032` → ARM crt0 at `0x080000D0` |
| Build stamp (file 0x3DF7C) | `REXE5TOB 20041006 US` (Team **of Blues**, 2004-10-06, USA) |
| MD5 | `71b00ba406c522d3cec48311bd7bc760` |
| SHA-1 | `b3774e96b1f107bb8b1db79b216be41b9bc5bac0` |
| SHA-256 | `b35f5890f54784c9d90a896dc5ac4831d43acc9f94e8c42816742fcfa6b41a7b` |

### Phase 0 header / patch scan

* **Embedded GBA headers:** a scan of the whole 8 MiB for the Nintendo-logo prefix
  `24 ff ae 51 69 9a` found **exactly one** hit, at file `0x04` (the primary header).
  There is **no multiboot image, second game, or appended trainer** in this file.
* **Modified header (observed):** the 156-byte logo region at file `0x04..0x9F` is
  **not** the standard Nintendo logo — only its first 6 bytes (`24 ff ae 51 69 9a`)
  match; the remaining 150 bytes are pseudorandom. Header complement byte `0xBD`
  is `0x41` while the byte-wise complement over `0xA0..0xBC` computes to `0x5A`,
  and the header checksum at `0xBE` is `0x0000`. This is a **rebuilt/patched header**
  (guide §16.1). The user code itself is intact: the crt0 at `0x080000D0` is normal
  ARM code (`mov r0,#0x12; msr ...; ldr r1,[pc,...]`) and the game boots and plays
  correctly in mGBA. No cracktro, no trainer menu, no code that patches the joypad
  reader was found.
* **Conclusion:** header edited, cartridge body authentic. Treat all addresses as
  belonging to the hash above.

### Sibling comparison (independent, static only)

`Mega Man Battle Network 5: Team Colonel.gba` (SHA-256
`d4b7aefc3918c9f801c84cfd1322c2cdbb9d13c2e3271b3c3f8f9927480f2633`) was inspected
**read-only**; its display was not touched. It is a **different build**: game code
`BRKE`, header title `MEGAMAN5_TC_`, build stamp `REXE5TOK 20041006 US` (file 0x3DF80),
and a different MD5/SHA. The two images share **32.21 %** of their bytes (2,701,686 of
8,388,608) — the common Capcom engine, graphics, sound and script — but the published
password literals tested (e.g. `35607360`) are **absent from both images**. Nothing
found in this Protoman image was copied from the Colonel analysis; the shared part is
generic engine code, and any SKU-specific finding must be verified per image (§16.11).

---

## 2. Executive summary

The target is a save-battery Capcom card-battler, **not** a password-only cart. Two
*developer-intended* cheat surfaces are documented for this SKU on the public web and
were confirmed to be genuine features of the game (not GameShark/CodeBreaker):

1. **Numberman Lotto machine** at Higsby's shop — 48 published **8-digit decimal**
   passwords granting Navi Customizer programs / chips (full list in §6).
2. **Navi Customizer compression codes** — ~20 published **10-button sequences**
   (hold D-pad Right, then press the sequence) that shrink a program by one block.

**Both systems are algorithmic, not lookup tables.** An exhaustive literal search
(§7) shows that **none** of the 48 published codes and **none** of the 21 published
button sequences appears in the ROM under any of the encodings tried (ASCII, UTF-16,
raw u16/u32/u64 integers, packed/unpacked BCD with all digit offsets 0..15, one byte
per digit with all offsets 0..255, all 24 button→2-bit permutations with both bit
orders, active-high/active-low key masks, GBA bit-index encodings, and XOR-masked
32-bit table scan in C). Linear, GF(2), modular and common-checksum models were also
fitted against all 48 codes and **rejected** (§5). The game therefore computes the
accepted set from an algorithm rather than storing a table of accepted strings.

**Important limitation, stated plainly:** the validator routine itself was **not
located**, so no novel code was minted and no in-game acceptance/rejection proof was
obtained. The published codes could not be entered because the Numberman machine is
**story-gated** and the Navi Customizer screen was not reached from the fresh save in
this session. Per the guide's evidence discipline (§8.4) this is reported as an
**unknown**, not as a "code confirmed" or as "no system". Everything else in this
report is reproducible from the address map and the commands in §3/§9.

---

## 3. How to reproduce

### Environment (exact)

```
export DISPLAY=:317 SDL_AUDIODRIVER=dummy
Xvfb :317 -screen 0 1024x768x24 -nolisten tcp &
DISPLAY=:317 openbox &
cd "roms/Mega Man Battle Network 5: Team Protoman"
mgba -3 "Mega Man Battle Network 5: Team Protoman.gba" &
```

Only PIDs created for :317 were used; no `pkill` was used. mGBA SDL keymap used:
A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrow keys.
Key holds of 100–300 ms; screenshots via `scrot` + `convert -crop 720x480+152+144`.

### Screen path actually walked (all with screenshots in `/tmp/mmbn5proto/`)

| # | Screen | Evidence | RAM proof |
|---|---|---|---|
| 1 | Capcom / licensed-by-Nintendo splash | `dbg_running.png` | — |
| 2 | Title ("MEGAMAN 5 BATTLE NETWORK TEAM PROTOMAN") | `gdb_title.png`, `title0.png` | savestate `state_a.ss1` |
| 3 | Title menu — **only `NEW GAME`** (no save present; Down×2 does not move) | `title_start.png`, `title_menu_down2.png` | — |
| 4 | Intro dialogue "The year was 19xx." | `ng_a_wait3.png` | — |
| 5 | Intro scene (classroom / SciLab) | `intro11.png`, `after_dlg4.png` | — |
| 6 | **Name-entry screen** (profile name, not a password field — §16.2b) | `name_entry.png` | — |
| 7 | World: Lan's room, room furniture, floor panels | `room2.png`, `on_panel.png` | — |
| 8 | PET menu: Chip Folder / Sub Chip / Library / MegaMan / E-Mail / KeyItem / Comm / Save / EXIT | `pause4.png`, `pet_all.png`, `back_pet2.png` | — |
| 9 | MEGAMAN status (HP 100/100, MegaBuster Attack/Speed/Charge LV1, Pwr Charges) | `megaman_menu.png`, `mm_3.png` | — |
| 10 | FOLDER EDIT (chip deck, 30/30 MB, Cannon/AirShot) | `sub_Comm.png`, `sub_KeyItem.png` | — |
| 11 | Outside / kitchen / town (walked; no machine reached) | `outside5.png`, `town1.png` | — |

**Screens NOT reached:** Higsby's-shop Numberman Lotto machine and the Navi Customizer
grid. Both require later story progress; repeated walking from the fresh save did not
find them. This is reported as a gate, not as absence.

### RAM evidence

Two mGBA `.ss1` savestates were captured at different PET-menu states
(`state_a.ss1`, `state_b.ss1`) and their `gbAs` zlib chunks decompressed
(`state_diff.py`): both are 397,312 bytes and **146,920 bytes differ**, spread over
VRAM (raw state 0x1000–0xC000), IWRAM (0x19000) and EWRAM (0x21000ff), confirming
observed menu/state transitions in RAM rather than only visually.

---

## 4. Address map

| Item | ROM / file address | Evidence |
|---|---|---|
| Header / entry branch | `0x08000000` / file `0x00` | observed bytes `32 00 00 ea` |
| Nintendo logo (scrambled) | file `0x04..0x9F` | observed |
| ARM crt0 | `0x080000D0` | observed disassembly |
| Header title / game code | file `0xA0` / `0xAC` | observed |
| Build stamp `REXE5TOB 20041006 US` | `0x0803DF7C` / file `0x3DF7C` | observed; xrefs at file `0x3E110`, `0x3E1DC`, `0x3E2AC` (error handlers, not a debug menu) |
| Generic u32→decimal divisor table A | `0x08000B54` / file `0xB54` | observed; single xref `0x08000B34` |
| Generic u32→decimal divisor table B | `0x08004844` / file `0x4844` | observed |
| Ascending divisor table | `0x0803F908` / file `0x3F908` | observed |
| Hex digit table `0123456789ABCDEF` | `0x080049D8` / file `0x49D8` | observed |
| Font/glyph replacement table block | `0x08057450..0x08057B00` / file `0x57450..` | observed `{u16 char,u16 attr}` records; many codes map to attr `0x0020` (space) |
| Debug printf strings (`P%02x`, `MESS %D`, `PL NUM(%D)`, `SIO ERROR`) | `0x0803072..`, `0x0803D2FB`, `0x0803EB..` | observed; **no** keyword string for any cheat system |

**No address was found for:** a Numberman password validator, a password literal
table, a button-code mask table, a prize/item table for the Lotto, or a hidden debug
menu. This is a bounded negative for the searches enumerated in §5 and §7 — not a
claim about unmapped/gated code paths.

---

## 5. Algorithm

### 5.1 Text encoding (partially decoded, per the guide's requirement)

The in-game UI is **not ASCII**. Evidence:

* `strings -t x -n 4` produced 88,019 lines; a case-insensitive keyword filter for
  `password|cheat|code|debug|secret|unlock|chip|menu|invalid|navigator|battle|modcard|
  style|bug|program` matched **0** lines.
* Ghidra's string inventory (452 strings) matched the same regex **0** times.
* Literal byte searches for the rendered strings `The year was`, `Chip Folder`,
  `Navi Cust`, `Numberman`, `PASSWORD` under strides 1–8 and byte offsets 0..stride-1
  all returned **0** hits; an offset-invariant (constant-byte-delta) search returned
  only a weak 3-byte accidental match for `Lan`.
* The font region at file `0x57450..0x57B00` stores 4-byte records of the form
  `{u16 code, u16 attr}` (e.g. `41 00 20 00` = code `0x0041` 'A', attr `0x0020`),
  with a pointer sub-table at `0x57A20`. Many punctuation codes map to attr `0x0020`,
  i.e. the glyph is replaced by a space. The actual glyph tiles are drawn from VRAM,
  so the visible text is a font/tile-index encoding, not a stored plain string.

Consequence: a `strings`-based negative would be meaningless here. The negative
results below are instead based on numeric/binary searches and on the screen walk.

### 5.2 Published-code structure — fitted and **rejected** models

Using all 48 unique published 8-digit codes (§6):

| Model tested | Result |
|---|---|
| Exact linear relation `Σ wᵢdᵢ = c` over integers (SVD null-space) | rejected — smallest singular value 1.64, non-integral null vector |
| Linear congruence `Σ wᵢdᵢ ≡ c (mod M)`, M ∈ {10,100,256,1000,10000,65536}, 200k–300k random weight trials each | rejected — no weight vector fits even a 12-code subset |
| UPC/Luhn-style weighted digit checksums (mod 10 / mod 11) | rejected — all residues 0..9 occur |
| `last2 = Σ wᵢ·first6ᵢ (mod 100)`, 200k trials | rejected |
| `last4 = first4 · K (mod 10000)`, K = 0..9999 | rejected — max fit < 4 codes |
| `code ≡ 0 (mod K)` for K = 2..101 | rejected — no common divisor (gcd of all codes = 1) |
| `code·K ≡ small (mod 2³²)`, K < 200,000 | rejected |
| GF(2) parity mask over 32-bit code bits | rank 27, null space only the 5 always-zero high bits (bits 27–31) — no bitwise checksum |
| CRC32 / Adler32 / sum-of-digits vs. code | rejected |
| Arithmetic progression / LCG modulo 10⁸ (sorted differences) | rejected — gcd of differences = 1 |

The accepted set is therefore produced by a **non-linear algorithm** (or by a table
stored in an encoded/compressed bank that none of the §7 searches reached).

### 5.3 What could not be reversed

The validator entry point was not identified. Candidate-finding techniques attempted
and their outcomes:

* Ghidra raw-ARM import at base `0x08000000`: **4,747 procedures**, 452 strings,
  default auto-analysis completed. Batch-decompiled **all** procedures and filtered
  pseudocode for a decimal-packing loop (`* 10` / `% 10` / `* 0xa` together with a
  `for`/`while`) → **0 hits**. (Ghidra's ARM/Thumb mode on a raw image is imperfect;
  this is a weak negative, not proof of absence.)
* xrefs from the build stamp and the divisor tables lead only to error handlers and
  a generic integer-formatting utility — no UI/password caller.
* The CLI debugger (`mgba -d`) works only while halted; the GDB stub (`mgba -g`)
  returned `pc=0` on connect and protocol warnings with `gdb-multiarch`, so the
  §16.19 "call the validator as an oracle" trick could not be applied without a
  candidate address.

---

## 6. Tables

### 6.1 Numberman Lotto passwords (published, 48 unique — **not** verified in ROM)

Source: 3rd party cheat indexes "Numberman codes" page (fetched 2026-11-18), cross-checked
against 3rd party cheat indexes "Lotto Codes" snippets, 3rd party cheat indexes snippets.
The `*` marker in the source denotes a code that is also found as normal game content.

| Effect | Password | Effect | Password |
|---|---|---|---|
| Anti Elec * | 35607360 | Anti Fire * | 73877466 |
| Anti Heal P | 44213168 | Anti Navi V | 05068930 |
| Anti Sword R | 10386794 | Anti Water * | 25465278 |
| Anti Wood * | 10133670 | Attack MAX (Yellow NCP) | 63231870 |
| BeatSupport NCP | 79877132 | BodyPack NCP | 30112002 |
| Bug Fix * | 50364410 | BusterPack NCP | 80246758 |
| Charge MAX (White NCP) | 87412146 | Custom 2 | 15595587 |
| Custom Bolt 3 G | 07765623 | Dark Invis * | 68799876 |
| Death Match 3 V | 52052687 | DjangoSP D | 91098051 |
| Full Energy | 12118790 | Full Energy | 90914896 |
| Gun Del Sol 3 O | 35321321 | HP +200 (Pink NCP) | 90630807 |
| HP+300 (Pink) NCP | 48785625 | HP+300 (White NCP) | 13926561 |
| HP+400 (Pink NCP) | 03419893 | HP+400 NCP | 45654128 |
| HP+50 NCP | 31084443 | HP+500 (Pink) NCP | 50906652 |
| HP+500 (White NCP) | 72846472 | Lock Enemy | 29789661 |
| Mega Folder 2 NCP | 97513648 | Megadrain | 56569865 |
| Noise Storm S | 48958798 | Quick Gauge * | 83143652 |
| Rapid MAX (Pink NCP) | 36695497 | Recovery-300 Y | 18746897 |
| RushSupport NCP | 09609807 | Shinobi Dash | 64892292 |
| SoulTime +1 (Yellow NCP) | 28256341 | SpeedMAX | 36695497 |
| Spin Blue | 12541883 | Spin Green | 78987728 |
| Spin Red | 30356451 | Static S | 48958798 |
| Steal Revenge P | 68942679 | TangoSupport NCP | 54288793 |
| Unlocker | 28706568 | Unlocker | 64664560 |
| Unlocker | 73978713 | Untrap | 00798216 |

Notes: `36695497` is listed twice (Rapid MAX Pink NCP / SpeedMAX) and `48958798`
twice (Noise Storm S / Static S) — likely aliases in the published list, not distinct
codes (§16.4b). `12118790`/`90914896` both claim "Full Energy" and three distinct
codes claim "Unlocker", so the code→effect map is not one-to-one in the source.

### 6.2 Navi Customizer compression codes (published, 21 — **not** verified in ROM)

Entered by highlighting a program, holding D-pad Right, then pressing 10 buttons from
{A,B,L,R}. Source: 3rd party cheat indexes (two independently identical lists).

```
AirShoes BLBABLBBAA        AttackMAX LLLRRBARBL     BatteryMode AABRABRLLR
BeatSupport ABBRAABRBR     BodyPack BARABRLRRA      Bugstopper BABLABRLRB
BusterPack LLRARLBLAR      ChargeMAX ALAARBRBAR     Collect BRALARBAAB
Custom+1 AARLBABALB        Custom2 BARLLRALBR       Dandyism RRBBRBRBAA
FirstBarrier RLABBARALR    FloatShoes ALLBRLAAAL    GigaFolder1 RRLBLLARBL
GigaVirus BBRALBLARR       HumourSense ABLARABLRL   KawarimiMagic RBBARBRARB
I'm Fish BABALRARAA        JungleLand LRLABLBBLA
```

One 3rd party cheat index entry (Reflect) had an empty code and is excluded. Both lists
agree on all 20 populated sequences, which is a good cross-source check.

---

## 6b. Enumeration

**Space definition (from the published input format, not from a recovered validator):**

* Numberman: alphabet `0-9`, length 8 → **10⁸ = 100,000,000** representable inputs.
  Field widths, checksum width/position and reserved bits are **unknown** because the
  validator was not recovered.
* Navi Customizer: alphabet `{A,B,L,R}`, length 10 → **4¹⁰ = 1,048,576** sequences.

**Published-set size:** 48 numeric passwords / 20 button sequences.

**Novel codes:** **none minted.** Without the validator or an accepted input there is
no decoder to invert and no oracle to confirm a generated value, so per §0.2 I do not
claim one. This is the one required deliverable that this engagement did not achieve;
it is recorded here rather than being papered over with an unverified guess.

**Bounds proven by rejection:** not obtained. No code was accepted or rejected in-game
because the entry screens are story-gated and were not reached. The rejection evidence
that *was* obtained is static: every published literal is **absent** from the image in
all encodings tried (§7), so any in-game acceptance must come from a computed algorithm
rather than a literal comparison table.

---

## 7. Validation evidence

### Observed
* Exact hashes, header bytes, entry branch, scrambled logo, build stamp (§1).
* Both ROMs boot to a playable title screen under mGBA on `:317` with `SDL_AUDIODRIVER=dummy`.
* Every screen listed in §3, with screenshots on disk.
* Savestate `gbAs` diff: 397,312-byte states, 146,920 differing bytes across VRAM/IWRAM/EWRAM.
* `strings` 88,019 lines, 0 keyword hits; Ghidra 452 strings, 0 keyword hits.

### Derived
* File-offset ↔ ROM-address mapping `0x08000000 + offset`, verified against the
  literal-pointer scan (`0x0803DF7C` found at file `0x3E110` etc.).
* Byte-level identity 32.21 % between Protoman and Colonel; both builds distinct.
* Rejection of the checksum models in §5.2 from the 48-code dataset.

### Inferred (low confidence)
* That the two cheat systems are algorithmic (strongly suggested by the total absence
  of literals plus the failed checksum fits, but not proven without the validator).
* That the missing logo/complement/checksum values indicate a rebuilt header rather
  than in-game content modification.

### Not observed / unknown
* No validator address, no flag word, no item-grant routine, no accepted or rejected
  in-game code entry, no hidden/debug menu.

---

## 8. Unknowns

1. **Validator location** — the single highest-value open item. A Ghidra/REA session
   with correct Thumb context, or a working GDB stub, plus a reached entry screen,
   should resolve it.
2. **Numberman code algorithm** — field layout, checksum, and generator remain unknown.
3. **Navi Customizer button-code encoding** — no mask/packed table found; may also be
   algorithmic.
4. **Story gate** — the exact save flag/quest step that places the Numberman machine
   and unlocks the Navi Customizer grid was not identified.
5. **Header provenance** — who rebuilt the logo/checksum bytes and whether any other
   byte outside `0x00..0xBF` was altered is unknown; the game body plays correctly.
6. **Prompt injection check** — fetched pages (3rd party cheat indexes, Brave result
   pages) contained advertising, tracking pixels and syndication boilerplate. No text
   in them instructed the analyst to run, download or send anything, and no such
   instruction was acted upon. The ROM's own strings were treated as data throughout.

---

## 9. Tooling

Scripts written for this engagement (all in `/tmp/mmbn5proto/`):

| Script | Purpose |
|---|---|
| `phase0.py`, `phase0b.py` | header parse, complement/checksum, logo scan, crt0 bytes |
| `recon.py` | `strings` keyword classification (88,019 lines) |
| `findcodes.py`, `findcodes2.py`, `xorscan.c` | literal/binary/BCD/offset/XOR-mask searches for 48 codes |
| `btnsearch.py`, `btnsearch2.py`, `btnpacked.py`, `btnidx.py` | button-code mask/packing/offset searches |
| `analyze_codes.py`, `analyze2.py`, `checksum_test.py`, `gf2.py` | checksum fitting, SVD, GF(2) null-space |
| `findpow10.py`, `findtext_rom.py`, `findtext2.py`, `findtext.py` | decimal tables and tile-encoded text searches |
| `emu.py`, `dbgd.py`, `dbg.py` | Xvfb/mGBA key control, PTY-wrapped CLI debugger |
| `parse_state.py`, `state_diff.py`, `dump.py` | savestate `gbAs` extraction and RAM diff |

External tools: `file`, `xxd`, `strings`, `grep`, `md5sum`/`sha1sum`/`sha256sum`,
`arm-none-eabi-objdump`, `mgba` (SDL + `-d` + `-g`), `gdb-multiarch`, `Xvfb :317`,
`openbox`, `xdotool`, `scrot`, ImageMagick `convert`, Python 3, GCC, and the REA MCP
Ghidra provider (Ghidra 12.1.4, raw-binary import, base `0x08000000`).
`numpy` was available; `sympy` was not installed and was not needed.

### Web sources consulted (treated as data)
* 3rd party cheat indexes — complete 48-code list.
* 3rd party cheat indexes — compression codes and hints.
* 3rd party cheat indexes — second, agreeing compression-code list.
* 3rd party cheat indexes — snippets only; direct fetches returned 403 / captcha / blocked. 3rd party cheat index cheat page and 3rd party cheat indexes have **no** Wayback snapshot under the URLs tried.
* Brave Search was the only working search backend; the built-in `websearch` tool returned no results for every query.

---

## 10. Legal note

No ROM bytes, graphics, music or game text are redistributed in this report. Only
hashes, addresses, algorithms, tool scripts and short code strings already public on
the cited cheat sites are recorded. Screenshots were used as private evidence and are
not attached.
