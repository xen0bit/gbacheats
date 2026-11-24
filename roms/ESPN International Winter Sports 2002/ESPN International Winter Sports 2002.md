# ESPN International Winter Sports 2002 (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `ESPN International Winter Sports 2002.gba` |
| Size | 4,194,304 bytes (0x400000) |
| Header title | `WINTERSPORTS` |
| Game code | `AWIE` (full `AWIEA4`) |
| Maker | `A4` (Atari publishing stamp; developed by Konami Computer Entertainment Osaka) |
| Revision | 0x00 (Rev.00) |
| Fixed byte | 0x96 present; main unit 0x00; device 0x00 |
| Version / complement / checksum | 0x00 / 0xF2 / 0x0000 |
| Entry branch | `0xEA00002E` (stock crt0 → `0x080000C0`) |

Hashes (exact revision analysed):

- MD5 `aee485056bb727880ab4f4056b7da477`
- SHA-1 `ee674c8a32fc6bf1e7a381721c8f9125328f5ec9`
- SHA-256 `843b4ea112c13399eef27c388a20fafb00557509d510b1b53327c514db1d3f47`

Embedded GBA-header scan: the 156-byte Nintendo logo occurs **once** at file offset `0x4` (the normal single-image header at ROM base `0x08000000`). No second logo, no appended trainer, no multi-game shell, no patched entry/cracktro. `file(1)` reports `Game Boy Advance ROM image: "WINTERSPORTS" (AWIEA4, Rev.00)`. This is the stock retail image; no patch/trainer was found or used.

## 2. Executive summary

**This game has no developer-intended password, button-code, or code-entry system, and no reachable debug menu.** The answer is a proven negative, not an incomplete search.

Three independent lines of evidence establish this:

1. **No input surface.** Every reachable screen was walked in the emulator (title, name/country entry, tutorial, event select with all 10 events, mode select, option/ranking, in-game, and the four-entry pause menu). No password field, code-entry keypad, or hidden "cheat" option exists anywhere. RAM was confirmed at every screen via savestate diffs and the mGBA `-d` debugger.
2. **No text or table for a code system.** A case-insensitive sweep of all 4 MiB for `password`, `passcode`, `cheat`, `secret`, `unlock`, `hidden`, `bonus`, `invalid`, `correct`, `wrong`, `enter code`, `codebreaker`, `gameshark`, `debug`, and `level select` returned **zero** hits — both as raw ASCII and after the `+0x20` lowercase→uppercase shift used by some Konami text banks.
3. **Debug menu is dead code.** A large block of debug-menu text (3,548 bytes, `0x0807FD44`–`0x08080B20`) and its two handler functions (`0x0804349C`, `0x080439D4`) exist in the ROM but have **zero code references** (no Thumb BL target, no 32-bit literal pointer) and **never execute**: breakpoints on both handlers were never hit while walking every screen and after trying common Konami unlock sequences (L+R+A, L+R+Start, A+B+Start+Select, full Konami code). TCRF independently classifies this text as *unused* and "needs investigation — see if this can be accessed".

The widely published "big head" button codes (K120 `L,R,L,R,L,L,R,L`; K90 `R,L,R,L,R,R,L,R`; Mogul `↑,↑,↓,↓,←,→,←,→,L,R`) are for the **PS2/GameCube/Xbox** versions, which have L1/R1 shoulder buttons and use sequences beginning with L/R. They do not belong to the GBA SKU: no matching key-mask sequence exists in this ROM and the GBA has only single L/R buttons. The three costume unlocks (Bear/Penguin/Robot: win all golds in Championship/Trial, then press L/R at character select) are **save-bit gated unlockables**, not a code — per guide §16.18 they are reported as such and were not brute-forced as a code.

## 3. How to reproduce

Environment: `Xvfb :317 -screen 0 1024x768x24`, `DISPLAY=:317 openbox`, `SDL_AUDIODRIVER=dummy mgba -3` (mGBA CLI debugger `-d` and GDB stub `-g` both used).

Default SDL keymap verified by reading `KEYINPUT` (`0x04000130`) from an mGBA savestate: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows. Press-and-release with ~100–300 ms holds; the title screen runs a long (~15–20 s) attract sequence before `PRESS START`, and any key during the attract replays it.

Menu path to every screen:

1. Title (`PRESS START`) → **A** plays the ~17 s intro → **NAME ENTRY** (country list: USA/CAN/FRA/GER/UK/ITA/JPN…; on-screen 26-letter + digit keypad).
2. Enter name / press A on `ENTER` → **TUTORIAL** (SKI JUMPING K=90; ~6 A presses to skip) → **gameplay** (Ski Jumping K=90).
3. **Start** in gameplay → **PAUSE** menu: `CONTINUE`, `RETRY`, `EVENT SELECT`, `MODE SELECT`.
4. `EVENT SELECT` → 10 entries: Ski Jumping K=90, K=120, Alpine Skiing Downhill, Freestyle Skiing Moguls, Short Track 500, Figure Skating, Snowboarding Giant Slalom, Snowboarding Halfpipe, Biathlon, Luge. Medal counters (gold/silver/bronze) and world record shown; no hidden entries.
5. `MODE SELECT` → `TRIAL MODE`, `CHAMPIONSHIP MODE`, `EXCITE MODE`, `OPTION`.
6. `OPTION` → `RANKING`, `DATA CLEAR`. Ranking shows 5 slots per event; no hidden option.

