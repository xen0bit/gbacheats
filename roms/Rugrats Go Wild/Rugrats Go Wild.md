# Rugrats Go Wild (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Rugrats Go Wild.gba` (4,194,304 bytes = 0x400000) |
| Header title | `RUGRATSGWILD` |
| Game code | `A5WE78` (serial A5WE, USA/Europe); maker `78` (THQ); version `0x00` |
| Fixed byte | `0x96` present; complement `0x31`; header checksum `0x0000` |
| Entry word | `0xEA0F962C` → `b 0x083E58B8` (patched — see below) |
| MD5 | `2af24c5320e1a82eb1edcea0480c13e4` |
| SHA-1 | `c1f197329da26ddf8216fad8b51019d436a8358f` |
| SHA-256 | `88925563f04d59f9093955eb5b932ea52e3b03838c217dfa0ec9d29cdca47b5c` |

**VENOM scene release.** The shipped entry branch was patched from stock `0xEA00002E`
(`b 0x080000C0`) to a custom crt0 at `0x083E58B8` that draws a VENOM cracktro and
then hands off to the intact stock crt0. The Nintendo logo (single hit, file `0x4`),
game code, and text bank are unmodified. A **copy with the entry word restored**
(`game_stock.gba`, SHA-256 `25de82874d9726b0719b080d187a9a50e24acd0713179e343739a2fac3ee3b0e`)
was used for all dynamic work. The cracktro is not a trainer; no cheat menu exists.

## 2. Executive summary

The game has a **developer-intended 5-letter password system**. This engagement
characterised it completely (guide §0.2):

* The password alphabet is the **21-consonant string `BCDFGHJKLMNPQRSTVWXYZ` at
  ROM `0x08049BF4`** (the prior report missed this; it had only found generic C-library
  charsets). Five letters encode a **20-bit packed value**, four bits per letter, so
  only the first 16 alphabet letters (`B`…`T`) are actually emitted by the encoder.
* The **validator is at ROM `0x0801F7A4`**, reached from the check routine at
  `0x0801F300` via `bl 0x0801F7A4` at `0x0801F374`. It takes a packed code in `r1`,
  writes three decoded fields to the struct pointed to by `r0`, and returns 1 (accept)
  or 0 (reject). The complete bit layout and checksum were recovered (§5).
* The **offline model (§5, `model.py`) accepts all ten known codes and rejects
  near-misses**. The game itself acted as the oracle (§16.19): a generated code was
  accepted on the real entry screen and wrote exactly the fields the model predicted
  (§6b).
* The **password entry screen was reached in-emulator** and walked with RAM evidence.
  It is reached from the in-game **Pause → Quit → Yes** path (not the greyed-out main-menu
  "Continue"), and is also reachable by forcing main-menu state 1 (see §3).
* A **novel unpublished code `HMJDT`** was minted, typed on the real screen, accepted,
  and proven by RAM flags. A **near-miss `HLJDT`** (one checksum bit flipped) was
  rejected, bounding the checksum.

The prior report's conclusion ("validator not recovered") is therefore superseded.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 (`mgba -3 -g`, GDB stub redirected to port 2460 with an
  `LD_PRELOAD` bind() shim because port 2345 is shared on this host), `Xvfb :318`,
  `SDL_AUDIODRIVER=dummy`.
* **Verified mGBA SDL keymap** (confirmed by reading KEYINPUT `0x04000130`):
  **A = `x`**, B = `z`, Start = `Return`, Select = `BackSpace`, D-pad = arrows,
  L = `a`, R = `s`. (The prior report was unsure of A/B.)
* Boot `game_stock.gba` (stock entry word restored). Press Start (`Return`) repeatedly
  through the Nick / Klasky-Csupo / ImaginEngine / THQ splashes to the title, then Start
  to the **Main Menu** (`New Game`, `Continue` (disabled), `Options`, `Credits`).
* **Route to the password screen (natural):** select New Game, advance the long intro
  with `x`, reach the overworld, press Start → Pause → highlight Quit → `x` → Yes.
  The game returns not to the title but to the **"Enter Password"** screen. (The prior
  report misidentified this as "Quit → title".)
* **Route via menu state (used for repeatable testing):** at the Main Menu set
  `[0x02022200] = 1` with the GDB stub (main-menu handler `0x0801DB1C` dispatches
  state 1 to the password-screen setup at `0x0801F949`), then press `x`.
