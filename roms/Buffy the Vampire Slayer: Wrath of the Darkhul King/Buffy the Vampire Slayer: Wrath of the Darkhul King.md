# Buffy the Vampire Slayer: Wrath of the Darkhul King (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Buffy the Vampire Slayer: Wrath of the Darkhul King.gba` |
| Size | 4,194,304 bytes (0x400000, 32 Mbit) |
| Header title | `BUFFY` (0xA0, NUL-padded) |
| Game code | `AVYE` (0xAC) |
| Maker code | `78` (0xB0) |
| Version | 0x00 (0xBC) |
| Complement check | 0xBD = `0x31` (matches `-(0x19 + sum(0xA0..0xBC)) & 0xFF`) |
| Header checksum | 0xBE..0xBF = `0x0000` (zeroed; normal artifact of a rebuilt/repacked header) |
| Entry word | `0xEA00002E` → ARM branch to `0x080000C0` (stock GBA crt0) |
| Nintendo logo | one hit, file offset `0x4` (single image, not a multi-game pack) |
| MD5 | `c2b19a62899cff0f0b61252c4e6b3e0f` |
| SHA-1 | `bcca25eba386a75beb300289f3e1344995966323` |
| SHA-256 | `55c73a1ea5e8339cfe1ece56f5142cbaaf181d947cbd6855409eb0506daca191` |
| Save type | mGBA created a 512-byte `.sav` → EEPROM (4 Kbit). The game is not password-saved. |

**This is a scene release, not a clean retail image.** Cold boot runs a **Mode 7
cracktro** before the legal screen: a yellow Mode 7 demo with a scrolling
message (“GAME SUPPLIED BY: HENAL SLICK / RELEASED ON: JUNE 27TH 2003”) and
scene greets (AGGRESSION, THANTHROX, DCS, ILLUSION, SNEAKERS, SHAT, MENACE,
UENOM, EURASIA, LIGHTFORCE, RISING SUN). It runs for about a minute, has no
menu, no code entry, and no observed skip; it is **not a trainer or a cheat menu**; it is not part
of the in-game cheat surface. The entry word and the crt0 at `0x080000C0` are
stock, so the cracktro is hooked elsewhere in the boot path (its hook was not
reverse-engineered because it does not affect the cheat system). The zero
header checksum is consistent with the release having been rebuilt; the
complement byte is still correct.

All findings below are for **this exact image**.

## 2. Executive summary

The GBA SKU has **exactly four developer button codes**, entered while
“Press Start” flashes on the title screen. No password screen exists, and no
level-select, gallery, sound-test, debug, or unlockable menu screen was
observed on any walked screen or found in the static search. The codes are not
compared as strings: they are matched against a **10-deep, newest-first history
of single button presses** by a validator at `0x08004804`, using a
**four-record table at `0x0828371C`** (10 × u32 per record, zero-terminated).
A match sets a bit in the flag word at `0x03004B30`.

| # | Code (press order) | Flag bit | Effect |
|---|---|---|---|
| 0 | Up, Down, Up, Down, B, A | 0x1 | 9 of every item/ammo |
| 1 | B, B, A, A, L, R, Down, Up | 0x2 | Invincibility |
| 2 | L, L, L, R, R, R, Right, Right | 0x4 | Infinite lives |
| 3 | Up, Right, Up, Left, Down, Right, Down, Left | 0x8 | Enemy health meters |

All four published codes were verified **literally in the ROM table** and by
watching the flag word in the emulator. The set is closed: record 4 at
`0x082837BC` is all zeros and the validator returns `-1` on it, so records 5–9
are unreachable. Over the 8-button alphabet there are 1,073,741,824 possible
10-press strings, of which exactly **4,288** end in an accepted pattern and
**21,056** trigger a code at some point. Only **four distinct effects** exist.

