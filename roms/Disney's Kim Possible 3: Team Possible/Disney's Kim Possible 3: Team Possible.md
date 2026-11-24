# Disney's Kim Possible 3: Team Possible (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Disney's Kim Possible 3: Team Possible/Disney's Kim Possible 3: Team Possible.gba` |
| Size | 8,388,608 bytes (0x800000, exactly 8 MiB, no appended data) |
| Header title | `KIMPOSSIBLE3` (0xA0, space/NUL padded) |
| Game code | `BQPE` (0xAC) |
| Maker code | `4Q` (0xB0) — Buena Vista / Disney |
| Software version | 0x00 (0xBC) |
| Main unit / device | 0x00 / 0x00 |
| Entry word | `0xEA00002E` → 0x080000C0 (stock ARM branch, unmodified) |
| Complement check | 0x2F (0xBD) — **correct** for 0xA0–0xBC (recomputed 0x2F) |
| Header checksum | stored `0x0000` (0xBE); recomputed 0x2F. The complement byte is valid, so this is the usual "tool left the field zero" case, not a modified header |
| Nintendo logo | canonical, **one** hit at file 0x4 — single image, not a multi-game pack |
| Save hardware | EEPROM 512 B (SDK id `EEPROM_V124` at file 0x181DD4; mGBA creates a 512-byte `.sav`) |
| CRC32 | `FDEC60EC` — matches the published USA (En,Fr) serial AGB-BQPE-USA |
| MD5 | `3c629e441d4842ccb9d05e1c91853f80` |
| SHA-1 | `47e99dcdbd97238778318dfd53421690e7acb48e` |
| SHA-256 | `fcfd38827038c5d40f9b57f8b8d1a2d5f60c2f7dc8c2d3bbdb4ecce6300bff94` |

**Patch/trainer check.** Entry branch is the stock `b 0x080000C0`; the complement byte is
valid; there is no cracktro string (`SUNHORS`/`MODE7`/`CRC BANDIT`/`PDX`/`FAIRLIGHT` = 0 real
hits; the four `grep` hits are random data and the French word `ENTRAiNER`); no second header,
no trainer menu, no appended payload. The image is a retail build. Engine fingerprints:
A2M (Artificial Mind & Movement) logo asset at boot, Shin'en audio banner
`Shin'en Multimedia. Code: B.Wodok` at file 0x1812E6 (an audio-engine credit, the known
§11 false positive).

## 2. Executive summary

**There is no typed password, keypad, cheat-code entry or reachable debug menu in this
retail SKU.** The game's secret content is (a) a save-gated unlock tree (slot-menu
**Extras**, mode-select **Global Justice** and **Minigames**, each dimmed and
cursor-skipped on a fresh save) and (b) a **20-entry developer boot / episode-select
directory compiled into ROM but referenced by exactly one scene-init routine whose gate
can never be true**. The only hidden *input* that exists and works is the SDK
**A+B+Select+Start soft reset**, implemented in the game's own code at `0x080132AC`, not
merely by the BIOS.

Findings in order of importance:

1. **No code-entry surface.** Every screen reachable from boot was walked (title,
   Load Game, profile/slot menu, mode select, Options, Credits, Erase Game, Multiplayer
   link wait, in-game pause). None has a text field, keypad, alphabet or "enter code"
   row. A whole-image decode of the message bank (2,102 `FF FE`-terminated strings)
   contains **0** `PASSWORD`, `PASSCODE`, `CHEAT`, `UNLOCK`, `DEBUG`, `ENTER CODE`,
   `ENTER YOUR` or `LEVEL SELECT` strings; the only `SECRET`/`CODE`/`BONUS` hits are
   story dialogue and French credit/role words.
2. **One hidden button combination exists: A+B+Select+Start → soft reset.** The handler
   at `0x080132AC` reads the held mask from the input struct (`0x0200C100+2`), tests
   `held & 0x000F == 0x000F`, fades `BLDCNT/BLDY`, then calls the SDK reset at
   `0x080492DC` (`SP=0x03007F00; SWI 1 r0=0xE0; SWI 0`). Observed twice: once in a
   cutscene and once on the title screen → `©2005 Disney` splash. **No published list
   for this SKU documents it.** Variants `A+B+Select` and `A+B+Start` do **not** reset
   (observed), which fixes the mask.