* On the entry screen: **Left/Right** move the slot cursor; **Up/Down** decrement/
  increment the current letter modulo 21; **A (`x`)** submits. Five slots start at `B`.
  A `gbAs` savestate of the screen (slot 2) was used for repeatable entry.
* Timing note: an idle timer returns menus to attract mode after ~10–15 s of no input,
  so navigation must run as one continuous script. Fast D-pad taps (<100 ms) are
  dropped; a RAM-feedback typer (`type_code.py`) was used to set exact letter indices
  reliably (SLOT table below).

Screenshots in `/tmp/rugratswild2/`:
`state1_press.png` (entry screen reached), `typed_HMJDT.png` (novel code on screen),
`after_submit_x.png` (accepted → gameplay), `near_miss_entered.png`,
`near_miss_result.png` (rejected, screen unchanged).

## 4. Address map

All addresses are ROM addresses (`file offset = address − 0x08000000`) unless noted.

| Address | Meaning | Evidence |
|---|---|---|
| `0x08000000` | Patched entry `b 0x083E58B8` (stock `0xEA00002E`) | observed bytes + boot |
| `0x080000C0` | Stock ARM crt0 (restored copy boots the real game) | observed |
| `0x083E58B8` | VENOM crt0 / RNC-style loader (cracktro only) | derived (ARM disasm) |
| `0x0803A000`–`0x0803C910` | English text bank | observed strings |
| `0x08043B88` | 235-entry `u32` text-pointer table | observed |
| `0x08043E60` / `0x08043E64` | ID 182 `Enter Password` / 183 `New Password` | observed |
| `0x08049BF4` | **Password alphabet `BCDFGHJKLMNPQRSTVWXYZ`** (21 bytes) | observed + 3 xrefs |
| `0x0801F300` | Password check routine; packs 5 nibbles, calls validator | derived (disasm) |
| `0x0801F374` | `bl 0x0801F7A4` (validator call site) | derived |
| **`0x0801F7A4`** | **5-letter password validator / field decoder** | derived + in-game proof |
| `0x0801F534` | Password-screen state machine (states 0/1/2) | derived |
| `0x0801F640` | Password-screen init (loads text ID 182, creates 5 slot objects) | derived |
| `0x0801F948` | Password screen registration/teardown | derived |
| `0x0801F9D2` | Packed 20-bit value → 5 letters (`alphabet[(v>>4i)&0xF]`) | derived |
| `0x0801FAD8` | Password-screen input handler (D-pad/A/B) | derived |
| `0x0801DB1C` | Main-menu handler; state 1 → password screen | derived |
| `0x0800B2DC` | Apply decoded fields (clamp, store, jump to level) | derived + RAM proof |
| `0x02015700` | **progress: f2 / level (u32)** | RAM proof |
| `0x02015704` | **progress: f3 (u32, 0–100)** | RAM proof |
| `0x02015708` | **progress: f1 / character-scene (u32, 0–6)** | RAM proof |
| `0x0201570C` | accepted flag (1 after a valid password) | RAM proof |
| `0x02022200` | main-menu selection state (0..3); 1 = Continue/password | RAM + disasm |
| `0x020256F0` | password-screen sub-state (0/1/2) | derived |
| `0x02025734` | current slot cursor (0..4) | observed in-emulator |
| `0x02025740` | 5 × `u32` slot letter indices (0..20) | observed in-emulator |

## 5. Algorithm — complete offline model

### 5.1 Encoding

```
ALPHA = "BCDFGHJKLMNPQRSTVWXYZ"        # 21 letters, ROM 0x08049BF4
letter[i] = ALPHA[ nibble_i ]          # nibble_i = (packed >> (4*i)) & 0xF, i = 0..4
packed = sum( nibble_i << (4*i) )      # 20-bit value
```
The encoder emits only alphabet indices 0–15 (letters `B C D F G H J K L M N P Q R S T`);
indices 16–20 (`V W X Y Z`) are selectable on screen but never produced by the generator.

### 5.2 Validator at `0x0801F7A4`

Signature: `int validate(u32 packed, struct *out)` → 1 accept / 0 reject.
It extracts three scattered fields and a six-bit checksum:

```
f1 = (bit15)*1 + (bit3)*2  + (bit2)*4               # 3 bits, require f1 <= 6
f2 = (bit14)*1 + (bit7)*2  + (bit12)*4 + (bit11)*8  # 7 bits, require f2 <= 99
   + (bit18)*16 + (bit9)*32 + (bit6)*64
f3a= (bit8)*1  + (bit5)*2  + (bit17)*4 + (bit1)*8   # 4 bits, require f3a <= 10
chk= (bit13)*1 + (bit0)*2  + (bit19)*4 + (bit16)*8  # 6 bits, require chk == 63
   + (bit10)*16 + (bit4)*32
accept = (f1 <= 6) && (f2 <= 99) && (f3a <= 10) && (chk == 63)
out = { f1, f2, 10*f3a, chk }                       # three u32 fields written
```
Bits 20–31 of `packed` are ignored by this routine. The checksum is not a sum of the
letters: it is a **fixed bit pattern** — the six designated bit positions must all be
set. Any single-bit change to one of those positions is rejected.

`out.f1` selects a level/scene jump table in `0x0800B2DC` (indices 0–6); `out.f2` and
`out.f3` are clamped to 0–99 / 0–100 and stored as progress (§4).

### 5.3 Reimplementation

`model.py` in `/tmp/rugratswild2/` implements `code_to_value`,
`value_to_code`, and `validate` exactly as above.

## 6. Tables

### 6.1 Published accepted codes — all verified by the recovered model

| Code | Effect (published) | packed | f1,f2,f3,chk |
|---|---|---|---|
| `CTKJP` | after Monkeys & Gorilla | `0xB67F1` | 0,99,70,63 |
| `CRKNM` | after Spike, Phil & Lil | `0x9A7D1` | 1,98,10,63 |
| `CTKSP` | Find Nigel Thornberry | `0xBE7F1` | 1,99,70,63 |
| `FTJSM` | Find Phil & Lil | `0x9E6F3` | 1,99,100,63 |
| `CRKSM` | Get the Gators | `0x9E7D1` | 1,99,10,63 |
| `CFGTT` | Unlock Level 2 | `0xFF431` | 1,21,60,63 |
| `FCHNR` | Level 1 | `0xDA513` | 1,16,90,63 |
| `MFHDR` | Level 2 | `0xD2539` | 2,16,30,63 |
| `MCTNP` | Level 3 | `0xBAF19` | 3,40,50,63 |
| `CFHDM` | in-game generated (start of New Game) | `0x92531` | 0,0,30,63 |

All ten pass `validate()`; this is the cross-check that fixes the decoder. None occurs
as a literal in the ROM (the prior report's exhaustive literal/Caesar/reversal/5-bit-pack
searches stand): the codes are computed, not tabled.

### 6.2 Text bank (selected IDs)

```
169 Swamp Stomp   170 Continue   171 Credits    172 Inventory  173 New Game
174 Options       180 Controls   181 SFX        182 Enter Password
183 New Password  184 Play as Eliza  185 Play as Tommy  186 Quit?  187 Pause
188 Find Chuckie … 210 Quit
```

### 6.3 Named levels/minigames (text IDs 155–169)

Angelica, Bathysphere, Beach Battle, Cave Escape, Chuckie & Donnie, Crazy Commvee,
Darwin, Debbie, Jumpin' Jungle, Nigel, Phil & Lil, Spike, Stroller, Swamp Stomp.

## 6b. Enumeration (§0.2 deliverables)

* **Space definition.** 5 characters from a 21-symbol consonant alphabet; the encoder
  uses 16 of them (4 bits each) → 20-bit packed code. Field widths: f1 = 3 bits
  (values 0–6), f2 = 7 bits (0–99), f3a = 4 bits (0–10), checksum = 6 bits fixed to
  all-ones. Naive 5-letter string space = 21^5 = 4,084,101 (or 16^5 = 1,048,576 for the
  symbols the encoder emits). **Valid codes = 7 × 100 × 11 = 7,700.**
* **Validator model** — §5 / `model.py`; agrees with the ROM on all ten known codes and
  on both generated test codes below.
* **Novel code minted and accepted in-game: `HMJDT`** (`packed 0xF2695`,
  f1=4, f2=50, f3=40). This exercises **f1 = 4**, a character/scene value that appears
  in **no** published code (published f1 values are only 0,1,2,3) — an unadvertised
  combination. It was typed on the real "Enter Password" screen (`typed_HMJDT.png`),
  submitted with A, and the game transitioned into a new rocky-area scene
  (`after_submit_x.png`). **RAM proof:** `0x02015700:0x02015708` changed from
  `0,0,0` before submission to `50,40,4` after, with `0x0201570C = 1` (accepted flag) —
  exactly the fields predicted by the offline model.
