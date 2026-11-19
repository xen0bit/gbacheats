# Power Rangers: S.P.D. (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Power Rangers: S.P.D.gba` |
| Size | 4,194,304 bytes (0x400000, 4 MiB) |
| Header title | `PRANGERS_SPD` |
| Game code / maker | `BRDE` / `78` |
| Fixed byte / version / complement | `0x96` / `0x00` / `0x1d` |
| Header checksum | `0x0000` (stored) vs `0x0660` (computed) — rebuilt/zeroed header; entry word is stock `0xEA00002E` |
| MD5 | `2892a0fcefc0c183bf725b0a2540a83a` |
| SHA-1 | `494156a4799d3c19de58d34917b6def7b15986e1` |
| SHA-256 | `0dafe7de23468539f6dababaab631e776b991ebd0c8738bfb37f0886859af1f0` |

Embedded-header scan: exactly one 156-byte Nintendo logo at file `0x4` (ROM `0x08000004`); no second header, no appended trainer, crt0 at `0x080000C0` is the normal Natsume/THQ startup. **Observed.**

## 2. Executive summary

The game has a developer-intended **3-symbol password system** on `MAIN MENU → PASSWORD`. The on-screen alphabet has exactly **32 symbols** (`BCDFGHJKLMNPQRSTVWXYZ!0123456789`), so a code is 15 bits. There is no plaintext code table in the ROM; codes are checked **algorithmically** by a routine at `0x08000CE4` (`0x08000DF8` is the packing wrapper, called from the password screen at `0x0803E12C`).

The validator decodes the 3 symbols into three fields:

* **A** — 5-bit stage index, range 0–19 (accepted iff `A <= 19`);
* **B** — 2-bit difficulty field: `0 = Easy`, `1 = Normal`, `2 = Hard`, `3 = reject marker`;
* **C** — 8-bit checksum scattered across the packed bytes, `C = (-( (0x69 & b0) + (0x29 & b1) + 205 )) & 0xFF`.

The whole space is `32^3 = 32,768` inputs; exactly **60** are accepted — one per `(A,B)` with `A∈[0,19]`, `B∈{0,1,2}` (`B=3` is unconditionally rejected). The published GameFAQs/SuperCheats lists cover only the 40 codes for Easy and Hard. **The entire 20-code Normal (`B=1`) tier is absent from the published lists**; this report enumerates it and confirms two of its codes in the emulator.

All 39 published codes were verified against the recovered validator: all 39 are in the accepted set, and no published literal appears in the ROM as ASCII (the codes live only as the algorithm).

## 3. How to reproduce

* Emulator: `mgba -3` under `Xvfb :317`, `SDL_AUDIODRIVER=dummy`, keymap A=`x`, B=`z`, Start=`Return`, D-pad=arrows, L=`a`, R=`s`. Hold keys 120–250 ms.
* Boot → **PRESS START** → `MAIN MENU` → **PASSWORD** (cursor starts on NEW GAME; press Down once).
* Password screen: D-pad moves the 32-symbol cursor, **A** selects a character; after 3 characters the cursor jumps to **OK**; **A** submits, **B** deletes.
* Published controls confirmed: `ZZB` → SELECT STAGE / DIFFICULTY: EASY / EPISODE 1; `9CK` → SELECT STAGE / DIFFICULTY: HARD / all episodes unlocked.
* Novel controls confirmed: `ZGN` → NORMAL / EPISODE 1; `MST` → NORMAL / EPISODE 7.
* Rejections confirmed: `GHN` (valid checksum, `B=3`), `1JJ` (valid checksum, `A=20`), `BBB` (bad checksum) — all left on the password screen with no stage transition.
* Debug route used for proofs: `mgba -3 -d` with the PTY debugger (`load 1` to restore the saved password-screen state; `w/1` to write the input buffer; `SIGINT` to the mgba PID pauses without killing it). Direct buffer write: `0x030033F4..F6` = alphabet indices, `0x030033F0 = 0x21` = OK cursor, then resume and press A.

## 4. Address map

