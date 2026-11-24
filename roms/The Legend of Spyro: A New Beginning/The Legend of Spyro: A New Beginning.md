# The Legend of Spyro: A New Beginning (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `The Legend of Spyro: A New Beginning.gba` |
| Size | 16,777,216 bytes (`0x01000000`) |
| Header title | `TLOS:ANB` |
| Game code / maker | `B3YE` / `7D` (USA, Rev 00) |
| Entry word | `0xEA00002E` → stock crt0 at `0x080000C0` (no cracktro/trainer) |
| Header version / fixed byte | `0x00` / `0x96` at `0xB2`; checksum word `0x0000` (rebuilt header artifact) |
| MD5 | `15fb7bb864e9876537890af774b43dbf` |
| SHA-1 | `f5ea1de26e8e7e342b9d579adb427934b2ec22a4` |
| SHA-256 | `0bc0197b4db95dbd39c8a04001558f53a7509f7871b549849919865a8092eae8` |
| Logo scan | Exactly **1** Nintendo logo / GBA header in the whole image (not a multi-game pack) |
| Build marker in text bank | `Build: 041220-002p` and `E3-demo` (English at file `0xCD580C` / `0xCDE3F4`; also in DE/NL/FR banks) — this image is an E3-demo build, so debug leftovers are expected |

## 2. Executive summary

**No in-game code system exists in this image.** There is no password screen, no
code-entry widget, no button-code matcher, and no cheat/unlock key sequence on
any reachable screen. Every input path in the ROM goes through one shared
input library: the **only** literal for `KEYINPUT` (`0x04000130`) is at
`0x08069120`, inside a 6 KiB library (`0x08068E40`–`0x08069158`) that exposes
"key pressed", "key held" and "held-duration" helpers. No game-side code
compares a stored button sequence.

The ROM does contain **developer-intended debug content**: a string-ID map with
`MENU_LEVEL_SELECT`, `LEVEL_TEST`, `FS_TEST`, `SPYRO_CAMEO_TEST1..11`, a
`rooms\test_room` asset and a level-name list (`Swamp1..6`, `Plains1..6`,
`TEST`, `LEVEL SELECT`). The menu entry **"LEVEL SELECT" is present in the
text bank and in a menu-ID list but is never drawn or reachable** from any of
the screens walked (see §8). This is a *gated* debug artifact, not a usable
cheat; the gate was not identified from reachable input, so it is reported as
an unknown rather than as a confirmed feature.

The only developer-intended state change observed was an **unlockable, not a
code**: saving a game makes `LOAD GAME` appear on the title menu (2 items → 3
items). Mini-games remain locked after one save. Screenshots and RAM evidence
are listed in §7.

## 3. How to reproduce

- Emulator: mGBA 0.10.5 under Xvfb `:316`, `SDL_AUDIODRIVER=dummy`, 3× scale.
- Keymap verified: `x`=A, `z`=B, `a`=L, `s`=R, `Return`=Start, `BackSpace`=Select,
  arrows=D-pad. Holds of 100–150 ms with ~150–400 ms gaps.
- Boot: health-and-safety screen → `x` → legal screen → `x` → Krome Studios →
  `x`×3 → title "Press Start" → `Return` → title menu.
- Menu confirm is **A (`x`)**, not Start; A also advances cutscenes.
- Screen walk (all reached, all screenshotted in `/tmp/spyrolegend/`):
  title, title menu (2 items, then 3 items after a save), OPTIONS
  (Music/Sound/Display/Credits), LOAD GAME (3 slots), in-game gameplay,
  pause menu (CONTINUE/SAVE GAME/EXIT GAME), pause→L "OPTIONS" page
  (Music/Sound), save-confirm dialog, exit-to-menu dialog, intro cutscenes.
- Savestates: `Shift+F1` saves, `F1` loads slot 1. States were saved at the
  title menu (`stateA.ss1` / `stateB.ss1` copied to the work dir).

## 4. Address map

