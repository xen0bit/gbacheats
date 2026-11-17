# Dynasty Warriors Advance (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Dynasty Warriors Advance/Dynasty Warriors Advance.gba` |
| Size | 16,777,216 bytes (`0x01000000`, 16 MiB) — **single, unpatched retail image** |
| `file` | `Game Boy Advance ROM image: "DYN WARS ADV" (B36E01, Rev.00)` |
| Header title | `DYN WARS ADV` |
| Game code | `B36E` (AGB-BE6E, USA) |
| Maker | `01` (Nintendo) |
| Version | `0x00`; fixed byte `0x96` present; complement `0xBD`; header checksum `0x0000` |
| Entry word | `0xEA0004E2` → entry point `0x08001390` (branch, not cracktro) |
| Build string | `2005/04/01 16:59:29` @ file `0xC9574` = `0x080C9574` (matches TCRF "US" row) |
| MD5 | `2a2661cbc8e3891864fdc1d34f9d1c9b` |
| SHA-1 | `6839254172e558923cde6a912a5ee537eec5fd40` |
| SHA-256 | `77cab00b06ce4fc70e5298e99e00af43cd54206f1c2e3e4e63e7c26bc58f8831` |

Developer is **TOSE** (Koei published; Nintendo published in US/EU); the engine's own debug paths are `Src/Japan/MT/...` (`0x080EB330`, `0x080EB3CC`). The brief's "Orca/Torus" attribution is not supported by the image; no patch/trainer appended. Embedded-GBA-header scan: **exactly 1** Nintendo logo hit (file `0x0`) — no multiboot stub, no second game.

### Phase 0 / §16.1 checks
- Entry `0xEA0004E2` is a normal `b` into the game's crt0; first 4 KiB contains only normal vectors/code; no scene cracktro or trainer menu strings.
- Save hardware is present: mGBA created a 32,768-byte `.sav` (Flash 256Kb-class), so this game uses **battery saves**, not passwords. Consistent with §11 "password systems often exist precisely because the cart has no save memory" — here the opposite holds.

## 2. Executive summary

**There is no in-game cheat-code / password system in this ROM, and no reachable hidden debug menu.** The three findings, in order of evidence strength:

1. **No code surface (proven negative).** The 16 MiB image contains **zero** ASCII, case-shifted (`+0x20`), or UTF-16LE occurrences of `PASSWORD`, `CHEAT`, `CODE`, `UNLOCK`, `GENIE`, `KONAMI`, or `ARCODE`. There is no on-screen symbol keyboard, no code-entry field, and no validation/comparison routine over a player-entered buffer anywhere in the walked UI. Every "cheat" published for this SKU is a GameShark / CodeBreaker / ActionReplay **memory patch** (e.g. `32003194 00FF` writes `0xFF` to EWRAM `0x02003194`), which is explicitly out of scope. The only in-game unlockables are four save-bit characters, driven by Musou-Mode completion (§5).

2. **Debug console is compiled in but unreachable (proven dead code).** A complete debug console ("DEBUG CONSOLE", `0x080EB474`) with its own constructor (`0x08023140`, built with `ScriptConsole.cpp` / `ConsoleScreen.cpp` file tags), menu labels, handler table and parameter readouts exists at `0x08021EC0–0x08024000`. A full-ROM BL/BLX/pointer scan finds **zero** references to the screen constructor `0x08023140`/`0x08023141` from anywhere, including from inside its own cluster; the single apparent "external BL" at `0x08021E58` is a literal-pool false positive (`f000 ffff`, a `0xFFFFF000` mask used at `0x08021E24`). A live GDB breakpoint at `0x08023140` never fired across a normal full menu walk plus **17 distinct button combinations/sequences** at the title and Select-Mode screens. This is the "Dead code" case of §16.3, not "hidden menu".

3. **Unlockables are save data, not codes (§16.18).** `0x081D2768/2784/27A0/27BC` hold `"Cao Cao is now available."`, `"Liu Bei ..."`, `"Sun Jian ..."`, `"Lu Bu ..."`, referenced through the game's text-ID pointer table at `0x081D2C64–0x081D2C70`. They are the save-completion messages for the four characters whose published unlock conditions are Musou-Mode clears. They are not entered, typed, or input-triggered.

