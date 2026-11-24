# Mike Tyson Boxing (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Mike Tyson Boxing.gba` (in `roms/Mike Tyson Boxing/`) |
| Size | 4,194,304 bytes = 0x400000 (4 MiB) |
| `file` ID | Game Boy Advance ROM image: "TYSON BOXING" (AM6E41, Rev.00) |
| Header title @0xA0 | `TYSON BOXING` |
| Game code @0xAC | `AM6E` |
| Maker @0xB0 | `41` (Ubisoft) |
| Software version @0xBC | `0x00`; complement @0xBD = `0x5F` (not 0xFF — header byte edited; see note) |
| Header checksum @0xBE | `0x0000` |
| Entry word @0x00 | `0xEA00002E` → stock `0x080000C0` (no cracktro patch) |
| MD5 | `26138b868def156d361525dc69c2899e` |
| SHA-1 | `7b60e69296eabd98ea17836add7f6f8bb9a07731` |
| SHA-256 | `758f03f068830972c7f7f256c149f458678b9c148851709ab279cd081dd19c0b` |
| Release | USA, 2002-03-06; developer Virtucraft, publisher Ubisoft (AGB-AM6E-USA) |

**Phase 0 / embedded-header scan:** the full 156-byte Nintendo logo occurs exactly **once**, at file offset `0x04`. There is no second GBA header, no multiboot stub, no appended trainer/cracktro, and the entry branch is the stock `b 0x080000C0`. The only non-stock header byte is the complement check (`0x5F` instead of `0xFF` for version 0), consistent with a rebuilt/edited header field; it does not affect the ROM body and no code patch was found. The `file` utility's "AM6E41" is game code `AM6E` + maker `41`, not a special revision.

**Save type:** 512-byte SRAM (`Mike Tyson Boxing.sav` created by mGBA); save data sits at the tail of that file (e.g. `00 00 ab b5 54 4d ff … 00 01 00 00` at 0x1F0). Generated `.sav`/`.ss*` were removed at the end of the run (§7).

---

## 2. Executive summary

**No developer-intended password, button code, or reachable hidden/debug menu exists in this retail GBA ROM.** The only codes published for the GBA SKU are Action Replay / GameShark / CodeBreaker memory-patch codes (Cheat Happens, CodeJunkies, GameHacking.org), which are explicitly out of scope for this engagement.

The ROM *does* contain a complete localized text bank for a **CHEAT** options screen — entries such as `SHOWCASE MODE / UNLOCKED BOXERS`, `WORLD MODE / UNLOCKED BOXERS`, `ALL MODES / UNLOCKED BOXERS`, brightness levels, and `WORLD MODE BOXER: #` (file 0x47940–0x47C6C, pointers at 0x3FBA94–0x3FBB84) — plus `Enter your name` style hidden-boxer messages (`You have unlocked a hidden boxer: #`, 0x50548). These strings are referenced **only** by the 5-language string-pointer tables (xrefs to `0x08047940` are `0x0803FBA94` and `0x0803FBA9C`), never by a code path that can be reached from any menu in the retail build. This is the **cut/dead-feature** case of §16.3, not a code system.

Every reachable screen was booted and walked with screenshots and RAM evidence (§3, §7): language select, PRESS START title, 5 main-menu tabs, OPTIONS → SOUND OPTIONS / GAME OPTIONS / CREDITS / DELETE DATA / EXIT, VS boxer select → fight setup → fight → pause, WORLD slot select → boxer creation → name entry → career GYM/CHALLENGE/STATS/CONTROL, SHOWCASE and PRACTICE description screens. The on-screen alphabet/text bank was decoded (font tile-indexed text; see §4). The title-screen button space (all 10 single presses and all 45 two-button combinations, plus common 3-button sets) was exercised without any hidden screen or confirmation appearing.

The name-entry field is a **label, not a validator** (§16.2b): its buffer is EWRAM `0x02003394`, and all nine code xrefs to that address are display/dialogue/menu functions, none a `strcmp`/comparison against a constant. The widely published PlayStation name passwords (`STUPID`, `BONGY`, `NORMAL`, `OUCH`, `HURTS`, `NECK`, `BINGY`, `GONE`, `CLUBFUD`, `OLD MAN`) and PS title-screen button codes do **not** exist in this GBA image (literal search count = 0 for each except the generic UI word `NORMAL`), consistent with §16.11: the GBA SKU is a different engine (Virtucraft) from the PS game (Codemasters).

