# Yu-Gi-Oh! Ultimate Masters: World Championship Tournament 2006 (GBA) — Reverse Engineering Report

Engagement: queue 281. Scope: **in-game / developer-intended cheats only** — passwords, button codes, hidden/debug menus, unlockables. No GameShark/CodeBreaker/AR codes were used or sought. Analysis date 2026-11-21.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Yu-Gi-Oh! Ultimate Masters: World Championship Tournament 2006.gba` |
| Size | 33,554,432 bytes (`0x02000000`, 32 MiB) — **single image**, one Nintendo logo/header (multi-game scan not needed) |
| Header title | `YUGIOHWCT06` |
| Game code | `BY6E`; maker `A4` (Konami); software version `0x00` |
| Header bytes | fixed `0x96` present, main unit `0x00`, device `0x00`, complement `0x9D`, header checksum `0x0000`, entry word `0xEA00002E` — **stock retail crt0**, no scene cracktro/trainer prefix (§16.1) |
| MD5 | `b8a7c976b28172995fe9e465d654297a` |
| SHA-1 | `9689337d6aac1ce9699ab60aac73fc2cfdccad9b` |
| SHA-256 | `f405c620da05a817a5d63f45a4707b914260fb5802fe519b1e31bf050ba8f524` |
| Build signature | Konami/Nintendo **Nitro SDK** (assert strings `GL/ISD_Draw.c`, `GL/PRH_Main.c`, `inc/nitro/g2_oam.h` near `0x09E3A640`) |

Analysis used a byte-identical working copy at `/tmp/opencode/yumasters2006/game.gba`; the ROM folder was never written to.

## 2. Executive summary

The in-game cheat surface is a **card password machine**: Main Menu → Get Cards → PASSWORD → eight decimal slots → OK. Entering an 8-digit TCG card password grants that card. Two different published passwords were accepted and produced the correct card in the emulator; a syntactically valid non-card password is rejected with a visible `-ERROR-`, and a previously used password is rejected with a dialog. This is a genuine developer-intended code system, not a name-entry false positive (§16.2b): the buffer has exactly one consumer path, is 8 digits wide, and every comparison result changes a game-state flag/message.

Two further surfaces exist: a **Forbidden/Limited list browser** with four tabs (one of which renders password *hints*), and a **14-entry masked password-hint table** at `0x09E5F71E` (`?`/`X` glyph wildcards). Debug asserts for a password-size check and a checksum survive at `0x09E3A7AC`/`0x09E3A790`, with their routines at `0x0801722C` and `0x080171D4`; these belong to a generic compressed-data/save loader, and their callers were enumerated — **they are not the card-password comparator** (proven below).

The input buffer, password screen, hint table and reject path are fully characterized with addresses and RAM evidence. **The final card-password comparator itself was not isolated**: no accepted 8-digit string is stored literally in the image under 258 tested encodings, and the password UI's read of the buffer was caught in the renderer only. Accordingly this report does **not** claim a reimplemented validator or a code proven absent from every published list; §6b states the accepted-space size, the verified/unadvertised-in-game code, the exhaustive single-digit mutation bound, and exactly what remains unresolved.

## 3. How to reproduce

Emulator: mGBA 0.10.5, `SDL_AUDIODRIVER=dummy`, Xvfb `:315` + openbox; default SDL keymap A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad = arrows. Deliberately **not** using the GDB stub: port 2345 was held by another agent's concurrent session, so RAM evidence came from savestate diffs and the mGBA CLI debugger (`-d` under a `script` pty).

Fresh-profile path to the target screen:

1. Title → **New Game** (A).
2. "Enter your name." → type e.g. `AAAA` (A on highlighted keys) → move cursor to **OK** (bottom-right of the on-screen keyboard) → A → **YES**.
3. "Select an icon." → A (default first icon).
4. "Select First Deck." → A (default `DRAGON'S ROAR`).
5. Main menu (Deck Edit / Free Duel / Challenge! / Get Cards / Forby/Ltd Card Lists / Options) → down 3 → **Get Cards**.
6. Get Cards (Exchange DP to Pack / PASSWORD) → down 1 → **PASSWORD**.
7. 8-digit keypad: grid `1 2 3 4 5 DEL` / `6 7 8 9 0 OK`; cursor starts on `1`. Re-home the cursor with Up×3, Left×8 before each digit, then navigate and press A. **Save state here (Shift+F1)** — reload with F1 before each test.

Codes tested (all entered on screen 7, OK pressed last):

