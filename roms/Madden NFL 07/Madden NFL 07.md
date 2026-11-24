# Madden NFL 07 (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Madden NFL 07.gba` (4,194,304 bytes / 0x400000) |
| Header title | `MADDEN 2007` (0xA0..0xAB) |
| Game code | `B7ME` (0xAC..0xAF) |
| Maker | `69` (EA), fixed byte `0x96`, version `0x00` |
| Header complement | `0x45` (expected `0x5E` for the title bytes — header was edited/rebuilt; normal for a scene image) |
| Header checksum | `0x0000` (rebuilt-header artifact) |
| Entry word | `0xEA00002E` (stock `b 0xC0`, not a cracktro patch) |
| MD5 | `7cb3748cbf790d4e8b50926b28299153` |
| SHA-1 | `fd62edcf3c30b8f2a821a5dbfe67aa50f150feae` |
| SHA-256 | `c2b1cb5acda7b2afbacc982ecd2ed41c462a220133c9f994f19c0762c360aaee` |

**Phase 0 result:** one Nintendo-logo hit only, at file offset `0x0`; there is no second/multiboot header, no appended trainer, and no boot selector. The image is a single retail-style NTSC-U GBA ROM (Exient Entertainment / EA Sports, 2006). The only 0x26..0x27 string-bank oddity is a leftover `Madden NFL 06 John Madden Football is a trademark` line at `0x26BFB0` — stale legal text, not a second game.

**Shared with the sibling `Madden NFL 06.gba` (B6ME, MD5 `37fe4eeab5274d244e5e6853881307ad`):** the engines are the same Exient family (identical `../frontend_psx/cardgal.c`, `../game_psx/...` source-path strings; both have exactly two ASCII `CODE` strings, both SFX enums), and 07 carries one stale 06 legal string. The images are otherwise distinct builds: only ~16% of the first 64 KiB is byte-identical, the UI text banks at `0x26B000..0x26D000` differ in 7,725/8,192 bytes, and the cheat surfaces are the same *kind* of negative (no password screen) for independent reasons verified in this image. Nothing from the 06 analysis was assumed for 07.

## 2. Executive summary

**There is no in-game password / code-entry system and no hidden/debug menu in this GBA build.** The "Madden Codes" password screen that the console versions of Madden NFL 07 expose under `My Madden → Madden Cards` does **not** exist here: the GBA `MADDEN CARDS` menu has exactly three entries (`CHALLENGE STATUS`, `CARD BOOK`, `RESET CARDS`) and no code field. All 61 published console-code literals (e.g. `5LAWO0`, `XL7SP1`, `WROA0R`, `S9OUSW`, `B57QLU`, the cheerleader set, and the Madden-06 set) are absent from this ROM in ASCII, lowercase, `+0x20`, reversed and UTF-16LE/BE encodings (0 hits). The complete GBA UI text bank (`0x26B2F4..0x26CF50`, dumped in full) contains no string containing `CODE`, `PASSWORD`, `SECRET`, `CHEAT`, `DEBUG` or `UNLOCK`; the only two `CODE` strings in the whole 4 MiB are SFX identifiers in `audset.c`/`sfxseq.c` tables. 3rd party cheat indexes independently reports "no Madden NFL 07 cheats or cheat codes for Game Boy Advance"; the only GBA "codes" published are CodeBreaker/GameShark RAM patches (memory editing), which are out of scope here.

**The in-game unlockable system is Madden Cards** — 100 challenge tasks, tokens, and 161 collectible cards — earned by gameplay, not entered as text. It was enumerated statically (§6b) and walked on screen with RAM evidence.

**One undocumented developer input exists:** holding **A+B+Select+Start simultaneously** fires a global soft-reset gate at `0x08017610`, which calls the re-init handler at `0x08016988`. This was confirmed both statically and in the emulator (screen returns to the EA Sports splash; RAM byte `0x0201F624` changes `0xFF → 0x00`, exactly the store at `0x08016994`). It is a reset/debug shortcut, **not** a cheat that grants content, and it is unreachable as a "code" because it has no entry UI. The `cmp r0,#0x7B` branch in the handler is dead: no code path ever writes 123 to `0x0201F624` (writers store only `0x00` and `0xFF`).

All fetched web pages were treated as data; no prompt-injection payload was encountered in this run.

## 3. How to reproduce

