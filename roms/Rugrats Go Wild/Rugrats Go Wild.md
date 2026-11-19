# Rugrats Go Wild (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Rugrats Go Wild.gba` (4,194,304 bytes = 0x400000) |
| Header title | `RUGRATSGWILD` |
| Game code | `A5WE78` (serial A5WE, USA/Europe) |
| Maker | `78` (THQ) |
| Version | `0x00` |
| Fixed byte | `0x96` (present) |
| Header checksum | `0x0000`; complement byte `0x31` (edited header — see below) |
| Entry word | `0xEA0F962C` → `b 0x083E58B8` (NOT stock) |
| MD5 | `2af24c5320e1a82eb1edcea0480c13e4` |
| SHA-1 | `c1f197329da26ddf8216fad8b51019d436a8358f` |
| SHA-256 | `88925563f04d59f9093955eb5b932ea52e3b03838c217dfa0ec9d29cdca47b5c` |

**Patch / trainer finding (Phase 0, §16.1):** the shipped image is a **VENOM scene release**, not the
retail image. The header entry branch was patched from stock `0xEA00002E`
(`b 0x080000C0`) to `0xEA0F962C`, redirecting to a custom crt0 at `0x083E58B8` that
draws a "VENOM PRESENTS / RUGATS GO WILD! (C) THE VENOM" splash and then hands
control back to the stock crt0 (`0x080000C0`). The stock crt0, Nintendo logo
(single hit at file offset `0x4`), game code and the full text bank are intact.
A **copy** with the entry word restored to `0xEA00002E` was used for all dynamic
work (`game_stock.gba`, SHA-256 `25de82874d9726b0719b080d187a9a50e24acd0713179e343739a2fac3ee3b0e`).
The VENOM splash is a cracktro, **not** an in-game cheat; no trainer menu is present.

The ROM is **not** compressed at rest (single GBA header; high-entropy regions are
graphics/audio). The patched crt0 at `0x083E58B8` contains an RNC-style decompressor
that copies a blob at `0x083E5CAC` to EWRAM `0x02000000` and branches to `0x020000C0`;
this is the cracktro's graphics loader, not the game code path.

## 2. Executive summary

The game contains a **developer-intended 5-letter password system** (level skip /
progress codes) — confirmed by in-game text (`Enter Password`, `New Password`),
a generated 5-letter password shown on the pause menu (`CFHDM` observed), and nine
published codes from GameFAQs, SuperCheats, ChapterCheats and Great Games Wiki.
The accepted codes are **not stored as plaintext or trivially encoded literals** in
the ROM: literal searches for every published code, all 25 Caesar shifts, lowercase,
reversed, A=0 byte values and 5-bit packings all returned no hit. The system is
therefore algorithmic (computed validator), consistent with games of this era.

The entire UI was enumerated with screenshots: title/attract, Main Menu
(New Game / Continue / Options / Credits), Options (Music / SFX / Controls),
the intro cutscene, the in-game pause menu (which displays the current password
and the current objective), and the "Play as Tommy / Play as Eliza" character-select
menu definitions (text IDs 184/185). Fourteen named levels/minigames exist.

**Status of the validator:** the comparison routine itself was **not recovered** to
the point of minting a novel accepted code. The input surface, the full text bank,
the menu/script data and the published accepted set are characterised below; the
algorithm and its checksum are recorded as an explicit unknown (§8) rather than
guessed. This is a bounded negative on the *search paths actually executed*, not a
claim that no password system exists — it demonstrably does.

## 3. How to reproduce

* Emulator: mGBA (`mgba -3`) and VisualBoyAdvance 1.8.0 under `Xvfb :316`,
  `SDL_AUDIODRIVER=dummy`. mGBA SDL keymap used here: A = `z`? — see note below;
  Start = `Return`, D-pad = arrows, B = `x`/`z` (verify per emulator).
  **Note:** the two emulators use opposite A/B assignments in this harness;
  confirm on the visible "OK (A)" prompt before each menu action.
* Boot `game_stock.gba` (stock entry word restored on a copy). The unmodified
  release boots the VENOM cracktro first.
