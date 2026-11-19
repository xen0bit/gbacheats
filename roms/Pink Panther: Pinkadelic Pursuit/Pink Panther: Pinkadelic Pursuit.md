# Pink Panther: Pinkadelic Pursuit (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Pink Panther: Pinkadelic Pursuit.gba` |
| Size | 8,388,608 bytes (0x800000, 8 MiB) |
| Header title | `PINK PANTHER` (12 bytes at 0xA0) |
| Game code | `APEE` (0xAC) |
| Maker code | `6U` (0xB0) |
| Version | Rev.00 (0xBC = 0x00) |
| Fixed byte | 0x96 at 0xB2 (OK) |
| Complement check | 0x47 at 0xBD (non-zero → header not rebuilt) |
| Header checksum | 0x0000 at 0xBE (common in retail images) |
| Entry word | `0xEA00002E` → stock `b 0xC0`, standard crt0 (§16.1: not a cracktro patch) |
| MD5 | `ba7746952e87a2c85927fa691e7230dd` |
| SHA-1 | `208c1bcf84856f1f2425cdc32abc10d618fca71d` |
| SHA-256 | `bb34934eb344ef18b4da8f9b42bb131bf06aa909252a2e63882aea2ce73bafd2` |

**Embedded-header scan:** the 156-byte Nintendo logo (`24 ff ae 51 69 9a a2 21 …`) occurs **exactly once**, at file 0x04 (header at 0x0). No multigame pack, no appended trainer, no second crt0. Single retail image.

## 2. Executive summary

The game has a **developer-intended password ("Continue") system** reached from the main menu. It is a **4-symbol code** over a 4-icon alphabet (smiley / star / paw / ball), entered by cycling icons with **Left/Right** and committing each with **A** (on-screen hint: "ENTER CORRECT CODE USING CONTROL PAD LEFT, RIGHT AND A BUTTON"). The complete space is **4^4 = 256** codes.

Exhaustive behavioural enumeration (all 256 codes typed on the real screen) shows **every code starts the game**. There is **no rejection anywhere in the 256-code space**: the system is a permissive continue/level-skip gate rather than a whitelist. Two response classes were observed:

* **247 codes** fade directly from the password screen into gameplay (level banner "3", 5 hearts).
* **9 codes** first show a pink **"code display" transition screen** — the four entered icons across the top and Pink Panther spinning in a swirl. Any button (A or B) advances from that screen into gameplay. The 9 codes are `0103, 0133, 0323, 1221, 1312, 2031, 3211, 3230, 3323` (icon-index notation, §6).

No button-code sequence, hidden debug menu, or level-select screen was found; the menus are title → main (New Game / Password / Options) → difficulty, password, options, and the in-game pause menu (Continue / New Game / Password / Options).

Published codes could **not** be retrieved: the web search integration returned no results for every query; GameFAQs and TCRF returned HTTP 403; Wayback CDX returned empty sets; DuckDuckGo served a bot challenge; Bing via a reader proxy returned unrelated results. No published code literal was available to verify against the ROM (§3.4 / §16.7).

## 3. How to reproduce

Emulator: `mgba -3` under `Xvfb :315`, `SDL_AUDIODRIVER=dummy`, keymap A=`x`, B=`z`, Start=`Return`, L=`a`, R=`s`, D-pad=arrow keys. Hold keys ≥100 ms; menus debounce.

Menu path (boot splashes are long — wait ~9 s, then press A for the title; press B from the difficulty screen to reach the main menu):

1. Title → main menu: **New Game / Password / Options**.
2. New Game → **Easy / Normal / Difficult**.
3. Password → password screen. Cycle icons with Left/Right; press A four times to submit.
4. Options → **Music / Sound / Brightness / Contrast** (sliders/toggles).
5. In gameplay, Start → pause = main menu **+ Continue**.

Password entry used for enumeration: from a clean password screen, for each symbol `s ∈ 0..3`, press Right `(s - current) mod 4` times, then A; after the fourth A, wait ~1.5 s and screenshot. mGBA savestate slot 2 (clean password screen) is reloaded with **F2** between trials (`Shift+F2` saves).

Novel-code proof: entering **star, paw, ball, face** (`1,2,3,0`) starts gameplay (level banner "3"). Bounds: entering only two symbols leaves the screen on the password entry; cycling Right four times from any icon returns to the same icon (alphabet size = 4).

## 4. Address map

