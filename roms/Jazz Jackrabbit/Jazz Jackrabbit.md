# Jazz Jackrabbit (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Jazz Jackrabbit.gba` (4,194,304 bytes / 0x400000) |
| Header title | `JAZZJACKRABB` |
| Game code / maker | `AJJE` / `0A`, revision 0x00 |
| Header checksum | 0x0000 (rebuilt header); complement byte 0x57 |
| MD5 | `db413093143aa1e05e81bcb52934360f` |
| SHA-1 | `1055efdb1363245fdf8a30127485adc85b137a76` |
| SHA-256 | `3733be3e9411ec848fc42c5920969c61ac7ba9f8beb5bf859bde19e0d3e230b5` |
| Embedded headers | second Nintendo-logo hit at file `0x53A0` with all-zero title/code (multiboot stub, not a second game) |
| Patch/trainer | **Yes — scene cracktro.** Entry word `0xEA0FA67E` branches to VMA `0x083E9A00` (file `0x3E9A00`) instead of the stock `0x080000C0`. The stub at `0x083E9A00` clears OAM, copies a segment loader into IWRAM, and decompresses tagged segments ("0nan", "0gge", "tixe") using a lookup at `0x083E9AC0`. Boot shows a "BORISIA is proud to present … december 03 of 2002" splash, then Jaleco/Epic legal text. No cheat menu is added by the cracktro. |

## 2. Executive summary

This GBA port has **no password/entry screen, no hidden debug menu, and no unlockable button menu**. All developer-intended cheats are **12-button sequences** entered while **paused during gameplay** (five codes) or on the **main menu** (one code). There are exactly **six** accepted sequences in the whole ROM, stored as plain arrays of active-high key masks (`u16` each):

- one 120-byte table at `0x083DC938` = 5 codes × 12 masks, checked by `0x0830F5C8` with a 5-way jump table at `0x083DC9B0`;
- one 24-byte table at `0x083DB338` = 1 code × 12 masks, checked by `0x08309F28`.

Both validators use the same simple algorithm (§5): copy the expected masks to the stack, shift a 12-entry key-history array, compare all 12 entries, dispatch an effect, then clear the history. The six sequences are **exactly** the six published GBA codes (3rd party cheat indexes); no unpublished valid sequence can exist because both tables are closed lookup sets. CodeBreaker/GameShark entries (memory edits) and the DOS/PC codes (`BACKSPACE+P`, `F10+F11+F12`) found in web searches do **not** apply to this SKU and are out of scope.

All six codes were entered in mGBA and confirmed by RAM reads (see §6b). Wrong 12-button combinations were entered and rejected with unchanged flags, proving the bounds.

## 3. How to reproduce

* Emulator: mGBA (`mgba -3`), Xvfb `:319`, `SDL_AUDIODRIVER=dummy`.
* Keymap used: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows. Hold ~90 ms, gap ~70 ms per press.
* Path to the five pause codes: boot → skip cracktro/legal screens → title → Start → slot 1 → **CAKEWALK/NORMAL** → skip the "Chameleon World / Level One" intro and the two dialogue boxes with A → gameplay → **Start** (real `PAUSED` panel with SPACE CREDITS/KEYS settings). Enter a sequence there.
* Path to the Level Select code: on the **menu screen** where the key-history buffer `0x03003A1C` is live (reachable from the title/save-file menus), press the sequence.
* RAM evidence: savestate `gbAs` chunks are PNG-zlib compressed; `zlib.decompress` yields 0x61000 bytes with VRAM at `0x1000`, IWRAM at `0x19000`, EWRAM at `0x21000`. Or use mGBA's `-d` PTY debugger (`r/2`, `x/2`, `w/2`, `watch/*`).

## 4. Address map

