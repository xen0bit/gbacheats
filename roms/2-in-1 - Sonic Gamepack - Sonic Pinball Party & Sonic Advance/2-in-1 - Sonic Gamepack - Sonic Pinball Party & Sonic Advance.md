# 2-in-1 — Sonic Gamepack: Sonic Pinball Party & Sonic Advance (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `2-in-1 - Sonic Gamepack - Sonic Pinball Party & Sonic Advance.gba` |
| Size | 16,777,216 bytes (16 MiB) |
| MD5 | `e0f566030c5ad91a20210476cd521d4e` |
| SHA-1 | `92f137372ec92e23c8dd190d761461653b80ea41` |
| SHA-256 | `ec51663053a8b8df120685ccc9f1c9fd8e9a0db9a1ec95b5fdeb46e52b51284e` |
| Shell header | title `2IN1_ADV_PIN`, code `BW5E`, maker `8P`, version `0`, entry `EA00002E` |
| Pinball header | title `SONICPINBALL`, code `A3VE`, maker `8P`, version `0`, entry `EA00002E` |
| Advance header | title `SONICADVANCE`, code `ASOE`, maker `8P`, version `1`, entry `EA00002E` |
| Header integrity | complement byte stored `0x3C/0x3C/0x32`; computed `0x38/0x38/0x2E`; header checksum `0x0000` for all three |

This is a patched multicart/master image, not three pristine retail headers. All three
headers fail the GBA complement check by 4 and store a zero header checksum; mGBA and
hardware-style loaders boot it anyway. The file utility reports `2IN1_ADV_PIN (BW5E8P, Rev.00)`.

### Embedded GBA images

Scanning the whole 16 MiB for the 156-byte Nintendo logo (`24 FF AE 51 ...`) and reading
the title/code at logo+0x9C/0xAC found three real images plus header copies:

| File offset | ROM address | Title | Code | Size / role |
|---:|---:|---|---|---|
| `0x00000000` | `0x08000000` | `2IN1_ADV_PIN` | `BW5E` | 0x60000-byte shell / boot selector / shared front-end |
| `0x00060000` | `0x08060000` | `SONICPINBALL` | `A3VE` | Sonic Pinball Party, to `0x800000` |
| `0x00800000` | `0x08800000` | `SONICADVANCE` | `ASOE` | Sonic Advance, to end of file |

Header-copy/stub hits (not separate games): `0x74EE14`, `0x7525CC`, `0x779CB0`,
`0x799378` (empty title, maker `01`, inside the Pinball image) and `0x800032C`,
`0xFC01A4`, `0xFC0354` (SONICADVANCE copies inside the Advance image). They have
`EA00002E` entry words but no independent title/code or crt0; they are multiboot/header
copies used by the pack, not playable images.

The shell is linked for `0x08000000`; the two games are linked for `0x08060000` and
`0x08800000`. The shell contains two small launch stubs:

```
0x08000214  mov r0, #0x08800000 ; bx r0     ; Sonic Advance
0x0800021C  ldr r0, =0x08060000 ; bx r0     ; Sonic Pinball Party
```

## 2. Executive summary

The prior triage claim "no in-game cheats" is **disproved**. The image contains a
developer-intended boot selector and a real in-game button code:

1. **Boot selector.** The shell splash shows both game logos and a `PRESS START` prompt.
   Hold **Down** from power-on (before the shell splash) through the `PRESS START` prompt,
   then press Start: the shell boots **Sonic Pinball Party**. With no direction held, or
   with Up/Left/Right, it boots **Sonic Advance**. This is how the second half is reached
   on the original image; no patching is needed. The selection is sampled during shell
   startup, before the splash; pressing Down only after restoring a splash savestate does
   not change it (tested).
2. **Sonic Advance "Tails as Sonic's partner" code.** At the character-select screen with
   Sonic highlighted, enter `Up, Right, Down, Right, L, Right, R, Right, A`. The confirm
   path plays the ring chime (SE `0x6A`, derived) and Tails follows Sonic in normal play
   (observed). This is a real validator, not a name-entry placeholder.
3. **Pinball Party has no in-game password or button code.** Its published "cheats" are
   GameShark/CodeBreaker memory codes and Story-Mode unlockables; the menus contain no
   password/code entry. The only text entry in either half is the Sonic Advance VS player
   name keyboard, which is a name field, not a validator.
4. **No retail debug/level-select menu exists in this Advance image.** The TCRF "debug
   save" is the SRAM-failsafe unlock-all behaviour, not a menu. The only button validator
   found is the Tails code.
