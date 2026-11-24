# F-14 Tomcat (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/F-14 Tomcat/F-14 Tomcat.gba` |
| Size | 4,194,304 bytes (0x400000, 4 MiB) |
| Header title | `F14-TOMCAT` |
| Game code / maker | `AFTE` / `5G` |
| Version | 0 |
| Entry word | `0xEA00002E` (stock crt0 branch to `0x080000C0`) |
| Header checksum | `0x0000` (rebuilt-header artifact, §16.1) |
| Complement byte | stored `0x15`, computed `0x2E` — header was edited |
| MD5 | `399e38ffba58fccf07950791fae00539` |
| SHA-1 | `cb7918076abe28ddb29c420a3bbba617915f2de8` |
| SHA-256 | `6dbbedbaffaba2f47498c084ea163963fa47a37e2b9065223084eea3da8343fd` |

Nintendo-logo scan found **one** header at file offset 0. The entry point is ordinary
ARM crt0 (`mov r2,#0x04000000 …`), not a cracktro. The last 256 bytes are `0xFF`
padding: no appended trainer. The odd complement/checksum is a header rebuild, not a
game patch; no code patching was detected.

## 2. Executive summary

F-14 Tomcat has an in-game **password system** on the title menu ("ENTER PASSWORD").
Passwords are **8 characters** drawn from a 21-letter no-vowel alphabet
`BCDFGHJKLMNPQRSTVWXYZ` (stored at `0x083FF5FC`). A single validator at
`0x0801BBB8` compares the 8 typed bytes against a **closed table of 42 entries** at
`0x083FF480` (9 bytes per record: 8 chars + NUL). There is no checksum, PRNG or
algorithmic generator — the entire accepted space is exactly those 42 strings.

