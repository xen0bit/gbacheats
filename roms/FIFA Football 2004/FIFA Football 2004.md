# FIFA Football 2004 (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `FIFA Football 2004.gba` |
| Size | 8,388,608 bytes (0x00800000, 8 MiB) |
| Header title | `FIFA 2004` |
| Game code | `BFIE` (Europe) |
| Maker code | `69` |
| Version | 0x00 (Rev.00) |
| Fixed byte / main unit / device | 0x96 / 0x00 / 0x00 |
| Header checksum | 0x0000 (normal rebuilt-header artifact, guide §16.1) |
| Entry word | `0xEA00002E` → `0x080000C0` (stock crt0, not a cracktro) |
| MD5 | `f9e6bfc9404be783b149259ffd9c5da0` |
| SHA-1 | `031204fbbfd00a2ece04eae590596cdf676d9537` |
| SHA-256 | `7d2499645581ef787423555830d90d46383553b735e1e209bd762369cf2fa78d` |

**Embedded-header scan:** the full 156-byte Nintendo logo occurs exactly **once**, at file 0x0 (ROM `0x08000000`) — a single retail image, no appended trainer, no multiboot stub, no second game. No patch/trainer was applied.

**Independence check (concurrent siblings):** FIFA 06 (`BF6E69`, MD5 `13682a498effaef25aaaad9ac02cb4c0`) and FIFA 07 (`B7FE69`, MD5 `bf4a0f61e2e78a120ba1edd4cfa6a101`) are different images with different hashes and game codes. Every address, string and conclusion below was derived from *this* image's own bytes; nothing was carried over from the siblings. The only commonality is the Exient FIFA GBA engine family (generic), which is not evidence of a shared code surface.

## 2. Executive summary

**There is no in-game / developer-intended cheat system in this ROM.** No password entry, no typed code, no button cheat sequence, and no hidden debug menu exists. The negative is proven, not assumed:

* The complete UI lexicon is plain ASCII/Latin-1 text (`strings` finds every on-screen label); keyword counts over 67,041 strings are `password`=0, `cheat`=0, `debug`=0, `codes`=0, `classic`=0, `stadium`=0, `legend`=0; the only `secret`/`unlock`/`boot` hits are a player surname ("Oliveira Secret"), the reset-dialog wording, and a player surname ("Walls"/"Booth") — all inspected in context.
* All published "codes" for this title are **out of scope**: GameShark/CodeBreaker memory codes, and three cheat-device label words (`MOMONEY`, `HOOLIGAN`, `BURNABY`, `SIZZLE`, `DIZZY`, `LIGHTSOUT`) that are **absent from the ROM** in ASCII, lowercase, ±0x20, UTF-16LE and UTF-16BE. The three often-quoted "Big Ball / Walls / Flying" cheats are **GameCube-link unlocks**, not typed codes; the link screen only says "Waiting for connection from Nintendo GameCube…".
* The only input-history structure in the game (32-entry u16 ring at `0x02013470`) is consumed solely for edge-triggered press detection and cleared on screen changes — no comparison against a code table exists.
* Every reachable screen was walked in mGBA with savestate RAM evidence (screen index `0x03007EB8` verified 0–4 on the main menu). Three undocumented button combinations were pressed on the main menu; no hidden screen appeared and RAM showed only ordinary menu navigation.

Unlockables (4 greyed competitions) are **save-data / GameCube-link progression flags**, not codes: `EFA Trophy`, `European Champions Cup`, `International Cup`, `Ladder Tournament`. A "Reset all completed competitions and relock all unlocked tournaments?" / "Relock All Competitions?" option exists in the link/credits text bank but is not reachable from any menu in this build without a link cable.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 under Xvfb `:315`, `SDL_AUDIODRIVER=dummy`, `-3` scale. Keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrow keys. Hold keys 50–200 ms.
* Language select (six flags) → any key → main menu.
* Menu path walked (all with screenshots and savestates): Main menu (Friendly / Multiplayer Mode / Competitions / Options / Nintendo GameCube Link) → Options (Game, Display, Sound, Control, Language, Credits) → each options submenu → Competitions → Choose a Save Space (3 slots) → Select a Competition (21 entries) → Friendly → Choose Your Team → Choose CPU Team → Select Kit → Team Management → Today's Friendly → Controls reminder → live match → Pause Menu (Resume, Team Management, Instant Replay, Match Statistics, Options, Quit Match) → Multiplayer Mode ("Connect all Players") → Nintendo GameCube Link (waiting screen).
* RAM evidence method (no GDB stub available — port 2345 was occupied by a sibling session): save mGBA states with `Shift+F1..F9`, decompress the PNG `gbAs` chunk with `zlib`, and read RAM with the mapping below. Mapping verified by finding the literal `"Nintendo GameCube Link"` at state offset `0x190E0` = IWRAM `0x030000E0`, and by a 512-byte all-`0xFF` block at state `0x25C30` = EWRAM `0x02034C30` matching the 512-byte `.sav`.
* Codes tested: none accepted by the game (no entry surface exists). Published words and CodeBreaker codes were verified statically only (see §6b).

## 4. Address map

