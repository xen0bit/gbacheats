# Prince of Persia: The Sands of Time (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Prince of Persia: The Sands of Time.gba` |
| Size | 8,388,608 bytes (0x800000) |
| Header title | `PRINCEPERSIA` |
| Game code | `BPYE` (Europe) |
| Maker code | `41` (Ubisoft) |
| Version | `0x00` |
| Header entry branch | `0xEA00002E` (stock `b 0x080000C0`) |
| Complement / checksum | `0x37` / `0x0000` |
| MD5 | `6d820b583b6ab2cc5c901d56b43e38cb` |
| SHA-1 | `c169e0c60d3e2dd01b09c478de7bb62cadb516d6` |
| SHA-256 | `bd6f9244bfad17b51e556a0b5cba509d9f42952be3e6f0b841c41a9af374dff0` |

**Phase 0 result:** single GBA header at `0x0`; no embedded/sub-image header, no appended
trainer, no cracktro patch (entry word is the stock `0xEA00002E`). The Nintendo-logo
bytes in this build are the variant `24 ff ae 51 69 9a a2 21 …` (not the common
`24 ff ae 51 71 96 af 11 …`), so a logo-based multi-header scan must use the
ROM's own first 16 logo bytes. No patch/trainer detected. The `.sav` created by
mGBA is a 512-byte Flash image with four 64-byte records (`00 00 bb aa 00 22 44 55`
signatures) — ordinary game saves, not trainer data.

## 2. Executive summary

**There is no in-game / developer-intended cheat system in this GBA build: no password
screen, no button-code sequence, no hidden/developer menu, and no level select.**

This is a **bounded negative result**, not an absence of effort:

* The complete UI text bank is plain ASCII (not font/tile-indexed) and is enumerated
  by an explicit master table of **32 screens per language × 6 languages = 192 screen
  descriptors**. Every screen's string-array count is stored as a `u32` immediately
  before its pointer array. The main menu has exactly 3 entries, Options exactly 3,
  the in-game pause menu exactly 3. None of the 192 descriptors names a password,
  cheat, code, debug, secret-menu or level-select screen.
* Every reachable screen was walked in mGBA with screenshots **and** savestate/RAM
  evidence (title/language, main menu, Options, DELETE confirm, START/name entry,
  gameplay, all six inventory tabs, pause menu, sleep prompt, GAME OVER path).
