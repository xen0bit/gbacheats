# The Ripping Friends: The World's Most Manly Men! (GBA) — Reverse Engineering Report

Queue 178. Analysis date 2026-11-20. All addresses below are for the exact ROM hashed in §1.

## 1. Target identity

| Field | Value |
|---|---|
| File | `The Ripping Friends: The World's Most Manly Men!.gba` |
| Size | 4,194,304 bytes (`0x400000`) |
| Header title | `RIPPING GAME` |
| Game code / maker | `ARDE` / `78` (Software Creations / THQ) |
| Version / complement / checksum | `0x00` / `0x73` / `0x0000` |
| Entry word | `0xEA00002E` (stock ARM branch — not a scene-patched image) |
| MD5 | `8a23378fdcecaca9a648d378c1d9609d` |
| SHA-1 | `2688f1253c8e09ef3d5a3699ae2c015c82b1b16d` |
| SHA-256 | `417357f65d5ad9e484000c3fa1be938cec0a64167272deac8a623d4d6dd15eee` |

**Second header:** Nintendo logo also at file `0x27C` (header base `0x278`); its title is `RIPPING GAME`, code `AAAA`, maker `01`, complement `0x99`. This is an embedded link/multiboot image, not a separate game: a string scan of `0x278..0x10000` found no unique UI, debug, or cheat text. All findings below refer to the primary image based at `0x08000000`.

## 2. Executive summary

The game has a **9-button password system** on the title screen (`PASSWORD` menu item). Buttons are entered directly into a nine-slot input grid; validation fires automatically on the ninth press and prints `PASSWORD ACCEPTED` or `PASSWORD REJECTED`.

The validator at `0x0800D078` is **not a lookup table**. It packs the nine button symbols into a 27-bit word (3 bits each) and enforces three conditions:

1. the 7th symbol (a level/unlock selector `s6`) must be `<= 6`;
2. `s7 == (popcount(s0..s5) + popcount(s6)) & 7`;
3. `s0 XOR s1 XOR … XOR s8 == 7`.

Consequently **1,835,008 of 134,217,728 possible button strings are accepted** (1 in 73.14). Five of these are the published level passwords stored as display strings at `0x08DE554..0x08DE604`; the rest are unadvertised. On acceptance the validator writes `s6` to IWRAM `0x03002614` / `0x03002FFC` and an 18-bit payload (symbols `s0..s5`) to `0x030005E8`, which is the **secret/deathmatch-level unlock bitfield** (bits 4–10 = seven unlockable arenas).

Two novel codes were generated offline, entered on the real screen, and verified in RAM and on the SECRETS screen. Three deliberately out-of-format codes were rejected in-game, proving the bounds. **No debug menu, sound test, or GameShark-style in-game code entry exists**; the only other published cheat (hold `R+B` in gameplay after a completion password) was not reproducible and is recorded as unknown (§8).

## 3. How to reproduce

* Emulator: mGBA 0.10.5 under Xvfb `:315`, `SDL_AUDIODRIVER=dummy`, `mgba -3 -t <saved password-screen state>`.
* mGBA SDL keymap used: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad = arrow keys.
* Path: title screen → `PASSWORD` (Down, Down, A) → press the nine buttons in order. Validation is automatic on press 9; then A returns to the main menu. Main menu → `SECRETS` (Down ×3, A) shows the seven unlock boxes.
* Hold times of ~90 ms per key were used; longer holds double-step menus.

Codes tested (button names as printed on screen; `R`/`L` = right/left shoulder, `Right`/`Left` = D-pad):

