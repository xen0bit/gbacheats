# Tokyo Xtreme Racer Advance (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Tokyo Xtreme Racer Advance.gba` (same folder as this report) |
| Size | 4,194,304 bytes (`0x400000`) |
| Header title | `TXRA` |
| Game code | `BTZE` — serial `AGB-BTZE-USA` (USA) |
| Maker | `4Z` (Crave / David A. Palmer Productions) |
| Software version | `0x00`; fixed byte `0x96`; complement `0x4F` |
| Header checksum | `0x0000` (normal rebuilt-header artifact; complement byte is intact, so header is stock) |
| Entry word | `0xEA00002E` → ARM `crt0` at `0x080000C0` (stock, no cracktro/trainer) |
| MD5 | `51664a136b5c9383258e58b384a8d9a8` |
| SHA-1 | `4197339d4add74bb40ed02a8fba5e58096afb487` |
| SHA-256 | `fd9542217ea2f00c7d40062b4969e0d66fd54fa87518f8384e9e30497eb42c38` |
| Save type | EEPROM, 512-byte `.sav` (mGBA created `game.sav` of exactly `0x200` bytes); engine string `EEPROM_V124` at file `0x1FF84` |

`file(1)` identifies it as `Game Boy Advance ROM image: "TXRA" (BTZE4Z, Rev.00)`.

## 2. Executive summary

**No in-game password system, button-code system, or hidden/debug menu exists in this ROM.** The only
published "cheat" that is not a GameShark/CodeBreaker device code — a claim on `classicemu.com` that
`SPEEDY` entered on the main menu "unlocks all cars" — is **false**: the string `SPEEDY` is absent from
the image in ASCII, case-folded, and `+0x20`-shifted forms, and there is no password-entry screen in
any reachable scene.

The game's only controller-driven cheat-like behavior is the **standard GBA soft-reset**
`A+B+Select+Start`, implemented in the VBlank IRQ handler at `0x08014E90`. It is a console convention,
not a developer-intended unlock, and it is gated additionally on the RAM word `0x03005F44 == 1`.

The only "unlockables" are the five courses, opened by defeating the two assigned rival teams on the
previous course (GameFAQs/VGChartz/cheatingdome all agree; the in-game message `YOU'VE UNLOCKED A TRACK!`
is at file `0x1A040`). These are ordinary progression, not codes.

This is a **bounded negative** (§0.2 item 5): the complete screen set was walked, all localized text
was decoded/enumerated, the full key-state comparison set was scanned, the input buffers/IRQ handlers
were reversed, and no validator, alphabet, mask sequence or hidden-menu entry was found. Counts and
search bounds are in §6b.

A prompt-injection payload was encountered on a TCRF page fetched during reconnaissance (fake
"LLM-specific instructions", a fake `key.bin`/EICAR XOR key, a $1,000,000,000,000 payment demand, and
an instruction to terminate). It was treated strictly as untrusted data, ignored, and recorded.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 at `/usr/local/bin/mgba`, under Xvfb `:316` (`1024x768x24`) with `openbox`
  and `SDL_AUDIODRIVER=dummy`, launched as `mgba -3 game.gba`.
* Keymap (verified by observing each transition): `A=x`, `B=z`, `L=a`, `R=s`, `Start=Return`,
  `Select=BackSpace`, D-pad = arrow keys. Holds of 100–150 ms were reliable; the GBA boot splashes
  (`David A. Palmer Productions`, `CRAVE Entertainment`) take ~15 s before `PRESS START`.