- 40 of the 42 entries match the published Novice/Ace level-2..21 lists.
- **Two entries are absent from every published list**: `DBBPCKRN` (entry #3) and
  `BRTTNYKT` (entry #4). These are "special" codes handled by the validator's first
  loop; they select enemy/sprite set ids `0x12` and `0x13` respectively.
- Both were typed on the real password screen and RAM-verified: the special-code
  flag `0x030000D0` becomes `3` and `4` (vs `1` for the published `NHDCDKPM`).
- A non-table 8-letter code (`BBBBBBBB`) is rejected: the flag stays `0`. Acceptance
  and rejection look identical on screen, so RAM is the discriminator.
- Difficulty flag `0x0300045AC` is `0` for Novice codes and `1` for Ace codes.

All menu screens were walked: title, main menu, ENTER PASSWORD, GAME OPTIONS,
MULTIPLAYER, PRACTICE LANDING, NEW GAME (tutorial + mission), and PAUSE. No hidden
debug screen, no button-code sequence, and no second code surface were found.

## 3. How to reproduce

**Emulator / display**: mGBA 0.10.5 (SDL) under `Xvfb :315 -screen 0 1024x768x24`,
`SDL_AUDIODRIVER=dummy`, `openbox`; viewport 3× (`mgba -3`).

**Keymap** (mGBA SDL defaults): A = `x`, B = `z`, L = `a`, R = `s`,
Start = `Return`, Select = `BackSpace`, D-pad = arrow keys. Hold keys ~100–150 ms.

**Menu path**: boot → Start (copyright) → Start (title "PRESS START TO BEGIN GAME") →
main menu → **ENTER PASSWORD** (Down×2, A).

**Password keyboard** (green cursor):
```
row 0:  B  C  D  F  G  H  J   ← (backspace)
row 1:  K  L  M  N  P  Q  R   E
row 2:  S  T  V  W  X  Y  Z   N   (E N T E R runs vertically down the right column)
```
Cursor starts on `B` (row 0, col 0). Right/Left move within a row, Up/Down between
rows, A types the highlighted letter into the next of 8 slots. After 8 letters,
navigate to row 1, col 7 and press A to submit (the vertical ENTER key). Backspace is
row 0, col 7.

**Codes tested** (all typed with the on-screen keyboard, not injected):

| Code | Result (`0x030000D0`) | Note |
|---|---|---|
| `DBBPCKRN` | `3` | undocumented, accepted |
| `BRTTNYKT` | `4` | undocumented, accepted |
| `NHDCDKPM` | `1` | published (UFO cheat / L21 Novice) |
| `DGHJKLFF` | `0`, difficulty `0` | published L2 Novice |
| `XDFTRLFF` | `0`, difficulty `1` | published L2 Ace |
| `BBBBBBBB` | `0` | rejected (not in table) |

**Reading RAM without a debugger**: mGBA `.ssN` savestates are PNGs with a `gbAs`
chunk; `zlib.decompress` that chunk to get a 397,312-byte state. The 32 KiB IWRAM
lives at raw offset `0x19000`; GBA address `0x03000000 + n` is at raw `0x19000 + n`.
`0x030000D0` is therefore at raw `0x190D0`. Scripts: `ss_parse.py`, `press.py`,
`enter_code.py`, `submit.py`.

## 4. Address map

| Address | Meaning | Evidence |
|---|---|---|
| `0x0801BBB8` | Password/menu function entry; prologue `push {r4-r7,lr}`; clears 8-byte input buffer at `sp+0x54` (`sl`) | Derived |
| `0x0801BEDA`–`0x0801BF4C` | First compare loop: table entries 0..3 (special codes), bound `cmp r4,#3; bls` | Derived |
| `0x0801BF5E`–`0x0801BFE2` | Second compare loop: 38 entries at base `0x083FF4A4`, bound `cmp r4,#0x25; bls` | Derived |
| `0x083FF480`–`0x083FF5FA` | 42 password records, 9-byte stride, NUL-terminated | Derived (hex dump) |
| `0x083FF5FC` | Alphabet `BCDFGHJKLMNPQRSTVWXYZ\0` (21 letters); loaded at `0x0801BE20`–`0x0801BE32` to map a typed letter to a display tile | Derived |
| `0x030000D0` | Special-code index (1..4), written by first loop at `0x0801BF22` | Observed (savestate) |
| `0x0300045AC` | Difficulty flag: 0 = Novice, 1 = Ace; written at `0x0801BFBE` / `0x0801BFD4` | Observed (savestate) |
| `0x03006E94` | Input/frame counter, incremented on every submit | Observed |
| `0x03003054` | Enemy/sprite-set table target; `0x0800665C` writes ids at +0,+0x104,+0x208,+0x30C | Derived |
| `0x08006878`–`0x08006960` | Consumer of `0x030000D0`: index 1→`0x10`, 2→`0x11`, 3→`0x12`, 4→`0x13` | Derived |
| `0x08027D24` | `CURRENT PASSWORD: ` text (pointer literal at file `0x130BC`) | Derived |
| `0x08028A1C` | `PASSWORD: ` text (pointer literal at file `0x1F5D0`) | Derived |
| `0x080283FA` / `0x080284D9` | `NHDCDKPM` / `LCMLFLTC` inside reward-message text (not the comparison table) | Derived |

File offset → ROM address: `0x08000000 + file_offset`. The table pointer was found
as a literal word at file `0x1BF4C` = `0x083FF480`; the alphabet pointer at
`0x1BF38` = `0x083FF5FC`.

## 5. Algorithm

Pseudocode recovered from the two compare loops:

```c
char input[8];                 // stack buffer at sp+0x54, zeroed on entry
u32 *special = (u32*)0x030000D0;
u32 *difficulty = (u32*)0x0300045AC;
u32 *counter = (u32*)0x03006E94;
const char *table = (const char*)0x083FF480;   // 42 records, stride 9

// ---- loop 1: 4 special codes (table entries 0..3) ----
for (int i = 0; i <= 3; i++) {
    if (memcmp(input, table + 9*i, 8) == 0) {
        *special = i + 1;                       // 1,2,3,4
        (*counter)++;
        sound(0x0B, (*counter)&3, 0x1F, 0x780);
        return 0;                               // accept
    }
}

// ---- loop 2: 38 level codes (table entries 4..41, base 0x083FF4A4) ----
for (int j = 0; j <= 37; j++) {
    if (memcmp(input, (table+0x24) + 9*j, 8) == 0) {
        (*counter)++;
        if (j <= 18) {                          // Novice L2..L20
            *difficulty = 0;
            return j + 1;                       // 1..19
        } else {                                // Ace L2..L20
            *difficulty = 1;
            return j - 18;                      // 1..19
        }
    }
}
sound(0x12, (*counter)&3, 0xFF, 0x780);
return 0;                                       // reject (same visual path)
```

Return values are consumed by the caller; the observable persistent effects are the
two RAM flags above. `0x030000D0` is read at six sites; the mode selector at
`0x08006878` switches on 1/2/3/4 and calls `0x0800665C` with sprite ids 0x10/0x11/
0x12/0x13.

## 6. Tables

### 6.1 Complete password table (42 entries, `0x083FF480`, 9-byte stride)

Index 1-based; "published" = present on 3rd party cheat indexes/etc.

| # | Code | Published as | # | Code | Published as |
|---:|---|---|---:|---|---|
| 1 | `NHDCDKPM` | L21 Novice + UFO cheat | 22 | `VBMQRWTP` | L19 Novice |
| 2 | `LCMLFLTC` | L21 Ace + "stick & rudder" | 23 | `LKFDSPBV` | L20 Novice |
| **3** | **`DBBPCKRN`** | **NOT PUBLISHED** | 24 | `XDFTRLFF` | L2 Ace |
| **4** | **`BRTTNYKT`** | **NOT PUBLISHED** | 25 | `KJTRDBPT` | L3 Ace |
| 5 | `DGHJKLFF` | L2 Novice | 26 | `RVBPZJVM` | L4 Ace |
| 6 | `GSDFBFPT` | L3 Novice | 27 | `BMNQYLNF` | L5 Ace |
| 7 | `RRHCFDVM` | L4 Novice | 28 | `LFMSDNBQ` | L6 Ace |
| 8 | `BPSXDFNF` | L5 Novice | 29 | `PGHPCZNJ` | L7 Ace |
| 9 | `LDFSDTKQ` | L6 Novice | 30 | `DKDGBPQK` | L8 Ace |
| 10 | `PXSBSZNJ` | L7 Novice | 31 | `GSYPZLCT` | L9 Ace |
| 11 | `DKXZGZQK` | L8 Novice | 32 | `DCZXRPQR` | L10 Ace |
| 12 | `GKQBGHCT` | L9 Novice | 33 | `WRTNJYSX` | L11 Ace |
| 13 | `DTRHRPFJ` | L10 Novice | 34 | `JDPQMLRT` | L12 Ace |
| 14 | `WZPKJYZX` | L11 Novice | 35 | `SPBXBMRG` | L13 Ace |
| 15 | `JDZFLKFV` | L12 Novice | 36 | `SPXPRGDH` | L14 Ace |
| 16 | `SPNGDRRG` | L13 Novice | 37 | `LPFGNBGZ` | L15 Ace |
| 17 | `SFGFJHDH` | L14 Novice | 38 | `TQWJGZHN` | L16 Ace |
| 18 | `LPFHPRFZ` | L15 Novice | 39 | `BGJKSZPQ` | L17 Ace |
| 19 | `TDKZXSHX` | L16 Novice | 40 | `PLMNHRTY` | L18 Ace |
| 20 | `DGBVKMNB` | L17 Novice | 41 | `GLMRTRRC` | L19 Ace |
| 21 | `KJHGRTCB` | L18 Novice | 42 | `NHDJPBCX` | L20 Ace |

### 6.2 Other tables

- Alphabet (`0x083FF5FC`): `B C D F G H J K L M N P Q R S T V W X Y Z` (21 symbols,
  exactly the 3×7 on-screen keyboard; no vowels, no `A`/`E`/`I`/`O`/`U`).
- Special-code index → sprite set: `1→0x10`, `2→0x11`, `3→0x12`, `4→0x13`
  (`0x08006878`–`0x08006960`). Published descriptions: index 1 = "enemy fighters
  become UFOs"; index 2 = "relive your stick and rudder days". Index 3/4 descriptions
  are unpublished.
- Difficulty: `0x0300045AC = 0` Novice (`j=0..18`), `1` Ace (`j=19..37`).

## 6b. Enumeration

**Space size**: exactly **42** accepted strings. There is no checksum and no
generator; the validator is a pure 42-entry lookup. The bounds are proven by the two
loop comparisons in the ROM (`cmp r4,#3; bls` → 4 entries; `cmp r4,#0x25; bls` →
38 entries), which together cover table indices 0..41 — the same 42 records extracted
from `0x083FF480`..`0x083FF5FA`. Number of representable accepted values: 42 out of
the 21^8 ≈ 3.78×10^10 possible 8-character strings.

**Novel codes (not on 3rd party cheat indexes, Code Book or any wiki)**:

| Code | Table # | Typed on screen | `0x030000D0` after | Sprite-set id (derived) |
|---|---:|---|---:|---:|
| `DBBPCKRN` | 3 | yes | **3** | `0x12` |
| `BRTTNYKT` | 4 | yes | **4** | `0x13` |

Before entry (clean main-menu savestate `ss1`) `0x030000D0 = 0x0`; after `DBBPCKRN`
(`ss2`) it is `0x3`; after `BRTTNYKT` (`ss5`) it is `0x4`; after the published
`NHDCDKPM` (`ss3`) it is `0x1`. These are *observed* RAM reads, not inferences.

**Bounds proven by rejection**: `BBBBBBBB` (eight letters all inside the alphabet but
not a table entry) was typed and submitted through the same screen; the flag remained
`0x0` (`ss4`). Also, `0x03006E94` increments on both accept and reject, confirming the
code actually reached the validator rather than being ignored. A 7-character code
cannot be submitted because the screen requires all 8 slots to be filled before ENTER
becomes active (verified by inspection of the slot fill; the table contains no
shorter records — all 42 records are 8 chars + NUL at a fixed 9-byte stride).

**Published-list verification**: all 40 published codes were located literally in the
table at `0x083FF480`; `NHDCDKPM`, `DGHJKLFF` (Novice) and `XDFTRLFF` (Ace) were also
entered in the emulator. Three sampled published codes from a "different-version"
concern were checked: the GBA-specific Code Book list matches the ROM exactly, so no
cross-version code mismatches were found. `Shin'en Multimedia. Code: B.Wodok` at
`0xCE6BB` is the GAX audio-engine banner (§11), not a cheat.

## 7. Validation evidence

**Observed** (emulator / savestate RAM):
- All screens listed in §3 were reached and screenshotted (`shot_00`..`shot_27`).
- `0x030000D0` = 0/3/4/1 for clean/`DBBPCKRN`/`BRTTNYKT`/`NHDCDKPM` respectively;
  `0x0300045AC` = 0 for `DGHJKLFF`, 1 for `XDFTRLFF`.
- `BBBBBBBB` leaves `0x030000D0 = 0`; accept and reject both return to the main menu
  visually, so RAM — not appearance — is the accept signal.
- Keyboard grid and cursor behaviour verified by typing and reading the 8 slots.

**Derived** (disassembly):
- Table base, stride, record count and alphabet address from literal-pool words at
  `0x0801BF38`–`0x0801BF50` and `0x0801BFC8`–`0x0801BFC8`.
- Loop bounds (4 + 38 = 42), 8-byte `memcmp`, and the writes to `0x030000D0`,
  `0x0300045AC`, `0x03006E94`.
- Index→sprite-set mapping `1..4 → 0x10..0x13`; difficulty flag semantics.

**Inferred**:
- The exact enemy aircraft represented by sprite ids `0x12`/`0x13` (codes #3/#4).
  The ROM text enumerates six enemy types (MiGs, UFOs, Triplanes, Classic Cars,
  Flying Dutchmen, F-14s); the published description for id `0x10` is UFOs and for
  `0x11` is "stick and rudder", but the two undocumented ids were not visually
  identified in a live mission. This does not affect code acceptance, which is fully
  proven.

## 8. Unknowns

- Friendly names for sprite sets `0x12` and `0x13` (would need sprite extraction or a
  long mission where those enemies spawn).
- The purpose of `0x030001BA` (a byte incremented elsewhere) and whether `0x03006E94`
  is a frame counter or an input counter.
- No button-code/debug surface was found; absence is bounded by (a) walking all six
  menu entries plus title/pause, (b) a full-string scan for `debug|secret|cheat|hidden|
  level select` finding only the GAX banner, and (c) a u16 button-mask scan returning
  203 runs, all in compressed-graphics regions with no validator-like comparison.

## 9. Tooling

- `capstone` 5.0.7 (+ `keystone`) for Thumb disassembly (`disasm.py`, `find_ldr.py`,
  `scan_ptrs.py`), `arm-none-eabi-objdump -M force-thumb` for spot checks.
- mGBA 0.10.5, Xvfb `:315`, openbox, xdotool, ImageMagick `import` for screenshots.
- Python helpers: `press.py` (XTEST key holds), `enter_code.py` (grid navigation to
  type a code), `submit.py` (navigate to ENTER), `table_extract.py` (dump the 42
  records), `ss_parse.py` (decompress mGBA `gbAs` chunk and read IWRAM).
- No ROM or copyrighted assets are redistributed; this report contains only hashes,
  addresses and the 42 short code strings already published or recovered from the
  ROM image.

---

**Legal note**: analysis only of a legally held ROM; no game assets, music, graphics,
or full text banks are reproduced here.
