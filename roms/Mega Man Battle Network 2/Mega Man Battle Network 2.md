# Mega Man Battle Network 2 (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Mega Man Battle Network 2/Mega Man Battle Network 2.gba` |
| Size | 8,388,608 bytes (0x00800000, 8 MiB) |
| Header title | `MEGAMAN_EXE2` |
| Game code | `AE2E` (USA) |
| Maker | `08` (Capcom) |
| Version | 0x00 |
| Entry branch | `0xEA00002E` → `0x080000C0` (stock crt0) |
| Fixed 0x96 | present; complement `0x83` (unedited header) |
| Header checksum | `0x0000` (normal rebuild artifact) |
| MD5 | `39f8a42133df444eeb7bf0b2194d6286` |
| SHA-1 | `601b5012f77001d2c5c11b31304afafc45a70d0b` |
| SHA-256 | `61a8324c5179f0f8f6b0078aaa1237ea7ac0b3c5a8370c5ba8136c513a22cf2d` |
| Build stamp | `ROCKMANEXE2 20011016` at file `0x30D40` (matches 3rd party cheat indexes US offset) |

**Embedded-header scan:** a search for the exact 156-byte Nintendo logo found **exactly one** header, at file offset `0x0`. This is a single retail image — no appended trainer, no second game, no patch/cracktro. The entry word and the first 4 KiB are stock ARM crt0 code. No patch/trainer to report.

## 2. Executive summary

**No reachable in-game password/cheat menu, code-entry screen, or unlockable debug menu exists in this ROM.** Every screen reachable from a fresh boot and from the provided save was walked and RAM-verified (§4, §7): title logo, title menu (NEW GAME / CONTINUE only), intro, overworld, the nine-entry pause menu, Folder, Subchips, Library, MegaMan, Nail, Key Items, Network (Practice / NetBattle / Trade Chips, plus its two save prompts) and Save. There is no Options screen and no third title-menu entry; pressing Up five times at the title menu stays on a two-item ring.

All UI text is **font/tile-indexed**, not ASCII: `strings` returns only garbage and one coincidental `CHIP` inside compressed graphics. I located the game's 8×8 4bpp font tileset (file `0x0696000`, 192 tiles), decoded its index→character mapping, and searched the ROM for every plausible encoding of password/cheat/debug/secret keywords and of known UI strings — **zero meaningful hits**. 623 valid GBA-LZ77 blocks were decompressed; none contained those strings.

One **hard-coded button-code validator** does exist in the ROM (§4, §5, §6). Its table at `0x0801C7F8` encodes eight presses **Left, Left, Right, Left, Right, Left, Right, Right**, and completing it writes value `8` to script variable `0x85`. It is fully decoded from disassembly (Derived), but it is **gated behind save-integrity state**: with the valid 32 KB SRAM save the gate byte is 2, so the validator never runs; on a fresh/no-save game I entered the exact sequence on the title screen, in the pause menu and in the overworld and observed **no distinct effect** beyond ordinary input. It is therefore reported as a **gated/dead path in every reachable state tested** (guide §16.3, category 4), not as a usable cheat. No password alphabet, generator, or accepted-code table was found anywhere.

**Published codes:** 3rd party cheat indexes document **no in-game cheat or password** for this game — only an *external* GameShark "map warp" used to reach the unused "Last Room", which is out of scope. Searches of 3rd party cheat indexes/search engines were blocked by CAPTCHA/bot checks; no published in-game code literal was available to verify. This is recorded as an unresolved web-recon limitation, not a claim that codes exist.

## 3. How to reproduce

* Emulator: `mgba` (SDL build), `DISPLAY=:317`, `SDL_AUDIODRIVER=dummy`, started with `mgba -3 <rom>`.
  Note: starting with `-g` pauses the core at boot until a GDB client attaches in this build; use the non-`-g` build for screen walking.
