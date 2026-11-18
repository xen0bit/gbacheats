# Masters of the Universe: He-Man – Power of Grayskull (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Masters of the Universe - He-man Power of Grayskull.gba` |
| Size | 8,388,608 bytes (0x00800000) |
| Header title | `HE-MAN POWER` |
| Game code | `AGUE` |
| Maker code | `6S` (TDK Mediactive / Taniko) |
| Version | 0x00 (Rev.00) |
| Entry branch | `0xEA00002E` (stock ARM branch — no cracked intro/trainer) |
| Nintendo-logo hits | exactly one, at file `0x4` → single GBA header at `0x0`; no multiboot/second image |
| MD5 | `11c77b84b23817cda21c24bc7ddd2605` |
| SHA-1 | `fe6e84ea4c6f81b3f560a1d2462a898216a8d1ba` |
| SHA-256 | `4bf3e7efcab718ea356937668dd34d7ae6a7e1bfa4441956a3d100e280e774ef` |

Header checksum field is `0x0000` and complement `0x63`; no scene-patch strings
(GS/CB/Action Replay/CRC Bandit/SUNHORS) and no appended trainer were found.
This is a licensed retail image.

**Web recon (§3.4) — negative, bounded:** `websearch` returned no results for
five queries; direct fetches were blocked (GameFAQs CAPTCHA/403, TCRF 403,
DuckDuckGo bot challenge, Wayback CDX empty/504, r.jina.ai 403). No published
code list could be retrieved, so every code below was verified against the ROM
and emulator rather than against a web list. No prompt-injection payload was
encountered; fetched pages contained only access-denied text.

## 2. Executive summary

The game has a **developer-intended password system** with a **21-consonant
alphabet** and **8-symbol passwords**. It is a **pure lookup table of exactly
14 hard-coded 8-byte codes** — there is no checksum, no PRNG and no generator:
the validator compares the 8 input bytes against table entries 0–13 and accepts
only an exact match. The complete space is therefore **14 accepted strings**,
all recovered and listed in §6. All 14 are mnemonic phrases (e.g.
`XCLLNTJB` ≈ "EXCELLENT JOB", `THNKYHMN` ≈ "THANK [YOU] HE-MAN",
`BLVWNDLS` ≈ "BONUS WORLD").

Entry 0 (`XCLLNTJB`) starts Mission 1; entries 1–12 display ending/credits
screens; **entry 13 (`BLVWNDLS`) is an unadvertised code that jumps directly
to the hidden SOUND TEST debug screen** — confirmed in emulator (screenshot
`enum_13_BLVWNDLS_c.png` / `t13_after_c.png`). A separate hidden title-menu gate
(flag `0x0203556C > 1`) reveals SOUND TEST and MUSIC TEST menu entries; the gate
was proven by setting the flag with a debugger and observing the menu grow from
3 to 5 entries (`w_title_debugflag_c.png`). The normal in-game writer of that
flag is a set of unlock-bit helpers (§4), but the exact gameplay trigger for the
title-menu entries was not isolated (see §8).

Bounds were proven in-game: `BBBBBBBB` produces **WRONG PASSWORD** and leaves
all unlock flags unchanged (`rej_wrong_result_c.png`, RAM `pwbuf0=0x01`,
`unlock0=0x01`).

All game text found is plain NUL-terminated ASCII (no font/tile-index bank had
to be decoded); the on-screen keyboard is drawn directly from an ASCII alphabet
string at `0x087EFF90`.

## 3. How to reproduce

* Emulator: `mgba -3 -g <rom>` under `Xvfb :319`, `SDL_AUDIODRIVER=dummy`,
  window managed by `openbox`. GDB stub on `:2345`; attach with
  `gdb-multiarch`, `set architecture arm`, `target remote :2345`.
* Keymap (mGBA SDL default): A = `x`, B = `z`, Start = `Return`,
  Select = `BackSpace`, D-pad = arrow keys. Hold 50–120 ms, gap 70–300 ms.
* Menu path: boot → (splash / legal / intro, press Start/A to skip) → **TITLE**
  (`PLAY GAME` / `PASSWORD` / `OPTIONS`) → Down → `PASSWORD` → A.
  Password screen: 3×7 letter grid `BCDFGHJ / KLMNPQR / STVWXYZ`, cursor starts
  on `B`; D-pad moves, A enters a letter; the 8th A submits immediately.
* Screens walked with screenshots + RAM snapshots:
  `s5_a1_c.png` (password), `w_title2_c.png` (title), `w_options2_c.png` +
  `w_opt_d4_c.png` (OPTIONS, 4 items), `s_afterstart2_c.png` /
  `s_mission_d01..15_c.png` (SELECT MISSION, 13 entries, rest locked),
  `pause_screen_c.png` (PAUSE: CONTINUE/QUIT), `t13_after_c.png` +
  `st_d10_c.png` (SOUND TEST), `w_title_debugflag_c.png` (hidden menu),
  `rej_wrong_result_c.png` (rejection).
