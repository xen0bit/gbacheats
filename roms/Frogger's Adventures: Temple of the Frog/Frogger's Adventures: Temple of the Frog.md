# Frogger's Adventures: Temple of the Frog (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Frogger's Adventures: Temple of the Frog.gba` |
| Size | 4,194,304 bytes (0x400000) |
| Header title | `FROG: TEMPLE` |
| Game code / maker | `AFRE` / `A4` (Konami) |
| Version | 0x00 (Rev.00), USA region |
| Internal string | `Konami Computer Entertainment`, `Konami Software Shanghai` |
| MD5 | `228cbf6936579b32b8cc6d7b092dad9c` |
| SHA-1 | `7b4c27009198df18555e63fb5dcad223eaf09815` |
| SHA-256 | `2dac7cdf9821c7ef672b5700f0114cf8bbe46bd019f85b97478e4c9a937637c5` |
| CRC32 | `2EB9EEE6` (matches published USA serial `AGB-AFRE-USA`) |

**Phase 0 result:** single embedded GBA header (156-byte Nintendo logo found once at file offset 0x04); stock entry word `0xEA00002E` (branch to 0x080000C0); fixed byte 0xB2 = `0x96`. CRC32 and SHA-1 match the published GameHacking.org / decomp-repo retail image. **No scene cracktro, no appended trainer, no second game image.** Header checksum bytes `0000` and complement byte `0x6F` are as-shipped for this revision (the image is byte-identical to the verified decomp baserom).

## 2. Executive summary

The game contains **one developer-intended button code**, a 12-press variant of the Konami Code entered on the **"Press Start" title screen**:

> **↑ ↑ ↓ ↓ ← → ← → B A B A**, then **START**

