# Crash Bandicoot: The Huge Adventure (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Crash Bandicoot: The Huge Adventure/Crash Bandicoot: The Huge Adventure.gba` |
| Size | 8,388,608 bytes (8 MiB / 64 Mbit) |
| Header title | `CRASH` (0xA0, NUL-padded) |
| Game code | `ACQE` (0xAC) |
| Maker code | `7D` (0xB0) |
| Software version | 0 (0xBC) |
| Complement | 0x4B (0xBD), valid for the header as stored |
| Header checksum | 0x0000 (0xBE), zeroed — rebuilt-header artifact (§16.1) |
| Entry word | `0xEA00002E` = stock `b 0x080000C0`; no cracktro, no trainer |
| MD5 | `32d74527bfe723470c2c5406c325fb59` |
| SHA-1 | `5a2651c78bb8a1d707e3c3af1f46fb64e2104198` |
| SHA-256 | `6be639d1db218ca2bf2b1ff0ee0867334404cead5fb6684af4870d4644a15635` |

Embedded-header scan: the 156-byte Nintendo logo occurs exactly once, at file
0x4. **Single image**, not a multicart, no second header. The first 4 KiB carry
no cracktro banner and the crt0 at 0x080000C0 is the normal Vicarious Visions
startup (stack/IWRAM setup, ARM/Thumb switch, then the game `main`). The image
is a retail USA build (`ACQE`, Feb 2002 US release), not the PAL "Crash
Bandicoot XS" or Japanese "Crash Bandicoot Advance" builds.

## 2. Executive summary

**This ROM contains no in-game password, button-code, hidden-menu or debug-menu
cheat system.** There is no code-entry screen, no alphabet, no validator, no
key-sequence table and no input-reachable gate.

The complete in-game interface was enumerated:

* **Title** (`press start`, sprite-drawn — no text-id call).
* **Main menu**: New Game (26), Load Game (27), Credits (59); 3 items, cursor
  wraps 0→1→2→0.
* **Save-file screen** (reached from Load Game and from the in-level pause
  "warp room" action): Load Game (27), **Load Link Game (28)**, Save Game (30),
  Delete Game (29), Exit (32). A separate table holds five more ids that this
  renderer never draws (crystals/powers/gems/relics/time trial, 54/53/55/56/57).
* **Link screen** (selecting Load Link Game): a dedicated screen with no
  menu-table text; B aborts back to the file menu (observed).
* **In-level pause**: Resume (50), Music (48), Sound (49), Warp Room (51) plus
  the Crystals (54) status header; the 5-entry table also contains Restart Trial
  (52), which is not counted in a normal level (RAM count = 4).
* **Credits** (main-menu item 2): rendered by a non-text-table path, so it emits
  no text ids; the screen change was observed.

What the game *does* contain, and what an analyst should record as its
developer-intended extras, is a **link-transfer save record**, byte-compatible
with the sibling title *Crash Bandicoot 2: N-Tranced*:

* A 512-byte record: four 112-byte (0x70) slots, four slot-present bytes at
  `+0x1F4`, magic `0x43`/`0x12` at `+0x1F8`/`+0x1F9`, an **unlock byte at
  `+0x1FA`**, a zero byte at `+0x1FB`, and a 32-bit checksum at `+0x1FC`
  (sum of 127 words).
* The unlock byte is initialised to 0 and written **only** by the link receive
  state machine: bit `0x02` when the partner type is 2, bit `0x04` when the
  partner type is 3 (`0x08003654` / `0x08003670`).
* No instruction site anywhere else materialises `0x1FA`; the bit-test helper
  `0x08002CF4` has no BL/BLX caller and no pointer reference. There is therefore
  **no local display or effect** for those bits in this build, and no controller
  path writes them.