* Codes tested in-game: `XCLLNTJB` (mission 1), `HMNCLDNT` (credits),
  `VLNTFFRT` (programmers), `FHSMBSHS` (programmers), `BLVWNDLS`
  (SOUND TEST), `BBBBBBBB` (rejected). Remaining entries verified in ROM by
  literal table decode; see §8 for the dynamic-coverage limit.
* RAM reads: with GDB attached the core halts; use `interrupt`, `x/1xb ADDR`,
  then `continue &` to resume. Key addresses: input buffer `0x020354D0` (8
  bytes), unlock array `0x02036380`, debug flag `0x0203556C`, keypad
  `0x04000130`.

## 4. Address map

All ROM addresses are `0x08000000 + file offset`.

| Address | Meaning | Evidence |
|---|---|---|
| `0x087EFF90` | alphabet string `-BCDFGHJKLMNPQRSTVWXYZ` (22 bytes: 0=`'-'`, 1..21 = 21 consonants) | read as bytes in ROM and live in GDB |
| `0x087F002C` | password table, 14 entries × 8 bytes, indices 0..13 | literal at `0x080060F0` / `0x080061A8` |
| `0x08006044` | password handler **entry** (input + validate) | breakpoint hit on A press |
| `0x08006076`–`0x080060AE` | validator: 8-byte compare loop over table indices 0..13 | disassembly + breakpoint at `0x08006076` |
| `0x080060F0` | literal pool word = `0x087F002C` | `struct.unpack_from` verified |
| `0x08006180` | password **generator** (called when a mission shows `PASSWORD: `): `table[(level+1)*8]` → alphabet glyphs | disassembly, caller at `0x08007A00` |
| `0x020354D0` | 8-byte input buffer (values are alphabet indices 1..21) | GDB read at validator breakpoint |
| `0x02036380[]` | per-mission unlock flags, set on success | success path `0x080060FC` |
| `0x0203556C` | debug/unlock bitmask; gate `>1` reveals hidden title entries | gate at `0x080065F4`; setter helpers `0x08007494`…`0x080074E8`, dispatch table `0x087F07AC` |
| `0x080060BA`–`0x080060E4` | special success path for table index 13: installs screen handler `0x08005879` (SOUND TEST) and touches `0x0203556C` | disassembly + observed jump to SOUND TEST |
| `0x087F040C` | title-menu string-pointer table: PLAY GAME, PASSWORD, OPTIONS, SOUND TEST, MUSIC TEST, SPLASH TEST | pointer dump |
| `0x087F0428` | SELECT MISSION name table (slots 1–13, 17.SOUND TEST, 18.MUSIC TEST; 14–16 unnamed/cut) | pointer dump + screen scroll |
| `0x080065F4`–`0x08006606` | menu-count gate: if `[0x0203556C] > 1`, count = 5 | disassembly + live flag write |
| `0x08006666` / `0x087F066C` | title-entry dispatch jumptable (5 handlers) | disassembly |
| `0x0816A1F0`, `0x0816A200`, `0x0816A214`, `0x0816A250`, `0x0816A260` | `ENTER PASSWORD`, `WRONG PASSWORD`, `SELECT MISSION`, `BONUS ROOM !`, `PASSWORD: ` strings | pointer scan |
| `0x0201F130` | mission index global (0 at title) | GDB |

File-offset ↔ ROM-address conversion used throughout: `strings -t x` gives hex
file offsets; `rom_address = 0x08000000 + file_offset`. `grep -abo` decimal
offsets were converted before use.

## 5. Algorithm

Validator (decompiled from `0x08006044`; Thumb, registers renamed):

```
password_handler(state):
    if cursor <= 7:                          # char entry
        buf[cursor] = selected_char_index + 1   # 0x020354D0[cursor]
        cursor += 1
        if cursor <= 7: return
    # validation (8 chars present)
    cursor = 0
    for entry in 0 .. 13:                    # inclusive: exactly 14 codes
        matches = 0
        for i in 0 .. 7:
            if buf[i] == table[entry*8 + i]:
                matches += 1
        if matches == 8:
            on_success(entry)
            return
    show("WRONG PASSWORD")
```

Key facts:
* Input values are **alphabet indices**, not ASCII: pressing the letter at
  keyboard index `k` stores `k+1`. Alphabet index 1 = `B`, …, 21 = `Z`.
  Index 0 (`'-'`) is a blank slot and is not used by any accepted code.
