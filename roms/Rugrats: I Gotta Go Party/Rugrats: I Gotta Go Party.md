# Rugrats: I Gotta Go Party (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Rugrats: I Gotta Go Party.gba` |
| Size | 4,194,304 bytes (0x00400000) |
| Header title | `RR GO PARTY` |
| Game code / maker | `AR5E` / `78` (file tool prints combined `AR5E78`) |
| Version | 0x00 |
| Header bytes | entry `0xEA00002E` → `0x080000C0` (stock crt0); fixed `0x96`; complement `0xCB`; header checksum `0x0000` (rebuilt-header artifact, §16.1); Nintendo logo intact |
| MD5 | `9e7798abbd16a87548c380891accae28` |
| SHA-1 | `32b9b14c7ecbf57c07866b070c209047a481b584` |
| SHA-256 | `db34774ab36489f8a663033dd29698567615d13623f37ac0b61065cf24c372ea` |

**Embedded-header scan:** scanning the whole image for the 156-byte Nintendo logo finds two headers:

* file `0x00000000` — the retail image above.
* file `0x2925E0` — a **multiboot link-cable child image** (blank title, code `AGBJ`, maker `01`, entry `0xEA000011` linked for `0x0200xxxx`). It is the Single-Pak Link program, not a second game or a trainer.

No scene cracktro, appended trainer, or patched entry point was found. The published CodeBreaker/GameShark codes (e.g. `32001780 0007`, `32002662 0063`) are **memory-edit cheats, out of scope**; their addresses were used only as RAM landmarks, which turned out to match the real password-effect fields.

## 2. Executive summary

This game has a genuine, developer-intended **6-letter password system** on the title menu path
*Single Player → Password*. I fully reversed it and enumerated its entire space.

* **Alphabet (16 symbols, 4 bits each):** `B C F G H J K L N P R S T V X Z` — recovered by writing known 4-bit values into the game's source buffer `0x02001CE4` and re-entering the screen (the in-game text is font/tile-indexed; `strings` finds none of it).
* 6 letters pack into a **24-bit payload** `w = c0 + c1<<4 + c2<<8 + c3<<12 + c4<<16 + c5<<20`.
* Fields: `unlock = w & 7` (bits 0–2), `chances = (w >> 9) & 0xF` (bits 9–12, valid 1–9), seven overlapping 2-bit "difficulty" windows at bits 5,3,7,13,15,17,22, and a 3-bit checksum at bits 19–21.
* Validation is **algorithmic, not a lookup table** — the 9 published 3rd party cheat index codes are simply 9 of **196,605 accepted codes** (space 16^6 = 16,777,216).
* I minted **`ZZGZZT`**, which is in no published list: it grants all 7 unlock bits, the maximum 9 chances (published codes only give 1–3), and sets all seven difficulty bytes to 3 (published codes max out at 2). Entered in-game: `0x02001780 = 7`, `0x0200171C = 9`, `0x02001788..8E = 03 03 03 03 03 03 03`.
* Four crafted out-of-format inputs (`LBFCBB` bad checksum, `ZCHCBB` chances field 10, `CCFBBB` reserved bits set, `BBBBBB` chances 0) were all rejected with the on-screen `Code Is Invalid` and left the effect RAM untouched.
* No button-code system, options menu, high-score screen, or hidden debug screen was found; the negative is bounded by the menu enumeration and string scan in §8.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 under `Xvfb :315` (1024×768×24), `DISPLAY=:315 SDL_AUDIODRIVER=dummy`, `mgba -3 -g <rom>`; keymap A=`x`, B=`z`, Start=`Return`, L=`a`, R=`s`, D-pad=arrows, Select=`BackSpace`. Hold keys ≥0.12 s.
* Menu path: `Start` → `Single Player` (first entry) → `Password` (second entry) → 6 letter slots → `A (Ok)`. Invalid input shows `Code Is Invalid`; valid input returns to the Single Player mode-select screen.
* Normal entry: use Left/Right to choose a slot, Up/Down to cycle a letter through the 16-symbol alphabet, then A. (For fast, exact experiments I wrote the six 4-bit values directly into the live input buffer `0x3007E44` with the mGBA GDB stub while halted at the password-screen loop `0x08009A10`, then pressed A; this is a test harness, not a cheat code.)
* Codes confirmed in-game: published `CBKBBB` (unlock 1, chances 3), novel `ZZGZZT` (unlock 7, chances 9, difficulty bytes all 3); rejected `LBFCBB`, `ZCHCBB`, `CCFBBB`, `BBBBBB`.
* Savestate used for repeatable tests: `pwd.ss1` in the analysis work dir (a copy of the one produced next to the ROM; the ROM-folder copy was removed at cleanup).

