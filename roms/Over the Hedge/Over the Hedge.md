# Over the Hedge (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Over the Hedge/Over the Hedge.gba` |
| Size | 8,388,608 bytes (0x00800000) |
| Header title | `OVER THE HED` |
| Game code | `BH5E` (file reports `BH5E52`; make byte `52`) |
| Maker | `52` (Atari/Activision-published licensed title) |
| Version | 0x00 (Rev.00) |
| Entry word | `0xEA00002E` → stock `b 0x080000C0` crt0 (not a patch/cracktro) |
| Header checksum | `0x0000` (rebuilt-header artifact, §16.1); complement `0xB8` (non-zero, non-canonical) |
| MD5 | `123978146274e2c7711209aba22ee244` |
| SHA-1 | `be86490d8161fd934a122020300ce6898ef81d45` |
| SHA-256 | `66056b4cdd8dd49c188362e3482c6d2ec650f9a6fdf529df06772fb31349ac9f` |

Phase 0 checks: single Nintendo-logo hit at file offset 0x0 (`0x08000000`) — **no second/sub-image header, no appended trainer, no patched entry**. The engine is a proprietary/scripted engine (leftover build paths `C:\p4\OTHGBA\Engineering\levels\objects.bol`, `<SOBJECT ...>` XML, `.flc` object icons) plus a libjpeg/Shin'en-audio code base. The string `Code: B.Wodok` at `0x7F6339` is the known Shin'en GAX audio-engine banner — a false positive for "code" (§11).

## 2. Executive summary

**No developer-intended cheat system exists in this ROM.** There is no password screen, no password alphabet/table, no key-mask (button-code) sequence table, no cheat/debug menu, and no hidden level-select. The only "unlockable" content is ordinary progression (a shop and chapter logs reached by normal play), which is a save-bit/progression feature, not a cheat code (§16.18).

The game boots to a legal screen; any button advances to an animated attract/title scene (a scrolling hedgerow in which the `OVER THE HEDGE` logo and a portal marker appear, with a running RJ). The attract scene accepts D-pad camera motion but no documented or discovered button code changes state. To reach the remaining real screens for enumeration I forced stage loads on **copies** of the ROM (see §3) — these produced the save-slot/hub screen and level 1 with a dialogue box. No menu on any of those screens exposes cheats.

Published-code research was attempted against 3rd party cheat indexes, the Wayback Machine, Google, DuckDuckGo and a Jina proxy; all were blocked (403 / 404 / CAPTCHA / no results). Consequently no published GBA password literal could be obtained or tested against the ROM. The negative result below therefore rests on (a) exhaustive in-ROM literal/encoding searches, (b) full input-space and button-mask searches, and (c) direct screen enumeration.

## 3. How to reproduce

Emulator: mGBA 0.10.5 (also cross-checked in VisualBoyAdvance — identical behaviour), `Xvfb :317`, `SDL_AUDIODRIVER=dummy`, `-3` scale. mGBA SDL keymap verified against `0x04000130`: A=`x`, B=`z`, Start=`Return`, Select=`BackSpace`, L=`a`, R=`s`, D-pad=arrows.

1. Boot the stock ROM. Legal screen appears and **waits indefinitely for a button** (verified: still present at t=12 s with no input); any face button dismisses it.
2. The attract/title scene follows. D-pad moves the view; after enough rightward presses the `OVER THE HEDGE` logo and a glowing-ring/down-arrow marker are visible. No sequence of A/B/Start/Select/L/R (single, held, or repeated; all 2- and 3-button combinations tested) changes screens. A 120-second no-input monitor produced no text or transition (screens `monitor/c_1.png` … `c_120.png`, no OCR output).
3. To reach the other real screens, stage records in a **copy** were repointed (the original ROM was never modified):
   - `patched.gba`: stage record 0 name/data → `0x080671C0` / `0x08068C84` ("slot select") → boots into the hub/save-slot screen with tree-stump logs.
   - `patched3.gba`: stage record 0 → `0x080672BC` / `0x08068CD8` ("C1L1_forest") → boots into level 1 with the opening dialogue box.
   These are labelled **debug interventions** (§16.10); they are not player input paths.
4. Savestates (`Shift+F1/F2`) were diffed via the `gbAs` PNG chunk (§16.13) for RAM evidence.

Codes tested: none available (no published code obtained; no password UI exists to accept one).

## 4. Address map