* There is **no checksum, XOR, permutation or PRNG**. The comparison is a
  byte-for-byte `memcmp`-style loop.
* The generator at `0x08006180` is the exact inverse for display: for level
  `L` (1-based) it reads `table[L*8 .. L*8+7]` and draws `alphabet[idx]` for
  each byte — proving the table is the authoritative code space, not a
  truncated subset of a larger algorithmic space (cf. §16.14).
* Return domain: full match → screen/state change; no match → WRONG PASSWORD.
  No partial/prefix matching exists.

Live RAM proof: after typing `XCLLNTJB` and halting at `0x08006076` the buffer
at `0x020354D0` read
`13 02 09 09 0B 10 07 01` = indices `[19,2,9,9,11,16,7,1]` = `X C L L N T J B`,
exactly table entry 0; cursor at `0x0201FB2C` read `0x00000008`.

## 6. Tables

**Alphabet (`0x087EFF90`):** file bytes `2D 42 43 44 46 47 48 4A 4B 4C 4D 4E
50 51 52 53 54 56 57 58 59 5A 00 00` = `-BCDFGHJKLMNPQRSTVWXYZ`. 21 usable
letters; the on-screen keyboard contains those 21 in a 3×7 grid. No two
keyboard cells map to the same index (no aliases).

**Complete password table (`0x087F002C`, 14 × 8 bytes, decoded):** the numeric
index list is the literal table content; the string is what the player types.

| # | ROM address | indices | Password | Observed effect |
|---:|---|---|---|---|
| 0 | `0x087F002C` | 19,2,9,9,11,16,7,1 | `XCLLNTJB` | Mission 1 briefing (`Mission 1 SAVE GRAYSKULL`) |
| 1 | `0x087F0034` | 6,10,11,2,9,3,11,16 | `HMNCLDNT` | Ending/credits (`DEVELOPED BY TANIKO, LLC.`) |
| 2 | `0x087F003C` | 6,17,3,11,1,16,16,14 | `HVDNBTTR` | credits screen |
| 3 | `0x087F0044` | 17,9,11,16,4,4,14,16 | `VLNTFFRT` | `PROGRAMMERS` credits |
| 4 | `0x087F004C` | 4,6,15,10,1,15,6,15 | `FHSMBSHS` | `PROGRAMMERS` credits |
| 5 | `0x087F0054` | 1,6,9,3,11,5,16,9 | `BHLDNGTL` | credits screen (ROM-verified) |
| 6 | `0x087F005C` | 16,6,11,8,20,6,10,11 | `THNKYHMN` | credits screen (ROM-verified) |
| 7 | `0x087F0064` | 16,6,15,11,14,15,16,14 | `THSNRSTR` | credits screen (ROM-verified) |
| 8 | `0x087F006C` | 3,10,5,14,1,15,5,17 | `DMGRBSGV` | credits screen (ROM-verified) |
| 9 | `0x087F0074` | 18,16,2,6,16,6,10,11 | `WTCHTHMN` | credits screen (ROM-verified) |
| 10 | `0x087F007C` | 4,9,9,20,14,15,16,14 | `FLLYRSTR` | credits screen (ROM-verified) |
| 11 | `0x087F0084` | 3,10,5,15,6,14,11,15 | `DMGSHRNS` | credits screen (ROM-verified) |
| 12 | `0x087F008C` | 18,14,8,9,8,3,10,5 | `WRKLKDMG` | credits screen (ROM-verified) |
| 13 | `0x087F0094` | 1,9,17,18,11,3,9,15 | `BLVWNDLS` | **hidden SOUND TEST debug screen** |

Entries 14+ contain garbage (`K??KK??K`) and are **not** compared: the loop
bound is `cmp r3,#13; ble` (indices 0..13 only). That is the hard proof that
exactly 14 codes exist.

**Title menu table (`0x087F040C`):** index 0 PLAY GAME, 1 PASSWORD, 2 OPTIONS,
3 SOUND TEST, 4 MUSIC TEST, 5 SPLASH TEST (index 5 unreachable: count is capped
at 5). Normal count is 3.

**SELECT MISSION table (`0x087F0428`):** names for missions 1–13 plus
`17.SOUND TEST` (`0x087F0464`) and `18.MUSIC TEST` (`0x087F0468`); slots 14–16
have no names. Locked missions render as `N.----------`. Only 13 entries are
selectable in normal play.

## 6b. Enumeration

* **Space definition:** alphabet = 22 symbols (`-` + 21 consonants), but only
  indices 1..21 are usable; length = 8; no checksum bits, no reserved bits in
  any accepted code. Raw symbol space is 21^8 ≈ 3.78×10¹⁰ strings, but the
  validator accepts **exactly 14**, all enumerated in §6. This is a closed
  lookup table, not an algorithmic code system — no unpublished *additional*
  code can be minted, and that is the complete characterisation required by
  §0.2 for a lookup.