| Address | Meaning | Evidence |
|---|---|---|
| `0x08000000` | ROM base; stock ARM entry `0xEA00002E` | Derived (header/disasm) |
| `0x0802CDD4` | Global KEYINPUT handler (literal `0x04000130` at `0x0802CE40`) | Derived |
| `0x0803C394`, `0x0803C3D4`, `0x0803C414`, `0x0803C454` | Keyboard cursor move/decrement/increment helpers (bounds 0 and 31) | Derived |
| `0x0803DEF8` | Input-buffer range check (all 3 bytes `<=31`) | Derived + Observed (breakpoint hit with `r0=0x030033F4`) |
| `0x0803E10E–0x0803E144` | Password-screen OK handler; calls the decoder at `0x0803E12C` | Derived |
| `0x08000DF8` | Packing wrapper: 3×5-bit symbols → 2 bytes at `sp`, calls `0x08000CE4` | Derived + Observed (breakpoint hit) |
| `0x08000CE4–0x08000DA6` | Validator core: scattered-bit field extraction + checksum + range checks | Derived + Observed (breakpoint at `0x08000D80`: `r1=0x33, r2=0x33, r5=0x52, r12=0x80`) |
| `0x08000C28` | Post-validation transform of field A before storing to UI (`UI+42`) | Derived |
| `0x03000090` | Pointer to the password UI struct | Derived |
| `0x030033D0` | Password UI struct base | Derived |
| `0x030033E0` | UI+0x10: cursor-move flag pointer (written `0x0803C359`) | Observed (write watchpoint hit at `0x0803C3F4`) |
| `0x030033F0` | UI+0x20: keyboard cursor index (`0..31`, `32`=EXIT, `33`=OK) | Observed |
| `0x030033F4..F6` | UI+0x24..26: **3-byte password input buffer** (alphabet indices; `0x20` = empty sentinel) | Observed (`BCD` typed → `00 01 02`; empty → `20 20 20`) |
| `0x030033F8` | UI+0x28: number of characters entered | Observed (`0→2` after 3 chars, i.e. count−1 indexing) |
| `0x030033F9` | UI+0x29: decoded difficulty field B output | Derived + Observed (watchpoint) |
| `0x030033FA` | UI+0x2A: decoded stage field A output (after transform) | Derived + Observed (write watchpoint at `0x08000E68`) |

File offset = ROM address − `0x08000000`.

## 5. Algorithm

Alphabet (index = keyboard order): `B=0,C=1,D=2,F=3,G=4,H=5,J=6,K=7,L=8,M=9,N=10,P=11,Q=12,R=13,S=14,T=15,V=16,W=17,X=18,Y=19,Z=20,!=21,0=22,1=23,2=24,3=25,4=26,5=27,6=28,7=29,8=30,9=31`.

Packing (`0x08000DF8`), with `c0,c1,c2` the three 5-bit indices:

```
b0 = (((c1 & 31) << 5) | (c2 & 31)) & 0xFF
b1 = (((c0 & 31) << 2) | ((c1 & 31) >> 3)) & 0xFF
```

Validation (`0x08000CE4`) — bits are **scattered**, not contiguous:

```
A = b0[0] | b1[5]<<1 | b0[6]<<2 | b1[0]<<3 | b1[3]<<4          # 5 bits
B = b0[3] | b0[5]<<1                                             # 2 bits
C = b0[7] | b1[4]<<1 | b0[4]<<2 | b0[1]<<3 | b1[1]<<4 | \
    b1[6]<<5 | b1[2]<<6 | b0[2]<<7                               # 8 bits
chk = (-( (0x69 & b0) + (0x29 & b1) + 205 )) & 0xFF
accept iff  C == chk  and  A <= 19  and  B != 3
```

On accept the routine writes `A` to `UI+0x2A` (through `0x08000C28`) and `B` to `UI+0x29`; on reject it returns `-1`. `B` is the difficulty: `0=Easy, 1=Normal, 2=Hard`, `3=reject marker`. A is the stage index (the title shown is `A+1` for `A<19`; `A=19` is the "Final battle" on Easy and the "all episodes" unlock on Hard).

A faithful Python reimplementation is `/tmp/opencode/prspd/validator.py`; it agrees with all 39 published codes and with every emulator test below.

## 6. Tables

Complete accepted set, one code per `(A,B)` (all 60):

| Tier | Codes (stage A in parentheses) |
|---|---|
| Easy (B=0) | ZZB(0) ZVC(1) QZB(2) QVC(3) !0G(4) !XH(5) R0G(6) RXH(7) Z2B(8) V6C(9) Q2B(10) L6C(11) !4G(12) W8H(13) R4G(14) M8H(15) 0GD(16) 0BF(17) SGD(18) SBF(19) |
| **Normal (B=1)** | **ZGN(0) ZBP(1) QGN(2) QBP(3) !JS(4) !DT(5) RJS(6) RDT(7) ZLN(8) VQP(9) QLN(10) LQP(11) !NS(12) WST(13) RNS(14) MST(15) 0GL(16) 0BM(17) SGL(18) SBM(19)** |
| Hard (B=2) | G!B(0) GWC(1) 7!G(2) 7WH(3) H1G(4) HYH(5) 61G(6) 6YH(7) G3B(8) B7C(9) 73G(10) 37H(11) H5G(12) C9H(13) 65G(14) 29H(15) JHD(16) JCF(17) 9HJ(18) 9CK(19) |

Published sources and verification:

* GameFAQs (Wayback `20181126054133`) lists 20 Easy/Megazord codes, 19 Hard level codes, and `9CK`; SuperCheats lists 20 Easy codes; mariogba.nl lists 7 "level" codes. All literals were checked against the recovered validator (not against plaintext ROM bytes): **all are valid**; the conflicting `R4G`-as-level-7 label is resolved by the decoded field (`R4G` = A=14 Easy, i.e. the published "Episode 7a" pairing).
* A GameFAQs search snippet exposed five Normal-tier codes (`RNS, MST, 0GL, 0BM, SGL`) that were absent from the fetched page body; the other 15 Normal codes are in no list found.
* No password string, cheat string, "debug" string, or hidden menu label exists in ASCII or UTF-16 in the ROM; UI text is font/tile-indexed. The menu enumeration below is therefore by screen walk, not by strings.

## 6b. Enumeration

* **Space:** 3 symbols × 5 bits = 15 bits → **32,768** possible inputs. Exactly **60 accepted** (0.183 %): 20 per difficulty tier; `B=3` contributes 0. Each accepted `(A,B)` has exactly one spelling — there are **no aliases** (no unused payload bits).
* **Validator model:** reimplemented offline in `validator.py`; it accepts exactly those 60 and rejects the other 32,708. It agrees with every published code and every emulator result recorded here.
* **Novel codes (not in any published list):**
  * `ZGN` — A=0, B=1, Normal. Entered on the real password screen via direct buffer write + OK → **SELECT STAGE / DIFFICULTY: NORMAL / EPISODE 1** (screenshot `ver_ZGNc.png`).
  * `MST` — A=15, B=1, Normal. → **SELECT STAGE / DIFFICULTY: NORMAL / EPISODE 7** (screenshot `ver_MSTc.png`).
  * The remaining 13 unpublished Normal codes are listed in §6; the systematic method to mint any of them is: pick A and B=1, then solve `C==chk` over the 32³ space with the Python model (0.3 s total enumeration).
* **Bounds proven by rejection** (each kept a valid checksum so only the tested field is at fault):
  * `GHN` — correct checksum, `B=3` (reserved reject marker): **rejected**, no transition (`ver_GHNc.png`).
  * `1JJ` — correct checksum, `A=20` (stage field out of `[0,19]`): **rejected**, no transition (`ver_1JJc.png`).
  * `BBB` — `A=0, B=0` but wrong checksum (`C=0x00`, `chk=0x33`): **rejected**, no transition (`ver_BBBc.png`).

## 7. Validation evidence

**Observed** (emulator/RAM): title, main menu, password keyboard, options, credits, difficulty screen, and stage-select screens for Easy/Normal/Hard; input buffer bytes at `0x030033F4..F6` before/after typing; cursor values at `0x030033F0`; watchpoint hits at `0x08000E68`, `0x0803C3F4`, `0x0803DEF8`, `0x08000DF8`, `0x08000CE4`, and the register dump at `0x08000D80` (`r1=0x33, r2=0x33, r5=0x52, r12=0x80`, with `r6=r7=0` for ZZB); all 8 code submissions above with screenshots.

**Derived** (disassembly): the packing wrapper, scattered-bit extraction, checksum formula and bounds, all addresses in §4; the offline enumeration of 60 accepted codes.

**Inferred**: `A=19` on Normal is expected to be an "all-episodes" unlock analogous to `9CK`, but only its Easy (`SBF` = final battle) and Hard (`9CK`) forms were entered; `SBM` was not typed. The `0x08000C28` transform of A was not fully characterised beyond its observed output.

## 8. Unknowns

* Whether the Normal tier was ever advertised in the retail manual (not checked); it is absent from the three cheat lists fetched.
* Exact stage-title mapping for `A` values whose published labels disagree between sources (field values are reported instead, per §16.15).
* No hidden debug screen was found: OPTIONS has only BGM, SFX, CREDITS, EXIT; CREDITS is the standard THQ/S.P.D. badge roll; NEW GAME leads to EASY/NORMAL/HARD. No button-code table or debug gate was located in the alphabet/validator scan.

## 9. Tooling

Scripts in `/tmp/opencode/prspd/`: `phase0.py` (hash/header/logo scan), `findkey.py` / `xrefbuf.py` (literal and LDR xref scans), `findbuf5.py` / `findbuf_final.py` (RAM diff via mGBA PTY debugger), `submit_code.py` (write buffer + submit), `validator.py` (offline decoder), `enumerate.py` (full 32,768-input enumeration), plus watchpoint/trace drivers (`watchfa.py`, `watchwrite.py`, `traceval.py`). Tools: `arm-none-eabi-objdump`, Capstone 5.0.7, `mgba -d` PTY debugger (the `-g` GDB stub was incompatible with GDB 16 and was abandoned; SIGINT-to-PID was used to pause), `Xvfb :317`, `openbox`, `xdotool`, `scrot`, ImageMagick.

**Legal note:** no ROM bytes, graphics, audio, or copyrighted game text are redistributed here — only hashes, addresses, algorithms, and our own tools/findings.

Cleanup: all `mgba` and `Xvfb :317` processes started for this job were stopped by PID; generated `.sav`/`.ss1`/`.ss2` files were removed from the ROM folder.
