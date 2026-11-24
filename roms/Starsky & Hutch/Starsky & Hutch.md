# Starsky & Hutch (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Starsky & Hutch.gba` |
| Size | 4,194,304 bytes (4 MiB) |
| Header title | `STARSKYHUTCH` |
| Game code | `AYHE` (file reports `AYHE7N, Rev.00`) |
| Maker | `7N` (Empire Interactive / 2003 CPT Holdings) |
| Version | `0x00`; fixed byte `0x96`; header checksum `0x0000`; complement `0xF8` |
| Entry word | `0xEA0FEFFE` (non-stock — see below) |
| MD5 | `b072e807210c6a868296bf1c19928312` |
| SHA-1 | `14405aadc8116732f8d87637fbc25b51e070de27` |
| SHA-256 | `19645f3bedd7dda7eeb31826018d8424d53eb2615696487f23ce75f3b5f3d9e6` |

**Packaging (§16.1):** the entry word is patched. `0xEA0FEFFE` branches to
ROM `0x083FC000`, which is a two-stage BIOS decompressor:

```
0x0803FC004  ldr r0,=0x083FC02C ; ldr r1,=0x02020000 ; svc 0x13  (HuffmanUnCompWRAM)
0x0803FC010  ldr r0,=0x02020000 ; mov r1,#0x02000000 ; svc 0x11  (LZ77UnCompWRAM)
0x0803FC01C  mov r0,#0x02000000 ; mov pc,r0            ; jump to unpacked payload
```

followed by ~1 MiB of high-entropy packed data. This is a scene-release
cracktro/intro wrapper, **not** an in-game cheat; it was not analysed further.
Per §16.1, the stock entry branch `0xEA00002E` was restored **on a copy**
(`/tmp/starsky/starsky_stock.gba`, MD5 `b2d2f51b0863201f88d195e2ca8f0cd5`)
for all dynamic work. All game strings/tables/addresses below are from the
unmodified image and apply equally to the original.

## 2. Executive summary

The GBA version has a real, developer-intended **passcode system** at
**Options → Enter Passcodes**. It is a **fixed table of exactly seven
5-character codes** — not a checksum/generator. The validator at
`0x080038C0` walks a 7-entry pointer table at `0x0816CD24`, byte-compares the
entered characters against each NUL-terminated string, and on a match sets a
bit in an unlock flag array at `0x0203E0F0`.

The seven codes are:

| # | Code | Flag byte set |
|---:|---|---|
| 0 | `L5NVW` | `0x0203E0F0` |
| 1 | `HKLPQ` | `0x0203E0F1` |
| 2 | `GBBDC` | `0x0203E0F2` |
| 3 | `MKLJK` | `0x0203E0F3` |
| 4 | `JGFDT` | `0x0203E0F4` |
| 5 | `SDLMK` | `0x0203E0F5` — observed to unlock **all six Game Modes** |
| 6 | `MBVNM` | `0x0203E0F6` |

**None of these seven strings appears in any published source** (web search
for all seven literals returned no Starsky & Hutch results; GameFAQs' GBA
FAQ explicitly says *"Enter Passcode … none I've found worked"*, and TCRF's
talk page says the same). The widely published `VADKRAM` "profile name"
cheat is a **different platform's** feature: the literal `VADKRAM` is absent
from this GBA image.

Three codes were submitted on the real in-game screen and RAM-verified
(flag byte transitions `0→1`). Rejection bounds and a prefix-match quirk were
proven with five further inputs.

## 3. How to reproduce

### Environment
- `Xvfb :316 -screen 0 1024x768x24 -nolisten tcp`, `openbox`,
  `SDL_AUDIODRIVER=dummy`.
- `mgba -3 <rom>` (mGBA 0.10.5). Keymap used: **A = `x`**, **B = `z`**,
  D-pad = arrow keys. `Return` (Start) did not activate menus in this build;
  A did.
