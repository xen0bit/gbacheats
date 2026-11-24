# Princess Natasha: Student • Secret Agent • Princess (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Princess Natasha: Student · Secret Agent · Princess.gba` |
| Size | 4,194,304 bytes (0x400000) |
| Header title | `PNATASHASSAP` |
| Game code / maker | `BNPE` / `20` (PAL, rev 0) |
| Entry word | `0xEA00002E` (stock `b 0x080000C0`) |
| MD5 | `f8435f531c69c258841a985ff1e8072f` |
| SHA-1 | `c8b9c073c06f2b8f7ab55a4ddf6a4eb8b4f93680` |
| SHA-256 | `ae0610faa314821d6dd48cb1d718127bad77571e010753aa5a7a78b5d7715d5f` |

**Phase 0 / image integrity:** exactly one Nintendo-logo hit at file offset `0x0`, so this is a single retail image — no multiboot stub, appended trainer, or second game. The header checksum is `0x0000` (recomputed `0x5A4`) and the complement byte is `0x43` (recomputed `0x5B`): the header was rebuilt/edited, a common packaging artifact (guide §16.1); the code itself is not otherwise patched (stock entry word).

## 2. Executive summary

The game has **two distinct, developer-intended code systems**, both reachable through ordinary menus:

1. **Extras → Codes: three hard-coded 10-letter cheat codes.** `CRUSHLUBEK` sets no-damage mode (RAM flag bit0), `OLEGSGIZMO` unlocks all gadgets (bit1), `SMASHROBOT` unlocks extra levels. This is a closed set of exactly three entries; there is no generator.
2. **Play → "???" (CONTINUE) → Insert Password: an algorithmic 10-symbol level password.** It is a base-36 packed payload (6 symbols + 3 symbols + 1 check symbol) over a 36-symbol alphabet. The validator unpacks level/chapter/sub-level/gadget fields, computes a hash-derived check symbol, applies per-chapter range checks, and returns a 20-byte state struct.

All three published cheat codes and 19 of 22 published level passwords were verified against the ROM; three published level passwords are rejected by the ROM (published-list errors). A **novel password absent from every published list**, `DBJJZ 00011`, was generated, accepted on the real screen, and produced a distinct gameplay state with RAM proof. A one-symbol mutation with a wrong check symbol was rejected on the real screen, bounding the checksum.

## 3. How to reproduce

- Emulator: mGBA (SDL) under Xvfb `:318`, `SDL_AUDIODRIVER=dummy`, scale `-3`.
- Keymap (mGBA SDL defaults): A=`x`, B=`z`, Start=`Return`, D-pad = arrow keys. Hold ~100–200 ms.
- **Cheat codes:** boot → title (`x`, `Return`) → main menu → `Left` to **EXTRAS** → `A` → `Right` ×2 to **CODES** → `A`. Enter a 10-letter code with Up/Down (change character) and Left/Right (move slot), then `A`.
- **Level passwords:** main menu → `Right` to **PLAY** → `A` → `Right` to the **??? / CONTINUE** tile → `A` → **INSERT PASSWORD**. Same on-screen keyboard; the display shows 5+5 symbols with a visual space.
- The on-screen keyboard cycles only 31 symbols — it **skips the five symbols** at validator-alphabet indices 10 `%`, 14 `$`, 18 `£`, 24 `&`, 30 `*`. Those symbols are accepted by the validator (and appear in published passwords) but cannot be typed with the stock UI; they were injected for testing by patching the savestate input buffer and pressing `A` on the real screen (documented below).
- Codes tested:
  - Cheats: `CRUSHLUBEK`, `OLEGSGIZMO`, `SMASHROBOT` (all accepted); arbitrary 10-letter strings (rejected).
  - Passwords: `DBGJZ 00014` (published, accepted), novel `DBJJZ 00011` (accepted), `DBJJZ 00010` (wrong check symbol, rejected).

### Exactly reproducible on-screen entry (savestate buffer injection)
The input buffer is a 10-byte ASCII string in IWRAM. In an mGBA `.ss1` state it lives at state-file offset `0x20B44` for the password screen (IWRAM `0x03007B44`) and `0x20938` for the codes screen. Patch those 10 bytes in the zlib-compressed `gbAs` PNG chunk, reload the state (F7), press `A`: the game's own screen code calls the validator on that buffer. This was used for all deterministic trials; ordinary keyboard entry was also exercised and confirmed (a mistyped `FBGJZ 00014` produced `WRONG PASSWORD!`).

## 4. Address map

