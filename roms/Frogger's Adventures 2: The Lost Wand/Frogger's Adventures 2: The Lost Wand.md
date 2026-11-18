# Frogger's Adventures 2: The Lost Wand (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Frogger's Adventures 2: The Lost Wand.gba` |
| Size | 8,388,608 bytes (0x800000, 8 MiB) |
| Header title | `FG2 THE LOST` |
| Game code / maker | `AFBE` / `A4` (Konami) |
| Version / complement / checksum | `0x00` / `0xAC` / `0x0000` (zero checksum = rebuilt-header artifact, §16.1) |
| MD5 | `dd3724923c44b2a7230f679ae94474fb` |
| SHA-1 | `817dfca0ba55c94557c456a6c61435b5cf079fab` |
| SHA-256 | `7ea54d461a2f841ab6c110f9683b3d4f4fa62193e74c56dd4339910389f4d80a` |

**Image is a scene release with a MODE7 cracktro, not a clean retail dump.** The entry word is
`0xEA1FF66E` (`b 0x087FD9C0`) instead of the stock `0xEA00002E`. At `0x087FD9C0`
there is a custom ARM loader that sets up IWRAM/EWRAM stacks, runs an LZSS-style bitstream
decompressor over the payload at `0x087FDB60` into EWRAM `0x02000000`, then `bx r0`
with `r0 = 0x02000001`. This displays an animated MODE7 logo and Frogger art
("IS THAT A BANANA IN YOUR POCKET...", "FRIENDS? SURE WE HAVE!") — observed on mGBA.
Three additional embedded GBA headers exist at file `0x765DC4`, `0x795E9C`, `0xCA4E4`,
all with the stock `0xEA00002E` entry and the same title/code (copies inside compressed data).

Stock crt0 is intact at `0x080000C0` (`bx r1` with `r1 = 0x08000235`, Thumb `main`).
Per §16.1, analysis used **a copy** with the first four bytes restored to `2E 00 00 EA`
(`/tmp/opencode/frogger2/clean.gba`). The cracktro is a separate release artifact and
is **not** an in-game cheat; no appended trainer menu was found.

## 2. Executive summary

The game has **one developer-intended button code and no password/code-entry system**.
Entering the Konami sequence **Up, Up, Down, Down, Left, Right, Left, Right, B, A** on the
**title screen** sets an unlock flag; pressing **R** on the four-option main menu then opens a
hidden **"MAGICIAN'S REALM"** level-select screen with three timed entries ("MAGICAL MIXUP").
This matches the published GameRevolution/GameFAQs-family code; it was verified in the ROM,
re-entered in the emulator, and confirmed by RAM diff.

The implementation is a single fixed 10-mask lookup table at `0x082B13B4` (u16 active-high
key masks, `0x0000` terminator) compared by an exact-equality sequential validator at
`0x0800F896`. There is no checksum, no variable field, no generator, and no second code
table reachable from code. Button substitutes, deleted presses, a reversed sequence and a
wrong final button are all rejected; inputs appended *after* completion are tolerated as
aliases, which yields an unpublished 11-press spelling that was accepted and RAM-verified.

All reachable screens were walked with screenshots and savestate/RAM checks. No option
screen, password prompt, level-select cheat, or hidden debug menu exists. The CodeBreaker /
GameShark codes published for this SKU are external memory-edit cheats and are out of scope.

## 3. How to reproduce

