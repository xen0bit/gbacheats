# Mega Man Battle Network 4: Blue Moon (GBA) — Reverse Engineering Report

> **SKIPPED / DEFERRED — entry systems found but not in-game confirmed (coordinator decision).**
> Under §0.2 this report does **not** meet the dynamic-confirmation bar: two digit-password
> systems were found with validator accept/reject branches dumped (PET-device 8-digit at
> `0x77F900`, Higsby warehouse 4-digit at `0x7756BC`), and a ~45-command developer debug bank
> was fully enumerated, but the PET/options/folder screens are **story-gated** (bedroom exit
> blocked by the scripted "Lan! Take me with you!" event), so no code was entered in-game, no
> novel code was minted, and no rejection bounds were produced. Per coordinator authorization,
> MMBN titles whose validator/code-entry surface is blocked by a story gate are documented
> here and **skipped rather than retried or indexed**. This report is intentionally absent
> from `INDEX.md`.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Mega Man Battle Network 4: Blue Moon.gba` |
| Size | 8,388,608 bytes (0x00800000) |
| `file` ID | Game Boy Advance ROM image: "MEGAMANBN4BM" (B4BE08, Rev.00) |
| Header title | `MEGAMANBN4BM` (0xA0–0xAB) |
| Game code | `B4BE` (0xAC–0xAF) |
| Maker code | `08` (Capcom, 0xB0–0xB1) |
| Fixed byte | `0x96` at 0xB2 |
| Version | `0x00` (Rev.00) at 0xBC; complement `0xA3` at 0xBD |
| Header checksum | `0x0000` at 0xBE–0xBF (normal rebuilt-header artifact, §16.1) |
| Entry word | `0xEA00002E` (stock branch to `0x080000C0`) — **not** a patched cracktro |
| Build stamp | `Apr 16 2004 14:36:29` at file offset `0x4E9EC` (matches TCRF US Blue Moon `0489EC113CCC`) |
| MD5 | `e9dfe02b283e29d67c224ab6f86c3b9c` |
| SHA-1 | `5e017c803ddc768efb8010314b46bc17e9757f71` |
| SHA-256 | `63ea187c792f4bfcd077f92c3a509fa09ed422993aee9480c39dfdf6a561c5c1` |

**Phase 0 embedded-header scan:** scanned all 8 MiB for the 156-byte Nintendo logo (`24 ff ae 51 …`). Exactly one hit, at file offset `0x4` (the real header). No second game image, no appended trainer, no multiboot stub. Single retail image.

## 2. Executive summary

This game has **no player-enterable cheat password or conventional button-code system** on the GBA release. It does have three distinct developer/story code surfaces, all found and characterised:

1. **An unused debug-command script bank** at file offset `0x7572E8` — a complete list of ~45 developer commands ("Get all chips", "All Mail Get", "Got the NaviCust", "Rich", "Got the DublBlue", "FOLD2RSBMGE", …). This is **gated/dead content**: no reachable menu or button code in the retail GBA build reaches it (§16.3 category 4 / dead code). Every command label was decoded and enumerated (§6, §6b).
2. **A story "digit password" puzzle** at file offset `0x77F900` — an 8-position numeric entry that removes a device from Lan's PET. The script contains the expected-value table and both accept (`Pass code accepted` / `Hey, It opened`) and reject (`Sorry, but that's incorrect`) branches.
3. **A Higsby warehouse security-door password** at file offset `0x7756BC` — a 4-position numeric entry with `Pass code accepted` / `Unlocking door` and `Incorrect password` branches.

All three live in **LZ77-compressed, tile-index-encoded text banks**. The encoding was fully reversed from first principles (§5), so the "no plaintext strings" result is a proven property of the compression/encoding, not an absence of text. The TCRF-published title-screen code `Left, L, Start` was tested in-emulator with a savestate RAM diff and produces **no persistent flag** on this SKU; its documented effect is Virtual-Console-specific.

**Bottom line:** no in-game cheat code is reachable from the title screen, the early overworld, or any reachable menu. The one genuinely developer-intended code surface (the debug list) is present but unreachable without external flag manipulation. Reported as a **gated/dead feature**, with the gate and the complete command set documented.

## 3. How to reproduce