3. **The unlock tree is save-gated, not code-gated.** On a save containing only
   `World 1 / 00% / 00:00`, the slot menu shows `Continue / Erase Game / Extras(dim) /
   Options / Credits`, and the mode select shows `Story Mode / Multiplayer /
   Global Justice(dim) / Minigames(dim)`; pressing Down from Multiplayer skips both
   dimmed rows and wraps to Story Mode (observed). Contents named in ROM:
   `PHOTO ALBUM` (0x7488B8), `MINIGAME 1/2/3` (0x7502F8/0x750310/0x750328),
   `MUSIC` (0x750394), `GLOBAL JUSTICE` (0x75016F), `EXTRAS` (0x75009C).
4. **A 20-entry A2M developer directory is present but dead.** Table at
   `0x0818B040–0x0818B270`, `0x1C`-byte records, labels at 0x0804A4B4+:
   `(text id 0x2001)`, `Obj Viewer`, `Music Player`, `Fx Player`, `Room 01..08`,
   `Normal Boot`, `Episode 1..3`, `Global Justice`, `Tangram`, `MasterKim`,
   `Rufus Game`. Only one literal in the whole image points at it (`0x0818B040` at file
   0x3C104; the companion `0x0818B03C` at 0x3C0F4). The scene-init code that consumes it
   (`0x0803BFFC–0x0803C042`) creates the menu objects only when `[0x200BFB4]+8 & 2`
   **and** the active scene record's `+0x14` bit is set. **All 185 scene records in the
   image have `+0x14 == 0x0000`**, and no observed writer sets bit 1 of the runtime
   object (the one direct writer to `[obj+8]` ORs 0x8; bit 1 read as 0 in three
   savestates). The menu cannot be produced by any input or scene.
   This is the same data TCRF lists as "Debug Text" (its labels are the ASCII block at
   file 0x4A484).
5. **Published "codes" for this SKU are host-side memory patches only.** GameFAQs,
   GameHacking.org and Almar's Guides list 12 **CodeBreaker** entries (master code
   `97C2CC187F35 / BE602C6068C2 / 776B175E63A2`, then health/tools/unlock writes). None is
   an in-game password or button code and none appears in the image as a literal (device
   codes are encrypted and applied by the cheat cartridge, not typed into the game).

Per §0.2 this is therefore a **bounded negative** with the exact menu, text and input
spaces bounded below, plus the unpublished soft-reset combination and the 20-entry dead
developer directory as the enumeration this ROM actually offers.

## 3. How to reproduce

Emulator: mGBA SDL 0.10.5 (`mgba -3`) on `Xvfb :326`, `SDL_AUDIODRIVER=dummy`, `openbox`.
Keymap (verified against the input struct, §5.1): `x`=A, `z`=B, `a`=L, `s`=R,
`Return`=Start, `BackSpace`=Select, arrows = D-pad. Hold keys 120 ms, leave ≥250 ms
between presses. `Shift+F1..F10` save state, `F1..F10` load it.

### 3.1 Screen walk (all observed on :326)

| # | Input | Screen | Items / notes |
|---:|---|---|---|
| 1 | boot | Disney Interactive → A2M logo → intro cut-scene → title `PRESS START` | 1 prompt |
| 2 | Start | **Load Game** | 2 slots (`-1-`, `-2-`), each `Empty` on a fresh save |
| 3 | A on a slot | **Profile menu** | `Start Game` (or `Continue` when the slot has data) / `Erase Game` / `Extras` (dim on a fresh save) / `Options` / `Credits` |
| 4 | A on Start/Continue | **Mode select** | `Story Mode` / `Multiplayer` / `Global Justice` (dim) / `Minigames` (dim) |
| 5 | A on Options | **Options** | `Language: English`, `Sound: YES`, `Music: YES` |
| 6 | A on Erase Game | **Erase Game** | both slots, right pane `Clear Data? Yes / No` |
| 7 | A on Credits | **Credits** roll (Disney Interactive / A2M / roles) | B returns |
| 8 | A on Multiplayer | **Waiting for connection** | link-cable wait, `B Back`; no code or password |
| 9 | Start in gameplay | **Pause** | `Map` (dim), `Continue`, `Options`, `Quit` |
| 10 | Down on `Multiplayer` (mode select) | — | cursor skips both dim rows and wraps to `Story Mode` |

Menu sizes were confirmed by cursor clamping/wrapping; the profile menu and mode select do
not scroll, so their item counts are complete.

