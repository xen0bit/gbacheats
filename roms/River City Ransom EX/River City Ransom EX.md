# River City Ransom EX (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/River City Ransom EX/River City Ransom EX.gba` |
| Size | 4,194,304 bytes (`0x400000`) |
| Header title | `RIVERCRANSOM` |
| Game code | `BDTE` |
| Maker | `EB` |
| Version | `0x00` |
| Entry word | `0xEA00002E` (stock GBA crt0 branch to `0x080000C0`) |
| Header complement | stored `0x10`, computed `0x29` — **header was edited** |
| Header checksum | `0x0000` |
| Nintendo logo | bytes `0x04..0x1F` diverge from the standard logo after the first 5 bytes — **patched dump** |
| MD5 | `0b95fb20b9f487eb64431e9db9f75c7f` |
| SHA-1 | `64d0b723ae4eb3f3589b535fb935618f2769229f` |
| SHA-256 | `c23ac5c8d3f20d44e1e35968219218e533a047dab083fb2170cf257a51533bb5` |

Phase 0 notes: a scan for the 156-byte Nintendo logo over the whole 4 MiB found **no** standard logo hit; the only header is at file `0x00`. The crt0 at `0x080000C0` is a normal, unmodified GBA startup (`ldr sp`, `msr CPSR`, `bx r1` into a Thumb `main` at `0x080003A1`). There is no appended trainer (the image ends exactly at `0x400000`) and no cracktro at the entry point: the patch affects the logo/complement only, so this is a header-patched ROM image, not a cheat trainer. No GameShark/CodeBreaker codes are reported anywhere below.

All ASCII `strings` searches for `password`, `cheat`, `debug`, `secret`, `code`, `unlock` returned nothing. The entire in-game text bank is **font/tile-indexed**, not ASCII: characters are stored as encoded bytes (`'A'`=`0xA4`, etc.), which is why a naive string scan produces a false negative (guide §11). The font/charset was decoded before reaching the negative conclusion (see §4).

## 2. Executive summary

The GBA EX release **retains a developer-intended cheat system**, but it is not the NES character-creation password system. It is a **"change name" code list**: from the in-game Start menu, `Status → Name → Change`, typing one of ten fixed 4–5 character names applies a built-in effect. There is **no algorithmic password generator, no 5-/6-bit checksum code, no button sequence, and no hidden debug menu**. The validator is a closed 10-entry table lookup with an exact NUL-terminated byte comparison; every accepted code is one of the ten published name codes, and the published list is complete and correct for this ROM.

The system was reversed end-to-end: the code table, its duplicated pointer tables, the charset encoding, the validator loop, its compare helper, its dispatch table and all five effect handlers have addresses below. Two codes were confirmed dynamically with RAM evidence (`PLAYA` → money `0x05F5E0FF`; `DAMAX` → all stats `0x7F`, HP/stamina `0xFF00`), and a non-code name was rejected with no effect. Because the accepted set is provably closed at ten values and all ten are already published, **no unpublished code exists** — that is the bounded negative result for the "novel code" deliverable (§0.2), supported by three independent closure proofs in §6b.

Published sources consulted (treated strictly as data): GameFAQs cheat page (archived snapshot 2023-02-12), GamingTarget "Name Codes", VGChartz, and Japanese walkthroughs (dtstoryexp.iinaa.net, wazap.com). The GameFAQs "Debug Password / Shin Mode" and its "Passwords" list are tagged **NES**, not GBA; no corresponding string exists in this GBA image. The Japanese SKU uses katakana code names (どらむすこ, てんこもり, さーびす０/１/２, …) instead of the English words; those strings are not in this English/European image, whose table holds the English words.

## 3. How to reproduce

Emulator: `mgba -3` under `Xvfb :318`, `SDL_AUDIODRIVER=dummy`. Keymap used: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad = arrow keys (hold ≈70–150 ms).

Exact menu path:

1. Boot; title menu shows `Story` / `Manage Data`. Choose **Story**, accept the setup (`Alex+Ryan`, Ally 4, Enemy 4, Level 1, Attack Weapon, Text Normal, COM Normal) with `OK`, then advance the opening dialogue.
2. Press **Start** → menu `Item / Status / Strategy / File / Technique / Log / Options / Mode`.
3. Choose **Status** → `OK / Name`.
4. Choose **Name** → `OK / Change / Default / Cancel`; choose **Change**.
5. The 8-slot name field clears to blanks and a 14×5 keyboard appears:
   - row 0 `A a B b C c D d E e Z z 0 ¥`
   - row 1 `F f G g H h I i J j 1 2 3 -`
   - row 2 `K k L l M m N n O o 4 5 6 !`
   - row 3 `P p Q q R r S s T t 7 8 9 ?`
   - row 4 `U u V v W w X x Y y , . · EN`
   - D-pad moves the highlight; A types it. After 5 characters the field auto-returns to `OK / Change / Default / Cancel`; press **A** on `OK` to commit. Codes are case-sensitive.
6. Confirmation is visible on the Status screen (name and/or stats/money changed); a savestate diff or the RAM addresses in §4 give machine-checkable proof.

Codes tested in this session: `PLAYA` (accepted, money max), `DAMAX` (accepted, stats max), `XTRA0` (accepted, name changed; handler writes item ID `0x0310`), `XXXXX` (rejected, no change).

## 4. Address map

File offset `F` ↔ ROM address `0x08000000 + F`. All RAM addresses are GBA bus addresses.

| Item | Address | Notes |
|---|---|---|
| Code-string table (10 × 8 bytes, NUL padded) | ROM `0x0810C184` (`F=0x10C184`) | encoded strings, 8-byte stride, last at `0x0810C1CC` |
| Code-string pointer table (copy) | EWRAM `0x02016F78` | 10 pointers + `0x00000000` terminator |
| Code-string pointer table (ROM source) | ROM `0x083722DC` | same 10 pointers, different physical order |
| Other pointer tables to same strings | ROM `0x080F9C64`, `0x080FBD20` | text-bank banks, not the validator |
| Name-code validator | ROM `0x0802A5FC` (Thumb) | loops indices 9→0 |
| Compare helper (`strcmp` on encoded bytes) | ROM `0x0802A5DC` (Thumb) | returns 1 on match |
| Accept point (breakpoint used) | ROM `0x0802A664` | reached only after a match |
| Effect dispatch (`mov pc, r0`) | ROM `0x0802A670` | jumps through handler table |
| Effect handler table (10 Thumb pointers) | ROM `0x0802A67C` | indexed by code index |
| Player struct base for slot 0 | EWRAM `0x02000414` | selected via `*(0x02010848 + idx*4)` |
| **Name buffer (8 bytes)** | EWRAM `0x02000494` | `player + 0x80`, NUL terminated |
| **Money (u32, cents)** | EWRAM `0x02000454` | `0x00000BB8` = $30.00; `0x05F5E0FF` = $999,999.99 |
| Stats (7 bytes) | EWRAM `0x02000414` | `0x7F` = max after `DAMAX` |
| Items (12 × u16) | EWRAM `0x02000458` | handler for `BEAR` writes here |
| Techniques (12 × u16) | EWRAM `0x02000470` | handlers for FUZZY/WUZZY/WAZZA write here |
| Current-location byte | IWRAM `0x03004988 + 0x04` (=`0x0300498C`) | used elsewhere; not a code input |
| Save-erase flag byte | IWRAM `0x03004988 + 0x51` (=`0x030049D9`) | set by `ERAZE` handler |
| Font/charset bank (decoded) | ROM `0x010E9C0` region | runs of `0xA4–0xBD` (A–Z), `0x02–0x1B` (a–z), `0x97–0xA0` (0–9) |
| Character encoding (derived from buffer + font bank) | — | `A–Z = 0xA4–0xBD`, `a–z = 0x02–0x1B`, `0–9 = 0x97–0xA0`; injective |

Savestate layout used for RAM diffs (mGBA `.ss1` PNG, zlib `gbAs` chunk, 397,312 bytes): IWRAM at file `0x19000`, EWRAM at `0x21000`. The money address was found by diffing a `$30.00` state against a `$999,999.99` state (EWRAM `+0x454`: `b8 0b 00 00` → `ff e0 f5 05`); the name buffer by diffing `PLAYA` vs `AAAAA` at EWRAM `+0x494` (`b3 af a4 bc a4` vs `a4 a4 a4 a4`).