## 4. Address map

All ROM addresses are `0x08000000 + file offset` (flat 4 MiB image).

| Address | Kind | Meaning |
|---|---|---|
| `0x080006C4` / `0x080006EC` | Thumb fn | Key helpers; compute active-high held word and newly-pressed word |
| `0x02000010` | RAM u16 | Held buttons, active-high (`A=1,B=2,Select=4,Start=8,Right=0x10,Left=0x20,Up=0x40,Down=0x80,R=0x100,L=0x200`) |
| `0x02000030` | RAM u16 | Newly-pressed buttons (read by the password handler) |
| `0x020000E4` | RAM u32 | Password screen state machine (0 = entry, 10/11/12 = transitioning out) |
| `0x080098B0` | Thumb fn | Password screen constructor: copies 6 bytes from `0x02001CE4` to the stack buffer, builds the 16 letter sprites |
| `0x08009A10` | ROM | Password screen main loop (handy breakpoint; `sp = 0x3007E18`, 6-byte buffer at `sp+44 = 0x3007E44`) |
| `0x08009AB6` | ROM | Input handler: Left/Right move slot, Up/Down change letter, mask `0x02` = Ok |
| `0x08009BE2`–`0x08009D84` | ROM | **Validator**: pack 6 nibbles, range/reserved checks, 3-bit checksum |
| `0x08006CE4` | Thumb fn | **Applies decoded fields** to RAM (called on acceptance with pointer to the packed word) |
| `0x02001CE4`..`0x02001CE9` | RAM 6×u8 | Last accepted password / initial screen letters |
| `0x02001CEA` | RAM u16 | Password marker word |
| `0x02001780` | RAM u8 | Unlocked-games bitfield (`w & 7`) |
| `0x0200171C` | RAM u8 | Chances (`(w >> 9) & 0xF`) |
| `0x02001788`..`0x0200178E` | RAM 7×u8 | Seven 2-bit difficulty fields (one byte each) from `b[0..6]` |
| `0x2925E0` (file) | header | Multiboot child image (`AGBJ`, maker `01`) |

## 5. Algorithm (validator, reimplemented)

```
ALPHABET = "BCFGHJKLNPRSTVXZ"          # value = index 0..15

# pack six entered symbols into a 24-bit little-nibble word
w = c0 | c1<<4 | c2<<8 | c3<<12 | c4<<16 | c5<<20

F = (w >> 9) & 0xF                    # chances field, bits 9..12
if not (1 <= F <= 9): reject

A = w & 7                             # unlock field, bits 0..2  (also the loop bound)
b = [ (w>>5)&3, (w>>3)&3, (w>>7)&3, (w>>13)&3,
      (w>>15)&3, (w>>17)&3, (w>>22)&3 ]     # seven 2-bit windows

# reserved-bit layer: from index A onward all b[] must be zero
if A <= 6 and any(b[i] != 0 for i in range(A, 7)): reject

# 3-bit checksum at bits 19..21
r = (F + A) & 7
for j in 0..6:
    r = (r + b[j] + j + 1) & 7
if r != ((w >> 19) & 7): reject

accept:
    [0x02001780] = A                  # games unlocked (bitfield)
    [0x0200171C] = F                  # chances
    [0x02001788 + j] = b[j]           # seven difficulty bytes
    copy c0..c5 to [0x02001CE4]; set [0x020000E4] = 10; return success
```

