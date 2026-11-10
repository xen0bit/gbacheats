# Chicken Shoot (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Chicken Shoot/Chicken Shoot.gba` |
| Size | 4,194,304 bytes (0x400000, 4 MiB) |
| Header title | `CHICKENSHOT1` (0xA0–0xAB) |
| Game code | `B6FE` (0xAC) |
| Maker code | `20` (0xB0) |
| Fixed byte / unit / device | `0x96` / `0x00` / `0x00` |
| Software version | `0x00` (Rev.00) |
| Complement check | `0x88`; recomputed `0x88` (header unmodified) |
| Header checksum | `0x0000` (rebuilt-header artifact; complement is the reliable signal) |
| Entry word | `0xEA00002E` (stock GBA branch to `0x080000C0`) |
| Nintendo logo | single hit at file `0x4` (one image, no hidden sub-header) |
| MD5 | `36a92215bc1fd68f9db49c1be06fe088` |
| SHA-1 | `55235f7f2c427e0684e909f3832567f1f576da02` |
| SHA-256 | `04f2430571194a94d0c7d6f48cc821b96b4e84d95db4747f0d4e6ead67f5caa9` |

No cracktro, trainer, appended payload or second GBA header. The entry branch and the first 4 KiB are stock; the only header oddity is the zero header-checksum artifact, with a correct complement byte.

## 2. Executive summary

**This ROM has no in-game cheat, password, hidden debug menu or unlockable code system.**

The evidence is a closed inventory, not a failed search:

* The complete text bank (`0x003DA000`–`0x003E0000`) contains **325 printable strings**, all menu labels, five-language localisations, credits, level-stats labels, link-error text and the five default highscore names. There is **no** occurrence of `password`, `cheat`, `debug`, `secret`, `unlock`, `gallery`, `code`, `level select`, `sound test`, `test mode` or `bonus` in ASCII, in the `+0x20` (lower-case-as-capital) encoding, or in UTF-16LE.
* **Ten screen definitions** exist in ROM (language select, main menu, mode select, options, pause, redefine keys, highscore, multiplayer connecting/level select, about/credits, level-stats overlay). Every screen definition was parsed; none has a text-entry or code-entry widget. The only text input in the game is the highscore name field (`-enter name-`), which is a display name, not a validator (see §5).
* The only anomalous text is `test arcade` / `test classic`, repeated once per language (10 strings). They have **zero pointer references** anywhere in the 4 MiB image: a cut test-mode label set, not a reachable screen.
* Published cheat sources list nothing: GameFAQs' Chicken Shoot GBA cheat page has no codes/passwords/unlockables; ChapterCheats lists "No Codes, No Passwords, No Unlockables, No Hints or Secrets, No Easter Eggs"; Cheat Happens lists no codes. A known code therefore cannot be tested because none is published, and the ROM contains no candidate literal either.
* The button-mask search space was enumerated: every contiguous run of valid GBA button masks (16-bit and 32-bit, both held and edge forms) was extracted. **14** 16-bit runs of ≥5 masks with ≥3 distinct values exist; all sit inside graphics/tile data (offset ≥ `0x485A2`, no code or pointer reference), and none matches the Konami or any documented sequence. The canonical Konami mask sequence is **absent** in both directions.

Dynamically the menu shell was exercised on `:244`: main menu, options, mode select and the multiplayer connecting/level-select screen were each identified by reading the live screen-descriptor pointer and the live text-glyph buffer from RAM. The game's menu is cursor/hover-driven: the D-pad moves an 8.8 fixed-point aim cursor (`0x0300541C` X, `0x03005420` Y), `A` confirms the item under it, `B`/`Start` cancel. No button sequence, text entry or hidden screen was found in any reached menu.

## 3. How to reproduce

Emulator and display:

```bash
Xvfb :244 -screen 0 1024x768x24 &
DISPLAY=:244 openbox &
DISPLAY=:244 SDL_AUDIODRIVER=dummy mgba -3 "Chicken Shoot.gba" &
```

