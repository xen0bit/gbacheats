# FIFA Football 2005 (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `FIFA Football 2005.gba` (8,388,608 bytes = 0x800000, 8 MiB) |
| Header title | `FIFA 2005` (offset 0xA0) |
| Game code | `BF5E`; maker `69` (Electronic Arts) |
| Version / complement / checksum | `0x00` / `0xE3` / `0x0000` |
| Entry branch | `0xEA00002E` → `0x080000C0` (stock crt0, **not** a patched/cracktro entry) |
| Embedded GBA headers | **1** (single retail image at 0x0; no multiboot/2-in-1/appended trainer) |
| MD5 | `4c5c302d02ecfcd274dae63461a1692b` |
| SHA-1 | `5f1b0aacc5afaa9dd275b2df780c8a588719afa8` |
| SHA-256 | `affcf268f0c3dd0b4fb021e2a30a01b6cee73dac333a2f263ff2d18b58baf466` |

Save device: 512-byte EEPROM (`game.sav` begins `10 00 00 22 78 EB C2 90 FF FF …`).

## 2. Executive summary

**No developer-intended cheat system exists in this image.** There is no password-entry
screen, no cheat-code validator, no button-code matcher, and no hidden debug menu. The
only unlockable content is **save-progression based**: a *Challenges* mode whose Historic
challenges unlock as earlier ones are completed and whose *Custom Challenge* is gated
until every challenge is complete. These are EEPROM save bits, not player-enterable codes.

**One dead developer leftover exists but is unreachable:** the literal `FIFA 05. Test Mode`
at 0x08221574 is loaded by the screen-initializer function at **0x08012B54** (LDR at
0x08012BD6, passed to 0x08012C0), but that function has **zero** BL, B, BLX and pointer
references anywhere in the 8 MiB. The same applies to the localized `Test Hooks` label
at 0x087E5AA1, which sits beside the pause-menu strings (`Quit Match`, `Restart
Challenge`) but is not among the six entries drawn on the observed pause menu. Per
§16.3 these are *dead code / cut feature*, not a reachable debug menu.

The ROM does contain the strings `Getting password`, `Your Password is:`,
`Retrieve Password`, `Change Password`, `New Password`, `Old Password`, `Password`,
`Checking IMEI`, `Invalid Billing DLL`, `Do you wish to enable Bluetooth?`,
`Username already exists`, `Protocol too old/new`, `Upload Score`, `High Scores`,
`Create New User`, `USERNAME`, `Login` (0x87C4D00–0x87C5400). This is a **cut/carried-over
N-Gage/Symbian online-billing module**: IMEI, billing DLL and Bluetooth are N-Gage
concepts with no GBA UI or hardware. No screen in the game reaches it, its five
non-English localization slots all fall back to the English string, and no published
GBA code uses it. Per guide §16.3 this is a *cut feature*, not a reachable code surface.

Every visible UI string was found as plain NUL-terminated ASCII in the ROM
(e.g. `Select Challenge Type` @ 0x87CAF88, `Comeback Challenges` @ 0x87CAD70,
`Rout Challenges` @ 0x87CAD0C, `Custom Challenges` @ 0x87CACA4, `Pause Menu` @
0x87E673C, `Connect all Players` @ 0x87E77DC). Therefore the §11/§16 "font/tile-indexed
text bank" trap does **not** apply here, and a negative string result is meaningful.

Cross-sibling check (this image verified independently): FIFA 2005, FIFA 06 and FIFA 07
GBA all contain the same N-Gage-derived online-billing strings and the same challenge
unlock strings (`Complete all Challenges to unlock Custom Challenge.`,
`You have unlocked the Custom Challenge!`, `You have unlocked an Historic %s Challenge!`).
FIFA Football 2004 contains **none** of them. So the shared engine/asset lineage is with
FIFA 06/07, not FIFA 04; no code system is inherited from either.

## 3. How to reproduce

* Emulator: `mgba -3` (SDL build), under `Xvfb :318 -screen 0 1024x768x24`,
  `SDL_AUDIODRIVER=dummy`. Own display only; no other displays touched.
