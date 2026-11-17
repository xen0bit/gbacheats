# Donkey Kong Country 2 (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Donkey Kong Country 2/Donkey Kong Country 2.gba` |
| Size | 8,388,608 bytes (0x800000) |
| Header title | `RAREDKC2` |
| Game code | `B2DE` (USA) |
| Maker | `01` (Nintendo); Rare is the developer (`RAREDKC2`) |
| Version | 0x00 |
| Entry word | `0xEA00002E` (stock Nintendo branch to `0x080000C0`) — no cracktro patch |
| Header complement | `0xC5`; header checksum `0x0000` (normal rebuilt-header artifact) |
| MD5 | `a1f160ee30ed36edea341a6f1c6a4efc` |
| SHA-1 | `b0a4d59447c8d7c321bea4dc7253b0f581129ede` |
| SHA-256 | `02d0756f7e95308aec4f44598433e93a9a66bf5eabbf0cec7fd8d5f31a06a2f5` |

Embedded-header scan: exactly **one** Nintendo-logo hit (file `0x0`), so this is a single-image ROM, not a 2-in-1. No appended trainer, patch, or alternate boot stub was found.

## 2. Executive summary

The GBA port **retains a developer-intended cheat system**, but it is nothing like the SNES "Cheat Mode" (which used a hidden menu reached by pressing Down on the two-player contest entry). The GBA implementation is a **closed, 9-entry exact-string lookup table** reached from
`Select Save Slot → Options → Cheats → ENTER CHEAT CODE`.

There is **no password generator, no checksum, no alphabet cipher, no button-code sequence, and no hidden debug menu**. The complete accepted set is the nine published codes; each is compared byte-for-byte with `strcmp` against a 12-byte record. A 16-bit flag word in IWRAM is written on acceptance. All nine codes and nine out-of-set strings were tested against the real screen and verified by reading that flag in RAM. Because the validator is a fixed 9-record `strcmp` loop with no algorithmic path, **no unpublished valid code can exist**; this is proved below rather than asserted.

Observed effects: `HELPME` → `x15` lives in the in-game HUD; `ONETIME` → Music Player screen; `KREDITS` → scrolling credits; `FREEDOM` → recorded flag `0x0008` (all levels on new file). Published sources were cross-checked against the table; all nine literals are present at their expected records.

## 3. How to reproduce

Emulator: mGBA 0.10.5 (SDL) under Xvfb `:315`, `SDL_AUDIODRIVER=dummy`, `-3` scale. Keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad = arrow keys. Hold keys 150–180 ms with ≥350 ms gaps — faster taps are dropped by the menu's debounce.

Menu path (every step observed):

1. Boot → title (`PRESS START`) → Start.
2. Main menu: **Start**, **Diddy's Dash**, **Bonus Games** (three items only). Select **Start** (A).
3. **SELECT SAVE SLOT** → move to bottom-right **Options** → A.
4. Options: **Music Volume**, **SFX Volume**, **Cheats** → Down, Down, A.
5. **ENTER CHEAT CODE**: on-screen keyboard rows `A–J / K–T / . U V W X Y Z * / DEL END`.
6. Type a code, select **END** → A. On acceptance the game returns to the save-slot screen; on rejection it also returns but leaves the flag at 0.

Deterministic testing shortcut (used for the enumeration): savestate at the cheat screen, patch the input buffer with `patchss.py`, set the cursor byte to `END` (29), reload, press A, save a state, and read the flag from the uncompressed `gbAs` chunk with `ss.py`. All scripts are in `/tmp/opencode/dkc2b/`.

Published codes tested (all accepted, all flags verified):
`RICHMAN`, `WELLRICH`, `HELPME`, `WEAKLING`, `WELLARD`, `ROCKARD`, `FREEDOM`, `ONETIME`, `KREDITS`.

Rejected inputs (all left flag = 0): `richman`, `RICHMAN `, `RICHMANX`, `R`, empty, `RICH.MAN`, `RICH*MAN`, `NOBODY`, `RICHMAN!`.

## 4. Address map

