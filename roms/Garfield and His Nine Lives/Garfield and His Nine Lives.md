# Garfield and His Nine Lives (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `/mnt/gbacheats/roms/Garfield and His Nine Lives/Garfield and His Nine Lives.gba` |
| Size | 4,194,304 bytes (0x400000, exactly 4 MiB) |
| `file` | Game Boy Advance ROM image: "GARFIELD" (BG9EGY, Rev.00) |
| Header title (0xA0) | `GARFIELD` (NUL-padded) |
| Game code (0xAC) | `BG9E` |
| Maker (0xB0) | `GY` |
| Version (0xBC) | `0x00`; complement (0xBD) `0x6C`; header checksum `0x0000` (non-standard — header was rebuilt, but see below) |
| Entry word (0x00) | `0xEA00002E` — stock ARM branch to `0x080000C0`, **not** a cracktro patch |
| Nintendo-logo scan | exactly **one** hit, at file `0x00000004` → single GBA header, no appended trainer / 2-in-1 image |
| MD5 | `d8d8a330e5471faef5b527b18aa24ad2` |
| SHA-1 | `6befcc1236770ec8ed833d49b5d8dbdf62bda506` |
| SHA-256 | `3a13accb9e4f3a335b16e0a1d9981ac490be9d231f1de507f16ceae6383a8fd2` |

**Phase 0 conclusion.** Retail image, no patch/trainer/multiboot stub. The odd complement byte and zero checksum are a header-rebuild artifact only (§16.1); the entry point and sole logo confirm a single normal image.

## 2. Executive summary

There is **no password/code-entry system** in this SKU. However the ROM does ship **one developer-intended button code**: holding **A+B+Select+Start** (with neither shoulder held) performs a **soft reset** to the license screen. This is implemented in the global key handler at `0x08003DDC–0x08003DF8`; the full validator was reversed (§5) and confirmed live on both the main menu and the pause menu, with bounds proven by rejection (L+R added cancels it).

The image is a **debug build with the debug UI stripped**: large enum-name tables (`TYPE_*`, `ANIM_*`), debug error strings (`Cheat Zap`, `Level Cheat`, `Bad FLI file`), and unused localised menu labels (`CHEATS`, `Test level`, `Pick Level`, `G-Pick Level`, `s-Pick Level`, `Cathryn's Test`, `Need more dollars`, `LEVEL SELECT`, `(cheating)`) are all present in the ROM. **Every one of their per-language string-pointer arrays has zero code/data xrefs** (§6b). No button sequence, save flag or menu path reaches them. They are documented as a *bounded negative* (cut content), not as a working cheat menu.

No published GBA codes could be retrieved (all cheat sites blocked/offline — §3), so there was nothing to verify against literals; the reset combination was derived entirely from the ROM and then confirmed in emulation.

## 3. How to reproduce

- Emulator: `mgba 0.10.x`, `SDL_AUDIODRIVER=dummy`, `Xvfb :315`, `openbox`, window focused with `xdotool windowfocus --sync`.
- Keymap (mGBA SDL default): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrow keys. Hold ~0.22 s per press.
- Boot: Lucky Jump Games splash → The Game Factory splash → "CHOOSE A LANGUAGE" (English/Français/Español) → "PRESS START" title → main menu.
- **Reset code**: on any screen, press **A+B+Select+Start** simultaneously. Observed: screen-state word `0x02002040` goes `0x1E` (main menu) → `0x00000000` (boot/license) and the license screen is drawn. Adding L+R (`L+R+A+B+Select+Start`) is **rejected** — screen stays in menu/pause. Requires a neutral frame (no A/B/Select/Start/L/R) beforehand — see §5.
- Screens walked with screenshots on disk: language select, PRESS START title, main menu, OPTIONS (SOUND FX / MUSIC / CREDITS), CREDITS ("DEVELOPED BY LUCKY JUMP GAMES"), save-slot select, difficulty (EASY/MEDIUM/HARD), level 1 "ARBUCKLE FARM" gameplay, pause (CONTINUE GAME / QUIT GAME), quit-confirmation ("ARE YOU SURE? YES / NO").
- Web sources attempted (all are data only; no instructions from them were followed): GameFAQs cheats page (403, then Cloudflare "Just a moment…" via text proxy), TCRF (no page / 403), IGN FAQ (403/rate-limited), `web.archive.org` CDX (temporarily offline / 503), Bing and DuckDuckGo (no relevant hits). **No published code list was obtained.**