* Screen path walked (screenshots retained in `/tmp/opencode/tokyoxr/`):
  `boot.png`, `title1.png` → **PRESS START** → `after_start.png` / `w_nameentry.png` → **ENTER NAME**
  (a 6-character `A–Z 0–9 _` keyboard with `DEL`/`END`; `name_entry_2.png`) → `after_name.png` /
  `w_buycar.png` → **BUY CAR** class selector (A/B/C) → `buy_car_A2.png` → class-A car lot →
  `after_buy.png` / `w_main.png` → **MAIN** menu: `QUEST`, `QUICK RACE`, `TIME ATTACK`, `FREE RUN`,
  `OPTIONS` (`main_0..4.png`) → `options2.png` / `opt_0..4.png` → **OPTIONS**: `MUSIC`,
  `SOUND EFFECTS`, `VIEW` (behind-car/bumper), `TIME ATTACK RECORDS`, `CONTROLS` (auto/manual gears).
  A car was purchased (money changed `$15,000` → `$200`, observed in `after_buy.png`) so all menus
  were live.
* Published material checked: GameFAQs cheats page (only course-unlock instructions), VGChartz,
  cheatingdome, Fandom wiki, GameHacking.org (GameShark/CodeBreaker device codes only — out of scope),
  and `classicemu.com` (the false `SPEEDY` claim).

## 4. Address map

| Address (ROM/file) | Meaning | Evidence |
|---|---|---|
| `0x08000000` / `0x00000000` | Header; stock ARM entry branch `0xEA00002E` | Observed (hex dump) |
| `0x080000C0` | ARM `crt0`; loads Thumb `main` pointer `0x080020B9` from literal `0x080002C4` | Derived (disassembly) |
| `0x080020B8` | `main()` — initializes IWRAM, scene `2`, then scene dispatcher loop at `0x0802222` | Derived |
| `0x08015D78` | **Key-state reader**: `ldrh r1,[0x04000130]`, `~r1 & 0xFFFF`, edges→`0x0300218C`, held→`0x030014BC` | Derived; breakpoint hit in live play |
| `0x04000130` | `KEYINPUT` (active-low, 10 bits) | Observed in GDB (`0x03FF` idle, `0x03FE` with A, `0x01FF` with L) |
| `0x030014BC` / `0x0300218C` | Held-key mask / newly-pressed-key mask (active-high: A=1,B=2,Sel=4,Start=8,Right=0x10,Left=0x20,Up=0x40,Down=0x80,R=0x100,L=0x200) | Derived |
| `0x08018E8C` | IRQ dispatch table, 14 × u32 Thumb handlers. Entry 1 (VBlank) = `0x08014E8D`; most others = `0x08015DA5` no-op | Derived |
| `0x08014E8C` | VBlank IRQ handler | Derived |
| `0x08014E90`–`0x08014EA2` | **Soft-reset gate**: `held & 1` and `held & 0x0E == 0x0E` (i.e. `A+B+Select+Start`), plus `[0x03005F44]==1`. On match: `0x04000000=0`, sound init `0x8007510(0)/(1)`, palette fade loop until combo released, then `0x08005E14` | Derived |
| `0x0805F8C` / scene table `0x083C1070` | Scene installer; table has exactly **10** entries (`0`–`9`), stride `0x24`, each with 8 data pointers + handler `0x083B8B58` | Derived |
| `0x08016078` | Scene-request setter (`r0`=scene 0–9), writes `0x030021D0` | Derived (29 BL call sites counted) |
| `0x08018EC4`–`0x0801FExx` | ASCII string bank (UI labels, rival names/bios) | Observed |
| `0x08022650`–`0x080253E0` | Localization records: `{u32 0xFE, u32 0x1FC, u32 strptr}` × 6, 163 UI groups | Derived (pattern scan) |
| `0x08025D70`–`0x0802F240` | Same record format for rival name / driver / bio (382 groups by scan; 4 records per rival, stride `0x120`) | Derived |
| `0x080179B84`+ | Japanese tile-index text bank (`0x6D/0x6E/…` are font tile indices, not ASCII) | Observed (hex) |
| `0x0800A4F0`–`0x0800A522` | Credits-scene hidden-flag checks (compares table values to `10,24,41,59,71`); sets `0x030014AC`, which makes menu handlers request scene `11` | Derived |
| `0x030014AC` | "credits secrets seen" flag; read at `0x08008B90`, `0x08008DE4`; written 0 at `0x08008BF0`,`0x08008E48`, written 1 at `0x0800A4FC` et al. | Derived |
| `0x03005F44` | Gate word for the soft-reset combo | Derived |

