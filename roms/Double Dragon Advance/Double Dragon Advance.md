# Double Dragon Advance (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Double Dragon Advance.gba` |
| Size | 4,194,304 bytes (0x00400000, 4 MiB) |
| Header title | `DOUBLEDRAGON` |
| Game code | `BDDE` |
| Maker code | `EB` |
| Revision | 00 |
| Version byte | 0x00 |
| Entry word | `0xEA00002E` (stock `b 0x080000C0`) |
| Complement byte | 0x45 (matches stock header; header checksum field 0x0000 is a normal rebuild artifact) |
| MD5 | `890eb1f0318bf4c5fc8552140a531c9f` |
| SHA-1 | `1b31cb065096f76c392c5ad5de4d63c19ee880b2` |
| SHA-256 | `19daa232414fa0b03f468b99787a640740751b46c4df8ef8ed0de245c1f747c1` |
| Developer / publisher | Million / Atlus (©2003), as shown on title screen and in ROM string `0x361B0` |

**Embedded-header / patch scan:** the whole 4 MiB was scanned for the 156-byte Nintendo
logo (`24 ff ae 51 69 9a a2 21 ...`). Exactly one hit, at file offset `0x00000004`,
i.e. the single normal GBA header at offset 0. There is no appended trainer, cracktro,
multiboot stub or second game image. The entry word is the stock branch and the
first 4 KiB disassembles as normal ARM crt0, so the image is a clean retail ROM
(rebuilt header only). No patch/trainer applies.

## 2. Executive summary

This game has **three developer-intended button cheats**, all entered on the **OPTIONS
screen** while **SELECT is held**. They are *not* passwords, not GameShark codes, and
not save-data unlocks. The ROM contains a single fixed table of exactly three
button sequences; each completion sets one bit in IWRAM flag byte `0x03000010`:

| # | Buttons (hold SELECT) | Effect | Flag bit |
|---|---|---|---|
| 0 | R, L, R, L | Unlock **BGM mode** (sound test) | 0x01 |
| 1 | Up, Up, Down, Down, Left, Right, Left, Right | Unlock **EXPERT difficulty** (and 10 starting credits — see §8) | 0x02 |
| 2 | L, R, Down, L, R, Down, L, R, Right | Start the game with **10 credits** | 0x04 |

All three published codes were verified literally in the ROM and executed against
the ROM's own validator running inside mGBA (debugger oracle, guide §16.19), with
the resulting flag byte read from RAM. An **unpublished accepted input** was also
confirmed: interleaving A/B/Start presses between the four BGM presses still
unlocks BGM (the validator ignores non-directional keys) — this is not in any
published list. Bounds were proven by rejected reversed, wrong-final-key and
prefix-only inputs (flag byte stayed 0).

The game also has a "You have discovered a secret code…" hint-reveal system that
shows these three hints as you meet in-game conditions; its messages are at
`0x08036490`–`0x08036570` and it is driven by a discovery counter at `0x020016A0+0x7A`.

## 3. How to reproduce

**Emulator / display:** mGBA (`/usr/local/bin/mgba`) under `Xvfb :317`, 1024×768,
`SDL_AUDIODRIVER=dummy`, started with the CLI debugger `mgba -d -3 <rom>`.
Keymap (mGBA SDL defaults): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
Select=`BackSpace`, D-pad = arrow keys. Hold keys ≥100 ms.

**Static path (no UI needed):**
1. `grep -abo` / Python literal search for the key masks (see §6) locates the
   sequence table at `0x0836271C` and its pointer table at `0x0836274C`.
2. Pointer xref to the pointer table finds the validator at `0x08002E80`.
3. `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`
   over `0x08002E80`–`0x0800300A` gives the algorithm in §5.

**Dynamic oracle path (ground truth, used for all effect claims):**
1. Start `mgba -d -3 <rom>` on a pty (helper `mgba_debug.py` in the work dir).
2. While paused, set `watch/r 0x04000130`, issue `continue` → the core halts at the
   first keypad read with the game fully booted; `delete` the watchpoint.
3. For each button press write the game's internal key masks:
   `w/2 0x020325A6 <pressed>` (newly pressed) and `w/2 0x020325A4 <held|0x100>`
   (SELECT held), then set `w/r lr 0x08000459`, `w/r pc 0x08002E81`, `continue`.
   A software breakpoint at `0x08000458` catches the return.
