# Gradius Galaxies (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Gradius Galaxies/Gradius Galaxies.gba` |
| Size | 4,194,304 bytes (0x400000, 4 MiB) |
| Header title | `GRADIUSGALAX` (12 bytes at 0xA0) |
| Game code | `AGAE` |
| Maker code | `A4` (Konami) |
| Revision | 0x00 (`Rev.00`) |
| Entry word | `0xEA00002E` → branch to 0x080000C0 (stock crt0, no cracktro patch) |
| MD5 | `6f16195283a6f16fc73c95c69f131b68` |
| SHA-1 | `dc0f3c4b71c7f543d1693d2a0c356f10f39d16d9` |
| SHA-256 | `ee14fc14052c8efcdf0256b666c45ba81dc26edd3213c86aca0f48e80fe58b52` |

ROM fingerprint: exactly one Nintendo-logo hit (file offset 0), so this is a single
retail image — no multiboot/2-in-1 shell, no appended trainer. No patch/trainer
strings were found. Header anomalies: header checksum at 0xBE is `0x0000` and the
complement byte at 0xBD is `0x52` while a valid complement would be `0x6B`
(sum of 0xA0..0xBD is `0xE7`, not `0xFF`). Per guide §16.1 this suggests a
rebuilt/edited header; the code itself is intact and the entry word is stock.

## 2. Executive summary

The shipped in-game cheat system is a **four-entry button-code table**, not a
password system. There is no password entry screen, no on-screen keyboard, and
no sound test. The codes are Konami-style sequences entered on the **PAUSE
screen** (press Start once during gameplay). All four were found as raw u16
key-mask arrays in ROM, the suffix-match validator was reversed, and all four
were entered with real keypresses in mGBA and confirmed by RAM deltas.

A **debug menu with a STAGE SELECT entry** exists in ROM (ASCII strings at
0x0805C950–0x0805D0E0 and a state handler at 0x0800F380), but it is **not
reachable from any screen walked**: no writer sets the dispatching state variable
(0x03004410) to 3, the value that selects the debug-menu handler. It is
dead/cut developer content (guide §16.3, category 2/3), not a player cheat.

Published-code recon (GameFAQs, TCRF, Wayback Machine, Bing/DuckDuckGo) was
blocked by 403/CAPTCHA/empty CDX; no published Gradius Galaxies list was
recovered. The classic Konami code — the only widely published candidate — is
present in the ROM as code B and verified below. Codes A/C/D are variants that
appear in no list consulted.

## 3. How to reproduce