### 3.2 Hidden input tests (observed)

| Test | Input | Result |
|---|---|---|
| SDK reset, title screen | hold A+B+Select+Start 1.5 s | fades to white → `©2005 Disney / LICENSED BY NINTENDO` |
| SDK reset, cut-scene | same | same reset |
| Mask rejection 1 | hold A+B+Select 1.2 s on title | nothing; title unchanged |
| Mask rejection 2 | hold A+B+Start 1.2 s on title | no reset (Start performs its normal advance) |
| Classic title sequences | Konami (U,U,D,D,L,R,L,R,B,A), L,R,L,R,L,R, Select×3, U,D,U,D,B,A | no new screen/flag; Start still opens the normal `Load Game` |
| Dimmed rows | Down from `Multiplayer` | `Global Justice`/`Minigames` cannot be selected |

### 3.3 Reading RAM without a debugger

mGBA `.ssN` files are PNGs with a zlib-compressed `gbAs` chunk. For this 8 MiB image the
state is 397,312 bytes; **IWRAM at 0x19000, EWRAM at 0x21000** after decompression
(`/tmp/kp3/state.py`). All RAM claims below were read this way. The same parser
can rebuild a state with patched bytes (`patchstate.py`), which was used only for
exploration and is labelled as such.

## 4. Address map

`rom_address = 0x08000000 + file_offset`.

### 4.1 Input / engine

| Address | Meaning |
|---|---|
| 0x08004010 | Key poll: `r0=[0x0200C100]`, `r1=0x04000130`, `r2=ldrh[r1]`, `r1=0x03FF & ~r2`, calls 0x08003ED0 |
| 0x08004040 | literal `0x04000130` (the **only** KEYINPUT literal in the image) |
| 0x08003ED0 | Key-state updater: `prev`,`held`,`changed`,`pressed`,`released` + per-key repeat counters |
| 0x0200C100 | **Key state struct**: `+0` prev held, `+2` held, `+4` changed, `+6` pressed, `+8` released, `+10/+12` counters, `+14` second held copy, `+0x18..` repeat state |
| 0x04000130 | KEYINPUT (active low) |
| 0x080132AC | **A+B+Select+Start handler** (see §5.2) |
| 0x080492DC | SDK soft reset: `SP=0x03007F00`, `SWI 1` (`r0=0xE0`), `SWI 0` |
| 0x02001FBC | "already resetting" flag checked by 0x080132AC |
| 0x02014B90 | non-zero guard checked before the fade |

### 4.2 Developer boot directory (dead data)

| Address | Meaning |
|---|---|
| 0x0818B040–0x0818B270 | 20 records × 0x1C bytes: `{u32 label; u32 0; u32 icon_rect_ptr; u32 id; u32 flags; u32 0; u32 0}` |
| 0x0818B03C | companion table pointer (10-entry object at 0x0803BFC6) |
| 0x0804A4B4–0x0804A584 | ASCII labels (file 0x4A4B4): `Obj Viewer` … `Asset Viewer` |
| 0x0804A484–0x0804A494 | `Level`, `MapX`, `MapY` label trio |
| 0x0803BFFC–0x0803C042 | Consumer: creates menu objects when `[0x200BFB4]+8 & 2` and scene `+0x14` bit 0/1 |
| 0x0803C0F4 / 0x0803C104 | The only two literal slots: `0x0818B03C` / `0x0818B040` |
| 0x0200C1A4 | runtime pointer to the active scene record (observed: `0x0872B3D0` Title_Screen, `0x0871059C` MainMenu, `0x08733CF8` cutscene01) |

### 4.3 Menus / text / save

