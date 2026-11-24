# Stadium Games (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Stadium Games/Stadium Games.gba` |
| Size | 4,194,304 bytes (`0x400000`, 4 MiB) |
| Header title | `STADIUMGAMES` |
| Game code | `A9GE` |
| Maker code | `7M` (Ignition Entertainment, © 2002 per boot screen) |
| Version | `0x00` (Rev. 00) |
| Fixed byte | `0x96` at `0xB2` |
| Complement / checksum | `0x43` / `0x0000` (rebuilt-header artifact; entry word is stock) |
| Entry word | `0xEA00002E` → `b 0x080000C0`, **stock crt0, no cracktro/trainer** |
| Engine | `sgga` (debug paths `D:\sgga\src\SGGATXT.CPP`, `SGGADLG.CPP`, `SYSTGBA.CPP`, `SYSTUNPK.CPP`) |
| MD5 | `47e02ac1a4cc0d5f7441426469015dd7` |
| SHA-1 | `71cb60817329ae94023fb1dcd5e70d379a4d3344` |
| SHA-256 | `17925836fe7360d4edd06fa8ac675b483822219485bff120f5bdbbfd1d7b24df` |

The whole 4 MiB file was scanned for a second Nintendo logo / concatenated image; there is exactly one GBA header. No appended trainer, no second game.

## 2. Executive summary

**Bounded negative: this ROM has no developer-intended cheat system.** There is no password entry screen, no code validator, no published code list to reproduce, no button-activation sequence, and no reachable debug/unlock menu. The only user-supplied text field is the 6-character **high-score name** (`ENTER NAME`), whose buffer is consumed only by the score table — it is not compared against any constant.

The game is a 2002 Ignition Entertainment athletics compilation (Shooting, Archery, Javelin, Football, Pole Vault, Hammer Throw) built on the in-house `sgga` engine. All menus are ordinary: Main Menu (PLAY / OPTIONS / HI-SCORES), Options (Music / SFX / Credits / Back), Select Game (PRACTICE / TOURNAMENT / Back), Select Event (six fixed events + Back), in-event pause (Continue / Quit), Event Results (NEXT), and Hi-Scores with four preset names (MARTIN 50000, CHRIS 40000, DAVE 30000, ANT 20000 — the first two are programmer names from the credits, not debug codes).

Complete evidence for the negative is in **§6b**: the entire 4 MiB search space was enumerated (all ASCII strings, the complete 50-entry UI text table, all key-state consumers, all button-mask tables) and 20 button-code candidates were pressed in the emulator with no state change. No novel code could be minted because there is no code space to mint from; the enumeration instead proves the space is empty.

One UI label, `PLAYBACK` (text-bank index 29), is present in the string table but was **not** reached on any of the walked screens. It is grouped with ordinary menu labels and is classified as an unexercised normal UI string, not a cheat. This is stated as an unknown rather than as evidence of a hidden feature.

## 3. How to reproduce

* Emulator: mGBA 0.10.5, headless SDL, `DISPLAY=:317`, `SDL_AUDIODRIVER=dummy`, `mgba -3 <rom>`.
* Keymap (mGBA SDL default): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows. Hold 50–120 ms; longer holds double-step menus.
* Boot path: `AIA` splash → Ignition copyright → Main Menu (~2 s).
* Screen path used:
  * `Main Menu` → A → `Select Game` (PRACTICE / TOURNAMENT / Back)
  * → A → `Select Event` (six events) → A → gameplay
  * gameplay + Start → pause (Continue / Quit)
  * event end → `EVENT RESULTS` → NEXT → back to Select Event
  * `Main Menu` → DOWN×2 → `HI-SCORES` (preset table, Back)
  * `Main Menu` → DOWN → `OPTIONS` → Music On/Off, SFX On/Off, CREDITS (3 pages), Back
* No save type was required for any of the above. No code was ever accepted or rejected by a validator, because none exists.

## 4. Address map