| Address (VMA) | File offset | Meaning |
|---|---|---|
| `0x08000000` | `0x000000` | Rebuilt header; entry word points to cracktro |
| `0x083E9A00` | `0x3E9A00` | Cracktro/decompression stub entry |
| `0x083E9AC0` | `0x3E9AC0` | Segment tag→address lookup table used by stub |
| `0x0830F5C8` | `0x30F5C8` | **Validator A** (5 pause-screen codes); called from `0x0831049E` |
| `0x083DC938` | `0x3DC938` | Validator A code table: 5 × 12 `u16` masks (120 bytes) |
| `0x083DC9B0` | `0x3DC9B0` | Validator A 5-entry effect jump table |
| `0x08309F28` | `0x309F28` | **Validator B** (Level Select code); called from `0x0830AAE0` |
| `0x083DB338` | `0x3DB338` | Validator B code table: 1 × 12 `u16` masks (24 bytes) |
| `0x0831A570` | `0x31A570` | Word-copy helper used by both validators to load tables onto the stack |
| `0x083189D0` | `0x3189D0` | Sound-effect dispatcher (arg 7 for validator B, 17 for validator A) |
| `0x03000D12` | — | "new key" count; validator skips if 0 |
| `0x03003C14` | — | Validator A key-history ring (12 × `u16`, newest appended at +22) |
| `0x03003A1C` | — | Validator B key-history ring (12 × `u16`) |
| `0x0200755C` / `0x0200756C` | — | current save slot / save-struct pointer (validator B reads this) |
| `0x030058F0` | — | Space credits (`u16`) |
| `0x030058F2` | — | infinite-health flag (`u8`) |
| `0x03002566` | — | health (`u8`, 0xFF = full) |
| `0x030034E4..E9` | — | weapon-owned bytes; `0x030034DC` carrots; `0x0300351A` ammo |
| `0x030059BD` | — | Level Select unlock flag (`u8`) |
| `0x02005C00+` | `0x205C00+` | Decompressed UI text bank (plain NUL-padded ASCII, see §9), ~0x1600 bytes |

## 5. Algorithm

Both validators are identical in structure (Thumb, ROM addresses above):

```
validator(table_ptr, table_len):
    copy(table_len bytes from table_ptr -> stack)
    if count_at_0x03000D12 == 0: return
    shift history[0..11] left by one (history[i] = history[i+1])
    history[11] = current_key_mask          # active-high ~KEYINPUT & 0x3FF
    for each table entry e (index i):
        match = true
        for j in 0..11:
            if history[j] != e.keys[j]: match = false; break
        if match: dispatch effect i; clear history[0..11]; return
    # no match: leave history intact
```

Key masks are active-high GBA bits: A=0x001, B=0x002, Select=0x004, Start=0x008,
Right=0x010, Left=0x020, Up=0x040, Down=0x080, R=0x100, L=0x200.

Validator A dispatch (`0x0830F63C`, `cmp r4,#4; bls`, jump table `0x083DC9B0`):
* index 0 → `0x0830F654`: set `0x030058F2 = 1` (infinite health).
* index 1 → `0x0830F660`: set weapon bytes `0x030034E5..E9 = 1`, set ammo via `0x082FB810` (100 / 10 / 100 / 5 / 5), carrots `0x030034DC += 10` capped at 99, write `0xFF` to `0x0300250C+90`; play sound 17.
* index 2 → `0x0830F6CC`: if save slot ≤3 and save+28 == 0, set save+28=1 and credits += 500 (0x1F4).
* index 3 → `0x0830F6F8`: same gate, credits += 1000 (0x3E8).
* index 4 → `0x0830F730`: same gate, credits += 5000 (0x1388).
* On any match, `0x0830F75A` zeroes the 12 history entries.

Validator B dispatch (`0x08309F96`): play sound 7; if `0x030059BD == 0`, increment the byte at the save pointer and set `0x030059BD = 1`; clear history.

## 6. Tables

Key masks in the table are stored little-endian `u16`, one per button press.

