# Fire Emblem (GBA, EU) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Fire Emblem/Fire Emblem.gba` (analysed copy `/tmp/opencode/fe1/fe.gba`) |
| Size | 16,777,216 bytes (0x01000000) |
| `file` | `Game Boy Advance ROM image: "FIREEMBLEME" (AE7E01, Rev.00)` |
| Header title | `FIREEMBLEME` (11 chars + NUL) — international **FE7 / The Blazing Blade**, European build |
| Game code / maker | `AE7E` / `01` (Nintendo), version `0x00`, fixed byte `0x96` |
| Entry word | `0xEA00002E` → stock ARM branch to `0x080000C0`; **no scene cracktro or appended trainer** in the first 4 KiB |
| Header checksum | stored `0x0000` (rebuilt header; complement byte `0xD1` is intact) — normal for this release |
| MD5 | `f1a1b9742fcd467a531dd4314c4e7d19` |
| SHA-1 | `c735fdbb9e8abe19e0c6a44708df19acc962e204` |
| SHA-256 | `f1200d19771b366b6ead15dec0eee4a7785b538d894c069c36f7592321ee799b` |

**Embedded GBA headers (Phase 0).** Scanning the whole image for the 156-byte Nintendo logo gives three hits: file `0x4` (the real header) and **two additional complete headers at file offsets `0xCF0CD0` and `0xCFA1F0`**. Both decode to title `FIREEMBLEM6\0`, game code `AFEJ` (the Japan-only FE6 / *Binding Blade* code), maker `01`, version `0`, entry word `0xEA000011`. The code following each header is a short ARM polling loop (`e1d010b8` / `e3110080` / `0afffffc` — LDRH/TST/BEQ), i.e. a small **multiboot-style FE6 payload** carried by the international FE7 ROM. They are two near-identical copies (~0x9520 apart); they are data, not a playable second game reached by any in-game menu found here. This is a concrete, independently verified explanation for "codes from other Fire Emblem titles" appearing in this image: the FE6 content is FE6 multiboot data, **not** an FE6 password/cheat system.

## 2. Executive summary

There is **no password-entry / cheat-code system** in this retail FE7 EU ROM. What exists is a set of **developer-intended button codes** and one **output-only generated password**:

1. **Soft reset** — hold `A+B+Select+Start` (published alternative `A+B+L+R`). Confirmed in emulator: instant reset to the "2003 Nintendo Presents" screen.
2. **Battle History password** — on the *Battle History* screen (Extras), **hold Select for ≈3.2 s**; a 26-character base-36 password is displayed. It encodes battle-history statistics plus the live game clock; it was used for a Japanese website contest and **does nothing when entered anywhere**. The generator and its SRAM source were located and matched to community reverse-engineering notes. A novel password was generated from synthetic save data and observed on the real screen.
3. **Sound Room hidden picture gallery** — press `R` in Sound Room to hide the song list, `A` cycles CGs. Confirmed.
4. **FE6-style `←←→→ L L Start`** is *not* a password trigger in this FE7 EU build (tested; pages just navigate). Community notes report the handler still exists in FE7/FE8 but no longer displays anything.
5. Published prototype-only combos (`R+B`+Select×2 "win chapter", `D-pad+A+B+Start+Select` tutorial escape, `B+R+Right` crash-info) do **not** fire in this retail build.
6. The `Select+Right+L` boot-time erase-save code is published for retail FE6/FE7/FE8; its exact frame-1 window could not be hit under mGBA's built-in BIOS (report as unverified in emulator, gate unreached).

Text is **Huffman-compressed** (not ASCII and not a simple tile-index substitution): `strings` finds only the header title. The game itself decompresses text into EWRAM — after entering Battle History, ASCII strings such as `"! her to the space"`, `"Place your cursor there,"`, `"!A Button"` appear at `0x0204B5BB`…, which is direct evidence of the decoded text bank.

**Relationship to the sibling FE8 (Sacred Stones) analysis:** the soft-reset combo and the boot `Select+Right+L` erase gate are shared FE6/FE7/FE8 engine behaviour (community-documented; the FE7 side verified here). The **Battle History password and its generator are FE7-specific** — FE8 has no Battle History screen and a different Extras layout. No password string, table or URL from FE8 was used as evidence here.

## 3. How to reproduce