Because the engagement has no code space, §0.2 is satisfied in its
negative-result form: the UI text space is enumerated (70 ids, all classified),
the menu space is enumerated (every drawn item listed above), the input surface
is enumerated (1 `KEYINPUT` literal, 20 latch callers, 75 key-state reads,
0 pointer-referenced mask tables), and the one writable flag space (the 8-bit
transfer byte) is fully mapped to its writers and proven write-only.

## 3. How to reproduce

### Emulator and harness

```bash
Xvfb :266 -screen 0 1024x768x24 &
DISPLAY=:266 openbox &
export DISPLAY=:266 SDL_AUDIODRIVER=dummy
mkfifo dbg.fifo; (sleep 999999 > dbg.fifo &)
script -qefc "mgba -d -3 'game.gba'" /dev/null < dbg.fifo > mgba.log 2>&1 &
```

mGBA 0.10.5 SDL with the **CLI debugger** (`-d`); every observation is a
register/RAM read. No screenshots were used; the proof is the text-id stream
plus RAM. Debugger commands used (one per line on the FIFO):

| Command | Use |
|---|---|
| `b/t ADDR` | Thumb software breakpoint |
| `d N` | delete breakpoint N |
| `frame` | advance exactly one frame and return to the prompt |
| `x/4 ADDR` | read 4 words (address must be 8-hex-digit) |
| `r/2 ADDR`, `r/4 ADDR` | read halfword/word |
| `save N`, `load N` | savestate slots (files `*.ssN` beside the ROM) |
| `status`, `lb` | registers / breakpoint list |

Keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`,
D-pad=arrows. Hold 3–10 frames; the input latch is polled once per frame.
**Important harness note:** a breakpoint left on a per-frame renderer
(here `0x080055B8`) or on the text routine starves the menu state machine and
makes cursor keys look dead. Delete unrelated breakpoints before testing input;
the pause menu also arms a 30-frame repeat lock (`[obj+0x68]`), so moves must be
≥35 frames apart or they are swallowed.

### Menu path used (all verified by text-id stream)

1. Boot; wait ~10 s (logos + title). Title draws no text id.
2. Start → main menu. Ids 26,27,59 every frame.
3. Cursor: main-menu object at `0x0200344C`, `[+0]` = index; 0→1→2→0.
4. Down to index 1, A → save-file screen (fade). Ids 27,37,35 on an empty slot
   (load game / empty / cancel).
5. B → slot-action menu: ids 27,28,30,29,32 (load / **load link** / save /
   delete / exit). Down to index 1, A → link screen (no text ids); B aborts back
   to the same 5-item menu.
6. In level: Start → pause. Ids 50,48,49,51 plus 54 header.
7. Main menu index 2, A → credits (no text ids; screen changes).

### Sequence test

At the main menu, the 10-press sequence
`Up Up Down Down Left Right Left Right B A` was entered (3-frame holds, 10-frame
gaps). The menu id set and cursor were unchanged; the savestate diff between
before and after was 2,185 bytes in IWRAM and 1,522 bytes in EWRAM — all
animation/timer state. No screen, flag or sound change.

## 4. Address map

| ROM address | Meaning |
|---|---|
| `0x080000C0` | crt0 (ARM), stock |
| `0x080007AC` | key latch: `held = ~KEYINPUT`, stores `u16` held at `0x030007E0`, pressed at `0x030007E2`; 20 BL callers |
| `0x080007D0` | the **only** `0x04000130` (KEYINPUT) literal in the image |
| `0x080007DC` | clear held/pressed |
| `0x08026F18` | `GetTextPtr(id)` → `u32[0x08172C18 + 4*id]` (44 callers) |
| `0x08172C18` | 70-entry UI text table (ids 0–69); strings `0x08172814`–`0x08172C10` |
| `0x0803603C` | main-menu renderer; hard-coded ids 26/27/59 at `0x08036054/64/74` |
| `0x08035DE8` | main-menu loop; action decode `0x08035CF0` |
| `0x0816ACFC` | save-file action table, 10 u32 ids (renderer draws first 5) |
| `0x08003A60` | save-file renderer (`cmp r7,#4`, loop 0..4) |
| `0x08003B40` | save-file input/loop (`B` → exit action 3) |
| `0x08004C2E` | caller of the save-file renderer |
| `0x0816ADD8` | pause table `{50,0}{48,4}{49,5}{51,2}{52,1}` |
| `0x0816ADC4` | second pause list `{48,4}{49,5}{51,2}{52,1}` |
| `0x08004EC0` | pause init; stores list at `[obj+0x14]`, selected at `[obj+0x18]` |
| `0x08004FAC` | `str r0,[r7,#0x14]` (list = `0x0816ADD8`) |
| `0x08004FB2` | count = 5 if `byte[0x030012A0+0x8C] != 0`, else 4 |
| `0x0800556C` | pause renderer (list walk at `0x080055B8`) |
| `0x080054E6` | pause action dispatch, jump table at `0x08005508` (actions 0–4) |
| `0x0801C1F8` | draws id 47 (`start:  load-save`) as the in-level HUD hint |
| `0x0801C560` | level-banner renderer; per-level record stride 0x24 |
| `0x0816C3AC` | level table, 25 records (20 levels + 5 bosses) |
| `0x0816AC50` / `0x0816AC64` | `"crash 1 <-> crash 2"` / `"... crash 3"` link labels, referenced from `0x087E3FCC`/`D0` |
| `0x08002B44` | record validate: sum 127 words, compare `[rec+0x1FC]` |
| `0x08002B70` | record checksum update |
| `0x08002B94` | `partner_type = byte[rec+0x1F9] >> 4` |
| `0x08002C14` | `slot_used(rec, idx)` = `byte[rec+0x1F4+idx] == 0` |
| `0x08002C40` | `write_slot(rec, idx, src)` copies 0x70 bytes + marks + checksum |
| `0x08002C6C` | `mark_slot(rec, idx)` |
| `0x08002C84` | reset record: mark slots, magic `'C'`/0x12, `+0x1FA=0`, checksum |
| `0x08002CE8` | `get_byte(rec,idx)` = `byte[rec+0x1F4+idx]` |
| `0x08002CF4` | `test_bit(rec,mask)` = `(byte[rec+0x1FA] & mask) != 0` — **no callers** |
| `0x08002D0C` | `clear_bit` — **no callers** |
| `0x08002D28` | `set_bit` — 2 callers, both link receive |
| `0x08002A64` | handshake validity: `byte[+0x1F8]==0x43` and `byte[+0x1F9]==0x12` |
| `0x08002E20`–`0x08002EFC` | transfer pack/unpack state machine |
| `0x080035F0`–`0x0800368C` | link receive dispatch: type 2 → bit 0x02, type 3 → bit 0x04 |
| `0x0816AE20` | sprite/UI coordinate table (near-miss for an input table; used by `0x080074E0`) |

`0x030007E0` has 75 literal references (gameplay + menus), all read the same
two halfwords.

## 5. Algorithm

### Key state

```
held   = (~*(u16*)0x04000130) & 0xFFFF
pressed = held & ~prev
*(u16*)0x030007E0 = held
*(u16*)0x030007E2 = pressed
prev = held
```

There is no history buffer, no ring, no timer. Menus branch on single bits of
`pressed`/`held`; the gamepad state is exactly two halfwords.

### Text ids

```
ptr(id) = u32[0x08172C18 + 4*id]      # ids 0..69, NUL-terminated ASCII
```

### Save record (512 bytes, used for link transfer and file slots)

```
+0x000  slot[0]   112 bytes
+0x070  slot[1]
+0x0E0  slot[2]
+0x150  slot[3]
+0x1C0  (52 bytes, not touched by the slot helpers)
+0x1F4  slot_present[4]   (0 = empty, 1 = used)
+0x1F8  0x43 ('C')
+0x1F9  0x12 (partner nibble = >>4; 1 = same game)
+0x1FA  unlock bits   (init 0)
+0x1FB  0
+0x1FC  checksum = sum of 127 little-endian words at +0x000..+0x1FB
```