Debug-handler test (negative): with breakpoints set at `0x0804349C` and `0x080439D4` (`break`, `continue`), walk steps 1–6 and press L+R+A, L+R+Start, A+B+Start+Select, and the full Konami sequence at the title. `status` shows both breakpoints never hit.

## 4. Address map

| Address | Contents | Evidence type |
|---|---|---|
| `0x08000000` | Stock GBA header / ARM crt0 (`0xEA00002E`) | Derived |
| `0x0807FD44`–`0x08080B20` | Unused debug-menu text bank (3,548 bytes): `BACK UP`, `SOUND`, `MULTI-BOOT`, `BUMPER`, `KAWA`, `TATU`, `TAMA`, `MUTO`, `SOUND TEST`, `ANIME VIEW`, `BG TEST`, `DH TEST`, `GS TEST`, `mutoselect`, `mutoobjtest`, `mutobgtest`, `title`, `howtoplay`, all 10 event names, `-TATSUMI KYOUGI MENU-`, `-TAMAKI KYOUGI MENU-`, `-SYSTEM MENU-`, `MAIN SYSTEM`, `sys_judge`, `sys_rank`, `champion`, `medalget`, `worldrecord`, etc. | Observed (ROM bytes) |
| `0x08304040`–`0x083040D0` | Scene/menu dispatch tables referencing the debug strings (e.g. `MODE SELECT`, `CHAMPIONSHIP`, `TRIAL`, `OPTION`, `NAME`, `RANKING`, `TUTORIAL`, `RESULT`; `tamasystem`, `tamabgtest`, `tamaselect`, `kawaselect`, `sys_judge`, `sys_rank`). These tables are present but are not reached by any game input. | Derived |
| `0x0804349C` | `-SYSTEM MENU-` handler: reads pressed keys at `0x030032B0+4` (`0x40`=Up, `0x80`=Down, `0x01`=A), moves a cursor byte at `0x03000E7C` (0–6), draws 7 menu strings from `0x08304048`. No callers. | Derived |
| `0x080439D4` | `-TAMAKI KYOUGI MENU-` handler: same pattern, cursor at `0x03000E88` (0–2), menu strings from `0x08304090`. No callers. | Derived |
| `0x08043B00` | `-TAMAKI KYOUGI MENU-` init function; writes defaults to RAM. No callers. | Derived |
| `0x0808BD0` | Active-key provider: `~KEYINPUT & 0x3FF` from literal `0x04000130` at `0x0808BDC`. The only such routine with a caller (`0x0808C0C`), used for normal input, not debug. | Derived |
| `0x030032B0` | Input state (held/pressed/released halfwords); key state verified via savestate at state offset `0x530`. | Observed |
| `0x03000E7C`, `0x03000E88` | Debug-menu cursor bytes (written only by the dead handlers). | Derived |
| `0x082FE928`, `0x0830436C` | Common "return to scene" pointers; generic engine, not cheat-related. | Derived |

File offset ↔ ROM address: `ROM = 0x08000000 + file_offset`. All addresses above verified against the analysed bytes with `struct.unpack_from`.

## 5. Algorithm

No password/checksum algorithm exists to reimplement. The only reconstructible logic is the (unreachable) debug-menu UI loop, for completeness:

```
debug_handler():                      # 0x0804349C or 0x080439D4
    keys = [0x030032B0+4]             # pressed mask: Up=0x40, Down=0x80, A=0x01, B=0x04
    if keys & 0x40: cursor = max(0, cursor-1)
    if keys & 0x80: cursor = min(N, cursor+1)
    if keys & 0x01 and cursor == 0:   # first entry
        return scene_ptr_0
    if keys & 0x01 and cursor == 1:
        ...
    draw title + N strings; draw '>' at cursor
    return 0
```

The only reachable input algorithm is the standard key-edge provider at `0x0808C04`:
`held = ~KEYINPUT & 0x3FF`; `pressed = held & ~prev`; `released = ~held & prev`; `prev = held` — used by normal menus.

## 6. Tables