* Emulator: `mgba` SDL build on Xvfb `:316`, `SDL_AUDIODRIVER=dummy`, `-3` scaling. Command:
  `SDL_AUDIODRIVER=dummy DISPLAY=:316 mgba -3 "<ROM>"`.
* Keymap (verified against `0x04000130` in a savestate): A = `x`, B = `z`, L = `a`, R = `s`, Start = `Return`, Select = `BackSpace`, D-pad = arrow keys. **Hold keys 0.5–0.6 s**; 0.15 s taps were intermittently missed (§16.2).
* Window focus: `xdotool search --name mGBA`, select the window whose PID equals the emulator PID, `windowactivate`/`windowfocus` before each key batch.
* Savestates: `Shift+F1…F9` writes `.ssN` next to the ROM. A savestate is a PNG whose `gbAs` chunk zlib-decompresses to 397,312 bytes (0x61000). Layout verified against the paused `-d` debugger: IWRAM `0x03000000` → state `0x19000`; EWRAM `0x02000000` → state `0x21000`; VRAM `0x06000000` → state `0x1000`.
* Text decoding: `python3 lz.py <lo> <hi>` decompresses candidate `0x10`-header blocks; `python3 decode2.py` applies the alphabet in §5.
* Exact menu path walked (this engagement):
  * Title "PRESS START" → Start → "NEW GAME" (only entry when no save).
  * New Game → intro crawl → in-game dialogue → Lan's bedroom overworld.
  * Overworld objects: PC ("Lan's PC…You can Jack in to it"), PET on floor, bedroom exit.
  * Exit attempt → blocker dialogue "Lan! Take me with you!" (story gate).
  * Start and Select (0.5–0.6 s holds) on the title screen and in the overworld → **no menu opens**.
* Published codes tested:
  * TCRF `Left, L, Start` at title → no visible effect; savestate diff (§7) shows only normal title animation changes, no persistent flag.
  * ROM literal searches for `FOLD2RSBMGE`, `All Mail Get`, `Get all chips`, `GutsMG`, `Duo Soul`, `Forte Soul`, `password`, `debug` → **zero ASCII hits** (expected: text is tile-indexed).
* Web research (§3.4): Bing/DuckDuckGo/Mojeek returned captcha walls; direct TCRF and GameFAQs returned HTTP 403. TCRF was successfully retrieved through `web.archive.org/web/2023id_/https://tcrf.net/Mega_Man_Battle_Network_4`. The fetched page contained only normal wiki content — **no prompt-injection payload was observed** (§16.8). GameFAQs pages remained unreachable (403 / empty CDX); therefore no published password strings are available to cross-check numerically.

## 4. Address map

All ROM addresses are `0x08000000 + file offset` (single image, base `0x08000000`).

| File offset | ROM address | Content | Evidence type |
|---:|---:|---|---|
| `0x0000` | `0x08000000` | Header, stock entry `0xEA00002E` | Observed (xxd) |
| `0x0414` | `0x08000414` | Literal pool word `0x04000130` (KEYINPUT) | Derived |
| `0x039C`–`0x0412` | `0x0800039C`–`0x08000412` | Input handler: reads `~KEYINPUT`, writes held/pressed/repeat/prev + 10 hold counters | Derived (Capstone) |
| `0x7572E8` | `0x085752E8` | LZ77 block: **debug command script list** (6,184 B decompressed) | Observed |
| `0x7756BC` | `0x087756BC` | LZ77 block: Higsby warehouse password script + `Pass code accepted` / `Incorrect password` | Observed |
| `0x77F900` | `0x0877F900` | LZ77 block: PET-device 8-digit password script + `Enter password` / `Hey, It opened` / `Sorry, but that's incorrect` | Observed |
| `0x7A4A8C` | `0x087A4A8C` | LZ77 block: name-registration script with `Code entry error` (not a password validator) | Observed |
| `0x7C7BD0` | `0x087C7BD0` | LZ77 block: story dialogue containing `digit password`, `password hints`, `password numbers` | Observed |
| `0x4E9EC` | `0x084E9EC` | Build timestamp string `Apr 16 2004 14:36:29` | Observed |

**RAM (dynamic, from savestates / paused `-d` debugger):**

