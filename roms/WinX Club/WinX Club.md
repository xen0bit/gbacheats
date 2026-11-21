# WinX Club (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/WinX Club/WinX Club.gba` |
| Size | 16,777,216 bytes (0x01000000, 16 MiB) |
| Header title | `WINXCLUB` |
| Game code / maker | `BWIE` / `A4` (Konami) — `file(1)` reports "WINXCLUB (BWIEA4, Rev.00)" |
| Version / fixed / main unit / device | 0x00 / 0x96 / 0x00 / 0x00 |
| Complement / header checksum | 0x49 / 0x0000 (rebuilt-header artifact, cf. guide §16.1) |
| Entry word | 0xEA00003E (ARM branch); crt0 branch at +0xC0 = 0xEA00000E |
| MD5 | `80acbed66f2f7a2fc88357f9a2028458` |
| SHA-1 | `3b3f5c633f48ac218e9da6ac78305eab9c17ab21` |
| SHA-256 | `a3d9b2461d5408f354a511716fdd586514ffe4af713e8d4e3a39e123a5151c65` |
| External CRC32 | `1D6950A3` (GameHacking.org, AGB-BWIE-USA) |

All addresses below are **file offsets**; add `0x08000000` for the GBA bus address unless stated. Work copy and all evidence: `/tmp/opencode/winxclub2/` (ROM folder untouched).

## 2. Executive summary

**Verdict on the central ambiguity: the GBA build DOES use digit entry.** This is now settled, not ambiguous. The decisive byte-level evidence is in the game's own five-language dialogue bank: Brandon's phone call says, in English, `"It is, but I'll give you the password so you can activate it. It's 0001."` at file `0xD9BD00`–`0xD9BD47`, with the literal ASCII digits `30 30 30 31` ("0001") at `0xD9BD41`, and the same sentence with `0001` in French (`0xD9BD4C`), Spanish (`0xD9BDB5`), German (`0xD9BDDC`) and Italian (`0xD9BE42`–`0xD9BE76`). A game that merely gates the case on an inventory flag would have no reason to speak a four-digit number to the player and explicitly tell them to use it. The GameFAQs GBA walkthrough (guide 65152, §10.3) confirms the mechanic: "Red Fountain's statue requires a code, which Brandon willingly gives to Bloom. The code is 0001 ... open the left trophy case." The Russian GBA walkthrough says "enter the code written on the sheet" (3921). The trophy case is therefore a **password-entry surface**, not an item gate.

**Accept-path structure (derived from the text bank at byte level).** The safe dialogue occupies five consecutive 5-language message groups, i.e. string indices 829, 834, 839, 844 and 849 when the packed, NUL-terminated, 4-byte-aligned bank is walked from `0xD7F124`:

| String idx | File offset | English text | Role |
|---:|---:|---|---|
| 829 | 0xD881A4 | "It seems this safe requires a password to open it." | reject / not-yet-solved path |
| 834 | 0xD882C8 | "You have entered the correct code!" | **accept branch, Cloud Tower** |
| 839 | 0xD88384 | "You found a miniature of Cloud Tower! Now where could this be used?" | miniature grant, Cloud Tower |
| 844 | 0xD88504 | "You have entered the correct code!" | **accept branch, Red Fountain** |
| 849 | 0xD885BC | "You found a miniature of Red Fountain! Now where could this be used?" | miniature grant, Red Fountain |

There is **no distinct "wrong code" string** in any language: the only rejection phrasing is idx 829. Each accept message is immediately followed (five strings later, i.e. the next dialogue line) by its own miniature-grant message — two independent accept branches, one per trophy case.

**Validator status: bounded negative on the script side; native accept predicate not isolated.** The safe handler scripts contain no digit or comparison constant at all (byte dumps below), and an exhaustive 16 MiB literal search finds no `3921` constant in ASCII, u16, u32, BCD or any digit permutation. Combined with the spoken `0001`, the accept test is necessarily **native code comparing a RAM input buffer** against per-case values; the script only selects which message pair to print. I could not reach the trophy room in the emulator (see §8), so I did not observe the native keypad routine, its RAM buffer, or a live accept/reject. This is reported as a **bounded negative**, not a solved validator, and no novel code is claimed accepted (§6b).