* mGBA keymap used: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`,
  D-pad = arrow keys. Holds of 100–150 ms; savestates (`Shift+F1..F4`) used for every
  repeat experiment.
* Boot path: language flag screen (default = Italian index) → EA/FIFA license screen →
  league-logo splash → **main menu**. Main menu (English):
  `Friendly | Challenges | Career | Competition | Multiplayer | Options`.
* Menu path to the only unlockables: `Challenges → Select Challenge Type →
  Comeback / Rout / Custom Challenges → Select Challenge` (10-entry lists).
* Pause path: start `Friendly` → choose teams → `Today's Friendly → Start Match` →
  two "Game Controls" pages → in match → **Start** opens `Pause Menu`
  (`Resume Match | Team Management | Instant Replay | Match Statistics | Options | Quit Match`).
  Select opens a replay, not the pause menu.
* Codes tested: **none exist to test.** Console-store "points" unlocks advertised on
  SuperCheats (Play Online, Football Fusion, Austrian OFB Cup, …) are from the
  PS2/Xbox/PC SKUs and are absent from this ROM. No GBA password or button code is
  published on the 8 sources consulted (§6b).

## 4. Address map

All addresses are ROM addresses (`file offset + 0x08000000`); verified with
`struct.unpack_from` and raw byte dumps, not with Ghidra auto-analysis (see §9).

| Region | Address | Role |
|---|---|---|
| GBA header | 0x08000000–0x080000BF | title BF5E/69, stock entry |
| crt0 / ARM boot | 0x080000C0 | `mov r0,#0x12 …` (valid stock ARM code) |
| Localization table | **0x087C0000** | 6 × 32-bit language pointers per string ID (stride 0x18) |
| Online/billing (cut) strings | 0x087C4D00–0x087C5400 | password/IMEI/Bluetooth/billing/score-upload |
| Challenge strings | 0x087CB000–0x087CC100 | Locked/Unlocked/Reset/Challenge results |
| UI strings | 0x087DF000–0x087F0000 | options, pause menu, multiplayer, etc. |
| "Pause Menu" | 0x087E673C | EN string in localization table |
| "Connect all Players" | 0x087E77DC | EN string |
| Dead Test Mode title | 0x08221574 | `FIFA 05. Test Mode` literal (unreachable) |
| Dead Test Mode initializer | 0x08012B54 | zero callers/xrefs in the whole 8 MiB |
| Unused pause label | 0x087E5AA1 | `Test Hooks` — not on the drawn 6-entry pause menu |
| Save | EEPROM 0x0E000000 | 512 bytes, host file `game.sav` |

Savestate RAM evidence (mGBA `.ssN` PNG → zlib `gbAs` chunk, 397,312 bytes;
IWRAM at state offset `0x19000`, EWRAM at `0x21000`):

| Savestate | Screen | IWRAM SHA-256 (first 16) | EWRAM SHA-256 (first 16) |
|---|---|---|---|
| `game.ss1` | Main menu (German) | `9271804b83aea37e` | `f25f55f7cddc84c2` |
| `game.ss2` | Select Challenge Type | `caea8d1d63ac3ae1` | `c93e314c896a2898` |
| `game.ss3` | Pause Menu (in match) | `c30cb98df6f3bc97` | `468951c61f95d519` |

The three screens are provably distinct RAM states, not the same frame redrawn.

## 5. Algorithm

**Not applicable — there is no validator to reverse.** No code/password entry surface
exists, so there is no input alphabet, checksum, key table, or accept/reject routine.
The only state machine found is ordinary menu navigation and the Challenge progression
gates (EEPROM bits tested when the `Locked`/`Unlocked` labels are drawn). No
`strlen`/`strcmp` validator, no password keypad, and no button-sequence matcher were
identified; see §6b for the searched spaces and counts.

## 6. Tables

### 6.1 Keyword evidence (literal and encoded search over all 8 MiB)

Counts from `scan.py` (encodings tried: ASCII, upper, lower, UTF-16LE, UTF-16BE,
`+0x20`, `-0x20`):