The acceptance work in §6b uses a prefixed 11-press spelling of the item code
that appears in no published list; it was entered on the real title screen and
produced the 9-item inventory. A combined four-code burst is also documented,
but only as a timing-bound experiment because the title resets its flag word
within about 5 seconds of entry.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 (`/usr/games/mgba`), SDL frontend, 3× scale.
* Display: `Xvfb :217 -screen 0 1024x768x24`, `DISPLAY=:217`, `SDL_AUDIODRIVER=dummy`.
* mGBA default keys: **A = `x`**, **B = `z`**, **L = `a`**, **R = `s`**,
  **Start = `Return`**, **Select = `BackSpace`**, D-pad = arrow keys.
* Hold each key ~120–180 ms and leave ~350–400 ms between presses. The input
  reader at `0x0800476C` consumes **newly pressed** bits only (edge-triggered),
  so holding a button does not repeat it, and two buttons in one frame collapse
  to one symbol (priority Up > Down > Left > Right > A > B > L > R).

Exact path for a code:

1. Cold boot. Wait out the Mode 7 cracktro (~60 s) → legal screen → Natsume →
   THQ → Buffy title with flashing **Press Start**.
2. Enter the button sequence while “Press Start” is flashing. Each accepted
   code plays SFX #2 (validator returns 0–3; call site `0x0802D8FC` does
   `bl 0x0800A44` with `r0 = 2`).
3. Press **Start** → Main Menu → **New Game** → **Normal** (default cursor) →
   skip the book intro and the Buffy dialogue with A.
4. In gameplay, **Start** opens the pause inventory. Normal difficulty starts
   with three item slots at count 4; the item code sets all 15 slots to 9.

**Timing is part of the format.** The title screen's input/flag reset
(`0x08004748`) can fire within about 5 seconds of entry: after a code, the flag
word read `0x1` at ~4.5 s and `0x0` at ~5.2 s (savestate sampling every
0.65 s). Enter the code and press **Start** inside that window, or the title
will wipe the flag and the 10-entry history before the game latches it.

Reproduction of the memory evidence does not need GDB: pressing **Shift+F1**…
**F8** writes `buffy.ssN`, whose `gbAs` PNG chunk is zlib-compressed state.
In this ROM the IWRAM block begins at uncompressed state offset `0x19000`, so:

* flags `0x03004B30` → state offset `0x1DB30`
* press history `0x03004B50` → state offset `0x1DB50`

## 4. Address map

File offset = ROM address − `0x08000000`.

| ROM address | File off | Meaning |
|---|---|---|
| `0x0800476C` | `0x476C` | Key decoder: reads newly-pressed bits `[0x03004B44]`, picks one button by priority, shifts it into the history. |
| `0x080046E6` | `0x46E6` | Key-state update: previous keys at `0x03004B42`, pressed = cur & ~prev at `0x03004B44`. |
| `0x08004804` | `0x4804` | **Cheat validator.** Returns 0–3 on match, −1 otherwise. |
| `0x0802D8FC` | `0x2D8FC` | Only BL call site: title-screen state machine. Plays SFX if return ≥ 0. |
| `0x08004748` | `0x4748` | Input/flag reset: clears `0x03004B30` and the 10-entry history. Called from boot (`0x0800035A`) and title transitions (`0x0802D84C`, `0x0802D9B2`). |
| `0x03004B30` | RAM | **Cheat flag word** (bit 0 items, bit 1 invincible, bit 2 lives, bit 3 health meters). |
| `0x03004B40` | RAM | Key-state struct: `+0` last D-pad state, `+2` previous raw keys, `+4` newly pressed, `+6` latch, `+8` repeat counter. |
| `0x03004B50` | RAM | 10 × u32 press history, **index 0 = newest** (`0x03004B74` = oldest). |
| `0x0828371C` | `0x28371C` | **Code table**, 10 records × 10 u32 (stride `0x28`). |
| `0x082837BC` | `0x2837BC` | Record 4 = all zeros → validator returns −1; table terminator. |
| `0x0800F878` | `0x0F878` | Bit 1 reader: forces damage value `r6 = 0` when invincibility is set. |
| `0x08025BBC` | `0x25BBC` | Bit 0 consumer: writes 9 to 15 inventory/ammo slots; without the bit writes difficulty value (5/4/3) to slots 0, 5, 9. |
| `0x0802E6BA` | `0x2E6BA` | Level-start check of bit 0, then `bl 0x08025BBC`. |
| `0x080072DA` | `0x072DA` | Bit 2 reader: skips the decrement of the life/continue counter at `0x03001268`. |
| `0x080179E0` | `0x179E0` | Bit 3 reader: 8-slot HUD drawing loop gated by bit 3 (published label “enemy health meters”; exact visual inferred). |
| `0x080000C0` | `0xC0` | Stock GBA crt0 (entry word `0xEA00002E`). |

