# Doom II: Hell on Earth (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Doom II: Hell on Earth.gba` |
| Size | 16,777,216 bytes (0x01000000) |
| Header title | `DOOM II` |
| Game code / maker | `A9DE` / `52` |
| Version | 0 |
| Entry branch | `0xEA000030` → `0x080000C0` (stock crt0, not a cracktro patch) |
| Header complement | stored `0x06`; expected `0x1F` from bytes 0xA0–0xBC — **header was rebuilt/edited**; checksum field `0x0000` |
| Embedded GBA headers | exactly **1** (Nintendo logo at file 0x4 only; no multi-game cart, no appended trainer) |
| MD5 | `efefee9082a83fc6e49f87510746eac0` |
| SHA-1 | `2feeffc96386cf2cc0b2076928b010f18e9e9748` |
| SHA-256 | `2a4c00510638659b6b207a7d2aa51cbd17bbad9a63f42bc2dc01c121eb83cf95` |
| Developer / publisher | Torus Games / Activision (per 3rd party cheat indexes release data) |

No scene cracktro or cheat trainer found: entry word is the stock branch and there is no second
header/resident trainer. The bad complement/checksum is a rebuilt-header artifact (guide §16.1),
not an in-game cheat.

## 2. Executive summary

This ROM implements a **developer button-code system**: while **paused in-game**, hold **L+R** and
press an eight-button **A/B** sequence. There are **exactly seven accepted codes**; they live in a
7-byte literal table at ROM `0x08037C12`. The validator was recovered at `0x08022778` and its gate
at `0x08021BB6`–`0x08021BEA`; every return branch was enumerated. All seven codes are already on
published lists, but the accepted space is **closed and fully characterised**: the complete 2^8 =
256 input space was entered in the emulator (§16.9) and precisely the seven table entries produce
effects.

A genuine **unpublished spelling** was found and proven in-game: because the validator compares
only the low eight bits of a left-shifting input register, any **longer** sequence whose **last eight**
buttons equal a table entry is accepted. `AABBAAAAA` (9 presses) and `BABABABAAABAAAAA`
(16 presses) are accepted and produce RAM-verified effects not present in any published list.

There is **no text/password system, no level-select screen, no sound test, no hidden debug menu and
no cheat options entry**. The PC cheats (`IDDQD`, `IDKFA`, `IDCLIP`, `IDCLEV`, …) are absent from the
image in any encoding; the two warp codes published for **Doom GBA** (`ABAABBBA`, `ABAABBAA`) are
**not** present in this Doom II table and were empirically rejected — confirming §16.11 (same
franchise, different SKU, different code set).

## 3. How to reproduce

**Emulator / display**: mGBA (SDL build), `DISPLAY=:316`, `SDL_AUDIODRIVER=dummy`,
`Xvfb :316 -screen 0 1024x768x24`, `openbox`. Default keymap verified against KEYINPUT `0x04000130`:
A=`x` (bit0), B=`z` (bit1), Select=`BackSpace`, Start=`Return`, D-pad=arrows, L=`a` (bit9),
R=`s` (bit8). Hold keys 60–100 ms; short taps can be missed.

**Menu path**: power on → title "PRESS START" → Start → main menu (New Game / Options / Load Game /
Credits) → New Game → skill ("I'm too young to die" / "Hey, not too rough" / "Hurt me plenty" /
"Ultra-Violence" / "Nightmare!") → in-game → **Start to pause** → hold **L+R** → tap the 8 (or more)
A/B buttons → release → Start to unpause.

**Codes verified in-game** (all need the pause + L+R gate):

| Sequence | Effect | RAM proof |
|---|---|---|
| `AABAAAAA` | God mode ON | `0x02016338` `0xF2000000` → `0xF2010000` |
| `AABABBBB` | God mode OFF | `0xF2010000` → `0xF2000000` |
| `ABBAAAAA` | All weapons, max ammo, 200% armor, all keys | keys `0x02016300`=0xFF00; armor `0x02016320`=0x00C80000; weapons `0x02016334`=0x02290000; cheats `0x02016338`=0xF2100000 |
| `BAAAAAAA` | Computer automap | `0x03000330` 0 → 1 |
| `BABAAAAA` | Berserk | `0x0201630C`=0x1E0000, `0x02016350`=0x10000 |
| `BBBAAAAA` | Invulnerability power-up | `0x02016354`=0x07080000 |
| `BBAAAAAA` | Radiation suit | `0x02016358`=0x0E100000 |
| **`AABBAAAAA` (9 presses, novel)** | same all-weapons effect | same four word changes as `ABBAAAAA`; screenshot `novel_code_effect_crop.png` |
| **`BABABABAAABAAAAA` (16 presses, novel)** | god mode ON (unpublished spelling) | `0x02016338` → `0xF2010000` |
| `AAAAAAAA` (rejected) | nothing | all monitored words unchanged |

**Published codes consulted**: DoomWiki "Console Doom cheats" (archived 2023 snapshot), 3rd party cheat indexes
GBA Doom II cheats page (archived 2023). The text-only PC codes on the same 3rd party cheat index page were
treated as PC-only and are not in this ROM (literal search for `IDDQD`/`IDKFA`/`IDCLIP`/… returned
zero hits). The fetched pages contained no prompt-injection payload.