| Address (ROM / RAM) | Meaning | Evidence |
|---|---|---|
| `0x08000000` / file `0x0` | Header, standard ARM crt0 entry `b 0x080000C0`; Thumb `main` reached via `bx r3` at `0x0800138` | Derived (objdump) |
| `0x08002228` | Key reader: `ldrh r1,[0x04000130]; mov r2,#0x3ff; eor r0,r2,r1` → active-high mask | Derived (objdump) + Observed (GDB breakpoint hit; `lr=0x080021B7`) |
| `0x08021A4` | Input manager; masks `0x30` (Left+Right) and `0xC0` (Up+Down) invalid diagonals, stores held/pressed words in a state struct | Derived |
| `0x080063C4` | Boot init / wait loop calling input manager at `0x08006496`, `0x080064B6` | Derived |
| `0x080671DC` | **Stage table** — 4 records × `0x38`: `{name_ptr, data_ptr, …}` = `logos`, `slot select`, `main`, `shop` | Derived (dump + ROM-patch experiment) |
| `0x0806734C` | **Level table** — 12 records × `0x38`: `C1L1_forest`, `C2L1_forest`, `C4L1_forest`, `C6L1_forest`, `D_forest01`..`D_forest08` | Derived |
| `0x080C2290/94/98/9C` | Per-stage UI-hint pointer arrays (12 `char*` each) into hint strings at `0x080C2FB4`… | Derived |
| `0x0C0000`–`0x0C8000` | Dialogue text bank: ASCII, `0x0C` newline, NUL-terminated, followed by self-pointer (e.g. `0x080C4F88`, `0x080C501C`) | Derived |
| `0x02000004` | EWRAM counter: `0xDA` (legal) → `0x102` (title/demo) | Observed (savestate diff) |
| `0x02000008`, `0x0200000C` | EWRAM flags: `1,0` (legal) → `0,1` (title/demo) | Observed (savestate diff) |
| `0x02000014` | Queue counter (0…127), *not* a stage selector (functions `0x08006676`…`0x08006744`) | Derived |
| `0x04000130` | KEYINPUT (active-low, 10 bits) | Observed (GDB) |

Savestate layout (§16.13): 397,312-byte `gbAs` chunk; CPU/header at `0x0`, VRAM at `0x1000`, IWRAM at `0x19000`, EWRAM at `0x21000`.

## 5. Algorithm

No password/checksum algorithm exists to reimplement. The relevant reverse-engineered logic is the input path:

```
mask = (~KEYINPUT) & 0x3FF          @ 0x08002228   ; active-high buttons
if ((mask & 0x30) == 0x30) mask &= ~0x30           ; reject Left+Right
if ((mask & 0xC0) == 0xC0) mask &= ~0xC0           ; reject Up+Down
held   ^= ... ; pressed = mask & ~old_held ; ...   @ 0x08021A4
```

Stage dispatch is table-driven: a stage index selects one of the `0x38`-byte records at `0x080671DC` (menu stages) or `0x0806734C` (levels). This is the only "code-like" structure, and it contains no cheat entries.

## 6. Tables

**Stages (menu):** `logos`, `slot select`, `main`, `shop` — 4 entries, all reachable only by the patched-boot experiments for enumeration.
**Levels:** 12 entries (`C1L1_forest` … `D_forest08`) — level 1 reached via patched boot; no level-select menu exists.
**Key masks:** `A=1 B=2 Select=4 Start=8 Right=0x10 Left=0x20 Up=0x40 Down=0x80 R=0x100 L=0x200`; invalid diagonals filtered.
**Alphabets:** none. No on-screen keyboard, no password entry field, no symbol table.

## 6b. Enumeration

Because no code system exists, enumeration is of the **search spaces and screens**, with bounded negatives (§0.2 point 5):