| Item | Address | Notes |
|---|---|---|
| Cheat record table | `0x087FF5B8` (file `0x7FF5B8`) | 9 × 12 bytes, ends `0x087FF623` |
| Record layout | `+0..+7` ASCII code (NUL padded), `+8..+11` u32 flag bitmask | flag's **high halfword** is what gets stored |
| Validator (check) | `0x080BE404` | loops r4=0..8, `bl 0x080016D0` (`strcmp`), returns 1 on match |
| Applier | `0x080BE430` | same loop; on match `ldrh r0,[r4,#10]`, `strh r0,[r7+2]` |
| Caller / UI result | `0x080BE534`, `0x080BE550` | bit0 → credits screen, bit8 → Music Player |
| `strcmp` | `0x080016D0` | plain byte-wise NUL-terminated compare, no transform |
| Cheat flag (u16) | IWRAM `0x030005D2` | written by applier; read at `0x080BE554` |
| Cheat-screen state struct | IWRAM `0x030005D0` | global room/state block |
| Input string buffer | EWRAM `0x0200561B` | NUL-terminated, max ~9 chars |
| Input length byte | EWRAM `0x02005618` | number of typed characters |
| Keyboard cursor index | EWRAM `0x02005624` | 0-based: 0=A … 9=J, 10=K … 19=T, 20=`.`, 21=U … 27=`*`, 28=DEL, 29=END |
| Keyboard layout table | `0x080DC1E0` | 30 records × 24 bytes (char, sentinel, x/y, L/R neighbor indices, w/h) |
| KEYINPUT | `0x04000130` | read once at `0x08001EA0` |
| Pressed-key mask | IWRAM `0x03000144` | active-high edge mask |
| Held-key mask | IWRAM `0x030001D4` | active-high held mask |
| Soft-reset gate | `0x08001EC2` → `0x080D08B8` | held & 0x0F == A+B+Select+Start ⇒ BIOS `svc 1` reset |
| Rhythm matcher (bonus minigames, **not** a cheat) | `0x08001EF0` | called only from `0x080BE1C0`/`0x080BE20C` |
| Room-name table | `0x08549C98` base | 84 records × 100 bytes; name pointer at `+0`; names at `0x080D1404+` |
| Text bank (menu labels) | `0x053AADC`–`0x053C700` | custom encoding with control bytes; `Cheat` label at `0x053BFA1` |

## 5. Algorithm

The entire cheat validator, in pseudocode:

```c
// r0 = pointer to NUL-terminated input string from 0x0200561B
int check(char *input) {
    u32 *rec = (u32*)0x087FF5B8;
    for (int i = 0; i <= 8; i++) {          // cmp r4,#8 ; bls
        if (strcmp(rec, input) == 0) return 1;
        rec += 3;                           // 12 bytes / record
    }
    return 0;
}

void apply(char *input) {
    u32 *rec = (u32*)0x087FF5B8;
    for (int i = 0; i <= 8; i++) {
        if (strcmp(rec, input) == 0) {
            *(u16*)0x030005D2 = *(u16*)((u8*)rec + 10);  // high halfword of flag
            return;
        }
        rec += 3;
    }
}
```

Caller (`0x080BE534`) checks the resulting flag: `flag & 0x0001` selects the credits screen (text id `0x24`), `flag & 0x0100` selects the Music Player (text id `0x2F`), otherwise text id `0x1E`. The remaining bits are consumed when a new save file is created; the flag is cleared after that (observed: flag `0x0002` after HELPME submission, `0x0000` on the world map of the newly started file).

## 6. Tables

The nine records at `0x087FF5B8` (flag = high halfword of the u32 at `+8`):

| ROM address | Code | Flag | Published effect |
|---|---|---|---|
| `0x087FF5B8` | `KREDITS` | `0x0001` | Show credits |
| `0x087FF5C4` | `HELPME` | `0x0002` | Start with 15 lives (observed) |
| `0x087FF5D0` | `WEAKLING` | `0x0004` | Start with 55 lives |
| `0x087FF5DC` | `RICHMAN` | `0x0010` | Start with 10 banana coins |
| `0x087FF5E8` | `WELLRICH` | `0x0020` | Start with 50 banana coins |
| `0x087FF5F4` | `FREEDOM` | `0x0008` | Unlock all levels (incl. Lost World) |
| `0x087FF600` | `WELLARD` | `0x0040` | Remove all DK barrels |
| `0x087FF60C` | `ROCKARD` | `0x00C0` | Remove DK and Star barrels (WELLARD bit + extra bit) |
| `0x087FF618` | `ONETIME` | `0x0100` | Music Player screen |

Trailing data at `0x087FF624` (`0x38` = 56), `0x087FF628` (`0x37` = 55) and `0x087FF62C` (`0xFFFFFFFF`) are numeric constants/sentinel, **not** additional records — the loop bound stops at index 8.

Flag-bit map: bit0 credits, bit1 15 lives, bit2 55 lives, bit3 all levels, bit4 10 coins, bit5 50 coins, bit6 no DK barrels, bit7 no Star barrels, bit8 music player. Bits 9–15 are unused by any table entry.

Input alphabet (keyboard table at `0x080DC1E0`): `A B C D E F G H I J K L M N O P Q R S T . U V W X Y Z *` (28 selectable symbols) plus `DEL` and `END` control keys.

## 6b. Enumeration

**Space definition.** The accepted space is not a checksum space: it is a literal lookup. The validator accepts exactly the 9 NUL-terminated strings stored at `0x087FF5B8..0x087FF623`. The input surface can express 28 symbols in up to ~9 positions, but only 9 exact strings are accepted. There is no encoder/decoder pair anywhere in the ROM (literal search for all 9 codes: one hit each, all inside this single 108-byte table; a scan for all NUL-terminated 5–12-character uppercase strings found 284 candidates, of which only these 9 are plausible codes and all 9 are in the table).

