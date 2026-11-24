# Hamtaro: Ham-Ham Heartbreak (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Hamtaro: Ham-Ham Heartbreak.gba` |
| Size | 8,388,608 bytes (`0x800000`) |
| `file` | Game Boy Advance ROM image: "HAMUTARO3" (AH3E01, Rev.00) |
| Header title | `HAMUTARO3` |
| Game code | `AH3E` / maker `01` (Nintendo) / version `0x00` |
| Header bytes | fixed `0x96` OK; complement `0x5B`; header checksum `0x0000` (normal rebuild-style retail value) |
| Entry word | `0xEA00002E` → stock branch to `0x080000C0` |
| MD5 | `42cca53c94c0bb8e5146631945bf0cd9` |
| SHA-1 | `2525cc23524068dfb3a2b4e0ce7b736f95023e82` |
| SHA-256 | `06f359a322fdba920c35ee0c794f1520a7f1b52827e372dd69c5fff648e6ae3d` |

**Embedded-header / patch scan (Phase 0):** the full 156-byte Nintendo logo occurs exactly **once**, at file offset `0x4` (header base `0x0`). There is one game image, no multiboot stub, no appended trainer, no cracktro. The first 4 KiB is a clean standard crt0 (`0x080000C0: mov r0,#0x100; ...`). CRC32 `CD48B673`, serial `AGB-AH3E-USA` (GameHacking.org listing) match this image.

## 2. Executive summary

**There is no in-game password, cheat-code, button-code, level-select, or hidden debug-menu system in this ROM.** The game is a licensed Pax Softonica adventure whose only "cheats" in the public press are (a) save-flag-gated unlockables — 10 Ham-Jam songs and three ending cinemas — and (b) CodeBreaker/GameShark **memory-edit** codes, which are out of scope. No developer-intended code surface exists to enumerate, mint, or validate.

Evidence for the negative is bounded rather than absence-by-omission:

1. The title screen, name-entry flow, confirmation screens, intro cutscenes and in-game field screens were all walked in mGBA; the title menu exposes exactly **one** entry (`New`) on a fresh save, and D-pad Down does not change selection (RAM diff shows only the input direction-code byte changing).
2. `strings` over the whole image: `password` ×0, `PASSWORD` ×0, `cheat` ×0, `CHEAT` ×0, `level select` ×0, `DEBUG` ×0; `debug` ×1 (dead text, below), `secret` ×12 (ordinary item/narrative words in the tokenized text bank). The UI text is a **tokenised/dictionary-compressed text bank** at file `0x46xxxx`, which was decoded by hand (leading byte = compressed word fragment, `0x01` = space). The visible UI labels `Continue / Item / Name / Boutique / Area Clear / Save Data / Ham-Ham Dictionary / Animation / Yes / No` are all present in that bank and pointed to by the text-ID table at `0x084AA8C0`; **no** password/debug/level-select label exists in it.
3. The nine widely-published 9-character "friend card" passwords (`AU3GMWN3A`, `6DHY4QCPD`, `U9M3WNDFY`, `W49UTANVG`, `39UTPVJAW`, `NPUF9E6MP`, `9H3MAVHJJ`, `MT79UVTJR`, `VYFW9MAQ9`, `P74AHWHPT`, `TAWA4FM3X`) belong to a **different game** — *Hamtaro: Ham-Ham Games* (AlphaDream, 2004). This is the §16.11 title-franchise trap. None of these literals appears in this ROM under ASCII, +0x20, or any direct byte encoding.
4. The single `debug` occurrence — decoded text "Sound debug mode" at file `0x46C243` (ROM `0x0846C243`), followed by "Sound changes", "Listen", "quit" and unique control sequences `E2 F5 05 D1` / `E2 F5 00 D1` — has **no 32-bit pointer** anywhere in the image and is **not** an entry in the text-ID table. It is orphaned development text (guide §16.3 case 2: dead code), not a reachable screen.
5. Nine simultaneous-button combos on the title screen, eight boot-time holds, and five button sequences (including the Konami code and the *Hamtaro 4* hidden-coloring code `L,L,B,A,R`) were pressed in the emulator. No hidden menu appeared; the only observable state change was ordinary new-game start and a title-screen cursor animation.

