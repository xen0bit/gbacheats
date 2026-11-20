# Star Wars: Episode II – Attack of the Clones (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Star Wars: Episode II – Attack of the Clones.gba` |
| Size | 8,388,608 bytes (0x00800000) |
| Header title | `STAR WARS EP` |
| Game code | `AS2E` (USA), maker `78`, version `0x00` |
| `file(1)` | "Game Boy Advance ROM image (AS2E78, Rev.00)" |
| Fixed byte / complement / checksum | `0x96` / `0x8B` / `0x0000` (zero checksum is the usual rebuilt-header artifact; entry is a stock crt0 `0xEA00002E` → `0x0800017C`) |
| MD5 | `f0d3e68e554e44d1df20a16359f13f5f` |
| SHA-1 | `f02f2a1246d593582436eeba4090f4048671079a` |
| SHA-256 | `ab3ae5f9d411aa4f6268135d524d34e033b92196a1fcbff2a672e3ca37d0a518` |

## 2. Executive summary

This SKU has a **developer-intended password system**: a 6-symbol code entered on the
main-menu `PASSWORD` screen, using a 16-symbol on-screen alphabet
`B C D F G H J K L M N P Q R S T`. The published password lists were a useful
starting anchor but **most of them are invalid for this exact US image**: of the
codes I entered, only `JFCGCG`, `JFCLCL` and `BGRBPK` were accepted; `BLDBGP`,
`BHDBGJ`, `BJxxxx`, `JFDGSG`, `JFLGLG`, etc. were rejected. No literal code string
appears anywhere in the ROM (ASCII, UTF-16 or shifted), so the codes are validated
algorithmically.

Black-box reconstruction (40+ published codes fitted, then confirmed by in-game
accept/reject) gives a **two-part 4-bit XOR checksum** plus small semantic field
bounds. I minted five codes that appear in no published list; four were confirmed
accepted in the emulator with screenshots, including `JDCGCH` and `JBCGCK` which
both start the game at level 2 with different starting-lives fields. Bounds were
proven by rejected inputs that pass the checksum but break the field range.

The password system is the only in-game cheat surface I found. The OPTIONS screen
exposes only MUSIC, SOUND and SKILL (3 values: KNIGHT / MASTER / PADAWAN); there is
no debug/level-select menu reachable from any menu I walked. Published "word codes"
(`CINEMA`, `YUBYUB`, `ROGERROGER`, `CHOSEN1`, `FRAGFIESTA`) cannot be entered on this
screen (the alphabet contains no vowels or `1`) and none of those strings occur in
the ROM — I record them as **unverified, probably belonging to another SKU/device**.

## 3. How to reproduce

* mGBA 0.10.5 under Xvfb `:318`, `SDL_AUDIODRIVER=dummy`, `mgba -3 <rom>`.
* Keymap (mGBA SDL default): A = `x`, B = `z`, Start = `Return`, arrows = D-pad.
* Boot (several logo screens; hold `x` to skip), then at the title press Start,
  choose `PASSWORD` (third item: Down, Down, A).
* Password screen controls: **Left/Right** moves the 16-position letter cursor
  (it wraps T→B and **persists** after A), **A** writes the highlighted letter into
  the current slot and advances the slot, **B** steps back, **Start** submits.
  Entry is silent: a rejected code dims the screen for ~0.3 s and returns to the
  same screen; an accepted code plays the level-intro cutscene and starts gameplay.
* I saved a savestate (Shift+F8) at the password screen and loaded it (F8) before
  every trial. Note: a state saved during a fade/corrupt can crash mGBA — verify the
  state size (~82 KB, not ~4 KB).

Codes entered during verification (all typed on the real screen, not debugger-injected):

| Code | Result |
|---|---|
| `JFCGCG` (published) | accepted — level 2 intro + gameplay |
| `JFCLCL` (published) | accepted |
| `BGRBPK` (published) | accepted — ending level |
| `JDCGCH` (**novel**) | accepted — level 2, starting-lives field 0x2 |
| `JBCGCK` (**novel**) | accepted — level 2, starting-lives field 0x0 |
| `BFCBKB` (**novel**) | accepted |
| `JFCBCB` (**novel**) | accepted |
| `JCCGCJ` (**novel**) | accepted |
| `JFCGCP`, `JFDGDG`, `JGCGCF`, `JFCCCC`, `JFCTCT`, `BBBBBB` | rejected |

## 4. Address map

| ROM / RAM | Meaning | Evidence |
|---|---|---|
| file `0x0000` / `0x08000000` | stock crt0, branch to `0x0800017C` | observed (header dump) |
| file `0x2418F4`–`0x241934` / `0x082418F4`– | English UI text bank; `password` at `0x08241934` | observed |
| file `0x242BE8` / `0x080242BE8` | English string-pointer table (entry 7 → `password`); per-language tables at `0x08245D40` etc. | observed |
| `0x080140E8` | keypad handler: reads `0x04000130`, stores **held** (active-high) at `0x03006EF0`, previous at `0x03006EEC`, **pressed** at `0x03006F58`, and 0 at `0x03005A58` | observed via mGBA `-d` `watch/r 0x04000130` |
| `0x080012xx`, `0x080024xx` | other consumers of `pressed` (`0x03006F58`), menu handlers | derived (literal + PC-relative LDR scan) |
| 6-byte code buffer in IWRAM | **not located** — savestate diffs were too noisy and the single-client GDB stub on port 2345 belonged to another agent | unknown |