| Address | Meaning |
|---|---|
| 0x07488000–0x07580000 | Message bank: 2,102 `FF FE`-terminated records; text encoding in §5.3 |
| 0x07488B8 | `PHOTO ALBUM` |
| 0x0748A08 | `CREDITS` |
| 0x075005C / 0x0750074 | `ERASE GAME` |
| 0x075009C | `EXTRAS` |
| 0x07502C0 | `LANGUAGE` |
| 0x07502F8 / 0x0750310 / 0x0750328 | `MINIGAME 1` / `MINIGAME 2` / `MINIGAME 3` |
| 0x0750340 | `MINIGAMES` |
| 0x075037C | `MULTIPLAYER` |
| 0x0750394 | `MUSIC` |
| 0x07506CC | `STORY MODE` |
| 0x075016F | `GLOBAL JUSTICE` (menu occurrence; dialogue occurrences at 0x749B5D+) |
| 0x0750410 | `OPTIONS` |
| 0x07507E4 | `START GAME` |
| 0x07502D4 | `LOAD GAME` |
| 0x07502E8 | `MAP` |
| 0x0750498 | `PAUSE` |
| 0x075008C / 0x07504D0 | `QUIT` |
| 0x0748880 | `THIS GAME ONLY SUPPORTS 2 PLAYERS` |
| 0x0710xxx | Scene records (185, see §6.4), e.g. `MainMenu` 0x71059C, `SaveMenu` 0x72A890, `Title_Screen` 0x72B3D0, `PauseMenu` 0x714ABC |
| 0x020160D0 | Save working copy, slot 0 (232 bytes); slot 1 at +0xE8 = 0x020161B8 |
| 0x08042BA0 | Save validator: compares `slot+8` with `0x0818B304` (`A2MW`) and checksums 16 bytes |
| 0x08042C5C | Save writer: 2 slots, stride 0xE8, EEPROM flush |
| 0x0818B304 | ROM magic constant `A2MW` |

## 5. Algorithm

### 5.1 Key state (reimplemented from 0x08004010 + 0x08003ED0)

```
held     = 0x03FF & ~KEYINPUT        # active-high 10-bit mask
prev     = key[+0]; key[+0] = key[+2]; key[+2] = held
changed  = held ^ prev            -> key[+4]
pressed  = held & changed         -> key[+6]
released = changed & ~held        -> key[+8]
```

RAM check (observed, savestate with Right held): `0x0200C100 = 10 00`, `0x0200C102 = 10 00`,
i.e. prev = held = 0x0010 (Right); the keymap is confirmed.

### 5.2 Soft reset (0x080132AC)

```
if (*0x02001FBC != 0) return                 # already resetting
held = *(u16*)0x0200C102
if ((held & 0x000F) == 0x000F) {             # A+B+Select+Start, all four
    if (*0x02014B90 != 0) {
        wait_vblank()
        BLDCNT = 0x00BF; BLDY = 0
        for (i = 0; i <= 30; i++) { BLDY = i; wait_vblank(); }
        BLDY = 31
        0x080492DC(0xE0)                    # SP=0x03007F00; SWI 1; SWI 0
    }
} else if ((held & 0x000F) == 0) {
    *0x02014B90 = 1                         # armed only after a clean frame
}
```

The `else` arm is the SDK edge guard: the reset only fires if every button was released
at least once since boot. This is why a held combo from power-on does nothing until the
title screen has seen a neutral frame.

### 5.3 Text encoding (needed for the text-space search)

One-byte characters plus two escape families:

* `FF FC` = word space, `FF FE` = end of string, `FF FD` = hyphen, other `FF xx` = inline
  icon/substitution.
* `0E` = `.`, `01` = `!`, `07` = `'`, `0C` = `,`.
* **The first letter of each word is stored as `0x21 + (letter - 'A')`** (A=0x21 … Z=0x3A);
  the rest of the word is plain ASCII uppercase. Accented letters in the French bank use
  their own glyph codes (`d`=É, `g`=È, `i`=Î, `c`=Ç, `a`=À, …).

Example: `THE SECRET MONKEY TEMPLE` is
`54 48 45 FF FC 53 45 43 52 45 54 FF FC 2D 4F 4E 4B 45 59 FF FC 34 45 4D 50 4C 45`.
This is why plain `strings` shows `4EMPLE`, `-ONKEY`, `0OSSIBLE` and finds no UI text.

### 5.4 Save record

```
struct save_slot {          // 232 (0xE8) bytes, RAM at 0x020160D0 / +0xE8
  u16 checksum;             // +0x00  sum of bytes 2..15 (checksum field zeroed), mod 0x10000
  u8  unk[6];               // +0x02  language/audio/version bytes (observed 0D 07 0E 07 00 00)
  u8  magic[4];             // +0x08  "A2MW" (RAM byte order; .sav stores it as "WM2A")
  u8  payload[0xD8];        // +0x0C  progress/flags (opaque; World 1 0% = mostly 0 with
};                          //         03 @ +0xC3, 01 @ +0xCB, 05 05 05 05 @ +0xCC, FF @ +0xD3/0xD7/0xF5)
```