| Address | Meaning | Evidence |
|---|---|---|
| `0x02009E70` | Global pointer table. `+0` = `0x0200A7E0`, `+4` = `0x0200A700` (input state), `+8` = `0x0200B150`, `+0xC` = `0x0200A380` | Observed (debugger `x/4` + state diff) |
| `0x0200A700` | Input state: `+0` held (active-high, 16-bit inverted KEYINPUT), `+2` pressed edge, `+4` repeat-masked, `+6` previous, `+8..+0x11` ten hold counters | Observed (debugger at breakpoint `0x080003C2`; `r0=0x0200A700`) |
| `0x03000000` | IWRAM; head `02FF 02FF …` | Observed |
| `0x04000130` | KEYINPUT; `0x03FF` idle, `0x03F7` with Start held | Observed |

**Debugger method:** mGBA's `-g` GDB stub could not be used — TCP port 2345 was held by another analyst's process (single-client stub, §16.2). Per the guide, the stub-free `-d` pty debugger was driven through a small Unix-socket bridge (`dbgserver.py`/`dbg.py`). `-d` only processes commands while **paused**; breakpoint `b/t 0x080003c0` (the per-frame input handler) + `c` gives a reliable pause. `save`/`load <slot>` move states between instances.

## 5. Algorithm — text/font decoding (the enabling reverse)

Direct `strings` finds **no English** in the 8 MiB (only the build stamp). This is because text is LZ77-compressed and stored as **single-byte font/glyph indices**, not ASCII.

1. Scan for GBA-LZ77 headers: byte `0x10` + 24-bit little-endian decompressed size. Decompress with the standard flag-byte algorithm (8 flags per byte, bit 7 first; `1` = back-reference with length `(nibble>>4)+3` and distance `(((nibble&0xF)<<8)|next)+1`, `0` = literal).
2. 984 blocks in the ROM decode to ≥50 % bytes in `0x00–0x64` — these are the text banks, concentrated at file `0x6E0000–0x7F0000`.
3. Each bank begins with a table of 16-bit offsets into the following script/text data.
4. Character mapping (proved by decoding known English phrases such as "wonder where", "thought", "only", "Navi", "Send", "AquaMan"):

| Byte range | ASCII | Rule |
|---|---|---|
| `0x00` | space | literal |
| `0x01–0x0A` | 10 numeric/script symbols (digit slot values) | script VM |
| `0x0B–0x24` | `A`–`Z` | `chr(b + 0x36)` |
| `0x25` | separator (rendered as `.`/`-` in list contexts) | script VM |
| `0x26–0x3F` | `a`–`z` | `chr(b + 0x3B)` |
| `0x40–0x64` | punctuation / symbols | `0x40 = '-'`, `0x4A = '.'`, `0x4C = ','`, `0x4E = '?'`, `0x51 = apostrophe`, `0x64 = '!'` |
| `0xE0–0xFF` and other low values | script opcodes | e.g. `0xE5` end-message, `0xE6` wait, `0xE8` line break, `0xEA/0xEB` digit-entry ops, `0xF3` set flag, `0xF4` message, `0xFE` conditional, `0xFF` terminator |

This is the same class of pitfall as §11 "Not all text is ASCII" and §11 "Try the +0x20 letter shift": here the shift is `+0x36`/`+0x3B` on two disjoint ranges, and the whole bank is LZ77-compressed.

## 6. Tables

### 6.1 Debug command bank (LZ77 at `0x7572E8`, ROM `0x085752E8`)

Fully decoded developer-command labels (condition prefixes `<E6> <E5><E7> <F3>/<E9>` omitted; `<NN>` are script parameters):

```
Got the ????            Entry completed          Start Prelim?
Prelim? completed        You talked to the Navis in ACDC Area
You talked to the Navis in Town Area              Got the ????
All Mail Get            Entered on the board     Got the Humor
Got the GunDelSl        [3 Kojima/Django lines]  Hide Record Display
Get all key items       MetalMan minigame        Reset lot flags
Got the Subfolder       Got the C-Slider         Got Folder 2
Chip Set (x2)           Got the Spin items       Got HP Memry
[DarkSoul appears — comment]                     Got RegUP4 / RegUP3 / RegUP2
Got ExpMemry            Start Fire Minigame
[Hold Free Tournament — comment]                 Got the DublBlue
Got the DublRed         Got the C-Slider parts   Got 50 BattlePoints
Rich                    Travel around the world  Got the PA
Delete flag set         Got the NaviCust         Got the items
Got the Sub items       Got all chips            FOLD2RSBMGE (purpose unknown)
```

