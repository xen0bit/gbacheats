# Gekido Advance: Kintaro's Revenge (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Gekido Advance: Kintaro's Revenge.gba` |
| Size | 8,388,608 bytes (8 MiB) |
| Header title | `GEKIDO` |
| Game code / maker | `AGEE` / `20` (full code `AGEE20`) |
| Version | `0x00` (Rev.00) |
| Region | USA — CRC32 `6BBC5F4D` matches `AGB-AGEE-USA` on 3rd party cheat indexes |
| Entry word | `0xEA00002E` = stock `b 0x080000C0` (no cracktro patch) |
| Header checksum / complement | `0x0000` / `0x2A` (non-standard but untouched retail values) |
| MD5 | `f58a7e485676f66c1c88126675d57eff` |
| SHA-1 | `720fe1c2ae59a19235c2045d5915d0d0565e555d` |
| SHA-256 | `d6add6091619b0e31654f284107b48afd628f836d76e74ccd4c87c0f1e4a757f` |

Embedded-header scan: exactly one Nintendo-logo occurrence (file `0x4`); no second game image, no appended trainer, tail padded with `0xFF`. No patch/trainer present.

## 2. Executive summary

The game has a **developer-intended password system** on the title screen (menu entry `PASSWORD`). It accepts exactly **44 five-character codes**, stored as two adjacent obfuscated lookup tables checked by a small Thumb routine:

* 40 **level/continue codes** at ROM `0x083EAD70` (stage 2–5 × 1–10 credits).
* 4 **cheat codes** at ROM `0x083EAE38` (the first, `PIZZA`, is published; the other three — `TOAST`, `CAFFE`, `TORTA` — are not).

The obfuscation is trivial: each input character is stored as ASCII and validated by `(SALT[i] + input[i]) & 0xFF == table[j*5+i]`. Published 3rd party cheat index lists cover only 30 of the 40 level codes and 1 of the 4 cheats, so **10 level codes and 3 cheat codes are absent from every published list**. Six of those novel codes were entered on the real password screen and confirmed with screenshots plus RAM reads; the other four are decoded from the same table with the same validator. Bounds were proven by an in-game rejection (`XXXXX`), by the input cap at 5 characters, and by the loop bounds of the validator itself.

All codes from other editions (`CRAZY`, `STARS`, `MIMMO`, `HURRY`, `FLASH`, `QUEEN`, `SMART`, `YNUTS`) are absent from this USA ROM's tables — they belong to the European/UK build and are correctly rejected here.

No button-code system, hidden character select, or hidden debug screen exists in this image: the title menu has exactly 3 entries, options exactly 3, pause is a freeze-only overlay, and the complete ASCII text banks contain no debug-menu strings.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 (SDL) under `Xvfb :315`, `SDL_AUDIODRIVER=dummy`, 3× scale, default keymap (A=`x`, B=`z`, Start=`Return`, Select=`BackSpace`, arrows = D-pad).
* Intro is ~27 s of splash screens; save a savestate at the title screen to avoid replaying it.
* Path: **title → PASSWORD (Down, A)**. The on-screen keyboard is 3 rows × 12 columns `A–Z 0–9`. Move with arrows, insert with A (button labelled `Insert`), delete one character with B (`Cancel`). A code is validated automatically when the 5th character is inserted. A correct code shows `PASSWORD CORRECT` and returns to the title; a cheat flag is then active in a new game.
* Published controls checked: `PIZZA` (3rd party cheat indexes unlimited-energy code) → `PASSWORD CORRECT`; `SACCO` → stage 2 with 7 credits (matches the published table).
* Novel codes entered on the real screen: `TOAST`, `CAFFE`, `TORTA`, `PALLA`, `SPUMA`, `LORDO`.
* Rejection tests: `XXXXX` (no table match) and an attempted 6th character after `PIZZA`.

## 4. Address map

File offset = ROM address − `0x08000000`.