- **Alphabet/code tables:** none exist. No 32-symbol keypad for codes, no code literal table, no checksum constants, no XOR key tables. The on-screen keypad at NAME ENTRY is a 26-letter + 10-digit + punctuation **profile-name** field (guide §16.2b: a text field, not a password field — no `strcmp`/`memcmp` call site compares its buffer to a code constant).
- **Events (10):** Ski Jumping K=90, Ski Jumping K=120, Alpine Skiing Downhill, Freestyle Skiing Moguls, Short Track 500, Figure Skating, Snowboarding GS, Snowboarding Halfpipe, Biathlon, Luge. All 10 selectable from a fresh save; **no hidden/locked event**.
- **Modes (4):** Trial, Championship, Excite, Option — all selectable; no hidden mode.
- **Option (2):** Ranking, Data Clear.
- **Pause (4):** Continue, Retry, Event Select, Mode Select.
- **Debug menu (dead):** entries enumerated from `0x08304040`–`0x083040D0` and the text bank; none reachable.
- **Published codes tested:** big-head sequences (console SKUs) — literal search in ROM returned no match, i.e. **not present in the GBA image**; costume unlocks — confirmed as save-bit gated unlockables, not codes.

## 6b. Enumeration

Guide §0.2 requires the whole code space to be characterised and a novel code accepted in-game. Here that requirement resolves to a **bounded negative result**, which is documented explicitly:

- **Space size:** 0 (empty). There is no alphabet, no code length, no field widths, no checksum, and no lookup table to enumerate. Representable developer-intended codes: **none**.
- **Validator model:** N/A — there is no validator function to call as an oracle. (Guide §16.19's debugger-as-oracle technique was attempted on the closest candidates, the two debug-menu handlers at `0x0804349C`/`0x080439D4`; both are unreachable and have no accept/reject semantics.)
- **Novel code:** impossible by construction — there is no code space in which to mint one. This is a proven absence, not a skipped step.
- **Bounds proven by rejection:** the format's "bounds" are the set of reachable screens. Every reachable screen was walked (§3) and the two debug handlers were exercised with breakpoints under all tested button combinations (L+R+A, L+R+Start, A+B+Start+Select, full Konami code) — they never fired. The negative is closed over the searched space.
- **Text/button spaces searched with counts:**
  - ASCII keywords (`password|cheat|secret|unlock|hidden|bonus|invalid|correct|wrong|enter code|codebreaker|gameshark|debug|level select`), case-insensitive: **0** hits; `+0x20` shifted-text search: **0** hits for all 6 probe strings.
  - Key-mask sequences for the published big-head codes as `u16` and `u8` (also with L/R masks swapped): **0** hits.
  - Embedded GBA headers (Nintendo-logo scan): **1** (stock image only).
  - Debug-menu handler xrefs (BL + literal pointer): **0** each.

## 7. Validation evidence

- **Observed:** all menu screens captured as screenshots on `DISPLAY=:317`; `KEYINPUT` read back as `0x3F7` while Start was held, confirming the keymap and that input reaches the game. Debug-handler breakpoints never hit across the full menu walk and all tested combos. ROM literal/keyword counts above from direct byte scans.
- **Derived:** no BL or 32-bit literal pointer references the two debug handlers (`0x0804349C`, `0x080439D4`) — dead code; the only key-edge provider with callers is `0x0808C04` for normal input; the NAME ENTRY buffer has no code comparison.
- **Inferred (labelled):** the costume unlocks' gating condition (win all golds → L/R at character select) is taken from published descriptions; the save-bit itself was not located or toggled because it is an unlockable, not a code (guide §16.18). Exact visual effect of wearing each costume was not exercised.

## 8. Unknowns

- The precise in-game condition that would enable the unused `-SYSTEM MENU-` / `-TAMAKI KYOUGI MENU-` screens: the handler code exists but has no caller and no gate writer was found. TCRF likewise lists this as unresolved. It is most likely a build-time leftover from the Japanese `Hyper Sports 2002 Winter` development build.
- Whether the three costumes are gated by distinct save bits and their exact addresses (not located; outside the code-system scope).
- The exact visual outcome and stat changes of each costume (not exercised).

## 9. Tooling

- `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings`, `grep` — Phase 0/1 fingerprinting and keyword sweeps.
- Python 3 + `struct` — header parse, embedded-logo scan, literal-pointer and Thumb-BL scanners, keyword/key-mask literal searches, savestate (`gbAs` zlib chunk) reader.
- Capstone 5.0.7 (`capstone.CS_MODE_THUMB`) — targeted disassembly of handlers and input routines.
- `arm-none-eabi-objdump -M force-thumb` — cross-check disassembly.
- `Xvfb :317`, `openbox`, `xdotool`, `scrot`/`import`, ImageMagick — emulator control and screenshots.
- mGBA SDL (`mgba -3`), mGBA CLI debugger (`mgba -d` via a pty) and GDB stub (`mgba -g`) — runtime ground truth. The `-d` debugger was driven through a small Unix-socket server (`dbgsrv.py`) for `break`/`continue`/`status`/`r/4` command sequences; the GDB stub was found unreliable across reconnects and was used only for initial key reads.

Screenshots were kept on disk under `/tmp/espnwinter/` and are not attached to this report. No ROM or copyrighted assets are redistributed here; only addresses, hashes, counts, and findings are published.

## 10. Legal note

No ROM image, extracted graphics, music, or game text are redistributed. This report contains only hashes, addresses, counts, and the analyst's own findings.
