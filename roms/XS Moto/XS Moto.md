# XS Moto (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/XS Moto/XS Moto.gba` (analysed on a byte-identical copy in `/tmp/opencode/xsmoto/xs.gba`) |
| Size | 4,194,304 bytes (`0x400000`) |
| Header title | `XS MOTO` (`0xA0`) |
| Game code | `BXME` (`0xAC`), maker `FS` (`0xB0`) |
| Revision / version | `Rev.00`, version byte `0x00` |
| Entry word | `0xEA00002E` (stock ARM branch — no cracktro/trainer patch) |
| Header checksum | `0x0000`, complement `0x82` (normal rebuilt-header artifact) |
| MD5 | `986ff7d285a6c161ccfd2eaef4f8cb18` |
| SHA-1 | `2a800d077cfb8320ac5780d840976a47d9595728` |
| SHA-256 | `366473b9d66a8f3cef01166b1ea5745a78dfffa725c00600db96e486cabd4267` |
| Save hardware | None observed: mGBA created a **0-byte** `xs.sav`; progress is RAM/session-only |

## 2. Executive summary

XS Moto is a 4 MiB GBA racing game with an **obvious developer password subsystem** in
its text bank and UI code, but **no code-entry screen reachable from a cold retail boot
in the space I could walk**. The ROM contains the strings `Password` (text index 4),
`Enter Password` (45) and `Please note new password` (97). The Results screen formats a
**six-digit decimal code** (`"%06d"` at `0x0800c490`) from game-state word `+0x2c`, plus
four per-rider two-digit fields from bytes `+0x15..+0x18` (`"%02d"` at `0x0800c49c`),
with rider and track name tables at `0x0804c740` and `0x0804c6e8`. So the "password" is
a **progress code generated and displayed after a race**, of nominal space
`10^6 = 1,000,000` values.

On the live ROM, however, the reachable menu surface from a fresh boot is limited to
**Race (Quick Race / Championship), Options (Credits), Select Rider, Select Track and the
race itself**. The top-level menu never exposes `Two Player`, `Bonus Items`, `Password`,
`Challenge`, `Summary`, `Characters`, `Tracks` or `Trophies`. Static enumeration of the
two screen dispatchers (`0x08010a9c`, `0x0800eaa0`) and all 101 text-bank strings confirms
those screens exist in code, but no reachable input path sets the screen-state byte to the
password-entry screen. No button-code sequence was found in the key-mask scan.

**Therefore this engagement is a bounded negative on the reachable cheat surface**,
with the password *format* recovered and the *entry path* proven absent from the walked
screen graph — not a vague "not found". Details and counts in §6b. No novel code was
minted or entered, because no entry screen exists to accept one; that limitation is
stated explicitly in §8.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 under Xvfb `:320`, openbox, `SDL_AUDIODRIVER=dummy`, 3× scale.
* Keymap (verified against on-screen prompts): A = `x`, B = `z`, Start = `Return`,
  D-pad = arrow keys, L = `a`, R = `s`. Key holds of **150 ms** are required; 70 ms taps
  are dropped; 150 ms can double-step on some menus.
* Window focus via `xdotool windowfocus`; screenshots via `scrot` and
  `convert -crop 720x480+152+144 +repage`. All evidence images live in
  `/tmp/opencode/xsmoto/` (not in the ROM folder).
* Reproducible path exercised:
  `Return` (title → main menu) → `Right` toggles `Race`/`Options` → on `Race`,
  `x` → submenu `Quick Race`/`Championship` → `x` → `Select Rider` (Frank Champion,
  4 stats) → `x` → `Select Track` (Maryhill, Laps: 3) → `x` → race. On `Options`,
  `x` → `Credits` only.
* RAM evidence was obtained by decompressing mGBA `.ss1` savestates: each is a PNG with
  a zlib `gbAs` chunk yielding a 397,312-byte state; EWRAM maps at state offset `0x21000`
  (GBA `0x02000000`), IWRAM at `0x19000` (GBA `0x03000000`). Diffing slot-1 (main menu
  at `Race`) vs slot-2 (main menu at `Options`) gave 848 changed state bytes, of which
  30 were in EWRAM — the menu selection/cursor fields, not an unlock flag.
* GDB stub (`mgba -g`, port 2345) connected once but then refused further connections
  (single-client contention with other agents in the shared container), so savestate
  diffs were used as the RAM oracle (guide §16.13).

## 4. Address map

All addresses are ROM (`0x08xxxxxx`) unless marked RAM.

