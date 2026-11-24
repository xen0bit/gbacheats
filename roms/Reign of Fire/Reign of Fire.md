# Reign of Fire (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Reign of Fire.gba` (8,388,608 bytes / 8 MiB) |
| Header title | `REIGN OF FIR` (12-byte GBA field; full title *Reign of Fire*) |
| Game code / maker | `AR9E` / `6L` (rev 0) |
| MD5 | `97e46f72ce3ccdaa76bee1eb60342bc7` |
| SHA-1 | `315b517c6e933e2137dd5385e8f3f564936540e8` |
| SHA-256 | `e0deda4906e0b9da17526ad571583f5d5f39d29a78e106640623cd06ddc927cf` |
| Entry word | `0xEA00002E` — stock `b 0x080000C0`, **not** a cracktro patch (§16.1) |
| Header checksum | stored `0x0000`, computed `0x554` → rebuilt header (§16.1); complement byte `0x93` |
| Embedded headers | Nintendo-logo scan finds exactly **one** header, at file `0x0`; no multiboot/trainer payload |

Developer/publisher (from credits screens): Crawfish Interactive / Bam Entertainment, 2002; external testing by "The Test Station".

## 2. Executive summary

The game has a genuine **developer-intended 9-symbol password system**, reachable from the title screen (`PASSWORD`). It is algorithmic, not a lookup table: the decoder at `0x080116D0` reads nine 5-bit symbol indices from EWRAM `0x02002A90`, packs them into six bytes, applies a byte transform, and checks a 5-bit additive checksum. On success it writes a 32-bit payload (sixteen 2-bit mission fields) plus three flag bytes, returns `r0=1`, and the game shows **"Password Accepted"**, rolls the credits, and enables the RANKINGS/level-select screen.

Published codes were found on 3rd party cheat indexes:
* `9XL?GSB78` — "unlock all levels": **verified valid** in the ROM and in the emulator.
* `RLF2T8T?6` — "unlock level 2" (3rd party cheat indexes only): **rejected** by the game ("Wrong Password / Try Again!") — a published-list error (§16.7).

The validator was reimplemented bit-for-bit in Python (`decoder.py`, `encoder.py`). Novel checksum-valid codes were minted and accepted on the real screen; one of them (`DY39ZK44D`) triggers an **unadvertised congratulations cutscene** ("Congratulations on using your own initiative and excelled. You are now ready for the toughest …", "The eggs are nearly ready to hatch …") and starts **MISSION 6**, an effect no published list describes. Bounds were proven in-game by rejecting a bad checksum and an out-of-range symbol. No debug menu or button code exists in this image (bounded negative, §7).

## 3. How to reproduce

**Environment:** mGBA 0.10.5 under Xvfb `:319`, `SDL_AUDIODRIVER=dummy`, `-3` scale, `-d` command-line debugger driven through a PTY. Default SDL keymap: A=`x`, B=`z`, Start=`Return`, D-pad=arrow keys.

**Menu path (RAM-verified):**
1. Boot → language select (UK/DE/ES/IT/FR flags) → press **A** for English.
2. Title screen → press **Down** once → press **A** → `PASSWORD` character grid.
3. Grid is 6×6: row0 `B C D F G H`, row1 `J K L M N P`, row2 `Q R S T V W`, row3 `X Y Z 0 1 2`, row4 `3 4 5 6 7 8`, row5 `9 ? -` + two red function cells. Move with D-pad, press **A** to append a symbol (nine slots at bottom); the red cells are delete/accept. Count lives at `0x02002AB8`.

**Fast code entry (used for all tests):** with the debugger, write the nine symbol indices to `0x02002A90`, write `9` to `0x02002AB8`, write `1` to `0x020090C4` (the "submit" flag set by the accept cell), then advance ~14–25 frames. Result text appears on the password screen.

**Codes tested:**
| Code | Origin | Result |
|---|---|---|
| `9XL?GSB78` | 3rd party cheat indexes | Password Accepted → credits → RANKINGS enabled |
| `RLF2T8T?6` | 3rd party cheat indexes | Wrong Password / Try Again! |
| `DY39ZK44D` | **generated here** | Password Accepted → unique congratulations cutscene → MISSION 6 |
| bad checksum (slot0 `D`→`F`) | generated here | Wrong Password / Try Again! |
| out-of-range symbol 44 in slot0 | generated here | Wrong Password / Try Again! |

## 4. Address map

All addresses are GBA bus addresses; ROM file offset = address − `0x08000000`.

