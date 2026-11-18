# Juka and the Monophonic Menace (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Juka and the Monophonic Menace.gba` |
| Size | 16,777,216 bytes (0x01000000, 16 MiB) |
| Header title | `JUKA` |
| Game code | `BJKP` (P = PAL/Europe), maker `7J` (Zoo Digital Publishing), version `0x00` |
| Fixed byte / main unit / device | `0x96` / `0x00` / `0x00` |
| Header complement / checksum | `0x7E` / `0x0000` |
| Entry word | `0xEA00002E` — the stock GBA `b 0x080000C0`, i.e. **not** a patched cracktro/trainer entry |
| MD5 | `7d098e6eab2ee1cfebdb12e60ac609be` |
| SHA-1 | `ea476896e93db126ea275c5240fec3aeec031db0` |
| SHA-256 | `4a8ea79bb677ca9cff1a490758654943a41e030941e90d4046c3da2990f65f36` |

**Embedded-header scan (Phase 0):** a full-file scan for the 156-byte Nintendo logo found exactly one hit, at file offset `0x00000004` (header base `0x00000000`). There is no second GBA header, no multiboot stub, and no appended trainer block. The `0x0000` header checksum plus a non-trivial complement `0x7E` is consistent with a rebuilt retail header, not a hacked image. **Conclusion: single retail PAL Rev.00 image, no patch/trainer.**

Scope note: the only published "cheat codes" findable for this SKU are **CodeBreaker memory-patch codes** (almarsguides.com); those are memory-edit codes and are explicitly out of scope. No in-game password, button code, or hidden debug menu is published for this game.

## 2. Executive summary

**No developer-intended in-game cheat/password/button-code system exists in this ROM.** This is a bounded negative result, not an absence of effort:

* Web recon found **zero** published in-game cheats (VGChartz "Total cheats available: 0"; GameFAQs hosts only a walkthrough; no TCRF article; the only "cheats" page is CodeBreaker memory patches).
* The ROM contains **no** plaintext UI/debug text in any encoding tested: 305,388 `strings` runs ≥4 chars, and literal counts of `PASSWORD`, `CHEAT`, `DEBUG`, `SECRET`, `UNLOCK`, `CODE`, `ENTER`, `INVALID`, `LEVEL SELECT`, `MENU`, `OPTIONS`, `SELECT`, `CONTINUE` are **all 0** in ASCII, UTF-16LE and case-shifted (`+0x20`) ASCII. All visible text is font/tile-indexed (e.g. "Sleep Potion" is plainly readable in-game but has no byte-string in the 16 MiB image).
* There is no password entry surface: the only title/option screens are the language selector and the "Juka … Monophonic Menace / Start" title card. The in-game screens are field gameplay, dialogue, the R-button potion selector, and a main menu that is **story-gated** (gate proven in §4/§7).
* Button-code tables were searched as u16/u8 single-key-mask runs; no code-referenced table was found. Eight conventional button sequences were pressed on both the title and gameplay screens with no effect (§6b).
* Static and dynamic evidence agree: this title's "menu", collectibles and unlockables are ordinary story/save progression, not a cheat system. Per guide §16.3 this is a **"no system"** result, with the searched space and screen enumeration recorded below.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 (SDL), command `SDL_AUDIODRIVER=dummy mgba -3 <rom>` under `Xvfb :318 -screen 0 1024x768x24` + `openbox`.
* Keymap (verified against savestate `KEYINPUT`, see §7): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows. Keys must be held ~100–250 ms.
* Screen path reproduced: boot → ZOO logo → Orbital Media logo → **language select** (A on English) → story prologue (A to advance) → **title card** (Start) → prologue/teleporter chamber → field gameplay. R opens the potion menu; B exits it. Select is gated (§7).
* Savestates: `Shift+F1…F9` save, `F1…F9` load (verified working). States are written next to the ROM (`*.ss1`…`*.ss9`) and were removed at teardown.
* No codes entered because no in-game code surface exists; published-code verification is documented in §6b.

## 4. Address map

| Item | Address / offset | Evidence |
|---|---|---|
| ROM base / entry | `0x08000000` / `0x080000C0` (branch `0xEA00002E`) | Header, observed |
| KEYINPUT literal pool | `0x08000814` → `0x04000130` | Ghidra xref `0x8000700`, derived |
| Key state, current | IWRAM `0x03001C58` (`u16`) | Ghidra `FUN_080006F4`, derived |
| Key state, previous | IWRAM `0x03001C50` (`u16`) | Ghidra `FUN_080006F4`, derived |
| Key-repeat byte | IWRAM `0x03001C54` | Ghidra, derived |
| "is held" helper | `0x08000228` | Ghidra/Capstone, derived |
| "just pressed" helper | `0x08000244` | Ghidra/Capstone, derived |
| Main game loop | `0x08000498` (calls system handler `0x08000850` each frame) | Ghidra, derived |
| Select/menu dispatcher | `0x08000980` | Ghidra decompile, derived |
| Menu-open function | `0x08008424` → `0x08001A24` | Ghidra xrefs (`0x800099E`, `0x80009B6`), derived |
| Menu gate flag A | IWRAM `0x030049E5` (= `struct@0x030049C0 + 0x25`) | `0x08000976` read; observed 0 |
| Menu gate flag B | IWRAM `0x030055DD` (= `struct@0x030055D0 + 0x0D`) | `0x08000996` read; observed 0 (1 at title) |
| Other Select-gate fields | `0x03001C63`=0, `0x03004530`=0xFFFF, `0x03003FB0`=0/1, `0x030055E2`=0xFF | savestate reads, observed |
| Savestate layout (mGBA `.ss1`, raw `gbAs` 397,312 B) | palette `0x800`, VRAM `0x1000`–`0x19000`, IWRAM `0x19000`–`0x21000`, EWRAM `0x21000`–`0x61000`, `KEYINPUT` @ `0x530` | zlib-decompressed state, observed |