## 5. Algorithm

### 5.1 Input history

```
every frame:
  keys      = ~KEYINPUT & 0x3FF
  pressed   = keys & ~previous_keys          ; edge-triggered
  previous  = keys
  if pressed != 0:
      b = highest-priority set bit of pressed ; Up,Down,Left,Right,A,B,L,R
      for i = 9 downto 1: hist[i] = hist[i-1]
      hist[0] = b                            ; newest first
```

Start (`0x8`) and Select (`0x4`) are not in the priority list and therefore can
never enter the history.

### 5.2 Validator (`0x08004804`)

Pseudocode exactly as the Thumb code does it:

```
rec = 0x0828371C                 ; ldr r0,[pc,#52] -> literal at 0x08004848
ip  = 0
for i = 0 .. 9:                  ; r7
    first = u32[rec + ip]
    if first == 0: return -1     ; 0x0800481A
    j = 0
    while True:
        expect = u32[rec + ip + 4*j]
        if expect == 0:          ; 0x08004826 -> success path
            clear hist[0..9]
            flags |= (1 << i)    ; [0x03004B30]
            return i
        if expect != hist[j]: break
        j += 1
    ip += 0x28                   ; 10 u32 per record
return -1                        ; 0x0800486E, r0 = -1
```

Consequences:

* Matching is **suffix matching over the last ≤10 presses**; earlier junk
  presses are ignored.
* Records are stored **newest-first**. A naive forward literal search for a
  published code fails because the ROM contains it reversed, e.g. record 0
  holds `A,B,Down,Up,Down,Up`.
* A successful code clears the 10-entry history, so it fires once per entry
  rather than every frame.
* The table was located by scanning for a run of key-mask values and confirmed
  by the literal word at `0x08004848` = `0x0828371C`.

## 6. Tables

### 6.1 Code table at `0x0828371C` (as stored, newest-first; values in hex)

| Rec | Address | u32 values | Press order (reverse of storage) | Flag |
|---|---|---|---|---|
| 0 | `0x0828371C` | `0x01, 0x02, 0x80, 0x40, 0x80, 0x40, 0x00, 0x00, 0x00, 0x00` | Up, Down, Up, Down, B, A (len 6) | 0x1 |
| 1 | `0x08283744` | `0x40, 0x80, 0x100, 0x200, 0x01, 0x01, 0x02, 0x02, 0x00, 0x00` | B, B, A, A, L, R, Down, Up (len 8) | 0x2 |
| 2 | `0x0828376C` | `0x10, 0x10, 0x100, 0x100, 0x100, 0x200, 0x200, 0x200, 0x00, 0x00` | L, L, L, R, R, R, Right, Right (len 8) | 0x4 |
| 3 | `0x08283794` | `0x20, 0x80, 0x10, 0x80, 0x20, 0x40, 0x10, 0x40, 0x00, 0x00` | Up, Right, Up, Left, Down, Right, Down, Left (len 8) | 0x8 |
| 4 | `0x082837BC` | all zero | **terminator; validator returns −1** | — |

Button mask values (unit = one bit): A=`0x001`, B=`0x002`,
Right=`0x010`, Left=`0x020`, Up=`0x040`, Down=`0x080`, R=`0x100`, L=`0x200`.

### 6.2 Flag word `0x03004B30`

