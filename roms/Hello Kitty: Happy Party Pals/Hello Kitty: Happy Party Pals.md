# Hello Kitty: Happy Party Pals (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Hello Kitty: Happy Party Pals.gba` |
| Size | 4,194,304 bytes (0x400000) |
| Header title | `HELLOKITTY` |
| Game code / maker | `B86E` / `78` |
| Version / complement / checksum | `00` / `0xE4` / `0x0000` |
| Entry word | `0xEA00002E` → `0x080000C0` (stock crt0) |
| MD5 | `18441e53efd724563581600a0f253879` |
| SHA-1 | `43496b1527dbe90627ab02a54a30acbcf42a3bdc` |
| SHA-256 | `2fdef617eb9f9d447bdc93f22d474bdb90e3c9a29b2d03e9aedf9fdbff9a01e9` |

**Phase 0 / 16.1:** exactly one Nintendo logo (file `0x4`), no appended trainer, no multicart, stock entry branch. Header checksum 0 is a rebuild artifact; complement `0xE4` is non-stock but the code and entry are intact. No patch detected.

**Engine note (from ASCII leftovers):** `Z:\Source\MapDisplay\AreaEntry.cpp` at `0x14400`, `Z:\Source\ByteCodeInterpreter\ByteCodeInterpreter.cpp` at `0x16d20`, C-runtime messages at `0x2b438`. All in-game text is **UTF-16LE**, so `strings` finds almost none of it — the full text bank was decoded from the pointer table (§3).

## 2. Executive summary

The game has a genuine developer-intended **8-letter password system** on the title-screen "Password" entry, labelled in UTF-16LE as `Secret Password` / `Enter Level Password`. It is *not* a GameShark-style system; all codes are typed on an on-screen A–Z keyboard with the D-pad.

There are **two validator modes** sharing one function at `0x0801ABC0`, gated by a runtime byte at `0x03002640`:

1. **Stage mode** (`[0x03002640]==1`): exact UTF-16LE compare against **six** fixed strings held in the game's string bank at indices 216–221.
2. **Item mode** (`[0x03002640]==0`): a **per-position dual-table** check. For each of 8 positions the entered letter must equal either `MYCHOICE[i]` (table A, ROM `0x081CE2D2`) or `URSPRKTY[i]` (table B, code literal `0x0801AECC`). Choosing B at a position grants one of eight items via `0x08016418`. Because all 16 position-pairs are distinct, this admits **2⁸ = 256** distinct codes.

Total accepted space: **6 + 256 = 262** inputs (with `MYCHOICE` belonging to both sets). Published GameFAQs/SuperCheats lists contain only a handful; a novel code was minted and accepted in-game (§6b).

Published-list corrections found and proven in the ROM/emulator:
* GameFAQs "GAMERIRL" is a typo — the ROM literal is **`GAMEGIRL`** (Accepted vs Denied, §7).
* The `UY*` codes are real but belong to item mode, not the stage table; they are *not* stored as whole strings in the ROM (they are combinations of the two 8-letter tables).

## 3. How to reproduce

* Emulator: mGBA 0.3+ under Xvfb; `SDL_AUDIODRIVER=dummy`, `mgba -3 game.gba`, display `:319`.
* Keymap (mGBA SDL): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad = arrows.
* Menu path: title → `Password` (Down once from `Party Time`, then `x`) → `Secret Password` screen → D-pad Left/Right selects a slot, Up/Down cycles the letter (Down steps A→Z→Y…), `x` submits.
* Input buffer: **`0x0203FDFA`** — eight UTF-16LE code units; cursor byte at `0x0203FDF8`. Changing a letter changes that halfword; this was verified by savestate diff and by writing the buffer with the mGBA pty debugger (`w/2`) and watching the on-screen letters change.
* Stage-mode path (fresh boot) accepted `YARDBASH` (written into `0x0203FDFA` with the debugger, then `x`) → `Accepted` → `Party Time` started ("Kitty must invite 3 friends.").
* Item-mode path (reached after loading the saved password-screen state, e.g. `F1` on a savestate made there) accepted `URSPRKTY`, `UYSHOICE` and the novel `MRSPRKTY` → `Accepted`.
* Published/unverified codes tested through the same UI: `GAMEGIRL` (Accepted), `GAMERIRL` (Denied), `UYSHOICE` (Accepted), `ZZZZZZZZ` (Denied), `CRSPRKTY` (Denied — `C` is legal at neither table position 0).