| Item | Address / offset | Evidence |
|---|---|---|
| ROM header / title | `0x08000000` / title at file `0xA0` | Observed (xxd) |
| Single Nintendo logo | file `0x0` | Derived (scan) |
| UI text bank (ASCII/Latin-1) | file `0x475000`–`0x47E000` (`0x08475000`–`0x084E0000`) | Observed (`strings` + screenshot text match) |
| Competition-name localization groups (6 pointers each: ES/IT/DE/FR/EN/0) | `0x0849F470` (European Champions Cup), `0x0849F488` (EFA Trophy), `0x0849F4A0` (International Cup), `0x0849F4B8` (Americas Club Championship), `0x0849F4D0` (Ladder Tournament) | Derived (pointer dump) |
| GC-link / unlock text | `0x08477C40` (waiting…), `0x08477D48` ("The %s is available in Competitions"), `0x08477ED8` ("Relock All Competitions?"), `0x08478500` ("Reset all completed competitions…") | Derived (pointer dump) |
| Main-menu selection index (IWRAM) | `0x03007EB8` = 0 Friendly, 1 Multiplayer, 2 Competitions, 3 Options, 4 GameCube Link; struct at `0x03007EB0` | Observed (savestate diff across five selections) |
| Key input literal `0x04000130` | file `0x3C8C`, `0x19020`, `0x2081C`; Thumb readers `0x08003C60`, `0x08018FEE`, `0x080207CC` | Derived (Capstone/objdump) |
| Input history ring (32 × u16, inverted `~KEYINPUT`) | base `0x02013470`, counter `0x02013A14`; writer `0x08003C34`, readers `0x08017978` (edge detect) and `0x08018D14` (clear) | Derived (disassembly) |
| Save-data image (512 bytes) | EWRAM `0x02034C30`; mirror `0x020358D0`; save/checksum routines `0x0802E4C0`, `0x0802E524`, `0x0802E57C`, `0x0802E60C` | Derived (disassembly + savestate) |
| mGBA `.ss1` layout | zlib `gbAs` chunk → 0x61000 bytes; IWRAM `0x03000000+X` → raw `0x19000+X`; EWRAM `0x02000000+X` → raw `0x21000+X` | Derived (verified against known strings/save block) |

## 5. Algorithm

No validator, decoder, checksum or code generator exists. The only algorithms recovered are engine housekeeping:

```
; input history writer, 0x08003C34 (Thumb)
counter = [0x02013A14]; counter++
history[(counter & 31) * 2 + 0x02013470] = ~KEYINPUT        ; 0x08003C60

; edge detection, 0x08017978 (Thumb), the ONLY substantive reader
cur  = history[((counter - 4) & 31) * 2 + 0x02013470]
prev = [previous_input]
pressed = (cur ^ prev) & cur                                ; 0x080179A8–AC
[pressed_var] = pressed; [previous_input] = cur
; no cmp against any constant mask or code table follows.

; screen-change reset, 0x08018D14
memset(0x02013470, 0, 0x40); clear pressed/prev/cursor vars
```

Save unlock data is a 512-byte EEPROM image at `0x02034C30`; the routine at `0x0802E4C0` computes a checksum with `0x08018E68` over 8 nibble-packed bytes from `0x020358D0`, appends it as byte 8, writes 9 bytes to the save image and commits 17 bytes. This is link/progress data, not a user-entered code.

## 6. Tables

**Main menu (index at `0x03007EB8`, RAM-verified):** 0 Friendly, 1 Multiplayer Mode, 2 Competitions, 3 Options, 4 Nintendo GameCube Link.

**Options menu:** Game Options, Display Options, Sound Options, Control Options, Language, Credits. Submenus contain only settings (CPU/GK skill, half length, extra time, pitch type, wind, auto replay; radar, score display, player names, brightness; sound FX, music; controls, auto switch). No hidden entry.

**Competition list (21 entries, observed on screen):** Americas Club Championship (available), **EFA Trophy (locked)**, **European Champions Cup (locked)**, **International Cup (locked)**, **Ladder Tournament (locked)**, then 16 available leagues (Austrian T-Mobile Bundesliga, Belgian League, Danish Superligaen, Dutch League, English Premiership, French Division 1, German Bundesliga, Italian League, K-League, MLS, Norwegian Tippeligaen, Portuguese League, Scottish Premier League, Spanish Primera, Swedish Allsvenkan, Swiss Super League). Locked entries render grey and cannot be started.

**Pause menu:** Resume Match, Team Management (disabled in friendly), Instant Replay, Match Statistics, Options (4 sub-options only), Quit Match.

**Published-code verification table:**

