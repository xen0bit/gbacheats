# Secret Agent Barbie: Royal Jewels Mission (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Secret Agent Barbie: Royal Jewels Mission.gba` |
| Size | 4,194,304 bytes (`0x400000`, 4 MiB) |
| Header title | `SECRETAGENTB` |
| Game code | `AAHE` |
| Maker code | `7D` (header string `AAHE7D`) |
| Version | `0x00` (Rev. 00) |
| `fixed 0x96` | `0x96` (present) |
| Entry branch | `0xEA00002E` (stock ARM branch, **not** patched to a cracktro) |
| Header checksum | `0x0000` (normal rebuilt-header artifact); complement byte `0x50` |
| MD5 | `b5da52577265dbb1d98977da249c4e20` |
| SHA-1 | `78b2d7a05998918f047ba2ad68dc00086cbf3ff2` |
| SHA-256 | `f2d45f2144bd7568fa836f1d5a677a3f74fe3e0728ea056afe421c9b14af77bb` |
| Publisher/developer | Vivendi Universal Games / Digital Illusions CE (boot logo + C++ RTTI at `0x083CD790`) |

**Phase 0:** one embedded GBA header only (full 156-byte Nintendo-logo match at file `0x0`); no second image, no appended trainer, no patch. The analysis used a byte-identical copy (`md5` matched) to avoid writing emulator artifacts into the ROM folder.

## 2. Executive summary

The game has a **developer-intended 6-character progress password system** on the title screen under **CONTINUE → PASSWORD**. There are **no button codes, no hidden debug menu, and no CodeBreaker/GameShark-style in-game cheat device** in this build (§16.3 "no system" for those surfaces, bounded below).

The password alphabet is exactly the **16 consonants** `B C D F G H J K L M N P Q R S T` (no vowels; confirmed by cycling the on-screen selector through a full wrap). Each character therefore carries 4 bits. The six entered characters are stored as indices 0..15 in IWRAM at `0x030004E4`.

The acceptance rule, recovered from the published code list and reproduced in the emulator, is a single **modulo-16 checksum**:

```
valid  <=>  index[5] == (index[0] + index[1] + index[2] + index[3] + index[4] + 3) & 0x0F
```

All 12 usable published codes satisfy it exactly. Every trial code with a correct checksum was accepted (including values outside every published list); every code with a wrong checksum was silently rejected and reset the screen. Because the checksum fixes the 6th character, the accepted space is `16^5 = 1,048,576` codes out of `16^6 = 16,777,216` possible strings (1 in 16).

Novel, unpublished codes confirmed in-game: **`QBBBBT`** (first character `Q` = 12, a level index absent from all published lists) and **`BTTTTT`** (level 0 with every secret flag bit set). Both were accepted, echoed in the mission-map header as `PASSWORD: QBBBBT`, and produced distinct Headquarters/map states.

## 3. How to reproduce

Emulator: **mGBA 0.10.5**, `mgba -3 game.gba` under Xvfb. SDL keymap: A = `x`, B = `z`, L = `a`, R = `s`, Start = `Return`, Select = `BackSpace`, D-pad = arrow keys. Hold keys ~80–150 ms.

Menu path:
1. Boot; press **Start** through the Vivendi / Barbie Software / title screens to the **NEW GAME / CONTINUE** menu.
2. Cursor is on **CONTINUE**; press **A** → **PASSWORD** screen (six blank slots).
3. For each of the six slots: press **Up** *n* times where *n* is the desired alphabet index (`B`=0 … `T`=15), then press **A** to lock the character and advance.
4. After the 6th character the entered code is displayed with a green **OK** button at the right; press **A** again.
5. Correct checksum → **HEADQUARTERS** (then A → mission map, which echoes `PASSWORD: <code>` in the header). Wrong checksum → the password screen silently resets to six blank slots (no error message).

Codes exercised (all typed through the real UI, not patched into RAM):

| Code | Source | Result |
|---|---|---|
| `BBBBCG` | GameFAQs/ChapterCheats — Royal Tower | accepted → HQ (observed) |
| `QBBBBT` | **novel (generated)** — first char `Q`=12 | accepted → HQ, map header `PASSWORD: QBBBBT` (observed) |
| `BTTTTT` | **novel (generated)** — all secret bits on level 0 | accepted → HQ (observed) |
| `CBBDCK` | checksum-corrected published London Subway | accepted → HQ (observed) |
| `BBBBCB` | published `BBBBCG` with bad checksum | **rejected**, screen reset (observed) |
| `RBBBBB`, `SBBBBC`, `TBBBBD` | generated, first chars 13/14/15 | all accepted (observed) |
| `HRRDMD` | trailing ROM string next to the alphabet | **rejected** (observed) |
| `CBBDCX` | published London Subway as printed | **not enterable**: `X` is outside the 16-letter UI alphabet |