* Path used (all screenshots in `/tmp/opencode/rugratswild/`):
  1. Nick Games splash → Klasky Csupo splash → title ("Press START") — `stock_c.png`, `t2c.png`.
  2. Start → Main Menu — `mm0c.png`.
  3. Down → Options (Continue is disabled with no save) → A — `fr4c.png`, `fr5c.png`.
     Options contains only **Music** (On/Off), **SFX** (On/Off) and an informational
     **Controls** row; B/Select = Back — `fr6c.png`, `fr7c.png`.
  4. Main Menu → New Game → long cutscene (advance with A) → gameplay — `cut3c.png`.
  5. Start in gameplay → Pause menu: title `Pause`, the current password `CFHDM`,
     the current objective `Find Chuckie`, then `Options`, `Quit` — `pz2c.png`, `q6c.png`.
  6. Quit → Yes → title; Continue → "Developed by ImaginEngine" / credits cutscene — `q10c.png`, `q11c.png`.
* Headless timing: a live idle timer returns the title/menu to attract mode after
  ~10–15 s of no input, so all multi-step navigation must run in a single script.

## 4. Address map

All addresses below are **ROM addresses** (`file offset = address − 0x08000000`).

| Address (ROM) | Meaning | Evidence |
|---|---|---|
| `0x08000000` | Patched entry `b 0x083E58B8` (stock `0xEA00002E`) | Observed bytes + boot |
| `0x080000C0` | Stock ARM crt0 (restored copy boots the real game) | Observed |
| `0x083E58B8` | VENOM crt0 / RNC-style loader (cracktro only) | Derived (ARM disasm) |
| `0x083E5CAC` | RNC-packed cracktro graphics blob (`RNC\x02`) | Observed bytes |
| `0x0803A000`–`0x0803C910` | Plaintext English text bank (credits, objectives, menus) | Observed strings |
| `0x08043B88` | 235-entry text pointer table (`u32` per ID) | Observed pointers |
| `0x08043E60` | Text ID 182 = `Enter Password` | Observed |
| `0x08043E64` | Text ID 183 = `New Password` | Observed |
| `0x08043E68` / `0x08043E6C` | IDs 184/185 = `Play as Eliza` / `Play as Tommy` | Observed |
| `0x08043E70`–`0x08043E74` | IDs 186/187 = `Quit?` / `Pause` | Observed |
| `0x08043F34` | 24-byte-stride, 43-entry game/entity table read by `0x08005C70` | Derived (disasm) |
| `0x08200F64` | Script data: adjacent IDs 182/183 (`Enter/New Password`) | Observed data |
| `0x08200FB4`–`0x08200FC6` | Script data: repeated IDs 184/185/186 (character select / Quit) | Observed data |
| `0x0803C87C` | C-library charset `-_,./` | Observed strings |
| `0x0803C884` / `0x0803C8AC` | C-library charsets `0-9a-z` / `0-9A-Z` | Observed strings |
| `0x0804BFF4`–`0x0804C008` | C-library charset pointer array (includes the above) | Observed pointers |

No password code table or validator address was confirmed by an xref, so none is
claimed. Ghidra auto-analysis of this raw image is unreliable at the candidate
sites (functions merged / not created), which is why manual `objdump -M force-thumb`
and byte scans were used.

## 5. Algorithm

**Confirmed structure:**

* Input: five uppercase ASCII letters (`[A-Z]{5}`). All nine published codes and the
  in-game generated code `CFHDM` are exactly five uppercase letters.
* The game **generates** a password from current progress and displays it in the
  pause menu (`CFHDM` at the start of a New Game). This proves a computed encoder
  exists (guide §0.2: a generator beside a validator implies an algorithmic space,
  not a fixed table).
* The codes are **not literal**: exhaustive literal/Caesar/reversal/byte/5-bit-pack
  searches over the 4 MiB image returned no match for any published code.
* The four C-library alphabet strings at `0x0803C87C`–`0x0803C900` are generic
  `printf`/ctype tables, **not** the password alphabet (they are referenced by a
  charset pointer array at `0x0804BFF4`, not by password UI code).

**Attempted and rejected models (offline, against all ten known codes):**