* Emulator: mGBA SDL (`mgba -3`, headless `Xvfb :316`, `SDL_AUDIODRIVER=dummy`), stock keymap A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows.
* Boot path with reproducible input: license screen → `Start` → EA Sports splash → `Start` → title ("MADDEN NFL 07") → `Start` → **MAIN MENU**.
* MAIN MENU entries: `PLAY NOW`, `LINK PLAY`, `GAME MODES`, `MY MADDEN`, `MINI CAMP`, `CREDITS`.
* `MY MADDEN`: `ROSTERS`, `MADDEN CARDS`, `NFL RECORD BOOK`, `SETTINGS`.
* `MADDEN CARDS`: `CHALLENGE STATUS`, `CARD BOOK`, `RESET CARDS` — **no "MADDEN CODES" entry**. `CARD BOOK` shows `COMPLETE SET 0/161`, `TOKENS REMAINING 0`, `Page 1 of 18`, `NEW PACK - 40 TKNS`.
* `GAME MODES`: `SEASON`, `TWO MINUTE DRILL`, `PRACTICE`, `SITUATION`. `MINI CAMP`: `FIELD GOAL KICK`, `PASSING`, `RUNNING`, `TACKLING`, `PUNTING INSIDE 20`, `WR CATCH`, `DB COVER`, `40 YARD DASH`, `RUSH QB` (scrollable).
* In-game pause menu (10 entries): `RESUME GAME`, `CALL TIMEOUT`, `INSTANT REPLAY`, `SUBSTITUTIONS`, `STATS`, `CHALLENGE STATUS`, `NFL RECORDS`, `AUDIOLES`, `CONTROLS`, `SETTINGS` → `GAMEPLAY`, `PENALTY SETTINGS`, `SOUND OPTIONS`; `GAMEPLAY` → `INJURIES`, `GAME FATIGUE`, `AUTO SUBS`, `REMEMBER LAST PLAYER`, `PASSING MODE`.
* Hidden input test: on any screen, hold `x`+`z`+`BackSpace`+`Return` (A+B+Select+Start) ~200 ms → game resets to the EA Sports splash. Rejected-control test: pressing `A+B+Start` (no Select) or `A+B+Select` (no Start) produces no reset.
* Published-code test: there is no field to type into; 61 console-code literals were searched in the ROM instead (0 hits, see §6b).

## 4. Address map

| Item | Address (ROM unless noted) | Evidence |
|---|---|---|
| GBA header / title | `0x08000000..0x080000BF` (title at `0x080000A0`) | Observed |
| UI text bank (all menu labels) | `0x0826B2F4..0x0826CF50` — plain ASCII, NUL-terminated | Observed (full dump) |
| 128-byte glyph/substitution table | `0x0826B42C` (chars `0x43..0x63`), 14 word xrefs; not a code alphabet | Derived |
| String-ID / text pointer table | `0x0838D318..0x083EEC4`, 1,771 pointers; **entries 1..100 = challenge texts** starting at `0x0838D318` (`COMPLETE A 30 YARD PASS OR LONGER`) | Derived |
| Card description table | `0x0838ECD0..0x083ED30` region (17 `NAME*SHORT*DESC****` records, `0x0838FD90..0x0839079C`) plus player-card names | Derived |
| Hidden-input gate (A+B+Select+Start) | `0x08017610` — `ldrb` flag `0x0201F624`; `ldrh` KEYINPUT `0x04000130`; `movs r0,#0xF; bics r0,r1; cmp r0,#0xF; bne`; `bl 0x08016988` | Derived |
| Hidden reset/re-init handler | `0x08016988` — writes 0 to `0x0201F624`, cycles `0x020201B4` 2..14 via `0x08017668`, calls `0x08019C9C`, `0x080174A0`, `0x08017AF4`, `0x080BACC8`×4, `0x080BFBC8` | Derived |
| Gate flag | EWRAM `0x0201F624` (0xFF in normal states, 0 after reset; writers at `0x080041A8`, `0x080041CA`, `0x08011BDE`, `0x08016994`, `0x080169F4`) | Derived + Observed |
| Standard input reader | `0x0801638` (`~KEYINPUT` mirror) and alternate at `0x0801A000` — no code checks | Derived |
| Token count (from published CodeBreaker search) | EWRAM `0x020276B4` — observed `0x00` at 0 tokens; memory-edit address only, not used as a code | Observed |
| Savestate RAM layout (for reproduction) | `.ss1` PNG `gbAs` zlib chunk: IWRAM at raw `0x19000`→GBA `0x03000000`; EWRAM raw `0x21000`→GBA `0x02000000`; state length `0x61000` | Derived |