| Item | ROM / RAM address | Notes |
|---|---|---|
| English menu text bank | `0x08357730` | ASCII, NUL-terminated; offset table at `0x083576C0` |
| Password-screen init | `0x08008560` | clears 12-byte buffer at `0x03000BB0`, resets count |
| Keyboard draw/handler | `0x08008374`, `0x08008774`–`0x080088C0` | 36-key grid, row ±12, left/right with row-wrap guards |
| Password validator | `0x080088C0`–`0x08008AC0` | two comparison loops (level then cheat) |
| Input buffer | IWRAM `0x03000BB0` | 12 bytes, ASCII (observed `54 4F 41 53 54` for TOAST) |
| Input length | IWRAM `0x03000BF0` | byte, observed 1 after one character |
| Insert count | IWRAM `0x03026D0` | byte, 0–5; gated by `cmp r0,#4; ble` |
| Keyboard cursor | IWRAM `0x03001C84` | byte, 0–35 |
| Alphabet string | ROM `0x0801C5DA` | `"ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"` |
| XOR/add SALT | ROM `0x0801C630` | 5 bytes `17 65 78 39 BC` |
| Level code table | ROM `0x083EAD70` | 40 × 5 bytes |
| Cheat code table | ROM `0x083EAE38` | 4 reachable × 5 bytes (loop bound `r4 ≤ 3`) |
| Cheat flag word | IWRAM `0x030000F0` | u32; bit `j` set by cheat `j` |
| Stage−1 output | IWRAM `0x03000634` | `j/10 + 1` for levels; `0xFE` for cheats; `0xFF` on rejection |
| Credits−1 output | IWRAM `0x03000BE0` | `j % 10` for levels; 5 on rejection |
| Debug printf literal | ROM `0x081BF6C` | `"Password: %s"` — no xrefs; unused library leftover |

## 5. Algorithm

```
keyboard: 36 symbols (A..Z, 0..9), 3 rows of 12, cursor index 0..35
insert(c):
    if count > 4: return                     # hard 5-character cap
    buffer[count] = ascii(c)                 # via conversion tables
    count++
    if count == 5: validate()

validate():
    for j in 0..39:                          # LEVEL table
        if all(i in 0..4: (SALT[i] + buffer[i]) & 0xFF == level[j*5+i]):
            ram[0x03000634] = j/10 + 1       # stage - 1
            ram[0x03000BE0] = j % 10         # credits - 1
            return LEVEL_START
    for j in 0..3:                           # CHEAT table
        if all(i in 0..4: (SALT[i] + buffer[i]) & 0xFF == cheat[j*5+i]):
            ram[0x030000F0] |= 1 << j        # persistent cheat flag
            ram[0x03000634] = 0xFE
            return TITLE
    ram[0x03000634] = 0xFF                   # invalid sentinel
    ram[0x03000BE0] = 5
    return NO_MATCH
```

`SALT = [0x17, 0x65, 0x78, 0x39, 0xBC]`. Decoding a stored record is simply
`password[i] = (table[j*5+i] - SALT[i]) & 0xFF`, which yields clean uppercase ASCII for all 44 accepted codes.

Stage and credits are recovered as `stage = j/10 + 2`, `credits = j % 10 + 1`. Verified against `SACCO` (j=6 → stage 2, 7 credits), which is exactly the published mapping.

## 6. Tables

### 6.1 Level codes (`0x083EAD70`) — 40 entries

`j` = table index. `*` = published on 3rd party cheat indexes; **bold** = absent from every published list.