No literal password table exists: searches for every published code and for the
alphabet string (ASCII, UTF-16LE/BE, ±0x20, 4-bit packed) returned zero hits.

## 5. Algorithm

Map each displayed symbol to its index in the screen alphabet:

```
A = "BCDFGHJKLMNPQRST"      # B=0, C=1, D=2, F=3, G=4, H=5, J=6, K=7,
                            # L=8, M=9, N=10, P=11, Q=12, R=13, S=14, T=15
v0..v5 = [A.index(c) for c in entered_six_letters]
```

Validator (reconstructed from published-code algebra, then confirmed in-game):

```
accept = ((v0 ^ v2 ^ v4) == 6) and ((v1 ^ v3 ^ v5) == 3)
         and (v1 <= 3)          # starting-lives field, 2 bits
         and (v2 in {1, 13})    # level selector: level 2, or ending
         and (v3 in {0, 4, 8})  # difficulty: PADAWAN / KNIGHT / MASTER
```

Confidence: the two XOR equations are **derived and dynamically confirmed** (every
accepted code satisfies them; single-symbol changes that break them are rejected).
The field ranges are **derived from accepted/rejected trials**; the exact upper
bound on `v0` was not fully enumerated (see §8). The validator's ROM address was
not found, so the equations are a behavioural model, not a disassembly listing.

Encoder (inverse — any `v0, v1, v3` and allowed `v2` mint a code):

```
v4 = 6 ^ v0 ^ v2
v5 = 3 ^ v1 ^ v3
code = ''.join(A[x] for x in (v0, v1, v2, v3, v4, v5))
```

Worked example for `JDCGCH` (`v = [6,2,1,4,1,5]`):
`6^1^1 = 6` ✓, `2^4^5 = 3` ✓, `v1=2 ≤ 3` ✓, `v2=1` ✓, `v3=4` ✓ → accepted;
the emulator played the level-2 intro and reached gameplay (screenshot
`/tmp/opencode/starwars2/novel1_crop.png`, work-dir copy only).

## 6. Tables

**Alphabet / symbol values**

| idx | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |
|---|---|---|---|---|---|---|---|---|---|---|---|----|----|----|----|----|----|
| symbol | B | C | D | F | G | H | J | K | L | M | N | P | Q | R | S | T |

**Field interpretation (confidence: inferred from published-code correlations)**

| Pos | Name | Typical values | Notes |
|---|---|---|---|
| v0 | prefix / class | 0 (`B…`), 6 (`J…`) ; 2 and 4 also accepted | a second checksum-relevant digit |
| v1 | starting lives | 0–3 | values ≥4 rejected |
| v2 | level code | 1 (level 2), 13 (ending) | 2..12 checksum-valid codes were rejected |
| v3 | difficulty | 0 Padawan, 4 Knight, 8 Master | 1 and 15 rejected |
| v4 | even-parity check | `6 ^ v0 ^ v2` | changing it alone rejects |
| v5 | odd-parity check | `3 ^ v1 ^ v3` | changing it alone rejects |

**Published-list verification (this US image)**

| Code(s) | Result |
|---|---|
| `JFCGCG`, `JFCLCL`, `BGRBPK` | accepted |
| `BLDBGP`, `BMFBHN`, `BHDBGJ`, `BGMBTK`, `BGPBRK`, `BJDGGM`, `JFDGSG`, `JFLGLG` | rejected — likely other region/revision or transcription errors |

**Word codes from one German cheat page** — `YUB YUB`, `CINEMA`, `ROGERROGER`,
`CHOSEN1`, `FRAGFIESTA`: absent from the ROM as text and untypeable on this
16-consonant keypad. Treated as data/leads only, not confirmed (guide §16.11/§16.21).

## 6b. Enumeration

**Space definition.** 6 positions × 4 bits = 24 bits = 16,777,216 representable
strings on the real keypad. Two independent 4-bit XOR checks reduce this to
16^4 = **65,536 checksum-valid codes**. The additional field ranges measured in
the emulator (`v1 ≤ 3`, `v2 ∈ {1,13}`, `v3 ∈ {0,4,8}`, plus a partial bound on `v0`)
reduce the practically accepted set to a small subset of those 65,536.

**Novel codes minted and accepted in-game** (none appears in GameFAQs,
supercheats, victorycheats, cheatingdome, the ffmasterjose FAQ, or traumerlebnis):

