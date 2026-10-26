# 007: Nightfire (GBA) — Reverse Engineering Report

Report generated from a local ROM analysis on 2026-10-24.
Methodology: [`GBA_REVERSE_ENGINEERING_GUIDE.md`](../../GBA_REVERSE_ENGINEERING_GUIDE.md)

Scope note: **in-game / developer-intended cheats only.**
GameShark/CodeBreaker/RAM-patch codes are out of scope.

---

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/007: Nightfire/007: Nightfire.gba` |
| Size | 8 MiB (`0x800000`) |
| Header title | `NIGHTFIRE` |
| Game code | `A7OE` |
| Maker code | `69` |
| Software version | `0` |
| MD5 | `71259fb2bf7adeb9b5d8c84619a2531e` |
| SHA-1 | `f4363923181b71448ddd6e28ac72d30b3ecfc019` |
| SHA-256 | `b39b223cfa5a6e19de3f7c3a9aca254a41eb2eebcf2718c8e0d0575291f7e903` |

ROM addresses below are `0x08000000 + file_offset`. All findings are tied to
this exact hash; another revision may differ.

---

## 2. Executive summary

The GBA build has a **hidden pause-menu cheat system**: a fixed
**six-button prefix** followed by **one action button**.

```
prefix:  R, Left, L, Right, Up, Select
action:  Left  -> God mode (invincibility) toggle
         Right -> 500 rounds for every weapon
         R     -> unlock all missions (level select)
         L     -> higher-pitched voices
```

These four are the **complete** set: the prefix matcher (`0x0800BA0E`) accepts
exactly six entries from the table at `0x0801E170`, and the seventh press is
dispatched against only four masks (`0x20 / 0x10 / 0x100 / 0x200`), each branch
ending in a distinct flag write. Any other seventh button does nothing.

Two were verified in the emulator end-to-end:

* **Prefix + Right** — ammo counter went `12 / 48` → `16 / 500` (screenshot).
* **Prefix + R** — after quitting the mission, the mission-select screen
  appeared with left/right arrows and allowed **Mission 2** to be chosen; the
  same screen had been fixed to Mission 1 before the code.

God mode and the voice-pitch toggle are proven by the dispatch code (distinct
flag writes plus a confirmation sample), but were not exercised under fire /
with audio, so their in-game effect is *derived*, not *observed*.

The GBA build has **no password entry**: the PS2/GC/Xbox "Secret Unlocks"
codes (`PARTY`, `Q LAB`, `PASSPORT`, ...) do not exist here. The GBA progress
model is medal-based; the pause-menu sequence is the only cheat surface.

Leftover dev text names the invincibility toggle: the string blob at
`0x083AC6B` contains `Temp God Mode: On` / `Temp God Mode: Off`
(`0x083AD66`).

---

## 3. How to reproduce

### Emulator

```bash
sudo apt-get install -y mgba-sdl xvfb xdotool imagemagick openbox
Xvfb :99 -screen 0 1024x768x24 &
DISPLAY=:99 openbox &
DISPLAY=:99 SDL_AUDIODRIVER=dummy mgba -3 "007: Nightfire.gba" &
```

`openbox` is needed for xdotool key delivery; capture with
`import -window <wid> out.png`. Default mGBA keymap: A=`x`, B=`z`,
L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad = arrows.
Hold keys ~150–200 ms.

### Path to a testable state

```
Language (English) -> title (START) -> main menu
 -> New Game -> slot -> difficulty -> Enter your name -> (check mark)
 -> mission briefing -> Mission 1 "Austrian Castle"
 -> Start (in mission) -> pause menu
```

### Codes exercised

| Input at pause menu | Observed result |
|---|---|
| `R Left L Right Up Select Right` | reserve ammo `48` -> `500` (counter reads `16/500` after firing) |
| `R Left L Right Up Select R` | quit mission; mission select now browses (Mission 2 reachable) |
| `R Left L Right Up Select Left` | no visible change (god-mode flag; sample plays) |
| `R Left L Right Up Select L` | audio-only (voice pitch; not evaluated headless) |

Note: the same buttons also drive the pause menu, so the cursor moves while
the code is typed. That is harmless — the matcher runs in parallel.

---

## 4. Address map

| ROM address | What |
|---:|---|
| `0x0800BA0E` | Cheat matcher: reads held keys, advances/resets progress |
| `0x0800BB68` | Per-step compare against prefix table (`progress <= 5`) |
| `0x0800BA1E` | Seventh-press action dispatch |
| `0x0800BA40` | God-mode toggle branch (`0x20`) |
| `0x0800BA80` | 500-ammo branch (`0x10`) |
| `0x0800BACC` | Level-unlock branch (`0x100`) |
| `0x0800BB24` | Voice-pitch branch (`0x200`) |
| `0x0801E170` | Prefix table, six `s16` masks: `0100 0020 0200 0010 0040 0004` |
| `0x0801ECB0` | 21-entry ammo default table used by the ammo branch |
| `0x083AC6B` | Text blob containing `Temp God Mode: On/Off` (`0x083AD66`, `0x083AD78`) |

RAM used by the cheat path:

| Address | Use |
|---|---|
| `0x020232C8` | current key state (active-low as read) |
| `0x0203EDA4` | god-mode toggle (u16; 0 = off, non-zero = on) |
| `0x0203EDA0` | flag word; bit 13 (`0x2000`) = higher-pitched voices |
| `0x0203A264` | u16 mission-unlock bitmask (bit *level* set by level-select) |
| `0x0202F080 + level*0x80 + 0x77` | per-level byte set to `8` by level-select |

GBA key masks in this engine (active-high after `~KEYINPUT & 0x3FF`):
`A=0x001`, `B=0x002`, `Select=0x004`, `Start=0x008`, `Right=0x010`,
`Left=0x020`, `Up=0x040`, `Down=0x080`, `R=0x100`, `L=0x200`.

---

## 5. Algorithm

### 5.1 Matcher (`0x0800BA0E`, derived)

```c
u16 held   = ~KEYINPUT & 0x3FF;      // 0x020232C8 in RAM
int *prog  = &cheat_progress;        // persistent while paused
static const s16 prefix[6] = { 0x100, 0x020, 0x200, 0x010, 0x040, 0x004 };

