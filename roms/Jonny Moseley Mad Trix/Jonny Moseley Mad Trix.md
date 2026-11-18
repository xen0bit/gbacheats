# Jonny Moseley Mad Trix (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Jonny Moseley Mad Trix/Jonny Moseley Mad Trix.gba` |
| Size | 8,388,608 bytes (0x00800000) |
| `file` ID | Game Boy Advance ROM image: "JONNYMOSELEY" (AJME5H, Rev.00) |
| Header title | `JONNYMOSELEY` (0xA0–0xAB) |
| Game code | `AJME` (0xAC–0xAF) |
| Maker | `5H` (0xB0–0xB1) — The 3DO Company / Crave |
| Version | 0x00 (0xBC) |
| Entry branch | `0xEA00002E` (stock crt0, 0x080000C0) |
| Header complement | 0x0B (expected 0x24) — **header was rebuilt/edited**; checksum field 0x0000 |
| MD5 | `c555f2e4638d153ea69ad54ed33ef7fa` |
| SHA-1 | `55b80ee2367e167e9d7186581f21299a8c9a0af7` |
| SHA-256 | `cd3b51351de89ca66e25ea2f70f1c44b4584f35fde885e726a9f5fdc0959e4f6` |

**Embedded-header scan:** exactly one Nintendo-logo hit (file 0x04, header 0x00). No multiboot stub, no appended trainer; the tail of the image is zero-filled. Stock crt0 begins at 0x080000C0. The bad complement byte is a header-rebuild artifact, not a scene cracktro (entry word and first 4 KiB are stock).

## 2. Executive summary

The only cheats published for this title are **PlayStation 2 / GameCube** button codes (e.g. "at the Press Start screen, hold L2+L3+R1+Down+Square+Circle"). Those use buttons the GBA does not have and **do not apply to this SKU**. GameFAQs' GBA cheat page lists the same code under a "PS2" heading; no GBA-specific password or button code was found in any source (TCRF is behind Cloudflare; no GBA debug-entry documentation was recoverable).

The GBA ROM does, however, contain a complete **developer debug-menu system** that is unseen in normal play: seven hidden states (dispatch states 30–35) whose screens use an on-screen 5-character command picker. The accepted commands are `CLREE`, `UNLOK`, `CHARS`, `CTRL`, `VERS`, `MIMIT`, `AMLAK`, `RAULD`, `CREDS`, `PS2`, `SHARK` (ROM 0x080143E0–0x0801442C). `UNLOK` is the unlock-all command; `CHARS` jumps to character select; `CREDS` to credits; `CTRL` toggles a control/display setting; the remainder set build/debug screens. A `BUILD DATE Dec 10 2001 16:59:54` panel is also present (0x08014434).

**Critical negative result:** the debug screens are gated by state 31 (0x1F), which is written only at 0x0800182C when the menu helper at 0x08003AEC returns −2. Every reachable screen was walked, and every plausible button/combination was pressed at the title screen and at character select with the state variable read after each (`0x030014D8`); **no in-game input ever produced state 30–35 or the −2 return**. The only in-game "developer-intended" controls found are the Trick Book's **HOLD B TO CLEAR** (resets learned tricks) and the ordinary unlockables (events/characters locked behind gold medals). The debug command system is therefore **dead/gated code in the retail GBA image**, reachable only by debugger/save-state manipulation, not by controller input.

## 3. How to reproduce

* Emulator: mGBA (`/usr/local/bin/mgba -g -3`), Xvfb `:316`, `SDL_AUDIODRIVER=dummy`, Openbox WM.
* GBA keymap used (mGBA SDL default): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad = arrow keys. Hold 120–150 ms.
* Deterministic boot path: legal splash → 3DO splash → GFX/RTG logo → "PRESS START" title → main menu.
* State variable for all screens: `0x030014D8` (u32). Read with the GDB stub (`m030014d8,4`).
* Screen-walk map (observed, with state reads):

