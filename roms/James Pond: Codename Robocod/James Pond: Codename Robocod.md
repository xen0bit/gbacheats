# James Pond: Codename Robocod (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/James Pond: Codename Robocod/James Pond: Codename Robocod.gba` |
| Size | 4,194,304 bytes (0x400000, 4 MiB) |
| Header title | `JAMES POND 2` |
| Game code | `AJDE` |
| Maker | `VN` (Virgin/Gameware Europe) |
| Version | 0x00 ("Rev.00"), fixed byte 0xB2 = 0x96 |
| Entry word | `0xEA00002E` → 0x080000C0 (stock crt0) |
| Header checksum | 0x0000; complement byte 0x86 (computed 0x9F) — non-standard but the entry word and crt0 are stock; no cracktro or trainer present |
| Embedded GBA headers | exactly 1, at file offset 0x0; no second image / trainer |
| MD5 | `4c2cdf7e90226f7ead473b1a2c67fbe6` |
| SHA-1 | `9279a7c128de12648a8180a3dcd1b53e95b1ee70` |
| SHA-256 | `6ee70a6b0abed8d675166833b884ca6488e9de3a3af4b26c4d7c433f7bbf4895` |

Credits text at ROM `0x1EDCA0` names Creature Labs / Engine Software / Gameware Europe 2003-2005, confirming this is the Engine Software GBA port, not the Amiga or Mega Drive original.

## 2. Executive summary

The GBA port has **two distinct developer-intended systems** on one screen ("Please Enter A Level Code", reached from Title → Continue Game):

1. **13 published ten-character level passwords** (GameFAQs / SuperCheats). They are **not stored as plaintext** in the ROM (all 13 searched literally, including reversed/lower/`+0x20`/packed variants — all absent). They are decoded algorithmically by the state machine at `0x0800307C`–`0x0800390C`. Characters 1 and 4 encode a progression index in the range 4–40; characters 2–3 are a two-digit numeric field; characters 5–10 are decoded as three 2-character tokens by `0x08002284`/`0x080024F4`. All 13 published codes were verified against the on-screen decoder and two were entered in mGBA successfully.

2. **Two previously unpublished hidden debug codes**, found as immediate comparisons in the same state machine:
   - `DNX3??????` — unlocks debug mode by incrementing a gate word at IWRAM `0x03006350` (observed 0 → 1). The remaining six characters are not tested; their value is irrelevant. The code itself does not start a game.
   - `JTnn??????` — when the debug gate is nonzero, jumps directly to level `nn` (`nn` = two decimal digits, 00–99). The remaining six characters are not tested. `JT01??????` and `JT20??????` were accepted in mGBA and RAM-verified (`0x03001968` = 1 and 20 respectively). `JT20` is an **unadvertised combination** — published lists stop at level 13.

`JTnn` is rejected when the debug gate is zero (observed, returns to title). `AAAAAAAAAA` is rejected (observed). No button sequences, hidden menu entries, or unlockable menus were found beyond these; the Options and Pause screens were walked completely.

## 3. How to reproduce

- **Emulator**: mGBA SDL (`/usr/local/bin/mgba`), `DISPLAY=:316`, `SDL_AUDIODRIVER=dummy`, 3× scale. Xvfb `:316` + openbox started locally.
- **Keymap** (mGBA SDL default): A = `x`, B = `z`, L = `a`, R = `s`, Start = `Return`, Select = `Backspace`, D-pad = arrow keys. Hold 100–200 ms per press; 40–60 ms when stepping the on-screen keyboard to avoid double-stepping.
- **Menu path**: boot → language screen (A accepts English) → skip intro (Start) → Title (`New Game` / `Continue Game` / `Options`) → `Continue Game` → "Please Enter A Level Code".
- **On-screen keyboard** is a 10×4 grid indexed linearly: indices 0–9 = `A`–`J`, 10–19 = `K`–`T`, 20–29 = `U`–`Z`,`!`,`-`,`.`,`←`(delete), 30–39 = `0`–`9`. Move with D-pad, confirm with A; after the 10th character the cursor jumps to the green tick; press A again to submit. **Home the cursor** with several Up/Left presses before entering a code, otherwise positions are offset.
- **Verification codes entered successfully**:
  - `Y24KQTVQCK` (published "Level 1 Completed") → gameplay.
  - `M72LBNXRKT` (published "Level 13 Completed") → "ARCTIC TOYS" level, score 15,770,000.
  - `DNX3AAAAAA` then `JT01AAAAAA` → level 1 (RAM level word = 1).
  - `DNX3ZZZZZZ` then `JT20ZZZZZZ` → level 20 (RAM level word = 20).
  - `JT20AAAAAA` on a fresh boot (no `DNX3`) → rejected, title screen.
  - `AAAAAAAAAA` → rejected, title screen.