* Emulator: mGBA (SDL), `DISPLAY=:318`, `SDL_AUDIODRIVER=dummy`, `mgba -3 <rom>`, Xvfb `:318` + openbox.
* Keymap (verified): `A=x`, `B=z`, `L=a`, `R=s`, `Start=Return`, `Select=BackSpace`, D-pad=arrow keys. Hold 100–300 ms; savestates with `xdotool key shift+F1..F9`, load with `F1..F9`.
* Soft reset: from any in-game screen, hold `x z BackSpace Return` for ~0.4 s → "2003 Nintendo Presents".
* **Reaching the password screen requires a completed game** (Extras → Battle History is gated). For analysis only, a **copy** of the ROM (`/tmp/opencode/fe1/fe_test.gba`) was patched at file offsets `0xA6070`, `0xA6090`, `0xA60A4`, `0xA60B6`, `0xA60C8`, `0xA60D8`, `0xA60EA` (branch instructions → `0x0000`) to force all Extras entries. The original ROM was never modified. With that patched copy: title → main menu → `Extras` (4×Down, A) → `Battle History` (3×Down, A) → hold `BackSpace` ≈4 s.
* Reaching Battle History on an unmodified ROM requires first clearing the game once; that legitimate path was not played end-to-end (see §8).
* To make the generator produce data, SRAM bytes at `0x7044` (148 bytes) of the save were set to a synthetic pattern and the sum+XOR checksum at `0x70D4` recomputed; with all-zero history, holding Select 3 s yields only the "Well done" dialogue.

## 4. Address map

All addresses are **ROM** (`0x08000000 + file offset`) unless marked RAM/SRAM. FE7U addresses published by the community were verified to be **identical in this EU build** for this subsystem (the literal pool at `0x0809D7F0` etc. matches).

| Address | Meaning | Evidence |
|---|---|---|
| `0x08000000` | Header; entry `0xEA00002E` | Derived (bytes) |
| `0x08001BC8` | Input routine: reads `0x04000130`, `~KEYINPUT`, masks to 10 bits, special-cases `A+B+Select+Start` (`0x0F`) and an IWRAM user mask at `0x0300000E` | Derived (disassembly) |
| `0x0809E25E` | Battle-History password maker (proc routine) | Derived |
| `0x08CC5AF0` | Proc definition for the Battle History screen (contains pointer `0x0809E25D`) | Derived (data) |
| `0x0809DFC4` | Extracts/obfuscates battle-history fields from SRAM (`mode`, `difficulty`) into RAM struct `0x020144E0` | Derived |
| `0x0809D7B4` | Math helper (`5,11`) used by encoder | Derived (community map, present) |
| `0x0809DBD8` | Encoding driver (calls hash + bit-packing helpers) | Derived |
| `0x0809DDE4` | Hash over 13 `(source byte, bit-width)` pairs | Derived |
| `0x0809D880` | Bit-packing helper: `data += PRNG(); data &= (1<<k)-1;` writes bits with modulus `[0x020143FC]` | Derived (disassembly) |
| `0x0809D82C` | PRNG: `u16 @0x02014434 = (x*13 + 1) & 0xFFFF` | Derived (disassembly, verified byte-for-byte) |
| `0x0809D800`, `0x0809D9A4`, `0x0809D9E4` | Additional encoding helpers | Derived |
| `0x0809E4C4` | Checksum: sum of u16 words XOR xor of u16 words, masked to 16 bits | Derived |
| `0x0809F0D8` | Reads 148 bytes from SRAM `0x0E007044` into `0x02020140`, checks u16 checksum at +`0x90` | Derived |
| `0x0809F134` | Reads `0x404` bytes from SRAM `0x0E007134`, checks u16 checksum at +`0x400` | Derived |
| `0x0809EB78` | "Sound Room unlocked?" check: 32 records × 20 bytes; unlocked when byte0≠0 and byte1∈{0,2} | Derived |
| `0x080A602C` / `0x080A60EA` | Extras menu builder / gated branches (patch target) | Derived |
| `0x08B857F8` | Literal pointer to the game's input struct (`0x02024C78`) | Derived |
| RAM `0x02014434`, `0x020143FC`, `0x02014438…0x020144D8` | Password encoder PRNG state, modulus, workspace | Derived |
| RAM `0x02020140` | Battle-history SRAM shadow buffer | Derived |
| RAM `0x0204B000`… | Huffman-decompressed dialogue text (observed ASCII) | **Observed** (savestate) |
| SRAM `0x0E007044` (+0x7044 in `.sav`) | 148-byte block used as password input | Derived + observed (synthetic injection) |
| file `0xCF0CD0`, `0xCFA1F0` | Embedded FE6 multiboot headers | Derived (bytes) |

