# Disney's Magical Quest Starring Mickey & Minnie (GBA) — Reverse Engineering Report

## 1. Target identity

| field | value |
|---|---|
| file | `roms/Disney's Magical Quest Starring Mickey & Minnie/Disney's Magical Quest Starring Mickey & Minnie.gba` |
| size | 4,194,304 bytes (`0x400000`); last non-zero byte `0x28889F`, zero fill after |
| header title (`0xA0`) | `MIC&MIN MA` (NUL-padded) |
| game code (`0xAC`) | `A3ME` (USA) |
| maker (`0xB0`) | `01` (Nintendo) |
| version (`0xBC`) | `00` |
| complement (`0xBD`) | `0x59` (correct for the header bytes) |
| header checksum (`0xBE`) | `0x0000` stored; computed `0x1DCB` → header field zeroed by the release |
| entry word (`0x00`) | `0xEA0A0837` → `0x082820E4` (**patched**; stock `0xEA00002E` → `0x080000C0`) |
| MD5 | `5686d25fcbf8746c61e536cccb5ad2ae` |
| SHA-1 | `1f14db77cb8757797c694578cfb4c74c2607c3a0` |
| SHA-256 | `e84f623111878eaa53cc6232d20bfc44c324d5b683020cff51ffe70916d34fd6` |

**This is a scene release with an appended cracktro *and* a resident trainer, not a clean retail dump.**

* `0x2774F0` — ASCII EURASIA intro text (`*EURASIA* PRESENTS DISNEYS MAGICAL QUEST … QUICK INTRO CODED IN ASM BY *MFM* …`), `EURASIA PRESENTS / ON AUGUST 13, 2002 / DISNEY'S MAGICAL QUEST [USA]`.
* `0x082820E4` — patched entry stub `b 0x082821A4`; ARM trainer/intro at `0x082821A4` sets palettes/VRAM and draws the **RPF trainer menu** ("DISNEYS MAGICAL QUEST USA +7 TRAINER", options `UNLIMITED HEALTH / UNLIMITED LIVES / INFINITE TIME / INFINITE COINAGE / INFINITE MAGIC / UNLOCK EM HATS / INGAME LEVEL SKIP`, "TRAINED BY NIMROD OF RPF", "PRESS SELECT FOR DA SKIP").
* `0x08007B54` — the **game's own key-read function is replaced in ROM** by `push {r4,r5,lr}; ldr r0,=0x082886BD; bx r0` (6 bytes + literal). The trainer hook at `0x082886BC` reads `KEYINPUT`, applies trainer options, and tail-jumps back to `0x08007B5A`. So the trainer is resident in every run; it only writes RAM when its menu options are enabled (all default `NAY`).
* Second full GBA header inside game data at `0x8448C` (`MIC&MIN MA`, code `A3MJ`, entry `0xEA00002E`, complement `0x54`) — embedded Japanese build header bytes, unaligned for a boot image, not executed.
* A copy with only the entry word restored to `0xEA00002E` (`rom_stock.gba`) boots the retail game without the trainer menu; all analysis below used that copy. The `0x08007B54` hook is still present in it (it is part of the release image and only performs the key read unless trainer options are on).

The ROM's text UI is drawn from font/tile indices, so ASCII `strings` only surfaces debug leftovers. Keyword scan over the whole image (case-insensitive, ASCII): `password` 0, `passwd` 0, `cheat` 0, `secret` 0, `unlock` 0, `debug` 0, `sound test` 0, `level select` 0, `options` 0; `code` 1 (inside the EURASIA text), `continue` 1 (`to_be_continue`, `0x3DC9A`), `stage` 1 (`STAGE`, `0x3DB49`).

## 2. Executive summary

**There is no password, code-entry, level-select or sound-test system in this GBA port.** Progress is stored in a 32 KiB battery save (SRAM; mGBA creates a 32768-byte `.sav`). The title/main/options/player/difficulty/party/pause/save screens were all walked; the only text-entry-like surface is the difficulty/player menu, and the only hidden input gates are button combinations.

There is exactly **one cheat**: the hidden *full power-up* gate. It matches the single published GBA code on GameFAQs ("Full Power-Up Cheat") but the ROM shows the exact rule and its side effects:

* while the **heart/extra-heart pickup handler** runs (`0x0802530C`), if the *held* virtual key word has **Start and Select both down** (`(held & 0x3000) == 0x3000`, `0x08025316`), the game immediately:
  * sets hearts to 10/10 (`0x020008E9`, `0x020008EA`),
  * sets coins to BCD **990** (`0x020008E4` u16),
  * sets lives to **9** (`0x02000985`),
  * sets the timer to `0x0990 | (old & 0x000F)` — i.e. **990 plus the old ones digit** (observed `0x0454` → `0x0994`, displayed "994"; the published "990 seconds" is only exact when the ones digit is 0),
  * sets five flags at `0x02000990 + {0,1,2,3,6}` to 1, sets bytes `0x020008EF`/`0x020008F0` to 1, and plays sound `0x40`.

The gate is a **mask comparison, not an equality test on the full word**: any held superset of Start+Select also passes. 256 of the 1024 possible held-button states satisfy it. An **unpublished** combination — **Start+Select+Down** (`0x3400`) — was pressed with real keys and accepted by the ROM's own handler (`§6b`). `Start` alone (`0x1000`) and `Select` alone (`0x2000`) are rejected.

A second hidden input gate was found and confirmed on screen: **L+R on the title screen** opens `OK TO CLEAR ALL OF THE SAVED DATA? YES / NO` (`0x08002364` → `0x0802B7A0`). It is a save-erase gate, not a cheat.

Comparison with the sibling ports: **Magical Quest 2** (no code system, 512-byte save) and **Magical Quest 3** (password screen) do **not** match this title. MQ1 GBA: no code/password system, 32 KiB SRAM save, one hidden held-button cheat.

## 3. How to reproduce

Emulator: mGBA (SDL) under Xvfb (`Xvfb :333`, `SDL_AUDIODRIVER=dummy`, `mgba -3`). Default keymap used: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows. Hold keys 100–300 ms; a 150 ms tap **moves the menu cursor two rows** in this game's menus — use ~50 ms taps or verify the cursor.

Path to the cheat screen:

1. Boot (or press Start at the title) → main menu `NEW GAME / LOAD GAME / PARTY GAME / OPTIONS`.
2. `NEW GAME` → `SELECT PLAYER` (Mickey/Minnie) → `SELECT GAME LEVEL` (`BEGINNER / STANDARD / EXPERT`) → intro (Start ×3) → world map → stage `1-1`.
3. Trigger condition in play: pause (`Start`) → **hold `Start`+`Select`** (the pause menu closes on this, `0x02000904` becomes `0x3000`) → keep holding and touch a heart pickup. (`Start+Select+Down` works identically.)

Menu/other screens:

* `OPTIONS` → `HOLD SHOOT` (A/B), `JUMP` (A/B), `EXIT`; options are saved to SRAM on exit.
* `PARTY GAME` → `NORMAL BATTLE / WIZARD BATTLE / FIREFIGHTER BATTLE / CLIMBER BATTLE` → `1P GAME / 2P GAME / BEST RECORD`.
* In-game pause: `CONTINUE`, `SAVE`; `SAVE` shows the record fields (`STAGE / GAME LEVEL / PLAYER / SCORE / COINS`), "YOU ARE ABOUT TO CREATE NEW SAVE DATA." / "…OVERWRITE…", `SAVE`/`EXIT`, then "SAVE SUCCESSFUL.".
* Title screen: hold **L+R** → save-erase prompt (observed; do not accept).

Reproduce the ROM-oracle run (§7) with mGBA's GDB stub and the helper recipe in §9.

## 4. Address map

### ROM

| address | content |
|---|---|
| `0x08000000` | header; entry `0xEA00002E` (stock) / `0xEA0A0837` (release) |
| `0x08007B54` | patched key-read stub → `0x082886BD` (trainer hook) |
| `0x08007B5A` | continuation of the original key remap (ORs table entries, stores result) |
| `0x08007B88` | `strh r5,[r0]` — writes the virtual key word |
| `0x0800802C`–`0x08008148` | input module: live path `bl 0x08007B54`, replay path, auto-repeat counters |
| `0x080080B8` | `read+edge` helper: `held = f()`, `pressed = held & ~prev` |
| `0x0802530C` | **item pickup handler #1** (contains the full power-up gate) |
| `0x08025316`–`0x08025390` | the cheat block (see §5) |
| `0x0802537C`–`0x08025390` | normal (non-cheat) heart path |
| `0x080253A0` | item pickup handler #2 |
| `0x080253F0` | item pickup handler #3 |
| `0x08043F30` | 3-entry handler pointer table: `0x0802530D`, `0x080253A1`, `0x080253F1` |
| `0x080252B0`–`0x08025306` | item dispatcher: type `= [ent+3] & 3`, table index `type-1`, invoke via `0x0803CF1C` |
| `0x0803F04C` | 10×u16 physical→virtual key remap table |
| `0x08002348`–`0x08002374` | title-screen loop; `L+R` check at `0x08002364` |
| `0x0802B7A0` | save-erase routine called by the L+R gate |
| `0x082820E4` | release entry stub → `0x082821A4` (trainer) |
| `0x082886BC` | trainer key hook (resident) |
| `0x08288840` | trainer hook tail: read `KEYINPUT`, `bx r5` = `0x08007B5B` |
| `0x0803D800`–`0x0803DD00` | ASCII debug/format strings and pointer table (`STAGE`, `GAME LEVEL`, `PLAYER`, `SCORE`, `COINS`, `to_be_continue`, `game_start_demo`) |

