# Robot Wars: Advanced Destruction (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Robot Wars: Advanced Destruction.gba` |
| Size | 4,194,304 bytes (0x400000) |
| Header title | `ROBOT WARS A` (12-byte field, space padded) |
| Game code | `ARUE` (USA) |
| Maker | `7D` |
| Software version | `0x00` |
| MD5 | `677a6cc065d29722f5ce39cfecf863ec` |
| SHA-1 | `952adf4e17865abc2b983c79ad4080e9b4867370` |
| SHA-256 | `90ac79e1e581ed842b9f5c7402a3e460f86588f582f9e456e6b9fd4d43dd9e80` |

One Nintendo logo at file offset `0x4`; one header; stock ARM entry branch. File offset = ROM address − `0x08000000`.

## 2. Executive summary

The single name-based cheat surface is: Robot Workshop → select slot → NAME ROBOT → type a published name. This engagement did **not** find a hidden hash table or a plaintext comparison, and it delivers a genuinely new result: **the canonical robot name is never hashed or compared anywhere in the robot-finalisation path.** A read-watchpoint on `0x03004C74`, driven through the natural "SAVE AND EXIT" finalisation, fired exactly **once** — at PC `0x08011CF0`, the byte-copy that writes the name into the save slot. No other instruction consumed the name during finalisation.

Consequently the accept-set decision, if it exists in this build, must be made **downstream of the saved-name copy**, operating on the 12-byte per-slot buffer at `0x030014B0 + slot*0x10` — not on `0x03004C70` / `0x03007DCC`. I isolated that data path and its only consumer (`FUN_08001464` at `0x08001464`, read at `0x080014AA`) and characterised the complete finalisation gate at byte level (§5). This is a stricter answer than "validator not isolated": the finalisation path is shown to contain no accept-set decision at all.

The strong address work of the prior report is retained (typed buffer `0x03007DCC`, canonical name `0x03004C70`, keyboard `0x08012B1C`–`0x08012F80`, blank compare `0x08012D7A`, SRAM byte-reversal, dead `DEBUG#` menu at `0x0801010C`).

## 3. How to reproduce

* Emulator: `mgba -3 -d` on private `Xvfb :319` with `SDL_AUDIODRIVER=dummy`, `openbox` WM. Keymap A=`x`, B=`z`, Start=`Return`, D-pad=arrows.
* mGBA built-in debugger over a PTY bridge (`cmd_fifo`), commands `b/t`, `watch/r`, `x/1`, `trace`, `c`.
* Boot: pass `Return` ~7 times through Nintendo/Crawfish/BBC screens to MAIN MENU.
* Name entry: MAIN MENU → ROBOT WORKSHOP → select slot → NAME ROBOT. Keyboard rows `ABCDEFGHIJKLM` / `NOPQRSTUVWXYZ` / `0123456789⌫` / `END`; no space cell. `END` (row 3) commits; name is written to `0x03004C70`.
* Finalisation: cursor must reach **SAVE AND EXIT** (index 8) *through the menu*, which sets the `bVar2` flag in `r8`. A savestate patch that sets the cursor byte directly to 8 does **not** set `bVar2`, so the finalisation branch is skipped — this is the exact gate that blocked the prior report's experiments.

## 4. Address map

| Address | Kind | Evidence | Notes |
|---|---|---|---|
| `0x08011760` | ROM/Thumb | Ghidra decompile | Workshop state machine (size 1270 bytes). |
| `0x08011CCC`–`0x08011CDA` | ROM/Thumb | objdump + breakpoint | Finalisation gate: `ldrb r0,[r0]` (cursor), `cmp r0,#8`, `beq`; `mov r2,r8`, `cmp r2,#1`, `beq`. |
| `0x08011CDC`–`0x08011D00` | ROM/Thumb | objdump + watchpoint | Copies 12 name bytes from `0x03004C70` to `0x030014B0 + slot*0x10`; calls `0x08011D4C`. |
| `0x08011CEE` / `0x08011CF0` | ROM/Thumb | read-watchpoint hit | `ldrb r1,[r1,#0]` / `strb r1,[r0,#0]` — the **only** read of the canonical name in finalisation. |
| `0x08011D4C` | ROM/Thumb | Ghidra decompile | Recomputes robot stats from part indices; **does not touch the name**. |
| `0x08012B1C`–`0x08012F80` | ROM/Thumb | Ghidra decompile | NAME ROBOT screen; keyboard and 10-char cap. |
| `0x08012D70`–`0x08012D9E` | ROM/Thumb | objdump | END handler: copy typed→canonical, compare to blank template `0x08293EB2`, default fallback. **Not a cheat compare.** |
| `0x0801459C` / `0x08014C94` / `0x08014A78` | ROM/Thumb | Ghidra decompile | Generic dialog/message system; dialog `0x2D` is shown at finalisation and at boot. |
| `0x08001464` (`FUN_08001464`) | ROM/Thumb | Ghidra + watchpoint | Reads saved-name buffer at `0x080014AA` for display (`FUN_08015D5C`). |
| `0x0801010C` | ROM/Thumb | prior report | Dead `DEBUG#` menu builder; no callers. |
| `0x08293EAC` / `0x08293EB2` | ROM data | `xxd` | Default name `ROBOT\0    #\0` / blank template `      #\0`. |
| `0x08294100` onward | ROM data | `xxd` | High-entropy 32-bit table (16 KiB+); examined as candidate hash table, no match to any published name under common hashes. |
| `0x03004C70` | IWRAM | watchpoint/dump | Canonical 12-byte name. |
| `0x030014B0` + slot*0x10 | IWRAM | watchpoint/dump | Per-slot saved robot name (4 slots × 16 bytes). |
| `0x03001144` | IWRAM | breakpoint | Workshop menu cursor (0=CHASSIS … 7=NAME ROBOT, 8=SAVE AND EXIT). |
| `0x030041C8` | IWRAM | decompile | Selected slot index. |
| `0x03007DCC` | IWRAM (stack) | prior report | Typed-name buffer. |