## 5. Algorithm

Button codes are edge/held checks on `~KEYINPUT & 0x3FF` (A=1, B=2, Select=4, Start=8, Right=0x10, Left=0x20, Up=0x40, Down=0x80, R=0x100, L=0x200). Soft reset is the special case where the low nibble equals `0x0F` (A+B+Select+Start) in the routine at `0x08001BC8`.

Battle-History password (reimplementation outline, from the verified ROM functions and the community notes):

```
history = read_sram(0x0E007044, 0x94)        # checksum = sum(u16) ^ xor(u16) over first 0x90
if history valid and non-empty:
    for (mode,difficulty) in pages:           # 0..2 x 0..1
        fields[16] = extract(history, mode, difficulty)   # func_809DFC4
        hash_input = [ (addr_i, width_i) ... ]            # 13 pairs, widths 3,3,3,3,3,8,6,10,6,6,8,8,24
        bits = pack(fields, widths, PRNG= x=(x*13+1)&0xFFFF, modulus=[0x020143FC])
        bits ^= (game_clock >> 3) & 0x3FF
        password = base36_string(bits)                    # 26 chars, displayed in groups 5-5-4 / 5-5-2
```

The clock term is session-only (not file time), so **repeated triggers give different passwords for identical history** — this is a generated token, not a stored table. Confirmed: the PRNG and checksum functions disassemble exactly as above; the 13-field hash is at `0x0809DDE4`.

## 6. Tables

**Key masks (active-high):**

| Combo | Mask | Result in this ROM |
|---|---|---|
| A+B+Select+Start | `0x00F` | Soft reset — **Observed** |
| A+B+L+R | `0x303` | Published soft-reset alternative (not separately timed) |
| Select alone, held ≥3.2 s on Battle History | `0x004` | Password screen — **Observed** |
| Select+Right+L at boot | `0x214` | Published erase-save gate; not reproduced under built-in BIOS |
| `R` in Sound Room | `0x100` | CG gallery; `A` cycles — **Observed** |
| `Select` in Sound Room | `0x004` | Random mode — published, not separately isolated |
| `←←→→ L L Start` | sequence | FE6 password trigger; **no effect in FE7 EU** — Observed |
| `R+B` + Select×2 / `Dpad+A+B+Start+Select` / `B+R+Right` | — | Prototype-only; no effect in retail prologue — Observed |

**Password format:** alphabet `0-9A-Z` (base 36); length 26 characters; displayed as `XXXXX XXXXX XXXX / XXXXX XXXXX XX`. Example generated with synthetic history bytes `(i*7+3)&0xFF` at SRAM `0x7044`:

```
5YTY7 D5DBH 39QY
QBM84 U9WYB SS
```

**Text encoding:** Huffman-compressed script bank; font glyph arrays (community EU offsets `0x0C4C90C` menu / ≈`0x0C4F704` text) index a 72-byte-per-glyph struct. No literal password string exists in `strings` output (the only 4+ char ASCII hits are header fields and one garbage run at `0x6ACB3B`).

## 6b. Enumeration

* **Space definition.** The code is 26 base-36 symbols ≈ `36^26 ≈ 2^134` possible spellings, but the *meaningful* space is the 16 extracted battle-history fields (mode 0–2 × difficulty 0–1, ranks, turns, exp, funds, assets, etc.) plus a session clock term. The generator accepts every history record with a valid checksum; there is no whitelist/table of accepted passwords (literal search for the observed password returns **zero** ROM hits in every encoding tried: raw, `±k`, XOR `k`, `+0x20`).
* **Novel codes.** No published list of FE7 password *strings* exists (only screenshots and "does nothing" descriptions), so every generated value is by construction absent from GameFAQs / VGChartz / TCRF / wikis. Generated and **observed on the real password screen**:
  * synthetic history `(i*7+3)&0xFF` → `5YTY7 D5DBH 39QY QBM84 U9WYB SS` (screenshots `syn_sel12.png`, `pw_zoom.png`).
  * The generator is clock-dependent, so re-triggering with the same history yields further distinct, unpublished values (differential behaviour confirmed by the `GetGameClock()>>3` term at `0x0809DE2E`).