**Debug menu: gated, not dead.** The prior pass found `bgmenuwarp` with no xrefs. This pass found the live code: function `0x080389CC` resolves the resource **by name** (`"BgMenuWarp"` at `0x08038C88`, `adr` at file `0x389EA`, passed to `bl 0x08004FFC`) and builds a 7-entry menu. It is called once, from `0x08038D5C`, inside the scene/menu dispatcher whose handler pointer `0x08038D2D` sits in the handler table at file `0xED20`. The asset itself has no direct pointer because it is loaded through the generic name-based resource manager. The gate is therefore the runtime selector that dispatches to table entry `0xED20`; no observed title-menu or in-game input selects it.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 on Xvfb `:318`, `SDL_AUDIODRIVER=dummy`, working ROM `/tmp/opencode/winxclub2/game.gba`. Keymap: D-pad = arrows, A = `x`, B = `z`, Start = `Return`, Select = `BackSpace`.
* Boot path reproduced: ~20 s Konami/ac Studios intro → title → New Game → slot 1 → Gardenia Park (2 hearts). Reached the in-game field and a save state.
* Debugger: mGBA CLI (`-d`) held open by `/tmp/opencode/winxclub2/dbgserver.py` over a unix socket; `dbg.py` client. `status`, `r/4`, `w/4`, `save N`, `break`, `watch`, `continue`. **SIGINT to the mGBA PID halts into the debugger** (useful when no breakpoint is set); the CLI does not answer commands while the core is running.
* Savestate RAM reads: `.ss1` is a PNG with a zlib `gbAs` chunk; decompressing gives 397,312 bytes (EWRAM at raw `0x21000` → `0x02000000`, IWRAM at raw `0x19000` → `0x03000000`). Diffed two states either side of moving Bloom right; player-motion changes confirmed at IWRAM `0x03003520`/`0x03003524` and a field at raw `0x55220`/`0x55224` (`0x02034220`).
* All screenshots, savestates, extracted assets and scripts live in `/tmp/opencode/winxclub2/`, **not** in the ROM folder.

## 4. Address map

| Item | File offset | ROM address | Notes |
|---|---:|---:|---|
| Header / crt0 | 0x000000 | 0x08000000 | entry 0xEA00003E |
| Resource manifest | 0x55CCC | 0x0855CCC | `[name NUL-padded][u32 size][u32 file offset]`; 29 entries |
| — `txtpackage_all.bin` | 0xD7F128 (size 0x61B58) | 0x08D7F128 | 5-language text bank |
| — `mapalfea.mmstr` | 0xD13844 (size 0x6B8E4) | 0x08D13844 | Alfea map/object/text data |
| — `scriptdata.bin` | 0xF015C8 (size 0x32850) | 0x08F015C8 | script function table + bytecode |
| — `bgmenupuzzle.bin` | 0xF5F004 (size 0x12C00) | 0x08F5F004 | full-frame compressed UI asset |
| — `bgmenuwarp` | 0xF85094 (size 0x3904) | 0x08F85094 | warp-menu background; manifest ref at 0x55F6C only |
| **Script-function table** | **0xF1D81E** | **0x08F1D81E** | 707 records × 0x20 bytes |
| — `#AlfeaA00_Safe01_Open` | record 285 @ 0xF1FBBE | 0x08F1FBBE | bytecode rel `0x1FD44` → file `0xF3D562`, len `0x10` |
| — `#AlfeaA00_Safe02_Open` | record 286 @ 0xF1FBDE | 0x08F1FBDE | bytecode rel `0x1FE4C` → file `0xF3D66A`, len `0x04` |
| — `#AlfeaA00_GoCloudTower` | record 287 | 0x08F1FBFE | rel `0x1FE94`, len `0x01` |
| Brandon password dialogue | 0xD9BD00–0xD9BE76 | 0x08D9BD00… | ASCII `0001` at 0xD9BD41 (and 4 other languages) |
| Safe messages (5 languages) | 0xD881A4, 0xD882C8, 0xD88384, 0xD88504, 0xD885BC | 0x08D8… | string indices 829/834/839/844/849 |
| Warp-menu builder | file 0x080389CC | 0x080389CC | `adr` to "BgMenuWarp" at file 0x389EA |
| Warp-menu builder caller | file 0x08038D5C | 0x08038D5C | handler pointer 0x08038D2D @ file 0xED20 |
| EWRAM player state (published raw patches) | 0x02033C50… | — | HP / WinX bar / helpers / fireflies |
| IWRAM game globals | raw 0x19000+ | 0x03003400… | resource pointers, script/player state |