## 5. Algorithm

The validator at `0x0802A5FC` is, in pseudocode:

```c
// r9 = 0x03004988 (global state), r5 = state->slot_index (byte at +0x4C)
// if (slot > 0x1AA) player = 0; else player = *(0x02010848 + slot*4);
// name = (u8*)(player + 0x80);           // 0x02000494 for slot 0
for (i = 9; i >= 0; i--) {                // 0x802A648, decrement at 0x802A7A8
    const char *code = code_ptrs[i];      // table at 0x02016F78
    if (strcmp_encoded(name, code)) {     // helper at 0x0802A5DC
        goto handler[i];                  // jump table at 0x0802A67C
    }
}
return;                                   // no code matched
```

`strcmp_encoded` is a byte-exact, NUL-terminated comparison (no checksum, no masking, no case folding):

```c
int cmp(const u8 *a, const u8 *b) {
    while (*a == *b) {
        if (*a == 0) return 1;            // both ended => match
        a++; b++;
    }
    return 0;
}
```

The code strings in the table are stored with the game's font encoding (uppercase letters `+0x63`, digits on a separate run), e.g. `PLAYA` = `B3 AF A4 BC A4 00 00 00`, `XTRA0` = `BB B7 B5 A4 97 00 00 00`. The name-entry UI writes the same encoding into the buffer, so a typed name can be compared directly.

Effects are dispatched to five distinct handlers by index:

| Index | Code | Handler | Effect (derived from handler code; cross-checked with published list) |
|---:|---|---|---|
| 0 | `FUZZY` | `0x0802A6A4` | grants technique set 1 (loop over 12 slots, offset `12*idx`) |
| 1 | `WUZZY` | `0x0802A6A4` | grants technique set 2 |
| 2 | `WAZZA` | `0x0802A6A4` | grants technique set 3 |
| 3 | `BEAR` | `0x0802A6D0` | copies 10 item IDs from `0x082CF832` into `player+0x5C` |
| 4 | `PLAYA` | `0x0802A70C` | writes `0x05F5E0FF` to `0x02000454` (max money) |
| 5 | `ERAZE` | `0x0802A718` | sets save-erase flag byte at `0x030049D9` |
| 6 | `DAMAX` | `0x0802A722` | writes `0x7F` to 8 stat bytes and `0xFF00` to HP/stamina halfwords |
| 7 | `XTRA0` | `0x0802A73E` | inserts item ID `0x0310` (Custom Character) in first free technique slot |
| 8 | `XTRA1` | `0x0802A73E` | inserts item ID `0x0312` (Custom Face) |
| 9 | `XTRA2` | `0x0802A73E` | inserts item ID `0x0313` (Custom Controls) |

The `XTRA*` handler searches `player+0x44` for the first `0xFFFF` slot and writes index-specific IDs (`0x0310`, `0x0312`, `0x0313`) — these match the Japanese item table (かすたむきゃら / かすたむかおづら / かすたむそうさ).

## 6. Tables

**Encoded code table at ROM `0x0810C184`** (8-byte records, decoded through the font charset):

| ROM address | Code | Record bytes |
|---|---|---|
| `0x0810C184` | `PLAYA` | `B3 AF A4 BC A4 00 00 00` |
| `0x0810C18C` | `FUZZY` | `A9 B8 BD BD BC 00 00 00` |
| `0x0810C194` | `WUZZY` | `BA B8 BD BD BC 00 00 00` |
| `0x0810C19C` | `WAZZA` | `BA A4 BD BD A4 00 00 00` |
| `0x0810C1A4` | `BEAR`  | `A5 A8 A4 B5 00 00 00 00` |
| `0x0810C1AC` | `ERAZE` | `A8 B5 A4 BD A8 00 00 00` |
| `0x0810C1B4` | `DAMAX` | `A7 A4 B0 A4 BB 00 00 00` |
| `0x0810C1BC` | `XTRA0` | `BB B7 B5 A4 97 00 00 00` |
| `0x0810C1C4` | `XTRA1` | `BB B7 B5 A4 98 00 00 00` |
| `0x0810C1CC` | `XTRA2` | `BB B7 B5 A4 99 00 00 00` |

**Pointer table at EWRAM `0x02016F78`** (index = validator loop index, 9→0):