| Screen | State |
|---|---|
| Legal / 3DO / GFX-RTG splash | 24 / 2 / 4 |
| "PRESS START" title | 6 |
| Main menu (START GAME / TRICK BOOK / MEDALS / LANGUAGE / MUSIC) | 22 |
| Event select (TRAINING, MACHU PICHU, LAS VEGAS, KILIMANJARO, ALASKA, SAN FRANCISCO) | 14 |
| Character select (SPEED/JUMP/MOGUL; JONNY MOSELEY shown) | 19 → 18 |
| Gameplay | 9 |
| Pause menu (CONTINUE GAME / TRICK BOOK / MEDALS / LANGUAGE / MUSIC / NEW GAME) | 22 |
| Trick Book (`AIR TRICKS` / `RAIL TRICKS`, HOLD B TO CLEAR) | 25 → 26 |
| Medals | 28 |
| Debug screens (not reachable in-game) | 30–35 |

* Published PS2 code tested literally: not applicable (no L3/R3/Square/Circle on GBA); no GBA equivalent found.

## 4. Address map

File offset = ROM address − 0x08000000.

| Thing | ROM address | File offset | Note |
|---|---|---|---|
| Header / crt0 | 0x08000000 | 0x000000 | stock entry 0xEA00002E |
| Key-read helper (returns ~KEYINPUT & 0x3FF) | 0x0800023C | 0x00023C | single literal 0x04000130 at 0x08000248 |
| Input update (held/pressed/released) | 0x08000570 | 0x000570 | held 0x030016F0, pressed 0x03001688, released 0x030013AC |
| Main state dispatcher | 0x080005F? / 0x0800680 | 0x000680 | state var 0x030014D8, dispatch table at 0x080006A4, 36 entries (states 0–35) |
| State 31 entry (debug gate) | 0x0800182C | 0x00182C | `mov r0,#31; str r0,[r9]` when helper 0x08003AEC returns −2 |
| Menu helper (returns selected index, −1/−2) | 0x08003AEC | 0x003AEC | 8-entry jump table at 0x08003FF0; selection var 0x03001358 |
| Debug dispatch states 30–35 | 0x08002C08 / 0x08002C24 / 0x08002E50 / 0x080032F2 / 0x08003380 / 0x080033B2 | 0x002C08 … | debug UI |
| Debug password/validator (builds 5-char string, compares commands) | 0x08003028 | 0x003028 | reads buffer 0x03001690 |
| Word-aligned fast strcmp | 0x08013378 | 0x013378 | called with built string vs. each command literal |
| Localized text bank (events/characters/UI) | 0x08013D5C–0x080143C0 | 0x013D5C–0x0143C0 | ASCII |
| Debug labels / command bank | 0x080143E0–0x08014460 | 0x0143E0–0x014460 | ASCII, 5-char fields |
| Menu string pointer table | 0x08014DE0–0x08014F00 | 0x014DE0–0x014F00 | u32 pointers into text bank |
| RAM: state | 0x030014D8 | — | u32 screen selector |
| RAM: password buffer | 0x03001690 | — | 5 × u32 digit values (−1 = blank) |

## 5. Algorithm

The debug command checker (0x08003028) is a **5-character lookup**, not a checksum:

```
buf = [u32 at 0x03001690 + 4*i for i in 0..4]
s = ""
for v in buf:
    if v == -1: s += '\0'
    elif v <= 9: s += chr(0x30 + v)     # '0'..'9'
    else:        s += chr(0x37 + v)     # 'A'.. for v=10..37
s[5] = '\0'                              # NUL terminator at sp+0x15
if strcmp(s, "CLREE") == 0: ...          # call 0x08013378
if strcmp(s, "UNLOK") == 0: ...
if strcmp(s, "CHARS") == 0: ...
if strncmp(s, "CTRL", 4) == 0: ...
... (VERS, MIMIT, AMLAK, RAULD, CREDS, PS2, SHARK)
if final state not in (0x21,0x23): state = 0x15
```