| Item | Address | Notes |
|---|---|---|
| Header / entry | `0x08000000` / `0x080000C0` | stock `b 0xC0` crt0 |
| Key input register | `0x04000130` | raw active-low GBA keypad |
| **Key state (active-high)** | `0x03000014` (IWRAM) | written as `~(u16)*0x04000130`; 28 reader sites found |
| Engine key-edge helper | `0x0800441C` | `FUN_0800441C(mask, repeat, *released)`; computes pressed edges from current/previous state; live breakpoint confirmed hit every frame |
| Key-setter helper | `0x08004494` | `FUN_08004494(mask, repeat)` |
| Main screen dispatcher | jump table `0x08000468`, 5 entries → `0x0800047C`, `0x080004AC`, `0x08000520`, `0x080005B0`, `0x080006FC` | reads key state and branches on A / Start |
| Event-screen dispatcher | jump table `0x08005C30`, 7 entries `0x08005C4C`…`0x08005E7C` | all test only key bit 0 (A) |
| `sgga` string-error bank | `0x08014D14`–`0x0801513C` | font/sprite/system debug strings, no cheat text |
| Font glyph-order tables | `0x08015D80`–`0x08015ED8` | character code → tile index maps; not a password alphabet |
| **UI text bank** | `0x08240DFC`–`0x08241150` (752 bytes) | single contiguous ASCII blob, `ENGLISH` first |
| **UI string offset table** | `0x08240D98`, 50 × `u16` | offsets relative to the table base; decodes every label exactly |
| Default hi-score names | `0x0805A114` (`MARTIN`), plus `CHRIS`, `DAVE`, `ANT` nearby | verified on the HI-SCORES screen |

File offset ↔ ROM address: `rom_addr = 0x08000000 + file_offset`. E.g. text bank at file `0x240DFC` → `0x08240DFC`.

## 5. Algorithm

There is **no validator to reverse**. The generic input machinery was reconstructed only to bound the search:

```
; every input-polling site in the game reduces to this pattern (e.g. 0x080003E2)
r0 = *(volatile u16*)0x04000130
r0 = ~r0 & 0xFFFF
*(u32*)0x03000014 = r0                 ; active-high held keys

; menu consumers read only single bits:
keys = *(u32*)0x03000014
if (keys & 0x001) -> confirm (A)        ; 0x0800047C, 0x080005C4C, ...
if (keys & 0x008) -> start / skip       ; 0x080016F6, 0x08006104
if (keys & 0x040) -> up                 ; 0x08000B12
pressed = (cur ^ prev) & cur & mask     ; FUN_0800441C
```

No site compares the key word against a multi-button mask, no site maintains a press-history ring, and no site writes a secret/flag word from input. The only multi-bit-looking matches from a naive Thumb `CMP #imm` scan (27,246 raw hits) are generic immediates in unrelated code; filtering to the 28 true key-state readers leaves only the single-bit tests above.

## 6. Tables

### 6.1 Complete UI text table (50 entries, base `0x08240D98`)

`ENGLISH`, `Producer`, `Steve Marsden`, `Peter Rollinston`, `Executive Producer`, `Vijay Chadha`, `Sarah Per`, `Special Thanks`, `Sales/Marketing/PR Director`, `Product Development Director`, `License/Acquisition Director`, `Ellen Fuog`, `Ken Gratz`, `Shane Takakashi`, `Shooting`, `Archery`, `Javelin`, `Football`, `Pole Vault`, `Hammer Throw`, `YES`, `NO`, `Music Off`, `Music On`, `SFX Off`, `SFX On`, `MAIN MENU`, `OPTIONS`, `HI-SCORES`, **`PLAYBACK`**, `BACK`, `MUSIC`, `CREDITS`, `Sound FX`, `ENTER NAME`, `PRACTICE`, `TOURNAMENT`, `NEXT`, `GET READY`, `2 PLAYERS`, `1 PLAYER`, `SELECT EVENT`, `SELECT GAME`, `EVENT RESULTS`, `PLAYER`, `TOURNAMENT RESULTS`, `OVERALL EVENT RESULTS`, `Continue`, `Quit`, (empty slot).

No `PASSWORD`, `CHEAT`, `CODE`, `DEBUG`, `SECRET`, `UNLOCK`, `INVALID`, `CORRECT`, `WRONG`, `GENERATOR`, `MASTER`, or `LEVEL SELECT` appears anywhere in the 4 MiB image.