Emulator: mGBA (SDL), `SDL_AUDIODRIVER=dummy`, Xvfb `:319`, `-3` scale.
Keymap used: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`,
D-pad=arrow keys. Keys held 80–130 ms with ~130–220 ms gaps.

Menu path: boot → press Start through the intro/attract screens → title
(`PRESS START`) → Start → main menu (`NEW START` / `CONTINUE` / `EXIT` / `OPTION`)
→ `OPTION` shows `Game Level: NORMAL|HARD`, `Life`, `BUTTON Config`, `Rapid`,
`Exit`; `NEW START` → `PowerUpSelect` → confirm `OK?` → `START` → Stage 1.

**Code entry:** during gameplay press **Start** once. RAM proof of the gate:
`0x03004D56 = 0x0100` (playing) → `0x0001` (pause / code-entry mode), and the
history index at `0x03000108` advances from 0 to 1 (the Start press is recorded).
Then press one of the sequences below. Press Start again to leave the mode
(clears bit 0).

| Code | Play order (press sequence) | ROM array (newest-first) | Effect (RAM-verified) |
|---|---|---|---|
| A — shoulder Konami | ↑↑↓↓ Lsh Rsh Lsh Rsh B A | 0x0805D504 | `0x03004D44` +1; `0x03004D58` −1 (needs `0x03004D58 != 0`) |
| B — classic Konami | ↑↑↓↓ ← → ← → B A | 0x0805D51A | `0x03004DAE = 0x00F0`; `0x03004D44` +1 |
| C — reversed D-pad | ↓↓↑↑ → ← → ← A B | 0x0805D530 | `0x03004D46` −1 (needs `>1`); `0x03004D44` +1 |
| D — reversed shoulder | ↓↓↑↑ Rsh Lsh Rsh Lsh A B | 0x0805D546 | `0x03004DAE = 0x00F0`; `0x03004D44` +1 |

Note the final two presses are **B then A** for A/B, and **A then B** for C/D —
reversing them is a rejection (verified). `Lsh`=`a`, `Rsh`=`s`.

## 4. Address map

All addresses are ROM (`0x08...`) or IWRAM (`0x03...`). File offset = addr − 0x08000000.

| Address | Meaning |
|---|---|
| `0x0805D4EC` | base of the key-mask/data table region |
| `0x0805D4F4`–`0x0805D502` | four u16 single-key entries (`B`, `B+Select` ×3); role not established (likely adjacent data table) |
| `0x0805D504` | code A sequence, 10 u16 + NUL |
| `0x0805D51A` | code B sequence (classic Konami) |
| `0x0805D530` | code C sequence |
| `0x0805D546` | code D sequence |
| `0x0805D55C` | following u16 data table (small indices, not key masks) |
| `0x08014694` | validator: `u16 *seq` in r0 → 1 if suffix matches, else 0 |
| `0x08014560` | cheat checker: records new key, dispatches A/B/C/D, writes flags |
| `0x0801458A` / `0x080145CA` / `0x0801460E` / `0x08014646` | four validator call sites (A, B, C, D) |
| `0x08013F3A` | only caller of the checker (gated) |
| `0x08013F14` / `0x08013EFC` | writers of gate bit 0 (set/clear on Start) |
| `0x03001EF2` | newly pressed key masks, active-high (A=1,B=2,Select=4,Start=8,→=0x10,←=0x20,↑=0x40,↓=0x80,R=0x100,L=0x200) |
| `0x030000E8` | 16-entry circular key-history buffer, u16 |
| `0x03000108` | history write index (mod 16) |
| `0x03004D10` | game-state struct base |
| `0x03004D44` (base+0x34) | "cheats used" counter, clamped to 98 |
| `0x03004D46` (base+0x36) | code-C availability counter |
| `0x03004D56` (base+0x46) | gate/flags: bit 8 = playing, bit 0 = code-entry (pause) |
| `0x03004D58` (base+0x48) | code-A availability counter |
| `0x03004DAE` (flag struct+0x3e) | set to `0x00F0` by codes B and D |
| `0x03004DB0` (flag struct+0x40) | cheat flag word; bit 1 set by all four codes (transient) |
| `0x0805C950`–`0x0805D0E0` | debug-menu ASCII strings and data tables |
| `0x0800EF08` | 22-state dispatcher (table at 0x0800EF30); state 3 → 0x0800EF94 |
| `0x0800F380` | debug-menu initialiser (state 3 handler) |
| `0x03004410` | screen-state global |
| `0x0800F4B4` | magic word `0x41434952` ("RICA") + 188-byte checksum record in debug code |

## 5. Algorithm

Key-mask semantics (derived from input routine at 0x08000914):
`new = (0x3FF & ~raw_keyinput) & ~(previous_active_high_state)`, stored at
0x03001EF2 — active-high, one bit per newly pressed button.

Checker (0x08014560), executed only when `gate & 1`:

```
key = [0x03001EF2]
if key == 0: return                      # no new press, do not advance ring
history[idx] = key                        # 0x030000E8, idx = [0x03000108]
if key == A:
    if [0x03004D58] != 0 and check(0x0805D504):
        flags |= 2; ctr34++; ctr48--
    if check(0x0805D51A):
        [0x03004DAE] = 0xF0; flags |= 2; ctr34++