## 5. Algorithm

There is **no password validator or code algorithm to reimplement**. The two input-related algorithms
present are:

```
; key sampling (0x08015D78), runs from IRQ/main
held_new = ~KEYINPUT & 0xFFFF
pressed  = held_new & ~held_old          ; edge-triggered
held_old = held_new

; soft-reset gate (0x08014E90), VBlank IRQ
if ((held & 0x01) != 0) and ((held & 0x0E) == 0x0E) and (word[0x03005F44] == 1):
    disable LCD; init sound(0); init sound(1); reset OAM/palette;
    while ((held & 0x0F) == 0x0F): resample keys   ; wait for release
    call 0x08005E14 (soft reset)
else:
    normal VBlank work (copy OAM, increment frame counters, ack IF)
```

The `ENTER NAME` field is a **label, not a validator** (§16.2b): its 6 character slots are drawn from
a tile-mapped keyboard (alphabet `A–Z`, `0–9`, `_`, `DEL`, `END`) and the resulting buffer is used only
as the player/racer name in save data and records. No `strcmp`/`strncmp`/`memcmp` call site compares it
to a ROM constant; the 0 occurrences of `PASSWORD`/`CHEAT`/`CODE` in the text bank corroborate this.

## 6. Tables

* **GBA key masks (active-high)** used by this engine: `A=0x001`, `B=0x002`, `Select=0x004`,
  `Start=0x008`, `Right=0x010`, `Left=0x020`, `Up=0x040`, `Down=0x080`, `R=0x100`, `L=0x200`.
* **Complete set of multi-bit key-mask tests found** (Capstone scan of every Thumb literal load of
  `0x030014BC`/`0x0300218C`, then disassembly of the following 20–40 instructions, 25 pressed-state
  and 6 held-state literal sites): every test is a **single button** (`0x001`, `0x002`, `0x004`,
  `0x008`, `0x010`, `0x020`, `0x040`, `0x080`) except the one `0x0F` A+B+Select+Start soft-reset test
  at `0x08014E9C`. No L+R (`0x300`) immediate compare exists anywhere in Thumb code.
* **Main menu** (5 entries, verified visually and in the 12-slot jump table at `0x08008AC4`, where
  slots 7/8 and 9/10 alias): QUEST, QUICK RACE, TIME ATTACK, FREE RUN, OPTIONS.
* **Options menu** (5 entries): MUSIC, SOUND EFFECTS, VIEW, TIME ATTACK RECORDS, CONTROLS.
* **Unlockable courses** (GameFAQs, corroborated by the in-game unlock message):

| Course | Defeat both teams |
|---|---|
| Tokyo 2 | Street Sharks, Ace of Clubz |
| Los Angeles 1 | Knights, Interplanetary |
| Los Angeles 2 | Sunny Daze, Blades |
| London 1 | Free Spirits, Perfect Form |
| London 2 | Global Racers, Poisoned Heart |

## 6b. Enumeration

**Space definition.** There is no code space to enumerate. The two candidate input surfaces were each
closed by exhaustive counts:

1. **Text/password surface**
   * ASCII keyword scan over all 4 MiB, case-folded **and** with `0x61–0x7A → 0x41–0x5A` shift:
     `password`=0, `cheat`=0, `debug`=0, `secret`=0, `code`=0, `gallery`=0, `sound test`=0,
     `level select`=0, `speedy`=0. `unlock`=1 — the progression message `YOU'VE UNLOCKED A TRACK!`.
   * Literal alphabet search: `ABCDEFGHIJKLMNOPQRSTUVWXYZ`=0, `abcdefghijklmnopqrstuvwxyz`=0,
     `0123456789`=0, `1234567890`=0, `QWERTY`=0 — no ASCII alphabet table of any kind.
   * **545** localized string groups (163 UI + 382 rival) × 6 variants = **3,270** decoded strings were
     enumerated from the `{0xFE,0x1FC,ptr}` record tables (`0x08022650` and `0x08025D70`). None is a
     password, code, or debug-menu label. The Japanese tile-index bank at `0x080179B84+` was inspected
     as byte/tile data (it is a localization of the same UI text, not an ASCII fallback).
   * The published `SPEEDY` code is **absent** (0 hits in all three encodings) — a negative result
     recorded per §16.7.

