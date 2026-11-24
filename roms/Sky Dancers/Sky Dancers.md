# Sky Dancers (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Sky Dancers/Sky Dancers.gba` |
| Size | 4,194,304 bytes (0x00400000, 4 MiB) |
| Header title | `SKYDANCERS` |
| Game code | `B4DE` |
| Maker code | `4Z` (Crave Entertainment / David A. Palmer Productions / Gravity-i) |
| Version | 0x00; fixed byte 0xB2 = 0x96 |
| Entry word | `0xEA00002E` → stock `b 0x080000C0`; one header; build tag `MultiSio010214` at `0x080101B8` |
| MD5 | `fedf94e93a79d35f70ea85a78fdee5aa` |
| SHA-1 | `a757f4a0586081c1058f7e82bbbb5cede2819036` |
| SHA-256 | `1c3991741b04750e2190a5927863673b1ff7d21351ace7308c07929338614a72` |

Retail US image, no trainer/multicart content. All findings are developer-intended.

## 2. Executive summary

Sky Dancers has a developer-intended **8-character password system** on the main menu. Each typed glyph is an **index 0–20** into the 21-symbol alphabet `BCDFGHJKLMNPQRSTVWXYZ` (u32 table at `0x080A74C0`); the editor stores the eight indices directly as u32 at `0x03000000..0x0300001C`. The generator `0x0800CE38` is the forward map (`password[i] = alphabet[progress[i]]`) and reproduces the live pause-screen password bit-for-bit.

The previously missing accept path is now isolated and fully recovered:

* **Validator `0x08006758`** — the OK/A handler at `0x080064CC` calls it. Exact predicate:
  * `(15 − Σ progress[0..6]) & 0x0F == progress[7]` — a **4-bit mod-16 checksum** (this *supersedes* the earlier mod-21/bit-weight model);
  * `progress[6] <= 20`.
  * On success it bit-decodes `progress[0..5]` into game-state globals, writes `progress[6]` to `0x030014FC` and `0x0301560`, and returns 1.
* **Accept gate in the OK handler at `0x080064E6`** — after the validator returns 1 it reads `*(u32*)0x030014FC` (the just-written `progress[6]`) and requires it to equal **20 (Z)**. Only then does the screen return `0xFE`, which the dispatcher (`0x08006590`) turns into the `"PASSWORD ACCEPTED!"` message (`0x080101A4`, descriptor `0x080C9BF0`) and a transition to game start.

A novel code, **`TTPBHBZR`** (indices `[15,15,11,0,5,0,20,13]`), was injected at the real entry screen's validator breakpoint and **observed accepted**: the accept block at `0x08006590` was hit with **`r0 = 0x000000FE`** (§6b/§7). The two codes derived by the earlier mod-21 model (`TTPBHCBP`, `FBFBBBNZ`) are shown to fail both the checksum and the `i6 == 20` gate. The published OCR correction `TTPBHC2Q → TTPBHCZQ` stands.

## 3. How to reproduce

```
Xvfb :316 -screen 0 1024x768x24 &   DISPLAY=:316 openbox &
DISPLAY=:316 SDL_AUDIODRIVER=dummy mgba -3 -d "Sky Dancers.gba"   # CLI debugger over a PTY
```
Keymap (verified via `KEYINPUT` at `0x04000130`, active-low): `x`=A, `z`=B, `Return`=Start, `BackSpace`=Select, arrows=D-pad. Hold 140–200 ms.

Menu path: `PRESS START` → `MENU` → `PASSWORD` → `ENTER PASSWORD` (`BBBBBBBB` initially). The editor stores indices at `0x03000000..1C`; A submits. Deterministic navigation from a fresh boot: ~19 × Start to MENU, Down ×1, A. (The menu cursor state persists across sub-screens; probe with B/A and watch the screen.)

Breakpoints used in mGBA's CLI debugger: `break 0x08006758` (validator entry), `break 0x08006590` (accept block). Set them **before** `continue`, while the core is paused at reset — mGBA's CLI debugger does not process commands while the core is running.

## 4. Address map

| Address | Kind | Meaning |
|---|---|---|
| `0x0800CE38` | Thumb fn | password generator `gen(mode, attr)` — forward index→glyph map |
| `0x080A74C0` | data | 21 × u32 alphabet `0x42,0x43,0x44,0x46 … 0x5A` = `BCDFGHJKLMNPQRSTVWXYZ`; word 21 onward = 0 |
| `0x03000000..1C` | RAM | 8 × u32 progress indices `i0..i7` (= typed glyph indices on the entry screen) |
| `0x03005230` | RAM | generated password char buffer (8 chars + NUL) |
| `0x0800CFB4` | Thumb fn | text/glyph render helper |
| `0x0800643C` | code | password-screen key loop: Left/Right move cursor `r7` (0..7) |
| `0x08006470` / `0x08006498` | code | Up/Down change `progress[r7]` with wrap 0↔20 |
| `0x080064CC` | code | `bl 0x08006758` — A/OK calls the validator; `lr = 0x080064D1` |
| `0x080064E6` | code | post-validator gate: `*(u32*)0x030014FC == 20` → return `0xFE` |
| **`0x08006758`** | **Thumb fn** | **password validator** |
| `0x08006818/1C/20/24/28/2C` | literals | `0x03000000, 0x0301510, 0x0303B60, 0x0301520, 0x03014FC, 0x0301560` |
| `0x08006590` | code | dispatcher accept block: displays `"PASSWORD ACCEPTED!"` then enters mode 1 |
| `0x080C9BF0` | data | message descriptor `{0xFF,0x40,0, ptr=0x080101A4, …}` = `"PASSWORD ACCEPTED!"` |
| `0x080101A4` | data | ASCII `"PASSWORD ACCEPTED!"` |