Confidence: **high** for the negative within the enumerated surfaces; the CHEAT screen's cut/dead status is **derived** from static xrefs plus exhaustive menu walking, and is reported as such.

---

## 3. How to reproduce

**Environment (exact):** Xvfb `:319`, 1024x768x24; `DISPLAY=:319 openbox`; `SDL_AUDIODRIVER=dummy`; mGBA (SDL binary at `/usr/local/bin/mgba`), `mgba -3 <rom>` (and `mgba -3 -d <rom>` for the pty debugger). mGBA SDL keymap used: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad = arrow keys. Key holds 100–300 ms; screenshots via `scrot` cropped with `convert -crop 720x480+152+144 +repage`.

**Menu path to every reachable screen (all observed):**

1. Boot → *Virtucraft* logo → *Codemasters* legal → language select (5 flags: EN, FR, DE, IT, ES). Press A on UK flag.
2. Title: `PRESS START` (animated red boxer background). Press Start.
3. Main menu: horizontal tab ring of 5 tabs — SHOWCASE, VS, WORLD, PRACTICE, OPTIONS (verified by pressing Right repeatedly and reading the highlighted tab).
4. Each mode tab opens a description box with `A Continue / B Cancel`: SHOWCASE (16 champions, tournament), VERSUS (8 champions), WORLD (career), PRACTICE (gym), OPTIONS.
5. OPTIONS → `SOUND OPTIONS` (MUSIC, SOUND FX, CROWD FX, GO BACK), `GAME OPTIONS` (3 KNOCK DOWN RULE, SAVED BY THE BELL, LANGUAGE, TURBO SHOWCASE, BRIGHTNESS, GO BACK), `CREDITS`, `DELETE DATA` ("do you want to erase this data?"), `EXIT`. **No CHEAT item at any time**, before or after the title/button-code tests.
6. VS → HOW MANY PLAYERS (ONE..EIGHT) → `PLAYER 1 CHOOSE YOUR BOXER` (8 boxers, Mike Tyson first) → fight OPTIONS (VENUE, NUMBER OF ROUNDS, ROUND LENGTH, DIFFICULTY) → fight → Start → pause menu: `GAME PAUSED / CONTINUE GAME / THROW IN THE TOWEL / QUIT GAME`. **No CHEAT entry.**
7. WORLD → CHOOSE A SLOT (two NEW BOXER slots) → SELECT PLAYER (name `Connor Melbourne`, weight, STR/SPD/BAL/RES/END bars) → `ENTER YOUR NAME` (grid A–Z, `-`, SPC, END; `A OK`, `B Cancel`) → career hub with GYM / CHALLENGE / STATS / CONTROL tabs (CHALLENGE offers Save Career, Retire, Load Career, Options). **No CHEAT entry.**
8. SHOWCASE and PRACTICE description screens were entered and cancelled; no further hidden screen behind them.

**Codes tested:** PS passwords and PS button codes mapped to GBA buttons (see §6b); all produced no visible confirmation and no new menu item. Published GBA codes are AR/GameShark memory patches and were **not** applied (out of scope).

---

## 4. Address map

