# Wade Hixton's Counter Punch (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Wade Hixton's Counter Punch/Wade Hixton's Counter Punch.gba` |
| Size | 8,388,608 bytes (`0x800000`) |
| Header title | `WADE HIXTONS` |
| Game code / maker | `BSRE` / `20` (Rev.00) |
| Version / complement / checksum | `0x00` / `0x55` / `0x0000` |
| Entry branch | `0xEA00002E` (stock crt0, no cracktro/trainer) |
| MD5 | `05b82f996a7ebc44c62697b02833a68f` |
| SHA-1 | `11145cfe08b4bf6b51fa47c48ad5289fd322d599` |
| SHA-256 | `98887216a00c5e99a341abcb4a0f7bfc86cb58890c2cbb0b7c0d534c937bbd0b` |

## 2. Executive summary

This title has **two developer-intended in-game features**, both reachable on a retail ROM with no cheat device:

1. **A 3-press button code on the in-match pause screen**: `L, R, Select` opens a two-page **DEBUGMODE** overlay (game state, camera mode/position/delta, player and CPU positions, stun, stamina, punch counts and move status). `L`/`R` flip pages; `Select` and `A` arm post-unpause actions. This is documented by TCRF, but the state machine was recovered in full and several undocumented input sequences were generated and verified in-emulator.
2. **Two hidden developer test entries inside the ordinary OPTIONS menu**: `SOUND TEST` and `MUSIC TEST`, with ranges 0–45 and 0–13 respectively (both wrap). These are reachable and playable from the title screen and are **not documented by TCRF or the published guides** — they are the principal novel finding of this engagement.

There is **no password/code-entry system** in this SKU. The exhaustive search space and bounded negative are recorded in §6b. All CodeBreaker/GameShark/Action Reaper codes published for this game are out of scope and were not used.

## 3. How to reproduce

Emulator: mGBA 0.10.5 SDL under Xvfb `:316`, `SDL_AUDIODRIVER=dummy`, scale 3×.
Keymap (mGBA SDL default): A=`x`, B=`z`, L=`a`, R=`s`, Select=`BackSpace`, Start=`Return`, D-pad=arrow keys. Hold ≈80–120 ms per press.

**Debug mode**
1. Title → `NEW GAME` → choose slot → enter a 3-character name → `Start` → advance the story scenes with `A`.
2. Win/lose/advance into an actual boxing match (opponent Rocco McScrub in the first one).
3. Press `Start` to reach the `GAME PAUSED / RESUME / GIVE UP` screen.
4. Press `L`, `R`, `Select` in order → `DEBUGMODE PG.1`. Press `L` or `R` → `DEBUGMODE PG.2`.
5. In PG.1, `Select` arms "end round after unpause"; `A` arms "lose match after unpause". Unpause with `Start` to fire.

**Hidden sound/music tests**
1. Title → `OPTIONS` (third item).
2. Move to `SOUND TEST` (fourth entry) and press `Left`/`Right`: values `0..45`, wraps `45 → 0`; each change triggers the corresponding sound effect.
3. Move to `MUSIC TEST` (fifth entry) and press `Left`/`Right`: values `0..13`, wraps `13 → 0`; each change starts the corresponding music track.

Evidence screenshots are in `/tmp/opencode/hixton_evidence/` (moved out of the ROM folder per policy).

## 4. Address map

