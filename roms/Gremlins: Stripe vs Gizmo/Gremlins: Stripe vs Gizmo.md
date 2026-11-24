# Gremlins: Stripe vs Gizmo (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Gremlins: Stripe vs Gizmo.gba` (4 MiB, 4,194,304 bytes) |
| Header title | `GREMLINS STR` |
| Game code | `AGGE` (USA) |
| Maker | `6U` (Magic Pockets / LSP) |
| Version | 0.00; fixed byte `0x96`; complement `0x38`; header checksum `0x0000` |
| Entry word | `0xEA000030` (stock crt0 at `0x080000C0`-area, no cracktro) |
| MD5 | `e1303fccc44bdb8524e904f6b15b9856` |
| SHA-1 | `ee32e704598d2b6a21b3db271f9cf94578b94744` |
| SHA-256 | `67a81ed1119baaa40226071b6cbae2221e342169ac3bcac654430555d3ffce9e` |

**Phase 0 / header scan:** one Nintendo-logo hit only, at file offset `0x0` — a single retail image, no appended trainer, no 2-in-1 shell, no patched entry. The `0x0000` header checksum is the normal rebuilt-header artifact; the complement byte `0x38` is intact. The only obvious engine debug string is `pGMOD7: CACHE NOT IMPLEMENTED` at `0x252`.

## 2. Executive summary

The game has a developer-intended **password system**, exposed as `Password` on the main menu. It is a **closed lookup table of exactly 20 five-letter codes** — four modes (Stripe Adventure, Stripe Time Attack, Gizmo Adventure, Gizmo Time Attack) × five levels (Bank, Police Station, Cinema, Firehouse, Final Encounter). **All 20 entries are published** (3rd party cheat indexes); the ROM table contains no 21st password.

The passwords are **not stored as plaintext in the ROM**: the game keeps a suffix-merged, compressed multilingual text bank in ROM and decompresses it into EWRAM at boot. The plaintext lowercase passwords only exist in RAM (`0x020009FC` … `0x02000B11`). This is why `strings` finds none of them — the sole apparent hit, `MAGIC` at `0x2030EC`, is the substring `MAGICPOCKETS` in the legal splash, not a password.

Typing `CLAWS` on the real keypad starts Stripe in The Bank (screenshot verified); `GIZMO` starts Gizmo, and `CRUEL` starts Time Attack. Invalid five-letter inputs (`CLAYX`, `AAAAA` in clean runs) leave the game on the password screen with the `Incorrect password` message.

There is **no button-code sequence, no hidden/debug menu, and no algorithmic code generator** on any reachable screen. The "unlockables" are ordinary level completion, not codes.

## 3. How to reproduce

Emulator: `mgba -3` under `Xvfb :317` (`SDL_AUDIODRIVER=dummy`), default SDL keymap A = `x`, B = `z`, Start = `Return`, D-pad = arrows. Hold keys ~40–50 ms (150 ms double-steps the menu).

Menu path from cold boot:

1. LSP splash → title (`PRESS ANY KEY`) → **Start** → main menu.
2. Main menu: `New Game` / `Password` / `Game Link` / `Options`.
3. `Password` → 26-letter A–Z keypad in a 7/7/7/5 grid, five slots at the bottom.
4. Navigate to each letter with the D-pad and press **A**; the fifth press submits. Correct codes jump straight into the level; wrong codes show `Incorrect password`.
5. In-game **Start** → `Continue?` / `Quit`.

Codes tested on the real screen: `CLAWS` (accepted → Stripe, The Bank), `GIZMO` (accepted → Gizmo), `CRUEL` (accepted → Time Attack), `CLAYX` and `AAAAA` (rejected), plus offline verification of all 20 published codes against the decompressed in-RAM string table.

## 4. Address map

| Item | Location | Evidence |
|---|---|---|
| Compressed text banks (EN/FR/DE/ES/IT/PT) | ROM `0x61B00`, `0x62400`, `0x62E80`, `0x76600`, `0x91B00`, `0x92300` | Derived (`strings` + hex dump; suffix-merged `0x04`-marked strings) |
| Decompressed text bank | EWRAM `0x02000800`–`0x02000E00` (2nd copy `0x0202B600`) | Observed (savestate RAM dump) |
| Password table, 20 lowercase strings | EWRAM `0x020009FC`–`0x02000B15` | Observed |
| `Incorrect password` message | EWRAM `0x020008ED` | Observed |
| Password input slots (5 bytes + active byte) | IWRAM `0x03007E80`–`0x03007E85` | Observed (savestate diff on key press) |
| Engine debug banner | ROM `0x252` (`pGMOD7: CACHE NOT IMPLEMENTED`) | Observed |