## 5. Algorithm

There is no password validator or checksum algorithm to reverse. The only algorithmic finding is the input/mode gate:

```c
// main loop 0x08000498 -> 0x08000850 each frame
cur  = *(u16*)0x03001C58;   // active-low KEYINPUT copy
prev = *(u16*)0x03001C50;
just_pressed(mask) = ((cur & mask) == 0) && ((prev & mask) != 0);  // 0x08000244

// Select dispatcher 0x08000980 (abridged from Ghidra):
if (gs[3]==0 && entity->field160 != 0xFFFF) open_menu();   // target-driven path
if (gs[3]==0 && [0x03003FA0+0x10]==0 && [0x030049E5]!=0 &&
    just_pressed(0x04 /*Select*/) && [0x030055E2]==0xFF && [0x030055DD]!=0)
        open_menu();                                   // 0x08008424
```

`open_menu()` (`0x08008424`) initialises the menu state and calls `0x08001A24`. In every reachable early-game state the conjunction failed because `0x030049E5` was 0; a patched savestate that set it to 1 had it cleared back to 0 by the game on the next frames, confirming a script-owned, story-gated flag (guide §16.3 category 4). The R-button potion menu opens unconditionally (`0x0800…` path, observed in emulator).

## 6. Tables

* **Language table:** 5 entries — English, French, Spanish, German, Italian (observed on the language screen; the only "options" surface).
* **Potion table (observed):** at least `Sleep Potion ×01`. Left/Right do not cycle it in the opening state (only one entry known).
* **Key masks (GBA active-low, derived from `KEYINPUT`):** A `0x001`, B `0x002`, Select `0x004`, Start `0x008`, Right `0x010`, Left `0x020`, Up `0x040`, Down `0x080`, R `0x100`, L `0x200`; all released `0x3FF`. Confirmed by holding keys and reading savestate offset `0x530` (`BackSpace`→`0x3FB`, `Return`→`0x3F7`, `Up`→`0x3BF`).
* **No cheat/code/password table exists** — see §6b for the bounded searches.

## 6b. Enumeration

Because no code system exists, this section records the **search spaces and their bounds** (guide §0.2 point 5) rather than a code count.

**Text space (proves no text-based password/debug surface):**
* `strings -t x -n 4` over all 16 MiB → 305,388 runs; keyword classification: `PASSWORD/CHEAT/DEBUG/SECRET/UNLOCK/BOSS/LEVEL SELECT/ENTER/INVALID/CODE/MENU/OPTIONS/SELECT/CONTINUE` → **0 each** in ASCII, 0 each in UTF-16LE, 0 each in `+0x20`-shifted ASCII.
* Password-shaped literals: mixed alphanumeric 6–16 char runs with ≥2 digits and ≥3 letters → 14,022 hits, all inside compressed graphics/audio banks (sample offsets `0x0801C26`…`0x080470B7`); 28–40 char "alphabet" runs → 19,982 hits, all data noise (e.g. `2i2i2i…` at `0x08074906`). None is in executable code or referenced as a password alphabet.
* Known cheat literals from other GBA games used as scanner sanity (`HAMA!333`, `L1TTLVN`, `CR3D1TS`, `G3N1VS`) → 0 hits each.

**Button-code space (proves no button-code system):**
* u16 runs of single-button masks `{1,2,4,8,0x10,0x20,0x40,0x80,0x100,0x200}`, length ≥6 → 7,276 runs; u8 analogue → 161,515 runs. Filtering to *distinct, non-repeating sequences with a code/reference xref* yields **0**. All runs lie in compressed data banks (`0x080D…`+).
* Only one hardware `KEYINPUT` reference in the whole image (`0x08000814`, crt0), and the only key consumers are generic helpers (`0x08000228/0x08000244/0x08000274`) and normal menu movement. No press-history ring buffer or validator was found.
* Eight sequences pressed on both **title** and **gameplay** screens, with a title savestate reload between each: Konami `↑↑↓↓←→←→BA`, its reverse, `L+R+Start+Select`, `A+B+Start`, `↑↑+B+A`, `Select+Start`, `L+R` alone, and all ten buttons. **All produced only normal game/menu transitions — no debug screen, unlock, or state change.**