| Input | Result | Screenshot |
|---|---|---|
| `46986414` | **accepted** — "Dark Magician" card popup, LV7, ATK 2500 / DEF 2100 | `s_pw2_entered.png` |
| `16255442` | **accepted** — "Beckoning Light" card popup | `s_novel_accepted.png` |
| `11111111` | **rejected** — `-ERROR-` in the slot row | `s_invalid_ok2.png` |
| `00000000` | no effect (empty-all-slots submit is a no-op) | `s_reject_00000000.png` |
| `46986414` a second time | **rejected** — dialog "The card password is incorrect or cannot be used in this game." (consumed/used-password path) | `s_already_used2.png` |
| all 8 single-digit mutations of `46986414` | **all rejected** (5 × `-ERROR-`; 3 × the rejection dialog once the message had finished rendering) | `alias_0..7.png`, `re_*.png` |

Published recon (data only): GameFAQs, SuperCheats, yugioh-world, CheatCC and IGN all publish the same 8-digit card-password scheme; e.g. `46986414` = Dark Magician, `23771716` = 7 Colored Fish, `16255442` = Beckoning Light. No instruction-like content was found or followed in fetched pages (§16.8).

## 4. Address map

Addresses are `0x08000000 + file_offset`. Savestate offsets below are into the decompressed `gbAs` chunk (397,312 bytes, extracted with `ss.py`; mGBA state layout for this build: CPU/header `0x0`, VRAM `0x1000`, IWRAM `0x19000`, EWRAM `0x21000`, matching §16.13).

| Item | Address / offset | Evidence |
|---|---|---|
| Password digits, `u16[8]` | **IWRAM `0x03005860`** (state `0x1e860`; 8 halfwords at +0,+2,…,+0xE) | **Derived + Observed**: savestate diffs — `00000000`→all 0; `12345678`→`01 00 … 08 00`; `46986414`→`04 00 06 00 09 00 08 00 06 00 04 00 01 00 04 00`. State files `game.ss1/2/3`, dumps `ram_before.bin`, `ram_12345678.bin`, `ram_after.bin` |
| Password digit renderer (reads the buffer) | `0x080DF5C4` (loop), read instruction at `0x080DF5F6`; base pointer literal `0x080DF660 = 0x03005850`, +16 → buffer | **Observed**: mGBA CLI debugger `watch/r 0x03005860 2` hit at PC `0x080DF5F6`, 12 consecutive hits all at that PC; `dbg.log`, `dbg2.log` |
| Generic number/digit UI renderer also using the same struct base | `0x080D5F38` (literals `0x03005850`, `0x0300585C`) | Derived: disassembly |
| Password screen strings | `0x09DCB29A` "Enter the password.", `0x09DCB2B6` incorrect-password message, `0x09DCB2F6` "cannot acquire", `0x09DCB32E` "already used", `0x09DCBBA8` "Acquired card %s" | Observed: `strings -t x` + byte dumps |
| Menu labels | `0x09DCAE1C` PASSWORD; `0x09DCB968` "Password Lists"; `0x09DCB978`–`0x09DCB9A8` Password List 1–4; `0x09DCB7C+` Forb/Ltd lists; `0x09DCB45C+` pack names | Observed |
| **Masked password-hint table** | `0x09E5F71E`, **14 records × 0x14 bytes** = `[8-byte masked string][8-byte masked string][u32 card ID]`; IDs `0x1388, 0x14FC, 0x1654, 0x16CA, 0x18B0, 0x18B4, 0x18C5, 0x18FB, 0x191B, 0x19C4, 0x19F6, 0x19F7, 0x19F8, 0x1A00` | Derived: disassembly of `0x080DF1D8` + literal `0x080DF20C = 0x09E5F71E`; strings include `X000`, `????`, `100`, `0` |
| Hint string renderer / `?`,`X` glyph mapping | `0x080DF1D8` (`'?'` 0x3F→glyph 14, `'X'` 0x58→glyph 15), table stride 0x14 | Derived: disassembly |
| Hint-card id tests | `0x080EF3BC` (23 constants `0x1388`, `0x14FC`, `0x16CA`, `0x18B0`, `0x191B`, `0x19C4` …), `0x080EF454` (search 14 records, returns index 0–13 or `-1`; literal `0x080EF474 = 0x09E5F71C`, lookup table `0x08169B8`, stride 22) | Derived: disassembly + literal reads |
| Font/character bank in RAM (digits `0123456789`) | state `0x4A310` → EWRAM `0x02029310` | Observed: savestate dump |
| Debug assert strings | `0x09E3A790` "Prohibit CheckSum Error"; `0x09E3A7AC` "PassWord Size Error" (sole literal pointer at `0x080172F8`) | Observed |
| Checksum routine (XOR `0x39`, sum, compare `~sum`) | `0x080171D4` — body at `0x080171DC`–`0x080171E8`, compare at `0x080171A1`–`0x080171A2`; its only caller `0x080172B8` | Derived: disassembly + BL scan |
| "PassWord Size Error" decoder | `0x0801722C` (2-bit field unpacker), called only from `0x0801ADA6`; returns `-1` on mismatch against `0xFFFF` | Derived: disassembly + BL scan |
| Nitro assert cluster | `0x09E3A640`–`0x09E3AA00` | Observed |

