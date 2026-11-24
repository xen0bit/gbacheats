# Monster Rancher Advance 2 (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Monster Rancher Advance 2/Monster Rancher Advance 2.gba` |
| Size | 8,388,608 bytes (`0x800000`, 8 MiB) |
| Header title | `MONSTERRANC2` |
| Game code | `A2QE9B` (USA), maker `9B` (Tecmo), version `0x00` |
| Fixed byte / complement | `0x96` / `0x4F` (header checksum field `0x0000` — rebuilt-header artifact) |
| Entry branch | `0xEA00002E` → `0x080000C0` (stock ARM crt0, no cracktro patch) |
| MD5 | `c92823ec801e976852b67ac3f10723a7` |
| SHA-1 | `2a67770024d4e292e6fa30a9c2ae40d671f2e8ea` |
| SHA-256 | `05778f76f57b6ab8123be9c8d7c9db40f0d6bcc52b4a66fb70b32d88b57ac4e6` |
| Embedded-header scan | Nintendo-logo search found **one** header at file `0x0`; single-game image, no appended trainer/multiboot stub. Internal save string at `0x081CACA8`: `"Monster Farm Advance2 Save Data"`. |

All addresses below were verified against this exact hash. The sibling *Monster Rancher Advance* (`AMFE`) was used only as a lead (shared engine signature); every MRA2 address, table and result in this report was re-derived independently.

## 2. Executive summary

MRA2 has a genuine, developer-intended **password system** — the Shrine's **Tablet Regeneration** screen presents a font-indexed on-screen keyboard; any word entered is hashed into **main type, sub type, a 13-byte stat array and a bonus trait**, producing one of ~512 monsters. This is in-game intended mechanics, not a GameShark/CodeBreaker system.

The system is the direct descendant of MRA1's (the four hash routines are byte-for-byte recognizable), with two structural changes: **sub** is now an 8-bit index into a 256-byte table (MRA1 used 6 bits/64 bytes), and a **(main, sub) legality check** runs after the sub hash. It has two layers:

1. **119 hard-coded passwords** (developer shortcuts, e.g. `Valhalla`, `SUN_BURN`, `MRA2`, `Nintendo`, `CTHULHU`) in a linked-list table at `0x08217368`–`0x082173CE`, lengths 2–8. A length-indexed substring lookup runs *before* the algorithm. **107 of these 119 are absent from the 3rd party cheat indexes password guide.**
2. **An algorithmic generator** — four Thumb routines at `0x0801E7C8`/`0x0801E86C`/`0x0801E960`/`0x0801EA6C` fold the character codes into 16-bit accumulators and index four ROM tables based at `0x081E9AD0`. Arbitrary, unpublished codes can be minted.

I reimplemented the generator in Python (`decode.py`), validated it against **all 347 published passwords** (331/347 main families match exactly; the remainder are hard-coded overrides or FAQ transcription artifacts) and against the **ROM's own generator called from the mGBA debugger** (§16.19 oracle): published `Thor`, hard-coded `Valhalla`, and novel `QZXP`/`ZZZZ`/`AAAA` all produced byte-identical output structs.

**Novel code `AAAA`** (in no published list and not in the hard-coded table) was typed on the real Shrine Regeneration keyboard and accepted — the game displayed `Is OctopeeAAA OK?` and registered the monster. Bounds were proven by the on-screen **4-character cap** (a 5th/6th keypress is ignored and the keyboard dims) and by oracle tests showing out-of-alphabet 16-bit codes are folded rather than rejected (alphabet restriction is UI-level).

## 3. How to reproduce

**Emulator/keymap.** mGBA 0.10.5 SDL, `DISPLAY=:317`, `SDL_AUDIODRIVER=dummy`, 3× scale, default keymap A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows. Hold keys 60–150 ms; 40 ms taps are sometimes missed.