**Validator model.** Implemented exactly in §5; agreed with the ROM on all 18 tested inputs (9 accepted with the exact expected flag, 9 rejected with flag 0). This is the complete model of the accept/reject decision.

**Novel codes.** None can exist. This is a property of the design, not a gap in the search: the check is `strcmp` against a fixed 9-record array, there is no transformation of the input, no generated path, and no reserved-bit or alias case (plain byte compare means exactly one spelling per record). By contrast with the Car Battler Joe / Pirates cases, there is no second algorithmic format hiding beside the preset list — the keyboard alphabet has 28 symbols but the table uses only `A–Z`.

**Bounds proven by rejection.** The following out-of-set inputs were entered on the real screen and all left `0x030005D2 == 0`: wrong case (`richman`), trailing space (`RICHMAN `), extra character (`RICHMANX`), wrong punctuation (`RICH.MAN`, `RICH*MAN`, `RICHMAN!`), truncation (`R`), empty input, and an unrelated word (`NOBODY`). Because the loop bound is `i <= 8` and every comparison is exact, these rejections prove the boundary: no 10th code, no prefix/suffix alias, no case-insensitivity.

**Button-code space.** The published SNES codes (50 lives `Y,A,Select,A,Down,Left,A,Down`; hard mode `B,A,Right,Right,A,Left,A,X`; pause exit `Right+Y,Left+A,Up+B,Down+X`) were searched as u16 mask arrays (active-high, active-low, 1-byte-per-press, forward and reversed): **zero hits** anywhere in the 8 MiB. The only global key-combine gate is `A+B+Select+Start` → soft reset. Common hidden-menu combos (`L+R+Start`, `L+R+A+B`, `L+R+Select`, Konami code) were pressed on the title screen: no new screen or flag appeared. The SNES "press Down five times on the two-player entry" trick was tried on the GBA Game Select screen (1 Player / 2-Player Team): no Music Test or Cheat Mode appeared.

**Hidden debug screen.** The shipping ROM contains developer room names (`Bug Options Menu`, `ER Options Menu`, `FF Options Menu`, `Video Hero Mode`, `WARP ROOM`, `Main options page`, `Pause Menu`, `Title Page`) in the 84-entry room table at `0x08549C98`, but no input path reaches them in the retail build: no caller, key sequence, or menu entry for a room-select screen was found, and every reachable screen was walked. Classified as **dead/unreachable data** (guide §16.3), not a cheat.

## 7. Validation evidence

- **Observed (emulator + RAM)**: all 9 codes accepted, each writing the expected u16 to `0x030005D2`; 9 rejections leaving it 0; `HELPME` producing `x15` lives in the HUD; `ONETIME` producing the Music Player screen; `KREDITS` producing the credits; menu walk listed in §3.
- **Derived (disassembly)**: 9-record loop bound (`cmp r4,#8`), `strcmp` at `0x080016D0`, flag extraction (`ldrh [r4,#10]`), bit0/bit8 screen dispatch, keyboard alphabet table, soft-reset gate.
- **Inferred**: exact numeric starting coins/lives for codes other than HELPME come from published descriptions plus the table constants (`0x38`/`0x37`); those specific values were not re-read from the save record. The pause screen shows only `PAUSED` with no selectable entries, so the SNES pause-exit code has no GBA equivalent.

## 8. Unknowns

- Where the flag bits for coins/lives/barrels are consumed in new-file initialization (the state struct at `0x030005D0` has 759 xrefs; the exact writer for each derived value was not isolated). The resulting flags and one visible effect were verified, so the cheat set itself is closed.
- Whether the developer rooms in the room table were reachable in an internal build; no retail input path exists.

## 9. Tooling

- `strings -t x -n 4`, `grep -abo`, `xxd`, `arm-none-eabi-objdump -D -M force-thumb`, Capstone 5.0.7 for literal/BL scans.
- mGBA 0.10.5 SDL under Xvfb `:315` with `xdotool` key injection; savestates for reproducible screen state.
- `/tmp/opencode/dkc2b/ss.py` — decodes mGBA's zlib `gbAs` savestate chunk and reads IWRAM/EWRAM.
- `/tmp/opencode/dkc2b/patchss.py` — patches savestate bytes (input buffer, length, cursor) for deterministic tests.
- `/tmp/opencode/dkc2b/testcode.py` — submits a code through the real END key and reads the RAM flag.
- `/tmp/opencode/dkc2b/diffstate.py` — diffs two savestates to locate RAM fields (buffer, cursor, flag).
- Web: GameFAQs, RareGamer, CheatingDome, GGmania, CheatCC, gamezone.de, Bahamut — all nine literals verified in ROM.
- No ROM or copyrighted assets are redistributed; only addresses, hashes, and our own tooling are published.