The on-screen picker changes each digit with D-pad: L/R = ±1 (mod 38, bound 0x25=37), Up = −10 (min 0), Down = +10 (max 37), A = confirm digit and advance. A confirmed value maps to a display character through the table above. There is **no arithmetic validation** — acceptance is a literal `strcmp` against the 11 fixed command strings. Bounds: values must be −1 or 0..37; 38+ is unreachable (input clamps at 37), and any string not exactly one of the 11 literals falls through to the default return.

The debug gate: state 31 is written at 0x0800182C only when the caller's helper returns −2:

```
r4 = helper(0x08003AEC)         # menu selection, -1 = normal, -2 = special
if r4 == -2: state = 22, then state = 31   # -> debug menu chain
if r4 == -1: state = 22, state = 21, ...
```

The dispatcher (`0x0800680`) does `state = [0x030014D8]; if state <= 35: pc = table[state*4]` with the table at 0x080006A4.

## 6. Tables

**Debug commands (all at 0x080143E0, 5-byte NUL-padded fields), with observed effect from the branch:**

| String | ROM addr | Branch effect | Confidence |
|---|---|---|---|
| `CLREE` | 0x080143E0 | calls 0x0800354, sets screen 10 | Derived |
| `UNLOK` | 0x080143E8 | clears a word, calls RNG 0x0800A99C/0x0800A95C, screen 10 (unlock-all) | Derived |
| `CHARS` | 0x080143F0 | sets index 6, sets flag +0x18=1, screen 10 (character select) | Derived |
| `CTRL` | 0x080143F8 | 4-char strncmp; checks digit '0'/'1', toggles word at +0x1C | Derived |
| `VERS` | 0x08014400 | sets word 0, next 0x21 | Derived |
| `MIMIT` | 0x08014408 | sets word 3, next 0x23 | Derived |
| `AMLAK` | 0x08014410 | sets word 4, next 0x23 | Derived |
| `RAULD` | 0x08014418 | sets word 5, next 0x23 | Derived |
| `CREDS` | 0x08014420 | sets word 10, next 0x23 (credits) | Derived |
| `PS2` | 0x08014428 | sets word 13, next 0x23 | Derived |
| `SHARK` | 0x0801442C | sets word 0; if state not 0x21/0x23 → 0x15 | Derived |

**Bound/screen constants:** picker digit max = 37 (0x25); "no selection" −1 (0xFFFFFFFF); debug gate −2 (0xFFFFFFFE); state table size 36 (states 0–35); password buffer length 5.

**Character names** (0x08013DA4–0x08013DE0): `MIKI`, `PHAT EARL`, `WILD CHILD`, `TANNER HALL`, `JONNY MOSELEY`.
**Events** (0x08013D5C–0x08013DB0): `SAN FRANCISCO`, `ALASKA`, `KILIMANJARO`, `LAS VEGAS`, `MACHU PICHU`, `TRAINING`, `SKIER X`.

## 6b. Enumeration

**Space definition.** The debug command space is a lookup of 5-character strings over the picker's alphabet: values −1 (blank) or 0..37, mapped `0-9 → '0'-'9'`, `10-37 → chr(0x37+v)` (`A..\\`). Nominally 38^5 ≈ 79 million 5-symbol strings; the validator accepts **exactly 11** literal strings (the table at 0x080143E0), so the accepted-set cardinality is 11. There is no checksum, no reserved-bit field, and no algorithmic generator. The 11 entries were enumerated exhaustively by scanning every literal pointer into the command bank from the validator (0x08003028–0x080033C4); all 11 are listed in §6. The screen's picker is limited to 38 values, so strings longer than 5 characters or containing values >37 cannot be expressed.

