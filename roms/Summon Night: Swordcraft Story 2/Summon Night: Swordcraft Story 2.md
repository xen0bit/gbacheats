# Summon Night: Swordcraft Story 2 (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Summon Night: Swordcraft Story 2.gba` |
| Size | 16,777,216 bytes (`0x01000000`, 16 MiB) |
| Header title | `SWORDCRAFT2` |
| Game code | `BSKE` (file says `BSKEEB`) |
| Maker | `EB` (Banpresto) |
| Version / complement / checksum | `0x00` / `0x74` / `0x0000` |
| Entry word | `0xEA00002E` — **stock** crt0 branch (not a cracktro, guide §16.1) |
| MD5 | `03eea2d57de9c16b5f10055e8e4e2893` |
| SHA-1 | `cbc4382b1fff2e1b2d3112ae8fbf290aec662121` |
| SHA-256 | `e267f052a3f138534f198bd33992d640568f80bf807e322c85c7b4cf6dd504ac` |
| Region / SKU | USA, `AGB-BSKE-USA` (CRC32 `1EAC1F48` per 3rd party cheat indexes) |

Single Nintendo logo hit at header offset `0x04`; this is one image, not a multigame pack.
Header checksum `0x0000` is the usual rebuilt-header artifact; the complement byte is intact.

## 2. Executive summary

This is a **save-flag unlockable** game, not a password game. There is no password entry
screen, no code alphabet, no validator and no button-code table. Every "cheat" published
for the USA SKU is a GameShark/CodeBreaker/AR ROM-write (out of scope for this engagement);
the only developer-intended cheat surface is the post-game **Extras** mode set and the
in-game **Options/Config** screen.

The Extras system was characterised end to end:

* the **title gate byte** `0x03000024` was isolated by savestate patching: `0` → no extra
  label, `1` → `Continue`, **`≥2` → `Extras`** (observed for 2, 3, 4, 5, 7, 16, 255).
* the Extras **menu itself** is built by the routine at `0x08053580` from a **9-entry
  pointer table at `0x084E0334`** and a **9×u16 flag-mask table at `0x0809173A`**.
  Six entries are gated by flag bits `0x0008, 0x0010, 0x0020, 0x0040, 0x0080, 0x0100`;
  three (`Rival Rush`, `Save`, `Exit`) are unconditional. The flag word is read as a
  signed 16-bit value at `struct+0x76`, where `struct` is the pointer stored at
  `0x030068A4`.
* Seven gameplay modes are named in the decoded fullwidth-Shift-JIS text bank.

The game text is **not ASCII**: it is Shift-JIS fullwidth Latin (e.g. `Ｒａｂｂｉｔ
Ｒａｍｐａｇｅ` = bytes `82 52 82 61 ...`). Decoding that bank is what exposed the Extras
labels; a plain `strings` scan returns nothing useful (guide §11).

**Gates and limits (honest):** entering the mode-select list requires a *cleared save* to
be loaded — the struct pointer at `0x030068A4` was `0x55555555` (uninitialised) on the
fresh title screen, so the builder never had a valid flag word. Reaching a real cleared
save would require completing the game; consequently the per-bit → per-mode mapping
below is **Derived** from the builder's mask table, and the title gate effect is
**Observed**. This is a bounded gated-feature result (guide §16.3 case 4), not a claim
that all seven modes were played.

## 3. How to reproduce

* mGBA 0.10.5 under Xvfb `:319`, `SDL_AUDIODRIVER=dummy`, `mgba -3 game.gba`.
* Keymap: A=`x`, B=`z`, Start=`Return`, Select=`BackSpace`, L=`a`, R=`s`, D-pad=arrows.
  Use single `xdotool key` taps with ≥150 ms gaps; 150 ms *holds* double-step menus.
* Boot: intro → `PRESS START` → `Return` → `New Game` → data slot → character select →
  name entry → story auto-dialogue (~300 A taps) → field.