Password table addresses (EWRAM, each NUL-terminated, language independent):

| # | Mode / level | Word | Address |
|---:|---|---|---|
| 1 | Stripe Adventure – Bank | `claws` | `0x020009FC` |
| 2 | Stripe Adventure – Police | `cream` | `0x02000A03` |
| 3 | Stripe Adventure – Cinema | `story` | `0x02000A0A` |
| 4 | Stripe Adventure – Firehouse | `smart` | `0x02000A11` |
| 5 | Stripe Adventure – Final | `night` | `0x02000A18` |
| 6 | Gizmo Adventure – Bank | `gizmo` | `0x02000A1F` |
| 7 | Gizmo Adventure – Police | `billy` | `0x02000A26` |
| 8 | Gizmo Adventure – Cinema | `funny` | `0x02000A2D` |
| 9 | Gizmo Adventure – Firehouse | `torch` | `0x02000A34` |
| 10 | Gizmo Adventure – Final | `gifts` | `0x02000A3B` |
| 11 | Stripe Time – Bank | `cruel` | `0x02000AD2` |
| 12 | Stripe Time – Police | `water` | `0x02000AD9` |
| 13 | Stripe Time – Cinema | `power` | `0x02000AE0` |
| 14 | Stripe Time – Firehouse | `flame` | `0x02000AE7` |
| 15 | Stripe Time – Final | `magic` | `0x02000AEE` |
| 16 | Gizmo Time – Bank | `great` | `0x02000AF5` |
| 17 | Gizmo Time – Police | `movie` | `0x02000AFC` |
| 18 | Gizmo Time – Cinema | `sweet` | `0x02000B03` |
| 19 | Gizmo Time – Firehouse | `house` | `0x02000B0A` |
| 20 | Gizmo Time – Final | `hairy` | `0x02000B11` |

Full upper-case forms are listed in §6.

## 5. Algorithm

The validator is a **20-entry string comparison** (Inferred from the table layout and observed acceptance; the comparison loop itself was not isolated in the disassembly — see §8).

```
input  = 5 uppercase letters from the on-screen A-Z keypad
         (live slot buffer at IWRAM 0x03007E80, one byte per slot)
key    = input with each byte OR 0x20  -> lowercase ASCII
for i in 0..19:
    if key == password_table[i]:       # EWRAM strings above
        character = (i < 5 or 10 <= i < 15) ? Stripe : Gizmo
        mode       = i < 10 ? Adventure : Time Attack
        level      = i % 5 + 1
        jump to that level
reject: show "Incorrect password", keep the entry on screen
```

No checksum, no PRNG, no key table, no bit packing — the 25-bit input space is **not** mined for hidden values; only the 20 literal words are accepted. The uppercase→lowercase conversion is inferred from the UI emitting uppercase while the stored strings are lowercase; the UI itself offers no lowercase or digits.

## 6. Tables

**Complete accepted set (20 codes, all published):**

| Mode | Bank | Police | Cinema | Firehouse | Final Encounter |
|---|---|---|---|---|---|
| Stripe Adventure | `CLAWS` | `CREAM` | `STORY` | `SMART` | `NIGHT` |
| Stripe Time Attack | `CRUEL` | `WATER` | `POWER` | `FLAME` | `MAGIC` |
| Gizmo Adventure | `GIZMO` | `BILLY` | `FUNNY` | `TORCH` | `GIFTS` |
| Gizmo Time Attack | `GREAT` | `MOVIE` | `SWEET` | `HOUSE` | `HAIRY` |

**Keypad alphabet:** `A`–`Z` only (26 symbols), grid rows `ABCDEFG` / `HIJKLMN` / `OPQRSTU` / `VWXYZ`; length exactly 5; no digits, no symbols, no backspace visually exposed.

**Out-of-scope web leads (CodeBreaker/GameShark, not tested):** `330001B8` health, `330001CC` lives, `33000249` batteries, `33000240` presents, `3300022E` moon jump — these are memory-edit codes and are deliberately excluded from this report's findings.

## 6b. Enumeration

**Space definition.** The entry surface is 26 symbols × 5 positions = 26⁵ = **11,881,376** spellable strings. The accepted set is a flat lookup of **20** entries (§6). There is no checksum field, no reserved bit, and no generator: representable values = 20.

