# Yu-Gi-Oh! Reshef of Destruction (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Yu-Gi-Oh! Reshef of Destruction.gba` (16,777,216 bytes = 0x1000000) |
| Header title | `YUGIOH DM8` |
| Game code | `AY8E` (USA/Europe) |
| Maker | `A4` (Konami) |
| Version | `0x00` |
| Entry word | `0xEA00002E` (stock ARM branch; **not** a patched cracktro) |
| Fixed `0x96` | present at 0xB2 |
| MD5 | `c06decdf51468503434dcb5e7bbdcca5` |
| SHA-1 | `dad3aa7dd470c9b475236fed2ea867b04ab1b089` |
| SHA-256 | `b64014de3986262114d7c6797bf92b97938d8bf2464f2b96071b3b41c25f4b8f` |

The in-game cheat surface is the **Password Terminal**, an orange machine inside
Trusdale's / Grandpa's toy shop in Clock Tower Square. It costs 1,000 Domino per
use and unlocks a card in the shop inventory. Two further, non-card passwords
change the final boss and Ra's form. All of these are developer-intended codes;
no GameShark/CodeBreaker/AR codes were used or reported as findings.

## 2. Executive summary

The password system is a **flat, 8-digit lookup table**, not a checksum algorithm.
Each accepted code is stored as eight raw bytes whose values are the decimal
digits 0–9 (`0x00..0x09`); `0x0F×8` terminates the table and `0x0F×7,0x0E` marks a
card that has no password.

* Main card table at ROM `0x08E0FD4C`: **801 entries**, of which **795 are valid
  passwords** and 6 are no-password sentinels; terminator at `0x08E11654`.
* Special (non-card) table at ROM `0x08E11664`: **2 entries** —
  `25410867` (Goemon Impact Reshef) and `51404976` (Ra's Phoenix Mode).
* Total accepted inputs: **797 out of 100,000,000** possible 8-digit strings.
* The validator is a linear scan with an exact 8-byte compare; there is no
  alphabet conversion, XOR, permutation or checksum.

A novel code, **`43063758`** (card index 550), was identified from the ROM table.
It is absent from the two fully retrievable published lists (a 3rd party cheat index's
791 codes; the 3rd party cheat index lists available via search snippets) and 3rd party cheat indexes have
no password page for it (HTTP 404). Its acceptance is proven by the ROM's own
validator path, and its bounds by the table counts and rejection branch.

The full accepted set was enumerated **from the ROM's own terminator/sentinel
semantics** (§16.9 equivalent for a lookup system): the scan stops only on the
`0x0F×8` terminator, so 795 + 2 is a closed count, not a sample.

## 3. How to reproduce

### Static
```bash
ROM="Yu-Gi-Oh! Reshef of Destruction.gba"
# passwords are 8 raw digit bytes, not ASCII:
python3 - <<'PY'
rom=open("Yu-Gi-Oh! Reshef of Destruction.gba","rb").read()
for off in (0xE0FD54,0xE11664,0xE1166C):
    print(hex(off), ''.join(str(x) for x in rom[off:off+8]))
PY
arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 \
  --start-address=0x08055C04 --stop-address=0x08056090 -M force-thumb "$ROM"
```

### Emulator
* mGBA 0.10.5, Xvfb `:320`, `SDL_AUDIODRIVER=dummy`, `-3` scale.
* Keymap: A=`x`, B=`z`, Start=`Return`, Select=`BackSpace`, D-pad = arrow keys.
  **Hold each key 0.20–0.25 s**; 0.09 s taps are frequently missed by this game
  (§16.2). Fast-forward = hold `Tab`.
* Boot path observed: title → `x` (new game) → 5-letter name entry → A on OK →
  long intro → dialogue (mask A) → Domino Plaza / Clock Tower Square.
* In-game status read at this point: Deck Capacity 1600, Duelist Level 72,
  Life Points 8000, **Money 500 Domino** — below the 1,000 Domino terminal fee.
* Shop location from published walkthroughs: leave Clock Tower Square by the
  **lower-right** exit and enter Trusdale's shop; the terminal is the orange
  machine on the right. (One FAQ says bottom-left; both exits were walked.)

### Money patch and terminal approach (follow-up run)
* The prior session's savestate was patched **offline** (PNG `gbAs` chunk,
  EWRAM blob offset `0x42DD0` = RAM `0x02021DD0`) from 500 to **5,000 Domino**.
  Reloading it in mGBA and opening Status shows `Money 5000 Domino`
  (`status.png` in the analysis work dir) — **observed in-game**, no ROM crt0
  or cheat-device patch.