5. **Enumeration result for the button system:** the validator is a fixed 9-step
   sequence (1 gated `Up` + 8 table entries). There is exactly one action branch (Tails
   partner). A generated, unpublished variant — holding **Select** throughout the same
   sequence — is accepted and produces the same effect. Wrong inputs are rejected by
   resetting the progress byte to `0xFF`.

## 3. How to reproduce

### Emulator and keymap

mGBA 0.10.5 SDL under Xvfb `:113`:

```bash
Xvfb :113 -screen 0 1024x768x24 &
DISPLAY=:113 openbox &
DISPLAY=:113 SDL_AUDIODRIVER=dummy mgba -3 \
  "roms/2-in-1 - Sonic Gamepack - Sonic Pinball Party & Sonic Advance/2-in-1 - Sonic Gamepack - Sonic Pinball Party & Sonic Advance.gba"
```

Default mGBA SDL keymap used: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
Select=`BackSpace`, D-pad=arrows. Hold keys 100–300 ms.

### Boot selector (original image, no patch)

1. Power on while **holding Down** (hold it from before the splash). The shell's
   selector samples the D-pad during startup.
2. Keep Down held and press Start at `PRESS START` → Pinball Party; release Down once
   the shell advances. (If Down is still held on the language screen it moves the cursor
   to Français; that is just the language menu reacting, and the game choice is already
   latched.)
3. To boot Advance, power on with **no direction** (or hold Up/Left/Right) and press
   Start at `PRESS START`.
4. The shell language screen appears on a fresh save; choose ENGLISH with Up/Down and A.
   It only selects text language and does not choose the game.

Do not press Down only after loading a splash savestate: that state is already past the
selector sample and will boot Advance even with Down held (tested).

### Tails code (Sonic Advance)

1. Boot Advance (no direction + Start), press Start twice to pass the two title screens,
   choose `GAME START`, and reach `SELECT A CHARACTER` with Sonic in the centre.
2. Press, one at a time: `Up, Right, Down, Right, L, Right, R, Right, A`.
   This is a single 9-input sequence; the intermediate Rights move the ring.
3. The confirm path plays SE `0x6A` (the published ring chime); Tails following in the
   level is the observed confirmation. Start Neo Green Hill Zone Act 1 and move right:
   Tails follows Sonic.
4. Do **not** interpret the published wording as "press Up on Sonic, then walk to Tails
   and press Down... and walk back with Left": pressing Left after `R` breaks the table
   and no Tails appears (tested).

### Novel unpublished variant

Hold **Select** from before the first `Up` until after the final `A`, then perform the
same nine inputs. The validator only examines newly pressed keys, so the held Select is
ignored and the code is accepted. This variant appears in no published list.

### Rejection examples

* `Up, Right, Down, Right, R, Right, R, Right, A` (R instead of L at step 4) → no Tails;
  the progress byte is set to `0xFF`.
* `Up, Right, Down, Right, L, Right, R, Right, B` (B instead of the final A) → character
  select is cancelled and the main menu returns.
* `Up, Right, Down, Right, L, Right, R, Right, Right, A` (extra Right; final cursor on
  Tails) → starts as Tails, no partner. The code is specifically Sonic's partner.

## 4. Address map

File offset = ROM address − `0x08000000`.

| Address | Meaning |
|---:|---|
| `0x08000000` | Shell image base (0x60000 bytes) |
| `0x08000214` | Shell launch stub for Advance (`mov r0,#0x08800000; bx r0`) |
| `0x0800021C` | Shell launch stub for Pinball (`ldr r0,=0x08060000; bx r0`) |
| `0x08060000` | Sonic Pinball Party image base |
| `0x08800000` | Sonic Advance image base |
| `0x0885A274` | Sonic Advance character-select update function |
| `0x0885A3B0` | `bl` to the button validator from character select |
| `0x0885B9F8` | **Tails-code validator** (Thumb) |
| `0x0885ABB8` | A-confirm / level-start function (selected character, object callbacks) |
| `0x0885BA6C` | B/cancel transition: clears object timer and installs callback `0x0885AE15` |
| `0x0885AE15` | Character-select cancel/transition state |
| `0x08E885E0` | **Expected-key table** (8 × u16 + terminator); file `0x6885E0` |
| `0x03001F80` | Pointer to the current character-select/player object |
| object base + `0x39` | Progress byte (in the tested run base `0x030026E4` → `0x0300271D`) |
| `0x0300236C` | Newly-pressed key state (u16, active-high) read by the validator |
| `0x030055B0` | Shared shell input struct: `+4` held, `+6` new-pressed, `+8` repeat |
| `0x03004C50` | Mode/state byte tested by the confirm path |

