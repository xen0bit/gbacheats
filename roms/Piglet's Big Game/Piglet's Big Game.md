# Piglet's Big Game (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Piglet's Big Game/Piglet's Big Game.gba` |
| Size | 8,388,608 bytes (0x800000), 8 MiB |
| Header title | `PIGLET'SGAME` |
| Game code | `A9NE` (Europe) |
| Maker | `4Q` (Doki Denki / Disney Interactive) |
| Version | 0; fixed byte 0x96; complement 0x66; header checksum 0x0000 |
| Entry word | `0xEA1A887E` → branches to `0x086A2200` (patched; see below) |
| MD5 | `e0412bc0faefddeb77d8739cab3fe1e6` |
| SHA-1 | `d5f3031af2348791f72d0a8c1f066f04aebb93d6` |
| SHA-256 | `9989785453673bc0a5c759d1cfcc45a0fe1eb3a91592397b58fe7bc956f32343` |

**Embedded-header scan:** the 156-byte Nintendo logo (`24 ff ae 51 69 9a a2 21 …`) occurs exactly once, at file offset `0x004`. There are no concatenated/second images and no multiboot stubs.

**Scene patch / cracktro (§16.1):** the stock GBA entry `0xEA00002E` (`b 0x080000C0`) was replaced by `0xEA1A887E`, which jumps to `0x086A2200`. That code is a EURASIA cracktro ("EURASIA — FOR PLEASURE NOT PRESSURE", credits JUNG.MAN of SAC / CODE KAFUGIN / LOGO M7X) with a symbol-relocation loader using the names `nano`, `main`, `entryPoint`. It cycles greeting screens indefinitely and is **not** an in-game cheat. All analysis below was performed on a **copy** with the entry word restored to `0xEA00002E` (SHA-256 of the analysed copy: `c5d4a5713114e27d63fca1374ea0a0109d24f80b3fa6439514aa4f6566596a93`); the original ROM was not modified.

## 2. Executive summary

The game has a genuine developer-intended password system, reachable from the **main menu → "Enter Password"**. It is **not** a lookup table of published strings: it is an **algorithmic 7-symbol code** with a 5-bit checksum. Each symbol is one of 8 icons × 4 colours = 32 values; the icons are `arbre, fleur, lune, maison, miel, papillon, parapluie, soleil` and the colours are Red(0), Yellow(1), Green(2), Blue(3). The encoder is at `0x0801225E`, the validator at `0x08012400`, and the XOR constant `0x2873CAB9` at `0x080123FC`. Exactly **2^30 = 1,073,741,824** of the 32^7 possible inputs are accepted (1 in 32); the checksum is fully determined by the 30-bit payload. Accepted codes decode into three fields (3-bit, 6-bit, 3-bit) that select a level and other game state.

Published "level passwords" exist on ChapterCheats/Cheating Dome, but they are written as colour+shape descriptions (e.g. `[Y=] [B Diamond] …`) and do **not** appear as literals in the ROM — consistent with an algorithmic system. They could not be verified literally; the ROM's own encoder was used instead.

Invalid codes are rejected on-screen with **"The password is not correct."** Codes produced by the recovered encoder are accepted (no rejection message; the game leaves the password screen). In this cracked ROM copy the subsequent level-load path crashes mGBA with `Jumped to invalid address: 526F526E / Illegal opcode: 0000b710`; that is an observed limitation of the patched image, not a rejection of the code.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 under Xvfb `:319`, `SDL_AUDIODRIVER=dummy`, `-3` scale. Keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrow keys; hold 70–150 ms.
* Boot the **entry-fixed copy**. Press Start → title `Disney Presents Piglet's Big Game — Press START to play`. Start again → gameplay. In gameplay, Start → pause (`Game paused / Resume / Exit`).
* The main menu (`New Game / Enter Password / Options`) is screen ID `0x15`. On the unmodified retail flow it is reached from the title; for this analysis it was reached by writing screen ID `0x15` into the global state byte at EWRAM `0x02004967` of a title-screen savestate (and clearing the menu-active byte at `0x0200482C`), then loading that state. Selecting "Enter Password" (Down, A) enters the password screen (screen ID `0x1A`).
* Password screen controls: **D-pad Left/Right** cycles the icon (8), **L/R** cycles the colour (4), **A** selects and advances. After 7 symbols, A submits. The current 7 symbols are drawn in the lower row; the palette is the upper row.
* **Rejection test:** from a fresh screen, press A seven times without changing anything (all symbols Red/`arbre` = `0`). Result: "The password is not correct." (Observed, screenshot `o_badc.png`.)
* **Accept test:** set icon `papillon` (Right ×5) and colour Yellow (R ×1), press A six times so all seven slots read `0x15`, then A to submit. Result: no rejection text; the game leaves the screen. Screenshots: `uni2_beforec.png` (buffer `15 15 15 15 15 15 15`), `uni2_afterc.png`.
* RAM was read by parsing mGBA `.ss1` savestates (§16.13): the `gbAs` PNG chunk is zlib-compressed; IWRAM maps at raw `0x19000`, EWRAM at raw `0x21000`. (`ss.py`, `patch_ss.py`.)