Keymap used (mGBA SDL defaults): `x`=A, `z`=B, `a`=L, `s`=R, `Return`=Start, `BackSpace`=Select, arrow keys = D-pad. Hold 100–300 ms per press; the menu cursor accelerates while a direction is held.

Menu paths observed:

1. Boot → 5 s → main menu (`-menu-` / new game / options / about).
2. At main menu, press **A** with the cursor over the middle tab (`x≈71, y≈64`) → **options**.
3. At main menu, move the cursor to about `(x≈53, y≈38)` and press **A** → **mode select** (`-select-`).
4. At mode select, cursor about `(x≈50–62, y≈81–90)`, press **A** → **connecting / level select** (`-connecting-`, d7=2). This screen lists `1 -`, `2 -`, `3 -`, `4 -`, `level -`, `back`.
5. `B` (or `Start`) cancels back one level. `A` activates the item under the aim cursor.

RAM-verified screen identity: read the current descriptor pointer at `0x03004348` and the text-glyph stream at `0x03004848` (8-byte entries `{u16 x, u16 0x0007, u16 glyph, u16 0}`). Glyph−ASCII is a per-character font offset, but the glyph *sequence* is stable and matches the descriptor's strings.

Savestates: `Shift+F1` writes slot 1 next to the ROM; `F1` loads it. RAM was read from the `gbAs` zlib chunk of the PNG savestate (layout: VRAM `0x1000`, IWRAM `0x19000`, EWRAM `0x21000`); no screenshots were used.

## 4. Address map

| Address | Meaning |
|---|---|
| `0x08000000` | ROM base; entry `0x080000C0` (ARM) |
| `0x08001AE4` | `main` (Thumb), reached from crt0 literal at `0x08000100` |
| `0x08006A44` | screen dispatcher: `state = *(u8*)(0x03005378+0x48C)` = `0x03005804`; jump table at `0x08006A7C`, states 0–5 |
| `0x08006A7C` | 6-entry state table: `0x08006A95`, `0x08006C41`, `0x08006DED`, `0x08006F99`, `0x08007099`, `0x08007189`; state >5 → `0x0800733A` |
| `0x080096F4` | input edge detector: `held=0x03002ABA`, `newpress=0x03002ABC`, `prev=0x03002ABE`; `KEYINPUT=0x04000130` |
| `0x0800617C` | generic screen builder: `r0` = screen descriptor pointer |
| `0x0800BFC0` | open main menu (`0x083DD458`) |
| `0x0800C2A0` | open options (`0x083DD678`) |
| `0x0800C324` | start game: sets `d7=2`, builds `0x083DE21C` |
| `0x0800C558` | open mode select (`0x083DD568`) |
| `0x0800C98C` | open multiplayer connecting (`0x083DDD58`) |
| `0x03002A20` | global game struct base |
| `0x03002A5C` | next-frame update callback pointer (menu animation/dispatch) |
| `0x03002A68` | per-frame animation counter |
| `0x03002AAC`–`0x03002AD6` | button-mask table: `0x0200/0x0100` L/R, `0x0020/0x0010` Left/Right, `0x0040/0x0080` Up/Down, `0x0001/0x0002` A/B, `0x0008/0x0004` Start/Select |
| `0x03002ABA` | held keys, active low (`0x03FF` = none) |
| `0x03002ABC` | newly-pressed keys, active low (`0xFFFF` = none) |
| `0x03002AF6` | transition phase (`d6`); `4` = screen active |
| `0x03002AF7` | mode (`d7`): `1` = menus, `2` = game/link |
| `0x03004348` | current screen descriptor pointer |
| `0x03004848` | current screen text-glyph stream |
| `0x0300541C` | aim cursor X, 8.8 fixed point |
| `0x03005420` | aim cursor Y, 8.8 fixed point |
| `0x03005804` | screen state byte (0–5, >5) |
| `0x03005A8E`+ | default highscore names `paula`, `mavey`, `rem`, `nelson`, `luk` (also copied to EWRAM `0x02000000`+) |