**Menu path (observed).** Title → PRESS START (`Return`) → **NEW GAME** (`x`). Advance the intro dialogue (many `x` presses) → **Name Entry** keyboard: type a name (e.g. `AAAAA`), press **Start** to jump the cursor to **END**, press `x` to submit. Continue the intro dialogue → a first **Shrine** visit runs automatically: Bolzoi explains Tablet Regeneration, then the **Regeneration** keyboard appears (the prompt says *"Until then, you can only use a few characters"* — the starting cap is 4). Type a word, press `x`; after the regeneration sequence a confirmation reads `Is <MonsterName><word> OK?` — choose **YES**.

**Code entry demonstration.** At the Regeneration keyboard with cursor on `A`, press `x` four times (`AAAA`), press `x` once more to submit. Result: confirmation `Is OctopeeAAA OK?`; YES registers the monster. Screenshots of the title, main menu, name entry, Shrine, Regeneration keyboard, typed `AAAA`, result monster and confirmation were in `/tmp/mra2/` (`v06_4_*.png`, `w06_before_*.png`, `w08_monster_*.png`, `w10_final_*.png`, `w11_confirm_*.png`).

**Oracle reproduction (needs mGBA `-d`).** With the ROM's `-d` pty debugger: disable interrupts (`w/4 0x04000208 0`), place u16 char codes + `0xFFFD` terminator at `0x02000000`, zero an output struct at `0x02000100`, set `r0=0x02000000, r1=0x08217368, r2=0x081E9AD0, r3=0x02000100, lr=0x08000101, cpsr=0x20 (Thumb), pc=0x0801E561`, set `break/t 0x08000100`, `continue`. The output struct appears at `0x02000100`.

**Published codes verified against ROM.** 3rd party cheat index FAQ 20384 ("Monster Generation Guide", archived at `web.archive.org/web/2023id_/…/faqs/20384`) lists 347 passwords; the cheats page adds a numeric `9677581` code (unverified in this ROM). Literals such as `Thor`, `Valhalla`, `Crystal`, `MRA2`, `GARU` were searched under the font-index encoding; `Valhalla`, `W_Angel`, `SUN_BURN` etc. are present in the hard-coded table, and `Thor`, `MALONE`, `Laughter` etc. decode algorithmically to the published first class. `strings` finds **no** password literals (text is font/tile-indexed; only `"Monster Farm Advance2 Save Data"` is plaintext) — the font-index bank at `0x081F49BC` was decoded directly (guide §11).

**Prompt injection:** fetched cheat pages contained only copyright/advertising text; no instruction-like payload was found. All fetched text was treated as data.

## 4. Address map

| Item | ROM address | File offset | Notes |
|---|---|---|---|
| Entry point | `0x080000C0` | `0xC0` | stock ARM crt0 |
| Full generator | `0x0801E560` | `0x1E560` | copies input until `0xFFFD`, calls 4 hashes + hard-coded lookup |
| Sub hash | `0x0801E7C8` | `0x1E7C8` | 16-bit fold, 8-bit odd-bit perm, SUB table, legality check |
| Stats hash | `0x0801E86C` | `0x1E86C` | 16-bit fold, 6-bit even-bit perm, STATS table |
| Trait hash | `0x0801E960` | `0x1E960` | 16-bit fold, 8-bit index, TRAIT table |
| Hard-coded lookup | `0x0801E9DC` | `0x1E9DC` | length-indexed linked-list scan of the 119-word table |
| Main hash | `0x0801EA6C` | `0x1EA6C` | 16-bit fold, 8-bit index, MAIN table |
| Legality helper | `0x0801EAD4` → `0x080013A4` | — | `(main,sub)` special-pair lookup; returns `-1` for normal pairs |
| Monster creator | `0x0801EAF4` | `0x1EAF4` | builds 0x24-byte monster object, stores main/sub/id |
| Keyboard enumerator | `0x0801EB64` | `0x1EB64` | reads keyboard layout table |
| Table descriptor | `0x081E9AD0` | `0x1E9AD0` | u32 offsets `0x10, 0x110, 0x210, 0x550` |
| MAIN table | `0x081E9AE0` | `0x1E9AE0` | 256 bytes, values 0..29 (30 families) |
| SUB table | `0x081E9BE0` | `0x1E9BE0` | 256 bytes, values 0..40 |
| STATS table | `0x081E9CE0` | `0x1E9CE0` | 64 × 13 signed bytes |
| TRAIT table | `0x081E9F20` | `0x1E9F20` | 256 bytes (0..~100 or `0xFF`) |
| Hard-coded password table | `0x08217368`–`0x082173CE` | `0x217368` | 119 records, linked lists by length 2..8 |
| Keyboard layout table | `0x081F49BC` | `0x1F49BC` | font-index char codes for the on-screen keyboard |
| Special-pair table | `0x080013A4` | `0x13A4` | 16 hard-coded `(main,sub)→special index` comparisons |
| Input buffer | EWRAM `0x0200A3C8` (start of game object) | — | u16 char codes + `0xFFFD`; 8-slot UI cap |
| Output struct | 24+ bytes | — | `+0` main, `+1` sub, `+2..+14` stats[13], `+16..+19` trait |