The Tails-code validator was confirmed dynamically: a GDB watchpoint on `0x0300271D`
stopped every increment `0→1→2→...→8` at PC `0x0885BA66` (the `strb` at the end of the
validator). The sequence table is at `0x08E885E0`; the table bytes are verified in §6.

## 5. Algorithm

Reimplementation of the Rust/Thumb validator (`0x0885B9F8`):

```
keys   = *(u16*)0x0300236C       # newly pressed this frame, active-high
obj    = *(u32*)0x03001F80       # character-select object pointer
base   = 0x03000000 + *(u16*)(obj + 6)
prog   = *(u8*)(base + 0x39)

char   = (*(u16*)(base + 0x28) >> 8) & 3

if (keys & 0x40) and char == 0:   # Up on Sonic only
    *(u8*)(base + 0x39) = 0
    return

if keys == 0 or prog == 0xFF:
    return

expected = TABLE[prog]            # TABLE at 0x08E885E0
if keys & expected:
    *(u8*)(base + 0x39) = prog + 1
else:
    *(u8*)(base + 0x39) = 0xFF
```

`TABLE` (u16 little-endian):

| index | mask | button |
|---:|---:|---|
| 0 | `0x0010` | Right |
| 1 | `0x0080` | Down |
| 2 | `0x0010` | Right |
| 3 | `0x0200` | L |
| 4 | `0x0010` | Right |
| 5 | `0x0100` | R |
| 6 | `0x0010` | Right |
| 7 | `0x0001` | A |
| 8 | `0x0000` | terminator |

The initial `Up` is not in the table; it is the special reset on character index 0.
When `prog` reaches 8 and A is pressed, the character-select A-confirm path at
`0x0885A40C` plays SE `0x6A` and, when `[0x03004C50] <= 1`, calls `0x0885ABB8`, which
starts the level with the selected character and sets up the object callbacks. The
B/cancel path at `0x0885A3C6` plays SE `0x6B` and calls `0x0885BA6C`, which clears the
object timer and installs the transition callback `0x0885AE15`.

The validator's only written state is the progress byte at object `+0x39`. The Tails
partner is observed at level start, so either the level-start path consumes that byte or
the selected-character state produced by the completed sequence; the exact read/branch
was not isolated (see §8).

## 6. Tables

### Key masks (GBA, active-high)

| Button | Mask | Button | Mask |
|---|---:|---|---:|
| A | `0x0001` | Right | `0x0010` |
| B | `0x0002` | Left | `0x0020` |
| Select | `0x0004` | Up | `0x0040` |
| Start | `0x0008` | Down | `0x0080` |
| R | `0x0100` | L | `0x0200` |

### Boot-selector actions (observed)

The selector is sampled during shell startup, before the splash. The table records the
direction held from power-on; Down is the explicit second-game selector.

| Held from power-on | Boots |
|---|---|
| Down | Sonic Pinball Party |
| Up | Sonic Advance (default; Up also moves the language cursor if still held on the language screen) |
| Left | Sonic Advance |
| Right | Sonic Advance |
| none | Sonic Advance |
| Select | Sonic Advance (no game-selection effect) |

### Published in-game codes checked

| Source | Code / unlock | ROM evidence | Result |
|---|---|---|---|
| Sonic Retro / GameFAQs / GameRevolution | Sonic Advance Tails partner: `Up,Right,Down,Right,L,Right,R,Right,A` at char select with Sonic | table at `0x08E885E0` matches exactly | **accepted**, Tails follows (screenshots 77, 92) |
| GameFAQs / SuperCheats | Pinball: Bingo after beating Amy; Slots after Tails; Samba de Amigo table after Knuckles | Story Mode bracket has these characters/tables | unlockables, not codes; menu path observed |
| GameFAQs | Pinball Super Sonic stage after Ring Mode in every zone | not a code | unlockable, not tested to completion |
| GameFAQs | Advance Moon Zone after all Emeralds + beat game; Sound Test 40–42 after Moon Zone | Sound Test wraps at 39 (screenshots `143`, `144`) | base range 1–39 confirmed; 40–42 are post-unlock |
| GameShark/CodeBreaker lists | memory-edit codes for both games | out of scope | excluded by brief |

### Menus enumerated

**Shell:** combined splash / `PRESS START`; `LANGUAGE` (日本語, English, Français, Deutsch,
Español; Select prompt; A/Start OK); SEGA logo.