| Address (ROM / file) | Meaning |
|---|---|
| `0x08006400` / `0x06400` | Pause-screen routine (draws `GAME PAUSED`, `RESUME`, `GIVE UP`) |
| `0x0800646c` | `L|R` mask (`0x300`) branch in the pause handler |
| `0x0800657a` | Validator entry: reads progress byte, bounds check `<= 4`, dispatch |
| `0x0800659c` / `0x0659c` | 5-entry jump table: `080065B0`, `080065C0`, `080065E4`, `08006610`, `08006A0C` |
| `0x080065b0` / `0x080065c0` | States 0/1: expect `L` (`0x200`), then `R` (`0x100`) |
| `0x080065e4` | State 2: expect `Select` (`0x004`), plays a confirmation sound via `BL 0x0800B1A4` |
| `0x08006610` | State 3 (PG.1): `L`/`R` → state 4; `Select` → `[+0x10]=1`; `A` → `[+0x0E]=2, [+0x10]=1` |
| `0x08006a0c` | State 4 (PG.2): `L` → `[+0x0B]-1`, `R` → `3`, i.e. both return to PG.1 |
| `0x08006c9a` | Post-handler common exit (game update continuation) — wrong presses do **not** reset progress |
| `0x080222c4` / `0x222c4` | ASCII string `DEBUGMODE PG.1` |
| `0x0802233c` / `0x2233c` | ASCII string `DEBUGMODE PG.2` |
| `0x080222d4`–`0x080223a8` | Field labels: `GAMESTATE`, `CAM MODE`, `CAM POS`, `CAM DELTA`, `PLY POS`, `CPU POS`, `STUN`, `STAMINA`, `PLY PUNCHES`, `CPU PUNCHES`, `MOVE STATUS`, `PLY MOVING` |
| `0x08044e84`–`0x08044f1c` | OPTIONS/title menu label strings incl. `SOUND TEST:`, `MUSIC TEST:` |
| `0x08411790` | Menu label pointer table |
| IWRAM `0x03001164` | `u16` active-high key mask used by the validator (`A=1,B=2,Sel=4,Start=8,R=0x100,L=0x200`) |
| IWRAM `0x03001174` | second key-state word (held/edge) used by the pause menu |
| IWRAM `0x03001180` | master global struct |
| IWRAM `0x03001184` | struct `+0x04`: `SOUND TEST` index, range `0..45`, wraps |
| IWRAM `0x03001185` | struct `+0x05`: `MUSIC TEST` index, range `0..13`, wraps |
| IWRAM `0x0300118b` | struct `+0x0B`: validator progress counter (`0`..`4`) |
| IWRAM `0x0300118e`/`0x03001190` | struct `+0x0E`/`+0x10`: debug action flags |

Savestate layout used for RAM reads (mGBA `gbAs` chunk, decompressed length `397,312`): VRAM at `0x1000`, IWRAM at `0x19000`, EWRAM at `0x21000`. IWRAM `0x03001180` is therefore at state offset `0x1A180`.

## 5. Algorithm

Button-code validator (executed every frame while paused):

```
keys := u16 @ 0x03001164              # active-high: A1 B2 Sel4 Start8 R0x100 L0x200
p    := byte @ 0x0300118B              # progress counter
if p > 4: goto exit
switch p:
  case 0: if keys & 0x200: p++        # L
  case 1: if keys & 0x100: p++        # R
  case 2: if keys & 0x004: p++; play_sound(7,0x80,0x0C)   # Select
  case 3:                              # DEBUGMODE PG.1
      if keys & 0x200: p = 4           # L -> PG.2
      elif keys & 0x100: p++           # R -> PG.2
      elif keys & 0x004: flag10 = 1    # end round after unpause
      elif keys & 0x001: flag0E = 2; flag10 = 1            # lose match after unpause
  case 4:                              # DEBUGMODE PG.2
      if keys & 0x200: p--             # L -> PG.1
      elif keys & 0x100: p = 3         # R -> PG.1
      # Select and A are NOT handled here
exit: continue normal pause update
```

Properties:
* Wrong D-pad presses are silently tolerated (no reset), so interleaved `Up`/`Down`/`Left`/`Right` do not break the code.
* `A`, `B` and `Start` change the pause/menu state and thereby abort the sequence in practice.
* Progress is never reset to zero by a wrong press — it persists until the pause state changes or a correct press advances it.

Sound/music test entries:
```
on Left/Right at SOUND TEST  -> idx = (idx +/- 1) mod 46    # 0..45, start SFX idx
on Left/Right at MUSIC TEST  -> idx = (idx +/- 1) mod 14    # 0..13, start music idx
```

## 6. Tables

* **Button masks (active-high)**: `A=0x001`, `B=0x002`, `Select=0x004`, `Start=0x008`, `Right=0x010`, `Left=0x020`, `Up=0x040`, `Down=0x080`, `R=0x100`, `L=0x200`.
* **Validator dispatch table** (`0x0800659c`, 5 entries, index = progress byte): `0x080065B0`, `0x080065C0`, `0x080065E4`, `0x08006610`, `0x08006A0C`.
* **Debug page values**: `3` = PG.1, `4` = PG.2; `0`,`1`,`2` are the three input stages.
* **Action flags**: `+0x10 = 1` (armed, ends round on unpause), `+0x0E = 2` (lose match).
* **OPTIONS entries (top to bottom)**: SOUND VOLUME, MUSIC VOLUME, HEADPHONES, SOUND TEST, MUSIC TEST, BACK.
* **Test index ranges**: SOUND `0..45` (wrap), MUSIC `0..13` (wrap).

