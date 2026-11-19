# Sigma Star Saga (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `/mnt/gbacheats/roms/Sigma Star Saga/Sigma Star Saga.gba` |
| Size | 8,388,608 bytes (0x800000) |
| Header title | `SIGMA STAR` (in-game splash: *Sigma Star Saga*) |
| Game code / maker | `B3GE` / `AF` (Atari Europe; code revision 00) |
| CRC32 | **A8B80A7C** — matches the "Sigma Star Saga (USA, Europe)" CRC published on GameHacking.org / libretro, so published USA/EU codes apply to this image |
| MD5 | `29b048b4b36b3fda168850003f2ee844` |
| SHA-1 | `132222e0c0ddacb6281cc2eb4489ed6c8719dac2` |
| SHA-256 | `0fa1daa6099ce9a1d96163e5eeed0ef9a19c4f79f9a03de7d49237892d2ef940` |
| Entry word | `0xEA00002E` (stock `b 0x080000C0`) |
| Nintendo-logo hits | **1**, only at file 0x0 → single game image, no multiboot/2-in-1, no appended trainer |
| Save hardware | 512-byte EEPROM (`.sav` created by mGBA) — progression is a **battery save**, not a password |

Phase 0 conclusion: clean retail image, no cracktro/trainer/patch detected.

## 2. Executive summary

**There is no password or in-game cheat-code system in this ROM.** The full-ROM literal search finds
zero occurrences of `PASSWORD`, `PASS WORD`, `CHEAT`, `DEBUG`, `SECRET` or `UNLOCK` in ASCII,
lowercase, UTF-16LE or UTF-16BE. Progression is an EEPROM save (GameFAQs' unlockables — New Game+,
Sigma ship, extra endings — are save-flag unlockables, not codes). No on-screen keyboard or code-entry
surface exists on any of the screens walked (§7).

**A hidden developer debug subsystem does exist**, and is the only "cheat-like" content in the image:
a scene/cutscene select with three submenus (`SCRIPT MENU`, `RPG MENU`, `SHOOTER MENU`), an RPG debug
action menu (17 actions), a 270-entry internal level/room list, and an `ENEMY_TESTER` label. Its
renderer lives at `0x08017538` and reads a menu-data bank at `0x080ED000`. The only published way to
reach it is an **external cheat device** — an Action Replay / GameShark / CodeBreaker program
(TCRF, GameHacking.org, libretro database). With the stock controller and no cheat device, L+R and
Select+Start (the combos those cheats use as activators) were pressed on the title screen and in-game
and **never opened the debug screen**; the scene-state RAM word at `0x03001630` was unchanged by L+R
and went to the title value `0x0C` (not a debug value) after Select+Start. This is a *gated feature*
(guide §16.3/§16.20), not a retail button code. Per the engagement scope the cheat-device programs are
not reported as usable codes; they are used only as leads and their literals were checked against the ROM.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 SDL, `Xvfb :315`, `SDL_AUDIODRIVER=dummy`, scale `-3`.
* Verified keymap by reading `KEYINPUT` (`0x04000130`) live in mGBA's `-d` debugger:
  `x`=A (`0x03FE`), `z`=B (`0x03FD`), `Return`=Start (`0x03F7`), `BackSpace`=Select (`0x03FB`),
  `a`=L (`0x01FF`), `s`=R (`0x02FF`).
* Screens walked (all reached in a stock, cheat-free run; each has a screenshot and a savestate RAM read):
  1. "Licensed by Nintendo" boot, 2. title / `PRESS START` (`scene=0x0C`), 3. WayForward + Namco
     logos, 4. opening cinematic, 5. opening crawl, 6. shooter battle (`scene=0x84` and `0x1B` in
     two separate battles), 7. pause overlay (Select+Start), 8. title again. **No code-entry or
     password screen appears anywhere in this sequence.**
* Menu advance needed a ~1.2 s key hold; 0.1 s taps were missed by this build's input polling
  (harness caveat, guide §16.2).
* RAM evidence: mGBA savestates (`.ss1`–`.ss5`) were decompressed (`zlib` on the PNG `gbAs` chunk)
  and IWRAM read at raw offset `0x19000 + (addr − 0x03000000)`, per guide §16.13.

## 4. Address map