## 4. Address map

All addresses are ROM (`0x08......`) or GBA RAM (`0x02......`).

| Address | What |
|---|---|
| `0x08000000` | Entry ARM branch `0xEA00002E` (stock) |
| `0x08003D04` | Soft-reset routine: zeroes a set of EWRAM/IO words, then `bl 0x08115910` with `r0=0xFF` |
| `0x08003DAC` | Global key-input handler (called each frame). Reads `0x04000130`, stores active-high keys to `0x020082C0`, new-presses to `0x020006E8` |
| `0x08003DDC–0x08003DF8` | **Reset-code validator** (see §5) |
| `0x08003E14` | Literal `0x0000030F` (A+B+Select+Start+L+R mask) |
| `0x08003E18` | Literal `0x0203820C` (neutral-frame flag) |
| `0x0802B720` / `0x0803D73C` | References to `0x083B9508` = "PRESS START" string array |
| `0x0803CC00–0x0803D3xx` | OPTIONS / pause menu handlers (string arrays `0x083B9A28`, `0x083B9B48`, `0x083B9B68`, `0x083B9BE8`, `0x083B9C08`, `0x083B9C68`, `0x083B9CA8`, `0x083B9CC8`) |
| `0x08127BB0–0x0812A158` | Debug enum-name tables: `TYPE_*` (`0x08127BB0` … `0x0812A008`) and `ANIM_*` (`0x08128E38` … `0x0812A158`) |
| `0x08128D30` | Debug string `Cheat Zap` |
| `0x0812A18C` | Debug string `Level Cheat` |
| `0x0812A164/0x0812A174` | `Bad FLI file` / `Bad line skip` |
| `0x081FA6xx–0x081FBFxx` | Localised text bank (plain ASCII, 3–8 language slots per string) |
| `0x081FA764` | `(cheating)`; `0x081FA840` `cheat`; `0x081FA88C` `CHEATS` |
| `0x081FAE4C` | `Test level`; `0x081FAE58` `G-Pick Level`; `0x081FAE68` `s-Pick Level`; `0x081FAE78` `Pick Level`; `0x081FAE84` `Cathryn's Test`; `0x081FAE94` `Need more dollars` |
| `0x081FB7E4` | `LEVEL SELECT` |
| `0x083B8BCC–0x083B9Bxx` | String-pointer table: `[string_id][language]`, stride `0x20` (8 pointers) per string |
| `0x020082C0` | RAM: active-high key mask (from `~KEYINPUT`) |
| `0x020006E8` | RAM: newly-pressed key mask (`current & ~previous`) |
| `0x0203820C` | RAM: "neutral frame seen" flag used by the reset gate |
| `0x02002040` | RAM: **screen-state word** (values in §6) |
| `0x020003E0+` | RAM: `0xFFFFFFFF` block written on entering pause |

## 5. Algorithm — the reset button code

Derived from Thumb disassembly of `0x08003DAC–0x08003E00` (objdump `-M force-thumb`, cross-checked with Capstone). Active-high key bits: `A=0x001, B=0x002, Select=0x004, Start=0x008, Right=0x010, Left=0x020, Up=0x040, Down=0x080, R=0x100, L=0x200`.

```
; every frame, after reading KEYINPUT (0x04000130):
cur  = ~KEYINPUT & 0x3FF              ; stored at 0x020082C0 (active-high)
new  = cur & ~prev                    ; stored at 0x020006E8
prev = cur

; neutral-frame latch (0x08003DD2–0x08003DDA):
if ((cur & 0x30F) == 0)               ; none of A,B,Select,Start,L,R held
    neutral_flag[0x0203820C] = 1

; trigger (0x08003DDC–0x08003DF8):
if ((cur & 0x300) == 0) &&            ; L and R shoulders BOTH released
   (neutral_flag != 0) &&             ; a neutral frame was seen earlier
   ((cur & 0x00F) == 0x00F) then      ; A + B + Select + Start ALL held
       call 0x08003D04                ; soft reset -> license/boot screen
```