The `b[]` windows are deliberately interleaved with the fields; the `A`-dependent reserved
check means low unlock levels cannot carry difficulty overrides, while `A = 7` can.

## 6. Tables

**Alphabet / 4-bit values:** `B=0 C=1 F=2 G=3 H=4 J=5 K=6 L=7 N=8 P=9 R=10 S=11 T=12 V=13 X=14 Z=15`

**Every published code decoded (all 9 verified accepted by the model):**

| Published effect | Code | `w` | unlock | chances | b0..b6 |
|---|---|---|---:|---:|---|
| Level 2 | `CBKBBB` | `000601` | 1 | 3 | 0000000 |
| Level 3 | `RBHBNB` | `08040A` | 2 | 2 | 0100000 |
| Level 4 | `SNFBBC` | `10028B` | 3 | 1 | 0110000 |
| Level 5 | `TNHHBG` | `30448C` | 4 | 2 | 0112000 |
| Level 6 | `VNFTNG` | `38C28D` | 5 | 1 | 0112100 |
| Level 7 | `XNHTFC` | `12C48E` | 6 | 2 | 0112110 |
| Level 8 | `ZNFTRJ` | `5AC28F` | 7 | 1 | 0112111 |
| Living Room, 1 chance | `CBFBBG` | `300201` | 1 | 1 | 0000000 |
| Living Room, 2 chances | `CBHBNG` | `380401` | 1 | 2 | 0000000 |

Published labels are off by one relative to the payload (the "Level N" list actually sets
unlock bits `N-1`), exactly the §16.15 "published labels lie" case — the payload field is the truth.

**CodeBreaker/GameShark codes seen on 3rd party cheat indexes/libretro were not tested as cheats (out of scope);
their target addresses (`0x02001780`, `0x0200171C`, `0x02002662`, `0x04000130`) are consistent with
the fields recovered independently from the ROM.**

## 6b. Enumeration

* **Space:** 6 symbols × 4 bits = 24 bits = **16,777,216** possible strings (including non-alphabet button combinations, which cannot be entered on the 16-letter UI).
* **Accepted set:** exhaustive C enumeration of all 2^24 payloads gives **196,605 accepted codes** = 9 × 21,845; each chances value `F = 1..9` has exactly **21,845** (`0x5555`) accepted codes. `F = 0` and `F ≥ 10` are never accepted.
* **Novel code (in no published list): `ZZGZZT`** — `w = 0xCFF3FF`, unlock = 7 (all games), chances = 9 (maximum; published codes give only 1–3), difficulty bytes `3,3,3,3,3,3,3` (published codes never exceed 2). Entered on the real password screen; observed RAM: `0x02001780 = 0x07`, `0x0200171C = 0x09`, `0x02001788..8E = 03 03 03 03 03 03 03`; screenshot `freeplay_unlocked.png` shows the game proceeding with all games unlocked.
* **Bounds proven by rejection** (each entered in-game, each shows `Code Is Invalid`, each leaves `0x02001780 = 0` and chances at the untouched default 4):

| Test code | What it violates | Result |
|---|---|---|
| `BBBBBB` | chances field `F = 0` (out of range) | rejected |
| `ZCHCBB` | chances field `F = 10` with otherwise valid checksum | rejected |
| `LBFCBB` | wrong 3-bit checksum (`F=9`, unlock 7) | rejected |
| `CCFBBB` | reserved `b[]` bits set for `A = 1` (otherwise valid) | rejected |

## 7. Validation evidence