**Published-code verification:** VGChartz cheat list = 0 entries; GameFAQs = walkthrough only, no password list; TCRF = no article; the sole "cheats" page is CodeBreaker (memory patch, out of scope). There is therefore no in-game code literal to verify in the ROM; the CodeBreaker codes were **not** tested because they are memory-edit codes, outside the requested scope.

**Screen enumeration (all reachable screens walked):** ZOO Digital Publishing logo → Orbital Media logo → Language select → Title card → story prologue/dialogue → teleporter chamber (field) → courtyard/tutorial overlays (highlighted target + R prompt, ingredient-jar HUD) → **R-button potion menu** (`Sleep Potion ×01`; Left/Right/Select/B exercised) → combat/tutorial dialogue → spiral teleport transition → lab room with Bufo. Select was tested at every gameplay/dialogue/lab state; the main menu never opened because `0x030049E5` remained 0. **This is the one menu screen that is provably gated, not merely unvisited** (§4, §7); the gate flags, dispatcher and opener are mapped, and the game actively rewrites the flag, so no controller input in the explored segment can reach it.

## 7. Validation evidence

* **Observed** (emulator/savestate): every screen in §6b; R opens the potion menu, B closes it; Select does not open the main menu in any reachable state; all eight button sequences have no cheat effect. `KEYINPUT` decoded from savestate offset `0x530` confirms the physical→GBA key mapping. Savestate diff gameplay vs. potion menu: 1,490 IWRAM bytes and 2,403 EWRAM bytes differ, proving the two are distinct RAM states rather than an overlay misread. Gate flags read from IWRAM: `0x030049E5 = 0`, `0x030055DD = 0` (gameplay) / `1` (title), `0x030055E2 = 0xFF`, `0x03004530 = 0xFFFF`.
* **Derived** (static): header/logo scan; string/keyword counts; button-mask run counts with xref filtering; Ghidra decompilation of the main loop (`0x08000498`), system handler (`0x08000850`), Select dispatcher (`0x08000980`) and menu opener (`0x08008424`); input-helper semantics at `0x08000228/0x08000244/0x08000274`.
* **Inferred**: the exact story event that sets `0x030049E5` is a scripted writer (xrefs `0x0800CB98`, `0x0800D28E`, `0x080174F4`); it was not driven to 1 within the explored early-game segment. The menu's contents (Recipes/Notes/Creatures/Quests/Collections/Instruments/Progress, per the published walkthrough) are therefore reported from the walkthrough, not from a screen I reached — this is the only claim not backed by an observed screen.
* **Prompt-injection check:** all fetched web pages (VGChartz, GameFAQs walkthrough snippets, Wikipedia, almarsguides) were treated as data. No instructions, payment requests, or "decode key" payloads were found in them on this run; none were acted upon.

## 8. Unknowns

* The exact narrative trigger for `0x030049E5` (one of the three writers at `0x0800CB98`/`0x0800D28E`/`0x080174F4`) and hence the main-menu screen itself were not reached; completing the full ~9–13 h story was out of scope. The gate is mapped, so a later analyst can resume at that flag.
* Font/tile glyph mapping was not fully decoded. This is acceptable for the negative because (a) every reachable screen was read visually, and (b) zero keyword literals were found in ASCII/UTF-16LE/case-shifted encodings; a tile-indexed hidden string would still have to be drawn by a screen or a code path, none of which were observed.
* PAL-specific Frostinator bug (Wikipedia trivia) was not investigated; it is a gameplay bug, not a cheat.

## 9. Tooling

* `file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings -t x`, `grep` — fingerprint and literal scans.
* Python 3 + `capstone`/`keystone`, `arm-none-eabi-objdump -M force-thumb/force-arm` — scanner `scan.py`, `static_neg.py`, `static_neg2.py` (keyword/alphabet/button-run counts).
* REA MCP (Ghidra 12.1.4 provider): `open_binary`, `xrefs`, `analyze_function` on `0x080006F4`, `0x08000850`, `0x08000980`, `0x08008424`; evidence IDs `ev_dd66f8387fe37cae3f271f78cd597122568688e51cd1d01e88dc4ccce4639293` (main loop) and `ev_ff922b636ca466dc984c0f8b0da0d6cfdd56f2c093445ebed4c497de635e8544` (KEYINPUT xref).
* mGBA 0.10.5 SDL on `Xvfb :318` + `openbox`, `xdotool` for XTEST input, `import`/`montage`/`convert` for screenshots (kept on disk in `/tmp/opencode/juka`, not attached).
* Savestate decoder `ss.py` (zlib decompress of the PNG `gbAs` chunk) and font experiments `font.py`/`font2.py`.

## 10. Legal note

No ROM bytes, graphics, music or game text are redistributed here. Only hashes, addresses, algorithms, counts and my own scripts are published.