| Address | Meaning | Evidence |
|---|---|---|
| `0x080116D0` | Password decoder / validator (returns `r0`=1 accept, 0 reject) | BL xref from `0x08006FDA`; called with injected codes |
| `0x0801184E`–`0x08011860` | copy 6 packed bytes → `0x02005E8` | disassembly |
| `0x08011862`–`0x08011890` | decode transform (`i<=1`: −13; `i>=2`: +6) | disassembly |
| `0x080118A6`–`0x080118C4` | checksum compare, `r0=0` on failure | disassembly |
| `0x080118D8`–`0x080118E8` | extract 16×2-bit mission fields | disassembly |
| `0x08014404` | `u8(x)` no-op used for each symbol | disassembly |
| `0x08006FDA`–`0x08006FE6` | caller: calls decoder, maps `r0` to sound `0x3E` (accept) / `0x3B` (reject) | disassembly |
| `0x08013300`–`0x080133A4` | password input handler (cursor 32=delete, 33=accept, writes buffer/count) | disassembly + RAM diff |
| `0x080134E8` | English string-pointer table base (`char*` array, 268+ entries) | pointer scan |
| `0x0802491C/30/40` | "Password Accepted" / "Wrong Password" / "LOCK-OUT" | `strings -t x` |
| `0x084934E8` | table base itself; stored to RAM at `0x02020608` | literal at `0x08013E60` |
| `0x02002A90` | 9-byte password buffer (raw symbol indices) | RAM search for injected values |
| `0x02002AB8` | u8 entered-character count | RAM diff on A press (2→3) |
| `0x02000670` | 9 packed bytes produced by decoder | literal `0x0801187C`; ROM/RAM byte-exact match |
| `0x02005E8` | 6 transformed payload bytes | literal `0x08011880` |
| `0x0200620` | 16 two-bit mission fields (written on success) | literal `0x08011914` |
| `0x02004490`, `0x0200086C`, `0x020090A0` | three flag bytes written on success | literals `0x08011908/C/10` |
| `0x020090C4` | "submit requested" flag (accept cell) | literal `0x0801334C` |
| `0x020007CC` | decoder result variable in caller | literal `0x08007028` |
| `0x02020608` | current language string-table pointer | RAM read = `0x084934E8` |

## 5. Algorithm

Precise reimplementation in `decoder.py`; verified byte-exact against ROM RAM.

```
symbols v[0..12] = buffer[0..8] + [0,0,0,0]      # 9 typed symbols, 4 zero-pad
# pack 13 × 5-bit symbols LSB-first into 9 bytes (B[0..8]):
B[0]  = v0 | ((v1&7)<<5)
B[1]  = ((v1>>3)&3) | ((v2&0xFF)<<2) | ((v3&1)<<7)
B[2]  = ((v3&0x1E)>>1) | ((v4&15)<<4)
B[3]  = ((v4>>4)&1) | ((v5&0xFF)<<1) | ((v6&3)<<6)
B[4]  = ((v6&0x1C)>>2) | ((v7&0xFF)<<3)
B[5]  = v8 | ((v9&7)<<5)
B[6]  = ((v9>>3)&3) | ((v10&0xFF)<<2) | ((v11&1)<<7)
B[7]  = ((v11&0x1E)>>1) | ((v12&15)<<4)
B[8]  = (v12>>4)&1
# transform first 6 bytes:
D[i] = B[i]-13  (i=0,1);  D[i] = B[i]+6  (i=2..5)     # all mod 256
# checksum:
stored = D[5] & 0x1F
total  = (D[0]+D[1]+D[2]+D[3]+D[4]+(D[5] & 0xC0)) & 0xFF
accept iff (total & 0x1F) == stored
```
On accept: `word = D[0] | D[1]<<8 | D[2]<<16 | D[3]<<24`; for `i=0..15`, `field[i] = (word >> 2i) & 3` → `0x0200620+i`; additional flag bits come from `D[4]` bits 5/6/7. Returns `1`; else `0`.

**Encoder** (inverse): choose the 16 fields → `D[0..3]`; choose free `D[4]`; solve `D[5]` from the checksum; invert the transform to `B[0..5]`, set `B[6..8]=0`; unpack the 65-bit stream into 13 five-bit symbols; the first nine are the typed code. Verified: `unpack(pack(v)) == v` for all test codes.

Proof of model: after submitting `DY39ZK44D` the ROM held `0x02000670 = 62 62 4F 4F CE 02`; Python `pack()` for that code gives exactly `62 62 4f 4f ce 02` (Derived + Observed).

## 6. Tables

**Alphabet (symbol index → glyph), obtained from the on-screen 6×6 grid:**

`0:B 1:C 2:D 3:F 4:G 5:H 6:J 7:K 8:L 9:M 10:N 11:P 12:Q 13:R 14:S 15:T 16:V 17:W 18:X 19:Y 20:Z 21:0 22:1 23:2 24:3 25:4 26:5 27:6 28:7 29:8 30:9 31:?`

All vowels (A E I O U) are omitted. The next grid cells (32=`-`, 33+, red) are control cells (delete/accept); index 44 is the delete marker the game itself writes into a slot (§5.4-style control plane).