| Bit | Meaning | Reader | Behaviour |
|---|---|---|---|
| 0 | 9 of every item | `0x08025BBC` | level start writes 9 into 15 slots; without it, difficulty value 5/4/3 goes to slots 0,5,9 |
| 1 | Invincibility | `0x0800F878` | damage value forced to 0 |
| 2 | Infinite lives | `0x080072DA` | decrement of the life/continue counter at `0x03001268` skipped |
| 3 | Enemy health meters | `0x080179E0` | 8-slot HUD drawing loop gated by bit 3 |

Observed live gameplay state with all four codes entered: **flags = `0xE`**
(bit 0 consumed by the item grant, bits 1–3 still set). This was read from the
uncompressed IWRAM image of savestate `buffy.ss9` (state offset `0x1DB30`).

### 6.3 Published list verification

Sources compared: GameFAQs cheat page (4 codes, page itself 403 but search
snippet lists the health-meter code), Tips & Tricks May 2004 full-text archive
(full four-code list), SuperCheats, IGN wiki snippet, NeoSeeker snippet.

| Published code | Source label | ROM result |
|---|---|---|
| Up, Down, Up, Down, B, A | nine of every item | present, rec 0, flag 0x1 |
| B, B, A, A, L, R, Down, Up | invincibility | present, rec 1, flag 0x2 |
| L, L, L, R, R, R, Right, Right | infinite lives | present, rec 2, flag 0x4 |
| Up, Right, Up, Left, Down, Right, Down, Left | enemy health meters | present, rec 3, flag 0x8 |

One Fandom snippet mislabels `L,L,L,R,R,R,Right,Right` as “Invincibility”;
the ROM mapping (bit 2 = life decrement skip) confirms the Tips & Tricks /
SuperCheats label “Infinite lives”. All four literals are present and correctly
ordered; no published code was rejected and no typo was found in this list.

## 6b. Enumeration

### Space definition

* **Alphabet**: 8 symbols actually recordable by `0x0800476C` — A, B, Right,
  Left, Up, Down, R, L. Start and Select are ignored.
* **History depth**: 10 presses (`0x03004B50..0x03004B74`), index 0 newest.
* **Record layout**: 10 u32 per record, zero-terminated; stride `0x28`.
* **Records present**: 4 reachable (lengths 6, 8, 8, 8), then an all-zero
  terminator. Records 5–9 exist in the image but are unreachable because the
  validator stops at record 4; record 5’s first word is `0x000800D1`, not a
  button mask.
* **Checksum**: none. Validity is exact table membership.
* **Representable space**: 8^10 = **1,073,741,824** 10-press strings.
  * 4,288 of them end in an accepted pattern.
  * 21,056 of them trigger a code at some point during the 10 presses (the
    validator is called every frame; the history clears on success).
  * 212 of the 19,173,960 strings of length ≤8 trigger.
* **Distinct accepted effects**: exactly **4**.

Closed-set proof: the C enumerator `enumerate.c` walks the actual four records
over the 8-symbol alphabet (lengths 1–8) and reproduces the counts above. The
Python model `validator.py` parses the table from this ROM, accepts all four
published codes, accepts the novel input below, and rejects the negative
tests. Both scripts are listed in §9.

### Novel input 1 — prefixed item code (not in any published list)

```
Up, Up, Up, Right, Left, Up, Down, Up, Down, B, A
```

The five junk presses are outside the last six and are ignored; the last six
are record 0. Entered at the flashing title screen, then savestate `buffy.ss5`
was written **before starting a game**:

* `buffy.ss5` flags = **0x1**
* History at `0x03004B50` is all zero, which is the validator’s own success
  clear.
* Starting a game from this input produced the item effect: pause inventory
  shows **9** on every slot (`prefix_inv_gba.png`).

This 11-press input appears in no published list checked (GameFAQs, Tips &
Tricks, SuperCheats, IGN/NeoSeeker snippets, Fandom); a TCRF search returned no
article for this title.