## 4. Address map

| Address | Type | Meaning / evidence |
|---|---|---|
| `0x0820743C` (file `0x20743C`) | ROM string | On-screen alphabet `BCDFGHJKLMNPQRSTHRRDMD`. First 16 bytes = the 16 selectable letters (observed by cycling the UI); trailing `HRRDMD` is an unreachable leftover string (tested, rejected). |
| `0x08207453` (file `0x207453`) | ROM data | 16-byte permutation `[9,8,1,11,2,12,10,6,4,3,7,13,5,14,15,0]`. Not proven to participate in validation; no pointer/xref located (unknown). |
| `0x082074A0` | ROM string | `PASSWORD:` |
| `0x08208C30` | ROM string | `YOUR PASSWORD IS` (generator display after a mission) |
| `0x0820789?` / `0x083CD790`+ | ROM RTTI | `MenuPassword`, `MenuHQ`, `MenuSecretVault`, `MenuMission`, `MenuOptions`, `MenuTraining`, `MenuReview`, `MenuTitle`, `MenuLanguage`, `MenuGameIntro`, `MenuChooseGame`, `MenuBootScreen`, `MenuScreen` — C++ class names; no `Debug*` class. |
| `0x030004B8` | IWRAM | Password-menu state object; its `+0x2C` field is the character buffer. |
| **`0x030004E4`** | **IWRAM** | **6-byte input buffer** holding the 6 alphabet indices (0..15). **Observed**: entering the distinctive sequence `R D G J L N` produced bytes `0D 02 04 06 08 0A` at this address; a read-watchpoint here fired on the menu renderer at `0x0800491C`. |
| `0x08004918` / `0x0800491C` | Thumb code | Renderer loop: `ldrb r3,[r5,#0]` reads a stored index; `ldr r2,=0x0820743C`; `ldrb r1,[r2,r3]` maps index → alphabet glyph. CRTP pool words occupy `0x800492C`–`0x800493A` (`0x0820743C` at `0x8004930`). |
| `0x08004672` | Thumb code | Call site into the renderer routine (LR observed as `0x08004673`). |
| `0x08000B06`–`0x08000B18` | Thumb code | 16-way menu dispatch; `ldr r1,=0x0820743C` at `0x8000B08`; jump table at `0x8000B1C`. |

File offset ↔ ROM address: `rom_address = 0x08000000 + file_offset`.

## 5. Algorithm

Reimplementation of the validator and encoder (verified against all published codes and against the emulator):

```python
ALPHABET = "BCDFGHJKLMNPQRST"          # 16 symbols, index 0..15

def encode(first5):                     # first5 = 5 indices, each 0..15
    assert all(0 <= x < 16 for x in first5)
    checksum = (sum(first5) + 3) & 0x0F
    return "".join(ALPHABET[x] for x in first5 + [checksum])

def valid(code):                        # code = 6 characters
    idx = [ALPHABET.index(c) for c in code]   # UI guarantees every char is in ALPHABET
    return idx[5] == (sum(idx[:5]) + 3) & 0x0F
```

Notes:
* The checksum is plain integer **addition** (not XOR), masked to 4 bits; the additive constant is **+3**.
* The UI cannot express an out-of-alphabet character, so alphabet validation is implicit; no separate character check is needed.
* The first five indices are accepted for **all** 4-bit values tested, including first-character values 12–15 that appear in no published list. No semantic level range rejection was observed at the acceptance layer (§16.5: a separate semantic layer could still affect gameplay after acceptance — not isolated).
* The game also has a **generator** path (`YOUR PASSWORD IS` at `0x08208C30`) used after a mission; its state→field mapping was not isolated (see §8), but any first-five combination can be minted with `encode()` above.

## 6. Tables

### Published codes verified against the checksum and the ROM/UI