- Boot takes ~10 s (Empire logo → legal screen → title). Press A at
  `PRESS START`.

### Menu path
`Main Menu` → `Options` → `Enter Passcodes`. The screen has a 43-symbol
character strip plus `OK` and `Clear` buttons, and echoes the current input
in a card (it starts pre-filled with `PL 1`, len 4).

### Static reproduction
```bash
# alphabet / tables
python3 -c "d=open('Starsky & Hutch.gba','rb').read(); print(d[0x16DF50:0x16DF80])"
# validator table
python3 - <<'PY'
import struct
d=open('Starsky & Hutch.gba','rb').read()
for i in range(7):
    p=struct.unpack_from('<I',d,0x16CD24+4*i)[0]-0x08000000
    print(i, d[p:d.find(b'\0',p)])
PY
```

### Dynamic reproduction of an accepted code
The keypad's on-screen cursor could not be driven reliably by XTEST in this
headless harness (arrow/A/B presses left `cursor`/`len` unchanged), so codes
were placed in the keyboard buffer through an mGBA savestate (§16.13) and
**submitted with the real on-screen `OK` button (A)**:

1. Save a state on the Enter Passcodes screen (`Shift+F1`).
2. Decode the PNG's `gbAs` zlib chunk; patch
   `len` (u16) at state `0x21000+0x2F1CC` and nine u32 chars at
   `0x21000+0x2F1D0`; recompress and re-embed.
3. Start `mgba -3 -t patched.ss1 <rom>`; press `x` (OK).
4. Save again and read the seven flag bytes at state `0x21000+0x3E0F0`.

Observed: `L5NVW→[1,0,0,0,0,0,0,0]`, `HKLPQ→[0,1,0,0,0,0,0,0]`,
`SDLMK→[0,0,0,0,0,1,0,0]`; the Game Modes screen then showed all six
modes with no padlocks for `SDLMK`.

## 4. Address map

| Item | ROM / RAM address | Notes |
|---|---|---|
| Patched entry loader | `0x0803FC000`–`0x0803FC020` | Huffman→LZ77→EWRAM |
| Stock entry branch (on copy) | `0x08000000` = `0xEA00002E` | → crt0 `0x080000C0` |
| Keyboard alphabet | `0x0816DF50` (file `0x16DF50`) | `ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.,'!?@ ` + NUL, 43 symbols |
| Keyboard input handler | `0x0800356C` (ARM) | reads keys at `0x0202DD6A/6C`; cursor clamp `0x2A` (42); max len 9 |
| Passcode validator | `0x080038C0` (ARM) | called when OK is pressed |
| Code pointer table | `0x0816CD24` (file `0x16CD24`) | 7 pointers, NULL-terminated |
| Code strings | `0x080EEF08`, `0x080EEF10`, `0x080EEF18`, `0x080EEF20`, `0x080EEF28`, `0x080EEF30`, `0x080EEF38` | 5 chars + NUL + 2 pad bytes each, 8-byte stride |
| Keyboard buffer | `0x0202F1C8` (EWRAM) | `{u16 state; i16 cursor; u16 len; u32 chars[9]}` |
| Unlock flags | `0x0203E0F0` (EWRAM) | 7 bytes, index = code index |
| Input/state base | `0x0202DD10` | key flags at `+0x6A` (press) / `+0x6C` (held), active-low GBA masks |
| UI strings | `0x081E3Fxx`–`0x081E4Axx` | `OK`, `Clear`, `Enter Passcodes`, six `You have unlocked …` pairs |
| Control names | `0x080EEF40`–`0x080EEF68` | `ACCELERATE`, `BRAKE`, `REAR VIEW`, `SHOOT` (adjacent, unrelated) |

