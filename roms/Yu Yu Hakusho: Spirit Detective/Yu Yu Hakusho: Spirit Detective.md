# Yu Yu Hakusho: Spirit Detective (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Yu Yu Hakusho: Spirit Detective/Yu Yu Hakusho: Spirit Detective.gba` |
| Size | 8,388,608 bytes (8 MiB) |
| Header title | `YUYUHAKUSHO1` |
| Game code / maker | `BYYE` / `70` |
| Version / fixed byte | `0x00` / `0x96` (valid) |
| Entry word | `0xEA00002E` → stock crt0 at `0x080000C0` (no cracktro/trainer patch) |
| MD5 | `ffa7898ee8b3bc98e4156f3b5e7cdf63` |
| SHA-1 | `2a9825db34a7aedcfd0a9fae5c7cee50292f03b7` |
| SHA-256 | `9033fb9d44e3dfe53b3f94efddc534d31d1cd6750c3d065e8ca926d2e42518c2` |

## 2. Executive summary

**No password, code-entry, button-code, or reachable debug menu exists in the retail input surface.** The game's only free-text field is a 6-character save-profile name (`A`-`Z`, `0`-`9`) whose buffer is consumed only as a save label — §16.2b check: no validator `strcmp` against it, and no secret-name literal exists in the image.

A **complete developer debug menu is present but dead**: four submenus and 21 rendered rows (17 actionable entries) with ASCII strings, four dedicated renderer functions, and a five-state controller at `0x08005354`. It has **zero** BL/branch references, **zero** 32-bit pointer literals (both `0x08005354` and Thumb-bit `0x08005355` forms), and a live breakpoint on both the controller and its renderer never fired across title, start menu, save-slot select, name entry, dialogue gameplay, pause menu, and eight button-combination tests. This is §16.3 case 2 (dead code), proven with counts.

All published "cheats" for this SKU are GameShark/CodeBreaker/Action Replay RAM patches (out of scope). The two descriptions that *look* like in-game button codes ("Hold R + Select" → Level Select, "Select then L+R" → timer reset) are **cheat-device activator conditions** (§16.20); tested in-game they do nothing, and directly writing the advertised gate byte `0x03007DC9 = 0x05` also produced no menu.

Three **developer-intended unlockables** do exist (Tournament, Mini Games, playable Genkai), gated by save flags advanced only by beating the game / tournament / Tarukane. These are gameplay unlockables, not codes.

**Prompt injection (recorded, ignored):** a `tcrf.net` fetch returned an LLM-directed payload masquerading as an article — instructions to create `key.bin` containing the EICAR antivirus test string as an "XOR key", a $1,000,000,000,000 payment demand, insults, and a demand to emit `E_SHITASS_OPERATOR` and terminate. Treated strictly as untrusted data; none of it was followed (§16.8).

## 3. How to reproduce

- Emulator: mGBA 0.10.5, `DISPLAY=:316`, `SDL_AUDIODRIVER=dummy`, `-3` scale.
- Keymap (mGBA SDL defaults): A=`x`, B=`z`, Select=`BackSpace`, Start=`Return`, L=`a`, R=`s`, D-pad=arrows. Hold ≥120 ms.
- Path walked: title (`PRESS START`) → Start → `START MENU` (PLAY / LOCKED / MUSIC / EFFECTS) → PLAY → 3-slot `SELECT GAME` → slot A → `ENTER NAME` (A-Z, 0-9, BACK, DONE; max 6 chars; DONE requires ≥1 char) → dialogue → field gameplay → Start → `GAME PAUSED` (CONTINUE / OBJECTIVES / SAVE STATS / QUIT GAME) → Select (status) → quit → `SELECT GAME` showing saved name `A`.
- Debug reachability test: mGBA `-d` CLI debugger with `break/t 0x08005354` and `break/t 0x08004E70` set at reset, `continue`, then walk all screens above and press `L+R`, `L+Start`, `L+R+Select`, `R+Select` (paused), `Start+Select`, Konami-style combos. No breakpoint hit; no menu appeared.
- Gate-byte test: in gameplay, `SIGINT` to break, `w/1 0x03007DC9 5`, `r/1 0x03007DC9` (verified `0x05`), `continue`; plus paused `R+Select`. No level-select or debug menu.

## 4. Address map