Validation and link merge:

```
if byte[+0x1F8] != 0x43: reject (2)
if byte[+0x1F9] != 0x12: reject (1)
type = byte[+0x1F9] >> 4
...
recv_type = partner_type(partner_record)
if recv_type == 2: set_bit(local, 0x02)
if recv_type == 3: set_bit(local, 0x04)
set_bit: byte[+0x1FA] |= mask; update_checksum()
```

`test_bit`/`clear_bit` exist but are dead in this build, so the bits have no
reader here.

### Pause menu

```
obj+0x14 = 0x0816ADD8            # {id,action} pairs
obj+0x18 = selected index
obj+0x1C = count                  # 4 in a normal level, 5 when flag set
action 0 = resume, 1 = restart trial, 2 = warp room, 3 = ?, 4 = music
action 5 = sound (per-item check at 0x080055F4)
```

## 6. Tables

### 6.1 UI text inventory (70 ids, `0x08172C18`)

| Ids | Count | Content |
|---|---:|---|
| 0 | 1 | `level` (generic label) |
| 1–20 | 20 | level names: jungle jam … final countdown |
| 21–25 | 5 | boss names: tiny, dingodile, n. gin, neo cortex, mega-mix |
| 26–32 | 7 | new game, load game, load link game, delete game, save game, quit, exit |
| 33–42 | 10 | save/link dialogs: error saving data, save ok, cancel, complete, empty, delete?, overwrite?, continue?, yes, no |
| 43–47 | 5 | transferring data, error transferring data, b button to abort, push start to continue, start: load-save |
| 48–52 | 5 | music, sound, resume, warp room, restart trial |
| 53–57 | 5 | powers, crystals, gems, relics, time trial |
| 58–63 | 6 | none, credits, super body slam, double jump, tornado spin, turbo run |
| 64–67 | 4 | ability help lines |
| 68–69 | 2 | bonus, pause |

Zero ids contain password/cheat/debug/secret/unlock/options/invalid/sound-test
wording.

### 6.2 Level table (`0x0816C3AC`, 25 × 0x24 bytes)

`word0` = text id, `word1` = world, `words2-4` = timing data, `word7` =
boss flag.

| Record | Text id | Name | Boss |
|---:|---:|---|---:|
| 0–19 | 1–20 | 20 normal levels | 0 |
| 20 | 22 | dingodile | 1 |
| 21 | 23 | n. gin | 1 |
| 22 | 21 | tiny | 1 |
| 23 | 24 | neo cortex | 1 |
| 24 | 25 | mega-mix | 1 |

### 6.3 Save-file action table (`0x0816ACFC`)

`27 load game, 28 load link game, 30 save game, 29 delete game, 32 exit,
54 crystals, 53 powers, 55 gems, 56 relics, 57 time trial`

The renderer at `0x08003A60` loops `r7 = 0..4`, so only the first five are drawn
on this screen; the status ids are for another context.

### 6.4 Pause tables

| Table | Entries |
|---|---|
| `0x0816ADD8` | `{50,0} resume, {48,4} music, {49,5} sound, {51,2} warp room, {52,1} restart trial` |
| `0x0816ADC4` | `{48,4} music, {49,5} sound, {51,2} warp room, {52,1} restart trial` |

Observed in-level object `0x020137B4`: list `0x0816ADD8`, selected 0, count 4 —
so Restart Trial is present in the table but not counted in a normal level.

### 6.5 Unlock bits (`byte[rec+0x1FA]`)

