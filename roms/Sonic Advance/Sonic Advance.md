# Sonic Advance (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Sonic Advance.gba` |
| Size | 8,388,608 bytes (0x00800000) |
| Header title | `SONICADVANCE` |
| Game code | `ASOE` (USA, En+Ja) |
| Maker | `78` |
| Version | 0x00; complement 0x4C; header checksum 0x0000 |
| Entry word | `0xEA00002E` — stock `b 0x080000C0`, no cracktro/trainer patch |
| Build stamp | `0.69Wed Oct 31 18:32:29  2001` at ROM `0x07F8F48` |
| MD5 | `49ecc8ef1988e7ae81fbda1b4cf71eed` |
| SHA-1 | `d842afa7dd1e84de08addb94a51506f1bcafd551` |
| SHA-256 | `afc29e3325baf68a1822e88b25fcb59c8bdc29b8cdc48fa21c56defbd60ca020` |

The SHA-1 matches the No-Intro retail image (ASOE, USA). Additional Nintendo-logo hits at file
`0x32C`, `0x7BA174`, `0x7BA324` are embedded header copies inside data (maker shown as `8P`),
not a multi-game cart; only one bootable header exists at `0x0`. No patch or trainer present.

## 2. Executive summary

Sonic Advance has **no password code system**. Its only in-game, developer-intended cheat is a
**button-code** on the character-select screen that grants a computer-controlled Tails partner
(the "Sonic & Tails" / "Sonic 2 mode" trick). It is a 9-press sequence gated by a single character
condition, validated by a table-driven progress machine:

```
UP (while Sonic highlighted) → RIGHT → DOWN → RIGHT → L → RIGHT → R → RIGHT → A
```

Correct entry plays the ring chime (sound 0x75) and sets `gTailsEnabled = 1` at RAM `0x03005050`;
Tails then visibly follows Sonic in the level. The whole space was enumerated from the ROM's
key-mask table and its validator (§5–6b), including **one undocumented accepted alias** (final
press `A+START`) and two proven rejection bounds. The published level-select-by-Japanese-language
claim was tested and **not reproduced** on this image; the level select is normally reached via
Time Attack.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 (`/usr/local/bin/mgba -3`), Xvfb `:317`, `SDL_AUDIODRIVER=dummy`.
* Keymap used: A = `x`, B = `z`, L = `a`, R = `s`, Start = `Return`, Select = `BackSpace`,
  D-pad = arrow keys. **Holds of ~100 ms are required** — zero-delay `xdotool key` taps are
  missed by this engine's input polling.
* Path: language screen (Japanese or English) → A → intro (~50 s, skippable) → title screen
  ("PRESS START"). Press **Start repeatedly at ~0.4 s intervals across the title cycle**; the
  title handler accepts Start only in frames 61–900, so a single poorly-timed press appears to
  do nothing (a demo runs after frame 900). → main menu (5 items) → Game Start → character select.
* Code entry: with Sonic highlighted, press `Up, Right, Down, Right, L, Right, R, Right, A`
  (100 ms holds, 180 ms gaps). The last `A` both completes the code and confirms Sonic.
  Ring chime + Tails following Sonic = success.
* Savestate workflow: save at the character-select screen (mGBA Shift+F1), then load with F1 for
  each trial. RAM reads used mGBA's `-d` pty debugger with `kill -INT <mgba pid>` to break and
  `r/4 <addr>` to read.
* Soft reset: hold `A+B+Start+Select` together.

Screenshots kept on disk in `/tmp/sonic1/`: `charselect.png`, `in_game.png`
(canonical code), `alias_game.png` (novel alias), `rejected.png` (near-miss rejected),
`course_select.png`, `soundtest.png`, `menu3c.png`.

## 4. Address map

All ROM addresses are `0x08000000 + file offset`.

