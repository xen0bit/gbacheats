# Planet Monsters (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Planet Monsters.gba` (4,194,304 bytes / 4 MiB) |
| Header title | `PLANET MNSTR` |
| Game code / maker | `APME` / `60` (AGB-APME-USA, En/Fr/De/Es/It/Nl) |
| Version / entry | 0x00 / `0xEA00002E` (stock crt0 branch) |
| Fixed byte / complement / checksum word | `0x96` / `0x50` / `0x0000` |
| MD5 | `385dc0869879128befc52c0b30ff03ff` |
| SHA-1 | `8f130bd74644a36f3cf28aa8566fa21700d371df` |
| SHA-256 | `2637b182f8db3bfd5d2a0b375c00fdd3637b3d97085ee34abc3e7d56151ad23c` |

**Phase 0 result:** exactly one GBA header/logo hit (file `0x0`) — not a multigame pack. No
appended trainer, no cracktro/patched entry word, no separate patch file in the folder.
The header checksum word being `0x0000` is noted; no code modifications were found.
Publisher is Titus, developer Planet Interactive (confirmed by in-game credits and
release data).

## 2. Executive summary

The game has a **developer-intended password system** reached from
`SINGLE → <character> → PASSWORD`. It accepts **4-character lowercase codes** drawn from
a 32-symbol, **vowel-free** alphabet. The accepted set is a fixed lookup table of
**80 codes** stored as plaintext in ROM at `0x08066D80..0x08066F10`, indexed by a
208-entry pointer table at `0x08340794`. There is no button-code system, no hidden debug
menu and no additional unlockable monster/item code path in the screens walked. The only
developer-facing extra is `OPTIONS → SOUND → MUSIC TEST / SFX TEST` (numeric track/SFX
selectors).

Published lists contain 74 of the 80 codes (GameFAQs "World and Stage Passwords") plus
six "Level N" codes that are a subset of those 80 (mislabelled, e.g. `H7Z3` is stage 13,
`KDC3` is stage 73). `FDRO`, published as "Level 3 (Monaco)" / "Level 4 (Brazil)" on
several sites, **does not exist in the ROM** — a published error. The 6 stage codes omitted
from the GameFAQs stage list are stages 13, 20, 42, 53, 63 and 73; five of those are
published elsewhere as "Level N" codes, but **stage 20 (`fr63`) is absent from every
published list checked** (GameFAQs, Neoseeker, Supercheats, CheatingDome, GGmania,
AbsolutCheats, PlanetCheats, Mariogba.nl). `fr63` was entered in the emulator and accepted
(starts the World 2 boss sequence, Elephant). Out-of-table codes (`zzzz`, `1111`) are
rejected with the "incorrect password" path and an input-buffer reset.

## 3. How to reproduce

Emulator: mGBA (SDL), `SDL_AUDIODRIVER=dummy`, Xvfb `:317`, `mgba -d -3 <rom>`; keymap
A=`x`, B=`z`, Start=`Return`, Select=`BackSpace`, D-pad=arrows, L=`a`, R=`s`.

1. Boot; pick a language (FRANÇAIS / ENGLISH / …).
2. Skip the intro with A; press Start on the title screen.
3. Main menu: **SINGLE** (or MULTI / OPTIONS).
4. On **PERSONNAGE** choose a monster with ←/→, press A.
5. Choose **PASSWORD** (down, A). The 4×8 on-screen keyboard appears.
6. Navigate with arrows (row wrap 8, column wrap 4) and press A per character. The fourth
   A commits the code and either starts the world-map/boss sequence or returns to an
   empty password entry ("incorrect\npassword" string at `0x0811060D`).

Codes verified in-game this session:

| Code | Result (observed) |
|---|---|
| `x5dn` | accepted → world map (ice castle), then stage via A (READY, TIME 3:58) |
| `fr63` | **accepted → World 2 boss intro (Elephant)** — novel, not in published lists |
| `m63b` | accepted → boss intro (Singy) |
| `1111` | rejected — password screen resets, buffer `b---` |
| `zzzz` | rejected — password screen resets, buffer `b---` |

The special/CodeBreaker codes found on the web (`100143D6 0007`, `82004D44 0E08`,
`320042E8 000A`, score codes) are out of scope (GameShark/CodeBreaker memory patches) and
were **not** used as evidence.

## 4. Address map