* All 22 published classic-*Prince of Persia* passwords (GameFAQs/GameCube/PS2/Xbox
  lists) were checked literally against the ROM under 16 encodings (ASCII upper/
  lower, reversed, UTF-16/32 LE/BE, XOR, additive, 5-bit packs): **0 hits**.
  Those codes belong to the bonus *PoP1* mini-game in other SKUs; the GBA SKU has
  no such screen. Project Cheat Codes states "no known cheat codes … on Game Boy
  Advance and PC". No GBA password list exists on GameFAQs, VGChartz, TCRF or
  Hidden Palace. (Hidden Palace's debug controls are for the **Xbox demo**, not GBA.)
* No key-mask sequence table exists: scanning the code region for runs of ≥3
  consecutive `u16` values in the GBA key range `0x0001–0x03FF` found 30 runs, all
  instruction/data coincidences, none a cheat sequence. The only special combo in
  the entire text bank is the documented `SELECT + L + R` sleep-wake prompt.
* Undocumented button combinations (L+R+Start+Select, Start+Select, L+R, L+R+A+B,
  Konami code) were pressed in-game; none opened a screen or changed game state.

The only bonus content is **link-cable hardware-gated**: three "Nintendo GameCube
Switches" / "Secret Doors" unlock extras in the *GameCube* version, and linking to
a GBA enables health regeneration in the GC version. These are not codes and are
not reachable by controller input (§16.18-style gated feature).

## 3. How to reproduce

* Emulator: mGBA (SDL), `SDL_AUDIODRIVER=dummy`, `DISPLAY=:319`, `mgba -3 <rom>`.
* Keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`,
  D-pad=arrow keys. Hold keys 50–120 ms (150 ms can double-step menus, §16.2).
* Screen path (US/English): language flag → **START GAME** → enter a 9-character
  profile name → cutscene (A to skip) → gameplay → **Start/Return** pauses into
  the 6-tab inventory; the 4th tab is the **Continue / Sleep / Quit** menu.
  OPTIONS has MUSIC, SFX, CREDITS. Main menu has START GAME, DELETE GAME, OPTIONS.
* Codes tested: none exist. 22 published non-GBA passwords rejected by ROM search;
  five undocumented button combos pressed in-game with no effect.
* RAM evidence: raw state read as `EWRAM = savestate[0x21000:0x61000]`,
  `IWRAM = savestate[0x19000:0x21000]` (verified against mGBA `-d` `r/4` reads:
  state `+0x21000` == `r/4 0x02000000`, state `+0x19000` == `r/4 0x03000000`).
  Main-menu selector is IWRAM `0x03002740` = 0 / 1 / 2 for
  START / DELETE / OPTIONS. EWRAM `[0x02000000]` = `0x080A3A8C` in gameplay,
  `0x00000000` on menu screens — a clean screen witness.
* Savestates/snapshots and scripts are under `/tmp/opencode/princepersia/`.

## 4. Address map

| Item | ROM address (file offset = addr − 0x08000000) | Notes |
|---|---|---|
| Entry branch | `0x08000000` | `0xEA00002E` |
| Input init/read | `0x0808F7CC`, `0x0808F7F0` | `held = ~KEYINPUT & 0x3FF`; `pressed = held ^ prev`; key-history stack at struct `+8` |
| KEYINPUT literal xrefs | `0x0808F7F0`, `0x0808F808`, `0x080911EC`, `0x08091208` | `0x04000130` |
| UI text bank (EN) | `0x08096A50`–`0x0809730C` | plain ASCII, NUL-terminated |
| – main menu strings | `0x08096A44` | `START GAME`,`DELETE GAME`,`OPTIONS` (3) |
| – options strings | `0x08096A70` | `MUSIC`,`SFX`,`CREDITS` (3) |
| – pause strings | `0x08096AC8` | `Continue`,`Sleep`,`Quit` (3) |
| – sleep prompt | `0x08096B0C` | `SELECT + L Button + R Button` |
| – bonus strings | `0x08097244`, `0x08097268`, `0x08097284` | GCN switches / secret doors / GCN bonus |
| **Master UI screen table (EN)** | **`0x080972D4`** | **32 × `{u32 count, u32 ptr}`** |
| Same table, FR / ES / IT / NL / DE | `0x08099234`, `0x0809B360`, `0x0809D148`, `0x0809F00C`, `0x080A0F88` | 32 entries each |
| Assert strings | `0x080A3FF0`–`0x080A402C` | `ASSERT!`, `Source Code Filename:`, `Function: `, `Line: ` — C assert handler, not a debug menu |
| RAM: menu selector | IWRAM `0x03002740` | 0/1/2 = START/DELETE/OPTIONS |
| RAM: screen witness | EWRAM `0x02000000` | `0x080A3A8C` gameplay; `0` menus |
| RAM: game state | EWRAM `0x0200xxxx` | Flash save mirrored; inventory values held here |

## 5. Algorithm

No validator exists. The relevant algorithms are:

1. **UI dispatch**: for language `L`, table `T_L` at the base in §4 is indexed by
   screen ID. Each entry is `{count, ptr}`; `ptr` points to an array of `count`
   `u32` pointers to NUL-terminated ASCII strings. The render loop draws exactly
   `count` rows — so a hidden menu row cannot exist without increasing `count`.
2. **Input**: `held = ~(*0x04000130) & 0x3FF`; `pressed = held ^ old`;
   `old = held`. A bounded key-history stack is maintained at struct `+8`, used
   for movement/combat, not for code entry. No comparison against a fixed key
   sequence was found anywhere in the image.
3. **Save**: 512-byte Flash, four 64-byte slots, signature `00 00 bb aa 00 22 44 55`;
   profile names and progress are stored there. No password/checksum encoder exists.

## 6. Tables

Master UI screen table, English (`0x080972D4`), all 32 descriptors with decoded
string arrays:

| # | Count | Strings (abridged) |
|---:|---:|---|
| 0 | 3 | START GAME, DELETE GAME, OPTIONS |
| 1 | 3 | MUSIC, SFX, CREDITS |
| 2 | 2 | ON, OFF |
| 3 | 1 | Delete this game? |
| 4 | 2 | Yes, No |
| 5 | 3 | Continue, Sleep, Quit |
| 6 | 3 | Are you sure?, Yes, No |
| 7 | 4 | SLEEP:, To resume, press, SELECT + L Button + R Button, (empty) |
| 8–27 | 2–4 each | tutorial hints (jump, roll, walling, rebound, rings, scrolls, medals, …) |
| 28–30 | 1 each | X/3 GameCube Switches; X/3 Secret Doors Opened; New Bonus on GameCube |
| 31 | 2 | GAME OVER, Press START to continue |

Critical counts are identical in all six languages (0→3, 1→3, 5→3, 28–30→1,
31→2); the few differences in rows 8–27 are line-break choices in translated
tutorial text, not extra entries.

Items enumerated by the same table (all in-game collectibles, none cheat-granted):
Freeze Ring, Slow-Down Ring, Life Potion, Sands Of Time, Antidote, Elixir;
8 medals (Copper, Jade, Onyx, Tagua, Azurite, Olivine, Spinel, Zircon);
15 Scrolls (Air Jump, Rolling, Ledges, Walling, Rebound, Fury, Rewind, Gathering,
Secret Medals, Farah, Absorbtion, Caution, Freeze, Slow-Motion, Liberation).

## 6b. Enumeration

**Code space size: 0.** There is no alphabet, no input length, no checksum, no
validator, no hard-coded code table and no level-select handler. The enumeration
that bounds this claim:

| Search space | Method | Result |
|---|---|---|
| 69,238 ASCII strings (`strings -n 4`) | keyword grep for password/cheat/code/debug/secret/unlock/level | 0 cheat-relevant hits; only `ASSERT!`/`Source Code Filename:`/`Function:`/`Line:` at `0x080A3FF0+` (C assert) |
| UI screens | 6 × 32 `{count,ptr}` descriptors | 192 descriptors; 0 password/cheat/debug/level-select screens |
| Menu entries | decoded pointer arrays | main 3, options 3, pause 3, delete-confirm 2, sleep 4 — all walked |
| 22 published passwords × 16 encodings | literal/encoded ROM search | 0 hits |
| Button-code masks | u16 runs in `0x0001–0x03FF` over code region | 30 runs, none a code sequence; only documented combo is SELECT+L+R |
| Undocumented combos | 5 combos pressed in emulator | no new screen/state |
| Key-input xrefs | `0x04000130` literal scan (4 sites) | generic input handler only; no fixed-sequence compare |

**Novel code: none can be minted, because no code system exists.** Per §0.2, a
negative result is bounded above by this table: the searched spaces (strings,
screen descriptors, menu tables, published literals, key masks, live combos) are
fully enumerated, and no candidate code surface was found in any of them. No
"unpublished code" claim is made. Bounds are proven by the rejection tests above
(published literals absent, undocumented combos inert) and by the exact counts in
the master table.

## 7. Validation evidence

* **Observed (emulator)**: language select; main menu (3 rows); Options (3 rows,
  MUSIC toggled ON→OFF during testing); DELETE confirm; 9-character name entry;
  cutscenes; gameplay; six inventory tabs; Continue/Sleep/Quit menu; undocumented
  button combos produced no visible change. Screenshots on disk under
  `/tmp/opencode/princepersia/` (e.g. `w_title_crop.png` … `x_tab6_crop.png`,
  `after_combos_crop.png`).
* **Observed (RAM)**: savestate EWRAM/IWRAM hashes distinct per screen;
  IWRAM `0x03002740` = 0/1/2 for the three main-menu selections; live `r/4`
  reads matched savestate bytes at `+0x21000`/`+0x19000`.
* **Derived (static)**: full ASCII text bank; 6×32 screen table with explicit
  counts; menu string arrays; input handler disassembly; 0 published-literal hits
  under 16 encodings; no key-mask sequence table.
* **Inferred (low confidence, labelled)**: the 9-character name field on START
  GAME is a profile label written to Flash, not a password — supported by the
  absence of any validator/comparison table in the enumerated UI, but no
  exhaustive call-site analysis of the save routine was performed.
* **Not instructions**: all fetched web/ROM text was treated as data; the Hidden
  Palace "modded Prince.bf" download and Xbox-demo debug controls were recorded
  as other-SKU content and not acted on.

## 8. Unknowns

* The save routine's consumer set was not traced instruction-by-instruction; the
  "profile label, not password" conclusion rests on the complete absence of a
  validation surface rather than on a data-flow proof.
* GameCube-link-gated content (three switches, bonus rooms, GC-side extras) was
  not exercised — no GameCube or GCN-GBA cable is available. It is hardware-gated,
  not input-gated, and is out of scope for controller cheats.
* The 512-byte Flash record layout beyond its four signatures was not fully
  decoded; not needed for the cheat question.

## 9. Tooling

* `arm-none-eabi-objdump -M force-thumb` (input-handler disassembly).
* Python 3 + Capstone 5.0.7 (`xref.py` literal/PC-relative scans),
  `pwenc.py` (published-code encoding search), `crib.py`, `keyscan.py`.
* mGBA SDL under Xvfb `:319` + openbox; `xdotool` XTEST input; `scrot`+ImageMagick
  screenshots; mGBA `-d` CLI debugger via a pty (`script -q -f`) for `r/4` RAM reads;
  savestate `gbAs` zlib chunk parsed for EWRAM/IWRAM (`ss.py`, `ramsnap.py`).
* GDB stub on port 2345 was blocked by other sessions (guide §16.2), so the
  `-d` pty debugger and savestate diffing were used instead (§16.13).
* No ROM or copyrighted assets are redistributed; only addresses, hashes, counts,
  and tool code are published.

## 10. Legal note

No ROM image, extracted graphics, music, or game text is redistributed. Only
hashes, addresses, algorithms, and independently written analysis scripts appear
here.