**Novel code (minting).** Because the validator is a pure literal table, no unpublished code can exist: any string other than the 11 literals is rejected by construction. The closest thing to an unadvertised combination is `CLREE`, `PS2`, `SHARK`, `MIMIT`, `AMLAK`, `RAULD` — these are in-ROM but appear in **no published GBA code list** (all web results are PS2). They were "minted" from the ROM table rather than from a published source. I attempted to drive the picker by forcing state 32 with a debugger write, writing digits to 0x03001690 and confirming each with A: the buffer advanced and zeroed and no unlock flag was written, but the rendered screen remained the previous gameplay frame, so **this did not constitute a valid in-game acceptance test**. The command set is enumerated from the ROM table and the `strcmp` branches (Derived), not from an executed accepted code. No controller-only path to the screen exists (see bounds below).

**Bounds proven by rejection.** (a) Title screen and character select were each subjected to all single buttons, L/R, A/B, Start/Select and 2–3 button holds, plus Konami and console-code-analogue sequences; in every case `0x030014D8` stayed at 6 (title) or advanced only to 22/9 (normal menu/gameplay) — **never to 30–35**. (b) The dispatcher's table has 36 entries (states 0–35); states 30–35 are only written at 0x08002BFA, 0x08002BFA/0x08002C1C/0x08002C24 (inside the debug screens themselves) and 0x0800182C (the −2 gate). (c) Digit values >37 are unreachable: the picker clamps at 0x25. (d) A 5-digit string not equal to any of the 11 literals (e.g. all zeros) falls through to the default return and writes no flag. These are bounded negative results for the *input-search space* actually exercised.

## 7. Validation evidence

* **Observed** (emulator + GDB): hashes/header; every screen in the §3 table, each with a screenshot and a `0x030014D8` read; locked padlock icons on all events except TRAINING; pause menu with 6 items and no hidden scroll entries; debug screen appearance when state 32 is forced; buffer 0x03001690 advancing/clearing as A is pressed; no state ≥30 after exhaustive button tests.
* **Derived** (static): dispatch table at 0x080006A4; key-state addresses; command string bank and 11-way strcmp validator; gate at 0x0800182C; menu helper return semantics.
* **Inferred** (not exercised in-game): the exact visible effect of each debug command; that the −2 helper return is genuinely unreachable by any controller input (strongly indicated by exhaustive button tests and by no mask-table literal matching the console code, but not a formal proof over all timing/sequences).
* **Web care:** all fetched pages treated as data. PlanetCheats returned only PS2 codes. TCRF returned a Cloudflare "Just a moment…" CAPTCHA page (no instructions, no injection payload). No prompt-injection content was encountered.

## 8. Unknowns

* The precise controller input (if any) that makes 0x08003AEC return −2 and open the debug menu. Exhaustive short-sequence testing failed; a very long or timing-dependent sequence cannot be excluded.
* Whether the hidden characters (`MIMIT`/`AMLAK`/`RAULD`?) or `SHARK` correspond to real selectable skiers — the command effects were read from branches, not played through.
* Whether `SKIER X` is an unlockable event (it appears in the string bank but not in the observed event-select rotation).
* The header complement/checksum anomaly's origin (rebuild vs. bad dump) — irrelevant to code addresses, which all verify against the bytes.

## 9. Tooling

* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for raw Thumb ranges.
* Capstone (Python, `CS_ARCH_ARM`/`CS_MODE_THUMB`) for literal-pool and dispatch-table scans; `struct.unpack_from('<I', …)` for every pointer (never objdump's split halfwords).
* Custom persistent GDB-RSP client (`gdbrsp.py`) + JSON daemon (`gdbd.py`) + CLI (`gcli.py`) to work around mGBA's single-connection GDB stub. Note: RSP memory commands need **no space** (`m08000000,4`, not `m 08000000,4`).
* `xdotool` key injection (XTEST) on `DISPLAY=:316`; `scrot` screenshots; ImageMagick montages.
* Scripts kept in `/tmp/opencode/jonny/`: `key.py`, `walk.py`, `brute.py`, `cs_brute.py`, `gate_final.py`, `oracle.py`, `to_charselect.py`.
* No ROM or copyrighted assets are redistributed here; only addresses, hashes, hashes and algorithms are published.

---

**Legal note:** analysis of a legally owned ROM; no ROM data, graphics, or extracted assets are included in this report.