| Keyword | ASCII hits | Notes |
|---|---:|---|
| `password` | 4 | all inside the cut billing module (0x87C4F85, 0x87C4FA0, 0x87C5086, 0x87C509D) |
| `unlock` | 3 | Challenge unlock strings only (0x87CB4C3, 0x87CB5D9, 0x87CB6E1) |
| `valid` | 2 | `Invalid Billing DLL` only |
| `master` (upper) | 1 | credit `EAC MASTERING` |
| `test` | 7 | credit `Testing Team`, `put yourself to the test`, etc. |
| `demo` | 1 | player surname substring |
| `boot`, `code`, `cheat`, `debug`, `secret`, `classic`, `legend`, `stadium`, `hidden` | 0 / noise | `code -0x20` 2 hits are bytes inside compressed data; `boot` 1 hit is surname `Booty` |

No encoding produced a "password screen", "enter code", "cheat menu", or "debug menu" UI string.

### 6.2 Screens walked (all with screenshots retained in `/tmp/fifa05/`)

1. Language flag select (6 flags: DE/EN/IT/FR/NL/ES)
2. FIFA license / legal splash
3. League-logo splash
4. Main menu (6 items)
5. Options (7 items): Game, Display, Sound, Control, Favourite Team, Language, Credits
6. Game Options (CPU Skill, GK Skill, Half Length, Extra Time, Pitch Type, Wind, Auto Replay)
7. Display Options (Radar, Score Display, Player Names, Brightness, Camera, Replay Camera View)
8. Sound Options (Sound FX, Music)
9. Control Options
10. Favourite Team (league/team picker)
11. Language list / Credits
12. Challenges → Select Challenge Type (Comeback, Rout, Custom=Locked, 0/10 Complete)
13. Comeback Challenges list (10 entries; last = Locked)
14. Rout Challenges list (9+ entries)
15. Friendly → Choose Your Team (your team + CPU team)
16. Today's Friendly (Start Match, Team Management, Change Kits, Game Options)
17. Team Management (Starting 11, Tactics, Key Players)
18. Game Controls, pages 1 (Attacking) and 2 (Defending)
19. In-match play
20. Pause Menu (6 items) + in-match Options (4 items: Game/Display/Sound/Control)
21. Competition → Season / Cup
22. Multiplayer Mode → Connect all Players

No cheat, password, code, unlock-code, or debug entry appears on any of these screens.

### 6.3 Unlockables actually present

| Item | Gate (observed) | Type |
|---|---|---|
| Comeback Challenges (10) | progressively playable; 10th shown `Locked` initially | EEPROM save progression |
| Rout Challenges (10) | same | EEPROM save progression |
| Historic challenge unlock | message `You have unlocked an Historic %s Challenge!` | save bit set on completion |
| Custom Challenge | `Locked`; requires all challenges complete | save bit set on completing all |

No classic teams, stadiums, boots, or unlockable kits were present in any menu or string
bank. (`Reset Challenge Data?` exists as string 0x87CBE4C; L/R/Select/Start on the
Challenge Type screen do not open it — probed, no screen change.) The dead `FIFA 05. Test
Mode` initializer at 0x08012B54 and the unused `Test Hooks` string at 0x087E5AA1 are
listed here for completeness; neither is reachable and neither changes any observable
state.

## 6b. Enumeration

**Code-space definition:** empty. There is no alphabet, length, checksum, table or
validator to enumerate, so §0.2's "mint a novel code" deliverable cannot be produced.
Per §0.2 item 5, the negative result is bounded as follows:

1. **Menu/screen space** — 22 distinct screen states enumerated above, each observed in
   mGBA with a screenshot; three confirmed as distinct RAM states by savestate hashes.
   Every menu leaf was entered; no attract/demo screen was mistaken for a menu.
2. **Text space** — 25 keywords × 7 encodings searched over all 0x800000 bytes; exact hit
   counts in §6.1. Every visible UI string was confirmed to be plain ASCII, so an
   encoded/tile-indexed hidden label was not merely assumed absent. The only "password"
   cluster is the cut N-Gage billing module.
3. **Button-code space** — `buttonscan.py`: 6 common u16 mask sequences (Konami
   `UUDDLRLRBA`, `L+R+Start`, `L+R+Select`, `A+B+Start+Select`, `L+R+A`, `L+R+B`,
   `L+R+Up+Down`) searched in both active-high and active-low form over the first
   0x300000 bytes: **0 hits** for all but two isolated, unaligned 3-press coincidences
   (0x80BEEE5, 0x80C40EC, 0x80CA81C — in data, not code). A generic scan for ≥4
   consecutive plausible key-mask halfwords found 735 runs; inspection shows they are
   the controller-label/string tables around 0x08063xxx and 0x0805Dxxx, not cheat tables.
   Dynamic: 12 combos on the pause menu + 12 on the main menu (each from a fresh savestate)
   + 4 held combos at boot = **28 tested**; none produced a new screen. Full list in
   `/tmp/fifa05/combos.py`.