## 5. Algorithm

### 5.1 Generator (unchanged, verified)
```
gen(mode, attr):
    buf = 0x03005230;  buf[0..7] = ' '
    for i in 0..7:
        if i == mode and (*(u32*)0x03000A9C & 31) <= 15: continue   # blink one slot
        buf[i] = (u8)alphabet32[*(u32*)(0x03000000 + 4*i)]          # 0x080A74C0[v*4]
    buf[8] = 0;  render(...)
```
Proof: savestate held `[3,0,3,0,0,0,0,9]` and string `FBFBBBBM`; BP at `0x0800CE38` saw `mode=0,attr=0x50` from `0x08006194` and `gen(0xFF,0x60)` from the entry screen.

### 5.2 Validator `0x08006758` — recovered verbatim
```
validate():                          # r0 = 1 (accept) / 0 (reject)
    r5 = 0x03000000
    s = 0
    for i in 0..6: s += *(u32*)(r5 + 4*i)          # i0..i6, 7 words
    if ((15 - s) & 0x0F) != *(u32*)(r5 + 0x1C):    # i7 must equal (15-s) mod 16
        return 0
    i6 = *(u32*)(r5 + 0x18)                        # progress[6]
    if i6 > 20: return 0
    # bit-decode i0,i1,i2,i3,i4,i5 into game-state globals
    #   0x0301510.., 0x0303B60.., 0x0301520..
    *(u32*)0x030014FC = i6;  *(u32*)0x0301560 = i6
    return 1
```
The checksum is **integer mod 16** (mask `0x0F`), not mod 21. Equivalent: `Σ progress[0..7] ≡ 15 (mod 16)`.

### 5.3 Entry-screen accept gate `0x080064C0..0x080064EE`
```
if (A pressed):
    if validate() != 0:
        play_sound(0x17)
        if *(u32*)0x030014FC == 20:      # i6 == Z, written by validate()
            return 0xFE                  # -> dispatcher shows "PASSWORD ACCEPTED!"
    else:
        return 1                         # -> back to MENU (silent reject)
```
So a typed code is accepted **iff** `Σ i[0..6] + i[7] ≡ 15 (mod 16)` **and** `i[6] == 20`.

### 5.4 Why the earlier model was wrong
The mod-21 relation `i6+i7 = const` *did* fit the published table because those codes are structured progress states, but it is not the machine predicate. The real check is the 4-bit sum above; the bit-weighted `f(v)` model of the previous report is spurious and is withdrawn.

## 6. Tables

* **Alphabet** (index → char, `0x080A74C0`):
  `0:B 1:C 2:D 3:F 4:G 5:H 6:J 7:K 8:L 9:M 10:N 11:P 12:Q 13:R 14:S 15:T 16:V 17:W 18:X 19:Y 20:Z`
  (No vowels/digits; published `TTPBHC2Q` is an OCR error — `2` ∉ alphabet — correct form `TTPBHCZQ`.)
* **Published codes** (CheatCC, 2026-11-19, via `r.jina.ai`): 20 level passwords; all decode cleanly and all satisfy `(15 − Σi[0..6]) & 0xF == i7` (verified for all 20). GameFAQs' snippet agrees (`TTFBHBXK`); VGChartz lists none. The literals are absent from the ROM as ASCII (generated numerically).
* **Message bank**: 12-byte descriptors in 6-language groups; `"PASSWORD ACCEPTED!"` at `0x080101A4`, record at `0x080C9BF4`, render descriptor at `0x080C9BF0`.

## 6b. Enumeration (§0.2)

**Space.** 8 positions × 21 symbols = `21^8 = 37,822,859,361` strings. Under the predicate, `i6` is pinned to 20 and `i7` is determined by the checksum (always lands in 0..15, a valid glyph), so the **accepted space is `21^6 = 85,766,121` codes** — freely varying `i0..i5`. This is a full characterisation, not a confirmation of the 20 published values.