4. Read the effect with `r/1 0x03000010`.

This calls the real validator in the real emulator; it is not a substitute model.
The standalone reimplementation `validator_model.py` reproduces every oracle
result (§9).

**Published codes tested:** BGM `R L R L`; Expert `U U D D L R L R`; 10 credits
`L R D L R D L R Right` — all confirmed. Sources: 3rd party cheat index cheat list, 3rd party cheat indexes.

## 4. Address map

| Address | Type | Meaning |
|---|---|---|
| `0x08000450`–`0x0800048C` | code | Input transform. Reads `0x04000130`, remaps key bits, writes held/pressed globals. |
| `0x08002E80`–`0x0800300A` | code | **Button-code validator** (called only from the OPTIONS screen at `0x080021E2`). |
| `0x080021C0`+ | code | OPTIONS screen update function (scene index 1 in dispatcher table). |
| `0x08002700`–`0x08002866` | code | "You have discovered a secret code" message display (switch on secret index). |
| `0x08002880`–`0x0800293A` | code | Secret-discovery progression check (counter at `0x020016A0+0x7A`). |
| `0x08000300`–`0x080033E` | code | Scene dispatcher: init table `0x08361E5C`, update table `0x08361E80`, scene index `0x0203259C`. |
| `0x0836271C`–`0x0836274A` | data | Three `0xFFFF`-terminated `u16` key-mask sequences. |
| `0x0836274C`–`0x08362758` | data | Pointer table: the three sequence pointers + NULL terminator. |
| `0x083626E4` / `0x083626F4` | data | Tile graphics of the EXPERT / 10-credit button hints (why `strings` found no ASCII for them). |
| `0x08036490`–`0x08036570` | data | Hint message fragments ("…secret code … holding SELECT: …"). |
| `0x0803623C`–`0x08036268` | data | OPTIONS menu labels: `OPTIONS`, `DIFFICULTY`, `PLAYERS`, `CREDITS`, `BGM `, `EXIT`. |
| `0x020325A4` | RAM (halfword) | Held keys, active-high, internal encoding (see §5). |
| `0x020325A6` | RAM (halfword) | Newly pressed keys, active-high. |
| `0x02032A04` | RAM (halfword) | Validator progress index (position in current sequence). |
| `0x02032A08` | RAM (halfword) | Validator code index (0..2; 4 = past end). |
| `0x03000010` | RAM (byte) | **Cheat flags**: bit0=BGM, bit1=EXPERT, bit2=10 credits. |
| `0x020016A0+0x7A` | RAM (halfword) | Secret-discovery counter (0..3), drives hint reveals. |

File offset = ROM address − `0x08000000` throughout (no multi-image offset).

## 5. Algorithm

### 5.1 Key encoding (derived from `0x08000450`)

KEYINPUT (`0x04000130`, active-low) is inverted and bit-remapped:

```
raw = ~KEYINPUT & 0x3FF
internal = (raw & 0x0F3) | ((raw & 0x00C) << 6) | ((raw & 0x300) >> 6)
```

giving active-high internal bits:

```
A=0x001  B=0x002  R=0x004  L=0x008  Right=0x010  Left=0x020
Up=0x040  Down=0x080  Select=0x100  Start=0x200
```

(Select/Start and the shoulder buttons are swapped relative to the raw KEYINPUT
bits — this is essential for matching the table literals.)

### 5.2 Validator pseudocode (from `0x08002E80`)

```
validate():                                  # one call per frame with input
    flags_byte = 0x03000010                  # 0x80009F0(16) -> 0x03000000+16
    pressed = [0x020325A6]; held = [0x020325A4]
    if pressed & SELECT:            progress=0; code_index=0; return   # SELECT just pressed
    if not (held & SELECT):         progress=0; code_index=0; return   # SELECT released
    if not (pressed & 0x0FC):       return                             # A/B/Start ignored

    if progress == 0:
        code_index = 0
        while table[code_index] != NULL and table[code_index][0] not in (0, pressed):
            code_index += 1                                            # pick code by first key
        if code_index >= 4: return
    seq = TABLE[code_index]
    if seq[progress] != pressed:    progress = 0; return               # mismatch clears progress
    progress += 1
    if seq[progress] == 0xFFFF:                                        # complete
        flags_byte |= (1 << code_index)                                # set unlock bit
        play_sound([0xAC, 0x96, 0xAE][code_index])
        if code_index == 0: draw_string("BGM ")                         # 0x08036260
        return
    # NOTE: progress is deliberately NOT cleared on completion; the next
    # relevant key press compares against the stale 0xFFFF terminator,
    # mismatches, and clears progress. The first press of the next code is
    # therefore swallowed unless an irrelevant key is pressed first.
```