**String-table indices** (base `0x084934E8`, 4-byte stride): 5=`NEW GAME`, 6=`PASSWORD`, 7=`RANKINGS`, 8=`OPTIONS`, 25=`B BUTTON TO CANCEL`, 26=`A BUTTON TO ACCEPT`, 28=`LOCK-OUT`, 29=`Wrong Password`, 30=`Password Accepted`, 31=`STAGE `.

## 6b. Enumeration

* **Space definition:** 9 typed symbols × 32 values = `32^9 = 35,184,372,088,832` raw entries. The decoder consumes 13 symbols (9 typed + 4 fixed zero), packs 65 bits into 9 bytes, and uses only the first 6 bytes (48 bits): 32 payload bits + flag bits + a 5-bit additive checksum. Since the checksum is 5 bits, the accepted set is `≈ 32^8 = 1,099,511,627,776` distinct 9-symbol codes (exactly one low-5-bit value of the final symbol per fixed prefix). Payload capacity is `4^16 = 4.29e9` mission-field combinations plus 3 flag bits.
* **Published space:** 2 codes found across 3rd party cheat indexes (Wayback `20181126`), 3rd party cheat indexes. One (`9XL?GSB78`) verified; one (`RLF2T8T?6`) rejected by the game. Neither contains any of the generated codes below.
* **Novel codes generated (absent from every published list), all passing the offline validator:**
  * `DY39ZK44D` — fields `[1]*16`; **accepted in-game**, unique congratulations cutscene + MISSION 6 (screenshots `novel_accepted_c.png`, `novel_msg2_c.png`, `novel_msg3_c.png`, `novel_msg4_c.png`, `after_cut_c.png`).
  * `DY3X?7641` — fields `[1]*8+[3]*8` (offline valid).
  * `9XLFHS34R` — published payload with field 8 changed 1→3 (offline valid).
* **Bounds proven by rejection (in-game):**
  * Wrong checksum (`DY39ZK44D` with first symbol 2→3, indices `[3,19,24,30,20,7,25,25,2]`) → **"Wrong Password / Try Again!"** (`reject_badchecksum_c.png`).
  * Out-of-range symbol (`44`, the delete marker, in slot 0) → **"Wrong Password / Try Again!"** (`reject_oor2_c.png`).
  * Published `RLF2T8T?6` → **"Wrong Password / Try Again!"** (`reject_pub2e_c.png`).
  * Six consecutive wrong submissions did **not** produce `LOCK-OUT`; that string's trigger remains unknown (§8).

## 7. Validation evidence

* **Observed (emulator + RAM):** title/menu/language/PASSWORD/OPTIONS/RANKINGS/pause/mission-select/credits/cutscene screens; buffer `0x02002A90` and count `0x02002AB8` changing on key entry; `0x02000670 = 62 62 4F 4F CE 02` after submitting the novel code; "Password Accepted" and "Wrong Password" result screens; RANKINGS changing from greyed to enabled after the published code.
* **Derived (disassembly):** decoder packing, transform, checksum, payload extraction, flag writes, caller's return-value mapping; string/pointer tables; input-handler special cells.
* **Inferred:** exact semantic names of the sixteen 2-bit fields and the three flag bytes (they are written on success, but each individual field's in-game meaning was not exhaustively exercised). `?` = index 31 is a real symbol (confirmed by the accepted published code).
* **Bounded negative:** the 268-entry English string pointer table contains zero occurrences of `debug`, `secret`, `cheat`, `level`, `test`, `unlock`, `code`, `extra`, `hidden`, `menu`; the whole-ROM `strings` dump likewise had no debug/cheat labels. No button-code mask table or hidden debug screen was found. Cut features are not indicated (no `TEMP` placeholders).

## 8. Unknowns

* The `LOCK-OUT` string exists but six wrong submissions never displayed it; its gate (maybe a much higher failure count or another mode) was not proven.
* The precise mapping of the 16 mission fields and 3 flag bytes to specific unlocks/difficulty was not enumerated field-by-field (the generated all-1 code produced MISSION 6 and a unique cutscene, which is sufficient to prove a distinct effect but not a full field semantics table).
* `RLF2T8T?6` may be a valid code for a different regional revision or a transcription error in 3rd party cheat indexes; only this `AR9E` image was analyzed.

## 9. Tooling

All artifacts in `/tmp/reignoffire/`: `phase0.py` (hash/header/logo scan), `scanptr.py`/`scanbl.py` (literal/BL scans), `inp.py` (XTEST key driver), `dbg_daemon.py`/`dc.py`/`db.py` (mGBA `-d` debugger over PTY + Unix socket), `bytediff.py`/`findbuf.py` (RAM diffs/ searches), `decoder.py`/`encoder.py` (reimplementation and generator), plus screenshots named in the text. Tools: `arm-none-eabi-objdump -M force-thumb`, mGBA 0.10.5 `-d` debugger, `xdotool`, `scrot`, `convert`, Python 3. No ROM or copyrighted assets are redistributed here — only addresses, hashes, and algorithms.