## 4. Address map

| Item | File offset | ROM address | Evidence |
|---|---:|---|---|
| Nintendo logo / header | `0x4` | `0x08000004` | Observed |
| C-runtime strings | `0x2b438` | `0x0802B438` | Observed (`strings`) |
| `AreaEntry.cpp` path | `0x14400` | `0x08014400` | Observed |
| `ByteCodeInterpreter.cpp` path | `0x16d20` | `0x08016D20` | Observed |
| String pointer table base | `0x1D4348` | `0x081D4348` | Derived; 4-byte pointers into UTF-16LE bank |
| `Accepted` / `Denied` strings | `0x1CD3BE` / `0x1CD3D0` | `0x081CD3BE` / `0x081CD3D0` | Observed on screen + table idx 46/47 |
| Stage code `YARDBASH` (idx 216) | `0x1CE278` | `0x081CE278` | ROM literal + watchpoint hit |
| Stage codes idx 217–221 | `0x1CE28A`…`0x1CE2D2` | `0x081CE28A`…`0x081CE2D2` | Table dump |
| Item table A `MYCHOICE` | `0x1CE2D2` | `0x081CE2D2` | `r6` read at `0x0801AC96` after `ldr r6,[r0,#52]` |
| Item table B `URSPRKTY` | `0x1AECC` | `0x0801AECC` | `adr r7, 0x801aecc` |
| Validator entry | `0x1ABC0` | `0x0801ABC0` | Breakpoint hit, `lr = 0x0802767B` |
| UTF-16LE `strncmp` | `0x207D4` | `0x080207D4` | Watchpoint on stage string hit here |
| Item-grant call | `0x16418` | `0x08016418` | Jump table at `0x0801ACCC` |
| Mode flag | RAM | `0x03002640` | `r/1`, `w/1` (1 = stage, 0 = item, 7 = item success) |
| Gate byte | RAM | `0x03002641` | `0x0801ABFA` returns 1 when nonzero |
| Password input buffer | EWRAM | `0x0203FDFA` | Savestate diff + debugger write + on-screen display |
| Cursor byte | EWRAM | `0x0203FDF8` | Savestate diff (0–7) |

Player struct base is `0x0203FDF0`; the validator reads the code at `struct+0x0A`.

## 5. Algorithm

Pseudocode recovered from `0x0801ABC0`, `0x080207D4`, `0x0801AC8C`–`0x0801ADAC`:

```c
// state byte s = byte[0x03002640];  gate = byte[0x03002641]
if (gate != 0) return 1;                       // 0x0801ABFA

if (s == 1) {                                  // STAGE MODE
    for (idx = 216; idx <= 221; idx++) {       // 0x0801AC1A..0x0801AC24
        str = string_table[idx];               // pointer array at 0x081D4348
        if (utf16_strncmp(input, str, 8) == 0) {
            byte[0x03002640] = idx + 42;       // 0x0801AC6E: idx 216..221 -> 2..7
            store stage/party state; show "Accepted"; return;
        }
    }
    if (s != 0) goto Denied;                   // 0x0801AC88
}

// ITEM MODE (s == 0), 0x0801AC8C
A = "MYCHOICE";                                // r6 = [0x081D4348 + 0x340 + 0x34]
B = "URSPRKTY";                                // r7 = 0x0801AECC
for (i = 0; i < 8; i++) {
    if (input[i] == A[i]) continue;            // no item for this slot
    if (input[i] != B[i]) goto Denied;         // 0x0801ACBE -> 0x0801ADAe
    grant_item(item_ids[i]);                   // call 0x08016418(r0, id, 1)
}
byte[0x03002640] = 7;                          // success marker, 0x0801AD68
show "Accepted"
```