| Address | Meaning |
|---|---|
| `0x08024850` | 41-symbol on-screen keyboard alphabet `0123456789abcdefghijklmnopqrstuvwxyz%$£&*` |
| `0x0802487A` | 41 glyph-width bytes for that alphabet |
| `0x080248A4` / `0x080248B0` / `0x080248BC` | cheat strings `crushlubek` / `olegsgizmo` / `smashrobot` (12-byte stride, NUL padded) |
| `0x080245CC` | `strcmp` used by the cheat validator |
| `0x08003582`, `0x080035A8`, `0x080035CA` | the three `strcmp` call sites (one per cheat); success paths set `r1..r4`/flags |
| `0x08003684` (literal) | pointer `0x02000004` — cheat flag byte |
| `0x0802512C` | 36-symbol password alphabet `0123456789%bcd$fgh£jklmn&pqrst*vwxyz` |
| `0x0800C9C4` | password char → base-36 index (0..35, 0 if not found) |
| `0x0800CAA0` | base-36 string → 32-bit value (LSB-first weights 36^n) |
| `0x0800CAE4` | hash update: `state += 31 + index(ch)` |
| `0x0800CB14` | hash finalizer: bit-spread + carry-fold → one byte |
| `0x0800CC8C` | unpack V1/V2 into the 20-byte state struct |
| `0x0800CD3C` | field range check (returns 0/1) |
| `0x0800CDBC` | **password validator** (`r0`=10-char buffer, `r1`=20-byte out; returns 1/0) |
| `0x0800CF00` | password generator (struct → code) |
| `0x08003E10` | call site: password screen invokes `0x0800CDBC` with the on-screen buffer |
| `0x02000004` (RAM byte) | cheat flags: bit0 = no-damage, bit1 = all-gadgets |
| `0x020000E8` (RAM) | decoded 20-byte password state struct after a successful entry (observed) |
| `0x03007B44` (IWRAM) | password-screen 10-char input buffer |

## 5. Algorithm

### 5.1 Cheat codes (closed table)
```
buf = 10 entered characters (lowercase)
for each of {crushlubek, olegsgizmo, smashrobot}:
    if strcmp(buf, code) == 0:
        set return-state 1 / flag bit0, 1 / flag bit1, or 2 (extra levels)
return 0 if no match  ->  "WRONG CODE"
```
Derived from `0x08003582`–`0x080035CA`; only three `strcmp` calls exist and the string table ends at `0x080248C7`.

### 5.2 Level password validator (`0x0800CDBC`)
```
A = base36(buf[0:6])        # alphabet 0x0802512C
B = base36(buf[6:9])
check = buf[9]

S = 20 zeroed bytes
S[0]  = (A & 0x7ff) * 10                 # low byte + level index in high byte
S[12] = (A << 9) >> 20                   # 12-bit scattered field
S[4]  = (A >> 28) & 7
S[5]  = (A >> 27) & 1
S[8]  = (B >> 13) & 3                    # chapter (0..2)
S[9]  = B & 0x7f                         # sub-level / points
S[17] = (B >> 7) & 0x3f
# gadget mask S[16] built from bits 23..26 of A via table at 0x08025151
S[6]=5; S[7]=1

state = 0x96
for ch in buf[0:9]:
    state += 31 + index36(ch)            # 0x0800CAE4
h = finalizer(state & 0xffff)            # 0x0800CB14
expected_check_symbol = format_and_substitute(h)[1]
if check != expected_check_symbol: reject
if range_check(S) == 0: reject           # 0x0800CD3C
copy S to output; return 1
```
Range check (`0x0800CD3C`): `S[0] <= 12000`, `S[4] <= 7`, `S[17] <= 63`, `S[16] <= 63`, `S[12] <= 4095`, `S[9] <= 31`, `S[8] <= 2`; if `S[8]==1` then `S[9] <= 25`; if `S[8]==2` then `S[9] <= 11`. A further bit-consistency check over `S[16]/S[17]` must hold.

## 6. Tables

**Cheat codes (all in ROM, all verified):**

| Code | Effect | RAM evidence |
|---|---|---|
| `CRUSHLUBEK` | No-damage mode (published as "infinite lives") | `0x02000004` bit0: 0x00 → 0x01 |
| `OLEGSGIZMO` | All gadgets available | `0x02000004` bit1: 0x00 → 0x02 |
| `SMASHROBOT` | Extra levels | no flag byte; state=2 → `0x080039E8` path; on-screen "EXTRA LEVELS!" |

**Alphabets:**
- Cheat/keyboard alphabet (41): `0123456789abcdefghijklmnopqrstuvwxyz%$£&*` @ `0x08024850`.
- Password alphabet (36): `0123456789%bcd$fgh£jklmn&pqrst*vwxyz` @ `0x0802512C`. Vowels are removed and the five symbols are inserted at positions 10,14,18,24,30.
- Keyboard-reachable subset (31): same 36 with those 5 symbol positions skipped (`0x08003F62`–`0x08003F80`).

**Published password verification (ROM truth):** 19 of 22 accepted. Rejected by the ROM under all plausible transcriptions: `1434$ 100£8` (1-7), `18YJS 26BP4` (2-2), `ZZZQC 26C4Z` (2 boss). These are published-list errors (or a different edition); they are not in the ROM's accepted set.

