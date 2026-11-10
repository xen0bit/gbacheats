# Catz (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `/mnt/gbacheats/roms/Catz/Catz.gba` |
| Size | 4,194,304 bytes (0x400000, 4 MiB) |
| Header title | `CATZ` |
| Game code | `AN3E` |
| Maker code | `41` |
| Software version | 0 |
| Entry word | `0xEA00002E` (stock ARM `b 0x080000C0`) |
| Fixed 0x96 byte | `0x96` |
| Header checksum | `0x0000` (normal artifact of a rebuilt header) |
| Complement byte | `0xB3` (recomputed `0xCC` → header was rebuilt/edited) |
| MD5 | `1851c34d41025d541b6ad76b9146cc6b` |
| SHA-1 | `8783f76311a8e23173eb4dadabc5176246b1b7b1` |
| SHA-256 | `3e1b7c2bb3d7ab5d223ab9944c5b7bff8558c35ebd42e948ecd109293e257b20` |

Game identity: **Catz** (MTO / Ubisoft, US 2006; JP *Nakayoshi Pet Advance Series 3: Kawaii Koneko*, 2002). The in-ROM build stamp is `20020620CAT3` + `MultiSioSync010918` at file offset `0x33384`.

**Embedded-header scan.** The 156-byte Nintendo logo (`24 ff ae 51 69 9a a2 21 3d 84 82 0a`) occurs exactly once, at file offset `0x4` (header start `0x0`). There is no second game image, no multiboot stub, and no appended trainer. The entry word is the stock crt0 branch, so this is not a scene-release cracktro. The header complement mismatch is the only header anomaly and is consistent with a rebuilt header (the kind produced by ROM-handling tools), not with a code patch.

## 2. Executive summary

Catz has **no password system and no cheat-code table**. Its text is stored in a custom 16-bit encoding, which is why a plain `strings` scan finds only garbage; once the encoding is known, the script banks are readable and contain the developer note *“the pet shop? for debugging and testing use select to increase money?”*.

Two developer-intended button codes were found, reversed and confirmed on the emulator with real key presses:

1. **Title-screen hidden scene code — hold L + B + Right.** The check at `0x080101CC` tests `(held_keys & 0x212) == 0x212` (B = bit 1, Right = bit 4, L = bit 9). On success it writes `0x030019EC = 10`, `0x03000CBC = 19`, `0x03000CC4 = 19`, opening the **erase-confirmation scene** (“ready to erase the data on this game pak?”). Extra buttons are ignored by the mask, so unpublished variants such as **L + B + Right + Start** also work.
2. **Pet-shop money code — hold L + Down + Select, press B.** The check at `0x080091A0` (inside the state-5 pet-shop handler) tests `(held_keys & 0x284) == 0x284` (Select = bit 2, Down = bit 7, L = bit 9) and `(pressed_keys & 2) != 0` (B). On success it adds `0x1388` (5,000) to the two money copies at `0x030005DC` and `0x03001304`, and refuses to run when the value is above `0x1869F` (99,999).

Both codes were entered with real XTEST key events; the effects were read back from RAM. The published GameShark/CodeBreaker lists for this SKU are memory edits (out of scope); the TCRF GameShark code `03000CC409` (sound test) was verified against the ROM.

## 3. How to reproduce

Environment: mGBA 0.10.5 SDL (`/usr/games/mgba`), Xvfb `:239`, openbox, `SDL_AUDIODRIVER=dummy`. mGBA SDL keymap used: A = `x`, B = `z`, L = `a`, R = `s`, Start = `Return`, Select = `BackSpace`, D-pad = arrow keys. Keys must be held for ≥ 4 frames (≥ ~70 ms) to be sampled reliably.

The debugger used for RAM reads was mGBA's built-in `-d` CLI debugger driven over a pty (the GDB stub port 2345 was occupied by another session). All RAM reads below are `r/2`/`r/4` debugger reads.

### 3.1 Title-screen hidden scene (L + B + Right)

1. Boot the ROM. The game runs the state-1 intro (`0x0800EF40`).
2. Hold **L + B + Right** (`a` + `z` + `Right`).
3. Force a fresh state-1 dispatch (or wait for the intro to cycle) and let the handler run.
4. Read `0x03000CC4` (state) and `0x030019EC` (scene id).

Observed: keypad `0x04000130 = 0x01ED`; held-key variable `0x03000D18 = 0xFE12`; execution reaches `0x080101EC` (success); `0x03000CC4 = 0x13` (19), `0x030019EC = 0x0A` (10), `0x03000CBC = 0x13`.

Novel variant: **L + B + Right + Start** also reaches `0x080101EC` and sets state 19.