`utf16_strncmp` at `0x080207D4` compares 16-bit code units and returns 0 only if all `N` match. Item IDs by slot (`0x0801ACD6`…`0x0801AD48`): **[76, 48, 50, 36, 77, 63, 43, 106]**.

## 6. Tables

**Stage passwords (exact, 8 UTF-16LE letters, string-table indices 216–221):**

| idx | ROM address | Code | Published effect |
|---:|---|---|---|
| 216 | `0x081CE278` | `YARDBASH` | Back Yard, Stage 1 |
| 217 | `0x081CE28A` | `MYPICNIC` | Park, Stage 2 |
| 218 | `0x081CE29C` | `SUSHIYUM` | Sushi Joint, Stage 3 |
| 219 | `0x081CE2AE` | `GAMEGIRL` | Arcade, Stage 4 (**ROM spelling**) |
| 220 | `0x081CE2C0` | `BEACHFUN` | Forest by the Beach, Stage 5 |
| 221 | `0x081CE2D2` | `MYCHOICE` | Anywhere, Stage 6 |

**Item-mode alphabet (per slot, "either/or", A=`MYCHOICE`, B=`URSPRKTY`):**

| slot | A | B | item granted when B chosen |
|---:|---|---|---:|
| 0 | M | U | 76 |
| 1 | Y | R | 48 |
| 2 | C | S | 50 |
| 3 | H | P | 36 |
| 4 | O | R | 77 |
| 5 | I | K | 63 |
| 6 | C | T | 43 |
| 7 | E | Y | 106 |

On-screen keyboard: exactly A–Z (26 symbols); Down decrements with wrap (A→Z), Up increments. No digits or symbols are reachable.

Published codes checked (GameFAQs 2018 snapshot via web.archive.org, SuperCheats, VGChartz, Fandom):
`MYCHOICE`, `UYSHOICE`, `UYSHOKE`, `UYCHOICE`, `UYSPOKCY`, `UYCPHOICE`, `YARDBASH`, `MYPICNIC`, `SUSHIYUM`, `GAMERIRL`, `BEACHFUN`, `URSPRKTY`.
`GAMERIRL` is absent from the ROM; `GAMEGIRL` is present. The `UY*` strings are absent from the ROM as whole literals — they are combinations of the two tables (verified: `UYSHOICE` = B,A,B,A,A,A,A,A → Accepted). `UYCPHOICE` is 9 characters and cannot be entered in the 8-slot UI (reported as unverified/likely typo).

## 6b. Enumeration

**Space definition.** 8 positions, 26-letter alphabet, UTF-16LE storage, no checksum.

* Stage mode: exactly **6** accepted strings (table above), all published except the corrected spelling.
* Item mode: each of 8 slots independently accepts one of two letters ⇒ **2⁸ = 256** accepted strings. The two 8-letter seeds are `MYCHOICE` (all A) and `URSPRKTY` (all B); every one of the 255 non-all-B combinations is unreported in the published lists. `MYCHOICE` aliases into the stage set (dual-mode alias).
* Grand total: **262** accepted inputs across both modes (256 + 6, with one overlap). No reserved bits or checksum exist; the mode gate at `0x03002640` selects the active set.

**Novel code minted and accepted in-game:** **`MRSPRKTY`** — slot 0 from table A (`M`), slots 1–7 from table B (`R,S,P,R,K,T,Y`). It grants items 48, 50, 36, 77, 63, 43 and 106 but *not* item 76 (the one `U`/slot-0 branch). It appears in no GameFAQs/VGChartz/TCRF/Fandom/SuperCheats list. Entered on the real Secret Password screen with the D-pad; result `Accepted` (screenshot `novel3_v.png`), and play started with the normal "Kitty must invite 8 friends." state rather than the all-areas state produced by `URSPRKTY` — a visibly distinct outcome, proving the per-position semantics.

**Bounds proven by rejection (observed, not inferred):**
* `ZZZZZZZZ` — 8 legal letters but matches neither table at slot 0 → **Denied** (`test_ZZZZZZZZ_v.png`). This proves the alphabet alone is insufficient; position-specific membership is enforced.
* `CRSPRKTY` — 8 legal letters, `C` at slot 0 matches neither `M` nor `U` → **Denied** (`novel_v.png`).
* `URSPRCKY` — `C` at slot 5 matches neither `I` nor `K` → **Denied** (`t_ursp_v.png`).
* `GAMERIRL` (published typo) — differs from ROM literal at slot 4 → **Denied** (`test_GAMERIRL_v.png`).