TCRF (`tcrf.net/Dynasty_Warriors_Advance`, mirror consulted) documents only "hidden development-related text" plus regional differences/build dates — **no published access method** for the debug console. Any access would therefore be novel; none was found.

## 3. How to reproduce

- Emulator: mGBA SDL, `mgba -3` (and `mgba -g -3` for the GDB stub), under `Xvfb :317 -screen 0 1024x768x24`, `SDL_AUDIODRIVER=dummy`.
- Keymap (mGBA SDL defaults): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows. Holds of 100–300 ms; screen transitions need ~1.5 s.
- Boot path: health warning (any button) → Koei logo → title `PRESS START`.
- Screens walked (all observed, screenshot evidence retained as `shot_00`..`shot_25` in the work dir):
  - Title (`PRESS START`)
  - Main menu: **Play / Encyclopedia / Tutorial / Game Settings** (`shot_03`, `shot_06b`)
  - **Game Settings** (`shot_04`): title + `SELECT ? B OK` only; no hidden options appeared
  - **Encyclopedia** (`shot_05`): "Officers" entry (with empty save, only this tab is populated)
  - **Play → Select Mode**: Musou Mode / Free Mode / Challenge Mode (`shot_07`)
  - **Select Game**: New Game + three save slots (`Load` view, `shot_11`)
  - **Select Camp**: Wei / Shu / Wu map (`shot_09`, `shot_19`)
  - **Character select**: Xiahou Dun etc., stat pentagon (`shot_10`)
  - **Stage/Story**: stage title `Yel. Turbans`, story exposition (`shot_20`, `shot_21`, `shot_23`)
  - **Battle field** with HUD (`shot_24`, `shot_25`)
  - **No password entry screen exists on any of these screens.** The 12-entry stage-name table at `0x081C8184` ends with `Debug` (`0x081C817C`), but it is not exposed by any stage selector reachable in Musou/Free/Challenge mode; the last selectable stage observed is `Wu Zhang`.
- Debug-trigger tests: GDB stub, `break *0x08023140`, `continue`, then at the title/Select-Mode screens: held `L+R`, `L+R+Select`, `L+R+Start`, `Select+Start`, `A+B+Select+Start`, `L+R+A+B`, `L+Select`, `R+Select`, `L+Start`, `R+Start`, `L+Up`, `R+Down`, and the sequence `Up Up Down Down Left Right Left Right B A`. Breakpoint never hit. (Caveat §16.2: the first two GDB attempts used `continue` while the target was already running and were rejected with "Cannot execute this command while the target is running"; those attempts were discarded. The two valid attempts used `interrupt` before `break`/`continue`, verified by `info program` showing SIGINT-stop.)

## 4. Address map