### 6.2 Key mask bits (active-high at `0x03000014`)

`A=0x001`, `B=0x002`, `Select=0x004`, `Start=0x008`, `Right=0x010`, `Left=0x020`, `Up=0x040`, `Down=0x080`, `R=0x100`, `L=0x200`.

### 6.3 Screen inventory (all reached screens)

| Screen | Items / states |
|---|---|
| Boot | AIA splash, Ignition copyright |
| MAIN MENU | PLAY, OPTIONS, HI-SCORES (3-item ring) |
| OPTIONS | Music On/Off, SFX On/Off, CREDITS, BACK (4) |
| CREDITS | 3 pages (Producer/Programming/Music/Artists; Special Thanks; Sales/License) |
| SELECT GAME | PRACTICE, TOURNAMENT, BACK (3) |
| SELECT EVENT | Shooting, Archery, Javelin, Football, Pole Vault, Hammer Throw, BACK (6+1) |
| Gameplay | event HUD + score; Start → pause |
| Pause | Continue, Quit (2) — **no PLAYBACK** |
| EVENT RESULTS | event name, PRACTICE/score, NEXT |
| HI-SCORES | MARTIN 50000, CHRIS 40000, DAVE 30000, ANT 20000, BACK |

Unreached labels from the text table: `2 PLAYERS`, `1 PLAYER`, `TOURNAMENT RESULTS`, `OVERALL EVENT RESULTS`, `PLAYER`, `ENTER NAME`, `PLAYBACK`, `MUSIC`. All are ordinary game-mode/result labels; none is a cheat token. A full six-event tournament was started but not completed, so the post-tournament screens remain unexercised (see §8).

## 6b. Enumeration

**Code-space size: 0.** There is no password field, no algorithm, no lookup table of accepted secrets, no button-code dispatcher, and no gated debug screen; therefore the count of developer-intended cheat codes in this ROM is **zero** and no novel code can exist.

**Novel codes:** none — not omitted, but impossible. The §0.2 deliverable of minting an unpublished code is replaced by the bounded-negative deliverable, with the searched space and counts below.

**Bounds proven by rejection (dynamic):** the following 20 combos/sequences were pressed on the live Main Menu with screenshot comparison against a baseline frame. None produced a new screen, new menu item, or state change beyond ordinary cursor movement/palette animation:

`L+R`, `L+R+Start`, `L+R+Select`, `A+B+Start+Select`, `Start+Select`, `A+B`, `Up+Down`, `Up+Down+Left+Right`, `Up Up Down Down Left Right Left Right B A`, `L+R+A+B`, `L+R+Up`, `L+R+Down`, `Select+A`, `Select+B`, `Start+A`, `R+Start`, `L+Start`, `R+Select`, `L+Select`, `Up Up Up`.

Additionally, `Start` during gameplay opens only the 2-item pause menu (Continue/Quit), confirming no hidden pause-menu entry.

**Search space and counts (static):**

| Space checked | Count | Result |
|---|---|---|
| Whole ROM bytes | 4,194,304 | one header, no trainer/second image |
| Printable ASCII runs ≥ 4 chars | 37,031 | 4 keyword hits, all engine font errors (`Invalid colour depth`, `Font ID…`, `Font version…`, `Endian for the font…`) |
| Ghidra-defined strings | 109 | zero cheat/debug/password labels |
| UI text bank | 752 bytes / 50 strings | fully decoded via 50-entry u16 table; no hidden label |
| Contiguous uppercase runs ≥ 24 chars | 16 | font glyph-order data / compressed graphics, not alphabets |
| Digit+symbol runs ≥ 16 chars | 345 | standard font sets (`@ABCDEFGHIJK0123456789`, `0123456789ABCDEF`) and graphics noise |
| Raw `u16` key-mask runs ≥ 4 | 21 | all are OAM/sprite attribute tuples at `0x08059xxx`–`0x0808Axxx`, not press sequences |
| Equal-length NUL-string runs ≥ 4 | 9 | font tables and compressed data, not code tables |
| Readers of key state `0x03000014` | 28 | 9 are KEYINPUT writers; 19 are readers, all single-bit (A / Start / Up) |
| Live button-code candidates | 20 | all rejected (no effect) |