## 6b. Enumeration

**Cheat system:** space = exactly 3 strings (one 12-byte record each at `0x080248A4/B0/BC`, three `strcmp` sites). No other 10-character input is accepted — confirmed on-screen by arbitrary input ("WRONG CODE"). This is a closed set, so no unpublished code can exist; the equivalent §0.2 deliverable is the proof that the table and validator contain exactly three entries.

**Password system:**
- Alphabet 36 symbols; length 10; structure 6+3+1 base-36 symbols.
- Nominal input space `36^10 ≈ 3.66×10^15`; keyboard-reachable space `31^10 ≈ 8.19×10^14`.
- Payload bits: `A` supplies an 11-bit low field (`S[0]`, level index = `S[0]>>8`), a 12-bit scattered field, and small gadget/flag fields; `B` supplies chapter (2 bits, values 0–2), sub-level (7 bits, chapter-bounded) and a 6-bit field. Check symbol = ~5.17 bits derived from a 9-character additive hash. For each 9-character prefix there is essentially one valid check symbol, so the accepted set is on the order of `36^9`; the range checks remove payloads whose decoded fields exceed the chapter/field bounds (a random 6-symbol prefix nearly always fails — a 144-prefix sample with fixed tail produced 0 accepted).
- **Novel code (in no published list):** `DBJJZ 00011` (lower-case in ROM buffer: `dbjjz00011`). Generated by mutating the level field of `DBGJZ 00014` and solving the check symbol with the Unicorn oracle over the ROM's own validator. Decoded fields: level index **28** (published maximum is 27), chapter 0, sub 1, state struct `[152,28,0,0,3,0,5,1,0,1,5,0,…]`. Entered on the real INSERT PASSWORD screen: accepted, transitioned to the level map with `PARK FREE`, counter **25**. RAM proof: struct bytes present at `0x020000E8` with `level=28`. By contrast the published `DBGJZ 00014` gives counter 30 on the same screen.
- **Bounds by rejection:** `DBJJZ 00010` (identical payload, wrong check symbol) → `WRONG PASSWORD!` on the real screen. Out-of-range chapters/sub-levels are rejected by `0x0800CD3C` (e.g. chapter 2 with sub > 11, chapter value 3).

## 7. Validation evidence

- **Observed (emulator):** all three cheat codes accepted with the three distinct on-screen messages; flag byte `0x02000004` changed 0→1 and 0→2; `SMASHROBOT` showed "EXTRA LEVELS!". Novel password accepted to a gameplay map; published password accepted to a different counter; wrong-check password showed "WRONG PASSWORD!". Screenshots are kept in `/tmp/princessnatasha/` (not attached).
- **Observed (RAM/savestate):** decoded level-28 struct at `0x020000E8`; cheat flag byte transitions; input buffers in IWRAM.
- **Derived (disassembly):** the three `strcmp` sites, the 36-symbol alphabet and base-36 parse, the additive hash and check-symbol comparison, the struct unpacking and all range checks, the generator at `0x0800CF00`.
- **Oracle (Unicorn):** the ROM's own validator at `0x0800CDBC` executed over thousands of inputs; it accepted 19/22 published passwords and the novel code, rejected the three bad published entries and every wrong-check mutant.
- **Inferred:** exact gameplay semantics of some decoded fields (gadget mask, `S[0xa]` counter) are named from their effect on the map screen, not fully traced to their readers.

## 8. Unknowns

- The precise gameplay meaning of every byte in the 20-byte state struct was not traced to all of its readers; the labels used are conservative.
- Five password-alphabet symbols are accepted by the validator but unreachable through the stock on-screen keyboard; whether the developers intended a separate entry path was not established.
- The three rejected published passwords may be valid for a different regional revision; only this `BNPE` image was tested.
- No hidden debug/menu screen was found in the reachable menus (EXTRAS, PLAY/NEW, PLAY/CONTINUE, OPTIONS and their sub-screens); this is a bounded negative over the menu graph and the `strings` text bank, not a proof about unreachable code.

## 9. Tooling

- `arm-none-eabi-objdump`, Capstone (`mydis.py`), custom Thumb PC-relative-LDR and BL scanners (`scanldr.py`, inline Python).
- Unicorn Engine 2.1.4 oracle harness (`uc_fast.py`) loading the 4 MiB ROM at `0x08000000` and calling `0x0800CDBC` with a synthetic stack; ~5 ms per trial.
- mGBA savestate RAM reader (`savestate.py`) and `gbAs`-chunk patcher (`patchss.py`) for deterministic input-buffer injection and RAM diffing.
- mGBA under Xvfb `:318` with `SDL_AUDIODRIVER=dummy`; `xdotool` for input; `scrot`/ImageMagick for screenshots.

**Legal note:** no ROM bytes, graphics, audio, or extracted game text are redistributed here; only addresses, hashes, algorithms, and self-generated codes are published.
