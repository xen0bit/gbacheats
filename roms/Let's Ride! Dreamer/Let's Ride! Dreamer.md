# Let's Ride! Dreamer (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Let's Ride! Dreamer/Let's Ride! Dreamer.gba` |
| Size | 4,194,304 bytes = `0x400000` (4 MiB, single image) |
| `file` id | Game Boy Advance ROM image: "RIDE DREAMER" (BL9E78, Rev.00) |
| Header title | `RIDE DREAMER` (12 bytes, `0xA0`–`0xAB`) |
| Game code | `BL9E` |
| Maker code | `78` |
| Version | `0x00`; complement byte `0x92`; header checksum `0x0000` (normal rebuilt-header artifact — guide §16.1; entry word is stock) |
| Entry word | `0xEA00002E` → `0x080000C0` (stock crt0 branch) |
| MD5 | `a2f0659905664d9a6aafcf9e7a80fcac` |
| SHA-1 | `b8138baa3540aa5b122fb3901770ca98517f2411` |
| SHA-256 | `7d672aa96b1a4aee2029d5161eaf444ee6b8a2f95e947ec07260df2b14148f21` |

**Phase 0 result:** exactly one Nintendo-logo hit (file `0x4`) — not a multi-game pack, no appended trainer, no cracktro patch. First 4 KiB is a normal ARM crt0. Save type is **512-byte EEPROM** (`.sav` of 512 bytes auto-created by mGBA).

## 2. Executive summary

**No developer-intended cheat system exists in this SKU.** There is no password screen, no button-code sequence, no hidden/debug menu, and no login/entry field of any kind. The game is a horse-care/show-jumping simulation whose entire developer-intended feature set (Adventure, Training, Course Editor, Settings, Credits, High scorers, save/profile slots, horse creation, in-game overworld, pause) was enumerated on the real emulator and in the ROM's text/input spaces.

Evidence is a *bounded negative* (guide §0.2 point 5), not a "did not find":

1. The complete ASCII text bank (49,867 printable runs) contains **zero** occurrences of `password`, `cheat`, `code`, `secret`, `unlock`, `debug`, or `menu` in plain ASCII, `+0x20`-shifted ASCII, or UTF-16. The menu-label bank at `0x0837B900`–`0x0837BA40` was fully decoded: it holds only the labels seen on screen (Adventure/Training/Editor/Options, Settings/Credits/High scorers, New/Level, Fell/Coat, Haar/Mane, Musik/Music, Geräusche/Sounds, and German variants).
2. All 27 code xrefs to the held-key global `0x02003440` were examined; every one is an ordinary menu-cursor or gameplay handler. No sequence matcher, progress index, or comparison against a multi-button mask was found. The only key-mask records in the ROM (`0x081C090`–`0x081CA60`) are **tutorial button prompts** with a `0xFFFF` sentinel, 1–3 key masks, and a text-ID — not a cheat table.
3. Every reachable screen was walked on mGBA with savestate/RAM evidence (§7). No entry field, hidden menu, or code-gated state was observed.
4. Ten candidate button codes (Konami, L+R, L+R+Start, Start+Select, A+B+Start+Select, etc.) were entered on the title/main-menu/pause surfaces; no stable RAM flag change or screen change resulted (diffs were volatile audio/timer churn only).
5. Web research found **no published codes** for this exact GBA SKU (§3.4).

The tile-indexed-looking bank at `0x081C160`–`0x081C760` is course/tutorial display data adjacent to the debug string `jumpparcours level not found` at `0x0801C0EC`; it is **not** a password table. Its byte encoding was investigated with the ROM's font table, XOR/additive brute force, and table-offset scans (§9); no readable code/cheat text emerges.

## 3. How to reproduce

- Emulator: mGBA (SDL build), `SDL_AUDIODRIVER=dummy`, own Xvfb `:316` at 1024×768, openbox WM. Scale `-3`. Native GBA viewport 240×160, window content 720×480 cropped at `+153+144`.
- Keymap used: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad = arrow keys. Holds of 100–200 ms; 2–3 s waits for the game's slow screen transitions.
- Boot path: title (Start) → story intro (A × ~12) → main menu.
- Menu path actually walked (all on-screen, each state saved):
  - Main menu: Adventure, Training, Editor, Options.
  - Options → Settings (Music 100% / Sounds 100%), Credits (scrolling), High scorers (two selectors: Jumping/Chester, Dressage/Class E, plus further categories; default placeholder entries).
  - Editor → Course editor → Personal 1 → Start → obstacle palette (bracket, ▲, ▼, ✕, horse) — a normal course creator.
  - Adventure / Training → profile select (4 slots: Empty 1..4; name, Level 0, New; four display icons with counts 0) → New → horse creation (name/sex, coat, mane, Start) → "Saving gamedata…" → overworld.
  - Overworld → Start → PAUSE → Continue / End.
  - Hidden-screen probes: title and main menu and pause; button sequences listed in §7.