| Item | ROM file offset / address | Notes |
|---|---|---|
| Header / crt0 | 0x000–0x1FF (`0x08000000`+) | stock entry `0xEA00002E` |
| Menu UI code | file `0x1C100`–`0x1C580` (`0x0801C100`–`0x0801C580`) | Thumb; menu item tables and handlers |
| Password menu handler | `0x0801C47C` | draws "PASSWORD" label (ptr `0x08051AF4`), launches password screen |
| Options menu handler | `0x0801C43C` | draws "OPTIONS" label (ptr `0x08051AEC`) |
| Language label bank | file `0x51AC0`–`0x51B50` | `PANTHER`, `OPTIONS`, `PASSWORD`, `NEW GAME`, localized variants |
| English menu text bank | file `0x401248`–`0x4014F0` | NUL-terminated ASCII (§3.1): `Continue`, `PRESS START TO CONTINUE PLAYING`, `ENTER CORRECT CODE USING CONTROL PAD LEFT, RIGHT AND A BUTTON`, `PRESS A BUTTON TO BEGIN GAME AT DIFFICULT/NORMAL/EASY LEVEL`, `WHO CREATED THIS GAME ?`, `Languages`, `Options`, `Password`, `New Game`, `Undefined` |
| Localized banks | file `0x401CD4`–`0x4041xx` | French, Spanish, Italian, German equivalents |
| Text renderer | `0x0801C100`, `0x0801BFB8`, `0x0803E97C`/`0x0803E9EC`/`0x0803E9...` | ASCII→tile mapping (width tables at `0x0805196C`, `0x0805192C`) |
| Main object loop | `0x08041478`–`0x080415BE` | entity update loop (observed as paused PC `0x080415A4`) |

**RAM evidence** (from mGBA `.ss1` savestates; state layout: CPU/header at 0x00000, VRAM at 0x1000, IWRAM at 0x19000, EWRAM at 0x21000 — §16.13):

| RAM address | Observation |
|---|---|
| `0x0300082C` | IWRAM byte that changes with the password icon cursor (observed values 0x00/0x01/0x02 across savestates taken while moving Left/Right). Correlates with the selected icon index; exact 0- vs 1-based encoding not fully isolated. |
| `0x03000940`–`0x03000B70` | IWRAM display/tile-index buffers; bytes change (e.g. 0x08↔0x00, 0x03↔0x00) when entered symbols change from face to star — direct RAM trace of the rendered code. |
| `0x02000C6C`–`0x02000C77` | EWRAM object-state bytes that change with each committed symbol. |
| `.sav` | Created by mGBA but **0 bytes** — the game does not use SRAM; passwords are the continue mechanism. |

Savestate diffs are included as evidence files in `/tmp/opencode/pinkpanther/` (`s3.ss1`/`s4.ss1` = 2 vs 3 symbols; `s5.ss1`/`s6.ss1` = `000` vs `111`).

## 5. Algorithm (behavioural model)

No arithmetic validator was recovered from disassembly. The accepted behaviour was characterised exhaustively instead, so this model agrees with the ROM on **all 256 inputs**:

```
input: 4 icons s0..s3, each in {0,1,2,3}      # face=0, star=1, paw=2, ball=3
commit: A after each icon; game fires when 4 are committed
result: ALWAYS start gameplay (banner "3", 5 hearts)
        247 codes: direct fade to gameplay
           9 codes: pink code-display/spinner screen, then any button → gameplay
```

The 9 spinner-class codes are the only inputs distinguished by the game; the distinction is a transition overlay, not a rejection. Length < 4 is not submitted (observed with 2 symbols). The alphabet wraps modulo 4 (observed with 9 Right presses landing on the 2nd icon).

## 6. Tables

**Icon → index:** smiley face = 0, star = 1, paw print = 2, ball/eyeball = 3. Codes are written as four icon indices, e.g. `0103`.

**Acceptance classes:**

| Class | Codes | Count | On-screen result |
|---|---|---:|---|
| Direct | all codes except the 9 below | 247 | password screen → black fade → gameplay (level "3", 5 hearts) |
| Spinner | `0103, 0133, 0323, 1221, 1312, 2031, 3211, 3230, 3323` | 9 | password screen → pink screen showing the four entered icons + spinning Panther → (A or B) → gameplay |

**Screen inventory (all walked, RAM/screenshot confirmed):** boot splashes (DreamCatcher, MusyX Factor 5), title, main menu, New Game difficulty, Password entry, Options, in-game pause menu, gameplay (forest and castle variants), pink spinner/transition screen. No level-select or debug screen was reachable.

