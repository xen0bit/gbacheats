# Pokémon LeafGreen (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Pokémon LeafGreen/Pokémon LeafGreen.gba` |
| Size | 16,777,216 bytes (`0x1000000`, 16 MiB) |
| `file(1)` | Game Boy Advance ROM image: "POKEMON LEAF" (BPGE01, Rev.01) |
| Header title / code / maker | `POKEMON LEAF` / `BPGE` / `01` |
| Version byte | `0x01` (Rev.01 = v1.1 English); comp `0x80`, checksum `0x0000` (normal for retail Pokémon) |
| Entry word | `0xEA00007F` → `0x08000204` (stock Pokémon GBA crt0; **no** cracktro/trainer) |
| MD5 | `9d33a02159e018d09073e700e1fd10fd` |
| SHA-1 | `7862c67bdecbe21d1d69ce082ce34327e1c6ed5e` |
| SHA-256 | `2f978f635b9593f6ca26ec42481c53a6b39f6cddd894ad5c062c1419fac58825` |

**Embedded GBA headers** (156-byte Nintendo-logo scan): `0x00000000` main game `BPGE`;
`0x006FF5B8` code `AGBJ`, entry `0xEA00003E` (multiboot Berry-Fix/wireless stub);
`0x007031AC` code `TEST`, entry `0xEA00002E` (multiboot test stub). Neither is a trainer;
both are developer multiboot images shipped inside the cart.

**Identity confirmation:** the `pret/pokefirered` decompiles `make leafgreen_rev1`
to a **byte-identical** ROM (built SHA-1 = `7862c67b…`, same as target). All addresses,
source, dead-code call counts and text banks below are therefore properties of *this exact
image*, not of a sibling revision. FireRed/Emerald were **not** used as evidence.

## 2. Executive summary

1. **One real, reachable in-game button code exists**: at the title screen, **hold B+Select**
   → the hidden **“Berry Program Update”** (Berry Fix / clock-fix) multiboot utility.
   It is developer-intended, works on the retail Rev.01 image, and is fully gated in ROM at
   `0x08079054`–`0x08079076` (`gMain.heldKeys & 0x06 == 0x06`).
2. A **second title-screen code** shares the same gate: **B+Select+Up** → “Clear all save data
   areas?” (mask `0x46`, checked *first*). **Soft reset** is **A+B+Start+Select**, gated in the
   global main loop (`gMain.heldKeysRaw & 0x01` and `& (B|Start|Select) == …`).
3. **No debug menu is usable in this retail build.** The much-discussed R+Start “Debug Menu” and
   “Test Menu” are **prototype-only** (TCRF `Proto:` pages). On this ROM, R+Start opens the
   ordinary HELP system. The retail image has zero debug-menu functions/tables; the `LinkTest`
   debug screen and ~12 `Debug_*` helpers are **dead code** (no callers / gate never set true).
4. **No password/code-entry system exists.** The in-game “passwords” (Sevii-Islands Team Rocket
   warehouses) are scripted dialogue flags, not typed codes. Only two text-input surfaces exist
   in the whole image (naming screen, Easy Chat), neither compared to a validator. No published
   in-game cheat-password list exists for this SKU; published “cheats” are GameShark/Action Replay
   memory codes, explicitly out of scope.

## 3. How to reproduce