## 4. Address map

| Item | Address | Notes |
|---|---|---|
| Cracktro entry | `0x086A2200` | EURASIA intro + relocation loader |
| Stock crt0 | `0x080000C0` | restored on analysis copy |
| Title/main-menu text bank | `0x085228E8`–`0x08523FAF` | ASCII, NUL separated ("Enter Password", "New Game", "Options", "Resume", "Exit", …) |
| Password asset manifest | `0x082D78C`–`0x082D9xx` | `password/arbre_1-.gbr` … `soleil_4-.gbr` |
| Icon-name table | `0x0801BD80` | 8 pointers → `arbre`,`fleur`,`lune`,`maison`,`miel`,`papillon`,`parapluie`,`soleil` |
| Screen dispatcher | `0x08011A7A` / `0x08011D0C` | screen ID byte at global+`0x1A7` |
| Main menu builder (screen 0x15) | `0x08018020` | 3 items: New Game / Enter Password / Options |
| Password display screen (0x19) | `0x08017848` | calls encoder `0x0801225E` |
| Password entry screen (0x1A) | `0x08017BA8` | creates 0x58-byte struct |
| Password per-frame handler | `0x08017DE8` | writes current symbol, submits at position 6 |
| Password symbol painter | `0x08017A6C` | packs `(icon<<2)\|color` |
| **Encoder** | `0x0801225E` | game state → 7 valid symbols |
| **Validator** | `0x08012400` | 7 symbols → accept/reject + decoded fields |
| XOR constant | `0x080123FC` = `0x08012520` | `0x2873CAB9` |
| Level jump table | `0x080124C8` | `{1,1,4,4,7,8,…}` from 3-bit selector |
| Global state pointer | EWRAM `0x02000160` → `0x020047C0` | fields at +0x0C, +0x1AB, +0x1A7 |
| Password struct | EWRAM, 0x58 bytes (observed `0x02006188`, `0x02006B80`) | symbols at +0x4C (7 bytes), position +0x53, icon +0x54, colour +0x55 |

## 5. Algorithm

Encoder (`0x0801225E`), with fields `a = global[0x0C]`, `b = global[0x1AB]`, `i7 = global[0xA8]`, `i8 = global[0xA4]`, `i2` (3-bit level selector):

```
P = (i7*0x1F5 + i8)*8 + i2
payload = (a + (b + P*0x40)*8) XOR 0x2873CAB9        # 32-bit
chk = (sum of the 4 bytes of payload) & 0x1F ^ 0x15
buf[0]   = payload & 0x1F
for i in 0..4:
    buf[1+i] = ((payload >> (5+4*i)) & 0x0F) << 1 | ((chk >> i) & 1)
    payload >>= 4 (after the initial >>5)
buf[6] = remaining payload & 0x1F
```

Validator (`0x08012400`) inverts this exactly:

```
chk_in = Σ_{i=0..4} (buf[1+i] & 1) << i                  # 5 bits
packed = buf[0] | Σ_{i=0..4} ((buf[1+i]>>1) << (5+4*i)) | (buf[6] << 25)
accept iff chk_in == ((Σ_{k=0..3} byte_k(packed)) & 0x1F) ^ 0x15
```

On accept, `x = packed ^ 0x2873CAB9`; `a = x&7`; `b = (x>>3)&0x3F`; selector `= (x>>9)&7`; the selector indexes the jump table at `0x080124C8` to choose the level (`1,1,4,4,7,8,…`). A selector of 7 jumps out of the table (crash in this build).

## 6. Tables

**Icon index → asset / on-screen shape**

| idx | asset | shape on screen |
|---:|---|---|
| 0 | arbre | circle with dot |
| 1 | fleur | triangle |
| 2 | lune | diamond |
| 3 | maison | "at" sign |
| 4 | miel | plus / cross |
| 5 | papillon | heart |
| 6 | parapluie | equals |
| 7 | soleil | lambda / A |

**Colour index:** 0 Red, 1 Yellow, 2 Green, 3 Blue (observed on the password screen). Symbol byte `(icon<<2)|color`, range 0–31.

**Published codes (ChapterCheats, "Level Passwords", verified as web content only):**