## 6b. Enumeration

* **Space definition:** alphabet size 4, length 4, no checksum/reserved bits observable → **4^4 = 256 representable codes**, all 256 tested on the real screen.
* **Space coverage:** 256/256 entered; 256/256 produced gameplay. **No rejected code exists in the space.** (An earlier automated pass reported 9 "rejects" because its pink-pixel detector could not distinguish the pink password-entry screen from the pink spinner overlay; re-testing those 9 with screenshots and a button press showed all 9 are accepted.)
* **Novel code:** `1,2,3,0` (star, paw, ball, face), entered on the Password screen, starts gameplay (banner "3", 5 hearts). No published code list was obtainable (§2), so this value is not attributable to any published list.
* **Bounds proven by constraint rather than rejection:** (a) fewer than 4 symbols is never submitted — 2 symbols left the screen on password entry indefinitely; (b) the alphabet is exactly 4 icons — Right wraps 3→0 and nine Right presses land on index 1; (c) submission fires exactly on the fourth A and no fifth symbol can be appended.

## 7. Validation evidence

* **Observed (emulator, screenshots):** every menu screen in §6; password entry icons and slot filling; all 256 code outcomes; the pink spinner screen with the entered code and its A/B continuation; level banner "3" and 5 hearts after codes; 2-symbol non-submission; 9-Right wraparound.
* **Observed (RAM / savestate):** `.sav` is 0 bytes; IWRAM `0x0300082C` and `0x03000940`–`0x03000B70` and EWRAM `0x02000C6C`–`0x02000C77` change with cursor/symbol state (§4).
* **Derived (disassembly):** stock entry/crt0; single embedded GBA header; menu handlers at `0x0801C43C`/`0x0801C47C`; ASCII text bank and its renderer; stock key tables (generation not required for the 4-icon alphabet).
* **Inferred:** exact semantics of the 9 spinner-class codes (whether they are privileged "real" passwords or simply a transition variant) — both classes end in the same gameplay state, so no behavioural difference was provable within the available time. The exact 0-/1-based encoding of `0x0300082C` is inferred, not proven.

## 8. Unknowns

* The ROM routine that validates/decodes the 4-symbol code was not isolated. Capstone/objdump scanning and a Ghidra attempt (REA) were inconclusive: the shared REA session was bound to another ROM, and Ghidra auto-analysis did not create a function at the menu handler addresses. The behavioural enumeration is therefore the validator model (complete over all 256 inputs), not a decompiled formula.
* Whether the 9 spinner-class codes encode distinct level/difficulty/progress state that is not visible in the HUD (all reached level "3" with 5 hearts).
* No published code list was accessible, so the "novel" claim rests on the absence of retrieved lists rather than a positive comparison.
* No button-code sequence or hidden debug menu was found; this is a bounded negative for the menus/strings searched (§6), not a proof that no such code exists in all possible input sequences.
* The on-screen text is partly tile-indexed; only the ASCII bank at `0x401248`+ was decoded directly. Localized banks were dumped but not exhaustively decoded symbol-by-symbol.

## 9. Tooling

* `file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings -t x`, `grep` for Phase 0/1.
* Python scripts (in `/tmp/opencode/pinkpanther/`): `scan.py` (literal/pointer scans), `ssdiff.py` (`.ss1` PNG `gbAs` zlib decode + RAM diff), `key.py` (xdotool driver with a fixed mGBA window ID), `tester.py`/`batch.py`/`enumerate_all.py` (code entry and 256-code enumeration), `gdbdrv.py`/`gdbdump.py`/`gdbpoke.py` (mGBA GDB stub experiments), REA/Ghidra (opened but session was contended).
* `arm-none-eabi-objdump -M force-thumb`, Capstone 5.0.7 (installed via pip) for static disassembly.
* mGBA 3× under Xvfb :315 + openbox; `scrot`, ImageMagick `convert`/`montage`, `tesseract` (OCR trial, unreliable on the stylised level font, superseded by visual reads).
* Installed/used packages already present: `binutils-arm-none-eabi`, `gdb-multiarch`, `xvfb`, `xdotool`, `scrot`, `imagemagick`, `tesseract-ocr`, `python3-capstone`, `python3-pil`, `pexpect`.

## Legal note

Only hashes, addresses, algorithms and original findings are published here. No ROM data or copyrighted graphics/text are redistributed.
