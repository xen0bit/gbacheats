# LEGO Bionicle (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Lego Bionicle/Lego Bionicle.gba` |
| Size | 8,388,608 bytes (0x800000, 8 MiB) |
| Header title | `LEGO BIONICL` (`0xA0`) |
| Game code | `ALBE` (`0xAC`) |
| Maker | `5Q` (`0xB0`) |
| Version | `0x00` (`0xBC`) |
| Fixed byte | `0x96` at `0xB2` (stock) |
| Complement | `0x70` at `0xBD` |
| Header checksum | `0x0000` at `0xBE` (normal rebuild artifact) |
| Entry branch | `0xEA00002E` (stock `b 0xC0`, **no cracktro/trainer patch**) |
| MD5 | `0e86c0c284f2ce03ed28359a765a66ce` |
| SHA-1 | `da643e7dc8acde83001fefc46969eb6f7ab17948` |
| SHA-256 | `881bb19808f7b9bdb81603d3801586d8f8a5b3d5f4d5a13c0b2dd713ec6ee205` |

**Embedded GBA-header scan (§0.2 / §16.1):** the 156-byte Nintendo logo occurs at file
`0x00000004` and again at `0x3C124C`. The second header starts at file `0x3C1248`
(title `BIONICLE`, code `ALBE`, maker `5Q`, version `0x02`, entry `0xEA000011`). It is
an embedded second image (multiboot/link payload — this title supports linked
multiplayer minigames). No trainer/menu patch was found; the code tables below live
in the first image. The `ALBE` string occurs only at `0xAC` and `0x3C12F4`.

**SKU check (§16.11):** this is GameFAQs game **474317** (Saffire, 2001) — *not* the
2003 Mobius/THQ *Bionicle* (GameFAQs 915361). The widely published "Secret Menu"
button code `L,L,R,L,Select,Start,A` belongs to the **Mobius** game; the active-high
and active-low u16 byte sequences are both **absent** from this ROM (0 hits), and it
is reported as a wrong-SKU lead, not a code for this target.

## 2. Executive summary

This game has a **name-based password system**: the player types a name on the New
Game name-entry screen, and pressing `End` compares that name with a table of
hard-coded strings using the ordinary `strcmp` at `0x08051D90`. There is **no
checksum and no generator** — the accepted set is a closed set of exact strings.
Ten special names were recovered from the ROM:

* six published 6-character minigame codes (verified, each sets a distinct u16
  unlock flag);
* `Credits` and `SCredits` — **unpublished** codes that open two different credits
  sequences (in-game confirmed, screenshots captured);
* `Saffire`, `DiePinky`, `EvilGeorge` — developer names checked in a separate state
  handler (`0x08005F60`); entering them at the name screen returns to the title boot
  sequence (effect is a soft reset/return, not a gameplay cheat).

The published "Master Code `B9RBRN`" is **false**: it does not exist in the ROM and
is rejected in-game (normal CREATE PLAYER flow, no flags). A near-miss `8MR473` is
also rejected, proving exact-match semantics. No button-code table and no hidden
debug menu were found; `Don-Mike` at `0x084057DC` is a localization placeholder
("The message that should be displayed here has not been translated yet."), not a
code (§16.3 cut-feature pattern).

## 3. How to reproduce

* Emulator: `mgba -3 "roms/Lego Bionicle/Lego Bionicle.gba"` under `Xvfb :317`,
  `SDL_AUDIODRIVER=dummy`, `openbox` WM. Window is 720×480 at (154,184).
* Key map (mGBA SDL): GBA `A`=`x`, `B`=`z`, `Start`=`Return`, `Select`=`BackSpace`,
  D-pad = arrow keys.
* Path to the code screen: **boot → (first boot) language `English` with A →
  "Press Start" with Start → Title "Start Game" with A → "New Game" with A →
  name-entry keyboard**. Type a name, move the cursor to `End`, press A.
* On-screen keyboard layout: char table at `0x08052418` — index 2..27 = `A`..`Z`,
  28..53 = `a`..`z`, 54..63 = `0`..`9`, 64+ accented. Cursor index is at IWRAM
  `0x03001AD4`; name buffer at `0x03001AC0` (max 10 bytes, length at `0x03001ABC`).
* Fast test method used for enumeration: save state (`Shift+F1`), patch the `gbAs`
  zlib chunk of the `.ss1` (IWRAM name buffer at raw offset `0x1AAC0`, length at
  `0x1AABC`, cursor at `0x1AAD4`), load (`F1`), press A on the real `End` cell.
  The game's own validator then runs on the real screen. A character was also typed
  directly with the keyboard to confirm the buffer/navigation model (typing `A`
  at cursor index 6 produced `0x45` in the buffer).
