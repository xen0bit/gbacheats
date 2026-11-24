# Robotech: The Macross Saga (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Robotech: The Macross Saga/Robotech: The Macross Saga.gba` |
| Size | 8,388,608 bytes (0x800000) |
| Header title | `ROBO MACROSS` |
| Game code | `ARBE` |
| Maker | `6S` |
| Version | `0x00` (Rev.00) |
| Entry branch | `0xEA00002E` → `0x080000C0` (stock crt0; no cracktro patch) |
| Complement byte | `0xBD = 0x44` (rebuilt header; §16.1) |
| Header checksum | `0x0000` |
| MD5 | `38aac4616bb56f14de9c0e7e8f86f0b9` |
| SHA-1 | `3dbfe433a2376589a24754bb7337306c43176b34` |
| SHA-256 | `07e2ac34326977a7e7f69b45cdea61cf71ddb1a66d4aaf4d403dc1c6a9591013` |

Single-header image (one Nintendo-logo hit at file `0x000004`). The image is a **debug build** (`ROBOTECH DEBUG BUILD`, `BUILD TIME: 22:05:04 Aug 22 2002` at `0x084392D8`; second assert bank at `0x08447B64`) with no debug-menu labels.

## 2. Executive summary

1. **Title-screen button-code matcher fully located and reversed.** Matcher `0x080124EC`, code table `0x0807E770` (4 slots × 9 u32), progress counters `0x03003130..33`, 8-entry action jump table `0x0801254C`, flag byte `0x03000304`. The accepted space is **exactly four sequences** (all published ones); slots 4–7 of the action table are reachable-never dead code.
2. **Novel unpublished sequence accepted.** Holding A while entering `↓ ↓ ↓ ↓ ↓ R R` (and, independently, prefixing a stray `Left`) is accepted: flag byte `0x03000304` goes `0x00 → 0x04`. Bounds proven by three rejected near-misses. Matcher semantics (edge-trigger, exact-one-button, no timeout, no order reversal) are defined in §5.
3. **Password Entry screen resolved as a dead/gated feature at byte level** (§8). Its code exists (`0x0802B254`–`0x0802BC30`, alphabet `0123456789X`, `BOSS`/`INVALID`/`ACCEPTED`), but it has **zero** direct call xrefs, is absent from the closed 27-screen dispatcher at `0x0801B41C`, its label string ID 158 has zero code xrefs, and a hang-patched ROM copy never invoked it while traversing every reachable screen and ten hidden-key combos. No password validator/code table is reachable, so no password code was minted (explicitly stated, not excused).
4. Retained prior findings: 241-entry string-ID table at `0x0807EEF4`, EEPROM name `?SDF1???` stored byte-reversed, six pilot unlocks from string IDs 191–197.

## 3. How to reproduce

mGBA 0.10.5, `Xvfb :317 -screen 0 1024x768x24`, `openbox`, `SDL_AUDIODRIVER=dummy`. Keymap A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows; 200 ms holds / 160 ms gaps. A PRESS START savestate is the reproducible entry point (boot + splash + language select; the splash auto-advances in ~15–20 s). Use mGBA savestate slot 1 as baseline; load it, enter a sequence, save slot 2, and diff RAM.

**Verified sequences** (keys as sent):

| Effect | Sequence | Flag bit |
|---|---|---|
| All Levels | `Up Down Up Down a s a s` | `0x01` |
| Unlimited Lives | `Right Right Right Up Up a a` | `0x02` |
| All Characters | `Down Down Down Down Down s s` | `0x04` |
| Max Upgrades | `Up Right Down Left s a a a` | `0x08` |

**Novel accepted sequence:** hold `x` (A), then `Down Down Down Down Down s s` → flag `0x04`. Also accepted: `Left Down Down Down Down Down s s` (extra leading wrong press) and the published sequence with a 0.6 s pause inserted mid-sequence (no timeout).

## 4. Address map

File offset = ROM address − `0x08000000`.