if (*prog <= 5) {
    if (held == prefix[*prog]) {      // 0x0800BB68
        (*prog)++;                    // 0x0800BB78
    } else if (*prog > 0 && held != 0) {
        if (held == prefix[*prog - 1]) {
            /* overlapping double-press: ignore */
        } else {
            *prog = 0;                // 0x0800BB9E
        }
    }
    return;
}

/* seventh press */
if (held == 0 || held == prefix[5]) return;   // no press / Select held
*prog = 0;
switch (held) {
case 0x020:  god_mode   ^= 1;  sample(0x521); break;   // 0x0800BA40
case 0x010:  ammo = 500; for (i = 0; i <= 20; i++) slots[i] = table[i]; break;
case 0x100:  unlock_level(level); unlock_mask |= 1 << level; break;
case 0x200:  flags ^= 0x2000; if (flags & 0x2000) sample(0x500); break;
}
```

Because the check is on **held** (level, not edge), each prefix button must be
released between presses; holding two at once is ignored by the overlap rule.

### 5.2 Level-unlock branch (`0x0800BACC`, derived)

```c
u16 level = *(s16*)0x020276FC;                 // current mission index
*(u8*)(0x0202F080 + level * 0x80 + 0x77) = 8;  // per-level "available" byte
*(u16*)0x0203A264 |= (1 << level);             // global unlocked mask
```

The per-level stride `0x80` and offset `0x77` are the same record layout used
by the mission-select screen, which is why the effect is visible there.

### 5.3 Ammo branch (`0x0800BA80`, derived)

Sets the reserve counter to `0x1F4` (500) and copies 21 bytes from
`0x0801ECB0` into the 21 weapon-slot entries (`+4` of each 8-byte slot), i.e.
500 rounds *per weapon*, matching the observed `500` reserve.

---

## 6. Tables

### 6.1 Prefix

| Step | Button | Mask |
|---:|---|---:|
| 0 | R | `0x100` |
| 1 | Left | `0x020` |
| 2 | L | `0x200` |
| 3 | Right | `0x010` |
| 4 | Up | `0x040` |
| 5 | Select | `0x004` |

### 6.2 Actions (exhaustive)

| 7th button | Mask | Effect | Confidence |
|---|---:|---|---|
| Left | `0x020` | God mode toggle (`Temp God Mode`) | Derived + public match |
| Right | `0x010` | 500 rounds per weapon | **Observed** |
| R | `0x100` | Unlock all missions / level select | **Observed** |
| L | `0x200` | Higher-pitched voices | Derived + public match |

No other seventh button has a branch; the dispatch falls through to the
no-op path. There is no fifth action.

---

## 7. Validation evidence

**Observed (emulator, screenshots)**
- Ammo `12/48` before, `16/500` after `...Select, Right` (the `16` is the
  magazine after a shot; reserve is the second number).
- Mission select after `...Select, R`: arrows appear, Mission 2
  "Mayhew's Estate" selectable; previously locked to Mission 1.
- Typing the sequence in the pause menu also moves the menu cursor (shared
  input), and the code still registers.

**Derived (Thumb disassembly, literals read directly from the image)**
- Prefix table contents and length, progress/overlap rules, four action
  branches and their flag addresses, ammo count `500` and 21-slot fill,
  level-unlock mask/byte writes.

**Inferred**
- "Temp God Mode: On/Off" is the display name of the invincibility toggle
  (string sits in the UI text blob; branch is the only invincibility-like
  consumer).
- Higher-pitched voices changes sample pitch only (audio not evaluated).

---

## 8. Unknowns

- Where the 6-step progress counter lives (register `sl` in the matcher; the
  backing global was not isolated). Consequence: whether partial prefixes
  survive leaving/returning to the pause menu is untested.
- God mode's exact semantics (full damage immunity vs. health floor) — needs
  taking damage in-game.
- Whether the voice-pitch toggle persists across missions or resets on load.
- Whether the level-unlock mask is written to the save file (it lives in RAM
  at `0x0203A264`; save-composition code not traced).
- No password/secret-unlock menu exists in this build, so the console
  code list (`PARTY`, `Q LAB`, `PASSPORT`, ...) was not searched for and is
  presumed absent (no such UI strings in the ROM).

---

## 9. Tooling

| Method | Purpose |
|---|---|
| `strings -t x` | found the UI text blob and `Temp God Mode` leftover |
| u16 mask-pattern search | located the prefix table at `0x1E170` in one pass |
| literal-pool scan for `0x04000130` | found the key-read routine at `0x080028A2` |
| Thumb disassembly (`objdump -M force-thumb`) | matcher, branches, flag writes |
| xdotool + `import -window` | code entry and screenshot evidence |
| web (GameFAQs via Wayback, VGChartz) | published codes to test and to bound the action set |

No ROM, graphics, or text from the game is redistributed here; only addresses,
algorithms, and short identifiers needed to describe the cheats.