Emulator: mGBA 0.10.5 (SDL) under `Xvfb :316` with `SDL_AUDIODRIVER=dummy`, 3× scale.
Keymap (mGBA SDL defaults): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`,
D-pad = arrow keys. Hold each key ~150–200 ms (short taps are missed).

1. Boot `clean.gba` (stock entry) — or boot the original and sit through the MODE7 cracktro.
2. Region select: **A** (US flag).
3. Skip the intro: **A ×6**.
4. At the title screen ("Frogger's Adventures 2 — The Lost Wand") press:
   **↑ ↑ ↓ ↓ ← → ← → B A** (≈200 ms per press).
5. Press **A** to reach the four-option main menu (story mode / time attack mode /
   single game pak vs / multi game pak vs).
6. Press **R** → the **MAGICIAN'S REALM** screen appears, listing three best times.
7. Control: press **R** at the menu *without* step 4 and nothing happens (verified).

Screenshots of each state are in `/tmp/opencode/frogger2/` (`title_here.png`,
`postcode_menu2.png`, `after_R2.png`, `nocode_R2.png`, `walk_story_slots.png`,
`vt_extra.png` for the novel code). Screenshots are evidence only; no assets are published.

## 4. Address map

File offset → ROM address = `0x08000000 + offset`.

| Address (ROM) | File | Meaning |
|---|---|---|
| `0x08000000` | `0x000000` | Header; entry patched to `0xEA1FF66E` by MODE7 cracktro |
| `0x080000C0` | `0x0000C0` | Stock ARM crt0 → `0x08000234` (Thumb `main`) |
| `0x0800F896` | `0x00F896` | Button-code validator (sequential exact-mask compare) |
| `0x0800F8C0` | `0x00F8C0` | Literal → `0x082B13B4` (mask table pointer) |
| `0x0800F8C4` | `0x00F8C4` | Literal → `0x02000196` (progress index, byte) |
| `0x0800F8C8` | `0x00F8C8` | Literal → `0x02000197` (code-complete flag, byte) |
| `0x0800F90C` | `0x00F90C` | Literal `0x000003FF` (10-key mask) |
| `0x082B13B4` | `0x2B13B4` | 10 × u16 key masks + `0x0000` terminator |
| `0x087FD9C0` | `0x7FD9C0` | MODE7 cracktro ARM loader |
| `0x087FDB60` | `0x7FDB60` | Cracktro compressed payload source |

RAM (from savestate diffs, §16.13, and the `-d` debugger):

| Address | Meaning |
|---|---|
| `0x0200019B` | Unlock flag: `0x00` → `0x03` when the code completes and R is enabled |
| `0x0200018C`..`0x0200019A` | Menu/state scratch bytes changed with unlock |
| `0x02000196` | Validator progress index (reset to 0 on completion) |
| `0x03006548` | Pointer to input struct (`0x03004F10` observed); struct `+0x82` holds active-high key mask |
| `0x03007550` | Pointer `0x03007560`; byte `[p+1]` also written with `0x03` on completion |

## 5. Algorithm

```
# mask table T = [0x040,0x040,0x080,0x080,0x020,0x010,0x020,0x010,0x002,0x001,0x000]
progress = 0                         # byte at 0x02000196
on each input event:
    held = ~KEYINPUT & 0x3FF         # active-high, struct +0x82, halfword
    if held == 0: return
    expected = T[progress]
    if held != expected:
        progress = 0                 # wrong press resets the whole sequence
        return
    progress += 1
    if T[progress] == 0:             # terminator reached
        progress = 0
        flag |= 3                    # byte 0x0200019B (and mirror byte)
        play_sfx(2)                  # confirmation sound (silent under dummy audio)
```

Derived from the Thumb sequence at `0x0800F896`–`0x0800F92E`: literal table pointer load,
`ldrh` of the expected mask, `ands r4, r0` with `0x03FF`, `cmp r4, expected` / `bne` reset,
progress increment, terminator test, `orr #3` / `strb` flag write, `bl 0x08005618` (sound).
A later gate at `0x0800F932`–`0x0800F960` tests the button state and `flag & 1`, then calls
`0x080058DC` / `0x080027C4` to switch to the hidden level list. The exact key-state bit
assignment in that gate was not fully resolved statically (see Unknowns); the observed
R-at-menu behaviour is the ground truth.

## 6. Tables

