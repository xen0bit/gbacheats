# Nicktoons: Freeze Frame Frenzy (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Nicktoons: Freeze Frame Frenzy.gba` |
| Size | 4,194,304 bytes (0x400000, 4 MiB) |
| Header title | `NICKTOONS` |
| Game code / maker | `BCCE` / `78` (Altron; published THQ) |
| Version / complement / checksum | `0x00` / `0x1D` / `0x0000` |
| Entry word | `0xEA00002E` (stock `b 0x080000C0`) |
| MD5 | `7a710c9d170d28397cf36002cce4734d` |
| SHA-1 | `a200cdaf66606bd724ce7073fd7990ea3fe6bcdd` |
| SHA-256 | `88034aa978153ace301d7026408a8cc2200e9b2a247b2fa70d6314fbfd00ba39` |

Phase 0: `file` reports `Game Boy Advance ROM image: "NICKTOONS" (BCCE78, Rev.00)`. A scan of the whole image for the 156-byte Nintendo logo found exactly **one** header, at file offset `0x0` — this is a single game image, not a 2-in-1 pack. The entry word is the unmodified ARM branch; no cracktro, no appended trainer, no patch was found. The zero header checksum is the usual rebuilt-header artifact; the complement byte is intact. Work was done on a byte-identical copy at `/tmp/nicktoonsfree/game.gba`.

## 2. Executive summary

**There is no developer-intended password, button-code, or enterable cheat-code system in this ROM.** Every published "cheat" for this SKU is a **progress unlockable** (photo-gallery completion and game/world completion), and all ten published entries are verifiable as literal UI strings in the image. There is no debug/test menu screen in the build: the only debug-adjacent strings (`Music Test`, `SFX Test`) are the ordinary OPTIONS volume controls, and `SECRET MODE` is the unlock-notification text bank, not a hidden menu.

The game is a photo-hunt action title. Its complete reachable screen set was walked in mGBA with screenshot **and RAM-state (VRAM hash) evidence**: Nick splash, attract sequence, title (NEW GAME only), intro dialogue, world select, character select (2 of 7 characters available at 0% gallery), gameplay HUD, pause menu (6 items + quit-confirm modal), main menu (4 items), OPTIONS (3 settings), SCORE RANKING (5 worlds), PHOTO ALBUM (7 pages, 0%). No screen beyond these exists at a fresh save.

The text system was decoded rather than assumed: the ASCII bank at `0x2D9050` holds every functional UI label, and the 75-symbol font charset at `0x0808150C` with its ASCII→tile converter at `0x08057B2C` was reversed. Searching the whole 4 MiB for font-indexed encodings of `PASSWORD`, `CHEAT`, `DEBUG`, `UNLOCK` across all 256 bases and both 8-bit/16-bit layouts returned **zero** hits; the stylized menu headings are baked tile art, not a hidden text bank. The input surface was bounded too: one joypad reader (`0x08000934`) with a single caller (`0x0807DE6C`), globals at `0x03004800`/`0x03004A00`, and **zero** button-mask code tables.

Per §0.2 this is a proven negative, not a "not found" claim: the screen set, the ASCII/tile text spaces, the button-mask space and the published-code space are all enumerated with counts below.

## 3. How to reproduce

* Emulator: mGBA SDL (`mgba -3 game.gba`, and `-g` for the GDB stub), `DISPLAY=:317`, `SDL_AUDIODRIVER=dummy`, Xvfb `:317` + openbox.
* Keymap (verified against on-screen menus): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad = arrows. **Hold keys 40–120 ms**; 150 ms double-steps some menus.
* Path: splash → Start → title `NEW GAME` → A → skip dialogue with Start → world select → A → character select → A → gameplay. In gameplay, Start opens PAUSE MENU; `RETURN TO MAIN MENU` → YES → main menu → `OPTIONS` / `SCORE RANKING` / `PHOTO ALBUM`.
* Codes tested: none exist to type. The ten published unlockables were checked as conditions: at a fresh save the PHOTO ALBUM reads `ALBUM% 00` and `01/07`, and the character select offers only **SpongeBob** and **Otto Rocket** (2 of 7); Danny Fenton, Tommy Pickles, Arnold, Jimmy Neutron and Invader Zim are absent, matching the locked set.
* Debug-only experiment: calling the SECRET MODE screen-init function `0x08079FC8` from GDB with a synthetic LR produced a black screen (§16.10 — a debugger call is not a screen entry). This is reported as a **failed forced view**, not as a reached screen.
* Web content used as data only (§16.8): 3rd party cheat indexes, Brave search snippets. No prompt-injection payload was observed in fetched pages.

## 4. Address map