**Sonic Advance:** title (two `PRESS START` screens), main menu (`GAME START`, `VS`,
`TIME ATTACK`, `OPTIONS`, `TINY CHAO GARDEN`), character select (Sonic, Tails, Knuckles,
Amy), Options (`PLAYER DATA`, `LEVEL`, `TIME UP`, `SOUND TEST`, `LANGUAGE`,
`BUTTON CONFIG.`, `DELETE GAME DATA`, `END`), Sound Test (1–39, wraps), pause (`PAUSE`
overlay; no pause menu), VS/Time Attack name entry (3-page A–Z/a–z/0–9/punctuation
keyboard), Tiny Chao Garden.

**Sonic Pinball Party:** title, mode carousel (`ARCADE`, `STORY`, `TUTORIAL`, `PARTY`,
`TINY CHAO GARDEN`, `CASINOPOLIS`, `OPTIONS`), Arcade/Tutorial table select
(Sonic / NiGHTS), gameplay, pause (`CONTINUE`, `SAVE & QUIT`, `QUIT`), Story intro and
`EGG CUP TOURNAMENT` bracket, Party minigame select (Hot Potato / VS), Tiny Chao Garden,
Casinopolis `GAME SELECT` (Roulette), Options (`Button Config`, `Language`,
`Sound Test`, `Chao Navi`), Sound Test (`BGM 001`, `SE 001`, PLAY).

No password, cheat-code, debug-menu, level-select, gallery, or sound-test **code entry**
screen exists in either half. The only text entry is the VS name field.

## 6b. Enumeration

**Space.** The validator has a 1-step character gate plus an 8-entry table. Naive input
space is 10⁹ over the 10 GBA buttons, but the ROM does not interpret arbitrary
sequences: it compares each newly pressed key against a fixed table and resets progress
to `0xFF` on the first mismatch. The table is 8 × u16 at `0x08E885E0` plus the special
`Up`-on-Sonic reset. Therefore the **accepted action set is exactly one**: the 9-input
Tails-partner sequence. There are no alternate action branches, difficulty flags, level
selects, or character unlocks in this validator.

**Novel code (not in any published list).** Hold **Select** before and throughout the
sequence, then enter `Up, Right, Down, Right, L, Right, R, Right, A`. Because the
validator reads only newly pressed keys, the held Select never appears in its key state;
the code is accepted and Tails follows. This exact input is absent from GameFAQs,
Sonic Retro, GameRevolution, TCRF, and the archived combo-pack page. Proof: screenshots
`91_holdsel.png` (level start) and `92_holdsel2.png` (Tails clearly behind Sonic).

**Bounds proven by rejection.**

| Input | Expected table step | Observed result |
|---|---|---|
| `Up,Right,Down,Right,R,Right,R,Right,A` | step 4 wants L (`0x0200`), receives R (`0x0100`) | progress → `0xFF`; no Tails; normal Sonic level (screenshot `90_wrong.png`) |
| `Up,Right,Down,Right,L,Right,R,Right,B` | step 8 wants A (`0x0001`), receives B (`0x0002`) | character select cancelled to main menu (screenshot `138_wrongB.png`) |
| `Up,Right,Down,Right,L,Right,R,Right,Right,A` | cursor ends on Tails | starts as Tails, no partner (screenshot `81_tailsA.png`) |
| `Up,Right,Down,Right,L,Right,R,Left,Left,Left,A` (per-character reading) | table expects Right at step 7; Left is `0x0020` | no Tails (screenshot `76_coded_start.png`) |
| `Up,Right,Down,Right,L,Right,R,Right` without final A | progress stays 7 | no start, no Tails |

**Positive controls.** Published sequence: screenshot `77_altstart.png` (Tails behind
Sonic at Neo Green Hill). Novel held-Select variant: `91_holdsel.png` / `92_holdsel2.png`.
Progress-byte probe (harness, state `ss3`): `0,1,2,3,4,5,6,7` for the eight table inputs,
`8` after the final A, `0xFF` after a wrong step (see §9).

**Pinball Party enumeration (negative result, bounded).** All seven mode cards were
entered, plus Options, all four Options pages, Sound Test, pause, and Story; no code
entry or hidden menu was found. Whole-file ASCII scan: `password` 0, `cheat` 0,
`debug` 0, `secret` 0, `unlock` 0, `sound test` 0, `level select` 0 hits in either
game half. The only `TEST` hits are credits (`TEST TEAM`, `TEST LEAD`, `LEAD TESTER`).
The only alphabetic text-entry surface is the VS name keyboard, which accepts a profile
name and has no published special name.

## 7. Validation evidence

**Observed (emulator screenshots / memory):**