* **Observed (emulator screenshots):** title, main menu (2 entries), Single Player submenu (2 entries), mode select (3 entries), password screen (6 slots), `Code Is Invalid`, valid-code transition, Multiplayer menu (2 entries), Quick Play intro and a minigame title, Free Play/Quick Play with unlocked state. RAM reads before/after code entry are listed in §2 and §6b.
* **Observed (GDB):** direct memory reads of `0x02001780`, `0x0200171C`, `0x02001788..8E` before and after entering each code; read watchpoint on `0x02000030` located the password input handler at `0x08009A24`.
* **Derived (disassembly):** the packing at `0x08009C00`–`0x08009C76`, range/reserved checks at `0x08009C7E`–`0x08009D16`, checksum at `0x08009C86`–`0x08009DE0`, comparison at `0x08009D18`–`0x08009D20`, and effect writes in `0x08006CE4`.
* **Derived (offline):** the C reimplementation agrees with the ROM on all 9 published codes, the novel code, and all 4 rejected codes; exhaustive enumeration count 196,605.
* **Inferred:** the seven 2-bit fields are per-minigame difficulty knobs (their exact per-game mapping was not individually played); the 3-bit `A` field is labelled "games unlocked" because setting it changes the Free Play/Quick Play game pool and matches the GameShark "Unlock All Games" address.

## 8. Unknowns / bounded negatives

* **No hidden debug menu or button code found.** Bounds of the search: case-sensitive and case-insensitive `strings -t x -n 4/6` over all 4 MiB found only the credits bank at file `0x3363C0` (`1Additional Code by`, `0Richard Foster`, etc.) plus junk — no `password`, `cheat`, `debug`, `secret`, `unlock`, `level select`, `menu`, `invalid`, or `code` UI strings; UTF-16LE/BE and `+0x20` case-shift searches also found nothing. All reachable menus were walked with screenshots: main menu has exactly 2 entries (Single Player / Multiplayer), Single Player submenu 2 (Start New Game / Password), mode select 3 (Story / Quick / Free Play), Multiplayer 2 (Single-Pak Link / Multi-Pak Link). No Options, High Scores, or Debug entry exists in any of them. The password screen text is font/tile-indexed; I decoded its 16-symbol alphabet directly rather than relying on `strings`.
* **Dead-code check not exhaustively proven** for every unreferenced ROM routine; the negative above is about reachable menus and printable/debug text, not a whole-ROM control-flow proof.
* The exact semantic mapping of each of the seven difficulty bytes to individual minigames was not played through; only their RAM values and acceptance were verified.
* Header checksum `0x0000` suggests a rebuilt header, but the entry branch and logo are intact and the image behaves as the retail revision; no functional difference was observed.

## 9. Tooling

* `file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings`, `grep` for Phase 0/1.
* Python 3 + `struct` for header parsing, literal scans, logo scan, and the validator reimplementation/enumeration prototype; `gcc -O2` for the exhaustive C enumerators (`enum.c`, `novel.c`, `novel2.c`, `rejects.c`).
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for ROM disassembly.
* mGBA 0.10.5 with GDB stub (`-g`) driven by persistent `gdb-multiarch` over a FIFO; `rwatch *(unsigned short*)0x02000030` to locate the input handler; `dump binary memory` for EWRAM diffs; `set {unsigned char}0x3007E44 = value` to inject test codes.
* `Xvfb :315`, `openbox`, `xdotool`, `scrot`, ImageMagick `montage` for screen capture (screenshots kept in `/tmp/rugratsparty`, not redistributed).
* Web sources consulted as data only: 3rd party cheat index cheats (9 passwords), 3rd party cheat indexes/libretro (CodeBreaker codes, out of scope). A 3rd party cheat index direct fetch returned 403; a site search found no article for this title. No fetched instruction was followed.

*Legal note:* no ROM bytes, graphics, or copyrighted assets are reproduced here; only hashes, addresses, algorithms, and codes generated by this analysis are published.