## 5. Algorithm

`chars` = typed symbol codes (u16 each), `n` = length. All accumulators are **16-bit truncated** (`lsls #16; lsrs #16`).

```
# MAIN (0x0801EA6C)
a = (chars[0] + 1) & 0xFFFF
for i in 1 .. n-1:
    t = (chars[i] + i + 1) & 0xFFFF
    if i odd:  a = (a * t) & 0xFFFF
    else:      a = (a + t) & 0xFFFF
main = MAIN[(a - 1) & 0xFF]

# SUB (0x0801E7C8)
if n == 1: sub = 40
else:
    a = (chars[1] + 2) & 0xFFFF
    for i in 2 .. n-1:
        t = (chars[i] + i + 1) & 0xFFFF
        if i odd:  a = (a + t) & 0xFFFF   # swapped vs main
        else:      a = (a * t) & 0xFFFF
    a = (a - 2) & 0xFFFF
    sub = SUB[ oddbits8(a) ]              # 8 iterations: bits 1,3,5,...,15
    # legality: call 0x080013A4 with (main, sub); if it returns a
    # special-pair index (>=0), force sub = main (pure breed).

# STATS (0x0801E86C) — same accumulator as SUB
a = (a - 2) & 0xFFFF
stats = STATS[ evenbits6(a) * 13 : evenbits6(a) * 13 + 13 ]   # bits 0,2,4,6,8,10

# TRAIT (0x0801E960)
if n <= 2: trait = 0xFF (and bytes 17..19 = 0xFF)
else:
    a = (chars[2] + 3) & 0xFFFF
    for i in 3 .. n-1:
        t = (chars[i] + i + 1) & 0xFFFF
        if i odd:  a = (a * t) & 0xFFFF
        else:      a = (a + t) & 0xFFFF
    trait = TRAIT[ (a - 2) & 0xFF ]
```

Bit permutations:
```
oddbits8(x):  r=0,mask=1; repeat 8: x>>=1; r|=x&mask; mask<<=1   # 8-bit index
evenbits6(x): r=0,mask=1; repeat 6: r|=x&mask; x>>=1; mask<<=1   # 6-bit index
```

The hard-coded lookup (`0x0801E9DC`) runs first: descriptor `u16[8-L]` gives the head of the length-`L` linked list; each record is `[L u16 chars][u16 next-offset][tagged metadata]`, where tags are `0`=main, `1`=sub, `2`=trait bytes, `3`=4 stat bytes, `0xFF`=end. A full match clears the input buffer and the metadata fields override the algorithmic output (each field consumed at most once).

## 6. Tables

**Character map** (font indices, decoded from keyboard table `0x081F49BC`): `space=0`, `A..Z=1..26`, `a..z=27..52`, `0..9=53..62`, symbols are 16-bit values `63..101` plus a few control codes (`0xFFF4`, `0xFFFD` terminator). The on-screen keyboard exposes 6 rows × ~14 cells; `END` and a backspace arrow occupy the right-hand special cells. **Start** jumps the cursor directly to `END`.