| Item | File offset | ROM address | Evidence |
|---|---:|---|---|
| GBA header / entry | 0x000–0x1FF | 0x08000000– | Observed `xxd` |
| CHEAT localized string (`CHEAT`, `TRICHE`, `CHEAT`, `TRUCCO`, `TRUCOS`) | 0x47940 | 0x08047940 | Derived pointer table |
| CHEAT-menu item strings (`SHOWCASE MODE\nUNLOCKED BOXERS` … `ALL MODES\nUNLOCKED BOXERS`) | 0x47960–0x47AF7 | 0x08047960–0x08047AF7 | Observed `xxd`; pointers at 0x3FBABC–0x3FBAF4 |
| OFF/ON, NORMAL/BRIGHT/VERY BRIGHT, `WORLD MODE BOXER:\n#` | 0x47B54–0x47C6C | 0x08047B54–0x08047C6C | Observed |
| Lowercase `cheat` (career newspaper headline block, not a menu) | 0x48124 | 0x08048124 | Observed context |
| `You have unlocked a hidden boxer: #` (5 langs + uppercase variants) | 0x50548–0x506C8 | 0x08050548–0x080506C8 | Observed; pointer table 0x3FBF38–0x3FBF5C |
| `NEMESIS UNLOCKED`, `ALL BOXERS UNLOCKED`, `# BOXERS REMAINING` | 0x22904, 0x22970, 0x22A6C | 0x0822904… | Observed (boxer-select status text bank) |
| Text-pointer group containing CHEAT | 0x3FBA94–0x3FBAA4 | 0x0803FBA94 | Derived: 5 u32 pointers; xrefs from code = none |
| Text-pointer groups for CHEAT-menu items | 0x3FBABC–0x3FBB84 | 0x0803FBABC… | Derived |
| `Shin'en Multimedia. Code: B.Wodok` (audio-engine banner — false positive) | 0xCF3E6 | 0x08CF3E6 | Observed; classified as engine banner (§11) |
| `CODE AI BOTTEGHINI PER LA SFIDA DI` | 0x4F698 | 0x0804F698 | Observed: Italian career-newspaper dialogue, not a password |
| Global keypad/history handler (`FUN_0800161C`) | 0x161C | 0x0800161C | Ghidra decompile; reads KEYINPUT 0x04000130 literals at 0x1660/0x16B4/0x1788 |
| Key-history buffer pointer | — | 0x02000A44 | Derived (23 code xrefs from Ghidra) |
| Career boxer **name** buffer (NUL-terminated) | state 0x24394 | 0x02003394 | Observed via savestate diff; xref from text table at 0x3FA658 |
| Name display/cursor copy | state 0x23024 | 0x02002024 | Observed via savestate diff |

Savestate mapping used (§16.13): mGBA `.ssN` PNG → `zlib.decompress` of `gbAs` chunk → 397,312-byte state; EWRAM begins at state offset 0x21000 (so state `0x24394` ↔ EWRAM `0x02003394`). Name buffer proof: baseline `Connor\nMelbourne` at 0x23024/0x24394; after typing one `A`, bytes became `41 5F 00 …` at 0x23024 and `41 00 6E …` at 0x24394 (RAM, observed). Typing `ZZZZ` produced ASCII 'Z' tile index `0x5A` in the VRAM tilemap copy at state 0xFA61 — confirming font/tile-indexed text, not secret encoding.

---

## 5. Algorithm

No password/validator algorithm exists in this SKU. The only "algorithm" worth recording is the text storage and the buffer layouts:

```
; localized text bank (5 languages: EN, FR, DE, IT, ES)
; each logical string = 5 consecutive u32 pointers, 20-byte stride
; example (CHEAT), file 0x3FBA94:
  ptr[0]=0x08047940  "CHEAT"       (EN)
  ptr[1]=0x08047948  "TRICHE"      (FR)
  ptr[2]=0x08047940  "CHEAT"       (DE -- shares EN)
  ptr[3]=0x08047950  "TRUCCO"      (IT)
  ptr[4]=0x08047958  "TRUCOS"      (ES)

; name entry buffer in EWRAM
u8 name[0x??] @ 0x02003394   ; NUL-terminated, ASCII, written by grid handler
u8 name_cursor_copy @ 0x02002024 ; display copy with '_' cursor byte
```

Strings are drawn through a font tile-index table: the on-screen alphabet letters correspond to ASCII-derived tile indices (observed 'Z' → 0x5A in VRAM tilemap), which is why a naive `strings` scan finds the UI labels but not their rendered glyphs. Decoding this bank is what let the CHEAT-menu entries be read at all; there is no hidden cipher.

---

## 6. Tables

**Published GBA codes (all out of scope — memory patches, not developer codes):**

| Source | Codes | Scope decision |
|---|---|---|
| Cheat Happens (2003-07-16), "Mike Tyson Boxing Action Replay Codes, US" | 27 encrypted AR codes: (M) master `aa99e094 8aafd4d0 c16b590b ce930b7e`; Inf Stamina, 1-Hit KO, Always Round 1–10, Max Cash, Max World Wins, **All Boxers Unlocked** `e58eb9e9 55235cad`, etc. | Excluded: Action Replay encrypted RAM patches |
| CodeJunkies US / GameHacking.org (AGB-AM6E-USA) | 27 ARMAX/GS codes incl. `Unlock All Boxers`, `Infinite Special`, `Maximum Training` | Excluded: GameShark/Action Replay memory patches |
| ROMSFUN / libretro | 41 **PlayStation** GameShark codes | Wrong SKU and out of scope |

**Published PS codes tested against this GBA ROM (all negative):**