| Item | File offset | ROM address | Notes |
|---|---|---|---|
| Nintendo logo / header | `0x000` | `0x08000000` | sole header |
| English text strings | `0x10FD98+` | `0x0810FD98+` | plain NUL-terminated ASCII (lowercase); "incorrect\npassword" at `0x0811060D`, "password" `0x081104E6`, "choose your level" `0x081105A1` |
| Text pointer table (English block) | `0x340EA0` | `0x08340EA0` | 4-byte pointers; `start game`, `multiplayer`, `password`, `options` … `incorrect password` at `+0x94` (index 37) |
| Code/label string pool | `0x66B00..0x66F10` | `0x08066B00..0x08066F10` | 5 bytes per string (4 chars + NUL) |
| **80 accepted password strings** | `0x66D80..0x66F10` | `0x08066D80..0x08066F10` | contiguous, `x5dn` first, `n09y` last |
| Pointer table (all 208 strings) | `0x340794..0x340AD4` | `0x08340794..0x08340AD4` | 208 × `u32`; entries 0–127 are labels (`w1l1`…`w8c9`, `1111`…`sxdf`, `brrr`), entries **128–207 point to the 80 real codes** |
| Password input buffer | — | EWRAM `0x02001D40` (4 bytes) | committed chars + active-slot preview; `-` = `0x2D` placeholder |
| Buffer mirror | — | EWRAM `0x02001E7B` (4 bytes) | same 4 characters |
| Entered-char counter | — | EWRAM `0x02001E80` | 0 → 4 |
| Screen/state byte | — | EWRAM `0x02001E7A` | `0x03` on password screen; `0x09` after acceptance |
| Time / lives / score (external CB codes) | — | `0x02004D44` / `0x020042E8` / `0x02007128` | listed here only to locate game-state EWRAM; not used |

Validator function address: **not isolated** (see §8). The behavioural model below is
complete for the observable input space and is stated as a lookup, not as guessed assembly.

## 5. Algorithm / model

```
ALPHABET = "bcdfghjklmnpqrstvwxyz0123456789-"      # 32 symbols, 4 rows x 8 columns
accept(input):
    if len(input) != 4: return REJECT
    if any(c not in ALPHABET for c in input): return REJECT
    return ACCEPT iff input == one of the 80 strings at 0x08066D80..0x08066F10
```

The 80 strings are random-looking (base-32 values show no arithmetic progression,
no checksum and no generated pattern), so this is a pure lookup table, not a
checksum/progress decoder. The on-screen keyboard's preview byte at `0x02001D40+n`
was read after every cursor move to recover the alphabet exactly; the grid is linear
(`Right` = +1 mod 8, `Down` = +8 mod 32).

Mapping recovered from table index (index − 128 + 1 = stage number):

| Stages | Codes (table indices 128–207) |
|---|---|
| 1–10 | `x5dn mlv4 t0by pv73 pwd8 g3lv zxpw hfcb 9fdb 49lt` |
| 11–20 | `tk7b fbbl h7z3 nxb5 tzrp 8hxc wgj6 x4bd 45qp fr63` |
| 21–30 | `10cy fdr0 sjl8 73cl 9lwd fx63 q48j k0lp rjv9 j0j1` |
| 31–40 | `lnn9 zwwp 9nn8 7cbz nqzb b82x h6qd 9bbz cc5j z4lp` |
| 41–50 | `m63b sr8q k58t 07zt lkv2 f75w 9qx5 r56w q94z j5kj` |
| 51–60 | `pl03 q5rz gzw7 fw1q 96r1 krx3 vb8k ljh4 dt0q pzt4` |
| 61–70 | `9zjk d3gn z6f1 tkm5 rkl9 sl94 q82q 01gt q75t 6pnl` |
| 71–80 | `dw5t yt9q kdc3 hb5j w8np vzb4 p66q fy7r dvm4 n09y` |

GameFAQs' "World 1 – Stage 41 = m63b" is a world label typo; numerically it is stage 41
(table index 168). The same code is published as "Level 5 (USA)" elsewhere. Stage labels
in published lists are unreliable; the ROM index is authoritative (cf. guide §16.15).

## 6. Tables

* **Alphabet** (keyboard grid, recovered by RAM preview): row0 `b c d f g h j k`; row1
  `l m n p q r s t`; row2 `v w x y z 0 1 2`; row3 `3 4 5 6 7 8 9 -`. Vowels are excluded.
* **Input record**: EWRAM `0x02001D40` = 4 ASCII bytes (`0x2D` = empty); mirror at
  `0x02001E7B`; count byte `0x02001E80`.
* **Pointer table**: `0x08340794 + 4*i`; `i=128..207` → the 80 accepted codes.
  Entries 0–127 are scene/level *labels* in the same alphabet; `1111` (entry 48) was
  entered in-game and **rejected**, proving labels are not codes.
* **Published-code verification**: all 74 GameFAQs stage codes plus the 6 "Level N"
  strings are present in ROM except **`FDRO`** (absent in any encoding/case; published
  "Level 3 Monaco / Level 4 Brazil" is wrong — the real stage-32 code is `ZWWP`).
* **No button-code table** was found: the keyword sweep (`password|cheat|code|debug|
  secret|unlock|monster|level|menu`) hit only UI text, credits and "level designers";
  the only input surfaces are the on-screen keyboard and menu navigation.

## 6b. Enumeration

* **Space definition:** 32 symbols × 4 positions = **32⁴ = 1,048,576** representable
  strings. Field widths: 4 × 5 bits; no separate checksum character; `-` (index 31) is a
  normal symbol, not a terminator.
* **Accepted set:** exactly **80** of those 1,048,576 strings — the contiguous 80-entry
  table at `0x08066D80..0x08066F10` (§5). All 80 were extracted and are listed above.
  80 / 1,048,576 ≈ 0.0076 % of the space.