elif key == B:
    if [0x03004D46] > 1 and check(0x0805D530):
        flags |= 2; ctr34++; ctr36--
    if check(0x0805D546):
        [0x03004DAE] = 0xF0; flags |= 2; ctr34++
idx = (idx + 1) & 15
```

Validator (0x08014694) — suffix match, sequences stored **newest-first**:

```
def check(seq_ptr):                       # seq_ptr = ROM address of NUL-terminated u16 seq
    i = [0x03000108]                      # index of newest entry
    p = seq_ptr
    expected = u16[p]; p += 2
    if expected == 0: return False
    if history[i] != expected: return False
    while True:
        i = (i - 1) & 15
        expected = u16[p]; p += 2
        if expected == 0: break
        if history[i] != expected: return False
    return True
```

Gate writer (0x08013ED0, Start handling): on Start, if bit 0 already set → call
0x08016418/0x080EBF0 and clear bit 0; else call 0x08014540 (reset history) and
set bit 0.

## 6. Tables

Key masks (active-high): A=0x001, B=0x002, Select=0x004, Start=0x008,
Right=0x010, Left=0x020, Up=0x040, Down=0x080, R=0x100, L=0x200.

The four sequences (u16, newest-first, NUL-terminated) and their in-game RAM
deltas are listed in §3. The `0xF0` byte and the `0x03004D44` counter were
observed directly; the transient flag-bit write was observed by calling the
handler in the debugger (§7).

Debug-menu string table (0x0805C950, 20-byte records + u32 target state):
`INITIAL START`→4, `PLAY GAME`→0xB, `STAGE SELECT`→0xC, `RECORD`→0x10,
`DEBUG 0024`→2, `DEBUG 0019`→3, blank→1; plus difficulty labels
`JP EASY`, `JP NORMAL`, `JP HARD`, `US HARD-1`, `US HARD-2` and toggle labels
`OFF`/`ON`, `LEVEL`, `UNDEAD`, `FULL POWER`, `OK` at 0x0805D050–0x0805D0DC.
None of these screens was reachable.

## 6b. Enumeration

**Space definition.** The accepted language is four fixed 10-press sequences
over the 10-bit key-mask space (2^10 = 1024 possible masks per press, but only
10 single-button masks are used). There is no checksum, no variable field, and
no generator: the validator compares the key history directly against four
hard-coded ROM arrays. Therefore the complete accepted set is exactly **4
codes**; the representational space is 4 × 10 = 40 pressed buttons.

**Full enumeration proof.** Pointer scan for references into the key-mask table
found exactly four validator call sites (0x0801458A/CA, 0x0801460E/46) and four
sequence pointers (0x0805D504/51A/530/546). `0x0805D55C` and beyond are small
indices, not key masks. The checker dispatches **only** on `key == A` or
`key == B`; no other action branch exists. All four branches were executed and
observed in-game (§7).

**No novel code is possible, and this is proven, not assumed.** Because the
validator's only inputs are the four fixed arrays, any 10-press sequence not
equal to one of them is rejected. Oracle tests against code B (calling
`0x08014694` from the debugger with a chosen history, per guide §16.19):

| candidate history (newest-first) | validator r0 |
|---|---|
| exact Konami `A B → ← → ← ↓ ↓ ↑ ↑` | 1 (accept) |
| one press changed (`→`→`←`) | 0 (reject) |
| reversed order | 0 (reject) |
| only 9 presses | 0 (reject) |
| one extra newer press | 0 (reject) |
| empty history | 0 (reject) |

In-game rejection: sequence `↑↑↓↓ ←←←→ B A` (one press changed) advanced only
the history index; none of `0x03004D44/46/48/DAE/DB0` changed. This is a bounded
negative result: the format has no free field to mint a novel value in.

**Hidden-menu enumeration.** The debug menu has 7 named entries (§6). Its
dispatcher (0x0800EF08) handles states 1–22; state 3 selects the debug-menu
init. A full scan of every `str` to the state global `0x03004410` found writes
of {1,4,5,6,7,8,9,10,13,15,17,18,19,20,21,22} and a table-driven write at
0x08010E60, but **no write of 3**. Screens walked (title, main menu, OPTION,
PowerUpSelect, gameplay, PAUSE, RANKING, name entry, history/hint) never
displayed it. Conclusion: dead/cut developer screen, not an unlockable.

## 7. Validation evidence

**Observed (emulator).**
- Title, main menu, OPTION (NORMAL/HARD, Life, BUTTON Config, Rapid, Exit),
  PowerUpSelect, Stage 1 gameplay, PAUSE, RANKING, name entry, history/hint
  screens all reached; screenshots saved on disk (e.g.
  `/tmp/opencode/gradius/s1.png`, `r_play.png`, `r_pause.png`,
  `m_option2.png`, `code_*.png`).
- Gate RAM: `0x03004D56` 0x0100 (playing) → 0x0001 after Start; history index
  0 → 1; after code entry index 1 → 0xB and history ring reads
  `Start, ↑,↑,↓,↓,←,→,←,→,B,A`.
- All four codes entered with real keys from a single gate-active savestate;
  RAM deltas: A `{c34: 0→1, c48: 1→0}`, B `{c34: 0→1, f3e: 0→240}`,
  C `{c34: 0→1, c36: 2→1}`, D `{c34: 0→1, f3e: 0→240}`, wrong code `{}`.
- Debugger oracle (mGBA `-d`, breakpoint at 0x080146D0): validator returned 1
  for each of the four ROM sequences; rejections as tabulated in §6b.
- Calling the game's own handler 0x08014560 with a Konami history and newkey=A
  wrote `flags=0x0002`, `+0x3e=0x00F0`, `+0x34=1` — the same effects seen from
  real keypresses.

**Derived (instructions).** Validator suffix-match loop, gate writers, the four
validator call sites and their flag/counter effects, the circular-history
layout, and the absence of a `state = 3` writer were all read from Thumb
disassembly with literal pools decoded via `struct.unpack_from("<I", ...)`.

**Inferred.** The semantic meaning of the counter fields (lives/continues) and
of `0x00F0` is not established; only the writes and reads are proven. The four
single-key entries at 0x0805D4F4–0x0805D502 are plausibly adjacent data rather
than cheats. No visible gameplay change was reliably attributable to a code —
the PAUSE overlay hides most of the playfield; RAM writes are the primary proof.

## 8. Unknowns

- What gameplay benefit `0x03004DAE = 0xF0` and `0x03004DB0` bit 1 confer;
  candidate readers exist at 0x08023C58 etc. but were not exercised to a
  visible outcome.
- Whether any indirect write (0x08010E60 reads a signed menu index) can ever
  produce state 3 and open the debug menu; no reachable menu index was found.
- Published-code list could not be fetched (403/CAPTCHA/empty archive), so
  "unpublished" status of codes A/C/D rests on the ROM's fixed four-entry table,
  not on a comparison with an actual GameFAQs list.

## 9. Tooling

`file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings -t x`, `grep -abo`,
`arm-none-eabi-objdump -M force-thumb`, Python 3 + Capstone (literal/BL/xref
scans), mGBA SDL under Xvfb `:319` + openbox, xdotool, scrot, Pillow for screen
detection. RAM evidence via mGBA `.ssN` savestates: PNG `gbAs` chunk,
`zlib.decompress`, IWRAM at raw offset 0x19000 (0x03000000 → 0x19000), EWRAM at
0x21000. Oracle via mGBA `-d` console driven through a Python Unix-socket
bridge (`w/2`, `w/r`, `b/t`, `continue`, `next`, `p/x`), with the emulator
halted. No ROM or copyrighted assets are redistributed here.

---

Legal note: findings, addresses, hashes and tools only; no ROM, graphics,
music or extracted game text are included.