* From Clock Tower Square the lower-left stairs leading to the GAME-shop
  street were taken; entering the shop puts the player in a small interior with
  shelves, a counter and the **orange Password Terminal** on the right.
  Pressing A on it yields the terminal greeting `Hello. I am the Pass...`
  (`t3_A.png`) followed by `You can enter a password` → `Yes/No` →
  `Please enter the 8-digit password` → the numeric keypad
  (`keypad_open2.png`, display `00000000`, keys `7 8 9 / 4 5 6 / 1 2 3 / 0 OK`).
* Typing on the keypad works (display tracked the pressed digits, e.g.
  `GOOD_type_2.png` shows `43000000`), but landing the cursor on the `OK` cell
  during navigation submits/derails the entry, so a full on-screen accept
  screenshot was **not** captured. Instead, the ROM's own search routine was
  executed in mGBA with the labelled RAM-buffer patch described in §6b.

## 4. Address map

### ROM (file offset = ROM address − 0x08000000)

| Address | Size | Meaning |
|---|---:|---|
| `0x08E0FD4C` | 801×8 B | Main card-password table (index = card ID − 1 offset) |
| `0x08E11654` | 8 B | Main table terminator `0F×8` |
| `0x08E1167C` | 8 B | Terminator pattern literal (`0F×8`) |
| `0x08E11684` | 8 B | No-password sentinel pattern literal (`0F×7,0E`) |
| `0x08E11664` | 2×8 B | Special-password table |
| `0x08E11674` | 8 B | Special table terminator |
| `0x08055C04` | — | `search_main_password()` — linear scan of main table |
| `0x08055D04` | — | `search_special_a()` (base `0x08E1165C`, empty in this build) |
| `0x08055DEC` | — | `search_special_b()` (base `0x08E11664`, 2 entries) |
| `0x08055C64` | — | Caller / top-level submit handler |
| `0x08055ED4` | — | `entry_state(index)` → 0 terminator, 1 sentinel, 2 valid |
| `0x08055D78` / `0x08055E60` | — | Same helper for the two special tables |
| `0x08055F1C` | — | 8-byte exact compare, returns 10 (equal) / 11 (differ) |
| `0x08056014` / `0x08056048` | — | Special-code effect handlers (bit setters) |
| `0x08034F60` | — | Message box by ID (`0xC9` = success, `0x39` = wrong) |
| `0x0800B3E4` | — | Unlock card by index |
| `0x08055FEC`, `0x08055F64`, `0x08055F68` | — | Post-accept flag/UI helpers |

### RAM

| Address | Meaning |
|---|---|
| `0x02021DC0` | 8 digit bytes written by the on-screen numeric keypad |
| `0x02024510` | `u16` current scan index |
| `0x02024512` | result byte: `10` = found, `11` = not found |
| `0x02024513` | local copy of the 8 entered digits |
| `0x02024588` / `0x0202458C` | special-code flag bytes (observed from handlers) |
| `0x02021DD0` | Money (observed as 500 in savestate EWRAM) |

mGBA `.ss1` savestates are PNG with a zlib `gbAs` chunk; decompressing gives a
397,312-byte blob with EWRAM at blob offset `0x21000`. EWRAM address
`0x02021DD0` maps to blob offset `0x42DD0` (verified: bytes `f4 01 00 00` = 500).

## 5. Algorithm

```
submit():
    copy 8 bytes from [0x02021DC0] to [0x02024513]
    call search_main()
    if result == 10:
        unlock_card(index)              # 0x0800B3E4
        message(0xC9)                   # correct
        flag_write(index, 1)
        return
    call search_special_a()             # empty table in this build
    if result == 10: ...special handler A...
    call search_special_b()             # 2 entries
    if result == 10: ...special handler B...
    else: message(0x39)                 # wrong password

search_main():
    index = 0
    loop:
        entry = 0x08E0FD4C + index*8
        state = entry_state(entry)      # 0=0F*8, 1=0F*7+0E, 2=other
        if state == 0: result = 11; return      # end of table → reject
        if state == 2 and compare(entry, entered) == 10:
            result = 10; return                # accept
        index++

compare(a, b):                          # 0x08055F1C
    for i in 0..7:
        if a[i] != b[i]: return 11
    return 10
```

Notes:
* `entry_state()` compares the entry against two *literal patterns elsewhere in
  ROM* (`0x08E1167C` and `0x08E11684`), not against inline constants.
* `0x08055D04`'s table base is `0x08E1165C`, whose first entry is already the
  `0F×8` terminator — that path has zero entries in this retail build.
* The special table base `0x08E11664` makes the Goemon password entry 0 and the
  Ra password entry 1; their handlers set bits in `0x02024588`/`0x0202458C`.

## 6. Tables

### Special / non-card codes

| Code | Table index | ROM offset | Effect (derived) |
|---|---:|---:|---|
| `25410867` | 0 | `0x08E11664` | Final boss Reshef becomes Goemon Impact |
| `51404976` | 1 | `0x08E1166C` | Ra → Phoenix Mode |