| # | Sequence (buttons) | Table entry | Effect |
|---|---|---|---|
| 0 | `L L ← R → R ↑ ↓ ← R → L` | `0x083DC938`, masks `200 200 020 100 010 100 040 080 020 100 010 200` | Infinite health (flag `0x030058F2=1`) |
| 1 | `L R ← R L → L R L R ← R` | `0x083DC950`, masks `200 100 020 100 200 010 200 100 200 100 020 100` | All weapons / ammo / +10 carrots |
| 2 | `→ ← → ← L R ↑ ↑ R R L L` | `0x083DC968`, masks `010 020 010 020 200 100 040 040 100 100 200 200` | +500 Space Credits (once/save) |
| 3 | `↑ ↓ ↑ ↓ ← → L R L R R L` | `0x083DC980`, masks `040 080 040 080 020 010 200 100 200 100 100 200` | +1000 Space Credits (once/save) |
| 4 | `↑ → ↓ ← L L → ← R R L L` | `0x083DC998`, masks `040 010 080 020 200 200 010 020 100 100 200 200` | +5000 Space Credits (once/save) |
| 5 | `← ↓ L L ↑ ↓ R → ↑ → L R` | `0x083DB338`, masks `020 080 200 200 040 080 100 010 040 010 200 100` | Unlock Level Select (`0x030059BD=1`) |

Note codes 2–4 are one-shot per save slot (flag at save+28), as published. Codes 0, 1 and 5 are idempotent once their flag is set.

**Out-of-scope / unverified web hits:** CodeBreaker/GameShark codes (`33002566 00FF`, `830058F0 C350`, etc.) are memory edits, not in-game cheats; the 3rd party cheat indexes PC page's `BACKSPACE+P` and `F10/F11/F12` belong to the DOS/console originals and do not appear in this GBA image under any encoding checked.

## 6b. Enumeration

**Space definition.** Two closed lookup tables, no generator/checksum:
* Validator A: **5** records × 12 key masks = 60 stored masks (120 bytes at `0x083DC938`), plus a 5-entry effect jump table.
* Validator B: **1** record × 12 key masks = 12 stored masks (24 bytes at `0x083DB338`).
* Total representable accepted inputs = **6**, drawn from a 10-symbol button alphabet (`A B Select Start ← → ↑ ↓ L R`) to the 12th power (~10^12 possible press sequences). All six accepted sequences are listed in §6; there is no unadvertised combination, no checksum field, no reserved bits, and no algorithmic encoder—both tables were read exhaustively and the dispatch bound (`cmp r4,#4`) limits validator A to exactly five actions.