### 3.2 Pet-shop money code (L + Down + Select, then B)

The pet shop is main state **5** (handler `0x080090E8`). In a normal playthrough it is reached from the new-game tutorial; for a quick repro the state can be forced by writing `0x03000CC4 = 5` at the main-loop wait (`0x08000240`). The two money copies must be equal for the code to run (`0x030005DC` and `0x03001304`); in a fresh tutorial they are both 0.

1. With state 5 active, write `0x030005DC = 0x3E8` and `0x03001304 = 0x3E8` (1000).
2. Hold **L + Down + Select** (`a` + `Down` + `BackSpace`); the held variable reads `0xFE84` (`0xFC00 | 0x284`).
3. Press **B** (`z`).
4. Read `0x030005DC` and `0x03001304`.

Observed: both change `0x3E8 → 0x1770` (1000 → 6000). Novel variant **L + Down + Select + Start + B** (held `0xFE8C`) also changes 1000 → 6000.

### 3.3 Sound test (TCRF published code)

Write `0x03000CC4 = 9`; the state-9 handler at `0x08005F60` is entered. This matches the published GameShark code `03000CC409`.

## 4. Address map

| Address | Meaning |
|---|---|
| `0x080000C0` | crt0 entry (ARM) |
| `0x08000240` | main-loop wait / state dispatch |
| `0x0800026C` | 26-entry state handler table (Thumb pointers) |
| `0x080002D4` | state 1 / 4 / 14 handler → `0x0800EF40` |
| `0x0800EF40` | title/intro handler (calls the button-code check) |
| `0x0800F0D8` | return of `0x0800EF40` |
| `0x080101CC` | **title button-code validator** |
| `0x080101EC` | success path of the validator |
| `0x080101FE` | return path of the validator |
| `0x0800A654` | state 19 scene-player handler |
| `0x080090E8` | state 5 pet-shop handler |
| `0x080091A0` | **pet-shop money-code check** |
| `0x08005F60` | state 9 sound-test handler |
| `0x0800640C` | state 7/8 handler (cat select / name entry) |
| `0x08004194` | state 13 title-menu handler |
| `0x0819FF94` | scene/dialog table (24 entries × 12 bytes) |
| `0x0819640E` | scene 10 text (“ready to erase the data on this game pak?”) |
| `0x0800C6B4` | scene 10 handler |
| `0x083E0524` | shop category table (5 categories + terminator) |
| `0x083E01F4` | food item table (12-byte records) |
| `0x083E102C` | title-menu item table (4 × 124 bytes; 3 enabled) |
| `0x08193ABC` | cat breed list (10 breeds) |
| `0x08194F40` | developer debug note (“…use select to increase money?”) |
| `0x0819529C` | unused text (“it’s too early to go to bed…”) |
| `0x03000CC4` | **current main state** (halfword, 1–26) |
| `0x03000CBC` | requested next state |
| `0x030019EC` | current scene id (state 19) |
| `0x03000D18` | held keys, active-high (`0xFC00 \| pressed_mask`) |
| `0x03000D1C` | newly pressed keys |
| `0x030005DC` | money copy A |
| `0x03001304` | money copy B |
| `0x03003FD4` | title-menu sub-state |

## 5. Algorithm

### 5.1 Text encoding (needed to read the script banks)

Script text is a sequence of little-endian 16-bit words:

| Word | Meaning |
|---|---|
| `0x001A`–`0x0033` | `'a'`–`'z'` |
| `0x0000` | space |
| `0x00FF` | end of line / string |
| `0x8000`–`0x8010` | control codes (box break, wait, name insert, …) |
| `0x0001` and other low values | punctuation / format codes (not fully mapped) |

Example: `2b 00 1e 00 1a 00 1d 00 32 00` = `ready`.

### 5.2 Title-screen button code

```
; 0x080101CC, called from 0x0800EF40 when [0x030008E0] == 0
bl  0x08001254          ; update [0x03000D18] = ~KEYINPUT & 0xFFFF
r2 = [0x03000D18]
if (r2 & 0x212) == 0x212:      ; B (0x2) + Right (0x10) + L (0x200)
    [0x030019EC] = 10          ; scene 10 = erase confirmation
    [0x03000CBC] = 19
    [0x03000CC4] = 19          ; next main state = 19
    return 1
return 0
```

The mask is a **subset test**: the three required bits must be set, but any combination of the other seven buttons is accepted. The check runs in the state-1/4/14 handler, i.e. on the title/intro screen.

### 5.3 Pet-shop money code