* Keymap (mGBA SDL defaults): A=`x`, B=`z`, Start=`Return`, Select=`BackSpace`, L=`a`, R=`s`, D-pad=arrows. Hold 120–180 ms per press; menus need ~0.3–0.5 s to finish a fade before the next press registers.
* Deterministic input helper: `/tmp/mmbn2/helper.py` (`focus()`, `key()`, `shot()`; screenshots cropped to `720x480+155+163`).
* Screen path reproduced:
  1. Boot → logo (shot `t_title.png`).
  2. `Start` → title menu `NEW GAME / CONTINUE` (shot `t_title_start1.png`); Up×5 proves a 2-item ring (`t_title_up5.png`).
  3. `A` → `CONTINUE` → overworld; `Start` → pause menu (shot `m8_mainmenu.png`).
  4. From the pause menu, `A` on each entry in turn: Folder (`m_folder.png`), Subchips (`m2_subchips.png`), Library (`m3_library.png`), MegaMan (`m4_megaman.png`), Nail (`m5_nail.png`), Key Items (`m6_keyitems.png`), Network (`m7_network.png` → `Trade Chips` → `m7_tradeenter.png`), Save (`m9_save.png`). `B` returns to the parent.
  5. Button code tested: on title menu, pause menu and overworld, press `Left Left Right Left Right Left Right Right` with 180 ms holds; shots `code_title_after2.png`, `fresh_seq_after.png`.
* Savestates: `Shift+F1` / `F1` (slot 1); `Shift+F3`/`F4` for slots 3/4. States were parsed by `zlib.decompress` of the PNG `gbAs` chunk (helper `ssdiff.py`).

## 4. Address map

All ROM addresses are `0x08000000 + file_offset`.

| Address | Meaning | Evidence type |
|---|---|---|
| `0x08000000` | Stock ARM crt0 / entry | Derived (objdump) |
| `0x08030D40` | Build stamp `ROCKMANEXE2 20011016` | Observed (ROM bytes) |
| `0x0801C108` | Init of the button-code event object; called at boot from `0x0800043E` and from `0x08024B60` | Derived |
| `0x0801C184`–`0x0801C1D0` | Save-validity checks; set object bytes `[r5,#14]`/`[r5,#15]`; compute gate byte `[r5,#8] = min(checksum, byte9-1)` | Derived |
| `0x08030C90` / `0x08030CEC` | Save checksum over `0x02000000..0x0200773A` + 22, stored at struct `+0x2C` | Derived |
| `0x08030D1C` | Compares 20 bytes at `[sl+0x78]+0x78` with `ROCKMANEXE2 20011016` | Derived |
| `0x08030D90` | Reads 4-byte checksum from SRAM `0x0E007FFC` | Derived |
| `0x0801C3AC` | Object state handler (vtable entry), cycles cursor bytes `[r5,#6]` 0–17 and `[r5,#7]` 0–63 | Derived |
| `0x0801C442` | Caller of the button-code validator (gated on object byte `[r5,#15] != 0` and a script result of `0xEC`) | Derived |
| **`0x0801C7B8`** | **Button-code validator** (Thumb). Full listing in §5 | Derived |
| **`0x0801C7F8`** | **8-entry key-mask table** (`u16[8]`) | Derived |
| `0x08000598` | Thunk that calls `0x080E71C0(r0=0x85, r1=8)` — sets script variable `0x85` | Derived |
| `0x080E71C0` | Generic script-variable setter (index derived from `r0`) | Derived |
| `0x0696000` | Font tileset in ROM (192 × 8×8 4bpp tiles) | Observed (tile render) |
| `0x06008000` | VRAM location the font is loaded to; tile index = ROM tile index | Observed (VRAM dump) |
| `0x020089E0`, `0x020089E6`, `0x020089EC` | EWRAM active-high cached key state (Right press = `0x0010`) | Observed (savestate diff) |
| `0x04000130` | Raw KEYINPUT; `0x03FF → 0x03EF` while Right held | Observed (savestate diff) |

Savestate (`gbAs`) section layout used: header/CPU `0x00000`, palette `0x00800`, OAM `0x00C00`, VRAM `0x01000`–`0x18FFF`, IWRAM `0x19000`, EWRAM `0x21000` (guide §16.13).

## 5. Algorithm