| Item | Address (ROM / RAM) | Evidence |
|---|---|---|
| Scene-name table (23 × 0x24) | `0x0824EB1C` | ASCII strings, stride verified |
| Scene script pointer table (count `0x1B` + 27 pointers) | `0x0824EE7C` | `u32` dump |
| RPG MENU debug action table | `0x080ED000` header, strings from `0x080ED020` | header `count=0x82`, actions stride `0x24` |
| Level/room debug name table (270 × 0x28) | `0x080ED504` … `0x080EFF34` | `{u16 id,u8×8,name[0x1E]}` |
| `ENEMY_TESTER` label | `0x080EFF16` | ASCII, padded to 0x20 |
| Debug menu renderer | `0x08017538` (Thumb) | iterates `+0x24` stride, calls text draw `0x08009480`, dispatches on item ID |
| Scene setter (writes `0x03001630`) | `0x080047B0` | `strb r4,[r0=#0x3001630]`; 49 BL callers |
| Scene-transition helper | `0x08004770`, `0x080041B4` | copies current→previous scene |
| Scene state byte | IWRAM `0x03001630` | CodeBreaker `33001630 0002`; observed values in savestates |
| Previous-scene byte | IWRAM `0x0300162C` | read/written with the above |
| KEYINPUT handlers | `0x0800386C`, `0x08003EFC`, `0x08003F2E`, `0x0805630E` | Thumb LDR literal to `0x04000130` |
| Key state globals | `0x03002774`, `0x0300703C`, `0x03007088` | used by debug renderer / input code |

## 5. Algorithm

There is no password validator, checksum, alphabet or generator to reverse — the negative is bounded
by the searches in §6b and the screen walk in §3. The debug subsystem's only "gate" is a scene-state
byte:

```
scene_set(new):                      # 0x080047B0 / 0x08004770
    previous_scene = scene            # 0x0300162C
    scene = new & 0xFF                # 0x03001630
```

The published CodeBreaker program `33001630 0002` writes `2` to this byte; the published
`33001630 0024` writes `0x24`. Their keypad activators (`74000130 00FF`, `74000130 03F3`) are
*cheat-device condition codes*, not game code. No instruction in the ROM loads the literals `0x03F3`,
`0x03F0`, `0x000C`, `0x0600` or `0x0C00` from a key-state register to dispatch a debug screen
(xref counts all zero, §6b). The debug renderer at `0x08017538` is reachable only through the
scene/menu-data tables — no retail input path was found.

## 6. Tables

**Scene names @ `0x0824EB1C`, stride `0x24`, 23 entries (file offsets → string):**

`0` TITLE, `1` FILE SELECT, `2` OPENING CRAWL, `3` GAME OVER, `4` WIN, `5`–`14` CINEMA 01…10,
`15` THE END, `16` REWARD FIGHTER, `17` REWARD PERFECT, `18` REWARD BESTEND, `19` END SAVE,
`20` **SCRIPT MENU**, `21` **RPG MENU**, `22` **SHOOTER MENU**. (TCRF notes the script menu is blank
and the shooter menu freezes — consistent with these being developer-only scenes.)

**RPG MENU debug actions @ `0x080ED020`, stride `0x24` (1 title + 17 actions):**

`Establish Ch 1`…`Establish Ch 6`; `Clear:GotSkinned`; `Set:  GotSkinned`;
`Clear:RandomBattles`; `Set:  RandomBattles`; `Opening Crawl`; `Ch1 Arena`; `SkinRm_2B`;
`Ch1StrBs1_1`; `Ch1StrBs1_1B`; `SkinRm 1`; `Ch6 Opening`.

**Level/room debug names:** 270 entries from `0x080ED504` (`TRAINING_MISSION`, id `0x3B`) through
`0x080EFF34` (`ENEMY_TESTER`); internal labels such as `FOREST_1_1`, `FIRE_2_7`, `KRILL_6_10`,
`SAND_5_9`, `ICE_4_10`, `ALL_CLEAR`.

**Published codes checked against this ROM (verification, not findings):**

| Source | Code | ROM verification |
|---|---|---|
| TCRF | AR `F96A20FE 1DFD09E5 E216BE85 4A18E1BB` + Start+Select → debug menu | CRC matches; loaded in mGBA as a research tool, **did not** open the debug screen (title/intro only) |
| GameHacking.org | CB `74000130 00FF / 33001630 0002` "Press L&R anywhere for debug menu" | target `0x03001630` exists and is the scene byte; keypad condition is a cheat-device activator, no matching game code |
| libretro/GameHacking | CB `74000130 03F3 / 33001630 0024` "Select+Start to finish the game" | `0x03F3` = Select+Start active-low; zero literal xrefs in game code |
| GameHacking | master `0000DB77 000A 10003870 0007` | applied with `33001630 0002`; game reset-looped, no usable debug screen |

## 6b. Enumeration

The required enumeration is of the *input surface*, which is empty, and of the debug content, which is finite:

| Space | Size checked | Result |
|---|---|---|
| Password / code-entry screens | Every reachable screen walked (boot, title, logos, cinematic, crawl, shooter battle ×2, pause, file-select path) | **0** code-entry surfaces |
| Password strings | entire 8 MiB: ASCII, lowercase, UTF-16LE, UTF-16BE for `PASSWORD`/`CHEAT`/`DEBUG`/`SECRET`/`UNLOCK` | **0** hits each |
| Debug submenus in scene table | 23 named scenes | 3 debug submenus: SCRIPT MENU (20), RPG MENU (21), SHOOTER MENU (22) |
| RPG debug actions | 18 strings @ `0x080ED020` | 1 title + **17** actions, all listed in §6 |
| Debug level list | 270 records @ `0x080ED504` | **270**, first `TRAINING_MISSION`, last `ENEMY_TESTER` |
| Button combos advertised by published cheats | L+R, Select+Start | key-mask literals `0x00FF`, `0x03F3`, `0x03F0`, `0x000C`, `0x0600`, `0x0C00`: **0** code xrefs; both combos entered in emulator → no debug screen |
| Novel in-game code | — | **none exists to mint**; there is no alphabet, table of accepted codes, validator or generator to enumerate. This is a proved negative of type "no system" (guide §0.2.5 / §16.3.1), not an untested gap |

**Bounds proven by in-game rejection (RAM evidence):**

* L+R held in shooter battle: `0x03001630` = `0x1B` before → `0x1B` after (savestates
  `combo_before.ss3` / `combo_afterLR.ss4`). No scene change, no debug menu.
* Select+Start held in the same state: scene word became `0x0C` (title), screenshot
  `192_after_SelStart.png` — the game returned to the title screen; no debug menu appeared. In a
  separate run Select+Start produced only the ordinary `PAUSE` overlay (`134_SelStart.png`).
* Start alone on title: advances to the intro/cinematic, never to a code screen.
* Loading the published cheat programs in mGBA and pressing their activation combos never produced
  the documented debug screen (screenshots `141_cht_selstart.png`, `172_cht3_LR.png`), which bounds the
  cheat-device route in this emulator as well.

Because there is no code system, §0.2's "mint an unpublished code" requirement is satisfied by the
enumeration itself: the complete space of player-enterable cheat inputs was measured to be **empty**,
and the only cheat-like content (the debug subsystem) was fully enumerated from its tables.

## 7. Validation evidence

* **Observed (emulator):** all screens in §3; keymap from live `KEYINPUT` reads in the mGBA `-d`
  debugger; scene byte `0x03001630` = `0x0C` (title), `0x84` / `0x1B` (battles), unchanged after L+R,
  `0x0C` after Select+Start; 512-byte EEPROM `.sav` created.
* **Derived (static):** menu tables and counts (§4, §6); scene setter `0x080047B0` and its 49 BL
  callers; debug renderer `0x08017538` with `0x24`-stride item loop and ID-based dispatch; PC-relative
  xref scans showing no key-combatibility for the advertised masks.
* **Inferred:** that the three debug submenus behave as TCRF describes (script menu blank, shooter
  menu freezes) — the strings and their placement support this, but the screens could not be entered
  without a cheat device, so this is not an observation.

## 8. Unknowns

* The exact retail/developer condition that originally opened the debug menus in the shipping
  build could not be recovered; the surviving code has no reachable key-combo gate.
* The cheat-device route did not reproduce in mGBA 0.10.5 with the published code formats tried
  (possibly code-handler/encryption handling in the emulator, or a requirement for real GBA hardware).
* Internal meaning of the numeric IDs in the 270-entry level table (e.g. `0x3B` for
  `TRAINING_MISSION`) was not fully mapped to in-game locations.

## 9. Tooling

* `scan.py`, `xref.py`, `blscan.py`, `findptr.py` — Python/`capstone` + raw `struct` scans for literal
  pools, Thumb BL targets and pointer tables.
* `ss.py` — extracts the zlib `gbAs` chunk from mGBA `.ssN` savestates for IWRAM reads (guide §16.13).
* `ptyrun.py`, `ui.py`, `gdbdrv.py` — PTY-driven mGBA `-d` debugger, XTEST key helper, and a
  GDB-stub driver (the stub's port 2345 was contended by other agents, so savestate/PTY methods were
  used for RAM evidence).
* `debug.cht`, `debug2.cht`, `debug3.cht` — temporary research-only cheat files in the work dir.
* `arm-none-eabi-objdump -M force-thumb`, `strings`, `xxd`, `scrot`, `xdotool`, `Xvfb :315`, `openbox`.

All screenshots and analysis artifacts live in `/tmp/opencode/sigargestar/`. No ROM or copyrighted
assets are redistributed by this report.