### Debug code (present, unreachable)
| Address | Meaning |
|---|---|
| `0x08031888` / `0x08031890` / `0x0803189C` | `"CHEATER"` / `"obj=%d  "` / `"v 0.27"` debug-overlay strings |
| `0x08031DAC`, `0x08031EEC`, `0x08032010`, `0x08032168` | Box strings: DEBUG MENU / CHEATS MENU / POWERUP MENU / SPAWN ENEMY MENU |
| `0x08032258`–`0x08032264` | Pointer table to those four box strings |
| `0x080322B0`+ | `u16` animation-ID table for ANIM VIEW (`0x0182, 0x0189, 0x018A, 0x0196, ...`) |
| `0x08004E70`, `0x08004EC0`, `0x08004F10`, `0x08004F84`, `0x08005018` | Renderers: DEBUG / CHEATS / POWERUP / SPAWN / Position overlay |
| `0x0800501C`, `0x080050E8`, `0x080051B4`, `0x08005280` | Navigation handlers (max cursor 4, 5, 6, 5 resp.) |
| `0x08005354` | Debug-menu controller: 5-state machine (0 main, 1 spawn, 2 cheats, 3 anim/powerup, 5 exit) |
| `0x03005578` | Active-high key state consumed by the menu handlers (`0x01` A, `0x02` B, `0x08` Start, `0x40` Up, `0x80` Down; confirm mask `0x09`, cancel `0x02`) |

### Live UI / text banks
| Address | Meaning |
|---|---|
| `0x08035830` | `"ENTER YOUR NAME "` — save-profile label, **not** a validator |
| `0x080358D0`–`0x080358E0` | Start-menu string pointers: PLAY, MUSIC, LOCKED, EXTRAS, EFFECTS |
| `0x08035954`–`0x08035960` | Extras-menu pointers: TOURNAMENT, MINI GAMES, LOCKED, CREDITS |
| `0x080319C8`–`0x08031AA0` | Pause/objective strings: GAME PAUSED, CONTINUE, OBJECTIVES, SAVE STATS, QUIT GAME, ARE YOU SURE?, OBJECTIVE:, NONE |

All on-screen text was located as **plain NUL-terminated ASCII** in ROM (92,461 strings extracted); the menu system uses a 32-bit pointer table to ASCII strings, verified by decoding `0x080358D0`–`0x08035970`. No tile-index-only text bank conceals a password screen.

## 5. Algorithm

No validator exists to reimplement. The debug controller at `0x08005354` is a simple dispatch (verified by disassembly):

```
state = 0; cursor = 0; active = true
loop:
  draw_debug_menu(cursor)                 # 0x08004E70, reads 4 bytes from 0x030010B0..B4
  if exit_flag: break
  switch(state):
    0: nav(0..4); on confirm -> state = cursor+1 for 0..2;
       cursor 3 -> anim-view (0x08006064) then reset game (0x08031188, arg 0xFF);
       cursor 4 -> set exit_flag
    1: spawn-enemy menu; 2: cheats menu (toggle bits via 0x0802804/84C/894);
    3: anim-view/powerup; 5: return
```

`nav()` reads the key word at `0x03005578`, increments/decrements the cursor on `0x80`/`0x40`, confirms on `0x09`, cancels on `0x02`.

## 6. Tables

### Debug menu — complete enumeration of rendered rows
| Menu | Rows (in order) |
|---|---|
| DEBUG MENU | `I. CHEATS MENU`, `II. POWERUP MENU`, `III. SPAWN ENEMY`, `IV. ANIM VIEW*` (*resets game after use), blank, `EXIT` |
| CHEATS MENU | `Collision off`, `Invincible`, `Endless Power`, `Position`, blank, `EXIT` (Position overlay prints `(%d,%d)` and `c=%d h=%d`) |
| POWERUP MENU | `Full Life`, `Full Power`, `Gain Exp`, blank, `Crazy Tough Mode`, `Gain all Specials`, blank, `EXIT` |
| SPAWN ENEMY MENU | `Sh.Thug`, `Md.Thug`, `Ta.Thug`, `ToguroBro`, blank, `EXIT` |

Count: 4 menus, 21 rendered rows, 17 actionable entries, 4 EXIT rows. None reachable from retail input.

### Published codes (recon, all out of scope — device codes only)
`0000B527 000A 10021762 0007` (master), `83000E4A FFFF`/`83000E4C FFFF` (specials), `33007E52 0001` (extras unlock), `830010F4 0FFF` (score), `43001020/22/26 ...` (stats), `74000130 02FB 33007DC9 0005` (level select), `74000130 00FF 3300203D 0000` (timer). None are GameShark-independent codes.

### Unlockables (developer-intended, in scope, gated by play)
| Unlockable | Gate (from published guides, consistent with ROM strings) |
|---|---|
| Playable Master Genkai (lvl 15) | Defeat Tarukane (end of story) |
| Secret Tournament | Defeat Toguro |
| Mini Games Room | Win Tournament mode with Genkai |