| j | Code | Stage | Credits | Published? |
|---:|---|---:|---:|:---:|
| 0 | **PALLA** | 2 | 1 | novel |
| 1 | DUOVA | 2 | 2 | * |
| 2 | LINEA | 2 | 3 | * |
| 3 | MENTO | 2 | 4 | * |
| 4 | VIALE | 2 | 5 | * |
| 5 | PORTO | 2 | 6 | * |
| 6 | SACCO | 2 | 7 | * |
| 7 | **SPUMA** | 2 | 8 | novel |
| 8 | **TENDA** | 2 | 9 | novel |
| 9 | **LAMPO** | 2 | 10 | novel |
| 10 | **RADIO** | 3 | 1 | novel |
| 11 | PESCA | 3 | 2 | * |
| 12 | BOCCA | 3 | 3 | * |
| 13 | LUSSO | 3 | 4 | * |
| 14 | VIDEO | 3 | 5 | * |
| 15 | SALSA | 3 | 6 | * |
| 16 | GERGO | 3 | 7 | * |
| 17 | TAPPO | 3 | 8 | * |
| 18 | **CORDA** | 3 | 9 | novel |
| 19 | **SEDIA** | 3 | 10 | novel |
| 20 | **AGLIO** | 4 | 1 | novel |
| 21 | PASTA | 4 | 2 | * |
| 22 | ZUPPA | 4 | 3 | * |
| 23 | COSTA | 4 | 4 | * |
| 24 | OCCHI | 4 | 5 | * |
| 25 | SISTO | 4 | 6 | * |
| 26 | TESTA | 4 | 7 | * |
| 27 | BUSTO | 4 | 8 | * |
| 28 | TEMPO | 4 | 9 | * |
| 29 | **CASTO** | 4 | 10 | novel |
| 30 | **LORDO** | 5 | 1 | novel |
| 31 | COLLO | 5 | 2 | * |
| 32 | NESSO | 5 | 3 | * |
| 33 | GALLO | 5 | 4 | * |
| 34 | NOTTE | 5 | 5 | * |
| 35 | VERDE | 5 | 6 | * |
| 36 | ROSSO | 5 | 7 | * |
| 37 | ACQUA | 5 | 8 | * |
| 38 | SONNO | 5 | 9 | * |
| 39 | BECCO | 5 | 10 | * |

### 6.2 Cheat codes (`0x083EAE38`) — 4 reachable entries

| j | Code | Flag bit (`0x030000F0`) | Status |
|---:|---|---:|---|
| 0 | PIZZA | bit 0 (`0x01`) | published (unlimited energy, USA) |
| 1 | TOAST | bit 1 (`0x02`) | **novel** |
| 2 | CAFFE | bit 2 (`0x04`) | **novel** |
| 3 | TORTA | bit 3 (`0x08`) | **novel** |

Records 4–39 of this 200-byte region are non-ASCII padding; the validator loop is bounded by `cmp r4,#3; ble`, so they are unreachable.

### 6.3 Published codes rejected by this ROM

`CRAZY`, `STARS`, `MIMMO`, `HURRY`, `FLASH`, `QUEEN`, `SMART`, `YNUTS` — all absent from both decoded tables (European/UK-edition codes, not valid in USA `AGEE`).

## 6b. Enumeration

* **Input space:** 36-symbol alphabet, exactly 5 characters → 36⁵ = **60,466,176** representable strings.
* **Accepted set:** exactly **44** codes (40 level + 4 cheat), proven by dumping both complete tables and reading the validator's loop bounds (`r4 ≤ 39` and `r4 ≤ 3`). There is no checksum or generator — the system is a pure obfuscated lookup, so the accepted set is closed and fully enumerated.
* **Novel codes generated and confirmed on the real screen** (none appears on 3rd party cheat indexes, or any other published list):

| Code | Type | Screen result | RAM proof |
|---|---|---|---|
| `TOAST` | cheat j=1 | `PASSWORD CORRECT`, returns to title | `0x030000F0 = 0x0002`, buffer `TOAST` |
| `CAFFE` | cheat j=2 | `PASSWORD CORRECT` | `0x030000F0 = 0x0004`, buffer `CAFFE` |
| `TORTA` | cheat j=3 | `PASSWORD CORRECT` | `0x030000F0 = 0x0008`, buffer `TORTA` |
| `PALLA` | level j=0 | `PASSWORD CORRECT` | `0x03000634=1`, `0x03000BE0=0` → stage 2 / 1 credit |
| `SPUMA` | level j=7 | `PASSWORD CORRECT` | `0x03000634=1`, `0x03000BE0=7` → stage 2 / 8 credits |
| `LORDO` | level j=30 | `PASSWORD CORRECT` | `0x03000634=4`, `0x03000BE0=0` → stage 5 / 1 credit |

  The remaining seven novel level codes (`TENDA`, `LAMPO`, `RADIO`, `CORDA`, `SEDIA`, `AGLIO`, `CASTO`) decode through the same validator with the same SALT and were not individually retyped.