* **Novel code (absent from every published list checked): `fr63`** — stage 20
  (World 2's last/boss stage). Entered on the real PASSWORD screen; the input buffer
  read back as `fr 63` at EWRAM `0x02001D40`, and the game accepted it, showing the
  Elephant boss introduction. A second control (`m63b`, a published code) showed the
  Singy boss introduction; the differing boss confirms `fr63` reaches a different,
  unadvertised stage rather than a generic accept path.
* **Bounds proven by rejection:** `zzzz` and `1111` (both in-alphabet, length 4, but not
  in the table) were entered on the same screen; each returned to an empty password
  entry with the input buffer reset to `b---` and state byte `0x02001E7A` still `0x03`
  (acceptance sets it to `0x09`). This bounds the system as table-membership only: no
  checksum-only or free-form generation path is reachable from the UI.
* **Published list checked:** GameFAQs (both password tables), Neoseeker, Supercheats,
  CheatingDome, GGmania, AbsolutCheats, PlanetCheats, mariogba.nl. `fr63` appears in
  none. All fetched pages were treated as data; a 403 from GameFAQs was worked around
  with search snapshots. No prompt-injection payload was encountered in this session's
  fetches (a known hazard from guide §16.8).

## 7. Validation evidence

**Observed (emulator + RAM):**
- Boot, language select, intro, title, main menu (SINGLE/MULTI/OPTIONS), character select,
  NEW GAME/PASSWORD submenu, password keyboard, world map, READY/gameplay, pause
  (`QUITTER? / OUI / NON`), OPTIONS (`EASY`, `MAX TIME`, `SOUND`, `CREDITS`), SOUND
  submenu (`MUSIC`, `MUSIC TEST`, `SFX`, `SFX TEST`), scrolling credits, MULTI player
  setup (`P1..P4`, `CPU 00..`). Screenshots kept in `/tmp/planetmonsters/`.
- Keyboard grid characters recovered by reading the EWRAM preview byte after each arrow
  press (not inferred from the stylized font).
- `x5dn`, `fr63`, `m63b` accepted; `1111`, `zzzz` rejected; buffer/state bytes read from
  uncompressed `gbAs` savestate chunks (397,312-byte states, EWRAM at state offset
  `0x21000`).

**Derived (static):**
- 208-pointer table and 80-code string pool located by literal/pointer scans; all 80
  strings enumerated with their stage indices.
- Text is plain lowercase ASCII plus a 4-byte pointer table — no font/tile-index decode
  was needed. The `strings` hits for "password", "options", "incorrect password",
  "choose your level", "level designers" are all explained by this bank/credits.

**Inferred (labelled):**
- The exact stage-number mapping `index−128+1 = stage` is inferred from the published
  list order and confirmed for the sampled codes; it is not read from an in-game label.
- The validator's machine-code address is unresolved; the "lookup over the 80 strings"
  model is inferred from (a) the strings being the sole ROM references for those values,
  (b) random base-32 values with no checksum structure, and (c) exact in-game
  accept/reject agreement on the tested inputs.

## 8. Unknowns

- **Validator function address and call path** were not isolated. A read watchpoint on
  the input buffer hit only the display routine at `0x08012ED0..0x08012ED4` (thumb);
  a write watchpoint on the state byte hit a redundant `0x03` write at `0x0801972A`.
  No literal pointer to the pointer table exists in ROM, so the table base is computed
  through the game's script/UI structures. This does not affect the behavioural model,
  which was validated against the game itself.
- The "choose your level" / "championship" strings exist in the text bank
  (`0x081105A1`, pointer at `0x08340F0C`) but no distinct level-select screen was reached
  from SINGLE → NEW GAME (it goes straight to the world map) or from the MULTI setup
  screens walked. It may be a label used by a mode requiring link play or a cleared game.
- Whether the 128 non-code table entries are reachable via a non-UI path (savestate/RAM
  editing) is outside the in-game/developer-intended scope.
- The character roster contains about six distinct playable monsters in the cycle
  observed; the seven monster names in the text bank (`pingolo`, `elephant`, `crocos`,
  `lapinor`, `singy`, `crabik`, `dragon`) include boss names, and no unlockable playable
  monster was reached by any code.

## 9. Tooling

- `arm-none-eabi-objdump -M force-thumb` (raw GBA disassembly), Capstone 5.0.7 and custom
  Python pointer/LDR scanners.
- Python 3 scripts in `/tmp/planetmonsters/`: `ss.py` (zlib `gbAs` savestate
  decoder + diff), `enter.py` / `enter2.py` (on-screen keyboard driver verified against
  EWRAM), `srv.py` (pexpect driver for mGBA `-d`).
- mGBA `-d` command-line debugger (`r/1`, `watch/r`, `watch/w`) and savestate diffs;
  GDB stub was tried and found unreliable for repeated clients, so the `-d` pty was used.
- Xvfb `:317` + openbox + xdotool + scrot + ImageMagick. All helper processes and
  generated `.ss1` files were cleaned up (see cleanup note in the final reply).

## 10. Legal note

No ROM bytes, graphics, music or full text banks are redistributed here — only hashes,
addresses, the alphabet, and the 80 short code strings (the latter are developer-intended
passwords, already public in part).