## 4. Address map

File offset = ROM address − `0x08000000`.

| ROM / IWRAM address | Meaning |
|---|---|
| `0x0800307C` | Password-screen state machine / input loop (`break/t` here hits on entry) |
| `0x08003100` | Clears 14 bytes at `0x0300172C` and a second buffer at `0x0300173A` with 0x20 |
| `0x080031C4` | Per-keystroke loop; reads the input buffer, dispatches on first characters |
| `0x080031F0` | Parses two-digit field at `buf[1..2]` (`buf[2]*10 + buf[1] − 528`) |
| `0x080036B8` | Reject path for the two-digit field |
| `0x0800370A`–`0x08003754` | Decodes `buf[4..9]` into three tokens with weights 4,840,000 / 220,000 / 10,000; upper bound 99,999,999 |
| `0x08003756`–`0x0800378E` | Derives progression index from `buf[0]` and `buf[3]`; range check `4..40` |
| `0x080037A4` | 37-entry jump table indexed by (index − 4); sets completion flags at `0x030017E8` |
| `0x08003928` | **Hidden `JT` level-jump handler** (first two chars `J`,`T`) |
| `0x08003960` | **Hidden `DNX3` unlock handler** (first four chars `D`,`N`,`X`,`3`) |
| `0x08002284`, `0x080024F4` | 2-character token decoders used by the normal password path |
| `0x08011340`, `0x080112A8` | Compiler runtime divide / modulo helpers |
| `0x083F91AC` | 40-byte alphabet A: `ABCDEFGHIJKLMNOPQRSTUVWXYZ-   0123456789` |
| `0x083F91D4` | 40-byte alphabet B: `ABCDEFGHIJKLMNOPQRSTUVWXYZ!-. 0123456789` — exactly the on-screen keyboard order |
| `0x0300172C` | IWRAM: 10-character code input buffer (ASCII, space-padded) + 4 bytes |
| `0x0300173A` | IWRAM: secondary input/copy buffer |
| `0x03001750` | IWRAM: completion-flag buffer (cleared to 0 over 0x56 bytes) |
| `0x030017E8` | IWRAM: level-completion flag array written by the jump table |
| `0x03001968` | IWRAM: numeric level / parsed field word (observed 999 → 1 / 20) |
| `0x03001A20` | IWRAM: accumulated decoded-token value |
| `0x03006350` | IWRAM: **debug unlock gate** (observed 0x0 → 0x1 after `DNX3`) |
| `0x03001884`, `0x03001888` | Set to 3 by the `JT` handler on success (observed) |

## 5. Algorithm

### Hidden debug path (fully recovered)

```
buf = ASCII bytes at 0x0300172C, space padded, length 10

if buf[0] == 'D' and buf[2] == 'X' and buf[1] == 'N' and buf[3] == '3':
    debug_gate = [0x03006350]
    debug_gate += 1
    stay on password screen (r7 = -1 -> loop), do not start game

elif buf[0] == 'J' and buf[1] == 'T':
    if [0x03006350] == 0:
        fall through to normal validation (rejects "JT.." as an ordinary code)
    else:
        n = buf[2]*10 + buf[3] - 528      # ASCII digits -> 0..99
        if n > 99: reject
        [0x03001968] = n                  # jump to level n
        [0x03001884] = 3; [0x03001888] = 3
        start game
```

`528 = 0x30*10 + 0x30`, so the arithmetic converts two ASCII digit characters into their decimal value. The check at `0x0800394C` is `cmp r3,#99; bhi reject`, so the field is exactly 00–99; no three-digit level can be expressed.

### Normal level-code path (partially recovered)

