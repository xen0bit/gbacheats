# Golden Nugget Casino (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Golden Nugget Casino.gba` |
| Size | 4,194,304 bytes (0x400000) |
| Header title | `GOLDENNUGGET` |
| Game code | `BGGE` (`BGGE5G` in `file(1)` output — maker `5G`) |
| Maker | `5G` |
| Version | 0x00 |
| Entry branch | `0xEA00002E` (stock GBA crt0) |
| Fixed 0x96 / main unit / device | 0x96 / 0x00 / 0x00 |
| Complement byte | 0x3D; header checksum 0x0000 |
| MD5 | `4df2176d0f881b309b9077d18a422f00` |
| SHA-1 | `5ecf4ead4b22a5916086a34bbf2abf299aaf3401` |
| SHA-256 | `36f59efde2cd887d80c4eba5a0fff6fa7f0d744a87a4b9c3a8adeea63ae218e8` |

Phase 0 result: **one** embedded GBA header (Nintendo-logo scan over the whole 4 MiB finds only offset 0). The entry word is the stock `b 0x080000C0`; no appended trainer, cracktro, or second image. Publisher splash on boot is Majesco (`www.majescoaudio.com` / `majesco` logo); audio engine banner `Shin'en Multimedia. Code: B.Wodok` at 0x3D0587 is the usual GAX copyright string, not a cheat.

Note on the hash: because header checksum 0x0000 and the unusual complement byte are normal for a rebuilt/patched header, the boot code and first 4 KiB were checked directly — they are a clean, unmodified crt0. No evidence of a patch/trainer.

## 2. Executive summary

The game has a **developer-intended password system**, reachable from the main casino lobby via the **PASSWORD** tile. It is a 13-symbol code drawn from a **64-character alphabet** formed by concatenating two 32-byte tables:

* 0x08080FBD — display alphabet `bcdfghjklmnpqrstvwxyz<=>?%/+#@-&`
* 0x08080FE2 — input alphabet  `BCDFGHJKLMNPQRSTVWXYZ0123456789!`

Each symbol carries **6 bits**; 12 symbols are payload and the 13th is a 6-bit checksum. The payload is laid out as:

| Field | Symbols | Bits | Meaning (high confidence for `credits`, nominal for the rest) |
|---|---:|---:|---|
| credits | 0–3 | 24 (LE) | player cash, global at 0x03004030 |
| f2 | 4–6 | 18 (LE) | secondary progress value (default 10000) |
| f3 | 7–9 | 18 (LE) | secondary progress value (default 0) |
| f4 | 10 | 6, stored complemented | small counter (default 46) |
| f5 | 11 | 6, stored complemented | small counter (default 0) |
| checksum | 12 | 6 | `(- (f4 + X + f5)) & 63` where `X = sum(first 12 values) & 63` |

The generator at **0x08011EC** builds the displayed password from the live globals; the validator lives in the same large password-screen function, with its checksum gate at **0x0801A76** and accept path at **0x0801A54–0x0801A8E**, which writes the decoded fields to 0x03004030 / 0x0300404C / 0x0300516C.

The generator was reimplemented bit-for-bit in `pwcoder.py` and reproduces **both** observed in-game codes exactly. A novel code was minted, injected into the live input buffer, submitted with the real in-game OK button, and RAM-verified:

* `!lZfv#dbbbxbz` → credits 0x03004030 = **0x000F423F = 999999** (screenshots `novel2_result.png`, `novel2_menu.png`).
* `!!!!v#dbbbxb=` → credits = **0x00FFFFFF = 16777215**, proving the 24-bit field bound.
* Bad checksum (`!lZfv#dbbbxbb`) and out-of-alphabet character (`A` in slot 0) were both **rejected** — credits remained unchanged.

No button-code table, debug menu, or hidden screen was found. Web research for published codes produced no usable source (see §8).

## 3. How to reproduce

### Emulator / display
```
Xvfb :317 -screen 0 1024x768x24 &        # PID tracked; own display only
DISPLAY=:317 openbox &
DISPLAY=:317 SDL_AUDIODRIVER=dummy mgba -g -3 <rom> &
```
mGBA 0.10.5 SDL. Keymap: A=`x`, B=`z`, Start=`Return`, Select=`BackSpace`, arrows = D-pad, L=`a`, R=`s`. The title screen ignores input until roughly 8–9 s have elapsed; the scrolling legal/credits screens take ~10 `Return` presses to skip.

### Menu path to PASSWORD
`Return` ×10 (legal scroll) → wait ~9 s → `Return` (title) → `x` (accept `Player` on sign-in) → main lobby → select the **PASSWORD** tile and press `A`.