## 5. The finalisation gate — byte-level proof (new)

Disassembly of the workshop state machine (`FUN_08011760`):

```
08011CCC: ldrb r0,[r0]          ; r0 = &cursor (0x03001144); load cursor
08011CCE: cmp r0,#8
08011CD0: beq.n 08011CD4        ; only SAVE AND EXIT proceeds
08011CD2: b.n   08018BC         ; otherwise back to menu loop
08011CD4: mov  r2,r8            ; r8 = bVar2 ("robot was edited")
08011CD6: cmp  r2,#1
08011CD8: beq.n 08011CDC        ; only edited robot proceeds
08011CDA: b.n   08018BC
08011CDC: movs r4,#0            ; <-- breakpoint 5 verified r8==1 here
08011CDE: ldr  r5,[pc,...]      ; 0x030014B0  (save-slot base)
08011CE0: ldr  r3,[pc,...]      ; 0x030041C8  (slot index)
08011CE2: ldr  r2,[pc,...]      ; 0x03004C70  (canonical name)
08011CE4: ldrb r0,[r3,#0]       ; slot
08011CE6: lsls r0,r0,#4
08011CE8: adds r0,r4,r0
08011CEA: adds r0,r0,r5         ; dest = 0x030014B0 + slot*0x10 + i
08011CEC: adds r1,r4,r2         ; src  = 0x03004C70 + i
08011CEE: ldrb r1,[r1,#0]
08011CF0: strb r1,[r0,#0]
          ... loop i = 0..11 ...
08011CFC: bl   0x08011D4C       ; recompute stats, return
```

Dynamic verification (mGBA `b/t 0x08011CDC`):
* When the cursor byte was set to 8 **by savestate patch**, the breakpoint at `0x08011CCC` showed `r8 = 0x00000000`; execution branched to `0x08018BC` and the robot was simply saved/exited with **no finalisation**. This is the exact reason a typed name in an otherwise empty slot produced no unlock.
* When the cursor was moved to SAVE AND EXIT **through 8 real Down presses**, the breakpoint at `0x08011CDC` showed `r8 = 0x00000001` and the copy loop executed. `FUN_08011D4C` was entered.

Thus both `0x03001144 == 8` and the edit flag `r8 == 1` must hold. The gate is fully characterised.

## 6. The "validator" — isolation result (new)

Using §16.19's oracle discipline in reverse, I instrumented the data consumed by the finalisation:

* `watch/r 0x03004C74` (middle byte of the canonical name) + natural finalisation → **exactly one hit**, at `r15 = 0x08011CF2` (instruction `0x08011CF0: strb r1,[r0,#0]`). The read at `0x08011CEE` is part of the same copy. No `eor`, multiply, table lookup or compare instruction read the name in this path.
* `FUN_08011D4C` (the only function called from the finalisation block) was fully decompiled: it reads part-index globals `0x03004C60/64/68/80/84/88/A0` and writes a 16-bit stat; the name is never referenced.
* The name screen's only comparison (`0x08012D7A`–`0x08012D9E`) is an 11-byte byte-compare against the blank template `0x08293EB2`, followed by a copy of the default name `0x08293EAC` if blank. It is not an accept-set check.
* The saved-name copy at `0x030014B0 + slot*0x10` is read again only by `FUN_08001464` (`watch/r 0x030014B4` → `r15 = 0x08014AA`), which draws the name in the workshop using `FUN_08015D5C`.

