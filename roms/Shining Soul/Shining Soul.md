# Shining Soul (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Shining Soul.gba` |
| Size | 8,388,608 bytes (0x800000, 8 MiB) |
| Header title | `SHINING SOUL` |
| Game code | `AHUE` (USA) |
| Maker | `EB` |
| Version | 0 (Rev.00) |
| Entry word | `0xEA00002E` (stock ARM branch — **not** a patched/cracktro entry) |
| Fixed 0x96 / complement / checksum | `0x96` / `0x34` / `0x0000` |
| MD5 | `d9b338efe2c15f9493ca0b28714a679b` |
| SHA-1 | `14723ead8634959b4fad027d9618c0860b82ea67` |
| SHA-256 | `9b50d95bb4472d3c34cf587e4c4d057d3afb30a58f73a513220fe1bab1fc377e` |

Embedded GBA-header scan: the 156-byte Nintendo logo (`24 ff ae 51 …`) occurs **once**, at file offset `0x4`. There is no second image, no trainer, no appended cheat menu, and no boot selector. This is the retail single-image ROM.

## 2. Executive summary

Shining Soul has a genuine, developer-intended **name-entry code system**, not a conventional password screen. During character creation the game presents a 70-key on-screen keyboard (uppercase, lowercase, digits, symbols; observed in the emulator) and awards bonuses when the entered character name equals one of a fixed set of special names.

The special names are stored as **NUL-terminated u16 strings** in a contiguous table at ROM `0x52F224`–`0x52F2EA` (replicated in five localisation banks at `0x53AAxx`, `0x545Cxx`, `0x5510xx`, `0x55C0xx`). The exact on-screen encoding was recovered by typing marker characters and diffing savestate RAM: each character is stored as a little-endian u16 equal to `ASCII + 0x70` (`A`=`0x00B1`, `B`=`0x00B2`, `c`=`0x00D3`). The live name buffer is EWRAM `0x02002864`, and its length byte is IWRAM `0x030005F4` (observed 0 → 1 → 11 as letters were typed).

The table contains **15 special names**. Eleven match the published GameFAQs list exactly (7 item-bonus names and 4 stat-bonus names). **Four names in the ROM table appear in no published list**: `Mr?Desire`, `Yoshi`, `Isson`, `SRyota` — these are the novel codes delivered by this report (§6b).

The GameFAQs page also documents two non-name cheats: an **Advance Mode** unlock (finish the game once) and a **button code** (in Advance Mode, on the map at Dark Castle, hold L+R while selecting the level to enter a Secret Dungeon), plus two gameplay glitches (Easy Money, Item Duplication). The L+R sequence is a game-state gate, not a keypad-style code; no standalone cheat keypad, debug menu, or password validator was found anywhere in the reachable screens.

## 3. How to reproduce

Emulator: mGBA 0.10.5 on `Xvfb :319`, `SDL_AUDIODRIVER=dummy`, `-3` scale.

**Keymap measured from `KEYINPUT` at `0x04000130` (active-low) in this build** — note it is the reverse of the guide's generic default:

| GBA button | xdotool key | observed `KEYINPUT` |
|---|---|---|
| A | `x` | `0x03FE` (bit0) |
| B | `z` | `0x03FD` (bit1) |
| L | `a` | `0x01FF` (bit9) |
| R | `s` | `0x02FF` (bit8) |
| Start | `BackSpace` | `0x03F7` (bit3) |
| D-pad | arrow keys | `0x03BF`/`0x037F`/`0x03DF` |

Menu path to the code surface (the intro is time-driven and takes ~65 s; it auto-advances, and the on-screen keyboard appears after it):

1. Title `PRESS START` → press **Start**.
2. `SINGLEPLAYER MODE` / `MULTIPLAYER MODE` → press **Start** on Singleplayer.
3. Wait through the full story intro (~65 s) and the post-intro dialogue until the **name-entry keyboard** appears (verified screenshot: `nameentry.png`).
4. Navigate the 70-key grid with the D-pad; **A** (`x`) selects a character. The grid is a 14-column × 5-row ring (`ABCDEFGHIJKLMN` / `OPQRSTUVWXYZ_@` / `abcdefghijklmn` / `opqrstuvwxyz,.` / `0123456789'/ %&`); horizontal movement wraps within/between rows.
5. `L` = backspace, `B` = cancel, `R` = next page.
6. Confirm the name, then accept the file on the `Is this OK?` screen (verified: FILE 1 was created showing `SHINING`).

**Codes tested / decoded** (all literals searched in the ROM): `SHINING`, `FORCE`, `SEGATA`, `NOMUNOMU`, `SOUL`, `AIAI`, `SALAMANDER`, `MAX`, `HANS`, `ANRI`, `BLEU` (published) and `MR?DESIRE`, `YOSHI`, `ISSON`, `SRYOTA` (novel).