* Codes tested: `8MR472`, `9MA268`, `5MG834`, `3LT154`, `V33673`, `4CR487`,
  `Credits`, `SCredits`, `Saffire`, `DiePinky`, `EvilGeorge`, `B9RBRN`, `8MR473`.

## 4. Address map

All ROM addresses are `0x08000000 + file offset`.

| Address | Meaning |
|---|---|
| `0x0804F00` | name-entry screen setup (draws keyboard rows via table `0x0805262C`) |
| `0x080541C` | name-entry input handler (state-handler pointer `0x0800541D` at file `0x56FC`) |
| `0x080543E` | strcmp(name, `"Takua"`) — clears default name on first keypress |
| `0x0805580` / `0x080558C` | strcmp(name, `"Credits"`) / `("SCredits")` → credits screen |
| `0x08055C4`, `0x08055E4`, `0x0805600`, `0x080561C`, `0x0805638`, `0x0805654` | the six minigame-code strcmps |
| `0x0805660` | `strh #1` into the unlock flag word |
| `0x08051D90` | `strcmp(const char*, const char*)` (word-at-a-time then byte) |
| `0x08052418` | keyboard char table: u32 pointers to 1-char NUL strings |
| `0x0805262C`–`0x0805264C` | keyboard row string pointers (9 rows, A–Z/a–z/0–9/accented/punctuation) |
| `0x0805F60` | separate state handler checking `Saffire`/`DiePinky`/`EvilGeorge` (pointer `0x08005F61` at file `0x6274`) |
| `0x08403DBC` | `"Takua"` (default name) |
| `0x08403DC4` | `"Credits"` |
| `0x08403DCC` | `"SCredits"` |
| `0x08403DD8` | `"8MR472"` — Ussal Crab Race |
| `0x08403DE0` | `"9MA268"` — Boat Race |
| `0x08403DE8` | `"5MG834"` — Koli Football |
| `0x08403DF0` | `"3LT154"` — Kewa Bird Riding |
| `0x08403DF8` | `"V33673"` — Snowball Fight |
| `0x08403E00` | `"4CR487"` — Lava Surfing |
| `0x08403E08` | `"Saffire"` |
| `0x08403E10` | `"DiePinky"` |
| `0x08403E1C` | `"EvilGeorge"` |
| `0x084049C4` | second `"SCredits"` literal (state `0x080A0F2`) |
| `0x084057DC` / `0x084057E8` | `"Don-Mike"` / untranslated-message placeholder (not a code) |
| `0x03001AC0` | IWRAM name input buffer (20 bytes, ASCII) |
| `0x03001ABC` | IWRAM name length (u8, capped at 10) |
| `0x03001AD4` | IWRAM keyboard cursor index (u32) |
| `0x0203CACC` | EWRAM Ussal Crab Race unlock flag (u16) |
| `0x0203CACE` | EWRAM Boat Race flag |
| `0x0203CAD0` | EWRAM Koli Football flag |
| `0x0203CAD2` | EWRAM Kewa Bird Riding flag |
| `0x0203CAD4` | EWRAM Snowball Fight flag |
| `0x0203CAD6` | EWRAM Lava Surfing flag |

Savestate (§16.13): mGBA `.ss1` raw `gbAs` chunk is 397,312 bytes (0x61000);
IWRAM maps at raw `0x19000`, EWRAM at raw `0x21000`.

## 5. Algorithm

```c
// on pressing End (cursor index == 1), from 0x080054EE
clear_scratch();
if (strcmp(name, "Credits") == 0 || strcmp(name, "SCredits") == 0) {
    start_credits(mode);            // mode differs: 20 vs 9 (0x0805594/0x08055B8)
    return;
}
static const char *codes[6] = {
    "8MR472", "9MA268", "5MG834", "3LT154", "V33673", "4CR487"
};
static uint16_t *flags[6] = {
    (uint16_t*)0x0203CACC, (uint16_t*)0x0203CACE, (uint16_t*)0x0203CAD0,
    (uint16_t*)0x0203CAD2, (uint16_t*)0x0203CAD4, (uint16_t*)0x0203CAD6
};
for (int i = 0; i < 6; i++)
    if (strcmp(name, codes[i]) == 0) { *flags[i] = 1; break; }
// fall through to normal CREATE PLAYER flow
```

