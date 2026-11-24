# Yu-Gi-Oh! Ultimate Masters: World Championship Tournament 2006 (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

Engagement: queue 281. Scope: **in-game / developer-intended cheats only** — passwords, button codes, hidden/debug menus, unlockables. No GameShark/CodeBreaker/AR codes were used or sought. Analysis date 2026-11-21 (focused retry, display `:315`, work dir `/tmp/yumasters2`).

## 1. Target identity

| Field | Value |
|---|---|
| File | `Yu-Gi-Oh! Ultimate Masters: World Championship Tournament 2006.gba` |
| Size | 33,554,432 bytes (`0x02000000`, 32 MiB), single image |
| Header title / code | `YUGIOHWCT06` / `BY6E`, maker `A4` (Konami), version `0x00` |
| Header bytes | fixed `0x96`, complement `0x9D`, entry `0xEA00002E` — stock retail crt0 |
| MD5 | `b8a7c976b28172995fe9e465d654297a` |
| SHA-1 | `9689337d6aac1ce9699ab60aac73fc2cfdccad9b` |
| SHA-256 | `f405c620da05a817a5d63f45a4707b914260fb5802fe519b1e31bf050ba8f524` |
| Build signature | Konami/Nintendo Nitro SDK (assert strings near `0x09E3A640`) |

A byte-identical working copy was analysed in `/tmp/yumasters2/game.gba`; the ROM folder was never written to.

## 2. Executive summary

The in-game cheat surface is a **card password machine**: Main Menu → Get Cards → PASSWORD → eight decimal slots → OK. Entering an 8-digit TCG card password grants that card for DP.

This pass **closes the §0.2 gap** left by the earlier report:

1. **Comparator isolated and fully recovered.** The 8 digits are packed into a single u32 at IWRAM `0x03005870` with **one decimal digit per hex nibble** (e.g. `46986414` → `0x46986414`, *not* decimal `0x02CCE16E`). The search loop is at `0x080E02D0`; it de-obfuscates each card-record password with an LCG-derived XOR key (`0x080EF370` → `0x080EF35C` → `0x080F5E00`). Full algorithm in §5.
2. **Offline validator reimplemented and cross-checked**: 16/16 agreement on accepted and rejected inputs (§7).
3. **Novel code minted and accepted on the real screen**: `00732302` → **Temple of Skulls** (card record 142), absent from the SuperCheats 1,584-token published list and from the card name list itself. On-screen popup + RAM proof (found index 142, cost 500, DP 3000→2500 internal) in §3, §6b.
4. **Rejection bound**: 1,170 further accepted-but-unpublished codes found by running the whole 67,616-entry card table through the validator; a one-digit near-miss (`00732303`) was entered and rejected with `-ERROR-` (§6b).
5. **Bounds**: 100,000,000 representable strings, exactly 2,751 accepted (2.751%), 99,997,249 rejected — a closed-set bounded characterisation, no longer a "comparator not isolated" gap.

## 3. How to reproduce