The action dispatch has exactly three branches (`cmp code_index, #1`, `>1`, `==0`
at `0x8002F70`–`0x8002F7E`): indices 0/1/2 set bits 0x1/0x2/0x4 respectively.
There is no fourth branch and no hidden action.

## 6. Tables

**Sequence table, `0x0836271C` (u16 little-endian, `0xFFFF` terminator):**

| Index | Address | Masks (internal) | Buttons | Length | Action / flag bit |
|---|---|---|---|---|---|
| 0 | `0x0836271C` | `0004 0008 0004 0008 FFFF` | R, L, R, L | 4 | BGM mode, bit `0x01` |
| 1 | `0x08362726` | `0040 0040 0080 0080 0020 0010 0020 0010 FFFF` | U, U, D, D, L, R, L, R | 8 | EXPERT, bit `0x02` |
| 2 | `0x08362738` | `0008 0004 0080 0008 0004 0080 0008 0004 0010 FFFF` | L, R, D, L, R, D, L, R, Right | 9 | 10 credits, bit `0x04` |

**Pointer table, `0x0836274C`:**
`0x0836271C`, `0x08362726`, `0x08362738`, `0x00000000` (NULL = end).
Three entries, terminated — the closed set is proven by this table plus the
three-branch dispatch, not inferred from a published list.

**Flags byte `0x03000010`:** bit0 = BGM unlocked, bit1 = Expert unlocked,
bit2 = 10 credits unlocked. Each branch checks the bit before setting it, so
re-entering an already-unlocked code is a no-op.

**Hint graphics:** the BGM hint is plain text `R\L\R\L` at `0x08036518`; the
EXPERT and 10-credit hints are tile-index runs at `0x083626E4` and `0x083626F4`
(`0x5C0C`=↑, `0x5C0B`=↓, `0x5C0A`/`0x5C09`=←/→ style glyphs), which is why a
plain `strings` search only found the BGM hint.

## 6b. Enumeration

**Space definition.** The system is a lookup table, not a checksum algorithm:

* alphabet = 10 relevant button masks (`R,L,Right,Left,Up,Down` plus `A,B,Start`
  which the validator ignores); SELECT is a gate held outside the sequences;
* sequence length ∈ {4, 8, 9}, each terminated by `0xFFFF`;
* exactly **3** accepted sequences, selected by a pointer table with a NULL
  sentinel and dispatched through exactly 3 action branches;
* representable accepted values = **3** (no checksum bits, no reserved bits,
  no generator function exists in this build).

**Closed-set proof beyond the table:** a ROM-wide scan for other
`0xFFFF`-terminated runs of valid `u16` key masks (≥3 masks, values ≤ `0x3FF`)
found ~242 raw candidates, all in compressed graphics/audio regions
(`0x082Bxxxx`–`0x0831xxxx`), none a code table. The only real table is
`0x0836271C`. The dispatch at `0x8002F70` has no branch for index ≥ 3.

**Novel unpublished input, accepted in-game.** The published lists all specify
pressing only the four sequence buttons while SELECT is held. The validator,
however, ignores `A/B/Start` (`pressed & 0x0FC == 0` → early return without
resetting progress). Feeding the BGM sequence with A interleaved —

```
(hold SELECT) R, A, L, A, R, A, L
```

— was executed against the ROM's validator in mGBA and produced
`flags = 0x01` (BGM unlocked), identical to the published `R L R L`. The same
works with B or Start interleaved. These spellings appear on no published list.

**Bounds proven by rejection:**

| Input (hold SELECT) | Result |
|---|---|
| `L, R, L, R` (reversed BGM) | flags `0x00` — rejected |
| `R, L, R, Up` (wrong final key) | flags `0x00` — rejected |
| `R, L` (prefix only) | flags `0x00` — rejected |
| `U U D D L R L R B A` (Konami tail appended to Expert) | flags `0x02` only — no extra effect |
| re-enter BGM after it is unlocked | flag stays `0x01`, no duplicate effect |