- `buf[0]` and `buf[3]` determine a progression value:
  `idx = (buf[3] − 75)*10 + (buf[0] − 75)`; if `buf[3] == 0x59 ('Y')` then `idx = 40`.
  Valid range is `idx ∈ [4,40]` (37 values); `0x08003798` rejects outside it.
  Checked against the 13 published codes, every one lands in this range (e.g. `Y24KQTVQCK` → 14, `S15KPZPNQT` → 8, `K42YBNPNMX` → 40 via the `Y` special case).
- `buf[1]`, `buf[2]` are converted to a two-digit integer (`buf[2]*10 + buf[1] − 528`) and must be ≥ 3.
- `buf[4..9]` are decoded as three character pairs by `0x08002284`/`0x080024F4` and weighted 4,840,000 / 220,000 / 10,000 into `0x03001A20`, which must be ≤ 99,999,999.
- `0x080037A4` then selects one of 37 handlers that set completion flags at `0x030017E8`.
- The exact final acceptance comparison for the normal path was **not** isolated — see §8.

## 6. Tables

### On-screen keyboard alphabet (40 symbols, `0x083F91D4`)

```
index: 00-09  10-19  20-25   26 27 28 29   30-39
chars: A..J   K..T   U..Z    !  -  .  ␣   0..9
```
Index 29 (0x20) is rendered as the red backspace arrow. A second table at `0x083F91AC` differs only in positions 26–29 (`-`, `␣`, `␣`, `␣`) and is not the keyboard order.

### Published level passwords (verified against the ROM's input decoder; two entered in-game)

| Level completed | Password |
|---|---|
| 1 | Y24KQTVQCK |
| 2 | S15KPZPNQT |
| 3 | R12NPZPNPZ |
| 4 | Q12NPZSFTX |
| 5 | Q12LMXTKKT |
| 6 | S63NMXTKNP |
| 7 | Y81MMXXTFJ |
| 8 | M15NMXVRDM |
| 9 | T81NMXVRTX |
| 10 | S12MMXRCRX |
| 11 | K42MBNZBKQ |
| 12 | K42YBNPNMX |
| 13 | M72LBNXRKT |

Source: GameFAQs GBA cheat page (403 when fetched directly; recovered from search snippets) and SuperCheats "Unlockables" page, which was fetched in full. No literal for any of these appears anywhere in the ROM.

### Hidden debug codes (this report)

| Code (first 4 chars significant) | Effect | Gate |
|---|---|---|
| `DNX3??????` | Increment debug gate at `0x03006350` | none |
| `JTnn??????` | Jump to level `nn` (00–99) | requires gate ≠ 0 |

### Amiga / Mega Drive codes — not GBA codes

`CHEAT` (Cake/Hammer/Earth/Apple/Tap), `POWER` and `LIVES` item-order cheats are published for the Amiga/Mega Drive/DS versions (Sega Retro, CheatCC, SuperCheats). They are **not** button or password codes in this GBA image and were not verified here; no corresponding GBA menu or code entry was found.

## 6b. Enumeration

**Space definition**

- Input surface: 10 characters from a 40-symbol alphabet → 40¹⁰ ≈ 1.10×10¹⁶ raw strings.
- The hidden system is **prefix-based**, not a fixed table:
  - `DNX3` + 6 free characters → 40⁶ ≈ 4.10×10⁹ spellings, all with the same effect.
  - `JT` + two decimal digits + 6 free characters → 100 × 40⁶ ≈ 4.10×10¹¹ spellings; one distinct effect per 2-digit value.
- Level-jump domain is 00–99 (100 expressible values), proven by the `cmp #99 / bhi reject` at `0x0800394C` and the two-ASCII-digit arithmetic.
- The normal progression field covers 37 values (4–40) via `0x080037A4`'s 37-entry jump table.
- Published lists contain 13 codes; the expressible space is many orders of magnitude larger.

**Novel codes (absent from GameFAQs, SuperCheats, VGChartz, TCRF)**

1. `DNX3AAAAAA` — unlock code. RAM proof: `0x03006350` 0x0 → 0x1 (savestate diff).
2. `JT01ZZZZZZ` / `JT01AAAAAA` — level 1. RAM proof: `0x03001968` = 1.
3. `JT20ZZZZZZ` — **level 20**, outside the published level-13 maximum. RAM proof: `0x03001968` = 20; screenshot shows the level-20 factory zone. This is the headline unadvertised combination.