The EEPROM `.sav` stores each 8-byte block **byte-reversed** relative to the RAM record
(verified: RAM `+8 = 41 32 4D 57`, `.sav` `0x0C = 57 4D 32 41`). The validator at
0x08042BA0 checks the magic and the 16-bit sum, so patching bytes ≥0x10 keeps a slot valid
as long as the checksum is left alone.

## 6. Tables

### 6.1 Key masks

| Bit | Key | Bit | Key |
|---:|---|---:|---|
| 0x0001 | A | 0x0020 | Left |
| 0x0002 | B | 0x0040 | Up |
| 0x0004 | Select | 0x0080 | Down |
| 0x0008 | Start | 0x0100 | R |
| 0x0010 | Right | 0x0200 | L |

### 6.2 Menu inventory (observed)

| Screen | Items |
|---|---|
| Title | 1 prompt (`PRESS START`) |
| Load Game | 2 slots |
| Profile/slot menu | 5 (Start Game/Continue, Erase Game, Extras, Options, Credits) |
| Mode select | 4 (Story Mode, Multiplayer, Global Justice, Minigames) |
| Options | 3 (Language, Sound, Music) |
| Erase Game | 2 slots × (Clear Data? Yes/No) |
| Multiplayer | link wait (`Waiting for connection`) |
| Credits | roll |
| Pause | 4 (Map, Continue, Options, Quit) |

### 6.3 Developer boot directory, 0x0818B040 (20 records, 0x1C stride)

| # | Address | Label | id | flags |
|---:|---|---|---:|---:|
| 0 | 0x0818B040 | *(text id 0x2001)* | 0x00060107 | 0 |
| 1 | 0x0818B05C | Obj Viewer | 0x00070107 | 0 |
| 2 | 0x0818B078 | Music Player | 0x00080107 | 0 |
| 3 | 0x0818B094 | Fx Player | 0x00060600 | 0 |
| 4 | 0x0818B0B0 | Room 01 | 0x00060700 | 0 |
| 5 | 0x0818B0CC | Room 02 | 0x00060800 | 0 |
| 6 | 0x0818B0E8 | Room 03 | 0x00060900 | 0 |
| 7 | 0x0818B104 | Room 04 | 0x00060A00 | 0 |
| 8 | 0x0818B120 | Room 05 | 0x00060B00 | 0 |
| 9 | 0x0818B13C | Room 06 | 0x00060C00 | 0 |
| 10 | 0x0818B158 | Room 07 | 0x00060D00 | 0 |
| 11 | 0x0818B174 | Room 08 | 0x00069201 | 0 |
| 12 | 0x0818B190 | Normal Boot | 0x00060000 | 0x80000000 |
| 13 | 0x0818B1AC | Episode 1 | 0x00060000 | 0x80020000 |
| 14 | 0x0818B1C8 | Episode 2 | 0x00060000 | 0x80030000 |
| 15 | 0x0818B1E4 | Episode 3 | 0x00060000 | 0x80010000 |
| 16 | 0x0818B200 | Global Justice | 0x00069804 | 0 |
| 17 | 0x0818B21C | Tangram | 0x00069904 | 0 |
| 18 | 0x0818B238 | MasterKim | 0x00069A04 | 0 |
| 19 | 0x0818B254 | Rufus Game | 0x00000000 | 0 |

The third word of each record is a Thumb-tagged pointer (`…B274/B275/B277`) into the
rectangle/icon list at 0x0818B274; the ids are the engine's boot/room ids. Index 0 has no
name pointer, only id 0x2001 (a text id), so it is probably the menu title.

### 6.4 Scene records (185; all `+0x14 == 0`)

`Title_Screen`, `MainMenu`, `SaveMenu`, `PauseMenu`, `Load01..04`, `MiniGame01..03`,
`WorldMap01..03`, `cards01..10`, `cutscene01..05`, `Legal`/`legal02`, `TutorialBG`,
`WallBG`, `SpaceBG`, `BeachBG`, `BeachHighBG`, `JungleBG`, `templeBG`, `AssetViewer`,
`EP00_GJ_HQ`, `EP00_GJ_elevator`, `EP01_CA_room*` (41), `EP02_SSS_room*` (32),
`EP03_blank_space`, `Race00_*` (10), `Race01_*` (15), `Race02_*` (20), `Race03_*` (20),
`Race_*` (5). Every record has the shape `{char name[16]; u32 0; u16 flags; u16 0xFFFF/…}`
and **all 185 have flags = 0x0000** (checked by scanning 4-aligned name records).

