# LEGO Knights' Kingdom (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Lego Knights' Kingdom.gba` (same folder as this report) |
| Size | 4,194,304 bytes (`0x400000`) |
| `file` | Game Boy Advance ROM image: "LEGO_KNIGHTS" (BKNE78, Rev.00) |
| Header title | `LEGO_KNIGHTS` |
| Game code / maker | `BKNE` / `78` (Europe), version `0x00`, complement `0x24`, checksum `0x0000` |
| Entry word | `0xEA00002E` (stock GBA branch — no cracktro/trainer patch) |
| Embedded GBA headers | exactly **1** (file `0x00000000`); no multiboot/user/nested image |
| MD5 | `5ad0ed7f2bbda3dab28d29b59f01cade` |
| SHA-1 | `5f6e9fada285dd4795d4103e5f97b8e714ab9099` |
| SHA-256 | `e6ebd3fca02f146dc0b3761c259a8ca02f8ebf842b493c90479e68f635ec2095` |
| Developer / publisher | Razorback Developments / THQ (from credits string at `0x083DE2EF`) |

Developed-as-published retail image; no appended trainer or SCUMM-style patch detected.

## 2. Executive summary

The game has a genuine developer password system on the **Password** entry of the main menu. It
is **algorithmic, not a lookup table**: none of the ten published 7-letter codes occurs as ASCII
anywhere in the ROM. The on-screen keyboard alphabet is the 16-letter set
`BDFGHIKPRSTVWXYZ` at ROM `0x08323DDC`, so each character is one nibble and a password is a
**28-bit word**. The word is packed from 21 one-byte progress flags (nine quest completions,
four Lost Key pieces, eight Lord Vladek artifacts), protected by **five parity bits and a 2-bit
popcount checksum**. I reimplemented the encoder and validator bit-for-bit; both agree with all
ten published codes, and a brute-force over the whole 2^28 space confirms **exactly 2,097,152
(2^21) accepted words**.

I minted an unpublished code, **`BBRBFBS`**, from an unadvertised flag combination (Trials of
Jayko + one artifact), entered it on the real screen and proved with a savestate RAM diff that
only flags 12 and 15 were set and the decoded word became `0x00080209`. A one-character
checksum corruption (`BBRBFBD`) and an all-`Z` word (`ZZZZZZZ`) were both rejected with no flag
changes, proving the bounds. Applying a published all-unlock code (`YZZVZYZ`) was also RAM-verified
(Trophy Room reads `Vladek Artifacts 4/4`, `Lost Key 4/4`; Lord Vladek becomes selectable).

A hidden debug menu exists as *text* (string IDs 120–126: `Cutscene Example`, `Game Level Test`,
`Level M02A/M02/MTA`, `Knight Select`, `Last Man Standing`) but no reachable gate was found:
every menu item on every screen was walked in both clean and fully-unlocked states, and common
button codes were tried on the title and main menus without reaching it. It is reported as a
bounded negative, not as an undiscovered cheat.

## 3. How to reproduce

* Emulator: mGBA (`/usr/local/bin/mgba -3`), headless on `Xvfb :318 -screen 0 1024x768x24`,
  `DISPLAY=:318 openbox`, `SDL_AUDIODRIVER=dummy`. GBA window is 720×480 at `X=154,Y=184`.
* Keymap: `A=x`, `B=z`, `L=a`, `R=s`, `Start=Return`, `Select=BackSpace`, D-pad = arrow keys.
  Hold keys 100 ms+. Shift+F*n* saves savestate slot *n*; plain F*n* loads it.
* Path: boot → legal text (press `A`) → Razorback logo → title `Press START!` (`Start`) →
  **MAIN MENU** → `Password` (5th of 7 items) → **ENTER PASSWORD**.
* Entering a code: the top field accepts up to **8** characters; the on-screen grid has
  row 1 `B D F G H I K P`, row 2 `R S T V W X Y Z`. Move with the D-pad, press `A` to append the
  highlighted letter, `B` (or `Delete`) to backspace, and `Done` (one row below the grid) to submit.
  Invalid codes return silently to the main menu; valid codes apply flags and return there.