* **Bounds proven by rejection.**
  * Hold-time: 2.5 s → no prompt; 3.0 s → "Well done" dialogue only; 3.5 s → password box. Threshold ≈3.2 s (measured by pixel-diff over six hold durations, `thr_*.png`).
  * Empty/all-zero history with valid checksum → dialogue only, no password at 3 s.
  * FE6 7-press sequence → no password on any Battle History page (`bh_fe6combo.png`).
  * "All buttons except B" + d-pad (Neoseeker claim) → no password (`bh_neoseeker_combo.png`).
  * Prototype "win chapter" combo on the retail prologue battle → no state change (`combo_win.png`, RAM diff = animation noise only).
  * Sweeping every mode/difficulty page by d-pad/L/R confirmed the password is page-dependent but never a fixed published phrase.
* **Button-code space.** The single input routine at `0x08001BC8` and the menu dispatchers were enumerated for the documented masks above; no hidden debug menu is reachable in the retail ROM. The debug text rows documented for FE7 (*Release Entry*, *Continue Chp.*, *Initialize File*, *Debug*, *Map*, *D.Info*, *G'Night!*, etc.) are present as leftover data but no caller reaches them (dead code, §16.3 case 2) — they were not observed on any walked screen.

## 7. Validation evidence

* **Observed** (emulator + RAM): title, main menu (Restart/Copy/Erase/New Game[/Extras on patched copy]), Extras submenu (all five entries), Battle History pages, password box and its 26 characters, Sound-Room CG gallery, name entry, prologue battle map with movement range, save-slot selection, class-description screens, soft reset to "2003 Nintendo Presents". Savestate `gbAs` chunks (zlib) were parsed at IWRAM `+0x19000` / EWRAM `+0x21000` and diffed to confirm state changes (e.g. 343 IWRAM / 24 EWRAM byte-runs on battle map → Start). Decompressed text observed at `0x0204Bxxx`.
* **Derived** (ROM bytes/disassembly): all addresses in §4; PRNG `x*13+1`; checksum `sum ^ xor` over u16; SRAM offsets `0x7044`/`0x7134`; the `0x0F` soft-reset special case; the Extras gate branches; the two embedded FE6 headers.
* **Inferred**: the exact SHA-like struct of the 13-field hash and the base-36 emission order follow the FE7U community notes (`feuniverse.us/t/17219`) cross-checked against the present functions; the bit-level encoder was not re-implemented standalone. The embedded `AFEJ` payloads are inferred to be FE6 multiboot images from their headers and polling stub, not from executing them.

## 8. Unknowns

* The legitimate unlock path was **not** played end-to-end. Unlocking Extras needs at least one cleared game (the menu builder at `0x080A602C` counts cleared files); reaching the password screen used a documented analysis patch on a ROM **copy** plus synthetic SRAM, clearly labelled above.
* Full offline reimplementation of the 26-character encoder (bit order and hash output) remains open; the game itself was used as the oracle.
* `Select+Right+L` at true frame 1 needs a real GBA BIOS / reset timing; mGBA's built-in BIOS did not expose the window.
* Sound Room "Random Mode" (`Select`) and "hold `L` when entering Sound Room unlocks all songs" were published for FE6/prototype FE7; the latter was not isolated here.
* Whether any of the 26 characters are check digits versus payload was not separated.

## 9. Tooling

* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb|force-arm` for targeted disassembly; Python + `capstone` 5.0.7 for literal/BL/xref scans; `keystone` available.
* Python helper `/tmp/opencode/fe1/drv.py` (mGBA XTEST keypress helper, screenshot crop `720x480+281+260`, savestate `gbAs` zlib parser + RAM diff at IWRAM `+0x19000` / EWRAM `+0x21000`), `gen_pw.py` (synthetic SRAM injection + boot/navigation).
* GDB stub (`mgba -g`, `gdb-multiarch` on `:2345`) used for read-only verification; complex `call` sequences were rejected by the minimal stub, so savestate diffing was the primary RAM tool (§16.13).
* Web sources (treated as **data**; no instructions followed): Fire Emblem Wiki (`FE7` trivia, Sound Room, unused content), Fire Emblem Universe (`Researches on Battle History Password` topic 17219 — function map and pseudocode; `Erase your save data at the start of the game`; prototype offset notes), GameFAQs cheat/walkthrough pages (403; snippets via search), The Cutting Room Floor mirror, Fire Emblem WoD. No prompt-injection payload was encountered in the fetched pages; all fetched text was read as data only.
* Analysis-only patched ROM `fe_test.gba` and synthetic `fe_test.sav` live in `/tmp/opencode/fe1` and were removed from the deliverable (no ROM or assets redistributed).

## 10. Legal note

No ROM bytes, graphics, music or game text are redistributed here. Only hashes, addresses, algorithms, and original observations are published.