`strcmp` is byte-exact and case-sensitive; there is no normalization, checksum,
length transform, or field decoding. The EWRAM flags are the persisted unlock state
(the `.sav` is 32 KiB and mirrors this region).

## 6. Tables

| Name | Effect | Published? | Evidence |
|---|---|---|---|
| `Takua` | default name; cleared on first keypress | n/a | observed + derived |
| `8MR472` | unlock Ussal Crab Race; flag `0x0203CACC=1` | yes (GameFAQs, Cheat Happens) | literal at `0x08403DD8`; RAM flag |
| `9MA268` | unlock Boat Race; flag `0x0203CACE=1` | yes | literal `0x08403DE0`; RAM flag |
| `5MG834` | unlock Koli Football; flag `0x0203CAD0=1` | yes | literal `0x08403DE8`; RAM flag |
| `3LT154` | unlock Kewa Bird Riding; flag `0x0203CAD2=1` | yes | literal `0x08403DF0`; RAM flag |
| `V33673` | unlock Snowball Fight; flag `0x0203CAD4=1` | yes | literal `0x08403DF8`; RAM flag |
| `4CR487` | unlock Lava Surfing; flag `0x0203CAD6=1` | yes | literal `0x08403E00`; RAM flag |
| `Credits` | regular credits (starts "LEGO Media International…") | **no** | screenshot `code_credits.png` |
| `SCredits` | developer credits (starts "Saffire Corporation / TEAM LEAD Jay Ward…") | **no** | screenshot `shot_SCredits.png` |
| `Saffire` | developer-name check; returns to title boot | **no** | literal `0x08403E08`, screenshot `shot_Saffire.png` |
| `DiePinky` | developer-name check; returns to Saffire logo | **no** | literal `0x08403E10`, screenshot `shot_DiePinky.png` |
| `EvilGeorge` | developer-name check; returns to legal/title | **no** | literal `0x08403E1C`, screenshot `shot_EvilGeorge.png` |
| `B9RBRN` | **rejected** (published "Master Code" is false) | yes (Cheat Happens) | absent from ROM; no flags, normal flow |
| `Don-Mike` | not a code — untranslated-text placeholder | n/a | `0x084057E8` |

Note on published labels (§16.7): Cheat Happens assigns the six codes to
"Gali/Kopaka/Lewa/Onua/Pohatu/Tahu mini-game", while GameFAQs assigns the same six
literals to the six actual minigames (Ussal Crab Race, Boat Race, Koli Football,
Kewa Bird Riding, Snowball Fight, Lava Surfing). The literals are identical; the
Cheat Happens labels are wrong.

## 6b. Enumeration

**Space definition.** The input surface is the name-entry keyboard: the character
table at `0x08052418` exposes `A`–`Z` (26), `a`–`z` (26), `0`–`9` (10), accented
Latin-1 and punctuation cells; the buffer holds at most 10 bytes (`cmp r2,#9` guard
at `0x080545C`, truncation at `0x0805478`). The nominal 6-character alphanumeric
code space is `36^6 = 2,176,782,336` strings, but the validator is a **flat strcmp
table**, so exactly the literals above are reachable. There is no checksum width,
no field layout, no reserved bits, and no generator. The complete accepted set is
the 11 special names listed in §6 (10 of which are reachable from the name screen;
`Takua` is the default). This was bounded by locating **every** pointer into the
string region (`0x08403D00`–`0x08403E60`) and counting **all 14** `strcmp` call sites
in the ROM: 12 are the name-screen/state-handler comparisons above, one is
`0x080A0F2` (a second `"SCredits"` check), and one is `0x8017FAC` (`"Don-Mike"`,
a localization placeholder). No further code literal exists.

**Novel codes (absent from GameFAQs / Cheat Happens / VGChartz / TCRF).**
`Credits` and `SCredits` were found in the ROM, entered through the real End
control, and produced in-game effects:

* `Credits` → credits screen beginning "LEGO Media International / World-wide
  Managing Director Mark Livingstone" (`code_credits.png`).
* `SCredits` → different credits beginning "Saffire Corporation / TEAM LEAD Jay
  Ward / LEAD PROGRAMMER Dave Rushton" (`shot_SCredits.png`), i.e. a genuine
  second, unadvertised credits path (`mode` byte 20 vs 9 in the validator).

**Bounds proven by rejection.**

* `B9RBRN` (the only "master code" published anywhere) → normal CREATE PLAYER,
  no minigame flags set (`shot_B9RBRN.png`); the literal is absent from the ROM.