* To read RAM without a working GDB stub: save a `.ss1`-style savestate before and after the
  action; the PNG has a zlib `gbAs` chunk that decompresses to a 397,312-byte raw state. EWRAM
  begins at raw offset `0x21000`, so GBA address `0x0200XXXX` is raw `0x21000 + XXXX`.
* Codes tested on-screen: all ten published codes (all accepted), novel `BBRBFBS` (accepted),
  rejects `BBRBFBD`, `ZZZZZZZ`, `BBBBBBB`.

## 4. Address map

| Address | Meaning |
|---|---|
| `0x08000000` | ROM base; file offset = address − `0x08000000` |
| `0x083D7FF4` | base of the localized string bank |
| `0x083D7FF8` | u32 string-offset table, 542 entries; string ID *n* → `base + table[n]` |
| `0x083D898E` | ID 25 `ENTER PASSWORD`; ID 26 `Done`, 27 `Delete`, 28 `Quit` |
| `0x083D8DDC` | ID 85 `NEW PASSWORD`, ID 86 `SELECT KNIGHT!` |
| `0x083D8FC7`–`0x083D9026` | IDs 118–126: Options labels and hidden debug labels |
| `0x08323DDC` | password alphabet `"BDFGHIKPRSTVWXYZ"` (16 bytes, NUL-terminated) |
| `0x0808628C` | **flag→word encoder** (`make_password_word`): packs 21 flag bytes, adds group parities and 2-bit checksum |
| `0x08086220` | **validator** (`check_password_word`): verifies parities and checksum, returns 1/0 |
| `0x08086448` | **apply**: expands an accepted word into the 21 flag bytes |
| `0x080A2300` | **decoder**: typed 7 letters → 28-bit word at `[0x02000F7C]` |
| `0x080A235C` | **generator**: word at `[0x02000F7C]` → 7 letters into the on-screen buffer (called from `0x080A3700`) |
| `0x080A2B4C` | password submit gate: `mov r0,#9` key test, `BL 0x080A2300`, `BL 0x08086220`, then apply or reject |
| `0x02000F64`..`0x02000F78` | 21 one-byte progress flags (quests, Lost Key, Vladek artifacts) |
| `0x02000F7C` | 28-bit decoded password word (written by `0x080A2300`) |
| `0x02000EB4` | `0xFFFFFFFF` after the all-unlock password (all unlock bits) |
| `0x0200B614` | offset of the password text buffer from the engine's base pointer held at `0x0200E11E` |

## 5. Algorithm

```
ALPHA = "BDFGHIKPRSTVWXYZ"          # 0..15

# Flag byte i (0..20 at 0x02000F64+i) maps to word bit BIT_OF_FLAG[i]:
BIT_OF_FLAG = {0:11,1:12,2:13,3:15,4:16,5:17,6:18,7:20,
               8:21,9:22,10:23,11:25,
               12:0,13:1,14:2,15:3,16:5,17:6,18:7,19:8,20:10}

encode(flags):
    w = sum(1 << BIT_OF_FLAG[i] for i,f in enumerate(flags) if f)
    acc = 0
    for g in 0..4:                       # five 5-bit groups: bits 5g..5g+3 data, bit 5g+4 parity
        acc += popcount((w >> (5*g)) & 0xF)
        if acc & 1: w |= 1 << (5*g+4)
        acc += 1                         # cumulative, gives the alternating parity convention
    w |= (popcount(w & 0x03FFFFFF) & 3) << 26
    return w & 0x0FFFFFFF

validate(w):                             # exact replica of 0x08086220
    acc = 0
    for g in 0..4:
        acc += popcount((w >> (5*g)) & 0xF)
        if (acc & 1) != ((w >> (5*g+4)) & 1): return REJECT
        acc += 1
    if (popcount(w & 0x03FFFFFF) & 3) != ((w >> 26) & 3): return REJECT
    return ACCEPT

word_to_code(w) = ALPHA[w>>24 & 15] ALPHA[w>>20 & 15] ... ALPHA[w & 15]
code_to_word(s) = fold nibbles: w = (w << 4) | ALPHA.index(ch)
```