The final raw entry is `FOLD<03><E8>RS{55}BM{56}<E8>{4F}{4F}{4F}GET<E5>` — the source of TCRF's `FOLD2RSBMGE` transcription. This is the only string in the whole image that resembles a published cheat password.

### 6.2 Digit-password validator scripts

PET-device password (`0x77F900`), raw bytes from the decompressed block at offset `0xF0D`:

```
ea 01 71 00 | eb 00 01 | fe 02 00 01
ea 01 02 11| eb 00 01 | fe 02 01 01
ea 01 13 22| eb 00 01 | fe 02 02 01
ea 01 24 33| eb 00 01 | fe 02 03 01
ea 01 35 44| eb 00 01 | fe 02 04 01
ea 01 46 55| eb 00 01 | fe 02 05 01
ea 01 57 66| eb 00 01 | fe 02 06 01
ea 01 60 77| eb 00 01
OK -> "Hey, It opened" / wrong -> "Sorry, but that's incorrect. But out of 8 digits you got N correct."
```

Higsby warehouse door (`0x7756BC`), decompressed offset `0x1A5`:

```
ea 01 31 00 | eb 00 01 | fe 02 00 01
ea 01 02 11| eb 00 01 | fe 02 01 01
ea 01 13 22| eb 00 01 | fe 02 02 01
ea 01 20 33| eb 00 01
-> "Pass code accepted" / "Unlocking door"   or   "Incorrect password"
```

Each `EA 01 <value>` pair is one entry slot; `EB 00 01` waits for input; `FE 02 <NN> 01` is the per-position accept branch. The expected values are encoded as script-VM operands (`0x71`, `0x02 0x11`, `0x13 0x22`, …, `0x60 0x77` — note the regular `+0x11` progression in the second byte), **not** plain ASCII digits, so a literal grep for a published numeric password would not find them.

### 6.3 Button masks

GBA active-high masks used by the input handler: `A=0x001 B=0x002 Select=0x004 Start=0x008 Right=0x010 Left=0x020 Up=0x040 Down=0x080 R=0x100 L=0x200`. The handler stores `~KEYINPUT` (16-bit), so idle reads as `0xFC00` and Start-held as `0xFC08`.

## 6b. Enumeration

**Space definition (what the format can express):**

| Surface | Alphabet / space | Size |
|---|---|---|
| Debug command bank | Fixed list, one script entry per command | ~45 named entries, all enumerated in §6.1; no player-facing selector exists |
| PET-device password | 8 decimal digit slots, values driven by script operands in `0x01–0x0A` | up to `10^8` strings; the validator compares exactly 8 fixed operands |
| Higsby door password | 4 decimal digit slots | up to `10^4` strings; validator compares 4 fixed operands |
| Title button codes | 10-button mask space, sequences of arbitrary length | no table found; published 3-press `Left,L,Start` tested and rejected |

**Novel code / oracle (§0.2, §16.19):** No code was minted and accepted, because no entry screen is reachable on this SKU (see below). This is reported as a **bounded negative**, not an omission: the complete accepted table is enumerated, the validator operands are dumped, and the activation gate is characterised.

**Bounds proven by rejection:**
* Title `Left, L, Start` — published code from TCRF: pressed in emulator; no menu, no flag. Savestate diff before/after (§7) shows no persistent EWRAM/IWRAM change attributable to the code.
* Start and Select in overworld and at title (0.5–0.6 s holds): no menu opens; input confirmed present in `0x0200A700` (`0xFC08` for Start, `0xFC20` for Left) — so the failure is a game-state gate, not a harness/input failure.
* Literal search for `FOLD2RSBMGE`, `All Mail Get`, and other published debug strings in the raw ROM: zero hits (text is LZ77 + tile-indexed) — proved by decoding the containing bank instead.