### Validator (annotated, `0x080038C0`)
```
r2 = 0x0816CD24            ; pointer table
r8 = 0x0202F1C8            ; keyboard buffer
r6 = 0x103E4               ; -> 0x0202DD10 + 0x103E4 = 0x0203E0F4
for idx in 0..:
    codeptr = table[idx]
    if codeptr == 0: break
    ip = 1                                  ; assume match
    bp = &buf.chars[0]
    while *codeptr != 0:
        if *codeptr++ != *(u32*)bp++: ip = 0
    if !ip: continue
    flags[idx] = 1                          ; strb 1,[0x0203E0F0 + idx]
    sound(26)
    if flags[6]:                            ; 0x0203E0F6
        flags[6] = 0; free/realloc UI object; sound(0xFF)
return
```

## 5. Algorithm

There is **no checksum and no generator**. Acceptance is a plain prefix
comparison against a fixed table:

```
accept(input):
    for i, code in enumerate(TABLE):
        if all(input.chars[j] == ord(code[j]) for j in range(len(code))):
            UNLOCK[i] = 1
            return i
    return none
```

Consequences (all verified in emulator):
- Inputs shorter than a table string are rejected (the missing u32 slots are
  zero).
- Wrong characters are rejected.
- **Extra trailing characters are ignored**: `L5NVWXYZ` was accepted as
  `L5NVW`, because the loop stops at the *table string's* NUL, not the
  input's length. The keypad caps input at 9 characters.

## 6. Tables

### 6.0 Input alphabet (`0x0816DF50`)
43 symbols, indices 0–42:
`A B C D E F G H I J K L M N O P Q R S T U V W X Y Z 0 1 2 3 4 5 6 7 8 9 . , ' ! ? @ <space>`

### 6.1 Accepted passcodes (complete)
| Index | String | Effect |
|---:|---|---|
| 0 | `L5NVW` | sets flag 0 |
| 1 | `HKLPQ` | sets flag 1 |
| 2 | `GBBDC` | sets flag 2 |
| 3 | `MKLJK` | sets flag 3 |
| 4 | `JGFDT` | sets flag 4 |
| 5 | `SDLMK` | sets flag 5 — **all Game Modes unlocked (observed)** |
| 6 | `MBVNM` | sets flag 6 (also cleared by the accept path) |

### 6.2 Unlock flags
`0x0203E0F0 + index`, one byte per code, set to `1` on acceptance and never
cleared by the entry screen. Flag 5's effect on the Game Modes padlocks was
observed directly; the exact consumers of flags 0–4 and 6 were not isolated
(see §8).

## 6b. Enumeration

**Space definition.** The accepted language is the union of exactly seven
5-character strings drawn from a 43-symbol alphabet. There is no checksum, no
key, no field packing and no algorithmic encoder. Representable raw input
space of the keypad is 43^1 … 43^9 (length ≤ 9); the accepted subset is
**exactly 7 strings**, plus their longer extensions under the prefix-match
quirk (each accepted 5-char code has 43^4 + 43^3 + 43^2 + 43 + 1 accepted
extensions up to length 9 = 3,468,801 spellings per code).

**Closed-set proof.** The table at `0x0816CD24` is NULL-terminated after seven
entries; the validator loop terminates on that NULL and compares against no
other data (no hash, no secondary table, no generator call in
`0x080038C0`). This is an exhaustive enumeration of the table, not a
best-effort list.

**Novel codes (absent from every published list).** All seven were recovered
from the ROM and none is published: web searches for `L5NVW`, `HKLPQ`,
`GBBDC`, `MKLJK`, `JGFDT`, `SDLMK`, `MBVNM` produced no Starsky & Hutch
results, and both GameFAQs and TCRF state that no working GBA passcodes were
known. Three were submitted on the real in-game screen with RAM proof:

| Code | In-game submission | RAM result | Evidence |
|---|---|---|---|
| `L5NVW` | OK pressed on Enter Passcodes | `[1,0,0,0,0,0,0,0]` | observed |
| `HKLPQ` | OK pressed on Enter Passcodes | `[0,1,0,0,0,0,0,0]` | observed |
| `SDLMK` | OK pressed on Enter Passcodes | `[0,0,0,0,0,1,0,0]` + all 6 Game Modes unlocked (padlocks gone) | observed |