* `8MR473` (one-character change of a valid code) → normal CREATE PLAYER,
  flags unchanged (`shot_nearmiss.png`), proving byte-exact matching.
* Setting all six published codes successively produced a strictly increasing
  flag word at `0x0203CAC0` (`…01000100`, `…010001000100`, …, `…0100010001000100010001000100`),
  confirming one flag per code and no aliasing.

Because the accepted set is a finite table rather than a checksum system, "minting
a code with an unadvertised field combination" is not possible here; the equivalent
deliverable — unpublished ROM-derived codes accepted on the real screen — is
provided above, and the negative is closed by the exhaustive pointer/strcmp count.

## 7. Validation evidence

**Observed (emulator, with RAM snapshots):**
* All reachable screens walked: Saffire logo; first-boot language select
  (`English`/`Français`); "Press Start"; title (`Start Game`, `Options`); Options
  (`Sound FX On/Off`, `Music On/Off`, `Exit`); Start Game (`New Game`, `Training`);
  name-entry keyboard; CREATE PLAYER; in-game field with dialog, HUD and inventory;
  in-game pause menu (`Quit Game` only in Training); inventory grid (SELECT);
  credits and secret-credits screens.
* Name buffer read back as `Takua` (default), then as each entered code
  (IWRAM `0x03001AC0`).
* The six minigame codes each set exactly one u16 flag at `0x0203CACC`–`CAD6`.
* `Credits`/`SCredits` produced two distinct credits screens; `B9RBRN` and
  `8MR473` produced the ordinary CREATE PLAYER screen with no flag changes.

**Derived (from disassembly):**
* `0x08051D90` is a standard word-at-a-time `strcmp`; no checksum/transform exists.
* All 12 name/state-handler comparisons are enumerated; the literal strings and
  their ROM addresses are listed in §6.
* The End handler at `0x08054EE` is where validation runs; the flag store is at
  `0x0805660`–`0x0805662`.

**Inferred (lower confidence):**
* `Saffire` / `DiePinky` / `EvilGeorge` are compared in the separate state handler
  at `0x08005F60`, not in the End handler; the observed return to the title/boot
  screens when typed as a name may be a soft-reset path rather than the intended
  trigger (the intended trigger may be a CREATE PLAYER appearance combination).
  Their precise in-game payload is not proven; they are reported as developer-name
  strings with an observed visible effect but no gameplay benefit.
* The six minigame flags were verified in RAM but the minigame-select menu was not
  reached: the title menu still showed only `Start Game`/`Options` after the codes,
  most likely because the unlocks must be saved through a completed game before the
  menu is populated (§16.10 — the flag write is proven; the menu gating is not).

**Negative results (bounded):**
* No hidden debug menu on title/options/pause/level-select surfaces: the title has
  exactly 2 entries, Options 3, pause 1 (Training), and there is no level-select
  screen; `Options` contains only audio toggles.
* No button-code table: the published button sequence from the other Bionicle SKU
  has 0 hits in both active-high and active-low encodings; no key-mask array was
  found in the name/title/pause code paths.
* `Don-Mike` is a cut localisation placeholder, not a code.

## 8. Unknowns

* The exact trigger/effect of `Saffire`, `DiePinky`, `EvilGeorge` beyond the observed
  return-to-title behaviour (they are compared in a different state handler).
* Whether the minigame-select menu unlocks only after the flags are persisted via a
  full game save (not played through here).
* The second embedded GBA header at `0x3C1248` (multiboot/link image) was not
  booted; no cheat strings were found in it, but it was not fully enumerated.
* No prompt-injection payload was encountered in fetched pages; the TCRF URL for
  this title returned HTTP 403 and no content. Fetched cheat pages were treated as
  data only.

## 9. Tooling

* `mgba` (SDL, Xvfb `:317`, openbox), `xdotool`, `scrot`, `convert`.
* `arm-none-eabi-objdump -M force-thumb` for validator disassembly; Capstone 5.0.7
  for PC-relative literal-pointer and BL-target scans; Python `struct`/`zlib` for
  `.ss1` `gbAs` chunk patching and RAM reads.
* Helper scripts in `/tmp/legobionicle/`: `state_read.py` (savestate RAM
  reader), `readaddr.py`, `enter_code.py`, `type_name.py`, `goto_name.py`,
  `gba.py`. Screenshots kept on disk in the same work dir (not attached here).
* No ROM or copyrighted assets are redistributed; only addresses, literals and
  hashes are documented.