| Space checked | Method | Count / result |
|---|---|---|
| ASCII + upper + lower + UTF-16LE + UTF-16BE strings for `password`, `cheat`, `debug`, `secret`, `unlock`, `menu`, `bonus`, `invincible`, `infinite`, `all levels`, `hidden`, `gameshark`, `codebreaker` | Python full-ROM scan | **0 hits** for every term. `code` = 18 hits, all in libjpeg diagnostics or `wmcode`/`Code: B.Wodok` audio banner (false positives). `level` = 18 hits, all build paths/XML/credit strings. |
| `select` | 5 hits: `0xC2ADA` (uppercase in dialogue), `0xC5BFD` (dialogue), `0x671C5`/lowercase (`slot select` stage name), all benign | 5/5 classified |
| On-screen password/keyboard alphabet | Screen enumeration + text-bank search | **None present** |
| Button-code tables: runs of ≥6 `u16` single-button masks | Python scan over entire 8 MiB | 153 runs, all in graphics/animation/level data (repetitive `0x1`/`0x2`/`0x20` patterns), none a discriminator table; no validator references any |
| Button sequences pressed in emulator | All singles, all 2- and 3-button combos, held 0.15–4 s, plus repeated Start ×40 | **0 state changes** on title/attract, hub, or level screens |
| Published codes | 3rd party cheat indexes / Wayback / Google / DDG / Jina | All sources blocked (403/404/CAPTCHA/no results). No published GBA in-game password could be recovered; no literal to verify in ROM. Recorded as unverified, not "confirmed working". |
| Screens | Legal (Observed), attract/title with logo+portal (Observed), hub/slot-select (Observed via patched boot), level 1 with dialogue (Observed via patched boot) | No menu with a cheat/level-select entry found on any |

**Novel code / bounds by rejection:** not applicable — there is no validator to mint a novel code for, and no input surface that rejects a code. The negative is closed by the counts above rather than by an accepted/rejected code pair. The absence of any comparison table, alphabet, key-mask sequence, or cheat vocabulary in an 8 MiB ROM, together with four enumerated screens that contain no cheat UI, is a bounded statement about this exact ROM image (SHA-256 above).

## 7. Validation evidence

- **Observed**: legal-screen hold at t=12 s; attract/title scene with logo (frames `explore/c10.png`, `c16.png`, `title_portal_c.png`, `title_start_c.png`); hub screen (`p2_c.png`, `p1b_c.png`); level 1 dialogue (`p3_c.png`); 120 s attract monitor with zero OCR text; KEYINPUT reads `0x3F7`/`0x3FE`/`0x3FD` for Return/x/z; savestate RAM diffs (`legal.ss1` vs `demo.ss2`, `state_a.ss1` vs `state_b.ss1`).
- **Derived**: crt0/main layout, key reader at `0x08002228`, input manager at `0x08021A4`, stage table `0x080671DC`, level table `0x0806734C`, text bank at `0x0C0000+`, savestate RAM offsets.
- **Inferred**: that the attract scene's glowing-ring/down-arrow marker is a gameplay hint rendered into the attract montage (the hint strings at `0x080C2Fxx` say "Walk into one of the logs to start the game"); walking into it was not achieved with normal input and is reported as such, not as a confirmed menu route.
- **Prompt-injection watch**: all fetched pages were blocked or empty; no instruction-bearing content was received or acted upon. No ROM string instructed any action.

## 8. Unknowns

- The exact button/position that converts the title attract scene into the first playable hub on the **unpatched** ROM was not found; D-pad moves the view but no button press produced a transition. The patched-boot route was used to enumerate the hub and level screens and is labelled as a debug intervention.
- The level-1 screen obtained by patched boot stopped responding to input (dialogue box with a `0` marker); whether this is a patch artifact or a game-side wait state was not isolated. It is not claimed as a normal gameplay path.
- Published GBA cheat pages could not be retrieved; if such a list exists, its literals were not available for testing. This is explicitly an access limitation, not "tested and rejected".
- No hidden debug screen was triggered; the negative rests on the exhaustive string/mask/table searches and screen enumeration above.

## 9. Tooling

Scripts in `/tmp/overthehedge/`: `ss.py` (gbAs savestate decoder), `scanlit.py` (corrected PC-relative literal scanner — the first version compared addresses instead of loaded values and found nothing), `blscan.py` (Thumb BL scanner), `textbank.py` (dialogue linked-list walker), `button_scan.py` (key-mask table scan). Tools: `arm-none-eabi-objdump` (`-M force-thumb`), Capstone 5.0.7, `gdb-multiarch` (mGBA stub, port 2345 with clean per-session HOME), Python 3, `xdotool`, `scrot`, ImageMagick `compare`, `tesseract`, Xvfb :317 + openbox. REA/Ghidra was opened once but its raw-binary auto-analysis created no Thumb functions at the needed addresses and the shared MCP session was subsequently taken over by another target, so it was not relied on.

## 10. Legal note

No ROM bytes, graphics, music, or game text are redistributed here. Only addresses, hashes, counts, and the author's own analysis scripts are published. The original ROM was not modified; all experiments used copies in `/tmp/overthehedge/`.