| Item | Address | Evidence |
|---|---|---|
| `CheckCPUPartnerUnlock` (validator) | ROM `0x0805B7B0` | Disassembly; literal pointer to table at `0x0805B814` |
| `sTailsUnlockKeys` (u16[10] key table) | ROM `0x08681514` | Literal byte pattern found uniquely |
| Success check `cmp state,#8` | ROM `0x0805AB50` | Disassembly of `Task_805AAF8` |
| Ring-chime play (sound 0x75) | ROM `0x0805AB54` | `movs r0,#0x75; bl 0x080977E4` |
| `gTailsEnabled = 1` write | ROM `0x0805AB5C–0x0805AB5E` | `ldr r1,=0x03005050; strb r0,[r1]` |
| `gTailsEnabled` (u8) | RAM `0x03005050` | Literal above; read 0 before / 1 after code |
| `gPressedKeys` (u16) | RAM `0x0300237C` | Literal at `0x0805B7EC`; validator reads it |
| Progress index `unk39` (u8) | `gCurTask->data + 0x39` | `adds r3,#0x39` at `0x0805B7F4`; literal `0x03000039`-based arithmetic |
| `gCurTask` | RAM `0x03001F90` | Literal at `0x0805B7E8` |
| Title-screen Start gate | ROM `0x0800D898–0x0800D8A2` | `ldrh gPressedKeys; and #8` |
| `Task_SwitchToMainMenu` | ROM `0x0800DF89` | Literal at `0x0800D8F8` |
| `CreateMainMenu` | ROM `0x0800D8FC` | Function prologue immediately after title handler |
| Save magic `PIRO` | `.sav` offset 0 | `0x4F524950`; 10 flash sectors, checksum at sector+0x42C |
| `gLoadedSaveGame` | RAM `0x03005160` | SA1 linker script / decompilation |

Static function names and addresses were cross-checked against the public SAT-R SA1/SA2
decompilation (`github.com/SAT-R/sa2`, `src/game/sa1/ui/character_select.c`,
`src/game/sa1/menus/title_screen.c`) and confirmed byte-for-byte in this ROM; all findings were
then reproduced live in mGBA.

## 5. Algorithm

Exact reimplementation of the validator (`0x0805B7B0`):

```python
TABLE = [0x10, 0x80, 0x10, 0x200, 0x10, 0x100, 0x10, 0x01, 0x00, 0x00]
#        RIGHT  DOWN  RIGHT  L      RIGHT  R      RIGHT  A      -      -
state = 0xFF                    # CharSelect_3C.unk39

def on_frame(gPressedKeys, selected_char):
    global state
    if gPressedKeys == 0:
        return
    if (gPressedKeys & 0x40) and selected_char == 0:   # DPAD_UP on Sonic
        state = 0
        return
    if state != 0xFF:
        if gPressedKeys & TABLE[state]:
            state += 1
        else:
            state = 0xFF                               # terminal failure

def on_confirm():                                      # Task_805AAF8, ~56 frames later
    if state == 8:
        play_sound(0x75)                               # ring chime
        gTailsEnabled = 1                              # 0x03005050
```

Notes:
* `selected_char` is `(unk28 >> 8) & 3` (0 = Sonic, 1 = Tails, 2 = Knuckles, 3 = Amy). It is
  tested **only** for the starting `UP`; the rest of the sequence is pure key-mask matching.
* Each comparison is a **bitwise AND**, not equality — extra simultaneously-held buttons do not
  invalidate a step (this yields the alias in §6b).
* `TABLE[8]` and `TABLE[9]` are zero sentinels; state 8 is the success value captured at confirm,
  so those entries are unreachable in practice.
* `gTailsEnabled` is cleared to 0 on every entry to the character-select screen
  (`CreateCharacterSelectionScreen`, disassembly near `0x08059BA4`): the cheat is a per-session
  RAM flag, **not** a saved unlock.

## 6. Tables

**Key masks (active-high, `~KEYINPUT & 0x3FF`):**