### 6.5 Published codes for this SKU (GameHacking.org / Almar; CodeBreaker, not in-game)

Master: `97C2CC187F35` + `BE602C6068C2` + `776B175E63A2`.

`5F9448ECACDB` Kim all tools · `DF1478ECAC9A` Kim infinite health ·
`5F9468ECACDB` Kim max health · `5F9648F9BCDB` Ron all tools ·
`DF1678F9BC9A` Ron infinite health · `5F9668F9BCDB` Ron max health ·
`22C7AD1B9F65` unlock sounds/music · `A241BF0E0324` unlock all minigames ·
`718BAB790B6E`+`14945D40AEAB`+`982E70F9FC92` unlock all episodes ·
`F755BD4C8E2E`+`24DBAE9B0A44`+`24D9AE8E1A44`+`A241BF0E0324` unlock all photos.

None is a typeable code; all are host-side memory writes in the CodeBreaker device
format. The plaintext master-code fragments (`97C2CC18`, `7F35`, `BE602C60`, `68C2`,
`776B175E`, `63A2`) occur **0** times in the image, as expected.

## 6b. Enumeration

**Space definitions.**

* *Typed-code space:* **0 representable accepted codes.** No screen offers text entry
  (§3.1), no alphabet constant or length rule exists, and no comparison against a user
  buffer exists. The searched text space is 2,102 `FF FE` strings plus a linear decode of
  all 8,388,608 bytes (8,266,644 decoded characters).
* *Button-code space:* **4 documented keys, 1 multi-key branch, 1 action.** The whole key
  surface is the struct at 0x0200C100; only one site in the image tests a multi-key
  combination — `held & 0x000F == 0x000F` at 0x080132AC. Its only action is the SDK soft
  reset. No site stores a press history, compares an ordered sequence, or dispatches on a
  prefix.
* *Unlock space (the system that does exist):* save-gated, 512-byte EEPROM, 2 slots of
  0xE8; the gate is observable (dim + cursor skip) but its exact bit was not isolated
  (§8).

**Novel values (not in any published list).**

1. **A+B+Select+Start soft reset** — implemented at 0x080132AC, observed on the title
   screen and in a cut-scene, with two rejected variants. No FAQ/cheat page for this SKU
   lists it (all published entries are CodeBreaker host codes).
2. **The 20-entry developer boot directory** (§6.3) — its entry names, ids and gating
   rule are published here for the first time for this SKU; it is proven unreachable in
   the retail image rather than presented as a cheat.

**Bounds proven by rejection / exhaustive search.**

| Space searched | Method | Result |
|---|---|---|
| Message bank | 2,102 `FF FE` records, decoded in both charsets | `PASSWORD` 0, `PASSCODE` 0, `CHEAT` 0, `UNLOCK` 0, `DEBUG` 0, `ENTER CODE` 0, `ENTER YOUR` 0, `LEVEL SELECT` 0, `SOUND TEST` 0; `SECRET` 2 (story dialogue), `CODE(S)` only story dialogue, `BONUS` 3 (French/dialogue) |
| Whole image | linear decode of 8,266,644 chars (both encodings) | same counts; `EXTRAS` 1, `MINIGAME` 7, `MUSIC` 13, `PHOTO` 21, `ALBUM` 42 |
| Button-mask tables | ≥5 consecutive u16 single-bit masks from `{1,2,4,8,0x10,0x20,0x40,0x80,0x100,0x200}` | 75 runs; **0** are referenced by a code/data pointer; inspected runs are graphics/tilemap data (`0x581BC8`, `0x185122`) |
| Multi-key comparisons | capstone scan for `ands #0xF; cmp #0xF` | 1 real handler (0x080132AC); the other two candidates read a menu object, not the key struct |
| Developer directory | `0x0818B040` / `0x0818B03C` as u32 across the image | 1 reference each (both in the same literal pool, 0x0803C0F4/0x0803C104) |
| Scene gate | 185 scene records, 4-aligned, name+`00 00 00 00`+`u16 flags` | 185/185 flags = 0 ⇒ the two menu objects are never created |
| Title-input space | Konami, LRLR, Select×3, UDUD, A+B+Select, A+B+Start | no state change; only the full four-key combo resets |
| Published codes | CRC32 match to AGB-BQPE-USA; literal search | release matches; 0 in-ROM literals; 12/12 entries are CodeBreaker host codes, none typeable |