* **Baseline cross-checks:** published `PIZZA` → flag `0x01`; published `SACCO` → `0x03000634=1`, `0x03000BE0=6` (stage 2 / 7 credits), exactly as published.
* **Bounds proven by rejection:**
  * `XXXXX` → no match: `0x03000634 = 0xFF` (invalid sentinel), `0x03000BE0 = 5`, cheat flags remain `0`, no `PASSWORD CORRECT`.
  * Attempted 6th character after `PIZZA` → ignored; buffer stays `PIZZA`, count stays `5` (`cmp r0,#4; ble` gate).
  * Cheat space bounded to 4 entries by the loop's `cmp r4,#3`; level space bounded to 40 by `cmp r4,#39`.
  * `TOAST`'s flag bit persisted across screen transitions and into a started game (`0x030000F0 = 0x02` after NEW GAME), so the cheat is a real state change, not a display artifact.

## 7. Validation evidence

**Observed** (emulator screenshots + savestate RAM reads, mGBA on `:315`):

* Title, PASSWORD, OPTIONS, pause, cutscene and gameplay screens walked; cursor on title wraps after 3 entries, options after 3, pause D-pad/A/Select produce no menu.
* On-screen keyboard: `A B C D E F G H I J K L / M N O P Q R S T U V W X / Y Z 0 1 2 3 4 5 6 7 8 9` (36 symbols).
* `PASSWORD CORRECT` for every accepted code above; `XXXXX` produced no such message.
* Input buffer bytes, count, cheat flag, stage and credit variables read from decompressed `gbAs` savestate chunks at the addresses in §4.

**Derived** (disassembly):

* Validator comparison `(SALT[i] + buffer[i]) & 0xFF == table[j*5+i]` at `0x08008930`–`0x0808A46`.
* Both table bases, their 5-byte record stride and their loop bounds.
* Stage/credit derivation via `/10` and `%10` calls at `0x08016400` / `0x08016498`.
* Hard 5-character input cap.

**Inferred** (not fully exercised):

* The specific gameplay effects of cheat bits 1–3 (`TOAST`, `CAFFE`, `TORTA`). Their flag bits, persistence and return-to-title behaviour were observed; which statistic each bit modifies was not isolated because no reader of `0x030000F0` could be pinned down statically and the GameShark-style addresses published for this title are memory-edit codes, out of scope here. Bit 0 (`PIZZA`) is documented by 3rd party cheat indexes as unlimited energy.

## 8. Unknowns

* Exact gameplay effect of `TOAST` / `CAFFE` / `TORTA` beyond the observed flag bits.
* Game-over and ending screens were not reached; the strings `CONTINUE`, `CREDITS`, `THE END` exist in the text bank but no menu entry for them appeared on any walked screen, so they are gated behind play progression.
* No hidden debug screen or button-code table was found: all reachable menus were walked with cursor-limit evidence, and the complete English/Italian/German/French/Spanish ASCII text banks (ROM `0x08357730`–`0x08360000`) contain no debug/level-select labels. The only debug-looking string, `"Password: %s"`, has zero code xrefs.

## 9. Tooling

* `file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings -t x`, `grep -abo`, Python `zlib`/`struct` for ROM and savestate parsing.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for disassembly; Capstone (Python) for Thumb PC-relative literal scans.
* mGBA 0.10.5 with GDB stub (`-g`, found unreliable: TCP connect accepted but no GDB replies) and `-d` pty debugger (worked, used for register/memory inspection experiments); primary dynamic evidence came from SDL mGBA plus `xdotool` input and Shift+F1/F2 savestates.
* `ssdiff.py` — decompresses the PNG `gbAs` chunk of mGBA `.ss1/.ss2` files and diffs raw bytes (GBA state layout: IWRAM at raw `0x19000`, so IWRAM `0x0300XXXX` → raw `0x19000+XXXX`).
* `typepw.py` — drives the on-screen keyboard: maps character → row/column, sends arrow keys and A with 60 ms holds / 160 ms gaps.
* Web: 3rd party cheat index cheats page, 3rd party cheat indexes.

No ROM data or copyrighted assets are redistributed in this report; only addresses, hashes, algorithms and the derived code strings are published.