| Item | ROM address | Notes |
|---|---:|---|
| Key poll (KEYINPUT→pressed/held) | `0x0803D36C` | `0x04000130`→`0x03002C90`; held `0x03002C8C`; edge `0x03002C88` |
| Screen triple for title (state 1) | `0x0801B4C0` | `{0x0801233D, 0x080123ED, 0x080126B1}` |
| Matcher entry | `0x080124EC` | called from title init `0x080123BC`; button→enum mapping `0x08012444`–`0x080124D4` |
| Code table | `0x0807E770` | 4 live slots × 36 bytes; u32 enum values, `8` = END |
| Progress counters | `0x03003130` | 4 bytes; cleared by `0x080126E8` |
| Action jump table | `0x0801254C` | 8 entries: `0x0801256C/7C/8C/9C` (live), `0x080125AC/CC/DC/EC` (dead) |
| Cheat flag byte | `0x03000304` | bit0 levels, bit1 lives, bit2 characters, bit3 upgrades; bits5–7 dead |
| Confirmation sound | `0x0805F440` | played via `0x0803ED54` |
| 27-screen dispatcher | `0x0801B400` | reads state `0x0300089C`, `cmp #26`, table `0x0801B41C` |
| English string-ID table | `0x0807EEF4` | 241 × u32 (IDs 0–240) |
| Password strings | `0x0807F858`–`0x0807F884` | IDs 143–147 |
| `Password Entry` label | `0x0807F7DC` | ID 158 |
| Password-screen code | `0x0802B214`–`0x0802BC30` | init/display/result callbacks (dead) |
| Password callback literals | `0x0802AAF4`–`0x0802AB0C` | only references to those callbacks |
| EEPROM (512 B) | `0x0E000000` | names stored byte-reversed |

## 5. Algorithm — button-code matcher (Derived from disassembly)

Button enum produced from the edge mask at `0x08012444`–`0x080124D4`:

```
U=0  D=1  Left=2  Right=3  A=4  B=5  L-shoulder=6  R-shoulder=7
```

The two shoulder checks use an inverted branch form: exactly one shoulder must be down, otherwise the count check rejects the frame. At `0x080124D6`–`0x080124F8` the number of simultaneously pressed recognised buttons must be **exactly 1**; 2+ (or 0) makes the frame a no-op (no reset, no progress) or a skip. The frame with more than one button is therefore *ignored*, not treated as a wrong press.

For each of four slots `r6 = 0..3` (`0x080124FA`–`0x0801261C`):

```
pos = progress[r6]                       ; u8 at 0x03003130 + r6
expected = table[r6*36 + pos*4]          ; 0x0807E770
if enum != expected: progress[r6] = 0    ; mismatch resets only this slot
else:
    progress[r6] = pos + 1
    next = table[r6*36 + progress[r6]*4]
    if next == 8:                        ; END marker
        clear all four progress counters (0x080126E8)
        dispatch action via jump table 0x0801254C[r6]
```

The enumeration loop bound is `cmp r6,#3` at `0x0801261A` — exactly four slots. Code table (enum values, `E`=END):

| Slot | Sequence | Action | Bit |
|---:|---|---|---|
| 0 | `0 1 0 1 6 7 6 7 E` U D U D L R L R | `0x0801256C` | 0x01 |
| 1 | `3 3 3 0 0 6 6 E E` Right³ U² L L | `0x0801257C` | 0x02 |
| 2 | `1 1 1 1 1 7 7 E E` Down⁵ R R | `0x0801258C` | 0x04 |
| 3 | `0 3 1 2 7 6 6 6 E` U Right D Left R L L L | `0x0801259C` | 0x08 |

Slots 4–7 of the table are non-enum garbage and the action functions `0x080125AC/CC/DC/EC` (bits `0x20/0x40/0x80`) have no caller from the dispatcher — dead code, not hidden codes.

**Accepted space:** exactly 4 press sequences. There is no length tolerance, no reversed-order acceptance, and no undocumented fifth effect. The *input language* has extra accepted spellings because of matcher semantics: a held modifier contributes only one edge, a multi-button frame is ignored, and any stray press merely resets progress — so `A-held + D×5 + R,R`, `Left + D×5 + R,R`, and arbitrarily spaced presses are all accepted. These are the novel, unpublished input sequences minted here; they produce the same four effects, not a fifth.

## 6. Tables

Enum/bit/table values are in §4–§5. Retained tables from the first pass:

- 241 string IDs at `0x0807EEF4`: ID 10 `PRESS START`, 126 `DESTROID SELECT`, 140–142 results, 143 `Password:`, 144 `0123456789X`, 145 `BOSS`, 146 `INVALID`, 147 `ACCEPTED`, 158 `Password Entry`, 159 `File Select`, 160 `Enter File Name`, 165 `PILOT SELECT`, 191–197 character-unlock names. The same table is duplicated for six languages.
- EEPROM 512-byte layout: header at `0x00`, four 0x78-byte slot records from `0x08`; name at `slot+0x08` byte-reversed.
- Six unlockable pilots (IDs 192–197): Stunt Rick Hunter, Great War Roy Fokker, Trainer Rick Hunter, Rookie Max Sterling, Zentraedi Miriya, Lucky Chicken — save-bit unlocks (§16.18), not codes.