* In-field `Start` opens the 10-entry COMMAND menu (6 on page 1; move to the `▶` row and
  press A for page 2).
* To reproduce the title gate: take a savestate on the title screen (mGBA slot 1),
  decompress the PNG `gbAs` chunk, write byte `0x02` at state offset `0x19024`
  (= IWRAM `0x03000024`), recompress, reload with `F1`, press `Start`. The `Extras`
  label appears. `patch_state.py` in the work dir automates this.
* Savestate RAM layout used (16 MiB ROM): `gbAs` zlib chunk → 397,312-byte state;
  IWRAM `0x03000000`→`0x19000`, EWRAM `0x02000000`→`0x21000` (guide §16.13).

## 4. Address map

| Address | Type | Meaning | Evidence |
|---|---|---|---|
| `0x08000000` | code | stock ARM entry (`0xEA00002E`) | Derived |
| `0x0800D7BC` | code | joypad reader; `ldrh` from `0x04000130`, pressed/held/released into `0x03004050/64/68/6C` | Derived (disasm) |
| `0x080534F4` | code | Extras scene dispatcher; switches on `struct+0x0C` → sub-scene functions `0x08053574/3734/3780/37C8/3810…` | Derived |
| `0x08053580` | code | **Extras menu list builder**: loops indices 0–8, `ands` each mask with flag word | Derived |
| `0x084E0334` | table | 9 pointers to Extras menu labels (reverse-visible order) | Derived |
| `0x0809173A` | table | 9×u16 masks `{0x0008,0,0x0010,0x0020,0x0040,0x0100,0x0080,0,0}` | Derived |
| `0x030068A4` | RAM | pointer to the game's work/save struct (uninitialised `0x55555555` without save) | Observed (savestate) |
| `struct+0x76` | RAM | signed 16-bit Extras unlock flag word | Derived |
| `0x03000024` | RAM | **title gate byte**: 0 = none, 1 = `Continue`, ≥2 = `Extras` | Observed |
| `0x020001A8` | RAM | published CB "all extras" word — **does not** change the title indicator | Observed (rejected) |
| `0x030003DA` | RAM | published GS "all extras" halfword — **does not** change the title indicator | Observed (rejected) |
| `0x08F924`–`0x08FBA8` | text | fullwidth-SJIS UI bank (save prompt, Extras labels, descriptions) | Decoded |
| `0x092CC0`–`0x093000` | text | ASCII debug-style labels `HP MAP MONEY … <SOUND> <MOVE> <COLOR> <BRIGHT> DEFAULT` — these are the **Config/Options** screen labels, not a hidden debug menu | Decoded |

## 5. Algorithm / pseudocode

```c
// Extras list builder, 0x08053580
struct = *(u32*)0x030068A4;
flags  = *(s16*)(struct + 0x76);          // sign-extended
u16 masks[9] = {0x0008,0x0000,0x0010,0x0020,0x0040,0x0100,0x0080,0x0000,0x0000};
char **labels = (char**)0x084E0334;       // 9 entries
for (int i = 0; i <= 8; i++) {
    if (i == 1 || i == 7 || i == 8) {       // always present
        add_row(labels[i], i); continue;
    }
    if (masks[i] & flags) add_row(labels[i], i);
}
```

```c
// Title gate (empirical, 0x03000024)
switch (gate) {
  case 0: show_none();        break;
  case 1: show("Continue");   break;
  default: show("Extras");    break;   // every value >=2 tested
}
```

## 6. Tables

### 6.1 Extras menu entries (decoded from `0x08F9xx` / `0x084E0334`)