The button-code validator at `0x0801C7B8`, reconstructed from `objdump -M force-thumb`:

```c
// r5 = event object, sl(r10) -> globals; [sl+4] -> struct with u16 key state at +2
void validator(u8 *obj) {
    if (obj[8] != 0) return;                 // gate: save-derived byte must be 0
    u16 keys = *(u16*)(globals->keystate + 2); // active-high button bits
    if (keys == 0) return;                   // require at least one button held
    int i = obj[10];                         // progress index
    u16 want = TABLE[i];                     // TABLE at 0x0801C7F8
    if (want == 0) return;                   // terminator
    if ((keys & want) == 0) { obj[10] = 0; return; }  // wrong press -> reset
    obj[10] = ++i;
    if (i == 8) set_script_var(0x85, 8);     // completion: r0=0x85, r1=8
}
```

TABLE (`0x0801C7F8`, `u16[8]`) = `0x0020, 0x0020, 0x0010, 0x0020, 0x0010, 0x0020, 0x0010, 0x0010`.
With GBA key bits (`Right=0x10`, `Left=0x20`) and the active-high cached state observed at `0x020089E0`, this is:

```
Left, Left, Right, Left, Right, Left, Right, Right
```

Semantics: edge/held is a **bitwise AND test** (`keys & want`), i.e. extra simultaneously-held buttons do not invalidate a press. The progress byte `obj[10]` is reset to 0 on the first mismatching press. Completion writes `8` to script variable `0x85` via `0x08000598 → 0x080E71C0`.

**Gate model (why it is not reachable with a valid save):**
`obj[8] = min(checksum, obj[9]-1)`, `obj[9] = obj[14] + obj[15] + 1`, where `obj[14]` and `obj[15]` are set only when both the save checksum (§4 `0x08030CEC`) and the 20-byte build-stamp magic (`0x08030D1C`) verify. With a valid save both are 1, so `obj[8] = 2` and the `if (obj[8]!=0) return` guard makes the validator inert. It would only run when both save checks fail (`obj[9]=1`, `obj[8]=0`) — a state no normal play path reaches from a valid or a fresh save in the tests performed.

## 6. Tables

| Table | Address | Contents |
|---|---|---|
| Button sequence | `0x0801C7F8` | `20 00 20 00 10 00 20 00 10 00 20 00 10 00 10 00` → L,L,R,L,R,L,R,R |
| Object vtables | `0x0801C218`–`0x0801C228` | `0x0801C21D, 0x0801C299, 0x0801C2C5, 0x0801C30D, 0x0801C319` (Thumb state handlers) |
| Font | `0x0696000` | 192 tiles; tile `0x40='0'…0x49='9'`, `0x51='A'…0x5A='J'`, `0x5B='K'…0x5F='O'`, `0x60='P'…`; lowercase/hiragana and symbols in remaining rows |
| Key cache | `0x020089E0` etc. | active-high; `Right=0x0010`, `Left=0x0020` |

No password alphabet table, no accepted-string table, and no code→effect table exists. Keyword/literal counts are in §6b.

## 6b. Enumeration

**Button-code space.** The only key-mask sequence table found has exactly **8 entries** and a single terminator test (`want == 0`); there is only **one** such validator function (BL count to `0x0801C7B8` = 1, from `0x0801C658`). The complete reachable action set of the gate is therefore `{no-op, reset, set-var(0x85)=8}` — there is no second dispatch branch and no hidden action (guide §5.4a step 5).

* Strict scan of the whole ROM for runs of ≥4 `u16` single-bit key masks found **130** runs; all but one are Thumb instruction streams or pointer/literal pools. The one plausible code table is `0x0801C7F8`.
* Broad scan allowing 2–3-bit masks found 724 runs; every hit was in executable code and disassembled as instructions/constants, not a second sequence table.
* The sequence was **entered in-game** (title menu, pause menu, overworld) — no distinct visible effect, no new flag write attributable to it in controlled A/B savestate tests (correct sequence vs. eight `A` presses from the same base state produced the same classes of RAM changes, i.e. only dialogue/sprite advancement).