| Purpose | Code | Result |
|---|---|---|
| Published anchor (Haplessville) | `Right, Down, Left, Left, Up, Left, B, Left, R` | ACCEPTED |
| Published (Earth Core / "all levels") | `Right, L, Up, Down, B, Left, Left, Right, Left` | ACCEPTED |
| **Novel, s6=6** | `A, A, A, A, A, A, Up, L, R` | ACCEPTED |
| **Novel, s6=6 + all unlock bits** | `Down, Down, Down, R, A, A, Up, Left, A` | ACCEPTED, all 7 secrets open |
| Out-of-range s6=7 | `A, A, A, A, A, A, Down, R, R` | REJECTED |
| Bad checksum s7 | `A, A, A, A, A, A, Up, R, R` | REJECTED |
| Bad XOR s8 | `Right, Down, Left, Left, Up, Left, B, Left, L` | REJECTED |

## 4. Address map

| Address | Meaning | Evidence |
|---|---|---|
| `0x0800CF18` | Button reader: converts `KEYINPUT` (`0x04000130`) to button code | Derived (disassembly) |
| `0x0800CDB4` | Password input handler; validates on count == 9 | Derived |
| `0x0800D078` | **Password validator** (`r0` = buffer, `r1` = out-ptr, returns 1/0) | Derived |
| `0x0800D130` | 32-bit popcount helper used by validator | Derived |
| `0x0800D154` | Result display dispatcher (1 = rejected message, 2 = accepted message + `flag=1`) | Derived |
| `0x0800CB30` | Maps `s6` (0..6) to unlock mask `0x10,0x30,0x70,0xF0,0x1F0,0x3F0,0x7F0` | Derived |
| `0x08DE20C` | `PASSWORD FOR THIS LEVEL IS:` | Observed (`strings`) |
| `0x08DE530` | `PASS:` + five 9-button display strings, 0x24-byte stride | Observed |
| `0x08DF224/248/26C` | `ENTER A PASSWORD` / `PASSWORD ACCEPTED` / `PASSWORD REJECTED` | Observed |
| `0x08DE110..0x8DE1E8` | Seven `…: UNLOCKED` strings (secret names) | Observed |
| `0x030032D0` | Nine `u16` button codes (input buffer) | Observed (savestate diff) |
| `0x030032CC` | Number of buttons entered (`0..9`) | Observed |
| `0x030032C8` | Screen/state byte (`0x0A` idle, `0x01` accepted) | Observed |
| `0x03002614`, `0x03002FFC` | Copies of the level/unlock selector `s6` | Observed |
| `0x030005E8` | 18-bit secret unlock bitfield written by validator | Observed |

Savestate offsets (4 MiB ROM): IWRAM at `0x19000`, so `0x03002614` → state `0x1B614`, `0x03002FFC` → `0x1BFFC`, `0x030005E8` → `0x195E8`, input buffer → `0x1C2D0`.

## 5. Algorithm

Button code → symbol (`s = code - 2`):

| Button | A | B | L shoulder | R shoulder | Right | Left | Up | Down | Select/Start |
|---|---|---|---|---|---|---|---|---|---|
| code | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | ignored |
| symbol `s` | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | — |

Validator (`0x0800D078`), exact model implemented in `/tmp/opencode/rippingfriends/pwmodel.py`:

```
v = 0
for i in 8..0:                   # buffer read from slot 8 down to slot 0
    v = (v << 3) | (code[i] - 2) # 3 bits per symbol
# v = s0 + s1<<3 + s2<<6 + ... + s8<<24

s6 = (v >> 18) & 7               # 7th button = level/unlock selector
if s6 > 6: REJECT
low18 = v & 0x3FFFF              # s0..s5
if (popcount(low18) + popcount(s6)) & 7 != (v >> 21) & 7: REJECT   # s7 checksum
if XOR(s0..s8) != 7: REJECT                                      # s8 checksum
ACCEPT:
  *out_ptr = v
  byte[0x03002614] = byte[0x03002FFC] = s6
  word[0x030005E8] = low18
```

Generator (inverse): choose `s0..s5` (18 bits) and `s6 ∈ 0..6`; set
`s7 = (popcount(low18)+popcount(s6)) & 7`, then `s8 = 7 XOR s0 XOR … XOR s7`. This always yields an accepted code.