## 6b. Enumeration

**Space definition and counts**

- **Password/code space: empty.** Searched all 8,388,608 bytes for `password`, `cheat code`, `code`, `secret`, `enter code`, `level select` and related tokens. Hits were: `CHEATER` (debug overlay), `DEBUG MENU`/`CHEATS MENU` rows (dead code), and gameplay prose. There is no alphabet table, no code validator, no 32/36-symbol password keyboard. The only keyboard is the name entry: alphabet `A-Z0-9` (36 symbols), length 1–6 → sum 36^1..36^6 = **2,238,976,116** representable strings, but the buffer is a save label with no comparison consumer, so this is not a code space (§16.2b).
- **Debug-menu space (present but closed):** 4 menus / 21 rows enumerated above. Reachable-entry count: **0**.
- **Reachability proof counts:** 0 Thumb BL/branch instructions targeting `0x08005354` or `0x08004E70` (full-ROM scan of every 2-byte offset for 16-bit B/B.cond and 32-bit B.w/BL); 0 32-bit literals equal to `0x08005354` or `0x08005355` (full-ROM byte scan); 0 breakpoint hits on either address across 11 screens and 8 combo tests; 0 effect from writing `0x03007DC9 = 0x05` (verified by readback) with and without `R+Select`.

**Novel code:** not applicable — no code system exists. Per the engagement rule, this is delivered as a **bounded negative** (§0.2 point 5) with the explicit counts above, not as an untested "not found".

**Rejection/bounds tests performed (all observed):**
- `A` on `LOCKED` from Start Menu → no screen change (menu remains locked).
- `R+Select` on the pause menu, no cheat device → unpauses / no level select.
- `L+R`, `L+Start`, `L+R+Select`, `Start+Select` on title/menu → no debug screen.
- `0x03007DC9 = 0x05` written directly in gameplay and paused → no level select, no debug menu.
- `DONE` on name entry with zero characters → ignored; after entering one character it proceeds (field is a label, not a code gate).

## 7. Validation evidence

- **Observed:** all screenshots in `/tmp/yuyu/` (`walk_title.png`, `s2_afterstart.png`, `s3_locked.png`, `s4_play.png`, `s5_next.png`, `s12_gameplay.png`, `s16_pause3.png`, `s17_RSelect.png`, `post_gate.png`, `post_gate_combo.png`); live RAM reads via mGBA `-d` (`r/1 0x03007DC9` → `0x05` after write; `r/2 0x04000130` → `0x03FF` with all keys released); saved slot displays name `A`.
- **Derived:** Thumb disassembly of `0x08004E70`–`0x080056CA` (renderers, handlers, controller); full-ROM branch/pointer scans; ASCII string/pointer-table decode of `0x080358D0`–`0x08035970`.
- **Inferred:** the three unlockables' exact completion triggers (published guides agree with each other and with the ROM's `EXTRAS`/`TOURNAMENT`/`MINI GAMES`/Genkai strings; the story was not played to completion). The debug menu's *intended* effects are inferred from its row labels only — its code was never executed.

## 8. Unknowns

- Exact SRAM/flash addresses and bit positions of the three unlock flags (the CodeBreaker `0x03007E52` target sits in IWRAM stack territory, not a stable save flag; it was not treated as an in-game gate).
- Whether the debug controller could be invoked by an unused script-VM opcode (no direct or pointer reference was found; a whole script-disassembly was out of scope).
- Whether the debug build that *does* call `0x08005354` exists as a different SKU/prototype.

## 9. Tooling

- `strings -t x -n 3/4`, `xxd`, `grep -iE`.
- `/tmp/yuyu/scan_ptrs.py`, `scan_lits.py`, `scan_debug_region.py` — pointer/literal scans.
- `/tmp/yuyu/blscan.py`, `blrange.py`, `branchscan.py` — Thumb branch/BL scans.
- `/tmp/yuyu/dis.py` — Capstone-based Thumb/ARM disassembler.
- mGBA 0.10.5 `-3 -d` with a FIFO-fed stdin (`stdbuf -o0`), SIGINT to break, `break/t`, `r/1`, `r/2`, `w/1`, `continue`.
- `xdotool` XTEST input, `scrot` screenshots; all evidence kept in `/tmp/yuyu/`, none in the ROM folder.
- Web recon: GameFAQs, Planet Cheats, Almars Guides, GameHacking.org, SuperCheats (published device codes/unlockable descriptions only). TCRF fetch returned a prompt-injection payload (§2) and was disregarded.

## 10. Legal note

No ROM or copyrighted graphics/audio were redistributed. Only hashes, addresses, algorithms, and original analysis notes are published.