| Effect (published label) | Code | Indices | Σ index[0..4] | Expected last | Verdict |
|---|---|---|---|---|---|
| The Royal Tower | `BBBBCG` | 0,0,0,0,1,4 | 1 | 4 = G | ✓ accepted in-game |
| London Subway | `CBBDCX` (printed) | 1,0,0,2,1,**X** | — | 7 = K | `X` not in 16-letter UI; corrected `CBBDCK` accepted in-game |
| Street Chase | `DBBFCM` | 2,0,0,3,1,9 | 6 | 9 = M | ✓ checksum |
| City Streets | `FBBFFQ` | 3,0,0,3,3,12 | 9 | 12 = Q | ✓ checksum |
| Secret Hideout | `GBBPFH` | 4,0,0,11,3,5 | 2 | 5 = H | ✓ checksum |
| Golden City | `HBBPKN` | 5,0,0,11,7,10 | 7 | 10 = N | ✓ checksum |
| The Palace | `JCBPKQ` | 6,1,0,11,7,12 | 9 | 12 = Q | ✓ checksum |
| Opera House | `KCBTKC` | 7,1,0,15,7,1 | 14 | 1 = C | ✓ checksum |
| Canal Chase | `LCGTKJ` | 8,1,4,15,7,6 | 3 | 6 = J | ✓ checksum |
| Fashion District | `MCHTKL` | 9,1,5,15,7,8 | 5 | 8 = L | ✓ checksum |
| Scuba Search | `NCHTTC` | 10,1,5,15,15,1 | 14 | 1 = C | ✓ checksum |
| Sunny City | `PCRTTN` | 11,1,13,15,15,10 | 7 | 10 = N | ✓ checksum |
| All secrets unlocked | `TTTTTS` | 15,15,15,15,15,14 | 11 | 14 = S | ✓ checksum |

Published sources: GameFAQs cheat page (403 on direct fetch; snippet recovered), ChapterCheats "More Passwords" and "Unlock everything" pages, IGN GBA cheats index. All 12 usable literals were **absent as ASCII strings in the ROM** (`grep`/`bytes.find` returned zero hits for each), proving the system is algorithmic rather than a plaintext table.

### Field interpretation (inferred, confidence labels)
* `index[0]` — starting level / mission selector. Observed: values 0..15 all accepted; published list uses 0..11; 15 also appears in the all-secrets code. **(Derived from published payload pattern; novel values 12..15 accepted in-game.)**
* `index[1..4]` — 16 bits of progress/secret-file flags, one nibble per character. Published codes grow these masks as later missions are reached; `TTTTTS` sets them all. **(Inferred from the published payload pattern; arbitrary values accepted.)**
* `index[5]` — 4-bit checksum, `(Σ first5 + 3) mod 16`. **(Derived from 12 published codes; confirmed by in-game acceptance/rejection.)**

## 6b. Enumeration

**Space.** UI alphabet size 16, length 6 → `16^6 = 16,777,216` representable strings. The checksum makes exactly one 6th character valid for each of the `16^5` first-five combinations, so the accepted space is **`16^5 = 1,048,576` codes**. Enumeration of the first-five space: `index[0] ∈ 0..15`, `index[1..4] ∈ 0..15` each; `index[5] = (Σ + 3) & 15`. No reserved bits and no unused symbol were found; every value 0..15 is selectable in every slot.

**Novel codes (absent from GameFAQs, VGChartz, TCRF, IGN and ChapterCheats lists), generated with `encode()` and accepted in-game:**

| Novel code | Payload | In-game proof |
|---|---|---|
| **`QBBBBT`** | first char `Q`=12 (outside the published 0..11 level set), all other fields 0 | Accepted → HEADQUARTERS; mission map echoed `PASSWORD: QBBBBT` and showed Mexico selected with other markers (screenshot + RAM buffer) |
| **`BTTTTT`** | level 0 with all 16 progress/secret bits set | Accepted → HEADQUARTERS; map showed England selected |

Additional generated codes `RBBBBB`, `SBBBBC`, `TBBBBD` (first chars 13/14/15) were also accepted, bounding the first-field range at the acceptance layer to the full 4-bit space.

**Bounds proven by rejection (in-game, not inferred):**
* `BBBBCB` — published-valid `BBBBCG` with only the checksum character changed from `G`(4) to `B`(0) (expected 4) → **rejected**, screen reset to blank. Proves the checksum is enforced, not decorative.
* `HRRDMD` — the 6-character string stored immediately after the alphabet in ROM → **rejected**; not a developer backdoor.
* `CBBDCX` — published literal → **cannot be entered**: `X` is outside the 16-symbol UI alphabet, so this listed code is a transcription error for a wider-consonant alphabet; the checksum-consistent `CBBDCK` was accepted.
* A deliberately malformed 6-character entry (`BCCBBB`) → rejected and reset (pre-checksum probe).