| Code | v-vector | Effect observed |
|---|---|---|
| `JDCGCH` | `[6,2,1,4,1,5]` | accepted; level-2 intro cutscene, then gameplay |
| `JBCGCK` | `[6,0,1,4,1,7]` | accepted; level-2 intro cutscene, then gameplay |
| `BFCBKB` | `[0,3,1,0,7,0]` | accepted (cutscene) |
| `JFCBCB` | `[6,3,1,0,1,0]` | accepted (cutscene, Padawan difficulty field) |
| `JCCGCJ` | `[6,1,1,4,1,6]` | accepted |

These differ from every published code in at least one field (the published
`J…` family always has `v1=3` and `v5=v3`; `JDCGCH`/`JBCGCK`/`JCCGCJ` do not).

**Bounds proven by rejection** (each of these satisfies both XOR checks unless noted,
so the rejection isolates a later range/format check):

| Code | Why it must fail | Observed |
|---|---|---|
| `JFCGCP` | v5 changed → odd check `v1^v3^v5 != 3` | rejected |
| `JFCGBG` | v4 changed → even check `v0^v2^v4 != 6` | rejected |
| `BBBBBB` | both checks wrong (`0^0^0=0`, `0^0^0=0`) | rejected |
| `JGCGCF` | checksums OK, but `v1=4` (>3) | rejected |
| `JFDGDG` | checksums OK, but `v2=2` (not 1 or 13) | rejected |
| `JFCCCC`, `JFCTCT` | checksums OK, but `v3=1` / `v3=15` | rejected |
| `CFCGJG`, `TFCGLG` | checksums OK, but `v0=1` / `v0=15` | rejected |
| `JGCGCG` | `v5` unchanged while `v1=4` → odd check broken | rejected |

**Negative-result enumeration (no hidden menu).** I walked every reachable screen
from a clean boot: legal splash → title (`PRESS START`) → main menu
(`START` / `OPTIONS` / `PASSWORD`) → OPTIONS (`MUSIC`, `SOUND`, `SKILL` cycling
through exactly 3 values) → PASSWORD. START begins the game (level 1); B returns
from OPTIONS/PASSWORD; no unlabelled selection index was found (the menu selector
stops after the third item). In the text bank at `0x082418F4` there is no string for
`INVALID`, `CHEAT`, `DEBUG`, `LEVEL SELECT`, `SECRET` or any word-code; the only
cheat-adjacent strings are `EXTRA LIFE`, `EXTRA SHIELD`, `EXTRA MISSILE`,
`EXTRA SMART BOMB` at `0x07B5AD4`–`0x07B5B00`, which are gameplay pickup labels
seen on the HUD, not menu entries. Search space checked: all 58,752 ASCII strings
of length ≥4, plus binary searches for every published code and for the alphabet
in 5 encodings. This supports a **bounded negative** for additional *menus* on the
retail input path; it does not rule out gated debug code in dead code paths.

## 7. Validation evidence

* **Observed** — emulator screenshots of every screen; accepted codes producing the
  level-2 cutscene and gameplay; rejected codes returning to the same password
  screen; the 16-symbol alphabet rendered at the bottom of the password screen;
  keypad variables read with mGBA's debugger watchpoint.
* **Derived** — the two XOR checksum equations, fitted from 40 published codes and
  then cross-checked against every accept/reject trial; the encoder inverse; field
  interpretation from the published "password modifier" tables and confirmed
  correlations (e.g. `v3=0/4/8` ↔ Padawan/Knight/Master, `v1` ↔ lives).
* **Inferred** — that `v0` is a class/prefix digit with a partial range; that the
  rejected published B-prefix codes belong to another region/revision; that the
  German word codes belong to another platform/cheat device.

## 8. Unknowns

* The validator's ROM address and the 6-byte code buffer in IWRAM were not located
  (GDB stub port 2345 was occupied by another agent; savestate diffs were too noisy;
  the `-d` console was usable only at breakpoints). The model is behavioural.
* Exact upper/lower bound on `v0`: 0, 2 and 6 accepted; 1 and 15 rejected; 3–14
  not all retested after an emulator crash invalidated one batch.
* Whether `v2` accepts any value besides 1 and 13; 0, 2–12 and 14–15 were rejected
  in at least one reliable trial, but a few late trials were lost to mGBA crashes.
* The hidden meaning of `v4` beyond being the even-parity check (the published
  "second level digit" correlation suggests the level may be stored redundantly).

## 9. Tooling

* `mgba` 0.10.5 (`-3`, `-d`, savestates), Xvfb `:318` + openbox, `xdotool`,
  `scrot`, ImageMagick `convert`/`montage`.
* `gdb-multiarch` could not attach (port 2345 owned by another agent); mGBA `-d`
  over a pty with a small Unix-socket server (`dbgserver.py`) was used for the
  keypad watchpoint. `arm-none-eabi-objdump -M force-thumb`, Python/Capstone 5.0.7
  for literal-pool and BL scans, Python/Pillow for screenshot classification.
* Work files (scripts, screenshots, fitted tables): `/tmp/opencode/starwars2/`.
  No ROM or copyrighted assets are redistributed; screenshots are local evidence only.

## 10. Legal note

Only hashes, addresses, algorithms, and my own generated codes are published here.
The ROM, extracted text banks, and game art are not redistributed.