Screen descriptors (ROM addresses):

| Descriptor | Screen | Items (text, handler) |
|---|---|---|
| `0x083DD2DC` | language select | `select language`; `english`, `francais`, `deutsch`, `espanol`, `italian`; `back` |
| `0x083DD384` | main menu | `-menu-`; `new game` (`0x0800C44D`), `options` (`0x0800C785`), `about` (`0x0800B35D`) |
| `0x083DD460` | highscore | `-highscore-`; `arcade` (`0x0800C5E5`), `classic` (`0x0800C659`), `multiplayer` (`0x0800C6CD`), `back` (`0x0800C735`) |
| `0x083DD570` | mode select | `-select-`; `arcade` (`0x0800AE11`), `classic` (`0x0800AEC5`), `multiplayer` (`0x0800B121`), `back` (`0x0800C375`) |
| `0x083DD680` | options | `-options-`; `difficulty` (`easy/normal/hard`, `0x0800C8C5`), `sfx` (`9`, `0x0800B501`), `music` (`9`, `0x0800B645`), `gamma` (`1`, `0x0800B3CD`), `controls` (`0x0800C9A5`), `back` |
| `0x083DD8C4` | pause | `-menu-`; `sfx` (`9`), `music` (`9`), `gamma` (`1`), `controls`, `back to game` (`0x0800CD45`), `quit` (`0x0800CADD`) |
| `0x083DDB4C` | redefine keys | `-redefine keys-`; `l` (`L/R/A/B`), `r` (`L/R/A/B`), `fire` (`L/R/A/B`), `reload` (`L/R/A/B`), `back` |
| `0x083DDF74` | connecting / level select | `-connecting-`; `1 -`, `2 -`, `3 -`, `4 -`, `level -` (`0x0800C29D`), `back` (`0x0800C2D5`), `ok` (`0x0800B885`) |
| `0x083DE21C` | game screen | in-game HUD/build |
| `0x083DD06C` | level stats overlay | `-level stats-`; `shots fired`, `hits`, `accuracy`, `score`, `game time`, `energy` |

## 5. Algorithm

### 5.1 Input

`0x080096F4` polls `0x04000130` once per frame:

```
cur  = ldrh 0x04000130          ; active low
prev = ldrh 0x03002ABE
store cur -> 0x03002ABA         ; held
change = cur ^ prev
if change == 0:
    store 0xFFFF -> 0x03002ABC  ; no new press
else:
    store ~(prev & change) -> 0x03002ABC ; active-low new presses
    store cur -> 0x03002ABE
```

Menu handlers test `newpress & mask`; the mask values live in the table at `0x03002AAC`. Because the stored value is active-low, a handler that branches on a *zero* result is testing “that button is currently down”; a handler that branches on *non-zero* is testing “that button is not down”. The menu item update functions in this ROM use the latter form with the B mask (`0x03002ACE`), which is why `A` on an item and `B` as cancel are the observed user-facing behaviour.

### 5.2 Screen dispatch

`0x08006A44`:

```
state = *(u8*)0x03005804
if state > 5: handler = 0x0800733A
else: handler = table[state]          ; 0x08006A7C
handler()
```

The state byte stayed `0` for every menu screen in this build; menus are distinguished by the descriptor pointer at `0x03004348`, not by the state byte. `d7=1` means “menu shell”, `d7=2` means “game/link”.

### 5.3 Menu activation (derived and observed)

The menu is a light-gun style cursor UI:

* D-pad moves the 8.8 cursor at `0x0300541C/0x03005420`.
* Hovering the cursor over a screen tab rebuilds the descriptor: hovering the options tab produced descriptor `0x083DD680` and the text `-options-...`; hovering the main-menu/new-game area produced `0x083DD384` or `0x083DD570` depending on the confirmed action.
* `A` activates the item under the cursor (`x≈53,y≈38` at the main menu → mode select; `x≈50–62,y≈81–90` at mode select → connecting).
* `B` and `Start` cancel one level (`options` → main, mode select → main, connecting → mode select).