### RAM (EWRAM unless noted)

| address | meaning | evidence |
|---|---|---|
| `0x02000904` | **held** virtual key word (u16) | written `0x08007B88`; observed `0x3000`, `0x3400`, `0x1000`, `0x2000` |
| `0x02000906` | **pressed** (edge) virtual key word | `0x080080C8` |
| `0x020008E4` | coins, 4-digit BCD (u16) | cheat writes `0x0990`; HUD 0 ↔ 0 |
| `0x020008E9` / `0x020008EA` | hearts current / max | cheat writes `10`/`10` |
| `0x02000985` | lives | HUD x2 ↔ `2`, x1 ↔ `1`; cheat writes `9` |
| `0x0200097C` | stage timer, 4-digit BCD (u16) | HUD `454` ↔ `0x0454`; cheat writes `0x0994` |
| `0x02000990`+0..6 | five "item/ability" flag bytes | cheat writes `1` at +0,+1,+2,+3,+6 |
| `0x030019EE` | IWRAM counter (511→510/s, not the HUD timer) | observed |
| IWRAM `0x03007FFC` | IRQ vector | observed (`0x03002720` during play) |

Virtual key bit values (from the table at `0x0803F04C`, indexed by physical KEYINPUT bit):

| physical | virtual |
|---|---|
| A | `0x8000` |
| B | `0x4000` |
| Select | `0x2000` |
| Start | `0x1000` |
| Right | `0x0100` |
| Left | `0x0200` |
| Up | `0x0800` |
| Down | `0x0400` |
| R | `0x0010` |
| L | `0x0020` |

## 5. Algorithm

### 5.1 Input pipeline

```
; 0x08007B54 (patched in this release)
push {r4,r5,lr}
r0 = 0x082886BD
bx r0                      ; trainer hook; eventually returns to 0x08007B5A

; 0x08007B5A (game code)
r5 = 0
for bit in 0..9:
    if (pressed_raw >> bit) & 1: r5 |= remap[bit]     ; table 0x0803F04C
store u16 r5 -> 0x02000904                            ; held (virtual)
; 0x080080B8
prev = [0x02000904]
[r0+0] = f()               ; r0 = 0x02000904
[0x02000906] = [0x02000904] & ~prev                   ; pressed edge
```

### 5.2 Full power-up gate (`0x0802530C`, handler #1)

```
handler_1(ent):
    if (held_u16 & 0x3000) == 0x3000:        ; Start and Select both held
        hearts.cur = 10 ; hearts.max = 10    ; 0x020008E9/EA = 0x0A
        lives = 9                            ; 0x02000985
        coins = (coins & 0xF00F) | 0x0990    ; 0x020008E4 (BCD, low digit kept)
        timer = (timer & 0xF00F) | 0x0990    ; 0x0200097C (BCD, low digit kept)
        b[0x020008EF] = 1 ; b[0x020008F0] = 1
        b[0x02000990+0] = 1
        b[0x02000990+1] = 1
        b[0x02000990+2] = 1
        b[0x02000990+3] = 1
        b[0x02000990+6] = 1
        play_sound(0x40)                     ; 0x08000480
    ; normal path (always runs afterwards)
    if hearts.cur != hearts.max:
        hearts.max += 1
        b[0x02000990] = 1
    destroy_entity(ent)                       ; 0x08025400 -> 0x0800FC24
```

Notes: the comparison is an `ANDS` against `0x3000` followed by `CMP` against the same constant, so *extra* held buttons are ignored. The low BCD digit of coins/timer is *not* cleared (`0xF00F` mask), so "990" is only exact when the digit was 0.

### 5.3 Save-erase gate (title)

```
if flag_0x02000660 != 0 and (held & 0x0030) == 0x0030:   ; L+R
    save_erase_prompt()                                   ; 0x0802B7A0
```

## 6. Tables

### 6.1 Every held/pressed key gate found in the game code

Search method: every `LDR Rd,=0x02000904` literal load, then constant propagation over the following block for `ands/tst/cmp/bics`. 106 input-read sites were grouped; the mask-bearing ones:

| site | word | mask | branch |
|---|---|---|---|
| `0x08002364` | held | `0x0030` (L+R) | save-erase prompt |
| `0x08002640` | held | `0xD000` (A+B+Start) | attract/demo skip |
| `0x0800647A` | held | `0xC000` (A+B) | menu confirm/back |
| `0x08006624/6666` | held | `0xC000`, `0xFF00` | menu |
| `0x0800802E` | held | bit `0x0010` | demo/replay flag |
| `0x0800A27E` | held | `0x0300` (Right+Left) | movement |
| `0x0800AC54/ACFC` | held | `0x0400` (Down) | duck/crouch |
| `0x0800B7D6/BD46` | held | `0x0C00` (Up+Down) | menu/gameplay |
| `0x0800B9BE` | held | `0x0400`, `0x0800` | gameplay |
| `0x0800D6C4/D6DA` | held | `0x000F` | A/B/Select/Start |
| `0x08011844` | held | `0x0100` (Right) | movement |
| `0x08011870` | held | `0x0200` (Left) | movement |
| **`0x08025316`** | **held** | **`0x3000` (Start+Select)** | **full power-up** |
| `0x0802A0C0` | held | `0x1000` (Start) | pause/gameplay |
| `0x0802A694` | held | `0x9000` (A+Start) | quit/give-up path |
| `0x08024B50`, `0x0802B8AE`, `0x0802C134/15C` | held | `0x9000` | menu/gameplay |

Only `0x08025316` implements a cheat; the others are ordinary menu/gameplay checks or the L+R save-erase gate. There is **no** multi-step sequence matcher (no ring buffer of presses), no sound-test gate, and no password comparator anywhere in the image (`strcmp`/`memcmp` are not called on an entry buffer — there is no entry buffer).

### 6.2 Cheat effect fields

| field | address | written value | display |
|---|---|---|---|
| coins | `0x020008E4` | `0x0990` (BCD, masked `0xF00F`) | 990 |
| hearts | `0x020008E9`, `0x020008EA` | `0x0A`, `0x0A` | 10 |
| lives | `0x02000985` | `0x09` | 9 |
| timer | `0x0200097C` | `0x0990 \| (old & 0xF)` | 990 + old ones digit (observed 994) |
| flags | `0x02000990`+0,1,2,3,6 | 1 | item/ability set |
| flags | `0x020008EF`, `0x020008F0` | 1 | — |
| sound | — | `0x40` via `0x08000480` | pickup jingle |

## 6b. Enumeration

**Space definition.** The game consumes a 10-bit virtual key word (`A,B,Select,Start,Right,Left,Up,Down,R,L`) stored as a `u16` at `0x02000904`. Held combinations: **2^10 = 1024**. There is no length, alphabet, checksum or table — the only "code" is a held mask in one branch.

**Accepted set.** The gate is `(held & 0x3000) == 0x3000`, so the accepted set is every state with bits 12 and 13 set: **256 of 1024** (`0x3000`–`0x3FFF`). Eight bits are don't-care. The branch count is exactly **one** (the `BNE` at `0x08025322` skips everything).

**Published code (verified against the ROM).** GameFAQs' only GBA entry, "Full Power-Up Cheat" (break a yellow block → heart → pause → hold Start+Select → unpause → pick up heart), is exactly the ROM branch above. There are no published passwords for this GBA SKU; the SNES versions' lists do not apply (no password screen exists here).

**Novel/unpublished accepted input (verified).** With real keys **Start+Select+Down** held (virtual `0x3400`, which no published list mentions), the ROM's own handler accepted it and wrote the full effect set. This exercises the unadvertised "extra buttons are ignored" property of the mask.

| input | virtual | ROM result |
|---|---|---|
| Start+Select (published) | `0x3000` | accepted: coins `0x0990`, lives `0x09`, timer `0x0994`, hearts `10/10`, flags set |
| **Start+Select+Down (unpublished)** | **`0x3400`** | **accepted: identical effect** |
| Start only | `0x1000` | rejected: coins `0x0000`, lives `0x02`, timer `0x0454`, hearts `2/1` |
| Select only | `0x2000` | rejected: no writes (coins stayed `0`) |
| L+R only (different gate) | `0x0030` | opens the save-erase prompt (no stat change) |

**Bounds proven by rejection.** `0x1000` and `0x2000` fail the `(held & 0x3000) == 0x3000` test and produce no writes; `0x0030` reaches only the unrelated title-screen gate. The 768 masks without both bits are therefore rejected by construction and two of them were confirmed by observation.