On success the game plays sound 13 and sets `gGameStuff._unk10` bit 0 (IWRAM `0x03005340`) to `1`. That bit is consumed by at least seven gameplay routines (`0x080094F8`, `0x0802BDBC`, `0x0802BC24`, `0x0802BF58`, `0x0800336C`, `0x08003668`, `0x0801E28C` family) to **skip enemy/hazard collision responses — i.e. an invincibility / no-damage cheat**. It stays set through a whole play session (verified in gameplay, mode 8) and is cleared on returning to the title screen (the menu's key-table initializer writes zero to the flag byte).

This code is **not documented for this title** anywhere found: published material for *Temple of the Frog* lists only GameShark/CodeBreaker memory patches (out of scope) plus a gameplay tip (50 coins unlock the final world). The Frogger Wiki's Konami-Code article lists the 10-press version for other Frogger titles, but **not** for this one.

There is **no password system, no level-select cheat code, and no hidden debug menu** in this image. The final-world unlock is a save-bit/coin gate, not a code (§16.18). All reachable screens were walked with RAM evidence; the ASCII text bank and the button/bitmap text paths were examined (details in §6 and §7).

## 3. How to reproduce

- Emulator: mGBA 0.10.5 under Xvfb, `SDL_AUDIODRIVER=dummy`, `-3` scale, started with `-d` (CLI debugger) or plain.
- Keymap (mGBA SDL default): A=`x`, B=`z`, L=`a`, R=`s`, START=`Return`, SELECT=`BackSpace`, D-pad=arrow keys.
- Reach the title screen ("Press Start"). This is game mode 4 with router sub-state 6 — **not** the attract/demo (mode 24) and not the NEW GAME/CONTINUE/OPTIONS menu.
- Press, with a short release between each (hold ≈70 ms, gap ≈40 ms):
  `Up Up Down Down Left Right Left Right B A B A`
- Then press `START`. Read IWRAM byte `0x03005340`: it changes `0x00 → 0x01`. The history buffer `0x03003610[0..11]` reads `01 01 02 02 04 08 04 08 20 10 20 10` before START and the SUCCESS sound plays.
- Continue through language select → main menu → NEW GAME → save slot → intro dialogue → gameplay. The flag remains `1` in gameplay (mode 8, scene 1).
- A mGBA savestate at the title screen makes repeats cheap: `Shift+F2` saves, `F2` reloads. RAM was read by decompressing the `gbAs` PNG chunk of `.ss1` states (stable IWRAM offset `0x19000` for this 4 MiB ROM).

### Published-code verification (all out-of-scope / rejected as in-game codes)
All web-published "codes" for this title are GameShark/CodeBreaker/Action Replay RAM patches: `330035E0 000A` (infinite lives), `33003502 0009` (continues), `330035E4 0005` (elements), `330035E2 0032` (coins), `704DECE5 EBCE`, `8493D33F 6AFA`, `0B1DE1AC CA66`, `FF452FE0 4506`, `53853F64FFC7 674A3FD11918` (open all levels), etc. None is an enterable password/button code; none was tested as a memory patch because that is outside the requested scope. No literal from any published list appears in the ROM as an ASCII password string.

## 4. Address map

| ROM / file address | Meaning |
|---|---|
| `0x080004C4` (`Input_Poll`) | Reads `REG_KEYINPUT`, inverts, computes just-pressed, remaps GBA keys to internal mask (see §6) |
| `0x08017BF8`/`0x08017BFC` (`Menu25_LoadAssets` / `Menu25_HandleInput`) | Title/menu screen loader and input handler; calls the three routines below |
| `0x080193D8` (`Menu25_InitKeyTable`) | Writes the 12-byte target sequence to `0x030053A0`; clears flag `0x03005340`, progress `0x03005350`, arms byte `0x03005348` |
| `0x08019420` (`Menu25_PollInput`) | Records each just-pressed key into the 22-byte history at `0x03003610`; 180-frame (3 s) inactivity reset; progress cap 14 |
| `0x08019984` (`FrogSelect_ValidateSelection`) | The validator: compares `history[0..11]` to `keytable[0..11]`; on match sets `0x03005340 = 1`, plays sound 13 |
| `0x0830806C` | Router handler table; index 6 = `0x08017DB8` (`Menu25_HandleInput`) — the **only** caller of PollInput/ValidateSelection/InitKeyTable |
| `0x081BDF70`–`0x081BE0B4` | ASCII text bank (localized level names, "LEVEL CLEARED"/"YOU WIN"/"YOU LOSE"/"TIME"/"Yes"/"No", credits, region labels) |
| `0x0801AB44` (`LevelSelect_Enter`), `0x0801B154` (`GetHighestUnlockedWorld`) | Read `gGameStuff.unlockedWorlds` (`0x0300533C`) save bitmap; no code path touches the cheat flag |

RAM (IWRAM):

| Address | Field | Role |
|---|---|---|
| `0x03005339` | `GameStuff.mode` | top-level state (observed: 4,5,6,8,24,27,29) |
| `0x0300533A` | `sceneType` | scene id |
| `0x0300533C` | `unlockedWorlds` | progression bitmap (save-based unlock) |
| `0x03005340` | `_unk10` bit 0 | **cheat flag** (set to 1 by the code) |
| `0x03005348` | state+0x18 bit 2 | sequence "armed" byte |
| `0x03005350` | state+0x20 | key-history progress index |
| `0x03005352` | state+0x22 (u16) | last-input frame tick (3 s timeout) |
| `0x030053A0` | key table | 12 target key masks (+2 zero guard bytes) |
| `0x03003610` | key history | 22-byte ring of recorded just-pressed masks |

## 5. Algorithm

```
Input_Poll():                       # every frame, mode 4
    raw   = ~REG_KEYINPUT
    press = raw & ~prev
    mapped = 0
    if press & START: mapped |= KEY_UP     (0x40)
    if press & UP:    mapped |= KEY_A      (0x01)
    if press & DOWN:  mapped |= KEY_B      (0x02)
    if press & LEFT:  mapped |= KEY_SELECT (0x04)
    if press & RIGHT: mapped |= KEY_START  (0x08)
    if press & A:     mapped |= KEY_RIGHT  (0x10)
    if press & B:     mapped |= KEY_LEFT   (0x20)
    return mapped                          # stored in gIwram_5398

Menu25_PollInput(mapped):
    if now - lastTick > 180: clear history[0..21], progress = 0
    if progress > 14:        clear history[0..21], progress = 0
    if mapped == 0: return
    if mapped == 1 and armed == 0:
        clear history, progress = 0, armed = 1, lastTick = now
    elif progress == 1 and mapped != 1:
        armed = 0
    history[progress] = mapped
    progress += 1

ValidateSelection():                # called only when mapped == START (0x40)
    if keytable[14] != 0: flag = 0; return
    for i in 0..11:
        if history[i] != keytable[i]: flag = 0; play_sound(1); return
    flag = 1                          # 0x03005340 = 1
    play_sound(13)
```

`keytable = [0x01,0x01,0x02,0x02,0x04,0x08,0x04,0x08,0x20,0x10,0x20,0x10]`, i.e. **UP UP DOWN DOWN LEFT RIGHT LEFT RIGHT B A B A** in physical GBA buttons (verified dynamically by the history dump).

## 6. Tables

**Button-code space:** exactly **one** accepted 12-press sequence (the table above). Matcher width = 12 bytes of a 22-byte history; inter-press window = 180 frames (3 s); progress cap = 14 presses. Validation is edge-triggered on START. No checksum, no variable fields, no second format.

**Key-mask remap (Input_Poll):** internal `0x01`=UP, `0x02`=DOWN, `0x04`=LEFT, `0x08`=RIGHT, `0x10`=A, `0x20`=B, `0x40`=START, `0x80`=SELECT (each a GBA physical button after the swap documented at `0x080004C4`).

**Cheat flag readers (effect, Derived from code):** `0x080094F8` skips hazard/hit flag writes for collision types 4,5,6,7,9,10; `0x0802BDBC`, `0x0802BC24`, `0x0802BF58`, `0x0800336C`, `0x08003668`, `0x0801E28C` all early-return or skip damage/knockback when `_unk10 & 1`. Net effect: no damage from enemies/hazards.

**Unlock gate (not a code):** `LevelSelect_Enter` requires `highest_unlocked <= 12/13` derived from `unlockedWorlds` bits; the published "50 coins → final world" tip is a save-data condition, not input.

**Text decoding:** the ASCII bank at `0x081BDF70` was dumped and decoded; it contains the localized level names (Temple of the Frog / Sky City / Sea Town / Ancient Ruins / Goblin Caverns in EN/FR/DE/ES/IT), five "CLEARED" banners, `ROUND`, `YOU WIN`, `YOU LOSE`, `TIME`, `Yes`/`No`, `CONTINUE`, and the full credits roll. Menu labels visible on screen (NEW GAME / CONTINUE / OPTIONS / PAUSED / QUIT / ENGLISH…ITALIANO) and the Lumpy dialogue are **not** ASCII anywhere in the 4 MiB — they are baked font/tile-indexed art drawn by the screen installers (consistent with guide §11). Every such screen was nonetheless visited and captured with RAM state, so the negative ("no hidden text/code prompt") is bounded by screen enumeration, not by a failed `strings` search.

## 6b. Enumeration

- **Space defined:** accepted set = 1 of 2^96 possible 12-byte histories (practically: one 12-press sequence × one trigger key). Entry surface = 1 screen (router sub-state 6). Timeout and progress cap fully characterised.
- **Novel / unpublished code:** `↑ ↑ ↓ ↓ ← → ← → B A B A` + START. Verified not listed for this title on GameFAQs-style sites, CheatZILLA, CodeTwink, Neoseeker, GameHacking.org, Ethereal Games, or the Frogger Wiki; the only published input code in the franchise's Konami-Code article is the 10-press version for *other* games. Entered in mGBA; RAM proof: history `01 01 02 02 04 08 04 08 20 10 20 10`, flag `0x03005340 = 1` (screenshot `w_konami2_c.png`, retained in work dir).
- **Bounds proven by rejection** (each from a clean title checkpoint, flag read after START):

| Input | history after presses | flag |
|---|---|---|
| Full 12-press code | `01 01 02 02 04 08 04 08 20 10 20 10` | **1** |
| Classic 10-press Konami (omit final B A) | `01 01 02 02 04 08 04 08 20 10 00 00` | 0 |
| 12 presses, 11th changed (UP instead of B) | `01 10 00 …` (sequence reset by early UP) | 0 |
| 12 presses, 12th changed (UP instead of A) | `01 00 …` (sequence reset) | 0 |
| 11 presses (drop last A) | `01 01 02 02 04 08 04 08 20 10 20 00` | 0 |
| Correct 12 presses with a 4 s pause mid-way | cleared to zeros (timeout) | 0 |

  The 3-second window and the "extra UP resets the matcher" behaviour are therefore observed, not inferred.
- **Screen/prompt space searched:** all reachable modes observed: 4 (title + NEW GAME/CONTINUE/OPTIONS menu), 5 (save select + name entry), 6, 8 (gameplay), 24 (attract), 27 (language/menu transition), 29 (intro dialogue); plus pause overlay, pause→QUIT→YES/NO confirm, level-clear/game-over banners from the extracted text bank. No password entry screen, no debug menu, no other key-table consumer: BL/xref scan shows `Menu25_PollInput`, `FrogSelect_ValidateSelection` and `Menu25_InitKeyTable` each have exactly **one** caller, and no ROM-resident copy of any other key-mask table was found.

## 7. Validation evidence

- **Observed:** emulator screenshots of every screen listed in §6b; RAM snapshots (`gbAs` savestate decompress) of mode/sub-state, key table, history, progress, and the cheat flag before/after each test; flag = 1 in gameplay.
- **Derived:** the remap, the 12-byte comparison, the 3-second reset, and the flag's damage-skipping readers, all from Thumb disassembly at the addresses in §4 and verified against the observed history bytes.
- **Inferred:** "invincibility" as the player-facing description — the flag clearly bypasses hazard collision flags in code, but a full no-damage playthrough was not timed; the RAM flag plus the code path are the proof.
- **Cross-title check:** this is a distinct ROM (SHA-1 above, code `AFRE`). The Frogger Wiki (fetched as data) attributes the *10-press* Konami code to *Frogger's Adventures 2: The Lost Wand* at its main menu (unlocks Magician's Realm) and to other Frogger SKUs — **nothing is shared with this image**: this title uses a 12-press code at the title screen that sets an invincibility flag. The other Frogger GBA images under concurrent analysis were not inspected here.
- **Fetched pages** contained cheat data only; no prompt-injection payload was encountered. All fetched content was treated as data.