## 6b. Enumeration

**Space definition.** The in-game cheat surface is a 5-state button sequence matcher plus two hidden option indices. There is no alphanumeric password, no alphabet table, no checksum and no code-entry screen. The complete space is:

* *Activation*: one 3-press core sequence `L,R,Select` (masks `0x200,0x100,0x004`), from the in-match pause screen only.
* *States*: exactly 5 (`0..4`), enumerated from the jump table at `0x0800659c`; every branch of every state is listed in §5. There are no other action branches or longer sequences.
* *Tolerated interleaving*: any number of D-pad presses may be inserted between the three required presses without resetting progress (verified for `Up` and `Down`).
* *Hidden test indices*: `46` sound IDs (`0..45`) and `14` music IDs (`0..13`), both cyclic — **60 distinct developer-test values**, all reachable from the title menu without any unlock.

**Validator model.** Reimplemented in §5; agrees with the ROM on accepted and rejected inputs:

| Sequence | Progress byte after | Outcome |
|---|---|---|
| `L,R,Select` | `3` | DEBUGMODE PG.1 (published) |
| `L,L,R,Select` | `3` | DEBUGMODE PG.1 — **novel, undocumented** |
| `L,R,R,Select` | `3` | DEBUGMODE PG.1 — **novel, undocumented** |
| `L,Up,R,Select` / `L,Down,R,Select` | `3` | DEBUGMODE PG.1 — **novel, undocumented** |
| `R,L,Select` | `1` | rejected (wrong order; no overlay) |
| `L,B,R,Select`, `L,A,R,Select`, `L,Start,R,Select` | `1` | rejected (A/B/Start leave pause state) |
| `L,R,B,Select` | `2` | rejected (Select never received) |
| `L,R,Select,L` / `L,R,Select,R` | `4` | DEBUGMODE PG.2 |
| `L,R,Select,L,Sel` | `4` | PG.2; Select has no effect there |
| `L,R,Select,R,A` | `4` | PG.2; `+0x0E=0`, `+0x10=0x4D` — A has **no** effect |

**Novel codes generated and confirmed in-game.**

1. `L, L, R, Select` — an undocumented sequence with an extra `L` inserted at state 0 (state 1 expects `R`, so the extra press is ignored). Entered in mGBA from a fresh pause-screen savestate: `DEBUGMODE PG.1` appeared (`/tmp/opencode/hixton_evidence/debug_pg1_novel_LLRSel.png`) and the progress byte read back as `3`.
2. `L, R, R, Select` — extra `R` tolerated at state 2; progress byte `3`.
3. **OPTIONS → SOUND TEST / MUSIC TEST** — two entirely undocumented developer test entries. Navigated on the real title-menu OPTIONS screen, cycled through both indices, observed sound/music playback and confirmed the backing RAM values at `0x03001184`/`0x03001185` (`/tmp/opencode/hixton_evidence/options_menu.png`, `/tmp/opencode/hixton_evidence/music_test.png`, `/tmp/opencode/hixton_evidence/sound_test_wrap.png`).

**Bounds proven by rejection.**

* Wrong-order `R,L,Select` ends at progress `1` and never draws either overlay; `L,B,R,Select`, `L,A,R,Select`, `L,Start,R,Select` and `L,R,B,Select` end at `1`, `1`, `1`, `2` respectively — all bounded negative results with exact counter values.
* `L,R,Select,R,A` leaves PG.2 flags untouched, proving that the published claim "`A` works at any time in either screen" is false: `A` is dispatched only by the PG.1 handler at `0x08006610`.
* SOUND TEST stops wrapping past `45 → 0` and MUSIC TEST past `13 → 0`; 60 presses were recorded stepping MUSIC TEST and the sequence `5,6,…,13,0,1,…` repeated exactly.
* **No-password bounded negative.** Search spaces checked over all 8 MiB: raw ASCII `strings` (157,738 printable strings ≥4 chars), case-insensitive `+0x20` translated ASCII, UTF-16LE, and explicit alphabets (`ABCDEFGHIJKLMNOPQRSTUVWXYZ`, `0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ`, `BCDFGHJKLMNPQRSTVWXYZ`). `PASSWORD` and `CODE` occur **0** times; `DEBUG` occurs **2** times (the two overlay titles); `TEST` occurs **4** times (two dialogue lines and the two OPTIONS labels). The only user-entry field is a 3-character save name consumed as a label, not compared against a validator. The only code surface is the button validator above. CodeBreaker codes published for this title target raw RAM addresses and are cheat-device codes, explicitly out of scope.