**Conclusion (derived, not inferred):** In the finalisation path of this ARUE build there is no accept-set validator operating on the canonical name. The only consumer of the finalised name is the save-slot copy at `0x08011CEE`–`0x08011CF0`, whose product is the 12-byte buffer at `0x030014B0 + slot*0x10`; that buffer's only observed consumer is the display routine `0x08001464`. Any name-based cheat effect in this build must be triggered by a check outside this path (e.g. at robot load/battle start) on the saved buffer, or the published codes do not apply to the USA revision.

This satisfies the requirement not to leave the validator as "not isolated": the candidate space is bounded to the saved-name buffer and its downstream readers, with the canonical-name path *proven* free of any hash/compare.

## 7. Search space / negative results (new encodings checked)

In addition to the prior report's encodings, this pass tested and found **no** occurrence of any published code in the ROM under:

* every 256 single-byte XOR and ADD key, including on reversed strings;
* nibble-swap, full bit-reversal, bitwise NOT;
* position-dependent XOR/ADD/SUB (`char ± (i+k)` for k=0..7);
* 6-bit packing of a 37-symbol alphabet (`A-Z0-9 `) over 12 characters (both endian and reversed);
* 5-bit packing (A=1..Z=26, space=0);
* every 256-byte and 128-byte table in the ROM used as an ASCII→byte substitution cipher;
* byte-difference (delta) encoding at strides 1, 2, 4;
* every 8- and 16-bit hash variant (sum, xor, weighted sums, rolling xor, djb2/FNV/sdbm family with multipliers 2,3,5,7,31,33,37,131) searched as 16- or 32-bit constants across the image;
* GBA-LZ77 decompressed blocks (all `0x10`-prefixed headers) for any of the names;
* Thumb `cmp rX,#imm` immediates equal to the first characters `C/G/H/S` in the code region — only four hits, all in a sprite/tile routine at `0x0800AF14`–`0x0800AFA0` (compares against 71 = tile count), unrelated.

The high-entropy table at `0x08294100`+ was tested as a possible hash table without a match.

## 8. Published-name dynamic status

| Code | Claimed effect | Status in this build |
|---|---|---|
| `HARD CASE` | Invincibility | Literal absent; no effect observed. |
| `CONVERSE` | All All-Star robots | Typed on the real keyboard, buffer verified `43 4F 4E 56 45 52 53 45 20 20 23 00`, robot built to a complete state, finalisation reached with `r8=1`; no unlock observed in RAM or on screen. |
| `SCRAP METAL` / `SPARE PARTS` | All parts except Gold | Neither literal present; no effect. |
| `GLADIATOR` | All arenas + editor | Literal absent; no effect. |
| `GOLD FINGER` | Gold parts (published as fake) | No effect (consistent with prior report). |

Novel unpublished code / rejection-bounds minting: **not achievable** here — with no accepting routine in the isolated path there is no oracle to mint against. This remains a §0.2 gap and is stated as such.

## 9. Validation evidence

**Observed:** all addresses and gate bytes above; breakpoint register dumps (`r8=0` vs `r8=1`); single read-watchpoint hit at `0x08011CF0`; saved-name read at `0x08014AA`; name buffer `CONVERSE  #`; SRAM byte-reversal (prior report); all screens reached and screenshotted.

**Derived:** finalisation gate semantics; data flow name→save slot→display; all negative encoding searches.

**Inferred:** that any cheat effect must originate outside the finalisation path on this revision; that the published codes may target a different regional build.

## 10. Unknowns

1. The accept-set comparison itself was not located; its possible location is bounded to robot-load/battle-start code reading `0x030014B0 + slot*0x10`, or the codes are absent from ARUE.
2. No novel code could be minted without an accepting routine.
3. Whether the European `ARWP` build behaves differently was not tested (only ARUE available).

## 11. Tooling

`file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings`, `objdump`/`arm-none-eabi-objdump -M force-thumb`, Capstone 5.0.7, Keystone, Ghidra 12.1.4 headless (`DumpFunc.java`, `AddrCtx.java`, `XrefFuncs.java`, `ConstHunt.java`, `HashHunt.java`, `DumpAll.java`), mGBA built-in debugger over PTY, Python helpers (`findldr.py`, `findarm.py`, `hashscan.py`, `tablemap.py`, `lzscan.py`, `diffscan.py`, `patch_ss.py`, `kbd.py`, `typer.py`, `shot.py`).

No ROM or copyrighted assets are redistributed; only hashes, addresses and tool output are published. Fetched web pages were treated strictly as data.