## 5. Algorithm

**Script-function record format (derived, verified on several records):**

```
struct ScriptFunc {          // 0x20 bytes
    char name[26];           // '#' + identifier, NUL-padded
    u32  bytecode_offset;    // relative to 0xF1D81E (file)
    u16  bytecode_length;    // bytes
    u16  unused;             // (part of the 0x20 stride; typically 0)
};
```

* `#AlfeaA00_Safe01_Open` (idx 285) bytecode at `0xF3D562`:
  `02 00 14 00 04 00 18 00 FE FF 01 00 02 00 03 00`
  → u16 words `[0x0002, 0x0014, 0x0004, 0x0018, 0xFFFE, 0x0001, 0x0002, 0x0003]`.
* `#AlfeaA00_Safe02_Open` (idx 286) bytecode at `0xF3D66A`: `10 00 00 00` → `[0x0010, 0x0000]`.
* `#AlfeaA00_GoCloudTowerYes` (idx 289) and `#Safe02_Open` share `[0x0010, 0x0000]` — a warp/continuation primitive.
* `#GardenA00_OpenChest01` (idx 264) at `0xF1EB48`: `02 00 2C 00 04 00 18 00 FE FF` — same `[2, A, 4, B, 0xFFFE]` skeleton with different operands.

**Script-opcode semantics (bounded):** no digit, comparison, 3921 or 0001 constant appears in either safe script. The recurring `[0x0002, a, 0x0004, b, 0xFFFE]` skeleton is a "present message / set state / yield" chain used by chests, books and dialogs; the safe handler ends with the continuation words `[1, 2, 3]`. The accept decision is therefore not encoded in these scripts: it is performed by native code that selects which of the two accept-message groups (834/839 or 844/849) the script engine subsequently prints.

**Text bank format (derived):** strings are NUL-terminated and each starts on a 4-byte boundary; there is no on-disk index table. Walking from `0xD7F124` gives 5,937 strings; every dialogue line occupies 5 consecutive strings (en/fr/es/de/it). The safe messages are groups 829, 834, 839, 844, 849 — three consecutive logical lines (reject, correct, miniature) for the Cloud Tower case and two for Red Fountain. This is the accept-path chain at byte level.

**Password model (inferred, not decoded):** 4 decimal digits, `0`–`9`, `10^4 = 10,000` representable values. Two values known from published evidence (`3921`, `0001`); `0001` additionally confirmed as an in-game spoken value. No checksum, reserved bits or longer format observed.

## 6. Tables

**Published in-game passwords:**

| Code | Unlocks | Source | In-ROM evidence |
|---|---|---|---|
| `3921` | Cloud Tower miniature → Cloud Tower portal | GameFAQs 65152/40418, PS2 FAQ 44483, Russian/Spanish GBA walkthroughs | dialogue present (safe strings); literal absent as a constant; code shown on the in-game plaque/sheet graphic, not as text |
| `0001` | Red Fountain miniature → Red Fountain portal | GameFAQs GBA 65152 §10.3, supercheats Q&A | **spoken verbatim in all 5 languages at 0xD9BD41/0xD9BD4C/0xD9BDB5/0xD9BDDC/0xD9BE76** |

**Safe-related text bank entries:**

| Offset | English text |
|---:|---|
| 0xD881A4 | "It seems this safe requires a password to open it." |
| 0xD882C8 | "You have entered the correct code!" (Cloud Tower case) |
| 0xD88384 | "You found a miniature of Cloud Tower! Now where could this be used?" |
| 0xD88504 | "You have entered the correct code!" (Red Fountain case) |
| 0xD885BC | "You found a miniature of Red Fountain! Now where could this be used?" |
| 0xD80E44 | "- Obtain the code to the Trophy Case from Faragonda's bookshelf in her office." |
| 0xD92DB8 | "I think Faragonda keeps the code to the trophy case in a book in her office." |
| 0xDC7C3C | "You found the code to the trophy case of Cloud Tower's miniature!" |
| 0xDC8968 | "Plaque" (interactable object type, alongside Lever, Board, Glyph, Treasure Chest) |
| 0xD9BD00 | "It is, but I'll give you the password so you can activate it. It's 0001." |