| What | ROM file offset / address | Notes |
|---|---|---|
| Header | `0x000–0x0BF` | title `0xA0`, code `0xAC`, maker `0xB0`, version `0xBC` |
| Key reader | `0x008934` (`0x08000934`) | ARM literal `0x04000130` at `0x800954`; stores active-high masks |
| Held buttons global | `0x03004800` (u16) | `A=1,B=2,Sel=4,Start=8,R=0x10,L=0x20,U=0x40,D=0x80,Rtr=0x100,Ltr=0x200` |
| Newly-pressed global | `0x03004A00` (u16) | `held & ~prev` |
| Single caller of key reader | `0x0807DE6C` | no other poller |
| Font charset (75 chars) | `0x008150C` (`0x0808150C`) | ``A-Z a-z 0-9 ! ? - ' . , ` : ( ) % ~ <space>`` |
| Glyph width table | `0x0081558` | follows charset |
| ASCII→tile converter | `0x08057B2C` (called from `0x08057ADA`) | index→tile: `i + (i>63?64:(i>31?32:0))` |
| OPTIONS text + table | `0x2D9050`, table `0x2D90E4` (15 records) | code ref `0x08077D3C` |
| SCORE RANKING text + table | `0x2D9248`, table `0x2D9274` (3) | code ref `0x080793C8` |
| SECRET MODE text + table | `0x2D92BA`, table `0x2D946C` | code refs `0x0807A28C`, `0x0807B1A8` |
| SECRET MODE screen init | `0x08079FC8` | Ghidra-decompiled; forced call failed |
| PHOTO ALBUM text + table | `0x2D95C4`, table `0x2D960C` | code ref `0x0807CA0C` |
| Unlock notification strings | `0x2D92C6`, `0x2D92DF`, `0x2D92F8`, `0x2D9311`, `0x2D931E` | 20% / 40% / 60% / cleared / 100% |

Text-table records are `{u32 string_ptr, u8 len, u8 flag, u16 pad}`; flag `0x22` marks the first string of each of the three localized banks (English, and two untranslated copies suffixed `1`/`2`).

## 5. Algorithm

No password validator exists, so there is no code algorithm to reimplement. The two reversible algorithms that were recovered:

```
# ASCII -> font tile (0x08057B2C)
charset = bytes at 0x0808150C          # 75 symbols, 'A' at index 0
i = charset.index(ch)                  # loop at 0x08057AE8, i in 0..74
tile = (i + (64 if i > 63 else (32 if i > 31 else 0))) & 0xFF
```

```
# text-table record (0x2D90E4 etc.)
ptr, packed = u32, u32
length = packed & 0xFF
flag   = (packed >> 8) & 0xFF          # 0x22 = bank header
string = rom[ptr - 0x08000000 : ptr - 0x08000000 + length]
```

## 6. Tables

### Published unlockables (all ten verified as ROM strings / gated state)

| Unlockable | Published condition | ROM evidence |
|---|---|---|
| Danny Fenton | 20% picture gallery | `Player has gone over 20%` @ `0x2D92C6` |
| Tommy Pickles | 40% picture gallery | `Player has gone over 40%` @ `0x2D92DF` |
| Arnold | 60% picture gallery | `Player has gone over 60%` @ `0x2D92F8` |
| Jimmy Neutron | Finish the game | `Game cleared` @ `0x2D9311` / `0x2D9338` |
| Invader Zim | Finish the game | `Game cleared` @ `0x2D9311` / `0x2D9338` |
| SpongeBob World | Complete FairlyOdd Parents World | world progression |
| Ocean Shores World | Complete SpongeBob World | world progression |
| Danny Phantom World | Complete Ocean Shores World | world progression |
| All Grown Up World | Complete Danny Phantom World | world progression |
| Invader Zim's Ship | Complete All Grown Up World | world progression |

Header string `SECRET MODE` @ `0x2D92BA` (×3 localized copies) accompanies those notifications; it is not a menu entry.

### Reachable screens and RAM evidence

Each row is a savestate whose decompressed `gbAs` VRAM region (state offset `0x1000..0x19000`, i.e. `0x06000000..0x06018000`) was hashed — a distinct hash is direct RAM evidence that the screen was rendered, independent of the screenshot.

| Screen | State file | VRAM SHA-256 (first 16) |
|---|---|---|
| Main menu (MAIN GAME highlighted) | `sc_main.ss1` | `8e163ab660d37c79` |
| Main menu (PHOTO ALBUM) | `sc_main_album_sel.ss1` | `58e05a4650cf3a01` |
| Main menu (SCORE RANKING) | `sc_main_score_sel.ss1` | `b8dca67e162c036f` |
| Main menu (OPTIONS) | `sc_main_options_sel.ss1` | `f0fff604cdbeec54` |
| OPTIONS screen | `sc_options.ss1` | `f9992110a5ea602b` |
| PHOTO ALBUM (0%) | `state_album.ss1` | `618eecbe09f4eeeb` |
| Character select | `sc_char_select.ss1` | `37a1d6aa68e78df2` |
| World select | `sc_world_select.ss1` | `acf436ef6e551ff3` |
| Gameplay HUD | `sc_gameplay.ss1` | `ca14c1b1dafbd0f2` |
| PAUSE MENU | `sc_pause2.ss1` | `0b237a98edf49578` |
| Quit-confirm modal | screenshot `s18_quit_yes.png` | (transient modal) |

Save file: 512-byte Flash/EEPROM `game.sav`; album at 0% on a fresh save.

## 6b. Enumeration

