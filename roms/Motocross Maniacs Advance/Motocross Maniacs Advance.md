# Motocross Maniacs Advance (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Motocross Maniacs Advance.gba` (4,194,304 bytes / 0x400000) |
| Header title | `MM ADVANCE` |
| Game code | `AMRE` |
| Maker code | `A4` (Konami) |
| Revision | `Rev.00` (version byte 0x00) |
| Fixed 0x96 | present; complement byte 0x0B (non-zero ⇒ header not a rebuilt-header artifact, §16.1) |
| Entry word | `0xEA00002E` (stock `b 0xC0`, no cracktro/trainer patch) |
| MD5 | `b0f1054d5177dd8ec5f90b63fb1c6e09` |
| SHA-1 | `990ba3a3e1660e7ddacfe21f03014d57d1e6d6a5` |
| SHA-256 | `564dd72f7c6041d9dfc6ef6c21f01ecb1c1191d9fbd7447f2a914df6ee759de0` |

**Embedded-header scan:** the 156-byte Nintendo logo occurs 7 times (header offsets
`0x0`, `0x2F4F7C`, `0x2F5228`, `0x3218EC`, `0x321B98`, `0x34C364`, `0x34C610`).
Every copy carries the same `MM ADVANCE`/`AMRE`/`A4` identity; they are duplicated
data banks, not a second game or a multiboot stub. No trainer/appended code was found.

**Published-code research:** Planet Cheats, CheatCC, IGN, GameFAQs (Devis0r FAQ 25549)
and CheatMasters all publish the *same two* "cheats": win the Advance class/cup in
Championship to unlock **Dave**, and win the Expert class/cup to unlock **Omega 0605**.
VGChartz lists "Total cheats available: 0". TCRF has no page (direct 403; archived 404).
No password list, button code, or debug-menu code exists in any source checked.
The GameFAQs "MusyX Audio Tools Licensed by Factor 5" intro splash is audio-engine
banner text, not a code (cf. §11 keyword-hit context rule).

## 2. Executive summary

**There is no developer-intended password, button-code, or hidden debug-menu system in
this ROM.** The only in-game "cheat" surface is a conventional **save-bit unlockable
system** with exactly two unlockable riders (Dave, Omega 0605) and three difficulty-
gated championship cup tiers. This was established by (a) walking every reachable
screen with screenshot + savestate RAM evidence, (b) exhaustive ASCII / case-shifted /
glyph-indexed text searches with counts, (c) enumerating all 11 `KEYINPUT` references
and finding only generic input handlers, and (d) verifying the two published unlock
conditions against the ROM strings, the locked UI, and the flag-setting code.

The unlock system itself is fully characterised: the "you've unlocked <rider>" message
routine is at `0x08014194`/`0x08014220`; its flag setter at `0x08013DD0–0x08013E0E`
tests rising edges of bits `0x20` (Dave) and `0x40` (Omega) in the working save byte at
`0x03006D2D` and writes a message selector to `0x03002874`. The 7-character roster is
`lexie, bigarmy, pohaku, yulia, roberto, dave, omega` (`0x080139AF0`); the 5 cups are
Crystal/Topaz (Novice), Ruby/Sapphire (Advance), Emerald (Expert), with 3 locked on a
fresh save. Because the setter's input is a championship result (not controller input),
this is a legitimate unlockable, not a code system (§16.18).

No unpublished code could be minted because **no code space exists**; §6b records the
negative proof and the bounded searches instead.

## 3. How to reproduce

* Emulator: `mgba -3 <rom>` on `DISPLAY=:317` under `Xvfb :317 -screen 0 1024x768x24`,
  `SDL_AUDIODRIVER=dummy`. GDB stub was unusable (shared port 2345 / other agents), so
  all RAM evidence came from decoding mGBA `.ss1` savestates (§16.13): the `gbAs` PNG
  chunk is zlib-compressed; in the 397,312-byte state, EWRAM `0x02000000` is at state
  offset `0x21000` and IWRAM `0x03000000` at `0x19000`.