The typed string is decoded at `0x080A2300` one character at a time; characters not in the
alphabet map to index 15 at most and are ignored when the index exceeds 15. Decoding writes the
raw word at `0x02000F7C`; validation happens separately in `0x08086220`; only then does
`0x08086448` unpack data bits into the flags and set the unlock word at `0x02000EB4`.

A full Python implementation is `/tmp/opencode/legoknights/pw.py`; the brute-force enumerator is
`/tmp/opencode/legoknights/enum.c`.

## 6. Tables

**Published codes (GameFAQs / Cheat Happens, all ten verified against the model and accepted in-game):**

| Effect | Code | Decoded word | Flags set |
|---|---|---|---|
| All stories 100%, all unlocks | `YZZVZYZ` | `0x0EFFBFEF` | 0–20 |
| Citadel of Orlan 100% | `TVPGGYZ` | `0x0AB733EF` | 1,2,4,5,6,7,8,10,11,12–19 |
| Danju's story 100% | `WTZKFKZ` | `0x0CAF626F` | 2,4,5,6,8,10,12–17 |
| Desolate Moorlands 100% | `YVPFBYZ` | `0x0EB720EF` | 2,4,5,6,7,8,10,12–18 |
| Free the King 100% | `VVZPVYZ` | `0x0BBF7BEF` | 0,1,2,4,5,6,7,8,10,11,12–19 |
| Grand Tournament 100% | `KVPZPYZ` | `0x06B7F7EF` | 1,2,3,4,5,6,7,8,10,11,12–20 |
| Jayko's story 100% | `IFSHBDP` | `0x05294017` | 4,8,12,13,14 |
| Rascus' story 67% | `SFVBFBZ` | `0x092B020F` | 4,5,8,12,13,14,15 |
| Santis' story 100% | `WTVFBFZ` | `0x0CAB202F` | 2,4,5,8,10,12,13,14,15,16 |
| Trials of Jayko 100% | `DBBHBDD` | `0x01004011` | 12 |

Byte-for-byte literals for these codes are **absent** from the ROM (verified by `grep -abo` for
all ten), confirming the algorithmic rather than table-based design.

**Alphabet / key:** `B=0, D=1, F=2, G=3, H=4, I=5, K=6, P=7, R=8, S=9, T=10, V=11, W=12,
X=13, Y=14, Z=15`. Keyboard grid (from cursor walk): row 1 `BDFGHIKP`, row 2 `RSTVWXYZ`;
cursor starts on `B`, `Down` from the grid cycles `Done → Delete → Quit`.

## 6b. Enumeration

* **Space**: 16 symbols × 7 positions = 16^7 = **268,435,456** strings. The word is 28 bits:
  21 data bits (the flags), 5 group-parity bits (positions 4, 9, 14, 19, 24) and a 2-bit
  popcount checksum (bits 26–27). Bit 25 is the flag-11 data bit.
* **Accepted set**: exhaustive C enumeration of all 2^28 words with the ROM's validator returns
  **2,097,152 = 2^21** accepted words — exactly 1 in 128. Every accepted word corresponds
  bijectively to a 21-flag progress state; re-encoding the decoded flags of every published code
  reproduces that same code exactly (all ten match).
* **Novel code**: **`BBRBFBS`** (word `0x00080209`, flags `{12,15}` = Trials of Jayko plus one
  artifact). This combination is in none of the GameFAQs, Cheat Happens, VGChartz, or TCRF
  lists consulted. Entered on the real password screen: RAM at `0x02000F64` after submission has
  only indices 12 and 15 set; `0x02000F7C = 0x00080209`. `BBRBFBS` satisfies the offline
  validator; effect observed in emulator.
* **Bounds proven by rejection**:
  * `BBRBFBD` — single-character change corrupting the 2-bit checksum: decoder writes
    `0x00080201`, validator rejects, **no flag changes** (all 21 bytes remain 0).
  * `ZZZZZZZ` — word `0x0FFFFFFF`, bad parity/checksum: decoded but rejected, no flags set.
  * `BBBBBBB` — word 0, rejected, no flags set.
  * The 8-character input field can be filled, but 8-character words contain bits 28–31 that
    the validator never reads; only the low 28 bits matter. This is an alias class, not a new
    code (documented as such).