| idx | Code | Pointer |
|---:|---|---|
| 0 | `FUZZY` | `0x0810C18C` |
| 1 | `WUZZY` | `0x0810C194` |
| 2 | `WAZZA` | `0x0810C19C` |
| 3 | `BEAR`  | `0x0810C1A4` |
| 4 | `PLAYA` | `0x0810C184` |
| 5 | `ERAZE` | `0x0810C1AC` |
| 6 | `DAMAX` | `0x0810C1B4` |
| 7 | `XTRA0` | `0x0810C1BC` |
| 8 | `XTRA1` | `0x0810C1C4` |
| 9 | `XTRA2` | `0x0810C1CC` |
| 10 | terminator | `0x00000000` |

**Key-mask/button-code tables:** none found; the only input surface is the on-screen keyboard. There is no hidden debug screen reachable by button input: the title, story setup, all eight Start menus (Item, Status, Strategy, File, Technique, Log, Options, Mode), the Status→Name screen and the name-entry screen were walked; the Options screen exposes only the normal configurable fields (Speed, Gravity, WpnThrow, Obstacles, AtkBalance, Restock, WpnBalance, Enemies, Techniques, DefBalance, Damage) with `OK / Change / Default / Cancel`. The Japanese guide's "debug stage" requires writing `0x23`/`0x24` to `0x0300498C` with a memory editor — out of scope and not developer-intended input.

## 6b. Enumeration

**Space definition.** Each accepted input is an 8-byte, NUL-terminated string in the game's font encoding, compared byte-exactly against a fixed table. The name-entry field is 8 characters wide; codes are 4–5 characters. Charset (derived from the name buffer and the font bank at `0x010E9C0`): `A–Z → 0xA4–0xBD`, `a–z → 0x02–0x1B`, `0–9 → 0x97–0xA0`; symbols occupy distinct values. The mapping is injective over all symbols used by the codes, so there are **no case/spelling aliases**.

**Space size and closure.** The accepted set contains exactly **10 values**. This was established three independent ways:

1. **Validator bound:** the loop counter `r6` is initialised to 9 (`0x802A648`) and decremented to 0 (`0x802A7A8`); there is no path that indexes beyond 9.
2. **Table size:** the pointer table at `0x02016F78` has exactly ten non-null entries followed by `0x00000000`; a string search over the whole 4 MiB for the encoding of each published code found each exactly once in the code-table region (plus dialogue copies of `PLAYA` at `0x010EACF`/`0x010EAF4`, which are text, not codes).
3. **No generator:** no encoder, checksum, key table or PRNG is involved — the compare helper at `0x0802A5DC` is a plain byte loop, and the dispatch table has exactly ten entries.

**Published-code cross-check.** The ten ROM codes are identical to the union of the GameFAQs and GamingTarget lists (`PLAYA`, `FUZZY`, `WUZZY`, `WAZZA`, `BEAR`, `ERAZE`, `DAMAX`, `XTRA0`, `XTRA1`, `XTRA2`). The digit bytes `0x97/0x98/0x99` are keyboard `0/1/2` (verified: typing `XTRA0` produced buffer `BB B7 B5 A4 97 00 00 00`), so the published `XTRA0/1/2` labels are correct — they are *not* `XTRA4/5/6` despite the apparent `+0x63` letter offset. No published literal was absent or misspelled in the ROM.

**Novel codes.** None exist. Because the accepted set is provably closed at ten values and all ten are published, it is impossible to mint a code absent from every published list for this SKU. This is the bounded negative result for the §0.2 novel-code deliverable: the search space (entire 4 MiB for encoded code strings; validator loop bounds; pointer-table length; charset injectivity) was enumerated and is reported with counts above. The Japanese katakana code names are a different regional SKU's strings and are not present in this image.

**Bounds proven by rejection.** With a clean state (money `0x00000BB8` = $30.00, stats `0x0F`, name `Alex`), entering `XXXXX` through the real UI and pressing OK left money at `0x00000BB8` and stats at `0x0F0F…` (screenshots `reject_xxxxx.png`, `reject_final.png`; state `ss5`). No handler ran. A lowercase spelling cannot match either, because `p` encodes to `0x11` and `P` to `0xB3` (distinct bytes), and the compare helper has no case folding.