| Address (ROM/file) | Meaning | Evidence |
|---|---|---|
| `0x00000000` / `0x000000C0` | Header / crt0 entry | Observed |
| `0x08069120` (file `0x69120`) | **Only** `KEYINPUT` literal in the entire 16 MiB image | Derived (word scan) |
| `0x080690F0` | Key poll: reads `KEYINPUT`, inverts into held mask at `0x02004822`, increments 10 hold counters | Derived (disasm) |
| `0x08068F10` | Hold-duration accessor (mask → counter), 7 BL callers | Derived (BL scan) |
| `0x08069020` | Key-pressed/held accessor, 152 BL callers | Derived (BL scan) |
| `0x02004820` / `0x02004822` | Previous / current active-high key mask | Derived + savestate RAM read |
| `0x02004830` | `u32 counter[10]` (frames held) used for key-repeat | Derived |
| `0x02002A00` | EWRAM save-shadow struct; bytes `+0x0C` / `+0x14` are the two menu-selection flags (NEW GAME / OPTIONS) | Observed (savestate diff) |
| `0x08CF5C00` | String-ID map: `u16 id; u16 0; char name[32]`, stride `0x24`, IDs `0x0000`–`0x049F` (414 named records) | Derived |
| `0x08CFF7AC` | ID `0x0453` = `MENU_LEVEL_SELECT` | Derived |
| `0x08CFF5D8` | ID `0x0446` = `LEVEL_TEST` | Derived |
| `0x08CE2D2C` | English localized text `LEVEL SELECT`; `TEST` at `0x08CE2C88` | Observed/derived |
| `0x082F4328` | Menu/level text-ID list containing `0x0453` (LEVEL SELECT), `0x0454` (LOAD), `0x0455` (MG_SELECT), `0x0456` (NEW) | Derived |
| `0x0800A954` | 106-entry data selector table (index from `[struct+0xD4]-13`) — not a function/cheat table | Derived |
| `0x08CE2C40`–`0x08CE2E00` | Debug level-name bank (`Swamp1..6`, `Plains1..6`, `TEST`, level select, mini-games) | Observed |

Savestate layout note (mGBA `.ss1` = PNG + zlib `gbAs` chunk, 397,312 B raw):
EWRAM `0x02000000` maps to raw offset `0x21000`; IWRAM to `0x1D000`; VRAM to
`0x1000`. This mapping was used for all RAM reads below.

## 5. Algorithm

Not applicable — no validator, encoder, checksum or comparison table exists.
The only "algorithm" found is the generic input pipeline:

```
KEYINPUT (0x04000130) --ldr at 0x080690F0--> held[+2] = ~KEYINPUT & 0x3FF
    prev[+0] = held[+2];  counter[i] += (held & (1<<i)) != 0,  i = 0..9
    game code --> BL 0x08069020 (pressed/held?) / 0x08068F10 (hold frames?)
```

159 BL references total to those two accessors (7 + 152); none is part of a sequence
matcher (no progress index, no mask table, no length/size check).

## 6. Tables

- **Text IDs** (stride `0x24` at `0x08CF5C00`): debug-relevant IDs
  `0x0416 LEVEL_CUTSCENE`, `0x0446 LEVEL_TEST`, `0x0452 MENU_CREDITS`,
  `0x0453 MENU_LEVEL_SELECT`, `0x0454 MENU_LOAD`, `0x0455 MENU_MG_SELECT`,
  `0x0458 MG_LOCKED`, `0x03EF/0x03F0 FS_TEST_1_1/2_1`,
  `0x0491..0x049B SPYRO_CAMEO_TEST1..11`.
- **Menu selection bytes**: `0x02002A0C` = NEW GAME selected, `0x02002A14` =
  OPTIONS selected (one-hot). Diff on Down: `0x02002A0C 01→00`,
  `0x02002A14 00→01`, `0x02002A58 6A→E8` (save-shadow checksum).
- **Button masks** (active-high, from `~KEYINPUT`): A=1, B=2, Select=4,
  Start=8, Right=0x10, Left=0x20, Up=0x40, Down=0x80, R=0x100, L=0x200.

## 6b. Enumeration

**Space definition:** empty. There is no code/password space to enumerate:

| Checked surface | Space searched | Result |
|---|---|---|
| Password / code-entry screen | All 10 reachable screens (§3) | 0 screens with a text/code field |
| Password-like ASCII strings | 16,777,216 B × 4 encodings (ASCII, `+0x20` up, `+0x20` down, UTF-16LE) | `password` 0, `cheat` 0, `invalid` 0, `debug` 0, `generate` 0, `unlock` 0; `code` 1 (a struct field name at `0x086348`), `secret` 1 (credits job title) |
| Password alphabets/tables | Full image, all 32-bit pointers and 16-bit ID records | No alphabet string, no code table, no generator/decoder pair |
| Button-code table | Full image, u16 and u8 mask sequences, length ≥ 4, mask ∈ 1..0x3FF | No structured sequence table; 106,872 loose u16 candidates and 610 byte runs, all inside code/graphics data with no validator/xref |
| Input entry points | Full image | 1 `KEYINPUT` literal (`0x08069120`); 10 references to key-state base `0x02004820`, all within `0x08068E40`–`0x08069158`; 23 to counter base `0x02004830`, same library |
| Title-screen button codes | 12 sequential sequences (Konami, LRAB, LRStart, ABStart, LLRRAB, UDLRLR, StartAB, LRA, RB, LB, RLUD, LR) + 10 simultaneous-hold combos | 0 changed the menu item set |
| Pause-menu buttons | L, R, L+R, A/B/D-pad | Only documented CONTINUE/SAVE/EXIT + L-options page; no hidden page |
| Validator found | Full image | None — no `strcmp`/length/packed-word/checksum code attached to user input |

**Novel codes:** cannot be generated — there is no encoding to mint. This is a
**bounded negative**, not an untested absence.

**Reachable unlockable (not a code):** first boot title menu = {NEW GAME,
OPTIONS} (`menu0_crop.png`); after saving once = {LOAD GAME, NEW GAME, OPTIONS}
(`menu_saved2_crop.png`). Mini-games remain locked (`MG_LOCKED`, ID `0x0458`).
This state change is caused by the save record at `0x02002A00` and is not
triggered by any button sequence.

**Rejection bounds:** entering arbitrary button combinations at the title and
pause screens produces no state transition other than normal menu navigation —
i.e. the "rejected" space is all tested sequences outside the documented
navigation set (22 sequences/combos), with zero acceptances.

## 7. Validation evidence

- **Observed:** all screenshots above; mGBA boot and screen walk; menu flag diff
  from savestates (`0x02002A0C/14/58`); `.sav` written by the in-game SAVE GAME
  dialog (8192 bytes, first bytes `ff ff ff ff ff ff ff 00 f5 e0 45 d3 …`).
- **Derived:** disassembly of `0x08068E40`–`0x08069158`; literal/BL scans;
  string-ID table layout; text bank contents; single-header logo scan.
- **Inferred:** that `MENU_LEVEL_SELECT` was *intended* as a debug menu (debug
  level names and `LEVEL_TEST` beside it); the gate that would expose it was
  not found and is **unknown**.
- Evidence labels: no claim of an accepted or rejected *code* is made, because
  no code surface exists.

## 8. Unknowns

1. **The `LEVEL SELECT` gate.** The string (ID `0x0453`) and a menu-ID list at
   `0x082F4328` exist, but no reachable input path was found. It may require a
   full clear, a link/transfer event, or a developer-only build flag. The
   writer of that menu-state byte was not isolated; the only observed writes to
   `0x02002A0C` came from a generic memory-copy routine at `0x080005EC`
   (LR `0x0805F5BB`) mirroring save data.
2. Direct pointers to the text-ID base (`0x08CF5C00`) do not occur; lookup is
   via a language-bank descriptor, so a text-ID xref scan is inconclusive for
   dead-code proofs.
3. Web reconnaissance was unavailable in this environment: the search tool
   returned no results for every query, and search/wiki/cheat sites returned
   403 or bot challenges. No published code list could be checked; the
   negative is based solely on local ROM + emulator evidence. (Any instruction
   or "code" text found in fetched pages would be treated as data; none was
   used.)

## 9. Tooling

- `file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings`, `grep`.
- Python 3: header parse, Nintendo-logo multi-header scan, word/literal/BL
  scans, Capstone Thumb disassembly, string-ID table decoder, `.ss1` `gbAs`
  zlib parser and RAM diff, savestate mapping.
- `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`.
- mGBA 0.10.5 (`-3`, `-g`, `-d`), Xvfb `:316`, openbox, xdotool, scrot,
  ImageMagick. mGBA's CLI debugger (`-d`) supports `watch/w`, `bt`, `x/1|2|4`,
  `w/1|2|4`, `trace` and was used to confirm the save-shadow write path.
- Work files/screenshots: `/tmp/spyrolegend/`.
- No ROM or copyrighted assets are redistributed here; only hashes, addresses
  and algorithms are published.