**Key masks** (GBA KEYINPUT convention, active-high `~KEYINPUT & 0x3FF`):
`A=0x001, B=0x002, Select=0x004, Start=0x008, Right=0x010, Left=0x020,
Up=0x040, Down=0x080, R=0x100, L=0x200`.

**Code table at `0x082B13B4`** (u16 little-endian):

| Index | Value | Button |
|---:|---:|---|
| 0 | 0x040 | Up |
| 1 | 0x040 | Up |
| 2 | 0x080 | Down |
| 3 | 0x080 | Down |
| 4 | 0x020 | Left |
| 5 | 0x010 | Right |
| 6 | 0x020 | Left |
| 7 | 0x010 | Right |
| 8 | 0x002 | B |
| 9 | 0x001 | A |
| 10 | 0x000 | terminator |

Bytes at file `0x2B13B4`: `40 00 40 00 80 00 80 00 20 00 10 00 20 00 10 00 02 00 01 00 00 00`.

**Published codes checked:** GameRevolution, VictoryCheats, Cheat Happens, AbsoluteCheats,
GameGenie.com and the Frogger Wiki all give the same 10-button sequence; all verified against
the table above and re-entered successfully. The CodeBreaker/GameShark entries
(`90AB05BA 8B66...`, `830036AC 6300`, `820036AC 0013`) are external memory cheats, explicitly
excluded from scope. No password strings were published or found.

## 6b. Enumeration

**Space definition.** The system is one fixed-length button sequence, not a parametrised
password: alphabet = 10 key masks, length = 10 presses, no checksum, no variable fields,
no reserved bits. The table has exactly one terminator, so the accepted base set has
**size 1**. A full ROM scan for u16 single-key-mask runs terminated by `0x0000` found one
code-like table in the game image (`0x082B13B4`); two other pointer-referenced hits
(`0x0826D7B4` = `0x80,0x40,0x20,0x10,0x08,0x04`, `0x080A0D00` = `0x100,0x100,0x01,...`)
are bitfield/graphics data in non-validator code, not button codes. No password alphabet,
keyboard table, checksum routine, or generator exists.

**Novel unpublished code (accepted).** `↑ ↑ ↓ ↓ ← → ← → B A ↑` — the published sequence
plus a trailing Up (11 presses) — is accepted by the game and opens MAGICIAN'S REALM
(screenshot `vt_extra.png`; OCR reads "MAGHAL MIX UP"). `... B A Start` is likewise accepted
(`vt_trailSTART.png`). These are alias spellings: once the terminator is reached the flag is
latched and extra non-navigating presses are ignored. RAM proof for the 11-press spelling
(clean savestate at main menu, vs. no-code control): `0x0200019B` `0x00 → 0x03`, plus
`0x02000192 0x15→0x82`, `0x02000193 0x00→0x01`, `0x0200018C`-area state bytes.
This input appears in no published list.

**Bounds proven by rejection** (fresh-boot visual oracle: R at menu must show the realm):

| Input | Result |
|---|---|
| `↑↑↓↓←→←→BA` (published) | accepted |
| `↑↑↓↓←→←→BA↑` (novel alias) | accepted |
| `↑↑↓↓←→←→BAStart` (novel alias) | accepted |
| `A B R L R L D D U U` (reversed) | rejected |
| `↑↑↓↓←→←→A` (9 presses, no B) | rejected |
| `↑↑↓↓←→←→BStart` (wrong last button) | rejected |
| `↑↑↓↓ L-button → L-button → B A` (Left substituted) | rejected |
| `↑↑↓↓← R-button ← R-button B A` (Right substituted) | rejected |
| `↑↑↓↓←→←→B` (truncated) | rejected |
| `↑↑↓↓←→←→BA B` (trailing B) | rejected (B navigates away) |
| Code entered on the four-option menu instead of title | rejected |
| R at menu with no code entered | no effect (verified) |

Rejection is exact: the validator compares the full masked key state, so extra *simultaneous*
buttons or a wrong button reset progress to zero. The trailing-input aliases are the only
accepted variation, and they are ignored post-completion rather than matched by the table.