**Novel codes.** **None can be minted.** This is a closed table system (§0.2's "lookup" case, §7.1): the entire accepted set is the six entries above, and each is already published. The §0.2 equivalent for a button-code system was performed instead: every action branch and sequence length was enumerated from the jump table and both `memcpy` lengths (24 and 120 bytes = 12 presses per code, no shorter/longer variants), and undocumented combinations were entered in the emulator (below).

**RAM-verified effects** (mGBA, savestate diff / direct reads; baseline = pause/menu state):

| Code | Before → After (address) | Result |
|---|---|---|
| 500 cr | credits `0x030058F0`: `0 → 500` | accepted |
| 1000 cr | credits: `0 → 1000` | accepted |
| 5000 cr | credits: `0 → 5000` | accepted |
| All weapons | `0x030034E4..E9`: `0,0,0,0,0,0 → 0,1,1,1,1,1`; carrots `0 → 10`; ammo `0 → 100` | accepted |
| Infinite health | `0x030058F2`: `0 → 1`; invuln timer `0x03002504`: `151 → 65535` | accepted |
| Level Select | `0x030059BD`: `0 → 1` | accepted |

**Bounds proven by rejection:**
1. Publishing a wrong reading of the 500-credit code (shoulder `R,L,R,L` instead of D-pad `→,←,→,←`) entered all 12 masks into history `0x03003C14` but left credits at 0 and the history uncleared — rejected. Re-entering the correct D-pad version gave 500. This proves both the exact alphabet mapping and that only the table entries are accepted.
2. The Level Select sequence entered on the **pause** screen (where validator B is not wired to the active history buffer) produced no flag change and left the history intact.
3. A wrong 12-press sequence (`A` ×12) on the menu where validator B runs left `0x030059BD = 0`, while the correct sequence on that same screen set it to 1.
4. No effect was observed for any sequence of a length other than 12 — both validators compare exactly 12 history entries (`cmp r3,#11`) and there is no prefix/short-code path.

## 7. Validation evidence

* **Observed (emulator + savestate RAM):** all six effects in the §6b table; the two rejection cases; menu text bank contents; cracktro/legal/title/save-select/difficulty/gameplay/pause screens.
* **Derived (disassembly):** table addresses and contents, validator algorithms, dispatch bounds and effect addresses, history-buffer addresses, save-flag gates.
* **Inferred:** the menu screen on which validator B is called (from the caller at `0x0830AAE0` and the live `0x03003A1C` history); the exact label "Level Select" for flag `0x030059BD` (from the effect code incrementing a save-byte and the published unlock description; the unlocked menu item itself was not re-opened for a screenshot).
* **Negative results:** decompressed UI text bank at `0x02005C00+` was dumped in full (all strings, §9) — no `PASSWORD`, `CHEAT`, `DEBUG`, `SECRET`, `UNLOCK`, `CODE`, `BONUS` or `INVINC` string exists in it. The two 12-mask tables are the only such arrays found in the 4 MiB image. Therefore there is no password screen and no hidden debug menu in this ROM.

## 8. Unknowns

* The main-menu screen itself was not captured with the Level Select item visibly enabled; the unlock is proven by the flag write, not by a screenshot of the now-selectable menu entry.
* The save-byte incremented by validator B (`ldr r0,[0x0200756C]; ldrb r1,[r0]; add r1,#1; strb r1,[r0]`) was not tracked to a named UI counter.
* The cracktro's decompressor was only characterized at the stub level; it was not necessary to reverse it fully because the game's code runs directly from ROM and the UI text is decompressed into EWRAM at boot.

## 9. Tooling

* `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings` for Phase 0.
* `python3` + `struct`/`zlib` to parse savestate `gbAs` chunks and read/diff EWRAM/IWRAM; helper scripts `snap.py`, `load.py`, `press.py`, `testcodes.py` in `/tmp/jazz`.
* `arm-none-eabi-objdump -M force-thumb` for static Thumb disassembly; custom Python BL/pointer scanners.
* mGBA `-d` CLI debugger driven over a Python PTY (`ptylaunch.py`, `dbg.py`) for `r/1|2|4`, `x/2`, `w/*`, `dis/t`, `watch/*`, `break`.
* UI text bank (decoded from EWRAM, all ASCII): `MAIN MENU` (New Game / Continue / Tournament / Settings / Level Select), `LEVEL SELECT`, `SELECT DIFFICULTY` (CAKEWALK / NORMAL / PRETTY HARD / WAY TOO HARD), `TOURNAMENT`, `MULTI-PAK`, `SINGLE-PAK`, `NEW GAME`, `CONTINUE`, `MULTI-PAK SETTINGS`, `SINGLE-PAK SETTINGS`, `SETTINGS`, `LEVEL SETTINGS`, `CONTROL CONFIGURATION`, `WEAPONS/ITEMS SETUP`. Pause panel adds `PAUSED`, `KEYS:`, `SPACE CREDITS:`, `BRIGHTNESS:`, `CONTROL TYPE:`, `MUSIC VOL:`, `SFX VOL:`.

## 10. Legal note

No ROM image or copyrighted graphics/audio are redistributed. Only addresses, hashes, button sequences and analysis tooling are published.