* Emulator: `mgba -3` under `Xvfb :317` / `openbox`, `SDL_AUDIODRIVER=dummy`, window focused with
  `xdotool windowfocus`. Keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`,
  D-pad = arrow keys (verified by key-state RAM reads, §7).
* **Published code**: boot to “PRESS START”; **hold `z`+`BackSpace` (B+Select) ≈1 s**. The green
  “Berry Program Update” screen appears; press A → link-cable diagram (“Ensure the connection…
  YES: Press A”). Hold times <~0.3 s can be missed (debounce / scene timing) — use ≥1 s.
* **Novel code**: hold **Right first**, then B+Select → same screen (proof below).
* **Rejection**: hold B+Up (no Select) → nothing happens, still title screen.
* **Third branch**: hold **Up first**, then B+Select → “Clear all save data areas?” (choose NO).
* **Soft reset**: hold `x`+`z`+`Return`+`BackSpace` (A+B+Start+Select) ≈0.8 s → cart reboots.
* **Debug-menu negative**: from the overworld press `s`+`Return` (R+Start) → HELP system only.
* RAM reads used mGBA's CLI debugger (`mgba -d`, PTY bridge), `r/2`/`r/4` at the `gMain` offsets
  in §4; breakpoints `break/t 0x080796FC` (Berry) and `break/t 0x080796E0` (save-clear).

## 4. Address map

### ROM / code (file offset = ROM address − `0x08000000`)

| Address | Symbol / meaning |
|---|---|
| `0x08000204` | crt0 entry |
| `0x080008EC` | `DoSoftReset` (called from global main loop near `0x080008BE`) |
| `0x08078928` | `CB2_InitTitleScreen` |
| `0x08078BB0` | `CB2_TitleScreenRun` |
| `0x08078C38` | `Task_TitleScreenMain` |
| **`0x08078FD8`** | **`SetTitleScreenScene_Run` — all three title-screen button-code branches** |
| `0x080796E0` | `CB2_FadeOutTransitionToSaveClearScreen` |
| `0x080796FC` | `CB2_FadeOutTransitionToBerryFix` |
| `0x0815F7A0` | `CB2_InitBerryFixProgram` (decompresses multiboot Berry Program) |
| `0x0815F838` | `CB2_BerryFix`; `0x0815F844` `Task_BerryFixMain` |
| `0x08009AA0` | `CB2_LinkTest` (dead); `0x08009654` `LinkTestScreen` (dead, “Unused”) |
| `0x080099E4` | `LinkTestProcessKeyInput` (dead); `0x0800A8A4` `SetLinkDebugValues` (dead) |
| `0x0826201C` | `sDebug_Messages[8]` (unused, zero xrefs); `0x08262089` trade debug texts |
| `0x083BF5DC` | `src/title_screen.o` `.rodata` (in-game text, custom encoding) |
| `0x087031AC` | embedded `TEST` multiboot header |

### RAM (IWRAM / EWRAM)

| Address | Symbol / meaning |
|---|---|
| `0x030030F0` | `gMain` |
| `0x030030F4` | `gMain.callback2` (Thumb pointer, low bit set) |
| `0x03003118` | `gMain.heldKeysRaw` (active-high) |
| `0x0300311A` | `gMain.newKeysRaw` |
| `0x0300311C` | `gMain.heldKeys` (active-high; L=A remap) |
| `0x0300311E` | `gMain.newKeys` |
| `0x03003530` | `gSoftResetDisabled` |
| `0x02022110` | `sLinkTestDebugValuesEnabled` — init `0`, only ever written `0` |
| `0x03003E6C` / `0x03003EB0` | `gLinkDebugSeed` / `gLinkDebugFlags` (dead link test) |

## 5. Algorithm (button-code validator)

Decompiled source (`src/title_screen.c`, REVISION=1; verified against ROM bytes at `0x08078FD8`):

```c
#define KEYSTROKE_DELSAVE  (B_BUTTON | SELECT_BUTTON | DPAD_UP)   // 0x46
#define KEYSTROKE_BERRY_FIX(B_BUTTON | SELECT_BUTTON)             // 0x06

// SetTitleScreenScene_Run(), case 1 — checked every frame on the title screen
if (JOY_HELD(KEYSTROKE_DELSAVE) == KEYSTROKE_DELSAVE)        // gMain.heldKeys & 0x46 == 0x46
    SetMainCallback2(CB2_FadeOutTransitionToSaveClearScreen); // 0x080796E0
else if (JOY_HELD(KEYSTROKE_BERRY_FIX) == KEYSTROKE_BERRY_FIX) // gMain.heldKeys & 0x06 == 0x06
    SetMainCallback2(CB2_FadeOutTransitionToBerryFix);        // 0x080796FC
else if (JOY_NEW(A_BUTTON | START_BUTTON))                    // gMain.newKeys & 0x09
    SetTitleScreenScene(data, TITLESCREENSCENE_CRY);          // start game
