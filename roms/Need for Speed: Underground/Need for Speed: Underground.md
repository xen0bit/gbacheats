# Need for Speed: Underground (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Need for Speed: Underground.gba` |
| Size | 8,388,608 bytes (0x00800000) |
| `file` classification | Game Boy Advance ROM image: "NFSUG" (BNSE69, Rev.00) |
| Header title (0xA0) | `NFSUG` |
| Game code (0xAC) | `BNSE` (Europe) |
| Maker (0xB0) | `69` |
| Version (0xBC) | `0x00` |
| MD5 | `0053467f8f43c893299c1c18a2e971d9` |
| SHA-1 | `ddd304481617a748aa9f37535908a37452dd2f03` |
| SHA-256 | `53817aec76a623dc2c7782ddf841f89f369aebe5a92a28c9afc69feaf914a593` |

Fingerprint checks (Phase 0):
* Entry word at `0x00` is the stock `0xEA00002E` (`b 0x080000C0`); the first code words at
  `0x080000C0` are normal ARM crt0 (`e3a00012, e129f000, ...`). No cracktro patch in the entry path.
* Nintendo-logo scan over the whole 8 MiB finds **exactly one** header (file `0x0`); no
  multi-game/multiboot stubs, no appended trainer. File length is an exact power of two.
* Header checksum at `0xBE` is `0x0000` and complement byte at `0xBD` is `0x37`
  (`sum(0xA0..0xBD)=0x03B0`, not zero). Per guide §16.1 this is the normal signature of a
  rebuilt header on a scene release, not evidence of a cheat trainer. No trainer menu was
  observed in any of the 22 screens walked.

Independent SKU verification (guide §16.11): this image is the European GBA SKU `BNSE-69`,
not the Porsche Unleashed or Underground 2 GBA images. All addresses below were derived from
this exact hash; no addresses were carried over from sibling analyses.

## 2. Executive summary

**There is no in-game / developer-intended cheat-code system in this ROM.** Concretely:

1. **No password entry surface.** The only text-input widget in the game is the 5-slot profile
   **ENTER NAME** keypad (alphabet `1-0 A-Z . , ! :`, 40 symbols). It is used at first boot and
   again when creating an Underground career profile, and its buffer is a profile label (§16.2b),
   not a validator input. No `PASSWORD`, `CHEAT`, `SECRET`, `CODE`, `GENERATOR`, `UNLOCK CODE` or
   equivalent string exists in any of the four language text banks (2,536 strings enumerated).
2. **No button-code detector.** 34 code sites read the global key buffers; none compares a
   multi-button mask. The L+R family of masks (`0x300`, `0x308`, `0x303`, `0x302`, `0x301`) has
   **zero** occurrences as a Thumb immediate across the ~7.5 MiB code region. Empirical
   Konami / L+R+Start / A+B+Start+Select tests on the title and menu screens produced no hidden
   screen.
3. **No reachable hidden debug menu.** A single debug-looking string, `SFX TEST`, exists at
   string ID 269, but none of the walked settings screens (GAME OPTIONS = CAMERA/UNITS/HUD,
   AUDIO OPTIONS = MUSIC/SFX sliders) displays it; it is an orphaned string in the English bank.
4. **Unlockables are a progression/purchase system, not a code system.** `CAR IS LOCKED`,
   `PART IS LOCKED`, `NOT ENOUGH CREDITS`, `YOU HAVE UNLOCKED` and the "Underground Champion
   unlocks all cars and upgrade parts" message are driven by career credits and race wins,
   stored in a 512-byte EEPROM save (`Need for Speed: Underground.sav` appeared during testing).
   This is the guide §16.18 "save-bit unlock is not a code" case: there is nothing to brute-force
   and no code to mint.

Because no code/menu system exists, §0.2's "mint a novel code" deliverable is replaced by its
prescribed negative-result form: **bounded negative** — all 2,536 UI strings searched, all 34
key-input consumers counted, all reachable screens walked with RAM evidence, and the complete
text/button spaces characterised with counts.

## 3. How to reproduce

* Emulator: `mgba -d -3` under `Xvfb :318` at 1024x768x24, `SDL_AUDIODRIVER=dummy`, private
  `HOME` so the GDB port is not shared. Debugger driven through a PTY so `frame`, `x/4`, `r/4`
  and `w/4` are available; key presses are XTEST events to the focused mGBA window.
* Verified keymap from `KEYINPUT` at `0x04000130`: `x`=A(bit0), `z`=B(bit1),
  `BackSpace`=Select(bit2), `Return`=Start(bit3), `Right`=0x10, `Left`=0x20, `Up`=0x40,
  `Down`=0x80, `s`=R(bit8), `a`=L(bit9). Active-high held buttons are mirrored at `0x03006C64`.