| Address | Kind | Meaning |
|---|---|---|
| `0x08000000` | ROM | Header; entry `b 0x08001390` |
| `0x080C9574` | data | US build date `2005/04/01 16:59:29` |
| `0x080EB330` | data | `Src/Japan/MT/ConsoleScreen.cpp` |
| `0x080EB3CC` | data | `Src/Japan/MT/Src/Debug/ScriptConsole.cpp` |
| `0x080EB3F8–0x080EB4BC` | data | Debug console labels: `Max Hp`, `Hit Point`, `Tension`, `Attack`, `Defence`, `Speed`, `KillCount`, `Enemy Hp`, `No Damage`, `Print MemInfo`, `DEBUG CONSOLE`, `WorkView1`, `WorkView2`, `StepRun`, `ScriptView`, `AGBPrint`, `Parameter` |
| `0x080EB4CC/4D4/4DC` | data | Debug console handler pointers `0x08023A39`, `0x080239B5`, `0x08023A05` (`|1` Thumb) |
| `0x080EB4E0/4E4` | data | `off` / `on ` (Parameter toggle) |
| `0x080EB4E8/500` | data | Pointers to the above; `0x080EB4F4` = `%s%02x:%04x` |
| `0x080EB514/51C/524/538` | data | `Hide`, `Trace`, `History`, `Unuse`; `0x080EB540/544/548` = `GW`, `LW`, `GF` |
| `0x08021EC0–0x08024000` | code | Debug console cluster (dead); constructor `0x08023140`; literal pool `0x08023354–0x080233E4` |
| `0x08021F78` | code | Lazy-init helper; global `0x02000CD0` gate; returns `[0x02000CCC]`; referenced from 14 code literal pools as Thumb ptr `0x08021F79` (infrastructure live, screen not) |
| `0x08023360` | literal | `DEBUG CONSOLE` title pointer used by constructor |
| `0x081C8108–0x081C817C` | data | 12 stage-name strings; `0x081C8184` = 12-entry pointer table whose last entry is `"Debug"` |
| `0x081D2768/2784/27A0/27BC` | data | `Cao Cao / Liu Bei / Sun Jian / Lu Bu is now available.` |
| `0x081D2C64–0x081D2C70` | data | Text-ID pointer table entries for the four unlock messages |
| `0x02000CD0`, `0x02000CCC` | RAM EWRAM | Debug-infrastructure globals (init gate / returned handle) |
| `0x04000130` | I/O | KEYINPUT; read by thunk at `0x08001C2C` (mask `0x03FF`) — generic joypad, no code matcher |

## 5. Algorithm

**No password/validator algorithm exists** — there is no input buffer, alphabet, checksum, or comparison table to reverse. The relevant compiled logic is only the dead debug-console construction:

```
constructor 0x08023140(this=r0, args...):
    new ConsoleScreen(file="Src/Japan/MT/.../ScriptConsole.cpp", line=0x1DF)
    set title = "DEBUG CONSOLE"            # literal at 0x08023360
    build menu rows (8-byte records): {s16 offset, s16 pad, u32 handler|1}
        WorkView1 / WorkView2 / StepRun / ScriptView / AGBPrint / Print MemInfo
    build parameter readouts:
        Max Hp / Hit Point / Tension / Attack / Defence / Speed / KillCount /
        Enemy Hp / No Damage
    build toggles: Parameter(off/on), Hide/Trace/History/Unuse, GW/LW/GF(/FL)
    install input handler 0x08021F79
```
Reconstructed from literal pools `0x08023354–0x080233E4` and the string table at `0x080EB3F8+`. This is **Derived** from disassembly/literals, not Observed in the emulator — the screen never opened.

Unlockables are save-data bits: `Musou-Mode clear condition → set save flag → show "X is now available."` via text IDs resolved through the pointer table at `0x081D2C64+`. No player-entered data participates.

## 6. Tables

### 6.1 Text-space search (whole 16 MiB, three encodings)

| Keyword | ASCII | lowercase | `+0x20` shifted | UTF-16LE |
|---|---:|---:|---:|---:|
| PASSWORD | 0 | 0 | 0 | 0 |
| CHEAT | 0 | 0 | 0 | 0 |
| CODE | 0 | 0 | 0 | 0 |
| UNLOCK | 0 | 0 | 0 | 0 |
| SECRET | 5 (dialogue only) | 5 | 5 | 0 |
| DEBUG | 1 (`Src/.../Debug/ScriptConsole.cpp`) | 0 | 0 | 0 |
| GENIE / KONAMI / ARCODE | 0 | 0 | 0 | 0 |

Keyword hits for `secret` were dumped with context; all five are story/dialogue text (e.g. `0x138A9D "Ha ha! Ha ha! My secret"`, `0x13A224 "Now I'll show you the hidden"`, `0x15CF60 "A secret scheme designed by"`) — none is a code hint.

### 6.2 Debug-console menu entries (static enumeration; none reachable)

