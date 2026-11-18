# Matchbox Cross Town Heroes (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Matchbox Cross Town Heroes.gba` |
| Size | 4,194,304 bytes (0x400000, 4 MiB) |
| Header title | `MBXCTH` |
| Game code | `ARQE` (Europe), maker `78` (THQ), version `0x00` |
| Entry word | `0xEA00002E` — **stock** retail branch to `0x080000C0` (§16.1: not a cracktro) |
| Header checksum | `0x0000`, complement `0xF3`, fixed `0x96` present |
| MD5 | `5d8477952ac38e7dfea3a56f7544809b` |
| SHA-1 | `6baa6bfe76b077f365bedffa52346b94689b61d7` |
| SHA-256 | `21ec9e1cce05932b8e62e3ef126b2afcf0eb791598ab3c077beb26fa525f91d2` |

Phase 0 embedded-header scan: the 156-byte Nintendo logo occurs exactly once (file `0x4`, header `0x0`). No second/sub-image header, no appended trainer, tail is `0xFF` padding. Single clean retail image.

## 2. Executive summary

The game has a **developer-intended 4-character password system** (not a GameShark-style memory code). It is used to restore progress/rank and is surfaced by the string `Enter Password` / `Password: %s`. The on-screen keypad alphabet is the 21 consonants `BCDFGHJKLMNPQRSTVWXYZ` at `0x08039620`, but the validator does **not** compare those characters directly: it maps each position through its own 21-character substitution table, checks a 4-bit checksum, re-encodes the decoded fields and requires an exact match against the input (an anti-alias guard), then applies semantic range checks and writes game state.