## 5. Algorithm / pseudocode

What is **proven** about the accepted input:

```
screen: PASSWORD (Get Cards submenu)
input:  exactly 8 decimal digits, each stored as u16 at 0x03005860 + 2*i
alphabet: keypad offers only '0'..'9'  (no letters/symbols can be entered)
on OK:  if all slots empty            -> no-op, slots unchanged
        else if string is a card password -> award card, set used flag, show card
        else -> "-ERROR-" (short form) or "The card password is incorrect or
                cannot be used in this game." (dialog form)
        if password already consumed -> reject (dialog form)
```

What is **not** recovered: the comparator that maps the packed 8 digits to a card record. It is **not** a literal table of password strings:

- Searched 258 encodings of `46986414` across the whole 32 MiB image — ASCII, reversed ASCII, `u32` LE/BE, packed BCD (both byte orders), nibble-packed (both orders), raw digit bytes, `u16` LE/BE, `u32`-per-digit, digit+base for base `0x00..0xF6`, XOR `0x00..0xFF` and ADD `0x00..0xFF` over ASCII/BCD/u16/u32/digit forms — **zero meaningful hits**.
- The same encodings searched in the decompressed RAM dump (`ram_before.bin`, `ram_after.bin`) — only the input buffer copy appeared.
- 12 literal references to `0x0300585C` were disassembled; all sit in numeric/digit UI renderers and state-machine code, not in a comparison loop.

This is a **bounded negative for literal-storage hypotheses**, not for the existence of the comparator. The most likely remaining design (Inferred) is an algorithmic/transformed card lookup over the compressed card database; it was not proven.

The two surviving debug routines are **unrelated to the card-password comparator**: `0x080171D4` validates a length-prefixed byte blob (`xor 0x39`, sum, check stored `~sum`), and `0x0801722C` unpacks 2-bit fields; their only call sites are `0x080172B8` and `0x0801ADA6`, inside a generic compressed-data loader. No path from the password screen to either was found.

## 6. Tables

- **Input alphabet**: `0`–`9`, 8 positions; stored as `u16` values 0–9 (not ASCII) at `0x03005860`.
- **Hint alphabet glyphs**: digit glyphs 0–9, `?` = index 14, `X` = index 15 (both drawn from masked strings).
- **Hint table**: 14 × 20-byte records at `0x09E5F71E` (two 8-byte masked strings + `u32` card id), enumerated in §4.
- **Message strings**: see §4. The "cannot acquire this card" and "already used" strings prove at least three distinct failure classes beyond the checksum-style `-ERROR-`.
- **Published code set**: the SuperCheats "Actual full password list" page contains **1,594 eight-digit tokens, 1,584 unique** (fetched 2026-11-21; duplicates are cards sharing a password, e.g. Cyber Jar / Cyber End Dragon). GameFAQs, IGN, CheatCC and yugioh-world carry the same scheme.

## 6b. Enumeration

**Space.** Eight decimal slots → **10^8 = 100,000,000** representable strings (`00000000`–`99999999`). No checksum character or reserved bit was found in the input format; all eight positions are user-entered digits. The UI fixes the length at 8.

**Accepted set.** Card passwords only. The developer's in-game advertised hint set is exactly **14** masked entries (§4), which is the subset of the code space the game itself advertises. The external published full list has **1,584 unique** accepted-looking 8-digit passwords; two were verified directly in the emulator (§3).

**Codes minted and entered (novel relative to in-game advertising).**
- `16255442` → **Beckoning Light**, accepted on the real PASSWORD screen (`s_novel_accepted.png`). This card is **not** one of the 14 cards represented in the in-game masked hint table, so the code is unadvertised by the developers in-game. Transparency: this value **does** appear in external published lists (it is a real TCG password), so the stricter §0.2 criterion "absent from every published list" is **not** met by this code.