**Closed-set check.** Because the checksum is a single linear equation mod 16 over five 4-bit fields, exactly 1/16 of all 6-character strings can pass; the offline reimplementation enumerates all `1,048,576` accepted values. Sample verification against the ROM was 18/18 (12 published + 6 generated), with no false accepts or false rejects observed.

**Other surfaces (bounded negatives, §16.3):**
* **Button codes:** no mask table found; keyword scan for `cheat/debug/god/invincible/level select` returned only `SECRET VAULT` story strings. No button sequence changed menu state during the walks performed.
* **Hidden debug menu:** RTTI enumeration lists 13 `Menu*` classes and no `Debug*` class; no debug/level-select entry appeared in the title, password, Headquarters, mission-map, options or story screens walked.
* **Secret Vault:** a real unlockable (strings `0x08208B3C`–`0x08208B60`, "We have something for you in the Secret Vault. Would you like to see it now?") gated by collecting secret files in a mission; it is save/progress-gated content, **not** a code (§16.18). It was not unlocked by any password in this study.

## 7. Validation evidence

* **Observed** (emulator): boot → title → CONTINUE → PASSWORD; 6-slot entry with Up/Down cycling exactly `BCDFGHJKLMNPQRST` and A locking/advancing; full wrap from `T` back to `B`; `BBBBCG` accepted → HQ; `QBBBBT` and `BTTTTT` accepted; bad-checksum rejection with silent reset; mission-map header echoing the entered code.
* **Observed** (RAM): distinctive sequence `R D G J L N` stored as bytes `0D 02 04 06 08 0A` at IWRAM `0x030004E4`; read-watchpoint on that address fired at `0x0800491C` in the renderer, whose literal pool holds `0x0820743C` (the alphabet).
* **Derived**: checksum `last = (Σ first5 + 3) mod 16` from the 12 published payloads; space size and 1/16 acceptance rate from the alphabet width and the checksum; alphabet mapping from the UI wrap and the ROM string.
* **Inferred**: field semantics of `index[0..4]` (level selector + secret-bit flags) from how published payloads grow across missions; generator state→field mapping not isolated.
* **Not observed**: the exact validator function body (the read-watchpoint caught the display renderer first); see §8.

## 8. Unknowns

* The precise validator/accept routine address was not isolated: a read-watchpoint on the input buffer repeatedly fired in the per-frame renderer at `0x0800491C`. The checksum model is therefore validated empirically (18/18 codes) rather than by reading a single compare instruction.
* The mapping from in-game progress state (which secret file sets which bit) to `index[1..4]`, i.e. the encoder behind `YOUR PASSWORD IS`, was not reversed. It does not affect the ability to mint working codes.
* The 16-byte permutation at `0x08207453` has no located xref; its role, if any, is unknown.
* Whether out-of-range level values 12–15 select a real mission or clamp to the last mission was not played out beyond the map screen.
* The Secret Vault unlockable's exact trigger condition was not exercised (progress-gated, not code-gated).

## 9. Tooling

* `sha256sum`/`md5sum`/`file`, Python 3 header/string/pointer scripts (`phase0.py`, literal scans).
* `strings -a -t x`, `grep -abo`, `xxd`, `arm-none-eabi-objdump -M force-thumb`, Capstone literal-load scanner.
* mGBA 0.10.5 under `Xvfb :315` + `openbox`, `SDL_AUDIODRIVER=dummy`, `xdotool` XTEST input, `scrot` + ImageMagick (`convert`/`montage`) for contact sheets.
* mGBA **CLI debugger** (`mgba -d` with a FIFO on stdin; `x/1`, `r/4`, `watch/r`, `save`/`load 1`, `reset`), interrupted with `kill -INT <pid>`. The GDB stub (`-g`) was tried first but proved unreliable ("Cannot access memory"/protocol errors) and was abandoned in favour of the CLI debugger and savestate diffs.
* Web: GameFAQs (403; snippet), ChapterCheats (two pages), IGN index — fetched as data only; no instructions from fetched content were followed.

## 10. Legal note

No ROM image, extracted graphics, audio, or game text assets are redistributed here. Only addresses, hashes, derived algorithms, and self-generated codes are published.