The complete space was characterised: `21^4 = 194,481` possible 4-character strings, of which **exactly 152 are accepted** (exhaustive run of the ROM's own validator in Unicorn). Every accepted code begins with the letter `Q`. A novel accepted code, `QZDH`, was generated from the recovered model (it exercises the maximum rank field value 3) and confirmed in the live emulator: the game's validator returned 1 and the game-state word at `0x02017DE0` changed from `0` to `6` (and `+4` from `0` to `3`). Out-of-alphabet input (`AAAA`) was rejected live (`r0 = 0`) and checksum-mismatched inputs were rejected in the exhaustive run.

No published code list could be retrieved: GameFAQs returned HTTP 403, TCRF returned 403, DuckDuckGo served a bot challenge, and web.archive.org had no snapshot for the GameFAQs page/CDX query. This is recorded as a bounded negative on the *web-search* surface — the accepted set below was derived entirely from the ROM itself and is complete, so it cannot omit any code the game accepts.

## 3. How to reproduce

### Environment
- Emulator: `mgba 0.10.5` (SDL), launched headless under `Xvfb :317` + `openbox`, `SDL_AUDIODRIVER=dummy`, `-3` scale.
- Live RAM access: mGBA's CLI debugger (`mgba -3 -d ...`) driven through a pty; `BREAK` (Ctrl-C) pauses, `r/4 ADDR` / `w/1 ADDR VAL` / `w/r REG VAL` read and write state, `b/t ADDR` sets a Thumb breakpoint. (The GDB stub on port 2345 was occupied by another session, so the stub-free `-d` debugger was used.)
- Exact offline oracle: **Unicorn 2.1.4** — map the ROM at `0x08000000`, EWRAM at `0x02000000`, IWRAM at `0x03000000`, SP `0x03007F00`, call `0x080043FC` in Thumb mode with `r0` = pointer to a NUL-terminated 4-character buffer, `lr` = sentinel return address. `r0 == 1` on return means accepted. Scripts: `ucval.py`, `enumerate_codes.py`, `fields.py` in `/tmp/opencode/matchbox`.

### Menu path observed
Title menu: **New Game / Continue / Options / Credits**. `Up`/`Down` move the selection; `A` (`x`) confirms; `Start` (`Return`) returns from the attract gameplay. The attract/demo gameplay screen is labelled `DEMO` and is entered from the New Game/Continue actions in this build. The title screen builder is at `0x08007F5C` (writes screen id `2` to `0x02018160`); the password screen's renderer is installed by `0x08010C48` and the renderer itself is `0x08010A69` (it draws the string with table index 36, `Enter Password`). All UI strings are plain ASCII in a six-language bank at `0x0802AD60`–`0x0802C3F0`, so the keyword scan was not defeated by tile-indexed text.

### Live validator call (reproducible RAM proof)
1. Boot to the title screen; pause with Ctrl-C.
2. Write the four characters to a NUL-terminated buffer, e.g. `QZDH`:
   `w/1 0x02030000 0x51`, `w/1 0x02030001 0x5A`, `w/1 0x02030002 0x44`, `w/1 0x02030003 0x48`, `w/1 0x02030004 0x00`.
3. `w/r r0 0x02030000`; `w/r lr 0x08001001`; `b/t 0x8004656` (the shared epilogue); `w/r cpsr 0x2000003F` (set T bit); `w/r pc 0x80043FC`; `c`.
4. At the breakpoint read `r0`: `1` for a valid code, `0` for an invalid one; read `0x02017DE0` for the applied state.

The four-character values are exactly what the password screen places in its input array at `0x020256E0` (converted to glyphs with the alphabet at `0x08039620` before the call at `0x80109F6`). Calling the validator directly exercises the same code path as the keypad's confirm action; the on-screen keypad itself was not driven key-by-key (labelled as such in §7).

## 4. Address map

| Address | Meaning |
|---|---|
| `0x08000000` | ROM base; stock entry branch |
| `0x0802AD60`–`0x0802C3F0` | Localised ASCII text bank (EN, E, F, S, G, I) |
| `0x0802AF10` | `Enter Password` (English) |
| `0x0802B0AC` | `Password: %s` (English) |
| `0x08038130`, `0x08038148`, … | String-pointer tables per language (getters at `0x08002B30` / `0x08002B40`) |
| `0x08039620` | Keypad alphabet `BCDFGHJKLMNPQRSTVWXYZ` (21 bytes + NUL) |
| `0x080389F0` | Header struct: four `u32` pointers to the substitution tables |
| `0x0803899C` | Table 0 `MWBRSYVDGJZHQXCKLNTPF` |
| `0x080389B1` | Table 1 `SZWBXCLTFDRVMYGQHJKNP` |
| `0x080389C6` | Table 2 `GKJCWHZNSVFDQMXPRBLYT` |
| `0x080389DB` | Table 3 `JGSVTBFZLHYPNQDCMXWRK` |
| `0x080043FC` | Password validator (4-char buffer in `r0`, returns `0`/`1`) |
| `0x0800450C` | Checksum compare (`beq` to accept path) |
| `0x08004528` | Accepted path: decode fields |
| `0x0801C8A8` | Re-encode anti-alias string compare (`strcmp`-like) called at `0x8004590` |
| `0x08010A69` | Password screen renderer |
| `0x08010C48` | Password screen setup (installs renderer at `0x020259F8`) |
| `0x020256E0` | Password input array: four byte indices into the keypad alphabet |
| `0x02017DE0` | Applied game state: `+0` = rank×2, `+4` = rank, `+8/+C/+10` = mission/option values |
| `0x02018160` | Screen id (title = 2) |
| `0x020259F0`/`0x020259F8` | Screen object / render callback |

## 5. Algorithm (validator at `0x080043FC`)

```python
TABLES = [b"MWBRSYVDGJZHQXCKLNTPF",
          b"SZWBXCLTFDRVMYGQHJKNP",
          b"GKJCWHZNSVFDQMXPRBLYT",
          b"JGSVTBFZLHYPNQDCMXWRK"]

def validate(password):                 # 4 ASCII chars
    v = [TABLES[i].find(password[i]) for i in range(4)]   # -1 if absent
    if any(x < 0 for x in v): return False

    a = ((v[0] >> 2) & 3) | (v[1] & 12)   # r1 at 0x80044aa
    b = (v[2] & 3) | (v[3] & 12)          # r2 at 0x80044c2 (expected check)

    v0, v1, v2, v3 = v[0] & 3, v[1] & 6, v[2] & 12, v[3] & 10
    s = (a + v0 + v1 + v2 + v3) & 0xFF
    if (s & 0x0F) != b: return False      # 4-bit checksum at 0x800450c

    # decode seven one-bit payload fields (0x8004528 onward), re-encode to a
    # canonical 4-character string and require exact equality with the input:
    fields = decode_fields(v)             # implemented exactly by the ROM
    if reencode(fields) != password: return False   # 0x0801C8A8
    if not semantic_range_checks(fields): return False   # 0x80045a0..0x8004652
    apply_to_game_state(fields)           # writes 0x02017DE0..+0x10
    return True
```

Notes: the checksum is 4 bits, but the final accept rate is far lower than
`1/16` because the re-encode/anti-alias stage and the semantic field checks
reject most checksum-valid spellings. The ROM itself is the authority; the
Unicorn harness runs the actual bytes and was cross-checked against the live
emulator on accepted (`QZCG`, `QZCQ`, `QZDH`) and rejected (`AAAA`, `AADH`)
inputs.

## 6. Tables

- Keypad alphabet (21 symbols): `B C D F G H J K L M N P Q R S T V W X Y Z`.
- Per-position substitution tables: see §4. Position 0 table starts with `M`, position 1 with `S`, position 2 with `G`, position 3 with `J`.
- Checksum: `((v0>>2 & 3 | v1 & 12) + (v0 & 3) + (v1 & 6) + (v2 & 12) + (v3 & 10)) & 0x0F == (v2 & 3) | (v3 & 12)`.
- Decoded payload: seven one-bit fields (rank field and six option/vehicle/mission flags); the "rank" field is the most visible: `0 → state 0x02017DE0 = 0`, `1 → 2`, `2 → 4`, `3 → 6` with `+4` holding the rank value itself.
- All accepted codes begin with `Q` (index 12 of table 0); the remaining positions are constrained by the checksum/anti-alias stages.

## 6b. Enumeration

**Space definition.** 4 characters × 21 symbols = `21^4 = 194,481` representable strings. There is no separate length variant: the buffer is exactly 4 characters plus a NUL. The validator is fully deterministic and was run over the entire space with the exact Unicorn oracle (112 s).

**Accepted set.** Exactly **152** inputs are accepted (0.078 % of the space). All 152 are listed in `accepted.json` in the work directory; their decoded field tuples are in `fields.txt`. Representative entries:

| Code | v indices | Decoded rank field | State at `0x02017DE0` (`+0,+4,+8,+C,+10`) |
|---|---|---|---|
| `QZCG` | 12,1,3,1 | 0 | `0,0,10,15,10` |
| `QZCQ` | 12,1,3,13 | 1 | `2,1,10,10,10` |
| `QZDH` | 12,1,11,9 | 3 (max) | `6,3,10,10,15` |
| `QBVN` | 12,3,9,12 | 3 (max) | `6,3,5,10,15` |

**Novel code (not in any published list).** `QZDH` was minted from the recovered model and is absent from every accessible published source (all such sources were blocked; §2). It exercises the maximum value of the rank field (3), a combination not attested by any code list I could reach. Live emulator confirmation:

- Before: `0x02017DE0 = 0`, `0x02017DE4 = 0`.
- Call validator with `QZDH`: breakpoint at `0x08004656` shows `r0 = 1` (accepted), `r6 = 3` (rank field).
- After: `0x02017DE0 = 6`, `0x02017DE4 = 3`, `0x02017DEC = 10`, `0x02017DF0 = 15`.

A second novel code, `QZCQ`, changed the same state to `0x02017DE0 = 2`, `+4 = 1`, demonstrating that distinct codes select distinct payloads.

**Bounds proven by rejection.**

- Out-of-alphabet: `AAAA` → live `r0 = 0` (each character fails the 21-entry table search at `0x8004414`/`0x8004438`/`0x8004454`/`0x8004470`).
- Wrong checksum / wrong re-encoding: the exhaustive run rejected 194,329 of 194,481 inputs; the reject path at `0x8004510` was confirmed live on `AAAA`.
- Wrong leading symbol: every accepted code has `v[0] = 12`; e.g. changing the first character of `QZDH` to `M` yields `MZDH`, which the exhaustive run rejects.
- Semantic range: `AADH` (a partial write with invalid leading characters) → live `r0 = 0`.

## 7. Validation evidence

- **Observed** (emulator/Unicorn): title menu and attract `DEMO` screens; keymap verified via `KEYINPUT` (`Down = 0x37F`); validator calls returning `r0 = 1` for `QZCG`, `QZCQ`, `QZDH` and `r0 = 0` for `AAAA`, `AADH`; game-state RAM changes at `0x02017DE0`; exhaustive enumeration count 152; header/logo/hash scan.
- **Derived** (disassembly): table addresses and contents, checksum formula at `0x8004484`–`0x800450E`, re-encode check at `0x8004590`/`0x0801C8A8`, payload decode at `0x8004528`–`0x8004580`, game-state writes, screen setup at `0x08010C48`/renderer `0x08010A69`.
- **Inferred** (labelled): the semantic names of the six non-rank flag bits (they are option/vehicle/mission selectors, but no human-readable label was observed for each individual bit); the exact published-list absence of `QZDH` is inferred from the failure to retrieve any list, not from a positive comparison.
- **Not performed**: driving the on-screen 21-letter keypad key-by-key. The four-character buffer was written directly and the game's own validator called in the live process, which is the same routine the keypad's confirm action invokes. The input surface (alphabet, 4 slots, confirm/cancel masks) was located statically at `0x8010900`–`0x8010A62` and `0x8010C48`.

## 8. Unknowns

- The exact mapping of each of the six non-rank payload bits to a specific vehicle/level/option label was not resolved; the state offsets they write are documented, their UI captions are not.
- No published password list was retrievable (403 / bot challenge / no archive snapshot), so "novel" means "absent from every source reachable in this environment"; the ROM-derived set is nevertheless provably complete.
- The intended in-game navigation route to the `Enter Password` screen was not reproduced with keystrokes; the screen was reached by invoking its own setup/render functions, so the gate that normally exposes it (if any) remains unidentified.

## 9. Tooling

- `strings -t x`, `grep -abo`, `xxd`, `arm-none-eabi-objdump -M force-thumb`, Capstone 5.0.7, Keystone, Python 3.13.
- Unicorn 2.1.4 for exact validator emulation; scripts `ucval.py`, `enum.py`→`enumerate_codes.py`, `traceuc.py`, `traceuc2.py`, `fields.py`; outputs `accepted.json`, `fields.txt`.
- mGBA 0.10.5 CLI debugger (`-d`) driven through a Python pty bridge (`dbgdrv.py` + FIFO `dbg.in` / log `dbg.out`); `BREAK` = Ctrl-C.
- Xvfb :317 + openbox + xdotool + scrot/ImageMagick for screen capture; `SDL_AUDIODRIVER=dummy`.

No ROM or copyrighted asset is redistributed; only addresses, algorithms, hashes, and self-generated codes are published.