* Boot selector: Down held from power-on → Pinball title (`98_down.png`,
  `103_pin_title.png`, `147_pin_title2.png`); Up held from power-on is **not** a Pinball
  selector — it moves the language cursor to Español (`151_up_early.png`); Left/Right/no
  direction → Advance (`102_left.png`, `101_right.png`, `148_nodir_crop`). A splash
  savestate loaded after the selector sample boots Advance even with Down held
  (`152_down_state.png`).
* Tails code: character select → level with Tails behind Sonic (`77_altstart.png`).
  A simple `A` start without the code shows no Tails (`73_clean_start.png`, `60_normal.png`).
* Novel held-Select variant: Tails follows (`91_holdsel.png`, `92_holdsel2.png`).
* Rejections: `90_wrong.png` (wrong step 4), `138_wrongB.png` (wrong final B),
  `81_tailsA.png` (final character Tails).
* Sound Test range: 1–39, wraps (`143_st39_exact.png`, `144_stwrap.png`).
* Menus: screenshots `01`–`142` in `/tmp/opencode/sonic/shots/`; key ones are
  `11_menu`, `12_options`, `13_soundtest`, `43_pin_menu`, `45_pin_options`,
  `48_pin_opt`, `49_pin_sound`, `104_pin_menu`, `107_arcade`, `114_story`,
  `116_story2`, `121_tutorial`, `122_party`, `123_chao`, `124_casino`,
  `130_vs`, `135_advchao`, `136_advpause`.

**Derived (instruction sequence):**

* Validator at `0x0885B9F8` reads `0x0300236C`, uses table `0x08E885E0`, gates `Up` on
  character 0, and writes progress at object `+0x39`; confirmed by GDB watchpoint PC
  `0x0885BA66` for values 0→8.
* A-confirm path at `0x0885A40C` plays SE `0x6A` and calls `0x0885ABB8` (level start);
  B/cancel path at `0x0885A3C6` plays SE `0x6B` and calls `0x0885BA6C` (installs
  callback `0x0885AE15`).
* Table bytes: `10 00 80 00 10 00 00 02 10 00 00 01 10 00 01 00 00 00`.

**Inferred:**

* The exact persistent "partner" global is set during the `0x0885AE15` transition and
  consumed by level init; the effect is observed but the single stored bit was not
  isolated.
* The SRAM-failsafe "unlock everything" behaviour (documented by TCRF/Sonic Retro) was
  not independently reproduced; it is a save-hardware condition, not a button code.

## 8. Unknowns

* Exact address of the persistent Tails-partner flag and the read of the validator's
  progress byte at level start (effect observed; handoff through the A-confirm/level-start
  path is derived).
* Exact instruction and sampling window in the shell that tests Down versus the default
  for the boot selector (behaviour fully enumerated; the launch stubs are identified, the
  key test is not).
* Whether the held-Select variant has any second-order effect beyond ignoring the held
  button; none was observed in the level.
* Full completion of Moon Zone / Sound Test 40–42 and the Pinball Story-Mode unlockables
  (these require lengthy play, not code entry).

## 9. Tooling

* `mGBA 0.10.5` SDL, `Xvfb :113`, `openbox`, `xdotool`, `scrot`, ImageMagick.
* `gdb-multiarch` against `mgba -g` (GDB stub) for the write watchpoint on
  `0x0300271D`; log `gdbrun.log` shows the 0→8 increments at `0x0885BA66`.
* Custom `libmgba` harness (`/tmp/opencode/sonic/harness.c`) for deterministic
  savestate loads, key injection, RAM dumps, and per-frame progress-byte probes.
  Compile: `gcc -O2 -o harness harness.c -lmgba -lm` (`libmgba-dev` installed).
* `findwrite.c` (mGBA debugger API) was built during the investigation; the GDB stub
  path was used for the final watchpoint because the custom debugger factory is not
  exported by the packaged library.
* Scripts: `scan_headers.py`, `find_keyseq.py`, `find_masktable.py`,
  `probe_progress.sh`, `boottest.py`, `ctl.py`.
* Savestates used: `.ss3` (Sonic Advance character select), `.ss5` (Pinball mode
  select), and `.ss6` (shell `PRESS START`) for selector timing tests. Both are generated
  artifacts, not redistributed assets.
* An early access copy `/tmp/opencode/sonic/pinball.gba` (entry word patched to
  `EA017FFE`, a direct ARM branch to `0x08060000`) was used to inspect Pinball before the
  Down boot selector was found. All evidence in this report uses the unmodified original
  image and the Down selector.

## 10. Legal note

No ROM, extracted graphics, music, or game text is redistributed in this report. Only
hashes, addresses, instruction-level findings, our own screenshots, and reproduction
steps are included.