```

ROM bytes at `0x08079018`: `ldr r2,=gMain; ldrh r1,[r2,#0x2C]; movs r0,#0x46; ands r0,r1;
cmp r0,#0x46; bne …`; at `0x08079054`: `movs r0,#6; ands; cmp r0,#6; bne …`; at
`0x08079080`: `ldrh r1,[r2,#0x2E]; movs r0,#9; ands; cmp r0,#0`.

**Semantics:** `JOY_HELD(mask)==mask` means “all mask bits held; extra held buttons are ignored”.
Because the `0x46` test runs first, B+Select+Up erases instead of opening Berry Fix. Both tests
use *held* keys, so a tap shorter than one frame can be missed. Soft reset is separate and global:

```c
// AgbMain loop, ~0x080008BE
if (!gSoftResetDisabled && (gMain.heldKeysRaw & A_BUTTON)
    && (gMain.heldKeysRaw & (B|START|SELECT)) == (B|START|SELECT))
    DoSoftReset();                       // 0x080008EC
```

## 6. Tables

| Held mask | Buttons | Result | Gate address | Verified |
|---|---|---|---|---|
| `0x46` | B+Select+Up | Save-clear confirmation screen | `0x08079018` | breakpoint + RAM `0x0046`, callback `0x080796E1` |
| `0x06` | B+Select | Berry Program Update (Berry Fix) | `0x08079054` | breakpoint + RAM `0x0006`, callback `0x080796FD` |
| `0x16` | B+Select+Right | Berry Fix (novel superset) | `0x08079054` | breakpoint + RAM `0x0016`, callback `0x080796FD` |
| `0x42` | B+Up | **rejected** (no branch) | — | RAM `0x0042`, callback stays `0x08078BB1` (title) |
| `0x9` (newKeys) | A or Start | Start game / skip title | `0x08079080` | observed via New Game walk |
| `0x01 + 0x0E` | A+B+Start+Select | Soft reset | main loop `0x080008BE` | observed: cart reboot |

### Debug-menu / code-entry negatives (proved, not assumed)

* Global button handlers in `src/main.c`: soft reset; `JOY_HELD(L_BUTTON)` watched-key help;
  nothing else. There is **no** R+Start branch in this build. Dynamic: R+Start → HELP.
* `CB2_LinkTest` / `LinkTestScreen` (debug hex screen with its own key commands) are **dead**:
  `LinkTestScreen` is commented “Unused” and has **zero callers**; `sLinkTestDebugValuesEnabled`
  is initialised `FALSE` and its **only other store is `FALSE`** (`src/link.c:112, 463`), so the
  `if (sLinkTestDebugValuesEnabled)` display can never be enabled by any input.
* All `Debug_*` helpers have no external callers: `Debug_AddDaycareSteps`, `Debug_FillEReaderTrainer
  WithPlayerData`, `Debug_NamingScreen{Player,Box,CaughtMon,Nickname,Rival}`, `Debug_RfuIdle`,
  `Debug_PrintStatus`, `Debug_SetPlayerNamesAndResults`, `Debug_UpdateNumPlayers`,
  `CreateUnknownDebugSprite`, `SpriteCB_UnusedDebugSprite`. The only *called* ones (`shop.c`)
  are **empty function bodies**. `sDebug_Messages` / `sDebug_TradeResultTexts` have zero xrefs.
* No password UI: source-wide `password|passcode` hits = 29, all in Sevii-Islands dialogue
  (`MtEmber_Exterior`, `FiveIsland_Meadow`, `SixIsland_DottedHole_SapphireRoom`) and one Mystery
  Event message string. Those doors are `goto_if_set FLAG_…` gates — the “password” is learned
  from an NPC and stored as a flag; the player never types a code. The only other text-input
  surfaces are `naming_screen.c` and Easy Chat, neither fed to a comparator.

## 6b. Enumeration

**Button-code space** (complete, not a sample): the title-screen validator has exactly three
branches over a 10-bit key mask. The accepted sets are all held-key supersets of `0x46` and
`0x06`; `0x46` takes precedence. There are `2^(10-3)=128` held-mask supersets of `0x06` and
`2^(10-3)=128` of `0x46`, of which 16 are in both (resolved to `0x46`). Every one of the 256
supersets maps to one of the two screens; every non-superset is rejected. Plus the independent
global soft-reset predicate and the two ordinary L/R help keys. There is no length field, no
sequence history and no checksum — this is a single-frame mask test, not a password format.

* **Published input** B+Select (`0x06`) → accepted (`callback2=0x080796FD`, green screen).
* **Novel, unpublished code minted and entered**: **B+Select+Right** (`0x0016`). This is absent
  from Bulbapedia, TCRF, GameFAQs and all published lists (which give only plain B+Select).
  It was held on the real title screen; the breakpoint at `0x080796FC` fired with
  `heldKeysRaw=0x0016` and `callback2=0x080796FD`, and after `continue` the green
  “Berry Program Update” screen appeared (screenshot `novel4_effect_c.png`).
* **Bounds proved by rejection**: B+Up (`0x0042`) — a one-bit change (drop Select) that is
  *not* a superset — left `callback2=0x08078BB1` (`CB2_TitleScreenRun`, still title) and the
  Berry-Fix breakpoint never fired; screenshot `reject_c.png` shows the untouched title.
  R as an extra button was also rejected *as a Berry code* — it routed to HELP instead,
  confirming that global L/R handling is a separate input path.
* **Precedence proved**: B+Select+Up (`0x0046`) hit the save-clear callback `0x080796E1`,
  not the Berry callback, with `heldKeysRaw=0x0046` — the `0x46` test is first.

## 7. Validation evidence

Labels follow the guide (Observed / Derived / Inferred).

* **Observed (emulator + RAM)**: green Berry screen from B+Select and from B+Select+Right;
  save-clear screen from B+Select+Up; HELP from R+Start; 5-item Start menu (BAG / AAAAAAA /
  SAVE / OPTION / EXIT); 7-item OPTIONS (TEXT SPEED, BATTLE SCENE, BATTLE STYLE, SOUND,
  BUTTON MODE, FRAME, CANCEL); New Game and intro walked to the overworld; soft reset rebooted
  the cart. Breakpoint hits at `0x080796FC`/`0x080796E0` with `heldKeysRaw` `0x0006`/`0x0016`/
  `0x0046` and `callback2` `0x080796FD`/`0x080796E1`; rejected B+Up `heldKeysRaw=0x0042`,
  `callback2=0x08078BB1`. Key names verified because the RAM masks equal the expected GBA bits.
* **Derived (ROM bytes)**: the three `movs #0x46/#6/#9` + `ands`/`cmp` gates at
  `0x08079018/0x08079054/0x08079080` and the literal `0x030030F0` (`gMain`) they load.
* **Derived (byte-identical decomp)**: source-level gate, dead-code caller counts, the
  `sLinkTestDebugValuesEnabled` writer set `{0}`, and the absence of any debug-menu symbol.
* **Inferred**: the Berry Program's purpose (repair the R/S berry-clock glitch) comes from the
  on-screen text and `pret/berry-fix`; the transfer itself was not completed (needs a second GBA).
* Web content (TCRF/pokemon-france/Bulbapedia) was treated strictly as data; no fetched
  instruction was executed. The TCRF fetch returned 403; snippets were used only as leads and
  every literal was then verified against the ROM.

## 8. Unknowns

* The multiboot transfer past the “YES: Press A” connection screen was not completed — no second
  GBA/link cable, so no RAM proof of a successful Berry update. The *entry* to that screen is proven.
* The exact fate of the R+Start “Debug Menu” in the unreleased prototype is out of scope for
  this retail image; only its absence here is proven.
* The 16 embedded multiboot/test images and the `AGBJ`/`TEST` stubs were identified by header
  but not individually executed.
* No attempt was made to confirm the save-clear code's *final* YES (destructive); only the
  confirmation screen was reached, and the `.sav` was backed up and restored.

## 9. Tooling

* `md5sum`/`sha1sum`/`sha256sum`, `file`, `xxd`, `strings -t x`, `grep -r`.
* `pret/pokefirered` shallow clone + `pret/agbcc` (built with `gcc-arm-none-eabi`,
  `libpng-dev`, `zlib1g-dev`, `libnewlib-arm-none-eabi`); `make leafgreen_rev1` produced a
  byte-identical ROM and `pokeleafgreen_rev1.map`/`.elf`; `arm-none-eabi-nm` gave static
  symbol addresses.
* `arm-none-eabi-objdump -M force-thumb` for the gate disassembly; Python 3 + capstone 5.0.7.
* mGBA under `Xvfb :317` + `openbox`, `xdotool`, `scrot`, ImageMagick; mGBA CLI debugger `-d`
  driven through a Python `pty` bridge (`ptybridge.py`) for `r/2`/`r/4`/`break/t`.
* `ssdiff.py` (mGBA `.ss1` `gbAs`/zlib extractor) used for an initial RAM diff cross-check.
* Legal: only findings/addresses/algorithms are published; no ROM bytes or extracted assets.