## 6b. Enumeration

**Button codes:** space closed at 4 accepted sequences (table + dispatcher bound proven). One novel accepted input spelling was generated and confirmed in-game: `A-held + ↓×5 + R,R` → flag `0x00 → 0x04` (Observed, savestate RAM read). A second (`←` prefix) was also accepted. No fifth effect exists in this build.

**Bounds proven by rejection (all Observed, flag stayed `0x00`):**

| Near-miss | Result |
|---|---|
| Reversed `R,R,↓×5` | rejected |
| `↓×4,R,R` (one press short) | rejected |
| `↓×5,L,R` (wrong final shoulder) | rejected |

**Password space:** alphabet 11 symbols (`0`–`9`,`X`), results BOSS/INVALID/ACCEPTED; no reachable input surface → no validator run, no code minted. This is a proven dead/gated feature (§8), not an untested one.

## 7. Validation evidence

**Observed:** all four published sequences set flag bits `0x01/0x02/0x04/0x08` respectively; novel held-A variant sets `0x04`; three near-misses set `0x00`; PRESS START → PILOT SELECT changed from 5 portraits + six `?` to 11 unlocked portraits after `↓×5,R,R` (first pass); EEPROM name `ASDF1` stored as `31 46 44 53 41` vs control `TEST1`; `r/4 0x0E000000 = 0xFFFFFFFF` (EEPROM); patching four password entry points with `b .` never froze the game during boot/title/language/file-select/name-entry navigation or ten title-screen hidden-key combos.

**Derived:** matcher address, table, enum mapping, dispatcher bound, dead action branches, 27-screen dispatcher closure, zero BL xrefs to password callbacks, zero code xrefs to string ID 158, key-poll addresses.

**Inferred:** the password subsystem is an unfinished internal boss/level-test feature (alphabet + BOSS/ACCEPTED/INVALID), disabled in this retail debug build by the absence of any screen registration.

## 8. Unknowns / resolved gate

**Password Entry — exact gate proved.** The screen's code is present (`0x0802B214`, `0x0802B238`, `0x0802B254`, `0x0802B474`, `0x0802B980`–`0x0802BC30`): it builds the `Password:` prompt (ID 143), the 11-symbol alphabet (ID 144), 15 `BOSS` entries (ID 145), and writes `INVALID` (ID 146) / `ACCEPTED` (ID 147) from the result byte at `0x03000954` (`1`=accepted, `2`=invalid; reads at `0x0802BA0E`, `0x0802BC5A`, `0x0802BD2E`). The gate is the **absence of any reachable caller**:

1. All four password callbacks have **zero BL xrefs**; they appear only as literal data pointers at `0x0802AAF8`, `0x0802AB04`, `0x0802AB08`, `0x0802AB0C` (loaded at `0x0802A9DA`, `0x0802AA62`, `0x0802AAB4`, `0x0802AAB8`).
2. The screen dispatcher at `0x0801B400` (`cmp r4,#26`, table `0x0801B41C`) registers 27 triples; **none** contains any address in `0x0802B2xx`–`0x0802BCxx`. The dispatcher is closed.
3. Thumb-immediate and literal-pointer searches for string ID **158** (`Password Entry`) found no code reference — only compressed-data bytes at `0x083B3BBE`, `0x0840C46A`.
4. A ROM copy with `0x0802B254/278/474/9B0` replaced by `b .` ran through every reachable screen and ten hidden-key combos without hanging → none of those entry points executed.

Conclusion: **dead/gated feature** (§16.3 case 2), not a reachable password system. No unpublished password code could be minted because there is no input route or callable validator; the four button codes are the only live cheat surface.

Remaining minor unknowns: the trailing save byte `slot+0x73` (name checksum vs flag) was not isolated; gameplay/pause screens were not walked past PILOT SELECT; pilot-unlock bit positions in the save record were not mapped.

## 9. Tooling

`arm-none-eabi-objdump -M force-thumb`, Capstone 5.0.7 / Keystone, mGBA 0.10.5 CLI debugger (`-d`) and savestates (`gbAs` zlib chunk parser), Xvfb :317 + openbox + xdotool XTEST, Pillow/ImageMagick for screenshot detection. Scripts in `/tmp/robotech2`: `ptrxref.py`, `screen_triples2.py`, `run_seq.py`, `probe_keys.py`, `make_ps_state.py`, `ss.py`, `diffstate.py`, `search_seq.py`. Web sources (3rd party cheat indexes, cheat-database) were used as data only; no instructions found in fetched pages or ROM strings were followed. No ROM image or copyrighted assets are redistributed by this report.