| Bit | Set by | Read by |
|---:|---|---|
| 0x01 | nothing | nothing |
| 0x02 | link receive, partner type 2 (`0x08003654`) | nothing |
| 0x04 | link receive, partner type 3 (`0x08003670`) | nothing |
| 0x08–0x80 | nothing | nothing |

All 256 values are representable; only 0x00, 0x02, 0x04, 0x06 are producible by
the ROM, and none change local behaviour.

## 6b. Enumeration

**Input code space: 0.** There is no alphabet, length, checksum or validator to
enumerate. The enumeration that can be performed is the enumeration of the
interface, the input surface and the one writable flag byte:

1. **Text space** — 84,314 `strings` lines; case-folded whole-image keyword
   census: `password` 0, `passwd` 0, `cheat` 0, `debug` 0, `secret` 0,
   `unlock` 0, `level select` 0, `select level` 0, `options` 0, `invalid` 0,
   `sound test` 0, `gallery` 0, `hidden` 0, `enter code` 0, `input` 0.
   `code` = 1 (GAX banner `Code: B.Wodok`), `warp` = 2 (UI id 51 and the
   `"warp room"` music track name), `bonus` = 2 (music track), `credits` = 2,
   `continue` = 3 (dialog text).
2. **UI id space** — exactly 70 ids (table above), all classified; 25 of them
   are level/boss names consumed by the level table. No id is a password, debug,
   option, level-select or sound-test label.
3. **Menu space** — 3 main items, 5 save-file items (10 in the table),
   4 pause items in-level (5 in the table), 1 link entry. Every menu action is a
   fixed handler; no action opens a text-entry field.
4. **Input space** — one `0x04000130` literal, one latch, 20 latch call sites,
   75 key-state reads, 10 button bits. Scanning the whole image for
   pointer-referenced runs of u16 button masks found **2** candidates
   (`0x084B689C` = four 0x10s; `0x085A077C` = 04/10/20/04) and u8 runs found
   **4**; every one lies in graphics/OAM/palette data. The only code-referenced
   candidate, `0x0816AE20`, is read by the sprite placement routine at
   `0x080074E0` (`ldrb` of per-tile offsets compared against screen
   coordinates), not by input. **0 sequence tables.**
5. **Unlock space** — one byte, 256 values. Writers: record reset
   (`0x08002CC6`, value 0) and `set_bit` (`0x08002D28`, masks 0x02/0x04) called
   from `0x08003654`/`0x08003670` inside the link-receive routine only. Readers:
   none (`test_bit`/`clear_bit` have 0 BL/BLX callers and no function-pointer
   references; a scan for the compiler's `movs #0xFD; lsls #1` materialisation
   of 0x1FA finds only 5 sites, all in `0x08002AF4`–`0x08002D2E`). Therefore no
   unpublished value can be
   minted through the UI, and bits 0x01/0x08–0x80 are aliases with no effect.
   That is the closed-set result for this title.
6. **Bounds by rejection** — (a) the 10-press sequence above left the main menu
   id set and cursor unchanged (transient savestate diff 2,185 IWRAM / 1,522
   EWRAM bytes); (b) the ROM contains no pointer-referenced button table, so no
   shorter sequence can be valid either; (c) selecting the link entry without a
   partner enters the link screen and immediately aborts back to the file menu
   on B, i.e. the transfer cannot complete without a second cartridge; (d) the
   0x1FA bits outside 0x02/0x04 have no producer and no consumer.

## 7. Validation evidence