## 6. Tables

### 6.1 Text and screen inventory

* Text bank: **325** printable strings in `0x003DA000`–`0x003E0000`.
* Referenced by widget pointers: **70** strings (the rest are credits, localisations of the same labels, and five default highscore names).
* Screen descriptors: **10** (table above).
* Text-entry widgets: **1** — `-enter name-` on the highscore name screen.
* Screens with a code/password widget: **0**.
* Keyword hits for `password|cheat|debug|secret|unlock|gallery|code|level select|sound test|test mode|bonus`: **0** in ASCII, **0** in `+0x20` shift, **0** in UTF-16LE.

### 6.2 Cut/unreferenced content

`test arcade` and `test classic` occur five times each (one per language). A literal-pointer scan for all ten addresses finds **no** reference in the 4 MiB image. They are the only menu strings with zero xrefs and correspond to a removed “test” entry in the mode-select table. They are not reachable text, so they do not constitute a hidden menu.

### 6.3 Button-code space

* 16-bit runs of valid masks (A/B/Select/Start/Right/Left/Up/Down/R/L): **545** runs of ≥4; **14** of ≥5 with ≥3 distinct values. All 14 lie in graphics/music data at offsets `0x485A2`, `0x9EF66`, `0xB658E`, `0xB9E06`, `0xBA05E`, `0x262FAA`, `0x29EFCE`, `0x29FFCE`, `0x2D56EE`, `0x2D66EE`, `0x361E76`, `0x362E76`, `0x388DEA`, `0x3D6154`; none is referenced by code and none forms a coherent directional sequence.
* 32-bit runs: **205** runs of ≥4; **103** of ≥5; every one is inside graphics data (no code xref).
* Byte runs of button indices 0–9: 37,148 raw runs of ≥4; 8,176 plausible ≥5 with ≥3 distinct — overwhelmingly tile data; no run is referenced by an input handler.
* Canonical Konami mask sequence `Up,Up,Down,Down,Left,Right,Left,Right,B,A`: **absent** as u16 little-endian in both forward and reversed order. The `A,B,A,B` mask prefix is also absent.

### 6.4 Published codes

| Source | Codes/passwords/unlockables |
|---|---|
| GameFAQs `gba/929317-chicken-shoot/cheats` | none (page has no code list) |
| ChapterCheats GBA page | “No Codes … No Passwords … No Unlockables … No Hints or Secrets … No Easter Eggs” |
| Cheat Happens GBA page | none |

No literal from any published list exists to search, and the ROM contains no such text under any tested encoding.

## 6b. Enumeration

**Space definition (negative result).** The game exposes no code alphabet and no code length. The complete input surface is:

* **10 screen definitions**, of which 8 are menu screens and 2 are in-game overlays/HUD; **0** contain a code/password entry field.
* **1** text-entry field, the highscore name (`-enter name-`), consumed only by the highscore name slot. It is not compared against any constant: the five stored names (`paula`, `mavey`, `rem`, `nelson`, `luk`) are copied to RAM at `0x03005A8E`/`0x02000000`+ and displayed. A password validator would show a `strcmp`/`memcmp` against the buffer; none exists.
* **10** buttons (A, B, Select, Start, Right, Left, Up, Down, R, L). The only sequence-shaped data in ROM is graphics noise; the exhaustive run extraction above eliminates the mask-table and index-table designs.
* **0** published codes to verify, and **0** matching literals in the ROM (ASCII, `+0x20`, UTF-16LE).

**Novel codes.** None can be minted: there is no encoder, decoder, checksum, alphabet, table or validator. This is the §0.2 “no system” case, proven as a statement about the enumerated space above, not as “I did not find it”.