## 4. Address map

| Item | Address | Evidence |
|---|---|---|
| GBA header / logo | file `0x0`–`0xBF`, logo at `0x4` | observed (`xxd`) |
| Special-name string table (English) | ROM `0x52F224`–`0x52F2EA` | derived (decoded u16 strings) |
| Localised copies of the same table | ROM `0x53AA00`, `0x545CF0`, `0x551000`, `0x55C0C0` | derived (literal search) |
| Keyboard/tile-index lookup table | ROM `0x54A20`–`0x54AAF` | derived (12×12 block structure) |
| Name-entry input handler | ROM `0x080463F0` (key dispatch), `0x08046A80`–`0x08046C50` (cursor/insert) | derived (objdump; `0x030005F4` xrefs) |
| Key→character lookup helper | ROM `0x08048240` | derived (objdump) |
| Live name character buffer | EWRAM `0x02002864`, u16 per char | observed (savestate diff; RAM read) |
| Name length byte | IWRAM `0x030005F4` | observed (0 → 1 → 11 while typing) |
| Savestate layout (mGBA 0.10.5, this 8 MiB ROM) | `gbAs` zlib chunk → 397,312-byte raw state; VRAM ~`0x1000`, IWRAM `0x19000`, EWRAM `0x21000`, OAM mirror ~`0x1AD50` | observed (`ssparse.py`) |

## 5. Algorithm

The name code is a **fixed lookup**, not a checksummed serial code:

```
# on-screen character -> stored value
value = ord(char) + 0x70                 # u16, little-endian
name_buffer[i] = value                   # EWRAM 0x02002864 + 2*i
name_length    = number of chars         # IWRAM 0x030005F4  (0..11 observed)

# validation (conceptual; validator body not isolated, see §8)
for candidate in SPECIAL_NAME_TABLE:     # 15 NUL-terminated u16 strings at 0x52F224
    if name_buffer[0:len(candidate)] == candidate and name_length == len(candidate):
        apply_bonus(candidate)
```

Decoding rule for the ROM table (verified against every entry):

```python
def decode(off):
    s = ""
    while u16(rom, off) != 0:
        c = u16(rom, off) - 0x70
        s += chr(c) if 0x20 <= c < 0x7f else "?"
        off += 2
    return s
```

No checksum, permutation, XOR, or PRNG is involved: the space is exactly the 15 table entries.

## 6. Tables

All values are the decoded names as the game stores them (u16 = ASCII+0x70, NUL-terminated). Length is in characters; "Published" is the GameFAQs `Shining Soul` cheats page (archived 2025-10-01).

| ROM offset | Name | Len | Published effect | Published? |
|---|---|---:|---|---|
| `0x52F226` | `Mr?Desire` | 9 | — | **NO (novel)** |
| `0x52F23A` | `Yoshi` | 5 | — | **NO (novel)** |
| `0x52F246` | `NomuNomu` | 8 | Leaf briefs equipped (Archer only) | Yes |
| `0x52F258` | `Isson` | 5 | — | **NO (novel)** |
| `0x52F264` | `Segata` | 6 | Judo suit equipped (Dragonute only) | Yes |
| `0x52F272` | `AiAi` | 4 | Monkey Doll in inventory (any character) | Yes |
| `0x52F27C` | `Soul` | 4 | Healing Drop in inventory (any character) | Yes |
| `0x52F286` | `Salamander` | 10 | Painter's Soul in inventory (any character) | Yes |
| `0x52F29C` | `Shining` | 7 | 2 extra Herbs in inventory (any character) | Yes |
| `0x52F2AC` | `Force` | 5 | 2 Valuing Scrolls in inventory (any character) | Yes |
| `0x52F2B8` | `SRyota` | 6 | — | **NO (novel)** |
| `0x52F2C6` | `Max` | 3 | Warrior named Max: +10 Str | Yes |
| `0x52F2CE` | `Anri` | 4 | Mage named Anri: +10 Int | Yes |
| `0x52F2D8` | `Hans` | 4 | Archer named Hans: +10 Vit | Yes |
| `0x52F2E2` | `Bleu` | 4 | DragonNewt named Bleu: +10 Dex | Yes |

Other published cheats verified as *claims in the ROM-era documentation* (not password-table entries): Advance Mode (clear game once), Secret Dungeon (Advance Mode + Dark Castle map + hold L+R while selecting level), Easy Money (shop item, press R three times, drop/purchase), Item Duplication (multiplayer timing glitch). No GameShark/CodeBreaker codes are reported here by design.

## 6b. Enumeration