**Effects confirmed via RAM:** `r/1 0x03000010` before a code = `0x00`; after
BGM = `0x01`; after Expert (fresh state) = `0x02`; after 10 credits (fresh
state) = `0x04`. The model in `validator_model.py` reproduces all of these
exactly (including the accepted interleaving and the three rejections).

## 7. Validation evidence

**Observed (emulator / RAM):**
* mGBA boots the ROM on `:317`; screenshots captured of licence screen, ATLUS
  logo, title (`PUSH START`), and the full story intro (e.g. `shot_00.png`,
  `flow_04.png`, `paced_18.png`, `title_saved.png` in the work dir).
* XTEST key events reach the game: Start advances the title → story, Start
  advances story pages, Down/Left/Right/Up/A/B/Select at the title produce no
  visible menu (confirmed by screenshots).
* Calling `0x08002E80` from the mGBA CLI debugger with simulated key globals and
  reading `0x03000010` yields the flag values in §6b. This is the ROM's own code
  executed in the emulator — ground truth per guide §16.19.
* Savestate at the title saved with Shift+F1; loading it with `-t` reproduces
  the title state.

**Derived (disassembly):**
* Key remap at `0x08000450`; validator control flow at `0x08002E80`;
  table contents at `0x0836271C`/`0x0836274C`; flag-byte address from
  `0x80009F0(16) = 0x03000000+0x10`; scene table and scene index
  `0x0203259C`; hint-message display at `0x08002700`.

**Inferred (not executed):**
* That entering the BGM code makes the `BGM ` menu item appear in OPTIONS:
  the code draws the literal `BGM ` (`0x08036260`, call at `0x8002FEE`) and the
  OPTIONS function gates an item on a status word, but the OPTIONS screen itself
  was not rendered in this session (see §8).
* That the Expert flag also selects 10 starting credits (published sources
  describe Expert mode as "start with 10 credits"); only the flag bit was read
  in RAM, no new game was started with Expert enabled.

## 8. Unknowns

* **OPTIONS screen not reached through the UI in this session.** The title
  screen offers only Start, which plays the long story intro; repeated Start
  presses advance/loop the story and return to the title, but no menu or OPTIONS
  screen was observed. Forcing the scene index (`0x0203259C`) to 1 through the
  scene dispatcher (`0x08000300`–`0x080033E`) did not render the OPTIONS menu —
  it returned to the story display, so some additional scene state is required.
  This does **not** leave the cheat system unverified: the validator was called
  directly inside mGBA with RAM reads of the resulting flags (§7). The OPTIONS
  screen function itself is fully identified at `0x080021C0` and its call site
  to the validator at `0x080021E2` is unambiguous.
* The full return domain of the story scene function (which scene index leads
  to a playable game / pause menu) was not enumerated; consequently the
  in-game pause/mode-select screens were not walked in this run.
* Exact bytes/graphics of the 10-credit hint tiles were not rendered; the hint
  strings are tile indices and were decoded by comparison with the code lengths.

## 9. Tooling

All helper scripts were kept in `/tmp/dda` (analysis scratch, not shipped):

| Script | Purpose |
|---|---|
| `mgba_debug.py` | Launch `mgba -d` on a pty; `send()`/`read_avail()` helpers; optional `-t` savestate. |
| `keylib.py` | XTEST key helpers for `:317` with mGBA's default keymap. |
| `oracle.py` | Calls the ROM validator at `0x08002E80` with simulated key globals; reads `0x03000010`. |
| `validator_model.py` | Clean Python reimplementation of the validator and its three tests + bounds. |
| `reach_options.py`, `nav_*.py` | Boot/navigation experiments and screenshots. |

System tools: `file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings`,
Python 3 + `capstone` 5.0.7, `arm-none-eabi-objdump` (`-M force-thumb`),
`gdb-multiarch` (GDB stub port 2345 was occupied by a sibling session, so the
`-d` pty debugger was used instead), `Xvfb`, `openbox`, `xdotool`, `scrot`,
ImageMagick `import`.

No ROM bytes or copyrighted assets are reproduced here; only addresses,
hashes, algorithms and the author's own button sequences are published.

## 10. Legal note

No ROM image, extracted graphics, music or game text is redistributed. All
findings are addresses, hashes, and original sequences derived from a legally
held copy of the ROM.