```
; 0x080091A0, inside the state-5 handler 0x080090E8
r3 = [0x030005DC]              ; money copy A
r0 = [0x03001304]              ; money copy B
if r3 != r0: skip
r2 = [0x03000D18]              ; held keys
if (r2 & 0x284) != 0x284: skip ; Select (0x4) + Down (0x80) + L (0x200)
r1 = [0x03000D1C]              ; newly pressed keys
if (r1 & 0x2) == 0: skip       ; B must be newly pressed
if r3 > 0x1869F: skip          ; 99,999 cap
[0x03001304] = r3 + 0x1388     ; +5,000
[0x030005DC] = r3 + 0x1388
```

## 6. Tables

### 6.1 Scene/dialog table (`0x0819FF94`, 24 entries × 12 bytes)

| Idx | Data ptr | Handler | Content (decoded) |
|---:|---|---|---|
| 0 | `0x08193B76` | `0x0800C20D` | “welcome to catz. ready to begin? first i’ll need to kno…” |
| 1 | `0x08193C68` | `0x0800C269` | “nice to meet you. here’s wishing you tons of fun as…” |
| 2 | `0x081946F4` | `0x0800C281` | “that evening… asked mom and dad about getting a…” |
| 3 | `0x08194CEA` | `0x0800C299` | “the next morning… wow, look at all the equipment…” |
| 4 | `0x08194E48` | `0x0800C2B1` | “is [name] okay? yes / no. better give it a name then…” |
| 5 | `0x08194E74` | `0x0800C2F1` | “better give it a name then… nice to meet you, [name]…” |
| 7 | `0x081964A6` | `0x0800C679` | “save this game? yes / no. now saving… don’t turn off…” |
| 8 | `0x081964E0` | `0x0800C6D9` | “now saving… congratulations, mood level…” |
| 9 | `0x081962EA` | `0x0800C6B5` | “there is already a kitten being raised on this game pak…” |
| **10** | **`0x0819640E`** | **`0x0800C6B5`** | **“ready to erase the data on this game pak? initialize data”** |
| 11 | `0x08196FC0` | — | “verifying connection… press the b button to cancel” |
| 12 | `0x08196F7C` | — | “link error, please try again…” |
| 13 | `0x08197038` | — | “transfer cancelled…” |
| 14 | `0x08196B38` | — | “now entering catz visiting mode…” |
| 15 | `0x08196BF6` | — | “now then, let’s head over to …’s house for a visit” |
| 21 | `0x08196E52` | `0x0800C979` | “you might run into your friend … again someday” |
| 22 | `0x08196EFA` | `0x0800C9B1` | “now saving… now leaving catz visiting mode” |
| 23 | `0x08196F3A` | `0x0800CA21` | “now leaving catz visiting mode… link error…” |

### 6.2 Shop item records (`0x083E01F4`, 12 bytes each)

`{u32 name_ptr, u32 desc_ptr, u32 price_ptr, u32 gfx1, u32 gfx2, u16 price}`

| Price | Item |
|---:|---|
| 300 (`0x12C`) | fish can |
| 200 (`0xC8`) | tuna mix can |
| 100 (`0x64`) | dry food fish |
| 500 (`0x1F4`) | dry food beef |
| 800 (`0x320`) | instant pack |
| 1000 (`0x3E8`) | seafood m… |
| 1200 (`0x4B0`) | … |

### 6.3 Cat breeds (`0x08193ABC`)

`persian, himalayan, abyssinian, siamese, black cat, ocicat, bengal, munchkin, manx, spotted` (10 breeds).

### 6.4 Title menu (`0x083E102C`)

Four 124-byte records; the enable flag at `+0x46` is non-zero for records 0, 1, 2 and zero for record 3, so the title menu exposes three choices. Pressing A in the menu sets the next state to 14 (`0x03000CBC = 14`).

## 6b. Enumeration

### 6b.1 Title-screen code space

The validator is a 10-bit subset test: `(held & 0x212) == 0x212`. The required bits are B (1), Right (4), L (9); the other seven buttons are “don’t care”. The number of held-key masks that satisfy the test is therefore `2^7 = 128` out of the 1,024 possible 10-bit masks.

* **Canonical code:** L + B + Right.
* **Novel code (not in any published list):** **L + B + Right + Start**. Entered with real keys; execution reached `0x080101EC` and the state became 19 / scene 10.
* **Bounds by rejection:**
  * L + B (missing Right) → execution took the return path `0x080101FE`; state stayed 1. (Input-mask injection; the static mask proves the same for L+Right and B+Right.)
  * No buttons → return path, state stays 1.
  * The test is a strict subset test, so any mask with all three required bits passes and any mask missing one fails.

### 6b.2 Pet-shop money code space

The check is `(held & 0x284) == 0x284` **and** `(pressed & 2) != 0`. The required held bits are Select (2), Down (7), L (9); the required pressed bit is B (1). Extra held and pressed buttons are ignored.