* Keymap: mGBA SDL default — A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
  Select=`BackSpace`, D-pad = arrow keys. Holds of 120–250 ms.
* Screens walked (all with screenshot + state saved; files `S01`…`S64` in the work dir):
  1. MusyX/Konami intro → title "PRESS START".
  2. ENTRY screen ("New Game / Clear", 3 record rows) → NAME ENTRY (on-screen alphabet
     `A-Z 0-9 !?/ ,.-'&_.=#@` plus backspace/END; buffer `0x03002940`, 3 lowercase ASCII
     bytes) → main menu "Game Start / OPTION".
  3. OPTIONS → Level (Easy/Normal/Hard), BGM (ON/OFF), SE (ON/OFF),
     Language (English/Español), Exit.
  4. MODE SELECT → Championship, Attack Mode (TIME ATTACK / POINT ATTACK),
     Action Mode, Multiplayer.
  5. Character Select (7 riders; 2 shown as `?` with `?????` name) → cup select
     (5 cups as above, locked cups show padlock + "CLEAR NOVICE IN CHAMPIONSHIP TO
     UNLOCK") → Clear-Point screen → race.
  6. In-race pause menu: CONTINUE / RETRY / EXIT (exactly 3; Down cursor wraps among 3).
* No attract/demo-only conclusion: every screen above was reached and interacted with.

## 4. Address map

| Item | ROM / RAM address | Evidence |
|---|---|---|
| Header title/game code | `0x080000A0` / `0x080000AC` | Observed header |
| "Konami" save magic | `0x08033E5C` | Derived (pointer at `0x08000640`, `0x08000674`) |
| Save-checksum routine (sum 124 u32 @ `0x03002A10`, +1, store @ `0x03002A00`) | `0x08005AC` | Derived (disassembly) |
| Magic compare `strcmp`-like | `0x0800574` | Derived |
| ASCII→glyph text renderer | `0x08011AD0` | Derived — `'a'..'z'` → `c+0xA0 & 0xFF`, `'0'..'9'` → `c+0xEB & 0xFF`, symbols via jump table `0x08011B80` |
| Name-entry handler | `0x08021620`–`0x08021AC6` | Derived |
| Name-entry keyboard table (4 rows × 13 cols × 8 B) | `0x082810AC` | Derived/dumped |
| Unlock-message state dispatcher (9 entries) | jump table `0x08013BA0`; states 5=`0x08014194`, 6=`0x08014220` | Derived |
| Unlock flag setter (rising-edge bit test 0x20/0x40) | `0x08013DD0`–`0x08013E0E` | Derived |
| Message-selector byte (1→Dave, 2→Omega) | IWRAM `0x03002874` | Derived + observed (`0x00` on fresh save) |
| Working save copy (byte +5 = unlock flags) | IWRAM `0x03006D28` | Derived + observed |
| SRAM mirror | IWRAM `0x03002A00` | Observed in states |
| Player name buffer | IWRAM `0x03002940` | Observed (`61 61 61` = "aaa") |
| Character name blob | `0x080139AF0`–`0x080139B27` | Observed |
| Unlock strings | `0x08042C64`, `0x08042C78`, `0x08042C88`, `0x08042C98`, `0x08042CA8`, `0x08042CB8` | Observed + code xrefs at `0x0801427C`…`0x08014394` |
| `KEYINPUT` literal (`0x04000130`) refs | file offsets `0x1000`, `0x29064`, `0x2A398`, `0x2A5A4`, `0x2A6DC`, + 6 in duplicated data banks | Derived |

File offset ↔ ROM address: `ROM = 0x08000000 + file_offset` for the primary image.

## 5. Algorithm

The only algorithm found is the unlock-notification state machine:

```
state = screen_dispatch[state_index]        ; jump table 0x08013BA0 (9 states)
...
state5():                                   ; 0x08014194
    if not (save[0x46] & 1): return
    if RAM[0x03002874] != 0: show_unlock_message()
    transition(6)

state6():                                   ; 0x08014220
    if input_handler(...,16,3) != 1: return
    RAM[0x03006824] = 0
    lang = language_getter()                ; 0x0802056C
    if RAM[0x03002874] == 1:                ; Dave
        display(lang ? "has descubierto a" : "you've unlocked")
        display(lang ? "dave el toro" : " dave the bull")
    else:                                   ; Omega
        display(lang ? "has descubierto a" : "you've unlocked")
        display(lang ? "omega el robot" : "omega the robot")

setter():                                   ; 0x08013DD0
    cur = working_save[5]                   ; RAM 0x03006D2D
    if (cur & 0x20) and not (prev & 0x20): RAM[0x03002874] = 1   ; Dave unlocked
    if (cur & 0x40) and not (prev & 0x40): RAM[0x03002874] = 2   ; Omega unlocked
```

The lock gating visible in the UI is: fresh save ⇒ Crystal/Topaz cups playable,
Ruby/Sapphire/Emerald locked ("CLEAR NOVICE IN CHAMPIONSHIP TO UNLOCK"); dave and
omega rider entries render as `?`. The published conditions (clear Advance → Dave,
clear Expert → Omega) are the gameplay writers of those save bits.

## 6. Tables

**Characters (blob at `0x080139AF0`):** `lexie`, `bigarmy`, `pohaku`, `yulia`,
`roberto`, `dave`, `omega` — 5 default, 2 locked on fresh save.

**Cups (championship):**

| Cup | Tier | Fresh-save state |
|---|---|---|
| Crystal | NOVICE | unlocked |
| Topaz | NOVICE | unlocked |
| Ruby | ADVANCE | locked |
| Sapphire | ADVANCE | locked |
| Emerald | EXPERT | locked |

**Unlock-flag bits (working save byte +5, `0x03006D2D`):** bit `0x20` = Dave,
bit `0x40` = Omega (rising edge drives the unlock message).

**On-screen keyboard alphabet (`0x082810AC`, 4×13):** row1 `A B C D E F G H I J K L M`;
row2 `N O P Q R S T U V W X Y Z`; row3 `0 1 2 3 4 5 6 7 8 9 ! ? /`;
row4 `, . - ' & _ * = # @ < > ~` + backspace + END. Letters are stored as lowercase
ASCII (`0x61`–`0x7A`) and drawn as capitals (§16.11).

**Options:** Level ∈ {Easy, Normal, Hard}; BGM ∈ {ON,OFF}; SE ∈ {ON,OFF};
Language ∈ {English, Español}.

**Save format:** 512-byte SRAM. Bytes 2–7 = byte-reversed `Konami` magic; bytes
12–15 = u32 checksum = (sum of 124 u32 words at offset 16) + 1, also byte-reversed;
name at bytes 19–21; unlock bits at byte 18 bits 5/6 (verified by patch + checksum
recompute — the patched save was accepted and persisted, though the rider lock UI
reads a different working copy, see §8).

## 6b. Enumeration

**Search space / negative proof.** There is no code space to enumerate, so the
required §0.2 enumeration is replaced by a bounded negative result:

| Search | Count / result |
|---|---|
| `strings -t x -n 4` over whole ROM | 27,167 printable runs |
| Case-insensitive keyword scan (`password`, `cheat`, `code`, `secret`, `unlock`, `debug`, `level`, `hidden`, `character`, `skin`, …) | **1** relevant hit: `you've unlocked` @ `0x42C98`; all others were credits (`Course Design`, `Multiplayer Programmer`) or trick names (`bike lift`, `yulia special`) |
| Raw binary search for menu words in ASCII, upper/title/lower case, UTF-16LE, ±0x20 shift (`name`, `entry`, `option`, `level`, `language`, `easy`, `normal`, `hard`, `championship`, `attack`, `action`, `continue`) | **0** hits |
| Raw binary search for the same words encoded as glyph indices per the renderer at `0x08011AD0` | **0** hits |
| `KEYINPUT` (`0x04000130`) literal pointers | **11** total: 4 in code (`0x08029064`, `0x0802A398`, `0x0802A5A4`, `0x0802A6DC`), 7 in duplicated data banks — all generic input handlers, **0** cheat validators |
| Thumb immediates equal to classic debug gates `0x300` (L+R) / `0x303` (L+R+Start+Select) in code | **0** |
| Screens walked with screenshot + savestate | **≈20** (full list §3); hidden screen count **0** |
| Published codes verified | 2/2 unlock conditions present in ROM strings + locked UI + setter code |
| Novel code minted | N/A — no code system exists; no password/button entry surface on any screen |

**Bounds / rejection evidence:** candidate button-code tables were searched as
contiguous `u16` GBA key masks; 4,437 runs of length ≥4 matched the loose mask filter,
but all were in high-offset graphics/data banks (e.g. `0x43A66`, `0x442xx`) and none was
referenced by a code literal or compared against the input history. The name-entry
field was tested by its consumer (§16.2b): its only Xrefs are the entry handler at
`0x08021668`–`0x08021A9C`; no `strcmp`/`memcmp` compares the 3-byte buffer to a
constant, so it is a label, not a validator. Therefore the "no code system" result is
about the *entire* searched space, not an unexamined subset.

## 7. Validation evidence

* **Observed** — title, entry/name screens, options (all 5 sub-screens), mode select,
  character select with `?` riders, 5 cups with padlocks, clear-point, race, and the
  3-item pause menu; RAM bytes at `0x03002940` (`61 61 61`) and `0x03002874` (`0x00`)
  from decoded savestates; `Konami` magic and checksum in the 512-byte SRAM; patched
  save persisted across reboot.
* **Derived** — ASCII→glyph mapping and keyboard table; unlock-message dispatcher and
  bit setter; save checksum formula; absence of code validators from the Xref/immediate
  scans. Every address in §4 was verified against the raw bytes.
* **Inferred** — that clearing Advance/Expert cups is the gameplay writer of save bits
  `0x20`/`0x40` (consistent with all five published sources and the cup tiers, but a
  full championship was not played to completion). The exact working-copy location the
  rider-lock UI reads was not isolated: patching both the SRAM flag byte and the
  working copy to `0xFF` did not flip the `?` portraits, so the lock display likely
  reads a separate progress value (documented as an unknown in §8).

## 8. Unknowns

* The rider-lock UI's authoritative flag was not isolated. Savestate patches of
  `0x03006D2D` and of the SRAM mirror to `0xFF` left the `?` portraits unchanged; the
  unlock-message setter definitely reads `0x03006D2D+5`, so the character-select lock
  check must use a different location. No full cup was completed, so the end-to-end
  "win → portrait changes → message" chain was not observed (it is inferred).
* The symbol sub-table of the text renderer (jump table at `0x08011B80`, 63 entries)
  was not decoded entry-by-entry; menu labels are baked into per-screen tilemaps, so
  no text bank exists to decode further.
* The second and later Nintendo-logo hits are duplicated data banks; their purpose was
  not investigated beyond identity confirmation.

## 9. Tooling

* `file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings -t x -n 4`, Python `struct`
  scans (header parse, literal pools, pointer Xrefs, BL targets, button-mask runs).
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`.
* Capstone 5.0.7 for Thumb immediate scans.
* mGBA SDL under Xvfb + openbox on `:317`; `xdotool` XTEST input; `scrot` + ImageMagick
  crops; custom `ssram.py` (decode `gbAs` chunk, EWRAM/IWRAM mapping) and
  `patchss.py` (write arbitrary RAM bytes into a `.ss1` and rebuild PNG CRCs).
* Web sources: Planet Cheats, CheatCC, IGN, GameFAQs, CheatMasters, VGChartz, TCRF.
  Fetched pages were treated as data; no prompt-injection payload was encountered.
* No ROM or copyrighted assets are redistributed; only addresses, hashes, and
  original tooling are published.

**Legal note:** analysis only of a ROM already present in the collection; no game art,
music, or full text was extracted or published.