| Button | Mask | Button | Mask |
|---|---|---|---|
| A | 0x001 | Right | 0x010 |
| B | 0x002 | Left | 0x020 |
| Select | 0x004 | Up | 0x040 |
| Start | 0x008 | Down | 0x080 |
| R | 0x100 | L | 0x200 |

**`sTailsUnlockKeys` at ROM `0x08681514`** (raw bytes
`10 00 80 00 10 00 00 02 10 00 00 01 10 00 01 00 00 00 00 00`):

| Index | Mask | Button | Effect when matched |
|---:|---:|---|---|
| 0 | 0x010 | Right | cursor Sonic→Tails |
| 1 | 0x080 | Down | — |
| 2 | 0x010 | Right | cursor Tails→Knuckles |
| 3 | 0x200 | L | — |
| 4 | 0x010 | Right | cursor Knuckles→Amy |
| 5 | 0x100 | R | — |
| 6 | 0x010 | Right | cursor Amy→Sonic |
| 7 | 0x001 | A | state 8 → success on confirm |
| 8 | 0x000 | — | unreachable sentinel |
| 9 | 0x000 | — | unreachable sentinel |

**Published-code verification:**

| Source | Claim | Result |
|---|---|---|
| GameFAQs / Victorycheats / Sonic World | `Up, Right, Down, Right, L, Right, R, Right, A` | **Verified** literally as the ROM table and accepted in emulator |
| SuperCheats / Sonic World | "Up on Sonic, Down on Tails, L on Knuckles, R on Amy, then A" | Same code; the intervening `Right` presses move the cursor to each character |
| Victorycheats | "Set language to Japanese → level select after character select" | **Not reproduced**: fresh Japanese save went straight to Neo Green Hill Act 1. Level select is reachable via Time Attack → character select → course select |
| Victorycheats | "Sound Test gains 3 songs after clearing Moon Zone / Super Sonic ending" | Save-gated; not tested (requires full game clear). Sound Test screen itself verified |

All CodeBreaker/GameShark entries found on the web are cheat-device memory pokes (e.g.
`33005084 000x` for character) and are **out of scope**; they were not used or reported as
in-game codes, though the RAM addresses they target (e.g. `0x03005084`) do appear in the ROM.

## 6b. Enumeration

**Space definition.** The system is a single fixed button sequence, not a parameterised code:

* Input alphabet: 10 GBA keypad bits; the validator only tests six (Up 0x40, Right 0x10,
  Down 0x80, L 0x200, R 0x100, A 0x01).
* Length: 1 start condition (`UP` while character index = 0) + 8 accepted key events = **9
  keypresses**; plus 2 zero sentinel slots in the 10-entry table that cannot be satisfied.
* Table size: exactly 10 `u16` entries at `0x08681514` (20 bytes). All were dumped and decoded.
* Validator states: `0xFF` (idle/failed), `0..7` (partial progress), `8` (success).
  There are **no action branches** and no difficulty/level/character fields — the entire
  developer-intended space is one canonical 9-press sequence.
* Because each step uses `gPressedKeys & mask`, any press whose mask is a **superset** of the
  required bit is accepted. The brute-force acceptance set is therefore unbounded (limited only
  by the UI: a stray `A`/`B` at the select screen triggers confirm/cancel). A+B+Start+Select also
  soft-resets, so usable aliases are constrained.

**Novel code (not in any published list).** Canonical sequence but with the **final press
`A+START` held simultaneously** (`x`+`Return`):

```
Up, Right, Down, Right, L, Right, R, Right, A+START
```

* Decoder prediction: `A+START` mask = `0x001|0x008 = 0x009`; `0x009 & TABLE[7]=0x001` → true →
  state 8. START has no handler in the character-select task, so A still confirms.
* Emulator result: ring chime, `gTailsEnabled` read back as **1** at `0x03005050`, and Tails
  visibly follows Sonic (`alias_game.png`).
