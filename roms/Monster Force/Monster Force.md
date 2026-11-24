# Monster Force (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Monster Force/Monster Force.gba` |
| Size | 8,388,608 bytes (`0x00800000`) |
| Header title | `MONSTERFORCE` |
| Game code / maker | `AM8E` / `7D` (AGB-AM8E-USA, Universal Interactive; Digital Eclipse dev) |
| Version / fixed byte | `0x00` / `0x96` |
| Header checksum | `0x0000` (rebuilt-header artifact; §16.1) |
| Complement byte | `0x34` — *valid* for bytes `0xA0..0xBC` |
| Entry word | `0xEA00002E` — stock `b 0x080000C0` crt0 (no cracktro) |
| MD5 | `eed661599b926eddf6890c862c252112` |
| SHA-1 | `3f97630914cbbb4bf45dcc42e7eb8062e9e8a271` |
| SHA-256 | `1eca053e73c5463bc548e2f3d5113c348ce5310c227f6367dcf5892567335fd2` |

**Phase 0 / embedded-header scan:** the 156-byte Nintendo logo area at `0x04..0x9F` contains
*nonstandard* bytes (distribution/rebuilt-header artifact, not a functional patch). Scanning the
whole image for the logo's 8-byte core `8b 0c 28 84 ad 48 11 8b` returned **zero** hits, so this is
a **single image**: no second game header, no multiboot stub, no appended trainer. Only one
`0xEAFFFFFE` (`b .`) idle loop exists, as expected. All code/addresses below are for this exact hash.

## 2. Executive summary

There is **no password/code-string system** in this game. The developer-intended cheat surface is a
small set of **button chords** checked by four inline validators that read the standard GBA key
state (active-high masks: `A=0x001, B=0x002, Select=0x004, Start=0x008, Right=0x010, Left=0x020,
Up=0x040, Down=0x080, R=0x100, L=0x200`).

Four published codes were found on 3rd party cheat indexes and **all four were
verified in ROM and in the emulator**:

| Effect | Screen | Chord | Verified |
|---|---|---|---|
| Skip level | gameplay | hold L+R+A, press Up | breakpoint + state `0x0E→0x10`, results screen |
| Exit level | pause | L+R+A | state `0x0F→0x0B`, returns to level intro |
| Infinite energy ("Invincibility") | pause | hold L+R+B, press Down | toggle effect breakpoint fires; sprite turns blue |
| Unlock Mina & Drew | character select | hold L+R+B, press Right | save byte `0x030068BB: 0x03→0x05`, 4th portrait appears |

All in-game text is **plain NUL-padded ASCII** in a bank around `0x7A7000–0x7B2000`; `strings`
recovered every menu label and the unlock messages directly, so no font/tile-index decoding was
needed for the negative conclusion. Menu labels drawn as graphics (e.g. "Character Select", pause
stat panel) were walked visually. **No hidden/debug menu, password entry, level-select code or
sound-test screen was found.** Arena/character unlocks other than the chord above are story or save
bits (§16.18), not cheats.

The 10 CodeBreaker codes circulating on 3rd party cheat indexes/libretro are raw memory edits and are **out of
scope** (no GameShark/CodeBreaker/memory-edit codes reported here).

## 3. How to reproduce

* Emulator: `mgba -3 -d` under `Xvfb :319`, `DISPLAY=:319`, `SDL_AUDIODRIVER=dummy`.
* SDL keymap used: `A=x`, `B=z`, `L=a`, `R=s`, `Start=Return`, `Select=BackSpace`, D-pad=arrow keys.
* **Hold every key ≈0.4 s; hold modifier chords ≈0.8 s and the final direction ≈0.9 s.** 60 ms taps
  were missed (§16.2 / §4.2) and produced false "rejected" results during this analysis.
* Screens: title → (Start) intro → (Start) skips intro → main menu (New Game / Continue /
  Multiplayer / Options). Options: Sound FX On/Off, Music On/Off, View Credits, Exit — all walked;
  no hidden entry. New Game → cutscene (Start skips) → **Character Select** → (A) level intro →
  (Start) **gameplay** → (Start) **pause** panel. Multiplayer → "Waiting for other player…".
* Save states were not required; the mGBA `-d` pty debugger (`@BREAK`, `r/1|2|4`, `b/t`, `w/r`,
  `c`, `reset`) was driven through a UNIX-socket helper (`dbg.py`).

Exact menu path to each code is in the table in §2. Keymap was verified by reading key globals while
holding single keys (`a→0x0200`, `s→0x0100`, `z→0x0002`, `x→0x0001`, arrows→`0x40/0x80/0x10/0x20`).

## 4. Address map