Emulator: mGBA 0.10.5, `SDL_AUDIODRIVER=dummy`, Xvfb `:315` + openbox; default SDL keymap A=`x`, B=`z`, arrows = D-pad. **No GDB stub was used** (port 2345 is occupied by a different agent's session on display `:316`). Static decompilation used REA/Ghidra 12.1.4 on a Thumb-symbolised ELF wrapper (`mkelf.py`) of ROM `0x080D0000–0x080F1000`; runtime evidence used mGBA's CLI debugger over a pty and ordinary savestates.

Path to the screen: New Game → name `AAAA` → OK/YES → icon → first deck → Main menu: down 3 → **Get Cards** → down 1 → **PASSWORD**. Save state at the empty keypad.

**Input-harness caveat:** key holds must be ≥0.12 s with ≥0.18 s gaps. The earlier `pw2.py` timings (0.07/0.09 s) drifted on this run and typed `12345672` instead of `00732302` — a harness failure, not a game behaviour. Re-home with Up×3, Left×8 before every digit.

Codes/actions on the real screen:

| Input | Result | Screenshot |
|---|---|---|
| `46986414` | accepted — Dark Magician (LV7, ATK 2500 / DEF 2100) | `s_pw2_entered.png` (prior pass) |
| `16255442` | accepted — Beckoning Light | `s_novel_accepted.png` (prior pass) |
| **`00732302`** | **accepted — Temple of Skulls; `Acquired card Temple of Skulls.`** | `novel_final.png`, `novel_granted_screen.png` |
| `00732303` (one digit changed) | **rejected — `-ERROR-`** | `nearmiss.png` |
| `11111111` | rejected — `-ERROR-` | `s_invalid_ok2.png` (prior pass) |
| `00000000` | no-op | `s_reject_00000000.png` (prior pass) |
| `46986414` re-entered | rejected (used-password dialog) | `s_already_used2.png` (prior pass) |
| 8 single-digit mutations of `46986414` | all rejected | `alias_*.png`, `re_*.png` (prior pass) |

## 4. Address map

`0x08000000 + file_offset`. Savestate offsets are into the decompressed `gbAs` chunk (397,312 B; IWRAM at `0x19000`, EWRAM at `0x21000`).

| Item | Address / offset | Evidence |
|---|---|---|
| Password digits, `u16[8]` | IWRAM `0x03005860` (state `0x1e860`) | Observed: savestate diffs; read-watchpoint at `0x080DF5F6` |
| **Packed password u32** | IWRAM **`0x03005870`** (state `0x1e870`) | Observed: `46986414`→`0x46986414`; `00732302`→`0x00732302`; written on submit |
| Found card index / cost / search cursor | `0x03005874` / `0x03005878` / `0x0300587C` (state `0x1e874/78/7c`) | Observed: accepted runs show index 37 (Dark Magician), 142 (novel) and cost 5200/500 |
| Password UI state machine (OK handler) | **`0x080DFCB0`** | Ghidra `ev_393b77ce035453ff9bacad6c19131b90c334deb5cffaedd8404d865cf6ab77f2` |
| Digit renderer (old watchpoint hit) | `0x080DF5C4`, read at `0x080DF5F6`, literal `0x080DF660=0x03005850` | Observed (prior pass) |
| **Comparator loop** | **`0x080E02D0`** (duplicate `0x080E02C8`) | Ghidra `ev_4249360a74510591373bac2decccc70ecb4aaf6fd6964b24726c3999295845b1`; sole caller of `0x080EF370` |
| Password decoder | `0x080EF370` → `0x080EF35C` | Ghidra `ev_5eed58b8594bed59d30eba63f1a4c7f2af46c6d064d55fd2765b1e0f716afb79`, `ev_7ab6b2adc582ce41742866705bcc57c5dce91dea0608801bcfc1407d91f1b2e1` |
| LCG key function | `0x080F5E00` | Capstone: `MUL 0x343FD`, `ADD 0x269EC3`, `>>16`, `OR 0x9EC30000` |
| **Card password table** `u32[N]` | **`0x09B94CC`** | Literal at `0x080EF388`; `N = u32[0x09B7CCA] = 67616` |
| **Card DP cost table** `u32[N]` | `0x09CEDFA4` | Literal at `0x080E03A8`; cost 5200 for Dark Magician, 500 for record 142 |
| DP counter | EWRAM `0x02006C38` (state `0x27c38`) | Observed 3000→2500 after paying for novel card |
| Hint table | `0x09E5F71E`, 14 × 0x14-byte records | Prior pass |
| Hint search helpers | `0x080EF3BC`, `0x080EF454` | Prior pass; unrelated to password lookup |
| Debug asserts (unrelated) | `0x080171D4`, `0x0801722C`; strings `0x09E3A790/A7AC` | Prior pass |

## 5. Algorithm / pseudocode

### Input packing
```
on OK pressed (UI state 5 at 0x080DFCB0):
    pw = 0
    for i in 0..7: pw |= digit[i] << (4*(7-i))     // one DIGIT PER NIBBLE
    *(u32*)0x03005870 = pw                         // e.g. 46986414 -> 0x46986414
```
This is why literal searches for decimal `46986414 == 0x02CCE16E`, packed BCD `0x04069864`, etc. all failed: the on-disk representation is additionally XOR-obfuscated.

### Comparator (0x080E02D0)
```c
u32 pw = *(u32*)0x03005870;
u32 n  = *(u32*)0x09B7CCA;          // 67616 card records
for (idx = 0; idx < n; idx++) {
    u32 stored = *(u32*)(0x09B94CC + 4*idx);
    u32 key    = decode_password(stored, idx);   // 0x080EF370
    if (pw == key) { found = idx; break; }       // -> 0x03005874
}
if (not found) -> "-ERROR-" / incorrect-password dialog

u32 decode_password(u32 stored, u16 idx) {        // 0x080EF370 + 0x080EF35C
    u32 x = (idx * 0x000343FD + 0x00269EC3) & 0xFFFFFFFF;  // 0x080F5E00
    u32 k = ((x >> 16) & 0xFFFF) | 0x9EC30000;
    return stored ^ k;
}
```
`0x343FD` / `0x269EC3` are the classic Numerical Recipes LCG constants; the routine keeps the high 16 bits of the state and ORs in the high halfword `0x9EC3` (from `0x269EC3 << 16`). The search loop is capped at 300 iterations per invocation in the UI, but starts at 0 for a fresh submission, so all records remain reachable.

### Accept predicate
An 8-digit string is accepted iff the nibble-packed u32 `pw` equals `decode_password(table[i], i)` for some `i < 67616` **and** all eight nibbles of `pw` are ≤ 9 (the keypad cannot express hex nibbles A–F) **and** the password has not already been consumed **and** the player has enough DP to pay `cost[i]`.

The DP cost is `*(u32*)(0x09CEDFA4 + 4*i)`; the UI charges it after the YES confirmation (observed internal 3000→2500 for record 142, display 30000→25000).

## 6. Tables

- **Input alphabet**: `0`–`9`, 8 positions, stored as `u16` at `0x03005860`, packed nibble-wise into `0x03005870`.
- **Card table**: 67,616 records; password u32 at `0x09B94CC`, cost u32 at `0x09CEDFA4`.
- **Hint table**: 14 × 20-byte masked records at `0x09E5F71E` (in-game advertising).
- **Published code set**: SuperCheats "Actual full password list" — **1,584 unique 8-digit tokens** (fetched and parsed 2026-11-21 from the print view; the earlier `publist.html` copy was a Cloudflare challenge page and contained zero tokens).
- Message strings and menu labels: see prior-pass address map; unchanged.

## 6b. Enumeration

**Space definition.** Eight decimal slots, alphabet `0`–`9`, no checksum character or reserved bit → **10^8 = 100,000,000** representable strings. Internally each digit occupies one hex nibble of a u32.

**Full-table enumeration.** The offline validator was run over **all 67,616 card records** in the ROM table:

| Quantity | Count |
|---|---|
| Card records scanned | 67,616 |
| Records whose decoded password has all nibbles ≤ 9 | 2,796 |
| **Distinct accepted 8-digit passwords** | **2,751** |
| Published unique tokens | 1,584 |
| Accepted ∩ published | 1,581 |
| **Accepted but NOT in any published list** | **1,170** |
| Published but not accepted in this ROM | 3 (`30548775`, `33875961`, `46128067`) |
| Rejected strings (100,000,000 − 2,751) | 99,997,249 |

**Validator / oracle agreement: 16/16.** Accepted: `46986414` (idx 37/38/39), `16255442` (idx 1553), `23771716` (idx 375), `00732302` (idx 142). Rejected: `11111111`, `00000000`, `00732303`, `12345678`, and all eight single-digit mutations of `46986414` (`56986414`, `47986414`, `46086414`, `46996414`, `46987414`, `46986514`, `46986424`, `46986415`).

**Novel code entered on the real screen.** `00732302` — absent from the 1,584-token SuperCheats list (and its card, Temple of Skulls, is not named there at all). On the PASSWORD screen: card popup "TEMPLE OF SKULL", then confirmation "You need 500 DP to acquire this card. Will you pay?" → YES → **`Acquired card Temple of Skulls.`** (screenshots `novel_final.png`, `novel_granted_screen.png`). RAM proof from `ram_novel_accepted.raw` / `ram_novel_granted.raw`: digits `[0,0,7,3,2,3,0,2]`, packed password `0x00732302`, found index **142** (exactly the validator's prediction), cost **500**, DP **3000 → 2500**, UI state `0x17 → 0x1B`.

**Rejection bound / near-miss.** Changing the last digit (`00732303`) — a value the validator also rejects — was entered on the same screen and produced `-ERROR-` with DP unchanged at 2500 (`nearmiss.png`). This is a one-nibble near-miss rejection immediately adjacent to an accepted novel code. The earlier `11111111`, all-zero, reuse and eight single-digit mutation rejections (§3) are subsumed by the full 67,616-record enumeration above.

**Closed-set result.** The accepted set is provably exactly the 2,751 distinct decoded passwords above — not merely "the published list". 1,170 of them are unlisted; the game's own `decode_password` was run over every record to establish this, not inferred from single-digit mutations.

## 7. Validation evidence

- **Observed (emulator/screenshots)**: full menu path, password keypad, all accept/reject dialogs, the novel card popup, the DP payment confirmation, the `Acquired card` message and the near-miss `-ERROR-`.
- **Observed (RAM)**: input buffer at `0x03005860`, packed password at `0x03005870`, found index/cost at `0x03005874/78`, DP at `0x02006C38`, across six savestate dumps.
- **Derived (Ghidra/REA decompilation, Evidence IDs in §4)**: UI state machine `0x080DFCB0`, comparator `0x080E02D0`, decoder `0x080EF370`/`0x080EF35C`, LCG `0x080F5E00`, table/count/cost addresses.
- **Derived (Capstone)**: exact LCG constants and `OR 0x9EC30000` key schedule.
- **Reimplemented oracle**: Python reimplementation over all 67,616 records; 16/16 agreement with observed accept/reject, and the novel code's predicted card index 142 matched RAM.
- **Not exercised**: full Deck Edit / Free Duel / Challenge / Options screens; the four list-browser tabs individually; the "cannot acquire this card" branch.

## 8. Unknowns

1. ~~Comparator address and algorithm~~ — **resolved** (§5).
2. ~~Physical password storage~~ — **resolved**: obfuscated u32 table XORed with LCG-derived key.
3. ~~Whether non-published values are accepted~~ — **resolved**: 1,170 such values; one entered and granted in-game.
4. Exact grading of DP charge and the "already used"/"cannot acquire" state machine (only the ordinary accept-and-pay path was followed after the novel grant).
5. Whether the four "Password List 1–4" browser entries expose the 14 hint cards directly (not fully enumerated).

## 9. Tooling

All artifacts in `/tmp/yumasters2` (none in the ROM folder):

- `mkelf.py` — builds a Thumb-symbolised ELF (`pwthumb.elf`) from ROM `0x080D0000–0x080F1000` for Ghidra/REA decompilation.
- `rec.dis`, `pwmodule.dis`, `scanldr*.py`, `recdis.py` — capstone/objdump scans that located the literals `0x03005850`, `0x09B94CC`, `0x09B7CCA`.
- `enum.json` — full validator output (accepted set, novel set, published set).
- `dbgdaemon.py`, `dbg.fifo`, `dbg.log` — mGBA CLI-debugger pty driver.
- `ss.py`, `ram_novel_*.raw`, `game.ss*.raw` — savestate RAM extraction.
- Screenshots listed in §3 and §6b; all kept in `/tmp`, never in the ROM folder.
- Toolchain: REA/Ghidra 12.1.4, capstone 5.0.7, `arm-none-eabi-objdump`, mGBA 0.10.5, Xvfb + openbox, `xdotool`, `scrot`, `curl`.

## 10. Legal note

No ROM bytes, card art, or copyrighted assets are reproduced. Only hashes, addresses, algorithms, counts and original helper scripts are published. Screenshots and dumps remain in `/tmp`.

## 11. Cleanup confirmation

- All mGBA / Xvfb `:315` / openbox / CLI-debugger processes started for this engagement were killed **by PID number only** (never `pkill`).
- The ROM folder was checked with `find` and contains **no** `.sav`, `.ss1`–`.ss9`, or `.state` files. All screenshots and dumps were kept under `/tmp/yumasters2`.
