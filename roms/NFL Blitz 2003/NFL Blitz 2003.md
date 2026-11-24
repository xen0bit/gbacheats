# NFL Blitz 2003 (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `NFL Blitz 2003.gba` (4,194,304 bytes / 0x400000) |
| Header title | `NFL BLITZ2K3` |
| Game code | `ANKE` (maker `5D`), revision 0 (software version byte `0x00`) |
| Entry word | `0xEA00002E` → `0x080000C0` (stock crt0, no cracktro patch) |
| Nintendo logo | Intact; exactly **one** embedded GBA header found (logo scan), no 2-in-1 image, no appended trainer |
| Header bytes | fixed `0xB2=0x96`; complement `0xBD=0x84`; checksum `0xBE=0x0000` |
| MD5 | `cfa185aa9c5c11136e16ce519f96e3e9` |
| SHA-1 | `6d63871abf8016248ff7f8777d762e7c75877d40` |
| SHA-256 | `cb51c493ece08de480ca52195778c366cf1336e85540ca05e36ce0026eabfb83` |

Note: sum of header bytes `0xA0..0xBC` = `0x63`; stored complement `0x84` would need `0x9D` to balance, and the header checksum is `0x0000`. Per guide §16.1 this is consistent with a header that was rebuilt at some point, but the logo, entry branch and code are stock and no trainer/wrapper is present. Verified independently of the sibling *NFL Blitz 2002* report.

## 2. Executive summary

This GBA SKU has **one developer-intended cheat system**: the Season-mode **PASSWORD** screen (reached from Season → Load Game). It is a *checksum-based algorithmic* password system, not a lookup table — none of the published codes appear as literals in the ROM. The screen presents a 32-symbol keyboard (consonants B–Z plus digits 0–9 and `+`; the five vowels are omitted) and accepts exactly 8 characters. Each character is a 5-bit symbol, so the input space is 32^8 = 2^40 codes.

I fully reversed the validator at `0x080194D0`: it unpacks six 5-bit characters from the first six symbols, takes two more bits from symbol 7, XORs the resulting 32-bit word with an 8-bit key derived from symbols 7 and 8, and checks (a) bit 0 clear, (b) a 5-bit "week/n" field ≤ 18, and (c) a 4-bit checksum against a 32-byte table at `0x0804FE8C`. It outputs a team index (0–31) and a 17-entry play-plan array. The on-screen `0` glyph is **aliased with `O`**: published codes written with `O` (e.g. `HZOTLYJX`) are the same value as `0` and validate once `O`→`0` is applied. This explains why published lists mix `O` and `0`.

All 32 published GBA codes were checked with the reimplementation: **31 pass**; `4L6B54W1` (Bears Level 6) is a published **typo** — the correct code is `4L6BS4W1` (position 5 is `S`, not `5`), which was generated and accepted in-game. A novel code for an unpublished team index, `BBBFBCBB`, was generated, entered, and accepted, producing a season schedule not in any published list (week 1 recorded as a **loss**, because the generated play bits were zero). Bounds were proven by rejection of a bad-checksum code (`BBBDBCBB`) and an out-of-range `n=25` code with an otherwise valid checksum (`BBBFBQVB`).

No hidden/debug menu and no working button code were found: the title-screen sequence `A,B,Select,Up,Right,Down` (published for the 2002 sibling) and the `5-5-5 Left` weather code (published for the 2003 consoles) produced no effect on this GBA image, and no secret-team names exist in the ROM under any encoding checked.

## 3. How to reproduce

* **Emulator**: mGBA (SDL build), `SDL_AUDIODRIVER=dummy`, on `Xvfb :317`, 3× scale. Keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrow keys. Hold keys 100–250 ms; 0.28 s gaps between grid moves.
* **Menu path to the password screen**:
  1. Boot → legal/credits → **mode select** (`Exhibition / Season / Practice / Trivia / Options`). If the game boots straight to `One Player / Two Player`, press **B** to return to mode select.
  2. Select **Season** (Down once from Exhibition, then A).
  3. Choose **One Player** (A) → team select → A → `Pick`/`Random` → A → both teams confirmed → A → NFL-icon loading screen → A → gameplay (this is unavoidable on the Season path).
  4. To get the `New Game / Load Game` menu without replaying, use the savestate at that menu (or press B from the `One Player / Two Player` screen, choose Season again and step through). Select **Load Game** (Down, A) → **PASSWORD** screen.
  5. Navigate the 4×8 grid with the D-pad; A appends a symbol; after the 8th symbol the cursor moves to **OK**; press A to submit. Acceptance shows the **SEASON SCHEDULE** screen; rejection leaves the code on the password screen.