**Space definition / negative proof.** There is no code space to enumerate; the searched spaces and their exact sizes are:

| Search space | Method | Result |
|---|---|---|
| All printable strings (4 MiB, `strings -t x -n 4`, 40,230 lines) | case-insensitive keyword counts | `password`=0, `cheat`=0, `unlock`=0, `debug`=0, `level select`=0, `GameShark`/`CodeBreaker`=0; `secret`=3 (all `SECRET MODE` banks); `code`=4 (all the same Zim dialogue line); `menu`=0 (baked art, see below) |
| Font/tile-indexed text | decoded 75-symbol charset `0x0808150C` + converter `0x08057B2C`; searched 4 MiB for tile sequences of `PASSWORD`,`CHEAT`,`CHEATCODE`,`DEBUG`,`UNLOCK` in 8-bit (bases 0–255) and 16-bit LE (bases 0–1023 × 5 attribute values) | 0 hits for all five words; only `SECRET` hit (the three known ASCII banks at base 0x41) |
| Stylized menu labels | searched for charset-index encodings of `MAIN GAME`, `PHOTO ALBUM`, `SCORE RANKING`, `MAIN MENU`, `NEW GAME` as 8-bit/16-bit, contiguous and strided | 0 hits → these are baked tile art, not a text bank |
| Button-mask tables | scanned every u16 pair; 2,995 runs of ≥4 consecutive plausible active-high masks; cross-checked against every 32-bit pointer in the image | 24 runs have code pointers, **all 24** lie in the font/graphics block `0x08081428–0x08082B68` (e.g. `08 01 01 00`, `100 302 104 2` = tile/palette data) → 0 button-code tables |
| Joypad input path | literal scan for `0x04000130` + BL scan | 1 reader (`0x08000934`), 1 caller (`0x0807DE6C`) → no cheat comparator |
| Reachable screens | full menu walk with states | 11 distinct screens + 1 modal (table above) |

**Novel codes:** none generated, because no enterable code system exists. Per §0.2 item 5 the negative is bounded by the counts above instead. **Bounds proven by rejection:** the on-screen character select rejects (does not list) five characters at 0% gallery; the PHOTO ALBUM rejects further entries (`01/07`, `ALBUM% 00`), and forcing `0x08079FC8` from the debugger does not produce a usable SECRET MODE screen — all three are observed bounds on what this save state can reach.

## 7. Validation evidence

* **Observed** (emulator): all screenshots listed in §3/§6; VRAM hashes from savestates; 2/7 characters selectable; album `00%`, `01/07`; OPTIONS 3 settings (`Music Test 01`, `SFX Test 01`, `Music/SFX ON`); SCORE RANKING 5 worlds; PAUSE MENU 6 items; quit-confirm modal.
* **Observed** (GDB, mGBA stub via persistent FIFO — `-batch` fails with `vMustReplyEmpty: timeout`): `0x03004800` held / `0x03004A00` pressed; single key-reader caller confirmed by BL scan.
* **Derived** (static, verified with `objdump -M force-thumb` and Ghidra): font charset/converter; text-table record layout and code xrefs; key-mask globals; unlock-string addresses; single-header/no-patch conclusion.
* **Inferred** (labeled): that `SECRET MODE` is the unlock-notification screen rather than a selectable main-menu item — the strings and two code xrefs support this, but the notification itself was not triggered in-game because the required gallery/game completion was not performed.
* **Negative** (bounded): no password, button-code or debug menu exists in this exact ROM; see §6b for the enumerated spaces and counts.

## 8. Unknowns

* The exact save-record field/bit for each unlock was not isolated; unlock conditions were verified by their literal strings and by the locked character set, not by tracing the setter's callers (§16.18).
* The unlock notification (`SECRET MODE`) was never triggered legitimately — it needs 20% gallery or game completion, which was not played through.
* The two localized banks suffixed `1`/`2` are untranslated English copies; no language selector was found, so their selection gate is unknown.
* Whether `SECRET MODE` could be entered after 100% completion was not proven; the debugger-forced call failed (black screen).

## 9. Tooling

`strings -t x`, `grep -abo`, `xxd`, `file`, `md5sum`/`sha1sum`/`sha256sum`, `arm-none-eabi-objdump -M force-thumb`, `capstone` 5.0.7, `gdb-multiarch` over a named FIFO against mGBA's `-g` stub (SIGINT needed to flush queued commands), Ghidra 12.1.4 via REA (`open_binary`, `procedure_pseudo_code`), Python helpers in `/tmp/nicktoonsfree/`: `ui.py` (xdotool input/screenshots), `ss.py` (zlib `gbAs` extraction from mGBA `.ss1`), `ram.py`/`gdbwrap.py` (state diff / GDB reads), `scan.py`, `textbank.py`, `fontscan.py`.

No ROM or copyrighted asset is redistributed here; only addresses, hashes, counts and findings are published.

---

*Cleanup note: all emulator/display processes started for this job were terminated by PID; generated `game.sav`, `game.ss1` and working artifacts were kept only under `/tmp/nicktoonsfree/` and removed from the ROM folder. `roms/INDEX.md` was not modified.*