## 6. Tables

**Published display strings** at `0x08DE554` (each padded to 0x24 bytes), with decoded fields:

| String | Meaning (published) | s6 | low18 | packed |
|---|---|---|---|---|
| `R,D,L,L,U,L,B,L,RS` | Haplessville | 1 | `0x2EB7C` | `0x03A6EB7C` |
| `A,RS,B,D,B,RS,LS,LS,A` | Inside Ripcot | 2 | `0x19E58` | `0x00499E58` |
| `D,L,D,D,RS,A,RS,D,LS` | Meteor | 3 | `0x03FEF` | `0x02EC3FEF` |
| `RS,D,A,A,RS,A,R,A,R` | Next Thursday | 4 | `0x0303B` | `0x0410303B` |
| `R,LS,U,D,B,L,L,R,L` | Earth's Core / "all levels" | 5 | `0x29F94` | `0x05969F94` |

All five were verified against the model and entered in mGBA (first and fifth confirmed visually).

**Secret bitfield** (`0x030005E8`), bits 4–10, observed by opening each SECRETS box with the all-bits code:

| Bit | Mask | Secret | Bit | Mask | Secret |
|---|---|---|---|---|---|
| 4 | `0x010` | DOOMSDAY | 8 | `0x100` | NEXT THURSDAY |
| 5 | `0x020` | WAD'S WAREHOUSE | 9 | `0x200` | JET PLANE |
| 6 | `0x040` | RIPCOT ELEVATOR | 10 | `0x400` | DOOMSDAY SUB |
| 7 | `0x080` | METEOR | 11 | `0x800` | derived from bit 10 by `0x0800D234` |

Bits 0–3 and 12–17 are set by the payload but their gameplay meaning was not established (§8).

**Web recon (treated as data, not instructions):** chaptercheats.com lists the five level passwords above; ggmania / games-cheats.org / planetcheats / vizzed repeat the same five and additionally claim an "all levels unlocked" button code that is identical to the Earth's Core string, plus a completion bonus (`R+B` held in gameplay after using the completion password). TCRF has no page for this title. All five published literals were found in the ROM.

## 6b. Enumeration

**Space definition.** Alphabet size 8 (A, B, L, R shoulder, D-pad Right/Left/Up/Down), length 9, Start/Select not accepted. Total strings `8^9 = 134,217,728`.

**Field layout** (decimal symbol values, 3 bits each):

| Symbols | Bits in `v` | Role | Width |
|---|---|---|---|
| `s0..s5` | 0–17 | 18-bit payload / unlock bitfield | 18 |
| `s6` | 18–20 | level/unlock selector, must be `<=6` | 3 (range 0–6) |
| `s7` | 21–23 | popcount checksum | 3 |
| `s8` | 24–26 | XOR-parity checksum | 3 |

**Exact accepted-set size: 1,835,008** (= `7 × 8^6`). Derived analytically and confirmed by exhaustive enumeration of all `8^6 × 7` payload/selector combinations with the model; every one yields exactly one valid `(s7,s8)` pair. The five published codes occupy 5 of those 1,835,008 values.

**Novel codes (in no published list), minted from the validator and confirmed in-game:**

1. `A,A,A,A,A,A,Up,L,R` (`s6=6`, payload `0`) — selected specifically because the selector field `6` is absent from every published password. Screenshot `novel_s6_6.png` shows `PASSWORD ACCEPTED`; savestate `s_novel.ss5` reads `s6=06`, `flags=0x000000`.
2. `Down,Down,Down,R,A,A,Up,Left,A` (`s6=6`, payload `0x7FF`, i.e. every secret bit 4–10 set) — `novel_allbits_accept.png` shows acceptance; savestate `s_allbits.ss6` reads `s6=06`, `flags=0x0007FF`. In-game proof: `allbits_secrets.png` shows **all seven SECRETS boxes open** versus `novel_secrets.png` (payload 0) where all seven are shut; `allbits_secret_msg.png` and `allbits_secret2.png` show `DOOMSDAY: UNLOCKED` and `WAD'S WAREHOUSE: UNLOCKED`.