| PS code (GameFAQs, PS SKU) | GBA button mapping tried | ROM literal search | Result |
|---|---|---|---|
| Unlock Everything: Square, Circle, Up, Down | A,B,Up,Down · B,A,Up,Down · Up,Down,A,B | mask arrays at §6b | No confirmation; OPTIONS unchanged |
| 2-D Mode: Down, Up, Circle, Square | Down,Up,B,A · Down,Up,A,B | none | No effect |
| Mutant Mode: Square, Left, Up, Triangle | B,Left,Up,A and variants | none | No effect |
| More Custom Boxer Parts: L1,R1,X,X,Triangle,X | L,R,B,B,A,B | none | No effect |
| Name passwords: STUPID, BONGY, NORMAL, OUCH, HURTS, NECK, BINGY, GONE, CLUBFUD, OLD MAN | typed on `ENTER YOUR NAME` (where practical) | 0 hits each, except `NORMAL` = generic brightness UI string at 0x47B70/0x47D48 | Not a code surface in GBA build |

**Hidden/unlockable boxers:** `NEMESIS` appears as a boxer name and in `NEMESIS UNLOCKED` status text (0x228A0, 0x22904); `You have unlocked a hidden boxer: #` exists in the text bank. **Derived/inferred:** these are progression/save-bit unlocks (§16.18), not code-triggered — no validator or input path to them was found, and no setter reachable from controller input was identified. Reported as an unlockable, **not** as a cheat code.

---

## 6b. Enumeration

Per §0.2, the enumeration target here is the *negative space*, stated with counts so the absence is a bounded result rather than "I did not find it".

**1. Code-system space — what was searched and the counts:**

| Search | Space | Hits relevant to a code system |
|---|---|---|
| Embedded GBA headers (156-byte logo) | whole 4 MiB | 1 (the real header) — no packed/second image |
| `strings -t x -n 4` grep for `password\|cheat\|code\|secret\|debug\|unlock\|boxer\|menu\|invalid\|continue\|options\|hidden` | 33,176 strings ≥5 chars | `CHEAT`/`cheat` only as localized menu/headline text (§4); no `password` prompt, no `INVALID`, no debug generator string |
| Literal `grep -abo` for the 10 PS name passwords | 4 MiB | 0 for 9; `NORMAL` only as generic UI word (2 hits) |
| Thumb PC-relative literal loads into the text-pointer-table region | every 2-byte offset, 0–4 MiB | 11 hits, all false positives (ASCII data decoded as code) |
| u32 word references into `0x0803F000–0x08040000` | every 4-byte offset | 63, all data-to-data (localized pointer groups / dialogue tables); **0 code→CHEAT-string xrefs** |
| Ghidra xrefs to `0x08047940` ("CHEAT") | complete analyzed program | 2, both data pointer-table slots (`0x0803FBA94`, `0x0803FBA9C`) |
| u16 key-mask table scan (single masks + 2-key combos, runs ≥3) | 0x08000000–0x08030000 | 53 runs, all coincidental instruction encodings; no button-code array |
| Literal u16 search for PS codes mapped to GBA masks (both active-high and KEYINPUT-complement forms) | whole ROM | 0 for all tested prefixes |
| Thumb `cmp` near `ldrh` with key-mask immediates | 0–0x50000 | 34 sites, none a sequence validator (all menu counters/linked-list code) |

**2. Screen space — every reachable screen walked (Observed):**

Language select → PRESS START title → main menu 5 tabs → 5 mode description boxes → OPTIONS/SOUND OPTIONS/GAME OPTIONS/CREDITS/DELETE DATA → VS player-count → boxer select → fight setup → fight HUD → pause menu → WORLD slot select → SELECT PLAYER → ENTER YOUR NAME → career GYM/CHALLENGE/STATS/CONTROL → SHOWCASE/PRACTICE descriptions. **Count: 5 main tabs + 5 options submenus + 8 in-game/career screens; CHEAT menu absent from all.**

**3. Button space at title screen (Observed):** 10 single presses + all 45 unordered 2-button combinations + common 3-button sets exercised with 100 ms holds; no hidden confirmation, no new menu entry. Full-screen-image hash comparison was invalidated by the animated title background, so the PRESS START box region (240×80) was used for the final targeted pass; no persistent change attributable to a code was seen.