### Main table structure

| Field | Value |
|---|---|
| Element size | 8 bytes, one byte per decimal digit (0–9) |
| Base | `0x08E0FD4C` |
| Entries | indices 0..800 (801); valid at 1..800 in mixed order |
| Valid passwords | 795 |
| No-password sentinels | 6 (`0F 0F 0F 0F 0F 0F 0F 0E`) |
| Terminator | index 801 at `0x08E11654` (`0F×8`) |
| Duplicates | 0 |

Sample entries (index, password): (1, `89631139` Blue-Eyes White Dragon),
(34, `46986414` Dark Magician), (110, `28913279` Ruklamba the Spirit King),
(151, `55908887` Orgoth the Relentless), (216, `81306586` Nightmare Penguin),
(250, `03366982` Alligator's Sword Dragon), (435, `54285230` Aeris),
(445, `80280944` Giant Rex), (550, **`43063758`**), (800, `74150658` Talons of
Shurilane). The complete 795-entry list is reproduced in `rom_passwords.json`
in the analysis work dir (addresses + digits only; no game assets).

## 6b. Enumeration

**Space definition.** The input is exactly 8 decimal digits, alphabet
`{0..9}` per position: `10^8 = 100,000,000` representable strings. There is no
checksum, no reserved bit and no length variant. Acceptance is membership in a
fixed 797-element set (795 card + 2 special). Accepted fraction =
`797 / 100,000,000 = 0.000797%`.

**Closed-set proof.** The ROM's own scan terminates only on `0F×8` at table
index 801. Walking from `0x08E0FD4C` with the ROM's exact terminator/sentinel
predicates yields 801 entries: 795 accepted passwords, 6 no-password sentinels,
1 terminator. The special table yields 2 accepted entries and a terminator at
index 2. No other table base is referenced by the three validator functions
(pointer scan for both table bases found only the literals at
`0x08055C48`, `0x08055D64`, `0x08055D64`-family, `0x08055E4C`, `0x08055E94`,
`0x08055EF8`).

**Novel code (not in any published list examined).**

| | |
|---|---|
| Code | **`43063758`** |
| ROM table index | 550 (offset `0x08E11378`) |
| Published-list status | Absent from a 3rd party cheat index's 791-code Reshef list; absent from 3rd party cheat indexes snippets retrieved; 3rd party cheat indexes returns HTTP 404 (no card/password page). |
| Acceptance evidence | **Derived + dynamically executed in mGBA**: present as eight digit bytes in the main table; `entry_state()` classifies it as valid (2); `compare()` returns 10 against a keypad buffer holding the same digits; caller then takes the card-unlock + `message(0xC9)` path. |
| In-game execution | Keypad reached through the real terminal and digits typed on screen; a full accept-message screenshot was not captured (see §8). The ROM validator itself was called in-emulator (below) and returned **accept**. |

**Dynamic validator oracle (mGBA CLI debugger, follow-up run).** Using the
`-d` debugger, a breakpoint was set at the idle loop `0x08008236`, the 8 digit
bytes were written to *both* the keypad source `0x02021DC0..C7` and the search
copy `0x02024513..1A` (the "labelled buffer patch at `0x02024510+3`"), PC was
set to `0x08055C05` (`search_main_password() | 1`) with a valid LR, and the
breakpoint at `0x08008238` caught the return. RAM afterwards:

```
0x02024510: 26 02 0A 04 03 00 06 03 ...
             ^^ index u16 = 0x0226 = 550   ^^ result byte 0x0A = 10 = FOUND
```

so the ROM's own validator accepted `43063758` at table index **550** —
exactly the static prediction. Repeating with the one-digit near-miss
`43063759` gives:

```
0x02024510: 21 03 0B 04 03 00 06 03 ...
             ^^ index u16 = 0x0321 = 801 (terminator)  ^^ result 0x0B = 11 = NOT FOUND
```

This is an **observed in-emulator accept/reject** of the ROM's search function,
not a screenshot of the UI message; it closes the "derived only" gap for the
validator's decision.

For contrast, the other nine ROM passwords missing from the 3rd party cheat index list
were each found in another published source and are therefore **not** novel:
`03366982` (Alligator's Sword Dragon), `17679043` (Penguin Torpedo),
`28913279` (Ruklamba the Spirit King), `54285230` (Aeris, 3rd party cheat indexes),
`55908887` (Orgoth the Relentless), `79106360` (Morphing Jar #2),
`80280944` (Giant Rex), `80558357` (Command Angel, 3rd party cheat indexes),
`81306586` (Nightmare Penguin, 3rd party cheat indexes). The 6 published codes absent from
this ROM's table (`10438194`, `10510953`, `14126321`, `15125587`, `28470714`,
`69474262`) are **rejected** by this build — a useful cross-SKU warning (§16.7,
§16.11).

**Bounds proven by structure and by in-emulator oracle:** an input not in the
table reaches the `0F×8` terminator and yields result 11 → `message(0x39)`; a
no-password sentinel is skipped by `entry_state()==1`. The near-miss
`43063759` (novel code +1, i.e. the smallest possible one-digit change in the
last position) was run through the real search routine in mGBA and returned
result `11` with the scan index at the terminator (`801`) — **observed reject
bound**, alongside the accept result `10`/index `550` for `43063758`. An
on-screen `message(0x39)` screenshot was not captured (§8).

## 7. Validation evidence

* **Observed** — ROM fingerprint/hashes; mGBA boot, title, name entry, intro,
  overworld and menu (Status: LP 8000; Money 500 originally, **5000 after the
  labelled savestate patch**); savestate EWRAM money value at `0x42DD0`; all
  8-digit literals in ROM as raw digit bytes; table counts; shop interior and
  orange Password Terminal interaction (`Hello. I am the Pass...`); the real
  numeric keypad screen; ROM search routine returning 10/index 550 for
  `43063758` and 11/index 801 for `43063759` when called in mGBA with the
  labelled buffer patch.
* **Derived** — validator control flow, table base pointers, return values
  (0/1/2 from `entry_state`, 10/11 from `compare`), accept/reject message IDs,
  special-code bit handlers, novel code acceptance.
* **Inferred** — friendly card names attached to table indices (cross-checked
  against published lists/3rd party cheat indexes, not against an in-game card-name table).
* No prompt-injection content was encountered or acted on in fetched pages or
  ROM strings.

## 8. Unknowns

1. **On-screen accept message / card-unlock flag not captured (partially closed).**
   The original blocker (money) is fixed: 5,000 Domino was patched into the
   savestate and confirmed on the Status screen, Trusdale's shop interior was
   reached and A was pressed on the orange Password Terminal (greeting and
   Yes/No prompt observed), and the real on-screen keypad was reached. Digits
   were typed on it, but moving the keypad cursor onto the `OK` cell submits
   immediately and derails a long entry, so a clean screenshot of `message(0xC9)`
   for `43063758` is still missing. In its place the ROM's own search function
   was executed in mGBA with the labelled buffer patch: result byte `10` and
   index `550` for the novel code, `11`/`801` for the near-miss — the
   validator's decision is therefore **observed in-emulator**, not merely
   derived. A second analyst should, from the shop-interior savestate, clear
   the shop dialogs slowly (the text box has a typewriter effect), approach the
   terminal from the right, and avoid crossing the `OK` cell while typing.
2. The 3rd party cheat indexes Reshef card list could not be fetched directly (HTTP 403), so
   "not in any published list" is bounded by the sources actually retrieved
   (3rd party cheat indexes full list, 3rd party cheat indexes password index, 3rd party cheat index search
   snippets) rather than every possible list.
3. The exact card name for index 550 (`43063758`) was not recovered from the
   ROM's own name table; only its index and password are certain.
4. The `0x08055D04` path has an empty table in this build — whether this is a
   cut feature or a pointer to a table used by another regional build is unknown.

## 9. Tooling

* `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings`, `grep -abo`
* `arm-none-eabi-objdump -M force-thumb` for validator disassembly
* Python 3: `search_pw.py` (multi-encoding literal search), `parse_table.py` /
  `parse2.py` (digit-run detection), `enumerate.py` (terminator/sentinel-aware
  enumeration → `rom_passwords.json`), `ptrscan.py`, `literals.py`,
  `compare.py` (published-list diff)
* mGBA 0.10.5 under Xvfb `:320` + openbox, SDL dummy audio; `xdotool` (hold
  0.20–0.25 s), `scrot` for screen evidence
* Savestate inspection: Python zlib decompression of the PNG `gbAs` chunk to
  recover the 397,312-byte raw state and locate EWRAM
* GDB stub port 2345 is a single shared socket on this host and was occupied by
  other sessions; for the follow-up run mGBA's `-d` command-line debugger over
  a PTY was used instead (`dbgpty.py`, `oracle.py`, `oracle_reject.py` in the
  analysis work dir). It provides `r/1`, `w/1`, `x/1`, `break/t`, `w/r pc` and
  `continue`, which were used to call `search_main_password()` at
  `0x08055C04` and read `0x02024510..17` as the accept/reject oracle. Savestate
  blob patching (zlib `gbAs` chunk) supplied the money and RAM-buffer patches.

## 10. Legal note

No ROM bytes, graphics, audio or game text are redistributed. This report
contains hashes, addresses, counts and the author-generated enumeration of
numeric codes only.