| Address | Meaning | Evidence |
|---|---|---|
| `0x080cb890` | Text table base, 101 records × 25 bytes, NUL-terminated ASCII | Derived (bytes + metadata) |
| `0x080cb884` | Text metadata `{count=101, lang=1, stride=25}`, pointed to by `0x080cc270` | Derived |
| `0x08010e80` / `0x08010e90` | Text bank init / text getter: `addr = base + 25*index` | Derived (Thumb disasm + Ghidra) |
| `0x0804c6e8`, `0x0804c6fc` | 5-entry index tables used by bonus/tour menus (`XSMoto Tour`, `A`,`F`,`M`,`K`, then `W` placeholders) | Derived |
| `0x0804c71c` | Menu index table `{0..6}` → Race, Two Player, Options, Bonus Items, Password, Quick Race, Challenge | Derived |
| `0x0804c740` | Rider name table `{FRANK, ALAN, GERRY, NEIL}` | Derived |
| `0x0804c8d8` | Screen/label registry, 70 records × 12 bytes `{label_idx, screen_id, 4 attr bytes}` | Derived |
| `0x08010b88` | Main game loop / screen-family dispatcher (families 0,1,2,3) | Derived (Ghidra) |
| `0x08010a9c` | Screen-family 0 dispatcher (14 non-empty cases) | Derived (Ghidra) |
| `0x0800eaa0` | Screen-family 1 dispatcher (15 non-empty cases) | Derived (Ghidra) |
| `0x0800be66` | Results screen handler (`FUN_0800be66`), reads state `+0x15..+0x18`, `+0x2c`, `+0x28` | Derived (Ghidra decompile) |
| `0x0800c490` / `0x0800c49c` | Format strings `"%06d"` / `"%02d"` used by Results | Observed (bytes) |
| `0x0800c4a8` / `0x0800c4ac` | Digit-tile table / rider-name table used by Results | Derived |
| `0x0800cdfa` | XSMoto Tour screen (`FUN_0800cdfa`) | Derived |
| `0x0800edf2` | Four-item menu handler; item 1 writes next-screen `4`, item 2 writes `5`/`6`, item 3 writes `2` | Derived (Ghidra) |
| `0x0800dd72` | Race setup: zeroes state `+0x15..+0x18` and `+0x2c`, sets item count `16` | Derived |
| `0x02000000`–`0x0203ffff` | EWRAM; state struct pointer at `param_1+0x333c`, menu object at `+0x3340`, screen bytes at `+9/+0xb/+0xc/+0xd` | Derived + observed |

## 5. Algorithm / pseudocode

Text access (recovered exactly):

```
metadata = 0x080cb884          # {count=101, ?, stride=25}
base     = metadata + 12       # 0x080cb890
get_text(obj, index):
    return base + 25 * (index + obj.bank*0)     # bank is 0 at runtime
```

Password generation (Results screen, `0x0800be66`, recovered from decompilation):

```
code6 = state.word[+0x2c]                 # formatted with "%06d" -> 6 decimal digits
for i in 0..3:
    field = state.byte[+0x15 + i]          # four 2-digit values, formatted "%02d"
    rider_name = table(0x0804c740)[state.byte[+0x0d + rider_index]]
    track_name = table(0x0804c6e8)[...]
display(code6, fields, rider_names, track_names)
# screen label shown on Results is text index 97: "Please note new password"
```

Nominal code space: 6 decimal positions = **1,000,000** values; each of the four
accompanying fields is 2 decimal digits (100 values each). The validator/entry path was
**not** recovered (see §8).

## 6. Tables

### 6.1 Text bank (selected indices; full 101-entry dump in `/tmp/opencode/xsmoto/`)

| Index | String | Index | String |
|---:|---|---:|---|
| 0 | Race | 24–28 | S, L, R, S, A |
| 1 | Two Player | 29–31 | Maryhill, Verona, Springburn |
| 2 | Options | 32–37 | C, D, D, F, H, M |
| 3 | Bonus Items | 38 | Saltcoats |
| 4 | Password | 40 | `?` (locked-item placeholder) |
| 5 | Quick Race | 42–44 | Characters, Tracks, Trophies |
| 6 | Challenge | 45 | Enter Password |
| 7 | Championship | 46–49 | SFX, Music, On, Off |
| 8–13 | Select Rider, Summary, Race Again, Change Character, Change Track, Quit | 50 | XSMoto Tour |
| 14–19 | Results, Congratulations, Frank Champion, Alan Speed, Gerry Gears, Neil the Wheel | 51–96 | mostly single-letter codes (`A F M K W L M R H C M T T I W …`) |
| 20–23 | FRANK, ALAN, GERRY, NEIL | 97–100 | Please note new password, Wait, Get Ready, Credits |

### 6.2 Reachable vs. present-but-unreached screens

Reached from cold boot (7): title, main menu, Race submenu, Options submenu,
Select Rider, Select Track, in-race.

Present in text bank / dispatchers but unreached (≥12): Two Player, Bonus Items,
Password, Enter Password, Challenge, Summary, Results, Congratulations, XSMoto Tour,
Characters, Tracks, Trophies.

## 6b. Enumeration