| Index | Label (ROM string) | Mask | Availability |
|---:|---|---|---|
| 0 | `Sound Test` (`0x0808FA48`) | `0x0008` | gated |
| 1 | `Rival Rush` (`0x0808FA30`) | — | always |
| 2 | `Boss Rush` (`0x0808FA1C`) | `0x0010` | gated — complete summon-beast encyclopedia + `Boss's Proof` |
| 3 | `GUNVALD vs. Borgrim` (`0x0808F9F4`) | `0x0020` | gated — clear all Gimmick Challenges + `Spectator Ticket` |
| 4 | `Summon Night 2: Cameo Battle` (`0x0808F9B8`) | `0x0040` | gated — max Craftsman rank + `Hero's Hammer` |
| 5 | `Gabriel Mode` (`0x0808F99C`) | `0x0100` | gated — clear game with the `Communicator` intact |
| 6 | `Rabbit Rampage` (`0x0808F97C`) | `0x0080` | gated — post-game Raging Rabbit + `Carrot Badge` |
| 7 | `Save` (`0x0808F970`) | — | always (UI button) |
| 8 | `Exit` (`0x0808F964`) | — | always (UI button) |

Unlock *conditions* in the right column are from published guides (3rd party cheat indexes/
Japanese wikis), treated as leads; the bits and labels are from the ROM.

### 6.2 In-game COMMAND menu (walked in emulator)

Page 1: `Equipment`, `Support`, `Item`, `Magic`, `Weapon`, `Status`, `▶`.
Page 2: `Quest Items`, `Techniques`, `Bestiary`, `Options`. Total **10** entries.
No hidden eleventh entry; the `▶` is a page-scroll row, not a cheat.

### 6.3 Published codes (rejected as out of scope / unverified as in-game inputs)

All fetched material is GameShark/CodeBreaker/AR ROM patches: max money/HP/items, enemy
modifier, "Access All Extras" (`820001A8 FFFF / 33000024 0002`), "Access Extras Menu"
(`73000024 0001 / 33000024 0002`), "Mono Shift [Press Select+Up]"
(`74000130 03BB …`). The `74000130 03BB` is a **cheat-device activation condition**, not
evidence of an in-game Select+Up shortcut. No published *typed* password exists for this
SKU. The literal search for `0x03BB` in ROM found one hit (`0x080CD0F4`) inside a
compressed/high-entropy region whose disassembly is nonsense — not a validator.

## 6b. Enumeration

### Code-space definition

There is **no code space to enumerate**: no alphabet, no fixed-length input, no checksum,
no comparison table and no entry screen exist. Bounded negative evidence:

* **Screens walked:** boot intro, `PRESS START`, title menu, data-slot select (2 slots),
  character select, name entry (alphabet `A-Z a-z 0-9 ., ' ? !` — a *name field*, not a
  validator), story dialogue, field, COMMAND menu pages 1 and 2. No password/cheat entry
  surface appears anywhere.
* **String search counts (whole 16 MiB):** ASCII `PASSWORD` 0, `CHEAT` 0, `SECRET CODE`
  0, `CODE` 0, `DEBUG` 0, `GAMESHARK` 0, `CODEBREAKER` 0, `UNLOCK` 0, `MASTER CODE` 0.
  Fullwidth-Shift-JIS `ＰＡＳＳＷＯＲＤ`, `ＣＨＥＡＴ`, `ＣＯＤＥ`, `ＳＥＣＲＥＴ`,
  `ＤＥＢＵＧ`, `パスワード`, `裏技`, `デバッグ`, `コード` — all 0. The only debug-looking
  hits (`<SOUND>`, `<MOVE>`, `<COLOR>`, `<BRIGHT>` at `0x08092D30`–`0x08092D68`) belong
  to the ordinary Config/Options screen and have ordinary pointer-table xrefs
  (`0x08078E20` etc.), so they are not a hidden menu (guide §16.7/§16.8: keyword hits need
  context).
* **Button-code search:** the only joypad reader is `0x0800D7BC`; it computes
  `pressed = ~KEYINPUT & 0x3FF` into IWRAM and contains no sequence matcher, no mask
  array and no progress counter. No 3-press mask table was found in the code region.

### Enumerated unlockable space (the actual developer-intended content)

* **Gate byte `0x03000024` — 256-value domain enumerated by sampling 0, 1, 2, 3, 4, 5,
  7, 16, 255:** 1 value gives no label, 1 gives `Continue`, 9 tested values `≥2` give
  `Extras`. Acceptance is a **threshold**, not an equality.