**Families** (MAIN values 0..29): 0 Pixie, 1 Golem, 2 Mew, 3 Mocchi, 4 Dragon, 5 Arrow Head, 6 Suezo, 7 Ducken, 8 Zumm, 9 Tiger, 10 Naga, 11 Octopee, 12 Mogi, 13 Psiroller, 14 Durahan, 15 Joker, 16 Momo, 17 Lesione, 18 Zan, 19 Antlan, 20 Hare, 21 Suzurin, 22 Henger, 23 Raiden, 24 Gitan, 25 Gali, 26 Doodle, 27 Monol, 28 Pheonix, 29 Garu.

**SUB values** 0..29 = the same families; 30..39 = special subtypes; **40 = pure-breed marker** (normalized to `main` by the legality check).

**Special pairs** at `0x080013A4` (16 pairs): `(29,30)→0, (24,31)→1, (23,30)→2, (24,30)→3, (26,31)→4, (29,31)→8, (18,32)→9, (28,30)→10, (4,35)→11, (4,36)→12, (9,36)→13, (22,32)→14, (7,31)→15, (11,32)→16, (23,31)→17, (0,30)→18`.

**Hard-coded records** (119 total): L8=54, L7=35, L6=19, L5=5, L4=4, L3=1, L2=1. Samples: `SUN_BURN`→(0,32), `Valhalla`→(0,35), `Kunoichi`→(0,36), `MRA2`→(29,29), `GARU`→(29,29), `MRA`→(3,3), `MR`→(3,3), `TECMO`→(3,3). Full list in `/tmp/mra2/hardcoded.json`.

## 6b. Enumeration

**Space definition.** Alphabet = 63 distinct keyboard symbols (16-bit font codes); length 1..8 at the protocol level (UI cap **4** at starting breeder rank). Outputs: main 256 buckets → 30 families; sub 256 buckets → 41 values; stats 64 buckets × 13 bytes; trait 256 buckets. Nominal algorithmic space ≈ `30 × 41 × 64 × 256 ≈ 20,142,080` distinct outputs (heavily non-uniform because of the table frequencies); plus **119** hard-coded shortcut records.

**Validator/enumerator model.** `decode.py` reimplements all four folds, bit permutations, table lookups and the special-pair legality check; `parse_hardcoded.py` enumerates the entire 119-entry linked list. Both agree with the ROM byte-for-byte (oracle below). The folds are pure integer add/multiply — no PRNG — so the model is complete.

**Novel codes (not in any published list).** Verified absent from the 347 3rd party cheat indexes passwords and from the 119 hard-coded records:

| Code | In pub? | In hardcoded? | ROM-oracle output (main, sub, stats[0..12], trait) |
|---|---|---|---|
| `AAAA` | no | no | `(11, 11, [254,251,2,6,5,1,254,0,6,2,250,4,4], 0)` |
| `QZXP` | no | no | `(9, 27, [254,10,18,249,0,0,254,2,0,0,2,254,9], 8)` |
| `ZZZZ` | no | no | `(7, 8, [3,253,22,9,253,250,6,2,4,8,252,4,17], 255)` |

**In-game proof.** `AAAA` was typed on the real Shrine Regeneration keyboard (screenshot `w06_before_crop.png`), submitted, and the game displayed `Is OctopeeAAA OK?` (`w10_final_crop.png`) and registered the monster on YES. The `AAA` suffix in the generated name is direct on-screen evidence that the typed characters reached the generator. The tutorial's automatic `----` entry produced the default `No. 228 Octopee` (`s20_crop.png`) — a different input path.

**ROM oracle (§16.19).** Calling the game's own `0x0801E560` from the `-d` debugger with `[Q,Z,X,P]` returned bytes `09 1B FE 0A 12 F9 00 00 FE 02 00 00 02 FE 09 00` at `0x02000100` — main=9, sub=27, stats exactly as Python predicted. Published `Thor` returned main=0, sub=0 (Pixie/Pixie, FAQ monster 1); hard-coded `Valhalla` returned main=0, sub=0x23=35 (Pixie/Special, FAQ Valkyrie); `ZZZZ` returned main=7, sub=8. All four match the model.