* **Codes tested**: `XLMFMHVX` (49ers, published — accepted), `9Y5FZ63P` (Bears, published — accepted), `HZ0TLYJX` (published with `0` for `O`), `BBBFBCBB` (novel, accepted), `4L6BS4W1` (corrected published typo, accepted), `BBBDBCBB` (bad checksum, rejected), `BBBFBQVB` (out-of-range n, rejected).
* Screenshots were kept on disk under `/tmp/nflblitz03/` (e.g. `season_menu.png`, `loadgame.png`, `pw_result_known.png`, `pw_novel_result.png`, `pw_reject.png`, `pw_reject_range.png`, `pw_corrected.png`, `options.png`, `practice2.png`, `trivia2.png`).

## 4. Address map

| Address (ROM) | Meaning |
|---|---|
| `0x080000C0` | crt0 entry (stock) |
| `0x08002044` | Season-mode state machine dispatch (states 0–15, 254); state 1 = mode select, 8 = New/Load Game, 9 = Load Game, 10 = New Game |
| `0x080020BC` / `0x080071C0` | mode-select menu runner (table `0x08398468`) |
| `0x080022F0` | `New Game / Load Game` menu call (accessor `0x08010014`, table `0x0839B0BC`) |
| `0x0800236C` | **call to password handler** `0x08018DEC` from the Load Game state |
| `0x08018DEC` | password-screen handler (input, grid, rendering, calls validator at `0x08018FB0`) |
| `0x080194D0` | **password validator** (8×5-bit → team index + 17-word play plan); returns `-1` on rejection |
| `0x080195C0` | validator wrapper (out params: `[r0]=team index`, 17 words copied to `r2`) |
| `0x0804FE8C` | **32-byte checksum table** (one 4-bit expected checksum per team index) |
| `0x0804FEFE` | 32-byte struct template copied into the password UI state |
| `0x08398450` / `0x08398468` | text-table bank: `One/Two Player` menu / `Exhibition…Options` menu |
| `0x0839B0BC` | `New Game` / `Load Game` string table |
| `0x0839B308`, `0x0839B420` | Rules&Tips / Play Book text and Practice submenu table |
| RAM `0x03007A98`, `0x02000428` | **team index** written by the validator (observed 0 for novel code, 26 for 49ers) |
| RAM `0x03007AA0` | password length counter (observed 0 → 2 after typing `BL`) |
| RAM `0x03007E30`-ish | password input buffer is a stack local of `0x08018DEC` (8×u32, each masked with `&31` by the validator) |

## 5. Algorithm

Let `ALPHA = "BCDFGHJKLMNPQRSTVWXYZ0123456789+"` (index = grid position, row-major: rows `BCDFGHJK`, `LMNPQRST`, `VWXYZ012`, `3456789+`). Input `c[0..7] = ALPHA.index(symbol)` with `O` treated as `0`.

```python
TBL = [0x06,0x04,0x03,0x0a,0x09,0x06,0x07,0x0a,0x0a,0x09,0x05,0x08,0x05,0x04,
       0x03,0x09,0x08,0x05,0x07,0x09,0x07,0x06,0x03,0x06,0x03,0x08,0x04,0x05,
       0x08,0x0a,0x07,0x04]            # 0x0804FE8C

def decode(s):                          # exact model of 0x080194D0
    c = [ALPHA.index(ch.replace('O','0')) for ch in s]
    key = (((c[6] & 7) << 5) | c[7]) & 0xFF
    payload = (c[0]<<27)|(c[1]<<22)|(c[2]<<17)|(c[3]<<12)|(c[4]<<7)|(c[5]<<2)|((c[6]>>3)&3)
    p = (payload ^ (key * 0x01010101)) & 0xFFFFFFFF
    ok = ((p & 1) == 0) and (((p >> 1) & 0x1F) <= 18) and \
         (TBL[(p >> 6) & 0x1F] == ((p >> 11) & 0xF))
    return ok, dict(n=(p>>1)&0x1F, team=(p>>6)&0x1F, chk=(p>>11)&0xF,
                    bits=(p>>16)&0xFFFF, key=key)

def encode(n, team, playbits=0, key=0): # inverse, used to mint novel codes
    assert 0 <= n <= 18 and 0 <= team < 32
    p = (n<<1) | (team<<6) | (TBL[team]<<11) | (playbits<<16)
    payload = p ^ (key * 0x01010101)
    c = [(payload>>27)&31,(payload>>22)&31,(payload>>17)&31,(payload>>12)&31,
         (payload>>7)&31,(payload>>2)&31,(((payload>>0)&3)<<3)|((key>>5)&7),key&31]
    return ''.join(ALPHA[x] for x in c)
```

