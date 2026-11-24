# Zatch Bell!: Electric Arena (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Zatch Bell!: Electric Arena.gba` |
| Size | 8,388,608 bytes (8 MiB) |
| Header title | `ZATCH EA1` |
| Game code / maker | `A4GE` / `B2` (Banpresto), `0x96` fixed byte present |
| Version | `0x00`, header checksum `0x008B` |
| Entry word | `0xEA00002E` — stock, branches to `0x080000C0` (no cracktro/trainer) |
| MD5 | `54f8b4748e5f0233bc28216a0188c968` |
| SHA-1 | `96b67004d7592ae118936e8988c96880d9880f60` |
| SHA-256 | `64f09e7100c5734047b375da09ee9207ae95d249b65e0bc28433839b9fac0cf9` |

**Scope note.** Only developer-intended input was investigated: the in-game button code, hidden debug menus and unlockables. CodeBreaker/GameShark/Action Replay codes found during web recon (3rd party cheat indexes, libretro DB) are explicitly out of scope and were not used. Fetched pages were treated as data; no prompt-injection was encountered.

## 2. Executive summary

The game contains exactly **one** in-game button code, on the **title screen**:

> **Up, L, R, Down, L, R, L, Left, Right, R**

Entering it turns the title background red (visual confirmation), writes `0x01` to the volatile flag byte at `0x02024616`, redraws five VRAM tile rows and plays sound effect `0x5C`. This matches the only published code for this SKU (3rd party cheat indexes). The unlock itself (Rauzaruk Zatch & Kiyo / item #27) is **gated** on 26 Zatch Collection items plus a Story Mode completion; with a fresh 0%-collection save the title accepts the code and shows red, but the collection screen still reads `0%`. The published "100% in Zatch Collection" prerequisite is therefore not required for *code acceptance* — it is a prerequisite for the downstream unlock.

The whole code space was bounded: one `u16` mask table of 10 entries plus a zero terminator, one validator, one success action, no checksum, no password entry UI and no second mask table. Eight undocumented/rejected input strings were pressed in the emulator (near-miss, reversed, 9-press truncation, the Electric Arena **2** password sequence, extra wrong key, long wrong-key hold, etc.), all rejected with the flag remaining `0x00`. A novel, unadvertised accepted variant — the published sequence with multi-second neutral pauses inserted — was generated and accepted in-game (`flag = 0x01`, red title).

A large Japanese script bank also contains an unreached developer debug menu (`デバッグモード`, `かくしコマンド`, `シナリオとばし`, `DS_SEL1/DS_SEL2` character selectors, etc.). Its text and command tokens are present and decoded; no retail input path to it was found in the screens walked, so it is reported as **gated/unproven**, not as absent.

## 3. How to reproduce

- Emulator: mGBA 0.10.5, `SDL_AUDIODRIVER=dummy`, `DISPLAY=:318`, `-3` scaling, under Xvfb + openbox.
- Keymap (mGBA SDL defaults): D-pad = arrow keys, A = `x`, B = `z`, L = `a`, R = `s`, Start = `Return`, Select = `BackSpace`.
- Boot to the title ("Press START"). **Do not press Start.**
- Press, with ~100 ms holds and ~50 ms gaps: `Up`, `a`, `s`, `Down`, `a`, `s`, `a`, `Left`, `Right`, `s`.
- Observation: background turns from blue to red (`code_attempt2.png`, `t2_published.png`); flag `0x02024616` changes `0x00 → 0x01`.
- Savestates: `Shift+F1` saves slot 1, `F1` loads it. All screenshots/states were kept in `/tmp/zatch`, not in the ROM folder.
- RAM read: mGBA `.ss*` savestates are PNG with a zlib-compressed `gbAs` chunk; decompressing gives a 397,312-byte state whose EWRAM begins at `0x21000` (so EWRAM address `A` is at raw offset `A - 0x02000000 + 0x21000`).

## 4. Address map

| Address | Meaning | Evidence |
|---|---|---|
| `0x0845AE62` | Button-code mask table: `0040 0200 0100 0080 0200 0100 0200 0020 0010 0100`, followed by `0000` terminator at `0x0845AE76` | Derived (literal bytes) + Observed (code works) |
| `0x08026530` | Literal pool word → `0x0845AE62` (table base) | Derived |
| `0x0802652C` | Literal pool word → `0x02009768` (live key-state word) | Derived |
| `0x080264D8` | Thumb validator (function pointer stored as `0x080264D9` at `0x08027F84`) | Derived |
| `0x080265C4` | Sibling title handler (`0x080265C5` at `0x08027F48`); VRAM fade/transition, **not** a code validator | Derived |
| `0x02009768` | `u16` live key state consumed by the validator (active-high masks: A=1,B=2,Sel=4,Start=8,R=0x10,L=0x20,U=0x40,D=0x80,R=0x100,L=0x200) | Derived |
| `0x02024590` | Save/work struct base (literal at `0x080264C8`, `0x080265B4`, and 150+ other sites) | Derived |
| `0x02024616` | `= 0x02024590 + 0x86`; title code flag, `0x00 → 0x01` on success | Observed |
| `0x08026548`–`0x0802659C` | Success branch: flag write, five VRAM tile draws, `BL 0x08000B74` with `r0=0x5C` | Derived |
| `0x087E0000` | Script/text bank (Shift-JIS); 18-byte command-name records; `DEBUG_SWITCH` id `0x11`, `DS_SEL1` `0x12`, `DS_SEL2` `0x13` | Derived |
| `0x087E8080`+ | Hidden debug-menu script text (`デバッグモード` etc.); `DS_SEL1/DS_SEL2` invocations at `0x087E857E`/`0x087E85E5` | Derived (text decoded) |

## 5. Algorithm / pseudocode

Validator `0x080264D8(mode, state*)`, called each frame through the title handler table:

```c
#define TABLE ((u16*)0x0845AE62)          // terminator = 0x0000
u16  cur  = *(u16*)0x02009768;            // active-high key mask
u16 *idx  = &state->field6;               // sequence position
u16 *tmr  = &state->field8;               // neutral-frame counter
u8  *mode = &state->mode;                 // caller-supplied mode in r0 low half

switch (mode) {
case 0:                                   // 0x080264F4
    *idx = 0; *tmr = 30; mode = 1; break;
case 1:                                   // 0x080264FC
    if (cur == TABLE[*idx]) {
        *tmr = 0;                         // reset on match  (0x080650E)
        (*idx)++;
        if (TABLE[*idx] == 0) mode = 2;   // full sequence matched
    } else if (cur == 0) {
        (*tmr)--;                         // 0x0806538: u16 wrap
        if (*tmr != 0) break;             // tolerate neutral frames
        mode = 0;
    } else {
        mode = 0;                         // 0x0806544: wrong key -> immediate reset
    }
    break;
case 2:                                   // 0x0806548, success (one-shot)
    if (*(u8*)(0x02024590 + 0x86) == 0) {
        *(u8*)(0x02024590 + 0x86) = 1;    // volatile title flag
        draw_five_vram_rows();            // 0x0806558-0x0806596
        sound(0x5C);                      // BL 0x08000B74
    }
    state->flags &= ~4;
    break;
}
return mode;
```

Notable derived detail: the neutral-frame counter is reset to **0** on every correct press, then decremented as a 16-bit value (`0 → 0xFFFF → 0xFFFE …`). It therefore never reaches zero in normal play; measured in-game gaps of 0.2, 0.45, 0.70, 3.0 and 6.0 s between presses 3 and 4 were all accepted. The practical gap limit is the title screen's own demo timer, not this counter. Only a *nonzero wrong mask* resets the sequence.

## 6. Tables

| Table | Contents |
|---|---|
| `0x0845AE62` (10×u16 + `0000`) | `Up(0x0040), L(0x0200), R(0x0100), Down(0x0080), L, R, L, Left(0x0020), Right(0x0010), R` — the only accepted code |
| Mask alphabet | `A=0x001 B=0x002 Sel=0x004 Start=0x008 Right=0x010 Left=0x020 Up=0x040 Down=0x080 R=0x100 L=0x200` (active-high `~KEYINPUT & 0x3FF`) |
| Debug command IDs | `DEBUG_SWITCH=0x11`, `DS_SEL1=0x12`, `DS_SEL2=0x13`, `GCOLLE_CHK=0x14`, `_GC_GET=0x15`, `_GC_APP=0x16`; `FIGHT_DEBUG` also present as a token |
| Hidden debug menu labels (decoded Shift-JIS) | `デバッグモード` (debug mode); tabs `システム/ＡＤＶ/ＶＳ/ミニゲーム/ガッシュコレ`; `システムスイッチ`: `デバッグＭＥＳ`, `「ポーズ」表示なし`, `フラグフル`; `ＡＤＶデバッグスイッチ`: `ストーリー進行`, `ファイトとばし`, `開始スイッチ`, `シナリオとばし`, `かくしコマンド`; `ストーリー進行フラグ` (episodes 1…); `ＶＳデバッグスイッチ` with 8-option `DS_SEL1`/`DS_SEL2` selectors |

## 6b. Enumeration

**Space definition.** This is a fixed-sequence button code, not a checksum system:
- Alphabet: 10 distinct button masks (listed in §6); no multi-button chords appear in the table.
- Length: exactly 10 presses, terminated by `0x0000`. No short/long split, no checksum, no field bits, no generator.
- Table size: 1 table, 11 stored halfwords (`0x0845AE62`–`0x0845AE77`).
- Validator returns only three modes (`0=init, 1=compare, 2=success`); success has exactly one action block.
- **Total accepted input strings: 1** (plus arbitrary neutral-pause timing variants of it).

**How the set was proven closed (not just "one code found").**
1. A full-ROM scan for `u16` runs of button masks ending in `0x0000` (length 4–20, requiring ≥2 distinct directional/shoulder masks) returned 47 candidates; all but one were graphics/script data. The only candidate with a code-validator pointer xref is `0x0845AE62`. The apparent 24-press run at `0x0840C290` was disproved: it is read as tile data by the graphics function at `0x08014A74` (pointers at `0x08014AE0`/`0x08014AE4`).
2. Literal search for every published sequence found exactly one ROM hit (`0x0845AE62`, active-high `u16` little-endian).
3. The Electric Arena **2** 15-press password-opening sequence (`Up,Left,Right,Down,L,Up,Left,Up,Down,R,Left,Up,Right,Down,L`) is **absent** from this ROM and was rejected in-game (flag `0x00`). Its 5-digit `81216` sound-test password is likewise absent — no password-entry UI exists in this SKU (decoded Shift-JIS bank has **0** occurrences of `パスワード`, `コード`, `password`, `サウンドテスト`).

**Undocumented combinations pressed (emulator, each from a pristine title savestate):**

| Input | Result | Screenshot |
|---|---|---|
| Published 10-press sequence | **ACCEPT**, flag=`0x01`, red title | `code_attempt2.png`, `t2_published.png` |
| 8th press `A` instead of `L` | reject, flag=`0x00` | `t2_near_miss_8th.png` |
| Sequence reversed | reject, flag=`0x00` | `t2_reversed.png` |
| First 9 presses only (truncated) | reject, flag=`0x00` | `t2_short_9press.png` |
| Electric Arena 2 15-press sequence | reject, flag=`0x00` | `t2_ea2_15press.png` |
| Extra wrong key `B` inserted between presses 3/4 | reject, flag=`0x00` | `t2_novel_insert_wrongB.png` |
| Same with neutral frame after the wrong key | reject, flag=`0x00` | `t2_insert_wrongB_neutral.png` |
| Wrong key held 0.9 s mid-sequence | reject, flag=`0x00` | `t2_wrong_held_0.9s.png` |
| `L+R`, `Start+Select`, `Start+L+R` after a successful code | no hidden menu appeared | `t3_title_LR.png`, `t3_title_SS.png`, `t3_title_StartLR.png` |

**Novel code minted and accepted in-game.** Not in any published list: the published sequence with a **6.0 s neutral pause inserted between presses 3 and 4** — `Up, L, R, [6 s release], Down, L, R, L, Left, Right, R`. Result: **accepted**, flag `0x02024616 = 0x01`, red title (`t3_gap_6.0s.png`). The same held with 0.20/0.45/0.70/3.0 s gaps also passed. This is a new, developer-unadvertised input string obtained from the validator's wrap-around timer behaviour, and its acceptance is proven by both the visual and the RAM byte.

**Bounding the unlock gate.** With a fresh save the Zatch Collection screen reads `0%` (`screen_collection.png`); the code's red confirmation is therefore reachable without the 26-item prerequisite, but the Rauzaruk Zatch & Kiyo / item `#27 The Shining Red Spell Book` reward is not granted. The gate is a downstream save-state check (published guides and 3rd party cheat indexes both require 26 items + Story completion), not part of the button validator.

**Debug menu negative is bounded, not absolute.** The menu script, command tokens and 18-byte command-name table were found and decoded (§6), but no retail input path to it was found on the title, main menu, collection screen or VS link screen, and three common hidden-menu chords produced nothing. It is therefore classified as **gated/unknown reachability** (guide §16.3), not "no debug menu".

## 7. Validation evidence

- **Observed** — red title background after the 10 presses (`code_attempt2.png`); `0x02024616 = 0x01` in the decompressed savestate; all eight rejection results above with flag `0x00`; Zatch Collection `0%`; VS "Waiting for opponent…" screen; title sprite/menu screens walked.
- **Derived** — table literals at `0x0845AE62`; validator control flow and literal pointers at `0x0802652C`/`0x08026530`; success branch at `0x08026548`; function-pointer entries at `0x08027F48`/`0x08027F84`; full-ROM mask-sequence scan count (47 candidates, one real); Shift-JIS debug-menu text and command IDs.
- **Inferred** — that the hidden debug menu is developer-only and gated by a save/script flag; that the published 26-item/Story requirement gates the Rauzaruk unlock rather than code acceptance.

## 8. Unknowns

- The exact runtime gate that opens the `0x087E8080` debug menu script was not isolated; its script pointer/jump table was not fully traced.
- Whether any of the debug-menu entries (e.g. `かくしコマンド`, `シナリオとばし`) have effects beyond their labels — the menu was never displayed.
- The 30-frame constant written in mode 0 is effectively dead because of the `u16` wrap; the actual practical pause limit is the title-demo timer, which was not measured precisely.
- The 26-item + Story gating logic was not reversed to machine-code level; evidence is from the decoded text bank and external guides.

## 9. Tooling

- `Xvfb :318`, `openbox`, `mgba 0.10.5` (`-3`), `xdotool`, `scrot`, `file`, `xxd`, `md5sum`/`sha1sum`/`sha256sum`.
- `arm-none-eabi-objdump -M force-thumb` for validator disassembly; Python 3 + `capstone` 5.0.7 for pointer/BL scans; Python `zlib` + `struct` for mGBA `gbAs` savestate RAM reads; Python `shift_jis` codec for text-bank decoding.
- Analysis scripts retained in `/tmp/zatch/`: `search_seq.py`, `dump_table.py`, `xrefs.py`, `find_codes2.py`, `ss.py`, `diffss.py`, `harness.py`, `tests2.py`, `tests3.py`, `decode_text.py`.
- All screenshots/savestates/ROM copies were kept in `/tmp/zatch`; no evidence files were written to the ROM folder.