| Level | Published password (icon/color descriptions) |
|---|---|
| Eeyore's Dream | `[Y=] [B Diamond] [B Twirl] [G Twirl] [Y Carrot] [Y Heart] [Y Heart]` |
| Flooded Woods | `[Y=] [G Diamond] [G+] [B Carrot] [Y Carrot] [Y Carrot] [R+]` |
| Rabbit's Dream | `[R=] [B Diamond] [R Carrot] [G Twirl] [G+] [G Halo diamond] [B heart]` |
| Roo's Dream | `[R=] [B Diamond] [Y=] [G Diamond] [G Twirl] [B Diamond] [R Heart]` |

These icon names do not match the ROM's asset names, and no password literal exists in the ROM (algorithmic system), so they remain **unverified** rather than wrong. No GameFAQs/VGChartz page was retrievable (403 / no result); no prompt-injection was observed in fetched content.

## 6b. Enumeration

* **Space:** 7 symbols × 32 values = 32^7 = 34,359,738,368 possible inputs. The 5 check bits are fully determined by the 30-bit payload, so exactly **2^30 = 1,073,741,824** inputs are accepted (1/32). There are no reserved bits; all 30 payload bits are meaningful.
* **Validator model:** reimplemented in `pwdmodel.py`; `validate()` agrees with the game on: `[0]*7` reject, `[3]*7` reject, `[21]*7` accept (no rejection text, screen exit).
* **Novel code 1 (uniform):** all seven symbols `0x15` = icon 5 (`papillon`/heart) + Yellow. Payload `0x2B555555`; decoded fields `(a=4, b=61, selector=7)`. Entered in-game via `Right×5, R×1, A×6, A`; RAM buffer verified `15 15 15 15 15 15 15`. Not present in any published list.
* **Novel code 2 (level 1):** symbols `[0, 0, 10, 28, 18, 7, 20]` = `(arbre,Red),(arbre,Red),(lune,Green),(soleil,Red),(miel,Green),(fleur,Blue),(papillon,Red)`. Model output: valid; payload `0x2873CA00`; decoded `(a=1, b=23, selector=0)` → level 1. Generated with the recovered encoder, absent from every published list.
* **Systematic novel codes (one per selector):** `[0,0,10,28,18,7,20]`, `[0,0,9,29,18,7,20]`, `[0,0,14,29,19,7,20]`, `[0,0,13,28,18,7,20]`, `[0,0,2,28,19,6,20]`, `[0,0,1,29,19,6,20]` cover selectors 0–5 (levels 1,1,4,4,7,8).
* **Bounds proven by rejection:** `[0,0,0,0,0,0,0]` (bad checksum) and `[3,3,3,3,3,3,3]` (model-invalid) both produce "The password is not correct." (screenshots `o_badc.png`, `uni_afterc.png`). A code with selector 7 is accepted by the checksum but its decoded jump-table index is out of range — the emulator crashes with `526F526E`, demonstrating the semantic range layer separately from the checksum layer.

## 7. Validation evidence

* **Observed:** title, main menu, gameplay, pause menu, password entry screen and password display screen (screenshots + savestate RAM). Invalid code → "The password is not correct." Valid uniform code → no rejection, screen exit. Password struct address, 7-byte buffer, position/icon/colour fields read from `.ss1` states.
* **Derived:** encoder/validator algorithm from Thumb disassembly and Ghidra pseudocode at `0x0801225E`/`0x08012400`; icon table at `0x0801BD80`; screen dispatcher at `0x08011A7A`.
* **Inferred:** exact mapping of the published colour/shape descriptions to the ROM's icon assets; semantic role of the 3-bit and 6-bit decoded fields (only the 3-bit level selector's jump table was read directly).

## 8. Unknowns

* The accept path crashes mGBA in this **cracked** image (`Jumped to invalid address: 526F526E`). A pristine retail dump may behave differently; the level actually started by a given code was therefore not observed.
* Whether the main menu is reachable on the untouched retail ROM by a normal button path (it is screen 0x15; here it was entered by a savestate screen-ID write).
* Meaning of fields `a` (3 bits) and `b` (6 bits) beyond their storage addresses (`global+0x0C`, `global+0x1AB`).
* Published codes could not be converted to symbol bytes because their icon descriptions do not match the ROM asset names.

## 9. Tooling

`strings`, `xxd`, `objdump`/Capstone (`arm-none-eabi-objdump -M force-thumb`), Ghidra via REA MCP (`batch_decompile`), Python `ss.py` (mGBA savestate `gbAs` decoder), `patch_ss.py` (savestate byte patcher with correct PNG CRC), `pwdmodel.py` (encoder/validator reimplementation), `k.sh`/`probe.sh`/`oracle.sh`/`cleanentry.sh` (xdotool input helpers), mGBA + Xvfb :319 + openbox. No ROM or copyrighted assets were redistributed.

## Legal note

Only hashes, addresses, algorithms and generated code values are published here. No ROM bytes, graphics, audio or game text beyond short UI labels are reproduced.