## 5. Algorithm

No password validator, checksum, alphabet, or code generator exists in this build. The only algorithmic input check is the hidden reset gate:

```text
gate_08017610():
    if byte[0x0201F624] == 0: return
    keys = ~(*0x04000130) & 0x000F          ; active-high A(1) B(2) Select(4) Start(8)
    if keys != 0x0F: return
    handler_08016988()

handler_08016988():
    if byte[0x0201F624] == 0x7B: goto tail ; DEAD: no writer stores 0x7B
    byte[0x0201F624] = 0
    if byte[0x0201FCA8] == 1: goto tail
    if byte[0x0201F628] != 1: call 0x080173DC
    byte[0x02028D48] = 1; byte[0x020201B4] = 0
    repeat: byte[0x020201B4] += 2; call 0x08017668(byte[0x020201B4])
            until byte[0x020201B4] > 13            ; cycles 2,4,...,14
    byte[0x020201B4] = 14
    if byte[0x0201F628] != 2: halfword[0x04000054] = 14
    call 0x08019C9C; byte[0x0201FCA8] = 1; call 0x080174A0; byte[0x02028D48] = 0
tail:
    call 0x08017AF4; call 0x080BACC8 ×4; clear two halfwords; call 0x080BFBC8
    ; observable result: soft reset to EA Sports splash
```

The "locked" branch `byte == 0x7B` cannot be reached by any controller input: exhaustive listing of the five literal-pointer writers of `0x0201F624` shows stores of only `0x00` and `0xFF`.

## 6. Tables

| Space | Count / encoding | Notes |
|---|---|---|
| Password/code entry fields | **0** | No screen, no alphabet, no validator, no buffer |
| ASCII `CODE` occurrences in ROM | **2** | `0x0838A9B0` (`audset.c` SFX enum: SEAS/USPR/AREC/USET/CODE/SINJ/2MIN) and `0x083EAD28` (`sfxseq.c`) — neither is user input |
| Published console codes verified literally | **61 tested / 0 present** | ASCII, lowercase, `+0x20`, reversed, UTF-16LE/BE; includes XL7SP1, WROA0R, 5LAWO0, S9OUSW, RLA9R7…W9UVI9, cheerleader set KL0CRL…PRI5SL, Madden-06 set 2Y6S7Q…7L8C2W |
| UI text-bank keyword hits | **0** for CODE/PASSWORD/SECRET/CHEAT/DEBUG/UNLOCK | Bank `0x0826B2F4..0x0826CF50` dumped in full |
| Hidden input gates found | **1** | `0x08017610`, mask `0x000F` held A+B+Select+Start |
| Known button sequences searched | 3 (Konami 10-press, L+R+Start, A+B+Select+Start as u8/u16 LE/BE) | No table entries; the A+B+S+Start behavior is code, not a stored mask sequence |
| Challenge tasks | **100** | String-ID table entries 1..100 at `0x0838D318`, e.g. `COMPLETE A 30 YARD PASS OR LONGER`, `WIN BY 56 OR MORE POINTS…` |
| Madden Cards | **161** (UI shows `COMPLETE SET 0/161`); 18 pages × 9 slots = 162 (one unused) | 17 named cheat-effect cards (BIG MONEY, BINGO, DA BOMB, STICKY FINGERS, CAN'T TACKLE THIS, EXTRA CREDIT, 13 O'CLOCK, 1ST AND 5, …) plus player/historic cards |
| Token economy | 40 tokens per new pack; task scale ROOKIE=1, PRO=2, ALL PRO=3, ALL MADDEN=6 | Observed on CHALLENGE STATUS and CARD BOOK |
| Published GBA CodeBreaker codes | 10 (e.g. `820276B4 FFFF` max tokens) | Memory-editor patches (out of scope); noted only as RAM landmarks |

## 6b. Enumeration

**Space definition.** There is no password space to enumerate: 0 input fields, 0 alphabets, 0 checksum fields, 0 literal tables. The closest in-scope system is the Madden Cards unlockable space, which is fully characterised above: 100 ordered challenge tasks, 161 card slots, a 40-token pack price, and token scales 1/2/3/6. The complete challenge-table extent was read from the pointer table (`0x0838D318` + 100 entries, ending at `0x0838D484` where mode names begin), so the negative "no 101st task" is bounded by the table, not by an incomplete search.