**Bounds proven by rejection.** Rejection is structural rather than per-code:

* No entry widget exists, so an out-of-range or wrong-length code has no screen to be typed into.
* The only text field is capped by the name-entry screen and is not validated.
* The only opaque feature on the multiplayer screen is level selection (`1 -` … `4 -`), which sets the multiplayer level, not a cheat flag.

**Screen reachability observed.** Main menu, options, mode select and connecting/level select were opened in the emulator and identified by reading `0x03004348` and the text buffer `0x03004848` (e.g. `-menu-new gameoptionsabout`, `-options-difficulty-easynormalhardsfx:music:gamma:back`, `-select-arcadeclassicmultiplayerback`, `-connecting-1 -2 -3 -4 -level -back`). The remaining descriptors (pause, redefine keys, highscore, about/credits, level stats) are enumerated from their own tables; they contain only volume/gamma/control settings, score names, credits and stats — no code surface. Their item lists (table in §4) are closed sets, so the negative conclusion does not depend on opening them.

## 7. Validation evidence

**Observed (emulator + RAM):**

* Main menu text buffer at `0x03004848` decoded to `-menu-`, `new game`, `options`, `about`; descriptor `0x083DD384` at `0x03004348`.
* Options screen text buffer decoded to `-options-`, `difficulty`, `easy/normal/hard`, `sfx`, `music`, `gamma`, `back`; descriptor `0x083DD680`.
* Mode select text buffer decoded to `-select-`, `arcade`, `classic`, `multiplayer`, `back`; descriptor `0x083DD570`.
* Connecting/level-select text buffer decoded to `-connecting-`, `1 -`, `2 -`, `3 -`, `4 -`, `level -`, `back`; descriptor `0x083DDF74`, `d7=2`.
* Main → mode select with `A` at cursor `(52.9, 38.3)`; mode select → connecting with `A` at `(50–62, 81–90)`; `B` returned from connecting to mode select and from options to main; options opened with `A` at `(71, 64)`.
* Ten-button fuzz at main-menu hotspots: only `A` changed the screen; no button produced a code/flag/unlock state.

**Derived (disassembly / data):**

* The full screen-descriptor tables, item handlers and text inventory in §4/§6.
* The input edge detector and the key-mask table.
* The absence of code/password/debug keywords, of any code-entry widget, and of any referenced button sequence table.

**Inferred:**

* The `test arcade` / `test classic` strings are a cut test entry (zero xrefs, same layout as the mode-select items).
* Multiplayer `level -` changes the link level only; no persistent unlock flag is written (no save/EEPROM write path is reached by that screen).

## 8. Unknowns

* The pause, redefine-keys, highscore and credits screens were not opened through normal input in this session; their complete item inventories are nevertheless parsed from their descriptor tables and contain no code entry.
* Whether the menu’s hover hitboxes are the intended final tuning: several item hotspots are narrow (e.g. new game requires `y≈38` while the item object’s stored position is `y=67`), which is a UI quirk, not a hidden selector.
* The game’s save type was not isolated; the absence of persistent progression is consistent with the reviewed behaviour that high scores do not survive power-off, but this report does not claim a save-format result.

## 9. Tooling

* `binutils-arm-none-eabi` (`objdump -M force-thumb`), Python 3 (`struct`, `zlib`), mGBA SDL on `Xvfb :244` with `openbox`, `xdotool`.
* Scripts in `/tmp/opencode/chickenshoot`: `myserver.py`/`server2.py` (pty-controlled mGBA debugger and frame stepping), `snap.py` (extract `gbAs` from `.ss1`), `differ.py` (IWRAM/EWRAM diff), plus ad-hoc pointer/mask scanners described above.
* Savestates were read as PNG `gbAs` zlib chunks; no screenshots or image assets were used as evidence.

## 10. Legal note

No ROM, extracted graphics, music or game text is redistributed here; the report contains only hashes, addresses, structural tables and original analysis.