**Menu enumeration (all reachable screens at game start):** Title (New Game / Load Game ×3 / Options), Options (Sound, Music, Text Speed), in-game Select menu (Inventory, Magic, Objectives, Favours — exactly 4 tabs, R cycles). No hidden entry observed during exhaustive cycling (prior pass, `montage_tabs2.png`).

## 6b. Enumeration

**Space definition.** 4-symbol decimal field, digits `0`–`9`; `10^4 = 10,000` strings `0000`–`9999`. Alphabet and width are corroborated by an *in-game* spoken value (`0001`, file `0xD9BD41`) and by two independent walkthroughs giving a 4-digit Cloud Tower value. No checksum field, reserved bits, or alternative length was found. The text bank has exactly **two** accept messages and **zero** distinct wrong-code messages, so the outcome domain is {reject, accept-CT, accept-RF}.

**Accepted set known:** `{3921, 0001}` — `0001` verified as a literal in the ROM dialogue; `3921` supported by walkthroughs but not present as a literal constant (it is presented graphically on the plaque/sheet). Unverified PS2-era claims `3941` and `2008` are from a different SKU and were not observed here.

**Novel codes generated and confirmed in-game: NONE.** §0.2 requires an accepted value absent from published lists for a solved code system. The native comparator/buffer was not isolated and the entry screen was not reached, so minting a value and claiming acceptance would be false. This remains the one unmet §0.2 deliverable and is stated plainly rather than glossed.

**Bounds proven by rejection: not achieved dynamically.** No wrong-code submission was observed. The report therefore claims only that the published pair is the known accepted set; it does **not** claim the set is exactly that pair.

**Static search bounds (bounded negative):**