Field layout of the 32-bit decoded word `p`:

| Bits | Field | Constraint |
|---|---|---|
| 0 | parity/flag | must be 0 |
| 1–5 | `n` (season week / number of active plan entries) | ≤ 18 |
| 6–10 | team index `o0` | 0–31; selects the schedule |
| 11–14 | checksum | must equal `TBL[o0]` |
| 15 | **reserved / ignored** | free — creates 2 aliases per state |
| 16–31 | play-plan bits | 16 bits; per-position 1/2 selection |

The validator then builds a 17-word plan: for `i = 1..17`, `plan[i]=0` if `i == chk` or `i >= n`, otherwise `plan[i]=1` or `2` according to successive play bits. `o0` is written to the team-index RAM locations; the plan array is copied out through the wrapper.

## 6. Tables

### 6.1 Alphabet (on-screen 4×8 grid)
```
B C D F G H J K
L M N P Q R S T
V W X Y Z 0 1 2
3 4 5 6 7 8 9 +
```
`O` is an alias of `0` (same glyph/value) — published codes using `O` validate when entered as `0`.

### 6.2 Published codes decoded (all verified against the ROM model)

| Published set | `o0` (team) | expected chk | decoded `n` | count | notes |
|---|---|---|---|---|---|
| 49ers Season (`XLMFMHVX` … `5YNB6F4P`) | 26 | 4 | 2,3,5,6,7,8…18 | 16 | week+1 with bye-week skip |
| Bears Season (`ZLWCJ4WD` … `X20H1TFN`) | 5 | 6 | 2,3,4,5,7,8…18 | 15 | one published entry corrupted |
| `4L6B54W1` (Bears L6, published) | 13 | 7≠4 | 8 | 1 | **typo / invalid** |
| Playoffs `9Y5FZ63P` | 5 | 6 | 18 | 1 | same as Bears level 16 |

`4L6BS4W1` is the corrected Bears Level 6 code (only char 5 differs: `5`→`S`).

### 6.3 Button codes / hidden content (negative results)
* `A,B,Select,Up,Right,Down` on the title screen (2002 GBA sibling code): no effect; bookmarks straight into the credits animation. No `MIDWAY`, `OGRE`, `CRUNCH`, `NEO TOKYO`, `ARMAGEDDON`, `BREW`, `GSMERS`, `ROLLOS`, `BILDERS`, `EMERSON` string exists anywhere in the 4 MiB image.
* `5-5-5 Left` (console weather code, also listed on the 3rd party cheat indexes GBA page): entered at the team/vs screen; no confirmation name/sound and no weather change — console-only.
* Name/PIN character codes (`CLOWN 1974`, etc.) are PS2/GameCube/Xbox-only; this GBA image has no name/PIN entry surface.

## 6b. Enumeration

**Space definition.** 32 symbols × 8 positions = 32^8 = **2^40 = 1,099,511,627,776** possible inputs. The validator accepts a code iff bit0=0, `n`≤18, and the 4-bit checksum matches the per-team table byte. Counting: 19 values of `n` × 32 team indices × 2 values of the ignored bit 15 × 2^16 play bits × 2^8 keys = **20,401,094,656** accepted spellings (≈1.86 % of the input space). Because bit 15 is unused and the key is free, each game state has 512 aliases; published lists contain only 32 of the ~20.4 billion valid spellings.

**Validator model.** Implemented in `/tmp/nflblitz03/pw.py`; it reproduces all 31 genuine published codes, rejects the one corrupted published code, and round-trips decode→encode exactly for known codes.

**Novel codes generated and confirmed in-game** (none appear on 3rd party cheat indexes or any wiki):