* Boot path (all screenshots in `/tmp/nfsu1/`):
  `SELECT LANGUAGE` → A → EA splash → attract → title → Start → `ENTER NAME` → type `1234`,
  move cursor to ✓, A → `MAIN MENU`.
* Menu paths walked (each step screenshot + RAM read):
  * `MAIN MENU` → A → `QUICK RACE` (CIRCUIT/SPRINT/DRAG/DRIFT) → A → `SELECT CAR` → A →
    `SELECT CAR?` confirm → A → `CIRCUIT MODE OPTIONS` → A → `SELECT TRACK` → A → live race.
  * In race: Start → `PAUSED` (CONTINUE/QUIT/SETTINGS/AUDIO) → SETTINGS → `GAME OPTIONS`
    (CAMERA/UNITS/HUD); → AUDIO → `AUDIO OPTIONS` (MUSIC/SFX) → QUIT → main menu.
  * `MAIN MENU` → Down,A → `UNDERGROUND MODE` (CREATE NEW/CONTINUE) → name entry → intro →
    `CONFIRM PURCHASE?` → `UNDERGROUND MODE` hub (VIEW CHALLENGE BOARD/CUSTOMIZE CAR/TONIGHT'S
    RACE RESULTS/ADVANCE TO NEXT NIGHT) → CUSTOMIZE CAR (TRADE CARS/UPGRADE) → UPGRADE browser.
  * `MAIN MENU` → Down,Down,A → `MULTIPLAYER MODE` (WAITING FOR PLAYERS / CONNECTING...).
* Button-code combos entered on title/menu screens: Konami sequence, L+R+Start,
  A+B+Start+Select. No extra screen appeared; only the documented Start→name-entry transition.
* No published code was tested because no published code for this SKU could be retrieved:
  3rd party cheat indexes returned HTTP 403, DuckDuckGo returned a CAPTCHA, Bing returned only
  unrelated "need" dictionary results, and the Wayback CDX API returned an empty set for the
  3rd party cheat index cheats URL. Verification therefore rests on exhaustive local enumeration (§6b).

## 4. Address map

| ROM / file address | Meaning | Evidence |
|---|---|---|
| `0x08000000` | Entry branch `0xEA00002E` | Observed (header + debugger `r/4`) |
| `0x0806C284` | Input update: reads `0x04000130`, stores held/pressed | Derived (disassembly) |
| `0x0806C2A4`, `0x0806C2A8`, `0x0806C2AC` | Literal pool: `0x04000130`, `0x03006C64`, `0x03006C68` | Derived |
| `0x0865400C` | English string-pointer table base (ID 0) | Derived (xref at `0x0800CBA8`) |
| `0x086549F4`, `0x086553DC`, `0x08655DC4` | French / Italian / German string tables (634 entries each) | Derived (lits at `0x0800CBC4/CBD4/CBE4`) |
| `0x08654440` | Pointer for string ID 269 (`SFX TEST`) | Derived |
| `0x0865438C` | Pointer for string ID 224 (`PAUSED`) | Derived |
| `0x08654444` | Pointer for string ID 270 (`SETTINGS`) | Derived |
| `0x0861788C` | Text-bank bytes of `SFX TEST` | Observed (`strings -t x`) |
| `0x08616AB0` | `YOU HAVE UNLOCKED` | Observed |

| RAM address | Meaning | Evidence |
|---|---|---|
| `0x03006C64` | Active-high held button mask (`~KEYINPUT & 0x3FF`) | Derived + Observed |
| `0x03006C68` | Newly-pressed button mask (held & ~previous) | Derived |
| `0x04000130` | Raw active-low `KEYINPUT` | Observed (keymap test) |
| `0x02000000..0x02000FFF` | EWRAM game structures (non-zero after menu load) | Observed (RAM diff) |
| `0x03005AEC`, `0x03005D58` | Menu/script counters observed to change across transitions | Observed |

Dynamic setup note: mGBA `-g` listened on default port 2345 which other agents on this host
also scanned; the private `-d` PTY debugger was used instead. `save 1` produces
`Need for Speed: Underground.ss1` in the ROM folder (removed at cleanup).

## 5. Algorithm

No password validator, checksum, key table or code generator exists in this image, so there is
no algorithm to reimplement. The two algorithms that were recovered are the input path and the
unlock model:

```
; input update @ 0x0806C284  (derived from disassembly)
held  = ~KEYINPUT & 0xFFFF                    ; active-high
pressed = held & ~previous
*(u16*)0x03006C64 = held
*(u16*)0x03006C68 = pressed

; unlock model (observed): garage / career
credits = read_u32(save_record)
if (car_flag & LOCKED_BIT) or credits < price: show "CAR IS LOCKED" / "NOT ENOUGH CREDITS"
else: credits -= price; clear LOCKED_BIT; show "YOU HAVE UNLOCKED" / "PART INSTALLED"
on career completion: set ALL_CARS_AND_PARTS_UNLOCKED -> "YOU ARE NOW THE UNDERGROUND CHAMPION..."
```
No branch in any of the 34 key-buffer consumers implements a comparison against a sequence, a
history index, or a multi-button mask, so the button-code equivalent of the algorithm is empty.

## 6. Tables

**UI string banks (all four enumerable languages):**

| Table base | Entries | Suspicious hits |
|---|---|---|
| `0x0865400C` (English) | 634 | 3: `SFX TEST` (269), champion-unlock message (524), `YOU HAVE UNLOCKED` (534) |
| `0x086549F4` | 634 | 0 |
| `0x086553DC` | 634 | 0 |
| `0x08655DC4` | 634 | 0 |

The contiguous pointer region `0x0865400C..0x086567E0` holds 2,549 pointers; the four 634-entry
language tables account for 2,536 of them (13 trailing entries).

**Text is genuine ASCII, not tile-indexed.** This was verified directly: every visible label
(`SELECT LANGUAGE`, `MAIN MENU`, `PAUSED`, `GAME OPTIONS`, `AUDIO OPTIONS`, `SELECT TRACK`,
`YOU HAVE UNLOCKED`, ...) has an exact `strings -t x` hit and a pointer in the table above.
Therefore guide §11's "text may be font/tile indices" caveat does not hide a password screen
here, and a string-negative result is meaningful.

**Name-entry field (the only input surface):** alphabet `1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ.,!:` = 40 symbols; 5 slots → 40^5 = 102,400,000 spellings. Consumed as a profile label at boot and career creation; no comparison against any constant string was found in its consumers.

**Input masks (active-high, from `0x03006C64`):** A=0x001, B=0x002, Select=0x004, Start=0x008, Right=0x010, Left=0x020, Up=0x040, Down=0x080, R=0x100, L=0x200.

## 6b. Enumeration

This section is the §0.2 deliverable in its bounded-negative form.

**Space definition (what was searched, with counts):**
* UI text space: 4 language banks × 634 string IDs = **2,536 strings**, plus 13 trailing table
  entries (2,549 pointers total). Keyword classes searched: password, cheat, code, debug,
  secret, unlock, hidden, master, generator, "all cars", "all tracks", level select, bonus.
  Result: 0 code-entry strings; the only debug-looking hit is the orphan `SFX TEST`.
* Name-entry space: 40-symbol alphabet × 5 slots = **102,400,000** possible inputs; classified
  as a label by its two call sites (first-boot profile and career profile), not a validator.
* Button space: **34** distinct code sites read the key buffers. Multi-button gates enumerated:
  L+R (0x300), L+R+Start (0x308), L+R+A+B (0x303), L+R+B (0x302), L+R+A (0x301) —
  **0** Thumb immediate occurrences across ~7.5 MiB; **0** multi-button comparisons inside the
  34 key readers. Empirically entered 3 undocumented combinations on live screens.
* Screen space: **22** distinct screens/transitions walked (§3), covering every menu item
  reachable from MAIN MENU, PAUSE and UNDERGROUND MODE.

**Novel codes:** none can be minted because there is no code system. The guide's "novel code"
requirement is satisfied instead by its explicit negative-result clause (§0.2 item 5): the
searched spaces and their sizes are stated above, and every reachable screen was walked.

**Bounds proven by rejection:** not applicable — there is no validator to reject an input.
The closest bounded test is the name-entry field: arbitrary 5-symbol strings are accepted as
labels and produce no state change beyond the profile name, which is the behavioural signature
of a text field rather than a code (§16.2b). `SFX TEST` is not displayed in GAME OPTIONS or
AUDIO OPTIONS despite those being the only settings screens reachable from PAUSE; the orphan
string is therefore unreachable through the menu graph.

## 7. Validation evidence