The lobby is a 6-item ring (BLACKJACK, CASHIER, SLOT MACHINES, TABLE GAMES, PASSWORD, VIDEO POKER). Depending on the stored cursor, a short arrow sequence followed by `A` lands on PASSWORD; once the cursor is on PASSWORD it stays there across `B`/re-entry. For fully deterministic access, set the menu-selection counter at 0x03003770 to 4 and press `A` (the handler maps index 4 → password screen state 6).

### Code test (exact, reproducible)
The on-screen keyboard is slow to drive, so the mGBA GDB stub (single persistent connection on port 2345, held open by `gdb_server.py`) is used to place the code in the game's **live 13-byte input buffer** at 0x03005230; submission then uses the real in-game OK button:

```
# at the PASSWORD screen
write 0x03005230 216c5a6676236462626278627a   # "!lZfv#dbbbxbz"
# press A (xdotool key x) with the cursor on OK
read 0x03004030 4        # -> 3f 42 0f 00  (999999)
```

Rejection controls use the same procedure with a modified last byte (`...62786262` = bad checksum) or `41` in byte 0 (`A`, outside both alphabets).

### Scripts
`pwcoder.py` (encoder/decoder), `gdb_server.py` (persistent GDB-stub bridge), `g.py` / `snap.py` (command + screenshot/RAM helpers), `scan.py` (pointer / literal-pool scanner). All under `/tmp/goldennugget/`.

## 4. Address map

### ROM (file offset = ROM address − 0x08000000)