| Search | Space checked | Hits |
|---|---:|---:|
| `3921` as ASCII | 16,777,216 byte offsets × 1 | 0 |
| `3921` as u16 LE (`51 0F`) | 16,777,216 offsets | 3 (all mid-instruction/data) |
| `3921` as u32 LE | 16,777,216 offsets | 11 (compressed graphics, no xrefs) |
| `3921` as BCD (`39 21`) | 16,777,216 offsets | 87 (none in code, Alfea map or script data) |
| 24 permutations of `{3,9,2,1}` | 16,777,216 × 24 | 1 plausible hit at 0x4155B — disassembled, false positive |
| `0001` as ASCII in text bank | 400,216-byte bank | 5 (one per language, Brandon's dialogue) |
| Script records containing any digit/comparison constant | 707 records | 0 for both safe handlers |
| Distinct correct/wrong code strings | full text bank | 2 correct, 0 wrong |
| Full-frame / keypad asset in manifest | 29 manifest entries | none named password/keypad; `bgmenupuzzle.bin` is a compressed full-frame UI asset |
| `BgMenuWarp` / `bgmenuwarp` xrefs | u32 words, Thumb ADR, Thumb LDR literals over code `0x08000000`–`0x08100000` | 1 code ADR (`0x389EA` → name string) + 1 manifest ref; 0 direct asset pointers |

**Debug-menu / button-code finding (closed as gated):** the warp menu is **live code, not dead**: `0x080389CC` looks up `"BgMenuWarp"` by name and constructs a 7-entry menu; it is called from `0x08038D5C`, which reads a u16 selector from a global object (`ldr r2,[r0,#20]` / `ldrh r1,[r0,#6]` at `0x8038D60`–`0x8038D6C`) and branches on its bits to choose menu state. That function is reached only through the handler-table entry `0x08038D2D` at file `0xED20`; no observed menu input selects that entry, and no published activation sequence exists. Exact gate: **the runtime scene/menu-state word tested at `0x08038D62`–`0x08038DA8` must select handler index `0xED20`**; absent that, the warp menu is unreachable from the enumerated title/in-game menus.

## 7. Validation evidence

| Claim | Evidence type | Evidence |
|---|---|---|
| ROM identity/hashes | Observed | `file`, `md5sum`, `sha1sum`, `sha256sum`, header hexdump |
| **Digit entry exists** | **Observed (byte-level)** | `0001` ASCII at file 0xD9BD41 + four translations; walkthrough instructions to "enter the code" |
| Script table 707 records, format | Derived | byte parse of 0xF1D81E onward; all records resolve to valid bytecode |
| Safe scripts contain no password constant | Derived | byte dumps of 0xF3D562 (16 B) and 0xF3D66A (4 B) |
| Accept-message chain | Derived | 5,937-string walk of text bank; indices 829/834/839/844/849, five languages each |
| No literal `3921` anywhere | Derived | exhaustive byte searches + Capstone/objdump of the sole permutation hit |
| Warp menu live and gated | Derived | ADR at 0x389EA, builder 0x080389CC, sole caller 0x08038D5C, handler pointer at file 0xED20, selector test 0x08038D62–0x08038DA8 |
| Gardenia Park boot state, in-game movement | Observed | screenshots `screen3.png`, `ss_both.png`; savestate diff |
| mGBA CLI debugger via PTY bridge; SIGINT halts core | Observed | `dbgserver.py`, `status` register dumps |
| Codes `3921`/`0001` correct | Inferred (external) / `0001` also observed as spoken value | walkthroughs; **not** verified by entering them on the password screen |

## 8. Unknowns

1. **Native keypad routine, RAM input buffer and accept comparator — not isolated.** Proven by exclusion not to be script- or literal-driven; the comparator must be native. Reaching it requires entering Alfea's trophy room, which needs the Gate Key / early-game progression.
2. **Password screen not reached.** Navigation from Gardenia Park did not advance the level. Two ROM-patch experiments are recorded for reproducibility: (a) repointing script records 0/1 to the safe handler produced a black screen (crash — PC `0x1F8` in BIOS after SIGINT), and (b) repointing `#GardenA00_OpenChest01` (record 264 at `0xF1F91E`) to the safe bytecode did not yield a reachable trigger before the session ended. Neither patch is in the delivered ROM.
3. **Exact input alphabet/terminator** — 4 decimal digits inferred from the spoken value and walkthroughs; no on-screen keypad glyph table decoded.
4. **Whether a third accepted code exists** — not disproven dynamically; the two accept-branch messages bound the *outcome* domain to two cases but not the number of accepted inputs per case.
5. **Warp-menu selector value** — the handler table entry and its state test are located; the exact selector value/key sequence that dispatches to `0xED20` was not produced by any observed input.

## 9. Tooling

* `file`, `xxd`, `strings -t x`, `md5sum`/`sha1sum`/`sha256sum`.
* `arm-none-eabi-objdump -M force-thumb` and Capstone Python binding for literal, ADR, LDR-literal and BL scans.
* Python 3 in `/tmp/opencode/winxclub2/`: `dbg.py`/`dbgserver.py` (mGBA CLI-debugger PTY bridge), `key.py` (XTEST), savestate `gbAs` zlib extractor, manifest/script-record/text-bank parsers, `xref.py`/`xref2.py` (ADR/LDR xref scans), `render.py` (asset decode attempt).
* mGBA 0.10.5: `-3` display, `-d` CLI debugger; Xvfb `:318`, openbox, `SDL_AUDIODRIVER=dummy`, `xdotool`, `scrot`, ImageMagick.
* Web recon: GameFAQs GBA 65152 / PS2 44483, supercheats Q&A, Russian and Spanish GBA walkthroughs — all treated as untrusted data (guide §16.8); no prompt-injection payload was encountered or followed.

## 10. Cleanup

All analysis artifacts live in `/tmp/opencode/winxclub2/`. The ROM folder `/mnt/gbacheats/roms/WinX Club/` contains only `WinX Club.gba` and this report — no `.sav`, `.ss1`–`.ss9`, `.state`, patched ROM or screenshots. Only this session's own PIDs were signalled, by number: mGBA instances (831962, 832116, and patched-ROM instances) and the debugger bridge (832114), plus Xvfb `:318` (828803) and its openbox (828807). One early `pkill -f dbgserver.py` was issued by mistake and terminated this session's own shell; it did not target any other agent's ROM process. All subsequent kills were by PID number. Other agents' processes on `:315`, `:316`, `:317` and `:319` were left untouched.