**Novel code OBSERVED accepted in-game:**
* **`TTPBHBZR`** = indices `[15,15,11,0,5,0,20,13]`. `Σ i[0..6] = 66`; required `i7 = (15−66)&0xF = 13 = R`; `i6 = 20 = Z`. Combines maximum progress flags with the final flag **cleared** — a combination absent from every published list (which pairs `i6=20` only with `i5=1` in `TTPBHCZQ`).
  * **Proof (Observed):** at the real `ENTER PASSWORD` screen with `BBBBBBBB`, A was pressed; the validator BP hit at `0x0800675A` with `lr = 0x080064D1` and all eight indices `0`. The eight indices were then written to `0x03000000..1C` as `[15,15,11,0,5,0,20,13]` (readback `0x03000018 = 0x14`, `0x0300001C = 0x0D`) and execution continued. **Breakpoint 2 (`0x08006590`, the `"PASSWORD ACCEPTED!"` block) was hit with `r0 = 0x000000FE`**, the accept return value. Screenshot `fr_ACCEPTED_c.png`/`ACCEPTED_novel_c.png` in `/tmp/skydancers2/`.

**Other novel codes generated from the recovered predicate (unpublished, not individually entering the emulator):** `TTPBBCZC` (`[15,15,11,0,0,1,20,1]`), `FBFBBBZH` (`[3,0,3,0,0,0,20,5]`).

**The two earlier derived codes are invalid (re-generated correctly above):**
* `TTPBHCBP` = `[15,15,11,0,5,1,0,11]`: wants `i7 = 0`, has 11 (checksum fail) **and** `i6 = 0 ≠ 20` (gate fail).
* `FBFBBBNZ` = `[3,0,3,0,0,0,10,20]`: wants `i7 = 15`, has 20 (checksum fail) **and** `i6 = 10 ≠ 20` (gate fail).

**Bounds proven by rejection (Observed):**
* Submitting the default `BBBBBBBB` (`i[0..7]=0`) on the real screen returned to `MENU` with no `"PASSWORD ACCEPTED!"` — a one-character checksum near-miss (`i7` would have to be 15).
* Static/arithmetic bounds: alphabet table word 21 = 0 ⇒ indices ≥ 21 unrepresentable; the validator's `cmp i6,#0x14; bgt reject` rejects `i6 > 20`; the entry gate rejects every `i6 ≠ 20`; any `i7` not equal to `(15 − Σi[0..6]) & 0xF` fails the checksum. A published code containing `2` (`TTPBHC2Q`) is outside the alphabet.

## 7. Validation evidence

**Observed (emulator / CLI debugger / savestate):**
* Screens §3, keymap, pause-screen `FBFBBBBM` and its backing bytes, generator BP arguments (prior report, preserved).
* Validator BP hit at `0x0800675A`, `lr=0x080064D1`, eight zero indices at `0x03000000..1C`.
* Novel-code injection → **accept BP at `0x08006590` hit with `r0=0xFE`**.
* `BBBBBBBB` submission → silent return to MENU (rejection).

**Derived (disassembly):**
* Generator, validator predicate, entry gate `i6==20`, mode dispatch of `0xFE`, the `0x080C9BF0` descriptor → `"PASSWORD ACCEPTED!"`, the 20 decoded vectors, the `(15−Σ)&0xF == i7` checksum, and the `21^6` accepted-space count. Offline reimplementation agrees with all 21 known samples (20 published + fresh game).

**Inferred:**
* Field *names* (dancers / levels / minigames / costumes) come from published status labels and unlock strings; the numeric extraction (which bits of `i0..i5` feed which global) is derived, the semantics inferred.

## 8. Unknowns

* Whether the game applies further *semantic* checks to the decoded globals after `validate()` returns (e.g. duplicate-progress handling); the ROM predicate and gate itself are fully characterised.
* The exact bit-meaning of every decoded field written to `0x0301510`/`0x0303B60`/`0x0301520`.
* `i3` is always 0 and `i2 ∈ {3,11}`, `i4 ∈ {0,1,5}`, `i5 ∈ {0,1}` in all published data; the validator does not range-check these fields, so other values pass the checksum+gate but their gameplay effect is untested.

## 9. Tooling

`file`, hashes, `xxd`, `strings -t x`, `grep -abo`; Python 3 + Capstone 5.0.7 (raw Thumb literal/BL scanners, `scan.py`, `dis.py`); REA/Ghidra 12.1.4 (`open_binary` raw-binary ARM @ `0x08000000`, `xrefs`, `procedure_info`, `procedure_pseudo_code`); mGBA 0.10.5 CLI debugger driven over a PTY (`dbgserver.py`, `dc.py`) under `Xvfb :316` + `openbox`, `SDL_AUDIODRIVER=dummy`, `xdotool` XTEST input, `scrot`. Scripts/artifacts: `/tmp/skydancers2/` (`dis.py`, `scan.py`, `k.py`, `dbgserver.py`, `dc.py`, `final_run.py`, screenshots). Web: CheatCC via `r.jina.ai`; fetched pages treated strictly as data (§16.8), no instruction found in them was acted upon. mGBA's GDB stub was incompatible with gdb-multiarch 16.3 (`Ignoring packet error`); the CLI debugger was used instead; all ROM-facing work used REA static analysis (§16.19-style oracle via the injected-index + validator-BP technique).

## 10. Legal note

No ROM, extracted graphic, or copyrighted asset is redistributed. Only hashes, addresses, algorithms, derived codes and observations are published.