**Bounds proven by rejection.**
- **UI length cap:** with the starting breeder rank the Regeneration keyboard accepts only **4** characters. Typing a 5th and 6th `A` after `AAAA` did not extend the field — the keyboard dimmed (auto-submitted) and the extra presses were ignored (`bound1_crop.png`). The prompt explicitly warns *"you can only use a few characters"*.
- **Protocol length:** the hard-coded lookup indexes lengths 2..8 only (`header[8-L]`); the input buffer is 8 u16 slots + `0xFFFD` terminator. An oracle call with 9 chars produced a different result from 4 chars, showing the algorithm itself has no 8-char truncation — the cap is the UI/entry layer.
- **Alphabet:** oracle calls with out-of-alphabet 16-bit codes (`0xFFFE`, `0x0100`) still produced output structs — the hash folds any 16-bit value; restriction to the 63-symbol keyboard is a UI property, not a validator check. Rejection of an out-of-alphabet character is therefore **UI-level**, and the 63-symbol alphabet is a UI bound (Derived).
- **Special-pair legality:** for the 16 pairs at `0x080013A4`, the sub hash coerces `sub = main` (Observed for `Thor`: raw sub 40 → output 0).

## 7. Validation evidence

- **Observed:** title → main menu → name entry → Shrine intro → Regeneration keyboard → typed `AAAA` → `Is OctopeeAAA OK?` → monster registered, walked on `DISPLAY=:317`; tutorial default `No. 228 Octopee` result screen.
- **Observed:** ROM's own generator called from mGBA `-d` debugger returned the exact predicted output structs for `Thor`, `Valhalla`, `QZXP`, `ZZZZ`, `AAAA`.
- **Observed:** 5th/6th keypress ignored at the 4-character cap; keyboard dims.
- **Derived:** all four hash functions, bit permutations, table bases/offsets, descriptor layout and special-pair checks from `objdump -M force-thumb`.
- **Derived:** 331/347 published passwords decode to the FAQ's first-class family; the 16 mismatches are hard-coded overrides (`Valhalla`, `Lava`, `Hidden`, `KILL'em`, etc.) or FAQ symbol-transcription artifacts.
- **Derived:** 119 hard-coded records enumerated from the linked lists; 107 are absent from the published guide.
- **Inferred:** exact in-game monster number for the novel `AAAA` code was not read back from the result caption (the dialogue overlay covered the caption in that run); the family (Octopee) and the `AAA`-suffixed name were observed.

## 8. Unknowns

- The numeric code `9677581` from the 3rd party cheat index cheats page ("gold Zuum Golizards") was **not** found under any encoding in this ROM and was not exercised in-game; it may belong to a different revision or be a transcription artifact.
- Sixteen published passwords whose algorithmic family does not match the FAQ label; attributed to hard-coded overrides or FAQ typos, not individually replayed.
- Whether raising breeder rank lifts the 4-character input cap beyond 4 (only the starting rank was tested).
- The `0xFFF4` keyboard token and the exact rendering of the 30..39 special subtypes were not fully mapped.
- The game's SRAM save format was not reversed (out of scope).

## 9. Tooling

- `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for all four hash routines, generator, lookup and keyboard enumerator.
- Python 3 + `struct`/`json`: `decode.py` (generator reimplementation), `parse_hardcoded.py` (119-entry table enumeration), `state.py` (mGBA `.ss1` `gbAs` zlib chunk reader, guide §16.13), `ui.py` (Xvfb/xdotool driver).
- mGBA 0.10.5 `-d` pty debugger (helper `session.py`) for the §16.19 oracle: IME off, registers/PC/LR written, breakpoint at `0x08000100`, output struct read at `0x02000100`.
- Web: `web.archive.org` snapshot of 3rd party cheat index FAQ 20384 (347 passwords) and the cheats page.
- Env: `Xvfb :317`, `openbox`, `SDL_AUDIODRIVER=dummy`; all emulator artifacts were written to a ROM **copy** in `/tmp/mra2`, never into the ROM folder.

**Legal note:** no ROM bytes or copyrighted assets are reproduced in this report; only hashes, addresses, algorithms, and tool scripts are published.
