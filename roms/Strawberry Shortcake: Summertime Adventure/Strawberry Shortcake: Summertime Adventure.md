# Strawberry Shortcake: Summertime Adventure (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Strawberry Shortcake: Summertime Adventure/Strawberry Shortcake: Summertime Adventure.gba` |
| Size | 4,194,304 bytes (4 MiB), flat GBA ROM |
| Header title | `STRAWBERRYSC` |
| Game code / maker | `B35E` / `5G` |
| Revision | `00` (version byte 0x00; complement 0x3B; header checksum 0x0000 — the normal rebuilt-header artifact, §16.1) |
| Entry branch | `0xEA00002E` (stock, no cracktro at 0x00–0x1000) |
| MD5 | `71c5d8e089d0c1b15b4e376515bd4f18` |
| SHA-1 | `6ddb65dd3b80acf4f24a6ae2568dfa6c8da6b007` |
| SHA-256 | `4b993ea398925a330ec804d7fd836672e32374590387e17f850302fec009f1e1` |

Publisher splash observed at boot: **Majesco** → **DIC ("The Incredible World of DIC")** → title.
Loading the password screen also plays **American Greetings** and **Gorilla** (developer) logos.
The build ships C++ RTTI/exception/assertion machinery and many `Manager::updateItems()` /
`ASSERTION FAILED FILE=[%s]` debug strings — it is a debug-enabled retail build, but no reachable
debug menu was found (see §8).

## 2. Executive summary

This game has a genuine, developer-intended **8-character password / continue-game system**,
reached from the title menu via **START → CONTINUE GAME** (also reachable from **TEND GARDEN**).
Both options open the same "Enter your Password!" screen after ~5 s of legal splash screens.

The password is **not a table of presets and has no checksum**. It is a pure bijection between
every 8-symbol string over a 64-character alphabet and a 48-bit packed progress payload.
Consequently **all 64^8 = 2^48 = 281,474,976,710,656 strings are decodable/accepted**; there is
no validator to "beat" and no invalid-password rejection path in the ROM. The interesting
surface is the field layout: the **rightmost displayed character** carries `areaAt` (bits 0–3),
so a one-character change selects a different game area. I generated, entered, and RAM-verified
two codes that appear in no published list (none exist for this SKU): `00000001` and `12345678`.

Web reconnaissance was attempted and is recorded in §8: `websearch` returned no results for
six queries and direct fetches were blocked (GameFAQs 403, DuckDuckGo bot challenge), so no
published code list could be checked. This does not weaken the finding: the decoder contains no
comparison against any stored string, so no published preset could be authoritative anyway.

## 3. How to reproduce