* `v4 = a·v0 + b·v1 + c·v2 + d·v3 + e (mod m)` for `m ∈ {25,26,27,31,32}` — no solution
  for any checksum position (0–4).
* XOR of the other four letters plus a constant — no solution.
* Plaintext / Caesar-shifted / reversed / A=0-byte / 5-bit packed literal tables — no hit.

These rejections bound simple checksum designs; they do **not** characterise the real
transform. The exact bit packing, checksum and field layout remain unknown (§8).

## 6. Tables

### 6.1 Published accepted codes (verified as *absent* from the ROM literals)

| Code | Effect | Source |
|---|---|---|
| `CTKJP` | After battle with Monkeys and Gorilla | GameFAQs, SuperCheats, CheatingDome, ChapterCheats |
| `CRKNM` | After Spike, and Phil & Lil | GameFAQs, CheatingDome |
| `CTKSP` | Find Nigel Thornberry | GameFAQs, SuperCheats, CheatingDome, ChapterCheats |
| `FTJSM` | Find Phil & Lil | GameFAQs, SuperCheats, CheatingDome, ChapterCheats |
| `CRKSM` | Get the Gators | GameFAQs, SuperCheats, CheatingDome, ChapterCheats |
| `CFGTT` | Unlock Level 2 | SuperCheats |
| `FCHNR` | Level 1 | Great Games Wiki |
| `MFHDR` | Level 2 | Great Games Wiki (conflicts with `CFGTT` for Level 2) |
| `MCTNP` | Level 3 | Great Games Wiki |

In-game generated code observed: **`CFHDM`** (pause menu, start of New Game).

All fetched pages were treated strictly as data. No prompt-injection payload was
encountered in the pages fetched for this engagement.

### 6.2 Text bank (selected IDs)

```
169 Swamp Stomp        170 Continue          171 Credits
172 Inventory          173 New Game          174 Options
180 Controls           181 SFX               182 Enter Password
183 New Password       184 Play as Eliza     185 Play as Tommy
186 Quit?              187 Pause             188 Find Chuckie
189 Find Chuckie & Donnie                    190 Get 20 Gooshy-balls
191 Scare away the monkeys 192 Find Phil & Lil 193 Find 3 Fish
194 Catch the kitty    195 Find Spike the dog 196 Find the boots
197 Get the gators     198 Find Stu Pickle   199 Find Donnie
200 Find Angelica      201 Use the bathysphere 202 Find Debbie Thornberry
203 Find 3 magazines   204 Find the keys     205 Drive the Commvee
206 Find Darwin in the cave 207 Raft the cave river 208 Find Nigel Thornberry
209 Protect Nigel Thornberry 210 Quit
```

### 6.3 Named levels/minigames (text IDs 155–169)

Angelica, Bathysphere, Beach Battle, Cave Escape, Chuckie & Donnie, Crazy Commvee,
Darwin, Debbie, Jumpin' Jungle, Nigel, Phil & Lil, Spike, Stroller, Swamp Stomp.

## 6b. Enumeration

* **Input surface:** 5 symbols from `[A-Z]`. Naive space size `26^5 = 11,881,376`
  strings, minus any reserved/excluded letters (the actual on-screen keypad alphabet
  was not recovered — see §8). If the keypad excludes `I`/`O` the space is
  `24^5 = 7,962,624`; if it is a 32-symbol alphanumeric keypad it is `32^5 = 33,554,432`.
* **Known accepted subset:** exactly 9 published codes (§6.1) plus the generated
  `CFHDM` observed in-game. `Great Games Wiki`'s `MFHDR` and SuperCheats' `CFGTT`
  both claim Level 2; at most one can be correct, so the published set contains at
  least one unverified/conflicting entry.
* **Novel code minted:** none. The validator was not recovered, so no code absent
  from the published lists could be generated with a defensible decoder. Stated
  explicitly rather than fabricating a value.
* **Bounds proven by rejection:** offline, all simple linear/XOR checksum models over
  mod 25/26/27/31/32 were rejected against the ten known codes (§5). No *in-game*
  rejection was captured, because the password entry screen was not reached in the
  emulator within this engagement (see §8). This is the principal incomplete item.
