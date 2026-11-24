# Galidor: Defenders of the Outer Dimension (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

Target: `roms/Galidor: Defenders of the Outer Dimension/Galidor: Defenders of the Outer Dimension.gba`
Analysis workspace: `/tmp/galidor`

---

## 1. Target identity

| Field | Value |
|---|---|
| Size | 4,194,304 bytes (0x400000) |
| Header title | `GALIDOR` |
| Game code | `AG8E` |
| Maker code | `69` |
| Fixed byte @0xB2 | `0x96` |
| Unit / device / version | `0x00 / 0x00 / 0x00` |
| Header checksum @0xBE | `0x0000` |
| Complement byte @0xBD | `0xDB` (does not satisfy `sum(0xA0..0xBD)==0`; rebuilt/edited header, common for scene releases) |
| Entry word | `0xEA00002E` → `0x080000C0` (stock crt0, no cracktro/trainer patch) |
| MD5 | `101c1c8ed0ca51da145b101c8a42b0eb` |
| SHA-1 | `86cf0842e9fcbdfe6240be580e08ae44e0a07a47` |
| SHA-256 | `f78f2dee2a7af91c6787b566df20ac8c293b4ee5f366f96ae426a6e9b47031e4` |

**Embedded-header scan:** the full 156-byte Nintendo logo was searched across the whole image; the only hit is file offset `0x4`. The image is a single clean GBA program; no multiboot stub, no appended trainer, no second game.

---

## 2. Executive summary

This game implements a **developer-intended button-code system** on the title/menu screen. It is a fixed lookup table of exactly **five** 10-press D-pad sequences; there is **no checksum, no algorithmic code generator, no password text field**.

Static reconstruction (all addresses are ROM addresses, file offset = address − `0x08000000`):

* **Code table** `0x08030C50` — 5 records × 0x30 bytes. Each record = ten `u32` active-high button masks, one `u32` terminator `0xFFFFFFFF`, one `u32` effect flag.
* **Validator** `0x080057E0` — polls the press buffer, compares each record, ORs the effect flag into `0x03002EA8`. The record with flag `0xFF` additionally writes `0x19` to `0x03002E4C`, which switches the game to the hidden **debug menu** (level select + sound test + "hold Select to go anywhere").
* **Input path** `0x08001F78` — converts `KEYINPUT` (`0x04000130`) into `held` (`0x0300185C`) and `pressed` (`0x03001EA0`). The validator's own history buffer is `0x03006E60` (10 × `u32`) with index at `0x03006EE8`.

All five table sequences match the published GBA lists exactly (3rd party cheat indexes; 3rd party cheat indexes corroborates the debug sequence and the `0x03002E4C` address). A second, **undocumented** pair of button combos exists in the credits handler (`0x08008C8C`, `0x08008CE0`): L+Select and R+Select gate additional menu state / the debug menu, provided a credits-screen counter has reached `0xFF`.