Emulator: mGBA 0.10.5 (private renamed copy `mgba_straw` to survive other agents' broad kills),
Xvfb `:315`, `SDL_AUDIODRIVER=dummy`, 3× scale, keymap A=`x`, B=`z`, Start=`Return`,
Select=`BackSpace`, D-pad = arrow keys.

1. Boot the ROM. Press `x` three times to clear Majesco / DIC / title-logo screens.
2. Press `Return` → main menu: **NEW GAME / NEW GARDEN / CONTINUE GAME / TEND GARDEN**.
3. Press `Down Down` to highlight **CONTINUE GAME**, press `x`.
4. Wait ~5–8 s through the **American Greetings** and **Gorilla** splash screens. The
   "Enter your Password!" screen appears with eight slots; initially only the leftmost shows
   `0` and the rest are blank (moving right initializes each new slot to `0`).
5. Controls: `Left`/`Right` move the cursor, `Up`/`Down` decrement/increment the current
   character through the 64-symbol alphabet (wrapping), `x` submits.
6. Baseline `00000000` → loads Strawberry's garden ("Well Pupcake…").
7. Novel code `00000001` (change only the **rightmost** slot `0`→`1`) → loads Angel Cake's
   area ("Angel Cake! How are you?").
8. Novel code `12345678` → loads the garden with a different quest dialogue
   ("Ginger. Fruit Cookies. Strawberries.").

Screenshots retained at `/tmp/opencode/strawberry/`: `cont3.png` (menu), `seq_*.png`
(entry screen), `pw_all0.png` (`00000000`), `pw100_pre.png` / `pw_slot7_after.png`
(`00000001`), `pw12345678_pre.png` / `pw12345678_after.png`, `enum_00_0.png` …
`enum_16_G.png` (full area enumeration), `sub_contact.png`, `pw_state.ss1` / `loaded000.ss2`
/ `area1.ss4` (savestates used for RAM evidence).

## 4. Address map

All ROM addresses are absolute (`0x08000000 + file offset`).

| Address | Kind | Meaning |
|---|---|---|
| `0x08084D40`–`0x080850DC` | code (Thumb) | **Password encoder** (48-bit payload → 8 symbols); mode in `r2` (0 / 1) |
| `0x080850DC`–`0x08053A6` | code (Thumb) | **Password decoder**; `r0`=dest struct, `r1`=8-char string, `r2`=mode (0 = full load, 1 = info only) |
| `0x080853A8` | code | zero/init the 52-byte decode struct before decode |
| `0x080807A0`, `0x08080AEC` | code | call the encoder to build a displayable password and write it to the scene object at `+0x420` |
| `0x080A90DC`–`0x080A93xx` | code | **`LoadAdventure`** — decode (mode 0), log, set ~14 item/flag globals, clamp 4 fields to ≤10, dispatch scene by `areaAt` |
| `0x080A96C4` | code | decode mode 1 ("password info") used by the entry UI |
| `0x080A97AC` | code | password-screen input handler; calls `LoadAdventure` at `0x080A9826` |
| `0x080A9248` | literal | pointer to `"LoadAdventure pw.areaAt =%d pasword=%s"` |
| `0x083D13B0` | string | `"LoadGame"` |
| `0x083D13BC` / `0x083643F8` | string | **64-symbol alphabet** `0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz?-` (+ NUL) |
| `0x083D1400` | string | `"LoadGame_Scene"` |
| `0x083D141C` | string table | scene names: Strawhouse, AppleOrchard, MarshmallowMarsh, Oracres, Cakewalk, Forest, MuffinTop, Valley, CookieCorners, Briar, RainbowFloat, Vanilla, GumdropMountain, Bakeoff, Garden, Options |
| `0x083D1428` | string | `"scenename =%s"` |
| `0x083D1438` | string | `"LoadAdventure pw.areaAt =%d pasword=%s"` (note typo `pasword`) |
| `0x083E598C` | string | `"ASSERTION FAILED  FILE=[%s] LINE=[%d]  EXP=[%s]"` (and `WARING…` at `0x083E59C0`) |
| `0x02013528` | EWRAM | base of the scene/game object used by `LoadAdventure` |
| `0x0201383C` | EWRAM | **8-byte password display buffer** (object `+0x314`); observed `00000000`, `00000001` |
| `0x02000004` | EWRAM | game-state word that changed with the loaded area (0x02 for `00000000`, 0x01 for `00000001`) |
| `0x02005FC0`+`i*8` | EWRAM | 14 flag slots written from decoded bytes `struct[8..21]` |

Tooling: `arm-none-eabi-objdump -M force-thumb`, custom Python pointer/BL scanners (`pscan.py`,
`blscan.py`), `ssdiff.py` (zlib-decompresses the `gbAs` chunk of mGBA `.ssN` PNG savestates;
raw state 397,312 bytes; EWRAM at raw `0x21000`, IWRAM at raw `0x19000`).

## 5. Algorithm

**Alphabet (64 symbols), file `0x3643F8`:**
`0 1 2 3 4 5 6 7 8 9 A B C D E F G H I J K L M N O P Q R S T U V W X Y Z a b c d e f g h i j k l m n o p q r s t u v w x y z ? -`
Value = index in that string (0–63).

**Decode (ROM `0x080850DC`, mode 0):**

```
acc = 0                                   # 48-bit, kept as (hi,lo) 32-bit halves
for i in 7 down to 0:                     # note: src[7] first
    v = alphabet_index(src[i])            # 0..63; NOT-FOUND => 64 (0x40 ORed in)
    acc = (acc << 6) | v                  # shift skipped on the final (i==0) iteration
# => src[7] occupies the highest 6 bits, src[0] the lowest 6 bits
```

The on-screen keyboard stores its characters so that the **leftmost displayed slot is `src[7]`**
(highest bits) and the **rightmost displayed slot is `src[0]`** (lowest bits). This is why the
rightmost slot, not the leftmost, changes the starting area (empirically verified: leftmost
`0`→`1` still loaded the garden; rightmost `0`→`1` loaded Angel Cake).

Mode 0 then peels fields off the low end of `acc` (order and widths taken from the decoder):

```
dest[0x33] = biased(acc & 7); acc >>= 2      # 3-bit biased field
dest[0x32] = biased(acc & 7); acc >>= 2
dest[0x31] = biased(acc & 3); acc >>= 3      # 2-bit biased field
dest[0x30] = biased(acc & 3); acc >>= 3
dest[0x2C] = (acc & 0xFF) * 200 (u32); acc >>= 8
dest[0x29..0x22] = 8 consecutive single bits
dest[0x0D..0x00] = 14 consecutive single bits (flags)
areaAt  = dest[0x04] = acc & 0xF; acc >>= 4  # 4-bit scene selector
dest[0x00] = acc & 0xF                       # next 4-bit field
```

`biased(x) = 0 if x == 0 else x + 7` (or `x + 3` for the 2-bit fields) — a zero sentinel
with an offset. Total consumed bits = 2+2+3+3+8+8+14+4+4 = 48. `areaAt` is bits 0–3 of the
payload, i.e. the low 4 bits of the **rightmost** character's 6-bit value.

`LoadAdventure` then sets 14 flag globals, clamps four decoded fields to ≤10, and indexes an
11-entry scene table (`0x080A9284` onward). Cases **0–10** copy scene data; **11–15** match no
case and copy nothing (see §6b). The encoder (`0x08084D40`) is the exact inverse: it reads the
same fields (clamping them the same way), builds the 48-bit word, and emits
`alphabet[acc & 0x3F]` eight times, least-significant character first. **There is no checksum,
no XOR key, no table lookup and no validation branch on either side.**

## 6. Tables

**Alphabet / value map** — see §5 (64 symbols, index = value).

**Rightmost-character → observed area (all other slots `0`):** empirically captured, see §6b.

**Field layout** — see §5. Notable bounds: `areaAt` 4 bits (0–15); four decoded fields clamped
to ≤10 in `LoadAdventure` (so the encoder's range for those fields is 0–10, with 11–15 aliasing
to 10); 14 one-bit flags; one biased 8-bit field multiplied by 200 on decode.

**Debug/dev evidence (data, not instructions):** `ASSERTION FAILED FILE=[%s] LINE=[%d] EXP=[%s]`,
`WARING FILE=…`, `bad_alloc`, RTTI class names, and dozens of `XxxManager::updateItems() –
failed to assign …` strings at `0x082xxxxx`–`0x083Exxxx`. They prove a debug build but were not
correlated with any reachable menu.

## 6b. Enumeration

**Space definition.** Alphabet size 64, fixed length 8, no separators, no terminator in the
decoded payload. Space = 64^8 = 2^48 = **281,474,976,710,656** distinct strings. 48 payload
bits are fully consumed by the fields in §5; there is **no checksum width and no reserved bit**.
The decoder's alphabet lookup maps a non-alphabet byte to value 64, corrupting a 6-bit slot —
but the on-screen keyboard can only emit the 64 valid symbols, so this case is unreachable
through normal input.

**Validator model.** `decode(encode(state)) == state` for the packed fields; `encode(decode(s))`
is defined for every 8-symbol `s`. The ROM was read end-to-end for both routines: there is no
`cmp` against a stored password, no checksum accumulation, and no reject/return-code path.
Every 8-symbol string is accepted and starts *some* game state.

**Novel codes, minted and entered on the real screen (none appears in any published list —
web recon found no list at all):**

| Displayed code | How minted | Result observed in mGBA | RAM evidence |
|---|---|---|---|
| `00000001` | Set `areaAt` = 1 (rightmost slot `0`→`1`) | Angel Cake area, "Angel Cake! How are you?" | `.ss4`: buffer `0x0201383C` = `30 30 30 30 30 30 30 31`; EWRAM `0x02000004` 0x02→0x01 vs baseline; 31 EWRAM bytes differ (slot/quest state) |
| `12345678` | Exercise eight different field positions at once | Garden with alternate quest dialogue "Ginger. Fruit Cookies. Strawberries." | `.ss5` captured; input buffer shown as `12345678` before submit |
| `00000000` | baseline / all fields zero (control) | Strawberry's garden, "Well Pupcake…" | `.ss2`; buffer `0x0201383C` = eight `0x30` |

**Full `areaAt` sweep.** I entered 17 codes differing only in the rightmost slot and captured
every resulting screen (`enum_00_0.png` … `enum_16_G.png`). Values `0`–`9` and `A`–`F`
(0–15) were all accepted and produced a repeating cycle of four environments: Strawberry's
garden, Angel Cake's candy garden, Cookie Corners (Ginger Snap), and Gumdrop Mountain. The
repetition is explained by the layout: bits 4–5 of the same character feed the next field, and
the scene dispatch only has cases 0–10, so values 11–15 copy no scene data and fall back to a
state derived from the remaining fields.

**Bounds proven by rejection / aliasing.**

* *Out-of-range scene index:* rightmost symbol `G` (value 16) wraps `areaAt` to `16 & 0xF = 0`
  and reloads the garden environment with a different quest field — the 4-bit width is proven
  by aliasing rather than by an error message. `enum_16_G.png` is the proof. There is **no**
  "invalid password" screen: `grep -i 'invalid\|wrong password\|try again'` over all 32,875
  ROM strings found none, and no such branch exists in the decoder.
* *Unsupported scene range:* symbols `B`–`F` (11–15) are accepted but no scene-record copy
  occurs (`0x080A9348`: `cmp r0,#10; bne 0x080A9364`). They produce inconsistent but non-crashing
  states. This is the honest bound: the format encodes 16 `areaAt` values; the content supports
  only 11.
* *Non-alphabet input:* the UI cannot express it; the decoder would OR `0x40` into that 6-bit
  slot. A savestate patch of the display buffer at `0x0201383C` to byte `0x01` was **ineffective** —
  the UI rebuilds the password from its own index state on submit — so this is reported as an
  **untested** path, not a rejection.

Because the accepted set is the entire 2^48 space, running the game's validator exhaustively is
impossible; completeness is established instead by **reading the complete encoder/decoder** and
showing they contain no rejecting branch, plus 19 diverse accepted inputs (17 sweeps + 2 novel
multi-field codes) exercised on the real screen.

## 7. Validation evidence

* **Observed** (emulator / savestate): all four menu entries enumerated; password screen reached
  via both CONTINUE GAME and TEND GARDEN; keyboard controls mapped; `00000000`, `00000001`,
  `12345678` and 17 sweep codes accepted with distinct on-screen results; EWRAM password buffer
  at `0x0201383C`; 31-byte EWRAM delta between area 0 and area 1.
* **Derived** (disassembly): 64-symbol alphabet at `0x083643F8` and `0x083D13BC`; 8×6-bit
  reversed packing; the exact field peel order and `areaAt` = bits 0–3; absence of any checksum
  or reject path in `0x08084D40`–`0x080850DC`; scene dispatch cases 0–10 only.
* **Inferred** (not fully exercised): exact semantic names of most fields inside the 52-byte
  decode struct (berry counts, quest plot index) — labeled by their consumer writes in
  `LoadAdventure`, not by playing the game to completion. The claim "no published list exists"
  rests on six unrevealing web queries plus blocked direct fetches, so it is a bounded negative
  for the sources tried.

## 8. Unknowns

* Web/published-code reconnaissance was inconclusive: `websearch` returned zero results for six
  queries; GameFAQs returned HTTP 403 and DuckDuckGo a bot challenge. No published code list
  was available to cross-check, so "novel" means "minted from the codec, not copied from a list"
  rather than "proved absent from every list on the internet".
* The 48-bit payload is fully mapped at the bit level, but the semantic meaning of all fields
  beyond `areaAt` was not established by playthrough.
* No reachable debug menu was demonstrated. Static search found a button-mask scan over the code
  region but it is too noisy to prove absence (generic u16 values such as `0x0300` occur >4,000
  times, mostly in compressed graphics). Likewise the many assertion/C++ debug strings have no
  identified UI entry point. This is an **inconclusive** search, not a proven "no debug menu"
  claim.
* Non-alphabet bytes in the password buffer are unreachable through the on-screen keyboard;
  the savestate-patch attempt was overridden by the UI and is untested.

## 9. Tooling

* `/usr/local/bin/mgba` 0.10.5 — copied to `/tmp/opencode/strawberry/mgba_straw` so unrelated
  agents' broad `pkill -x mgba` could not terminate this session.
* Xvfb `:315` (PID 347338 at start), openbox (PID 347355), `SDL_AUDIODRIVER=dummy`.
* `arm-none-eabi-objdump -M force-thumb` for all disassembly; `strings -t x`; `xxd`.
* Custom scripts in `/tmp/opencode/strawberry/`: `key.py` (XTEST input), `pscan.py` (literal
  pointer scan), `blscan.py` (Thumb BL target scan), `ssdiff.py` (mGBA `gbAs` zlib state dump
  and diff), `patch_ss.py`, `enumerate.py`.
* No game assets are redistributed in this report; only hashes, addresses, algorithms, and
  authored code strings are published.