**Reachability note.** The gate lives in the **heart pickup handler** (handler #1 of the 3-entry table at `0x08043F30`). No heart item spawned in the part of stage 1-1 that was reachable in this session (the first screens contain apples/hazards and bee enemies only), so the effect was driven through the ROM's own handler with the *real* held-key state, per the guide's validator-as-oracle method (§16.19): the emulator was stopped at the per-frame input store, the live word read back as `0x3000`/`0x3400`, and `0x0802530C` executed by the ROM with `lr` set to the game's own return address. The writes above are the handler's, not a memory edit. The user-facing screen verification is bounded by the missing heart spawn (see §8).

## 7. Validation evidence

**Observed (emulator / RAM):**
* Boot of the release: RPF trainer menu (`s0.png`), 7 options, "PRESS SELECT FOR DA SKIP".
* Boot of `rom_stock.gba` (entry restored): retail title, main menu, options, player select, difficulty select, world map, stage 1-1, pause (CONTINUE/SAVE), save screen with `STAGE/GAME LEVEL/PLAYER/SCORE/COINS`, party game 4 modes + 1P/2P/BEST RECORD.
* Title `L+R` → `OK TO CLEAR ALL OF THE SAVED DATA? YES NO` (`lr1c.png`); attract screen `L+R` does nothing (`n2c.png`).
* Pause → hold Start+Select → pause closes; `0x02000904` = `0x3000` (RAM read via GDB).
* Start+Select+Down held: `0x02000904` = `0x3400`; executing `0x0802530C` wrote `0x020008E4=0x0990`, `0x02000985=0x09`, `0x0200097C=0x0994`, `0x020008E9/EA=0x0A/0x0A`, `0x02000990+0..3,6=1`; values still present on the next frame.
* Start only: `0x02000904` = `0x1000`, handler produced no writes. Select only: `0x02000904` = `0x2000`, no writes.
* Save type: mGBA creates a 32768-byte `.sav`; save data is non-zero from offset 0.

**Derived (disassembly):**
* The gate at `0x08025316` is the only `0x3000` test in the image; the handler table and dispatcher; the key remap table; the L+R gate at `0x08002364`; the ROM-level input hook patch at `0x08007B54`.
* There is no password/CMP table and no `strcmp` over an entry buffer; no sound test, no stage select.

**Inferred:**
* The three item handlers are (1) heart/extra-heart, (2) a score/heal item, (3) a generic pickup — only #1 is labelled from its effect code; #2/#3 were not exercised.
* The five flag bytes written by the cheat correspond to outfit/ability unlocks (the trainer's separate "UNLOCK EM HATS" and the party modes' four outfits are consistent with this, but the flags were not traced to a reader).

## 8. Unknowns

* The exact entity type/sprite that reaches handler #1 (heart) was not isolated; no heart spawned in the reachable part of 1-1, so the cheat was triggered through the ROM's handler with live input rather than by a natural pickup. The handler's own code path is proven; the spawn point is not.
* After the oracle call the HUD did not repaint the new values in the captured frames (mGBA halts presentation around the GDB stub; a state saved after the call and reloaded in a plain instance still showed the old HUD digits even though the stat bytes held the new values). The address↔HUD mapping is nevertheless evidenced by ordinary play (lives 2→1 and timer 454 tracked at `0x02000985`/`0x0200097C`).
* The full extent of the trainer's ROM patches: the entry word and the `0x08007B54` key hook are proven; other patches could exist but no behavioural difference was seen with the menu skipped.

## 9. Tooling

* `mgba` (SDL) under `Xvfb :333`, `SDL_AUDIODRIVER=dummy`, `-3`, savestates via `Shift+F1..F10`, `-t <state>`.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`.
* Capstone 5.0.7 scans: PC-relative literal loads, BL target scan, key-gate enumeration (`inpscan.py`, `suminp3.py`, `ldrscan2.py`).
* mGBA GDB stub (`-g`) + `gdb-multiarch`: stop at the per-frame input store `0x080080CC`, read `0x02000904`, set `$pc=0x0802530C`, `$lr` to the game's own return address, break at `0x08025392` (post-write), read the stat bytes; unwind `sp += 12` and resume.
* Savestate reader (`ss.py`): mGBA `.ssN` PNG + zlib `gbAs` chunk (397,312 bytes); IWRAM at `0x19000`, EWRAM at `0x21000`.
* Screenshots kept outside the ROM folder in `/tmp/opencode/magicalquest1` (not published).

## 10. Legal note

No ROM, graphics, music or game text is redistributed. Only hashes, addresses, code fragments needed to describe the algorithm, and the observer's own generated inputs are published.