**4. Novel code / bounds proof:** **Not applicable — there is no code format to mint.** Per §0.2 this section must state the space; the space here is empty for developer-intended inputs: 0 alphabets, 0 validators, 0 reachable debug screens, 0 published in-game codes (all published GBA codes are external memory patches). Consequently there is no checksum to break and no out-of-range value to reject in-game. The negative is bounded by the counts in items 1–3 and by the literal/ps-code tests in §6.

**5. What would change this conclusion:** a hidden activation reachable only after a full career clear (e.g. winning all belts) was not played to completion — that is a *progression gate*, not a code, and would be a save-bit unlock (§16.18). No evidence of a controller-input setter for the unlock flags was found.

---

## 7. Validation evidence

* **Observed:** all hashes/header bytes; single Nintendo-logo hit; every screenshot listed in §3; savestate RAM diff locating `0x02002024`/`0x02003394` and the font tile index `0x5A` for 'Z'; name buffer changing from `Connor…` to `A\0…`; 512-byte SRAM with tail data; mGBA `-d` pty debugger `status`/`x/4`/`watch` responses; Ghidra/REA xref results.
* **Derived:** CHEAT strings are referenced only by 5-language pointer tables (ROM xrefs), so no code path reads them as a menu label in the retail build; name-field xrefs are display-only (not a validator); PS literals absent ⇒ PS code system not ported; key-mask tables absent ⇒ no title-screen button-code array.
* **Inferred:** the CHEAT screen is a **cut feature** inherited from the Codemasters PS engine (the GBA text bank carries its labels and hidden-boxer messages), not a gated developer menu with a known trigger. A read watchpoint on `0x0803FBA94` never fired while walking menus, but a control watchpoint on a string that *is* displayed (`0x0803FB940`) also failed to fire, so the watchpoint oracle is **inconclusive** and is not used as evidence.
* **Prompt injection check:** fetched web pages were treated as data. No fake "decode key", payment request, or tool instruction was encountered in this run; the only suspicious-looking hits (`Shin'en … Code: B.Wodok`, `CODE AI BOTTEGHINI…`) are ordinary engine/dialogue text and are classified as such.

---

## 8. Unknowns

* Full career completion was not played to a gold belt; if the hidden-boxer unlock (`NEMESIS`, `You have unlocked a hidden boxer`) is awarded there, that is a gameplay/save unlock and remains unproven either way (labelled inferred in §6).
* The exact semantics of the SRAM tail bytes at 0x1F0 (`ab b5 54 4d … 00 01 00 00`) were not reversed; no cheat-code setter was found pointing at them.
* The CHEAT screen's would-be entries are fully readable from the text bank (§4/§6), but no executable handler could be tied to them, so their exact runtime effect (if any in a dev build) is unknown.
* mGBA's read watchpoints on ROM did not fire even for a control string; the debugger could not be used as an accept/reject oracle on this title (§16.19) because there is no validator to call.

---

## 9. Tooling

* `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings`, `grep -abo` — Phase 0/1.
* Python 3 + `capstone` 5.0.7 (installed) — Thumb literal/BL/key-mask scans; custom `ptr.py`, `dumpptrs.py`, `scanlit.py`, `nameentry.py`, `ssdiff.py`, `dbg.py`, `dbgdaemon.py`, `gba.py`, `ram.py` in `/tmp/miketyson/`.
* `arm-none-eabi-objdump` (`-M force-thumb`) — targeted disassembly of the keypad handler.
* REA MCP (Ghidra 12.1.4 via `provider_id: "ghidra"`) — `open_binary`, `xrefs`, `trace_feature`, `analyze_function`; session closed after analysis.
* mGBA SDL (`-3`) under Xvfb `:319` + openbox; `xdotool` XTEST input; `scrot` + ImageMagick for screenshots.
* mGBA `-d` pty debugger bridged by a Python TCP daemon (mGBA's GDB stub was unreliable: `vMustReplyEmpty: timeout`).
* Savestate RAM extraction: PNG `gbAs` chunk → `zlib.decompress` (§16.13).

**Legal note:** no ROM image, extracted graphics, music, or game text assets are redistributed here — only hashes, addresses, algorithms, and the analyst's own tooling are published.

**Cleanup:** all processes started for this run were terminated by their recorded PIDs (mGBA, Xvfb :319, openbox, debugger daemon); generated `Mike Tyson Boxing.sav` and `.ss1–.ss9` files were removed from the ROM folder. No other display or process was touched; `roms/INDEX.md` was not edited.