## 4. Address map

| Address (ROM unless noted) | Meaning |
|---|---|
| `0x08021BB6`–`0x08021BEA` | Cheat gate in the in-game pause handler: requires game-mode byte at `[0x03082708]+2 == 1`, L/R edge on `0x0300120C`, A/B on `0x03001210`; calls validator with `(player_struct, A?1:0)`. |
| `0x08022778` | **Cheat validator / shift-register sequencer** (called from `0x08021BEA`). |
| `0x08037C12` | **Cheat code table**, 7 bytes: `DF D0 9F 7F 1F 5F 3F`. |
| `0x08022800` | 7-entry jump table of cheat action handlers. |
| `0x0802281C` / `0x0802282C` | God ON / god OFF (`0x08014190`). |
| `0x0802283C` | Give everything (`0x08012510`). |
| `0x0802284C` / `0x0802285C` / `0x0802286C` / `0x0802287C` | Power-ups via `0x080125AC` with action index 0 / 3 / 1 / 5. |
| `0x0800E964` | Frame input reader; produces `0x0300120C` (newly pressed), `0x03001210` (edge), `0x03001214` (previous), `0x03000334` (held). `mvn r1,r1` at `0x0800E96A` converts active-low KEYINPUT. |
| `0x08037C0E` | ASCII debug string `"form 0x%X to 0x%X"` immediately before the code table (context only). |
| `0x020162E4` | Player structure base (observed in watchpoints). |
| `0x02016300` / `0x02016320` / `0x02016334` / `0x02016338` | Keys bitmask / armor / weapons-owned / cheat flags. |
| `0x02016354` / `0x02016358` | Power-up timers (invulnerability / radiation suit). |
| `0x03000330` | Automap flag. |
| `0x03082708` + 2 | Game-mode byte; must be 1 (in-game/pause) for the gate. |

Saved-state mapping (mGBA `.ssN`, 397,312-byte `gbAs` chunk): IWRAM at state `0x19000`,
EWRAM at `0x21000`; e.g. armor `0x02016320` ↔ state `0x37320`, automap `0x03000330` ↔ `0x19330`.
Verified by matching debugger reads to savestate words.

## 5. Algorithm

Reconstruction from the disassembly of `0x08022778` and the gate at `0x08021BBE`:

```
# per frame, only while paused in-game and L/R activity detected:
btn = 1 if (NEW_KEYS & KEY_A) else 0        # A=1, B=0
state = player[0x82]                        # 8-bit shift register
player[0x82] = (state << 1) | btn           # newest press enters bit 0
# (bytes player[0x83..0x84] keep additional shift/count bits; only the low
#  8 bits at player[0x82] are compared against the table)
for i in 0..6:
    if player[0x82] == CODE_TABLE[i]:       # table at 0x08037C12
        JUMP_TABLE[i]()                     # dispatch action, then reset
        player[0x82] = 0
        clear player[0x83..0x84] bits
        sound(0x0800BEC0)                   # confirmation SFX (exploding barrel)
        break
```

Consequences (all confirmed in emulator):

* Only the **low 8 bits** of the register are compared, so the *effective* code is the **last eight**
  A/B presses; any number of preceding presses is ignored. This is the source of the novel aliases.
* `A` contributes bit 1, `B` contributes bit 0; the **first** of the eight presses ends up in bit 7.
  `AABAAAAA` → `0b11011111 = 0xDF`, matching `CODE_TABLE[0]`.
* The gate is in the *pause/in-game* handler, so codes are unreachable on the title, main, options,
  skill-select and credits screens (no player struct there).

## 6. Tables

`CODE_TABLE` at `0x08037C12` (bytes `DF D0 9F 7F 1F 5F 3F`):

| Index | Value | Sequence | Effect | Action target |
|---:|---:|---|---|---|
| 0 | `0xDF` | `AABAAAAA` | God mode on | `0x0802281C` → `0x08014190(1)` |
| 1 | `0xD0` | `AABABBBB` | God mode off | `0x0802282C` → `0x08014190(0)` |
| 2 | `0x9F` | `ABBAAAAA` | All weapons/ammo/armor/keys | `0x0802283C` → `0x08012510` |
| 3 | `0x7F` | `BAAAAAAA` | Computer automap | `0x0802284C` → `0x080125AC(0)` |
| 4 | `0x1F` | `BBBAAAAA` | Invulnerability | `0x0802285C` → `0x080125AC(3)` |
| 5 | `0x5F` | `BABAAAAA` | Berserk | `0x0802286C` → `0x080125AC(1)` |
| 6 | `0x3F` | `BBAAAAAA` | Radiation suit | `0x0802287C` → `0x080125AC(5)` |

Alphabet: two symbols, `A`/`B`; fixed length 8 effective presses; no checksum, no parameters, no
level/difficulty field. Representable code space = **2^8 = 256**, of which **7** are accepted.