Per guide §16.18 the song/ending unlocks are save-bit flags, not codes: they cannot be entered, generated, or brute-forced, and no published source describes a code entry path for them.

## 3. How to reproduce

```bash
Xvfb :318 -screen 0 1024x768x24 &
DISPLAY=:318 openbox &
export DISPLAY=:318 SDL_AUDIODRIVER=dummy
ROM="roms/Hamtaro: Ham-Ham Heartbreak/Hamtaro: Ham-Ham Heartbreak.gba"
mgba -3 "$ROM" &
W=$(xdotool search --name mGBA | tail -1); xdotool windowfocus "$W"
# IMPORTANT: capture with `import -window "$W" out.png`.
# `scrot` on the root window returns black for mGBA's GLX canvas in this environment.
```

Keymap (verified against RAM, see below): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrow keys. Hold keys 70–150 ms.

Menu path walked: power on → Nintendo logo → copyright (1× Start) → title (`New`) → A → player-name keyboard (navigate to `end`, A) → player confirmation (Down, Right, A) → partner-name keyboard (navigate to `end`, A) → partner confirmation (Down, Right, A) → "Are they really OK?" (A on Yep-P) → heart/ amusement-park intro → bedroom field → Clubhouse dialogue. Documented system reset is Start+Select+A+B held together (confirmed: returns to Nintendo logo).

Savestates were taken with `Shift+F1..F4` (written into the ROM folder as `.ss1`–`.ss4`). mGBA 0.10.5 savestates are PNG with a zlib `gbAs` chunk; `zlib.decompress` yields 397,312 bytes with IWRAM at `state+0x19000` and EWRAM at `state+0x21000`.

## 4. Address map

| Item | File offset | ROM / RAM address | Type | Note |
|---|---:|---|---|---|
| Header / entry | `0x000` | `0x08000000` | data | stock `0xEA00002E` |
| Nintendo logo | `0x004` | `0x08000004` | data | only occurrence |
| Input read routine | `0x009614` | `0x08009614` | Thumb fn | reads `KEYINPUT` literal `0x04000130` at `0x0800966C`, mask `0x03FF` at `0x08009670` |
| Input state struct | — | `0x03000820` | IWRAM | `+0` held (active-high), `+2` pressed, `+4` released, `+6` repeat counter, `+8` d-pad direction code |
| Previous-key word | — | `0x03000838` | IWRAM | previous held mask |
| Text-ID pointer table | `0x4AA8C0` | `0x084AA8C0` | table | `u32` pointers to tokenised strings (`Continue`, `Item`, `Name`, `Boutique`, `Area Clear`, `Save Data`, `Ham-Ham Dictionary`, `Yes`, `No`, …) |
| Tokenised text bank | `0x46A000`–`0x46D000` | `0x0846A000`–`0x0846D000` | compressed text | leading byte = word-fragment token, `0x01` = space, `0x00` = terminator, `>=0x80` = control codes |
| Orphan "debug mode" text | `0x46C243` | `0x0846C243` | dead text | "Sound debug mode" + `E2 F5 05 D1`; no xref |
| Save image | — | cart SRAM/Flash | save | 32 KiB `.sav`, header `HAMUTARO3\0\0\0AH3E` + timestamp |

Input-state RAM evidence (savestate reads, IWRAM base `state+0x19000`):

* Holding `x` (A): `0x03000820 = 0x0001` — bit 0 = A active-high.
* Holding `Return` (Start): `0x03000820 = 0x0008` — bit 3 = Start.
* Pressing Down on the title screen changed `0x03000828` from `0x0000` to `0x0005` (d-pad direction code produced by the table lookup at `0x08009684`–`0x0800969C`), while the selected menu entry remained `New`.

## 5. Algorithm