**Novel code.** Not applicable — no code system exists, so no unpublished code can be minted. Per §0.2 this negative is proven rather than asserted: (a) every reachable screen was walked with a saved state and a RAM diff (main menu, My Madden, Madden Cards and all three sub-screens, Game Modes, Mini Camp, Credits, Link Play, team/side select, coin toss, live game, pause and all pause sub-screens); (b) the entire UI text bank was decoded and contains no code-related label; (c) 61 published code literals were searched in six encodings with 0 hits; (d) the only input gate in ROM was found statically, enumerated to its single mask (`0x000F` held), its dead branch was proven unreachable, and it was triggered in-game with RAM confirmation.

**Bounds proven by rejection.** The gate rejects subsets: `A+B+Start` (no Select) and `A+B+Select` (no Start) do not fire `0x08016988` — the comparison `keys == 0x0F` is exact, and any other key combination yields a different value (the mask ignores D-pad/L/R, so those are not "rejections" but don't add effects). The dead `0x7B` branch is unreachable by input. Published codes cannot be "entered" to be rejected because no entry surface exists; their absence from the ROM is the bounded result.

**Unpublished finding.** The A+B+Select+Start soft reset is not in any of the GBA cheat lists consulted (3rd party cheat indexes GBA cheats, 3rd party cheat index-equivalent wiki checks, 3rd party cheat indexes). It is developer-intended (a re-init shortcut in the input/timer code) and was reproduced with RAM evidence: after the press, `0x0201F624 = 0x00` (was `0xFF`), the screen returned to the EA Sports splash, and the token/card state did not change (0 tokens, 0/161 cards before and after).

## 7. Validation evidence

* **Observed** — emulator screenshots and savestate RAM reads: every screen listed in §3; `CARD BOOK` `COMPLETE SET 0/161`; token scale 1/2/3/6; soft-reset screen EA splash; `0x0201F624` `0xFF → 0x00` across the combo; EWRAM/IWRAM diffs of 280–90k bytes between screens.
* **Derived** — disassembly of `0x08017610` / `0x08016988` / `0x08017668`; literal-pointer enumeration of all five writers of `0x0201F624` (no `0x7B`); full ASCII text-bank dump; 1,771-entry string table with challenges 1..100; 61-code × 6-encoding ROM scan with 0 hits; single Nintendo-logo header at `0x0`.
* **Inferred** — the exact visual intent of the `0x08016988` re-init sub-steps (camera/audio reset cycling `0x020201B4 = 2..14`) is inferred from the I/O writes and call graph; the observable outcome (soft reset) is observed. The 128-byte table at `0x0826B42C` is likely a glyph/substitution table, not a code alphabet — its exact consumer was not isolated.

## 8. Unknowns

* The purpose of the 128-byte `0x0826B42C` table (14 xrefs; probably font/glyph ordering) was not fully isolated; it contains no code-like strings.
* The exact semantics of the `0x7B` sentinel check in `0x08016988` are unknown; it is unreachable from controller input, and only a direct RAM write could set it.
* Whether a Nintendo-GameCube-GBA link cable or the DS "insert GBA cart" bonus-card easter egg is implemented in this image was not tested (no second console/link hardware; no strings for it in the GBA bank).
* The per-card gameplay effects were not individually triggered (would require farming 40 tokens per pack); the card table and challenge table are enumerated statically.

## 9. Tooling

* `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, GNU `strings`, `grep`, `objdump` (`arm-none-eabi-objdump -M force-thumb`), Python 3 + capstone 5.0.7.
* Scripts in `/tmp/madden07/`: `xref.py` (PC-relative literal / BL target scanner), `state.py` (mGBA `.ss1` PNG `gbAs` zlib reader), `ramdiff.py` (IWRAM/EWRAM differ), `key.py`, `walk.py`, `survey.py` (XTEST input, screenshots, Tesseract OCR, savestates).
* Headless runtime: `Xvfb :316 -screen 0 1024x768x24`, `openbox`, `mgba -3` with `SDL_AUDIODRIVER=dummy`; GDB stub (`-g`) was blocked by environment conditions, so the guide's §16.13 savestate-diff technique was used for RAM evidence.

## 10. Legal note

No ROM, extracted graphics, audio, or copyrighted assets are redistributed in this report. Only hashes, addresses, algorithms, and original scripts are published.