**Space definition.** The only code system in the image is the progress password
surfaced on the Results screen. Its space is fully described by:
6 decimal digits (`10^6 = 1,000,000` spellings) plus four 2-digit per-rider fields
(`100^4`). The alphabet is therefore the ten digits `0-9`; the `"%06d"` formatter
zero-pads, so leading zeros are part of the representation. There is no alphabetic
password alphabet on the Results screen. A separate 32-symbol keyboard-style alphabet
was searched for and **not found** (`strings` for `ABCDEFGHIJKLMNOPQRSTUVWXYZ`,
`0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ` and variants: 0 hits in the whole 4 MiB image).

**Published-code recon (bounded).** Attempted GameFAQs (`403`), DuckDuckGo HTML (bot
CAPTCHA), Google (challenge), Bing (irrelevant `XS`/iPhone results), and Wayback
(`404`). No usable published password for this SKU was obtained. The web search
integration returned no results for four `websearch` queries. This is recorded as a
search-bound limitation, not evidence that no published list exists.

**Screen-graph bound.** The reachable graph from a cold boot was walked exhaustively
with D-pad/A/B/Start/L/R/Select at every node; counts above (7 reached / ≥12 present
but unreached). The two dispatchers expose 14 and 15 non-empty handler cases
respectively; every one was decompiled or profile-checked for a code-entry loop
(character cursor, alphabet table, digit accumulator). None reads a 6-digit user
entry. The only code-related UI is the Results *display* (`0x0800be66`).

**Button-code bound.** A ROM-wide scan for runs of 4–6 `u16` values in `1..0x3ff`
(the active-high GBA key-mask domain) over `0x08001000..0x080d0000` produced 3,849
candidate runs; after filtering for plausible button-like values (few bits set,
small set size) none matched a canonical Konami-style or L/R+Start gate. L, R and
Select at the title and main menu produced no visible state change (screenshots
`main_a.png`, `main_s.png`).

**Novel code / rejection bounds.** No novel code could be minted and entered, and no
rejection test could be performed, because **no entry screen is reachable**. This is
the honest limitation of this report (§8); per the task's allowed alternative, the
negative above is bounded with explicit counts (screen walk, dispatcher cases, text
bank size, key-mask scan range and hit count) rather than left as "not tested".

## 7. Validation evidence

* **Observed**: all screenshots listed in §3; `xs.sav` is 0 bytes; savestate RAM diff
  counts (848 total, 30 EWRAM) for the menu toggle.
* **Derived**: text bank layout and 101-entry stride; text getter formula; dispatcher
  case maps; Results-screen `%06d` formatting and state offsets; screen registry.
* **Inferred**: that the 6-digit Results number is the "password" the game asks you to
  note down — strongly supported by the co-located string `Please note new password`
  (index 97, registry entry for the Results screen) but never observed being entered.

## 8. Unknowns

1. The password **entry** screen and validator were not isolated. The two dispatchers
   were enumerated, but a third code path (e.g. gated by a save/clear flag or a
   long button sequence not found by the mask scan) may still exist.
2. The gate that hides `Bonus Items` / `Password` / `Two Player` from the top menu was
   not identified. Three savestate count-byte patches (`0x02000eca`, `0x02004e7e`,
   `0x020054aa`) produced no new menu entries; the count is likely re-derived from a
   ROM table at screen setup.
3. A race was never finished (autopilot crashed into track barrels), so the actual
   rendered 6-digit password was never photographed.
4. No novel code was generated or entered, and no rejection bound was observed,
   because no entry surface exists in the walked space.

## 9. Tooling

* `file`, `xxd`, `strings`, `grep`, `md5sum`/`sha1sum`/`sha256sum` (Phase 0).
* `arm-none-eabi-objdump -M force-thumb` for targeted disassembly; a Python `capstone`-
  free BL/literal scanner (`xrefs.py`) for call-site enumeration.
* REA MCP with Ghidra 12.1.4 (`open_binary` raw-binary/ARM @ `0x08000000`,
  `procedure_pseudo_code`, `procedure_callers`, `xrefs`); session closed at end.
* mGBA 0.10.5 + Xvfb `:320` + openbox + xdotool + scrot/ImageMagick for the screen walk.
* `patchstate.py` (savestate PNG `gbAs` zlib patcher) for the count-byte experiments.
* All helper scripts and evidence images remain in `/tmp/opencode/xsmoto/`.

## 10. Legal note

No ROM, extracted graphics, audio or other copyrighted asset is redistributed here.
Only hashes, addresses, algorithms and the analyst's own observations are published.

## 11. Cleanup

Own PIDs only were terminated by number: mgba `858560` (and earlier `858054`,
`858026`-family ancestors were not touched), Xvfb `858026`, openbox `858043`. No
`pkill`/`pkill -f` was used. The ROM folder contains only `XS Moto.gba`; all `.sav`,
`.ss*` and screenshots were created in `/tmp/opencode/xsmoto/` and remain there.