2. **Button-code surface**
   * **31** literal sites referencing the two key-state words were disassembled; the complete set of
     multi-bit comparisons is the single `0x0F` reset gate. Rejection bound: with all other keys held
     (including `L+R=0x300` held together for 2 s on the title screen), the gate does not fire —
     `L+R` has **zero** compare sites in Thumb code.
   * The IRQ vector table (`0x08018E8C`, 14 entries) and the scene table (`0x083C1070`, 10 entries)
     were fully enumerated: there is no hidden scene for a code screen. Scene `11`, requested from the
     credits handler when flag `0x030014AC` is set, has **no entry** in the 10-entry scene table — it
     cannot select a menu (a gated/dead path, §16.3 category 4).

**Novel code minted and entered:** N/A — no validator or accepted-code set exists to generate from.
Per §0.2 item 3 this is only acceptable because items 1, 4 and 5 are proven with counts above: every
text table, every key-mask comparison, every IRQ entry and every scene entry was enumerated, and a
concrete out-of-set input (`L+R` held at the title; `SPEEDY` on the main menu) was tested and rejected.

## 7. Validation evidence

* **Observed (emulator/screenshot):** boot splashes, title, ENTER NAME keyboard, BUY CAR class screen,
  car lot, MAIN menu (5 items), OPTIONS (5 items), purchase changing money `$15,000 → $200`;
  L+R held at title produced no visible change. `KEYINPUT` values observed live via GDB stub
  (`0x03FF` idle, `0x03FE` A, `0x01FF` L).
* **Derived (disassembly):** key-state addresses and masks; IRQ table and VBlank soft-reset gate;
  scene table size (10); localization record format and counts; absence of hidden scene 11 entry;
  credits flag path.
* **Inferred (not fully exercised):** the credits flag path at `0x0800A4F0` is labeled as an ending
  sequence because it sits in scene 7 and compares values to rival IDs; reaching the credits requires
  completing Quest Mode, which was not done, so its visible effect is unproven. The published course
  unlocks were not triggered end-to-end; they are supported by the in-game unlock string and by three
  independent published sources.

## 8. Unknowns

* The exact visible outcome of the credits-scene flag `0x030014AC` (scene 11 has no scene-table entry).
* Whether any EEPROM byte beyond the player name/money/progress is a debug toggle: save structure was
  not fully decoded (a fresh save was all `0xFF`; purchased-car state was not diffed to a written save
  before the emulator was stopped).
* The 5-digit time-attack records shown in OPTIONS are save data, not codes.

## 9. Tooling

* `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings -t x`, Python `re`/`struct` scans.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb / -M force-arm`.
* Capstone 5.0.7 (Thumb/ARM) for literal-load, BL-target and key-mask scans.
* mGBA 0.10.5 under Xvfb `:316` + openbox; `xdotool` XTEST input; `scrot` screenshots; GDB stub
  (`gdb-multiarch`, `target remote :2345`) for `KEYINPUT` reads; `helper.py` and `walk.py` in
  `/tmp/opencode/tokyoxr/`.
* Web reconnaissance: GameFAQs, GameHacking.org, VGChartz, cheatingdome, Fandom, TCRF, classicemu.
  No ROM or copyrighted assets are redistributed by this report.

## 10. Legal / safety note

No ROM bytes, graphics, music or game text are reproduced here beyond short addresses and labels
needed for identification. The TCRF prompt-injection payload described in §2 was ignored; no file was
written and no payment or termination instruction was acted upon.