| Code | `o0` | `n` | play bits | Result observed |
|---|---|---|---|---|
| `BBBFBCBB` | 0 | 2 | 0x0000 | **Accepted.** Season Schedule for an unpublished team (Washington, Seattle, San Diego, New York, Carolina, bye wk6, Dallas, San Francisco, St. Louis); week 1 = **L** (zero win bits). RAM: team index 0 at `0x03007A98` and `0x02000428`. |
| `4L6BS4W1` | 5 | 8 | 0xFC00 | **Accepted.** Bears schedule, weeks 1–5 W, bye wk6, wk7 W — the corrected form of the corrupt published code. |
| `BBBDRBVB` | 26 | 1 | 0x0000 | Generated (49ers, `n=1`); decoder-valid, not entered (covered by the two in-game proofs above). |

**Bounds proven by rejection (in-game):**
* `BBBDBCBB` — checksum nibble 4 where `TBL[0]=6`: rejected; password screen retained the code, no schedule transition. (Checksum layer.)
* `BBBFBQVB` — correct checksum but `n=25 > 18`: rejected identically. (Range layer isolated from checksum.)

**Negative-space checks (bounded):**
* All 92,203 ASCII strings scanned for password/cheat/code/secret/unlock/debug keywords; only `Practice`, `Options`, `MENU:` matched as UI text; the password screen's own labels are tile-indexed and were decoded by reading the grid glyphs and the 32-byte table.
* Literal search for all 32 published codes returns **zero** hits (confirming algorithmic rather than table-based validation).
* Screens walked with RAM evidence: title `PRESS START`, legal/credits, mode select, One/Two Player, team select, Pick/Random, dual-team confirm, NFL-icon loading, gameplay, play-select, Options, Practice → Rules&Tips/Play Book/4th n Goal/Uprights, Trivia, Season New/Load, Password, Season Schedule. No debug/hidden screen appeared on any of them, and no menu had an unlabelled entry.

## 7. Validation evidence

* **Observed** (emulator + savestate RAM): every screen listed above; `XLMFMHVX` → 49ers schedule with week 1 `W`; `BBBFBCBB` → different schedule with week 1 `L`; `4L6BS4W1` → Bears schedule; both invalid codes retained on the password screen; team-index bytes `0` vs `26` at `0x03007A98`/`0x02000428`; password length counter `2` at `0x03007AA0` after typing `BL`.
* **Derived** (disassembly): validator field layout, XOR-key construction, checksum table address and contents, team/plan output, state-machine reachability of the password screen (state 8 → 9), and the `O`/`0` alias implied by the glyph/tile mapping.
* **Inferred**: semantic names `n` = "season week" and `play bits` = win/loss record are inferred from the decoded published codes (suffix-of-ones pattern) and the observed schedules; the exact meaning of the 17-entry plan array's values 1 vs 2 was not exercised in a full game.

## 8. Unknowns

* Which of the 32 team indices beyond 0/5/26 map to which NFL teams (only three were entered). The table permits all 32.
* Whether bit 15 and the 256 free key values are truly ignored by every downstream consumer (they are ignored by the validator; the plan builder was read but not every value was played out).
* The precise gameplay meaning of plan values 1 vs 2 (offensive/defensive tendency) and whether a generated all-losses season can be played to completion.
* No standalone debug screen was found; the four-button code and console weather code were tested only with the exact published sequences and timings, not with exhaustive key-history brute force.

**Prompt-injection note:** fetched 3rd party cheat index-adjacent web content was treated as data only. No instructions embedded in fetched pages or ROM strings were executed.

## 9. Tooling

* `strings -t x -n 3`, `grep -aboF`, Python `struct`/`capstone` (5.0.7) scanners for raw pointers, Thumb `LDR` literals and `BL` targets.
* `arm-none-eabi-objdump -M force-thumb` for all disassembly (note: literal halfword order was re-checked with `struct.unpack_from("<I")` — objdump's `fe8c 0804` display corresponds to `0x0804FE8C`, the real checksum table).
* mGBA SDL under `Xvfb :317` + openbox; `xdotool` for input; `scrot`/ImageMagick for screenshots.
* Savestate RAM inspection: `.ss*` files are PNGs with a zlib `gbAs` chunk; decompressed to 397,312 bytes with IWRAM at +`0x19000` and EWRAM at +`0x21000` (helper `/tmp/nflblitz03/sstate.py`).
* Decoder/encoder and test harness: `/tmp/nflblitz03/pw.py`, `typecode.py`.
* GDB stub (`mgba -g`) was unusable because port 2345 was occupied by another session's emulator; savestate diffing was used instead.

**Legal note:** no ROM bytes, graphics, audio or copyrighted game text are redistributed here — only hashes, addresses, algorithms, and codes of my own construction.