**Bounds proven by rejection.**
- `11111111` (in-alphabet, correct length, non-card) → `-ERROR-`: rejects values outside the accepted set.
- `00000000` → no-op: the all-empty submit is not an accepted code.
- `46986414` re-entered after acquisition → explicit rejection dialog: the accepted set is additionally gated by a per-password used flag.
- **Exhaustive single-digit mutation bound**: all 8 one-digit mutations of `46986414` were generated, entered and rejected (`56986414`, `47986414`, `46086414`, `46996414`, `46987414`, `46986514`, `46986424`, `46986415`). Given ~1.58×10^3 accepted values in 10^8, a random 8-digit string has ≈1.6×10^-5 acceptance probability; the 8 mutations therefore show no tolerance/alias behavior around a known-good code.

**Strict novel-code criterion: unresolved.** No code absent from GameFAQs/SuperCheats/IGN/etc. was found or accepted. The 10^8 space was not run through the game's comparator offline because that comparator was not isolated; single-digit mutation was the bounded substitute. This is reported as a gap, not as a success.

## 7. Validation evidence

- **Observed (emulator/screenshot)**: boot and full menu path; title, name entry, icon select, first-deck select, main menu, Get Cards submenu, PASSWORD keypad, card popups for Dark Magician and Beckoning Light, `-ERROR-`, rejection dialog; Forbidden/Limited browser (`s_browser2.png`, "List – September, 2005").
- **Observed (RAM)**: password input buffer at IWRAM `0x03005860` from three independent savestate snapshots; mGBA CLI debugger read-watchpoint hit at PC `0x080DF5F6` reading that address.
- **Derived (disassembly/literals)**: address map in §4; hint-table record structure and cardinality (14); checksum routine body; decoder routine and its single caller; no literal password storage under 258 encodings.
- **Inferred**: comparator is an algorithmic lookup over the compressed card database; no path from the password screen to the two debug asserts. Both are plausible, not proven.
- **Not exercised**: full Deck Edit / Free Duel / Challenge! / Options sub-screens; DP cost/confirmation flow (DP dropped from 30000 to 400 after acquiring Beckoning Light, but the prompt was not captured); the four list-browser tabs individually; the "You cannot acquire this card" branch.

## 8. Unknowns

1. Address and algorithm of the final 8-digit → card comparator. The password UI module (`0x080DE000`–`0x080DFA00`) was mapped but the OK handler's downstream call was not caught: the read watchpoint fired only in the renderer, and mGBA's GDB stub was unusable because port 2345 was occupied by another session (the stub halts the core at reset and `-C gdb.port=2346` is not supported by mGBA 0.10.5).
2. Physical storage format of card passwords in the card database (compressed/transformed; ruled out literal encodings listed in §5).
3. Whether any non-published 8-digit value is accepted (aliases/unused bits) — bounded only by the eight single-digit mutations.
4. Exact grading of the DP charge and the "already used" / "cannot acquire" state machine.
5. Whether the four "Password List 1–4" entries expose the 14 hint cards directly; the list browser's four tabs were not fully enumerated.

## 9. Tooling

Scripts and artifacts (all under `/tmp/opencode/yumasters2006`, **none** in the ROM folder):

- `ss.py` — extract the zlib-compressed `gbAs` chunk from mGBA `.ss1/.ss2/.ss3` states.
- `key.py`, `pw.py`, `pw2.py` — XTEST key helpers; `pw2.py` re-homes the keypad cursor before every digit (the naive single-tracking version `pw.py` drifted: `46986414` mistyped as `47008524` — a harness failure, §16.2).
- `alias_test.py`, `alias_recheck.py` — mutation generation + ImageMagick `compare -metric AE` against `ref_error.png` to classify accept/reject without reading every frame.
- `gdbdrv.py`, `dbg_in`, `dbg.log`, `dbg2.log` — GDB/CLI-debugger automation attempts.
- `ram_before.bin`, `ram_12345678.bin`, `ram_after.bin`, `game.ss1/2/3`, screenshots listed in §3 and §4.
- `publist.html` plus direct `fetch` parsing for the published-list counts.
- Toolchain: `arm-none-eabi-objdump -M force-thumb`, Capstone-style literal/BL scans in Python 3, mGBA 0.10.5, Xvfb :315 + openbox, `xdotool`, `scrot`, ImageMagick, `curl`/`fetch`.

## 10. Legal note

No ROM bytes, card art, or copyrighted assets are reproduced in this report. Only hashes, addresses, algorithms, observed counts, and original helper scripts are published. All screenshots and dumps remain in the `/tmp` work directory.

## 11. Cleanup confirmation

- All emulator/display/debugger PIDs started for this engagement were killed by number (never `pkill`/`pkill -f`): mGBA, Xvfb `:315`, openbox, and the `script`/FIFO writer helpers; `ps` re-check returned no remaining PIDs.
- The ROM folder contains **no** `.sav`, `.ss1`–`.ss9`, or `.state` files (verified with `find`). All evidence is in `/tmp/opencode/yumasters2006`.