## 8. Unknowns

- The exact visual in-game manifestation of "no damage" was not timed through a full hazard encounter; the effect is established from the flag and its readers (Derived), not from a before/after life-count screenshot.
- `keytable[14]` (0x030053AE) is a guard byte that is zero during normal play; no writer that sets it was identified, so no way to disable the code in-game is known.
- Router sub-states 1,2,3,4,7,9 were not individually observed; the decomp's handler table has entries for them, but they were not reachable from the menu paths walked. No debug screen was found in them by static string/xref search.
- Sound 13 on success is inferred from the `Sound_Play(13)` call; audio was disabled (`SDL_AUDIODRIVER=dummy`) so it was not heard.

## 9. Tooling

- `arm-none-eabi-objdump -M force-thumb` for the validator/input routines; Capstone 5.0.7 available for scans.
- Python 3 + Pillow for savestate `gbAs` zlib chunk parsing and screenshot cropping; `xdotool` for input; `scrot` for captures.
- mGBA 0.10.5 under `Xvfb :317` + `openbox`; RAM read via savestate diffing (guide §16.13) because the GDB stub port 2345 is shared with concurrent sessions.
- Reference only: public WIP decomp `JRickey/frog-adv-temple-decomp` (SHA-1-matched baserom) used to locate named functions; every claim above was re-verified against the actual ROM bytes and emulator RAM.
- Work dir: `/tmp/opencode/frogger3` (scripts `walk.py`, `state.py`, `bounds.py`; screenshots `w_*.png`).

**Legal note:** no ROM bytes or copyrighted assets are reproduced here; only hashes, addresses, algorithms, and original findings are published.