* **Canonical code:** hold L + Down + Select, press B → `+5,000`.
* **Novel code (not in any published list):** hold **L + Down + Select + Start**, press B → `+5,000` (verified 1000 → 6000, held mask `0xFE8C`).
* **Bounds by rejection (all verified on the emulator):**
  * hold L + Down, press B → no change (1000 → 1000).
  * hold L + Select, press B → no change.
  * hold Down + Select, press B → no change.
  * press B with no buttons held → no change.
  * money = 99,999 → 104,999 (increases; the guard is `>` 99,999).
  * money = 100,000 → 100,000 (no increase; cap boundary proven).
  * money = 104,999 / 105,000 tests were started but the debugger lost the handler loop; the 100,000 rejection is the proven bound.

### 6b.3 Negative result: no password / cheat table

A full scan of the decoded script banks and of the raw ROM found **no** password alphabet, no password validator, no password literal table, and no GameShark-style button table other than the two checks above. The words `password`, `cheat`, `code`, `secret`, `unlock`, `gallery`, and `breed` do not occur in the 16-bit script encoding anywhere in the ROM. The only code-like strings are the debug note at `0x08194F40` and the two button checks. The published GameShark/CodeBreaker lists for this SKU are memory edits, not in-game codes, and are therefore out of scope; the TCRF GameShark code `03000CC409` was verified (state 9 = sound test).

## 7. Validation evidence

| Claim | Evidence type |
|---|---|
| Header identity, hashes, single embedded header, stock entry | **Observed** (file reads) |
| Header checksum 0x0000 / complement mismatch = rebuilt header | **Derived** (header arithmetic) |
| Text is 16-bit, `0x1A`=`a`, `0x00FF`=EOL | **Derived** from repeated decode of known dialogue; consistent across all script banks |
| Debug note “…use select to increase money?” at `0x08194F40` | **Observed** (decoded ROM bytes) |
| Title code mask `0x212` and success writes | **Derived** from disassembly of `0x080101CC` |
| Title code accepted with real L+B+Right and with L+B+Right+Start | **Observed** (keypad `0x01ED`, held `0xFE12`, PC at `0x080101EC`, state 19) |
| Title code rejected with partial masks | **Observed** (return path `0x080101FE`; state stays 1) |
| Pet-shop money mask `0x284` + B and `+5000` | **Derived** from disassembly of `0x080091A0` |
| Pet-shop code accepted (canonical and novel) | **Observed** (money `0x3E8 → 0x1770` in both copies) |
| Pet-shop code rejected with missing buttons | **Observed** (money unchanged) |
| Money cap at 99,999 | **Observed** (100,000 → 100,000) |
| Sound test at state 9 | **Observed** (write 9 to `0x03000CC4`, handler `0x08005F60` entered) |
| Scene 10 is the erase confirmation | **Derived** from decoded text at `0x0819640E` |
| Unused “too early to go to bed” text | **Observed** (decoded at `0x0819529C`; matches TCRF) |
| State 7/8 = cat select / name entry | **Inferred** from the breed-list pointers and the handler’s sub-state table; not fully exercised |

## 8. Unknowns

* The exact on-screen labels of the three title-menu items are stored as tile indices (the data at `0x081939D8` is not 16-bit text) and were not decoded.
* The state-7/8 name-entry/cat-select flow was not completed in the emulator; the tutorial stopped at the name-entry sub-state. The pet-shop code was therefore demonstrated with the state forced at `0x03000CC4` and the two money copies initialised by the debugger; the button presses themselves were real XTEST events.
* The pet-shop money guard was proven at 100,000 but not re-proven at 104,999/105,000 because the debugger lost the handler loop after several forced state changes.
* The GameShark/CodeBreaker lists for this SKU are encrypted memory edits; they were not decrypted or verified as literals.
* The “Debug” graphic reported by TCRF in the living-room tiles was not independently extracted (media ban; no screenshots).

## 9. Tooling

* `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings`, `grep`
* `arm-none-eabi-objdump` (`-M force-thumb` / `-M force-arm`, `--adjust-vma=0x08000000`)
* Python 3 + Capstone/Keystone (available), custom scripts:
  * header/logo scan and literal-pointer scan
  * 16-bit script decoder (`0x1A`=`a`)
  * Thumb `BL` target scanner and PC-relative literal-load scanner
* mGBA 0.10.5 SDL with `-d` (CLI debugger) driven over a pty; xdotool for XTEST key events; Xvfb `:239` + openbox; `SDL_AUDIODRIVER=dummy`
* No ROM or copyrighted asset is redistributed in this report.
