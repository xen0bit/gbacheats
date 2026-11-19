# Frogger's Journey: The Forgotten Relic (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Frogger's Journey: The Forgotten Relic.gba` |
| Size | 8,388,608 bytes (`0x00800000`) |
| Header title | `FROGGER RPG` (`0xA0`–`0xAB`) |
| Game code | `BFJE` |
| Maker | `A4` (Konami) |
| Version | `0x00` |
| Fixed byte `0xB2` | `0x96` |
| Complement `0xBD` | `0xB0` |
| Header checksum `0xBE` | `0x0000` |
| Entry word `0x00` | `0xEA00002E` (stock ARM branch to crt0 at `0x080000C0`) |
| MD5 | `16ae239c819d0a772307e3193d593860` |
| SHA-1 | `19ed8e33fee941bae582adbc67bf8b6bc53cb069` |
| SHA-256 | `3ab7f261854c35067666e303d8fd8cdd662cefcbedb45e84b152b13a585288dd` |

Phase 0 result: **single, unmodified retail image**. Scanning all 8 MiB for the 156-byte Nintendo logo produced exactly one hit, at file offset `0x4`. No multiboot stub, no concatenated image, no appended trainer, and the entry branch is the stock `b 0x080000C0` rather than a scene cracktro (§16.1). Header checksum `0x0000` is the ordinary rebuilt-header artifact; nothing in the first 4 KiB indicates a patched loader. crt0 calls `main` at `0x080002A0` (Thumb pointer `0x080002A1` in the literal pool at `0x08000100`).

## 2. Executive summary

**No developer-intended in-game cheat/password/button-code system exists in this ROM.** The game is a battery-save action-adventure: it has no password entry screen, no cheat menu, no level-select code surface, and no reachable debug menu.

The one genuine piece of debug material is a cell-position overlay routine at **`0x080189D8`**. It renders `"Player Cell X: {%}"` / `"Player Cell Y: {%}"` (message-table entries 178/179) plus three numeric format fragments. **It is dead code in the retail build**: a full 8 MiB scan found **zero** Thumb `BL` references and **zero** 32-bit data pointers to it (Thumb-bit variant `0x080189D9` included), and its private output flag at `0x02028EB4` is referenced only by that routine and its own literal pool. The TCRF article states that "there exists a working debug code that shows Frogger's cell positions" but leaves the actual code as "To do: Cheat Code"; no such sequence is documented on any list found, and none could be recovered from the image.

Published material for this title consists only of **CodeBreaker / Game Genie memory-edit codes** (e.g. `8200041C FFFF`, `DE0D2A764ABA`), which are explicitly out of scope here and are *not* in-game codes. GameFAQs' cheats page for this exact SKU (id `915003`) is **empty**; the "level passwords" found in searches belong to *Frogger Advance: The Great Quest*, a different GBA game (§16.11), and were verified absent as literals from this ROM. The widely published Konami code belongs to *Frogger's Adventures 2: The Lost Wand* and other Frogger SKUs, not this one; entering it at the title screen and in-game produced no state change.

The negative is bounded rather than assumed: all on-screen surfaces were walked with screenshots and savestate RAM reads, the entire 298-message × 5-language text bank was decoded to ASCII, 57,160 ASCII strings were classified, and the complete 8 MiB was scanned for key-mask code tables. Counts and searches are in §6b.

## 3. How to reproduce