**Reachable-screen enumeration** (all 9 rows of §3.1 observed): title, Load Game, profile
menu, mode select, Options, Erase Game, Credits, Multiplayer wait, pause. No tenth screen
could be produced by input; the two dim entries are skipped by the cursor, and the profile
menu/mode select do not scroll.

## 7. Validation evidence

### Observed (emulator screenshots, RAM reads)

* Full screen walk per §3.1 on `:326`, every transition captured.
* `Extras`, `Global Justice` and `Minigames` rendered dim on a `World 1 / 00% / 00:00`
  save; Down from `Multiplayer` wraps to `Story Mode`, skipping both dim rows.
* A+B+Select+Start → fade → `©2005 Disney` splash, twice (title and cut-scene).
* A+B+Select and A+B+Start do not reset.
* Input struct read from a savestate: `0x0200C100 = 10 00 10 00 …` with Right held
  (prev = held = 0x0010); keymap confirmed.
* Load Game shows two slots; slot 1 with data displays `World 1 / 00% / 00:00`.

### Derived (instruction sequence)

* Key-state derivation and the single `0x04000130` poll (0x08004010 → 0x08003ED0).
* Soft-reset mask, edge guard and SDK call (0x080132AC → 0x080492DC).
* Developer-directory record layout (0x1C stride), label/icon/id fields, and the single
  consumer with its two gates (0x0803BFFC–0x0803C042).
* Save record layout, magic and checksum (0x08042BA0 / 0x08042C5C), and the `.sav`
  per-8-byte-block reversal.
* Message encoding (first-letter glyph + `FF FC`/`FF FE` controls), confirmed by decoding
  several thousand strings coherently.

### Inferred

* The 20-entry directory is an A2M developer boot/episode-select menu (label set, episode
  flags 0x8000_00xx, minigame ids) whose renderer is the scene-init path that is gated
  off; the retail build never shows it.
* The `Room 01..08` ids probably map to EP01/EP02 room groups, but the mapping was not
  exercised.

### Negative evidence with counts

* `strings -t x -n 5` → 82,319 lines; `password|cheat|debug|secret|unlock|level select|
  sound test|gallery` inside the decoded text → only story/credit words (see §6b table).
* 2,102 message records; 0 code-entry strings.
* 185 scene records; 0 with the debug-menu flag.
* 75 button-mask runs; 0 referenced by code.
* 12 published codes; 0 in-ROM literals; 0 typeable.

## 8. Unknowns

* The exact save bit/field that enables `Extras`, `Global Justice` and `Minigames` was not
  isolated. The gate is observed (dim + cursor-skipped on a fresh save) and the published
  achievement text says the sound test unlocks on finishing the game; the 0xE8-byte
  payload is otherwise opaque and edits to it invalidate the slot.
* The content behind the unlocked Extras screen (Photo Album page count, sound-test track
  count, whether Global Justice is a level or a mode) was not observed; only the ROM
  strings and the published unlock list name it.
* The published CodeBreaker codes are encrypted device codes; a GBATEK-based decryptor
  produced an inconsistent address map, so their exact RAM targets were not verified.
  They are host-side memory writes and outside the in-game scope.
* The 20-entry directory's index-0 text id 0x2001 and the companion `0x0818B03C` table's
  ten entries were not resolved to visible text (no renderer is reachable).

## 9. Tooling

* `mgba -3` + `Xvfb :326` + `openbox`; `xdotool` (XTEST to the focused window),
  `import -window root` + ImageMagick `convert` for 720×480 crops.
* mGBA savestates parsed/patched in Python (PNG `gbAs` → zlib → 397,312-byte state;
  IWRAM 0x19000, EWRAM 0x21000) — `state.py`, `patchstate.py`.
* `arm-none-eabi-objdump -M force-thumb` and Python + `capstone` for literal-pool, BL and
  mask-run scans; `cbdec*.py` for the CodeBreaker experiment (inconclusive).
* `textdec*.py` / linear decoder for the two-charset message bank; `keys.py` input helper;
  `patchsav.py` for EEPROM exploration. Work directory `/tmp/kp3` (transient).

## 10. Legal note

No ROM, graphics, audio or extracted game text is redistributed here. Only hashes,
addresses, record formats and reimplemented algorithms are published.