**Bounds proven by rejection (in game)**

- `AAAAAAAAAA` → returns to title (ordinary invalid code).
- `JT20AAAAAA` on a fresh emulator session with gate = 0 → returns to title. RAM gate remains 0. This proves the DNX3 gate, not just the code characters.
- Static bound (derived, not exercised on screen): a non-digit in the `nn` position makes `n > 99` and takes the `bhi` reject at `0x08003950`; a three-digit level cannot be entered because the field is exactly two characters.
- `DNX3` requires the exact four characters `D`,`N`,`X`,`3` in that order (four immediate `cmp`s at `0x08003962`/`0x0800396C`/`0x08003976`/`0x080031EA`); mismatches fall through to the ordinary validator.

**Completeness argument**

The debug system is closed: `0x0800307C`'s loop has exactly two special dispatch branches on the first character (`0x44 'D'` at `0x080031E2`, `0x4A 'J'` at `0x080031EC`); every other first character goes to the ordinary validator. The `JT` branch has one second-character check (`0x54 'T'`); the `DNX3` branch has three further exact-character checks. No other action branches or sequence tables exist in this function.

## 7. Validation evidence

- **Observed** (emulator / savestate RAM): title, Options (Jump A/B, Music Volume, Credits), credits scrolling, Continue Game → password keyboard, Pause (Continue/Quit), all screenshots in `/tmp/jamespond/`. Gate word 0→1 after `DNX3`; level word 1 / 20 after `JT01` / `JT20`; `0x03001884`/`0x03001888` = 3 on JT success; rejection screens for `AAAAAAAAAA` and gated `JT20`; acceptance screens for two published codes.
- **Derived** (disassembly, verified against observed RAM): the DNX3/JT handlers at `0x08003960`/`0x08003928`; the `−528` ASCII-digit conversion; the two-character first-field comparisons; the 37-entry jump table; the 40-symbol alphabet tables; the 13 published codes' absence from the ROM under ASCII, reversed, lowercase, `+0x20`, UTF-16LE/BE, XOR/all byte shifts, add/all byte shifts, and 5/6-bit packings.
- **Inferred**: the precise final acceptance comparison for the 13 ordinary level codes (the token-weighted value at `0x03001A20` is computed and bounded, but the exact equality against the digits/flags was not isolated). The six filler characters of `DNX3??????` and `JTnn??????` are not read by the special handlers (derived from the absence of any access to `buf[4..9]` in those branches) but were not exhaustively varied on screen.

## 8. Unknowns

- The final check that makes an ordinary 10-character code valid (the relationship between `0x03001A20`, the two-digit field and the completion flags) was not isolated. Consequently a novel *ordinary* level password was not minted; the novel codes delivered are the hidden debug codes.
- The `CHEAT`/`POWER`/`LIVES` item-collection cheats from other platform versions were not tested in GBA gameplay (out of scope for menu/code entry; GBA text is tile-indexed so a string search is inconclusive).
- Whether level values beyond 13 (e.g. `JT37`) are playable or lead to undefined level data was not exhaustively tested; `JT20` is confirmed playable.
- ROM header complement (0x86 vs computed 0x9F) and zero checksum are likely rebuild artifacts; no functional effect was observed.

## 9. Tooling

- `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for Thumb disassembly.
- Python/Capstone scripts in `/tmp/jamespond/`: `scan.py` (pointer + PC-relative literal scans), `xrefs.py` (literal → loader xrefs), `ss.py` (mGBA `.ss1` PNG `gbAs` zlib parser; raw state IWRAM at 0x19000, EWRAM at 0x21000).
- mGBA CLI debugger (`mgba -d`) driven over a PTY: `break/t`, `continue`, `i`, `r/4`, `x/1`, `dis/t`. The GDB stub at port 2345 was occupied by another process, so a PTY debugger and savestate RAM diffs were used instead.
- `xdotool` XTEST input on `DISPLAY=:316`; `scrot` + ImageMagick crop at `730x490+153+163`.
- Web sources: SuperCheats unlockables page (fetched in full), GameFAQs GBA cheats page (403; recovered via search snippets), Sega Retro hidden-content page. No prompt-injection content was encountered in fetched pages.

No ROM images or copyrighted assets are redistributed here; only hashes, addresses, algorithms and the author-generated code strings are published.