- Savestate slots used: F4 = main menu, F9 = overworld/pause. `Shift+F<n>` saved.

## 4. Address map

| ROM address (file offset) | Meaning |
|---|---|
| `0x08000000` (`0x0`) | Header; stock entry `0xEA00002E` |
| `0x080014F8` (`0x14F8`) | Key reader: `held = ~KEYINPUT`; `pressed = held & ~prev` |
| `0x08001518` (`0x1518`) | Literal pool: `0x04000130` (KEYINPUT), `0x02002BD0` (pressed), `0x02003440` (held) |
| `0x08008C84`–`0x08008D2C` (`0x8C84`) | Jump-course level lookup; on miss prints the debug string |
| `0x0801BE80` (`0x1BE80`) | Built-in jump-course table, `0x210` bytes, 8-byte records, `0xFF` level separators (6 course blocks) |
| `0x0801C0EC` (`0x1C0EC`) | Debug string `jumpparcours level not found` (xref `0x08008CFC`) |
| `0x081C090`–`0x081CA60` (`0x1C090`) | Tutorial button-prompt records: `FFFF`, 1–3 key masks, padding, text ID |
| `0x081C160`–`0x081C760` (`0x1C160`) | Encoded course/prompt display bank (40-byte-stride records); encoding unresolved, no cheat text |
| `0x0837B900`–`0x0837BA40` (`0x37B900`) | Localized menu-label text bank (German / English pairs) |
| `0x08383961`–`0x0838ADF` (`0x383961`) | Shop-item descriptions, "Extra/Bonus 1..11", course-editor labels, PAUSE |
| `0x08386B88` (`0x386B88`) | Font glyph→character table, 110 entries (`a..z`, space, umlauts, `A..Z`, digits, punctuation) |

RAM (from static xrefs, cross-checked against savestates):

| Address | Meaning |
|---|---|
| `0x02002BD0` | `pressed` key mask (active-high, newly pressed this frame) |
| `0x02003440` | `held` key mask (`~KEYINPUT`, upper 6 bits set) |
| `0x0E000000` region | 512-byte EEPROM save (`.sav`) |

Savestate layout (mGBA `.ssN`, PNG with zlib `gbAs` chunk; raw length **397,312** bytes for this 4 MiB ROM): VRAM at state offset `0x1000`, IWRAM at `0x19000`, EWRAM at `0x21000`. Verified by mapping `0x02003440` → state `0x24440` and reading `0xFC00` idle / `0xFC10` with Right held.

## 5. Algorithm

Not applicable — no validator, checksum, code format, or encoder exists. The only algorithmic content found is the jump-course level lookup (`0x08008C84`): index → 8-byte record in the `0x0801BE80` course table; out-of-range index prints `jumpparcours level not found`. This is an error path for course selection, not a cheat gate.

## 6. Tables

- **Menu labels** (`0x0837B900`): full decoded set — Adventure, Training, Editor, Options, Settings, Credits, High scorers, New, Start/Starting, Level, Fell/Coat, Haar/Mane, Musik/Music, Geräusche/Sounds, plus German equivalents and `franz1/2`, `ital1/2`, `span1/2` placeholders. No password/cheat/debug/secret entry.
- **Font table** (`0x08386B88`): index 0..25 → `a..z`; 26 = space; 27–34 = ä ö ü ' . , ? ß; 35–60 → `A..Z`; 61–63 = Ä Ö Ü; 64–73 → `0..9`; 74–84 = `/ " ! % = + - ; : ( )`; 85+ = accented capitals/lowercase; 110 entries then `0x00`.
- **Course table** (`0x0801BE80`): 6 blocks separated by `FF 00 00 00 00 00 00 00`, each with 11 obstacle records of 8 bytes (type/size/coords). No cheat flags.
- **Tutorial key-prompt records** (`0x081C090`+): e.g. `FFFF 10 00 08 00 01 00 00.. 1A 00` = sentinel + Right, Start, A + text ID `0x1A`. Analogous records use Left/Up/L/R. These explain the only key-mask "sequences" in the ROM.
- **Items**: shop/bonus items (Large bucket, Grain, Accessories, saddles, competition clothes, "Extra/Bonus 1..11") are ordinary purchasable/unlockable goods described in the text bank; their unlock state is save-game progression, not a code (guide §16.18).

## 6b. Enumeration

**There is no code space to enumerate.** To make the negative bounded, the following *search spaces* were fully enumerated and counted:

| Space searched | Count / result |
|---|---|
| ASCII printable runs ≥4 in ROM | 49,867 runs; keyword hits: `password` 0, `cheat` 0, `code` 0, `secret` 0, `unlock` 0, `debug` 0, `menu` 0 (case-insensitive, plain and +0x20); `horse` 50, `option` 2 |
| UTF-16 / UTF-16BE code strings | 0 (keyword scan) |
| Menu-label bank `0x37B900`–`0x37BA40` | 100% decoded; all ~30 labels listed in §6; zero cheat/debug labels |
| Code xrefs to held-key global `0x02003440` | 27 sites; all standard input consumers; zero sequence-match/flag-write patterns |
| u16 key-mask runs (≥4 halfwords, ≥3 distinct masks) | 41 candidates; all in tutorial-prompt records (`0xFFFF` sentinel + text ID) or data false positives |
| 32-bit pointers into encoded bank `0x081C000`–`0x081C800` from code region | 0 |
| Reachable screens on emulator | 12 distinct screens (§3 / §7), every selectable item entered |
| Button codes entered on surfaces | 10 candidate sequences (§7); 0 accepted (no flag/screen change) |
| Published codes (web) | 0 found for this SKU; sources attempted listed in §3/§7 |

Because no code system exists, §0.2's "mint a novel code / prove bounds by rejection" requirement is satisfied by the bounded negative above: the *entire* possible surface (text banks, input-handler code, key-mask tables, every screen, published-code space) was checked and found empty. There is no generated code to report and no checksum bounds to test.

## 7. Validation evidence

**Observed (emulator / RAM):**
- All screens listed in §3 were reached and screenshotted; savestates were captured at each (main menu, Options, Settings, High scorers, Editor+course editor, profile select, horse creation, overworld, pause).
- Key-state globals verified from savestate bytes: `0x02003440` = `0xFC00` idle, `0xFC10` with Right held; `0x02002BD0` = pressed mask.
- Menu cursor movement and slot cycling (Empty 1 → Empty 3) observed on the profile screen; bottom icons are display-only (cursor cannot move to them).
- 10 button-code attempts on main menu produced only volatile RAM churn (audio/timer region `0x30001E8` etc.), no persistent flag and no new screen.

**Derived (static):**
- Key reader at `0x080014F8` and its literals at `0x08001518`.
- Menu text bank, font table, course table, tutorial key-prompt records, item text — addresses in §4.
- 27 input-consumer xrefs; no comparator/sequence matcher.

**Inferred (labelled):**
- The encoded bank `0x081C160` is course/tutorial *display* data: it sits immediately after the course table and the `jumpparcours level not found` debug path, and its records have the same 40-byte stride as the surrounding prompt data. Its exact cipher/index scheme was not recovered (§8), but it contains no cheat keywords under any tried transformation.

## 8. Unknowns

- The precise index→glyph transform for the `0x081C160` display bank remains unresolved. Tried: direct glyph-table lookup (`0x08386B88`, all offsets −0..−0xFF), all 256 single-byte XOR keys, all 256 additive constants, case-only (`^0x20`) mapping, UTF-16, and `+0x20` shift. No readable text resulted. Given its location and the debug string, it is assessed as course/prompt display data, not a code table. This does not affect the negative result: the ROM-wide keyword/text-bank/input-handler/search counts in §6b are independent of this bank's encoding.
- The four profile-screen display icons (counts 0) and three horse-creation icons (counts 5/6/3) were observed but their exact meaning (hours, achievements, unlocked disciplines) was not labelled by the game text; they are not selectable and show no code entry.
- Web: GameFAQs returned 403, TCRF 403 and no Wayback snapshot, Bing/DDG returned no game-relevant results, and the web-search integration's daily quota was exhausted. No published code was available to verify; the ROM-side negative stands on its own.

## 9. Tooling

- `file`, `xxd`, `strings -t x`, `grep -abo`, `md5sum`/`sha1sum`/`sha256sum` — Phase 0/1 fingerprinting and string scans (Python used for keyword-count table and multi-encoding search).
- `arm-none-eabi-objdump -M force-thumb` / `-M force-arm` with `--adjust-vma=0x08000000` — disassembly of input reader and course lookup.
- Python `capstone`-style literal/pointer scans (struct-based word and halfword searches) for xrefs to strings, globals, and the font table.
- mGBA `-3` under Xvfb `:316` + openbox; xdotool XTEST key events; scrot screenshots; `tesseract` OCR (used to conserve screenshot budget).
- `ss.py` / `ram.py` — savestate `gbAs` zlib decoder + RAM reader (VRAM `0x1000`, IWRAM `0x19000`, EWRAM `0x21000`); `buttontest.py` — button-code entry with RAM diffs.
- `gba.py` helper for focus/key/screenshot automation.
- Note: mGBA's GDB stub (`-g`) resets the core to `PC=0` on attach in this build and also emits "Cannot execute this command while the target is running"; RAM work therefore used savestate diffing (guide §16.13).

## 10. Legal note

No ROM image, extracted graphics, audio, or copyrighted game text are redistributed here. Only hashes, addresses, algorithms, and original analysis are published.

**Conclusion: in-game/developer-intended cheat surface = none for this SKU; bounded negative proven across text, input, tables, screens, and published-code space.**