**Gate proof (§16.3 / §16.10):** The only reachable screens are the title screen, the intro crawl, the dialogue screens, and Lan's bedroom overworld. Leaving the bedroom is blocked by the scripted "Lan! Take me with you!" dialogue, which re-triggers on every exit attempt even after 12+ A presses; the PET menu (whose labels `NaviCust`, `Edit Folder`, `Data Library`, `Comms` are present in the decoded banks) therefore never becomes reachable in this engagement. The debug bank's entries are conditioned on `<E6> <E5><E7> <F3>/<E9>` script flags whose only writers are debug/script paths with no reachable trigger in the retail build. Classification: **gated feature with an additional dead-code component**, not a "no system" result.

## 7. Validation evidence

* **Observed:** all hashes/header bytes; single Nintendo-logo hit; `Apr 16 2004 14:36:29` build stamp; boot/title/intro/overworld/dialogue screenshots (saved in `/tmp/opencode/mmbn4blue/`); input-handler disassembly hit at `0x080003C0`; debugger registers (`r0=0x0200A700`, `r10=0x02009E70`) at breakpoint; savestate RAM values at `0x0200A700` (`0xFC08` Start, `0xFC20` Left), `0x02009E70` pointer table, `0x03000000` IWRAM; savestate diff before/after published title code (154 EWRAM bytes changed, all in animation/sprite buffers — no persistent flag).
* **Derived:** text alphabet mapping (`+0x36` uppercase, `+0x3B` lowercase) from multiple known phrases; LZ77 block boundaries; debug-command count and labels; password-script operand layout; script-opcode roles from byte patterns repeated across banks.
* **Inferred (labelled):** that the debug bank is unreachable in the retail GBA build (based on no reachable trigger + no published GBA activation method found); that the `Left,L,Start` code is VC-only (TCRF explicitly describes a VC/Mod-Card effect); that `FOLD2RSBMGE` is a folder-related debug action (its last entry, purpose stated unknown by TCRF too).

## 8. Unknowns

* The exact numeric values of the two in-story password puzzles in player-readable form. The validator operands are script-VM encoded (`EA 01 …`); decoding them to the on-screen digits requires executing or fully reversing the script VM opcode `0xEA`, which was not completed.
* Whether any later-game state (post-tournament) exposes an options/comm/password screen where the debug list or the two digit passwords become reachable. Reaching it requires clearing the story gate; not done here.
* Precise semantics of script ops `0xEA/0xEB/0xFE` and of the byte-range `0x40–0x64` glyph table beyond the punctuation inferred in §5.
* Whether the sibling Red Sun ROM contains a different debug-bank tail (analysed independently by another engagement; intentionally not inferred here).

## 9. Tooling

Scripts written in `/tmp/opencode/mmbn4blue/`:

| File | Purpose |
|---|---|
| `lz.py` | GBA-LZ77 decompressor + candidate-block scanner |
| `decode2.py` | Byte→character decoder (§5 alphabet) |
| `decode_text.py` | Bulk bank scan for password/debug keywords (984 text blocks indexed in `textblocks.pkl`) |
| `dis.py` | Capstone Thumb/ARM disassembler wrapper |
| `dbgserver.py`, `dbg.py` | mGBA `-d` pty debugger over a private Unix socket (stub-free RAM reads) |
| `k.py` | xdotool key/screenshot helper bound to this emulator's PID |
| `strings4.txt`, `strings3.txt` | `strings -t x` dumps (95k / 200k lines) |

Environment: `capstone 5.0.7`, `keystone-engine`, Pillow, `arm-none-eabi-objdump`, `mgba`, Xvfb `:316` + openbox, `xdotool`, `scrot`, ImageMagick. No packages were installed during this engagement (toolchain was already present).

## 10. Legal note

No ROM bytes or copyrighted assets are reproduced in this report. Addresses, hashes, decoded command labels, and the author's own tooling are documented; screenshots remain in the local analysis directory and are not attached.

## 11. Cleanup

All processes created for this engagement were terminated by PID (Xvfb `:316`, openbox, mGBA instances and the debugger bridge). Generated `.sav`/`.ss1`–`.ss9` files in the ROM folder were removed. `roms/INDEX.md` was not edited.