**Published-code verification**: all seven ROM table entries match the 3rd party cheat indexes Doom II GBA list.
DoomWiki's GBA list adds `ABAABBBA` (warp next) and `ABAABBAA` (warp 10); both are absent from this
table and were entered in-game with no visual or RAM effect — they belong to the sibling **Doom**
SKU, not this Doom II image. DoomWiki's "Disable god mode" and 3rd party cheat index entries are otherwise
consistent. No published code was found to be a typo.

## 6b. Enumeration

* **Space**: 8 button positions × 2 symbols = 256 candidate sequences (as a byte, `A=1, B=0`).
  The validator is a 7-entry closed lookup; no computed/checksum path exists.
* **Method (§16.9)**: all 256 sequences were entered on the real pause screen in a controlled loop
  (savestate reload each trial, L+R held, 60 ms presses), and the player-struct/automap words were
  diffed against a no-code control. Result: **exactly 7 accepted**, `BAAAAAAA`, `BBAAAAAA`,
  `AABAAAAA`, `BABAAAAA`, `ABBAAAAA`, `BBBAAAAA` produced direct effects; `AABABBBB` was proven by
  enabling god mode first and observing the flag return to `0xF2000000`. No 8-press sequence outside
  the table produced any effect. Full log: `enumerate_log.txt`, `enumerate2_log.txt`.
* **Novel (unpublished) codes accepted in-game** — longer sequences whose **last eight** presses
  match a table entry:
  * `AABBAAAAA` (9 presses; last eight = `ABBAAAAA`) → all-weapons effect, RAM values
    keys=`0xFF00`, armor=`0x00C80000`, weapons=`0x02290000`, cheats=`0xF2100000`; screenshot
    `novel_code_effect_crop.png`. Not on 3rd party cheat indexes (all published codes are 8 presses).
  * `BABABABAAABAAAAA` (16 presses; last eight = `AABAAAAA`) → god flag `0x02016338` =
    `0xF2010000`.
  * `BAABBAAAAA`, `ABAABBAAAAA` (10/11 presses) also accepted with the same all-weapons effect.
* **Bounds proven by rejection**: `AAAAAAAA` (byte `0xFF`, not in table) — no change in any
  monitored word. 249 of the 256 8-press sequences were rejected. The two Doom-GBA warp codes were
  also rejected with zero effect. A code whose trailing eight presses are not a table value is
  rejected however long it is (the low byte simply never matches).

## 7. Validation evidence

* **Observed** — emulator screenshots of the title, main/options/skill-select/credits/pause screens;
  HUD change from 50/0%/pistol to 400/200%/all weapons/keys after `ABBAAAAA` and after the novel
  `AABBAAAAA`; mGBA savestate word diffs at the addresses in §4; read-watchpoint hit on `0x03000330`
  with caller `0x08012657` during `BAAAAAAA` entry; KEYINPUT values confirming the keymap.
* **Derived** — disassembly of the gate (`0x08021BB6`–`0x08021BEA`), validator (`0x08022778`),
  its 7-byte table (`0x08037C12`), and 7-entry jump table (`0x08022800`); decoded byte→sequence
  mapping matches all 7 published codes and all 256 in-game trials.
* **Inferred** — the extra bytes at `player+0x83/+0x84` implement wider shift/count bookkeeping;
  only their low byte at `player+0x82` is used for matching. The confirmation sound routine
  (`0x0800BEC0`) was identified from the dispatch epilogue, not listened to under `SDL_AUDIODRIVER=dummy`.

## 8. Unknowns

* The purpose of the `player+0x83/+0x84` bookkeeping bits was not fully traced (they do not affect
  acceptance; the low 8 bits are authoritative).
* The exact semantic label of power-up action indices 0/3/1/5 in `0x080125AC` is inferred from the
  observed RAM effects (automap / invulnerability / berserk / rad suit), not from debug symbols.
* Whether the two warp codes work on the *Doom* GBA SKU is the sibling report's scope; this ROM
  rejects them.
* Game mode byte `0x03082708+2 == 1` was not enumerated across all values; it is only known to be
  required for the gate.

## 9. Tooling

* `file`, `md5sum`/`sha1sum`/`sha256sum`, Python header/logo scan (`find_codes.py`,
  `packed_table.py`, `lit_scan.py`, `find_lr.py`, `scan_input_funcs.py`).
* `strings -t x`, `grep -abo`, web archive snapshots of 3rd party cheat indexes / DoomWiki.
* `arm-none-eabi-objdump -M force-thumb` for all disassembly; Capstone 5.0.7 literal/BL scanners.
* mGBA SDL (`-3`, `-t` savestates, `-d` command-line debugger) on Xvfb `:316`; `xdotool` XTEST
  input; `import -window root` + `convert` crops.
* Savestate `gbAs` chunk decompressed with Python `zlib` for RAM word diffs (`effect_scan.py`,
  `enumerate_codes.py`, `enumerate2.py`, `aliastest.py`, `verify_final.py`, `mgba_dbg.py`).
* mGBA `-d` read watchpoint on `0x03000330` used as a dynamic xref to the cheat action dispatcher.

No ROM or copyrighted assets are redistributed; only addresses, hashes, algorithms and our own
scripts are reported.