**Password/text space (negative proven by counts).**

| Search | Space checked | Hits |
|---|---|---|
| `strings -n 4` case-insensitive for `password\|cheat\|secret\|unlock\|debug\|code\|menu\|invalid\|continue` | whole 8 MiB | 0 (only header `MEGAMAN_EXE2AE2E08`) |
| ASCII exact `PASSWORD`, `CHEAT`, `DEBUG`, `SECRET`, `MENU`, `CHIP`, `DECK`, `ENTER` | whole ROM | 1 coincidental `CHIP` at `0x181A8A` inside compressed graphics |
| `+0x20` lowercase→uppercase translation, same keywords | whole ROM | same single `CHIP` |
| UTF-16LE/BE, UTF-32LE/BE for the same keywords | whole ROM | 0 |
| Affine `byte+k`, `byte^k`, 16-bit LE/BE `+k` of known UI strings (`Folder`, `You have nothing`, `Trade BattleChips`, …) | whole ROM | 0 |
| LZ77 decompression of all `0x10`-header blocks | 623 blocks | 0 target strings |
| Known password alphabets (`0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ`, `BCDFGHJKLMNPQRSTVWXYZ0123456789`, …) | whole ROM | 0 (`0123456789` appears 4× coincidentally) |
| `strcmp`-style literal tables | scan for NUL-padded equal-length string runs | none |

**Published codes tested.** None available: 3rd party cheat index lists no in-game code; 3rd party cheat indexes/search engines were blocked. The external GameShark map-warp mentioned by 3rd party cheat indexes are not an in-game code and was not used.

**Conclusion of enumeration.** Code-space size for the one found system: 1 table × 8 masks; no mintable variant exists because the terminator is the only branch and the single effect has no parameterization. No novel code could be generated — the system is a fixed, gated sequence, and there is no password system to enumerate.

## 7. Validation evidence

* **Observed** (emulator / ROM bytes): hashes and header; exactly one embedded GBA header; every screen in §3; title menu has exactly NEW GAME/CONTINUE; Network → Trade Chips says "Your friend isn't ready yet…" (link-only, no code entry); KEYINPUT `0x03FF→0x03EF` on Right and active-high EWRAM cache `0x020089E0=0x0010`; font tiles rendered from ROM `0x0696000` and matched to VRAM `0x06008000`; no effect from entering the button sequence in reachable states.
* **Derived** (disassembly): validator at `0x0801C7B8`, its 8-entry table, its completion call to `0x08000598 → 0x080E71C0(0x85, 8)`, its save-validity gate, and the boot-time creation of its object.
* **Inferred** (not exercised): that setting variable `0x85` would unlock anything visible if the gate were open. No such state was reached, so this is explicitly **not** claimed as an observed cheat.

## 8. Unknowns

* The in-game meaning of script variable `0x85` and any consumer that reads it — the gate could not be opened in any reachable state, so the effect of a successful completion was never observed.
* Whether a save edited to fail both integrity checks while remaining playable would enable the sequence; the needed SRAM layout for such an edit was not fully established.
* Web sources other than the archived 3rd party cheat index page were inaccessible (CAPTCHA/bot blocks), so the absence of published codes could not be independently confirmed beyond 3rd party cheat indexes.

## 9. Tooling

* `arm-none-eabi-objdump -M force-thumb` for disassembly; Capstone 5.0.7 + Python for literal/BL scans.
* `strings`, `xxd`, Python `re`/`struct` for string and encoding scans; custom GBA-LZ77 decompressor `lzscan.py`.
* mGBA SDL under Xvfb `:317` with openbox; `xdotool` for input; `scrot` + ImageMagick crop for screenshots.
* `ssdiff.py` (zlib `gbAs` savestate diff) and `render_vram.py` (4bpp tile rendering) for RAM/font evidence.
* GDB stub (`mgba -g`, port 2345) was attempted but proved unreliable under concurrent use; savestate diffing was used instead (guide §16.13).
* No ROM or copyrighted assets are redistributed; only addresses, hashes, and the author's scripts are published.