* Emulator: `/usr/local/bin/mgba` 0.10.5, SDL front-end, `SDL_AUDIODRIVER=dummy`, Xvfb `:315`, 3× scale, 1024×768 root.
* **Input caveat (§16.2):** X11 auto-repeat makes a 150 ms key hold fire twice. Every GBA press must be a **30–40 ms tap** with ≥120 ms gap; longer holds made menus appear to "ignore" input or bounce straight back to the attract screen.
* Keymap verified in-emulator: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad = arrow keys (the mGBA SDL defaults).
* Menu path actually walked:
  1. Boot → Konami Computer Entertainment Hawaii splash → title logo (`Frogger's Journey — The Forgotten Relic`, "© 1981 2003 KONAMI").
  2. `x` → character attract cycle (bird, fox, squirrel, …) → `x` → **NEW GAME** menu (single visible entry, orange cursor).
  3. `x` → **three-slot save screen** ("empty / empty / empty").
  4. `x` on slot 1 → long intro (chair, aircraft, grandpa's letter) → in-game at Kabohti with heart HUD and curio counter.
  5. `BackSpace` in gameplay → OPART inventory (3×3 item grid, A/B assignment slots, L/R tabs, description pane). No hidden tab or extra page appeared.
  6. `Return` in gameplay → no pause menu; `BackSpace` advances dialogue.
* Code tests performed (all with 30–40 ms taps): Konami `↑↑↓↓←→←→ B A` at the title menu, in gameplay, and re-tested after fixing the auto-repeat problem; plus L/R and Select at the title and save-slot screens. None changed game state.
* RAM evidence method (§16.13): mGBA `.ssN` files are PNGs with a zlib `gbAs` chunk; decompressed size is 397,312 bytes. Layout used: CPU/IO `0x00000`, VRAM `0x1000`, IWRAM `0x19000` (maps `0x03000000`), EWRAM `0x21000` (maps `0x02000000`). Savestates were taken before (`ss1`) and after (`ss2`) the in-game Konami attempt and diffed.

## 4. Address map

| ROM address | File offset | Meaning | Evidence |
|---|---|---|---|
| `0x08000000` | `0x000000` | Header, Nintendo logo, stock entry branch | Observed |
| `0x080000C0` | `0x0000C0` | ARM crt0 | Derived (disassembly) |
| `0x080002A0` | `0x0002A0` | `main`; dispatches `[global+0x77]` mode 0..4 | Derived |
| `0x08002408` | `0x002408` | Input sampler: reads `0x04000130`, XORs with `0x3FF` (active-high), stores 256-frame history at `[0x030063BC] + 0x84 + i*4` (`held` u16, `released` u16 at `+2`) | Derived |
| `0x08018990` | `0x018990` | Message-display helper used by the debug overlay | Derived |
| **`0x080189D8`** | **`0x0189D8`** | **Debug cell-position overlay routine** (dead code) | Derived |
| `0x08018A74`–`0x08018A8C` | `0x018A74`–`0x018A8C` | Its literal pool: `0x02028EB4` (private flag), `0x08064FE4`, `0x08064FEC`, `0x08064FF4`, `0x08064FFC` | Derived |
| `0x0801D6FC` | `0x01D6FC` | Script-VM getter returning bit 7 of `[global+0x48]`; used as the overlay's enable gate | Derived |
| `0x080219C4` / `0x080219D4` | `0x0219C4` / `0x0219D4` | Script getters "get player cell X" / "get player cell Y" | Derived |
| `0x08050000`–`0x0805FFFF` | `0x050000`–`0x05FFFF` | English/other-language message text bank | Observed |
| `0x08064D38`–`0x08065000` | `0x064D38`–`0x065000` | Script-VM opcode *debug names* (`get joy trigger`, `get player cell X`, `get save_data_check`, …); not cheats | Observed |
| `0x08064FE4` | `0x064FE4` | `{r}{s0}` — overlay format prefix | Observed |
| `0x08064FEC`/`0x08064FF4`/`0x08064FFC` | `0x064FEC`/… | `({%},` / ` {%})` / `({%},` — numeric fragments for the overlay | Observed |
| `0x082264BC` | `0x02264BC` | Text pointer table, language 1, **298 entries** of `u32` into `0x0805xxxx`. Other 298-entry tables: `0x0822B578`, `0x0822DDC0`, `0x0830608`, `0x0832E50` (five languages total) | Derived |
| table index 178 / 179 | `0x0226784` / `0x0226788` | `0x08059A28` = `{r}{s0}Player Cell X: {%}{n}`; `0x08059A10` = `{s0}Player Cell Y: {%}` | Observed |

RAM addresses (from decompressed savestates):

| Address | Role | Observed value |
|---|---|---|
| `0x030063BC` | Pointer to the main global state struct | `0x03004890` |
| `0x03004890 + 0x48` / `+0x49` | Gate byte family | `0x00` / `0x00` at title; bit 7 = 0 |
| `0x03004890 + 0x84…` | Input history (see input sampler) | populated per frame |
| `0x02028EB4` | Debug-overlay private flag | `0x11` before and after the Konami test — **unchanged** |

## 5. Algorithm

There is no cheat validator to reimplement. The only algorithm recovered is the debug overlay, reconstructed from Thumb disassembly at `0x080189D8`:

```c
void debug_cell_overlay(void) {
    if (script_get_bit7_global_48()) {   // BL 0x0801D6FC, bit 7 of [g+0x48]
        *(u8*)0x02028EB4 = 0;            // suppress / turn off
        return;
    }
    if (*(u8*)0x02028EB4) return;        // already on
    u16 cx = script_get_player_cell_x(); // BL 0x080219C4
    u16 cy = script_get_player_cell_y(); // BL 0x080219D4
    msg_start(0, 0, ...);                // 0x08007E9C / 0x08007EC0 family
    msg_text(0x08064FE4);                // "{r}{s0}"
    msg_number(0, cx, ...);              // 0x08007CD8
    msg_text(0x08064FEC);                // "({%},"
    msg_number(0, cy, ...);
    msg_text(0x08064FF4);                // " {%})"
    msg_text(0x08064FFC);                // "({%},"
    *(u8*)0x02028EB4 = 1;                // latch on
}
```

This routine's two message strings are ordinary entries in the 298-message text table, which is why a `strings` search finds them. Nothing in the ROM calls it. The main loop at `0x080002A0` dispatches on `[global+0x77]` (values 0–4) to the title/attract, menu, gameplay and transition handlers; no branch tests a cheat flag or a button sequence.

## 6. Tables

1. **Message table** — five parallel 298-entry `u32` tables (§4). Index 178/179 are the debug cell strings. No entry in any of the five languages is a password prompt, cheat list, level-select, unlock code, or debug-menu label. The menu labels visible on screen ("NEW GAME", "empty", the OPART grid) are **tile-indexed bitmap graphics** and do not appear as ASCII anywhere (§11 / §16) — the text bank was therefore decoded by table, not inferred from `strings`.
2. **Published codes (verified absent from ROM as literals)** — Game Genie/CodeBreaker memory edits only, out of scope: `00000000 000A / 1000241C 0007` (master), `8200041A FFFF` (all special items), `8200041C FFFF` (all letters), `82000416 FFFF` (all weapons), `320003CD 000A` (unlimited health), `820003D6 270F` (max curio), `DE0D2A764ABA`, `F60DF4D641B9`, `F38DD0C61191`, `319684D54399`, `1C047A7C41DB`, `7C68E9BF41DF`, `3C5EE87E640E`. Literal search for each in the 8 MiB: **0 hits**. `59NR`, `23G-W`, `7F3J-F`, `16YWLT` (published for *Frogger Advance: The Great Quest*) also: **0 hits**.
3. **Input key masks** — active-high after the XOR at `0x08002408`: `A=0x001, B=0x002, Select=0x004, Start=0x008, Right=0x010, Left=0x020, Up=0x040, Down=0x080, R=0x100, L=0x200`. Used for the exhaustive mask-sequence scan in §6b.
4. **Unlockables** — OPART abilities (Grappling Hook, Shield, Scuba, Push Blocks, Time Stop, Rock Buster, Mega Claw, Flashlight, Long Jump) are ordinary quest-item flags carried in the battery save; their setter is the story script, reachable only by playing the game. This is a save-bit progression system, not a cheat system (§16.18).

## 6b. Enumeration

Because the answer is negative, this section proves the *searched space*, as §0.2 requires.

| Search | Space examined | Result |
|---|---|---|
| Embedded images | all 8,388,608 bytes, Nintendo logo scan | **1** header; no trainer/second image |
| ASCII text | `strings -n 3`: 114,406 strings; `strings -n 4`: 57,160 strings | 0 password/cheat/code/debug-menu strings; every `secret` hit is NPC dialogue |
| Localized message tables | **5 × 298 = 1,490** decoded messages (all five language banks) | 0 password/cheat/debug labels; 2 messages are the debug cell overlay |
| Literal published codes | 13 CodeBreaker/Game Genie strings + 4 passwords from a different SKU | **0** hits in 8 MiB |
| Button-code mask tables | all 8 MiB scanned for u8 and u16 runs of ≥5 consecutive single-key masks (both active-high and active-low encodings), plus Konami prefix stored newest-first | **0** plausible tables; all hits fall in compressed graphics/audio |
| Debug-overlay reachability | all 8 MiB for Thumb `BL` targets, 32-bit literal loads and 32-bit pointers to `0x080189D8`/`0x080189D9` | **0** `BL`, **0** literals, **0** pointers |
| Debug flag writers | all 8 MiB for `0x02028EB4` | **3** hits, all inside the overlay routine and its literal pool (file `0x189D4`, `0x18A74`, `0x18A94`) — no external writer |
| Live button codes | Konami `↑↑↓↓←→←→BA` at title menu, at save-slot screen, and in gameplay; Select/L/R at each | **0** state changes; savestate diff: overlay flag `0x02028EB4` = `0x11` → `0x11` |
| Reachable screens (walked) | title logo; 4+ character attract frames; NEW GAME menu; 3 save slots; 4 intro cutscenes; Kabohti gameplay with HUD; OPART inventory (3×3 grid, L/R tabs, A/B slots) — 8+ distinct surfaces | **0** hidden/debug/level-select entry, **0** text-entry field |

**Space size statement:** there is no code space to enumerate — the accepted set is **empty** for in-game codes (0 passwords, 0 button codes, 0 cheat menu entries). Consequently no novel code could be minted and no bounds could be proven by rejection; the requirement for a generated unpublished code applies only when a system exists (§0.2). The bounded result above is the applicable deliverable.

**What would change the answer:** a developer/prototype build containing the script that invokes `0x080189D8`, or documentation of the exact input sequence TCRF alludes to. Neither is present in this exact ROM (`SHA-256 3ab7f261…288dd`).

## 7. Validation evidence

* **Observed** — all eight screens above captured via `scrot` on `:315`; hashes/header from `file`, `xxd`, `md5sum`/`sha1sum`/`sha256sum`; one logo hit; `0x02028EB4` read as `0x11` from both decompressed savestates; 135 EWRAM bytes differed between `ss1`/`ss2`, all attributable to NPC/dialogue/gameplay state, with the debug flag unchanged.
* **Derived** — Thumb disassembly of `0x08002408` (input sampler), `0x080189D8`–`0x08018A92` (overlay), `0x0801D6FC` (gate getter), `0x080219C4`/`0x080219D4` (cell getters), `0x080002A0` (main dispatch); text-table indexing derived from the 298-entry pointer table and confirmed by decoding indices 178/179.
* **Inferred** — the purpose of `[global+0x48]` bit 7 (likely an "in menu / in dialogue" state, since the overlay clears itself when it is set) and the role of the overlay as leftover debug infrastructure rather than a shipped feature. Both are consistent with the code but not exercised, because the routine is unreachable.
* **External claim, unverified** — TCRF's statement that a "working debug code" exists. Treated as data, not as an instruction; the article does not publish the code and no fetched page was followed as a command (§16.8).

## 8. Unknowns

* The exact input sequence behind the TCRF claim, if it exists outside this retail build.
* Whether the overlay was ever invoked by a script that was removed before release; the three format strings and two message rows survive, the call site does not.
* The five language tables were counted and decoded structurally; the four non-English banks were not proofread word by word, but the same index positions hold the same debug rows and none contains a password-like token.
* Physical cartridge behavior was not tested; all conclusions are for this exact 8 MiB image.

## 9. Tooling

* `file`, `xxd`, `strings -t x`, `grep -abo`, `md5sum`/`sha1sum`/`sha256sum` — Phase 0/1.
* Custom Python in `/tmp/opencode/froggersjourney/`: `phase0.py` (header/logo scan), `xref.py`/`xref2.py` (Capstone Thumb literal-pointer and direct-pointer xrefs), `blscan.py` (raw Thumb BL scan), `dis.py` (Capstone Thumb disassembly), `btnsearch.py` (key-mask sequence scan), `dumptext.py` (message bank decoder), `ss.py`/`ssread.py`/`ssdiff.py` (mGBA `gbAs` savestate parser and RAM diff), `ui.py`/`ui2.py`/`nav.py` (XTEST input and screenshots).
* `arm-none-eabi-objdump`, Capstone (bulk Thumb disassembly), `gdb-multiarch` (GDB stub was unavailable: ports 2345/2460 were held by other sessions), REA/Ghidra (opened the raw image at `0x08000000`; its generic ARM language does not recover Thumb procedures, so it contributed no xrefs; session closed).
* `Xvfb :315`, `openbox`, `mgba` 0.10.5 SDL, `xdotool`, `scrot`, ImageMagick. All started on display `:315` only.

## 10. Legal note

No ROM bytes, graphics, music or game text are redistributed here. Only hashes, addresses, derived algorithms and short diagnostic string fragments are recorded. Fetched web pages were treated strictly as data.