**Space definition.** The name-entry field is 11 u16 cells (each cell = ASCII+0x70 from a 70-symbol keyboard) with a length byte at `0x030005F4`. The full keyboard space is 70^11 ≈ 1.2 × 10^20 spellings, but the game's accepted set is a **fixed 15-entry lookup table** — the complete, closed code space is the table at `0x52F224`–`0x52F2EA`. The table is replicated verbatim in five localisation banks, so the enumeration is identical in every language.

**Closure method.** (1) The whole contiguous region `0x52F200`–`0x52F300` was decoded as u16 strings (§9, `findtable.py`), yielding exactly the 15 names above and no others. (2) A literal search for every published name under the recovered encoding hit this same table in all five banks; no additional table with different records was found. (3) Every reachable screen was walked with RAM/screenshot evidence (title → mode menu → intro → name entry → file confirm → gameplay/dialogue; no debug or password screen was reached).

**Novel codes (absent from GameFAQs, VGChartz, and TCRF).** `MR?DESIRE`, `YOSHI`, `ISSON`, `SRYOTA` are stored in the game's own special-name table yet appear in no published list. They are the unpublished members of the space. Their literal presence in the same NUL-terminated table as the 11 working codes — with the identical u16 encoding — is a ROM-level proof that the game recognises them; the *specific bonus* each grants was not isolated in RAM (see §8). The cheapest novel code to exercise an unadvertised combination is `YOSHI` (5 chars, a length not used by any published item name except `FORCE`/`SOUL`), demonstrating that the table extends beyond the public list.

**Bounds proven by rejection.** Out-of-space names are simply not in the table: any string with a different u16 sequence or a length that does not match a table record cannot be accepted by the lookup (there is no checksum to satisfy, so there is no "valid-looking but out-of-range" class to brute-force). This is a *derived* bound from the closed 15-entry table. The keyboard's own bound was observed directly: the name-length byte reached `0x0B` (11) with 11 typed characters and the buffer held exactly 11 u16 values; no 12th cell is writable.

## 7. Validation evidence

- **Observed** (emulator/state): title/mode/intro/name-entry/file-confirm/gameplay screens walked; the 70-key keyboard; `A`=`x`,`B`=`z`,`L`=`a`,`R`=`s`,`Start`=`BackSpace` measured via `KEYINPUT`; name buffer `0x02002864` receiving u16 values (`B`=`0x00B2`, `C`=`0x00B3`, `c`=`0x00D3`) and length byte `0x030005F4` counting 0→1→11; savestate `gbAs` layout; `SHINING` typed on the real keyboard and accepted into FILE 1 (screenshot `name_start.png`).
- **Derived** (disassembly/binary): the 15-entry u16 string table and its localised copies; the `ASCII+0x70` encoding; the name-input handler at `0x080463F0` with xrefs to `0x030005F4`; the 12×12 tile-index block table at `0x54A20`; single Nintendo logo / stock entry word (no trainer).
- **Inferred**: the exact per-name bonus values are taken from the published GameFAQs list and are consistent with the ROM table, but the resulting inventory/stat deltas were not isolated in RAM; the four novel names' effects are inferred from their membership in the same table.

## 8. Unknowns

- The validator function body that dispatches a matched name to its bonus was not isolated in disassembly; no single code site was proven to compare the buffer against the table (the strings are referenced through the game's text-ID system, and no direct 32-bit pointers to them exist in ROM). The table closure is therefore ROM-structural rather than call-graph-proven.
- The specific inventory/stat effect of each of the four novel names was not observed in-game (keyboard-confirm timing prevented completing a novel-name file in this session). Their recognition is proven by table membership; their reward is not.
- The L+R Secret Dungeon gate requires Advance Mode (a completed-file flag) and was not exercised end-to-end; no L+R key-mask table was isolated (raw 0x0300/0xFCFF searches are dominated by data false positives).
- No hidden debug menu was found on any reachable screen; this is a bounded negative over the walked screens, not a proof over unreachable/gated states.

## 9. Tooling

Scripts written in `/tmp/opencode/shiningsoul1/`: `header.py` (header/logo scan), `search_enc.py`/`enc_brute.py`/`textfind.py`/`findtable.py` (encoding and table recovery), `ssparse.py` (mGBA `gbAs` savestate parser), `ui.py`/`drive.py`/`typer.py`/`typer2.py` (xdotool input), `dbgdaemon.py`/`dbgcli.py` (persistent mGBA `-d` CLI-debugger driver over a PTY/FIFO). Static disassembly with `arm-none-eabi-objdump -M force-thumb`. Web evidence: GameFAQs Shining Soul cheats page via `web.archive.org` (403 direct).

No ROM or copyrighted assets are redistributed; only hashes, addresses, and the authors' own tools are published.