**Bounds proven by rejection.** Each input below was patched into the buffer,
submitted with OK on the real screen, and the flag array read back:

| Input | Result | Interpretation |
|---|---|---|
| `L5NVX` (one wrong char) | all flags `0` | exact byte comparison |
| `ZZZZZ` (in-alphabet but unlisted) | all flags `0` | closed set, not a checksum |
| `L5NV` (truncated) | all flags `0` | short input cannot match |
| `""` (empty) | all flags `0` | no accidental match |
| `L5NVWXYZ` (valid prefix + junk) | flag 0 = `1` | prefix-match quirk; length not validated |

**Other cheat surfaces checked.** No published GBA button codes were found
(the widely listed `R,Z,L,Z`, `Y,B,A,X…` sequences use GameCube buttons and
belong to the GC version). No debug-menu strings (`debug`, `level select`,
etc.) occur in the image; the only `unlock` strings are the six season-reward
messages at `0x081E48F6`–`0x081E4A37`. `VADKRAM` is absent from the ROM. The
packer at `0x0803FC000` is a scene cracktro, reported separately from
developer-intended cheats.

## 7. Validation evidence

- **Observed (emulator):** every screen transition from title → Main Menu →
  Options → Enter Passcodes → Game Modes; codes displayed on the passcode
  card; flag bytes `0→1` after pressing OK; all Game Modes unlocked after
  `SDLMK`; the five rejection/acceptance results in §6b.
- **Derived (disassembly):** alphabet at `0x0816DF50`; keyboard struct layout
  at `0x0202F1C8`; 8-byte-stride code table at `0x080EEF08`; validator control
  flow at `0x080038C0`; NULL-terminated pointer table at `0x0816CD24`; flag
  array at `0x0203E0F0`; prefix-match behaviour (loop ends on the *code*
  string's NUL).
- **Inferred:** flag indices 0–4 and 6 likely gate other bonus content (TV
  Specials / Locker / Free Roam, hinted at by the GameCube `VADKRAM`
  description), but this was not proven on a GBA screen.

## 8. Unknowns

- Exact consumer(s) of flag bytes 0–4 and 6. Flag 5's Game Modes effect was
  observed; the other flags produced no visible change on the Game Modes
  screen. They may gate content reached only after season completion.
- Direct character entry through the on-screen strip could not be driven in
  the headless harness; input was injected via savestate and submitted with
  the real OK button. The validator itself was exercised on the real screen.
- The cracktro payload at `0x0803FC02C` was not unpacked; it is a packaging
  artifact, not an in-game cheat.
- Whether the six "SEASON COMPLETE / You have unlocked …" messages are
  driven by the same flag bytes or by a separate save-progress structure.

## 9. Tooling

- `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 … -M force-arm`
  (this engine's early code is **ARM**, not Thumb — a Thumb disassembly of
  `0x08003400`–`0x08003A00` is garbage).
- Python + `struct` for pointer/literal scans; `zlib` for mGBA `gbAs`
  savestate patching (`ssdecode.py`, `testcode.py`, `kprobe.py`,
  `mapcodes.py`, `key.py` in `/tmp/starsky/`).
- mGBA 0.10.5 under Xvfb `:316` + openbox; `xdotool`, `scrot`, ImageMagick
  `convert`/`montage` for screen evidence.
- Web recon: GameFAQs GBA FAQ/cheats, GamesRadar, Tips & Tricks #111
  (2004-05), TCRF talk page (HTTP 403; recovered via search snippets).

**Legal note:** no ROM or copyrighted asset is redistributed here; only
addresses, hashes, algorithms and the seven recovered code strings
(which are short developer literals) are published.