* **Flag word — 16 bits, 6 meaningful:** mask domain `0x0008 | 0x0010 | 0x0020 | 0x0040
  | 0x0080 | 0x0100 = 0x01F8`; 6 bits → 64 distinct mode combinations; bits `0x0001`,
  `0x0002`, `0x0004` and bits ≥`0x0200` are **unused by the builder** (aliases).
* **Novel values accepted in-game:** `0x03000024 = 3, 4, 5, 7, 16, 255` are accepted by
  the title screen and render the `Extras` label; none of these appear in any published
  list (which always uses `2`). Screenshots: `gate_3.png`, `gate_4.png`, `gate_5.png`,
  `gate_7.png`, `gate_16.png`, `gate_255.png` in the work dir.
* **Bounds proven by rejection:** `0x03000024 = 0` rejects the `Extras` label entirely;
  `1` yields only `Continue`. Setting the two other published "all extras" addresses
  alone (`0x020001A8 = 0xFFFF`, `0x030003DA = 0xFFFF`) was rejected — no `Extras` label
  (`iso_ewram.png`, `iso_iwram.png`). This isolates the gate to `0x03000024`.
* **Not reached:** the mode-select list itself (needs a cleared save, see §2). The
  9-entry count, 6-bit mask map and all seven mode labels are therefore a *closed static
  enumeration* of that menu; playing each mode is out of reach without game completion.

## 7. Validation evidence

* **Observed:** emulator screenshots of every enumerated screen; the `Extras` label
  appearing/disappearing under controlled savestate patches; isolated gate tests;
  savestate RAM reads at `0x03000024`, `0x030068A4`, `0x020001A8`, `0x030003DA`;
  10-entry COMMAND menu walk.
* **Derived:** Thumb disassembly of `0x080534F4`–`0x080537xx`, the pointer table at
  `0x084E0334`, the mask table at `0x0809173A`, the Shift-JIS text bank decode, and the
  absence of `strcmp`/table comparisons against the name-entry buffer.
* **Inferred:** which real-world achievement sets each flag bit (from published guides);
  the exact per-bit → per-mode wiring is fixed by the mask table but was not exercised
  on the mode-select screen.

## 8. Unknowns

* How the six flag bits are *set* by normal play (the writers of `struct+0x76` were not
  located); the published unlock conditions are leads only.
* Whether the mode-select screen, once entered, adds/clamps entries beyond the 9 built
  rows (the builder's `ip` counter would need a live run with a cleared save).
* Exact semantics of gate values `≥3` (all render `Extras`; a deeper menu may distinguish
  them). No cleared save was available to test.
* No attempt was made to finish the game to obtain a genuine cleared save.

## 9. Tooling

* `mgba` 0.10.5 (Xvfb :319 + openbox, `SDL_AUDIODRIVER=dummy`), `xdotool`, `scrot`,
  ImageMagick `montage`/`convert`.
* `arm-none-eabi-objdump -M force-thumb` for raw Thumb disassembly; Python `capstone`
  available but not needed for the final scans.
* `patch_state.py` (work dir `/tmp/summonnight2`) — rewrites the zlib `gbAs`
  chunk of an mGBA `.ss1` savestate; RAM mapping `IWRAM +0x19000`, `EWRAM +0x21000`.
* REA/Ghidra 12.1.4 was opened on the ROM for cross-checking; raw-image auto-analysis
  created no function at `0x08053580` (known Thumb/raw-import limitation, guide §5.5), so
  the menu builder was read with `objdump` instead. Session closed after use.
* No GameShark/CodeBreaker/AR code was applied to the game; published codes were used
  only as reconnaissance leads, and savestate byte patches are analysis instrumentation,
  not a shipped cheat.

## 10. Legal note

No ROM bytes, graphics, music or game text are redistributed here. Only addresses,
hashes, decoded label names and tools are published.