| Claim | Type | Evidence |
|---|---|---|
| Stock retail USA image, no trainer/cracktro | Observed | entry `0xEA00002E`; single logo at 0x4; no cracktro strings; `ACQE` |
| Header checksum zeroed, complement valid | Observed | computed complement 0x4B = stored; stored header checksum 0x0000 |
| Only one KEYINPUT reader | Derived | one u32 literal `0x04000130` at `0x080007D0`; latch `0x080007AC` |
| Key latch semantics | Observed + Derived | `~KEYINPUT` at `0x030007E0`; pressing Return gave `0xFC00`→`0xFC08`, Down `0xFC80`, A `0xFC01` |
| Title draws no text id | Observed | no text-routine hit for ~10 s; first ids appear after Start |
| Main menu ids 26,27,59; 3 items; cursor wraps | Observed | text stream; `[0x0200344C]` took 0→1→2→0 |
| Save-file menu ids 27,28,30,29,32 | Observed | text stream after B on the slot dialog (twice) |
| Link entry exists and B aborts | Observed | id 28 drawn; selecting it cleared text ids; B restored the 5-item menu |
| Pause ids 48,49,51,54,50; count 4 | Observed | text stream; object `0x020137B4` list `0x0816ADD8`, selected 0, count 4 |
| Pause table/actions and count flag | Derived | `0x0816ADD8`, `0x08004FB2`, jump table `0x08005508` |
| Credits screen exists, non-text renderer | Observed | main-menu index 2 + A changed screen; no text ids |
| Level table 25 entries | Derived | `0x0816C3AC`, stride 0x24, word0 = text id; renderer `0x0801C560` |
| Save record layout + checksum | Derived | `0x08002B44` (127-word sum), `0x08002C14/40/6C/84` |
| Unlock bits 0x02/0x04 set only by link | Derived | two BL callers of `0x08002D28`; handshake at `0x08002A64` |
| Unlock byte has no local reader | Derived | only 5 instruction sites mention 0x1FA; `test_bit`/`clear_bit` uncalled; no pointer refs |
| No password/cheat/debug text | Observed | whole-image case-folded keyword counts above |
| No button-sequence table | Derived | pointer-referenced u16/u8 mask-run scan: 2+4 candidates, all graphics; sole code-referenced one is a sprite table |
| Sequence rejected | Observed | menu unchanged; transient EWRAM/IWRAM diff only |
| No in-game codes published | Observed (web) | 3rd party cheat index cheats page lists only unlockables (extra level at 100%, Turbo Run) |

## 8. Unknowns

* The 112-byte slot payload is only partially mapped (level/progress/gem/relic
  flags are inside it); the exact bit for the 101% extra level and for the
  post-completion Turbo Run was not decoded. Both are progress unlocks, not
  codes.
* The link screen draws no id from the 70-entry table, so its "transferring
  data"/"error" wording (ids 43–46) was not observed on screen in this session;
  those ids exist and are referenced at `0x0800335A`/`0x0800360A`/`0x08003686`.
  With a second cartridge the transfer would exercise them.
* What a partner game does with bits 0x02/0x04 is outside this ROM (the sibling
  report documents the N-Tranced side).
* The credits renderer path is not addressed; only its reachability is proven.

## 9. Tooling

* Python 3 (`struct`, `zlib`, `hashlib`, regex) for header/hash/pointer/table
  analysis, text-id decoding, keyword census and mask-run scans.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`
  for code reads.
* mGBA 0.10.5 SDL CLI debugger on `Xvfb :266` (no screenshots): `frame`,
  `b/t`, `x/4`, `r/2`, `save`/`load`, `status`, `lb`.
* Savestate decoding: mGBA `.ssN` is a PNG with a zlib `gbAs` chunk; the raw
  state is 397,312 bytes (IWRAM at 0x19000, EWRAM at 0x21000), used for the
  before/after diff.
* Local scripts kept in `/tmp/crashhuge`: `rsp.py`, `drv.py`,
  `dbg.py`, `ids.py`, `pad.py`, `restart.sh`.

## 10. Notes

* No ROM, graphics, music or text assets are redistributed; only hashes,
  addresses and short UI identifiers are published.
* The save file dumped during the session did not contain a valid record
  (slot flags 0, magic bytes not `0x43`/`0x12`, checksum 0x45140202 vs stored
  0x43120000), which matches the in-game "empty" slot. It is a generated
  artifact and was removed.