Because the reachable table is exactly four records and all four effects are
already published, **no accepted input can produce an unpublished effect** in
this image. The unpublished object that does exist is an accepted *spelling*:
the four codes have 8^(10−L) prefix aliases each, and the prefixed input above
is one of them. The closed-set proof (four records, zero terminator) is what
makes that statement exhaustive rather than a failure to find a fifth effect.

### Combined-bit experiment (timing-bound, not claimed as a deliverable)

Entering all four codes in one burst was tested. Because the title's input/flag
reset can fire within ~5 s, the result is timing-dependent:

* With the emulator **paused between codes** (debugger watchpoint reads), the
  cumulative flags reached `0xF` and the live game state later showed `0xE`
  (bit 0 consumed, bits 1–3 active), with the inventory at 9
  (`inv_comb_gba.png`).
* A real-time fast 30-press burst (~4.8 s) left **`0xE`**: codes 1–3 landed,
  the item bit was lost to the reset.
* A slower burst (~11 s) left **`0x0`**: a reset occurred after the final code.

This combined input is therefore recorded as a bounded experiment, not as a
reproducible novel code. The reproducible novel code is the prefixed item input
above; the individual continuous bits can still be combined by entering the
three 8-press codes inside one reset window.

### Bounds proven by rejection

| Test | Input | Result |
|---|---|---|
| Wrong final button | Up, Down, Up, Down, B, **B** | flags `0x0` in `buffy.ss6`; history contains the attempted 6 presses |
| Too short | Up, Down, Up, Down, B | flags `0x0` in `buffy.ss7` |
| No input (control) | — | flags `0x0` in `buffy.ss8` |
| Unreachable record | record 4 first word = 0 | `0x0800481A` returns −1; records 5–9 never compared |
| Non-mask record | record 5 first word `0x000800D1` | cannot be produced by the 8-button alphabet |
| More than 10 presses | any | history depth is 10; the oldest presses are discarded before comparison |
| Title reset window | enter a code, wait >5 s | flag word returns to `0x0` at ~5.2 s; the title's `0x08004748` reset bounds the entry window |

The accepted input language is therefore infinite in *spelling* (arbitrary
prefixes) but has exactly four effects. The rejected inputs above show the
validator is not “accept everything” and that the table terminator, not a
checksum, is what bounds the set.

### Visual evidence kept on disk

All files are in `/tmp/opencode/buffy/`:

| File | Shows |
|---|---|
| `shot1.png`, `shot2.png` | Mode 7 cracktro / “GAME SUPPLIED BY HENAL SLICK” |
| `t2.png`, `title2.png` | Title screen with flashing “Press Start” |
| `main_gba.png` | Main menu (New Game / Options / Load) |
| `options_s.png` | Options: SFX On, Music On, Credits |
| `credits_s.png` | Credits screen |
| `prefix1_s.png` | Difficulty select (Easy / Normal / Hard) |
| `inv_control_gba.png` | Normal-difficulty control inventory: three slots at 4 |
| `prefix_inv_gba.png` | Novel prefixed code: every inventory slot at 9 |
| `inv_comb_gba.png` | All four codes entered with debugger pauses: every slot at 9 |
| `enemy_zoom.png`, `hp11_s.png` | Tutorial NPC sampled with bit 3 set; no bar drawn |

## 7. Validation evidence

**Observed (emulator/savestate):**

* Four codes accepted on the real title screen; each sets its flag bit
  (watchpoint/state reads: `0x1`, `0x3`, `0x7`, `0xF` cumulative).
* Item code changes the pause inventory from three “4” counters
  (Normal difficulty default) to “9” in all 15 slots.
* Prefixed 11-press input sets flags `0x1` and produces the same 9-item
  inventory.
* Wrong-final-button and short inputs leave flags `0x0`.
* After a code, the title flag word read `0x1` at ~4.5 s and `0x0` at ~5.2 s:
  the title's periodic reset bounds the usable entry window.