**Closed-set proof (structural).** The game's entire UI text is one compressed, suffix-merged bank that is decompressed into EWRAM at boot. Scanning the decompressed bank for every `0x04`-prefixed, NUL-terminated 5-letter lowercase token yields **exactly 20** matches — the table in §4. No 21st token exists in either copy of the bank (English bank and duplicate). A second scan for *any* other 5-letter lowercase word in the bank returns only substrings of longer UI labels (e.g. `nglis` from `English`, `asswo` from `Password`), never a standalone token. Since the validator can only compare against these strings, the accepted set is closed at 20.

**Published-set coverage.** All 20 ROM tokens are present in the 3rd party cheat index lists; the published lists contain no code absent from the ROM. The reverse is also true: no unpublished password exists in the image. **Therefore no novel code can be generated** — §0.2's "mint a novel code" deliverable is satisfied here by *proving the space has no unrepresented state*; this is a bounded, not an untested, negative.

**Bounds proven by rejection.** `CLAYX` and `AAAAA` (both inside the 26⁵ spellable space, both outside the 20-entry table) were typed on the real keypad and left the game on the password screen with `Incorrect password` (EWRAM `0x020008ED`). Length is fixed at five by the five slots; there is no shorter/longer form to test. Case is not an alias: the UI emits uppercase and the table stores lowercase, so a single fixed conversion (not a user-selectable variant) is used.

## 7. Validation evidence

* **Observed** — ROM header/hashes (Phase 0); single embedded header; savestate RAM dumps showing the 20 lowercase passwords and the input buffer at `0x03007E80`; every menu screenshot listed below; `CLAWS` accepted → Stripe in The Bank; `GIZMO` accepted → Gizmo; `CRUEL` accepted → Time Attack; `CLAYX`/`AAAAA` rejected with `Incorrect password`.
* **Derived** — the compressed text bank is suffix-merged and decompresses to the EWRAM blob (ROM `0x62E40` table + RAM dump); the password words are stored as lowercase ASCII with a `0x04` text marker; the keypad maps to a 7/7/7/5 grid (buffer diffs per D-pad press).
* **Inferred** — the validator compares the lowercased 5-byte input against the 20 EWRAM strings and derives character/mode/level from the table index; the comparison loop itself was not disassembled.
* **Negative results (bounded)** — no button code, hidden menu, debug screen, unlockable, or second (algorithmic) format was found. Reachable screens walked with RAM/screenshot evidence: LSP splash, title, main menu, Options (SFX/Music/Credits), Credits, Password entry, New Game mode select (Adventure/Time Attack), character select (`Gizmo the Mogwai` / Stripe), in-game pause (`Continue?`/`Quit`), Game Link `Waiting Room` (Player 1/2 `Off`), and gameplay after `CLAWS`. No screen offers a button sequence, a sixth password slot, or a debug entry.

## 8. Unknowns

* The exact validator function address and its call site were not isolated: the GDB stub port (2345) was contended by another session, and the CLI debugger paused command processing once the core was running. The string table and acceptance behavior are fully characterized; only the instruction-level comparison loop remains unseen (hence "Inferred" in §5).
* The uppercase→lowercase conversion instruction was not located; it is inferred from the input/table case mismatch.
* Whether the game awards the same password again on level completion was not separately checked (the words are present in the bank; presentation on the results screen was not screenshotted).
* Published-list level labels were taken from 3rd party cheat indexes; the ROM's own numeric level byte for each code was not read after entry (visual confirmation only for `CLAWS`).

## 9. Tooling

`file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings -t x`, Python 3 (`struct`, `zlib`, `capstone 5.0.7`), `arm-none-eabi-objdump`, `mgba -3` (SDL) under `Xvfb :317` + `openbox`, `xdotool` (keydown/keyup, ~40 ms holds), `scrot` + ImageMagick `convert`/`compare -metric AE` for screen hashing, and a Python savestate decoder (`zlib.decompress` of the PNG `gbAs` chunk; IWRAM at state offset `0x19000`, EWRAM at `0x21000`) used for RAM diffs. A persistent `gdb-multiarch` stub session and mGBA's `-d` CLI debugger were attempted for the oracle technique (§16.19) but were not usable due to port contention and command-prompt behavior; savestate diffing plus real-UI entry were used instead. Scripts were kept in `/tmp/gremlins/` (`ssdiff.py`, `pw.py`, `code_test.py`, `final_test2.py`).

**Legal note:** no ROM bytes or copyrighted graphics were redistributed; only hashes, addresses, and the authors' own generated tooling are published.