* **Button-code space**: no password-like button sequence system exists on the title or main
  menu. Tested there: `L,R,Start` (published for the *Bionicle* half of the 2-in-1 cart — not
  applicable here), `L,L,R,L,Select,Start,A` (the published 2-in-1 secret-menu code — rejected
  on this standalone ROM), Konami code, `L+R+A+B`, `Select+A+B`, `L+R` held for 2 s, and
  `L,L,R,R,L,R`. None opened a hidden screen.
* **Debug strings**: IDs 120–126 are present in the English and German text banks and are
  *not* reachable from Options with either clean or fully-unlocked flags. No literal pointer to
  the string bank or to ID 120–126 was found, and no debug-screen handler was identified. The
  negative is bounded by: full text-bank enumeration (542 IDs), full screen walk, both flag
  states, and the button-code set above.

## 7. Validation evidence

* **Observed** (emulator screenshots, saved on disk in `/tmp/opencode/legoknights/`): boot/legal,
  title, MAIN MENU, SELECT QUEST, ENTER PASSWORD + keyboard, GAME PAUSED, Options, Trophy Room
  (`Vladek Artifacts 4/4`, `Lost Key 4/4` after `YZZVZYZ`), SELECT KNIGHT! with Lord Vladek
  selectable, Multiplayer "Waiting for player", and the novel-code result.
* **Observed** (RAM): the clean password screen has `0x02000F64..F78 = 0`; `YZZVZYZ` sets all
  21 flags to 1, `0x02000F7C = 0x0EFFBFEF`, `0x02000EB4 = 0xFFFFFFFF`; novel `BBRBFBS` sets
  only flags 12 and 15, `0x02000F7C = 0x00080209`; each rejected code leaves all flags at 0.
* **Derived** (disassembly): alphabet, bit layout, parity/checksum equations, decoder,
  generator, validator and apply routine at the addresses in §4. All ten published codes satisfy
  the derived validator; the offline encoder reproduces each of them exactly.
* **Inferred**: the semantic names of the 21 flags (quest completions, Lost Key pieces, Vladek
  artifacts) come from the published effect labels and the in-game Trophy Room; the bijection
  itself is proven, the exact per-flag prose label for each of the 21 bits is not individually
  exercised.
* **Web content**: GameFAQs, Cheat Happens and 2-in-1-cheats pages were treated as data. One
  searched-for "secret menu" entry was found to belong to the *Bionicle* half of the
  2-in-1 cartridge, not this game. No prompt-injection payload was encountered in the fetched
  pages; nothing in fetched content was executed.

## 8. Unknowns

* The hidden debug menu's trigger (string IDs 120–126) was not identified; it may be dead code
  or gated by a development-only condition not reachable in the retail build.
* Exact names for each of the 21 progress-flag bytes beyond the grouped Trophy Room labels.
* Whether the 8th input character (bit 28+) can be used by any other code path — the validator
  ignores it, so it is treated as an alias.
* mGBA's GDB stub was unreliable on this build (protocol errors); all RAM evidence therefore
  comes from decompressed savestate diffs, which are deterministic and reproducible.

## 9. Tooling

* `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings`, `grep -abo` for Phase 0/1.
* Python 3 with `capstone` 5.0.7 for literal/PC-relative scans; `arm-none-eabi-objdump
  -M force-thumb` for all disassembly; REA/Ghidra (`open_binary` raw-binary ARM @ `0x08000000`,
  `search_strings`, `xrefs`) for string discovery and cross-reference checks.
* `/tmp/opencode/legoknights/ss.py` — mGBA `.ss*` `gbAs` zlib extractor / RAM reader.
* `/tmp/opencode/legoknights/pw.py` — bit-exact encoder, validator, decoder and flag map.
* `/tmp/opencode/legoknights/enum.c` — exhaustive 2^28 validator enumeration.
* `/tmp/opencode/legoknights/enter.py`, `key.py` — reproducible on-screen code entry via XTEST.
* Screenshots and savestates are in `/tmp/opencode/legoknights/` and in the ROM folder during
  the run; all generated `.sav`/`.ss*` files were removed from the ROM folder at the end.

*Legal note*: no ROM bytes, graphics, music or game text are redistributed by this report —
only hashes, addresses, algorithms and my own tooling are published.