No password validator, checksum, key schedule, or code generator exists in this image; there is nothing to reimplement. Two small algorithms were recovered because they are the relevant input/text surfaces:

**Input decode (`0x08009614`) — active-high button state:**

```
held    = 0x03FF & ~KEYINPUT                 # 0x04000130, active-low
pressed = held & ~prev
released= ~held & prev
state[0]=held; state[2]=pressed; state[4]=released
state[8]=dir_table[(held & 0xF0) >> 4]       # d-pad → direction code
prev = held
```

Button bit masks (`1 << n`): A=0, B=1, Select=2, Start=3, Right=4, Left=5, Up=6, Down=7, R=8, L=9. `L|R = 0x0300`; documented reset `Start|Select|A|B = 0x000F`.

**Text bank decode (for the negative proof):** bytes `0x20`–`0x7E` are literal ASCII; `0x00` terminates; `0x01` is a space; small bytes `0x02`–`0x22` are compressed word-fragment tokens (e.g. `0x0E`→"Cl", `0x1E`→"S", `0x0F`→"P/D", `0x22`→"W"); bytes `>=0x80` are control codes with parameters. Decoded example: `1E 6F 75 6E 64 00` → "Sound"; `01 64 65 62 75 67 01 6D 6F 64 65 E2 F5 05 D1` → " debug mode" + control.

## 6. Tables

**Unlocked content (save-bit flags, not codes):**

| Category | Entries | Gate (published / observed) |
|---|---|---|
| Ham-Jam songs | Hamtaro Time (default), Condor's Wings, Dizzy for You, Flower Waltz, Go Ham Rangers, Great Springs, Hamour, Hidden Riches, Monkey Salsa, Moonlight | story/item flags; no entry code |
| Ending cinemas (view via Lookie on Clubhouse TV) | Nightmare (available from start), Couples, Duet, Ham-Hams | clear flags / completion |

**Published "cheats" that are out of scope (verified as memory edits, not in-game codes):** CodeBreaker master `0000D435 000A / 100E3AA8 0007`; infinite seeds/acorns/rocks at `0x0201D0C2/C4/C6`; "Have All Items" `83002184 FFFF …`; "Press Select During Transitions" `D0000020 0004 / 320039F0 0001`. These set RAM directly and are GameShark/CodeBreaker codes; no UI accepts them.

**UI alphabet (player/partner name entry, 7 characters):** `A B C D E F G H I J K L M N O P Q R S T U V W X Y Z`, `0 1 2 3 4 5 6 7 8 9`, `( ) < > - / \ _ ; . " ' , ? # ♡ & *`, plus a `♪` glyph and an `end` cell. This is a name-entry field (guide §16.2b): comparisons against its buffer are name-display only; no `strcmp`/validator consumes it as a code.

## 6b. Enumeration

**Code space size: 0.** There is no alphabet/length/checksum/lookup table for a code, so no value can be minted and no bounds can be demonstrated by rejection. The requirement to generate an unpublished code is *not applicable* (the system does not exist), and the negative is proven over the following checked spaces:

| Space searched | Result | Count / method |
|---|---|---|
| Whole-ROM ASCII strings (`strings -n 4`) | 87,201 lines; `password`/`cheat`/`level select` = 0 | `strings -t x -n 4`, case-insensitive keyword grep |
| Keyword literals | `password` ×0, `PASSWORD` ×0, `cheat` ×0, `CHEAT` ×0, `level select` ×0, `debug` ×1, `DEBUG` ×0, `secret` ×12 | `bytes.count()` over all 8 MiB |
| Published 9-char friend-card passwords | 11/11 absent | literal `grep -abo` for each; belong to *Ham-Ham Games* |
| Text-ID table `0x084AA8C0` and neighbours | ~200 string pointers decoded; menu labels only, no code/debug entry | `u32` pointer enumeration |
| `u32` pointers to orphan debug text | 0 | full-ROM `u32` scan for `0x0846C243` and surrounding addresses |
| `u16` offsets to orphan debug text | no canonical base produces a unique xref (base `0x46C000` yields thousands of coincidental matches) | full-ROM `u16` scan |
| Reachable screens (fresh save) | copyright, title (1 item: New), player keyboard, player confirm, partner keyboard, partner confirm, "Are they really OK?", heart intro, amusement-park intro, bedroom field, Clubhouse dialogue | screenshots + savestate RAM snapshots |
| Gated screens | Ham-Ham Dictionary / Status / Ham-Jam / Dress Up exist as label strings but did not open at the pre-first-Ham-Chat story point (Start/Select produced no menu; Start key verified as `0x0008` in RAM) | emulator + RAM |
| Simultaneous combos on title | L+R; L+R+Start; L+R+Select; L+R+A+B; Start+Select; L+Start; R+Start; A+B; Select+A | 9 combos, montage evidence, no screen change |
| Boot-time holds | L+R; L+R+Start; L+R+B; L+Start; R+Start; Start+Select; A+B; Select+A | 8 holds, no screen change |
| Sequences on title | Konami code; `L,L,B,A,R` (the *Hamtaro 4* coloring cheat); Up/Down alternating; Select+A×3; Start+Select+A+B | 5 sequences; only ordinary new-game start / documented reset |
| Raw key-mask table scan | no contiguous button-code table identified; apparent u16 "runs" in code are Thumb instruction halves, not data | Capstone/objdump cross-check of `0x08009614` |

**Published claims verified:** GameFAQs lists only "Unlockable Songs" and "Watch the Endings Again" (Lookie on Clubhouse TV) for this SKU; the archived GameFAQs/GameHacking/Neoseeker pages confirm. A Japanese hidden-features roundup states *Tottoko Hamtaro 3* has no hidden elements/cheats information, while the `L,L,B,A,R` coloring code is explicitly attributed to *Hamtaro 4*, a different game. All of this was checked against the ROM as described above.

## 7. Validation evidence

* **Observed:** every screen listed in §6b captured with `import -window` on `DISPLAY=:318`; savestate RAM reads at `0x03000820` (A=`0x0001`, Start=`0x0008`), `0x03000828` direction code changing on Down; title menu unchanged after all tested combos; published 9-char passwords absent.
* **Derived:** input routine `0x08009614` decodes active-high held/pressed/released from `0x04000130` with mask `0x03FF`; the tokenised text bank and its pointer table contain only ordinary UI/dialogue labels; the orphan "Sound debug mode" string has no `u32` xref.
* **Inferred (labelled):** "Sound debug mode" is leftover development text rather than a reachable debug screen, based on it being the sole `debug` occurrence, its absence from the text-ID table, and the negative combo/screen walk. It was not proven by executing a debug-menu handler, because no such handler was located.

## 8. Unknowns

* Ham-Jam / Dress Up / Status / Dictionary were not entered: they are gated behind story progress (first Ham-Chat word / save flags). Their existence is established from the text-ID table and manual, but their full contents were not enumerated in this fresh-save run.
* The exact mechanic that enables the title-screen `Continue`/`Ham-Jam`/`Dress Up` entries on a completed save was not isolated (it is a save-flag gate, not a code).
* The token dictionary's complete byte→fragment mapping was not reconstructed; only the entries needed to decode the searched labels were derived. This does not affect the keyword/xref counts, which were done on raw bytes.

## 9. Tooling

`mgba 0.10.5` (SDL, `-3` scale), `Xvfb :318`, `openbox`, `xdotool`, ImageMagick `import`/`montage`, `strings`, `grep`, `xxd`, Python 3 (`struct`, `zlib`, `capstone 5.0.7`), `arm-none-eabi-objdump -M force-thumb`. Savestate RAM extraction: parse PNG `gbAs` chunk → `zlib.decompress` → read IWRAM at `+0x19000`.

No ROM or copyrighted assets are redistributed; this report contains only hashes, addresses, and derived findings.

## Legal note

Analyzed a legally obtained ROM for research. No ROM image, screenshot, extracted graphic, or game text is published here beyond short UI labels needed to document the negative.