| Source | Claim | ROM verification | Verdict |
|---|---|---|---|
| emuinfo.pl "Fifa 2004 (PL)" | `MOMONEY`, `HOOLIGAN`, `BURNABY`, `SIZZLE`, `DIZZY`, `LIGHTSOUT` | 0 hits in ASCII, lowercase, +0x20, −0x20, UTF-16LE/BE over all 8 MiB | Unverified; cheat-device labels, not in-game codes |
| Almars/GameShark GBA | Master code `00006496 000A` etc. | Cheat-device memory patches | Out of scope (not developer-intended) |
| GameFAQs/TGDB "Three cheats GC" | Big Ball / Walls / Flying via GBA–GameCube link | No code strings; link screen is a passive "Waiting for connection" screen; unlock text at `0x08477D48` | Real unlocks, but link-gated, not typed codes |
| GameFAQs "Unlock More Teams GBA" | Defeat tournament with Brazil 4 times | Progression text at `0x08478264` ("You won the ladder tournament") | Gameplay unlock, not a code |
| Console/PC guides | Seoul/Yokohama stadiums, third kits | `stadium`=0, `classic`=0, kit unlock strings absent as codes | Console-version content, not GBA codes |

## 6b. Enumeration

**Code space:** empty. There is no password alphabet, no literal table, no validator and no code entry widget anywhere in this build. Bounded search proof:

* `strings -t x -n 4` → 67,041 strings over 8 MiB; keyword counts: `password` 0, `cheat` 0, `debug` 0, `codes` 0, `secret` 1 (player name), `unlock` 1 (reset dialog), `classic` 0, `legend` 0, `stadium` 0, `boot` 1 (player "Booth").
* Candidate published words (9 literals × 6 encodings = 54 literal searches): all zero hits.
* Embedded GBA headers: 1.
* `0x04000130` literals: 3; input-history readers: 2; both are edge detection / reset, with no constant-mask comparison and no code table.
* UI text is ASCII/Latin-1 (verified bytes `0x47B6C4` = "Competiciones\0"; `0x477D48` = "The %s is available in Competitions\0"), so the `strings` lexicon covers the entire visible text space — there is no tile-indexed hidden text bank to decode.

**Button-code space:** the ring buffer holds 32 recent u16 masks, but no matcher consumes it. Three undocumented combinations were pressed on the main menu with pre/post RAM reads:

1. `L+R+Start` → index stayed `0x00` (no hidden screen).
2. `↑↑↓↓←→←→ B A` → index `0x15` (ordinary menu enter).
3. `A+B+Start+Select` → index `0xC0` (returned to language select).

No undocumented state was produced; the only state changes are normal menu navigation.

**Unlockables (not codes):** 4 competitions are locked from a fresh save — EFA Trophy, European Champions Cup, International Cup, Ladder Tournament. They are gated by save/link data (512-byte EEPROM image at `0x02034C30`), not by any user input code. "Reset all completed competitions and relock all unlocked tournaments?" and "Relock All Competitions?" exist in the link text bank (`0x08478500`, `0x08477ED8`) but no reachable menu in this build exposes them without a GameCube link cable. Per guide §16.18, a save-bit unlock is not a code and was not brute-forced.

**Novel code:** not applicable — §0.2's "mint a code absent from published lists" deliverable requires a code system; none exists. The §0.2 point-5 negative-result deliverable is met by the exhaustive screen walk, the counted string/literal/button searches, and the published-code verification above.

## 7. Validation evidence

* **Observed:** all 13 screen families listed in §3, screenshots saved on disk; main-menu index `0x03007EB8` read as 0,1,2,3,4 across five savestates matching the highlighted row; 512-byte all-`0xFF` save image at EWRAM `0x02034C30`; four greyed competitions; three button combos producing only ordinary navigation.
* **Derived:** single embedded header; input ring buffer is edge detection (`0x08017978: eors/ands`) and reset (`memset` 0x40 at `0x08018D14`), with no code-table comparison; save checksum/link-write routine at `0x0802E4C0`; published literals absent in six encodings; `KEYINPUT` has exactly three literal references.
* **Inferred:** the 4 locked competitions unlock through progression and/or GameCube link (consistent with GameFAQs and the ROM's unlock text at `0x08477D48`), but a full season/link session was not played, so the precise unlock bit and its setter are not individually proven. This does not affect the code-system negative.

## 8. Unknowns

* Exact save-bit position/format for each of the four locked competitions (EEPROM image at `0x02034C30`); requires a completed season or a live GameCube link to observe a setter.
* The "Relock All Competitions?" prompt's exact trigger screen; present in the text bank but not reached by any offline menu path.
* Whether the GameCube-link "Big Ball / Walls / Flying" flags map to distinct bits in the 9-byte link write at `0x0802E4C0`; not exercised without a link cable.

## 9. Tooling

* `file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings -t x -n 4`, `grep -abo`.
* Python 3 with `capstone` 5.0.7 / `keystone-engine` for literal, LDR-pool and BL scans; `arm-none-eabi-objdump -M force-thumb` for disassembly.
* mGBA 0.10.5 under `Xvfb :315` + `openbox`; `xdotool` XTEST input; `import -window root` screenshots; `Shift+F1..F9` savestates; Python `zlib` decompression of the PNG `gbAs` chunk for RAM reads (`ramread.py`).
* No GDB stub was used: port 2345 was held by a concurrent sibling session, and the occupancy was confirmed by resolving socket inode to PID (not killed).
* All generated `.ss*` / `.sav` files were removed from the ROM folder; only this report remains next to the ROM. No ROM or copyrighted asset is redistributed.