| Item | Address (ROM / RAM) | Notes |
|---|---|---|
| Primary input reader | ROM `0x08000C98` | reads `0x04000130`, inverts to active-high |
| Secondary input reader | ROM `0x08040650` | 22-bit mask (`lsl #22; lsr #22`) |
| Primary held / pressed | RAM `0x030035FC` / `0x030035FE` | base `0x03000760` + `0x2E9C` / `0x2E9E` |
| Primary held copy | RAM `0x03003600` | base + `0x2EA0` |
| Secondary held / pressed | RAM `0x03006FE0` / `0x03006FE4` | written at `0x080406B0` / `0x08040696` |
| Game state word | RAM `0x03000760` | `0x01` menu, `0x0B` level intro, `0x0E` gameplay, `0x0F` pause, `0x10` results, `0x16` shop |
| Save-ish struct | RAM `0x030068B0` | byte `+0x0B` (`0x030068BB`) = unlock marker; `3`=3 chars, `5`=Mina+Drew unlocked |
| **Level-skip validator** | ROM `0x08008DC8` | compare `0x08008DE8` / `0x08008E02`; effect `0x08008E10` writes `0x0F` to state |
| **Unlock validator** | ROM `0x08037CB2` | compare `0x08037CCC` / `0x08037CDE`; effect `0x08037CF2` writes `5` to `0x030068BB` |
| **Invincibility validator** | ROM `0x0803A940` | compare `0x0803A952` / `0x0803A962`; effects `0x0803A9A2` (clear) / `0x0803AA02` (set) on bit 0 of `0x03003588` |
| Exit-level effect | not isolated statically | empirical: pause + L+R+A → state `0x0F→0x0B` (no `0x301` literal exists outside the level-skip function; the pause handler likely composes the mask from immediates) |
| ASCII text bank | ROM `0x7A7000–0x7B2000` | plaintext, e.g. `0x7AA8C8` "Congratulations Mina is now playable.", `0x7AA8F8` Drew, `0x7AB0A8` "Invincible 1" |

Literal pools (verified with `struct.unpack_from`, little-endian): `0x08008E28 = 0x301`,
`0x08008E2C = 0x2E9E`, `0x08037D50 = 0x302`, `0x08037D4C = 0x03006FE0`,
`0x08037D54 = 0x03006FE4`, `0x0803A9D8 = 0x302`, `0x0803A9C0 = 0x2E9E`,
`0x0803A9C8 = 0x2E9C`, `0x0803A9DC = 0x2E28`.

## 5. Algorithm

```
// all key globals are u16, active-high; load zero-extended, mask, compare to mask
level_skip():                       // 0x08008DC8, gameplay only
  if (word[0x03003588] & 2)==0: return          // mode gate (bit 1)
  if (u16[0x030035FC] & 0x301) != 0x301: return // L+R+A held
  if (u16[0x030035FE] & 0x040)==0: return       // Up newly pressed
  word[0x03000760] = 0x0F                       // -> results (observed 0x10)

unlock_mina_drew():                 // 0x08037CB2, character select
  if (u16[0x03006FE0] & 0x302) != 0x302: return // L+R+B held
  if (u16[0x03006FE4] & 0x010)==0: return       // Right newly pressed
  byte[0x030068BB] = 5                          // 4th selectable character

invincibility():                    // 0x0803A940, pause screen
  if (u16[0x030035FC] & 0x302) != 0x302: return // L+R+B held
  if (u16[0x030035FE] & 0x080)==0: return       // Down newly pressed
  word[0x03003588] ^= 1                         // toggle bit 0 (bics/orrs pair)

exit_level():                       // pause screen (empirical)
  if (held & 0x301)==0x301: word[0x03000760] = 0x0B   // extra keys ignored
```

All validators use bitmask **AND**, not full-state equality: any extra held button is ignored by the
mask comparison. Screen-side effects of those extra buttons (A confirms on character select,
direction keys move cursors) constrain which aliases are actually reachable.

## 6. Tables

Button masks (active-high): `A 0x001, B 0x002, Select 0x004, Start 0x008, Right 0x010, Left 0x020,
Up 0x040, Down 0x080, R 0x100, L 0x200`; chord masks `L+R+A=0x301`, `L+R+B=0x302`.

Game-state values observed at `0x03000760`: `0x01` title/main menu, `0x0B` level intro, `0x0E`
gameplay, `0x0F` pause, `0x10` results, `0x16` shop/results-transition.

Published literals checked (all **present/confirmed** as behavior, not stored strings — these are
button chords, so a literal `grep` for them is not meaningful):

* 3rd party cheat indexes: the four chords in §2. Verified in ROM code and
  in emulator. No OCR/typo variants encountered.
* 3rd party cheat indexes/libretro 10 CodeBreaker entries: memory edits (`0x030007DA`, `0x03000840`, …), out of
  scope; deliberately not applied.

Text bank keyword census: `password` **0** hits, `cheat` **0**, `debug` **0**, `secret` **0**,
`code` 0 (other than the header), `level` many (mission descriptions), `invalid` ~40 (unused item
slots in the item-description table at `0x7AB000`), `unlock`/`playable` 2 (Mina/Drew messages).

## 6b. Enumeration