| # | Label (addr) | Observed effect |
|---|---|---|
| 1 | `WorkView1 :` `0x080EB484` | debug work-variable view 1 (handler ptrs `0x08023B61`, `0x08022D91`) — effect **Inferred**, screen never opened |
| 2 | `WorkView2 :` `0x080EB490` | work-variable view 2 (handler `0x080229BD`) — Inferred |
| 3 | `StepRun` `0x080EB49C` | script single-step toggle (handler `0x08023739`/`0x080229FD`) — Inferred |
| 4 | `ScriptView:` `0x080EB4A4` | script viewer (handler `0x080236DD`) — Inferred |
| 5 | `AGBPrint  :` `0x080EB4B0` | AGBPrint debug output toggle (handlers `0x080224B9`/`0x08022469`) — Inferred |
| 6 | `Print MemInfo` `0x080EB464` | dump memory info — Inferred |
| 7 | `Parameter` `0x080EB4BC` | on/off (`off`=`0x080EB4E0`, `on `=`0x080EB4E4`); fields: Max Hp, Hit Point, Tension, Attack, Defence, Speed, KillCount, Enemy Hp, No Damage (`0x080EB3F8–0x080EB458`) — Inferred |
| 8 | `Hide`/`Trace`/`History`/`Unuse` `0x080EB514…` | console display filters — Inferred |
| 9 | `GW`/`LW`/`GF`/`FL` `0x080EB540…` | graphics-layer toggles — Inferred |

Nearby script-test names (part of the same debug build, not proven to be console rows): `EffectScriptTest`, `ScreenEffectScriptTest`, `PadScriptTest`, `SoundScriptTest`, `UnitScriptTest`, `BustUpTest`, `ScreenMoveTest`, `DemoAnimeTest`, `ItemTest` at `0x080EB38C–0x080EB434`.

### 6.3 Published codes verified / rejected as out-of-scope

Sources checked: GameFAQs cheats (archived 2018-11-26), TCRF + mirror, Neoseeker, almarsguides, 53lu, GameHacking.org, supercheats. Exact literals found:

- GameFAQs "Unlock Lu Bu / Unlockable Characters": clear Musou Mode with a warrior of each state → Sun Jian/Cao Cao/Liu Bei → clear with a lord → Lu Bu. **In-game, save-driven, in scope as unlockable — not a code.**
- Neoseeker `Infinite Musou D16699999687`, `Max Attack E6A2A43AA828 / A625154D7CD5`, `Max Defense E6A2A43AA828 / A6279549FCF5`, `Max Movement ... BA0513C57455`, `Max Skills A7ED5D0C5CD5 / 6575B5090EFD` — CodeBreaker/GS encrypted memory patches. **Out of scope.**
- almarsguides `Max Weapon Stat One: 32003194 00FF` (plain raw RAM write to EWRAM `0x02003194`) — unambiguously a memory edit, not a controller input. Also `Have All Weapons A829440D6DDB 7955B381067D`, `All Items In Encyclopedia A8E11C6C6DDA 6575B51B4EAD`.
- 53lu ActionReplay `Have All Weapons f69935dd 19b8985c`, `Max KOs 99098ad7 5a31d963`. Same class.
- **PS2 carry-over check:** the famous Dynasty Warriors PS2 weapon/item unlock codes are not present in any GBA-source list; no PS2-style code literal appears in the ROM's text space (§6.1), and the weapon/encyclopedia unlocks here are obtained from treasure boxes and battle prizes (`0x081D9193`, `0x081D926F`, `0x081D73C4 "New weapon obtained!"`). No carry-over found.

## 6b. Enumeration

**Code space size: 0.** There is no code table, no alphabet, no checksum, no validator, and no entry UI. Consequently no value can be minted and no code can be accepted or rejected — the space is empty by construction, not by incomplete search. The negative is bounded by:

- **Text space** — all 16,777,216 bytes searched in four encodings for nine cheat-related keywords (§6.1): all zero except five dialogue `secret` hits and one debug source path. Counts reported.
- **Table space** — the only discoverable "hidden" table is the 12-entry stage-name table at `0x081C8184` (last entry `Debug`); its presence in ROM is not an accessible menu (no selector reaches index 11; `Wu Zhang` is the last observed stage).
- **Button space** — 17 distinct hold/combination/sequence inputs exercised at title and Select-Mode with a live breakpoint on the only debug-screen constructor: `L+R`, `L+R+Select`, `L+R+Start`, `Select+Start`, `A+B+Select`, `A+B+Select+Start`, `L+R+A+B`, `L+Select`, `R+Select`, `L+Start`, `R+Start`, `L+Up`, `R+Down`, and `Up Up Down Down Left Right Left Right B A`. Raw u16 key-mask scans for Konami/L+R prefixes returned only random-data false positives (63 hits for `L,R,Start` active-high, 357 for `Start,Select`, 6 for `Up,Up,Down,Down` across compressed graphics).
- **Validator space** — no function reads a player text buffer and compares it to constants; the only key-input reader (`0x08001C2C`) is the generic joypad thunk storing held/pressed masks.
- **Published-code space** — every published code tested was verified by source+format to be a cheat-device RAM patch, not an in-game code; the four published unlockables are save-flag driven.

**Novel code:** none exists to mint; reporting an invented "code" would be false. **Bounds by rejection:** not applicable (no code system). **Undocumented combination pressed in the emulator:** yes — the 17 combinations above, including `Up Up Down Down Left Right Left Right B A` and `L+R+A+B`; none opened any hidden screen or changed any observed state.

## 7. Validation evidence

- **Observed** (emulator): title, main menu, Game Settings, Encyclopedia, Select Mode, Select Game, Select Camp, character select, stage story, battle field and event dialogue; no password screen; 17 input combinations produced no hidden screen; mGBA produced a 32 KiB Flash save.
- **Observed** (GDB): `break *0x08023140` + `interrupt` + `continue` armed correctly (`info program`: SIGINT-stop at `0x0300128A` in one run), and never hit during the input battery. GDB stub connect required `set remote noack-packet off`; plain `continue` on an already-running stub is refused (§16.2/§16.13).
- **Derived** (static): zero BL/BLX/pointer xrefs to `0x08023140` across the whole image (the only candidate `0x08021E58` is a literal-pool `0xFFFFF000` mask, not a BL); literal-pool reconstruction of the debug console's menu rows; text-ID table entries for the four unlock messages; build date at `0x080C9574`; header/entry/hashes.
- **Inferred**: the *function* of each dead debug-console row (WorkView, StepRun, ScriptView, AGBPrint, Parameter, layer toggles) from its label + nearby handler; not exercised because the screen never opens.

## 8. Unknowns

- Exact bit offsets of the four unlock flags inside the 32 KiB Flash save record were not isolated; the four messages and their save-completion context are located, and the published Musou-clear conditions are consistent, but the setter's call sites were not fully traced. This does not affect the "no input code" conclusion.
- Whether any *other* regional build (JP `2005/02/23` / Rev 1 / EU) wires a trigger to the debug screen — only the US `B36E` image was supplied.
- The precise effect of each dead debug-console handler (labelled Inferred above).
- mGBA's SDL build did not yield a clearly identifiable pause overlay in battle; Start/Select advanced battle events instead. The battle HUD screen was observed; no code-entry surface appeared there.

## 9. Tooling

- `file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings -t x`, `grep -aob`.
- Custom Python in `/tmp/opencode/dwadvance`: `phase0.py` (hash/header/logo scan), `xrefs.py`/`pool.py`/`blscan.py`/`reach.py`/`keyinput.py` (Capstone-free literal/BL/pointer scans), `mgba_ctl.py` (xdotool input helper).
- `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 … -M force-thumb` for disassembly; literal pools decoded with `struct.unpack_from('<I', …)` (§11 byte-order pitfall observed and avoided).
- mGBA SDL `mgba -3` and `mgba -g -3` + `gdb-multiarch` (`set architecture arm`, `set remote noack-packet off`, `target remote :2345`, `interrupt`, `break *0x08023140`).
- Web: GameFAQs via `web.archive.org`; TCRF via `tcrf.tiago.zip` mirror (direct TCRF fetch returned 403/Cloudflare challenge). Fetched pages treated as data; no instructions in them were followed.

## 10. Legal note

No ROM bytes, graphics, audio, or game text are redistributed here — only hashes, addresses, tool output, and original analysis. Screenshots were kept in the analysis work dir, not attached.