## 7. Validation evidence

- **Observed (emulator, :316):** region select, intro, title, four-option main menu, save-slot
  screen (initially three "empty" slots; later "continue / new game"), world/level select
  ("JUNGLE ISLAND / jungle river"), in-game dialogue and HUD, dialogue with the wizard,
  MAGICIAN'S REALM screen with three times (7:31'11", 9:46'37", 11:52'09"). R opens the realm
  only after the code; R does nothing beforehand.
- **Observed (RAM):** controlled savestate diff at the main menu, no-code vs. code: only three
  EWRAM bytes changed (`0x02000192 0x15→0xC7`, `0x02000193 0x00→0x01`,
  `0x0200019B 0x00→0x03`); IWRAM audio-state differences are the confirmation SFX. The novel
  11-press spelling produced the same `0x0200019B = 0x03` flag.
- **Derived (static):** table bytes and validator control flow at `0x0800F896`–`0x0800F92E`;
  a Thumb breakpoint at `0x0800F896` was observed to hit during code entry (`lr = 0x0800CCBD`).
- **Inferred:** the precise button-bit semantics of the R gate at `0x0800F932` (the `0x08`/
  `0x01` tests) were not mapped register-by-register; the visible R behaviour is the anchor.
- **Negative results bounded:** all reachable screens enumerated by screenshots; text search
  across ASCII, lower-case, `+0x20`, UTF-16LE/BE and reversed encodings returned **0** hits
  for PASSWORD, PASS CODE, SECRET, UNLOCK, DEBUG, LEVEL SELECT, CHEAT, OPTIONS, CODE,
  MAGICIAN and REALM (BONUS/ENTER/WAND/SHARD hits are lowercase dialogue lines at `0x73xxxx`).
  In-game dialogue is plain ASCII with `{n}`/`{w}` markup; menu labels are baked into
  background tile art, so no separate text bank exists for them. No password screen, debug
  menu, or unlockable list beyond Magician's Realm was found.
- **Independence from the concurrent title:** `Frogger Advance: The Great Quest` has header
  code `AFQE`, title `FROGQST`, and does not contain the `AFBE` string or the Konami table
  byte sequence. Nothing is shared; each image was verified independently.

## 8. Unknowns

- The R-gate's internal key-mask constants at `0x0800F93A`/`0x0800F94A` were not mapped to
  physical buttons instruction-by-instruction (the emulator confirms R is the trigger).
- The three Magician's Realm entries were displayed but not played through to completion;
  whether beating them changes the stored best times was not exhaustively tested.
- Pause screen was entered but captured mid-fade-to-black; a settled pause screenshot was not
  obtained. No cheat-related control was observed there.
- The confirmation sound could not be heard (`SDL_AUDIODRIVER=dummy`); its presence is
  inferred from the SFX call at `0x0800F92E` and IWRAM audio-state changes.

## 9. Tooling

- `arm-none-eabi-objdump -M force-thumb` / `force-arm` for validator and crt0 disassembly.
- Python 3 + `capstone` 5.0.7 available; searches used `python3` byte/pattern scans.
- mGBA 0.10.5 SDL with `-3`, `-g` (one-shot GDB stub) and `-d` (pty CLI debugger).
- `Xvfb :316`, `openbox`, `xdotool` (XTEST keys), `scrot`, ImageMagick `convert`,
  `tesseract` (OCR-based screen-state oracle).
- Savestate analysis: PNG `gbAs` chunk → `zlib.decompress` → 397,312-byte state;
  EWRAM at `0x21000`, IWRAM at `0x19000` (§16.13). Scripts in
  `/tmp/opencode/frogger2/` (`ss.py`, `vtest.py`, `ram_novel.py`, `scan_codes.py`, etc.).

**Legal note:** no ROM data, graphics, music or full game text is reproduced here; only
hashes, addresses, algorithms and the author-generated button sequence are published.