| Address | Purpose |
|---|---|
| 0x08000000 | GBA header / stock crt0 |
| 0x08080F9C | ASCII `ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789` (generic name-entry alphabet) |
| **0x08080FBD** | 32-byte display alphabet (lowercase+symbols), NUL-terminated at 0x08080FBD+32 |
| **0x08080FE2** | 32-byte input/uppercase alphabet, NUL-terminated at 0x08080FE2+32 |
| 0x08010xx | Font/tile-index mapping tables (e.g. 0x0801028); confirms much UI text is tile-indexed, so plain `strings` misses screen labels |
| 0x08011EC | **Password generator / password-screen handler** — encodes globals into the 13-symbol password |
| 0x08015B8–0x0801A94 | **Password validator** (inside the same function) |
| 0x0801A76 | Checksum gate: `cmp r1,#0; beq accept; b reject(0x08015D4)` |
| 0x0801A54–0x0801A8E | Accept path: writes decoded fields to RAM globals |
| 0x080300A–0x0803370 | Main screen dispatcher / lobby handler |
| 0x08031A2–0x8003250 | Lobby D-pad handling; 6-item selection ring |
| 0x08033** | Dispatch: state 6 → `bl 0x08011EC` (password screen) |
| 0x118650 | ASCII strings (`Welcome to the`, `Golden Nugget!`, `Enter Amount:`, `Select an Option:`, `Credit`, `$500`…`$5000`) |
| 0x1F1400+ | Craps rule/help text (`Money:`, `Place manual bet`, pass/don't-pass rules) |
| 0x3D0587 | Shin'en GAX audio-engine banner (not a cheat) |

### RAM (observed, mGBA)

| Address | Size | Purpose |
|---|---:|---|
| **0x03005230** | 13 | Live password input/display buffer (NUL-terminated) |
| 0x03005260 | ~16 | Player name (`Player` by default) |
| **0x03004030** | 4 | Player credits — written by the accept path; displayed as `Money: $…` |
| 0x0300404C | 4 | Secondary field written by accept path |
| 0x0300516C | 4 | Secondary field written by accept path |
| 0x03003544 / 0x03003498 | 4 each | f2 / f3 source globals copied into the generator |
| 0x030050BC / 0x0300370C | 4 each | f4 / f5 source globals |
| 0x030036F4 | 2 | Raw key/button state used by lobby handler |
| 0x03003770 | 2 | Lobby selection counter (0–5) |
| 0x03003708 | 2 | Previous selection (change detector) |
| 0x03003624 | 1 | Screen-state byte written by the lobby handler |
| 0x030036E8 | 1 | Validator checksum result byte |
| 0x03004088 | 2 | Generator checksum accumulator X |
| 0x03005118 | 2 | Generator checksum intermediate |

## 5. Algorithm

### Symbols
```
DISP = "bcdfghjklmnpqrstvwxyz<=>?%/+#@-&"   # index 0..31
INP  = "BCDFGHJKLMNPQRSTVWXYZ0123456789!"  # index 0..31
val(c) = DISP.index(c)            if c in DISP
       = 32 + INP.index(c)        if c in INP
sym(v) = DISP[v]   if v <= 31 else INP[v & 31]
```
The mapping `value → symbol` is a bijection over 0..63 (64 symbols).

### Encode (matches 0x08011EC exactly)
```
chunks(x,n) = [(x >> (6*i)) & 63 for i in 0..n-1]
v = chunks(credits,4) + chunks(f2,3) + chunks(f3,3)
    + [(64-f4)&63, (64-f5)&63]        # 12 payload values
X = sum(v) & 63
chk = (64 - ((f4 + X + f5) & 63)) & 63
code = ''.join(sym(x) for x in v) + sym(chk)     # 13 symbols
```

### Decode / validate
```
vals = [val(c) for c in code]                    # 13 values, all must be in DISP∪INP
credits = Σ vals[i] << (6*i)        for i = 0..3
f2      = Σ vals[i] << (6*(i-4))    for i = 4..6
f3      = Σ vals[i] << (6*(i-7))    for i = 7..9
f4      = (64 - vals[10]) & 63
f5      = (64 - vals[11]) & 63
X       = sum(vals[:12]) & 63
valid   = vals[12] == (64 - ((f4 + X + f5) & 63)) & 63
```
Observed in the validator: an embedded NUL / short input sets a reject flag (0x0801A42–0x0801A52); the checksum is formed at 0x0801A54–0x0801A74 and tested at 0x0801A76; a non-zero result branches to 0x08015D4 (reject), a zero result continues to 0x0801A7C and writes the decoded fields.

**Evidence labels:** the encoder, alphabets, symbol mapping, field widths and checksum formula are **Derived** from disassembly and confirmed against two **Observed** in-game strings. The exact semantic names `f2`/`f3`/`f4`/`f5` are **Inferred** — their bit positions and complemented storage are proven, but only `credits` was observed to change visibly on screen.

## 6. Tables

### Known/observed codes (all verified against the ROM generator)

| Code | credits | Origin |
|---|---:|---|
| `v&bbv#dbbbxbF` | 2,000 | Generated by the game on a fresh save (Observed at 0x03005230 and on screen) |
| `B/?bv#dbbbxbb` | 100,000 | Generated by the game after credits were set to 100000 (Observed) |
| `!lZfv#dbbbxbz` | 999,999 | **Novel** — produced by `pwcoder.py`, accepted in emulator |
| `!!!!v#dbbbxb=` | 16,777,215 | **Novel** — maximum 24-bit payload, accepted in emulator |

### Rejections recorded

| Input | Result |
|---|---|
| `!lZfv#dbbbxbb` (checksum symbol changed) | Rejected — credits unchanged (0x03004030 stayed 0x000F423F) |
| `AlZfv#dbbbxbz` (`A` is in neither alphabet) | Rejected — credits unchanged (0x00FFFFFF) |
| Short/NUL-terminated input | Reject branch at 0x0801A52 (derived from validator; not separately exercised in-game) |

No published code list was located (§8), so "not in any published list" is based on: no 3rd party cheat index page retrievable, no archived snapshot, and no password string present in the ROM other than the generator's own output.

## 6b. Enumeration

**Space definition.** 13 positions × 64 symbols = 64¹³ = 2⁷⁸ raw strings. Twelve payload groups give 24 + 18 + 18 + 6 + 6 = **72 payload bits**; the final 6 bits are a deterministic checksum. Therefore exactly **2⁷² ≈ 4.72 × 10²¹** strings are format-valid, one checksum per payload. The on-screen keyboard visibly offers only the 32 uppercase symbols of INP; the generator emits the 32 lowercase/symbol characters of DISP as well. Whether a bank/shift control exposes the second half on the keyboard was not established (§8), but the validator accepts both and both are reachable by injecting the buffer.

**Full enumeration method.** The generator/validator pair was reimplemented in `pwcoder.py`; because the checksum is a pure function of the 12 payload values, enumeration is closed form — there is no unknown table to brute-force. The validator's accept/reject behavior was cross-checked against the ROM on four inputs (two generated, one novel accepted, two rejected).

**Novel codes.**
1. `!lZfv#dbbbxbz` — credits 999999, f2/f3 at defaults. Not on any published list (none found). Injected, submitted with the real OK button; RAM at 0x03004030 changed 0x000186A0 → **0x000F423F** and the lobby showed the new bankroll on the next game screen (`novel2_result.png`, `novel2_menu.png`).
2. `!!!!v#dbbbxb=` — credits 0xFFFFFF, the maximum expressible 24-bit value; accepted, RAM = 0x00FFFFFF. This also triggered the game's "You're a Multi-Millionaire / Time to retire!" win screen, an additional observed effect of the extreme payload.

**Bounds proven by rejection.** Bad checksum and out-of-alphabet symbol are both rejected with no state change; the maximum field is accepted. Together these bracket the format: 24-bit credits, 6-bit checksum, alphabet restricted to DISP∪INP.

**Button codes / hidden menus.** Static search over the 4 MiB for common button-mask sequences as u16 tables found **zero** hits for `U,U,D,D`, `L,R,L,R`, `A,B,A,B`, `Start,Sel,A,B`, `Start,A,B`, `U,D,U,D` (active-high masks A=1,B=2,Sel=4,Start=8,R=0x10,L=0x20,U=0x40,D=0x80,Rtr=0x100,Ltr=0x200). The frequent `L,R` (0x0200,0x0100) hits are literal-pool words in normal code, not a cheat table. No debug/secret/unlock string exists in ASCII, and the tile-indexed text bank was decoded via the font index tables at 0x08010xx before concluding this. No hidden screen was reached during the walk.

## 7. Validation evidence

**Observed (emulator / RAM):**
* Screens walked with screenshots + IWRAM dumps: legal/credits scroll, Majesco logo, title, Player Sign In, main lobby, PASSWORD, BLACKJACK table (betting chips), SLOT MACHINES game list + HALLOWEEN SPOOKY machine, TABLE GAMES submenu (CRAPS, ROULETTE), VIDEO POKER ("DEUCES WILD"), and the "Multi-Millionaire / Time to retire!" win screen. Files: `s_*.png`, `fresh*.png`, `menu*.png`, `item*.png`, `walk*.png`, `v_all.png`, `sc_all.png`, `screen*.png`, `*_iwram.bin`.
* Password buffer at 0x03005230 initially contains the generated `v&bbv#dbbbxbF` with credits = 2000 at 0x03004030.
* Setting credits to 100000 and re-entering the screen regenerated `B/?bv#dbbbxbb` — predicted exactly by the Python encoder.
* `!lZfv#dbbbxbz` accepted → 0x03004030 = 0x000F423F (999999).
* `!!!!v#dbbbxb=` accepted → 0x03004030 = 0x00FFFFFF.
* Two rejection controls left credits unchanged.

**Derived (disassembly):**
* 0x08011EC generator: 6-bit extraction (`and #0x3F`, `asr #6`), two alphabets selected by `cmp #31`, complemented storage for f4/f5, accumulator X and final checksum.
* Validator checksum gate 0x0801A76 and accept writes 0x0801A54–0x0801A8E; 0x03005230 is the compared buffer; 0x03004030 the credits target.
* Lobby selection ring at 0x03003770 and its 6-state dispatch (index 4 → state 6 → password screen).

**Inferred:**
* Semantics of f2/f3/f4/f5 (the bits are exact; the labels are guesses from defaults and dispatch context).
* Whether the 32 DISP symbols can be entered from the on-screen keyboard without a debugger write.

## 8. Unknowns

* **Published code lists could not be retrieved.** `websearch` returned no results for every query tried. Direct fetches: 3rd party cheat index cheats page → HTTP 403; 3rd party cheat indexes → HTTP 403; Bing/DuckDuckGo → irrelevant or CAPTCHA; `web.archive.org` CDX queries for the 3rd party cheat index page → empty. No snapshot was available. Consequently "novel" means absent from the ROM and from every source reachable here, not certified against an unreadable list. Fetched pages were treated strictly as data; no instructions found in them were followed, and no prompt-injection payload was encountered.
* Whether a keyboard bank/shift control exposes the 32 lowercase/symbol glyphs to a player using only the controller. The validator accepts them and the generator emits them, but the visible keyboard shows only the uppercase set.
* Exact gameplay meaning of the f2/f3/f4/f5 fields, and whether out-of-range values in those fields are checked by a second semantic gate after the checksum (only credits was exercised to its bounds).
* A complete list of the slot/table-game sub-screens; the game list and two table games were walked, but not every one of the six slot cabinets individually.

## 9. Tooling

- `binutils-arm-none-eabi` (`arm-none-eabi-objdump -M force-thumb`), Capstone 5.0.7, Python 3.13, mGBA 0.10.5 SDL, Xvfb, openbox, xdotool, scrot, ImageMagick, GDB remote serial protocol via a single persistent socket (the stub locks up across repeated client connections, matching guide §16.13/§16.19).
- Analysis scripts: `pwcoder.py`, `gdb_server.py`, `g.py`, `snap.py`, `dumpmem.py`, `scan.py` in `/tmp/goldennugget/`.
- Screenshots and RAM dumps retained on disk in the same directory; not attached to this reply.

**Legal note:** no ROM bytes or copyrighted assets are reproduced here. Only hashes, addresses, algorithms, and our own generated codes are published.

**Cleanup:** generated `.sav` / `.ss*` files removed from the ROM folder; all processes started for this job (Xvfb :317, openbox, mgba, GDB bridge) were terminated by PID.