* **Negative-result boundary:** literal tables under ASCII, lowercase, reversed,
  +0x20 shift, A=0 bytes, Caesar shifts 1–25 and 5-bit packing were searched across
  all 4 MiB; none of the nine published codes nor the generated code occurs. There is
  therefore no plain lookup table of accepted passwords in this image.

## 7. Validation evidence

* **Observed:** ROM hashes/header/entry word (Phase 0); VENOM splash and Nick/Klasky
  splashes on the unmodified image; stock-crt0 copy boots the real game; Main Menu,
  Options, Pause menu and cutscenes screens captured (PNG files listed in §3);
  pause menu displays generated password `CFHDM`; text bank strings at
  `0x0803A000`–`0x0803C910`; text pointer table at `0x08043B88`; no literal hits for
  any published code.
* **Derived (disassembly):** patched entry targets `0x083E58B8`; crt0 RNC loader
  copies to `0x02000000`; `0x08005C70` scans 43 24-byte records at `0x08043F34`;
  `0x0800AC9C`/`0x0800ACB0` are the text-table base/getter; script data at
  `0x08200F64` carries IDs 182/183.
* **Inferred:** the password is algorithmic (generator on pause menu + no literal
  table); the published codes are genuine for the US/Europe A5WE build (titles and
  code strings match this SKU, consistent with §16.11's SKU check).
* **Not observed:** the password entry screen itself, acceptance/rejection of any
  typed code, and any RAM flag changed by a code.

## 8. Unknowns

1. **Password validator/generator address and algorithm** — the primary unresolved
   item. Candidate code regions were inspected with `objdump -M force-thumb` and
   Ghidra; the `cmp #0x41`/`cmp #0x1A` hits proved to be entity-opcode switches and
   C-library code, not letter math. No function that reads a 5-letter buffer and
   writes a progress/state flag was located.
2. **On-screen keypad alphabet** — the exact symbol set and index mapping for the
   password screen. The C-library charsets in ROM are not it.
3. **Entry path to the password screen** — the text IDs 182/183 and script data at
   `0x08200F64` are present, but the menu that draws them was not reached. Likely
   gated behind a story event or a title-screen state not found in this session.
4. **Field layout / checksum** — level, character (Tommy/Eliza), progress flags and
   check digits cannot be separated from the ten known codes with the simple models
   tried. A decoder oracle (guide §16.19) would settle this in minutes once the
   validator address is found.
5. **Character-select unlock gate** — "Play as Tommy"/"Play as Eliza" exist in the
   script bank; whether they are always available or save-gated was not tested.
6. **GameShark/CodeBreaker codes** from GameHacking.org and gbadamud
   (`32015700 0062`, `32015704 0064`, etc.) are external memory-edit codes and are
   explicitly **out of scope** for this report.

## 9. Tooling

* `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings -t x`, `grep -abo`.
* Python 3 with `capstone` 5.0.7 (Thumb immediate scanner), `Pillow` (screenshot crop),
  `zlib`/`struct` (mGBA `.ss1` `gbAs` chunk parser, guide §16.13 — used to confirm
  the saved state was in a cutscene and contained no password string).
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`
  for raw Thumb disassembly; `-M force-arm` for the crt0.
* REA MCP / Ghidra 12.1.4 (raw ARM import at `0x08000000`) for string inventory,
  xrefs and procedure callers; auto-analysis coverage was partial on this image.
* mGBA (`mgba -3`, `-g`, `-d`, `-t`) and VBA 1.8.0 under `Xvfb :316` + `openbox`,
  `xdotool` XTEST input, `scrot` + ImageMagick `convert` for crops.
* Helper scripts in `/tmp/opencode/rugratswild/`: `emu.py`, `walk.py`, `nav.py`,
  `fullnav.py`, `keytest.py`, `dbg.py`, `vbagdb.py`, `state_raw.bin` (parsed savestate).
* Web sources: GameFAQs, SuperCheats, ChapterCheats, CheatingDome, Great Games Wiki,
  GameHacking.org (all treated as untrusted data).

Legal note: no ROM bytes or copyrighted assets are reproduced here; only hashes,
addresses, algorithms and original observations are published.