**Accepted-code proofs (dynamic).**

- `PLAYA`: a write watchpoint on `0x02000454` hit at PC `0x0802A712` with old value `0x00000BB8`, new value `0x05F5E0FF`, and `r7 = 0x02000494` (the name buffer) — i.e. the validator's PLAYA handler at `0x0802A70C` wrote max money. Screenshot `playa_result.png` shows `$999999.99` and the name changed to `PLAYA`.
- `DAMAX`: state `ss7` vs clean `ss1` — bytes at `0x02000414..0x0200041B` changed from `0F 0F 0F 0F 0F 0F 0F 0F` to `7F 7F 7F 7F 7F 7F 7F 7F`, and HP/stamina at `0x0200041C/0x02000420` from `0x4000` to `0xFF00`. Screenshot `damax.png`.
- `XTRA0`: name accepted and changed; the index-7 handler at `0x0802A73E` writes item ID `0x0310` into the first free `0xFFFF` technique slot at `player+0x44`.

## 7. Validation evidence

- **Observed** (emulator/screenshot/RAM): title and all menus walked; `PLAYA` → `$999,999.99`; `DAMAX` → stats `0x7F`, HP `0xFF00`; `XTRA0` → name accepted; `XXXXX` → no effect; watchpoint hit at `0x0802A712` with `r7 = name buffer`; savestate diffs locating money `0x02000454`, name buffer `0x02000494`, stats `0x02000414`.
- **Derived** (disassembly): validator `0x0802A5FC`, compare helper `0x0802A5DC`, loop bounds and dispatch `0x0802A664`/`0x0802A670`, handler table `0x0802A67C`, all ten handler bodies, code table and pointer tables, encoding from buffer bytes and font bank.
- **Inferred** (not exhaustively exercised): the exact in-game item names granted by `BEAR`/`FUZZY`/`WUZZY`/`WAZZA`/`XTRA*` were taken from the published lists and the handler's numeric IDs, not from opening the inventory after each code; `ERASE`'s flag byte was read from the handler, not followed through a full save-erase cycle. These do not affect the code-space conclusion.

Header/logo patching and the absence of ASCII text were handled explicitly (§0–§1), so the negative findings ("no password generator", "no debug menu", "no unpublished code") are bounded by the decoded text bank, the enumerated validator, and the full menu walk rather than by a failed string search.

## 8. Unknowns

- The exact reason the header logo/complement were patched (source of the dump) is unknown; the crt0 and all game code appear stock.
- The per-code technique/item sets for indices 0–3 were confirmed as table copies/offset writes, but the resulting inventory screens were not individually screenshotted.
- Whether `ERAZE` requires an additional confirmation step beyond the flag byte at `0x030049D9` was not exercised (would destroy the disposable save).
- The Japanese SKU's katakana code table was not present in this ROM and was not analysed.

## 9. Tooling

- `mgba -3` (Xvfb `:318`, `SDL_AUDIODRIVER=dummy`) for all dynamic work; `mgba -d` under a pseudo-TTY for CLI debugging (the GDB stub on port 2345 was occupied by another process, so the CLI debugger was used instead).
- `xdotool` XTEST input; screenshot feedback loop (`scrot`, Pillow) to locate the orange keyboard cursor and drive the 14×5 name-entry grid (`typer.py`, `try_code.py`).
- mGBA `.ss1` savestates parsed with Python `zlib` (`ss.py`); RAM diffs for address discovery.
- `arm-none-eabi-objdump -M force-thumb` for disassembly; Capstone for pointer/BL/literal xref scans (`xrefs.py`).
- Python scripts: `find_codes.py` (encoding brute force), `analyze_ss.py` (VRAM/RAM analysis), `gdb.py` (unused GDB-RSP client), `dbg.py` (pty debugger controller), `watch_trace.py` (money watchpoint), `test_accept.py` (acceptance breakpoint), `sweep.py` (menu walk).
- No copyrighted ROM data or extracted assets are redistributed here; only hashes, addresses, algorithms and tool scripts are published.

---

**Cleanup note:** all processes started for this engagement were terminated by PID, and generated `.sav` / `.ss*` files were removed from the ROM folder. `roms/INDEX.md` was not modified.