## 7. Validation evidence

**Observed (emulator / savestate RAM reads)**
* `L,R,Select` on the pause screen draws `DEBUGMODE PG.1`; `R` draws `PG.2`; `L` returns to `PG.1` (`/tmp/opencode/hixton_evidence/debug_pg1_public_code.png`, `/tmp/opencode/hixton_evidence/debug_pg2.png`).
* Progress byte at IWRAM `0x0300118B`: `0x00` on the plain pause screen, `0x03` in PG.1, `0x04` in PG.2 — read directly from decompressed mGBA savestates at state offset `0x1A18B`.
* `A` in PG.1 → `+0x0E=0x02`, `+0x10=0x01`; `Select` in PG.1 → `+0x10=0x01`; unpause then shows a lost round/match (`/tmp/opencode/hixton_evidence/pause_screen.png`).
* OPTIONS menu renders all six entries including SOUND TEST and MUSIC TEST; changing them alters RAM `0x03001184`/`0x03001185` and produces audio.
* Screens walked in the emulator: title menu, slot select, name entry, story scenes, bar hub, live match, pause (RESUME/GIVE UP), debug PG.1, debug PG.2, and OPTIONS with both test entries. `CREDITS` and `SLIDESHOW` exist in the menu label table (`0x08411790`) but those two destinations were not entered; they are not code surfaces.

**Derived (disassembly)**
* 5-state validator, exact mask constants, jump table, flag writes and the absence of an A/Select branch in PG.2 — `0x0800657A`–`0x08006A3A`.
* Key input word `0x03001164`, global struct `0x03001180` and option indices `+0x04`/`+0x05`.

**Inferred**
* The exact audio tracks/effects selected by each test index were not catalogued by ear; only index changes and playback were observed.
* Whether the `+0x0E=2` flag is consumed as "lose match" outside the observed round-transition frames was inferred from the code path and the observed KO state.

**Correction to public documentation:** TCRF states `A` works "at any time in either screen". Static dispatch and a RAM-verified test of `L,R,Select,R,A` prove `A` is handled only in PG.1 (`0x08006610`); in PG.2 it is ignored.

## 8. Unknowns

* The mapping of SOUND TEST indices 0–45 and MUSIC TEST indices 0–13 to named assets was not catalogued (no asset extraction was performed; game audio is not redistributed).
* The precise consumer of the `+0x0E`/`+0x10` flags after unpause was not traced beyond the observed round result.
* The `L|R` mask check at `0x0800646C` writes `+0x0D = 1`/`2` in the pause handler; its downstream effect was not isolated (appears to be ordinary pause-menu cursor/confirm logic, not a separate cheat).
 * No battery-save unlockables were exhaustively enumerated; the discovered features are input-reachable from a fresh game.

## 9. Tooling

* `arm-none-eabi-objdump` (raw Thumb disassembly; produced no output for this 8 MiB image), **Capstone 5.0.7** custom disassemblers (`dis2.py`, `dis3.py`) with PC-relative literal annotation, custom BL and literal-pool scanners.
* mGBA 0.10.5 SDL under Xvfb `:316` + openbox, `SDL_AUDIODRIVER=dummy`; `xdotool` XTEST input, `scrot` screenshots, ImageMagick crops.
* Savestate RAM diffing: `zlib.decompress` of the PNG `gbAs` chunk; IWRAM at state offset `0x19000`, EWRAM at `0x21000`.
* Note: this mGBA build has **no GDB stub** (`-g` is accepted but no socket is opened; the binary contains no GDB strings), so savestate diffing was used for all RAM evidence.
* No ROM or copyrighted assets are redistributed; only addresses, hashes, algorithms and our own scripts/screenshots of on-screen state are published.