* No published list specifies `A+START`; all list plain `A`. This is a genuinely new accepted
  combination derived from the validator's bitwise-AND semantics.

**Bounds proven by rejection (all RAM-verified):**

| Test | Changed field | Expected | Observed `gTailsEnabled` |
|---|---|---|---|
| Near-miss | `L` (index 3) replaced by `Select` | reject | **0**, Sonic alone (`rejected.png`) |
| Wrong start | `UP` pressed while Tails highlighted (index 1) instead of Sonic | reject | **0** |
| Sentinel | `TABLE[8]=TABLE[9]=0` — no 10th/11th press can advance; any key press after state 8 fails | structurally unreachable | derived from table + validator |

**Negative-space checks for other systems.** `strings -t x -n 4` over all 8 MiB produced no
`password`, `cheat`, `secret`, `unlock`, `invalid`, or `enter code` strings; the only plaintext
runs are the credits block near `0x0A6800` and the build stamp. All in-game UI text (menus,
"PRESS START", "SELECT A CHARACTER", level names) is **font/tile-indexed**, so `strings` silence
does not imply no UI — every reachable screen was walked visually (language, title, main menu,
Options, Sound Test, Time Attack, character select, course select, in-game). No password entry
surface, no debug menu, and no level-select code beyond the normal Time Attack→course-select
path exists on these screens.

## 7. Validation evidence

* **Observed** — mGBA screenshots at each screen; `gTailsEnabled = 0x00000000` before code entry and
  `0x00000001` after both the canonical code and the novel `A+START` alias; `0x00000000` after both
  rejected trials; Tails sprite following Sonic in `in_game.png` and `alias_game.png`.
* **Derived** — validator algorithm, table semantics, success branch and sound ID from
  disassembly at `0x0805B7B0`, `0x0805AB50`, and the literal pool at `0x0805B814`; key table bytes
  at `0x08681514`; title-screen frame window 61–900 and Start gate from `0x0800D878`.
* **Inferred** — sound 0x75 is the ring chime (audio was muted with `SDL_AUDIODRIVER=dummy`, so the
  chime was not heard; the call and ID are confirmed in code); save-based unlockables (Moon Zone,
  Chao Garden, Super Sonic, +3 Sound Test songs) are gated behind clearing the game and were not
  exercised.
* **Unverified published claim** — Japanese language → level select (tested, not reproduced).

## 8. Unknowns

* The exact in-game effect of the +3 Sound Test songs after a full clear (save-gated, not tested).
* Whether `gTailsEnabled` is ever written to flash; disassembly shows it is cleared on character
  select entry, so a permanent unlock is unlikely, but no full-game-clear save was produced.
* The two zero sentinel table entries are unreachable through the UI; a debugger forced state 8
  would be an artificial path, not an in-game code.
* Pause-menu contents were only glanced at (`Start` during Time Attack returned the records
  screen rather than an in-game pause overlay); no hidden pause cheat was found.

## 9. Tooling

* `md5sum`/`sha1sum`/`sha256sum`, `file`, `xxd`, `strings -t x`, Python 3 byte/literal scanning.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for ROM
  disassembly; Python `struct` for literal-pool decoding (the `5894 083b`-style byte-order trap
  was avoided by decoding literals directly).
* mGBA 0.10.5 with `-3` and `-d` (pty debugger driven through a FIFO daemon; `kill -INT` to break,
  `r/4` to read RAM, `w/4` for one diagnostic write), Xvfb `:317`, openbox, xdotool, scrot,
  ImageMagick `montage`/`convert`.
* Public SAT-R SA1/SA2 decompilation (`github.com/SAT-R/sa2`) used as a cross-reference for
  function names/addresses; all of its claims were verified against this ROM's bytes and then in
  the emulator. Fetched web content was treated strictly as data.
* No copyrighted assets or ROM data are redistributed here; only addresses, hashes, algorithms
  and original observations are published.