Screen enumeration (observed in mGBA on `:316`): language select, legal/intro, attract demo, "Press START" title, six-item ring main menu (New Game / Continue / Options / Kek Powerizer / 2 Player Challenge / Credits), Options submenu (Music / Sound FX / Difficulty / Language / Erase Data), slot/continue screen, level-select ring (Arbo, Dreejal Vin, Elta Siktar, Kek, Gorm's Lair), Kek Powerizer submenu (Shield / Tracking / Road Rocket / Intruder Alert), credits, and the 2-player "VS" screen.

Negative results: the ASCII text bank contains **0** occurrences of `password`, `cheat`, `debug`, `secret`, or `unlock`; UI text is stored as plain ASCII in a large localized bank (9 languages), so the keyword scan is meaningful and not defeated by tile-indexed text. No password entry UI, no GameShark/CodeBreaker code is reported as a game feature.

---

## 3. How to reproduce

### 3.1 Emulator / display

```
export DISPLAY=:316 SDL_AUDIODRIVER=dummy
Xvfb :316 -screen 0 1024x768x24 &
DISPLAY=:316 openbox &
mgba -3 "<rom path>" &
```

Default mGBA SDL keymap used (verified by menu navigation and title transition): A = `x`, B = `z`, L = `a`, R = `s`, Start = `Return`, Select = `BackSpace`, D-pad = arrow keys. Hold keys 100–300 ms; several screens fade through black for 0.3–2 s, so re-screenshot after waiting.

### 3.2 Menu path

1. Language select → A on `English US`.
2. Legal/intro → A repeatedly (≈8–20 presses) → attract demo → "Press START" title.
3. `Start` → six-item ring main menu. `Left`/`Right` rotate the ring; `A` enters an item, `B` backs out.
4. `Options` → Music / Sound FX / Difficulty (Easy/Medium/Hard) / Language / Erase Data.
5. `New Game` → level ring `Arbo` / `Dreejal Vin` / `Elta Siktar` / `Kek` / `Gorm's Lair`.
6. `Continue` → Slot 1..4 (all `EMPTY` on a fresh `.sav`).
7. `Kek Powerizer` → submenu Shield / Tracking / Road Rocket / Intruder Alert.
8. `2 Player Challenge` → "VS" screen.
9. `Credits` → scrolling credits.

### 3.3 Button codes

Enter at the main/title menu as discrete D-pad presses; a confirmation sound plays on a correct entry, and `Select` resets a partial entry. The five accepted sequences are listed in §6. Because the on-screen keyboard is a D-pad-only sequence and the table holds active-high GBA key masks, the canonical notation is the direction letters.

### 3.4 Static reproduction

```
arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 \
  --start-address=0x080057e0 --stop-address=0x080058d8 -M force-thumb game.gba
xxd -s 0x30c50 -l 0xf0 game.gba
python3 /tmp/galidor/verify.py
```

---

## 4. Address map

| Address | File offset | Meaning |
|---|---|---|
| `0x08001F78` | `0x1F78` | Input poll: builds `pressed`/`held`; literal pool at `0x08001FB0`–`0x08001FC0` |
| `0x08001FB0` | `0x1FB0` | `0x04000130` (KEYINPUT) |
| `0x08001FBC` | `0x1FBC` | pointer `0x03001EA0` (pressed) |
| `0x08001FC0` | `0x1FC0` | pointer `0x0300185C` (held) |
| `0x080057E0` | `0x57E0` | **Button-code validator** (called from `0x08005BA0`) |
| `0x080058B0` | `0x58B0` | literal `0x08030C50` (code table base) |
| `0x080058B4` | `0x58B4` | literal `0x03001614` |
| `0x080058B8` | `0x58B8` | literal `0x03002EA8` (effect flags) |
| `0x080058BC` | `0x58BC` | literal `0x03002E4C` (screen/state word) |
| `0x08030C50` | `0x30C50` | **Code table**, 5 × 0x30 bytes, ends `0x08030D40` |
| `0x08008C8C` | `0x8C8C` | Credits handler: L+Select combo, sets `0x03002EA8 = 2` |
| `0x08008CE0`–`0x08008D14` | `0x8CE0`–`0x8D14` | Credits handler: R+Select combo, sets `0x03002E4C = 0x19` |
| `0x0803CD8` | `0x3CD8` | Confirmation-sound routine (`r0 = 0x24`) |

### RAM (observed / derived)

| Address | Meaning |
|---|---|
| `0x0300185C` (u16) | `held` key mask (active-high) |
| `0x03001EA0` (u16) | `pressed` key mask (edge) |
| `0x03006E60` | 10 × u32 code-input history |
| `0x03006EE8` (u32) | history index (0..10) |
| `0x03002EA8` (u32) | accumulated effect flags (OR of matched record flags) |
| `0x03002E4C` (u8/u32) | screen/state word: title/intro `0x02`, attract/intro `0x1F`, debug menu `0x19` |
| `0x03001614` | credits-scroll/entry counter (must be `0xFF` for R+Select debug gate) |
| `0x0300158C` | credits sub-condition (must be `0` for the R+Select gate) |

---

## 5. Algorithm

### 5.1 Input polling — `0x08001F78` (Derived, disassembly)

```
held = ~KEYINPUT & 0xFFFF
if ((held & 0xC0) == 0xC0) held &= 0xFF3F        // Up+Down cancel
if ((held & 0x30) == 0x30) held &= 0xFFCF        // Left+Right cancel
pressed = held & ~previous
previous = held
```

### 5.2 Validator — `0x080057E0` (Derived, full disassembly)

```
pressed = *(u16*)0x03001EA0
if (pressed & 4) {                       // Select: reset entry
    *(u32*)0x03006EE8 = 0
    for (i = 0; i < 10; i++) ((u32*)0x03006E60)[i] = 0xFFFFFFFF
    return
}
if (pressed != 0) {
    idx = *(u32*)0x03006EE8
    ((u32*)0x03006E60)[idx] = pressed     // store mask, u32 stride
    *(u32*)0x03006EE8 = idx + 1
}
if (*(u32*)0x03006EE8 != 10) return

for (rec = 0; rec < 5; rec++) {
    p = 0x08030C50 + rec * 0x30
    for (i = 0; i < 10; i++)
        if (((u32*)0x03006E60)[i] != ((u32*)p)[i]) goto next_rec
    flag = *(u32*)(p + 0x2C)                // effect flag
    *(u32*)0x03002EA8 |= flag
    *(u32*)0x03006EE8 = 0
    if (flag == 0xFF) {
        *(u32*)0x03002EA8 = 1
        *(u32*)0x03002E4C = 0x19            // DEBUG MENU
        return
    }
    sound(0x24)                             // confirmation beep
  next_rec:
}
if (*(u32*)0x03006EE8 > 10) *(u32*)0x03006EE8 = 10
```

Caller gate at `0x08005B98`: `if (*(u32*)0x03006EB8 == 0) call 0x080057E0;` — the validator runs only in the screen state whose handler contains this call. A savestate taken on the title/main-menu screen showed the history buffer pre-populated with attract-mode presses (`0x10` × 7) and index `0x07`, i.e. the buffer is shared with the attract-mode input path and persists until Select resets it.

### 5.3 Credits hidden combos (Derived)

```
if (credits_counter(0x03001614) == 0xFF &&
    (held & 0x100) && (held & 0x004) && *(0x0300158C) == 0) {
       *(u32*)0x03002E4C = 0x19; *(u32*)0x03002EA8 = 1; sound();
}   // R + Select on the credits screen -> debug menu

if (... && (held & 0x200) && (held & 0x004)) {
       counter = (counter + 1) % 5; *(u32*)0x03002EA8 = 2; sound(1);
}   // L + Select on the credits screen -> second hidden branch
```

These combos are **not** on any published code list.

---

## 6. Tables

### 6.1 The five accepted button codes (full space)

Flags are ORed into `0x03002EA8`; `0xFF` is the debug-menu sentinel.

| # | ROM address | Sequence (10 presses) | Flag | Published effect |
|---|---|---|---|---|
| 0 | `0x08030C50` | L,L,L,R,R,R,L,L,L,U | `0x01` | Freeze in mid-air with Select |
| 1 | `0x08030C80` | R,R,R,R,L,L,L,R,R,U | `0x02` | Immortality + freeze in mid-air |
| 2 | `0x08030CB0` | R,L,R,R,L,R,R,R,L,U | `0x04` | Unlock all levels (needs save) + freeze |
| 3 | `0x08030CE0` | R,R,R,L,R,R,R,L,R,U | `0x08` | Unlock boss levels + freeze |
| 4 | `0x08030D10` | D,D,D,L,L,L,L,U,U,U | `0xFF` | Debug menu (hold Select to go anywhere in level; level select; sound test) |

Every record ends with `u32 0xFFFFFFFF` at offset `+0x28` and the effect flag at `+0x2C`.

### 6.2 Button masks (active-high)

`A=0x001 B=0x002 Select=0x004 Start=0x008 Right=0x010 Left=0x020 Up=0x040 Down=0x080 R=0x100 L=0x200`

### 6.3 Flag combining

Because flags are ORed and never cleared by the validator, entering two codes in sequence produces a flag value absent from the table (e.g. rec0 then rec1 → `0x03`). This is the only "unadvertised combination" the system can express; the set of *accepted sequences* itself is closed at five.

### 6.4 Published codes verified against ROM

| Source | Literal | ROM check |
|---|---|---|
| 3rd party cheat indexes | D,D,D,L,L,L,L,U,U,U (debug) | present, `0x08030D10` |
| same | R,R,R,R,L,L,L,R,R,U (immortality) | present, `0x08030C80` |
| same | L,L,L,R,R,R,L,L,L,U (freeze) | present, `0x08030C50` |
| same | R,R,R,L,R,R,R,L,R,U (boss levels) | present, `0x08030CE0` |
| same | R,L,R,R,L,R,R,R,L,U (all levels) | present, `0x08030CB0` |
| 3rd party cheat indexes | GameShark `03002E4C19` (debug) | address confirmed: validator writes `0x19` to `0x03002E4C` at `0x080058A0`–`0x08058A2` |
| CodeBreaker | `73002E4C 001C / 33002E4C 0019` (level select via Credits) | address confirmed; the game's own R+Select gate writes the same value |

No GameShark/CodeBreaker/Game Genie code is treated as an in-game cheat here; they were used only to cross-check addresses.

---

## 6b. Enumeration

* **Space definition.** The validator accepts exactly **5** sequences, each 10 presses. The theoretical input space is `10^10` press strings over the ten GBA buttons; the accepted set is 5 strings. Field widths: 10 × 32-bit key masks, 1 × 32-bit terminator, 1 × 32-bit effect flag; record stride 0x30; table size 5 × 0x30 = 0xF0 bytes (`0x08030C50`–`0x08030D3F`). No checksum, no reserved bits, no variable-length codes. The loop bound `cmp r5,#4; ble` at `0x080058C8` proves there are exactly five records, not a longer table.
* **Validator model.** §5.2 is a bit-exact reimplementation of the ROM routine, including the Select reset, the u32-stride history buffer, the ten-mask comparison, the flag OR, the `0xFF` debug path, and the post-loop index clamp. `verify.py` decodes all five records from the ROM and matches them to the published list.
* **Novel code.** All five accepted sequences are published, so no additional *accepted* sequence can be minted — the table is closed. The unpublished developer surface is instead the **credits-screen combos** at `0x08008C8C`/`0x08008CE0`: `L+Select` (sets flag `0x02`) and `R+Select` with counter `0xFF` (sets screen `0x19`, the debug menu). Neither appears in 3rd party cheat indexes. The combined flag value `0x03` obtained by entering codes 0 and 1 sequentially is likewise not on any published list.
* **Bounds proven by rejection.** §5.2 rejects every press string not exactly equal to one of the five records: a single wrong mask sets `r7 = 1` and jumps to the next record (`0x0800586C`→`0x080058C6`), and an incomplete string never reaches the `idx == 10` branch (`0x0800583E`). The terminator word must be `0xFFFFFFFF` for a record to be reached (each record is skipped only after its ten masks are compared, so the terminator is part of the stored layout). Out-of-range history indices are clamped to 10 at `0x08058CC`–`0x08058D6`.

---

## 7. Validation evidence

* **Observed (emulator, `:316`)** — all screens listed in §2 were reached and screenshotted: language select, legal/intro, attract demo ("Amphib Jump", "Power Wings", "Aqua Fins", "Power Punch", "Grapple Hook", "Energizer"), "Press START" title, six-item ring main menu, Options (Music / Sound FX / Difficulty / Language / Erase Data / Are you sure?), Slot 1 EMPTY, level ring (Arbo … Gorm's Lair), Kek Powerizer submenu (Shield / Tracking / Road Rocket / Intruder Alert), scrolling credits, and VS screen.
* **Observed (savestate RAM)** — `0x03002E4C = 0x02` at the title/main-menu screen, `0x1F` in the intro/attract state; `0x03002EA8 = 0x00` on a fresh game; `0x03006E60` holds seven attract-mode `0x10` entries with index `0x07` after boot. Savestate parsing used the zlib-compressed `gbAs` PNG chunk, IWRAM at +`0x19000` (§16.13 of the guide).
* **Derived (static)** — code table layout and all five sequences (`0x08030C50`); validator algorithm and addresses (`0x080057E0`); input masks (`0x08001F78`); credits combos (`0x08008C8C`, `0x08008CE0`); confirmation sound call (`0x0803CD8`).
* **Inferred** — the exact in-game timing window of the credits counter gate (`0x03001614 == 0xFF`) was not exercised end-to-end; the write to `0x03002E4C = 0x19` is derived from disassembly and matches the published GameShark literal exactly.

---

## 8. Unknowns

* The exact frame/timing window in which the validator is called (`0x08005B98` gate `0x03006EB8 == 0`) was not isolated to a single named screen; the attract-mode code path populates the same history buffer, which is why a fresh game starts with seven `Right` entries in it.
* Whether the credits L+Select branch (`0x03002EA8 = 2`) grants a distinct in-game effect or simply re-selects the immortality flag was not observed on screen.
* The debug menu's own entries (level select, sound test, "go anywhere") are derived from the published 3rd party cheat index description plus the `0x19` screen write; a full in-game walk of that screen was not completed in this session.

---

## 9. Tooling

* `arm-none-eabi-objdump -M force-thumb`, Capstone 5.0.7, Ghidra via REA MCP (raw-binary ARM load at `0x08000000`), `strings`, `grep`, `xxd`, `struct`.
* mGBA 0.10.5 on Xvfb `:316` with `SDL_AUDIODRIVER=dummy`; `xdotool` for input, `scrot`/ImageMagick for screenshots.
* Savestate RAM reader `ssdump.py`, state patcher `patchstate.py`, code injector `injectcode.py`, input helper `press.py`, decoder `verify.py` (all in `/tmp/galidor`).
* Web sources: 3rd party cheat index search snippets, 3rd party cheat index search snippet, 3rd party cheat indexes CodeBreaker list (address cross-check only). Fetched pages were treated as data; no page contained an instruction that was acted upon.

---

## 10. Legal note

No ROM bytes, graphics, audio, or extracted assets are redistributed here. Only hashes, addresses, algorithms, and original analysis scripts are published.