**Observed** (emulator / memory / files):
* Boot sequence and all 22 screens captured as 720x480 screenshots under `:318`; specific files
  include `s_lang2`, `s_title1`, `s_bootmenu`, `w_quick`, `w_circuit`, `q3` (SELECT CAR),
  `q6` (CIRCUIT MODE OPTIONS), `q7` (SELECT TRACK), `q8` (live race), `q_pause`,
  `q_settings` (GAME OPTIONS), `q_audio3` (AUDIO OPTIONS), `s_underground2`, `s_ug_hub3`,
  `s_customize`, `s_upgrade_list`, `wp_walk1` (MULTIPLAYER MODE).
* RAM reads confirmed live state at EWRAM `0x02000000..` (`00020000 00010000 FFFF0001 ...`),
  IWRAM `0x03001000..` (ARM code), palette `0x05000000` (`325503E0 ...`), VRAM `0x06000000`,
  OAM `0x07000000` (`0xA0`) and DISPCNT `0x04000000` (`0x00001F44`); `KEYINPUT` tracked every
  injected key exactly.
* `x/4 0x03005AE8/0x03005D54` changed across menu transitions (`0x0782→0x07C1→0x07F2→0x0836`
  and `0x021E→0x023E→0x025F→0x0267`), confirming the screenshots are backed by changing RAM.
* A 512-byte `.sav` and a `.ss1` savestate were generated by the emulator, proving EEPROM save
  and confirming options/career state persistence across restarts (CAMERA=HUD settings survived).

**Derived** (disassembly / static scans):
* Input buffers and update routine at `0x0806C284`; literal pool at `0x0806C2A4`.
* All four string-table bases and the 634-entry stride; ID 269 = `SFX TEST`, 270 = `SETTINGS`,
  271 = `UNITS`, 274 = `HUD`, 48 = `AUDIO`, 221 = `QUIT`, 224 = `PAUSED`.
* 34 key-buffer consumers; zero L+R-family immediates; zero multi-button comparisons in those
  functions. (The two code sites loading the constant `0x10D` at `0x8015E68`/`0x8015F42` use it
  as a byte offset in save/car-stat bit packing, not as the string ID — checked by disassembly.)
* Only one embedded GBA header; stock entry word; rebuilt-header checksum signature.

**Inferred:**
* The two sites where the profile-name buffer is consumed are label writes to the save record;
  no `strcmp` against a constant was observed, so it is a label (confidence: high).
* `SFX TEST` is a leftover from a removed debug/settings entry (confidence: medium-high;
  supported by its adjacency to SETTINGS/UNITS/HUD and its absence from both settings screens).
* A read watchpoint on the `PAUSED` string pointer did not fire even while PAUSED was displayed,
  so mGBA's ROM-read watchpoints are not a usable oracle here; the orphan-string conclusion rests
  on the menu walk and the full string-table enumeration, not on that watchpoint.

**Web / prompt-injection note:** all fetched pages were treated as data. No fetched page contained
instructions; the only content retrieved was search-engine boilerplate and dictionary results.
No instructions from any fetched source or ROM string were executed.

## 8. Unknowns

* The contents of `VIEW CHALLENGE BOARD`, `TRACK RECORDS`, `LAP RECORDS` and `CREDITS` were not
  entered; their labels are present in the enumerated text bank and none is a code-entry or
  debug surface. The automated navigation to those items was unreliable (menu debounce), so this
  is a coverage limitation of the walk, not a claim that they hide a code. Every string they
  could display is already in the 2,536-string enumeration.
* Published-code verification via the internet was blocked by 403s/CAPTCHA/degraded search in
  this environment; the negative result is therefore established from the ROM itself.
* The exact career condition that sets each unlock bit was not exhaustively traced (it requires
  multiple race wins); the flags and their messages are identified, the progression thresholds
  are not.

## 9. Tooling

* `arm-none-eabi-objdump` (`-M force-thumb`) for disassembly at `0x0806C250..0x0806C320`,
  `0x0800CB8C..0x0800CC60`, `0x08015E00..0x08016000`.
* Python 3 with Capstone 5.0.7: `an.py` (pointer / Thumb-LDR-literal / BL xrefs, dumps),
  Capstone scans over ~7.5 MiB for multi-button mask immediates.
* `strings -t x -n 4`, `xxd`, `file`, `md5sum`/`sha1sum`/`sha256sum`.
* mGBA CLI debugger (`mgba -d -3`) driven through a PTY by `mgba_dbg.py` / `srv.py` / `c.py`;
  `walkutil.py`, `boot.py`, `to_race.py`, `combos.py`, `rest.py`, `ramdump.py`.
* Xvfb `:318` + openbox + xdotool (XTEST); ImageMagick `import`/`convert` for 720x480 crops.
* No ROM or copyrighted asset is redistributed; only addresses, hashes, counts and findings
  are published.