* With the emulator paused between codes, cumulative flags reached `0xF`; the
  later live gameplay state was `0xE` (item bit consumed), inventory 9.
  A real-time fast four-code burst left `0xE`; a slow burst left `0x0`.
* Cold boot on this image shows the Mode 7 cracktro, then the stock legal →
  Natsume → THQ → title sequence.

**Derived (from disassembly):**

* Validator `0x08004804`, table `0x0828371C`, history `0x03004B50`, flags
  `0x03004B30`, title call site `0x0802D8FC` (plays SFX #2 when the return value
  is ≥ 0).
* Bit 1 forces damage to zero at `0x0800F878`; bit 2 skips the decrement of the
  life/continue counter at `0x080072DA`; bit 0 writes 9 into the 15 item slots
  at `0x08025BBC`; bit 3 gates the 8-slot HUD drawing loop at `0x080179E0`.
* Exact 8-symbol alphabet and priority-based one-symbol-per-frame recording.
* Closed table set: 4 reachable records and a zero terminator.

**Inferred / bounded negative:**

* The bit-3 health-meter visual was not seen above the tutorial NPC sampled in
  the first street scene (the bit was set, `0xE`, and the HUD reader was
  identified, but that character did not enter the enemy list before the
  snapshot). The effect label is retained from the published list and the HUD
  code path.
* No password/cheat/debug/gallery/level-select screen was found: all title,
  main, options, credits, load, difficulty and pause screens were walked, and
  keyword searches over the whole image found zero occurrences of
  `PASSWORD`, `CHEAT`, `DEBUG`, `SECRET`, `UNLOCK`, `LEVEL`, `STAGE`, `WARP`,
  `GALLERY`, `CODE`, `OPTIONS`, `CONTINUE` in ASCII upper, ASCII lower, the
  +0x20 shifted form, or UTF-16LE/BE. The only key-mask sequence table found by
  the mask-run scan is the four-record cheat table above.
* The game’s UI text is font-index encoded, so the absence of ASCII keywords is
  not by itself proof of absence; it is combined with the full menu walk and
  the single-table scan.

## 8. Unknowns

* The exact visual of bit 3 (enemy health meters) for an active enemy was not
  captured; the bit and its HUD reader are proven, the first sampled character
  was not drawn with a bar.
* Records 5–9 are dead data after the terminator; their original purpose (if
  any) is unknown and unreachable.
* The cracktro’s boot hook was not reversed (it does not affect the game’s
  cheat system).
* Any story-gated bonus screen that might exist after full completion was not
  reached; no such gate, table, or string was found in the static search.

## 9. Tooling

| File | Purpose |
|---|---|
| `/tmp/opencode/buffy/validator.py` | Parses the real ROM table, reimplements the validator, asserts the four published codes, the prefixed novel input, and the rejected cases. |
| `/tmp/opencode/buffy/enumerate.c` | Exhaustive 8-symbol enumeration to length 8; prints end-in-code and triggered-at-some-prefix counts. |
| `/tmp/opencode/buffy/ptydbg.py` | mGBA CLI-debugger driver over a pty, used to set watchpoints/breakpoints and read the flag word. |
| `arm-none-eabi-objdump -M force-thumb` | Raw Thumb disassembly of the validator and flag readers. |
| mGBA 0.10.5 + Xvfb :217 + xdotool + scrot | Gameplay, screenshots, savestates. |

Reproduce the offline model:

```
python3 /tmp/opencode/buffy/validator.py
gcc -O2 -o /tmp/opencode/buffy/enumerate /tmp/opencode/buffy/enumerate.c
/tmp/opencode/buffy/enumerate
```

Expected validator output: 4 reachable records; code0–3 → 0,1,2,3; short and
wrong-tail → −1; prefixed input → 0. Expected enumerator: 1 accepted length-6
string, 8 length-7, 67 length-8; 4,288 end-in-code at length 10.

## 10. Legal note

No ROM, graphics, music, or extracted text is redistributed here. Only
addresses, algorithms, hashes, and self-generated test inputs are documented.