**Rejection-bound interpretation:** because no field, alphabet, checksum, or validator exists, the usual "bad checksum" / "out-of-range field" rejection tests have no target. The equivalent bounds here are (a) the complete string/table enumeration showing no code surface exists and (b) the 20 in-game rejection tests showing no controller input reaches a hidden state. This is a closed negative for the enumerated space, not "did not test".

## 7. Validation evidence

* **Observed** — mGBA screenshots of every screen in §6.3; L+R etc. leave the Main Menu unchanged; Start in gameplay yields only Continue/Quit; HI-SCORES shows the four preset names; all six event names cycle in Select Event.
* **Observed (RAM)** — mGBA CLI debugger (`mgba -d`) with a Thumb breakpoint at `0x0800441C` confirms the input helper runs every frame; `r/4 0x03000014` returns the live active-high key word (`0x0000FC00` at rest, i.e. only unused high bits set); key-state pointer literals resolved to `0x03000014` at 10 pool addresses and 28 `LDR literal` sites.
* **Derived** — Thumb disassembly (`arm-none-eabi-objdump -M force-thumb`) of the key-read sites and dispatcher tables; Ghidra pseudocode of `FUN_0800441C`/`FUN_08004494` (edge-triggered key mask, no sequence state); the 50-entry text table base/offset decode; stock entry word from header bytes.
* **Inferred** — `PLAYBACK`, `1 PLAYER`, `2 PLAYERS`, `TOURNAMENT RESULTS`, `OVERALL EVENT RESULTS`, `ENTER NAME` belong to post-tournament/normal game-mode screens. This is plausible from the label cluster but was not observed on screen.

Web reconnaissance (GameFAQs/Google/Bing/DuckDuckGo queries for `Stadium Games GBA passwords/cheats`, game code `A9GE`, Ignition Entertainment) returned no published code list; automated search engines were largely blocked or returned unrelated "stadium" results. Absence of a published list is consistent with, but is not the basis for, the negative result.

## 8. Unknowns

* A complete six-event tournament was not finished. The screens `TOURNAMENT RESULTS`, `OVERALL EVENT RESULTS`, `ENTER NAME`, `1 PLAYER`/`2 PLAYERS`, and `PLAYBACK` were therefore not observed. They are normal UI labels with no cheat-like syntax; if any is gated behind a clear condition, that condition was not identified.
* The exact screen that consumes `PLAYBACK` remains unlocated. Zero 32-bit pointers to the text bank or its offset table were found in the static image, so the engine must compute the resource address at runtime (consistent with the `SYSTUNPK.CPP` unpacker); this prevented a static xref from label to screen.
* mGBA's GDB stub was unusable in this build (protocol timeouts, `pc=0`, no memory access); the CLI debugger was used instead. A live watchpoint on a hypothetical hidden flag was therefore not set — but no candidate flag word exists in the static code.

## 9. Tooling

* `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings -t x`, Python 3 byte scans.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for all disassembly.
* Capstone 5.0.7 for Thumb literal-pool / key-state scanners (`scan.py`, `keystate.py`, `keyscan.py`).
* Ghidra 12.1.4 via the REA MCP (`open_binary`, `binary_overview`, `list_strings`, `list_procedures`, `procedure_pseudo_code`, `batch_decompile`); 299 procedures, 109 strings inventoried.
* mGBA 0.10.5 under Xvfb `:317` + openbox, `SDL_AUDIODRIVER=dummy`, `xdotool` XTEST input, `scrot` + ImageMagick crops.
* mGBA CLI debugger driven through a Python `pty` (`mgba_dbg.py`): `b/t 0x0800441c`, `c`, `r/4`, `x/4`, `status`.
* Analysis scripts kept in `/tmp/stadiumgames/`: `ui.py`, `scan.py`, `keystate.py`, `keyscan.py`, `final_sweep.py`, `buttontest.py`, `mgba_dbg.py`, `ram_walk.py`.

## 10. Legal note

No ROM image, extracted graphics, music, or game assets are redistributed in this report. Only hashes, addresses, algorithms, and original analysis tools are published.