4. **Published-code space** — 8 sources consulted: GameFAQs GBA cheats (403), archived
   GameFAQs (404), SuperCheats, ChapterCheats, Neoseeker (403), Cheatbook, VGChartz,
   CheatCodes.com (transport error). Every reachable page lists only gameplay hints
   ("Guaranteed Goal", "Super curve ball", "Season objectives") or console-store "points"
   unlocks. **Zero GBA passwords, button codes or unlock codes were found**, so there is
   no published literal to verify or reject. Console-store labels were checked against
   the ROM: `Play Online`, `Football Fusion` → not present.
5. **Novel code** — impossible by construction; correctly reported as absent rather than
   fabricated.
6. **Bounds by rejection** — a code system would have an entry screen; no such screen
   exists, and 28 button probes plus the full menu walk produced no rejection or
   acceptance event to bound. For the real unlockables, the bound is the observed
   `Locked`→`Unlocked` gate on Custom Challenge (§6.3).

## 7. Validation evidence

* **Observed** — all 22 screens in emulator; Custom Challenge `Locked`, Comeback 10th
  challenge `Locked`, `0/10 Complete`; Start=Pause, Select=Replay; 28 button probes with
  no hidden screen; savestate hashes; EEPROM contents; string hits and offsets.
* **Derived** — header/entry parse (`0xEA00002E` → `0x080000C0`); localization table
  stride 0x18 with 6 language pointers per ID; key-mask scan classifications; the
  "password" module identified as N-Gage-derived from IMEI/Bluetooth/Billing-DLL markers;
  the Test Mode function at 0x08012B54 proven dead by zero BL/B/ARM-branch/pointer
  references (scanned over all 0x800000 bytes).
* **Inferred** — the online module is unreachable (no GBA UI, no hardware, no code
  xref); the precise EEPROM bit positions of the Challenge flags were not isolated.
  No inference is presented as an observation.

## 8. Unknowns

* The exact EEPROM byte/bit addresses of the 21 Challenge completion/unlock flags were
  not isolated (would require completing challenges or a save-patch experiment); the
  gates themselves are observed, the storage encoding is not.
* Whether the cut online/billing module's handlers execute on any unreachable code path
  was not proven by a never-firing breakpoint (GDB port 2345 was held by a sibling
  session; savestate diffing was used instead). No GBA UI reaches it.
* REA/Ghidra raw-binary import assigned mismatched addresses to this image (its
  "0x86F79DC = Custom Challenges" is compressed garbage; the real string is at
  0x087CACA4). REA results were discarded; all addresses in this report come from direct
  byte/pointer verification.

## 9. Tooling

* `file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings -t x`, `grep -abo`
* `python3` + `capstone` 5.0.7 (`scan.py`, `ptr.py`, `buttonscan.py`, `ss.py`, `rsp.py`,
  `helpers.py`, `combos.py`)
* `arm-none-eabi-objdump`, GDB RSP client (port was contended, not used for final evidence)
* `mgba -3` under `Xvfb :318`, `xdotool` XTEST input, `import -window root` screenshots,
  ImageMagick diff checks
* REA/Ghidra 12.1.4 was opened and closed; its raw-import addresses were rejected as
  unreliable for this image (§8).

## 10. Legal note

No ROM bytes, graphics, audio or game text are redistributed here — only hashes,
offsets, search counts and original observations. No GameShark/CodeBreaker or
memory-edit codes are published or used as cheat deliverables.

## 11. Cleanup

All processes started for this engagement were terminated by their own PID numbers
(Xvfb :318, openbox, mgba); no `pkill` was used. No `.sav`/`.ss*` files remain in
`roms/FIFA Football 2005/` — all emulator artifacts were created in `/tmp/fifa05/`.
`roms/INDEX.md` was not modified.