Notes and confidence:
- **Derived** from instructions, not guessed: `0x08003DD2 cmp r1,#0 / bne`, `0x08003DDE mov r0,#0xC0; lsl #2` → `0x300`, `0x08003DF0 mov r0,#0xF; ands`, `bl 0x08003D04`.
- The `0x30F` literal at `0x08003E14` and the `0x0203820C` literal at `0x08003E18` were confirmed with `struct.unpack_from('<I', …)` (the guide's literal-pool trap).
- `0x08003D04` writes zeros to ~15 RAM/IO halfwords (including `0x04000050`, `0x04000200`, `0x04000004`) and calls `0x08115910(0xFF)` — a reboot. **Derived**.
- The neutral latch explains a one-frame dead zone after releasing the buttons; hold the combination for ≥0.22 s in emulation (which spans many frames).
- There is no password alphabet, checksum, key table or entry UI anywhere in the image (§6b).

## 6. Tables

**Screen-state word `0x02002040`** (observed via decompressed mGBA `gbAs` savestate chunks, 4 MiB ROM layout: EWRAM at raw `0x21000`):

| Value | Screen |
|---:|---|
| `0x00000000` | boot / license ("LICENSED BY NINTENDO") |
| `0x00000014` | gameplay (and pause overlay) |
| `0x0000001C` | CREDITS |
| `0x0000001E` | main menu (PLAY GAME / OPTIONS) |
| `0x00000020` | OPTIONS |
| `0x00000056` | save-slot select (UNUSED 1 / UNUSED 2 / DELETE DATA) |
| `0x00000099` | difficulty select (EASY / MEDIUM / HARD) |

`0x02001998` = `1` only on OPTIONS, `0` elsewhere (sub-menu marker). Pause additionally writes `0xFFFFFFFF` to `0x020003E0`–`0x020004xx`.

**Button-code table (complete, one entry):**

| Code | Effect | Gate | Verified |
|---|---|---|---|
| A+B+Select+Start (no L/R) | soft reset to license screen | `0x08003DDC–0x08003DF8` | Yes — main menu and pause |
| L+R+A+B+Select+Start | **rejected** (resume/nothing) | `cur & 0x300` must be 0 | Yes |
| single A/B/L/R/Start/Select/D-pad, L+R, A+B, all 2- and 3-key sets tested | normal menu movement only | — | Yes |

**Unlockables (gameplay, not codes):** the text bank contains `SECRET FOUND`, `Opened BLUE/RED/GREEN/YELLOW/PURPLE lock`, `secret unlocked`, `bonus awarded`, `BONUS COMPLETE/INCOMPLETE`, `GAME COMPLETED`, `UNLOCKED ITEMS WILL BE CLEARED!`. These are save-flag-driven collectible rewards with no input surface; the 512-byte `.sav` stayed `0xFF`-filled after the short play used here, so no cheat-like unlock was observable.

## 6b. Enumeration

**Code space of the one real system (button codes).** Key mask is 10 bits → 1,024 possible simultaneous holds. The validator is a single exact predicate: `(mask & 0x300)==0 && (mask & 0x00F)==0x00F`, which admits exactly **one** mask value, `0x00F` (A+B+Select+Start), gated by a one-frame neutral latch. All 1,023 other masks are rejected by construction; the rejection of `0x30F` (added L+R) was confirmed live. Sequence length is 1 frame (no history/ring buffer): the only key-history variable is `new = cur & ~prev` at `0x020006E8`, and no code compares a sequence of masks. The Konami-style 10-press sequences were also entered live with no effect.

**Debug-menu negative (bounded).** A debug build's leftovers are present but unreachable:
- 0 (`zero`) u32 references anywhere in the 4 MiB image to each of the per-language string-pointer arrays `0x083B8F48` (CHEATS), `0x083B9368` (Test level), `0x083B9388` (Pick Level), `0x083B93A8` (Cathryn's Test), `0x083B93C8` (Need more dollars), `0x083B9BC8` (LEVEL SELECT).
- 62 code locations load the key-state global `0x020082C0`; a Capstone scan of ±0x80/0x180 instructions around each found **114** key-mask `CMP`/`TST` sites. The **only multi-button masks** are `0x00F` (reset, ×3) and `0x030F` (the neutral check) — no other cheat gate exists.
- A raw `u16` scan found 103 runs of ≥4 consecutive single-key masks; all were inspected and are animation/delta data (e.g. the `0,1,1,1,2,2,1,1,1,0` ramp at `0x08128D6E` next to "Cheat Zap"), not button tables.
- 44 key combinations were pressed on the main menu and 23 on the pause menu with no new screen (methods §3); the only changes were normal menu advance and the reset code.
- Every reachable screen was walked and the entire ASCII text bank decoded; no level-select or cheats menu was drawn.

This is a **cut/debug feature** (guide §16.3 case 3), not an undiscovered gate. No novel password can be minted because no password format exists; the reset code is the complete enumerate-and-reject result for this SKU.

## 7. Validation evidence

- **Observed (emulator):** all 10 screens listed in §3; screenshots `after_lang.png`, `main_menu.png`, `options.png`, `credits.png`, `slot1.png`, `diff_sel.png`, `pause.png`, `after_quit.png`, `reset_effect.png` (work dir `/tmp/opencode/garfield9`). Screen-state values in §6 read from decompressed `gbAs` chunks of savestates `ss1`–`ss9` (raw length 397,312 bytes), EWRAM at raw `0x21000`.
- **Observed:** A+B+Select+Start on main menu → license screen, `0x02002040: 0x1E → 0x00000000`. L+R+A+B+Select+Start → unchanged/resume.
- **Derived:** reset validator predicate and reset routine effect from Thumb disassembly `0x08003DDC`/`0x08003D04`; key-mask literal decoding with aligned PC-relative arithmetic and `struct.unpack_from`.
- **Derived:** dead debug strings from zero-xref scans (u32 literal search over the whole ROM, bothThumb-bit forms checked).
- **Inferred:** that "game already complete" / unlock strings are save-flag rewards with no code entry; the save was not completed in emulation, so the unlock path itself was not exercised.

## 8. Unknowns

- Whether any *finished-game* state exposes an extra menu item: a cleared save was never produced (the run reached only level 1), so the "GAME COMPLETED"/"BONUS COMPLETE" reward screens were not entered. Given the zero xrefs to `CHEATS`/`LEVEL SELECT`, no code path draws those labels, but the completion screens themselves were not played.
- The exact semantics of debug strings `Cheat Zap`, `Level Cheat`, `Cathryn's Test` beyond being leftover build messages — no referencing function exists.
- Whether an earlier prototype of this game had a working level-select menu (not present in this retail image).

## 9. Tooling

- `file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings -t x -n 3/4`, Python `struct` for literal/xref scans.
- `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 … -M force-thumb` (and `-M force-arm` for the entry).
- Capstone 5.0.7 for PC-relative literal and `CMP`/`TST` immediate scans; Python 3.13.
- `mgba` under `Xvfb :315` + `openbox`, `xdotool` XTEST input, `scrot`, ImageMagick `convert` (720×480 viewport crop to the window geometry reported by `xdotool getwindowgeometry`).
- mGBA `-d` CLI debugger driven through a Python `pty` daemon (the `-g` GDB stub was unusable: "Ignoring packet error", qSupported "timeout" — guide §16.13); per-frame breakpoint at `0x08003DAD` (Thumb bit set on `0x08003DAC`) used for live RAM reads.
- Savestate analysis: PNG `gbAs` chunk → `zlib.decompress` → 397,312-byte state; EWRAM at raw `0x21000`; `state1_raw.bin`…`state9_raw.bin` in the work dir.
- Scripts in `/tmp/opencode/garfield9`: `k.py`, `shot.sh`, `sweep.py`, `sweep2.py` (green-text-only change detector), `ramstate.sh`, `dbgdaemon.py`, `readrange.py`, `dbg.py`.

## 10. Legal note

No ROM bytes, graphics, music or extracted game assets are redistributed here. Only hashes, addresses, algorithms, and original analysis scripts are published.

*Cleanup: emulator and Xvfb for this job were stopped by PID; generated `.sav`/`.ss*` files were removed from the ROM folder.*