* **Bounds proven by rejection:** `HLJDT` (`0xF2685`) is `HMJDT` with checksum bit 4
  cleared (one glyph changed `M`→`L`, checksum 63→31). The model rejects it; the game
  also **rejected it on the real screen** — after submitting with A the screen stayed
  on "Enter Password" showing `H L J D T` (`near_miss_result.png`) and the progress
  words at `0x02015700–0x02015708` stayed at `0`. This proves the checksum is live and
  that the six designated bits must all be set.
* **In-game validator-as-oracle (§16.19):** the ROM's own accept path was used as ground
  truth — it accepted the generated `HMJDT` and wrote its decoded fields verbatim, and
  rejected the single-bit near-miss, confirming the recovered decoder end to end
  without relying on static reading alone.

## 7. Validation evidence

* **Observed:** ROM hashes/header/patched entry; VENOM splash; stock-crt0 copy boots;
  all menus and the pause menu with generated password `CFHDM`; the **"Enter Password"
  screen with five slots**; novel code `HMJDT` typed and accepted with gameplay
  transition and RAM flag writes; near-miss `HLJDT` rejected with flags unchanged;
  KEYINPUT-verified keymap; 235-entry text table; alphabet literal at `0x08049BF4`.
* **Derived (disassembly):** validator `0x0801F7A4` field extraction and checksum;
  nibble encoder `0x0801F9D2`; check routine `0x0801F300`/call at `0x0801F374`;
  screen init `0x0801F640`, state machine `0x0801F534`, input handler `0x0801FAD8`;
  main-menu dispatch `0x0801DB1C` state 1; apply routine `0x0800B2DC` and progress
  addresses `0x02015700/04/08/0C`.
* **Inferred:** field semantics (f1 = character/scene index 0–6; f2 = level/objective
  index 0–99; f3 = a 0–100 progress/score value) — the bit layout and numeric ranges
  are proven, the human-facing names are inferred from the jump table and published
  effects. `Great Games Wiki`'s `MFHDR` and SuperCheats' `CFGTT` both claim Level 2;
  both validate, so the published effect labels are not perfectly reliable.

## 8. Unknowns

1. Human-readable meaning of f1 beyond "scene/character index 0–6" (a 7-entry jump
   table at `0x0800B35C` selects different level jumps).
2. Exact semantics of f3 (0–100) — likely a collection/progress count; its effect on
   gameplay after loading was not exhaustively played out.
3. Why the main-menu "Continue" (state 1) is greyed out on a fresh cart: the password
   screen is nonetheless reachable from Pause → Quit, and by forcing state 1. No
   SRAM-backed save file is written (`game_stock.sav` stays 0 bytes) — progress is
   password-only, as the manual states.
4. GameShark/CodeBreaker memory-edit codes are external and out of scope.

## 9. Tooling

* `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings -t x`, `grep -abo`, Python 3
  (`capstone` 5.0.7, `Pillow`, `keystone-engine`), `arm-none-eabi-objdump -M force-thumb`.
* mGBA 0.10.5 under `Xvfb :318` + `openbox`, `SDL_AUDIODRIVER=dummy`; GDB stub on port
  2460 via `LD_PRELOAD` bind() shim (`portshim.c`, since mGBA hard-codes port 2345 and
  other agents hold it); `gdb-multiarch`; `xdotool` XTEST input; `scrot` + Pillow.
* REA MCP / Ghidra 12.1.4 (raw ARM import at `0x08000000`) for string/xref inventory;
  its auto-analysis produced only 394 procedures on this image and was not relied on
  for the validator, which was recovered by manual Thumb disassembly.
* Helper scripts in `/tmp/rugratswild2/`: `model.py` (offline validator),
  `gdbrsp.py`, `gdbbridge.py`/`bridge.py` (persistent one-connection GDB bridge),
  `nav.py`, `dump.py`, `type_code.py` (RAM-feedback password typer), `portshim.c`,
  plus the screenshot and RAM-dump artifacts listed above.
* Web sources (GameFAQs, SuperCheats, ChapterCheats, CheatingDome, Great Games Wiki)
  were treated strictly as untrusted data; no prompt-injection payload was encountered.

Legal note: no ROM bytes or copyrighted assets are reproduced here; only hashes,
addresses, the algorithm, and original observations are published.