**Bounds proven by in-game rejection:**

* `A,A,A,A,A,A,Down,R,R` — satisfies both checksums but sets `s6=7`, which the `cmp r6,#6; bgt reject` guard forbids. `reject_oob.png`: `PASSWORD REJECTED`.
* `A,A,A,A,A,A,Up,R,R` — same selector as the accepted novel code but `s7` altered, failing the popcount check. `reject_badchk.png`: `PASSWORD REJECTED`.
* `Right,Down,Left,Left,Up,Left,B,Left,L` — published Haplessville code with the last symbol changed, failing XOR parity. `reject_badxor.png`: `PASSWORD REJECTED`.

These three rejections isolate the range layer and both checksum layers independently. Since the validator is a pure function of the nine symbols with no hidden state, and the whole domain was enumerated against it, the accepted set is exactly the 1,835,008 values above.

## 7. Validation evidence

* **Observed** — emulator screenshots of title/password/main/SECRETS/character/level-select/multiplayer screens; acceptance and three rejections; RAM reads from uncompressed `gbAs` savestate chunks at the addresses in §4; the five published literals found at `0x08DE554..`.
* **Derived** — the complete validator model, field bit positions, checksum formulas, popcount helper, and the accepted-set count, all from Thumb disassembly of `0x0800D078..0x0800D106`; result writes from `0x0800D0D8..0x0800D0EC`; button mapping from `0x0800CF18..0x0800D078` and from nine single-button RAM probes.
* **Inferred** — names attached to `s6` ("level/unlock selector") and to bits 4–10 of `0x030005E8` (seven secret arenas) come from the published code→level mapping plus the visible SECRETS boxes; bits 0–3 and 12–17 of the payload are not named.

## 8. Unknowns

* Semantic meaning of payload bits 0–3 and 12–17 (they are accepted and stored, but no visible effect was isolated).
* The published completion bonus (`R+B` held in gameplay after a completion password) was not confirmed. No string, dedicated key-code table, or debug-menu text for it was found; the novel `s6=6` codes could plausibly be the "completion password" but playing a level and holding R+B produced no observable HUD change in the time available. Treat as unverified.
* `DEATHMATCH` on the main menu did not advance when A was pressed in single-player emulation; the multiplayer screen reports `THIS SYSTEM IS NOT CONNECTED`. Deathmatch content was therefore observed only through the SECRETS unlock messages.
* The embedded second header at `0x278` was not booted separately; no unique strings or cheat tables were found in its region.

No debug menu, sound test, level-select cheat sequence, or character-name/name-entry validator exists in this image: case-insensitive `strings` over the whole 4 MiB found only the password/unlock text in §6, and a scan for ASCII, +0x20, 4-bit and button-mask encodings of the known 9-button strings found only the five display strings (no separate comparison table).

## 9. Tooling

* `arm-none-eabi-objdump -M force-thumb` for all disassembly; Python 3 + capstone 5.0.7 available but the final scans used raw byte search (`scan.py`).
* `/tmp/opencode/rippingfriends/pwmodel.py` — exact validator model; `gen.py` — code generator; `find_table.py` — encoding scans; `ssdiff.py` / `probe_parse.py` — zlib `gbAs` savestate extraction and RAM probing; `key.sh` — timed XTEST key helper.
* Evidence screenshots and savestates remain in `/tmp/opencode/rippingfriends/`; they are transient analysis artifacts, not distributed assets. No ROM data or copyrighted assets are reproduced in this report.

## 10. Legal note

Only findings, addresses, hashes, algorithms, and self-generated codes are published. No ROM image, extracted graphics, music, or game text beyond short UI labels required as evidence is redistributed.