**Enumeration method:** the item-mode set is a simple product of 2 choices per slot; no brute force was needed. The game's own validator was used as an oracle (breakpoint `0x0801ABC0`, read watchpoint on `0x081CE278`, `w/2` writes to `0x0203FDFA`) to confirm each table pointer and the accept/reject results before typing codes on the real screen.

## 7. Validation evidence

**Observed (emulator / RAM):**
* Title: `Party Time / Password / Party Games`; Party Games carousel shows 13 minigames (`Pinball Party Treats`, `Shop Hop`, `Bouncing Balloons`, …) and launches a playable minigame.
* Password screen shows 8 slots, on-screen A–Z picker, `Accepted` / `Denied`.
* In-game Party Time, dialogue, Journal prompt (Select), and pause menus (party: `Continue/Quit`; minigame: `Continue/Retry/Quit`) all walked with confirmation screens.
* `YARDBASH` written to `0x0203FDFA` + `x` → `Accepted`, then Party Time started.
* `URSPRKTY`, `UYSHOICE`, `MRSPRKTY`, `GAMEGIRL` typed on the real screen → `Accepted`; `GAMERIRL`, `ZZZZZZZZ`, `CRSPRKTY`, `URSPRCKY` → `Denied`.
* Cache of savestate raw (`gbAs` → zlib, IWRAM `0x19000`, EWRAM `0x21000`) used to locate input buffer and cursor byte.

**Derived (disassembly):**
* Six-entry stage loop `idx 216..221` and stride-4 string pointer table at `0x081D4348`.
* Two-table item check, per-slot item IDs, flag writes at `0x0801AC6E` / `0x0801AD68`.
* Alphabet and wrap behaviour of the on-screen picker.

**Inferred / not fully exercised:**
* The writer of the mode byte at `0x03002640` was not traced; observed values were 1 on a fresh boot and 0 after loading the saved password-screen state. The report therefore does not claim exactly which game state selects item mode, only that both modes are reachable and both were exercised.
* The exact in-game identity of item IDs 76/48/50/36/77/63/43/106 was not read from the inventory screen; item names in GameFAQs (`Hagota Paddle Boat`, `Diamond Necklace`, `Gameboy`, `Red Fish`, `Energy Drink`, …) are plausible but unverified per slot.

## 8. Unknowns

* Which condition sets `0x03002640` to 0 vs 1 (save-file state, story progress, or entry point). Both branches were reached and validated, but the gate's writer is untraced.
* Whether the 9-character `UYCPHOICE` from GameFAQs is a transcription error or belongs to an unreachable mode (the UI has only 8 slots).
* Per-item display names for the eight grant IDs.
* No hidden/debug menu was found on any screen walked; no button-code sequence was observed. The only hidden surface is the password system documented above.

## 9. Tooling

* `strings -t x`, `xxd`, `grep` for the first pass; Python for header/logo scan and UTF-16LE string-table decode.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for all disassembly (the pty debugger's own `dis` was abandoned after it produced runaway output).
* Capstone 5.0.7 for PC-relative literal scans.
* mGBA `-d` pty debugger driven through a FIFO bridge (`ptybridge.py`, `dbg3.py`) — used for breakpoints, register reads, `w/2` RAM writes, and the read watchpoint that located the validator.
* Savestate parser (`ss.py`, `pwbuf.py`) — zlib-decompresses the `gbAs` PNG chunk; IWRAM at raw `0x19000`, EWRAM at raw `0x21000`.
* Input helper (`gba.py`, `enter2.py`) — XTEST key events with 100 ms holds / 280 ms gaps (shorter holds were missed or double-stepped), savestate-verified letter entry.
* Xvfb `:319` + openbox; all processes launched and stopped by PID.

**Legal note:** no ROM bytes, graphics, music or full game text are redistributed here — only addresses, hashes, algorithms and the author-generated example code.