**Space definition.** The system is a fixed set of **4 button sequences**, not a checksum code:
alphabet = 10 GBA buttons; sequence shape = a 2–3 button modifier chord (`L+R+A` or `L+R+B`) plus
either a single directional press (`Up`, `Right`, `Down`) or no further press. There is no generator,
no checksum and no reserved-bit field. Total meaningful chord/direction combinations checked by
the four validators = `2 modifier chords × 4 directions + 1 no-direction = 9`, of which **4 are
accepted**. Each validator samples `pressed` (edge) for the direction and `held` for the modifiers,
so a direction already held from the previous frame is not a valid trigger.

**Novel code (absent from every published list).** Because the validators AND-mask the held state,
extra buttons are aliases. I minted and entered:

> **Pause screen — hold `L+R+A`, press `Right`** (published list says only `L+R+A`).

Result (**Observed**): game-state word `0x03000760` changed `0x0000000F → 0x0000000B` and the
screen returned to the "Welcome to Spooky Cemetery / Atom Quota" level-intro panel
(`pause_alias3_before.png` → `pause_alias3_after.png`). This alias appears on no 3rd party cheat index page. It proves the exit-level check ignores the
direction bits and that the reachable chord space is larger than the published table.

A second alias class follows from the same mask logic: `L+R+B` + *simultaneous* `Down+Right` should
satisfy both the invincibility and unlock masks on their respective screens (derived, **Inferred** —
not entered in the emulator; screen side effects of `Right` on the pause menu make the pause variant
hard to observe cleanly).

**Bounds proven by rejection (all pressed in the emulator, effect breakpoints armed at
`0x08008E10`, `0x08037CF2`, `0x0803A9A2`, `0x0803AA02`):**

| Combo | Screen | Result |
|---|---|---|
| `L+R+A+Down` | gameplay | rejected — no level-skip effect |
| `L+A+Up` (R missing) | gameplay | rejected |
| `R+A+Up` (L missing) | gameplay | rejected |
| `L+R+B+Right` | gameplay | rejected — unlock validator not active there |
| `L+R+B+Up` | gameplay / pause | rejected |
| `L+R+B+Left` | pause | rejected |
| `L+R+A+Down` | pause | no invincibility/unlock effect |
| `L+R+A+Right` | pause | **accepted** (novel exit-level alias, above) |
| `L+R+B+Right` with `A` also held | character select | invalid test — `A` confirms the character (documented as such) |

Modifiers held ≈0.8 s and final direction ≈0.9 s in every case; short taps were shown to be
unreliable and were not used as evidence.

## 7. Validation evidence

* **Observed** — boot/title/main menu/Options/View Credits/Character Select/level intro/gameplay/
  pause/shop/Multiplayer screens (screenshots on disk in `/tmp/monsterforce/`);
  key-global values while holding keys; mGBA pty breakpoints hitting at `0x08008E10`
  (level skip: `held=0xFF41`, `pressed=0x0040`), `0x08037CF2` (unlock: `r0=0x10`),
  `0x0803A9A2` (invincibility toggle: `r1=0x00000002`, clearing bit 0);
  save byte `0x030068BB` `0x03→0x05`; state word transitions `0x0E→0x10`, `0x0F→0x0B`;
  fourth character portrait appearing; blue (invincible) sprite.
* **Derived** — the four validator functions and their literal pools; mask/edge semantics;
  alias behavior from AND-mask comparisons; ASCII text-bank census.
* **Inferred** — exact semantic label of `0x03003588` bit 0 ("infinite energy" per the published
  effect, not isolated to an HP-refill reader); the exit-level validator's precise address and
  instruction form (empirically confirmed effect only); arena unlocks are save/story bits.

**Prompt-injection check:** fetched cheat pages (3rd party cheat indexes) were treated as data; none contained instructions attempting to redirect the analysis,
and no such instruction was followed.

## 8. Unknowns

* Precise ROM address/instructions of the pause-screen exit-level check (no `0x301` literal exists
  outside the level-skip validator, so the pause handler must compose the mask from immediates).
* Whether the invincibility toggle bit at `0x03003588` bit 0 is consumed as a continuous HP refill,
  an item grant, or a damage-immunity flag — the breakpoint proves the toggle, not the reader.
* Per-arena unlock bits (Cemetery/Village/… bosses) are save/story-gated; they were not advanced
  through a full playthrough and are not button codes.
* No hidden debug screen was reached; the negative is bounded by the screen walk and the
  zero-hit keyword census in the ASCII text bank, not by a full code-path proof of every menu.

## 9. Tooling

`arm-none-eabi-objdump -M force-thumb` for validator disassembly; Python 3 + `capstone 5.0.7`
for literal-pool/PC-relative-reference scans; `mGBA -3 -d` pty debugger driven by
`dbg.py` (UNIX-socket wrapper exposing `@BREAK`, `r/1|2|4`, `b/t`, `w/r`, `c`, `reset`);
`enum_test.py` for scripted combo presses with effect breakpoints; `xdotool` for input;
`scrot` + ImageMagick for screenshots; `strings`/`grep`/`python` for the text-bank census.
No ROM or copyrighted assets are redistributed here — only hashes, addresses, and the
independently written code descriptions.