* **Validator model:** §5 pseudocode agrees with the ROM on accepted inputs
  (all 14 decoded literals) and on a rejected input (`BBBBBBBB` →
  `WRONG PASSWORD`, RAM `pwbuf0=0x01`, unlock flags unchanged).
* **Novel / unadvertised code:** `BLVWNDLS` (table index 13) is not advertised
  anywhere in the UI and was not found by any `strings` search of the game
  text. It was **entered on the real password screen** and produced the hidden
  **SOUND TEST** screen (screenshot `t13_after_c.png`, `st_d10_c.png`); RAM at
  that moment: dbgflag `0x00`, mission `0x00`, unlock0 `0x01` — i.e. a distinct
  screen state with no mission unlocked. No published list was retrievable
  (web blocked), so this is reported as *unadvertised in-game* rather than
  *absent from every web list*.
* **Bounds proof:** `BBBBBBBB` (all indices = 1, a well-formed 8-symbol input
  from the legal alphabet) is rejected with WRONG PASSWORD. Entry index 14 is
  unreachable by construction (`cmp r3,#13; ble` in the validator) even though
  its garbage bytes sit immediately after entry 13 in ROM. Both bounds (code
  content and table length) are therefore demonstrated, not inferred.

## 7. Validation evidence

* **Observed** (emulator + GDB): title, OPTIONS (4 items), SELECT MISSION (13
  selectable, remainder locked), PASSWORD entry keyboard, PAUSE (CONTINUE /
  QUIT), SOUND TEST. Password `XCLLNTJB` → mission-1 briefing; `HMNCLDNT` →
  developer credits; `BLVWNDLS` → SOUND TEST; `BBBBBBBB` → WRONG PASSWORD.
  Input buffer `0x020354D0` = `13 02 09 09 0B 10 07 01` when `XCLLNTJB` was
  submitted; `pwbuf0=0x01` after the rejected code.
* **Derived** (disassembly): validator loop and bound 0..13; generator at
  `0x08006180`; alphabet mapping; menu-count gate `[0x0203556C] > 1` → 5;
  special dispatch for index 13 → `0x08005879`.
* **Inferred**: the mnemonics in the "Password" column of §6 are
  interpretations of the letter strings (e.g. `XCLLNTJB` ≈ "EXCELLENT JOB").
  Entry effects marked "ROM-verified" were decoded from the table but not
  individually replayed on screen because the credits sequence is long and
  has no fast exit (see §8). The gameplay action that sets the unlock bits for
  the title-menu hidden entries was not isolated.

## 8. Unknowns

* Published GBA code lists could not be fetched (all sources blocked), so the
  "not in any published list" claim is stated as *unadvertised in-game*.
* Entries 2 and 5–12 were verified in ROM and accepted by the decoder, but
  their exact on-screen result was not replayed individually: most lead into a
  long, non-skippable scrolling credits sequence. (Entries 0, 1, 3, 4, 13 were
  replayed; see §7.)
* The in-game trigger that raises `0x0203556C` above 1 to expose SOUND TEST /
  MUSIC TEST as *title-menu entries* was not isolated. Setting the flag with a
  debugger proves the gate but is not itself a player cheat. The bit-setting
  helpers at `0x08007494`–`0x080074E8` and their table at `0x087F07AC` are the
  likely writers, but their gameplay callers were not traced to completion.
  SPLASH TEST (menu index 5) is never selectable — count is capped at 5 — and
  is reported as unreachable dead menu data.
* No button-code sequence was found; the secret entry point is the password
  `BLVWNDLS`, not a keypad combination.

## 9. Tooling

* `file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings -t x`, `grep -abo`.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 … -M
  force-thumb` for validator/menu/generator disassembly.
* Python 3 + `capstone` (literal/BL xref scans), `struct` (literal pool reads),
  `zlib` (savestate `gbAs` chunk), PIL (screenshot crop).
* `mgba -g -3` under `Xvfb :319` + `openbox`; `xdotool` (XTEST keys);
  `scrot`/ImageMagick. `gdb-multiarch` attached with a persistent pty session;
  `interrupt` → `x/1xb` → `continue &` cycle for reliable RAM reads.
* Analysis scripts in `/tmp/opencode/heman2/`: `phase0.py`, `scan_pw.py`,
  `tables.py`, `pw_decode.py`, `emu.py`, `pwentry.py`, `ram.py`,
  `gdb_server.py`, `ss.py`.

**Legal note:** no ROM data, graphics, music or game text are redistributed
here — only hashes, addresses, algorithms and the author's own tools/notes.
